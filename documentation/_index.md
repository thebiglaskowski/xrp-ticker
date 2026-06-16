# Feature Documentation

> One doc per feature. Claude reads the relevant doc before touching any code.
> Working on a feature? Find it in the table below and read the doc first.

## Lookup Table

| Feature | Doc | Description |
|---------|-----|-------------|
| Configuration | `documentation/01-configuration.md` | TOML config loading, Pydantic validation, file search |
| CLI / Startup | `documentation/02-cli.md` | argparse entry point, --init flow, wallet prompting |
| Price Feed (Coinbase) | `documentation/03-price-feed.md` | REST API polling, rate limiting, circuit breaker |
| XRPL Balance | `documentation/04-xrpl-balance.md` | WebSocket client, endpoint failover, balance aggregation |
| TUI Application | `documentation/05-tui-app.md` | Main Textual app, keybindings, service wiring, theme cycling |
| Security | `documentation/06-security.md` | Address validation, rate limiter, endpoint allowlist, sanitization |
| Themes | `documentation/07-themes.md` | 3 built-in themes, cycling, CSS class application |
| Widgets | `documentation/08-widgets.md` | 5 display widgets with reactive data binding |

## Doc-First Workflow

When working on a feature:
1. Find the feature in the lookup table above
2. Read the full doc before writing any code
3. If no doc exists, run `/cs-docs "feature name"` to generate one
4. Update the doc if implementation reveals a mismatch

## Quality Bar

A good feature doc lets Claude implement the feature correctly without reading source code.
Business rules matter more than API shapes. Claude can infer patterns -- it cannot infer limits,
cascade rules, permission gates, or state machines.
