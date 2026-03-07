import React from "react";
import { cn } from "../../lib/utils";

export function Button({ className, variant = "default", size = "default", ...props }) {
  const variants = {
    default: "bg-ot-blue text-white hover:opacity-90",
    outline: "border border-ot-border bg-transparent text-white hover:bg-ot-card",
    ghost: "bg-transparent hover:bg-ot-card text-white",
    destructive: "bg-ot-red text-white hover:opacity-90"
  };

  const sizes = {
    default: "h-10 px-4 py-2",
    sm: "h-8 px-3 text-sm",
    lg: "h-11 px-6",
    icon: "h-10 w-10"
  };

  return (
    <button
      className={cn(
        "inline-flex items-center justify-center rounded-md font-medium transition disabled:opacity-50",
        variants[variant],
        sizes[size],
        className
      )}
      {...props}
    />
  );
}
