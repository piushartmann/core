"""Constants for the SoFlow Scooter integration."""

from typing import Final

DOMAIN: Final = "soflow"

# Bluetooth UUIDs
WRITE_UUID: Final = "43480002-f001-4b49-4e47-204d45544552"
NOTIFY_UUID: Final = "43480003-f001-4b49-4e47-204d45544552"

# Configuration keys
CONF_AUTH_PACKET: Final = "auth_packet"
CONF_LOCK_PACKET: Final = "lock_packet"
CONF_UNLOCK_PACKET: Final = "unlock_packet"

# Lock status bytes from King-Meter telemetry
LOCK_STATUS_UNLOCKED: Final = 0x0C
LOCK_STATUS_LOCKED: Final = 0x0F

# Timeout for device connection
DEVICE_TIMEOUT: Final = 30
