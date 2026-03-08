import { useMemo, useState } from "react";
import { useParams, Link } from "react-router-dom";
import { useQuery } from "@tanstack/react-query";
import { getAsset } from "../api/assets";
import { getDatapoints, queryTimeseries } from "../api/datapoints";
import { getAlerts } from "../api/alerts";
import { Card, CardContent, CardHeader, CardTitle } from "../components/ui/card";
import { Button } from "../components/ui/button";
import { Dialog } from "../components/ui/dialog";
import { Input } from "../components/ui/input";
import { Table, TBody, TD, TH, THead, TR } from "../components/ui/table";
import SeverityBadge from "../components/ui/SeverityBadge";
import LoadingSpinner from "../components/ui/LoadingSpinner";
import { formatDate, formatValue } from "../lib/utils";
import { Line, LineChart, ResponsiveContainer } from "recharts";

export default function AssetDetailPage() {
  const { id } = useParams();
  const [editOpen, setEditOpen] = useState(false);

  const { data: asset, isLoading } = useQuery({
    queryKey: ["asset", id],
    queryFn: () => getAsset(id)
  });

  const { data: datapointsData } = useQuery({
    queryKey: ["asset-datapoints", id],
    queryFn: () => getDatapoints(id),
    refetchInterval: 30000
  });

  const datapoints = datapointsData?.items || datapointsData || [];
  const dataPointIds = useMemo(
    () => datapoints.map((dp) => dp.id).filter(Boolean),
    [datapoints]
  );

  const { data: tsData } = useQuery({
    queryKey: ["asset-spark", id, dataPointIds],
    queryFn: () => {
      const stop = new Date();
      const start = new Date(stop.getTime() - 60 * 60 * 1000);
      return queryTimeseries({
        data_point_ids: dataPointIds,
        start: start.toISOString(),
        stop: stop.toISOString(),
        aggregate_window: "1m",
        aggregate_fn: "mean"
      });
    },
    enabled: dataPointIds.length > 0,
    refetchInterval: 30000
  });

  const { data: alertsData } = useQuery({
    queryKey: ["asset-alerts", id],
    queryFn: () => getAlerts({ asset_id: id, limit: 10 })
  });

  if (isLoading) return <LoadingSpinner />;

  const alerts = alertsData?.items || alertsData || [];
  const spark = tsData?.data || tsData || [];

  return (
    <div className="space-y-4">
      <div className="text-sm text-gray-300">
        <Link to="/assets" className="text-ot-blue">Assets</Link> {" > "} {asset?.name}
      </div>

      <div className="grid gap-4 xl:grid-cols-3">
        <Card className="xl:col-span-1">
          <CardHeader className="flex flex-row items-center justify-between">
            <CardTitle>Asset Information</CardTitle>
            <Button size="sm" onClick={() => setEditOpen(true)}>Edit</Button>
          </CardHeader>
          <CardContent className="space-y-1 text-sm">
            <div>Tag: <span className="font-mono">{asset?.tag}</span></div>
            <div>Name: {asset?.name}</div>
            <div>Type: {asset?.asset_type}</div>
            <div>Protocol: {asset?.protocol || "-"}</div>
            <div>IP: {asset?.ip_address || "-"}</div>
            <div>Purdue Level: {asset?.purdue_level ?? "-"}</div>
            <div>Status: {asset?.status || "-"}</div>
            <div>Vendor: {asset?.vendor || "-"}</div>
            <div>Model: {asset?.model || "-"}</div>
          </CardContent>
        </Card>

        <div className="xl:col-span-2 space-y-4">
          <Card>
            <CardHeader><CardTitle>Live Data Points</CardTitle></CardHeader>
            <CardContent className="grid gap-3 md:grid-cols-2">
              {datapoints.length === 0 ? (
                <div className="text-sm text-gray-300">No live datapoints available for this asset.</div>
              ) : (
                datapoints.map((dp) => (
                  <div key={dp.id} className="rounded border border-ot-border p-3">
                    <div className="font-mono text-xs text-ot-blue">{dp.tag}</div>
                    <div className="text-sm">{dp.name}</div>
                    <div className="font-mono text-lg">
                      {formatValue(dp.latest_value)} {dp.unit || ""}
                    </div>
                    <div className="text-xs text-gray-300">Last updated: {formatDate(dp.last_updated)}</div>
                    <div className="mt-2 h-16">
                      <ResponsiveContainer width="100%" height="100%">
                        <LineChart data={spark}>
                          <Line type="monotone" dataKey={dp.tag} stroke="#00A8E8" dot={false} />
                        </LineChart>
                      </ResponsiveContainer>
                    </div>
                  </div>
                ))
              )}
            </CardContent>
          </Card>
        </div>
      </div>

      <Card>
        <CardHeader><CardTitle>Related Alerts</CardTitle></CardHeader>
        <CardContent>
          <Table>
            <THead>
              <TR>
                <TH>Severity</TH>
                <TH>Title</TH>
                <TH>Status</TH>
                <TH>Triggered</TH>
              </TR>
            </THead>
            <TBody>
              {alerts.map((a) => (
                <TR key={a.id}>
                  <TD><SeverityBadge severity={a.severity} /></TD>
                  <TD>{a.title}</TD>
                  <TD>{a.status}</TD>
                  <TD>{formatDate(a.triggered_at)}</TD>
                </TR>
              ))}
            </TBody>
          </Table>
        </CardContent>
      </Card>

      <Dialog open={editOpen} onOpenChange={setEditOpen} title="Edit Asset">
        <div className="space-y-3">
          <Input value={asset?.name || ""} readOnly />
          <Input value={asset?.tag || ""} readOnly />
          <Button className="w-full" onClick={() => setEditOpen(false)}>Close</Button>
        </div>
      </Dialog>
    </div>
  );
}
