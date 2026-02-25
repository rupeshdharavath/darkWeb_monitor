import axios from "axios";

const api = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL || "",
  headers: {
    "Content-Type": "application/json"
  }
});

export async function scanOnion(url) {
  const response = await api.post("/scan", { url });
  return response.data;
}

export async function getHistory() {
  const response = await api.get("/history");
  return response.data;
}

export async function getHistoryEntry(entryId) {
  const response = await api.get(`/history/${entryId}`);
  return response.data;
}

// Monitor Management
export async function createMonitor(url, interval = 5) {
  const response = await api.post("/monitors", { url, interval });
  return response.data;
}

export async function listMonitors() {
  const response = await api.get("/monitors");
  return response.data;
}

export async function getMonitor(monitorId) {
  const response = await api.get(`/monitors/${monitorId}`);
  return response.data;
}

export async function deleteMonitor(monitorId) {
  const response = await api.delete(`/monitors/${monitorId}`);
  return response.data;
}

export async function deleteAllMonitors() {
  const response = await api.delete("/monitors/all");
  return response.data;
}

export async function pauseMonitor(monitorId) {
  const response = await api.post(`/monitors/${monitorId}/pause`);
  return response.data;
}

export async function resumeMonitor(monitorId) {
  const response = await api.post(`/monitors/${monitorId}/resume`);
  return response.data;
}

// Alerts
export async function getAlerts() {
  const response = await api.get("/alerts");
  return response.data;
}

export async function acknowledgeAlert(alertId) {
  const response = await api.post(`/alerts/${alertId}/acknowledge`);
  return response.data;
}

// Comparison
export async function compareScans(urlHash, limit = 2) {
  const response = await api.get(`/compare/${urlHash}`, { params: { limit } });
  return response.data;
}
