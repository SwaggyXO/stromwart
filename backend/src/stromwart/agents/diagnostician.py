from __future__ import annotations

from typing import Any
from uuid import uuid4

from stromwart.agents.base import ActionKind, AgentAction, BaseAgent, Step
from stromwart.orchestrator.state import CognitiveState
from stromwart.providers.analyst import AnalystProvider


class DiagnosticianAgent(BaseAgent):
    """
    Root cause analysis agent.
    Core logic: deterministic rules + QoE GBM feature importance.
    Optional LLM enrichment: generates natural language hypothesis.
    """

    name = "diagnostician"

    def __init__(self, *args: Any, llm_provider: AnalystProvider | None = None, **kwargs: Any):
        super().__init__(*args, **kwargs)
        self._llm = llm_provider

    async def _decide(
        self,
        state: CognitiveState,
        history: list[Step],
        reflection: str | None,
    ) -> AgentAction:
        # Step 1: Gather features for the affected slice
        if not history:
            affected_slices = (
                state.detection_result.get("affected_slices", ["global"])
                if state.detection_result
                else ["global"]
            )
            return AgentAction(
                kind=ActionKind.TOOL,
                tool_name="features",
                tool_args={
                    "event_id": state.event_id,
                    "slices": affected_slices,
                },
                reasoning="Gathering feature vectors for root cause analysis",
            )

        # Step 2: Get topology context
        if len(history) == 1:
            return AgentAction(
                kind=ActionKind.TOOL,
                tool_name="topology",
                tool_args={"event_id": state.event_id},
                reasoning="Checking network topology for infrastructure issues",
            )

        # Step 3: Produce diagnosis
        features = history[0].observation.output if history[0].observation else {}
        topology = (
            history[1].observation.output if len(history) > 1 and history[1].observation else {}
        )

        diagnosis = self._analyze_root_cause(features, topology, state, reflection)

        # Optional LLM enrichment for natural language hypothesis
        if self._llm is not None:
            try:
                from stromwart.contracts.agents import ToolCall, ToolName, ToolResult

                evidence = [
                    ToolResult(
                        call=ToolCall(name=ToolName.FEATURES, arguments={}),
                        output=features,
                    ),
                    ToolResult(
                        call=ToolCall(name=ToolName.TOPOLOGY, arguments={}),
                        output=topology,
                    ),
                ]
                finding = await self._llm.analyze(
                    {"anomalies": state.detection_result, "diagnosis_hint": diagnosis},
                    evidence,
                )
                diagnosis["hypothesis"] = finding.hypothesis
                diagnosis["rationale"] = finding.rationale
                diagnosis["llm_enriched"] = True
            except Exception:
                diagnosis["llm_enriched"] = False

        return AgentAction(
            kind=ActionKind.FINAL,
            final_output=diagnosis,
            reasoning=diagnosis.get("hypothesis", "Deterministic root cause analysis complete"),
        )

    def _analyze_root_cause(
        self,
        features: dict[str, Any],
        topology: dict[str, Any],
        state: CognitiveState,
        reflection: str | None,
    ) -> dict[str, Any]:
        """Deterministic root cause analysis using feature importance + rules."""
        del state
        evidence_id = str(uuid4())
        hypothesis = "Unknown root cause"
        confidence = 0.5
        recommended_action = "investigate_only"

        # Rule-based diagnosis from feature patterns
        avg_bitrate = features.get("avg_bitrate_kbps", 0)
        stall_ratio = features.get("stall_ratio", 0)
        cdn_load = topology.get("cdn_edge_cpu_pct", 0)
        packet_loss = features.get("packet_loss_pct", 0)

        if isinstance(cdn_load, (int, float)) and cdn_load > 85:
            hypothesis = "CDN edge node saturation causing bitrate throttling"
            confidence = 0.85
            recommended_action = "scale_cdn_edge"
        elif isinstance(packet_loss, (int, float)) and packet_loss > 2.0:
            hypothesis = "Network packet loss degrading stream quality"
            confidence = 0.75
            recommended_action = "reroute_traffic"
        elif (
            isinstance(avg_bitrate, (int, float))
            and avg_bitrate < 2000
            and isinstance(stall_ratio, (int, float))
            and stall_ratio > 3.0
        ):
            hypothesis = "Insufficient bandwidth allocation for affected segment"
            confidence = 0.70
            recommended_action = "increase_bandwidth_allocation"
        elif isinstance(stall_ratio, (int, float)) and stall_ratio > 5.0:
            hypothesis = "Origin server response time degradation causing stalls"
            confidence = 0.65
            recommended_action = "scale_origin"

        # Reflexion: adjust confidence down if this is a retry
        if reflection:
            confidence *= 0.9  # Reduce confidence on retry

        return {
            "hypothesis": hypothesis,
            "confidence": confidence,
            "recommended_action": recommended_action,
            "evidence_ids": [evidence_id],
            "contributing_factors": {
                "cdn_load": cdn_load,
                "packet_loss": packet_loss,
                "avg_bitrate": avg_bitrate,
                "stall_ratio": stall_ratio,
            },
            "llm_enriched": False,
            "reflection_applied": reflection is not None,
        }
