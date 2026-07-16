from datetime import datetime

from pydantic import ConfigDict, Field

from stromwart.contracts.common import ApiModel


class LiveIncidentSummary(ApiModel):
    """Compact incident representation for SSE stream."""

    incident_id: str = Field(description="Incident UUID")
    severity: str = Field(description="Alert severity level")
    state: str = Field(description="Incident lifecycle state")
    slice_key: str = Field(description="Affected topology slice")


class LiveEventUpdate(ApiModel):
    """Single SSE payload for a live event stream."""

    event_id: str = Field(description="Event UUID")
    active_sessions: int = Field(ge=0, description="Currently active session count")
    total_sessions: int = Field(ge=0, description="Total provisioned sessions for event")
    incidents: list[LiveIncidentSummary] = Field(
        default_factory=list,
        description="Active (unresolved) incidents",
    )

    model_config = ConfigDict(
        extra="forbid",
        populate_by_name=True,
        json_schema_extra={
            "examples": [
                {
                    "event_id": "evt_live_001",
                    "active_sessions": 350,
                    "total_sessions": 350,
                    "incidents": [
                        {
                            "incident_id": "inc_001",
                            "severity": "critical",
                            "state": "investigating",
                            "slice_key": "EU-West|android|CDN-A",
                        }
                    ],
                }
            ]
        },
    )


class EventSessionStats(ApiModel):
    """Authoritative session counts for an event."""

    total_sessions: int = Field(ge=0, description="Total sessions provisioned for event")
    active_sessions: int = Field(ge=0, description="Sessions without ended_at")


class SessionSummary(ApiModel):
    """Session summary for event listing."""

    session_id: str = Field(description="Session UUID")
    event_id: str = Field(description="Parent event UUID")
    external_id: str = Field(description="Client-assigned session ID")
    client_type: str = Field(description="Client platform")
    region: str | None = Field(default=None, description="Geographic region")
    started_at: datetime | None = Field(default=None, description="Session start time")


class KPISnapshot(ApiModel):
    """Event-level KPI card for the live dashboard strip."""

    label: str = Field(description="KPI display label")
    value: float | int | str = Field(description="Current KPI value")
    unit: str | None = Field(default=None, description="Optional unit suffix")
    delta: float | None = Field(default=None, description="Change vs prior window")
    trend: str = Field(description="Direction: up, down, or stable")
    status: str = Field(description="Health: good, warning, or critical")


class AuditEventRead(ApiModel):
    """Audit trail entry."""

    audit_id: str = Field(description="Audit event UUID")
    correlation_id: str = Field(description="Links related audit events")
    actor_type: str = Field(
        description="Who performed the action: system, agent, human, simulation"
    )
    artifact_type: str = Field(
        description="What was acted upon: incident, proposal, agent_run, etc."
    )
    artifact_id: str = Field(description="UUID of the affected artifact")
    payload: dict[str, object] = Field(description="Action-specific data snapshot")
    created_at: datetime = Field(description="When the audit event was recorded")

    model_config = ConfigDict(
        extra="forbid",
        populate_by_name=True,
        json_schema_extra={
            "examples": [
                {
                    "audit_id": "aud_001",
                    "correlation_id": "inc_001",
                    "actor_type": "agent",
                    "artifact_type": "agent_run",
                    "artifact_id": "run_001",
                    "payload": {
                        "state": "waiting_for_human",
                        "reflection": {"accepted": True},
                    },
                    "created_at": "2026-07-14T20:18:45Z",
                }
            ]
        },
    )
