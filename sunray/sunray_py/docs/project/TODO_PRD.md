# TODO: Umsetzung der PRD-Anforderungen

## Priorität 1: Grundfunktionalität vervollständigen

### IMU BNO085 Integration
- [x] Upgrade von BNO055 auf BNO085 implementieren
- [x] Sensorfusion (IMU + GPS) für stabile Navigation
- [x] Sicherheitsabschaltung bei >35° Neigung
- [x] Kursbestimmung (Euler/Yaw) mit `adafruit_bno08x` + `smbus2`

### Zonenbasierte Mählogik
- [ ] Pfadplanung implementieren (linienbasiert, spiralförmig, zufällig)
- [ ] Rückkehr zur Ladestation bei niedrigem Akkustand vervollständigen
- [ ] Zonenwechsel-Logik implementieren

### Hinderniserkennung
- [x] Stromspitzenüberwachung via INA226 implementieren
- [x] Mechanische Kollisionen via Bumper verbessern (mit Bitmaske für links/rechts)
- [x] IMU-basierte Sicherheitsabschaltung implementieren
- [x] Debouncing und Kollisions-Reset-Timer für Bumper implementiert

### Sicherheitsfunktionen
- [ ] Not-Aus über Taste implementieren
- [ ] Anhebeschutz (IMU + Encoder-Differenz) implementieren
- [ ] Watchdog auf Pico + Heartbeat vom Pi implementieren

## Priorität 2: Benutzeroberfläche

### Web-GUI
- [ ] Echtzeit-Kartendarstellung mit Leaflet.js implementieren
- [ ] WebSocket-Kommunikation für Live-Updates einrichten
- [ ] Anzeige: RTK-Fix, Akku, Modus, aktuelle Position
- [ ] Buttons für Start, Stopp, Zonenwechsel, Statuslog
- [ ] Responsive Design (Desktop + Mobil)
- [ ] Speicherung von Punkten per Klick auf Karte

### Konfiguration & Profile
- [ ] Konfigurationsverwaltung in `/etc/mower/config.json` verbessern
- [ ] Parameter: PID-Werte, Zonengrenzen, Min/Max PWM & RPM
- [ ] Profile für verschiedene Flächen implementieren

## Priorität 3: Erweiterte Funktionen

### Bluetooth Gamepad-Steuerung
- [ ] Bluetooth-Verbindung zum Roboter für manuelle Steuerung
- [ ] Anzeige aktueller Zustände

### Logging
- [ ] CSV- oder JSON-Logs mit Zeitstempeln verbessern
- [ ] Ereignisse: Start/Stopp, Hindernis, Neigung, GPS-Verlust
- [ ] Remote-Download via Webinterface

### Remote-Updates
- [ ] Remote-Updates ermöglichen (lokal via USB oder Web-Upload)

## Abnahmekriterien

- [ ] Roboter kann vollständig autonom Zone abfahren
- [ ] Webinterface zeigt Live-Position & Log an
- [ ] Hindernisse werden erkannt und umfahren/gestoppt
- [ ] RTK-Fix muss erreicht werden (> 95 % der Zeit)
- [ ] Software ist stabil über 2+ Stunden Laufzeit