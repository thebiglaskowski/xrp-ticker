---
feature: Themes
version: "1.0"
last_updated: 2026-03-05
dependencies: []
status: stable
---

# Themes

> Three built-in color themes applied via CSS classes on the Textual screen.
> Themes cycle in fixed order: ripple -> monokai -> cyberpunk -> ripple.

## Available Themes

| Name | Primary | Background | Aesthetic |
|------|---------|------------|-----------|
| `ripple` | `#00A4E4` (Ripple blue) | `#0D1117` | Dark GitHub-style |
| `monokai` | `#F92672` (pink/magenta) | `#1E1E1E` | Classic editor dark |
| `cyberpunk` | `#00FF41` (matrix green) | `#0A0A0A` | Terminal hacker |

## ThemeColors Fields

| Field | Purpose |
|-------|---------|
| `primary` | Accent/header color |
| `secondary` | Panel/border background |
| `background` | App background |
| `surface` | Widget surface color |
| `text` | Primary text |
| `text_muted` | Secondary/label text |
| `success` | Connection OK, positive change |
| `warning` | Reconnecting, neutral states |
| `error` | Connection failed |
| `price_up` | Upward price movement |
| `price_down` | Downward price movement |

## How Themes Are Applied

Themes are applied via CSS classes on the Textual screen (not inline styles):

```python
# _apply_theme() in XRPTickerApp
screen.remove_class("theme-ripple", "theme-monokai", "theme-cyberpunk")
screen.add_class(f"theme-{theme_name}")
```

The TCSS file (`styles/app.tcss`) defines color variables under each `.theme-*` rule. No Python color values are injected at runtime — everything is CSS.

## Default Theme

`DEFAULT_THEME = "ripple"`. The config file can specify a different starting theme via `[display] theme = "..."`, but the TUI currently initializes at index 0 of `THEME_NAMES` regardless. Config `theme` field is stored but not wired to the initial `_current_theme_index` in the app.

The configured theme is applied on startup: `on_mount()` calls `_apply_theme(THEME_NAMES[_current_theme_index])` where the index is resolved from `config.display.theme` in `__init__`. If the config value is not a valid theme name, it falls back to index 0.

## Cycle Order

`THEME_NAMES = ["ripple", "monokai", "cyberpunk"]` — fixed list order. `get_next_theme(current)` wraps at the end. If `current` is not found in the list (e.g., invalid theme name), returns `THEME_NAMES[0]`.

## Adding a New Theme

1. Define a `ThemeColors(...)` constant in `themes.py`
2. Add it to the `THEMES` dict with a string key
3. Add CSS variables under `.theme-{name}` in `styles/app.tcss`
4. The theme key is automatically included in `THEME_NAMES` and available for cycling

## Business Rules

- Theme names are lowercased for lookups (`get_theme()` and `get_next_theme()` both call `.lower()`)
- `validate_theme(name)` returns a bool (used in config validation if needed)
- `ThemeColors` is a frozen dataclass — immutable after creation
