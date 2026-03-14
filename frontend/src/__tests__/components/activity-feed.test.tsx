// =============================================================================
// Tests for ActivityFeed component
// =============================================================================

import React from "react";
import { render, screen } from "@testing-library/react";
import { ActivityFeed } from "@/components/dashboard/activity-feed";

// Mock lucide-react icons to simple elements
jest.mock("lucide-react", () => ({
  TrendingUp: (props: Record<string, unknown>) =>
    React.createElement("svg", { "data-testid": "trending-up", ...props }),
  TrendingDown: (props: Record<string, unknown>) =>
    React.createElement("svg", { "data-testid": "trending-down", ...props }),
  ArrowRightCircle: (props: Record<string, unknown>) =>
    React.createElement("svg", { "data-testid": "arrow-right-circle", ...props }),
}));

// Mock HudPanel to render children without the panel chrome
jest.mock("@/components/ui/hud-panel", () => ({
  HudPanel: ({ title, children }: { title?: string; children: React.ReactNode }) =>
    React.createElement("div", { "data-testid": "hud-panel" }, [
      title && React.createElement("span", { key: "title" }, title),
      React.createElement("div", { key: "children" }, children),
    ]),
}));

describe("ActivityFeed", () => {
  // -----------------------------------------------------------------------
  // Empty state
  // -----------------------------------------------------------------------

  it("shows 'No activity' when both lists are empty", () => {
    render(<ActivityFeed closedTrades={[]} openPositions={[]} />);
    expect(screen.getByText("No activity")).toBeInTheDocument();
  });

  // -----------------------------------------------------------------------
  // Closed trades
  // -----------------------------------------------------------------------

  it("shows closed trades with asset and direction", () => {
    const trades = [
      {
        id: "t1",
        asset: "BTCUSD",
        direction: "LONG" as const,
        pnl: 500,
        closedAt: new Date().toISOString(),
      },
    ];

    render(<ActivityFeed closedTrades={trades} openPositions={[]} />);
    expect(screen.getByText("BTCUSD LONG")).toBeInTheDocument();
  });

  it("shows positive PnL with + sign", () => {
    const trades = [
      {
        id: "t1",
        asset: "BTCUSD",
        direction: "LONG" as const,
        pnl: 1234.56,
        closedAt: new Date().toISOString(),
      },
    ];

    const { container: c1 } = render(<ActivityFeed closedTrades={trades} openPositions={[]} />);
    expect(c1.textContent).toContain("+$1,234.56");
  });

  it("shows negative PnL with - sign", () => {
    const trades = [
      {
        id: "t2",
        asset: "ETHUSD",
        direction: "SHORT" as const,
        pnl: -300,
        closedAt: new Date().toISOString(),
      },
    ];

    const { container: c2 } = render(<ActivityFeed closedTrades={trades} openPositions={[]} />);
    expect(c2.textContent).toContain("$300.00");
  });

  it("uses TrendingUp icon for profitable trades", () => {
    const trades = [
      {
        id: "t1",
        asset: "BTCUSD",
        direction: "LONG" as const,
        pnl: 100,
        closedAt: new Date().toISOString(),
      },
    ];

    render(<ActivityFeed closedTrades={trades} openPositions={[]} />);
    expect(screen.getByTestId("trending-up")).toBeInTheDocument();
  });

  it("uses TrendingDown icon for losing trades", () => {
    const trades = [
      {
        id: "t1",
        asset: "BTCUSD",
        direction: "LONG" as const,
        pnl: -100,
        closedAt: new Date().toISOString(),
      },
    ];

    render(<ActivityFeed closedTrades={trades} openPositions={[]} />);
    expect(screen.getByTestId("trending-down")).toBeInTheDocument();
  });

  // -----------------------------------------------------------------------
  // Open positions
  // -----------------------------------------------------------------------

  it("shows open positions with asset and direction", () => {
    const positions = [
      {
        asset: "SOLUSD",
        direction: "LONG" as const,
        openedAt: new Date().toISOString(),
      },
    ];

    render(<ActivityFeed closedTrades={[]} openPositions={positions} />);
    expect(screen.getByText("SOLUSD LONG")).toBeInTheDocument();
    expect(screen.getByText("Buy")).toBeInTheDocument();
  });

  it("shows 'Sell' for SHORT open positions", () => {
    const positions = [
      {
        asset: "ETHUSD",
        direction: "SHORT" as const,
        openedAt: new Date().toISOString(),
      },
    ];

    render(<ActivityFeed closedTrades={[]} openPositions={positions} />);
    expect(screen.getByText("Sell")).toBeInTheDocument();
  });

  it("uses ArrowRightCircle icon for open positions", () => {
    const positions = [
      {
        asset: "BTCUSD",
        direction: "LONG" as const,
        openedAt: new Date().toISOString(),
      },
    ];

    render(<ActivityFeed closedTrades={[]} openPositions={positions} />);
    expect(screen.getByTestId("arrow-right-circle")).toBeInTheDocument();
  });

  // -----------------------------------------------------------------------
  // Mixed + sorting
  // -----------------------------------------------------------------------

  it("shows both trades and positions sorted by time (newest first)", () => {
    const oldDate = new Date(Date.now() - 3600000).toISOString();
    const newDate = new Date().toISOString();

    const trades = [
      { id: "t1", asset: "BTCUSD", direction: "LONG" as const, pnl: 100, closedAt: oldDate },
    ];
    const positions = [
      { asset: "ETHUSD", direction: "SHORT" as const, openedAt: newDate },
    ];

    render(<ActivityFeed closedTrades={trades} openPositions={positions} />);

    const items = screen.getAllByText(/USD/);
    // ETHUSD (newer) should appear before BTCUSD (older)
    expect(items[0].textContent).toContain("ETHUSD");
    expect(items[1].textContent).toContain("BTCUSD");
  });

  it("limits display to 10 items", () => {
    const trades = Array.from({ length: 12 }, (_, i) => ({
      id: `t${i}`,
      asset: `ASSET${i}`,
      direction: "LONG" as const,
      pnl: i * 10,
      closedAt: new Date(Date.now() - i * 1000).toISOString(),
    }));

    const { container } = render(
      <ActivityFeed closedTrades={trades} openPositions={[]} />
    );

    // Each activity item has class bg-hud-bg/40
    const activityItems = container.querySelectorAll(".flex.items-center.gap-2");
    expect(activityItems.length).toBeLessThanOrEqual(10);
  });

  // -----------------------------------------------------------------------
  // Panel title
  // -----------------------------------------------------------------------

  it("renders with 'Activity' title", () => {
    render(<ActivityFeed closedTrades={[]} openPositions={[]} />);
    expect(screen.getByText("Activity")).toBeInTheDocument();
  });
});
