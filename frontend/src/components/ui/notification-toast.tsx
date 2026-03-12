// =============================================================================
// src/components/ui/notification-toast.tsx — Push-style notification toasts
// =============================================================================

"use client";

import { useEffect, useRef, useState } from "react";
import { X } from "lucide-react";
import { useNotifications, type AppNotification, type NotificationType } from "@/hooks/use-notifications";
import { cn } from "@/lib/utils";

const MAX_VISIBLE = 3;
const AUTO_DISMISS_MS = 5000;

const TYPE_COLORS: Record<NotificationType, string> = {
  signal: "border-blue-500/40 bg-blue-500/5",
  alert: "border-yellow-500/40 bg-yellow-500/5",
  achievement: "border-purple-500/40 bg-purple-500/5",
  trade: "border-green-500/40 bg-green-500/5",
  system: "border-border/50 bg-muted/5",
};

const TYPE_DOT: Record<NotificationType, string> = {
  signal: "bg-blue-500",
  alert: "bg-yellow-500",
  achievement: "bg-purple-500",
  trade: "bg-green-500",
  system: "bg-muted-foreground",
};

interface VisibleToast {
  notification: AppNotification;
  expiresAt: number;
}

export function NotificationToastContainer() {
  const { notifications, lastPushedAt } = useNotifications();
  const [visibleToasts, setVisibleToasts] = useState<VisibleToast[]>([]);
  const shownIdsRef = useRef<Set<string>>(new Set());
  const mountedAtRef = useRef(Date.now());

  // Detect new notifications and add them as visible toasts
  useEffect(() => {
    if (lastPushedAt === 0) return;
    // Don't show toasts for notifications that existed before mount
    if (lastPushedAt < mountedAtRef.current) return;

    const latest = notifications[0];
    if (!latest || shownIdsRef.current.has(latest.id)) return;

    shownIdsRef.current.add(latest.id);

    setVisibleToasts((prev) => {
      const next: VisibleToast[] = [
        { notification: latest, expiresAt: Date.now() + AUTO_DISMISS_MS },
        ...prev,
      ];
      // Keep only MAX_VISIBLE
      return next.slice(0, MAX_VISIBLE);
    });
  }, [lastPushedAt, notifications]);

  // Auto-dismiss timer
  useEffect(() => {
    if (visibleToasts.length === 0) return;

    const soonest = Math.min(...visibleToasts.map((t) => t.expiresAt));
    const delay = Math.max(soonest - Date.now(), 100);

    const timer = setTimeout(() => {
      const now = Date.now();
      setVisibleToasts((prev) => prev.filter((t) => t.expiresAt > now));
    }, delay);

    return () => clearTimeout(timer);
  }, [visibleToasts]);

  const dismiss = (id: string) => {
    setVisibleToasts((prev) => prev.filter((t) => t.notification.id !== id));
  };

  if (visibleToasts.length === 0) return null;

  return (
    <div className="fixed top-16 right-4 z-40 flex flex-col gap-2 w-80 pointer-events-none">
      {visibleToasts.map((toast) => (
        <div
          key={toast.notification.id}
          className={cn(
            "pointer-events-auto flex items-start gap-2.5 rounded-lg border px-3 py-2.5 shadow-lg backdrop-blur-sm animate-in slide-in-from-right-5 fade-in duration-300",
            TYPE_COLORS[toast.notification.type]
          )}
        >
          <div
            className={cn(
              "mt-1.5 h-2 w-2 rounded-full shrink-0",
              TYPE_DOT[toast.notification.type]
            )}
          />
          <div className="min-w-0 flex-1">
            <div className="text-xs font-medium text-white truncate">
              {toast.notification.title}
            </div>
            <div className="text-[10px] text-muted-foreground line-clamp-2">
              {toast.notification.message}
            </div>
          </div>
          <button
            onClick={() => dismiss(toast.notification.id)}
            className="shrink-0 text-muted-foreground hover:text-white transition-colors mt-0.5"
          >
            <X className="h-3 w-3" />
          </button>
        </div>
      ))}
    </div>
  );
}
