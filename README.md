# Supervisord MCP

[![PyPI version](https://badge.fury.io/py/supervisord-mcp.svg)](https://badge.fury.io/py/supervisord-mcp)
[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

**Streamlined Supervisord process management with AI agent integration through the Model Context Protocol (MCP).**

Supervisord MCP provides coding agents with direct access to Supervisord process management through the Model Context Protocol. By offering standardized process control capabilities, it eliminates the complexity of shell command parsing and reduces token consumption for AI agents working in production and development environments.

## MCP Integration Sequence

```mermaid
sequenceDiagram
    participant Agent as AI Coding Agent
    participant MCP as Supervisord MCP Server
    participant Supervisord as Supervisord Daemon
    participant Process as Application Process

    Agent->>MCP: Request: start_process("webapp")
    MCP->>Supervisord: Start process via XML-RPC
    Supervisord->>Process: Launch application
    Process-->>Supervisord: Process started (PID: 1234)
    Supervisord-->>MCP: Process status: RUNNING
    MCP-->>Agent: {"status": "ok", "message": "Process started"}

    Agent->>MCP: Request: get_logs("webapp", lines=50)
    MCP->>Supervisord: Fetch stdout/stderr logs
    Supervisord-->>MCP: Log entries
    MCP-->>Agent: {"status": "ok", "logs": ["Application started..."]}
```

## What is Supervisord MCP?

Supervisord MCP enables AI coding agents to work more efficiently with production process management, contributing to better deployment reliability and operational efficiency.

Supervisord MCP provides direct process control through the Model Context Protocol, eliminating the overhead of shell commands and reducing token consumption for AI agents managing production and development environments.

**Core Features**:
- **AI Integration**: Built-in MCP protocol support for coding agents
- **Production Ready**: Based on battle-tested Supervisord process manager
- **Real-time Monitoring**: Process status and log access
- **Robust Operations**: Reliable process lifecycle management

## Quick Start

### Installation

```bash
uv add supervisord-mcp
```

### Basic Usage

```bash
# Start a process (requires it to be configured in supervisord.conf)
uv run supervisord-mcp start webapp

# Check what's running
uv run supervisord-mcp list-processes

# View logs
uv run supervisord-mcp logs webapp

# Get system information
uv run supervisord-mcp info
```

## Key Features

### 🚀 Process Management Made Easy

```bash
# Start/stop/restart processes
uv run supervisord-mcp start api
uv run supervisord-mcp stop api
uv run supervisord-mcp restart api

# Get detailed status
uv run supervisord-mcp status api
```

### 📊 Comprehensive Monitoring

```bash
# List all processes with status
uv run supervisord-mcp list-processes

# View real-time logs
uv run supervisord-mcp logs api --lines 100
uv run supervisord-mcp logs api --stderr

# System information
uv run supervisord-mcp info
```

### 🤖 AI Agent Integration

Supervisord MCP includes built-in MCP protocol support, allowing AI agents to manage your processes:

```bash
# Start MCP server for AI integration
uv run supervisord-mcp mcp
```

Configure in your AI agent using the **recommended stdio transport**:
```json
{
  "mcpServers": {
    "supervisord-mcp": {
      "command": "uv",
      "args": ["run", "supervisord-mcp", "mcp"],
      "cwd": "/path/to/your/project"
    }
  }
}
```

For different project setups:
```json
{
  "mcpServers": {
    "supervisord-mcp": {
      "command": "uv",
      "args": ["run", "supervisord-mcp", "mcp"],
      "cwd": "/app"
    }
  }
}
```

**Note**: This tool is designed for production and development environments using MCP's stdio transport method as specified in the [MCP documentation](https://modelcontextprotocol.io/). This approach provides secure, direct communication between AI agents and the process manager.

## Common Use Cases

### Production Web Application

```bash
# Configure in supervisord.conf:
[program:webapp]
command=gunicorn app:application
directory=/app
numprocs=4
autostart=true
autorestart=true

# Then manage via Supervisord MCP:
uv run supervisord-mcp start webapp
uv run supervisord-mcp logs webapp
```

### Development Environment

```bash
# Configure multiple services in supervisord.conf:
[program:frontend]
command=npm run dev
directory=/app/frontend
autostart=false

[program:backend]
command=python manage.py runserver
directory=/app/backend
autostart=false

# Manage the stack:
uv run supervisord-mcp start frontend
uv run supervisord-mcp start backend
uv run supervisord-mcp list-processes
```

### Microservices

```bash
# Multiple services configured in supervisord.conf
uv run supervisord-mcp start auth-service
uv run supervisord-mcp start user-service
uv run supervisord-mcp start notification-service
```

## Why Supervisord MCP?

### vs. Circus MCP
- **Production Focus**: Supervisord is designed for production environments
- **Stability**: Battle-tested process supervisor with years of production use
- **Configuration**: Uses standard supervisord.conf for process definitions

> **Note: AI Agent Integration Limitations**
>
> Supervisord's XML-RPC API has constraints for dynamic AI agent process management:
> - `add_process` is not supported via API (requires manual config file edit + `reload`)
> - stdout/stderr logs require separate API calls
> - No CPU/memory resource metrics available via API
> - Starting an already-running process throws `ALREADY_STARTED` error (not idempotent)
>
> For use cases where AI agents need to dynamically add and monitor processes, [Circus MCP](https://github.com/aether-platform/circus-mcp) offers a more complete API. Supervisord MCP is best suited for integrating with existing Supervisord environments.

### vs. systemd
- **Cross-platform**: Works on any system with Python
- **User-friendly**: Simple commands and AI integration
- **Flexible**: Easy configuration and process management

### vs. PM2
- **Python-native**: Perfect for Python applications
- **AI integration**: MCP protocol support out of the box
- **Production proven**: Based on widely-used Supervisord

## Advanced Features

### Process Control

```bash
# Standard operations
uv run supervisord-mcp start webapp
uv run supervisord-mcp stop webapp
uv run supervisord-mcp restart webapp

# Get detailed status
uv run supervisord-mcp status webapp
```

### Log Management

```bash
# View logs with options
uv run supervisord-mcp logs webapp --lines 100
uv run supervisord-mcp logs webapp --stderr

# Real-time log monitoring (use supervisorctl tail in another terminal)
```

### Configuration Management

```bash
# Reload configuration after changes
uv run supervisord-mcp reload
```

## Installation & Setup

### System Requirements

- Python 3.10 or higher
- Supervisord installed and running
- Any operating system (Linux, macOS, Windows)

### Installation Options

```bash
# From PyPI (recommended)
uv add supervisord-mcp

# With pip (alternative)
pip install supervisord-mcp

# From source
git clone https://github.com/aether-platform/supervisord-mcp.git
cd supervisord-mcp
uv sync
```

### Supervisord Setup

1. Install Supervisord:
```bash
pip install supervisor
```

2. Create configuration directory:
```bash
mkdir -p /etc/supervisor/conf.d
```

3. Create main configuration file `/etc/supervisor/supervisord.conf`:
```ini
[unix_http_server]
file=/tmp/supervisor.sock

[supervisord]
logfile=/tmp/supervisord.log
logfile_maxbytes=50MB
logfile_backups=10
loglevel=info
pidfile=/tmp/supervisord.pid
nodaemon=false
minfds=1024
minprocs=200

[rpcinterface:supervisor]
supervisor.rpcinterface_factory = supervisor.rpcinterface:make_main_rpcinterface

[supervisorctl]
serverurl=unix:///tmp/supervisor.sock

[inet_http_server]
port=127.0.0.1:9001

[include]
files = /etc/supervisor/conf.d/*.conf
```

**Important**: Supervisord MCP requires the `[inet_http_server]` configuration block to be enabled with HTTP access. The tool connects to Supervisord via HTTP XML-RPC protocol and does not support Unix domain socket connections.

4. Start Supervisord:
```bash
supervisord -c /etc/supervisor/supervisord.conf
```

### Verify Installation

```bash
uv run supervisord-mcp --help
uv run supervisord-mcp info
```

## Configuration

Supervisord MCP works with standard Supervisord configuration. Add your programs to `/etc/supervisor/conf.d/`:

### Example Program Configuration

```ini
[program:webapp]
command=gunicorn app:application --bind 0.0.0.0:8000
directory=/app
numprocs=1
autostart=true
autorestart=true
startsecs=10
startretries=3
user=www-data
redirect_stderr=true
stdout_logfile=/var/log/webapp.log
```

### Custom Server URL

```bash
# Use custom Supervisord server
uv run supervisord-mcp --server-url http://localhost:9001/RPC2 list-processes
```

## MCP Tools Available

The following tools are available for AI agents:

- **add_process**: Add a new process (requires config reload)
- **start_process**: Start a process
- **stop_process**: Stop a process
- **restart_process**: Restart a process
- **list_processes**: List all processes
- **get_process_status**: Get detailed process status
- **get_logs**: Retrieve process logs (stdout/stderr)
- **get_system_info**: Get Supervisord system information
- **reload_config**: Reload Supervisord configuration

## Getting Help

### Documentation

- **[Supervisord Documentation](http://supervisord.org/)** - Official Supervisord documentation
- **[MCP Documentation](https://modelcontextprotocol.io/)** - Model Context Protocol specification

### Support

- **GitHub Issues**: [Report bugs or request features](https://github.com/aether-platform/supervisord-mcp/issues)
- **Discussions**: [Join the community](https://github.com/aether-platform/supervisord-mcp/discussions)

### Quick Command Reference

```bash
# Process Management
uv run supervisord-mcp start <name>
uv run supervisord-mcp stop <name>
uv run supervisord-mcp restart <name>
uv run supervisord-mcp status <name>

# Monitoring
uv run supervisord-mcp list-processes
uv run supervisord-mcp logs <name> [--lines N] [--stderr]
uv run supervisord-mcp info

# Configuration
uv run supervisord-mcp reload

# AI Integration
uv run supervisord-mcp mcp
```

## Token Cost Analysis for AI Agents

**Reduce tokens, agents work faster.** Every token an AI agent spends on process monitoring is a token not spent on solving the actual problem. Research shows that iterative debugging stages consume up to 59.4% of total tokens in agentic workflows ([Tokenomics, 2026](https://arxiv.org/abs/2601.14470)). By providing structured, concise responses through MCP, we cut the largest cost driver in AI-assisted debugging: unnecessary round trips and unstructured output parsing.

### Tool Schema Overhead (Context Residency Cost)

When MCP tools are registered, their schema definitions persist in the conversation context throughout the session.

| Item | Est. Tokens |
|------|-------------|
| 9 tools schema | **~1,100 tokens** |

### Per-Call Token Cost

| Operation | Request | Response | Total |
|-----------|---------|----------|-------|
| `list_processes` (5 procs) | ~30 | ~120-200 | **~150-230** |
| `get_process_status` | ~40 | ~100-150 | **~140-190** |
| `get_logs` (10 lines) | ~50 | ~150-450 | **~200-500** |
| `get_logs` (50 lines) | ~50 | ~750-2,450 | **~800-2,500** |
| `get_logs` (100 lines, default) | ~50 | ~1,450-4,950 | **~1,500-5,000** |
| `get_system_info` | ~30 | ~50-90 | **~80-120** |
| `start/stop/restart_process` | ~40 | ~30-60 | **~70-100** |
| `reload_config` | ~30 | ~40-70 | **~70-100** |

### MCP vs Raw Linux Commands — "Quit Quickly" Investigation

Cost comparison when debugging a process that dies immediately after startup.

#### Raw Commands (without MCP): 12 steps

```
supervisorctl status                              # Step 1:  Check all processes
supervisorctl status webapp                       # Step 2:  Check target → FATAL
supervisorctl tail webapp stderr                  # Step 3:  stderr logs (unbounded output risk)
cat /var/log/supervisor/webapp-stderr.log | tail -50  # Step 4:  Read log file directly
supervisorctl start webapp                        # Step 5:  Attempt restart
sleep 2 && supervisorctl status webapp            # Step 6:  Check after restart
supervisorctl tail webapp stderr | tail -20       # Step 7:  Check logs again
ps aux | grep webapp                              # Step 8:  Verify process existence
journalctl -u supervisor --no-pager -n 30         # Step 9:  systemd logs
cat /etc/supervisor/conf.d/webapp.conf            # Step 10: Check configuration
lsof -i :8080                                     # Step 11: Check port conflicts
free -m                                           # Step 12: Check resource exhaustion
```

- Each Bash invocation has **~60-90 tokens of fixed overhead**
- `supervisorctl tail` has no line limit — **token explosion risk**
- Unstructured text output leads to LLM **parsing errors**
- **Reasoning tokens** are consumed between each step (~150-250 tokens/step)
- "Quit Quickly" scenarios typically require **2-3 loops** of this sequence

#### MCP (Structured Tools): 5 steps

```
list_processes                                    # Spot FATAL immediately
get_process_status("webapp")                      # Detailed status
get_logs("webapp", lines=20, stderr=true)         # Error logs (bounded to 20 lines)
restart_process("webapp")                         # Restart
get_process_status("webapp")                      # Verify after restart
```

#### Comparison

| Metric | Raw Commands | MCP | Reduction |
|--------|-------------|-----|-----------|
| Tool calls | 8-12 | 3-5 | **60-70%** |
| Output tokens | 2,000-8,500 | 560-1,160 | **70-85%** |
| Reasoning tokens (inter-step) | ~1,500-3,000 | ~500-1,000 | **60-70%** |
| Total tokens (excl. schema) | 2,900-9,400 | 935-1,535 | **60-85%** |
| Total tokens (incl. schema) | 2,900-9,400 | 2,035-2,635 | **30-70%** |
| Round trips | 8-12 | 3-5 | **60%** |
| Wall-clock time | 12-36s | ~5s | **60-85%** |
| Parse reliability | Low (unstructured) | High (structured) | — |

#### Scaling with Retries

Cumulative cost when repeated investigation is needed (common with "Quit Quickly" issues):

| Retries | Raw Commands | MCP | Savings |
|---------|-------------|-----|---------|
| 1 (success) | ~2,900-9,400 | ~935-1,535 | 60-85% |
| 2 loops | ~5,000-15,000 | ~1,500-2,500 | 70-83% |
| 3 loops | ~7,000-20,000 | ~2,000-3,500 | 71-82% |

Raw command costs grow exponentially with retries (exploratory commands pile up), while MCP costs scale linearly.

**Break-even point**: Accounting for schema residency cost (~1,100 tokens), MCP becomes cost-equivalent at **3-4 tool calls** and cheaper beyond that.

### Optimization Tips

| Tip | Effect |
|-----|--------|
| Limit `get_logs` to `lines=10~20` | **70-80% reduction** in log retrieval cost |
| Use a single `list_processes` call for overview | Eliminates need for individual status calls |
| Use `stderr=true` to fetch only stderr | Avoids wasting tokens on stdout |
| Skip `get_system_info` for status checks only | Saves ~80-120 tokens |

### References

Research underpinning this token cost analysis:

- [Tokenomics: Quantifying Where Tokens Are Used in Agentic SE](https://arxiv.org/abs/2601.14470) — First empirical analysis of token consumption in agentic workflows. Iterative stages consume 59.4% of tokens
- [Help or Hurdle? Rethinking MCP-Augmented LLMs](https://arxiv.org/abs/2508.12566) — MCPGAUGE: first MCP evaluation framework with 4 dimensions including overhead
- [MCP Tool Descriptions Are Smelly!](https://arxiv.org/abs/2602.14878) — Large-scale study of 856 tools / 103 MCP servers. Tool description quality directly impacts agent efficiency
- [MCPAgentBench](https://arxiv.org/abs/2512.24565) — 841 tasks, 20,000+ MCP tools benchmark. Defines Token Efficiency (TEFS) as evaluation metric
- [AgentDiet: Trajectory Reduction](https://arxiv.org/abs/2509.23586) — Reduces input tokens by 39.9-59.7%
- [Token-Budget-Aware LLM Reasoning](https://aclanthology.org/2025.findings-acl.1274.pdf) — 67% output token reduction, 59% cost reduction
- [Token Efficiency with Structured Output](https://medium.com/data-science-at-microsoft/token-efficiency-with-structured-output-from-language-models-be2e51d3d9d5) — Function calling is the most token-efficient output format (Microsoft)

## License

MIT License - see [LICENSE](LICENSE) for details.

## About the Author

**AetherPlatform** - Building the future of cloud-native development tools

- **GitHub**: [@aether-platform](https://github.com/aether-platform)
- **Project Website**: [AetherPlatform](https://github.com/aether-platform)
- **Contact**: aether-platform@re-x.info

### Our Mission
We develop tools that enhance developer productivity through AI integration and modern cloud-native technologies. Supervisord MCP is part of our broader ecosystem of development tools designed to streamline the software development lifecycle.

### Other Projects
- **AetherSaaS**: SaaS platform management console
- **AetherCoding**: AI-enhanced development environments
- **AetherOperation**: Operations and terminal management tools
- **Circus MCP**: Alternative process management with Circus

## Acknowledgments

We extend our heartfelt gratitude to the **[Supervisord](http://supervisord.org/)** development team for creating such a robust and reliable process management foundation. Their excellent work made this project possible. Supervisord MCP builds upon their solid architecture to bring modern AI agent integration to process management.

## Related Projects

- **[Supervisord](http://supervisord.org/)** - The underlying process manager
- **[Model Context Protocol](https://modelcontextprotocol.io/)** - AI agent communication standard
- **[AetherPlatform](https://github.com/aether-platform)** - Cloud-native development tools
- **[Circus MCP](https://github.com/aether-platform/circus-mcp)** - Alternative process management solution

---

**Made with ❤️ by [AetherPlatform](https://github.com/aether-platform)**

*Supervisord MCP: Production-ready process management, AI-powered automation.*