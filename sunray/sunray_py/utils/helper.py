import math
import random
import struct
from typing import Tuple, List

# Utility-Funktionen aus Sunray-Firmware portiert

def voltage_divider_uges(R1: float, R2: float, U2: float) -> float:
    """Spannungsteiler: Gesamtspannung berechnen."""
    return (U2 / R2) * (R1 + R2)

def adc2voltage(adc_value: float, io_ref: float = 3.3, resolution: int = 4095) -> float:
    """Wandelt ADC-Wert in Spannung um."""
    return (adc_value / resolution) * io_ref

def scale_pi(v: float) -> float:
    """Skaliert Winkel v auf -π..+π."""
    d = v
    while d < -math.pi:
        d += 2 * math.pi
    while d >= math.pi:
        d -= 2 * math.pi
    return d

def scale_180(v: float) -> float:
    """Skaliert Winkel v auf -180..+180 Grad."""
    d = v
    while d < -180:
        d += 360
    while d >= 180:
        d -= 360
    return d

def distance_pi(x: float, w: float) -> float:
    """Minimale Winkel-Differenz zwischen x und w in Rad."""
    return scale_pi(w - x)

def distance_180(x: float, w: float) -> float:
    """Minimale Winkel-Differenz zwischen x und w in Grad."""
    return scale_180(w - x)

def distance_line_infinite(px: float, py: float, x1: float, y1: float, x2: float, y2: float) -> float:
    """Abstand Punkt (px,py) zu unendlicher Linie durch (x1,y1)-(x2,y2)."""
    num = abs((y2 - y1)*px - (x2 - x1)*py + x2*y1 - y2*x1)
    den = math.hypot(y2 - y1, x2 - x1)
    return num / den if den != 0 else 0.0

def distance_line(px: float, py: float, x1: float, y1: float, x2: float, y2: float) -> float:
    """Abstand Punkt zu Strecken-Segment."""
    lx, ly = x2 - x1, y2 - y1
    l2 = lx*lx + ly*ly
    if l2 == 0:
        return math.hypot(px - x1, py - y1)
    u = ((px - x1)*lx + (py - y1)*ly) / l2
    u = max(0.0, min(1.0, u))
    x = x1 + u * lx
    y = y1 + u * ly
    return math.hypot(px - x, py - y)

def fusion_pi(w: float, a: float, b: float) -> float:
    """Gewichtete Mittelung zweier Winkeln in Rad."""
    # Sonderfälle um -π/π-Grenze
    if b >= math.pi/2 and a <= -math.pi/2:
        b -= 2*math.pi
    elif b <= -math.pi/2 and a >= math.pi/2:
        a -= 2*math.pi
    return scale_pi(w*a + (1-w)*b)

def scale_pi_angles(set_angle: float, curr_angle: float) -> float:
    """Skaliert set_angle so, dass Vorzeichen mit curr_angle übereinstimmt."""
    if set_angle >= math.pi/2 and curr_angle <= -math.pi/2:
        return set_angle - 2*math.pi
    if set_angle <= -math.pi/2 and curr_angle >= math.pi/2:
        return set_angle + 2*math.pi
    return set_angle

def distance(p0: Tuple[float, float], p1: Tuple[float, float]) -> float:
    """Euklidische Distanz zwischen zwei Punkten."""
    return math.hypot(p0[0] - p1[0], p0[1] - p1[1])

def sign(x: float) -> int:
    """Vorzeichenfunktion."""
    return -1 if x < 0 else 1

def deg2rad(deg: float) -> float:
    return math.radians(deg)

def rad2deg(rad: float) -> float:
    return math.degrees(rad)

def points_angle(x1: float, y1: float, x2: float, y2: float) -> float:
    """Winkel von (x1,y1) nach (x2,y2) in Rad."""
    return scale_pi(math.atan2(y2 - y1, x2 - x1))

def distance_ll(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Großkreisdistanz in Metern (Annäherung)."""
    # Haversine Formel
    R = 6372795.0
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlambda = math.radians(lon2 - lon1)
    a = math.sin(dphi/2)**2 + math.cos(phi1)*math.cos(phi2)*math.sin(dlambda/2)**2
    return 2 * R * math.atan2(math.sqrt(a), math.sqrt(1 - a))

def relative_ll(lat1: float, lon1: float, lat2: float, lon2: float) -> Tuple[float, float]:
    """Relative Nord/Ost-Distanz in Metern."""
    n = distance_ll(lat1, lon1, lat2, lon1)*(sign(lat2-lat1))
    e = distance_ll(lat1, lon1, lat1, lon2)*(sign(lon2-lon1))
    return n, e

def gauss_random() -> float:
    """Zufallswert ≈ Normalverteilung (0,1)."""
    return random.gauss(0, 1)

def gauss(mean: float, std_dev: float) -> float:
    return mean + gauss_random() * std_dev

def gaussian(mu: float, sigma: float, x: float) -> float:
    """1D-Gauß-Funktion."""
    return math.exp(-((mu - x)**2) / (2*sigma**2)) / math.sqrt(2*math.pi*sigma**2)

def parse_float_value(s: str, key: str) -> float:
    """Parst in 'key=Zahl' eingebetteten Float."""
    idx = s.find(f"{key}=")
    if idx < 0:
        return 0.0
    start = idx + len(key) + 1
    num = ''
    while start < len(s) and (s[start].isdigit() or s[start] in '.-'):
        num += s[start]
        start += 1
    try:
        return float(num)
    except ValueError:
        return 0.0

def to_eulerian_angle(w: float, x: float, y: float, z: float) -> Tuple[float, float, float]:
    """Konvertiert Quaternion zu (roll, pitch, yaw) in Rad."""
    ysqr = y * y
    t0 = +2.0 * (w * x + y * z)
    t1 = +1.0 - 2.0 * (x * x + ysqr)
    roll = math.atan2(t0, t1)
    t2 = +2.0 * (w * y - z * x)
    t2 = max(-1.0, min(1.0, t2))
    pitch = math.asin(t2)
    t3 = +2.0 * (w * z + x * y)
    t4 = +1.0 - 2.0 * (ysqr + z * z)
    yaw = math.atan2(t3, t4)
    return roll, pitch, yaw

def free_ram() -> int:
    """Stub für freien RAM (Plattform-spezifisch)."""
    return 0
