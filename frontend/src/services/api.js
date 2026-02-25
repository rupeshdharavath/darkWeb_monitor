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
