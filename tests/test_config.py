"""Tests for configuration loading and validation."""

import tempfile
from pathlib import Path

import pytest

from xrp_ticker.config import (
    AppConfig,
    ConnectionsConfig,
    DisplayConfig,
    WalletConfig,
    create_default_config,
    load_config,
)


class TestWalletConfig:
    """Tests for WalletConfig validation."""

    def test_valid_address(self):
        """Valid XRP address should pass validation."""
        config = WalletConfig(addresses=["rN7n3473SaZBCG4dFL83w7a1RXtXtbk2D9"])
        assert len(config.addresses) == 1
        assert config.addresses[0] == "rN7n3473SaZBCG4dFL83w7a1RXtXtbk2D9"

    def test_multiple_addresses(self):
        """Multiple valid addresses should pass validation."""
        addresses = [
            "rN7n3473SaZBCG4dFL83w7a1RXtXtbk2D9",
            "rETnan6RaUmPnsPHoMjZqb1smNPeWwwago",
        ]
        config = WalletConfig(addresses=addresses)
        assert len(config.addresses) == 2

    def test_invalid_address_not_starting_with_r(self):
        """Address not starting with 'r' should fail."""
        with pytest.raises(ValueError, match="must start with 'r'"):
            WalletConfig(addresses=["xN7n3473SaZBCG4dFL83w7a1RXtXtbk2D9"])

    def test_invalid_address_too_short(self):
        """Address shorter than 25 characters should fail."""
        with pytest.raises(ValueError, match="must be 25-35 characters"):
            WalletConfig(addresses=["rShort"])

    def test_invalid_address_too_long(self):
        """Address longer than 35 characters should fail."""
        with pytest.raises(ValueError, match="must be 25-35 characters"):
            WalletConfig(addresses=["r" + "A" * 40])

    def test_legacy_address_field(self):
        """Legacy 'address' field should be converted to 'addresses' list."""
        config = WalletConfig.model_validate(
            {"address": "rN7n3473SaZBCG4dFL83w7a1RXtXtbk2D9"}
        )
        assert config.addresses == ["rN7n3473SaZBCG4dFL83w7a1RXtXtbk2D9"]

    def test_single_address_string_converted_to_list(self):
        """Single address string should be converted to list."""
        config = WalletConfig(addresses="rN7n3473SaZBCG4dFL83w7a1RXtXtbk2D9")
        assert config.addresses == ["rN7n3473SaZBCG4dFL83w7a1RXtXtbk2D9"]


class TestDisplayConfig:
    """Tests for DisplayConfig validation."""

    def test_default_values(self):
        """Default values should be set correctly."""
        config = DisplayConfig()
        assert config.refresh_rate == 0.5
        assert config.sparkline_minutes == 60
        assert config.theme == "cyberpunk"

    def test_refresh_rate_bounds(self):
        """Refresh rate should be within bounds."""
        config = DisplayConfig(refresh_rate=0.1)
        assert config.refresh_rate == 0.1

        config = DisplayConfig(refresh_rate=5.0)
        assert config.refresh_rate == 5.0

    def test_refresh_rate_too_low(self):
        """Refresh rate below 0.1 should fail."""
        with pytest.raises(ValueError):
            DisplayConfig(refresh_rate=0.05)

    def test_refresh_rate_too_high(self):
        """Refresh rate above 5.0 should fail."""
        with pytest.raises(ValueError):
            DisplayConfig(refresh_rate=10.0)


class TestConnectionsConfig:
    """Tests for ConnectionsConfig."""

    def test_default_endpoints(self):
        """Default XRPL endpoints should be set."""
        config = ConnectionsConfig()
        assert len(config.xrpl_endpoints) == 4
        assert "wss://xrplcluster.com" in config.xrpl_endpoints

    def test_poll_interval_bounds(self):
        """Poll interval should be within bounds."""
        config = ConnectionsConfig(xrpl_poll_interval=10)
        assert config.xrpl_poll_interval == 10

        config = ConnectionsConfig(xrpl_poll_interval=300)
        assert config.xrpl_poll_interval == 300

    def test_poll_interval_too_low(self):
        """Poll interval below 10 should fail."""
        with pytest.raises(ValueError):
            ConnectionsConfig(xrpl_poll_interval=5)

    def test_endpoint_must_be_wss(self):
        """Endpoints must use wss:// scheme."""
        with pytest.raises(ValueError, match="Only secure WebSocket"):
            ConnectionsConfig(xrpl_endpoints=["ws://xrplcluster.com"])

    def test_endpoint_must_be_trusted(self):
        """Endpoints must be in trusted allowlist."""
        with pytest.raises(ValueError, match="not in trusted allowlist"):
            ConnectionsConfig(xrpl_endpoints=["wss://evil-xrpl.attacker.com"])

    def test_empty_endpoints_rejected(self):
        """Empty endpoint list should be rejected."""
        with pytest.raises(ValueError, match="At least one XRPL endpoint"):
            ConnectionsConfig(xrpl_endpoints=[])

    def test_trusted_endpoints_accepted(self):
        """All trusted endpoints should be accepted."""
        trusted = [
            "wss://xrplcluster.com",
            "wss://s1.ripple.com",
            "wss://s2.ripple.com",
            "wss://xrpl.ws",
        ]
        config = ConnectionsConfig(xrpl_endpoints=trusted)
        assert config.xrpl_endpoints == trusted

    def test_partial_trusted_endpoints(self):
        """Subset of trusted endpoints should be accepted."""
        config = ConnectionsConfig(xrpl_endpoints=["wss://xrplcluster.com"])
        assert config.xrpl_endpoints == ["wss://xrplcluster.com"]


class TestAppConfig:
    """Tests for AppConfig."""

    def test_minimal_config(self):
        """Minimal config with just wallet should work."""
        config = AppConfig(
            wallet=WalletConfig(addresses=["rN7n3473SaZBCG4dFL83w7a1RXtXtbk2D9"])
        )
        assert config.wallet.addresses[0] == "rN7n3473SaZBCG4dFL83w7a1RXtXtbk2D9"
        assert config.display.refresh_rate == 0.5
        assert len(config.connections.xrpl_endpoints) == 4


class TestLoadConfig:
    """Tests for config file loading."""

    def test_load_valid_config(self):
        """Valid TOML config should load correctly."""
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".toml", delete=False
        ) as f:
            f.write("""
[wallet]
addresses = ["rN7n3473SaZBCG4dFL83w7a1RXtXtbk2D9"]

[display]
refresh_rate = 1.0
theme = "monokai"

[connections]
xrpl_poll_interval = 60
""")
            f.flush()
            config = load_config(Path(f.name))

        assert config is not None
        assert config.wallet.addresses[0] == "rN7n3473SaZBCG4dFL83w7a1RXtXtbk2D9"
        assert config.display.refresh_rate == 1.0
        assert config.display.theme == "monokai"
        assert config.connections.xrpl_poll_interval == 60

    def test_load_nonexistent_config(self):
        """Loading nonexistent config should return None."""
        config = load_config(Path("/nonexistent/path/config.toml"))
        assert config is None


class TestCreateDefaultConfig:
    """Tests for default config creation."""

    def test_create_default_config(self):
        """Default config should be created with valid address."""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "config.toml"
            result = create_default_config(
                "rN7n3473SaZBCG4dFL83w7a1RXtXtbk2D9",
                output_path=output_path,
            )

            assert result == output_path
            assert output_path.exists()

            # Verify it's loadable
            config = load_config(output_path)
            assert config is not None
            assert config.wallet.addresses[0] == "rN7n3473SaZBCG4dFL83w7a1RXtXtbk2D9"
