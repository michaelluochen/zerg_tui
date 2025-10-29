"""
Shared pytest fixtures and configuration for ZTC tests.

Follows patterns from Zerg's test suite.
"""

from unittest.mock import AsyncMock, Mock

import pytest

from ztc.client import ZergClient
from ztc.main import ZergTerminalClient


@pytest.fixture
def mock_event_callback():
    """Create a mock event callback function."""
    return Mock()


@pytest.fixture
def zerg_client(mock_event_callback):
    """Create a ZergClient instance with mocked Socket.IO."""
    client = ZergClient("http://localhost:3333", event_callback=mock_event_callback)
    # Replace sio with a mock
    client.sio = Mock()
    client.sio.emit = AsyncMock()
    client.sio.connect = AsyncMock()
    client.sio.disconnect = AsyncMock()
    client.sio.on = Mock()
    client.sio.off = Mock()
    return client


@pytest.fixture
def ztc_app():
    """Create a ZTC app instance for testing."""
    app = ZergTerminalClient()
    return app


@pytest.fixture
def mock_zerg_client():
    """Create a fully mocked ZergClient for TUI testing."""
    client = Mock(spec=ZergClient)
    client.connected = False
    client.connect = AsyncMock()
    client.disconnect = AsyncMock()
    client.zerg_command = AsyncMock()
    client.initialize_zerg = AsyncMock()
    client.update_zerg = AsyncMock()
    client.upload_file = AsyncMock()
    client.download_file = AsyncMock()
    return client


# Configure pytest-asyncio
pytest_plugins = ("pytest_asyncio",)
