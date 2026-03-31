from __future__ import annotations

from pathlib import Path

from app.config import ENABLE_HARDWARE_FALLBACKS, FALLBACK_TEMPERATURE_C


class DS18B20Reader:
    def __init__(self, fallback_temp_c: float = FALLBACK_TEMPERATURE_C):
        self.fallback_temp_c = fallback_temp_c
        self.sysfs_base = Path("/sys/bus/w1/devices")
        self.sensor = None
        self._setup_library_sensor()

    def _setup_library_sensor(self) -> None:
        try:
            from w1thermsensor import W1ThermSensor  # type: ignore
            self.sensor = W1ThermSensor()
        except Exception:
            self.sensor = None

    def _read_from_w1thermsensor(self) -> float | None:
        if self.sensor is None:
            return None
        try:
            return float(self.sensor.get_temperature())
        except Exception:
            return None

    def _read_from_sysfs(self) -> float | None:
        try:
            for device_dir in self.sysfs_base.glob("28-*"):
                sensor_file = device_dir / "w1_slave"
                if not sensor_file.exists():
                    continue
                content = sensor_file.read_text(encoding="utf-8").strip().splitlines()
                if len(content) < 2 or not content[0].strip().endswith("YES"):
                    continue
                token = "t="
                index = content[1].find(token)
                if index == -1:
                    continue
                value = int(content[1][index + len(token):])
                return value / 1000.0
        except Exception:
            return None
        return None

    def read_celsius(self) -> float:
        value = self._read_from_w1thermsensor()
        if value is not None:
            return value

        value = self._read_from_sysfs()
        if value is not None:
            return value

        if ENABLE_HARDWARE_FALLBACKS:
            return float(self.fallback_temp_c)

        raise RuntimeError("DS18B20 sensor could not be read.")
