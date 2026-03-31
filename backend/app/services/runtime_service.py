from __future__ import annotations

from datetime import datetime


class RuntimeService:
    def __init__(self, runtime_store):
        self.runtime_store = runtime_store

    def get_runtime_data(self) -> dict:
        return self.runtime_store.read()

    def update_engine_state(self, engine_on: bool, elapsed_seconds: float) -> dict:
        data = self.runtime_store.read()

        total_hours = float(data.get("total_engine_hours", 0.0))
        hours_at_last_maintenance = float(data.get("hours_at_last_maintenance", 0.0))

        if engine_on:
            total_hours += max(0.0, elapsed_seconds) / 3600.0

        data["total_engine_hours"] = round(total_hours, 4)
        data["hours_since_maintenance"] = round(total_hours - hours_at_last_maintenance, 4)
        data["engine_on"] = bool(engine_on)
        data["last_update"] = datetime.utcnow().isoformat() + "Z"

        self.runtime_store.write(data)
        return data

    def reset_maintenance_counter(self) -> dict:
        data = self.runtime_store.read()
        total_hours = float(data.get("total_engine_hours", 0.0))

        data["hours_at_last_maintenance"] = round(total_hours, 4)
        data["hours_since_maintenance"] = 0.0
        data["last_maintenance_reset"] = datetime.utcnow().isoformat() + "Z"

        self.runtime_store.write(data)
        return data
