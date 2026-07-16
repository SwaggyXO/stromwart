from datetime import datetime
from uuid import UUID

from pydantic import ConfigDict, Field, model_validator

from stromwart.contracts.common import ApiModel, SourceType


class ObservationCreate(ApiModel):
    """A single telemetry chunk from a streaming session."""

    session_id: UUID = Field(description="Parent session UUID")
    observed_at: datetime = Field(description="Wall-clock time of observation (UTC)")
    sequence: int = Field(ge=0, description="Monotonically increasing chunk index within session")
    duration_ms: int = Field(gt=0, le=60_000, description="Chunk duration in milliseconds")
    bitrate_kbps: int = Field(ge=0, description="Video bitrate for this chunk")
    buffer_level_ms: int = Field(ge=0, description="Client buffer level at observation time")
    rebuffer_duration_ms: int = Field(
        default=0, ge=0, description="Rebuffering time during this chunk"
    )
    throughput_kbps: int = Field(ge=0, description="Measured network throughput")
    rtt_ms: int | None = Field(default=None, ge=0, description="Round-trip time (nullable)")
    jitter_ms: float | None = Field(default=None, ge=0, description="Network jitter (nullable)")
    packet_loss_pct: float | None = Field(
        default=None, ge=0, le=100, description="Packet loss percentage"
    )
    resolution: str | None = Field(default=None, max_length=20, description="e.g. 720p, 1080p")
    source_type: SourceType = Field(description="Origin: live, replay, synthetic, benchmark")
    metadata: dict[str, object] = Field(default_factory=dict, description="Additional context")

    model_config = ConfigDict(
        extra="forbid",
        populate_by_name=True,
        json_schema_extra={
            "examples": [
                {
                    "session_id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
                    "observed_at": "2026-07-14T20:15:30Z",
                    "sequence": 42,
                    "duration_ms": 2000,
                    "bitrate_kbps": 5000,
                    "buffer_level_ms": 8500,
                    "rebuffer_duration_ms": 0,
                    "throughput_kbps": 6200,
                    "rtt_ms": 35,
                    "jitter_ms": 4.2,
                    "packet_loss_pct": 0.3,
                    "resolution": "1080p",
                    "source_type": "live",
                    "metadata": {},
                }
            ]
        },
    )

    @model_validator(mode="after")
    def validate_rebuffer_duration(self) -> "ObservationCreate":
        if self.rebuffer_duration_ms > self.duration_ms * 10:
            raise ValueError("rebuffer duration exceeds permitted observation window")
        return self


class ObservationRead(ObservationCreate):
    id: UUID
    payload_hash: str
    deduplicated: bool = False
