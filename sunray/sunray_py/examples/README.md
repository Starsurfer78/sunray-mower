# Sunray Python Examples

Dieser Ordner enthält Beispielskripte und Demonstrationen für verschiedene Funktionalitäten des Sunray Python Mähroboter-Systems.

## 📁 Verfügbare Beispiele

### 🔊 Buzzer Feedback
- **`buzzer_example.py`** - Demonstriert das Buzzer-Feedback-System
  - System-Events (Start, WiFi, GPS, Shutdown)
  - Navigations-Events (Hindernis, Neigung, Mähen)
  - Enhanced System Events (Escape-Operationen)
  - Warn-Events (Batterie, Motor, Sensoren)
  - Ton-Sequenzen und globales Feedback-System

### 🤖 System Integration
- **`integration_example.py`** - Zeigt die Integration des Enhanced Escape Systems
  - Erweiterte Sunray-Steuerung mit intelligenten Ausweichmanövern
  - Sensorfusion und Self-Learning Integration
  - Hardware/Mock-Hardware Fallback-System
  - Buzzer-Feedback Integration
  - Hauptschleife mit Enhanced Escape Logik

### 🌱 Autonomes Mähen
- **`example_autonomous_mowing.py`** - Demonstriert autonome Mähfunktionalität
  - Verschiedene Mähmuster (Linien, Spiral, Zufall)
  - Pfadplanung mit Zonen und Hindernissen
  - Motor-Integration und Navigation
  - Praktische Anwendungsbeispiele

## 🚀 Verwendung

### Voraussetzungen
```bash
cd sunray_py
pip install -r requirements.txt
```

### Beispiele ausführen
```bash
# Buzzer-Demo
python examples/buzzer_example.py

# Integration-Demo
python examples/integration_example.py

# Autonomes Mähen Demo
python examples/example_autonomous_mowing.py
```

## 📝 Hinweise

- Alle Beispiele verwenden Mock-Hardware, wenn echte Hardware nicht verfügbar ist
- Die Skripte sind vollständig dokumentiert und erklären jeden Schritt
- Ideal zum Lernen und Verstehen der Systemarchitektur
- Können als Basis für eigene Implementierungen verwendet werden

## 🔧 Anpassung

Die Beispiele können einfach angepasst werden:
- Konfigurationsparameter in den Skripten ändern
- Eigene Callback-Funktionen hinzufügen
- Hardware-spezifische Anpassungen vornehmen
- Als Vorlage für neue Funktionalitäten verwenden