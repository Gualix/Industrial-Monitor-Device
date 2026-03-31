from __future__ import annotations


class AlarmService:
    def __init__(
        self,
        buzzer_controller,
        pressure_low_psi: float,
        temp_high_c: float,
        maintenance_interval_hours: float,
    ):
        self.buzzer_controller = buzzer_controller
        self.pressure_low_psi = pressure_low_psi
        self.temp_high_c = temp_high_c
        self.maintenance_interval_hours = maintenance_interval_hours

    def evaluate(self, pressure_psi: float, temperature_c: float, hours_since_maintenance: float) -> dict:
        low_pressure = pressure_psi < self.pressure_low_psi
        high_temperature = temperature_c > self.temp_high_c
        maintenance_due = hours_since_maintenance >= self.maintenance_interval_hours

        alarms = {
            "low_pressure": low_pressure,
            "high_temperature": high_temperature,
            "maintenance_due": maintenance_due,
        }
        alarms["active"] = any(alarms.values())

        self.buzzer_controller.set_alarm_active(alarms["active"])
        return alarms
