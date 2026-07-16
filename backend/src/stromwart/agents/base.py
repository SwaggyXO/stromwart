from __future__ import annotations

import time
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from enum import StrEnum
from typing import TYPE_CHECKING, Any

from stromwart.orchestrator.state import CognitiveState

if TYPE_CHECKING:
    from stromwart.agents.guardrails import AgentGuardrails
    from stromwart.agents.tools import ToolGateway


class ActionKind(StrEnum):
    TOOL = "tool"
    FINAL = "final"


@dataclass(frozen=True)
class AgentAction:
    kind: ActionKind
    tool_name: str | None = None
    tool_args: dict[str, Any] = field(default_factory=dict)
    final_output: dict[str, Any] = field(default_factory=dict)
    reasoning: str = ""


@dataclass
class Observation:
    tool_name: str
    output: dict[str, Any]
    success: bool = True
    error: str | None = None


@dataclass
class Step:
    action: AgentAction
    observation: Observation | None = None


@dataclass
class AgentResult:
    success: bool
    output: dict[str, Any]
    steps: list[Step]
    duration_ms: float
    stop_reason: str  # "success" | "budget_exhausted" | "guardrail_blocked" | "error"


class BudgetExhausted(Exception):
    pass


class GuardrailBlocked(Exception):
    def __init__(self, reason: str):
        self.reason = reason
        super().__init__(reason)


@dataclass
class Budget:
    max_steps: int = 10
    max_seconds: float = 30.0
    max_tool_calls: int = 8
    _steps_used: int = 0
    _tools_used: int = 0
    _start_time: float = 0.0

    def start(self) -> None:
        self._start_time = time.monotonic()
        self._steps_used = 0
        self._tools_used = 0

    def check_step(self) -> None:
        self._steps_used += 1
        if self._steps_used > self.max_steps:
            raise BudgetExhausted(f"exceeded {self.max_steps} steps")
        elapsed = time.monotonic() - self._start_time
        if elapsed > self.max_seconds:
            raise BudgetExhausted(f"exceeded {self.max_seconds}s time budget")

    def check_tool(self) -> None:
        self._tools_used += 1
        if self._tools_used > self.max_tool_calls:
            raise BudgetExhausted(f"exceeded {self.max_tool_calls} tool calls")


class BaseAgent(ABC):
    """
    Base for all specialist agents. Implements ReAct loop with Reflexion support.
    Subclasses implement _decide() with their domain logic (ML or deterministic).
    """

    name: str = "base"

    def __init__(
        self,
        tools: ToolGateway,
        guardrails: AgentGuardrails,
        budget: Budget | None = None,
    ) -> None:
        self.tools = tools
        self.guardrails = guardrails
        self.budget = budget or Budget()

    async def run(
        self,
        state: CognitiveState,
        reflection: str | None = None,
    ) -> AgentResult:
        """Execute ReAct loop with optional Reflexion context from a prior failure."""
        self.budget.start()
        steps: list[Step] = []
        start = time.monotonic()

        try:
            for _ in range(self.budget.max_steps):
                self.budget.check_step()

                # Pre-execution guardrail
                self.guardrails.pre_check(self.name, state, steps)

                # Think: decide next action
                action = await self._decide(state, steps, reflection)

                if action.kind == ActionKind.FINAL:
                    result = AgentResult(
                        success=True,
                        output=action.final_output,
                        steps=steps,
                        duration_ms=(time.monotonic() - start) * 1000,
                        stop_reason="success",
                    )
                    # Post-execution guardrail
                    self.guardrails.post_check(self.name, result)
                    return result

                # Act: execute via tool gateway
                self.budget.check_tool()
                observation = await self.tools.call(
                    action.tool_name,
                    action.tool_args,
                    caller_agent=self.name,
                )
                steps.append(Step(action=action, observation=observation))

        except BudgetExhausted as error:
            return AgentResult(
                success=False,
                output={"error": str(error)},
                steps=steps,
                duration_ms=(time.monotonic() - start) * 1000,
                stop_reason="budget_exhausted",
            )
        except GuardrailBlocked as error:
            return AgentResult(
                success=False,
                output={"error": error.reason},
                steps=steps,
                duration_ms=(time.monotonic() - start) * 1000,
                stop_reason="guardrail_blocked",
            )

        return AgentResult(
            success=False,
            output={"error": "max steps reached without final action"},
            steps=steps,
            duration_ms=(time.monotonic() - start) * 1000,
            stop_reason="budget_exhausted",
        )

    @abstractmethod
    async def _decide(
        self,
        state: CognitiveState,
        history: list[Step],
        reflection: str | None,
    ) -> AgentAction:
        """Subclass implements decision logic. Can be ML-based, rule-based, or LLM-based."""
        ...


# Re-export for pack_validator import smoke test (ToolGateway lives in agents.tools).
from stromwart.agents.tools import ToolGateway as ToolGateway  # noqa: E402
