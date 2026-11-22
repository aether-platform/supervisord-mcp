"""
Supervisord manager for process control operations.
"""

import asyncio
import logging
import re
import urllib.parse
import xmlrpc.client
from collections.abc import Callable
from typing import Any

DEFAULT_SERVER_URL = "http://localhost:9001/RPC2"

# Log retrieval limits. Supervisord's log API works in bytes, so both a line cap and a
# byte cap are enforced to keep tool responses bounded.
DEFAULT_LOG_LINES = 100
MAX_LOG_LINES = 1000
DEFAULT_LOG_BYTES = 16 * 1024
MAX_LOG_BYTES = 256 * 1024

REDACTED = "***"
_PROCESS_NAME_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_.:-]*$")


def split_credentials(url: str) -> tuple[str, str | None, str | None]:
    """Split ``user:password@`` userinfo out of a URL.

    Returns:
        (url_without_userinfo, username, password)
    """
    parts = urllib.parse.urlsplit(url)
    if "@" not in parts.netloc:
        return url, None, None
    netloc = parts.netloc.rsplit("@", 1)[1]
    clean = urllib.parse.urlunsplit((parts.scheme, netloc, parts.path, parts.query, parts.fragment))
    username = urllib.parse.unquote(parts.username) if parts.username else None
    password = urllib.parse.unquote(parts.password) if parts.password else None
    return clean, username, password


def _bounded_int(value: Any, low: int, high: int) -> bool:
    """True if value is an int (not bool) within [low, high]."""
    return isinstance(value, int) and not isinstance(value, bool) and low <= value <= high


class SupervisordManager:
    """Manager for Supervisord process operations."""

    def __init__(
        self,
        server_url: str = DEFAULT_SERVER_URL,
        username: str | None = None,
        password: str | None = None,
    ):
        """Initialize Supervisord manager.

        Args:
            server_url: URL of Supervisord XML-RPC server. Credentials embedded as
                ``http://user:pass@host`` are still accepted for compatibility, but they
                are stripped from ``server_url`` and never echoed back.
            username: Basic auth username (takes precedence over the URL)
            password: Basic auth password (takes precedence over the URL)
        """
        clean_url, url_user, url_password = split_credentials(server_url)
        self.server_url = clean_url  # safe to display: never contains credentials
        self._username = username or url_user
        self._password = password or url_password
        self.server: xmlrpc.client.ServerProxy | None = None
        self.logger = logging.getLogger(__name__)

    @property
    def has_credentials(self) -> bool:
        """Whether Basic auth credentials are configured."""
        return bool(self._username or self._password)

    def _proxy_url(self) -> str:
        """URL including credentials, used for the XML-RPC transport only."""
        if not self.has_credentials:
            return self.server_url
        parts = urllib.parse.urlsplit(self.server_url)
        userinfo = urllib.parse.quote(self._username or "", safe="")
        if self._password:
            userinfo += ":" + urllib.parse.quote(self._password, safe="")
        return urllib.parse.urlunsplit(
            (parts.scheme, f"{userinfo}@{parts.netloc}", parts.path, parts.query, parts.fragment)
        )

    def redact(self, text: str) -> str:
        """Remove configured credentials from arbitrary text (error messages, logs)."""
        secrets: set[str] = set()
        if self._password:
            secrets.add(self._password)
            secrets.add(urllib.parse.quote(self._password, safe=""))
        # Longest first so overlapping secrets are fully replaced.
        for secret in sorted(secrets, key=len, reverse=True):
            text = text.replace(secret, REDACTED)
        return text

    def _error(self, action: str, exc: BaseException) -> dict[str, Any]:
        """Build an error result with credentials redacted."""
        message = self.redact(str(exc))
        self.logger.error(f"Failed to {action}: {message}")
        return {"status": "error", "message": message}

    async def _call(self, method: Callable[..., Any], *args: Any) -> Any:
        """Run a blocking XML-RPC call in the default executor."""
        return await asyncio.get_event_loop().run_in_executor(None, method, *args)

    def _require_server(self) -> xmlrpc.client.ServerProxy:
        if not self.server:
            raise ConnectionError("Not connected to Supervisord")
        return self.server

    async def connect(self) -> bool:
        """Connect to Supervisord server.

        Returns:
            True if connection successful, False otherwise
        """
        try:
            if self.server is None:
                self.server = xmlrpc.client.ServerProxy(self._proxy_url())
            # Test connection by getting API version
            await self._call(self.server.supervisor.getAPIVersion)
            self.logger.debug(f"Connected to Supervisord at {self.server_url}")
            return True
        except Exception as e:
            self.logger.error(
                f"Failed to connect to Supervisord at {self.server_url}: {self.redact(str(e))}"
            )
            self.server = None
            return False

    async def add_process(
        self,
        name: str,
        command: str,
        directory: str | None = None,
        autostart: bool = False,
        autorestart: str = "unexpected",
        numprocs: int = 1,
        **kwargs: Any,
    ) -> dict[str, Any]:
        """Prepare a configuration snippet for a new process.

        Supervisord cannot add programs over XML-RPC, so nothing is written or
        started; the returned config must be added to supervisord.conf manually.

        Returns:
            Dict with operation result
        """
        self._require_server()

        if not _PROCESS_NAME_RE.match(name) or ".." in name:
            return {
                "status": "error",
                "message": f"Invalid process name {name!r}: use letters, digits, '_', '.', '-', ':'",
            }

        config: dict[str, Any] = {
            "command": command,
            "autostart": autostart,
            "autorestart": autorestart,
            "numprocs": numprocs,
            "redirect_stderr": True,
            "stdout_logfile": f"/tmp/{name}.log",
            "stderr_logfile": f"/tmp/{name}_error.log",
        }
        if directory:
            config["directory"] = directory
        config.update(kwargs)

        self.logger.warning(
            "Dynamic process addition not supported. "
            "Please add process to supervisord.conf and reload configuration."
        )
        return {
            "status": "warning",
            "message": f"Process '{name}' configuration prepared. "
            "Please add to supervisord.conf and reload.",
            "config": config,
        }

    async def start_process(self, name: str) -> dict[str, Any]:
        """Start a process."""
        server = self._require_server()
        try:
            result = await self._call(server.supervisor.startProcess, name)
            self.logger.info(f"Started process {name}")
            return {"status": "ok", "message": f"Process '{name}' started", "result": result}
        except Exception as e:
            return self._error(f"start process {name}", e)

    async def stop_process(self, name: str) -> dict[str, Any]:
        """Stop a process."""
        server = self._require_server()
        try:
            result = await self._call(server.supervisor.stopProcess, name)
            self.logger.info(f"Stopped process {name}")
            return {"status": "ok", "message": f"Process '{name}' stopped", "result": result}
        except Exception as e:
            return self._error(f"stop process {name}", e)

    async def restart_process(self, name: str) -> dict[str, Any]:
        """Restart a process (stop, then start)."""
        server = self._require_server()
        try:
            await self._call(server.supervisor.stopProcess, name)
            result = await self._call(server.supervisor.startProcess, name)
            self.logger.info(f"Restarted process {name}")
            return {"status": "ok", "message": f"Process '{name}' restarted", "result": result}
        except Exception as e:
            return self._error(f"restart process {name}", e)

    async def list_processes(self) -> dict[str, Any]:
        """List all processes."""
        server = self._require_server()
        try:
            processes = await self._call(server.supervisor.getAllProcessInfo)
            if not isinstance(processes, list):
                processes = []
            self.logger.debug(f"Listed {len(processes)} processes")
            return {"status": "ok", "processes": processes}
        except Exception as e:
            return self._error("list processes", e)

    async def get_process_status(self, name: str) -> dict[str, Any]:
        """Get status of a specific process."""
        server = self._require_server()
        try:
            info = await self._call(server.supervisor.getProcessInfo, name)
            self.logger.debug(f"Got status for process {name}")
            return {"status": "ok", "process": info}
        except Exception as e:
            return self._error(f"get status for process {name}", e)

    async def get_logs(
        self,
        name: str,
        lines: int = DEFAULT_LOG_LINES,
        stderr: bool = False,
        max_bytes: int = DEFAULT_LOG_BYTES,
    ) -> dict[str, Any]:
        """Get the tail of a process log, bounded in both lines and bytes.

        Args:
            name: Process name
            lines: Maximum number of trailing lines to return (1..MAX_LOG_LINES)
            stderr: Whether to get stderr logs
            max_bytes: Maximum number of trailing bytes to read (1..MAX_LOG_BYTES)

        Returns:
            Dict with ``logs`` (list of lines) and ``truncated`` (older output omitted)
        """
        server = self._require_server()

        if not _bounded_int(lines, 1, MAX_LOG_LINES):
            return {
                "status": "error",
                "message": f"lines must be an integer between 1 and {MAX_LOG_LINES}",
            }
        if not _bounded_int(max_bytes, 1, MAX_LOG_BYTES):
            return {
                "status": "error",
                "message": f"max_bytes must be an integer between 1 and {MAX_LOG_BYTES}",
            }

        try:
            method = (
                server.supervisor.tailProcessStderrLog
                if stderr
                else server.supervisor.tailProcessStdoutLog
            )
            # tail*Log(name, offset, length) -> [data, new_offset, overflow]
            tail = await self._call(method, name, 0, max_bytes)
            if isinstance(tail, list | tuple) and tail:
                data = str(tail[0] or "")
                overflow = bool(tail[2]) if len(tail) > 2 else False
            else:
                data = str(tail or "")
                overflow = False
            # Never trust the daemon to honour the length argument.
            if len(data) > max_bytes:
                data = data[-max_bytes:]
                overflow = True

            log_lines = data.split("\n") if data else []
            if log_lines and log_lines[-1] == "":
                log_lines.pop()
            # When the byte window cut into a line, drop the partial first line.
            if overflow and len(log_lines) > 1:
                log_lines = log_lines[1:]
            truncated = overflow or len(log_lines) > lines
            log_lines = log_lines[-lines:]
            self.logger.debug(f"Retrieved {len(log_lines)} log lines for process {name}")
            return {"status": "ok", "logs": log_lines, "truncated": truncated}
        except Exception as e:
            return self._error(f"get logs for process {name}", e)

    async def get_system_info(self) -> dict[str, Any]:
        """Get Supervisord system information (never includes credentials)."""
        server = self._require_server()
        try:
            api_version = await self._call(server.supervisor.getAPIVersion)
            supervisor_version = await self._call(server.supervisor.getSupervisorVersion)
            state = await self._call(server.supervisor.getState)
            info = {
                "api_version": api_version,
                "supervisor_version": supervisor_version,
                "state": state,
                "server_url": self.server_url,
                "authentication": "configured" if self.has_credentials else "none",
            }
            self.logger.debug("Retrieved system information")
            return {"status": "ok", "info": info}
        except Exception as e:
            return self._error("get system info", e)

    async def reload_config(self) -> dict[str, Any]:
        """Reload Supervisord configuration."""
        server = self._require_server()
        try:
            result = await self._call(server.supervisor.reloadConfig)
            self.logger.info("Reloaded Supervisord configuration")
            return {"status": "ok", "message": "Configuration reloaded", "result": result}
        except Exception as e:
            return self._error("reload configuration", e)
