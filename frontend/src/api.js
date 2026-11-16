const API_URL = import.meta.env.VITE_API_URL || "http://localhost:8000";

async function request(path, options = {}) {
  const response = await fetch(`${API_URL}${path}`, {
    headers: { "Content-Type": "application/json", ...(options.headers || {}) },
    ...options,
  });
  if (!response.ok) {
    const detail = await response.text();
    throw new Error(detail || `HTTP ${response.status}`);
  }
  return response.json();
}

export const api = {
  health: () => request("/health"),
  metrics: () => request("/api/metrics"),
  movements: () => request("/api/movements"),
  pipeline: () => request("/api/pipeline", { method: "POST" }),
  analyze: () => request("/api/analyze", { method: "POST" }),
};
