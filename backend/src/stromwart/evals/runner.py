from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from stromwart.evals.clustering import FailureCluster, FailureClustering
from stromwart.evals.judge import LLMJudge
from stromwart.evals.scorers import DeterministicScorer, ScoreResult
from stromwart.evals.tracer import AgentTrace, AgentTracer


@dataclass
class EvalSummary:
    trace_id: str
    scores: list[ScoreResult]
    overall_score: float
    cluster_id: str | None = None


@dataclass
class AgentEvalMetrics:
    agent_name: str
    total_runs: int = 0
    avg_latency_ms: float = 0.0
    avg_score: float = 0.0
    failure_rate: float = 0.0
    dimension_averages: dict[str, float] = field(default_factory=dict)


class EvalRunner:
    """Orchestrates the full eval pipeline: score → judge → cluster."""

    def __init__(
        self,
        tracer: AgentTracer,
        judge: LLMJudge | None = None,
    ) -> None:
        self._tracer = tracer
        self._scorer = DeterministicScorer()
        self._judge = judge or LLMJudge()
        self._clustering = FailureClustering()
        self._summaries: list[EvalSummary] = []

    async def evaluate_trace(self, trace: AgentTrace) -> EvalSummary:
        """Run full evaluation on a single trace."""
        # Layer 1: Deterministic scorers
        scores = self._scorer.score_all(trace)

        # Layer 2: LLM judge (optional)
        if self._judge.available:
            judge_scores = await self._judge.score_all(trace)
            scores.extend(judge_scores)

        # Overall score (weighted average)
        if scores:
            overall = sum(score.score for score in scores) / len(scores)
        else:
            overall = 0.0

        # Layer 3: Failure clustering
        cluster_id = self._clustering.ingest(trace, scores)

        summary = EvalSummary(
            trace_id=trace.trace_id,
            scores=scores,
            overall_score=overall,
            cluster_id=cluster_id,
        )
        self._summaries.append(summary)
        return summary

    def get_agent_metrics(self) -> list[AgentEvalMetrics]:
        """Aggregate metrics per agent across all evaluated traces."""
        agent_data: dict[str, list[dict[str, Any]]] = {}

        for summary in self._summaries:
            trace = self._tracer.get_trace(summary.trace_id)
            if not trace:
                continue

            for agent_name, spans in trace.agent_spans.items():
                agent_data.setdefault(agent_name, [])
                agent_data[agent_name].append(
                    {
                        "latency_ms": sum(span.duration_ms for span in spans),
                        "success": all(span.status == "ok" for span in spans),
                        "scores": {score.dimension: score.score for score in summary.scores},
                    }
                )

        metrics: list[AgentEvalMetrics] = []
        for agent_name, runs in agent_data.items():
            total = len(runs)
            avg_lat = sum(run["latency_ms"] for run in runs) / total if total else 0
            failures = sum(1 for run in runs if not run["success"])

            # Aggregate dimension scores
            dim_totals: dict[str, list[float]] = {}
            for run in runs:
                for dim, score in run["scores"].items():
                    dim_totals.setdefault(dim, []).append(score)

            metrics.append(
                AgentEvalMetrics(
                    agent_name=agent_name,
                    total_runs=total,
                    avg_latency_ms=avg_lat,
                    avg_score=(
                        sum(sum(values) / len(values) for values in dim_totals.values())
                        / len(dim_totals)
                        if dim_totals
                        else 0
                    ),
                    failure_rate=failures / total if total else 0,
                    dimension_averages={
                        key: sum(values) / len(values) for key, values in dim_totals.items()
                    },
                )
            )

        return metrics

    def get_failure_clusters(self) -> list[FailureCluster]:
        return self._clustering.get_clusters()

    def get_summaries(self, limit: int = 50) -> list[EvalSummary]:
        return self._summaries[-limit:]

    def clear(self) -> None:
        """Reset scored summaries and failure clusters for a fresh demo run."""
        self._summaries = []
        self._clustering.clear()
        self._tracer.clear()
