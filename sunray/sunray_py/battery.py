import time
from typing import Dict

class Battery:
    """
    Batteriemanagement-Logik aus Sunray-Firmware portiert nach Python.
    Methoden:
      - begin(): Initialisiert interne Zustände.
      - enable_charging(flag): Steuerung des Lade-Relais.
      - run(battery_v, charge_v, charge_i): Verarbeitungsschritt mit aktuellen Spannungs- und Stromwerten.
      - Abfrage-Methoden: charger_connected(), is_docked(), should_go_home(), under_voltage(), is_charging_completed().
    """
    def __init__(
        self,
        bat_go_home_if_below: float = 21.5,
        bat_switch_off_if_below: float = 20.0,
        bat_switch_off_if_idle: float = 300,
        bat_full_current: float = 0.2,
        bat_full_voltage: float = 28.7,
        enable_charging_timeout: int = 1800,
    ):
        # Parameter
        self.bat_go_home_if_below = bat_go_home_if_below
        self.bat_switch_off_if_below = bat_switch_off_if_below
        self.bat_switch_off_if_idle = bat_switch_off_if_idle
        self.bat_full_current = bat_full_current
        self.bat_full_voltage = bat_full_voltage
        self.enable_charging_timeout = enable_charging_timeout

        # Statusvariablen
        self.docked = False
        self.charger_connected_state = False
        self.charging_enabled = False
        self._charging_completed = False
        self._last_battery_voltage = 0.0
        self.switch_off_time = 0.0

        # Laufzeit-Variablen
        self._startup_phase = 0
        self._next_battery_time = 0.0
        self._next_enable_time = 0.0
        self._charging_start = 0.0

        self.begin()

    def begin(self):
        """
        Setzt alle internen Timer und Zustände zurück.
        """
        now = time.monotonic()
        self._startup_phase = 0
        self._next_battery_time = now
        self._next_enable_time = now
        self._charging_start = now
        self.switch_off_time = now + self.bat_switch_off_if_idle

    def enable_charging(self, flag: bool):
        """
        Setzt das Lade-Relais (extern). Hier nur internes Flag setzen.
        """
        self.charging_enabled = flag

    def charger_connected(self) -> bool:
        return self.charger_connected_state

    def is_docked(self) -> bool:
        return self.docked

    def set_docked(self, state: bool):
        self.docked = state

    def should_go_home(self) -> bool:
        """
        True, wenn Batteriespannung unter Schwelle und Startup beendet.
        """
        if self._startup_phase < 2:
            return False
        return self._last_battery_voltage < self.bat_go_home_if_below

    def under_voltage(self) -> bool:
        """
        True, wenn Batteriespannung unter Abschaltschwelle und Startup beendet.
        """
        if self._startup_phase < 2:
            return False
        return self._last_battery_voltage < self.bat_switch_off_if_below

    def is_charging_completed(self) -> bool:
        return self._charging_completed

    def reset_idle(self):
        """
        Setzt den Idle-Timer zurück.
        """
        self.switch_off_time = time.monotonic() + self.bat_switch_off_if_idle

    def run(self, battery_v: float, charge_v: float, charge_i: float) -> Dict[str, bool]:
        """
        Muss in Schleife aufgerufen werden. Übergibt aktuelle Messwerte:
          battery_v: gemessene Batterie-Spannung
          charge_v : Ladespannung
          charge_i : Ladestrom
        Rückgabe:
          {
            'enable_charging': bool,
            'keep_power_on': bool,
            'switch_off': bool
          }
        """
        now = time.monotonic()

        # Startup-Phase initial delay
        if self._startup_phase == 0:
            self._next_battery_time = now + 2.0
            self._startup_phase = 1
            return {}
        if now < self._next_battery_time:
            return {}
        if self._startup_phase == 1:
            self._startup_phase = 2
        # Intervall 50ms
        self._next_battery_time = now + 0.05

        # Speichere letzte Batteriespannung
        self._last_battery_voltage = battery_v

        # Charger Connected Erkennung (Threshold)
        self.charger_connected_state = (charge_v > 5.0)

        # Idle-Abschaltung prüfen
        switch_off = False
        if self.under_voltage():
            switch_off = True
        elif now >= self.switch_off_time:
            switch_off = True

        # Ladezustand prüfen
        if self.charger_connected_state:
            if self.charging_enabled:
                # Nach 30s prüfen, ob Laden abgeschlossen
                if now - self._charging_start > 30.0:
                    done = (charge_i <= self.bat_full_current) or (battery_v >= self.bat_full_voltage)
                    if done:
                        self._charging_completed = True
                        self._next_enable_time = now + self.enable_charging_timeout
                        self.enable_charging(False)
            else:
                # Bei niedriger Batteriespannung Laden aktivieren
                if battery_v < self.bat_go_home_if_below:
                    self.enable_charging(True)
                    self._charging_start = now

        # Stromversorgung halten, wenn nicht abschalten
        keep_power = not switch_off

        return {
            'enable_charging': self.charging_enabled,
            'keep_power_on': keep_power,
            'switch_off': switch_off
        }
