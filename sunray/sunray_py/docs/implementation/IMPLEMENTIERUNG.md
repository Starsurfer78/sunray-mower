# Implementierungsroadmap für RTK-Mähroboter

Dieses Dokument beschreibt die detaillierte Implementierungsstrategie für die noch fehlenden Komponenten des RTK-Mähroboters gemäß der PRD.

## 1. IMU BNO085 Integration

### Technische Details
- **Bibliothek**: `adafruit_bno08x` über `smbus2`
- **Dateien**: `imu.py` anpassen
- **Schnittstelle**: I2C (Adresse 0x28 oder 0x29)

### Implementierungsschritte
1. Installation der Bibliothek: `pip install adafruit-circuitpython-bno08x`
2. Anpassung der `IMUSensor`-Klasse für BNO085:
   ```python
   class IMUSensor:
       def __init__(self, i2c_bus=1, address=0x28):
           self.i2c = smbus2.SMBus(i2c_bus)
           self.sensor = adafruit_bno08x.BNO08X_I2C(self.i2c, address=address)
           self.sensor.enable_feature(adafruit_bno08x.BNO_REPORT_ACCELEROMETER)
           self.sensor.enable_feature(adafruit_bno08x.BNO_REPORT_GYROSCOPE)
           self.sensor.enable_feature(adafruit_bno08x.BNO_REPORT_MAGNETOMETER)
           self.sensor.enable_feature(adafruit_bno08x.BNO_REPORT_ROTATION_VECTOR)
   ```
3. Implementierung der Sensorfusion in `state_estimator.py`:
   - Kombination von IMU-Heading und GPS-Kurs
   - Kalman-Filter für stabile Navigation
4. Implementierung der Sicherheitsabschaltung bei >35° Neigung

## 2. Zonenbasierte Mählogik

### Technische Details
- **Dateien**: `map.py`, `op.py` erweitern
- **Algorithmen**: Linienbasiert, Spiralförmig, Zufällig

### Implementierungsschritte
1. Erweiterung der `Map`-Klasse um Pfadplanungsalgorithmen:
   ```python
   def plan_path(self, strategy="lines", spacing=0.3):
       """Erzeugt einen Pfad basierend auf der gewählten Strategie."""
       if strategy == "lines":
           return self._plan_lines_path(spacing)
       elif strategy == "spiral":
           return self._plan_spiral_path(spacing)
       elif strategy == "random":
           return self._plan_random_path()
   ```
2. Implementierung der Rückkehr zur Ladestation:
   - A*-Algorithmus für Pfadplanung
   - Berücksichtigung von Hindernissen
3. Implementierung der Zonenwechsel-Logik in `MowOp`

## 3. Hinderniserkennung

### Technische Details
- **Hardware**: INA226 über I2C, Bumper über GPIO, IMU
- **Dateien**: Neue Datei `obstacle_detection.py`

### Implementierungsschritte
1. Implementierung der Stromspitzenüberwachung:
   ```python
   class CurrentMonitor:
       def __init__(self, i2c_bus=1, address=0x40):
           self.i2c = smbus2.SMBus(i2c_bus)
           # INA226 Register-Setup
           # ...
       
       def read_current(self):
           """Liest den aktuellen Strom in mA."""
           # INA226 Register lesen
           # ...
           return current_ma
       
       def detect_spike(self, threshold=1000):
           """Erkennt Stromspitzen über dem Schwellenwert."""
           current = self.read_current()
           return current > threshold
   ```
2. Verbesserung der Bumper-Erkennung
3. Implementierung der IMU-basierten Sicherheitsabschaltung

## 4. Web-GUI

### Technische Details
- **Framework**: Flask + WebSocket + Leaflet.js
- **Dateien**: `http_server.py` erweitern, neue Dateien für Frontend

### Implementierungsschritte
1. Erweiterung des Flask-Servers um WebSocket-Unterstützung:
   ```python
   from flask import Flask, request, jsonify, render_template
   from flask_socketio import SocketIO
   
   app = Flask(__name__)
   socketio = SocketIO(app)
   
   @app.route('/')
   def index():
       return render_template('index.html')
   
   @socketio.on('connect')
   def handle_connect():
       print('Client connected')
   
   @socketio.on('command')
   def handle_command(data):
       # Kommando verarbeiten
       # ...
       socketio.emit('status', {'status': 'command received'})
   ```
2. Implementierung des Frontends mit Leaflet.js:
   - HTML/CSS/JS-Dateien in `templates/` und `static/`
   - Karte mit Mähzonen, aktueller Position, Pfad
   - Steuerelemente für Start, Stopp, Zonenwechsel
3. Implementierung der Live-Updates über WebSocket

## 5. Konfiguration & Profile

### Technische Details
- **Format**: JSON
- **Speicherort**: `/etc/mower/config.json`
- **Dateien**: Neue Datei `config.py`

### Implementierungsschritte
1. Implementierung der Konfigurationsverwaltung:
   ```python
   class Config:
       def __init__(self, config_file="/etc/mower/config.json"):
           self.config_file = config_file
           self.config = self._load_config()
       
       def _load_config(self):
           """Lädt die Konfiguration aus der Datei."""
           try:
               with open(self.config_file, 'r') as f:
                   return json.load(f)
           except Exception as e:
               print(f"Fehler beim Laden der Konfiguration: {e}")
               return {}
       
       def save_config(self):
           """Speichert die Konfiguration in der Datei."""
           try:
               with open(self.config_file, 'w') as f:
                   json.dump(self.config, f, indent=2)
               return True
           except Exception as e:
               print(f"Fehler beim Speichern der Konfiguration: {e}")
               return False
       
       def get(self, key, default=None):
           """Gibt den Wert für den Schlüssel zurück."""
           keys = key.split('.')
           value = self.config
           for k in keys:
               if k in value:
                   value = value[k]
               else:
                   return default
           return value
       
       def set(self, key, value):
           """Setzt den Wert für den Schlüssel."""
           keys = key.split('.')
           config = self.config
           for i, k in enumerate(keys[:-1]):
               if k not in config:
                   config[k] = {}
               config = config[k]
           config[keys[-1]] = value
           return self.save_config()
   ```
2. Implementierung der Profilunterstützung:
   - Erweiterung der Konfigurationsklasse
   - UI-Elemente für Profilauswahl

## 6. Sicherheitsfunktionen

### Technische Details
- **Hardware**: Stopptaste über GPIO, IMU, Encoder
- **Dateien**: Neue Datei `safety.py`

### Implementierungsschritte
1. Implementierung des Not-Aus:
   ```python
   class EmergencyStop:
       def __init__(self, pin=17):
           self.pin = pin
           GPIO.setmode(GPIO.BCM)
           GPIO.setup(self.pin, GPIO.IN, pull_up_down=GPIO.PUD_UP)
           GPIO.add_event_detect(self.pin, GPIO.FALLING, callback=self._emergency_stop, bouncetime=300)
       
       def _emergency_stop(self, channel):
           """Callback für den Not-Aus."""
           print("Not-Aus ausgelöst!")
           # Motoren stoppen
           # ...
   ```
2. Implementierung des Anhebeschutzes
3. Implementierung des Watchdogs und Heartbeats

## 7. Bluetooth Gamepad-Steuerung

### Technische Details
- **Bibliothek**: `bleak` für BLE
- **Dateien**: Neue Datei `gamepad.py`

### Implementierungsschritte
1. Implementierung der Bluetooth-Verbindung
2. Implementierung der Gamepad-Steuerung

## 8. Logging

### Technische Details
- **Format**: CSV oder JSON
- **Dateien**: `events.py` erweitern

### Implementierungsschritte
1. Erweiterung des Loggings um CSV/JSON-Unterstützung
2. Implementierung des Remote-Downloads über die Web-GUI

## Zeitplan

1. **Woche 1-2**: IMU BNO085 Integration, Sicherheitsfunktionen
2. **Woche 3-4**: Zonenbasierte Mählogik, Hinderniserkennung
3. **Woche 5-6**: Web-GUI, Konfiguration & Profile
4. **Woche 7-8**: Bluetooth Gamepad-Steuerung, Logging, Tests

## Testplan

1. **Komponententests**: Jede Komponente einzeln testen
2. **Integrationstests**: Zusammenspiel der Komponenten testen
3. **Systemtests**: Gesamtsystem in realer Umgebung testen
4. **Abnahmetests**: Überprüfung der Abnahmekriterien