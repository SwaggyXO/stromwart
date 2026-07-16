import hashlib
import json
from dataclasses import dataclass
from datetime import UTC, datetime
from typing import cast
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from stromwart.contracts.common import EventCreate, SessionCreate
from stromwart.contracts.telemetry import ObservationCreate
from stromwart.errors import ConflictError, NotFoundError
from stromwart.persistence import EventRow, ObservationRow, SessionRow


@dataclass(frozen=True)
class SessionCounts:
    total: int
    active: int


class TelemetryRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def create_event(self, value: EventCreate) -> EventRow:
        row = EventRow(
            name=value.name,
            content_type=value.content_type,
            starts_at=value.starts_at,
            metadata_=value.metadata,
        )
        self._session.add(row)
        await self._session.flush()
        return row

    async def list_events(self, limit: int = 50) -> list[EventRow]:
        statement = select(EventRow).order_by(EventRow.starts_at.desc()).limit(limit)
        return list((await self._session.scalars(statement)).all())

    async def get_active_event(self) -> EventRow | None:
        """Prefer an unfinished event; otherwise return the most recently started."""
        now = datetime.now(UTC)
        active = cast(
            EventRow | None,
            await self._session.scalar(
                select(EventRow)
                .where(EventRow.starts_at <= now)
                .where((EventRow.ends_at.is_(None)) | (EventRow.ends_at > now))
                .order_by(EventRow.starts_at.desc())
                .limit(1)
            ),
        )
        if active is not None:
            return active

        return cast(
            EventRow | None,
            await self._session.scalar(
                select(EventRow).order_by(EventRow.starts_at.desc()).limit(1)
            ),
        )

    async def end_event(self, event_id: str) -> None:
        row = await self._session.get(EventRow, event_id)
        if row is not None and row.ends_at is None:
            row.ends_at = datetime.now(UTC)
            await self._session.flush()

    async def get_event(self, event_id: UUID) -> EventRow:
        row = await self._session.get(EventRow, str(event_id))
        if row is None:
            raise NotFoundError("event does not exist")
        return row

    async def create_session(self, value: SessionCreate) -> SessionRow:
        await self.get_event(value.event_id)

        row = SessionRow(
            event_id=str(value.event_id),
            external_id=value.external_id,
            client_type=value.client_type,
            source_type=value.source_type.value,
            started_at=value.started_at,
            region=value.region,
            asn=value.asn,
            device_class=value.device_class,
            network_type=value.network_type,
            cdn_edge_id=value.cdn_edge_id,
            abr_profile=value.abr_profile,
        )
        self._session.add(row)
        await self._session.flush()
        return row

    async def timestamp_before(
        self,
        session_id: UUID,
        sequence: int,
    ) -> datetime | None:
        statement = (
            select(ObservationRow.observed_at)
            .where(
                ObservationRow.session_id == str(session_id),
                ObservationRow.sequence < sequence,
            )
            .order_by(ObservationRow.sequence.desc())
            .limit(1)
        )
        return cast(datetime | None, await self._session.scalar(statement))

    async def timestamp_after(
        self,
        session_id: UUID,
        sequence: int,
    ) -> datetime | None:
        statement = (
            select(ObservationRow.observed_at)
            .where(
                ObservationRow.session_id == str(session_id),
                ObservationRow.sequence > sequence,
            )
            .order_by(ObservationRow.sequence.asc())
            .limit(1)
        )
        return cast(datetime | None, await self._session.scalar(statement))

    async def sessions_for_event(self, event_id: str, limit: int = 100) -> list[SessionRow]:
        statement = (
            select(SessionRow)
            .where(SessionRow.event_id == event_id)
            .order_by(SessionRow.started_at.desc())
            .limit(limit)
        )
        return list((await self._session.scalars(statement)).all())

    async def count_sessions_for_event(self, event_id: str) -> SessionCounts:
        total = await self._session.scalar(
            select(func.count()).select_from(SessionRow).where(SessionRow.event_id == event_id)
        )
        active = await self._session.scalar(
            select(func.count())
            .select_from(SessionRow)
            .where(SessionRow.event_id == event_id)
            .where(SessionRow.ended_at.is_(None))
        )
        return SessionCounts(total=int(total or 0), active=int(active or 0))

    async def get_session(self, session_id: UUID) -> SessionRow:
        row = await self._session.get(SessionRow, str(session_id))
        if row is None:
            raise NotFoundError("session does not exist")
        return row

    async def prior_timestamp(
        self,
        session_id: UUID,
        sequence: int,
    ) -> datetime | None:
        statement = (
            select(ObservationRow.observed_at)
            .where(
                ObservationRow.session_id == str(session_id),
                ObservationRow.sequence < sequence,
            )
            .order_by(ObservationRow.sequence.desc())
            .limit(1)
        )
        return cast(datetime | None, await self._session.scalar(statement))

    async def get_observation(
        self,
        session_id: UUID,
        sequence: int,
    ) -> ObservationRow | None:
        statement = select(ObservationRow).where(
            ObservationRow.session_id == str(session_id),
            ObservationRow.sequence == sequence,
        )
        return cast(ObservationRow | None, await self._session.scalar(statement))

    async def add_observation(
        self,
        value: ObservationCreate,
    ) -> tuple[ObservationRow, bool]:
        payload_hash = self.payload_hash(value)
        existing = await self.get_observation(value.session_id, value.sequence)

        if existing is not None:
            if existing.payload_hash != payload_hash:
                raise ConflictError("sequence already exists with a different telemetry payload")
            return existing, True

        row = ObservationRow(
            session_id=str(value.session_id),
            observed_at=value.observed_at,
            sequence=value.sequence,
            duration_ms=value.duration_ms,
            bitrate_kbps=value.bitrate_kbps,
            buffer_level_ms=value.buffer_level_ms,
            rebuffer_duration_ms=value.rebuffer_duration_ms,
            throughput_kbps=value.throughput_kbps,
            rtt_ms=value.rtt_ms,
            jitter_ms=value.jitter_ms,
            packet_loss_pct=value.packet_loss_pct,
            resolution=value.resolution,
            source_type=value.source_type.value,
            payload_hash=payload_hash,
            metadata_=value.metadata,
        )
        self._session.add(row)
        await self._session.flush()
        return row, False

    async def observations(
        self,
        session_id: UUID,
        limit: int = 60,
    ) -> list[ObservationRow]:
        statement = (
            select(ObservationRow)
            .where(ObservationRow.session_id == str(session_id))
            .order_by(ObservationRow.sequence.desc())
            .limit(limit)
        )
        rows = list((await self._session.scalars(statement)).all())
        return list(reversed(rows))

    @staticmethod
    def payload_hash(value: ObservationCreate) -> str:
        canonical = value.model_dump(mode="json")
        canonical.pop("session_id")
        canonical.pop("sequence")
        encoded = json.dumps(
            canonical,
            separators=(",", ":"),
            sort_keys=True,
        ).encode()
        return hashlib.sha256(encoded).hexdigest()
