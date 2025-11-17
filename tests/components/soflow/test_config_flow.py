"""Test the SoFlow Scooter config flow."""

from unittest.mock import AsyncMock, patch

import pytest

from homeassistant import config_entries
from homeassistant.components.soflow.const import DOMAIN
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResultType

from tests.common import MockConfigEntry


async def test_user_step_no_devices_found(hass: HomeAssistant) -> None:
    """Test user step with no devices found."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )

    assert result["type"] is FlowResultType.ABORT
    assert result["reason"] == "no_devices_found"


async def test_form_user_with_valid_device(
    hass: HomeAssistant, mock_config_entry: MockConfigEntry
) -> None:
    """Test we get the form with valid device."""
    with (
        patch(
            "homeassistant.components.soflow.config_flow.async_discovered_service_info",
            return_value=[
                type(
                    "MockServiceInfo",
                    (),
                    {
                        "name": "SoFlow Scooter",
                        "address": "4C:E1:00:00:1B:42",
                        "service_uuids": ["43480003-f001-4b49-4e47-204d45544552"],
                    },
                )()
            ],
        ),
    ):
        result = await hass.config_entries.flow.async_init(
            DOMAIN, context={"source": config_entries.SOURCE_USER}
        )

        assert result["type"] is FlowResultType.FORM
        assert result["step_id"] == "user"


async def test_form_packets_invalid_hex(hass: HomeAssistant) -> None:
    """Test we handle invalid hex format."""
    with patch(
        "homeassistant.components.soflow.config_flow.async_discovered_service_info",
        return_value=[
            type(
                "MockServiceInfo",
                (),
                {
                    "name": "SoFlow Scooter",
                    "address": "4C:E1:00:00:1B:42",
                    "service_uuids": ["43480003-f001-4b49-4e47-204d45544552"],
                    "device": None,
                },
            )()
        ],
    ):
        result = await hass.config_entries.flow.async_init(
            DOMAIN, context={"source": config_entries.SOURCE_USER}
        )

        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {"address": "4C:E1:00:00:1B:42"},
        )

        assert result["type"] is FlowResultType.FORM
        assert result["step_id"] == "packets"

        # Test invalid hex
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {
                "auth_packet": "INVALID_HEX",
                "lock_packet": "43C144561FA0120FC5E76218D24C6276",
                "unlock_packet": "B38487C1D81AB08639FC46BA2B06669E",
            },
        )

        assert result["type"] is FlowResultType.FORM
        assert result["errors"] == {"base": "invalid_packet_format"}


async def test_form_packets_create_entry(hass: HomeAssistant) -> None:
    """Test we can create an entry."""
    mock_device = type("MockDevice", (), {"address": "4C:E1:00:00:1B:42"})()

    with (
        patch(
            "homeassistant.components.soflow.config_flow.async_discovered_service_info",
            return_value=[
                type(
                    "MockServiceInfo",
                    (),
                    {
                        "name": "SoFlow Scooter",
                        "address": "4C:E1:00:00:1B:42",
                        "service_uuids": ["43480003-f001-4b49-4e47-204d45544552"],
                        "device": mock_device,
                    },
                )()
            ],
        ),
        patch(
            "homeassistant.components.soflow.config_flow.BleakClient"
        ) as mock_client_class,
    ):
        mock_client = mock_client_class.return_value
        mock_client.is_connected = True
        mock_client.connect = AsyncMock()
        mock_client.disconnect = AsyncMock()

        result = await hass.config_entries.flow.async_init(
            DOMAIN, context={"source": config_entries.SOURCE_USER}
        )

        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {"address": "4C:E1:00:00:1B:42"},
        )

        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {
                "auth_packet": "23FC5736B5ADD7E27578DA1BCC73E808",
                "lock_packet": "43C144561FA0120FC5E76218D24C6276",
                "unlock_packet": "B38487C1D81AB08639FC46BA2B06669E",
            },
        )

        assert result["type"] is FlowResultType.CREATE_ENTRY
        assert result["title"] == "SoFlow Scooter"
        assert result["data"] == {
            "address": "4C:E1:00:00:1B:42",
            "auth_packet": "23FC5736B5ADD7E27578DA1BCC73E808",
            "lock_packet": "43C144561FA0120FC5E76218D24C6276",
            "unlock_packet": "B38487C1D81AB08639FC46BA2B06669E",
        }
