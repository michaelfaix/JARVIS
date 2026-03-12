// =============================================================================
// src/components/risk/risk-score-gauge.tsx — Portfolio risk score gauge
// =============================================================================

"use client";

import { useMemo } from "react";
import { Shield, AlertTriangle, CheckCircle2 } from "lucide-react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { cn } from "@/lib/utils";

interface RiskScoreGaugeProps {
  score: number; // 0-100
  maxExposure: number; // percentage, e.g. 35.5
  openPositions: number;
  drawdown: number; // percentage
}

function getRiskLevel(score: number) {
  if (score <= 30) return { label: "Low Risk", color: "text-green-500", bg: "bg-green-500/10 border-green-500/30 text-green-500", icon: CheckCircle2 };
  if (score <= 60) return { label: "Medium Risk", color: "text-yellow-500", bg: "bg-yellow-500/10 border-yellow-500/30 text-yellow-500", icon: AlertTriangle };
  return { label: "High Risk", color: "text-red-500", bg: "bg-red-500/10 border-red-500/30 text-red-500", icon: Shield };
}

function getDiversification(positions: number): { label: string; color: string } {
  if (positions >= 8) return { label: "Good", color: "text-green-500" };
  if (positions >= 4) return { label: "Fair", color: "text-yellow-500" };
  return { label: "Poor", color: "text-red-500" };
}

function getExposureColor(exposure: number): string {
  if (exposure <= 25) return "text-green-500";
  if (exposure <= 50) return "text-yellow-500";
  return "text-red-500";
}

function getDrawdownColor(drawdown: number): string {
  if (drawdown <= 5) return "text-green-500";
  if (drawdown <= 15) return "text-yellow-500";
  return "text-red-500";
}

// Convert a score (0-100) to an angle on the semi-circle (180° to 0°)
function scoreToAngle(score: number): number {
  const clamped = Math.max(0, Math.min(100, score));
  return Math.PI - (clamped / 100) * Math.PI; // 180° at 0, 0° at 100
}

// Get a point on the arc given center, radius, and angle in radians
function polarToCartesian(cx: number, cy: number, r: number, angle: number) {
  return {
    x: cx + r * Math.cos(angle),
    y: cy - r * Math.sin(angle),
  };
}

// Build an SVG arc path from startAngle to endAngle (radians, counterclockwise)
function describeArc(
  cx: number,
  cy: number,
  r: number,
  startAngle: number,
  endAngle: number
): string {
  const start = polarToCartesian(cx, cy, r, startAngle);
  const end = polarToCartesian(cx, cy, r, endAngle);
  const largeArc = startAngle - endAngle > Math.PI ? 1 : 0;
  return `M ${start.x} ${start.y} A ${r} ${r} 0 ${largeArc} 0 ${end.x} ${end.y}`;
}

export function RiskScoreGauge({
  score,
  maxExposure,
  openPositions,
  drawdown,
}: RiskScoreGaugeProps) {
  const clampedScore = Math.max(0, Math.min(100, score));
  const risk = useMemo(() => getRiskLevel(clampedScore), [clampedScore]);
  const diversification = useMemo(() => getDiversification(openPositions), [openPositions]);

  const cx = 100;
  const cy = 100;
  const r = 80;
  const strokeWidth = 12;

  // Full background arc (180° to 0°)
  const bgArc = describeArc(cx, cy, r, Math.PI, 0);

  // Zone arcs
  const greenArc = describeArc(cx, cy, r, Math.PI, scoreToAngle(30));
  const yellowArc = describeArc(cx, cy, r, scoreToAngle(30), scoreToAngle(60));
  const redArc = describeArc(cx, cy, r, scoreToAngle(60), 0);

  // Score arc (colored portion)
  const scoreAngle = scoreToAngle(clampedScore);
  const scoreArc = clampedScore > 0 ? describeArc(cx, cy, r, Math.PI, scoreAngle) : "";

  // Needle endpoint
  const needleLength = r - 20;
  const needleTip = polarToCartesian(cx, cy, needleLength, scoreAngle);

  // Score arc color
  const arcColor =
    clampedScore <= 30
      ? "#22c55e"
      : clampedScore <= 60
        ? "#eab308"
        : "#ef4444";

  const RiskIcon = risk.icon;

  return (
    <Card className="bg-card/50 border-border/50">
      <CardHeader className="pb-2">
        <CardTitle className="flex items-center gap-2 text-lg">
          <Shield className="h-5 w-5 text-muted-foreground" />
          Risk Guardian
        </CardTitle>
      </CardHeader>
      <CardContent className="flex flex-col items-center gap-4">
        {/* SVG Gauge */}
        <div className="w-full max-w-[280px]">
          <svg viewBox="0 0 200 120" className="w-full">
            {/* Background arc */}
            <path
              d={bgArc}
              fill="none"
              stroke="currentColor"
              className="text-muted/30"
              strokeWidth={strokeWidth}
              strokeLinecap="round"
            />

            {/* Color zone arcs (subtle) */}
            <path
              d={greenArc}
              fill="none"
              stroke="#22c55e"
              opacity={0.15}
              strokeWidth={strokeWidth}
              strokeLinecap="butt"
            />
            <path
              d={yellowArc}
              fill="none"
              stroke="#eab308"
              opacity={0.15}
              strokeWidth={strokeWidth}
              strokeLinecap="butt"
            />
            <path
              d={redArc}
              fill="none"
              stroke="#ef4444"
              opacity={0.15}
              strokeWidth={strokeWidth}
              strokeLinecap="butt"
            />

            {/* Active score arc */}
            {scoreArc && (
              <path
                d={scoreArc}
                fill="none"
                stroke={arcColor}
                strokeWidth={strokeWidth}
                strokeLinecap="round"
              />
            )}

            {/* Needle */}
            <line
              x1={cx}
              y1={cy}
              x2={needleTip.x}
              y2={needleTip.y}
              stroke={arcColor}
              strokeWidth={2.5}
              strokeLinecap="round"
            />

            {/* Needle center dot */}
            <circle cx={cx} cy={cy} r={4} fill={arcColor} />

            {/* Score number */}
            <text
              x={cx}
              y={cy - 20}
              textAnchor="middle"
              className="fill-foreground"
              fontSize={28}
              fontWeight={700}
            >
              {clampedScore}
            </text>

            {/* Label */}
            <text
              x={cx}
              y={cy - 6}
              textAnchor="middle"
              className="fill-muted-foreground"
              fontSize={10}
            >
              Risk Score
            </text>

            {/* Zone labels */}
            <text x={18} y={118} textAnchor="middle" fill="#22c55e" fontSize={7} fontWeight={500}>
              0
            </text>
            <text x={100} y={14} textAnchor="middle" fill="#eab308" fontSize={7} fontWeight={500}>
              50
            </text>
            <text x={182} y={118} textAnchor="middle" fill="#ef4444" fontSize={7} fontWeight={500}>
              100
            </text>
          </svg>
        </div>

        {/* Risk Level Badge */}
        <Badge className={cn("gap-1.5 px-3 py-1 text-sm", risk.bg)}>
          <RiskIcon className="h-3.5 w-3.5" />
          {risk.label}
        </Badge>

        {/* Risk Breakdown Grid */}
        <div className="grid w-full grid-cols-2 gap-3">
          {/* Max Exposure */}
          <div className="rounded-lg border border-border/50 bg-card/50 p-3">
            <p className="text-xs text-muted-foreground">Max Exposure</p>
            <p className={cn("text-lg font-semibold", getExposureColor(maxExposure))}>
              {(isFinite(maxExposure) ? maxExposure : 0).toFixed(1)}%
            </p>
          </div>

          {/* Open Positions */}
          <div className="rounded-lg border border-border/50 bg-card/50 p-3">
            <p className="text-xs text-muted-foreground">Open Positions</p>
            <p className="text-lg font-semibold text-foreground">
              {openPositions}
            </p>
          </div>

          {/* Drawdown */}
          <div className="rounded-lg border border-border/50 bg-card/50 p-3">
            <p className="text-xs text-muted-foreground">Drawdown</p>
            <p className={cn("text-lg font-semibold", getDrawdownColor(drawdown))}>
              {(isFinite(drawdown) ? drawdown : 0).toFixed(1)}%
            </p>
          </div>

          {/* Diversification */}
          <div className="rounded-lg border border-border/50 bg-card/50 p-3">
            <p className="text-xs text-muted-foreground">Diversification</p>
            <p className={cn("text-lg font-semibold", diversification.color)}>
              {diversification.label}
            </p>
          </div>
        </div>
      </CardContent>
    </Card>
  );
}
