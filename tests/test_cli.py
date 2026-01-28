"""Tests for CLI entry point (__main__.py)."""

import tempfile
from pathlib import Path
from unittest.mock import MagicMock, patch

from xrp_ticker.__main__ import main, parse_args, prompt_for_wallet


class TestParseArgs:
    """Tests for CLI argument parsing."""

    def test_parse_args_defaults(self):
        """Default arguments should be set correctly."""
        with patch("sys.argv", ["xrp-ticker"]):
            args = parse_args()

        assert args.wallet is None
        assert args.config is None
        assert args.init is None
        assert args.debug is False

    def test_parse_args_wallet(self):
        """--wallet argument should be parsed."""
        with patch("sys.argv", ["xrp-ticker", "-w", "rTestAddress1234567890123456"]):
            args = parse_args()

        assert args.wallet == "rTestAddress1234567890123456"

    def test_parse_args_wallet_long(self):
        """--wallet long form should work."""
        with patch("sys.argv", ["xrp-ticker", "--wallet", "rTestAddress1234567890123456"]):
            args = parse_args()

        assert args.wallet == "rTestAddress1234567890123456"

    def test_parse_args_config(self):
        """--config argument should be parsed as Path."""
        with patch("sys.argv", ["xrp-ticker", "-c", "/path/to/config.toml"]):
            args = parse_args()

        assert args.config == Path("/path/to/config.toml")

    def test_parse_args_init(self):
        """--init argument should be parsed."""
        with patch("sys.argv", ["xrp-ticker", "--init", "rNewWalletAddress12345678901"]):
            args = parse_args()

        assert args.init == "rNewWalletAddress12345678901"

    def test_parse_args_debug(self):
        """--debug flag should be parsed."""
        with patch("sys.argv", ["xrp-ticker", "-d"]):
            args = parse_args()

        assert args.debug is True

    def test_parse_args_debug_long(self):
        """--debug long form should work."""
        with patch("sys.argv", ["xrp-ticker", "--debug"]):
            args = parse_args()

        assert args.debug is True

    def test_parse_args_combined(self):
        """Multiple arguments should be parsed together."""
        with patch(
            "sys.argv",
            [
                "xrp-ticker",
                "-w", "rTestAddress1234567890123456",
                "-c", "/path/config.toml",
                "-d",
            ],
        ):
            args = parse_args()

        assert args.wallet == "rTestAddress1234567890123456"
        assert args.config == Path("/path/config.toml")
        assert args.debug is True


class TestPromptForWallet:
    """Tests for interactive wallet prompt."""

    def test_prompt_for_wallet_valid(self):
        """Valid wallet address should be accepted."""
        with patch("builtins.input", return_value="rN7n3473SaZBCG4dFL83w7a1RXtXtbk2D9"):
            result = prompt_for_wallet()

        assert result == "rN7n3473SaZBCG4dFL83w7a1RXtXtbk2D9"

    def test_prompt_for_wallet_strips_whitespace(self):
        """Whitespace should be stripped from input."""
        with patch("builtins.input", return_value="  rN7n3473SaZBCG4dFL83w7a1RXtXtbk2D9  "):
            result = prompt_for_wallet()

        assert result == "rN7n3473SaZBCG4dFL83w7a1RXtXtbk2D9"

    def test_prompt_for_wallet_retries_on_empty(self):
        """Empty input should prompt again."""
        inputs = iter(["", "rN7n3473SaZBCG4dFL83w7a1RXtXtbk2D9"])
        with patch("builtins.input", lambda _: next(inputs)):
            result = prompt_for_wallet()

        assert result == "rN7n3473SaZBCG4dFL83w7a1RXtXtbk2D9"

    def test_prompt_for_wallet_retries_on_invalid_prefix(self):
        """Address not starting with 'r' should prompt again."""
        inputs = iter(["xInvalidAddress1234567890123", "rN7n3473SaZBCG4dFL83w7a1RXtXtbk2D9"])
        with patch("builtins.input", lambda _: next(inputs)):
            result = prompt_for_wallet()

        assert result == "rN7n3473SaZBCG4dFL83w7a1RXtXtbk2D9"

    def test_prompt_for_wallet_retries_on_short_address(self):
        """Short address should prompt again."""
        inputs = iter(["rShort", "rN7n3473SaZBCG4dFL83w7a1RXtXtbk2D9"])
        with patch("builtins.input", lambda _: next(inputs)):
            result = prompt_for_wallet()

        assert result == "rN7n3473SaZBCG4dFL83w7a1RXtXtbk2D9"


class TestMain:
    """Tests for main entry point."""

    def test_main_init_creates_config(self):
        """--init should create config file and exit."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config_path = Path(tmpdir) / "config.toml"

            with patch("sys.argv", ["xrp-ticker", "--init", "rN7n3473SaZBCG4dFL83w7a1RXtXtbk2D9"]):
                with patch(
                    "xrp_ticker.__main__.create_default_config", return_value=config_path
                ) as mock_create:
                    result = main()

            assert result == 0
            mock_create.assert_called_once_with("rN7n3473SaZBCG4dFL83w7a1RXtXtbk2D9")

    def test_main_config_not_found(self):
        """Should return 1 if explicit config file not found."""
        with patch("sys.argv", ["xrp-ticker", "-c", "/nonexistent/config.toml"]):
            with patch("xrp_ticker.__main__.load_config", return_value=None):
                result = main()

        assert result == 1

    def test_main_no_wallet_addresses(self):
        """Should return 1 if no wallet addresses configured."""
        mock_config = MagicMock()
        mock_config.wallet.addresses = []

        with patch("sys.argv", ["xrp-ticker"]):
            with patch("xrp_ticker.__main__.load_config", return_value=mock_config):
                result = main()

        assert result == 1

    def test_main_wallet_override(self):
        """CLI wallet should override config file wallet."""
        mock_config = MagicMock()
        mock_config.wallet.addresses = ["rOriginalAddress1234567890123"]
        mock_app = MagicMock()

        with patch("sys.argv", ["xrp-ticker", "-w", "rOverrideAddress123456789012"]):
            with patch("xrp_ticker.__main__.load_config", return_value=mock_config):
                with patch("xrp_ticker.__main__.XRPTickerApp", return_value=mock_app):
                    main()

        # Verify wallet was overridden
        assert mock_config.wallet.addresses == ["rOverrideAddress123456789012"]

    def test_main_runs_app(self):
        """Should create and run XRPTickerApp with config."""
        mock_config = MagicMock()
        mock_config.wallet.addresses = ["rN7n3473SaZBCG4dFL83w7a1RXtXtbk2D9"]
        mock_app = MagicMock()

        with patch("sys.argv", ["xrp-ticker"]):
            with patch("xrp_ticker.__main__.load_config", return_value=mock_config):
                with patch("xrp_ticker.__main__.XRPTickerApp", return_value=mock_app) as mock_class:
                    result = main()

        assert result == 0
        mock_class.assert_called_once_with(config=mock_config)
        mock_app.run.assert_called_once()

    def test_main_prompts_when_no_config(self):
        """Should prompt for wallet when no config exists."""
        mock_app = MagicMock()

        wallet_addr = "rN7n3473SaZBCG4dFL83w7a1RXtXtbk2D9"
        with patch("sys.argv", ["xrp-ticker"]):
            with patch("xrp_ticker.__main__.load_config", return_value=None):
                with patch("xrp_ticker.__main__.prompt_for_wallet", return_value=wallet_addr):
                    with patch("builtins.input", return_value="n"):  # Don't save config
                        with patch("xrp_ticker.__main__.XRPTickerApp", return_value=mock_app):
                            result = main()

        assert result == 0
        mock_app.run.assert_called_once()
