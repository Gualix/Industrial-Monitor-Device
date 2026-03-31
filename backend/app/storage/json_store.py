from __future__ import annotations

import json
from pathlib import Path
from typing import Any


class JsonStore:
    def __init__(self, path: Path, default_data: dict[str, Any]):
        self.path = path
        self.default_data = default_data
        self.path.parent.mkdir(parents=True, exist_ok=True)
        if not self.path.exists():
            self.write(self.default_data.copy())

    def read(self) -> dict[str, Any]:
        try:
            with self.path.open("r", encoding="utf-8") as file:
                return json.load(file)
        except Exception:
            return self.default_data.copy()

    def write(self, data: dict[str, Any]) -> None:
        with self.path.open("w", encoding="utf-8") as file:
            json.dump(data, file, indent=2, ensure_ascii=False)
