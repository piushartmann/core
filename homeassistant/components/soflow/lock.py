"""Support for SoFlow Scooter locks."""

from __future__ import annotations

import asyncio
import logging
from typing import Any

from bleak_retry_connector import BleakError

from homeassistant.components.lock import LockEntity
from homeassistant.core import Event, HomeAssistant, callback
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback

from . import SoFlowConfigEntry
from .const import DOMAIN, WRITE_UUID

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: SoFlowConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    """Set up SoFlow Scooter lock."""
    async_add_entities([SoFlowLock(entry, hass)])


class SoFlowLock(LockEntity):
    """Representation of a SoFlow Scooter lock."""

    _attr_has_entity_name = True
    _attr_name = None

    def __init__(self, entry: SoFlowConfigEntry, hass: HomeAssistant) -> None:
        """Initialize the lock."""
        self._entry = entry
        self._hass = hass
        self._attr_unique_id = entry.entry_id
        self._attr_device_info = {
            "identifiers": {(DOMAIN, entry.entry_id)},
            "name": entry.title,
            "manufacturer": "SoFlow",
            "model": "Scooter",
        }

    async def async_added_to_hass(self) -> None:
        """Run when entity about to be added to hass."""
        await super().async_added_to_hass()

        @callback
        def _handle_event(event: Event) -> None:
            """Handle state update event."""
            if event.data.get("entry_id") == self._entry.entry_id:
                self.async_write_ha_state()

        self.async_on_remove(
            self._hass.bus.async_listen(f"{DOMAIN}_update", _handle_event)
        )

    @property
    def is_locked(self) -> bool | None:
        """Return true if lock is locked."""
        return self._entry.runtime_data.is_locked

    @property
    def available(self) -> bool:
        """Return True if entity is available."""
        return self._entry.runtime_data.client.is_connected

    async def async_lock(self, **kwargs: Any) -> None:
        """Lock the scooter."""
        data = self._entry.runtime_data
        try:
            await asyncio.wait_for(
                data.client.write_gatt_char(
                    WRITE_UUID, data.lock_packet, response=False
                ),
                timeout=30,
            )
            _LOGGER.debug("Lock command sent to SoFlow Scooter")
            # Update state optimistically
            data.is_locked = True
            self.async_write_ha_state()
        except (BleakError, asyncio.TimeoutError) as ex:
            _LOGGER.error("Failed to lock SoFlow Scooter: %s", ex)
            raise

    async def async_unlock(self, **kwargs: Any) -> None:
        """Unlock the scooter."""
        data = self._entry.runtime_data
        try:
            await asyncio.wait_for(
                data.client.write_gatt_char(
                    WRITE_UUID, data.unlock_packet, response=False
                ),
                timeout=30,
            )
            _LOGGER.debug("Unlock command sent to SoFlow Scooter")
            # Update state optimistically
            data.is_locked = False
            self.async_write_ha_state()
        except (BleakError, asyncio.TimeoutError) as ex:
            _LOGGER.error("Failed to unlock SoFlow Scooter: %s", ex)
            raise
