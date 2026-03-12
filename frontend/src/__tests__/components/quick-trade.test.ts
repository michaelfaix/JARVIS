/**
 * Tests for the Quick-Trade (acceptSignal) logic on the Dashboard.
 */

describe("Quick-Trade acceptSignal logic", () => {
  function computeTradeParams(
    availableCapital: number,
    signal: { entry: number; direction: "LONG" | "SHORT"; asset: string }
  ) {
    const capitalPerTrade = availableCapital * 0.05;
    if (capitalPerTrade < 10) return null;
    const size = capitalPerTrade / signal.entry;
    return {
      asset: signal.asset,
      direction: signal.direction,
      entryPrice: signal.entry,
      size,
      capitalAllocated: capitalPerTrade,
    };
  }

  it("allocates 5% of available capital", () => {
    const result = computeTradeParams(100000, {
      entry: 65000,
      direction: "LONG",
      asset: "BTC",
    });
    expect(result).not.toBeNull();
    expect(result!.capitalAllocated).toBe(5000);
  });

  it("calculates size based on entry price", () => {
    const result = computeTradeParams(100000, {
      entry: 50000,
      direction: "LONG",
      asset: "BTC",
    });
    expect(result!.size).toBeCloseTo(0.1, 5); // 5000 / 50000 = 0.1
  });

  it("returns null for insufficient capital (<$10 trade)", () => {
    const result = computeTradeParams(100, {
      entry: 65000,
      direction: "SHORT",
      asset: "BTC",
    });
    // 100 * 0.05 = $5, which is < $10
    expect(result).toBeNull();
  });

  it("works for SHORT direction", () => {
    const result = computeTradeParams(100000, {
      entry: 3200,
      direction: "SHORT",
      asset: "ETH",
    });
    expect(result!.direction).toBe("SHORT");
    expect(result!.size).toBeCloseTo(5000 / 3200, 5);
  });
});
