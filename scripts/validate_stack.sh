#!/usr/bin/env bash
set -euo pipefail

API_URL="${API_URL:-http://localhost:8000}"
FRONTEND_URL="${FRONTEND_URL:-http://localhost:8081}"

printf '\n[STEP 5/6] Stack validation started\n'
printf '[INFO] API_URL=%s\n' "$API_URL"
printf '[INFO] FRONTEND_URL=%s\n\n' "$FRONTEND_URL"

python3 - <<'PY'
import json
import os
import sys
import urllib.error
import urllib.request

api = os.environ.get("API_URL", "http://localhost:8000")
frontend = os.environ.get("FRONTEND_URL", "http://localhost:8081")


def get_json(url: str):
    req = urllib.request.Request(url, method="GET")
    with urllib.request.urlopen(req, timeout=10) as resp:
        return resp.status, json.loads(resp.read().decode("utf-8"))


def post_json(url: str, payload: dict):
    data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(
        url,
        data=data,
        method="POST",
        headers={"Content-Type": "application/json"},
    )
    with urllib.request.urlopen(req, timeout=10) as resp:
        return resp.status, json.loads(resp.read().decode("utf-8"))


try:
    with urllib.request.urlopen(frontend, timeout=10) as resp:
        assert resp.status == 200, "Frontend is not returning HTTP 200"
except Exception as exc:
    print(f"[FAIL] Frontend check failed: {exc}")
    sys.exit(1)

try:
    status, health = get_json(f"{api}/api/v1/health")
    assert status == 200
    assert health.get("status") == "ok"
except Exception as exc:
    print(f"[FAIL] API health check failed: {exc}")
    sys.exit(1)

sample = {
    "source": "SIEM",
    "host": "FIN-WS-442",
    "user": "finance.admin",
    "ip_address": "203.0.113.56",
    "process_name": "mimikatz.exe",
    "command_line": "mimikatz.exe sekurlsa::logonpasswords",
    "description": "Potential credential dumping behavior detected on endpoint",
}

try:
    status, analysis = post_json(f"{api}/api/v1/alerts/analyze", sample)
    assert status == 200
    assert analysis["triage"]["severity"] in {"high", "critical"}
    assert analysis["response"]["containment_priority"] in {"P1", "P2"}
except Exception as exc:
    print(f"[FAIL] Analysis endpoint validation failed: {exc}")
    sys.exit(1)

try:
    status, kb = get_json(f"{api}/api/v1/knowledge/search?query=mimikatz")
    assert status == 200
    assert len(kb.get("results", [])) > 0
except Exception as exc:
    print(f"[FAIL] Knowledge search validation failed: {exc}")
    sys.exit(1)

try:
    status, playbooks = get_json(f"{api}/api/v1/playbooks")
    assert status == 200
    ids = {item["id"] for item in playbooks.get("playbooks", [])}
    assert {"block_ip", "isolate_host"}.issubset(ids)
except Exception as exc:
    print(f"[FAIL] Playbook endpoint validation failed: {exc}")
    sys.exit(1)

try:
    status, phase_status = get_json(f"{api}/api/v1/next-phases/status")
    assert status == 200
    assert "phase2" in phase_status and "phase3" in phase_status
except Exception as exc:
    print(f"[FAIL] Next-phase status endpoint validation failed: {exc}")
    sys.exit(1)

try:
    status, quickstart = get_json(f"{api}/api/v1/next-phases/quickstart")
    assert status == 200
    assert len(quickstart.get("phase2_next_steps", [])) > 0
    assert len(quickstart.get("phase3_next_steps", [])) > 0
except Exception as exc:
    print(f"[FAIL] Next-phase quickstart endpoint validation failed: {exc}")
    sys.exit(1)

print("[PASS] Step 5/6 stack validation passed.")
PY
