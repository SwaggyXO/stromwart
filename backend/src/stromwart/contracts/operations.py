from datetime import datetime
from enum import StrEnum
from uuid import UUID

from pydantic import Field

from stromwart.contracts.common import ApiModel


class Severity(StrEnum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class IncidentState(StrEnum):
    DETECTED = "detected"
    INVESTIGATING = "investigating"
    ASSESSED = "assessed"
    RESOLVED = "resolved"


class AlertState(StrEnum):
    OPEN = "open"
    ACKNOWLEDGED = "acknowledged"
    RESOLVED = "resolved"


class AlertCreate(ApiModel):
    event_id: UUID
    slice_key: str = Field(min_length=1, max_length=1000)
    rule_id: str = Field(min_length=1, max_length=100)
    severity: Severity
    observed_value: float
    threshold: float


class AlertRead(ApiModel):
    """Alert raised by a detection rule against an event slice."""

    id: UUID = Field(description="Alert UUID")
    event_id: UUID = Field(description="Parent live event")
    slice_key: str = Field(description="Affected topology slice")
    rule_id: str = Field(description="Rule that fired")
    severity: Severity = Field(description="Alert severity")
    state: AlertState = Field(description="Lifecycle state")
    observed_value: float = Field(description="Measured value that breached the threshold")
    threshold: float = Field(description="Rule threshold that was breached")
    description: str = Field(description="Human-readable summary derived from the rule")
    created_at: datetime = Field(description="When the alert was created")


class IncidentRead(ApiModel):
    """A detected incident with affected slice and evidence."""

    id: UUID = Field(description="Incident UUID")
    event_id: UUID = Field(description="Parent live event")
    slice_key: str = Field(description="Canonical slice identifier (pipe-separated)")
    state: IncidentState = Field(description="Current lifecycle state")
    severity: Severity = Field(description="Highest alert severity in this incident")
    affected_slice: dict[str, str | None] = Field(description="Structured slice dimensions")
    evidence_ids: list[UUID] = Field(description="Alert IDs that triggered this incident")
    hypothesis: dict[str, object] | None = Field(
        default=None, description="LLM analyst finding (if analyzed)"
    )
    created_at: datetime = Field(description="Detection timestamp")
    updated_at: datetime = Field(description="Last state change timestamp")
