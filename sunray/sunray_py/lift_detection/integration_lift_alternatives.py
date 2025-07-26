#!/usr/bin/env python3
"""
Integration der alternativen Lift-Erkennung in das Sunray-System

Dieses Skript zeigt, wie IMU und GPS als Ersatz für den Hardware-Lift-Sensor
verwendet und in die bestehende Sicherheitslogik integriert werden können.

Autor: Sunray Python Team
Datum: 2024-01-01
"""

import time
import threading
from typing import Dict, Optional
from .lift_detection_alternatives import AlternativeLiftDetector, LiftDetectionResult

class IntegratedLiftSafety:
    """
    Integriert alternative Lift-Erkennung in das Sunray-Sicherheitssystem.
    Kombiniert Hardware-Lift-Sensor (falls vorhanden) mit IMU/GPS-basierter Erkennung.
    """
    
    def __init__(self, motor, imu, gps, config: Dict = None):
        self.motor = motor
        self.imu = imu
        self.gps = gps
        self.config = config or self._get_default_config()
        
        # Alternative Lift-Erkennung initialisieren
        self.alt_detector = AlternativeLiftDetector(self.config.get('alternative_lift', {}))
        
        # Zustandsvariablen
        self.hardware_lift_available = self.config.get('hardware_lift_sensor', False)
        self.last_lift_state = False
        self.lift_confirmed_time = None
        self.emergency_stop_triggered = False
        
        # Kalibrierung
        self.calibration_required = True
        self.calibration_thread = None
        
        # Statistiken
        self.detection_stats = {
            'hardware_detections': 0,
            'imu_detections': 0,
            'gps_detections': 0,
            'combined_detections': 0,
            'false_positives': 0
        }
        
    def _get_default_config(self) -> Dict:
        """Standard-Konfiguration für integrierte Lift-Erkennung"""
        return {
            'hardware_lift_sensor': False,  # Hardware-Sensor verfügbar?
            'fallback_mode': True,  # IMU/GPS als Fallback verwenden?
            'hybrid_mode': True,  # Hardware + IMU/GPS kombinieren?
            
            # Sicherheitsparameter
            'emergency_stop_delay': 0.5,  # Sekunden bis Notaus
            'auto_calibration': True,  # Automatische Kalibrierung
            'calibration_interval': 300,  # Sekunden zwischen Kalibrierungen
            
            # Alternative Lift-Erkennung
            'alternative_lift': {
                'imu_enabled': True,
                'gps_enabled': True,
                'confidence_threshold': 0.75,
                'confirmation_time': 0.3,
            },
            
            # Logging und Debugging
            'debug_mode': False,
            'log_detections': True,
        }
    
    def start(self):
        """Startet das integrierte Lift-Erkennungssystem"""
        print("Starte integriertes Lift-Erkennungssystem...")
        
        # Automatische Kalibrierung starten
        if self.config['auto_calibration'] and self.calibration_required:
            self._start_calibration()
        
        print(f"Hardware-Lift-Sensor: {'Verfügbar' if self.hardware_lift_available else 'Nicht verfügbar'}")
        print(f"Alternative Erkennung: {'Aktiviert' if not self.hardware_lift_available else 'Fallback-Modus'}")
    
    def update(self, pico_data: Dict = None) -> bool:
        """
        Hauptfunktion für Lift-Erkennung.
        
        Args:
            pico_data: Daten vom Pico (enthält Hardware-Lift-Sensor falls verfügbar)
            
        Returns:
            bool: True wenn Lift erkannt wurde
        """
        current_time = time.time()
        lift_detected = False
        detection_source = "none"
        
        # 1. Hardware-Lift-Sensor prüfen (falls verfügbar)
        hardware_lift = self._check_hardware_lift(pico_data)
        
        # 2. Alternative Erkennung (IMU/GPS)
        imu_data = self._get_imu_data()
        gps_data = self._get_gps_data()
        motor_data = self._get_motor_data()
        
        alt_result = self.alt_detector.update(imu_data, gps_data, motor_data)
        
        # 3. Ergebnisse kombinieren
        if self.hardware_lift_available:
            if self.config['hybrid_mode']:
                # Hybrid-Modus: Hardware + Alternative
                lift_detected = hardware_lift or alt_result.is_lifted
                detection_source = self._determine_detection_source(hardware_lift, alt_result)
            else:
                # Nur Hardware-Sensor
                lift_detected = hardware_lift
                detection_source = "hardware" if hardware_lift else "none"
        else:
            # Nur alternative Erkennung
            lift_detected = alt_result.is_lifted
            detection_source = alt_result.detection_method
        
        # 4. Sicherheitslogik anwenden
        if lift_detected != self.last_lift_state:
            self._handle_lift_state_change(lift_detected, detection_source, current_time)
        
        # 5. Notfall-Stopp prüfen
        if lift_detected and not self.emergency_stop_triggered:
            self._check_emergency_stop(current_time)
        
        # 6. Statistiken aktualisieren
        self._update_statistics(hardware_lift, alt_result, detection_source)
        
        # 7. Debug-Ausgabe
        if self.config['debug_mode']:
            self._debug_output(lift_detected, detection_source, alt_result)
        
        self.last_lift_state = lift_detected
        return lift_detected
    
    def _check_hardware_lift(self, pico_data: Dict) -> bool:
        """Prüft Hardware-Lift-Sensor aus Pico-Daten"""
        if not self.hardware_lift_available or not pico_data:
            return False
        
        # Lift-Status aus Pico-Daten extrahieren
        lift_status = pico_data.get('lift', 0)
        return bool(lift_status)
    
    def _get_imu_data(self) -> Dict:
        """Holt aktuelle IMU-Daten"""
        try:
            return self.imu.read() if self.imu else {}
        except Exception as e:
            if self.config['debug_mode']:
                print(f"IMU-Fehler: {e}")
            return {}
    
    def _get_gps_data(self) -> Dict:
        """Holt aktuelle GPS-Daten"""
        try:
            return self.gps.read() if self.gps else {}
        except Exception as e:
            if self.config['debug_mode']:
                print(f"GPS-Fehler: {e}")
            return {}
    
    def _get_motor_data(self) -> Dict:
        """Holt aktuelle Motor-Daten"""
        try:
            if hasattr(self.motor, 'get_status'):
                return self.motor.get_status()
            return {
                'left_speed': getattr(self.motor, 'left_speed_setpoint', 0),
                'right_speed': getattr(self.motor, 'right_speed_setpoint', 0),
                'mow_enabled': getattr(self.motor, 'mow_enabled', False)
            }
        except Exception as e:
            if self.config['debug_mode']:
                print(f"Motor-Daten-Fehler: {e}")
            return {}
    
    def _determine_detection_source(self, hardware_lift: bool, alt_result: LiftDetectionResult) -> str:
        """Bestimmt die primäre Erkennungsquelle"""
        if hardware_lift and alt_result.is_lifted:
            return "hardware+alternative"
        elif hardware_lift:
            return "hardware"
        elif alt_result.is_lifted:
            return alt_result.detection_method
        else:
            return "none"
    
    def _handle_lift_state_change(self, lift_detected: bool, source: str, timestamp: float):
        """Behandelt Änderungen im Lift-Status"""
        if lift_detected:
            print(f"⚠️  LIFT ERKANNT! Quelle: {source}")
            self.lift_confirmed_time = timestamp
            
            if self.config['log_detections']:
                self._log_detection(source, timestamp)
        else:
            print(f"✅ Roboter abgesetzt. Quelle: {source}")
            self.lift_confirmed_time = None
            self.emergency_stop_triggered = False
    
    def _check_emergency_stop(self, current_time: float):
        """Prüft ob Notfall-Stopp ausgelöst werden soll"""
        if not self.lift_confirmed_time:
            return
        
        time_since_lift = current_time - self.lift_confirmed_time
        
        if time_since_lift >= self.config['emergency_stop_delay']:
            print("🚨 NOTFALL-STOPP: Roboter angehoben!")
            
            # Motor stoppen
            try:
                if hasattr(self.motor, 'emergency_stop'):
                    self.motor.emergency_stop()
                elif hasattr(self.motor, 'stop_immediately'):
                    self.motor.stop_immediately()
                else:
                    # Fallback: Alle Geschwindigkeiten auf Null
                    self.motor.set_linear_angular_speed(0, 0)
                    if hasattr(self.motor, 'set_mow_state'):
                        self.motor.set_mow_state(False)
                
                self.emergency_stop_triggered = True
                print("✅ Notfall-Stopp ausgeführt")
                
            except Exception as e:
                print(f"❌ Fehler beim Notfall-Stopp: {e}")
    
    def _start_calibration(self):
        """Startet automatische Kalibrierung in separatem Thread"""
        def calibration_worker():
            print("🔧 Starte automatische Kalibrierung...")
            print("   Bitte stellen Sie sicher, dass der Roboter auf ebenem Boden steht.")
            
            time.sleep(2)  # Kurze Pause
            
            try:
                imu_data = self._get_imu_data()
                gps_data = self._get_gps_data()
                
                if imu_data or gps_data:
                    self.alt_detector.calibrate(imu_data, gps_data, duration=5.0)
                    self.calibration_required = False
                    print("✅ Kalibrierung abgeschlossen")
                else:
                    print("❌ Kalibrierung fehlgeschlagen: Keine Sensordaten")
                    
            except Exception as e:
                print(f"❌ Kalibrierungsfehler: {e}")
        
        self.calibration_thread = threading.Thread(target=calibration_worker, daemon=True)
        self.calibration_thread.start()
    
    def _update_statistics(self, hardware_lift: bool, alt_result: LiftDetectionResult, source: str):
        """Aktualisiert Erkennungsstatistiken"""
        if hardware_lift:
            self.detection_stats['hardware_detections'] += 1
        
        if alt_result.is_lifted:
            if 'imu' in alt_result.detection_method:
                self.detection_stats['imu_detections'] += 1
            elif 'gps' in alt_result.detection_method:
                self.detection_stats['gps_detections'] += 1
        
        if '+' in source:  # Kombinierte Erkennung
            self.detection_stats['combined_detections'] += 1
    
    def _log_detection(self, source: str, timestamp: float):
        """Protokolliert Lift-Erkennungen"""
        log_entry = {
            'timestamp': timestamp,
            'source': source,
            'time_str': time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(timestamp))
        }
        
        # Hier könnte eine echte Logging-Implementierung stehen
        print(f"📝 Log: {log_entry}")
    
    def _debug_output(self, lift_detected: bool, source: str, alt_result: LiftDetectionResult):
        """Debug-Ausgabe für Entwicklung"""
        print(f"DEBUG: Lift={lift_detected}, Quelle={source}, Alt-Konfidenz={alt_result.confidence:.2f}")
        if alt_result.details:
            print(f"       Details: {alt_result.details}")
    
    def get_statistics(self) -> Dict:
        """Gibt Erkennungsstatistiken zurück"""
        return self.detection_stats.copy()
    
    def reset_statistics(self):
        """Setzt Statistiken zurück"""
        for key in self.detection_stats:
            self.detection_stats[key] = 0
    
    def recalibrate(self):
        """Startet manuelle Neukalibrierung"""
        self.calibration_required = True
        self._start_calibration()


def demonstrate_integration():
    """Demonstriert die Integration der alternativen Lift-Erkennung"""
    print("=== Demonstration: Integrierte Lift-Erkennung ===")
    
    # Mock-Objekte für Demo
    class MockMotor:
        def __init__(self):
            self.left_speed_setpoint = 0
            self.right_speed_setpoint = 0
            self.mow_enabled = False
            self.emergency_stopped = False
        
        def emergency_stop(self):
            self.emergency_stopped = True
            self.left_speed_setpoint = 0
            self.right_speed_setpoint = 0
            self.mow_enabled = False
            print("🛑 Motor: Notfall-Stopp ausgeführt")
        
        def set_linear_angular_speed(self, linear, angular):
            # Vereinfachte Umrechnung
            self.left_speed_setpoint = linear - angular
            self.right_speed_setpoint = linear + angular
    
    class MockIMU:
        def __init__(self):
            self.lifted = False
        
        def read(self):
            if self.lifted:
                return {
                    'acceleration': [0.5, 1.0, 2.0],  # Reduzierte Gravitation
                    'gyro': [20.0, 15.0, 10.0],  # Erhöhte Rotation
                    'euler': [45.0, 20.0, 15.0]
                }
            else:
                return {
                    'acceleration': [0.1, -0.2, 9.8],  # Normale Gravitation
                    'gyro': [0.5, -0.3, 0.1],
                    'euler': [45.0, 2.0, 1.0]
                }
    
    class MockGPS:
        def __init__(self):
            self.altitude_offset = 0
        
        def read(self):
            return {
                'lat': 52.5200,
                'lon': 13.4050,
                'alt': 50.0 + self.altitude_offset,
                'hdop': 1.0
            }
    
    # Mock-Objekte erstellen
    motor = MockMotor()
    imu = MockIMU()
    gps = MockGPS()
    
    # Konfiguration für Demo
    config = {
        'hardware_lift_sensor': False,  # Kein Hardware-Sensor
        'fallback_mode': True,
        'hybrid_mode': True,
        'auto_calibration': True,
        'calibration_interval': 300,
        'alternative_lift': {
            'imu_enabled': True,
            'gps_enabled': True,
            'accel_threshold': 2.0,
            'gyro_threshold': 30.0,
            'free_fall_threshold': 7.0,
            'sudden_movement_threshold': 15.0,
            'altitude_threshold': 0.3,
            'altitude_rate_threshold': 0.5,
            'gps_accuracy_required': 2.0,
            'confidence_threshold': 0.6,  # Niedrigere Schwelle für Demo
            'confirmation_time': 0.2,
            'reset_time': 2.0,
            'moving_average_window': 5,
            'outlier_rejection_factor': 2.0,
            'stationary_threshold': 0.1
        },
        'emergency_stop_delay': 1.0,
        'debug_mode': True,
        'log_detections': True
    }
    
    # Integriertes System erstellen
    lift_safety = IntegratedLiftSafety(motor, imu, gps, config)
    lift_safety.start()
    
    print("\n--- Test 1: Normale Bedingungen ---")
    for i in range(3):
        lift_detected = lift_safety.update()
        print(f"Update {i+1}: Lift erkannt = {lift_detected}")
        time.sleep(0.5)
    
    print("\n--- Test 2: Roboter anheben (IMU-Simulation) ---")
    imu.lifted = True  # Lift-Bedingungen simulieren
    
    for i in range(5):
        lift_detected = lift_safety.update()
        print(f"Lift-Test {i+1}: Lift erkannt = {lift_detected}")
        if motor.emergency_stopped:
            print("   ⚠️  Notfall-Stopp wurde ausgelöst!")
            break
        time.sleep(0.3)
    
    print("\n--- Test 3: Roboter absetzen ---")
    imu.lifted = False
    gps.altitude_offset = 0
    
    for i in range(3):
        lift_detected = lift_safety.update()
        print(f"Absetzen {i+1}: Lift erkannt = {lift_detected}")
        time.sleep(0.5)
    
    # Statistiken anzeigen
    print("\n--- Statistiken ---")
    stats = lift_safety.get_statistics()
    for key, value in stats.items():
        print(f"{key}: {value}")


def create_config_example():
    """Erstellt eine Beispiel-Konfiguration für die Integration"""
    config = {
        "lift_detection": {
            "_description": "Konfiguration für Lift-Erkennung ohne Hardware-Sensor",
            
            "hardware_sensor_available": False,
            "_hardware_sensor_description": "Ist ein Hardware-Lift-Sensor verfügbar?",
            
            "use_imu_fallback": True,
            "_imu_fallback_description": "IMU als Fallback für Lift-Erkennung verwenden",
            
            "use_gps_fallback": True,
            "_gps_fallback_description": "GPS-Höhendaten für Lift-Erkennung verwenden",
            
            "imu_settings": {
                "acceleration_threshold": 3.0,
                "_acceleration_description": "Schwellenwert für Beschleunigungsänderung (m/s²)",
                
                "free_fall_threshold": 6.0,
                "_free_fall_description": "Schwellenwert für Freier-Fall-Erkennung (m/s²)",
                
                "gyro_threshold": 25.0,
                "_gyro_description": "Schwellenwert für Rotationserkennung (°/s)"
            },
            
            "gps_settings": {
                "altitude_threshold": 0.5,
                "_altitude_description": "Minimale Höhenänderung für Lift-Erkennung (m)",
                
                "altitude_rate_threshold": 0.3,
                "_altitude_rate_description": "Geschwindigkeit der Höhenänderung (m/s)",
                
                "accuracy_required": 2.0,
                "_accuracy_description": "Erforderliche GPS-Genauigkeit (m)"
            },
            
            "safety_settings": {
                "confidence_threshold": 0.75,
                "_confidence_description": "Mindest-Konfidenz für Lift-Alarm (0.0-1.0)",
                
                "confirmation_time": 0.5,
                "_confirmation_description": "Bestätigungszeit vor Alarm (Sekunden)",
                
                "emergency_stop_delay": 1.0,
                "_emergency_stop_description": "Verzögerung bis Notfall-Stopp (Sekunden)"
            }
        }
    }
    
    return config


if __name__ == "__main__":
    # Demonstration ausführen
    demonstrate_integration()
    
    print("\n" + "="*50)
    print("Beispiel-Konfiguration:")
    import json
    config = create_config_example()
    print(json.dumps(config, indent=2, ensure_ascii=False))