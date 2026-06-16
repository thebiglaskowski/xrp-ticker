# Widgets

> Textual widgets for the XRP Ticker TUI. Each widget is a self-contained display component with reactive data binding.

## Patterns

All widgets in this directory follow these conventions:

- Inherit from `textual.widget.Widget` (not `Static`)
- Use `reactive` attributes for data that drives display updates
- Implement `watch_*` methods to react to reactive attribute changes
- Provide a public `update_*` method as the external API for pushing data in
- Include `DEFAULT_CSS` as a class-level string for baseline sizing/layout
- Accept `name`, `id`, `classes` constructor params and forward to `super().__init__()`
- Use CSS classes (not inline styles) for visual state: `flash-up`, `flash-down`, `price-up`, `price-down`, `price-neutral`, `trend-up`, `trend-down`, `visible`
- Query child elements with `self.query_one("#id", WidgetType)` — wrap in try/except for calls that may fire before mount

## Widget Inventory

| Widget | File | Purpose | Key Reactives |
|--------|------|---------|---------------|
| `PriceDisplayWidget` | `price_display.py` | Large animated XRP price | `price`, `price_change`, `price_change_percent`, `is_connected` |
| `MarketStatsWidget` | `market_stats.py` | 24h high/low/volume/change | Updated via `update_from_price_data()` |
| `SparklineWidget` | `sparkline.py` | Unicode sparkline chart | `sparkline` (rendered string) |
| `PortfolioWidget` | `portfolio.py` | Wallet balance + USD value | Updated via `update_balance()`, `update_price()` |
| `StatusBarWidget` | `status_bar.py` | Connection status indicators | Updated via `update_price_status()`, `update_xrpl_status()` |

## Adding a New Widget

1. Create `src/xrp_ticker/widgets/your_widget.py`
2. Subclass `Widget`, add `DEFAULT_CSS`, define reactive attributes
3. Implement `compose()` returning child `Label`/`Container` elements
4. Add `watch_*` methods for each reactive
5. Export from `__init__.py`
6. Add to layout in `app.py` `compose()` method
7. Wire data flow from service callbacks in `app.py`
