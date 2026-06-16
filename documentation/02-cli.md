---
feature: CLI / Startup
version: "1.0"
last_updated: 2026-03-05
dependencies:
  - "01-configuration.md"
status: stable
---

# CLI / Startup

> The `xrp-ticker` command parses arguments, resolves configuration, optionally prompts
> for a wallet address, and launches the Textual TUI app.

## CLI Flags

| Flag | Short | Type | Description |
|------|-------|------|-------------|
| `--wallet` | `-w` | `str` | XRP wallet address. Overrides addresses in config file. |
| `--config` | `-c` | `Path` | Explicit path to a TOML config file. |
| `--init` | — | `str` (WALLET_ADDRESS) | Create a default config file and exit. Does not start the TUI. |
| `--debug` | `-d` | flag | Enable DEBUG-level logging. |

## Startup Flow

```
parse_args()
  |
  +-- --init flag? --> validate_xrp_address() --> create_default_config() --> exit 0
  |
  +-- --config provided? --> load_config(explicit_path) --> error if None
  |
  +-- try default locations: load_config()
        |
        +-- config found? --> use it
        |
        +-- no config?
              |
              +-- --wallet provided? --> use wallet address
              |
              +-- no wallet? --> prompt_for_wallet() (interactive)
                    |
                    +-- valid address returned?
                          |
                          +-- ask: save config? --> create_default_config() if yes
                          |
                          +-- build in-memory AppConfig
  |
  +-- --wallet provided AND config loaded? --> override config.wallet.addresses = [wallet]
  |
  +-- validate: config.wallet.addresses not empty (error if empty)
  |
  +-- XRPTickerApp(config=config).run()
```

## Business Rules

- **--wallet overrides config:** If both a config file and `--wallet` are provided, `--wallet` replaces all addresses from the config file.
- **--init validates address first:** The address is validated with `validate_xrp_address()` before writing any file. Invalid addresses print a user-friendly error and exit code 1.
- **Interactive wallet prompt:** Max 5 attempts. Accepts `quit`, `exit`, `q` to cancel. On cancel returns `None` and the main function exits with code 1.
- **Save config prompt:** After interactive wallet entry, the user is asked `[y/N]` whether to save the config. Default is no (any input other than `y`/`yes` skips saving).
- **Debug env var:** `XRP_TICKER_DEBUG=1` (or `true`/`yes`) also enables debug logging, equivalent to `--debug`.

## Exit Codes

| Code | Condition |
|------|-----------|
| 0 | Normal exit, or successful `--init` |
| 1 | Invalid address, missing config, max prompt attempts exceeded |

## Edge Cases

- **Empty wallet addresses after config load:** Explicitly checked; prints error and exits 1.
- **EOFError/KeyboardInterrupt in prompt:** Caught cleanly, prints "Cancelled." and returns None.
- **Config file path not found:** When `--config` is given but file does not exist, prints error and exits 1.
