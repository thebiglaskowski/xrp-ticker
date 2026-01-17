"""Configuration loading and validation for XRP Ticker."""

import logging
import os
import tomllib
from pathlib import Path

from pydantic import BaseModel, Field, field_validator

logger = logging.getLogger(__name__)


class WalletConfig(BaseModel):
    """Wallet configuration."""

    address: str = Field(description="XRP wallet address (r-address)")

    @field_validator("address")
    @classmethod
    def validate_xrp_address(cls, v: str) -> str:
        """Validate XRP address format."""
        if not v.startswith("r"):
            raise ValueError("XRP address must start with 'r'")
        if len(v) < 25 or len(v) > 35:
            raise ValueError("XRP address must be 25-35 characters")
        return v


class DisplayConfig(BaseModel):
    """Display configuration."""

    refresh_rate: float = Field(default=0.5, ge=0.1, le=5.0)
    sparkline_minutes: int = Field(default=60, ge=5, le=1440)
    theme: str = Field(default="cyberpunk")


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

    try:
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
address = "{wallet_address}"

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
