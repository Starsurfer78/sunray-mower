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
    def on_start(self, params: Dict[str, Any]) -> None:
        # Initialisierung Mähvorgang
        pass

    def run(self) -> None:
        # Logik Mähstrategie
        pass

    def on_stop(self) -> None:
        # Aufräumen
        pass

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
            # Fallback: Direktes Pico-Kommando
            from pico_comm import PicoComm
            self.pico = PicoComm(port='/dev/ttyS0', baudrate=115200)
            self.pico.send_command("AT+MOTOR,0,0,0")
    
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
                self.pico.send_command("AT+MOTOR,100,100,0")  # Fallback
        
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
                self.pico.send_command(f"AT+MOTOR,{left_speed},{right_speed},0")
        
        elif self.phase == "rotate" and elapsed_in_phase >= self.rotate_duration:
            # Drehung beendet, Operation abschließen
            self.phase = "complete"
            if self.motor:
                self.motor.stop_immediately(include_mower=False)
            else:
                self.pico.send_command("AT+MOTOR,0,0,0")  # Fallback
            
            # Zurück zum Mähen wechseln
            from events import Logger, EventCode
            Logger.event(EventCode.OBSTACLE_DETECTED, "Escape maneuver completed")
            
            # Operation beenden (wird in der Hauptschleife auf MowOp zurückgesetzt)
            self.active = False
    
    def on_stop(self) -> None:
        # Aufräumen: Motoren stoppen
        if self.motor:
            self.motor.stop_immediately(include_mower=False)
        elif hasattr(self, 'pico'):
            self.pico.send_command("AT+MOTOR,0,0,0")

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
