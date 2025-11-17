"""Fixtures for SoFlow Scooter integration tests."""

from collections.abc import Generator
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from homeassistant.components.soflow.const import DOMAIN

from tests.common import MockConfigEntry


@pytest.fixture
def mock_setup_entry() -> Generator[AsyncMock]:
    """Override async_setup_entry."""
    with patch(
        "homeassistant.components.soflow.async_setup_entry", return_value=True
    ) as mock_setup_entry:
        yield mock_setup_entry


@pytest.fixture
def mock_bleak_client() -> Generator[MagicMock]:
    """Mock a BleakClient."""
    with patch("homeassistant.components.soflow.BleakClient") as mock_client:
        client = mock_client.return_value
        client.is_connected = True
        client.connect = AsyncMock(return_value=True)
        client.disconnect = AsyncMock()
        client.write_gatt_char = AsyncMock()
        client.start_notify = AsyncMock()
        yield client


@pytest.fixture
def mock_config_entry() -> MockConfigEntry:
    """Mock a config entry."""
    return MockConfigEntry(
        domain=DOMAIN,
        title="SoFlow Scooter",
        data={
            "address": "4C:E1:00:00:1B:42",
            "auth_packet": "23FC5736B5ADD7E27578DA1BCC73E808",
            "lock_packet": "43C144561FA0120FC5E76218D24C6276",
            "unlock_packet": "B38487C1D81AB08639FC46BA2B06669E",
        },
        unique_id="4C:E1:00:00:1B:42",
    )
