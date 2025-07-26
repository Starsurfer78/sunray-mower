import can
from typing import Callable, Optional

class CANClient:
    """
    Wrapper für python-can Interface.
    Methoden:
      - connect(channel: str, bustype: str = 'socketcan', bitrate: int = 500000)
      - send(arbitration_id: int, data: bytes)
      - receive(timeout: Optional[float] = 1.0) -> can.Message
      - add_listener(callback: Callable[[can.Message], None])
      - shutdown()
    """
    def __init__(self):
        self.bus: Optional[can.Bus] = None
        self.notifier: Optional[can.Notifier] = None

    def connect(self, channel: str, bustype: str = 'socketcan', bitrate: int = 500000):
        """Öffnet CAN-Bus."""
        self.bus = can.Bus(channel=channel, bustype=bustype, bitrate=bitrate)

    def send(self, arbitration_id: int, data: bytes) -> None:
        """Sendet Raw-Datenframe."""
        if self.bus:
            msg = can.Message(arbitration_id=arbitration_id, data=data, is_extended_id=False)
            self.bus.send(msg)

    def receive(self, timeout: Optional[float] = 1.0) -> Optional[can.Message]:
        """Wartet auf Message."""
        if self.bus:
            return self.bus.recv(timeout)
        return None

    def add_listener(self, callback: Callable[[can.Message], None]) -> None:
        """Callback bei neuer Nachricht."""
        if self.bus:
            self.notifier = can.Notifier(self.bus, [callback])

    def shutdown(self) -> None:
        """Schließt Bus und Notifier."""
        if self.notifier:
            self.notifier.stop()
        if self.bus:
            self.bus.shutdown()
