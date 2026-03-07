import { useMemo } from "react";
import { AlertTriangle, Bell, Database, Activity } from "lucide-react";
import { useQuery } from "@tanstack/react-query";
import MetricCard from "../components/ui/MetricCard";
import TimeSeriesChart from "../components/charts/TimeSeriesChart";
import AlertBarChart from "../components/charts/AlertBarChart";
import { getAssets } from "../api/assets";
import { getAlerts } from "../api/alerts";
import { queryTimeseries } from "../api/datapoints";
import SeverityBadge from "../components/ui/SeverityBadge";
import { Table, TBody, TD, TH, THead, TR } from "../components/ui/table";
import { useSiteContext } from "../hooks/useSiteContext";
import { formatDate } from "../lib/utils";

export default function DashboardPage() {
  const { selectedSite } = useSiteContext();

  const { data: assetsData } = useQuery({
    queryKey: ["assets-dashboard", selectedSite?.id],
    queryFn: () => getAssets({ site_id: selectedSite?.id }),
    refetchInterval: 30000
  });

  const { data: alertsData } = useQuery({
    queryKey: ["alerts-dashboard", selectedSite?.id],
    queryFn: () => getAlerts({ site_id: selectedSite?.id, limit: 100 }),
    refetchInterval: 30000
  });

  const { data: tsData, isLoading: tsLoading } = useQuery({
    queryKey: ["dashboard-timeseries", selectedSite?.id],
    queryFn: () => queryTimeseries({ site_id: selectedSite?.id, range: "6h", limit: 200 }),
    refetchInterval: 30000
  });

  const assets = assetsData?.items || assetsData || [];
  const alerts = alertsData?.items || alertsData || [];

  const summary = useMemo(() => {
    const total = assets.length;
    const online = assets.filter((a) => a.status === "online").length;
    const onlinePct = total ? Math.round((online / total) * 100) : 0;
    const openAlerts = alerts.filter((a) => a.status !== "resolved");
    const criticalAlerts = alerts.filter((a) => a.severity === "critical" && a.status !== "resolved");
    return {
      total,
      onlinePct,
      open: openAlerts.length,
      critical: criticalAlerts.length
    };
  }, [assets, alerts]);

  const chartData = tsData?.data || tsData || [];
  const trendData = (alertsData?.trend || []).slice(0, 7);

  return (
    <div className="space-y-4">
      <div>
        <h1 className="text-2xl font-semibold">Operations Dashboard</h1>
        <p className="text-sm text-gray-300">{selectedSite?.name || "All Sites"}</p>
      </div>

      <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-4">
        <MetricCard icon={<Database className="h-5 w-5" />} title="Total Assets" value={summary.total} iconColor="text-ot-blue" />
        <MetricCard
          icon={<Activity className="h-5 w-5" />}
          title="Online Assets"
          value={summary.onlinePct}
          unit="%"
          iconColor={summary.onlinePct > 90 ? "text-ot-green" : summary.onlinePct >= 60 ? "text-ot-orange" : "text-ot-red"}
        />
        <MetricCard
          icon={<Bell className="h-5 w-5" />}
          title="Open Alerts"
          value={summary.open}
          iconColor={summary.critical > 0 ? "text-ot-red" : "text-ot-orange"}
        />
        <MetricCard icon={<AlertTriangle className="h-5 w-5" />} title="Critical Alerts" value={summary.critical} iconColor="text-ot-red" />
      </div>

      <TimeSeriesChart data={chartData} loading={tsLoading} />
      <AlertBarChart data={trendData} />

      <div className="rounded-lg border border-ot-border bg-ot-card p-4">
        <h3 className="mb-3 text-sm font-semibold">Recent Alerts</h3>
        <Table>
          <THead>
            <TR>
              <TH>Severity</TH>
              <TH>Title</TH>
              <TH>Asset</TH>
              <TH>Triggered</TH>
            </TR>
          </THead>
          <TBody>
            {alerts.slice(0, 5).map((a) => (
              <TR key={a.id}>
                <TD><SeverityBadge severity={a.severity} /></TD>
                <TD>{a.title}</TD>
                <TD>{a.asset_name || "-"}</TD>
                <TD>{formatDate(a.triggered_at)}</TD>
              </TR>
            ))}
          </TBody>
        </Table>
      </div>
    </div>
  );
}
