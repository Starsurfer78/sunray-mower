# Autonomer Mähroboter mit RTK-GPS-Navigation

Dieses Projekt implementiert eine modulare Software für einen autonomen Mähroboter mit RTK-GPS-Navigation, zonenbasiertem Mähverhalten, Hinderniserkennung, Web-GUI und App-Steuerung. Die Software läuft vollständig auf einem Raspberry Pi (High-Level) in Python und einem Raspberry Pi Pico (Low-Level) in C++.

## Systemarchitektur

### Hardwareübersicht

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

### Softwarearchitektur

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

## Installation und Inbetriebnahme

### 1. Vorbereitung der Hardware

#### Raspberry Pi 4 Setup
- Installieren Sie Raspberry Pi OS (ehemals Raspbian) auf dem Raspberry Pi 4
- Aktivieren Sie SSH, I2C, UART und GPIO in den Raspberry Pi-Einstellungen (`sudo raspi-config`)
- Stellen Sie sicher, dass alle erforderlichen Bibliotheken installiert sind:
  ```
  sudo apt update
  sudo apt install -y python3-pip python3-dev i2c-tools
  ```

#### Raspberry Pi Pico Setup
- Flashen Sie die Firmware auf den Raspberry Pi Pico
- Die Pico-Firmware muss die UART-Kommunikation, PWM-Motorsteuerung und Encoder-Auswertung unterstützen

#### Verkabelung
- Verbinden Sie den Raspberry Pi 4 mit dem Raspberry Pi Pico über UART (TX/RX)
- Schließen Sie die RTK-GPS-Einheit an den Raspberry Pi 4 über USB an
- Verbinden Sie den BNO085 IMU-Sensor mit dem Raspberry Pi 4 über I2C
- Verbinden Sie die Motortreiber mit dem Raspberry Pi Pico

### 2. Software-Installation

#### Auf dem Raspberry Pi 4

1. Klonen Sie das Repository auf den Raspberry Pi:
   ```
   git clone https://github.com/IhrRepository/sunray.git
   cd sunray
   ```

2. Installieren Sie die erforderlichen Python-Pakete:
   ```
   cd sunray_py
   pip3 install -r requirements.txt
   ```

3. Erstellen Sie die Konfigurationsdateien:
   ```
   sudo mkdir -p /etc/mower
   sudo touch /etc/mower/config.json
   ```

4. Bearbeiten Sie die Konfigurationsdatei mit den richtigen Parametern:
   ```
   sudo nano /etc/mower/config.json
   ```
   
   Beispielkonfiguration:
   ```json
   {
     "gps": {
       "port": "/dev/ttyUSB0",
       "baudrate": 38400
     },
     "pico": {
       "port": "/dev/ttyS0",
       "baudrate": 115200
     },
     "motor": {
       "max_rpm": 100,
       "pid": {
         "kp": 0.5,
         "ki": 0.1,
         "kd": 0.01
       }
     },
     "mower": {
       "max_rpm": 3000
     },
     "battery": {
       "go_home_voltage": 21.5,
       "shutdown_voltage": 20.0
     }
   }
   ```

5. Erstellen Sie eine Zonendatei für die Mähbereiche:
   ```
   nano zones.json
   ```
   
   Beispiel:
   ```json
   {
     "mow_zones": [
       [
         {"x": 0.0, "y": 0.0},
         {"x": 10.0, "y": 0.0},
         {"x": 10.0, "y": 10.0},
         {"x": 0.0, "y": 10.0}
       ]
     ]
   }
   ```

#### Auf dem Raspberry Pi Pico

Die Pico-Firmware muss separat entwickelt und geflasht werden. Sie sollte folgende Funktionen unterstützen:

- UART-Kommunikation mit dem Raspberry Pi 4
- PWM-Motorsteuerung
- Encoder-Auswertung
- Stromüberwachung über INA226
- Bumper- und Stopptasten-Erkennung

### 3. Testen der Komponenten

Bevor Sie den Mähroboter autonom fahren lassen, sollten Sie die einzelnen Komponenten testen:

1. Testen Sie die GPS-Verbindung:
   ```
   python3 -c "from rtk_gps import RTKGPS; gps = RTKGPS(); print(gps.read())"
   ```

2. Testen Sie die IMU-Verbindung:
   ```
   python3 -c "from imu import IMUSensor; imu = IMUSensor(); print(imu.read())"
   ```

3. Testen Sie die Pico-Kommunikation:
   ```
   python3 -c "from pico_comm import PicoComm; pico = PicoComm('/dev/ttyS0', 115200); pico.send_command('AT'); print(pico.read_sensor_data())"
   ```

4. Testen Sie die Motoren (vorsichtig, der Roboter könnte sich bewegen):
   ```
   python3 -c "from pico_comm import PicoComm; pico = PicoComm('/dev/ttyS0', 115200); pico.send_command('AT+M:10,10,0')"
   ```

### 4. Starten des Mähroboters

1. Starten Sie den Hauptprozess:
   ```
   cd sunray_py
   python3 main.py
   ```

2. Öffnen Sie die Weboberfläche in einem Browser:
   ```
   http://<raspberry-pi-ip>:5000
   ```

3. Verwenden Sie die Weboberfläche, um den Mähroboter zu steuern und zu überwachen.

### 5. Fehlerbehebung

Wenn der Mähroboter nicht wie erwartet funktioniert, überprüfen Sie Folgendes:

1. Überprüfen Sie die Logs:
   ```
   tail -f /var/log/syslog | grep sunray
   ```

2. Überprüfen Sie die UART-Verbindung zwischen Raspberry Pi und Pico:
   ```
   sudo cat /dev/ttyS0
   ```

3. Überprüfen Sie die GPS-Verbindung:
   ```
   sudo cat /dev/ttyUSB0
   ```

4. Überprüfen Sie die I2C-Verbindung für den IMU-Sensor:
   ```
   sudo i2cdetect -y 1
   ```

5. Stellen Sie sicher, dass alle erforderlichen Dienste laufen:
   ```
   ps aux | grep python
   ```

### 6. Automatischer Start beim Booten

Um den Mähroboter automatisch beim Booten zu starten, erstellen Sie einen systemd-Service:

```
sudo nano /etc/systemd/system/mower.service
```

Inhalt:
```
[Unit]
Description=Autonomous Mower Service
After=network.target

[Service]
ExecStart=/usr/bin/python3 /home/pi/sunray/sunray_py/main.py
WorkingDirectory=/home/pi/sunray/sunray_py
StandardOutput=inherit
StandardError=inherit
Restart=always
User=pi

[Install]
WantedBy=multi-user.target
```

Aktivieren und starten Sie den Service:
```
sudo systemctl enable mower.service
sudo systemctl start mower.service
```

## Hauptfunktionen

### Navigation & Mählogik
- Zentimetergenaue RTK-Navigation (Fix-Status prüfen)
- Zonenbasierte Mählogik (digitale Karten)
- Pfadplanung (linienbasiert, spiralförmig, zufällig)
- Rückkehr zur Ladestation bei niedrigem Akkustand

### Hinderniserkennung
- Stromspitzenüberwachung (via INA226)
- Mechanische Kollisionen via Bumper
- IMU-basierte Sicherheitsabschaltung bei Neigung/Kippen

### Kommunikation
- UART-Kommunikation zwischen Pi und Pico mit `pyserial`
- WebSocket-Kommunikation für Live-GUI mit `websockets`
- Logging und Steuerung über Webinterface mit Flask
- Bluetooth Gamepad-Steuerung (manuell)

### Benutzeroberfläche
- Web-GUI auf dem Pi (Leaflet.js)
- Anzeige aktueller Position, Zustand, Logs
- Verwaltung mehrerer Mähzonen
- Einstellbare Zeitpläne und Profile

## Projektstruktur

```
sunray/
├── sunray_py/           # Python-Code für Raspberry Pi
│   ├── main.py          # Hauptskript
│   ├── rtk_gps.py       # RTK-GPS-Integration
│   ├── imu.py           # IMU-Sensor-Integration
│   ├── pico_comm.py     # Kommunikation mit Pico
│   ├── map.py           # Kartierung und Navigation
│   ├── motor.py         # Motorsteuerung
│   ├── battery.py       # Batteriemanagement
│   ├── pid.py           # PID-Regelung
│   ├── events.py        # Ereignisprotokollierung
│   ├── storage.py       # Persistente Speicherung
│   ├── http_server.py   # Web-GUI
│   └── mqtt_client.py   # MQTT-Integration
└── Pico/                # C++-Firmware für Raspberry Pi Pico
    └── 1.0/             # Firmware-Version
```

## Lizenz

Dieses Projekt steht unter der [MIT-Lizenz](LICENSE).

## Mitwirkende

- Ihr Name - Hauptentwickler

## Kontakt

Bei Fragen oder Problemen können Sie ein Issue auf GitHub erstellen oder uns direkt kontaktieren.