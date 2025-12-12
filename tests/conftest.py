"""
Pytest configuration and shared fixtures.
"""

import pytest


@pytest.fixture
def mock_contract():
    """Provide a mock contract address."""
    return "0x000Ae314E2A2172a039B26378814C252734f556A"


@pytest.fixture
def mock_wallet():
    """Provide a mock wallet address."""
    return "0xE8c3e6559513eEbAc3e05fd75c19a17F4A51A892"
