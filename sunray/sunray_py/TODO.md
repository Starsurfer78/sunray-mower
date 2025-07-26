# Sunray Python - TODO Liste

## Projektfortschritt

### RTK-GPS Integration (100% abgeschlossen)

#### ✅ Abgeschlossen:
- [x] u-blox F9P GPS Receiver Support (Ardusimple RTK Board)
- [x] XBee 868MHz RTK-Kommunikation (Rover ↔ Basisstation)
- [x] NTRIP-Client für Internet-basierte RTK-Korrekturdaten
- [x] Automatische RTK-Quellenerkennung (XBee → NTRIP Fallback)
- [x] Flexible RTK-Modi (auto, xbee, ntrip)
- [x] GPS-basierte Navigation und Wegpunkt-System
- [x] Koordinatentransformation (WGS84 zu lokalen Koordinaten)
- [x] Kidnap Detection (Erkennung von GPS-Sprüngen)
- [x] Fix-Status Monitoring (No Fix, 2D, 3D, RTK Float, RTK Fixed)
- [x] RTK-Quelle Tracking und Gesundheitsüberwachung
- [x] Konfigurierbare Parameter über config.json
- [x] Erweiterte Dokumentation und Setup-Anleitung
- [x] USB-Plug-and-Play Support
- [x] Automatische Board-Konfiguration (UBX-Nachrichten, Update-Rate, RTK-Modi)
- [x] Hart codierte Port/Baudrate-Werte in Konfiguration ausgelagert
- [x] Integration in Pfadplanung und autonome Navigation
- [x] GPS-Navigation Klasse implementiert
- [x] Hochpräzise Wegpunkt-Navigation
- [x] Integration in Motor-Steuerung

#### 🔄 In Bearbeitung:
- [ ] Feldtests mit XBee RTK-Station

#### 📋 Geplant:
- [ ] GPS-basierte Docking-Präzision
- [ ] Multi-Constellation Support (GPS + GLONASS + Galileo)
- [ ] RTK-Baseline Monitoring
- [ ] GPS-Spoofing Detection

### Weitere Module

#### Sensorfusion
- [x] IMU Integration
- [x] GPS Integration
- [x] Komplementärfilter
- [ ] Erweiterte Kalman-Filter

#### Navigation
- [x] Grundlegende Wegpunkt-Navigation
- [x] Hinderniserkennung
- [x] Enhanced Escape System
- [x] Pfadplanung mit A*
- [x] Dynamische Hindernisvermeidung
- [x] Hybride Pfadplanungsstrategien
- [x] Adaptive Strategieauswahl
- [x] A*-Algorithmus mit konfigurierbarer Heuristik

#### Hardware-Integration
- [x] Motor-Controller
- [x] Batterie-Monitoring
- [x] Hardware-Manager
- [ ] Erweiterte Sensorintegration

#### Kommunikation
- [x] MQTT-Telemetrie
- [x] Smart Button Controller
- [x] Web-Interface
- [ ] Mobile App Integration

## Prioritäten

1. **Hoch**: RTK-GPS Feldtests abschließen
2. **Mittel**: Pfadplanung implementieren
3. **Niedrig**: Web-Interface entwickeln

## Bekannte Probleme

- [ ] GPS-Initialisierung bei kaltem Start optimieren
- [ ] MQTT-Verbindung bei Netzwerkproblemen stabilisieren
- [ ] Speicherverbrauch bei langen Läufen überwachen

## Dokumentation

- [x] RTK-GPS Setup Guide
- [ ] Vollständige API-Dokumentation
- [ ] Troubleshooting Guide
- [ ] Performance Tuning Guide