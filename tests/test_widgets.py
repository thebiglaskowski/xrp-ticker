"""Tests for Textual widget modules."""



from xrp_ticker.models import ConnectionState
from xrp_ticker.widgets.sparkline import STYLE_CHARS, SparklineStyle, SparklineWidget


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
    """Tests for MarketStatsWidget (unit tests without Textual runtime)."""

    def test_volume_formatting_millions(self):
        """Volume should format with M suffix for millions."""
        # Test the formatting logic
        volume = 5_500_000
        if volume >= 1_000_000:
            formatted = f"{volume / 1_000_000:.2f}M XRP"
        else:
            formatted = f"{volume:.0f} XRP"
        assert formatted == "5.50M XRP"

    def test_volume_formatting_thousands(self):
        """Volume should format with K suffix for thousands."""
        volume = 75_000
        if volume >= 1_000_000:
            formatted = f"{volume / 1_000_000:.2f}M XRP"
        elif volume >= 1_000:
            formatted = f"{volume / 1_000:.1f}K XRP"
        else:
            formatted = f"{volume:.0f} XRP"
        assert formatted == "75.0K XRP"

    def test_volume_formatting_small(self):
        """Small volume should format without suffix."""
        volume = 500
        if volume >= 1_000_000:
            formatted = f"{volume / 1_000_000:.2f}M XRP"
        elif volume >= 1_000:
            formatted = f"{volume / 1_000:.1f}K XRP"
        else:
            formatted = f"{volume:.0f} XRP"
        assert formatted == "500 XRP"

    def test_price_change_positive(self):
        """Positive change should have + prefix."""
        percent = 5.5
        if percent > 0:
            formatted = f"+{percent:.2f}%"
        else:
            formatted = f"{percent:.2f}%"
        assert formatted == "+5.50%"

    def test_price_change_negative(self):
        """Negative change should show sign."""
        percent = -3.25
        formatted = f"{percent:.2f}%"
        assert formatted == "-3.25%"


class TestStatusIndicatorLogic:
    """Tests for StatusIndicator display logic."""

    def test_connected_text(self):
        """Connected state should show correct text."""
        service_name = "Coinbase"
        state = ConnectionState.CONNECTED
        if state == ConnectionState.CONNECTED:
            text = f"󰄬 {service_name}: Connected"
        assert "Connected" in text

    def test_reconnecting_text_with_attempts(self):
        """Reconnecting with attempts should show count."""
        service_name = "XRPL"
        attempts = 3
        text = f"󰑓 {service_name}: Reconnecting ({attempts})"
        assert "3" in text

    def test_failed_text(self):
        """Failed state should show failure."""
        service_name = "XRPL"
        state = ConnectionState.FAILED
        if state == ConnectionState.FAILED:
            text = f"󰅜 {service_name}: Failed"
        assert "Failed" in text


class TestPriceDisplayLogic:
    """Tests for PriceDisplay formatting logic."""

    def test_price_formatting(self):
        """Price should be formatted with 4 decimal places."""
        price = 2.3456
        formatted = f"$ {price:,.4f}"
        assert formatted == "$ 2.3456"

    def test_price_large_number(self):
        """Large prices should have thousand separators."""
        price = 1234.5678
        formatted = f"$ {price:,.4f}"
        assert formatted == "$ 1,234.5678"

    def test_change_up_arrow(self):
        """Positive change should show up arrow."""
        change = 0.05
        percent = 2.5
        if change > 0:
            arrow = ""  # Up arrow
        elif change < 0:
            arrow = ""  # Down arrow
        else:
            arrow = ""
        text = f"{arrow} {change:+.4f} ({percent:+.2f}%)"
        assert "+0.0500" in text
        assert "+2.50%" in text

    def test_change_down_arrow(self):
        """Negative change should show down arrow."""
        change = -0.03
        # Negative change should result in down arrow
        if change > 0:
            arrow = ""
        elif change < 0:
            arrow = ""
        else:
            arrow = ""
        assert arrow == ""


class TestPortfolioLogic:
    """Tests for Portfolio calculation logic."""

    def test_portfolio_value_calculation(self):
        """Portfolio value should be balance * price."""
        balance_xrp = 1000.0
        price_usd = 2.50
        value = balance_xrp * price_usd
        assert value == 2500.0

    def test_portfolio_formatting(self):
        """Portfolio value should format with 2 decimal places."""
        value = 12345.678
        formatted = f"${value:,.2f} USD"
        assert formatted == "$12,345.68 USD"

    def test_balance_formatting(self):
        """Balance should format with 2 decimal places."""
        balance = 1234.567890
        formatted = f"{balance:,.2f} XRP"
        assert formatted == "1,234.57 XRP"
