// =============================================================================
// src/lib/widget-registry.ts — Widget definitions for the dashboard grid
// =============================================================================

import {
  LayoutDashboard,
  Wallet,
  Star,
  Radio,
  Activity,
  Shield,
  BarChart3,
  GraduationCap,
  ShieldAlert,
  Radar,
  CalendarDays,
  type LucideIcon,
} from "lucide-react";

export interface WidgetDefinition {
  id: string;
  label: string;
  icon: LucideIcon;
  defaultSize: { w: number; h: number };
  minSize: { w: number; h: number };
}

export const WIDGET_REGISTRY: WidgetDefinition[] = [
  {
    id: "system-status",
    label: "System Status",
    icon: LayoutDashboard,
    defaultSize: { w: 2, h: 4 },
    minSize: { w: 2, h: 3 },
  },
  {
    id: "portfolio",
    label: "Portfolio",
    icon: Wallet,
    defaultSize: { w: 4, h: 3 },
    minSize: { w: 3, h: 2 },
  },
  {
    id: "watchlist",
    label: "Watchlist",
    icon: Star,
    defaultSize: { w: 4, h: 3 },
    minSize: { w: 2, h: 2 },
  },
  {
    id: "signals",
    label: "Top Signals",
    icon: Radio,
    defaultSize: { w: 2, h: 4 },
    minSize: { w: 2, h: 3 },
  },
  {
    id: "sentiment",
    label: "Market Sentiment",
    icon: Activity,
    defaultSize: { w: 3, h: 3 },
    minSize: { w: 2, h: 2 },
  },
  {
    id: "signal-quality",
    label: "Signal Quality",
    icon: Shield,
    defaultSize: { w: 2, h: 4 },
    minSize: { w: 2, h: 3 },
  },
  {
    id: "activity",
    label: "Activity Feed",
    icon: BarChart3,
    defaultSize: { w: 3, h: 3 },
    minSize: { w: 2, h: 2 },
  },
  {
    id: "learning",
    label: "Lernfortschritt",
    icon: GraduationCap,
    defaultSize: { w: 3, h: 2 },
    minSize: { w: 2, h: 2 },
  },
  {
    id: "risk-control",
    label: "Risk Control",
    icon: ShieldAlert,
    defaultSize: { w: 3, h: 3 },
    minSize: { w: 2, h: 2 },
  },
  {
    id: "radar",
    label: "Chancen-Radar",
    icon: Radar,
    defaultSize: { w: 3, h: 3 },
    minSize: { w: 2, h: 2 },
  },
  {
    id: "calendar",
    label: "Kalender",
    icon: CalendarDays,
    defaultSize: { w: 3, h: 3 },
    minSize: { w: 2, h: 2 },
  },
];

export function getWidgetDef(id: string): WidgetDefinition | undefined {
  return WIDGET_REGISTRY.find((w) => w.id === id);
}
