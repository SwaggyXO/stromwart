import json
import os
import time
import urllib.request

BASE = os.environ.get("STROMWART_BASE", "http://localhost:8001/v1")


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


st = get("/simulation/status")
if isinstance(st, dict) and st.get("status") == "running":
    post("/simulation/stop")
    time.sleep(1)

start = post("/simulation/start", {"scenario_id": "cdn_regional_outage", "speed_multiplier": 50})
event_id = start["event_id"]
for _ in range(30):
    time.sleep(5)
    sim = get("/simulation/status")
    if isinstance(sim, dict) and sim.get("status") == "completed":
        break

incidents = get(f"/events/{event_id}/incidents")
if not incidents:
    print("no incidents")
    raise SystemExit(1)

incident_id = incidents[0]["id"]
inc = get(f"/incidents/{incident_id}")
print("hypothesis:", inc.get("hypothesis"))
print("proposals:", get(f"/incidents/{incident_id}/proposals"))
runs = get(f"/incidents/{incident_id}/agent-runs?limit=20")
print("agent runs:", len(runs))
audit = get(f"/audit?event_id={event_id}&limit=50")
print("audit artifact types:", [a.get("artifact_type") for a in audit])
for entry in audit:
    if entry.get("artifact_type") == "supervisor_step":
        p = entry.get("payload", {})
        print("step:", p.get("agent"), p.get("action"), "ok=", p.get("success"))
