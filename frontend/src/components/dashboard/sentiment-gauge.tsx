// =============================================================================
// src/components/dashboard/sentiment-gauge.tsx — Semi-circular Fear & Greed Gauge
//
// Self-contained SVG gauge with color gradient, needle, and classification.
// =============================================================================

"use client";

import React from "react";

interface SentimentGaugeProps {
  value: number; // 0-100
  classification: string;
  size?: number; // width in px, default 200
  loading?: boolean;
}

// Color stops for the gauge arc
const GAUGE_COLORS = [
  { stop: 0, color: "#ef4444" }, // red — Extreme Fear
  { stop: 25, color: "#f97316" }, // orange — Fear
  { stop: 45, color: "#eab308" }, // yellow — Neutral
  { stop: 55, color: "#84cc16" }, // light green — Greed
  { stop: 75, color: "#22c55e" }, // green — Extreme Greed
  { stop: 100, color: "#16a34a" }, // darker green
];

function getColor(value: number): string {
  if (value <= 25) return "#ef4444";
  if (value <= 45) return "#f97316";
  if (value <= 55) return "#eab308";
  if (value <= 75) return "#84cc16";
  return "#22c55e";
}

export function SentimentGauge({
  value,
  classification,
  size = 180,
  loading = false,
}: SentimentGaugeProps) {
  const clamped = Math.max(0, Math.min(100, value));

  // SVG arc geometry
  const cx = 100;
  const cy = 95;
  const radius = 72;
  const strokeWidth = 14;

  // Arc from 180deg (left) to 0deg (right) = semi-circle
  const startAngle = Math.PI; // 180 degrees
  const endAngle = 0; // 0 degrees
  const sweepAngle = startAngle - endAngle; // PI radians

  // Needle angle: map 0-100 to PI..0
  const needleAngle = startAngle - (clamped / 100) * sweepAngle;
  const needleLength = radius - 8;
  const needleX = cx + needleLength * Math.cos(needleAngle);
  const needleY = cy - needleLength * Math.sin(needleAngle);

  // Create arc path for background (full semi-circle)
  const arcStartX = cx + radius * Math.cos(startAngle);
  const arcStartY = cy - radius * Math.sin(startAngle);
  const arcEndX = cx + radius * Math.cos(endAngle);
  const arcEndY = cy - radius * Math.sin(endAngle);

  const bgArcPath = `M ${arcStartX} ${arcStartY} A ${radius} ${radius} 0 0 1 ${arcEndX} ${arcEndY}`;

  // Gradient ID
  const gradientId = "sentimentGradient";

  return (
    <div className="flex flex-col items-center" style={{ width: size }}>
      <svg
        viewBox="0 0 200 115"
        width={size}
        height={size * 0.575}
        className="overflow-visible"
      >
        <defs>
          <linearGradient id={gradientId} x1="0%" y1="0%" x2="100%" y2="0%">
            {GAUGE_COLORS.map((c) => (
              <stop
                key={c.stop}
                offset={`${c.stop}%`}
                stopColor={c.color}
                stopOpacity={1}
              />
            ))}
          </linearGradient>
        </defs>

        {/* Background track */}
        <path
          d={bgArcPath}
          fill="none"
          stroke="rgba(255,255,255,0.08)"
          strokeWidth={strokeWidth}
          strokeLinecap="round"
        />

        {/* Colored arc */}
        <path
          d={bgArcPath}
          fill="none"
          stroke={`url(#${gradientId})`}
          strokeWidth={strokeWidth}
          strokeLinecap="round"
          opacity={loading ? 0.3 : 0.9}
        />

        {/* Tick marks */}
        {[0, 25, 50, 75, 100].map((tick) => {
          const angle = startAngle - (tick / 100) * sweepAngle;
          const outerR = radius + strokeWidth / 2 + 3;
          const innerR = radius + strokeWidth / 2 - 1;
          const ox = cx + outerR * Math.cos(angle);
          const oy = cy - outerR * Math.sin(angle);
          const ix = cx + innerR * Math.cos(angle);
          const iy = cy - innerR * Math.sin(angle);
          return (
            <line
              key={tick}
              x1={ix}
              y1={iy}
              x2={ox}
              y2={oy}
              stroke="rgba(255,255,255,0.3)"
              strokeWidth={1.5}
            />
          );
        })}

        {/* Needle */}
        {!loading && (
          <>
            {/* Needle line */}
            <line
              x1={cx}
              y1={cy}
              x2={needleX}
              y2={needleY}
              stroke="white"
              strokeWidth={2.5}
              strokeLinecap="round"
              style={{
                filter: "drop-shadow(0 0 3px rgba(255,255,255,0.4))",
              }}
            />
            {/* Needle center dot */}
            <circle
              cx={cx}
              cy={cy}
              r={5}
              fill={getColor(clamped)}
              stroke="white"
              strokeWidth={2}
            />
            {/* Value dot at tip */}
            <circle
              cx={needleX}
              cy={needleY}
              r={3}
              fill="white"
              opacity={0.8}
            />
          </>
        )}

        {/* Center value text */}
        <text
          x={cx}
          y={cy - 18}
          textAnchor="middle"
          className="font-mono"
          fill="white"
          fontSize="28"
          fontWeight="700"
        >
          {loading ? "--" : clamped}
        </text>

        {/* Small "/ 100" label */}
        <text
          x={cx + 22}
          y={cy - 10}
          textAnchor="start"
          fill="rgba(255,255,255,0.4)"
          fontSize="10"
          fontWeight="400"
        >
          /100
        </text>
      </svg>

      {/* Classification label */}
      <div
        className="text-xs font-semibold tracking-wide mt-0.5"
        style={{ color: loading ? "rgba(255,255,255,0.3)" : getColor(clamped) }}
      >
        {loading ? "Loading..." : classification}
      </div>
    </div>
  );
}
