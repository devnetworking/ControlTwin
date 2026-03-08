import { useEffect, useMemo, useState } from "react";
import ReactFlow, { Background, Controls, MiniMap } from "react-flow-renderer";
import dagre from "@dagrejs/dagre";
import { Cpu, Radio, Monitor, Activity, Settings, Server, Box } from "lucide-react";
import StatusDot from "../ui/StatusDot";
import { Button } from "../ui/button";
import { useNavigate } from "react-router-dom";

const nodeW = 190;
const nodeH = 70;

const typeIcon = {
  plc: Cpu,
  rtu: Radio,
  hmi: Monitor,
  sensor: Activity,
  actuator: Settings,
  scada_server: Server,
  default: Box
};

function getLayout(elements) {
  const g = new dagre.graphlib.Graph();
  g.setDefaultEdgeLabel(() => ({}));
  g.setGraph({ rankdir: "BT", ranksep: 100, nodesep: 60 });

  elements.nodes.forEach((n) => g.setNode(n.id, { width: nodeW, height: nodeH }));
  elements.edges.forEach((e) => g.setEdge(e.source, e.target));
  dagre.layout(g);

  return {
    nodes: elements.nodes.map((n) => {
      const p = g.node(n.id);
      return { ...n, position: { x: p.x - nodeW / 2, y: p.y - nodeH / 2 } };
    }),
    edges: elements.edges
  };
}

export default function ICSTopology({ assets = [] }) {
  const navigate = useNavigate();
  const [selected, setSelected] = useState(null);

  const data = useMemo(() => {
    const nodes = assets.map((a) => ({
      id: String(a.id),
      data: a,
      position: { x: 0, y: 0 },
      style: {
        width: nodeW,
        border: "1px solid #1B3A6B",
        background: "#0F1F3D",
        color: "#fff",
        boxShadow:
          a.status === "online"
            ? "0 0 10px #2ECC71"
            : a.status === "offline"
            ? "0 0 8px #E74C3C"
            : a.status === "degraded"
            ? "0 0 8px #F4A020"
            : "none"
      },
      label: `${a.tag} - ${a.name}`
    }));

    const edges = assets
      .filter((a) => a.parent_asset_id)
      .map((a, i) => ({
        id: `e-${i}`,
        source: String(a.parent_asset_id),
        target: String(a.id),
        animated: a.status === "online",
        style: { stroke: a.status === "offline" ? "#6B7280" : "#00A8E8" }
      }));

    return getLayout({ nodes, edges });
  }, [assets]);

  const flowNodes = useMemo(
    () =>
      data.nodes.map((n) => {
        const d = n.data;
        const Icon = typeIcon[d.asset_type] || typeIcon.default;
        return {
          ...n,
          data: {
            label: (
              <div className="text-xs">
                <div className="mb-1 flex items-center gap-1 font-mono text-[10px] text-ot-blue">
                  <Icon className="h-3 w-3" /> {d.tag}
                </div>
                <div className="truncate text-sm">{d.name}</div>
              </div>
            )
          }
        };
      }),
    [data.nodes]
  );

  useEffect(() => {
    if (selected) {
      const found = assets.find((a) => String(a.id) === String(selected.id));
      if (found) setSelected(found);
    }
  }, [assets]);

  return (
    <div className="relative h-[calc(100vh-8rem)] rounded-lg border border-ot-border bg-ot-card">
      <ReactFlow
        nodes={flowNodes}
        edges={data.edges}
        fitView
        onNodeClick={(_, node) => setSelected(node)}
      >
        <MiniMap />
        <Controls />
        <Background color="#1B3A6B" />
      </ReactFlow>

      <div className="absolute bottom-3 left-3 rounded border border-ot-border bg-[#081328]/90 p-3 text-xs">
        <div className="mb-1 font-semibold">Legend</div>
        <div>Green glow: online</div>
        <div>Red glow: offline</div>
        <div>Orange glow: degraded</div>
      </div>

      {selected?.data && (
        <div className="absolute right-0 top-0 h-full w-80 border-l border-ot-border bg-[#081328] p-4">
          <h3 className="mb-2 text-lg font-semibold">{selected.data.name}</h3>
          <p className="mb-2 font-mono text-xs text-ot-blue">{selected.data.tag}</p>
          <div className="space-y-1 text-sm">
            <div>Type: {selected.data.asset_type}</div>
            <div>IP: {selected.data.ip_address || "-"}</div>
            <div>Protocol: {selected.data.protocol || "-"}</div>
            <div>Vendor: {selected.data.vendor || "-"}</div>
            <div>Model: {selected.data.model || "-"}</div>
            <StatusDot status={selected.data.status} />
          </div>
          <Button className="mt-4 w-full" onClick={() => navigate(`/assets/${selected.data.id}`)}>
            View Details
          </Button>
        </div>
      )}
    </div>
  );
}
