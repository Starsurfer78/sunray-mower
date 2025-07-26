import gpsdclient

class GPSModule:
    """
    Liest GPS-Daten über gpsdclient von einem USB-GNSS-Modul.
    """
    def __init__(self, host: str = "127.0.0.1", port: int = 2947):
        self.client = gpsdclient.GPSDClient(host=host, port=port)

    def read(self) -> dict:
        """
        Gibt ein Dictionary mit aktuellen GPS-Werten zurück.
        Keys: lat, lon, alt, time, mode
        """
        for result in self.client.dict_stream(convert_datetime=True):
            return {
                'lat': result.get('lat'),
                'lon': result.get('lon'),
                'alt': result.get('alt'),
                'time': str(result.get('time')),
                'mode': result.get('mode')
            }
        return {}
