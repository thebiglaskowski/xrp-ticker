"""Main price display widget with animations."""

from textual.app import ComposeResult
from textual.containers import Container
from textual.reactive import reactive
from textual.widget import Widget
from textual.widgets import Label


class PriceDisplayWidget(Widget):
    """Large animated price display showing current XRP price."""

    DEFAULT_CSS = """
    PriceDisplayWidget {
        width: 1fr;
        height: 100%;
    }
    """

    # Reactive attributes
    price: reactive[float | None] = reactive(None)
    price_change: reactive[float] = reactive(0.0)
    price_change_percent: reactive[float] = reactive(0.0)
    is_connected: reactive[bool] = reactive(False)

    def __init__(
        self,
        name: str | None = None,
        id: str | None = None,
        classes: str | None = None,
    ) -> None:
        super().__init__(name=name, id=id, classes=classes)
        self._previous_price: float | None = None

    def compose(self) -> ComposeResult:
        """Create child widgets."""
        with Container(classes="price-container"):
            yield Label(
                "\uede8 XRP/USD • \uf0ec Coinbase", id="source-label", classes="price-source"
            )
            yield Label("---.----", id="price-label", classes="price-value price-large")
            yield Label("", id="change-label", classes="price-change price-neutral")

    def watch_price(self, old_price: float | None, new_price: float | None) -> None:
        """React to price changes with animation."""
        price_label = self.query_one("#price-label", Label)
        container = self.query_one(".price-container", Container)

        if new_price is None:
            price_label.update("Price Unavailable")
            price_label.add_class("price-unavailable")
            return

        price_label.remove_class("price-unavailable")
        price_label.update(f"$ {new_price:,.4f}")

        # Flash animation on price change
        if old_price is not None and old_price != new_price:
            # Remove any existing flash classes
            container.remove_class("flash-up", "flash-down")

            # Add appropriate flash class
            if new_price > old_price:
                container.add_class("flash-up")
            else:
                container.add_class("flash-down")

            # Remove flash after delay
            self.set_timer(0.3, self._remove_flash)

        self._previous_price = new_price

    def _remove_flash(self) -> None:
        """Remove flash animation classes."""
        container = self.query_one(".price-container", Container)
        container.remove_class("flash-up", "flash-down")

    def watch_price_change(self, change: float) -> None:
        """Update the price change display."""
        self._update_change_label()

    def watch_price_change_percent(self, percent: float) -> None:
        """Update the price change percentage display."""
        self._update_change_label()

    def _update_change_label(self) -> None:
        """Update the change label with current values."""
        change_label = self.query_one("#change-label", Label)

        if self.price is None:
            change_label.update("")
            return

        # Determine direction
        if self.price_change > 0:
            arrow = ""
            change_label.remove_class("price-down", "price-neutral")
            change_label.add_class("price-up")
        elif self.price_change < 0:
            arrow = ""
            change_label.remove_class("price-up", "price-neutral")
            change_label.add_class("price-down")
        else:
            arrow = ""
            change_label.remove_class("price-up", "price-down")
            change_label.add_class("price-neutral")

        change_label.update(f"{arrow} {self.price_change:+.4f} ({self.price_change_percent:+.2f}%)")

    def watch_is_connected(self, connected: bool) -> None:
        """React to connection state changes."""
        if not connected and self.price is not None:
            # Keep showing price but indicate it may be stale
            pass

    def update_price_data(
        self,
        price: float,
        price_change: float,
        price_change_percent: float,
    ) -> None:
        """Update all price data at once."""
        self.price = price
        self.price_change = price_change
        self.price_change_percent = price_change_percent
