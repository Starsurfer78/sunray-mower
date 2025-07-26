# Sunray Mähroboter Projekt

Ein autonomer Mähroboter basierend auf dem Sunray-Framework mit Python-Implementierung.

## Projektstruktur

```
sunray/
├── sunray.ino              # Arduino-Hauptprogramm
├── sunray_py/              # Python-Implementierung
│   ├── main.py             # Hauptprogramm
│   ├── motor.py            # Motorsteuerung
│   ├── config.py           # Konfigurationsverwaltung
│   ├── config_example.json # Beispielkonfiguration
│   ├── config.json         # Basis-Konfiguration
│   ├── config_enhanced.json # Enhanced System Konfiguration
│   ├── gps_module.py       # GPS-Funktionalität
│   ├── imu.py              # Inertialsensorik
│   ├── battery.py          # Batterieüberwachung
│   ├── obstacle_detection.py # Hinderniserkennung
│   ├── enhanced_escape_operations.py # 🆕 Enhanced Navigation System
│   ├── integration_example.py # 🆕 Enhanced Sunray Controller
│   ├── mock_hardware.py    # 🆕 Mock Hardware für Entwicklung
│   ├── ENHANCED_NAVIGATION_INTEGRATION.md # 🆕 Enhanced System Dokumentation
│   └── tests/              # Unit-Tests
├── src/                    # C++ Quellcode
└── Pico/                   # Raspberry Pi Pico Code
```

## Features

### Basis-Features
- **Autonome Navigation**: GPS-basierte Pfadplanung und -verfolgung
- **Motorsteuerung**: PID-geregelte Antriebsmotoren und Mähwerk
- **Sicherheitssysteme**: Not-Aus, Hebe- und Neigungssensoren
- **Hinderniserkennung**: Ultraschall- und Bumper-Sensoren
- **Batteriemanagement**: Überwachung und automatisches Laden
- **Web-Interface**: Fernsteuerung und Monitoring
- **MQTT-Integration**: IoT-Konnektivität

### 🚀 Enhanced Navigation System (NEU!)
- **Adaptive Hindernisumgehung**: KI-basierte Escape-Strategien mit maschinellem Lernen
- **Sensorfusion**: Intelligente Kombination von GPS, IMU, Odometrie und Stromdaten
- **Lernfähiges System**: Automatische Verbesserung der Navigation durch Erfahrung
- **HTTP API**: RESTful API für Fernsteuerung und Statusabfrage
- **MQTT Telemetrie**: Echtzeit-Datenübertragung für Monitoring
- **Mock Hardware**: Entwicklung und Tests ohne echte Hardware möglich
- **Konfigurierbare Parameter**: Anpassbare Algorithmus-Parameter

## Installation

### Voraussetzungen

- Python 3.8+
- Arduino IDE (für Hardware-Programmierung)
- Git

### Python-Umgebung einrichten

```bash
cd sunray/sunray_py
pip install -r requirements.txt
```

### Konfiguration

1. Kopiere `config_example.json` zu `config.json`
2. Passe die Konfiguration an deine Hardware an
3. Siehe `CONFIG_README.md` für detaillierte Informationen

## Verwendung

### Standard-Version starten

```bash
cd sunray/sunray_py
python main.py
```

### Enhanced Navigation System starten

```bash
cd sunray/sunray_py
python integration_example.py
```

**Features des Enhanced Systems:**
- Adaptive Hindernisumgehung mit maschinellem Lernen
- HTTP API auf Port 8080 für Fernsteuerung
- MQTT Telemetrie für Echtzeit-Monitoring
- Automatischer Fallback auf Mock-Hardware in Entwicklungsumgebungen

### Tests ausführen

```bash
python -m pytest tests/ -v
```

## Konfiguration

Das System verwendet eine JSON-basierte Konfiguration:

- `config_example.json`: Beispielkonfiguration mit Dokumentation
- `config.json`: Basis-Konfiguration für Standard-System
- `config_enhanced.json`: Erweiterte Konfiguration für Enhanced Navigation System
- `CONFIG_README.md`: Detaillierte Konfigurationsdokumentation
- `ENHANCED_NAVIGATION_INTEGRATION.md`: Enhanced System Dokumentation

### Enhanced System Konfiguration

Das Enhanced Navigation System bietet erweiterte Konfigurationsmöglichkeiten:

```json
{
  "enhanced_escape": {
    "enabled": true,
    "learning_enabled": true,
    "sensor_fusion": {
      "gps_weight": 0.4,
      "imu_weight": 0.3,
      "odometry_weight": 0.2,
      "current_weight": 0.1
    }
  }
}
```

## Hardware

- **Hauptcontroller**: Raspberry Pi
- **Motorcontroller**: Raspberry Pi Pico
- **GPS**: RTK-fähiges Modul
- **IMU**: 9-DOF Inertialsensor
- **Sensoren**: Ultraschall, Bumper, Hebe-/Neigungssensoren

## Entwicklung

### Code-Stil

- Python: PEP 8
- C++: Google Style Guide
- Dokumentation: Docstrings für alle Funktionen

### Testing

- Unit-Tests für alle Module
- Integration-Tests für Hardware-Komponenten
- Kontinuierliche Integration mit pytest

## Beitragen

1. Fork das Repository
2. Erstelle einen Feature-Branch
3. Implementiere deine Änderungen
4. Füge Tests hinzu
5. Erstelle einen Pull Request

## Lizenz

Dieses Projekt steht unter der MIT-Lizenz. Siehe LICENSE-Datei für Details.

## Support

Bei Fragen oder Problemen:

1. Prüfe die Dokumentation in `docs/`
2. Durchsuche die Issues
3. Erstelle ein neues Issue mit detaillierter Beschreibung

## Changelog

Siehe CHANGELOG.md für Versionshistorie und Änderungen.
