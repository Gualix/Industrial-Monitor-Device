from __future__ import annotations

from flask import Blueprint, current_app, jsonify

settings_bp = Blueprint("settings", __name__)


@settings_bp.get("/api/settings")
def get_settings():
    return jsonify(current_app.config["public_settings"])
