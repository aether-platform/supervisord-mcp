"""
MCP Server for Supervisord process management.
"""

import logging
from typing import Any

from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import TextContent, Tool

from .manager import SupervisordManager


class SupervisordMCPServer:
    """MCP Server for Supervisord process management."""

    def __init__(self, server_url: str = "http://localhost:9001/RPC2"):
        """Initialize Supervisord MCP Server.

        Args:
            server_url: URL of Supervisord XML-RPC server
        """
        self.server: Server = Server("supervisord-mcp")
        self.manager = SupervisordManager(server_url)
        self.logger = logging.getLogger(__name__)
        self._setup_tools()

    def _setup_tools(self) -> None:
        """Setup MCP tools."""

        @self.server.list_tools()
        async def list_tools() -> list[Tool]:
            """List available tools."""
            return [
                Tool(
                    name="add_process",
                    description="Add a new process to Supervisord (requires config reload)",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "name": {"type": "string", "description": "Process name"},
                            "command": {"type": "string", "description": "Command to run"},
                            "directory": {"type": "string", "description": "Working directory"},
                            "autostart": {
                                "type": "boolean",
                                "default": False,
                                "description": "Start automatically on boot",
                            },
                            "autorestart": {
                                "type": "string",
                                "default": "unexpected",
                                "description": "Restart policy (true, false, unexpected)",
                            },
                            "numprocs": {
                                "type": "integer",
                                "default": 1,
                                "description": "Number of processes",
                            },
                        },
                        "required": ["name", "command"],
                    },
                ),
                Tool(
                    name="start_process",
                    description="Start a process",
                    inputSchema={
                        "type": "object",
                        "properties": {"name": {"type": "string", "description": "Process name"}},
                        "required": ["name"],
                    },
                ),
                Tool(
                    name="stop_process",
                    description="Stop a process",
                    inputSchema={
                        "type": "object",
                        "properties": {"name": {"type": "string", "description": "Process name"}},
                        "required": ["name"],
                    },
                ),
                Tool(
                    name="restart_process",
                    description="Restart a process",
                    inputSchema={
                        "type": "object",
                        "properties": {"name": {"type": "string", "description": "Process name"}},
                        "required": ["name"],
                    },
                ),
                Tool(
                    name="list_processes",
                    description="List all processes",
                    inputSchema={"type": "object", "properties": {}},
                ),
                Tool(
                    name="get_process_status",
                    description="Get process status",
                    inputSchema={
                        "type": "object",
                        "properties": {"name": {"type": "string", "description": "Process name"}},
                        "required": ["name"],
                    },
                ),
                Tool(
                    name="get_logs",
                    description="Get process logs",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "name": {"type": "string", "description": "Process name"},
                            "lines": {
                                "type": "integer",
                                "default": 100,
                                "description": "Number of lines to retrieve",
                            },
                            "stderr": {
                                "type": "boolean",
                                "default": False,
                                "description": "Get stderr logs instead of stdout",
                            },
                        },
                        "required": ["name"],
                    },
                ),
                Tool(
                    name="get_system_info",
                    description="Get Supervisord system information",
                    inputSchema={"type": "object", "properties": {}},
                ),
                Tool(
                    name="reload_config",
                    description="Reload Supervisord configuration",
                    inputSchema={"type": "object", "properties": {}},
                ),
            ]

        @self.server.call_tool()
        async def call_tool(name: str, arguments: dict[str, Any]) -> list[TextContent]:
            """Handle tool calls."""

            # Ensure connection
            if not await self.manager.connect():
                return [TextContent(type="text", text="Failed to connect to Supervisord daemon")]

            try:
                if name == "add_process":
                    result = await self.manager.add_process(
                        arguments["name"],
                        arguments["command"],
                        directory=arguments.get("directory"),
                        autostart=arguments.get("autostart", False),
                        autorestart=arguments.get("autorestart", "unexpected"),
                        numprocs=arguments.get("numprocs", 1),
                    )
                elif name == "start_process":
                    result = await self.manager.start_process(arguments["name"])
                elif name == "stop_process":
                    result = await self.manager.stop_process(arguments["name"])
                elif name == "restart_process":
                    result = await self.manager.restart_process(arguments["name"])
                elif name == "list_processes":
                    result = await self.manager.list_processes()
                elif name == "get_process_status":
                    result = await self.manager.get_process_status(arguments["name"])
                elif name == "get_logs":
                    result = await self.manager.get_logs(
                        arguments["name"],
                        lines=arguments.get("lines", 100),
                        stderr=arguments.get("stderr", False),
                    )
                elif name == "get_system_info":
                    result = await self.manager.get_system_info()
                elif name == "reload_config":
                    result = await self.manager.reload_config()
                else:
                    return [TextContent(type="text", text=f"Unknown tool: {name}")]

                # Format result for better readability
                if result.get("status") == "ok":
                    if "processes" in result:
                        # Format process list
                        processes = result["processes"]
                        output = f"Found {len(processes)} processes:\n\n"
                        for proc in processes:
                            status = proc.get("statename", "UNKNOWN")
                            name = proc.get("name", "unknown")
                            pid = proc.get("pid", 0)
                            description = proc.get("description", "")
                            output += f"• {name}: {status}"
                            if pid:
                                output += f" (PID: {pid})"
                            if description:
                                output += f" - {description}"
                            output += "\n"
                        return [TextContent(type="text", text=output)]

                    elif "process" in result:
                        # Format single process info
                        proc = result["process"]
                        output = f"Process: {proc.get('name', 'unknown')}\n"
                        output += f"Status: {proc.get('statename', 'UNKNOWN')}\n"
                        output += f"PID: {proc.get('pid', 'N/A')}\n"
                        output += f"Uptime: {proc.get('description', 'N/A')}\n"
                        output += f"Start time: {proc.get('start', 'N/A')}\n"
                        return [TextContent(type="text", text=output)]

                    elif "logs" in result:
                        # Format logs
                        logs = result["logs"]
                        if logs:
                            output = f"Last {len(logs)} log lines:\n\n"
                            output += "\n".join(logs)
                        else:
                            output = "No logs available"
                        return [TextContent(type="text", text=output)]

                    elif "info" in result:
                        # Format system info
                        info = result["info"]
                        output = "Supervisord System Information:\n\n"
                        output += f"API Version: {info.get('api_version', 'Unknown')}\n"
                        output += (
                            f"Supervisor Version: {info.get('supervisor_version', 'Unknown')}\n"
                        )
                        output += f"Server URL: {info.get('server_url', 'Unknown')}\n"
                        state = info.get("state", {})
                        output += f"State: {state.get('statename', 'Unknown')}\n"
                        return [TextContent(type="text", text=output)]

                    else:
                        # Generic success message
                        message = result.get("message", "Operation completed successfully")
                        return [TextContent(type="text", text=message)]

                else:
                    # Error case
                    error_msg = result.get("message", "Unknown error occurred")
                    return [TextContent(type="text", text=f"Error: {error_msg}")]

            except Exception as e:
                self.logger.error(f"Error executing tool {name}: {e}")
                return [TextContent(type="text", text=f"Error: {str(e)}")]

    async def run(self) -> None:
        """Run the MCP server."""
        self.logger.info("Starting Supervisord MCP Server")
        async with stdio_server() as streams:
            await self.server.run(
                streams[0], streams[1], self.server.create_initialization_options()
            )
