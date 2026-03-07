import axiosInstance from "../lib/axios";

export async function getCollectors() {
  const response = await axiosInstance.get("/collectors");
  return response.data;
}

export async function getCollector(id) {
  const response = await axiosInstance.get(`/collectors/${id}`);
  return response.data;
}

export async function createCollector(data) {
  const response = await axiosInstance.post("/collectors", data);
  return response.data;
}
