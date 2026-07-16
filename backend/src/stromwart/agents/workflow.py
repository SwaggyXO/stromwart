from uuid import UUID

from stromwart.agents.critic import EvidenceCritic
from stromwart.contracts.agents import (
    AgentRunState,
    HumanFeedback,
    ToolResult,
)
from stromwart.database import Database
from stromwart.errors import InvalidStateError, NotFoundError
from stromwart.persistence import AgentRunRow
from stromwart.providers.analyst import AnalystProvider
from stromwart.repositories.agents import AgentRunRepository
from stromwart.repositories.audit import AuditRepository
from stromwart.repositories.incidents import IncidentRepository


class AgentWorkflow:
    def __init__(
        self,
        database: Database,
        provider: AnalystProvider,
        critic: EvidenceCritic,
    ) -> None:
        self._database = database
        self._provider = provider
        self._critic = critic

    async def start(
        self,
        incident_id: UUID,
        correlation_id: str,
        evidence: list[ToolResult],
    ) -> AgentRunRow:
        async with self._database.transaction() as uow:
            incidents = IncidentRepository(uow.session)
            if await incidents.get_incident(incident_id) is None:
                raise NotFoundError("incident does not exist")

            runs = AgentRunRepository(uow.session)
            audit = AuditRepository(uow.session)

            run = await runs.create(
                incident_id,
                AgentRunState.GATHERING_EVIDENCE.value,
                {"tool_results": [item.model_dump(mode="json") for item in evidence]},
            )

            await audit.append(
                correlation_id,
                "agent",
                "agent_run",
                run.id,
                {"state": run.state, "incident_id": str(incident_id)},
            )
            return run

    async def analyze(
        self,
        run_id: UUID,
        incident_context: dict[str, object],
        correlation_id: str,
    ) -> AgentRunRow:
        async with self._database.transaction() as uow:
            runs = AgentRunRepository(uow.session)
            audit = AuditRepository(uow.session)
            run = await runs.get(run_id)

            if run is None:
                raise NotFoundError("agent run does not exist")
            if run.state != AgentRunState.GATHERING_EVIDENCE.value:
                raise InvalidStateError("agent run cannot be analyzed in current state")

            evidence = [
                ToolResult.model_validate(item)
                for item in run.workflow_data["tool_results"]
            ]
            finding = await self._provider.analyze(incident_context, evidence)
            reflection = self._critic.review(finding, evidence)

            workflow_data = dict(run.workflow_data)
            workflow_data["finding"] = finding.model_dump(mode="json")
            workflow_data["reflection"] = reflection.model_dump(mode="json")

            state = (
                AgentRunState.WAITING_FOR_HUMAN.value
                if reflection.accepted
                else AgentRunState.REFLECTION_REQUIRED.value
            )
            await runs.update(run, state, workflow_data)

            incidents = IncidentRepository(uow.session)
            incident = await incidents.get_incident(UUID(run.incident_id))
            if incident is not None and reflection.accepted:
                incident.hypothesis = {
                    "hypothesis": finding.hypothesis,
                    "confidence": finding.confidence,
                    "source": "llm_analyst",
                    "evidence_ids": [str(item) for item in finding.evidence_ids],
                    "recommended_action": finding.recommended_action,
                    "llm_enriched": True,
                }
                await uow.flush()

            await audit.append(
                correlation_id,
                "llm_analyst",
                "agent_run",
                run.id,
                {
                    "state": state,
                    "hypothesis": finding.hypothesis,
                    "reflection": workflow_data["reflection"],
                },
            )
            return run

    async def retry(
        self,
        run_id: UUID,
        incident_context: dict[str, object],
        correlation_id: str,
    ) -> AgentRunRow:
        async with self._database.transaction() as uow:
            runs = AgentRunRepository(uow.session)
            run = await runs.get(run_id)

            if run is None:
                raise NotFoundError("agent run does not exist")
            if run.state != AgentRunState.REFLECTION_REQUIRED.value:
                raise InvalidStateError("agent run is not awaiting reflection retry")

            workflow_data = dict(run.workflow_data)
            workflow_data["retry_context"] = incident_context
            await runs.update(run, AgentRunState.GATHERING_EVIDENCE.value, workflow_data)

        return await self.analyze(run_id, incident_context, correlation_id)

    async def resolve(
        self,
        run_id: UUID,
        feedback: HumanFeedback,
        correlation_id: str,
    ) -> AgentRunRow:
        async with self._database.transaction() as uow:
            runs = AgentRunRepository(uow.session)
            audit = AuditRepository(uow.session)
            run = await runs.get(run_id)

            if run is None:
                raise NotFoundError("agent run does not exist")
            if run.state != AgentRunState.WAITING_FOR_HUMAN.value:
                raise InvalidStateError("agent run is not awaiting human feedback")

            data = dict(run.workflow_data)
            data["human_feedback"] = feedback.model_dump(mode="json")
            state = (
                AgentRunState.COMPLETED.value
                if feedback.approved
                else AgentRunState.REJECTED.value
            )
            await runs.update(run, state, data)

            await audit.append(
                correlation_id,
                "human",
                "agent_run_feedback",
                run.id,
                data["human_feedback"],
            )
            return run
