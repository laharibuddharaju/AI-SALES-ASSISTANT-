// ─── Central API layer ────────────────────────────────────────────────────────
// Reads the port from localStorage so the user can switch between 8000 / 8001
// without touching source code.

const PORT = localStorage.getItem("api_port") || "8000";
export const API_BASE = process.env.REACT_APP_API_URL || `http://127.0.0.1:${PORT}/api/v1`;

// ─── Token helpers ─────────────────────────────────────────────────────────────
export const getToken = () => localStorage.getItem("access_token");
export const getRefresh = () => localStorage.getItem("refresh_token");
export const saveTokens = (data) => {
  localStorage.setItem("access_token", data.access_token);
  localStorage.setItem("refresh_token", data.refresh_token);
};
export const clearTokens = () => {
  localStorage.removeItem("access_token");
  localStorage.removeItem("refresh_token");
};

// ─── Auto-refresh + fetch wrapper ─────────────────────────────────────────────
async function apiFetch(path, options = {}, retry = true) {
  const res = await fetch(`${API_BASE}${path}`, {
    ...options,
    headers: {
      "Content-Type": "application/json",
      ...(getToken() ? { Authorization: `Bearer ${getToken()}` } : {}),
      ...(options.headers || {}),
    },
  });

  // Auto-refresh on 401
  if (res.status === 401 && retry && getRefresh()) {
    const refreshed = await refreshTokens();
    if (refreshed) return apiFetch(path, options, false);
    clearTokens();
    window.location.reload();
    return;
  }

  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    throw new Error(err.detail || `HTTP ${res.status}`);
  }

  return res.json();
}

// ─── Auth ──────────────────────────────────────────────────────────────────────
export const registerUser = async (email, password) => {
  const res = await fetch(`${API_BASE}/register`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ email, password }),
  });
  const data = await res.json();
  if (!res.ok) throw new Error(data.detail || "Registration failed");
  return data;
};

export const loginUser = async (email, password) => {
  const res = await fetch(`${API_BASE}/login`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ email, password }),
  });
  const data = await res.json();
  if (!res.ok) throw new Error(data.detail || "Invalid credentials");
  saveTokens(data);
  return data;
};

const refreshTokens = async () => {
  try {
    const res = await fetch(`${API_BASE}/refresh`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ refresh_token: getRefresh() }),
    });
    if (!res.ok) return false;
    const data = await res.json();
    saveTokens(data);
    return true;
  } catch {
    return false;
  }
};

// ─── Chat ──────────────────────────────────────────────────────────────────────
export const sendMessage = (message) =>
  apiFetch("/chat", {
    method: "POST",
    body: JSON.stringify({ user_id: getToken()?.slice(-8) || "1", channel: "chat", message }),
  });

// ─── Analytics ─────────────────────────────────────────────────────────────────
export const fetchAnalyticsSummary = () => apiFetch("/analytics/summary");
export const fetchIntentDistribution = () => apiFetch("/analytics/intent-distribution");
export const fetchLeadsOverTime = () => apiFetch("/analytics/leads-over-time");
export const fetchLeadStatusBreakdown = () => apiFetch("/analytics/lead-status-breakdown");

// ─── Leads ────────────────────────────────────────────────────────────────────
export const fetchLeads = ({ page = 1, limit = 25, status = "", search = "" } = {}) => {
  const params = new URLSearchParams({ page, limit });
  if (status) params.set("status", status);
  if (search) params.set("search", search);
  return apiFetch(`/leads?${params}`);
};

export const createLead = (payload) =>
  apiFetch("/leads", { method: "POST", body: JSON.stringify(payload) });

export const updateLead = (id, payload) =>
  apiFetch(`/leads/${id}`, { method: "PATCH", body: JSON.stringify(payload) });

export const deleteLead = (id) =>
  apiFetch(`/leads/${id}`, { method: "DELETE" });

export const syncLeads = () =>
  apiFetch("/leads/sync", { method: "POST" });

// ─── Approvals ────────────────────────────────────────────────────────────────
export const fetchApprovals = (status = "pending") => apiFetch(`/approvals?status=${status}`);
export const resolveApproval = (id, approved) =>
  apiFetch(`/approvals/${id}/resolve?approved=${approved}`, { method: "POST" });