from __future__ import annotations

from typing import Any

from stromwart.agents.base import ActionKind, AgentAction, BaseAgent, Step
from stromwart.orchestrator.state import CognitiveState


class DetectorAgent(BaseAgent):
    """
    Anomaly and threshold detection agent.
    Purely deterministic — uses ML model predictions + threshold rules.
    No LLM dependency.
    """

    name = "detector"

    async def _decide(
        self,
        state: CognitiveState,
        history: list[Step],
        reflection: str | None,
    ) -> AgentAction:
        del reflection

        # Step 1: If no observations yet, gather telemetry
        if not history:
            return AgentAction(
                kind=ActionKind.TOOL,
                tool_name="telemetry",
                tool_args={"event_id": state.event_id, "window_minutes": 5},
                reasoning="Gathering recent telemetry for anomaly detection",
            )

        # Step 2: If telemetry gathered, get predictions
        if len(history) == 1 and history[0].observation and history[0].observation.success:
            return AgentAction(
                kind=ActionKind.TOOL,
                tool_name="predictions",
                tool_args={"event_id": state.event_id},
                reasoning="Getting QoE model predictions to compare against actuals",
            )

        # Step 3: Analyze and produce detection result
        telemetry = history[0].observation.output if history[0].observation else {}
        predictions = (
            history[1].observation.output if len(history) > 1 and history[1].observation else {}
        )

        anomalies = self._detect_anomalies(telemetry, predictions, state)

        return AgentAction(
            kind=ActionKind.FINAL,
            final_output={
                "anomalies_detected": len(anomalies) > 0,
                "anomalies": anomalies,
                "severity": self._classify_severity(anomalies),
                "affected_slices": self._extract_slices(anomalies),
            },
            reasoning="Detection complete based on threshold + prediction comparison",
        )

    def _detect_anomalies(
        self,
        telemetry: dict[str, Any],
        predictions: dict[str, Any],
        state: CognitiveState,
    ) -> list[dict[str, Any]]:
        del state
        anomalies: list[dict[str, Any]] = []

        # Threshold-based detection
        mos = telemetry.get("avg_mos", 0)
        if isinstance(mos, (int, float)) and mos < 3.5:
            anomalies.append(
                {
                    "type": "threshold_breach",
                    "metric": "avg_mos",
                    "value": mos,
                    "threshold": 3.5,
                    "severity": "high" if mos < 3.0 else "medium",
                }
            )

        buffer_ratio = telemetry.get("buffer_ratio", 0)
        if isinstance(buffer_ratio, (int, float)) and buffer_ratio > 3.0:
            anomalies.append(
                {
                    "type": "threshold_breach",
                    "metric": "buffer_ratio",
                    "value": buffer_ratio,
                    "threshold": 3.0,
                    "severity": "high" if buffer_ratio > 5.0 else "medium",
                }
            )

        # Prediction-based detection (compare actual vs predicted)
        predicted_mos = predictions.get("predicted_mos")
        if predicted_mos is not None and isinstance(mos, (int, float)) and mos > 0:
            residual = abs(mos - predicted_mos)
            if residual > 0.5:
                anomalies.append(
                    {
                        "type": "prediction_deviation",
                        "metric": "mos_residual",
                        "actual": mos,
                        "predicted": predicted_mos,
                        "residual": residual,
                        "severity": "high" if residual > 1.0 else "medium",
                    }
                )

        return anomalies

    def _classify_severity(self, anomalies: list[dict[str, Any]]) -> str:
        if any(anomaly["severity"] == "high" for anomaly in anomalies):
            return "high"
        if anomalies:
            return "medium"
        return "low"

    def _extract_slices(self, anomalies: list[dict[str, Any]]) -> list[str]:
        slices: set[str] = set()
        for anomaly in anomalies:
            if "slice" in anomaly:
                slices.add(str(anomaly["slice"]))
        return list(slices) if slices else ["global"]
