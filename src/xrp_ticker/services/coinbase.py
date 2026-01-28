"""Coinbase Exchange API service for XRP price data with 24h stats."""

import asyncio
import logging
import time
from collections.abc import Callable
from datetime import datetime
from typing import Final

import httpx

from ..models import ConnectionState, PriceData, ServiceStatus
from ..security import (
    MAX_HTTP_RESPONSE_SIZE,
    REQUEST_TIMEOUT_SECONDS,
    RateLimiter,
    generate_request_id,
    get_safe_user_agent,
    sanitize_error_message,
)

logger = logging.getLogger(__name__)

# Service constants
SERVICE_NAME: Final[str] = "Coinbase"

# Coinbase Exchange API - free, public, no auth required
COINBASE_STATS_URL: Final[str] = "https://api.exchange.coinbase.com/products/XRP-USD/stats"
COINBASE_TICKER_URL: Final[str] = "https://api.exchange.coinbase.com/products/XRP-USD/ticker"
POLL_INTERVAL: Final[int] = 5

# HTTP client configuration
DEFAULT_HEADERS: Final[dict] = {
    "User-Agent": get_safe_user_agent(),
    "Accept": "application/json",
}


class CoinbaseService:
    """REST API client for Coinbase Exchange price data with polling."""

    def __init__(
        self,
        on_price_update: Callable[[PriceData], None] | None = None,
        on_status_change: Callable[[ServiceStatus], None] | None = None,
        poll_interval: int = POLL_INTERVAL,
        request_timeout: float = REQUEST_TIMEOUT_SECONDS,
    ):
        self.on_price_update = on_price_update
        self.on_status_change = on_status_change
        self.poll_interval = max(poll_interval, 5)  # Enforce minimum
        self.request_timeout = request_timeout

        self._status = ServiceStatus(name=SERVICE_NAME, state=ConnectionState.DISCONNECTED)
        self._running = False
        self._task: asyncio.Task | None = None
        self._client: httpx.AsyncClient | None = None
        self._rate_limiter = RateLimiter(max_requests=30, window_seconds=60)
        self._consecutive_failures = 0
        self._max_consecutive_failures = 5

    @property
    def status(self) -> ServiceStatus:
        """Get current service status."""
        return self._status

    def _update_status(
        self,
        state: ConnectionState | None = None,
        error_message: str | None = None,
    ) -> None:
        """Update service status and notify callback."""
        if state is not None:
            self._status.state = state
        if error_message is not None:
            self._status.error_message = error_message

        if self.on_status_change:
            self.on_status_change(self._status)

    async def _fetch_price(self) -> PriceData | None:
        """Fetch current XRP price and 24h stats from Coinbase Exchange API."""
        request_id = generate_request_id()

        # Check rate limiting
        current_time = time.time()
        if not self._rate_limiter.can_make_request(current_time):
            wait_time = self._rate_limiter.time_until_available(current_time)
            logger.debug("Rate limited, waiting %.1fs (req_id=%s)", wait_time, request_id)
            return None

        try:
            # Record this request
            self._rate_limiter.record_request(current_time)

            # Fetch stats and ticker concurrently
            stats_response, ticker_response = await asyncio.gather(
                self._client.get(COINBASE_STATS_URL, timeout=self.request_timeout),
                self._client.get(COINBASE_TICKER_URL, timeout=self.request_timeout),
            )

            # Validate response sizes
            for resp in (stats_response, ticker_response):
                content_length = resp.headers.get("content-length")
                if content_length:
                    try:
                        if int(content_length) > MAX_HTTP_RESPONSE_SIZE:
                            logger.warning("Response too large (req_id=%s)", request_id)
                            return None
                    except ValueError:
                        # Invalid content-length header, skip size check
                        pass

            stats_response.raise_for_status()
            ticker_response.raise_for_status()

            stats = stats_response.json()
            ticker = ticker_response.json()

            # Extract and validate values
            try:
                price = float(ticker.get("price", 0))
                open_24h = float(stats.get("open", price))
                high_24h = float(stats.get("high", 0))
                low_24h = float(stats.get("low", 0))
                volume_24h = float(stats.get("volume", 0))
            except (ValueError, TypeError):
                logger.warning("Invalid numeric data in response (req_id=%s)", request_id)
                return None

            # Validate price data
            if price <= 0:
                logger.warning("Invalid price received (req_id=%s)", request_id)
                return None

            # Validate price is within reasonable bounds (sanity check)
            if price > 10000:  # XRP unlikely to exceed $10,000
                logger.warning("Price out of expected range (req_id=%s)", request_id)
                return None

            # Calculate 24h change
            price_change = price - open_24h
            price_change_percent = ((price - open_24h) / open_24h * 100) if open_24h > 0 else 0

            # Reset failure counter on success
            self._consecutive_failures = 0

            return PriceData(
                symbol="XRPUSD",
                price=price,
                price_change=price_change,
                price_change_percent=price_change_percent,
                high_24h=high_24h,
                low_24h=low_24h,
                volume=volume_24h,
                timestamp=datetime.now(),
                source="coinbase",
            )

        except httpx.TimeoutException:
            self._consecutive_failures += 1
            logger.warning("Request timeout (req_id=%s)", request_id)
            return None
        except httpx.HTTPStatusError as e:
            self._consecutive_failures += 1
            logger.warning("HTTP error %d (req_id=%s)", e.response.status_code, request_id)
            return None
        except Exception as e:
            self._consecutive_failures += 1
            logger.error("Fetch error: %s (req_id=%s)", sanitize_error_message(e), request_id)
            return None

    async def _poll_loop(self) -> None:
        """Main polling loop with circuit breaker pattern."""
        self._client = httpx.AsyncClient(
            headers=DEFAULT_HEADERS,
            timeout=httpx.Timeout(self.request_timeout, connect=10.0),
            limits=httpx.Limits(max_connections=10, max_keepalive_connections=5),
        )

        try:
            while self._running:
                # Circuit breaker: if too many failures, back off
                if self._consecutive_failures >= self._max_consecutive_failures:
                    backoff = min(30, self._consecutive_failures * 5)
                    logger.warning(
                        "Circuit breaker: backing off %ds after %d failures",
                        backoff, self._consecutive_failures
                    )
                    self._update_status(
                        state=ConnectionState.RECONNECTING,
                        error_message="Too many failures, backing off",
                    )
                    await asyncio.sleep(backoff)
                    self._consecutive_failures = 0  # Reset after backoff

                price_data = await self._fetch_price()

                if price_data:
                    self._status.last_message = datetime.now()

                    if self._status.state != ConnectionState.CONNECTED:
                        self._update_status(state=ConnectionState.CONNECTED)
                        logger.info("%s connected", SERVICE_NAME)

                    if self.on_price_update:
                        self.on_price_update(price_data)

                    logger.debug(
                        "Price: $%.4f | 24h: $%.4f-$%.4f | Change: %+.2f%%",
                        price_data.price,
                        price_data.low_24h or 0,
                        price_data.high_24h or 0,
                        price_data.price_change_percent,
                    )
                else:
                    if self._status.state == ConnectionState.CONNECTED:
                        self._update_status(
                            state=ConnectionState.RECONNECTING,
                            error_message="Failed to fetch price",
                        )

                await asyncio.sleep(self.poll_interval)

        finally:
            if self._client:
                await self._client.aclose()
                self._client = None

    async def start(self) -> None:
        """Start the polling service."""
        if self._running:
            logger.warning("%s service already running", SERVICE_NAME)
            return

        self._running = True
        self._update_status(state=ConnectionState.RECONNECTING)
        self._task = asyncio.create_task(self._poll_loop())
        logger.info("%s service started", SERVICE_NAME)

    async def stop(self) -> None:
        """Stop the polling service."""
        self._running = False

        if self._task:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
            self._task = None

        self._update_status(state=ConnectionState.DISCONNECTED)
        logger.info("%s service stopped", SERVICE_NAME)

    @property
    def service_name(self) -> str:
        """Get the service name."""
        return SERVICE_NAME

    async def restart(self) -> None:
        """Restart the service."""
        await self.stop()
        await self.start()
