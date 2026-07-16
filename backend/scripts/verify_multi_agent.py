"""Verification script for pack_multi_agent checklist items."""

from __future__ import annotations

import asyncio

from stromwart.agents.base import Budget, GuardrailBlocked, Step
from stromwart.agents.detector import DetectorAgent
from stromwart.agents.diagnostician import DiagnosticianAgent
from stromwart.agents.guardrails import AgentGuardrails, GuardrailPolicy
from stromwart.agents.mitigator import MitigatorAgent
from stromwart.agents.tools import ToolGateway, ToolSpec
from stromwart.agents.verifier import VerifierAgent
from stromwart.evals.scorers import DeterministicScorer
from stromwart.evals.tracer import AgentTracer
from stromwart.orchestrator.state import CognitiveState
from stromwart.orchestrator.supervisor import Supervisor


async def _handler(args: dict) -> dict:
    event_id = args.get("event_id")
    name = args.get("action_type", "telemetry")
    if name == "scale_cdn_edge" or args.get("window_minutes") == 2:
        return {"avg_mos": 3.8, "buffer_ratio": 2.0, "event_id": event_id}
    if "slices" in args:
        return {
            "avg_bitrate_kbps": 1800,
            "stall_ratio": 4.0,
            "packet_loss_pct": 1.5,
        }
    if "action_type" in args:
        return {"action_type": args["action_type"], "steps": ["verify"]}
    if args.get("event_id") and len(args) == 1:
        return {"cdn_edge_cpu_pct": 90}
    return {"avg_mos": 3.2, "buffer_ratio": 4.5, "event_id": event_id}


async def _predictions_handler(args: dict) -> dict:
    del args
    return {"predicted_mos": 4.2}


def _build_supervisor() -> Supervisor:
    gateway = ToolGateway([
        ToolSpec("telemetry", "telemetry", _handler),
        ToolSpec("features", "features", _handler),
        ToolSpec("predictions", "predictions", _predictions_handler),
        ToolSpec("topology", "topology", _handler),
        ToolSpec("runbook", "runbook", _handler),
    ])
    guardrails = AgentGuardrails()
    budget = Budget(max_steps=10, max_seconds=30.0)
    agents = {
        "detector": DetectorAgent(gateway, guardrails, budget),
        "diagnostician": DiagnosticianAgent(gateway, guardrails, budget),
        "mitigator": MitigatorAgent(gateway, guardrails, budget),
        "verifier": VerifierAgent(gateway, guardrails, budget),
    }
    return Supervisor(agents)


async def main() -> None:
    supervisor = _build_supervisor()
    state = CognitiveState(event_id="evt-1", max_retries=2)
    signals = {
        "kpis": {"avg_mos": 3.1, "buffer_ratio": 4.0},
        "new_alerts": [{"severity": "high", "message": "mos drop"}],
        "session_count": 100,
        "qoe_prediction": 3.2,
    }

    # Detector cycle
    state = await supervisor.cycle(state, signals)
    assert state.detection_complete
    assert state.detection_result is not None
    assert state.detection_result["anomalies_detected"] is True

    # Diagnostician cycle
    state = await supervisor.cycle(state, signals)
    assert state.diagnosis_complete
    assert state.diagnosis_result is not None
    assert "evidence_ids" in state.diagnosis_result

    # Mitigator cycle
    state = await supervisor.cycle(state, signals)
    assert state.mitigation_proposed
    assert state.mitigation_proposal is not None
    assert state.mitigation_proposal["action_type"] in {
        "scale_cdn_edge",
        "reroute_traffic",
        "increase_bandwidth_allocation",
        "scale_origin",
        "investigate_only",
    }

    # Verifier cycle (simulate action executed)
    state.action_executed = True
    state = await supervisor.cycle(state, signals)
    assert state.action_verified

    # Eval scorer produces 5 dimensions
    tracer = AgentTracer()
    tracer.start_trace()
    tracer.start_span("tool telemetry", "detector")
    tracer.end_span("ok", {"evidence_ids": ["abc"]})
    tracer.start_span("final diagnosis", "diagnostician")
    tracer.end_span("ok", {"hypothesis": "test", "evidence_ids": ["abc"]})
    trace = tracer.end_trace()
    assert trace is not None
    scores = DeterministicScorer().score_all(trace)
    assert len(scores) == 5

    # Guardrails block consecutive failures
    guardrails = AgentGuardrails(
        policies={"detector": GuardrailPolicy(max_consecutive_failures=2)}
    )
    from stromwart.agents.base import AgentAction, ActionKind, Observation

    history = [
        Step(
            action=AgentAction(kind=ActionKind.TOOL, tool_name="telemetry"),
            observation=Observation("telemetry", {}, success=False, error="fail"),
        ),
        Step(
            action=AgentAction(kind=ActionKind.TOOL, tool_name="telemetry"),
            observation=Observation("telemetry", {}, success=False, error="fail"),
        ),
    ]
    try:
        guardrails.pre_check("detector", CognitiveState(), history)
        raise AssertionError("expected GuardrailBlocked")
    except GuardrailBlocked:
        pass

    print("all verification checks passed")


if __name__ == "__main__":
    asyncio.run(main())
