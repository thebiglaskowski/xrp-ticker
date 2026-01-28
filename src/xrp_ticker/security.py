"""Security utilities and constants for XRP Ticker."""

import logging
import re
import secrets
from functools import lru_cache
from typing import Final

logger = logging.getLogger(__name__)

# Security constants
MAX_WEBSOCKET_MESSAGE_SIZE: Final[int] = 1024 * 1024  # 1MB max message size
MAX_HTTP_RESPONSE_SIZE: Final[int] = 10 * 1024 * 1024  # 10MB max response
REQUEST_TIMEOUT_SECONDS: Final[float] = 30.0
CONNECTION_TIMEOUT_SECONDS: Final[float] = 10.0

# Rate limiting constants
MIN_POLL_INTERVAL_SECONDS: Final[int] = 5
MAX_REQUESTS_PER_MINUTE: Final[int] = 30

# XRP address validation
XRP_ADDRESS_PATTERN: Final[re.Pattern] = re.compile(r"^r[1-9A-HJ-NP-Za-km-z]{24,34}$")
XRP_ADDRESS_MIN_LENGTH: Final[int] = 25
XRP_ADDRESS_MAX_LENGTH: Final[int] = 35

# Trusted domains for XRPL endpoints
TRUSTED_XRPL_DOMAINS: Final[frozenset] = frozenset({
    "xrplcluster.com",
    "s1.ripple.com",
    "s2.ripple.com",
    "xrpl.ws",
})

# Version info (for User-Agent, not exposed to users)
APP_VERSION: Final[str] = "1.0.0"
APP_NAME: Final[str] = "XRP-Ticker"


def generate_request_id() -> str:
    """Generate a unique request ID for tracing."""
    return secrets.token_hex(8)


def validate_xrp_address(address: str) -> bool:
    """
    Validate XRP address format.

    Args:
        address: XRP wallet address to validate

    Returns:
        True if valid, False otherwise
    """
    if not address:
        return False

    # Check length
    if not (XRP_ADDRESS_MIN_LENGTH <= len(address) <= XRP_ADDRESS_MAX_LENGTH):
        return False

    # Check pattern (starts with 'r', followed by base58 chars)
    if not XRP_ADDRESS_PATTERN.match(address):
        return False

    return True


def sanitize_error_message(error: Exception) -> str:
    """
    Sanitize error message to prevent information leakage.

    Args:
        error: Exception to sanitize

    Returns:
        Safe error message without sensitive details
    """
    # Map of error types to generic messages
    error_mappings = {
        "ConnectionRefusedError": "Connection refused",
        "TimeoutError": "Request timed out",
        "SSLError": "SSL/TLS error",
        "SSLCertVerificationError": "Certificate verification failed",
        "gaierror": "DNS resolution failed",
        "ConnectionResetError": "Connection reset",
        "BrokenPipeError": "Connection broken",
    }

    error_type = type(error).__name__

    # Return generic message if we have a mapping
    if error_type in error_mappings:
        return error_mappings[error_type]

    # For other errors, return generic message without details
    return "An error occurred"


def mask_sensitive_data(data: str, visible_chars: int = 4) -> str:
    """
    Mask sensitive data for safe logging.

    Args:
        data: Data to mask
        visible_chars: Number of characters to show at start and end

    Returns:
        Masked string
    """
    if not data:
        return "***"

    if len(data) <= visible_chars * 2:
        return "***"

    return f"{data[:visible_chars]}...{data[-visible_chars:]}"


def sanitize_display_text(text: str, max_length: int = 100) -> str:
    """
    Sanitize text for display to prevent injection.

    Args:
        text: Text to sanitize
        max_length: Maximum allowed length

    Returns:
        Sanitized text
    """
    if not text:
        return ""

    # Remove control characters except newline and tab
    sanitized = "".join(
        char for char in text
        if char.isprintable() or char in ("\n", "\t")
    )

    # Truncate if too long
    if len(sanitized) > max_length:
        sanitized = sanitized[:max_length - 3] + "..."

    return sanitized


@lru_cache(maxsize=128)
def is_trusted_endpoint(endpoint: str) -> bool:
    """
    Check if an endpoint is in the trusted allowlist.

    Args:
        endpoint: WebSocket endpoint URL

    Returns:
        True if trusted, False otherwise
    """
    if not endpoint:
        return False

    # Must be wss://
    if not endpoint.startswith("wss://"):
        return False

    # Extract domain
    try:
        # Remove wss:// prefix
        remainder = endpoint[6:]
        # Get domain (before first /)
        domain = remainder.split("/")[0]
        # Remove port if present
        domain = domain.split(":")[0]

        return domain in TRUSTED_XRPL_DOMAINS
    except (IndexError, ValueError):
        return False


def get_safe_user_agent() -> str:
    """Get a generic User-Agent string that doesn't expose system info."""
    return f"{APP_NAME}/{APP_VERSION}"


class RateLimiter:
    """Simple rate limiter for API requests."""

    def __init__(self, max_requests: int = MAX_REQUESTS_PER_MINUTE, window_seconds: int = 60):
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        self._requests: list[float] = []

    def can_make_request(self, current_time: float) -> bool:
        """
        Check if a request can be made within rate limits.

        Args:
            current_time: Current timestamp

        Returns:
            True if request is allowed, False otherwise
        """
        # Remove old requests outside window
        cutoff = current_time - self.window_seconds
        self._requests = [t for t in self._requests if t > cutoff]

        # Check if under limit
        return len(self._requests) < self.max_requests

    def record_request(self, current_time: float) -> None:
        """Record a request timestamp."""
        self._requests.append(current_time)

    def time_until_available(self, current_time: float) -> float:
        """
        Get seconds until next request is allowed.

        Args:
            current_time: Current timestamp

        Returns:
            Seconds to wait, 0 if request is allowed now
        """
        if self.can_make_request(current_time):
            return 0.0

        # Find oldest request in window
        cutoff = current_time - self.window_seconds
        requests_in_window = [t for t in self._requests if t > cutoff]

        # Safety check: if no requests in window, allow immediately
        if not requests_in_window:
            return 0.0

        oldest = min(requests_in_window)
        return oldest + self.window_seconds - current_time
