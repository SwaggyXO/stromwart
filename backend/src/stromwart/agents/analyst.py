from collections.abc import Awaitable, Callable
from uuid import UUID

from stromwart.contracts.agents import AnalystFinding, ToolCall, ToolResult


Planner = Callable[[dict[str, object], list[ToolResult]], Awaitable[ToolCall | AnalystFinding]]


def validate_evidence(
    response_evidence: list[UUID],
    tool_results: list[ToolResult],
) -> bool:
    available = {
        evidence_id
        for result in tool_results
        for evidence_id in result.evidence_ids
    }
    return bool(response_evidence) and set(response_evidence).issubset(available)


class AnalystWorkflow:
    def __init__(
        self,
        planner: Planner,
        max_steps: int = 5,
    ) -> None:
        self.planner = planner
        self.max_steps = max_steps

    async def investigate(
        self,
        context: dict[str, object],
    ) -> tuple[AnalystFinding, list[ToolResult]]:
        results: list[ToolResult] = []

        for _ in range(self.max_steps):
            next_step = await self.planner(context, results)

            if isinstance(next_step, AnalystFinding):
                if not validate_evidence(next_step.evidence_ids, results):
                    raise ValueError("analyst response cites unavailable evidence")
                return next_step, results

            raise RuntimeError("tool calls are not supported in this workflow variant")

        raise RuntimeError("analyst workflow exceeded maximum evidence steps")
