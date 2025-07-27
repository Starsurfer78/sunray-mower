#!/usr/bin/env python3
"""
Test-Skript für GPS-Sicherheitsmechanismen
Validiert die Implementierung der GPS-Sicherheitslogik
"""

import json
import time
from gps_safety_manager import GPSSafetyManager, GPSSafetyLevel

def test_gps_safety_scenarios():
    """Testet verschiedene GPS-Sicherheitsszenarien."""
    
    # Konfiguration laden
    with open('config.json', 'r') as f:
        config = json.load(f)
    
    # GPS Safety Manager initialisieren
    safety_manager = GPSSafetyManager(config)
    
    print("=== GPS-Sicherheitstest gestartet ===")
    print()
    
    # Test 1: RTK Fixed - Normaler Betrieb
    print("Test 1: RTK Fixed (Normaler Betrieb)")
    gps_data = {
        'mode': 6,  # RTK Fixed
        'accuracy': 0.02,  # 2cm
        'lat': 15.0,
        'lon': 12.0
    }
    position = (15.0, 12.0)
    result = safety_manager.evaluate_gps_safety(gps_data, position)
    print(f"  Sicherheitslevel: {result['safety_level']}")
    print(f"  Kann mähen: {result['can_mow']}")
    print(f"  Empfohlene Aktion: {result['recommended_action']}")
    print(f"  Geschwindigkeitsfaktor: {result['speed_factor']}")
    print()
    
    # Test 2: RTK Float in kritischer Zone
    print("Test 2: RTK Float in kritischer Zone")
    gps_data = {
        'mode': 5,  # RTK Float
        'accuracy': 0.15,  # 15cm
        'lat': 15.0,
        'lon': 12.0
    }
    position = (15.0, 12.0)  # In kritischer Zone
    result = safety_manager.evaluate_gps_safety(gps_data, position)
    print(f"  Sicherheitslevel: {result['safety_level']}")
    print(f"  Kann mähen: {result['can_mow']}")
    print(f"  Empfohlene Aktion: {result['recommended_action']}")
    print(f"  Geschwindigkeitsfaktor: {result['speed_factor']}")
    print()
    
    # Test 3: 3D Fix - Sofortiger Stopp
    print("Test 3: 3D Fix (Sofortiger Stopp)")
    gps_data = {
        'mode': 3,  # 3D Fix
        'accuracy': 1.5,  # 1.5m
        'lat': 15.0,
        'lon': 12.0
    }
    position = (15.0, 12.0)
    result = safety_manager.evaluate_gps_safety(gps_data, position)
    print(f"  Sicherheitslevel: {result['safety_level']}")
    print(f"  Kann mähen: {result['can_mow']}")
    print(f"  Empfohlene Aktion: {result['recommended_action']}")
    print(f"  RTK-Wartezeit verbleibend: {result['rtk_wait_remaining']:.1f}s")
    print()
    
    # Test 4: Kein GPS-Fix
    print("Test 4: Kein GPS-Fix")
    gps_data = {
        'mode': 1,  # Kein Fix
        'accuracy': 999.0,
        'lat': None,
        'lon': None
    }
    position = None
    result = safety_manager.evaluate_gps_safety(gps_data, position)
    print(f"  Sicherheitslevel: {result['safety_level']}")
    print(f"  Kann mähen: {result['can_mow']}")
    print(f"  Empfohlene Aktion: {result['recommended_action']}")
    print(f"  RTK-Wartezeit verbleibend: {result['rtk_wait_remaining']:.1f}s")
    print()
    
    # Test 5: RTK-Timeout-Simulation
    print("Test 5: RTK-Timeout-Simulation")
    # Simuliere 3D Fix für längere Zeit
    safety_manager._rtk_wait_start_time = time.time() - 310  # 310 Sekunden ago
    safety_manager._current_safety_level = GPSSafetyLevel.FIX_3D_WAIT
    
    gps_data = {
        'mode': 3,  # 3D Fix
        'accuracy': 1.0,
        'lat': 15.0,
        'lon': 12.0
    }
    position = (15.0, 12.0)
    result = safety_manager.evaluate_gps_safety(gps_data, position)
    print(f"  Sicherheitslevel: {result['safety_level']}")
    print(f"  Kann mähen: {result['can_mow']}")
    print(f"  Empfohlene Aktion: {result['recommended_action']}")
    print(f"  RTK-Wartezeit verbleibend: {result['rtk_wait_remaining']:.1f}s")
    print()
    
    print("=== GPS-Sicherheitstest abgeschlossen ===")

class MockZone:
    def __init__(self, points):
        self.points = [MockPoint(p[0], p[1]) for p in points]

class MockPoint:
    def __init__(self, x, y):
        self.x = x
        self.y = y

class MockMap:
    def __init__(self):
        # Mähzonen definieren
        self.zones = [
            MockZone([[0, 0], [10, 0], [10, 10], [0, 10]]),  # Sichere Zone
            MockZone([[15, 15], [25, 15], [25, 25], [15, 25]])  # Weitere Mähzone
        ]
        
        # Ausschlusszonen definieren
        self.exclusions = [
            MockZone([[12, 12], [18, 12], [18, 18], [12, 18]])  # Kritische Zone
        ]

def test_zone_detection():
    """Testet die Zonenerkennung."""
    print("\n=== Zonenerkennungstest ===")
    
    # GPS-Sicherheitsmanager mit Mock-Karte initialisieren
    config = {
        'gps_safety': {
            'rtk_fixed_threshold': 0.02,
            'rtk_float_threshold': 0.1,
            'fix_3d_threshold': 2.0,
            'degradation_timeout': 10.0,
            'rtk_wait_timeout': 300.0,
            'safe_zone_margin': 2.0,
            'critical_zone_margin': 1.0,
            'rtk_float_speed_factor': 0.5,
            'critical_zone_speed_factor': 0.3
        }
    }
    
    mock_map = MockMap()
    safety_manager = GPSSafetyManager(config, mock_map)
    
    # Test verschiedene Positionen
    test_positions = [
        (5.0, 5.0, "Sichere Mähzone"),
        (15.0, 15.0, "Ausschlusszone (kritisch)"),
        (20.0, 20.0, "Mähzone außerhalb Ausschluss"),
        (30.0, 30.0, "Außerhalb aller Zonen")
    ]
    
    for x, y, description in test_positions:
        position_safety = safety_manager._evaluate_position_safety((x, y))
        print(f"\nPosition ({x}, {y}) - {description}:")
        print(f"  In Mähzone: {position_safety['in_mow_zone']}")
        print(f"  In Ausschlusszone: {position_safety['in_exclusion']}")
        print(f"  In sicherer Zone: {position_safety['in_safe_zone']}")
        print(f"  In kritischer Zone: {position_safety['in_critical_area']}")
        print(f"  Abstand zur Grenze: {position_safety['distance_to_boundary']:.1f}m")
    
    print("\n=== Zonenerkennungstest abgeschlossen ===")

if __name__ == '__main__':
    try:
        test_gps_safety_scenarios()
        print()
        test_zone_detection()
    except Exception as e:
        print(f"Fehler beim Test: {e}")
        import traceback
        traceback.print_exc()