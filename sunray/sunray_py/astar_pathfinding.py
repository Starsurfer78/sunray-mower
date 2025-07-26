#!/usr/bin/env python3
"""
A* Pfadplanungsalgorithmus für Sunray Mähroboter.

Implementiert den A*-Algorithmus für optimale Pfadplanung:
- Hinderniserkennung und -vermeidung
- Dynamische Pfadanpassung
- Optimierte Routenberechnung
- Integration mit GPS-Navigation
- Echtzeit-Pfadplanung

Autor: Sunray Python Team
Version: 1.0
"""

import math
import heapq
from typing import List, Tuple, Optional, Set, Dict
from dataclasses import dataclass, field
from enum import Enum

from map import Point, Polygon
from config import get_config

class NodeType(Enum):
    """Knotentypen für A*-Pfadplanung."""
    FREE = "free"          # Freier Bereich
    OBSTACLE = "obstacle"  # Hindernis
    GOAL = "goal"          # Ziel
    START = "start"        # Start
    PATH = "path"          # Pfad

@dataclass
class AStarNode:
    """Knoten für A*-Algorithmus."""
    x: int
    y: int
    g_cost: float = float('inf')  # Kosten vom Start
    h_cost: float = 0.0           # Heuristische Kosten zum Ziel
    f_cost: float = float('inf')  # Gesamtkosten (g + h)
    parent: Optional['AStarNode'] = None
    node_type: NodeType = NodeType.FREE
    
    def __post_init__(self):
        self.f_cost = self.g_cost + self.h_cost
    
    def __lt__(self, other):
        return self.f_cost < other.f_cost
    
    def __eq__(self, other):
        return self.x == other.x and self.y == other.y
    
    def __hash__(self):
        return hash((self.x, self.y))

class AStarPathfinder:
    """
    A*-Pfadplanungsalgorithmus für optimale Routenberechnung.
    
    Diese Klasse implementiert den A*-Algorithmus für die Pfadplanung:
    - Findet optimale Pfade zwischen Start- und Zielpunkt
    - Berücksichtigt Hindernisse und Ausschlusszonen
    - Unterstützt verschiedene Heuristiken
    - Dynamische Pfadanpassung bei Hindernisänderungen
    - Integration mit GPS-Navigation
    
    Beispiel:
        pathfinder = AStarPathfinder(grid_size=0.1)
        path = pathfinder.find_path(start_point, goal_point, obstacles)
        if path:
            print(f"Pfad gefunden mit {len(path)} Wegpunkten")
    """
    
    def __init__(self, grid_size: float = 0.1):
        """
        Initialisiert den A*-Pfadfinder.
        
        Args:
            grid_size: Größe der Gitterzellen in Metern
        """
        self.config = get_config()
        self.grid_size = grid_size
        
        # A*-Parameter aus Konfiguration
        astar_config = self.config.get('astar_pathfinding', {})
        self.diagonal_movement = astar_config.get('diagonal_movement', True)
        self.heuristic_weight = astar_config.get('heuristic_weight', 1.0)
        self.obstacle_inflation = astar_config.get('obstacle_inflation', 0.2)  # Meter
        self.max_iterations = astar_config.get('max_iterations', 10000)
        
        # Gitter und Knoten
        self.grid: Dict[Tuple[int, int], AStarNode] = {}
        self.obstacles: Set[Tuple[int, int]] = set()
        self.bounds = {'min_x': 0, 'max_x': 0, 'min_y': 0, 'max_y': 0}
        
        # Bewegungsrichtungen (8-Richtungen wenn diagonal erlaubt)
        if self.diagonal_movement:
            self.directions = [
                (-1, -1), (-1, 0), (-1, 1),
                (0, -1),           (0, 1),
                (1, -1),  (1, 0),  (1, 1)
            ]
            self.direction_costs = [
                math.sqrt(2), 1, math.sqrt(2),
                1,               1,
                math.sqrt(2), 1, math.sqrt(2)
            ]
        else:
            self.directions = [(-1, 0), (1, 0), (0, -1), (0, 1)]
            self.direction_costs = [1, 1, 1, 1]
        
        print(f"A*-Pfadfinder: Initialisiert (Gittergröße: {grid_size}m)")
    
    def set_obstacles(self, obstacles: List[Polygon]) -> None:
        """
        Setzt die Hindernisse für die Pfadplanung.
        
        Args:
            obstacles: Liste der Hindernispolygone
        """
        self.obstacles.clear()
        
        for obstacle in obstacles:
            self._add_polygon_to_grid(obstacle, NodeType.OBSTACLE)
        
        print(f"A*-Pfadfinder: {len(obstacles)} Hindernisse gesetzt")
    
    def _add_polygon_to_grid(self, polygon: Polygon, node_type: NodeType) -> None:
        """
        Fügt ein Polygon zum Gitter hinzu.
        """
        if len(polygon.points) < 3:
            return
        
        # Bounding Box des Polygons
        min_x = min(p.x for p in polygon.points)
        max_x = max(p.x for p in polygon.points)
        min_y = min(p.y for p in polygon.points)
        max_y = max(p.y for p in polygon.points)
        
        # Inflation für Hindernisse
        if node_type == NodeType.OBSTACLE:
            min_x -= self.obstacle_inflation
            max_x += self.obstacle_inflation
            min_y -= self.obstacle_inflation
            max_y += self.obstacle_inflation
        
        # Gitterpunkte innerhalb der Bounding Box prüfen
        grid_min_x = int(min_x / self.grid_size)
        grid_max_x = int(max_x / self.grid_size) + 1
        grid_min_y = int(min_y / self.grid_size)
        grid_max_y = int(max_y / self.grid_size) + 1
        
        for gx in range(grid_min_x, grid_max_x):
            for gy in range(grid_min_y, grid_max_y):
                # Weltkoordinaten des Gitterpunkts
                world_x = gx * self.grid_size
                world_y = gy * self.grid_size
                point = Point(world_x, world_y)
                
                # Prüfen ob Punkt im Polygon liegt
                if self._point_in_polygon(point, polygon):
                    if node_type == NodeType.OBSTACLE:
                        self.obstacles.add((gx, gy))
                    
                    # Gittergrenzen aktualisieren
                    self.bounds['min_x'] = min(self.bounds['min_x'], gx)
                    self.bounds['max_x'] = max(self.bounds['max_x'], gx)
                    self.bounds['min_y'] = min(self.bounds['min_y'], gy)
                    self.bounds['max_y'] = max(self.bounds['max_y'], gy)
    
    def _point_in_polygon(self, point: Point, polygon: Polygon) -> bool:
        """
        Prüft ob ein Punkt innerhalb eines Polygons liegt (Ray-Casting).
        """
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
    
    def find_path(self, start: Point, goal: Point, dynamic_obstacles: List[Polygon] = None) -> Optional[List[Point]]:
        """
        Findet den optimalen Pfad vom Start zum Ziel.
        
        Args:
            start: Startpunkt
            goal: Zielpunkt
            dynamic_obstacles: Zusätzliche dynamische Hindernisse
            
        Returns:
            Liste von Wegpunkten oder None wenn kein Pfad gefunden
            
        Beispiel:
            path = pathfinder.find_path(Point(0, 0), Point(10, 10))
            if path:
                for waypoint in path:
                    print(f"Wegpunkt: ({waypoint.x:.2f}, {waypoint.y:.2f})")
        """
        # Dynamische Hindernisse temporär hinzufügen
        temp_obstacles = set()
        if dynamic_obstacles:
            for obstacle in dynamic_obstacles:
                temp_obstacle_points = self._get_polygon_grid_points(obstacle)
                temp_obstacles.update(temp_obstacle_points)
        
        # Start- und Zielknoten in Gitterkoordinaten
        start_grid = self._world_to_grid(start)
        goal_grid = self._world_to_grid(goal)
        
        # Prüfen ob Start oder Ziel in Hindernis liegt
        if start_grid in self.obstacles or start_grid in temp_obstacles:
            print(f"A*-Pfadfinder: Startpunkt liegt in Hindernis")
            return None
        
        if goal_grid in self.obstacles or goal_grid in temp_obstacles:
            print(f"A*-Pfadfinder: Zielpunkt liegt in Hindernis")
            return None
        
        # A*-Algorithmus ausführen
        path_nodes = self._astar_search(start_grid, goal_grid, temp_obstacles)
        
        if not path_nodes:
            print(f"A*-Pfadfinder: Kein Pfad gefunden")
            return None
        
        # Gitterkoordinaten zurück in Weltkoordinaten umwandeln
        world_path = []
        for node in path_nodes:
            world_point = self._grid_to_world(node.x, node.y)
            world_path.append(world_point)
        
        # Pfad glätten
        smoothed_path = self._smooth_path(world_path)
        
        print(f"A*-Pfadfinder: Pfad gefunden mit {len(smoothed_path)} Wegpunkten")
        return smoothed_path
    
    def _get_polygon_grid_points(self, polygon: Polygon) -> Set[Tuple[int, int]]:
        """
        Gibt alle Gitterpunkte zurück, die von einem Polygon abgedeckt werden.
        """
        grid_points = set()
        
        if len(polygon.points) < 3:
            return grid_points
        
        # Bounding Box
        min_x = min(p.x for p in polygon.points) - self.obstacle_inflation
        max_x = max(p.x for p in polygon.points) + self.obstacle_inflation
        min_y = min(p.y for p in polygon.points) - self.obstacle_inflation
        max_y = max(p.y for p in polygon.points) + self.obstacle_inflation
        
        grid_min_x = int(min_x / self.grid_size)
        grid_max_x = int(max_x / self.grid_size) + 1
        grid_min_y = int(min_y / self.grid_size)
        grid_max_y = int(max_y / self.grid_size) + 1
        
        for gx in range(grid_min_x, grid_max_x):
            for gy in range(grid_min_y, grid_max_y):
                world_point = Point(gx * self.grid_size, gy * self.grid_size)
                if self._point_in_polygon(world_point, polygon):
                    grid_points.add((gx, gy))
        
        return grid_points
    
    def _astar_search(self, start: Tuple[int, int], goal: Tuple[int, int], temp_obstacles: Set[Tuple[int, int]]) -> Optional[List[AStarNode]]:
        """
        Führt die A*-Suche aus.
        """
        # Initialisierung
        open_set = []
        closed_set = set()
        
        start_node = AStarNode(start[0], start[1], g_cost=0.0)
        start_node.h_cost = self._heuristic(start, goal)
        start_node.f_cost = start_node.g_cost + start_node.h_cost
        
        heapq.heappush(open_set, start_node)
        
        iterations = 0
        
        while open_set and iterations < self.max_iterations:
            iterations += 1
            
            # Knoten mit niedrigsten f_cost
            current = heapq.heappop(open_set)
            
            # Ziel erreicht?
            if (current.x, current.y) == goal:
                return self._reconstruct_path(current)
            
            closed_set.add((current.x, current.y))
            
            # Nachbarn untersuchen
            for i, (dx, dy) in enumerate(self.directions):
                neighbor_x = current.x + dx
                neighbor_y = current.y + dy
                neighbor_pos = (neighbor_x, neighbor_y)
                
                # Prüfungen
                if neighbor_pos in closed_set:
                    continue
                
                if neighbor_pos in self.obstacles or neighbor_pos in temp_obstacles:
                    continue
                
                # Bewegungskosten
                move_cost = self.direction_costs[i]
                tentative_g = current.g_cost + move_cost
                
                # Nachbar in open_set suchen
                neighbor_in_open = None
                for node in open_set:
                    if node.x == neighbor_x and node.y == neighbor_y:
                        neighbor_in_open = node
                        break
                
                if neighbor_in_open is None:
                    # Neuer Knoten
                    neighbor = AStarNode(neighbor_x, neighbor_y, g_cost=tentative_g)
                    neighbor.h_cost = self._heuristic(neighbor_pos, goal)
                    neighbor.f_cost = neighbor.g_cost + neighbor.h_cost
                    neighbor.parent = current
                    heapq.heappush(open_set, neighbor)
                elif tentative_g < neighbor_in_open.g_cost:
                    # Besserer Pfad gefunden
                    neighbor_in_open.g_cost = tentative_g
                    neighbor_in_open.f_cost = neighbor_in_open.g_cost + neighbor_in_open.h_cost
                    neighbor_in_open.parent = current
                    heapq.heapify(open_set)  # Heap-Eigenschaft wiederherstellen
        
        print(f"A*-Pfadfinder: Maximale Iterationen erreicht ({iterations})")
        return None
    
    def _heuristic(self, pos1: Tuple[int, int], pos2: Tuple[int, int]) -> float:
        """
        Heuristische Funktion (Manhattan oder Euklidische Distanz).
        """
        dx = abs(pos1[0] - pos2[0])
        dy = abs(pos1[1] - pos2[1])
        
        if self.diagonal_movement:
            # Euklidische Distanz für diagonale Bewegung
            return self.heuristic_weight * math.sqrt(dx*dx + dy*dy)
        else:
            # Manhattan-Distanz für 4-Richtungen
            return self.heuristic_weight * (dx + dy)
    
    def _reconstruct_path(self, goal_node: AStarNode) -> List[AStarNode]:
        """
        Rekonstruiert den Pfad vom Ziel zum Start.
        """
        path = []
        current = goal_node
        
        while current is not None:
            path.append(current)
            current = current.parent
        
        path.reverse()
        return path
    
    def _smooth_path(self, path: List[Point]) -> List[Point]:
        """
        Glättet den Pfad durch Entfernung unnötiger Wegpunkte.
        """
        if len(path) <= 2:
            return path
        
        smoothed = [path[0]]  # Startpunkt
        
        i = 0
        while i < len(path) - 1:
            # Versuche direkte Verbindung zu späteren Punkten
            for j in range(len(path) - 1, i + 1, -1):
                if self._line_of_sight(path[i], path[j]):
                    smoothed.append(path[j])
                    i = j
                    break
            else:
                # Kein direkter Weg gefunden, nächsten Punkt nehmen
                i += 1
                if i < len(path):
                    smoothed.append(path[i])
        
        return smoothed
    
    def _line_of_sight(self, start: Point, end: Point) -> bool:
        """
        Prüft ob eine direkte Linie zwischen zwei Punkten frei von Hindernissen ist.
        """
        # Bresenham-ähnlicher Algorithmus für Gitter
        start_grid = self._world_to_grid(start)
        end_grid = self._world_to_grid(end)
        
        dx = abs(end_grid[0] - start_grid[0])
        dy = abs(end_grid[1] - start_grid[1])
        
        x_step = 1 if start_grid[0] < end_grid[0] else -1
        y_step = 1 if start_grid[1] < end_grid[1] else -1
        
        error = dx - dy
        x, y = start_grid
        
        while True:
            if (x, y) in self.obstacles:
                return False
            
            if x == end_grid[0] and y == end_grid[1]:
                break
            
            error2 = 2 * error
            if error2 > -dy:
                error -= dy
                x += x_step
            if error2 < dx:
                error += dx
                y += y_step
        
        return True
    
    def _world_to_grid(self, point: Point) -> Tuple[int, int]:
        """
        Wandelt Weltkoordinaten in Gitterkoordinaten um.
        """
        return (int(point.x / self.grid_size), int(point.y / self.grid_size))
    
    def _grid_to_world(self, gx: int, gy: int) -> Point:
        """
        Wandelt Gitterkoordinaten in Weltkoordinaten um.
        """
        return Point(gx * self.grid_size, gy * self.grid_size)
    
    def get_statistics(self) -> Dict:
        """
        Gibt Statistiken über das Gitter zurück.
        """
        return {
            'grid_size': self.grid_size,
            'obstacle_count': len(self.obstacles),
            'grid_bounds': self.bounds,
            'diagonal_movement': self.diagonal_movement,
            'obstacle_inflation': self.obstacle_inflation
        }
    
    def clear_obstacles(self) -> None:
        """
        Entfernt alle Hindernisse.
        """
        self.obstacles.clear()
        print("A*-Pfadfinder: Alle Hindernisse entfernt")