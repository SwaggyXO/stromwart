from uuid import UUID

from fastapi import APIRouter, Query

from stromwart.application.dependencies import UnitOfWorkDep
from stromwart.contracts.live import AuditEventRead
from stromwart.persistence import AuditRow
from stromwart.repositories.audit import AuditRepository

router = APIRouter(tags=["audit"])


def _serialize(row: AuditRow) -> AuditEventRead:
    return AuditEventRead(
        audit_id=row.id,
        correlation_id=row.correlation_id,
        actor_type=row.actor_type,
        artifact_type=row.artifact_type,
        artifact_id=row.artifact_id,
        payload=row.payload,
        created_at=row.created_at,
    )


@router.get(
    "/audit/{correlation_id}",
    response_model=list[AuditEventRead],
    summary="Get audit trail",
    description="Retrieve all audit events for a given correlation ID, ordered chronologically.",
)
async def get_audit_trail(
    correlation_id: str,
    uow: UnitOfWorkDep,
) -> list[AuditEventRead]:
    audit = AuditRepository(uow.session)
    rows = await audit.by_correlation_id(correlation_id)
    return [_serialize(row) for row in rows]


@router.get(
    "/audit",
    response_model=list[AuditEventRead],
    summary="List recent audit events",
    description=(
        "Get the most recent audit events. Pass event_id to scope to a specific simulation event."
    ),
)
async def list_audit_events(
    uow: UnitOfWorkDep,
    limit: int = 50,
    event_id: UUID | None = Query(default=None),
) -> list[AuditEventRead]:
    audit = AuditRepository(uow.session)
    if event_id is not None:
        rows = await audit.recent_for_event(str(event_id), limit)
    else:
        rows = await audit.recent(limit)
    return [_serialize(row) for row in rows]
