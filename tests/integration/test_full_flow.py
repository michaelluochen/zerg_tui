"""
Integration tests for ZTC.

Tests the full flow with a mock Socket.IO server.
Marked with @pytest.mark.integration to run separately.
"""

import asyncio

import pytest

from tests.fixtures.mock_server import MockZergServer
from ztc.client import ZergClient
from ztc.main import ZergTerminalClient


@pytest.fixture
async def mock_server():
    """
    Start a mock Zerg Socket.IO server for testing.

    Runs on port 3334 to avoid conflicts with real Zerg service.
    """
    server = MockZergServer(port=3334)
    await server.start()

    # Give server time to start
    await asyncio.sleep(0.2)

    yield server

    # Cleanup
    await server.stop()


class TestClientServerIntegration:
    """Test ZergClient with mock server."""

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_connect_and_disconnect(self, mock_server):
        """Test full connection lifecycle."""
        # Track events
        events_received = []

        def callback(event_type, data):
            events_received.append((event_type, data))

        # Create client pointing to mock server
        client = ZergClient("http://localhost:3334", event_callback=callback)

        # Connect
        await client.connect()
        assert client.connected

        # Wait for connection event
        await asyncio.sleep(0.2)

        # Verify connection event was received
        assert any(e[0] == "connection" for e in events_received)

        # Disconnect
        await client.disconnect()
        await asyncio.sleep(0.2)

        # Verify disconnection event
        assert any(
            e[0] == "connection" and e[1].get("status") == "disconnected" for e in events_received
        )

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_initialize_zerg_flow(self, mock_server):
        """Test Zerg initialization flow."""
        events_received = []

        def callback(event_type, data):
            events_received.append((event_type, data))

        client = ZergClient("http://localhost:3334", event_callback=callback)
        await client.connect()

        # Initialize
        await client.initialize_zerg()

        # Wait for response
        await asyncio.sleep(0.3)

        # Verify initialization events
        output_events = [e for e in events_received if e[0] == "zerg_output"]
        assert len(output_events) > 0
        assert any("Mock Zerg" in str(e[1].get("value", "")) for e in output_events)

        await client.disconnect()

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_command_response_flow(self, mock_server):
        """Test sending command and receiving response."""
        events_received = []

        def callback(event_type, data):
            events_received.append((event_type, data))

        client = ZergClient("http://localhost:3334", event_callback=callback)
        await client.connect()
        await client.initialize_zerg()

        # Clear previous events
        events_received.clear()

        # Send command
        await client.zerg_command("test command")

        # Wait for response
        await asyncio.sleep(0.3)

        # Verify command was processed
        output_events = [e for e in events_received if e[0] == "zerg_output"]
        assert any("Processing command" in str(e[1].get("value", "")) for e in output_events)

        await client.disconnect()

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_file_upload_download_flow(self, mock_server):
        """Test file upload and download cycle."""
        client = ZergClient("http://localhost:3334")
        await client.connect()

        # Upload a file
        test_content = "Hello from test!"
        await client.upload_file("test.txt", test_content)
        await asyncio.sleep(0.2)

        # Download the file
        downloaded = await client.download_file("test.txt")
        await asyncio.sleep(0.2)

        # Verify content matches
        # Note: download returns bytes
        assert downloaded == test_content.encode("utf-8")

        await client.disconnect()

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_update_zerg_flow(self, mock_server):
        """Test requesting Zerg state update."""
        events_received = []

        def callback(event_type, data):
            events_received.append((event_type, data))

        client = ZergClient("http://localhost:3334", event_callback=callback)
        client.enable_channel("zerg_update")  # Enable channel to receive update events
        await client.connect()

        # Request update
        await client.update_zerg()

        # Wait for response
        await asyncio.sleep(0.2)

        # Verify update events
        assert any(e[0] == "zerg_update" for e in events_received)

        await client.disconnect()


class TestTUIIntegration:
    """Test TUI with mock server."""

    @pytest.mark.integration
    @pytest.mark.slow
    @pytest.mark.asyncio
    async def test_tui_connects_to_mock_server(self, mock_server):
        """Test TUI app connecting to mock server."""
        app = ZergTerminalClient()
        app.socket_url = "http://localhost:3334"  # Point to mock server

        async with app.run_test() as pilot:
            # Wait for connection
            await pilot.pause(0.8)

            # Verify client is connected
            assert app.client is not None
            assert app.client.connected

    @pytest.mark.integration
    @pytest.mark.slow
    @pytest.mark.asyncio
    async def test_tui_send_command_flow(self, mock_server):
        """Test full TUI command flow with mock server."""
        app = ZergTerminalClient()
        app.socket_url = "http://localhost:3334"

        async with app.run_test() as pilot:
            # Wait for connection and initialization
            await pilot.pause(0.8)

            # Type command in input
            input_widget = app.query_one("#chat-input")
            input_widget.value = "test command"
            await pilot.press("enter")

            # Wait for command to be sent and response received
            await pilot.pause(0.5)

            # Command should have been sent and response received
            # (Response would appear in chat pane)

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_multiple_commands_sequence(self, mock_server):
        """Test sending multiple commands in sequence."""
        events_received = []

        def callback(event_type, data):
            events_received.append((event_type, data))

        client = ZergClient("http://localhost:3334", event_callback=callback)
        await client.connect()
        await client.initialize_zerg()

        # Send multiple commands
        await client.zerg_command("command 1")
        await asyncio.sleep(0.2)

        await client.zerg_command("command 2")
        await asyncio.sleep(0.2)

        await client.update_zerg()
        await asyncio.sleep(0.2)

        # Verify all events were received
        output_events = [e for e in events_received if e[0] == "zerg_output"]
        assert len(output_events) >= 4  # init messages + command responses

        await client.disconnect()
