"""Shared utilities for service modules."""

import random
import ssl
from typing import Final

# Reconnection backoff settings
INITIAL_DELAY: Final[float] = 1.0
MAX_DELAY: Final[float] = 60.0
MULTIPLIER: Final[float] = 2.0
JITTER: Final[float] = 0.1


def mask_address(address: str) -> str:
    """Mask wallet address for safe logging. Shows first 4 and last 4 characters."""
    if len(address) > 8:
        return f"{address[:4]}...{address[-4:]}"
    return "***"


def create_ssl_context() -> ssl.SSLContext:
    """Create a secure SSL context for WebSocket connections."""
    ctx = ssl.create_default_context()
    ctx.check_hostname = True
    ctx.verify_mode = ssl.CERT_REQUIRED
    # Enforce TLS 1.2 minimum
    ctx.minimum_version = ssl.TLSVersion.TLSv1_2
    return ctx


class BackoffCalculator:
    """Exponential backoff with jitter for reconnection delays."""

    def __init__(
        self,
        initial_delay: float = INITIAL_DELAY,
        max_delay: float = MAX_DELAY,
        multiplier: float = MULTIPLIER,
        jitter: float = JITTER,
    ) -> None:
        self._initial_delay = initial_delay
        self._max_delay = max_delay
        self._multiplier = multiplier
        self._jitter = jitter
        self._current_delay = initial_delay

    def calculate(self) -> float:
        """Calculate next backoff delay with jitter."""
        jitter_range = self._current_delay * self._jitter
        jitter_value = random.uniform(-jitter_range, jitter_range)
        delay = min(self._current_delay + jitter_value, self._max_delay)
        self._current_delay = min(self._current_delay * self._multiplier, self._max_delay)
        return delay

    def reset(self) -> None:
        """Reset backoff delay to initial value."""
        self._current_delay = self._initial_delay
