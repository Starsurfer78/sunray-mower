import serial
import threading

class PicoComm:
    """
    UART-Kommunikation mit Pico im ASCII-Format.
    Liest ASCII-Sensordaten und sendet ASCII-Kommandos (AT-Befehle).
    """
    def __init__(self, port: str, baudrate: int = 115200, timeout: float = 0.1):
        self.ser = serial.Serial(port, baudrate, timeout=timeout)
        self.lock = threading.Lock()

    def read_sensor_data(self) -> str:
        """
        Liest eine ASCII-Zeile vom Pico.
        Rückgabe: gesamte Zeile ohne Zeilenumbruch oder ''.
        """
        try:
            line = self.ser.readline().decode('ascii', errors='ignore').strip()
            return line
        except Exception:
            return ''

    def send_command(self, cmd: str) -> None:
        """
        Sendet ein ASCII-Kommando an den Pico.
        """
        msg = cmd + "\r\n"
        with self.lock:
            self.ser.write(msg.encode('ascii'))

    def close(self) -> None:
        """
        Schließt die serielle Verbindung.
        """
        with self.lock:
            if self.ser.is_open:
                self.ser.close()
