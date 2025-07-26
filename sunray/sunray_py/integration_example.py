#!/usr/bin/env python3
"""
Beispiel-Integration des Enhanced Escape Systems in die Hauptschleife.
Zeigt, wie Sensorfusion und Self-Learning in das bestehende System integriert werden.
"""

import time
import json
from typing import Dict, Any

# Bestehende Imports
from motor import Motor
from obstacle_detection import ObstacleDetector
from state_estimator import StateEstimator
from imu import IMUSensor
from rtk_gps import RTKGPS
from events import Logger, EventCode
from op import Operation, MowOp, IdleOp

# Neue Enhanced Escape Imports
from enhanced_escape_operations import (
    SensorFusion, 
    LearningSystem, 
    AdaptiveEscapeOp
)

class EnhancedSunrayController:
    """
    Erweiterte Sunray-Steuerung mit intelligenten Ausweichmanövern.
    Integriert Sensorfusion und Self-Learning in die bestehende Architektur.
    """
    
    def __init__(self, config_file: str = 'config.json'):
        # Bestehende Komponenten
        self.motor = Motor()
        self.obstacle_detector = ObstacleDetector()
        self.state_estimator = StateEstimator()
        self.imu = IMUSensor()
        self.gps = RTKGPS()
        
        # Enhanced Escape Komponenten
        self.sensor_fusion = SensorFusion()
        self.learning_system = LearningSystem()
        
        # Konfiguration laden
        self.config = self._load_config(config_file)
        self.enhanced_escape_enabled = self.config.get('enhanced_escape', {}).get('enabled', True)
        
        # Zustandsvariablen
        self.current_op = IdleOp("idle")
        self.last_escape_time = 0
        self.escape_cooldown = 5.0  # Sekunden zwischen Ausweichmanövern
        
        # Statistiken
        self.stats = {
            'total_escapes': 0,
            'enhanced_escapes': 0,
            'traditional_escapes': 0,
            'escape_success_rate': 0.0
        }
        
        Logger.event(EventCode.SYSTEM_STARTED, 
                    f"Enhanced Sunray Controller initialized (Enhanced Escape: {self.enhanced_escape_enabled})")
    
    def _load_config(self, config_file: str) -> Dict:
        """Lädt Konfiguration mit Enhanced Escape Einstellungen."""
        try:
            with open(config_file, 'r') as f:
                config = json.load(f)
            
            # Standard Enhanced Escape Konfiguration hinzufügen falls nicht vorhanden
            if 'enhanced_escape' not in config:
                config['enhanced_escape'] = {
                    'enabled': True,
                    'learning_enabled': True,
                    'learning_file': 'escape_learning_data.json',
                    'min_samples_for_learning': 5,
                    'learning_rate': 0.1,
                    'sensor_fusion': {
                        'gps_weight': 0.4,
                        'imu_weight': 0.3,
                        'odometry_weight': 0.2,
                        'current_weight': 0.1
                    },
                    'escape_strategies': {
                        'adaptive_escape_threshold': 0.7,
                        'fallback_to_traditional': True,
                        'max_learning_attempts': 100
                    }
                }
            
            return config
        except (FileNotFoundError, json.JSONDecodeError) as e:
            Logger.event(EventCode.ERROR, f"Config loading failed: {e}")
            return {'enhanced_escape': {'enabled': False}}
    
    def run_main_loop(self):
        """Hauptschleife mit Enhanced Escape Integration."""
        Logger.event(EventCode.SYSTEM_STARTED, "Starting enhanced main loop")
        
        try:
            while True:
                loop_start_time = time.time()
                
                # Sensordaten sammeln
                sensor_data = self._collect_sensor_data()
                
                # Zustand schätzen
                robot_state = self.state_estimator.compute_robot_state(
                    sensor_data['imu_data'],
                    sensor_data['gps_data'],
                    sensor_data['pico_data']
                )
                
                # Hinderniserkennung
                obstacle_detected = self.obstacle_detector.update(
                    sensor_data['pico_data'],
                    sensor_data['imu_data']
                )
                
                # Enhanced Escape Logik
                if obstacle_detected:
                    self._handle_obstacle_detection(sensor_data, robot_state)
                
                # Aktuelle Operation ausführen
                if self.current_op and self.current_op.active:
                    self.current_op.run()
                else:
                    # Zurück zum Mähen wenn keine Operation aktiv
                    if not isinstance(self.current_op, MowOp):
                        self._start_mowing()
                
                # Neigungswarnung prüfen
                if robot_state.get('tilt_warning', False):
                    self._handle_tilt_warning()
                
                # Statistiken aktualisieren
                self._update_statistics()
                
                # Loop-Timing
                loop_duration = time.time() - loop_start_time
                if loop_duration < 0.1:  # 10 Hz Target
                    time.sleep(0.1 - loop_duration)
                
        except KeyboardInterrupt:
            Logger.event(EventCode.SYSTEM_STOPPED, "Main loop interrupted by user")
        except Exception as e:
            Logger.event(EventCode.ERROR, f"Main loop error: {e}")
        finally:
            self._cleanup()
    
    def _collect_sensor_data(self) -> Dict[str, Any]:
        """Sammelt alle verfügbaren Sensordaten."""
        return {
            'imu_data': self.imu.read(),
            'gps_data': self.gps.read() or {},
            'pico_data': self.motor.get_pico_data(),
            'odometry_data': self.motor.get_odometry_data(),
            'current_data': self.motor.get_current_data(),
            'motor_status': self.motor.get_status(),
            'timestamp': time.time()
        }
    
    def _handle_obstacle_detection(self, sensor_data: Dict, robot_state: Dict):
        """Behandelt Hinderniserkennung mit Enhanced Escape System."""
        current_time = time.time()
        
        # Cooldown prüfen
        if current_time - self.last_escape_time < self.escape_cooldown:
            Logger.event(EventCode.OBSTACLE_DETECTED, "Obstacle detected but in cooldown period")
            return
        
        self.last_escape_time = current_time
        self.stats['total_escapes'] += 1
        
        # Enhanced Escape verwenden wenn aktiviert
        if self.enhanced_escape_enabled:
            success = self._execute_enhanced_escape(sensor_data, robot_state)
            if success:
                self.stats['enhanced_escapes'] += 1
                return
            else:
                Logger.event(EventCode.WARNING, "Enhanced escape failed, falling back to traditional")
        
        # Fallback auf traditionelle Ausweichmanöver
        self._execute_traditional_escape(sensor_data)
        self.stats['traditional_escapes'] += 1
    
    def _execute_enhanced_escape(self, sensor_data: Dict, robot_state: Dict) -> bool:
        """Führt Enhanced Escape mit Sensorfusion und Learning aus."""
        try:
            # Sensorfusion durchführen
            fused_context = self.sensor_fusion.fuse_sensor_data(
                sensor_data['gps_data'],
                sensor_data['imu_data'],
                sensor_data['odometry_data'],
                sensor_data['current_data']
            )
            
            # Lernbasierte Strategieempfehlung
            strategy, params, confidence = self.learning_system.get_recommended_strategy(fused_context)
            
            # Mindestvertrauen prüfen
            min_confidence = self.config['enhanced_escape']['escape_strategies']['adaptive_escape_threshold']
            if confidence < min_confidence:
                Logger.event(EventCode.WARNING, 
                           f"Low confidence ({confidence:.2f}) for enhanced escape")
                return False
            
            # Enhanced Escape Operation starten
            escape_params = {
                'gps_data': sensor_data['gps_data'],
                'imu_data': sensor_data['imu_data'],
                'odometry_data': sensor_data['odometry_data'],
                'current_data': sensor_data['current_data'],
                'robot_position': {
                    'x': robot_state.get('x', 0),
                    'y': robot_state.get('y', 0),
                    'heading': robot_state.get('heading', 0)
                },
                'fused_context': fused_context
            }
            
            # Aktuelle Operation stoppen
            if self.current_op and self.current_op.active:
                self.current_op.stop()
            
            # Adaptive Escape starten
            self.current_op = AdaptiveEscapeOp("enhanced_escape", self.motor)
            self.current_op.start(escape_params)
            
            Logger.event(EventCode.OBSTACLE_DETECTED, 
                        f"Enhanced escape started: {strategy} (confidence: {confidence:.2f})")
            
            return True
            
        except Exception as e:
            Logger.event(EventCode.ERROR, f"Enhanced escape failed: {e}")
            return False
    
    def _execute_traditional_escape(self, sensor_data: Dict):
        """Führt traditionelles Ausweichmanöver aus."""
        from op import EscapeForwardOp, SmartBumperEscapeOp
        
        # Bumper-Status prüfen
        pico_data = sensor_data['pico_data']
        left_bumper = pico_data.get('bumper_left', False)
        right_bumper = pico_data.get('bumper_right', False)
        
        # Aktuelle Operation stoppen
        if self.current_op and self.current_op.active:
            self.current_op.stop()
        
        # Strategie basierend auf Bumper-Status wählen
        if left_bumper or right_bumper:
            # Smart Bumper Escape für Bumper-Kollisionen
            escape_params = {
                'left_bumper': left_bumper,
                'right_bumper': right_bumper
            }
            self.current_op = SmartBumperEscapeOp("smart_bumper_escape", self.motor)
            Logger.event(EventCode.OBSTACLE_DETECTED, "Traditional smart bumper escape started")
        else:
            # Forward Escape für andere Hindernisse
            self.current_op = EscapeForwardOp("escape_forward", self.motor)
            Logger.event(EventCode.OBSTACLE_DETECTED, "Traditional forward escape started")
        
        self.current_op.start(escape_params if 'escape_params' in locals() else {})
    
    def _handle_tilt_warning(self):
        """Behandelt Neigungswarnung."""
        if self.current_op and self.current_op.active:
            self.current_op.stop()
        
        # Sofortiger Stopp bei gefährlicher Neigung
        self.motor.stop_immediately()
        
        # Idle-Operation starten
        self.current_op = IdleOp("tilt_safety")
        self.current_op.start()
        
        Logger.event(EventCode.SAFETY_STOP, "Robot tilted - safety stop activated")
    
    def _start_mowing(self):
        """Startet Mähoperation."""
        self.current_op = MowOp("mow", self.motor)
        self.current_op.start()
        Logger.event(EventCode.OPERATION_STARTED, "Mowing operation started")
    
    def _update_statistics(self):
        """Aktualisiert Systemstatistiken."""
        if self.stats['total_escapes'] > 0:
            enhanced_rate = self.stats['enhanced_escapes'] / self.stats['total_escapes']
            self.stats['enhanced_escape_rate'] = enhanced_rate
        
        # Learning-Statistiken abrufen
        if self.enhanced_escape_enabled:
            learning_stats = self.learning_system.get_learning_statistics()
            self.stats.update(learning_stats)
    
    def _cleanup(self):
        """Aufräumarbeiten beim Beenden."""
        Logger.event(EventCode.SYSTEM_STOPPED, "Cleaning up Enhanced Sunray Controller")
        
        # Aktuelle Operation stoppen
        if self.current_op and self.current_op.active:
            self.current_op.stop()
        
        # Motoren stoppen
        self.motor.stop_immediately()
        
        # Statistiken ausgeben
        self._print_final_statistics()
        
        # GPS-Verbindung schließen
        self.gps.close()
    
    def _print_final_statistics(self):
        """Gibt finale Statistiken aus."""
        print("\n=== Enhanced Sunray Controller Statistics ===")
        print(f"Total Escapes: {self.stats['total_escapes']}")
        print(f"Enhanced Escapes: {self.stats['enhanced_escapes']}")
        print(f"Traditional Escapes: {self.stats['traditional_escapes']}")
        
        if 'overall_success_rate' in self.stats:
            print(f"Overall Success Rate: {self.stats['overall_success_rate']:.2%}")
        
        if 'learned_contexts' in self.stats:
            print(f"Learned Contexts: {self.stats['learned_contexts']}")
        
        print("============================================\n")
    
    def get_status(self) -> Dict:
        """Gibt aktuellen Systemstatus zurück."""
        status = {
            'current_operation': self.current_op.name if self.current_op else 'none',
            'enhanced_escape_enabled': self.enhanced_escape_enabled,
            'motor_status': self.motor.get_status(),
            'obstacle_status': self.obstacle_detector.get_status(),
            'statistics': self.stats.copy()
        }
        
        if self.enhanced_escape_enabled:
            status['learning_stats'] = self.learning_system.get_learning_statistics()
        
        return status
    
    def enable_enhanced_escape(self, enabled: bool):
        """Aktiviert/deaktiviert Enhanced Escape System."""
        self.enhanced_escape_enabled = enabled
        Logger.event(EventCode.SYSTEM_CONFIG_CHANGED, 
                    f"Enhanced Escape {'enabled' if enabled else 'disabled'}")
    
    def reset_learning_data(self):
        """Setzt Learning-Daten zurück."""
        if self.enhanced_escape_enabled:
            self.learning_system = LearningSystem()
            Logger.event(EventCode.SYSTEM_CONFIG_CHANGED, "Learning data reset")

# Beispiel für HTTP-API-Integration
def create_enhanced_api_endpoints(app, controller: EnhancedSunrayController):
    """Erstellt API-Endpunkte für Enhanced Escape System."""
    
    @app.route('/api/enhanced/status')
    def get_enhanced_status():
        return controller.get_status()
    
    @app.route('/api/enhanced/escape/enable', methods=['POST'])
    def enable_enhanced_escape():
        enabled = request.json.get('enabled', True)
        controller.enable_enhanced_escape(enabled)
        return {'success': True, 'enabled': enabled}
    
    @app.route('/api/enhanced/learning/stats')
    def get_learning_stats():
        if controller.enhanced_escape_enabled:
            return controller.learning_system.get_learning_statistics()
        return {'error': 'Enhanced escape not enabled'}
    
    @app.route('/api/enhanced/learning/reset', methods=['POST'])
    def reset_learning():
        controller.reset_learning_data()
        return {'success': True, 'message': 'Learning data reset'}

# Hauptfunktion für direkten Start
def main():
    """Hauptfunktion für Enhanced Sunray Controller."""
    print("Starting Enhanced Sunray Controller...")
    
    controller = EnhancedSunrayController()
    
    try:
        controller.run_main_loop()
    except KeyboardInterrupt:
        print("\nShutdown requested by user")
    except Exception as e:
        print(f"\nUnexpected error: {e}")
    finally:
        print("Enhanced Sunray Controller stopped")

if __name__ == "__main__":
    main()