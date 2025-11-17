"""The SoFlow Scooter integration."""

from __future__ import annotations

import asyncio
import logging

from bleak import BleakClient
from bleak_retry_connector import (
    BleakError,
    establish_connection,
)

from homeassistant.components import bluetooth
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_ADDRESS, EVENT_HOMEASSISTANT_STOP, Platform
from homeassistant.core import Event, HomeAssistant, callback
from homeassistant.exceptions import ConfigEntryNotReady

from .const import (
    CONF_AUTH_PACKET,
    CONF_LOCK_PACKET,
    CONF_UNLOCK_PACKET,
    DEVICE_TIMEOUT,
    DOMAIN,
    NOTIFY_UUID,
    WRITE_UUID,
)
from .models import SoFlowData

type SoFlowConfigEntry = ConfigEntry[SoFlowData]

PLATFORMS: list[Platform] = [Platform.LOCK]

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(hass: HomeAssistant, entry: SoFlowConfigEntry) -> bool:
    """Set up SoFlow Scooter from a config entry."""
    address = entry.data[CONF_ADDRESS]
    auth_packet = bytes.fromhex(entry.data[CONF_AUTH_PACKET])
    lock_packet = bytes.fromhex(entry.data[CONF_LOCK_PACKET])
    unlock_packet = bytes.fromhex(entry.data[CONF_UNLOCK_PACKET])

    # Get BLE device
    ble_device = bluetooth.async_ble_device_from_address(
        hass, address, connectable=True
    )
    if not ble_device:
        raise ConfigEntryNotReady(f"Could not find SoFlow Scooter with address {address}")

    # Establish connection
    try:
        client = await establish_connection(
            BleakClient,
            ble_device,
            ble_device.address,
            disconnected_callback=lambda _: _LOGGER.info("SoFlow Scooter disconnected"),
            max_attempts=3,
        )
    except (BleakError, asyncio.TimeoutError) as ex:
        raise ConfigEntryNotReady(f"Could not connect to SoFlow Scooter: {ex}") from ex

    # Authenticate with the scooter
    try:
        await asyncio.wait_for(
            client.write_gatt_char(WRITE_UUID, auth_packet, response=False),
            timeout=DEVICE_TIMEOUT,
        )
        _LOGGER.debug("Authentication packet sent to SoFlow Scooter")
    except (BleakError, asyncio.TimeoutError) as ex:
        await client.disconnect()
        raise ConfigEntryNotReady(f"Failed to authenticate with SoFlow Scooter: {ex}") from ex

    # Store runtime data
    entry.runtime_data = SoFlowData(
        title=entry.title,
        client=client,
        auth_packet=auth_packet,
        lock_packet=lock_packet,
        unlock_packet=unlock_packet,
    )

    # Set up notification handler
    def _notification_handler(sender: int, data: bytearray) -> None:
        """Handle notifications from the scooter."""
        if len(data) >= 9:
            lock_status_byte = data[8]
            from .const import LOCK_STATUS_LOCKED, LOCK_STATUS_UNLOCKED

            if lock_status_byte == LOCK_STATUS_UNLOCKED:
                entry.runtime_data.is_locked = False
                _LOGGER.debug("SoFlow Scooter status: Unlocked")
            elif lock_status_byte == LOCK_STATUS_LOCKED:
                entry.runtime_data.is_locked = True
                _LOGGER.debug("SoFlow Scooter status: Locked")
            else:
                _LOGGER.debug("SoFlow Scooter status: Unknown (%02X)", lock_status_byte)

            # Trigger entity state update
            hass.bus.async_fire(
                f"{DOMAIN}_update",
                {"entry_id": entry.entry_id},
            )

    try:
        await client.start_notify(NOTIFY_UUID, _notification_handler)
        _LOGGER.debug("Notifications enabled for SoFlow Scooter")
    except BleakError as ex:
        _LOGGER.warning("Failed to enable notifications: %s", ex)

    @callback
    def _async_shutdown(event: Event | None = None) -> None:
        """Disconnect on shutdown."""
        hass.async_create_task(_disconnect_client())

    async def _disconnect_client() -> None:
        """Disconnect the client."""
        try:
            if client.is_connected:
                await client.disconnect()
                _LOGGER.info("SoFlow Scooter disconnected")
        except Exception as ex:  # noqa: BLE001
            _LOGGER.error("Error disconnecting SoFlow Scooter: %s", ex)

    entry.async_on_unload(
        hass.bus.async_listen_once(EVENT_HOMEASSISTANT_STOP, _async_shutdown)
    )

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    return True


async def async_unload_entry(hass: HomeAssistant, entry: SoFlowConfigEntry) -> bool:
    """Unload a config entry."""
    if unload_ok := await hass.config_entries.async_unload_platforms(entry, PLATFORMS):
        client = entry.runtime_data.client
        if client.is_connected:
            await client.disconnect()
            _LOGGER.info("SoFlow Scooter disconnected")
    return unload_ok
