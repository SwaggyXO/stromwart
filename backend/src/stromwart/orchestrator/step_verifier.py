"""Lightweight per-agent step verification after OODA dispatch."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from stromwart.agents.base import AgentResult


@dataclass(frozen=True)
class StepReflection:
    passed: bool
    checks: list[str] = field(default_factory=list)
    reasons: list[str] = field(default_factory=list)

    def as_dict(self) -> dict[str, object]:
        return {
            "passed": self.passed,
            "checks": self.checks,
            "reasons": self.reasons,
        }


_REQUIRED_OUTPUT_KEYS: dict[str, list[str]] = {
    "detector": ["anomalies_detected"],
    "diagnostician": ["hypothesis", "recommended_action"],
    "mitigator": ["action_type", "rationale"],
    "verifier": ["passed"],
}


def verify_agent_step(agent_name: str, result: AgentResult) -> StepReflection:
    checks: list[str] = []
    reasons: list[str] = []

    if not result.success:
        reasons.append(f"agent returned success=False ({result.stop_reason})")
    else:
        checks.append("agent_success")

    if result.stop_reason:
        checks.append(f"stop_reason:{result.stop_reason}")

    for key in _REQUIRED_OUTPUT_KEYS.get(agent_name, []):
        if key not in result.output:
            reasons.append(f"missing output key: {key}")
        else:
            checks.append(f"has_{key}")

    if agent_name == "diagnostician":
        hypothesis = result.output.get("hypothesis")
        if isinstance(hypothesis, str) and len(hypothesis) < 10:
            reasons.append("hypothesis too short to be actionable")

    if agent_name == "mitigator":
        session_count = result.output.get("target_scope", {})
        if isinstance(session_count, dict):
            sc = session_count.get("session_count")
            if sc is not None and not isinstance(sc, int):
                reasons.append("target_scope.session_count must be int")

    passed = not reasons and result.success
    return StepReflection(passed=passed, checks=checks, reasons=reasons)
