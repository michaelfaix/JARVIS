// =============================================================================
// Tests for PnlTicker component
// =============================================================================

import React from "react";
import { render, screen } from "@testing-library/react";
import { PnlTicker } from "@/components/dashboard/pnl-ticker";

describe("PnlTicker", () => {
  // -----------------------------------------------------------------------
  // Empty / null state
  // -----------------------------------------------------------------------

  it("returns null when positions array is empty", () => {
    const { container } = render(<PnlTicker positions={[]} prices={{}} />);
    expect(container.firstChild).toBeNull();
  });

  it("returns null when positions is undefined-like empty array", () => {
    const { container } = render(<PnlTicker positions={[]} prices={{ BTCUSD: 40000 }} />);
    expect(container.firstChild).toBeNull();
  });

  // -----------------------------------------------------------------------
  // Single position — positive PnL
  // -----------------------------------------------------------------------

  it("shows positive PnL for a LONG position when price goes up", () => {
    const positions = [
      { asset: "BTCUSD", direction: "LONG" as const, entryPrice: 40000, size: 1 },
    ];

    render(<PnlTicker positions={positions} prices={{ BTCUSD: 41000 }} />);

    // PnL = (41000 - 40000) * 1 = +$1,000.00
    expect(screen.getAllByText("+$1,000.00").length).toBeGreaterThanOrEqual(1);
  });

  it("shows positive PnL for a SHORT position when price goes down", () => {
    const positions = [
      { asset: "BTCUSD", direction: "SHORT" as const, entryPrice: 40000, size: 1 },
    ];

    render(<PnlTicker positions={positions} prices={{ BTCUSD: 39000 }} />);

    // PnL = (40000 - 39000) * 1 = +$1,000.00
    expect(screen.getAllByText("+$1,000.00").length).toBeGreaterThanOrEqual(1);
  });

  // -----------------------------------------------------------------------
  // Single position — negative PnL
  // -----------------------------------------------------------------------

  it("shows negative PnL for a LONG position when price goes down", () => {
    const positions = [
      { asset: "BTCUSD", direction: "LONG" as const, entryPrice: 40000, size: 1 },
    ];

    render(<PnlTicker positions={positions} prices={{ BTCUSD: 39500 }} />);

    // PnL = (39500 - 40000) * 1 = -500, formatted as $500.00 (no minus prefix)
    expect(screen.getAllByText("$500.00").length).toBeGreaterThanOrEqual(1);
  });

  it("shows negative PnL for a SHORT position when price goes up", () => {
    const positions = [
      { asset: "ETHUSD", direction: "SHORT" as const, entryPrice: 3000, size: 2 },
    ];

    render(<PnlTicker positions={positions} prices={{ ETHUSD: 3100 }} />);

    // PnL = (3000 - 3100) * 2 = -200, formatted as $200.00 (no minus prefix)
    expect(screen.getAllByText("$200.00").length).toBeGreaterThanOrEqual(1);
  });

  // -----------------------------------------------------------------------
  // Asset name display
  // -----------------------------------------------------------------------

  it("displays the asset name", () => {
    const positions = [
      { asset: "BTCUSD", direction: "LONG" as const, entryPrice: 40000, size: 1 },
    ];

    render(<PnlTicker positions={positions} prices={{ BTCUSD: 40000 }} />);
    expect(screen.getByText("BTCUSD")).toBeInTheDocument();
  });

  // -----------------------------------------------------------------------
  // Direction indicators
  // -----------------------------------------------------------------------

  it("shows up arrow for LONG positions", () => {
    const positions = [
      { asset: "BTCUSD", direction: "LONG" as const, entryPrice: 40000, size: 1 },
    ];

    const { container } = render(
      <PnlTicker positions={positions} prices={{ BTCUSD: 40000 }} />
    );

    // The component renders text-hud-green class for LONG direction indicator
    const greenArrow = container.querySelector(".text-hud-green");
    expect(greenArrow).toBeInTheDocument();
  });

  it("shows down arrow for SHORT positions", () => {
    const positions = [
      { asset: "BTCUSD", direction: "SHORT" as const, entryPrice: 40000, size: 1 },
    ];

    const { container } = render(
      <PnlTicker positions={positions} prices={{ BTCUSD: 40000 }} />
    );

    const redArrow = container.querySelector(".text-hud-red");
    expect(redArrow).toBeInTheDocument();
  });

  // -----------------------------------------------------------------------
  // Multiple positions + total
  // -----------------------------------------------------------------------

  it("shows total PnL across multiple positions", () => {
    const positions = [
      { asset: "BTCUSD", direction: "LONG" as const, entryPrice: 40000, size: 1 },
      { asset: "ETHUSD", direction: "LONG" as const, entryPrice: 3000, size: 10 },
    ];

    render(
      <PnlTicker
        positions={positions}
        prices={{ BTCUSD: 41000, ETHUSD: 3200 }}
      />
    );

    // BTC PnL = +$1,000, ETH PnL = +$2,000, Total = +$3,000
    // Individual
    expect(screen.getAllByText("+$1,000.00").length).toBeGreaterThanOrEqual(1);
    expect(screen.getByText("+$2,000.00")).toBeInTheDocument();
    // Total — the last "+$3,000.00" in the DOM is the total
    expect(screen.getByText("+$3,000.00")).toBeInTheDocument();
  });

  it("shows both asset names for multiple positions", () => {
    const positions = [
      { asset: "BTCUSD", direction: "LONG" as const, entryPrice: 40000, size: 1 },
      { asset: "ETHUSD", direction: "SHORT" as const, entryPrice: 3000, size: 1 },
    ];

    render(
      <PnlTicker positions={positions} prices={{ BTCUSD: 40000, ETHUSD: 3000 }} />
    );

    expect(screen.getByText("BTCUSD")).toBeInTheDocument();
    expect(screen.getByText("ETHUSD")).toBeInTheDocument();
  });

  // -----------------------------------------------------------------------
  // Fallback to entry price when no current price
  // -----------------------------------------------------------------------

  it("uses entry price when no current price is available (PnL = 0)", () => {
    const positions = [
      { asset: "BTCUSD", direction: "LONG" as const, entryPrice: 40000, size: 1 },
    ];

    render(<PnlTicker positions={positions} prices={{}} />);

    // PnL = (40000 - 40000) * 1 = +$0.00
    expect(screen.getAllByText("+$0.00").length).toBeGreaterThanOrEqual(1);
  });

  // -----------------------------------------------------------------------
  // Color classes
  // -----------------------------------------------------------------------

  it("applies green class for positive total PnL", () => {
    const positions = [
      { asset: "BTCUSD", direction: "LONG" as const, entryPrice: 40000, size: 1 },
    ];

    const { container } = render(
      <PnlTicker positions={positions} prices={{ BTCUSD: 41000 }} />
    );

    // The total PnL element should have text-hud-green
    const totalEl = container.querySelector(".font-bold.text-hud-green");
    expect(totalEl).toBeInTheDocument();
  });

  it("applies red class for negative total PnL", () => {
    const positions = [
      { asset: "BTCUSD", direction: "LONG" as const, entryPrice: 40000, size: 1 },
    ];

    const { container } = render(
      <PnlTicker positions={positions} prices={{ BTCUSD: 39000 }} />
    );

    const totalEl = container.querySelector(".font-bold.text-hud-red");
    expect(totalEl).toBeInTheDocument();
  });

  // -----------------------------------------------------------------------
  // "Open P&L" label
  // -----------------------------------------------------------------------

  it("displays 'Open P&L' label", () => {
    const positions = [
      { asset: "BTCUSD", direction: "LONG" as const, entryPrice: 40000, size: 1 },
    ];

    render(<PnlTicker positions={positions} prices={{ BTCUSD: 40000 }} />);
    // The component uses &amp; which renders as &
    expect(screen.getByText("Open P&L")).toBeInTheDocument();
  });
});
