from __future__ import annotations

from flask import Blueprint, current_app, jsonify, request

runtime_bp = Blueprint("runtime", __name__)


@runtime_bp.get("/api/runtime")
def get_runtime():
    return jsonify(current_app.config["runtime_service"].get_runtime_data())


@runtime_bp.post("/api/runtime/reset-maintenance")
def reset_maintenance():
    payload = request.get_json(silent=True) or {}
    password = str(payload.get("password", ""))

    ok, data = current_app.config["maintenance_service"].reset(password)
    if not ok:
        return jsonify({"ok": False, **data}), 403

    return jsonify({"ok": True, "data": data})
