"use client";
import { createContext, useCallback, useContext, useState } from "react";

interface Toast {
  id: number;
  text: string;
  tone: "info" | "success" | "error";
}

const ToastContext = createContext<{ push: (text: string, tone?: Toast["tone"]) => void }>({
  push: () => {},
});

export function ToastProvider({ children }: { children: React.ReactNode }) {
  const [toasts, setToasts] = useState<Toast[]>([]);
  const push = useCallback((text: string, tone: Toast["tone"] = "info") => {
    const id = Date.now() + Math.random();
    setToasts((t) => [...t, { id, text, tone }]);
    setTimeout(() => setToasts((t) => t.filter((x) => x.id !== id)), 4500);
  }, []);
  return (
    <ToastContext.Provider value={{ push }}>
      {children}
      <div className="fixed bottom-4 right-4 z-50 flex w-80 flex-col gap-2">
        {toasts.map((t) => (
          <div
            key={t.id}
            role="status"
            className={`card px-4 py-3 text-sm shadow-xl ${
              t.tone === "error"
                ? "border-alert-600/60"
                : t.tone === "success"
                  ? "border-safe-500/60"
                  : ""
            }`}
          >
            {t.text}
          </div>
        ))}
      </div>
    </ToastContext.Provider>
  );
}

export const useToast = () => useContext(ToastContext);
