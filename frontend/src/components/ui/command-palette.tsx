// =============================================================================
// src/components/ui/command-palette.tsx — Command Palette (Cmd+K / Ctrl+K)
// =============================================================================

"use client";

import { useEffect, useRef, useState, useCallback, useMemo } from "react";
import {
  Search,
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
  Trophy,
  Users,
  Settings,
  Moon,
  Download,
  Keyboard,
  Bitcoin,
  TrendingUp,
  type LucideIcon,
} from "lucide-react";
import { cn } from "@/lib/utils";

// ---------------------------------------------------------------------------
// Types
// ---------------------------------------------------------------------------

interface CommandPaletteProps {
  open: boolean;
  onClose: () => void;
  onNavigate: (path: string) => void;
  onAction: (action: string) => void;
}

interface CommandItem {
  id: string;
  label: string;
  group: "Navigation" | "Actions" | "Assets";
  icon: LucideIcon;
  shortcut?: string;
  onSelect: () => void;
}

// ---------------------------------------------------------------------------
// Data
// ---------------------------------------------------------------------------

function buildItems(
  onNavigate: (path: string) => void,
  onAction: (action: string) => void
): CommandItem[] {
  return [
    // ── Navigation ──────────────────────────────────────────────────────
    { id: "nav-dashboard",      label: "Dashboard",          group: "Navigation", icon: LayoutDashboard,  shortcut: "G D", onSelect: () => onNavigate("/") },
    { id: "nav-charts",         label: "Charts",             group: "Navigation", icon: CandlestickChart, shortcut: "G C", onSelect: () => onNavigate("/charts") },
    { id: "nav-signals",        label: "Signals",            group: "Navigation", icon: Radio,            shortcut: "G S", onSelect: () => onNavigate("/signals") },
    { id: "nav-portfolio",      label: "Portfolio",          group: "Navigation", icon: PieChart,         shortcut: "G P", onSelect: () => onNavigate("/portfolio") },
    { id: "nav-risk",           label: "Risk Guardian",      group: "Navigation", icon: ShieldAlert,      shortcut: "G R", onSelect: () => onNavigate("/risk") },
    { id: "nav-radar",          label: "Opportunity Radar",  group: "Navigation", icon: Radar,                             onSelect: () => onNavigate("/radar") },
    { id: "nav-strategy-lab",   label: "Strategy Lab",       group: "Navigation", icon: FlaskConical,                      onSelect: () => onNavigate("/strategy-lab") },
    { id: "nav-chat",           label: "AI Chat",            group: "Navigation", icon: MessageSquare,                     onSelect: () => onNavigate("/chat") },
    { id: "nav-markets",        label: "Markets",            group: "Navigation", icon: Globe,                             onSelect: () => onNavigate("/markets") },
    { id: "nav-journal",        label: "Trade Journal",      group: "Navigation", icon: BookOpen,                          onSelect: () => onNavigate("/journal") },
    { id: "nav-alerts",         label: "Price Alerts",       group: "Navigation", icon: BellRing,                          onSelect: () => onNavigate("/alerts") },
    { id: "nav-leaderboard",    label: "Leaderboard",        group: "Navigation", icon: Trophy,                            onSelect: () => onNavigate("/leaderboard") },
    { id: "nav-social",         label: "Social Trading",     group: "Navigation", icon: Users,                             onSelect: () => onNavigate("/social") },
    { id: "nav-settings",       label: "Settings",           group: "Navigation", icon: Settings,                          onSelect: () => onNavigate("/settings") },

    // ── Actions ─────────────────────────────────────────────────────────
    { id: "action-dark-mode",   label: "Toggle Dark Mode",       group: "Actions", icon: Moon,     onSelect: () => onAction("toggle-dark-mode") },
    { id: "action-export-csv",  label: "Export Trades CSV",      group: "Actions", icon: Download, onSelect: () => onAction("export-trades-csv") },
    { id: "action-shortcuts",   label: "Show Keyboard Shortcuts", group: "Actions", icon: Keyboard, shortcut: "?", onSelect: () => onAction("show-shortcuts") },

    // ── Assets ──────────────────────────────────────────────────────────
    { id: "asset-btc",  label: "BTC — Bitcoin",   group: "Assets", icon: Bitcoin,      onSelect: () => onNavigate("/charts?asset=BTC") },
    { id: "asset-eth",  label: "ETH — Ethereum",  group: "Assets", icon: TrendingUp,   onSelect: () => onNavigate("/charts?asset=ETH") },
    { id: "asset-sol",  label: "SOL — Solana",    group: "Assets", icon: TrendingUp,   onSelect: () => onNavigate("/charts?asset=SOL") },
    { id: "asset-spy",  label: "SPY — S&P 500",   group: "Assets", icon: TrendingUp,   onSelect: () => onNavigate("/charts?asset=SPY") },
    { id: "asset-aapl", label: "AAPL — Apple",    group: "Assets", icon: TrendingUp,   onSelect: () => onNavigate("/charts?asset=AAPL") },
    { id: "asset-nvda", label: "NVDA — NVIDIA",   group: "Assets", icon: TrendingUp,   onSelect: () => onNavigate("/charts?asset=NVDA") },
    { id: "asset-tsla", label: "TSLA — Tesla",    group: "Assets", icon: TrendingUp,   onSelect: () => onNavigate("/charts?asset=TSLA") },
    { id: "asset-gld",  label: "GLD — Gold",      group: "Assets", icon: TrendingUp,   onSelect: () => onNavigate("/charts?asset=GLD") },
  ];
}

// ---------------------------------------------------------------------------
// Helpers
// ---------------------------------------------------------------------------

const GROUP_ORDER: CommandItem["group"][] = ["Navigation", "Actions", "Assets"];

function filterItems(items: CommandItem[], query: string): CommandItem[] {
  if (!query.trim()) return items;
  const lower = query.toLowerCase();
  return items.filter((item) => item.label.toLowerCase().includes(lower));
}

function groupItems(items: CommandItem[]): { group: string; items: CommandItem[] }[] {
  const map = new Map<string, CommandItem[]>();
  for (const item of items) {
    const arr = map.get(item.group) ?? [];
    arr.push(item);
    map.set(item.group, arr);
  }
  return GROUP_ORDER
    .filter((g) => map.has(g))
    .map((g) => ({ group: g, items: map.get(g)! }));
}

// ---------------------------------------------------------------------------
// KeyBadge (reusable keyboard hint)
// ---------------------------------------------------------------------------

function KeyBadge({ children }: { children: React.ReactNode }) {
  return (
    <kbd className="inline-flex items-center rounded border border-border/50 bg-muted/50 px-1.5 py-0.5 text-[10px] font-mono text-muted-foreground">
      {children}
    </kbd>
  );
}

// ---------------------------------------------------------------------------
// Component
// ---------------------------------------------------------------------------

export function CommandPalette({ open, onClose, onNavigate, onAction }: CommandPaletteProps) {
  const [query, setQuery] = useState("");
  const [activeIndex, setActiveIndex] = useState(0);
  const inputRef = useRef<HTMLInputElement>(null);
  const listRef = useRef<HTMLDivElement>(null);
  const backdropRef = useRef<HTMLDivElement>(null);

  // Build all command items (stable across renders while props stay same)
  const allItems = useMemo(() => buildItems(onNavigate, onAction), [onNavigate, onAction]);

  // Filtered + grouped
  const filtered = useMemo(() => filterItems(allItems, query), [allItems, query]);
  const grouped = useMemo(() => groupItems(filtered), [filtered]);

  // Flat list for index-based navigation
  const flatFiltered = useMemo(() => grouped.flatMap((g) => g.items), [grouped]);

  // Reset state when opened
  useEffect(() => {
    if (open) {
      setQuery("");
      setActiveIndex(0);
      // Small delay to let the DOM mount before focusing
      requestAnimationFrame(() => inputRef.current?.focus());
    }
  }, [open]);

  // Clamp active index when results change
  useEffect(() => {
    setActiveIndex((prev) => Math.min(prev, Math.max(flatFiltered.length - 1, 0)));
  }, [flatFiltered.length]);

  // Scroll active item into view
  useEffect(() => {
    if (!listRef.current) return;
    const active = listRef.current.querySelector("[data-active='true']");
    active?.scrollIntoView({ block: "nearest" });
  }, [activeIndex]);

  // Select handler
  const selectItem = useCallback(
    (item: CommandItem) => {
      onClose();
      item.onSelect();
    },
    [onClose]
  );

  // Keyboard handler
  useEffect(() => {
    if (!open) return;

    const handler = (e: KeyboardEvent) => {
      switch (e.key) {
        case "ArrowDown":
          e.preventDefault();
          setActiveIndex((i) => (i + 1) % Math.max(flatFiltered.length, 1));
          break;
        case "ArrowUp":
          e.preventDefault();
          setActiveIndex((i) => (i - 1 + flatFiltered.length) % Math.max(flatFiltered.length, 1));
          break;
        case "Enter":
          e.preventDefault();
          if (flatFiltered[activeIndex]) {
            selectItem(flatFiltered[activeIndex]);
          }
          break;
        case "Escape":
          e.preventDefault();
          onClose();
          break;
      }
    };

    document.addEventListener("keydown", handler);
    return () => document.removeEventListener("keydown", handler);
  }, [open, activeIndex, flatFiltered, onClose, selectItem]);

  if (!open) return null;

  // Compute a running index offset per group for highlighting
  let runningIndex = 0;

  return (
    <div
      ref={backdropRef}
      className="fixed inset-0 z-50 flex items-start justify-center pt-[15vh] bg-black/60 backdrop-blur-sm"
      onClick={(e) => {
        if (e.target === backdropRef.current) onClose();
      }}
    >
      <div className="w-full max-w-lg rounded-xl border border-border/50 bg-card shadow-2xl overflow-hidden">
        {/* ── Search Input ─────────────────────────────────────────────── */}
        <div className="flex items-center gap-3 border-b border-border/40 px-4 py-3">
          <Search className="h-5 w-5 shrink-0 text-muted-foreground" />
          <input
            ref={inputRef}
            type="text"
            placeholder="Type a command or search..."
            value={query}
            onChange={(e) => {
              setQuery(e.target.value);
              setActiveIndex(0);
            }}
            className="flex-1 bg-transparent text-sm text-white placeholder:text-muted-foreground outline-none"
          />
          <kbd className="hidden sm:inline-flex items-center rounded border border-border/50 bg-muted/50 px-1.5 py-0.5 text-[10px] font-mono text-muted-foreground">
            ESC
          </kbd>
        </div>

        {/* ── Results ──────────────────────────────────────────────────── */}
        <div ref={listRef} className="max-h-[360px] overflow-y-auto py-2">
          {flatFiltered.length === 0 && (
            <div className="px-4 py-8 text-center text-sm text-muted-foreground">
              No results found.
            </div>
          )}

          {grouped.map((section) => {
            const startIndex = runningIndex;
            runningIndex += section.items.length;

            return (
              <div key={section.group}>
                {/* Group header */}
                <div className="px-4 pb-1 pt-3 text-[11px] font-medium uppercase tracking-wider text-muted-foreground">
                  {section.group}
                </div>

                {section.items.map((item, i) => {
                  const globalIndex = startIndex + i;
                  const isActive = globalIndex === activeIndex;
                  const Icon = item.icon;

                  return (
                    <button
                      key={item.id}
                      data-active={isActive}
                      onClick={() => selectItem(item)}
                      onMouseEnter={() => setActiveIndex(globalIndex)}
                      className={cn(
                        "flex w-full items-center gap-3 px-4 py-2 text-sm transition-colors",
                        isActive
                          ? "bg-blue-600/20 text-blue-400"
                          : "text-foreground/80 hover:bg-muted/50"
                      )}
                    >
                      <Icon className="h-4 w-4 shrink-0 text-muted-foreground" />
                      <span className="flex-1 truncate text-left">{item.label}</span>
                      {item.shortcut && (
                        <span className="flex items-center gap-1">
                          {item.shortcut.split(" ").map((k, ki) => (
                            <KeyBadge key={ki}>{k}</KeyBadge>
                          ))}
                        </span>
                      )}
                    </button>
                  );
                })}
              </div>
            );
          })}
        </div>

        {/* ── Footer hint ──────────────────────────────────────────────── */}
        <div className="flex items-center gap-4 border-t border-border/40 px-4 py-2 text-[11px] text-muted-foreground">
          <span className="flex items-center gap-1">
            <KeyBadge>&uarr;</KeyBadge>
            <KeyBadge>&darr;</KeyBadge>
            navigate
          </span>
          <span className="flex items-center gap-1">
            <KeyBadge>&crarr;</KeyBadge>
            select
          </span>
          <span className="flex items-center gap-1">
            <KeyBadge>esc</KeyBadge>
            close
          </span>
        </div>
      </div>
    </div>
  );
}
