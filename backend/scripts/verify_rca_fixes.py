"""Verify RCA fix plan: unified session counts, incident audit, agent runs."""
from __future__ import annotations

import json
import os
import sys
import time
import urllib.request

BASE = os.environ.get("STROMWART_BASE", "http://localhost:8000/v1")


def get(path: str) -> object:
    with urllib.request.urlopen(BASE + path, timeout=60) as response:
        return json.load(response)


def post(path: str, body: dict | None = None) -> object:
    data = json.dumps(body or {}).encode()
    req = urllib.request.Request(
        BASE + path,
        data=data,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=60) as response:
        return json.load(response)


def main() -> int:
    status = get("/simulation/status")
    if isinstance(status, dict) and status.get("status") == "running":
        post("/simulation/stop")
        time.sleep(1)

    start = post(
        "/simulation/start",
        {"scenario_id": "cdn_regional_outage", "speed_multiplier": 50},
    )
    assert isinstance(start, dict)
    event_id = start["event_id"]
    print("Started:", start.get("sessions_provisioned"), "provisioned")

    # Wait for sessions
    for _ in range(10):
        stats = get(f"/events/{event_id}/session-stats")
        if isinstance(stats, dict) and stats.get("total_sessions", 0) >= 100:
            break
        time.sleep(2)

    stats = get(f"/events/{event_id}/session-stats")
    kpis = get(f"/events/{event_id}/kpis")
    assert isinstance(stats, dict) and isinstance(kpis, list)

    active_kpi = next(k["value"] for k in kpis if k["label"] == "Active Sessions")
    total_kpi = next(k["value"] for k in kpis if k["label"] == "Total Sessions")
    print(f"Session stats: active={stats['active_sessions']} total={stats['total_sessions']}")
    print(f"KPIs: active={active_kpi} total={total_kpi}")

    assert stats["active_sessions"] == active_kpi == total_kpi, (
        f"Counts mismatch: stats={stats}, kpis active={active_kpi} total={total_kpi}"
    )
    assert stats["total_sessions"] == 350, f"Expected 350 sessions, got {stats}"
    sim_status = get("/simulation/status")
    if isinstance(sim_status, dict) and sim_status.get("sessions_provisioned"):
        assert stats["total_sessions"] == sim_status["sessions_provisioned"]
    print("CHECK: unified session counts PASS (~350)")

    # Wait for simulation completion
    incidents: list = []
    sim_status: dict = {}
    for attempt in range(40):
        time.sleep(5)
        sim_status = get("/simulation/status")
        incidents = get(f"/events/{event_id}/incidents?active_only=true")
        if not isinstance(sim_status, dict):
            continue
        if sim_status.get("status") == "completed":
            print(f"  attempt {attempt + 1}: simulation completed")
            break
        print(
            f"  attempt {attempt + 1}: status={sim_status.get('status')}, "
            f"incidents={len(incidents) if isinstance(incidents, list) else 0}"
        )
    else:
        raise AssertionError("Simulation did not complete within timeout")

    assert isinstance(incidents, list) and len(incidents) == 1, f"Expected 1 incident, got {incidents}"
    print("CHECK: single open incident PASS")

    incident_id = incidents[0]["id"]
    audit = get(f"/audit?event_id={event_id}&limit=100")
    assert isinstance(audit, list)
    incident_audits = [a for a in audit if a.get("artifact_type") == "incident"]
    created = [
        a
        for a in incident_audits
        if "detected from degraded" in str(a.get("payload", {}).get("description", ""))
    ]
    updated = [
        a
        for a in incident_audits
        if "merged" in str(a.get("payload", {}).get("description", "")).lower()
    ]
    print(f"Audit incident entries: created={len(created)} updated={len(updated)}")
    assert len(created) >= 1, "Missing incident created audit"
    assert len(created) == 1, f"Expected 1 created audit, got {len(created)}"

    agent_runs = get(f"/incidents/{incident_id}/agent-runs?limit=20")
    assert isinstance(agent_runs, list) and len(agent_runs) > 0, "No agent runs"
    print(f"CHECK: {len(agent_runs)} agent runs PASS")

    supervisor_steps = [
        a for a in audit if a.get("artifact_type") == "supervisor_step"
    ]
    assert len(supervisor_steps) > 0, "No supervisor_step audit entries"
    print(f"CHECK: {len(supervisor_steps)} supervisor steps PASS")

    eval_summary = get("/evals/summary")
    assert isinstance(eval_summary, dict)
    agents = eval_summary.get("agents", [])
    total_runs = sum(a.get("total_runs", 0) for a in agents if isinstance(a, dict))
    print(f"Eval agent total_runs: {total_runs}")
    assert total_runs > 0, "Eval traces empty"
    if total_runs > 0:
        assert any(
            isinstance(a, dict) and a.get("avg_latency_ms", 0) > 0
            for a in agents
            if a.get("total_runs", 0) > 0
        ), "Eval agent latency metrics are all zero"
        print("CHECK: eval agent latency PASS")

    incident_detail = get(f"/incidents/{incident_id}")
    assert isinstance(incident_detail, dict)
    assert incident_detail.get("hypothesis"), "Incident hypothesis not populated"
    hypothesis_text = str(incident_detail.get("hypothesis", {}).get("hypothesis", ""))
    assert hypothesis_text != "Unknown root cause", (
        f"Expected concrete hypothesis, got: {hypothesis_text}"
    )
    print("CHECK: incident hypothesis PASS")

    proposals = get(f"/incidents/{incident_id}/proposals")
    assert isinstance(proposals, list) and len(proposals) >= 1, "No proposals created"
    print(f"CHECK: {len(proposals)} proposal(s) PASS")

    proposal_id = proposals[0]["id"]
    if proposals[0].get("state") == "simulate":
        approved = post(
            f"/proposals/{proposal_id}/approve",
            {
                "approved": True,
                "actor_id": "verify-script",
                "reason": "Verification approval",
            },
        )
        assert isinstance(approved, dict)
        assert approved.get("state") == "approved", (
            f"Expected approved state, got {approved.get('state')}"
        )
        print("CHECK: simulate proposal approve PASS")

    verifier_steps = [
        s
        for s in supervisor_steps
        if s.get("payload", {}).get("agent") == "verifier"
    ]
    assert len(verifier_steps) >= 1, "Verifier agent did not run"
    print(f"CHECK: {len(verifier_steps)} verifier step(s) PASS")

    reflection_steps = [
        s
        for s in supervisor_steps
        if isinstance(s.get("payload", {}).get("step_reflection"), dict)
    ]
    assert len(reflection_steps) >= 1, "No per-step reflection in audit"
    print(f"CHECK: {len(reflection_steps)} step reflection(s) PASS")

    if isinstance(sim_status, dict) and sim_status.get("execution_mode"):
        print(f"CHECK: execution_mode={sim_status['execution_mode']}")

    alerts = get(f"/events/{event_id}/alerts?limit=20")
    if isinstance(alerts, list):
        open_alerts = [a for a in alerts if a.get("state") == "open"]
        if open_alerts:
            alert_id = open_alerts[0]["id"]
            post(f"/alerts/{alert_id}/acknowledge", {})
            audit_ack = get(f"/audit?event_id={event_id}&limit=100")
            acked = [
                a
                for a in audit_ack
                if isinstance(a, dict)
                and a.get("payload", {}).get("transition") == "acknowledged"
            ]
            assert len(acked) >= 1, "Alert acknowledge not in audit trail"
            print("CHECK: alert acknowledge audit PASS")

    print("\nALL DEMO TRUST VERIFICATION CHECKS PASSED")
    return 0


if __name__ == "__main__":
    sys.exit(main())
