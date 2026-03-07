import { useMemo, useState } from "react";
import { useAlerts } from "../hooks/useAlerts";
import { acknowledgeAlert, resolveAlert } from "../api/alerts";
import { useQueryClient, useMutation } from "@tanstack/react-query";
import { Input } from "../components/ui/input";
import { Select } from "../components/ui/select";
import { Button } from "../components/ui/button";
import AlertTable from "../components/alerts/AlertTable";
import AlertDetailDrawer from "../components/alerts/AlertDetailDrawer";
import { SEVERITY_LEVELS, ALERT_CATEGORIES } from "../constants/ics";
import { toast } from "../components/ui/toast";

export default function AlertsPage() {
  const [filters, setFilters] = useState({ severity: "", status: "", category: "", q: "" });
  const [selectedIds, setSelectedIds] = useState([]);
  const [detail, setDetail] = useState(null);
  const qc = useQueryClient();

  const { data } = useAlerts(filters);
  const alerts = data?.items || data || [];

  const ackMutation = useMutation({
    mutationFn: ({ id, comment }) => acknowledgeAlert(id, comment),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["alerts"] });
      toast({ title: "Alert acknowledged" });
    }
  });

  const resolveMutation = useMutation({
    mutationFn: ({ id, payload }) => resolveAlert(id, payload),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["alerts"] });
      toast({ title: "Alert resolved" });
    }
  });

  const filtered = useMemo(() => {
    let v = alerts;
    if (filters.severity) v = v.filter((a) => a.severity === filters.severity);
    if (filters.status) v = v.filter((a) => a.status === filters.status);
    if (filters.category) v = v.filter((a) => a.category === filters.category);
    if (filters.q) {
      const q = filters.q.toLowerCase();
      v = v.filter((a) => (a.title || "").toLowerCase().includes(q));
    }
    return v;
  }, [alerts, filters]);

  function toggleSelect(id) {
    setSelectedIds((s) => (s.includes(id) ? s.filter((x) => x !== id) : [...s, id]));
  }

  async function bulkAck() {
    for (const id of selectedIds) {
      await ackMutation.mutateAsync({ id, comment: "Bulk acknowledged" });
    }
    setSelectedIds([]);
  }

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-semibold">Alerts</h1>
        <div className="rounded bg-ot-red/20 px-3 py-1 text-sm text-ot-red">
          Open: {filtered.filter((a) => a.status !== "resolved").length}
        </div>
      </div>

      <div className="grid gap-3 md:grid-cols-5">
        <Select value={filters.severity} onChange={(e) => setFilters((s) => ({ ...s, severity: e.target.value }))}>
          <option value="">All Severities</option>
          {Object.keys(SEVERITY_LEVELS).map((s) => (
            <option key={s} value={s}>{s}</option>
          ))}
        </Select>
        <Select value={filters.status} onChange={(e) => setFilters((s) => ({ ...s, status: e.target.value }))}>
          <option value="">All Statuses</option>
          <option value="open">open</option>
          <option value="acknowledged">acknowledged</option>
          <option value="resolved">resolved</option>
        </Select>
        <Select value={filters.category} onChange={(e) => setFilters((s) => ({ ...s, category: e.target.value }))}>
          <option value="">All Categories</option>
          {ALERT_CATEGORIES.map((c, idx) => {
            const value = typeof c === "string" ? c : c.value;
            const label = typeof c === "string" ? c : c.label;
            return (
              <option key={`alert-category-${value || "unknown"}-${idx}`} value={value}>
                {label}
              </option>
            );
          })}
        </Select>
        <Input
          placeholder="Search title"
          value={filters.q}
          onChange={(e) => setFilters((s) => ({ ...s, q: e.target.value }))}
        />
        <Button variant="outline" onClick={bulkAck} disabled={!selectedIds.length}>
          Acknowledge selected ({selectedIds.length})
        </Button>
      </div>

      <AlertTable
        alerts={filtered}
        selected={selectedIds}
        onToggleSelect={toggleSelect}
        onOpen={setDetail}
        onAcknowledge={(a) => ackMutation.mutate({ id: a.id, comment: "Acknowledged from table" })}
        onResolve={(a) => resolveMutation.mutate({ id: a.id, payload: { resolution_note: "Resolved from table" } })}
      />

      <AlertDetailDrawer
        alert={detail}
        open={!!detail}
        onClose={() => setDetail(null)}
        onAcknowledge={(id, comment) => ackMutation.mutate({ id, comment })}
        onResolve={(id, payload) => resolveMutation.mutate({ id, payload })}
      />
    </div>
  );
}
