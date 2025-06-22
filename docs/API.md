# API Reference

Complete reference for Supervisord MCP tools, CLI commands, and Python API.

## MCP Tools

These tools are available for AI agents through the Model Context Protocol.

### Process Control

#### `start_process`

Start a configured process.

**Parameters:**
- `name` (string, required): Process name as configured in supervisord.conf

**Returns:**
```json
{
  "status": "ok",
  "message": "Process 'webapp' started",
  "result": true
}
```

**Example:**
```json
{
  "name": "start_process",
  "arguments": {
    "name": "webapp"
  }
}
```

#### `stop_process`

Stop a running process.

**Parameters:**
- `name` (string, required): Process name

**Returns:**
```json
{
  "status": "ok",
  "message": "Process 'webapp' stopped",
  "result": true
}
```

#### `restart_process`

Restart a process (stop then start).

**Parameters:**
- `name` (string, required): Process name

**Returns:**
```json
{
  "status": "ok",
  "message": "Process 'webapp' restarted",
  "result": true
}
```

### Process Information

#### `list_processes`

List all configured processes with their status.

**Parameters:** None

**Returns:**
```
Found 3 processes:

• webapp: RUNNING (PID: 1234) - pid 1234, uptime 0:01:23
• worker: STOPPED - Not started
• redis: RUNNING (PID: 5678) - pid 5678, uptime 0:05:42
```

#### `get_process_status`

Get detailed status for a specific process.

**Parameters:**
- `name` (string, required): Process name

**Returns:**
```
Process: webapp
Status: RUNNING
PID: 1234
Uptime: pid 1234, uptime 0:01:23
Start time: 1672531200
```

### Logging

#### `get_logs`

Retrieve process logs.

**Parameters:**
- `name` (string, required): Process name
- `lines` (integer, optional): Number of lines to retrieve (default: 100)
- `stderr` (boolean, optional): Get stderr instead of stdout (default: false)

**Returns:**
```
Last 50 log lines:

2024-06-22 10:30:01 INFO Starting webapp
2024-06-22 10:30:02 INFO Server listening on port 8000
2024-06-22 10:30:03 INFO Ready to accept connections
```

### System Operations

#### `get_system_info`

Get Supervisord system information.

**Parameters:** None

**Returns:**
```
Supervisord System Information:

API Version: 3.0
Supervisor Version: 4.2.4
Server URL: http://localhost:9001/RPC2
State: RUNNING
```

#### `reload_config`

Reload Supervisord configuration.

**Parameters:** None

**Returns:**
```json
{
  "status": "ok",
  "message": "Configuration reloaded",
  "result": [[], [], []]
}
```

#### `add_process`

Add a new process configuration (requires manual config update).

**Parameters:**
- `name` (string, required): Process name
- `command` (string, required): Command to execute
- `directory` (string, optional): Working directory
- `autostart` (boolean, optional): Start automatically (default: false)
- `autorestart` (string, optional): Restart policy (default: "unexpected")
- `numprocs` (integer, optional): Number of processes (default: 1)

**Returns:**
```json
{
  "status": "warning",
  "message": "Process 'webapp' configuration prepared. Please add to supervisord.conf and reload.",
  "config": {
    "command": "gunicorn app:application",
    "autostart": false,
    "autorestart": "unexpected",
    "numprocs": 1,
    "redirect_stderr": true,
    "stdout_logfile": "/tmp/webapp.log",
    "stderr_logfile": "/tmp/webapp_error.log"
  }
}
```

## CLI Commands

### Global Options

- `--verbose, -v`: Enable verbose logging
- `--server-url`: Supervisord XML-RPC server URL (default: http://localhost:9001/RPC2)

### Process Management

#### `supervisord-mcp start <name>`

Start a process.

```bash
supervisord-mcp start webapp
supervisord-mcp start worker
```

#### `supervisord-mcp stop <name>`

Stop a process.

```bash
supervisord-mcp stop webapp
supervisord-mcp stop worker
```

#### `supervisord-mcp restart <name>`

Restart a process.

```bash
supervisord-mcp restart webapp
supervisord-mcp restart worker
```

### Process Information

#### `supervisord-mcp list-processes`

List all processes with status indicators.

```bash
supervisord-mcp list-processes
```

Output:
```
Found 3 processes:

🟢 webapp: RUNNING
   PID: 1234
   Description: pid 1234, uptime 0:01:23

🔴 worker: STOPPED
   Description: Not started

🟢 redis: RUNNING
   PID: 5678
   Description: pid 5678, uptime 0:05:42
```

#### `supervisord-mcp status <name>`

Get detailed status for a specific process.

```bash
supervisord-mcp status webapp
```

### Logging

#### `supervisord-mcp logs <name> [options]`

View process logs.

**Options:**
- `--lines INTEGER`: Number of lines to show (default: 100)
- `--stderr`: Show stderr instead of stdout

```bash
# Show last 100 stdout lines
supervisord-mcp logs webapp

# Show last 50 stderr lines
supervisord-mcp logs webapp --lines 50 --stderr

# Show specific number of lines
supervisord-mcp logs worker --lines 200
```

### System Operations

#### `supervisord-mcp info`

Show Supervisord system information.

```bash
supervisord-mcp info
```

#### `supervisord-mcp reload`

Reload Supervisord configuration.

```bash
supervisord-mcp reload
```

#### `supervisord-mcp mcp`

Start MCP server for AI agent integration.

```bash
supervisord-mcp mcp
```

### Process Configuration

#### `supervisord-mcp add <name> <command> [options]`

Add a new process configuration.

**Options:**
- `--directory TEXT`: Working directory
- `--autostart/--no-autostart`: Start automatically (default: no-autostart)
- `--autorestart TEXT`: Restart policy (default: unexpected)
- `--numprocs INTEGER`: Number of processes (default: 1)

```bash
# Basic process
supervisord-mcp add webapp "gunicorn app:application"

# With options
supervisord-mcp add api "uvicorn main:app" \
  --directory /app \
  --autostart \
  --numprocs 4
```

## Python API

### SupervisordManager

Core manager class for Supervisord operations.

```python
from supervisord_mcp import SupervisordManager

# Initialize manager
manager = SupervisordManager("http://localhost:9001/RPC2")

# Connect to Supervisord
await manager.connect()

# Start a process
result = await manager.start_process("webapp")
print(result)  # {"status": "ok", "message": "Process 'webapp' started"}

# Get process status
result = await manager.get_process_status("webapp")
print(result["process"]["statename"])  # "RUNNING"

# Get logs
result = await manager.get_logs("webapp", lines=50)
for line in result["logs"]:
    print(line)
```

### SupervisordMCPServer

MCP server for AI agent integration.

```python
from supervisord_mcp import SupervisordMCPServer

# Initialize and run MCP server
server = SupervisordMCPServer("http://localhost:9001/RPC2")
await server.run()
```

## Error Handling

All operations return structured responses with consistent error handling:

### Success Response
```json
{
  "status": "ok",
  "message": "Operation successful",
  "data": {...}
}
```

### Error Response
```json
{
  "status": "error",
  "message": "Error description"
}
```

### Warning Response
```json
{
  "status": "warning",
  "message": "Warning description",
  "data": {...}
}
```

## Common Error Codes

- **Connection Error**: Cannot connect to Supervisord daemon
- **Process Not Found**: Process not configured in supervisord.conf
- **Already Started**: Process is already running
- **Not Running**: Process is not currently running
- **Spawn Error**: Process failed to start
- **Abnormal Termination**: Process exited unexpectedly

## Configuration Examples

### Basic Web Application

```ini
[program:webapp]
command=gunicorn app:application --bind 0.0.0.0:8000
directory=/app
numprocs=1
autostart=true
autorestart=true
startsecs=10
user=www-data
redirect_stderr=true
stdout_logfile=/var/log/webapp.log
```

### Worker Process

```ini
[program:worker]
command=celery worker -A app --loglevel=info
directory=/app
numprocs=2
autostart=true
autorestart=true
startsecs=10
user=worker
redirect_stderr=true
stdout_logfile=/var/log/worker.log
```

### Development Server

```ini
[program:dev-server]
command=python manage.py runserver 0.0.0.0:8000
directory=/app
numprocs=1
autostart=false
autorestart=false
startsecs=5
user=developer
redirect_stderr=true
stdout_logfile=/var/log/dev-server.log
```

## Best Practices

1. **Process Names**: Use descriptive, unique names
2. **Logging**: Configure appropriate log files and rotation
3. **User Permissions**: Run processes with minimal required privileges
4. **Resource Limits**: Set appropriate resource limits in configuration
5. **Health Checks**: Implement health checks for critical processes
6. **Graceful Shutdown**: Ensure processes handle SIGTERM properly

## Troubleshooting

### Connection Issues

1. Verify Supervisord is running:
   ```bash
   ps aux | grep supervisord
   ```

2. Check Supervisord configuration:
   ```bash
   supervisorctl status
   ```

3. Test XML-RPC endpoint:
   ```python
   import xmlrpc.client
   server = xmlrpc.client.ServerProxy('http://localhost:9001/RPC2')
   print(server.supervisor.getState())
   ```

### Process Issues

1. Check process configuration:
   ```bash
   supervisorctl reread
   supervisorctl update
   ```

2. View process logs:
   ```bash
   supervisorctl tail webapp
   ```

3. Check Supervisord logs:
   ```bash
   tail -f /tmp/supervisord.log
   ```