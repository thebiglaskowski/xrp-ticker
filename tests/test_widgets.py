"""Tests for Textual widget modules."""

from xrp_ticker.constants import format_volume
from xrp_ticker.models import ConnectionState
from xrp_ticker.widgets.market_stats import MarketStatsWidget, StatBox
from xrp_ticker.widgets.portfolio import PortfolioWidget
from xrp_ticker.widgets.price_display import PriceDisplayWidget
from xrp_ticker.widgets.sparkline import STYLE_CHARS, SparklineStyle, SparklineWidget
from xrp_ticker.widgets.status_bar import StatusBarWidget, StatusIndicator


class TestSparklineWidget:
    """Tests for SparklineWidget."""

    def test_initial_state(self):
        """Widget should start with empty sparkline."""
        widget = SparklineWidget()
        assert widget.sparkline == ""
        assert widget.price_count == 0
        assert widget.trend == "neutral"

    def test_default_style(self):
        """Default style should be BRAILLE."""
        widget = SparklineWidget()
        assert widget.style == SparklineStyle.BRAILLE

    def test_custom_style(self):
        """Custom style should be applied."""
        widget = SparklineWidget(style=SparklineStyle.BLOCKS)
        assert widget.style == SparklineStyle.BLOCKS

    def test_max_points(self):
        """Widget should respect max_points setting."""
        widget = SparklineWidget(max_points=10)
        assert widget.max_points == 10

    def test_add_price(self):
        """Adding price should update price count."""
        widget = SparklineWidget()
        widget.add_price(1.0)
        assert widget.price_count == 1
        widget.add_price(2.0)
        assert widget.price_count == 2

    def test_sparkline_requires_two_prices(self):
        """Sparkline should be empty with less than 2 prices."""
        widget = SparklineWidget()
        widget.add_price(1.0)
        assert widget.sparkline == ""

    def test_sparkline_generated_with_two_prices(self):
        """Sparkline should be generated with 2+ prices."""
        widget = SparklineWidget()
        widget.add_price(1.0)
        widget.add_price(2.0)
        assert widget.sparkline != ""

    def test_trend_up(self):
        """Trend should be up when last price > first price."""
        widget = SparklineWidget()
        widget.add_price(1.0)
        widget.add_price(1.5)
        widget.add_price(2.0)
        assert widget.trend == "up"

    def test_trend_down(self):
        """Trend should be down when last price < first price."""
        widget = SparklineWidget()
        widget.add_price(2.0)
        widget.add_price(1.5)
        widget.add_price(1.0)
        assert widget.trend == "down"

    def test_trend_neutral(self):
        """Trend should be neutral when prices are equal."""
        widget = SparklineWidget()
        widget.add_price(1.0)
        widget.add_price(1.5)
        widget.add_price(1.0)
        assert widget.trend == "neutral"

    def test_cycle_style(self):
        """Cycling style should move to next style."""
        widget = SparklineWidget(style=SparklineStyle.BLOCKS)
        new_style = widget.cycle_style()
        assert widget.style != SparklineStyle.BLOCKS
        assert new_style == widget.style.value

    def test_cycle_style_wraps(self):
        """Cycling should wrap around to first style."""
        widget = SparklineWidget()
        styles_count = len(SparklineStyle)
        for _ in range(styles_count):
            widget.cycle_style()
        # Should be back to original
        assert widget.style == SparklineStyle.BRAILLE

    def test_clear(self):
        """Clear should reset all state."""
        widget = SparklineWidget()
        widget.add_price(1.0)
        widget.add_price(2.0)
        widget.clear()
        assert widget.sparkline == ""
        assert widget.price_count == 0

    def test_max_points_enforced(self):
        """Prices beyond max_points should be dropped."""
        widget = SparklineWidget(max_points=5)
        for i in range(10):
            widget.add_price(float(i))
        assert widget.price_count == 5

    def test_render_waiting_message(self):
        """Render should show waiting message when no data."""
        widget = SparklineWidget()
        result = widget.render()
        assert "Collecting" in result

    def test_render_sparkline(self):
        """Render should show sparkline when data exists."""
        widget = SparklineWidget()
        widget.add_price(1.0)
        widget.add_price(2.0)
        result = widget.render()
        assert result == widget.sparkline

    def test_all_styles_have_chars(self):
        """All styles should have character mappings."""
        for style in SparklineStyle:
            assert style in STYLE_CHARS
            assert len(STYLE_CHARS[style]) > 0

    def test_same_prices_uses_mid_char(self):
        """Same prices should use middle character."""
        widget = SparklineWidget()
        widget.add_price(1.0)
        widget.add_price(1.0)
        widget.add_price(1.0)
        # All chars should be the same (middle char)
        assert len(set(widget.sparkline)) == 1


class TestSparklineStyle:
    """Tests for SparklineStyle enum."""

    def test_all_styles_defined(self):
        """All expected styles should be defined."""
        assert SparklineStyle.BLOCKS.value == "blocks"
        assert SparklineStyle.BRAILLE.value == "braille"
        assert SparklineStyle.DOTS.value == "dots"
        assert SparklineStyle.LINE.value == "line"


class TestMarketStatsWidget:
    """Tests for MarketStatsWidget."""

    def test_widget_constructable(self):
        """Widget should be constructable with standard params."""
        widget = MarketStatsWidget(id="test-stats")
        assert widget.id == "test-stats"

    def test_has_reactive_attributes(self):
        """Widget class should define expected reactive attributes."""
        assert hasattr(MarketStatsWidget, "high_24h")
        assert hasattr(MarketStatsWidget, "low_24h")
        assert hasattr(MarketStatsWidget, "volume_24h")
        assert hasattr(MarketStatsWidget, "current_price")
        assert hasattr(MarketStatsWidget, "price_change_percent")

    def test_update_from_price_data_method_exists(self):
        """Widget should expose update_from_price_data method."""
        widget = MarketStatsWidget()
        assert callable(widget.update_from_price_data)

    def test_volume_formatting_uses_centralized_function(self):
        """Volume formatting should match constants.format_volume."""
        assert format_volume(5_500_000) == "5.50M XRP"
        assert format_volume(75_000) == "75.0K XRP"
        assert format_volume(500) == "500 XRP"

    def test_statbox_constructable(self):
        """StatBox should be constructable with label and value."""
        box = StatBox("Test Label", "---", id="test-box")
        assert box._label == "Test Label"
        assert box._value == "---"


class TestStatusIndicator:
    """Tests for StatusIndicator widget."""

    def test_initial_state(self):
        """StatusIndicator should start disconnected."""
        indicator = StatusIndicator("Coinbase")
        assert indicator.state == ConnectionState.DISCONNECTED
        assert indicator._service_name == "Coinbase"

    def test_update_state_sets_state(self):
        """update_state should update the reactive state attribute."""
        indicator = StatusIndicator("Coinbase")
        indicator.update_state(ConnectionState.CONNECTED, reconnect_attempts=0)
        assert indicator.state == ConnectionState.CONNECTED
        assert indicator._reconnect_attempts == 0

    def test_update_state_tracks_reconnect_attempts(self):
        """update_state should track reconnect attempts."""
        indicator = StatusIndicator("XRPL")
        indicator.update_state(ConnectionState.RECONNECTING, reconnect_attempts=3)
        assert indicator.state == ConnectionState.RECONNECTING
        assert indicator._reconnect_attempts == 3

    def test_all_connection_states(self):
        """StatusIndicator should accept all connection states."""
        indicator = StatusIndicator("Test")
        for state in ConnectionState:
            indicator.update_state(state)
            assert indicator.state == state


class TestStatusBarWidget:
    """Tests for StatusBarWidget."""

    def test_constructable(self):
        """StatusBarWidget should be constructable."""
        widget = StatusBarWidget(id="test-bar")
        assert widget.id == "test-bar"

    def test_has_reactive_last_update(self):
        """Widget class should define last_update reactive."""
        assert hasattr(StatusBarWidget, "last_update")

    def test_public_api_methods_exist(self):
        """Widget should expose public API methods."""
        widget = StatusBarWidget()
        assert callable(widget.update_price_status)
        assert callable(widget.update_xrpl_status)
        assert callable(widget.set_update_time)


class TestPriceDisplayWidget:
    """Tests for PriceDisplayWidget."""

    def test_constructable(self):
        """Widget should be constructable with standard params."""
        widget = PriceDisplayWidget(id="test-price")
        assert widget.id == "test-price"

    def test_has_reactive_attributes(self):
        """Widget class should define expected reactive attributes."""
        assert hasattr(PriceDisplayWidget, "price")
        assert hasattr(PriceDisplayWidget, "price_change")
        assert hasattr(PriceDisplayWidget, "price_change_percent")
        assert hasattr(PriceDisplayWidget, "is_connected")

    def test_previous_price_tracking(self):
        """Widget should initialize previous price as None."""
        widget = PriceDisplayWidget()
        assert widget._previous_price is None

    def test_update_price_data_method_exists(self):
        """Widget should expose update_price_data method."""
        widget = PriceDisplayWidget()
        assert callable(widget.update_price_data)

    def test_price_formatting(self):
        """Price should be formatted with 4 decimal places."""
        assert f"$ {2.3456:,.4f}" == "$ 2.3456"
        assert f"$ {1234.5678:,.4f}" == "$ 1,234.5678"

    def test_change_formatting(self):
        """Price change should show direction and percentage."""
        change = 0.05
        percent = 2.5
        text = f"{change:+.4f} ({percent:+.2f}%)"
        assert "+0.0500" in text
        assert "+2.50%" in text


class TestPortfolioWidget:
    """Tests for PortfolioWidget."""

    def test_constructable(self):
        """Widget should be constructable with standard params."""
        widget = PortfolioWidget(id="test-portfolio")
        assert widget.id == "test-portfolio"

    def test_has_reactive_attributes(self):
        """Widget class should define expected reactive attributes."""
        assert hasattr(PortfolioWidget, "balance_xrp")
        assert hasattr(PortfolioWidget, "price_usd")
        assert hasattr(PortfolioWidget, "portfolio_value")

    def test_public_api_methods_exist(self):
        """Widget should expose public API methods."""
        widget = PortfolioWidget()
        assert callable(widget.update_balance)
        assert callable(widget.update_price)

    def test_portfolio_value_calculation(self):
        """Portfolio value should be balance * price."""
        balance_xrp = 1000.0
        price_usd = 2.50
        value = balance_xrp * price_usd
        assert value == 2500.0

    def test_portfolio_formatting(self):
        """Portfolio value should format with 2 decimal places."""
        assert f"${12345.678:,.2f} USD" == "$12,345.68 USD"

    def test_balance_formatting(self):
        """Balance should format with 2 decimal places."""
        assert f"{1234.567890:,.2f} XRP" == "1,234.57 XRP"
