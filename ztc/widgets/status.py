"""
Status bar widget for displaying connection and agent status.
"""

from textual.reactive import reactive
from textual.widgets import Static


class StatusBar(Static):
    """Status bar showing connection and agent status."""

    DEFAULT_CSS = """
    StatusBar {
        dock: bottom;
        height: 1;
        background: $panel;
        color: $text;
        padding: 0 1;
    }

    StatusBar.connected {
        background: $success-darken-2;
    }

    StatusBar.connecting {
        background: $warning-darken-2;
    }

    StatusBar.disconnected {
        background: $error-darken-2;
    }
    """

    connection_status: reactive[str] = reactive("disconnected")
    agent_status: reactive[str] = reactive("Idle")

    def render(self) -> str:
        """Render the status bar content."""
        status_symbols = {
            "connected": "🟢",
            "connecting": "🟡",
            "reconnecting": "🟡",
            "disconnected": "🔴",
        }
        symbol = status_symbols.get(self.connection_status, "⚫")

        status_text = {
            "connected": "Connected",
            "connecting": "Connecting...",
            "reconnecting": f"Reconnecting...",
            "disconnected": "Disconnected",
        }.get(self.connection_status, "Unknown")

        return f"{symbol} {status_text} | Agent: {self.agent_status}"

    def watch_connection_status(self, old_status: str, new_status: str) -> None:
        """Update CSS class when connection status changes."""
        # Remove old class if it exists
        if old_status:
            self.remove_class(old_status)
        # Add new class
        self.add_class(new_status)