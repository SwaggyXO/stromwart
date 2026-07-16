from uuid import UUID

from stromwart.contracts.actions import ProposalRead, ProposalState
from stromwart.contracts.agents import AgentRunRead, AgentRunState
from stromwart.contracts.common import EventRead, SessionRead, SourceType
from stromwart.contracts.features import FeatureRead
from stromwart.contracts.operations import (
    AlertRead,
    AlertState,
    IncidentRead,
    IncidentState,
    Severity,
)
from stromwart.contracts.telemetry import ObservationRead
from stromwart.persistence import (
    AgentRunRow,
    AlertRow,
    EventRow,
    FeatureSnapshotRow,
    IncidentRow,
    ObservationRow,
    ProposalRow,
    SessionRow,
)


def event_read(row: EventRow) -> EventRead:
    return EventRead(
        id=UUID(row.id),
        name=row.name,
        content_type=row.content_type,
        starts_at=row.starts_at,
        ends_at=row.ends_at,
        metadata=row.metadata_,
    )


def session_read(row: SessionRow) -> SessionRead:
    return SessionRead(
        id=UUID(row.id),
        event_id=UUID(row.event_id),
        external_id=row.external_id,
        client_type=row.client_type,
        source_type=SourceType(row.source_type),
        started_at=row.started_at,
        ended_at=row.ended_at,
        region=row.region,
        asn=row.asn,
        device_class=row.device_class,
        network_type=row.network_type,
        cdn_edge_id=row.cdn_edge_id,
        abr_profile=row.abr_profile,
    )


def observation_read(
    row: ObservationRow,
    deduplicated: bool = False,
) -> ObservationRead:
    return ObservationRead(
        id=UUID(row.id),
        session_id=UUID(row.session_id),
        observed_at=row.observed_at,
        sequence=row.sequence,
        duration_ms=row.duration_ms,
        bitrate_kbps=row.bitrate_kbps,
        buffer_level_ms=row.buffer_level_ms,
        rebuffer_duration_ms=row.rebuffer_duration_ms,
        throughput_kbps=row.throughput_kbps,
        rtt_ms=row.rtt_ms,
        jitter_ms=row.jitter_ms,
        packet_loss_pct=row.packet_loss_pct,
        resolution=row.resolution,
        source_type=SourceType(row.source_type),
        metadata=row.metadata_,
        payload_hash=row.payload_hash,
        deduplicated=deduplicated,
    )


def feature_read(row: FeatureSnapshotRow) -> FeatureRead:
    return FeatureRead(
        id=UUID(row.id),
        session_id=UUID(row.session_id),
        schema_version=row.schema_version,
        values=row.values,
        computed_at=row.created_at,
    )


def alert_read(row: AlertRow) -> AlertRead:
    return AlertRead(
        id=UUID(row.id),
        event_id=UUID(row.event_id),
        slice_key=row.slice_key,
        rule_id=row.rule_id,
        severity=Severity(row.severity),
        state=AlertState(row.state),
        observed_value=row.observed_value,
        threshold=row.threshold,
        description=f"{row.rule_id} breached on {row.slice_key}",
        created_at=row.created_at,
    )


def incident_read(row: IncidentRow) -> IncidentRead:
    return IncidentRead(
        id=UUID(row.id),
        event_id=UUID(row.event_id),
        slice_key=row.slice_key,
        state=IncidentState(row.state),
        severity=Severity(row.severity),
        affected_slice=row.affected_slice,
        evidence_ids=[UUID(item) for item in row.evidence_ids],
        hypothesis=row.hypothesis,
        created_at=row.created_at,
        updated_at=row.updated_at,
    )


def proposal_read(row: ProposalRow) -> ProposalRead:
    return ProposalRead(
        id=UUID(row.id),
        incident_id=UUID(row.incident_id),
        action_type=row.action_type,
        target_scope=row.target_scope,
        rationale=row.rationale,
        expected_effect=row.expected_effect,
        confidence=row.confidence,
        risk_score=row.risk_score,
        evidence_ids=[UUID(item) for item in row.evidence_ids],
        state=ProposalState(row.policy_state),
        policy_reasons=row.policy_reasons,
        created_at=row.created_at,
    )


def agent_read(row: AgentRunRow) -> AgentRunRead:
    return AgentRunRead(
        id=UUID(row.id),
        incident_id=UUID(row.incident_id),
        state=AgentRunState(row.state),
        workflow_data=row.workflow_data,
        created_at=row.created_at,
    )
