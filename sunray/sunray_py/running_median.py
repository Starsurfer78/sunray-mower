import bisect
from typing import List

class RunningMedian:
    """
    Einfacher gleitender Median-Filter.
    Puffer mit fester Größe, neue Werte schieben, Median berechnen.
    """
    def __init__(self, size: int):
        self.size = size
        self.buffer: List[float] = []
        self.sorted: List[float] = []

    def add(self, value: float) -> None:
        """
        Fügt neuen Wert hinzu. Entfernt ältesten, wenn Puffer voll.
        """
        if len(self.buffer) == self.size:
            old = self.buffer.pop(0)
            # alten Wert aus sortierter Liste entfernen
            idx = bisect.bisect_left(self.sorted, old)
            if 0 <= idx < len(self.sorted):
                self.sorted.pop(idx)
        # neuen Wert in Puffer und sortierte Liste einfügen
        self.buffer.append(value)
        bisect.insort(self.sorted, value)

    def median(self) -> float:
        """
        Gibt Median des aktuellen Puffers zurück.
        """
        n = len(self.sorted)
        if n == 0:
            return 0.0
        if n % 2 == 1:
            return self.sorted[n // 2]
        else:
            return 0.5 * (self.sorted[n // 2 - 1] + self.sorted[n // 2])
