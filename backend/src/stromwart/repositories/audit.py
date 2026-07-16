import hashlib
import json
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from stromwart.persistence import AuditRow


class AuditRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def append(
        self,
        correlation_id: str,
        actor_type: str,
        artifact_type: str,
        artifact_id: UUID | str,
        payload: dict[str, object],
    ) -> AuditRow:
        encoded = json.dumps(
            payload,
            default=str,
            separators=(",", ":"),
            sort_keys=True,
        ).encode()

        row = AuditRow(
            correlation_id=correlation_id,
            actor_type=actor_type,
            artifact_type=artifact_type,
            artifact_id=str(artifact_id),
            payload_hash=hashlib.sha256(encoded).hexdigest(),
            payload=payload,
        )
        self._session.add(row)
        await self._session.flush()
        return row

    async def by_correlation_id(self, correlation_id: str) -> list[AuditRow]:
        from sqlalchemy import select

        result = await self._session.execute(
            select(AuditRow)
            .where(AuditRow.correlation_id == correlation_id)
            .order_by(AuditRow.created_at.asc())
        )
        return list(result.scalars().all())

    async def recent(self, limit: int = 50) -> list[AuditRow]:
        from sqlalchemy import select

        result = await self._session.execute(
            select(AuditRow).order_by(AuditRow.created_at.desc()).limit(limit)
        )
        return list(result.scalars().all())

    async def recent_for_event(self, event_id: str, limit: int = 50) -> list[AuditRow]:
        """Return audit rows for incidents/alerts that belong to the given event."""
        from sqlalchemy import or_, select

        from stromwart.persistence.control import AlertRow, IncidentRow, ProposalRow

        inc_ids_q = select(IncidentRow.id).where(IncidentRow.event_id == event_id)
        alert_ids_q = select(AlertRow.id).where(AlertRow.event_id == event_id)
        proposal_ids_q = select(ProposalRow.id).where(
            ProposalRow.incident_id.in_(inc_ids_q)
        )

        result = await self._session.execute(
            select(AuditRow)
            .where(
                or_(
                    AuditRow.correlation_id.in_(inc_ids_q),
                    AuditRow.correlation_id.in_(alert_ids_q),
                    AuditRow.correlation_id.in_(proposal_ids_q),
                    AuditRow.artifact_id.in_(alert_ids_q),
                    AuditRow.artifact_id.in_(inc_ids_q),
                    AuditRow.artifact_id.in_(proposal_ids_q),
                )
            )
            .order_by(AuditRow.created_at.desc())
            .limit(limit)
        )
        return list(result.scalars().all())
