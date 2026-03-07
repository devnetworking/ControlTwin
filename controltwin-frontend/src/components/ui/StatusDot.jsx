const STATUS_STYLE = {
  online: { color: "#2ECC71", pulseByDefault: true },
  running: { color: "#2ECC71", pulseByDefault: true },
  offline: { color: "#E74C3C", pulseByDefault: false },
  stopped: { color: "#E74C3C", pulseByDefault: false },
  degraded: { color: "#F4A020", pulseByDefault: false },
  error: { color: "#F4A020", pulseByDefault: false },
  maintenance: { color: "#6B7280", pulseByDefault: false },
  connecting: { color: "#06B6D4", pulseByDefault: true },
  unknown: { color: "#6B7280", pulseByDefault: false },
};

const SIZE_CLASSES = {
  sm: "w-2 h-2",
  md: "w-3 h-3",
  lg: "w-4 h-4",
};

export function StatusDot({ status, label = true, size = "md", pulse }) {
  const normalizedStatus = (status || "unknown").toLowerCase();
  const style = STATUS_STYLE[normalizedStatus] || STATUS_STYLE.unknown;
  const shouldPulse = typeof pulse === "boolean" ? pulse : style.pulseByDefault;
  const sizeClass = SIZE_CLASSES[size] || SIZE_CLASSES.md;

  return (
    <span className="flex items-center gap-2">
      <span
        className={`${sizeClass} rounded-full ${shouldPulse ? "animate-pulse" : ""}`}
        style={{ backgroundColor: style.color }}
        aria-hidden="true"
      />
      {label ? (
        <span className="text-sm text-gray-300">
          {normalizedStatus.charAt(0).toUpperCase() + normalizedStatus.slice(1)}
        </span>
      ) : null}
    </span>
  );
}

export default StatusDot;
