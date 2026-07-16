from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from stromwart.evals.scorers import ScoreResult
from stromwart.evals.tracer import AgentTrace


@dataclass
class FailureCluster:
    cluster_id: str
    label: str
    traces: list[str] = field(default_factory=list)  # trace_ids
    common_attributes: dict[str, Any] = field(default_factory=dict)
    count: int = 0
    representative_trace_id: str | None = None


class FailureClustering:
    """
    Clusters failing traces by common attributes.
    Lightweight implementation (no HDBSCAN dep for MVP — uses rule-based grouping).
    Production: swap in sklearn.cluster.HDBSCAN with embedding-based similarity.
    """

    def __init__(self) -> None:
        self._clusters: dict[str, FailureCluster] = {}

    def ingest(self, trace: AgentTrace, scores: list[ScoreResult]) -> str | None:
        """If trace has failures, assign to a cluster. Returns cluster_id or None."""
        failing_dims = [score for score in scores if score.score < 0.5]
        if not failing_dims:
            return None

        # Rule-based clustering key: combination of failing dimensions + agent
        failing_agents: set[str] = set()
        for span in trace.spans:
            if span.status == "error":
                failing_agents.add(span.agent_name)

        cluster_key = "|".join(
            sorted([score.dimension for score in failing_dims] + list(failing_agents))
        )

        if cluster_key not in self._clusters:
            self._clusters[cluster_key] = FailureCluster(
                cluster_id=cluster_key,
                label=f"Failures in: {', '.join(score.dimension for score in failing_dims)}",
                common_attributes={
                    "failing_dimensions": [score.dimension for score in failing_dims],
                    "failing_agents": list(failing_agents),
                },
            )

        cluster = self._clusters[cluster_key]
        cluster.traces.append(trace.trace_id)
        cluster.count += 1
        if cluster.representative_trace_id is None:
            cluster.representative_trace_id = trace.trace_id

        return cluster_key

    def get_clusters(self) -> list[FailureCluster]:
        return sorted(self._clusters.values(), key=lambda cluster: cluster.count, reverse=True)

    def get_cluster(self, cluster_id: str) -> FailureCluster | None:
        return self._clusters.get(cluster_id)

    def clear(self) -> None:
        self._clusters = {}
