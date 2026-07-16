from datetime import datetime
from enum import StrEnum
from uuid import UUID

from pydantic import Field

from stromwart.contracts.common import ApiModel


class AgentRunState(StrEnum):
    GATHERING_EVIDENCE = "gathering_evidence"
    REFLECTION_REQUIRED = "reflection_required"
    WAITING_FOR_HUMAN = "waiting_for_human"
    COMPLETED = "completed"
    REJECTED = "rejected"
    FAILED = "failed"


class ToolName(StrEnum):
    INCIDENT = "incident"
    TELEMETRY = "telemetry"
    FEATURES = "features"
    PREDICTIONS = "predictions"
    FORECASTS = "forecasts"
    TOPOLOGY = "topology"
    RUNBOOK = "runbook"


class ToolCall(ApiModel):
    name: ToolName
    arguments: dict[str, str | int | float | bool | None]


class ToolResult(ApiModel):
    call: ToolCall
    output: dict[str, object]
    evidence_ids: list[UUID] = Field(default_factory=list)


class AnalystFinding(ApiModel):
    """Structured output from the LLM incident analyst."""

    hypothesis: str = Field(
        min_length=1,
        max_length=2000,
        description="Root cause hypothesis grounded in cited evidence",
    )
    confidence: float = Field(ge=0, le=1, description="Analyst self-assessed confidence")
    evidence_ids: list[UUID] = Field(
        min_length=1,
        description="UUIDs of evidence items supporting the hypothesis",
    )
    missing_evidence: list[str] = Field(
        description="Data the analyst needs but doesn't have",
    )
    recommended_action: str = Field(
        min_length=1,
        max_length=100,
        description="Suggested mitigation from the action allowlist",
    )
    rationale: str = Field(
        min_length=1,
        max_length=4000,
        description="Detailed reasoning chain",
    )


class ReflectionResult(ApiModel):
    accepted: bool
    reasons: list[str]


class HumanFeedback(ApiModel):
    approved: bool
    actor_id: str = Field(min_length=1, max_length=200)
    feedback: str = Field(min_length=1, max_length=2000)


class AgentRunRead(ApiModel):
    id: UUID
    incident_id: UUID
    state: AgentRunState
    workflow_data: dict[str, object]
    created_at: datetime
