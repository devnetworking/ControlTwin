import axiosInstance from "../lib/axios";

export async function login(username, password) {
  const { data } = await axiosInstance.post("/auth/login", { username, password });
  return data;
}

export function logout() {
  // No API call by design; token/session cleanup is handled by authStore.
  return true;
}

export async function refreshToken(refresh_token) {
  const { data } = await axiosInstance.post("/auth/refresh", { refresh_token });
  return data;
}

export async function getMe() {
  const { data } = await axiosInstance.get("/users/me");
  return data;
}
