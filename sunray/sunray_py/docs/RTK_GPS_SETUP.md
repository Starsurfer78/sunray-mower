# RTK-GPS Setup für Sunray Python

Diese Anleitung beschreibt die Einrichtung des RTK-GPS-Systems für zentimetergenaue Navigation mit dem Sunray Python-System.

## Hardware-Anforderungen

- **GPS-Empfänger**: Ardusimple RTK Board (u-blox F9P) über USB
- **Verbindung**: USB zum Raspberry Pi
- **RTK-Korrekturdaten**: 
  - **Option 1**: Eigene RTK-Station mit XBee 868MHz Modulen (Rover + Basisstation)
  - **Option 2**: NTRIP-Zugang über Internet (Fallback oder primär)

## RTK-Modi

Das System unterstützt drei RTK-Modi:

1. **Auto-Modus** (`"rtk_mode": "auto"`) - Empfohlen
   - Erkennt automatisch XBee RTK-Nachrichten
   - Wechselt zu NTRIP als Fallback wenn XBee nicht verfügbar
   
2. **XBee-Modus** (`"rtk_mode": "xbee"`)
   - Nur XBee RTK-Kommunikation
   - Kein NTRIP-Fallback
   
3. **NTRIP-Modus** (`"rtk_mode": "ntrip"`)
   - Nur NTRIP-basierte RTK-Korrekturdaten
   - Ignoriert XBee-Nachrichten

## Software-Setup

### 1. Abhängigkeiten installieren

```bash
cd sunray_py
pip install -r requirements.txt
```

### 2. Konfiguration

#### Empfohlene Konfiguration (Auto-Modus mit XBee + NTRIP-Fallback)

1. Kopiere die Beispielkonfiguration:
```bash
cp config.json.example config.json
```

2. Bearbeite `config.json` für optimale Flexibilität:

```json
{
  "rtk_gps": {
    "rtk_mode": "auto",
    "ntrip_enabled": true,
    "ntrip_fallback": true,
    "port": "/dev/ttyUSB0",
    "baudrate": 115200,
    "auto_configure": true,
    
    "ntrip": {
      "host": "your-ntrip-caster.com",
      "port": 2101,
      "mountpoint": "YOUR_MOUNTPOINT",
      "username": "your_username",
      "password": "your_password"
    }
  },
  "hardware": {
    "pico_comm": {
      "port": "/dev/ttyS0",
      "baudrate": 115200,
      "timeout": 0.1
    }
  }
}
```

#### Nur XBee RTK (ohne NTRIP)

```json
{
    "rtk_gps": {
      "rtk_mode": "xbee",
      "ntrip_enabled": false,
      "port": "/dev/ttyUSB0",
      "baudrate": 115200
    }
  }
```

#### Nur NTRIP (ohne XBee)

```json
{
    "rtk_gps": {
      "rtk_mode": "ntrip",
      "ntrip_enabled": true,
      "port": "/dev/ttyUSB0",
      "baudrate": 115200,
      "ntrip": {
        "host": "your-ntrip-caster.com",
        "port": 2101,
        "mountpoint": "YOUR_MOUNTPOINT",
        "username": "your_username",
        "password": "your_password"
      }
    }
  }
```

## NTRIP-Anbieter

### Deutschland
- **SAPOS**: Staatliche Vermessungsdienste der Länder
- **RTK2go**: Kostenloser Community-Service
- **Trimble RTX**: Kommerzielle Lösung

### Österreich
- **APOS**: Austrian Positioning Service

### Schweiz
- **swipos**: Schweizerischer Positionierungsdienst

### 3. XBee RTK-Station Setup (für eigene RTK-Station)

Für eine eigene RTK-Station mit XBee 868MHz:

1. **Hardware-Setup**:
   - **Basisstation**: Ardusimple RTK Board + XBee 868MHz Modul
   - **Rover**: Ardusimple RTK Board + XBee 868MHz Modul (am Roboter)
   - Feste Position der Basisstation mit bekannten Koordinaten
   - Reichweite: bis zu mehrere Kilometer (je nach Gelände)

2. **XBee-Konfiguration** (direkt am Ardusimple Board):
   - Beide XBee-Module auf gleiche Frequenz (868MHz)
   - Gleiche PAN-ID und Netzwerk-Einstellungen über XCTU-Software
   - Basisstation sendet RTCM3-Korrekturdaten automatisch
   - Rover empfängt Korrekturdaten transparent über XBee
   - **Keine Raspberry Pi Konfiguration erforderlich** - alles wird vom Ardusimple Board gehandhabt

## Hardware-Verbindung

### Ardusimple RTK Board über USB (Standard-Setup)

```
Ardusimple RTK Board --[USB]-- Raspberry Pi
                    |
                    +-- XBee 868MHz Modul (optional)
```

**Vorteile**:
- Einfache Plug-and-Play Installation
- Stromversorgung über USB
- Automatische Geräteerkennung
- Unterstützt sowohl XBee RTK als auch NTRIP

### Port und Baudrate Konfiguration

Port, Baudrate und automatische Konfiguration können über die `config.json` gesteuert werden:

```json
{
  "rtk_gps": {
    "port": "/dev/ttyUSB0",     // USB-Port des RTK Boards
    "baudrate": 115200,         // Standard für Ardusimple RTK Board
    "timeout": 1.0,
    "auto_configure": true      // Automatische Board-Konfiguration
  }
}
```

### Automatische Board-Konfiguration

Der Parameter `auto_configure` (Standard: `true`) aktiviert die automatische Konfiguration des Ardusimple RTK Boards:

**Was wird automatisch konfiguriert:**
- **Update-Rate:** 5Hz für optimale Performance
- **UBX-Nachrichten:** NAV-PVT (Position/Velocity/Time), NAV-RELPOSNED (RTK-Status)
- **NMEA-Nachrichten:** Nur GGA (für Kompatibilität), alle anderen deaktiviert
- **Baudrate:** 115200 (falls noch nicht gesetzt)
- **RTK-Modi:** Automotive Dynamic Model, 3D-Fix only
- **Elevation Mask:** 5° (filtert niedrige Satelliten)
- **Protokolle:** UBX+NMEA+RTCM3 Input, UBX+NMEA Output

**Konfiguration wird im Flash gespeichert** - einmalige Ausführung reicht!

```json
// Automatische Konfiguration deaktivieren (für manuell konfigurierte Boards)
{
  "rtk_gps": {
    "auto_configure": false
  }
}
```

### Parameter-Beschreibung

#### RTK-GPS Parameter
- **port**: Serieller Port des RTK-GPS-Moduls (z.B. `/dev/ttyUSB0`, `/dev/ttyACM0`)
- **baudrate**: Baudrate für die serielle Kommunikation (Standard: 115200)
- **rtk_mode**: RTK-Betriebsmodus (`auto`, `xbee`, `ntrip`)
- **ntrip_fallback**: Aktiviert NTRIP als Fallback wenn XBee nicht verfügbar
- **auto_configure**: Aktiviert automatische Board-Konfiguration beim Start

#### Hardware Parameter
- **pico_comm.port**: Serieller Port für Pico-Kommunikation (z.B. `/dev/ttyS0`, `COM3`)
- **pico_comm.baudrate**: Baudrate für Pico-Kommunikation (Standard: 115200)
- **pico_comm.timeout**: Timeout für serielle Kommunikation in Sekunden (Standard: 0.1)

**Häufige Port-Einstellungen**:
- **Linux/Raspberry Pi**: `/dev/ttyUSB0`, `/dev/ttyUSB1`, `/dev/ttyACM0`
- **Windows**: `COM3`, `COM4`, `COM5`, etc.
- **macOS**: `/dev/tty.usbserial-*`, `/dev/tty.usbmodem-*`

**Baudrate-Einstellungen**:
- **Ardusimple RTK Board**: `115200` (Standard)
- **u-blox F9P direkt**: `38400` oder `115200`
- **Andere GPS-Module**: `9600`, `19200`, `38400`

## Test der automatischen Konfiguration

Ein Test-Skript ist verfügbar, um die automatische Board-Konfiguration zu testen:

```bash
python test_rtk_config.py
```

**Das Test-Skript überprüft:**
- Automatische Board-Konfiguration beim Start
- GPS-Fix und Datenempfang
- RTK-Status und Quellenerkennung
- Manuelle Neukonfiguration

**Voraussetzungen für den Test:**
- Ardusimple RTK Board über USB verbunden
- GPS-Modul hat Satellitensicht (im Freien testen)
- Korrekte Port-Konfiguration in `test_rtk_config.py`

### Verkabelung (falls UART benötigt)

```
GPS-Modul  -->  Raspberry Pi
VCC        -->  3.3V oder 5V
GND        -->  GND
TX         -->  GPIO 15 (RX)
RX         -->  GPIO 14 (TX)
```

### USB-Verbindung

Bei USB-Verbindung wird automatisch `/dev/ttyUSB0` oder `/dev/ttyACM0` verwendet.

## Funktionen

### Automatische Features
- **Koordinatentransformation**: GPS → lokales Koordinatensystem
- **Kidnap Detection**: Erkennung plötzlicher Positionssprünge
- **Fix-Status Monitoring**: Überwachung der GPS-Qualität
- **Waypoint Navigation**: Automatische Wegpunkt-Verfolgung

### GPS-Datenformat

Das System liefert erweiterte GPS-Informationen:

```python
{
    'lat': 52.123456,           # Breitengrad
    'lon': 13.654321,           # Längengrad
    'alt': 45.2,                # Höhe über Meeresspiegel
    'fix_type': 4,              # Fix-Typ (0-5)
    'hdop': 0.8,                # Horizontale Genauigkeit
    'nsat': 12,                 # Anzahl Satelliten
    'local_x': 123.45,          # Lokale X-Koordinate
    'local_y': 67.89,           # Lokale Y-Koordinate
    'rtk_age': 2.1,             # Alter der RTK-Korrekturdaten
    'rtk_ratio': 0.95,          # RTK-Qualität
    'kidnap_detected': false,   # Kidnap-Erkennung
    'waypoint_distance': 5.2,   # Entfernung zum Waypoint
    'waypoint_bearing': 45.0    # Richtung zum Waypoint
}
```

### Fix-Typen
- **0**: No Fix
- **1**: Dead Reckoning
- **2**: 2D Fix
- **3**: 3D Fix
- **4**: GNSS + Dead Reckoning
- **5**: RTK Fixed (zentimetergenau)

## Troubleshooting

### Häufige Probleme

1. **Keine GPS-Daten**
   - Prüfen Sie die serielle Verbindung
   - Überprüfen Sie Port und Baudrate
   - Stellen Sie sicher, dass die Antenne freie Sicht zum Himmel hat

2. **NTRIP-Verbindung fehlgeschlagen**
   - Überprüfen Sie Internetverbindung
   - Validieren Sie NTRIP-Zugangsdaten
   - Prüfen Sie Firewall-Einstellungen

3. **Schlechte RTK-Qualität**
   - Überprüfen Sie die Entfernung zur Basisstation (< 20km)
   - Stellen Sie sicher, dass keine Hindernisse die Sicht blockieren
   - Warten Sie auf bessere Satellitenkonstellation

### Debug-Modus

Aktivieren Sie Debug-Ausgaben in `config.json`:

```json
{
  "system": {
    "debug_mode": true,
    "log_level": "DEBUG"
  }
}
```

## Integration in Sunray

Das RTK-GPS-System ist vollständig in die Sunray-Navigation integriert:

- **Pfadplanung**: Verwendet GPS-Koordinaten für präzise Navigation
- **Kartierung**: Erstellt hochgenaue Karten der Mähfläche
- **Docking**: Präzise Rückkehr zur Ladestation
- **Hinderniserkennung**: GPS-basierte Kollisionsvermeidung

## Weiterführende Informationen

- [u-blox F9P Dokumentation](https://www.u-blox.com/en/product/zed-f9p-module)
- [NTRIP Protokoll Spezifikation](https://igs.bkg.bund.de/root_ftp/NTRIP/documentation/NtripDocumentation.pdf)
- [RTK-GPS Grundlagen](https://www.gps.gov/technical/ps/2008-SPS-performance-standard.pdf)