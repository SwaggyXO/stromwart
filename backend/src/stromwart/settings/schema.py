from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field


class DataSourceConfig(BaseModel):
    type: Literal["simulation", "prometheus", "websocket", "file"] = "simulation"
    endpoint: str | None = None
    scenario_id: str | None = None
    active: bool = False
    label: str = "Demo Scenario"


class SystemSettings(BaseModel):
    """User-configurable system settings. Persisted to DB or YAML."""

    # ─── LLM Provider ─────────────────────────────────────────
    llm_provider: Literal[
        "disabled", "groq", "gemini", "ollama", "openai", "anthropic"
    ] = "disabled"
    llm_model: str = ""
    llm_endpoint: str | None = None  # For ollama/lmstudio (e.g., http://localhost:11434)
    llm_api_key: str | None = None  # Encrypted at rest in production
    llm_discovered_models: list[str] = Field(default_factory=list)
    llm_connection_verified: bool = False

    # ─── ML Models ─────────────────────────────────────────────
    qoe_model_path: str = "models/qoe_gbm.joblib"
    forecaster_model_path: str = "models/quantile_forecaster.joblib"

    # ─── Alerting Thresholds ──────────────────────────────────
    alert_mos_threshold: float = Field(default=3.5, ge=1.0, le=5.0)
    alert_buffer_ratio_threshold: float = Field(default=3.0, ge=0.0, le=100.0)
    alert_stall_count_threshold: int = Field(default=5, ge=0)

    # ─── Policy Thresholds ────────────────────────────────────
    policy_min_confidence: float = Field(default=0.6, ge=0.0, le=1.0)
    policy_max_blast_radius: int = Field(default=50_000, ge=0)
    policy_max_prediction_interval: float = Field(default=1.5, ge=0.0)
    policy_high_risk_threshold: float = Field(default=0.7, ge=0.0, le=1.0)

    # ─── Agent Configuration ──────────────────────────────────
    detector_enabled: bool = True
    diagnostician_enabled: bool = True
    mitigator_enabled: bool = True
    verifier_enabled: bool = True
    autonomy_level: Literal["observe_only", "recommend", "auto_simulate", "auto_execute"] = (
        "recommend"
    )
    max_retries: int = Field(default=2, ge=0, le=5)
    agent_step_budget: int = Field(default=10, ge=1, le=50)
    agent_time_budget_seconds: float = Field(default=30.0, ge=1.0, le=300.0)

    # ─── Eval Configuration ───────────────────────────────────
    eval_enabled: bool = True
    eval_llm_judge_enabled: bool = False
    eval_trace_sample_rate: float = Field(default=1.0, ge=0.0, le=1.0)

    # ─── MCP Configuration ────────────────────────────────────
    mcp_server_enabled: bool = True
    mcp_external_servers: list[dict[str, str]] = Field(default_factory=list)

    # ─── Data Sources ─────────────────────────────────────────
    data_sources: list[DataSourceConfig] = Field(
        default_factory=lambda: [
            DataSourceConfig(type="simulation", label="Demo Scenario", active=True),
            DataSourceConfig(type="prometheus", label="Prometheus", active=False),
            DataSourceConfig(type="websocket", label="Custom WebSocket", active=False),
        ]
    )


class ProviderInfo(BaseModel):
    """Information about an available LLM provider."""

    id: str
    name: str
    description: str
    requires_api_key: bool
    requires_endpoint: bool
    free_tier: bool
    models: list[str]


AVAILABLE_PROVIDERS: list[ProviderInfo] = [
    ProviderInfo(
        id="disabled",
        name="Disabled",
        description="No LLM — system runs on ML models + rules only",
        requires_api_key=False,
        requires_endpoint=False,
        free_tier=True,
        models=[],
    ),
    ProviderInfo(
        id="groq",
        name="Groq",
        description="Fast inference, free tier with rate limits",
        requires_api_key=True,
        requires_endpoint=False,
        free_tier=True,
        models=["llama-3.3-70b-versatile", "llama-3.1-8b-instant", "mixtral-8x7b-32768"],
    ),
    ProviderInfo(
        id="gemini",
        name="Google Gemini",
        description="Google AI, free tier available",
        requires_api_key=True,
        requires_endpoint=False,
        free_tier=True,
        models=["gemini-2.0-flash", "gemini-2.0-flash-lite", "gemini-1.5-flash"],
    ),
    ProviderInfo(
        id="ollama",
        name="Ollama / LMStudio",
        description="Local models on your hardware",
        requires_api_key=False,
        requires_endpoint=True,
        free_tier=True,
        models=["llama3.3", "mistral", "phi-4", "qwen2.5"],
    ),
    ProviderInfo(
        id="openai",
        name="OpenAI",
        description="GPT models (paid)",
        requires_api_key=True,
        requires_endpoint=False,
        free_tier=False,
        models=["gpt-4o", "gpt-4o-mini"],
    ),
    ProviderInfo(
        id="anthropic",
        name="Anthropic",
        description="Claude models (paid)",
        requires_api_key=True,
        requires_endpoint=False,
        free_tier=False,
        models=["claude-sonnet-4-20250514", "claude-haiku-3-5-20241022"],
    ),
]
