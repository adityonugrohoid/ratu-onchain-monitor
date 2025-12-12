"""
Main entry point for On-chain Monitor.

On-chain Monitor provides token holder analytics:
- Snapshot all token holders
- Track whale wallets
- Monitor holder changes over time

Usage:
  onchain-monitor snapshot <contract> [chain]
  onchain-monitor holders <contract> [chain]
  onchain-monitor price <contract> [chain]
"""

import logging
import sys
from datetime import datetime
from pathlib import Path

from onchain_monitor.ankr_client import AnkrClient
from onchain_monitor.config import LOG_FILE, LOG_LEVEL, SUPPORTED_CHAINS
from onchain_monitor.snapshot import create_holders_snapshot


def setup_logging():
    """Configure logging for the application."""
    LOG_FILE.parent.mkdir(parents=True, exist_ok=True)

    logging.basicConfig(
        level=getattr(logging, LOG_LEVEL.upper()),
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        handlers=[
            logging.FileHandler(LOG_FILE),
        ],
    )
    logging.getLogger("httpx").setLevel(logging.WARNING)


def print_header(command: str, token_name: str = None):
    """Print command header."""
    print()
    print("=" * 80)
    if token_name:
        print(f"  ON-CHAIN MONITOR - {command} | {token_name}")
    else:
        print(f"  ON-CHAIN MONITOR - {command}")
    print("=" * 80)
    print()
    print(f"  Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    print("-" * 80)


def print_footer():
    """Print command footer."""
    print("-" * 80)
    print(f"  Completed: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 80)
    print()


def get_token_display_name(client: AnkrClient, contract: str, chain: str) -> str:
    """Get token display name (symbol or contract)."""
    metadata = client.get_token_metadata(contract, chain)
    if metadata:
        return f"{metadata.name} ({metadata.symbol})"
    return contract[:20] + "..."


def cmd_snapshot(contract: str, chain: str = "bsc"):
    """Create a holder snapshot."""
    with AnkrClient() as client:
        token_name = get_token_display_name(client, contract, chain)

    print_header(f"Holder Snapshot ({chain})", token_name)
    print(f"  Contract: {contract}")
    print(f"  Chain: {chain}")
    print()

    def progress(count):
        print(f"  Fetched {count} holders...", end="\r")

    snapshot = create_holders_snapshot(
        contract, chain, progress_callback=progress
    )

    print()
    print(f"  Token: {snapshot.get('token_name', 'Unknown')} ({snapshot.get('token_symbol', '???')})")
    print(f"  Total holders: {snapshot['holder_count']:,}")
    if snapshot.get("price_usd"):
        print(f"  Token price: ${snapshot['price_usd']:.6f}")

    print_footer()


def cmd_holders(contract: str, chain: str = "bsc", limit: int = 20):
    """Show top token holders."""
    with AnkrClient() as client:
        token_name = get_token_display_name(client, contract, chain)
        print_header(f"Top Holders ({chain})", token_name)
        print(f"  Contract: {contract}")
        print()

        holders, _ = client.get_token_holders(contract, chain, page_size=limit)
        price = client.get_token_price(contract, chain)

        print(f"  {'#':<4} {'Address':<44} {'Balance':<18} {'Label':<20}")
        print("  " + "-" * 86)

        for i, h in enumerate(holders[:limit], 1):
            balance = float(h.balance) if h.balance else 0
            label = h.label if h.label else ""
            addr_display = h.address[:42]
            print(f"  {i:<4} {addr_display:<44} {balance:>16,.2f}  {label:<20}")

        if price:
            print()
            print(f"  Token price: ${price:.6f}")

    print_footer()


def cmd_basic(contract: str, chain: str = "bsc"):
    """Get basic token info (fast, immediate data)."""
    with AnkrClient() as client:
        print_header(f"Token Info ({chain})")
        print(f"  Contract: {contract}")
        print()

        # Get metadata first (fast)
        metadata = client.get_token_metadata(contract, chain)
        if metadata:
            print(f"  Name: {metadata.name}")
            print(f"  Symbol: {metadata.symbol}")
            print(f"  Decimals: {metadata.decimals}")

        # Get price (fast)
        price = client.get_token_price(contract, chain)
        if price:
            print(f"  Price: ${price:.6f}")
        else:
            print("  Price: Not available")

        # Get top holder preview (fast - just 1 page)
        holders, _ = client.get_token_holders(contract, chain, page_size=5)
        if holders:
            print()
            print("  Top 5 Holders:")
            for i, h in enumerate(holders[:5], 1):
                balance = float(h.balance) if h.balance else 0
                label = f" ({h.label})" if h.label else ""
                print(f"    {i}. {h.address[:20]}... {balance:,.0f}{label}")

    print_footer()


def print_help():
    """Print usage help."""
    print("""
On-chain Monitor - Token Holder Analytics

Usage:
  onchain-monitor basic <contract> [chain]      Get basic token info (fast)
  onchain-monitor holders <contract> [chain]    Show top holders
  onchain-monitor snapshot <contract> [chain]   Create holder snapshot (slow)

Examples:
  onchain-monitor basic 0x000Ae314E2A2172a039B26378814C252734f556A bsc
  onchain-monitor holders 0xdAC17F958D2ee523a2206206994597C13D831ec7 eth
  onchain-monitor snapshot 0x0E09FaBB73Bd3Ade0a17ECC321fD13a19e81cE82 bsc

Supported chains: bsc, eth, polygon, arbitrum, base, avalanche
""")


def main():
    """Main entry point."""
    setup_logging()
    logger = logging.getLogger(__name__)

    if len(sys.argv) < 2:
        print_help()
        return

    command = sys.argv[1].lower()

    if command in ["help", "-h", "--help"]:
        print_help()
        return

    if len(sys.argv) < 3:
        print("Error: Contract address required")
        print_help()
        sys.exit(1)

    contract = sys.argv[2]
    chain = sys.argv[3] if len(sys.argv) > 3 else "bsc"

    if chain not in SUPPORTED_CHAINS:
        print(f"Error: Unsupported chain '{chain}'")
        print(f"Supported: {', '.join(SUPPORTED_CHAINS)}")
        sys.exit(1)

    logger.info(f"Running {command} for {contract} on {chain}")

    try:
        if command == "snapshot":
            cmd_snapshot(contract, chain)
        elif command == "holders":
            cmd_holders(contract, chain)
        elif command == "basic":
            cmd_basic(contract, chain)
        else:
            print(f"Unknown command: {command}")
            print_help()
            sys.exit(1)

    except Exception as e:
        logger.error(f"Command failed: {e}")
        print(f"\n  Error: {e}")
        print()
        sys.exit(1)


if __name__ == "__main__":
    main()
