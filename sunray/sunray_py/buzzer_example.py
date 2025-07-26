#!/usr/bin/env python3
"""
Buzzer Feedback Beispiel für Sunray Enhanced Navigation System

Dieses Skript demonstriert die Verwendung des Buzzer-Feedback-Systems
für verschiedene Ereignisse und Operationen.
"""

import time
from buzzer_feedback import BuzzerFeedback, BuzzerTone, get_buzzer_feedback
from events import EventCode

class MockHardwareManager:
    """Mock Hardware Manager für Buzzer-Tests."""
    
    def send_buzzer_command(self, frequency, duration):
        """Simuliert Buzzer-Befehl."""
        print(f"🔊 BUZZER: {frequency}Hz für {duration}ms")
        return True

def demo_system_events():
    """Demonstriert System-Ereignis Buzzer-Feedback."""
    print("\n=== System Events Demo ===")
    
    # Hardware Manager initialisieren
    hardware_manager = MockHardwareManager()
    buzzer = BuzzerFeedback(hardware_manager)
    
    # System-Start
    print("System startet...")
    buzzer.handle_event(EventCode.SYSTEM_STARTED)
    time.sleep(1)
    
    # WiFi-Verbindung
    print("WiFi verbindet...")
    buzzer.handle_event(EventCode.WIFI_CONNECTED)
    time.sleep(1)
    
    # GPS-Verbindung
    print("GPS verbindet...")
    buzzer.handle_event(EventCode.GPS_CONNECTED)
    time.sleep(1)
    
    # System-Shutdown
    print("System fährt herunter...")
    buzzer.handle_event(EventCode.SYSTEM_SHUTTING_DOWN)
    time.sleep(1)

def demo_navigation_events():
    """Demonstriert Navigations-Ereignis Buzzer-Feedback."""
    print("\n=== Navigation Events Demo ===")
    
    hardware_manager = MockHardwareManager()
    buzzer = BuzzerFeedback(hardware_manager)
    
    # Hindernis erkannt
    print("Hindernis erkannt!")
    buzzer.handle_event(EventCode.OBSTACLE_DETECTED)
    time.sleep(1)
    
    # Neigungswarnung
    print("Neigungswarnung!")
    buzzer.handle_event(EventCode.TILT_WARNING)
    time.sleep(1)
    
    # Mähen gestartet
    print("Mähen startet...")
    buzzer.play_tone(BuzzerTone.NAVIGATION_START)
    time.sleep(1)
    
    # Mähen beendet
    print("Mähen beendet.")
    buzzer.play_tone(BuzzerTone.NAVIGATION_COMPLETE)
    time.sleep(1)

def demo_enhanced_system_events():
    """Demonstriert Enhanced System Buzzer-Feedback."""
    print("\n=== Enhanced System Events Demo ===")
    
    hardware_manager = MockHardwareManager()
    buzzer = BuzzerFeedback(hardware_manager)
    
    # Enhanced Escape startet
    print("Enhanced Escape startet...")
    buzzer.play_tone(BuzzerTone.ENHANCED_ESCAPE_START)
    time.sleep(1)
    
    # Enhanced Escape erfolgreich
    print("Enhanced Escape erfolgreich!")
    buzzer.play_tone(BuzzerTone.ENHANCED_ESCAPE_SUCCESS)
    time.sleep(1)
    
    # Enhanced Escape fehlgeschlagen
    print("Enhanced Escape fehlgeschlagen!")
    buzzer.play_tone(BuzzerTone.ENHANCED_ESCAPE_FAILED)
    time.sleep(1)
    
    # Fallback zu traditionellem Escape
    print("Fallback zu traditionellem Escape...")
    buzzer.play_tone(BuzzerTone.ENHANCED_ESCAPE_FALLBACK)
    time.sleep(1)
    
    # Learning System Update
    print("Learning System Update...")
    buzzer.play_tone(BuzzerTone.LEARNING_UPDATE)
    time.sleep(1)

def demo_warning_events():
    """Demonstriert Warn-Ereignis Buzzer-Feedback."""
    print("\n=== Warning Events Demo ===")
    
    hardware_manager = MockHardwareManager()
    buzzer = BuzzerFeedback(hardware_manager)
    
    # Batterie schwach
    print("Batterie schwach!")
    buzzer.play_tone(BuzzerTone.WARNING_BATTERY_LOW)
    time.sleep(1)
    
    # Motor überlastet
    print("Motor überlastet!")
    buzzer.play_tone(BuzzerTone.WARNING_MOTOR_OVERLOAD)
    time.sleep(1)
    
    # Sensor Fehler
    print("Sensor Fehler!")
    buzzer.play_tone(BuzzerTone.WARNING_SENSOR_ERROR)
    time.sleep(1)
    
    # Allgemeine Warnung
    print("Allgemeine Warnung!")
    buzzer.play_tone(BuzzerTone.WARNING_GENERAL)
    time.sleep(1)

def demo_tone_sequences():
    """Demonstriert Ton-Sequenzen."""
    print("\n=== Tone Sequences Demo ===")
    
    hardware_manager = MockHardwareManager()
    buzzer = BuzzerFeedback(hardware_manager)
    
    # Startup-Sequenz
    print("Startup-Sequenz...")
    startup_sequence = [
        (BuzzerTone.SYSTEM_STARTUP, 0.2),
        (BuzzerTone.SYSTEM_READY, 0.3),
        (BuzzerTone.NAVIGATION_START, 0.2)
    ]
    buzzer.play_sequence(startup_sequence)
    time.sleep(2)
    
    # Alarm-Sequenz
    print("Alarm-Sequenz...")
    alarm_sequence = [
        (BuzzerTone.WARNING_GENERAL, 0.1),
        (None, 0.1),  # Pause
        (BuzzerTone.WARNING_GENERAL, 0.1),
        (None, 0.1),
        (BuzzerTone.WARNING_GENERAL, 0.1)
    ]
    buzzer.play_sequence(alarm_sequence)
    time.sleep(2)
    
    # Success-Sequenz
    print("Success-Sequenz...")
    success_sequence = [
        (BuzzerTone.ENHANCED_ESCAPE_SUCCESS, 0.15),
        (BuzzerTone.NAVIGATION_COMPLETE, 0.25)
    ]
    buzzer.play_sequence(success_sequence)
    time.sleep(1)

def demo_global_buzzer_feedback():
    """Demonstriert globales Buzzer-Feedback-System."""
    print("\n=== Global Buzzer Feedback Demo ===")
    
    # Globales Buzzer-System initialisieren
    hardware_manager = MockHardwareManager()
    buzzer_feedback = get_buzzer_feedback(hardware_manager)
    
    print("Globales Buzzer-System initialisiert.")
    
    # Verschiedene Events testen
    events_to_test = [
        EventCode.SYSTEM_STARTED,
        EventCode.OBSTACLE_DETECTED,
        EventCode.TILT_WARNING,
        EventCode.SYSTEM_SHUTTING_DOWN
    ]
    
    for event in events_to_test:
        print(f"Event: {event.name}")
        buzzer_feedback.handle_event(event)
        time.sleep(0.8)

def main():
    """Hauptfunktion für Buzzer-Demo."""
    print("🔊 Sunray Buzzer Feedback System Demo")
    print("=====================================")
    
    try:
        # Alle Demos ausführen
        demo_system_events()
        demo_navigation_events()
        demo_enhanced_system_events()
        demo_warning_events()
        demo_tone_sequences()
        demo_global_buzzer_feedback()
        
        print("\n✅ Buzzer Demo abgeschlossen!")
        
    except KeyboardInterrupt:
        print("\n⏹️  Demo durch Benutzer unterbrochen.")
    except Exception as e:
        print(f"\n❌ Fehler in Demo: {e}")

if __name__ == "__main__":
    main()