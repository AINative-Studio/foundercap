"""Command-line interface for the FounderCap application."""
import argparse
import asyncio
import logging
from typing import Any, List, Optional

import uvicorn
from fastapi import FastAPI

from app.core.config import settings
from app.main import app as fastapi_app

logger = logging.getLogger(__name__)


class CLI:
    """Command-line interface for the FounderCap application."""

    def __init__(self) -> None:
        """Initialize the CLI."""
        self.parser = argparse.ArgumentParser(
            description="FounderCap - Startup Funding Tracker & Dashboard Automation"
        )
        self.subparsers = self.parser.add_subparsers(dest="command", help="Command to run")
        self._setup_commands()

    def _setup_commands(self) -> None:
        """Set up command-line commands."""
        # Run server command
        run_parser = self.subparsers.add_parser("run", help="Run the API server")
        run_parser.add_argument(
            "--host",
            type=str,
            default=settings.HOST,
            help=f"Host to bind to (default: {settings.HOST})",
        )
        run_parser.add_argument(
            "--port",
            type=int,
            default=settings.PORT,
            help=f"Port to bind to (default: {settings.PORT})",
        )
        run_parser.add_argument(
            "--reload",
            action="store_true",
            help="Enable auto-reload for development",
        )

        # Run tests command
        test_parser = self.subparsers.add_parser("test", help="Run tests")
        test_parser.add_argument(
            "test_paths",
            nargs="*",
            default=["tests"],
            help="Test paths to run (default: tests)",
        )

    def parse_args(self, args: Optional[List[str]] = None) -> argparse.Namespace:
        """Parse command-line arguments.

        Args:
            args: Command-line arguments (default: None, uses sys.argv).

        Returns:
            Parsed arguments.
        """
        return self.parser.parse_args(args)

    async def run(self, args: Optional[argparse.Namespace] = None) -> int:
        """Run the CLI.

        Args:
            args: Parsed command-line arguments (default: None, parses sys.argv).

        Returns:
            Exit code.
        """
        if args is None:
            args = self.parse_args()

        if args.command == "run":
            return await self.run_server(args)
        elif args.command == "test":
            return await self.run_tests(args)
        else:
            self.parser.print_help()
            return 1

    async def run_server(self, args: argparse.Namespace) -> int:
        """Run the API server.

        Args:
            args: Parsed command-line arguments.

        Returns:
            Exit code (0 for success, non-zero for error).
        """
        logger.info("Starting FounderCap API server...")
        logger.info("Host: %s", args.host)
        logger.info("Port: %d", args.port)
        logger.info("Reload: %s", args.reload)

        config = uvicorn.Config(
            "app.main:app",
            host=args.host,
            port=args.port,
            reload=args.reload,
            log_level=logging.getLevelName(logging.INFO).lower(),
        )
        server = uvicorn.Server(config)
        await server.serve()
        return 0

    async def run_tests(self, args: argparse.Namespace) -> int:
        """Run tests.

        Args:
            args: Parsed command-line arguments.

        Returns:
            Exit code (0 for success, non-zero for error).
        """
        import pytest

        logger.info("Running tests: %s", " ".join(args.test_paths))
        return await asyncio.get_event_loop().run_in_executor(
            None, pytest.main, [*args.test_paths, "-v"]
        )


def main() -> None:
    """Run the CLI."""
    # Configure logging
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )

    # Run the CLI
    cli = CLI()
    args = cli.parse_args()
    exit_code = asyncio.run(cli.run(args))
    exit(exit_code)


if __name__ == "__main__":
    main()
