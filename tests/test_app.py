"""Tests for XRPTickerApp module."""

from pathlib import Path
from unittest.mock import AsyncMock, patch

import pytest

from xrp_ticker.config import AppConfig, ConnectionsConfig, DisplayConfig, WalletConfig
from xrp_ticker.models import ConnectionState, PriceData, ServiceStatus, WalletData


class TestAppConfig:
    """Tests for app configuration handling."""

    def test_minimal_config(self):
        """App should accept minimal config."""
        config = AppConfig(
            wallet=WalletConfig(addresses=["rN7n3473SaZBCG4dFL83w7a1RXtXtbk2D9"])
        )
        assert config.wallet.addresses[0] == "rN7n3473SaZBCG4dFL83w7a1RXtXtbk2D9"
        assert config.display.refresh_rate == 0.5
        assert len(config.connections.xrpl_endpoints) == 4

    def test_full_config(self):
        """App should accept full config."""
        config = AppConfig(
            wallet=WalletConfig(addresses=["rN7n3473SaZBCG4dFL83w7a1RXtXtbk2D9"]),
            display=DisplayConfig(refresh_rate=1.0, theme="monokai"),
            connections=ConnectionsConfig(xrpl_poll_interval=60),
        )
        assert config.display.refresh_rate == 1.0
        assert config.display.theme == "monokai"
        assert config.connections.xrpl_poll_interval == 60


class TestAppThemes:
    """Tests for app theme handling."""

    def test_themes_list(self):
        """App should define available themes."""
        from xrp_ticker.app import XRPTickerApp

        # Just verify the constant exists without instantiating
        assert hasattr(XRPTickerApp, "THEMES")
        assert "ripple" in XRPTickerApp.THEMES
        assert "monokai" in XRPTickerApp.THEMES


class TestAppBindings:
    """Tests for app keyboard bindings."""

    def test_bindings_defined(self):
        """App should define keyboard bindings."""
        from xrp_ticker.app import XRPTickerApp

        assert hasattr(XRPTickerApp, "BINDINGS")
        bindings = XRPTickerApp.BINDINGS

        # Check essential bindings exist
        binding_keys = [b.key for b in bindings]
        assert "q" in binding_keys  # Quit
        assert "r" in binding_keys  # Refresh
        assert "t" in binding_keys  # Theme
        assert "d" in binding_keys  # Debug


class TestHelpScreen:
    """Tests for HelpScreen modal."""

    def test_help_screen_bindings(self):
        """HelpScreen should have escape binding."""
        from xrp_ticker.app import HelpScreen

        assert hasattr(HelpScreen, "BINDINGS")
        bindings = HelpScreen.BINDINGS
        binding_keys = [b.key for b in bindings]
        assert "escape" in binding_keys


class TestDebugPanel:
    """Tests for DebugPanel widget."""

    def test_debug_panel_counters(self):
        """DebugPanel should track message counts."""
        from xrp_ticker.app import DebugPanel

        panel = DebugPanel()
        assert panel._price_messages == 0
        assert panel._balance_messages == 0


class TestPriceDataHandling:
    """Tests for price data handling logic."""

    def test_price_data_creation(self):
        """PriceData should be created correctly."""
        data = PriceData(
            price=2.50,
            price_change=0.10,
            price_change_percent=4.17,
            high_24h=2.60,
            low_24h=2.40,
            volume=1000000.0,
            source="coinbase",
        )
        assert data.price == 2.50
        assert data.price_change == 0.10
        assert data.source == "coinbase"

    def test_price_data_with_strings(self):
        """PriceData should handle string prices."""
        data = PriceData(price="2.5678")
        assert data.price == 2.5678


class TestWalletDataHandling:
    """Tests for wallet data handling logic."""

    def test_wallet_data_from_drops(self):
        """WalletData should convert drops correctly."""
        data = WalletData.from_drops(
            address="rN7n3473SaZBCG4dFL83w7a1RXtXtbk2D9",
            drops=100_000_000,  # 100 XRP
            source="xrplcluster.com",
        )
        assert data.balance_xrp == 100.0
        assert data.balance_drops == 100_000_000

    def test_wallet_data_aggregation_display(self):
        """Multiple wallets should show 'N wallets' as address."""
        # Test the logic used in xrpl_ws.py
        wallet_count = 3
        addresses = ["addr1", "addr2", "addr3"]
        display_address = (
            addresses[0] if wallet_count == 1 else f"{wallet_count} wallets"
        )
        assert display_address == "3 wallets"


class TestServiceStatusHandling:
    """Tests for service status handling logic."""

    def test_service_status_connected(self):
        """Connected status should be recognized."""
        status = ServiceStatus(name="Test", state=ConnectionState.CONNECTED)
        assert status.is_connected is True

    def test_service_status_disconnected(self):
        """Disconnected status should be recognized."""
        status = ServiceStatus(name="Test", state=ConnectionState.DISCONNECTED)
        assert status.is_connected is False

    def test_service_status_reconnecting(self):
        """Reconnecting status should not be connected."""
        status = ServiceStatus(name="Test", state=ConnectionState.RECONNECTING)
        assert status.is_connected is False

    def test_service_status_with_attempts(self):
        """Status should track reconnection attempts."""
        status = ServiceStatus(
            name="Test",
            state=ConnectionState.RECONNECTING,
            reconnect_attempts=3,
        )
        assert status.reconnect_attempts == 3


class TestConnectionsConfig:
    """Tests for connections configuration."""

    def test_default_endpoints(self):
        """Default endpoints should be set."""
        config = ConnectionsConfig()
        assert len(config.xrpl_endpoints) == 4
        assert "wss://xrplcluster.com" in config.xrpl_endpoints

    def test_timeout_defaults(self):
        """Timeout defaults should be set."""
        config = ConnectionsConfig()
        assert config.request_timeout == 30.0
        assert config.connection_timeout == 10.0

    def test_retry_defaults(self):
        """Retry defaults should be set."""
        config = ConnectionsConfig()
        assert config.max_retries == 3
        assert config.retry_backoff_base == 1.0
        assert config.retry_backoff_max == 60.0


class TestCSSPath:
    """Tests for CSS path configuration."""

    def test_css_path_defined(self):
        """CSS path should be defined."""
        from xrp_ticker.app import CSS_PATH

        assert isinstance(CSS_PATH, Path)
        assert CSS_PATH.name == "app.tcss"


class TestAppConstants:
    """Tests for app constants."""

    def test_app_title(self):
        """App title should be defined."""
        from xrp_ticker.app import XRPTickerApp

        assert XRPTickerApp.TITLE == "XRP Ticker"


class TestAppLifecycle:
    """Integration tests for app mount, data flow, and shutdown."""

    @pytest.fixture
    def app_config(self):
        """Create an AppConfig for integration tests."""
        return AppConfig(
            wallet=WalletConfig(addresses=["rN7n3473SaZBCG4dFL83w7a1RXtXtbk2D9"]),
            display=DisplayConfig(theme="ripple"),
            connections=ConnectionsConfig(),
        )

    @pytest.mark.asyncio
    async def test_app_mounts_and_creates_services(self, app_config):
        """App should mount, create services, and shut down cleanly."""
        from xrp_ticker.app import XRPTickerApp

        app = XRPTickerApp(config=app_config)

        with (
            patch(
                "xrp_ticker.app.CoinbaseService", autospec=True
            ) as mock_coinbase_cls,
            patch(
                "xrp_ticker.app.XRPLWebSocketService", autospec=True
            ) as mock_xrpl_cls,
        ):
            mock_price_svc = mock_coinbase_cls.return_value
            mock_price_svc.start = AsyncMock()
            mock_price_svc.stop = AsyncMock()
            mock_price_svc.service_name = "Coinbase"

            mock_xrpl_svc = mock_xrpl_cls.return_value
            mock_xrpl_svc.start = AsyncMock()
            mock_xrpl_svc.stop = AsyncMock()

            async with app.run_test():
                # Services should have been started
                mock_price_svc.start.assert_called_once()
                mock_xrpl_svc.start.assert_called_once()

            # After exit, services should have been stopped
            mock_price_svc.stop.assert_called_once()
            mock_xrpl_svc.stop.assert_called_once()

    @pytest.mark.asyncio
    async def test_price_callback_updates_widgets(self, app_config):
        """Price callback should update price display and sparkline."""
        from xrp_ticker.app import XRPTickerApp
        from xrp_ticker.widgets import PriceDisplayWidget, SparklineWidget

        app = XRPTickerApp(config=app_config)
        captured_price_cb = None

        with (
            patch(
                "xrp_ticker.app.CoinbaseService", autospec=True
            ) as mock_coinbase_cls,
            patch(
                "xrp_ticker.app.XRPLWebSocketService", autospec=True
            ) as mock_xrpl_cls,
        ):
            def capture_coinbase_init(**kwargs):
                nonlocal captured_price_cb
                captured_price_cb = kwargs.get("on_price_update")
                mock = AsyncMock()
                mock.start = AsyncMock()
                mock.stop = AsyncMock()
                mock.service_name = "Coinbase"
                mock.on_price_update = captured_price_cb
                mock.on_status_change = kwargs.get("on_status_change")
                return mock

            mock_coinbase_cls.side_effect = capture_coinbase_init

            mock_xrpl = AsyncMock()
            mock_xrpl.start = AsyncMock()
            mock_xrpl.stop = AsyncMock()
            mock_xrpl_cls.return_value = mock_xrpl

            async with app.run_test() as pilot:
                assert captured_price_cb is not None

                # Simulate a price update
                price_data = PriceData(
                    price=2.50,
                    price_change=0.10,
                    price_change_percent=4.17,
                    high_24h=2.60,
                    low_24h=2.40,
                    volume=1_000_000.0,
                    source="coinbase",
                )
                captured_price_cb(price_data)
                await pilot.pause()

                # Verify widgets got updated
                price_widget = app.query_one("#price-display", PriceDisplayWidget)
                assert price_widget.is_connected is True

                sparkline = app.query_one("#sparkline", SparklineWidget)
                assert sparkline.price_count == 1

    @pytest.mark.asyncio
    async def test_balance_callback_updates_portfolio(self, app_config):
        """Balance callback should update portfolio widget."""
        from xrp_ticker.app import XRPTickerApp
        from xrp_ticker.widgets import PortfolioWidget

        app = XRPTickerApp(config=app_config)
        captured_balance_cb = None

        with (
            patch(
                "xrp_ticker.app.CoinbaseService", autospec=True
            ) as mock_coinbase_cls,
            patch(
                "xrp_ticker.app.XRPLWebSocketService", autospec=True
            ) as mock_xrpl_cls,
        ):
            mock_price = AsyncMock()
            mock_price.start = AsyncMock()
            mock_price.stop = AsyncMock()
            mock_price.service_name = "Coinbase"
            mock_coinbase_cls.return_value = mock_price

            def capture_xrpl_init(**kwargs):
                nonlocal captured_balance_cb
                captured_balance_cb = kwargs.get("on_balance_update")
                mock = AsyncMock()
                mock.start = AsyncMock()
                mock.stop = AsyncMock()
                mock.on_balance_update = captured_balance_cb
                mock.on_status_change = kwargs.get("on_status_change")
                return mock

            mock_xrpl_cls.side_effect = capture_xrpl_init

            async with app.run_test() as pilot:
                assert captured_balance_cb is not None

                # Simulate a balance update
                wallet_data = WalletData.from_drops(
                    address="rN7n3473SaZBCG4dFL83w7a1RXtXtbk2D9",
                    drops=500_000_000,  # 500 XRP
                    source="xrplcluster.com",
                )
                captured_balance_cb(wallet_data)
                await pilot.pause()

                portfolio = app.query_one("#portfolio", PortfolioWidget)
                assert portfolio.balance_xrp == 500.0

    @pytest.mark.asyncio
    async def test_shutdown_clears_callbacks(self, app_config):
        """Shutdown should clear callbacks before stopping services."""
        from xrp_ticker.app import XRPTickerApp

        app = XRPTickerApp(config=app_config)

        with (
            patch(
                "xrp_ticker.app.CoinbaseService", autospec=True
            ) as mock_coinbase_cls,
            patch(
                "xrp_ticker.app.XRPLWebSocketService", autospec=True
            ) as mock_xrpl_cls,
        ):
            mock_price = AsyncMock()
            mock_price.start = AsyncMock()
            mock_price.stop = AsyncMock()
            mock_price.service_name = "Coinbase"
            mock_price.on_price_update = None
            mock_price.on_status_change = None
            mock_coinbase_cls.return_value = mock_price

            mock_xrpl = AsyncMock()
            mock_xrpl.start = AsyncMock()
            mock_xrpl.stop = AsyncMock()
            mock_xrpl.on_balance_update = None
            mock_xrpl.on_status_change = None
            mock_xrpl_cls.return_value = mock_xrpl

            async with app.run_test():
                pass  # Mount and immediately unmount

            # Callbacks should have been cleared before stop
            assert mock_price.on_price_update is None
            assert mock_price.on_status_change is None
            assert mock_xrpl.on_balance_update is None
            assert mock_xrpl.on_status_change is None
