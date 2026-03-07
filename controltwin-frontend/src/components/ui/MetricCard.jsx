import { TrendingDown, TrendingUp } from "lucide-react";

export function MetricCard({
  title,
  value,
  unit,
  icon,
  iconColor = "text-ot-blue",
  trend,
  loading = false,
  onClick,
}) {
  const isPositiveTrend = trend?.direction === "up";
  const trendClasses = isPositiveTrend
    ? "text-green-400 bg-green-400/10"
    : "text-red-400 bg-red-400/10";
  const TrendIcon = isPositiveTrend ? TrendingUp : TrendingDown;

  return (
    <div
      onClick={onClick}
      className={`rounded-xl border border-[#1B3A6B] bg-[#0F1F3D] p-6 transition-colors ${
        onClick ? "cursor-pointer hover:border-ot-blue" : ""
      }`}
      role={onClick ? "button" : undefined}
      tabIndex={onClick ? 0 : undefined}
      onKeyDown={(e) => {
        if (!onClick) return;
        if (e.key === "Enter" || e.key === " ") {
          e.preventDefault();
          onClick();
        }
      }}
    >
      <div className="mb-4 flex items-start justify-between">
        <div className={`rounded-lg bg-[#1B3A6B] p-2 ${iconColor}`}>{icon}</div>
        {trend ? (
          <div className={`inline-flex items-center gap-1 rounded-md px-2 py-1 text-xs ${trendClasses}`}>
            <TrendIcon className="h-3.5 w-3.5" />
            <span>{Math.abs(trend.value)}%</span>
          </div>
        ) : null}
      </div>

      {loading ? (
        <div className="animate-pulse">
          <div className="mb-2 h-10 w-2/3 rounded bg-gray-700/50" />
          <div className="h-4 w-1/2 rounded bg-gray-700/40" />
        </div>
      ) : (
        <>
          <div className="mb-2 flex items-end gap-2">
            <span className="font-mono text-3xl font-bold text-white">{value}</span>
            {unit ? <span className="text-sm text-gray-400">{unit}</span> : null}
          </div>
          <p className="text-sm text-gray-400">{title}</p>
          {trend?.label ? <p className="mt-1 text-xs text-gray-500">{trend.label}</p> : null}
        </>
      )}
    </div>
  );
}

export default MetricCard;
