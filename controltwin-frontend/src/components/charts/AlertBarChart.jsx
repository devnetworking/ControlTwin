import { Bar, BarChart, CartesianGrid, Legend, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";
import EmptyState from "../ui/EmptyState";

export default function AlertBarChart({ data = [] }) {
  if (!data.length) {
    return <EmptyState title="No alerts trend" description="No alert activity for selected period." />;
  }

  return (
    <div className="rounded-lg border border-ot-border bg-ot-card p-4">
      <h3 className="mb-3 text-sm font-semibold">Alerts by Severity (7 days)</h3>
      <div className="h-64">
        <ResponsiveContainer width="100%" height="100%">
          <BarChart data={data}>
            <CartesianGrid stroke="#1B3A6B" strokeDasharray="3 3" />
            <XAxis dataKey="date" stroke="#94A3B8" />
            <YAxis stroke="#94A3B8" />
            <Tooltip contentStyle={{ background: "#0F1F3D", border: "1px solid #1B3A6B" }} />
            <Legend />
            <Bar dataKey="critical" stackId="a" fill="#E74C3C" />
            <Bar dataKey="high" stackId="a" fill="#F4A020" />
            <Bar dataKey="medium" stackId="a" fill="#EAB308" />
            <Bar dataKey="low" stackId="a" fill="#00A8E8" />
            <Bar dataKey="info" stackId="a" fill="#6B7280" />
          </BarChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
}
