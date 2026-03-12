// =============================================================================
// src/app/(app)/layout.tsx — Shared layout with sidebar navigation
//
// Responsive: <768px overlay sidebar, 768-1024px collapsed, >1024px user choice
// =============================================================================

"use client";

import { useEffect, useState } from "react";
import { Sidebar } from "@/components/layout/sidebar";
import { Footer } from "@/components/layout/footer";
import { ToastProvider } from "@/components/ui/toast";
import { NotificationProvider } from "@/hooks/use-notifications";
import { NotificationToastContainer } from "@/components/ui/notification-toast";
import { LocaleProvider } from "@/hooks/use-locale";
import { useBackendHealth } from "@/hooks/use-jarvis";
import { useSidebar } from "@/hooks/use-sidebar";
import { cn } from "@/lib/utils";

export default function AppLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  const { connected } = useBackendHealth();
  const { collapsed, toggle } = useSidebar();
  const [isMobile, setIsMobile] = useState(false); // <768px
  const [isTablet, setIsTablet] = useState(false); // 768-1023px
  const [mobileOpen, setMobileOpen] = useState(false);

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
      <div className="min-h-screen bg-background overflow-x-hidden">
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
            isMobile ? "ml-0" : sidebarCollapsed ? "ml-16" : "ml-60"
          )}
        >
          {/* Mobile hamburger button */}
          {isMobile && (
            <button
              onClick={() => setMobileOpen(true)}
              className="fixed top-3 left-3 z-20 flex h-8 w-8 items-center justify-center rounded-lg bg-card border border-border/50 text-muted-foreground hover:text-white"
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

          <main className="flex-1 w-full max-w-full">{children}</main>
          <Footer />
        </div>
      </div>
    </ToastProvider>
    </NotificationProvider>
    </LocaleProvider>
  );
}
