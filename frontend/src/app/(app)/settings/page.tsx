// =============================================================================
// src/app/(app)/settings/page.tsx — Settings Page
// =============================================================================

"use client";

import { useEffect, useState } from "react";
import { AppHeader } from "@/components/layout/app-header";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Select } from "@/components/ui/select";
import { Switch } from "@/components/ui/switch";
import { Button } from "@/components/ui/button";
import { Separator } from "@/components/ui/separator";
import { Badge } from "@/components/ui/badge";
import { useSettings } from "@/hooks/use-settings";
import { usePortfolio } from "@/hooks/use-portfolio";
import { STRATEGIES, DEFAULT_ASSETS } from "@/lib/constants";
import { Settings, RotateCcw, Save } from "lucide-react";

export default function SettingsPage() {
  const { settings, update, reset } = useSettings();
  const { resetPortfolio } = usePortfolio();
  const [capitalInput, setCapitalInput] = useState("");

  useEffect(() => {
    setCapitalInput(settings.paperCapital.toString());
  }, [settings.paperCapital]);

  const handleCapitalSave = () => {
    const value = parseFloat(capitalInput);
    if (!isNaN(value) && value > 0) {
      update({ paperCapital: value });
      resetPortfolio(value);
    }
  };

  const handleThemeToggle = () => {
    const newTheme = settings.theme === "dark" ? "light" : "dark";
    update({ theme: newTheme });
    // Update the HTML class
    if (typeof document !== "undefined") {
      document.documentElement.classList.toggle("dark", newTheme === "dark");
    }
  };

  return (
    <>
      <AppHeader title="Settings" subtitle="Configuration" />
      <div className="p-6 space-y-6 max-w-3xl">
        {/* Paper Trading */}
        <Card className="bg-card/50 border-border/50">
          <CardHeader className="pb-3">
            <CardTitle className="text-sm font-medium text-muted-foreground flex items-center gap-2">
              <Settings className="h-4 w-4" />
              Paper Trading
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-6">
            {/* Capital */}
            <div className="space-y-2">
              <Label>Starting Capital (USD)</Label>
              <div className="flex gap-2">
                <Input
                  type="number"
                  value={capitalInput}
                  onChange={(e) => setCapitalInput(e.target.value)}
                  className="max-w-[200px] font-mono"
                  min={1000}
                  step={1000}
                />
                <Button
                  variant="outline"
                  size="sm"
                  onClick={handleCapitalSave}
                  className="gap-1"
                >
                  <Save className="h-3 w-3" />
                  Apply
                </Button>
              </div>
              <p className="text-xs text-muted-foreground">
                Resets portfolio to the new capital amount. All open positions
                will be closed.
              </p>
            </div>

            <Separator className="opacity-30" />

            {/* Strategy */}
            <div className="space-y-2">
              <Label>Active Strategy</Label>
              <Select
                value={settings.strategy}
                onChange={(e) =>
                  update({
                    strategy: e.target.value as typeof settings.strategy,
                  })
                }
                className="max-w-[200px]"
              >
                {STRATEGIES.map((s) => (
                  <option key={s.id} value={s.id}>
                    {s.label}
                  </option>
                ))}
              </Select>
              <p className="text-xs text-muted-foreground">
                Determines how signals are generated on the Signals page.
              </p>
            </div>

            <Separator className="opacity-30" />

            {/* Tracked Assets */}
            <div className="space-y-2">
              <Label>Tracked Assets</Label>
              <div className="flex flex-wrap gap-2">
                {DEFAULT_ASSETS.map((asset) => {
                  const isTracked = settings.trackedAssets.includes(
                    asset.symbol
                  );
                  return (
                    <Badge
                      key={asset.symbol}
                      variant={isTracked ? "default" : "outline"}
                      className={`cursor-pointer transition-colors ${
                        isTracked
                          ? "bg-blue-600 hover:bg-blue-700"
                          : "hover:bg-muted"
                      }`}
                      onClick={() => {
                        const next = isTracked
                          ? settings.trackedAssets.filter(
                              (s) => s !== asset.symbol
                            )
                          : [...settings.trackedAssets, asset.symbol];
                        update({ trackedAssets: next });
                      }}
                    >
                      {asset.symbol}
                    </Badge>
                  );
                })}
              </div>
              <p className="text-xs text-muted-foreground">
                Click to toggle. These assets appear on Signals and Radar pages.
              </p>
            </div>
          </CardContent>
        </Card>

        {/* Appearance */}
        <Card className="bg-card/50 border-border/50">
          <CardHeader className="pb-3">
            <CardTitle className="text-sm font-medium text-muted-foreground">
              Appearance
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="flex items-center justify-between">
              <div>
                <Label>Dark Mode</Label>
                <p className="text-xs text-muted-foreground mt-0.5">
                  Toggle between dark and light theme
                </p>
              </div>
              <Switch
                checked={settings.theme === "dark"}
                onCheckedChange={handleThemeToggle}
              />
            </div>

            <Separator className="opacity-30" />

            <div className="flex items-center justify-between">
              <div>
                <Label>Poll Interval</Label>
                <p className="text-xs text-muted-foreground mt-0.5">
                  How often to fetch new data from the backend
                </p>
              </div>
              <Select
                value={settings.pollIntervalMs.toString()}
                onChange={(e) =>
                  update({ pollIntervalMs: parseInt(e.target.value) })
                }
                className="w-32"
              >
                <option value="5000">5 sec</option>
                <option value="10000">10 sec</option>
                <option value="30000">30 sec</option>
                <option value="60000">1 min</option>
              </Select>
            </div>
          </CardContent>
        </Card>

        {/* Danger Zone */}
        <Card className="bg-card/50 border-red-500/20">
          <CardHeader className="pb-3">
            <CardTitle className="text-sm font-medium text-red-400">
              Danger Zone
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-white">Reset All Settings</p>
                <p className="text-xs text-muted-foreground">
                  Restore defaults for capital, strategy, theme, and tracked
                  assets
                </p>
              </div>
              <Button
                variant="outline"
                size="sm"
                className="text-red-400 border-red-500/30 hover:bg-red-500/10 gap-1"
                onClick={() => {
                  reset();
                  resetPortfolio();
                }}
              >
                <RotateCcw className="h-3 w-3" />
                Reset
              </Button>
            </div>
          </CardContent>
        </Card>
      </div>
    </>
  );
}
