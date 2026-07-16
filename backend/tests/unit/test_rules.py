from datetime import UTC, datetime
from uuid import uuid4

from stromwart.contracts.features import FeatureVector
from stromwart.incidents.rules import AlertRules


def test_rules_identify_independent_high_severity_signals() -> None:
    features = FeatureVector(
        session_id=uuid4(),
        window_start=datetime.now(UTC),
        window_end=datetime.now(UTC),
        observation_count=4,
        throughput_mean_kbps=1000,
        throughput_std_kbps=10,
        buffer_mean_ms=500,
        buffer_min_ms=300,
        rebuffer_total_ms=1000,
        stall_ratio=0.2,
        downswitch_count=1,
        latest_bitrate_kbps=500,
        latest_packet_loss_pct=8.0,
    )

    rule_ids = {match.rule_id for match in AlertRules().evaluate(features)}

    assert rule_ids == {
        "stall_ratio_critical",
        "buffer_depletion",
        "packet_loss_high",
    }