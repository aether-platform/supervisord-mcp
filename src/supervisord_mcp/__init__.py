"""
Supervisord MCP - Process management with MCP integration.
"""

__version__ = "1.0.0"
__author__ = "AetherPlatform"
__email__ = "aether-platform@re-x.info"

from .manager import SupervisordManager
from .mcp_server import SupervisordMCPServer

__all__ = ["SupervisordManager", "SupervisordMCPServer"]
