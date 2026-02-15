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
from .security import validate_xrp_address


def parse_args() -> argparse.Namespace:
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        prog="xrp-ticker",
        description="A modern terminal-based XRP portfolio tracker",
    )

    parser.add_argument(
        "-w",
        "--wallet",
        help="XRP wallet address (overrides config file)",
        type=str,
    )

    parser.add_argument(
        "-c",
        "--config",
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
        "-d",
        "--debug",
        help="Enable debug logging",
        action="store_true",
    )

    return parser.parse_args()


def prompt_for_wallet() -> str | None:
    """Prompt user for wallet address.

    Returns:
        Wallet address string if valid, None if user cancels or max attempts exceeded.
    """
    max_attempts = 5
    print("\nNo configuration file found.")
    print("Please enter your XRP wallet address (starts with 'r'):")
    print("(Press Ctrl+C or enter 'quit' to exit)")

    for attempt in range(max_attempts):
        try:
            address = input("> ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\nCancelled.")
            return None

        if address.lower() in ("quit", "exit", "q"):
            print("Exiting.")
            return None

        if not address:
            remaining = max_attempts - attempt - 1
            if remaining > 0:
                print(f"Wallet address cannot be empty. {remaining} attempts remaining:")
            continue

        if not address.startswith("r"):
            remaining = max_attempts - attempt - 1
            if remaining > 0:
                print(f"XRP addresses must start with 'r'. {remaining} attempts remaining:")
            continue

        if len(address) < 25 or len(address) > 35:
            remaining = max_attempts - attempt - 1
            if remaining > 0:
                print(f"XRP addresses are 25-35 characters. {remaining} attempts remaining:")
            continue

        return address

    print("Maximum attempts exceeded.")
    return None


def main() -> int:
    """Main entry point."""
    args = parse_args()

    # Setup logging
    setup_logging(debug=args.debug)

    # Handle --init flag to create config file
    if args.init:
        if not validate_xrp_address(args.init):
            print(f"Error: Invalid XRP address: {args.init}")
            print("XRP addresses start with 'r' and are 25-35 base58 characters.")
            return 1
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
            if wallet_address is None:
                return 1

        # Ask if they want to save config
        print(f"\nUsing wallet: {wallet_address}")
        print("Would you like to save this as your config file? [y/N]")
        save = input("> ").strip().lower()

        if save in ("y", "yes"):
            config_path = create_default_config(wallet_address)
            print(f"Config saved to: {config_path}")

        # Create in-memory config
        config = AppConfig(
            wallet=WalletConfig(addresses=[wallet_address]),
            display=DisplayConfig(),
            connections=ConnectionsConfig(),
        )

    # Override wallet address if provided via CLI
    if args.wallet:
        config.wallet.addresses = [args.wallet]

    # Validate wallet addresses
    if not config.wallet.addresses:
        print("Error: No wallet addresses configured")
        return 1

    # Run the app
    app = XRPTickerApp(config=config)
    app.run()

    return 0


if __name__ == "__main__":
    sys.exit(main())
