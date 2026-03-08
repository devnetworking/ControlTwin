from typing import Any


class MitreMapper:
    def __init__(self) -> None:
        self.rules = [
            (lambda a, t, c: a == "communication_loss" and t == "plc", {"id": "T0827", "name": "Loss of Control", "tactic": "impact"}),
            (lambda a, t, c: a == "threshold_breach" and t == "actuator" and c.get("sudden"), {"id": "T0855", "name": "Unauthorized Command Message", "tactic": "impair-process-control"}),
            (lambda a, t, c: a == "config_change", {"id": "T0836", "name": "Modify Parameter", "tactic": "impair-process-control"}),
            (lambda a, t, c: a == "replay_pattern", {"id": "T0856", "name": "Spoof Reporting Message", "tactic": "evasion"}),
            (lambda a, t, c: a == "sequential_multi_asset", {"id": "T0878", "name": "Alarm Suppression", "tactic": "inhibit-response-function"}),
            (lambda a, t, c: a == "dos_pattern", {"id": "T0814", "name": "Denial of Service", "tactic": "impact"}),
            (lambda a, t, c: a == "baseline_deviation" and c.get("gradual"), {"id": "T0801", "name": "Monitor Process State", "tactic": "collection"}),
            (lambda a, t, c: a == "bad_quality", {"id": "T0832", "name": "Manipulation of View", "tactic": "impair-process-control"}),
            (lambda a, t, c: a == "controller_task_change", {"id": "T0821", "name": "Modify Controller Tasking", "tactic": "execution"}),
            (lambda a, t, c: a == "network_scan", {"id": "T0841", "name": "Network Identification", "tactic": "discovery"}),
        ]

    def map(self, anomaly_type: str, asset_type: str, context: dict[str, Any] | None = None) -> dict[str, str]:
        context = context or {}
        for pred, mapping in self.rules:
            try:
                if pred(anomaly_type, asset_type, context):
                    return mapping
            except Exception:
                continue
        return {"id": "T0802", "name": "Automated Collection", "tactic": "collection"}
