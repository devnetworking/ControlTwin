import axiosInstance from "../lib/axios";

export async function listUsers() {
  const { data } = await axiosInstance.get("/users");
  return Array.isArray(data) ? data : [];
}

export async function createUser(payload) {
  const { data } = await axiosInstance.post("/users", payload);
  return data;
}

export async function updateUser(userId, payload) {
  const { data } = await axiosInstance.patch(`/users/${userId}`, payload);
  return data;
}

export async function activateUser(userId) {
  const { data } = await axiosInstance.post(`/users/${userId}/activate`);
  return data;
}

export async function deactivateUser(userId) {
  const { data } = await axiosInstance.post(`/users/${userId}/deactivate`);
  return data;
}

export async function deleteUser(userId) {
  await axiosInstance.delete(`/users/${userId}`);
}
