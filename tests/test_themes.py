"""Tests for themes module."""

import pytest

from xrp_ticker.themes import (
    CYBERPUNK_THEME,
    DEFAULT_THEME,
    MONOKAI_THEME,
    RIPPLE_THEME,
    THEME_NAMES,
    THEMES,
    get_next_theme,
    get_theme,
    validate_theme,
)


class TestThemeColors:
    """Tests for ThemeColors dataclass."""

    def test_ripple_theme_has_all_colors(self):
        """Ripple theme should have all color properties."""
        theme = RIPPLE_THEME
        assert theme.primary
        assert theme.secondary
        assert theme.background
        assert theme.surface
        assert theme.text
        assert theme.text_muted
        assert theme.success
        assert theme.warning
        assert theme.error
        assert theme.price_up
        assert theme.price_down

    def test_monokai_theme_has_all_colors(self):
        """Monokai theme should have all color properties."""
        theme = MONOKAI_THEME
        assert theme.primary
        assert theme.price_up
        assert theme.price_down

    def test_cyberpunk_theme_has_all_colors(self):
        """Cyberpunk theme should have all color properties."""
        theme = CYBERPUNK_THEME
        assert theme.primary
        assert theme.price_up
        assert theme.price_down

    def test_theme_colors_are_frozen(self):
        """Theme colors should be immutable."""
        theme = RIPPLE_THEME
        with pytest.raises(AttributeError):
            theme.primary = "#FFFFFF"

    def test_colors_are_hex(self):
        """All colors should be valid hex colors."""
        for theme in THEMES.values():
            for attr in [
                "primary", "secondary", "background", "surface",
                "text", "text_muted", "success", "warning", "error",
                "price_up", "price_down"
            ]:
                color = getattr(theme, attr)
                assert color.startswith("#"), f"{attr} should start with #"
                assert len(color) == 7, f"{attr} should be 7 chars (e.g., #RRGGBB)"


class TestThemesRegistry:
    """Tests for THEMES registry."""

    def test_all_themes_registered(self):
        """All expected themes should be in registry."""
        assert "ripple" in THEMES
        assert "monokai" in THEMES
        assert "cyberpunk" in THEMES

    def test_theme_names_matches_registry(self):
        """THEME_NAMES should match THEMES keys."""
        assert set(THEME_NAMES) == set(THEMES.keys())

    def test_default_theme_exists(self):
        """Default theme should exist in registry."""
        assert DEFAULT_THEME in THEMES


class TestGetTheme:
    """Tests for get_theme function."""

    def test_get_existing_theme(self):
        """Should return theme for valid name."""
        theme = get_theme("ripple")
        assert theme == RIPPLE_THEME

    def test_get_theme_case_insensitive(self):
        """Theme lookup should be case insensitive."""
        theme = get_theme("RIPPLE")
        assert theme == RIPPLE_THEME

    def test_get_nonexistent_theme(self):
        """Should return default for invalid name."""
        theme = get_theme("nonexistent")
        assert theme == THEMES[DEFAULT_THEME]

    def test_get_monokai_theme(self):
        """Should return Monokai theme."""
        theme = get_theme("monokai")
        assert theme == MONOKAI_THEME

    def test_get_cyberpunk_theme(self):
        """Should return Cyberpunk theme."""
        theme = get_theme("cyberpunk")
        assert theme == CYBERPUNK_THEME


class TestGetNextTheme:
    """Tests for get_next_theme function."""

    def test_cycles_to_next(self):
        """Should return next theme in cycle."""
        current = THEME_NAMES[0]
        next_theme = get_next_theme(current)
        assert next_theme == THEME_NAMES[1]

    def test_wraps_around(self):
        """Should wrap to first theme after last."""
        last = THEME_NAMES[-1]
        next_theme = get_next_theme(last)
        assert next_theme == THEME_NAMES[0]

    def test_invalid_theme_returns_first(self):
        """Invalid theme should return first theme."""
        next_theme = get_next_theme("invalid")
        assert next_theme == THEME_NAMES[0]

    def test_case_insensitive(self):
        """Should be case insensitive."""
        next_theme = get_next_theme("RIPPLE")
        # Should work without error
        assert next_theme in THEME_NAMES


class TestValidateTheme:
    """Tests for validate_theme function."""

    def test_valid_theme(self):
        """Valid themes should return True."""
        assert validate_theme("ripple") is True
        assert validate_theme("monokai") is True
        assert validate_theme("cyberpunk") is True

    def test_invalid_theme(self):
        """Invalid themes should return False."""
        assert validate_theme("invalid") is False
        assert validate_theme("") is False

    def test_case_insensitive(self):
        """Should be case insensitive."""
        assert validate_theme("RIPPLE") is True
        assert validate_theme("Monokai") is True
