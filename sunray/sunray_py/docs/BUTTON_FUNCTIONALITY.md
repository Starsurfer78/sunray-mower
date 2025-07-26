# Erweiterte Button-Funktionalität für Sunray Python Mähroboter

Dieses Dokument beschreibt die implementierte erweiterte Button-Funktionalität, die verschiedene Aktionen basierend auf Druckdauer und aktuellem Roboterzustand ausführt.

## Übersicht

Der Sunray Python Mähroboter verfügt über einen intelligenten Button-Controller, der kontextabhängige Aktionen basierend auf:
- **Druckdauer** (kurz/mittel/lang)
- **Aktuellem Roboterzustand** (IDLE, MOWING, DOCKING, etc.)
- **Verfügbaren Karten und Zonen**
- **Batteriezustand**

ausführt.

## Button-Aktionen

### 1. Kurzer Druck (< 1 Sekunde)
**Kontextabhängige Start/Stop-Funktion**

#### Im IDLE-Modus:
- ✅ **Startet Mähvorgang**, wenn:
  - Karte geladen ist
  - Batteriestand > 20%
  - Roboter betriebsbereit
- ❌ **Keine Aktion**, wenn Voraussetzungen nicht erfüllt

#### Während Mähvorgang:
- 🛑 **Stoppt Mähvorgang** sofort
- Motoren werden abgeschaltet
- Roboter wechselt in IDLE-Modus

#### In anderen Zuständen:
- **ESCAPE/GPS_RECOVERY**: Stoppt aktuelle Operation
- **DOCKING/CHARGING**: Startet Mähvorgang (wenn Batterie > 80% und Karte verfügbar)
- **ERROR**: Versucht Reset/Emergency Stop

### 2. Mittlerer Druck (1-5 Sekunden)
**Notfall-Stopp**

- 🚨 **Emergency Stop** aller Motoren
- Sofortiger Stopp aller Bewegungen
- Wechsel in sicheren Zustand
- Geeignet für Notfälle und unerwartete Situationen

### 3. Langer Druck (≥ 5 Sekunden)
**GoHome/Docking-Vorgang**

- 🏠 **Startet Docking-Vorgang** zur Ladestation
- Roboter navigiert automatisch zur Ladestation
- **Pieptöne während Druck**:
  - Jede Sekunde ein Piepton (1-4 Sekunden)
  - Bei 5 Sekunden: Bestätigungston für GoHome-Aktivierung

## Buzzer-Feedback

Der Button-Controller bietet akustisches Feedback für bessere Benutzerinteraktion:

### Sofortiges Feedback:
- **Button gedrückt**: Kurzer Bestätigungston (1kHz, 100ms)

### Während langem Druck:
- **1-4 Sekunden**: Piepton jede Sekunde (1.5kHz, 200ms)
- **5 Sekunden**: GoHome-Aktivierungston (1.8kHz, 400ms)

### Aktions-Bestätigung:
- **Mähvorgang gestartet**: Doppelton (800Hz, 300ms, 2x)
- **Mähvorgang gestoppt**: Einzelton (600Hz, 500ms)
- **GoHome aktiviert**: Dreifachton (1.8kHz, 400ms, 3x)
- **Notfall-Stopp**: Alarmton (2.5kHz, 1000ms, 3x)
- **Fehler**: Tiefer Ton (300Hz, 800ms, 2x)

## Hardware-Integration

### Pico-Seite (E:\VibeCoding\sunray\Pico\1.0\main.py)

```python
# Button-Zustandsverfolgung
stopButtonPressed = False
stopButtonPressTime = 0
lastBuzzerTime = 0
buzzerBeepCount = 0
LONG_PRESS_DURATION = 5000  # 5 Sekunden
BEEP_INTERVAL = 1000  # 1 Sekunde zwischen Pieptönen

# Erweiterte Button-Verarbeitung in readSensors()
# - Erkennt Button-Zustandsänderungen
# - Misst Druckdauer
# - Sendet Pieptöne während langem Druck
# - Überträgt Button-Aktionen an Haupteinheit
```

### Python-Seite (E:\VibeCoding\sunray\sunray_py\)

```python
# Smart Button Controller
from smart_button_controller import SmartButtonController, ButtonAction

# Initialisierung
button_controller = SmartButtonController(
    motor=motor,
    state_estimator=estimator,
    hardware_manager=hardware_manager
)

# Callback-Registrierung
button_controller.set_action_callback(ButtonAction.START_MOW, start_mowing_action)
button_controller.set_action_callback(ButtonAction.STOP_MOW, stop_mowing_action)
button_controller.set_action_callback(ButtonAction.GO_HOME, go_home_action)
button_controller.set_action_callback(ButtonAction.EMERGENCY_STOP, emergency_stop_action)
```

## Web-API Integration

Die Button-Funktionalität ist vollständig in die Web-API integriert:

### Verfügbare Endpunkte:

#### `GET /button/status`
Gibt aktuellen Button-Controller-Status zurück:
```json
{
  "status": "success",
  "button_controller": {
    "button_pressed": false,
    "current_robot_state": "idle",
    "has_map_loaded": true,
    "battery_level": 85.5,
    "is_docked": false
  }
}
```

#### `POST /button/simulate`
Simuliert Button-Druck für Tests:
```json
{
  "duration": 2.5
}
```

Antwort:
```json
{
  "status": "success",
  "simulated_duration": 2.5,
  "executed_action": "emergency_stop",
  "message": "Button-Druck (2.5s) simuliert -> emergency_stop"
}
```

#### `GET /button/actions`
Listet verfügbare Button-Aktionen auf:
```json
{
  "status": "success",
  "available_actions": {
    "short_press": {
      "duration": "< 1 second",
      "action": "START_MOW or STOP_MOW (context dependent)",
      "description": "Startet/stoppt Mähvorgang je nach aktuellem Zustand"
    },
    "medium_press": {
      "duration": "1-5 seconds",
      "action": "EMERGENCY_STOP",
      "description": "Notfall-Stopp aller Motoren"
    },
    "long_press": {
      "duration": "≥ 5 seconds",
      "action": "GO_HOME",
      "description": "Startet Docking-Vorgang zur Ladestation"
    }
  }
}
```

#### `GET/POST /button/config`
Konfiguration des Button-Controllers:
```json
{
  "short_press_max_duration": 1.0,
  "long_press_duration": 5.0,
  "beep_interval": 1.0,
  "button_debounce_time": 0.05
}
```

## Sicherheitsfeatures

### Entprellung
- **Debounce-Zeit**: 50ms zur Vermeidung von Fehlauslösungen
- **Mindestabstand**: Verhindert zu schnelle aufeinanderfolgende Aktionen

### Zustandsvalidierung
- **Batterieprüfung**: Mähvorgang nur bei ausreichender Batterie
- **Kartenprüfung**: Start nur mit geladener Karte
- **Zustandsabhängigkeit**: Aktionen abhängig vom aktuellen Roboterzustand

### Fehlerbehandlung
- **Callback-Fehler**: Abfangen und Logging von Callback-Fehlern
- **Hardware-Fehler**: Graceful Degradation bei Hardware-Problemen
- **Timeout-Schutz**: Vermeidung von hängenden Operationen

## Konfiguration

### Timing-Parameter
```python
self.short_press_max_duration = 1.0  # Sekunden
self.long_press_duration = 5.0       # Sekunden
self.beep_interval = 1.0             # Sekunden
self.button_debounce_time = 0.05     # Sekunden
```

### Buzzer-Konfiguration
```python
# Pico-Seite
LONG_PRESS_DURATION = 5000  # Millisekunden
BEEP_INTERVAL = 1000        # Millisekunden
```

## Verwendung

### Grundlegende Bedienung
1. **Mähen starten**: Kurz drücken im IDLE-Modus
2. **Mähen stoppen**: Kurz drücken während Mähvorgang
3. **Notfall-Stopp**: 2-3 Sekunden drücken
4. **Nach Hause**: 5+ Sekunden drücken (mit Pieptönen)

### Erweiterte Funktionen
- **Web-Interface**: Vollständige Kontrolle über Browser
- **API-Integration**: Programmatische Steuerung
- **Simulation**: Testen ohne physischen Button
- **Konfiguration**: Anpassung der Timing-Parameter

## Troubleshooting

### Häufige Probleme

#### Button reagiert nicht
- Prüfen Sie die Hardware-Verbindung (Pin 21)
- Überprüfen Sie die Entprellung-Einstellungen
- Kontrollieren Sie die UART-Kommunikation

#### Falsche Aktionen
- Überprüfen Sie die Druckdauer-Konfiguration
- Validieren Sie den aktuellen Roboterzustand
- Prüfen Sie die Callback-Registrierung

#### Kein Buzzer-Feedback
- Überprüfen Sie die Hardware-Manager-Verbindung
- Kontrollieren Sie die Buzzer-Hardware
- Prüfen Sie die Lautstärke-Einstellungen

### Debug-Informationen

```python
# Status abrufen
status = button_controller.get_status()
print(f"Button Status: {status}")

# Simulation für Tests
action = button_controller.simulate_button_press(2.5)
print(f"Simulierte Aktion: {action.value}")

# Buzzer-Statistiken
buzzer_stats = buzzer_feedback.get_statistics()
print(f"Buzzer Stats: {buzzer_stats}")
```

## Erweiterungsmöglichkeiten

### Zukünftige Features
- **Multi-Button-Support**: Unterstützung für mehrere Buttons
- **Gestenerkennung**: Komplexere Button-Sequenzen
- **Adaptive Timing**: Lernende Druckdauer-Anpassung
- **Sprachfeedback**: Zusätzlich zum Buzzer-Feedback
- **Mobile App**: Smartphone-Integration

### Anpassungen
- **Neue Aktionen**: Einfache Erweiterung um weitere ButtonActions
- **Timing-Anpassung**: Konfigurierbare Druckdauer-Schwellen
- **Zustandslogik**: Erweiterte kontextabhängige Aktionen
- **Hardware-Integration**: Support für verschiedene Button-Typen

## Fazit

Die erweiterte Button-Funktionalität bietet eine intuitive und sichere Bedienung des Sunray Python Mähroboters. Durch die kontextabhängigen Aktionen, das akustische Feedback und die vollständige API-Integration wird eine professionelle Benutzererfahrung gewährleistet.

Die modulare Architektur ermöglicht einfache Erweiterungen und Anpassungen für spezifische Anforderungen.