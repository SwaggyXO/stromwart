"""Pre-built simulation scenario profiles."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Literal


@dataclass(frozen=True)
class DegradationPhase:
    """A phase within a scenario where metrics change."""

    start_minute: float
    end_minute: float
    mos_range: tuple[float, float]
    session_count_range: tuple[int, int]
    packet_loss_pct: tuple[float, float]
    buffer_ratio: tuple[float, float]
    stall_ratio: tuple[float, float]
    description: str


@dataclass(frozen=True)
class ScenarioProfile:
    """Defines a complete simulation scenario."""

    id: str
    name: str
    description: str
    duration_minutes: int
    category: Literal["sports", "entertainment", "infrastructure"]
    sessions_peak: int
    phases: list[DegradationPhase] = field(default_factory=list)


FIFA_WC_GER_JPN = ScenarioProfile(
    id="fifa_wc_ger_jpn",
    name="FIFA WC 2026 — Germany vs Japan",
    description="High-stakes knockout match with CDN regional failure at minute 82.",
    duration_minutes=95,
    category="sports",
    sessions_peak=52000,
    phases=[
        DegradationPhase(
            start_minute=0,
            end_minute=75,
            mos_range=(4.1, 4.6),
            session_count_range=(38000, 52000),
            packet_loss_pct=(0.1, 0.5),
            buffer_ratio=(0.01, 0.03),
            stall_ratio=(0.005, 0.015),
            description="Stable streaming, growing audience",
        ),
        DegradationPhase(
            start_minute=75,
            end_minute=80,
            mos_range=(3.5, 4.1),
            session_count_range=(50000, 52000),
            packet_loss_pct=(0.5, 2.0),
            buffer_ratio=(0.03, 0.08),
            stall_ratio=(0.015, 0.04),
            description="CDN pressure building, minor degradation",
        ),
        DegradationPhase(
            start_minute=80,
            end_minute=85,
            mos_range=(1.8, 3.0),
            session_count_range=(48000, 52000),
            packet_loss_pct=(3.0, 8.0),
            buffer_ratio=(0.1, 0.25),
            stall_ratio=(0.05, 0.15),
            description="Regional CDN outage — critical incident",
        ),
        DegradationPhase(
            start_minute=85,
            end_minute=90,
            mos_range=(3.5, 4.2),
            session_count_range=(45000, 50000),
            packet_loss_pct=(0.5, 1.5),
            buffer_ratio=(0.02, 0.06),
            stall_ratio=(0.01, 0.03),
            description="Recovery post-mitigation (failover activated)",
        ),
        DegradationPhase(
            start_minute=90,
            end_minute=95,
            mos_range=(4.0, 4.5),
            session_count_range=(48000, 52000),
            packet_loss_pct=(0.1, 0.4),
            buffer_ratio=(0.01, 0.03),
            stall_ratio=(0.005, 0.01),
            description="Stabilized — full recovery confirmed",
        ),
    ],
)

CONCERT_STREAM_SPIKE = ScenarioProfile(
    id="concert_stream_spike",
    name="Live Concert — Global Artist Drop",
    description="Sudden 5x traffic spike when artist goes live, partial edge overload.",
    duration_minutes=60,
    category="entertainment",
    sessions_peak=120000,
    phases=[
        DegradationPhase(
            start_minute=0,
            end_minute=5,
            mos_range=(4.3, 4.7),
            session_count_range=(20000, 25000),
            packet_loss_pct=(0.1, 0.3),
            buffer_ratio=(0.005, 0.02),
            stall_ratio=(0.002, 0.01),
            description="Pre-show audience trickling in",
        ),
        DegradationPhase(
            start_minute=5,
            end_minute=10,
            mos_range=(3.0, 4.0),
            session_count_range=(80000, 120000),
            packet_loss_pct=(1.0, 4.0),
            buffer_ratio=(0.05, 0.15),
            stall_ratio=(0.03, 0.08),
            description="Traffic spike — edge servers overwhelmed",
        ),
        DegradationPhase(
            start_minute=10,
            end_minute=20,
            mos_range=(2.2, 3.2),
            session_count_range=(100000, 120000),
            packet_loss_pct=(2.5, 6.0),
            buffer_ratio=(0.08, 0.2),
            stall_ratio=(0.04, 0.12),
            description="Sustained pressure — multiple regions affected",
        ),
        DegradationPhase(
            start_minute=20,
            end_minute=35,
            mos_range=(3.8, 4.4),
            session_count_range=(90000, 110000),
            packet_loss_pct=(0.3, 1.0),
            buffer_ratio=(0.02, 0.05),
            stall_ratio=(0.01, 0.025),
            description="Auto-scaling kicks in, gradual recovery",
        ),
        DegradationPhase(
            start_minute=35,
            end_minute=60,
            mos_range=(4.2, 4.6),
            session_count_range=(85000, 100000),
            packet_loss_pct=(0.1, 0.4),
            buffer_ratio=(0.01, 0.03),
            stall_ratio=(0.005, 0.012),
            description="Stable for remainder of show",
        ),
    ],
)

CDN_REGIONAL_OUTAGE = ScenarioProfile(
    id="cdn_regional_outage",
    name="CDN Regional Outage — EU-West",
    description="Complete origin shield failure in EU-West region, 12-minute MTTR.",
    duration_minutes=30,
    category="infrastructure",
    sessions_peak=35000,
    phases=[
        DegradationPhase(
            start_minute=0,
            end_minute=5,
            mos_range=(4.2, 4.5),
            session_count_range=(30000, 35000),
            packet_loss_pct=(0.1, 0.3),
            buffer_ratio=(0.01, 0.02),
            stall_ratio=(0.005, 0.01),
            description="Normal operation",
        ),
        DegradationPhase(
            start_minute=5,
            end_minute=8,
            mos_range=(1.5, 2.5),
            session_count_range=(28000, 35000),
            packet_loss_pct=(5.0, 15.0),
            buffer_ratio=(0.2, 0.4),
            stall_ratio=(0.1, 0.3),
            description="Origin shield down — catastrophic packet loss",
        ),
        DegradationPhase(
            start_minute=8,
            end_minute=17,
            mos_range=(2.5, 3.5),
            session_count_range=(22000, 30000),
            packet_loss_pct=(2.0, 5.0),
            buffer_ratio=(0.05, 0.12),
            stall_ratio=(0.03, 0.07),
            description="Partial failover in progress, some sessions migrated",
        ),
        DegradationPhase(
            start_minute=17,
            end_minute=30,
            mos_range=(4.0, 4.5),
            session_count_range=(28000, 34000),
            packet_loss_pct=(0.2, 0.5),
            buffer_ratio=(0.01, 0.03),
            stall_ratio=(0.005, 0.015),
            description="Full recovery — all traffic rerouted",
        ),
    ],
)

SCENARIOS: dict[str, ScenarioProfile] = {
    FIFA_WC_GER_JPN.id: FIFA_WC_GER_JPN,
    CONCERT_STREAM_SPIKE.id: CONCERT_STREAM_SPIKE,
    CDN_REGIONAL_OUTAGE.id: CDN_REGIONAL_OUTAGE,
}
