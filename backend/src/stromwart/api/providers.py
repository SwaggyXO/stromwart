"""Dynamic model discovery for LLM providers."""
from __future__ import annotations

import logging

import httpx
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from stromwart.settings.guides import PROVIDER_GUIDES

router = APIRouter(prefix="/settings/providers", tags=["providers"])
logger = logging.getLogger(__name__)

DISCOVERY_TIMEOUT = 5.0


class DiscoveryResult(BaseModel):
    models: list[str]
    status: str  # "connected" | "unreachable" | "auth_required" | "unsupported"
    message: str | None = None


class DiscoveryRequest(BaseModel):
    api_key: str | None = None
    endpoint: str | None = None


@router.post("/{provider_id}/discover-models", response_model=DiscoveryResult)
async def discover_models(
    provider_id: str,
    body: DiscoveryRequest | None = None,
) -> DiscoveryResult:
    """Probe a provider for available models at runtime."""
    body = body or DiscoveryRequest()

    try:
        match provider_id:
            case "ollama":
                return await _discover_ollama(body.endpoint or "http://localhost:11434")
            case "openai":
                return await _discover_openai(body.api_key)
            case "groq":
                return await _discover_groq(body.api_key)
            case "gemini":
                return await _discover_gemini(body.api_key)
            case "anthropic":
                return _static_anthropic()
            case "disabled":
                return DiscoveryResult(models=[], status="connected", message="LLM disabled")
            case _:
                raise HTTPException(status_code=404, detail=f"Unknown provider: {provider_id}")
    except HTTPException:
        raise
    except httpx.ConnectError:
        return DiscoveryResult(
            models=[], status="unreachable", message="Cannot reach provider endpoint"
        )
    except httpx.TimeoutException:
        return DiscoveryResult(models=[], status="unreachable", message="Connection timed out")
    except Exception as e:
        logger.warning("Discovery failed for %s: %s", provider_id, e)
        return DiscoveryResult(models=[], status="unreachable", message=str(e))


@router.get("/{provider_id}/guide")
async def get_provider_guide(provider_id: str) -> dict[str, str]:
    """Get setup guide for a provider."""
    guide = PROVIDER_GUIDES.get(provider_id)
    if not guide:
        raise HTTPException(status_code=404, detail=f"No guide for: {provider_id}")
    return guide


async def _discover_ollama(endpoint: str) -> DiscoveryResult:
    """Probe Ollama for installed models via /api/tags."""
    async with httpx.AsyncClient(timeout=DISCOVERY_TIMEOUT) as client:
        resp = await client.get(f"{endpoint}/api/tags")
        if resp.status_code == 200:
            data = resp.json()
            models = [m["name"] for m in data.get("models", [])]
            if not models:
                return DiscoveryResult(
                    models=[],
                    status="connected",
                    message="Ollama is running but no models installed. Run: ollama pull qwen2.5",
                )
            return DiscoveryResult(models=models, status="connected")
        return DiscoveryResult(models=[], status="unreachable", message=f"HTTP {resp.status_code}")


async def _discover_openai(api_key: str | None) -> DiscoveryResult:
    """Probe OpenAI models endpoint."""
    if not api_key:
        return DiscoveryResult(models=[], status="auth_required", message="API key required")

    async with httpx.AsyncClient(timeout=DISCOVERY_TIMEOUT) as client:
        resp = await client.get(
            "https://api.openai.com/v1/models",
            headers={"Authorization": f"Bearer {api_key}"},
        )
        if resp.status_code == 401:
            return DiscoveryResult(models=[], status="auth_required", message="Invalid API key")
        if resp.status_code == 200:
            data = resp.json()
            models = sorted(
                [
                    m["id"]
                    for m in data.get("data", [])
                    if "gpt" in m["id"] or "o1" in m["id"] or "o3" in m["id"]
                ],
                reverse=True,
            )
            return DiscoveryResult(models=models[:20], status="connected")
        return DiscoveryResult(models=[], status="unreachable", message=f"HTTP {resp.status_code}")


async def _discover_groq(api_key: str | None) -> DiscoveryResult:
    """Probe Groq models endpoint."""
    if not api_key:
        return DiscoveryResult(models=[], status="auth_required", message="API key required")

    async with httpx.AsyncClient(timeout=DISCOVERY_TIMEOUT) as client:
        resp = await client.get(
            "https://api.groq.com/openai/v1/models",
            headers={"Authorization": f"Bearer {api_key}"},
        )
        if resp.status_code == 401:
            return DiscoveryResult(models=[], status="auth_required", message="Invalid API key")
        if resp.status_code == 200:
            data = resp.json()
            models = sorted([m["id"] for m in data.get("data", [])])
            return DiscoveryResult(models=models, status="connected")
        return DiscoveryResult(models=[], status="unreachable", message=f"HTTP {resp.status_code}")


async def _discover_gemini(api_key: str | None) -> DiscoveryResult:
    """Probe Google Gemini models."""
    if not api_key:
        return DiscoveryResult(models=[], status="auth_required", message="API key required")

    async with httpx.AsyncClient(timeout=DISCOVERY_TIMEOUT) as client:
        resp = await client.get(
            f"https://generativelanguage.googleapis.com/v1beta/models?key={api_key}"
        )
        if resp.status_code in (400, 403):
            return DiscoveryResult(models=[], status="auth_required", message="Invalid API key")
        if resp.status_code == 200:
            data = resp.json()
            models = [
                m["name"].replace("models/", "")
                for m in data.get("models", [])
                if "generateContent" in str(m.get("supportedGenerationMethods", []))
            ]
            return DiscoveryResult(models=sorted(models), status="connected")
        return DiscoveryResult(models=[], status="unreachable", message=f"HTTP {resp.status_code}")


def _static_anthropic() -> DiscoveryResult:
    """Anthropic has no public models listing endpoint."""
    return DiscoveryResult(
        models=[
            "claude-sonnet-4-20250514",
            "claude-haiku-4-20250414",
            "claude-3-5-sonnet-20241022",
            "claude-3-5-haiku-20241022",
        ],
        status="connected",
        message="Static list (Anthropic has no models discovery API)",
    )
