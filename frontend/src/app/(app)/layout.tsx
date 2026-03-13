// =============================================================================
// src/app/(app)/layout.tsx — Shared layout with sidebar + HUD topbar
//
// Desktop: 44px icon-only sidebar + HudTopbar above content
// Mobile: overlay sidebar + AppHeader + bottom MobileNav
// =============================================================================

"use client";

import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import { useRouter } from "next/navigation";
import { Sidebar } from "@/components/layout/sidebar";
import { Footer } from "@/components/layout/footer";
import { MobileNav } from "@/components/layout/mobile-nav";
import { ToastProvider } from "@/components/ui/toast";
import { NotificationProvider } from "@/hooks/use-notifications";
import { NotificationToastContainer } from "@/components/ui/notification-toast";
import { LocaleProvider } from "@/hooks/use-locale";
import { useBackendHealth, useSystemStatus } from "@/hooks/use-jarvis";
import { useSidebar } from "@/hooks/use-sidebar";
import { usePrices } from "@/hooks/use-prices";
import { useSentiment } from "@/hooks/use-sentiment";
import { HudTopbar } from "@/components/layout/hud-topbar";
import { AppHeader } from "@/components/layout/app-header";
import { WelcomeFlow } from "@/components/onboarding/welcome-flow";
import { ShortcutsHelp } from "@/components/ui/shortcuts-help";
import { CommandPalette } from "@/components/ui/command-palette";
import { useKeyboardShortcuts } from "@/hooks/use-keyboard-shortcuts";
import { cn } from "@/lib/utils";

export default function AppLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  const router = useRouter();
  const { connected } = useBackendHealth();
  const { collapsed, toggle } = useSidebar();
  const { regime, apiLatencyMs } = useSystemStatus(5000);
  const { wsConnected } = usePrices(5000);
  const sentimentData = useSentiment({}, {});
  const sentimentValue = sentimentData ? sentimentData[sentimentData.activeTab].sentiment.value : 50;
  const [isMobile, setIsMobile] = useState(false); // <768px
  const [isTablet, setIsTablet] = useState(false); // 768-1023px
  const [mobileOpen, setMobileOpen] = useState(false);
  const [showShortcuts, setShowShortcuts] = useState(false);
  const [showCommandPalette, setShowCommandPalette] = useState(false);

  // "G then X" navigation pattern — track last "g" press timestamp
  const gPressedAt = useRef<number>(0);

  const gotoIfG = useCallback(
    (path: string) => {
      if (Date.now() - gPressedAt.current < 1000) {
        gPressedAt.current = 0;
        router.push(path);
      }
    },
    [router],
  );

  const shortcuts = useMemo(
    () => [
      {
        key: "g",
        description: "Start navigation sequence",
        action: () => {
          gPressedAt.current = Date.now();
        },
      },
      { key: "d", description: "Dashboard (after G)", action: () => gotoIfG("/") },
      { key: "c", description: "Charts (after G)", action: () => gotoIfG("/charts") },
      { key: "s", description: "Signals (after G)", action: () => gotoIfG("/signals") },
      { key: "p", description: "Portfolio (after G)", action: () => gotoIfG("/portfolio") },
      { key: "r", description: "Risk (after G)", action: () => gotoIfG("/risk") },
      {
        key: "k",
        ctrl: true,
        description: "Open command palette",
        action: () => setShowCommandPalette((prev) => !prev),
      },
      {
        key: "?",
        shift: true,
        description: "Toggle keyboard shortcuts help",
        action: () => setShowShortcuts((prev) => !prev),
      },
      {
        key: "Escape",
        description: "Close modals",
        action: () => {
          setShowShortcuts(false);
          setShowCommandPalette(false);
        },
      },
    ],
    [gotoIfG],
  );

  useKeyboardShortcuts(shortcuts);

  // Detect viewport breakpoints
  useEffect(() => {
    const mqMobile = window.matchMedia("(max-width: 767px)");
    const mqTablet = window.matchMedia("(min-width: 768px) and (max-width: 1023px)");

    const update = () => {
      setIsMobile(mqMobile.matches);
      setIsTablet(mqTablet.matches);
      if (mqMobile.matches) setMobileOpen(false);
    };
    update();

    mqMobile.addEventListener("change", update);
    mqTablet.addEventListener("change", update);
    return () => {
      mqMobile.removeEventListener("change", update);
      mqTablet.removeEventListener("change", update);
    };
  }, []);

  // Sidebar is always collapsed on tablet, user-controlled on desktop
  const sidebarCollapsed = isMobile ? !mobileOpen : isTablet ? true : collapsed;
  const sidebarToggle = isMobile
    ? () => setMobileOpen((p) => !p)
    : isTablet
      ? () => {} // no toggle on tablet — always collapsed
      : toggle;

  return (
    <LocaleProvider>
    <NotificationProvider>
    <ToastProvider>
      <NotificationToastContainer />
      <div className="dark min-h-screen bg-hud-bg overflow-x-hidden">
        {/* Mobile overlay backdrop */}
        {isMobile && mobileOpen && (
          <div
            className="fixed inset-0 z-30 bg-black/50 backdrop-blur-sm"
            onClick={() => setMobileOpen(false)}
          />
        )}

        <Sidebar
          collapsed={sidebarCollapsed}
          onToggle={sidebarToggle}
          connected={connected}
          mobile={isMobile}
          mobileOpen={mobileOpen}
        />

        <div
          className={cn(
            "flex min-h-screen flex-col transition-all duration-200 overflow-x-hidden",
            isMobile ? "ml-0" : "ml-[44px]"
          )}
        >
          {/* HUD Topbar: desktop only */}
          <HudTopbar
            wsConnected={wsConnected}
            regime={regime}
            sentimentValue={sentimentValue}
            apiLatencyMs={apiLatencyMs}
          />

          {/* Mobile AppHeader */}
          <div className="md:hidden">
            <AppHeader title="JARVIS" subtitle="Trading Intelligence" />
          </div>

          {/* Mobile hamburger button */}
          {isMobile && (
            <button
              onClick={() => setMobileOpen(true)}
              className="fixed top-3 left-3 z-20 flex h-8 w-8 items-center justify-center rounded-lg bg-hud-panel border border-hud-border text-muted-foreground hover:text-hud-cyan"
            >
              <svg
                className="h-4 w-4"
                fill="none"
                stroke="currentColor"
                viewBox="0 0 24 24"
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={2}
                  d="M4 6h16M4 12h16M4 18h16"
                />
              </svg>
            </button>
          )}

          <main className="flex-1 w-full max-w-full pb-16 md:pb-0">{children}</main>
          <Footer />
        </div>

        {/* Mobile bottom navigation */}
        <MobileNav />
      </div>
      <WelcomeFlow />
      <CommandPalette
        open={showCommandPalette}
        onClose={() => setShowCommandPalette(false)}
        onNavigate={(path) => {
          setShowCommandPalette(false);
          router.push(path);
        }}
        onAction={(action) => {
          setShowCommandPalette(false);
          if (action === "shortcuts" || action === "show-shortcuts") setShowShortcuts(true);
        }}
      />
      <ShortcutsHelp
        open={showShortcuts}
        onClose={() => setShowShortcuts(false)}
      />
    </ToastProvider>
    </NotificationProvider>
    </LocaleProvider>
  );
}
