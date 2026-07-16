"""Unit tests for fast provider connectivity test endpoint."""
from __future__ import annotations

from unittest.mock import AsyncMock, patch

import pytest
from fastapi.testclient import TestClient

from stromwart.api.providers import DiscoveryResult
from stromwart.app import create_app
from stromwart.settings.connectivity import probe_provider


@pytest.fixture
def client() -> TestClient:
    return TestClient(create_app())


@pytest.mark.asyncio
async def test_probe_disabled_provider() -> None:
    outcome = await probe_provider("disabled", "", None, None)
    assert outcome.success is True


@pytest.mark.asyncio
async def test_probe_openai_requires_key() -> None:
    outcome = await probe_provider("openai", "gpt-4o", None, None)
    assert outcome.success is False
    assert "API key" in outcome.message


def test_test_provider_endpoint_disabled(client: TestClient) -> None:
    response = client.post(
        "/v1/settings/providers/test",
        params={"provider_id": "disabled", "model": ""},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert "latency_ms" in data


def test_test_provider_endpoint_openai_no_key(client: TestClient) -> None:
    response = client.post(
        "/v1/settings/providers/test",
        params={"provider_id": "openai", "model": "gpt-4o"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is False
    assert data["message"]


@pytest.mark.asyncio
async def test_probe_ollama_model_check() -> None:
    discovery = DiscoveryResult(
        models=["qwen2.5:latest"],
        status="connected",
    )
    with patch(
        "stromwart.settings.connectivity._run_discovery",
        new_callable=AsyncMock,
        return_value=discovery,
    ):
        ok = await probe_provider("ollama", "qwen2.5", None, "http://localhost:11434")
        assert ok.success is True

        bad = await probe_provider("ollama", "missing-model", None, "http://localhost:11434")
        assert bad.success is False
