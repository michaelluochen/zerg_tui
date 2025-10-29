#!/usr/bin/env python3
"""
Main CLI entry point for the Zerg Terminal Client.
"""

import logging
from pathlib import Path

import click

from .app import ZergTerminalClient
from .config import ZTCConfig

# Set up logging
logging.basicConfig(level=logging.INFO)
L = logging.getLogger(__name__)


@click.command()
@click.option(
    "--workspace",
    "-w",
    type=click.Path(exists=True, path_type=Path),
    default=Path.cwd(),
    help="Workspace directory",
)
@click.option("--batch", is_flag=True, help="Enable batch mode (accept all changes at once)")
@click.option("--yolo", is_flag=True, help="YOLO mode (auto-approve file changes)")
@click.option("--debug", is_flag=True, help="Enable debug mode")
@click.option(
    "--socket-url",
    "-s",
    help="Socket.IO server URL (default: http://localhost:3333)",
)
@click.version_option(version="0.1.0", prog_name="ztc")
def main(
    workspace: Path,
    batch: bool,
    yolo: bool,
    debug: bool,
    socket_url: str | None,
) -> None:
    """
    ZTC - Zerg Terminal Client

    A terminal-native client for the Zerg AI agent.
    """
    # Configure logging
    if debug:
        logging.getLogger().setLevel(logging.DEBUG)

    # Create configuration from CLI arguments
    config = ZTCConfig.from_cli(
        workspace=workspace,
        batch=batch,
        yolo=yolo,
        debug=debug,
    )

    # Override socket URL if provided
    if socket_url:
        config.socket_url = socket_url

    # Merge with environment variables (env vars take precedence)
    config = config.merge_with_env()

    # Create and run the app with config
    app = ZergTerminalClient(config=config)
    app.run()


if __name__ == "__main__":
    main()
