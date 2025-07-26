import time
import json
import math
import numpy as np
from typing import Dict, List, Tuple, Optional, Any
from abc import ABC, abstractmethod
from op import Operation
from events import Logger, EventCode

class SensorFusion:
    """
    Erweiterte Sensorfusion für intelligente Ausweichmanöver.
    Kombiniert GPS, IMU, Odometrie und Stromspitzen für kontextbewusste Entscheidungen.
    """
    
    def __init__(self):
        # Kalman-Filter für Positionsschätzung
        self.position_filter = self._init_kalman_filter()
        
        # Gewichtungen für Sensorfusion
        self.sensor_weights = {
            'gps': 0.4,
            'imu': 0.3,
            'odometry': 0.2,
            'current': 0.1
        }
        
        # Vertrauenswerte der Sensoren
        self.sensor_confidence = {
            'gps': 1.0,
            'imu': 1.0,
            'odometry': 1.0,
            'current': 1.0
        }
        
        # Bewegungshistorie für Trendanalyse
        self.movement_history = []
        self.max_history_length = 50
        
    def _init_kalman_filter(self):
        """Initialisiert erweiterten Kalman-Filter für Positionsschätzung."""
        return {
            'state': np.array([0.0, 0.0, 0.0, 0.0]),  # [x, y, vx, vy]
            'covariance': np.eye(4) * 0.1,
            'process_noise': np.eye(4) * 0.01,
            'measurement_noise': np.eye(2) * 0.1
        }
    
    def fuse_sensor_data(self, gps_data: Dict, imu_data: Dict, 
                        odometry_data: Dict, current_data: Dict) -> Dict:
        """
        Führt erweiterte Sensorfusion durch und gibt fusionierten Zustand zurück.
        """
        # Sensor-Vertrauenswerte aktualisieren
        self._update_sensor_confidence(gps_data, imu_data, odometry_data, current_data)
        
        # Gewichtete Fusion der Positionsdaten
        fused_position = self._fuse_position_data(gps_data, odometry_data)
        
        # Orientierungsfusion (IMU + GPS-Kurs)
        fused_heading = self._fuse_heading_data(imu_data, gps_data)
        
        # Bewegungsanalyse
        movement_state = self._analyze_movement_pattern(imu_data, current_data)
        
        # Hinderniskontext aus allen Sensoren
        obstacle_context = self._analyze_obstacle_context(
            gps_data, imu_data, odometry_data, current_data
        )
        
        fused_state = {
            'position': fused_position,
            'heading': fused_heading,
            'movement_state': movement_state,
            'obstacle_context': obstacle_context,
            'sensor_confidence': self.sensor_confidence.copy(),
            'timestamp': time.time()
        }
        
        # Historie aktualisieren
        self._update_movement_history(fused_state)
        
        return fused_state
    
    def _update_sensor_confidence(self, gps_data: Dict, imu_data: Dict, 
                                 odometry_data: Dict, current_data: Dict):
        """Aktualisiert Vertrauenswerte der Sensoren basierend auf Datenqualität."""
        # GPS-Vertrauen basierend auf Fix-Qualität und HDOP
        gps_mode = gps_data.get('mode', 0)
        hdop = gps_data.get('hdop', 99.0)
        if gps_mode >= 4:  # RTK-Fix
            self.sensor_confidence['gps'] = min(1.0, 2.0 / max(hdop, 0.5))
        elif gps_mode >= 2:  # 3D-Fix
            self.sensor_confidence['gps'] = min(0.8, 1.5 / max(hdop, 1.0))
        else:
            self.sensor_confidence['gps'] = 0.1
        
        # IMU-Vertrauen basierend auf Kalibrierungsstatus und Stabilität
        if imu_data.get('calibrated', False):
            accel_magnitude = np.linalg.norm(imu_data.get('acceleration', [0, 0, 9.81]))
            # Vertrauen sinkt bei ungewöhnlichen Beschleunigungen
            self.sensor_confidence['imu'] = max(0.3, 1.0 - abs(accel_magnitude - 9.81) / 10.0)
        else:
            self.sensor_confidence['imu'] = 0.5
        
        # Odometrie-Vertrauen basierend auf Motorzustand
        motor_health = 1.0 - current_data.get('overload_count', 0) / 10.0
        self.sensor_confidence['odometry'] = max(0.2, motor_health)
        
        # Strom-Sensor-Vertrauen (meist zuverlässig)
        self.sensor_confidence['current'] = 0.9
    
    def _fuse_position_data(self, gps_data: Dict, odometry_data: Dict) -> Dict:
        """Fusioniert GPS- und Odometrie-Positionsdaten."""
        gps_weight = self.sensor_confidence['gps'] * self.sensor_weights['gps']
        odom_weight = self.sensor_confidence['odometry'] * self.sensor_weights['odometry']
        
        total_weight = gps_weight + odom_weight
        if total_weight == 0:
            return {'x': 0.0, 'y': 0.0, 'confidence': 0.0}
        
        gps_x = gps_data.get('lat', 0.0)
        gps_y = gps_data.get('lon', 0.0)
        odom_x = odometry_data.get('x', gps_x)
        odom_y = odometry_data.get('y', gps_y)
        
        fused_x = (gps_x * gps_weight + odom_x * odom_weight) / total_weight
        fused_y = (gps_y * gps_weight + odom_y * odom_weight) / total_weight
        
        return {
            'x': fused_x,
            'y': fused_y,
            'confidence': total_weight / (self.sensor_weights['gps'] + self.sensor_weights['odometry'])
        }
    
    def _fuse_heading_data(self, imu_data: Dict, gps_data: Dict) -> Dict:
        """Fusioniert IMU- und GPS-Heading-Daten."""
        imu_weight = self.sensor_confidence['imu'] * self.sensor_weights['imu']
        gps_weight = self.sensor_confidence['gps'] * self.sensor_weights['gps']
        
        # GPS-Kurs nur bei ausreichender Geschwindigkeit verwenden
        gps_speed = gps_data.get('speed', 0.0)
        if gps_speed < 0.3:  # Unter 0.3 m/s ist GPS-Kurs unzuverlässig
            gps_weight = 0.0
        
        total_weight = imu_weight + gps_weight
        if total_weight == 0:
            return {'heading': 0.0, 'confidence': 0.0}
        
        imu_heading = imu_data.get('heading', 0.0)
        gps_heading = gps_data.get('course', imu_heading)
        
        # Winkel-Fusion (berücksichtigt 360°-Übergang)
        fused_heading = self._fuse_angles(imu_heading, gps_heading, imu_weight, gps_weight)
        
        return {
            'heading': fused_heading,
            'confidence': total_weight / (self.sensor_weights['imu'] + self.sensor_weights['gps'])
        }
    
    def _fuse_angles(self, angle1: float, angle2: float, weight1: float, weight2: float) -> float:
        """Fusioniert zwei Winkel unter Berücksichtigung der 360°-Periodizität."""
        # Konvertiere zu Einheitsvektoren
        x1, y1 = math.cos(math.radians(angle1)), math.sin(math.radians(angle1))
        x2, y2 = math.cos(math.radians(angle2)), math.sin(math.radians(angle2))
        
        # Gewichtete Mittelung der Vektoren
        total_weight = weight1 + weight2
        if total_weight == 0:
            return angle1
        
        x_fused = (x1 * weight1 + x2 * weight2) / total_weight
        y_fused = (y1 * weight1 + y2 * weight2) / total_weight
        
        # Zurück zu Winkel konvertieren
        return math.degrees(math.atan2(y_fused, x_fused))
    
    def _analyze_movement_pattern(self, imu_data: Dict, current_data: Dict) -> Dict:
        """Analysiert Bewegungsmuster für Anomalieerkennung."""
        acceleration = imu_data.get('acceleration', (0, 0, 0))
        gyro = imu_data.get('gyro', (0, 0, 0))
        
        # Bewegungsanomalien erkennen
        accel_magnitude = np.linalg.norm(acceleration)
        gyro_magnitude = np.linalg.norm(gyro)
        
        # Klassifizierung der Bewegung
        movement_type = 'normal'
        if accel_magnitude > 15.0:  # Starke Beschleunigung
            movement_type = 'collision'
        elif gyro_magnitude > 2.0:  # Starke Rotation
            movement_type = 'spinning'
        elif current_data.get('motor_overload', False):
            movement_type = 'stuck'
        
        return {
            'type': movement_type,
            'acceleration_magnitude': accel_magnitude,
            'gyro_magnitude': gyro_magnitude,
            'stability': 1.0 / (1.0 + accel_magnitude + gyro_magnitude)
        }
    
    def _analyze_obstacle_context(self, gps_data: Dict, imu_data: Dict, 
                                 odometry_data: Dict, current_data: Dict) -> Dict:
        """Analysiert Hinderniskontext aus allen verfügbaren Sensordaten."""
        context = {
            'obstacle_detected': False,
            'obstacle_direction': None,
            'obstacle_type': 'unknown',
            'severity': 0.0
        }
        
        # Stromspitzen-Analyse
        if current_data.get('motor_overload', False):
            context['obstacle_detected'] = True
            context['obstacle_type'] = 'current_spike'
            
            # Richtung aus Motorströmen ableiten
            left_current = current_data.get('motor_left_current', 0)
            right_current = current_data.get('motor_right_current', 0)
            
            if left_current > right_current * 1.5:
                context['obstacle_direction'] = 'left'
            elif right_current > left_current * 1.5:
                context['obstacle_direction'] = 'right'
            else:
                context['obstacle_direction'] = 'front'
            
            context['severity'] = min(1.0, max(left_current, right_current) / 1000.0)
        
        # IMU-Kollisionserkennung
        acceleration = imu_data.get('acceleration', (0, 0, 0))
        if np.linalg.norm(acceleration) > 12.0:
            context['obstacle_detected'] = True
            context['obstacle_type'] = 'physical_collision'
            
            # Richtung aus Beschleunigungsvektor
            ax, ay, az = acceleration
            angle = math.degrees(math.atan2(ay, ax))
            context['obstacle_direction'] = self._angle_to_direction(angle)
            context['severity'] = min(1.0, np.linalg.norm(acceleration) / 20.0)
        
        return context
    
    def _angle_to_direction(self, angle: float) -> str:
        """Konvertiert Winkel zu Richtungsbezeichnung."""
        angle = angle % 360
        if angle < 45 or angle >= 315:
            return 'front'
        elif angle < 135:
            return 'left'
        elif angle < 225:
            return 'back'
        else:
            return 'right'
    
    def _update_movement_history(self, state: Dict):
        """Aktualisiert Bewegungshistorie für Trendanalyse."""
        self.movement_history.append(state)
        if len(self.movement_history) > self.max_history_length:
            self.movement_history.pop(0)
    
    def get_movement_trend(self) -> Dict:
        """Analysiert Bewegungstrends aus der Historie."""
        if len(self.movement_history) < 5:
            return {'trend': 'insufficient_data'}
        
        recent_states = self.movement_history[-10:]
        
        # Positionstrend
        positions = [s['position'] for s in recent_states]
        x_trend = np.polyfit(range(len(positions)), [p['x'] for p in positions], 1)[0]
        y_trend = np.polyfit(range(len(positions)), [p['y'] for p in positions], 1)[0]
        
        # Bewegungsgeschwindigkeit
        speed = math.sqrt(x_trend**2 + y_trend**2)
        
        return {
            'trend': 'moving' if speed > 0.01 else 'stationary',
            'speed': speed,
            'direction_trend': math.degrees(math.atan2(y_trend, x_trend))
        }

class LearningSystem:
    """
    Self-Learning System für adaptive Ausweichstrategien.
    Lernt aus erfolgreichen und fehlgeschlagenen Manövern.
    """
    
    def __init__(self, learning_file: str = 'escape_learning_data.json'):
        self.learning_file = learning_file
        self.learning_data = self._load_learning_data()
        
        # Lernparameter
        self.learning_rate = 0.1
        self.success_threshold = 0.8
        self.min_samples_for_learning = 5
        
    def _load_learning_data(self) -> Dict:
        """Lädt gespeicherte Lerndaten."""
        try:
            with open(self.learning_file, 'r') as f:
                return json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            return {
                'escape_strategies': {},
                'context_patterns': {},
                'success_rates': {},
                'parameter_optimizations': {}
            }
    
    def _save_learning_data(self):
        """Speichert Lerndaten."""
        try:
            with open(self.learning_file, 'w') as f:
                json.dump(self.learning_data, f, indent=2)
        except Exception as e:
            Logger.event(EventCode.ERROR, f"Failed to save learning data: {e}")
    
    def record_escape_attempt(self, context: Dict, strategy: str, 
                            parameters: Dict, success: bool, duration: float):
        """Zeichnet einen Ausweichversuch für das Lernen auf."""
        # Kontext-Schlüssel generieren
        context_key = self._generate_context_key(context)
        
        # Datenstruktur initialisieren falls nötig
        if context_key not in self.learning_data['escape_strategies']:
            self.learning_data['escape_strategies'][context_key] = []
        
        # Versuch aufzeichnen
        attempt = {
            'strategy': strategy,
            'parameters': parameters,
            'success': success,
            'duration': duration,
            'timestamp': time.time()
        }
        
        self.learning_data['escape_strategies'][context_key].append(attempt)
        
        # Erfolgsraten aktualisieren
        self._update_success_rates(context_key, strategy, success)
        
        # Parameter optimieren
        if success:
            self._optimize_parameters(context_key, strategy, parameters, duration)
        
        # Daten speichern
        self._save_learning_data()
    
    def _generate_context_key(self, context: Dict) -> str:
        """Generiert einen Schlüssel für den Kontext."""
        obstacle_type = context.get('obstacle_context', {}).get('obstacle_type', 'unknown')
        obstacle_direction = context.get('obstacle_context', {}).get('obstacle_direction', 'unknown')
        terrain_type = self._classify_terrain(context)
        
        return f"{obstacle_type}_{obstacle_direction}_{terrain_type}"
    
    def _classify_terrain(self, context: Dict) -> str:
        """Klassifiziert Terrain basierend auf Kontext."""
        movement_state = context.get('movement_state', {})
        stability = movement_state.get('stability', 1.0)
        
        if stability < 0.3:
            return 'rough'
        elif stability < 0.7:
            return 'moderate'
        else:
            return 'smooth'
    
    def _update_success_rates(self, context_key: str, strategy: str, success: bool):
        """Aktualisiert Erfolgsraten für Strategie-Kontext-Kombinationen."""
        rate_key = f"{context_key}_{strategy}"
        
        if rate_key not in self.learning_data['success_rates']:
            self.learning_data['success_rates'][rate_key] = {'successes': 0, 'attempts': 0}
        
        self.learning_data['success_rates'][rate_key]['attempts'] += 1
        if success:
            self.learning_data['success_rates'][rate_key]['successes'] += 1
    
    def _optimize_parameters(self, context_key: str, strategy: str, 
                           parameters: Dict, duration: float):
        """Optimiert Parameter basierend auf erfolgreichen Versuchen."""
        param_key = f"{context_key}_{strategy}"
        
        if param_key not in self.learning_data['parameter_optimizations']:
            self.learning_data['parameter_optimizations'][param_key] = {
                'optimal_params': parameters.copy(),
                'best_duration': duration,
                'sample_count': 1
            }
        else:
            opt_data = self.learning_data['parameter_optimizations'][param_key]
            
            # Wenn diese Ausführung schneller war, Parameter aktualisieren
            if duration < opt_data['best_duration']:
                # Gewichtete Mittelung mit bisherigen optimalen Parametern
                for key, value in parameters.items():
                    if key in opt_data['optimal_params']:
                        old_value = opt_data['optimal_params'][key]
                        opt_data['optimal_params'][key] = (
                            old_value * (1 - self.learning_rate) + 
                            value * self.learning_rate
                        )
                
                opt_data['best_duration'] = duration
            
            opt_data['sample_count'] += 1
    
    def get_recommended_strategy(self, context: Dict) -> Tuple[str, Dict, float]:
        """Empfiehlt beste Strategie basierend auf gelernten Daten."""
        context_key = self._generate_context_key(context)
        
        # Alle verfügbaren Strategien für diesen Kontext
        available_strategies = ['smart_bumper_escape', 'escape_forward', 'adaptive_escape']
        
        best_strategy = 'escape_forward'  # Fallback
        best_params = self._get_default_parameters(best_strategy)
        best_confidence = 0.0
        
        for strategy in available_strategies:
            rate_key = f"{context_key}_{strategy}"
            param_key = f"{context_key}_{strategy}"
            
            # Erfolgsrate prüfen
            if rate_key in self.learning_data['success_rates']:
                rate_data = self.learning_data['success_rates'][rate_key]
                if rate_data['attempts'] >= self.min_samples_for_learning:
                    success_rate = rate_data['successes'] / rate_data['attempts']
                    
                    if success_rate > best_confidence:
                        best_strategy = strategy
                        best_confidence = success_rate
                        
                        # Optimierte Parameter verwenden falls verfügbar
                        if param_key in self.learning_data['parameter_optimizations']:
                            best_params = self.learning_data['parameter_optimizations'][param_key]['optimal_params']
                        else:
                            best_params = self._get_default_parameters(strategy)
        
        return best_strategy, best_params, best_confidence
    
    def _get_default_parameters(self, strategy: str) -> Dict:
        """Gibt Standard-Parameter für eine Strategie zurück."""
        defaults = {
            'smart_bumper_escape': {
                'reverse_duration': 1.0,
                'curve_duration': 3.0,
                'return_duration': 2.0,
                'linear_speed': 0.3,
                'angular_speed': 0.3
            },
            'escape_forward': {
                'pause_duration': 0.5,
                'forward_duration': 1.5,
                'rotate_duration': 2.0,
                'linear_speed': 0.3,
                'angular_speed': 0.5
            },
            'adaptive_escape': {
                'analysis_duration': 0.2,
                'maneuver_duration': 2.0,
                'recovery_duration': 1.0,
                'max_speed': 0.4,
                'aggressiveness': 0.5
            }
        }
        
        return defaults.get(strategy, defaults['escape_forward'])
    
    def get_learning_statistics(self) -> Dict:
        """Gibt Lernstatistiken zurück."""
        total_attempts = sum(
            data['attempts'] for data in self.learning_data['success_rates'].values()
        )
        
        total_successes = sum(
            data['successes'] for data in self.learning_data['success_rates'].values()
        )
        
        overall_success_rate = total_successes / total_attempts if total_attempts > 0 else 0.0
        
        return {
            'total_attempts': total_attempts,
            'total_successes': total_successes,
            'overall_success_rate': overall_success_rate,
            'learned_contexts': len(self.learning_data['escape_strategies']),
            'optimized_strategies': len(self.learning_data['parameter_optimizations'])
        }

class AdaptiveEscapeOp(Operation):
    """
    Adaptive Ausweichoperation mit Sensorfusion und Self-Learning.
    Kombiniert alle verfügbaren Sensordaten für optimale Ausweichstrategien.
    """
    
    def __init__(self, name: str, motor=None):
        super().__init__(name)
        self.motor = motor
        self.sensor_fusion = SensorFusion()
        self.learning_system = LearningSystem()
        
        # Zustandsvariablen
        self.start_time = None
        self.current_strategy = None
        self.strategy_params = None
        self.phase = 'analyze'
        self.phase_start_time = None
        
        # Kontext für Lernen
        self.initial_context = None
        self.maneuver_start_time = None
        
    def on_start(self, params: Dict[str, Any]) -> None:
        """Startet adaptive Ausweichoperation."""
        self.start_time = time.time()
        self.phase = 'analyze'
        self.phase_start_time = self.start_time
        
        # Sensordaten aus Parametern extrahieren
        gps_data = params.get('gps_data', {})
        imu_data = params.get('imu_data', {})
        odometry_data = params.get('odometry_data', {})
        current_data = params.get('current_data', {})
        
        # Sensorfusion durchführen
        self.initial_context = self.sensor_fusion.fuse_sensor_data(
            gps_data, imu_data, odometry_data, current_data
        )
        
        # Beste Strategie basierend auf gelernten Daten ermitteln
        strategy, strategy_params, confidence = self.learning_system.get_recommended_strategy(
            self.initial_context
        )
        
        self.current_strategy = strategy
        self.strategy_params = strategy_params
        
        Logger.event(EventCode.OBSTACLE_DETECTED, 
                    f"Adaptive escape started: {strategy} (confidence: {confidence:.2f})")
        
        # Motoren stoppen für Analyse
        if self.motor:
            self.motor.stop_immediately(include_mower=False)
        
        print(f"AdaptiveEscape: Strategie {strategy} gewählt (Vertrauen: {confidence:.2f})")
    
    def run(self) -> None:
        """Führt adaptive Ausweichlogik aus."""
        current_time = time.time()
        elapsed_in_phase = current_time - self.phase_start_time
        
        if self.phase == 'analyze':
            # Kurze Analysephase
            analysis_duration = self.strategy_params.get('analysis_duration', 0.2)
            if elapsed_in_phase >= analysis_duration:
                self._start_maneuver()
        
        elif self.phase == 'maneuver':
            # Ausweichmanöver ausführen
            self._execute_maneuver(elapsed_in_phase)
        
        elif self.phase == 'recovery':
            # Erholungsphase
            recovery_duration = self.strategy_params.get('recovery_duration', 1.0)
            if elapsed_in_phase >= recovery_duration:
                self._complete_maneuver(success=True)
    
    def _start_maneuver(self):
        """Startet das eigentliche Ausweichmanöver."""
        self.phase = 'maneuver'
        self.phase_start_time = time.time()
        self.maneuver_start_time = self.phase_start_time
        
        print(f"AdaptiveEscape: Starte Manöver-Phase ({self.current_strategy})")
    
    def _execute_maneuver(self, elapsed_time: float):
        """Führt das spezifische Ausweichmanöver aus."""
        if self.current_strategy == 'smart_bumper_escape':
            self._execute_smart_bumper_maneuver(elapsed_time)
        elif self.current_strategy == 'escape_forward':
            self._execute_forward_escape_maneuver(elapsed_time)
        elif self.current_strategy == 'adaptive_escape':
            self._execute_adaptive_maneuver(elapsed_time)
        else:
            # Fallback
            self._execute_forward_escape_maneuver(elapsed_time)
    
    def _execute_smart_bumper_maneuver(self, elapsed_time: float):
        """Führt intelligentes Bumper-Ausweichmanöver aus."""
        reverse_duration = self.strategy_params.get('reverse_duration', 1.0)
        curve_duration = self.strategy_params.get('curve_duration', 3.0)
        
        if elapsed_time < reverse_duration:
            # Rückwärtsfahrt
            if self.motor:
                self.motor.set_linear_angular_speed(-0.2, 0.0)
        elif elapsed_time < reverse_duration + curve_duration:
            # Kurvenfahrt
            linear_speed = self.strategy_params.get('linear_speed', 0.3)
            angular_speed = self.strategy_params.get('angular_speed', 0.3)
            
            # Richtung basierend auf Hinderniskontext
            obstacle_direction = self.initial_context.get('obstacle_context', {}).get('obstacle_direction')
            if obstacle_direction == 'left':
                angular_speed = abs(angular_speed)  # Rechts drehen
            elif obstacle_direction == 'right':
                angular_speed = -abs(angular_speed)  # Links drehen
            
            if self.motor:
                self.motor.set_linear_angular_speed(linear_speed, angular_speed)
        else:
            # Manöver beendet
            self._start_recovery()
    
    def _execute_forward_escape_maneuver(self, elapsed_time: float):
        """Führt Vorwärts-Ausweichmanöver aus."""
        pause_duration = self.strategy_params.get('pause_duration', 0.5)
        forward_duration = self.strategy_params.get('forward_duration', 1.5)
        rotate_duration = self.strategy_params.get('rotate_duration', 2.0)
        
        if elapsed_time < pause_duration:
            # Pause
            pass
        elif elapsed_time < pause_duration + forward_duration:
            # Vorwärtsfahrt
            linear_speed = self.strategy_params.get('linear_speed', 0.3)
            if self.motor:
                self.motor.set_linear_angular_speed(linear_speed, 0.0)
        elif elapsed_time < pause_duration + forward_duration + rotate_duration:
            # Rotation
            angular_speed = self.strategy_params.get('angular_speed', 0.5)
            
            # Zufällige Richtung oder basierend auf Kontext
            if int(self.start_time * 1000) % 2 == 0:
                angular_speed = -angular_speed
            
            if self.motor:
                self.motor.set_linear_angular_speed(0.0, angular_speed)
        else:
            # Manöver beendet
            self._start_recovery()
    
    def _execute_adaptive_maneuver(self, elapsed_time: float):
        """Führt vollständig adaptives Manöver aus."""
        maneuver_duration = self.strategy_params.get('maneuver_duration', 2.0)
        max_speed = self.strategy_params.get('max_speed', 0.4)
        aggressiveness = self.strategy_params.get('aggressiveness', 0.5)
        
        # Dynamische Anpassung basierend auf aktueller Sensorfusion
        # (Hier würde eine komplexere Logik implementiert werden)
        
        progress = elapsed_time / maneuver_duration
        if progress < 0.3:
            # Rückwärts mit variabler Geschwindigkeit
            speed = -max_speed * aggressiveness
            if self.motor:
                self.motor.set_linear_angular_speed(speed, 0.0)
        elif progress < 0.8:
            # Adaptive Kurve
            linear_speed = max_speed * (1 - aggressiveness)
            angular_speed = max_speed * aggressiveness
            
            # Richtung basierend auf Hinderniskontext
            obstacle_direction = self.initial_context.get('obstacle_context', {}).get('obstacle_direction')
            if obstacle_direction == 'left':
                angular_speed = abs(angular_speed)
            elif obstacle_direction == 'right':
                angular_speed = -abs(angular_speed)
            
            if self.motor:
                self.motor.set_linear_angular_speed(linear_speed, angular_speed)
        else:
            # Stabilisierung
            if self.motor:
                self.motor.set_linear_angular_speed(0.1, 0.0)
        
        if elapsed_time >= maneuver_duration:
            self._start_recovery()
    
    def _start_recovery(self):
        """Startet Erholungsphase."""
        self.phase = 'recovery'
        self.phase_start_time = time.time()
        
        if self.motor:
            self.motor.stop_immediately(include_mower=False)
        
        print("AdaptiveEscape: Starte Erholungsphase")
    
    def _complete_maneuver(self, success: bool):
        """Schließt das Manöver ab und zeichnet Ergebnis auf."""
        duration = time.time() - self.maneuver_start_time
        
        # Lernergebnis aufzeichnen
        self.learning_system.record_escape_attempt(
            self.initial_context,
            self.current_strategy,
            self.strategy_params,
            success,
            duration
        )
        
        Logger.event(EventCode.OBSTACLE_DETECTED, 
                    f"Adaptive escape completed: {self.current_strategy} ({'success' if success else 'failed'})")
        
        print(f"AdaptiveEscape: Manöver abgeschlossen ({'erfolgreich' if success else 'fehlgeschlagen'})")
        
        # Operation beenden
        self.active = False
    
    def on_stop(self) -> None:
        """Aufräumen beim Beenden der Operation."""
        if self.motor:
            self.motor.stop_immediately(include_mower=False)
        
        # Falls Operation vorzeitig beendet wird, als Fehlschlag aufzeichnen
        if self.phase != 'recovery' and self.initial_context:
            self._complete_maneuver(success=False)
        
        print("AdaptiveEscape: Operation gestoppt")