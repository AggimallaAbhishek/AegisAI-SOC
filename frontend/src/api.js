const API_BASE = (import.meta.env.VITE_API_BASE_URL || "").replace(/\/$/, "");

async function request(path, options = {}) {
  const response = await fetch(`${API_BASE}${path}`, {
    ...options,
    headers: {
      "Content-Type": "application/json",
      ...(options.headers || {})
    }
  });

  if (!response.ok) {
    const body = await response.text();
    throw new Error(body || `Request failed with status ${response.status}`);
  }

  return response.json();
}

export function getHealth() {
  return request("/api/v1/health", { method: "GET" });
}

export function analyzeAlert(payload) {
  return request("/api/v1/alerts/analyze", {
    method: "POST",
    body: JSON.stringify(payload)
  });
}

export function searchKnowledge(query) {
  const params = new URLSearchParams({ query });
  return request(`/api/v1/knowledge/search?${params.toString()}`, { method: "GET" });
}

export function getPlaybooks() {
  return request("/api/v1/playbooks", { method: "GET" });
}
