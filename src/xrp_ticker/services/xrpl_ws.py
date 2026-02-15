"""XRPL WebSocket service for wallet balance data."""

import asyncio
import json
import logging
from collections.abc import Callable
from datetime import datetime
from typing import Final

from websockets.asyncio.client import connect
from websockets.exceptions import ConnectionClosed, InvalidHandshake, InvalidURI

from ..models import ConnectionState, ServiceStatus, WalletData
from ..security import (
    MAX_WEBSOCKET_MESSAGE_SIZE,
    generate_request_id,
    is_trusted_endpoint,
    sanitize_error_message,
)
from .utils import BackoffCalculator, create_ssl_context, mask_address

logger = logging.getLogger(__name__)

# WebSocket settings
WS_PING_INTERVAL: Final[float] = 30.0
WS_PING_TIMEOUT: Final[float] = 10.0
WS_CLOSE_TIMEOUT: Final[float] = 5.0

# Default XRPL endpoints in priority order
DEFAULT_ENDPOINTS: Final[list[str]] = [
    "wss://xrplcluster.com",
    "wss://s1.ripple.com",
    "wss://s2.ripple.com",
    "wss://xrpl.ws",
]


class XRPLWebSocketService:
    """WebSocket client for XRPL wallet balance with reconnection and endpoint failover."""

    def __init__(
        self,
        wallet_addresses: list[str],
        endpoints: list[str] | None = None,
        poll_interval: int = 30,
        on_balance_update: Callable[[WalletData], None] | None = None,
        on_status_change: Callable[[ServiceStatus], None] | None = None,
        request_timeout: float = 30.0,
    ):
        self.wallet_addresses = wallet_addresses
        self.endpoints = endpoints or DEFAULT_ENDPOINTS.copy()
        self.poll_interval = max(poll_interval, 10)  # Enforce minimum
        self.on_balance_update = on_balance_update
        self.on_status_change = on_status_change
        self.request_timeout = request_timeout

        self._status = ServiceStatus(name="XRPL", state=ConnectionState.DISCONNECTED)
        self._running = False
        self._task: asyncio.Task | None = None
        self._backoff = BackoffCalculator()
        self._current_endpoint_index = 0
        self._last_balance: WalletData | None = None
        self._consecutive_failures = 0
        self._max_consecutive_failures = 5

        # Validate endpoints on initialization
        self._validate_endpoints()

    def _validate_endpoints(self) -> None:
        """Validate that all endpoints are trusted."""
        for endpoint in self.endpoints:
            if not is_trusted_endpoint(endpoint):
                logger.warning("Endpoint %s not in trusted list", endpoint[:30])

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

    def _try_next_endpoint(self) -> bool:
        """Try the next endpoint in the list. Returns False if all endpoints exhausted."""
        next_index = self._current_endpoint_index + 1
        if next_index >= len(self.endpoints):
            # All endpoints exhausted in this cycle
            return False
        self._current_endpoint_index = next_index
        return True

    async def _fetch_single_balance(self, websocket, address: str) -> int:
        """Fetch balance for a single wallet. Returns drops or 0 on error."""
        request_id = generate_request_id()
        masked_addr = mask_address(address)

        request = {
            "id": request_id,
            "command": "account_info",
            "account": address,
            "ledger_index": "validated",
        }

        try:
            await websocket.send(json.dumps(request))

            # Wait for response with timeout
            response_str = await asyncio.wait_for(
                websocket.recv(), timeout=self.request_timeout
            )

            # Validate message size
            if len(response_str) > MAX_WEBSOCKET_MESSAGE_SIZE:
                logger.warning("Response too large (req_id=%s)", request_id)
                return 0

            response = json.loads(response_str)

            if "error" in response:
                error_code = response.get("error", "unknown")
                # Don't log full error message, just the code
                logger.warning(
                    "XRPL error %s for %s (req_id=%s)", error_code, masked_addr, request_id
                )

                # Account not found (unfunded wallet) - return 0
                if error_code == "actNotFound":
                    logger.info("Wallet %s not found (may be unfunded)", masked_addr)
                    return 0
                return 0

            # Extract account data
            result = response.get("result", {})
            account_data = result.get("account_data", {})

            if not account_data:
                logger.warning("No account_data for %s (req_id=%s)", masked_addr, request_id)
                return 0

            try:
                balance_drops = int(account_data.get("Balance", 0))
            except (ValueError, TypeError):
                logger.warning("Invalid balance format for %s (req_id=%s)", masked_addr, request_id)
                return 0

            # Validate balance is reasonable (max 100 billion XRP in existence)
            if balance_drops < 0 or balance_drops > 100_000_000_000_000_000:
                logger.warning("Balance out of range for %s (req_id=%s)", masked_addr, request_id)
                return 0

            logger.debug("Balance for %s: %.6f XRP", masked_addr, balance_drops / 1_000_000)
            return balance_drops

        except TimeoutError:
            logger.warning("Request timeout for %s (req_id=%s)", masked_addr, request_id)
            return 0
        except json.JSONDecodeError:
            logger.warning("Invalid JSON for %s (req_id=%s)", masked_addr, request_id)
            return 0
        except Exception as e:
            logger.error(
                "Fetch error for %s: %s (req_id=%s)",
                masked_addr, sanitize_error_message(e), request_id
            )
            return 0

    async def _fetch_all_balances(self, websocket) -> WalletData | None:
        """Fetch and aggregate balances for all wallets concurrently."""
        if not self.wallet_addresses:
            return WalletData.from_drops(
                address="No wallets", drops=0, source=self.current_endpoint
            )

        # Fetch all wallet balances concurrently
        results = await asyncio.gather(
            *(self._fetch_single_balance(websocket, addr) for addr in self.wallet_addresses)
        )
        total_drops = sum(results)

        # Create aggregated wallet data
        wallet_count = len(self.wallet_addresses)
        if wallet_count == 1:
            display_address = self.wallet_addresses[0]
        else:
            display_address = f"{wallet_count} wallets"

        wallet_data = WalletData.from_drops(
            address=display_address,
            drops=total_drops,
            source=self.current_endpoint,
        )

        logger.debug(f"Total balance ({wallet_count} wallets): {wallet_data.balance_xrp:.6f} XRP")
        return wallet_data

    async def _connect_and_poll(self) -> None:
        """Main connection loop with polling and automatic reconnection."""
        ssl_context = create_ssl_context()

        while self._running:
            endpoint = self.current_endpoint

            # Circuit breaker: if too many failures, back off
            if self._consecutive_failures >= self._max_consecutive_failures:
                backoff = min(60, self._consecutive_failures * 10)
                logger.warning(
                    "Circuit breaker: backing off %ds after %d failures",
                    backoff, self._consecutive_failures
                )
                await asyncio.sleep(backoff)
                self._consecutive_failures = 0

            try:
                logger.info("Connecting to XRPL endpoint")
                self._update_status(state=ConnectionState.RECONNECTING)

                async with connect(
                    endpoint,
                    ssl=ssl_context,
                    ping_interval=WS_PING_INTERVAL,
                    ping_timeout=WS_PING_TIMEOUT,
                    close_timeout=WS_CLOSE_TIMEOUT,
                    max_size=MAX_WEBSOCKET_MESSAGE_SIZE,
                ) as websocket:
                    logger.info("XRPL WebSocket connected")
                    self._update_status(state=ConnectionState.CONNECTED)
                    self._backoff.reset()
                    self._consecutive_failures = 0

                    # Poll loop
                    while self._running:
                        # Fetch balances for all wallets
                        wallet_data = await self._fetch_all_balances(websocket)

                        if wallet_data:
                            self._status.last_message = datetime.now()
                            self._last_balance = wallet_data

                            if self.on_balance_update:
                                self.on_balance_update(wallet_data)

                        # Wait for next poll
                        await asyncio.sleep(self.poll_interval)

            except ConnectionClosed as e:
                self._consecutive_failures += 1
                logger.warning("XRPL connection closed: code=%s", e.code)
                self._update_status(
                    state=ConnectionState.RECONNECTING,
                    error_message="Connection closed",
                    increment_reconnect=True,
                )

            except InvalidURI:
                self._consecutive_failures += 1
                logger.error("Invalid XRPL endpoint URI")
                # Try next endpoint
                if not self._try_next_endpoint():
                    self._update_status(
                        state=ConnectionState.FAILED,
                        error_message="All endpoints failed",
                    )
                    break
                # Brief delay before trying next endpoint
                await asyncio.sleep(1.0)
                continue

            except InvalidHandshake:
                self._consecutive_failures += 1
                logger.warning("XRPL WebSocket handshake failed")
                # Try next endpoint
                if not self._try_next_endpoint():
                    self._update_status(
                        state=ConnectionState.RECONNECTING,
                        error_message="Handshake failed",
                        increment_reconnect=True,
                    )
                else:
                    # Brief delay before trying next endpoint
                    await asyncio.sleep(1.0)
                    continue

            except OSError as e:
                self._consecutive_failures += 1
                logger.warning("Network connectivity error: %s", sanitize_error_message(e))
                self._update_status(
                    state=ConnectionState.RECONNECTING,
                    error_message="Network issue",
                    increment_reconnect=True,
                )

            except Exception as e:
                self._consecutive_failures += 1
                logger.error("Connection error: %s", sanitize_error_message(e))
                self._update_status(
                    state=ConnectionState.RECONNECTING,
                    error_message="Connection error",
                    increment_reconnect=True,
                )

            # Wait before reconnecting
            if self._running:
                delay = self._backoff.calculate()
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
        self._backoff.reset()
        self._current_endpoint_index = 0  # Reset to first endpoint
        await self.start()

    async def fetch_balance_once(self) -> WalletData | None:
        """Fetch balance once without starting the polling loop."""
        ssl_context = create_ssl_context()

        for endpoint in self.endpoints:
            try:
                async with connect(
                    endpoint,
                    ssl=ssl_context,
                    ping_interval=WS_PING_INTERVAL,
                    ping_timeout=WS_PING_TIMEOUT,
                    close_timeout=WS_CLOSE_TIMEOUT,
                    max_size=MAX_WEBSOCKET_MESSAGE_SIZE,
                ) as websocket:
                    wallet_data = await self._fetch_all_balances(websocket)
                    if wallet_data:
                        return wallet_data
            except Exception as e:
                logger.warning("Failed to fetch: %s", sanitize_error_message(e))
                continue

        return None
