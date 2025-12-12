"""
Ankr API client for on-chain token analytics.

Provides methods for:
- Token holder queries
- Wallet balances
- Token prices
- Transfer history
"""

import logging
from dataclasses import dataclass
from typing import Any, Optional

import httpx

from onchain_monitor.config import ANKR_RPC_URL, PAGE_SIZE, REQUEST_TIMEOUT

logger = logging.getLogger(__name__)


@dataclass
class TokenHolder:
    """Represents a token holder."""

    address: str
    balance: str
    balance_raw: str
    label: str = ""  # Known label (exchange, burn, etc.)


@dataclass
class TokenMetadata:
    """Represents token metadata."""

    contract: str
    blockchain: str
    name: str
    symbol: str
    decimals: int


@dataclass
class TokenInfo:
    """Represents token information."""

    contract: str
    blockchain: str
    holder_count: int
    price_usd: Optional[float] = None
    name: str = ""
    symbol: str = ""


# Known wallet labels (exchanges, burn addresses, etc.)
KNOWN_LABELS = {
    "0x000000000000000000000000000000000000dEaD": "Burn Address",
    "0x0000000000000000000000000000000000000000": "Null Address",
    # Binance
    "0xF977814e90dA44bFA03b6295A0616a897441aceC": "Binance Hot Wallet",
    "0x8894E0a0c962CB723c1976a4421c95949bE2D4E3": "Binance",
    "0xe2fc31F816A9b94326492132018C3aEcC4a93aE1": "Binance",
    "0x3c783c21a0383057D128bae431894a5C19F9Cf06": "Binance",
    # OKX
    "0x5a52E96BAcdaBb82fd05763E25335261B270Efcb": "OKX",
    "0x6cC5F688a315f3dC28A7781717a9A798a59fDA7b": "OKX",
    # Other exchanges
    "0x28C6c06298d514Db089934071355E5743bf21d60": "Binance 14",
    "0x21a31Ee1afC51d94C2eFcCAa2092aD1028285549": "Bybit",
}


def get_holder_label(address: str) -> str:
    """Get label for a known address."""
    return KNOWN_LABELS.get(address, KNOWN_LABELS.get(address.lower(), ""))


class AnkrClient:
    """
    Client for Ankr Token API.

    Provides methods for querying token data via JSON-RPC.
    """

    def __init__(self, rpc_url: Optional[str] = None):
        """Initialize the Ankr client."""
        self.rpc_url = rpc_url or ANKR_RPC_URL
        self._client: Optional[httpx.Client] = None
        self._request_id = 0

    def _get_client(self) -> httpx.Client:
        """Get or create HTTP client."""
        if self._client is None:
            self._client = httpx.Client(
                headers={"Content-Type": "application/json"},
                timeout=REQUEST_TIMEOUT,
            )
        return self._client

    def close(self):
        """Close the HTTP client."""
        if self._client:
            self._client.close()
            self._client = None

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()

    def _call(self, method: str, params: dict[str, Any]) -> dict[str, Any]:
        """Make a JSON-RPC call to Ankr API."""
        self._request_id += 1
        payload = {
            "id": self._request_id,
            "jsonrpc": "2.0",
            "method": method,
            "params": params,
        }

        client = self._get_client()
        response = client.post(self.rpc_url, json=payload)
        response.raise_for_status()

        data = response.json()
        if "error" in data:
            logger.error(f"Ankr API error: {data['error']}")
            raise ValueError(f"Ankr API error: {data['error']}")

        return data.get("result", {})

    def get_token_holders_count(self, contract: str, blockchain: str = "bsc") -> int:
        """
        Get the number of token holders.

        Args:
            contract: Token contract address
            blockchain: Blockchain name (bsc, eth, polygon, etc.)

        Returns:
            Number of token holders
        """
        result = self._call(
            "ankr_getTokenHoldersCount",
            {"blockchain": blockchain, "contractAddress": contract},
        )
        return int(result.get("holderCount", 0))

    def get_token_holders(
        self,
        contract: str,
        blockchain: str = "bsc",
        page_size: int = PAGE_SIZE,
        page_token: Optional[str] = None,
    ) -> tuple[list[TokenHolder], Optional[str]]:
        """
        Get a page of token holders.

        Args:
            contract: Token contract address
            blockchain: Blockchain name
            page_size: Number of holders per page
            page_token: Pagination token

        Returns:
            Tuple of (holders list, next page token)
        """
        params = {
            "blockchain": blockchain,
            "contractAddress": contract,
            "pageSize": page_size,
        }
        if page_token:
            params["pageToken"] = page_token

        result = self._call("ankr_getTokenHolders", params)

        holders = [
            TokenHolder(
                address=h.get("holderAddress", ""),
                balance=h.get("balance", "0"),
                balance_raw=h.get("balanceRawInteger", "0"),
                label=get_holder_label(h.get("holderAddress", "")),
            )
            for h in result.get("holders", [])
        ]

        next_token = result.get("nextPageToken")
        return holders, next_token

    def get_all_holders(
        self, contract: str, blockchain: str = "bsc", progress_callback=None
    ) -> list[TokenHolder]:
        """
        Get all token holders with pagination.

        Args:
            contract: Token contract address
            blockchain: Blockchain name
            progress_callback: Optional callback(count) for progress updates

        Returns:
            List of all token holders
        """
        all_holders = []
        page_token = None

        while True:
            holders, page_token = self.get_token_holders(
                contract, blockchain, page_token=page_token
            )
            all_holders.extend(holders)

            if progress_callback:
                progress_callback(len(all_holders))

            if not page_token or not holders:
                break

        return all_holders

    def get_token_price(self, contract: str, blockchain: str = "bsc") -> Optional[float]:
        """
        Get token price in USD.

        Args:
            contract: Token contract address
            blockchain: Blockchain name

        Returns:
            Price in USD or None if not available
        """
        try:
            result = self._call(
                "ankr_getTokenPrice",
                {"blockchain": blockchain, "contractAddress": contract},
            )
            return float(result.get("usdPrice", 0))
        except Exception as e:
            logger.warning(f"Could not fetch token price: {e}")
            return None

    def get_account_balance(
        self, wallet: str, blockchain: str = "bsc", only_whitelisted: bool = False
    ) -> list[dict[str, Any]]:
        """
        Get token balances for a wallet.

        Args:
            wallet: Wallet address
            blockchain: Blockchain name
            only_whitelisted: Only return whitelisted tokens

        Returns:
            List of token balances
        """
        result = self._call(
            "ankr_getAccountBalance",
            {
                "blockchain": blockchain,
                "walletAddress": wallet,
                "onlyWhitelisted": only_whitelisted,
            },
        )
        return result.get("assets", [])

    def get_token_transfers(
        self,
        address: str,
        blockchain: str = "bsc",
        contract: Optional[str] = None,
        page_size: int = 10,
    ) -> list[dict[str, Any]]:
        """
        Get recent token transfers for an address.

        Args:
            address: Wallet address
            blockchain: Blockchain name
            contract: Optional token contract filter
            page_size: Number of transfers to return

        Returns:
            List of transfers
        """
        params = {
            "address": [address],
            "blockchain": blockchain,
            "descOrder": True,
            "pageSize": page_size,
        }
        if contract:
            params["contractAddress"] = contract

        result = self._call("ankr_getTokenTransfers", params)
        return result.get("transfers", [])

    def get_token_metadata(
        self, contract: str, blockchain: str = "bsc"
    ) -> Optional[TokenMetadata]:
        """
        Get token metadata (name, symbol, decimals).

        Args:
            contract: Token contract address
            blockchain: Blockchain name

        Returns:
            TokenMetadata or None if not available
        """
        try:
            result = self._call(
                "ankr_getCurrencies",
                {"blockchain": blockchain},
            )

            # Find the token in currencies list
            for currency in result.get("currencies", []):
                if currency.get("address", "").lower() == contract.lower():
                    return TokenMetadata(
                        contract=contract,
                        blockchain=blockchain,
                        name=currency.get("name", "Unknown"),
                        symbol=currency.get("symbol", "???"),
                        decimals=int(currency.get("decimals", 18)),
                    )

            # If not found, try to get from account balance (fallback)
            logger.debug(f"Token {contract} not in currencies, trying balance lookup")
            return None

        except Exception as e:
            logger.warning(f"Could not fetch token metadata: {e}")
            return None

