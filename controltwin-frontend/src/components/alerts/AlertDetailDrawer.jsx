import { useState } from "react";
import { Sheet } from "../ui/sheet";
import { Button } from "../ui/button";
import { Input } from "../ui/input";
import SeverityBadge from "../ui/SeverityBadge";
import { MITRE_ICS_TECHNIQUES } from "../../constants/ics";

export default function AlertDetailDrawer({ alert, open, onClose, onAcknowledge, onResolve }) {
  const [ackComment, setAckComment] = useState("");
  const [resolution, setResolution] = useState("");
  const [falsePositive, setFalsePositive] = useState(false);

  if (!alert) return null;

  const technique = MITRE_ICS_TECHNIQUES.find((t) => t.id === alert.technique_id);

  return (
    <Sheet open={open} onOpenChange={onClose} title="Alert Details">
      <div className="space-y-4">
        <div>
          <h4 className="text-lg font-semibold">{alert.title}</h4>
          <p className="text-sm text-gray-300">{alert.description || "No description"}</p>
        </div>

        <div className="space-y-1 text-sm">
          <div>
            Severity: <SeverityBadge severity={alert.severity} />
          </div>
          <div>Status: {alert.status}</div>
          <div>Category: {alert.category || "-"}</div>
          <div>Asset: {alert.asset_name || alert.asset?.name || "-"}</div>
        </div>

        {technique ? (
          <div className="rounded border border-ot-border bg-[#081328] p-3 text-sm">
            <div className="font-semibold">MITRE ATT&CK for ICS</div>
            <div className="mt-1">
              {technique.id} — {technique.name}
            </div>
            <a
              className="text-ot-blue underline"
              href={`https://attack.mitre.org/techniques/ics/${technique.id}`}
              target="_blank"
              rel="noreferrer"
            >
              View Technique
            </a>
          </div>
        ) : null}

        <div className="space-y-2 rounded border border-ot-border p-3">
          <div className="font-semibold">Acknowledge</div>
          <Input
            placeholder="Comment"
            value={ackComment}
            onChange={(e) => setAckComment(e.target.value)}
          />
          <Button
            className="w-full"
            onClick={() => {
              onAcknowledge?.(alert.id, ackComment);
              setAckComment("");
            }}
          >
            Submit Acknowledge
          </Button>
        </div>

        <div className="space-y-2 rounded border border-ot-border p-3">
          <div className="font-semibold">Resolve</div>
          <Input
            placeholder="Resolution note"
            value={resolution}
            onChange={(e) => setResolution(e.target.value)}
          />
          <label className="flex items-center gap-2 text-sm">
            <input
              type="checkbox"
              checked={falsePositive}
              onChange={(e) => setFalsePositive(e.target.checked)}
            />
            Mark as false positive
          </label>
          <Button
            className="w-full"
            onClick={() => {
              onResolve?.(alert.id, { resolution_note: resolution, false_positive: falsePositive });
              setResolution("");
              setFalsePositive(false);
            }}
          >
            Resolve Alert
          </Button>
        </div>
      </div>
    </Sheet>
  );
}
