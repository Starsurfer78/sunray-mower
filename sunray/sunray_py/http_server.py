from flask import Flask, request, jsonify, render_template_string, send_from_directory
import os
import psutil
import json
import subprocess
import time
from datetime import datetime
from imu import IMUSensor
from gps_module import GPSModule
from hardware_manager import get_hardware_manager
from path_planner import MowPattern
from map import Point, Polygon
from enhanced_escape_operations import SensorFusion, LearningSystem, AdaptiveEscapeOp
from examples.integration_example import EnhancedSunrayController
from smart_button_controller import get_smart_button_controller, ButtonAction

# Hardware-Konfiguration laden
def load_hardware_config():
    """Lädt Hardware-Konfiguration aus config.json."""
    try:
        import json
        with open('config.json', 'r') as f:
            config = json.load(f)
            hardware_config = config.get('hardware', {})
            pico_config = hardware_config.get('pico_comm', {})
            return {
                'port': pico_config.get('port', '/dev/ttyS0'),
                'baudrate': pico_config.get('baudrate', 115200)
            }
    except (FileNotFoundError, json.JSONDecodeError, KeyError):
        return {'port': '/dev/ttyS0', 'baudrate': 115200}

app = Flask(__name__, static_folder='static', static_url_path='/static')
imu = IMUSensor()
gps = GPSModule()

# Hardware Manager mit konfigurierbaren Einstellungen
hw_config = load_hardware_config()
hw_manager = get_hardware_manager(port=hw_config['port'], baudrate=hw_config['baudrate'])
print(f"HTTP Server: Hardware Manager konfiguriert - Port: {hw_config['port']}, Baudrate: {hw_config['baudrate']}")

# Global instances - werden von main.py gesetzt
motor_instance = None
enhanced_controller = None
sensor_fusion = None
learning_system = None
button_controller = None

def set_motor_instance(motor):
    """Setzt die Motor-Instanz für API-Zugriff."""
    global motor_instance
    motor_instance = motor

def set_enhanced_system(controller, fusion, learning):
    """Setzt die Enhanced System Instanzen für API-Zugriff."""
    global enhanced_controller, sensor_fusion, learning_system
    enhanced_controller = controller
    sensor_fusion = fusion
    learning_system = learning

def set_button_controller(controller):
    """Setzt die Button Controller Instanz."""
    global button_controller
    button_controller = controller

@app.route('/sensors', methods=['GET'])
def get_sensors():
    """
    Gibt aktuelle Sensordaten zurück.
    Beispiele:
      GET /sensors
    """
    data = {
        'imu': imu.read(),
        'gps': gps.read()
    }
    return jsonify(data)

@app.route('/command', methods=['POST'])
def post_command():
    """
    Empfängt JSON-Kommando und sendet ASCII-Befehl an Pico.
    Beispiel-Body: {"command": "AT+M"}
    """
    payload = request.get_json(force=True)
    cmd = payload.get('command', '')
    hw_manager.send_command(cmd)
    return jsonify({'status': 'sent', 'command': cmd})

@app.route('/navigation/start', methods=['POST'])
def start_autonomous_mowing():
    """
    Startet autonomes Mähen.
    """
    if not motor_instance:
        return jsonify({'error': 'Motor instance not available'}), 500
    
    try:
        motor_instance.start_autonomous_mowing()
        return jsonify({'status': 'started', 'message': 'Autonomous mowing started'})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/navigation/stop', methods=['POST'])
def stop_autonomous_mowing():
    """
    Stoppt autonomes Mähen.
    """
    if not motor_instance:
        return jsonify({'error': 'Motor instance not available'}), 500
    
    try:
        motor_instance.stop_autonomous_mowing()
        return jsonify({'status': 'stopped', 'message': 'Autonomous mowing stopped'})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/navigation/status', methods=['GET'])
def get_navigation_status():
    """
    Gibt den aktuellen Navigationsstatus zurück.
    """
    if not motor_instance:
        return jsonify({'error': 'Motor instance not available'}), 500
    
    try:
        status = motor_instance.get_navigation_status()
        return jsonify(status)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/navigation/pattern', methods=['POST'])
def set_mow_pattern():
    """
    Setzt das Mähmuster.
    Beispiel-Body: {"pattern": "LINES", "line_spacing": 0.3}
    """
    if not motor_instance:
        return jsonify({'error': 'Motor instance not available'}), 500
    
    payload = request.get_json(force=True)
    pattern_name = payload.get('pattern', 'LINES')
    line_spacing = payload.get('line_spacing', 0.3)
    
    try:
        # Pattern-String zu Enum konvertieren
        pattern = MowPattern[pattern_name.upper()]
        motor_instance.set_mow_pattern(pattern)
        motor_instance.set_line_spacing(line_spacing)
        return jsonify({
            'status': 'set', 
            'pattern': pattern_name, 
            'line_spacing': line_spacing
        })
    except KeyError:
        return jsonify({'error': f'Invalid pattern: {pattern_name}'}), 400
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/navigation/zones', methods=['POST'])
def set_mow_zones():
    """
    Setzt Mähzonen.
    Beispiel-Body: {
        "zones": [
            {"points": [[0, 0], [10, 0], [10, 10], [0, 10]]}
        ]
    }
    """
    if not motor_instance:
        return jsonify({'error': 'Motor instance not available'}), 500
    
    payload = request.get_json(force=True)
    zones_data = payload.get('zones', [])
    
    try:
        zones = []
        for zone_data in zones_data:
            points = [Point(p[0], p[1]) for p in zone_data['points']]
            zones.append(Polygon(points))
        
        motor_instance.set_mow_zones(zones)
        return jsonify({
            'status': 'set', 
            'zones_count': len(zones)
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# Enhanced Escape System API Endpunkte
@app.route('/enhanced/status', methods=['GET'])
def get_enhanced_status():
    """Gibt den Status des Enhanced Escape Systems zurück."""
    if not all([enhanced_controller, sensor_fusion, learning_system]):
        return jsonify({'error': 'Enhanced system not available'}), 500
    
    try:
        return jsonify({
            'sensor_fusion': {
                'current_weights': sensor_fusion.get_current_weights(),
                'confidence': sensor_fusion.get_confidence(),
                'statistics': sensor_fusion.get_statistics()
            },
            'learning_system': {
                'statistics': learning_system.get_statistics(),
                'context_distribution': learning_system.get_context_distribution(),
                'learning_enabled': learning_system.learning_enabled
            },
            'controller': {
                'active': enhanced_controller.is_active(),
                'last_strategy': enhanced_controller.get_last_strategy()
            }
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/enhanced/learning/toggle', methods=['POST'])
def toggle_learning():
    """Aktiviert/deaktiviert maschinelles Lernen."""
    if not learning_system:
        return jsonify({'error': 'Learning system not available'}), 503
    
    try:
        data = request.get_json() or {}
        enabled = data.get('enabled', not learning_system.learning_enabled)
        
        learning_system.set_learning_enabled(enabled)
        
        return jsonify({
            'learning_enabled': learning_system.learning_enabled,
            'message': f"Learning {'aktiviert' if enabled else 'deaktiviert'}"
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# Button Controller API Endpunkte
@app.route('/button/status', methods=['GET'])
def get_button_status():
    """Gibt den aktuellen Status des Button Controllers zurück."""
    if not button_controller:
        return jsonify({'error': 'Button controller not available'}), 503
    
    try:
        status = button_controller.get_status()
        return jsonify({
            'status': 'success',
            'button_controller': status
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/button/simulate', methods=['POST'])
def simulate_button_press():
    """Simuliert einen Button-Druck für Tests."""
    if not button_controller:
        return jsonify({'error': 'Button controller not available'}), 503
    
    try:
        data = request.get_json()
        if not data or 'duration' not in data:
            return jsonify({'error': 'Duration parameter required'}), 400
        
        duration = float(data['duration'])
        if duration < 0 or duration > 10:
            return jsonify({'error': 'Duration must be between 0 and 10 seconds'}), 400
        
        action = button_controller.simulate_button_press(duration)
        
        return jsonify({
            'status': 'success',
            'simulated_duration': duration,
            'executed_action': action.value,
            'message': f'Button-Druck ({duration:.1f}s) simuliert -> {action.value}'
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/button/actions', methods=['GET'])
def get_available_actions():
    """Gibt verfügbare Button-Aktionen zurück."""
    try:
        actions = {
            'short_press': {
                'duration': '< 1 second',
                'action': 'START_MOW or STOP_MOW (context dependent)',
                'description': 'Startet/stoppt Mähvorgang je nach aktuellem Zustand'
            },
            'medium_press': {
                'duration': '1-5 seconds',
                'action': 'EMERGENCY_STOP',
                'description': 'Notfall-Stopp aller Motoren'
            },
            'long_press': {
                'duration': '≥ 5 seconds',
                'action': 'GO_HOME',
                'description': 'Startet Docking-Vorgang zur Ladestation'
            }
        }
        
        return jsonify({
            'status': 'success',
            'available_actions': actions,
            'button_actions': [action.value for action in ButtonAction]
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/button/config', methods=['GET', 'POST'])
def button_config():
    """Konfiguration des Button Controllers."""
    if not button_controller:
        return jsonify({'error': 'Button controller not available'}), 503
    
    try:
        if request.method == 'GET':
            # Aktuelle Konfiguration zurückgeben
            config = {
                'short_press_max_duration': button_controller.short_press_max_duration,
                'long_press_duration': button_controller.long_press_duration,
                'beep_interval': button_controller.beep_interval,
                'button_debounce_time': button_controller.button_debounce_time
            }
            return jsonify({
                'status': 'success',
                'config': config
            })
        
        elif request.method == 'POST':
            # Konfiguration aktualisieren
            data = request.get_json() or {}
            
            if 'short_press_max_duration' in data:
                button_controller.short_press_max_duration = float(data['short_press_max_duration'])
            
            if 'long_press_duration' in data:
                button_controller.long_press_duration = float(data['long_press_duration'])
            
            if 'beep_interval' in data:
                button_controller.beep_interval = float(data['beep_interval'])
            
            if 'button_debounce_time' in data:
                button_controller.button_debounce_time = float(data['button_debounce_time'])
            
            return jsonify({
                'status': 'success',
                'message': 'Button-Konfiguration aktualisiert',
                'config': {
                    'short_press_max_duration': button_controller.short_press_max_duration,
                    'long_press_duration': button_controller.long_press_duration,
                    'beep_interval': button_controller.beep_interval,
                    'button_debounce_time': button_controller.button_debounce_time
                }
            })
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/enhanced/learning/reset', methods=['POST'])
def reset_learning():
    """Setzt das Lernsystem zurück."""
    if not learning_system:
        return jsonify({'error': 'Learning system not available'}), 500
    
    try:
        learning_system.reset_learning_data()
        return jsonify({'status': 'reset', 'message': 'Learning data cleared'})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/enhanced/sensor_fusion/weights', methods=['POST'])
def set_sensor_weights():
    """Setzt manuelle Sensor-Gewichtungen."""
    if not sensor_fusion:
        return jsonify({'error': 'Sensor fusion not available'}), 500
    
    payload = request.get_json(force=True)
    weights = payload.get('weights', {})
    
    try:
        sensor_fusion.set_manual_weights(weights)
        return jsonify({
            'status': 'set',
            'current_weights': sensor_fusion.get_current_weights()
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/enhanced/sensor_fusion/auto_weights', methods=['POST'])
def enable_auto_weights():
    """Aktiviert automatische Sensor-Gewichtung."""
    if not sensor_fusion:
        return jsonify({'error': 'Sensor fusion not available'}), 500
    
    try:
        sensor_fusion.enable_adaptive_weighting()
        return jsonify({
            'status': 'enabled',
            'message': 'Adaptive weighting enabled'
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/enhanced/statistics', methods=['GET'])
def get_enhanced_statistics():
    """Gibt detaillierte Statistiken des Enhanced Systems zurück."""
    if not all([enhanced_controller, sensor_fusion, learning_system]):
        return jsonify({'error': 'Enhanced system not available'}), 500
    
    try:
        return jsonify({
            'learning_statistics': learning_system.get_detailed_statistics(),
            'sensor_fusion_statistics': sensor_fusion.get_detailed_statistics(),
            'performance_metrics': enhanced_controller.get_performance_metrics()
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

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
        imu_data = imu.read()
        gps_data = gps.read()
        
        # Batterie-Simulation (falls nicht verfügbar)
        battery_level = 85  # Placeholder
        
        return jsonify({
            'battery': {
                'level': battery_level,
                'voltage': 12.6,
                'charging': False
            },
            'gps': {
                'latitude': gps_data.get('latitude', 0),
                'longitude': gps_data.get('longitude', 0),
                'quality': gps_data.get('quality', 0),
                'satellites': gps_data.get('satellites', 0)
            },
            'imu': {
                'heading': imu_data.get('heading', 0),
                'roll': imu_data.get('roll', 0),
                'pitch': imu_data.get('pitch', 0),
                'temperature': imu_data.get('temperature', 25.0)
            },
            'timestamp': datetime.now().isoformat()
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/navigation/pause', methods=['POST'])
def pause_navigation():
    """Pausiert die Navigation."""
    if not motor_instance:
        return jsonify({'error': 'Motor instance not available'}), 500
    
    try:
        # Implementierung für Pause-Funktionalität
        motor_instance.pause_autonomous_mowing()
        return jsonify({'status': 'paused', 'message': 'Navigation paused'})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/navigation/home', methods=['POST'])
def return_home():
    """Startet Rückkehr zur Basis."""
    if not motor_instance:
        return jsonify({'error': 'Motor instance not available'}), 500
    
    try:
        motor_instance.return_to_base()
        return jsonify({'status': 'returning', 'message': 'Returning to base'})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/map/current')
def get_current_map():
    """Gibt die aktuelle Karte zurück."""
    try:
        # Placeholder für Kartendaten
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
                {'x': 140, 'y': 75}
            ],
            'robot_position': {'x': 125, 'y': 75, 'heading': 90}
        }
        return jsonify(map_data)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/system/stats')
def get_system_stats():
    """Gibt System-Statistiken zurück."""
    try:
        # CPU Auslastung
        cpu_usage = psutil.cpu_percent(interval=1)
        
        # RAM Nutzung
        memory = psutil.virtual_memory()
        memory_usage = memory.percent
        
        # Festplatten-Nutzung
        disk = psutil.disk_usage('/')
        disk_usage = (disk.used / disk.total) * 100
        
        # CPU Temperatur (Linux spezifisch)
        cpu_temp = 45.0  # Placeholder
        try:
            if os.path.exists('/sys/class/thermal/thermal_zone0/temp'):
                with open('/sys/class/thermal/thermal_zone0/temp', 'r') as f:
                    cpu_temp = int(f.read()) / 1000.0
        except:
            pass
        
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
        # Placeholder für Update-Check
        return jsonify({
            'current_version': '1.0.0',
            'latest_version': '1.0.1',
            'update_available': True,
            'release_notes': 'Bugfixes und Verbesserungen',
            'download_url': 'https://github.com/user/sunray/releases/latest'
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/updates/install', methods=['POST'])
def install_update():
    """Installiert ein Update."""
    try:
        # Placeholder für Update-Installation
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
        firmware_path = data.get('firmware_path', '')
        
        if not firmware_path or not os.path.exists(firmware_path):
            return jsonify({'error': 'Firmware file not found'}), 400
        
        # Placeholder für Pico Flash-Prozess
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
    # Placeholder für Kamera-Stream
    return jsonify({
        'stream_url': '/api/camera/mjpeg',
        'resolution': '640x480',
        'fps': 15
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
                zones = []
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

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
