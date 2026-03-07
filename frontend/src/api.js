const API_BASE = (import.meta.env.VITE_API_BASE_URL || "").replace(/\/$/, "");

async function request(path, options = {}, role = "analyst") {
  const response = await fetch(`${API_BASE}${path}`, {
    ...options,
    headers: {
      "Content-Type": "application/json",
      "X-SOC-Role": role,
      ...(options.headers || {})
    }
  });

  if (!response.ok) {
    const body = await response.text();
    throw new Error(body || `Request failed with status ${response.status}`);
  }

  return response.json();
}

export function getHealth(role = "analyst") {
  return request("/api/v1/health", { method: "GET" }, role);
}

export function analyzeAlert(payload, role = "analyst") {
  return request(
    "/api/v1/alerts/analyze",
    {
      method: "POST",
      body: JSON.stringify(payload)
    },
    role
  );
}

export function searchKnowledge(query, role = "analyst") {
  const params = new URLSearchParams({ query });
  return request(`/api/v1/knowledge/search?${params.toString()}`, { method: "GET" }, role);
}

export function getPlaybooks(role = "analyst") {
  return request("/api/v1/playbooks", { method: "GET" }, role);
}

export function getKpiOverview(days = 30, role = "analyst") {
  return request(`/api/v1/phase3/kpi/overview?days=${days}`, { method: "GET" }, role);
}

export function getKpiTrends(days = 14, role = "analyst") {
  return request(`/api/v1/phase3/kpi/trends?days=${days}`, { method: "GET" }, role);
}

export function getSlaOverview(days = 30, role = "analyst") {
  return request(`/api/v1/phase3/sla/overview?days=${days}`, { method: "GET" }, role);
}

export function getCaseStoreStatus(role = "analyst") {
  return request("/api/v1/phase3/case-store/status", { method: "GET" }, role);
}
