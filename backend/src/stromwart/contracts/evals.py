from typing import Any

from pydantic import Field

from stromwart.contracts.common import ApiModel


class EvalScoreRead(ApiModel):
    dimension: str = Field(description="Eval dimension name")
    score: float = Field(description="Score in [0, 1]")
    explanation: str = Field(description="Short rationale for the score")


class EvalAgentMetric(ApiModel):
    name: str = Field(description="Agent name")
    total_runs: int = Field(ge=0, description="Number of evaluated runs")
    avg_latency_ms: float = Field(ge=0, description="Average latency in milliseconds")
    avg_score: float = Field(description="Average overall score")
    failure_rate: float = Field(ge=0, le=1, description="Fraction of failing runs")
    dimensions: dict[str, float] = Field(
        default_factory=dict,
        description="Per-dimension average scores",
    )


class EvalSummaryResponse(ApiModel):
    agents: list[EvalAgentMetric] = Field(description="Per-agent aggregated metrics")


class TraceSummary(ApiModel):
    trace_id: str
    overall_score: float
    cluster_id: str | None = None
    scores: list[EvalScoreRead] = Field(default_factory=list)


class TraceListResponse(ApiModel):
    traces: list[TraceSummary]


class SpanRead(ApiModel):
    span_id: str
    parent_id: str | None = None
    name: str
    agent_name: str
    duration_ms: float
    status: str
    attributes: dict[str, Any] = Field(default_factory=dict)


class TraceDetailResponse(ApiModel):
    trace_id: str
    total_duration_ms: float
    metadata: dict[str, Any] = Field(default_factory=dict)
    spans: list[SpanRead] = Field(default_factory=list)


class FailureClusterRead(ApiModel):
    cluster_id: str
    label: str
    count: int = Field(ge=0)
    representative_trace_id: str | None = None
    common_attributes: dict[str, Any] = Field(default_factory=dict)


class FailureClusterListResponse(ApiModel):
    clusters: list[FailureClusterRead]
