from typing import Callable, Optional
from bleak import BleakClient, BleakScanner

class BLEClient:
    """
    Wrapper für BLE-Kommunikation mit bleak.
    Methoden:
      - scan(timeout: float) -> List[str]
      - connect(address: str) -> None
      - disconnect() -> None
      - write_char(uuid: str, data: bytes) -> None
      - read_char(uuid: str) -> bytes
      - start_notify(uuid: str, callback: Callable[[bytes], None]) -> None
      - stop_notify(uuid: str) -> None
    """
    def __init__(self):
        self.client: Optional[BleakClient] = None

    async def scan(self, timeout: float = 5.0) -> list:
        """Scannt nach BLE-Geräten und gibt deren Adressen zurück."""
        devices = await BleakScanner.discover(timeout=timeout)
        return [d.address for d in devices]

    async def connect(self, address: str) -> None:
        """Verbindet mit BLE-Gerät."""
        self.client = BleakClient(address)
        await self.client.connect()

    async def disconnect(self) -> None:
        """Trennt die Verbindung."""
        if self.client and self.client.is_connected:
            await self.client.disconnect()

    async def write_char(self, uuid: str, data: bytes) -> None:
        """Schreibt Daten an Charakteristik UUID."""
        if self.client:
            await self.client.write_gatt_char(uuid, data)

    async def read_char(self, uuid: str) -> bytes:
        """Liest Daten von Charakteristik UUID."""
        if self.client:
            return await self.client.read_gatt_char(uuid)
        return b''

    async def start_notify(self, uuid: str, callback: Callable[[bytes], None]) -> None:
        """Registriert Benachrichtigungen für UUID."""
        if self.client:
            await self.client.start_notify(uuid, lambda _, data: callback(data))

    async def stop_notify(self, uuid: str) -> None:
        """Deaktiviert Benachrichtigungen für UUID."""
        if self.client:
            await self.client.stop_notify(uuid)
