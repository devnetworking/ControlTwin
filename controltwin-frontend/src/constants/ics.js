export const ASSET_TYPES = [
  { value: "plc", label: "PLC", icon: "Cpu", color: "#00A8E8" },
  { value: "rtu", label: "RTU", icon: "Radio", color: "#A78BFA" },
  { value: "hmi", label: "HMI", icon: "Monitor", color: "#22D3EE" },
  { value: "sensor", label: "Sensor", icon: "Activity", color: "#2ECC71" },
  { value: "actuator", label: "Actuator", icon: "Settings", color: "#F4A020" },
  { value: "scada_server", label: "SCADA Server", icon: "Server", color: "#00A8E8" }
];

export const PROTOCOLS = [
  { value: "modbus", label: "Modbus" },
  { value: "opcua", label: "OPC-UA" },
  { value: "dnp3", label: "DNP3" },
  { value: "mqtt", label: "MQTT" }
];

export const PURDUE_LEVELS = {
  0: "Field Devices",
  1: "Control",
  2: "Supervisory",
  3: "Operations",
  4: "Enterprise"
};

export const SEVERITY_LEVELS = {
  critical: { label: "Critical", color: "#E74C3C" },
  high: { label: "High", color: "#F4A020" },
  medium: { label: "Medium", color: "#FACC15" },
  low: { label: "Low", color: "#00A8E8" },
  info: { label: "Info", color: "#6B7280" }
};

export const ALERT_CATEGORIES = [
  "anomaly",
  "intrusion",
  "equipment_failure",
  "network",
  "process_deviation"
];

export const MITRE_ICS_TECHNIQUES = [
  { id: "T0801", name: "Monitor Process State", tactic: "Collection" },
  { id: "T0802", name: "Automated Collection", tactic: "Collection" },
  { id: "T0803", name: "Block Command Message", tactic: "Inhibit Response Function" },
  { id: "T0804", name: "Block Reporting Message", tactic: "Inhibit Response Function" },
  { id: "T0805", name: "Block Serial COM", tactic: "Inhibit Response Function" },
  { id: "T0836", name: "Modify Parameter", tactic: "Impair Process Control" },
  { id: "T0855", name: "Unauthorized Command Message", tactic: "Execution" },
  { id: "T0856", name: "Spoof Reporting Message", tactic: "Impair Process Control" },
  { id: "T0878", name: "Alarm Suppression", tactic: "Impair Process Control" },
  { id: "T0890", name: "Loss of Safety", tactic: "Impact" }
];

export const STATUS_OPTIONS = ["online", "offline", "degraded", "maintenance"];

export const ROLE_LABELS = {
  super_admin: { label: "Super Admin", color: "text-ot-red" },
  admin: { label: "Admin", color: "text-ot-orange" },
  ot_analyst: { label: "OT Analyst", color: "text-ot-blue" },
  ot_operator: { label: "OT Operator", color: "text-cyan-300" },
  viewer: { label: "Viewer", color: "text-gray-300" },
  readonly: { label: "Read Only", color: "text-gray-400" }
};
