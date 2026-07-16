from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from stromwart.evals.tracer import AgentTrace


@dataclass
class ScoreResult:
    dimension: str
    score: float  # 0.0 - 1.0
    explanation: str
    details: dict[str, Any] | None = None


class DeterministicScorer:
    """
    Scores agent traces without LLM. Runs on every execution.
    Produces per-dimension scores that can be aggregated.
    """

    def score_all(self, trace: AgentTrace) -> list[ScoreResult]:
        return [
            self.score_latency(trace),
            self.score_policy_compliance(trace),
            self.score_evidence_grounding(trace),
            self.score_budget_efficiency(trace),
            self.score_tool_success_rate(trace),
        ]

    def score_latency(self, trace: AgentTrace, budget_ms: float = 30_000) -> ScoreResult:
        """Score based on total execution time vs budget."""
        duration = trace.total_duration_ms
        if duration <= 0:
            return ScoreResult("latency", 1.0, "No execution time recorded")

        # Linear decay: 1.0 at 0ms, 0.0 at budget
        score = max(0.0, 1.0 - (duration / budget_ms))
        return ScoreResult(
            "latency",
            score,
            f"Completed in {duration:.0f}ms (budget: {budget_ms:.0f}ms)",
            {"duration_ms": duration, "budget_ms": budget_ms},
        )

    def score_policy_compliance(self, trace: AgentTrace) -> ScoreResult:
        """Check if any guardrail was triggered."""
        guardrail_blocks = [
            span
            for span in trace.spans
            if span.status == "error" and "guardrail" in span.name.lower()
        ]
        if guardrail_blocks:
            return ScoreResult(
                "policy_compliance",
                0.0,
                f"{len(guardrail_blocks)} guardrail violations",
                {"violations": [span.attributes for span in guardrail_blocks]},
            )
        return ScoreResult("policy_compliance", 1.0, "No policy violations")

    def score_evidence_grounding(self, trace: AgentTrace) -> ScoreResult:
        """Check if diagnosis/outputs cite evidence from tool calls."""
        tool_spans = [
            span
            for span in trace.spans
            if "tool" in span.name.lower() and span.status == "ok"
        ]
        final_spans = [span for span in trace.spans if "final" in span.name.lower()]

        if not final_spans:
            return ScoreResult("evidence_grounding", 0.5, "No final output to evaluate")

        # Check if final output references tool observations
        has_evidence = any(
            span.attributes.get("evidence_ids") or span.attributes.get("contributing_factors")
            for span in final_spans
        )

        if tool_spans and has_evidence:
            return ScoreResult("evidence_grounding", 1.0, "Output grounded in tool evidence")
        if tool_spans and not has_evidence:
            return ScoreResult(
                "evidence_grounding",
                0.3,
                "Tools called but output lacks evidence citations",
            )
        return ScoreResult("evidence_grounding", 0.5, "No tools called")

    def score_budget_efficiency(self, trace: AgentTrace) -> ScoreResult:
        """Score based on steps used vs max budget."""
        total_steps = len(trace.spans)
        if total_steps == 0:
            return ScoreResult("budget_efficiency", 1.0, "No steps taken")

        # Penalize for using too many steps (ideal: resolve in <5 steps)
        ideal_steps = 5
        if total_steps <= ideal_steps:
            score = 1.0
        else:
            score = max(0.0, 1.0 - ((total_steps - ideal_steps) / 20))

        return ScoreResult(
            "budget_efficiency",
            score,
            f"Used {total_steps} steps (ideal: <={ideal_steps})",
            {"total_steps": total_steps},
        )

    def score_tool_success_rate(self, trace: AgentTrace) -> ScoreResult:
        """Ratio of successful tool calls to total tool calls."""
        tool_spans = [span for span in trace.spans if "tool" in span.name.lower()]
        if not tool_spans:
            return ScoreResult("tool_success_rate", 1.0, "No tool calls")

        success_count = sum(1 for span in tool_spans if span.status == "ok")
        rate = success_count / len(tool_spans)

        return ScoreResult(
            "tool_success_rate",
            rate,
            f"{success_count}/{len(tool_spans)} tool calls succeeded",
        )
