#!/usr/bin/env python3
"""
Demo-Skript für die erweiterte Pfadplanung des Sunray Mähroboters.

Dieses Skript demonstriert:
- Verschiedene Planungsstrategien
- Dynamische Hindernisvermeidung
- Adaptive Strategieauswahl
- Integration mit GPS-Navigation
- Performance-Monitoring

Autor: Sunray Python Team
Version: 1.0
"""

import time
import json
from typing import List

# Sunray Module
from map import Point, Polygon
from advanced_path_planner import AdvancedPathPlanner, PlanningStrategy, PathType
from astar_pathfinding import AStarPathfinder
from path_planner import MowPattern
from gps_navigation import GPSNavigation

def create_test_zones() -> List[Polygon]:
    """
    Erstellt Testzonen für die Demonstration.
    """
    zones = []
    
    # Zone 1: Rechteckige Hauptfläche
    main_zone = Polygon([
        Point(0, 0),
        Point(20, 0),
        Point(20, 15),
        Point(0, 15)
    ])
    zones.append(main_zone)
    
    # Zone 2: L-förmige Fläche
    l_zone = Polygon([
        Point(25, 0),
        Point(35, 0),
        Point(35, 10),
        Point(30, 10),
        Point(30, 15),
        Point(25, 15)
    ])
    zones.append(l_zone)
    
    # Zone 3: Kleine runde Fläche (approximiert)
    small_zone = Polygon([
        Point(40, 5),
        Point(43, 3),
        Point(45, 5),
        Point(43, 7),
        Point(40, 5)
    ])
    zones.append(small_zone)
    
    return zones

def create_test_obstacles() -> List[Polygon]:
    """
    Erstellt Testhindernisse für die Demonstration.
    """
    obstacles = []
    
    # Hindernis 1: Baum in der Hauptzone
    tree = Polygon([
        Point(8, 6),
        Point(10, 6),
        Point(10, 8),
        Point(8, 8)
    ])
    obstacles.append(tree)
    
    # Hindernis 2: Blumenbeet
    flower_bed = Polygon([
        Point(15, 2),
        Point(18, 2),
        Point(18, 5),
        Point(15, 5)
    ])
    obstacles.append(flower_bed)
    
    # Hindernis 3: Gartenhaus
    garden_house = Polygon([
        Point(27, 12),
        Point(32, 12),
        Point(32, 14),
        Point(27, 14)
    ])
    obstacles.append(garden_house)
    
    return obstacles

def demonstrate_strategy(planner: AdvancedPathPlanner, strategy: PlanningStrategy, 
                       pattern: MowPattern = MowPattern.LINES) -> dict:
    """
    Demonstriert eine spezifische Planungsstrategie.
    
    Args:
        planner: Der Pfadplaner
        strategy: Die zu testende Strategie
        pattern: Das Mähmuster (für traditionelle Planung)
        
    Returns:
        dict: Statistiken der Planung
    """
    print(f"\n=== Teste Strategie: {strategy.value.upper()} ===")
    
    # Strategie setzen
    planner.set_strategy(strategy)
    
    # Zeitmessung
    start_time = time.time()
    
    # Planung durchführen
    success = planner.plan_zone_coverage(pattern)
    
    planning_time = time.time() - start_time
    
    if success:
        status = planner.get_planning_status()
        print(f"✅ Planung erfolgreich in {planning_time:.3f}s")
        print(f"   Segmente: {status['total_segments']}")
        print(f"   Geplante Distanz: {status['total_planned_distance']:.1f}m")
        print(f"   Strategie: {status['strategy']}")
        
        return {
            'success': True,
            'planning_time': planning_time,
            'segments': status['total_segments'],
            'distance': status['total_planned_distance'],
            'strategy': status['strategy']
        }
    else:
        print(f"❌ Planung fehlgeschlagen nach {planning_time:.3f}s")
        return {
            'success': False,
            'planning_time': planning_time,
            'segments': 0,
            'distance': 0,
            'strategy': strategy.value
        }

def simulate_navigation(planner: AdvancedPathPlanner, max_waypoints: int = 20) -> dict:
    """
    Simuliert die Navigation entlang des geplanten Pfads.
    
    Args:
        planner: Der Pfadplaner
        max_waypoints: Maximale Anzahl zu simulierender Wegpunkte
        
    Returns:
        dict: Navigationsstatistiken
    """
    print("\n--- Simuliere Navigation ---")
    
    current_position = Point(0, 0)
    waypoints_visited = 0
    total_distance = 0.0
    path_types = {}
    
    for i in range(max_waypoints):
        # Nächsten Wegpunkt abrufen
        result = planner.get_next_waypoint(current_position)
        
        if result is None:
            print("🏁 Navigation abgeschlossen - keine weiteren Wegpunkte")
            break
        
        waypoint, path_type = result
        
        # Distanz berechnen
        distance = ((waypoint.x - current_position.x)**2 + 
                   (waypoint.y - current_position.y)**2)**0.5
        total_distance += distance
        
        # Statistiken aktualisieren
        path_types[path_type.value] = path_types.get(path_type.value, 0) + 1
        waypoints_visited += 1
        
        print(f"   Wegpunkt {i+1}: ({waypoint.x:.1f}, {waypoint.y:.1f}) - {path_type.value} - {distance:.1f}m")
        
        # Position aktualisieren
        current_position = waypoint
        
        # Kurze Pause für Simulation
        time.sleep(0.1)
    
    print(f"📊 Navigation: {waypoints_visited} Wegpunkte, {total_distance:.1f}m Gesamtdistanz")
    print(f"   Pfadtypen: {path_types}")
    
    return {
        'waypoints_visited': waypoints_visited,
        'total_distance': total_distance,
        'path_types': path_types
    }

def demonstrate_dynamic_obstacles(planner: AdvancedPathPlanner) -> None:
    """
    Demonstriert die Behandlung dynamischer Hindernisse.
    
    Args:
        planner: Der Pfadplaner
    """
    print("\n=== Dynamische Hindernisse ===")
    
    # Callback für Hinderniserkennung
    def obstacle_detected(obstacle):
        print(f"🚧 Dynamisches Hindernis erkannt: {len(obstacle.points)} Punkte")
    
    def replanning_triggered(count):
        print(f"🔄 Neuplanung #{count} ausgelöst")
    
    # Callbacks registrieren
    planner.set_obstacle_detected_callback(obstacle_detected)
    planner.set_replanning_callback(replanning_triggered)
    
    # Initiale Planung
    planner.set_strategy(PlanningStrategy.HYBRID)
    success = planner.plan_zone_coverage(MowPattern.LINES)
    
    if not success:
        print("❌ Initiale Planung fehlgeschlagen")
        return
    
    initial_status = planner.get_planning_status()
    print(f"📋 Initiale Planung: {initial_status['total_segments']} Segmente")
    
    # Dynamisches Hindernis hinzufügen
    print("\n➕ Füge dynamisches Hindernis hinzu...")
    dynamic_obstacle = Polygon([
        Point(5, 5),
        Point(7, 5),
        Point(7, 7),
        Point(5, 7)
    ])
    
    planner.add_dynamic_obstacle(dynamic_obstacle)
    
    # Status nach Neuplanung
    time.sleep(0.5)  # Kurz warten für Neuplanung
    new_status = planner.get_planning_status()
    print(f"📋 Nach Neuplanung: {new_status['total_segments']} Segmente")
    print(f"   Neuplanungen: {new_status['replanning_count']}")
    
    # Zweites dynamisches Hindernis
    print("\n➕ Füge zweites dynamisches Hindernis hinzu...")
    dynamic_obstacle2 = Polygon([
        Point(12, 8),
        Point(14, 8),
        Point(14, 10),
        Point(12, 10)
    ])
    
    planner.add_dynamic_obstacle(dynamic_obstacle2)
    
    # Finaler Status
    time.sleep(0.5)
    final_status = planner.get_planning_status()
    print(f"📋 Finaler Status: {final_status['total_segments']} Segmente")
    print(f"   Neuplanungen: {final_status['replanning_count']}")
    print(f"   Dynamische Hindernisse: {final_status['dynamic_obstacles']}")

def performance_comparison() -> None:
    """
    Vergleicht die Performance verschiedener Strategien.
    """
    print("\n=== Performance-Vergleich ===")
    
    # Testzonen und Hindernisse erstellen
    zones = create_test_zones()
    obstacles = create_test_obstacles()
    
    # Planer initialisieren
    planner = AdvancedPathPlanner()
    planner.set_zones_and_obstacles(zones, obstacles)
    
    # Strategien testen
    strategies = [
        (PlanningStrategy.TRADITIONAL, MowPattern.LINES),
        (PlanningStrategy.TRADITIONAL, MowPattern.SPIRAL),
        (PlanningStrategy.ASTAR, MowPattern.LINES),
        (PlanningStrategy.HYBRID, MowPattern.LINES),
        (PlanningStrategy.ADAPTIVE, MowPattern.LINES)
    ]
    
    results = []
    
    for strategy, pattern in strategies:
        # Planer zurücksetzen
        planner.reset()
        
        # Strategie testen
        result = demonstrate_strategy(planner, strategy, pattern)
        result['pattern'] = pattern.value
        results.append(result)
    
    # Ergebnisse zusammenfassen
    print("\n📊 Performance-Zusammenfassung:")
    print("Strategy\t\tPattern\t\tTime(s)\tSegments\tDistance(m)\tSuccess")
    print("-" * 80)
    
    for result in results:
        success_icon = "✅" if result['success'] else "❌"
        print(f"{result['strategy']:<15}\t{result.get('pattern', 'N/A'):<10}\t"
              f"{result['planning_time']:.3f}\t{result['segments']:<8}\t"
              f"{result['distance']:<10.1f}\t{success_icon}")
    
    # Beste Strategie ermitteln
    successful_results = [r for r in results if r['success']]
    if successful_results:
        best_time = min(successful_results, key=lambda x: x['planning_time'])
        best_distance = min(successful_results, key=lambda x: x['distance'])
        
        print(f"\n🏆 Schnellste Planung: {best_time['strategy']} ({best_time['planning_time']:.3f}s)")
        print(f"🏆 Kürzeste Distanz: {best_distance['strategy']} ({best_distance['distance']:.1f}m)")

def adaptive_strategy_demo() -> None:
    """
    Demonstriert die adaptive Strategieauswahl.
    """
    print("\n=== Adaptive Strategieauswahl ===")
    
    # Verschiedene Zonentypen erstellen
    test_cases = [
        {
            'name': 'Große offene Fläche',
            'zones': [Polygon([
                Point(0, 0), Point(50, 0), Point(50, 30), Point(0, 30)
            ])],
            'obstacles': []
        },
        {
            'name': 'Kleine komplexe Fläche',
            'zones': [Polygon([
                Point(0, 0), Point(5, 0), Point(5, 5), Point(0, 5)
            ])],
            'obstacles': [Polygon([
                Point(1, 1), Point(2, 1), Point(2, 2), Point(1, 2)
            ])]
        },
        {
            'name': 'Mittlere Fläche mit vielen Hindernissen',
            'zones': [Polygon([
                Point(0, 0), Point(20, 0), Point(20, 15), Point(0, 15)
            ])],
            'obstacles': [
                Polygon([Point(3, 3), Point(5, 3), Point(5, 5), Point(3, 5)]),
                Polygon([Point(8, 8), Point(10, 8), Point(10, 10), Point(8, 10)]),
                Polygon([Point(15, 2), Point(17, 2), Point(17, 4), Point(15, 4)]),
                Polygon([Point(12, 12), Point(14, 12), Point(14, 14), Point(12, 14)])
            ]
        }
    ]
    
    planner = AdvancedPathPlanner()
    
    for test_case in test_cases:
        print(f"\n--- {test_case['name']} ---")
        
        # Zonen und Hindernisse setzen
        planner.set_zones_and_obstacles(test_case['zones'], test_case['obstacles'])
        
        # Adaptive Strategie verwenden
        result = demonstrate_strategy(planner, PlanningStrategy.ADAPTIVE)
        
        if result['success']:
            # Zeige welche Strategie gewählt wurde
            status = planner.get_planning_status()
            print(f"   🎯 Gewählte Strategie: {status['strategy']}")
        
        planner.reset()

def main():
    """
    Hauptfunktion für die Demonstration.
    """
    print("🤖 Sunray Erweiterte Pfadplanung - Demo")
    print("=" * 50)
    
    try:
        # Performance-Vergleich
        performance_comparison()
        
        # Adaptive Strategieauswahl
        adaptive_strategy_demo()
        
        # Navigation simulieren
        print("\n=== Navigation-Simulation ===")
        zones = create_test_zones()
        obstacles = create_test_obstacles()
        
        planner = AdvancedPathPlanner()
        planner.set_zones_and_obstacles(zones, obstacles)
        planner.set_strategy(PlanningStrategy.HYBRID)
        
        if planner.plan_zone_coverage(MowPattern.LINES):
            simulate_navigation(planner, max_waypoints=10)
        
        # Dynamische Hindernisse
        demonstrate_dynamic_obstacles(planner)
        
        print("\n✅ Demo abgeschlossen!")
        
    except Exception as e:
        print(f"❌ Fehler während der Demo: {e}")
        import traceback
        traceback.print_exc()

if __name__ == '__main__':
    main()