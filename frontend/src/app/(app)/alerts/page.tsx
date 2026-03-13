// =============================================================================
// src/app/(app)/alerts/page.tsx — Price Alerts Page
// =============================================================================

"use client";

import { useEffect, useState } from "react";
import { HudPanel } from "@/components/ui/hud-panel";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Select } from "@/components/ui/select";
import { Separator } from "@/components/ui/separator";
import { useAlerts } from "@/hooks/use-alerts";
import { usePrices } from "@/hooks/use-prices";
import { DEFAULT_ASSETS } from "@/lib/constants";
import {
  Bell,
  Plus,
  Trash2,
  TrendingUp,
  TrendingDown,
  BellOff,
  CheckCircle2,
} from "lucide-react";

export default function AlertsPage() {
  const { prices } = usePrices();
  const {
    activeAlerts,
    triggeredAlerts,
    addAlert,
    removeAlert,
    clearTriggered,
    checkPrices,
    notificationPermission,
    requestPermission,
  } = useAlerts();

  const [selectedAsset, setSelectedAsset] = useState("BTC");
  const [condition, setCondition] = useState<"above" | "below">("above");
  const [targetPrice, setTargetPrice] = useState("");

  // Check prices against alerts
  useEffect(() => {
    checkPrices(prices);
  }, [prices, checkPrices]);

  const handleCreate = () => {
    const price = parseFloat(targetPrice);
    if (isNaN(price) || price <= 0) return;
    addAlert({ asset: selectedAsset, condition, targetPrice: price });
    setTargetPrice("");
  };

  const currentPrice = prices[selectedAsset] ?? 0;

  return (
    <div className="p-2 sm:p-3 md:p-4 space-y-3 max-w-3xl">
      {/* Notification Permission Banner */}
      {notificationPermission !== "granted" &&
        notificationPermission !== "unsupported" && (
          <HudPanel className="border-hud-cyan/30">
            <div className="p-3">
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-3">
                  <BellOff className="h-5 w-5 text-hud-cyan" />
                  <div>
                    <div className="text-sm font-medium text-hud-cyan font-mono">
                      Enable Browser Notifications
                    </div>
                    <div className="text-[10px] text-muted-foreground">
                      Get notified when your price alerts trigger, even when
                      you&apos;re on another tab.
                    </div>
                  </div>
                </div>
                <Button
                  variant="outline"
                  size="sm"
                  onClick={requestPermission}
                  className="gap-1 border-hud-cyan/30 text-hud-cyan hover:bg-hud-cyan/10"
                >
                  <Bell className="h-3 w-3" />
                  Enable
                </Button>
              </div>
            </div>
          </HudPanel>
        )}

      {/* Create Alert */}
      <HudPanel title="Create Alert">
        <div className="p-2.5 space-y-4">
          <div className="grid grid-cols-1 sm:grid-cols-4 gap-3 items-end">
            <div className="space-y-1.5">
              <Label className="text-[10px] text-muted-foreground font-mono">Asset</Label>
              <Select
                value={selectedAsset}
                onChange={(e) => setSelectedAsset(e.target.value)}
                className="border-hud-border bg-hud-bg font-mono"
              >
                {DEFAULT_ASSETS.map((a) => (
                  <option key={a.symbol} value={a.symbol}>
                    {a.symbol} — {a.name}
                  </option>
                ))}
              </Select>
            </div>
            <div className="space-y-1.5">
              <Label className="text-[10px] text-muted-foreground font-mono">Condition</Label>
              <Select
                value={condition}
                onChange={(e) =>
                  setCondition(e.target.value as "above" | "below")
                }
                className="border-hud-border bg-hud-bg font-mono"
              >
                <option value="above">Price Above</option>
                <option value="below">Price Below</option>
              </Select>
            </div>
            <div className="space-y-1.5">
              <Label className="text-[10px] text-muted-foreground font-mono">Target Price (USD)</Label>
              <Input
                type="number"
                value={targetPrice}
                onChange={(e) => setTargetPrice(e.target.value)}
                placeholder={currentPrice.toLocaleString()}
                className="font-mono border-hud-border bg-hud-bg"
                min={0}
                step="any"
                onKeyDown={(e) => e.key === "Enter" && handleCreate()}
              />
            </div>
            <Button onClick={handleCreate} className="gap-1 bg-hud-cyan/20 text-hud-cyan border border-hud-cyan/30 hover:bg-hud-cyan/30">
              <Plus className="h-3.5 w-3.5" />
              Add Alert
            </Button>
          </div>
          <div className="text-[10px] text-muted-foreground font-mono">
            Current {selectedAsset} price:{" "}
            <span className="font-mono text-hud-cyan">
              $
              {currentPrice.toLocaleString("en-US", {
                minimumFractionDigits: 2,
                maximumFractionDigits: 2,
              })}
            </span>
          </div>
        </div>
      </HudPanel>

      {/* Active Alerts */}
      <HudPanel title="Active Alerts">
        <div className="p-2.5">
          <div className="flex items-center justify-end mb-2">
            <Badge variant="outline" className="text-[10px] border-hud-border text-hud-cyan font-mono">
              {activeAlerts.length} active
            </Badge>
          </div>
          {activeAlerts.length === 0 ? (
            <div className="text-sm text-muted-foreground py-6 text-center font-mono">
              No active alerts. Create one above to get started.
            </div>
          ) : (
            <div className="space-y-2">
              {activeAlerts.map((alert) => {
                const current = prices[alert.asset] ?? 0;
                const distance = current > 0
                  ? alert.condition === "above"
                    ? ((alert.targetPrice - current) / current) * 100
                    : ((current - alert.targetPrice) / current) * 100
                  : 0;

                return (
                  <div
                    key={alert.id}
                    className="flex items-center gap-3 rounded bg-hud-bg/60 border border-hud-border/30 p-2.5"
                  >
                    <div
                      className={`flex h-9 w-9 items-center justify-center rounded ${
                        alert.condition === "above"
                          ? "bg-hud-green/10"
                          : "bg-hud-red/10"
                      }`}
                    >
                      {alert.condition === "above" ? (
                        <TrendingUp className="h-4 w-4 text-hud-green" />
                      ) : (
                        <TrendingDown className="h-4 w-4 text-hud-red" />
                      )}
                    </div>
                    <div className="flex-1 min-w-0">
                      <div className="flex items-center gap-2">
                        <span className="font-medium text-white text-sm font-mono">
                          {alert.asset}
                        </span>
                        <Badge
                          className={`text-[10px] ${
                            alert.condition === "above"
                              ? "bg-hud-green/20 text-hud-green border-hud-green/30"
                              : "bg-hud-red/20 text-hud-red border-hud-red/30"
                          }`}
                        >
                          {alert.condition === "above" ? "↑ Above" : "↓ Below"}
                        </Badge>
                      </div>
                      <div className="text-[10px] text-muted-foreground mt-0.5">
                        Target:{" "}
                        <span className="font-mono text-white">
                          ${alert.targetPrice.toLocaleString()}
                        </span>
                        {" · "}Current:{" "}
                        <span className="font-mono">
                          ${current.toLocaleString("en-US", { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
                        </span>
                        {" · "}
                        <span
                          className={`font-mono ${
                            distance > 0
                              ? "text-hud-amber"
                              : "text-hud-green"
                          }`}
                        >
                          {distance > 0
                            ? `${distance.toFixed(2)}% away`
                            : "Close!"}
                        </span>
                      </div>
                    </div>
                    <button
                      onClick={() => removeAlert(alert.id)}
                      className="text-muted-foreground hover:text-hud-red transition-colors p-1"
                    >
                      <Trash2 className="h-4 w-4" />
                    </button>
                  </div>
                );
              })}
            </div>
          )}
        </div>
      </HudPanel>

      {/* Triggered Alerts */}
      {triggeredAlerts.length > 0 && (
        <HudPanel title="Triggered">
          <div className="p-2.5">
            <div className="flex items-center justify-end gap-2 mb-2">
              <Badge variant="outline" className="text-[10px] border-hud-border text-hud-green font-mono">
                {triggeredAlerts.length}
              </Badge>
              <Button
                variant="outline"
                size="sm"
                onClick={clearTriggered}
                className="text-xs gap-1 border-hud-border text-muted-foreground hover:text-hud-red"
              >
                <Trash2 className="h-3 w-3" />
                Clear
              </Button>
            </div>
            <div className="space-y-2">
              {triggeredAlerts.map((alert) => (
                <div
                  key={alert.id}
                  className="flex items-center gap-3 rounded bg-hud-green/5 border border-hud-green/20 p-2.5"
                >
                  <CheckCircle2 className="h-4 w-4 text-hud-green shrink-0" />
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center gap-2">
                      <span className="font-medium text-white text-sm font-mono">
                        {alert.asset}
                      </span>
                      <span className="text-[10px] text-muted-foreground font-mono">
                        {alert.condition === "above" ? "crossed above" : "dropped below"}{" "}
                        <span className="font-mono text-white">
                          ${alert.targetPrice.toLocaleString()}
                        </span>
                      </span>
                    </div>
                    {alert.triggeredAt && (
                      <div className="text-[9px] text-muted-foreground mt-0.5 font-mono">
                        {new Date(alert.triggeredAt).toLocaleString()}
                      </div>
                    )}
                  </div>
                  <button
                    onClick={() => removeAlert(alert.id)}
                    className="text-muted-foreground hover:text-hud-red transition-colors p-1"
                  >
                    <Trash2 className="h-3 w-3" />
                  </button>
                </div>
              ))}
            </div>
          </div>
        </HudPanel>
      )}

      {/* Info */}
      <Separator className="opacity-30 border-hud-border" />
      <div className="text-[10px] text-muted-foreground space-y-1 font-mono">
        <p>
          Alerts are checked in real-time against live Binance WebSocket prices
          for crypto assets. Non-crypto assets use synthetic prices.
        </p>
        <p>
          Alerts are stored locally in your browser. Enable browser
          notifications to get alerted even when on another tab.
        </p>
      </div>
    </div>
  );
}
