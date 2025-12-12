"""
Configuration module for On-chain Monitor.

Contains API settings, token configurations, and runtime constants.
"""

import os
from pathlib import Path

from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# =============================================================================
# API Configuration
# =============================================================================

ANKR_API_KEY = os.getenv("ANKR_API_KEY", "")
ANKR_RPC_URL = os.getenv(
    "ANKR_RPC_URL",
    f"https://rpc.ankr.com/multichain/{ANKR_API_KEY}" if ANKR_API_KEY else "https://rpc.ankr.com/multichain"
)

# =============================================================================
# Logging Configuration
# =============================================================================

LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
LOG_FILE = Path("logs/onchain_monitor.log")

# =============================================================================
# Supported Blockchains
# =============================================================================

SUPPORTED_CHAINS = ["bsc", "eth", "polygon", "arbitrum", "base", "avalanche"]

# =============================================================================
# Example Token Contracts (customize in .env or pass as argument)
# =============================================================================

EXAMPLE_TOKENS = {
    "bsc": {
        "ASTER": "0x000Ae314E2A2172a039B26378814C252734f556A",
        "CAKE": "0x0E09FaBB73Bd3Ade0a17ECC321fD13a19e81cE82",
    },
    "eth": {
        "USDT": "0xdAC17F958D2ee523a2206206994597C13D831ec7",
        "USDC": "0xA0b86991c6218b36c1d19D4a2e9Eb0cE3606eb48",
    },
}

# =============================================================================
# Scanner Settings
# =============================================================================

REQUEST_TIMEOUT = 30  # seconds (Ankr can be slow for large queries)
PAGE_SIZE = 10000  # Max holders per page
SNAPSHOT_DIR = Path("snapshots")
