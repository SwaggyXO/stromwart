from uuid import UUID

from stromwart.contracts.actions import ApprovalCreate, ProposalCreate
from stromwart.contracts.operations import IncidentState
from stromwart.database import Database
from stromwart.errors import InvalidStateError, NotFoundError
from stromwart.persistence import ProposalRow
from stromwart.policies.service import PolicyService
from stromwart.repositories.actions import ActionRepository
from stromwart.repositories.audit import AuditRepository
from stromwart.repositories.incidents import IncidentRepository


class ProposalService:
    def __init__(self, database: Database, policies: PolicyService) -> None:
        self._database = database
        self._policies = policies

    async def create(
        self,
        incident_id: UUID,
        value: ProposalCreate,
        correlation_id: str,
    ) -> ProposalRow:
        async with self._database.transaction() as uow:
            incidents = IncidentRepository(uow.session)
            actions = ActionRepository(uow.session)
            audit = AuditRepository(uow.session)

            incident = await incidents.get_incident(incident_id)
            if incident is None:
                raise NotFoundError("incident does not exist")

            allowed_states = {
                IncidentState.INVESTIGATING.value,
                IncidentState.ASSESSED.value,
            }
            if incident.state not in allowed_states:
                raise InvalidStateError("incident is not ready for proposals")

            evidence_is_valid = set(map(str, value.evidence_ids)).issubset(
                set(incident.evidence_ids)
            )
            decision = self._policies.evaluate(value, evidence_is_valid)
            proposal = await actions.create(
                incident_id,
                value,
                decision.state.value,
                decision.reasons,
            )

            if decision.state.value in {
                "observe",
                "simulate",
                "approval_required",
            }:
                incident.state = IncidentState.ASSESSED.value
                await uow.flush()

            await audit.append(
                correlation_id=correlation_id,
                actor_type="policy",
                artifact_type="proposal",
                artifact_id=proposal.id,
                payload={
                    "state": decision.state.value,
                    "reasons": decision.reasons,
                    "evidence_is_valid": evidence_is_valid,
                },
            )
            return proposal

    async def approve(
        self,
        proposal_id: UUID,
        value: ApprovalCreate,
        correlation_id: str,
    ) -> ProposalRow:
        async with self._database.transaction() as uow:
            actions = ActionRepository(uow.session)
            audit = AuditRepository(uow.session)

            proposal = await actions.get(proposal_id)
            if proposal is None:
                raise NotFoundError("proposal does not exist")

            approvable = {"approval_required", "simulate"}
            if proposal.policy_state not in approvable:
                raise InvalidStateError(
                    f"proposal in state '{proposal.policy_state}' cannot be approved or rejected"
                )

            if not value.approved:
                next_state = "blocked"
            elif proposal.policy_state == "approval_required":
                next_state = "simulate"
            else:
                next_state = "approved"

            await actions.record_approval(proposal, value, next_state=next_state)
            await audit.append(
                correlation_id=correlation_id,
                actor_type="human",
                artifact_type="proposal_approval",
                artifact_id=proposal.id,
                payload=value.model_dump(mode="json"),
            )
            return proposal
