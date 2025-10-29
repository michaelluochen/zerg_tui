#!/usr/bin/env python3
"""
Main entry point for the Zerg Terminal Client.
"""

import asyncio
import logging
from pathlib import Path

import click
from rich.text import Text
from textual.app import App, ComposeResult
from textual.containers import Horizontal, ScrollableContainer, Vertical
from textual.message import Message
from textual.widgets import Footer, Header, Input, RichLog

from .client import ZergClient

# Set up logging
logging.basicConfig(level=logging.INFO)
L = logging.getLogger(__name__)


class ZergEvent(Message):
    """Custom message for Zerg events from Socket.IO."""

    def __init__(self, event_type: str, data: dict) -> None:
        """
        Create a ZergEvent message.

        Args:
            event_type: Type of event (e.g., 'zerg_output', 'stdout', 'connection')
            data: Event data dictionary
        """
        self.event_type = event_type
        self.data = data
        super().__init__()


class ChatPane(ScrollableContainer):
    """Chat pane for agent communication."""

    def compose(self) -> ComposeResult:
        """Compose the chat pane."""
        yield RichLog(id="chat-log", wrap=True, highlight=True, markup=True)
        yield Input(placeholder="Type a command or message...", id="chat-input")

    def on_mount(self) -> None:
        """Initialize the chat pane."""
        chat_log = self.query_one("#chat-log", RichLog)
        chat_log.write("Welcome to ZTC - Zerg Terminal Client")
        chat_log.write(Text("Connecting to Zerg service...", style="dim"))

    def add_user_message(self, message: str) -> None:
        """Add a user message to the chat log."""
        chat_log = self.query_one("#chat-log", RichLog)
        chat_log.write(Text(f"You: {message}", style="bold cyan"))

    def add_agent_message(self, message: str, event_type: str = "output") -> None:
        """Add an agent message to the chat log."""
        chat_log = self.query_one("#chat-log", RichLog)

        # Style based on event type
        style_map = {
            "zerg_output": "green",
            "zerg_reasoning": "yellow italic",
            "zerg_error": "bold red",
            "zerg_warning": "bold yellow",
            "zerg_tests": "magenta",
            "zerg_evals": "blue",
        }

        style = style_map.get(event_type, "white")
        prefix = (
            f"[{event_type.replace('zerg_', '').upper()}]"
            if event_type.startswith("zerg_")
            else "Agent:"
        )

        chat_log.write(Text(f"{prefix} {message}", style=style))

    def add_system_message(self, message: str) -> None:
        """Add a system message to the chat log."""
        chat_log = self.query_one("#chat-log", RichLog)
        chat_log.write(Text(f"[SYSTEM] {message}", style="dim italic"))


class ReviewPane(ScrollableContainer):
    """Review pane for diffs and code changes."""

    def compose(self) -> ComposeResult:
        """Compose the review pane."""
        yield RichLog(id="review-log", wrap=True, highlight=True, markup=True)

    def on_mount(self) -> None:
        """Initialize the review pane."""
        review_log = self.query_one("#review-log", RichLog)
        review_log.write(Text("Review Pane", style="bold"))
        review_log.write(Text("Diffs and changes will appear here...", style="dim"))

    def show_diff(self, diff_text: str) -> None:
        """Display a diff in the review pane."""
        review_log = self.query_one("#review-log", RichLog)
        review_log.clear()
        review_log.write(Text("Code Changes:", style="bold underline"))
        review_log.write(diff_text)

    def clear(self) -> None:
        """Clear the review pane."""
        review_log = self.query_one("#review-log", RichLog)
        review_log.clear()


class ExecutionPane(ScrollableContainer):
    """Execution pane for streaming logs and command output."""

    def compose(self) -> ComposeResult:
        """Compose the execution pane."""
        yield RichLog(id="execution-log", wrap=True, highlight=True, markup=True)

    def on_mount(self) -> None:
        """Initialize the execution pane."""
        execution_log = self.query_one("#execution-log", RichLog)
        execution_log.write(Text("Execution Pane", style="bold"))
        execution_log.write(Text("Logs and output will appear here...", style="dim"))

    def add_stdout(self, text: str) -> None:
        """Add stdout output to the execution log."""
        execution_log = self.query_one("#execution-log", RichLog)
        execution_log.write(Text(text, style="white"))

    def add_stderr(self, text: str) -> None:
        """Add stderr output to the execution log."""
        execution_log = self.query_one("#execution-log", RichLog)
        execution_log.write(Text(text, style="red"))

    def add_status(self, status: str, passed: bool = True) -> None:
        """Add a status message to the execution log."""
        execution_log = self.query_one("#execution-log", RichLog)
        style = "bold green" if passed else "bold red"
        symbol = "✓" if passed else "✗"
        execution_log.write(Text(f"{symbol} {status}", style=style))

    def clear(self) -> None:
        """Clear the execution pane."""
        execution_log = self.query_one("#execution-log", RichLog)
        execution_log.clear()


class ZergTerminalClient(App):
    """The main ZTC TUI application."""

    # Class attributes set by CLI
    workspace: Path = Path.cwd()
    batch_mode: bool = False
    yolo_mode: bool = False
    debug_mode: bool = False

    # Instance attributes
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.client: ZergClient | None = None
        self.socket_url = "http://localhost:3333"

    # CSS for styling the app
    CSS = """
    Screen {
        background: $surface;
    }

    #chat-pane {
        width: 60%;
        height: 100%;
        border: solid $primary;
    }

    #chat-log {
        height: 1fr;
        padding: 1;
    }

    #chat-input {
        dock: bottom;
        height: 3;
        border: solid $primary;
    }

    #side-pane {
        width: 40%;
        height: 100%;
    }

    #review-pane {
        height: 60%;
        border: solid $accent;
    }

    #review-log {
        height: 100%;
        padding: 1;
    }

    #execution-pane {
        height: 40%;
        border: solid $warning;
    }

    #execution-log {
        height: 100%;
        padding: 1;
    }

    RichLog {
        background: $panel;
        color: $text;
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
            yield ChatPane(id="chat-pane")

            # Side panes
            with Vertical(id="side-pane"):
                yield ReviewPane(id="review-pane")
                yield ExecutionPane(id="execution-pane")

        yield Footer()

    def on_mount(self) -> None:
        """Initialize the app and connect to Zerg service."""
        # Only create client if not already set (allows tests to inject mock client)
        if self.client is None:
            self.client = ZergClient(
                socket_url=self.socket_url, event_callback=self.handle_zerg_event
            )

            # Start connection worker
            self.run_worker(self.connect_to_zerg(), exclusive=True, name="zerg-connection")

    async def connect_to_zerg(self) -> None:
        """Worker to connect to Zerg service and initialize."""
        try:
            chat_pane = self.query_one("#chat-pane", ChatPane)
            chat_pane.add_system_message(f"Connecting to {self.socket_url}...")

            await self.client.connect()

            if self.client.connected:
                chat_pane.add_system_message("Connected successfully!")
                chat_pane.add_system_message("Initializing Zerg agent...")

                # Initialize Zerg
                await self.client.initialize_zerg()

                chat_pane.add_system_message("Ready! Type a command or message below.")
            else:
                chat_pane.add_system_message("Failed to connect to Zerg service.")

        except Exception as e:
            L.error(f"Connection error: {e}")
            chat_pane = self.query_one("#chat-pane", ChatPane)
            chat_pane.add_system_message(f"Connection error: {e}")

    def handle_zerg_event(self, event_type: str, data: dict) -> None:
        """
        Handle events from the Zerg client.

        This is called from Socket.IO async handlers running in the same event loop.
        Uses post_message() which is thread-safe and works from any context.
        """
        # Post message to be handled by the message system
        self.post_message(ZergEvent(event_type, data))

    def on_zerg_event(self, message: ZergEvent) -> None:
        """
        Message handler for ZergEvent messages.

        This is called by Textual's message system when a ZergEvent is posted.
        """
        self._handle_zerg_event_sync(message.event_type, message.data)

    def _handle_zerg_event_sync(self, event_type: str, data: dict) -> None:
        """Synchronous event handler that updates widgets."""
        try:
            chat_pane = self.query_one("#chat-pane", ChatPane)
            execution_pane = self.query_one("#execution-pane", ExecutionPane)
            # review_pane = self.query_one("#review-pane", ReviewPane)  # TODO: Add when diff routing implemented

            # Route events to appropriate panes
            if event_type == "connection":
                status = data.get("status", "unknown")
                if status == "connected":
                    chat_pane.add_system_message("Connected to Zerg service")
                elif status == "disconnected":
                    chat_pane.add_system_message("Disconnected from Zerg service")

            elif event_type in [
                "zerg_output",
                "zerg_reasoning",
                "zerg_error",
                "zerg_warning",
                "zerg_tests",
                "zerg_evals",
                "zerg_choices",
            ]:
                # Agent messages go to chat pane
                message = data.get("value", "")
                chat_pane.add_agent_message(message, event_type)

            elif event_type in ["stdout", "zerg_stdout"]:
                # Standard output goes to execution pane
                text = data.get("value", "")
                execution_pane.add_stdout(text)

            elif event_type in ["stderr", "zerg_stderr"]:
                # Standard error goes to execution pane
                text = data.get("value", "")
                execution_pane.add_stderr(text)

            elif event_type == "prompt":
                # Prompts can go to chat for visibility
                text = data.get("value", "")
                chat_pane.add_agent_message(f"Prompt: {text}", "prompt")

        except Exception as e:
            L.error(f"Error handling event {event_type}: {e}")

    def on_input_submitted(self, event: Input.Submitted) -> None:
        """Handle input submission from the chat input widget."""
        if event.input.id == "chat-input":
            message = event.value.strip()

            if not message:
                return

            # Add user message to chat
            chat_pane = self.query_one("#chat-pane", ChatPane)
            chat_pane.add_user_message(message)

            # Clear input
            event.input.value = ""

            # Send command to Zerg
            if self.client and self.client.connected:
                self.run_worker(
                    self.send_command(message),
                    name=f"send-command-{asyncio.get_event_loop().time()}",
                )
            else:
                chat_pane.add_system_message("Not connected to Zerg service!")

    async def send_command(self, message: str) -> None:
        """Worker to send command to Zerg."""
        try:
            # Parse command if it starts with special keywords
            if message.startswith("init"):
                await self.client.initialize_zerg()
            elif message.startswith("update"):
                await self.client.update_zerg()
            else:
                # Send as regular command
                await self.client.zerg_command(message)

        except Exception as e:
            L.error(f"Error sending command: {e}")
            chat_pane = self.query_one("#chat-pane", ChatPane)
            chat_pane.add_system_message(f"Error sending command: {e}")

    def action_new_session(self) -> None:
        """Create a new session."""
        self.notify("New session feature coming soon!", severity="information")

    def action_list_sessions(self) -> None:
        """List all sessions."""
        self.notify("Session list feature coming soon!", severity="information")


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
@click.version_option(version="0.1.0", prog_name="ztc")
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
