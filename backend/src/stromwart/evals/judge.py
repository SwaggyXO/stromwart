from __future__ import annotations

from stromwart.evals.scorers import ScoreResult
from stromwart.evals.tracer import AgentTrace
from stromwart.providers.analyst import AnalystProvider


class LLMJudge:
    """
    Optional LLM-as-judge for scoring natural language quality.
    Only runs if an LLM provider is configured and enabled.
    Scores hypothesis quality and rationale coherence.
    """

    def __init__(self, provider: AnalystProvider | None = None) -> None:
        self._provider = provider

    @property
    def available(self) -> bool:
        return self._provider is not None

    async def score_hypothesis_quality(self, trace: AgentTrace) -> ScoreResult | None:
        if not self.available:
            return None

        # Extract hypothesis from diagnostician output
        diag_spans = [
            span
            for span in trace.spans
            if span.agent_name == "diagnostician" and "final" in span.name.lower()
        ]
        if not diag_spans:
            return None

        hypothesis = diag_spans[-1].attributes.get("hypothesis", "")
        if not hypothesis:
            return None

        try:
            from stromwart.contracts.agents import ToolCall, ToolName, ToolResult

            evidence = [
                ToolResult(
                    call=ToolCall(name=ToolName.INCIDENT, arguments={}),
                    output={"hypothesis_to_judge": hypothesis, "trace_metadata": trace.metadata},
                )
            ]
            assert self._provider is not None
            finding = await self._provider.analyze(
                {
                    "task": "judge_hypothesis_quality",
                    "rubric": (
                        "Score 0-1: Is the hypothesis specific, actionable, and grounded "
                        "in evidence? 1.0=excellent, 0.5=adequate, 0.0=vague/unsupported"
                    ),
                    "hypothesis": hypothesis,
                },
                evidence,
            )
            score = finding.confidence  # Repurpose confidence as the judge score
            return ScoreResult(
                "hypothesis_quality",
                score,
                finding.rationale[:200],
            )
        except Exception:
            return None

    async def score_all(self, trace: AgentTrace) -> list[ScoreResult]:
        results: list[ScoreResult] = []
        hyp = await self.score_hypothesis_quality(trace)
        if hyp:
            results.append(hyp)
        return results
