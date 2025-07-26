# Motor-Integration in Sunray Python

Diese Dokumentation beschreibt die Integration der Motor-Klasse in das Sunray Python System, basierend auf der Analyse in `MOTOR_PID_ANALYSIS.md`.

## Übersicht

Die Motor-Klasse wurde erfolgreich in das Hauptsystem integriert und bietet folgende Funktionalitäten:

- **PID-Regelung** für Fahrmotor-Geschwindigkeiten
- **Pico-Datenverarbeitung** für Strom- und Odometrie-Werte
- **Überlastungsschutz** mit automatischem Stopp
- **Adaptive Geschwindigkeitsanpassung** basierend auf Motorstrom
- **Mähmotor-Steuerung** mit Fehlererkennnung
- **Integration in MQTT-Telemetrie**

## Implementierte Komponenten

### 1. Motor-Klasse (`motor.py`)

#### Hauptfunktionen:
- `begin()`: Initialisierung der Motor-Hardware
- `update(pico_data)`: Verarbeitung von Pico-Sensordaten
- `run()`: Periodische Steuerungsroutine
- `control()`: PID-Regelung der Motorgeschwindigkeiten

#### Geschwindigkeitssteuerung:
- `set_linear_angular_speed(linear, angular)`: Differential Drive Kinematik
- `enable_traction_motors(enabled)`: Aktivierung/Deaktivierung der Fahrmotoren
- `stop_immediately()`: Notfall-Stopp aller Motoren

#### Mähmotor-Steuerung:
- `set_mow_state(enabled)`: Ein-/Ausschalten des Mähmotors
- `set_mow_pwm(pwm)`: Direkte PWM-Steuerung
- `check_mow_rpm_fault()`: Fehlererkennnung basierend auf Stromfluss

#### Sicherheitsfunktionen:
- `check_overload()`: Überlastungserkennung
- `check_fault()`: Allgemeine Fehlerprüfung
- `adaptive_speed()`: Geschwindigkeitsanpassung bei hohem Strom

### 2. Integration in main.py

#### Initialisierung:
```python
motor = Motor(pico_comm=pico_comm)
motor.begin()
```

#### Hauptschleife:
```python
# Motor-Datenverarbeitung
motor.update(pico_data)
motor.run()

# MQTT-Telemetrie
motor_status = motor.get_status()
payload = {
    # ... andere Daten ...
    "motor_status": motor_status
}
```

#### Notfall-Stopp:
```python
if emergency_stop:
    motor.stop_immediately()
    pico.send_command("AT+STOP")  # Zusätzlicher Fallback
```

### 3. Integration in Operationen (`op.py`)

Die `EscapeForwardOp`-Klasse wurde aktualisiert:

```python
class EscapeForwardOp(Operation):
    def __init__(self, motor=None):
        self.motor = motor
    
    def run(self, robot_state):
        if self.motor:
            self.motor.set_linear_angular_speed(0.3, 0.0)  # Vorwärts
            # ...
            self.motor.set_linear_angular_speed(0.0, 1.0)  # Drehen
        else:
            # Fallback auf direkte Pico-Kommandos
```

## PID-Konfiguration

### Fahrmotor-PIDs (VelocityPID):
- **Kp**: 2.0 (Proportionalverstärkung)
- **Ki**: 0.5 (Integralverstärkung)
- **Kd**: 0.1 (Differentialverstärkung)
- **Output-Limits**: ±255 PWM

### Mähmotor-PID (Standard PID):
- **Kp**: 1.0
- **Ki**: 0.1
- **Kd**: 0.05
- **Output-Limits**: ±255 PWM

## Sicherheitsfeatures

### Überlastungsschutz:
- **Stromgrenzwerte**: 3.0A für Fahrmotoren, 4.0A für Mähmotor
- **Überlastungszähler**: Automatischer Stopp nach 5 aufeinanderfolgenden Überlastungen
- **Adaptive Geschwindigkeit**: Reduzierung bei hohem Durchschnittsstrom

### Fehlererkennnung:
- **Mähmotor-Überwachung**: Erkennung von Blockierungen durch Stromanalyse
- **Odometrie-Validierung**: Prüfung auf unrealistische Sprünge
- **Hardware-Fehler**: Integration von Pico-Fehlermeldungen

## MQTT-Telemetrie

Der Motor-Status wird in die MQTT-Telemetrie integriert:

```json
{
  "motor_status": {
    "enabled": true,
    "target_linear_speed": 0.5,
    "target_angular_speed": 0.0,
    "current_left_speed": 0.48,
    "current_right_speed": 0.52,
    "current_left_current": 1.2,
    "current_right_current": 1.3,
    "current_mow_current": 2.1,
    "mow_enabled": true,
    "overload_detected": false,
    "fault_detected": false
  }
}
```

## Tests

Umfassende Integrationstests in `tests/test_motor_integration.py`:

- ✅ Motor-Initialisierung
- ✅ Pico-Datenverarbeitung
- ✅ Überlastungserkennung und -schutz
- ✅ Geschwindigkeitssteuerung
- ✅ Mähmotor-Steuerung
- ✅ Notfall-Stopp
- ✅ PID-Regelung
- ✅ Adaptive Geschwindigkeitsanpassung
- ✅ Fehlererkennnung
- ✅ Funktionalität ohne Pico-Kommunikation

## Verwendung

### Grundlegende Motorsteuerung:
```python
# Motor initialisieren
motor = Motor(pico_comm=pico_comm)
motor.begin()

# Fahrmotoren aktivieren
motor.enable_traction_motors(True)

# Geschwindigkeit setzen (linear: 0.5 m/s, angular: 0.2 rad/s)
motor.set_linear_angular_speed(0.5, 0.2)

# Mähmotor einschalten
motor.set_mow_state(True)

# In Hauptschleife:
motor.update(pico_data)  # Sensordaten verarbeiten
motor.run()              # Regelung ausführen

# Notfall-Stopp
motor.stop_immediately()
```

### Status abfragen:
```python
status = motor.get_status()
print(f"Motor enabled: {status['enabled']}")
print(f"Current speed: {status['current_left_speed']:.2f} m/s")
print(f"Overload: {status['overload_detected']}")
```

## Nächste Schritte

1. **Kalibrierung**: Feinabstimmung der PID-Parameter basierend auf realen Tests
2. **Erweiterte Telemetrie**: Zusätzliche Metriken für Performance-Monitoring
3. **Adaptive Algorithmen**: Verbesserung der adaptiven Geschwindigkeitsanpassung
4. **Weitere Operationen**: Integration in andere Operation-Klassen
5. **Logging**: Detailliertes Logging für Debugging und Analyse

## Fazit

Die Motor-Integration ist erfolgreich abgeschlossen und bietet:
- Robuste PID-Regelung für präzise Geschwindigkeitssteuerung
- Umfassende Sicherheitsfeatures mit Überlastungsschutz
- Nahtlose Integration in das bestehende Sunray-System
- Vollständige Testabdeckung für Zuverlässigkeit
- Flexible Architektur für zukünftige Erweiterungen