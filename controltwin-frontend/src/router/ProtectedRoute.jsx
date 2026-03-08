import { Navigate } from "react-router-dom";
import { useAuth } from "../hooks/useAuth";

const ROLE_ORDER = ["viewer", "readonly", "ot_operator", "ot_analyst", "admin", "super_admin"];

export default function ProtectedRoute({ children, minRole }) {
  const { isAuthenticated, role } = useAuth();

  if (!isAuthenticated) return <Navigate to="/login" replace />;

  if (minRole) {
    const current = ROLE_ORDER.indexOf(role);
    const required = ROLE_ORDER.indexOf(minRole);
    if (current < required) return <Navigate to="/dashboard" replace />;
  }

  return children;
}
