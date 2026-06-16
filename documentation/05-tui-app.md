---
feature: TUI Application
version: "1.0"
last_updated: 2026-03-05
dependencies:
  - "01-configuration.md"
  - "03-price-feed.md"
  - "04-xrpl-balance.md"
  - "07-themes.md"
  - "08-widgets.md"
status: stable
---

# TUI Application

> `XRPTickerApp` is the main Textual `App` subclass. It owns the service lifecycle,
> wires data callbacks to widgets, manages theme cycling, and exposes keyboard bindings.

## Layout

```
[header-title]           -- Label: " XRP TICKER"

[main-content]           -- Vertical container
  [top-row]              -- Horizontal container
    [price-display]      -- PriceDisplayWidget (1fr width)
    [portfolio]          -- PortfolioWidget (1fr width)
  [market-stats]         -- MarketStatsWidget
  [sparkline]            -- SparklineWidget (max_points=60)

[debug-panel]            -- DebugPanel (hidden by default, CSS class "visible" toggles)
[status-bar]             -- StatusBarWidget
```

## Keyboard Bindings

| Key | Action | Description |
|-----|--------|-------------|
| `q` | quit | Exit application (priority=True) |
| `r` | refresh | Restart both services, clear sparkline |
| `t` | cycle_theme | Advance to next theme in cycle |
| `s` | cycle_sparkline | Cycle sparkline chart style |
| `?` | help | Push HelpScreen modal |
| `d` | toggle_debug | Toggle debug panel visibility |
| `Esc` | dismiss (in HelpScreen) | Close help modal |

## Service Wiring (Data Flow)

```
CoinbaseService.on_price_update --> _handle_price_update()
  -> PriceDisplayWidget.update_price_data(price, price_change, price_change_percent)
  -> PriceDisplayWidget.is_connected = True
  -> MarketStatsWidget.update_from_price_data(...)
  -> SparklineWidget.add_price(price)
  -> PortfolioWidget.update_price(price)
  -> StatusBarWidget.set_update_time(timestamp)
  -> DebugPanel.increment_price_count()

CoinbaseService.on_status_change --> _handle_price_status()
  -> StatusBarWidget.update_price_status(state, reconnect_attempts)
  -> PriceDisplayWidget.is_connected = status.is_connected
  -> notify() on CONNECTED or FAILED

XRPLWebSocketService.on_balance_update --> _handle_balance_update()
  -> PortfolioWidget.update_balance(balance_xrp)
  -> DebugPanel.increment_balance_count()
  -> DebugPanel.update_endpoints(price_source, xrpl)

XRPLWebSocketService.on_status_change --> _handle_xrpl_status()
  -> StatusBarWidget.update_xrpl_status(state, reconnect_attempts)
  -> notify() on CONNECTED or FAILED
```

## Lifecycle

**on_mount():**
1. Creates `CoinbaseService` with price/status callbacks
2. Creates `XRPLWebSocketService` with config addresses, endpoints, poll_interval, balance/status callbacks
3. Updates debug panel with initial endpoint info
4. Calls `await service.start()` for both services

**on_unmount():**
1. Clears both services' callbacks (sets to `None`) before stopping
2. Calls `await service.stop()` for both services

**Callback clearing is required** to prevent callbacks firing on widgets that are being torn down.

## Theme Cycling

- Themes are listed in `THEME_NAMES = ["ripple", "monokai", "cyberpunk"]`
- `_current_theme_index` tracks position in the list
- `_apply_theme(name)` removes all `theme-*` CSS classes from the screen, then adds `theme-{name}`
- `get_next_theme(current)` wraps around at end of list

## Debug Panel

Hidden by default (`DebugPanel` without CSS class `visible`). Toggled with `d`. Displays:
- Price message count
- Balance message count
- Price data source (first 30 chars)
- XRPL endpoint in use (first 30 chars)

The debug panel is not connected to reactive attributes; it uses direct `Label.update()` calls and catches exceptions from pre-mount queries.

## Notifications

| Event | Severity | Timeout |
|-------|----------|---------|
| Coinbase connected | information | 2s |
| Coinbase connection failed | error | persistent |
| XRPL connected | information | 2s |
| XRPL connection failed | error | persistent |
| Theme changed | information (implicit) | 2s |
| Refreshing connections | information | 2s |
| Chart style changed | information (implicit) | 2s |

## Business Rules

- **CSS loaded from file:** `src/xrp_ticker/styles/app.tcss` (not embedded in Python)
- **Refresh resets sparkline:** `action_refresh()` calls `SparklineWidget.clear()` after restarting services
- **Services initialized at mount, not in `__init__`:** `_price_service` and `_xrpl_service` are `None` until `on_mount()` runs
