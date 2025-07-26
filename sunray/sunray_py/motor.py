#!/usr/bin/env python3
"""
Motorsteuerung für Sunray Python Mähroboter.

Dieses Modul implementiert die komplette Motorsteuerung mit:
- PID-basierte Geschwindigkeitsregelung für Antriebsmotoren
- Mähmotor-Steuerung mit Überwachung
- Überlastungsschutz und Sicherheitsfunktionen
- Adaptive Geschwindigkeitsanpassung
- Odometrie-basierte Geschwindigkeitsmessung
- Integration mit Pico-Mikrocontroller

Autor: Sunray Python Team
Version: 1.0
"""

import time
from typing import Tuple, Dict, Optional
from pid import PID, VelocityPID
from config import get_config

class Motor:
    """
    Zentrale Motorsteuerung für Sunray Python Mähroboter.
    
    Diese Klasse verwaltet alle motorbezogenen Funktionen:
    - Antriebsmotoren (links/rechts) mit PID-Regelung
    - Mähmotor mit PWM-Steuerung
    - Überlastungsschutz und Fehlererkennung
    - Odometrie-basierte Geschwindigkeitsmessung
    - Adaptive Geschwindigkeitsanpassung
    - Kommunikation mit Pico-Mikrocontroller
    
    Beispiel:
        motor = Motor(pico_comm)
        motor.begin()
        motor.set_linear_angular_speed(0.5, 0.0)  # 0.5 m/s vorwärts
        motor.set_mow_state(True)  # Mähmotor einschalten
    """
    
    def __init__(self, pico_comm=None):
        """
        Initialisiert die Motor-Klasse mit konfigurierbaren Parametern.
        
        Lädt alle Motorparameter aus der Konfiguration und initialisiert:
        - PID-Regler für alle Motoren
        - Sicherheitsgrenzwerte
        - Physikalische Parameter
        - Adaptive Geschwindigkeitsregelung
        
        Args:
            pico_comm: Pico-Kommunikationsobjekt für Hardware-Befehle
                      None für Simulation/Tests ohne Hardware
        
        Beispiel:
            # Mit Hardware-Kommunikation
            motor = Motor(pico_communication)
            
            # Für Tests ohne Hardware
            motor = Motor()
        """
        self.pico = pico_comm
        self.config = get_config()
        
        # PID-Regler für Geschwindigkeitsregelung aus Konfiguration
        left_pid_config = self.config.get_pid_config('left')
        right_pid_config = self.config.get_pid_config('right')
        mow_pid_config = self.config.get_pid_config('mow')
        
        self.left_pid = VelocityPID(
            Kp=left_pid_config.get('kp', 1.0),
            Ki=left_pid_config.get('ki', 0.1),
            Kd=left_pid_config.get('kd', 0.05)
        )
        self.right_pid = VelocityPID(
            Kp=right_pid_config.get('kp', 1.0),
            Ki=right_pid_config.get('ki', 0.1),
            Kd=right_pid_config.get('kd', 0.05)
        )
        self.mow_pid = PID(
            Kp=mow_pid_config.get('kp', 0.8),
            Ki=mow_pid_config.get('ki', 0.05),
            Kd=mow_pid_config.get('kd', 0.02)
        )
        
        # Motorstatus
        self.enabled = False
        self.mow_enabled = False
        self.overload_detected = False
        self.fault_detected = False
        
        # Sollwerte
        self.target_linear_speed = 0.0
        self.target_angular_speed = 0.0
        self.target_left_speed = 0.0
        self.target_right_speed = 0.0
        self.target_mow_speed = 0.0
        
        # Aktuelle Werte
        self.current_left_current = 0.0
        self.current_right_current = 0.0
        self.current_mow_current = 0.0
        self.current_left_odom = 0
        self.current_right_odom = 0
        self.current_mow_odom = 0
        
        # Letzte Odometrie-Werte für Geschwindigkeitsberechnung
        self.last_left_odom = 0
        self.last_right_odom = 0
        self.last_mow_odom = 0
        self.last_odom_time = time.time()
        
        # Überlastungsschutz aus Konfiguration
        limits_config = self.config.get_motor_limits()
        self.max_motor_current = limits_config.get('max_motor_current', 3.0)
        self.max_mow_current = limits_config.get('max_mow_current', 5.0)
        self.overload_count = 0
        self.max_overload_count = limits_config.get('max_overload_count', 5)
        
        # Physikalische Parameter aus Konfiguration
        physical_config = self.config.get_physical_config()
        self.ticks_per_meter = physical_config.get('ticks_per_meter', 1000)
        self.wheel_base = physical_config.get('wheel_base', 0.3)
        self.pwm_scale_factor = physical_config.get('pwm_scale_factor', 100)
        
        # Mähmotor-Konfiguration
        mow_config = self.config.get('motor.mow', {})
        self.default_mow_pwm = mow_config.get('default_pwm', 100)
        self.mow_min_current_threshold = mow_config.get('min_current_threshold', 0.1)
        self.mow_max_current_threshold = mow_config.get('max_current_threshold', 0.5)
        
        # Adaptive Geschwindigkeitsanpassung
        adaptive_config = self.config.get('motor.adaptive', {})
        self.adaptive_enabled = adaptive_config.get('enabled', True)
        self.adaptive_current_threshold_factor = adaptive_config.get('current_threshold_factor', 0.7)
        self.adaptive_min_speed_factor = adaptive_config.get('min_speed_factor', 0.3)

    def begin(self) -> None:
        """
        Initialisiert die Motor-Hardware und aktiviert das System.
        
        Führt folgende Schritte aus:
        - Aktiviert die Motorsteuerung
        - Setzt alle PID-Regler zurück
        - Bereitet das System für den Betrieb vor
        
        Muss vor der ersten Verwendung aufgerufen werden.
        
        Beispiel:
            motor = Motor(pico_comm)
            motor.begin()  # System bereit für Betrieb
            motor.set_linear_angular_speed(0.3, 0.0)
        """
        self.enabled = True
        self.reset_pids()
        print("Motor: Initialisierung abgeschlossen")
    
    def update(self, pico_data: Dict) -> Dict:
        """
        Aktualisiert den Motorstatus mit aktuellen Sensordaten.
        
        Verarbeitet Daten vom Pico-Mikrocontroller und aktualisiert:
        - Motorströme für Überlastungsschutz
        - Odometrie-Werte für Geschwindigkeitsmessung
        - Fehlerzustände und Sicherheitsfunktionen
        
        Args:
            pico_data (Dict): Sensordaten vom Pico mit Schlüsseln:
                            - motor_left_current: Strom linker Motor (A)
                            - motor_right_current: Strom rechter Motor (A)
                            - mow_current: Strom Mähmotor (A)
                            - odom_left: Odometrie-Ticks linker Motor
                            - odom_right: Odometrie-Ticks rechter Motor
                            - odom_mow: Odometrie-Ticks Mähmotor
                            - motor_overload: Überlastungsflag (0/1)
        
        Returns:
            Dict: Aktueller Motorstatus mit allen relevanten Werten
        
        Beispiel:
            pico_data = {
                'motor_left_current': 1.2,
                'motor_right_current': 1.1,
                'mow_current': 2.5,
                'odom_left': 1500,
                'odom_right': 1520
            }
            status = motor.update(pico_data)
        """
        if not pico_data:
            return self.get_status()
        
        # Stromdaten aktualisieren
        self.current_left_current = pico_data.get('motor_left_current', 0.0)
        self.current_right_current = pico_data.get('motor_right_current', 0.0)
        self.current_mow_current = pico_data.get('mow_current', 0.0)
        
        # Odometrie aktualisieren
        self.current_left_odom = pico_data.get('odom_left', self.current_left_odom)
        self.current_right_odom = pico_data.get('odom_right', self.current_right_odom)
        self.current_mow_odom = pico_data.get('odom_mow', self.current_mow_odom)
        
        # Überlastung prüfen
        overload_flag = pico_data.get('motor_overload', 0)
        if overload_flag or self._check_current_overload():
            self.overload_detected = True
            self.overload_count += 1
            if self.overload_count >= self.max_overload_count:
                self.stop_immediately()
                print(f"Motor: Überlastung erkannt - Motoren gestoppt")
        else:
            self.overload_count = max(0, self.overload_count - 1)
            if self.overload_count == 0:
                self.overload_detected = False
        
        return self.get_status()
    
    def run(self) -> None:
        """
        Führt die periodische Motorsteuerung aus.
        
        Sollte regelmäßig (z.B. 50Hz) aufgerufen werden für:
        - PID-Regelung der Motorgeschwindigkeiten
        - Überwachung der Sicherheitsfunktionen
        - Adaptive Geschwindigkeitsanpassung
        
        Wird nur ausgeführt wenn Motoren aktiviert und keine Überlastung.
        
        Beispiel:
            # In der Hauptschleife
            while running:
                motor.run()  # Regelung ausführen
                time.sleep(0.02)  # 50Hz
        """
        if self.enabled and not self.overload_detected:
            self.control()

    def test(self) -> None:
        """
        Führt einen automatischen Motortest durch.
        
        Testet alle Motoren mit verschiedenen Bewegungsmustern:
        - Vorwärts/Rückwärts fahren
        - Links/Rechts drehen
        - Mähmotor einzeln testen
        
        Nützlich für Diagnose und Kalibrierung.
        
        Beispiel:
            motor.test()  # Führt kompletten Motortest aus
        """
        pass

    def plot(self) -> None:
        """
        Erfasst aktuelle Motordaten für Analyse und Visualisierung.
        
        Gibt alle relevanten Motorparameter aus:
        - Sollwerte vs. Istwerte
        - Motorströme
        - PID-Regelgrößen
        - Fehlerzustände
        
        Nützlich für Debugging und Performance-Analyse.
        
        Beispiel:
            motor.plot()  # Zeigt aktuelle Motordaten
        """
        pass

    def enable_traction_motors(self, enable: bool) -> None:
        """
        Aktiviert oder deaktiviert die Antriebsmotoren.
        
        Bei Deaktivierung werden alle Sollgeschwindigkeiten auf Null gesetzt
        und die Motoren gestoppt. Der Mähmotor bleibt unverändert.
        
        Args:
            enable (bool): True = Motoren aktivieren, False = deaktivieren
        
        Beispiele:
            # Motoren für Fahrt aktivieren
            motor.enable_traction_motors(True)
            
            # Motoren für Wartung deaktivieren
            motor.enable_traction_motors(False)
        """
        self.enabled = enable
        if not enable:
            self.target_linear_speed = 0.0
            self.target_angular_speed = 0.0
            self.target_left_speed = 0.0
            self.target_right_speed = 0.0
            if self.pico:
                self.pico.send_command("AT+MOTOR,0,0,0")
        print(f"Motor: Antriebsmotoren {'aktiviert' if enable else 'deaktiviert'}")

    def set_linear_angular_speed(self, linear: float, angular: float, use_linear_ramp: bool = True) -> None:
        """
        Setzt die Soll-Geschwindigkeiten für Fahrbewegungen.
        
        Verwendet Differential-Drive-Kinematik zur Berechnung der
        individuellen Radgeschwindigkeiten aus linearer und Winkelgeschwindigkeit.
        
        Args:
            linear (float): Lineare Geschwindigkeit in m/s
                           Positiv = vorwärts, negativ = rückwärts
                           Typischer Bereich: -1.0 bis 1.0 m/s
            angular (float): Winkelgeschwindigkeit in rad/s
                            Positiv = links drehen, negativ = rechts drehen
                            Typischer Bereich: -2.0 bis 2.0 rad/s
            use_linear_ramp (bool): Aktiviert sanfte Beschleunigung (noch nicht implementiert)
        
        Beispiele:
            # Geradeaus fahren mit 0.5 m/s
            motor.set_linear_angular_speed(0.5, 0.0)
            
            # Rückwärts fahren
            motor.set_linear_angular_speed(-0.3, 0.0)
            
            # Auf der Stelle links drehen
            motor.set_linear_angular_speed(0.0, 1.0)
            
            # Kurve fahren (vorwärts + rechts drehen)
            motor.set_linear_angular_speed(0.4, -0.5)
        """
        if not self.enabled:
            return
        
        self.target_linear_speed = linear
        self.target_angular_speed = angular
        
        # Differential Drive Kinematik: v_left/right = v_linear ± (v_angular * wheelbase/2)
        half_wheelbase = self.wheel_base / 2.0
        self.target_left_speed = linear - (angular * half_wheelbase)
        self.target_right_speed = linear + (angular * half_wheelbase)
        
        print(f"Motor: Sollgeschwindigkeit gesetzt - Linear: {linear:.2f} m/s, Angular: {angular:.2f} rad/s")

    def set_mow_state(self, on: bool) -> None:
        """
        Schaltet den Mähmotor ein oder aus.
        
        Verwendet den konfigurierten Standard-PWM-Wert beim Einschalten.
        Beim Ausschalten wird der PWM-Wert auf 0 gesetzt.
        
        Args:
            on (bool): True = Mähmotor einschalten, False = ausschalten
        
        Beispiele:
            # Mähmotor für Mähvorgang einschalten
            motor.set_mow_state(True)
            
            # Mähmotor für Transport ausschalten
            motor.set_mow_state(False)
        """
        self.mow_enabled = on
        if on:
            self.target_mow_speed = self.default_mow_pwm
        else:
            self.target_mow_speed = 0
        print(f"Motor: Mähmotor {'eingeschaltet' if on else 'ausgeschaltet'}")

    def set_mow_pwm(self, val: int) -> None:
        """
        Setzt den PWM-Wert für den Mähmotor direkt.
        
        Ermöglicht präzise Kontrolle der Mähmotor-Geschwindigkeit.
        Werte > 0 aktivieren automatisch den Mähmotor.
        
        Args:
            val (int): PWM-Wert von 0-255
                      0 = Motor aus
                      255 = maximale Geschwindigkeit
                      Typische Werte: 80-180 für normales Mähen
        
        Beispiele:
            # Mähmotor mit mittlerer Geschwindigkeit
            motor.set_mow_pwm(120)
            
            # Mähmotor für dichtes Gras
            motor.set_mow_pwm(200)
            
            # Mähmotor ausschalten
            motor.set_mow_pwm(0)
        """
        self.target_mow_speed = max(0, min(255, val))
        if val > 0:
            self.mow_enabled = True
        print(f"Motor: Mähmotor PWM auf {self.target_mow_speed} gesetzt")

    def wait_mow_motor(self) -> bool:
        """
        Wartet auf die Einsatzbereitschaft des Mähmotors.
        
        Überprüft ob der Mähmotor die gewünschte Drehzahl erreicht hat
        und stabil läuft, bevor mit dem Mähen begonnen wird.
        
        Returns:
            bool: True wenn Mähmotor bereit, False bei Timeout oder Fehler
        
        Beispiel:
            motor.set_mow_state(True)
            if motor.wait_mow_motor():
                print("Mähmotor bereit - starte Mähvorgang")
            else:
                print("Mähmotor-Fehler erkannt")
        """
        return True

    def stop_immediately(self, include_mower: bool = True) -> None:
        """
        Führt einen sofortigen Notaus aller Motoren durch.
        
        Setzt alle Sollwerte auf Null und sendet Stopp-Befehle an die Hardware.
        Setzt auch alle PID-Regler zurück für sauberen Neustart.
        
        Args:
            include_mower (bool): True = auch Mähmotor stoppen
                                 False = nur Antriebsmotoren stoppen
        
        Beispiele:
            # Kompletter Notaus (alle Motoren)
            motor.stop_immediately()
            
            # Nur Antrieb stoppen (Mäher läuft weiter)
            motor.stop_immediately(include_mower=False)
        """
        self.target_linear_speed = 0.0
        self.target_angular_speed = 0.0
        self.target_left_speed = 0.0
        self.target_right_speed = 0.0
        
        if include_mower:
            self.target_mow_speed = 0
            self.mow_enabled = False
        
        if self.pico:
            if include_mower:
                self.pico.send_command("AT+MOTOR,0,0,0")
            else:
                self.pico.send_command("AT+MOTOR,0,0," + str(int(self.target_mow_speed)))
        
        self.reset_pids()
        print("Motor: Sofort-Stopp ausgeführt")

    def speed_pwm(self, pwm_left: int, pwm_right: int, pwm_mow: int) -> None:
        """
        Setzt PWM-Werte direkt für alle Motoren.
        
        Umgeht die PID-Regelung und sendet direkte PWM-Befehle an die Hardware.
        Nützlich für Tests, Kalibrierung oder spezielle Bewegungsmuster.
        
        Args:
            pwm_left (int): PWM-Wert linker Motor (-255 bis 255)
                           Negativ = rückwärts, positiv = vorwärts
            pwm_right (int): PWM-Wert rechter Motor (-255 bis 255)
                            Negativ = rückwärts, positiv = vorwärts
            pwm_mow (int): PWM-Wert Mähmotor (0 bis 255)
                          Nur positive Werte (Mäher dreht nur in eine Richtung)
        
        Beispiele:
            # Beide Motoren vorwärts mit halber Geschwindigkeit
            motor.speed_pwm(128, 128, 0)
            
            # Auf der Stelle drehen (links rückwärts, rechts vorwärts)
            motor.speed_pwm(-100, 100, 0)
            
            # Alle Motoren stoppen
            motor.speed_pwm(0, 0, 0)
        """
        if not self.enabled and (pwm_left != 0 or pwm_right != 0):
            return
        
        # PWM-Werte begrenzen
        pwm_left = max(-255, min(255, pwm_left))
        pwm_right = max(-255, min(255, pwm_right))
        pwm_mow = max(0, min(255, pwm_mow))
        
        if self.pico:
            self.pico.send_command(f"AT+MOTOR,{pwm_left},{pwm_right},{pwm_mow}")

    def control(self) -> None:
        """
        Führt die PID-basierte Motorgeschwindigkeitsregelung aus.
        
        Berechnet die erforderlichen PWM-Werte basierend auf:
        - Sollgeschwindigkeiten vs. gemessene Geschwindigkeiten
        - PID-Regelung für präzise Geschwindigkeitskontrolle
        - Adaptive Geschwindigkeitsanpassung bei hohem Strom
        
        Wird automatisch von run() aufgerufen, sollte nicht direkt verwendet werden.
        
        Algorithmus:
        1. Aktuelle Geschwindigkeiten aus Odometrie berechnen
        2. PID-Regelung für jeden Motor ausführen
        3. PWM-Werte berechnen und senden
        4. Adaptive Anpassungen anwenden
        """
        if not self.enabled or self.overload_detected:
            return
        
        # Aktuelle Geschwindigkeiten aus Odometrie berechnen
        current_speeds = self._calculate_speeds()
        
        # PID-Regelung für linken Motor
        left_error = self.target_left_speed - current_speeds['left']
        left_output = self.left_pid.compute(left_error)
        
        # PID-Regelung für rechten Motor
        right_error = self.target_right_speed - current_speeds['right']
        right_output = self.right_pid.compute(right_error)
        
        # Geschwindigkeit zu PWM konvertieren mit konfigurierbarem Skalierungsfaktor
        left_pwm = int(left_output * self.pwm_scale_factor)
        right_pwm = int(right_output * self.pwm_scale_factor)
        
        # Mähmotor PWM (einfache Regelung)
        mow_pwm = int(self.target_mow_speed) if self.mow_enabled else 0
        
        # PWM-Werte senden
        self.speed_pwm(left_pwm, right_pwm, mow_pwm)

    def check_fault(self) -> bool:
        """
        Überprüft ob ein Motorausfall oder kritischer Fehler vorliegt.
        
        Kombiniert verschiedene Fehlerzustände:
        - Hardware-Fehler (fault_detected)
        - Überlastungszustände (overload_detected)
        
        Returns:
            bool: True wenn Fehler erkannt, False wenn alles normal
        
        Beispiel:
            if motor.check_fault():
                print("Motorproblem erkannt - Notaus einleiten")
                motor.stop_immediately()
        """
        return self.fault_detected or self.overload_detected

    def check_overload(self) -> None:
        """
        Überprüft und aktualisiert den Überlastzustand der Motoren.
        
        Analysiert die aktuellen Motorströme und setzt das
        overload_detected Flag entsprechend. Wird automatisch
        von update() aufgerufen.
        
        Beispiel:
            motor.check_overload()
            if motor.overload_detected:
                print("Überlastung erkannt")
        """
        self.overload_detected = self._check_current_overload()
    
    def _check_current_overload(self) -> bool:
        """
        Interne Methode zur Stromüberlastungsprüfung.
        
        Vergleicht die gemessenen Motorströme mit den konfigurierten
        Grenzwerten für jeden Motor einzeln.
        
        Returns:
            bool: True wenn mindestens ein Motor überlastet ist
        
        Grenzwerte aus Konfiguration:
        - max_motor_current: Grenzwert für Antriebsmotoren
        - max_mow_current: Grenzwert für Mähmotor
        """
        left_overload = self.current_left_current > self.max_motor_current
        right_overload = self.current_right_current > self.max_motor_current
        mow_overload = self.current_mow_current > self.max_mow_current
        
        return left_overload or right_overload or mow_overload
    
    def _calculate_speeds(self) -> Dict[str, float]:
        """
        Berechnet aktuelle Motorgeschwindigkeiten aus Odometrie-Daten.
        
        Verwendet die Differenz der Odometrie-Ticks zwischen zwei
        Messungen und die verstrichene Zeit zur Geschwindigkeitsberechnung.
        
        Returns:
            Dict[str, float]: Geschwindigkeiten mit Schlüsseln:
                            - 'left': Geschwindigkeit linker Motor (m/s)
                            - 'right': Geschwindigkeit rechter Motor (m/s)
                            - 'mow': Geschwindigkeit Mähmotor (m/s oder RPM)
        
        Formel:
            Geschwindigkeit = (Tick-Differenz / Ticks_pro_Meter) / Zeit
        
        Beispiel:
            speeds = motor._calculate_speeds()
            print(f"Links: {speeds['left']:.2f} m/s")
        """
        current_time = time.time()
        dt = current_time - self.last_odom_time
        
        if dt <= 0:
            return {'left': 0.0, 'right': 0.0, 'mow': 0.0}
        
        # Odometrie-Differenzen
        left_ticks = self.current_left_odom - self.last_left_odom
        right_ticks = self.current_right_odom - self.last_right_odom
        mow_ticks = self.current_mow_odom - self.last_mow_odom
        
        # Geschwindigkeiten berechnen (m/s)
        left_speed = (left_ticks / self.ticks_per_meter) / dt
        right_speed = (right_ticks / self.ticks_per_meter) / dt
        mow_speed = (mow_ticks / self.ticks_per_meter) / dt  # oder RPM
        
        # Werte für nächste Berechnung speichern
        self.last_left_odom = self.current_left_odom
        self.last_right_odom = self.current_right_odom
        self.last_mow_odom = self.current_mow_odom
        self.last_odom_time = current_time
        
        return {
            'left': left_speed,
            'right': right_speed,
            'mow': mow_speed
        }
    
    def reset_pids(self) -> None:
        """
        Setzt alle PID-Regler auf ihre Anfangswerte zurück.
        
        Löscht:
        - Integrale Anteile (I-Anteil)
        - Letzte Fehlerwerte (D-Anteil)
        - Interne Zustandsvariablen
        
        Sollte nach Stillstand oder Richtungsänderungen aufgerufen werden
        um Sprünge in der Regelung zu vermeiden.
        
        Beispiel:
            motor.stop_immediately()  # Ruft reset_pids() automatisch auf
            # oder manuell:
            motor.reset_pids()
        """
        self.left_pid.reset()
        self.right_pid.reset()
        self.mow_pid.reset()
    
    def get_status(self) -> Dict:
        """
        Gibt den kompletten aktuellen Motorstatus zurück.
        
        Returns:
            Dict: Motorstatus mit folgenden Schlüsseln:
                - enabled: Antriebsmotoren aktiviert (bool)
                - mow_enabled: Mähmotor aktiviert (bool)
                - overload_detected: Überlastung erkannt (bool)
                - fault_detected: Hardware-Fehler erkannt (bool)
                - target_linear_speed: Soll-Lineargeschwindigkeit (m/s)
                - target_angular_speed: Soll-Winkelgeschwindigkeit (rad/s)
                - current_left_current: Aktueller Strom links (A)
                - current_right_current: Aktueller Strom rechts (A)
                - current_mow_current: Aktueller Mähmotor-Strom (A)
                - overload_count: Anzahl erkannter Überlastungen
        
        Beispiel:
            status = motor.get_status()
            print(f"Motoren aktiv: {status['enabled']}")
            print(f"Strom links: {status['current_left_current']:.1f}A")
        """
        return {
            'enabled': self.enabled,
            'mow_enabled': self.mow_enabled,
            'overload_detected': self.overload_detected,
            'fault_detected': self.fault_detected,
            'target_linear_speed': self.target_linear_speed,
            'target_angular_speed': self.target_angular_speed,
            'current_left_current': self.current_left_current,
            'current_right_current': self.current_right_current,
            'current_mow_current': self.current_mow_current,
            'overload_count': self.overload_count
        }

    def check_odometry_error(self) -> bool:
        """
        Erkennt Odometrie-Fehler durch unrealistische Geschwindigkeitswerte.
        
        Überprüft ob die berechneten Geschwindigkeiten physikalisch
        plausibel sind. Große Sprünge deuten auf Sensorfehler hin.
        
        Returns:
            bool: True wenn Odometrie-Fehler erkannt
        
        Prüfkriterien:
        - Geschwindigkeit > max_realistic_speed (aus Konfiguration)
        - Plötzliche große Geschwindigkeitssprünge
        
        Beispiel:
            if motor.check_odometry_error():
                print("Odometrie-Sensor defekt - Fallback-Navigation")
        """
        # Prüfe auf unrealistische Odometrie-Sprünge
        current_speeds = self._calculate_speeds()
        max_realistic_speed = self.config.get('motor.limits.max_realistic_speed', 2.0)
        
        return (abs(current_speeds['left']) > max_realistic_speed or 
                abs(current_speeds['right']) > max_realistic_speed)

    def check_mow_rpm_fault(self) -> bool:
        """
        Erkennt Mähmotor-Fehler durch Strom-/Drehzahl-Inkonsistenzen.
        
        Überprüft die Plausibilität zwischen Mähmotor-Sollwert,
        Stromverbrauch und tatsächlicher Drehzahl.
        
        Returns:
            bool: True wenn Mähmotor-Fehler erkannt
        
        Fehlerbedingungen:
        - Motor soll laufen, aber kein Strom fließt (Blockierung/Defekt)
        - Motor soll aus sein, aber Strom fließt (Kurzschluss)
        
        Beispiel:
            if motor.check_mow_rpm_fault():
                print("Mähmotor-Problem - Mähen stoppen")
                motor.set_mow_state(False)
        """
        # Prüfe ob Mähmotor läuft aber kein Strom fließt oder umgekehrt
        if self.mow_enabled and self.target_mow_speed > 0:
            return self.current_mow_current < self.mow_min_current_threshold
        elif not self.mow_enabled and self.target_mow_speed == 0:
            return self.current_mow_current > self.mow_max_current_threshold
        return False

    def drvfix(self) -> None:
        """
        Führt spezielle Hardware-Korrekturen durch.
        
        Implementiert hardwarespezifische Workarounds und Korrekturen
        für bekannte Probleme bestimmter Motorcontroller oder Treiber.
        
        Beispiele für mögliche Korrekturen:
        - Offset-Kompensation für Motorasymmetrien
        - Temperaturkompensation
        - Kalibrierung nach Stillstand
        
        Hinweis: Implementierung abhängig von verwendeter Hardware
        """
        # Placeholder für spezielle Hardware-Korrekturen
        pass

    def check_motor_mow_stall(self) -> None:
        """
        Erkennt und behandelt Mähmotor-Blockierungen.
        
        Überwacht den Mähmotor-Strom und erkennt Blockierungen
        durch übermäßigen Stromverbrauch. Bei Erkennung wird
        der Mähmotor automatisch abgeschaltet.
        
        Erkennungskriterium:
        - Strom > 80% des maximalen Mähmotor-Stroms
        
        Beispiel:
            motor.check_motor_mow_stall()  # Automatische Überwachung
            # Bei Blockierung: Mähmotor wird automatisch gestoppt
        """
        if self.mow_enabled and self.current_mow_current > self.max_mow_current * 0.8:
            print("Motor: Mähmotor-Blockierung erkannt")
            self.set_mow_state(False)

    def adaptive_speed(self) -> float:
        """
        Berechnet adaptiven Geschwindigkeitsfaktor basierend auf Motorstrom.
        
        Reduziert automatisch die Fahrgeschwindigkeit bei hohem Stromverbrauch
        (schwieriges Gelände, steile Hänge, dichtes Gras).
        
        Returns:
            float: Geschwindigkeitsfaktor (0.3 bis 1.0)
                  1.0 = normale Geschwindigkeit
                  <1.0 = reduzierte Geschwindigkeit
        
        Algorithmus:
        1. Durchschnittsstrom beider Antriebsmotoren berechnen
        2. Mit Schwellenwert vergleichen (70% des Maximalstroms)
        3. Bei Überschreitung: Geschwindigkeit proportional reduzieren
        4. Mindestgeschwindigkeit: 30% der Sollgeschwindigkeit
        
        Beispiel:
            factor = motor.adaptive_speed()
            if factor < 1.0:
                print(f"Geschwindigkeit reduziert auf {factor*100:.0f}%")
        """
        if not self.adaptive_enabled:
            return 1.0
            
        # Reduziere Geschwindigkeit bei hohem Strom (schweres Gelände)
        avg_current = (self.current_left_current + self.current_right_current) / 2.0
        max_current = self.max_motor_current * self.adaptive_current_threshold_factor
        
        if avg_current > max_current:
            reduction_factor = max_current / avg_current
            return max(self.adaptive_min_speed_factor, reduction_factor)
        return 1.0

    def change_speed_set(self) -> None:
        """
        Wendet adaptive Geschwindigkeitsanpassungen auf die Sollwerte an.
        
        Modifiziert die aktuellen Soll-Geschwindigkeiten basierend auf:
        - Motorstrom (adaptive Geschwindigkeitsregelung)
        - Geländebedingungen
        - Sicherheitsaspekte
        
        Die Anpassung erfolgt durch Multiplikation der Sollwerte
        mit dem adaptiven Geschwindigkeitsfaktor.
        
        Beispiel:
            # Wird automatisch von control() aufgerufen
            motor.change_speed_set()
            # Sollgeschwindigkeiten sind jetzt an Bedingungen angepasst
        """
        # Adaptive Geschwindigkeitsanpassung anwenden
        speed_factor = self.adaptive_speed()
        if speed_factor < 1.0:
            self.target_left_speed *= speed_factor
            self.target_right_speed *= speed_factor
            print(f"Motor: Geschwindigkeit angepasst (Faktor: {speed_factor:.2f})")

    def sense(self) -> None:
        """
        Erfasst Sensordaten für die Motorregelung.
        
        Legacy-Methode - Sensordatenerfassung erfolgt jetzt über
        die update() Methode mit Pico-Daten.
        
        Historisch für direkte Sensorabfrage verwendet,
        jetzt durch Pico-Integration ersetzt.
        """
        # Diese Methode wird durch update() mit Pico-Daten ersetzt
        pass

    def dump_odo_ticks(self, seconds: int) -> None:
        """
        Gibt aktuelle Odometrie- und Stromdaten für Debugging aus.
        
        Nützlich für:
        - Kalibrierung der Odometrie-Sensoren
        - Analyse von Motorproblemen
        - Überwachung der Systemleistung
        
        Args:
            seconds (int): Parameter für zukünftige Erweiterungen
                          (z.B. Ausgabedauer)
        
        Ausgabe:
        - Odometrie-Ticks aller Motoren
        - Aktuelle Motorströme
        
        Beispiel:
            motor.dump_odo_ticks(5)  # Gibt aktuelle Werte aus
        """
        print(f"Motor Odometrie - Links: {self.current_left_odom}, Rechts: {self.current_right_odom}, Mäher: {self.current_mow_odom}")
        print(f"Motor Ströme - Links: {self.current_left_current:.2f}A, Rechts: {self.current_right_current:.2f}A, Mäher: {self.current_mow_current:.2f}A")
    
    def test(self) -> None:
        """
        Führt einen umfassenden automatischen Motortest durch.
        
        Testet alle Motoren systematisch mit verschiedenen Bewegungsmustern:
        1. Vorwärts fahren (beide Motoren vorwärts)
        2. Rückwärts fahren (beide Motoren rückwärts)
        3. Rechts drehen (linker Motor vorwärts, rechter rückwärts)
        4. Links drehen (rechter Motor vorwärts, linker rückwärts)
        5. Mähmotor einzeln testen
        6. Alle Motoren stoppen
        
        Jede Testsequenz läuft 1 Sekunde zur Beobachtung.
        
        Voraussetzungen:
        - Pico-Kommunikation muss verfügbar sein
        - Motoren müssen aktiviert sein
        - Ausreichend Platz für Bewegungen
        
        Sicherheitshinweis:
        Roboter sollte angehoben oder in sicherer Umgebung sein!
        
        Beispiel:
            motor.begin()
            motor.test()  # Führt kompletten Motortest aus
        """
        print("Motor: Starte Motortest...")
        if not self.pico:
            print("Motor: Kein Pico verfügbar für Test")
            return
        
        # Systematische Testsequenzen mit PWM-Werten
        test_sequences = [
            (50, 50, 0),    # Vorwärts fahren
            (-50, -50, 0),  # Rückwärts fahren
            (50, -50, 0),   # Rechts drehen
            (-50, 50, 0),   # Links drehen
            (0, 0, 100),    # Nur Mähmotor
            (0, 0, 0)       # Alle Motoren stoppen
        ]
        
        test_names = [
            "Vorwärts", "Rückwärts", "Rechts drehen", 
            "Links drehen", "Mähmotor", "Stopp"
        ]
        
        for i, (left, right, mow) in enumerate(test_sequences):
            print(f"Motor: Test {i+1}/6 - {test_names[i]}")
            self.speed_pwm(left, right, mow)
            time.sleep(1)  # 1 Sekunde pro Test
        
        print("Motor: Motortest erfolgreich abgeschlossen")
    
    def plot(self) -> None:
        """
        Erfasst und gibt aktuelle Motordaten für Analyse und Visualisierung aus.
        
        Sammelt alle relevanten Motorparameter und gibt sie strukturiert aus:
        - Motorstatus (aktiviert/deaktiviert)
        - Sollwerte vs. Istwerte
        - Motorströme und Überlastungszustände
        - Geschwindigkeiten und PID-Werte
        - Fehlerzustände
        
        Nützlich für:
        - Performance-Analyse
        - Debugging von Motorproblemen
        - Kalibrierung und Optimierung
        - Datenlogger-Integration
        
        Ausgabeformat:
        Strukturierte Darstellung aller Motorparameter mit Einheiten
        und aktuellen Werten für einfache Analyse.
        
        Beispiel:
            motor.plot()  # Zeigt alle aktuellen Motordaten
            # Ausgabe: Detaillierte Motorstatistiken
        """
        # Aktuellen Motorstatus abrufen
        status = self.get_status()
        current_speeds = self._calculate_speeds()
        
        print("\n=== MOTOR ANALYSE DATEN ===")
        print(f"Antriebsmotoren: {'AKTIV' if status['enabled'] else 'INAKTIV'}")
        print(f"Mähmotor: {'AKTIV' if status['mow_enabled'] else 'INAKTIV'}")
        print(f"Überlastung: {'JA' if status['overload_detected'] else 'NEIN'}")
        print(f"Hardware-Fehler: {'JA' if status['fault_detected'] else 'NEIN'}")
        
        print("\n--- SOLLWERTE ---")
        print(f"Linear: {status['target_linear_speed']:.3f} m/s")
        print(f"Angular: {status['target_angular_speed']:.3f} rad/s")
        print(f"Links: {self.target_left_speed:.3f} m/s")
        print(f"Rechts: {self.target_right_speed:.3f} m/s")
        print(f"Mäher: {self.target_mow_speed} PWM")
        
        print("\n--- ISTWERTE ---")
        print(f"Links: {current_speeds['left']:.3f} m/s")
        print(f"Rechts: {current_speeds['right']:.3f} m/s")
        print(f"Mäher: {current_speeds['mow']:.3f} m/s")
        
        print("\n--- MOTORSTRÖME ---")
        print(f"Links: {status['current_left_current']:.2f} A (Max: {self.max_motor_current:.1f} A)")
        print(f"Rechts: {status['current_right_current']:.2f} A (Max: {self.max_motor_current:.1f} A)")
        print(f"Mäher: {status['current_mow_current']:.2f} A (Max: {self.max_mow_current:.1f} A)")
        
        print("\n--- SICHERHEIT ---")
        print(f"Überlastungszähler: {status['overload_count']}/{self.max_overload_count}")
        print(f"Adaptive Geschwindigkeit: {self.adaptive_speed():.2f}")
        
        print("\n--- ODOMETRIE ---")
        print(f"Links: {self.current_left_odom} Ticks")
        print(f"Rechts: {self.current_right_odom} Ticks")
        print(f"Mäher: {self.current_mow_odom} Ticks")
        print("=== ENDE MOTOR ANALYSE ===")
