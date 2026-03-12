// =============================================================================
// src/components/risk/position-calculator.tsx — Risk-based position size calculator
// =============================================================================

"use client";

import { useMemo, useState } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Calculator, AlertTriangle } from "lucide-react";

interface PositionCalculatorProps {
  availableCapital: number;
  totalValue: number;
  prices: Record<string, number>;
}

export function PositionCalculator({
  availableCapital,
  totalValue,
  prices,
}: PositionCalculatorProps) {
  const [asset, setAsset] = useState("BTC");
  const [riskPct, setRiskPct] = useState(2); // % of portfolio risked
  const [stopLossPct, setStopLossPct] = useState(5); // % from entry

  const result = useMemo(() => {
    const entryPrice = prices[asset] ?? 0;
    if (entryPrice === 0 || stopLossPct === 0) return null;

    const riskAmount = (totalValue * riskPct) / 100;
    const stopLossDistance = entryPrice * (stopLossPct / 100);
    const positionSize = riskAmount / stopLossDistance;
    const positionValue = positionSize * entryPrice;
    const capitalPct = totalValue > 0 ? (positionValue / totalValue) * 100 : 0;
    const stopLossPrice = entryPrice * (1 - stopLossPct / 100);
    const canAfford = positionValue <= availableCapital;

    return {
      entryPrice,
      riskAmount,
      positionSize,
      positionValue,
      capitalPct,
      stopLossPrice,
      stopLossDistance,
      canAfford,
    };
  }, [asset, riskPct, stopLossPct, prices, totalValue, availableCapital]);

  const assetOptions = Object.keys(prices).filter((k) => prices[k] > 0);

  return (
    <Card className="bg-card/50 border-border/50">
      <CardHeader className="pb-3">
        <CardTitle className="text-sm font-medium text-muted-foreground flex items-center gap-2">
          <Calculator className="h-4 w-4" />
          Position Size Calculator
        </CardTitle>
      </CardHeader>
      <CardContent className="space-y-4">
        {/* Inputs */}
        <div className="grid grid-cols-3 gap-3">
          <div>
            <label className="text-[10px] text-muted-foreground block mb-1">Asset</label>
            <select
              value={asset}
              onChange={(e) => setAsset(e.target.value)}
              className="w-full h-8 rounded-md border border-border/50 bg-background px-2 text-xs text-white"
            >
              {assetOptions.map((a) => (
                <option key={a} value={a}>{a}</option>
              ))}
            </select>
          </div>
          <div>
            <label className="text-[10px] text-muted-foreground block mb-1">
              Risk per Trade (%)
            </label>
            <input
              type="number"
              min={0.1}
              max={10}
              step={0.1}
              value={riskPct}
              onChange={(e) => setRiskPct(Number(e.target.value))}
              className="w-full h-8 rounded-md border border-border/50 bg-background px-2 text-xs font-mono text-white"
            />
          </div>
          <div>
            <label className="text-[10px] text-muted-foreground block mb-1">
              Stop Loss (%)
            </label>
            <input
              type="number"
              min={0.5}
              max={50}
              step={0.5}
              value={stopLossPct}
              onChange={(e) => setStopLossPct(Number(e.target.value))}
              className="w-full h-8 rounded-md border border-border/50 bg-background px-2 text-xs font-mono text-white"
            />
          </div>
        </div>

        {/* Risk presets */}
        <div className="flex items-center gap-2">
          <span className="text-[10px] text-muted-foreground">Presets:</span>
          {[1, 2, 3, 5].map((pct) => (
            <button
              key={pct}
              onClick={() => setRiskPct(pct)}
              className={`px-2 py-0.5 rounded text-[10px] transition-colors ${
                riskPct === pct
                  ? "bg-blue-600/20 text-blue-400"
                  : "text-muted-foreground hover:text-white hover:bg-muted"
              }`}
            >
              {pct}% risk
            </button>
          ))}
        </div>

        {/* Results */}
        {result && (
          <div className="rounded-lg bg-background/50 p-3 space-y-2">
            <div className="grid grid-cols-2 gap-y-2 gap-x-4 text-xs">
              <div className="flex justify-between">
                <span className="text-muted-foreground">Entry Price</span>
                <span className="font-mono text-white">
                  ${result.entryPrice.toLocaleString("en-US", { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
                </span>
              </div>
              <div className="flex justify-between">
                <span className="text-muted-foreground">Stop Loss</span>
                <span className="font-mono text-red-400">
                  ${result.stopLossPrice.toLocaleString("en-US", { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
                </span>
              </div>
              <div className="flex justify-between">
                <span className="text-muted-foreground">Risk Amount</span>
                <span className="font-mono text-yellow-400">
                  ${result.riskAmount.toFixed(2)}
                </span>
              </div>
              <div className="flex justify-between">
                <span className="text-muted-foreground">Position Size</span>
                <span className="font-mono text-white">
                  {result.positionSize.toFixed(6)} {asset}
                </span>
              </div>
              <div className="flex justify-between">
                <span className="text-muted-foreground">Position Value</span>
                <span className="font-mono text-white">
                  ${result.positionValue.toLocaleString("en-US", { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
                </span>
              </div>
              <div className="flex justify-between">
                <span className="text-muted-foreground">% of Portfolio</span>
                <span className={`font-mono ${result.capitalPct > 25 ? "text-red-400" : "text-white"}`}>
                  {result.capitalPct.toFixed(1)}%
                </span>
              </div>
            </div>

            {!result.canAfford && (
              <div className="flex items-center gap-1.5 text-[10px] text-yellow-400 mt-2">
                <AlertTriangle className="h-3 w-3" />
                Insufficient available capital (${availableCapital.toFixed(0)} available)
              </div>
            )}
            {result.capitalPct > 25 && (
              <div className="flex items-center gap-1.5 text-[10px] text-red-400 mt-1">
                <AlertTriangle className="h-3 w-3" />
                Position exceeds 25% exposure limit — consider reducing risk or widening stop
              </div>
            )}
          </div>
        )}
      </CardContent>
    </Card>
  );
}
