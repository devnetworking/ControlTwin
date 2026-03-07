import { cn } from "../../lib/utils";

export function Badge({ className, variant = "default", ...props }) {
  const variants = {
    default: "bg-ot-blue/20 text-ot-blue border border-ot-blue/40",
    critical: "bg-ot-red/20 text-ot-red border border-ot-red/40",
    warning: "bg-ot-orange/20 text-ot-orange border border-ot-orange/40",
    success: "bg-ot-green/20 text-ot-green border border-ot-green/40",
    muted: "bg-gray-600/20 text-gray-300 border border-gray-500/40"
  };

  return (
    <span
      className={cn(
        "inline-flex items-center rounded px-2 py-0.5 text-xs font-medium",
        variants[variant] || variants.default,
        className
      )}
      {...props}
    />
  );
}
