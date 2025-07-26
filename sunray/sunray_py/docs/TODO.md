# TODO: Sunray-Firmware Portierung nach Python

## Priorisierte Module

1. **Batteriemanagement** (portiert)
   - `battery.cpp` / `Battery` → `battery.py` / `Battery`
   - Methoden: begin, enable_charging, run, charger_connected, is_docked, should_go_home, under_voltage, is_charging_completed
2. **Motorsteuerung & PID-Regler** (portiert)
   - `motor.cpp` / `Motor` → `motor.py` / `Motor`
   - `pid.cpp` / `PID`, `VelocityPID` → `pid.py` / `PID`, `VelocityPID`
   - Methoden: begin, run, test, plot, enable_traction_motors, set_linear_angular_speed, set_mow_state, set_mow_pwm, wait_mow_motor, stop_immediately, speed_pwm, control, check_fault, check_overload, check_odometry_error, check_mow_rpm_fault, drvfix, check_motor_mow_stall, adaptive_speed, change_speed_set, sense, dump_odo_ticks; reset, compute
3. **Kartierung (Map)** (portiert)
   - `map.cpp` / `Map`, `Point`, `Polygon`, `PathFinder` → `map.py` / `Map`, `Point`, `Polygon`, `PolygonList`, `Node`, `NodeList`
   - Funktionen: begin, clear, set_point, save, load; Platzhalter: find_path, next_mow_point
4. **Kommunikation (kommando-basiert)** (portiert)
   - `comm.cpp` / `processCmd`, `cmd*` → `comm.py` / `CommParser`
   - Methoden: process_line, \_compute_crc, \_answer
5. **Sensor-Filter & Utilities** (portiert)
   - `lowpass_filter.cpp` / `LowPassFilter` → `lowpass_filter.py` / `LowPassFilter`
   - `RunningMedian.cpp` / `RunningMedian` → `running_median.py` / `RunningMedian`
   - `helper.cpp` / Utility-Funktionen → `helper.py`
6. **State Estimation & Operations** (teilportiert)
   - `StateEstimator.cpp` → `state_estimator.py` / `StateEstimator`
   - `src/op` Operationen (MowOp, DockOp, IdleOp, EscapeOps) → noch offen
7. **Ereignis-Logging & Storage** (portiert)
   - `events.cpp` / `EventLogger` → `events.py` / `EventLogger`, `EventCode`
   - `Storage.cpp` / `Storage`, `Stats` → `storage.py` / `Storage`; `stats.py` / `Stats`, `OperationType`
8. **Kommunikationsschnittstellen**
   - MQTT (`mqtt.cpp`), HTTP-Server (`httpserver.cpp`), CAN (`can.h`), BLE (`ble.cpp`)
9. **Tests & Validierung**
   - Unittests aus `src/test` nach Python übertragen / pytest-Suite

## Nächste Schritte

- Für jedes Modul:
  1. Python-Schnittstellen entwerfen (Klassen + Methoden)
  2. Dependencies prüfen (Libraries, GPIO, I2C, Serial)
  3. Implementierung in `sunray_py/` – Moduldateien anlegen
  4. Unit-Tests schreiben (pytest)
- CI-Umgebung aufsetzen: `pytest`, Linter, Flake8
- Dokumentation aktualisieren (README, API-Referenz)
