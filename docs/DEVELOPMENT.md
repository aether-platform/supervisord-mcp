# Development Guide

This guide covers development setup, testing, and contribution guidelines for Supervisord MCP.

## Development Setup

### Prerequisites

- Python 3.10 or higher
- [uv](https://docs.astral.sh/uv/) for dependency management
- Supervisord installed and configured
- Git for version control

### Environment Setup

1. **Clone the repository:**
```bash
git clone https://github.com/aether-platform/supervisord-mcp.git
cd supervisord-mcp
```

2. **Install dependencies:**
```bash
# Install all dependencies including dev tools
uv sync --extra dev

# Install package in development mode
uv pip install -e .
```

3. **Setup Supervisord:**
```bash
# Install supervisor
pip install supervisor

# Copy example configuration
cp supervisord.conf /etc/supervisor/supervisord.conf

# Start supervisord daemon
supervisord -c /etc/supervisor/supervisord.conf
```

4. **Verify installation:**
```bash
# Test CLI
uv run supervisord-mcp --help

# Test connection to Supervisord
uv run supervisord-mcp info
```

## Development Workflow

### Code Organization

```
src/supervisord_mcp/
├── __init__.py          # Package initialization
├── manager.py           # Core Supervisord operations
├── mcp_server.py        # MCP protocol implementation
├── cli.py              # Command-line interface
└── main.py             # Entry point
```

### Key Components

1. **SupervisordManager** (`manager.py`)
   - Core business logic
   - XML-RPC client for Supervisord communication
   - Async operations with proper error handling

2. **SupervisordMCPServer** (`mcp_server.py`)
   - MCP protocol implementation
   - Tool definitions for AI agents
   - Response formatting

3. **CLI** (`cli.py`)
   - Click-based command-line interface
   - User-friendly process management
   - Error handling and output formatting

### Running Tests

```bash
# Run all tests
uv run pytest tests/ -v

# Run with coverage
uv run pytest tests/ --cov=supervisord_mcp --cov-report=html

# Run specific test files
uv run pytest tests/test_manager.py -v

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

# Run all quality checks
uv run ruff check src/ tests/ && \
uv run ruff format --check src/ tests/ && \
uv run mypy src/
```

### Testing Strategy

1. **Unit Tests**: Test individual functions and methods
2. **Integration Tests**: Test with real Supervisord instance
3. **MCP Protocol Tests**: Validate MCP tool functionality
4. **CLI Tests**: Test command-line interface

### Integration Testing Setup

For integration tests, you need a running Supervisord instance:

```bash
# Create test configuration
cat > test_supervisord.conf << EOF
[unix_http_server]
file=/tmp/supervisor_test.sock

[supervisord]
logfile=/tmp/supervisord_test.log
pidfile=/tmp/supervisord_test.pid
nodaemon=false

[rpcinterface:supervisor]
supervisor.rpcinterface_factory = supervisor.rpcinterface:make_main_rpcinterface

[inet_http_server]
port=127.0.0.1:9002

[program:test_app]
command=python -c "import time; [print(f'Hello {i}') or time.sleep(1) for i in range(100)]"
autostart=false
autorestart=false
EOF

# Start test Supervisord
supervisord -c test_supervisord.conf

# Run integration tests
uv run pytest tests/ -m integration --server-url http://localhost:9002/RPC2

# Stop test Supervisord
supervisorctl -c test_supervisord.conf shutdown
```

## Contributing

### Pull Request Process

1. **Fork the repository**
2. **Create a feature branch:**
   ```bash
   git checkout -b feature/your-feature-name
   ```

3. **Make your changes:**
   - Write tests for new functionality
   - Update documentation as needed
   - Follow code style guidelines

4. **Run quality checks:**
   ```bash
   uv run ruff check src/ tests/
   uv run ruff format src/ tests/
   uv run mypy src/
   uv run pytest tests/ -v
   ```

5. **Commit your changes:**
   ```bash
   git add .
   git commit -m "feat: add your feature description"
   ```

6. **Push and create PR:**
   ```bash
   git push origin feature/your-feature-name
   ```

### Commit Message Guidelines

Follow [Conventional Commits](https://conventionalcommits.org/):

- `feat:` New features
- `fix:` Bug fixes
- `docs:` Documentation updates
- `test:` Test additions/updates
- `refactor:` Code refactoring
- `style:` Code style changes
- `chore:` Maintenance tasks

### Code Style Guidelines

- Use type hints for all functions and methods
- Write docstrings for public APIs
- Follow PEP 8 style guidelines
- Use async/await for I/O operations
- Handle errors gracefully with structured responses

## Architecture Decisions

### XML-RPC vs Direct API

We chose XML-RPC for Supervisord communication because:
- It's the standard Supervisord interface
- Provides reliable process management operations
- Supports remote supervision scenarios
- Well-documented and stable API

### Async Architecture

All I/O operations use async/await because:
- Non-blocking operations for better performance
- Consistent with MCP protocol requirements
- Better resource utilization
- Future-proof for concurrent operations

### Error Handling Strategy

Structured error responses with:
```python
{
    "status": "ok" | "error" | "warning",
    "message": "Human-readable message",
    "data": {...}  # Optional additional data
}
```

This provides:
- Consistent error handling across components
- Machine-readable status indicators
- Human-friendly error messages
- Structured data for programmatic use

## Debugging

### Enable Verbose Logging

```bash
# CLI with verbose output
uv run supervisord-mcp --verbose list-processes

# Python logging
import logging
logging.basicConfig(level=logging.DEBUG)
```

### Common Issues

1. **Connection Refused**: Ensure Supervisord is running with inet_http_server enabled
2. **Process Not Found**: Check process is configured in supervisord.conf
3. **Permission Denied**: Ensure proper user permissions for Supervisord operations

### Development Tools

- **MCP Inspector**: Use for testing MCP protocol integration
- **Supervisorctl**: Standard Supervisord CLI for comparison
- **XML-RPC Client**: For direct API testing

```python
import xmlrpc.client
server = xmlrpc.client.ServerProxy('http://localhost:9001/RPC2')
print(server.supervisor.getAllProcessInfo())
```

## Release Process

1. **Update version in pyproject.toml**
2. **Update CHANGELOG.md**
3. **Create release tag:**
   ```bash
   git tag -a v1.0.1 -m "Release v1.0.1"
   git push origin v1.0.1
   ```
4. **GitHub Actions will automatically build and publish to PyPI**

## Support

- **GitHub Issues**: [Bug reports and feature requests](https://github.com/aether-platform/supervisord-mcp/issues)
- **GitHub Discussions**: [Community support](https://github.com/aether-platform/supervisord-mcp/discussions)
- **Documentation**: [Project documentation](https://github.com/aether-platform/supervisord-mcp/docs)