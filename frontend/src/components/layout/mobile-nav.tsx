// =============================================================================
// src/components/layout/mobile-nav.tsx — Fixed bottom tab bar for mobile
// =============================================================================

"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import {
  LayoutDashboard,
  CandlestickChart,
  Radio,
  PieChart,
  Settings,
} from "lucide-react";
import { cn } from "@/lib/utils";

const tabs = [
  { href: "/", label: "Dashboard", icon: LayoutDashboard },
  { href: "/charts", label: "Charts", icon: CandlestickChart },
  { href: "/signals", label: "Signals", icon: Radio },
  { href: "/portfolio", label: "Portfolio", icon: PieChart },
  { href: "/settings", label: "Settings", icon: Settings },
] as const;

export function MobileNav() {
  const pathname = usePathname();

  return (
    <nav
      className={cn(
        "fixed inset-x-0 bottom-0 z-50 md:hidden",
        "bg-card/95 backdrop-blur-md border-t border-border/50",
        "pb-[env(safe-area-inset-bottom,0px)]"
      )}
    >
      <ul className="flex items-center justify-around h-14">
        {tabs.map(({ href, label, icon: Icon }) => {
          const isActive =
            href === "/" ? pathname === "/" : pathname.startsWith(href);

          return (
            <li key={href} className="flex-1">
              <Link
                href={href}
                className={cn(
                  "flex flex-col items-center justify-center gap-0.5 pt-1 relative",
                  isActive
                    ? "text-blue-400"
                    : "text-muted-foreground hover:text-foreground"
                )}
              >
                {/* Active indicator bar */}
                <span
                  className={cn(
                    "absolute top-0 left-1/2 -translate-x-1/2 h-0.5 w-6 rounded-full transition-colors",
                    isActive ? "bg-blue-400" : "bg-transparent"
                  )}
                />

                <Icon size={20} strokeWidth={isActive ? 2.2 : 1.8} />
                <span className="text-[9px] leading-tight font-medium">
                  {label}
                </span>
              </Link>
            </li>
          );
        })}
      </ul>
    </nav>
  );
}
