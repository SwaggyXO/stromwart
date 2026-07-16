from uuid import UUID

from stromwart.contracts.actions import SimulationRead
from stromwart.errors import InvalidStateError, NotFoundError
from stromwart.persistence import ProposalRow


class SimulationService:
    _effectiveness = {
        "increase_cdn_capacity": 0.55,
        "adjust_traffic_routing": 0.45,
        "recommend_abr_profile": 0.25,
        "investigate_only": 0.0,
    }

    def simulate(self, proposal: ProposalRow) -> SimulationRead:
        if proposal.policy_state != "simulate":
            raise InvalidStateError("policy does not permit simulation")

        base_effect = self._effectiveness.get(proposal.action_type)
        if base_effect is None:
            raise NotFoundError("no simulation model is defined for action type")

        reduction = base_effect * proposal.confidence * (1 - proposal.risk_score * 0.2)

        return SimulationRead(
            proposal_id=UUID(proposal.id),
            successful=reduction > 0,
            projected_risk_reduction=round(reduction, 4),
            projected_affected_sessions=int(
                proposal.target_scope.get("session_count", 0)
            ),
            explanation=(
                f"Projected risk reduction is {round(reduction * 100, 1)}% "
                f"for '{proposal.action_type}'."
            ),
        )
