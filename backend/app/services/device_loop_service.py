from __future__ import annotations

import threading
import time


class DeviceLoopService:
    def __init__(self, sensor_service, state_store, poll_interval_seconds: float = 1.0):
        self.sensor_service = sensor_service
        self.state_store = state_store
        self.poll_interval_seconds = poll_interval_seconds
        self._last_snapshot = None
        self._last_read_time = None
        self._thread = None
        self._running = False

    def start(self) -> None:
        if self._running:
            return
        self._running = True
        self._thread = threading.Thread(target=self._run, daemon=True)
        self._thread.start()

    def stop(self) -> None:
        self._running = False

    def get_snapshot(self) -> dict:
        if self._last_snapshot is None:
            snapshot = self.sensor_service.read_snapshot(elapsed_seconds=0.0)
            self._last_snapshot = snapshot
            self.state_store.write(snapshot)
            return snapshot
        return self._last_snapshot

    def _run(self) -> None:
        while self._running:
            now = time.time()
            elapsed = 0.0 if self._last_read_time is None else max(0.0, now - self._last_read_time)
            self._last_snapshot = self.sensor_service.read_snapshot(elapsed_seconds=elapsed)
            self.state_store.write(self._last_snapshot)
            self._last_read_time = now
            time.sleep(self.poll_interval_seconds)
