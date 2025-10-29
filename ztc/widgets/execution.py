"""
Execution pane widget for displaying logs and command output.
"""

from rich.text import Text
from textual.app import ComposeResult
from textual.containers import ScrollableContainer
from textual.widgets import RichLog


class ExecutionPane(ScrollableContainer):
    """Execution pane for streaming logs and command output."""

    BINDINGS = [
        ("pageup", "page_up", "Scroll Up"),
        ("pagedown", "page_down", "Scroll Down"),
    ]

    def compose(self) -> ComposeResult:
        """Compose the execution pane."""
        yield RichLog(
            id="execution-log",
            wrap=True,
            highlight=True,
            markup=True,
            max_lines=500,  # Smaller buffer for execution pane
            auto_scroll=True,
        )

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

    def action_page_up(self) -> None:
        """Scroll up one page."""
        self.scroll_page_up()

    def action_page_down(self) -> None:
        """Scroll down one page."""
        self.scroll_page_down()