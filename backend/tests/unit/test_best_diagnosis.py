from stromwart.orchestrator.state import AgentStepRecord, CognitiveState
from stromwart.simulation.engine import _best_diagnostician_observation


def test_best_diagnostician_prefers_known_hypothesis() -> None:
    state = CognitiveState()
    state.step_history = [
        AgentStepRecord(
            agent_name="diagnostician",
            action="dispatch_diagnostician",
            observation={
                "hypothesis": "CDN edge node saturation causing bitrate throttling",
                "confidence": 0.85,
            },
        ),
        AgentStepRecord(
            agent_name="diagnostician",
            action="dispatch_diagnostician",
            observation={
                "hypothesis": "Unknown root cause",
                "confidence": 0.45,
            },
        ),
    ]

    best = _best_diagnostician_observation(state)
    assert best is not None
    assert "CDN edge" in str(best.get("hypothesis"))
