from dataclasses import dataclass
from pathlib import Path
from typing import Any, cast

import yaml

from stromwart.contracts.actions import ProposalCreate, ProposalState


@dataclass(frozen=True)
class PolicyDecision:
    state: ProposalState
    reasons: list[str]


class PolicyService:
    def __init__(
        self,
        allowlist_path: Path,
        guardrails_path: Path,
    ) -> None:
        self._allowlist = self._load(allowlist_path)
        self._guardrails = self._load(guardrails_path)

    def evaluate(
        self,
        proposal: ProposalCreate,
        evidence_is_valid: bool,
    ) -> PolicyDecision:
        reasons: list[str] = []

        if proposal.action_type not in self._allowlist["allowed_actions"]:
            reasons.append("action_type is not permitted")

        if not evidence_is_valid:
            reasons.append("proposal evidence is not attached to the incident")

        if proposal.drift_active:
            reasons.append("model drift is active")

        max_interval = self._guardrails["maximum_prediction_interval_width"]
        if (
            proposal.prediction_interval_width is not None
            and proposal.prediction_interval_width > max_interval
        ):
            reasons.append("prediction uncertainty exceeds policy threshold")

        session_count = proposal.target_scope.get("session_count", 0)
        max_scope = self._guardrails["maximum_blast_radius_sessions"]

        if not isinstance(session_count, int) or session_count < 0:
            reasons.append("target_scope.session_count must be a non-negative integer")
        elif session_count > max_scope:
            reasons.append("target scope exceeds permitted blast radius")

        if reasons:
            return PolicyDecision(ProposalState.BLOCKED, reasons)

        if proposal.confidence < self._guardrails["minimum_confidence"]:
            return PolicyDecision(
                ProposalState.INVESTIGATE,
                ["proposal confidence is below policy threshold"],
            )

        if proposal.risk_score >= self._guardrails["high_risk_approval_threshold"]:
            return PolicyDecision(
                ProposalState.APPROVAL_REQUIRED,
                ["proposal risk requires human approval"],
            )

        if proposal.action_type == "investigate_only":
            return PolicyDecision(ProposalState.OBSERVE, [])

        return PolicyDecision(ProposalState.SIMULATE, [])

    @staticmethod
    def _load(path: Path) -> dict[str, Any]:
        with path.open(encoding="utf-8") as source:
            value = yaml.safe_load(source)

        if not isinstance(value, dict):
            raise ValueError(f"policy file must contain a mapping: {path}")

        return cast(dict[str, Any], value)
