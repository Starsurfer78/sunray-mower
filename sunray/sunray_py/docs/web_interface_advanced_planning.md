# Web-Interface für Erweiterte Pfadplanung

## Übersicht

Das Web-Interface für die erweiterte Pfadplanung bietet eine moderne, benutzerfreundliche Oberfläche zur Konfiguration, Überwachung und Steuerung der intelligenten Pfadplanung des Sunray Mähroboters.

## Features

### 🎯 Hauptfunktionen

- **Interaktive Konfiguration**: Einfache Auswahl von Planungsstrategien und Parametern
- **Echtzeit-Visualisierung**: Live-Darstellung von Pfaden, Zonen und Hindernissen
- **Performance-Monitoring**: Detaillierte Statistiken und Metriken
- **Dynamische Simulation**: Test von Hindernissen und Navigation
- **Export-Funktionen**: Speichern von Logs und Visualisierungen

### 🛠️ Planungsstrategien

1. **Traditional**: Klassische Mähmuster (Linien, Spiral, Zufällig, Umrandung)
2. **A***: Optimale Pfadplanung mit A*-Algorithmus
3. **Hybrid**: Kombination aus traditionellen Mustern und A*-Optimierung
4. **Adaptive**: Automatische Strategieauswahl basierend auf Umgebung

### 📊 Konfigurierbare Parameter

- **Max. Segmentlänge**: Kontrolle der Pfadsegmentierung (1-50m)
- **Hindernis-Erkennungsradius**: Sicherheitsabstand zu Hindernissen (0.1-5m)
- **A* Heuristik-Gewichtung**: Balance zwischen Optimalität und Geschwindigkeit (0.1-3.0)
- **Mähmuster**: Auswahl des Grundmusters für die Flächenabdeckung

## Benutzeroberfläche

### 🎨 Design-Prinzipien

- **Responsive Design**: Optimiert für Desktop, Tablet und Mobile
- **Moderne UI**: Gradient-Designs und glassmorphe Effekte
- **Intuitive Navigation**: Klare Struktur und logische Gruppierung
- **Echtzeit-Feedback**: Sofortige Rückmeldung bei Aktionen

### 📱 Layout-Bereiche

#### Konfiguration
- Strategieauswahl mit Dropdown-Menü
- Parameter-Eingabefelder mit Validierung
- Action-Buttons für Start, Reset und Stopp

#### Status-Panel
- Aktuelle Strategie und Planungsstatus
- Fortschrittsbalken mit Prozentanzeige
- Segmentinformationen und geplante Distanz
- Neuplanungs- und Zeitstatistiken

#### Statistiken
- Gesamte Planungen und Durchschnittszeit
- Erfolgsrate und dynamische Hindernisse
- Performance-Metriken in Karten-Layout

#### Visualisierung
- Interaktive Canvas-Darstellung
- Zoom- und Pan-Funktionen
- Pfad-, Zonen- und Hindernis-Rendering
- Export-Möglichkeiten für Screenshots

#### Logs
- Echtzeit-Protokollierung aller Aktionen
- Farbkodierte Log-Level (Info, Success, Warning, Error)
- Export-Funktion für Textdateien

## API-Integration

### 🔌 REST-Endpunkte

#### Planungssteuerung
```
POST /api/advanced_planning/start
POST /api/advanced_planning/reset
POST /api/advanced_planning/stop
GET  /api/advanced_planning/status
```

#### Dynamische Hindernisse
```
POST /api/advanced_planning/add_obstacle
```

#### Simulation
```
POST /api/advanced_planning/simulate_navigation
```

### 📡 Datenformat

#### Planungsanfrage
```json
{
  "strategy": "hybrid",
  "pattern": "lines",
  "max_segment_length": 10.0,
  "obstacle_detection_radius": 1.0,
  "heuristic_weight": 1.0
}
```

#### Status-Antwort
```json
{
  "strategy": "hybrid",
  "status": "completed",
  "progress": 1.0,
  "total_segments": 25,
  "total_planned_distance": 245.7,
  "replanning_count": 2,
  "last_planning_time": 1.23,
  "statistics": {
    "total_plans": 15,
    "successful_plans": 14,
    "dynamic_obstacles": 3
  }
}
```

## Technische Implementierung

### 🏗️ Frontend-Technologien

- **HTML5**: Semantische Struktur und Canvas-API
- **CSS3**: Grid-Layout, Flexbox, Animationen
- **JavaScript ES6+**: Moderne Syntax und Async/Await
- **Canvas 2D**: Pfad-Visualisierung und Interaktion

### 🔧 Backend-Integration

- **Flask**: Python Web-Framework
- **RESTful API**: Standardisierte Endpunkte
- **JSON**: Datenformat für API-Kommunikation
- **Threading**: Thread-sichere Zustandsverwaltung

### 📊 Visualisierung

#### Canvas-Rendering
- **Grid-System**: Koordinaten-Raster für Orientierung
- **Zonen-Darstellung**: Grüne Bereiche für Mähzonen
- **Hindernis-Rendering**: Rote Bereiche für Ausschlusszonen
- **Pfad-Visualisierung**: Blaue Linien für geplante Routen
- **Roboter-Position**: Markierung der aktuellen Position

#### Interaktive Features
- **Zoom**: Mausrad-Steuerung (0.1x - 5x)
- **Pan**: Drag-and-Drop Navigation
- **Animation**: Simulierte Roboterbewegung
- **Export**: PNG-Download der Visualisierung

## Verwendung

### 🚀 Schnellstart

1. **Server starten**:
   ```bash
   cd sunray_py
   python web_server.py
   ```

2. **Interface öffnen**:
   - Hauptdashboard: `http://localhost:5000`
   - Erweiterte Pfadplanung: `http://localhost:5000/static/advanced_planning.html`

3. **Planung konfigurieren**:
   - Strategie auswählen (Traditional, A*, Hybrid, Adaptive)
   - Parameter anpassen
   - "Planung starten" klicken

4. **Ergebnisse überwachen**:
   - Status-Panel beobachten
   - Pfad-Visualisierung prüfen
   - Logs verfolgen

### 🎮 Interaktive Funktionen

#### Dynamische Hindernisse
- "Dynamisches Hindernis hinzufügen" klicken
- Automatische Platzierung an zufälliger Position
- Mögliche Neuplanung bei Kollision

#### Navigation-Simulation
- "Navigation simulieren" klicken
- Animierte Roboterbewegung entlang des Pfads
- Echtzeit-Fortschritts-Updates

#### Visualisierung-Steuerung
- **Zoom**: Mausrad oder Buttons verwenden
- **Pan**: Maus ziehen für Navigation
- **Reset**: "Ansicht zurücksetzen" für Standardansicht
- **Export**: "Bild exportieren" für PNG-Download

## Konfiguration

### ⚙️ Parameter-Optimierung

#### Für kleine Gärten (< 500m²)
- Max. Segmentlänge: 5-8m
- Hindernis-Radius: 0.5-1.0m
- Heuristik-Gewichtung: 1.2-1.5

#### Für mittlere Gärten (500-2000m²)
- Max. Segmentlänge: 8-15m
- Hindernis-Radius: 1.0-1.5m
- Heuristik-Gewichtung: 1.0-1.2

#### Für große Gärten (> 2000m²)
- Max. Segmentlänge: 15-25m
- Hindernis-Radius: 1.5-2.0m
- Heuristik-Gewichtung: 0.8-1.0

### 🎯 Strategieauswahl

- **Traditional**: Einfache Gärten ohne komplexe Hindernisse
- **A***: Komplexe Layouts mit vielen Hindernissen
- **Hybrid**: Ausgewogene Lösung für die meisten Szenarien
- **Adaptive**: Unbekannte oder wechselnde Umgebungen

## Fehlerbehebung

### 🔍 Häufige Probleme

#### Server startet nicht
- Python-Installation prüfen
- Abhängigkeiten installieren: `pip install -r requirements.txt`
- Port 5000 verfügbar?

#### Interface lädt nicht
- Browser-Cache leeren
- JavaScript aktiviert?
- Netzwerkverbindung prüfen

#### Visualisierung zeigt nichts
- Canvas-Unterstützung im Browser?
- Zoom-Level prüfen
- "Ansicht zurücksetzen" versuchen

#### API-Fehler
- Server-Logs prüfen
- JSON-Format der Anfragen validieren
- Netzwerk-Tab in Entwicklertools öffnen

### 📝 Debug-Modus

```bash
# Server mit Debug-Informationen starten
python web_server.py
```

- Detaillierte Logs in der Konsole
- Automatisches Neuladen bei Änderungen
- Debugger-PIN für erweiterte Diagnose

## Erweiterungen

### 🔮 Zukünftige Features

- **3D-Visualisierung**: Höheninformationen und Terrain
- **Wetterintegration**: Planungsanpassung basierend auf Wetter
- **Machine Learning**: Adaptive Optimierung durch Lernen
- **Multi-Roboter**: Koordination mehrerer Mähroboter
- **Mobile App**: Native iOS/Android-Anwendung

### 🛠️ Anpassungen

#### Custom Themes
```css
/* Eigene Farbschemata in style.css */
:root {
  --primary-color: #your-color;
  --secondary-color: #your-color;
}
```

#### Zusätzliche Metriken
```javascript
// Neue Statistiken in advanced_planning.html
function updateCustomStats(data) {
  // Ihre Implementierung
}
```

#### API-Erweiterungen
```python
# Neue Endpunkte in web_server.py
@app.route('/api/custom/endpoint', methods=['POST'])
def custom_endpoint():
    # Ihre Implementierung
    pass
```

## Support

### 📞 Hilfe und Dokumentation

- **GitHub**: Issues und Pull Requests
- **Forum**: Community-Support
- **Dokumentation**: Vollständige API-Referenz
- **Beispiele**: Demo-Implementierungen

### 🤝 Beitragen

1. Repository forken
2. Feature-Branch erstellen
3. Änderungen implementieren
4. Tests hinzufügen
5. Pull Request erstellen

---

*Entwickelt für das Sunray Mähroboter-Projekt*  
*Lizenz: GPL-3.0 (wie das ursprüngliche Sunray-Projekt)*