#!/usr/bin/env bash
set -euo pipefail

API_URL="${API_URL:-http://localhost:8000}"
FRONTEND_URL="${FRONTEND_URL:-http://localhost:8081}"

printf '\n[STEP 5/6/7/8/9] Stack validation started\n'
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
admin_headers = {"X-SOC-Role": "admin"}


def get_json(url: str, headers: dict | None = None):
    req = urllib.request.Request(url, method="GET", headers=headers or {})
    with urllib.request.urlopen(req, timeout=10) as resp:
        return resp.status, json.loads(resp.read().decode("utf-8"))


def post_json(url: str, payload: dict, headers: dict | None = None):
    data = json.dumps(payload).encode("utf-8")
    req_headers = {"Content-Type": "application/json"}
    if headers:
        req_headers.update(headers)
    req = urllib.request.Request(
        url,
        data=data,
        method="POST",
        headers=req_headers,
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
    status, analysis = post_json(f"{api}/api/v1/alerts/analyze", sample, headers=admin_headers)
    assert status == 200
    assert analysis["triage"]["severity"] in {"high", "critical"}
    assert analysis["response"]["containment_priority"] in {"P1", "P2"}
    assert "threat_intel" in analysis["investigation"]
    assert analysis.get("case_id")
    assert "automation" in analysis
    assert "jira" in analysis["automation"]
    assert "slack" in analysis["automation"]
except Exception as exc:
    print(f"[FAIL] Analysis endpoint validation failed: {exc}")
    sys.exit(1)

try:
    status, kb = get_json(f"{api}/api/v1/knowledge/search?query=mimikatz", headers=admin_headers)
    assert status == 200
    assert len(kb.get("results", [])) > 0
except Exception as exc:
    print(f"[FAIL] Knowledge search validation failed: {exc}")
    sys.exit(1)

try:
    status, playbooks = get_json(f"{api}/api/v1/playbooks", headers=admin_headers)
    assert status == 200
    ids = {item["id"] for item in playbooks.get("playbooks", [])}
    assert {"block_ip", "isolate_host"}.issubset(ids)
except Exception as exc:
    print(f"[FAIL] Playbook endpoint validation failed: {exc}")
    sys.exit(1)

try:
    status, phase_status = get_json(f"{api}/api/v1/next-phases/status", headers=admin_headers)
    assert status == 200
    assert "phase2" in phase_status and "phase3" in phase_status
    assert "completion_percent" in phase_status["phase2"]
except Exception as exc:
    print(f"[FAIL] Next-phase status endpoint validation failed: {exc}")
    sys.exit(1)

try:
    status, quickstart = get_json(f"{api}/api/v1/next-phases/quickstart", headers=admin_headers)
    assert status == 200
    assert len(quickstart.get("phase2_next_steps", [])) > 0
    assert len(quickstart.get("phase3_next_steps", [])) > 0
except Exception as exc:
    print(f"[FAIL] Next-phase quickstart endpoint validation failed: {exc}")
    sys.exit(1)

try:
    status, integrations = get_json(f"{api}/api/v1/next-phases/integrations", headers=admin_headers)
    assert status == 200
    records = integrations.get("integrations", [])
    assert isinstance(records, list)
    assert len(records) >= 4
    for item in records:
        assert "missing_fields" in item
except Exception as exc:
    print(f"[FAIL] Next-phase integrations endpoint validation failed: {exc}")
    sys.exit(1)

try:
    status, intel_status = get_json(f"{api}/api/v1/phase3/threat-intel/status", headers=admin_headers)
    assert status == 200
    assert "enabled" in intel_status and "ioc_count" in intel_status
except Exception as exc:
    print(f"[FAIL] Threat-intel status endpoint validation failed: {exc}")
    sys.exit(1)

try:
    status, case_store_status = get_json(f"{api}/api/v1/phase3/case-store/status", headers=admin_headers)
    assert status == 200
    assert "configured" in case_store_status and "ready" in case_store_status
except Exception as exc:
    print(f"[FAIL] Case-store status endpoint validation failed: {exc}")
    sys.exit(1)

try:
    status, kpi = get_json(f"{api}/api/v1/phase3/kpi/overview", headers=admin_headers)
    assert status == 200
    assert "total_incidents" in kpi
except Exception as exc:
    print(f"[FAIL] KPI overview endpoint validation failed: {exc}")
    sys.exit(1)

try:
    status, trends = get_json(f"{api}/api/v1/phase3/kpi/trends", headers=admin_headers)
    assert status == 200
    assert isinstance(trends.get("daily_incidents", []), list)
except Exception as exc:
    print(f"[FAIL] KPI trend endpoint validation failed: {exc}")
    sys.exit(1)

try:
    status, sla = get_json(f"{api}/api/v1/phase3/sla/overview", headers=admin_headers)
    assert status == 200
    assert "compliance_percent" in sla
except Exception as exc:
    print(f"[FAIL] SLA overview endpoint validation failed: {exc}")
    sys.exit(1)

try:
    status, policy = get_json(f"{api}/api/v1/phase3/rbac/policy", headers=admin_headers)
    assert status == 200
    assert "policy_matrix" in policy
except Exception as exc:
    print(f"[FAIL] RBAC policy endpoint validation failed: {exc}")
    sys.exit(1)

print("[PASS] Step 5/6/7/8/9 stack validation passed.")
PY
