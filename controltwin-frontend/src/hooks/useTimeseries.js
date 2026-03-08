import { useQuery } from "@tanstack/react-query";
import { queryTimeseries } from "../api/datapoints";

export function useTimeseries(dpIds = [], range = "6h") {
  return useQuery({
    queryKey: ["timeseries", dpIds, range],
    enabled: dpIds.length > 0,
    refetchInterval: 30000,
    queryFn: () => queryTimeseries({ datapoint_ids: dpIds, range }),
    select: (raw) => {
      const rows = raw?.items || raw?.data || [];
      const grouped = {};
      rows.forEach((row) => {
        const ts = row.timestamp || row.time;
        const tag = row.tag || row.datapoint_tag || row.datapoint?.tag || "value";
        grouped[ts] = grouped[ts] || { name: ts };
        grouped[ts][tag] = Number(row.value);
      });
      return Object.values(grouped);
    }
  });
}
