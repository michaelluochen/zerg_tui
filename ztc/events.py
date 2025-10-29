"""
Event handling and routing for ZTC.
"""

import logging
from typing import Any, Callable, Dict, Optional

from textual.message import Message

from .widgets import ChatPane, ExecutionPane, ReviewPane, StatusBar

L = logging.getLogger(__name__)


class ZergEvent(Message):
    """Custom message for Zerg events from Socket.IO."""

    def __init__(self, event_type: str, data: Dict[str, Any]) -> None:
        """
        Create a ZergEvent message.

        Args:
            event_type: Type of event (e.g., 'zerg_output', 'stdout', 'connection')
            data: Event data dictionary
        """
        self.event_type = event_type
        self.data = data
        super().__init__()


class EventRouter:
    """Routes Zerg events to appropriate panes."""

    def __init__(
        self,
        chat_pane: ChatPane,
        execution_pane: ExecutionPane,
        review_pane: ReviewPane,
        status_bar: StatusBar,
        reconnect_callback: Optional[Callable] = None,
    ) -> None:
        """
        Initialize the event router.

        Args:
            chat_pane: The chat pane widget
            execution_pane: The execution pane widget
            review_pane: The review pane widget
            status_bar: The status bar widget
            reconnect_callback: Optional callback for triggering reconnection
        """
        self.chat_pane = chat_pane
        self.execution_pane = execution_pane
        self.review_pane = review_pane
        self.status_bar = status_bar
        self.reconnect_callback = reconnect_callback
        self.is_reconnecting = False

        # Define the routing table
        self.routes: Dict[str, Callable[[ZergEvent], None]] = {
            "connection": self._handle_connection,
            "disconnect": self._handle_disconnect,
            # Agent messages
            "zerg_output": lambda e: self.chat_pane.add_agent_message(
                e.data.get("value", ""), e.event_type
            ),
            "zerg_reasoning": lambda e: self.chat_pane.add_agent_message(
                e.data.get("value", ""), e.event_type
            ),
            "zerg_error": lambda e: self.chat_pane.add_agent_message(
                e.data.get("value", ""), e.event_type
            ),
            "zerg_warning": lambda e: self.chat_pane.add_agent_message(
                e.data.get("value", ""), e.event_type
            ),
            "zerg_tests": lambda e: self.chat_pane.add_agent_message(
                e.data.get("value", ""), e.event_type
            ),
            "zerg_evals": lambda e: self.chat_pane.add_agent_message(
                e.data.get("value", ""), e.event_type
            ),
            "zerg_choices": lambda e: self.chat_pane.add_agent_message(
                e.data.get("value", ""), e.event_type
            ),
            # Execution output
            "stdout": lambda e: self.execution_pane.add_stdout(e.data.get("value", "")),
            "zerg_stdout": lambda e: self.execution_pane.add_stdout(e.data.get("value", "")),
            "stderr": lambda e: self.execution_pane.add_stderr(e.data.get("value", "")),
            "zerg_stderr": lambda e: self.execution_pane.add_stderr(e.data.get("value", "")),
            # Prompts
            "prompt": lambda e: self.chat_pane.add_agent_message(
                f"Prompt: {e.data.get('value', '')}", "prompt"
            ),
        }

    def route(self, event: ZergEvent) -> None:
        """
        Route an event to the appropriate handler.

        Args:
            event: The ZergEvent to route
        """
        try:
            handler = self.routes.get(event.event_type)
            if handler:
                handler(event)
            else:
                L.debug(f"No handler for event type: {event.event_type}")
        except Exception as e:
            L.error(f"Error handling event {event.event_type}: {e}")

    def _handle_connection(self, event: ZergEvent) -> None:
        """Handle connection events."""
        status = event.data.get("status", "unknown")
        if status == "connected":
            self.chat_pane.add_system_message("Connected to Zerg service")
            self.status_bar.connection_status = "connected"
        elif status == "disconnected":
            self.chat_pane.add_system_message("Disconnected from Zerg service")
            self.status_bar.connection_status = "disconnected"
            # Trigger reconnect if callback provided and not already reconnecting
            if self.reconnect_callback and not self.is_reconnecting:
                self.is_reconnecting = True
                self.reconnect_callback()

    def _handle_disconnect(self, event: ZergEvent) -> None:
        """Handle disconnect events."""
        self.status_bar.connection_status = "disconnected"
        self.chat_pane.add_system_message("Lost connection to Zerg service")
        # Trigger reconnect if callback provided and not already reconnecting
        if self.reconnect_callback and not self.is_reconnecting:
            self.is_reconnecting = True
            self.reconnect_callback()

    def set_reconnecting(self, reconnecting: bool) -> None:
        """Set the reconnecting state."""
        self.is_reconnecting = reconnecting