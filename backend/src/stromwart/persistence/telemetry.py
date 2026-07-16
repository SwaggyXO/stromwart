from datetime import datetime
from typing import Any

from sqlalchemy import JSON, DateTime, ForeignKey, Index, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from stromwart.database import Base
from stromwart.persistence.base import IdentifierMixin


class EventRow(IdentifierMixin, Base):
    __tablename__ = "events"

    name: Mapped[str] = mapped_column(String(200))
    content_type: Mapped[str] = mapped_column(String(50))
    starts_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), index=True)
    ends_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    metadata_: Mapped[dict[str, Any]] = mapped_column("metadata", JSON, default=dict)


class SessionRow(IdentifierMixin, Base):
    __tablename__ = "sessions"
    __table_args__ = (
        Index("uq_sessions_event_external", "event_id", "external_id", unique=True),
        Index("ix_sessions_event_started", "event_id", "started_at"),
    )

    event_id: Mapped[str] = mapped_column(ForeignKey("events.id", ondelete="RESTRICT"))
    external_id: Mapped[str] = mapped_column(String(200))
    client_type: Mapped[str] = mapped_column(String(50))
    source_type: Mapped[str] = mapped_column(String(20))
    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    ended_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    region: Mapped[str | None] = mapped_column(String(100))
    asn: Mapped[str | None] = mapped_column(String(100))
    device_class: Mapped[str | None] = mapped_column(String(100))
    network_type: Mapped[str | None] = mapped_column(String(50))
    cdn_edge_id: Mapped[str | None] = mapped_column(String(100))
    abr_profile: Mapped[str | None] = mapped_column(String(100))


class ObservationRow(IdentifierMixin, Base):
    __tablename__ = "observations"
    __table_args__ = (
        Index("uq_observations_session_sequence", "session_id", "sequence", unique=True),
        Index("ix_observations_session_time", "session_id", "observed_at"),
    )

    session_id: Mapped[str] = mapped_column(ForeignKey("sessions.id", ondelete="CASCADE"))
    observed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    sequence: Mapped[int] = mapped_column(Integer)
    duration_ms: Mapped[int] = mapped_column(Integer)
    bitrate_kbps: Mapped[int] = mapped_column(Integer)
    buffer_level_ms: Mapped[int] = mapped_column(Integer)
    rebuffer_duration_ms: Mapped[int] = mapped_column(Integer)
    throughput_kbps: Mapped[int] = mapped_column(Integer)
    rtt_ms: Mapped[int | None] = mapped_column(Integer)
    jitter_ms: Mapped[float | None] = mapped_column()
    packet_loss_pct: Mapped[float | None] = mapped_column()
    resolution: Mapped[str | None] = mapped_column(String(20))
    source_type: Mapped[str] = mapped_column(String(20))
    payload_hash: Mapped[str] = mapped_column(String(64))
    metadata_: Mapped[dict[str, Any]] = mapped_column("metadata", JSON, default=dict)
