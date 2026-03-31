from __future__ import annotations

import threading
import time

from app.hardware.gpio_compat import GPIO


class BuzzerController:
    def __init__(self, pin_one: int, pin_two: int):
        self.pin_one = pin_one
        self.pin_two = pin_two
        self._initialized = False
        self._alarm_active = False
        self._thread = None
        self._lock = threading.Lock()
        self._setup()

    def _setup(self) -> None:
        GPIO.setwarnings(False)
        GPIO.setmode(GPIO.BCM)
        GPIO.setup(self.pin_one, GPIO.OUT)
        GPIO.setup(self.pin_two, GPIO.OUT)
        self._write(GPIO.LOW)
        self._initialized = True

    def _write(self, state) -> None:
        GPIO.output(self.pin_one, state)
        GPIO.output(self.pin_two, state)

    def set_alarm_active(self, active: bool) -> None:
        with self._lock:
            self._alarm_active = bool(active)
        if active:
            if self._thread is None or not self._thread.is_alive():
                self._thread = threading.Thread(target=self._alarm_loop, daemon=True)
                self._thread.start()
        else:
            self._write(GPIO.LOW)

    def _alarm_loop(self) -> None:
        while True:
            with self._lock:
                active = self._alarm_active
            if not active:
                self._write(GPIO.LOW)
                break
            self._write(GPIO.HIGH)
            time.sleep(0.25)
            with self._lock:
                active = self._alarm_active
            if not active:
                self._write(GPIO.LOW)
                break
            self._write(GPIO.LOW)
            time.sleep(0.20)

    def on(self) -> None:
        self.set_alarm_active(True)

    def off(self) -> None:
        self.set_alarm_active(False)

    def cleanup(self) -> None:
        self.off()
        if self._initialized:
            GPIO.cleanup([self.pin_one, self.pin_two])
            self._initialized = False
