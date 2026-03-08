import { cn } from "../../lib/utils";

export function Input({ className, ...props }) {
  return (
    <input
      className={cn(
        "h-10 w-full rounded-md border border-ot-border bg-[#0B1B36] px-3 text-sm text-white placeholder:text-gray-400 focus:outline-none focus:ring-2 focus:ring-ot-blue",
        className
      )}
      {...props}
    />
  );
}
