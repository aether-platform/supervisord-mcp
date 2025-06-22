# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.0.0] - 2024-06-22

### Added
- Initial release of Supervisord MCP
- Core process management functionality via Supervisord XML-RPC API
- MCP (Model Context Protocol) server integration for AI agents
- CLI interface for direct process management
- Support for process start, stop, restart operations
- Process status monitoring and listing
- Log retrieval (stdout/stderr) with configurable line limits
- System information reporting
- Configuration reload functionality
- Comprehensive error handling and logging
- Async/await support throughout the codebase
- Professional CLI with click framework
- Detailed documentation and examples

### Features
- **Process Control**: Start, stop, restart processes managed by Supervisord
- **Status Monitoring**: Real-time process status and system information
- **Log Management**: Retrieve and display process logs with filtering options
- **AI Integration**: Full MCP protocol support for AI coding agents
- **CLI Interface**: User-friendly command-line interface
- **Configuration**: Support for custom Supervisord server URLs
- **Error Handling**: Robust error handling with informative messages

### MCP Tools
- `add_process`: Add new process configuration (requires manual config reload)
- `start_process`: Start a configured process
- `stop_process`: Stop a running process
- `restart_process`: Restart a process
- `list_processes`: List all processes with status
- `get_process_status`: Get detailed status for specific process
- `get_logs`: Retrieve process logs with options
- `get_system_info`: Get Supervisord system information
- `reload_config`: Reload Supervisord configuration

### CLI Commands
- `supervisord-mcp start <name>`: Start a process
- `supervisord-mcp stop <name>`: Stop a process
- `supervisord-mcp restart <name>`: Restart a process
- `supervisord-mcp status <name>`: Get process status
- `supervisord-mcp list-processes`: List all processes
- `supervisord-mcp logs <name>`: Get process logs
- `supervisord-mcp info`: Get system information
- `supervisord-mcp reload`: Reload configuration
- `supervisord-mcp mcp`: Start MCP server for AI integration

### Technical Details
- Built on Supervisord XML-RPC API
- Async/await architecture for non-blocking operations
- Type hints throughout codebase
- Comprehensive test coverage support
- Production-ready error handling
- Logging configuration with verbosity control