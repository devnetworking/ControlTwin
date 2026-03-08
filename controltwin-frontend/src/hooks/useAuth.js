import { useMemo } from "react";
import * as authApi from "../api/auth";
import { useAuthStore } from "../store/authStore";

const ROLE_HIERARCHY = [
  "readonly",
  "viewer",
  "ot_operator",
  "ot_analyst",
  "admin",
  "super_admin",
];

const PERMISSIONS_BY_ROLE = {
  readonly: ["read:dashboard"],
  viewer: ["read:dashboard", "read:assets", "read:alerts"],
  ot_operator: ["read:dashboard", "read:assets", "read:alerts", "write:datapoints"],
  ot_analyst: [
    "read:dashboard",
    "read:assets",
    "read:alerts",
    "write:datapoints",
    "analyze:alerts",
    "read:predictive",
  ],
  admin: ["*"],
  super_admin: ["*"],
};

export function useAuth() {
  const user = useAuthStore((s) => s.user);
  const role = user?.role || "viewer";
  const isAuthenticated = useAuthStore((s) => s.isAuthenticated);
  const storeLogin = useAuthStore((s) => s.login);
  const storeLogout = useAuthStore((s) => s.logout);

  const login = async (username, password) => {
    // Ensure API call path is explicit, then persist through store contract.
    await authApi.login(username, password);
    return storeLogin({ username, password });
  };

  const logout = () => {
    authApi.logout();
    storeLogout();
  };

  const hasRole = (requiredRole) => {
    const currentIdx = ROLE_HIERARCHY.indexOf(role);
    const requiredIdx = ROLE_HIERARCHY.indexOf(requiredRole);
    if (requiredIdx === -1) return false;
    return currentIdx >= requiredIdx;
  };

  const hasPermission = (permission) => {
    const permissions = PERMISSIONS_BY_ROLE[role] || [];
    return permissions.includes("*") || permissions.includes(permission);
  };

  const flags = useMemo(
    () => ({
      isAdmin: role === "admin" || role === "super_admin",
      isOTAnalyst: role === "ot_analyst",
    }),
    [role]
  );

  return {
    user,
    role,
    isAuthenticated,
    login,
    logout,
    hasRole,
    hasPermission,
    ...flags,
  };
}
