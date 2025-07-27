#!/usr/bin/env python3
"""
GPS-Navigation für Sunray Mähroboter.

Integriert RTK-GPS-Daten in die Pfadplanung und Navigation:
- Hochpräzise GPS-basierte Positionierung
- Koordinatentransformation (WGS84 zu lokalen Koordinaten)
- RTK-GPS Integration in Pfadplanung
- Waypoint-Navigation mit cm-Genauigkeit
- GPS-basierte Zonenerkennung

Autor: Sunray Python Team
Version: 1.0
"""

import math
import time
from typing import Dict, List, Optional, Tuple, Callable
from dataclasses import dataclass
from enum import Enum

from rtk_gps import RTKGPS
from path_planner import PathPlanner, MowPattern
from map import Point, Polygon
from config import get_config

class NavigationMode(Enum):
    """Verfügbare Navigationsmodi."""
    MANUAL = "manual"              # Manuelle Steuerung
    WAYPOINT = "waypoint"          # Einzelner Wegpunkt
    ZONE_MOWING = "zone_mowing"    # Zonenmähen
    PERIMETER = "perimeter"        # Umrandung fahren
    RETURN_HOME = "return_home"    # Zur Ladestation

@dataclass
class GPSWaypoint:
    """GPS-Wegpunkt mit Metadaten."""
    latitude: float
    longitude: float
    local_x: float
    local_y: float
    tolerance: float = 0.1  # Meter
    zone_id: Optional[str] = None
    waypoint_type: str = "mow"  # mow, transit, dock
    timestamp: float = 0.0

class GPSNavigation:
    """
    GPS-basierte Navigation für Sunray Mähroboter.
    
    Diese Klasse verbindet RTK-GPS-Daten mit der Pfadplanung:
    - Hochpräzise Positionierung durch RTK-GPS
    - Automatische Koordinatentransformation
    - Integration in bestehende Pfadplanung
    - Waypoint-Navigation mit cm-Genauigkeit
    - GPS-basierte Zonenerkennung und -überwachung
    
    Beispiel:
        gps_nav = GPSNavigation(rtk_gps, path_planner)
        gps_nav.set_reference_point(52.1234, 8.5678)  # Referenzpunkt setzen
        gps_nav.start_zone_mowing(zones)  # Autonomes Mähen starten
    """
    
    def __init__(self, rtk_gps: RTKGPS, path_planner: PathPlanner):
        """
        Initialisiert die GPS-Navigation.
        
        Args:
            rtk_gps: RTK-GPS-Instanz für hochpräzise Positionierung
            path_planner: Pfadplaner für Mähmuster
        """
        self.rtk_gps = rtk_gps
        self.path_planner = path_planner
        self.config = get_config()
        
        # Referenzpunkt für lokale Koordinaten
        self.reference_lat = None
        self.reference_lon = None
        self.reference_set = False
        
        # Navigation Status
        self.navigation_mode = NavigationMode.MANUAL
        self.current_waypoint = None
        self.waypoint_queue = []
        self.navigation_active = False
        
        # Position und Status
        self.current_position = Point(0.0, 0.0)
        self.current_gps_position = (0.0, 0.0)  # (lat, lon)
        self.position_accuracy = 0.0
        self.rtk_status = "No Fix"
        
        # Zonen
        self.mow_zones = []
        self.exclusion_zones = []
        
        # Navigation Parameter
        nav_config = self.config.get('gps_navigation', {})
        self.waypoint_tolerance = nav_config.get('waypoint_tolerance', 0.15)  # Meter
        self.rtk_required_accuracy = nav_config.get('rtk_required_accuracy', 0.05)  # 5cm
        self.max_position_age = nav_config.get('max_position_age', 2.0)  # Sekunden
        self.zone_boundary_tolerance = nav_config.get('zone_boundary_tolerance', 0.5)  # Meter
        
        # Callbacks
        self.position_callback = None
        self.waypoint_reached_callback = None
        self.zone_completed_callback = None
        
        # Statistiken
        self.total_distance = 0.0
        self.mowing_time = 0.0
        self.start_time = 0.0
        
        print("GPS-Navigation: Initialisiert")
    
    def set_reference_point(self, latitude: float, longitude: float) -> bool:
        """
        Setzt den Referenzpunkt für lokale Koordinatentransformation.
        
        Args:
            latitude: Referenz-Breitengrad
            longitude: Referenz-Längengrad
            
        Returns:
            bool: True wenn erfolgreich gesetzt
            
        Beispiel:
            # Ladestation als Referenzpunkt
            gps_nav.set_reference_point(52.1234, 8.5678)
        """
        self.reference_lat = latitude
        self.reference_lon = longitude
        self.reference_set = True
        
        print(f"GPS-Navigation: Referenzpunkt gesetzt ({latitude:.6f}, {longitude:.6f})")
        return True
    
    def update(self) -> Dict:
        """
        Aktualisiert GPS-Navigation mit aktuellen RTK-GPS-Daten.
        
        Returns:
            Dict: Aktueller Navigationsstatus
            
        Sollte regelmäßig in der Hauptschleife aufgerufen werden.
        """
        # RTK-GPS-Daten lesen
        gps_data = self.rtk_gps.read()
        if not gps_data:
            return self._get_status()
        
        # Position und Status aktualisieren
        self._update_position(gps_data)
        self._update_rtk_status(gps_data)
        
        # Navigation ausführen wenn aktiv
        if self.navigation_active:
            self._run_navigation()
        
        # Callbacks ausführen
        if self.position_callback:
            self.position_callback(self.current_position, gps_data)
        
        return self._get_status()
    
    def _update_position(self, gps_data: Dict) -> None:
        """
        Aktualisiert die aktuelle Position aus GPS-Daten.
        """
        if not gps_data.get('latitude') or not gps_data.get('longitude'):
            return
        
        lat = gps_data['latitude']
        lon = gps_data['longitude']
        self.current_gps_position = (lat, lon)
        self.position_accuracy = gps_data.get('accuracy', 999.0)
        
        # In lokale Koordinaten umwandeln
        if self.reference_set:
            local_x, local_y = self._gps_to_local(lat, lon)
            self.current_position = Point(local_x, local_y)
        
    def _update_rtk_status(self, gps_data: Dict) -> None:
        """
        Aktualisiert den RTK-Status.
        """
        self.rtk_status = gps_data.get('fix_type', 'No Fix')
        
        # RTK-Qualität prüfen
        rtk_data = self.rtk_gps.get_rtk_status()
        if rtk_data:
            self.position_accuracy = rtk_data.get('accuracy', self.position_accuracy)
    
    def _gps_to_local(self, latitude: float, longitude: float) -> Tuple[float, float]:
        """
        Wandelt GPS-Koordinaten in lokale Koordinaten um.
        
        Args:
            latitude: Breitengrad
            longitude: Längengrad
            
        Returns:
            Tuple[float, float]: (x, y) in Metern vom Referenzpunkt
        """
        if not self.reference_set:
            return (0.0, 0.0)
        
        # Vereinfachte Umrechnung für kleine Entfernungen
        # Für größere Gebiete sollte UTM-Projektion verwendet werden
        
        # Entfernung in Grad
        dlat = latitude - self.reference_lat
        dlon = longitude - self.reference_lon
        
        # Umrechnung in Meter (approximativ)
        lat_rad = math.radians(self.reference_lat)
        meters_per_deg_lat = 111132.92 - 559.82 * math.cos(2 * lat_rad) + 1.175 * math.cos(4 * lat_rad)
        meters_per_deg_lon = 111412.84 * math.cos(lat_rad) - 93.5 * math.cos(3 * lat_rad)
        
        x = dlon * meters_per_deg_lon
        y = dlat * meters_per_deg_lat
        
        return (x, y)
    
    def _local_to_gps(self, x: float, y: float) -> Tuple[float, float]:
        """
        Wandelt lokale Koordinaten in GPS-Koordinaten um.
        
        Args:
            x: X-Koordinate in Metern
            y: Y-Koordinate in Metern
            
        Returns:
            Tuple[float, float]: (latitude, longitude)
        """
        if not self.reference_set:
            return (0.0, 0.0)
        
        # Umkehrung der _gps_to_local Berechnung
        lat_rad = math.radians(self.reference_lat)
        meters_per_deg_lat = 111132.92 - 559.82 * math.cos(2 * lat_rad) + 1.175 * math.cos(4 * lat_rad)
        meters_per_deg_lon = 111412.84 * math.cos(lat_rad) - 93.5 * math.cos(3 * lat_rad)
        
        dlat = y / meters_per_deg_lat
        dlon = x / meters_per_deg_lon
        
        latitude = self.reference_lat + dlat
        longitude = self.reference_lon + dlon
        
        return (latitude, longitude)
    
    def start_zone_mowing(self, zones: List[Polygon], pattern: MowPattern = MowPattern.LINES) -> bool:
        """
        Startet das autonome Zonenmähen mit GPS-Navigation.
        
        Args:
            zones: Liste der zu mähenden Zonen
            pattern: Mähmuster
            
        Returns:
            bool: True wenn erfolgreich gestartet
        """
        if not self.reference_set:
            print("GPS-Navigation: Kein Referenzpunkt gesetzt")
            return False
        
        if not self._check_rtk_quality():
            print("GPS-Navigation: RTK-Qualität unzureichend")
            return False
        
        # Pfadplaner konfigurieren
        self.path_planner.set_pattern(pattern)
        
        # Wegpunkte für alle Zonen generieren
        self.waypoint_queue = []
        for zone in zones:
            zone_waypoints = self._generate_zone_waypoints(zone)
            self.waypoint_queue.extend(zone_waypoints)
        
        if not self.waypoint_queue:
            print("GPS-Navigation: Keine Wegpunkte generiert")
            return False
        
        # Navigation starten
        self.navigation_mode = NavigationMode.ZONE_MOWING
        self.navigation_active = True
        self.current_waypoint = None
        self.start_time = time.time()
        
        print(f"GPS-Navigation: Zonenmähen gestartet - {len(self.waypoint_queue)} Wegpunkte")
        return True
    
    def _generate_zone_waypoints(self, zone: Polygon) -> List[GPSWaypoint]:
        """
        Generiert GPS-Wegpunkte für eine Zone.
        """
        # Pfad von Pfadplaner generieren
        path_points = self.path_planner.generate_zone_path(zone)
        
        waypoints = []
        for point in path_points:
            # Lokale Koordinaten in GPS umwandeln
            lat, lon = self._local_to_gps(point.x, point.y)
            
            waypoint = GPSWaypoint(
                latitude=lat,
                longitude=lon,
                local_x=point.x,
                local_y=point.y,
                tolerance=self.waypoint_tolerance,
                waypoint_type="mow",
                timestamp=time.time()
            )
            waypoints.append(waypoint)
        
        return waypoints
    
    def _run_navigation(self) -> None:
        """
        Führt die aktive Navigation aus.
        """
        # Aktuellen Wegpunkt prüfen
        if self.current_waypoint:
            if self._is_waypoint_reached(self.current_waypoint):
                print(f"GPS-Navigation: Wegpunkt erreicht ({self.current_waypoint.local_x:.2f}, {self.current_waypoint.local_y:.2f})")
                
                if self.waypoint_reached_callback:
                    self.waypoint_reached_callback(self.current_waypoint)
                
                self.current_waypoint = None
        
        # Nächsten Wegpunkt holen
        if not self.current_waypoint and self.waypoint_queue:
            self.current_waypoint = self.waypoint_queue.pop(0)
            print(f"GPS-Navigation: Neuer Wegpunkt ({self.current_waypoint.local_x:.2f}, {self.current_waypoint.local_y:.2f})")
        
        # Prüfen ob alle Wegpunkte abgearbeitet
        if not self.current_waypoint and not self.waypoint_queue:
            self._complete_navigation()
    
    def _is_waypoint_reached(self, waypoint: GPSWaypoint) -> bool:
        """
        Prüft ob ein Wegpunkt erreicht wurde.
        """
        if not self.reference_set:
            return False
        
        # Entfernung zum Wegpunkt berechnen
        dx = self.current_position.x - waypoint.local_x
        dy = self.current_position.y - waypoint.local_y
        distance = math.sqrt(dx*dx + dy*dy)
        
        return distance <= waypoint.tolerance
    
    def _complete_navigation(self) -> None:
        """
        Schließt die Navigation ab.
        """
        self.navigation_active = False
        self.navigation_mode = NavigationMode.MANUAL
        self.mowing_time = time.time() - self.start_time
        
        print(f"GPS-Navigation: Navigation abgeschlossen - Zeit: {self.mowing_time:.1f}s")
        
        if self.zone_completed_callback:
            self.zone_completed_callback({
                'mowing_time': self.mowing_time,
                'total_distance': self.total_distance
            })
    
    def _check_rtk_quality(self) -> bool:
        """
        Prüft die RTK-GPS-Qualität für Navigation.
        """
        rtk_status = self.rtk_gps.get_rtk_status()
        if not rtk_status:
            return False
        
        # RTK Fixed oder Float erforderlich
        status = rtk_status.get('status', 'No Fix')
        accuracy = rtk_status.get('accuracy', 999.0)
        
        if status in ['RTK Fixed', 'RTK Float'] and accuracy <= self.rtk_required_accuracy:
            return True
        
        return False
    
    def get_current_waypoint(self) -> Optional[GPSWaypoint]:
        """
        Gibt den aktuellen Ziel-Wegpunkt zurück.
        """
        return self.current_waypoint
    
    def get_navigation_target(self) -> Optional[Tuple[float, float]]:
        """
        Gibt das aktuelle Navigationsziel in lokalen Koordinaten zurück.
        
        Returns:
            Optional[Tuple[float, float]]: (x, y) oder None
        """
        if self.current_waypoint:
            return (self.current_waypoint.local_x, self.current_waypoint.local_y)
        return None
    
    def stop_navigation(self) -> None:
        """
        Stoppt die aktive Navigation.
        """
        self.navigation_active = False
        self.navigation_mode = NavigationMode.MANUAL
        self.current_waypoint = None
        self.waypoint_queue.clear()
        
        print("GPS-Navigation: Navigation gestoppt")
    
    def _get_status(self) -> Dict:
        """
        Gibt den aktuellen Navigationsstatus zurück.
        """
        return {
            'navigation_active': self.navigation_active,
            'navigation_mode': self.navigation_mode.value,
            'current_position': {
                'local': (self.current_position.x, self.current_position.y),
                'gps': self.current_gps_position
            },
            'current_waypoint': {
                'local': (self.current_waypoint.local_x, self.current_waypoint.local_y) if self.current_waypoint else None,
                'gps': (self.current_waypoint.latitude, self.current_waypoint.longitude) if self.current_waypoint else None
            },
            'waypoints_remaining': len(self.waypoint_queue),
            'rtk_status': self.rtk_status,
            'position_accuracy': self.position_accuracy,
            'reference_set': self.reference_set,
            'rtk_quality_ok': self._check_rtk_quality(),
            'total_distance': self.total_distance,
            'mowing_time': time.time() - self.start_time if self.navigation_active else self.mowing_time
        }
    
    def set_position_callback(self, callback: Callable) -> None:
        """
        Setzt Callback für Positionsupdates.
        
        Args:
            callback: Funktion(position: Point, gps_data: Dict)
        """
        self.position_callback = callback
    
    def set_waypoint_reached_callback(self, callback: Callable) -> None:
        """
        Setzt Callback für erreichte Wegpunkte.
        
        Args:
            callback: Funktion(waypoint: GPSWaypoint)
        """
        self.waypoint_reached_callback = callback
    
    def set_zone_completed_callback(self, callback: Callable) -> None:
        """
        Setzt Callback für abgeschlossene Zonen.
        
        Args:
            callback: Funktion(stats: Dict)
        """
        self.zone_completed_callback = callback
    
    def set_mow_zones(self, zones: List[Polygon]) -> None:
        """
        Setzt die Mähzonen für die GPS-Navigation.
        
        Args:
            zones: Liste der Mähzonen
        """
        self.mow_zones = zones
        print(f"GPS-Navigation: {len(zones)} Mähzonen gesetzt")
    
    def set_exclusion_zones(self, exclusions: List[Polygon]) -> None:
        """
        Setzt die Ausschlusszonen für die GPS-Navigation.
        
        Args:
            exclusions: Liste der Ausschlusszonen
        """
        self.exclusion_zones = exclusions
        print(f"GPS-Navigation: {len(exclusions)} Ausschlusszonen gesetzt")