# Battery Integration mit Pico-Daten

## Übersicht

Die `Battery`-Klasse wurde erfolgreich in die Hauptschleife integriert, um Batteriedaten vom Pico zu verarbeiten und Batteriemanagement-Funktionen bereitzustellen.

## Implementierte Änderungen

### 1. Integration in main.py

**Vorher:**
- Battery-Klasse wurde instanziiert, aber nie mit Daten gefüttert
- Nur `battery.under_voltage()` wurde aufgerufen
- Batteriedaten vom Pico wurden nicht verarbeitet

**Nachher:**
- `battery.run()` wird mit Pico-Daten aufgerufen
- Batteriedaten werden aus Summary-Nachrichten (`S,`) extrahiert
- Vollständige Batteriestatusinformationen werden über MQTT gesendet

### 2. Datenverarbeitung

```python
# Batteriedaten vom Pico verarbeiten
if pico_data and 'bat_voltage' in pico_data:
    battery_status = battery.run(
        pico_data.get('bat_voltage', 0.0),
        pico_data.get('chg_voltage', 0.0),
        pico_data.get('chg_current', 0.0)
    )
else:
    battery_status = {}
```

### 3. MQTT Telemetrie

Erweiterte Telemetriedaten mit vollständigen Batteriestatusinformationen:

```python
"battery": {
    "voltage": pico_data.get('bat_voltage', 0.0),
    "charge_voltage": pico_data.get('chg_voltage', 0.0),
    "charge_current": pico_data.get('chg_current', 0.0),
    "charger_connected": battery.charger_connected(),
    "is_docked": battery.is_docked(),
    "should_go_home": battery.should_go_home(),
    "under_voltage": battery.under_voltage(),
    "charging_completed": battery.is_charging_completed(),
    **battery_status
}
```

## Pico-Datenformat

Die Batteriedaten kommen vom Pico im Summary-Format:

```
S,batVoltageLP,chgVoltage,chgCurrentLP,lift,bumper,raining,motorOverload,mowCurrLP,motorLeftCurrLP,motorRightCurrLP,batteryTemp
```

**Beispiel:**
```
S,24.5,0.0,0.0,0,0,0,0,1.2,0.8,0.9,25.3
```

- `batVoltageLP` (Index 0): Batteriespannung in Volt
- `chgVoltage` (Index 1): Ladespannung in Volt
- `chgCurrentLP` (Index 2): Ladestrom in Ampere

## Funktionalitäten

### Batterieüberwachung
- **Unterspannungsschutz**: Warnung bei niedriger Batteriespannung
- **Ladeerkennung**: Erkennt angeschlossenes Ladegerät
- **Docking-Status**: Überprüft, ob Roboter gedockt ist
- **Ladeabschluss**: Erkennt vollständig geladene Batterie
- **Home-Empfehlung**: Empfiehlt Rückkehr zur Ladestation

### Sicherheitsfunktionen
- Automatische Abschaltung bei Unterspannung
- Überwachung der Ladezyklen
- Temperaturüberwachung (über Pico-Daten verfügbar)

## Tests

### test_battery_integration.py

Umfassende Tests für:
- Normale Batteriedatenverarbeitung
- Unterspannungserkennung
- Ladegerätanschluss-Erkennung
- Ladeabschluss-Erkennung
- Pico-Datenformat-Parsing

**Ausführung:**
```bash
cd sunray_py
python tests/test_battery_integration.py
```

## Geänderte Dateien

1. **main.py**
   - Integration von `battery.run()` in Hauptschleife
   - Erweiterte MQTT-Telemetrie mit Batteriedaten

2. **tests/test_battery_integration.py** (neu)
   - Umfassende Tests für Batterieintegration

3. **tests/README.md**
   - Dokumentation des neuen Tests

4. **BATTERY_INTEGRATION.md** (neu)
   - Diese Dokumentation

## Vorteile der Integration

1. **Vollständige Batterieüberwachung**: Alle Batteriedaten werden verarbeitet
2. **Erweiterte Telemetrie**: Detaillierte Batteriestatusinformationen über MQTT
3. **Verbesserte Sicherheit**: Proaktive Unterspannungsüberwachung
4. **Automatisches Lademanagement**: Intelligente Rückkehr zur Ladestation
5. **Testabdeckung**: Umfassende Tests für Zuverlässigkeit

## Nächste Schritte

- [ ] Integration von Batterietemperatur-Überwachung
- [ ] Erweiterte Ladezyklen-Analyse
- [ ] Batteriekapazitäts-Schätzung
- [ ] Energieverbrauchs-Optimierung
- [ ] Wartungsintervall-Berechnung