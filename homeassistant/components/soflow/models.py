"""Models for the SoFlow Scooter integration."""

from __future__ import annotations

from dataclasses import dataclass

from bleak import BleakClient


@dataclass
class SoFlowData:
    """Data for the SoFlow integration."""

    title: str
    client: BleakClient
    auth_packet: bytes
    lock_packet: bytes
    unlock_packet: bytes
    is_locked: bool | None = None
