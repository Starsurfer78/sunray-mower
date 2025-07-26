import time
from typing import Optional

class PID:
    """
    PID-Regler portiert aus Sunray-Firmware.
    Methoden:
      - reset(): Setzt Integral- und Vorzeichenzustand zurück.
      - compute(error: float, dt: float = None) -> float: Berechnet die Stellgröße.
    """
    def __init__(self, Kp: float = 0.0, Ki: float = 0.0, Kd: float = 0.0):
        self.Kp = Kp
        self.Ki = Ki
        self.Kd = Kd
        self._integral = 0.0
        self._last_error = 0.0
        self._last_time = None

    def reset(self):
        """Setzt Integral- und letzte Fehlergröße zurück."""
        self._integral = 0.0
        self._last_error = 0.0
        self._last_time = None

    def compute(self, error: float, dt: Optional[float] = None) -> float:
        """
        Berechnet PID-Ausgang basierend auf Fehler und Zeitdifferenz dt.
        Wenn dt nicht übergeben, wird Zeit seit letzter Ausführung verwendet.
        """
        now = time.time()
        if dt is None:
            if self._last_time is None:
                dt = 0.0
            else:
                dt = now - self._last_time
        self._last_time = now

        # Integralterm
        self._integral += error * dt

        # Differentialterm
        derivative = 0.0
        if dt > 0.0:
            derivative = (error - self._last_error) / dt

        # PID-Ausgang
        output = (self.Kp * error) + (self.Ki * self._integral) + (self.Kd * derivative)

        # Error sichern
        self._last_error = error

        return output

class VelocityPID(PID):
    """
    Erweiterter PID-Regler für Geschwindigkeit (Sunray VelocityPID).
    Evtl. zusätzliches Verhalten implementieren.
    """
    def __init__(self, Kp: float = 0.0, Ki: float = 0.0, Kd: float = 0.0):
        super().__init__(Kp, Ki, Kd)
