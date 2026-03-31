from __future__ import annotations


class MaintenanceService:
    def __init__(self, runtime_service, password: str):
        self.runtime_service = runtime_service
        self.password = password

    def validate_password(self, password: str) -> bool:
        return password == self.password

    def reset(self, password: str) -> tuple[bool, dict]:
        if not self.validate_password(password):
            return False, {"error": "Invalid password"}
        return True, self.runtime_service.reset_maintenance_counter()
