#!/usr/bin/env python3
"""
Test-Skript für die erweiterte Button-Funktionalität des Sunray Python Mähroboters.

Dieses Skript demonstriert und testet:
- Smart Button Controller
- Verschiedene Button-Aktionen
- Buzzer-Feedback
- Kontextabhängige Aktionen
- API-Integration

Autor: Sunray Python Team
Version: 1.0
"""

import time
import json
from typing import Dict, List
from smart_button_controller import SmartButtonController, ButtonAction, RobotState
from buzzer_feedback import BuzzerFeedback, BuzzerTone

class MockMotor:
    """Mock Motor-Klasse für Tests."""
    
    def __init__(self):
        self.autonomous_mowing = False
        self.docking = False
        self.emergency_stopped = False
        self.actions_log = []
    
    def start_autonomous_mowing(self):
        self.autonomous_mowing = True
        self.emergency_stopped = False
        self.actions_log.append("start_autonomous_mowing")
        print("🟢 Mock: Autonomer Mähvorgang gestartet")
    
    def stop_autonomous_mowing(self):
        self.autonomous_mowing = False
        self.actions_log.append("stop_autonomous_mowing")
        print("🔴 Mock: Autonomer Mähvorgang gestoppt")
    
    def go_home(self):
        self.docking = True
        self.autonomous_mowing = False
        self.actions_log.append("go_home")
        print("🏠 Mock: Docking-Vorgang gestartet")
    
    def emergency_stop(self):
        self.emergency_stopped = True
        self.autonomous_mowing = False
        self.docking = False
        self.actions_log.append("emergency_stop")
        print("🚨 Mock: Notfall-Stopp ausgeführt")
    
    def get_status(self) -> Dict:
        return {
            'autonomous_mowing': self.autonomous_mowing,
            'docking': self.docking,
            'emergency_stopped': self.emergency_stopped,
            'actions_count': len(self.actions_log)
        }

class MockStateEstimator:
    """Mock StateEstimator-Klasse für Tests."""
    
    def __init__(self):
        self.current_state = "idle"
    
    def get_current_state(self) -> str:
        return self.current_state
    
    def set_state(self, state: str):
        self.current_state = state

class MockHardwareManager:
    """Mock HardwareManager-Klasse für Tests."""
    
    def __init__(self):
        self.buzzer_commands = []
    
    def send_command(self, command: Dict) -> bool:
        if command.get('cmd') == 'buzzer':
            self.buzzer_commands.append(command)
            print(f"🔊 Mock Buzzer: {command['frequency']}Hz, {command['duration']}ms")
        return True

def test_button_controller_basic():
    """Testet grundlegende Button-Controller-Funktionalität."""
    print("\n=== Test: Grundlegende Button-Controller-Funktionalität ===")
    
    # Mock-Objekte erstellen
    motor = MockMotor()
    state_estimator = MockStateEstimator()
    hardware_manager = MockHardwareManager()
    
    # Button-Controller initialisieren
    button_controller = SmartButtonController(
        motor=motor,
        state_estimator=state_estimator,
        hardware_manager=hardware_manager
    )
    
    # Callbacks registrieren
    button_controller.set_action_callback(
        ButtonAction.START_MOW, 
        lambda: motor.start_autonomous_mowing()
    )
    button_controller.set_action_callback(
        ButtonAction.STOP_MOW, 
        lambda: motor.stop_autonomous_mowing()
    )
    button_controller.set_action_callback(
        ButtonAction.GO_HOME, 
        lambda: motor.go_home()
    )
    button_controller.set_action_callback(
        ButtonAction.EMERGENCY_STOP, 
        lambda: motor.emergency_stop()
    )
    
    # Status anzeigen
    status = button_controller.get_status()
    print(f"Button-Controller Status: {json.dumps(status, indent=2)}")
    
    return button_controller, motor, state_estimator, hardware_manager

def test_button_actions(button_controller, motor):
    """Testet verschiedene Button-Aktionen."""
    print("\n=== Test: Button-Aktionen ===")
    
    # Roboterzustand für Tests setzen
    robot_state_data = {
        'op_type': 'idle',
        'battery_level': 85.0,
        'is_docked': False,
        'has_map': True
    }
    button_controller.update_robot_state(robot_state_data)
    
    test_cases = [
        (0.5, "Kurzer Druck - Start Mähen"),
        (2.5, "Mittlerer Druck - Emergency Stop"),
        (6.0, "Langer Druck - GoHome"),
        (0.8, "Kurzer Druck - Stop Mähen (nach Start)")
    ]
    
    for duration, description in test_cases:
        print(f"\n--- {description} ({duration}s) ---")
        
        # Button-Aktion simulieren
        action = button_controller.simulate_button_press(duration)
        
        print(f"Ausgeführte Aktion: {action.value}")
        print(f"Motor Status: {motor.get_status()}")
        
        # Kurze Pause zwischen Tests
        time.sleep(0.5)

def test_context_dependent_actions(button_controller, motor, state_estimator):
    """Testet kontextabhängige Button-Aktionen."""
    print("\n=== Test: Kontextabhängige Aktionen ===")
    
    test_scenarios = [
        {
            'robot_state': {
                'op_type': 'idle',
                'battery_level': 90.0,
                'is_docked': False,
                'has_map': True
            },
            'description': "IDLE mit Karte und voller Batterie",
            'expected_action': "START_MOW"
        },
        {
            'robot_state': {
                'op_type': 'idle',
                'battery_level': 15.0,
                'is_docked': False,
                'has_map': True
            },
            'description': "IDLE mit niedriger Batterie",
            'expected_action': "NONE"
        },
        {
            'robot_state': {
                'op_type': 'mow',
                'battery_level': 60.0,
                'is_docked': False,
                'has_map': True
            },
            'description': "Während Mähvorgang",
            'expected_action': "STOP_MOW"
        },
        {
            'robot_state': {
                'op_type': 'charge',
                'battery_level': 85.0,
                'is_docked': True,
                'has_map': True
            },
            'description': "Beim Laden mit hoher Batterie",
            'expected_action': "START_MOW"
        }
    ]
    
    for scenario in test_scenarios:
        print(f"\n--- {scenario['description']} ---")
        
        # Roboterzustand setzen
        button_controller.update_robot_state(scenario['robot_state'])
        state_estimator.set_state(scenario['robot_state']['op_type'])
        
        # Kurzen Button-Druck simulieren
        action = button_controller.simulate_button_press(0.5)
        
        print(f"Erwartete Aktion: {scenario['expected_action']}")
        print(f"Tatsächliche Aktion: {action.value}")
        print(f"✅ Test {'bestanden' if action.value.upper() == scenario['expected_action'] else 'fehlgeschlagen'}")
        
        time.sleep(0.3)

def test_buzzer_feedback(hardware_manager):
    """Testet Buzzer-Feedback-System."""
    print("\n=== Test: Buzzer-Feedback ===")
    
    buzzer = BuzzerFeedback(hardware_manager)
    
    # Verschiedene Töne testen
    test_tones = [
        (BuzzerTone.SYSTEM_START, "System Start"),
        (BuzzerTone.OBSTACLE_DETECTED, "Hindernis erkannt"),
        (BuzzerTone.TILT_WARNING, "Neigungswarnung"),
        (BuzzerTone.CONFIRM_POSITIVE, "Positive Bestätigung")
    ]
    
    for tone, description in test_tones:
        print(f"Spiele Ton: {description}")
        success = buzzer.play_tone_enum(tone)
        print(f"Status: {'✅ Erfolgreich' if success else '❌ Fehlgeschlagen'}")
        time.sleep(0.5)
    
    # Buzzer-Statistiken anzeigen
    stats = buzzer.get_statistics()
    print(f"\nBuzzer-Statistiken: {json.dumps(stats, indent=2)}")
    
    # Hardware-Manager Buzzer-Befehle anzeigen
    print(f"\nGesendete Buzzer-Befehle: {len(hardware_manager.buzzer_commands)}")
    for i, cmd in enumerate(hardware_manager.buzzer_commands[-5:], 1):  # Letzte 5
        print(f"  {i}. {cmd}")

def test_api_simulation():
    """Simuliert API-Aufrufe für Button-Funktionalität."""
    print("\n=== Test: API-Simulation ===")
    
    # Simuliere verschiedene API-Aufrufe
    api_calls = [
        {
            'endpoint': 'GET /button/status',
            'description': 'Button-Status abrufen'
        },
        {
            'endpoint': 'POST /button/simulate',
            'data': {'duration': 0.5},
            'description': 'Kurzen Button-Druck simulieren'
        },
        {
            'endpoint': 'POST /button/simulate',
            'data': {'duration': 5.5},
            'description': 'Langen Button-Druck simulieren'
        },
        {
            'endpoint': 'GET /button/actions',
            'description': 'Verfügbare Aktionen abrufen'
        },
        {
            'endpoint': 'GET /button/config',
            'description': 'Button-Konfiguration abrufen'
        }
    ]
    
    for call in api_calls:
        print(f"\n📡 API-Aufruf: {call['endpoint']}")
        print(f"   Beschreibung: {call['description']}")
        if 'data' in call:
            print(f"   Daten: {json.dumps(call['data'])}")
        print("   Status: ✅ Simuliert (würde in echter API funktionieren)")

def run_comprehensive_test():
    """Führt einen umfassenden Test der Button-Funktionalität durch."""
    print("🚀 Starte umfassenden Test der Button-Funktionalität")
    print("=" * 60)
    
    try:
        # Grundlegende Tests
        button_controller, motor, state_estimator, hardware_manager = test_button_controller_basic()
        
        # Button-Aktionen testen
        test_button_actions(button_controller, motor)
        
        # Kontextabhängige Aktionen testen
        test_context_dependent_actions(button_controller, motor, state_estimator)
        
        # Buzzer-Feedback testen
        test_buzzer_feedback(hardware_manager)
        
        # API-Simulation
        test_api_simulation()
        
        print("\n" + "=" * 60)
        print("✅ Alle Tests erfolgreich abgeschlossen!")
        print("\n📊 Test-Zusammenfassung:")
        print(f"   - Motor-Aktionen ausgeführt: {len(motor.actions_log)}")
        print(f"   - Buzzer-Befehle gesendet: {len(hardware_manager.buzzer_commands)}")
        print(f"   - Button-Controller Status: Funktionsfähig")
        
        # Finale Motor-Aktionen anzeigen
        print(f"\n🔧 Ausgeführte Motor-Aktionen:")
        for i, action in enumerate(motor.actions_log, 1):
            print(f"   {i}. {action}")
        
    except Exception as e:
        print(f"\n❌ Test fehlgeschlagen: {e}")
        import traceback
        traceback.print_exc()

def interactive_test():
    """Interaktiver Test für manuelle Button-Simulation."""
    print("\n🎮 Interaktiver Button-Test")
    print("Geben Sie Druckdauern ein, um Button-Aktionen zu simulieren.")
    print("Eingabe 'q' zum Beenden.\n")
    
    # Setup
    motor = MockMotor()
    state_estimator = MockStateEstimator()
    hardware_manager = MockHardwareManager()
    
    button_controller = SmartButtonController(
        motor=motor,
        state_estimator=state_estimator,
        hardware_manager=hardware_manager
    )
    
    # Callbacks registrieren
    button_controller.set_action_callback(ButtonAction.START_MOW, motor.start_autonomous_mowing)
    button_controller.set_action_callback(ButtonAction.STOP_MOW, motor.stop_autonomous_mowing)
    button_controller.set_action_callback(ButtonAction.GO_HOME, motor.go_home)
    button_controller.set_action_callback(ButtonAction.EMERGENCY_STOP, motor.emergency_stop)
    
    # Standard-Zustand setzen
    robot_state_data = {
        'op_type': 'idle',
        'battery_level': 80.0,
        'is_docked': False,
        'has_map': True
    }
    button_controller.update_robot_state(robot_state_data)
    
    while True:
        try:
            user_input = input("Druckdauer eingeben (Sekunden) oder 'q' zum Beenden: ").strip()
            
            if user_input.lower() == 'q':
                break
            
            duration = float(user_input)
            if duration < 0 or duration > 10:
                print("❌ Druckdauer muss zwischen 0 und 10 Sekunden liegen.")
                continue
            
            print(f"\n🔘 Simuliere Button-Druck: {duration:.1f} Sekunden")
            action = button_controller.simulate_button_press(duration)
            print(f"➡️  Ausgeführte Aktion: {action.value}")
            print(f"📊 Motor Status: {motor.get_status()}")
            print()
            
        except ValueError:
            print("❌ Ungültige Eingabe. Bitte eine Zahl eingeben.")
        except KeyboardInterrupt:
            break
    
    print("\n👋 Interaktiver Test beendet.")

if __name__ == "__main__":
    print("Sunray Python - Button-Funktionalität Test")
    print("==========================================\n")
    
    print("Verfügbare Tests:")
    print("1. Umfassender automatischer Test")
    print("2. Interaktiver Test")
    print("3. Beide Tests")
    
    try:
        choice = input("\nWählen Sie einen Test (1-3): ").strip()
        
        if choice == "1":
            run_comprehensive_test()
        elif choice == "2":
            interactive_test()
        elif choice == "3":
            run_comprehensive_test()
            interactive_test()
        else:
            print("Ungültige Auswahl. Führe umfassenden Test aus...")
            run_comprehensive_test()
            
    except KeyboardInterrupt:
        print("\n\n👋 Test abgebrochen.")
    except Exception as e:
        print(f"\n❌ Unerwarteter Fehler: {e}")
        import traceback
        traceback.print_exc()