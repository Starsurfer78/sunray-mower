# type: ignore
import serial
import pynmea2
from pyubx2 import UBXReader, UBXMessage, UBXWriter, SET
from typing import Optional, Dict, Callable
from ntrip_client import NTRIPClient
import time
import math

class RTKGPS:
    """
    RTK-GPS Klasse für Ardusimple RTK Board mit flexibler Korrekturdaten-Quelle.
    
    Features:
    - Ardusimple RTK Board Support (u-blox F9P basiert)
    - XBee 868MHz für eigene RTK-Basisstation
    - NTRIP Client als Alternative (optional)
    - Koordinatentransformation zu lokalem System
    - GPS-basierte Navigation und Waypoint-Verfolgung
    - Kidnap Detection
    - Fix-Status Monitoring
    
    RTK-Korrekturdaten-Modi:
    1. XBee 868MHz: Rover/Base mit XBee-Modulen (automatisch erkannt)
    2. NTRIP: Internet-basierte Korrekturdaten (fallback)
    """

    def __init__(self, port: str = None, baudrate: int = None, timeout: float = None, 
                 rtk_mode: str = None, enable_ntrip_fallback: bool = None, auto_configure: bool = None, config: dict = None):
        """
        Initialisiert RTK-GPS für Ardusimple RTK Board.
        
        Args:
            port: USB-Port des Ardusimple RTK Boards (optional, aus config geladen)
            baudrate: Baudrate (optional, aus config geladen)
            timeout: Serial timeout (optional, aus config geladen)
            rtk_mode: "auto", "xbee", "ntrip" - Korrekturdaten-Modus (optional, aus config geladen)
            enable_ntrip_fallback: NTRIP als Fallback wenn XBee nicht verfügbar (optional, aus config geladen)
            auto_configure: Automatische Konfiguration des Ardusimple Boards (optional, aus config geladen)
            config: Konfigurationsdictionary mit hardware.rtk_gps Einstellungen
        """
        # Lade Konfiguration
        if config and 'hardware' in config and 'rtk_gps' in config['hardware']:
            rtk_config = config['hardware']['rtk_gps']
            port = port or rtk_config.get('port', '/dev/ttyUSB0')
            baudrate = baudrate or rtk_config.get('baudrate', 115200)
            timeout = timeout or rtk_config.get('timeout', 1.0)
            rtk_mode = rtk_mode or rtk_config.get('rtk_mode', 'auto')
            enable_ntrip_fallback = enable_ntrip_fallback if enable_ntrip_fallback is not None else rtk_config.get('enable_ntrip_fallback', True)
            auto_configure = auto_configure if auto_configure is not None else rtk_config.get('auto_configure', True)
        else:
            # Fallback zu Standardwerten
            port = port or '/dev/ttyUSB0'
            baudrate = baudrate or 115200
            timeout = timeout or 1.0
            rtk_mode = rtk_mode or 'auto'
            enable_ntrip_fallback = enable_ntrip_fallback if enable_ntrip_fallback is not None else True
            auto_configure = auto_configure if auto_configure is not None else True
        
        print(f"RTK-GPS: Initialisiere mit Port: {port}, Baudrate: {baudrate}, Timeout: {timeout}s")
        print(f"RTK-GPS: RTK-Modus: {rtk_mode}, NTRIP-Fallback: {enable_ntrip_fallback}, Auto-Config: {auto_configure}")
        
        self.ser = serial.Serial(port, baudrate, timeout=timeout)
        self.ubx_reader = UBXReader(self.ser, protfilter=0, msgmode=UBXReader.MSGMODE_AUTO)
        self.ubx_writer = UBXWriter(self.ser, protfilter=0)
        
        # RTK-Modus Konfiguration
        self.rtk_mode = rtk_mode
        self.enable_ntrip_fallback = enable_ntrip_fallback
        self.correction_source = "none"
        
        # XBee RTK Status
        self.xbee_rtk_active = False
        self.last_rtk_message_time = 0
        self.rtk_timeout = 30  # Sekunden ohne RTK-Nachrichten
        
        # NTRIP Client (optional/fallback)
        self.ntrip_client = None
        
        # Automatische Board-Konfiguration
        if auto_configure:
            self._configure_ardusimple_board()
        
        # RTK-Korrekturdaten-Quelle ermitteln und konfigurieren
        self._configure_rtk_source()
        
        # Lokales Koordinatensystem
        self.origin_lat = None
        self.origin_lon = None
        self.origin_set = False
        
        # GPS-Status
        self.last_fix_time = 0
        self.fix_type = 0
        self.last_position = {'lat': 0, 'lon': 0}
        self.position_history = []
        self.max_history = 10
        
        # Navigation
        self.current_waypoint = None
        self.waypoint_tolerance = 0.5  # Meter
        self.navigation_callback = None
        
        # Kidnap Detection
        self.kidnap_threshold = 10.0  # Meter
        self.last_valid_position = None
    
    def _configure_ardusimple_board(self):
        """
        Konfiguriert das Ardusimple RTK Board automatisch für optimale Performance.
        
        Konfiguriert:
        - UBX-Nachrichten: NAV-PVT (Position/Velocity/Time), NAV-RELPOSNED (RTK-Status)
        - NMEA-Nachrichten: GGA (für Kompatibilität)
        - Baudrate: 115200
        - Update-Rate: 5Hz
        - RTK-Modi aktiviert
        """
        print("RTK-GPS: Konfiguriere Ardusimple Board...")
        
        try:
            # 1. Setze Baudrate auf 115200 (falls noch nicht gesetzt)
            cfg_prt = UBXMessage('CFG', 'CFG-PRT', SET, 
                                portID=1,  # UART1
                                reserved0=0,
                                txReady=0,
                                mode=0x8D0,  # 8N1
                                baudRate=115200,
                                inProtoMask=0x07,  # UBX+NMEA+RTCM3
                                outProtoMask=0x03,  # UBX+NMEA
                                flags=0,
                                reserved5=0)
            self.ubx_writer.write(cfg_prt)
            time.sleep(0.1)
            
            # 2. Setze Update-Rate auf 5Hz (200ms)
            cfg_rate = UBXMessage('CFG', 'CFG-RATE', SET,
                                 measRate=200,  # 200ms = 5Hz
                                 navRate=1,
                                 timeRef=1)  # GPS time
            self.ubx_writer.write(cfg_rate)
            time.sleep(0.1)
            
            # 3. Aktiviere NAV-PVT Nachrichten (5Hz)
            cfg_msg_pvt = UBXMessage('CFG', 'CFG-MSG', SET,
                                    msgClass=0x01,  # NAV
                                    msgID=0x07,     # PVT
                                    rates=[0, 1, 0, 0, 0, 0])  # UART1 = 1Hz
            self.ubx_writer.write(cfg_msg_pvt)
            time.sleep(0.1)
            
            # 4. Aktiviere NAV-RELPOSNED für RTK-Status (1Hz)
            cfg_msg_relpos = UBXMessage('CFG', 'CFG-MSG', SET,
                                       msgClass=0x01,  # NAV
                                       msgID=0x3C,     # RELPOSNED
                                       rates=[0, 1, 0, 0, 0, 0])  # UART1 = 1Hz
            self.ubx_writer.write(cfg_msg_relpos)
            time.sleep(0.1)
            
            # 5. Aktiviere NMEA GGA für Kompatibilität (1Hz)
            cfg_msg_gga = UBXMessage('CFG', 'CFG-MSG', SET,
                                    msgClass=0xF0,  # NMEA
                                    msgID=0x00,     # GGA
                                    rates=[0, 1, 0, 0, 0, 0])  # UART1 = 1Hz
            self.ubx_writer.write(cfg_msg_gga)
            time.sleep(0.1)
            
            # 6. Deaktiviere unnötige NMEA-Nachrichten
            nmea_msgs_to_disable = [
                (0xF0, 0x01),  # GLL
                (0xF0, 0x02),  # GSA
                (0xF0, 0x03),  # GSV
                (0xF0, 0x04),  # RMC
                (0xF0, 0x05),  # VTG
                (0xF0, 0x08),  # ZDA
            ]
            
            for msg_class, msg_id in nmea_msgs_to_disable:
                cfg_msg = UBXMessage('CFG', 'CFG-MSG', SET,
                                    msgClass=msg_class,
                                    msgID=msg_id,
                                    rates=[0, 0, 0, 0, 0, 0])  # Alle Ports deaktiviert
                self.ubx_writer.write(cfg_msg)
                time.sleep(0.05)
            
            # 7. Konfiguriere RTK-Modi
            cfg_nav5 = UBXMessage('CFG', 'CFG-NAV5', SET,
                                 mask=0x0001,  # Dynamic model mask
                                 dynModel=4,    # Automotive
                                 fixMode=2,     # 3D only
                                 fixedAlt=0,
                                 fixedAltVar=10000,
                                 minElev=5,     # 5° Elevation mask
                                 drLimit=0,
                                 pDop=25.0,
                                 tDop=25.0,
                                 pAcc=100,
                                 tAcc=300,
                                 staticHoldThresh=0,
                                 dgnssTimeout=60,
                                 cnoThreshNumSVs=0,
                                 cnoThresh=0,
                                 reserved1=0,
                                 staticHoldMaxDist=0,
                                 utcStandard=0,
                                 reserved2=0,
                                 reserved3=0)
            self.ubx_writer.write(cfg_nav5)
            time.sleep(0.1)
            
            # 8. Speichere Konfiguration im Flash
            cfg_cfg = UBXMessage('CFG', 'CFG-CFG', SET,
                                clearMask=0x00000000,
                                saveMask=0x0000061F,  # Speichere alle relevanten Einstellungen
                                loadMask=0x00000000,
                                deviceMask=0x01)  # BBR
            self.ubx_writer.write(cfg_cfg)
            time.sleep(0.5)
            
            print("RTK-GPS: Ardusimple Board erfolgreich konfiguriert")
            print("RTK-GPS: - Update-Rate: 5Hz")
            print("RTK-GPS: - UBX-Nachrichten: NAV-PVT, NAV-RELPOSNED")
            print("RTK-GPS: - NMEA-Nachrichten: GGA")
            print("RTK-GPS: - RTK-Modi aktiviert")
            
        except Exception as e:
            print(f"RTK-GPS: Fehler bei Board-Konfiguration: {e}")
            print("RTK-GPS: Verwende Standard-Konfiguration")
    
    def reconfigure_board(self):
        """
        Führt eine manuelle Neukonfiguration des Ardusimple Boards durch.
        Nützlich wenn Board-Einstellungen geändert werden sollen.
        """
        print("RTK-GPS: Manuelle Board-Neukonfiguration...")
        self._configure_ardusimple_board()
    
    def _configure_rtk_source(self):
        """Konfiguriert die RTK-Korrekturdaten-Quelle basierend auf Modus und Verfügbarkeit."""
        if self.rtk_mode == "auto":
            # Automatische Erkennung: Prüfe auf XBee RTK-Nachrichten
            print("RTK-GPS: Automatische Erkennung der Korrekturdaten-Quelle...")
            if self._detect_xbee_rtk():
                self.correction_source = "xbee"
                self.xbee_rtk_active = True
                print("RTK-GPS: XBee 868MHz RTK-Verbindung erkannt")
            elif self.enable_ntrip_fallback:
                self._setup_ntrip_fallback()
            else:
                print("RTK-GPS: Keine RTK-Korrekturdaten verfügbar (Standalone-Modus)")
                self.correction_source = "none"
        
        elif self.rtk_mode == "xbee":
            # Erzwinge XBee-Modus
            self.correction_source = "xbee"
            self.xbee_rtk_active = True
            print("RTK-GPS: XBee 868MHz RTK-Modus erzwungen")
        
        elif self.rtk_mode == "ntrip":
            # Erzwinge NTRIP-Modus
            self._setup_ntrip_fallback()
        
        else:
            print(f"RTK-GPS: Unbekannter RTK-Modus '{self.rtk_mode}', verwende Standalone")
            self.correction_source = "none"
    
    def _detect_xbee_rtk(self) -> bool:
        """Erkennt ob XBee RTK-Nachrichten empfangen werden."""
        # Prüfe für 5 Sekunden auf RTCM-Nachrichten über XBee
        start_time = time.time()
        rtcm_detected = False
        
        while time.time() - start_time < 5.0:
            try:
                (raw_data, parsed_data) = self.ubx_reader.read()
                if raw_data and len(raw_data) > 0:
                    # Prüfe auf RTCM3-Nachrichten (beginnen mit 0xD3)
                    if raw_data[0] == 0xD3:
                        rtcm_detected = True
                        self.last_rtk_message_time = time.time()
                        break
            except Exception:
                pass
            time.sleep(0.1)
        
        return rtcm_detected
    
    def _setup_ntrip_fallback(self):
        """Richtet NTRIP als Fallback oder primäre Quelle ein."""
        try:
            self.ntrip_client = NTRIPClient()
            self.ntrip_client.set_rtcm_callback(self._send_rtcm_to_gps)
            if self.ntrip_client.connect():
                self.correction_source = "ntrip"
                print("RTK-GPS: NTRIP-Korrekturdaten aktiviert")
            else:
                print("RTK-GPS: NTRIP-Verbindung fehlgeschlagen")
                self.correction_source = "none"
        except Exception as e:
            print(f"RTK-GPS: NTRIP-Setup fehlgeschlagen: {e}")
            self.correction_source = "none"
    
    def _check_rtk_source_health(self):
        """Überwacht die Gesundheit der RTK-Korrekturdaten-Quelle."""
        current_time = time.time()
        
        # XBee RTK Timeout-Prüfung
        if self.correction_source == "xbee":
            if current_time - self.last_rtk_message_time > self.rtk_timeout:
                print("RTK-GPS: XBee RTK-Timeout, wechsle zu NTRIP-Fallback")
                self.xbee_rtk_active = False
                if self.enable_ntrip_fallback:
                    self._setup_ntrip_fallback()
                else:
                    self.correction_source = "none"
        
        # NTRIP Verbindungs-Prüfung
        elif self.correction_source == "ntrip":
            if self.ntrip_client and not self.ntrip_client.is_connected():
                print("RTK-GPS: NTRIP-Verbindung verloren")
                # Versuche XBee-Wiederherstellung
                if self._detect_xbee_rtk():
                    self.correction_source = "xbee"
                    self.xbee_rtk_active = True
                    if self.ntrip_client:
                        self.ntrip_client.disconnect()
                        self.ntrip_client = None
                    print("RTK-GPS: Wechsel zurück zu XBee RTK")
                else:
                    self.correction_source = "none"

    def read(self) -> Optional[Dict]:
        """
        Liest GPS-Daten und gibt erweiterte Informationen zurück:
        {
            'lat': float,
            'lon': float,
            'alt': float,
            'fix_type': int,
            'hdop': float,
            'nsat': int,
            'time': str,
            'local_x': float,  # Lokale Koordinaten
            'local_y': float,
            'rtk_age': float,  # Alter der RTK-Korrekturdaten
            'rtk_ratio': float,  # RTK-Qualität
            'rtk_source': str,  # "xbee", "ntrip", "none"
            'kidnap_detected': bool,
            'waypoint_distance': float,
            'waypoint_bearing': float
        }
        """
        # RTK-Quelle Gesundheitsprüfung
        self._check_rtk_source_health()
        
        gps_data = None
        
        try:
            # Versuche UBX
            (raw_data, parsed_data) = self.ubx_reader.read()
            
            # Prüfe auf RTCM3-Nachrichten von XBee (für RTK-Erkennung)
            if raw_data and len(raw_data) > 0 and raw_data[0] == 0xD3:
                if self.correction_source == "xbee":
                    self.last_rtk_message_time = time.time()
                elif self.correction_source == "none" and self.rtk_mode == "auto":
                    # XBee RTK wurde aktiviert
                    self.correction_source = "xbee"
                    self.xbee_rtk_active = True
                    self.last_rtk_message_time = time.time()
                    print("RTK-GPS: XBee RTK-Verbindung wiederhergestellt")
                    # NTRIP deaktivieren falls aktiv
                    if self.ntrip_client:
                        self.ntrip_client.disconnect()
                        self.ntrip_client = None
            
            if isinstance(parsed_data, UBXMessage):
                if parsed_data.identity == "NAV-PVT":
                    gps_data = {
                        "lat": parsed_data.lat / 1e7,
                        "lon": parsed_data.lon / 1e7,
                        "alt": parsed_data.height / 1e3,
                        "fix_type": parsed_data.fixType,
                        "hdop": parsed_data.hAcc / 1e3,
                        "nsat": parsed_data.numSV,
                        "time": str(parsed_data.iTOW)
                    }
                elif parsed_data.identity == "NAV-RELPOSNED":
                    # RTK-spezifische Daten
                    if gps_data:
                        gps_data.update({
                            "rtk_age": getattr(parsed_data, 'relPosAge', 0) / 100.0,
                            "rtk_ratio": getattr(parsed_data, 'relPosHPLength', 0) / 1e4
                        })
        except Exception:
            # Fallback auf NMEA
            self.ser.reset_input_buffer()
        
        # NMEA-Fallback
        if not gps_data:
            try:
                line = self.ser.readline().decode('ascii', errors='ignore').strip()
                if line.startswith('$'):
                    msg = pynmea2.parse(line)
                    if isinstance(msg, pynmea2.types.talker.GGA):
                        gps_data = {
                            "lat": msg.latitude,
                            "lon": msg.longitude,
                            "alt": float(msg.altitude),
                            "fix_type": int(msg.gps_qual),
                            "hdop": float(msg.horizontal_dil),
                            "nsat": int(msg.num_sats),
                            "time": str(msg.timestamp)
                        }
            except Exception:
                pass
        
        if gps_data:
            # Erweiterte Verarbeitung
            gps_data = self._process_gps_data(gps_data)
            # RTK-Quelle hinzufügen
            gps_data['rtk_source'] = self.correction_source
            
        return gps_data

    def _process_gps_data(self, gps_data: Dict) -> Dict:
        """Verarbeitet GPS-Daten und fügt erweiterte Informationen hinzu."""
        # Aktualisiere Position History
        self.position_history.append({
            'lat': gps_data['lat'],
            'lon': gps_data['lon'],
            'time': time.time()
        })
        if len(self.position_history) > self.max_history:
            self.position_history.pop(0)
        
        # Setze Origin falls noch nicht gesetzt
        if not self.origin_set and gps_data['fix_type'] >= 2:
            self.set_origin(gps_data['lat'], gps_data['lon'])
        
        # Koordinatentransformation
        local_x, local_y = self.to_local_coordinates(gps_data['lat'], gps_data['lon'])
        gps_data['local_x'] = local_x
        gps_data['local_y'] = local_y
        
        # Kidnap Detection
        gps_data['kidnap_detected'] = self._detect_kidnap(gps_data)
        
        # Waypoint Navigation
        if self.current_waypoint:
            distance, bearing = self._calculate_waypoint_info(gps_data)
            gps_data['waypoint_distance'] = distance
            gps_data['waypoint_bearing'] = bearing
        else:
            gps_data['waypoint_distance'] = 0.0
            gps_data['waypoint_bearing'] = 0.0
        
        # RTK-Daten falls nicht vorhanden
        if 'rtk_age' not in gps_data:
            gps_data['rtk_age'] = 999.0
        if 'rtk_ratio' not in gps_data:
            gps_data['rtk_ratio'] = 0.0
        
        # Update Status
        self.last_fix_time = time.time()
        self.fix_type = gps_data['fix_type']
        self.last_position = {'lat': gps_data['lat'], 'lon': gps_data['lon']}
        
        if gps_data['fix_type'] >= 2:
            self.last_valid_position = {'lat': gps_data['lat'], 'lon': gps_data['lon']}
        
        return gps_data
    
    def set_origin(self, lat: float, lon: float):
        """Setzt den Ursprung für das lokale Koordinatensystem."""
        self.origin_lat = lat
        self.origin_lon = lon
        self.origin_set = True
        print(f"GPS Origin gesetzt: {lat:.8f}, {lon:.8f}")
    
    def to_local_coordinates(self, lat: float, lon: float) -> tuple:
        """Wandelt GPS-Koordinaten in lokales Koordinatensystem um."""
        if not self.origin_set:
            return 0.0, 0.0
        
        # Einfache Projektion (für kleine Bereiche ausreichend)
        R = 6371000  # Erdradius in Metern
        
        dlat = math.radians(lat - self.origin_lat)
        dlon = math.radians(lon - self.origin_lon)
        
        x = R * dlon * math.cos(math.radians(self.origin_lat))
        y = R * dlat
        
        return x, y
    
    def from_local_coordinates(self, x: float, y: float) -> tuple:
        """Wandelt lokale Koordinaten zurück zu GPS-Koordinaten."""
        if not self.origin_set:
            return 0.0, 0.0
        
        R = 6371000  # Erdradius in Metern
        
        dlat = y / R
        dlon = x / (R * math.cos(math.radians(self.origin_lat)))
        
        lat = self.origin_lat + math.degrees(dlat)
        lon = self.origin_lon + math.degrees(dlon)
        
        return lat, lon
    
    def _detect_kidnap(self, gps_data: Dict) -> bool:
        """Erkennt plötzliche Positionssprünge (Kidnap Detection)."""
        if not self.last_valid_position or gps_data['fix_type'] < 2:
            return False
        
        distance = self._calculate_distance(
            self.last_valid_position['lat'], self.last_valid_position['lon'],
            gps_data['lat'], gps_data['lon']
        )
        
        return distance > self.kidnap_threshold
    
    def _calculate_distance(self, lat1: float, lon1: float, lat2: float, lon2: float) -> float:
        """Berechnet die Entfernung zwischen zwei GPS-Punkten in Metern."""
        R = 6371000  # Erdradius in Metern
        
        dlat = math.radians(lat2 - lat1)
        dlon = math.radians(lon2 - lon1)
        
        a = (math.sin(dlat/2) * math.sin(dlat/2) + 
             math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * 
             math.sin(dlon/2) * math.sin(dlon/2))
        
        c = 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))
        
        return R * c
    
    def _calculate_bearing(self, lat1: float, lon1: float, lat2: float, lon2: float) -> float:
        """Berechnet die Peilung zwischen zwei GPS-Punkten in Grad."""
        dlat = math.radians(lat2 - lat1)
        dlon = math.radians(lon2 - lon1)
        
        y = math.sin(dlon) * math.cos(math.radians(lat2))
        x = (math.cos(math.radians(lat1)) * math.sin(math.radians(lat2)) - 
             math.sin(math.radians(lat1)) * math.cos(math.radians(lat2)) * math.cos(dlon))
        
        bearing = math.atan2(y, x)
        return math.degrees(bearing) % 360
    
    def _calculate_waypoint_info(self, gps_data: Dict) -> tuple:
        """Berechnet Entfernung und Peilung zum aktuellen Waypoint."""
        if not self.current_waypoint:
            return 0.0, 0.0
        
        distance = self._calculate_distance(
            gps_data['lat'], gps_data['lon'],
            self.current_waypoint['lat'], self.current_waypoint['lon']
        )
        
        bearing = self._calculate_bearing(
            gps_data['lat'], gps_data['lon'],
            self.current_waypoint['lat'], self.current_waypoint['lon']
        )
        
        return distance, bearing
    
    def set_waypoint(self, lat: float, lon: float, tolerance: float = None):
        """Setzt einen neuen Waypoint für die Navigation."""
        self.current_waypoint = {'lat': lat, 'lon': lon}
        if tolerance:
            self.waypoint_tolerance = tolerance
        print(f"Waypoint gesetzt: {lat:.8f}, {lon:.8f} (Toleranz: {self.waypoint_tolerance}m)")
    
    def clear_waypoint(self):
        """Löscht den aktuellen Waypoint."""
        self.current_waypoint = None
    
    def is_waypoint_reached(self, gps_data: Dict) -> bool:
        """Prüft ob der aktuelle Waypoint erreicht wurde."""
        if not self.current_waypoint:
            return False
        
        distance, _ = self._calculate_waypoint_info(gps_data)
        return distance <= self.waypoint_tolerance
    
    def _send_rtcm_to_gps(self, rtcm_data: bytes):
        """Sendet RTCM-Korrekturdaten an den GPS-Empfänger."""
        try:
            self.ser.write(rtcm_data)
        except Exception as e:
            print(f"Fehler beim Senden von RTCM-Daten: {e}")
    
    def get_fix_status(self) -> Dict:
        """Gibt detaillierte Fix-Status-Informationen zurück."""
        fix_types = {
            0: "No Fix",
            1: "Dead Reckoning",
            2: "2D Fix",
            3: "3D Fix",
            4: "GNSS + Dead Reckoning",
            5: "Time Only Fix"
        }
        
        rtk_status = "Unknown"
        if hasattr(self, 'last_rtk_age'):
            if self.last_rtk_age < 10:
                rtk_status = "RTK Fixed"
            elif self.last_rtk_age < 60:
                rtk_status = "RTK Float"
            else:
                rtk_status = "RTK Timeout"
        
        return {
            'fix_type': self.fix_type,
            'fix_description': fix_types.get(self.fix_type, "Unknown"),
            'rtk_status': rtk_status,
            'time_since_last_fix': time.time() - self.last_fix_time,
            'ntrip_connected': self.ntrip_client.is_connected() if self.ntrip_client else False
        }
    
    def set_navigation_callback(self, callback: Callable):
        """Setzt einen Callback für Navigation Events."""
        self.navigation_callback = callback
    
    def close(self):
        """Schließt die serielle Verbindung und NTRIP-Client."""
        if self.ntrip_client:
            self.ntrip_client.disconnect()
        if self.ser and self.ser.is_open:
            self.ser.close()
