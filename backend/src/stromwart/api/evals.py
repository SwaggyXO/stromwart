from fastapi import APIRouter

from stromwart.application.dependencies import ContainerDep
from stromwart.contracts.evals import (
    EvalAgentMetric,
    EvalScoreRead,
    EvalSummaryResponse,
    FailureClusterListResponse,
    FailureClusterRead,
    SpanRead,
    TraceDetailResponse,
    TraceListResponse,
    TraceSummary,
)
from stromwart.errors import NotFoundError

router = APIRouter(prefix="/evals", tags=["evals"])


@router.get(
    "/summary",
    response_model=EvalSummaryResponse,
    summary="Eval metrics summary",
    description="Per-agent aggregated eval metrics across scored traces.",
)
async def eval_summary(container: ContainerDep) -> EvalSummaryResponse:
    metrics = container.eval_runner.get_agent_metrics()
    return EvalSummaryResponse(
        agents=[
            EvalAgentMetric(
                name=metric.agent_name,
                total_runs=metric.total_runs,
                avg_latency_ms=round(metric.avg_latency_ms, 1),
                avg_score=round(metric.avg_score, 3),
                failure_rate=round(metric.failure_rate, 3),
                dimensions={
                    key: round(value, 3) for key, value in metric.dimension_averages.items()
                },
            )
            for metric in metrics
        ],
    )


@router.get(
    "/traces",
    response_model=TraceListResponse,
    summary="List eval traces",
    description="Recent evaluated traces with overall scores and cluster assignment.",
)
async def list_traces(container: ContainerDep, limit: int = 50) -> TraceListResponse:
    summaries = container.eval_runner.get_summaries(limit)
    return TraceListResponse(
        traces=[
            TraceSummary(
                trace_id=summary.trace_id,
                overall_score=round(summary.overall_score, 3),
                cluster_id=summary.cluster_id,
                scores=[
                    EvalScoreRead(
                        dimension=score.dimension,
                        score=round(score.score, 3),
                        explanation=score.explanation,
                    )
                    for score in summary.scores
                ],
            )
            for summary in summaries
        ],
    )


@router.get(
    "/traces/{trace_id}",
    response_model=TraceDetailResponse,
    summary="Get eval trace detail",
    description="Full trace with spans for debugging agent execution.",
)
async def get_trace(trace_id: str, container: ContainerDep) -> TraceDetailResponse:
    trace = container.tracer.get_trace(trace_id)
    if trace is None:
        raise NotFoundError("trace not found")
    return TraceDetailResponse(
        trace_id=trace.trace_id,
        total_duration_ms=round(trace.total_duration_ms, 1),
        metadata=trace.metadata,
        spans=[
            SpanRead(
                span_id=span.span_id,
                parent_id=span.parent_id,
                name=span.name,
                agent_name=span.agent_name,
                duration_ms=round(span.duration_ms, 1),
                status=span.status,
                attributes=span.attributes,
            )
            for span in trace.spans
        ],
    )


@router.get(
    "/clusters",
    response_model=FailureClusterListResponse,
    summary="List failure clusters",
    description="Grouped failing traces for debugging common failure modes.",
)
async def failure_clusters(container: ContainerDep) -> FailureClusterListResponse:
    clusters = container.eval_runner.get_failure_clusters()
    return FailureClusterListResponse(
        clusters=[
            FailureClusterRead(
                cluster_id=cluster.cluster_id,
                label=cluster.label,
                count=cluster.count,
                representative_trace_id=cluster.representative_trace_id,
                common_attributes=cluster.common_attributes,
            )
            for cluster in clusters
        ],
    )
