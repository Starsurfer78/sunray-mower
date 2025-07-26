#!/usr/bin/env python3
"""
Hauptskript für Sunray-Python-Port auf Raspberry Pi 4B.
Initialisiert Module, startet Web-API und MQTT, führt State-Machine aus.
"""

import time
import threading
from imu import IMUSensor
from rtk_gps import RTKGPS
from pico_comm import PicoComm
from battery import Battery
from motor import Motor
from map import Map
from state_estimator import StateEstimator
from events import Logger, EventCode
from storage import Storage
from mqtt_client import MQTTClient
from http_server import app
from op import IdleOp, DockOp, MowOp, EscapeForwardOp
from obstacle_detection import ObstacleDetector

def select_operation(op_type: str, motor=None):
    """Operation-Factory basierend auf Zustand."""
    if op_type == "mow":
        return MowOp("mow")
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
    imu = IMUSensor()
    gps = RTKGPS()
    battery = Battery()
    pico = PicoComm(port='/dev/ttyS0', baudrate=115200)
    motor = Motor(pico_comm=pico)
    map_module = Map()
    map_module.load_zones('zones.json')
    estimator = StateEstimator()
    storage = Storage('state.json')
    logger = Logger
    mqtt = MQTTClient()
    obstacle_detector = ObstacleDetector()  # Stromdaten kommen vom Pico über UART

    # Zustand aus Speicher laden
    last_state = storage.load()
    logger.event(EventCode.SYSTEM_STARTED)
    robot_state = last_state
    
    # Motor initialisieren
    motor.begin()

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
                pico.send_command("AT+S,1")  # Summary mit Sunray-State anfordern
                last_summary_request = current_time
            
            pico_line = pico.read_sensor_data()
            pico_data = process_pico_data(pico_line) if pico_line else {}

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
            
            # Hindernis erkannt
            if obstacle_detected:
                # Wenn im Mähmodus, auf EscapeForward wechseln
                if current_op.name == "mow":
                    current_op.stop()
                    current_op = EscapeForwardOp("escape_forward", motor=motor)
                    current_op.start()
                    motor.stop_immediately(include_mower=False)  # Motoren über Motor-Klasse stoppen
                # Bei anderen Modi komplett stoppen
                elif current_op.name != "idle" and current_op.name != "escape_forward":
                    emergency_stop = True
            
            # Notfall-Stopp durchführen wenn nötig
            if emergency_stop and current_op.name != "idle":
                current_op.stop()
                current_op = IdleOp("idle")
                current_op.start()
                motor.stop_immediately()  # Motoren über Motor-Klasse stoppen
                pico.send_command("AT+STOP")  # Zusätzlicher Notfall-Stopp an Pico
            
            # Roboterzustand berechnen
            robot_state = estimator.compute_robot_state(
                imu_data, gps_data, pico_data
            )
            
            # Hindernisinfo zum Roboterzustand hinzufügen
            robot_state.update(obstacle_detector.get_status())

            desired_op = select_operation(robot_state.get("op_type", "idle"), motor=motor)
            if type(desired_op) is not type(current_op):
                current_op.stop()
                current_op = desired_op
                current_op.start(robot_state)

            current_op.run()

            # Telemetriedaten über MQTT veröffentlichen
            mqtt.publish("sunray/telemetry", {
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
                **pico_data
            })

            storage.save(robot_state)
            time.sleep(0.1)

    except KeyboardInterrupt:
        print("Sunray-Pi: Beende Hauptloop")
    finally:
        pico.close()
        logger.event(EventCode.SYSTEM_SHUTTING_DOWN)
        storage.save(robot_state)

if __name__ == '__main__':
    main()
