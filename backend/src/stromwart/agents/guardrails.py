from __future__ import annotations

from dataclasses import dataclass, field

from stromwart.agents.base import AgentResult, GuardrailBlocked, Step
from stromwart.orchestrator.state import CognitiveState


@dataclass
class GuardrailPolicy:
    """Per-agent guardrail configuration."""

    max_consecutive_failures: int = 3
    required_evidence_grounding: bool = True
    allowed_action_types: list[str] = field(default_factory=list)
    max_output_confidence: float = 1.0
    min_output_confidence: float = 0.0


class AgentGuardrails:
    """
    Pre/post execution guards. Runs on EVERY agent step.
    Pre-checks are fast and deterministic (no LLM).
    Post-checks validate output quality.
    """

    def __init__(self, policies: dict[str, GuardrailPolicy] | None = None) -> None:
        self._policies = policies or {}

    def get_policy(self, agent_name: str) -> GuardrailPolicy:
        return self._policies.get(agent_name, GuardrailPolicy())

    def pre_check(
        self,
        agent_name: str,
        state: CognitiveState,
        history: list[Step],
    ) -> None:
        """Runs BEFORE each agent decision step."""
        policy = self.get_policy(agent_name)

        # Check consecutive failures
        recent_failures = 0
        for step in reversed(history):
            if step.observation and not step.observation.success:
                recent_failures += 1
            else:
                break
        if recent_failures >= policy.max_consecutive_failures:
            raise GuardrailBlocked(
                f"agent '{agent_name}' hit {recent_failures} consecutive tool failures"
            )

        # Check for drift — block mitigator if drift active
        if agent_name == "mitigator" and state.drift_detected:
            raise GuardrailBlocked(
                "mitigator blocked: model drift detected, predictions unreliable"
            )

    def post_check(self, agent_name: str, result: AgentResult) -> None:
        """Runs AFTER agent produces final output."""
        policy = self.get_policy(agent_name)

        if not result.success:
            return  # Don't validate failed results

        output = result.output

        # Confidence bounds
        confidence = output.get("confidence")
        if confidence is not None:
            if confidence > policy.max_output_confidence:
                raise GuardrailBlocked(
                    f"agent '{agent_name}' output confidence {confidence} "
                    f"exceeds max {policy.max_output_confidence}"
                )
            if confidence < policy.min_output_confidence:
                raise GuardrailBlocked(
                    f"agent '{agent_name}' output confidence {confidence} "
                    f"below min {policy.min_output_confidence}"
                )

        # Action allowlist (for mitigator)
        action_type = output.get("action_type")
        if action_type and policy.allowed_action_types:
            if action_type not in policy.allowed_action_types:
                raise GuardrailBlocked(
                    f"agent '{agent_name}' proposed action '{action_type}' not in allowlist"
                )

        # Evidence grounding (for diagnostician)
        if policy.required_evidence_grounding:
            evidence_ids = output.get("evidence_ids", [])
            if agent_name == "diagnostician" and not evidence_ids:
                raise GuardrailBlocked(
                    f"agent '{agent_name}' produced diagnosis without evidence citations"
                )
