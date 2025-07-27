import time
import math
from typing import Optional, Dict, Any
from events import Logger, EventCode

class CurrentMonitor:
    """
    Überwacht Stromspitzen der Motoren basierend auf Daten vom Pico zur Hinderniserkennung.
    Die INA226-Sensoren sind am Pico angeschlossen und senden Daten über UART.
    """
    
    def __init__(self):
        # Konfiguration für Stromspitzenerkennung
        self.spike_thresholds = {
            'mow_current': 8.0,           # Ampere
            'motor_left_current': 6.0,    # Ampere  
            'motor_right_current': 6.0    # Ampere
        }
        
        # Gleitender Durchschnitt für Stromwerte
        self.current_history = {
            'mow_current': [],
            'motor_left_current': [],
            'motor_right_current': []
        }
        self.history_size = 5
        
        # Cooldown nach Spitzenerkennung
        self.last_spike_time = 0
        self.cooldown_period = 2.0  # Sekunden
        
        # Status-Tracking
        self.last_detection_time = None
        self.spike_source = None
    

    
    def detect_current_spike(self, pico_data: dict) -> bool:
        """
        Erkennt Stromspitzen basierend auf Pico-Daten.
        """
        current_time = time.time()
        
        # Cooldown prüfen
        if current_time - self.last_spike_time < self.cooldown_period:
            return False
        
        # Prüfen ob motor_overload Flag vom Pico gesetzt ist
        if pico_data.get('motor_overload', 0) == 1:
            print("Motor-Überlastung vom Pico gemeldet")
            self.last_spike_time = current_time
            self.last_detection_time = current_time
            self.spike_source = "pico_overload"
            return True
        
        spike_detected = False
        
        # Manuelle Stromspitzenerkennung basierend auf Stromwerten
        for motor_key in ['mow_current', 'motor_left_current', 'motor_right_current']:
            current = pico_data.get(motor_key)
            if current is None:
                continue
                
            # Gleitenden Durchschnitt aktualisieren
            history = self.current_history[motor_key]
            history.append(current)
            if len(history) > self.history_size:
                history.pop(0)
            
            # Durchschnitt berechnen
            if len(history) >= 3:
                avg_current = sum(history) / len(history)
                threshold = self.spike_thresholds[motor_key]
                
                # Stromspitze erkannt?
                if current > threshold and current > avg_current * 1.5:
                    print(f"Stromspitze erkannt bei {motor_key}: {current:.2f}A (Schwelle: {threshold}A)")
                    spike_detected = True
                    self.last_spike_time = current_time
                    self.last_detection_time = current_time
                    self.spike_source = motor_key
                    break
        
        return spike_detected
    
    def get_status(self) -> dict:
        """
        Gibt den aktuellen Status des Current Monitors zurück.
        """
        return {
            'last_detection_time': self.last_detection_time,
            'spike_source': self.spike_source,
            'cooldown_remaining': max(0, self.cooldown_period - (time.time() - self.last_spike_time)),
            'thresholds': self.spike_thresholds.copy(),
            'current_averages': {k: sum(v)/len(v) if v else 0 for k, v in self.current_history.items()}
        }


class BumperDetector:
    """
    Verbesserte Erkennung von Kollisionen über Bumper-Sensoren.
    Unterstützt Debouncing und Erkennung von kurzen Kontakten.
    """
    def __init__(self):
        # Zustand der Bumper (links, rechts)
        self.bumper_state = [False, False]
        
        # Debouncing-Parameter
        self.debounce_time = 0.05  # 50ms
        self.last_change_time = [0.0, 0.0]
        
        # Kollisionserkennung
        self.collision_detected = False
        self.collision_time = 0.0
        self.collision_reset_time = 1.0  # Zeit bis Reset nach Kollision
    
    def detect_collision(self, bumper_value: int) -> bool:
        """
        Erkennt Kollisionen basierend auf Bumper-Wert.
        bumper_value: Bitmaske (Bit 0: links, Bit 1: rechts)
        Gibt True zurück, wenn eine Kollision erkannt wurde.
        """
        now = time.time()
        
        # Kollisionserkennung zurücksetzen, wenn Zeit abgelaufen
        if self.collision_detected and (now - self.collision_time > self.collision_reset_time):
            self.collision_detected = False
        
        # Bumper-Zustände extrahieren (1 = aktiviert/gedrückt)
        left_bumper = (bumper_value & 0x01) > 0
        right_bumper = (bumper_value & 0x02) > 0
        current_state = [left_bumper, right_bumper]
        
        # Für jeden Bumper prüfen
        collision = False
        for i, state in enumerate(current_state):
            # Wenn sich der Zustand geändert hat und Debounce-Zeit abgelaufen ist
            if state != self.bumper_state[i] and (now - self.last_change_time[i] > self.debounce_time):
                self.bumper_state[i] = state
                self.last_change_time[i] = now
                
                # Kollision erkannt, wenn Bumper aktiviert wurde
                if state:
                    collision = True
        
        # Kollision registrieren
        if collision and not self.collision_detected:
            self.collision_detected = True
            self.collision_time = now
            Logger.event(EventCode.OBSTACLE_DETECTED, "Bumper collision")
            return True
        
        return self.collision_detected


class IMUCollisionDetector:
    """
    Erkennt Kollisionen basierend auf plötzlichen Änderungen der IMU-Daten.
    """
    def __init__(self):
        # Schwellenwerte für Beschleunigung
        self.accel_threshold = 2.0  # m/s²
        
        # Gleitender Durchschnitt für Beschleunigungswerte
        self.accel_avg = [0.0, 0.0, 0.0]  # x, y, z
        self.alpha = 0.3  # Gewichtungsfaktor
        
        # Kollisionserkennung
        self.collision_detected = False
        self.collision_time = 0.0
        self.collision_reset_time = 1.0  # Zeit bis Reset nach Kollision
    
    def detect_collision(self, imu_data: Dict) -> bool:
        """
        Erkennt Kollisionen basierend auf IMU-Daten.
        imu_data: Dict mit 'acceleration' als Tuple (x, y, z)
        Gibt True zurück, wenn eine Kollision erkannt wurde.
        """
        now = time.time()
        
        # Kollisionserkennung zurücksetzen, wenn Zeit abgelaufen
        if self.collision_detected and (now - self.collision_time > self.collision_reset_time):
            self.collision_detected = False
        
        # Beschleunigungsdaten extrahieren
        accel = imu_data.get('acceleration', (0.0, 0.0, 0.0))
        if not accel or len(accel) != 3:
            return self.collision_detected
        
        # Plötzliche Änderung in der Beschleunigung erkennen
        collision = False
        for i in range(3):
            # Gleitenden Durchschnitt aktualisieren
            delta = abs(accel[i] - self.accel_avg[i])
            self.accel_avg[i] = self.alpha * accel[i] + (1 - self.alpha) * self.accel_avg[i]
            
            # Kollision erkannt, wenn Änderung über Schwellenwert
            if delta > self.accel_threshold:
                collision = True
        
        # Kollision registrieren
        if collision and not self.collision_detected:
            self.collision_detected = True
            self.collision_time = now
            Logger.event(EventCode.OBSTACLE_DETECTED, "IMU collision")
            return True
        
        return self.collision_detected


class ObstacleDetector:
    """
    Kombiniert verschiedene Methoden zur Hinderniserkennung.
    """
    def __init__(self):
        self.current_monitor = CurrentMonitor()
        self.bumper_detector = BumperDetector()
        self.imu_detector = IMUCollisionDetector()
        
        # Gesamtzustand
        self.obstacle_detected = False
        self.detection_time = 0.0
        self.reset_time = 2.0  # Zeit bis Reset nach Hinderniserkennung
    
    def update(self, pico_data: Dict, imu_data: Dict) -> bool:
        """
        Aktualisiert alle Detektoren und gibt True zurück, wenn ein Hindernis erkannt wurde.
        """
        now = time.time()
        
        # Hinderniserkennung zurücksetzen, wenn Zeit abgelaufen
        if self.obstacle_detected and (now - self.detection_time > self.reset_time):
            self.obstacle_detected = False
        
        # Alle Detektoren prüfen
        bumper_collision = self.bumper_detector.detect_collision(pico_data.get('bumper', 0))
        imu_collision = self.imu_detector.detect_collision(imu_data)
        
        # Stromspitzen erkennen (nur wenn Daten vom Pico vorhanden)
        current_spike = False
        if pico_data:
            current_spike = self.current_monitor.detect_current_spike(pico_data)
        
        # Hindernis erkannt, wenn einer der Detektoren anschlägt
        if (bumper_collision or imu_collision or current_spike) and not self.obstacle_detected:
            self.obstacle_detected = True
            self.detection_time = now
            Logger.event(EventCode.OBSTACLE_DETECTED, 
                         f"Bumper: {bumper_collision}, IMU: {imu_collision}, Current: {current_spike}")
            return True
        
        return self.obstacle_detected
    
    def get_status(self) -> Dict:
        """
        Gibt den aktuellen Status aller Detektoren mit detaillierten Informationen zurück.
        """
        return {
            "detected": self.obstacle_detected,
            "last_detection_time": self.detection_time,
            "reset_time": self.reset_time,
            "bumper": {
                "collision_detected": self.bumper_detector.collision_detected,
                "collision_time": self.bumper_detector.collision_time,
                "state": self.bumper_detector.bumper_state
            },
            "imu": {
                "collision_detected": self.imu_detector.collision_detected,
                "collision_time": self.imu_detector.collision_time,
                "threshold": self.imu_detector.accel_threshold
            },
            "current": self.current_monitor.get_status()
        }