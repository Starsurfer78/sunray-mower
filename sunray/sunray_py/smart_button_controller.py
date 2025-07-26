#!/usr/bin/env python3
"""
Intelligente Button-Steuerung für Sunray Python Mähroboter.

Dieses Modul implementiert eine erweiterte Button-Funktionalität:
- Kurzer Druck: Start/Stop Mähvorgang
- Langer Druck (5s): GoHome/Docking-Vorgang
- Kontextabhängige Aktionen basierend auf aktuellem Zustand
- Buzzer-Feedback für Benutzerinteraktion

Autor: Sunray Python Team
Version: 1.0
"""

import time
from typing import Dict, Optional, Callable
from enum import Enum
from buzzer_feedback import BuzzerFeedback, BuzzerTone, get_buzzer_feedback

class ButtonAction(Enum):
    """Verfügbare Button-Aktionen."""
    START_MOW = "start_mow"
    STOP_MOW = "stop_mow"
    RESUME_MOW = "resume_mow"
    GO_HOME = "go_home"
    EMERGENCY_STOP = "emergency_stop"
    NONE = "none"

class RobotState(Enum):
    """Roboter-Betriebszustände."""
    IDLE = "idle"
    MOWING = "mow"
    DOCKING = "dock"
    CHARGING = "charge"
    ERROR = "error"
    ESCAPE = "escape"
    GPS_RECOVERY = "gps_recovery"

class SmartButtonController:
    """
    Intelligente Button-Steuerung mit kontextabhängigen Aktionen.
    
    Diese Klasse verwaltet die Button-Eingaben und führt entsprechende
    Aktionen basierend auf:
    - Druckdauer (kurz/lang)
    - Aktuellem Roboterzustand
    - Verfügbaren Karten und Zonen
    - Batteriezustand
    
    Beispiel:
        button_controller = SmartButtonController(motor, state_estimator)
        button_controller.set_action_callback(ButtonAction.START_MOW, start_mowing_func)
        
        # In der Hauptschleife
        button_controller.update(pico_data)
    """
    
    def __init__(self, motor=None, state_estimator=None, hardware_manager=None):
        """
        Initialisiert den Smart Button Controller.
        
        Args:
            motor: Motor-Instanz für Bewegungssteuerung
            state_estimator: StateEstimator für aktuellen Roboterzustand
            hardware_manager: HardwareManager für Buzzer-Kommunikation
        """
        self.motor = motor
        self.state_estimator = state_estimator
        self.hardware_manager = hardware_manager
        
        # Button-Zustand
        self.button_pressed = False
        self.button_press_start_time = 0
        self.last_button_state = 1  # Pull-up: 1 = nicht gedrückt
        self.button_debounce_time = 0.05  # 50ms Entprellung
        self.last_debounce_time = 0
        
        # Timing-Konfiguration
        self.short_press_max_duration = 1.0  # Sekunden
        self.long_press_duration = 5.0  # Sekunden für GoHome
        self.beep_interval = 1.0  # Sekunden zwischen Pieptönen
        self.last_beep_time = 0
        self.beep_count = 0
        
        # Buzzer-System
        self.buzzer_feedback = get_buzzer_feedback(hardware_manager)
        
        # Action Callbacks
        self.action_callbacks = {}
        
        # Zustandsverfolgung
        self.current_robot_state = RobotState.IDLE
        self.has_map_loaded = False
        self.battery_level = 100.0
        self.is_docked = False
        
        print("Smart Button Controller initialisiert")
    
    def set_action_callback(self, action: ButtonAction, callback: Callable):
        """
        Registriert eine Callback-Funktion für eine bestimmte Aktion.
        
        Args:
            action (ButtonAction): Die Aktion, für die der Callback registriert wird
            callback (Callable): Die Funktion, die bei der Aktion aufgerufen wird
        
        Beispiel:
            button_controller.set_action_callback(
                ButtonAction.START_MOW, 
                lambda: motor.start_autonomous_mowing()
            )
        """
        self.action_callbacks[action] = callback
        print(f"Callback für {action.value} registriert")
    
    def update_robot_state(self, robot_state_data: Dict):
        """
        Aktualisiert den aktuellen Roboterzustand.
        
        Args:
            robot_state_data (Dict): Zustandsdaten mit Schlüsseln:
                                   - op_type: Aktueller Operationstyp
                                   - battery_level: Batteriestand in %
                                   - is_docked: Ob Roboter gedockt ist
                                   - has_map: Ob Karte geladen ist
        """
        # Roboterzustand aktualisieren
        op_type = robot_state_data.get('op_type', 'idle')
        try:
            self.current_robot_state = RobotState(op_type)
        except ValueError:
            self.current_robot_state = RobotState.IDLE
        
        # Weitere Zustandsinformationen
        self.battery_level = robot_state_data.get('battery_level', 100.0)
        self.is_docked = robot_state_data.get('is_docked', False)
        self.has_map_loaded = robot_state_data.get('has_map', False)
    
    def update(self, pico_data: Dict) -> Optional[ButtonAction]:
        """
        Verarbeitet Button-Eingaben und führt entsprechende Aktionen aus.
        
        Args:
            pico_data (Dict): Sensordaten vom Pico mit 'stopButton' Schlüssel
        
        Returns:
            Optional[ButtonAction]: Die ausgeführte Aktion oder None
        
        Beispiel:
            action = button_controller.update(pico_data)
            if action:
                print(f"Button-Aktion ausgeführt: {action.value}")
        """
        if not pico_data or 'stopButton' not in pico_data:
            return None
        
        current_time = time.time()
        button_state = pico_data['stopButton']
        
        # Entprellung
        if current_time - self.last_debounce_time < self.button_debounce_time:
            return None
        
        # Button-Zustandsänderung erkennen
        if button_state != self.last_button_state:
            self.last_debounce_time = current_time
            
            # Button gedrückt (1 -> 0, da Pull-up)
            if self.last_button_state == 1 and button_state == 0:
                self.button_pressed = True
                self.button_press_start_time = current_time
                self.last_beep_time = current_time
                self.beep_count = 0
                
                # Sofortiges Feedback
                self.buzzer_feedback.play_tone(BuzzerTone.BUTTON_PRESS)
                print("Button gedrückt - Aktion wird bestimmt...")
            
            # Button losgelassen (0 -> 1)
            elif self.last_button_state == 0 and button_state == 1:
                if self.button_pressed:
                    press_duration = current_time - self.button_press_start_time
                    action = self._determine_action(press_duration)
                    self.button_pressed = False
                    return self._execute_action(action)
            
            self.last_button_state = button_state
        
        # Während Button gedrückt ist - Pieptöne für lange Drücke
        if self.button_pressed and button_state == 0:
            press_duration = current_time - self.button_press_start_time
            
            # Pieptöne alle Sekunde während langem Druck
            if (current_time - self.last_beep_time >= self.beep_interval and 
                press_duration >= 1.0):
                self.beep_count += 1
                self.last_beep_time = current_time
                
                if self.beep_count < 5:  # Bis zu 5 Pieptöne
                    self.buzzer_feedback.play_tone(BuzzerTone.BUTTON_LONG_PRESS)
                    print(f"Langer Druck erkannt - {self.beep_count}/5 Sekunden")
                elif self.beep_count == 5:
                    # GoHome wird aktiviert
                    self.buzzer_feedback.play_tone(BuzzerTone.GO_HOME_ACTIVATED)
                    print("GoHome-Modus aktiviert - Button loslassen zum Bestätigen")
        
        return None
    
    def _determine_action(self, press_duration: float) -> ButtonAction:
        """
        Bestimmt die auszuführende Aktion basierend auf Druckdauer und Zustand.
        
        Args:
            press_duration (float): Dauer des Button-Drucks in Sekunden
        
        Returns:
            ButtonAction: Die zu ausführende Aktion
        """
        # Langer Druck (≥5 Sekunden) = GoHome
        if press_duration >= self.long_press_duration:
            return ButtonAction.GO_HOME
        
        # Kurzer Druck - kontextabhängig
        if press_duration <= self.short_press_max_duration:
            return self._determine_short_press_action()
        
        # Mittlerer Druck (1-5 Sekunden) = Emergency Stop
        return ButtonAction.EMERGENCY_STOP
    
    def _determine_short_press_action(self) -> ButtonAction:
        """
        Bestimmt die Aktion für kurzen Button-Druck basierend auf aktuellem Zustand.
        
        Returns:
            ButtonAction: Die kontextabhängige Aktion
        """
        # Im IDLE-Zustand
        if self.current_robot_state == RobotState.IDLE:
            if self.has_map_loaded and self.battery_level > 20.0:
                return ButtonAction.START_MOW
            else:
                print("Kann nicht starten: Keine Karte geladen oder Batterie zu niedrig")
                return ButtonAction.NONE
        
        # Während Mähvorgang
        elif self.current_robot_state == RobotState.MOWING:
            return ButtonAction.STOP_MOW
        
        # In anderen Zuständen
        elif self.current_robot_state in [RobotState.ESCAPE, RobotState.GPS_RECOVERY]:
            return ButtonAction.STOP_MOW  # Stoppe aktuelle Operation
        
        # In Dock/Charge-Zustand
        elif self.current_robot_state in [RobotState.DOCKING, RobotState.CHARGING]:
            if self.battery_level > 80.0 and self.has_map_loaded:
                return ButtonAction.START_MOW  # Starte von Dock aus
            else:
                return ButtonAction.NONE
        
        # Fehler-Zustand
        elif self.current_robot_state == RobotState.ERROR:
            return ButtonAction.EMERGENCY_STOP  # Reset versuchen
        
        return ButtonAction.NONE
    
    def _execute_action(self, action: ButtonAction) -> ButtonAction:
        """
        Führt die bestimmte Aktion aus.
        
        Args:
            action (ButtonAction): Die auszuführende Aktion
        
        Returns:
            ButtonAction: Die ausgeführte Aktion
        """
        if action == ButtonAction.NONE:
            self.buzzer_feedback.play_tone(BuzzerTone.ERROR)
            return action
        
        print(f"Führe Button-Aktion aus: {action.value}")
        
        # Buzzer-Feedback für verschiedene Aktionen
        if action == ButtonAction.START_MOW:
            self.buzzer_feedback.play_tone(BuzzerTone.MOWING_STARTED)
        elif action == ButtonAction.STOP_MOW:
            self.buzzer_feedback.play_tone(BuzzerTone.MOWING_STOPPED)
        elif action == ButtonAction.GO_HOME:
            self.buzzer_feedback.play_tone(BuzzerTone.GO_HOME_ACTIVATED)
        elif action == ButtonAction.EMERGENCY_STOP:
            self.buzzer_feedback.play_tone(BuzzerTone.EMERGENCY_STOP)
        
        # Callback ausführen falls registriert
        if action in self.action_callbacks:
            try:
                self.action_callbacks[action]()
                print(f"Callback für {action.value} erfolgreich ausgeführt")
            except Exception as e:
                print(f"Fehler beim Ausführen des Callbacks für {action.value}: {e}")
                self.buzzer_feedback.play_tone(BuzzerTone.ERROR)
        else:
            print(f"Kein Callback für {action.value} registriert")
        
        return action
    
    def get_status(self) -> Dict:
        """
        Gibt den aktuellen Status des Button-Controllers zurück.
        
        Returns:
            Dict: Status-Informationen
        """
        return {
            'button_pressed': self.button_pressed,
            'current_robot_state': self.current_robot_state.value,
            'has_map_loaded': self.has_map_loaded,
            'battery_level': self.battery_level,
            'is_docked': self.is_docked,
            'registered_callbacks': list(self.action_callbacks.keys())
        }
    
    def simulate_button_press(self, duration: float) -> ButtonAction:
        """
        Simuliert einen Button-Druck für Tests.
        
        Args:
            duration (float): Simulierte Druckdauer in Sekunden
        
        Returns:
            ButtonAction: Die simulierte Aktion
        """
        action = self._determine_action(duration)
        print(f"Simuliere Button-Druck ({duration:.1f}s) -> {action.value}")
        return self._execute_action(action)

# Globale Instanz für einfachen Zugriff
_smart_button_controller = None

def get_smart_button_controller(motor=None, state_estimator=None, hardware_manager=None):
    """
    Gibt die globale SmartButtonController-Instanz zurück.
    
    Args:
        motor: Motor-Instanz (nur beim ersten Aufruf)
        state_estimator: StateEstimator-Instanz (nur beim ersten Aufruf)
        hardware_manager: HardwareManager-Instanz (nur beim ersten Aufruf)
    
    Returns:
        SmartButtonController: Die globale Instanz
    """
    global _smart_button_controller
    if _smart_button_controller is None:
        _smart_button_controller = SmartButtonController(motor, state_estimator, hardware_manager)
    return _smart_button_controller

def reset_smart_button_controller():
    """
    Setzt die globale SmartButtonController-Instanz zurück.
    Nützlich für Tests.
    """
    global _smart_button_controller
    _smart_button_controller = None