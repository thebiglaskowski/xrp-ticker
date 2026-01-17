"""Coinbase Exchange API service for XRP price data with 24h stats."""

import asyncio
import logging
from collections.abc import Callable
from datetime import datetime

import httpx

from ..models import ConnectionState, PriceData, ServiceStatus

logger = logging.getLogger(__name__)

# Coinbase Exchange API - free, public, no auth required
COINBASE_STATS_URL = "https://api.exchange.coinbase.com/products/XRP-USD/stats"
COINBASE_TICKER_URL = "https://api.exchange.coinbase.com/products/XRP-USD/ticker"
POLL_INTERVAL = 5


class CoinbaseService:
    """REST API client for Coinbase Exchange price data with polling."""

    def __init__(
        self,
        on_price_update: Callable[[PriceData], None] | None = None,
        on_status_change: Callable[[ServiceStatus], None] | None = None,
        poll_interval: int = POLL_INTERVAL,
    ):
        self.on_price_update = on_price_update
        self.on_status_change = on_status_change
        self.poll_interval = poll_interval

        self._status = ServiceStatus(name="Coinbase", state=ConnectionState.DISCONNECTED)
        self._running = False
        self._task: asyncio.Task | None = None
        self._client: httpx.AsyncClient | None = None
        self._last_price: float | None = None

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
        try:
            # Fetch 24h stats (high, low, open, volume)
            stats_response = await self._client.get(COINBASE_STATS_URL, timeout=10.0)
            stats_response.raise_for_status()
            stats = stats_response.json()

            # Fetch current ticker (price, bid, ask)
            ticker_response = await self._client.get(COINBASE_TICKER_URL, timeout=10.0)
            ticker_response.raise_for_status()
            ticker = ticker_response.json()

            # Extract values
            price = float(ticker.get("price", 0))
            open_24h = float(stats.get("open", price))
            high_24h = float(stats.get("high", 0))
            low_24h = float(stats.get("low", 0))
            volume_24h = float(stats.get("volume", 0))

            # Calculate 24h change
            price_change = price - open_24h
            price_change_percent = ((price - open_24h) / open_24h * 100) if open_24h > 0 else 0

            self._last_price = price

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
            logger.warning("Coinbase request timeout")
            return None
        except httpx.HTTPStatusError as e:
            logger.warning(f"Coinbase HTTP error: {e.response.status_code}")
            return None
        except Exception as e:
            logger.error(f"Coinbase error: {e}")
            return None

    async def _poll_loop(self) -> None:
        """Main polling loop."""
        self._client = httpx.AsyncClient(
            headers={"User-Agent": "XRP-Ticker/1.0"}
        )

        try:
            while self._running:
                price_data = await self._fetch_price()

                if price_data:
                    self._status.last_message = datetime.now()

                    if self._status.state != ConnectionState.CONNECTED:
                        self._update_status(state=ConnectionState.CONNECTED)
                        logger.info("Coinbase connected")

                    if self.on_price_update:
                        self.on_price_update(price_data)

                    logger.debug(
                        f"Price: ${price_data.price:.4f} | "
                        f"24h: ${price_data.low_24h:.4f}-${price_data.high_24h:.4f} | "
                        f"Change: {price_data.price_change_percent:+.2f}%"
                    )
                else:
                    if self._status.state == ConnectionState.CONNECTED:
                        self._update_status(
                            state=ConnectionState.RECONNECTING,
                            error_message="Failed to fetch price",
                        )

                await asyncio.sleep(self.poll_interval)

        finally:
            await self._client.aclose()
            self._client = None

    async def start(self) -> None:
        """Start the polling service."""
        if self._running:
            logger.warning("Coinbase service already running")
            return

        self._running = True
        self._update_status(state=ConnectionState.RECONNECTING)
        self._task = asyncio.create_task(self._poll_loop())
        logger.info("Coinbase service started")

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
        logger.info("Coinbase service stopped")

    async def restart(self) -> None:
        """Restart the service."""
        await self.stop()
        await self.start()
