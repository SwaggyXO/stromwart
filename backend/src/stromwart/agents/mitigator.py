from __future__ import annotations

from typing import Any

from stromwart.agents.base import ActionKind, AgentAction, BaseAgent, Step
from stromwart.orchestrator.state import CognitiveState

ACTION_PLAYBOOK: dict[str, dict[str, Any]] = {
    "scale_cdn_edge": {
        "description": "Add CDN edge nodes to saturated cluster",
        "risk_score": 0.15,
        "expected_effect": "Reduce p95 latency by ~40%, restore MOS above 3.8",
        "reversible": True,
        "blast_radius": "cluster",
    },
    "reroute_traffic": {
        "description": "Shift traffic to alternate network path",
        "risk_score": 0.25,
        "expected_effect": "Reduce packet loss from >2% to <0.5%",
        "reversible": True,
        "blast_radius": "region",
    },
    "increase_bandwidth_allocation": {
        "description": "Increase bandwidth cap for affected segment",
        "risk_score": 0.10,
        "expected_effect": "Restore bitrate to target levels",
        "reversible": True,
        "blast_radius": "segment",
    },
    "scale_origin": {
        "description": "Scale origin server pool to reduce response time",
        "risk_score": 0.20,
        "expected_effect": "Reduce stall events by ~60%",
        "reversible": True,
        "blast_radius": "global",
    },
    "investigate_only": {
        "description": "No automated action; flag for manual investigation",
        "risk_score": 0.0,
        "expected_effect": "Human review within SLA",
        "reversible": True,
        "blast_radius": "none",
    },
}


class MitigatorAgent(BaseAgent):
    """
    Proposes remediation actions based on diagnosis.
    Purely deterministic — maps diagnosis to action playbook.
    Respects policy constraints (blast radius, confidence thresholds).
    """

    name = "mitigator"

    async def _decide(
        self,
        state: CognitiveState,
        history: list[Step],
        reflection: str | None,
    ) -> AgentAction:
        # Step 1: Check runbook for context
        if not history:
            recommended = (
                state.diagnosis_result.get("recommended_action", "investigate_only")
                if state.diagnosis_result
                else "investigate_only"
            )
            return AgentAction(
                kind=ActionKind.TOOL,
                tool_name="runbook",
                tool_args={"action_type": recommended},
                reasoning=f"Checking runbook for action: {recommended}",
            )

        # Step 2: Produce proposal
        diagnosis = state.diagnosis_result or {}
        recommended = diagnosis.get("recommended_action", "investigate_only")
        playbook_entry = ACTION_PLAYBOOK.get(recommended, ACTION_PLAYBOOK["investigate_only"])

        confidence = diagnosis.get("confidence", 0.5)
        if not isinstance(confidence, (int, float)):
            confidence = 0.5

        # If reflection says previous action failed, downgrade to investigate_only
        if reflection and "failed" in reflection.lower():
            recommended = "investigate_only"
            playbook_entry = ACTION_PLAYBOOK["investigate_only"]
            confidence = float(confidence) * 0.5

        return AgentAction(
            kind=ActionKind.FINAL,
            final_output={
                "action_type": recommended,
                "target_scope": {
                    "event_id": state.event_id,
                    "affected_slices": diagnosis.get("contributing_factors", {}),
                    "blast_radius": playbook_entry["blast_radius"],
                    "session_count": int(state.active_sessions_count or 0),
                },
                "rationale": playbook_entry["description"],
                "expected_effect": playbook_entry["expected_effect"],
                "confidence": confidence,
                "risk_score": playbook_entry["risk_score"],
                "reversible": playbook_entry["reversible"],
            },
            reasoning=f"Proposing {recommended} with confidence {float(confidence):.2f}",
        )
