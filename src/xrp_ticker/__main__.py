"""Entry point for XRP Ticker application."""

import argparse
import sys
from pathlib import Path

from .app import XRPTickerApp
from .config import (
    AppConfig,
    ConnectionsConfig,
    DisplayConfig,
    WalletConfig,
    create_default_config,
    load_config,
    setup_logging,
)


def parse_args() -> argparse.Namespace:
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        prog="xrp-ticker",
        description="A modern terminal-based XRP portfolio tracker",
    )

    parser.add_argument(
        "-w", "--wallet",
        help="XRP wallet address (overrides config file)",
        type=str,
    )

    parser.add_argument(
        "-c", "--config",
        help="Path to config file",
        type=Path,
    )

    parser.add_argument(
        "--init",
        help="Create a default config file with the specified wallet address",
        type=str,
        metavar="WALLET_ADDRESS",
    )

    parser.add_argument(
        "-d", "--debug",
        help="Enable debug logging",
        action="store_true",
    )

    return parser.parse_args()


def prompt_for_wallet() -> str:
    """Prompt user for wallet address."""
    print("\nNo configuration file found.")
    print("Please enter your XRP wallet address (starts with 'r'):")

    while True:
        address = input("> ").strip()

        if not address:
            print("Wallet address cannot be empty. Please try again:")
            continue

        if not address.startswith("r"):
            print("XRP addresses must start with 'r'. Please try again:")
            continue

        if len(address) < 25 or len(address) > 35:
            print("XRP addresses are typically 25-35 characters. Please verify and try again:")
            continue

        return address


def main() -> int:
    """Main entry point."""
    args = parse_args()

    # Setup logging
    setup_logging(debug=args.debug)

    # Handle --init flag to create config file
    if args.init:
        try:
            config_path = create_default_config(args.init)
            print(f"Created config file: {config_path}")
            print("Edit this file to customize your settings, then run xrp-ticker again.")
            return 0
        except ValueError as e:
            print(f"Error: {e}")
            return 1

    # Try to load config
    config = None

    if args.config:
        # Explicit config path provided
        config = load_config(args.config)
        if config is None:
            print(f"Error: Config file not found: {args.config}")
            return 1
    else:
        # Try default locations
        config = load_config()

    # If no config and wallet provided via CLI, create minimal config
    if config is None:
        if args.wallet:
            wallet_address = args.wallet
        else:
            # Prompt for wallet address
            wallet_address = prompt_for_wallet()

        # Ask if they want to save config
        print(f"\nUsing wallet: {wallet_address}")
        print("Would you like to save this as your config file? [y/N]")
        save = input("> ").strip().lower()

        if save in ("y", "yes"):
            config_path = create_default_config(wallet_address)
            print(f"Config saved to: {config_path}")

        # Create in-memory config
        config = AppConfig(
            wallet=WalletConfig(address=wallet_address),
            display=DisplayConfig(),
            connections=ConnectionsConfig(),
        )

    # Override wallet address if provided via CLI
    if args.wallet:
        config.wallet.address = args.wallet

    # Validate wallet address
    try:
        WalletConfig(address=config.wallet.address)
    except ValueError as e:
        print(f"Error: Invalid wallet address - {e}")
        return 1

    # Run the app
    app = XRPTickerApp(config=config)
    app.run()

    return 0


if __name__ == "__main__":
    sys.exit(main())
