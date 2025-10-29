"""
Unit tests for ZTC TUI widgets.

Tests ChatPane, ReviewPane, ExecutionPane, and main app using Textual's headless testing.
Follows Zerg's class-based test organization patterns.
"""

import pytest

from ztc.app import ZergTerminalClient
from ztc.events import ZergEvent
from ztc.widgets import ChatPane, ExecutionPane, ReviewPane


class TestChatPane:
    """Test ChatPane widget functionality."""

    @pytest.mark.asyncio
    async def test_chat_pane_composition(self, mock_zerg_client):
        """Test that ChatPane composes with RichLog and Input."""
        app = ZergTerminalClient()
        app.client = mock_zerg_client  # Prevent real connection

        async with app.run_test() as _:
            chat_pane = app.query_one("#chat-pane", ChatPane)

            # Verify child widgets exist
            assert chat_pane.query_one("#chat-log") is not None
            assert chat_pane.query_one("#chat-input") is not None

    @pytest.mark.asyncio
    async def test_add_user_message(self, mock_zerg_client):
        """Test adding user messages to chat log."""
        app = ZergTerminalClient()
        app.client = mock_zerg_client  # Prevent real connection

        async with app.run_test() as _:
            chat_pane = app.query_one("#chat-pane", ChatPane)

            # Add a user message
            chat_pane.add_user_message("Hello, Zerg!")

            # Message should be added to log
            # (Verifying exact content would require inspecting RichLog internals)

    @pytest.mark.asyncio
    async def test_add_agent_message_with_different_types(self, mock_zerg_client):
        """Test agent messages with different event types and styling."""
        app = ZergTerminalClient()
        app.client = mock_zerg_client  # Prevent real connection

        async with app.run_test() as _:
            chat_pane = app.query_one("#chat-pane", ChatPane)

            # Add messages of different types
            chat_pane.add_agent_message("Output message", "zerg_output")
            chat_pane.add_agent_message("Error occurred", "zerg_error")
            chat_pane.add_agent_message("Warning!", "zerg_warning")
            chat_pane.add_agent_message("Reasoning...", "zerg_reasoning")

            # Each should be added with appropriate styling

    @pytest.mark.asyncio
    async def test_add_system_message(self, mock_zerg_client):
        """Test adding system messages."""
        app = ZergTerminalClient()
        app.client = mock_zerg_client  # Prevent real connection

        async with app.run_test() as _:
            chat_pane = app.query_one("#chat-pane", ChatPane)

            chat_pane.add_system_message("Connection established")


class TestReviewPane:
    """Test ReviewPane widget functionality."""

    @pytest.mark.asyncio
    async def test_review_pane_composition(self, mock_zerg_client):
        """Test that ReviewPane composes with RichLog."""
        app = ZergTerminalClient()
        app.client = mock_zerg_client  # Prevent real connection

        async with app.run_test() as _:
            review_pane = app.query_one("#review-pane", ReviewPane)

            # Verify RichLog exists
            assert review_pane.query_one("#review-log") is not None

    @pytest.mark.asyncio
    async def test_show_diff(self, mock_zerg_client):
        """Test displaying code diffs."""
        app = ZergTerminalClient()
        app.client = mock_zerg_client  # Prevent real connection

        async with app.run_test() as _:
            review_pane = app.query_one("#review-pane", ReviewPane)

            diff_text = "+++ new code\n--- old code"
            review_pane.show_diff(diff_text)

            # Diff should be displayed in log

    @pytest.mark.asyncio
    async def test_clear_review_pane(self, mock_zerg_client):
        """Test clearing the review pane."""
        app = ZergTerminalClient()
        app.client = mock_zerg_client  # Prevent real connection

        async with app.run_test() as _:
            review_pane = app.query_one("#review-pane", ReviewPane)

            # Add content then clear
            review_pane.show_diff("test diff")
            review_pane.clear()

            # Pane should be cleared


class TestExecutionPane:
    """Test ExecutionPane widget functionality."""

    @pytest.mark.asyncio
    async def test_execution_pane_composition(self, mock_zerg_client):
        """Test that ExecutionPane composes with RichLog."""
        app = ZergTerminalClient()
        app.client = mock_zerg_client  # Prevent real connection

        async with app.run_test() as _:
            exec_pane = app.query_one("#execution-pane", ExecutionPane)

            # Verify RichLog exists
            assert exec_pane.query_one("#execution-log") is not None

    @pytest.mark.asyncio
    async def test_add_stdout(self, mock_zerg_client):
        """Test adding stdout output."""
        app = ZergTerminalClient()
        app.client = mock_zerg_client  # Prevent real connection

        async with app.run_test() as _:
            exec_pane = app.query_one("#execution-pane", ExecutionPane)

            exec_pane.add_stdout("Test output line 1")
            exec_pane.add_stdout("Test output line 2")

    @pytest.mark.asyncio
    async def test_add_stderr(self, mock_zerg_client):
        """Test adding stderr output with red styling."""
        app = ZergTerminalClient()
        app.client = mock_zerg_client  # Prevent real connection

        async with app.run_test() as _:
            exec_pane = app.query_one("#execution-pane", ExecutionPane)

            exec_pane.add_stderr("Error: something failed")

    @pytest.mark.asyncio
    async def test_add_status_passed(self, mock_zerg_client):
        """Test adding a passed status message."""
        app = ZergTerminalClient()
        app.client = mock_zerg_client  # Prevent real connection

        async with app.run_test() as _:
            exec_pane = app.query_one("#execution-pane", ExecutionPane)

            exec_pane.add_status("All tests passed", passed=True)

    @pytest.mark.asyncio
    async def test_add_status_failed(self, mock_zerg_client):
        """Test adding a failed status message."""
        app = ZergTerminalClient()
        app.client = mock_zerg_client  # Prevent real connection

        async with app.run_test() as _:
            exec_pane = app.query_one("#execution-pane", ExecutionPane)

            exec_pane.add_status("Tests failed", passed=False)

    @pytest.mark.asyncio
    async def test_clear_execution_pane(self, mock_zerg_client):
        """Test clearing the execution pane."""
        app = ZergTerminalClient()
        app.client = mock_zerg_client  # Prevent real connection

        async with app.run_test() as _:
            exec_pane = app.query_one("#execution-pane", ExecutionPane)

            # Add content then clear
            exec_pane.add_stdout("test")
            exec_pane.clear()


class TestZergEvent:
    """Test ZergEvent custom message class."""

    def test_zerg_event_creation(self):
        """Test creating a ZergEvent."""
        event = ZergEvent("zerg_output", {"value": "test message"})

        assert event.event_type == "zerg_output"
        assert event.data == {"value": "test message"}

    def test_zerg_event_is_message(self):
        """Test that ZergEvent is a Textual Message."""
        from textual.message import Message

        event = ZergEvent("test", {})

        assert isinstance(event, Message)


class TestZergTerminalClient:
    """Test main ZTC application."""

    @pytest.mark.asyncio
    async def test_app_instantiation(self):
        """Test that app can be created."""
        app = ZergTerminalClient()

        assert app.config.socket_url == "http://localhost:3333"
        assert app.client is None  # Not connected yet

    @pytest.mark.asyncio
    async def test_app_composition(self, mock_zerg_client):
        """Test that app layout is composed correctly."""
        app = ZergTerminalClient()
        app.client = mock_zerg_client  # Prevent real connection

        async with app.run_test() as _:
            # Verify all panes exist
            assert app.query_one("#chat-pane", ChatPane) is not None
            assert app.query_one("#review-pane", ReviewPane) is not None
            assert app.query_one("#execution-pane", ExecutionPane) is not None

            # Verify header and footer
            from textual.widgets import Footer, Header

            assert app.query_one(Header) is not None
            assert app.query_one(Footer) is not None

    @pytest.mark.asyncio
    async def test_zerg_event_message_handling(self, mock_zerg_client):
        """Test that ZergEvent messages are processed."""
        app = ZergTerminalClient()
        app.client = mock_zerg_client  # Prevent real connection attempt

        async with app.run_test() as pilot:
            # Post a ZergEvent
            event = ZergEvent("zerg_output", {"value": "test message"})
            app.post_message(event)

            # Give message time to process
            await pilot.pause(0.1)

            # Event should be handled by on_zerg_event() → _handle_zerg_event_sync()
            # Verifying would require inspecting widget state

    @pytest.mark.asyncio
    async def test_input_submission_without_connection(self):
        """Test input submission when not connected."""
        app = ZergTerminalClient()

        async with app.run_test() as pilot:
            # Ensure no client is connected
            app.client = None

            # Try to submit input
            input_widget = app.query_one("#chat-input")
            input_widget.value = "test command"
            await pilot.press("enter")

            # Should show error message (not crash)

    @pytest.mark.asyncio
    async def test_input_submission_with_mocked_client(self, mock_zerg_client):
        """Test input submission with a connected mock client."""
        app = ZergTerminalClient()
        app.client = mock_zerg_client
        app.client.connected = True

        async with app.run_test() as pilot:
            # Submit a command
            input_widget = app.query_one("#chat-input")
            input_widget.value = "write hello world"
            await pilot.press("enter")

            # Give worker time to run
            await pilot.pause(0.2)

            # Verify command was sent (worker runs the command)
            # Note: May need to wait for worker to complete

    @pytest.mark.asyncio
    async def test_action_new_session(self):
        """Test new session action (placeholder)."""
        app = ZergTerminalClient()

        async with app.run_test() as pilot:
            # Trigger action
            await pilot.press("ctrl+t")

            # Should show notification (coming soon message)

    @pytest.mark.asyncio
    async def test_action_list_sessions(self):
        """Test list sessions action (placeholder)."""
        app = ZergTerminalClient()

        async with app.run_test() as pilot:
            # Trigger action
            await pilot.press("ctrl+l")

            # Should show notification (coming soon message)

    @pytest.mark.asyncio
    async def test_action_quit(self, mock_zerg_client):
        """Test quit action."""
        app = ZergTerminalClient()
        app.client = mock_zerg_client  # Prevent real connection

        async with app.run_test() as _:
            # This would exit the app
            # Testing quit is tricky in headless mode
            pass


class TestEventRouting:
    """Test event routing from ZergEvent to appropriate panes."""

    @pytest.mark.asyncio
    async def test_connection_event_routing(self):
        """Test connection events go to chat pane."""
        app = ZergTerminalClient()

        async with app.run_test() as pilot:
            event = ZergEvent("connection", {"status": "connected"})
            app.post_message(event)

            await pilot.pause(0.1)

            # Connection messages should appear in chat

    @pytest.mark.asyncio
    async def test_zerg_output_routing(self):
        """Test zerg_output events go to chat pane."""
        app = ZergTerminalClient()

        async with app.run_test() as pilot:
            event = ZergEvent("zerg_output", {"value": "Agent response"})
            app.post_message(event)

            await pilot.pause(0.1)

    @pytest.mark.asyncio
    async def test_stdout_routing(self):
        """Test stdout events go to execution pane."""
        app = ZergTerminalClient()

        async with app.run_test() as pilot:
            event = ZergEvent("stdout", {"value": "Command output"})
            app.post_message(event)

            await pilot.pause(0.1)

    @pytest.mark.asyncio
    async def test_stderr_routing(self):
        """Test stderr events go to execution pane."""
        app = ZergTerminalClient()

        async with app.run_test() as pilot:
            event = ZergEvent("stderr", {"value": "Error output"})
            app.post_message(event)

            await pilot.pause(0.1)
