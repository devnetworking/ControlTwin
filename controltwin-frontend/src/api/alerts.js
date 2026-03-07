import api from "../lib/axios";

export async function getAlerts(filters = {}) {
  const { data } = await api.get("/alerts", { params: filters });
  return data;
}

export async function acknowledgeAlert(id, comment) {
  const { data } = await api.post(`/alerts/${id}/acknowledge`, { comment });
  return data;
}

export async function resolveAlert(id, payload) {
  const { data } = await api.post(`/alerts/${id}/resolve`, payload);
  return data;
}

export async function createAlert(payload) {
  const { data } = await api.post("/alerts", payload);
  return data;
}
