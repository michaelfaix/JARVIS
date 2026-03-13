// =============================================================================
// src/components/layout/sidebar.tsx — Collapsible Sidebar (Claude.ai style)
//
// Desktop: 44px collapsed (icons only) ↔ 220px expanded (icons + labels)
// Mobile: 240px slide-in overlay with labels
// Toggle persisted in localStorage via useSidebar hook
// =============================================================================

"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { LogOut, User, PanelLeftClose, PanelLeft } from "lucide-react";
import { cn } from "@/lib/utils";
import { Separator } from "@/components/ui/separator";
import { useAuth } from "@/hooks/use-auth";
import { useLocale } from "@/hooks/use-locale";
import type { TranslationKey } from "@/lib/i18n";

const NAV_ITEMS: { key: TranslationKey; emoji: string; path: string }[] = [
  { key: "nav_dashboard", emoji: "📊", path: "/" },
  { key: "nav_charts", emoji: "📈", path: "/charts" },
  { key: "nav_signals", emoji: "📡", path: "/signals" },
  { key: "nav_portfolio", emoji: "💼", path: "/portfolio" },
  { key: "nav_risk_guardian", emoji: "🛡️", path: "/risk" },
  { key: "nav_opportunity_radar", emoji: "🎯", path: "/radar" },
  { key: "nav_strategy_lab", emoji: "🧪", path: "/strategy-lab" },
  { key: "nav_ai_chat", emoji: "💬", path: "/chat" },
  { key: "nav_markets", emoji: "🌐", path: "/markets" },
  { key: "nav_trade_journal", emoji: "📓", path: "/journal" },
  { key: "nav_price_alerts", emoji: "🔔", path: "/alerts" },
  { key: "nav_calendar", emoji: "📅", path: "/calendar" },
  { key: "nav_leaderboard", emoji: "🏆", path: "/leaderboard" },
  { key: "nav_social_trading", emoji: "👥", path: "/social" },
  { key: "nav_settings", emoji: "⚙️", path: "/settings" },
];

interface SidebarProps {
  collapsed: boolean;
  onToggle: () => void;
  connected: boolean;
  mobile?: boolean;
  mobileOpen?: boolean;
}

export function Sidebar({ collapsed, onToggle, connected, mobile, mobileOpen }: SidebarProps) {
  const pathname = usePathname();
  const { user, signOut } = useAuth();
  const { t } = useLocale();

  if (mobile && !mobileOpen) return null;

  // Mobile: always expanded (overlay). Desktop: respects collapsed prop.
  const isExpanded = mobile ? true : !collapsed;

  return (
    <aside
      className={cn(
        "fixed left-0 top-0 z-40 flex h-screen flex-col border-r overflow-hidden transition-all duration-300 ease-in-out",
        mobile
          ? "w-60 border-border/50 bg-[#060c18]/95 backdrop-blur-md"
          : isExpanded
            ? "w-[220px] border-hud-border bg-[#060c18]"
            : "w-[44px] border-hud-border bg-[#060c18]"
      )}
    >
      {/* Header: Logo + Toggle */}
      <div className="flex h-10 items-center px-2 shrink-0">
        <div className="flex h-7 w-7 shrink-0 items-center justify-center rounded bg-hud-cyan/20 font-bold text-hud-cyan text-xs font-mono">
          J
        </div>
        {isExpanded && (
          <div className="overflow-hidden ml-2 flex-1 min-w-0">
            <div className="text-sm font-bold text-white truncate">JARVIS</div>
          </div>
        )}
        {/* Toggle button (desktop only) */}
        {!mobile && (
          <button
            onClick={onToggle}
            className={cn(
              "flex items-center justify-center h-6 w-6 rounded text-muted-foreground hover:text-hud-cyan hover:bg-hud-cyan/10 transition-colors shrink-0",
              !isExpanded && "mx-auto"
            )}
            title={isExpanded ? "Collapse sidebar" : "Expand sidebar"}
          >
            {isExpanded ? (
              <PanelLeftClose className="h-3.5 w-3.5" />
            ) : (
              <PanelLeft className="h-3.5 w-3.5" />
            )}
          </button>
        )}
      </div>

      <Separator className="opacity-20 border-hud-border" />

      {/* Navigation */}
      <nav role="navigation" aria-label="Main navigation" className="flex-1 space-y-0.5 px-1 py-2 overflow-y-auto scrollbar-hide">
        {NAV_ITEMS.map((item) => {
          const isActive = pathname === item.path;
          return (
            <Link
              key={item.path}
              href={item.path}
              aria-current={isActive ? "page" : undefined}
              title={!isExpanded ? t(item.key) : undefined}
              className={cn(
                "flex items-center rounded transition-colors relative",
                isExpanded ? "gap-3 px-3 py-1.5" : "justify-center px-0 py-1.5 mx-0.5",
                isActive
                  ? "bg-hud-cyan/10"
                  : "hover:bg-[#0a1528]"
              )}
            >
              {/* Cyan left border for active state */}
              {isActive && (
                <div className="absolute left-0 top-1 bottom-1 w-0.5 rounded-r bg-hud-cyan" />
              )}
              <span className={cn("shrink-0 select-none", isExpanded ? "text-lg" : "text-lg")} role="img" aria-hidden>
                {item.emoji}
              </span>
              {isExpanded && (
                <span
                  className={cn(
                    "truncate text-[13px]",
                    isActive ? "text-hud-cyan font-medium" : "text-muted-foreground"
                  )}
                  suppressHydrationWarning
                >
                  {t(item.key)}
                </span>
              )}
            </Link>
          );
        })}
      </nav>

      <Separator className="opacity-20 border-hud-border" />

      {/* User section (expanded + user logged in) */}
      {user && isExpanded && (
        <div className="px-2 py-2">
          <div className="flex items-center gap-2 rounded px-2 py-1.5">
            <div className="flex h-6 w-6 shrink-0 items-center justify-center rounded-full bg-hud-cyan/20 text-hud-cyan">
              <User className="h-3 w-3" />
            </div>
            <div className="min-w-0 flex-1">
              <div className="truncate text-[11px] font-medium text-white">
                {user.email}
              </div>
            </div>
          </div>
          <button
            onClick={signOut}
            className="flex w-full items-center gap-2 rounded px-3 py-1.5 text-[12px] text-muted-foreground hover:bg-red-500/10 hover:text-red-400 transition-colors"
            suppressHydrationWarning
          >
            <LogOut className="h-3.5 w-3.5 shrink-0" />
            <span suppressHydrationWarning>{t("nav_sign_out")}</span>
          </button>
        </div>
      )}

      {/* Bottom: connection indicator */}
      <div className={cn(
        "flex items-center px-2 py-2 shrink-0",
        isExpanded ? "gap-2 px-3" : "justify-center"
      )}>
        <div className="flex items-center gap-2" title={connected ? "Connected" : "Offline"}>
          <div
            className={cn(
              "h-2 w-2 rounded-full shrink-0",
              connected ? "bg-hud-green animate-pulse-live" : "bg-hud-red"
            )}
          />
          {isExpanded && (
            <span className="text-[10px] text-muted-foreground" suppressHydrationWarning>
              {connected ? t("common_api_connected") : t("common_offline")}
            </span>
          )}
        </div>
      </div>
    </aside>
  );
}
