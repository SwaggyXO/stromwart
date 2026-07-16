from __future__ import annotations

import httpx

from stromwart.providers.analyst import AnalystProvider
from stromwart.providers.anthropic import AnthropicProvider
from stromwart.providers.disabled import DisabledAnalystProvider
from stromwart.providers.openai_compatible import OpenAiCompatibleProvider


def create_provider(
    provider_id: str,
    model: str = "",
    api_key: str | None = None,
    endpoint: str | None = None,
    http_client: httpx.AsyncClient | None = None,
) -> AnalystProvider:
    """Factory for LLM providers. Returns DisabledAnalystProvider if not configured."""

    if provider_id == "disabled" or not provider_id:
        return DisabledAnalystProvider()

    client = http_client or httpx.AsyncClient(timeout=30.0)

    if provider_id == "anthropic":
        return AnthropicProvider(
            client=client,
            base_url="https://api.anthropic.com",
            api_key=api_key or "",
            model=model,
        )

    if provider_id == "openai":
        return OpenAiCompatibleProvider(
            client=client,
            base_url="https://api.openai.com/v1",
            api_key=api_key or "",
            model=model,
        )

    if provider_id == "groq":
        return OpenAiCompatibleProvider(
            client=client,
            base_url="https://api.groq.com/openai/v1",
            api_key=api_key or "",
            model=model,
        )

    if provider_id == "gemini":
        return OpenAiCompatibleProvider(
            client=client,
            base_url="https://generativelanguage.googleapis.com/v1beta/openai/",
            api_key=api_key or "",
            model=model,
        )

    if provider_id == "ollama":
        return OpenAiCompatibleProvider(
            client=client,
            base_url=endpoint or "http://localhost:11434/v1",
            api_key="ollama",
            model=model,
        )

    return DisabledAnalystProvider()
