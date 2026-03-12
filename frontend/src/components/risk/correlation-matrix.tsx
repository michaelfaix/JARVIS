// =============================================================================
// src/components/risk/correlation-matrix.tsx — Asset correlation heatmap
// =============================================================================

"use client";

import { useMemo } from "react";

interface CorrelationMatrixProps {
  assets: string[];
  prices: Record<string, number>;
}

// Generate deterministic pseudo-correlations based on asset pairs
// In production, these would be computed from historical return data
function getCorrelation(a: string, b: string): number {
  if (a === b) return 1.0;

  // Known correlation patterns (realistic crypto/equity/commodity relationships)
  const pairs: Record<string, number> = {
    "BTC-ETH": 0.85,
    "BTC-SOL": 0.78,
    "ETH-SOL": 0.82,
    "BTC-SPY": 0.35,
    "ETH-SPY": 0.30,
    "SOL-SPY": 0.28,
    "BTC-AAPL": 0.25,
    "ETH-AAPL": 0.22,
    "SOL-AAPL": 0.20,
    "BTC-NVDA": 0.40,
    "ETH-NVDA": 0.38,
    "SOL-NVDA": 0.35,
    "BTC-TSLA": 0.45,
    "ETH-TSLA": 0.42,
    "SOL-TSLA": 0.40,
    "BTC-GLD": -0.15,
    "ETH-GLD": -0.12,
    "SOL-GLD": -0.10,
    "SPY-AAPL": 0.88,
    "SPY-NVDA": 0.75,
    "SPY-TSLA": 0.65,
    "SPY-GLD": 0.05,
    "AAPL-NVDA": 0.72,
    "AAPL-TSLA": 0.55,
    "AAPL-GLD": -0.05,
    "NVDA-TSLA": 0.60,
    "NVDA-GLD": -0.08,
    "TSLA-GLD": -0.10,
  };

  const key1 = `${a}-${b}`;
  const key2 = `${b}-${a}`;
  return pairs[key1] ?? pairs[key2] ?? 0;
}

function correlationColor(val: number): string {
  if (val >= 0.7) return "rgba(239, 68, 68, 0.6)"; // strong positive = red (risk)
  if (val >= 0.4) return "rgba(239, 68, 68, 0.3)";
  if (val >= 0.1) return "rgba(234, 179, 8, 0.2)";
  if (val >= -0.1) return "rgba(107, 114, 128, 0.1)";
  if (val >= -0.4) return "rgba(34, 197, 94, 0.2)";
  return "rgba(34, 197, 94, 0.4)"; // negative = green (diversification)
}

function correlationTextColor(val: number): string {
  if (val >= 0.7) return "text-red-400";
  if (val >= 0.4) return "text-red-300";
  if (val >= 0.1) return "text-yellow-400";
  if (val >= -0.1) return "text-muted-foreground";
  if (val >= -0.4) return "text-green-300";
  return "text-green-400";
}

export function CorrelationMatrix({ assets }: CorrelationMatrixProps) {
  const matrix = useMemo(() => {
    return assets.map((a) =>
      assets.map((b) => getCorrelation(a, b))
    );
  }, [assets]);

  return (
    <div className="overflow-x-auto">
      <table className="w-full border-collapse">
        <thead>
          <tr>
            <th className="p-1.5 text-[10px] text-muted-foreground" />
            {assets.map((a) => (
              <th key={a} className="p-1.5 text-[10px] text-white font-bold text-center">
                {a}
              </th>
            ))}
          </tr>
        </thead>
        <tbody>
          {assets.map((rowAsset, ri) => (
            <tr key={rowAsset}>
              <td className="p-1.5 text-[10px] text-white font-bold">{rowAsset}</td>
              {assets.map((colAsset, ci) => {
                const val = matrix[ri][ci];
                const isDiagonal = ri === ci;
                return (
                  <td
                    key={colAsset}
                    className="p-1 text-center"
                  >
                    <div
                      className={`rounded px-1 py-1.5 text-[10px] font-mono font-medium ${
                        isDiagonal ? "text-white" : correlationTextColor(val)
                      }`}
                      style={{
                        backgroundColor: isDiagonal
                          ? "rgba(59, 130, 246, 0.15)"
                          : correlationColor(val),
                      }}
                    >
                      {isDiagonal ? "1.00" : val.toFixed(2)}
                    </div>
                  </td>
                );
              })}
            </tr>
          ))}
        </tbody>
      </table>
      <div className="flex items-center gap-4 mt-3 text-[10px] text-muted-foreground">
        <span className="flex items-center gap-1">
          <span className="w-3 h-2 rounded" style={{ backgroundColor: "rgba(34, 197, 94, 0.4)" }} />
          Negative (diversified)
        </span>
        <span className="flex items-center gap-1">
          <span className="w-3 h-2 rounded" style={{ backgroundColor: "rgba(107, 114, 128, 0.1)" }} />
          Low
        </span>
        <span className="flex items-center gap-1">
          <span className="w-3 h-2 rounded" style={{ backgroundColor: "rgba(239, 68, 68, 0.3)" }} />
          Moderate
        </span>
        <span className="flex items-center gap-1">
          <span className="w-3 h-2 rounded" style={{ backgroundColor: "rgba(239, 68, 68, 0.6)" }} />
          High (concentrated risk)
        </span>
      </div>
    </div>
  );
}
