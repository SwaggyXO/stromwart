from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from stromwart.contracts.actions import ApprovalCreate, ProposalCreate
from stromwart.persistence import ExecutionRow, ProposalRow


class ActionRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get(self, proposal_id: UUID) -> ProposalRow | None:
        return await self._session.get(ProposalRow, str(proposal_id))

    async def list_for_incident(
        self,
        incident_id: UUID,
        limit: int = 50,
    ) -> list[ProposalRow]:
        statement = (
            select(ProposalRow)
            .where(ProposalRow.incident_id == str(incident_id))
            .order_by(ProposalRow.created_at.desc())
            .limit(limit)
        )
        return list((await self._session.scalars(statement)).all())

    async def create(
        self,
        incident_id: UUID,
        value: ProposalCreate,
        state: str,
        reasons: list[str],
    ) -> ProposalRow:
        row = ProposalRow(
            incident_id=str(incident_id),
            action_type=value.action_type,
            target_scope=value.target_scope,
            rationale=value.rationale,
            expected_effect=value.expected_effect,
            confidence=value.confidence,
            risk_score=value.risk_score,
            evidence_ids=[str(item) for item in value.evidence_ids],
            policy_state=state,
            policy_reasons=reasons,
        )
        self._session.add(row)
        await self._session.flush()
        return row

    async def record_approval(
        self,
        proposal: ProposalRow,
        value: ApprovalCreate,
        *,
        next_state: str | None = None,
    ) -> ExecutionRow:
        if next_state is not None:
            proposal.policy_state = next_state
        else:
            proposal.policy_state = "simulate" if value.approved else "blocked"
        proposal.policy_reasons = [value.reason]

        row = ExecutionRow(
            proposal_id=proposal.id,
            mode="approval",
            approved=value.approved,
            approved_by=value.actor_id,
            approval_reason=value.reason,
        )
        self._session.add(row)
        await self._session.flush()
        return row

    async def record_simulation(
        self,
        proposal_id: UUID,
        result: dict[str, object],
    ) -> ExecutionRow:
        row = ExecutionRow(
            proposal_id=str(proposal_id),
            mode="simulation",
            simulated_result=result,
        )
        self._session.add(row)
        await self._session.flush()
        return row
