import re
from typing import Dict, Optional, Tuple

class CommParser:
    """
    Parser für ASCII-basierte Sunray-Kommandos (AT+X).
    Jede Zeile beginnt mit 'AT+' gefolgt von Befehlscode und optional Parametern.
    Methoden:
      - process_line(line: str) -> str: Verarbeitet eine Eingabezeile und liefert die Antwort (mit CRC).
    """

    CRC_MOD = 256

    def __init__(self):
        # interner Zustand, z.B. Parameter für tuneParam
        self.state: Dict[str, float] = {}

    def _compute_crc(self, s: str) -> str:
        crc = sum(ord(c) for c in s) % self.CRC_MOD
        return f"{crc:02X}"

    def _answer(self, code: str) -> str:
        """Generiert die Antwort mit Code und CRC."""
        crc = self._compute_crc(code)
        return f"{code},{crc}\r\n"

    def process_line(self, line: str) -> str:
        """
        Verarbeitet eine ASCII-Zeile.
        Erwartet Format: 'AT+<Cmd><Rest>'.
        Liefert Antwort via _answer().
        """
        line = line.strip()
        if not line.startswith("AT+"):
            return ""
        cmd = line[3:]
        # AT+S: Summary oder AT+S2: Obstacles
        if cmd.startswith("S"):
            return self._answer("S")
        if cmd.startswith("M,"):
            return self._answer("M")
        if cmd.startswith("C"):
            # TuneParam: AT+CT,<idx>,<value>
            if cmd.startswith("CT"):
                return self._answer("CT")
            # Control: AT+C,<mow>,<op>,...
            return self._answer("C")
        if cmd.startswith("W,"):
            return self._answer("W")
        if cmd.startswith("N,"):
            return self._answer("N")
        if cmd.startswith("X,"):
            return self._answer("X")
        if cmd.startswith("V,"):
            return self._answer("V")
        # weitere Kommandos als Platzhalter
        # E: MotorTest, Q: MotorPlot, F: SensorTest, etc.
        code = cmd[0]
        return self._answer(code)

# Beispielnutzung
# parser = CommParser()
# response = parser.process_line("AT+S")
# print(response)
