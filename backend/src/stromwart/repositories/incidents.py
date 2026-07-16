from typing import cast
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from stromwart.contracts.operations import Severity
from stromwart.persistence import AlertRow, IncidentRow


class IncidentRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get_incident(self, incident_id: UUID) -> IncidentRow | None:
        return await self._session.get(IncidentRow, str(incident_id))

    async def create_alert(
        self,
        event_id: UUID,
        slice_key: str,
        rule_id: str,
        severity: Severity,
        observed_value: float,
        threshold: float,
    ) -> AlertRow:
        row = AlertRow(
            event_id=str(event_id),
            slice_key=slice_key,
            rule_id=rule_id,
            severity=severity.value,
            observed_value=observed_value,
            threshold=threshold,
        )
        self._session.add(row)
        await self._session.flush()
        return row

    async def active_incident(self, active_key: str) -> IncidentRow | None:
        statement = select(IncidentRow).where(IncidentRow.active_key == active_key)
        return cast(IncidentRow | None, await self._session.scalar(statement))

    async def create_incident(
        self,
        event_id: UUID,
        slice_key: str,
        affected_slice: dict[str, str | None],
        severity: Severity,
        evidence_ids: list[str],
    ) -> IncidentRow:
        row = IncidentRow(
            event_id=str(event_id),
            slice_key=slice_key,
            active_key=f"{event_id}:{slice_key}",
            state="detected",
            severity=severity.value,
            affected_slice=affected_slice,
            evidence_ids=evidence_ids,
        )
        self._session.add(row)
        await self._session.flush()
        return row

    async def active_for_event(self, event_id: str) -> list[IncidentRow]:
        statement = (
            select(IncidentRow)
            .where(IncidentRow.event_id == event_id)
            .where(IncidentRow.active_key.isnot(None))
        )
        return list((await self._session.scalars(statement)).all())

    async def incidents_for_event(
        self,
        event_id: str,
        *,
        active_only: bool = False,
        limit: int = 50,
    ) -> list[IncidentRow]:
        statement = select(IncidentRow).where(IncidentRow.event_id == event_id)
        if active_only:
            statement = statement.where(IncidentRow.active_key.isnot(None))
        statement = statement.order_by(IncidentRow.created_at.desc()).limit(limit)
        return list((await self._session.scalars(statement)).all())

    async def alerts_for_event(
        self,
        event_id: str,
        *,
        state: str | None = None,
        limit: int = 50,
    ) -> list[AlertRow]:
        statement = select(AlertRow).where(AlertRow.event_id == event_id)
        if state is not None:
            statement = statement.where(AlertRow.state == state)
        statement = statement.order_by(AlertRow.created_at.desc()).limit(limit)
        return list((await self._session.scalars(statement)).all())

    async def get_alert(self, alert_id: UUID) -> AlertRow | None:
        return await self._session.get(AlertRow, str(alert_id))

    async def acknowledge_alert(self, alert: AlertRow) -> AlertRow:
        alert.state = "acknowledged"
        await self._session.flush()
        return alert

    async def resolve(self, incident: IncidentRow) -> IncidentRow:
        incident.state = "resolved"
        incident.active_key = None
        await self._session.flush()
        return incident
