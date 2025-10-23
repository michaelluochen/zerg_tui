#!/usr/bin/env python3
"""
Main entry point for the Zerg Terminal Client.
"""

import asyncio
from pathlib import Path

import click
from textual.app import App, ComposeResult
from textual.containers import Container, Horizontal, Vertical
from textual.widgets import Header, Footer, Static, Welcome


class ZergTerminalClient(App):
    """The main ZTC TUI application."""

    # CSS for styling the app
    CSS = """
    Screen {
        background: $surface;
    }

    #chat-pane {
        width: 60%;
        height: 100%;
        border: solid $primary;
        padding: 1;
    }

    #side-pane {
        width: 40%;
        height: 100%;
    }

    #review-pane {
        height: 60%;
        border: solid $accent;
        padding: 1;
    }

    #execution-pane {
        height: 40%;
        border: solid $warning;
        padding: 1;
    }
    """

    BINDINGS = [
        ("ctrl+q", "quit", "Quit"),
        ("ctrl+t", "new_session", "New Session"),
        ("ctrl+l", "list_sessions", "List Sessions"),
    ]

    def compose(self) -> ComposeResult:
        """Create the layout of the application."""
        yield Header(name="ZTC - Zerg Terminal Client")

        with Horizontal():
            # Main chat pane
            with Vertical(id="chat-pane"):
                yield Static("Chat Pane\n\nAgent communication will appear here...", id="chat")

            # Side panes
            with Vertical(id="side-pane"):
                with Container(id="review-pane"):
                    yield Static("Review Pane\n\nDiffs and changes will appear here...", id="review")

                with Container(id="execution-pane"):
                    yield Static("Execution Pane\n\nLogs and output will appear here...", id="execution")

        yield Footer()

    def action_new_session(self) -> None:
        """Create a new session."""
        self.notify("New session feature coming soon!", severity="information")

    def action_list_sessions(self) -> None:
        """List all sessions."""
        self.notify("Session list feature coming soon!", severity="information")


@click.command()
@click.option('--workspace', '-w', type=click.Path(exists=True, path_type=Path),
              default=Path.cwd(), help='Workspace directory')
@click.option('--batch', is_flag=True, help='Enable batch mode (accept all changes at once)')
@click.option('--yolo', is_flag=True, help='YOLO mode (auto-approve file changes)')
@click.option('--debug', is_flag=True, help='Enable debug mode')
@click.version_option(version='0.1.0', prog_name='ztc')
def main(workspace: Path, batch: bool, yolo: bool, debug: bool) -> None:
    """
    ZTC - Zerg Terminal Client

    A terminal-native client for the Zerg AI agent.
    """
    # Store configuration in class attributes before instantiation
    ZergTerminalClient.workspace = workspace
    ZergTerminalClient.batch_mode = batch
    ZergTerminalClient.yolo_mode = yolo
    ZergTerminalClient.debug_mode = debug

    # Create and run the app
    app = ZergTerminalClient()
    app.run()


if __name__ == "__main__":
    main()