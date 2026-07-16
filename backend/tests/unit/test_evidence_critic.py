from uuid import uuid4

from stromwart.agents.critic import EvidenceCritic
from stromwart.contracts.agents import (
    AnalystFinding,
    ToolCall,
    ToolName,
    ToolResult,
)


def test_critic_accepts_grounded_telemetry_finding() -> None:
    evidence_id = uuid4()
    finding = AnalystFinding(
        hypothesis="The selected CDN slice has insufficient throughput.",
        confidence=0.7,
        evidence_ids=[evidence_id],
        missing_evidence=[],
        recommended_action="increase_cdn_capacity",
        rationale="Telemetry shows sustained throughput degradation.",
    )
    result = ToolResult(
        call=ToolCall(name=ToolName.TELEMETRY, arguments={}),
        output={"throughput_mean_kbps": 800},
        evidence_ids=[evidence_id],
    )

    reflection = EvidenceCritic().review(finding, [result])

    assert reflection.accepted is True


def test_critic_rejects_unknown_evidence() -> None:
    finding = AnalystFinding(
        hypothesis="Unverified root cause.",
        confidence=0.6,
        evidence_ids=[uuid4()],
        missing_evidence=[],
        recommended_action="investigate_only",
        rationale="No tool result supports this claim.",
    )

    reflection = EvidenceCritic().review(finding, [])

    assert reflection.accepted is False
    assert "finding cites evidence unavailable from tools" in reflection.reasons