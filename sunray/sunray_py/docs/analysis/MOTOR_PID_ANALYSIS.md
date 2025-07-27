# Motor und PID Klassen - Aktuelle Implementierung

## Übersicht

Die Motor- und PID-Klassen sind **vollständig implementiert** und in das Sunray-System integriert. Dieses Dokument beschreibt den aktuellen Stand der Implementierung.

## Aktuelle Implementierung

### Motor-Klasse (hardware/motor.py)
- **Status**: ✅ Vollständig implementiert (1292 Zeilen Code)
- **Verwendung in main.py**: ✅ Importiert und aktiv verwendet
- **Pico-Integration**: ✅ Vollständige Datenverarbeitung implementiert
- **Funktionalität**: ✅ Alle Kernfunktionen verfügbar

### PID-Klassen (utils/pid.py)
- **Status**: ✅ Vollständig implementiert
- **Verwendung**: ✅ Aktiv in Motor-Klasse verwendet
- **Typen**: PID (Standard) und VelocityPID (Geschwindigkeitsregelung)
- **Integration**: ✅ Für alle Motoren konfiguriert

## Pico-Datenintegration

### Verarbeitete Sensordaten

Die Motor-Klasse verarbeitet folgende Pico-Daten über die `update()` Methode:

```python
# Stromdaten für Überlastungsschutz
{
    "motor_left_current": float,    # Linker Motorstrom (A)
    "motor_right_current": float,   # Rechter Motorstrom (A)
    "mow_current": float,           # Mähmotorstrom (A)
    "motor_overload": int,          # Überlastungsflag (0/1)
}

# Odometrie-Daten für Geschwindigkeitsmessung
{
    "odom_left": int,               # Linke Odometrie-Ticks
    "odom_right": int,              # Rechte Odometrie-Ticks
    "odom_mow": int,                # Mähmotor-Odometrie-Ticks
}
```

### Datenverarbeitung in main.py

```python
# Regelmäßige Datenabfrage
hardware_manager.send_command("AT+S,1")  # Summary-Daten anfordern
sensor_data = hardware_manager.get_sensor_data()
pico_data = process_pico_data(sensor_data)

# Motor-Update mit Pico-Daten
motor_status = motor.update(pico_data)
motor.run()  # PID-Regelung ausführen
```

## Implementierte Funktionen

### 1. PID-basierte Geschwindigkeitsregelung

```python
# Separate PID-Regler für jeden Motor
self.left_pid = VelocityPID(Kp=1.0, Ki=0.1, Kd=0.05)
self.right_pid = VelocityPID(Kp=1.0, Ki=0.1, Kd=0.05)
self.mow_pid = PID(Kp=0.8, Ki=0.05, Kd=0.02)
```

### 2. Überlastungsschutz

- Automatische Stromdatenüberwachung
- Konfigurierbare Grenzwerte
- Automatischer Notaus bei Überlastung
- Zählerbasierte Fehlererkennung

### 3. Differential Drive Kinematik

```python
# Umrechnung von linearer/Winkelgeschwindigkeit zu Radgeschwindigkeiten
half_wheelbase = self.wheel_base / 2.0
self.target_left_speed = linear - (angular * half_wheelbase)
self.target_right_speed = linear + (angular * half_wheelbase)
```

### 4. Adaptive Geschwindigkeitsanpassung

- Geschwindigkeitsreduzierung bei hohem Motorstrom
- Konfigurierbare Anpassungsparameter
- Automatische Optimierung für verschiedene Geländetypen

### 5. Autonome Navigation

- Wegpunkt-basierte Pfadplanung
- PID-Regelung für Kurs und Entfernung
- Integration mit GPS-Navigation
- Hinderniserkennung und -umfahrung

## Zentrale Motorsteuerung

### Ersetzt direkte Pico-Kommandos

**Früher (direkte Kommandos)**:
```python
pico.send_command("AT+MOTOR,100,100,0")  # Direkt an Pico
```

**Jetzt (zentrale Steuerung)**:
```python
motor.set_linear_angular_speed(0.5, 0.0)  # Über Motor-Klasse
motor.set_mow_state(True)                  # Zentrale Kontrolle
```

### Hardware-Integration

```python
# Kommunikation über Hardware Manager
if self.hardware_manager:
    self.hardware_manager.send_motor_command(left_pwm, right_pwm, mow_pwm)
```

## Konfiguration

Alle Motorparameter sind über `config.json` konfigurierbar:

```json
{
  "motor": {
    "pid": {
      "left": {"kp": 1.0, "ki": 0.1, "kd": 0.05},
      "right": {"kp": 1.0, "ki": 0.1, "kd": 0.05},
      "mow": {"kp": 0.8, "ki": 0.05, "kd": 0.02}
    },
    "limits": {
      "max_motor_current": 3.0,
      "max_mow_current": 5.0,
      "max_overload_count": 5
    },
    "physical": {
      "ticks_per_meter": 1000,
      "wheel_base": 0.3,
      "pwm_scale_factor": 100
    }
  }
}
```

## Verwendung in der Praxis

### Grundlegende Motorsteuerung

```python
# Motor initialisieren
motor = Motor(hardware_manager=hardware_manager)
motor.begin()

# Bewegung steuern
motor.set_linear_angular_speed(0.5, 0.0)  # 0.5 m/s vorwärts
motor.set_mow_state(True)                  # Mähmotor einschalten

# In Hauptschleife
while running:
    motor_status = motor.update(pico_data)  # Sensordaten verarbeiten
    motor.run()                             # PID-Regelung ausführen
    time.sleep(0.02)                        # 50Hz
```

### Autonome Navigation

```python
# Mähzonen setzen
motor.set_mow_zones(map_module.zones)
motor.set_obstacles(map_module.exclusions)

# Autonomes Mähen starten
motor.start_autonomous_mowing()
```

## Vorteile der aktuellen Implementierung

### 1. Sicherheit
- Automatischer Überlastungsschutz
- Stromdatenüberwachung in Echtzeit
- Notaus-Funktionen
- Fehlererkennung und -behandlung

### 2. Präzision
- PID-basierte Geschwindigkeitsregelung
- Odometrie-Feedback
- Adaptive Geschwindigkeitsanpassung
- Differential Drive Kinematik

### 3. Flexibilität
- Konfigurierbare Parameter
- Modularer Aufbau
- Erweiterbare Funktionen
- Hardware-Abstraktion

### 4. Integration
- Nahtlose Pico-Kommunikation
- GPS-Navigation
- Pfadplanung
- Web-Interface

## Tests und Validierung

Die Implementierung wird durch umfangreiche Tests validiert:

- `tests/test_motor_integration.py` - Integrationstests
- `tests/test_motor_config.py` - Konfigurationstests
- `tests/test_motor_pid_placeholder.py` - PID-Funktionalitätstests
- `examples/example_autonomous_mowing.py` - Praxisbeispiele

## Fazit

Die Motor- und PID-Integration ist **vollständig implementiert** und bietet:

✅ **Vollständige Pico-Datenintegration**  
✅ **PID-basierte Geschwindigkeitsregelung**  
✅ **Zentrale Motorsteuerung**  
✅ **Überlastungsschutz und Sicherheit**  
✅ **Autonome Navigation**  
✅ **Konfigurierbare Parameter**  
✅ **Umfangreiche Tests**  

Das System ist produktionsreif und wird aktiv in der Hauptanwendung verwendet.

---

**Letzte Aktualisierung**: Dezember 2024  
**Status**: Vollständig implementiert und getestet  
**Dokumentation**: Aktuell und vollständig