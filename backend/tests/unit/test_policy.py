from pathlib import Path
from uuid import uuid4

from stromwart.contracts.actions import ProposalCreate, ProposalState
from stromwart.policies.service import PolicyService


def service() -> PolicyService:
    root = Path(__file__).parents[2]
    return PolicyService(
        root / "configs/policies/action_allowlist.yaml",
        root / "configs/policies/live_event_guardrails.yaml",
    )


def proposal(**changes: object) -> ProposalCreate:
    values: dict[str, object] = {
        "action_type": "increase_cdn_capacity",
        "target_scope": {"session_count": 50},
        "rationale": "Stall ratio exceeds the critical threshold.",
        "expected_effect": "Reduce rebuffering.",
        "confidence": 0.9,
        "risk_score": 0.2,
        "evidence_ids": [uuid4()],
    }
    values.update(changes)
    return ProposalCreate(**values)


def test_low_risk_valid_proposal_can_simulate() -> None:
    decision = service().evaluate(proposal(), evidence_is_valid=True)

    assert decision.state is ProposalState.SIMULATE


def test_invalid_evidence_blocks_proposal() -> None:
    decision = service().evaluate(proposal(), evidence_is_valid=False)

    assert decision.state is ProposalState.BLOCKED


def test_high_risk_requires_human_approval() -> None:
    decision = service().evaluate(
        proposal(risk_score=0.8),
        evidence_is_valid=True,
    )

    assert decision.state is ProposalState.APPROVAL_REQUIRED


def test_unknown_action_is_blocked() -> None:
    decision = service().evaluate(
        proposal(action_type="delete_everything"),
        evidence_is_valid=True,
    )

    assert decision.state is ProposalState.BLOCKED
    assert "action_type is not permitted" in decision.reasons