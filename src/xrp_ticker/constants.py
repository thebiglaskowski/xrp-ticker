"""Centralized constants for XRP Ticker application."""

from typing import Final

# Application metadata
APP_NAME: Final[str] = "XRP Ticker"
APP_VERSION: Final[str] = "0.1.0"
APP_DESCRIPTION: Final[str] = "A modern terminal-based XRP portfolio tracker"

# XRP Ledger constants
XRP_DROPS_PER_UNIT: Final[int] = 1_000_000
XRP_MAX_SUPPLY_DROPS: Final[int] = 100_000_000_000_000_000  # 100 billion XRP

# Price display constants
PRICE_DECIMAL_PLACES: Final[int] = 4
CHANGE_DECIMAL_PLACES: Final[int] = 2
BALANCE_DECIMAL_PLACES: Final[int] = 2
VALUE_DECIMAL_PLACES: Final[int] = 2

# Price validation
MAX_REASONABLE_XRP_PRICE: Final[float] = 10000.0  # Sanity check upper bound

# Volume formatting thresholds
VOLUME_MILLIONS_THRESHOLD: Final[int] = 1_000_000
VOLUME_THOUSANDS_THRESHOLD: Final[int] = 1_000

# Connection state messages
CONNECTION_MESSAGES: Final[dict[str, str]] = {
    "connected": "Connected",
    "disconnected": "Disconnected",
    "reconnecting": "Reconnecting",
    "failed": "Failed",
}

# Status icons (Nerd Font icons)
ICONS: Final[dict[str, str]] = {
    "connected": "󰄬",
    "disconnected": "󰅖",
    "reconnecting": "󰑓",
    "failed": "󰅜",
    "price_up": "",
    "price_down": "",
    "high": "󰁝",
    "low": "󰁅",
    "change": "󰘦",
    "volume": "󰁨",
    "wallet": "\uef8d",
    "xrp": "\uede8",
    "exchange": "\uf0ec",
    "dollar": "\uf155",
}

# Keyboard shortcuts
SHORTCUTS: Final[dict[str, str]] = {
    "quit": "q",
    "refresh": "r",
    "theme": "t",
    "chart_style": "s",
    "debug": "d",
    "help": "?",
}

# Default polling intervals (seconds)
DEFAULT_PRICE_POLL_INTERVAL: Final[int] = 5
DEFAULT_BALANCE_POLL_INTERVAL: Final[int] = 30

# Minimum polling intervals (seconds)
MIN_PRICE_POLL_INTERVAL: Final[int] = 5
MIN_BALANCE_POLL_INTERVAL: Final[int] = 10

# Data source names
PRICE_SOURCE_COINBASE: Final[str] = "Coinbase"
BALANCE_SOURCE_XRPL: Final[str] = "XRPL"

# Error messages (user-facing)
ERROR_MESSAGES: Final[dict[str, str]] = {
    "no_config": "No configuration file found",
    "invalid_config": "Invalid configuration file",
    "no_wallet": "No wallet addresses configured",
    "connection_failed": "Connection failed",
    "fetch_failed": "Failed to fetch data",
    "invalid_address": "Invalid XRP address format",
}

# Log messages (internal)
LOG_MESSAGES: Final[dict[str, str]] = {
    "service_started": "%s service started",
    "service_stopped": "%s service stopped",
    "service_connected": "%s connected",
    "connection_error": "Connection error",
    "fetch_error": "Fetch error",
    "rate_limited": "Rate limited",
}


def format_xrp_balance(drops: int) -> float:
    """Convert drops to XRP."""
    return drops / XRP_DROPS_PER_UNIT


def format_price(price: float) -> str:
    """Format price for display."""
    return f"$ {price:,.{PRICE_DECIMAL_PLACES}f}"


def format_change(change: float, percent: float) -> str:
    """Format price change for display."""
    if change > 0:
        arrow = ICONS["price_up"]
    elif change < 0:
        arrow = ICONS["price_down"]
    else:
        arrow = ""
    return f"{arrow} {change:+.{PRICE_DECIMAL_PLACES}f} ({percent:+.{CHANGE_DECIMAL_PLACES}f}%)"


def format_volume(volume: float) -> str:
    """Format volume for display with K/M suffix."""
    if volume >= VOLUME_MILLIONS_THRESHOLD:
        return f"{volume / VOLUME_MILLIONS_THRESHOLD:.2f}M XRP"
    elif volume >= VOLUME_THOUSANDS_THRESHOLD:
        return f"{volume / VOLUME_THOUSANDS_THRESHOLD:.1f}K XRP"
    else:
        return f"{volume:.0f} XRP"


def format_balance(balance_xrp: float) -> str:
    """Format XRP balance for display."""
    return f"{balance_xrp:,.{BALANCE_DECIMAL_PLACES}f} XRP"


def format_portfolio_value(value_usd: float) -> str:
    """Format portfolio USD value for display."""
    return f"${value_usd:,.{VALUE_DECIMAL_PLACES}f} USD"
