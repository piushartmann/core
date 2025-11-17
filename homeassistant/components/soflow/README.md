# SoFlow Scooter Integration

This Home Assistant integration allows you to control your SoFlow electric scooter via Bluetooth Low Energy (BLE).

## Features

- Lock and unlock your scooter remotely
- Real-time lock status monitoring via BLE notifications
- Automatic device discovery via Bluetooth

## Prerequisites

- Home Assistant with Bluetooth support
- SoFlow electric scooter with BLE support
- Authentication packets specific to your scooter (obtained from BLE sniffing tools)

## Installation

1. Ensure your Home Assistant instance has Bluetooth adapters configured
2. Add this integration through the Home Assistant UI
3. Select your SoFlow Scooter from the discovered devices
4. Enter your device-specific authentication packets:
   - Authentication packet (hex)
   - Lock packet (hex)
   - Unlock packet (hex)

## Configuration

### Obtaining Authentication Packets

The authentication packets are unique to each scooter. You'll need to capture them using a BLE sniffing tool:

1. Use a BLE packet sniffer (like nRF Connect, Wireshark with BLE adapter, or similar)
2. Capture the packets when authenticating with your scooter using the official app
3. Extract the hex values for:
   - Authentication packet (sent during connection)
   - Lock packet (sent when locking)
   - Unlock packet (sent when unlocking)

### Example Configuration

```
Authentication packet: 23FC5736B5ADD7E27578DA1BCC73E808
Lock packet: 43C144561FA0120FC5E76218D24C6276
Unlock packet: B38487C1D81AB08639FC46BA2B06669E
```

## Technical Details

### Bluetooth UUIDs

- **Write UUID**: `43480002-f001-4b49-4e47-204d45544552`
- **Notify UUID**: `43480003-f001-4b49-4e47-204d45544552`

### Lock Status Interpretation

The integration interprets the King-Meter telemetry format:
- Byte 8 = `0x0C`: Unlocked
- Byte 8 = `0x0F`: Locked

## Usage

Once configured, a lock entity will appear in Home Assistant:

- **Lock**: Sends the lock packet to the scooter
- **Unlock**: Sends the unlock packet to the scooter
- **Status**: Displays the current lock state based on notifications

## Troubleshooting

### Device Not Found

- Ensure your scooter is powered on
- Move your Bluetooth adapter closer to the scooter
- Check that Bluetooth is enabled on your Home Assistant instance

### Connection Failed

- Verify your authentication packets are correct
- Ensure the scooter is not connected to another device
- Try restarting the integration

### Status Not Updating

- Check that notifications are properly enabled
- Verify the scooter is sending telemetry data
- Review Home Assistant logs for any errors

## Security Considerations

- Authentication packets are stored in Home Assistant's configuration
- Packets are transmitted over local Bluetooth (not internet)
- Keep your authentication packets secure and don't share them publicly

## Credits

Based on the BLE communication protocol used by SoFlow electric scooters with King-Meter controllers.
