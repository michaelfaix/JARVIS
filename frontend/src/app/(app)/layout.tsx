// =============================================================================
// src/app/(app)/layout.tsx — Shared layout with sidebar navigation
// =============================================================================

"use client";

import { Sidebar } from "@/components/layout/sidebar";
import { Footer } from "@/components/layout/footer";
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

  return (
    <div className="min-h-screen bg-background">
      <Sidebar collapsed={collapsed} onToggle={toggle} connected={connected} />
      <div
        className={cn(
          "flex min-h-screen flex-col transition-all duration-200",
          collapsed ? "ml-16" : "ml-60"
        )}
      >
        <main className="flex-1">{children}</main>
        <Footer />
      </div>
    </div>
  );
}
