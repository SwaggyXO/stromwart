"""Generate synthetic telemetry observations for simulation scenarios."""
from __future__ import annotations

import random
from datetime import datetime, timedelta, timezone
from uuid import UUID, uuid4

from stromwart.contracts.common import SourceType
from stromwart.contracts.telemetry import ObservationCreate
from stromwart.simulation.scenarios import DegradationPhase


def generate_observations_for_phase(
    phase: DegradationPhase,
    session_ids: list[str],
    phase_start: datetime,
    sequence_counters: dict[str, int],
    sample_rate: float = 0.1,
) -> list[ObservationCreate]:
    """Generate telemetry observations for a scenario phase."""
    observations: list[ObservationCreate] = []
    duration_seconds = int((phase.end_minute - phase.start_minute) * 60)
    tick_interval = 10

    for tick in range(0, duration_seconds, tick_interval):
        progress = tick / max(duration_seconds, 1)
        sampled_sessions = random.sample(
            session_ids,
            k=max(1, int(len(session_ids) * sample_rate)),
        )

        for session_id in sampled_sessions:
            sequence = sequence_counters.get(session_id, 0)
            obs = _generate_single_observation(
                phase=phase,
                progress=progress,
                session_id=UUID(session_id),
                timestamp=phase_start + timedelta(seconds=tick),
                sequence=sequence,
            )
            observations.append(obs)
            sequence_counters[session_id] = sequence + 1

    return observations


def _generate_single_observation(
    phase: DegradationPhase,
    progress: float,
    session_id: UUID,
    timestamp: datetime,
    sequence: int,
) -> ObservationCreate:
    """Generate a single telemetry observation interpolated within a phase."""

    def lerp_range(r: tuple[float, float]) -> float:
        base = r[0] + (r[1] - r[0]) * progress
        jitter = random.gauss(0, (r[1] - r[0]) * 0.1)
        return max(0.0, base + jitter)

    mos = lerp_range(phase.mos_range)
    packet_loss = lerp_range(phase.packet_loss_pct)
    buffer_ratio = lerp_range(phase.buffer_ratio)
    stall_ratio = lerp_range(phase.stall_ratio)

    bitrate = int(max(500, 6000 - (5.0 - mos) * 1200 + random.gauss(0, 200)))
    throughput = int(bitrate * (1.0 + random.gauss(0, 0.1)))
    duration_ms = 2000
    rebuffer_ms = int(min(duration_ms, stall_ratio * 10000 * random.uniform(0.5, 1.5)))

    if mos < 3.0:
        buffer_level_ms = int(random.uniform(200, 800))
    else:
        buffer_level_ms = int(max(500, 8000 * (1 - buffer_ratio)))

    return ObservationCreate(
        session_id=session_id,
        observed_at=timestamp.astimezone(timezone.utc),
        sequence=sequence,
        duration_ms=duration_ms,
        bitrate_kbps=bitrate,
        buffer_level_ms=buffer_level_ms,
        rebuffer_duration_ms=rebuffer_ms,
        throughput_kbps=throughput,
        packet_loss_pct=round(packet_loss, 3),
        resolution="1080p" if mos > 3.5 else "720p" if mos > 2.5 else "480p",
        source_type=SourceType.SYNTHETIC,
        metadata={
            "cdn_node": (
                f"edge-{random.choice(['us-east', 'eu-west', 'ap-south'])}"
                f"-{random.randint(1, 8)}"
            ),
            "simulated_mos": round(mos, 2),
        },
    )


def create_session_pool(event_id: str, count: int) -> list[dict[str, str]]:
    """Create session registration payloads."""
    regions = ["us-east", "eu-west", "ap-south", "us-west", "eu-central"]
    clients = ["web", "ios", "android", "smart-tv", "roku"]
    started_at = datetime.now(timezone.utc).isoformat()

    return [
        {
            "id": str(uuid4()),
            "event_id": event_id,
            "external_id": f"sim-session-{i:05d}",
            "client_type": random.choice(clients),
            "region": random.choice(regions),
            "started_at": started_at,
        }
        for i in range(count)
    ]
