// =============================================================================
// Tests: lib/constants.ts — App constants validation
// =============================================================================

import {
  DEFAULT_ASSETS,
  DEFAULT_CAPITAL,
  STRATEGIES,
  TIER_LIMITS,
  FREE_ASSETS,
} from "@/lib/constants";

describe("DEFAULT_ASSETS", () => {
  it("contains at least 5 assets", () => {
    expect(DEFAULT_ASSETS.length).toBeGreaterThanOrEqual(5);
  });

  it("each asset has symbol, name, and price", () => {
    for (const asset of DEFAULT_ASSETS) {
      expect(typeof asset.symbol).toBe("string");
      expect(asset.symbol.length).toBeGreaterThan(0);
      expect(typeof asset.name).toBe("string");
      expect(asset.name.length).toBeGreaterThan(0);
      expect(typeof asset.price).toBe("number");
      expect(asset.price).toBeGreaterThan(0);
    }
  });

  it("contains BTC, ETH, and SOL", () => {
    const symbols = DEFAULT_ASSETS.map((a) => a.symbol);
    expect(symbols).toContain("BTC");
    expect(symbols).toContain("ETH");
    expect(symbols).toContain("SOL");
  });

  it("has unique symbols", () => {
    const symbols = DEFAULT_ASSETS.map((a) => a.symbol);
    const unique = new Set(symbols);
    expect(unique.size).toBe(symbols.length);
  });
});

describe("DEFAULT_CAPITAL", () => {
  it("is 100,000", () => {
    expect(DEFAULT_CAPITAL).toBe(100_000);
  });

  it("is a positive number", () => {
    expect(DEFAULT_CAPITAL).toBeGreaterThan(0);
  });
});

describe("STRATEGIES", () => {
  it("contains momentum, mean_reversion, and combined", () => {
    const ids = STRATEGIES.map((s) => s.id);
    expect(ids).toContain("momentum");
    expect(ids).toContain("mean_reversion");
    expect(ids).toContain("combined");
  });

  it("each strategy has id and label", () => {
    for (const strategy of STRATEGIES) {
      expect(typeof strategy.id).toBe("string");
      expect(typeof strategy.label).toBe("string");
      expect(strategy.id.length).toBeGreaterThan(0);
      expect(strategy.label.length).toBeGreaterThan(0);
    }
  });
});

describe("TIER_LIMITS", () => {
  it("has free, pro, and enterprise tiers", () => {
    expect(TIER_LIMITS).toHaveProperty("free");
    expect(TIER_LIMITS).toHaveProperty("pro");
    expect(TIER_LIMITS).toHaveProperty("enterprise");
  });

  it("free tier has stricter limits than pro", () => {
    expect(TIER_LIMITS.free.maxAssets).toBeLessThan(TIER_LIMITS.pro.maxAssets);
    expect(TIER_LIMITS.free.maxCapital).toBeLessThan(TIER_LIMITS.pro.maxCapital);
    expect(TIER_LIMITS.free.signalDelayMinutes).toBeGreaterThan(
      TIER_LIMITS.pro.signalDelayMinutes
    );
    expect(TIER_LIMITS.free.maxStrategies).toBeLessThan(TIER_LIMITS.pro.maxStrategies);
  });

  it("free tier does not show OOD", () => {
    expect(TIER_LIMITS.free.showOod).toBe(false);
  });

  it("pro and enterprise show OOD", () => {
    expect(TIER_LIMITS.pro.showOod).toBe(true);
    expect(TIER_LIMITS.enterprise.showOod).toBe(true);
  });

  it("enterprise has Infinity limits", () => {
    expect(TIER_LIMITS.enterprise.maxAssets).toBe(Infinity);
    expect(TIER_LIMITS.enterprise.maxCapital).toBe(Infinity);
    expect(TIER_LIMITS.enterprise.maxStrategies).toBe(Infinity);
  });
});

describe("FREE_ASSETS", () => {
  it("contains the first 3 default asset symbols", () => {
    expect(FREE_ASSETS).toHaveLength(3);
    expect(FREE_ASSETS[0]).toBe("BTC");
    expect(FREE_ASSETS[1]).toBe("ETH");
    expect(FREE_ASSETS[2]).toBe("SOL");
  });
});
