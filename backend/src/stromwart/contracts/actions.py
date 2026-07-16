from datetime import datetime
from enum import StrEnum
from uuid import UUID

from pydantic import ConfigDict, Field

from stromwart.contracts.common import ApiModel


class ProposalState(StrEnum):
    OBSERVE = "observe"
    INVESTIGATE = "investigate"
    SIMULATE = "simulate"
    APPROVAL_REQUIRED = "approval_required"
    APPROVED = "approved"
    BLOCKED = "blocked"


class ProposalCreate(ApiModel):
    """Propose a mitigation action for an incident."""

    action_type: str = Field(
        min_length=1,
        max_length=100,
        description=(
            "Action from allowlist: increase_cdn_capacity, adjust_traffic_routing, "
            "recommend_abr_profile, investigate_only"
        ),
    )
    target_scope: dict[str, str | int | float | bool | None] = Field(
        description="Scope of the action (must include session_count)",
    )
    rationale: str = Field(
        min_length=1, max_length=4000, description="Evidence-grounded justification"
    )
    expected_effect: str = Field(
        min_length=1, max_length=1000, description="Projected outcome description"
    )
    confidence: float = Field(ge=0, le=1, description="Analyst confidence in the recommendation")
    risk_score: float = Field(ge=0, le=1, description="Estimated risk of the action itself")
    evidence_ids: list[UUID] = Field(
        min_length=1, description="Alert/evidence IDs supporting this proposal"
    )
    prediction_interval_width: float | None = Field(
        default=None,
        ge=0,
        description="Width of the QoE prediction interval (used by guardrails)",
    )
    drift_active: bool = Field(
        default=False, description="Whether model drift is currently detected"
    )

    model_config = ConfigDict(
        extra="forbid",
        populate_by_name=True,
        json_schema_extra={
            "examples": [
                {
                    "action_type": "adjust_traffic_routing",
                    "target_scope": {
                        "region": "EU-West",
                        "cdn_edge_id": "CDN-A",
                        "session_count": 45000,
                    },
                    "rationale": (
                        "CDN-A Frankfurt edge showing 42% stall rate "
                        "correlated with packet loss burst"
                    ),
                    "expected_effect": (
                        "Reroute to CDN-B (68% spare capacity) reducing stall rate to <5%"
                    ),
                    "confidence": 0.84,
                    "risk_score": 0.22,
                    "evidence_ids": ["a1b2c3d4-e5f6-7890-abcd-ef1234567890"],
                    "drift_active": False,
                    "prediction_interval_width": 0.68,
                }
            ]
        },
    )


class ProposalRead(ProposalCreate):
    id: UUID
    incident_id: UUID
    state: ProposalState
    policy_reasons: list[str]
    created_at: datetime


class ApprovalCreate(ApiModel):
    approved: bool
    actor_id: str = Field(min_length=1, max_length=200)
    reason: str = Field(min_length=1, max_length=1000)


class RejectCreate(ApiModel):
    """Reject a proposal awaiting human approval."""

    actor_id: str = Field(min_length=1, max_length=200)
    reason: str = Field(min_length=1, max_length=1000)


class SimulationRead(ApiModel):
    proposal_id: UUID
    successful: bool
    projected_risk_reduction: float = Field(ge=0, le=1)
    projected_affected_sessions: int = Field(ge=0)
    explanation: str
