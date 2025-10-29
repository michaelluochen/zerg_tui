"""
Custom exception hierarchy for ZTC.
"""


class ZTCError(Exception):
    """Base exception for all ZTC errors."""

    pass


class ConnectionError(ZTCError):
    """Connection-related errors."""

    pass


class SocketIOConnectionError(ConnectionError):
    """Socket.IO connection specific errors."""

    pass


class ReconnectionError(ConnectionError):
    """Errors during reconnection attempts."""

    pass


class CommandError(ZTCError):
    """Command execution errors."""

    pass


class InvalidCommandError(CommandError):
    """Invalid command format or syntax."""

    pass


class CommandExecutionError(CommandError):
    """Error during command execution."""

    pass


class FileOperationError(ZTCError):
    """File operation errors."""

    pass


class FileUploadError(FileOperationError):
    """Error during file upload."""

    pass


class FileDownloadError(FileOperationError):
    """Error during file download."""

    pass


class ConfigurationError(ZTCError):
    """Configuration-related errors."""

    pass


class InvalidConfigError(ConfigurationError):
    """Invalid configuration values."""

    pass


class ConfigFileError(ConfigurationError):
    """Error reading or parsing configuration file."""

    pass


class EventError(ZTCError):
    """Event handling errors."""

    pass


class EventRoutingError(EventError):
    """Error routing events to handlers."""

    pass


class EventHandlerError(EventError):
    """Error in event handler execution."""

    pass


class UIError(ZTCError):
    """User interface errors."""

    pass


class WidgetError(UIError):
    """Widget-related errors."""

    pass


class RenderError(UIError):
    """Error during UI rendering."""

    pass