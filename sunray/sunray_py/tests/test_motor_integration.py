#!/usr/bin/env python3
"""
Integrationstests für Motor-Klasse mit Pico-Daten.
Testet die Integration der Motor-Klasse in die Hauptschleife.
"""

import unittest
import time
from unittest.mock import Mock, patch
import sys
import os

# Pfad zum Hauptverzeichnis hinzufügen
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from motor import Motor
from pid import PID, VelocityPID
from pico_comm import PicoComm

class TestMotorIntegration(unittest.TestCase):
    """Tests für Motor-Klasse Integration mit Pico-Daten."""
    
    def setUp(self):
        """Setup für jeden Test."""
        # Mock Pico-Kommunikation
        self.mock_pico = Mock(spec=PicoComm)
        self.motor = Motor(pico_comm=self.mock_pico)
        self.motor.begin()
    
    def test_motor_initialization(self):
        """Test Motor-Initialisierung."""
        self.assertTrue(self.motor.enabled)
        self.assertIsInstance(self.motor.left_pid, VelocityPID)
        self.assertIsInstance(self.motor.right_pid, VelocityPID)
        self.assertIsInstance(self.motor.mow_pid, PID)
        self.assertEqual(self.motor.target_linear_speed, 0.0)
        self.assertEqual(self.motor.target_angular_speed, 0.0)
    
    def test_pico_data_processing(self):
        """Test Verarbeitung von Pico-Daten."""
        # Simuliere Pico-Daten
        pico_data = {
            'motor_left_current': 1.5,
            'motor_right_current': 1.3,
            'mow_current': 2.1,
            'odom_left': 1000,
            'odom_right': 1020,
            'odom_mow': 500,
            'motor_overload': 0
        }
        
        status = self.motor.update(pico_data)
        
        # Prüfe ob Daten korrekt übernommen wurden
        self.assertEqual(self.motor.current_left_current, 1.5)
        self.assertEqual(self.motor.current_right_current, 1.3)
        self.assertEqual(self.motor.current_mow_current, 2.1)
        self.assertEqual(self.motor.current_left_odom, 1000)
        self.assertEqual(self.motor.current_right_odom, 1020)
        self.assertEqual(self.motor.current_mow_odom, 500)
        
        # Prüfe Status-Rückgabe
        self.assertIn('enabled', status)
        self.assertIn('current_left_current', status)
        self.assertIn('overload_detected', status)
    
    def test_overload_detection(self):
        """Test Überlastungserkennung."""
        # Simuliere Überlastung
        pico_data = {
            'motor_left_current': 4.0,  # Über max_motor_current (3.0)
            'motor_right_current': 1.0,
            'mow_current': 1.0,
            'motor_overload': 0
        }
        
        self.motor.update(pico_data)
        
        self.assertTrue(self.motor.overload_detected)
        self.assertGreater(self.motor.overload_count, 0)
    
    def test_overload_protection(self):
        """Test Überlastungsschutz mit automatischem Stopp."""
        # Simuliere anhaltende Überlastung
        pico_data = {
            'motor_left_current': 4.0,
            'motor_right_current': 4.0,
            'mow_current': 1.0,
            'motor_overload': 1
        }
        
        # Mehrfach aktualisieren bis Überlastungsgrenze erreicht
        for _ in range(self.motor.max_overload_count + 1):
            self.motor.update(pico_data)
        
        # Prüfe ob stop_immediately aufgerufen wurde
        self.mock_pico.send_command.assert_called()
        self.assertTrue(self.motor.overload_detected)
    
    def test_speed_control(self):
        """Test Geschwindigkeitssteuerung."""
        # Setze Geschwindigkeiten
        self.motor.set_linear_angular_speed(0.5, 0.2)
        
        self.assertEqual(self.motor.target_linear_speed, 0.5)
        self.assertEqual(self.motor.target_angular_speed, 0.2)
        
        # Prüfe Differential Drive Kinematik
        expected_left = 0.5 - (0.2 * self.motor.wheel_base / 2.0)
        expected_right = 0.5 + (0.2 * self.motor.wheel_base / 2.0)
        
        self.assertAlmostEqual(self.motor.target_left_speed, expected_left, places=3)
        self.assertAlmostEqual(self.motor.target_right_speed, expected_right, places=3)
    
    def test_mow_control(self):
        """Test Mähmotor-Steuerung."""
        # Mähmotor einschalten
        self.motor.set_mow_state(True)
        
        self.assertTrue(self.motor.mow_enabled)
        self.assertEqual(self.motor.target_mow_speed, 100)
        
        # PWM-Wert setzen
        self.motor.set_mow_pwm(150)
        
        self.assertEqual(self.motor.target_mow_speed, 150)
        
        # Mähmotor ausschalten
        self.motor.set_mow_state(False)
        
        self.assertFalse(self.motor.mow_enabled)
        self.assertEqual(self.motor.target_mow_speed, 0)
    
    def test_emergency_stop(self):
        """Test Notfall-Stopp."""
        # Setze Geschwindigkeiten
        self.motor.set_linear_angular_speed(1.0, 0.5)
        self.motor.set_mow_state(True)
        
        # Notfall-Stopp
        self.motor.stop_immediately()
        
        self.assertEqual(self.motor.target_linear_speed, 0.0)
        self.assertEqual(self.motor.target_angular_speed, 0.0)
        self.assertEqual(self.motor.target_left_speed, 0.0)
        self.assertEqual(self.motor.target_right_speed, 0.0)
        self.assertEqual(self.motor.target_mow_speed, 0)
        self.assertFalse(self.motor.mow_enabled)
        
        # Prüfe Pico-Kommando
        self.mock_pico.send_command.assert_called_with("AT+MOTOR,0,0,0")
    
    def test_pid_control(self):
        """Test PID-Regelung."""
        # Setze Sollgeschwindigkeit
        self.motor.set_linear_angular_speed(0.5, 0.0)
        
        # Simuliere Odometrie-Daten für Geschwindigkeitsberechnung
        pico_data = {
            'odom_left': 100,
            'odom_right': 100,
            'odom_mow': 50,
            'motor_left_current': 1.0,
            'motor_right_current': 1.0,
            'mow_current': 0.5
        }
        
        self.motor.update(pico_data)
        
        # Warte kurz für Zeitdifferenz
        time.sleep(0.1)
        
        # Aktualisiere mit neuen Odometrie-Werten
        pico_data.update({
            'odom_left': 150,
            'odom_right': 150,
            'odom_mow': 75
        })
        
        self.motor.update(pico_data)
        
        # Führe Regelung aus
        self.motor.control()
        
        # Prüfe ob Pico-Kommando gesendet wurde
        self.mock_pico.send_command.assert_called()
    
    def test_adaptive_speed(self):
        """Test adaptive Geschwindigkeitsanpassung."""
        # Simuliere hohen Strom
        self.motor.current_left_current = 2.5
        self.motor.current_right_current = 2.8
        
        speed_factor = self.motor.adaptive_speed()
        
        # Geschwindigkeit sollte reduziert werden
        self.assertLess(speed_factor, 1.0)
        self.assertGreaterEqual(speed_factor, 0.3)  # Mindestens 30%
    
    def test_fault_detection(self):
        """Test Fehlererkennnung."""
        # Simuliere Mähmotor-Fehler
        self.motor.mow_enabled = True
        self.motor.target_mow_speed = 100
        self.motor.current_mow_current = 0.05  # Zu wenig Strom
        
        mow_fault = self.motor.check_mow_rpm_fault()
        self.assertTrue(mow_fault)
        
        # Simuliere Überlastung
        self.motor.overload_detected = True
        
        fault = self.motor.check_fault()
        self.assertTrue(fault)

class TestMotorWithoutPico(unittest.TestCase):
    """Tests für Motor-Klasse ohne Pico-Kommunikation."""
    
    def test_motor_without_pico(self):
        """Test Motor-Funktionalität ohne Pico."""
        motor = Motor(pico_comm=None)
        motor.begin()
        
        # Sollte ohne Fehler funktionieren
        motor.set_linear_angular_speed(0.5, 0.0)
        motor.set_mow_state(True)
        motor.stop_immediately()
        
        # Kein Pico-Kommando sollte gesendet werden
        self.assertIsNone(motor.pico)

if __name__ == '__main__':
    unittest.main()