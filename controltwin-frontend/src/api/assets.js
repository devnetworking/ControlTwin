import api from "../lib/axios";

export async function getAssets(filters = {}) {
  const { data } = await api.get("/assets", { params: filters });
  return data;
}

export async function getAsset(id) {
  const { data } = await api.get(`/assets/${id}`);
  return data;
}

export async function createAsset(payload) {
  const { data } = await api.post("/assets", payload);
  return data;
}

export async function updateAsset(id, payload) {
  const { data } = await api.put(`/assets/${id}`, payload);
  return data;
}

export async function deleteAsset(id) {
  const { data } = await api.delete(`/assets/${id}`);
  return data;
}
