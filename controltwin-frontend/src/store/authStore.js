import { create } from "zustand";
import { login as loginApi, refreshToken as refreshApi } from "../api/auth";

const AUTH_KEY = "controltwin_auth";

export const useAuthStore = create((set, get) => ({
  user: null,
  accessToken: null,
  refreshToken: null,
  isAuthenticated: false,

  setTokens: (accessToken, refreshToken) => {
    const state = get();
    const next = { ...state, accessToken, refreshToken, isAuthenticated: !!accessToken };
    set(next);
    localStorage.setItem(
      AUTH_KEY,
      JSON.stringify({
        user: next.user,
        accessToken,
        refreshToken,
        isAuthenticated: !!accessToken
      })
    );
  },

  login: async ({ username, password }) => {
    const data = await loginApi(username, password);
    const payload = {
      user: data.user || { username, role: data.role || "viewer" },
      accessToken: data.access_token || data.accessToken,
      refreshToken: data.refresh_token || data.refreshToken,
      isAuthenticated: true
    };
    set(payload);
    localStorage.setItem(AUTH_KEY, JSON.stringify(payload));
    return payload;
  },

  logout: () => {
    set({
      user: null,
      accessToken: null,
      refreshToken: null,
      isAuthenticated: false
    });
    localStorage.removeItem(AUTH_KEY);
    window.location.href = "/login";
  },

  initFromStorage: () => {
    try {
      const raw = localStorage.getItem(AUTH_KEY);
      if (!raw) return;
      const parsed = JSON.parse(raw);
      set({
        user: parsed.user || null,
        accessToken: parsed.accessToken || null,
        refreshToken: parsed.refreshToken || null,
        isAuthenticated: !!parsed.accessToken
      });
    } catch {
      localStorage.removeItem(AUTH_KEY);
    }
  },

  attemptRefresh: async () => {
    const { refreshToken } = get();
    if (!refreshToken) return null;
    const data = await refreshApi(refreshToken);
    const access = data.access_token || data.accessToken;
    const refresh = data.refresh_token || data.refreshToken || refreshToken;
    get().setTokens(access, refresh);
    return access;
  }
}));
