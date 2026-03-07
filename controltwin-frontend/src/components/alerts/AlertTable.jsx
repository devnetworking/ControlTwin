import { Eye, Check, ShieldCheck } from "lucide-react";
import { formatDate } from "../../lib/utils";
import SeverityBadge from "../ui/SeverityBadge";
import StatusDot from "../ui/StatusDot";
import { Button } from "../ui/button";
import { Table, TBody, TD, TH, THead, TR } from "../ui/table";
import EmptyState from "../ui/EmptyState";

export default function AlertTable({
  alerts = [],
  selected = [],
  onToggleSelect,
  onOpen,
  onAcknowledge,
  onResolve
}) {
  if (!alerts.length) {
    return <EmptyState title="No alerts found" description="No alerts match your current filters." />;
  }

  return (
    <div className="rounded-lg border border-ot-border bg-ot-card">
      <Table>
        <THead>
          <TR>
            <TH />
            <TH>Severity</TH>
            <TH>Category</TH>
            <TH>Title</TH>
            <TH>Asset</TH>
            <TH>Site</TH>
            <TH>Triggered At</TH>
            <TH>Status</TH>
            <TH>Actions</TH>
          </TR>
        </THead>
        <TBody>
          {alerts.map((a) => (
            <TR key={a.id}>
              <TD>
                <input
                  type="checkbox"
                  checked={selected.includes(a.id)}
                  onChange={() => onToggleSelect?.(a.id)}
                />
              </TD>
              <TD>
                <SeverityBadge severity={a.severity} />
              </TD>
              <TD>{a.category || "-"}</TD>
              <TD className="max-w-[320px] truncate">{a.title}</TD>
              <TD>{a.asset_name || a.asset?.name || "-"}</TD>
              <TD>{a.site_name || a.site?.name || "-"}</TD>
              <TD>{formatDate(a.triggered_at)}</TD>
              <TD>
                <StatusDot status={a.status || "open"} />
              </TD>
              <TD>
                <div className="flex gap-1">
                  <Button size="sm" variant="ghost" onClick={() => onOpen?.(a)}>
                    <Eye className="h-4 w-4" />
                  </Button>
                  <Button size="sm" variant="ghost" onClick={() => onAcknowledge?.(a)}>
                    <Check className="h-4 w-4" />
                  </Button>
                  <Button size="sm" variant="ghost" onClick={() => onResolve?.(a)}>
                    <ShieldCheck className="h-4 w-4" />
                  </Button>
                </div>
              </TD>
            </TR>
          ))}
        </TBody>
      </Table>
    </div>
  );
}
