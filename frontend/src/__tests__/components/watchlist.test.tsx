import { render, screen, fireEvent } from "@testing-library/react";
import { Watchlist } from "@/components/dashboard/watchlist";

describe("Watchlist", () => {
  const defaultPrices = { BTC: 65000, ETH: 3200, SOL: 145 };

  beforeEach(() => {
    localStorage.clear();
  });

  it("renders default watched assets", () => {
    render(<Watchlist prices={defaultPrices} />);
    expect(screen.getByText("BTC")).toBeInTheDocument();
    expect(screen.getByText("ETH")).toBeInTheDocument();
    expect(screen.getByText("SOL")).toBeInTheDocument();
  });

  it("shows formatted prices", () => {
    render(<Watchlist prices={defaultPrices} />);
    expect(screen.getByText("$65,000.00")).toBeInTheDocument();
  });

  it("shows Edit button", () => {
    render(<Watchlist prices={defaultPrices} />);
    expect(screen.getByText("Edit")).toBeInTheDocument();
  });

  it("toggles to Done when editing", () => {
    render(<Watchlist prices={defaultPrices} />);
    fireEvent.click(screen.getByText("Edit"));
    expect(screen.getByText("Done")).toBeInTheDocument();
  });

  it("shows add buttons in edit mode for available assets", () => {
    render(<Watchlist prices={defaultPrices} />);
    fireEvent.click(screen.getByText("Edit"));
    // Should show + buttons for assets not in watchlist (SPY, GLD, OIL, etc.)
    const addButtons = screen.getAllByText(/SPY|GLD|OIL/);
    expect(addButtons.length).toBeGreaterThan(0);
  });

  it("shows signal badges when signals provided", () => {
    const signals = [{ asset: "BTC", direction: "LONG" as const, confidence: 0.8 }];
    render(<Watchlist prices={defaultPrices} signals={signals} />);
    expect(screen.getByText("LONG")).toBeInTheDocument();
  });

  it("handles empty prices gracefully", () => {
    render(<Watchlist prices={{}} />);
    // Should still render the component without crashing
    expect(screen.getByText("BTC")).toBeInTheDocument();
  });
});
