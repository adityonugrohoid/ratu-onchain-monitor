"""
Tests for AnkrClient API methods with mocked RPC responses.

These tests verify API method logic without making real network requests.
"""

from unittest.mock import MagicMock, patch

import httpx
import pytest

from onchain_monitor.ankr_client import (
    AnkrClient,
    TokenHolder,
    TokenMetadata,
    get_holder_label,
)


class TestGetHolderLabel:
    """Tests for get_holder_label function."""

    def test_known_burn_address(self):
        """Test that burn address returns correct label."""
        result = get_holder_label("0x000000000000000000000000000000000000dEaD")
        assert result == "Burn Address"

    def test_unknown_address(self):
        """Test that unknown address returns empty string."""
        result = get_holder_label("0x1234567890abcdef1234567890abcdef12345678")
        assert result == ""


class TestAnkrClientGetTokenHoldersCount:
    """Tests for get_token_holders_count method."""

    def test_get_token_holders_count_mocked(self, mock_contract):
        """Test get_token_holders_count with mocked response."""
        mock_rpc_response = {"holderCount": 12500}

        with patch.object(AnkrClient, "_call", return_value=mock_rpc_response):
            client = AnkrClient()
            result = client.get_token_holders_count(mock_contract, blockchain="bsc")

            assert result == 12500
            client.close()

    def test_get_token_holders_count_zero(self, mock_contract):
        """Test get_token_holders_count returns 0 when no holders."""
        mock_rpc_response = {}

        with patch.object(AnkrClient, "_call", return_value=mock_rpc_response):
            client = AnkrClient()
            result = client.get_token_holders_count(mock_contract)

            assert result == 0
            client.close()


class TestAnkrClientGetTokenHolders:
    """Tests for get_token_holders method."""

    def test_get_token_holders_mocked(self, mock_contract):
        """Test get_token_holders with mocked response."""
        mock_rpc_response = {
            "holders": [
                {
                    "holderAddress": "0xHolder1",
                    "balance": "1000.5",
                    "balanceRawInteger": "1000500000000000000000",
                },
                {
                    "holderAddress": "0xHolder2",
                    "balance": "500.25",
                    "balanceRawInteger": "500250000000000000000",
                },
            ],
            "nextPageToken": "page2token",
        }

        with patch.object(AnkrClient, "_call", return_value=mock_rpc_response):
            client = AnkrClient()
            holders, next_token = client.get_token_holders(mock_contract)

            assert len(holders) == 2
            assert isinstance(holders[0], TokenHolder)
            assert holders[0].address == "0xHolder1"
            assert holders[0].balance == "1000.5"
            assert next_token == "page2token"
            client.close()

    def test_get_token_holders_empty(self, mock_contract):
        """Test get_token_holders returns empty list when no holders."""
        mock_rpc_response = {"holders": [], "nextPageToken": None}

        with patch.object(AnkrClient, "_call", return_value=mock_rpc_response):
            client = AnkrClient()
            holders, next_token = client.get_token_holders(mock_contract)

            assert len(holders) == 0
            assert next_token is None
            client.close()


class TestAnkrClientGetTokenPrice:
    """Tests for get_token_price method."""

    def test_get_token_price_mocked(self, mock_contract):
        """Test get_token_price with mocked response."""
        mock_rpc_response = {"usdPrice": 0.0025}

        with patch.object(AnkrClient, "_call", return_value=mock_rpc_response):
            client = AnkrClient()
            result = client.get_token_price(mock_contract)

            assert result == 0.0025
            client.close()

    def test_get_token_price_error_returns_none(self, mock_contract):
        """Test get_token_price returns None on error."""
        with patch.object(AnkrClient, "_call", side_effect=Exception("RPC Error")):
            client = AnkrClient()
            result = client.get_token_price(mock_contract)

            assert result is None
            client.close()


class TestAnkrClientGetAccountBalance:
    """Tests for get_account_balance method."""

    def test_get_account_balance_mocked(self, mock_wallet):
        """Test get_account_balance with mocked response."""
        mock_rpc_response = {
            "assets": [
                {"tokenSymbol": "BNB", "balance": "1.5"},
                {"tokenSymbol": "USDT", "balance": "100.0"},
            ]
        }

        with patch.object(AnkrClient, "_call", return_value=mock_rpc_response):
            client = AnkrClient()
            result = client.get_account_balance(mock_wallet)

            assert len(result) == 2
            assert result[0]["tokenSymbol"] == "BNB"
            client.close()


class TestAnkrClientGetTokenTransfers:
    """Tests for get_token_transfers method."""

    def test_get_token_transfers_mocked(self, mock_wallet):
        """Test get_token_transfers with mocked response."""
        mock_rpc_response = {
            "transfers": [
                {"from": "0xSender", "to": mock_wallet, "value": "100"},
                {"from": mock_wallet, "to": "0xReceiver", "value": "50"},
            ]
        }

        with patch.object(AnkrClient, "_call", return_value=mock_rpc_response):
            client = AnkrClient()
            result = client.get_token_transfers(mock_wallet)

            assert len(result) == 2
            assert result[0]["from"] == "0xSender"
            client.close()


class TestAnkrClientCallMethod:
    """Tests for _call RPC method."""

    def test_call_rpc_error_raises_exception(self):
        """Test that RPC errors raise ValueError."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"error": {"message": "Invalid request"}}
        mock_response.raise_for_status = MagicMock()

        with patch.object(AnkrClient, "_get_client") as mock_get_client:
            mock_client = MagicMock()
            mock_client.post.return_value = mock_response
            mock_get_client.return_value = mock_client

            client = AnkrClient()
            with pytest.raises(ValueError, match="Ankr API error"):
                client._call("test_method", {})
            client.close()

    def test_call_http_error(self):
        """Test that HTTP errors are raised."""
        with patch.object(AnkrClient, "_get_client") as mock_get_client:
            mock_client = MagicMock()
            mock_client.post.side_effect = httpx.HTTPStatusError(
                "Server Error", request=MagicMock(), response=MagicMock()
            )
            mock_get_client.return_value = mock_client

            client = AnkrClient()
            with pytest.raises(httpx.HTTPStatusError):
                client._call("test_method", {})
            client.close()


class TestAnkrClientGetTokenMetadata:
    """Tests for get_token_metadata method."""

    def test_get_token_metadata_found(self, mock_contract):
        """Test get_token_metadata when token is found."""
        mock_rpc_response = {
            "currencies": [
                {
                    "address": mock_contract,
                    "name": "Test Token",
                    "symbol": "TEST",
                    "decimals": 18,
                }
            ]
        }

        with patch.object(AnkrClient, "_call", return_value=mock_rpc_response):
            client = AnkrClient()
            result = client.get_token_metadata(mock_contract)

            assert result is not None
            assert isinstance(result, TokenMetadata)
            assert result.name == "Test Token"
            assert result.symbol == "TEST"
            client.close()

    def test_get_token_metadata_not_found(self, mock_contract):
        """Test get_token_metadata returns None when token not found."""
        mock_rpc_response = {"currencies": []}

        with patch.object(AnkrClient, "_call", return_value=mock_rpc_response):
            client = AnkrClient()
            result = client.get_token_metadata(mock_contract)

            assert result is None
            client.close()
