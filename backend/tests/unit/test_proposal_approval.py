from stromwart.contracts.actions import ApprovalCreate
from stromwart.persistence import ProposalRow
from stromwart.repositories.actions import ActionRepository


class _FakeSession:
    def add(self, _row: object) -> None:
        return None

    async def flush(self) -> None:
        return None


def test_record_approval_simulate_to_approved() -> None:
    proposal = ProposalRow(
        incident_id="inc-1",
        action_type="increase_cdn_capacity",
        target_scope={"session_count": 100},
        rationale="test",
        expected_effect="test",
        confidence=0.8,
        risk_score=0.1,
        evidence_ids=["ev-1"],
        policy_state="simulate",
        policy_reasons=[],
    )
    repo = ActionRepository(_FakeSession())  # type: ignore[arg-type]
    value = ApprovalCreate(
        approved=True,
        actor_id="operator",
        reason="Operator approved remediation",
    )

    import asyncio

    asyncio.run(repo.record_approval(proposal, value, next_state="approved"))

    assert proposal.policy_state == "approved"
    assert proposal.policy_reasons == [value.reason]


def test_record_approval_reject_to_blocked() -> None:
    proposal = ProposalRow(
        incident_id="inc-1",
        action_type="increase_cdn_capacity",
        target_scope={"session_count": 100},
        rationale="test",
        expected_effect="test",
        confidence=0.8,
        risk_score=0.1,
        evidence_ids=["ev-1"],
        policy_state="simulate",
        policy_reasons=[],
    )
    repo = ActionRepository(_FakeSession())  # type: ignore[arg-type]
    value = ApprovalCreate(
        approved=False,
        actor_id="operator",
        reason="Operator rejected remediation",
    )

    import asyncio

    asyncio.run(repo.record_approval(proposal, value, next_state="blocked"))

    assert proposal.policy_state == "blocked"
