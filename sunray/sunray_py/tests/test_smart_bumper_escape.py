#!/usr/bin/env python3
"""
Test-Skript für die SmartBumperEscapeOp-Funktionalität.
Testet die richtungsabhängige Bumper-Ausweichlogik.
"""

import time
import sys
import os

# Pfad zum sunray_py Verzeichnis hinzufügen
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from op import SmartBumperEscapeOp
from motor import Motor
from hardware_manager import get_hardware_manager

def test_smart_bumper_escape():
    """
    Testet die SmartBumperEscapeOp mit verschiedenen Bumper-Kombinationen.
    """
    print("=== SmartBumperEscapeOp Funktionstest ===")
    print("Testet richtungsabhängige Bumper-Ausweichlogik\n")
    
    # Mock Hardware Manager für Tests
    class MockHardwareManager:
        def send_motor_command(self, left, right, mow):
            print(f"  Motor-Kommando: Links={left}, Rechts={right}, Mäher={mow}")
        
        def send_command(self, cmd):
            print(f"  Hardware-Kommando: {cmd}")
    
    # Mock Motor für Tests
    class MockMotor:
        def __init__(self):
            self.hw_manager = MockHardwareManager()
        
        def stop_immediately(self, include_mower=True):
            print(f"  Motor gestoppt (Mäher: {include_mower})")
        
        def set_linear_angular_speed(self, linear, angular):
            print(f"  Geschwindigkeit gesetzt: Linear={linear:.2f} m/s, Angular={angular:.2f} rad/s")
    
    motor = MockMotor()
    
    # Test-Szenarien
    test_scenarios = [
        {
            'name': 'Rechter Bumper ausgelöst',
            'params': {
                'left_bumper': False,
                'right_bumper': True,
                'robot_position': {'x': 5.0, 'y': 3.0, 'heading': 1.57}  # 90 Grad
            },
            'expected_direction': 'links'
        },
        {
            'name': 'Linker Bumper ausgelöst',
            'params': {
                'left_bumper': True,
                'right_bumper': False,
                'robot_position': {'x': 2.0, 'y': 1.0, 'heading': 0.0}  # 0 Grad
            },
            'expected_direction': 'rechts'
        },
        {
            'name': 'Beide Bumper ausgelöst',
            'params': {
                'left_bumper': True,
                'right_bumper': True,
                'robot_position': {'x': 1.0, 'y': 1.0, 'heading': 3.14}  # 180 Grad
            },
            'expected_direction': 'zufällig'
        },
        {
            'name': 'Keine Bumper ausgelöst',
            'params': {
                'left_bumper': False,
                'right_bumper': False,
                'robot_position': {'x': 0.0, 'y': 0.0, 'heading': 0.0}
            },
            'expected_direction': 'zufällig'
        }
    ]
    
    for i, scenario in enumerate(test_scenarios, 1):
        print(f"Test {i}: {scenario['name']}")
        print(f"  Parameter: {scenario['params']}")
        print(f"  Erwartete Richtung: {scenario['expected_direction']}")
        
        # SmartBumperEscapeOp erstellen und starten
        escape_op = SmartBumperEscapeOp("test_smart_escape", motor=motor)
        escape_op.start(scenario['params'])
        
        # Kurz warten und dann Phase simulieren
        print("  Phasen-Simulation:")
        
        # Phase 1: Stop (0.3s)
        print("    Phase: Stop")
        time.sleep(0.1)  # Verkürzt für Test
        
        # Phase 2: Reverse (1.0s)
        escape_op.phase = "reverse"
        escape_op.phase_start_time = time.time()
        escape_op.run()
        time.sleep(0.1)
        
        # Phase 3: Curve (3.0s)
        escape_op.phase = "curve"
        escape_op.phase_start_time = time.time()
        escape_op.run()
        time.sleep(0.1)
        
        # Phase 4: Return (2.0s)
        escape_op.phase = "return"
        escape_op.phase_start_time = time.time()
        escape_op.run()
        time.sleep(0.1)
        
        # Operation beenden
        escape_op.stop()
        print(f"  ✅ Test {i} abgeschlossen\n")

def test_phase_transitions():
    """
    Testet die Phasenübergänge der SmartBumperEscapeOp.
    """
    print("=== Phasenübergangs-Test ===")
    
    class MockMotor:
        def stop_immediately(self, include_mower=True):
            print(f"Motor gestoppt")
        
        def set_linear_angular_speed(self, linear, angular):
            direction = "vorwärts" if linear > 0 else "rückwärts" if linear < 0 else "stopp"
            rotation = "rechts" if angular > 0 else "links" if angular < 0 else "gerade"
            print(f"Bewegung: {direction} ({linear:.2f} m/s), {rotation} ({angular:.2f} rad/s)")
    
    motor = MockMotor()
    
    # Test mit rechtem Bumper
    params = {
        'left_bumper': False,
        'right_bumper': True,
        'robot_position': {'x': 1.0, 'y': 1.0, 'heading': 0.0}
    }
    
    escape_op = SmartBumperEscapeOp("phase_test", motor=motor)
    escape_op.start(params)
    
    # Verkürzte Phasendauern für Test
    escape_op.stop_duration = 0.1
    escape_op.reverse_duration = 0.1
    escape_op.curve_duration = 0.1
    escape_op.return_duration = 0.1
    
    print("Starte Phasen-Simulation...")
    
    # Simulation der Phasen
    start_time = time.time()
    while escape_op.active and (time.time() - start_time) < 2.0:  # Max 2 Sekunden
        escape_op.run()
        time.sleep(0.05)  # 50ms zwischen Updates
    
    print("✅ Phasenübergangs-Test abgeschlossen\n")

def test_map_integration():
    """
    Testet die Integration mit dem Map-Modul (falls verfügbar).
    """
    print("=== Map-Integration Test ===")
    
    class MockMotor:
        def stop_immediately(self, include_mower=True):
            pass
        def set_linear_angular_speed(self, linear, angular):
            pass
    
    motor = MockMotor()
    
    params = {
        'left_bumper': False,
        'right_bumper': True,
        'robot_position': {'x': 1.0, 'y': 1.0, 'heading': 0.0}
    }
    
    escape_op = SmartBumperEscapeOp("map_test", motor=motor)
    
    try:
        escape_op.start(params)
        
        # Test der _is_safe_position Methode
        test_positions = [
            (0.0, 0.0),
            (1.0, 1.0),
            (5.0, 5.0),
            (-1.0, -1.0)
        ]
        
        print("Teste Positionssicherheit:")
        for x, y in test_positions:
            is_safe = escape_op._is_safe_position(x, y)
            print(f"  Position ({x}, {y}): {'✅ Sicher' if is_safe else '❌ Unsicher'}")
        
        escape_op.stop()
        print("✅ Map-Integration Test abgeschlossen")
        
    except Exception as e:
        print(f"⚠️  Map-Integration nicht verfügbar: {e}")
    
    print()

if __name__ == "__main__":
    print("SmartBumperEscapeOp Test Suite")
    print("=" * 50)
    
    try:
        test_smart_bumper_escape()
        test_phase_transitions()
        test_map_integration()
        
        print("🎉 Alle Tests erfolgreich abgeschlossen!")
        
    except Exception as e:
        print(f"❌ Test fehlgeschlagen: {e}")
        import traceback
        traceback.print_exc()