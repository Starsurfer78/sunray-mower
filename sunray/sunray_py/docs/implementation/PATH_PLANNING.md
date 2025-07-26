# Pfadplanung Implementation

## Übersicht

Die Pfadplanungsimplementierung ermöglicht es dem Sunray Mähroboter, verschiedene Mähmuster autonom auszuführen. Das System besteht aus mehreren integrierten Komponenten:

- **PathPlanner**: Generiert Mähpfade für verschiedene Muster
- **Motor-Integration**: Erweiterte Motor-Klasse mit Navigationsfunktionen
- **HTTP-API**: Web-Endpunkte zur Steuerung der Pfadplanung
- **Autonome Navigation**: Automatische Wegpunkt-Navigation

## Implementierte Komponenten

### 1. PathPlanner-Klasse (`path_planner.py`)

#### Verfügbare Mähmuster:
- **LINES**: Parallele Linien mit Boustrophedon-Muster
- **SPIRAL**: Spiralförmig von außen nach innen
- **RANDOM**: Zufällige Punkte basierend auf Zonengröße
- **PERIMETER**: Umrandung der Zone

#### Hauptmethoden:
```python
planner = PathPlanner()
planner.set_pattern(MowPattern.LINES)
planner.set_line_spacing(0.3)  # 30cm Abstand
waypoints = planner.generate_zone_path(zone, obstacles)
```

### 2. Motor-Klasse Erweiterung (`motor.py`)

#### Neue Navigationsfunktionen:
- `set_mow_zones(zones)`: Setzt Mähzonen
- `set_obstacles(obstacles)`: Setzt Hindernisse
- `set_mow_pattern(pattern)`: Wählt Mähmuster
- `start_autonomous_mowing()`: Startet autonomes Mähen
- `stop_autonomous_mowing()`: Stoppt autonomes Mähen
- `update_position(x, y, heading)`: Aktualisiert Roboterposition
- `get_navigation_status()`: Gibt Navigationsstatus zurück

#### PID-Regler für Navigation:
- **Heading PID**: Kursregelung (Kp=2.0, Ki=0.1, Kd=0.5)
- **Distance PID**: Entfernungsregelung (Kp=1.0, Ki=0.05, Kd=0.2)

### 3. HTTP-API Erweiterung (`http_server.py`)

#### Neue Endpunkte:

**Navigation starten:**
```bash
POST /navigation/start
# Startet autonomes Mähen
```

**Navigation stoppen:**
```bash
POST /navigation/stop
# Stoppt autonomes Mähen
```

**Navigationsstatus:**
```bash
GET /navigation/status
# Gibt aktuellen Status zurück
```

**Mähmuster setzen:**
```bash
POST /navigation/pattern
Content-Type: application/json

{
  "pattern": "LINES",
  "line_spacing": 0.3
}
```

**Mähzonen setzen:**
```bash
POST /navigation/zones
Content-Type: application/json

{
  "zones": [
    {
      "points": [[0, 0], [10, 0], [10, 10], [0, 10]]
    }
  ]
}
```

### 4. MowOp Integration (`op.py`)

Die `MowOp`-Klasse wurde erweitert, um die neue autonome Mähfunktionalität zu nutzen:

- Automatisches Starten der autonomen Navigation
- Überwachung des Mähfortschritts
- Automatisches Stoppen bei Abschluss

### 5. Main-Loop Integration (`main.py`)

- Automatische Konfiguration der Pfadplanung beim Start
- Positionsaktualisierung alle 0.5 Sekunden
- Integration mit bestehender Sicherheitslogik

## Konfiguration

### Standard-Einstellungen:
```python
# Mähmuster
motor.set_mow_pattern(MowPattern.LINES)
motor.set_line_spacing(0.3)  # 30cm Abstand

# Navigation
waypoint_tolerance = 0.5  # 50cm Toleranz
max_linear_speed = 0.5    # 0.5 m/s
max_angular_speed = 1.0   # 1.0 rad/s
min_turn_radius = 0.3     # 30cm
```

### Zonenbasierte Konfiguration:
```python
# Zonen aus map.py laden
if map_module.zones:
    motor.set_mow_zones(map_module.zones)
    
if map_module.exclusions:
    motor.set_obstacles(map_module.exclusions)
```

## Verwendung

### 1. Programmatische Steuerung:
```python
from motor import Motor
from path_planner import MowPattern
from map import Point, Polygon

# Motor initialisieren
motor = Motor(hardware_manager=hw_manager)
motor.begin()

# Zone definieren
zone_points = [Point(0, 0), Point(10, 0), Point(10, 10), Point(0, 10)]
zone = Polygon(zone_points)

# Pfadplanung konfigurieren
motor.set_mow_zones([zone])
motor.set_mow_pattern(MowPattern.LINES)
motor.set_line_spacing(0.3)

# Autonomes Mähen starten
motor.start_autonomous_mowing()
```

### 2. Web-API Steuerung:
```bash
# Mähmuster setzen
curl -X POST http://localhost:5000/navigation/pattern \
  -H "Content-Type: application/json" \
  -d '{"pattern": "SPIRAL", "line_spacing": 0.4}'

# Navigation starten
curl -X POST http://localhost:5000/navigation/start

# Status abfragen
curl http://localhost:5000/navigation/status

# Navigation stoppen
curl -X POST http://localhost:5000/navigation/stop
```

## Testen

### Testskript ausführen:
```bash
cd sunray_py
python test_path_planning.py
```

### Beispielskript:
```bash
python example_autonomous_mowing.py
```

## Sicherheitsfeatures

### Kollisionserkennung:
- Automatisches Stoppen bei Hinderniserkennung
- Wechsel zu EscapeForwardOp bei Kollision
- Fortsetzung nach erfolgreicher Umfahrung

### Notfall-Stopp:
- Sofortiger Stopp bei Neigungswarnung (>35°)
- Deaktivierung der autonomen Navigation
- Wechsel zu IdleOp

### Überwachung:
- Kontinuierliche Positionsaktualisierung
- Wegpunkt-Toleranz-Überwachung
- Automatische Pfadneuberechnung bei Bedarf

## Erweiterungsmöglichkeiten

### Zusätzliche Muster:
- Kreisförmige Muster
- Adaptive Muster basierend auf Grastyp
- Wetterabhängige Muster

### Optimierungen:
- A*-Pfadfindung für komplexe Hindernisse
- Dynamische Linienabstände
- Energieoptimierte Pfade

### Integration:
- GPS-basierte Präzisionsnavigation
- Kamerabasierte Hinderniserkennung
- Machine Learning für Musteroptimierung

## Status

✅ **Abgeschlossen:**
- PathPlanner-Implementierung
- Motor-Integration
- HTTP-API-Erweiterung
- Grundlegende Mähmuster (LINES, SPIRAL, RANDOM, PERIMETER)
- Sicherheitsintegration
- Testframework

🔄 **In Arbeit:**
- Rückkehr zur Ladestation
- Zonenwechsel-Logik
- Erweiterte Hindernisumfahrung

📋 **Geplant:**
- GPS-Präzisionsnavigation
- Erweiterte Muster
- Performance-Optimierungen