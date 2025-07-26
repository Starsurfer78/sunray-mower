#!/usr/bin/env python3
"""
Zentrale Hardware-Manager-Klasse für Sunray Python Mähroboter.

Diese Klasse koordiniert die gesamte Hardware-Kommunikation:
- Zentrale Pico-Kommunikation
- Sensor-Datenverteilung
- Hardware-Abstraktionsschicht
- Thread-sichere Kommunikation
- Einheitliche Hardware-Schnittstelle

Autor: Sunray Python Team
Version: 1.0
"""

import time
import threading
from typing import Dict, Optional, Callable, Any
from pico_comm import PicoComm
from config import get_config

class HardwareManager:
    """
    Zentrale Hardware-Manager-Klasse für alle Hardware-Kommunikation.
    
    Diese Klasse fungiert als einziger Zugangspunkt zur Hardware:
    - Verwaltet die Pico-Kommunikation zentral
    - Stellt einheitliche Schnittstellen bereit
    - Koordiniert Sensor-Datenverteilung
    - Gewährleistet Thread-Sicherheit
    - Implementiert Hardware-Abstraktionsschicht
    
    Beispiel:
        hw_manager = HardwareManager()
        hw_manager.begin()
        
        # Motor-Befehle senden
        hw_manager.send_motor_command(100, 100, 0)
        
        # Sensor-Daten lesen
        data = hw_manager.get_latest_sensor_data()
        
        # Callbacks für Datenverarbeitung registrieren
        hw_manager.register_data_callback('motor', motor.update)
    """
    
    def __init__(self, port: str = '/dev/ttyS0', baudrate: int = 115200):
        """
        Initialisiert den Hardware-Manager.
        
        Args:
            port (str): Serieller Port für Pico-Kommunikation
            baudrate (int): Baudrate für serielle Kommunikation
        """
        self.config = get_config()
        self.pico = None
        self.port = port
        self.baudrate = baudrate
        
        # Thread-Sicherheit
        self.lock = threading.Lock()
        self.running = False
        self.data_thread = None
        
        # Aktuelle Sensor-Daten
        self.latest_sensor_data = {}
        self.last_update_time = 0
        
        # Callbacks für Datenverarbeitung
        self.data_callbacks = {}
        
        # Summary-Request-Timer
        self.last_summary_request = 0
        self.summary_interval = 1.0  # Sekunden
        
        # Hardware-Status
        self.hardware_connected = False
        self.communication_errors = 0
        self.max_communication_errors = 10
    
    def begin(self) -> bool:
        """
        Initialisiert die Hardware-Kommunikation.
        
        Returns:
            bool: True wenn erfolgreich initialisiert
        """
        try:
            self.pico = PicoComm(self.port, self.baudrate)
            self.hardware_connected = True
            self.running = True
            
            # Daten-Thread starten
            self.data_thread = threading.Thread(target=self._data_loop, daemon=True)
            self.data_thread.start()
            
            print(f"HardwareManager: Verbindung zu {self.port} hergestellt")
            return True
            
        except Exception as e:
            print(f"HardwareManager: Fehler bei Initialisierung: {e}")
            self.hardware_connected = False
            return False
    
    def stop(self) -> None:
        """
        Beendet die Hardware-Kommunikation sauber.
        """
        self.running = False
        
        if self.data_thread and self.data_thread.is_alive():
            self.data_thread.join(timeout=2.0)
        
        if self.pico:
            self.pico.close()
            
        print("HardwareManager: Hardware-Kommunikation beendet")
    
    def _data_loop(self) -> None:
        """
        Haupt-Datenverarbeitungsschleife (läuft in separatem Thread).
        """
        while self.running:
            try:
                # Regelmäßig Summary-Daten anfordern
                current_time = time.time()
                if current_time - self.last_summary_request >= self.summary_interval:
                    self._send_command("AT+S,1")  # Summary mit Sunray-State
                    self.last_summary_request = current_time
                
                # Sensor-Daten lesen
                line = self.pico.read_sensor_data() if self.pico else ""
                if line:
                    data = self._process_pico_data(line)
                    if data:
                        with self.lock:
                            self.latest_sensor_data.update(data)
                            self.last_update_time = current_time
                        
                        # Callbacks ausführen
                        self._execute_callbacks(data)
                        
                        # Kommunikationsfehler zurücksetzen
                        self.communication_errors = 0
                
                time.sleep(0.01)  # 100Hz Datenrate
                
            except Exception as e:
                self.communication_errors += 1
                if self.communication_errors >= self.max_communication_errors:
                    print(f"HardwareManager: Zu viele Kommunikationsfehler: {e}")
                    self.hardware_connected = False
                time.sleep(0.1)
    
    def _process_pico_data(self, line: str) -> Dict[str, Any]:
        """
        Verarbeitet ASCII-Sensordaten vom Pico.
        
        Args:
            line (str): Rohe ASCII-Zeile vom Pico
            
        Returns:
            Dict: Verarbeitete Sensor-Daten
        """
        if line.startswith("AT+S:"):
            # Normale Sensordaten: AT+S:odom_right,odom_left,odom_mow,chg_voltage,,bumper,lift
            parts = line[5:].split(",")
            if len(parts) >= 7:
                return {
                    "odom_right": int(parts[0]) if parts[0] else 0,
                    "odom_left": int(parts[1]) if parts[1] else 0,
                    "odom_mow": int(parts[2]) if parts[2] else 0,
                    "chg_voltage": float(parts[3]) if parts[3] else 0.0,
                    "bumper": int(parts[5]) if parts[5] else 0,
                    "lift": int(parts[6]) if parts[6] else 0,
                }
        elif line.startswith("S,"):
            # Summary-Daten: S,batVoltageLP,chgVoltage,chgCurrentLP,lift,bumper,raining,motorOverload,mowCurrLP,motorLeftCurrLP,motorRightCurrLP,batteryTemp
            parts = line[2:].split(",")
            if len(parts) >= 11:
                return {
                    "bat_voltage": float(parts[0]) if parts[0] else 0.0,
                    "chg_voltage": float(parts[1]) if parts[1] else 0.0,
                    "chg_current": float(parts[2]) if parts[2] else 0.0,
                    "lift": int(parts[3]) if parts[3] else 0,
                    "bumper": int(parts[4]) if parts[4] else 0,
                    "raining": int(parts[5]) if parts[5] else 0,
                    "motor_overload": int(parts[6]) if parts[6] else 0,
                    "mow_current": float(parts[7]) if parts[7] else 0.0,
                    "motor_left_current": float(parts[8]) if parts[8] else 0.0,
                    "motor_right_current": float(parts[9]) if parts[9] else 0.0,
                    "battery_temp": float(parts[10]) if parts[10] else 0.0,
                }
        return {}
    
    def _execute_callbacks(self, data: Dict[str, Any]) -> None:
        """
        Führt registrierte Callbacks für neue Sensor-Daten aus.
        
        Args:
            data (Dict): Neue Sensor-Daten
        """
        for callback_name, callback_func in self.data_callbacks.items():
            try:
                callback_func(data)
            except Exception as e:
                print(f"HardwareManager: Fehler in Callback '{callback_name}': {e}")
    
    def register_data_callback(self, name: str, callback: Callable[[Dict], None]) -> None:
        """
        Registriert einen Callback für Sensor-Datenverarbeitung.
        
        Args:
            name (str): Name des Callbacks
            callback (Callable): Funktion die bei neuen Daten aufgerufen wird
        """
        self.data_callbacks[name] = callback
        print(f"HardwareManager: Callback '{name}' registriert")
    
    def unregister_data_callback(self, name: str) -> None:
        """
        Entfernt einen registrierten Callback.
        
        Args:
            name (str): Name des zu entfernenden Callbacks
        """
        if name in self.data_callbacks:
            del self.data_callbacks[name]
            print(f"HardwareManager: Callback '{name}' entfernt")
    
    def get_latest_sensor_data(self) -> Dict[str, Any]:
        """
        Gibt die neuesten Sensor-Daten zurück.
        
        Returns:
            Dict: Aktuelle Sensor-Daten (Thread-sicher)
        """
        with self.lock:
            return self.latest_sensor_data.copy()
    
    def _send_command(self, command: str) -> bool:
        """
        Sendet einen Befehl an den Pico (interne Methode).
        
        Args:
            command (str): AT-Befehl
            
        Returns:
            bool: True wenn erfolgreich gesendet
        """
        if not self.pico or not self.hardware_connected:
            return False
        
        try:
            self.pico.send_command(command)
            return True
        except Exception as e:
            print(f"HardwareManager: Fehler beim Senden von '{command}': {e}")
            return False
    
    # Öffentliche Hardware-Schnittstellen
    
    def send_motor_command(self, left_pwm: int, right_pwm: int, mow_pwm: int) -> bool:
        """
        Sendet Motor-PWM-Befehle an den Pico.
        
        Args:
            left_pwm (int): PWM-Wert linker Motor (-255 bis 255)
            right_pwm (int): PWM-Wert rechter Motor (-255 bis 255)
            mow_pwm (int): PWM-Wert Mähmotor (0 bis 255)
            
        Returns:
            bool: True wenn erfolgreich gesendet
        """
        command = f"AT+MOTOR,{left_pwm},{right_pwm},{mow_pwm}"
        return self._send_command(command)
    
    def send_stop_command(self) -> bool:
        """
        Sendet Notfall-Stopp-Befehl an den Pico.
        
        Returns:
            bool: True wenn erfolgreich gesendet
        """
        return self._send_command("AT+STOP")
    
    def send_buzzer_command(self, frequency: int, duration: int) -> bool:
        """
        Sendet Buzzer-Befehl an den Pico.
        
        Args:
            frequency (int): Frequenz in Hz
            duration (int): Dauer in Millisekunden
            
        Returns:
            bool: True wenn erfolgreich gesendet
        """
        command = f"AT+BUZZER,{frequency},{duration}"
        return self._send_command(command)
    
    def send_led_command(self, led_id: int, state: bool) -> bool:
        """
        Sendet LED-Steuerungsbefehl an den Pico.
        
        Args:
            led_id (int): LED-Nummer
            state (bool): Ein/Aus-Zustand
            
        Returns:
            bool: True wenn erfolgreich gesendet
        """
        command = f"AT+LED,{led_id},{1 if state else 0}"
        return self._send_command(command)
    
    def request_sensor_data(self) -> bool:
        """
        Fordert aktuelle Sensor-Daten vom Pico an.
        
        Returns:
            bool: True wenn erfolgreich angefordert
        """
        return self._send_command("AT+S")
    
    def is_connected(self) -> bool:
        """
        Prüft ob Hardware-Verbindung aktiv ist.
        
        Returns:
            bool: True wenn verbunden
        """
        return self.hardware_connected
    
    def get_connection_status(self) -> Dict[str, Any]:
        """
        Gibt detaillierten Verbindungsstatus zurück.
        
        Returns:
            Dict: Status-Informationen
        """
        return {
            "connected": self.hardware_connected,
            "port": self.port,
            "baudrate": self.baudrate,
            "communication_errors": self.communication_errors,
            "last_update": self.last_update_time,
            "data_age": time.time() - self.last_update_time if self.last_update_time > 0 else 0
        }
    
    def get_pico_comm(self) -> Optional[PicoComm]:
        """
        Gibt direkten Zugriff auf PicoComm für Legacy-Code.
        
        DEPRECATED: Sollte nur für Übergangszeit verwendet werden.
        Neue Implementierungen sollten HardwareManager-Methoden verwenden.
        
        Returns:
            Optional[PicoComm]: PicoComm-Instanz oder None
        """
        return self.pico

# Globale Hardware-Manager-Instanz (Singleton-Pattern)
_hardware_manager_instance = None

def get_hardware_manager(port='/dev/ttyS0', baudrate=115200):
    """Gibt eine Singleton-Instanz des HardwareManagers zurück."""
    global _hardware_manager_instance
    if _hardware_manager_instance is None:
        _hardware_manager_instance = HardwareManager(port, baudrate)
    return _hardware_manager_instance

def shutdown_hardware_manager():
    """Schließt den globalen HardwareManager."""
    global _hardware_manager_instance
    if _hardware_manager_instance is not None:
        _hardware_manager_instance.stop()
        _hardware_manager_instance = None

def initialize_hardware(port: str = '/dev/ttyS0', baudrate: int = 115200) -> bool:
    """
    Initialisiert die globale Hardware-Manager-Instanz.
    
    Args:
        port (str): Serieller Port
        baudrate (int): Baudrate
        
    Returns:
        bool: True wenn erfolgreich initialisiert
    """
    global _hardware_manager_instance
    _hardware_manager_instance = HardwareManager(port, baudrate)
    return _hardware_manager_instance.begin()

def shutdown_hardware() -> None:
    """
    Beendet die Hardware-Kommunikation sauber.
    """
    global _hardware_manager_instance
    if _hardware_manager_instance:
        _hardware_manager_instance.stop()
        _hardware_manager_instance = None