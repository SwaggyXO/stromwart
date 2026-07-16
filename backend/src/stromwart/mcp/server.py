from __future__ import annotations

from typing import Any
from uuid import uuid4


class StromwartMCPServer:
    """
    Exposes Stromwart capabilities as MCP-compliant tools.
    Any MCP client (Claude, GPT, other agents) can discover and invoke these.
    Follows JSON-RPC 2.0 over HTTP (Streamable HTTP transport).
    """

    TOOLS = [
        {
            "name": "stromwart/score_qoe",
            "description": (
                "Score a session's Quality of Experience using the trained GBM model. "
                "Returns MOS prediction with conformal prediction interval."
            ),
            "inputSchema": {
                "type": "object",
                "properties": {
                    "session_id": {"type": "string"},
                    "features": {
                        "type": "object",
                        "properties": {
                            "bitrate_kbps": {"type": "number"},
                            "stall_count": {"type": "integer"},
                            "packet_loss_pct": {"type": "number"},
                            "latency_ms": {"type": "number"},
                        },
                    },
                },
                "required": ["features"],
            },
        },
        {
            "name": "stromwart/forecast_qoe",
            "description": "Get quantile QoE forecast (p10, p50, p90) for the next 10 minutes.",
            "inputSchema": {
                "type": "object",
                "properties": {
                    "event_id": {"type": "string"},
                    "horizon_minutes": {"type": "integer", "default": 10},
                },
                "required": ["event_id"],
            },
        },
        {
            "name": "stromwart/check_policy",
            "description": (
                "Validate a proposed action against the policy engine. "
                "Returns policy decision (BLOCKED, INVESTIGATE, SIMULATE, APPROVAL_REQUIRED)."
            ),
            "inputSchema": {
                "type": "object",
                "properties": {
                    "action_type": {"type": "string"},
                    "confidence": {"type": "number"},
                    "risk_score": {"type": "number"},
                    "blast_radius_sessions": {"type": "integer"},
                },
                "required": ["action_type", "confidence", "risk_score"],
            },
        },
        {
            "name": "stromwart/get_incidents",
            "description": "List active incidents with their current state and severity.",
            "inputSchema": {
                "type": "object",
                "properties": {
                    "event_id": {"type": "string"},
                    "status_filter": {
                        "type": "string",
                        "enum": ["open", "investigating", "assessed", "resolved"],
                    },
                },
            },
        },
        {
            "name": "stromwart/get_audit_trail",
            "description": "Query audit log by correlation ID to trace a full decision chain.",
            "inputSchema": {
                "type": "object",
                "properties": {
                    "correlation_id": {"type": "string"},
                    "limit": {"type": "integer", "default": 50},
                },
                "required": ["correlation_id"],
            },
        },
    ]

    def __init__(self, container: Any) -> None:
        self._container = container

    def list_tools(self) -> list[dict[str, Any]]:
        return self.TOOLS

    async def call_tool(self, name: str, arguments: dict[str, Any]) -> dict[str, Any]:
        """Route MCP tool calls to internal services."""
        if name == "stromwart/score_qoe":
            return await self._score_qoe(arguments)
        if name == "stromwart/forecast_qoe":
            return await self._forecast_qoe(arguments)
        if name == "stromwart/check_policy":
            return await self._check_policy(arguments)
        if name == "stromwart/get_incidents":
            return await self._get_incidents(arguments)
        if name == "stromwart/get_audit_trail":
            return await self._get_audit_trail(arguments)
        return {"error": f"unknown tool: {name}"}

    async def _score_qoe(self, args: dict[str, Any]) -> dict[str, Any]:
        features = args.get("features", {})
        result = self._container.models.predict("qoe_gbm", features)
        return {"prediction": result}

    async def _forecast_qoe(self, args: dict[str, Any]) -> dict[str, Any]:
        event_id = args.get("event_id", "")
        horizon = args.get("horizon_minutes", 10)
        result = self._container.models.predict(
            "quantile_forecaster",
            {"event_id": event_id, "horizon_minutes": horizon},
        )
        return {"forecast": result}

    async def _check_policy(self, args: dict[str, Any]) -> dict[str, Any]:
        from stromwart.contracts.actions import ProposalCreate

        proposal = ProposalCreate(
            action_type=args["action_type"],
            confidence=args["confidence"],
            risk_score=args["risk_score"],
            target_scope={"session_count": args.get("blast_radius_sessions", 0)},
            rationale="mcp policy check",
            expected_effect="policy evaluation",
            evidence_ids=[uuid4()],
            drift_active=False,
            prediction_interval_width=None,
        )
        decision = self._container.policies.evaluate(proposal, evidence_is_valid=True)
        return {"state": decision.state.value, "reasons": decision.reasons}

    async def _get_incidents(self, args: dict[str, Any]) -> dict[str, Any]:
        del args
        return {"incidents": [], "note": "wire to IncidentRepository"}

    async def _get_audit_trail(self, args: dict[str, Any]) -> dict[str, Any]:
        del args
        return {"events": [], "note": "wire to AuditRepository"}
