#!/usr/bin/env python3
"""
NTRIP Client für RTK-GPS Korrekturdaten

Unterstützt sowohl Internet-basierte NTRIP-Caster als auch lokale RTK-Basisstationen.
Optional konfigurierbar über config.json.

Autor: Sunray Python Team
Version: 1.0
"""

import socket
import base64
import threading
import time
from typing import Optional, Callable, Dict, Any
from config import get_config

class NTRIPClient:
    """
    NTRIP Client für RTK-Korrekturdaten.
    
    Unterstützt:
    - Internet-basierte NTRIP-Caster (SAPOS, FLEPOS, SWEPOS, etc.)
    - Lokale RTK-Basisstationen
    - Automatisches Reconnect
    - RTCM3-Datenweiterleitung an GPS-Empfänger
    
    Beispiel:
        ntrip = NTRIPClient()
        ntrip.set_rtcm_callback(gps_receiver.send_rtcm_data)
        ntrip.connect()
    """
    
    def __init__(self, config_section: str = "ntrip"):
        """
        Initialisiert den NTRIP Client.
        
        Args:
            config_section (str): Konfigurationssektion in config.json
        """
        self.config = get_config().get(config_section, {})
        
        # NTRIP-Konfiguration
        self.enabled = self.config.get('enabled', False)
        self.host = self.config.get('host', '')
        self.port = self.config.get('port', 2101)
        self.mountpoint = self.config.get('mountpoint', '')
        self.username = self.config.get('username', '')
        self.password = self.config.get('password', '')
        
        # Lokale RTK-Station als Fallback
        self.local_rtk_enabled = self.config.get('local_rtk_enabled', False)
        self.local_rtk_host = self.config.get('local_rtk_host', '192.168.1.100')
        self.local_rtk_port = self.config.get('local_rtk_port', 2101)
        
        # Verbindungsparameter
        self.user_agent = self.config.get('user_agent', 'Sunray-Python/1.0')
        self.reconnect_interval = self.config.get('reconnect_interval', 30)
        self.timeout = self.config.get('timeout', 10)
        
        # Interne Variablen
        self.socket = None
        self.connected = False
        self.running = False
        self.thread = None
        self.rtcm_callback = None
        self.status_callback = None
        
        # Statistiken
        self.bytes_received = 0
        self.last_data_time = 0
        self.connection_attempts = 0
        self.using_local_rtk = False
    
    def set_rtcm_callback(self, callback: Callable[[bytes], None]) -> None:
        """
        Setzt Callback für empfangene RTCM-Daten.
        
        Args:
            callback: Funktion die RTCM-Daten verarbeitet
        """
        self.rtcm_callback = callback
    
    def set_status_callback(self, callback: Callable[[Dict[str, Any]], None]) -> None:
        """
        Setzt Callback für Statusupdates.
        
        Args:
            callback: Funktion die Status-Dict verarbeitet
        """
        self.status_callback = callback
    
    def connect(self) -> bool:
        """
        Startet NTRIP-Verbindung (falls aktiviert).
        
        Returns:
            bool: True wenn erfolgreich gestartet
        """
        if not self.enabled:
            print("NTRIP Client: Deaktiviert in Konfiguration")
            return False
        
        if not self.host or not self.mountpoint:
            print("NTRIP Client: Unvollständige Konfiguration")
            return False
        
        self.running = True
        self.thread = threading.Thread(target=self._connection_loop, daemon=True)
        self.thread.start()
        
        print(f"NTRIP Client: Gestartet für {self.host}:{self.port}/{self.mountpoint}")
        return True
    
    def disconnect(self) -> None:
        """
        Beendet NTRIP-Verbindung.
        """
        self.running = False
        
        if self.socket:
            try:
                self.socket.close()
            except:
                pass
            self.socket = None
        
        self.connected = False
        print("NTRIP Client: Verbindung beendet")
    
    def _connection_loop(self) -> None:
        """
        Haupt-Verbindungsschleife mit automatischem Reconnect.
        """
        while self.running:
            try:
                # Primäre NTRIP-Verbindung versuchen
                if self._connect_ntrip(self.host, self.port):
                    self.using_local_rtk = False
                    self._data_loop()
                # Fallback auf lokale RTK-Station
                elif self.local_rtk_enabled and self._connect_ntrip(self.local_rtk_host, self.local_rtk_port):
                    self.using_local_rtk = True
                    print(f"NTRIP Client: Fallback auf lokale RTK-Station {self.local_rtk_host}")
                    self._data_loop()
                else:
                    print(f"NTRIP Client: Verbindung fehlgeschlagen, Retry in {self.reconnect_interval}s")
                    time.sleep(self.reconnect_interval)
                    
            except Exception as e:
                print(f"NTRIP Client: Verbindungsfehler: {e}")
                time.sleep(self.reconnect_interval)
            
            finally:
                self._cleanup_connection()
    
    def _connect_ntrip(self, host: str, port: int) -> bool:
        """
        Stellt NTRIP-Verbindung her.
        
        Args:
            host: NTRIP-Host
            port: NTRIP-Port
            
        Returns:
            bool: True wenn erfolgreich verbunden
        """
        try:
            self.connection_attempts += 1
            
            # Socket erstellen
            self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.socket.settimeout(self.timeout)
            
            # Verbindung herstellen
            self.socket.connect((host, port))
            
            # NTRIP-Request senden
            request = self._build_ntrip_request()
            self.socket.send(request.encode('utf-8'))
            
            # Response lesen
            response = self.socket.recv(1024).decode('utf-8')
            
            if 'ICY 200 OK' in response or 'HTTP/1.1 200 OK' in response:
                self.connected = True
                print(f"NTRIP Client: Verbunden mit {host}:{port}")
                
                # Status-Callback
                if self.status_callback:
                    self.status_callback({
                        'connected': True,
                        'host': host,
                        'port': port,
                        'using_local_rtk': self.using_local_rtk
                    })
                
                return True
            else:
                print(f"NTRIP Client: Ungültige Response: {response[:100]}")
                return False
                
        except Exception as e:
            print(f"NTRIP Client: Verbindungsfehler zu {host}:{port} - {e}")
            return False
    
    def _build_ntrip_request(self) -> str:
        """
        Erstellt NTRIP-HTTP-Request.
        
        Returns:
            str: HTTP-Request String
        """
        request = f"GET /{self.mountpoint} HTTP/1.1\r\n"
        request += f"Host: {self.host}\r\n"
        request += f"User-Agent: {self.user_agent}\r\n"
        
        # Authentifizierung falls erforderlich
        if self.username and self.password:
            credentials = base64.b64encode(f"{self.username}:{self.password}".encode()).decode()
            request += f"Authorization: Basic {credentials}\r\n"
        
        request += "Connection: close\r\n"
        request += "\r\n"
        
        return request
    
    def _data_loop(self) -> None:
        """
        Empfängt und verarbeitet RTCM-Daten.
        """
        buffer = b''
        
        while self.running and self.connected:
            try:
                # Daten empfangen
                data = self.socket.recv(1024)
                if not data:
                    print("NTRIP Client: Verbindung vom Server geschlossen")
                    break
                
                buffer += data
                self.bytes_received += len(data)
                self.last_data_time = time.time()
                
                # RTCM-Nachrichten extrahieren und weiterleiten
                buffer = self._process_rtcm_buffer(buffer)
                
            except socket.timeout:
                # Timeout ist normal, weiter versuchen
                continue
            except Exception as e:
                print(f"NTRIP Client: Datenfehler: {e}")
                break
    
    def _process_rtcm_buffer(self, buffer: bytes) -> bytes:
        """
        Verarbeitet RTCM-Daten aus dem Puffer.
        
        Args:
            buffer: Rohe Daten vom NTRIP-Stream
            
        Returns:
            bytes: Verbleibende Daten im Puffer
        """
        # Einfache RTCM-Verarbeitung - suche nach RTCM3-Präambel (0xD3)
        while len(buffer) >= 3:
            if buffer[0] == 0xD3:
                # RTCM3-Nachricht gefunden
                length = ((buffer[1] & 0x03) << 8) | buffer[2]
                total_length = length + 6  # Header (3) + Payload + CRC (3)
                
                if len(buffer) >= total_length:
                    # Vollständige Nachricht verfügbar
                    rtcm_message = buffer[:total_length]
                    
                    # An GPS-Empfänger weiterleiten
                    if self.rtcm_callback:
                        self.rtcm_callback(rtcm_message)
                    
                    # Nachricht aus Puffer entfernen
                    buffer = buffer[total_length:]
                else:
                    # Unvollständige Nachricht, warten auf mehr Daten
                    break
            else:
                # Ungültiges Byte, entfernen
                buffer = buffer[1:]
        
        return buffer
    
    def _cleanup_connection(self) -> None:
        """
        Räumt Verbindungsressourcen auf.
        """
        if self.socket:
            try:
                self.socket.close()
            except:
                pass
            self.socket = None
        
        self.connected = False
        
        # Status-Callback
        if self.status_callback:
            self.status_callback({
                'connected': False,
                'bytes_received': self.bytes_received,
                'last_data_time': self.last_data_time
            })
    
    def get_status(self) -> Dict[str, Any]:
        """
        Gibt aktuellen NTRIP-Status zurück.
        
        Returns:
            Dict: Status-Informationen
        """
        return {
            'enabled': self.enabled,
            'connected': self.connected,
            'host': self.host,
            'port': self.port,
            'mountpoint': self.mountpoint,
            'using_local_rtk': self.using_local_rtk,
            'bytes_received': self.bytes_received,
            'last_data_time': self.last_data_time,
            'connection_attempts': self.connection_attempts,
            'data_age': time.time() - self.last_data_time if self.last_data_time > 0 else 0
        }
    
    def is_data_fresh(self, max_age: float = 30.0) -> bool:
        """
        Prüft ob RTCM-Daten aktuell sind.
        
        Args:
            max_age: Maximales Alter in Sekunden
            
        Returns:
            bool: True wenn Daten aktuell
        """
        if not self.connected or self.last_data_time == 0:
            return False
        
        return (time.time() - self.last_data_time) <= max_age


# Beispiel-Konfiguration für config.json:
"""
{
    "ntrip": {
        "enabled": true,
        "host": "sapos.bayern.de",
        "port": 2101,
        "mountpoint": "VRS_3_4G_DE",
        "username": "your_username",
        "password": "your_password",
        "local_rtk_enabled": true,
        "local_rtk_host": "192.168.1.100",
        "local_rtk_port": 2101,
        "user_agent": "Sunray-Python/1.0",
        "reconnect_interval": 30,
        "timeout": 10
    }
}
"""