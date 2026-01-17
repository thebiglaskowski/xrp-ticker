"""Market statistics widget showing 24h high/low and volume."""

from textual.app import ComposeResult
from textual.containers import Horizontal
from textual.reactive import reactive
from textual.widget import Widget
from textual.widgets import Label, Static


class StatBox(Static):
    """A compact stat display box."""

    DEFAULT_CSS = """
    StatBox {
        width: 1fr;
        height: auto;
        padding: 0 1;
        margin: 0;
        min-width: 12;
    }

    StatBox .stat-label {
        color: $text-muted;
        height: 1;
    }

    StatBox .stat-value {
        text-style: bold;
        height: 1;
    }
    """

    def __init__(
        self,
        label: str,
        value: str = "---",
        value_class: str = "",
        name: str | None = None,
        id: str | None = None,
        classes: str | None = None,
    ) -> None:
        super().__init__(name=name, id=id, classes=classes)
        self._label = label
        self._value = value
        self._value_class = value_class

    def compose(self) -> ComposeResult:
        """Create child widgets."""
        yield Label(self._label, classes="stat-label")
        yield Label(self._value, id="stat-value", classes=f"stat-value {self._value_class}")

    def update_value(self, value: str, value_class: str = "") -> None:
        """Update the displayed value."""
        value_label = self.query_one("#stat-value", Label)
        value_label.update(value)
        # Update class for coloring
        value_label.remove_class("market-stat-high", "market-stat-low")
        if value_class:
            value_label.add_class(value_class)


class MarketStatsWidget(Widget):
    """Widget displaying market statistics: 24h high/low, change %, volume."""

    DEFAULT_CSS = """
    MarketStatsWidget {
        width: 100%;
        height: auto;
        padding: 0;
    }

    MarketStatsWidget Horizontal {
        width: 100%;
        height: auto;
        align: center middle;
    }
    """

    # Reactive attributes for 24h data from API
    high_24h: reactive[float | None] = reactive(None)
    low_24h: reactive[float | None] = reactive(None)
    volume_24h: reactive[float | None] = reactive(None)
    current_price: reactive[float | None] = reactive(None)
    price_change_percent: reactive[float] = reactive(0.0)

    def __init__(
        self,
        name: str | None = None,
        id: str | None = None,
        classes: str | None = None,
    ) -> None:
        super().__init__(name=name, id=id, classes=classes)

    def compose(self) -> ComposeResult:
        """Create child widgets."""
        with Horizontal():
            yield StatBox(
                "󰁝 24h High", "---", "market-stat-high",
                id="stat-high", classes="market-stat"
            )
            yield StatBox(
                "󰁅 24h Low", "---", "market-stat-low",
                id="stat-low", classes="market-stat"
            )
            yield StatBox(
                "󰘦 24h Change", "---", "",
                id="stat-change", classes="market-stat"
            )
            yield StatBox(
                "󰁨 24h Volume", "---", "",
                id="stat-volume", classes="market-stat"
            )

    def watch_high_24h(self, high: float | None) -> None:
        """Update high display."""
        stat_box = self.query_one("#stat-high", StatBox)
        if high is not None:
            stat_box.update_value(f"${high:.4f}", "market-stat-high")
        else:
            stat_box.update_value("---")

    def watch_low_24h(self, low: float | None) -> None:
        """Update low display."""
        stat_box = self.query_one("#stat-low", StatBox)
        if low is not None:
            stat_box.update_value(f"${low:.4f}", "market-stat-low")
        else:
            stat_box.update_value("---")

    def watch_price_change_percent(self, percent: float) -> None:
        """Update change % display."""
        stat_box = self.query_one("#stat-change", StatBox)
        if percent > 0:
            stat_box.update_value(f"+{percent:.2f}%", "market-stat-high")
        elif percent < 0:
            stat_box.update_value(f"{percent:.2f}%", "market-stat-low")
        else:
            stat_box.update_value("0.00%", "")

    def watch_volume_24h(self, volume: float | None) -> None:
        """Update volume display."""
        stat_box = self.query_one("#stat-volume", StatBox)
        if volume is not None:
            # Format volume with K/M suffixes
            if volume >= 1_000_000:
                stat_box.update_value(f"{volume / 1_000_000:.2f}M XRP")
            elif volume >= 1_000:
                stat_box.update_value(f"{volume / 1_000:.1f}K XRP")
            else:
                stat_box.update_value(f"{volume:.0f} XRP")
        else:
            stat_box.update_value("---")

    def update_from_price_data(
        self,
        price: float,
        change_percent: float,
        high_24h: float | None = None,
        low_24h: float | None = None,
        volume: float | None = None,
    ) -> None:
        """Update all stats from price data."""
        self.current_price = price
        self.price_change_percent = change_percent
        self.high_24h = high_24h
        self.low_24h = low_24h
        self.volume_24h = volume

    def reset_session(self) -> None:
        """Reset statistics (kept for compatibility)."""
        # No longer tracking session data, but keep method for refresh action
        pass
