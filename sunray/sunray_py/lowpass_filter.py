import time

class LowPassFilter:
    """
    Exponentieller Tiefpass-Filter.
    y[n] = alpha * y[n-1] + (1 - alpha) * x[n]
    alpha = exp(-dt / time_constant)
    """
    def __init__(self, time_constant: float):
        self.time_constant = time_constant
        self._last = 0.0
        self._last_time = None

    def reset(self):
        """Setzt internen Zustand zurück."""
        self._last = 0.0
        self._last_time = None

    def __call__(self, x: float) -> float:
        """
        Filtert Eingang x. Bei erstem Aufruf wird x zurückgegeben.
        """
        now = time.time()
        if self._last_time is None or self.time_constant <= 0:
            out = x
        else:
            dt = now - self._last_time
            alpha = 0.0
            try:
                alpha = pow(2.718281828459045, -dt / self.time_constant)
            except OverflowError:
                alpha = 0.0
            out = alpha * self._last + (1.0 - alpha) * x
        self._last = out
        self._last_time = now
        return out
