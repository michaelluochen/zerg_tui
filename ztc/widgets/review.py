"""
Review pane widget for displaying diffs and code changes.
"""

from rich.text import Text
from textual.app import ComposeResult
from textual.containers import ScrollableContainer
from textual.widgets import RichLog


class ReviewPane(ScrollableContainer):
    """Review pane for diffs and code changes."""

    BINDINGS = [
        ("pageup", "page_up", "Scroll Up"),
        ("pagedown", "page_down", "Scroll Down"),
    ]

    def compose(self) -> ComposeResult:
        """Compose the review pane."""
        yield RichLog(
            id="review-log",
            wrap=True,
            highlight=True,
            markup=True,
            max_lines=500,  # Smaller buffer for review pane
            auto_scroll=True,
        )

    def on_mount(self) -> None:
        """Initialize the review pane."""
        review_log = self.query_one("#review-log", RichLog)
        review_log.write(Text("Review Pane", style="bold"))
        review_log.write(Text("Code Review (Coming Soon)", style="dim italic"))

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

    def action_page_up(self) -> None:
        """Scroll up one page."""
        self.scroll_page_up()

    def action_page_down(self) -> None:
        """Scroll down one page."""
        self.scroll_page_down()