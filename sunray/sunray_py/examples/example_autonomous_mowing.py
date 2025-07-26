#!/usr/bin/env python3
"""
Beispielskript für autonomes Mähen mit Pfadplanung.

Zeigt die Verwendung der neuen Pfadplanungsfunktionalität
der Motor-Klasse für vollautomatisches Mähen.
"""

import time
from motor import Motor
from map import Point, Polygon
from path_planner import MowPattern
from hardware_manager import get_hardware_manager

def create_example_zones():
    """
    Erstellt Beispiel-Mähzonen für die Demonstration.
    
    Returns:
        List[Polygon]: Liste von Mähzonen
    """
    # Rechteckige Hauptzone (10x8 Meter)
    main_zone = Polygon([
        Point(0, 0),
        Point(10, 0),
        Point(10, 8),
        Point(0, 8)
    ])
    
    # Kleinere Nebenzone (5x3 Meter)
    side_zone = Polygon([
        Point(12, 2),
        Point(17, 2),
        Point(17, 5),
        Point(12, 5)
    ])
    
    return [main_zone, side_zone]

def create_example_obstacles():
    """
    Erstellt Beispiel-Hindernisse.
    
    Returns:
        List[Polygon]: Liste von Hindernissen
    """
    # Baum in der Hauptzone
    tree = Polygon([
        Point(4, 3),
        Point(6, 3),
        Point(6, 5),
        Point(4, 5)
    ])
    
    # Blumenbeet
    flower_bed = Polygon([
        Point(1, 6),
        Point(3, 6),
        Point(3, 7.5),
        Point(1, 7.5)
    ])
    
    return [tree, flower_bed]

def demonstrate_line_pattern():
    """
    Demonstriert das Linienmuster für systematisches Mähen.
    """
    print("\n=== LINIENMUSTER DEMONSTRATION ===")
    
    # Motor mit Hardware-Manager initialisieren
    hw_manager = get_hardware_manager()
    motor = Motor(hw_manager)
    motor.begin()
    
    # Zonen und Hindernisse setzen
    zones = create_example_zones()
    obstacles = create_example_obstacles()
    
    motor.set_mow_zones(zones)
    motor.set_obstacles(obstacles)
    
    # Linienmuster konfigurieren
    motor.set_mow_pattern(MowPattern.LINES)
    motor.set_line_spacing(0.3)  # 30cm Abstand zwischen Linien
    
    # Startposition setzen (Ecke der ersten Zone)
    motor.update_position(0.5, 0.5)
    
    # Mähmotor aktivieren
    motor.set_mow_state(True)
    
    # Autonomes Mähen starten
    if motor.start_autonomous_mowing():
        print("Linienmuster-Mähen gestartet...")
        
        # Simulation für 30 Sekunden
        start_time = time.time()
        while time.time() - start_time < 30:
            # Motorsteuerung ausführen (inkl. Navigation)
            motor.run()
            
            # Status anzeigen
            status = motor.get_navigation_status()
            if status['target_waypoint']:
                print(f"Ziel: ({status['target_waypoint'][0]:.1f}, {status['target_waypoint'][1]:.1f}), "
                      f"Fortschritt: {status['progress']:.1%}")
            
            time.sleep(0.1)  # 10Hz für Demo
            
            # Beenden wenn alle Zonen abgeschlossen
            if not status['navigation_enabled']:
                print("Alle Zonen abgeschlossen!")
                break
    
    motor.stop_autonomous_mowing()
    print("Linienmuster-Demo beendet")

def demonstrate_spiral_pattern():
    """
    Demonstriert das Spiralmuster für effizientes Mähen.
    """
    print("\n=== SPIRALMUSTER DEMONSTRATION ===")
    
    hw_manager = get_hardware_manager()
    motor = Motor(hw_manager)
    motor.begin()
    
    # Nur eine Zone für Spirale verwenden
    zones = [create_example_zones()[0]]  # Nur Hauptzone
    motor.set_mow_zones(zones)
    
    # Spiralmuster konfigurieren
    motor.set_mow_pattern(MowPattern.SPIRAL)
    motor.path_planner.set_spiral_spacing(0.4)  # 40cm zwischen Spiralwindungen
    
    # Startposition im Zentrum
    motor.update_position(5.0, 4.0)
    
    motor.set_mow_state(True)
    
    if motor.start_autonomous_mowing():
        print("Spiralmuster-Mähen gestartet...")
        
        # Simulation für 20 Sekunden
        start_time = time.time()
        while time.time() - start_time < 20:
            motor.run()
            
            status = motor.get_navigation_status()
            if status['target_waypoint']:
                print(f"Spirale: ({status['target_waypoint'][0]:.1f}, {status['target_waypoint'][1]:.1f})")
            
            time.sleep(0.1)
            
            if not status['navigation_enabled']:
                break
    
    motor.stop_autonomous_mowing()
    print("Spiralmuster-Demo beendet")

def demonstrate_random_pattern():
    """
    Demonstriert das Zufallsmuster für unvorhersagbares Mähen.
    """
    print("\n=== ZUFALLSMUSTER DEMONSTRATION ===")
    
    hw_manager = get_hardware_manager()
    motor = Motor(hw_manager)
    motor.begin()
    
    zones = create_example_zones()
    obstacles = create_example_obstacles()
    
    motor.set_mow_zones(zones)
    motor.set_obstacles(obstacles)
    
    # Zufallsmuster konfigurieren
    motor.set_mow_pattern(MowPattern.RANDOM)
    motor.path_planner.random_points_per_m2 = 3  # 3 Punkte pro Quadratmeter
    
    motor.update_position(2.0, 2.0)
    motor.set_mow_state(True)
    
    if motor.start_autonomous_mowing():
        print("Zufallsmuster-Mähen gestartet...")
        
        start_time = time.time()
        while time.time() - start_time < 15:
            motor.run()
            
            status = motor.get_navigation_status()
            if status['target_waypoint']:
                print(f"Zufallspunkt: ({status['target_waypoint'][0]:.1f}, {status['target_waypoint'][1]:.1f})")
            
            time.sleep(0.1)
            
            if not status['navigation_enabled']:
                break
    
    motor.stop_autonomous_mowing()
    print("Zufallsmuster-Demo beendet")

def demonstrate_perimeter_pattern():
    """
    Demonstriert das Umrandungsmuster für Kantenmähen.
    """
    print("\n=== UMRANDUNGSMUSTER DEMONSTRATION ===")
    
    hw_manager = get_hardware_manager()
    motor = Motor(hw_manager)
    motor.begin()
    
    zones = create_example_zones()
    motor.set_mow_zones(zones)
    
    # Umrandungsmuster
    motor.set_mow_pattern(MowPattern.PERIMETER)
    
    motor.update_position(0.0, 0.0)
    motor.set_mow_state(True)
    
    if motor.start_autonomous_mowing():
        print("Umrandungsmuster-Mähen gestartet...")
        
        start_time = time.time()
        while time.time() - start_time < 25:
            motor.run()
            
            status = motor.get_navigation_status()
            if status['target_waypoint']:
                print(f"Umrandung: ({status['target_waypoint'][0]:.1f}, {status['target_waypoint'][1]:.1f})")
            
            time.sleep(0.1)
            
            if not status['navigation_enabled']:
                break
    
    motor.stop_autonomous_mowing()
    print("Umrandungsmuster-Demo beendet")

def demonstrate_mixed_strategy():
    """
    Demonstriert eine gemischte Mähstrategie:
    1. Erst Umrandung mähen
    2. Dann Linienmuster für die Fläche
    """
    print("\n=== GEMISCHTE MÄHSTRATEGIE ===")
    
    hw_manager = get_hardware_manager()
    motor = Motor(hw_manager)
    motor.begin()
    
    zones = create_example_zones()
    obstacles = create_example_obstacles()
    
    motor.set_mow_zones(zones)
    motor.set_obstacles(obstacles)
    motor.update_position(0.0, 0.0)
    motor.set_mow_state(True)
    
    # Phase 1: Umrandung
    print("Phase 1: Umrandung mähen...")
    motor.set_mow_pattern(MowPattern.PERIMETER)
    
    if motor.start_autonomous_mowing():
        start_time = time.time()
        while time.time() - start_time < 15:
            motor.run()
            
            status = motor.get_navigation_status()
            if not status['navigation_enabled']:
                print("Umrandung abgeschlossen")
                break
            
            time.sleep(0.1)
    
    # Phase 2: Linienmuster
    print("Phase 2: Flächenmähen mit Linien...")
    motor.set_mow_pattern(MowPattern.LINES)
    motor.set_line_spacing(0.25)
    
    if motor.start_autonomous_mowing():
        start_time = time.time()
        while time.time() - start_time < 20:
            motor.run()
            
            status = motor.get_navigation_status()
            if not status['navigation_enabled']:
                print("Flächenmähen abgeschlossen")
                break
            
            time.sleep(0.1)
    
    motor.stop_autonomous_mowing()
    print("Gemischte Strategie abgeschlossen")

def main():
    """
    Hauptfunktion - führt alle Demonstrationen aus.
    """
    print("=== AUTONOMES MÄHEN MIT PFADPLANUNG ===")
    print("Demonstration verschiedener Mähmuster")
    
    try:
        # Verschiedene Muster demonstrieren
        demonstrate_line_pattern()
        time.sleep(2)
        
        demonstrate_spiral_pattern()
        time.sleep(2)
        
        demonstrate_random_pattern()
        time.sleep(2)
        
        demonstrate_perimeter_pattern()
        time.sleep(2)
        
        demonstrate_mixed_strategy()
        
        print("\n=== ALLE DEMONSTRATIONEN ABGESCHLOSSEN ===")
        
    except KeyboardInterrupt:
        print("\nDemo durch Benutzer abgebrochen")
    except Exception as e:
        print(f"\nFehler in Demo: {e}")
    finally:
        print("Demo beendet")

if __name__ == "__main__":
    main()