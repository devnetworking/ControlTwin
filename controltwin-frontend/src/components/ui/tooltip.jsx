import { useState } from "react";

export function Tooltip({ text, children }) {
  const [open, setOpen] = useState(false);

  return (
    <span className="relative inline-flex" onMouseEnter={() => setOpen(true)} onMouseLeave={() => setOpen(false)}>
      {children}
      {open && (
        <span className="absolute -top-9 left-1/2 z-50 -translate-x-1/2 rounded bg-black px-2 py-1 text-xs text-white shadow">
          {text}
        </span>
      )}
    </span>
  );
}
