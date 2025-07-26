import time
from abc import ABC, abstractmethod
from typing import Any, Dict, Optional

class Operation(ABC):
    """
    Basisklasse für Roboter-Operationen (src/op).
    Jede Operation implementiert einen Lebenszyklus: start(), run(), stop().
    """
    def __init__(self, name: str):
        self.name = name
        self.active = False

    def start(self, params: Optional[Dict[str, Any]] = None) -> None:
        """Beginnt die Operation mit optionalen Parametern."""
        self.active = True
        self.on_start(params or {})

    @abstractmethod
    def on_start(self, params: Dict[str, Any]) -> None:
        """Einmalig beim Start ausgeführt."""
        pass

    @abstractmethod
    def run(self) -> None:
        """Wird im Hauptloop wiederholt aufgerufen."""
        pass

    def stop(self) -> None:
        """Beendet die Operation."""
        self.active = False
        self.on_stop()

    @abstractmethod
    def on_stop(self) -> None:
        """Aufräumarbeiten beim Beenden."""
        pass

# Beispiele für konkrete Operationen
class MowOp(Operation):
    def __init__(self, name: str, motor=None):
        super().__init__(name)
        self.motor = motor
        self.autonomous_started = False
    
    def on_start(self, params: Dict[str, Any]) -> None:
        # Initialisierung Mähvorgang
        print("MowOp: Starte Mähvorgang")
        if self.motor:
            # Mähmotor einschalten
            self.motor.set_mow_state(True)
            # Autonomes Mähen starten falls noch nicht aktiv
            if not self.motor.is_autonomous_navigation_active():
                self.motor.start_autonomous_mowing()
                self.autonomous_started = True
                print("MowOp: Autonome Navigation gestartet")

    def run(self) -> None:
        # Logik Mähstrategie - wird hauptsächlich von der Motor-Klasse übernommen
        if self.motor and self.motor.is_autonomous_navigation_active():
            # Navigation läuft, prüfe Status
            nav_status = self.motor.get_navigation_status()
            if nav_status.get('completed', False):
                print("MowOp: Mähvorgang abgeschlossen")
                self.active = False
        else:
            # Fallback: Einfache Mählogik ohne Navigation
            pass

    def on_stop(self) -> None:
        # Aufräumen
        print("MowOp: Beende Mähvorgang")
        if self.motor:
            if self.autonomous_started:
                self.motor.stop_autonomous_mowing()
                print("MowOp: Autonome Navigation gestoppt")
            self.motor.set_mow_state(False)
            self.motor.stop_immediately()

class DockOp(Operation):
    def on_start(self, params: Dict[str, Any]) -> None:
        pass

    def run(self) -> None:
        pass

    def on_stop(self) -> None:
        pass

# Weitere Operationen

class IdleOp(Operation):
    def on_start(self, params: Dict[str, Any]) -> None:
        pass
    def run(self) -> None:
        pass
    def on_stop(self) -> None:
        pass

class EscapeForwardOp(Operation):
    """
    Operation zum Umfahren eines Hindernisses durch Vorwärtsfahren und Drehen.
    Wird aktiviert, wenn ein Hindernis erkannt wurde.
    Verwendet die Motor-Klasse für präzise Steuerung.
    """
    def __init__(self, name: str, motor=None):
        super().__init__(name)
        self.motor = motor
    
    def on_start(self, params: Dict[str, Any]) -> None:
        # Initialisierung
        self.start_time = time.time()
        self.phase = "pause"  # Phasen: pause -> forward -> rotate -> complete
        self.phase_start_time = self.start_time
        self.phase_duration = 0.5  # Anfangspause in Sekunden
        self.forward_duration = 1.5  # Vorwärtsfahrt in Sekunden
        self.rotate_duration = 2.0  # Drehung in Sekunden
        self.rotate_direction = 1  # 1 = rechts, -1 = links
        
        # Zufällige Richtung wählen (basierend auf Millisekunden)
        if int(self.start_time * 1000) % 2 == 0:
            self.rotate_direction = -1
        
        # Motoren über Motor-Klasse stoppen
        if self.motor:
            self.motor.stop_immediately(include_mower=False)
        else:
            # Fallback: Direktes Hardware-Manager-Kommando
            from hardware_manager import get_hardware_manager
            self.hw_manager = get_hardware_manager()
            self.hw_manager.send_motor_command(0, 0, 0)
    
    def run(self) -> None:
        # Aktuelle Zeit und Phase prüfen
        current_time = time.time()
        elapsed_in_phase = current_time - self.phase_start_time
        
        # Phasenübergänge
        if self.phase == "pause" and elapsed_in_phase >= self.phase_duration:
            # Pause beendet, vorwärts fahren
            self.phase = "forward"
            self.phase_start_time = current_time
            if self.motor:
                self.motor.set_linear_angular_speed(0.3, 0.0)  # 0.3 m/s vorwärts
            else:
                self.hw_manager.send_motor_command(100, 100, 0)  # Fallback
        
        elif self.phase == "forward" and elapsed_in_phase >= self.forward_duration:
            # Vorwärtsfahrt beendet, drehen
            self.phase = "rotate"
            self.phase_start_time = current_time
            if self.motor:
                # Drehen mit 0.5 rad/s (links oder rechts)
                angular_speed = 0.5 * self.rotate_direction
                self.motor.set_linear_angular_speed(0.0, angular_speed)
            else:
                # Fallback: Direkte PWM-Werte
                left_speed = -100 if self.rotate_direction > 0 else 100
                right_speed = 100 if self.rotate_direction > 0 else -100
                self.hw_manager.send_motor_command(left_speed, right_speed, 0)
        
        elif self.phase == "rotate" and elapsed_in_phase >= self.rotate_duration:
            # Drehung beendet, Operation abschließen
            self.phase = "complete"
            if self.motor:
                self.motor.stop_immediately(include_mower=False)
            else:
                self.hw_manager.send_motor_command(0, 0, 0)  # Fallback
            
            # Zurück zum Mähen wechseln
            from events import Logger, EventCode
            Logger.event(EventCode.OBSTACLE_DETECTED, "Escape maneuver completed")
            
            # Operation beenden (wird in der Hauptschleife auf MowOp zurückgesetzt)
            self.active = False
    
    def on_stop(self) -> None:
        # Aufräumen: Motoren stoppen
        if self.motor:
            self.motor.stop_immediately(include_mower=False)
        elif hasattr(self, 'hw_manager'):
            self.hw_manager.send_motor_command(0, 0, 0)


class SmartBumperEscapeOp(Operation):
    """
    Intelligente Bumper-Ausweichoperation mit richtungsabhängiger Reaktion.
    Berücksichtigt Hindernisse und Grenzen bei der Ausweichstrategie.
    """
    def __init__(self, name: str, motor=None):
        super().__init__(name)
        self.motor = motor
        self.map_module = None
        
    def on_start(self, params: Dict[str, Any]) -> None:
        # Initialisierung
        self.start_time = time.time()
        self.phase = "stop"  # Phasen: stop -> reverse -> curve -> return -> complete
        self.phase_start_time = self.start_time
        
        # Phasendauern
        self.stop_duration = 0.3  # Kurzer Stopp
        self.reverse_duration = 1.0  # Rückwärtsfahrt
        self.curve_duration = 3.0  # Kurvenfahrt
        self.return_duration = 2.0  # Rückkehr zur ursprünglichen Bahn
        
        # Bumper-Informationen aus params extrahieren
        self.left_bumper_active = params.get('left_bumper', False)
        self.right_bumper_active = params.get('right_bumper', False)
        
        # Ausweichrichtung bestimmen
        if self.right_bumper_active and not self.left_bumper_active:
            # Rechter Bumper: Hindernis rechts -> nach links ausweichen
            self.escape_direction = -1  # Links
            print("SmartBumperEscape: Rechter Bumper ausgelöst - Ausweichen nach links")
        elif self.left_bumper_active and not self.right_bumper_active:
            # Linker Bumper: Hindernis links -> nach rechts ausweichen
            self.escape_direction = 1  # Rechts
            print("SmartBumperEscape: Linker Bumper ausgelöst - Ausweichen nach rechts")
        else:
            # Beide oder unklare Situation: Zufällige Richtung
            self.escape_direction = 1 if int(self.start_time * 1000) % 2 == 0 else -1
            print("SmartBumperEscape: Beide/unklare Bumper - Zufällige Ausweichrichtung")
        
        # Aktuelle Position und Orientierung speichern
        self.start_position = params.get('robot_position', {'x': 0, 'y': 0, 'heading': 0})
        self.original_heading = self.start_position.get('heading', 0)
        
        # Map-Modul für Hinderniss- und Grenzprüfung laden
        try:
            from map import Map
            self.map_module = Map()
            self.map_module.load_zones('zones.json')
        except Exception as e:
            print(f"SmartBumperEscape: Warnung - Map-Modul nicht verfügbar: {e}")
        
        # Nur Antriebsmotoren stoppen, Mähmotor läuft weiter
        if self.motor:
            # Aktuellen Mähmotor-Status speichern
            self.saved_mow_pwm = getattr(self.motor, 'target_mow_speed', 100)
            self.motor.stop_immediately(include_mower=False)
        else:
            from hardware_manager import get_hardware_manager
            self.hw_manager = get_hardware_manager()
            # Standard-Mähmotor-PWM verwenden
            self.saved_mow_pwm = 100
            self.hw_manager.send_motor_command(0, 0, self.saved_mow_pwm)
    
    def _is_safe_position(self, x: float, y: float) -> bool:
        """
        Prüft, ob eine Position sicher ist (innerhalb der Grenzen und ohne Hindernisse).
        """
        if not self.map_module:
            return True  # Wenn keine Karte verfügbar, als sicher annehmen
        
        # Prüfe Mähzonen (muss innerhalb einer Zone sein)
        in_mow_zone = False
        if self.map_module.zones:
            for zone in self.map_module.zones:
                if self._point_in_polygon(x, y, zone.points):
                    in_mow_zone = True
                    break
        
        # Prüfe Ausschlusszonen (darf nicht in Ausschlusszone sein)
        in_exclusion = False
        if self.map_module.exclusions:
            for exclusion in self.map_module.exclusions:
                if self._point_in_polygon(x, y, exclusion.points):
                    in_exclusion = True
                    break
        
        return in_mow_zone and not in_exclusion
    
    def _point_in_polygon(self, x: float, y: float, polygon_points) -> bool:
        """
        Prüft, ob ein Punkt innerhalb eines Polygons liegt (Ray-Casting-Algorithmus).
        """
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
    
    def run(self) -> None:
        current_time = time.time()
        elapsed_in_phase = current_time - self.phase_start_time
        
        if self.phase == "stop" and elapsed_in_phase >= self.stop_duration:
            # Stopp beendet, rückwärts fahren
            self.phase = "reverse"
            self.phase_start_time = current_time
            if self.motor:
                self.motor.set_linear_angular_speed(-0.2, 0.0)  # 0.2 m/s rückwärts
            else:
                self.hw_manager.send_motor_command(-80, -80, 0)
            print("SmartBumperEscape: Phase Rückwärtsfahrt")
        
        elif self.phase == "reverse" and elapsed_in_phase >= self.reverse_duration:
            # Rückwärtsfahrt beendet, Kurve fahren
            self.phase = "curve"
            self.phase_start_time = current_time
            if self.motor:
                # Leichte Kurve: 0.3 m/s vorwärts + 0.3 rad/s Drehung
                linear_speed = 0.3
                angular_speed = 0.3 * self.escape_direction
                self.motor.set_linear_angular_speed(linear_speed, angular_speed)
            else:
                # Fallback: Asymmetrische Motorgeschwindigkeiten für Kurve
                if self.escape_direction > 0:  # Rechts
                    self.hw_manager.send_motor_command(60, 100, 0)
                else:  # Links
                    self.hw_manager.send_motor_command(100, 60, 0)
            print(f"SmartBumperEscape: Phase Kurvenfahrt ({'rechts' if self.escape_direction > 0 else 'links'})")
        
        elif self.phase == "curve" and elapsed_in_phase >= self.curve_duration:
            # Kurve beendet, zur ursprünglichen Bahn zurückkehren
            self.phase = "return"
            self.phase_start_time = current_time
            if self.motor:
                # Gegenrichtung einschlagen um zur ursprünglichen Bahn zurückzukehren
                linear_speed = 0.25
                angular_speed = -0.2 * self.escape_direction  # Gegenrichtung
                self.motor.set_linear_angular_speed(linear_speed, angular_speed)
            else:
                # Fallback: Gegenrichtung
                if self.escape_direction > 0:  # War rechts, jetzt links
                    self.hw_manager.send_motor_command(100, 70, 0)
                else:  # War links, jetzt rechts
                    self.hw_manager.send_motor_command(70, 100, 0)
            print("SmartBumperEscape: Phase Rückkehr zur ursprünglichen Bahn")
        
        elif self.phase == "return" and elapsed_in_phase >= self.return_duration:
            # Rückkehr beendet, Operation abschließen
            self.phase = "complete"
            if self.motor:
                self.motor.stop_immediately(include_mower=False)
            else:
                # Gespeicherten Mähmotor-PWM verwenden
                mow_pwm = getattr(self, 'saved_mow_pwm', 100)
                self.hw_manager.send_motor_command(0, 0, mow_pwm)
            
            from events import Logger, EventCode
            Logger.event(EventCode.OBSTACLE_DETECTED, "Smart bumper escape maneuver completed")
            print("SmartBumperEscape: Ausweichmanöver abgeschlossen")
            
            # Operation beenden
            self.active = False
    
    def on_stop(self) -> None:
        # Aufräumen: Nur Antriebsmotoren stoppen, Mähmotor läuft weiter
        if self.motor:
            self.motor.stop_immediately(include_mower=False)
        elif hasattr(self, 'hw_manager'):
            # Gespeicherten Mähmotor-PWM verwenden
            mow_pwm = getattr(self, 'saved_mow_pwm', 100)
            self.hw_manager.send_motor_command(0, 0, mow_pwm)
        print("SmartBumperEscape: Operation gestoppt")

class EscapeLawnOp(Operation):
    def on_start(self, params: Dict[str, Any]) -> None:
        pass
    def run(self) -> None:
        pass
    def on_stop(self) -> None:
        pass

class EscapeReverseOp(Operation):
    def on_start(self, params: Dict[str, Any]) -> None:
        pass
    def run(self) -> None:
        pass
    def on_stop(self) -> None:
        pass

class EscapeRotationOp(Operation):
    def on_start(self, params: Dict[str, Any]) -> None:
        pass
    def run(self) -> None:
        pass
    def on_stop(self) -> None:
        pass

class GpsRebootRecoveryOp(Operation):
    def on_start(self, params: Dict[str, Any]) -> None:
        pass
    def run(self) -> None:
        pass
    def on_stop(self) -> None:
        pass

class GpsWaitFixOp(Operation):
    def on_start(self, params: Dict[str, Any]) -> None:
        pass
    def run(self) -> None:
        pass
    def on_stop(self) -> None:
        pass

class GpsWaitFloatOp(Operation):
    def on_start(self, params: Dict[str, Any]) -> None:
        pass
    def run(self) -> None:
        pass
    def on_stop(self) -> None:
        pass

class ImuCalibrationOp(Operation):
    def on_start(self, params: Dict[str, Any]) -> None:
        pass
    def run(self) -> None:
        pass
    def on_stop(self) -> None:
        pass

class KidnapWaitOp(Operation):
    def on_start(self, params: Dict[str, Any]) -> None:
        pass
    def run(self) -> None:
        pass
    def on_stop(self) -> None:
        pass

class WaitOp(Operation):
    def on_start(self, params: Dict[str, Any]) -> None:
        self._delay = params.get('delay', 1)
        self._start = time.time()
    def run(self) -> None:
        if time.time() - self._start >= self._delay:
            self.stop()
    def on_stop(self) -> None:
        pass
