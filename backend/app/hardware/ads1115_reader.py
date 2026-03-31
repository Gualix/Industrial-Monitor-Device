from __future__ import annotations

from app.config import (
    ADS1115_GAIN,
    ENABLE_HARDWARE_FALLBACKS,
    FALLBACK_PRESSURE_VOLTAGE,
    PRESSURE_SENSOR_MAX_PSI,
    PRESSURE_SENSOR_MAX_V,
    PRESSURE_SENSOR_MIN_PSI,
    PRESSURE_SENSOR_MIN_V,
)


class ADS1115Reader:
    def __init__(self, channel: int = 0, fallback_voltage: float = FALLBACK_PRESSURE_VOLTAGE):
        self.channel = channel
        self.fallback_voltage = fallback_voltage
        self.analog_in = None
        self._setup_reader()

    def _setup_reader(self) -> None:
        try:
            import board  # type: ignore
            import busio  # type: ignore
            import adafruit_ads1x15.ads1115 as ADS  # type: ignore
            from adafruit_ads1x15.analog_in import AnalogIn  # type: ignore

            i2c = busio.I2C(board.SCL, board.SDA)
            ads = ADS.ADS1115(i2c)
            ads.gain = ADS1115_GAIN
            self.analog_in = AnalogIn(ads, self.channel)

        except Exception:
            import traceback
            print("ADS1115 setup error:")
            traceback.print_exc()
            self.analog_in = None

    def read_voltage(self) -> float:
        if self.analog_in is not None:
            try:
                return float(self.analog_in.voltage)
            except Exception:
                pass

        if ENABLE_HARDWARE_FALLBACKS:
            return float(self.fallback_voltage)

        raise RuntimeError("ADS1115 pressure channel could not be read.")

    @staticmethod
    def voltage_to_psi(voltage: float) -> float:
        clamped = max(PRESSURE_SENSOR_MIN_V, min(PRESSURE_SENSOR_MAX_V, voltage))
        span_v = PRESSURE_SENSOR_MAX_V - PRESSURE_SENSOR_MIN_V
        span_psi = PRESSURE_SENSOR_MAX_PSI - PRESSURE_SENSOR_MIN_PSI
        ratio = (clamped - PRESSURE_SENSOR_MIN_V) / span_v
        return PRESSURE_SENSOR_MIN_PSI + (ratio * span_psi)