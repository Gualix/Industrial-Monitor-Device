from __future__ import annotations

import atexit
from pathlib import Path

from flask import Flask, send_from_directory

from app.api.routes_health import health_bp
from app.api.routes_runtime import runtime_bp
from app.api.routes_sensors import sensors_bp
from app.api.routes_settings import settings_bp
from app.config import (
    ADS1115_CHANNEL,
    API_HOST,
    API_PORT,
    BUZZER_1_GPIO,
    BUZZER_2_GPIO,
    DISPLAY_SIZE_INCHES,
    MAINTENANCE_INTERVAL_HOURS,
    MAINTENANCE_PASSWORD,
    LAST_STATE_FILE,
    POLL_INTERVAL_SECONDS,
    PRESSURE_LOW_PSI,
    RUNTIME_FILE,
    TEMP_HIGH_C,
)
from app.hardware.ads1115_reader import ADS1115Reader
from app.hardware.buzzer_controller import BuzzerController
from app.hardware.ds18b20_reader import DS18B20Reader
from app.services.alarm_service import AlarmService
from app.services.device_loop_service import DeviceLoopService
from app.services.maintenance_service import MaintenanceService
from app.services.runtime_service import RuntimeService
from app.services.sensor_service import SensorService
from app.storage.json_store import JsonStore


def create_app() -> Flask:
    frontend_dir = Path(__file__).resolve().parent.parent.parent / "frontend"
    app = Flask(__name__, static_folder=str(frontend_dir), static_url_path="")

    runtime_store = JsonStore(
        RUNTIME_FILE,
        {
            "total_engine_hours": 0.0,
            "hours_at_last_maintenance": 0.0,
            "hours_since_maintenance": 0.0,
            "engine_on": False,
            "last_update": None,
            "last_maintenance_reset": None,
        },
    )
    state_store = JsonStore(
        LAST_STATE_FILE,
        {
            "sensors": {
                "pressure_psi": 0.0,
                "pressure_voltage": 0.0,
                "temperature_c": 0.0,
                "engine_on": False,
                "alarms": {
                    "low_pressure": False,
                    "high_temperature": False,
                    "maintenance_due": False,
                    "active": False,
                },
            },
            "runtime": runtime_store.read(),
        },
    )

    runtime_service = RuntimeService(runtime_store)
    buzzer_controller = BuzzerController(BUZZER_1_GPIO, BUZZER_2_GPIO)
    alarm_service = AlarmService(
        buzzer_controller=buzzer_controller,
        pressure_low_psi=PRESSURE_LOW_PSI,
        temp_high_c=TEMP_HIGH_C,
        maintenance_interval_hours=MAINTENANCE_INTERVAL_HOURS,
    )
    pressure_reader = ADS1115Reader(channel=ADS1115_CHANNEL)
    temp_reader = DS18B20Reader()

    sensor_service = SensorService(
        pressure_reader=pressure_reader,
        temp_reader=temp_reader,
        alarm_service=alarm_service,
        runtime_service=runtime_service,
    )
    device_loop_service = DeviceLoopService(
        sensor_service=sensor_service,
        state_store=state_store,
        poll_interval_seconds=POLL_INTERVAL_SECONDS,
    )
    maintenance_service = MaintenanceService(
        runtime_service=runtime_service,
        password=MAINTENANCE_PASSWORD,
    )

    app.config["runtime_service"] = runtime_service
    app.config["maintenance_service"] = maintenance_service
    app.config["device_loop_service"] = device_loop_service
    app.config["public_settings"] = {
        "display_inches": DISPLAY_SIZE_INCHES,
        "maintenance_interval_hours": MAINTENANCE_INTERVAL_HOURS,
        "pressure_low_psi": PRESSURE_LOW_PSI,
        "temp_high_c": TEMP_HIGH_C,
        "buzzer_pins": [BUZZER_1_GPIO, BUZZER_2_GPIO],
    }

    app.register_blueprint(health_bp)
    app.register_blueprint(runtime_bp)
    app.register_blueprint(sensors_bp)
    app.register_blueprint(settings_bp)

    @app.get("/")
    def index():
        return send_from_directory(app.static_folder, "index.html")

    @app.get("/<path:path>")
    def static_proxy(path: str):
        return send_from_directory(app.static_folder, path)

    device_loop_service.start()
    atexit.register(device_loop_service.stop)
    atexit.register(buzzer_controller.cleanup)

    return app


def run() -> None:
    app = create_app()
    app.run(host=API_HOST, port=API_PORT, debug=False)


if __name__ == "__main__":
    run()
