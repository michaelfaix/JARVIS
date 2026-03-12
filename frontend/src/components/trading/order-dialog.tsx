// =============================================================================
// src/components/trading/order-dialog.tsx — Order placement dialog
// =============================================================================

"use client";

import React, { useState, useMemo } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Tabs, TabsList, TabsTrigger, TabsContent } from "@/components/ui/tabs";
import { Separator } from "@/components/ui/separator";
import { X, TrendingUp, TrendingDown, ShieldAlert, Target } from "lucide-react";
import type { Signal } from "@/lib/types";
import type { OrderType, NewOrder } from "@/hooks/use-orders";

// ---------------------------------------------------------------------------
// Props
// ---------------------------------------------------------------------------

interface OrderDialogProps {
  signal: Signal;
  currentPrice: number;
  availableCapital: number;
  onPlaceOrder: (order: NewOrder) => void;
  onClose: () => void;
}

// ---------------------------------------------------------------------------
// Capital % presets
// ---------------------------------------------------------------------------

const CAPITAL_PRESETS = [
  { label: "5%", value: 0.05 },
  { label: "10%", value: 0.1 },
  { label: "25%", value: 0.25 },
  { label: "50%", value: 0.5 },
];

// ---------------------------------------------------------------------------
// Component
// ---------------------------------------------------------------------------

export function OrderDialog({
  signal,
  currentPrice,
  availableCapital,
  onPlaceOrder,
  onClose,
}: OrderDialogProps) {
  const [orderType, setOrderType] = useState<OrderType>("market");
  const [capitalPercent, setCapitalPercent] = useState(0.1);
  const [limitPrice, setLimitPrice] = useState(
    signal.direction === "LONG"
      ? (currentPrice * 0.995).toFixed(2)
      : (currentPrice * 1.005).toFixed(2)
  );
  const [stopPrice, setStopPrice] = useState(
    signal.direction === "LONG"
      ? (currentPrice * 1.01).toFixed(2)
      : (currentPrice * 0.99).toFixed(2)
  );

  const capitalAllocated = Math.min(
    availableCapital * capitalPercent,
    availableCapital
  );

  const entryPrice = useMemo(() => {
    if (orderType === "market") return currentPrice;
    return parseFloat(limitPrice) || currentPrice;
  }, [orderType, limitPrice, currentPrice]);

  const size = entryPrice > 0 ? capitalAllocated / entryPrice : 0;

  // Risk/reward calculation
  const slDistance = Math.abs(entryPrice - signal.stopLoss);
  const tpDistance = Math.abs(signal.takeProfit - entryPrice);
  const riskReward = slDistance > 0 ? tpDistance / slDistance : 0;
  const riskAmount = slDistance * size;
  const rewardAmount = tpDistance * size;

  function handleSubmit() {
    if (capitalAllocated < 1 || size <= 0) return;

    const order: NewOrder = {
      asset: signal.asset,
      direction: signal.direction,
      type: orderType,
      size,
      capitalAllocated,
      stopLoss: signal.stopLoss,
      takeProfit: signal.takeProfit,
    };

    if (orderType === "market") {
      order.limitPrice = currentPrice;
    } else if (orderType === "limit") {
      order.limitPrice = parseFloat(limitPrice) || currentPrice;
    } else if (orderType === "stop_limit") {
      order.stopPrice = parseFloat(stopPrice) || currentPrice;
      order.limitPrice = parseFloat(limitPrice) || currentPrice;
    }

    onPlaceOrder(order);
    onClose();
  }

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 backdrop-blur-sm" role="dialog" aria-modal="true" aria-labelledby="order-dialog-title">
      <Card className="w-full max-w-lg mx-4 bg-card border-border/50 shadow-2xl max-h-[90vh] overflow-y-auto">
        <CardHeader className="pb-3">
          <div className="flex items-center justify-between">
            <CardTitle id="order-dialog-title" className="text-sm font-medium flex items-center gap-2">
              {signal.direction === "LONG" ? (
                <TrendingUp className="h-4 w-4 text-green-400" />
              ) : (
                <TrendingDown className="h-4 w-4 text-red-400" />
              )}
              Trade {signal.asset}
              <Badge
                className={
                  signal.direction === "LONG"
                    ? "bg-green-500/20 text-green-400 border-green-500/30"
                    : "bg-red-500/20 text-red-400 border-red-500/30"
                }
              >
                {signal.direction}
              </Badge>
            </CardTitle>
            <Button
              variant="ghost"
              size="sm"
              className="h-7 w-7 p-0 text-muted-foreground hover:text-white"
              onClick={onClose}
            >
              <X className="h-4 w-4" />
            </Button>
          </div>
          <div className="text-xs text-muted-foreground">
            Current: $
            {currentPrice.toLocaleString("en-US", {
              minimumFractionDigits: 2,
              maximumFractionDigits: 2,
            })}{" "}
            | Confidence: {(signal.confidence * 100).toFixed(0)}%
          </div>
        </CardHeader>

        <CardContent className="space-y-4">
          {/* Order Type Tabs */}
          <Tabs defaultValue="market">
            <TabsList className="w-full">
              <TabsTrigger
                value="market"
                className="flex-1 text-xs"
                onClick={() => setOrderType("market")}
              >
                Market
              </TabsTrigger>
              <TabsTrigger
                value="limit"
                className="flex-1 text-xs"
                onClick={() => setOrderType("limit")}
              >
                Limit
              </TabsTrigger>
              <TabsTrigger
                value="stop_limit"
                className="flex-1 text-xs"
                onClick={() => setOrderType("stop_limit")}
              >
                Stop Limit
              </TabsTrigger>
            </TabsList>

            {/* Market Order */}
            <TabsContent value="market">
              <div className="space-y-3 pt-2">
                <div className="rounded-lg bg-background/50 border border-border/30 p-3">
                  <div className="text-xs text-muted-foreground mb-1">
                    Execution Price
                  </div>
                  <div className="text-lg font-bold font-mono text-white">
                    $
                    {currentPrice.toLocaleString("en-US", {
                      minimumFractionDigits: 2,
                      maximumFractionDigits: 2,
                    })}
                  </div>
                  <div className="text-[10px] text-muted-foreground">
                    Fills immediately at market price
                  </div>
                </div>
              </div>
            </TabsContent>

            {/* Limit Order */}
            <TabsContent value="limit">
              <div className="space-y-3 pt-2">
                <div>
                  <Label className="text-xs text-muted-foreground">
                    Limit Price
                  </Label>
                  <Input
                    type="number"
                    step="0.01"
                    value={limitPrice}
                    onChange={(e) => setLimitPrice(e.target.value)}
                    className="mt-1 h-9 font-mono text-sm"
                  />
                  <div className="text-[10px] text-muted-foreground mt-1">
                    {signal.direction === "LONG"
                      ? "Order fills when price drops to or below limit"
                      : "Order fills when price rises to or above limit"}
                  </div>
                </div>
              </div>
            </TabsContent>

            {/* Stop Limit Order */}
            <TabsContent value="stop_limit">
              <div className="space-y-3 pt-2">
                <div>
                  <Label className="text-xs text-muted-foreground">
                    Stop Price (trigger)
                  </Label>
                  <Input
                    type="number"
                    step="0.01"
                    value={stopPrice}
                    onChange={(e) => setStopPrice(e.target.value)}
                    className="mt-1 h-9 font-mono text-sm"
                  />
                </div>
                <div>
                  <Label className="text-xs text-muted-foreground">
                    Limit Price (execution)
                  </Label>
                  <Input
                    type="number"
                    step="0.01"
                    value={limitPrice}
                    onChange={(e) => setLimitPrice(e.target.value)}
                    className="mt-1 h-9 font-mono text-sm"
                  />
                </div>
                <div className="text-[10px] text-muted-foreground">
                  Order activates at stop price, then fills at limit price
                </div>
              </div>
            </TabsContent>
          </Tabs>

          <Separator className="opacity-50" />

          {/* Capital Allocation */}
          <div>
            <Label className="text-xs text-muted-foreground">
              Capital Allocation
            </Label>
            <div className="flex gap-2 mt-2">
              {CAPITAL_PRESETS.map((preset) => (
                <Button
                  key={preset.value}
                  variant={capitalPercent === preset.value ? "default" : "outline"}
                  size="sm"
                  className="flex-1 h-8 text-xs"
                  onClick={() => setCapitalPercent(preset.value)}
                >
                  {preset.label}
                </Button>
              ))}
            </div>
            <div className="flex justify-between mt-2 text-xs text-muted-foreground">
              <span>
                $
                {capitalAllocated.toLocaleString("en-US", {
                  maximumFractionDigits: 0,
                })}
              </span>
              <span>
                of $
                {availableCapital.toLocaleString("en-US", {
                  maximumFractionDigits: 0,
                })}{" "}
                available
              </span>
            </div>
          </div>

          {/* Size display */}
          <div className="rounded-lg bg-background/50 border border-border/30 p-3">
            <div className="flex justify-between text-xs">
              <span className="text-muted-foreground">Size</span>
              <span className="font-mono text-white">{size.toFixed(4)}</span>
            </div>
            <div className="flex justify-between text-xs mt-1">
              <span className="text-muted-foreground">Entry</span>
              <span className="font-mono text-white">
                $
                {entryPrice.toLocaleString("en-US", {
                  minimumFractionDigits: 2,
                  maximumFractionDigits: 2,
                })}
              </span>
            </div>
          </div>

          <Separator className="opacity-50" />

          {/* Risk Preview */}
          <div className="space-y-2">
            <div className="flex items-center gap-2 text-xs font-medium text-muted-foreground">
              <ShieldAlert className="h-3.5 w-3.5" />
              Risk Preview
            </div>
            <div className="grid grid-cols-2 gap-2">
              <div className="rounded-lg bg-red-500/5 border border-red-500/20 p-2">
                <div className="text-[10px] text-red-400 mb-0.5">Stop Loss</div>
                <div className="text-xs font-mono text-red-400">
                  $
                  {signal.stopLoss.toLocaleString("en-US", {
                    minimumFractionDigits: 2,
                    maximumFractionDigits: 2,
                  })}
                </div>
                <div className="text-[10px] font-mono text-red-400/70">
                  -${riskAmount.toFixed(2)} risk
                </div>
              </div>
              <div className="rounded-lg bg-green-500/5 border border-green-500/20 p-2">
                <div className="text-[10px] text-green-400 mb-0.5">
                  Take Profit
                </div>
                <div className="text-xs font-mono text-green-400">
                  $
                  {signal.takeProfit.toLocaleString("en-US", {
                    minimumFractionDigits: 2,
                    maximumFractionDigits: 2,
                  })}
                </div>
                <div className="text-[10px] font-mono text-green-400/70">
                  +${rewardAmount.toFixed(2)} reward
                </div>
              </div>
            </div>
            <div className="flex items-center justify-center gap-2 py-1">
              <Target className="h-3.5 w-3.5 text-blue-400" />
              <span className="text-xs font-mono text-blue-400">
                R:R {riskReward.toFixed(2)}
              </span>
            </div>
          </div>

          {/* Place Order Button */}
          <Button
            className={`w-full h-10 font-medium ${
              signal.direction === "LONG"
                ? "bg-green-600 hover:bg-green-700 text-white"
                : "bg-red-600 hover:bg-red-700 text-white"
            }`}
            onClick={handleSubmit}
            disabled={capitalAllocated < 1 || size <= 0}
          >
            {orderType === "market"
              ? `Place Market ${signal.direction}`
              : orderType === "limit"
              ? `Place Limit ${signal.direction}`
              : `Place Stop-Limit ${signal.direction}`}
          </Button>
        </CardContent>
      </Card>
    </div>
  );
}
