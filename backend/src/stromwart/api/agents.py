from uuid import UUID

from fastapi import APIRouter, Request, status

from stromwart.api.serializers import agent_read
from stromwart.application.dependencies import ContainerDep
from stromwart.contracts.agents import AgentRunRead, HumanFeedback, ToolResult
from stromwart.errors import NotFoundError
from stromwart.repositories.agents import AgentRunRepository
from stromwart.repositories.incidents import IncidentRepository

router = APIRouter(tags=["agents"])


@router.post(
    "/incidents/{incident_id}/agent-runs",
    response_model=AgentRunRead,
    status_code=status.HTTP_201_CREATED,
    summary="Start agent run",
    description="Initialize an LLM analyst run for an incident with gathered evidence.",
)
async def start_agent_run(
    incident_id: UUID,
    evidence: list[ToolResult],
    request: Request,
    container: ContainerDep,
) -> AgentRunRead:
    return agent_read(
        await container.agent.start(
            incident_id,
            request.state.correlation_id,
            evidence,
        )
    )


@router.get(
    "/incidents/{incident_id}/agent-runs",
    response_model=list[AgentRunRead],
    summary="List agent runs for incident",
    description="Return agent run history for an incident, newest first.",
)
async def list_agent_runs(
    incident_id: UUID,
    container: ContainerDep,
    limit: int = 50,
) -> list[AgentRunRead]:
    async with container.database.transaction() as uow:
        if await IncidentRepository(uow.session).get_incident(incident_id) is None:
            raise NotFoundError("incident does not exist")
        rows = await AgentRunRepository(uow.session).list_for_incident(
            incident_id,
            limit=limit,
        )
    return [agent_read(row) for row in rows]


@router.post(
    "/agent-runs/{run_id}/analyze",
    response_model=AgentRunRead,
    summary="Run LLM analysis",
    description=(
        "Trigger the LLM analyst to produce a finding (hypothesis + evidence + "
        "recommendation). The evidence critic validates grounding."
    ),
)
async def analyze_agent_run(
    run_id: UUID,
    incident_context: dict[str, object],
    request: Request,
    container: ContainerDep,
) -> AgentRunRead:
    return agent_read(
        await container.agent.analyze(
            run_id,
            incident_context,
            request.state.correlation_id,
        )
    )


@router.post(
    "/agent-runs/{run_id}/feedback",
    response_model=AgentRunRead,
    summary="Submit human feedback",
    description="Approve or reject an analyst finding. Transitions run to COMPLETED or REJECTED.",
)
async def resolve_agent_run(
    run_id: UUID,
    feedback: HumanFeedback,
    request: Request,
    container: ContainerDep,
) -> AgentRunRead:
    return agent_read(
        await container.agent.resolve(
            run_id,
            feedback,
            request.state.correlation_id,
        )
    )


@router.get(
    "/agent-runs/{run_id}",
    response_model=AgentRunRead,
    summary="Get agent run status",
    description="Retrieve the current state and workflow data for an agent run.",
)
async def get_agent_run(
    run_id: UUID,
    container: ContainerDep,
) -> AgentRunRead:
    async with container.database.transaction() as uow:
        repo = AgentRunRepository(uow.session)
        run = await repo.get(run_id)
        if run is None:
            raise NotFoundError("agent run does not exist")
        return agent_read(run)


@router.post(
    "/agent-runs/{run_id}/retry",
    response_model=AgentRunRead,
    summary="Retry after reflection",
    description="Re-analyze with reflexion feedback when state is reflection_required.",
)
async def retry_agent_run(
    run_id: UUID,
    incident_context: dict[str, object],
    request: Request,
    container: ContainerDep,
) -> AgentRunRead:
    return agent_read(
        await container.agent.retry(
            run_id,
            incident_context,
            request.state.correlation_id,
        )
    )
