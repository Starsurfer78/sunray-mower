# Sunray Test Suite

Dieser Ordner enthält alle Testskripte für den Sunray-Python-Port.

## Struktur

- `test_bumper.py` - Tests für die Bumper-Funktionalität
- `__init__.py` - Python-Paket-Initialisierung

## Tests ausführen

### Einzelne Tests

```bash
# Bumper-Tests
python tests/test_bumper.py
```

### Alle Tests (zukünftig)

```bash
# Mit pytest (wenn installiert)
pytest tests/

# Oder manuell
python -m tests
```

## Neue Tests hinzufügen

1. Erstelle eine neue Datei mit dem Präfix `test_`
2. Implementiere Testfunktionen
3. Dokumentiere den Test in dieser README

## Test-Kategorien

### Hardware-Tests
- `test_bumper.py` - Test der Bumper-Funktionalität mit Bitmask und Debouncing
- `test_battery_integration.py` - Test der Battery-Klasse Integration mit Pico-Daten

### Geplante Tests
- `test_imu.py` - IMU-Sensordaten und Kalibrierung
- `test_gps.py` - GPS/RTK-Funktionalität
- `test_map.py` - Kartenerstellung und Zonenmanagement
- `test_state_estimator.py` - Zustandsschätzung
- `test_storage.py` - Persistierung
- `test_mqtt.py` - MQTT-Kommunikation
- `test_http_server.py` - Web-API
- `test_motor_pid.py` - Motor- und PID-Integration (nach Implementierung)

### Integration-Tests
- `test_battery_integration.py` - Überprüft Batteriedatenverarbeitung vom Pico
- `test_integration.py` - End-to-End Tests
- `test_pico_comm.py` - Kommunikation mit Pico

## Testdaten

Testdaten sollten in einem separaten `test_data/` Unterordner gespeichert werden.