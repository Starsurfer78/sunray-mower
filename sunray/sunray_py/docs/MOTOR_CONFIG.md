# Motor-Konfiguration

Diese Dokumentation beschreibt alle konfigurierbaren Parameter für die Motor-Steuerung in Sunray Python.

## Übersicht

Alle Motor-Einstellungen wurden aus der `Motor`-Klasse in die zentrale Konfigurationsdatei `/etc/mower/config.json` ausgelagert. Dies ermöglicht:

- **Einfache Anpassung** ohne Code-Änderungen
- **Verschiedene Profile** für unterschiedliche Roboter-Konfigurationen
- **Laufzeit-Konfiguration** über Web-GUI oder API
- **Backup und Wiederherstellung** von Einstellungen

## Konfigurationsstruktur

### Motor-Sektion

```json
{
  "motor": {
    "pid": { ... },
    "limits": { ... },
    "physical": { ... },
    "mow": { ... },
    "adaptive": { ... }
  }
}
```

## Detaillierte Parameter

### 1. PID-Regelung (`motor.pid`)

Konfiguration der PID-Regler für die Motorgeschwindigkeitsregelung.

#### Linker Motor (`motor.pid.left`)
```json
"left": {
  "kp": 1.0,           // Proportionalverstärkung
  "ki": 0.1,           // Integralverstärkung  
  "kd": 0.05,          // Differentialverstärkung
  "output_min": -255,  // Minimaler PWM-Wert
  "output_max": 255    // Maximaler PWM-Wert
}
```

#### Rechter Motor (`motor.pid.right`)
```json
"right": {
  "kp": 1.0,           // Proportionalverstärkung
  "ki": 0.1,           // Integralverstärkung
  "kd": 0.05,          // Differentialverstärkung
  "output_min": -255,  // Minimaler PWM-Wert
  "output_max": 255    // Maximaler PWM-Wert
}
```

#### Mähmotor (`motor.pid.mow`)
```json
"mow": {
  "kp": 0.8,           // Proportionalverstärkung
  "ki": 0.05,          // Integralverstärkung
  "kd": 0.02,          // Differentialverstärkung
  "output_min": 0,     // Minimaler PWM-Wert (nur vorwärts)
  "output_max": 255    // Maximaler PWM-Wert
}
```

**Anpassungshinweise:**
- **Kp (Proportional)**: Höhere Werte = schnellere Reaktion, aber mögliche Instabilität
- **Ki (Integral)**: Eliminiert stationäre Fehler, zu hoch kann zu Schwingungen führen
- **Kd (Differential)**: Dämpft Schwingungen, zu hoch kann zu Rauschen führen

### 2. Grenzwerte (`motor.limits`)

Sicherheitsgrenzwerte für Strom und Geschwindigkeit.

```json
"limits": {
  "max_motor_current": 3.0,      // Max. Strom Fahrmotoren [A]
  "max_mow_current": 5.0,        // Max. Strom Mähmotor [A]
  "max_overload_count": 5,       // Max. aufeinanderfolgende Überlastungen
  "max_realistic_speed": 2.0     // Max. realistische Geschwindigkeit [m/s]
}
```

**Anpassungshinweise:**
- **max_motor_current**: Abhängig von Motor-Spezifikation und Sicherung
- **max_mow_current**: Mähmotor hat typischerweise höheren Stromverbrauch
- **max_overload_count**: Niedrigere Werte = empfindlicherer Schutz
- **max_realistic_speed**: Verhindert Odometrie-Fehler durch unrealistische Werte

### 3. Physikalische Parameter (`motor.physical`)

Roboter-spezifische mechanische Eigenschaften.

```json
"physical": {
  "ticks_per_meter": 1000,       // Encoder-Ticks pro Meter
  "wheel_base": 0.3,             // Radstand [m]
  "pwm_scale_factor": 100        // PWM-Skalierungsfaktor
}
```

**Anpassungshinweise:**
- **ticks_per_meter**: Muss für jeden Roboter kalibriert werden
- **wheel_base**: Abstand zwischen linkem und rechtem Rad
- **pwm_scale_factor**: Konvertierung von Geschwindigkeit zu PWM-Werten

### 4. Mähmotor-Konfiguration (`motor.mow`)

Spezielle Einstellungen für den Mähmotor.

```json
"mow": {
  "default_pwm": 100,                // Standard-PWM beim Einschalten
  "min_current_threshold": 0.1,      // Min. Strom bei laufendem Motor [A]
  "max_current_threshold": 0.5       // Max. Strom bei gestopptem Motor [A]
}
```

**Anpassungshinweise:**
- **default_pwm**: Sollte ausreichend für normales Mähen sein
- **min_current_threshold**: Erkennt blockierten oder defekten Motor
- **max_current_threshold**: Erkennt ungewollten Stromfluss

### 5. Adaptive Geschwindigkeitsanpassung (`motor.adaptive`)

Automatische Geschwindigkeitsreduzierung bei hohem Strom.

```json
"adaptive": {
  "enabled": true,                   // Adaptive Anpassung aktiviert
  "current_threshold_factor": 0.7,   // Stromgrenze als Faktor von max_current
  "min_speed_factor": 0.3            // Minimale Geschwindigkeit als Faktor
}
```

**Anpassungshinweise:**
- **enabled**: Kann für Tests oder spezielle Situationen deaktiviert werden
- **current_threshold_factor**: 0.7 = 70% des maximalen Stroms als Grenze
- **min_speed_factor**: 0.3 = mindestens 30% der ursprünglichen Geschwindigkeit

## Verwendung in der Motor-Klasse

### Konfiguration laden
```python
from config import get_config

class Motor:
    def __init__(self, pico_comm=None):
        self.config = get_config()
        
        # PID-Parameter aus Konfiguration
        left_pid_config = self.config.get_pid_config('left')
        self.left_pid = VelocityPID(
            Kp=left_pid_config.get('kp', 1.0),
            Ki=left_pid_config.get('ki', 0.1),
            Kd=left_pid_config.get('kd', 0.05)
        )
```

### Konfiguration zur Laufzeit ändern
```python
# Einzelnen Wert ändern
config.set('motor.pid.left.kp', 1.5)

# Komplette Sektion ändern
config.set('motor.limits.max_motor_current', 3.5)

# Konfiguration neu laden
config.reload()
```

## Kalibrierung und Optimierung

### 1. PID-Parameter optimieren

**Schritt-für-Schritt-Anleitung:**

1. **Kp einstellen:**
   - Beginnen Sie mit Kp=1.0, Ki=0, Kd=0
   - Erhöhen Sie Kp bis der Motor schnell reagiert
   - Reduzieren Sie wenn Schwingungen auftreten

2. **Ki hinzufügen:**
   - Beginnen Sie mit Ki=0.1
   - Erhöhen Sie um stationäre Fehler zu eliminieren
   - Reduzieren Sie bei Instabilität

3. **Kd feinabstimmen:**
   - Beginnen Sie mit Kd=0.05
   - Erhöhen Sie zur Dämpfung von Schwingungen
   - Reduzieren Sie bei zu träger Reaktion

### 2. Physikalische Parameter kalibrieren

**ticks_per_meter bestimmen:**
```python
# 1. Roboter genau 1 Meter fahren lassen
# 2. Odometrie-Differenz messen
# 3. Wert in Konfiguration eintragen
ticks_per_meter = gemessene_ticks / gefahrene_distanz
```

**wheel_base messen:**
```python
# 1. Roboter eine komplette Drehung machen lassen
# 2. Odometrie-Differenz zwischen linkem und rechtem Rad messen
# 3. Radstand berechnen
wheel_base = (left_ticks - right_ticks) / (2 * pi * ticks_per_meter)
```

### 3. Stromgrenzwerte anpassen

**Überwachung:**
```python
# Maximale Ströme während normalem Betrieb messen
max_normal_current = max(gemessene_ströme)
max_motor_current = max_normal_current * 1.2  # 20% Sicherheitspuffer
```

## Beispiel-Konfigurationen

### Kleiner Roboter (leicht)
```json
{
  "motor": {
    "pid": {
      "left": {"kp": 0.8, "ki": 0.05, "kd": 0.02},
      "right": {"kp": 0.8, "ki": 0.05, "kd": 0.02}
    },
    "limits": {
      "max_motor_current": 2.0,
      "max_mow_current": 3.0
    },
    "physical": {
      "ticks_per_meter": 1500,
      "wheel_base": 0.25
    }
  }
}
```

### Großer Roboter (schwer)
```json
{
  "motor": {
    "pid": {
      "left": {"kp": 1.5, "ki": 0.2, "kd": 0.1},
      "right": {"kp": 1.5, "ki": 0.2, "kd": 0.1}
    },
    "limits": {
      "max_motor_current": 5.0,
      "max_mow_current": 8.0
    },
    "physical": {
      "ticks_per_meter": 800,
      "wheel_base": 0.4
    }
  }
}
```

## Fehlerbehebung

### Häufige Probleme

**Motor schwingt/oszilliert:**
- Kp zu hoch → reduzieren
- Kd zu niedrig → erhöhen
- Ki zu hoch → reduzieren

**Motor reagiert zu träge:**
- Kp zu niedrig → erhöhen
- Kd zu hoch → reduzieren

**Stationärer Fehler:**
- Ki zu niedrig → erhöhen
- Integrator-Windup → output_limits prüfen

**Häufige Überlastungen:**
- max_motor_current zu niedrig → erhöhen
- Mechanische Probleme → Hardware prüfen
- PWM-Skalierung falsch → pwm_scale_factor anpassen

### Debug-Funktionen

```python
# Aktuelle Konfiguration anzeigen
motor_config = config.get_motor_config()
print(json.dumps(motor_config, indent=2))

# Konfiguration validieren
if not config.validate_config():
    print("Konfigurationsfehler erkannt!")

# Auf Standardwerte zurücksetzen
config.reset_to_defaults()
```

## Migration von hartcodierten Werten

Die folgenden Parameter wurden von der `Motor`-Klasse in die Konfiguration verschoben:

| Alter Code | Neue Konfiguration |
|------------|--------------------|
| `Kp=1.0, Ki=0.1, Kd=0.05` | `motor.pid.left/right.*` |
| `max_motor_current = 3.0` | `motor.limits.max_motor_current` |
| `max_mow_current = 5.0` | `motor.limits.max_mow_current` |
| `ticks_per_meter = 1000` | `motor.physical.ticks_per_meter` |
| `wheel_base = 0.3` | `motor.physical.wheel_base` |
| `target_mow_speed = 100` | `motor.mow.default_pwm` |
| `left_output * 100` | `left_output * pwm_scale_factor` |

Dies ermöglicht eine flexible Anpassung ohne Code-Änderungen und unterstützt verschiedene Roboter-Konfigurationen.