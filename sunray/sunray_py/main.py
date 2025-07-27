#!/usr/bin/env python3
"""
Sunray Mähroboter - Python Implementation
Based on the Ardumower Sunray project

Original Sunray project:
- Forum: https://forum.ardumower.de/
- GitHub: https://github.com/Ardumower/Sunray
- Copyright (c) 2021-2024 by Alexander Grau, Grau GmbH

This implementation extends and adapts the original Sunray firmware
for Python-based autonomous mower control with enhanced features.

License: GPL-3.0 (same as original Sunray project)
Author: [Ihr Name]
Project: https://github.com/Starsurfer78/sunray-mower

Hauptskript für Sunray-Python-Port auf Raspberry Pi 4B.
Initialisiert Module, startet Web-API und MQTT, führt State-Machine aus.
"""

import time
import threading

# Hardware Imports mit Fallback
try:
    from hardware.imu import IMUSensor
    from rtk_gps import RTKGPS
    from hardware.hardware_manager import get_hardware_manager
    HARDWARE_AVAILABLE = True
except (ImportError, NotImplementedError):
    print("Hardware Module nicht verfügbar, verwende Mock Hardware")
    from mock_hardware import get_hardware_or_mock
    HARDWARE_AVAILABLE = False
from hardware.battery import Battery
from hardware.motor import Motor
from map import Map
from state_estimator import StateEstimator
from events import Logger, EventCode
from storage import Storage
from communication.mqtt_client import MQTTClient
from http_server import app
from op import IdleOp, MowOp, EscapeForwardOp, SmartBumperEscapeOp, GpsWaitRtkOp, GpsErrorOp, ReturnToSafeZoneOp
from safety.obstacle_detection import ObstacleDetector
from navigation.path_planner import MowPattern
from enhanced_escape_operations import SensorFusion, LearningSystem, AdaptiveEscapeOp
from examples.integration_example import EnhancedSunrayController
from smart_button_controller import SmartButtonController, ButtonAction, RobotState, get_smart_button_controller
from navigation.gps_navigation import GPSNavigation
from navigation.advanced_path_planner import AdvancedPathPlanner, PlanningStrategy

def select_operation(op_type: str, motor=None, **params):
    """Operation-Factory basierend auf Zustand."""
    if op_type == "mow":
        return MowOp("mow", motor=motor)
    if op_type == "dock":
        return DockOp("dock")
    if op_type == "escape_forward":
        return EscapeForwardOp("escape_forward", motor=motor)
    if op_type == "gps_wait_rtk":
        return GpsWaitRtkOp("gps_wait_rtk", motor=motor)
    if op_type == "gps_error":
        return GpsErrorOp("gps_error", motor=motor)
    if op_type == "return_to_safe_zone":
        return ReturnToSafeZoneOp("return_to_safe_zone", motor=motor)
    return IdleOp("idle")

def process_pico_data(line: str) -> dict:
    """
    Verarbeitung der ASCII-Sensordatenzeile vom Pico.
    Unterstützt sowohl AT+S: (Sensordaten) als auch S, (Summary mit Stromdaten).
    Erweitert um Stop-Button-Verarbeitung.
    """
    if line.startswith("AT+S:"):
        # Normale Sensordaten: AT+S:odom_right,odom_left,odom_mow,chg_voltage,,bumper,lift,stopButton
        parts = line[5:].split(",")
        data = {
            "odom_right": int(parts[0]) if len(parts) > 0 and parts[0] else 0,
            "odom_left": int(parts[1]) if len(parts) > 1 and parts[1] else 0,
            "odom_mow": int(parts[2]) if len(parts) > 2 and parts[2] else 0,
            "chg_voltage": float(parts[3]) if len(parts) > 3 and parts[3] else 0.0,
            "bumper": int(parts[5]) if len(parts) > 5 and parts[5] else 0,
            "lift": int(parts[6]) if len(parts) > 6 and parts[6] else 0,
        }
        # Stop-Button hinzufügen falls verfügbar
        if len(parts) > 7 and parts[7]:
            data["stopButton"] = int(parts[7])
        return data
    elif line.startswith("S,"):
        # Summary-Daten mit Stromdaten: S,batVoltageLP,chgVoltage,chgCurrentLP,lift,bumper,raining,motorOverload,mowCurrLP,motorLeftCurrLP,motorRightCurrLP,batteryTemp,stopButton
        parts = line[2:].split(",")
        if len(parts) >= 11:
            data = {
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
            # Stop-Button hinzufügen falls verfügbar
            if len(parts) > 11 and parts[11]:
                data["stopButton"] = int(parts[11])
            return data
    return {}

def main():
    # Module initialisieren
    if HARDWARE_AVAILABLE:
        imu = IMUSensor()
        # Konfiguration laden
        rtk_mode = "auto"
        ntrip_enabled = False
        ntrip_fallback = True
        rtk_port = "/dev/ttyUSB0"
        rtk_baudrate = 115200
        auto_configure = True
        
        # Hardware-Konfiguration
        pico_port = "/dev/ttyS0"
        pico_baudrate = 115200
        
        try:
            import json
            with open('config.json', 'r') as f:
                config = json.load(f)
                
                # Hardware-Konfiguration
                hardware_config = config.get('hardware', {})
                pico_config = hardware_config.get('pico_communication', {})
                pico_port = pico_config.get('port', '/dev/ttyS0')
                pico_baudrate = pico_config.get('baudrate', 115200)
                
        except (FileNotFoundError, json.JSONDecodeError, KeyError) as e:
            print(f"Warnung: Konfigurationsdatei nicht gefunden oder fehlerhaft ({e}). Verwende Standardwerte.")
            config = {}
        
        # RTK-GPS initialisieren mit Konfiguration
        gps = RTKGPS(config=config)
        
        # RTK-Konfiguration für Ausgabe laden
        rtk_config = config.get('hardware', {}).get('rtk_gps', {})
        rtk_mode = rtk_config.get('rtk_mode', 'auto')
        ntrip_fallback = rtk_config.get('enable_ntrip_fallback', True)
        
        print(f"RTK-GPS: Modus '{rtk_mode}' - XBee RTK mit NTRIP-Fallback: {ntrip_fallback}")
        if rtk_mode == "ntrip":
            print("RTK-GPS: Nur NTRIP-Modus")
        elif rtk_mode == "xbee":
            print("RTK-GPS: Nur XBee RTK-Modus")
        else:
            print("RTK-GPS: Automatische RTK-Quellenerkennung")
        
        # Hardware Manager mit konfigurierbarem Port/Baudrate
        hardware_manager = get_hardware_manager(port=pico_port, baudrate=pico_baudrate)
        print(f"Hardware Manager: Port '{pico_port}', Baudrate {pico_baudrate}")
    else:
        imu, gps, hardware_manager = get_hardware_or_mock()
    
    battery = Battery()
    motor = Motor(hardware_manager=hardware_manager)
    map_module = Map()
    map_module.load_zones('zones.json')
    # Konfiguration für StateEstimator laden
    try:
        import json
        with open('config.json', 'r') as f:
            config = json.load(f)
    except (FileNotFoundError, json.JSONDecodeError) as e:
        print(f"Warnung: Konfigurationsdatei nicht gefunden ({e}). Verwende Standardwerte.")
        config = {}
    
    estimator = StateEstimator(config)
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
    
    # Erweiterte Pfadplanung initialisieren
    advanced_planner = AdvancedPathPlanner()
    print("Erweiterte Pfadplanung initialisiert")
    
    # GPS-Navigation mit erweiterter Pfadplanung initialisieren
    gps_navigation = GPSNavigation(gps, advanced_planner)
    print("GPS-Navigation mit erweiterter Pfadplanung initialisiert")
    
    # Smart Button Controller initialisieren
    button_controller = get_smart_button_controller(
        motor=motor,
        state_estimator=estimator,
        hardware_manager=hardware_manager
    )
    
    # Button-Aktionen registrieren
    def start_mowing_action():
        """Startet den autonomen Mähvorgang."""
        print("Button-Aktion: Starte Mähvorgang")
        motor.start_autonomous_mowing()
        logger.event(EventCode.SYSTEM_STARTED, "Mähvorgang über Button gestartet")
    
    def stop_mowing_action():
        """Stoppt den aktuellen Mähvorgang."""
        print("Button-Aktion: Stoppe Mähvorgang")
        motor.stop_autonomous_mowing()
        logger.event(EventCode.SYSTEM_STOPPED, "Mähvorgang über Button gestoppt")
    
    def go_home_action():
        """Startet den Docking-Vorgang."""
        print("Button-Aktion: Starte GoHome/Docking")
        motor.go_home()
        logger.event(EventCode.SYSTEM_STARTED, "Docking über Button gestartet")
    
    def emergency_stop_action():
        """Führt einen Notfall-Stopp aus."""
        print("Button-Aktion: Notfall-Stopp")
        motor.emergency_stop()
        logger.event(EventCode.EMERGENCY_STOP, "Notfall-Stopp über Button ausgelöst")
    
    # Callbacks registrieren
    button_controller.set_action_callback(ButtonAction.START_MOW, start_mowing_action)
    button_controller.set_action_callback(ButtonAction.STOP_MOW, stop_mowing_action)
    button_controller.set_action_callback(ButtonAction.GO_HOME, go_home_action)
    button_controller.set_action_callback(ButtonAction.EMERGENCY_STOP, emergency_stop_action)
    
    print("Enhanced Escape System initialisiert - Intelligente Navigation aktiviert")
    print("Smart Button Controller initialisiert - Erweiterte Button-Funktionen verfügbar")

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
        
        # Erweiterte Pfadplanung mit Zonen und Hindernissen konfigurieren
        obstacles = map_module.exclusions if map_module.exclusions else []
        advanced_planner.set_zones_and_obstacles(map_module.zones, obstacles)
        
        # GPS-Navigation mit Zonen konfigurieren
        gps_navigation.set_mow_zones(map_module.zones)
    
    if map_module.exclusions:
        motor.set_obstacles(map_module.exclusions)
        print(f"Pfadplanung: {len(map_module.exclusions)} Ausschlusszonen als Hindernisse gesetzt")
        
        # GPS-Navigation mit Ausschlusszonen konfigurieren
        gps_navigation.set_exclusion_zones(map_module.exclusions)
    
    # Standard-Mähmuster setzen
    motor.set_mow_pattern(MowPattern.LINES)
    motor.set_line_spacing(0.3)  # 30cm Abstand zwischen Linien
    
    # Position tracking
    last_position_update = 0
    position_update_interval = 0.5  # Sekunden

    # Motor-Instanz, Enhanced System und Button Controller an HTTP-Server übergeben
    from http_server import set_motor_instance, set_enhanced_system, set_button_controller
    set_motor_instance(motor)
    set_enhanced_system(enhanced_controller, sensor_fusion, learning_system)
    set_button_controller(button_controller)
    
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
            
            # Smart Button Controller aktualisieren
            button_action = None
            if pico_data:
                # Roboterzustand für Button Controller aktualisieren
                robot_state_data = {
                    'op_type': current_op.name if current_op else 'idle',
                    'battery_level': battery.get_percentage(),
                    'is_docked': battery.is_charging(),
                    'has_map': len(map_module.zones) > 0 if map_module.zones else False
                }
                button_controller.update_robot_state(robot_state_data)
                
                # Button-Eingaben verarbeiten
                button_action = button_controller.update(pico_data)
                if button_action:
                    print(f"Button-Aktion ausgeführt: {button_action.value}")
            
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
                
                # Dynamisches Hindernis zur erweiterten Pfadplanung hinzufügen
                obstacle_status = obstacle_detector.get_status()
                if obstacle_status.get('dynamic_obstacle'):
                    from map import Polygon, Point
                    # Vereinfachtes Hindernis um aktuelle Position erstellen
                    current_pos = robot_state.get('position', {'x': 0, 'y': 0})
                    obstacle_points = [
                        Point(current_pos['x'] - 0.5, current_pos['y'] - 0.5),
                        Point(current_pos['x'] + 0.5, current_pos['y'] - 0.5),
                        Point(current_pos['x'] + 0.5, current_pos['y'] + 0.5),
                        Point(current_pos['x'] - 0.5, current_pos['y'] + 0.5)
                    ]
                    dynamic_obstacle = Polygon(obstacle_points)
                    advanced_planner.add_dynamic_obstacle(dynamic_obstacle)
                    print("Dynamisches Hindernis zur erweiterten Pfadplanung hinzugefügt")
                
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
            
            # Roboterzustand berechnen (inkl. GPS-Sicherheitsbewertung)
            robot_state = estimator.compute_robot_state(
                imu_data, gps_data, pico_data
            )
            
            # GPS-Sicherheitsaktionen verarbeiten
            gps_action = robot_state.get('gps_recommended_action')
            gps_action_params = robot_state.get('gps_action_params', {})
            
            if gps_action and gps_action != 'continue':
                print(f"GPS-Sicherheitsaktion: {gps_action}")
                
                # Aktuelle Operation stoppen falls nötig
                if gps_action in ['stop_and_wait_rtk', 'return_to_safe_zone', 'rtk_wait_timeout_error']:
                    if current_op.name not in ['idle', 'gps_wait_rtk', 'gps_error', 'return_to_safe_zone']:
                        current_op.stop()
                        
                        # Neue GPS-Sicherheitsoperation starten
                        if gps_action == 'stop_and_wait_rtk':
                            current_op = GpsWaitRtkOp("gps_wait_rtk", motor=motor)
                            current_op.start(gps_action_params)
                        elif gps_action == 'return_to_safe_zone':
                            current_op = ReturnToSafeZoneOp("return_to_safe_zone", motor=motor)
                            current_op.start(gps_action_params)
                        elif gps_action == 'rtk_wait_timeout_error':
                            current_op = GpsErrorOp("gps_error", motor=motor)
                            current_op.start(gps_action_params)
                        
                        print(f"GPS-Sicherheitsoperation gestartet: {current_op.name}")
            
            # Geschwindigkeitsfaktor aus GPS-Sicherheit anwenden
            gps_speed_factor = robot_state.get('gps_speed_factor', 1.0)
            if gps_speed_factor < 1.0:
                motor.set_speed_factor(gps_speed_factor)
                print(f"GPS-Sicherheit: Geschwindigkeit reduziert auf {gps_speed_factor*100:.0f}%")
            
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
            
            # GPS-Navigation aktualisieren
            if current_time - last_position_update >= position_update_interval:
                if gps_navigation:
                    gps_status = gps_navigation.update()
                    
                    # Navigation Target an Motor weitergeben
                    nav_target = gps_navigation.get_navigation_target()
                    if nav_target:
                        motor.set_navigation_target(nav_target[0], nav_target[1])
                    
                    # Position an Motor für Navigation weitergeben
                    current_pos = gps_status['current_position']['local']
                    if current_pos[0] != 0.0 or current_pos[1] != 0.0:
                        motor.update_position(current_pos[0], current_pos[1])
                        
                        # Heading aus robot_state verwenden falls verfügbar
                        if 'heading' in robot_state:
                            motor.update_heading(robot_state['heading'])
                
                last_position_update = current_time

            # Operation nur wechseln wenn keine GPS-Sicherheitsoperation aktiv
            if current_op.name not in ['gps_wait_rtk', 'gps_error', 'return_to_safe_zone']:
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
                "advanced_path_planning": advanced_planner.get_planning_status(),
                **pico_data
            }
            
            mqtt.publish("sunray/telemetry", enhanced_telemetry)
            
            # Separate Enhanced System Statistiken
            if current_time % 10 < 0.1:  # Alle 10 Sekunden
                mqtt.publish("sunray/enhanced_stats", {
                    "learning_stats": learning_system.get_statistics(),
                    "sensor_fusion_stats": sensor_fusion.get_statistics(),
                    "context_distribution": learning_system.get_context_distribution(),
                    "path_planning_stats": advanced_planner.get_planning_status()
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
