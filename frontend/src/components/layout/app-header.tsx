// =============================================================================
// src/components/layout/app-header.tsx — Top header bar with notification bell
// =============================================================================

"use client";

import { useRef, useState, useEffect } from "react";
import { Badge } from "@/components/ui/badge";
import { useNotifications, type NotificationType } from "@/hooks/use-notifications";
import { useLocale } from "@/hooks/use-locale";
import { Bell, Check, Trash2 } from "lucide-react";

interface AppHeaderProps {
  title: string;
  subtitle?: string;
}

const TYPE_COLORS: Record<NotificationType, string> = {
  signal: "bg-blue-500",
  alert: "bg-yellow-500",
  achievement: "bg-purple-500",
  trade: "bg-green-500",
  system: "bg-muted-foreground",
};

export function AppHeader({ title, subtitle }: AppHeaderProps) {
  const { notifications, unreadCount, markAllRead, clearAll } =
    useNotifications();
  const { locale, setLocale, t } = useLocale();
  const [open, setOpen] = useState(false);
  const dropdownRef = useRef<HTMLDivElement>(null);

  // Close on outside click
  useEffect(() => {
    function handleClick(e: MouseEvent) {
      if (
        dropdownRef.current &&
        !dropdownRef.current.contains(e.target as Node)
      ) {
        setOpen(false);
      }
    }
    if (open) {
      document.addEventListener("mousedown", handleClick);
      return () => document.removeEventListener("mousedown", handleClick);
    }
  }, [open]);

  return (
    <header className="flex h-14 items-center justify-between border-b border-border/50 px-6">
      <div className="flex items-center gap-3">
        <h1 className="text-lg font-bold text-white">{title}</h1>
        {subtitle && (
          <span className="text-sm text-muted-foreground">{subtitle}</span>
        )}
      </div>
      <div className="flex items-center gap-3">
        <Badge
          variant="outline"
          className="text-[10px] text-muted-foreground"
        >
          {t('common_paper_trading')}
        </Badge>
        <Badge
          variant="outline"
          className="text-[10px] text-green-400 border-green-400/30"
        >
          {t('common_research_only')}
        </Badge>

        {/* Language toggle */}
        <div className="flex items-center rounded-md border border-border/50 overflow-hidden">
          <button
            onClick={() => setLocale('en')}
            className={`px-2 py-1 text-[10px] font-medium transition-colors ${
              locale === 'en'
                ? 'bg-blue-600/20 text-blue-400'
                : 'text-muted-foreground hover:text-foreground hover:bg-muted'
            }`}
          >
            EN
          </button>
          <div className="w-px h-4 bg-border/50" />
          <button
            onClick={() => setLocale('de')}
            className={`px-2 py-1 text-[10px] font-medium transition-colors ${
              locale === 'de'
                ? 'bg-blue-600/20 text-blue-400'
                : 'text-muted-foreground hover:text-foreground hover:bg-muted'
            }`}
          >
            DE
          </button>
        </div>

        {/* Notification Bell */}
        <div className="relative" ref={dropdownRef}>
          <button
            onClick={() => setOpen((p) => !p)}
            className="relative flex h-8 w-8 items-center justify-center rounded-lg text-muted-foreground hover:text-white hover:bg-muted transition-colors"
          >
            <Bell className="h-4 w-4" />
            {unreadCount > 0 && (
              <span className="absolute -top-0.5 -right-0.5 flex h-4 min-w-4 items-center justify-center rounded-full bg-blue-600 px-1 text-[9px] font-bold text-white">
                {unreadCount > 9 ? "9+" : unreadCount}
              </span>
            )}
          </button>

          {open && (
            <div className="absolute right-0 top-10 z-50 w-80 rounded-lg border border-border/50 bg-card/95 backdrop-blur-md shadow-xl">
              {/* Header */}
              <div className="flex items-center justify-between border-b border-border/30 px-3 py-2">
                <span className="text-xs font-medium text-white">
                  {t('common_notifications')}
                </span>
                <div className="flex items-center gap-1">
                  {unreadCount > 0 && (
                    <button
                      onClick={markAllRead}
                      className="text-[10px] text-muted-foreground hover:text-white transition-colors px-1.5 py-0.5 rounded flex items-center gap-1"
                    >
                      <Check className="h-2.5 w-2.5" />
                      {t('common_read_all')}
                    </button>
                  )}
                  {notifications.length > 0 && (
                    <button
                      onClick={clearAll}
                      className="text-[10px] text-muted-foreground hover:text-red-400 transition-colors px-1.5 py-0.5 rounded flex items-center gap-1"
                    >
                      <Trash2 className="h-2.5 w-2.5" />
                      {t('common_clear')}
                    </button>
                  )}
                </div>
              </div>

              {/* Notification list */}
              <div className="max-h-80 overflow-y-auto">
                {notifications.length === 0 ? (
                  <div className="px-3 py-6 text-center text-xs text-muted-foreground">
                    {t('common_no_notifications')}
                  </div>
                ) : (
                  notifications.slice(0, 20).map((n) => (
                    <div
                      key={n.id}
                      className={`flex items-start gap-2.5 px-3 py-2.5 border-b border-border/20 last:border-0 ${
                        !n.read ? "bg-blue-500/5" : ""
                      }`}
                    >
                      <div
                        className={`mt-1.5 h-2 w-2 rounded-full shrink-0 ${
                          TYPE_COLORS[n.type]
                        }`}
                      />
                      <div className="min-w-0 flex-1">
                        <div className="text-xs font-medium text-white truncate">
                          {n.title}
                        </div>
                        <div className="text-[10px] text-muted-foreground line-clamp-2">
                          {n.message}
                        </div>
                        <div className="text-[9px] text-muted-foreground mt-0.5">
                          {formatTimeAgo(n.timestamp)}
                        </div>
                      </div>
                      {!n.read && (
                        <div className="mt-1.5 h-1.5 w-1.5 rounded-full bg-blue-500 shrink-0" />
                      )}
                    </div>
                  ))
                )}
              </div>
            </div>
          )}
        </div>
      </div>
    </header>
  );
}

function formatTimeAgo(iso: string): string {
  const diff = Date.now() - new Date(iso).getTime();
  const secs = Math.floor(diff / 1000);
  if (secs < 60) return "just now";
  const mins = Math.floor(secs / 60);
  if (mins < 60) return `${mins}m ago`;
  const hours = Math.floor(mins / 60);
  if (hours < 24) return `${hours}h ago`;
  const days = Math.floor(hours / 24);
  return `${days}d ago`;
}
