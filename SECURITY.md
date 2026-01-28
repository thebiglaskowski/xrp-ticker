# Security Policy

## Supported Versions

| Version | Supported          |
| ------- | ------------------ |
| 0.1.x   | :white_check_mark: |

## Security Features

### Network Security

- **TLS 1.2+ Required**: All WebSocket connections enforce TLS 1.2 minimum
- **Certificate Verification**: SSL certificates are verified by default
- **Trusted Endpoints Only**: XRPL endpoints are validated against an allowlist
- **Rate Limiting**: Built-in rate limiting prevents API abuse

### Data Protection

- **Address Masking**: Wallet addresses are masked in logs (shows `rXXX...XXXX`)
- **No Credential Storage**: The application does not store private keys or secrets
- **Read-Only Operations**: All XRPL operations are read-only (balance queries)
- **Error Sanitization**: Error messages are sanitized to prevent information leakage

### Input Validation

- **XRP Address Validation**: Addresses are validated using regex patterns
- **Configuration Validation**: All config values are validated using Pydantic
- **Message Size Limits**: WebSocket messages are limited to 1MB
- **Response Size Limits**: HTTP responses are limited to 10MB

### Trusted XRPL Endpoints

The following XRPL endpoints are in the trusted allowlist:

- `wss://xrplcluster.com`
- `wss://s1.ripple.com`
- `wss://s2.ripple.com`
- `wss://xrpl.ws`

Custom endpoints outside this list will be rejected.

## Configuration Security

### Config File Location

The config file is searched in the following order:
1. `./config.toml` (current directory)
2. `~/.config/xrp-ticker/config.toml`
3. `$XDG_CONFIG_HOME/xrp-ticker/config.toml`

### Config File Permissions

Recommended file permissions:
```bash
chmod 600 ~/.config/xrp-ticker/config.toml
```

### Sensitive Data in Config

The config file may contain:
- XRP wallet addresses (public, read-only)

The config file should NOT contain:
- Private keys
- API secrets
- Passwords

## Reporting a Vulnerability

If you discover a security vulnerability, please:

1. **Do not** open a public issue
2. Email details to the maintainers
3. Include steps to reproduce if possible
4. Allow reasonable time for a fix before disclosure

## Security Best Practices

### For Users

1. Keep the application updated
2. Use secure network connections
3. Verify config file permissions
4. Don't share wallet addresses publicly
5. Monitor for unexpected behavior

### For Developers

1. Never log full wallet addresses
2. Always validate external input
3. Use parameterized queries
4. Keep dependencies updated
5. Run security tests regularly

## Threat Model

### Assets Protected

- Wallet address privacy (partial)
- Network connection integrity
- Application configuration

### Out of Scope

- Private key management (not handled)
- Transaction signing (not supported)
- Wallet creation (not supported)

### Known Limitations

- Wallet addresses in config are stored in plaintext
- Display shows full wallet address (by design)
- Network traffic patterns may reveal usage

## Dependencies

Security-critical dependencies:
- `pydantic`: Data validation
- `websockets`: Secure WebSocket connections
- `httpx`: Secure HTTP client
- `ssl`: TLS/SSL support (Python standard library)

Keep all dependencies updated to receive security patches.
