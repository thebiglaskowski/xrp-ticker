---
feature: Security
version: "1.0"
last_updated: 2026-03-05
dependencies: []
status: stable
---

# Security

> Centralized security utilities: XRP address validation, endpoint allowlisting,
> rate limiting, message size caps, error message sanitization, and safe logging.

## XRP Address Validation

Pattern: `r[1-9A-HJ-NP-Za-km-z]{24,34}` (base58 alphabet, excludes `0`, `O`, `I`, `l`)

| Check | Rule |
|-------|------|
| First character | Must be `r` |
| Length | 25-35 characters inclusive |
| Charset | base58 only (no `0`, `O`, `I`, `l`) |

`validate_xrp_address(address: str) -> bool` — returns False for empty string, wrong length, or pattern mismatch.

## Trusted XRPL Endpoint Allowlist

`TRUSTED_XRPL_DOMAINS`:
```
xrplcluster.com
s1.ripple.com
s2.ripple.com
xrpl.ws
```

`is_trusted_endpoint(endpoint: str) -> bool`:
- Must start with `wss://`
- Domain (after stripping `wss://`, port, and path) must be in the allowlist
- Result is cached with `@lru_cache(maxsize=128)`

## Rate Limiter

`RateLimiter(max_requests=30, window_seconds=60)` — sliding window.

| Method | Behavior |
|--------|----------|
| `can_make_request(time)` | Returns True if under limit; prunes old timestamps |
| `record_request(time)` | Appends timestamp to internal list |
| `time_until_available(time)` | Returns seconds to wait; 0 if allowed |

**Coinbase service config:** 30 requests / 60 seconds = max 0.5 req/sec. Poll interval is 5 seconds so normal operation is well under this limit.

## Message Size Limits

| Limit | Value | Where Enforced |
|-------|-------|----------------|
| `MAX_WEBSOCKET_MESSAGE_SIZE` | 1MB | `websockets` `max_size` param + manual size check |
| `MAX_HTTP_RESPONSE_SIZE` | 10MB | Content-Length header check before body read |

## Error Message Sanitization

`sanitize_error_message(error: Exception) -> str` — maps known error types to generic strings to prevent leaking stack traces, internal paths, or addresses in logs:

| Exception type | Returned message |
|----------------|-----------------|
| `ConnectionRefusedError` | `"Connection refused"` |
| `TimeoutError` | `"Request timed out"` |
| `SSLError` | `"SSL/TLS error"` |
| `SSLCertVerificationError` | `"Certificate verification failed"` |
| `gaierror` | `"DNS resolution failed"` |
| `ConnectionResetError` | `"Connection reset"` |
| `BrokenPipeError` | `"Connection broken"` |
| Any other | `"An error occurred"` |

## Address Masking (for logging)

`mask_address(address: str) -> str` — from `services/utils.py`. Shortens wallet addresses to `rABC...XYZ` format for log lines (4 visible chars at start and end). Also available as `mask_sensitive_data(data, visible_chars=4)` in `security.py`.

## Display Text Sanitization

`sanitize_display_text(text: str, max_length: int = 100) -> str`:
- Strips all non-printable characters (except `\n`, `\t`)
- Truncates to `max_length` with `...` suffix

## User-Agent

`get_safe_user_agent() -> str` returns `"XRP-Ticker/{version}"`. Does not include OS, Python version, or hostname.

## Request ID Generation

`generate_request_id() -> str` — returns a 16-character hex string from `secrets.token_hex(8)`. Used as a correlation ID in log messages, not exposed externally.

## Business Rules

- **No credentials stored:** The app has no auth tokens, API keys, or passwords.
- **No user PII logged:** Wallet addresses are masked in all log output.
- **Config file size cap:** 64KB maximum to prevent malicious config files causing memory issues.
- **SSL enforced:** All external connections use TLS (wss:// for XRPL, https:// for Coinbase).
