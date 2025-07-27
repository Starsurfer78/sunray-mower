import time
import math
from typing import Dict, Optional, Tuple
from safety.gps_safety_manager import GPSSafetyManager

class KalmanFilter:
    """
    Einfacher Kalman-Filter für die Sensorfusion von IMU und GPS.
    """
    def __init__(self, process_variance=0.01, measurement_variance=0.1):
        self.process_variance = process_variance
        self.measurement_variance = measurement_variance
        self.estimate = 0.0
        self.estimate_error = 1.0
        self.initialized = False
    
    def update(self, measurement):
        # Initialisierung bei erstem Messwert
        if not self.initialized:
            self.estimate = measurement
            self.initialized = True
            return self.estimate
        
        # Vorhersage
        prediction_error = self.estimate_error + self.process_variance
        
        # Update
        kalman_gain = prediction_error / (prediction_error + self.measurement_variance)
        self.estimate = self.estimate + kalman_gain * (measurement - self.estimate)
        self.estimate_error = (1 - kalman_gain) * prediction_error
        
        return self.estimate

class StateEstimator:
    """
    Schätzlogik für Roboterzustand.
    Portierung von StateEstimator.cpp/h mit Erweiterungen für BNO085.
    Attribute:
      state_x, state_y, state_delta, state_heading, state_roll, state_pitch,
      state_delta_gps, state_delta_imu, state_ground_speed, lateral_error
    Methoden:
      start_imu(force: bool) -> bool
      read_imu() -> None
      compute_robot_state(imu_data, gps_data, pico_data) -> Dict
      reset_imu_timeout() -> None
      should_mow(gps_data, imu_data) -> bool
    """
    def __init__(self, config: Dict = None):
        # Zustand
        self.state_x = 0.0
        self.state_y = 0.0
        self.state_delta = 0.0
        self.state_heading = 0.0
        self.state_roll = 0.0
        self.state_pitch = 0.0
        self.state_delta_gps = 0.0
        self.state_delta_imu = 0.0
        self.state_ground_speed = 0.0
        self.lateral_error = 0.0

        # interne Variablen
        self.imu_is_calibrating = False
        self.imu_data_timeout = 0.0
        self.last_imu_yaw = 0.0
        self._imu_started = False
        
        # Kalman-Filter für Sensorfusion
        self.heading_filter = KalmanFilter(process_variance=0.01, measurement_variance=0.1)
        self.roll_filter = KalmanFilter(process_variance=0.01, measurement_variance=0.1)
        self.pitch_filter = KalmanFilter(process_variance=0.01, measurement_variance=0.1)
        
        # Sicherheitsparameter
        self.max_tilt_angle = 35.0  # Maximaler Neigungswinkel in Grad
        self.tilt_warning_active = False
        self.tilt_warning_start_time = 0.0
        self.tilt_warning_duration = 1.0  # Sekunden, bevor Abschaltung erfolgt
        
        # GPS-Sicherheitsmanager
        self.gps_safety_manager = GPSSafetyManager(config or {})

    def start_imu(self, force: bool = False) -> bool:
        """
        Initialisiert IMU-Datenstrom.
        force: bei True immer neu starten.
        """
        self._imu_started = True
        self.imu_is_calibrating = True
        self.imu_data_timeout = time.time() + 1.0
        return self._imu_started

    def read_imu(self, imu_data: Dict) -> None:
        """
        Verarbeitet IMU-Daten und aktualisiert interne Zustandsvariablen.
        """
        if not imu_data:
            return
            
        # Euler-Winkel aus IMU-Daten extrahieren
        euler = imu_data.get('euler', (0.0, 0.0, 0.0))
        yaw, pitch, roll = euler
        
        # Kalman-Filter anwenden für stabilere Werte
        filtered_yaw = self.heading_filter.update(yaw)
        filtered_pitch = self.pitch_filter.update(pitch)
        filtered_roll = self.roll_filter.update(roll)
        
        # Zustandsupdate
        self.state_heading = filtered_yaw
        self.state_pitch = filtered_pitch
        self.state_roll = filtered_roll
        
        # Berechnung der Änderung im Heading seit letztem Update
        heading_diff = self._normalize_angle(filtered_yaw - self.last_imu_yaw)
        self.state_delta_imu = heading_diff
        self.last_imu_yaw = filtered_yaw
        
        # Neigungswarnung prüfen
        self._check_tilt_warning(filtered_pitch, filtered_roll)
        
        # Timeout zurücksetzen
        self.reset_imu_timeout()

    def _normalize_angle(self, angle: float) -> float:
        """
        Normalisiert einen Winkel auf den Bereich [-180, 180].
        """
        while angle > 180.0:
            angle -= 360.0
        while angle < -180.0:
            angle += 360.0
        return angle

    def _check_tilt_warning(self, pitch: float, roll: float) -> None:
        """
        Prüft, ob die Neigung des Roboters zu stark ist und setzt Warnflag.
        """
        is_tilted = abs(pitch) > self.max_tilt_angle or abs(roll) > self.max_tilt_angle
        
        # Wenn Neigung zu stark ist und Warnung noch nicht aktiv
        if is_tilted and not self.tilt_warning_active:
            self.tilt_warning_active = True
            self.tilt_warning_start_time = time.time()
        # Wenn Neigung wieder im normalen Bereich
        elif not is_tilted and self.tilt_warning_active:
            self.tilt_warning_active = False

    def compute_robot_state(self, imu_data: Dict, gps_data: Dict, pico_data: Dict) -> Dict:
        """
        Berechnet neuen Roboterzustand aus GPS, IMU und Odometrie und gibt Status-Dict zurück.
        Implementiert Sensorfusion zwischen IMU und GPS sowie GPS-Sicherheitslogik.
        """
        # IMU-Daten verarbeiten
        self.read_imu(imu_data)
        
        # Basis-Koordinaten aus GPS
        x = gps_data.get("lat")
        y = gps_data.get("lon")
        gps_heading = gps_data.get("course", None)
        
        # Sensorfusion für Heading (IMU + GPS)
        if gps_heading is not None and gps_data.get("speed", 0) > 0.5:  # Nur bei ausreichender Geschwindigkeit
            # Gewichtung: 70% IMU, 30% GPS bei gutem GPS-Fix
            if gps_data.get("mode", 0) >= 4:  # RTK-Fix
                self.state_heading = 0.7 * self.state_heading + 0.3 * gps_heading
            else:  # Normaler Fix
                self.state_heading = 0.9 * self.state_heading + 0.1 * gps_heading
        
        # Geschwindigkeit aus GPS
        self.state_ground_speed = gps_data.get("speed", 0.0)
        
        # State-Update für Position
        if x is not None and y is not None:
            self.state_x = x
            self.state_y = y
        
        # GPS-Sicherheitsbewertung
        current_position = (self.state_x, self.state_y) if x is not None and y is not None else None
        gps_safety_result = self.gps_safety_manager.evaluate_gps_safety(
            gps_data, current_position
        )
        
        # Operation basierend auf GPS-Sicherheit und anderen Bedingungen
        can_mow_basic = self.should_mow(gps_data, imu_data)
        can_mow_gps = gps_safety_result.get('can_mow', False)
        op_type = "mow" if (can_mow_basic and can_mow_gps) else "idle"
        
        # Rückgabe des erweiterten Zustands
        return {
            "x": self.state_x,
            "y": self.state_y,
            "heading": self.state_heading,
            "roll": self.state_roll,
            "pitch": self.state_pitch,
            "speed": self.state_ground_speed,
            "tilt_warning": self.tilt_warning_active,
            "op_type": op_type,
            # GPS-Sicherheitsinformationen
            "gps_safety_level": gps_safety_result.get('safety_level'),
            "gps_can_mow": can_mow_gps,
            "gps_speed_factor": gps_safety_result.get('speed_factor', 1.0),
            "gps_recommended_action": gps_safety_result.get('recommended_action'),
            "gps_action_params": gps_safety_result.get('action_params', {}),
            "rtk_wait_remaining": gps_safety_result.get('rtk_wait_remaining', 0.0)
        }

    def reset_imu_timeout(self) -> None:
        """
        Setzt den IMU-Timeout zurück, wenn Daten ankommen.
        """
        self.imu_data_timeout = time.time() + 1.0

    def should_mow(self, gps_data: Dict, imu_data: Dict) -> bool:
        """
        Entscheidet, ob gemäht werden soll basierend auf:
        - GPS-Fix vorhanden
        - Keine zu starke Neigung
        - Keine Tilt-Warnung aktiv länger als erlaubte Dauer
        """
        # GPS-Fix prüfen
        gps_ok = gps_data.get("mode", 0) >= 2
        
        # Neigungswarnung prüfen
        tilt_ok = True
        if self.tilt_warning_active:
            # Wenn Warnung länger als erlaubte Dauer aktiv, nicht mähen
            if time.time() - self.tilt_warning_start_time > self.tilt_warning_duration:
                tilt_ok = False
        
        # Nur mähen, wenn alle Bedingungen erfüllt sind
        return gps_ok and tilt_ok
