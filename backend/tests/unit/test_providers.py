"""Unit tests for dynamic provider model discovery."""
from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

import httpx
import pytest
from fastapi.testclient import TestClient

from stromwart.api.providers import (
    DiscoveryResult,
    _discover_ollama,
    _discover_openai,
    _static_anthropic,
    discover_models,
    get_provider_guide,
)
from stromwart.app import create_app


@pytest.fixture
def client() -> TestClient:
    return TestClient(create_app())


@pytest.mark.asyncio
async def test_discover_ollama_returns_models() -> None:
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {
        "models": [{"name": "qwen2.5:latest"}, {"name": "llama3.2:latest"}],
    }

    mock_client = AsyncMock()
    mock_client.get = AsyncMock(return_value=mock_response)
    mock_client.__aenter__ = AsyncMock(return_value=mock_client)
    mock_client.__aexit__ = AsyncMock(return_value=None)

    with patch("stromwart.api.providers.httpx.AsyncClient", return_value=mock_client):
        result = await _discover_ollama("http://localhost:11434")

    assert result.status == "connected"
    assert result.models == ["qwen2.5:latest", "llama3.2:latest"]


@pytest.mark.asyncio
async def test_discover_ollama_unreachable_on_connect_error() -> None:
    with patch(
        "stromwart.api.providers._discover_ollama",
        side_effect=httpx.ConnectError("connection refused"),
    ):
        result = await discover_models("ollama", None)

    assert result.status == "unreachable"
    assert result.models == []


@pytest.mark.asyncio
async def test_discover_openai_requires_api_key() -> None:
    result = await _discover_openai(None)
    assert result.status == "auth_required"
    assert result.message == "API key required"


def test_static_anthropic_returns_models() -> None:
    result = _static_anthropic()
    assert result.status == "connected"
    assert len(result.models) == 4


def test_get_provider_guide_ollama() -> None:
    import asyncio

    guide = asyncio.run(get_provider_guide("ollama"))
    assert guide["title"] == "Ollama (Local, Free)"
    assert "ollama pull" in guide["setup_steps"]


def test_get_provider_guide_unknown() -> None:
    import asyncio

    from fastapi import HTTPException

    with pytest.raises(HTTPException) as exc_info:
        asyncio.run(get_provider_guide("unknown"))
    assert exc_info.value.status_code == 404


def test_discover_models_endpoint_openai_no_key(client: TestClient) -> None:
    response = client.post("/v1/settings/providers/openai/discover-models", json={})
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "auth_required"


def test_discover_models_endpoint_ollama_guide(client: TestClient) -> None:
    response = client.get("/v1/settings/providers/ollama/guide")
    assert response.status_code == 200
    assert response.json()["free"] == "true"


def test_discover_models_unknown_provider(client: TestClient) -> None:
    response = client.post("/v1/settings/providers/unknown/discover-models", json={})
    assert response.status_code == 404
