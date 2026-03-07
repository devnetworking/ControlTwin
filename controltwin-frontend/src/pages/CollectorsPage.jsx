import { useQuery } from "@tanstack/react-query";
import { getCollectors } from "../api/collectors";
import { Table, TBody, TD, TH, THead, TR } from "../components/ui/table";
import { formatDate } from "../lib/utils";
import EmptyState from "../components/ui/EmptyState";

function statusClass(status) {
  switch (status) {
    case "running":
      return "text-ot-green";
    case "stopped":
      return "text-gray-400";
    case "error":
      return "text-ot-red";
    case "connecting":
      return "text-ot-orange";
    default:
      return "text-gray-300";
  }
}

export default function CollectorsPage() {
  const { data } = useQuery({
    queryKey: ["collectors"],
    queryFn: getCollectors,
    refetchInterval: 15000
  });

  const collectors = data?.items || data || [];

  if (!collectors.length) {
    return <EmptyState title="No collectors" description="No collectors are configured for this environment." />;
  }

  return (
    <div className="space-y-4">
      <h1 className="text-2xl font-semibold">Collectors</h1>
      <div className="rounded-lg border border-ot-border bg-ot-card">
        <Table>
          <THead>
            <TR>
              <TH>Name</TH>
              <TH>Protocol</TH>
              <TH>Host:Port</TH>
              <TH>Poll Interval</TH>
              <TH>Status</TH>
              <TH>Last Heartbeat</TH>
              <TH>Points Collected</TH>
              <TH>Site</TH>
            </TR>
          </THead>
          <TBody>
            {collectors.map((c) => (
              <TR key={c.id}>
                <TD>{c.name}</TD>
                <TD>{c.protocol}</TD>
                <TD>{c.host}:{c.port}</TD>
                <TD>{c.poll_interval || "-"}s</TD>
                <TD className={statusClass(c.status)}>{c.status}</TD>
                <TD>{formatDate(c.last_heartbeat)}</TD>
                <TD>{Number(c.points_collected || 0).toLocaleString()}</TD>
                <TD>{c.site_name || "-"}</TD>
              </TR>
            ))}
          </TBody>
        </Table>
      </div>
    </div>
  );
}
