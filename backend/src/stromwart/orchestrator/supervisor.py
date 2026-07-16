from __future__ import annotations

import time
from enum import StrEnum
from typing import Any

from stromwart.agents.base import AgentResult, BaseAgent
from stromwart.orchestrator.state import AgentStepRecord, CognitiveState, IncidentPhase
from stromwart.orchestrator.step_verifier import verify_agent_step


class SupervisorDecision(StrEnum):
    DISPATCH_DETECTOR = "dispatch_detector"
    DISPATCH_DIAGNOSTICIAN = "dispatch_diagnostician"
    DISPATCH_MITIGATOR = "dispatch_mitigator"
    DISPATCH_VERIFIER = "dispatch_verifier"
    ESCALATE_HUMAN = "escalate_human"
    IDLE = "idle"


class Supervisor:
    """
    Deterministic OODA supervisor. No LLM dependency.
    Routes to specialist agents based on cognitive state.
    """

    def __init__(
        self,
        agents: dict[str, BaseAgent],
        enabled_agents: dict[str, bool] | None = None,
    ) -> None:
        self._agents = agents
        self._enabled = enabled_agents or dict.fromkeys(agents, True)

    # ─── OBSERVE ───────────────────────────────────────────────

    def observe(self, state: CognitiveState, raw_signals: dict[str, Any]) -> CognitiveState:
        """Ingest raw signals (telemetry, alerts, model outputs) into state."""
        state.latest_kpis = raw_signals.get("kpis", state.latest_kpis)
        state.unprocessed_alerts = raw_signals.get("new_alerts", state.unprocessed_alerts)
        state.active_sessions_count = raw_signals.get("session_count", state.active_sessions_count)
        state.qoe_prediction = raw_signals.get("qoe_prediction", state.qoe_prediction)
        state.prediction_confidence = raw_signals.get(
            "prediction_confidence", state.prediction_confidence
        )
        state.forecast_trend = raw_signals.get("forecast_trend", state.forecast_trend)
        state.drift_detected = raw_signals.get("drift_detected", state.drift_detected)
        state.has_unprocessed_alerts = len(state.unprocessed_alerts) > 0
        return state

    # ─── ORIENT ────────────────────────────────────────────────

    def orient(self, state: CognitiveState) -> CognitiveState:
        """Contextualize observations. Classify severity using ML model outputs."""
        # Severity classification based on QoE prediction + alerts
        if state.qoe_prediction is not None:
            if state.qoe_prediction < 3.0:
                state.severity_classification = "critical"
            elif state.qoe_prediction < 3.5:
                state.severity_classification = "high"
            elif state.qoe_prediction < 4.0:
                state.severity_classification = "medium"
            else:
                state.severity_classification = "low"
        elif state.has_unprocessed_alerts:
            # Fallback: classify by alert severity
            severities = [alert.get("severity", "low") for alert in state.unprocessed_alerts]
            if "critical" in severities:
                state.severity_classification = "critical"
            elif "high" in severities:
                state.severity_classification = "high"
            else:
                state.severity_classification = "medium"
        else:
            state.severity_classification = "low"

        return state

    # ─── DECIDE ────────────────────────────────────────────────

    def decide(self, state: CognitiveState) -> SupervisorDecision:
        """Deterministic routing rules. No LLM."""
        reasons: list[str] = []

        # Escalation check
        if state.verification_failed and state.retry_count >= state.max_retries:
            reasons.append(f"verification failed {state.retry_count} times, escalating")
            state.decision_reasons = reasons
            return SupervisorDecision.ESCALATE_HUMAN

        # Reflexion: retry diagnosis after verification failure
        if state.verification_failed and state.retry_count < state.max_retries:
            reasons.append("verification failed, retrying with reflexion feedback")
            state.decision_reasons = reasons
            return SupervisorDecision.DISPATCH_DIAGNOSTICIAN

        # Normal flow
        if state.has_unprocessed_alerts and not state.detection_complete:
            if not self._enabled.get("detector", True):
                state.detection_complete = True
                reasons.append("detector disabled, skipping")
            else:
                reasons.append("unprocessed alerts detected")
                state.decision_reasons = reasons
                return SupervisorDecision.DISPATCH_DETECTOR

        if state.detection_complete and not state.diagnosis_complete:
            if not self._enabled.get("diagnostician", True):
                state.diagnosis_complete = True
                reasons.append("diagnostician disabled, skipping")
            else:
                reasons.append("detection complete, proceeding to diagnosis")
                state.decision_reasons = reasons
                return SupervisorDecision.DISPATCH_DIAGNOSTICIAN

        if state.diagnosis_complete and not state.mitigation_proposed:
            if not self._enabled.get("mitigator", True):
                state.mitigation_proposed = True
                reasons.append("mitigator disabled, skipping")
            else:
                reasons.append("diagnosis complete, generating mitigation proposal")
                state.decision_reasons = reasons
                return SupervisorDecision.DISPATCH_MITIGATOR

        if state.action_executed and not state.action_verified:
            if not self._enabled.get("verifier", True):
                state.action_verified = True
                reasons.append("verifier disabled, skipping")
            else:
                reasons.append("action executed, verifying effect")
                state.decision_reasons = reasons
                return SupervisorDecision.DISPATCH_VERIFIER

        reasons.append("no actionable state transition")
        state.decision_reasons = reasons
        return SupervisorDecision.IDLE

    # ─── ACT ──────────────────────────────────────────────────

    async def act(
        self,
        decision: SupervisorDecision,
        state: CognitiveState,
    ) -> CognitiveState:
        """Dispatch to specialist agent and update state with result."""
        if decision == SupervisorDecision.IDLE:
            return state

        if decision == SupervisorDecision.ESCALATE_HUMAN:
            state.human_escalation_required = True
            state.phase = IncidentPhase.ESCALATED
            return state

        agent_map = {
            SupervisorDecision.DISPATCH_DETECTOR: "detector",
            SupervisorDecision.DISPATCH_DIAGNOSTICIAN: "diagnostician",
            SupervisorDecision.DISPATCH_MITIGATOR: "mitigator",
            SupervisorDecision.DISPATCH_VERIFIER: "verifier",
        }

        agent_name = agent_map.get(decision)
        if agent_name is None or agent_name not in self._agents:
            return state

        agent = self._agents[agent_name]

        # Build reflexion context if retrying
        reflection: str | None = None
        if state.verification_failed and state.reflection_feedback:
            reflection = "; ".join(state.reflection_feedback)

        # Execute agent
        start = time.monotonic()
        result = await agent.run(state, reflection)
        elapsed = (time.monotonic() - start) * 1000
        duration_ms = max(elapsed, result.duration_ms)
        reflection_result = verify_agent_step(agent_name, result)

        # Record step
        state.step_history.append(
            AgentStepRecord(
                agent_name=agent_name,
                action=decision.value,
                observation=result.output,
                duration_ms=duration_ms,
                success=result.success,
                error=None if result.success else str(result.output.get("error")),
                stop_reason=result.stop_reason,
                llm_enriched=bool(result.output.get("llm_enriched")),
                step_reflection=reflection_result.as_dict(),
            )
        )

        # Update state based on which agent ran
        self._apply_result(agent_name, result, state)
        return state

    def _apply_result(self, agent_name: str, result: AgentResult, state: CognitiveState) -> None:
        if agent_name == "detector":
            state.detection_result = result.output
            state.detection_complete = True
            state.phase = IncidentPhase.DETECTING
            if not result.output.get("anomalies_detected", False):
                state.phase = IncidentPhase.IDLE
                state.has_unprocessed_alerts = False

        elif agent_name == "diagnostician":
            state.diagnosis_result = result.output
            state.diagnosis_complete = True
            state.phase = IncidentPhase.DIAGNOSING

        elif agent_name == "mitigator":
            state.mitigation_proposal = result.output
            state.mitigation_proposed = True
            state.phase = IncidentPhase.MITIGATING

        elif agent_name == "verifier":
            state.verification_result = result.output
            state.action_verified = True
            state.phase = IncidentPhase.VERIFYING

            if not result.output.get("passed", False):
                state.verification_failed = True
                state.retry_count += 1
                state.diagnosis_complete = False
                state.mitigation_proposed = False
                state.action_executed = False
                state.action_verified = False
                # Add reflexion feedback
                reasons = result.output.get("reasons", [])
                if isinstance(reasons, list):
                    state.reflection_feedback.extend(str(reason) for reason in reasons)
            else:
                state.phase = IncidentPhase.RESOLVED

    # ─── FULL CYCLE ───────────────────────────────────────────

    async def cycle(self, state: CognitiveState, signals: dict[str, Any]) -> CognitiveState:
        """Run one full OODA cycle."""
        state = self.observe(state, signals)
        state = self.orient(state)
        decision = self.decide(state)
        state.current_decision = decision.value
        state = await self.act(decision, state)
        return state
