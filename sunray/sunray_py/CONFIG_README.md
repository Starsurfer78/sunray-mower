# Konfigurationsverwaltung

Dieses Dokument beschreibt die Konfigurationsverwaltung für das Sunray Python System.

## Übersicht

Das Konfigurationssystem verwendet JSON-Dateien zur Verwaltung aller Einstellungen. Es gibt zwei Hauptkomponenten:

1. **Beispiel-Konfiguration** (`config_example.json`) - Enthält alle Standardwerte
2. **Aktive Konfiguration** (`/etc/mower/config.json`) - Die tatsächlich verwendete Konfiguration

## Dateien

### config_example.json

Die `config_example.json` Datei enthält alle Standardkonfigurationswerte und dient als:
- **Vorlage** für neue Installationen
- **Referenz** für verfügbare Einstellungen
- **Fallback** wenn die Hauptkonfiguration beschädigt ist
- **Dokumentation** der Konfigurationsstruktur

### Aktive Konfiguration

Die aktive Konfigurationsdatei wird standardmäßig unter `/etc/mower/config.json` gespeichert und enthält die tatsächlich verwendeten Einstellungen.

## Verwendung

### Neue Installation

1. Kopiere `config_example.json` nach `/etc/mower/config.json`:
   ```bash
   sudo mkdir -p /etc/mower
   sudo cp config_example.json /etc/mower/config.json
   ```

2. Passe die Werte in `/etc/mower/config.json` an deine Hardware an

### Konfiguration anpassen

```python
from config import get_config

# Konfiguration laden
config = get_config()

# Werte lesen
kp_left = config.get('motor.pid.left.kp')
max_current = config.get('motor.limits.max_motor_current')

# Werte setzen
config.set('motor.pid.left.kp', 1.5)
config.set('motor.limits.max_motor_current', 4.0)
```

### Konfiguration zurücksetzen

```python
from config import get_config

config = get_config()
config.reset_to_defaults()  # Setzt alle Werte auf Standardwerte zurück
```

## Konfigurationsstruktur

### Motor-Konfiguration

```json
{
  "motor": {
    "pid": {
      "left": { "kp": 1.0, "ki": 0.1, "kd": 0.05 },
      "right": { "kp": 1.0, "ki": 0.1, "kd": 0.05 },
      "mow": { "kp": 0.8, "ki": 0.05, "kd": 0.02 }
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

### System-Konfiguration

```json
{
  "system": {
    "debug": false,
    "log_level": "INFO",
    "mqtt_enabled": true,
    "web_gui_enabled": true
  }
}
```

### Sicherheits-Konfiguration

```json
{
  "safety": {
    "emergency_stop_enabled": true,
    "lift_detection_enabled": true,
    "tilt_detection_enabled": true,
    "max_tilt_angle": 30.0
  }
}
```

## Vorteile der neuen Struktur

1. **Wartbarkeit**: Konfigurationswerte sind in einer separaten JSON-Datei
2. **Versionierung**: `config_example.json` kann versioniert werden
3. **Flexibilität**: Einfache Anpassung ohne Code-Änderungen
4. **Dokumentation**: Beispiel-Datei dient als lebende Dokumentation
5. **Fallback**: Robuste Behandlung fehlender Konfigurationswerte

## Migration

Für bestehende Installationen:

1. Die `config.py` lädt automatisch Werte aus `config_example.json`
2. Fehlende Werte werden automatisch ergänzt
3. Bestehende Konfigurationen bleiben kompatibel
4. Keine manuellen Änderungen erforderlich

## Entwicklung

Beim Hinzufügen neuer Konfigurationsoptionen:

1. Füge den neuen Wert zu `config_example.json` hinzu
2. Dokumentiere den Parameter in diesem README
3. Verwende `config.get('section.key', default_value)` im Code
4. Teste mit verschiedenen Konfigurationszuständen

## Fehlerbehebung

### Konfiguration wird nicht geladen

- Prüfe ob `config_example.json` existiert
- Prüfe JSON-Syntax mit einem Validator
- Prüfe Dateiberechtigungen

### Werte werden nicht übernommen

- Prüfe Schlüssel-Syntax (z.B. `motor.pid.left.kp`)
- Verwende `config.validate_config()` zur Überprüfung
- Prüfe Log-Ausgaben für Fehlermeldungen

### Zurücksetzen auf Standardwerte

```python
config.reset_to_defaults()
```

oder manuell:

```bash
sudo rm /etc/mower/config.json
# Beim nächsten Start werden Standardwerte geladen
```