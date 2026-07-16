from datetime import UTC, datetime
from uuid import uuid4

from stromwart.contracts.common import SourceType
from stromwart.contracts.telemetry import ObservationCreate
from stromwart.repositories.telemetry import TelemetryRepository


def observation(sequence: int, bitrate_kbps: int = 1000) -> ObservationCreate:
    return ObservationCreate(
        session_id=uuid4(),
        observed_at=datetime.now(UTC),
        sequence=sequence,
        duration_ms=1000,
        bitrate_kbps=bitrate_kbps,
        buffer_level_ms=3000,
        throughput_kbps=2000,
        source_type=SourceType.REPLAY,
    )


def test_payload_hash_ignores_session_and_sequence() -> None:
    first = observation(0)
    second = first.model_copy(update={"sequence": 1})

    assert TelemetryRepository.payload_hash(first) == TelemetryRepository.payload_hash(second)


def test_payload_hash_changes_when_telemetry_changes() -> None:
    first = observation(0, bitrate_kbps=1000)
    second = first.model_copy(update={"bitrate_kbps": 500})

    assert TelemetryRepository.payload_hash(first) != TelemetryRepository.payload_hash(second)