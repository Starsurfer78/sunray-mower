# Enhanced Escape System für Sunray Mähroboter

## Überblick

Das Enhanced Escape System erweitert den Sunray Mähroboter um intelligente Ausweichmanöver durch **Sensorfusion** und **Self-Learning**. Es kombiniert GPS-, IMU-, Odometrie- und Stromsensordaten, um kontextbewusste Entscheidungen zu treffen und aus Erfahrungen zu lernen.

## Kernkomponenten

### 1. Sensorfusion (`SensorFusion`)

**Zweck**: Kombiniert mehrere Sensordatenquellen zu einem einheitlichen, vertrauenswürdigen Zustandsbild.

**Features**:
- Dynamische Gewichtung der Sensoren basierend auf Zuverlässigkeit
- Bewegungsmuster-Analyse (Kollision, Durchdrehen, Feststecken)
- Kontextklassifizierung für verschiedene Hindernistypen
- Adaptive Vertrauenswerte für jeden Sensor

**Eingangsdaten**:
```python
{
    'gps_data': {'lat': float, 'lon': float, 'accuracy': float},
    'imu_data': {'accel': [x,y,z], 'gyro': [x,y,z], 'heading': float},
    'odometry_data': {'distance': float, 'speed': float, 'direction': float},
    'current_data': {'left_motor': float, 'right_motor': float, 'mow_motor': float}
}
```

### 2. Lernsystem (`LearningSystem`)

**Zweck**: Lernt aus erfolgreichen und fehlgeschlagenen Ausweichmanövern, um zukünftige Strategien zu optimieren.

**Features**:
- Kontextbasierte Strategieempfehlungen
- Parameter-Optimierung durch Erfahrung
- Erfolgsrate-Tracking pro Kontext
- Adaptive Exploration vs. Exploitation

**Lernbare Parameter**:
- Ausweichdistanz
- Drehwinkel
- Geschwindigkeitsprofil
- Pausendauer
- Wiederherstellungspfad

### 3. Adaptive Ausweichoperation (`AdaptiveEscapeOp`)

**Zweck**: Führt intelligente, kontextabhängige Ausweichmanöver durch.

**Phasen**:
1. **Analyse**: Sensorfusion und Kontextbestimmung
2. **Manöver**: Ausführung der optimalen Strategie
3. **Wiederherstellung**: Rückkehr zum normalen Betrieb
4. **Lernen**: Bewertung und Speicherung der Erfahrung

## Implementierung

### Installation

1. **Dateien kopieren**:
   ```bash
   cp enhanced_escape_operations.py /path/to/sunray/
   cp integration_example.py /path/to/sunray/
   cp config_enhanced_example.json /path/to/sunray/config.json
   ```

2. **Abhängigkeiten installieren**:
   ```bash
   pip install numpy scipy scikit-learn
   ```

### Integration in bestehende main.py

```python
# Bestehende Imports erweitern
from enhanced_escape_operations import SensorFusion, LearningSystem, AdaptiveEscapeOp

# In der Hauptklasse initialisieren
class SunrayController:
    def __init__(self):
        # ... bestehende Initialisierung
        
        # Enhanced Escape Komponenten
        self.sensor_fusion = SensorFusion()
        self.learning_system = LearningSystem()
        self.enhanced_escape_enabled = True
    
    def handle_obstacle_detection(self, sensor_data, robot_state):
        if self.enhanced_escape_enabled:
            # Sensorfusion
            fused_context = self.sensor_fusion.fuse_sensor_data(
                sensor_data['gps_data'],
                sensor_data['imu_data'], 
                sensor_data['odometry_data'],
                sensor_data['current_data']
            )
            
            # Strategieempfehlung
            strategy, params, confidence = self.learning_system.get_recommended_strategy(fused_context)
            
            if confidence > 0.7:  # Mindestvertrauen
                # Enhanced Escape ausführen
                escape_op = AdaptiveEscapeOp("enhanced_escape", self.motor)
                escape_op.start({
                    'fused_context': fused_context,
                    'robot_position': robot_state,
                    **sensor_data
                })
                return
        
        # Fallback auf traditionelle Methoden
        self.execute_traditional_escape(sensor_data)
```

### Konfiguration

Die Konfiguration erfolgt über `config.json`:

```json
{
  "enhanced_escape": {
    "enabled": true,
    "sensor_fusion": {
      "sensor_weights": {
        "gps_weight": 0.4,
        "imu_weight": 0.3,
        "odometry_weight": 0.2,
        "current_weight": 0.1
      }
    },
    "learning_system": {
      "learning_rate": 0.1,
      "min_samples_for_learning": 5
    },
    "escape_strategies": {
      "adaptive_escape_threshold": 0.7,
      "fallback_to_traditional": true
    }
  }
}
```

## Erkannte Kontexte

Das System klassifiziert verschiedene Hindernissituationen:

| Kontext | Beschreibung | Typische Strategie |
|---------|--------------|-------------------|
| `current_spike_front_smooth` | Durchdrehen auf glattem Untergrund | Rückwärts + Kurve |
| `current_spike_front_rough` | Durchdrehen auf rauem Untergrund | Seitliche Umfahrung |
| `bumper_collision_front` | Frontale Bumper-Kollision | Smart Bumper Escape |
| `bumper_collision_corner` | Eck-Kollision | Angepasster Winkel |
| `stuck_spinning` | Festgefahren mit Durchdrehen | Spiral-Escape |
| `stuck_blocked` | Komplett blockiert | Mehrfach-Rückwärts |
| `slope_too_steep` | Zu steile Neigung | Kontrollierter Abstieg |
| `boundary_approach` | Annäherung an Grenze | Sanfte Richtungsänderung |

## Ausweichstrategien

### 1. Adaptive Reverse Turn
- **Anwendung**: Frontale Hindernisse auf ebenem Gelände
- **Ablauf**: Rückwärts → Drehung (adaptiver Winkel) → Vorwärts
- **Lernparameter**: Rückwärtsdistanz, Drehwinkel, Vorwärtsdistanz

### 2. Smart Side Escape
- **Anwendung**: Seitliche Hindernisse oder Ecken
- **Ablauf**: Seitliche Bewegung → Kurvenfahrt → Rückkehr
- **Lernparameter**: Seitendistanz, Kurvenradius, Geschwindigkeit

### 3. Spiral Escape
- **Anwendung**: Festgefahrene Situationen
- **Ablauf**: Spiralförmige Bewegung mit zunehmendem Radius
- **Lernparameter**: Startradius, Radiusinkrement, Spiralwindungen

### 4. Slope Descent
- **Anwendung**: Zu steile Neigungen
- **Ablauf**: Kontrollierter Abstieg in sicherem Winkel
- **Lernparameter**: Abstiegswinkel, Geschwindigkeitsbegrenzung

## Monitoring und Debugging

### Logging
```python
# Enhanced Escape spezifische Logs
Logger.event(EventCode.ENHANCED_ESCAPE_STARTED, 
            f"Context: {context}, Strategy: {strategy}, Confidence: {confidence}")

Logger.event(EventCode.LEARNING_UPDATE, 
            f"Strategy {strategy} success rate: {success_rate:.2%}")
```

### API-Endpunkte
```bash
# Status abrufen
GET /api/enhanced/status

# Learning-Statistiken
GET /api/enhanced/learning/stats

# Enhanced Escape aktivieren/deaktivieren
POST /api/enhanced/escape/enable
{"enabled": true}

# Learning-Daten zurücksetzen
POST /api/enhanced/learning/reset
```

### Statistiken
```python
stats = controller.get_status()
print(f"Enhanced Escape Rate: {stats['enhanced_escape_rate']:.2%}")
print(f"Overall Success Rate: {stats['overall_success_rate']:.2%}")
print(f"Learned Contexts: {stats['learned_contexts']}")
```

## Sicherheitsfeatures

### Fail-Safe Mechanismen
- **Timeout**: Maximale Ausweichdauer (30s)
- **Sensor-Überwachung**: Automatischer Fallback bei Sensorausfall
- **Neigungsüberwachung**: Sofortiger Stopp bei gefährlicher Neigung
- **Stromüberwachung**: Schutz vor Motorüberlastung

### Notfall-Bedingungen
- Neigungswinkel überschritten
- GPS-Signal verloren
- Mehrfach-Sensorausfall
- Kritische Stromüberlastung

### Recovery-Bedingungen
- Alle Sensoren stabil
- Position bestätigt
- Keine Hindernisse erkannt

## Performance-Optimierung

### Sensorfusion
- **Update-Frequenz**: 10 Hz (konfigurierbar)
- **Adaptive Gewichtung**: Dynamische Anpassung basierend auf Sensorqualität
- **Caching**: Zwischenspeicherung häufig verwendeter Berechnungen

### Lernsystem
- **Batch-Learning**: Periodische Updates statt kontinuierlicher Anpassung
- **Daten-Kompression**: Effiziente Speicherung von Lerndaten
- **Lazy Loading**: Strategien werden nur bei Bedarf geladen

## Wartung und Updates

### Regelmäßige Aufgaben
1. **Learning-Daten sichern**: Wöchentliche Backups
2. **Erfolgsraten prüfen**: Monatliche Analyse
3. **Sensor-Kalibrierung**: Bei Bedarf
4. **Parameter-Tuning**: Saisonale Anpassungen

### Troubleshooting

**Problem**: Niedrige Erfolgsrate
- **Lösung**: Learning-Parameter anpassen, mehr Trainingsdaten sammeln

**Problem**: Sensorfusion instabil
- **Lösung**: Sensor-Gewichtung überprüfen, Kalibrierung durchführen

**Problem**: Zu aggressive Ausweichmanöver
- **Lösung**: Exploration-Rate reduzieren, konservativere Parameter

## Erweiterungsmöglichkeiten

### Zukünftige Features
- **Computer Vision**: Kamera-basierte Hinderniserkennung
- **Wetter-Integration**: Anpassung an Wetterbedingungen
- **Multi-Robot Learning**: Erfahrungsaustausch zwischen Robotern
- **Predictive Maintenance**: Vorhersage von Wartungsbedarf

### Plugin-Architektur
```python
# Neue Strategien als Plugins
class CustomEscapeStrategy(EscapeStrategy):
    def execute(self, context, params):
        # Benutzerdefinierte Logik
        pass

# Registrierung
learning_system.register_strategy("custom_strategy", CustomEscapeStrategy())
```

## Fazit

Das Enhanced Escape System bringt dem Sunray Mähroboter:

✅ **Intelligente Hinderniserkennung** durch Sensorfusion  
✅ **Adaptive Ausweichmanöver** basierend auf Kontext  
✅ **Kontinuierliches Lernen** aus Erfahrungen  
✅ **Verbesserte Robustheit** in komplexen Situationen  
✅ **Datengetriebene Optimierung** der Performance  

Die Implementierung ist modular aufgebaut und kann schrittweise in bestehende Systeme integriert werden, wobei traditionelle Ausweichmethoden als Fallback erhalten bleiben.