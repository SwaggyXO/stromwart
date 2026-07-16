from __future__ import annotations

import time
from collections.abc import Awaitable, Callable
from dataclasses import dataclass
from typing import Any

from stromwart.agents.base import Observation

ToolHandler = Callable[[dict[str, Any]], Awaitable[dict[str, Any]]]


@dataclass(frozen=True)
class ToolSpec:
    name: str
    description: str
    handler: ToolHandler
    allowed_agents: list[str] | None = None  # None = all agents can use


class ToolGateway:
    """
    Controlled execution boundary between agent intent and tool execution.
    Enforces: allowlist, per-agent access, loop detection, timing.
    """

    def __init__(self, tools: list[ToolSpec]) -> None:
        self._tools: dict[str, ToolSpec] = {tool.name: tool for tool in tools}
        self._call_history: list[tuple[str, str]] = []  # (tool_name, args_hash)

    @property
    def available_tools(self) -> list[str]:
        return list(self._tools.keys())

    def tool_descriptions(self) -> list[dict[str, str]]:
        return [
            {"name": tool.name, "description": tool.description}
            for tool in self._tools.values()
        ]

    async def call(
        self,
        tool_name: str | None,
        args: dict[str, Any],
        caller_agent: str = "",
    ) -> Observation:
        if tool_name is None:
            return Observation(
                tool_name="none",
                output={},
                success=False,
                error="no tool specified",
            )

        spec = self._tools.get(tool_name)
        if spec is None:
            return Observation(
                tool_name=tool_name,
                output={},
                success=False,
                error=f"tool '{tool_name}' is not registered",
            )

        # Access control
        if spec.allowed_agents is not None and caller_agent not in spec.allowed_agents:
            return Observation(
                tool_name=tool_name,
                output={},
                success=False,
                error=f"agent '{caller_agent}' is not allowed to use tool '{tool_name}'",
            )

        # Loop detection
        args_hash = str(sorted(args.items()))
        call_sig = (tool_name, args_hash)
        if self._call_history.count(call_sig) >= 2:
            return Observation(
                tool_name=tool_name,
                output={},
                success=False,
                error="loop detected: same tool+args called 2+ times",
            )
        self._call_history.append(call_sig)

        # Execute
        try:
            start = time.monotonic()
            output = await spec.handler(args)
            elapsed = (time.monotonic() - start) * 1000
            return Observation(
                tool_name=tool_name,
                output={**output, "_elapsed_ms": elapsed},
                success=True,
            )
        except Exception as error:
            return Observation(
                tool_name=tool_name,
                output={},
                success=False,
                error=f"{type(error).__name__}: {error}",
            )

    def reset_history(self) -> None:
        self._call_history = []
