"""
Chat-related widgets for ZTC.
"""

from typing import List, Optional

from rich.text import Text
from textual.app import ComposeResult
from textual.containers import ScrollableContainer
from textual.events import Key
from textual.widgets import Input, RichLog


class CommandInput(Input):
    """Input widget with command history support."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.command_history: List[str] = []
        self.history_index: int = -1
        self.current_draft: str = ""  # Store current typing when navigating history
        self.max_history: int = 100  # Maximum number of commands to store

    def add_to_history(self, command: str) -> None:
        """Add command to history, avoiding duplicates at the top."""
        if command and command.strip():
            # Remove the command if it already exists (to move it to top)
            if command in self.command_history:
                self.command_history.remove(command)
            # Add to the front
            self.command_history.insert(0, command)
            # Limit history size
            if len(self.command_history) > self.max_history:
                self.command_history.pop()

    def on_key(self, event: Key) -> None:
        """Handle arrow key events for history navigation."""
        if event.key == "up":
            # Navigate backward in history (older commands)
            if self.history_index < len(self.command_history) - 1:
                if self.history_index == -1:
                    # Store current input before navigating
                    self.current_draft = self.value
                self.history_index += 1
                self.value = self.command_history[self.history_index]
                self.cursor_position = len(self.value)
                event.stop()

        elif event.key == "down":
            # Navigate forward in history (newer commands)
            if self.history_index > 0:
                self.history_index -= 1
                self.value = self.command_history[self.history_index]
                self.cursor_position = len(self.value)
                event.stop()
            elif self.history_index == 0:
                # Restore draft or clear
                self.history_index = -1
                self.value = self.current_draft
                self.cursor_position = len(self.value)
                event.stop()

    def on_input_submitted(self, event: Input.Submitted) -> None:
        """Reset history index and add command to history when submitted."""
        if self.value.strip():
            self.add_to_history(self.value)
        self.history_index = -1
        self.current_draft = ""


class ChatPane(ScrollableContainer):
    """Chat pane for agent communication."""

    BINDINGS = [
        ("pageup", "page_up", "Scroll Up"),
        ("pagedown", "page_down", "Scroll Down"),
        ("home", "scroll_home", "Top"),
        ("end", "scroll_end", "Bottom"),
    ]

    def compose(self) -> ComposeResult:
        """Compose the chat pane."""
        yield RichLog(
            id="chat-log",
            wrap=True,
            highlight=True,
            markup=True,
            max_lines=1000,  # Limit buffer to prevent memory issues
            auto_scroll=True,  # Auto-scroll to new content
        )
        yield CommandInput(placeholder="Type a command or message...", id="chat-input")

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

    def action_page_up(self) -> None:
        """Scroll up one page."""
        self.scroll_page_up()

    def action_page_down(self) -> None:
        """Scroll down one page."""
        self.scroll_page_down()

    def action_scroll_home(self) -> None:
        """Scroll to top."""
        self.scroll_home(animate=True)

    def action_scroll_end(self) -> None:
        """Scroll to bottom."""
        self.scroll_end(animate=True)