# Tests

> Pytest test suite for XRP Ticker. Tests run with `pytest` from the project root.

## Patterns

- Test classes grouped by module: `TestPriceData`, `TestWalletData`, `TestSparklineWidget`, etc.
- Class-based organization: `class TestClassName:` with methods `def test_behavior(self):`
- Docstrings on every test method describing the expected behavior
- Shared fixtures in `conftest.py` — use these instead of creating ad-hoc test data
- `pytest-asyncio` with `asyncio_mode = "auto"` — async test functions are detected automatically
- Widget tests that don't require the Textual runtime test formatting/calculation logic directly (no `App` needed)
- Use `pytest.raises(ValueError)` for validation error assertions
- Use `pytest.approx()` for floating-point comparisons

## Available Fixtures (from conftest.py)

| Fixture | Type | Description |
|---------|------|-------------|
| `valid_xrp_address` | `str` | Single valid XRP r-address |
| `valid_xrp_addresses` | `list[str]` | Two valid XRP r-addresses |
| `sample_wallet_config` | `WalletConfig` | Config with one address |
| `sample_display_config` | `DisplayConfig` | Default display settings |
| `sample_connections_config` | `ConnectionsConfig` | Default connection settings |
| `sample_app_config` | `AppConfig` | Full app configuration |
| `sample_price_data` | `PriceData` | XRP price at $2.50 |
| `sample_wallet_data` | `WalletData` | 100 XRP balance |
| `connected_status` | `ServiceStatus` | Connected state |
| `disconnected_status` | `ServiceStatus` | Disconnected state |
| `reconnecting_status` | `ServiceStatus` | Reconnecting with 3 attempts |

## Test File Mapping

| Test File | Covers |
|-----------|--------|
| `test_models.py` | `models.py` — PriceData, WalletData, XRPLAccountInfo, ServiceStatus, ConnectionState |
| `test_config.py` | `config.py` — WalletConfig, DisplayConfig, ConnectionsConfig, AppConfig, TOML loading |
| `test_widgets.py` | `widgets/` — SparklineWidget, formatting logic for MarketStats, PriceDisplay, Portfolio |
| `test_services.py` | `services/` — CoinbaseService, XRPLWebSocketService |
| `test_security.py` | `security.py` — Address validation, input sanitization |
| `test_themes.py` | `themes.py` — Theme definitions, cycling |
| `test_constants.py` | `constants.py` — Format functions, constant values |
| `test_cli.py` | `__main__.py` — CLI argument parsing |
| `test_app.py` | `app.py` — App initialization, bindings |
