import time
import math
import board
import busio
import smbus2
import adafruit_bno08x
from adafruit_bno08x.i2c import BNO08X_I2C

class IMUSensor:
    """
    Liest Daten von einem BNO085-IMU-Sensor über I2C.
    Unterstützt erweiterte Sensorfusion und Neigungserkennung.
    """
    def __init__(self, i2c_bus=1, address=0x28):
        # Initialisierung über smbus2 für Raspberry Pi
        self.i2c = busio.I2C(board.SCL, board.SDA)
        self.sensor = BNO08X_I2C(self.i2c, address=address)
        
        # Aktivieren der benötigten Features
        self.sensor.enable_feature(adafruit_bno08x.BNO_REPORT_ACCELEROMETER)
        self.sensor.enable_feature(adafruit_bno08x.BNO_REPORT_GYROSCOPE)
        self.sensor.enable_feature(adafruit_bno08x.BNO_REPORT_MAGNETOMETER)
        self.sensor.enable_feature(adafruit_bno08x.BNO_REPORT_ROTATION_VECTOR)
        
        # Für Neigungserkennung
        self.sensor.enable_feature(adafruit_bno08x.BNO_REPORT_GEOMAGNETIC_ROTATION_VECTOR)
        
        # Kalibrierungsstatus
        self.calibrated = False
        self.last_read_time = time.time()

    def read(self) -> dict:
        """
        Gibt ein Dictionary mit aktuellen IMU-Werten zurück.
        Keys: acceleration, gyro, magnetic, euler, quaternion, temperature, tilt_warning
        """
        current_time = time.time()
        # Mindestens 10ms zwischen Lesevorgängen warten (BNO085 Anforderung)
        if current_time - self.last_read_time < 0.01:
            time.sleep(0.01)
        
        self.last_read_time = time.time()
        
        # Quaternion zu Euler-Winkeln konvertieren
        quat = self.sensor.quaternion
        euler = self._quaternion_to_euler(quat)
        
        # Neigungswarnung (>35 Grad)
        tilt_warning = abs(euler[1]) > 35 or abs(euler[2]) > 35
        
        return {
            'acceleration': self.sensor.acceleration,
            'gyro': self.sensor.gyro,
            'magnetic': self.sensor.magnetic,
            'euler': euler,  # (yaw, pitch, roll) in Grad
            'quaternion': quat,
            'heading': euler[0],  # Yaw-Winkel für Navigation
            'tilt_warning': tilt_warning,
        }
    
    def _quaternion_to_euler(self, quaternion):
        """
        Konvertiert Quaternion (w, x, y, z) zu Euler-Winkeln (yaw, pitch, roll) in Grad.
        """
        w, x, y, z = quaternion
        
        # Yaw (Z-Achse Rotation)
        t0 = 2.0 * (w * z + x * y)
        t1 = 1.0 - 2.0 * (y * y + z * z)
        yaw = math.degrees(math.atan2(t0, t1))
        
        # Pitch (Y-Achse Rotation)
        t2 = 2.0 * (w * y - z * x)
        t2 = 1.0 if t2 > 1.0 else t2
        t2 = -1.0 if t2 < -1.0 else t2
        pitch = math.degrees(math.asin(t2))
        
        # Roll (X-Achse Rotation)
        t3 = 2.0 * (w * x + y * z)
        t4 = 1.0 - 2.0 * (x * x + y * y)
        roll = math.degrees(math.atan2(t3, t4))
        
        return (yaw, pitch, roll)
    
    def is_tilted(self) -> bool:
        """
        Gibt True zurück, wenn der Roboter mehr als 35 Grad geneigt ist.
        """
        data = self.read()
        return data['tilt_warning']
