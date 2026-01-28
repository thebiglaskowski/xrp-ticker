"""Theme configuration for XRP Ticker."""

from dataclasses import dataclass
from typing import Final


@dataclass(frozen=True)
class ThemeColors:
    """Color scheme for a theme."""

    primary: str
    secondary: str
    background: str
    surface: str
    text: str
    text_muted: str
    success: str
    warning: str
    error: str
    price_up: str
    price_down: str


# Theme definitions
RIPPLE_THEME = ThemeColors(
    primary="#00A4E4",
    secondary="#23292F",
    background="#0D1117",
    surface="#161B22",
    text="#E6EDF3",
    text_muted="#7D8590",
    success="#3FB950",
    warning="#D29922",
    error="#F85149",
    price_up="#3FB950",
    price_down="#F85149",
)

MONOKAI_THEME = ThemeColors(
    primary="#F92672",
    secondary="#272822",
    background="#1E1E1E",
    surface="#2D2D2D",
    text="#F8F8F2",
    text_muted="#75715E",
    success="#A6E22E",
    warning="#E6DB74",
    error="#F92672",
    price_up="#A6E22E",
    price_down="#F92672",
)

CYBERPUNK_THEME = ThemeColors(
    primary="#00FF41",
    secondary="#003B00",
    background="#0A0A0A",
    surface="#1A1A1A",
    text="#00FF41",
    text_muted="#008F11",
    success="#00FF41",
    warning="#FFFF00",
    error="#FF0040",
    price_up="#00FF41",
    price_down="#FF0040",
)

# Available themes registry
THEMES: Final[dict[str, ThemeColors]] = {
    "ripple": RIPPLE_THEME,
    "monokai": MONOKAI_THEME,
    "cyberpunk": CYBERPUNK_THEME,
}

# Default theme
DEFAULT_THEME: Final[str] = "ripple"

# Theme names list (for cycling)
THEME_NAMES: Final[list[str]] = list(THEMES.keys())


def get_theme(name: str) -> ThemeColors:
    """
    Get theme colors by name.

    Args:
        name: Theme name

    Returns:
        ThemeColors for the theme, or default if not found
    """
    return THEMES.get(name.lower(), THEMES[DEFAULT_THEME])


def get_next_theme(current: str) -> str:
    """
    Get the next theme name in the cycle.

    Args:
        current: Current theme name

    Returns:
        Next theme name
    """
    try:
        current_index = THEME_NAMES.index(current.lower())
        next_index = (current_index + 1) % len(THEME_NAMES)
        return THEME_NAMES[next_index]
    except ValueError:
        return THEME_NAMES[0]


def validate_theme(name: str) -> bool:
    """
    Check if a theme name is valid.

    Args:
        name: Theme name to validate

    Returns:
        True if valid, False otherwise
    """
    return name.lower() in THEMES
