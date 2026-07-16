from __future__ import annotations

from datetime import UTC, datetime
from enum import StrEnum
from typing import Any

from pydantic import BaseModel, Field


class IncidentPhase(StrEnum):
    IDLE = "idle"
    DETECTING = "detecting"
    DIAGNOSING = "diagnosing"
    MITIGATING = "mitigating"
    VERIFYING = "verifying"
    ESCALATED = "escalated"
    RESOLVED = "resolved"


class AgentStepRecord(BaseModel):
    agent_name: str
    action: str
    observation: dict[str, Any] = Field(default_factory=dict)
    timestamp: datetime = Field(default_factory=lambda: datetime.now(UTC))
    duration_ms: float = 0.0
    success: bool = True
    error: str | None = None
    stop_reason: str | None = None
    llm_enriched: bool = False
    step_reflection: dict[str, Any] = Field(default_factory=dict)


class CognitiveState(BaseModel):
    """Shared memory for the OODA supervisor. Fully serializable."""

    event_id: str | None = None
    incident_id: str | None = None
    correlation_id: str = ""

    phase: IncidentPhase = IncidentPhase.IDLE
    retry_count: int = 0
    max_retries: int = 2

    # Observe
    latest_kpis: dict[str, float] = Field(default_factory=dict)
    unprocessed_alerts: list[dict[str, Any]] = Field(default_factory=list)
    active_sessions_count: int = 0

    # Orient (contextualized by ML models)
    severity_classification: str | None = None
    qoe_prediction: float | None = None
    prediction_confidence: float | None = None
    forecast_trend: str | None = None  # "degrading" | "stable" | "improving"
    drift_detected: bool = False

    # Decide outputs
    current_decision: str | None = None
    decision_reasons: list[str] = Field(default_factory=list)

    # Act outputs
    detection_result: dict[str, Any] | None = None
    diagnosis_result: dict[str, Any] | None = None
    mitigation_proposal: dict[str, Any] | None = None
    verification_result: dict[str, Any] | None = None

    # Reflexion memory
    reflection_feedback: list[str] = Field(default_factory=list)
    step_history: list[AgentStepRecord] = Field(default_factory=list)

    # Flags
    has_unprocessed_alerts: bool = False
    detection_complete: bool = False
    diagnosis_complete: bool = False
    mitigation_proposed: bool = False
    action_executed: bool = False
    action_verified: bool = False
    verification_failed: bool = False
    human_escalation_required: bool = False

    def reset_for_new_incident(self) -> None:
        self.phase = IncidentPhase.IDLE
        self.retry_count = 0
        self.detection_result = None
        self.diagnosis_result = None
        self.mitigation_proposal = None
        self.verification_result = None
        self.reflection_feedback = []
        self.step_history = []
        self.detection_complete = False
        self.diagnosis_complete = False
        self.mitigation_proposed = False
        self.action_executed = False
        self.action_verified = False
        self.verification_failed = False
        self.human_escalation_required = False
