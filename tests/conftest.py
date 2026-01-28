"""Shared pytest fixtures for XRP Ticker tests."""

import pytest

from xrp_ticker.config import AppConfig, ConnectionsConfig, DisplayConfig, WalletConfig
from xrp_ticker.models import ConnectionState, PriceData, ServiceStatus, WalletData

# Sample valid XRP addresses for testing
VALID_ADDRESS_1 = "rN7n3473SaZBCG4dFL83w7a1RXtXtbk2D9"
VALID_ADDRESS_2 = "rETnan6RaUmPnsPHoMjZqb1smNPeWwwago"


@pytest.fixture
def valid_xrp_address() -> str:
    """Return a valid XRP address for testing."""
    return VALID_ADDRESS_1


@pytest.fixture
def valid_xrp_addresses() -> list[str]:
    """Return a list of valid XRP addresses for testing."""
    return [VALID_ADDRESS_1, VALID_ADDRESS_2]


@pytest.fixture
def sample_wallet_config(valid_xrp_address) -> WalletConfig:
    """Create a sample WalletConfig for testing."""
    return WalletConfig(addresses=[valid_xrp_address])


@pytest.fixture
def sample_display_config() -> DisplayConfig:
    """Create a sample DisplayConfig for testing."""
    return DisplayConfig(
        refresh_rate=0.5,
        sparkline_minutes=60,
        theme="ripple",
    )


@pytest.fixture
def sample_connections_config() -> ConnectionsConfig:
    """Create a sample ConnectionsConfig for testing."""
    return ConnectionsConfig(
        xrpl_poll_interval=30,
        request_timeout=30.0,
        connection_timeout=10.0,
    )


@pytest.fixture
def sample_app_config(
    sample_wallet_config,
    sample_display_config,
    sample_connections_config,
) -> AppConfig:
    """Create a sample AppConfig for testing."""
    return AppConfig(
        wallet=sample_wallet_config,
        display=sample_display_config,
        connections=sample_connections_config,
    )


@pytest.fixture
def sample_price_data() -> PriceData:
    """Create sample price data for testing."""
    return PriceData(
        symbol="XRPUSD",
        price=2.50,
        price_change=0.10,
        price_change_percent=4.17,
        high_24h=2.60,
        low_24h=2.40,
        volume=1_000_000.0,
        source="coinbase",
    )


@pytest.fixture
def sample_wallet_data(valid_xrp_address) -> WalletData:
    """Create sample wallet data for testing."""
    return WalletData.from_drops(
        address=valid_xrp_address,
        drops=100_000_000,  # 100 XRP
        source="xrplcluster.com",
    )


@pytest.fixture
def connected_status() -> ServiceStatus:
    """Create a connected ServiceStatus for testing."""
    return ServiceStatus(
        name="TestService",
        state=ConnectionState.CONNECTED,
    )


@pytest.fixture
def disconnected_status() -> ServiceStatus:
    """Create a disconnected ServiceStatus for testing."""
    return ServiceStatus(
        name="TestService",
        state=ConnectionState.DISCONNECTED,
    )


@pytest.fixture
def reconnecting_status() -> ServiceStatus:
    """Create a reconnecting ServiceStatus for testing."""
    return ServiceStatus(
        name="TestService",
        state=ConnectionState.RECONNECTING,
        reconnect_attempts=3,
        error_message="Connection lost",
    )
