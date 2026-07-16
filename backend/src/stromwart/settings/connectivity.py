"""Fast connectivity probes for LLM providers."""

from __future__ import annotations

from stromwart.api.providers import (
    DiscoveryResult,
    _discover_gemini,
    _discover_groq,
    _discover_ollama,
    _discover_openai,
    _static_anthropic,
)


class ProbeOutcome:
    __slots__ = ("success", "message")

    def __init__(self, success: bool, message: str) -> None:
        self.success = success
        self.message = message


async def probe_provider(
    provider_id: str,
    model: str,
    api_key: str | None,
    endpoint: str | None,
) -> ProbeOutcome:
    """Lightweight connectivity check — no full LLM inference."""
    if provider_id == "disabled" or not provider_id:
        return ProbeOutcome(True, "LLM disabled")

    discovery = await _run_discovery(provider_id, api_key, endpoint)
    if discovery.status == "auth_required":
        return ProbeOutcome(False, discovery.message or "API key required")
    if discovery.status == "unreachable":
        return ProbeOutcome(False, discovery.message or "Provider unreachable")
    if discovery.status != "connected":
        return ProbeOutcome(False, discovery.message or "Provider unavailable")

    if model and discovery.models:
        model_found = any(
            model == listed or listed.startswith(f"{model}:") for listed in discovery.models
        )
        if not model_found:
            return ProbeOutcome(
                False,
                f"Model '{model}' not found. Available: {', '.join(discovery.models[:5])}",
            )

    if discovery.message and "no models installed" in discovery.message.lower():
        return ProbeOutcome(False, discovery.message)

    label = provider_id.capitalize()
    if model:
        return ProbeOutcome(True, f"Connected to {label} — model '{model}' is available")
    return ProbeOutcome(True, f"Connected to {label}")


async def _run_discovery(
    provider_id: str,
    api_key: str | None,
    endpoint: str | None,
) -> DiscoveryResult:
    match provider_id:
        case "ollama":
            return await _discover_ollama(endpoint or "http://localhost:11434")
        case "openai":
            return await _discover_openai(api_key)
        case "groq":
            return await _discover_groq(api_key)
        case "gemini":
            return await _discover_gemini(api_key)
        case "anthropic":
            return _static_anthropic()
        case _:
            return DiscoveryResult(
                models=[],
                status="unreachable",
                message=f"Unknown provider: {provider_id}",
            )
