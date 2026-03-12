// =============================================================================
// src/app/(app)/settings/page.tsx — Settings Page
// =============================================================================

"use client";

import { useEffect, useState } from "react";
import { useSearchParams } from "next/navigation";
import { AppHeader } from "@/components/layout/app-header";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Select } from "@/components/ui/select";
import { Switch } from "@/components/ui/switch";
import { Button } from "@/components/ui/button";
import { Separator } from "@/components/ui/separator";
import { Badge } from "@/components/ui/badge";
import { useToast } from "@/components/ui/toast";
import { useSettings } from "@/hooks/use-settings";
import { usePortfolio } from "@/hooks/use-portfolio";
import { useProfile } from "@/hooks/use-profile";
import { useSubscription } from "@/hooks/use-subscription";
import { useLocale } from "@/hooks/use-locale";
import { PricingModal } from "@/components/upgrade/pricing-modal";
import { STRATEGIES, DEFAULT_ASSETS, TIER_LIMITS, FREE_ASSETS } from "@/lib/constants";
import { Settings, RotateCcw, Save, Lock, Crown, CreditCard } from "lucide-react";

const TIER_COLORS: Record<string, string> = {
  free: "bg-zinc-600/20 text-zinc-400 border-zinc-500/30",
  pro: "bg-blue-600/20 text-blue-400 border-blue-500/30",
  enterprise: "bg-purple-600/20 text-purple-400 border-purple-500/30",
};

export default function SettingsPage() {
  const { settings, update, reset } = useSettings();
  const { resetPortfolio } = usePortfolio();
  const { tier, isPro } = useProfile();
  const { manageSubscription, loading: subLoading } = useSubscription();
  const { toast } = useToast();
  const { locale, setLocale, t } = useLocale();
  const searchParams = useSearchParams();
  const limits = TIER_LIMITS[tier];
  const [capitalInput, setCapitalInput] = useState("");
  const [pricingOpen, setPricingOpen] = useState(false);

  useEffect(() => {
    setCapitalInput(settings.paperCapital.toString());
  }, [settings.paperCapital]);

  // Show toast on upgrade redirect
  useEffect(() => {
    const upgraded = searchParams.get("upgraded");
    if (upgraded === "true") {
      toast("success", "Upgraded! Your new plan is now active.");
    } else if (upgraded === "mock") {
      toast("warning", "Stripe not configured — this was a mock upgrade.");
    }
    // Only run on mount
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const handleCapitalSave = () => {
    const value = parseFloat(capitalInput);
    if (!isNaN(value) && value > 0) {
      const capped = Math.min(value, limits.maxCapital);
      update({ paperCapital: capped });
      resetPortfolio(capped);
    }
  };

  useEffect(() => {
    const saved = localStorage.getItem("jarvis-theme");
    if (saved === "light" || saved === "dark") {
      update({ theme: saved });
      document.documentElement.classList.toggle("dark", saved === "dark");
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const handleThemeToggle = () => {
    const newTheme = settings.theme === "dark" ? "light" : "dark";
    update({ theme: newTheme });
    localStorage.setItem("jarvis-theme", newTheme);
    if (typeof document !== "undefined") {
      document.documentElement.classList.toggle("dark", newTheme === "dark");
    }
  };

  return (
    <>
      <AppHeader title={t('settings_title')} subtitle={t('settings_configuration')} />
      <div className="p-3 sm:p-4 md:p-6 space-y-4 md:space-y-6 max-w-3xl">
        {/* Subscription Info */}
        <Card className="bg-card/50 border-border/50">
          <CardContent className="pt-4 pb-3 px-4">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-3">
                <div className={`flex h-10 w-10 items-center justify-center rounded-xl ${
                  isPro ? "bg-blue-600/20" : "bg-muted"
                }`}>
                  <Crown className={`h-5 w-5 ${isPro ? "text-blue-400" : "text-muted-foreground"}`} />
                </div>
                <div>
                  <div className="flex items-center gap-2">
                    <span className="text-sm font-semibold text-white capitalize">{tier} Plan</span>
                    <Badge className={`text-[10px] ${TIER_COLORS[tier]}`}>
                      {tier.toUpperCase()}
                    </Badge>
                  </div>
                  <div className="text-xs text-muted-foreground">
                    {isPro
                      ? t('settings_all_features_unlocked')
                      : `${limits.maxAssets} assets, $${limits.maxCapital.toLocaleString()} capital, ${limits.signalDelayMinutes}min signal delay`}
                  </div>
                </div>
              </div>
              <div className="flex items-center gap-2">
                {isPro ? (
                  <Button
                    variant="outline"
                    size="sm"
                    className="gap-1.5 text-xs"
                    onClick={manageSubscription}
                    disabled={subLoading}
                  >
                    <CreditCard className="h-3 w-3" />
                    {subLoading ? `${t('common_loading')}...` : t('settings_manage_subscription')}
                  </Button>
                ) : (
                  <Button
                    size="sm"
                    className="gap-1.5 text-xs bg-blue-600 hover:bg-blue-700 text-white"
                    onClick={() => setPricingOpen(true)}
                  >
                    <Crown className="h-3 w-3" />
                    {t('settings_upgrade')}
                  </Button>
                )}
              </div>
            </div>
          </CardContent>
        </Card>

        {/* Paper Trading */}
        <Card className="bg-card/50 border-border/50">
          <CardHeader className="pb-3">
            <CardTitle className="text-sm font-medium text-muted-foreground flex items-center gap-2">
              <Settings className="h-4 w-4" />
              {t('settings_paper_trading')}
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-6">
            {/* Capital */}
            <div className="space-y-2">
              <Label>{t('settings_starting_capital')}</Label>
              <div className="flex gap-2">
                <Input
                  type="number"
                  value={capitalInput}
                  onChange={(e) => setCapitalInput(e.target.value)}
                  className="max-w-[200px] font-mono"
                  min={1000}
                  max={limits.maxCapital === Infinity ? undefined : limits.maxCapital}
                  step={1000}
                />
                <Button
                  variant="outline"
                  size="sm"
                  onClick={handleCapitalSave}
                  className="gap-1"
                >
                  <Save className="h-3 w-3" />
                  {t('settings_apply')}
                </Button>
              </div>
              <p className="text-xs text-muted-foreground">
                {t('settings_capital_hint')}
                {!isPro && (
                  <span className="text-yellow-400">
                    {" "}Max ${limits.maxCapital.toLocaleString()} on {tier} plan.
                  </span>
                )}
              </p>
            </div>

            <Separator className="opacity-30" />

            {/* Strategy */}
            <div className="space-y-2">
              <Label>{t('settings_active_strategy')}</Label>
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
                {t('settings_strategy_hint')}
              </p>
            </div>

            <Separator className="opacity-30" />

            {/* Tracked Assets */}
            <div className="space-y-2">
              <Label>{t('settings_tracked_assets')}</Label>
              <div className="flex flex-wrap gap-2">
                {DEFAULT_ASSETS.map((asset) => {
                  const isTracked = settings.trackedAssets.includes(
                    asset.symbol
                  );
                  const isLocked = !isPro && !FREE_ASSETS.includes(asset.symbol);
                  return (
                    <Badge
                      key={asset.symbol}
                      variant={isTracked && !isLocked ? "default" : "outline"}
                      className={`transition-colors ${
                        isLocked
                          ? "opacity-50 cursor-not-allowed"
                          : isTracked
                          ? "bg-blue-600 hover:bg-blue-700 cursor-pointer"
                          : "hover:bg-muted cursor-pointer"
                      }`}
                      onClick={() => {
                        if (isLocked) return;
                        const next = isTracked
                          ? settings.trackedAssets.filter(
                              (s) => s !== asset.symbol
                            )
                          : [...settings.trackedAssets, asset.symbol];
                        update({ trackedAssets: next });
                      }}
                    >
                      {isLocked && <Lock className="h-2.5 w-2.5 mr-1" />}
                      {asset.symbol}
                    </Badge>
                  );
                })}
              </div>
              <p className="text-xs text-muted-foreground">
                {t('settings_tracked_assets_hint')}
                {!isPro && (
                  <span className="text-yellow-400">
                    {" "}Free plan: {limits.maxAssets} assets only.
                  </span>
                )}
              </p>
            </div>
          </CardContent>
        </Card>

        {/* Appearance */}
        <Card className="bg-card/50 border-border/50">
          <CardHeader className="pb-3">
            <CardTitle className="text-sm font-medium text-muted-foreground">
              {t('settings_appearance')}
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="flex items-center justify-between">
              <div>
                <Label>{t('settings_dark_mode')}</Label>
                <p className="text-xs text-muted-foreground mt-0.5">
                  {t('settings_dark_mode_hint')}
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
                <Label>{t('settings_poll_interval')}</Label>
                <p className="text-xs text-muted-foreground mt-0.5">
                  {t('settings_poll_interval_hint')}
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

        {/* Language */}
        <Card className="bg-card/50 border-border/50">
          <CardHeader className="pb-3">
            <CardTitle className="text-sm font-medium text-muted-foreground">
              {t('settings_language')}
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="flex items-center gap-3">
              <button
                onClick={() => setLocale('en')}
                className={`flex items-center gap-2 rounded-lg px-4 py-2.5 text-sm font-medium transition-colors border ${
                  locale === 'en'
                    ? 'border-blue-500 bg-blue-600/20 text-blue-400'
                    : 'border-border/50 text-muted-foreground hover:bg-muted hover:text-foreground'
                }`}
              >
                <span className="text-base">&#x1F1EC;&#x1F1E7;</span>
                English
              </button>
              <button
                onClick={() => setLocale('de')}
                className={`flex items-center gap-2 rounded-lg px-4 py-2.5 text-sm font-medium transition-colors border ${
                  locale === 'de'
                    ? 'border-blue-500 bg-blue-600/20 text-blue-400'
                    : 'border-border/50 text-muted-foreground hover:bg-muted hover:text-foreground'
                }`}
              >
                <span className="text-base">&#x1F1E9;&#x1F1EA;</span>
                Deutsch
              </button>
            </div>
          </CardContent>
        </Card>

        {/* Danger Zone */}
        <Card className="bg-card/50 border-red-500/20">
          <CardHeader className="pb-3">
            <CardTitle className="text-sm font-medium text-red-400">
              {t('settings_danger_zone')}
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-white">{t('settings_reset_all')}</p>
                <p className="text-xs text-muted-foreground">
                  {t('settings_reset_all_hint')}
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
                {t('settings_reset')}
              </Button>
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Pricing Modal */}
      <PricingModal open={pricingOpen} onClose={() => setPricingOpen(false)} />
    </>
  );
}
