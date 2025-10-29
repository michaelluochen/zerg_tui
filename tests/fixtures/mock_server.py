"""
Mock Zerg Socket.IO server for testing.

Mimics the behavior of the real Zerg service without requiring the full backend.
"""

import asyncio
import logging

import socketio
from aiohttp import web

L = logging.getLogger(__name__)


class MockZergServer:
    """
    Mock Zerg server that implements the Socket.IO protocol.

    Used for integration tests to avoid dependency on running Zerg service.
    """

    def __init__(self, port: int = 3334):
        """
        Initialize the mock server.

        Args:
            port: Port to run the server on (default 3334 to avoid conflict with real Zerg)
        """
        self.port = port
        self.sio = socketio.AsyncServer(async_mode="aiohttp", cors_allowed_origins="*")
        self.app = web.Application()
        self.sio.attach(self.app)
        self.runner = None
        self.site = None

        # Storage for uploaded files
        self.files = {}

        # Track connected clients
        self.connected_clients = set()

        # Setup event handlers
        self._setup_handlers()

    def _setup_handlers(self):
        """Set up Socket.IO event handlers."""

        @self.sio.event
        async def connect(sid, environ):
            """Handle client connection."""
            self.connected_clients.add(sid)
            L.info(f"Mock server: Client connected: {sid}")

            # Send welcome message
            await self.sio.emit(
                "stdout",
                {
                    "value": "mock zerg service connected",
                    "timestamp": asyncio.get_event_loop().time(),
                },
                room=sid,
            )

        @self.sio.event
        async def disconnect(sid):
            """Handle client disconnection."""
            self.connected_clients.discard(sid)
            L.info(f"Mock server: Client disconnected: {sid}")

        @self.sio.on("initialize_zerg")
        async def on_initialize(sid, data):
            """Handle Zerg initialization request."""
            L.info(f"Mock server: Initializing Zerg for {sid}")

            # Simulate initialization sequence
            await self.sio.emit(
                "zerg_output",
                {"value": "Hello, I'm Mock Zerg!", "timestamp": asyncio.get_event_loop().time()},
                room=sid,
            )

            await asyncio.sleep(0.05)

            await self.sio.emit(
                "zerg_output",
                {
                    "value": "Mock Zerg initialized and ready",
                    "timestamp": asyncio.get_event_loop().time(),
                },
                room=sid,
            )

            await self.sio.emit(
                "stdout",
                {
                    "value": "zerg initialized and updated",
                    "timestamp": asyncio.get_event_loop().time(),
                },
                room=sid,
            )

        @self.sio.on("zerg_command")
        async def on_command(sid, data):
            """Handle Zerg command."""
            command = data.get("command", "")
            L.info(f"Mock server: Received command from {sid}: {command}")

            # Simulate command processing
            await self.sio.emit(
                "zerg_output",
                {
                    "value": f"Processing command: {command}",
                    "timestamp": asyncio.get_event_loop().time(),
                },
                room=sid,
            )

            await asyncio.sleep(0.1)

            await self.sio.emit(
                "zerg_output",
                {
                    "value": f"Command completed: {command}",
                    "timestamp": asyncio.get_event_loop().time(),
                },
                room=sid,
            )

        @self.sio.on("request_zerg_update")
        async def on_update_request(sid, data):
            """Handle Zerg update request."""
            L.info(f"Mock server: Update requested by {sid}")

            await self.sio.emit(
                "stdout",
                {"value": "zerg updated", "timestamp": asyncio.get_event_loop().time()},
                room=sid,
            )

            # Send mock zerg_update event
            await self.sio.emit(
                "zerg_update",
                {
                    "zerg": {"status": "IDLE", "workspace": "/mock/workspace", "mock": True},
                    "timestamp": asyncio.get_event_loop().time(),
                },
                room=sid,
            )

        @self.sio.on("upload_file")
        async def on_upload(sid, data):
            """Handle file upload."""
            filename = data.get("filename")
            file_data = data.get("file_data")  # base64 encoded

            self.files[filename] = file_data
            L.info(f"Mock server: File uploaded: {filename}")

            await self.sio.emit(
                "zerg_output",
                {
                    "value": f"File uploaded successfully: {filename}",
                    "timestamp": asyncio.get_event_loop().time(),
                },
                room=sid,
            )

        @self.sio.on("request_file_download")
        async def on_download_request(sid, data):
            """Handle file download request."""
            filename = data.get("filename")
            L.info(f"Mock server: Download requested: {filename}")

            if filename in self.files:
                await self.sio.emit(
                    "download_file_response",
                    {"filename": filename, "file_data": self.files[filename]},
                    room=sid,
                )
            else:
                await self.sio.emit(
                    "download_file_response", {"error": f"File not found: {filename}"}, room=sid
                )

        @self.sio.on("fetch_zerg_commands")
        async def on_fetch_commands(sid, data):
            """Handle command list request."""
            L.info(f"Mock server: Commands requested by {sid}")

            # Send mock command list
            await self.sio.emit(
                "zerg_output",
                {
                    "value": "Available commands: init, cmd, update, upload, download",
                    "timestamp": asyncio.get_event_loop().time(),
                },
                room=sid,
            )

    async def start(self):
        """Start the mock server."""
        self.runner = web.AppRunner(self.app)
        await self.runner.setup()
        self.site = web.TCPSite(self.runner, "localhost", self.port)
        await self.site.start()
        L.info(f"Mock Zerg server started on http://localhost:{self.port}")

    async def stop(self):
        """Stop the mock server."""
        if self.site:
            await self.site.stop()
        if self.runner:
            await self.runner.cleanup()
        L.info("Mock Zerg server stopped")

    async def emit_event(self, event_type: str, data: dict, sid: str = None):
        """
        Manually emit an event to a specific client or all clients.

        Args:
            event_type: Type of event to emit
            data: Event data
            sid: Specific client ID, or None for broadcast
        """
        if sid:
            await self.sio.emit(event_type, data, room=sid)
        else:
            await self.sio.emit(event_type, data)
