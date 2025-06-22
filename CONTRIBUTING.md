# Contributing to Supervisord MCP

Thank you for your interest in contributing to Supervisord MCP! This document provides guidelines and information for contributors.

## Table of Contents

- [Code of Conduct](#code-of-conduct)
- [Getting Started](#getting-started)
- [Development Process](#development-process)
- [Submitting Changes](#submitting-changes)
- [Coding Standards](#coding-standards)
- [Testing Guidelines](#testing-guidelines)
- [Documentation](#documentation)
- [Community](#community)

## Code of Conduct

This project and everyone participating in it is governed by our Code of Conduct. By participating, you are expected to uphold this code.

### Our Pledge

We are committed to making participation in this project a harassment-free experience for everyone, regardless of age, body size, disability, ethnicity, gender identity and expression, level of experience, nationality, personal appearance, race, religion, or sexual identity and orientation.

### Our Standards

Examples of behavior that contributes to creating a positive environment include:

- Using welcoming and inclusive language
- Being respectful of differing viewpoints and experiences
- Gracefully accepting constructive criticism
- Focusing on what is best for the community
- Showing empathy towards other community members

## Getting Started

### Prerequisites

- Python 3.10 or higher
- [uv](https://docs.astral.sh/uv/) for dependency management
- Git
- Supervisord installed

### Development Setup

1. **Fork the repository** on GitHub

2. **Clone your fork:**
   ```bash
   git clone https://github.com/YOUR_USERNAME/supervisord-mcp.git
   cd supervisord-mcp
   ```

3. **Add upstream remote:**
   ```bash
   git remote add upstream https://github.com/aether-platform/supervisord-mcp.git
   ```

4. **Install dependencies:**
   ```bash
   uv sync --extra dev
   ```

5. **Install pre-commit hooks:**
   ```bash
   uv run pre-commit install
   ```

6. **Verify installation:**
   ```bash
   uv run supervisord-mcp --help
   uv run pytest tests/ -v
   ```

## Development Process

### Branching Strategy

We use a simplified Git flow:

- `main`: Stable, production-ready code
- `feature/*`: New features
- `fix/*`: Bug fixes
- `docs/*`: Documentation updates

### Working on Issues

1. **Find an issue** to work on or create a new one
2. **Assign yourself** to the issue
3. **Create a branch:**
   ```bash
   git checkout -b feature/issue-description
   ```
4. **Make your changes**
5. **Test thoroughly**
6. **Submit a pull request**

### Keeping Your Fork Updated

```bash
git checkout main
git fetch upstream
git merge upstream/main
git push origin main
```

## Submitting Changes

### Pull Request Process

1. **Update your branch:**
   ```bash
   git checkout main
   git pull upstream main
   git checkout your-feature-branch
   git rebase main
   ```

2. **Run quality checks:**
   ```bash
   # Format code
   uv run ruff format src/ tests/
   
   # Lint code
   uv run ruff check src/ tests/
   
   # Type check
   uv run mypy src/
   
   # Run tests
   uv run pytest tests/ -v
   ```

3. **Commit your changes:**
   ```bash
   git add .
   git commit -m "feat: add awesome new feature"
   ```

4. **Push to your fork:**
   ```bash
   git push origin your-feature-branch
   ```

5. **Create a pull request** on GitHub

### Pull Request Guidelines

- **Clear title**: Use descriptive titles that explain the change
- **Detailed description**: Explain what changes were made and why
- **Link issues**: Reference any related issues
- **Screenshots**: Include screenshots for UI changes
- **Tests**: Ensure all tests pass
- **Documentation**: Update documentation as needed

### Commit Message Format

We follow [Conventional Commits](https://conventionalcommits.org/):

```
<type>[optional scope]: <description>

[optional body]

[optional footer(s)]
```

**Types:**
- `feat`: New feature
- `fix`: Bug fix
- `docs`: Documentation only changes
- `style`: Changes that do not affect the meaning of the code
- `refactor`: Code change that neither fixes a bug nor adds a feature
- `perf`: Performance improvement
- `test`: Adding missing tests or correcting existing tests
- `chore`: Changes to the build process or auxiliary tools

**Examples:**
```
feat: add support for process groups
fix: handle connection timeout errors gracefully
docs: update API documentation for new tools
test: add integration tests for MCP server
```

## Coding Standards

### Python Style Guide

We follow PEP 8 with some modifications enforced by our tools:

- **Line length**: 100 characters (configured in ruff)
- **Imports**: Use isort via ruff for import sorting
- **Formatting**: Use ruff format for code formatting
- **Type hints**: Use type hints for all public APIs

### Code Quality Tools

We use several tools to maintain code quality:

```bash
# Format code (automatic)
uv run ruff format src/ tests/

# Lint code (with auto-fix)
uv run ruff check --fix src/ tests/

# Type checking
uv run mypy src/

# All checks together
make quality  # if Makefile exists
```

### Best Practices

1. **Type Hints**: Use type hints for all function signatures
2. **Docstrings**: Write docstrings for public APIs
3. **Error Handling**: Use structured error responses
4. **Async/Await**: Use async/await for I/O operations
5. **Testing**: Write tests for new functionality
6. **Logging**: Use appropriate log levels

## Testing Guidelines

### Test Types

1. **Unit Tests**: Test individual functions and methods
2. **Integration Tests**: Test component interactions
3. **End-to-End Tests**: Test complete workflows

### Writing Tests

```python
import pytest
from unittest.mock import AsyncMock, Mock

@pytest.mark.asyncio
async def test_start_process_success():
    """Test successful process start."""
    manager = SupervisordManager()
    manager.server = Mock()
    
    with patch('asyncio.get_event_loop') as mock_loop:
        mock_loop.return_value.run_in_executor = AsyncMock(return_value=True)
        
        result = await manager.start_process("test_app")
        
        assert result["status"] == "ok"
        assert "started" in result["message"].lower()
```

### Running Tests

```bash
# Run all tests
uv run pytest tests/ -v

# Run specific test file
uv run pytest tests/test_manager.py -v

# Run with coverage
uv run pytest tests/ --cov=supervisord_mcp --cov-report=html

# Run integration tests (requires Supervisord)
uv run pytest tests/ -m integration
```

### Test Guidelines

- **Test Names**: Use descriptive test names
- **Test Structure**: Follow Arrange-Act-Assert pattern
- **Mock External Dependencies**: Mock XML-RPC calls and file operations
- **Test Edge Cases**: Test error conditions and edge cases
- **Fast Tests**: Keep tests fast and independent

## Documentation

### Types of Documentation

1. **API Documentation**: Function and class documentation
2. **User Guides**: How-to guides and tutorials
3. **Architecture Documentation**: System design and decisions
4. **Contributing Guide**: This document

### Documentation Standards

- **Clear Language**: Use clear, concise language
- **Examples**: Include code examples and usage samples
- **Up-to-Date**: Keep documentation synchronized with code
- **Comprehensive**: Cover all public APIs and features

### Building Documentation

```bash
# Install documentation dependencies
uv sync --extra docs

# Build documentation (if using Sphinx/MkDocs)
uv run mkdocs serve
```

## Community

### Communication Channels

- **GitHub Issues**: Bug reports, feature requests, questions
- **GitHub Discussions**: Community discussions, ideas, support
- **Pull Requests**: Code review and collaboration

### Getting Help

- **Documentation**: Check the docs directory first
- **Search Issues**: Look for existing issues before creating new ones
- **Ask Questions**: Use GitHub Discussions for questions
- **Be Specific**: Provide details, error messages, and context

### Code Review Process

1. **All changes require review** by at least one maintainer
2. **Constructive feedback** is encouraged and expected
3. **Address feedback** promptly and thoroughly
4. **Automated checks** must pass before merge
5. **Maintainers** have final say on architectural decisions

### Recognition

Contributors are recognized in several ways:

- **CONTRIBUTORS.md**: All contributors listed
- **Release Notes**: Significant contributions highlighted
- **GitHub**: Contributions visible on GitHub profiles

## Release Process

For maintainers, the release process is:

1. **Update version** in `pyproject.toml`
2. **Update CHANGELOG.md** with release notes
3. **Create release tag:**
   ```bash
   git tag -a v1.x.x -m "Release v1.x.x"
   git push origin v1.x.x
   ```
4. **GitHub Actions** automatically builds and publishes to PyPI

## Questions?

If you have questions about contributing, please:

1. **Search existing issues** and discussions
2. **Check the documentation** in the `docs/` directory
3. **Open a discussion** on GitHub
4. **Contact maintainers** through GitHub

Thank you for contributing to Supervisord MCP! 🎉