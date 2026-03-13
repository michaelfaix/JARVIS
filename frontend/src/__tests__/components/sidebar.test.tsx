// =============================================================================
// Tests: Sidebar component — Navigation links and active state
// =============================================================================

import React from "react";
import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { Sidebar } from "@/components/layout/sidebar";

// Mock next/navigation
let mockPathname = "/";
jest.mock("next/navigation", () => ({
  usePathname: () => mockPathname,
}));

// Mock next/link
jest.mock("next/link", () => {
  return function MockLink({
    children,
    href,
    ...props
  }: {
    children: React.ReactNode;
    href: string;
    [key: string]: unknown;
  }) {
    return (
      <a href={href} {...props}>
        {children}
      </a>
    );
  };
});

// Mock useAuth
const mockSignOut = jest.fn();
jest.mock("@/hooks/use-auth", () => ({
  useAuth: () => ({
    user: { id: "u1", email: "test@jarvis.com" },
    loading: false,
    signOut: mockSignOut,
  }),
}));

// Mock useLocale
jest.mock("@/hooks/use-locale", () => ({
  useLocale: () => ({
    t: (key: string) => {
      const map: Record<string, string> = {
        nav_dashboard: "Dashboard",
        nav_charts: "Charts",
        nav_signals: "Signals",
        nav_portfolio: "Portfolio",
        nav_risk_guardian: "Risk Guardian",
        nav_opportunity_radar: "Radar",
        nav_strategy_lab: "Strategy Lab",
        nav_ai_chat: "AI Chat",
        nav_markets: "Markets",
        nav_trade_journal: "Journal",
        nav_price_alerts: "Alerts",
        nav_calendar: "Calendar",
        nav_leaderboard: "Leaderboard",
        nav_social_trading: "Social",
        nav_settings: "Settings",
        nav_sign_out: "Sign Out",
        common_api_connected: "Connected",
        common_offline: "Offline",
      };
      return map[key] ?? key;
    },
    locale: "en",
    setLocale: jest.fn(),
  }),
}));

// Mock Separator
jest.mock("@/components/ui/separator", () => ({
  Separator: ({ className }: { className?: string }) => (
    <hr className={className} />
  ),
}));

describe("Sidebar", () => {
  const defaultProps = {
    collapsed: false,
    onToggle: jest.fn(),
    connected: true,
  };

  beforeEach(() => {
    mockPathname = "/";
    jest.clearAllMocks();
  });

  it("renders all 15 navigation links", () => {
    render(<Sidebar {...defaultProps} />);

    const expectedPaths = [
      "/",
      "/charts",
      "/signals",
      "/portfolio",
      "/risk",
      "/radar",
      "/strategy-lab",
      "/chat",
      "/markets",
      "/journal",
      "/alerts",
      "/calendar",
      "/leaderboard",
      "/social",
      "/settings",
    ];

    const links = screen.getAllByRole("link");
    const hrefs = links.map((l) => l.getAttribute("href"));
    for (const path of expectedPaths) {
      expect(hrefs).toContain(path);
    }
    expect(links.length).toBeGreaterThanOrEqual(15);
  });

  it("renders as 44px icon-only sidebar when collapsed", () => {
    const { container } = render(<Sidebar {...defaultProps} collapsed={true} />);
    const aside = container.querySelector("aside");
    expect(aside).toBeInTheDocument();
    expect(aside?.className).toContain("w-[44px]");
  });

  it("renders as 220px expanded sidebar when not collapsed", () => {
    const { container } = render(<Sidebar {...defaultProps} collapsed={false} />);
    const aside = container.querySelector("aside");
    expect(aside).toBeInTheDocument();
    expect(aside?.className).toContain("w-[220px]");
  });

  it("shows navigation labels when expanded", () => {
    render(<Sidebar {...defaultProps} collapsed={false} />);
    expect(screen.getByText("Dashboard")).toBeInTheDocument();
    expect(screen.getByText("Charts")).toBeInTheDocument();
  });

  it("hides navigation labels when collapsed", () => {
    render(<Sidebar {...defaultProps} collapsed={true} />);
    expect(screen.queryByText("Dashboard")).not.toBeInTheDocument();
    expect(screen.queryByText("Charts")).not.toBeInTheDocument();
  });

  it("shows navigation labels on mobile when open", () => {
    render(<Sidebar {...defaultProps} mobile={true} mobileOpen={true} />);
    expect(screen.getByText("Dashboard")).toBeInTheDocument();
    expect(screen.getByText("Charts")).toBeInTheDocument();
    expect(screen.getByText("Signals")).toBeInTheDocument();
    expect(screen.getByText("Portfolio")).toBeInTheDocument();
    expect(screen.getByText("Settings")).toBeInTheDocument();
  });

  it("marks the active route with aria-current", () => {
    mockPathname = "/signals";
    render(<Sidebar {...defaultProps} />);

    const activeLink = screen.getByRole("link", { current: "page" });
    expect(activeLink).toHaveAttribute("href", "/signals");
  });

  it("applies active styling to current route with cyan", () => {
    mockPathname = "/portfolio";
    render(<Sidebar {...defaultProps} />);

    const activeLink = screen.getByRole("link", { current: "page" });
    expect(activeLink.className).toContain("cyan");
  });

  it("shows connection indicator as green when connected", () => {
    const { container } = render(
      <Sidebar {...defaultProps} connected={true} />
    );
    const dot = container.querySelector(".bg-hud-green");
    expect(dot).toBeInTheDocument();
  });

  it("shows connection indicator as red when disconnected", () => {
    const { container } = render(
      <Sidebar {...defaultProps} connected={false} />
    );
    const dot = container.querySelector(".bg-hud-red");
    expect(dot).toBeInTheDocument();
  });

  it("shows user email on mobile overlay", () => {
    render(<Sidebar {...defaultProps} mobile={true} mobileOpen={true} />);
    expect(screen.getByText("test@jarvis.com")).toBeInTheDocument();
  });

  it("calls signOut when sign out button is clicked (mobile)", async () => {
    const user = userEvent.setup();
    render(<Sidebar {...defaultProps} mobile={true} mobileOpen={true} />);

    const signOutButton = screen.getByText("Sign Out").closest("button");
    expect(signOutButton).toBeInTheDocument();

    await user.click(signOutButton!);
    expect(mockSignOut).toHaveBeenCalledTimes(1);
  });

  it("returns null on mobile when not open", () => {
    const { container } = render(
      <Sidebar {...defaultProps} mobile={true} mobileOpen={false} />
    );
    expect(container.querySelector("aside")).not.toBeInTheDocument();
  });

  it("renders on mobile when open with 240px width", () => {
    const { container } = render(
      <Sidebar {...defaultProps} mobile={true} mobileOpen={true} />
    );
    const aside = container.querySelector("aside");
    expect(aside).toBeInTheDocument();
    expect(aside?.className).toContain("w-60");
  });

  it("shows JARVIS branding logo", () => {
    render(<Sidebar {...defaultProps} />);
    expect(screen.getByText("J")).toBeInTheDocument();
  });

  it("shows tooltip titles when collapsed (icon-only)", () => {
    render(<Sidebar {...defaultProps} collapsed={true} />);
    const dashboardLink = screen.getAllByRole("link").find(l => l.getAttribute("href") === "/");
    expect(dashboardLink).toHaveAttribute("title", "Dashboard");
  });
});
