"""API verification for pack_multi_agent HTTP checklist items."""

from __future__ import annotations

from datetime import UTC, datetime
from uuid import uuid4

from starlette.testclient import TestClient

from stromwart.app import create_app
from stromwart.contracts.agents import ToolCall, ToolName, ToolResult


def main() -> None:
    app = create_app()
    with TestClient(app) as client:
        settings_resp = client.get("/v1/settings")
        assert settings_resp.status_code == 200, settings_resp.text
        settings = settings_resp.json()
        assert settings["llm_provider"] == "disabled"

        providers_resp = client.get("/v1/settings/providers")
        assert providers_resp.status_code == 200
        assert len(providers_resp.json()) >= 1

        put_resp = client.put("/v1/settings", json={"max_retries": 3})
        assert put_resp.status_code == 200
        assert put_resp.json()["max_retries"] == 3

        eval_resp = client.get("/v1/evals/summary")
        assert eval_resp.status_code == 200
        assert "agents" in eval_resp.json()

        mcp_list = client.post("/v1/mcp/tools/list", json={})
        assert mcp_list.status_code == 200
        tools = mcp_list.json()["tools"]
        assert any(tool["name"] == "stromwart/score_qoe" for tool in tools)

        mcp_call = client.post(
            "/v1/mcp/tools/call",
            json={"name": "stromwart/score_qoe", "arguments": {"features": {"bitrate_kbps": 2000}}},
        )
        assert mcp_call.status_code == 200
        assert "result" in mcp_call.json()

        event_resp = client.post(
            "/v1/events",
            json={
                "name": "verify-event",
                "content_type": "live",
                "starts_at": "2026-07-14T00:00:00Z",
                "metadata": {},
            },
        )
        assert event_resp.status_code == 201, event_resp.text
        event_id = event_resp.json()["id"]

        session_id = uuid4()
        session_resp = client.post(
            "/v1/sessions",
            json={
                "event_id": event_id,
                "external_id": f"verify-{session_id}",
                "client_type": "web",
                "source_type": "live",
                "started_at": "2026-07-14T00:00:00Z",
            },
        )
        assert session_resp.status_code == 201, session_resp.text
        session_id = session_resp.json()["id"]

        features = {
            "session_id": session_id,
            "window_start": datetime.now(UTC).isoformat(),
            "window_end": datetime.now(UTC).isoformat(),
            "observation_count": 4,
            "throughput_mean_kbps": 1000,
            "throughput_std_kbps": 10,
            "buffer_mean_ms": 500,
            "buffer_min_ms": 300,
            "rebuffer_total_ms": 1000,
            "stall_ratio": 0.2,
            "downswitch_count": 1,
            "latest_bitrate_kbps": 500,
            "latest_packet_loss_pct": 8.0,
        }
        incident_resp = client.post(
            f"/v1/events/{event_id}/detect",
            json={
                "features": features,
                "affected_slice": {"event_id": event_id},
            },
        )
        assert incident_resp.status_code == 200, incident_resp.text
        incident = incident_resp.json()
        assert incident is not None, "expected incident from detect"
        incident_id = incident["id"]

        evidence = [
            ToolResult(
                call=ToolCall(name=ToolName.TELEMETRY, arguments={"event_id": event_id}),
                output={"avg_mos": 3.2},
            ).model_dump(mode="json")
        ]
        start_resp = client.post(
            f"/v1/incidents/{incident_id}/agent-runs",
            json=evidence,
        )
        assert start_resp.status_code == 201, start_resp.text
        run = start_resp.json()
        run_id = run["id"]
        assert run["state"] == "gathering_evidence"

        get_resp = client.get(f"/v1/agent-runs/{run_id}")
        assert get_resp.status_code == 200
        assert get_resp.json()["id"] == run_id

        analyze_resp = client.post(
            f"/v1/agent-runs/{run_id}/analyze",
            json={"event_id": event_id},
        )
        if analyze_resp.status_code == 200:
            state = analyze_resp.json()["state"]
            if state == "reflection_required":
                retry_resp = client.post(
                    f"/v1/agent-runs/{run_id}/retry",
                    json={"event_id": event_id},
                )
                assert retry_resp.status_code == 200

    print("api verification checks passed")


if __name__ == "__main__":
    main()
