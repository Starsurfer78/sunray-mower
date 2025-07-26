#!/usr/bin/env python3
"""
Lift-Erkennung ohne dedizierten Lift-Sensor

Dieses Modul zeigt, wie IMU und GPS als Alternative zum Hardware-Lift-Sensor
verwendet werden können, um das Anheben des Mähroboters zu erkennen.

Autor: Sunray Python Team
Datum: 2024-01-01
"""

import time
import math
from typing import Dict, Optional, Tuple
from dataclasses import dataclass
from collections import deque

@dataclass
class LiftDetectionResult:
    """Ergebnis der Lift-Erkennung"""
    is_lifted: bool
    confidence: float  # 0.0 - 1.0
    detection_method: str
    details: Dict

class AlternativeLiftDetector:
    """
    Erkennt das Anheben des Mähroboters ohne dedizierten Lift-Sensor
    durch Analyse von IMU- und GPS-Daten.
    """
    
    def __init__(self, config: Dict = None):
        self.config = config or self._get_default_config()
        
        # Datenhistorie für Trend-Analyse
        self.accel_history = deque(maxlen=20)  # 1 Sekunde bei 20Hz
        self.altitude_history = deque(maxlen=10)  # 5 Sekunden bei 2Hz
        self.gyro_history = deque(maxlen=20)
        
        # Zustandsvariablen
        self.last_ground_altitude = None
        self.lift_start_time = None
        self.is_stationary = False
        self.baseline_established = False
        
        # Kalibrierungsdaten
        self.gravity_baseline = 9.81  # m/s²
        self.altitude_baseline = None
        self.noise_threshold = 0.5  # m/s² für Rauschfilterung
        
    def _get_default_config(self) -> Dict:
        """Standard-Konfiguration für Lift-Erkennung"""
        return {
            # IMU-basierte Erkennung
            'imu_enabled': True,
            'accel_threshold': 2.0,  # m/s² Abweichung von Gravitation
            'gyro_threshold': 30.0,  # Grad/s für Rotationserkennung
            'free_fall_threshold': 7.0,  # m/s² unter Gravitation
            'sudden_movement_threshold': 15.0,  # m/s² plötzliche Beschleunigung
            
            # GPS-basierte Erkennung
            'gps_enabled': True,
            'altitude_threshold': 0.3,  # Meter Höhenänderung
            'altitude_rate_threshold': 0.5,  # m/s Geschwindigkeit der Höhenänderung
            'gps_accuracy_required': 2.0,  # Meter horizontale Genauigkeit
            
            # Kombinierte Erkennung
            'confidence_threshold': 0.7,  # Mindest-Konfidenz für Lift-Alarm
            'confirmation_time': 0.5,  # Sekunden für Bestätigung
            'reset_time': 2.0,  # Sekunden bis Reset nach Absetzen
            
            # Filter und Rauschunterdrückung
            'moving_average_window': 5,
            'outlier_rejection_factor': 2.0,
            'stationary_threshold': 0.1,  # m/s für Stillstand-Erkennung
        }
    
    def update(self, imu_data: Dict, gps_data: Dict, motor_data: Dict = None) -> LiftDetectionResult:
        """
        Hauptfunktion zur Lift-Erkennung basierend auf Sensordaten.
        
        Args:
            imu_data: IMU-Sensordaten (acceleration, gyro, euler)
            gps_data: GPS-Daten (lat, lon, alt, accuracy)
            motor_data: Optional - Motordaten für Kontext
            
        Returns:
            LiftDetectionResult mit Erkennungsergebnis
        """
        current_time = time.time()
        
        # Datenhistorie aktualisieren
        self._update_history(imu_data, gps_data, current_time)
        
        # Verschiedene Erkennungsmethoden anwenden
        imu_result = self._detect_lift_imu(imu_data, current_time)
        gps_result = self._detect_lift_gps(gps_data, current_time)
        motion_result = self._detect_lift_motion_analysis(imu_data, motor_data)
        
        # Ergebnisse kombinieren
        combined_result = self._combine_results(imu_result, gps_result, motion_result)
        
        # Zeitbasierte Bestätigung
        final_result = self._apply_temporal_filtering(combined_result, current_time)
        
        return final_result
    
    def _update_history(self, imu_data: Dict, gps_data: Dict, timestamp: float):
        """Aktualisiert die Datenhistorie für Trend-Analyse"""
        if imu_data and 'acceleration' in imu_data:
            accel = imu_data['acceleration']
            if accel and len(accel) >= 3:
                # Z-Achsen-Beschleunigung (vertikal)
                self.accel_history.append({
                    'timestamp': timestamp,
                    'z_accel': accel[2],
                    'magnitude': math.sqrt(sum(a**2 for a in accel))
                })
        
        if imu_data and 'gyro' in imu_data:
            gyro = imu_data['gyro']
            if gyro and len(gyro) >= 3:
                self.gyro_history.append({
                    'timestamp': timestamp,
                    'angular_velocity': math.sqrt(sum(g**2 for g in gyro))
                })
        
        if gps_data and 'alt' in gps_data and gps_data['alt'] is not None:
            self.altitude_history.append({
                'timestamp': timestamp,
                'altitude': float(gps_data['alt']),
                'accuracy': gps_data.get('hdop', 999.0)
            })
    
    def _detect_lift_imu(self, imu_data: Dict, timestamp: float) -> Dict:
        """
        IMU-basierte Lift-Erkennung durch Analyse der Beschleunigungsdaten.
        
        Erkennt:
        1. Plötzliche Änderung der Z-Achsen-Beschleunigung
        2. Freier Fall (reduzierte Gravitation)
        3. Ungewöhnliche Rotationsbewegungen
        """
        if not self.config['imu_enabled'] or not imu_data:
            return {'confidence': 0.0, 'method': 'imu_disabled'}
        
        confidence = 0.0
        details = {}
        
        # Z-Achsen-Beschleunigung analysieren
        if 'acceleration' in imu_data and imu_data['acceleration']:
            accel = imu_data['acceleration']
            if len(accel) >= 3:
                z_accel = accel[2]
                accel_magnitude = math.sqrt(sum(a**2 for a in accel))
                
                # Abweichung von der Gravitation
                gravity_deviation = abs(accel_magnitude - self.gravity_baseline)
                
                # Freier Fall erkennen (reduzierte Gravitation)
                if accel_magnitude < (self.gravity_baseline - self.config['free_fall_threshold']):
                    confidence += 0.8
                    details['free_fall_detected'] = True
                    details['accel_magnitude'] = accel_magnitude
                
                # Plötzliche Beschleunigung (Anheben)
                elif gravity_deviation > self.config['sudden_movement_threshold']:
                    confidence += 0.6
                    details['sudden_acceleration'] = True
                    details['gravity_deviation'] = gravity_deviation
                
                # Trend-Analyse der Z-Beschleunigung
                if len(self.accel_history) >= 5:
                    z_trend = self._analyze_acceleration_trend()
                    if z_trend['significant_change']:
                        confidence += 0.4
                        details['z_trend'] = z_trend
        
        # Gyro-Daten analysieren (ungewöhnliche Rotation)
        if 'gyro' in imu_data and imu_data['gyro']:
            gyro = imu_data['gyro']
            if len(gyro) >= 3:
                angular_velocity = math.sqrt(sum(g**2 for g in gyro))
                
                if angular_velocity > self.config['gyro_threshold']:
                    confidence += 0.3
                    details['high_rotation'] = True
                    details['angular_velocity'] = angular_velocity
        
        return {
            'confidence': min(confidence, 1.0),
            'method': 'imu_analysis',
            'details': details
        }
    
    def _detect_lift_gps(self, gps_data: Dict, timestamp: float) -> Dict:
        """
        GPS-basierte Lift-Erkennung durch Höhenänderung.
        
        Erkennt:
        1. Plötzliche Höhenänderung
        2. Schnelle vertikale Bewegung
        3. Höhenänderung ohne horizontale Bewegung
        """
        if not self.config['gps_enabled'] or not gps_data:
            return {'confidence': 0.0, 'method': 'gps_disabled'}
        
        confidence = 0.0
        details = {}
        
        # GPS-Genauigkeit prüfen
        accuracy = gps_data.get('hdop', 999.0)
        if accuracy > self.config['gps_accuracy_required']:
            return {'confidence': 0.0, 'method': 'gps_poor_accuracy', 'accuracy': accuracy}
        
        # Höhendaten analysieren
        if 'alt' in gps_data and gps_data['alt'] is not None:
            current_altitude = float(gps_data['alt'])
            
            # Baseline etablieren
            if not self.baseline_established and len(self.altitude_history) >= 5:
                self.altitude_baseline = self._calculate_altitude_baseline()
                self.baseline_established = True
            
            if self.altitude_baseline is not None:
                altitude_change = current_altitude - self.altitude_baseline
                
                # Signifikante Höhenänderung
                if abs(altitude_change) > self.config['altitude_threshold']:
                    confidence += 0.6
                    details['altitude_change'] = altitude_change
                    details['baseline_altitude'] = self.altitude_baseline
                
                # Geschwindigkeit der Höhenänderung
                if len(self.altitude_history) >= 2:
                    altitude_rate = self._calculate_altitude_rate()
                    if abs(altitude_rate) > self.config['altitude_rate_threshold']:
                        confidence += 0.4
                        details['altitude_rate'] = altitude_rate
        
        return {
            'confidence': min(confidence, 1.0),
            'method': 'gps_analysis',
            'details': details
        }
    
    def _detect_lift_motion_analysis(self, imu_data: Dict, motor_data: Dict) -> Dict:
        """
        Bewegungsanalyse zur Lift-Erkennung.
        
        Erkennt Lift durch Kombination von:
        1. Stillstand der Motoren
        2. Trotzdem vorhandene Beschleunigung
        3. Inkonsistenz zwischen Motor-Sollwerten und IMU-Daten
        """
        confidence = 0.0
        details = {}
        
        # Prüfen ob Motoren stillstehen
        motors_stopped = False
        if motor_data:
            left_speed = motor_data.get('left_speed', 0)
            right_speed = motor_data.get('right_speed', 0)
            motors_stopped = abs(left_speed) < 0.1 and abs(right_speed) < 0.1
        
        # IMU zeigt Bewegung obwohl Motoren stillstehen
        if motors_stopped and imu_data:
            if 'acceleration' in imu_data and imu_data['acceleration']:
                accel = imu_data['acceleration']
                if len(accel) >= 3:
                    # Horizontale Beschleunigung bei stillstehenden Motoren
                    horizontal_accel = math.sqrt(accel[0]**2 + accel[1]**2)
                    if horizontal_accel > 1.0:  # Signifikante horizontale Bewegung
                        confidence += 0.5
                        details['motion_without_motors'] = True
                        details['horizontal_acceleration'] = horizontal_accel
        
        return {
            'confidence': min(confidence, 1.0),
            'method': 'motion_analysis',
            'details': details
        }
    
    def _analyze_acceleration_trend(self) -> Dict:
        """Analysiert den Trend der Z-Achsen-Beschleunigung"""
        if len(self.accel_history) < 5:
            return {'significant_change': False}
        
        recent_values = [entry['z_accel'] for entry in list(self.accel_history)[-5:]]
        
        # Einfache Trend-Erkennung
        first_half = sum(recent_values[:2]) / 2
        second_half = sum(recent_values[-2:]) / 2
        
        change = abs(second_half - first_half)
        significant = change > self.config['accel_threshold']
        
        return {
            'significant_change': significant,
            'change_magnitude': change,
            'trend_direction': 'up' if second_half > first_half else 'down'
        }
    
    def _calculate_altitude_baseline(self) -> float:
        """Berechnet die Baseline-Höhe aus der Historie"""
        if len(self.altitude_history) < 3:
            return None
        
        altitudes = [entry['altitude'] for entry in self.altitude_history]
        return sum(altitudes) / len(altitudes)
    
    def _calculate_altitude_rate(self) -> float:
        """Berechnet die Geschwindigkeit der Höhenänderung"""
        if len(self.altitude_history) < 2:
            return 0.0
        
        recent = list(self.altitude_history)[-2:]
        dt = recent[1]['timestamp'] - recent[0]['timestamp']
        dh = recent[1]['altitude'] - recent[0]['altitude']
        
        return dh / dt if dt > 0 else 0.0
    
    def _combine_results(self, imu_result: Dict, gps_result: Dict, motion_result: Dict) -> Dict:
        """Kombiniert die Ergebnisse verschiedener Erkennungsmethoden"""
        # Gewichtete Kombination der Konfidenzwerte
        weights = {
            'imu': 0.5,
            'gps': 0.3,
            'motion': 0.2
        }
        
        total_confidence = (
            imu_result['confidence'] * weights['imu'] +
            gps_result['confidence'] * weights['gps'] +
            motion_result['confidence'] * weights['motion']
        )
        
        # Bestimmung der primären Erkennungsmethode
        primary_method = max(
            [imu_result, gps_result, motion_result],
            key=lambda x: x['confidence']
        )['method']
        
        return {
            'confidence': total_confidence,
            'primary_method': primary_method,
            'imu_result': imu_result,
            'gps_result': gps_result,
            'motion_result': motion_result
        }
    
    def _apply_temporal_filtering(self, result: Dict, timestamp: float) -> LiftDetectionResult:
        """Wendet zeitbasierte Filterung an, um Fehlalarme zu reduzieren"""
        confidence = result['confidence']
        is_lifted = confidence >= self.config['confidence_threshold']
        
        # Bestätigung über Zeit
        if is_lifted:
            if self.lift_start_time is None:
                self.lift_start_time = timestamp
            
            # Mindestzeit für Bestätigung
            time_since_detection = timestamp - self.lift_start_time
            if time_since_detection < self.config['confirmation_time']:
                is_lifted = False  # Noch nicht bestätigt
        else:
            # Reset nach Absetzen
            if self.lift_start_time and (timestamp - self.lift_start_time) > self.config['reset_time']:
                self.lift_start_time = None
        
        return LiftDetectionResult(
            is_lifted=is_lifted,
            confidence=confidence,
            detection_method=result['primary_method'],
            details=result
        )
    
    def calibrate(self, imu_data: Dict, gps_data: Dict, duration: float = 10.0):
        """
        Kalibriert den Detektor basierend auf aktuellen Bedingungen.
        
        Args:
            imu_data: Aktuelle IMU-Daten
            gps_data: Aktuelle GPS-Daten
            duration: Kalibrierungsdauer in Sekunden
        """
        print(f"Starte Kalibrierung für {duration} Sekunden...")
        
        start_time = time.time()
        accel_samples = []
        altitude_samples = []
        
        while time.time() - start_time < duration:
            # IMU-Kalibrierung
            if imu_data and 'acceleration' in imu_data:
                accel = imu_data['acceleration']
                if accel and len(accel) >= 3:
                    magnitude = math.sqrt(sum(a**2 for a in accel))
                    accel_samples.append(magnitude)
            
            # GPS-Kalibrierung
            if gps_data and 'alt' in gps_data and gps_data['alt'] is not None:
                altitude_samples.append(float(gps_data['alt']))
            
            time.sleep(0.1)
        
        # Baseline-Werte berechnen
        if accel_samples:
            self.gravity_baseline = sum(accel_samples) / len(accel_samples)
            print(f"Gravitations-Baseline: {self.gravity_baseline:.2f} m/s²")
        
        if altitude_samples:
            self.altitude_baseline = sum(altitude_samples) / len(altitude_samples)
            print(f"Höhen-Baseline: {self.altitude_baseline:.2f} m")
        
        self.baseline_established = True
        print("Kalibrierung abgeschlossen.")


def test_lift_detection():
    """Test-Funktion für die alternative Lift-Erkennung"""
    print("=== Test: Alternative Lift-Erkennung ===")
    
    # Mock-Daten für Tests
    detector = AlternativeLiftDetector()
    
    # Normale Bedingungen (auf dem Boden)
    normal_imu = {
        'acceleration': [0.1, -0.2, 9.8],  # Normale Gravitation
        'gyro': [0.5, -0.3, 0.1],  # Minimale Rotation
        'euler': [45.0, 2.0, 1.0]  # Normale Orientierung
    }
    
    normal_gps = {
        'lat': 52.5200,
        'lon': 13.4050,
        'alt': 50.0,  # 50m Höhe
        'hdop': 1.0  # Gute Genauigkeit
    }
    
    # Test 1: Normale Bedingungen
    result = detector.update(normal_imu, normal_gps)
    print(f"Normal: Lift={result.is_lifted}, Konfidenz={result.confidence:.2f}, Methode={result.detection_method}")
    
    # Test 2: Anheben simulieren (reduzierte Gravitation)
    lifted_imu = {
        'acceleration': [0.5, 1.2, 3.0],  # Reduzierte Z-Beschleunigung
        'gyro': [15.0, 8.0, 12.0],  # Erhöhte Rotation
        'euler': [45.0, 15.0, 8.0]  # Veränderte Orientierung
    }
    
    lifted_gps = {
        'lat': 52.5200,
        'lon': 13.4050,
        'alt': 50.8,  # 80cm höher
        'hdop': 1.2
    }
    
    # Mehrere Updates für zeitbasierte Bestätigung
    for i in range(10):
        result = detector.update(lifted_imu, lifted_gps)
        print(f"Lift Test {i+1}: Lift={result.is_lifted}, Konfidenz={result.confidence:.2f}")
        time.sleep(0.1)
    
    # Test 3: Freier Fall simulieren
    freefall_imu = {
        'acceleration': [0.1, 0.2, 1.0],  # Stark reduzierte Gravitation
        'gyro': [25.0, 30.0, 20.0],  # Hohe Rotation
        'euler': [45.0, 25.0, 15.0]
    }
    
    result = detector.update(freefall_imu, normal_gps)
    print(f"Freier Fall: Lift={result.is_lifted}, Konfidenz={result.confidence:.2f}")
    print(f"Details: {result.details}")


if __name__ == "__main__":
    test_lift_detection()