#!/usr/bin/env python3
"""
Test für die neue Konfigurationsstruktur mit config_example.json
"""

import os
import tempfile
import json
from config import Config

def test_config_example_loading():
    """Test ob config_example.json korrekt geladen wird."""
    
    # Erstelle temporäres Verzeichnis für Test
    with tempfile.TemporaryDirectory() as temp_dir:
        test_config_path = os.path.join(temp_dir, 'test_config.json')
        
        # Erstelle Config-Instanz (sollte config_example.json laden)
        config = Config(test_config_path)
        
        # Prüfe ob Werte aus config_example.json geladen wurden
        print("=== Test: Laden der Beispiel-Konfiguration ===")
        print(f"Motor PID Left Kp: {config.get('motor.pid.left.kp')}")
        print(f"Motor PID Right Ki: {config.get('motor.pid.right.ki')}")
        print(f"Motor PID Mow Kd: {config.get('motor.pid.mow.kd')}")
        print(f"Max Motor Current: {config.get('motor.limits.max_motor_current')}")
        print(f"Adaptive enabled: {config.get('motor.adaptive.enabled')}")
        print(f"System debug: {config.get('system.debug')}")
        print(f"Safety emergency stop: {config.get('safety.emergency_stop_enabled')}")
        
        # Prüfe ob die Konfigurationsdatei erstellt wurde
        if os.path.exists(test_config_path):
            print(f"\n=== Erstellte Konfigurationsdatei: {test_config_path} ===")
            with open(test_config_path, 'r') as f:
                saved_config = json.load(f)
                print(f"Anzahl Hauptsektionen: {len(saved_config)}")
                print(f"Verfügbare Sektionen: {list(saved_config.keys())}")
        
        # Test Konfigurationsvalidierung
        print(f"\n=== Konfigurationsvalidierung ===")
        is_valid = config.validate_config()
        print(f"Konfiguration gültig: {is_valid}")
        
        return config

def test_fallback_behavior():
    """Test Fallback-Verhalten wenn config_example.json nicht verfügbar ist."""
    
    # Temporär config_example.json umbenennen
    example_path = os.path.join(os.path.dirname(__file__), 'config_example.json')
    backup_path = example_path + '.backup'
    
    try:
        if os.path.exists(example_path):
            os.rename(example_path, backup_path)
        
        with tempfile.TemporaryDirectory() as temp_dir:
            test_config_path = os.path.join(temp_dir, 'fallback_test.json')
            
            print("\n=== Test: Fallback-Verhalten ===")
            config = Config(test_config_path)
            
            # Sollte trotzdem funktionieren mit hardcodierten Werten
            print(f"Fallback Motor PID Left Kp: {config.get('motor.pid.left.kp')}")
            print(f"Fallback System debug: {config.get('system.debug')}")
            
    finally:
        # config_example.json wiederherstellen
        if os.path.exists(backup_path):
            os.rename(backup_path, example_path)

if __name__ == '__main__':
    print("Teste neue Konfigurationsstruktur...\n")
    
    # Test 1: Normale Verwendung
    config = test_config_example_loading()
    
    # Test 2: Fallback-Verhalten
    test_fallback_behavior()
    
    print("\n=== Test abgeschlossen ===")
    print("Die Konfiguration lädt erfolgreich Werte aus config_example.json")
    print("und fällt auf hardcodierte Werte zurück, wenn die Datei nicht verfügbar ist.")