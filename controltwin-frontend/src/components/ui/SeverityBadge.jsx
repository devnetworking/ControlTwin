const SEVERITY_STYLES = {
  critical: "bg-red-500/20 text-red-400 border-red-500/30",
  high: "bg-orange-500/20 text-orange-400 border-orange-500/30",
  medium: "bg-yellow-500/20 text-yellow-400 border-yellow-500/30",
  low: "bg-blue-500/20 text-blue-400 border-blue-500/30",
  info: "bg-gray-500/20 text-gray-400 border-gray-500/30",
};

const SIZE_STYLES = {
  sm: "text-xs px-2 py-0.5",
  md: "text-sm px-2.5 py-1",
};

export function SeverityBadge({ severity, size = "md", dot = true }) {
  const normalized = (severity || "info").toLowerCase();
  const style = SEVERITY_STYLES[normalized] || SEVERITY_STYLES.info;
  const sizeStyle = SIZE_STYLES[size] || SIZE_STYLES.md;
  const label = normalized.charAt(0).toUpperCase() + normalized.slice(1);

  return (
    <span className={`inline-flex items-center gap-1.5 rounded-full border font-medium ${style} ${sizeStyle}`}>
      {dot ? <span className="h-1.5 w-1.5 rounded-full bg-current" aria-hidden="true" /> : null}
      <span>{label}</span>
    </span>
  );
}

export default SeverityBadge;
