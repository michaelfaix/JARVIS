// =============================================================================
// src/app/(app)/calendar/page.tsx — Economic Calendar Page (HUD)
// =============================================================================

"use client";

import { useMemo, useState } from "react";
import { HudPanel } from "@/components/ui/hud-panel";
import { Badge } from "@/components/ui/badge";
import { Calendar, Clock, AlertTriangle, TrendingUp } from "lucide-react";
import { cn } from "@/lib/utils";

// ---------------------------------------------------------------------------
// Types
// ---------------------------------------------------------------------------

interface EconomicEvent {
  id: string;
  date: string;
  time: string;
  title: string;
  country: string;
  impact: "high" | "medium" | "low";
  category: string;
  previous?: string;
  forecast?: string;
  actual?: string;
}

// ---------------------------------------------------------------------------
// Helpers
// ---------------------------------------------------------------------------

const COUNTRY_FLAGS: Record<string, string> = {
  US: "\u{1F1FA}\u{1F1F8}",
  EU: "\u{1F1EA}\u{1F1FA}",
  UK: "\u{1F1EC}\u{1F1E7}",
  JP: "\u{1F1EF}\u{1F1F5}",
  CN: "\u{1F1E8}\u{1F1F3}",
};

const IMPACT_COLORS: Record<string, string> = {
  high: "bg-hud-red",
  medium: "bg-hud-amber",
  low: "bg-hud-green",
};

const IMPACT_TEXT: Record<string, string> = {
  high: "text-hud-red",
  medium: "text-hud-amber",
  low: "text-hud-green",
};

const CATEGORY_STYLES: Record<string, string> = {
  "Interest Rates": "bg-purple-500/15 text-purple-400 border-purple-500/30",
  Employment: "bg-hud-cyan/15 text-hud-cyan border-hud-cyan/30",
  Inflation: "bg-hud-red/15 text-hud-red border-hud-red/30",
  GDP: "bg-hud-green/15 text-hud-green border-hud-green/30",
  Earnings: "bg-hud-amber/15 text-hud-amber border-hud-amber/30",
  "Consumer Data": "bg-hud-cyan/15 text-hud-cyan border-hud-cyan/30",
};

function dayOffset(base: Date, days: number): Date {
  const d = new Date(base);
  d.setDate(d.getDate() + days);
  return d;
}

function toISO(d: Date): string {
  return d.toISOString().slice(0, 10);
}

function formatDayHeader(date: Date, today: Date): string {
  const todayStr = toISO(today);
  const tomorrowStr = toISO(dayOffset(today, 1));
  const yesterdayStr = toISO(dayOffset(today, -1));
  const dateStr = toISO(date);

  if (dateStr === todayStr) return "Today";
  if (dateStr === tomorrowStr) return "Tomorrow";
  if (dateStr === yesterdayStr) return "Yesterday";

  return date.toLocaleDateString("en-US", {
    weekday: "short",
    month: "short",
    day: "numeric",
  });
}

function isPast(event: EconomicEvent, now: Date): boolean {
  const eventDate = new Date(event.date + "T00:00:00");
  const todayDate = new Date(toISO(now) + "T00:00:00");
  return eventDate < todayDate;
}

// ---------------------------------------------------------------------------
// Event generator — creates realistic events anchored to today
// ---------------------------------------------------------------------------

function generateEvents(): EconomicEvent[] {
  const now = new Date();
  const today = new Date(now.getFullYear(), now.getMonth(), now.getDate());

  const dayOfWeek = today.getDay();
  const monday = dayOffset(today, dayOfWeek === 0 ? -6 : 1 - dayOfWeek);

  const events: EconomicEvent[] = [
    { id: "1", date: toISO(monday), time: "10:00 UTC", title: "EU Consumer Confidence", country: "EU", impact: "low", category: "Consumer Data", previous: "-14.5", forecast: "-14.2", actual: "-13.8" },
    { id: "2", date: toISO(dayOffset(monday, 1)), time: "07:00 UTC", title: "UK Unemployment Rate", country: "UK", impact: "medium", category: "Employment", previous: "4.0%", forecast: "4.1%", actual: "4.0%" },
    { id: "3", date: toISO(dayOffset(monday, 1)), time: "13:30 UTC", title: "US CPI (YoY)", country: "US", impact: "high", category: "Inflation", previous: "3.1%", forecast: "2.9%", actual: "3.0%" },
    { id: "4", date: toISO(dayOffset(monday, 1)), time: "21:00 UTC", title: "AAPL Earnings Q1 2026", country: "US", impact: "high", category: "Earnings", previous: "$2.18 EPS", forecast: "$2.36 EPS", actual: "$2.41 EPS" },
    { id: "5", date: toISO(dayOffset(monday, 2)), time: "13:30 UTC", title: "US Core PPI (MoM)", country: "US", impact: "medium", category: "Inflation", previous: "0.0%", forecast: "0.2%", actual: "0.1%" },
    { id: "6", date: toISO(dayOffset(monday, 2)), time: "19:00 UTC", title: "Fed Interest Rate Decision", country: "US", impact: "high", category: "Interest Rates", previous: "4.50%", forecast: "4.50%" },
    { id: "7", date: toISO(dayOffset(monday, 2)), time: "19:30 UTC", title: "FOMC Press Conference", country: "US", impact: "high", category: "Interest Rates" },
    { id: "8", date: toISO(dayOffset(monday, 3)), time: "13:30 UTC", title: "Initial Jobless Claims", country: "US", impact: "medium", category: "Employment", previous: "219K", forecast: "215K" },
    { id: "9", date: toISO(dayOffset(monday, 3)), time: "00:30 UTC", title: "Japan GDP Growth Rate (QoQ)", country: "JP", impact: "medium", category: "GDP", previous: "0.3%", forecast: "0.4%" },
    { id: "10", date: toISO(dayOffset(monday, 3)), time: "21:00 UTC", title: "NVDA Earnings Q4 2026", country: "US", impact: "high", category: "Earnings", previous: "$5.16 EPS", forecast: "$5.78 EPS" },
    { id: "11", date: toISO(dayOffset(monday, 4)), time: "13:30 UTC", title: "US Retail Sales (MoM)", country: "US", impact: "medium", category: "Consumer Data", previous: "0.6%", forecast: "0.3%" },
    { id: "12", date: toISO(dayOffset(monday, 4)), time: "10:00 UTC", title: "Eurozone GDP Growth Rate (QoQ)", country: "EU", impact: "medium", category: "GDP", previous: "0.0%", forecast: "0.1%" },
    { id: "13", date: toISO(dayOffset(monday, 7)), time: "02:00 UTC", title: "China Industrial Production (YoY)", country: "CN", impact: "medium", category: "GDP", previous: "6.8%", forecast: "5.5%" },
    { id: "14", date: toISO(dayOffset(monday, 8)), time: "13:30 UTC", title: "US Non-Farm Payrolls", country: "US", impact: "high", category: "Employment", previous: "256K", forecast: "200K" },
    { id: "15", date: toISO(dayOffset(monday, 8)), time: "13:30 UTC", title: "US Unemployment Rate", country: "US", impact: "high", category: "Employment", previous: "4.1%", forecast: "4.1%" },
    { id: "16", date: toISO(dayOffset(monday, 9)), time: "13:30 UTC", title: "Core PCE Price Index (MoM)", country: "US", impact: "high", category: "Inflation", previous: "0.2%", forecast: "0.3%" },
    { id: "17", date: toISO(dayOffset(monday, 9)), time: "21:00 UTC", title: "TSLA Earnings Q1 2026", country: "US", impact: "high", category: "Earnings", previous: "$0.71 EPS", forecast: "$0.78 EPS" },
    { id: "18", date: toISO(dayOffset(monday, 10)), time: "19:00 UTC", title: "FOMC Meeting Minutes", country: "US", impact: "medium", category: "Interest Rates" },
    { id: "19", date: toISO(dayOffset(monday, 11)), time: "21:00 UTC", title: "GOOG Earnings Q1 2026", country: "US", impact: "high", category: "Earnings", previous: "$2.12 EPS", forecast: "$2.28 EPS" },
  ];

  return events.map((e) => {
    if (isPast(e, now)) {
      return { ...e, actual: e.actual ?? e.forecast };
    }
    // eslint-disable-next-line @typescript-eslint/no-unused-vars
    const { actual, ...rest } = e;
    return rest;
  });
}

// ---------------------------------------------------------------------------
// Countdown helper
// ---------------------------------------------------------------------------

function getNextEventCountdown(events: EconomicEvent[], now: Date): string {
  const todayStr = toISO(now);
  const future = events.filter((e) => e.date >= todayStr).sort((a, b) => {
    if (a.date !== b.date) return a.date.localeCompare(b.date);
    return a.time.localeCompare(b.time);
  });

  if (future.length === 0) return "No upcoming events";

  const next = future[0];
  const timeParts = next.time.match(/(\d+):(\d+)/);
  if (!timeParts) return "Today";

  const eventDate = new Date(next.date + "T00:00:00Z");
  eventDate.setUTCHours(parseInt(timeParts[1]), parseInt(timeParts[2]));

  const diffMs = eventDate.getTime() - now.getTime();
  if (diffMs < 0) return "In progress";

  const hours = Math.floor(diffMs / (1000 * 60 * 60));
  const minutes = Math.floor((diffMs % (1000 * 60 * 60)) / (1000 * 60));

  if (hours > 24) {
    const days = Math.floor(hours / 24);
    return `${days}d ${hours % 24}h`;
  }
  return `${hours}h ${minutes}m`;
}

// ---------------------------------------------------------------------------
// Component
// ---------------------------------------------------------------------------

export default function CalendarPage() {
  const [impactFilter, setImpactFilter] = useState<"all" | "high" | "medium" | "low">("all");
  const [countryFilter, setCountryFilter] = useState<string>("all");

  const allEvents = useMemo(() => generateEvents(), []);
  const now = useMemo(() => new Date(), []);

  const filtered = useMemo(() => {
    return allEvents.filter((e) => {
      if (impactFilter !== "all" && e.impact !== impactFilter) return false;
      if (countryFilter !== "all" && e.country !== countryFilter) return false;
      return true;
    });
  }, [allEvents, impactFilter, countryFilter]);

  const grouped = useMemo(() => {
    const map = new Map<string, EconomicEvent[]>();
    const sorted = [...filtered].sort((a, b) => {
      if (a.date !== b.date) return a.date.localeCompare(b.date);
      return a.time.localeCompare(b.time);
    });
    for (const e of sorted) {
      const existing = map.get(e.date) ?? [];
      existing.push(e);
      map.set(e.date, existing);
    }
    return Array.from(map.entries());
  }, [filtered]);

  const todayStr = toISO(now);
  const endOfWeek = toISO(dayOffset(now, 7 - now.getDay()));
  const thisWeekEvents = allEvents.filter((e) => e.date >= todayStr && e.date <= endOfWeek);
  const highImpactCount = thisWeekEvents.filter((e) => e.impact === "high").length;
  const countdown = getNextEventCountdown(allEvents, now);

  const impactButtons: { label: string; value: typeof impactFilter }[] = [
    { label: "All", value: "all" },
    { label: "High", value: "high" },
    { label: "Medium", value: "medium" },
    { label: "Low", value: "low" },
  ];

  const countryButtons = [
    { label: "All", value: "all" },
    { label: "US", value: "US" },
    { label: "EU", value: "EU" },
    { label: "UK", value: "UK" },
    { label: "JP", value: "JP" },
    { label: "CN", value: "CN" },
  ];

  return (
    <div className="p-2 sm:p-3 md:p-4 space-y-3">
      {/* Summary Stats */}
      <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
        <HudPanel>
          <div className="p-2.5 flex items-center gap-3">
            <div className="flex h-8 w-8 items-center justify-center rounded bg-hud-cyan/10">
              <Calendar className="h-4 w-4 text-hud-cyan" />
            </div>
            <div>
              <div className="text-[9px] font-mono text-muted-foreground/60 uppercase tracking-wider">Events This Week</div>
              <div className="text-lg font-bold font-mono text-white">{thisWeekEvents.length}</div>
            </div>
          </div>
        </HudPanel>
        <HudPanel>
          <div className="p-2.5 flex items-center gap-3">
            <div className="flex h-8 w-8 items-center justify-center rounded bg-hud-red/10">
              <AlertTriangle className="h-4 w-4 text-hud-red" />
            </div>
            <div>
              <div className="text-[9px] font-mono text-muted-foreground/60 uppercase tracking-wider">High Impact</div>
              <div className="text-lg font-bold font-mono text-white">{highImpactCount}</div>
            </div>
          </div>
        </HudPanel>
        <HudPanel>
          <div className="p-2.5 flex items-center gap-3">
            <div className="flex h-8 w-8 items-center justify-center rounded bg-hud-green/10">
              <Clock className="h-4 w-4 text-hud-green" />
            </div>
            <div>
              <div className="text-[9px] font-mono text-muted-foreground/60 uppercase tracking-wider">Next Event</div>
              <div className="text-lg font-bold font-mono text-white">{countdown}</div>
            </div>
          </div>
        </HudPanel>
      </div>

      {/* Filter Bar */}
      <HudPanel title="FILTERS">
        <div className="p-2.5">
          <div className="flex flex-col sm:flex-row gap-3">
            <div className="space-y-1">
              <div className="text-[9px] font-mono text-muted-foreground/60 uppercase tracking-wider">Impact</div>
              <div className="flex gap-1">
                {impactButtons.map((btn) => (
                  <button
                    key={btn.value}
                    onClick={() => setImpactFilter(btn.value)}
                    className={cn(
                      "px-2 py-1 rounded text-[10px] font-mono font-medium transition-colors",
                      impactFilter === btn.value
                        ? "bg-hud-cyan/15 text-hud-cyan border border-hud-cyan/30"
                        : "text-muted-foreground hover:text-hud-cyan hover:bg-hud-cyan/5 border border-transparent"
                    )}
                  >
                    {btn.value !== "all" && (
                      <span className={cn("inline-block h-1.5 w-1.5 rounded-full mr-1", IMPACT_COLORS[btn.value])} />
                    )}
                    {btn.label}
                  </button>
                ))}
              </div>
            </div>

            <div className="space-y-1">
              <div className="text-[9px] font-mono text-muted-foreground/60 uppercase tracking-wider">Country</div>
              <div className="flex gap-1">
                {countryButtons.map((btn) => (
                  <button
                    key={btn.value}
                    onClick={() => setCountryFilter(btn.value)}
                    className={cn(
                      "px-2 py-1 rounded text-[10px] font-mono font-medium transition-colors",
                      countryFilter === btn.value
                        ? "bg-hud-cyan/15 text-hud-cyan border border-hud-cyan/30"
                        : "text-muted-foreground hover:text-hud-cyan hover:bg-hud-cyan/5 border border-transparent"
                    )}
                  >
                    {btn.value !== "all" && <span className="mr-1">{COUNTRY_FLAGS[btn.value]}</span>}
                    {btn.label}
                  </button>
                ))}
              </div>
            </div>
          </div>
        </div>
      </HudPanel>

      {/* Week View — Events grouped by day */}
      {grouped.length === 0 ? (
        <HudPanel>
          <div className="py-8 text-center">
            <Calendar className="h-6 w-6 text-muted-foreground mx-auto mb-2" />
            <div className="text-[10px] font-mono text-muted-foreground">No events match your filters.</div>
          </div>
        </HudPanel>
      ) : (
        grouped.map(([dateStr, events]) => {
          const date = new Date(dateStr + "T00:00:00");
          const isToday = dateStr === todayStr;

          return (
            <HudPanel
              key={dateStr}
              title={formatDayHeader(date, now).toUpperCase()}
              className={cn(isToday && "border-hud-cyan/30")}
            >
              <div className="p-2.5">
                <div className="flex items-center gap-2 mb-2">
                  {isToday && (
                    <Badge className="bg-hud-cyan/15 text-hud-cyan border-hud-cyan/30 text-[9px]">Today</Badge>
                  )}
                  <span className="ml-auto text-[9px] font-mono text-muted-foreground">
                    {events.length} event{events.length !== 1 ? "s" : ""}
                  </span>
                </div>
                <div className="space-y-1.5">
                  {events.map((event) => {
                    const past = isPast(event, now);
                    return (
                      <div
                        key={event.id}
                        className={cn(
                          "flex items-start gap-2.5 rounded p-2 transition-colors",
                          past ? "bg-hud-bg/30" : "bg-hud-bg/60 border border-hud-border/20 hover:border-hud-border/40"
                        )}
                      >
                        {/* Time */}
                        <div className="w-14 shrink-0 pt-0.5">
                          <div className="text-[10px] font-mono text-muted-foreground">{event.time}</div>
                        </div>

                        {/* Impact dot */}
                        <div className="pt-1 shrink-0">
                          <div className={cn("h-2 w-2 rounded-full", IMPACT_COLORS[event.impact])} />
                        </div>

                        {/* Content */}
                        <div className="flex-1 min-w-0">
                          <div className="flex items-center gap-1.5 flex-wrap">
                            <span className={cn("font-medium text-[11px]", past ? "text-muted-foreground" : "text-white")}>
                              {event.title}
                            </span>
                            <span className="text-[11px]">{COUNTRY_FLAGS[event.country]}</span>
                            <Badge variant="outline" className={cn("text-[8px] px-1 py-0", CATEGORY_STYLES[event.category] ?? "text-muted-foreground")}>
                              {event.category}
                            </Badge>
                            <Badge variant="outline" className={cn("text-[8px] px-1 py-0", IMPACT_TEXT[event.impact])}>
                              {event.impact}
                            </Badge>
                          </div>

                          {(event.previous || event.forecast || event.actual) && (
                            <div className="flex items-center gap-2.5 mt-1 flex-wrap">
                              {event.previous && (
                                <div className="flex items-center gap-0.5">
                                  <span className="text-[9px] font-mono text-muted-foreground/60">Prev:</span>
                                  <span className="text-[10px] font-mono text-muted-foreground">{event.previous}</span>
                                </div>
                              )}
                              {event.forecast && (
                                <div className="flex items-center gap-0.5">
                                  <span className="text-[9px] font-mono text-muted-foreground/60">Fcst:</span>
                                  <span className="text-[10px] font-mono text-hud-amber">{event.forecast}</span>
                                </div>
                              )}
                              {event.actual && (
                                <div className="flex items-center gap-0.5">
                                  <span className="text-[9px] font-mono text-muted-foreground/60">Act:</span>
                                  <span className="text-[10px] font-mono text-hud-green font-semibold">{event.actual}</span>
                                </div>
                              )}
                            </div>
                          )}
                        </div>

                        {event.impact === "high" && !past && (
                          <div className="pt-0.5 shrink-0">
                            <TrendingUp className="h-3.5 w-3.5 text-hud-red/50" />
                          </div>
                        )}
                      </div>
                    );
                  })}
                </div>
              </div>
            </HudPanel>
          );
        })
      )}

      {/* Footer */}
      <div className="text-[9px] font-mono text-muted-foreground/50 space-y-0.5 pb-2">
        <p>Economic calendar data is simulated for demonstration. Events are anchored to the current week.</p>
        <p>High-impact events (Fed decisions, NFP, CPI) typically cause significant market volatility.</p>
      </div>
    </div>
  );
}
