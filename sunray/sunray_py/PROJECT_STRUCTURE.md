# Sunray Python - Projektstruktur

Dieses Dokument beschreibt die organisierte Struktur des Sunray Python Mähroboter-Projekts nach der Aufräumung.

## 📁 Hauptverzeichnis-Struktur

```
sunray_py/
├── 📋 Dokumentation
│   ├── BUTTON_FUNCTIONALITY.md
│   ├── BUZZER_FEEDBACK_DOCUMENTATION.md
│   ├── CONFIG_README.md
│   ├── ENHANCED_NAVIGATION_INTEGRATION.md
│   ├── README_ENHANCED_ESCAPE.md
│   └── TODO.md
│
├── 🔧 Kern-Module
│   ├── main.py                    # Hauptprogramm
│   ├── motor.py                   # Motorsteuerung
│   ├── imu.py                     # IMU-Sensor
│   ├── gps_module.py             # GPS-Modul
│   ├── rtk_gps.py                # RTK-GPS
│   ├── battery.py                # Batteriemanagement
│   ├── obstacle_detection.py     # Hinderniserkennung
│   ├── path_planner.py           # Pfadplanung
│   ├── state_estimator.py        # Zustandsschätzung
│   └── map.py                    # Kartenfunktionen
│
├── 🎛️ Steuerung & Interface
│   ├── smart_button_controller.py # Button-Steuerung
│   ├── buzzer_feedback.py        # Akustisches Feedback
│   ├── http_server.py            # Web-Interface
│   ├── mqtt_client.py            # MQTT-Kommunikation
│   └── events.py                 # Event-System
│
├── 🔗 Kommunikation
│   ├── pico_comm.py              # Pico-Kommunikation
│   ├── ble_client.py             # Bluetooth
│   ├── can_client.py             # CAN-Bus
│   └── comm.py                   # Allgemeine Kommunikation
│
├── 🛠️ Hilfsfunktionen
│   ├── config.py                 # Konfigurationssystem
│   ├── hardware_manager.py       # Hardware-Management
│   ├── mock_hardware.py          # Mock-Hardware für Tests
│   ├── helper.py                 # Hilfsfunktionen
│   ├── storage.py                # Datenspeicherung
│   ├── stats.py                  # Statistiken
│   ├── pid.py                    # PID-Regler
│   ├── lowpass_filter.py         # Filter
│   └── running_median.py         # Median-Filter
│
├── 🚀 Erweiterte Funktionen
│   ├── enhanced_escape_operations.py # Intelligente Ausweichmanöver
│   └── op.py                     # Operationen
│
├── 📂 Organisierte Unterordner
│   ├── examples/                 # Beispielskripte
│   ├── tests/                    # Test-Suite
│   ├── docs/                     # Detaillierte Dokumentation
│   └── lift_detection/           # Lift-Erkennungssystem
│
└── ⚙️ Konfiguration
    ├── config_example.json        # Beispielkonfiguration
    ├── requirements.txt           # Python-Abhängigkeiten
    └── __init__.py               # Python-Paket
```

## 📂 Unterordner im Detail

### 🎯 `examples/`
Demonstrationen und Beispielskripte:
- `buzzer_example.py` - Buzzer-Feedback-Demo
- `integration_example.py` - System-Integration
- `example_autonomous_mowing.py` - Autonomes Mähen
- `README.md` - Dokumentation der Beispiele

### 🧪 `tests/`
Test-Suite für alle Komponenten:
- `test_button_functionality.py` - Button-Tests
- `test_config_example.py` - Konfigurations-Tests
- `test_path_planning.py` - Pfadplanungs-Tests
- `test_smart_bumper_escape.py` - Escape-Tests
- Weitere Hardware- und Integrationstests

### 📚 `docs/`
Detaillierte technische Dokumentation:
- `MOTOR_CONFIG.md` - Motor-Konfiguration
- `MOTOR_INTEGRATION.md` - Motor-Integration
- `analysis/` - Systemanalysen
- `implementation/` - Implementierungsdetails
- `project/` - Projektdokumentation

### 🔍 `lift_detection/`
Alternative Lift-Erkennungssysteme:
- `lift_detection_alternatives.py` - Hauptalgorithmus
- `integration_lift_alternatives.py` - Systemintegration
- `README.md` - Vollständige Dokumentation

## 🎯 Vorteile der neuen Struktur

### ✅ **Übersichtlichkeit**
- Klare Trennung von Kern-Code, Tests und Beispielen
- Logische Gruppierung verwandter Funktionen
- Reduzierte Unordnung im Hauptverzeichnis

### ✅ **Wartbarkeit**
- Einfachere Navigation und Dateifindung
- Bessere Versionskontrolle durch organisierte Struktur
- Klare Abhängigkeiten zwischen Modulen

### ✅ **Entwicklerfreundlichkeit**
- Separate Bereiche für verschiedene Entwicklungsaktivitäten
- Einfache Integration neuer Features
- Bessere Testorganisation

### ✅ **Dokumentation**
- Zentrale Dokumentation mit klarer Struktur
- Beispiele und Tests als lebende Dokumentation
- Spezielle Bereiche für erweiterte Features

## ⚙️ IDE-Konfiguration (.vscode/)

Für eine optimale Entwicklungsumgebung:
- **settings.json** - VS Code Projekteinstellungen mit Python-Pfaden
- **launch.json** - Debug-Konfigurationen für verschiedene Anwendungsteile
- **tasks.json** - Automatisierte Tasks (Tests, Linting, Formatierung)
- **.gitignore** - Git-Ignore-Konfiguration für temporäre Dateien

## 🚀 Nächste Schritte

1. **Import-Pfade aktualisieren**: Prüfen Sie alle Import-Statements in bestehenden Skripten
2. **IDE-Konfiguration**: Passen Sie Ihre IDE-Einstellungen an die neue Struktur an
3. **CI/CD-Pipeline**: Aktualisieren Sie Testpfade in automatisierten Builds
4. **Dokumentation**: Halten Sie diese Struktur bei zukünftigen Entwicklungen bei

## 📞 Support

Bei Fragen zur neuen Projektstruktur:
- Konsultieren Sie die README-Dateien in den jeweiligen Unterordnern
- Prüfen Sie die Beispielskripte für Verwendungsmuster
- Nutzen Sie die Test-Suite als Referenz für korrekte Integration