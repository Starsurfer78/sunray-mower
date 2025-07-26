#!/usr/bin/env python3
"""
Konfigurationsverwaltung für Sunray Python Mähroboter.

Dieses Modul verwaltet alle Systemeinstellungen in JSON-Format und bietet:
- Automatisches Laden von Standardwerten aus config_example.json
- Sichere Konfigurationsverwaltung mit Validierung
- Fallback-Mechanismen für robuste Systemfunktion
- Einfache API für Konfigurationszugriff

Verwendung:
    from config import get_config
    config = get_config()
    motor_kp = config.get('motor.pid.left.kp', 1.0)
    config.set('motor.pid.left.kp', 1.5)

Autor: Sunray Python Team
Version: 1.0
"""

import json
import os
from typing import Any, Dict, Optional

class Config:
    """
    Zentrale Konfigurationsverwaltung für Sunray Python Mähroboter.
    
    Diese Klasse verwaltet alle Systemeinstellungen in einer JSON-Datei und bietet:
    - Automatisches Laden von Standardwerten
    - Sichere Konfigurationszugriffe mit Fallback-Werten
    - Validierung von Konfigurationsparametern
    - Persistente Speicherung von Änderungen
    
    Beispiel:
        config = Config('/etc/mower/config.json')
        kp_value = config.get('motor.pid.left.kp')
        config.set('motor.pid.left.kp', 1.5)
        config.save_config()
    """
    
    def __init__(self, config_file: str = "/etc/mower/config.json"):
        """
        Initialisiert die Konfigurationsverwaltung.
        
        Lädt die Konfiguration aus der angegebenen Datei und stellt sicher,
        dass alle erforderlichen Standardwerte vorhanden sind.
        
        Args:
            config_file (str): Pfad zur Konfigurationsdatei.
                             Standard: '/etc/mower/config.json'
                             Beispiel: '/home/user/my_mower_config.json'
        
        Raises:
            Keine - Fehler werden abgefangen und geloggt
        
        Beispiel:
            # Standard-Konfiguration
            config = Config()
            
            # Benutzerdefinierte Konfigurationsdatei
            config = Config('/path/to/my/config.json')
        """
        self.config_file = config_file
        self.config = self._load_config()
        self._ensure_default_config()
    
    def _load_config(self) -> Dict:
        """
        Lädt die Konfiguration aus der JSON-Datei.
        
        Versucht die Konfigurationsdatei zu laden und zu parsen.
        Bei Fehlern wird eine leere Konfiguration zurückgegeben.
        
        Returns:
            Dict: Geladene Konfiguration oder leeres Dictionary bei Fehlern
            
        Beispiele für mögliche Fehler:
            - Datei existiert nicht
            - JSON-Syntax-Fehler
            - Keine Leseberechtigung
        """
        try:
            if os.path.exists(self.config_file):
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            else:
                print(f"Config: Konfigurationsdatei {self.config_file} nicht gefunden, verwende Standardwerte")
                return {}
        except Exception as e:
            print(f"Config: Fehler beim Laden der Konfiguration: {e}")
            return {}
    
    def _ensure_default_config(self) -> None:
        """
        Stellt sicher, dass alle Standard-Konfigurationswerte vorhanden sind.
        
        Führt einen Merge zwischen der geladenen Konfiguration und den
        Standardwerten durch. Fehlende Werte werden automatisch ergänzt.
        Die aktualisierte Konfiguration wird automatisch gespeichert.
        
        Beispiel:
            Wenn 'motor.pid.left.kp' in der Datei fehlt, wird der
            Standardwert 1.0 automatisch hinzugefügt.
        """
        defaults = self._get_default_config()
        
        # Merge defaults with existing config
        self._merge_defaults(self.config, defaults)
        
        # Save updated config
        self.save_config()
    
    def _merge_defaults(self, config: Dict, defaults: Dict) -> None:
        """
        Fügt fehlende Standardwerte rekursiv zur Konfiguration hinzu.
        
        Durchläuft die Standardkonfiguration und fügt alle fehlenden
        Schlüssel zur aktuellen Konfiguration hinzu, ohne bestehende
        Werte zu überschreiben.
        
        Args:
            config (Dict): Aktuelle Konfiguration (wird modifiziert)
            defaults (Dict): Standardwerte zum Hinzufügen
            
        Beispiel:
            config = {'motor': {'pid': {'left': {'kp': 1.5}}}}
            defaults = {'motor': {'pid': {'left': {'ki': 0.1, 'kd': 0.05}}}}
            # Nach dem Merge: config enthält kp=1.5, ki=0.1, kd=0.05
        """
        for key, value in defaults.items():
            if key not in config:
                config[key] = value
            elif isinstance(value, dict) and isinstance(config[key], dict):
                self._merge_defaults(config[key], value)
    
    def _get_default_config(self) -> Dict:
        """Gibt die Standard-Konfiguration zurück.
        
        Lädt die Standardwerte aus der Beispiel-Konfigurationsdatei.
        Falls diese nicht verfügbar ist, werden hardcodierte Fallback-Werte verwendet.
        """
        # Versuche zuerst die Beispiel-Konfigurationsdatei zu laden
        example_config_path = os.path.join(os.path.dirname(__file__), 'config_example.json')
        
        try:
            if os.path.exists(example_config_path):
                with open(example_config_path, 'r', encoding='utf-8') as f:
                    return json.load(f)
        except Exception as e:
            print(f"Config: Warnung - Konnte Beispiel-Konfiguration nicht laden: {e}")
        
        # Fallback auf minimale hardcodierte Standardwerte
        return {
            "motor": {
                "pid": {
                    "left": {"kp": 1.0, "ki": 0.1, "kd": 0.05, "output_min": -255, "output_max": 255},
                    "right": {"kp": 1.0, "ki": 0.1, "kd": 0.05, "output_min": -255, "output_max": 255},
                    "mow": {"kp": 0.8, "ki": 0.05, "kd": 0.02, "output_min": 0, "output_max": 255}
                },
                "limits": {"max_motor_current": 3.0, "max_mow_current": 5.0, "max_overload_count": 5, "max_realistic_speed": 2.0},
                "physical": {"ticks_per_meter": 1000, "wheel_base": 0.3, "pwm_scale_factor": 100},
                "mow": {"default_pwm": 100, "min_current_threshold": 0.1, "max_current_threshold": 0.5},
                "adaptive": {"enabled": True, "current_threshold_factor": 0.7, "min_speed_factor": 0.3}
            },
            "system": {"debug": False, "log_level": "INFO", "mqtt_enabled": True, "web_gui_enabled": True},
            "safety": {"emergency_stop_enabled": True, "lift_detection_enabled": True, "tilt_detection_enabled": True, "max_tilt_angle": 30.0},
            "navigation": {"gps_enabled": True, "imu_enabled": True, "obstacle_detection_enabled": True}
        }
    
    def save_config(self) -> bool:
        """Speichert die Konfiguration in der Datei."""
        try:
            # Erstelle Verzeichnis falls es nicht existiert
            os.makedirs(os.path.dirname(self.config_file), exist_ok=True)
            
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(self.config, f, indent=2, ensure_ascii=False)
            return True
        except Exception as e:
            print(f"Config: Fehler beim Speichern der Konfiguration: {e}")
            return False
    
    def get(self, key: str, default: Any = None) -> Any:
        """
        Gibt den Konfigurationswert für den angegebenen Schlüssel zurück.
        
        Verwendet Punkt-Notation für verschachtelte Konfigurationswerte.
        Gibt den Standardwert zurück, wenn der Schlüssel nicht existiert.
        
        Args:
            key (str): Schlüssel im Format 'section.subsection.key'
                      Beispiele:
                      - 'motor.pid.left.kp'
                      - 'system.debug'
                      - 'safety.max_tilt_angle'
            default (Any): Standardwert falls Schlüssel nicht existiert
                          Beispiele: 1.0, True, "INFO", []
        
        Returns:
            Any: Konfigurationswert oder Standardwert
        
        Beispiele:
            # PID-Parameter abrufen
            kp = config.get('motor.pid.left.kp', 1.0)
            
            # System-Einstellung mit Fallback
            debug = config.get('system.debug', False)
            
            # Komplexe Struktur abrufen
            pid_config = config.get('motor.pid.left', {})
        """
        keys = key.split('.')
        value = self.config
        
        for k in keys:
            if isinstance(value, dict) and k in value:
                value = value[k]
            else:
                return default
        
        return value
    
    def set(self, key: str, value: Any) -> bool:
        """
        Setzt den Konfigurationswert für den angegebenen Schlüssel.
        
        Erstellt automatisch fehlende Zwischensektionen und speichert
        die Konfiguration persistent in der Datei.
        
        Args:
            key (str): Schlüssel im Format 'section.subsection.key'
                      Beispiele:
                      - 'motor.pid.left.kp'
                      - 'system.debug'
                      - 'safety.max_tilt_angle'
            value (Any): Zu setzender Wert
                        Beispiele:
                        - Zahlen: 1.5, 100, 3.0
                        - Booleans: True, False
                        - Strings: "INFO", "DEBUG"
                        - Listen/Dicts: [], {}
        
        Returns:
            bool: True wenn erfolgreich gespeichert, False bei Fehlern
        
        Beispiele:
            # PID-Parameter setzen
            success = config.set('motor.pid.left.kp', 1.5)
            
            # Debug-Modus aktivieren
            config.set('system.debug', True)
            
            # Neue Sektion erstellen
            config.set('custom.new_feature.enabled', True)
        """
        keys = key.split('.')
        config = self.config
        
        # Navigiere zu der gewünschten Sektion
        for k in keys[:-1]:
            if k not in config:
                config[k] = {}
            config = config[k]
        
        # Setze den Wert
        config[keys[-1]] = value
        
        return self.save_config()
    
    def get_motor_config(self) -> Dict:
        """
        Gibt die komplette Motor-Konfiguration zurück.
        
        Praktische Hilfsfunktion für den Zugriff auf alle motorbezogenen
        Einstellungen in einem Dictionary.
        
        Returns:
            Dict: Komplette Motor-Konfiguration mit allen Subsektionen:
                 - pid: PID-Parameter für alle Motoren
                 - limits: Stromgrenzen und Sicherheitswerte
                 - physical: Physikalische Parameter (Radstand, etc.)
                 - mow: Mähmotor-spezifische Einstellungen
                 - adaptive: Adaptive Geschwindigkeitsregelung
        
        Beispiel:
            motor_config = config.get_motor_config()
            left_kp = motor_config['pid']['left']['kp']
            max_current = motor_config['limits']['max_motor_current']
        """
        return self.get('motor', {})
    
    def get_pid_config(self, motor: str) -> Dict:
        """
        Gibt PID-Konfiguration für einen bestimmten Motor zurück.
        
        Praktische Hilfsfunktion für den direkten Zugriff auf PID-Parameter
        eines spezifischen Motors.
        
        Args:
            motor (str): Motor-Bezeichnung
                        Gültige Werte:
                        - 'left': Linker Antriebsmotor
                        - 'right': Rechter Antriebsmotor  
                        - 'mow': Mähmotor
        
        Returns:
            Dict: PID-Konfiguration mit Schlüsseln:
                 - kp: Proportionalfaktor
                 - ki: Integralfaktor
                 - kd: Differentialfaktor
                 - output_min: Minimaler PWM-Wert
                 - output_max: Maximaler PWM-Wert
        
        Beispiele:
            # Linker Motor PID-Parameter
            left_pid = config.get_pid_config('left')
            kp = left_pid['kp']
            
            # Mähmotor PID-Parameter
            mow_pid = config.get_pid_config('mow')
            max_pwm = mow_pid['output_max']
        """
        return self.get(f'motor.pid.{motor}', {})
    
    def get_motor_limits(self) -> Dict:
        """
        Gibt alle Motor-Grenzwerte für Sicherheit und Schutz zurück.
        
        Returns:
            Dict: Motor-Grenzwerte mit Schlüsseln:
                 - max_motor_current: Maximaler Antriebsmotor-Strom (A)
                 - max_mow_current: Maximaler Mähmotor-Strom (A)
                 - max_overload_count: Anzahl Überlastungen vor Notaus
                 - max_realistic_speed: Maximale Geschwindigkeit (m/s)
        
        Beispiel:
            limits = config.get_motor_limits()
            if current > limits['max_motor_current']:
                # Überlastung erkannt
                motor.emergency_stop()
        """
        return self.get('motor.limits', {})
    
    def get_physical_config(self) -> Dict:
        """Gibt physikalische Motor-Parameter zurück."""
        return self.get('motor.physical', {})
    
    def reload(self) -> bool:
        """Lädt die Konfiguration neu aus der Datei."""
        try:
            self.config = self._load_config()
            self._ensure_default_config()
            return True
        except Exception as e:
            print(f"Config: Fehler beim Neuladen der Konfiguration: {e}")
            return False
    
    def reset_to_defaults(self) -> bool:
        """Setzt die Konfiguration auf Standardwerte zurück."""
        try:
            self.config = self._get_default_config()
            return self.save_config()
        except Exception as e:
            print(f"Config: Fehler beim Zurücksetzen der Konfiguration: {e}")
            return False
    
    def validate_config(self) -> bool:
        """
        Validiert die aktuelle Konfiguration auf Vollständigkeit und Konsistenz.
        
        Überprüft:
        - Vorhandensein aller erforderlichen Motor-Parameter
        - Gültigkeit der PID-Parameter für alle Motoren
        - Vorhandensein aller Sicherheitsgrenzwerte
        
        Returns:
            bool: True wenn Konfiguration gültig, False bei Fehlern
        
        Beispiel:
            if not config.validate_config():
                print("Konfiguration unvollständig - verwende Standardwerte")
                config.reset_to_defaults()
        """
        try:
            # Prüfe Motor-Konfiguration
            motor_config = self.get_motor_config()
            if not motor_config:
                return False
            
            # Prüfe PID-Parameter
            for motor in ['left', 'right', 'mow']:
                pid_config = self.get_pid_config(motor)
                required_keys = ['kp', 'ki', 'kd', 'output_min', 'output_max']
                if not all(key in pid_config for key in required_keys):
                    return False
            
            # Prüfe Grenzwerte
            limits = self.get_motor_limits()
            required_limits = ['max_motor_current', 'max_mow_current', 'max_overload_count']
            if not all(key in limits for key in required_limits):
                return False
            
            return True
        except Exception as e:
            print(f"Config: Fehler bei der Validierung: {e}")
            return False

# Globale Konfigurationsinstanz
_config_instance = None

def get_config(config_file: str = "/etc/mower/config.json") -> Config:
    """Gibt die globale Konfigurationsinstanz zurück."""
    global _config_instance
    if _config_instance is None:
        _config_instance = Config(config_file)
    return _config_instance

def reload_config() -> bool:
    """Lädt die globale Konfiguration neu."""
    global _config_instance
    if _config_instance is not None:
        return _config_instance.reload()
    return False