---
feature: Configuration
version: "1.0"
last_updated: 2026-03-05
dependencies: []
status: stable
---

# Configuration

> TOML-based configuration system using Pydantic models for validation. Searches standard
> OS locations for the config file, supports multi-wallet setups, and enforces security
> constraints at load time.

## Data Model

### WalletConfig

| Field | Type | Constraints | Notes |
|-------|------|-------------|-------|
| `addresses` | `list[str]` | Each: starts with `r`, 25-35 chars, base58 | XRP wallet r-addresses |

**Backward compatibility:** Legacy `address` (singular) field is auto-converted to `addresses` list. A single string value for `addresses` is also accepted and wrapped in a list.

**Validation:** Each address is validated against `XRP_ADDRESS_PATTERN = r"^r[1-9A-HJ-NP-Za-km-z]{24,34}$"`. Characters `0`, `O`, `I`, `l` are excluded (base58).

### DisplayConfig

| Field | Type | Constraints | Default | Notes |
|-------|------|-------------|---------|-------|
| `refresh_rate` | `float` | 0.1 - 5.0 | 0.5 | Seconds between UI refreshes |
| `sparkline_minutes` | `int` | 5 - 1440 | 60 | Historical window for sparkline chart |
| `theme` | `str` | any | `"cyberpunk"` | Must match a key in `THEMES` dict |

### ConnectionsConfig

| Field | Type | Constraints | Default | Notes |
|-------|------|-------------|---------|-------|
| `xrpl_endpoints` | `list[str]` | wss:// only, trusted allowlist | 4 defaults | Priority-ordered XRPL WebSocket endpoints |
| `xrpl_poll_interval` | `int` | 10 - 300 | 30 | Seconds between XRPL balance checks |
| `request_timeout` | `float` | 5.0 - 60.0 | 30.0 | HTTP/WebSocket request timeout |
| `connection_timeout` | `float` | 1.0 - 30.0 | 10.0 | Connection establishment timeout |
| `max_retries` | `int` | 0 - 10 | 3 | Max retry attempts before failing |
| `retry_backoff_base` | `float` | 0.5 - 5.0 | 1.0 | Base delay for exponential backoff |
| `retry_backoff_max` | `float` | 10.0 - 300.0 | 60.0 | Maximum backoff delay cap |

### AppConfig

| Field | Type | Notes |
|-------|------|-------|
| `wallet` | `WalletConfig` | Required |
| `display` | `DisplayConfig` | Optional, defaults applied |
| `connections` | `ConnectionsConfig` | Optional, defaults applied |

## Trusted XRPL Endpoints Allowlist

Only these endpoints are accepted in `xrpl_endpoints`. Any other value causes a `ValueError` at config load time:

```
wss://xrplcluster.com
wss://s1.ripple.com
wss://s2.ripple.com
wss://xrpl.ws
```

**Security rule:** Only `wss://` scheme is allowed. `ws://` is rejected.

## Config File Format

```toml
[wallet]
addresses = ["rYourAddress1", "rYourAddress2"]

[display]
refresh_rate = 0.5
sparkline_minutes = 60
theme = "ripple"

[connections]
xrpl_poll_interval = 30
```

## Config File Search Order

`find_config_file()` searches in this priority order, returning the first match:
1. `./config.toml` (current working directory)
2. `$XDG_CONFIG_HOME/xrp-ticker/config.toml` (if `XDG_CONFIG_HOME` env var is set)
3. `~/.config/xrp-ticker/config.toml`

## Business Rules

- **Max file size:** 64KB. Files larger than this are rejected with a `ValueError` before parsing.
- **Load returns None:** If no config file is found in any search location, `load_config()` returns `None` (not an error). The CLI then prompts the user.
- **No auth required:** Coinbase API is public and requires no API key. XRPL nodes are public.
- **Config init:** `create_default_config(wallet_address, output_path)` writes a pre-filled TOML to `./config.toml` by default. The `--init` CLI flag calls this.

## Edge Cases

- **Invalid TOML:** Raises `tomllib.TOMLDecodeError` (not caught; propagates to CLI error handler).
- **Invalid address format:** Raises `ValueError` from Pydantic validator with a human-readable message.
- **Endpoint not in allowlist:** Raises `ValueError` listing the allowed endpoints.
- **Empty addresses list:** WalletConfig accepts an empty list; the app will run in price-only mode (no portfolio widget data).
