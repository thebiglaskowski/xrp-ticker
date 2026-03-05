"""Debug panel widget for XRP Ticker."""

import logging

from textual.app import ComposeResult
from textual.widget import Widget
from textual.widgets import Label

logger = logging.getLogger(__name__)


class DebugPanel(Widget):
    """Debug panel showing connection stats."""

    def __init__(self) -> None:
        super().__init__(id="debug-panel")
        self._price_messages = 0
        self._balance_messages = 0

    def compose(self) -> ComposeResult:
        yield Label("Debug Info", id="debug-title")
        yield Label("Price messages: 0", id="debug-price-count", classes="debug-item")
        yield Label("Balance messages: 0", id="debug-balance-count", classes="debug-item")
        yield Label("Price source: ---", id="debug-price-endpoint", classes="debug-item")
        yield Label("XRPL endpoint: ---", id="debug-xrpl-endpoint", classes="debug-item")

    def increment_price_count(self) -> None:
        """Increment and display the price message counter."""
        self._price_messages += 1
        try:
            self.query_one("#debug-price-count", Label).update(
                f"Price messages: {self._price_messages}"
            )
        except Exception:
            pass  # Widget not yet mounted

    def increment_balance_count(self) -> None:
        """Increment and display the balance message counter."""
        self._balance_messages += 1
        try:
            self.query_one("#debug-balance-count", Label).update(
                f"Balance messages: {self._balance_messages}"
            )
        except Exception:
            pass  # Widget not yet mounted

    def update_endpoints(self, price_source: str = "---", xrpl: str = "---") -> None:
        """Update the endpoint labels in the debug panel."""
        try:
            self.query_one("#debug-price-endpoint", Label).update(
                f"Price: {price_source[:30]}..."
            )
            self.query_one("#debug-xrpl-endpoint", Label).update(f"XRPL: {xrpl[:30]}...")
        except Exception:
            pass  # Widget not yet mounted
