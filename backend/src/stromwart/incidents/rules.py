from dataclasses import dataclass

from stromwart.contracts.features import FeatureVector
from stromwart.contracts.operations import Severity


@dataclass(frozen=True)
class RuleMatch:
    rule_id: str
    severity: Severity
    observed_value: float
    threshold: float


class AlertRules:
    def evaluate(self, features: FeatureVector) -> list[RuleMatch]:
        matches: list[RuleMatch] = []

        if features.stall_ratio >= 0.15:
            matches.append(
                RuleMatch(
                    "stall_ratio_critical",
                    Severity.CRITICAL,
                    features.stall_ratio,
                    0.15,
                )
            )
        elif features.stall_ratio >= 0.05:
            matches.append(
                RuleMatch(
                    "stall_ratio_high",
                    Severity.HIGH,
                    features.stall_ratio,
                    0.05,
                )
            )

        if features.buffer_min_ms <= 500:
            matches.append(
                RuleMatch(
                    "buffer_depletion",
                    Severity.HIGH,
                    float(features.buffer_min_ms),
                    500.0,
                )
            )

        if features.latest_packet_loss_pct is not None:
            if features.latest_packet_loss_pct >= 5.0:
                matches.append(
                    RuleMatch(
                        "packet_loss_high",
                        Severity.HIGH,
                        features.latest_packet_loss_pct,
                        5.0,
                    )
                )

        return matches
