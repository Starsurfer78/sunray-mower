#!/usr/bin/env python3
"""
Pfadplanungsmodul für Sunray Mähroboter.
Implementiert verschiedene Mähmuster: linienbasiert, spiralförmig, zufällig.
"""

import math
import random
from typing import List, Optional, Tuple
from enum import Enum
from map import Point, Polygon

class MowPattern(Enum):
    """Verfügbare Mähmuster."""
    LINES = "lines"          # Parallele Linien
    SPIRAL = "spiral"        # Spiralförmig von außen nach innen
    RANDOM = "random"        # Zufällige Punkte
    PERIMETER = "perimeter"  # Umrandung zuerst

class PathPlanner:
    """
    Pfadplanungsklasse für verschiedene Mähmuster.
    
    Generiert optimierte Pfade für effizientes Mähen verschiedener Zonen
    unter Berücksichtigung von Hindernissen und Ausschlusszonen.
    """
    
    def __init__(self):
        self.current_pattern = MowPattern.LINES
        self.line_spacing = 0.3  # Meter zwischen Mählinien
        self.spiral_spacing = 0.3  # Meter zwischen Spiralwindungen
        self.random_points_per_m2 = 2  # Zufällige Punkte pro Quadratmeter
        self.current_zone_index = 0
        self.current_path_index = 0
        self.generated_paths: List[List[Point]] = []
        
    def set_pattern(self, pattern: MowPattern) -> None:
        """Setzt das aktuelle Mähmuster."""
        self.current_pattern = pattern
        self.generated_paths = []  # Pfade zurücksetzen
        self.current_path_index = 0
        
    def set_line_spacing(self, spacing: float) -> None:
        """Setzt den Abstand zwischen Mählinien."""
        self.line_spacing = max(0.1, spacing)  # Mindestens 10cm
        
    def set_spiral_spacing(self, spacing: float) -> None:
        """Setzt den Abstand zwischen Spiralwindungen."""
        self.spiral_spacing = max(0.1, spacing)  # Mindestens 10cm
        
    def generate_zone_path(self, zone: Polygon, obstacles: List[Polygon] = None) -> List[Point]:
        """
        Generiert einen Pfad für eine Zone basierend auf dem aktuellen Muster.
        
        Args:
            zone: Zu mähende Zone
            obstacles: Liste von Hindernissen in der Zone
            
        Returns:
            Liste von Wegpunkten
        """
        if obstacles is None:
            obstacles = []
            
        if self.current_pattern == MowPattern.LINES:
            return self._generate_line_pattern(zone, obstacles)
        elif self.current_pattern == MowPattern.SPIRAL:
            return self._generate_spiral_pattern(zone, obstacles)
        elif self.current_pattern == MowPattern.RANDOM:
            return self._generate_random_pattern(zone, obstacles)
        elif self.current_pattern == MowPattern.PERIMETER:
            return self._generate_perimeter_pattern(zone, obstacles)
        else:
            return [zone.get_center()]  # Fallback
            
    def _generate_line_pattern(self, zone: Polygon, obstacles: List[Polygon]) -> List[Point]:
        """
        Generiert parallele Mählinien in der Zone.
        """
        if len(zone.points) < 3:
            return [zone.get_center()]
            
        # Bounding Box der Zone ermitteln
        min_x = min(p.x for p in zone.points)
        max_x = max(p.x for p in zone.points)
        min_y = min(p.y for p in zone.points)
        max_y = max(p.y for p in zone.points)
        
        path = []
        y = min_y
        direction = 1  # 1 für links->rechts, -1 für rechts->links
        
        while y <= max_y:
            if direction == 1:
                # Links nach rechts
                start_point = Point(min_x, y)
                end_point = Point(max_x, y)
            else:
                # Rechts nach links
                start_point = Point(max_x, y)
                end_point = Point(min_x, y)
                
            # Prüfe ob Linie in Zone liegt und nicht durch Hindernisse geht
            line_points = self._clip_line_to_zone(start_point, end_point, zone, obstacles)
            path.extend(line_points)
            
            y += self.line_spacing
            direction *= -1  # Richtung wechseln für Boustrophedon-Muster
            
        return path
        
    def _generate_spiral_pattern(self, zone: Polygon, obstacles: List[Polygon]) -> List[Point]:
        """
        Generiert spiralförmiges Mähmuster von außen nach innen.
        """
        if len(zone.points) < 3:
            return [zone.get_center()]
            
        center = zone.get_center()
        path = []
        
        # Maximaler Radius basierend auf Zone
        max_radius = self._get_max_radius_in_zone(center, zone)
        
        # Spirale von außen nach innen
        radius = max_radius
        angle = 0
        angle_step = 0.1  # Radiant pro Schritt
        
        while radius > self.spiral_spacing:
            x = center.x + radius * math.cos(angle)
            y = center.y + radius * math.sin(angle)
            point = Point(x, y)
            
            # Prüfe ob Punkt in Zone liegt und nicht in Hindernis
            if self._point_in_zone(point, zone) and not self._point_in_obstacles(point, obstacles):
                path.append(point)
                
            angle += angle_step
            # Radius langsam verringern für Spirale
            radius -= self.spiral_spacing / (2 * math.pi / angle_step)
            
        return path
        
    def _generate_random_pattern(self, zone: Polygon, obstacles: List[Polygon]) -> List[Point]:
        """
        Generiert zufällige Mähpunkte in der Zone.
        """
        if len(zone.points) < 3:
            return [zone.get_center()]
            
        # Bounding Box der Zone
        min_x = min(p.x for p in zone.points)
        max_x = max(p.x for p in zone.points)
        min_y = min(p.y for p in zone.points)
        max_y = max(p.y for p in zone.points)
        
        # Anzahl Punkte basierend auf Zonengröße
        area = (max_x - min_x) * (max_y - min_y)
        num_points = int(area * self.random_points_per_m2)
        
        path = []
        attempts = 0
        max_attempts = num_points * 10  # Verhindere Endlosschleife
        
        while len(path) < num_points and attempts < max_attempts:
            x = random.uniform(min_x, max_x)
            y = random.uniform(min_y, max_y)
            point = Point(x, y)
            
            if self._point_in_zone(point, zone) and not self._point_in_obstacles(point, obstacles):
                path.append(point)
                
            attempts += 1
            
        return path
        
    def _generate_perimeter_pattern(self, zone: Polygon, obstacles: List[Polygon]) -> List[Point]:
        """
        Generiert Umrandungsmuster - folgt der Zonengrenze.
        """
        if len(zone.points) < 3:
            return [zone.get_center()]
            
        path = []
        
        # Äußere Umrandung
        for i, point in enumerate(zone.points):
            path.append(Point(point.x, point.y))
            
            # Zwischenpunkte für glatte Kurven
            next_point = zone.points[(i + 1) % len(zone.points)]
            mid_point = Point(
                (point.x + next_point.x) / 2,
                (point.y + next_point.y) / 2
            )
            path.append(mid_point)
            
        # Schließe den Ring
        if path:
            path.append(Point(zone.points[0].x, zone.points[0].y))
            
        return path
        
    def _clip_line_to_zone(self, start: Point, end: Point, zone: Polygon, obstacles: List[Polygon]) -> List[Point]:
        """
        Schneidet eine Linie an Zonengrenzen und Hindernissen ab.
        """
        # Vereinfachte Implementierung - prüfe nur Start- und Endpunkt
        points = []
        
        if self._point_in_zone(start, zone) and not self._point_in_obstacles(start, obstacles):
            points.append(start)
            
        if self._point_in_zone(end, zone) and not self._point_in_obstacles(end, obstacles):
            points.append(end)
            
        return points
        
    def _point_in_zone(self, point: Point, zone: Polygon) -> bool:
        """
        Prüft ob ein Punkt innerhalb einer Zone liegt (Ray-Casting-Algorithmus).
        """
        if len(zone.points) < 3:
            return False
            
        x, y = point.x, point.y
        n = len(zone.points)
        inside = False
        
        p1x, p1y = zone.points[0].x, zone.points[0].y
        for i in range(1, n + 1):
            p2x, p2y = zone.points[i % n].x, zone.points[i % n].y
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
        """
        Prüft ob ein Punkt in einem Hindernis liegt.
        """
        for obstacle in obstacles:
            if self._point_in_zone(point, obstacle):
                return True
        return False
        
    def _get_max_radius_in_zone(self, center: Point, zone: Polygon) -> float:
        """
        Ermittelt maximalen Radius vom Zentrum bis zur Zonengrenze.
        """
        max_dist = 0
        for point in zone.points:
            dist = math.sqrt((center.x - point.x)**2 + (center.y - point.y)**2)
            max_dist = max(max_dist, dist)
        return max_dist
        
    def get_next_waypoint(self, current_pos: Point, zones: List[Polygon]) -> Optional[Point]:
        """
        Gibt den nächsten Wegpunkt für die aktuelle Position zurück.
        
        Args:
            current_pos: Aktuelle Position des Roboters
            zones: Liste der zu mähenden Zonen
            
        Returns:
            Nächster Wegpunkt oder None wenn fertig
        """
        if not zones or self.current_zone_index >= len(zones):
            return None
            
        # Generiere Pfad für aktuelle Zone falls noch nicht vorhanden
        if not self.generated_paths or self.current_zone_index >= len(self.generated_paths):
            current_zone = zones[self.current_zone_index]
            zone_path = self.generate_zone_path(current_zone)
            
            if self.current_zone_index >= len(self.generated_paths):
                self.generated_paths.append(zone_path)
            else:
                self.generated_paths[self.current_zone_index] = zone_path
                
        # Hole aktuellen Pfad
        current_path = self.generated_paths[self.current_zone_index]
        
        if self.current_path_index >= len(current_path):
            # Aktuelle Zone abgeschlossen, zur nächsten wechseln
            self.current_zone_index += 1
            self.current_path_index = 0
            return self.get_next_waypoint(current_pos, zones)
            
        # Nächsten Wegpunkt zurückgeben
        next_point = current_path[self.current_path_index]
        self.current_path_index += 1
        
        return next_point
        
    def reset(self) -> None:
        """
        Setzt den Pfadplaner zurück.
        """
        self.current_zone_index = 0
        self.current_path_index = 0
        self.generated_paths = []
        
    def get_progress(self, zones: List[Polygon]) -> Tuple[float, int, int]:
        """
        Gibt den aktuellen Fortschritt zurück.
        
        Returns:
            (Gesamtfortschritt 0-1, aktuelle Zone, aktuelle Zone Fortschritt %)
        """
        if not zones:
            return 1.0, 0, 100
            
        total_zones = len(zones)
        completed_zones = self.current_zone_index
        
        # Fortschritt in aktueller Zone
        zone_progress = 0
        if self.current_zone_index < len(self.generated_paths):
            current_path = self.generated_paths[self.current_zone_index]
            if current_path:
                zone_progress = min(100, int((self.current_path_index / len(current_path)) * 100))
                
        # Gesamtfortschritt
        overall_progress = (completed_zones + zone_progress / 100) / total_zones
        
        return overall_progress, self.current_zone_index + 1, zone_progress