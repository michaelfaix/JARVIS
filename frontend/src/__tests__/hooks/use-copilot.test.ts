import { renderHook, act } from "@testing-library/react";
import { useCoPilot } from "@/hooks/use-copilot";
import type { CoPilotInput } from "@/hooks/use-copilot";

// Mock supabase
jest.mock("@/lib/supabase/client", () => ({
  createClient: () => ({}),
}));

const baseInput: CoPilotInput = {
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
  candles: [],
};

describe("useCoPilot", () => {
  beforeEach(() => {
    localStorage.clear();
    jest.useFakeTimers();
  });

  afterEach(() => {
    jest.useRealTimers();
  });

  it("initializes with default confidence", () => {
    const { result } = renderHook(() => useCoPilot(baseInput));
    expect(typeof result.current.state.confidence).toBe("number");
    expect(result.current.state.confidence).toBeGreaterThan(0);
    expect(result.current.state.confidence).toBeLessThanOrEqual(1);
  });

  it("initializes with riskReward", () => {
    const { result } = renderHook(() => useCoPilot(baseInput));
    expect(result.current.state.riskReward).toHaveProperty("ratio");
    expect(result.current.state.riskReward).toHaveProperty("rating");
    expect(result.current.state.riskReward.ratio).toBeGreaterThan(0);
  });

  it("initializes with empty messages", () => {
    const { result } = renderHook(() => useCoPilot(baseInput));
    expect(result.current.state.messages).toEqual([]);
  });

  it("defaults to moderate risk profile", () => {
    const { result } = renderHook(() => useCoPilot(baseInput));
    expect(result.current.state.riskProfile).toBe("moderate");
  });

  it("can send a message and receive a response", () => {
    const { result } = renderHook(() => useCoPilot(baseInput));

    act(() => {
      result.current.sendMessage("Analyze chart");
    });

    // User message added immediately
    expect(result.current.state.messages.length).toBeGreaterThanOrEqual(1);
    expect(result.current.state.messages[0].role).toBe("user");
    expect(result.current.state.messages[0].content).toBe("Analyze chart");

    // Typing indicator should be on
    expect(result.current.state.isTyping).toBe(true);

    // Fast-forward to get response
    act(() => {
      jest.advanceTimersByTime(2000);
    });

    // Should have assistant response now
    expect(result.current.state.isTyping).toBe(false);
    expect(result.current.state.messages.length).toBe(2);
    expect(result.current.state.messages[1].role).toBe("assistant");
  });

  it("can change risk profile", () => {
    const { result } = renderHook(() => useCoPilot(baseInput));

    act(() => {
      result.current.setRiskProfile("aggressive");
    });

    expect(result.current.state.riskProfile).toBe("aggressive");
  });

  it("can clear history", () => {
    const { result } = renderHook(() => useCoPilot(baseInput));

    act(() => {
      result.current.sendMessage("test");
    });

    act(() => {
      jest.advanceTimersByTime(2000);
    });

    expect(result.current.state.messages.length).toBeGreaterThan(0);

    act(() => {
      result.current.clearHistory();
    });

    expect(result.current.state.messages).toEqual([]);
  });

  it("computes higher confidence in RISK_ON than CRISIS", () => {
    const { result: riskOn } = renderHook(() => useCoPilot(baseInput));
    const { result: crisis } = renderHook(() =>
      useCoPilot({ ...baseInput, regime: "CRISIS" })
    );
    expect(riskOn.current.state.confidence).toBeGreaterThan(crisis.current.state.confidence);
  });
});
