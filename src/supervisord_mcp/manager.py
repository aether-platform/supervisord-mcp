"""
Supervisord manager for process control operations.
"""

import asyncio
import logging
import xmlrpc.client
from typing import Any


class SupervisordManager:
    """Manager for Supervisord process operations."""

    def __init__(self, server_url: str = "http://localhost:9001/RPC2"):
        """Initialize Supervisord manager.

        Args:
            server_url: URL of Supervisord XML-RPC server
        """
        self.server_url = server_url
        self.server: xmlrpc.client.ServerProxy | None = None
        self.logger = logging.getLogger(__name__)

    async def connect(self) -> bool:
        """Connect to Supervisord server.

        Returns:
            True if connection successful, False otherwise
        """
        try:
            self.server = xmlrpc.client.ServerProxy(self.server_url)
            # Test connection by getting API version
            await asyncio.get_event_loop().run_in_executor(
                None, self.server.supervisor.getAPIVersion
            )
            self.logger.info(f"Connected to Supervisord at {self.server_url}")
            return True
        except Exception as e:
            self.logger.error(f"Failed to connect to Supervisord: {e}")
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
        """Add a new process to Supervisord configuration.

        Args:
            name: Process name
            command: Command to execute
            directory: Working directory
            autostart: Whether to start automatically
            autorestart: Restart policy
            numprocs: Number of processes
            **kwargs: Additional configuration options

        Returns:
            Dict with operation result
        """
        if not self.server:
            raise ConnectionError("Not connected to Supervisord")

        try:
            # Create program configuration
            config = {
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

            # Note: Supervisord doesn't support dynamic process addition via XML-RPC
            # This would typically require updating the configuration file and reloading
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

        except Exception as e:
            self.logger.error(f"Failed to add process {name}: {e}")
            return {"status": "error", "message": str(e)}

    async def start_process(self, name: str) -> dict[str, Any]:
        """Start a process.

        Args:
            name: Process name

        Returns:
            Dict with operation result
        """
        if not self.server:
            raise ConnectionError("Not connected to Supervisord")

        try:
            result = await asyncio.get_event_loop().run_in_executor(
                None, self.server.supervisor.startProcess, name
            )
            self.logger.info(f"Started process {name}")
            return {"status": "ok", "message": f"Process '{name}' started", "result": result}
        except Exception as e:
            self.logger.error(f"Failed to start process {name}: {e}")
            return {"status": "error", "message": str(e)}

    async def stop_process(self, name: str) -> dict[str, Any]:
        """Stop a process.

        Args:
            name: Process name

        Returns:
            Dict with operation result
        """
        if not self.server:
            raise ConnectionError("Not connected to Supervisord")

        try:
            result = await asyncio.get_event_loop().run_in_executor(
                None, self.server.supervisor.stopProcess, name
            )
            self.logger.info(f"Stopped process {name}")
            return {"status": "ok", "message": f"Process '{name}' stopped", "result": result}
        except Exception as e:
            self.logger.error(f"Failed to stop process {name}: {e}")
            return {"status": "error", "message": str(e)}

    async def restart_process(self, name: str) -> dict[str, Any]:
        """Restart a process.

        Args:
            name: Process name

        Returns:
            Dict with operation result
        """
        if not self.server:
            raise ConnectionError("Not connected to Supervisord")

        try:
            # Stop then start the process
            await asyncio.get_event_loop().run_in_executor(
                None, self.server.supervisor.stopProcess, name
            )
            result = await asyncio.get_event_loop().run_in_executor(
                None, self.server.supervisor.startProcess, name
            )
            self.logger.info(f"Restarted process {name}")
            return {"status": "ok", "message": f"Process '{name}' restarted", "result": result}
        except Exception as e:
            self.logger.error(f"Failed to restart process {name}: {e}")
            return {"status": "error", "message": str(e)}

    async def list_processes(self) -> dict[str, Any]:
        """List all processes.

        Returns:
            Dict with list of processes
        """
        if not self.server:
            raise ConnectionError("Not connected to Supervisord")

        try:
            processes = await asyncio.get_event_loop().run_in_executor(
                None, self.server.supervisor.getAllProcessInfo
            )
            # Ensure processes is a list for type checking
            if not isinstance(processes, list):
                processes = []
            self.logger.debug(f"Listed {len(processes)} processes")
            return {"status": "ok", "processes": processes}
        except Exception as e:
            self.logger.error(f"Failed to list processes: {e}")
            return {"status": "error", "message": str(e)}

    async def get_process_status(self, name: str) -> dict[str, Any]:
        """Get status of a specific process.

        Args:
            name: Process name

        Returns:
            Dict with process status
        """
        if not self.server:
            raise ConnectionError("Not connected to Supervisord")

        try:
            info = await asyncio.get_event_loop().run_in_executor(
                None, self.server.supervisor.getProcessInfo, name
            )
            self.logger.debug(f"Got status for process {name}")
            return {"status": "ok", "process": info}
        except Exception as e:
            self.logger.error(f"Failed to get status for process {name}: {e}")
            return {"status": "error", "message": str(e)}

    async def get_logs(self, name: str, lines: int = 100, stderr: bool = False) -> dict[str, Any]:
        """Get logs for a process.

        Args:
            name: Process name
            lines: Number of lines to retrieve
            stderr: Whether to get stderr logs

        Returns:
            Dict with logs
        """
        if not self.server:
            raise ConnectionError("Not connected to Supervisord")

        try:
            if stderr:
                logs = await asyncio.get_event_loop().run_in_executor(
                    None, self.server.supervisor.readProcessStderrLog, name, -lines, 0
                )
            else:
                logs = await asyncio.get_event_loop().run_in_executor(
                    None, self.server.supervisor.readProcessStdoutLog, name, -lines, 0
                )

            log_lines = str(logs).split("\n") if logs else []
            self.logger.debug(f"Retrieved {len(log_lines)} log lines for process {name}")
            return {"status": "ok", "logs": log_lines}
        except Exception as e:
            self.logger.error(f"Failed to get logs for process {name}: {e}")
            return {"status": "error", "message": str(e)}

    async def get_system_info(self) -> dict[str, Any]:
        """Get Supervisord system information.

        Returns:
            Dict with system information
        """
        if not self.server:
            raise ConnectionError("Not connected to Supervisord")

        try:
            api_version = await asyncio.get_event_loop().run_in_executor(
                None, self.server.supervisor.getAPIVersion
            )
            supervisor_version = await asyncio.get_event_loop().run_in_executor(
                None, self.server.supervisor.getSupervisorVersion
            )
            state = await asyncio.get_event_loop().run_in_executor(
                None, self.server.supervisor.getState
            )

            info = {
                "api_version": api_version,
                "supervisor_version": supervisor_version,
                "state": state,
                "server_url": self.server_url,
            }

            self.logger.debug("Retrieved system information")
            return {"status": "ok", "info": info}
        except Exception as e:
            self.logger.error(f"Failed to get system info: {e}")
            return {"status": "error", "message": str(e)}

    async def reload_config(self) -> dict[str, Any]:
        """Reload Supervisord configuration.

        Returns:
            Dict with operation result
        """
        if not self.server:
            raise ConnectionError("Not connected to Supervisord")

        try:
            result = await asyncio.get_event_loop().run_in_executor(
                None, self.server.supervisor.reloadConfig
            )
            self.logger.info("Reloaded Supervisord configuration")
            return {"status": "ok", "message": "Configuration reloaded", "result": result}
        except Exception as e:
            self.logger.error(f"Failed to reload configuration: {e}")
            return {"status": "error", "message": str(e)}
