from stromwart.agents.base import AgentResult, Step
from stromwart.orchestrator.step_verifier import verify_agent_step


def test_verify_agent_step_passes_successful_detector() -> None:
    result = AgentResult(
        success=True,
        output={"anomalies_detected": True, "anomalies": []},
        steps=[],
        duration_ms=0.5,
        stop_reason="success",
    )
    reflection = verify_agent_step("detector", result)
    assert reflection.passed
    assert "agent_success" in reflection.checks


def test_verify_agent_step_fails_missing_keys() -> None:
    result = AgentResult(
        success=True,
        output={},
        steps=[],
        duration_ms=1.0,
        stop_reason="success",
    )
    reflection = verify_agent_step("mitigator", result)
    assert not reflection.passed
    assert reflection.reasons
