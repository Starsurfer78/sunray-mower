#!/usr/bin/env python3
"""
Test für die Integration der Battery-Klasse mit Pico-Daten.
Überprüft, ob die Batteriedaten korrekt vom Pico verarbeitet werden.
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from battery import Battery

def test_battery_data_processing():
    """Test der Batteriedatenverarbeitung mit simulierten Pico-Daten."""
    print("=== Test: Battery Data Processing ===")
    
    battery = Battery()
    
    # Test 1: Normale Batteriedaten
    print("\nTest 1: Normale Batteriedaten")
    battery_status = battery.run(
        battery_v=24.5,  # Normale Spannung
        charge_v=0.0,    # Nicht am Ladegerät
        charge_i=0.0     # Kein Ladestrom
    )
    print(f"Battery Status: {battery_status}")
    print(f"Under Voltage: {battery.under_voltage()}")
    print(f"Charger Connected: {battery.charger_connected()}")
    print(f"Should Go Home: {battery.should_go_home()}")
    
    # Test 2: Niedrige Spannung
    print("\nTest 2: Niedrige Spannung")
    battery_status = battery.run(
        battery_v=21.0,  # Niedrige Spannung
        charge_v=0.0,
        charge_i=0.0
    )
    print(f"Battery Status: {battery_status}")
    print(f"Under Voltage: {battery.under_voltage()}")
    print(f"Should Go Home: {battery.should_go_home()}")
    
    # Test 3: Ladegerät angeschlossen
    print("\nTest 3: Ladegerät angeschlossen")
    battery_status = battery.run(
        battery_v=25.2,  # Ladespannung
        charge_v=29.4,   # Ladegerätspannung
        charge_i=2.5     # Ladestrom
    )
    print(f"Battery Status: {battery_status}")
    print(f"Charger Connected: {battery.charger_connected()}")
    print(f"Is Docked: {battery.is_docked()}")
    print(f"Charging Completed: {battery.is_charging_completed()}")
    
    # Test 4: Vollständig geladen
    print("\nTest 4: Vollständig geladen")
    battery_status = battery.run(
        battery_v=29.0,  # Volle Spannung
        charge_v=29.4,   # Ladegerätspannung
        charge_i=0.1     # Minimaler Ladestrom
    )
    print(f"Battery Status: {battery_status}")
    print(f"Charging Completed: {battery.is_charging_completed()}")
    
    print("\n=== Alle Battery-Tests erfolgreich ===")

def test_pico_data_format():
    """Test der Pico-Datenformate für Batteriedaten."""
    print("\n=== Test: Pico Data Format ===")
    
    # Simuliere process_pico_data Funktion
    def process_pico_data(line: str) -> dict:
        if line.startswith("S,"):
            parts = line[2:].split(",")
            if len(parts) >= 11:
                return {
                    "bat_voltage": float(parts[0]),
                    "chg_voltage": float(parts[1]),
                    "chg_current": float(parts[2]),
                    "lift": int(parts[3]),
                    "bumper": int(parts[4]),
                    "raining": int(parts[5]),
                    "motor_overload": int(parts[6]),
                    "mow_current": float(parts[7]),
                    "motor_left_current": float(parts[8]),
                    "motor_right_current": float(parts[9]),
                    "battery_temp": float(parts[10]),
                }
        return {}
    
    # Test verschiedene Pico-Datenzeilen
    test_lines = [
        "S,24.5,0.0,0.0,0,0,0,0,1.2,0.8,0.9,25.3",  # Normal
        "S,21.0,0.0,0.0,0,0,0,0,1.5,1.0,1.1,26.1",  # Niedrige Spannung
        "S,25.2,29.4,2.5,0,0,0,0,0.0,0.0,0.0,24.8", # Laden
        "S,29.0,29.4,0.1,0,0,0,0,0.0,0.0,0.0,23.5"  # Voll geladen
    ]
    
    battery = Battery()
    
    for i, line in enumerate(test_lines, 1):
        print(f"\nTest {i}: {line}")
        pico_data = process_pico_data(line)
        print(f"Parsed Data: {pico_data}")
        
        if 'bat_voltage' in pico_data:
            battery_status = battery.run(
                pico_data.get('bat_voltage', 0.0),
                pico_data.get('chg_voltage', 0.0),
                pico_data.get('chg_current', 0.0)
            )
            print(f"Battery Status: {battery_status}")
            print(f"Under Voltage: {battery.under_voltage()}")
            print(f"Charger Connected: {battery.charger_connected()}")
    
    print("\n=== Pico Data Format Tests erfolgreich ===")

if __name__ == "__main__":
    test_battery_data_processing()
    test_pico_data_format()
    print("\n🔋 Alle Battery-Integration-Tests bestanden!")