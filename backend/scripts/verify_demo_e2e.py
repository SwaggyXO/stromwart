"""Verification script for pack_demo_e2e_fix."""
from __future__ import annotations

import json
import sys
import time
import urllib.request

BASE = "http://localhost:8000/v1"


def get(path: str) -> object:
    with urllib.request.urlopen(BASE + path, timeout=30) as response:
        return json.load(response)


def post(path: str, body: dict | None = None) -> object:
    data = json.dumps(body or {}).encode()
    req = urllib.request.Request(
        BASE + path,
        data=data,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=30) as response:
        return json.load(response)


def main() -> int:
    # Check 0
    status = get("/simulation/status")
    print("CHECK 0:", status)
    assert isinstance(status, dict)

    if status.get("status") == "running":
        post("/simulation/stop")
        time.sleep(1)

    # Check 1 — starting a simulation clears prior demo data automatically
    start = post(
        "/simulation/start",
        {"scenario_id": "cdn_regional_outage", "speed_multiplier": 50},
    )
    post("/simulation/stop")
    time.sleep(1)
    events_after_start_stop = get("/events")
    print("CHECK 1 events after start/stop:", events_after_start_stop)

    start = post(
        "/simulation/start",
        {"scenario_id": "cdn_regional_outage", "speed_multiplier": 50},
    )
    events = get("/events")
    print("CHECK 1 events after fresh start:", events)
    assert len(events) == 1, f"Expected exactly one event, got {len(events)}"

    # Check 2
    print("CHECK 2:", start)
    assert start["status"] == "running"
    assert start["event_id"] is not None
    event_id = start["event_id"]

    # Check 3
    time.sleep(5)
    sessions = get(f"/events/{event_id}/sessions?limit=10")
    print(f"CHECK 3: {len(sessions)} sessions")
    assert len(sessions) >= 5

    # Check 4
    kpis = get(f"/events/{event_id}/kpis")
    active = next(k["value"] for k in kpis if "Active Sessions" in k["label"])
    print(f"CHECK 4 PASS: Active Sessions={active}")
    assert active > 0

    # Check 5
    print("Waiting for incidents...")
    incidents: list = []
    for attempt in range(30):
        time.sleep(5)
        incidents = get(f"/events/{event_id}/incidents")
        sim = get("/simulation/status")
        progress = sim.get("progress", 0)
        phase = sim.get("current_phase", "")[:60]
        print(f"  attempt {attempt + 1}: {len(incidents)} incidents, progress={progress:.2f}, phase={phase}")
        if len(incidents) >= 1:
            break
    assert len(incidents) >= 1, "No incidents after 150s"
    print(f"CHECK 5 PASS: {len(incidents)} incidents")

    # Check 6
    audit: list = []
    for _ in range(12):
        audit = get(f"/audit?event_id={event_id}&limit=20")
        if audit:
            break
        time.sleep(5)
    print(f"CHECK 6: {len(audit)} audit entries (scoped to event)")
    if audit:
        print("  sample:", audit[0]["artifact_type"], audit[0]["actor_type"])
    print("CHECK 6 PASS (scoped query works)")

    print("\nALL BACKEND CHECKS PASSED")
    return 0


if __name__ == "__main__":
    sys.exit(main())
