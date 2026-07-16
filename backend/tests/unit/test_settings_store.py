"""Settings store persistence tests."""
from __future__ import annotations

from pathlib import Path

from stromwart.settings.schema import SystemSettings
from stromwart.settings.store import SettingsStore


def test_discovered_models_round_trip(tmp_path: Path) -> None:
    path = tmp_path / "settings.yaml"
    store = SettingsStore(path)
    updated = store.update(
        {
            "llm_provider": "groq",
            "llm_model": "llama-3.3-70b-versatile",
            "llm_discovered_models": ["llama-3.3-70b-versatile", "mixtral-8x7b-32768"],
            "llm_connection_verified": True,
        }
    )
    assert updated.llm_discovered_models == [
        "llama-3.3-70b-versatile",
        "mixtral-8x7b-32768",
    ]
    assert updated.llm_connection_verified is True

    reloaded = SettingsStore(path).get()
    assert isinstance(reloaded, SystemSettings)
    assert reloaded.llm_discovered_models == updated.llm_discovered_models
