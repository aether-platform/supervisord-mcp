"""
CLI interface for Supervisord MCP.
"""

import asyncio
import logging
import sys
from collections.abc import Callable
from typing import Any

import click

from .manager import SupervisordManager
from .mcp_server import SupervisordMCPServer


def setup_logging(verbose: bool = False) -> None:
    """Setup logging configuration."""
    level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(
        level=level,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        handlers=[logging.StreamHandler(sys.stdout)],
    )


@click.group()
@click.option("--verbose", "-v", is_flag=True, help="Enable verbose logging")
@click.option(
    "--server-url", default="http://localhost:9001/RPC2", help="Supervisord XML-RPC server URL"
)
@click.pass_context
def cli(ctx: click.Context, verbose: bool, server_url: str) -> None:
    """Supervisord MCP - Process management with MCP integration."""
    setup_logging(verbose)
    ctx.ensure_object(dict)
    ctx.obj["server_url"] = server_url
    ctx.obj["verbose"] = verbose


@cli.command()
@click.pass_context
async def mcp(ctx: click.Context) -> None:
    """Start MCP server for AI agent integration."""
    server_url = ctx.obj["server_url"]
    server = SupervisordMCPServer(server_url)
    await server.run()


@cli.command()
@click.argument("name")
@click.argument("command")
@click.option("--directory", help="Working directory")
@click.option("--autostart/--no-autostart", default=False, help="Start automatically")
@click.option("--autorestart", default="unexpected", help="Restart policy")
@click.option("--numprocs", default=1, help="Number of processes")
@click.pass_context
async def add(
    ctx: click.Context,
    name: str,
    command: str,
    directory: str | None,
    autostart: bool,
    autorestart: str,
    numprocs: int,
) -> None:
    """Add a new process to Supervisord."""
    manager = SupervisordManager(ctx.obj["server_url"])

    if not await manager.connect():
        click.echo("Failed to connect to Supervisord", err=True)
        sys.exit(1)

    result = await manager.add_process(
        name,
        command,
        directory=directory,
        autostart=autostart,
        autorestart=autorestart,
        numprocs=numprocs,
    )

    if result["status"] == "ok":
        click.echo(f"✓ {result['message']}")
    else:
        click.echo(f"✗ {result['message']}", err=True)
        sys.exit(1)


@cli.command()
@click.argument("name")
@click.pass_context
async def start(ctx: click.Context, name: str) -> None:
    """Start a process."""
    manager = SupervisordManager(ctx.obj["server_url"])

    if not await manager.connect():
        click.echo("Failed to connect to Supervisord", err=True)
        sys.exit(1)

    result = await manager.start_process(name)

    if result["status"] == "ok":
        click.echo(f"✓ {result['message']}")
    else:
        click.echo(f"✗ {result['message']}", err=True)
        sys.exit(1)


@cli.command()
@click.argument("name")
@click.pass_context
async def stop(ctx: click.Context, name: str) -> None:
    """Stop a process."""
    manager = SupervisordManager(ctx.obj["server_url"])

    if not await manager.connect():
        click.echo("Failed to connect to Supervisord", err=True)
        sys.exit(1)

    result = await manager.stop_process(name)

    if result["status"] == "ok":
        click.echo(f"✓ {result['message']}")
    else:
        click.echo(f"✗ {result['message']}", err=True)
        sys.exit(1)


@cli.command()
@click.argument("name")
@click.pass_context
async def restart(ctx: click.Context, name: str) -> None:
    """Restart a process."""
    manager = SupervisordManager(ctx.obj["server_url"])

    if not await manager.connect():
        click.echo("Failed to connect to Supervisord", err=True)
        sys.exit(1)

    result = await manager.restart_process(name)

    if result["status"] == "ok":
        click.echo(f"✓ {result['message']}")
    else:
        click.echo(f"✗ {result['message']}", err=True)
        sys.exit(1)


@cli.command(name="list-processes")
@click.pass_context
async def list_processes(ctx: click.Context) -> None:
    """List all processes."""
    manager = SupervisordManager(ctx.obj["server_url"])

    if not await manager.connect():
        click.echo("Failed to connect to Supervisord", err=True)
        sys.exit(1)

    result = await manager.list_processes()

    if result["status"] == "ok":
        processes = result["processes"]
        if processes:
            click.echo(f"Found {len(processes)} processes:\n")
            for proc in processes:
                status = proc.get("statename", "UNKNOWN")
                name = proc.get("name", "unknown")
                pid = proc.get("pid", 0)
                description = proc.get("description", "")

                status_icon = (
                    "🟢"
                    if status == "RUNNING"
                    else "🔴"
                    if status in ["STOPPED", "FATAL"]
                    else "🟡"
                )
                click.echo(f"{status_icon} {name}: {status}")
                if pid:
                    click.echo(f"   PID: {pid}")
                if description:
                    click.echo(f"   Description: {description}")
                click.echo()
        else:
            click.echo("No processes found")
    else:
        click.echo(f"✗ {result['message']}", err=True)
        sys.exit(1)


@cli.command()
@click.argument("name")
@click.pass_context
async def status(ctx: click.Context, name: str) -> None:
    """Get process status."""
    manager = SupervisordManager(ctx.obj["server_url"])

    if not await manager.connect():
        click.echo("Failed to connect to Supervisord", err=True)
        sys.exit(1)

    result = await manager.get_process_status(name)

    if result["status"] == "ok":
        proc = result["process"]
        click.echo(f"Process: {proc.get('name', 'unknown')}")
        click.echo(f"Status: {proc.get('statename', 'UNKNOWN')}")
        click.echo(f"PID: {proc.get('pid', 'N/A')}")
        click.echo(f"Uptime: {proc.get('description', 'N/A')}")
        click.echo(f"Start time: {proc.get('start', 'N/A')}")
    else:
        click.echo(f"✗ {result['message']}", err=True)
        sys.exit(1)


@cli.command()
@click.argument("name")
@click.option("--lines", default=100, help="Number of lines to show")
@click.option("--stderr", is_flag=True, help="Show stderr instead of stdout")
@click.pass_context
async def logs(ctx: click.Context, name: str, lines: int, stderr: bool) -> None:
    """Get process logs."""
    manager = SupervisordManager(ctx.obj["server_url"])

    if not await manager.connect():
        click.echo("Failed to connect to Supervisord", err=True)
        sys.exit(1)

    result = await manager.get_logs(name, lines=lines, stderr=stderr)

    if result["status"] == "ok":
        logs = result["logs"]
        if logs:
            stream_type = "stderr" if stderr else "stdout"
            click.echo(f"Last {len(logs)} lines from {name} ({stream_type}):\n")
            for line in logs:
                if line.strip():  # Skip empty lines
                    click.echo(line)
        else:
            click.echo("No logs available")
    else:
        click.echo(f"✗ {result['message']}", err=True)
        sys.exit(1)


@cli.command()
@click.pass_context
async def info(ctx: click.Context) -> None:
    """Get Supervisord system information."""
    manager = SupervisordManager(ctx.obj["server_url"])

    if not await manager.connect():
        click.echo("Failed to connect to Supervisord", err=True)
        sys.exit(1)

    result = await manager.get_system_info()

    if result["status"] == "ok":
        info = result["info"]
        click.echo("Supervisord System Information:")
        click.echo(f"  API Version: {info.get('api_version', 'Unknown')}")
        click.echo(f"  Supervisor Version: {info.get('supervisor_version', 'Unknown')}")
        click.echo(f"  Server URL: {info.get('server_url', 'Unknown')}")
        state = info.get("state", {})
        click.echo(f"  State: {state.get('statename', 'Unknown')}")
    else:
        click.echo(f"✗ {result['message']}", err=True)
        sys.exit(1)


@cli.command()
@click.pass_context
async def reload(ctx: click.Context) -> None:
    """Reload Supervisord configuration."""
    manager = SupervisordManager(ctx.obj["server_url"])

    if not await manager.connect():
        click.echo("Failed to connect to Supervisord", err=True)
        sys.exit(1)

    result = await manager.reload_config()

    if result["status"] == "ok":
        click.echo(f"✓ {result['message']}")
    else:
        click.echo(f"✗ {result['message']}", err=True)
        sys.exit(1)


def run_async_command(func: Callable[..., Any]) -> Callable[..., Any]:
    """Wrapper to run async click commands."""

    def wrapper(*args: Any, **kwargs: Any) -> Any:
        return asyncio.run(func(*args, **kwargs))

    return wrapper


# Apply async wrapper to all async commands
for command_name in [
    "mcp",
    "add",
    "start",
    "stop",
    "restart",
    "list-processes",
    "status",
    "logs",
    "info",
    "reload",
]:
    command = cli.commands[command_name]
    command.callback = run_async_command(command.callback)


if __name__ == "__main__":
    cli()
