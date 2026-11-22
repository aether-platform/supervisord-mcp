"""
Supervisord MCP - Process management with MCP integration.
"""

from importlib.metadata import PackageNotFoundError, version

try:
    __version__ = version("supervisord-mcp")
except PackageNotFoundError:  # running from a source tree without installation
    __version__ = "1.1.0"
__author__ = "AetherPlatform"
__email__ = "aether-platform@re-x.info"

from .manager import SupervisordManager
from .mcp_server import SupervisordMCPServer

__all__ = ["SupervisordManager", "SupervisordMCPServer"]
