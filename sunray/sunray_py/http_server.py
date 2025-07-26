from flask import Flask, request, jsonify
from imu import IMUSensor
from gps_module import GPSModule
from hardware_manager import get_hardware_manager
from path_planner import MowPattern
from map import Point, Polygon
from enhanced_escape_operations import SensorFusion, LearningSystem, AdaptiveEscapeOp
from examples.integration_example import EnhancedSunrayController
from smart_button_controller import get_smart_button_controller, ButtonAction

app = Flask(__name__)
imu = IMUSensor()
gps = GPSModule()
hw_manager = get_hardware_manager(port='/dev/ttyS0', baudrate=115200)

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

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
