from __future__ import annotations

import time
from dataclasses import dataclass, field
from typing import Any
from uuid import uuid4


@dataclass
class Span:
    span_id: str
    parent_id: str | None
    name: str
    agent_name: str
    start_time: float
    end_time: float = 0.0
    attributes: dict[str, Any] = field(default_factory=dict)
    events: list[dict[str, Any]] = field(default_factory=list)
    status: str = "ok"  # "ok" | "error"

    @property
    def duration_ms(self) -> float:
        return (self.end_time - self.start_time) * 1000


@dataclass
class AgentTrace:
    trace_id: str
    spans: list[Span] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)

    @property
    def total_duration_ms(self) -> float:
        if not self.spans:
            return 0.0
        start = min(span.start_time for span in self.spans)
        end = max(span.end_time for span in self.spans if span.end_time > 0)
        return (end - start) * 1000

    @property
    def agent_spans(self) -> dict[str, list[Span]]:
        result: dict[str, list[Span]] = {}
        for span in self.spans:
            result.setdefault(span.agent_name, []).append(span)
        return result


class AgentTracer:
    """
    Lightweight tracing for agent execution.
    Produces OpenTelemetry-compatible spans that can be exported to any OTel collector.
    For MVP: stores in-memory and exposes via API. Production: export to Jaeger/Grafana Tempo.
    """

    def __init__(self, sample_rate: float = 1.0) -> None:
        self._sample_rate = sample_rate
        self._traces: list[AgentTrace] = []
        self._active_trace: AgentTrace | None = None
        self._span_stack: list[Span] = []

    def start_trace(self, metadata: dict[str, Any] | None = None) -> str:
        trace_id = str(uuid4())
        trace = AgentTrace(trace_id=trace_id, metadata=metadata or {})
        self._active_trace = trace
        self._traces.append(trace)
        return trace_id

    def start_span(
        self,
        name: str,
        agent_name: str,
        attributes: dict[str, Any] | None = None,
    ) -> str:
        span_id = str(uuid4())
        parent_id = self._span_stack[-1].span_id if self._span_stack else None
        span = Span(
            span_id=span_id,
            parent_id=parent_id,
            name=name,
            agent_name=agent_name,
            start_time=time.monotonic(),
            attributes=attributes or {},
        )
        self._span_stack.append(span)
        if self._active_trace:
            self._active_trace.spans.append(span)
        return span_id

    def end_span(
        self,
        status: str = "ok",
        attributes: dict[str, Any] | None = None,
        *,
        duration_ms: float | None = None,
    ) -> None:
        if self._span_stack:
            span = self._span_stack.pop()
            if duration_ms is not None and duration_ms > 0:
                span.end_time = span.start_time + duration_ms / 1000
            else:
                span.end_time = time.monotonic()
            span.status = status
            if attributes:
                span.attributes.update(attributes)

    def add_event(self, name: str, attributes: dict[str, Any] | None = None) -> None:
        if self._span_stack:
            self._span_stack[-1].events.append({
                "name": name,
                "timestamp": time.monotonic(),
                "attributes": attributes or {},
            })

    def end_trace(self) -> AgentTrace | None:
        trace = self._active_trace
        self._active_trace = None
        self._span_stack = []
        return trace

    def get_traces(self, limit: int = 100) -> list[AgentTrace]:
        return self._traces[-limit:]

    def get_trace(self, trace_id: str) -> AgentTrace | None:
        for trace in self._traces:
            if trace.trace_id == trace_id:
                return trace
        return None

    def clear(self) -> None:
        """Drop in-memory traces (e.g. when a new simulation starts)."""
        self._traces = []
        self._active_trace = None
        self._span_stack = []
