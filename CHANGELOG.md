# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [1.1.0] - 2026-11-22

### Fixed
- Pin the MCP SDK to `mcp>=1.30,<2`. Without an upper bound a fresh install resolved
  `mcp` 2.x and the server crashed on startup (`'Server' object has no attribute 'list_tools'`).
- Logging now goes to stderr. Previously log lines were written to stdout and corrupted
  the MCP stdio JSON-RPC stream.
- `get_system_info` no longer returns Basic auth credentials embedded in the server URL.
  Credentials are also redacted from error messages and logs.
- `get_logs` is bounded: it uses `tailProcess*Log` with a byte window (`max_bytes`,
  default 16 KiB, max 256 KiB) and returns at most `lines` trailing lines (max 1000).
  Previously `lines` was passed as a byte offset, so large or negative values returned
  the whole log.
- Tool failures are returned with `isError: true` instead of a success result.
- mypy errors that kept CI red since 2026-03.

### Added
- `SUPERVISORD_URL`, `SUPERVISORD_USERNAME`, `SUPERVISORD_PASSWORD` environment
  variables (and `--username` / `--password` options).
- `max_bytes` argument for the `get_logs` tool.
- Regression tests, including an end-to-end stdio test against a real supervisord.

### Changed
- `add_process` validates the process name and its "configuration prepared" result is
  no longer shown as an error.
- `__version__` is read from the installed package metadata.

### Removed
- Unused runtime dependencies `supervisor` and `psutil`, and the unused `logging` extra.

## [1.0.1] - 2025-06-22

### Changed
- Updated release workflow to use GitHub Actions PyPI publish action
- Replaced manual twine dependency with `pypa/gh-action-pypi-publish@release/v1`
- Improved release process consistency with circus-mcp
- Enhanced GitHub release notes with detailed installation instructions
- Split release workflow into separate build, GitHub release, and PyPI publish jobs

### Removed
- Manual twine dependency from dev requirements

### Technical
- Streamlined CI/CD pipeline for better reliability
- Added proper artifact handling between workflow jobs
- Improved release automation and consistency

## [1.0.0] - 2025-06-22

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