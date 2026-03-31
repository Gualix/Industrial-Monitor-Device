from __future__ import annotations

from app.config import ENGINE_ON_PRESSURE_THRESHOLD_PSI


class SensorService:
    def __init__(self, pressure_reader, temp_reader, alarm_service, runtime_service):
        self.pressure_reader = pressure_reader
        self.temp_reader = temp_reader
        self.alarm_service = alarm_service
        self.runtime_service = runtime_service

    def read_snapshot(self, elapsed_seconds: float = 0.0) -> dict:
        pressure_voltage = float(self.pressure_reader.read_voltage())
        pressure_psi = float(self.pressure_reader.voltage_to_psi(pressure_voltage))
        temperature_c = float(self.temp_reader.read_celsius())
        engine_on = pressure_psi >= ENGINE_ON_PRESSURE_THRESHOLD_PSI

        runtime = self.runtime_service.update_engine_state(
            engine_on=engine_on,
            elapsed_seconds=elapsed_seconds,
        )

        alarms = self.alarm_service.evaluate(
            pressure_psi=pressure_psi,
            temperature_c=temperature_c,
            hours_since_maintenance=float(runtime.get("hours_since_maintenance", 0.0)),
        )

        return {
            "sensors": {
                "pressure_psi": round(pressure_psi, 2),
                "pressure_voltage": round(pressure_voltage, 3),
                "temperature_c": round(temperature_c, 2),
                "engine_on": engine_on,
                "alarms": alarms,
            },
            "runtime": runtime,
        }
