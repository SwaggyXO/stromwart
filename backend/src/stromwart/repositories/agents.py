from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from stromwart.persistence import AgentRunRow


class AgentRunRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get(self, run_id: UUID) -> AgentRunRow | None:
        return await self._session.get(AgentRunRow, str(run_id))

    async def list_for_incident(
        self,
        incident_id: UUID,
        limit: int = 50,
    ) -> list[AgentRunRow]:
        statement = (
            select(AgentRunRow)
            .where(AgentRunRow.incident_id == str(incident_id))
            .order_by(AgentRunRow.created_at.desc())
            .limit(limit)
        )
        return list((await self._session.scalars(statement)).all())

    async def create(
        self,
        incident_id: UUID,
        state: str,
        workflow_data: dict[str, object],
    ) -> AgentRunRow:
        row = AgentRunRow(
            incident_id=str(incident_id),
            state=state,
            workflow_data=workflow_data,
        )
        self._session.add(row)
        await self._session.flush()
        return row

    async def update(
        self,
        row: AgentRunRow,
        state: str,
        workflow_data: dict[str, object],
    ) -> AgentRunRow:
        row.state = state
        row.workflow_data = workflow_data
        await self._session.flush()
        return row
