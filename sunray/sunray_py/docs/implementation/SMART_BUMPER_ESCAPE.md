# SmartBumperEscapeOp - Intelligente Bumper-Ausweichlogik

## Übersicht

Die `SmartBumperEscapeOp` ist eine erweiterte Ausweichoperation, die speziell für Bumper-Kollisionen entwickelt wurde. Sie implementiert eine richtungsabhängige Ausweichstrategie, die berücksichtigt, welcher Bumper ausgelöst wurde, und entsprechend reagiert.

## Funktionsweise

### Grundprinzip

Wenn ein Bumper ausgelöst wird, führt der Roboter folgende Sequenz aus:

1. **Stopp** (0,3s): Sofortiger Stopp zur Stabilisierung
2. **Rückwärtsfahrt** (1,0s): Kurzes Rückwärtsfahren um Abstand zu gewinnen
3. **Kurvenfahrt** (3,0s): Ausweichkurve in die sichere Richtung
4. **Rückkehr** (2,0s): Versuch zur ursprünglichen Bahn zurückzukehren

### Richtungslogik

| Bumper-Status | Hindernis-Position | Ausweichrichtung | Begründung |
|---------------|-------------------|------------------|------------|
| Rechter Bumper | Rechts | Links | Weg vom Hindernis |
| Linker Bumper | Links | Rechts | Weg vom Hindernis |
| Beide Bumper | Unbekannt | Zufällig | Fallback-Strategie |
| Kein Bumper | Unbekannt | Zufällig | Fallback-Strategie |

## Implementierung

### Klassen-Struktur

```python
class SmartBumperEscapeOp(Operation):
    def __init__(self, name: str, motor=None):
        # Initialisierung mit Motor-Referenz
        
    def on_start(self, params: Dict[str, Any]):
        # Bumper-Status analysieren
        # Ausweichrichtung bestimmen
        # Map-Integration laden (optional)
        
    def run(self):
        # Phasen-basierte Ausführung
        # stop -> reverse -> curve -> return -> complete
        
    def on_stop(self):
        # Aufräumen und Motoren stoppen
```

### Parameter

Die Operation erwartet folgende Parameter beim Start:

```python
escape_params = {
    'left_bumper': bool,      # Status des linken Bumpers
    'right_bumper': bool,     # Status des rechten Bumpers
    'robot_position': {       # Aktuelle Roboterposition
        'x': float,
        'y': float,
        'heading': float
    }
}
```

### Phasen-Details

#### Phase 1: Stop (0,3s)
- Alle Motoren werden gestoppt
- Stabilisierung des Roboters
- Vorbereitung für Rückwärtsfahrt

#### Phase 2: Reverse (1,0s)
- Rückwärtsfahrt mit 0,2 m/s
- Gerade Bewegung ohne Rotation
- Abstand zum Hindernis schaffen

#### Phase 3: Curve (3,0s)
- Vorwärtsfahrt mit 0,3 m/s
- Gleichzeitige Rotation mit 0,3 rad/s
- Richtung abhängig vom ausgelösten Bumper

#### Phase 4: Return (2,0s)
- Vorwärtsfahrt mit 0,25 m/s
- Gegenrotation mit 0,2 rad/s
- Versuch zur ursprünglichen Bahn zurückzukehren

## Integration in main.py

### Bumper-Erkennung

```python
# Bumper-Status aus Obstacle Detector extrahieren
obstacle_status = obstacle_detector.get_status()
bumper_info = obstacle_status.get('bumper', {})
bumper_state = bumper_info.get('state', [False, False])

# Parameter vorbereiten
escape_params = {
    'left_bumper': bumper_state[0],
    'right_bumper': bumper_state[1],
    'robot_position': {
        'x': robot_state.get('x', 0),
        'y': robot_state.get('y', 0),
        'heading': robot_state.get('heading', 0)
    }
}

# SmartBumperEscapeOp starten
if bumper_info.get('collision_detected', False):
    current_op = SmartBumperEscapeOp("smart_bumper_escape", motor=motor)
    current_op.start(escape_params)
```

### Fallback-Mechanismus

Für nicht-Bumper-Kollisionen (IMU, Stromspitzen) wird weiterhin die `EscapeForwardOp` verwendet:

```python
else:
    # Fallback für andere Hindernisarten
    current_op = EscapeForwardOp("escape_forward", motor=motor)
    current_op.start({})
```

##### Mähmotor-Verhalten

**Wichtig**: Der Mähmotor läuft während des gesamten Ausweichmanövers weiter!

- **Stopp-Phase**: Nur Antriebsmotoren werden gestoppt
- **Alle Phasen**: Mähmotor behält seine aktuelle Geschwindigkeit bei
- **Begründung**: Das Gras wird kontinuierlich gemäht, auch während Hindernisumfahrung
- **Sicherheit**: Mähmotor wird nur bei echten Notfällen gestoppt

```python
# Beispiel: Nur Antriebsmotoren stoppen
self.motor.stop_immediately(include_mower=False)

# Gespeicherter Mähmotor-PWM wird beibehalten
self.saved_mow_pwm = getattr(self.motor, 'target_mow_speed', 100)
```

### Sicherheitsfeatures

### Map-Integration (Optional)

- Lädt Mähzonen und Ausschlusszonen aus `zones.json`
- Implementiert `_is_safe_position()` für Positionsprüfung
- Verwendet Ray-Casting-Algorithmus für Polygon-Tests
- Graceful Degradation wenn Map nicht verfügbar

### Robuste Ausführung

- **Timeout-Schutz**: Jede Phase hat eine maximale Dauer
- **Motor-Fallback**: Direkte Hardware-Kommandos wenn Motor-Klasse nicht verfügbar
- **Fehlerbehandlung**: Exceptions werden abgefangen und geloggt
- **Zustandsreset**: Automatische Rückkehr zum Mähmodus nach Abschluss

## Konfiguration

### Anpassbare Parameter

```python
# Phasendauern (in Sekunden)
self.stop_duration = 0.3
self.reverse_duration = 1.0
self.curve_duration = 3.0
self.return_duration = 2.0

# Geschwindigkeiten
reverse_speed = -0.2      # m/s rückwärts
curve_linear = 0.3        # m/s vorwärts in Kurve
curve_angular = 0.3       # rad/s Rotation in Kurve
return_linear = 0.25      # m/s vorwärts bei Rückkehr
return_angular = 0.2      # rad/s Rotation bei Rückkehr
```

### Hardware-Fallback-Werte

```python
# PWM-Werte für direkte Hardware-Steuerung
reverse_pwm = -80         # Rückwärts
curve_left_pwm = (100, 60)   # Links: (links, rechts)
curve_right_pwm = (60, 100)  # Rechts: (links, rechts)
return_left_pwm = (100, 70)  # Rückkehr links
return_right_pwm = (70, 100) # Rückkehr rechts
```

## Testing

### Test-Suite

Die Implementierung wird durch `test_smart_bumper_escape.py` getestet:

- **Richtungslogik-Tests**: Alle Bumper-Kombinationen
- **Phasenübergangs-Tests**: Vollständige Sequenz-Simulation
- **Map-Integration-Tests**: Positionssicherheit (optional)

### Test-Ergebnisse

```
✅ Rechter Bumper → Ausweichen nach links
✅ Linker Bumper → Ausweichen nach rechts  
✅ Beide Bumper → Zufällige Richtung
✅ Phasenübergänge funktionieren korrekt
✅ Motor-Kommandos werden korrekt generiert
```

## Vorteile gegenüber EscapeForwardOp

| Feature | EscapeForwardOp | SmartBumperEscapeOp |
|---------|-----------------|---------------------|
| Richtungserkennung | ❌ Zufällig | ✅ Bumper-abhängig |
| Rückwärtsfahrt | ❌ Nein | ✅ Ja |
| Map-Integration | ❌ Nein | ✅ Optional |
| Mähmotor-Verhalten | ❓ Unbekannt | ✅ Läuft weiter |
| Phasen-Anzahl | 3 | 4 |
| Intelligenz | ⭐⭐ | ⭐⭐⭐⭐ |

## Zukünftige Erweiterungen

### Geplante Features

1. **Dynamische Geschwindigkeitsanpassung**: Basierend auf Hindernistyp
2. **Lernende Algorithmen**: Anpassung basierend auf Erfolgsrate
3. **Multi-Sensor-Fusion**: Integration von Ultraschall und Kamera
4. **Pfadplanung-Integration**: Berücksichtigung der aktuellen Route

### Optimierungsmöglichkeiten

1. **Adaptive Phasendauern**: Basierend auf Umgebung
2. **Hindernisvorhersage**: Präventive Ausweichmanöver
3. **Energieoptimierung**: Minimierung des Energieverbrauchs
4. **Kollisionsvermeidung**: Integration mit anderen Sensoren

## Dateien

### Implementierung
- `op.py`: SmartBumperEscapeOp-Klasse
- `main.py`: Integration in Hauptschleife
- `obstacle_detection.py`: Bumper-Detektor

### Tests und Dokumentation
- `test_smart_bumper_escape.py`: Test-Suite
- `SMART_BUMPER_ESCAPE.md`: Diese Dokumentation

### Konfiguration
- `zones.json`: Mähzonen und Ausschlusszonen (optional)

## Fazit

Die `SmartBumperEscapeOp` stellt eine erhebliche Verbesserung gegenüber der bisherigen Ausweichlogik dar. Durch die richtungsabhängige Reaktion und die mehrstufige Ausweichsequenz wird eine deutlich intelligentere und effektivere Hindernisumfahrung erreicht.

Die Implementation ist robust, gut getestet und bietet eine solide Basis für zukünftige Erweiterungen der autonomen Navigation.