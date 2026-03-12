// =============================================================================
// src/components/ui/toast.tsx — Lightweight toast notification system
// =============================================================================

"use client";

import {
  createContext,
  useCallback,
  useContext,
  useState,
  type ReactNode,
} from "react";
import { Check, X, AlertTriangle, Info } from "lucide-react";
import { cn } from "@/lib/utils";

type ToastType = "success" | "error" | "warning" | "info";

interface Toast {
  id: number;
  type: ToastType;
  message: string;
}

interface ToastCtx {
  toast: (type: ToastType, message: string) => void;
}

const Ctx = createContext<ToastCtx>({ toast: () => {} });

export function useToast() {
  return useContext(Ctx);
}

const ICONS: Record<ToastType, ReactNode> = {
  success: <Check className="h-4 w-4 text-green-400" />,
  error: <X className="h-4 w-4 text-red-400" />,
  warning: <AlertTriangle className="h-4 w-4 text-yellow-400" />,
  info: <Info className="h-4 w-4 text-blue-400" />,
};

const BORDER: Record<ToastType, string> = {
  success: "border-green-500/30",
  error: "border-red-500/30",
  warning: "border-yellow-500/30",
  info: "border-blue-500/30",
};

let nextId = 0;

export function ToastProvider({ children }: { children: ReactNode }) {
  const [toasts, setToasts] = useState<Toast[]>([]);

  const toast = useCallback((type: ToastType, message: string) => {
    const id = ++nextId;
    setToasts((prev) => [...prev, { id, type, message }]);
    setTimeout(() => {
      setToasts((prev) => prev.filter((t) => t.id !== id));
    }, 3000);
  }, []);

  const dismiss = useCallback((id: number) => {
    setToasts((prev) => prev.filter((t) => t.id !== id));
  }, []);

  return (
    <Ctx.Provider value={{ toast }}>
      {children}
      {/* Toast container — fixed bottom-right */}
      <div className="fixed bottom-4 right-4 z-50 flex flex-col gap-2 pointer-events-none">
        {toasts.map((t) => (
          <div
            key={t.id}
            className={cn(
              "pointer-events-auto flex items-center gap-3 rounded-lg border bg-card/95 backdrop-blur-sm px-4 py-3 shadow-lg animate-in slide-in-from-right-5 fade-in duration-200",
              BORDER[t.type]
            )}
          >
            {ICONS[t.type]}
            <span className="text-sm text-white">{t.message}</span>
            <button
              onClick={() => dismiss(t.id)}
              className="ml-2 text-muted-foreground hover:text-white transition-colors"
            >
              <X className="h-3 w-3" />
            </button>
          </div>
        ))}
      </div>
    </Ctx.Provider>
  );
}
