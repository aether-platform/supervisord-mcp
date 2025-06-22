"""
Main entry point for Supervisord MCP.
"""

import sys

from .cli import cli


def main() -> None:
    """Main entry point."""
    try:
        cli()
    except KeyboardInterrupt:
        print("\nInterrupted by user", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
