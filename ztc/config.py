"""
Configuration management for ZTC.
"""

import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional


@dataclass
class ZTCConfig:
    """Configuration for the Zerg Terminal Client."""

    # Server configuration
    socket_url: str = field(
        default_factory=lambda: os.environ.get("ZTC_SOCKET_URL", "http://localhost:3333")
    )

    # Reconnection settings
    max_reconnect_attempts: int = 5
    initial_backoff: float = 1.0  # seconds
    max_backoff: float = 60.0  # seconds
    backoff_multiplier: float = 2.0

    # UI settings
    chat_log_max_lines: int = 1000
    review_log_max_lines: int = 500
    execution_log_max_lines: int = 500
    command_history_size: int = 100

    # Workspace settings
    workspace: Path = field(default_factory=Path.cwd)
    batch_mode: bool = False
    yolo_mode: bool = False
    debug_mode: bool = False

    # File paths
    history_file: Optional[Path] = field(
        default_factory=lambda: Path.home() / ".ztc_history"
    )
    config_file: Optional[Path] = field(
        default_factory=lambda: Path.home() / ".ztcrc"
    )

    @classmethod
    def from_cli(
        cls,
        workspace: Optional[Path] = None,
        batch: bool = False,
        yolo: bool = False,
        debug: bool = False,
        **kwargs,
    ) -> "ZTCConfig":
        """
        Create config from CLI arguments.

        Args:
            workspace: Workspace directory
            batch: Enable batch mode
            yolo: Enable YOLO mode
            debug: Enable debug mode
            **kwargs: Additional config options

        Returns:
            ZTCConfig instance
        """
        return cls(
            workspace=workspace or Path.cwd(),
            batch_mode=batch,
            yolo_mode=yolo,
            debug_mode=debug,
            **kwargs,
        )

    @classmethod
    def from_file(cls, path: Path) -> "ZTCConfig":
        """
        Load config from a file (JSON or TOML).

        Args:
            path: Path to config file

        Returns:
            ZTCConfig instance

        Raises:
            NotImplementedError: Config file loading not yet implemented
        """
        # TODO: Implement config file loading (JSON/TOML)
        raise NotImplementedError("Config file loading not yet implemented")

    @classmethod
    def from_env(cls) -> "ZTCConfig":
        """
        Create config from environment variables.

        Environment variables:
            ZTC_SOCKET_URL: Socket.IO server URL
            ZTC_WORKSPACE: Workspace directory
            ZTC_BATCH_MODE: Enable batch mode (1/true/yes)
            ZTC_YOLO_MODE: Enable YOLO mode (1/true/yes)
            ZTC_DEBUG_MODE: Enable debug mode (1/true/yes)
            ZTC_MAX_RECONNECT_ATTEMPTS: Maximum reconnection attempts
            ZTC_INITIAL_BACKOFF: Initial backoff in seconds
            ZTC_MAX_BACKOFF: Maximum backoff in seconds

        Returns:
            ZTCConfig instance
        """

        def parse_bool(value: str) -> bool:
            return value.lower() in ("1", "true", "yes")

        return cls(
            socket_url=os.environ.get("ZTC_SOCKET_URL", "http://localhost:3333"),
            workspace=Path(os.environ.get("ZTC_WORKSPACE", Path.cwd())),
            batch_mode=parse_bool(os.environ.get("ZTC_BATCH_MODE", "")),
            yolo_mode=parse_bool(os.environ.get("ZTC_YOLO_MODE", "")),
            debug_mode=parse_bool(os.environ.get("ZTC_DEBUG_MODE", "")),
            max_reconnect_attempts=int(
                os.environ.get("ZTC_MAX_RECONNECT_ATTEMPTS", "5")
            ),
            initial_backoff=float(os.environ.get("ZTC_INITIAL_BACKOFF", "1.0")),
            max_backoff=float(os.environ.get("ZTC_MAX_BACKOFF", "60.0")),
        )

    def merge_with_env(self) -> "ZTCConfig":
        """
        Merge current config with environment variables.

        Environment variables take precedence over existing values.

        Returns:
            Updated ZTCConfig instance
        """
        env_config = self.from_env()
        # Update only if env var was explicitly set
        if "ZTC_SOCKET_URL" in os.environ:
            self.socket_url = env_config.socket_url
        if "ZTC_WORKSPACE" in os.environ:
            self.workspace = env_config.workspace
        if "ZTC_BATCH_MODE" in os.environ:
            self.batch_mode = env_config.batch_mode
        if "ZTC_YOLO_MODE" in os.environ:
            self.yolo_mode = env_config.yolo_mode
        if "ZTC_DEBUG_MODE" in os.environ:
            self.debug_mode = env_config.debug_mode
        if "ZTC_MAX_RECONNECT_ATTEMPTS" in os.environ:
            self.max_reconnect_attempts = env_config.max_reconnect_attempts
        if "ZTC_INITIAL_BACKOFF" in os.environ:
            self.initial_backoff = env_config.initial_backoff
        if "ZTC_MAX_BACKOFF" in os.environ:
            self.max_backoff = env_config.max_backoff
        return self