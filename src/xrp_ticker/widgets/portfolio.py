"""Portfolio display widget showing wallet balance and USD value."""

from textual.app import ComposeResult
from textual.containers import Container
from textual.reactive import reactive
from textual.widget import Widget
from textual.widgets import Label


class PortfolioWidget(Widget):
    """Widget displaying wallet balance and portfolio value."""

    DEFAULT_CSS = """
    PortfolioWidget {
        width: 1fr;
        height: 100%;
    }
    """

    # Reactive attributes
    balance_xrp: reactive[float | None] = reactive(None)
    price_usd: reactive[float | None] = reactive(None)
    portfolio_value: reactive[float | None] = reactive(None)

    def __init__(
        self,
        name: str | None = None,
        id: str | None = None,
        classes: str | None = None,
    ) -> None:
        super().__init__(name=name, id=id, classes=classes)

    def compose(self) -> ComposeResult:
        """Create child widgets."""
        with Container(classes="portfolio-container"):
            yield Label("\uef8d Portfolio • XRPL", classes="portfolio-title")
            yield Label("--- XRP", id="balance-value", classes="balance-value")
            yield Label("$---", id="portfolio-value", classes="portfolio-value-label")

    def watch_balance_xrp(self, balance: float | None) -> None:
        """Update balance display when balance changes."""
        balance_label = self.query_one("#balance-value", Label)

        if balance is None:
            balance_label.update("--- XRP")
            balance_label.add_class("balance-value-unavailable")
        else:
            balance_label.update(f"{balance:,.2f} XRP")
            balance_label.remove_class("balance-value-unavailable")

        self._recalculate_portfolio()

    def watch_price_usd(self, price: float | None) -> None:
        """Update portfolio value when price changes."""
        self._recalculate_portfolio()

    def _recalculate_portfolio(self) -> None:
        """Recalculate and update portfolio value."""
        portfolio_label = self.query_one("#portfolio-value", Label)

        if self.balance_xrp is not None and self.price_usd is not None:
            value = self.balance_xrp * self.price_usd
            self.portfolio_value = value
            portfolio_label.update(f"${value:,.2f} USD")
            portfolio_label.remove_class("balance-value-unavailable")
        elif self.balance_xrp is not None:
            portfolio_label.update("$--- USD")
            portfolio_label.add_class("balance-value-unavailable")
        else:
            portfolio_label.update("$--- USD")
            portfolio_label.add_class("balance-value-unavailable")
            self.portfolio_value = None

    def update_balance(self, balance_xrp: float) -> None:
        """Update the wallet balance."""
        self.balance_xrp = balance_xrp

    def update_price(self, price_usd: float) -> None:
        """Update the current price."""
        self.price_usd = price_usd
