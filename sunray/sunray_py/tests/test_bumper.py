#!/usr/bin/env python3
"""
Test-Skript für die verbesserte Bumper-Funktionalität.
Überprüft die korrekte Interpretation der Bumper-Bitmaske vom Pico.
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from obstacle_detection import BumperDetector
import time

def test_bumper_detection():
    """
    Testet die Bumper-Erkennung mit verschiedenen Bitmasken.
    """
    detector = BumperDetector()
    
    print("=== Bumper-Funktionstest ===")
    print("Bitmaske: Bit 0 = bumperX (links), Bit 1 = bumperY (rechts)")
    print()
    
    # Test-Szenarien
    test_cases = [
        (0, "Keine Bumper aktiviert"),
        (1, "Linker Bumper aktiviert (bumperX)"),
        (2, "Rechter Bumper aktiviert (bumperY)"),
        (3, "Beide Bumper aktiviert")
    ]
    
    for bumper_value, description in test_cases:
        print(f"Test: {description} (Bitmaske: {bumper_value:02b})")
        
        # Bumper-Zustand setzen
        collision = detector.detect_collision(bumper_value)
        
        # Zustand anzeigen
        left_active = (bumper_value & 0x01) > 0
        right_active = (bumper_value & 0x02) > 0
        
        print(f"  Links aktiv: {left_active}")
        print(f"  Rechts aktiv: {right_active}")
        print(f"  Kollision erkannt: {collision}")
        print(f"  Detector-Zustand: {detector.bumper_state}")
        print()
        
        # Kurz warten für Debouncing
        time.sleep(0.1)
        
        # Bumper wieder deaktivieren
        detector.detect_collision(0)
        time.sleep(0.1)
    
    print("=== Debouncing-Test ===")
    print("Teste schnelle Änderungen (sollten ignoriert werden)")
    
    # Schnelle Änderungen testen
    for i in range(5):
        collision = detector.detect_collision(1)  # Links aktivieren
        print(f"Schnelle Aktivierung {i+1}: {collision}")
        time.sleep(0.01)  # Unter Debounce-Zeit
        detector.detect_collision(0)  # Deaktivieren
        time.sleep(0.01)
    
    print()
    print("=== Kollisions-Reset-Test ===")
    
    # Kollision auslösen
    collision = detector.detect_collision(1)
    print(f"Kollision ausgelöst: {collision}")
    print(f"Kollisionsstatus: {detector.collision_detected}")
    
    # Warten bis Reset
    print("Warte auf automatischen Reset...")
    start_time = time.time()
    while detector.collision_detected and (time.time() - start_time) < 2.0:
        detector.detect_collision(0)  # Bumper nicht mehr gedrückt
        time.sleep(0.1)
    
    print(f"Reset nach {time.time() - start_time:.1f} Sekunden")
    print(f"Kollisionsstatus: {detector.collision_detected}")
    
    print("\n=== Test abgeschlossen ===")

if __name__ == '__main__':
    test_bumper_detection()