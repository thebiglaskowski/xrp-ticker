"""Status bar widget showing connection status and last update time."""

from datetime import datetime

from textual.app import ComposeResult
from textual.containers import Horizontal
from textual.reactive import reactive
from textual.widget import Widget
from textual.widgets import Label

from ..models import ConnectionState


class StatusIndicator(Label):
    """A single connection status indicator."""

    DEFAULT_CSS = """
    StatusIndicator {
        width: auto;
        margin: 0 2;
    }

    StatusIndicator.connected {
        color: $success;
    }

    StatusIndicator.disconnected {
        color: $error;
    }

    StatusIndicator.reconnecting {
        color: $warning;
    }

    StatusIndicator.failed {
        color: $error;
        text-style: bold;
    }
    """

    state: reactive[ConnectionState] = reactive(ConnectionState.DISCONNECTED)

    def __init__(
        self,
        service_name: str,
        name: str | None = None,
        id: str | None = None,
        classes: str | None = None,
    ) -> None:
        super().__init__(name=name, id=id, classes=classes)
        self._service_name = service_name
        self._reconnect_attempts = 0

    def watch_state(self, state: ConnectionState) -> None:
        """Update display when state changes."""
        # Remove all state classes
        self.remove_class("connected", "disconnected", "reconnecting", "failed")

        # Add appropriate class and update text
        if state == ConnectionState.CONNECTED:
            self.add_class("connected")
            self.update(f"󰄬 {self._service_name}: Connected")
        elif state == ConnectionState.DISCONNECTED:
            self.add_class("disconnected")
            self.update(f"󰅖 {self._service_name}: Disconnected")
        elif state == ConnectionState.RECONNECTING:
            self.add_class("reconnecting")
            if self._reconnect_attempts > 0:
                self.update(f"󰑓 {self._service_name}: Reconnecting ({self._reconnect_attempts})")
            else:
                self.update(f"󰑓 {self._service_name}: Reconnecting...")
        elif state == ConnectionState.FAILED:
            self.add_class("failed")
            self.update(f"󰅜 {self._service_name}: Failed")

    def update_state(self, state: ConnectionState, reconnect_attempts: int = 0) -> None:
        """Update the indicator state."""
        self._reconnect_attempts = reconnect_attempts
        self.state = state


class StatusBarWidget(Widget):
    """Status bar showing connection indicators and last update time."""

    DEFAULT_CSS = """
    StatusBarWidget {
        dock: bottom;
        width: 100%;
        height: 1;
        background: $surface;
        border-top: solid $primary-darken-2;
    }

    StatusBarWidget Horizontal {
        width: 100%;
        height: 100%;
        align: center middle;
    }

    StatusBarWidget .status-time {
        width: auto;
        margin-left: 2;
        color: $text-muted;
    }

    StatusBarWidget .status-spacer {
        width: 1fr;
    }
    """

    last_update: reactive[datetime | None] = reactive(None)

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
            yield StatusIndicator("Coinbase", id="price-status")
            yield StatusIndicator("XRPL", id="xrpl-status")
            yield Label("", classes="status-spacer")
            yield Label("Updated: --:--:--", id="update-time", classes="status-time")

    def watch_last_update(self, update_time: datetime | None) -> None:
        """Update the time display when last_update changes."""
        time_label = self.query_one("#update-time", Label)

        if update_time is None:
            time_label.update("Updated: --:--:--")
        else:
            time_label.update(f"Updated: {update_time.strftime('%H:%M:%S')}")

    def update_price_status(self, state: ConnectionState, reconnect_attempts: int = 0) -> None:
        """Update price service connection status."""
        indicator = self.query_one("#price-status", StatusIndicator)
        indicator.update_state(state, reconnect_attempts)

    def update_xrpl_status(self, state: ConnectionState, reconnect_attempts: int = 0) -> None:
        """Update XRPL connection status."""
        indicator = self.query_one("#xrpl-status", StatusIndicator)
        indicator.update_state(state, reconnect_attempts)

    def set_update_time(self, time: datetime | None = None) -> None:
        """Set the last update time."""
        self.last_update = time or datetime.now()
