#!/usr/bin/env python3
"""
Tests für Motor-Konfigurationsintegration.
Testet die Verwendung von Konfigurationswerten in der Motor-Klasse.
"""

import unittest
import tempfile
import os
import json
from unittest.mock import Mock, patch
import sys

# Pfad zum Hauptverzeichnis hinzufügen
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config import Config
from motor import Motor
from hardware_manager import HardwareManager

class TestMotorConfig(unittest.TestCase):
    """Tests für Motor-Konfigurationsintegration."""
    
    def setUp(self):
        """Setup für jeden Test."""
        # Temporäre Konfigurationsdatei erstellen
        self.temp_config_file = tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False)
        self.temp_config_path = self.temp_config_file.name
        self.temp_config_file.close()
        
        # Mock Hardware-Manager
        self.mock_hw_manager = Mock(spec=HardwareManager)
    
    def tearDown(self):
        """Cleanup nach jedem Test."""
        # Temporäre Datei löschen
        if os.path.exists(self.temp_config_path):
            os.unlink(self.temp_config_path)
    
    def test_default_config_creation(self):
        """Test Erstellung der Standard-Konfiguration."""
        config = Config(self.temp_config_path)
        
        # Prüfe ob Standard-Konfiguration erstellt wurde
        self.assertTrue(os.path.exists(self.temp_config_path))
        
        # Prüfe Motor-Sektion
        motor_config = config.get_motor_config()
        self.assertIn('pid', motor_config)
        self.assertIn('limits', motor_config)
        self.assertIn('physical', motor_config)
        self.assertIn('mow', motor_config)
        self.assertIn('adaptive', motor_config)
    
    def test_pid_config_loading(self):
        """Test Laden der PID-Konfiguration."""
        config = Config(self.temp_config_path)
        
        # Teste PID-Konfiguration für alle Motoren
        for motor_name in ['left', 'right', 'mow']:
            pid_config = config.get_pid_config(motor_name)
            self.assertIn('kp', pid_config)
            self.assertIn('ki', pid_config)
            self.assertIn('kd', pid_config)
            self.assertIn('output_min', pid_config)
            self.assertIn('output_max', pid_config)
    
    def test_motor_with_custom_config(self):
        """Test Motor-Klasse mit angepasster Konfiguration."""
        # Angepasste Konfiguration erstellen
        custom_config = {
            "motor": {
                "pid": {
                    "left": {"kp": 2.0, "ki": 0.2, "kd": 0.1, "output_min": -255, "output_max": 255},
                    "right": {"kp": 1.8, "ki": 0.15, "kd": 0.08, "output_min": -255, "output_max": 255},
                    "mow": {"kp": 1.5, "ki": 0.1, "kd": 0.05, "output_min": 0, "output_max": 255}
                },
                "limits": {
                    "max_motor_current": 4.0,
                    "max_mow_current": 6.0,
                    "max_overload_count": 3,
                    "max_realistic_speed": 1.5
                },
                "physical": {
                    "ticks_per_meter": 1200,
                    "wheel_base": 0.35,
                    "pwm_scale_factor": 120
                },
                "mow": {
                    "default_pwm": 150,
                    "min_current_threshold": 0.2,
                    "max_current_threshold": 0.8
                },
                "adaptive": {
                    "enabled": False,
                    "current_threshold_factor": 0.8,
                    "min_speed_factor": 0.4
                }
            }
        }
        
        # Konfiguration in Datei schreiben
        with open(self.temp_config_path, 'w') as f:
            json.dump(custom_config, f)
        
        # Motor mit angepasster Konfiguration erstellen
        with patch('motor.get_config') as mock_get_config:
            config = Config(self.temp_config_path)
            mock_get_config.return_value = config
            
            motor = Motor(hardware_manager=self.mock_hw_manager)
            
            # Prüfe PID-Parameter
            self.assertEqual(motor.left_pid.Kp, 2.0)
            self.assertEqual(motor.left_pid.Ki, 0.2)
            self.assertEqual(motor.right_pid.Kp, 1.8)
            self.assertEqual(motor.right_pid.Ki, 0.15)
            
            # Prüfe Grenzwerte
            self.assertEqual(motor.max_motor_current, 4.0)
            self.assertEqual(motor.max_mow_current, 6.0)
            self.assertEqual(motor.max_overload_count, 3)
            
            # Prüfe physikalische Parameter
            self.assertEqual(motor.ticks_per_meter, 1200)
            self.assertEqual(motor.wheel_base, 0.35)
            self.assertEqual(motor.pwm_scale_factor, 120)
            
            # Prüfe Mähmotor-Parameter
            self.assertEqual(motor.default_mow_pwm, 150)
            self.assertEqual(motor.mow_min_current_threshold, 0.2)
            self.assertEqual(motor.mow_max_current_threshold, 0.8)
            
            # Prüfe adaptive Parameter
            self.assertFalse(motor.adaptive_enabled)
            self.assertEqual(motor.adaptive_current_threshold_factor, 0.8)
            self.assertEqual(motor.adaptive_min_speed_factor, 0.4)
    
    def test_config_validation(self):
        """Test Konfigurationsvalidierung."""
        config = Config(self.temp_config_path)
        
        # Standard-Konfiguration sollte gültig sein
        self.assertTrue(config.validate_config())
        
        # Ungültige Konfiguration testen
        config.config = {"motor": {"invalid": "config"}}
        self.assertFalse(config.validate_config())
    
    def test_config_get_set(self):
        """Test Konfigurationswerte setzen und abrufen."""
        config = Config(self.temp_config_path)
        
        # Einzelnen Wert setzen
        self.assertTrue(config.set('motor.pid.left.kp', 1.5))
        self.assertEqual(config.get('motor.pid.left.kp'), 1.5)
        
        # Verschachtelten Wert setzen
        self.assertTrue(config.set('motor.limits.max_motor_current', 3.5))
        self.assertEqual(config.get('motor.limits.max_motor_current'), 3.5)
        
        # Nicht existierenden Wert abrufen
        self.assertIsNone(config.get('motor.nonexistent.value'))
        self.assertEqual(config.get('motor.nonexistent.value', 'default'), 'default')
    
    def test_motor_mow_state_with_config(self):
        """Test Mähmotor-Zustand mit Konfigurationswerten."""
        with patch('motor.get_config') as mock_get_config:
            config = Config(self.temp_config_path)
            # Angepassten Standard-PWM setzen
            config.set('motor.mow.default_pwm', 180)
            mock_get_config.return_value = config
            
            motor = Motor(hardware_manager=self.mock_hw_manager)
            
            # Mähmotor einschalten
            motor.set_mow_state(True)
            
            # Prüfe ob konfigurierter Standard-PWM verwendet wird
            self.assertEqual(motor.target_mow_speed, 180)
            self.assertTrue(motor.mow_enabled)
    
    def test_adaptive_speed_with_config(self):
        """Test adaptive Geschwindigkeitsanpassung mit Konfiguration."""
        with patch('motor.get_config') as mock_get_config:
            config = Config(self.temp_config_path)
            # Adaptive Anpassung konfigurieren
            config.set('motor.adaptive.enabled', True)
            config.set('motor.adaptive.current_threshold_factor', 0.6)
            config.set('motor.adaptive.min_speed_factor', 0.4)
            config.set('motor.limits.max_motor_current', 3.0)
            mock_get_config.return_value = config
            
            motor = Motor(hardware_manager=self.mock_hw_manager)
            
            # Simuliere hohen Strom
            motor.current_left_current = 2.0
            motor.current_right_current = 2.0
            
            speed_factor = motor.adaptive_speed()
            
            # Erwarteter Faktor: (3.0 * 0.6) / 2.0 = 0.9
            expected_factor = (3.0 * 0.6) / 2.0
            self.assertAlmostEqual(speed_factor, expected_factor, places=2)
            
            # Test mit deaktivierter adaptiver Anpassung
            config.set('motor.adaptive.enabled', False)
            with patch('motor.get_config') as mock_get_config2:
                mock_get_config2.return_value = config
                motor2 = Motor(hardware_manager=self.mock_hw_manager)
                motor2.current_left_current = 2.0
                motor2.current_right_current = 2.0
                
                speed_factor = motor2.adaptive_speed()
                self.assertEqual(speed_factor, 1.0)
    
    def test_config_reload(self):
        """Test Konfiguration neu laden."""
        config = Config(self.temp_config_path)
        
        # Ursprünglichen Wert abrufen
        original_value = config.get('motor.pid.left.kp')
        
        # Konfigurationsdatei extern ändern
        with open(self.temp_config_path, 'r') as f:
            config_data = json.load(f)
        
        config_data['motor']['pid']['left']['kp'] = 999.0
        
        with open(self.temp_config_path, 'w') as f:
            json.dump(config_data, f)
        
        # Konfiguration neu laden
        self.assertTrue(config.reload())
        
        # Prüfe ob neuer Wert geladen wurde
        new_value = config.get('motor.pid.left.kp')
        self.assertNotEqual(original_value, new_value)
        self.assertEqual(new_value, 999.0)
    
    def test_config_reset_to_defaults(self):
        """Test Zurücksetzen auf Standardwerte."""
        config = Config(self.temp_config_path)
        
        # Wert ändern
        config.set('motor.pid.left.kp', 999.0)
        self.assertEqual(config.get('motor.pid.left.kp'), 999.0)
        
        # Auf Standardwerte zurücksetzen
        self.assertTrue(config.reset_to_defaults())
        
        # Prüfe ob Standardwert wiederhergestellt wurde
        default_value = config.get('motor.pid.left.kp')
        self.assertEqual(default_value, 1.0)  # Standard-Kp-Wert
    
    def test_motor_fault_detection_with_config(self):
        """Test Fehlererkennnung mit konfigurierbaren Schwellenwerten."""
        with patch('motor.get_config') as mock_get_config:
            config = Config(self.temp_config_path)
            # Angepasste Schwellenwerte setzen
            config.set('motor.mow.min_current_threshold', 0.3)
            config.set('motor.mow.max_current_threshold', 0.7)
            mock_get_config.return_value = config
            
            motor = Motor(pico_comm=self.mock_pico)
            
            # Test Mähmotor-Fehlererkennnung
            motor.mow_enabled = True
            motor.target_mow_speed = 100
            
            # Zu wenig Strom
            motor.current_mow_current = 0.2  # Unter 0.3
            self.assertTrue(motor.check_mow_rpm_fault())
            
            # Normaler Strom
            motor.current_mow_current = 0.5
            self.assertFalse(motor.check_mow_rpm_fault())
            
            # Motor aus, aber Strom fließt
            motor.mow_enabled = False
            motor.target_mow_speed = 0
            motor.current_mow_current = 0.8  # Über 0.7
            self.assertTrue(motor.check_mow_rpm_fault())

class TestConfigHelperFunctions(unittest.TestCase):
    """Tests für Konfigurationshilfsfunktionen."""
    
    def setUp(self):
        """Setup für jeden Test."""
        self.temp_config_file = tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False)
        self.temp_config_path = self.temp_config_file.name
        self.temp_config_file.close()
    
    def tearDown(self):
        """Cleanup nach jedem Test."""
        if os.path.exists(self.temp_config_path):
            os.unlink(self.temp_config_path)
    
    def test_get_motor_config(self):
        """Test get_motor_config Hilfsfunktion."""
        config = Config(self.temp_config_path)
        motor_config = config.get_motor_config()
        
        self.assertIsInstance(motor_config, dict)
        self.assertIn('pid', motor_config)
        self.assertIn('limits', motor_config)
    
    def test_get_pid_config(self):
        """Test get_pid_config für verschiedene Motoren."""
        config = Config(self.temp_config_path)
        
        for motor in ['left', 'right', 'mow']:
            pid_config = config.get_pid_config(motor)
            self.assertIsInstance(pid_config, dict)
            self.assertIn('kp', pid_config)
    
    def test_get_motor_limits(self):
        """Test get_motor_limits Hilfsfunktion."""
        config = Config(self.temp_config_path)
        limits = config.get_motor_limits()
        
        self.assertIsInstance(limits, dict)
        self.assertIn('max_motor_current', limits)
        self.assertIn('max_mow_current', limits)
    
    def test_get_physical_config(self):
        """Test get_physical_config Hilfsfunktion."""
        config = Config(self.temp_config_path)
        physical = config.get_physical_config()
        
        self.assertIsInstance(physical, dict)
        self.assertIn('ticks_per_meter', physical)
        self.assertIn('wheel_base', physical)

if __name__ == '__main__':
    unittest.main()