"""
Sunray Mähroboter - Python Implementation
Based on the Ardumower Sunray project

Original Sunray project:
- Forum: https://forum.ardumower.de/
- GitHub: https://github.com/Ardumower/Sunray
- Copyright (c) 2021-2024 by Alexander Grau, Grau GmbH

This implementation extends and adapts the original Sunray firmware
for Python-based autonomous mower control with enhanced features.

License: GPL-3.0 (same as original Sunray project)
Author: [Ihr Name]
Project: https://github.com/Starsurfer78/sunray-mower
"""

import time
from typing import Dict
from config import Config
from lowpass_filter import LowPassFilter
from running_median import RunningMedian

class Battery:
    """
    Batteriemanagement-Logik aus Sunray-Firmware portiert nach Python.
    Methoden:
      - begin(): Initialisiert interne Zustände.
      - enable_charging(flag): Steuerung des Lade-Relais.
      - run(battery_v, charge_v, charge_i): Verarbeitungsschritt mit aktuellen Spannungs- und Stromwerten.
      - Abfrage-Methoden: charger_connected(), is_docked(), should_go_home(), under_voltage(), is_charging_completed().
    """
    def __init__(self, config: Config = None):
        # Lade Konfiguration
        if config is None:
            config = Config()
        
        # Batterie-Parameter aus Konfiguration laden
        battery_config = config.get('battery', {})
        voltage_thresholds = battery_config.get('voltage_thresholds', {})
        charging_config = battery_config.get('charging', {})
        power_management = battery_config.get('power_management', {})
        filtering_config = battery_config.get('filtering', {})
        
        # Parameter mit Fallback-Werten
        self.bat_go_home_if_below = voltage_thresholds.get('go_home_if_below', 21.5)
        self.bat_switch_off_if_below = voltage_thresholds.get('switch_off_if_below', 20.0)
        self.bat_full_voltage = voltage_thresholds.get('full_voltage', 28.7)
        self.bat_full_current = charging_config.get('full_current', 0.2)
        self.enable_charging_timeout = charging_config.get('timeout', 1800)
        self.bat_switch_off_if_idle = power_management.get('switch_off_if_idle', 300)
        
        # Filter-Parameter
        self.voltage_filter_enabled = filtering_config.get('voltage_filter_enabled', True)
        self.voltage_filter_time_constant = filtering_config.get('voltage_filter_time_constant', 5.0)
        self.voltage_median_filter_size = filtering_config.get('voltage_median_filter_size', 5)
        self.low_voltage_confirmation_time = filtering_config.get('low_voltage_confirmation_time', 10.0)
        
        # Filter initialisieren
        self.voltage_lowpass_filter = LowPassFilter(self.voltage_filter_time_constant)
        self.voltage_median_filter = RunningMedian(self.voltage_median_filter_size)
        
        # Spannungsüberwachung für bestätigte Niederspannung
        self._low_voltage_start_time = None
        self._switch_off_voltage_start_time = None

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
        
        # Filter zurücksetzen
        self.voltage_lowpass_filter.reset()
        self._low_voltage_start_time = None
        self._switch_off_voltage_start_time = None

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
        Verwendet Bestätigungszeit um kurze Spannungsabfälle zu ignorieren.
        """
        if self._startup_phase < 2:
            return False
        
        now = time.monotonic()
        voltage_low = self._last_battery_voltage < self.bat_go_home_if_below
        
        if voltage_low:
            if self._low_voltage_start_time is None:
                self._low_voltage_start_time = now
            # Bestätige niedrige Spannung nur nach Wartezeit
            return (now - self._low_voltage_start_time) >= self.low_voltage_confirmation_time
        else:
            # Spannung ist wieder OK, Timer zurücksetzen
            self._low_voltage_start_time = None
            return False

    def under_voltage(self) -> bool:
        """
        True, wenn Batteriespannung unter Abschaltschwelle und Startup beendet.
        Verwendet Bestätigungszeit um kurze Spannungsabfälle zu ignorieren.
        """
        if self._startup_phase < 2:
            return False
        
        now = time.monotonic()
        voltage_critical = self._last_battery_voltage < self.bat_switch_off_if_below
        
        if voltage_critical:
            if self._switch_off_voltage_start_time is None:
                self._switch_off_voltage_start_time = now
            # Bestätige kritische Spannung nur nach Wartezeit
            return (now - self._switch_off_voltage_start_time) >= self.low_voltage_confirmation_time
        else:
            # Spannung ist wieder OK, Timer zurücksetzen
            self._switch_off_voltage_start_time = None
            return False

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

        # Spannungsfilterung anwenden
        if self.voltage_filter_enabled:
            # Median-Filter für Ausreißer-Entfernung
            self.voltage_median_filter.add(battery_v)
            median_voltage = self.voltage_median_filter.median()
            
            # Tiefpass-Filter für Glättung
            filtered_voltage = self.voltage_lowpass_filter(median_voltage)
        else:
            filtered_voltage = battery_v
        
        # Speichere letzte gefilterte Batteriespannung
        self._last_battery_voltage = filtered_voltage

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
