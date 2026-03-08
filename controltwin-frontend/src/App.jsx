import { Navigate, Route, Routes } from "react-router-dom";
import ProtectedRoute from "./router/ProtectedRoute";
import AppLayout from "./components/layout/AppLayout";
import LoginPage from "./pages/LoginPage";
import DashboardPage from "./pages/DashboardPage";
import AssetsPage from "./pages/AssetsPage";
import AssetDetailPage from "./pages/AssetDetailPage";
import TopologyPage from "./pages/TopologyPage";
import AlertsPage from "./pages/AlertsPage";
import CollectorsPage from "./pages/CollectorsPage";
import UsersPage from "./pages/UsersPage";
import SettingsPage from "./pages/SettingsPage";
import SitesPage from "./pages/SitesPage";
import AssetCreatePage from "./pages/AssetCreatePage";

function ProtectedLayout({ children, minRole }) {
  return (
    <ProtectedRoute minRole={minRole}>
      <AppLayout>{children}</AppLayout>
    </ProtectedRoute>
  );
}

export default function App() {
  return (
    <Routes>
      <Route path="/login" element={<LoginPage />} />
      <Route path="/" element={<Navigate to="/dashboard" replace />} />
      <Route
        path="/dashboard"
        element={
          <ProtectedLayout>
            <DashboardPage />
          </ProtectedLayout>
        }
      />
      <Route
        path="/assets"
        element={
          <ProtectedLayout>
            <AssetsPage />
          </ProtectedLayout>
        }
      />
      <Route
        path="/assets/:id"
        element={
          <ProtectedLayout>
            <AssetDetailPage />
          </ProtectedLayout>
        }
      />
      <Route
        path="/assets/new"
        element={
          <ProtectedLayout>
            <AssetCreatePage />
          </ProtectedLayout>
        }
      />
      <Route
        path="/topology"
        element={
          <ProtectedLayout>
            <TopologyPage />
          </ProtectedLayout>
        }
      />
      <Route
        path="/alerts"
        element={
          <ProtectedLayout>
            <AlertsPage />
          </ProtectedLayout>
        }
      />
      <Route
        path="/collectors"
        element={
          <ProtectedLayout minRole="ot_analyst">
            <CollectorsPage />
          </ProtectedLayout>
        }
      />
      <Route
        path="/users"
        element={
          <ProtectedLayout minRole="admin">
            <UsersPage />
          </ProtectedLayout>
        }
      />
      <Route
        path="/sites"
        element={
          <ProtectedLayout minRole="admin">
            <SitesPage />
          </ProtectedLayout>
        }
      />
      <Route
        path="/settings"
        element={
          <ProtectedLayout>
            <SettingsPage />
          </ProtectedLayout>
        }
      />
      <Route path="*" element={<Navigate to="/dashboard" replace />} />
    </Routes>
  );
}
