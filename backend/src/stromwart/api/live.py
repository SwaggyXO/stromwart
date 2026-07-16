import asyncio
import json
from collections.abc import AsyncIterator
from uuid import UUID

from fastapi import APIRouter, Request
from fastapi.responses import StreamingResponse

from stromwart.api.serializers import alert_read, event_read, incident_read
from stromwart.application.dependencies import ContainerDep
from stromwart.contracts.common import EventRead
from stromwart.contracts.live import EventSessionStats, KPISnapshot, LiveEventUpdate, SessionSummary
from stromwart.contracts.operations import AlertRead, IncidentRead
from stromwart.errors import NotFoundError
from stromwart.repositories.incidents import IncidentRepository
from stromwart.repositories.telemetry import TelemetryRepository

router = APIRouter(tags=["live"])


@router.get(
    "/events",
    response_model=list[EventRead],
    summary="List events",
    description="Return recent events ordered by start time (newest first).",
)
async def list_events(
    container: ContainerDep,
    limit: int = 50,
) -> list[EventRead]:
    async with container.database.transaction() as uow:
        rows = await TelemetryRepository(uow.session).list_events(limit=limit)
    return [event_read(row) for row in rows]


@router.get(
    "/events/active",
    response_model=EventRead,
    summary="Get active event",
    description=(
        "Return the currently live event (started and not ended). "
        "Falls back to the most recently started event when none are in-window."
    ),
)
async def get_active_event(container: ContainerDep) -> EventRead:
    async with container.database.transaction() as uow:
        row = await TelemetryRepository(uow.session).get_active_event()
    if row is None:
        raise NotFoundError("no active event")
    return event_read(row)


@router.get(
    "/events/{event_id}/kpis",
    response_model=list[KPISnapshot],
    summary="Event KPI snapshots",
    description="Aggregate live-dashboard KPIs for an event from sessions and incidents.",
)
async def event_kpis(event_id: UUID, container: ContainerDep) -> list[KPISnapshot]:
    async with container.database.transaction() as uow:
        telemetry = TelemetryRepository(uow.session)
        incidents_repo = IncidentRepository(uow.session)
        await telemetry.get_event(event_id)
        counts = await telemetry.count_sessions_for_event(str(event_id))
        incidents = await incidents_repo.incidents_for_event(str(event_id), limit=200)

    open_incidents = sum(1 for row in incidents if row.state != "resolved")
    critical = sum(
        1
        for row in incidents
        if row.state != "resolved" and row.severity == "critical"
    )

    return [
        KPISnapshot(
            label="Active Sessions",
            value=counts.active,
            trend="up" if counts.active > 0 else "stable",
            status="good" if counts.active > 0 else "warning",
        ),
        KPISnapshot(
            label="Open Incidents",
            value=open_incidents,
            trend="up" if open_incidents > 0 else "stable",
            status=(
                "good"
                if open_incidents == 0
                else "critical" if open_incidents > 2 else "warning"
            ),
        ),
        KPISnapshot(
            label="Critical",
            value=critical,
            trend="up" if critical > 0 else "stable",
            status="good" if critical == 0 else "critical",
        ),
        KPISnapshot(
            label="Total Sessions",
            value=counts.total,
            trend="stable",
            status="good",
        ),
    ]


@router.get(
    "/events/{event_id}/session-stats",
    response_model=EventSessionStats,
    summary="Event session counts",
    description="Authoritative total and active session counts for an event.",
)
async def event_session_stats(event_id: UUID, container: ContainerDep) -> EventSessionStats:
    async with container.database.transaction() as uow:
        telemetry = TelemetryRepository(uow.session)
        await telemetry.get_event(event_id)
        counts = await telemetry.count_sessions_for_event(str(event_id))
    return EventSessionStats(
        total_sessions=counts.total,
        active_sessions=counts.active,
    )


@router.get(
    "/events/{event_id}/alerts",
    response_model=list[AlertRead],
    summary="List event alerts",
    description="Return alerts for an event, optionally filtered by state.",
)
async def list_event_alerts(
    event_id: UUID,
    container: ContainerDep,
    state: str | None = None,
    limit: int = 50,
) -> list[AlertRead]:
    async with container.database.transaction() as uow:
        await TelemetryRepository(uow.session).get_event(event_id)
        rows = await IncidentRepository(uow.session).alerts_for_event(
            str(event_id),
            state=state,
            limit=limit,
        )
    return [alert_read(row) for row in rows]


@router.get(
    "/events/{event_id}/incidents",
    response_model=list[IncidentRead],
    summary="List event incidents",
    description="Return incidents for an event. Set active_only=true for unresolved only.",
)
async def list_event_incidents(
    event_id: UUID,
    container: ContainerDep,
    active_only: bool = False,
    limit: int = 50,
) -> list[IncidentRead]:
    async with container.database.transaction() as uow:
        await TelemetryRepository(uow.session).get_event(event_id)
        rows = await IncidentRepository(uow.session).incidents_for_event(
            str(event_id),
            active_only=active_only,
            limit=limit,
        )
    return [incident_read(row) for row in rows]


@router.get(
    "/events/{event_id}/stream",
    summary="Live event SSE stream",
    description="Server-Sent Events stream pushing real-time QoE updates for a live event.",
    response_model=LiveEventUpdate,
    responses={
        200: {
            "description": "SSE stream of LiveEventUpdate payloads",
            "content": {"text/event-stream": {}},
        }
    },
)
async def event_stream(
    event_id: UUID,
    request: Request,
    container: ContainerDep,
) -> StreamingResponse:
    async def generate() -> AsyncIterator[str]:
        while True:
            if await request.is_disconnected():
                break

            async with container.database.transaction() as uow:
                telemetry = TelemetryRepository(uow.session)
                incidents_repo = IncidentRepository(uow.session)

                counts = await telemetry.count_sessions_for_event(str(event_id))
                active_incidents = await incidents_repo.active_for_event(str(event_id))

            payload = {
                "event_id": str(event_id),
                "active_sessions": counts.active,
                "total_sessions": counts.total,
                "incidents": [
                    {
                        "incident_id": inc.id,
                        "severity": inc.severity,
                        "state": inc.state,
                        "slice_key": inc.slice_key,
                    }
                    for inc in active_incidents
                ],
            }

            yield f"data: {json.dumps(payload)}\n\n"
            await asyncio.sleep(2)

    return StreamingResponse(
        generate(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )


@router.get(
    "/events/{event_id}/sessions",
    response_model=list[SessionSummary],
    summary="List event sessions",
    description="Get all sessions for an event with optional limit.",
)
async def list_sessions(
    event_id: UUID,
    container: ContainerDep,
    limit: int = 50,
) -> list[SessionSummary]:
    async with container.database.transaction() as uow:
        telemetry = TelemetryRepository(uow.session)
        rows = await telemetry.sessions_for_event(str(event_id), limit=limit)

    return [
        SessionSummary(
            session_id=row.id,
            event_id=row.event_id,
            external_id=row.external_id,
            client_type=row.client_type,
            region=row.region,
            started_at=row.started_at,
        )
        for row in rows
    ]
