import { cn } from "../../lib/utils";

export function Select({ className, children, ...props }) {
  return (
    <select
      className={cn(
        "h-10 w-full rounded-md border border-ot-border bg-[#0B1B36] px-3 text-sm text-white focus:outline-none focus:ring-2 focus:ring-ot-blue",
        className
      )}
      {...props}
    >
      {children}
    </select>
  );
}
