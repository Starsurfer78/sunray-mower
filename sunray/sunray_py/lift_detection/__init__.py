"""Lift Detection Package

Dieses Paket enthält alternative Lift-Erkennungsmethoden ohne Hardware-Sensor.
"""

from .lift_detection_alternatives import AlternativeLiftDetector, LiftDetectionResult
from .integration_lift_alternatives import IntegratedLiftSafety

__all__ = [
    'AlternativeLiftDetector',
    'LiftDetectionResult', 
    'IntegratedLiftSafety'
]