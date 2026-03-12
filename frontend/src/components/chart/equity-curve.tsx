// =============================================================================
// src/components/chart/equity-curve.tsx — SVG portfolio equity curve + benchmarks
// =============================================================================

"use client";

import { useState } from "react";
import type { ClosedTrade } from "@/lib/types";

interface EquityCurveProps {
  closedTrades: ClosedTrade[];
  initialCapital: number;
  currentValue: number;
  height?: number;
  benchmarks?: { label: string; color: string; returnPct: number }[];
}

export function EquityCurve({
  closedTrades,
  initialCapital,
  currentValue,
  height = 200,
  benchmarks = [],
}: EquityCurveProps) {
  const [showBenchmarks, setShowBenchmarks] = useState(true);

  // Build equity points from trade history
  const sorted = [...closedTrades].sort(
    (a, b) => new Date(a.closedAt).getTime() - new Date(b.closedAt).getTime()
  );

  const points: { x: number; y: number; label: string }[] = [
    { x: 0, y: initialCapital, label: "Start" },
  ];

  let equity = initialCapital;
  sorted.forEach((trade, i) => {
    equity += trade.pnl;
    points.push({
      x: i + 1,
      y: equity,
      label: `${trade.asset} ${trade.pnl >= 0 ? "+" : ""}$${trade.pnl.toFixed(0)}`,
    });
  });

  // Add current value as last point
  points.push({
    x: sorted.length + 1,
    y: currentValue,
    label: "Now",
  });

  if (points.length < 2) return null;

  const width = 600;
  const padding = { top: 20, right: 80, bottom: 30, left: 60 };
  const chartW = width - padding.left - padding.right;
  const chartH = height - padding.top - padding.bottom;

  // Compute benchmark lines to determine Y range
  const benchmarkLines = benchmarks.map((b) => {
    // Linear interpolation from initialCapital to final value based on return
    const finalVal = initialCapital * (1 + b.returnPct / 100);
    return points.map((p) => ({
      x: p.x,
      y: initialCapital + ((finalVal - initialCapital) * p.x) / (points.length - 1),
    }));
  });

  const allYValues = [
    ...points.map((p) => p.y),
    ...benchmarkLines.flatMap((line) => line.map((p) => p.y)),
  ];
  const minY = Math.min(...allYValues) * 0.995;
  const maxY = Math.max(...allYValues) * 1.005;
  const rangeY = maxY - minY || 1;
  const maxX = points.length - 1;

  const toSvgX = (x: number) => padding.left + (x / maxX) * chartW;
  const toSvgY = (y: number) =>
    padding.top + chartH - ((y - minY) / rangeY) * chartH;

  // Build SVG path
  const linePath = points
    .map((p, i) => `${i === 0 ? "M" : "L"} ${toSvgX(p.x).toFixed(1)} ${toSvgY(p.y).toFixed(1)}`)
    .join(" ");

  // Fill area
  const areaPath = `${linePath} L ${toSvgX(maxX).toFixed(1)} ${toSvgY(minY).toFixed(1)} L ${toSvgX(0).toFixed(1)} ${toSvgY(minY).toFixed(1)} Z`;

  const isPositive = currentValue >= initialCapital;
  const lineColor = isPositive ? "#22c55e" : "#ef4444";
  const fillColor = isPositive ? "rgba(34,197,94,0.1)" : "rgba(239,68,68,0.1)";

  // Y-axis labels (4 ticks)
  const yTicks = Array.from({ length: 4 }, (_, i) => minY + (rangeY * i) / 3);

  const portfolioReturn = initialCapital > 0
    ? ((currentValue - initialCapital) / initialCapital) * 100
    : 0;

  return (
    <div>
      {benchmarks.length > 0 && (
        <div className="flex items-center gap-4 mb-2">
          <button
            onClick={() => setShowBenchmarks((p) => !p)}
            className="text-[10px] text-muted-foreground hover:text-white transition-colors"
          >
            {showBenchmarks ? "Hide" : "Show"} Benchmarks
          </button>
          <div className="flex items-center gap-3">
            <div className="flex items-center gap-1">
              <div className="h-0.5 w-4" style={{ backgroundColor: lineColor }} />
              <span className="text-[10px] text-muted-foreground">
                Portfolio ({portfolioReturn >= 0 ? "+" : ""}{portfolioReturn.toFixed(1)}%)
              </span>
            </div>
            {showBenchmarks && benchmarks.map((b) => (
              <div key={b.label} className="flex items-center gap-1">
                <div className="h-0.5 w-4 opacity-50" style={{ backgroundColor: b.color, borderStyle: "dashed" }} />
                <span className="text-[10px] text-muted-foreground">
                  {b.label} ({b.returnPct >= 0 ? "+" : ""}{b.returnPct.toFixed(1)}%)
                </span>
              </div>
            ))}
          </div>
        </div>
      )}

      <svg
        viewBox={`0 0 ${width} ${height}`}
        className="w-full"
        style={{ maxHeight: height }}
      >
        {/* Grid lines */}
        {yTicks.map((tick, i) => (
          <g key={i}>
            <line
              x1={padding.left}
              x2={width - padding.right}
              y1={toSvgY(tick)}
              y2={toSvgY(tick)}
              stroke="currentColor"
              className="text-border/30"
              strokeDasharray="4 4"
            />
            <text
              x={padding.left - 8}
              y={toSvgY(tick)}
              textAnchor="end"
              dominantBaseline="middle"
              className="fill-muted-foreground"
              fontSize={10}
              fontFamily="monospace"
            >
              ${(tick / 1000).toFixed(1)}k
            </text>
          </g>
        ))}

        {/* Benchmark lines */}
        {showBenchmarks && benchmarkLines.map((line, bi) => {
          const benchPath = line
            .map((p, i) => `${i === 0 ? "M" : "L"} ${toSvgX(p.x).toFixed(1)} ${toSvgY(p.y).toFixed(1)}`)
            .join(" ");
          return (
            <g key={benchmarks[bi].label}>
              <path
                d={benchPath}
                fill="none"
                stroke={benchmarks[bi].color}
                strokeWidth={1.5}
                strokeDasharray="6 3"
                opacity={0.5}
              />
              <text
                x={toSvgX(maxX) + 4}
                y={toSvgY(line[line.length - 1].y)}
                dominantBaseline="middle"
                fontSize={9}
                fontFamily="monospace"
                fill={benchmarks[bi].color}
                opacity={0.7}
              >
                {benchmarks[bi].label}
              </text>
            </g>
          );
        })}

        {/* Area fill */}
        <path d={areaPath} fill={fillColor} />

        {/* Line */}
        <path d={linePath} fill="none" stroke={lineColor} strokeWidth={2} />

        {/* Data points */}
        {points.map((p, i) => (
          <circle
            key={i}
            cx={toSvgX(p.x)}
            cy={toSvgY(p.y)}
            r={i === 0 || i === points.length - 1 ? 4 : 2.5}
            fill={lineColor}
            className="opacity-80"
          />
        ))}

        {/* Start and end labels */}
        <text
          x={toSvgX(0)}
          y={height - 8}
          textAnchor="start"
          className="fill-muted-foreground"
          fontSize={10}
        >
          Start
        </text>
        <text
          x={toSvgX(maxX)}
          y={height - 8}
          textAnchor="end"
          className="fill-muted-foreground"
          fontSize={10}
        >
          Now
        </text>

        {/* Current value label */}
        <text
          x={toSvgX(maxX) + 4}
          y={toSvgY(currentValue)}
          dominantBaseline="middle"
          className="fill-white"
          fontSize={11}
          fontWeight="bold"
          fontFamily="monospace"
        >
          ${currentValue.toLocaleString("en-US", { maximumFractionDigits: 0 })}
        </text>
      </svg>
    </div>
  );
}
