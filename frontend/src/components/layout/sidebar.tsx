// =============================================================================
// src/components/layout/sidebar.tsx — Left Sidebar Navigation (HUD)
//
// Desktop: 44px icon-only with cyan left-border active state
// Mobile: 240px slide-in overlay with labels (existing behavior)
// =============================================================================

"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import {
  LayoutDashboard,
  Radio,
  CandlestickChart,
  PieChart,
  ShieldAlert,
  Radar,
  FlaskConical,
  MessageSquare,
  BellRing,
  Trophy,
  Users,
  Globe,
  BookOpen,
  CalendarDays,
  Settings,
  LogOut,
  User,
} from "lucide-react";
import { cn } from "@/lib/utils";
import { Separator } from "@/components/ui/separator";
import { useAuth } from "@/hooks/use-auth";
import { useLocale } from "@/hooks/use-locale";
import type { TranslationKey } from "@/lib/i18n";

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
  { key: "nav_leaderboard", icon: Trophy, path: "/leaderboard" },
  { key: "nav_social_trading", icon: Users, path: "/social" },
  { key: "nav_settings", icon: Settings, path: "/settings" },
];

interface SidebarProps {
  collapsed: boolean;
  onToggle: () => void;
  connected: boolean;
  mobile?: boolean;
  mobileOpen?: boolean;
}

// eslint-disable-next-line @typescript-eslint/no-unused-vars
export function Sidebar({ collapsed, onToggle, connected, mobile, mobileOpen }: SidebarProps) {
  const pathname = usePathname();
  const { user, signOut } = useAuth();
  const { t } = useLocale();

  // On mobile: hidden by default, slides in when open
  if (mobile && !mobileOpen) return null;

  // Desktop: always icon-only (44px). Mobile overlay: 240px with labels.
  const isIconOnly = !mobile;

  return (
    <aside
      className={cn(
        "fixed left-0 top-0 z-40 flex h-screen flex-col border-r overflow-hidden transition-all duration-200",
        mobile
          ? "w-60 border-border/50 bg-card/95 backdrop-blur-md"
          : "w-[44px] border-hud-border bg-hud-bg/95 backdrop-blur-sm"
      )}
    >
      {/* Logo */}
      <div className="flex h-10 items-center justify-center px-2 shrink-0">
        <div className="flex h-7 w-7 shrink-0 items-center justify-center rounded bg-hud-cyan/20 font-bold text-hud-cyan text-xs font-mono">
          J
        </div>
        {!isIconOnly && (
          <div className="overflow-hidden ml-2">
            <div className="text-sm font-bold text-white truncate">
              JARVIS Trader
            </div>
            <div className="text-[10px] text-muted-foreground">v7.1</div>
          </div>
        )}
      </div>

      <Separator className="opacity-30" />

      {/* Navigation */}
      <nav role="navigation" aria-label="Main navigation" className="flex-1 space-y-0.5 px-1 py-2 overflow-y-auto">
        {NAV_ITEMS.map((item) => {
          const isActive = pathname === item.path;
          const Icon = item.icon;
          return (
            <Link
              key={item.path}
              href={item.path}
              aria-current={isActive ? "page" : undefined}
              title={isIconOnly ? t(item.key) : undefined}
              className={cn(
                "flex items-center gap-3 rounded text-sm transition-colors relative",
                isIconOnly ? "justify-center px-0 py-2 mx-0.5" : "px-3 py-2.5",
                isActive
                  ? isIconOnly
                    ? "text-hud-cyan"
                    : "bg-hud-cyan/10 text-hud-cyan"
                  : "text-muted-foreground hover:text-hud-cyan hover:bg-hud-cyan/5"
              )}
            >
              {/* Cyan left border for active state (desktop) */}
              {isActive && isIconOnly && (
                <div className="absolute left-0 top-1 bottom-1 w-0.5 rounded-r bg-hud-cyan" />
              )}
              <Icon className={cn("shrink-0", isIconOnly ? "h-4 w-4" : "h-5 w-5")} />
              {!isIconOnly && (
                <span className="truncate">{t(item.key)}</span>
              )}
            </Link>
          );
        })}
      </nav>

      <Separator className="opacity-30" />

      {/* User section */}
      {user && !isIconOnly && (
        <div className="px-3 py-2">
          <div className="flex items-center gap-2 rounded-lg px-2 py-2">
            <div className="flex h-7 w-7 shrink-0 items-center justify-center rounded-full bg-hud-cyan/20 text-hud-cyan">
              <User className="h-3.5 w-3.5" />
            </div>
            <div className="min-w-0 flex-1">
              <div className="truncate text-xs font-medium text-white">
                {user.email}
              </div>
            </div>
          </div>
          <button
            onClick={signOut}
            className="flex w-full items-center gap-3 rounded-lg px-3 py-2 text-sm text-muted-foreground hover:bg-red-500/10 hover:text-red-400 transition-colors"
          >
            <LogOut className="h-4 w-4 shrink-0" />
            <span>{t("nav_sign_out")}</span>
          </button>
        </div>
      )}

      {/* Bottom section */}
      <div className={cn(
        "flex items-center px-2 py-2 shrink-0",
        isIconOnly ? "justify-center" : "justify-between px-4 py-3"
      )}>
        {/* Connection indicator */}
        <div className="flex items-center gap-2" title={connected ? "Connected" : "Offline"}>
          <div
            className={cn(
              "h-2 w-2 rounded-full",
              connected ? "bg-hud-green animate-pulse-live" : "bg-hud-red"
            )}
          />
          {!isIconOnly && (
            <span className="text-[10px] text-muted-foreground">
              {connected ? t("common_api_connected") : t("common_offline")}
            </span>
          )}
        </div>

        {/* Settings icon for desktop icon-only */}
        {isIconOnly && (
          <Link
            href="/settings"
            className="hidden"
            aria-hidden
          >
            Settings
          </Link>
        )}
      </div>
    </aside>
  );
}
