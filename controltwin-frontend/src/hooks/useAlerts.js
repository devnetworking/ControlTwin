import { useQuery } from "@tanstack/react-query";
import { getAlerts } from "../api/alerts";
import { useAlertStore } from "../store/alertStore";

export function useAlerts(filters = {}) {
  const setUnreadCount = useAlertStore((s) => s.setUnreadCount);

  return useQuery({
    queryKey: ["alerts", filters],
    queryFn: () => getAlerts(filters),
    staleTime: 10000,
    refetchInterval: 30000,
    select: (data) => {
      const list = data?.items || data || [];
      const unread = list.filter((a) => a.status === "open").length;
      setUnreadCount(unread);
      return list;
    }
  });
}
