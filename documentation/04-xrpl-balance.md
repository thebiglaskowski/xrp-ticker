---
feature: XRPL Balance
version: "1.0"
last_updated: 2026-03-05
dependencies:
  - "01-configuration.md"
status: stable
---

# XRPL Balance

> `XRPLWebSocketService` maintains a persistent WebSocket connection to an XRPL node
> and polls wallet balances on a configurable interval. Supports multiple wallets with
> concurrent fetching, automatic endpoint failover, and exponential backoff reconnection.

## External Protocol

Protocol: XRPL WebSocket JSON-RPC API

**Request format (account_info command):**
```json
{
  "id": "<16-char hex request ID>",
  "command": "account_info",
  "account": "<XRP_address>",
  "ledger_index": "validated"
}
```

**Success response path:** `result.account_data.Balance` — balance in drops (string integer)

**Error response:** `response.error == "actNotFound"` means the wallet exists but is unfunded. Returns 0 drops (not an error state).

## Data Produced

Each poll cycle produces a `WalletData` object:

| Field | Value | Notes |
|-------|-------|-------|
| `address` | wallet address or `"{n} wallets"` | Multi-wallet display label |
| `balance_drops` | sum of all wallet balances | In drops (1 XRP = 1,000,000 drops) |
| `balance_xrp` | `balance_drops / 1_000_000` | Computed at creation |
| `source` | current XRPL endpoint URL | Which node answered |
| `timestamp` | `datetime.now()` | Local time of fetch |

## Multi-Wallet Aggregation

All wallet balances are fetched **concurrently** via `asyncio.gather()` over a single WebSocket connection. Results are summed. The `address` field in the result is:
- The address string if exactly 1 wallet
- `"2 wallets"` (or `"N wallets"`) if multiple wallets

## Endpoint Failover

The service maintains an ordered list of XRPL endpoints (default: xrplcluster.com, s1.ripple.com, s2.ripple.com, xrpl.ws). On `InvalidURI` or `InvalidHandshake`, it advances to the next endpoint in the list. If all endpoints are exhausted in one cycle, the state changes to `FAILED` and the loop exits. On `restart()`, the endpoint index resets to 0.

## Service Lifecycle

```
XRPLWebSocketService(wallet_addresses=..., endpoints=..., poll_interval=...)
  -> start()    # creates asyncio task running _connect_and_poll()
  -> stop()     # cancels task, emits DISCONNECTED
  -> restart()  # stop() + reset backoff + reset endpoint index + start()
```

The app **clears callbacks before stopping:**
```python
self._xrpl_service.on_balance_update = None
self._xrpl_service.on_status_change = None
await self._xrpl_service.stop()
```

## Reconnection / Backoff

Uses `BackoffCalculator` from `services/utils.py`. On any `ConnectionClosed` or `OSError`:
- State -> `RECONNECTING`, reconnect_attempts incremented
- Waits `backoff.calculate()` seconds before retrying (exponential backoff)
- On successful connection, `backoff.reset()` and `consecutive_failures = 0`

## Circuit Breaker

After 5 consecutive failures:
- Backs off `min(60, consecutive_failures * 10)` seconds
- Resets `consecutive_failures` to 0 after backoff (polling resumes normally)

## WebSocket Settings

| Setting | Value |
|---------|-------|
| Ping interval | 30 seconds |
| Ping timeout | 10 seconds |
| Close timeout | 5 seconds |
| Max message size | 1MB |
| SSL | System SSL context (enforced) |

## Connection State Transitions

```
DISCONNECTED -> RECONNECTING (on start() or connection attempt)
RECONNECTING -> CONNECTED    (on successful WebSocket handshake)
CONNECTED    -> RECONNECTING (on ConnectionClosed / OSError)
RECONNECTING -> FAILED       (on InvalidURI after all endpoints exhausted)
any          -> DISCONNECTED (on stop())
```

## Security Rules

- Endpoint must start with `wss://` (enforced at config validation)
- Endpoint must be in `TRUSTED_XRPL_DOMAINS` allowlist (validated at service init; logs warning if not)
- Wallet addresses are masked in logs: `rABC...XYZ` format via `mask_address()`
- Response size capped at 1MB
- Balance range check: `0 <= balance_drops <= 100_000_000_000_000_000` (100B XRP max supply)

## Business Rules

- **Poll interval minimum:** 10 seconds (enforced by `max(poll_interval, 10)` in constructor)
- **No wallet configured:** Returns `WalletData` with address `"No wallets"` and balance 0 (not an error)
- **Unfunded wallet (actNotFound):** Returns 0 drops for that wallet, does not affect other wallets
- **`fetch_balance_once()`:** One-shot fetch without starting the polling loop; tries each endpoint in order
