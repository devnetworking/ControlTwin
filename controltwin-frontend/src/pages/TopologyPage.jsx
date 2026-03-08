import { useQuery } from "@tanstack/react-query";
import ICSTopology from "../components/topology/ICSTopology";
import { getAssets } from "../api/assets";
import { Card, CardContent, CardHeader, CardTitle } from "../components/ui/card";

export default function TopologyPage() {
  const { data } = useQuery({
    queryKey: ["topology-assets"],
    queryFn: () => getAssets({ limit: 500 }),
    refetchInterval: 30000
  });

  const assets = data?.items || data || [];

  return (
    <div className="space-y-4">
      <h1 className="text-2xl font-semibold">ICS Topology</h1>
      <ICSTopology assets={assets} />
      <Card>
        <CardHeader>
          <CardTitle>Legend</CardTitle>
        </CardHeader>
        <CardContent className="grid gap-2 text-sm md:grid-cols-2 lg:grid-cols-3">
          <div>plc: CPU icon, blue border</div>
          <div>rtu: radio icon, purple border</div>
          <div>hmi: monitor icon, cyan border</div>
          <div>sensor: activity icon, green border</div>
          <div>actuator: settings icon, orange border</div>
          <div>scada_server: server icon, blue border</div>
        </CardContent>
      </Card>
    </div>
  );
}
