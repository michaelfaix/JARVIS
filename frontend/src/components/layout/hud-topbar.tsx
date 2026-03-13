// =============================================================================
// src/components/layout/hud-topbar.tsx — Iron Man HUD Top Navigation Bar
//
// Desktop only (hidden md:flex). Mobile keeps existing AppHeader + MobileNav.
// =============================================================================

"use client";

import { useRef, useState, useEffect } from "react";
import Link from "next/link";
import { usePathname } from "next/navigation";
import { useLocale } from "@/hooks/use-locale";
import { useNotifications } from "@/hooks/use-notifications";
import {
  LayoutDashboard,
  CandlestickChart,
  Radio,
  PieChart,
  ShieldAlert,
  Radar,
  FlaskConical,
  MessageSquare,
  Globe,
  BookOpen,
  BellRing,
  CalendarDays,
  Bell,
  Grip,
  Check,
  Trash2,
} from "lucide-react";
import { cn } from "@/lib/utils";
import type { TranslationKey } from "@/lib/i18n";
import type { RegimeState } from "@/lib/types";
import type { NotificationType } from "@/hooks/use-notifications";

const NAV_ITEMS: { key: TranslationKey; icon: typeof LayoutDashboard; path: string }[] = [
  { key: "nav_dashboard", icon: LayoutDashboard, path: "/" },
  { key: "nav_charts", icon: CandlestickChart, path: "/charts" },
  { key: "nav_signals", icon: Radio, path: "/signals" },
  { key: "nav_portfolio", icon: PieChart, path: "/portfolio" },
  { key: "nav_risk_guardian", icon: ShieldAlert, path: "/risk" },
  { key: "nav_opportunity_radar", icon: Radar, path: "/radar" },
  { key: "nav_strategy_lab", icon: FlaskConical, path: "/strategy-lab" },
  { key: "nav_ai_chat", icon: MessageSquare, path: "/chat" },
  { key: "nav_markets", icon: Globe, path: "/markets" },
  { key: "nav_trade_journal", icon: BookOpen, path: "/journal" },
  { key: "nav_price_alerts", icon: BellRing, path: "/alerts" },
  { key: "nav_calendar", icon: CalendarDays, path: "/calendar" },
];

const TYPE_COLORS: Record<NotificationType, string> = {
  signal: "bg-blue-500",
  alert: "bg-yellow-500",
  achievement: "bg-purple-500",
  trade: "bg-green-500",
  system: "bg-muted-foreground",
};

interface HudTopbarProps {
  wsConnected: boolean;
  regime: RegimeState;
  sentimentValue: number;
  apiLatencyMs: number | null;
  onWidgetsClick?: () => void;
}

export function HudTopbar({
  wsConnected,
  regime,
  sentimentValue,
  apiLatencyMs,
  onWidgetsClick,
}: HudTopbarProps) {
  const pathname = usePathname();
  const { locale, setLocale, t } = useLocale();
  const { notifications, unreadCount, markAllRead, clearAll } = useNotifications();
  const [bellOpen, setBellOpen] = useState(false);
  const bellRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    function handleClick(e: MouseEvent) {
      if (bellRef.current && !bellRef.current.contains(e.target as Node)) {
        setBellOpen(false);
      }
    }
    if (bellOpen) {
      document.addEventListener("mousedown", handleClick);
      return () => document.removeEventListener("mousedown", handleClick);
    }
  }, [bellOpen]);

  const isRiskOn = regime === "RISK_ON";

  return (
    <header className="hidden md:flex items-center h-10 border-b border-hud-border bg-hud-bg/95 backdrop-blur-sm px-3 gap-2 shrink-0 z-30">
      {/* Left: Brand */}
      <div className="flex items-center gap-2 shrink-0">
        <span className="font-mono text-xs font-bold text-hud-cyan tracking-wide">
          JARVIS
        </span>
        <span className="font-mono text-[9px] text-hud-cyan/50">/</span>
        <span className="font-mono text-[9px] text-hud-cyan/50">MASP v7.1</span>
      </div>

      {/* Center: Nav tabs */}
      <nav className="flex-1 flex items-center overflow-x-auto scrollbar-hide mx-3 gap-0.5">
        {NAV_ITEMS.map((item) => {
          const isActive = pathname === item.path;
          const Icon = item.icon;
          return (
            <Link
              key={item.path}
              href={item.path}
              className={cn(
                "flex items-center gap-1.5 px-2 py-1 rounded text-[10px] font-mono whitespace-nowrap transition-colors",
                isActive
                  ? "bg-hud-cyan/10 text-hud-cyan border border-hud-cyan/30"
                  : "text-muted-foreground hover:text-hud-cyan hover:bg-hud-cyan/5"
              )}
            >
              <Icon className="h-3 w-3 shrink-0" />
              <span className="hidden lg:inline" suppressHydrationWarning>{t(item.key)}</span>
            </Link>
          );
        })}
      </nav>

      {/* Right: Badges & Controls */}
      <div className="flex items-center gap-1.5 shrink-0">
        {/* Paper Trading badge */}
        <span className="font-mono text-[8px] uppercase tracking-wider text-hud-amber/80 border border-hud-amber/30 rounded px-1.5 py-0.5" suppressHydrationWarning>
          {t("common_paper_trading")}
        </span>

        {/* Research Only badge */}
        <span className="font-mono text-[8px] uppercase tracking-wider text-hud-green/80 border border-hud-green/30 rounded px-1.5 py-0.5" suppressHydrationWarning>
          {t("common_research_only")}
        </span>

        {/* Language toggle */}
        <div className="flex items-center rounded border border-hud-border overflow-hidden">
          <button
            onClick={() => setLocale("en")}
            className={cn(
              "px-1.5 py-0.5 text-[9px] font-mono transition-colors",
              locale === "en"
                ? "bg-hud-cyan/20 text-hud-cyan"
                : "text-muted-foreground hover:text-hud-cyan"
            )}
            suppressHydrationWarning
          >
            EN
          </button>
          <div className="w-px h-3 bg-hud-border" />
          <button
            onClick={() => setLocale("de")}
            className={cn(
              "px-1.5 py-0.5 text-[9px] font-mono transition-colors",
              locale === "de"
                ? "bg-hud-cyan/20 text-hud-cyan"
                : "text-muted-foreground hover:text-hud-cyan"
            )}
            suppressHydrationWarning
          >
            DE
          </button>
        </div>

        {/* Notification Bell */}
        <div className="relative" ref={bellRef}>
          <button
            onClick={() => setBellOpen((p) => !p)}
            className="relative flex h-6 w-6 items-center justify-center rounded text-muted-foreground hover:text-hud-cyan transition-colors"
            suppressHydrationWarning
          >
            <Bell className="h-3.5 w-3.5" />
            <span
              className={cn(
                "absolute -top-0.5 -right-0.5 flex h-3.5 min-w-3.5 items-center justify-center rounded-full bg-hud-red px-0.5 text-[8px] font-bold text-white",
                unreadCount === 0 && "hidden"
              )}
              suppressHydrationWarning
            >
              {unreadCount > 9 ? "9+" : unreadCount}
            </span>
          </button>
          {bellOpen && (
            <div className="absolute right-0 top-8 z-50 w-72 rounded border border-hud-border bg-hud-panel/95 backdrop-blur-md shadow-xl">
              <div className="flex items-center justify-between border-b border-hud-border px-3 py-1.5">
                <span className="text-[10px] font-mono text-hud-cyan uppercase tracking-wider" suppressHydrationWarning>
                  {t("common_notifications")}
                </span>
                <div className="flex items-center gap-1">
                  {unreadCount > 0 && (
                    <button
                      onClick={markAllRead}
                      className="text-[9px] text-muted-foreground hover:text-hud-cyan transition-colors px-1 py-0.5 rounded flex items-center gap-0.5"
                      suppressHydrationWarning
                    >
                      <Check className="h-2.5 w-2.5" />
                      {t("common_read_all")}
                    </button>
                  )}
                  {notifications.length > 0 && (
                    <button
                      onClick={clearAll}
                      className="text-[9px] text-muted-foreground hover:text-hud-red transition-colors px-1 py-0.5 rounded flex items-center gap-0.5"
                      suppressHydrationWarning
                    >
                      <Trash2 className="h-2.5 w-2.5" />
                      {t("common_clear")}
                    </button>
                  )}
                </div>
              </div>
              <div className="max-h-64 overflow-y-auto">
                {notifications.length === 0 ? (
                  <div className="px-3 py-4 text-center text-[10px] text-muted-foreground">
                    {t("common_no_notifications")}
                  </div>
                ) : (
                  notifications.slice(0, 15).map((n) => (
                    <div
                      key={n.id}
                      className={cn(
                        "flex items-start gap-2 px-3 py-2 border-b border-hud-border/30 last:border-0",
                        !n.read && "bg-hud-cyan/5"
                      )}
                    >
                      <div className={cn("mt-1 h-1.5 w-1.5 rounded-full shrink-0", TYPE_COLORS[n.type])} />
                      <div className="min-w-0 flex-1">
                        <div className="text-[10px] font-medium text-white truncate">{n.title}</div>
                        <div className="text-[9px] text-muted-foreground line-clamp-1">{n.message}</div>
                      </div>
                    </div>
                  ))
                )}
              </div>
            </div>
          )}
        </div>

        {/* LIVE badge */}
        <div
          className={cn(
            "flex items-center gap-1 px-1.5 py-0.5 rounded border text-[8px] font-mono uppercase tracking-wider",
            wsConnected
              ? "border-hud-green/40 text-hud-green"
              : "border-hud-red/40 text-hud-red"
          )}
          suppressHydrationWarning
        >
          <div
            className={cn(
              "h-1.5 w-1.5 rounded-full",
              wsConnected ? "bg-hud-green animate-pulse-live" : "bg-hud-red"
            )}
          />
          {wsConnected ? "LIVE" : "OFF"}
        </div>

        {/* Regime */}
        <div
          className={cn(
            "px-1.5 py-0.5 rounded border text-[8px] font-mono uppercase tracking-wider",
            isRiskOn
              ? "border-hud-green/30 text-hud-green"
              : regime === "CRISIS"
                ? "border-hud-red/30 text-hud-red"
                : "border-hud-amber/30 text-hud-amber"
          )}
          suppressHydrationWarning
        >
          {isRiskOn ? "RISK ON" : regime === "CRISIS" ? "CRISIS" : "RISK OFF"}
        </div>

        {/* Fear index */}
        <div className="flex items-center gap-1 text-[9px] font-mono text-muted-foreground" suppressHydrationWarning>
          <span className="text-[8px] text-muted-foreground/60">FEAR</span>
          <span className={cn(
            sentimentValue >= 60 ? "text-hud-green" : sentimentValue >= 40 ? "text-hud-amber" : "text-hud-red"
          )}>
            {sentimentValue}
          </span>
        </div>

        {/* API latency */}
        {apiLatencyMs !== null && (
          <span className="text-[9px] font-mono text-muted-foreground" suppressHydrationWarning>
            {apiLatencyMs}ms
          </span>
        )}

        {/* Widgets button */}
        {onWidgetsClick && (
          <button
            onClick={onWidgetsClick}
            className="flex items-center gap-1 px-1.5 py-0.5 rounded border border-hud-border text-[9px] font-mono text-muted-foreground hover:text-hud-cyan hover:border-hud-cyan/30 transition-colors"
            suppressHydrationWarning
          >
            <Grip className="h-3 w-3" />
            <span className="hidden xl:inline" suppressHydrationWarning>WIDGETS</span>
          </button>
        )}
      </div>
    </header>
  );
}
