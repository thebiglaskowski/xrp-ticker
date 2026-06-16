# XRP Ticker

> A modern terminal-based XRP portfolio tracker with real-time price updates and wallet balance monitoring. Built with Python and the Textual TUI framework.

## Quality Philosophy

- Fix every error you encounter, regardless of who introduced it
- Never label issues as "pre-existing" or "out of scope"
- Quality gates must pass with ZERO errors, not "zero new errors"
- The goal is a perfect codebase, not just "didn't make it worse"
- Solve root causes, never apply workarounds or quick fixes
- If you cannot fix something, explain why and propose alternatives — don't dismiss it
- Admit mistakes immediately — "I made a mistake" not "there was an issue"

## Tech Stack

| Technology | Purpose |
|-----------|---------|
| Python 3.11+ | Language |
| Textual | TUI framework |
| Pydantic 2.x | Data models and validation |
| httpx | HTTP client (Coinbase REST API) |
| websockets | XRPL WebSocket client |
| Ruff | Linter and formatter |
| Pytest | Testing (with pytest-asyncio) |
| Hatchling | Build system |

## Architecture

```
src/xrp_ticker/
    __init__.py          # Package init, exports APP_NAME/APP_VERSION
    __main__.py          # CLI entry point (argparse)
    app.py               # Main Textual App (XRPTickerApp)
    config.py            # TOML config loading (Pydantic models)
    constants.py         # All constants, icons, format functions
    models.py            # Pydantic data models (PriceData, WalletData, etc.)
    security.py          # Security validation (address patterns, sanitization)
    themes.py            # Theme definitions (ripple, monokai)
    services/
        coinbase.py      # Coinbase REST API polling service
        xrpl_ws.py       # XRPL WebSocket client with auto-reconnect
    widgets/
        price_display.py # Large animated price display
        market_stats.py  # 24h market statistics
        sparkline.py     # Unicode sparkline chart
        portfolio.py     # Wallet balance and portfolio value
        status_bar.py    # Connection status indicators
    styles/
        app.tcss         # Textual CSS styles
tests/                   # Pytest test suite
config.toml.example      # Example configuration
```

## Commands

```bash
# Install (editable + dev deps)
pip install -e ".[dev]"

# Run the app
xrp-ticker
xrp-ticker -w rYourAddress     # with wallet address
xrp-ticker -d                  # debug mode
xrp-ticker --init rAddress     # create config file

# Lint
ruff check src/
ruff check src/ --fix           # auto-fix

# Format
ruff format src/

# Test
pytest
pytest tests/test_models.py     # single file
pytest -x                       # stop on first failure
```

## Code Standards

Ruff configuration (from `pyproject.toml`):
- Line length: 100
- Target: Python 3.11
- Rules: E (pycodestyle errors), F (pyflakes), I (isort), N (pep8-naming), W (warnings), UP (pyupgrade)

Conventions observed in this codebase:
- Type hints on all function signatures using `|` union syntax (not `Optional`)
- `typing.Final` for constants
- Pydantic `BaseModel` for all data structures with `Field()` descriptors and validators
- `str` enums for states (`ConnectionState(str, Enum)`)
- Callback-based service pattern: services accept `on_*` callbacks, not event emitters
- Logging via `logging.getLogger(__name__)` in every module
- Docstrings on all classes and public methods (single-line or first-line summary)

## Configuration

TOML-based config loaded from (in order):
1. `./config.toml`
2. `~/.config/xrp-ticker/config.toml`
3. `$XDG_CONFIG_HOME/xrp-ticker/config.toml`

Sections: `[wallet]` (addresses list), `[display]` (theme, refresh rate), `[connections]` (XRPL endpoints, polling interval, timeouts, retries)

XRPL endpoints are validated against a trusted allowlist in `config.py`. Only `wss://` schemes are allowed.

## Key Patterns

**Service lifecycle:** Services (`CoinbaseService`, `XRPLWebSocketService`) follow `start()` → callbacks fire → `stop()` / `restart()`. The app clears callbacks before stopping to prevent errors during shutdown.

**Widget reactivity:** Widgets use Textual's `reactive` attributes. Changes trigger `watch_*` methods automatically. CSS classes (`flash-up`, `flash-down`, `trend-up`, `trend-down`) drive visual feedback.

**Theme switching:** Themes are applied via CSS classes on the screen (`theme-ripple`, `theme-monokai`), toggled by adding/removing classes.

**Constants centralization:** All magic numbers, icons, format strings, and error messages live in `constants.py`. Format helper functions (`format_price`, `format_volume`, etc.) are also there.

## Environment Variables

| Variable | Purpose |
|----------|---------|
| `XRP_TICKER_DEBUG` | Enable debug logging (`1`, `true`, `yes`) |
| `XDG_CONFIG_HOME` | Override config file search path |
