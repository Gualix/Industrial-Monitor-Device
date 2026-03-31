from __future__ import annotations


class MockGPIO:
    BCM = "BCM"
    OUT = "OUT"
    HIGH = 1
    LOW = 0

    def setmode(self, mode):
        self._mode = mode

    def setwarnings(self, enabled):
        return None

    def setup(self, pin, direction):
        return None

    def output(self, pin, state):
        return None

    def cleanup(self, pins=None):
        return None


try:
    import RPi.GPIO as GPIO  # type: ignore
except Exception:  # pragma: no cover
    GPIO = MockGPIO()
