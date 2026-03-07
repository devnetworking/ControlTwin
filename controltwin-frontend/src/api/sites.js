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
