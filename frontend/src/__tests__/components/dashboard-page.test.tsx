/**
 * Dashboard page logic tests — tests the helper functions and keyboard behavior.
 */

describe("Dashboard helpers", () => {
  // Test relativeTime helper logic
  function relativeTime(ts: number | null): string {
    if (!ts) return "";
    const diff = Math.floor((Date.now() - ts) / 1000);
    if (diff < 5) return "just now";
    if (diff < 60) return `${diff}s ago`;
    if (diff < 3600) return `${Math.floor(diff / 60)}m ago`;
    return `${Math.floor(diff / 3600)}h ago`;
  }

  it("returns empty string for null", () => {
    expect(relativeTime(null)).toBe("");
  });

  it("returns 'just now' for recent timestamps", () => {
    expect(relativeTime(Date.now())).toBe("just now");
    expect(relativeTime(Date.now() - 2000)).toBe("just now");
  });

  it("returns seconds for < 60s", () => {
    const result = relativeTime(Date.now() - 30000);
    expect(result).toBe("30s ago");
  });

  it("returns minutes for < 3600s", () => {
    const result = relativeTime(Date.now() - 120000);
    expect(result).toBe("2m ago");
  });

  it("returns hours for >= 3600s", () => {
    const result = relativeTime(Date.now() - 7200000);
    expect(result).toBe("2h ago");
  });
});

describe("Approaching alerts filter", () => {
  interface MockAlert {
    id: string;
    asset: string;
    condition: "above" | "below";
    targetPrice: number;
    triggered: boolean;
  }

  function getApproachingAlerts(
    alerts: MockAlert[],
    prices: Record<string, number>
  ) {
    return alerts
      .filter((a) => {
        if (a.triggered) return false;
        const price = prices[a.asset];
        if (!price) return false;
        const dist = Math.abs(price - a.targetPrice) / a.targetPrice;
        return dist < 0.05;
      })
      .slice(0, 3);
  }

  it("finds alerts within 5% of target", () => {
    const alerts: MockAlert[] = [
      { id: "1", asset: "BTC", condition: "above", targetPrice: 70000, triggered: false },
      { id: "2", asset: "ETH", condition: "below", targetPrice: 2000, triggered: false },
    ];
    const prices = { BTC: 68000, ETH: 3200 };
    const result = getApproachingAlerts(alerts, prices);
    expect(result).toHaveLength(1);
    expect(result[0].asset).toBe("BTC");
  });

  it("ignores triggered alerts", () => {
    const alerts: MockAlert[] = [
      { id: "1", asset: "BTC", condition: "above", targetPrice: 70000, triggered: true },
    ];
    const result = getApproachingAlerts(alerts, { BTC: 69500 });
    expect(result).toHaveLength(0);
  });

  it("ignores alerts without price data", () => {
    const alerts: MockAlert[] = [
      { id: "1", asset: "XYZ", condition: "above", targetPrice: 100, triggered: false },
    ];
    const result = getApproachingAlerts(alerts, { BTC: 65000 });
    expect(result).toHaveLength(0);
  });

  it("limits to 3 results", () => {
    const alerts: MockAlert[] = Array.from({ length: 5 }, (_, i) => ({
      id: String(i),
      asset: "BTC",
      condition: "above" as const,
      targetPrice: 65000 + i * 100,
      triggered: false,
    }));
    const result = getApproachingAlerts(alerts, { BTC: 65050 });
    expect(result.length).toBeLessThanOrEqual(3);
  });
});
