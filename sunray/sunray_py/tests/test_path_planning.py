#!/usr/bin/env python3
"""
Testskript für die Pfadplanungsfunktionalität.
Testet PathPlanner, Motor-Integration und API-Endpunkte.
"""

import time
import requests
import json
from path_planner import PathPlanner, MowPattern
from map import Point, Polygon

def test_path_planner():
    """Testet die PathPlanner-Klasse direkt."""
    print("=== PathPlanner Test ===")
    
    # Testzone erstellen
    zone_points = [Point(0, 0), Point(10, 0), Point(10, 10), Point(0, 10)]
    zone = Polygon(zone_points)
    
    # Hindernis erstellen
    obstacle_points = [Point(4, 4), Point(6, 4), Point(6, 6), Point(4, 6)]
    obstacle = Polygon(obstacle_points)
    
    # PathPlanner initialisieren
    planner = PathPlanner()
    planner.set_pattern(MowPattern.LINES)
    planner.set_line_spacing(1.0)
    
    print(f"Muster: {planner.current_pattern}")
    print(f"Linienabstand: {planner.line_spacing}m")
    
    # Wegpunkte für Zone generieren
    waypoints = planner.generate_zone_path(zone, [obstacle])
    
    print(f"Generierte Wegpunkte für Zone: {len(waypoints)}")
    for i, waypoint in enumerate(waypoints[:10]):  # Nur erste 10 anzeigen
        print(f"Wegpunkt {i+1}: ({waypoint.x:.2f}, {waypoint.y:.2f})")
    
    print(f"Generierte Wegpunkte: {len(waypoints)}")
    print()

def test_api_endpoints():
    """Testet die HTTP-API-Endpunkte."""
    print("=== API Test ===")
    base_url = "http://localhost:5000"
    
    # Test 1: Navigationsstatus abrufen
    try:
        response = requests.get(f"{base_url}/navigation/status")
        print(f"Status-Abfrage: {response.status_code}")
        if response.status_code == 200:
            print(f"Status: {response.json()}")
    except requests.exceptions.ConnectionError:
        print("Server nicht erreichbar - starte zuerst main.py")
        return
    
    # Test 2: Mähmuster setzen
    pattern_data = {
        "pattern": "LINES",
        "line_spacing": 0.5
    }
    response = requests.post(f"{base_url}/navigation/pattern", json=pattern_data)
    print(f"Muster setzen: {response.status_code} - {response.json()}")
    
    # Test 3: Mähzonen setzen
    zones_data = {
        "zones": [
            {
                "points": [[0, 0], [20, 0], [20, 15], [0, 15]]
            },
            {
                "points": [[25, 5], [35, 5], [35, 10], [25, 10]]
            }
        ]
    }
    response = requests.post(f"{base_url}/navigation/zones", json=zones_data)
    print(f"Zonen setzen: {response.status_code} - {response.json()}")
    
    # Test 4: Autonomes Mähen starten
    response = requests.post(f"{base_url}/navigation/start")
    print(f"Navigation starten: {response.status_code} - {response.json()}")
    
    # Test 5: Status nach Start prüfen
    time.sleep(1)
    response = requests.get(f"{base_url}/navigation/status")
    print(f"Status nach Start: {response.status_code} - {response.json()}")
    
    # Test 6: Navigation stoppen
    time.sleep(2)
    response = requests.post(f"{base_url}/navigation/stop")
    print(f"Navigation stoppen: {response.status_code} - {response.json()}")
    
    print()

def test_different_patterns():
    """Testet verschiedene Mähmuster."""
    print("=== Muster-Test ===")
    
    # Testzone
    zone_points = [Point(0, 0), Point(8, 0), Point(8, 8), Point(0, 8)]
    zone = Polygon(zone_points)
    
    patterns = [MowPattern.LINES, MowPattern.SPIRAL, MowPattern.RANDOM, MowPattern.PERIMETER]
    
    for pattern in patterns:
        print(f"\nTeste Muster: {pattern.name}")
        planner = PathPlanner()
        planner.set_pattern(pattern)
        planner.set_line_spacing(1.5)
        
        waypoints = planner.generate_zone_path(zone, [])
        
        print(f"  Generierte Wegpunkte: {len(waypoints)}")
        for i, waypoint in enumerate(waypoints[:5]):  # Nur erste 5 anzeigen
            print(f"  Wegpunkt {i+1}: ({waypoint.x:.2f}, {waypoint.y:.2f})")

def main():
    """Hauptfunktion für alle Tests."""
    print("Pfadplanungs-Test Suite")
    print("=" * 50)
    
    # Direkte PathPlanner-Tests
    test_path_planner()
    
    # Verschiedene Muster testen
    test_different_patterns()
    
    # API-Tests (nur wenn Server läuft)
    print("Teste API-Endpunkte...")
    print("(Starte zuerst main.py für vollständige API-Tests)")
    test_api_endpoints()
    
    print("=" * 50)
    print("Tests abgeschlossen!")

if __name__ == '__main__':
    main()