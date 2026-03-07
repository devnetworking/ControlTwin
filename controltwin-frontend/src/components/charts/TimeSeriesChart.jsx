import { useMemo, useState } from "react";
import {
  CartesianGrid,
  Legend,
  Line,
  LineChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis
} from "recharts";
import { format } from "date-fns";
import { Button } from "../ui/button";
import EmptyState from "../ui/EmptyState";
import LoadingSpinner from "../ui/LoadingSpinner";

const RANGES = ["1h", "6h", "24h", "7d"];
const COLORS = ["#00A8E8", "#2ECC71", "#F4A020", "#E74C3C", "#A78BFA", "#22D3EE"];

export default function TimeSeriesChart({ data = [], loading = false, onRangeChange, tags = [] }) {
  const [range, setRange] = useState("6h");

  const lines = useMemo(() => {
    if (tags?.length) return tags;
    if (!data.length) return [];
    return Object.keys(data[0]).filter((k) => k !== "name");
  }, [data, tags]);

  if (loading) return <LoadingSpinner label="Loading timeseries..." />;
  if (!data.length) return <EmptyState title="No data" description="No sensor data available for selected range." />;

  return (
    <div className="rounded-lg border border-ot-border bg-ot-card p-4">
      <div className="mb-3 flex items-center justify-between">
        <h3 className="text-sm font-semibold">Sensor Time Series</h3>
        <div className="flex gap-2">
          {RANGES.map((r) => (
            <Button
              key={r}
              size="sm"
              variant={range === r ? "default" : "outline"}
              onClick={() => {
                setRange(r);
                onRangeChange?.(r);
              }}
            >
              {r.toUpperCase()}
            </Button>
          ))}
        </div>
      </div>

      <div className="h-72">
        <ResponsiveContainer width="100%" height="100%">
          <LineChart data={data}>
            <CartesianGrid stroke="#1B3A6B" strokeDasharray="3 3" />
            <XAxis
              dataKey="name"
              stroke="#94A3B8"
              tickFormatter={(v) => {
                const d = new Date(v);
                return range === "7d" || range === "24h" ? format(d, "MM/dd HH:mm") : format(d, "HH:mm");
              }}
            />
            <YAxis stroke="#94A3B8" domain={["auto", "auto"]} />
            <Tooltip
              contentStyle={{ background: "#0F1F3D", border: "1px solid #1B3A6B" }}
              labelFormatter={(v) => format(new Date(v), "yyyy-MM-dd HH:mm:ss")}
            />
            <Legend />
            {lines.map((key, idx) => (
              <Line key={key} type="monotone" dataKey={key} stroke={COLORS[idx % COLORS.length]} dot={false} />
            ))}
          </LineChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
}
