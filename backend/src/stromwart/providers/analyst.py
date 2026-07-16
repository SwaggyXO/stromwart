from typing import Protocol

from stromwart.contracts.agents import AnalystFinding, ToolResult


class AnalystProvider(Protocol):
    async def analyze(
        self,
        incident_context: dict[str, object],
        evidence: list[ToolResult],
    ) -> AnalystFinding: ...
