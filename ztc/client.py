"""
Zerg Socket.IO client for TUI interaction.
"""

import asyncio
import base64
import logging
from collections.abc import Callable
from typing import Any, Dict, Optional, Union

import socketio

L = logging.getLogger(__name__)


class ZergClient:
    """Zerg Socket.IO client adapted for Textual TUI."""

    def __init__(
        self,
        socket_url: str,
        event_callback: Optional[Callable[[str, Dict[str, Any]], None]] = None
    ) -> None:
        """
        Initialize the Zerg client.

        Args:
            socket_url: URL of the Zerg Socket.IO server (e.g., "http://localhost:3333")
            event_callback: Callback function to handle events: callback(event_type, data)
        """
        self.socket_url = socket_url
        self.sio = socketio.AsyncClient()
        self.connected: bool = False
        self.zerg_data: Dict[str, Any] = {}
        self.event_callback = event_callback

        # Dictates which channels are enabled / disabled
        self.channels: Dict[str, bool] = {
            "stdout": True,
            "stderr": True,
            "prompt": False,
            "system_prompt": False,
            "zerg_tests": True,
            "zerg_evals": True,
            "zerg_choices": True,
            "zerg_output": True,
            "zerg_reasoning": True,
            "zerg_error": True,
            "zerg_warning": True,
            "zerg_stdout": True,
            "zerg_stderr": True,
            "zerg_update": False,
        }

        # Set up handlers
        self.setup_handlers()

    def set_event_callback(self, callback: Callable[[str, Dict[str, Any]], None]) -> None:
        """Set or update the event callback function."""
        self.event_callback = callback

    def _handle_event(self, event_type: str, data: Dict[str, Any]) -> None:
        """Internal method to route events to callback."""
        if self.event_callback:
            try:
                self.event_callback(event_type, data)
            except Exception as e:
                L.error(f"Error in event callback for {event_type}: {e}")

    def set_channel(self, channel_name: str, value: bool) -> None:
        """Enable or disable a specific event channel."""
        if channel_name in self.channels:
            self.channels[channel_name] = value
        else:
            L.warning(f"Channel {channel_name} does not exist")

    def enable_channel(self, channel_name: str) -> None:
        """Enable a specific event channel."""
        self.set_channel(channel_name, True)

    def disable_channel(self, channel_name: str) -> None:
        """Disable a specific event channel."""
        self.set_channel(channel_name, False)

    def _register_channel_handler(self, event_type: str) -> None:
        """Register a channel-filtered event handler."""

        async def handler(data):
            if "value" in data and self.channels.get(event_type, False):
                self._handle_event(event_type, data)

        # Register the handler with the Socket.IO client
        self.sio.on(event_type)(handler)

    def setup_handlers(self) -> None:
        """Set up Socket.IO event handlers."""

        # Connection handlers
        @self.sio.event
        async def connect() -> None:
            self.connected = True
            L.info("Connected to Zerg server")
            self._handle_event("connection", {"status": "connected"})

        @self.sio.event
        async def disconnect() -> None:
            self.connected = False
            L.info("Disconnected from Zerg server")
            self._handle_event("connection", {"status": "disconnected"})
            self._handle_event("disconnect", {})

        # Register channel-based handlers
        channel_event_types = [
            "stdout",
            "stderr",
            "prompt",
            "system_prompt",
            "zerg_tests",
            "zerg_evals",
            "zerg_choices",
            "zerg_output",
            "zerg_reasoning",
            "zerg_error",
            "zerg_warning",
            "zerg_stdout",
            "zerg_stderr",
        ]

        for event_type in channel_event_types:
            self._register_channel_handler(event_type)

        # Special handler for zerg_update (has different logic)
        @self.sio.on("zerg_update")
        async def on_zerg_update(data):
            if "zerg" in data:
                self.zerg_data = data["zerg"]
                if self.channels.get("zerg_update", False):
                    self._handle_event("zerg_update", data)
            else:
                self.zerg_data = {}

    async def connect(self) -> None:
        """Connect to the Zerg Socket.IO server."""
        try:
            await self.sio.connect(self.socket_url)
            L.info(f"Connected to {self.socket_url}")
        except Exception as e:
            L.error(f"Error connecting to {self.socket_url}: {e}")
            raise

    async def disconnect(self) -> None:
        """Disconnect from the Zerg Socket.IO server."""
        await self.sio.disconnect()

    async def fetch_zerg_commands(self) -> None:
        """Fetch available Zerg commands."""
        L.info("Fetching Zerg commands...")
        await self.sio.emit("fetch_zerg_commands", {})

    async def initialize_zerg(self) -> None:
        """Initialize the Zerg agent."""
        L.info("Initializing Zerg...")
        await self.sio.emit("initialize_zerg", {})

    async def zerg_command(self, cmd_value: str) -> None:
        """
        Send a command to the Zerg agent.

        Args:
            cmd_value: The command string to execute
        """
        L.info(f"Sending command: {cmd_value}")
        await self.sio.emit("zerg_command", {"command": cmd_value})

    async def update_zerg(self) -> None:
        """Request a full Zerg state update."""
        L.info("Requesting Zerg update...")
        await self.sio.emit("request_zerg_update", {})

    async def upload_file(self, filename: str, content: Union[bytes, str]) -> None:
        """
        Upload a file to the Zerg workspace.

        Args:
            filename: Name of the file to upload
            content: File content (string or bytes)
        """
        try:
            # Convert content to base64
            content_bytes = content.encode("utf-8") if isinstance(content, str) else content
            base64_data = base64.b64encode(content_bytes).decode("utf-8")

            L.info(f"Uploading file: {filename}")
            await self.sio.emit("upload_file", {"filename": filename, "file_data": base64_data})
        except Exception as e:
            L.error(f"Error uploading file {filename}: {e}")
            raise

    async def download_file(self, filename: str) -> Optional[bytes]:
        """
        Download a file from the Zerg workspace.

        Args:
            filename: Name of the file to download

        Returns:
            File content as bytes, or None if error
        """
        L.info(f"Downloading file: {filename}")

        # Create a future to wait for the response
        future = asyncio.Future()

        @self.sio.on("download_file_response")
        def handle_download_response(response):
            if "error" in response:
                future.set_exception(Exception(response["error"]))
            else:
                # Decode base64 data
                file_data = base64.b64decode(response["file_data"])
                future.set_result(file_data)

            # Remove this handler after receiving the response
            self.sio.off("download_file_response")

        # Request the file
        await self.sio.emit("request_file_download", {"filename": filename})

        # Wait for the response
        try:
            return await future
        except Exception as e:
            L.error(f"Error downloading file {filename}: {e}")
            return None
