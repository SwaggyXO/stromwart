from datetime import datetime
from uuid import UUID

from pydantic import Field

from stromwart.contracts.common import ApiModel


class FeatureVector(ApiModel):
    session_id: UUID
    window_start: datetime
    window_end: datetime
    schema_version: str = "telemetry-v1"
    observation_count: int = Field(ge=1)
    throughput_mean_kbps: float = Field(ge=0)
    throughput_std_kbps: float = Field(ge=0)
    buffer_mean_ms: float = Field(ge=0)
    buffer_min_ms: int = Field(ge=0)
    rebuffer_total_ms: int = Field(ge=0)
    stall_ratio: float = Field(ge=0, le=1)
    downswitch_count: int = Field(ge=0)
    latest_bitrate_kbps: int = Field(ge=0)
    latest_packet_loss_pct: float | None = Field(default=None, ge=0, le=100)


class FeatureRead(ApiModel):
    id: UUID
    session_id: UUID
    schema_version: str
    values: dict[str, object]
    computed_at: datetime
