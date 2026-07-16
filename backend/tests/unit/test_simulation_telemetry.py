"""Tests for simulation telemetry timestamp continuity."""
from datetime import datetime, timedelta, timezone

from stromwart.simulation.scenarios import FIFA_WC_GER_JPN
from stromwart.simulation.telemetry_gen import generate_observations_for_phase


def test_phase_timestamps_increase_with_sequence() -> None:
    """Across two phases, same session: later sequence => later observed_at."""
    scenario = FIFA_WC_GER_JPN
    session_ids = ["aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa"]
    sequence_counters = dict.fromkeys(session_ids, 0)
    sim_start = datetime(2026, 1, 1, 12, 0, 0, tzinfo=timezone.utc)

    phase_a = scenario.phases[0]
    phase_b = scenario.phases[1]

    obs_a = generate_observations_for_phase(
        phase=phase_a,
        session_ids=session_ids,
        phase_start=sim_start + timedelta(minutes=phase_a.start_minute),
        sequence_counters=sequence_counters,
        sample_rate=1.0,
    )
    obs_b = generate_observations_for_phase(
        phase=phase_b,
        session_ids=session_ids,
        phase_start=sim_start + timedelta(minutes=phase_b.start_minute),
        sequence_counters=sequence_counters,
        sample_rate=1.0,
    )

    combined = obs_a + obs_b
    by_session: dict[str, list[tuple[int, datetime]]] = {}
    for obs in combined:
        sid = str(obs.session_id)
        by_session.setdefault(sid, []).append((obs.sequence, obs.observed_at))

    for pairs in by_session.values():
        sorted_pairs = sorted(pairs, key=lambda p: p[0])
        for i in range(1, len(sorted_pairs)):
            assert sorted_pairs[i][1] >= sorted_pairs[i - 1][1], (
                f"observed_at decreased at sequence {sorted_pairs[i][0]}"
            )
