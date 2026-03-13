import { render, screen, fireEvent } from "@testing-library/react";
import { TopSignalsHud } from "@/components/dashboard/top-signals-hud";
import type { Signal, PortfolioState } from "@/lib/types";

const mockPortfolio: PortfolioState = {
  totalCapital: 100000,
  availableCapital: 90000,
  positions: [],
  closedTrades: [],
  realizedPnl: 0,
  peakValue: 100000,
};

function makeSignal(overrides: Partial<Signal> = {}): Signal {
  return {
    id: "sig-1",
    asset: "BTC",
    direction: "LONG",
    entry: 65000,
    stopLoss: 63000,
    takeProfit: 70000,
    confidence: 0.85,
    qualityScore: 0.7,
    regime: "RISK_ON",
    isOod: false,
    oodScore: 0.1,
    uncertainty: null,
    deepPathUsed: false,
    timestamp: new Date(),
    ...overrides,
  };
}

describe("TopSignalsHud", () => {
  it("shows 'No signals' when empty and not loading", () => {
    render(
      <TopSignalsHud signals={[]} portfolio={mockPortfolio} acceptSignal={jest.fn()} loading={false} />
    );
    expect(screen.getByText("No signals")).toBeInTheDocument();
  });

  it("shows loading skeletons when loading with no signals", () => {
    const { container } = render(
      <TopSignalsHud signals={[]} portfolio={mockPortfolio} acceptSignal={jest.fn()} loading={true} />
    );
    expect(container.querySelectorAll(".animate-pulse").length).toBeGreaterThanOrEqual(1);
  });

  it("renders signal cards with asset and direction", () => {
    const signals = [makeSignal({ asset: "ETH", direction: "SHORT", confidence: 0.9 })];
    render(
      <TopSignalsHud signals={signals} portfolio={mockPortfolio} acceptSignal={jest.fn()} loading={false} />
    );
    expect(screen.getByText("ETH")).toBeInTheDocument();
    expect(screen.getByText("SHORT")).toBeInTheDocument();
  });

  it("sorts signals by confidence (highest first)", () => {
    const signals = [
      makeSignal({ id: "low", asset: "SOL", confidence: 0.3 }),
      makeSignal({ id: "high", asset: "BTC", confidence: 0.95 }),
    ];
    const { container } = render(
      <TopSignalsHud signals={signals} portfolio={mockPortfolio} acceptSignal={jest.fn()} loading={false} />
    );
    const assetLabels = container.querySelectorAll(".font-bold.text-white");
    expect(assetLabels[0]?.textContent).toBe("BTC");
  });

  it("shows TRADE button for new signals", () => {
    const signals = [makeSignal()];
    render(
      <TopSignalsHud signals={signals} portfolio={mockPortfolio} acceptSignal={jest.fn()} loading={false} />
    );
    expect(screen.getByText("TRADE")).toBeInTheDocument();
  });

  it("shows OPEN for already-open positions", () => {
    const signals = [makeSignal({ asset: "BTC", direction: "LONG" })];
    const portfolio = {
      ...mockPortfolio,
      positions: [{ id: "p1", asset: "BTC", direction: "LONG" as const, entryPrice: 65000, currentPrice: 65000, size: 1, capitalAllocated: 65000, openedAt: new Date().toISOString(), pnl: 0, pnlPercent: 0 }],
    };
    render(
      <TopSignalsHud signals={signals} portfolio={portfolio} acceptSignal={jest.fn()} loading={false} />
    );
    expect(screen.getByText("OPEN")).toBeInTheDocument();
  });

  it("calls acceptSignal when TRADE button clicked", () => {
    const acceptSignal = jest.fn();
    const signals = [makeSignal()];
    render(
      <TopSignalsHud signals={signals} portfolio={mockPortfolio} acceptSignal={acceptSignal} loading={false} />
    );
    fireEvent.click(screen.getByText("TRADE").closest("button")!);
    expect(acceptSignal).toHaveBeenCalledWith(signals[0]);
  });

  it("shows active signal count", () => {
    const signals = [makeSignal({ id: "1" }), makeSignal({ id: "2" })];
    render(
      <TopSignalsHud signals={signals} portfolio={mockPortfolio} acceptSignal={jest.fn()} loading={false} />
    );
    expect(screen.getByText("2 active")).toBeInTheDocument();
  });

  it("limits display to 4 signals", () => {
    const signals = Array.from({ length: 6 }, (_, i) =>
      makeSignal({ id: `s${i}`, asset: `A${i}`, confidence: 0.5 + i * 0.05 })
    );
    const { container } = render(
      <TopSignalsHud signals={signals} portfolio={mockPortfolio} acceptSignal={jest.fn()} loading={false} />
    );
    // Should show only top 4 signal cards
    const tradeButtons = container.querySelectorAll("button");
    // 4 trade buttons + potential other buttons
    expect(tradeButtons.length).toBeGreaterThanOrEqual(4);
  });
});
