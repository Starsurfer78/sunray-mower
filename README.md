# Sunray Mähroboter Projekt

> **Basierend auf dem ursprünglichen [Ardumower Sunray Projekt](https://github.com/Ardumower/Sunray)**  
> Copyright (c) 2013-2020 by Alexander Grau, Grau GmbH  
> Lizenziert unter GPL-3.0 - siehe [Forum](https://www.ardumower.de/forum/threads/ardumower-sunray.20426/) für Details

Ein autonomer Mähroboter basierend auf dem Sunray-Framework mit Python-Implementierung.

## 🏆 Projektattribution

Dieses Projekt baut auf dem hervorragenden **Ardumower Sunray Projekt** auf, das von Alexander Grau und der Grau GmbH entwickelt wurde. Alle Dateien enthalten entsprechende Header-Kommentare, die das ursprüngliche Projekt würdigen und die GPL-3.0 Lizenz respektieren.

- **Original Projekt**: [Ardumower Sunray auf GitHub](https://github.com/Ardumower/Sunray)
- **Community Forum**: [Ardumower Forum](https://www.ardumower.de/forum/threads/ardumower-sunray.20426/)
- **Lizenz**: GPL-3.0
- **Copyright**: Alexander Grau, Grau GmbH (2013-2020)

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
│   ├── buzzer_feedback.py  # 🆕 Buzzer-Feedback-System
│   ├── buzzer_example.py   # 🆕 Buzzer-Beispiele und Demo
│   ├── web_server.py       # 🆕 HTTP/API Server
│   ├── static/             # 🆕 Web-Interface Dateien
│   │   ├── index.html      # Startseite (Weiterleitung)
│   │   ├── dashboard_modular.html # 🆕 Hauptdashboard
│   │   ├── gps_mapping.html # 🆕 GPS-Kartenerstellung mit Hindernissen
│   │   ├── path_planning.html # 🆕 Intelligente Pfadplanung
│   │   ├── map_editor.html # Kartenverwaltung (Legacy)
│   │   └── css/
│   │       └── styles.css  # 🆕 Moderne CSS-Styles
│   ├── ENHANCED_NAVIGATION_INTEGRATION.md # 🆕 Enhanced System Dokumentation
│   ├── BUZZER_FEEDBACK_DOCUMENTATION.md # 🆕 Buzzer-System Dokumentation
│   └── tests/              # Unit-Tests
├── src/                    # C++ Quellcode
└── Pico/                   # Raspberry Pi Pico Code
```

## 🚀 Neueste Updates

### Version 2024.2 - GPS-Kartenerstellung und Pfadplanung
- ✅ **GPS-Kartenerstellung**: Vollständig neue Seite für interaktive Kartenerstellung mit GPS-Punkten
- ✅ **Hindernismanagement**: Einzeichnen und Verwaltung von Hindernissen nach Kartenerstellung
- ✅ **Intelligente Pfadplanung**: Verschiedene Mähbild-Algorithmen (Parallel, Spiral, Zickzack, Zufällig)
- ✅ **Echtzeit-Vorschau**: Live-Visualisierung von Pfaden mit detaillierten Statistiken
- ✅ **Docking-Integration**: Automatische Pfadplanung zur Ladestation
- ✅ **Modulares Web-Interface**: Saubere Navigation zwischen Dashboard, Kartenerstellung und Pfadplanung
- ✅ **Responsive Design**: Optimiert für Desktop und mobile Geräte

### Version 2024.1 - Header Attribution Update
- ✅ **Projektattribution**: Alle Dateien enthalten Header-Kommentare mit Verweis auf das ursprüngliche Ardumower Sunray Projekt
- ✅ **Lizenz-Compliance**: GPL-3.0 Lizenzinformationen in allen Quelldateien
- ✅ **Copyright-Würdigung**: Angemessene Anerkennung von Alexander Grau und Grau GmbH

### Commit-Historie
- `🗺️ Add comprehensive GPS mapping and path planning system with obstacle support` - Neue Kartenerstellungs- und Pfadplanungsfunktionen
- `📄 Add Ardumower Sunray project attribution headers to all files` - Vollständige Header-Attribution

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

### 🔊 Buzzer-Feedback-System (NEU!)
- **Akustisches Feedback**: Töne für System-, Navigations- und Warnereignisse
- **Event-basierte Steuerung**: Automatische Tonwiedergabe bei verschiedenen Ereignissen
- **Enhanced System Integration**: Spezielle Töne für Enhanced Escape Operationen
- **Ton-Sequenzen**: Komplexe Melodien für verschiedene Systemzustände
- **Mock-Hardware-Unterstützung**: Entwicklung ohne echten Buzzer möglich
- **Konfigurierbare Töne**: Anpassbare Frequenzen und Dauern

### 🌐 GPS-Kartenerstellung und Pfadplanung (NEU!)
- **GPS-basierte Kartenerstellung**: Interaktive Erstellung von Mähflächen mit GPS-Punkten
- **Hindernismanagement**: Einzeichnen und Verwaltung von Hindernissen auf der Karte
- **Intelligente Pfadplanung**: Verschiedene Mähbild-Algorithmen (Parallel, Spiral, Zickzack, Zufällig)
- **Echtzeit-Vorschau**: Live-Visualisierung von Pfaden mit Statistiken
- **Docking-Station Integration**: Automatische Pfadplanung zur Ladestation
- **Responsive Web-Interface**: Optimiert für Desktop und mobile Geräte
- **Modulares Design**: Saubere Trennung von Kartenerstellung und Pfadplanung

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
- Integriertes Buzzer-Feedback für alle Systemereignisse

### Buzzer-Feedback-System testen

```bash
cd sunray/sunray_py
python buzzer_example.py
```

**Buzzer-Features:**
- System-Töne (Start, Bereit, Shutdown, Fehler)
- Navigations-Töne (Start, Abschluss, Hindernis erkannt)
- Warn-Töne (Batterie schwach, Motor überlastet, Neigungswarnung)
- Enhanced System Töne (Escape Start/Erfolg/Fehler, Learning Updates)

### Tests ausführen

```bash
python -m pytest tests/ -v
```

### Web-Interface verwenden

Das GPS-Kartenerstellungs- und Pfadplanungssystem ist über den integrierten Web-Server erreichbar:

```bash
# Web-Server starten
cd sunray/sunray_py
python web_server.py
```

**Verfügbare Seiten:**
- **Dashboard** (`http://localhost:5000/static/dashboard_modular.html`): Hauptübersicht mit Systemstatus und Navigation
- **GPS-Kartenerstellung** (`http://localhost:5000/static/gps_mapping.html`): Interaktive Kartenerstellung mit GPS-Punkten und Hindernissen
- **Pfadplanung** (`http://localhost:5000/static/path_planning.html`): Intelligente Mähbild-Erstellung mit verschiedenen Algorithmen

**GPS-Kartenerstellung Features:**
- Sammeln von GPS-Grenzpunkten für Mähflächen
- Automatisches Abschließen von Flächen ab 3 Punkten
- Hinzufügen von Docking-Pfaden zur Ladestation
- Einzeichnen von Hindernissen nach Kartenerstellung
- Echtzeit-GPS-Simulation für Entwicklung
- Speichern und Laden von Karten

**Pfadplanung Features:**
- Auswahl verschiedener Mähbild-Algorithmen (Parallel, Spiral, Zickzack, Zufällig)
- Konfigurierbare Parameter (Schnittbreite, Überlappung, Geschwindigkeit, Richtung)
- Echtzeit-Vorschau mit Statistiken (Pfadlänge, geschätzte Zeit, Abdeckung, Effizienz)
- Speichern als Tasks oder Zonen
- Laden auf Roboter-Hardware

**Technische Features:**
- Responsive Design für Desktop und mobile Geräte
- Canvas-basierte Kartendarstellung
- Modulare Navigation zwischen allen Bereichen
- API-Integration für Datenübertragung

## Konfiguration

Das System verwendet eine JSON-basierte Konfiguration:

- `config_example.json`: Beispielkonfiguration mit Dokumentation
- `config.json`: Basis-Konfiguration für Standard-System
- `config_enhanced.json`: Erweiterte Konfiguration für Enhanced Navigation System
- `CONFIG_README.md`: Detaillierte Konfigurationsdokumentation
- `ENHANCED_NAVIGATION_INTEGRATION.md`: Enhanced System Dokumentation
- `BUZZER_FEEDBACK_DOCUMENTATION.md`: Buzzer-System Dokumentation

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
  },
  "buzzer": {
    "enabled": true,
    "system_events": true,
    "navigation_events": true,
    "warning_events": true,
    "enhanced_events": true
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

## 🤝 Beitragen

### Entwicklungsrichtlinien

1. **Fork das Repository** von [GitHub](https://github.com/Starsurfer78/sunray-mower)
2. **Erstelle einen Feature-Branch** (`git checkout -b feature/amazing-feature`)
3. **Implementiere deine Änderungen** unter Beachtung der Code-Stil-Richtlinien
4. **Füge Tests hinzu** für neue Funktionalität
5. **Commit deine Änderungen** (`git commit -m 'Add amazing feature'`)
6. **Push zum Branch** (`git push origin feature/amazing-feature`)
7. **Erstelle einen Pull Request**

### Code-Qualität

- **Header-Attribution**: Alle neuen Dateien müssen entsprechende Header-Kommentare enthalten
- **Lizenz-Compliance**: Einhaltung der GPL-3.0 Lizenzbestimmungen
- **Dokumentation**: Vollständige Dokumentation für neue Features
- **Tests**: Unit-Tests für alle neuen Funktionen
- **Code-Review**: Alle Änderungen durchlaufen ein Review-Verfahren

### Repository-Informationen

- **GitHub Repository**: [https://github.com/Starsurfer78/sunray-mower](https://github.com/Starsurfer78/sunray-mower)
- **Hauptbranch**: `master`
- **Issue-Tracking**: GitHub Issues für Bugs und Feature-Requests
- **Continuous Integration**: Automatische Tests bei Pull Requests

## 📋 Lizenz und Rechtliches

Dieses Projekt basiert auf dem **Ardumower Sunray Projekt** und steht unter der **GPL-3.0 Lizenz**.

- **Lizenz**: GNU General Public License v3.0
- **Original Copyright**: Alexander Grau, Grau GmbH (2013-2020)
- **Projekt-Erweiterungen**: Unter derselben GPL-3.0 Lizenz
- **Quellcode-Verfügbarkeit**: Vollständig Open Source

### Lizenz-Compliance

Alle Dateien in diesem Projekt enthalten entsprechende Header-Kommentare mit:
- Verweis auf das ursprüngliche Ardumower Sunray Projekt
- Copyright-Hinweise für Alexander Grau und Grau GmbH
- GPL-3.0 Lizenzinformationen
- Links zu Forum und GitHub des Originalprojekts

### Respektvolle Nutzung

Bei der Nutzung dieses Projekts bitten wir um:
- Anerkennung des ursprünglichen Ardumower Sunray Projekts
- Einhaltung der GPL-3.0 Lizenzbestimmungen
- Respekt vor der Arbeit von Alexander Grau und der Community

## Support

Bei Fragen oder Problemen:

1. Prüfe die Dokumentation in `docs/`
2. Durchsuche die Issues
3. Erstelle ein neues Issue mit detaillierter Beschreibung

## Changelog

Siehe CHANGELOG.md für Versionshistorie und Änderungen.