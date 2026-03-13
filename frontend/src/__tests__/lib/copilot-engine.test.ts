import {
  calculateRiskReward,
  calculateConfidence,
  parseAlertFromMessage,
  generateOfflineResponse,
  type CoPilotContext,
} from "@/lib/copilot-engine";

describe("calculateRiskReward", () => {
  it("returns good rating for R:R >= 2", () => {
    const result = calculateRiskReward(1000, 2, 5);
    expect(result.ratio).toBeCloseTo(2.5);
    expect(result.rating).toBe("good");
  });

  it("returns neutral rating for R:R between 1 and 2", () => {
    const result = calculateRiskReward(1000, 3, 4);
    expect(result.ratio).toBeCloseTo(1.333, 2);
    expect(result.rating).toBe("neutral");
  });

  it("returns bad rating for R:R < 1", () => {
    const result = calculateRiskReward(1000, 5, 3);
    expect(result.ratio).toBeCloseTo(0.6);
    expect(result.rating).toBe("bad");
  });

  it("handles zero SL (no risk)", () => {
    const result = calculateRiskReward(1000, 0, 5);
    expect(result.ratio).toBe(0);
  });

  it("calculates correct risk and reward amounts", () => {
    const result = calculateRiskReward(50000, 2, 6);
    expect(result.riskAmount).toBe(1000);
    expect(result.rewardAmount).toBe(3000);
  });
});

describe("calculateConfidence", () => {
  it("returns high confidence for good conditions", () => {
    const conf = calculateConfidence(0, 0, 0.9, "RISK_ON");
    expect(conf).toBeCloseTo(0.9);
  });

  it("reduces confidence in CRISIS regime", () => {
    const normal = calculateConfidence(0, 0, 0.8, "RISK_ON");
    const crisis = calculateConfidence(0, 0, 0.8, "CRISIS");
    expect(crisis).toBeLessThan(normal);
  });

  it("reduces confidence with high ECE", () => {
    const low = calculateConfidence(0, 0, 0.8, "RISK_ON");
    const high = calculateConfidence(0.15, 0, 0.8, "RISK_ON");
    expect(high).toBeLessThan(low);
  });

  it("reduces confidence with high OOD score", () => {
    const low = calculateConfidence(0, 0, 0.8, "RISK_ON");
    const high = calculateConfidence(0, 0.8, 0.8, "RISK_ON");
    expect(high).toBeLessThan(low);
  });

  it("never exceeds 1.0", () => {
    const conf = calculateConfidence(0, 0, 1.0, "RISK_ON");
    expect(conf).toBeLessThanOrEqual(1.0);
  });

  it("returns 0 for extreme OOD", () => {
    const conf = calculateConfidence(0, 1.0, 0.8, "RISK_ON");
    expect(conf).toBe(0);
  });
});

describe("parseAlertFromMessage", () => {
  it("parses 'BTC hits $75000'", () => {
    const result = parseAlertFromMessage("Tell me when BTC hits $75000");
    expect(result).not.toBeNull();
    expect(result!.asset).toBe("BTC");
    expect(result!.targetPrice).toBe(75000);
    expect(result!.condition).toBe("above");
  });

  it("parses 'ETH drops below $3000'", () => {
    const result = parseAlertFromMessage("Alert when ETH drops below $3000");
    expect(result).not.toBeNull();
    expect(result!.asset).toBe("ETH");
    expect(result!.condition).toBe("below");
  });

  it("returns null for unknown assets", () => {
    const result = parseAlertFromMessage("Alert when XYZ hits 100");
    expect(result).toBeNull();
  });

  it("returns null for no price", () => {
    const result = parseAlertFromMessage("Tell me about BTC");
    expect(result).toBeNull();
  });

  it("handles German text", () => {
    const result = parseAlertFromMessage("Sag mir wenn BTC unter $70000 fällt");
    expect(result).not.toBeNull();
    expect(result!.condition).toBe("below");
  });
});

describe("generateOfflineResponse", () => {
  const baseCtx: CoPilotContext = {
    regime: "RISK_ON",
    ece: 0.03,
    oodScore: 0.1,
    metaUncertainty: 0.05,
    strategy: "combined",
    selectedAsset: "BTC",
    interval: "4h",
    slPercent: 2,
    tpPercent: 6,
    currentPrice: 65000,
    totalValue: 100000,
    drawdown: 2,
    positionCount: 1,
    closedTradeCount: 5,
    realizedPnl: 500,
    winRate: 60,
    signalCount: 3,
    topSignalAsset: "BTC",
    topSignalDirection: "LONG",
    topSignalConfidence: 0.8,
    patterns: [],
  };

  it("returns a non-empty string", () => {
    const response = generateOfflineResponse("Analyze chart", baseCtx, "en", "moderate");
    expect(response.length).toBeGreaterThan(0);
  });

  it("returns markdown-formatted text", () => {
    const response = generateOfflineResponse("Best Strategy?", baseCtx, "en", "moderate");
    // Should contain some markdown markers
    expect(response).toMatch(/[#*\-|]/);
  });

  it("returns German text for locale de", () => {
    const response = generateOfflineResponse("Analysiere den Chart", baseCtx, "de", "moderate");
    expect(response.length).toBeGreaterThan(0);
  });

  it("returns different responses for different prompts", () => {
    const r1 = generateOfflineResponse("Chart analysis", baseCtx, "en", "moderate");
    const r2 = generateOfflineResponse("Calculate R:R", baseCtx, "en", "moderate");
    // They should differ (different prompt types)
    expect(r1).not.toBe(r2);
  });
});
