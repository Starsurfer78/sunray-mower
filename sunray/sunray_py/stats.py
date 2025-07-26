import time
from enum import Enum

class OperationType(Enum):
    IDLE = 0
    MOW = 1
    CHARGE = 2
    ERROR = 3
    DOCK = 4

class Stats:
    """
    Statistikzähler portiert aus Stats.cpp.
    Aufruf: stats.calc(op, motor_recovery, gps_solution)
    """
    def __init__(self):
        # Sekunden-Zähler
        self.idle_duration = 0
        self.charge_duration = 0
        self.mow_duration = 0
        self.mow_recovery = 0
        self.mow_fix = 0
        self.mow_float = 0
        self.mow_invalid = 0
        # Weitere Zähler
        self.invalid_recoveries = 0
        self.imu_recoveries = 0
        self.obstacles = 0
        self.bumper = 0
        self.sonar = 0
        self.lift = 0
        self.gps_timeouts = 0
        # intern
        self._last_solution = None
        self._next_stat_time = time.time()

    def reset(self) -> None:
        """Setzt alle Statistiken auf Null."""
        for attr in list(self.__dict__):
            if not attr.startswith("_"):
                setattr(self, attr, 0)

    def calc(self, op: OperationType, motor_recovery: bool, gps_solution: OperationType) -> None:
        """
        Muss im Loop aufgerufen werden, z.B. einmal pro Sekunde.
        op: aktuelle Operation
        motor_recovery: True, wenn Motor im Erholungsmodus
        gps_solution: OperationType.FLOAT/FIX/ERROR als Ersatz
        """
        now = time.time()
        if now < self._next_stat_time:
            return
        self._next_stat_time = now + 1.0
        if op == OperationType.IDLE:
            self.idle_duration += 1
        elif op == OperationType.MOW:
            self.mow_duration += 1
            if motor_recovery:
                self.mow_recovery += 1
            if gps_solution == OperationType.CHARGE:
                self.mow_fix += 1
            elif gps_solution == OperationType.ERROR:
                self.mow_invalid += 1
            # track solution changes
            if self._last_solution and gps_solution != self._last_solution:
                if self._last_solution == OperationType.ERROR and gps_solution == OperationType.CHARGE:
                    self.invalid_recoveries += 1
            self._last_solution = gps_solution
        elif op == OperationType.CHARGE:
            self.charge_duration += 1
        # weitere Fälle nach Bedarf...
