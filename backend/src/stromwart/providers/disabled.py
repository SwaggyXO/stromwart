from stromwart.contracts.agents import AnalystFinding, ToolResult
from stromwart.errors import ProviderUnavailableError


class DisabledAnalystProvider:
    async def analyze(
        self,
        incident_context: dict[str, object],
        evidence: list[ToolResult],
    ) -> AnalystFinding:
        raise ProviderUnavailableError(
            "LLM provider is disabled; submit an operator finding instead"
        )
