#!/usr/bin/env python3
"""
Erweiterte Pfadplanung für Sunray Mähroboter.

Kombiniert verschiedene Pfadplanungsalgorithmen:
- A*-Algorithmus für optimale Pfade
- Traditionelle Mähmuster (Linien, Spiral, etc.)
- Dynamische Hindernisvermeidung
- GPS-basierte Navigation
- Adaptive Pfadanpassung

Autor: Sunray Python Team
Version: 1.0
"""

import math
import time
from typing import List, Optional, Tuple, Dict, Callable
from enum import Enum
from dataclasses import dataclass

from map import Point, Polygon
from path_planner import PathPlanner, MowPattern
from astar_pathfinding import AStarPathfinder
from config import get_config

class PlanningStrategy(Enum):
    """Verfügbare Planungsstrategien."""
    TRADITIONAL = "traditional"    # Traditionelle Muster
    ASTAR = "astar"               # A*-basierte Planung
    HYBRID = "hybrid"             # Kombination beider
    ADAPTIVE = "adaptive"         # Adaptive Strategie

class PathType(Enum):
    """Pfadtypen für verschiedene Aufgaben."""
    MOWING = "mowing"             # Mähpfad
    TRANSIT = "transit"           # Transitpfad (ohne Mähen)
    RETURN_HOME = "return_home"   # Rückkehr zur Ladestation
    PERIMETER = "perimeter"       # Umrandung
    OBSTACLE_AVOIDANCE = "obstacle_avoidance"  # Hindernisvermeidung

@dataclass
class PathSegment:
    """Pfadsegment mit Metadaten."""
    points: List[Point]
    path_type: PathType
    estimated_time: float = 0.0
    mow_enabled: bool = True
    speed_factor: float = 1.0
    priority: int = 0

class AdvancedPathPlanner:
    """
    Erweiterte Pfadplanung mit A*-Integration.
    
    Diese Klasse kombiniert verschiedene Pfadplanungsansätze:
    - Traditionelle Mähmuster für Effizienz
    - A*-Algorithmus für Hindernisvermeidung
    - Dynamische Pfadanpassung
    - GPS-basierte Präzisionsnavigation
    - Adaptive Strategieauswahl
    
    Beispiel:
        planner = AdvancedPathPlanner()
        planner.set_strategy(PlanningStrategy.HYBRID)
        path = planner.plan_zone_coverage(zones, obstacles)
    """
    
    def __init__(self):
        """
        Initialisiert den erweiterten Pfadplaner.
        """
        self.config = get_config()
        
        # Untermodule
        self.traditional_planner = PathPlanner()
        self.astar_pathfinder = AStarPathfinder(grid_size=0.1)
        
        # Konfiguration
        planning_config = self.config.get('advanced_path_planning', {})
        self.strategy = PlanningStrategy(planning_config.get('strategy', 'hybrid'))
        self.max_segment_length = planning_config.get('max_segment_length', 10.0)  # Meter
        self.obstacle_detection_radius = planning_config.get('obstacle_detection_radius', 1.0)  # Meter
        self.replanning_threshold = planning_config.get('replanning_threshold', 0.5)  # Meter
        
        # Zustand
        self.current_plan: List[PathSegment] = []
        self.current_segment_index = 0
        self.current_point_index = 0
        self.obstacles: List[Polygon] = []
        self.dynamic_obstacles: List[Polygon] = []
        self.zones: List[Polygon] = []
        
        # Statistiken
        self.total_planned_distance = 0.0
        self.replanning_count = 0
        self.last_planning_time = 0.0
        
        # Callbacks
        self.obstacle_detected_callback = None
        self.replanning_callback = None
        self.segment_completed_callback = None
        
        print(f"Erweiterte Pfadplanung: Initialisiert (Strategie: {self.strategy.value})")
    
    def set_strategy(self, strategy: PlanningStrategy) -> None:
        """
        Setzt die Planungsstrategie.
        
        Args:
            strategy: Neue Planungsstrategie
        """
        self.strategy = strategy
        print(f"Erweiterte Pfadplanung: Strategie auf {strategy.value} gesetzt")
    
    def set_zones_and_obstacles(self, zones: List[Polygon], obstacles: List[Polygon]) -> None:
        """
        Setzt Zonen und Hindernisse für die Planung.
        
        Args:
            zones: Zu mähende Zonen
            obstacles: Statische Hindernisse
        """
        self.zones = zones
        self.obstacles = obstacles
        
        # A*-Pathfinder mit Hindernissen konfigurieren
        self.astar_pathfinder.set_obstacles(obstacles)
        
        print(f"Erweiterte Pfadplanung: {len(zones)} Zonen, {len(obstacles)} Hindernisse gesetzt")
    
    def plan_zone_coverage(self, pattern: MowPattern = MowPattern.LINES) -> bool:
        """
        Plant die vollständige Zonenabdeckung.
        
        Args:
            pattern: Mähmuster für traditionelle Planung
            
        Returns:
            bool: True wenn Planung erfolgreich
        """
        if not self.zones:
            print("Erweiterte Pfadplanung: Keine Zonen definiert")
            return False
        
        start_time = time.time()
        self.current_plan.clear()
        self.current_segment_index = 0
        self.current_point_index = 0
        
        try:
            if self.strategy == PlanningStrategy.TRADITIONAL:
                success = self._plan_traditional(pattern)
            elif self.strategy == PlanningStrategy.ASTAR:
                success = self._plan_astar()
            elif self.strategy == PlanningStrategy.HYBRID:
                success = self._plan_hybrid(pattern)
            elif self.strategy == PlanningStrategy.ADAPTIVE:
                success = self._plan_adaptive(pattern)
            else:
                success = self._plan_hybrid(pattern)  # Fallback
            
            if success:
                self._calculate_plan_statistics()
                self.last_planning_time = time.time() - start_time
                print(f"Erweiterte Pfadplanung: Plan erstellt in {self.last_planning_time:.2f}s")
                print(f"Erweiterte Pfadplanung: {len(self.current_plan)} Segmente, {self.total_planned_distance:.1f}m")
            
            return success
            
        except Exception as e:
            print(f"Erweiterte Pfadplanung: Fehler bei Planung - {e}")
            return False
    
    def _plan_traditional(self, pattern: MowPattern) -> bool:
        """
        Traditionelle Pfadplanung mit Mähmustern.
        """
        self.traditional_planner.set_pattern(pattern)
        
        for i, zone in enumerate(self.zones):
            # Mähpfad für Zone generieren
            zone_path = self.traditional_planner.generate_zone_path(zone, self.obstacles)
            
            if zone_path:
                # Pfad in Segmente aufteilen
                segments = self._split_path_into_segments(zone_path, PathType.MOWING)
                self.current_plan.extend(segments)
                
                # Transitpfad zur nächsten Zone (falls vorhanden)
                if i < len(self.zones) - 1:
                    next_zone = self.zones[i + 1]
                    transit_path = self._plan_transit_path(
                        zone_path[-1] if zone_path else zone.get_center(),
                        next_zone.get_center()
                    )
                    if transit_path:
                        transit_segment = PathSegment(
                            points=transit_path,
                            path_type=PathType.TRANSIT,
                            mow_enabled=False,
                            speed_factor=1.5
                        )
                        self.current_plan.append(transit_segment)
        
        return len(self.current_plan) > 0
    
    def _plan_astar(self) -> bool:
        """
        A*-basierte Pfadplanung.
        """
        for zone in self.zones:
            # Sampling-basierte Abdeckung der Zone
            coverage_points = self._generate_coverage_points(zone)
            
            if not coverage_points:
                continue
            
            # Optimale Reihenfolge mit TSP-Heuristik
            ordered_points = self._optimize_point_order(coverage_points)
            
            # A*-Pfade zwischen den Punkten
            zone_segments = []
            for i in range(len(ordered_points) - 1):
                start_point = ordered_points[i]
                end_point = ordered_points[i + 1]
                
                path = self.astar_pathfinder.find_path(
                    start_point, end_point, self.dynamic_obstacles
                )
                
                if path:
                    segment = PathSegment(
                        points=path,
                        path_type=PathType.MOWING,
                        mow_enabled=True
                    )
                    zone_segments.append(segment)
                else:
                    print(f"Erweiterte Pfadplanung: Kein A*-Pfad von {start_point} zu {end_point}")
            
            self.current_plan.extend(zone_segments)
        
        return len(self.current_plan) > 0
    
    def _plan_hybrid(self, pattern: MowPattern) -> bool:
        """
        Hybride Planung: Traditionell für Hauptbereiche, A* für Hindernisse.
        """
        self.traditional_planner.set_pattern(pattern)
        
        for zone in self.zones:
            # Traditioneller Pfad als Basis
            base_path = self.traditional_planner.generate_zone_path(zone, self.obstacles)
            
            if not base_path:
                continue
            
            # Pfad auf Hinderniskollisionen prüfen und A* verwenden
            refined_segments = []
            current_segment = []
            
            for i, point in enumerate(base_path):
                # Prüfe auf Hindernisse im Umkreis
                if self._point_near_obstacles(point, self.dynamic_obstacles):
                    # Aktuelles Segment abschließen
                    if current_segment:
                        segment = PathSegment(
                            points=current_segment.copy(),
                            path_type=PathType.MOWING
                        )
                        refined_segments.append(segment)
                        current_segment.clear()
                    
                    # A*-Umgehung planen
                    if i < len(base_path) - 1:
                        detour_path = self._plan_obstacle_detour(
                            point, base_path[i + 1], self.dynamic_obstacles
                        )
                        if detour_path:
                            detour_segment = PathSegment(
                                points=detour_path,
                                path_type=PathType.OBSTACLE_AVOIDANCE,
                                speed_factor=0.8
                            )
                            refined_segments.append(detour_segment)
                else:
                    current_segment.append(point)
            
            # Letztes Segment hinzufügen
            if current_segment:
                segment = PathSegment(
                    points=current_segment,
                    path_type=PathType.MOWING
                )
                refined_segments.append(segment)
            
            self.current_plan.extend(refined_segments)
        
        return len(self.current_plan) > 0
    
    def _plan_adaptive(self, pattern: MowPattern) -> bool:
        """
        Adaptive Planung basierend auf Zoneneigenschaften.
        """
        for zone in self.zones:
            # Zoneneigenschaften analysieren
            zone_area = self._calculate_polygon_area(zone)
            obstacle_density = self._calculate_obstacle_density(zone)
            zone_complexity = self._calculate_zone_complexity(zone)
            
            # Strategie basierend auf Eigenschaften wählen
            if obstacle_density > 0.3 or zone_complexity > 0.7:
                # Hohe Hindernisdichte oder Komplexität -> A*
                print(f"Adaptive Planung: A* für komplexe Zone (Dichte: {obstacle_density:.2f})")
                zone_segments = self._plan_zone_astar(zone)
            elif zone_area < 50.0:  # Kleine Zone
                # Kleine Zone -> Spiralmuster
                print(f"Adaptive Planung: Spiral für kleine Zone ({zone_area:.1f}m²)")
                self.traditional_planner.set_pattern(MowPattern.SPIRAL)
                zone_path = self.traditional_planner.generate_zone_path(zone, self.obstacles)
                zone_segments = self._split_path_into_segments(zone_path, PathType.MOWING)
            else:
                # Standard -> Linienmuster
                print(f"Adaptive Planung: Linien für Standardzone ({zone_area:.1f}m²)")
                self.traditional_planner.set_pattern(pattern)
                zone_path = self.traditional_planner.generate_zone_path(zone, self.obstacles)
                zone_segments = self._split_path_into_segments(zone_path, PathType.MOWING)
            
            self.current_plan.extend(zone_segments)
        
        return len(self.current_plan) > 0
    
    def _generate_coverage_points(self, zone: Polygon) -> List[Point]:
        """
        Generiert Abdeckungspunkte für eine Zone.
        """
        if len(zone.points) < 3:
            return [zone.get_center()]
        
        # Bounding Box
        min_x = min(p.x for p in zone.points)
        max_x = max(p.x for p in zone.points)
        min_y = min(p.y for p in zone.points)
        max_y = max(p.y for p in zone.points)
        
        # Gitterpunkte generieren
        spacing = 0.5  # Meter zwischen Punkten
        points = []
        
        y = min_y
        while y <= max_y:
            x = min_x
            while x <= max_x:
                point = Point(x, y)
                # Prüfe ob Punkt in Zone liegt
                if self._point_in_polygon(point, zone):
                    # Prüfe ob Punkt nicht in Hindernis liegt
                    if not self._point_in_obstacles(point, self.obstacles):
                        points.append(point)
                x += spacing
            y += spacing
        
        return points
    
    def _optimize_point_order(self, points: List[Point]) -> List[Point]:
        """
        Optimiert die Reihenfolge der Punkte (vereinfachte TSP-Heuristik).
        """
        if len(points) <= 2:
            return points
        
        # Nearest-Neighbor-Heuristik
        ordered = [points[0]]
        remaining = points[1:]
        
        while remaining:
            current = ordered[-1]
            nearest = min(remaining, key=lambda p: self._distance(current, p))
            ordered.append(nearest)
            remaining.remove(nearest)
        
        return ordered
    
    def _split_path_into_segments(self, path: List[Point], path_type: PathType) -> List[PathSegment]:
        """
        Teilt einen Pfad in Segmente auf.
        """
        if not path:
            return []
        
        segments = []
        current_segment = []
        current_length = 0.0
        
        for i, point in enumerate(path):
            current_segment.append(point)
            
            if i > 0:
                current_length += self._distance(path[i-1], point)
            
            # Segment bei maximaler Länge oder am Ende abschließen
            if current_length >= self.max_segment_length or i == len(path) - 1:
                if current_segment:
                    segment = PathSegment(
                        points=current_segment.copy(),
                        path_type=path_type,
                        estimated_time=current_length / 0.5  # Angenommene Geschwindigkeit
                    )
                    segments.append(segment)
                
                current_segment.clear()
                current_length = 0.0
        
        return segments
    
    def _plan_transit_path(self, start: Point, end: Point) -> Optional[List[Point]]:
        """
        Plant einen Transitpfad zwischen zwei Punkten.
        """
        # Versuche direkten Pfad
        if self._line_of_sight(start, end):
            return [start, end]
        
        # Verwende A* für Hindernisvermeidung
        return self.astar_pathfinder.find_path(start, end, self.dynamic_obstacles)
    
    def _plan_obstacle_detour(self, start: Point, end: Point, obstacles: List[Polygon]) -> Optional[List[Point]]:
        """
        Plant eine Umgehung um Hindernisse.
        """
        return self.astar_pathfinder.find_path(start, end, obstacles)
    
    def get_next_waypoint(self, current_position: Point) -> Optional[Tuple[Point, PathType]]:
        """
        Gibt den nächsten Wegpunkt zurück.
        
        Args:
            current_position: Aktuelle Position
            
        Returns:
            Tuple[Point, PathType]: Nächster Wegpunkt und Pfadtyp oder None
        """
        if not self.current_plan or self.current_segment_index >= len(self.current_plan):
            return None
        
        current_segment = self.current_plan[self.current_segment_index]
        
        if self.current_point_index >= len(current_segment.points):
            # Nächstes Segment
            self.current_segment_index += 1
            self.current_point_index = 0
            
            if self.segment_completed_callback:
                self.segment_completed_callback(current_segment)
            
            return self.get_next_waypoint(current_position)
        
        next_point = current_segment.points[self.current_point_index]
        self.current_point_index += 1
        
        return (next_point, current_segment.path_type)
    
    def add_dynamic_obstacle(self, obstacle: Polygon) -> None:
        """
        Fügt ein dynamisches Hindernis hinzu und löst Neuplanung aus.
        
        Args:
            obstacle: Neues Hindernis
        """
        self.dynamic_obstacles.append(obstacle)
        
        if self.obstacle_detected_callback:
            self.obstacle_detected_callback(obstacle)
        
        # Prüfe ob Neuplanung erforderlich
        if self._requires_replanning():
            self.replan_from_current_position()
    
    def _requires_replanning(self) -> bool:
        """
        Prüft ob eine Neuplanung erforderlich ist.
        """
        if not self.current_plan or self.current_segment_index >= len(self.current_plan):
            return False
        
        # Prüfe verbleibende Segmente auf Kollisionen
        for i in range(self.current_segment_index, len(self.current_plan)):
            segment = self.current_plan[i]
            for point in segment.points:
                if self._point_near_obstacles(point, self.dynamic_obstacles):
                    return True
        
        return False
    
    def replan_from_current_position(self) -> bool:
        """
        Plant den Pfad von der aktuellen Position neu.
        
        Returns:
            bool: True wenn Neuplanung erfolgreich
        """
        if not self.current_plan:
            return False
        
        self.replanning_count += 1
        
        if self.replanning_callback:
            self.replanning_callback(self.replanning_count)
        
        # Verbleibende Zonen ermitteln
        remaining_zones = self.zones[self.current_segment_index:] if self.current_segment_index < len(self.zones) else []
        
        if not remaining_zones:
            return True  # Bereits fertig
        
        # Neuplanung mit aktuellen Hindernissen
        old_plan = self.current_plan.copy()
        old_segment_index = self.current_segment_index
        
        # Temporär alle Hindernisse setzen
        all_obstacles = self.obstacles + self.dynamic_obstacles
        self.astar_pathfinder.set_obstacles(all_obstacles)
        
        # Neue Planung
        success = self.plan_zone_coverage()
        
        if not success:
            # Rollback bei Fehler
            self.current_plan = old_plan
            self.current_segment_index = old_segment_index
            print("Erweiterte Pfadplanung: Neuplanung fehlgeschlagen - Rollback")
            return False
        
        print(f"Erweiterte Pfadplanung: Neuplanung erfolgreich (#{self.replanning_count})")
        return True
    
    # Hilfsmethoden
    def _point_in_polygon(self, point: Point, polygon: Polygon) -> bool:
        """Ray-Casting-Algorithmus für Punkt-in-Polygon-Test."""
        if len(polygon.points) < 3:
            return False
        
        x, y = point.x, point.y
        n = len(polygon.points)
        inside = False
        
        p1x, p1y = polygon.points[0].x, polygon.points[0].y
        for i in range(1, n + 1):
            p2x, p2y = polygon.points[i % n].x, polygon.points[i % n].y
            if y > min(p1y, p2y):
                if y <= max(p1y, p2y):
                    if x <= max(p1x, p2x):
                        if p1y != p2y:
                            xinters = (y - p1y) * (p2x - p1x) / (p2y - p1y) + p1x
                        if p1x == p2x or x <= xinters:
                            inside = not inside
            p1x, p1y = p2x, p2y
        
        return inside
    
    def _point_in_obstacles(self, point: Point, obstacles: List[Polygon]) -> bool:
        """Prüft ob Punkt in Hindernissen liegt."""
        for obstacle in obstacles:
            if self._point_in_polygon(point, obstacle):
                return True
        return False
    
    def _point_near_obstacles(self, point: Point, obstacles: List[Polygon]) -> bool:
        """Prüft ob Punkt nahe Hindernissen liegt."""
        for obstacle in obstacles:
            for obs_point in obstacle.points:
                if self._distance(point, obs_point) < self.obstacle_detection_radius:
                    return True
        return False
    
    def _line_of_sight(self, start: Point, end: Point) -> bool:
        """Prüft freie Sichtlinie zwischen zwei Punkten."""
        # Vereinfachte Implementierung
        steps = int(self._distance(start, end) / 0.1)  # 10cm Schritte
        if steps == 0:
            return True
        
        dx = (end.x - start.x) / steps
        dy = (end.y - start.y) / steps
        
        for i in range(steps + 1):
            check_point = Point(start.x + i * dx, start.y + i * dy)
            if self._point_in_obstacles(check_point, self.obstacles + self.dynamic_obstacles):
                return False
        
        return True
    
    def _distance(self, p1: Point, p2: Point) -> float:
        """Euklidische Distanz zwischen zwei Punkten."""
        return math.sqrt((p1.x - p2.x)**2 + (p1.y - p2.y)**2)
    
    def _calculate_polygon_area(self, polygon: Polygon) -> float:
        """Berechnet die Fläche eines Polygons."""
        if len(polygon.points) < 3:
            return 0.0
        
        area = 0.0
        n = len(polygon.points)
        
        for i in range(n):
            j = (i + 1) % n
            area += polygon.points[i].x * polygon.points[j].y
            area -= polygon.points[j].x * polygon.points[i].y
        
        return abs(area) / 2.0
    
    def _calculate_obstacle_density(self, zone: Polygon) -> float:
        """Berechnet die Hindernisdichte in einer Zone."""
        zone_area = self._calculate_polygon_area(zone)
        if zone_area == 0:
            return 0.0
        
        obstacle_area = 0.0
        for obstacle in self.obstacles:
            # Vereinfachte Überschneidungsberechnung
            if self._polygons_intersect(zone, obstacle):
                obstacle_area += self._calculate_polygon_area(obstacle)
        
        return min(1.0, obstacle_area / zone_area)
    
    def _calculate_zone_complexity(self, zone: Polygon) -> float:
        """Berechnet die Komplexität einer Zone (0-1)."""
        if len(zone.points) < 3:
            return 0.0
        
        # Basiert auf Anzahl der Ecken und Konkavität
        complexity = min(1.0, len(zone.points) / 20.0)  # Mehr Ecken = komplexer
        
        # TODO: Konkavitätsanalyse hinzufügen
        
        return complexity
    
    def _polygons_intersect(self, poly1: Polygon, poly2: Polygon) -> bool:
        """Vereinfachte Polygonüberschneidung."""
        # Prüfe ob ein Punkt von poly1 in poly2 liegt
        for point in poly1.points:
            if self._point_in_polygon(point, poly2):
                return True
        
        # Prüfe umgekehrt
        for point in poly2.points:
            if self._point_in_polygon(point, poly1):
                return True
        
        return False
    
    def _plan_zone_astar(self, zone: Polygon) -> List[PathSegment]:
        """Plant eine Zone mit A*."""
        coverage_points = self._generate_coverage_points(zone)
        ordered_points = self._optimize_point_order(coverage_points)
        
        segments = []
        for i in range(len(ordered_points) - 1):
            path = self.astar_pathfinder.find_path(
                ordered_points[i], ordered_points[i + 1], self.dynamic_obstacles
            )
            if path:
                segment = PathSegment(points=path, path_type=PathType.MOWING)
                segments.append(segment)
        
        return segments
    
    def _calculate_plan_statistics(self) -> None:
        """Berechnet Planungsstatistiken."""
        self.total_planned_distance = 0.0
        
        for segment in self.current_plan:
            for i in range(len(segment.points) - 1):
                self.total_planned_distance += self._distance(
                    segment.points[i], segment.points[i + 1]
                )
    
    def get_planning_status(self) -> Dict:
        """
        Gibt den aktuellen Planungsstatus zurück.
        """
        total_segments = len(self.current_plan)
        completed_segments = self.current_segment_index
        
        progress = 0.0
        if total_segments > 0:
            progress = completed_segments / total_segments
        
        return {
            'strategy': self.strategy.value,
            'total_segments': total_segments,
            'completed_segments': completed_segments,
            'current_segment_index': self.current_segment_index,
            'current_point_index': self.current_point_index,
            'progress': progress,
            'total_planned_distance': self.total_planned_distance,
            'replanning_count': self.replanning_count,
            'last_planning_time': self.last_planning_time,
            'dynamic_obstacles': len(self.dynamic_obstacles)
        }
    
    def set_obstacle_detected_callback(self, callback: Callable) -> None:
        """Setzt Callback für Hinderniserkennung."""
        self.obstacle_detected_callback = callback
    
    def set_replanning_callback(self, callback: Callable) -> None:
        """Setzt Callback für Neuplanung."""
        self.replanning_callback = callback
    
    def set_segment_completed_callback(self, callback: Callable) -> None:
        """Setzt Callback für abgeschlossene Segmente."""
        self.segment_completed_callback = callback
    
    def reset(self) -> None:
        """
        Setzt den Planer zurück.
        """
        self.current_plan.clear()
        self.current_segment_index = 0
        self.current_point_index = 0
        self.dynamic_obstacles.clear()
        self.replanning_count = 0
        self.total_planned_distance = 0.0
        
        print("Erweiterte Pfadplanung: Zurückgesetzt")