from stromwart.contracts.agents import AnalystFinding, ReflectionResult, ToolResult


class EvidenceCritic:
    def review(
        self,
        finding: AnalystFinding,
        results: list[ToolResult],
    ) -> ReflectionResult:
        available_ids = {evidence_id for result in results for evidence_id in result.evidence_ids}
        reasons: list[str] = []

        if not set(finding.evidence_ids).issubset(available_ids):
            reasons.append("finding cites evidence unavailable from tools")

        if finding.confidence >= 0.8 and finding.missing_evidence:
            reasons.append("high-confidence finding conflicts with declared missing evidence")

        if finding.recommended_action == "increase_cdn_capacity":
            telemetry_seen = any(
                result.call.name.value == "telemetry" and "throughput_mean_kbps" in result.output
                for result in results
            )
            if not telemetry_seen:
                reasons.append("capacity recommendation lacks telemetry evidence")

        return ReflectionResult(accepted=not reasons, reasons=reasons)
