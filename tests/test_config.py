"""
Tests for the config module.
"""

from onchain_monitor import config


def test_supported_chains_exist():
    """Test that supported chains are defined."""
    assert hasattr(config, "SUPPORTED_CHAINS")
    assert len(config.SUPPORTED_CHAINS) > 0
    assert "bsc" in config.SUPPORTED_CHAINS
    assert "eth" in config.SUPPORTED_CHAINS


def test_ankr_rpc_url():
    """Test that Ankr RPC URL is defined."""
    assert hasattr(config, "ANKR_RPC_URL")
    assert "ankr.com" in config.ANKR_RPC_URL


def test_snapshot_dir():
    """Test that snapshot directory is defined."""
    assert hasattr(config, "SNAPSHOT_DIR")


def test_request_timeout_positive():
    """Test that request timeout is positive."""
    assert config.REQUEST_TIMEOUT > 0
