#!/usr/bin/env python3
"""
Test für Batterie-Spannungsfilterung
Überprüft, ob kurze Spannungsabfälle korrekt gefiltert werden.
"""

import time
import sys
import os

# Pfad für Import hinzufügen
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from battery import Battery
from config import Config

def test_voltage_filtering():
    """Test der Spannungsfilterung bei kurzen Abfällen"""
    print("=== Test: Batterie-Spannungsfilterung ===")
    
    # Battery-Instanz erstellen
    battery = Battery()
    
    print(f"Filter aktiviert: {battery.voltage_filter_enabled}")
    print(f"Tiefpass-Zeitkonstante: {battery.voltage_filter_time_constant}s")
    print(f"Median-Filter-Größe: {battery.voltage_median_filter_size}")
    print(f"Bestätigungszeit: {battery.low_voltage_confirmation_time}s")
    print()
    
    # Test 1: Normale Spannung
    print("Test 1: Normale Batteriespannung (24.0V)")
    for i in range(10):
        result = battery.run(24.0, 0.0, 0.0)
        time.sleep(0.1)
    
    print(f"  Gefilterte Spannung: {battery._last_battery_voltage:.2f}V")
    print(f"  Should go home: {battery.should_go_home()}")
    print(f"  Under voltage: {battery.under_voltage()}")
    print()
    
    # Test 2: Kurzer Spannungsabfall (sollte gefiltert werden)
    print("Test 2: Kurzer Spannungsabfall auf 20.0V (3 Sekunden)")
    start_time = time.time()
    
    # 3 Sekunden niedrige Spannung simulieren
    while time.time() - start_time < 3.0:
        result = battery.run(20.0, 0.0, 0.0)  # Unter go_home_threshold
        print(f"  Zeit: {time.time() - start_time:.1f}s, Gefiltert: {battery._last_battery_voltage:.2f}V, Go Home: {battery.should_go_home()}")
        time.sleep(0.5)
    
    print("  -> Kurzer Abfall sollte NICHT zu Go Home führen")
    print()
    
    # Test 3: Spannung wieder normal
    print("Test 3: Spannung wieder normal (24.0V)")
    for i in range(5):
        result = battery.run(24.0, 0.0, 0.0)
        time.sleep(0.1)
    
    print(f"  Gefilterte Spannung: {battery._last_battery_voltage:.2f}V")
    print(f"  Should go home: {battery.should_go_home()}")
    print()
    
    # Test 4: Anhaltend niedrige Spannung (sollte zu Go Home führen)
    print("Test 4: Anhaltend niedrige Spannung (20.0V für 12 Sekunden)")
    start_time = time.time()
    
    # 12 Sekunden niedrige Spannung (länger als confirmation_time)
    while time.time() - start_time < 12.0:
        result = battery.run(20.0, 0.0, 0.0)
        elapsed = time.time() - start_time
        print(f"  Zeit: {elapsed:.1f}s, Gefiltert: {battery._last_battery_voltage:.2f}V, Go Home: {battery.should_go_home()}")
        time.sleep(1.0)
    
    print("  -> Anhaltend niedrige Spannung sollte zu Go Home führen")
    print()
    
    # Test 5: Kritische Spannung (Switch Off) - verwende 18.0V (deutlich unter 20.0V Schwelle)
    print("Test 5: Kritische Spannung (18.0V für 12 Sekunden)")
    start_time = time.time()
    
    while time.time() - start_time < 12.0:
        result = battery.run(18.0, 0.0, 0.0)  # Deutlich unter switch_off_threshold (20.0V)
        elapsed = time.time() - start_time
        print(f"  Zeit: {elapsed:.1f}s, Gefiltert: {battery._last_battery_voltage:.2f}V, Under Voltage: {battery.under_voltage()}")
        time.sleep(1.0)
    
    print("  -> Kritische Spannung sollte zu Under Voltage führen")
    print()
    
    print("=== Test abgeschlossen ===")

def test_filter_disabled():
    """Test mit deaktivierter Filterung"""
    print("\n=== Test: Filter deaktiviert ===")
    
    # Konfiguration mit deaktiviertem Filter
    config = Config()
    config.set('battery.filtering.voltage_filter_enabled', False)
    
    battery = Battery(config)
    print(f"Filter aktiviert: {battery.voltage_filter_enabled}")
    
    # Kurzer Spannungsabfall ohne Filter
    print("Kurzer Spannungsabfall ohne Filter:")
    # Warte bis Startup-Phase beendet ist
    time.sleep(2.1)
    result = battery.run(20.0, 0.0, 0.0)  # Unter go_home_threshold (21.5V)
    print(f"  Spannung: {battery._last_battery_voltage:.2f}V")
    print(f"  Should go home: {battery.should_go_home()}")
    
    print("  -> Ohne Filter sollte sofort reagiert werden")

if __name__ == "__main__":
    test_voltage_filtering()
    test_filter_disabled()