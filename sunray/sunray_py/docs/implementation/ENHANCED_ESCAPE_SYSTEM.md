# Enhanced Escape System mit Sensorfusion und Self-Learning

## Überblick

Das Enhanced Escape System erweitert die bestehenden Ausweichmanöver um intelligente Sensorfusion und selbstlernende Algorithmen. Es kombiniert GPS-, IMU-, Odometrie- und Stromsensordaten für kontextbewusste Entscheidungen und lernt aus Erfahrungen für optimierte Ausweichstrategien.

## Architektur

### 1. SensorFusion-Klasse

#### Zweck
- Kombiniert alle verfügbaren Sensordaten zu einem kohärenten Zustandsbild
- Bewertet Vertrauenswürdigkeit einzelner Sensoren dynamisch
- Erkennt Bewegungsmuster und Hinderniskontexte

#### Kernfunktionen

**Erweiterte Kalman-Filter:**
```python
# Positionsschätzung mit 4D-Zustandsvektor [x, y, vx, vy]
self.position_filter = {
    'state': np.array([0.0, 0.0, 0.0, 0.0]),
    'covariance': np.eye(4) * 0.1,
    'process_noise': np.eye(4) * 0.01,
    'measurement_noise': np.eye(2) * 0.1
}
```

**Dynamische Sensor-Gewichtung:**
- GPS: Gewichtung basierend auf Fix-Qualität (RTK > 3D > 2D)
- IMU: Vertrauen abhängig von Kalibrierungsstatus und Stabilität
- Odometrie: Reduziert bei Motorüberlastungen
- Stromsensoren: Konstant hohe Zuverlässigkeit

**Intelligente Winkelfusion:**
```python
def _fuse_angles(self, angle1, angle2, weight1, weight2):
    # Konvertierung zu Einheitsvektoren für 360°-sichere Mittelung
    x1, y1 = cos(radians(angle1)), sin(radians(angle1))
    x2, y2 = cos(radians(angle2)), sin(radians(angle2))
    
    # Gewichtete Vektormittelung
    x_fused = (x1 * weight1 + x2 * weight2) / (weight1 + weight2)
    y_fused = (y1 * weight1 + y2 * weight2) / (weight1 + weight2)
    
    return degrees(atan2(y_fused, x_fused))
```

#### Bewegungsanalyse

**Anomalieerkennung:**
- `collision`: Starke Beschleunigung (>15 m/s²)
- `spinning`: Hohe Rotationsrate (>2 rad/s)
- `stuck`: Motorüberlastung bei geringer Bewegung
- `normal`: Reguläre Bewegung

**Hinderniskontext-Analyse:**
- Richtungsbestimmung aus Motorströmen und IMU-Daten
- Schweregradeinschätzung basierend auf Sensormagnitude
- Klassifizierung: `current_spike`, `physical_collision`, `unknown`

### 2. LearningSystem-Klasse

#### Zweck
- Sammelt Erfahrungen aus Ausweichmanövern
- Optimiert Strategieparameter basierend auf Erfolgsraten
- Empfiehlt beste Strategien für gegebene Kontexte

#### Datenstruktur

```json
{
  "escape_strategies": {
    "current_spike_front_smooth": [
      {
        "strategy": "smart_bumper_escape",
        "parameters": {"reverse_duration": 1.0, "curve_duration": 3.0},
        "success": true,
        "duration": 4.2,
        "timestamp": 1703123456.789
      }
    ]
  },
  "success_rates": {
    "current_spike_front_smooth_smart_bumper_escape": {
      "successes": 8,
      "attempts": 10
    }
  },
  "parameter_optimizations": {
    "current_spike_front_smooth_smart_bumper_escape": {
      "optimal_params": {"reverse_duration": 0.8, "curve_duration": 2.5},
      "best_duration": 3.1,
      "sample_count": 8
    }
  }
}
```

#### Kontext-Klassifizierung

**Kontextschlüssel-Format:** `{obstacle_type}_{obstacle_direction}_{terrain_type}`

Beispiele:
- `current_spike_left_rough`
- `physical_collision_front_smooth`
- `unknown_right_moderate`

**Terrain-Klassifizierung:**
- `smooth`: Stabilität > 0.7
- `moderate`: Stabilität 0.3-0.7
- `rough`: Stabilität < 0.3

#### Lernalgorithmus

**Erfolgsraten-Update:**
```python
def _update_success_rates(self, context_key, strategy, success):
    rate_key = f"{context_key}_{strategy}"
    self.learning_data['success_rates'][rate_key]['attempts'] += 1
    if success:
        self.learning_data['success_rates'][rate_key]['successes'] += 1
```

**Parameter-Optimierung:**
- Gewichtete Mittelung erfolgreicher Parameter
- Bevorzugung schnellerer Ausführungszeiten
- Mindestanzahl Samples für statistisch relevante Optimierung

### 3. AdaptiveEscapeOp-Klasse

#### Phasen-basierte Ausführung

1. **Analyze-Phase (0.2s):**
   - Sensorfusion durchführen
   - Kontext analysieren
   - Optimale Strategie auswählen
   - Motoren stoppen

2. **Maneuver-Phase (variabel):**
   - Gewählte Strategie ausführen
   - Kontinuierliche Überwachung
   - Dynamische Anpassungen

3. **Recovery-Phase (1.0s):**
   - Stabilisierung
   - Vorbereitung für normale Operation
   - Lernergebnis aufzeichnen

#### Verfügbare Strategien

**Smart Bumper Escape:**
- Richtungsabhängiges Ausweichen
- Optimiert für physische Kollisionen
- Parameter: `reverse_duration`, `curve_duration`, `linear_speed`, `angular_speed`

**Escape Forward:**
- Universelle Ausweichstrategie
- Pause → Vorwärts → Rotation
- Parameter: `pause_duration`, `forward_duration`, `rotate_duration`

**Adaptive Escape:**
- Vollständig kontextabhängige Strategie
- Dynamische Geschwindigkeits- und Richtungsanpassung
- Parameter: `maneuver_duration`, `max_speed`, `aggressiveness`

## Integration in das bestehende System

### 1. Hauptschleife (main.py)

```python
# Erweiterte Hinderniserkennung
if obstacle_detected:
    # Sensordaten sammeln
    escape_params = {
        'gps_data': gps_data,
        'imu_data': imu_data,
        'odometry_data': motor.get_odometry_data(),
        'current_data': motor.get_current_data()
    }
    
    # Adaptive Escape-Operation starten
    current_op = AdaptiveEscapeOp("adaptive_escape", motor)
    current_op.start(escape_params)
```

### 2. Konfiguration (config.json)

```json
{
  "enhanced_escape": {
    "enabled": true,
    "learning_enabled": true,
    "learning_file": "escape_learning_data.json",
    "min_samples_for_learning": 5,
    "learning_rate": 0.1,
    "sensor_fusion": {
      "gps_weight": 0.4,
      "imu_weight": 0.3,
      "odometry_weight": 0.2,
      "current_weight": 0.1
    }
  }
}
```

### 3. Monitoring und Debugging

**Lernstatistiken abrufen:**
```python
learning_system = LearningSystem()
stats = learning_system.get_learning_statistics()
print(f"Erfolgsrate: {stats['overall_success_rate']:.2%}")
print(f"Gelernte Kontexte: {stats['learned_contexts']}")
```

**HTTP-API-Endpunkt:**
```python
@app.route('/api/escape/stats')
def get_escape_stats():
    return jsonify(learning_system.get_learning_statistics())
```

## Vorteile des Enhanced Systems

### 1. Intelligente Sensorfusion
- **Robustheit:** Ausfall einzelner Sensoren wird kompensiert
- **Präzision:** Kombination mehrerer Datenquellen erhöht Genauigkeit
- **Adaptivität:** Dynamische Gewichtung je nach Sensorqualität

### 2. Kontextbewusste Entscheidungen
- **Terrain-Anpassung:** Verschiedene Strategien für unterschiedliche Untergründe
- **Hindernistyp-Erkennung:** Spezifische Reaktionen auf verschiedene Hindernisarten
- **Richtungsoptimierung:** Ausweichen in optimale Richtung basierend auf Kontext

### 3. Kontinuierliches Lernen
- **Selbstoptimierung:** System wird mit der Zeit besser
- **Anpassung an Umgebung:** Lernt spezifische Eigenschaften des Einsatzgebiets
- **Parameteroptimierung:** Automatische Feinabstimmung der Manöverparameter

### 4. Datengetriebene Verbesserungen
- **Erfolgsraten-Tracking:** Objektive Bewertung der Strategieeffektivität
- **Performance-Optimierung:** Minimierung der Ausweichzeiten
- **Predictive Analytics:** Vorhersage problematischer Bereiche

## Implementierungsschritte

### Phase 1: Grundintegration
1. Enhanced Escape Operations in main.py integrieren
2. Konfigurationsparameter hinzufügen
3. Basis-Sensorfusion implementieren

### Phase 2: Learning-System
1. Datensammlung aktivieren
2. Erfolgsraten-Tracking implementieren
3. Parameter-Optimierung einführen

### Phase 3: Erweiterte Features
1. Predictive Analytics
2. Terrain-Mapping
3. Proaktive Hinderniserkennung

### Phase 4: Optimierung
1. Performance-Tuning
2. Speicher-Optimierung
3. Real-time Anpassungen

## Monitoring und Wartung

### Logging
- Alle Ausweichmanöver werden mit Kontext und Ergebnis protokolliert
- Sensorfusion-Entscheidungen werden nachvollziehbar dokumentiert
- Learning-Updates werden mit Zeitstempel gespeichert

### Debugging
- Visualisierung der Sensorfusion-Gewichtungen
- Analyse der Lernfortschritte über Zeit
- Identifikation problematischer Kontexte

### Wartung
- Regelmäßige Bereinigung alter Lerndaten
- Backup der optimierten Parameter
- Überwachung der Systemperformance

## Fazit

Das Enhanced Escape System stellt einen bedeutenden Fortschritt gegenüber den statischen Ausweichmanövern dar. Durch die Kombination von Sensorfusion und maschinellem Lernen wird das System:

- **Intelligenter:** Kontextbewusste Entscheidungen statt starrer Sequenzen
- **Adaptiver:** Anpassung an verschiedene Umgebungen und Situationen
- **Selbstoptimierend:** Kontinuierliche Verbesserung durch Erfahrungssammlung
- **Robuster:** Ausfall-tolerant durch Sensorfusion
- **Effizienter:** Optimierte Parameter für minimale Ausweichzeiten

Die Implementierung ermöglicht es dem Sunray-System, von einem reaktiven zu einem proaktiven und lernenden Roboter zu werden, der sich kontinuierlich an seine Umgebung anpasst und optimiert.