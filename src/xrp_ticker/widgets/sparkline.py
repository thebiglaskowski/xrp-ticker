"""Sparkline chart widget for price history visualization."""

from collections import deque
from enum import Enum

from textual.reactive import reactive
from textual.widget import Widget


class SparklineStyle(Enum):
    """Available sparkline rendering styles."""
    BLOCKS = "blocks"
    BRAILLE = "braille"
    DOTS = "dots"
    LINE = "line"


# Character sets for each style
STYLE_CHARS = {
    SparklineStyle.BLOCKS: " ▁▂▃▄▅▆▇█",
    SparklineStyle.BRAILLE: " ⣀⣤⣶⣿",
    SparklineStyle.DOTS: " ·•●",
    SparklineStyle.LINE: " ⎽⎼⎻⎺",
}


class SparklineWidget(Widget):
    """Unicode sparkline chart showing recent price history."""

    DEFAULT_CSS = """
    SparklineWidget {
        width: 100%;
        height: 3;
        padding: 0 2;
        content-align: center middle;
    }

    SparklineWidget .sparkline-text {
        color: $primary;
        text-align: center;
    }

    SparklineWidget.trend-up .sparkline-text {
        color: $success;
    }

    SparklineWidget.trend-down .sparkline-text {
        color: $error;
    }
    """

    # Reactive sparkline string
    sparkline: reactive[str] = reactive("")

    def __init__(
        self,
        max_points: int = 60,
        style: SparklineStyle = SparklineStyle.BRAILLE,
        name: str | None = None,
        id: str | None = None,
        classes: str | None = None,
    ) -> None:
        super().__init__(name=name, id=id, classes=classes)
        self.max_points = max_points
        self._prices: deque[float] = deque(maxlen=max_points)
        self._style = style
        self._style_list = list(SparklineStyle)

    @property
    def style(self) -> SparklineStyle:
        """Get current sparkline style."""
        return self._style

    @style.setter
    def style(self, value: SparklineStyle) -> None:
        """Set sparkline style and refresh."""
        self._style = value
        self._update_sparkline()

    def cycle_style(self) -> str:
        """Cycle to the next sparkline style. Returns the new style name."""
        current_index = self._style_list.index(self._style)
        next_index = (current_index + 1) % len(self._style_list)
        self._style = self._style_list[next_index]
        self._update_sparkline()
        return self._style.value

    def render(self) -> str:
        """Render the sparkline."""
        if not self.sparkline:
            return "Collecting price data..."
        return self.sparkline

    def add_price(self, price: float) -> None:
        """Add a new price point to the sparkline."""
        self._prices.append(price)
        self._update_sparkline()

    def _update_sparkline(self) -> None:
        """Regenerate the sparkline from current price data."""
        if len(self._prices) < 2:
            self.sparkline = ""
            return

        prices = list(self._prices)
        min_price = min(prices)
        max_price = max(prices)
        price_range = max_price - min_price

        chars = STYLE_CHARS[self._style]

        if price_range == 0:
            # All prices are the same
            mid_char = chars[len(chars) // 2]
            self.sparkline = mid_char * len(prices)
            self.remove_class("trend-up", "trend-down")
            return

        # Map each price to a character
        result = []
        for price in prices:
            # Normalize to 0-1 range
            normalized = (price - min_price) / price_range
            # Map to character index
            index = int(normalized * (len(chars) - 1))
            result.append(chars[index])

        self.sparkline = "".join(result)

        # Update trend class
        self.remove_class("trend-up", "trend-down")
        if prices[-1] > prices[0]:
            self.add_class("trend-up")
        elif prices[-1] < prices[0]:
            self.add_class("trend-down")

    def clear(self) -> None:
        """Clear all price history."""
        self._prices.clear()
        self.sparkline = ""
        self.remove_class("trend-up", "trend-down")

    @property
    def price_count(self) -> int:
        """Number of price points currently stored."""
        return len(self._prices)

    @property
    def trend(self) -> str:
        """Get the current trend direction."""
        if len(self._prices) < 2:
            return "neutral"
        if self._prices[-1] > self._prices[0]:
            return "up"
        elif self._prices[-1] < self._prices[0]:
            return "down"
        return "neutral"
