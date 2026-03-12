// =============================================================================
// src/app/(app)/layout.tsx — Shared layout with sidebar navigation
// =============================================================================

"use client";

import { useEffect, useState } from "react";
import { Sidebar } from "@/components/layout/sidebar";
import { Footer } from "@/components/layout/footer";
import { ToastProvider } from "@/components/ui/toast";
import { NotificationProvider } from "@/hooks/use-notifications";
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
  const [isMobile, setIsMobile] = useState(false);
  const [mobileOpen, setMobileOpen] = useState(false);

  // Detect mobile viewport
  useEffect(() => {
    const mq = window.matchMedia("(max-width: 768px)");
    const handler = (e: MediaQueryListEvent | MediaQueryList) => {
      setIsMobile(e.matches);
      if (e.matches) setMobileOpen(false);
    };
    handler(mq);
    mq.addEventListener("change", handler);
    return () => mq.removeEventListener("change", handler);
  }, []);

  return (
    <NotificationProvider>
    <ToastProvider>
      <div className="min-h-screen bg-background">
        {/* Mobile overlay */}
        {isMobile && mobileOpen && (
          <div
            className="fixed inset-0 z-30 bg-black/50 backdrop-blur-sm"
            onClick={() => setMobileOpen(false)}
          />
        )}

        <Sidebar
          collapsed={isMobile ? !mobileOpen : collapsed}
          onToggle={isMobile ? () => setMobileOpen((p) => !p) : toggle}
          connected={connected}
          mobile={isMobile}
          mobileOpen={mobileOpen}
        />

        <div
          className={cn(
            "flex min-h-screen flex-col transition-all duration-200",
            isMobile ? "ml-0" : collapsed ? "ml-16" : "ml-60"
          )}
        >
          {/* Mobile hamburger */}
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

          <main className="flex-1">{children}</main>
          <Footer />
        </div>
      </div>
    </ToastProvider>
    </NotificationProvider>
  );
}
