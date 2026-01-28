"""Configuration loading and validation for XRP Ticker."""

import logging
import os
import tomllib
from pathlib import Path
from typing import Final

from pydantic import BaseModel, Field, field_validator, model_validator

from .security import (
    REQUEST_TIMEOUT_SECONDS,
    XRP_ADDRESS_MAX_LENGTH,
    XRP_ADDRESS_MIN_LENGTH,
    XRP_ADDRESS_PATTERN,
)

logger = logging.getLogger(__name__)

# Configuration limits
MAX_CONFIG_FILE_SIZE: Final[int] = 64 * 1024  # 64KB max config file


class WalletConfig(BaseModel):
    """Wallet configuration."""

    addresses: list[str] = Field(default=[], description="XRP wallet addresses (r-addresses)")

    @model_validator(mode="before")
    @classmethod
    def handle_legacy_address(cls, data):
        """Convert legacy 'address' field to 'addresses' list."""
        if isinstance(data, dict) and "address" in data and "addresses" not in data:
            data["addresses"] = [data.pop("address")]
        return data

    @field_validator("addresses", mode="before")
    @classmethod
    def convert_single_address(cls, v):
        """Convert single address string to list for backwards compatibility."""
        if isinstance(v, str):
            return [v]
        return v

    @field_validator("addresses")
    @classmethod
    def validate_xrp_addresses(cls, v: list[str]) -> list[str]:
        """Validate XRP address formats with strict pattern matching."""
        for addr in v:
            # Basic checks
            if not addr.startswith("r"):
                raise ValueError("XRP address must start with 'r'")
            if len(addr) < XRP_ADDRESS_MIN_LENGTH or len(addr) > XRP_ADDRESS_MAX_LENGTH:
                min_len, max_len = XRP_ADDRESS_MIN_LENGTH, XRP_ADDRESS_MAX_LENGTH
                raise ValueError(f"XRP address must be {min_len}-{max_len} characters")

            # Pattern validation (base58 characters only)
            if not XRP_ADDRESS_PATTERN.match(addr):
                raise ValueError("XRP address contains invalid characters")
        return v


class DisplayConfig(BaseModel):
    """Display configuration."""

    refresh_rate: float = Field(default=0.5, ge=0.1, le=5.0)
    sparkline_minutes: int = Field(default=60, ge=5, le=1440)
    theme: str = Field(default="cyberpunk")


# Trusted XRPL endpoints (security allowlist)
TRUSTED_XRPL_ENDPOINTS = frozenset({
    "wss://xrplcluster.com",
    "wss://s1.ripple.com",
    "wss://s2.ripple.com",
    "wss://xrpl.ws",
})


class ConnectionsConfig(BaseModel):
    """Connection endpoints configuration."""

    # XRPL endpoints (in priority order)
    xrpl_endpoints: list[str] = Field(
        default=[
            "wss://xrplcluster.com",
            "wss://s1.ripple.com",
            "wss://s2.ripple.com",
            "wss://xrpl.ws",
        ]
    )

    xrpl_poll_interval: int = Field(default=30, ge=10, le=300)

    # Timeout configuration
    request_timeout: float = Field(
        default=REQUEST_TIMEOUT_SECONDS,
        ge=5.0,
        le=60.0,
        description="HTTP/WebSocket request timeout in seconds"
    )
    connection_timeout: float = Field(
        default=10.0,
        ge=1.0,
        le=30.0,
        description="Connection establishment timeout in seconds"
    )

    # Retry configuration
    max_retries: int = Field(
        default=3,
        ge=0,
        le=10,
        description="Maximum retry attempts before failing"
    )
    retry_backoff_base: float = Field(
        default=1.0,
        ge=0.5,
        le=5.0,
        description="Base delay for exponential backoff"
    )
    retry_backoff_max: float = Field(
        default=60.0,
        ge=10.0,
        le=300.0,
        description="Maximum backoff delay in seconds"
    )

    @field_validator("xrpl_endpoints")
    @classmethod
    def validate_xrpl_endpoints(cls, v: list[str]) -> list[str]:
        """Validate XRPL endpoints for security."""
        if not v:
            raise ValueError("At least one XRPL endpoint is required")

        for endpoint in v:
            # Enforce secure WebSocket scheme
            if not endpoint.startswith("wss://"):
                raise ValueError(
                    f"Only secure WebSocket (wss://) endpoints are allowed: {endpoint}"
                )

            # Validate against trusted endpoint allowlist
            if endpoint not in TRUSTED_XRPL_ENDPOINTS:
                raise ValueError(
                    f"Endpoint not in trusted allowlist: {endpoint}. "
                    f"Allowed endpoints: {', '.join(sorted(TRUSTED_XRPL_ENDPOINTS))}"
                )

        return v


class AppConfig(BaseModel):
    """Main application configuration."""

    wallet: WalletConfig
    display: DisplayConfig = Field(default_factory=DisplayConfig)
    connections: ConnectionsConfig = Field(default_factory=ConnectionsConfig)


def find_config_file() -> Path | None:
    """
    Find the config file in standard locations.

    Search order:
    1. Current working directory (config.toml)
    2. User config directory (~/.config/xrp-ticker/config.toml)
    3. XDG_CONFIG_HOME/xrp-ticker/config.toml
    """
    search_paths = [
        Path.cwd() / "config.toml",
        Path.home() / ".config" / "xrp-ticker" / "config.toml",
    ]

    # Add XDG_CONFIG_HOME if set
    xdg_config = os.environ.get("XDG_CONFIG_HOME")
    if xdg_config:
        search_paths.insert(1, Path(xdg_config) / "xrp-ticker" / "config.toml")

    for path in search_paths:
        if path.exists():
            logger.info(f"Found config file: {path}")
            return path

    logger.warning("No config file found in standard locations")
    return None


def load_config(config_path: Path | None = None) -> AppConfig | None:
    """
    Load configuration from TOML file.

    Args:
        config_path: Optional explicit path to config file

    Returns:
        AppConfig if successful, None if config file not found
    """
    if config_path is None:
        config_path = find_config_file()

    if config_path is None:
        return None

    if not config_path.exists():
        return None

    try:
        # Security: Check file size before loading
        file_size = config_path.stat().st_size
        if file_size > MAX_CONFIG_FILE_SIZE:
            logger.error("Config file too large (max %d bytes)", MAX_CONFIG_FILE_SIZE)
            raise ValueError(f"Config file exceeds maximum size of {MAX_CONFIG_FILE_SIZE} bytes")

        with open(config_path, "rb") as f:
            data = tomllib.load(f)

        config = AppConfig(**data)
        logger.info(f"Configuration loaded successfully from {config_path}")
        return config

    except tomllib.TOMLDecodeError as e:
        logger.error(f"Invalid TOML in config file: {e}")
        raise
    except Exception as e:
        logger.error(f"Error loading config: {e}")
        raise


def create_default_config(wallet_address: str, output_path: Path | None = None) -> Path:
    """
    Create a default config file with the given wallet address.

    Args:
        wallet_address: XRP wallet address
        output_path: Where to save the config (defaults to cwd/config.toml)

    Returns:
        Path to created config file
    """
    if output_path is None:
        output_path = Path.cwd() / "config.toml"

    config_content = f'''# XRP Ticker Configuration

[wallet]
# Single address or multiple addresses supported
addresses = ["{wallet_address}"]

[display]
refresh_rate = 0.5
sparkline_minutes = 60
theme = "ripple"

[connections]
# Seconds between balance checks (lower = faster updates, higher = less API load)
xrpl_poll_interval = 30
'''

    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(config_content)
    logger.info(f"Created config file: {output_path}")

    return output_path


def setup_logging(debug: bool = False) -> None:
    """Configure logging for the application."""
    level = logging.DEBUG if debug else logging.INFO

    # Check for debug environment variable
    if os.environ.get("XRP_TICKER_DEBUG", "").lower() in ("1", "true", "yes"):
        level = logging.DEBUG

    logging.basicConfig(
        level=level,
        format="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
        datefmt="%H:%M:%S",
    )

    # Reduce noise from third-party libraries
    logging.getLogger("websockets").setLevel(logging.WARNING)
    logging.getLogger("httpx").setLevel(logging.WARNING)
