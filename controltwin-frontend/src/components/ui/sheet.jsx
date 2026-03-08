import { X } from "lucide-react";
import { Button } from "./button";

export function Sheet({ open, onOpenChange, title, children }) {
  if (!open) return null;

  return (
    <div className="fixed inset-0 z-50 bg-black/60">
      <div className="absolute right-0 top-0 h-full w-full max-w-md border-l border-ot-border bg-ot-card p-4 shadow-2xl">
        <div className="mb-4 flex items-center justify-between">
          <h3 className="text-lg font-semibold">{title}</h3>
          <Button variant="ghost" size="icon" onClick={() => onOpenChange(false)}>
            <X className="h-4 w-4" />
          </Button>
        </div>
        <div className="h-[calc(100%-3rem)] overflow-auto">{children}</div>
      </div>
    </div>
  );
}
