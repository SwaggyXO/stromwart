from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml

from stromwart.settings.schema import SystemSettings


class SettingsStore:
    """
    Persist/load settings from a YAML file.
    Production: swap to DB-backed store.
    """

    def __init__(self, path: Path | None = None) -> None:
        self._path = path or Path("settings.yaml")
        self._settings = self._load()

    def get(self) -> SystemSettings:
        return self._settings

    def update(self, changes: dict[str, Any]) -> SystemSettings:
        current = self._settings.model_dump()
        current.update(changes)
        self._settings = SystemSettings.model_validate(current)
        self._save()
        return self._settings

    def _load(self) -> SystemSettings:
        if self._path.exists():
            with self._path.open(encoding="utf-8") as source:
                data = yaml.safe_load(source) or {}
            return SystemSettings.model_validate(data)
        return SystemSettings()

    def _save(self) -> None:
        with self._path.open("w", encoding="utf-8") as target:
            yaml.dump(
                self._settings.model_dump(exclude_none=True),
                target,
                default_flow_style=False,
            )
