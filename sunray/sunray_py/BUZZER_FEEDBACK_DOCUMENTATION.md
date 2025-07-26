# Buzzer Feedback System Documentation

## Übersicht

Das Buzzer Feedback System bietet akustisches Feedback für verschiedene Ereignisse und Operationen im Sunray Enhanced Navigation System. Es ermöglicht dem Benutzer, den Status des Roboters auch ohne visuelle Überwachung zu verstehen.

## Komponenten

### 1. BuzzerTone Enum

Definiert verschiedene Töne für unterschiedliche Ereignistypen:

#### System-Töne
- `SYSTEM_STARTUP` (800Hz, 200ms) - System startet
- `SYSTEM_READY` (1000Hz, 300ms) - System bereit
- `SYSTEM_SHUTDOWN` (600Hz, 500ms) - System fährt herunter
- `SYSTEM_ERROR` (400Hz, 1000ms) - Systemfehler

#### Navigations-Töne
- `NAVIGATION_START` (1200Hz, 250ms) - Navigation startet
- `NAVIGATION_COMPLETE` (1500Hz, 400ms) - Navigation abgeschlossen
- `OBSTACLE_DETECTED` (900Hz, 150ms) - Hindernis erkannt
- `PATH_BLOCKED` (700Hz, 300ms) - Pfad blockiert

#### Warn-Töne
- `WARNING_BATTERY_LOW` (500Hz, 200ms) - Batterie schwach
- `WARNING_MOTOR_OVERLOAD` (450Hz, 250ms) - Motor überlastet
- `WARNING_SENSOR_ERROR` (550Hz, 300ms) - Sensorfehler
- `WARNING_GENERAL` (600Hz, 200ms) - Allgemeine Warnung
- `TILT_WARNING` (350Hz, 500ms) - Neigungswarnung

#### Enhanced System Töne
- `ENHANCED_ESCAPE_START` (1100Hz, 200ms) - Enhanced Escape startet
- `ENHANCED_ESCAPE_SUCCESS` (1400Hz, 300ms) - Enhanced Escape erfolgreich
- `ENHANCED_ESCAPE_FAILED` (500Hz, 400ms) - Enhanced Escape fehlgeschlagen
- `ENHANCED_ESCAPE_FALLBACK` (800Hz, 250ms) - Fallback zu traditionellem Escape
- `LEARNING_UPDATE` (1300Hz, 150ms) - Learning System Update
- `SENSOR_FUSION_ACTIVE` (1600Hz, 100ms) - Sensorfusion aktiv

### 2. BuzzerFeedback Klasse

Hauptklasse für Buzzer-Steuerung:

```python
class BuzzerFeedback:
    def __init__(self, hardware_manager, enabled=True)
    def play_tone(self, tone: BuzzerTone) -> bool
    def play_sequence(self, sequence: List[Tuple]) -> bool
    def handle_event(self, event_code: EventCode) -> bool
    def set_enabled(self, enabled: bool)
    def is_enabled(self) -> bool
```

#### Methoden

##### `play_tone(tone: BuzzerTone)`
Spielt einen einzelnen Ton ab.

**Parameter:**
- `tone`: BuzzerTone Enum-Wert

**Rückgabe:**
- `bool`: True bei Erfolg, False bei Fehler

##### `play_sequence(sequence: List[Tuple])`
Spielt eine Sequenz von Tönen ab.

**Parameter:**
- `sequence`: Liste von Tupeln (BuzzerTone, Pause_in_Sekunden)

**Beispiel:**
```python
sequence = [
    (BuzzerTone.SYSTEM_STARTUP, 0.2),
    (BuzzerTone.SYSTEM_READY, 0.3)
]
buzzer.play_sequence(sequence)
```

##### `handle_event(event_code: EventCode)`
Behandelt Ereignisse automatisch mit entsprechenden Tönen.

**Parameter:**
- `event_code`: EventCode Enum-Wert

**Unterstützte Events:**
- `SYSTEM_STARTED` → `SYSTEM_STARTUP`
- `SYSTEM_SHUTTING_DOWN` → `SYSTEM_SHUTDOWN`
- `OBSTACLE_DETECTED` → `OBSTACLE_DETECTED`
- `TILT_WARNING` → `TILT_WARNING`
- `ERROR_*` → `SYSTEM_ERROR`

### 3. Globales Buzzer System

```python
from buzzer_feedback import get_buzzer_feedback

# Globales Buzzer-System initialisieren
buzzer_feedback = get_buzzer_feedback(hardware_manager)

# Ereignis behandeln
buzzer_feedback.handle_event(EventCode.OBSTACLE_DETECTED)
```

## Integration

### 1. Hardware Manager Integration

Der Hardware Manager muss die `send_buzzer_command` Methode implementieren:

```python
class HardwareManager:
    def send_buzzer_command(self, frequency: int, duration: int) -> bool:
        """Sendet Buzzer-Befehl an Hardware.
        
        Args:
            frequency: Frequenz in Hz
            duration: Dauer in Millisekunden
            
        Returns:
            bool: True bei Erfolg
        """
        # Hardware-spezifische Implementierung
        pass
```

### 2. Enhanced Sunray Controller Integration

```python
from buzzer_feedback import BuzzerFeedback, get_buzzer_feedback
from events import EventCode

class EnhancedSunrayController:
    def __init__(self):
        # Buzzer-Feedback initialisieren
        self.buzzer_feedback = get_buzzer_feedback(self.hardware_manager)
        
    def run_main_loop(self):
        # System-Start Feedback
        self.buzzer_feedback.handle_event(EventCode.SYSTEM_STARTED)
        
        try:
            while True:
                # Hinderniserkennung
                if obstacle_detected:
                    self.buzzer_feedback.handle_event(EventCode.OBSTACLE_DETECTED)
                    
                # Enhanced Escape
                if enhanced_escape_started:
                    self.buzzer_feedback.play_tone(BuzzerTone.ENHANCED_ESCAPE_START)
                    
        except KeyboardInterrupt:
            self.buzzer_feedback.handle_event(EventCode.SYSTEM_SHUTTING_DOWN)
```

### 3. Mock Hardware für Tests

```python
class MockHardwareManager:
    def send_buzzer_command(self, frequency, duration):
        print(f"MOCK BUZZER: {frequency}Hz für {duration}ms")
        return True
```

## Konfiguration

### Buzzer aktivieren/deaktivieren

```python
# Buzzer deaktivieren
buzzer_feedback.set_enabled(False)

# Status prüfen
if buzzer_feedback.is_enabled():
    buzzer_feedback.play_tone(BuzzerTone.SYSTEM_READY)
```

### Konfigurationsdatei

```json
{
  "buzzer": {
    "enabled": true,
    "volume": 80,
    "system_events": true,
    "navigation_events": true,
    "warning_events": true,
    "enhanced_events": true
  }
}
```

## Verwendungsbeispiele

### Einfache Tonwiedergabe

```python
from buzzer_feedback import BuzzerFeedback, BuzzerTone

buzzer = BuzzerFeedback(hardware_manager)
buzzer.play_tone(BuzzerTone.SYSTEM_READY)
```

### Ereignisbehandlung

```python
from events import EventCode

# Automatische Ereignisbehandlung
buzzer.handle_event(EventCode.OBSTACLE_DETECTED)
buzzer.handle_event(EventCode.TILT_WARNING)
```

### Ton-Sequenzen

```python
# Startup-Sequenz
startup_sequence = [
    (BuzzerTone.SYSTEM_STARTUP, 0.2),
    (BuzzerTone.SYSTEM_READY, 0.3),
    (BuzzerTone.NAVIGATION_START, 0.2)
]
buzzer.play_sequence(startup_sequence)

# Alarm-Sequenz
alarm_sequence = [
    (BuzzerTone.WARNING_GENERAL, 0.1),
    (None, 0.1),  # Pause
    (BuzzerTone.WARNING_GENERAL, 0.1),
    (None, 0.1),
    (BuzzerTone.WARNING_GENERAL, 0.1)
]
buzzer.play_sequence(alarm_sequence)
```

### Enhanced System Integration

```python
# Enhanced Escape Feedback
def execute_enhanced_escape(self):
    try:
        # Start-Feedback
        self.buzzer_feedback.play_tone(BuzzerTone.ENHANCED_ESCAPE_START)
        
        # Escape ausführen
        success = self.perform_escape()
        
        if success:
            self.buzzer_feedback.play_tone(BuzzerTone.ENHANCED_ESCAPE_SUCCESS)
        else:
            self.buzzer_feedback.play_tone(BuzzerTone.ENHANCED_ESCAPE_FAILED)
            
    except Exception as e:
        self.buzzer_feedback.play_tone(BuzzerTone.ENHANCED_ESCAPE_FAILED)
```

## Fehlerbehebung

### Häufige Probleme

1. **Buzzer funktioniert nicht**
   - Hardware Manager `send_buzzer_command` Methode prüfen
   - Buzzer-Status mit `is_enabled()` prüfen
   - Hardware-Verbindung prüfen

2. **Töne werden nicht abgespielt**
   - Frequenz- und Dauerwerte prüfen
   - Hardware-Unterstützung für Frequenzbereich prüfen

3. **Sequenzen werden unterbrochen**
   - Threading-Konflikte prüfen
   - Ausreichende Pausen zwischen Tönen sicherstellen

### Debug-Modus

```python
# Mock Hardware für Debugging
class DebugHardwareManager:
    def send_buzzer_command(self, frequency, duration):
        print(f"DEBUG BUZZER: {frequency}Hz für {duration}ms")
        return True

buzzer = BuzzerFeedback(DebugHardwareManager())
```

## Erweiterungen

### Neue Töne hinzufügen

```python
class BuzzerTone(Enum):
    # Bestehende Töne...
    
    # Neue Töne
    CUSTOM_TONE = (1800, 200)  # 1800Hz, 200ms
    SPECIAL_EVENT = (2000, 100)  # 2000Hz, 100ms
```

### Ereignis-Mapping erweitern

```python
def handle_event(self, event_code: EventCode) -> bool:
    # Bestehende Mappings...
    
    # Neue Mappings
    if event_code == EventCode.CUSTOM_EVENT:
        return self.play_tone(BuzzerTone.CUSTOM_TONE)
```

## Performance

- Töne werden asynchron abgespielt
- Minimale CPU-Belastung
- Keine Blockierung der Hauptschleife
- Effiziente Hardware-Kommunikation

## Sicherheit

- Frequenzbegrenzung (50Hz - 5000Hz)
- Dauerbegrenzung (max. 2000ms)
- Automatische Fehlerbehandlung
- Hardware-Fallback bei Fehlern