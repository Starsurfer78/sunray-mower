# Erweiterte Pfadplanung für Sunray Mähroboter

## Überblick

Die erweiterte Pfadplanung kombiniert verschiedene Algorithmen für optimale und adaptive Navigation:

- **A*-Algorithmus** für optimale Pfade um Hindernisse
- **Traditionelle Mähmuster** für effiziente Flächenabdeckung
- **Hybride Strategien** für beste Performance
- **Adaptive Auswahl** basierend auf Zoneneigenschaften
- **Dynamische Neuplanung** bei Hinderniserkennung

## Architektur

### Klassen-Hierarchie

```
AdvancedPathPlanner
├── AStarPathfinder (A*-Algorithmus)
├── PathPlanner (Traditionelle Muster)
└── GPSNavigation (GPS-Integration)
```

### Planungsstrategien

#### 1. Traditional (Traditionell)
- Verwendet klassische Mähmuster (Linien, Spiral, etc.)
- Optimal für offene Flächen ohne Hindernisse
- Hohe Effizienz bei der Flächenabdeckung

#### 2. A*-basiert
- Sampling-basierte Abdeckung mit optimalen Pfaden
- Ideal für komplexe Bereiche mit vielen Hindernissen
- TSP-Heuristik für Punkt-Reihenfolge-Optimierung

#### 3. Hybrid (Empfohlen)
- Kombiniert traditionelle Muster mit A*-Umgehungen
- Traditionelle Pfade als Basis
- A*-Umgehungen bei Hindernissen
- Beste Balance zwischen Effizienz und Robustheit

#### 4. Adaptive
- Automatische Strategieauswahl basierend auf:
  - Zonengröße
  - Hindernisdichte
  - Zonenkomplexität
- Optimiert für verschiedene Umgebungen

## Konfiguration

### config.json Parameter

```json
{
  "advanced_path_planning": {
    "strategy": "hybrid",
    "max_segment_length": 10.0,
    "obstacle_detection_radius": 1.0,
    "replanning_threshold": 0.5
  },
  "astar_pathfinding": {
    "diagonal_movement": true,
    "heuristic_weight": 1.0,
    "obstacle_inflation": 0.2,
    "max_iterations": 10000
  }
}
```

### Parameter-Beschreibung

- **strategy**: Planungsstrategie (traditional/astar/hybrid/adaptive)
- **max_segment_length**: Maximale Segmentlänge in Metern
- **obstacle_detection_radius**: Radius für Hinderniserkennung
- **replanning_threshold**: Schwellwert für Neuplanung
- **diagonal_movement**: Diagonale Bewegung im A*-Grid
- **heuristic_weight**: Gewichtung der A*-Heuristik
- **obstacle_inflation**: Hindernis-Aufblähung für Sicherheit
- **max_iterations**: Maximale A*-Iterationen

## Verwendung

### Grundlegende Initialisierung

```python
from advanced_path_planner import AdvancedPathPlanner, PlanningStrategy

# Planer erstellen
planner = AdvancedPathPlanner()

# Strategie setzen
planner.set_strategy(PlanningStrategy.HYBRID)

# Zonen und Hindernisse konfigurieren
planner.set_zones_and_obstacles(zones, obstacles)

# Pfadplanung durchführen
success = planner.plan_zone_coverage(MowPattern.LINES)
```

### Navigation

```python
# Nächsten Wegpunkt abrufen
waypoint, path_type = planner.get_next_waypoint(current_position)

if waypoint:
    # Navigation zum Wegpunkt
    motor.navigate_to_waypoint(waypoint.x, waypoint.y)
```

### Dynamische Hindernisse

```python
# Dynamisches Hindernis hinzufügen
obstacle = create_obstacle_polygon(position, size)
planner.add_dynamic_obstacle(obstacle)

# Automatische Neuplanung wird ausgelöst
```

## Features

### Pfadsegmente

Jeder Pfad wird in Segmente unterteilt mit Metadaten:

- **Pfadtyp**: Mähen, Transit, Rückkehr, Umrandung, Hindernisvermeidung
- **Geschwindigkeitsfaktor**: Anpassung der Fahrgeschwindigkeit
- **Mäh-Status**: Ob während des Segments gemäht werden soll
- **Priorität**: Für Segmentreihenfolge
- **Geschätzte Zeit**: Für Zeitplanung

### Intelligente Zonenerkennung

```python
# Automatische Strategieauswahl
if obstacle_density > 0.3 or zone_complexity > 0.7:
    # Hohe Komplexität -> A*
    strategy = PlanningStrategy.ASTAR
elif zone_area < 50.0:
    # Kleine Zone -> Spiral
    strategy = PlanningStrategy.TRADITIONAL
else:
    # Standard -> Hybrid
    strategy = PlanningStrategy.HYBRID
```

### Neuplanung

Automatische Neuplanung bei:
- Dynamischen Hindernissen
- Pfadblockierungen
- GPS-Signalverlust
- Sensorfehlern

## Integration

### Mit GPS-Navigation

```python
# GPS-Navigation mit erweiterter Pfadplanung
gps_navigation = GPSNavigation(gps, advanced_planner)
```

### Mit Motor-Steuerung

```python
# Navigation Target setzen
nav_target = planner.get_navigation_target()
if nav_target:
    motor.set_navigation_target(nav_target[0], nav_target[1])
```

### MQTT-Telemetrie

```python
# Planungsstatistiken abrufen
status = planner.get_planning_status()

# Über MQTT senden
mqtt.publish("sunray/path_planning", status)
```

## Callbacks

### Ereignis-Callbacks

```python
# Hindernis erkannt
planner.set_obstacle_detected_callback(
    lambda obstacle: print(f"Hindernis erkannt: {obstacle}")
)

# Neuplanung durchgeführt
planner.set_replanning_callback(
    lambda count: print(f"Neuplanung #{count}")
)

# Segment abgeschlossen
planner.set_segment_completed_callback(
    lambda segment: print(f"Segment {segment.path_type} abgeschlossen")
)
```

## Statistiken

### Planungsstatistiken

```python
status = planner.get_planning_status()

print(f"Strategie: {status['strategy']}")
print(f"Fortschritt: {status['progress']:.1%}")
print(f"Geplante Distanz: {status['total_planned_distance']:.1f}m")
print(f"Neuplanungen: {status['replanning_count']}")
print(f"Planungszeit: {status['last_planning_time']:.2f}s")
```

### Performance-Metriken

- **Planungszeit**: Zeit für Pfadgenerierung
- **Pfadlänge**: Gesamtlänge des geplanten Pfads
- **Neuplanungen**: Anzahl dynamischer Neuplanungen
- **Segmentanzahl**: Anzahl der Pfadsegmente
- **Abdeckungsrate**: Prozent der abgedeckten Fläche

## Optimierung

### Performance-Tipps

1. **Grid-Größe**: Kleinere Grids für höhere Präzision, größere für Performance
2. **Heuristik-Gewichtung**: Höhere Werte für schnellere, aber suboptimale Pfade
3. **Segment-Länge**: Längere Segmente für weniger Overhead
4. **Obstacle Inflation**: Balance zwischen Sicherheit und Effizienz

### Speicher-Optimierung

- Pfadsegmente werden bei Bedarf geladen
- Alte Segmente werden automatisch freigegeben
- Dynamische Hindernisse haben Timeout

## Fehlerbehandlung

### Fallback-Strategien

1. **A*-Fehler**: Fallback auf traditionelle Muster
2. **Keine Lösung**: Vereinfachte Pfade oder manuelle Intervention
3. **GPS-Verlust**: Odometrie-basierte Navigation
4. **Speicher-Limit**: Segmentweise Planung

### Debugging

```python
# Debug-Modus aktivieren
planner.set_debug_mode(True)

# Pfad visualisieren
planner.visualize_current_plan()

# Statistiken ausgeben
planner.print_debug_info()
```

## Erweiterungen

### Zukünftige Features

- **Machine Learning**: Adaptive Parameteranpassung
- **Multi-Robot**: Koordination mehrerer Mähroboter
- **Weather Integration**: Wetterbasierte Pfadanpassung
- **3D-Planung**: Höhenbasierte Navigation
- **Predictive Planning**: Vorhersage-basierte Optimierung

### Plugin-System

```python
# Custom Strategy Plugin
class CustomStrategy(PlanningStrategy):
    def plan(self, zones, obstacles):
        # Custom implementation
        pass

# Plugin registrieren
planner.register_strategy("custom", CustomStrategy())
```

## Troubleshooting

### Häufige Probleme

1. **Langsame Planung**: Grid-Größe vergrößern, max_iterations reduzieren
2. **Suboptimale Pfade**: Heuristik-Gewichtung anpassen
3. **Häufige Neuplanung**: Replanning-Threshold erhöhen
4. **Speicher-Probleme**: Segment-Länge erhöhen

### Log-Analyse

```bash
# Planungszeiten analysieren
grep "Pfadplanung:" sunray.log | tail -20

# Neuplanungen verfolgen
grep "Neuplanung" sunray.log | wc -l

# Fehler finden
grep "ERROR.*path" sunray.log
```

## Beispiele

### Einfache Konfiguration

```python
# Minimale Konfiguration für kleine Gärten
planner = AdvancedPathPlanner()
planner.set_strategy(PlanningStrategy.TRADITIONAL)
planner.plan_zone_coverage(MowPattern.LINES)
```

### Komplexe Umgebung

```python
# Optimiert für viele Hindernisse
planner = AdvancedPathPlanner()
planner.set_strategy(PlanningStrategy.HYBRID)
planner.obstacle_detection_radius = 1.5
planner.plan_zone_coverage(MowPattern.LINES)
```

### Adaptive Konfiguration

```python
# Automatische Anpassung
planner = AdvancedPathPlanner()
planner.set_strategy(PlanningStrategy.ADAPTIVE)
planner.plan_zone_coverage()  # Pattern wird automatisch gewählt
```

---

*Dokumentation erstellt für Sunray Python Implementation v1.0*
*Letzte Aktualisierung: 2024*