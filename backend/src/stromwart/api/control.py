from uuid import UUID

from fastapi import APIRouter, Request, status

from stromwart.api.serializers import alert_read, incident_read, proposal_read
from stromwart.application.dependencies import ContainerDep, UnitOfWorkDep
from stromwart.contracts.actions import (
    ApprovalCreate,
    ProposalCreate,
    ProposalRead,
    RejectCreate,
    SimulationRead,
)
from stromwart.contracts.features import FeatureVector
from stromwart.contracts.operations import AlertRead, AlertState, IncidentRead, IncidentState
from stromwart.errors import InvalidStateError, NotFoundError
from stromwart.repositories.actions import ActionRepository
from stromwart.repositories.audit import AuditRepository
from stromwart.repositories.incidents import IncidentRepository

router = APIRouter(tags=["control"])


@router.post(
    "/events/{event_id}/detect",
    response_model=IncidentRead | None,
    summary="Detect incident",
    description=(
        "Run alert rules against a feature vector. "
        "Returns an incident if thresholds are breached, or null if healthy."
    ),
)
async def detect_incident(
    event_id: UUID,
    features: FeatureVector,
    affected_slice: dict[str, str | None],
    container: ContainerDep,
) -> IncidentRead | None:
    incident = await container.incidents.detect(event_id, affected_slice, features)
    if incident is None:
        return None
    row, _created, _alerts = incident
    return incident_read(row)


@router.get(
    "/incidents/{incident_id}",
    response_model=IncidentRead,
    summary="Get incident",
    description="Retrieve full incident details including evidence IDs and hypothesis.",
)
async def get_incident(
    incident_id: UUID,
    uow: UnitOfWorkDep,
) -> IncidentRead:
    incident = await IncidentRepository(uow.session).get_incident(incident_id)
    if incident is None:
        raise NotFoundError("incident does not exist")
    return incident_read(incident)


@router.get(
    "/incidents/{incident_id}/proposals",
    response_model=list[ProposalRead],
    summary="List incident proposals",
    description="Return remediation proposals for an incident, newest first.",
)
async def list_incident_proposals(
    incident_id: UUID,
    uow: UnitOfWorkDep,
    limit: int = 50,
) -> list[ProposalRead]:
    incidents = IncidentRepository(uow.session)
    if await incidents.get_incident(incident_id) is None:
        raise NotFoundError("incident does not exist")
    rows = await ActionRepository(uow.session).list_for_incident(incident_id, limit=limit)
    return [proposal_read(row) for row in rows]


@router.post(
    "/alerts/{alert_id}/acknowledge",
    response_model=AlertRead,
    summary="Acknowledge alert",
    description="Mark an open alert as acknowledged by an operator.",
)
async def acknowledge_alert(
    alert_id: UUID,
    uow: UnitOfWorkDep,
) -> AlertRead:
    repository = IncidentRepository(uow.session)
    audit = AuditRepository(uow.session)
    alert = await repository.get_alert(alert_id)
    if alert is None:
        raise NotFoundError("alert does not exist")
    if alert.state != AlertState.OPEN.value:
        raise InvalidStateError("alert is not open")

    await repository.acknowledge_alert(alert)
    await audit.append(
        str(alert.id),
        "human",
        "alert",
        alert.id,
        {
            "transition": "acknowledged",
            "alert_id": alert.id,
            "event_id": alert.event_id,
            "rule_id": alert.rule_id,
            "slice_key": alert.slice_key,
            "severity": alert.severity,
        },
    )
    return alert_read(alert)


@router.post(
    "/incidents/{incident_id}/investigate",
    response_model=IncidentRead,
    summary="Start investigation",
    description="Transition incident from DETECTED to INVESTIGATING state.",
)
async def investigate(
    incident_id: UUID,
    request: Request,
    uow: UnitOfWorkDep,
) -> IncidentRead:
    repository = IncidentRepository(uow.session)
    audit = AuditRepository(uow.session)
    incident = await repository.get_incident(incident_id)

    if incident is None:
        raise NotFoundError("incident does not exist")
    if incident.state != IncidentState.DETECTED.value:
        raise InvalidStateError("incident cannot enter investigation")

    incident.state = IncidentState.INVESTIGATING.value
    await uow.flush()
    await audit.append(
        request.state.correlation_id,
        "operator",
        "incident",
        incident.id,
        {"transition": "investigating"},
    )
    return incident_read(incident)


@router.post(
    "/incidents/{incident_id}/proposals",
    response_model=ProposalRead,
    status_code=status.HTTP_201_CREATED,
    summary="Create mitigation proposal",
    description=(
        "Submit a mitigation proposal. The deterministic policy verifier evaluates it "
        "and assigns a state (SIMULATE, BLOCKED, APPROVAL_REQUIRED, etc.)."
    ),
)
async def create_proposal(
    incident_id: UUID,
    value: ProposalCreate,
    request: Request,
    container: ContainerDep,
) -> ProposalRead:
    proposal = await container.proposals.create(
        incident_id,
        value,
        request.state.correlation_id,
    )
    return proposal_read(proposal)


@router.post(
    "/proposals/{proposal_id}/approve",
    response_model=ProposalRead,
    summary="Approve or reject proposal",
    description=(
        "Human operator decision for a proposal in APPROVAL_REQUIRED or SIMULATE. "
        "Pass approved=true to allow simulation or sign off, or approved=false to reject/block. "
        "Prefer POST /proposals/{id}/reject for an explicit reject route."
    ),
)
async def approve_proposal(
    proposal_id: UUID,
    value: ApprovalCreate,
    request: Request,
    container: ContainerDep,
) -> ProposalRead:
    proposal = await container.proposals.approve(
        proposal_id,
        value,
        request.state.correlation_id,
    )
    return proposal_read(proposal)


@router.post(
    "/proposals/{proposal_id}/reject",
    response_model=ProposalRead,
    summary="Reject proposal",
    description=(
        "Explicit reject for a proposal awaiting approval. "
        "Equivalent to POST /approve with approved=false."
    ),
)
async def reject_proposal(
    proposal_id: UUID,
    value: RejectCreate,
    request: Request,
    container: ContainerDep,
) -> ProposalRead:
    proposal = await container.proposals.approve(
        proposal_id,
        ApprovalCreate(approved=False, actor_id=value.actor_id, reason=value.reason),
        request.state.correlation_id,
    )
    return proposal_read(proposal)


@router.post(
    "/proposals/{proposal_id}/simulate",
    response_model=SimulationRead,
    summary="Simulate proposal",
    description=(
        "Run the action through the simulation engine. "
        "Returns projected risk reduction and affected session count."
    ),
)
async def simulate_proposal(
    proposal_id: UUID,
    request: Request,
    uow: UnitOfWorkDep,
    container: ContainerDep,
) -> SimulationRead:
    actions = ActionRepository(uow.session)
    audit = AuditRepository(uow.session)
    proposal = await actions.get(proposal_id)

    if proposal is None:
        raise NotFoundError("proposal does not exist")

    result = container.simulation.simulate(proposal)
    payload = result.model_dump(mode="json")
    await actions.record_simulation(proposal_id, payload)
    await audit.append(
        request.state.correlation_id,
        "simulation",
        "proposal",
        proposal.id,
        payload,
    )
    return result


@router.post(
    "/incidents/{incident_id}/resolve",
    response_model=IncidentRead,
    summary="Resolve incident",
    description="Mark an incident as resolved. Cannot be called on already-resolved incidents.",
)
async def resolve_incident(
    incident_id: UUID,
    request: Request,
    uow: UnitOfWorkDep,
) -> IncidentRead:
    repository = IncidentRepository(uow.session)
    audit = AuditRepository(uow.session)
    incident = await repository.get_incident(incident_id)

    if incident is None:
        raise NotFoundError("incident does not exist")
    if incident.state == IncidentState.RESOLVED.value:
        raise InvalidStateError("incident is already resolved")

    await repository.resolve(incident)
    await audit.append(
        request.state.correlation_id,
        "operator",
        "incident",
        incident.id,
        {"transition": "resolved"},
    )
    return incident_read(incident)
