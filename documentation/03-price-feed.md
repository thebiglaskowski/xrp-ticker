---
feature: Price Feed (Coinbase)
version: "1.0"
last_updated: 2026-03-05
dependencies:
  - "01-configuration.md"
status: stable
---

# Price Feed (Coinbase)

> `CoinbaseService` polls the Coinbase Exchange public REST API for XRP/USD price data
> every 5 seconds. No API key required. Uses a circuit breaker pattern for resilience.

## External API

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `https://api.exchange.coinbase.com/products/XRP-USD/stats` | GET | 24h open/high/low/volume |
| `https://api.exchange.coinbase.com/products/XRP-USD/ticker` | GET | Current price |

Both endpoints are fetched **concurrently** per poll cycle via `asyncio.gather()`.

## Data Produced

Each successful poll produces a `PriceData` object:

| Field | Source | Notes |
|-------|--------|-------|
| `symbol` | hardcoded | `"XRPUSD"` |
| `price` | ticker.price | Current price in USD |
| `price_change` | `price - open_24h` | Calculated from stats.open |
| `price_change_percent` | `(price - open_24h) / open_24h * 100` | 0 if open_24h == 0 |
| `high_24h` | stats.high | 24h high |
| `low_24h` | stats.low | 24h low |
| `volume` | stats.volume | 24h volume |
| `timestamp` | `datetime.now()` | Local time of fetch |
| `source` | hardcoded | `"coinbase"` |

## Service Lifecycle

```
CoinbaseService(on_price_update=..., on_status_change=...)
  -> start()    # creates asyncio task running _poll_loop()
  -> stop()     # cancels task, closes HTTP client, emits DISCONNECTED
  -> restart()  # stop() then start()
```

The app **clears callbacks before stopping** to prevent callbacks firing during shutdown:
```python
self._price_service.on_price_update = None
self._price_service.on_status_change = None
await self._price_service.stop()
```

## Rate Limiting

- **Limit:** 30 requests per 60-second window (sliding window, per `RateLimiter`)
- **Behavior:** If rate-limited, `_fetch_price()` returns `None` and logs at DEBUG level (no status change)
- **Poll interval:** 5 seconds minimum (enforced by `max(poll_interval, 5)` in constructor)

## Circuit Breaker

After 5 consecutive fetch failures:
- Status changes to `RECONNECTING`
- Service backs off: `min(30, consecutive_failures * 5)` seconds
- After backoff, `consecutive_failures` resets to 0 and polling resumes

## Connection State Transitions

```
DISCONNECTED -> RECONNECTING (on start())
RECONNECTING -> CONNECTED    (on first successful fetch)
CONNECTED    -> RECONNECTING (on failed fetch)
RECONNECTING -> DISCONNECTED (on stop())
```

## Price Validation Rules

- Price must be > 0 (zero or negative → log warning, return None)
- Price must be <= 10,000 USD (sanity upper bound, XRP-specific)
- Non-numeric values in API response → log warning, return None
- HTTP 4xx/5xx → increment failure counter, return None
- Timeout → increment failure counter, return None

## HTTP Client Configuration

- User-Agent: `XRP-Ticker/{version}` (generic, no system info leaked)
- Max connections: 10
- Max keepalive connections: 5
- Response size limit: 10MB (checked via Content-Length header)

## Business Rules

- **No auth required:** Coinbase Exchange public API, no API key or account needed.
- **Consecutive failure tracking:** Resets to 0 on any successful fetch.
- **Status callback always fires:** Even when state doesn't change (e.g., reconnect attempt count increments).
- **Service name:** The `service_name` property returns `"Coinbase"`, used in the debug panel and status notifications.
