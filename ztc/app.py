"""
Main application class for ZTC.
"""

import asyncio
import logging
from typing import Optional

from textual.app import App, ComposeResult
from textual.containers import Horizontal, Vertical
from textual.widgets import Footer, Header, Input

from .client import ZergClient
from .config import ZTCConfig
from .events import EventRouter, ZergEvent
from .widgets import ChatPane, ExecutionPane, ReviewPane, StatusBar

# Set up logging
L = logging.getLogger(__name__)


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
    }

    #chat-log {
        height: 1fr;
        padding: 1;
        overflow-y: auto;
        scrollbar-size: 1 1;
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
        overflow-y: auto;
        scrollbar-size: 1 1;
    }

    #execution-pane {
        height: 40%;
        border: solid $warning;
    }

    #execution-log {
        height: 100%;
        padding: 1;
        overflow-y: auto;
        scrollbar-size: 1 1;
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

    def __init__(self, config: Optional[ZTCConfig] = None, *args, **kwargs):
        """
        Initialize the ZTC application.

        Args:
            config: Configuration for the app
            *args: Additional positional arguments for the App
            **kwargs: Additional keyword arguments for the App
        """
        super().__init__(*args, **kwargs)
        self.config = config or ZTCConfig()
        self.client: Optional[ZergClient] = None
        self.event_router: Optional[EventRouter] = None

        # Auto-reconnect state
        self.reconnect_attempts = 0
        self.is_reconnecting = False

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

        yield StatusBar(id="status-bar")
        yield Footer()

    def on_mount(self) -> None:
        """Initialize the app and connect to Zerg service."""
        # Get widget references
        chat_pane = self.query_one("#chat-pane", ChatPane)
        execution_pane = self.query_one("#execution-pane", ExecutionPane)
        review_pane = self.query_one("#review-pane", ReviewPane)
        status_bar = self.query_one("#status-bar", StatusBar)

        # Create event router
        self.event_router = EventRouter(
            chat_pane=chat_pane,
            execution_pane=execution_pane,
            review_pane=review_pane,
            status_bar=status_bar,
            reconnect_callback=lambda: self.run_worker(
                self.auto_reconnect_worker(), exclusive=True, name="auto-reconnect"
            ),
        )

        # Create client if not already set (allows tests to inject mock client)
        if self.client is None:
            self.client = ZergClient(
                socket_url=self.config.socket_url,
                event_callback=self.handle_zerg_event,
            )

            # Start connection worker
            self.run_worker(self.connect_to_zerg(), exclusive=True, name="zerg-connection")

    async def connect_to_zerg(self) -> None:
        """Worker to connect to Zerg service and initialize."""
        try:
            chat_pane = self.query_one("#chat-pane", ChatPane)
            status_bar = self.query_one("#status-bar", StatusBar)

            status_bar.connection_status = "connecting"
            chat_pane.add_system_message(f"Connecting to {self.config.socket_url}...")

            await self.client.connect()

            if self.client.connected:
                status_bar.connection_status = "connected"
                status_bar.agent_status = "Initializing"
                chat_pane.add_system_message("Connected successfully!")
                chat_pane.add_system_message("Initializing Zerg agent...")

                # Initialize Zerg
                await self.client.initialize_zerg()

                status_bar.agent_status = "Ready"
                chat_pane.add_system_message("Ready! Type a command or message below.")
            else:
                status_bar.connection_status = "disconnected"
                chat_pane.add_system_message("Failed to connect to Zerg service.")
                # Start auto-reconnect
                self.run_worker(
                    self.auto_reconnect_worker(), exclusive=True, name="auto-reconnect"
                )

        except Exception as e:
            L.error(f"Connection error: {e}")
            status_bar = self.query_one("#status-bar", StatusBar)
            status_bar.connection_status = "disconnected"
            chat_pane = self.query_one("#chat-pane", ChatPane)
            chat_pane.add_system_message(f"Connection error: {e}")
            # Start auto-reconnect
            self.run_worker(
                self.auto_reconnect_worker(), exclusive=True, name="auto-reconnect"
            )

    def handle_zerg_event(self, event_type: str, data: dict) -> None:
        """
        Handle events from the Zerg client.

        This is called from Socket.IO async handlers running in the same event loop.
        Uses post_message() which is thread-safe and works from any context.

        Args:
            event_type: Type of event
            data: Event data
        """
        # Post message to be handled by the message system
        self.post_message(ZergEvent(event_type, data))

    def on_zerg_event(self, message: ZergEvent) -> None:
        """
        Message handler for ZergEvent messages.

        This is called by Textual's message system when a ZergEvent is posted.

        Args:
            message: The ZergEvent message to handle
        """
        if self.event_router:
            self.event_router.route(message)

    def on_input_submitted(self, event: Input.Submitted) -> None:
        """
        Handle input submission from the chat input widget.

        Args:
            event: The input submission event
        """
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
        """
        Worker to send command to Zerg.

        Args:
            message: The command to send
        """
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

    async def auto_reconnect_worker(self) -> None:
        """Worker that handles reconnection with exponential backoff."""
        if self.is_reconnecting:
            return  # Already reconnecting

        self.is_reconnecting = True
        self.event_router.set_reconnecting(True)
        chat_pane = self.query_one("#chat-pane", ChatPane)
        status_bar = self.query_one("#status-bar", StatusBar)

        while (
            self.is_reconnecting
            and self.reconnect_attempts < self.config.max_reconnect_attempts
        ):
            self.reconnect_attempts += 1

            # Calculate backoff delay
            backoff = min(
                self.config.initial_backoff
                * (self.config.backoff_multiplier ** (self.reconnect_attempts - 1)),
                self.config.max_backoff,
            )

            status_bar.connection_status = "reconnecting"
            chat_pane.add_system_message(
                f"Reconnecting in {backoff:.1f}s... "
                f"(attempt {self.reconnect_attempts}/{self.config.max_reconnect_attempts})"
            )

            await asyncio.sleep(backoff)

            # Attempt reconnection
            try:
                status_bar.connection_status = "connecting"
                await self.client.connect()

                if self.client.connected:
                    status_bar.connection_status = "connected"
                    status_bar.agent_status = "Re-initializing"
                    self.reconnect_attempts = 0
                    self.is_reconnecting = False
                    self.event_router.set_reconnecting(False)

                    chat_pane.add_system_message("✓ Reconnected successfully!")

                    # Re-initialize Zerg
                    await self.client.initialize_zerg()
                    status_bar.agent_status = "Ready"
                    chat_pane.add_system_message("Agent re-initialized. Ready!")
                    return

            except Exception as e:
                L.warning(f"Reconnection attempt {self.reconnect_attempts} failed: {e}")
                status_bar.connection_status = "disconnected"

        # Max attempts reached
        if self.reconnect_attempts >= self.config.max_reconnect_attempts:
            chat_pane.add_system_message(
                f"Failed to reconnect after {self.config.max_reconnect_attempts} attempts. "
                "Please check your connection and restart."
            )
            status_bar.agent_status = "Connection Failed"
            self.is_reconnecting = False
            self.event_router.set_reconnecting(False)

    def action_new_session(self) -> None:
        """Create a new session."""
        self.notify("New session feature coming soon!", severity="information")

    def action_list_sessions(self) -> None:
        """List all sessions."""
        self.notify("Session list feature coming soon!", severity="information")