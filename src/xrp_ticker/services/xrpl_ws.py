"""XRPL WebSocket service for wallet balance data."""

import asyncio
import json
import logging
import random
from collections.abc import Callable
from datetime import datetime

from websockets.asyncio.client import connect
from websockets.exceptions import ConnectionClosed, InvalidHandshake, InvalidURI

from ..models import ConnectionState, ServiceStatus, WalletData

logger = logging.getLogger(__name__)

# Reconnection backoff settings
INITIAL_DELAY = 1.0
MAX_DELAY = 60.0
MULTIPLIER = 2.0
JITTER = 0.1

# Default XRPL endpoints in priority order
DEFAULT_ENDPOINTS = [
    "wss://xrplcluster.com",
    "wss://s1.ripple.com",
    "wss://s2.ripple.com",
    "wss://xrpl.ws",
]


class XRPLWebSocketService:
    """WebSocket client for XRPL wallet balance with reconnection and endpoint failover."""

    def __init__(
        self,
        wallet_address: str,
        endpoints: list[str] | None = None,
        poll_interval: int = 30,
        on_balance_update: Callable[[WalletData], None] | None = None,
        on_status_change: Callable[[ServiceStatus], None] | None = None,
    ):
        self.wallet_address = wallet_address
        self.endpoints = endpoints or DEFAULT_ENDPOINTS.copy()
        self.poll_interval = poll_interval
        self.on_balance_update = on_balance_update
        self.on_status_change = on_status_change

        self._status = ServiceStatus(name="XRPL", state=ConnectionState.DISCONNECTED)
        self._running = False
        self._task: asyncio.Task | None = None
        self._current_delay = INITIAL_DELAY
        self._current_endpoint_index = 0
        self._last_balance: WalletData | None = None

    @property
    def status(self) -> ServiceStatus:
        """Get current service status."""
        return self._status

    @property
    def current_endpoint(self) -> str:
        """Get the current endpoint being used."""
        return self.endpoints[self._current_endpoint_index]

    def _update_status(
        self,
        state: ConnectionState | None = None,
        error_message: str | None = None,
        increment_reconnect: bool = False,
    ) -> None:
        """Update service status and notify callback."""
        if state is not None:
            self._status.state = state
        if error_message is not None:
            self._status.error_message = error_message
        if increment_reconnect:
            self._status.reconnect_attempts += 1
        else:
            self._status.reconnect_attempts = 0

        if self.on_status_change:
            self.on_status_change(self._status)

    def _calculate_backoff(self) -> float:
        """Calculate next backoff delay with jitter."""
        jitter_range = self._current_delay * JITTER
        jitter = random.uniform(-jitter_range, jitter_range)
        delay = min(self._current_delay + jitter, MAX_DELAY)
        self._current_delay = min(self._current_delay * MULTIPLIER, MAX_DELAY)
        return delay

    def _reset_backoff(self) -> None:
        """Reset backoff delay after successful connection."""
        self._current_delay = INITIAL_DELAY

    def _try_next_endpoint(self) -> bool:
        """Try the next endpoint in the list. Returns False if all endpoints exhausted."""
        self._current_endpoint_index = (self._current_endpoint_index + 1) % len(self.endpoints)
        # If we've cycled back to 0, we've tried all endpoints
        return self._current_endpoint_index != 0

    async def _fetch_balance(self, websocket) -> WalletData | None:
        """Fetch wallet balance via account_info request."""
        request = {
            "command": "account_info",
            "account": self.wallet_address,
            "ledger_index": "validated",
        }

        try:
            await websocket.send(json.dumps(request))

            # Wait for response with timeout
            response_str = await asyncio.wait_for(websocket.recv(), timeout=10.0)
            response = json.loads(response_str)

            if "error" in response:
                error_msg = response.get("error_message", response.get("error", "Unknown error"))
                logger.warning(f"XRPL error: {error_msg}")

                # Check for account not found (unfunded wallet)
                if response.get("error") == "actNotFound":
                    logger.info(f"Wallet {self.wallet_address} not found (may be unfunded)")
                    return WalletData.from_drops(
                        address=self.wallet_address,
                        drops=0,
                        source=self.current_endpoint,
                    )
                return None

            # Extract account data
            result = response.get("result", {})
            account_data = result.get("account_data", {})

            if not account_data:
                logger.warning("No account_data in response")
                return None

            balance_drops = int(account_data.get("Balance", 0))
            wallet_data = WalletData.from_drops(
                address=account_data.get("Account", self.wallet_address),
                drops=balance_drops,
                source=self.current_endpoint,
            )

            logger.debug(f"Balance: {wallet_data.balance_xrp:.6f} XRP")
            return wallet_data

        except TimeoutError:
            logger.warning("XRPL request timeout")
            return None
        except json.JSONDecodeError as e:
            logger.warning(f"Invalid JSON response: {e}")
            return None
        except Exception as e:
            logger.error(f"Error fetching balance: {e}")
            return None

    async def _connect_and_poll(self) -> None:
        """Main connection loop with polling and automatic reconnection."""
        while self._running:
            endpoint = self.current_endpoint

            try:
                logger.info(f"Connecting to XRPL: {endpoint}")
                self._update_status(state=ConnectionState.RECONNECTING)

                async with connect(endpoint) as websocket:
                    logger.info(f"XRPL WebSocket connected to {endpoint}")
                    self._update_status(state=ConnectionState.CONNECTED)
                    self._reset_backoff()

                    # Poll loop
                    while self._running:
                        # Fetch balance
                        wallet_data = await self._fetch_balance(websocket)

                        if wallet_data:
                            self._status.last_message = datetime.now()
                            self._last_balance = wallet_data

                            if self.on_balance_update:
                                self.on_balance_update(wallet_data)

                        # Wait for next poll
                        await asyncio.sleep(self.poll_interval)

            except ConnectionClosed as e:
                logger.warning(f"XRPL connection closed: {e.code} - {e.reason}")
                self._update_status(
                    state=ConnectionState.RECONNECTING,
                    error_message=f"Connection closed: {e.reason}",
                    increment_reconnect=True,
                )

            except InvalidURI as e:
                logger.error(f"Invalid XRPL URI: {e}")
                # Try next endpoint
                if not self._try_next_endpoint():
                    self._update_status(
                        state=ConnectionState.FAILED,
                        error_message="All endpoints failed",
                    )
                    break
                continue

            except InvalidHandshake as e:
                logger.warning(f"XRPL handshake failed: {e}")
                # Try next endpoint
                if not self._try_next_endpoint():
                    self._update_status(
                        state=ConnectionState.RECONNECTING,
                        error_message=f"Handshake failed: {e}",
                        increment_reconnect=True,
                    )
                else:
                    continue

            except OSError as e:
                logger.warning(f"Network error: {e}")
                self._update_status(
                    state=ConnectionState.RECONNECTING,
                    error_message=f"Network error: {e}",
                    increment_reconnect=True,
                )

            except Exception as e:
                logger.error(f"Unexpected error: {e}")
                self._update_status(
                    state=ConnectionState.RECONNECTING,
                    error_message=str(e),
                    increment_reconnect=True,
                )

            # Wait before reconnecting
            if self._running:
                delay = self._calculate_backoff()
                logger.info(
                    f"Reconnecting in {delay:.1f}s (attempt {self._status.reconnect_attempts})"
                )
                await asyncio.sleep(delay)

    async def start(self) -> None:
        """Start the WebSocket service."""
        if self._running:
            logger.warning("XRPL service already running")
            return

        self._running = True
        self._task = asyncio.create_task(self._connect_and_poll())
        logger.info("XRPL WebSocket service started")

    async def stop(self) -> None:
        """Stop the WebSocket service."""
        self._running = False

        if self._task:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
            self._task = None

        self._update_status(state=ConnectionState.DISCONNECTED)
        logger.info("XRPL WebSocket service stopped")

    async def restart(self) -> None:
        """Restart the WebSocket connection."""
        await self.stop()
        self._reset_backoff()
        self._current_endpoint_index = 0  # Reset to first endpoint
        await self.start()

    async def fetch_balance_once(self) -> WalletData | None:
        """Fetch balance once without starting the polling loop."""
        for i, endpoint in enumerate(self.endpoints):
            try:
                async with connect(endpoint) as websocket:
                    wallet_data = await self._fetch_balance(websocket)
                    if wallet_data:
                        return wallet_data
            except Exception as e:
                logger.warning(f"Failed to fetch from {endpoint}: {e}")
                continue

        return None
