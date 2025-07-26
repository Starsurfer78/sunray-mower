#!/usr/bin/env python3
"""
Test-Skript für die automatische Ardusimple RTK Board Konfiguration.

Dieses Skript demonstriert:
1. Automatische Board-Konfiguration beim Start
2. Manuelle Neukonfiguration
3. Überprüfung der GPS-Daten

Verwendung:
    python test_rtk_config.py
"""

import time
import sys
from rtk_gps import RTKGPS

def test_rtk_configuration():
    """
    Testet die automatische RTK-Board-Konfiguration.
    """
    print("=== Ardusimple RTK Board Konfigurationstest ===")
    print()
    
    # Konfiguration laden
    print("1. Lade Konfiguration...")
    try:
        import json
        with open('config.json', 'r') as f:
            config = json.load(f)
            rtk_config = config.get('rtk_gps', {})
            port = rtk_config.get('port', '/dev/ttyUSB0')
            baudrate = rtk_config.get('baudrate', 115200)
            rtk_mode = rtk_config.get('rtk_mode', 'auto')
            ntrip_fallback = rtk_config.get('ntrip_fallback', True)
            auto_configure = rtk_config.get('auto_configure', True)
            print(f"✅ Konfiguration geladen: Port {port}, Baudrate {baudrate}")
    except (FileNotFoundError, json.JSONDecodeError, KeyError) as e:
        print(f"⚠️  Konfigurationsdatei nicht gefunden ({e}), verwende Standardwerte")
        port = "/dev/ttyUSB0"
        baudrate = 115200
        rtk_mode = "auto"
        ntrip_fallback = True
        auto_configure = True
    
    # RTK-GPS mit Konfiguration initialisieren
    print("2. Initialisiere RTK-GPS mit automatischer Konfiguration...")
    try:
        gps = RTKGPS(
            port=port,
            baudrate=baudrate,
            rtk_mode=rtk_mode,
            enable_ntrip_fallback=ntrip_fallback,
            auto_configure=auto_configure
        )
        print("✅ RTK-GPS erfolgreich initialisiert")
    except Exception as e:
        print(f"❌ Fehler bei RTK-GPS Initialisierung: {e}")
        print("Hinweis: Überprüfen Sie den USB-Port und die Verbindung")
        return False
    
    print()
    print("3. Warte auf GPS-Fix...")
    
    # Warte auf GPS-Daten
    fix_found = False
    start_time = time.time()
    timeout = 60  # 60 Sekunden Timeout
    
    while time.time() - start_time < timeout:
        gps_data = gps.read()
        
        if gps_data:
            print(f"GPS-Daten empfangen:")
            print(f"  - Position: {gps_data.get('lat', 0):.8f}, {gps_data.get('lon', 0):.8f}")
            print(f"  - Fix-Typ: {gps_data.get('fix_type', 0)}")
            print(f"  - Satelliten: {gps_data.get('nsat', 0)}")
            print(f"  - HDOP: {gps_data.get('hdop', 0):.2f}")
            print(f"  - RTK-Quelle: {gps_data.get('rtk_source', 'none')}")
            print(f"  - RTK-Alter: {gps_data.get('rtk_age', 999):.1f}s")
            
            if gps_data.get('fix_type', 0) >= 2:
                fix_found = True
                print("✅ GPS-Fix erhalten!")
                break
        
        time.sleep(1)
    
    if not fix_found:
        print("⚠️  Kein GPS-Fix innerhalb des Timeouts")
        print("Hinweis: Stellen Sie sicher, dass das GPS-Modul Satellitensicht hat")
    
    print()
    print("4. Teste manuelle Neukonfiguration...")
    
    try:
        gps.reconfigure_board()
        print("✅ Manuelle Neukonfiguration erfolgreich")
    except Exception as e:
        print(f"❌ Fehler bei manueller Neukonfiguration: {e}")
    
    print()
    print("5. Teste RTK-Status...")
    
    try:
        status = gps.get_fix_status()
        print(f"Fix-Status:")
        print(f"  - Fix-Typ: {status.get('fix_type', 0)} ({status.get('fix_description', 'Unknown')})")
        print(f"  - RTK-Status: {status.get('rtk_status', 'Unknown')}")
        print(f"  - Zeit seit letztem Fix: {status.get('time_since_last_fix', 0):.1f}s")
        print(f"  - NTRIP verbunden: {status.get('ntrip_connected', False)}")
    except Exception as e:
        print(f"❌ Fehler beim Abrufen des Fix-Status: {e}")
    
    print()
    print("6. Schließe Verbindung...")
    
    try:
        gps.close()
        print("✅ RTK-GPS Verbindung geschlossen")
    except Exception as e:
        print(f"❌ Fehler beim Schließen: {e}")
    
    print()
    print("=== Test abgeschlossen ===")
    return True

def main():
    """
    Hauptfunktion des Test-Skripts.
    """
    print("Ardusimple RTK Board - Automatische Konfiguration Test")
    print("======================================================")
    print()
    print("Dieses Skript testet die automatische Konfiguration des Ardusimple RTK Boards.")
    print("Stellen Sie sicher, dass:")
    print("1. Das Ardusimple RTK Board über USB verbunden ist")
    print("2. Der korrekte USB-Port in der Konfiguration angegeben ist")
    print("3. Das GPS-Modul Satellitensicht hat (im Freien)")
    print()
    
    input("Drücken Sie Enter zum Fortfahren...")
    print()
    
    success = test_rtk_configuration()
    
    if success:
        print("\n🎉 Test erfolgreich abgeschlossen!")
        print("Das Ardusimple RTK Board wurde automatisch konfiguriert.")
        print("Die Einstellungen sind im Flash gespeichert und bleiben erhalten.")
    else:
        print("\n❌ Test fehlgeschlagen!")
        print("Überprüfen Sie die Verbindung und Konfiguration.")
        return 1
    
    return 0

if __name__ == "__main__":
    sys.exit(main())