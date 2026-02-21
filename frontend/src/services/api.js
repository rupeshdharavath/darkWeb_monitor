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
