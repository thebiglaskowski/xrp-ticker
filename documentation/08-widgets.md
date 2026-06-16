---
feature: Widgets
version: "1.0"
last_updated: 2026-03-05
dependencies:
  - "03-price-feed.md"
  - "04-xrpl-balance.md"
  - "07-themes.md"
status: stable
---

# Widgets

> Five Textual Widget subclasses that compose the TUI layout. All are data-in /
> display-out: they expose public update methods, use reactive attributes internally,
> and fire watch_* methods to update DOM labels.

## Widget Conventions (All Widgets)

- Subclass `textual.widget.Widget` (not `Static`)
- Use `reactive` attributes for data driving display
- `watch_*` methods react to reactive changes (called automatically by Textual)
- Public `update_*` methods are the external API (called by `XRPTickerApp`)
- `DEFAULT_CSS` class attribute handles baseline sizing/layout
- Constructor accepts `name`, `id`, `classes` forwarded to `super().__init__()`
- CSS classes (not inline styles) for visual states: `flash-up`, `flash-down`, `price-up`, `price-down`, `price-neutral`, `trend-up`, `trend-down`, `visible`
- `query_one("#id", WidgetType)` wrapped in try/except for pre-mount safety

---

## PriceDisplayWidget

**File:** `widgets/price_display.py`
**Purpose:** Large animated price display for XRP/USD.

### Reactive Attributes

| Attribute | Type | Default | Effect |
|-----------|------|---------|--------|
| `price` | `float \| None` | `None` | Triggers `watch_price()`, updates label, triggers flash animation |
| `price_change` | `float` | `0.0` | Triggers `watch_price_change()`, updates change label |
| `price_change_percent` | `float` | `0.0` | Triggers `watch_price_change_percent()`, updates change label |
| `is_connected` | `bool` | `False` | Used for display state (connected vs. disconnected) |

### Public API

`update_price_data(price, price_change, price_change_percent)` — sets all three price reactives at once.

### Flash Animation

On each price change (when old price is not None and differs from new):
- Adds CSS class `flash-up` or `flash-down` to `.price-container`
- Timer fires after 0.3 seconds to remove flash class via `_remove_flash()`

### DOM Elements

| ID | Type | Content |
|----|------|---------|
| `#source-label` | Label | " XRP/USD •  Coinbase" (Nerd Font icons) |
| `#price-label` | Label | `"$ {price:,.4f}"` or `"---.----"` or `"Price Unavailable"` |
| `#change-label` | Label | `"arrow {change:+.4f} ({percent:+.2f}%)"` |

---

## PortfolioWidget

**File:** `widgets/portfolio.py`
**Purpose:** Wallet XRP balance and USD portfolio value.

### Reactive Attributes

| Attribute | Type | Default | Effect |
|-----------|------|---------|--------|
| `balance_xrp` | `float \| None` | `None` | Triggers balance label update, recalculates value |
| `price_usd` | `float \| None` | `None` | Triggers portfolio value recalculation |
| `portfolio_value` | `float \| None` | `None` | Updated internally by `_recalculate_portfolio()` |

### Portfolio Value Calculation

`portfolio_value = balance_xrp * price_usd`

Shows `$--- USD` if either value is missing.

### Public API

- `update_balance(balance_xrp: float)` — sets `self.balance_xrp`
- `update_price(price_usd: float)` — sets `self.price_usd`

### DOM Elements

| ID | Type | Content |
|----|------|---------|
| `.portfolio-title` | Label | " Portfolio • XRPL" |
| `#balance-value` | Label | `"{balance:,.2f} XRP"` or `"--- XRP"` |
| `#portfolio-value` | Label | `"${value:,.2f} USD"` or `"$--- USD"` |

---

## MarketStatsWidget

**File:** `widgets/market_stats.py`
**Purpose:** 24h market statistics: high, low, volume, percent change.

### Public API

`update_from_price_data(price, change_percent, high_24h, low_24h, volume)` — updates all stats labels directly (no reactive attributes; direct DOM mutation).

---

## SparklineWidget

**File:** `widgets/sparkline.py`
**Purpose:** Unicode sparkline chart of recent prices.

### Reactive Attributes

| Attribute | Type | Effect |
|-----------|------|--------|
| `sparkline` | `str` | Rendered unicode sparkline string, updates display label |

### Public API

- `add_price(price: float)` — appends to internal history, recomputes sparkline
- `clear()` — resets price history (called on `action_refresh` in app)
- `cycle_style() -> str` — cycles through chart styles, returns new style name

### Constructor

`SparklineWidget(max_points=60, ...)` — rolling window size. Default is 60 data points.

---

## StatusBarWidget

**File:** `widgets/status_bar.py`
**Purpose:** Connection status indicators for Coinbase and XRPL services.

### Public API

- `update_price_status(state: ConnectionState, reconnect_attempts: int)` — updates Coinbase status
- `update_xrpl_status(state: ConnectionState, reconnect_attempts: int)` — updates XRPL status
- `set_update_time(timestamp: datetime)` — updates last-update timestamp display

### Status Display

Uses `ICONS` dict from `constants.py` for Nerd Font icons per state:
- `connected` → checkmark icon, green
- `disconnected` → X icon, dim
- `reconnecting` → refresh icon, yellow, shows attempt count
- `failed` → error icon, red

---

## Business Rules (All Widgets)

- **No direct service access:** Widgets never import or reference services. All data arrives via the app's callback-to-update_method wiring.
- **No side effects in watch_* methods:** Watch methods only update display; they do not emit events or modify other widgets.
- **Pre-mount safety:** Any widget method that might be called before `on_mount` wraps `query_one()` in try/except to avoid `NoMatches` errors.
- **CSS class state machine:** Visual states (connected, flash, trend) are expressed via CSS class add/remove, not style mutations.
