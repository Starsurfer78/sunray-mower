# Umfassende Implementierungs-TODO

Kombination aus Portierungs-TODO und PRD-Erweiterungen.

## A. Bereits portierte Module (aus sunray_py/TODO.md)

1. **Batteriemanagement** (portiert)

   - `battery.cpp` → `battery.py`
   - Methoden: begin, enable_charging, run, charger_connected, is_docked, should_go_home, under_voltage, is_charging_completed

2. **Motorsteuerung & PID-Regler** (portiert)

   - `motor.cpp` → `motor.py`
   - `pid.cpp` → `pid.py` (`PID`, `VelocityPID`)
   - Methoden: begin, run, test, plot, enable_traction_motors, set_linear_angular_speed, set_mow_state, set_mow_pwm, wait_mow_motor, stop_immediately, speed_pwm, control, check_fault, check_overload, check_odometry_error, check_mow_rpm_fault, drvfix, check_motor_mow_stall, adaptive_speed, change_speed_set, sense, dump_odo_ticks; reset, compute

3. **Kartierung (Map)** (portiert)

   - `map.cpp` → `map.py` (`Map`, `Point`, `Polygon`, `PolygonList`, `Node`, `NodeList`)
   - Funktionen: begin, clear, set_point, save, load; Platzhalter: find_path, next_mow_point

4. **Kommunikation (kommando-basiert)** (portiert)

   - `comm.cpp` → `comm.py` (`CommParser`)
   - Methoden: process_line, \_compute_crc, \_answer

5. **Sensor-Filter & Utilities** (portiert)

   - `lowpass_filter.cpp` → `lowpass_filter.py`
   - `RunningMedian.cpp` → `running_median.py`
   - `helper.cpp` → `helper.py`

6. **State Estimation & Operations** (teilportiert)

   - `StateEstimator.cpp` → `state_estimator.py`
   - `src/op` → `op.py` (Basis + IdleOp, Escape\*, GpsOps, ImuCalibrationOp, WaitOp)

7. **Ereignis-Logging & Storage** (portiert)

   - `events.cpp` → `events.py` (`EventLogger`, `EventCode`)
   - `Storage.cpp` + `Stats.cpp` → `storage.py`, `stats.py`

8. **Kommunikationsschnittstellen** (teilportiert)

   - MQTT → `mqtt_client.py`
   - HTTP → `http_server.py`
   - CAN → `can_client.py`
   - BLE → `ble_client.py`

9. **Tests & Validierung**
   - noch aufzusetzen mit pytest
10. **Pico-Firmware** (fertig)

- Pfad: `Pico/1.0/main.py`
- Funktionen/Services:
  - Odometry-Interrupts: OdometryMowISR, OdometryLeftISR, OdometryRightISR
  - Motorsteuerung: motor(), mower()
  - Sensorik: readSensorHighFrequency(), readSensors(), readMotorCurrent()
  - Power-Management: keepPowerOn(), Watchdog (WDT)
  - UART-Kommandos: cmdMotor(), cmdSummary(), processConsole(), processCmd()
  - Anzeige: printInfo(), printLcd(), secondLoop()
  - Utility: sunrayStateToText()

---

## B. PRD-Ergänzungen (weitere Module & Konzept)

1. **RTK-GPS-Integration**

   - USB-Serial einlesen (pyubx2/pynmea2)
   - GPS-Nachrichten parsen (GGA, VTG, GST)
   - Fix-Status prüfen & lokale Koordinaten umrechnen

2. **Zonenbasierte Mählogik & Navigation**

   - Polygon-basierte Zonen in JSON definieren
   - Pfadgeneratoren (Spirale, Linien)
   - Integration in `map.py.next_mow_point()`
   - Sensorfusion IMU+GPS im `StateEstimator.compute_robot_state()`

3. **State Machine / Operations-Konzept**

   - Zustände: Idle, Mow, Dock, Error, Escape…
   - Zustandsübergänge implementieren in `op.py`
   - Ablaufdiagramm erstellen

4. **Architektur-Konzeptdokument**

   - Schichten- und Modulübersicht
   - Kommunikations- und Datenflussdiagramme

5. **Nächste Priorität**
   - A1–A9 abschließen
   - B1: Motorsteuerung & PID auf Pico dokumentieren
   - B2: RTK+IMU-Fusion implementieren
   - B3: State Machine fertigstellen
   - Konzeptdokument verfassen

---

## C. Übergeordnete Steuerung auf Raspberry Pi 4B

1. Hauptskript `main.py` gestalten

   - Initialisierung der Module (`battery`, `map`, `state_estimator`, `comm`, `mqtt_client`, `http_server`)
   - Instanziierung der State-Machine über `op.py`
   - Einlesen von Sensordaten vom Pico per `pico_comm`
   - Aufruf von `StateEstimator.compute_robot_state()`
   - Disposition von Operationen je nach Zustand (Akku, GPS-Fix, Hindernis)
   - Logging über `events.py` und `storage.py`

2. Kommandozentrale

   - REST-API-Aufrufe an `http_server.py` integrieren
   - MQTT-Client für Telemetrie und Steuerbefehle nutzen

3. Konfigurationsmanagement

   - Einlesen von `/etc/mower/config.json`
   - Parameterübergabe an `PID`, `map`, `StateEstimator`

4. Loop-Architektur
   - Zeitgesteuerte Periodik (Sensor, Steuerung, Telemetrie, Logging)
   - Error-Handling & Graceful Shutdown bei SIGTERM/SIGINT

---

Diese Datei deckt nun Portierungsschritte und PRD-Anforderungen in einem zentralen TODO ab.
