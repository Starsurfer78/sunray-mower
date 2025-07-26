import json
from typing import List, Optional, Dict

class Point:
    """
    Repräsentiert einen Punkt (Meter).
    """
    def __init__(self, x: float = 0.0, y: float = 0.0):
        self.x = x
        self.y = y

    def init(self) -> None:
        self.x = 0.0
        self.y = 0.0

    def set_xy(self, x: float, y: float) -> None:
        self.x = x
        self.y = y

    def assign(self, other: 'Point') -> None:
        self.x = other.x
        self.y = other.y

    def crc(self) -> int:
        """Einfaches CRC aus Rundungswerten."""
        return hash((round(self.x, 3), round(self.y, 3)))

    def to_dict(self) -> dict:
        return {'x': self.x, 'y': self.y}

    @staticmethod
    def from_dict(data: dict) -> 'Point':
        return Point(data.get('x', 0.0), data.get('y', 0.0))


class Polygon:
    """
    Geschlossener Ring von Punkten.
    """
    def __init__(self, points: Optional[List[Point]] = None):
        self.points: List[Point] = points if points else []

    def init(self) -> None:
        self.points = []

    def alloc(self, count: int) -> None:
        self.points = [Point() for _ in range(count)]

    def dealloc(self) -> None:
        self.points = []

    def dump(self) -> None:
        print([p.to_dict() for p in self.points])

    def crc(self) -> int:
        return hash(tuple(p.crc() for p in self.points))

    def get_center(self) -> Point:
        if not self.points:
            return Point()
        xs = [p.x for p in self.points]
        ys = [p.y for p in self.points]
        return Point(sum(xs) / len(xs), sum(ys) / len(ys))

    def to_list(self) -> List[dict]:
        return [p.to_dict() for p in self.points]

    @staticmethod
    def from_list(data: List[dict]) -> 'Polygon':
        poly = Polygon()
        poly.points = [Point.from_dict(d) for d in data]
        return poly


class PolygonList:
    """
    Liste von Polygon-Objekten.
    """
    def __init__(self, polygons: Optional[List[Polygon]] = None):
        self.polygons: List[Polygon] = polygons if polygons else []

    def init(self) -> None:
        self.polygons = []

    def alloc(self, count: int) -> None:
        self.polygons = [Polygon() for _ in range(count)]

    def dealloc(self) -> None:
        self.polygons = []

    def dump(self) -> None:
        for poly in self.polygons:
            poly.dump()

    def crc(self) -> int:
        return hash(tuple(poly.crc() for poly in self.polygons))

    def to_list(self) -> List[List[dict]]:
        return [poly.to_list() for poly in self.polygons]

    @staticmethod
    def from_list(data: List[List[dict]]) -> 'PolygonList':
        pl = PolygonList()
        pl.polygons = [Polygon.from_list(lst) for lst in data]
        return pl


class Map:
    """
    Kartierung und Pathfinding inklusive zonenbasierter Navigation.
    """
    def __init__(self):
        self.points = Polygon()
        self.perimeter = Polygon()
        self.exclusions = PolygonList()
        self.obstacles = PolygonList()
        self.free_points = Polygon()
        self.way_mode = None  # e.g. 'mow', 'dock', 'free'
        self.mow_zones: List[Polygon] = []

    def begin(self) -> None:
        """Initialisierung der Karte."""
        self.points.init()
        self.perimeter.init()
        self.exclusions.init()
        self.obstacles.init()
        self.free_points.init()

    def clear(self) -> None:
        """Löscht alle Punkte und Listen."""
        self.begin()

    def set_point(self, idx: int, x: float, y: float) -> bool:
        try:
            self.points.points[idx].set_xy(x, y)
            return True
        except IndexError:
            return False

    def save(self, filename: str) -> bool:
        """Speichert Karte als JSON."""
        data = {
            'points': self.points.to_list(),
            'perimeter': self.perimeter.to_list(),
            'exclusions': self.exclusions.to_list(),
            'obstacles': self.obstacles.to_list(),
            'free_points': self.free_points.to_list(),
        }
        try:
            with open(filename, 'w') as f:
                json.dump(data, f)
            return True
        except Exception:
            return False

    def load(self, filename: str) -> bool:
        """Lädt Karte aus JSON."""
        try:
            with open(filename, 'r') as f:
                data = json.load(f)
            self.points = Polygon.from_list(data.get('points', []))
            self.perimeter = Polygon.from_list(data.get('perimeter', []))
            self.exclusions = PolygonList.from_list(data.get('exclusions', []))
            self.obstacles = PolygonList.from_list(data.get('obstacles', []))
            self.free_points = Polygon.from_list(data.get('free_points', []))
            return True
        except Exception:
            return False

    # Platzhalter für Pathfinding-Methoden
    def find_path(self, src: Point, dst: Point) -> List[Point]:
        """Ermittelt Weg von src nach dst."""
        raise NotImplementedError

    def next_mow_point(self) -> Optional[Point]:
        """Gibt nächsten Mähpunkt zurück (erstes Zonen-Zentrum)."""
        if not self.mow_zones:
            return None
        zone = self.mow_zones.pop(0)
        return zone.get_center()

    def load_zones(self, filename: str) -> bool:
        """Lädt Mähzonen aus JSON-Datei."""
        try:
            with open(filename, 'r') as f:
                data = json.load(f)
            self.mow_zones = [Polygon.from_list(zone) for zone in data.get('mow_zones', [])]
            return True
        except Exception:
            return False

    def save_zones(self, filename: str) -> bool:
        """Speichert Mähzonen in JSON-Datei."""
        try:
            with open(filename, 'w') as f:
                json.dump({'mow_zones': [poly.to_list() for poly in self.mow_zones]}, f)
            return True
        except Exception:
            return False
