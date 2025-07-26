# type: ignore
import serial
import pynmea2
from pyubx2 import UBXReader, UBXMessage
from typing import Optional, Dict

class RTKGPS:
    """
    Liest GPS-Daten via USB-Serial im UBX- oder NMEA-Format.
    Nutzt pyubx2 für UBX und pynmea2 für NMEA.
    Wandelt Koordinaten in lokales Koordinatensystem um (Platzhalter).
    """

    def __init__(self, port: str = "/dev/ttyUSB0", baudrate: int = 38400, timeout: float = 1.0):
        self.ser = serial.Serial(port, baudrate, timeout=timeout)
        self.ubx_reader = UBXReader(self.ser, protfilter=0, msgmode=UBXReader.MSGMODE_AUTO)

    def read(self) -> Optional[Dict]:
        """
        Liest ein einziges Paket (UBX oder NMEA) und gibt ein Dictionary zurück:
        {
            'lat': float,
            'lon': float,
            'alt': float,
            'fix_type': int,
            'hdop': float,
            'nsat': int,
            'time': str
        }
        Rückgabe None bei Timeout oder unbekanntem Format.
        """
        try:
            # Versuche UBX
            (raw_data, parsed_data) = self.ubx_reader.read()
            if isinstance(parsed_data, UBXMessage):
                # Beispiel für NAV-PVT Nachricht
                if parsed_data.identity == "NAV-PVT":
                    return {
                        "lat": parsed_data.lat / 1e7,
                        "lon": parsed_data.lon / 1e7,
                        "alt": parsed_data.height / 1e3,
                        "fix_type": parsed_data.fixType,
                        "hdop": parsed_data.hAcc / 1e3,
                        "nsat": parsed_data.numSV,
                        "time": parsed_data.jnsec.isoformat()
                    }
        except Exception:
            # Fallback auf NMEA
            self.ser.reset_input_buffer()
        # NMEA-Lesung
        try:
            line = self.ser.readline().decode('ascii', errors='ignore').strip()
            if line.startswith('$'):
                msg = pynmea2.parse(line)
                if isinstance(msg, pynmea2.types.talker.GGA):
                    return {
                        "lat": msg.latitude,
                        "lon": msg.longitude,
                        "alt": float(msg.altitude),
                        "fix_type": int(msg.gps_qual),
                        "hdop": float(msg.horizontal_dil),
                        "nsat": int(msg.num_sats),
                        "time": msg.timestamp.isoformat()
                    }
        except Exception:
            pass
        return None

    def close(self):
        """Schließt die serielle Verbindung."""
        if self.ser and self.ser.is_open:
            self.ser.close()
