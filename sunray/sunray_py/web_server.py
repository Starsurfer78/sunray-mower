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

from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
import os
import psutil
import json
import time
from datetime import datetime
import random
import threading
from typing import Dict, List, Any

app = Flask(__name__, static_folder='static', static_url_path='/static')
CORS(app)  # Enable CORS for all routes

# Global variables for advanced path planning
advanced_planner_instance = None
planning_stats = {
    'total_plans': 0,
    'total_time': 0.0,
    'successful_plans': 0,
    'replanning_count': 0,
    'dynamic_obstacles': 0,
    'last_planning_time': 0.0
}

current_planning_status = {
    'strategy': 'hybrid',
    'status': 'ready',
    'progress': 0.0,
    'total_segments': 0,
    'current_segment': 0,
    'total_planned_distance': 0.0,
    'replanning_count': 0,
    'last_planning_time': 0.0
}

planning_lock = threading.Lock()

# Mock data for demonstration
mock_sensor_data = {
    'battery': {'level': 85, 'voltage': 12.6, 'charging': False},
    'gps': {'latitude': 52.5200, 'longitude': 13.4050, 'quality': 4, 'satellites': 8},
    'imu': {'heading': 90, 'roll': 0, 'pitch': 0, 'temperature': 25.0}
}

mock_robot_status = {
    'state': 'Bereit',
    'mode': 'Automatisch',
    'position': {'x': 125, 'y': 75, 'heading': 90}
}

# Web Interface Routes
@app.route('/')
def index():
    """Hauptseite des Web Interfaces."""
    return send_from_directory('static', 'index.html')

@app.route('/api/status')
def api_status():
    """API Status für Verbindungscheck."""
    return jsonify({
        'status': 'online',
        'timestamp': datetime.now().isoformat(),
        'version': '1.0.0'
    })

@app.route('/api/sensors')
def api_sensors():
    """Erweiterte Sensordaten für das Web Interface."""
    try:
        # Simuliere leichte Schwankungen in den Sensordaten
        import random
        mock_sensor_data['battery']['level'] = max(20, min(100, mock_sensor_data['battery']['level'] + random.randint(-2, 2)))
        mock_sensor_data['imu']['heading'] = (mock_sensor_data['imu']['heading'] + random.randint(-5, 5)) % 360
        mock_sensor_data['imu']['temperature'] = 25.0 + random.uniform(-2, 2)
        
        return jsonify({
            **mock_sensor_data,
            'timestamp': datetime.now().isoformat()
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/navigation/start', methods=['POST'])
def start_autonomous_mowing():
    """Startet autonomes Mähen."""
    try:
        mock_robot_status['state'] = 'Mähen'
        mock_robot_status['mode'] = 'Automatisch'
        return jsonify({'status': 'started', 'message': 'Autonomous mowing started'})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/navigation/stop', methods=['POST'])
def stop_autonomous_mowing():
    """Stoppt autonomes Mähen."""
    try:
        mock_robot_status['state'] = 'Gestoppt'
        return jsonify({'status': 'stopped', 'message': 'Autonomous mowing stopped'})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/navigation/pause', methods=['POST'])
def pause_navigation():
    """Pausiert die Navigation."""
    try:
        mock_robot_status['state'] = 'Pausiert'
        return jsonify({'status': 'paused', 'message': 'Navigation paused'})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/navigation/home', methods=['POST'])
def return_home():
    """Startet Rückkehr zur Basis."""
    try:
        mock_robot_status['state'] = 'Rückkehr zur Basis'
        return jsonify({'status': 'returning', 'message': 'Returning to base'})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/navigation/status', methods=['GET'])
def get_navigation_status():
    """Gibt den aktuellen Navigationsstatus zurück."""
    try:
        return jsonify(mock_robot_status)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/map/current')
def get_current_map():
    """Gibt die aktuelle Karte zurück."""
    try:
        # Simuliere Roboterbewegung
        import random
        mock_robot_status['position']['x'] += random.randint(-5, 5)
        mock_robot_status['position']['y'] += random.randint(-5, 5)
        
        map_data = {
            'zones': [
                {
                    'id': 1,
                    'name': 'Hauptbereich',
                    'points': [
                        {'x': 50, 'y': 50},
                        {'x': 200, 'y': 50},
                        {'x': 200, 'y': 150},
                        {'x': 50, 'y': 150}
                    ]
                }
            ],
            'path': [
                {'x': 100, 'y': 75},
                {'x': 120, 'y': 75},
                {'x': 140, 'y': 75},
                {'x': 160, 'y': 75}
            ],
            'robot_position': mock_robot_status['position']
        }
        return jsonify(map_data)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/system/stats')
def get_system_stats():
    """Gibt System-Statistiken zurück."""
    try:
        # CPU Auslastung
        cpu_usage = psutil.cpu_percent(interval=0.1)
        
        # RAM Nutzung
        memory = psutil.virtual_memory()
        memory_usage = memory.percent
        
        # Festplatten-Nutzung
        disk = psutil.disk_usage('C:' if os.name == 'nt' else '/')
        disk_usage = (disk.used / disk.total) * 100
        
        # CPU Temperatur (Simulation für Windows)
        cpu_temp = 45.0 + (cpu_usage / 10)  # Simulierte Temperatur basierend auf CPU-Last
        
        return jsonify({
            'cpu_usage': round(cpu_usage, 1),
            'memory_usage': round(memory_usage, 1),
            'disk_usage': round(disk_usage, 1),
            'cpu_temp': round(cpu_temp, 1),
            'uptime': time.time() - psutil.boot_time(),
            'timestamp': datetime.now().isoformat()
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/config', methods=['GET', 'POST'])
def robot_config():
    """Roboter-Konfiguration verwalten."""
    config_file = 'robot_config.json'
    
    if request.method == 'GET':
        try:
            if os.path.exists(config_file):
                with open(config_file, 'r') as f:
                    config = json.load(f)
            else:
                # Standard-Konfiguration
                config = {
                    'mow_speed': 1.0,
                    'line_spacing': 0.3,
                    'mow_pattern': 'LINES',
                    'auto_return': True,
                    'battery_threshold': 20
                }
            return jsonify(config)
        except Exception as e:
            return jsonify({'error': str(e)}), 500
    
    elif request.method == 'POST':
        try:
            config = request.get_json()
            with open(config_file, 'w') as f:
                json.dump(config, f, indent=2)
            return jsonify({'status': 'saved', 'config': config})
        except Exception as e:
            return jsonify({'error': str(e)}), 500

@app.route('/api/updates/check')
def check_updates():
    """Prüft auf verfügbare Updates."""
    try:
        return jsonify({
            'current_version': '1.0.0',
            'latest_version': '1.0.1',
            'update_available': True,
            'release_notes': 'Bugfixes und Verbesserungen der Navigation',
            'download_url': 'https://github.com/user/sunray/releases/latest'
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/updates/install', methods=['POST'])
def install_update():
    """Installiert ein Update."""
    try:
        return jsonify({
            'status': 'started',
            'message': 'Update-Installation gestartet',
            'estimated_time': '5 minutes'
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/pico/flash', methods=['POST'])
def flash_pico():
    """Flasht den Pico über UART."""
    try:
        data = request.get_json() or {}
        firmware_path = data.get('firmware_path', 'firmware.uf2')
        
        return jsonify({
            'status': 'started',
            'message': 'Pico Flash-Prozess gestartet',
            'firmware_path': firmware_path
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/camera/stream')
def camera_stream():
    """Kamera-Stream Endpunkt."""
    return jsonify({
        'stream_url': '/api/camera/mjpeg',
        'resolution': '640x480',
        'fps': 15,
        'available': False,
        'message': 'Kamera nicht verfügbar (Demo-Modus)'
    })

@app.route('/api/zones', methods=['GET', 'POST', 'DELETE'])
def manage_zones():
    """Verwaltet Mähzonen."""
    zones_file = 'zones.json'
    
    if request.method == 'GET':
        try:
            if os.path.exists(zones_file):
                with open(zones_file, 'r') as f:
                    zones = json.load(f)
            else:
                # Standard-Zonen
                zones = [
                    {
                        'id': 1,
                        'name': 'Hauptbereich',
                        'points': [
                            {'x': 50, 'y': 50},
                            {'x': 200, 'y': 50},
                            {'x': 200, 'y': 150},
                            {'x': 50, 'y': 150}
                        ],
                        'created': datetime.now().isoformat()
                    }
                ]
            return jsonify(zones)
        except Exception as e:
            return jsonify({'error': str(e)}), 500
    
    elif request.method == 'POST':
        try:
            zone = request.get_json()
            
            # Lade bestehende Zonen
            zones = []
            if os.path.exists(zones_file):
                with open(zones_file, 'r') as f:
                    zones = json.load(f)
            
            # Füge neue Zone hinzu
            zone['id'] = len(zones) + 1
            zone['created'] = datetime.now().isoformat()
            zones.append(zone)
            
            # Speichere Zonen
            with open(zones_file, 'w') as f:
                json.dump(zones, f, indent=2)
            
            return jsonify({'status': 'created', 'zone': zone})
        except Exception as e:
            return jsonify({'error': str(e)}), 500
    
    elif request.method == 'DELETE':
        try:
            zone_id = request.args.get('id', type=int)
            if not zone_id:
                return jsonify({'error': 'Zone ID required'}), 400
            
            # Lade und filtere Zonen
            zones = []
            if os.path.exists(zones_file):
                with open(zones_file, 'r') as f:
                    zones = json.load(f)
            
            zones = [z for z in zones if z.get('id') != zone_id]
            
            # Speichere gefilterte Zonen
            with open(zones_file, 'w') as f:
                json.dump(zones, f, indent=2)
            
            return jsonify({'status': 'deleted', 'zone_id': zone_id})
        except Exception as e:
            return jsonify({'error': str(e)}), 500

# Advanced Path Planning API Endpoints
@app.route('/api/advanced_planning/start', methods=['POST'])
def start_advanced_planning():
    """Startet die erweiterte Pfadplanung."""
    try:
        data = request.get_json() or {}
        strategy = data.get('strategy', 'hybrid')
        pattern = data.get('pattern', 'lines')
        max_segment_length = data.get('max_segment_length', 10.0)
        obstacle_detection_radius = data.get('obstacle_detection_radius', 1.0)
        heuristic_weight = data.get('heuristic_weight', 1.0)
        
        with planning_lock:
            start_time = time.time()
            
            # Simuliere Planungszeit
            planning_time = random.uniform(0.5, 2.0)
            time.sleep(planning_time)
            
            # Update planning status
            current_planning_status.update({
                'strategy': strategy,
                'status': 'completed',
                'progress': 1.0,
                'total_segments': random.randint(15, 50),
                'current_segment': 0,
                'total_planned_distance': random.uniform(100, 500),
                'last_planning_time': planning_time
            })
            
            # Update statistics
            planning_stats['total_plans'] += 1
            planning_stats['total_time'] += planning_time
            planning_stats['successful_plans'] += 1
            planning_stats['last_planning_time'] = planning_time
            
            # Generate mock path
            path = generate_mock_path(pattern, current_planning_status['total_segments'])
            
            return jsonify({
                'success': True,
                'status': current_planning_status.copy(),
                'path': path,
                'planning_time': planning_time,
                'message': f'Planung mit {strategy} Strategie erfolgreich'
            })
            
    except Exception as e:
        with planning_lock:
            current_planning_status['status'] = 'error'
            planning_stats['total_plans'] += 1
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/advanced_planning/reset', methods=['POST'])
def reset_advanced_planning():
    """Setzt die erweiterte Pfadplanung zurück."""
    try:
        with planning_lock:
            current_planning_status.update({
                'status': 'ready',
                'progress': 0.0,
                'current_segment': 0,
                'total_segments': 0,
                'total_planned_distance': 0.0
            })
            
        return jsonify({
            'success': True,
            'message': 'Pfadplanung zurückgesetzt'
        })
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/advanced_planning/stop', methods=['POST'])
def stop_advanced_planning():
    """Stoppt die erweiterte Pfadplanung."""
    try:
        with planning_lock:
            current_planning_status['status'] = 'stopped'
            
        return jsonify({
            'success': True,
            'message': 'Pfadplanung gestoppt'
        })
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/advanced_planning/status', methods=['GET'])
def get_advanced_planning_status():
    """Gibt den aktuellen Status der erweiterten Pfadplanung zurück."""
    try:
        with planning_lock:
            status = current_planning_status.copy()
            stats = planning_stats.copy()
            
        return jsonify({
            **status,
            'statistics': stats,
            'timestamp': datetime.now().isoformat()
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/advanced_planning/add_obstacle', methods=['POST'])
def add_dynamic_obstacle():
    """Fügt ein dynamisches Hindernis hinzu."""
    try:
        data = request.get_json() or {}
        x = data.get('x', 0.0)
        y = data.get('y', 0.0)
        size = data.get('size', 1.0)
        
        with planning_lock:
            planning_stats['dynamic_obstacles'] += 1
            
            # Simuliere Neuplanung bei 30% Wahrscheinlichkeit
            replanning_triggered = random.random() < 0.3
            
            if replanning_triggered:
                planning_stats['replanning_count'] += 1
                current_planning_status['replanning_count'] += 1
                
        return jsonify({
            'success': True,
            'obstacle': {'x': x, 'y': y, 'size': size},
            'replanning_triggered': replanning_triggered,
            'message': f'Dynamisches Hindernis bei ({x:.1f}, {y:.1f}) hinzugefügt'
        })
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/advanced_planning/simulate_navigation', methods=['POST'])
def simulate_navigation():
    """Simuliert Navigation entlang des geplanten Pfads."""
    try:
        data = request.get_json() or {}
        max_waypoints = data.get('max_waypoints', 20)
        
        # Generiere Wegpunkte für Simulation
        waypoints = []
        total_distance = 0.0
        
        for i in range(max_waypoints):
            x = random.uniform(50, 200)
            y = random.uniform(50, 150)
            waypoints.append({'x': x, 'y': y, 'timestamp': time.time() + i})
            
            if i > 0:
                prev = waypoints[i-1]
                distance = ((x - prev['x'])**2 + (y - prev['y'])**2)**0.5
                total_distance += distance
        
        with planning_lock:
            current_planning_status['current_segment'] = min(
                max_waypoints, 
                current_planning_status['total_segments']
            )
            current_planning_status['progress'] = min(1.0, max_waypoints / max(1, current_planning_status['total_segments']))
        
        return jsonify({
            'success': True,
            'waypoints': waypoints,
            'waypoints_visited': len(waypoints),
            'total_distance': total_distance,
            'message': f'Navigation simuliert: {len(waypoints)} Wegpunkte'
        })
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

def generate_mock_path(pattern: str, num_segments: int) -> List[Dict[str, float]]:
    """Generiert einen Mock-Pfad basierend auf dem gewählten Muster."""
    path = []
    
    if pattern == 'lines':
        # Linien-Muster
        for i in range(num_segments):
            x = 60 + (i % 10) * 15
            y = 60 + (i // 10) * 10
            path.append({'x': x, 'y': y})
            
    elif pattern == 'spiral':
        # Spiral-Muster
        center_x, center_y = 125, 100
        for i in range(num_segments):
            angle = i * 0.3
            radius = 5 + i * 2
            x = center_x + radius * math.cos(angle)
            y = center_y + radius * math.sin(angle)
            path.append({'x': x, 'y': y})
            
    elif pattern == 'random':
        # Zufälliges Muster
        for i in range(num_segments):
            x = random.uniform(60, 190)
            y = random.uniform(60, 140)
            path.append({'x': x, 'y': y})
            
    else:  # perimeter
        # Umrandungs-Muster
        perimeter_points = [
            (60, 60), (190, 60), (190, 140), (60, 140)
        ]
        for i in range(num_segments):
            point_idx = i % len(perimeter_points)
            x, y = perimeter_points[point_idx]
            # Kleine Variation
            x += random.uniform(-5, 5)
            y += random.uniform(-5, 5)
            path.append({'x': x, 'y': y})
    
    return path

# Import math for spiral pattern
import math

if __name__ == '__main__':
    print("Sunray Mähroboter Web Interface")
    print("Starte Server auf http://localhost:5000")
    print("Erweiterte Pfadplanung verfügbar unter /static/advanced_planning.html")
    print("Drücke Ctrl+C zum Beenden")
    app.run(host='0.0.0.0', port=5000, debug=True)