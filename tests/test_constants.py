"""Tests for constants module."""


from xrp_ticker.constants import (
    APP_NAME,
    APP_VERSION,
    BALANCE_DECIMAL_PLACES,
    CHANGE_DECIMAL_PLACES,
    CONNECTION_MESSAGES,
    DEFAULT_BALANCE_POLL_INTERVAL,
    DEFAULT_PRICE_POLL_INTERVAL,
    ERROR_MESSAGES,
    ICONS,
    LOG_MESSAGES,
    MAX_REASONABLE_XRP_PRICE,
    MIN_BALANCE_POLL_INTERVAL,
    MIN_PRICE_POLL_INTERVAL,
    PRICE_DECIMAL_PLACES,
    SHORTCUTS,
    VALUE_DECIMAL_PLACES,
    VOLUME_MILLIONS_THRESHOLD,
    VOLUME_THOUSANDS_THRESHOLD,
    XRP_DROPS_PER_UNIT,
    XRP_MAX_SUPPLY_DROPS,
    format_balance,
    format_change,
    format_portfolio_value,
    format_price,
    format_volume,
    format_xrp_balance,
)


class TestAppMetadata:
    """Tests for application metadata constants."""

    def test_app_name(self):
        """App name should be defined."""
        assert APP_NAME == "XRP Ticker"

    def test_app_version(self):
        """App version should be defined."""
        assert APP_VERSION == "0.1.0"


class TestXRPConstants:
    """Tests for XRP-related constants."""

    def test_drops_per_unit(self):
        """Drops per XRP should be correct."""
        assert XRP_DROPS_PER_UNIT == 1_000_000

    def test_max_supply(self):
        """Max supply should be 100 billion XRP in drops."""
        assert XRP_MAX_SUPPLY_DROPS == 100_000_000_000_000_000


class TestDecimalPlaces:
    """Tests for decimal place constants."""

    def test_price_decimal_places(self):
        """Price should use 4 decimal places."""
        assert PRICE_DECIMAL_PLACES == 4

    def test_change_decimal_places(self):
        """Change should use 2 decimal places."""
        assert CHANGE_DECIMAL_PLACES == 2

    def test_balance_decimal_places(self):
        """Balance should use 2 decimal places."""
        assert BALANCE_DECIMAL_PLACES == 2

    def test_value_decimal_places(self):
        """Value should use 2 decimal places."""
        assert VALUE_DECIMAL_PLACES == 2


class TestVolumeThresholds:
    """Tests for volume formatting thresholds."""

    def test_millions_threshold(self):
        """Millions threshold should be 1 million."""
        assert VOLUME_MILLIONS_THRESHOLD == 1_000_000

    def test_thousands_threshold(self):
        """Thousands threshold should be 1 thousand."""
        assert VOLUME_THOUSANDS_THRESHOLD == 1_000


class TestPriceValidation:
    """Tests for price validation constants."""

    def test_max_reasonable_price(self):
        """Max reasonable price should be defined."""
        assert MAX_REASONABLE_XRP_PRICE == 10000.0


class TestPollingIntervals:
    """Tests for polling interval constants."""

    def test_default_price_poll(self):
        """Default price poll should be 5 seconds."""
        assert DEFAULT_PRICE_POLL_INTERVAL == 5

    def test_default_balance_poll(self):
        """Default balance poll should be 30 seconds."""
        assert DEFAULT_BALANCE_POLL_INTERVAL == 30

    def test_min_price_poll(self):
        """Minimum price poll should be 5 seconds."""
        assert MIN_PRICE_POLL_INTERVAL == 5

    def test_min_balance_poll(self):
        """Minimum balance poll should be 10 seconds."""
        assert MIN_BALANCE_POLL_INTERVAL == 10


class TestConnectionMessages:
    """Tests for connection message constants."""

    def test_all_states_have_messages(self):
        """All connection states should have messages."""
        assert "connected" in CONNECTION_MESSAGES
        assert "disconnected" in CONNECTION_MESSAGES
        assert "reconnecting" in CONNECTION_MESSAGES
        assert "failed" in CONNECTION_MESSAGES


class TestIcons:
    """Tests for icon constants."""

    def test_status_icons(self):
        """Status icons should be defined."""
        assert "connected" in ICONS
        assert "disconnected" in ICONS
        assert "reconnecting" in ICONS
        assert "failed" in ICONS

    def test_price_icons(self):
        """Price icons should be defined."""
        assert "price_up" in ICONS
        assert "price_down" in ICONS

    def test_stat_icons(self):
        """Stat icons should be defined."""
        assert "high" in ICONS
        assert "low" in ICONS
        assert "change" in ICONS
        assert "volume" in ICONS


class TestShortcuts:
    """Tests for keyboard shortcut constants."""

    def test_essential_shortcuts(self):
        """Essential shortcuts should be defined."""
        assert "quit" in SHORTCUTS
        assert "refresh" in SHORTCUTS
        assert "theme" in SHORTCUTS
        assert "help" in SHORTCUTS


class TestErrorMessages:
    """Tests for error message constants."""

    def test_common_errors(self):
        """Common error messages should be defined."""
        assert "no_config" in ERROR_MESSAGES
        assert "invalid_address" in ERROR_MESSAGES
        assert "connection_failed" in ERROR_MESSAGES


class TestLogMessages:
    """Tests for log message constants."""

    def test_service_logs(self):
        """Service log messages should be defined."""
        assert "service_started" in LOG_MESSAGES
        assert "service_stopped" in LOG_MESSAGES


class TestFormatXrpBalance:
    """Tests for format_xrp_balance function."""

    def test_convert_drops_to_xrp(self):
        """Should convert drops to XRP."""
        assert format_xrp_balance(1_000_000) == 1.0
        assert format_xrp_balance(100_000_000) == 100.0
        assert format_xrp_balance(500_000) == 0.5


class TestFormatPrice:
    """Tests for format_price function."""

    def test_format_price(self):
        """Should format price with 4 decimal places."""
        result = format_price(2.5)
        assert result == "$ 2.5000"

    def test_format_price_with_commas(self):
        """Should include thousand separators."""
        result = format_price(1234.5678)
        assert result == "$ 1,234.5678"


class TestFormatChange:
    """Tests for format_change function."""

    def test_positive_change(self):
        """Should show up arrow for positive change."""
        result = format_change(0.05, 2.5)
        assert "+0.0500" in result
        assert "+2.50%" in result

    def test_negative_change(self):
        """Should show down arrow for negative change."""
        result = format_change(-0.03, -1.5)
        assert "-0.0300" in result
        assert "-1.50%" in result

    def test_zero_change(self):
        """Should handle zero change."""
        result = format_change(0.0, 0.0)
        assert "+0.0000" in result
        assert "+0.00%" in result


class TestFormatVolume:
    """Tests for format_volume function."""

    def test_millions(self):
        """Should format millions with M suffix."""
        assert format_volume(5_500_000) == "5.50M XRP"

    def test_thousands(self):
        """Should format thousands with K suffix."""
        assert format_volume(75_000) == "75.0K XRP"

    def test_small(self):
        """Should format small volumes without suffix."""
        assert format_volume(500) == "500 XRP"


class TestFormatBalance:
    """Tests for format_balance function."""

    def test_format_balance(self):
        """Should format balance with 2 decimal places."""
        assert format_balance(1234.567890) == "1,234.57 XRP"


class TestFormatPortfolioValue:
    """Tests for format_portfolio_value function."""

    def test_format_value(self):
        """Should format value with USD prefix."""
        assert format_portfolio_value(12345.67) == "$12,345.67 USD"
