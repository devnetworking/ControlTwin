import api from "../lib/axios";

export async function listSettings(params = {}) {
  const response = await api.get("/settings", { params });
  return response.data;
}

export async function upsertSetting(key, payload) {
  const response = await api.put(`/settings/${encodeURIComponent(key)}`, payload);
  return response.data;
}

export async function bulkUpsertSettings(items = []) {
  const response = await api.post("/settings/bulk", { items });
  return response.data;
}
