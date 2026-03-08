import { create } from "zustand";
import { useEffect } from "react";

const useToastStore = create((set) => ({
  toasts: [],
  push: (toast) => set((s) => ({ toasts: [...s.toasts, { id: Date.now(), ...toast }] })),
  remove: (id) => set((s) => ({ toasts: s.toasts.filter((t) => t.id !== id) }))
}));

export function toast(payload) {
  useToastStore.getState().push(payload);
}

export function Toaster() {
  const toasts = useToastStore((s) => s.toasts);
  const remove = useToastStore((s) => s.remove);

  useEffect(() => {
    const timers = toasts.map((t) => setTimeout(() => remove(t.id), t.duration || 4000));
    return () => timers.forEach(clearTimeout);
  }, [toasts, remove]);

  return (
    <div className="pointer-events-none fixed right-4 top-4 z-[100] space-y-2">
      {toasts.map((t) => (
        <div
          key={t.id}
          className="pointer-events-auto rounded-md border border-ot-border bg-ot-card px-4 py-3 shadow-lg"
        >
          <div className="font-semibold">{t.title || "Notification"}</div>
          {t.description && <div className="text-sm text-gray-300">{t.description}</div>}
        </div>
      ))}
    </div>
  );
}
