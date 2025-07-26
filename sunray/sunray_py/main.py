#!/usr/bin/env python3
"""
Hauptskript für Sunray-Python-Port auf Raspberry Pi 4B.
Initialisiert Module, startet Web-API und MQTT, führt State-Machine aus.
"""

import time
import threading

# Hardware Imports mit Fallback
try:
    from imu import IMUSensor
    from rtk_gps import RTKGPS
    from hardware_manager import get_hardware_manager
    HARDWARE_AVAILABLE = True
except (ImportError, NotImplementedError):
    print("Hardware Module nicht verfügbar, verwende Mock Hardware")
    from mock_hardware import get_hardware_or_mock
    HARDWARE_AVAILABLE = False
from battery import Battery
from motor import Motor
from map import Map
from state_estimator import StateEstimator
from events import Logger, EventCode
from storage import Storage
from mqtt_client import MQTTClient
from http_server import app
from op import IdleOp, MowOp, EscapeForwardOp, SmartBumperEscapeOp
from obstacle_detection import ObstacleDetector
from path_planner import MowPattern
from enhanced_escape_operations import SensorFusion, LearningSystem, AdaptiveEscapeOp
from integration_example import EnhancedSunrayController

def select_operation(op_type: str, motor=None):
    """Operation-Factory basierend auf Zustand."""
    if op_type == "mow":
        return MowOp("mow", motor=motor)
    if op_type == "dock":
        return DockOp("dock")
    if op_type == "escape_forward":
        return EscapeForwardOp("escape_forward", motor=motor)
    return IdleOp("idle")

def process_pico_data(line: str) -> dict:
    """
    Verarbeitung der ASCII-Sensordatenzeile vom Pico.
    Unterstützt sowohl AT+S: (Sensordaten) als auch S, (Summary mit Stromdaten).
    """
    if line.startswith("AT+S:"):
        # Normale Sensordaten: AT+S:odom_right,odom_left,odom_mow,chg_voltage,,bumper,lift
        parts = line[5:].split(",")
        return {
            "odom_right": int(parts[0]),
            "odom_left": int(parts[1]),
            "odom_mow": int(parts[2]),
            "chg_voltage": float(parts[3]),
            "bumper": int(parts[5]),
            "lift": int(parts[6]),
        }
    elif line.startswith("S,"):
        # Summary-Daten mit Stromdaten: S,batVoltageLP,chgVoltage,chgCurrentLP,lift,bumper,raining,motorOverload,mowCurrLP,motorLeftCurrLP,motorRightCurrLP,batteryTemp
        parts = line[2:].split(",")
        if len(parts) >= 11:
            return {
                "bat_voltage": float(parts[0]),
                "chg_voltage": float(parts[1]),
                "chg_current": float(parts[2]),
                "lift": int(parts[3]),
                "bumper": int(parts[4]),
                "raining": int(parts[5]),
                "motor_overload": int(parts[6]),
                "mow_current": float(parts[7]),
                "motor_left_current": float(parts[8]),
                "motor_right_current": float(parts[9]),
                "battery_temp": float(parts[10]),
            }
    return {}

def main():
    # Module initialisieren
    if HARDWARE_AVAILABLE:
        imu = IMUSensor()
        gps = RTKGPS()
        hardware_manager = get_hardware_manager(port='/dev/ttyS0', baudrate=115200)
    else:
        imu, gps, hardware_manager = get_hardware_or_mock()
    
    battery = Battery()
    motor = Motor(hardware_manager=hardware_manager)
    map_module = Map()
    map_module.load_zones('zones.json')
    estimator = StateEstimator()
    storage = Storage('state.json')
    logger = Logger
    mqtt = MQTTClient()
    obstacle_detector = ObstacleDetector()  # Stromdaten kommen vom Pico über UART
    
    # Enhanced Escape System initialisieren
    sensor_fusion = SensorFusion()
    learning_system = LearningSystem()
    enhanced_controller = EnhancedSunrayController(
        motor=motor,
        sensor_fusion=sensor_fusion,
        learning_system=learning_system,
        obstacle_detector=obstacle_detector,
        state_estimator=estimator
    )
    
    print("Enhanced Escape System initialisiert - Intelligente Navigation aktiviert")

    # Zustand aus Speicher laden
    last_state = storage.load()
    logger.event(EventCode.SYSTEM_STARTED)
    robot_state = last_state
    
    # Motor initialisieren
    motor.begin()
    
    # Pfadplanung konfigurieren
    if map_module.zones:
        motor.set_mow_zones(map_module.zones)
        print(f"Pfadplanung: {len(map_module.zones)} Mähzonen geladen")
    
    if map_module.exclusions:
        motor.set_obstacles(map_module.exclusions)
        print(f"Pfadplanung: {len(map_module.exclusions)} Ausschlusszonen als Hindernisse gesetzt")
    
    # Standard-Mähmuster setzen
    motor.set_mow_pattern(MowPattern.LINES)
    motor.set_line_spacing(0.3)  # 30cm Abstand zwischen Linien
    
    # Position tracking
    last_position_update = 0
    position_update_interval = 0.5  # Sekunden

    # Motor-Instanz und Enhanced System an HTTP-Server übergeben
    from http_server import set_motor_instance, set_enhanced_system
    set_motor_instance(motor)
    set_enhanced_system(enhanced_controller, sensor_fusion, learning_system)
    
    # Web-API starten (Flask)
    threading.Thread(
        target=lambda: app.run(host='0.0.0.0', port=5000),
        daemon=True
    ).start()

    # MQTT-Verbindung starten
    mqtt.connect('localhost', 1883)
    threading.Thread(target=mqtt.loop_forever, daemon=True).start()

    print("Sunray-Pi: System bereit.")

    # Start-Operation (Idle)
    current_op = IdleOp("idle")
    current_op.start()
    
    # Timer für Summary-Anfragen
    last_summary_request = 0
    summary_interval = 1.0  # Sekunden

    try:
        while True:
            # Regelmäßig Summary-Daten anfordern für Stromdaten
            current_time = time.time()
            if current_time - last_summary_request >= summary_interval:
                hardware_manager.send_command("AT+S,1")  # Summary mit Sunray-State anfordern
                last_summary_request = current_time
            
            sensor_data = hardware_manager.get_sensor_data()
            pico_data = process_pico_data(sensor_data) if sensor_data else {}

            # IMU-Daten lesen und Neigungswarnung prüfen
            imu_data = imu.read()
            gps_data = gps.read() or {}
            
            # Batteriedaten vom Pico verarbeiten
            if pico_data and 'bat_voltage' in pico_data:
                battery_status = battery.run(
                    pico_data.get('bat_voltage', 0.0),
                    pico_data.get('chg_voltage', 0.0),
                    pico_data.get('chg_current', 0.0)
                )
            else:
                battery_status = {}
            
            # Motordaten vom Pico verarbeiten
            motor_status = motor.update(pico_data)
            motor.run()  # PID-Regelung ausführen
            
            batt_ok = not battery.under_voltage()
            
            # Hinderniserkennung aktualisieren
            obstacle_detected = obstacle_detector.update(pico_data, imu_data)
            
            # Sicherheitsabschaltung bei zu starker Neigung oder Hindernis
            emergency_stop = False
            
            # Neigungswarnung prüfen
            if imu_data.get('tilt_warning', False):
                logger.event(EventCode.TILT_WARNING)
                emergency_stop = True
            
            # Enhanced Escape System - Intelligente Hindernisbehandlung
            if obstacle_detected:
                # Sensordaten für Enhanced System sammeln
                sensor_data_enhanced = {
                    'imu': imu_data,
                    'gps': gps_data,
                    'pico': pico_data,
                    'robot_state': robot_state,
                    'obstacle_status': obstacle_detector.get_status()
                }
                
                # Enhanced Escape System verwenden für intelligente Ausweichmanöver
                if current_op.name == "mow":
                    current_op.stop()
                    
                    # Intelligente Ausweichstrategie durch Enhanced System bestimmen
                    escape_result = enhanced_controller.handle_obstacle(
                        sensor_data_enhanced,
                        current_context=current_op.name
                    )
                    
                    if escape_result['success']:
                        # Adaptive Escape Operation verwenden
                        current_op = AdaptiveEscapeOp(
                            "adaptive_escape", 
                            motor=motor,
                            strategy=escape_result['strategy'],
                            parameters=escape_result['parameters'],
                            sensor_fusion=sensor_fusion,
                            learning_system=learning_system
                        )
                        print(f"Enhanced Escape aktiviert: Strategie={escape_result['strategy']}, Kontext={escape_result['context']}")
                        current_op.start(escape_result['parameters'])
                    else:
                        # Fallback auf traditionelle Methode
                        obstacle_status = obstacle_detector.get_status()
                        bumper_info = obstacle_status.get('bumper', {})
                        if bumper_info.get('collision_detected', False):
                            current_op = SmartBumperEscapeOp("smart_bumper_escape", motor=motor)
                        else:
                            current_op = EscapeForwardOp("escape_forward", motor=motor)
                        current_op.start({})
                        print("Fallback auf traditionelle Ausweichstrategie")
                    
                    motor.stop_immediately(include_mower=False)
                    
                # Bei anderen Modi komplett stoppen
                elif current_op.name != "idle" and current_op.name not in ["escape_forward", "smart_bumper_escape", "adaptive_escape"]:
                    emergency_stop = True
            
            # Notfall-Stopp durchführen wenn nötig
            if emergency_stop and current_op.name != "idle":
                current_op.stop()
                current_op = IdleOp("idle")
                current_op.start()
                motor.stop_immediately()  # Motoren über Motor-Klasse stoppen
                hardware_manager.send_command("AT+STOP")  # Zusätzlicher Notfall-Stopp an Pico
            
            # Roboterzustand berechnen
            robot_state = estimator.compute_robot_state(
                imu_data, gps_data, pico_data
            )
            
            # Hindernisinfo zum Roboterzustand hinzufügen
            robot_state.update(obstacle_detector.get_status())
            
            # Enhanced System kontinuierlich aktualisieren
            enhanced_sensor_data = {
                'imu': imu_data,
                'gps': gps_data,
                'pico': pico_data,
                'robot_state': robot_state,
                'obstacle_status': obstacle_detector.get_status(),
                'timestamp': current_time
            }
            
            # Sensorfusion aktualisieren
            fused_data = sensor_fusion.fuse_sensors(enhanced_sensor_data)
            
            # Learning System mit aktuellen Daten füttern
            if current_op.name == "mow":
                learning_system.update_context_data(fused_data)
            
            # Adaptive Escape Operation Feedback verarbeiten
            if hasattr(current_op, 'get_performance_feedback'):
                feedback = current_op.get_performance_feedback()
                if feedback:
                    learning_system.process_feedback(feedback)
                    print(f"Enhanced System Lernen: {feedback.get('strategy', 'unknown')} - Erfolg: {feedback.get('success', False)}")
            
            # Position für Pfadplanung aktualisieren
            if current_time - last_position_update >= position_update_interval:
                if 'x' in robot_state and 'y' in robot_state and 'heading' in robot_state:
                    motor.update_position(
                        robot_state['x'], 
                        robot_state['y'], 
                        robot_state['heading']
                    )
                last_position_update = current_time

            desired_op = select_operation(robot_state.get("op_type", "idle"), motor=motor)
            if type(desired_op) is not type(current_op):
                current_op.stop()
                current_op = desired_op
                current_op.start(robot_state)

            current_op.run()

            # Telemetriedaten über MQTT veröffentlichen (mit Enhanced System Daten)
            enhanced_telemetry = {
                "imu": imu_data,
                "gps": gps_data,
                "obstacles": obstacle_detector.get_status(),
                "battery": {
                    "voltage": pico_data.get('bat_voltage', 0.0),
                    "charge_voltage": pico_data.get('chg_voltage', 0.0),
                    "charge_current": pico_data.get('chg_current', 0.0),
                    "charger_connected": battery.charger_connected(),
                    "is_docked": battery.is_docked(),
                    "should_go_home": battery.should_go_home(),
                    "under_voltage": battery.under_voltage(),
                    "charging_completed": battery.is_charging_completed(),
                    **battery_status
                },
                "motor": motor_status,
                "enhanced_system": {
                    "sensor_fusion": {
                        "confidence": fused_data.get('confidence', 0.0),
                        "context": fused_data.get('context', 'unknown'),
                        "sensor_weights": sensor_fusion.get_current_weights()
                    },
                    "learning_system": {
                        "total_maneuvers": learning_system.get_statistics().get('total_maneuvers', 0),
                        "success_rate": learning_system.get_statistics().get('success_rate', 0.0),
                        "active_strategy": getattr(current_op, 'strategy', None) if hasattr(current_op, 'strategy') else None,
                        "learning_enabled": learning_system.learning_enabled
                    },
                    "current_operation": {
                        "name": current_op.name,
                        "is_adaptive": isinstance(current_op, AdaptiveEscapeOp)
                    }
                },
                **pico_data
            }
            
            mqtt.publish("sunray/telemetry", enhanced_telemetry)
            
            # Separate Enhanced System Statistiken
            if current_time % 10 < 0.1:  # Alle 10 Sekunden
                mqtt.publish("sunray/enhanced_stats", {
                    "learning_stats": learning_system.get_statistics(),
                    "sensor_fusion_stats": sensor_fusion.get_statistics(),
                    "context_distribution": learning_system.get_context_distribution()
                })

            storage.save(robot_state)
            time.sleep(0.1)

    except KeyboardInterrupt:
        print("Sunray-Pi: Beende Hauptloop")
    finally:
        if HARDWARE_AVAILABLE and hardware_manager:
            hardware_manager.close()
        logger.event(EventCode.SYSTEM_SHUTTING_DOWN)
        storage.save(robot_state)

if __name__ == '__main__':
    main()
