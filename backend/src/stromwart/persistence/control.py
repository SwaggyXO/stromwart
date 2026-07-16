from datetime import datetime
from typing import Any

from sqlalchemy import JSON, Boolean, DateTime, Float, ForeignKey, Index, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from stromwart.database import Base
from stromwart.persistence.base import IdentifierMixin, TimestampMixin, utcnow


class AlertRow(IdentifierMixin, TimestampMixin, Base):
    __tablename__ = "alerts"

    event_id: Mapped[str] = mapped_column(ForeignKey("events.id", ondelete="RESTRICT"))
    slice_key: Mapped[str] = mapped_column(String(1000))
    rule_id: Mapped[str] = mapped_column(String(100))
    severity: Mapped[str] = mapped_column(String(20))
    observed_value: Mapped[float] = mapped_column(Float)
    threshold: Mapped[float] = mapped_column(Float)
    state: Mapped[str] = mapped_column(String(20), default="open")


class IncidentRow(IdentifierMixin, TimestampMixin, Base):
    __tablename__ = "incidents"
    __table_args__ = (Index("uq_incidents_active_key", "active_key", unique=True),)

    event_id: Mapped[str] = mapped_column(ForeignKey("events.id", ondelete="RESTRICT"))
    slice_key: Mapped[str] = mapped_column(String(1000))
    active_key: Mapped[str | None] = mapped_column(String(1100))
    state: Mapped[str] = mapped_column(String(30))
    severity: Mapped[str] = mapped_column(String(20))
    affected_slice: Mapped[dict[str, Any]] = mapped_column(JSON)
    evidence_ids: Mapped[list[str]] = mapped_column(JSON, default=list)
    hypothesis: Mapped[dict[str, Any] | None] = mapped_column(JSON)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=utcnow,
        onupdate=utcnow,
    )


class ProposalRow(IdentifierMixin, TimestampMixin, Base):
    __tablename__ = "action_proposals"

    incident_id: Mapped[str] = mapped_column(ForeignKey("incidents.id", ondelete="RESTRICT"))
    action_type: Mapped[str] = mapped_column(String(100))
    target_scope: Mapped[dict[str, Any]] = mapped_column(JSON)
    rationale: Mapped[str] = mapped_column(Text)
    expected_effect: Mapped[str] = mapped_column(Text)
    confidence: Mapped[float] = mapped_column(Float)
    risk_score: Mapped[float] = mapped_column(Float)
    evidence_ids: Mapped[list[str]] = mapped_column(JSON)
    policy_state: Mapped[str] = mapped_column(String(30))
    policy_reasons: Mapped[list[str]] = mapped_column(JSON, default=list)


class ExecutionRow(IdentifierMixin, TimestampMixin, Base):
    __tablename__ = "action_executions"

    proposal_id: Mapped[str] = mapped_column(ForeignKey("action_proposals.id", ondelete="RESTRICT"))
    mode: Mapped[str] = mapped_column(String(30))
    approved: Mapped[bool | None] = mapped_column(Boolean)
    approved_by: Mapped[str | None] = mapped_column(String(200))
    approval_reason: Mapped[str | None] = mapped_column(Text)
    simulated_result: Mapped[dict[str, Any] | None] = mapped_column(JSON)


class AgentRunRow(IdentifierMixin, TimestampMixin, Base):
    __tablename__ = "agent_runs"

    incident_id: Mapped[str] = mapped_column(ForeignKey("incidents.id", ondelete="RESTRICT"))
    state: Mapped[str] = mapped_column(String(30))
    workflow_data: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict)


class AuditRow(IdentifierMixin, TimestampMixin, Base):
    __tablename__ = "audit_events"
    __table_args__ = (Index("ix_audit_correlation_created", "correlation_id", "created_at"),)

    correlation_id: Mapped[str] = mapped_column(String(100))
    actor_type: Mapped[str] = mapped_column(String(50))
    artifact_type: Mapped[str] = mapped_column(String(50))
    artifact_id: Mapped[str] = mapped_column(String(36))
    payload_hash: Mapped[str] = mapped_column(String(64))
    payload: Mapped[dict[str, Any]] = mapped_column(JSON)
