import { useQuery } from "@tanstack/react-query";
import { getCollectors } from "../api/collectors";
import { Table, TBody, TD, TH, THead, TR } from "../components/ui/table";
import { formatDate } from "../lib/utils";
import EmptyState from "../components/ui/EmptyState";
import { useLang } from "../lang";

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
  const { t } = useLang();
  const { data } = useQuery({
    queryKey: ["collectors"],
    queryFn: getCollectors,
    refetchInterval: 15000
  });

  const collectors = data?.items || data || [];

  if (!collectors.length) {
    return <EmptyState title={t("collectors.noCollectors")} description={t("common.noData")} />;
  }

  return (
    <div className="space-y-4">
      <h1 className="text-2xl font-semibold">{t("collectors.title")}</h1>
      <div className="rounded-lg border border-ot-border bg-ot-card">
        <Table>
          <THead>
            <TR>
              <TH>{t("collectors.name")}</TH>
              <TH>{t("collectors.protocol")}</TH>
              <TH>{t("collectors.host")}:{t("collectors.port")}</TH>
              <TH>{t("collectors.lastPoll")}</TH>
              <TH>{t("collectors.status")}</TH>
              <TH>{t("collectors.lastPoll")}</TH>
              <TH>{t("dashboard.totalAssets")}</TH>
              <TH>{t("assets.site")}</TH>
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
