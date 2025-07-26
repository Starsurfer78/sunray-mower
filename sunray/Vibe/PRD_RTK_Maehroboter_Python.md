# Product Requirements Document (PRD)
## Projekt: Autonomer RTK-Mähroboter  
## Kunde: [Dein Name]  
## Erstellt am: 2025-07-25

---

## 1. Ziel des Projekts

Ziel ist die Entwicklung einer modularen Software für einen autonomen Mähroboter mit RTK-GPS-Navigation, zonenbasiertem Mähverhalten, Hinderniserkennung, Web-GUI und App-Steuerung. Die Software soll vollständig auf einem Raspberry Pi (High-Level) in Python und einem Raspberry Pi Pico (Low-Level) in C++ laufen. Alle typischen Funktionen eines modernen, kabellosen Mähroboters sollen abgedeckt werden.

---

## 2. Systemarchitektur

### 2.1 Hardwareübersicht

- **Recheneinheit**:  
  - Raspberry Pi 4 (Navigation, GUI, Logging, in Python)  
  - Raspberry Pi Pico (Motorsteuerung, Sensorik, IO, in C++)

- **Sensorik & Aktorik**:  
  - RTK-GPS (u-blox F9P oder Ardusimple) via USB  
  - IMU (BNO085) via I2C  
  - 3x bürstenlose Motoren mit ZS-X11H-Treibern  
  - 3x Encoder (1300 Impulse/U)  
  - 3x INA226 (2x Motorstrom, 1x Akku)  
  - Bumper (2x) + Stopptaste  
  - LCD + Summer  
  - 29.4V Akku

### 2.2 Softwarearchitektur

- **High-Level (Raspberry Pi, Python 3.x)**:
  - RTK-Integration (`pyubx2`, `pynmea2`)
  - Kursregelung (IMU + GPS)
  - Zonenplanung & Navigation
  - Logging
  - Web-GUI (Flask + WebSocket + Leaflet.js)
  - Konfigurationsverwaltung (JSON)

- **Low-Level (Raspberry Pi Pico, Firmware C++):**
  - PWM-Motorsteuerung
  - PID-Regelung
  - Encoder-Auswertung
  - Stromüberwachung
  - Bumper + Notstopp-Logik
  - UART-Protokoll mit CRC

---

## 3. Hauptfunktionen

### 3.1 Navigation & Mählogik
- Zentimetergenaue RTK-Navigation (Fix-Status prüfen)
- Zonenbasierte Mählogik (digitale Karten)
- Pfadplanung (linienbasiert, spiralförmig, zufällig)
- Rückkehr zur Ladestation bei niedrigem Akkustand

### 3.2 Hinderniserkennung
- Stromspitzenüberwachung (via INA226)
- Mechanische Kollisionen via Bumper
- IMU-basierte Sicherheitsabschaltung bei Neigung/Kippen

### 3.3 Kommunikation
- UART-Kommunikation zwischen Pi und Pico mit `pyserial`
- WebSocket-Kommunikation für Live-GUI mit `websockets`
- Logging und Steuerung über Webinterface mit Flask
- Bluetooth Gamepad-Steuerung (manuell)

### 3.4 Benutzeroberfläche
- Web-GUI auf dem Pi (Leaflet.js)
- Anzeige aktueller Position, Zustand, Logs
- Verwaltung mehrerer Mähzonen
- Einstellbare Zeitpläne und Profile

---

## 4. Detailanforderungen

### 4.1 RTK-GPS-Modul
- RTK-Fix prüfen (ggf. zurück zur Station)
- GGA, VTG, GST auswerten mit `pyubx2` oder `pynmea2`
- Positionsdaten in `lat/lon` & lokale Koordinaten umrechnen

### 4.2 IMU BNO085
- Kursbestimmung (Euler/Yaw) mit `adafruit_bno08x` + `smbus2`
- Sensorfusion (IMU + GPS) für stabile Navigation
- Sicherheitsabschaltung bei >35° Neigung

### 4.3 Motorregelung
- PWM-Output über Pi Pico
- PID-Regelung auf Ziel-RPM (geregelt auf Pico)
- Rückmeldung via UART (RPM, PWM, Strom)

### 4.4 Konfiguration & Profile
- Ablage in `/etc/mower/config.json`
- Parameter: PID-Werte, Zonengrenzen, Min/Max PWM & RPM
- Profile für verschiedene Flächen (z. B. Garten vorne, hinten)

### 4.5 Logging
- CSV- oder JSON-Logs mit Zeitstempeln
- Ereignisse: Start/Stopp, Hindernis, Neigung, GPS-Verlust
- Remote-Download via Webinterface

### 4.6 Sicherheit
- Not-Aus über Taste
- Anhebeschutz (IMU + Encoder-Differenz)
- Spannungsüberwachung Akku
- Watchdog auf Pico + Heartbeat vom Pi

---

## 5. Nicht-funktionale Anforderungen

- Modularer Python-Code mit Struktur (z. B. `main.py`, `modules/`, `config/`)
- Dokumentierter Code mit Kommentaren
- Systemstart <30 s
- CPU-Auslastung < 40 % bei Navigation
- Remote-Updates möglich (lokal via USB oder Web-Upload)

---

## 6. Web-GUI (Frontend)
- Echtzeit-Kartendarstellung (Leaflet.js)
- Anzeige: RTK-Fix, Akku, Modus, aktuelle Position
- Buttons für Start, Stopp, Zonenwechsel, Statuslog
- Responsive Design (Desktop + Mobil)
- Speicherung von Punkten per Klick auf Karte

---

## 7. Mobile App (optional, Phase 2)
- Android WebView-App
- Bluetooth-Verbindung zum Roboter für manuelle Steuerung
- Anzeige aktueller Zustände

---

## 8. Schnittstellen

| Komponente         | Protokoll      | Richtung       |
|--------------------|----------------|----------------|
| Pico <-> Pi        | UART + CRC     | Bidirektional  |
| Pi <-> RTK-GPS     | USB (Serial)   | Nur Eingabe    |
| Pi <-> BNO085      | I2C            | Nur Eingabe    |
| Pi <-> Web-GUI     | WebSocket/HTTP | Bidirektional  |
| Pi <-> App         | Bluetooth (HID)| Optional       |

---

## 9. Projektmanagement & Übergabe

- Git-Repository mit strukturierter Codebasis
- Dokumentation in Markdown
- Unit Tests mit `pytest`
- Übergabe inkl. Build-Skript, Konfigurationsbeispielen und Testdaten

---

## 10. Abnahmekriterien

- Roboter kann vollständig autonom Zone abfahren
- Webinterface zeigt Live-Position & Log an
- Hindernisse werden erkannt und umfahren/gestoppt
- RTK-Fix muss erreicht werden (> 95 % der Zeit)
- Software ist stabil über 2+ Stunden Laufzeit
