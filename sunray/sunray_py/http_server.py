from flask import Flask, request, jsonify
from imu import IMUSensor
from gps_module import GPSModule
from pico_comm import PicoComm

app = Flask(__name__)
imu = IMUSensor()
gps = GPSModule()
comm = PicoComm(port='/dev/ttyS0', baudrate=115200)

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
    comm.send_command(cmd)
    return jsonify({'status': 'sent', 'command': cmd})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
