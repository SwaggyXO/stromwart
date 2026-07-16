from datetime import UTC, datetime
from uuid import uuid4

import pytest
from pydantic import ValidationError

from stromwart.contracts.common import SourceType
from stromwart.contracts.telemetry import ObservationCreate


def test_observation_rejects_invalid_packet_loss() -> None:
    with pytest.raises(ValidationError):
        ObservationCreate(
            session_id=uuid4(),
            observed_at=datetime.now(UTC),
            sequence=0,
            duration_ms=1_000,
            bitrate_kbps=1_000,
            buffer_level_ms=3_000,
            throughput_kbps=2_000,
            packet_loss_pct=101,
            source_type=SourceType.REPLAY,
        )


def test_observation_rejects_implausible_stall_duration() -> None:
    with pytest.raises(ValidationError):
        ObservationCreate(
            session_id=uuid4(),
            observed_at=datetime.now(UTC),
            sequence=0,
            duration_ms=1_000,
            bitrate_kbps=1_000,
            buffer_level_ms=3_000,
            throughput_kbps=2_000,
            rebuffer_duration_ms=10_001,
            source_type=SourceType.REPLAY,
        )