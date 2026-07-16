from __future__ import annotations

from typing import Any

from stromwart.agents.base import ActionKind, AgentAction, BaseAgent, Step
from stromwart.orchestrator.state import CognitiveState


class VerifierAgent(BaseAgent):
    """
    Post-action verification agent.
    Checks whether a mitigation action had the desired effect.
    Runs deterministic comparison of before/after metrics.
    """

    name = "verifier"

    async def _decide(
        self,
        state: CognitiveState,
        history: list[Step],
        reflection: str | None,
    ) -> AgentAction:
        del reflection

        # Step 1: Gather current (post-action) telemetry
        if not history:
            return AgentAction(
                kind=ActionKind.TOOL,
                tool_name="telemetry",
                tool_args={"event_id": state.event_id, "window_minutes": 2},
                reasoning="Gathering post-action telemetry to verify effect",
            )

        # Step 2: Compare against pre-action state
        post_telemetry = history[0].observation.output if history[0].observation else {}
        verification = self._verify(state, post_telemetry)

        return AgentAction(
            kind=ActionKind.FINAL,
            final_output=verification,
            reasoning=f"Verification {'passed' if verification['passed'] else 'failed'}",
        )

    def _verify(
        self,
        state: CognitiveState,
        post_telemetry: dict[str, Any],
    ) -> dict[str, Any]:
        """Compare pre-action anomalies against post-action metrics."""
        pre_anomalies = (
            state.detection_result.get("anomalies", [])
            if state.detection_result
            else []
        )

        passed = True
        reasons: list[str] = []
        improvements: dict[str, Any] = {}

        # Check if key metrics improved
        post_mos = post_telemetry.get("avg_mos", 0)
        pre_mos = state.latest_kpis.get("avg_mos", 0)

        if isinstance(post_mos, (int, float)) and isinstance(pre_mos, (int, float)):
            if post_mos > pre_mos:
                improvements["mos_delta"] = post_mos - pre_mos
            elif pre_mos > 0 and post_mos <= pre_mos:
                reasons.append(f"MOS did not improve: {pre_mos:.2f} → {post_mos:.2f}")
                passed = False

        post_buffer = post_telemetry.get("buffer_ratio", 0)
        pre_buffer = state.latest_kpis.get("buffer_ratio", 100)
        if (
            isinstance(post_buffer, (int, float))
            and isinstance(pre_buffer, (int, float))
            and post_buffer < pre_buffer
        ):
            improvements["buffer_ratio_delta"] = pre_buffer - post_buffer

        # If no improvements detected at all, fail
        if not improvements and pre_anomalies:
            passed = False
            reasons.append("No measurable improvement in any monitored metric")

        return {
            "passed": passed,
            "reasons": reasons,
            "improvements": improvements,
            "recommendation": "close_incident" if passed else "retry_diagnosis",
        }
