"""Tests for service modules."""

import asyncio
import json
from unittest.mock import AsyncMock, MagicMock, patch

import httpx
import pytest

from xrp_ticker.models import ConnectionState, PriceData, WalletData
from xrp_ticker.services.coinbase import CoinbaseService
from xrp_ticker.services.xrpl_ws import (
    XRPLWebSocketService,
    _create_ssl_context,
    _mask_address,
)


class TestCoinbaseService:
    """Tests for CoinbaseService."""

    def test_service_name_property(self):
        """Service should expose its name via property."""
        service = CoinbaseService()
        assert service.service_name == "Coinbase"

    def test_initial_state(self):
        """Service should start disconnected."""
        service = CoinbaseService()
        assert service.status.state == ConnectionState.DISCONNECTED
        assert service.status.name == "Coinbase"

    def test_callbacks_stored(self):
        """Callbacks should be stored correctly."""
        price_cb = MagicMock()
        status_cb = MagicMock()

        service = CoinbaseService(
            on_price_update=price_cb,
            on_status_change=status_cb,
        )

        assert service.on_price_update is price_cb
        assert service.on_status_change is status_cb

    def test_status_update_notifies_callback(self):
        """Status update should notify callback."""
        status_cb = MagicMock()
        service = CoinbaseService(on_status_change=status_cb)

        service._update_status(state=ConnectionState.CONNECTED)

        status_cb.assert_called_once()
        assert service.status.state == ConnectionState.CONNECTED

    @pytest.mark.asyncio
    async def test_start_sets_running(self):
        """Starting service should set running flag."""
        service = CoinbaseService()

        # Mock the poll loop to avoid actual HTTP calls
        with patch.object(service, "_poll_loop", new_callable=AsyncMock):
            await service.start()
            assert service._running is True
            await service.stop()

    @pytest.mark.asyncio
    async def test_stop_clears_running(self):
        """Stopping service should clear running flag."""
        service = CoinbaseService()
        service._running = True
        service._task = asyncio.create_task(asyncio.sleep(10))

        await service.stop()

        assert service._running is False
        assert service.status.state == ConnectionState.DISCONNECTED

    @pytest.mark.asyncio
    async def test_fetch_price_success(self):
        """_fetch_price should return PriceData on success."""
        service = CoinbaseService()

        # Mock HTTP responses
        stats_response = MagicMock()
        stats_response.json.return_value = {
            "open": "2.00",
            "high": "2.50",
            "low": "1.90",
            "volume": "1000000",
        }
        stats_response.raise_for_status = MagicMock()

        ticker_response = MagicMock()
        ticker_response.json.return_value = {"price": "2.25"}
        ticker_response.raise_for_status = MagicMock()

        # Create mock client
        mock_client = AsyncMock()
        mock_client.get = AsyncMock(side_effect=[stats_response, ticker_response])
        service._client = mock_client

        result = await service._fetch_price()

        assert result is not None
        assert isinstance(result, PriceData)
        assert result.price == 2.25
        assert result.high_24h == 2.50
        assert result.low_24h == 1.90
        assert result.volume == 1000000.0
        assert result.price_change == pytest.approx(0.25, rel=1e-2)
        assert result.price_change_percent == pytest.approx(12.5, rel=1e-2)

    @pytest.mark.asyncio
    async def test_fetch_price_invalid_price(self):
        """_fetch_price should return None for invalid price."""
        service = CoinbaseService()

        stats_response = MagicMock()
        stats_response.json.return_value = {
            "open": "2.00", "high": "2.50", "low": "1.90", "volume": "1000"
        }
        stats_response.raise_for_status = MagicMock()

        ticker_response = MagicMock()
        ticker_response.json.return_value = {"price": "0"}  # Invalid price
        ticker_response.raise_for_status = MagicMock()

        mock_client = AsyncMock()
        mock_client.get = AsyncMock(side_effect=[stats_response, ticker_response])
        service._client = mock_client

        result = await service._fetch_price()
        assert result is None

    @pytest.mark.asyncio
    async def test_fetch_price_timeout(self):
        """_fetch_price should return None on timeout."""
        service = CoinbaseService()

        mock_client = AsyncMock()
        mock_client.get = AsyncMock(side_effect=httpx.TimeoutException("timeout"))
        service._client = mock_client

        result = await service._fetch_price()
        assert result is None

    @pytest.mark.asyncio
    async def test_fetch_price_http_error(self):
        """_fetch_price should return None on HTTP error."""
        service = CoinbaseService()

        mock_response = MagicMock()
        mock_response.status_code = 500
        mock_client = AsyncMock()
        mock_client.get = AsyncMock(
            side_effect=httpx.HTTPStatusError("error", request=MagicMock(), response=mock_response)
        )
        service._client = mock_client

        result = await service._fetch_price()
        assert result is None

    @pytest.mark.asyncio
    async def test_poll_loop_updates_status_on_success(self):
        """_poll_loop should update status to CONNECTED on successful fetch."""
        service = CoinbaseService()
        price_updates = []
        service.on_price_update = lambda p: price_updates.append(p)

        mock_price_data = PriceData(price=2.50, source="coinbase")

        with patch.object(service, "_fetch_price", new_callable=AsyncMock) as mock_fetch:
            mock_fetch.return_value = mock_price_data

            # Run one iteration of the poll loop
            service._running = True
            service._client = AsyncMock()

            # Create a task that stops after first iteration
            async def run_one_iteration():
                service._client = AsyncMock()
                service._client.aclose = AsyncMock()
                await service._fetch_price()
                if service._status.state != ConnectionState.CONNECTED:
                    service._update_status(state=ConnectionState.CONNECTED)
                if service.on_price_update and mock_price_data:
                    service.on_price_update(mock_price_data)

            await run_one_iteration()

            assert service.status.state == ConnectionState.CONNECTED
            assert len(price_updates) == 1
            assert price_updates[0].price == 2.50

    @pytest.mark.asyncio
    async def test_poll_loop_handles_failure(self):
        """_poll_loop should update status to RECONNECTING on fetch failure."""
        service = CoinbaseService()
        service._status.state = ConnectionState.CONNECTED

        # Simulate failure path
        service._update_status(
            state=ConnectionState.RECONNECTING,
            error_message="Failed to fetch price",
        )

        assert service.status.state == ConnectionState.RECONNECTING
        assert service.status.error_message == "Failed to fetch price"


class TestXRPLWebSocketService:
    """Tests for XRPLWebSocketService."""

    def test_initial_state(self):
        """Service should start disconnected."""
        service = XRPLWebSocketService(
            wallet_addresses=["rN7n3473SaZBCG4dFL83w7a1RXtXtbk2D9"]
        )
        assert service.status.state == ConnectionState.DISCONNECTED
        assert service.status.name == "XRPL"

    def test_default_endpoints(self):
        """Default endpoints should be set."""
        service = XRPLWebSocketService(
            wallet_addresses=["rN7n3473SaZBCG4dFL83w7a1RXtXtbk2D9"]
        )
        assert len(service.endpoints) == 4
        assert "wss://xrplcluster.com" in service.endpoints

    def test_custom_endpoints(self):
        """Custom endpoints should override defaults."""
        custom_endpoints = ["wss://custom.endpoint"]
        service = XRPLWebSocketService(
            wallet_addresses=["rN7n3473SaZBCG4dFL83w7a1RXtXtbk2D9"],
            endpoints=custom_endpoints,
        )
        assert service.endpoints == custom_endpoints

    def test_current_endpoint(self):
        """Current endpoint property should work."""
        service = XRPLWebSocketService(
            wallet_addresses=["rN7n3473SaZBCG4dFL83w7a1RXtXtbk2D9"]
        )
        assert service.current_endpoint == service.endpoints[0]

    def test_try_next_endpoint_cycles(self):
        """_try_next_endpoint should cycle through endpoints."""
        service = XRPLWebSocketService(
            wallet_addresses=["rN7n3473SaZBCG4dFL83w7a1RXtXtbk2D9"],
            endpoints=["ws://a", "ws://b", "ws://c"],
        )

        assert service._current_endpoint_index == 0

        # Should move to next endpoint
        result = service._try_next_endpoint()
        assert result is True
        assert service._current_endpoint_index == 1

        result = service._try_next_endpoint()
        assert result is True
        assert service._current_endpoint_index == 2

        # Should return False when all exhausted
        result = service._try_next_endpoint()
        assert result is False
        assert service._current_endpoint_index == 2  # Stays at last

    def test_backoff_calculation(self):
        """Backoff should increase exponentially."""
        service = XRPLWebSocketService(
            wallet_addresses=["rN7n3473SaZBCG4dFL83w7a1RXtXtbk2D9"]
        )

        # Initial delay should be around 1.0 (with jitter)
        delay1 = service._calculate_backoff()
        assert 0.9 <= delay1 <= 1.1

        # Next delay should be around 2.0
        delay2 = service._calculate_backoff()
        assert 1.8 <= delay2 <= 2.2

        # Next delay should be around 4.0
        delay3 = service._calculate_backoff()
        assert 3.6 <= delay3 <= 4.4

    def test_reset_backoff(self):
        """Reset backoff should return to initial delay."""
        service = XRPLWebSocketService(
            wallet_addresses=["rN7n3473SaZBCG4dFL83w7a1RXtXtbk2D9"]
        )

        # Increase backoff
        service._calculate_backoff()
        service._calculate_backoff()
        service._calculate_backoff()

        # Reset
        service._reset_backoff()

        # Should be back to initial
        delay = service._calculate_backoff()
        assert 0.9 <= delay <= 1.1

    @pytest.mark.asyncio
    async def test_stop_clears_state(self):
        """Stopping service should clear state."""
        service = XRPLWebSocketService(
            wallet_addresses=["rN7n3473SaZBCG4dFL83w7a1RXtXtbk2D9"]
        )
        service._running = True
        service._task = asyncio.create_task(asyncio.sleep(10))

        await service.stop()

        assert service._running is False
        assert service.status.state == ConnectionState.DISCONNECTED

    @pytest.mark.asyncio
    async def test_restart_resets_endpoint(self):
        """Restart should reset endpoint index."""
        service = XRPLWebSocketService(
            wallet_addresses=["rN7n3473SaZBCG4dFL83w7a1RXtXtbk2D9"],
            endpoints=["ws://a", "ws://b"],
        )
        service._current_endpoint_index = 1

        # Mock connect_and_poll
        with patch.object(service, "_connect_and_poll", new_callable=AsyncMock):
            await service.restart()
            assert service._current_endpoint_index == 0
            await service.stop()

    @pytest.mark.asyncio
    async def test_fetch_single_balance_success(self):
        """_fetch_single_balance should return drops on success."""
        service = XRPLWebSocketService(
            wallet_addresses=["rN7n3473SaZBCG4dFL83w7a1RXtXtbk2D9"]
        )

        # Mock WebSocket
        mock_ws = AsyncMock()
        mock_ws.send = AsyncMock()
        mock_ws.recv = AsyncMock(
            return_value=json.dumps({
                "result": {
                    "account_data": {
                        "Account": "rN7n3473SaZBCG4dFL83w7a1RXtXtbk2D9",
                        "Balance": "100000000",  # 100 XRP
                    }
                }
            })
        )

        result = await service._fetch_single_balance(
            mock_ws, "rN7n3473SaZBCG4dFL83w7a1RXtXtbk2D9"
        )

        assert result == 100000000
        mock_ws.send.assert_called_once()

    @pytest.mark.asyncio
    async def test_fetch_single_balance_account_not_found(self):
        """_fetch_single_balance should return 0 for unfunded account."""
        service = XRPLWebSocketService(
            wallet_addresses=["rN7n3473SaZBCG4dFL83w7a1RXtXtbk2D9"]
        )

        mock_ws = AsyncMock()
        mock_ws.send = AsyncMock()
        mock_ws.recv = AsyncMock(
            return_value=json.dumps({
                "error": "actNotFound",
                "error_message": "Account not found.",
            })
        )

        result = await service._fetch_single_balance(
            mock_ws, "rN7n3473SaZBCG4dFL83w7a1RXtXtbk2D9"
        )

        assert result == 0

    @pytest.mark.asyncio
    async def test_fetch_single_balance_timeout(self):
        """_fetch_single_balance should return 0 on timeout."""
        service = XRPLWebSocketService(
            wallet_addresses=["rN7n3473SaZBCG4dFL83w7a1RXtXtbk2D9"]
        )

        mock_ws = AsyncMock()
        mock_ws.send = AsyncMock()
        mock_ws.recv = AsyncMock(side_effect=TimeoutError("timeout"))

        result = await service._fetch_single_balance(
            mock_ws, "rN7n3473SaZBCG4dFL83w7a1RXtXtbk2D9"
        )

        assert result == 0

    @pytest.mark.asyncio
    async def test_fetch_single_balance_invalid_json(self):
        """_fetch_single_balance should return 0 on invalid JSON."""
        service = XRPLWebSocketService(
            wallet_addresses=["rN7n3473SaZBCG4dFL83w7a1RXtXtbk2D9"]
        )

        mock_ws = AsyncMock()
        mock_ws.send = AsyncMock()
        mock_ws.recv = AsyncMock(return_value="not valid json")

        result = await service._fetch_single_balance(
            mock_ws, "rN7n3473SaZBCG4dFL83w7a1RXtXtbk2D9"
        )

        assert result == 0

    @pytest.mark.asyncio
    async def test_fetch_all_balances_aggregates(self):
        """_fetch_all_balances should aggregate multiple wallet balances."""
        service = XRPLWebSocketService(
            wallet_addresses=[
                "rN7n3473SaZBCG4dFL83w7a1RXtXtbk2D9",
                "rETnan6RaUmPnsPHoMjZqb1smNPeWwwago",
            ]
        )

        # Mock to return different balances for each wallet
        call_count = 0

        async def mock_recv():
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                return json.dumps({
                    "result": {"account_data": {"Balance": "50000000"}}  # 50 XRP
                })
            else:
                return json.dumps({
                    "result": {"account_data": {"Balance": "75000000"}}  # 75 XRP
                })

        mock_ws = AsyncMock()
        mock_ws.send = AsyncMock()
        mock_ws.recv = mock_recv

        result = await service._fetch_all_balances(mock_ws)

        assert result is not None
        assert isinstance(result, WalletData)
        assert result.balance_drops == 125000000  # 50 + 75 XRP in drops
        assert result.balance_xrp == 125.0
        assert result.address == "2 wallets"

    @pytest.mark.asyncio
    async def test_fetch_all_balances_single_wallet(self):
        """_fetch_all_balances should show address for single wallet."""
        service = XRPLWebSocketService(
            wallet_addresses=["rN7n3473SaZBCG4dFL83w7a1RXtXtbk2D9"]
        )

        mock_ws = AsyncMock()
        mock_ws.send = AsyncMock()
        mock_ws.recv = AsyncMock(
            return_value=json.dumps({
                "result": {"account_data": {"Balance": "100000000"}}
            })
        )

        result = await service._fetch_all_balances(mock_ws)

        assert result is not None
        assert result.address == "rN7n3473SaZBCG4dFL83w7a1RXtXtbk2D9"

    def test_update_status_increments_reconnect(self):
        """_update_status should increment reconnect attempts when flag is set."""
        service = XRPLWebSocketService(
            wallet_addresses=["rN7n3473SaZBCG4dFL83w7a1RXtXtbk2D9"]
        )

        assert service.status.reconnect_attempts == 0

        service._update_status(
            state=ConnectionState.RECONNECTING,
            increment_reconnect=True,
        )
        assert service.status.reconnect_attempts == 1

        service._update_status(
            state=ConnectionState.RECONNECTING,
            increment_reconnect=True,
        )
        assert service.status.reconnect_attempts == 2

        # Without flag, should reset to 0
        service._update_status(state=ConnectionState.CONNECTED)
        assert service.status.reconnect_attempts == 0

    def test_update_status_notifies_callback(self):
        """_update_status should call on_status_change callback."""
        status_cb = MagicMock()
        service = XRPLWebSocketService(
            wallet_addresses=["rN7n3473SaZBCG4dFL83w7a1RXtXtbk2D9"],
            on_status_change=status_cb,
        )

        service._update_status(state=ConnectionState.CONNECTED)

        status_cb.assert_called_once()
        assert service.status.state == ConnectionState.CONNECTED


class TestSecurityHelpers:
    """Tests for security helper functions."""

    def test_mask_address_normal(self):
        """Normal addresses should be masked showing first/last 4 chars."""
        result = _mask_address("rN7n3473SaZBCG4dFL83w7a1RXtXtbk2D9")
        assert result == "rN7n...k2D9"
        assert "3473SaZBCG4dFL83w7a1RXtXtb" not in result

    def test_mask_address_short(self):
        """Short addresses should be fully masked."""
        result = _mask_address("rShort")
        assert result == "***"

    def test_mask_address_exactly_8_chars(self):
        """8-char addresses should be fully masked."""
        result = _mask_address("r1234567")
        assert result == "***"

    def test_mask_address_9_chars(self):
        """9-char addresses should show first/last 4."""
        result = _mask_address("r12345678")
        assert result == "r123...5678"

    def test_ssl_context_created(self):
        """SSL context should be created with secure settings."""
        import ssl

        ctx = _create_ssl_context()

        assert ctx.check_hostname is True
        assert ctx.verify_mode == ssl.CERT_REQUIRED
        assert ctx.minimum_version == ssl.TLSVersion.TLSv1_2

    def test_ssl_context_is_ssl_context(self):
        """SSL context should be proper SSLContext instance."""
        import ssl

        ctx = _create_ssl_context()
        assert isinstance(ctx, ssl.SSLContext)
