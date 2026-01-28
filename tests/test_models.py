"""Tests for Pydantic models."""

from datetime import datetime

import pytest

from xrp_ticker.models import (
    ConnectionState,
    PriceData,
    ServiceStatus,
    WalletData,
    XRPLAccountInfo,
)


class TestPriceData:
    """Tests for PriceData model."""

    def test_basic_price_data(self):
        """Basic price data should be created correctly."""
        data = PriceData(price=2.5)
        assert data.price == 2.5
        assert data.symbol == "XRPUSDT"
        assert data.source == "unknown"

    def test_price_must_be_non_negative(self):
        """Price must be >= 0."""
        with pytest.raises(ValueError):
            PriceData(price=-1.0)

    def test_string_price_conversion(self):
        """String prices should be converted to float."""
        data = PriceData(price="2.5678")
        assert data.price == 2.5678

    def test_full_price_data(self):
        """Full price data with all fields."""
        data = PriceData(
            symbol="XRPUSD",
            price=2.5,
            price_change=0.15,
            price_change_percent=6.38,
            high_24h=2.75,
            low_24h=2.30,
            volume=1000000.0,
            source="coinbase",
        )
        assert data.high_24h == 2.75
        assert data.low_24h == 2.30
        assert data.volume == 1000000.0


class TestWalletData:
    """Tests for WalletData model."""

    def test_wallet_data_from_drops(self):
        """WalletData.from_drops should create correct data."""
        data = WalletData.from_drops(
            address="rN7n3473SaZBCG4dFL83w7a1RXtXtbk2D9",
            drops=1000000000,  # 1000 XRP
            source="xrplcluster.com",
        )
        assert data.address == "rN7n3473SaZBCG4dFL83w7a1RXtXtbk2D9"
        assert data.balance_drops == 1000000000
        assert data.balance_xrp == 1000.0
        assert data.source == "xrplcluster.com"

    def test_balance_drops_non_negative(self):
        """Balance drops must be >= 0."""
        with pytest.raises(ValueError):
            WalletData(
                address="rN7n3473SaZBCG4dFL83w7a1RXtXtbk2D9",
                balance_drops=-1,
                balance_xrp=0,
            )

    def test_xrp_calculated_from_drops(self):
        """XRP balance should be calculated from drops if not provided."""
        data = WalletData(
            address="rN7n3473SaZBCG4dFL83w7a1RXtXtbk2D9",
            balance_drops=50000000,  # 50 XRP
            balance_xrp=0,  # Will be calculated
        )
        assert data.balance_xrp == 50.0


class TestXRPLAccountInfo:
    """Tests for XRPLAccountInfo model."""

    def test_to_wallet_data(self):
        """XRPLAccountInfo should convert to WalletData."""
        info = XRPLAccountInfo(
            Account="rN7n3473SaZBCG4dFL83w7a1RXtXtbk2D9",
            Balance="123456789",
        )
        wallet = info.to_wallet_data()

        assert wallet.address == "rN7n3473SaZBCG4dFL83w7a1RXtXtbk2D9"
        assert wallet.balance_drops == 123456789
        assert wallet.balance_xrp == pytest.approx(123.456789, rel=1e-6)


class TestServiceStatus:
    """Tests for ServiceStatus model."""

    def test_default_state(self):
        """Default state should be disconnected."""
        status = ServiceStatus(name="TestService")
        assert status.state == ConnectionState.DISCONNECTED
        assert status.is_connected is False
        assert status.reconnect_attempts == 0

    def test_is_connected(self):
        """is_connected should reflect connection state."""
        status = ServiceStatus(name="TestService", state=ConnectionState.CONNECTED)
        assert status.is_connected is True

        status.state = ConnectionState.RECONNECTING
        assert status.is_connected is False

    def test_is_stale_without_message(self):
        """is_stale should be True without last_message."""
        status = ServiceStatus(name="TestService")
        assert status.is_stale is True

    def test_is_stale_with_recent_message(self):
        """is_stale should be False with recent message."""
        status = ServiceStatus(name="TestService", last_message=datetime.now())
        assert status.is_stale is False


class TestConnectionState:
    """Tests for ConnectionState enum."""

    def test_all_states(self):
        """All connection states should be defined."""
        assert ConnectionState.CONNECTED == "connected"
        assert ConnectionState.DISCONNECTED == "disconnected"
        assert ConnectionState.RECONNECTING == "reconnecting"
        assert ConnectionState.FAILED == "failed"
