// =============================================================================
// src/components/social/trader-profile-card.tsx — Trader profile card
// =============================================================================

"use client";

import { Card, CardContent } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Heart, Copy } from "lucide-react";
import { useSocialTrading } from "@/hooks/use-social-trading";
import { useState } from "react";

export interface TraderData {
  id: string;
  name: string;
  tier: "free" | "pro" | "enterprise";
  totalReturn: number;
  winRate: number;
  trades: number;
  drawdown: number;
  isCurrentUser?: boolean;
}

const TIER_BADGE: Record<string, string> = {
  enterprise: "bg-purple-500/20 text-purple-400 border-purple-500/30",
  pro: "bg-blue-500/20 text-blue-400 border-blue-500/30",
  free: "bg-muted text-muted-foreground border-border/50",
};

function getRiskBadge(drawdown: number): { label: string; className: string } {
  if (drawdown <= 5) return { label: "Conservative", className: "bg-green-500/20 text-green-400 border-green-500/30" };
  if (drawdown <= 10) return { label: "Moderate", className: "bg-yellow-500/20 text-yellow-400 border-yellow-500/30" };
  return { label: "Aggressive", className: "bg-red-500/20 text-red-400 border-red-500/30" };
}

function getStrategyTags(trader: TraderData): string[] {
  const tags: string[] = [];
  if (trader.trades > 200) tags.push("Scalper");
  else if (trader.trades > 80) tags.push("Day Trader");
  else if (trader.trades > 30) tags.push("Swing Trader");
  else tags.push("Position Trader");

  if (trader.winRate >= 65) tags.push("High Win Rate");
  if (trader.drawdown <= 5) tags.push("Low Risk");
  if (trader.totalReturn > 20) tags.push("Top Performer");

  return tags.slice(0, 3);
}

function getInitials(name: string): string {
  return name
    .split(/[_\s]+/)
    .slice(0, 2)
    .map((s) => s[0]?.toUpperCase() ?? "")
    .join("");
}

interface TraderProfileCardProps {
  trader: TraderData;
  compact?: boolean;
  showCopyControls?: boolean;
}

export function TraderProfileCard({ trader, compact, showCopyControls = true }: TraderProfileCardProps) {
  const { isFollowing, followTrader, unfollowTrader, canFollow, copySettings, setCopySettings } = useSocialTrading();
  const following = isFollowing(trader.id);
  const risk = getRiskBadge(trader.drawdown);
  const tags = getStrategyTags(trader);
  const settings = copySettings[trader.id];
  const [localCapital, setLocalCapital] = useState(settings?.maxCapitalPercent ?? 5);

  const handleFollowToggle = () => {
    if (following) {
      unfollowTrader(trader.id);
    } else {
      followTrader(trader.id);
    }
  };

  const handleCopyToggle = () => {
    setCopySettings(trader.id, { enabled: !settings?.enabled });
  };

  const handleCapitalChange = (value: number) => {
    setLocalCapital(value);
    setCopySettings(trader.id, { maxCapitalPercent: value });
  };

  if (compact) {
    return (
      <div className="flex items-center gap-3 p-2">
        <div className="flex h-8 w-8 shrink-0 items-center justify-center rounded-full bg-blue-600/20 text-blue-400 text-xs font-bold">
          {getInitials(trader.name)}
        </div>
        <div className="min-w-0 flex-1">
          <div className="text-xs font-medium text-white truncate">{trader.name}</div>
          <div className="text-[10px] text-muted-foreground">
            {trader.totalReturn >= 0 ? "+" : ""}{trader.totalReturn.toFixed(1)}% · {trader.winRate}% WR
          </div>
        </div>
        <Button
          variant="ghost"
          size="sm"
          className="h-7 w-7 p-0"
          onClick={handleFollowToggle}
          disabled={!following && !canFollow && !trader.isCurrentUser}
        >
          <Heart
            className={`h-3.5 w-3.5 ${following ? "fill-red-500 text-red-500" : "text-muted-foreground"}`}
          />
        </Button>
      </div>
    );
  }

  return (
    <Card className="bg-card/50 border-border/50">
      <CardContent className="pt-4 pb-3 px-4 space-y-3">
        {/* Header: Avatar + Name + Tier */}
        <div className="flex items-start gap-3">
          <div className="flex h-10 w-10 shrink-0 items-center justify-center rounded-full bg-blue-600/20 text-blue-400 text-sm font-bold">
            {getInitials(trader.name)}
          </div>
          <div className="min-w-0 flex-1">
            <div className="flex items-center gap-2">
              <span className="text-sm font-bold text-white truncate">{trader.name}</span>
              <Badge className={`text-[9px] ${TIER_BADGE[trader.tier]}`}>{trader.tier}</Badge>
            </div>
            <div className="flex items-center gap-2 mt-0.5">
              <Badge className={`text-[9px] ${risk.className}`}>{risk.label}</Badge>
              {tags.map((tag) => (
                <Badge key={tag} variant="outline" className="text-[9px] text-muted-foreground border-border/50">
                  {tag}
                </Badge>
              ))}
            </div>
          </div>
          {!trader.isCurrentUser && (
            <Button
              variant="ghost"
              size="sm"
              className="h-8 w-8 p-0 shrink-0"
              onClick={handleFollowToggle}
              disabled={!following && !canFollow}
              title={following ? "Unfollow" : canFollow ? "Follow" : "Max follows reached (upgrade to Pro)"}
            >
              <Heart
                className={`h-4 w-4 ${following ? "fill-red-500 text-red-500" : "text-muted-foreground hover:text-red-400"}`}
              />
            </Button>
          )}
        </div>

        {/* Stats Grid */}
        <div className="grid grid-cols-4 gap-2">
          <div className="text-center">
            <div className={`text-sm font-bold font-mono ${trader.totalReturn >= 0 ? "text-green-400" : "text-red-400"}`}>
              {trader.totalReturn >= 0 ? "+" : ""}{trader.totalReturn.toFixed(1)}%
            </div>
            <div className="text-[9px] text-muted-foreground">Return</div>
          </div>
          <div className="text-center">
            <div className="text-sm font-bold font-mono text-white">{trader.winRate}%</div>
            <div className="text-[9px] text-muted-foreground">Win Rate</div>
          </div>
          <div className="text-center">
            <div className="text-sm font-bold font-mono text-white">{trader.trades}</div>
            <div className="text-[9px] text-muted-foreground">Trades</div>
          </div>
          <div className="text-center">
            <div className={`text-sm font-bold font-mono ${trader.drawdown > 10 ? "text-red-400" : trader.drawdown > 5 ? "text-yellow-400" : "text-green-400"}`}>
              {trader.drawdown.toFixed(1)}%
            </div>
            <div className="text-[9px] text-muted-foreground">Max DD</div>
          </div>
        </div>

        {/* Copy Trading Controls */}
        {showCopyControls && following && !trader.isCurrentUser && (
          <div className="border-t border-border/30 pt-2 space-y-2">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-1.5">
                <Copy className="h-3 w-3 text-muted-foreground" />
                <span className="text-[11px] text-muted-foreground">Copy Trades</span>
              </div>
              <button
                onClick={handleCopyToggle}
                className={`relative inline-flex h-5 w-9 shrink-0 cursor-pointer items-center rounded-full transition-colors ${
                  settings?.enabled ? "bg-blue-600" : "bg-muted"
                }`}
              >
                <span
                  className={`pointer-events-none block h-4 w-4 rounded-full bg-white shadow-sm transition-transform ${
                    settings?.enabled ? "translate-x-4" : "translate-x-0.5"
                  }`}
                />
              </button>
            </div>
            {settings?.enabled && (
              <div className="space-y-1">
                <div className="flex items-center justify-between">
                  <span className="text-[10px] text-muted-foreground">Capital allocation</span>
                  <span className="text-[10px] font-mono text-white">{localCapital}%</span>
                </div>
                <input
                  type="range"
                  min={1}
                  max={50}
                  value={localCapital}
                  onChange={(e) => handleCapitalChange(Number(e.target.value))}
                  className="w-full h-1 bg-muted rounded-full appearance-none cursor-pointer accent-blue-600"
                />
                <div className="flex justify-between text-[9px] text-muted-foreground">
                  <span>1%</span>
                  <span>50%</span>
                </div>
              </div>
            )}
          </div>
        )}
      </CardContent>
    </Card>
  );
}
