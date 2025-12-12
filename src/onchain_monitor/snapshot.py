"""
Snapshot module for creating token holder snapshots.

Creates timestamped JSON files of token holder data for analysis.
"""

import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Optional

from onchain_monitor.ankr_client import AnkrClient, TokenHolder
from onchain_monitor.config import SNAPSHOT_DIR

logger = logging.getLogger(__name__)


def save_snapshot(data: dict, label: str, output_dir: Optional[Path] = None) -> Path:
    """
    Save a snapshot to a JSON file.

    Args:
        data: Snapshot data
        label: Label for the snapshot file
        output_dir: Output directory (defaults to SNAPSHOT_DIR)

    Returns:
        Path to the saved file
    """
    output_dir = output_dir or SNAPSHOT_DIR
    output_dir.mkdir(parents=True, exist_ok=True)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = output_dir / f"{label}_{timestamp}.json"

    with open(filename, "w") as f:
        json.dump(data, f, indent=2)

    logger.info(f"Snapshot saved: {filename}")
    return filename


def create_holders_snapshot(
    contract: str,
    blockchain: str = "bsc",
    client: Optional[AnkrClient] = None,
    progress_callback=None,
) -> dict:
    """
    Create a full snapshot of all token holders.

    Args:
        contract: Token contract address
        blockchain: Blockchain name
        client: Optional AnkrClient (creates one if not provided)
        progress_callback: Optional callback for progress updates

    Returns:
        Snapshot data dict
    """
    should_close = False
    if client is None:
        client = AnkrClient()
        should_close = True

    try:
        # Get holder count first
        holder_count = client.get_token_holders_count(contract, blockchain)
        logger.info(f"Token has {holder_count} holders")

        # Get token metadata
        metadata = client.get_token_metadata(contract, blockchain)
        token_name = metadata.name if metadata else "Unknown"
        token_symbol = metadata.symbol if metadata else "???"

        # Get all holders
        holders = client.get_all_holders(
            contract, blockchain, progress_callback=progress_callback
        )

        # Get token price
        price = client.get_token_price(contract, blockchain)

        # Build snapshot with token info and labels
        snapshot = {
            "timestamp": datetime.now().isoformat(),
            "contract": contract,
            "blockchain": blockchain,
            "token_name": token_name,
            "token_symbol": token_symbol,
            "holder_count": len(holders),
            "price_usd": price,
            "holders": [
                {
                    "address": h.address,
                    "balance": h.balance,
                    "balance_raw": h.balance_raw,
                    "label": h.label,
                }
                for h in holders
            ],
        }

        # Save snapshot
        save_snapshot(snapshot, f"holders_{blockchain}")

        return snapshot

    finally:
        if should_close:
            client.close()


def load_snapshot(filepath: Path) -> dict:
    """Load a snapshot from a JSON file."""
    with open(filepath) as f:
        return json.load(f)


def compare_snapshots(old: dict, new: dict) -> dict:
    """
    Compare two snapshots to find changes.

    Returns:
        Dict with new_holders, removed_holders, and balance_changes
    """
    old_addresses = {h["address"]: h for h in old.get("holders", [])}
    new_addresses = {h["address"]: h for h in new.get("holders", [])}

    new_holders = [new_addresses[a] for a in new_addresses if a not in old_addresses]
    removed_holders = [old_addresses[a] for a in old_addresses if a not in new_addresses]

    balance_changes = []
    for addr in set(old_addresses.keys()) & set(new_addresses.keys()):
        old_bal = old_addresses[addr]["balance"]
        new_bal = new_addresses[addr]["balance"]
        if old_bal != new_bal:
            balance_changes.append({
                "address": addr,
                "old_balance": old_bal,
                "new_balance": new_bal,
            })

    return {
        "new_holders": new_holders,
        "removed_holders": removed_holders,
        "balance_changes": balance_changes,
    }
