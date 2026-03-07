import { useState } from "react";
import { cn } from "../../lib/utils";

export function DropdownMenu({ trigger, children }) {
  const [open, setOpen] = useState(false);

  return (
    <div className="relative">
      <button onClick={() => setOpen((s) => !s)}>{trigger}</button>
      {open && (
        <div className="absolute right-0 z-40 mt-2 w-48 rounded-md border border-ot-border bg-ot-card p-1 shadow-lg">
          {typeof children === "function" ? children(() => setOpen(false)) : children}
        </div>
      )}
    </div>
  );
}

export function DropdownMenuItem({ className, ...props }) {
  return (
    <button
      className={cn("flex w-full items-center rounded px-3 py-2 text-left text-sm hover:bg-white/10", className)}
      {...props}
    />
  );
}
