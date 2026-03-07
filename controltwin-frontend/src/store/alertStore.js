import { create } from "zustand";

const initialState = {
  unreadCount: 0,
  recentAlerts: [],
  criticalCount: 0,
  highCount: 0,
};

const recomputeSeverityCounts = (alerts) => {
  const criticalCount = alerts.filter((a) => (a?.severity || "").toLowerCase() === "critical").length;
  const highCount = alerts.filter((a) => (a?.severity || "").toLowerCase() === "high").length;
  return { criticalCount, highCount };
};

export const useAlertStore = create((set, get) => ({
  ...initialState,

  setUnreadCount: (n) => set({ unreadCount: Number(n) || 0 }),

  incrementUnread: () => set((state) => ({ unreadCount: state.unreadCount + 1 })),

  markAllRead: () => set({ unreadCount: 0 }),

  addAlert: (alert) =>
    set((state) => {
      const recentAlerts = [alert, ...state.recentAlerts].slice(0, 20);
      const { criticalCount, highCount } = recomputeSeverityCounts(recentAlerts);
      return {
        recentAlerts,
        unreadCount: state.unreadCount + 1,
        criticalCount,
        highCount,
      };
    }),

  removeAlert: (alertId) =>
    set((state) => {
      const recentAlerts = state.recentAlerts.filter((alert) => alert?.id !== alertId);
      const { criticalCount, highCount } = recomputeSeverityCounts(recentAlerts);
      return {
        recentAlerts,
        criticalCount,
        highCount,
      };
    }),

  setRecentAlerts: (alerts) =>
    set(() => {
      const recentAlerts = Array.isArray(alerts) ? alerts.slice(0, 20) : [];
      const { criticalCount, highCount } = recomputeSeverityCounts(recentAlerts);
      return {
        recentAlerts,
        criticalCount,
        highCount,
      };
    }),

  clearAll: () => set({ ...initialState }),

  getAlertsBySerity: (severity) => {
    const normalized = (severity || "").toLowerCase();
    return get().recentAlerts.filter((alert) => (alert?.severity || "").toLowerCase() === normalized);
  },
}));
