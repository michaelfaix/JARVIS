// =============================================================================
// src/app/(app)/alerts/page.tsx — Price Alerts Page
// =============================================================================

"use client";

import { useEffect, useState } from "react";
import { AppHeader } from "@/components/layout/app-header";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
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
  BellRing,
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
    <>
      <AppHeader title="Price Alerts" subtitle="Notifications" />
      <div className="p-3 sm:p-4 md:p-6 space-y-4 md:space-y-6 max-w-3xl">
        {/* Notification Permission Banner */}
        {notificationPermission !== "granted" &&
          notificationPermission !== "unsupported" && (
            <Card className="bg-blue-600/10 border-blue-500/30">
              <CardContent className="pt-4 pb-3 px-4">
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-3">
                    <BellOff className="h-5 w-5 text-blue-400" />
                    <div>
                      <div className="text-sm font-medium text-white">
                        Enable Browser Notifications
                      </div>
                      <div className="text-xs text-muted-foreground">
                        Get notified when your price alerts trigger, even when
                        you&apos;re on another tab.
                      </div>
                    </div>
                  </div>
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={requestPermission}
                    className="gap-1 border-blue-500/30 text-blue-400 hover:bg-blue-500/10"
                  >
                    <Bell className="h-3 w-3" />
                    Enable
                  </Button>
                </div>
              </CardContent>
            </Card>
          )}

        {/* Create Alert */}
        <Card className="bg-card/50 border-border/50">
          <CardHeader className="pb-3">
            <CardTitle className="text-sm font-medium text-muted-foreground flex items-center gap-2">
              <Plus className="h-4 w-4" />
              Create Alert
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="grid grid-cols-1 sm:grid-cols-4 gap-3 items-end">
              <div className="space-y-1.5">
                <Label className="text-xs">Asset</Label>
                <Select
                  value={selectedAsset}
                  onChange={(e) => setSelectedAsset(e.target.value)}
                >
                  {DEFAULT_ASSETS.map((a) => (
                    <option key={a.symbol} value={a.symbol}>
                      {a.symbol} — {a.name}
                    </option>
                  ))}
                </Select>
              </div>
              <div className="space-y-1.5">
                <Label className="text-xs">Condition</Label>
                <Select
                  value={condition}
                  onChange={(e) =>
                    setCondition(e.target.value as "above" | "below")
                  }
                >
                  <option value="above">Price Above</option>
                  <option value="below">Price Below</option>
                </Select>
              </div>
              <div className="space-y-1.5">
                <Label className="text-xs">Target Price (USD)</Label>
                <Input
                  type="number"
                  value={targetPrice}
                  onChange={(e) => setTargetPrice(e.target.value)}
                  placeholder={currentPrice.toLocaleString()}
                  className="font-mono"
                  min={0}
                  step="any"
                  onKeyDown={(e) => e.key === "Enter" && handleCreate()}
                />
              </div>
              <Button onClick={handleCreate} className="gap-1">
                <Plus className="h-3.5 w-3.5" />
                Add Alert
              </Button>
            </div>
            <div className="text-xs text-muted-foreground">
              Current {selectedAsset} price:{" "}
              <span className="font-mono text-white">
                $
                {currentPrice.toLocaleString("en-US", {
                  minimumFractionDigits: 2,
                  maximumFractionDigits: 2,
                })}
              </span>
            </div>
          </CardContent>
        </Card>

        {/* Active Alerts */}
        <Card className="bg-card/50 border-border/50">
          <CardHeader className="pb-3">
            <CardTitle className="text-sm font-medium text-muted-foreground flex items-center gap-2">
              <BellRing className="h-4 w-4" />
              Active Alerts
              <Badge variant="outline" className="ml-auto text-[10px]">
                {activeAlerts.length} active
              </Badge>
            </CardTitle>
          </CardHeader>
          <CardContent>
            {activeAlerts.length === 0 ? (
              <div className="text-sm text-muted-foreground py-6 text-center">
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
                      className="flex items-center gap-3 rounded-lg bg-background/50 p-3"
                    >
                      <div
                        className={`flex h-9 w-9 items-center justify-center rounded-lg ${
                          alert.condition === "above"
                            ? "bg-green-500/10"
                            : "bg-red-500/10"
                        }`}
                      >
                        {alert.condition === "above" ? (
                          <TrendingUp className="h-4 w-4 text-green-400" />
                        ) : (
                          <TrendingDown className="h-4 w-4 text-red-400" />
                        )}
                      </div>
                      <div className="flex-1 min-w-0">
                        <div className="flex items-center gap-2">
                          <span className="font-medium text-white text-sm">
                            {alert.asset}
                          </span>
                          <Badge
                            className={`text-[10px] ${
                              alert.condition === "above"
                                ? "bg-green-500/20 text-green-400 border-green-500/30"
                                : "bg-red-500/20 text-red-400 border-red-500/30"
                            }`}
                          >
                            {alert.condition === "above" ? "↑ Above" : "↓ Below"}
                          </Badge>
                        </div>
                        <div className="text-xs text-muted-foreground mt-0.5">
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
                                ? "text-yellow-400"
                                : "text-green-400"
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
                        className="text-muted-foreground hover:text-red-400 transition-colors p-1"
                      >
                        <Trash2 className="h-4 w-4" />
                      </button>
                    </div>
                  );
                })}
              </div>
            )}
          </CardContent>
        </Card>

        {/* Triggered Alerts */}
        {triggeredAlerts.length > 0 && (
          <Card className="bg-card/50 border-border/50">
            <CardHeader className="pb-3">
              <CardTitle className="text-sm font-medium text-muted-foreground flex items-center gap-2">
                <CheckCircle2 className="h-4 w-4 text-green-400" />
                Triggered
                <Badge variant="outline" className="ml-auto text-[10px]">
                  {triggeredAlerts.length}
                </Badge>
                <Button
                  variant="outline"
                  size="sm"
                  onClick={clearTriggered}
                  className="ml-2 text-xs gap-1"
                >
                  <Trash2 className="h-3 w-3" />
                  Clear
                </Button>
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="space-y-2">
                {triggeredAlerts.map((alert) => (
                  <div
                    key={alert.id}
                    className="flex items-center gap-3 rounded-lg bg-green-500/5 border border-green-500/10 p-3"
                  >
                    <CheckCircle2 className="h-4 w-4 text-green-400 shrink-0" />
                    <div className="flex-1 min-w-0">
                      <div className="flex items-center gap-2">
                        <span className="font-medium text-white text-sm">
                          {alert.asset}
                        </span>
                        <span className="text-xs text-muted-foreground">
                          {alert.condition === "above" ? "crossed above" : "dropped below"}{" "}
                          <span className="font-mono text-white">
                            ${alert.targetPrice.toLocaleString()}
                          </span>
                        </span>
                      </div>
                      {alert.triggeredAt && (
                        <div className="text-[10px] text-muted-foreground mt-0.5">
                          {new Date(alert.triggeredAt).toLocaleString()}
                        </div>
                      )}
                    </div>
                    <button
                      onClick={() => removeAlert(alert.id)}
                      className="text-muted-foreground hover:text-red-400 transition-colors p-1"
                    >
                      <Trash2 className="h-3 w-3" />
                    </button>
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>
        )}

        {/* Info */}
        <Separator className="opacity-30" />
        <div className="text-xs text-muted-foreground space-y-1">
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
    </>
  );
}
