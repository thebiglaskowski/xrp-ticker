# ADR-002: Security Architecture

## Status

Accepted

## Date

2026-01-27

## Context

XRP Ticker handles sensitive financial data:

1. **Wallet addresses** - User's XRP wallet addresses (could enable tracking)
2. **Balance information** - User's portfolio value (financial privacy)
3. **Network connections** - WebSocket/HTTPS to external services

The application connects to external services (Coinbase API, XRPL nodes) and must protect against:

- Information leakage through logs or error messages
- Malicious/compromised XRPL endpoints
- Denial of service through resource exhaustion
- Man-in-the-middle attacks
- Injection attacks via configuration

**Forces at play:**

- **Privacy** - Users don't want wallet addresses/balances exposed
- **Reliability** - Security measures shouldn't break functionality
- **Debuggability** - Need enough logging to diagnose issues
- **Defense in depth** - Multiple layers of protection
- **Simplicity** - Security code must be auditable and maintainable

## Decision

We will implement a **layered security architecture** with the following components:

1. **Endpoint allowlist** - Only trusted XRPL WebSocket endpoints permitted
2. **TLS enforcement** - Minimum TLS 1.2 with certificate validation
3. **Error sanitization** - Generic error messages, no internal details exposed
4. **Data masking** - Wallet addresses masked in logs (show first/last 4 chars)
5. **Rate limiting** - Sliding window limiter to prevent API abuse
6. **Message size limits** - Cap WebSocket/HTTP response sizes
7. **Request tracing** - Unique IDs for debugging without exposing sensitive data
8. **Input validation** - Strict validation of addresses, config files
9. **Circuit breaker** - Prevent cascading failures from repeated errors

## Options Considered

### Option 1: Minimal Security (Trust External Services)

**Description:** Basic HTTPS/WSS with no additional security layers.

**Pros:**
- Simpler implementation
- Fewer dependencies
- Faster initial development

**Cons:**
- Vulnerable to malicious endpoint injection via config
- Error messages may leak internal paths/state
- No protection against resource exhaustion
- Logs may expose wallet addresses

### Option 2: Security Library Integration

**Description:** Use established security libraries (e.g., python-owasp, security middleware).

**Pros:**
- Battle-tested implementations
- Comprehensive coverage
- Regular security updates

**Cons:**
- Additional dependencies to maintain
- May be overkill for a terminal app
- Harder to customize for specific needs
- Larger attack surface from dependencies

### Option 3: Custom Security Module (Chosen)

**Description:** Centralized `security.py` module with purpose-built security utilities.

**Pros:**
- Tailored to exact requirements
- No external dependencies
- Easy to audit (single file)
- Consistent patterns across codebase
- Lightweight for terminal app

**Cons:**
- Must implement and maintain ourselves
- Risk of missing edge cases
- No automatic security updates

### Option 4: External Security Service

**Description:** Route traffic through security proxy/gateway.

**Pros:**
- Centralized security enforcement
- Advanced threat detection
- Logging and monitoring built-in

**Cons:**
- Overkill for personal terminal app
- Adds latency and complexity
- Requires infrastructure setup
- Potential single point of failure

## Rationale

**Option 3 (Custom Security Module)** was selected because:

1. **Appropriate scale** - A terminal portfolio tracker doesn't need enterprise security infrastructure
2. **Auditability** - All security code in one 230-line module
3. **No dependencies** - Uses only Python standard library
4. **Tailored protection** - Addresses specific threats (endpoint injection, log leakage)
5. **Testable** - 45+ unit tests covering security functions

The security module (`security.py`) centralizes all security utilities, making it easy to audit and update.

## Consequences

### Positive

- **Endpoint protection** - Only 4 trusted XRPL endpoints allowed, preventing malicious node injection
- **Log safety** - Wallet addresses appear as `rN7n...k2D9` in all logs
- **Error privacy** - Users see "Connection refused" not internal stack traces
- **Resource protection** - Rate limiter prevents accidental API abuse; message size limits prevent memory exhaustion
- **Request correlation** - 16-char hex request IDs enable debugging without exposing data
- **TLS security** - Enforced TLS 1.2+ with hostname verification

### Negative

- **Maintenance burden** - Must update trusted endpoint list if XRPL infrastructure changes
- **Debugging complexity** - Sanitized errors require request IDs to correlate with detailed internal logs
- **False sense of security** - Custom implementation may have undiscovered vulnerabilities

### Neutral

- Security constants centralized in `security.py`
- Config validation happens at startup (fail-fast)
- Rate limiter state is per-service instance (not shared)

## Implementation Notes

### Trusted Endpoint Allowlist

```python
TRUSTED_XRPL_DOMAINS = frozenset({
    "xrplcluster.com",
    "s1.ripple.com",
    "s2.ripple.com",
    "xrpl.ws",
})
```

Only `wss://` endpoints with these domains are permitted. Config validation rejects untrusted endpoints.

### Error Sanitization

```python
error_mappings = {
    "ConnectionRefusedError": "Connection refused",
    "TimeoutError": "Request timed out",
    "SSLError": "SSL/TLS error",
    "SSLCertVerificationError": "Certificate verification failed",
    "gaierror": "DNS resolution failed",
}
```

Unknown errors return "An error occurred" - never expose internal details.

### Address Masking

```python
def mask_sensitive_data(data: str, visible_chars: int = 4) -> str:
    return f"{data[:4]}...{data[-4:]}"  # "rN7n...k2D9"
```

All logging of wallet addresses uses this function.

### Rate Limiting

```python
class RateLimiter:
    def __init__(self, max_requests=30, window_seconds=60):
        # Sliding window algorithm
```

Prevents exceeding API rate limits; defaults to 30 requests/minute.

### TLS Configuration

```python
ctx = ssl.create_default_context()
ctx.check_hostname = True
ctx.verify_mode = ssl.CERT_REQUIRED
ctx.minimum_version = ssl.TLSVersion.TLSv1_2
```

Enforces modern TLS with full certificate validation.

### Message Size Limits

```python
MAX_WEBSOCKET_MESSAGE_SIZE = 1024 * 1024   # 1MB
MAX_HTTP_RESPONSE_SIZE = 10 * 1024 * 1024  # 10MB
MAX_CONFIG_FILE_SIZE = 64 * 1024           # 64KB
```

Prevents memory exhaustion from malformed/malicious responses.

## Related Decisions

- [ADR-001: Service Architecture](ADR-001-service-architecture.md) - Services implement these security patterns
- ADR-003: Configuration Approach - To be documented (validation, allowlists)

## References

- [OWASP Secure Coding Practices](https://owasp.org/www-project-secure-coding-practices-quick-reference-guide/)
- [Python SSL Module Documentation](https://docs.python.org/3/library/ssl.html)
- [XRPL Public Servers](https://xrpl.org/public-servers.html)
- [Rate Limiting Algorithms](https://www.figma.com/blog/an-alternative-approach-to-rate-limiting/)
