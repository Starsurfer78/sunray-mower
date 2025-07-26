import datetime
from enum import Enum
from typing import Optional

class EventCode(Enum):
    SYSTEM_STARTING = "system_starting"
    SYSTEM_STARTED = "system_started"
    SYSTEM_RESTARTING = "system_restarting"
    SYSTEM_SHUTTING_DOWN = "system_shutting_down"
    SYSTEM_STARTING_FAILED = "system_starting_failed"
    WIFI_CONNECTED = "wifi_connected"
    APP_CONNECTED = "app_connected"
    IMU_CALIBRATING = "imu_calibrating"
    ERROR_GPS_NOT_CONNECTED = "error_gps_not_connected"
    ERROR_IMU_NOT_CONNECTED = "error_imu_not_connected"
    ERROR_IMU_TIMEOUT = "error_imu_timeout"
    ERROR_BATTERY_UNDERVOLTAGE = "error_battery_undervoltage"
    TILT_WARNING = "tilt_warning"  # Warnung bei zu starker Neigung (>35°)
    OBSTACLE_DETECTED = "obstacle_detected"  # Hindernis erkannt
    GPS_FIX_LOST = "gps_fix_lost"  # GPS-Fix verloren
    GPS_FIX_ACQUIRED = "gps_fix_acquired"  # GPS-Fix erhalten
    RTK_FIX_ACQUIRED = "rtk_fix_acquired"  # RTK-Fix erhalten
    # ... weitere Codes nach Bedarf ...

class EventLogger:
    """
    Protokolliert Ereignisse mit Zeitstempel.
    """
    def __init__(self, logfile: Optional[str] = None):
        self.logfile = logfile

    def _timestamp(self) -> str:
        return datetime.datetime.now().isoformat()

    def event(self, evt: EventCode, additional_data: Optional[str] = None) -> None:
        """
        Protokolliert ein Ereignis.
        evt: EventCode
        additional_data: optionale Zusatzinformationen
        """
        ts = self._timestamp()
        line = f"{ts} - {evt.value}"
        if additional_data:
            line += f" - {additional_data}"
        if self.logfile:
            with open(self.logfile, "a") as f:
                f.write(line + "\n")
        else:
            print(line)

# Globaler Logger
Logger = EventLogger()
