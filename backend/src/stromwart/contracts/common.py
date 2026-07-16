from datetime import datetime
from enum import StrEnum
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class ApiModel(BaseModel):
    model_config = ConfigDict(extra="forbid", populate_by_name=True)


class SourceType(StrEnum):
    LIVE = "live"
    REPLAY = "replay"
    SYNTHETIC = "synthetic"
    BENCHMARK = "benchmark"


class EventCreate(ApiModel):
    name: str = Field(min_length=1, max_length=200, description="Human-readable event name")
    content_type: str = Field(
        min_length=1,
        max_length=50,
        description="Category: sports, concert, conference, esports",
    )
    starts_at: datetime = Field(description="Scheduled start time (UTC)")
    metadata: dict[str, object] = Field(
        default_factory=dict,
        description="Arbitrary key-value metadata (organizer, region, notes)",
    )

    model_config = ConfigDict(
        extra="forbid",
        populate_by_name=True,
        json_schema_extra={
            "examples": [
                {
                    "name": "Champions League Final 2026",
                    "content_type": "sports",
                    "starts_at": "2026-07-14T20:00:00Z",
                    "metadata": {"organizer": "UEFA", "venue": "Wembley"},
                }
            ]
        },
    )


class EventRead(EventCreate):
    id: UUID
    ends_at: datetime | None = None


class SessionCreate(ApiModel):
    event_id: UUID
    external_id: str = Field(min_length=1, max_length=200)
    client_type: str = Field(min_length=1, max_length=50)
    source_type: SourceType
    started_at: datetime
    region: str | None = Field(default=None, max_length=100)
    asn: str | None = Field(default=None, max_length=100)
    device_class: str | None = Field(default=None, max_length=100)
    network_type: str | None = Field(default=None, max_length=50)
    cdn_edge_id: str | None = Field(default=None, max_length=100)
    abr_profile: str | None = Field(default=None, max_length=100)


class SessionRead(SessionCreate):
    id: UUID
    ended_at: datetime | None = None
