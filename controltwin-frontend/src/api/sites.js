import axiosInstance from "../lib/axios";

export async function getSites() {
  const { data } = await axiosInstance.get("/sites");
  return data;
}

export async function getSite(id) {
  const { data } = await axiosInstance.get(`/sites/${id}`);
  return data;
}

export async function createSite(data) {
  const response = await axiosInstance.post("/sites", data);
  return response.data;
}

export async function updateSite(id, data) {
  const response = await axiosInstance.patch(`/sites/${id}`, data);
  return response.data;
}

export async function activateSite(id) {
  const { data } = await axiosInstance.post(`/sites/${id}/activate`);
  return data;
}

export async function deactivateSite(id) {
  const { data } = await axiosInstance.post(`/sites/${id}/deactivate`);
  return data;
}

export async function deleteSite(id) {
  await axiosInstance.delete(`/sites/${id}`);
}
