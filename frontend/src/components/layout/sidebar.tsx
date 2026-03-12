// =============================================================================
// src/components/layout/sidebar.tsx — Left Sidebar Navigation
// =============================================================================

"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import {
  LayoutDashboard,
  Radio,
  PieChart,
  ShieldAlert,
  Radar,
  FlaskConical,
  MessageSquare,
  BellRing,
  Trophy,
  Globe,
  BookOpen,
  Settings,
  ChevronsLeft,
  ChevronsRight,
  LogOut,
  User,
} from "lucide-react";
import { cn } from "@/lib/utils";
import { Separator } from "@/components/ui/separator";
import { useAuth } from "@/hooks/use-auth";

const NAV_ITEMS = [
  { label: "Dashboard", icon: LayoutDashboard, path: "/" },
  { label: "Signals", icon: Radio, path: "/signals" },
  { label: "Portfolio", icon: PieChart, path: "/portfolio" },
  { label: "Risk Guardian", icon: ShieldAlert, path: "/risk" },
  { label: "Opportunity Radar", icon: Radar, path: "/radar" },
  { label: "Strategy Lab", icon: FlaskConical, path: "/strategy-lab" },
  { label: "AI Chat", icon: MessageSquare, path: "/chat" },
  { label: "Markets", icon: Globe, path: "/markets" },
  { label: "Trade Journal", icon: BookOpen, path: "/journal" },
  { label: "Price Alerts", icon: BellRing, path: "/alerts" },
  { label: "Leaderboard", icon: Trophy, path: "/leaderboard" },
  { label: "Settings", icon: Settings, path: "/settings" },
] as const;

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

  // On mobile: hidden by default, slides in when open
  if (mobile && !mobileOpen) return null;

  return (
    <aside
      className={cn(
        "fixed left-0 top-0 z-40 flex h-screen flex-col border-r border-border/50 bg-card/95 backdrop-blur-md transition-all duration-200",
        mobile ? "w-60" : collapsed ? "w-16" : "w-60"
      )}
    >
      {/* Logo */}
      <div className="flex h-14 items-center gap-3 px-4">
        <div className="flex h-8 w-8 shrink-0 items-center justify-center rounded-lg bg-blue-600 font-bold text-white text-sm">
          J
        </div>
        {!collapsed && (
          <div className="overflow-hidden">
            <div className="text-sm font-bold text-white truncate">
              JARVIS Trader
            </div>
            <div className="text-[10px] text-muted-foreground">v7.1</div>
          </div>
        )}
      </div>

      <Separator className="opacity-50" />

      {/* Navigation */}
      <nav className="flex-1 space-y-1 px-2 py-4">
        {NAV_ITEMS.map((item) => {
          const isActive = pathname === item.path;
          const Icon = item.icon;
          return (
            <Link
              key={item.path}
              href={item.path}
              className={cn(
                "flex items-center gap-3 rounded-lg px-3 py-2.5 text-sm transition-colors",
                isActive
                  ? "bg-blue-600/20 text-blue-400"
                  : "text-muted-foreground hover:bg-muted hover:text-foreground"
              )}
            >
              <Icon className="h-5 w-5 shrink-0" />
              {!collapsed && (
                <span className="truncate">{item.label}</span>
              )}
            </Link>
          );
        })}
      </nav>

      <Separator className="opacity-50" />

      {/* User section */}
      {user && (
        <div className="px-3 py-2">
          <div className="flex items-center gap-2 rounded-lg px-2 py-2">
            <div className="flex h-7 w-7 shrink-0 items-center justify-center rounded-full bg-blue-600/20 text-blue-400">
              <User className="h-3.5 w-3.5" />
            </div>
            {!collapsed && (
              <div className="min-w-0 flex-1">
                <div className="truncate text-xs font-medium text-white">
                  {user.email}
                </div>
              </div>
            )}
          </div>
          <button
            onClick={signOut}
            className={cn(
              "flex w-full items-center gap-3 rounded-lg px-3 py-2 text-sm text-muted-foreground hover:bg-red-500/10 hover:text-red-400 transition-colors",
            )}
          >
            <LogOut className="h-4 w-4 shrink-0" />
            {!collapsed && <span>Sign Out</span>}
          </button>
        </div>
      )}

      <Separator className="opacity-50" />

      {/* Bottom section */}
      <div className="flex items-center justify-between px-4 py-3">
        {/* Connection indicator */}
        <div className="flex items-center gap-2">
          <div
            className={cn(
              "h-2 w-2 rounded-full",
              connected ? "bg-green-500" : "bg-red-500"
            )}
          />
          {!collapsed && (
            <span className="text-[10px] text-muted-foreground">
              {connected ? "API Connected" : "Offline"}
            </span>
          )}
        </div>

        {/* Collapse toggle */}
        <button
          onClick={onToggle}
          className="rounded-md p-1 text-muted-foreground hover:bg-muted hover:text-foreground transition-colors"
        >
          {collapsed ? (
            <ChevronsRight className="h-4 w-4" />
          ) : (
            <ChevronsLeft className="h-4 w-4" />
          )}
        </button>
      </div>
    </aside>
  );
}
