# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Supervisord MCP is a process management system that integrates Supervisord with the Model Context Protocol (MCP). It enables AI agents to control production and development processes through standardized MCP tools and resources.

## Architecture

The system follows a clean architecture pattern:

```
CLI → Manager → Supervisord XML-RPC API
MCP Server → Manager → Supervisord XML-RPC API
```

Key components:
- **SupervisordManager**: Core business logic for Supervisord operations via XML-RPC
- **SupervisordMCPServer**: MCP protocol implementation for AI agent communication
- **CLI**: Command-line interface using Click framework
- **Async Architecture**: All operations are async for better performance

## Development Commands

### Installation and Setup
```bash
# Install dependencies with uv
uv sync

# Install development dependencies
uv sync --extra dev

# Install in development mode
uv pip install -e .
```

### Running the Application
```bash
# Start MCP server (main application for AI agents)
uv run supervisord-mcp mcp

# Use CLI interface
uv run supervisord-mcp start myapp
uv run supervisord-mcp list-processes
uv run supervisord-mcp logs myapp

# With custom server URL
uv run supervisord-mcp --server-url http://remote:9001/RPC2 info
```

### Testing
```bash
# Run all tests
uv run pytest tests/ -v

# Run with coverage
uv run pytest tests/ --cov=supervisord_mcp --cov-report=html

# Run integration tests (requires running Supervisord)
uv run pytest tests/ -m integration
```

### Code Quality
```bash
# Format code
uv run ruff format src/ tests/

# Lint code
uv run ruff check src/ tests/

# Type checking
uv run mypy src/
```

## Configuration

### Supervisord Setup
The system requires a running Supervisord instance with XML-RPC interface enabled:

```ini
[inet_http_server]
port=127.0.0.1:9001

[rpcinterface:supervisor]
supervisor.rpcinterface_factory = supervisor.rpcinterface:make_main_rpcinterface
```

### Process Configuration
Processes are defined in standard Supervisord configuration files:

```ini
[program:webapp]
command=gunicorn app:application
directory=/app
numprocs=1
autostart=true
autorestart=true
```

## Key Development Patterns

### Async/Await Architecture
All I/O operations use async/await for non-blocking execution:
```python
async def start_process(self, name: str) -> Dict[str, Any]:
    result = await asyncio.get_event_loop().run_in_executor(
        None, self.server.supervisor.startProcess, name
    )
```

### Error Handling
Consistent error handling with structured responses:
```python
try:
    # Operation
    return {"status": "ok", "message": "Success"}
except Exception as e:
    return {"status": "error", "message": str(e)}
```

### XML-RPC Integration
All Supervisord operations go through XML-RPC client:
```python
self.server = xmlrpc.client.ServerProxy(self.server_url)
```

## MCP Integration

The system exposes MCP tools for AI agents:
- **Process Control**: `start_process`, `stop_process`, `restart_process`
- **Status Monitoring**: `list_processes`, `get_process_status`
- **Log Management**: `get_logs`
- **System Operations**: `get_system_info`, `reload_config`

## Testing Strategy

- **Unit Tests**: Test individual components and business logic
- **Integration Tests**: Test against real Supervisord instance
- **MCP Protocol Tests**: Validate MCP tool functionality
- **CLI Tests**: Test command-line interface

## Limitations and Notes

1. **Process Addition**: Supervisord doesn't support dynamic process addition via XML-RPC. New processes must be added to configuration files and reloaded.

2. **Authentication**: Currently supports basic HTTP authentication. For production, consider secure authentication methods.

3. **Logging**: Process logs are retrieved from Supervisord's log buffers, not directly from log files.

4. **Platform Support**: Works on any platform where Python and Supervisord are available.

## Development Tips

1. **Testing with Real Supervisord**: For integration testing, start a local Supervisord instance with test configuration.

2. **MCP Development**: Use the MCP protocol stdio transport for AI agent integration.

3. **Error Handling**: Always handle XML-RPC exceptions gracefully and return structured responses.

4. **Performance**: Use async/await consistently to avoid blocking operations.

5. **Configuration**: Test with different Supervisord configurations to ensure compatibility.