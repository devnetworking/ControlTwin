import { useEffect, useMemo, useState } from "react";
import { bulkUpsertSettings, listSettings } from "../api/settings";
import { useAuthStore } from "../store/authStore";

const DEFAULTS = {
  ui_theme: { mode: "dark", compactMode: false, language: "fr" },
  notifications: {
    emailEnabled: true,
    smsEnabled: false,
    pushEnabled: true,
    dailyDigest: true
  },
  dashboard: {
    refreshIntervalSec: 10,
    showKpiCards: true,
    showTopologyMiniMap: true,
    defaultTimeRange: "24h"
  },
  security: {
    sessionTimeoutMin: 30,
    mfaRequired: false,
    loginAlertEnabled: true
  },
  data_collection: {
    pollIntervalMs: 1000,
    writeBatchSize: 500,
    retentionDays: 30,
    anomalyDetectionEnabled: true
  }
};

function Toggle({ checked, onChange }) {
  return (
    <button
      type="button"
      className={`h-6 w-12 rounded-full transition ${
        checked ? "bg-emerald-500" : "bg-gray-600"
      }`}
      onClick={() => onChange(!checked)}
    >
      <span
        className={`block h-6 w-6 rounded-full bg-white transition ${
          checked ? "translate-x-6" : "translate-x-0"
        }`}
      />
    </button>
  );
}

export default function SettingsPage() {
  const user = useAuthStore((s) => s.user);
  const [settings, setSettings] = useState(DEFAULTS);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [status, setStatus] = useState("");

  const userId = user?.id;

  const entries = useMemo(
    () => Object.entries(settings).map(([key, value]) => ({ key, value })),
    [settings]
  );

  useEffect(() => {
    let mounted = true;
    async function run() {
      try {
        const params = userId ? { scope: "user", user_id: userId } : { scope: "user" };
        const rows = await listSettings(params);
        const merged = { ...DEFAULTS };
        rows.forEach((r) => {
          merged[r.key] = r.value;
        });
        if (mounted) setSettings(merged);
      } catch {
        if (mounted) setStatus("Impossible de charger les paramètres serveur.");
      } finally {
        if (mounted) setLoading(false);
      }
    }
    run();
    return () => {
      mounted = false;
    };
  }, [userId]);

  async function saveAll() {
    setSaving(true);
    setStatus("");
    try {
      await bulkUpsertSettings(
        Object.entries(settings).map(([key, value]) => ({
          key,
          scope: "user",
          user_id: userId || undefined,
          value
        }))
      );
      setStatus("Paramètres sauvegardés.");
    } catch {
      setStatus("Échec de sauvegarde des paramètres.");
    } finally {
      setSaving(false);
    }
  }

  function updateSection(section, patch) {
    setSettings((prev) => ({ ...prev, [section]: { ...prev[section], ...patch } }));
  }

  if (loading) {
    return <div className="text-gray-300">Chargement des paramètres...</div>;
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-semibold">Settings</h1>
        <button
          type="button"
          className="rounded border border-ot-border bg-ot-card px-4 py-2 text-sm hover:bg-gray-800 disabled:opacity-50"
          onClick={saveAll}
          disabled={saving}
        >
          {saving ? "Sauvegarde..." : "Sauvegarder"}
        </button>
      </div>

      {status ? (
        <div className="rounded border border-ot-border bg-ot-card p-3 text-sm text-gray-300">
          {status}
        </div>
      ) : null}

      <section className="rounded-lg border border-ot-border bg-ot-card p-4 space-y-3">
        <h2 className="font-medium">UI / Affichage</h2>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
          <label className="space-y-1">
            <span className="text-sm text-gray-300">Mode</span>
            <select
              className="w-full rounded bg-gray-900 border border-gray-700 px-2 py-1"
              value={settings.ui_theme.mode}
              onChange={(e) => updateSection("ui_theme", { mode: e.target.value })}
            >
              <option value="dark">dark</option>
              <option value="light">light</option>
              <option value="system">system</option>
            </select>
          </label>
          <label className="space-y-1">
            <span className="text-sm text-gray-300">Langue</span>
            <select
              className="w-full rounded bg-gray-900 border border-gray-700 px-2 py-1"
              value={settings.ui_theme.language}
              onChange={(e) => updateSection("ui_theme", { language: e.target.value })}
            >
              <option value="fr">fr</option>
              <option value="en">en</option>
            </select>
          </label>
          <div className="flex items-end justify-between rounded border border-gray-700 p-2">
            <span className="text-sm text-gray-300">Compact mode</span>
            <Toggle
              checked={settings.ui_theme.compactMode}
              onChange={(v) => updateSection("ui_theme", { compactMode: v })}
            />
          </div>
        </div>
      </section>

      <section className="rounded-lg border border-ot-border bg-ot-card p-4 space-y-3">
        <h2 className="font-medium">Notifications</h2>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
          {["emailEnabled", "smsEnabled", "pushEnabled", "dailyDigest"].map((k) => (
            <div key={k} className="flex items-center justify-between rounded border border-gray-700 p-2">
              <span className="text-sm text-gray-300">{k}</span>
              <Toggle
                checked={Boolean(settings.notifications[k])}
                onChange={(v) => updateSection("notifications", { [k]: v })}
              />
            </div>
          ))}
        </div>
      </section>

      <section className="rounded-lg border border-ot-border bg-ot-card p-4 space-y-3">
        <h2 className="font-medium">Dashboard</h2>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
          <label className="space-y-1">
            <span className="text-sm text-gray-300">Refresh interval (sec)</span>
            <input
              type="number"
              className="w-full rounded bg-gray-900 border border-gray-700 px-2 py-1"
              value={settings.dashboard.refreshIntervalSec}
              onChange={(e) =>
                updateSection("dashboard", { refreshIntervalSec: Number(e.target.value || 0) })
              }
            />
          </label>
          <label className="space-y-1">
            <span className="text-sm text-gray-300">Default time range</span>
            <select
              className="w-full rounded bg-gray-900 border border-gray-700 px-2 py-1"
              value={settings.dashboard.defaultTimeRange}
              onChange={(e) => updateSection("dashboard", { defaultTimeRange: e.target.value })}
            >
              <option value="1h">1h</option>
              <option value="24h">24h</option>
              <option value="7d">7d</option>
              <option value="30d">30d</option>
            </select>
          </label>
          <div className="flex items-center justify-between rounded border border-gray-700 p-2">
            <span className="text-sm text-gray-300">Show KPI cards</span>
            <Toggle
              checked={settings.dashboard.showKpiCards}
              onChange={(v) => updateSection("dashboard", { showKpiCards: v })}
            />
          </div>
          <div className="flex items-center justify-between rounded border border-gray-700 p-2">
            <span className="text-sm text-gray-300">Show topology minimap</span>
            <Toggle
              checked={settings.dashboard.showTopologyMiniMap}
              onChange={(v) => updateSection("dashboard", { showTopologyMiniMap: v })}
            />
          </div>
        </div>
      </section>

      <section className="rounded-lg border border-ot-border bg-ot-card p-4 space-y-3">
        <h2 className="font-medium">Security</h2>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
          <label className="space-y-1">
            <span className="text-sm text-gray-300">Session timeout (min)</span>
            <input
              type="number"
              className="w-full rounded bg-gray-900 border border-gray-700 px-2 py-1"
              value={settings.security.sessionTimeoutMin}
              onChange={(e) =>
                updateSection("security", { sessionTimeoutMin: Number(e.target.value || 0) })
              }
            />
          </label>
          <div className="flex items-center justify-between rounded border border-gray-700 p-2">
            <span className="text-sm text-gray-300">MFA required</span>
            <Toggle
              checked={settings.security.mfaRequired}
              onChange={(v) => updateSection("security", { mfaRequired: v })}
            />
          </div>
          <div className="flex items-center justify-between rounded border border-gray-700 p-2">
            <span className="text-sm text-gray-300">Login alert</span>
            <Toggle
              checked={settings.security.loginAlertEnabled}
              onChange={(v) => updateSection("security", { loginAlertEnabled: v })}
            />
          </div>
        </div>
      </section>

      <section className="rounded-lg border border-ot-border bg-ot-card p-4 space-y-3">
        <h2 className="font-medium">Data Collection</h2>
        <div className="grid grid-cols-1 md:grid-cols-4 gap-3">
          <label className="space-y-1">
            <span className="text-sm text-gray-300">Poll interval (ms)</span>
            <input
              type="number"
              className="w-full rounded bg-gray-900 border border-gray-700 px-2 py-1"
              value={settings.data_collection.pollIntervalMs}
              onChange={(e) =>
                updateSection("data_collection", { pollIntervalMs: Number(e.target.value || 0) })
              }
            />
          </label>
          <label className="space-y-1">
            <span className="text-sm text-gray-300">Write batch size</span>
            <input
              type="number"
              className="w-full rounded bg-gray-900 border border-gray-700 px-2 py-1"
              value={settings.data_collection.writeBatchSize}
              onChange={(e) =>
                updateSection("data_collection", { writeBatchSize: Number(e.target.value || 0) })
              }
            />
          </label>
          <label className="space-y-1">
            <span className="text-sm text-gray-300">Retention days</span>
            <input
              type="number"
              className="w-full rounded bg-gray-900 border border-gray-700 px-2 py-1"
              value={settings.data_collection.retentionDays}
              onChange={(e) =>
                updateSection("data_collection", { retentionDays: Number(e.target.value || 0) })
              }
            />
          </label>
          <div className="flex items-center justify-between rounded border border-gray-700 p-2">
            <span className="text-sm text-gray-300">Anomaly detection</span>
            <Toggle
              checked={settings.data_collection.anomalyDetectionEnabled}
              onChange={(v) => updateSection("data_collection", { anomalyDetectionEnabled: v })}
            />
          </div>
        </div>
      </section>

      <details className="rounded-lg border border-ot-border bg-ot-card p-4">
        <summary className="cursor-pointer text-sm text-gray-300">Raw payload preview</summary>
        <pre className="mt-3 overflow-auto text-xs text-gray-300">
          {JSON.stringify(entries, null, 2)}
        </pre>
      </details>
    </div>
  );
}
