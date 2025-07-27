import time
import math
from typing import Dict, Tuple, Optional, List
from enum import Enum
from events import Logger, EventCode

class GPSSafetyLevel(Enum):
    RTK_FIXED = "rtk_fixed"
    RTK_FLOAT = "rtk_float" 
    FIX_3D_WAIT = "3d_fix_wait"
    NO_FIX = "no_fix"

class GPSSafetyManager:
    """
    Verwaltet GPS-basierte Sicherheitsmechanismen für den Mähroboter.
    """
    
    def __init__(self, config: Dict, map_module=None):
        self.config = config.get('gps_safety', {})
        self.map_module = map_module
        
        # Schwellenwerte
        self.rtk_fixed_threshold = self.config.get('rtk_fixed_accuracy_threshold', 0.05)
        self.rtk_float_threshold = self.config.get('rtk_float_accuracy_threshold', 0.50)
        self.safe_zone_margin = self.config.get('safe_zone_boundary_margin', 2.0)
        self.critical_zone_margin = self.config.get('critical_zone_boundary_margin', 5.0)
        self.degradation_timeout = self.config.get('gps_degradation_timeout', 3.0)
        self.rtk_wait_timeout = self.config.get('rtk_wait_timeout', 300.0)
        self.reduced_speed_factor = self.config.get('reduced_speed_factor', 0.3)
        
        # Zustandsverfolgung
        self.current_safety_level = GPSSafetyLevel.NO_FIX
        self.last_rtk_fixed_time = 0.0
        self.degradation_start_time = None
        self.rtk_wait_start_time = None
        self.last_safe_position = None
        
        print("GPS-Sicherheitsmanager initialisiert")
    
    def evaluate_gps_safety(self, gps_data: Dict, current_position: Tuple[float, float]) -> Dict:
        """
        Bewertet die aktuelle GPS-Sicherheitssituation.
        
        Returns:
            Dict mit Sicherheitsstatus und empfohlenen Aktionen
        """
        current_time = time.time()
        
        # GPS-Qualität bestimmen
        new_safety_level = self._determine_safety_level(gps_data)
        
        # Positionssicherheit prüfen
        position_safety = self._evaluate_position_safety(current_position)
        
        # Sicherheitslevel-Übergänge verwalten
        safety_action = self._handle_safety_transitions(
            new_safety_level, current_time, position_safety
        )
        
        # Sichere Position aktualisieren
        if new_safety_level == GPSSafetyLevel.RTK_FIXED and position_safety['in_safe_zone']:
            self.last_safe_position = current_position
            self.last_rtk_fixed_time = current_time
        
        return {
            'safety_level': new_safety_level,
            'position_safety': position_safety,
            'recommended_action': safety_action,
            'can_mow': self._can_mow(new_safety_level, position_safety),
            'speed_factor': self._get_speed_factor(new_safety_level, position_safety),
            'last_safe_position': self.last_safe_position,
            'rtk_wait_remaining': self._get_rtk_wait_remaining(current_time)
        }
    
    def _determine_safety_level(self, gps_data: Dict) -> GPSSafetyLevel:
        """Bestimmt GPS-Sicherheitslevel basierend auf Genauigkeit und Fix-Typ."""
        gps_mode = gps_data.get('mode', 0)
        accuracy = gps_data.get('accuracy', 999.0)
        
        if gps_mode < 2:  # Kein 3D-Fix
            return GPSSafetyLevel.NO_FIX
        elif gps_mode >= 4 and accuracy <= self.rtk_fixed_threshold:  # RTK Fixed
            return GPSSafetyLevel.RTK_FIXED
        elif gps_mode >= 4 and accuracy <= self.rtk_float_threshold:  # RTK Float
            return GPSSafetyLevel.RTK_FLOAT
        else:  # 3D Fix oder schlechte RTK-Genauigkeit
            return GPSSafetyLevel.FIX_3D_WAIT
    
    def _evaluate_position_safety(self, position: Tuple[float, float]) -> Dict:
        """Bewertet die Sicherheit der aktuellen Position."""
        if not self.map_module or not position:
            return {
                'in_safe_zone': False,
                'distance_to_boundary': 999.0,
                'in_critical_area': True
            }
        
        x, y = position
        
        # Prüfe Mähzonen
        in_mow_zone = False
        min_distance_to_boundary = 999.0
        
        if hasattr(self.map_module, 'zones') and self.map_module.zones:
            for zone in self.map_module.zones:
                if self._point_in_polygon(x, y, zone.points):
                    in_mow_zone = True
                    # Berechne Abstand zur Zonengrenze
                    distance = self._distance_to_polygon_edge(x, y, zone.points)
                    min_distance_to_boundary = min(min_distance_to_boundary, distance)
        
        # Prüfe Ausschlusszonen
        in_exclusion = False
        if hasattr(self.map_module, 'exclusions') and self.map_module.exclusions:
            for exclusion in self.map_module.exclusions:
                if self._point_in_polygon(x, y, exclusion.points):
                    in_exclusion = True
                    break
        
        # Sicherheitsbewertung
        in_safe_zone = (in_mow_zone and not in_exclusion and 
                       min_distance_to_boundary >= self.safe_zone_margin)
        in_critical_area = (not in_mow_zone or in_exclusion or 
                           min_distance_to_boundary < self.critical_zone_margin)
        
        return {
            'in_safe_zone': in_safe_zone,
            'distance_to_boundary': min_distance_to_boundary,
            'in_critical_area': in_critical_area,
            'in_mow_zone': in_mow_zone,
            'in_exclusion': in_exclusion
        }
    
    def _handle_safety_transitions(self, new_level: GPSSafetyLevel, 
                                 current_time: float, position_safety: Dict) -> str:
        """Verwaltet Übergänge zwischen Sicherheitsstufen."""
        previous_level = self.current_safety_level
        
        # Verschlechterung der GPS-Qualität
        if (previous_level == GPSSafetyLevel.RTK_FIXED and 
            new_level in [GPSSafetyLevel.RTK_FLOAT, GPSSafetyLevel.FIX_3D_WAIT]):
            
            if self.degradation_start_time is None:
                self.degradation_start_time = current_time
                Logger.event(EventCode.GPS_FIX_LOST, f"GPS-Qualität verschlechtert: {new_level.value}")
            
            # Timeout für Verschlechterung prüfen
            if current_time - self.degradation_start_time >= self.degradation_timeout:
                self.current_safety_level = new_level
                self.degradation_start_time = None
                
                if new_level == GPSSafetyLevel.FIX_3D_WAIT:
                    self.rtk_wait_start_time = current_time
                    return "stop_and_wait_rtk"
                elif position_safety['in_critical_area']:
                    return "return_to_safe_zone"
                else:
                    return "reduce_speed"
        
        # Verbesserung der GPS-Qualität
        elif new_level == GPSSafetyLevel.RTK_FIXED and previous_level != GPSSafetyLevel.RTK_FIXED:
            self.current_safety_level = new_level
            self.degradation_start_time = None
            self.rtk_wait_start_time = None
            Logger.event(EventCode.RTK_FIX_ACQUIRED, "RTK Fixed wiederhergestellt")
            return "resume_normal_operation"
        
        # RTK-Warte-Timeout
        elif (self.current_safety_level in [GPSSafetyLevel.FIX_3D_WAIT, GPSSafetyLevel.NO_FIX] and 
              self.rtk_wait_start_time and 
              current_time - self.rtk_wait_start_time >= self.rtk_wait_timeout):
            return "rtk_wait_timeout_error"
        
        # Kein GPS-Fix
        elif new_level == GPSSafetyLevel.NO_FIX:
            self.current_safety_level = new_level
            if self.rtk_wait_start_time is None:
                self.rtk_wait_start_time = current_time
            return "stop_and_wait_rtk"
        
        return "continue"
    
    def _can_mow(self, safety_level: GPSSafetyLevel, position_safety: Dict) -> bool:
        """Bestimmt ob gemäht werden darf."""
        if safety_level == GPSSafetyLevel.RTK_FIXED:
            return position_safety['in_safe_zone']
        elif safety_level == GPSSafetyLevel.RTK_FLOAT:
            return position_safety['in_safe_zone'] and not position_safety['in_critical_area']
        else:
            return False
    
    def _get_speed_factor(self, safety_level: GPSSafetyLevel, position_safety: Dict) -> float:
        """Bestimmt Geschwindigkeitsfaktor basierend auf Sicherheitslevel."""
        if safety_level == GPSSafetyLevel.RTK_FIXED:
            return 1.0
        elif safety_level == GPSSafetyLevel.RTK_FLOAT and not position_safety['in_critical_area']:
            return self.reduced_speed_factor
        else:
            return 0.0
    
    def _get_rtk_wait_remaining(self, current_time: float) -> float:
        """Gibt verbleibende RTK-Wartezeit zurück."""
        if self.rtk_wait_start_time:
            elapsed = current_time - self.rtk_wait_start_time
            remaining = self.rtk_wait_timeout - elapsed
            return max(0.0, remaining)
        return 0.0
    
    def _point_in_polygon(self, x: float, y: float, polygon_points) -> bool:
        """Ray-Casting-Algorithmus für Punkt-in-Polygon-Test."""
        n = len(polygon_points)
        inside = False
        
        p1x, p1y = polygon_points[0].x, polygon_points[0].y
        for i in range(1, n + 1):
            p2x, p2y = polygon_points[i % n].x, polygon_points[i % n].y
            if y > min(p1y, p2y):
                if y <= max(p1y, p2y):
                    if x <= max(p1x, p2x):
                        if p1y != p2y:
                            xinters = (y - p1y) * (p2x - p1x) / (p2y - p1y) + p1x
                        if p1x == p2x or x <= xinters:
                            inside = not inside
            p1x, p1y = p2x, p2y
        
        return inside
    
    def _distance_to_polygon_edge(self, x: float, y: float, polygon_points) -> float:
        """Berechnet minimalen Abstand zu Polygonkante."""
        min_distance = float('inf')
        n = len(polygon_points)
        
        for i in range(n):
            p1 = polygon_points[i]
            p2 = polygon_points[(i + 1) % n]
            
            # Abstand zu Liniensegment berechnen
            distance = self._point_to_line_distance(x, y, p1.x, p1.y, p2.x, p2.y)
            min_distance = min(min_distance, distance)
        
        return min_distance
    
    def _point_to_line_distance(self, px: float, py: float, 
                               x1: float, y1: float, x2: float, y2: float) -> float:
        """Berechnet Abstand von Punkt zu Liniensegment."""
        A = px - x1
        B = py - y1
        C = x2 - x1
        D = y2 - y1
        
        dot = A * C + B * D
        len_sq = C * C + D * D
        
        if len_sq == 0:
            return math.sqrt(A * A + B * B)
        
        param = dot / len_sq
        
        if param < 0:
            xx, yy = x1, y1
        elif param > 1:
            xx, yy = x2, y2
        else:
            xx = x1 + param * C
            yy = y1 + param * D
        
        dx = px - xx
        dy = py - yy
        return math.sqrt(dx * dx + dy * dy)