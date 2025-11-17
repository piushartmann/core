"""Config flow for SoFlow Scooter integration."""

from __future__ import annotations

import logging
from typing import Any

from bleak import BleakClient
from bleak_retry_connector import BleakError
import voluptuous as vol

from homeassistant.components.bluetooth import (
    BluetoothServiceInfoBleak,
    async_discovered_service_info,
)
from homeassistant.config_entries import ConfigFlow, ConfigFlowResult
from homeassistant.const import CONF_ADDRESS

from .const import (
    CONF_AUTH_PACKET,
    CONF_LOCK_PACKET,
    CONF_UNLOCK_PACKET,
    DOMAIN,
    NOTIFY_UUID,
)

_LOGGER = logging.getLogger(__name__)


class SoFlowConfigFlow(ConfigFlow, domain=DOMAIN):
    """Handle a config flow for SoFlow Scooter."""

    VERSION = 1

    def __init__(self) -> None:
        """Initialize the config flow."""
        self._discovery_info: BluetoothServiceInfoBleak | None = None
        self._discovered_devices: dict[str, BluetoothServiceInfoBleak] = {}

    async def async_step_bluetooth(
        self, discovery_info: BluetoothServiceInfoBleak
    ) -> ConfigFlowResult:
        """Handle bluetooth discovery step."""
        await self.async_set_unique_id(discovery_info.address)
        self._abort_if_unique_id_configured()
        self._discovery_info = discovery_info
        return await self.async_step_user()

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Handle the user step to pick discovered device."""
        errors: dict[str, str] = {}

        if user_input is not None:
            address = user_input[CONF_ADDRESS]
            self._discovery_info = self._discovered_devices[address]
            return await self.async_step_packets()

        current_addresses = self._async_current_ids()
        for discovery_info in async_discovered_service_info(self.hass):
            if (
                discovery_info.address in current_addresses
                or discovery_info.address in self._discovered_devices
            ):
                continue
            # Check if device has the notify UUID
            if NOTIFY_UUID.lower() in [
                str(service).lower() for service in discovery_info.service_uuids
            ]:
                self._discovered_devices[discovery_info.address] = discovery_info

        if not self._discovered_devices:
            return self.async_abort(reason="no_devices_found")

        data_schema = vol.Schema(
            {
                vol.Required(CONF_ADDRESS): vol.In(
                    {
                        service_info.address: f"{service_info.name} ({service_info.address})"
                        for service_info in self._discovered_devices.values()
                    }
                )
            }
        )
        return self.async_show_form(
            step_id="user",
            data_schema=data_schema,
            errors=errors,
        )

    async def async_step_packets(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Handle the packets configuration step."""
        errors: dict[str, str] = {}

        if user_input is not None:
            # Validate hex format
            try:
                auth_packet = user_input[CONF_AUTH_PACKET].replace(" ", "")
                lock_packet = user_input[CONF_LOCK_PACKET].replace(" ", "")
                unlock_packet = user_input[CONF_UNLOCK_PACKET].replace(" ", "")

                # Validate hex strings
                bytes.fromhex(auth_packet)
                bytes.fromhex(lock_packet)
                bytes.fromhex(unlock_packet)

                # Test connection
                assert self._discovery_info is not None
                try:
                    client = BleakClient(self._discovery_info.device)
                    await client.connect()
                    if not client.is_connected:
                        errors["base"] = "cannot_connect"
                    else:
                        await client.disconnect()
                except BleakError:
                    errors["base"] = "cannot_connect"
                except Exception:
                    _LOGGER.exception("Unexpected error")
                    errors["base"] = "unknown"

                if not errors:
                    await self.async_set_unique_id(
                        self._discovery_info.address, raise_on_progress=False
                    )
                    self._abort_if_unique_id_configured()

                    return self.async_create_entry(
                        title=self._discovery_info.name or "SoFlow Scooter",
                        data={
                            CONF_ADDRESS: self._discovery_info.address,
                            CONF_AUTH_PACKET: auth_packet,
                            CONF_LOCK_PACKET: lock_packet,
                            CONF_UNLOCK_PACKET: unlock_packet,
                        },
                    )
            except ValueError:
                errors["base"] = "invalid_packet_format"

        assert self._discovery_info is not None
        data_schema = vol.Schema(
            {
                vol.Required(CONF_AUTH_PACKET, default="23FC5736B5ADD7E27578DA1BCC73E808"): str,
                vol.Required(CONF_LOCK_PACKET, default="43C144561FA0120FC5E76218D24C6276"): str,
                vol.Required(CONF_UNLOCK_PACKET, default="B38487C1D81AB08639FC46BA2B06669E"): str,
            }
        )

        return self.async_show_form(
            step_id="packets",
            data_schema=data_schema,
            errors=errors,
            description_placeholders={
                "name": self._discovery_info.name or "SoFlow Scooter",
                "address": self._discovery_info.address,
            },
        )
