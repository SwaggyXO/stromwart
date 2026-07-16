"""Setup guides for LLM providers."""

from __future__ import annotations

PROVIDER_GUIDES: dict[str, dict[str, str]] = {
    "ollama": {
        "title": "Ollama (Local, Free)",
        "description": "Run open-source models locally on your machine.",
        "setup_steps": (
            "1. Install: curl -fsSL https://ollama.com/install.sh | sh\n"
            "2. Pull a model: ollama pull qwen2.5\n"
            "3. Verify: ollama list\n"
            "4. Endpoint will be http://localhost:11434"
        ),
        "docs_url": "https://ollama.com/library",
        "free": "true",
        "requires_api_key": "false",
        "requires_endpoint": "true",
    },
    "groq": {
        "title": "Groq (Cloud, Free Tier)",
        "description": "Ultra-fast inference with generous free tier.",
        "setup_steps": (
            "1. Sign up at https://console.groq.com\n"
            "2. Go to API Keys → Create new key\n"
            "3. Copy key and paste below\n"
            "4. Free tier: 30 req/min, 14,400 req/day"
        ),
        "docs_url": "https://console.groq.com/keys",
        "free": "true",
        "requires_api_key": "true",
        "requires_endpoint": "false",
    },
    "gemini": {
        "title": "Google Gemini (Cloud, Free Tier)",
        "description": "Google's multimodal models with free API access.",
        "setup_steps": (
            "1. Go to https://aistudio.google.com/apikey\n"
            "2. Create an API key\n"
            "3. Copy key and paste below\n"
            "4. Free tier: 15 req/min, 1500 req/day"
        ),
        "docs_url": "https://aistudio.google.com/apikey",
        "free": "true",
        "requires_api_key": "true",
        "requires_endpoint": "false",
    },
    "openai": {
        "title": "OpenAI (Cloud, Paid)",
        "description": "GPT-4o and other OpenAI models. Requires billing.",
        "setup_steps": (
            "1. Sign up at https://platform.openai.com\n"
            "2. Add billing at Settings → Billing\n"
            "3. Create API key at Settings → API keys\n"
            "4. Copy key and paste below"
        ),
        "docs_url": "https://platform.openai.com/api-keys",
        "free": "false",
        "requires_api_key": "true",
        "requires_endpoint": "false",
    },
    "anthropic": {
        "title": "Anthropic Claude (Cloud, Paid)",
        "description": "Claude models for advanced reasoning. Requires billing.",
        "setup_steps": (
            "1. Sign up at https://console.anthropic.com\n"
            "2. Add billing information\n"
            "3. Create API key at Settings → API Keys\n"
            "4. Copy key and paste below"
        ),
        "docs_url": "https://console.anthropic.com/settings/keys",
        "free": "false",
        "requires_api_key": "true",
        "requires_endpoint": "false",
    },
}
