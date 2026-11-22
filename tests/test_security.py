"""
Regression tests for the 1.1.0 security fixes (credential redaction, bounded logs,
isError reporting).
"""

import logging
from unittest.mock import Mock

import pytest
from mcp import types

from supervisord_mcp.cli import setup_logging
from supervisord_mcp.manager import (
    MAX_LOG_BYTES,
    MAX_LOG_LINES,
    SupervisordManager,
    split_credentials,
)
from supervisord_mcp.mcp_server import SupervisordMCPServer

SECRET = "S3cret/PW@x"
URL_WITH_CREDS = "http://audituser:S3cret%2FPW%40x@127.0.0.1:19001/RPC2"


def test_split_credentials_strips_userinfo():
    clean, user, password = split_credentials(URL_WITH_CREDS)
    assert clean == "http://127.0.0.1:19001/RPC2"
    assert user == "audituser"
    assert password == SECRET


def test_split_credentials_without_userinfo():
    assert split_credentials("http://localhost:9001/RPC2") == (
        "http://localhost:9001/RPC2",
        None,
        None,
    )


def test_manager_never_stores_credentials_in_server_url():
    manager = SupervisordManager(URL_WITH_CREDS)
    assert manager.server_url == "http://127.0.0.1:19001/RPC2"
    assert SECRET not in manager.server_url
    # but the transport still authenticates
    assert "audituser:S3cret%2FPW%40x@" in manager._proxy_url()


def test_explicit_credentials_take_precedence():
    manager = SupervisordManager("http://u:old@h:1/RPC2", username="new", password="pw2")
    assert manager._proxy_url() == "http://new:pw2@h:1/RPC2"


def test_redact_removes_raw_and_quoted_password():
    manager = SupervisordManager(URL_WITH_CREDS)
    text = f"<ProtocolError for audituser:S3cret%2FPW%40x@127.0.0.1/RPC2> raw={SECRET}"
    redacted = manager.redact(text)
    assert SECRET not in redacted
    assert "S3cret%2FPW%40x" not in redacted


@pytest.mark.asyncio
async def test_get_system_info_does_not_return_password():
    manager = SupervisordManager(URL_WITH_CREDS)
    manager.server = Mock()
    manager.server.supervisor.getAPIVersion.return_value = "3.0"
    manager.server.supervisor.getSupervisorVersion.return_value = "4.2.5"
    manager.server.supervisor.getState.return_value = {"statename": "RUNNING"}

    result = await manager.get_system_info()

    assert result["status"] == "ok"
    assert SECRET not in repr(result)
    assert "S3cret" not in repr(result)
    assert result["info"]["authentication"] == "configured"


@pytest.mark.asyncio
async def test_error_messages_are_redacted():
    manager = SupervisordManager(URL_WITH_CREDS)
    manager.server = Mock()
    manager.server.supervisor.startProcess.side_effect = Exception(
        "ProtocolError for audituser:S3cret%2FPW%40x@127.0.0.1:19001/RPC2: 401"
    )
    result = await manager.start_process("x")
    assert result["status"] == "error"
    assert "S3cret" not in result["message"]


@pytest.mark.parametrize("lines", [0, -10, MAX_LOG_LINES + 1, 5_000_000, True, "10"])
@pytest.mark.asyncio
async def test_get_logs_rejects_out_of_range_lines(lines):
    manager = SupervisordManager()
    manager.server = Mock()
    result = await manager.get_logs("app", lines=lines)
    assert result["status"] == "error"
    manager.server.supervisor.tailProcessStdoutLog.assert_not_called()


@pytest.mark.parametrize("max_bytes", [0, -1, MAX_LOG_BYTES + 1])
@pytest.mark.asyncio
async def test_get_logs_rejects_out_of_range_bytes(max_bytes):
    manager = SupervisordManager()
    manager.server = Mock()
    result = await manager.get_logs("app", max_bytes=max_bytes)
    assert result["status"] == "error"


@pytest.mark.asyncio
async def test_get_logs_uses_tail_api_with_byte_limit():
    manager = SupervisordManager()
    manager.server = Mock()
    manager.server.supervisor.tailProcessStdoutLog.return_value = ["a\nb\nc\n", 6, False]

    result = await manager.get_logs("app", lines=2, max_bytes=1024)

    manager.server.supervisor.tailProcessStdoutLog.assert_called_once_with("app", 0, 1024)
    assert result["logs"] == ["b", "c"]
    assert result["truncated"] is True


@pytest.mark.asyncio
async def test_get_logs_drops_partial_first_line_on_overflow():
    manager = SupervisordManager()
    manager.server = Mock()
    manager.server.supervisor.tailProcessStderrLog.return_value = ["ial\nfull\n", 99, True]

    result = await manager.get_logs("app", stderr=True)

    assert result["logs"] == ["full"]
    assert result["truncated"] is True


@pytest.mark.asyncio
async def test_get_logs_caps_oversized_daemon_response():
    manager = SupervisordManager()
    manager.server = Mock()
    manager.server.supervisor.tailProcessStdoutLog.return_value = ["x" * 10_000, 0, False]

    result = await manager.get_logs("app", lines=10, max_bytes=100)

    assert sum(len(line) for line in result["logs"]) <= 100


def test_setup_logging_uses_stderr():
    setup_logging()
    handlers = logging.getLogger().handlers
    assert handlers
    import sys

    assert all(getattr(h, "stream", None) is not sys.stdout for h in handlers)


async def _call_tool(server: SupervisordMCPServer, name: str, args: dict) -> types.CallToolResult:
    handler = server.server.request_handlers[types.CallToolRequest]
    request = types.CallToolRequest(
        method="tools/call", params=types.CallToolRequestParams(name=name, arguments=args)
    )
    result = await handler(request)
    assert isinstance(result.root, types.CallToolResult)
    return result.root


@pytest.mark.asyncio
async def test_tool_errors_are_reported_with_is_error():
    server = SupervisordMCPServer(URL_WITH_CREDS)
    server.manager.connect = Mock(side_effect=_async_true)  # type: ignore[method-assign]
    server.manager.server = Mock()
    server.manager.server.supervisor.startProcess.side_effect = Exception(
        "BAD_NAME: nope (audituser:S3cret%2FPW%40x@127.0.0.1)"
    )

    result = await _call_tool(server, "start_process", {"name": "nope"})

    assert result.isError is True
    text = result.content[0].text  # type: ignore[union-attr]
    assert "BAD_NAME" in text
    assert "S3cret" not in text


@pytest.mark.asyncio
async def test_get_logs_schema_rejects_huge_lines():
    server = SupervisordMCPServer()
    server.manager.connect = Mock(side_effect=_async_true)  # type: ignore[method-assign]
    server.manager.server = Mock()

    # list_tools must be called first so the SDK caches the input schema.
    await server.server.request_handlers[types.ListToolsRequest](
        types.ListToolsRequest(method="tools/list")
    )
    result = await _call_tool(server, "get_logs", {"name": "app", "lines": 5_000_000})

    assert result.isError is True
    server.manager.server.supervisor.tailProcessStdoutLog.assert_not_called()


@pytest.mark.asyncio
async def test_system_info_tool_hides_password():
    server = SupervisordMCPServer(URL_WITH_CREDS)
    server.manager.connect = Mock(side_effect=_async_true)  # type: ignore[method-assign]
    server.manager.server = Mock()
    server.manager.server.supervisor.getAPIVersion.return_value = "3.0"
    server.manager.server.supervisor.getSupervisorVersion.return_value = "4.2.5"
    server.manager.server.supervisor.getState.return_value = {"statename": "RUNNING"}

    result = await _call_tool(server, "get_system_info", {})

    assert result.isError is False
    text = result.content[0].text  # type: ignore[union-attr]
    assert "http://127.0.0.1:19001/RPC2" in text
    assert "S3cret" not in text
    assert "audituser" not in text


async def _async_true() -> bool:
    return True


def test_server_reports_package_version():
    from importlib.metadata import version

    assert SupervisordMCPServer().server.version == version("supervisord-mcp")
