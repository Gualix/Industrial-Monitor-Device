from __future__ import annotations

from flask import Blueprint, current_app, jsonify

sensors_bp = Blueprint("sensors", __name__)


@sensors_bp.get("/api/sensors")
def get_sensors():
    snapshot = current_app.config["device_loop_service"].get_snapshot()
    return jsonify(snapshot["sensors"])


@sensors_bp.get("/api/state")
def get_state():
    return jsonify(current_app.config["device_loop_service"].get_snapshot())
