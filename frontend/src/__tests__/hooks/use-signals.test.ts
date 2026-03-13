import { renderHook, waitFor } from "@testing-library/react";
import { useSignals } from "@/hooks/use-signals";

// Mock the API
jest.mock("@/lib/api", () => ({
  batchPredict: jest.fn().mockRejectedValue(new Error("Backend offline")),
  WS_BASE: "ws://localhost:8000/api/v1/stream",
}));

// Mock signal stream (WebSocket)
jest.mock("@/hooks/use-signal-stream", () => ({
  useSignalStream: () => ({ streamSignals: [], wsConnected: false }),
}));

describe("useSignals", () => {
  beforeEach(() => {
    jest.clearAllMocks();
    jest.useFakeTimers();
  });

  afterEach(() => {
    jest.useRealTimers();
  });

  it("starts in loading state", () => {
    const { result } = renderHook(() => useSignals("RISK_ON", 60000));
    expect(result.current.loading).toBe(true);
  });

  it("returns signals array", () => {
    const { result } = renderHook(() => useSignals("RISK_ON", 60000));
    expect(Array.isArray(result.current.signals)).toBe(true);
  });

  it("provides a refresh function", () => {
    const { result } = renderHook(() => useSignals("RISK_ON", 60000));
    expect(typeof result.current.refresh).toBe("function");
  });

  it("falls back to local signals when backend is offline", async () => {
    const prices = { BTC: 65000, ETH: 3200, SOL: 145, SPY: 520, GLD: 215, OIL: 78 };
    const priceHistory = {
      BTC: [64000, 64500, 65000, 65200, 65100, 65000],
      ETH: [3100, 3150, 3200, 3180, 3200, 3200],
      SOL: [140, 142, 144, 145, 143, 145],
      SPY: [515, 517, 519, 520, 518, 520],
      GLD: [212, 213, 214, 215, 214, 215],
      OIL: [76, 77, 78, 77, 78, 78],
    };

    const { result } = renderHook(() => useSignals("RISK_ON", 60000, prices, priceHistory));

    await waitFor(() => {
      expect(result.current.loading).toBe(false);
    });

    expect(result.current.backendOnline).toBe(false);
    expect(result.current.signals.length).toBeGreaterThan(0);

    // Verify signal structure
    const sig = result.current.signals[0];
    expect(sig).toHaveProperty("id");
    expect(sig).toHaveProperty("asset");
    expect(sig).toHaveProperty("direction");
    expect(sig).toHaveProperty("entry");
    expect(sig).toHaveProperty("stopLoss");
    expect(sig).toHaveProperty("takeProfit");
    expect(sig).toHaveProperty("confidence");
    expect(["LONG", "SHORT"]).toContain(sig.direction);
  });

  it("local signals have confidence between 0.1 and 0.95", async () => {
    const prices = { BTC: 65000 };
    const priceHistory = { BTC: [64000, 64500, 65000, 65200, 65100, 65000] };

    const { result } = renderHook(() => useSignals("RISK_ON", 60000, prices, priceHistory));

    await waitFor(() => {
      expect(result.current.loading).toBe(false);
    });

    for (const sig of result.current.signals) {
      expect(sig.confidence).toBeGreaterThanOrEqual(0.1);
      expect(sig.confidence).toBeLessThanOrEqual(0.95);
    }
  });

  it("reports wsConnected status", () => {
    const { result } = renderHook(() => useSignals("RISK_ON", 60000));
    expect(typeof result.current.wsConnected).toBe("boolean");
  });
});
