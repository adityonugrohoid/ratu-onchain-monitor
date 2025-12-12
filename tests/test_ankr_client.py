"""
Tests for the Ankr client module.
"""

from onchain_monitor.ankr_client import AnkrClient, TokenHolder


def test_token_holder_dataclass():
    """Test TokenHolder dataclass creation."""
    holder = TokenHolder(
        address="0x1234567890abcdef",
        balance="1000.5",
        balance_raw="1000500000000000000000",
    )
    assert holder.address == "0x1234567890abcdef"
    assert holder.balance == "1000.5"


def test_ankr_client_creation():
    """Test AnkrClient can be created."""
    client = AnkrClient()
    assert client.rpc_url is not None
    client.close()


def test_ankr_client_context_manager():
    """Test AnkrClient context manager."""
    with AnkrClient() as client:
        assert client.rpc_url is not None
