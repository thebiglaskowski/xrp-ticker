# ADR-001: Service Architecture for External Data Sources

## Status

Accepted

## Date

2026-01-27

## Context

XRP Ticker is a terminal-based portfolio tracker that needs to fetch data from two external sources:

1. **Price data** - Current XRP/USD price, 24h statistics (high, low, volume, change)
2. **Wallet balance** - XRP balance from XRPL blockchain for user's wallet(s)

The application runs in a terminal UI (Textual framework) and must maintain responsive UX while continuously updating data from these external sources.

**Forces at play:**

- **Real-time updates required** - Users expect live price data without manual refresh
- **Network reliability** - External services may be unavailable or slow
- **Rate limiting** - External APIs have usage limits
- **Resource efficiency** - Terminal app should be lightweight
- **Error resilience** - Network failures shouldn't crash the app
- **Multiple data sources** - Each source has different characteristics and APIs

## Decision

We will implement a **dual-service polling architecture** with the following characteristics:

1. **Separate service classes** for each data source (CoinbaseService, XRPLWebSocketService)
2. **Callback-based communication** to decouple services from UI
3. **Async/await patterns** for non-blocking I/O
4. **Independent polling loops** with configurable intervals
5. **Circuit breaker pattern** for fault tolerance
6. **Rate limiting** to respect API limits

## Options Considered

### Option 1: Single Unified Service

**Description:** One service class that fetches both price and balance data sequentially.

**Pros:**
- Simpler codebase with fewer classes
- Easier to coordinate data updates
- Single point of configuration

**Cons:**
- Failure in one data source blocks the other
- Different polling intervals not easily supported
- Harder to add new data sources later
- Tight coupling between unrelated concerns

### Option 2: Dual-Service with Direct UI Integration

**Description:** Separate services that directly update UI widgets.

**Pros:**
- Direct updates without callback indirection
- Potentially faster updates

**Cons:**
- Services tightly coupled to UI framework
- Harder to test services in isolation
- Services need knowledge of widget structure
- Makes headless/CLI mode difficult

### Option 3: Dual-Service with Callback Communication (Chosen)

**Description:** Independent services that communicate via callbacks, allowing the UI layer to handle updates.

**Pros:**
- Services are framework-agnostic and testable
- Clean separation of concerns
- Easy to add new data sources
- Each service can have independent error handling
- Supports different polling intervals per source
- UI can aggregate/transform data as needed

**Cons:**
- More indirection than direct integration
- Requires careful callback management to avoid memory leaks
- Slightly more complex initial setup

### Option 4: Event Bus / Message Queue

**Description:** Services publish to an event bus; UI subscribes to events.

**Pros:**
- Maximum decoupling
- Easy to add observers
- Natural fit for reactive UI

**Cons:**
- Overkill for two services
- Adds dependency on event bus library
- More complex debugging
- Harder to trace data flow

## Rationale

**Option 3 (Dual-Service with Callbacks)** was selected because:

1. **Testability** - Services can be unit tested without Textual framework
2. **Separation of concerns** - Price fetching logic is isolated from balance fetching
3. **Fault isolation** - Coinbase failures don't affect XRPL balance updates
4. **Flexibility** - Price polls every 5s; balance polls every 30s (configurable)
5. **Simplicity** - Callbacks are Python-native, no external dependencies
6. **Future-proof** - Easy to add Binance, Kraken, or other sources later

The callback pattern mirrors how Textual's reactive system works, making integration natural.

## Consequences

### Positive
- Services are independently testable with mock callbacks
- Adding a new price source (e.g., Binance) requires minimal UI changes
- Network failures in one service don't block the other
- Clear ownership: CoinbaseService owns price logic, XRPLWebSocketService owns balance logic
- Circuit breaker prevents cascading failures

### Negative
- Must clear callbacks before stopping services to avoid errors during shutdown
- Two polling loops means two places to configure intervals
- Callback registration happens at startup, requiring careful lifecycle management

### Neutral
- Services maintain their own connection state (CONNECTED, RECONNECTING, FAILED)
- Each service has its own exponential backoff for reconnection
- Debug panel tracks message counts per service

## Implementation Notes

- Callbacks are optional (`None` by default) - services work without them
- Services expose `start()`, `stop()`, `restart()` async methods
- Status changes trigger `on_status_change` callback with `ServiceStatus` object
- Data updates trigger `on_price_update` or `on_balance_update` callbacks
- Services should clear callbacks before `stop()` to avoid errors during shutdown:
  ```python
  service.on_price_update = None
  service.on_status_change = None
  await service.stop()
  ```

## Related Decisions

- ADR-002: Security Architecture (rate limiting, endpoint validation) - To be documented
- ADR-003: UI Framework Selection (Textual TUI) - To be documented

## References

- [Textual Framework Documentation](https://textual.textualize.io/)
- [Circuit Breaker Pattern](https://martinfowler.com/bliki/CircuitBreaker.html)
- [Coinbase Exchange API](https://docs.cloud.coinbase.com/exchange/reference)
- [XRPL WebSocket API](https://xrpl.org/websocket-api-tool.html)
