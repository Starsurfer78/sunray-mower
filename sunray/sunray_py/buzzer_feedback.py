#!/usr/bin/env python3
"""
Buzzer Feedback System für Sunray Mähroboter
Bietet akustisches Feedback für verschiedene System-Events
"""

import time
from typing import Dict, Optional, Tuple
from enum import Enum
from events import EventCode

class BuzzerTone(Enum):
    """Vordefinierte Buzzer-Töne für verschiedene Events"""
    # System Events
    SYSTEM_START = (1000, 200)  # 1kHz, 200ms
    SYSTEM_READY = (800, 100)   # 800Hz, 100ms
    SYSTEM_SHUTDOWN = (400, 500) # 400Hz, 500ms
    
    # Navigation Events
    OBSTACLE_DETECTED = (1500, 150)  # 1.5kHz, 150ms
    ESCAPE_SUCCESS = (600, 100)      # 600Hz, 100ms
    GPS_FIX_ACQUIRED = (1200, 100)   # 1.2kHz, 100ms
    GPS_FIX_LOST = (300, 300)        # 300Hz, 300ms
    
    # Warning Events
    TILT_WARNING = (2000, 100)       # 2kHz, 100ms (kurz und scharf)
    BATTERY_LOW = (500, 200)         # 500Hz, 200ms
    ERROR_GENERAL = (250, 1000)      # 250Hz, 1s (tiefer Ton)
    
    # Enhanced System Events
    LEARNING_UPDATE = (900, 50)      # 900Hz, 50ms (kurz)
    ADAPTIVE_ESCAPE = (1100, 120)    # 1.1kHz, 120ms
    SENSOR_FUSION_ACTIVE = (700, 80) # 700Hz, 80ms
    
    # Confirmation Tones
    CONFIRM_POSITIVE = (1000, 100)   # 1kHz, 100ms
    CONFIRM_NEGATIVE = (400, 200)    # 400Hz, 200ms

class BuzzerFeedback:
    """
    Buzzer Feedback System für akustische Rückmeldungen.
    Integriert sich in das Event-System und Hardware-Management.
    """
    
    def __init__(self, hardware_manager=None, enabled: bool = True):
        """
        Initialisiert das Buzzer Feedback System.
        
        Args:
            hardware_manager: HardwareManager Instanz für Buzzer-Steuerung
            enabled: Ob Buzzer-Feedback aktiviert ist
        """
        self.hardware_manager = hardware_manager
        self.enabled = enabled
        self.last_buzzer_time = 0
        self.min_buzzer_interval = 0.1  # Mindestabstand zwischen Tönen
        
        # Event-zu-Ton Mapping
        self.event_tone_mapping = {
            EventCode.SYSTEM_STARTING: BuzzerTone.SYSTEM_START,
            EventCode.SYSTEM_STARTED: BuzzerTone.SYSTEM_READY,
            EventCode.SYSTEM_SHUTTING_DOWN: BuzzerTone.SYSTEM_SHUTDOWN,
            EventCode.OBSTACLE_DETECTED: BuzzerTone.OBSTACLE_DETECTED,
            EventCode.GPS_FIX_ACQUIRED: BuzzerTone.GPS_FIX_ACQUIRED,
            EventCode.GPS_FIX_LOST: BuzzerTone.GPS_FIX_LOST,
            EventCode.TILT_WARNING: BuzzerTone.TILT_WARNING,
            EventCode.ERROR_BATTERY_UNDERVOLTAGE: BuzzerTone.BATTERY_LOW,
            EventCode.ERROR_GPS_NOT_CONNECTED: BuzzerTone.ERROR_GENERAL,
            EventCode.ERROR_IMU_NOT_CONNECTED: BuzzerTone.ERROR_GENERAL,
        }
        
        # Sequenzen für komplexere Feedback-Muster
        self.tone_sequences = {
            'startup_sequence': [
                (800, 100),   # Kurzer Ton
                (0, 50),      # Pause
                (1000, 150),  # Längerer Ton
                (0, 50),      # Pause
                (1200, 100)   # Bestätigungston
            ],
            'shutdown_sequence': [
                (1000, 100),
                (0, 50),
                (800, 100),
                (0, 50),
                (600, 200)
            ],
            'error_sequence': [
                (300, 200),
                (0, 100),
                (300, 200),
                (0, 100),
                (300, 200)
            ],
            'success_sequence': [
                (600, 80),
                (0, 30),
                (800, 80),
                (0, 30),
                (1000, 120)
            ]
        }
    
    def set_enabled(self, enabled: bool) -> None:
        """Aktiviert oder deaktiviert Buzzer-Feedback."""
        self.enabled = enabled
        print(f"Buzzer Feedback {'aktiviert' if enabled else 'deaktiviert'}")
    
    def play_tone(self, frequency: int, duration: int) -> bool:
        """
        Spielt einen einzelnen Ton ab.
        
        Args:
            frequency: Frequenz in Hz
            duration: Dauer in Millisekunden
            
        Returns:
            bool: True wenn Ton abgespielt wurde
        """
        if not self.enabled:
            return False
            
        current_time = time.time()
        if current_time - self.last_buzzer_time < self.min_buzzer_interval:
            return False  # Zu kurzer Abstand zum letzten Ton
            
        if self.hardware_manager and hasattr(self.hardware_manager, 'send_buzzer_command'):
            success = self.hardware_manager.send_buzzer_command(frequency, duration)
            if success:
                self.last_buzzer_time = current_time
                print(f"Buzzer: {frequency}Hz für {duration}ms")
            return success
        else:
            # Mock-Ausgabe für Entwicklung
            print(f"BUZZER MOCK: {frequency}Hz für {duration}ms")
            self.last_buzzer_time = current_time
            return True
    
    def play_tone_enum(self, tone: BuzzerTone) -> bool:
        """
        Spielt einen vordefinierten Ton ab.
        
        Args:
            tone: BuzzerTone Enum-Wert
            
        Returns:
            bool: True wenn Ton abgespielt wurde
        """
        frequency, duration = tone.value
        return self.play_tone(frequency, duration)
    
    def play_sequence(self, sequence_name: str) -> bool:
        """
        Spielt eine Tonsequenz ab (asynchron).
        
        Args:
            sequence_name: Name der Sequenz
            
        Returns:
            bool: True wenn Sequenz gestartet wurde
        """
        if not self.enabled or sequence_name not in self.tone_sequences:
            return False
            
        sequence = self.tone_sequences[sequence_name]
        
        # Einfache synchrone Implementierung
        # TODO: Für Produktionsumgebung asynchron implementieren
        for frequency, duration in sequence:
            if frequency > 0:
                self.play_tone(frequency, duration)
            time.sleep(duration / 1000.0)  # Pause oder Ton-Dauer
            
        return True
    
    def handle_event(self, event_code: EventCode, additional_data: Optional[str] = None) -> bool:
        """
        Behandelt ein Event und spielt entsprechenden Ton ab.
        
        Args:
            event_code: EventCode für das aufgetretene Event
            additional_data: Zusätzliche Event-Daten
            
        Returns:
            bool: True wenn Feedback abgespielt wurde
        """
        if not self.enabled:
            return False
            
        # Spezielle Sequenzen für bestimmte Events
        if event_code == EventCode.SYSTEM_STARTING:
            return self.play_sequence('startup_sequence')
        elif event_code == EventCode.SYSTEM_SHUTTING_DOWN:
            return self.play_sequence('shutdown_sequence')
        elif event_code in [EventCode.ERROR_GPS_NOT_CONNECTED, 
                           EventCode.ERROR_IMU_NOT_CONNECTED,
                           EventCode.ERROR_BATTERY_UNDERVOLTAGE]:
            return self.play_sequence('error_sequence')
        
        # Standard-Ton für Event
        if event_code in self.event_tone_mapping:
            tone = self.event_tone_mapping[event_code]
            return self.play_tone_enum(tone)
            
        return False
    
    def play_enhanced_feedback(self, feedback_type: str, success: bool = True) -> bool:
        """
        Spielt Enhanced System spezifisches Feedback ab.
        
        Args:
            feedback_type: Art des Feedbacks ('learning', 'escape', 'fusion')
            success: Ob die Aktion erfolgreich war
            
        Returns:
            bool: True wenn Feedback abgespielt wurde
        """
        if not self.enabled:
            return False
            
        if feedback_type == 'learning' and success:
            return self.play_tone_enum(BuzzerTone.LEARNING_UPDATE)
        elif feedback_type == 'escape':
            if success:
                return self.play_tone_enum(BuzzerTone.ADAPTIVE_ESCAPE)
            else:
                return self.play_tone_enum(BuzzerTone.CONFIRM_NEGATIVE)
        elif feedback_type == 'fusion':
            return self.play_tone_enum(BuzzerTone.SENSOR_FUSION_ACTIVE)
        elif feedback_type == 'success':
            return self.play_sequence('success_sequence')
            
        return False
    
    def test_all_tones(self) -> None:
        """
        Testet alle verfügbaren Töne (für Debugging).
        """
        if not self.enabled:
            print("Buzzer ist deaktiviert")
            return
            
        print("Teste alle Buzzer-Töne...")
        
        for tone in BuzzerTone:
            print(f"Spiele {tone.name}...")
            self.play_tone_enum(tone)
            time.sleep(0.5)  # Pause zwischen Tönen
            
        print("Teste Sequenzen...")
        for seq_name in self.tone_sequences.keys():
            print(f"Spiele Sequenz '{seq_name}'...")
            self.play_sequence(seq_name)
            time.sleep(1.0)  # Pause zwischen Sequenzen
            
        print("Buzzer-Test abgeschlossen")

# Globale Buzzer-Instanz
_buzzer_feedback_instance = None

def get_buzzer_feedback(hardware_manager=None, enabled: bool = True) -> BuzzerFeedback:
    """Gibt eine Singleton-Instanz des BuzzerFeedback zurück."""
    global _buzzer_feedback_instance
    if _buzzer_feedback_instance is None:
        _buzzer_feedback_instance = BuzzerFeedback(hardware_manager, enabled)
    return _buzzer_feedback_instance

def shutdown_buzzer_feedback() -> None:
    """Schließt das globale BuzzerFeedback."""
    global _buzzer_feedback_instance
    if _buzzer_feedback_instance is not None:
        _buzzer_feedback_instance.set_enabled(False)
        _buzzer_feedback_instance = None