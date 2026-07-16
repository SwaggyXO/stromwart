from typing import Any

from sqlalchemy import JSON, Float, ForeignKey, Index, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from stromwart.database import Base
from stromwart.persistence.base import IdentifierMixin, TimestampMixin


class FeatureSnapshotRow(IdentifierMixin, TimestampMixin, Base):
    __tablename__ = "feature_snapshots"

    session_id: Mapped[str] = mapped_column(ForeignKey("sessions.id", ondelete="CASCADE"))
    schema_version: Mapped[str] = mapped_column(String(100))
    values: Mapped[dict[str, Any]] = mapped_column(JSON)


class PredictionRow(IdentifierMixin, TimestampMixin, Base):
    __tablename__ = "predictions"
    __table_args__ = (Index("ix_predictions_entity_created", "entity_id", "created_at"),)

    entity_type: Mapped[str] = mapped_column(String(50))
    entity_id: Mapped[str] = mapped_column(String(36))
    prediction_type: Mapped[str] = mapped_column(String(50))
    value: Mapped[float] = mapped_column(Float)
    lower_bound: Mapped[float | None] = mapped_column(Float)
    upper_bound: Mapped[float | None] = mapped_column(Float)
    confidence: Mapped[float | None] = mapped_column(Float)
    model_name: Mapped[str] = mapped_column(String(100))
    model_version: Mapped[str] = mapped_column(String(100))
    feature_schema_version: Mapped[str] = mapped_column(String(100))


class ForecastRow(IdentifierMixin, TimestampMixin, Base):
    __tablename__ = "forecasts"

    entity_type: Mapped[str] = mapped_column(String(50))
    entity_id: Mapped[str] = mapped_column(String(36))
    metric_name: Mapped[str] = mapped_column(String(100))
    horizon_seconds: Mapped[int] = mapped_column(Integer)
    p10: Mapped[float] = mapped_column(Float)
    p50: Mapped[float] = mapped_column(Float)
    p90: Mapped[float] = mapped_column(Float)
    model_version: Mapped[str] = mapped_column(String(100))
