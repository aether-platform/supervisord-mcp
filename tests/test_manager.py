"""
Tests for SupervisordManager.
"""

import xmlrpc.client
from unittest.mock import AsyncMock, Mock, patch

import pytest

from supervisord_mcp.manager import SupervisordManager


@pytest.fixture
def manager():
    """Create a SupervisordManager instance for testing."""
    return SupervisordManager("http://localhost:9001/RPC2")


@pytest.mark.asyncio
async def test_connect_success(manager):
    """Test successful connection to Supervisord."""
    with patch("xmlrpc.client.ServerProxy") as mock_proxy:
        mock_server = Mock()
        mock_server.supervisor.getAPIVersion.return_value = "3.0"
        mock_proxy.return_value = mock_server

        with patch("asyncio.get_event_loop") as mock_loop:
            mock_loop.return_value.run_in_executor = AsyncMock(return_value="3.0")

            result = await manager.connect()

            assert result is True
            assert manager.server is not None


@pytest.mark.asyncio
async def test_connect_failure(manager):
    """Test connection failure to Supervisord."""
    with patch("xmlrpc.client.ServerProxy") as mock_proxy:
        mock_proxy.side_effect = ConnectionError("Connection refused")

        result = await manager.connect()

        assert result is False
        assert manager.server is None


@pytest.mark.asyncio
async def test_start_process_success(manager):
    """Test successful process start."""
    manager.server = Mock()

    with patch("asyncio.get_event_loop") as mock_loop:
        mock_loop.return_value.run_in_executor = AsyncMock(return_value=True)

        result = await manager.start_process("test_app")

        assert result["status"] == "ok"
        assert "started" in result["message"].lower()


@pytest.mark.asyncio
async def test_start_process_not_connected(manager):
    """Test process start without connection."""
    with pytest.raises(ConnectionError):
        await manager.start_process("test_app")


@pytest.mark.asyncio
async def test_start_process_failure(manager):
    """Test process start failure."""
    manager.server = Mock()

    with patch("asyncio.get_event_loop") as mock_loop:
        mock_loop.return_value.run_in_executor = AsyncMock(
            side_effect=xmlrpc.client.Fault(10, "ALREADY_STARTED")
        )

        result = await manager.start_process("test_app")

        assert result["status"] == "error"
        assert "ALREADY_STARTED" in result["message"]


@pytest.mark.asyncio
async def test_stop_process_success(manager):
    """Test successful process stop."""
    manager.server = Mock()

    with patch("asyncio.get_event_loop") as mock_loop:
        mock_loop.return_value.run_in_executor = AsyncMock(return_value=True)

        result = await manager.stop_process("test_app")

        assert result["status"] == "ok"
        assert "stopped" in result["message"].lower()


@pytest.mark.asyncio
async def test_restart_process_success(manager):
    """Test successful process restart."""
    manager.server = Mock()

    with patch("asyncio.get_event_loop") as mock_loop:
        mock_loop.return_value.run_in_executor = AsyncMock(return_value=True)

        result = await manager.restart_process("test_app")

        assert result["status"] == "ok"
        assert "restarted" in result["message"].lower()


@pytest.mark.asyncio
async def test_list_processes_success(manager):
    """Test successful process listing."""
    manager.server = Mock()

    mock_processes = [
        {"name": "test_app", "statename": "RUNNING", "pid": 1234},
        {"name": "test_worker", "statename": "STOPPED", "pid": 0},
    ]

    with patch("asyncio.get_event_loop") as mock_loop:
        mock_loop.return_value.run_in_executor = AsyncMock(return_value=mock_processes)

        result = await manager.list_processes()

        assert result["status"] == "ok"
        assert len(result["processes"]) == 2
        assert result["processes"][0]["name"] == "test_app"


@pytest.mark.asyncio
async def test_get_process_status_success(manager):
    """Test successful process status retrieval."""
    manager.server = Mock()

    mock_process = {
        "name": "test_app",
        "statename": "RUNNING",
        "pid": 1234,
        "description": "pid 1234, uptime 0:01:23",
    }

    with patch("asyncio.get_event_loop") as mock_loop:
        mock_loop.return_value.run_in_executor = AsyncMock(return_value=mock_process)

        result = await manager.get_process_status("test_app")

        assert result["status"] == "ok"
        assert result["process"]["name"] == "test_app"
        assert result["process"]["statename"] == "RUNNING"


@pytest.mark.asyncio
async def test_get_logs_stdout_success(manager):
    """Test successful stdout log retrieval."""
    manager.server = Mock()

    mock_logs = "Log line 1\nLog line 2\nLog line 3"

    with patch("asyncio.get_event_loop") as mock_loop:
        mock_loop.return_value.run_in_executor = AsyncMock(return_value=mock_logs)

        result = await manager.get_logs("test_app", lines=10, stderr=False)

        assert result["status"] == "ok"
        assert len(result["logs"]) == 3
        assert result["logs"][0] == "Log line 1"


@pytest.mark.asyncio
async def test_get_logs_stderr_success(manager):
    """Test successful stderr log retrieval."""
    manager.server = Mock()

    mock_logs = "Error line 1\nError line 2"

    with patch("asyncio.get_event_loop") as mock_loop:
        mock_loop.return_value.run_in_executor = AsyncMock(return_value=mock_logs)

        result = await manager.get_logs("test_app", lines=10, stderr=True)

        assert result["status"] == "ok"
        assert len(result["logs"]) == 2
        assert result["logs"][0] == "Error line 1"


@pytest.mark.asyncio
async def test_get_system_info_success(manager):
    """Test successful system info retrieval."""
    manager.server = Mock()

    with patch("asyncio.get_event_loop") as mock_loop:
        mock_loop.return_value.run_in_executor = AsyncMock(
            side_effect=["3.0", "4.2.4", {"statename": "RUNNING"}]
        )

        result = await manager.get_system_info()

        assert result["status"] == "ok"
        assert result["info"]["api_version"] == "3.0"
        assert result["info"]["supervisor_version"] == "4.2.4"
        assert result["info"]["state"]["statename"] == "RUNNING"


@pytest.mark.asyncio
async def test_reload_config_success(manager):
    """Test successful configuration reload."""
    manager.server = Mock()

    with patch("asyncio.get_event_loop") as mock_loop:
        mock_loop.return_value.run_in_executor = AsyncMock(return_value=[[], [], []])

        result = await manager.reload_config()

        assert result["status"] == "ok"
        assert "reloaded" in result["message"].lower()


@pytest.mark.asyncio
async def test_add_process_warning(manager):
    """Test add_process returns warning about manual configuration."""
    manager.server = Mock()

    result = await manager.add_process("test_app", "python app.py")

    assert result["status"] == "warning"
    assert "supervisord.conf" in result["message"]
    assert "config" in result
