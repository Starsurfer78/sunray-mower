#!/usr/bin/env python3
"""
Mock Hardware Module für Entwicklung und Tests
Ersetzt Hardware-spezifische Module wenn diese nicht verfügbar sind
"""

import time
import random
import math
from typing import Dict, Any, Optional, Tuple

class MockIMUSensor:
    """Mock IMU Sensor für Entwicklung"""
    
    def __init__(self):
        self.is_connected = True
        self.calibrated = True
        self._yaw = 0.0
        self._pitch = 0.0
        self._roll = 0.0
        self._accel_x = 0.0
        self._accel_y = 0.0
        self._accel_z = 9.81
        self._gyro_x = 0.0
        self._gyro_y = 0.0
        self._gyro_z = 0.0
        
    def update(self):
        """Simuliert IMU Datenaktualisierung"""
        # Simuliere kleine zufällige Bewegungen
        self._yaw += random.uniform(-0.1, 0.1)
        self._pitch += random.uniform(-0.05, 0.05)
        self._roll += random.uniform(-0.05, 0.05)
        
        # Simuliere Beschleunigungsdaten
        self._accel_x = random.uniform(-0.5, 0.5)
        self._accel_y = random.uniform(-0.5, 0.5)
        self._accel_z = 9.81 + random.uniform(-0.2, 0.2)
        
        # Simuliere Gyroskopdaten
        self._gyro_x = random.uniform(-0.1, 0.1)
        self._gyro_y = random.uniform(-0.1, 0.1)
        self._gyro_z = random.uniform(-0.1, 0.1)
        
    @property
    def yaw(self) -> float:
        return self._yaw
        
    @property
    def pitch(self) -> float:
        return self._pitch
        
    @property
    def roll(self) -> float:
        return self._roll
        
    @property
    def accel_x(self) -> float:
        return self._accel_x
        
    @property
    def accel_y(self) -> float:
        return self._accel_y
        
    @property
    def accel_z(self) -> float:
        return self._accel_z
        
    @property
    def gyro_x(self) -> float:
        return self._gyro_x
        
    @property
    def gyro_y(self) -> float:
        return self._gyro_y
        
    @property
    def gyro_z(self) -> float:
        return self._gyro_z
        
    def get_acceleration(self) -> Tuple[float, float, float]:
        """Gibt Beschleunigungsdaten zurück"""
        return (self._accel_x, self._accel_y, self._accel_z)
        
    def get_gyroscope(self) -> Tuple[float, float, float]:
        """Gibt Gyroskopdaten zurück"""
        return (self._gyro_x, self._gyro_y, self._gyro_z)
        
    def get_orientation(self) -> Tuple[float, float, float]:
        """Gibt Orientierungsdaten zurück"""
        return (self._yaw, self._pitch, self._roll)

class MockGPSModule:
    """Mock GPS Modul für Entwicklung"""
    
    def __init__(self):
        self.is_connected = True
        self.has_fix = True
        self.latitude = 52.5200  # Berlin
        self.longitude = 13.4050
        self.altitude = 34.0
        self.speed = 0.0
        self.course = 0.0
        self.hdop = 1.0
        self.satellites = 8
        
    def update(self):
        """Simuliert GPS Datenaktualisierung"""
        # Simuliere kleine GPS-Drift
        self.latitude += random.uniform(-0.00001, 0.00001)
        self.longitude += random.uniform(-0.00001, 0.00001)
        self.altitude += random.uniform(-0.1, 0.1)
        self.speed = max(0, self.speed + random.uniform(-0.1, 0.1))
        self.course += random.uniform(-1, 1)
        self.hdop = max(0.5, min(3.0, self.hdop + random.uniform(-0.1, 0.1)))
        
    def get_position(self) -> Tuple[float, float, float]:
        """Gibt Position zurück"""
        return (self.latitude, self.longitude, self.altitude)
        
    def get_speed_course(self) -> Tuple[float, float]:
        """Gibt Geschwindigkeit und Kurs zurück"""
        return (self.speed, self.course)

class MockPicoComm:
    """Mock Pico Kommunikation für Entwicklung"""
    
    def __init__(self):
        self.is_connected = True
        self.motor_left_speed = 0
        self.motor_right_speed = 0
        self.motor_mow_speed = 0
        self.bumper_left = False
        self.bumper_right = False
        self.current_left = 0.5
        self.current_right = 0.5
        self.current_mow = 0.3
        self.battery_voltage = 24.5
        
    def send_command(self, command: str) -> bool:
        """Simuliert Kommando senden"""
        print(f"Mock Pico Command: {command}")
        return True
        
    def set_motor_speeds(self, left: float, right: float, mow: float = 0):
        """Setzt Motorgeschwindigkeiten"""
        self.motor_left_speed = left
        self.motor_right_speed = right
        self.motor_mow_speed = mow
        
    def get_sensor_data(self) -> Dict[str, Any]:
        """Gibt Sensordaten zurück"""
        # Simuliere Bumper basierend auf zufälligen Ereignissen
        if random.random() < 0.01:  # 1% Chance für Bumper-Aktivierung
            self.bumper_left = random.choice([True, False])
            self.bumper_right = random.choice([True, False])
        else:
            self.bumper_left = False
            self.bumper_right = False
            
        # Simuliere Stromverbrauch basierend auf Motorgeschwindigkeiten
        self.current_left = 0.3 + abs(self.motor_left_speed) * 0.5
        self.current_right = 0.3 + abs(self.motor_right_speed) * 0.5
        self.current_mow = 0.2 + abs(self.motor_mow_speed) * 0.8
        
        # Simuliere Batteriespannung
        self.battery_voltage = max(20.0, 24.5 + random.uniform(-0.5, 0.1))
        
        return {
            'bumper_left': self.bumper_left,
            'bumper_right': self.bumper_right,
            'current_left': self.current_left,
            'current_right': self.current_right,
            'current_mow': self.current_mow,
            'battery_voltage': self.battery_voltage,
            'motor_left_speed': self.motor_left_speed,
            'motor_right_speed': self.motor_right_speed,
            'motor_mow_speed': self.motor_mow_speed
        }

def create_mock_hardware():
    """Erstellt Mock Hardware Instanzen"""
    return {
        'imu': MockIMUSensor(),
        'gps': MockGPSModule(),
        'pico': MockPicoComm()
    }

# Automatische Mock-Erkennung
def is_hardware_available() -> bool:
    """Prüft ob echte Hardware verfügbar ist"""
    try:
        import board
        return True
    except (ImportError, NotImplementedError):
        return False

def get_hardware_or_mock():
    """Gibt echte Hardware oder Mock zurück"""
    if is_hardware_available():
        try:
            from imu import IMUSensor
            from gps_module import GPSModule
            from pico_comm import PicoComm
            return {
                'imu': IMUSensor(),
                'gps': GPSModule(),
                'pico': PicoComm()
            }
        except ImportError:
            print("Hardware Module nicht verfügbar, verwende Mock")
            return create_mock_hardware()
    else:
        print("Hardware nicht erkannt, verwende Mock")
        return create_mock_hardware()