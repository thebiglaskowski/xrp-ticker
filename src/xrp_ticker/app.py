"""Main Textual application for XRP Ticker."""

import logging
from pathlib import Path

from textual.app import App, ComposeResult
from textual.binding import Binding
from textual.containers import Container, Horizontal, Vertical
from textual.screen import ModalScreen
from textual.widgets import Label, Static

from .config import AppConfig
from .models import ConnectionState, PriceData, ServiceStatus, WalletData
from .services import CoinbaseService, XRPLWebSocketService
from .widgets import (
    MarketStatsWidget,
    PortfolioWidget,
    PriceDisplayWidget,
    SparklineWidget,
    StatusBarWidget,
)

logger = logging.getLogger(__name__)

# Path to CSS file
CSS_PATH = Path(__file__).parent / "styles" / "app.tcss"


class HelpScreen(ModalScreen):
    """Help overlay showing keyboard shortcuts."""

    BINDINGS = [
        Binding("escape", "dismiss", "Close"),
        Binding("?", "dismiss", "Close"),
    ]

    def compose(self) -> ComposeResult:
        with Container(id="help-overlay"):
            with Vertical(id="help-content"):
                yield Label("XRP Ticker Help", id="help-title")
                yield Label("")
                yield Label("[cyan]q[/cyan]        Quit application", markup=True)
                yield Label("[cyan]r[/cyan]        Refresh connections", markup=True)
                yield Label("[cyan]t[/cyan]        Cycle theme", markup=True)
                yield Label("[cyan]s[/cyan]        Cycle chart style", markup=True)
                yield Label("[cyan]d[/cyan]        Toggle debug panel", markup=True)
                yield Label("[cyan]?[/cyan]        Show this help", markup=True)
                yield Label("[cyan]Esc[/cyan]      Close overlay", markup=True)
                yield Label("")
                yield Label("Press any key to close", classes="help-desc")


class DebugPanel(Static):
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
        self._price_messages += 1
        self.query_one("#debug-price-count", Label).update(
            f"Price messages: {self._price_messages}"
        )

    def increment_balance_count(self) -> None:
        self._balance_messages += 1
        self.query_one("#debug-balance-count", Label).update(
            f"Balance messages: {self._balance_messages}"
        )

    def update_endpoints(self, price_source: str = "---", xrpl: str = "---") -> None:
        self.query_one("#debug-price-endpoint", Label).update(
            f"Price: {price_source[:30]}..."
        )
        self.query_one("#debug-xrpl-endpoint", Label).update(
            f"XRPL: {xrpl[:30]}..."
        )


class XRPTickerApp(App):
    """Main XRP Ticker application."""

    TITLE = "XRP Ticker"
    CSS_PATH = CSS_PATH

    BINDINGS = [
        Binding("q", "quit", "Quit", priority=True),
        Binding("r", "refresh", "Refresh"),
        Binding("t", "cycle_theme", "Theme"),
        Binding("s", "cycle_sparkline", "Chart Style"),
        Binding("question_mark", "help", "Help"),
        Binding("d", "toggle_debug", "Debug"),
    ]

    # Available themes
    THEMES = ["ripple", "monokai"]

    def __init__(
        self,
        config: AppConfig,
        **kwargs,
    ) -> None:
        super().__init__(**kwargs)
        self.config = config
        self._price_service: CoinbaseService | None = None
        self._xrpl_service: XRPLWebSocketService | None = None
        self._debug_visible = False
        self._current_theme_index = 0

    def compose(self) -> ComposeResult:
        """Create the application layout."""
        # Simple header
        yield Label("\uf155 XRP TICKER", id="header-title")

        # Main content
        with Vertical(id="main-content"):
            # Top row: Price and Portfolio side by side
            with Horizontal(id="top-row"):
                yield PriceDisplayWidget(id="price-display")
                yield PortfolioWidget(id="portfolio")
            # Bottom section: Stats and sparkline
            yield MarketStatsWidget(id="market-stats")
            yield SparklineWidget(max_points=60, id="sparkline")

        # Debug panel (hidden by default)
        yield DebugPanel()

        # Status bar
        yield StatusBarWidget(id="status-bar")

    async def on_mount(self) -> None:
        """Initialize services when the app mounts."""
        logger.info("XRP Ticker starting...")

        # Initialize price service (Coinbase - works in US)
        self._price_service = CoinbaseService(
            on_price_update=self._handle_price_update,
            on_status_change=self._handle_price_status,
        )

        # Initialize XRPL service
        self._xrpl_service = XRPLWebSocketService(
            wallet_address=self.config.wallet.address,
            endpoints=self.config.connections.xrpl_endpoints,
            poll_interval=self.config.connections.xrpl_poll_interval,
            on_balance_update=self._handle_balance_update,
            on_status_change=self._handle_xrpl_status,
        )

        # Update debug panel with endpoints
        debug_panel = self.query_one(DebugPanel)
        debug_panel.update_endpoints(
            price_source="Coinbase API",
            xrpl=self.config.connections.xrpl_endpoints[0],
        )

        # Start services
        await self._price_service.start()
        await self._xrpl_service.start()

    async def on_unmount(self) -> None:
        """Cleanup services when the app unmounts."""
        logger.info("XRP Ticker shutting down...")

        # Clear callbacks before stopping to avoid errors during shutdown
        if self._price_service:
            self._price_service.on_price_update = None
            self._price_service.on_status_change = None
            await self._price_service.stop()

        if self._xrpl_service:
            self._xrpl_service.on_balance_update = None
            self._xrpl_service.on_status_change = None
            await self._xrpl_service.stop()

    def _handle_price_update(self, price_data: PriceData) -> None:
        """Handle incoming price data from Coinbase."""
        # Update price display
        price_display = self.query_one("#price-display", PriceDisplayWidget)
        price_display.update_price_data(
            price=price_data.price,
            price_change=price_data.price_change,
            price_change_percent=price_data.price_change_percent,
        )
        price_display.is_connected = True

        # Update market stats (24h high/low/volume from API)
        market_stats = self.query_one("#market-stats", MarketStatsWidget)
        market_stats.update_from_price_data(
            price=price_data.price,
            change_percent=price_data.price_change_percent,
            high_24h=price_data.high_24h,
            low_24h=price_data.low_24h,
            volume=price_data.volume,
        )

        # Update sparkline
        sparkline = self.query_one("#sparkline", SparklineWidget)
        sparkline.add_price(price_data.price)

        # Update portfolio with new price
        portfolio = self.query_one("#portfolio", PortfolioWidget)
        portfolio.update_price(price_data.price)

        # Update status bar time
        status_bar = self.query_one("#status-bar", StatusBarWidget)
        status_bar.set_update_time(price_data.timestamp)

        # Update debug panel
        debug_panel = self.query_one(DebugPanel)
        debug_panel.increment_price_count()

    def _handle_balance_update(self, wallet_data: WalletData) -> None:
        """Handle incoming wallet balance from XRPL."""
        # Update portfolio
        portfolio = self.query_one("#portfolio", PortfolioWidget)
        portfolio.update_balance(wallet_data.balance_xrp)

        # Update debug panel
        debug_panel = self.query_one(DebugPanel)
        debug_panel.increment_balance_count()
        debug_panel.update_endpoints(
            price_source="Coinbase API",
            xrpl=wallet_data.source,
        )

    def _handle_price_status(self, status: ServiceStatus) -> None:
        """Handle price service status changes."""
        status_bar = self.query_one("#status-bar", StatusBarWidget)
        status_bar.update_price_status(status.state, status.reconnect_attempts)

        # Update price display connection state
        price_display = self.query_one("#price-display", PriceDisplayWidget)
        price_display.is_connected = status.is_connected

        if status.state == ConnectionState.CONNECTED:
            self.notify("Coinbase connected", severity="information", timeout=2)
        elif status.state == ConnectionState.FAILED:
            self.notify(f"Coinbase connection failed: {status.error_message}", severity="error")

    def _handle_xrpl_status(self, status: ServiceStatus) -> None:
        """Handle XRPL service status changes."""
        status_bar = self.query_one("#status-bar", StatusBarWidget)
        status_bar.update_xrpl_status(status.state, status.reconnect_attempts)

        if status.state == ConnectionState.CONNECTED:
            self.notify("XRPL connected", severity="information", timeout=2)
        elif status.state == ConnectionState.FAILED:
            self.notify(f"XRPL connection failed: {status.error_message}", severity="error")

    async def action_refresh(self) -> None:
        """Refresh all connections."""
        self.notify("Refreshing connections...", timeout=2)

        if self._price_service:
            await self._price_service.restart()

        if self._xrpl_service:
            await self._xrpl_service.restart()

        # Clear sparkline
        sparkline = self.query_one("#sparkline", SparklineWidget)
        sparkline.clear()

        # Reset market stats session data
        market_stats = self.query_one("#market-stats", MarketStatsWidget)
        market_stats.reset_session()

    def action_cycle_theme(self) -> None:
        """Cycle through available themes."""
        self._current_theme_index = (self._current_theme_index + 1) % len(self.THEMES)
        theme_name = self.THEMES[self._current_theme_index]
        self._apply_theme(theme_name)
        self.notify(f"Theme: {theme_name.title()}", timeout=2)

    def _apply_theme(self, theme_name: str) -> None:
        """Apply the specified theme by adding/removing CSS classes."""
        screen = self.screen
        # Remove all theme classes
        for theme in self.THEMES:
            screen.remove_class(f"theme-{theme}")
        # Add the new theme class
        screen.add_class(f"theme-{theme_name}")

    def action_cycle_sparkline(self) -> None:
        """Cycle through sparkline chart styles."""
        sparkline = self.query_one("#sparkline", SparklineWidget)
        new_style = sparkline.cycle_style()
        self.notify(f"Chart style: {new_style.title()}", timeout=2)

    def action_help(self) -> None:
        """Show the help overlay."""
        self.push_screen(HelpScreen())

    def action_toggle_debug(self) -> None:
        """Toggle the debug panel visibility."""
        debug_panel = self.query_one("#debug-panel", DebugPanel)
        self._debug_visible = not self._debug_visible

        if self._debug_visible:
            debug_panel.add_class("visible")
        else:
            debug_panel.remove_class("visible")
