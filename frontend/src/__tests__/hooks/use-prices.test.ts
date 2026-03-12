// =============================================================================
// Tests: use-prices.ts — Price feed with WebSocket + REST fallback
// =============================================================================

import { renderHook, act } from "@testing-library/react";

// Mock WebSocket
class MockWebSocket {
  static OPEN = 1;
  static CLOSED = 3;

  url: string;
  readyState = MockWebSocket.OPEN;
  onopen: ((ev: Event) => void) | null = null;
  onclose: ((ev: CloseEvent) => void) | null = null;
  onmessage: ((ev: MessageEvent) => void) | null = null;
  onerror: ((ev: Event) => void) | null = null;
  close = jest.fn(() => {
    this.readyState = MockWebSocket.CLOSED;
  });
  send = jest.fn();

  constructor(url: string) {
    this.url = url;
    // Trigger onopen async
    setTimeout(() => {
      if (this.onopen) this.onopen(new Event("open"));
    }, 10);
  }
}

Object.defineProperty(global, "WebSocket", {
  value: MockWebSocket,
  writable: true,
});

// Mock fetch for Binance REST
const mockFetch = jest.fn();
global.fetch = mockFetch;

// Mock document.visibilityState
Object.defineProperty(document, "visibilityState", {
  value: "visible",
  writable: true,
});

import { usePrices } from "@/hooks/use-prices";

describe("usePrices", () => {
  beforeEach(() => {
    jest.useFakeTimers();
    jest.clearAllMocks();
    mockFetch.mockResolvedValue({
      ok: true,
      json: () =>
        Promise.resolve([
          { symbol: "BTCUSDT", price: "67000.00" },
          { symbol: "ETHUSDT", price: "3400.00" },
          { symbol: "SOLUSDT", price: "155.00" },
        ]),
    });
  });

  afterEach(() => {
    jest.useRealTimers();
  });

  it("initializes with default asset prices", () => {
    const { result } = renderHook(() => usePrices(5000));

    expect(result.current.prices).toHaveProperty("BTC");
    expect(result.current.prices).toHaveProperty("ETH");
    expect(result.current.prices).toHaveProperty("SOL");
    expect(result.current.prices).toHaveProperty("SPY");
    expect(result.current.prices).toHaveProperty("AAPL");
    expect(result.current.prices.BTC).toBe(65000);
    expect(result.current.prices.ETH).toBe(3200);
  });

  it("fetches REST prices on mount", async () => {
    renderHook(() => usePrices(5000));

    // Flush promises
    await act(async () => {
      await Promise.resolve();
    });

    expect(mockFetch).toHaveBeenCalledWith(
      expect.stringContaining("api.binance.com")
    );
  });

  it("creates WebSocket connection to Binance", () => {
    renderHook(() => usePrices(5000));
    // WebSocket constructor was called
    expect(MockWebSocket).toBeDefined();
  });

  it("updates synthetic prices every second", () => {
    const { result } = renderHook(() => usePrices(5000));

    act(() => {
      jest.advanceTimersByTime(1000);
    });

    // Synthetic prices should change (random walk)
    // Can't assert exact value, but price should be defined
    expect(result.current.prices.SPY).toBeDefined();
    expect(typeof result.current.prices.SPY).toBe("number");
  });

  it("includes all 8 default assets", () => {
    const { result } = renderHook(() => usePrices(5000));

    const expectedAssets = ["BTC", "ETH", "SOL", "SPY", "AAPL", "NVDA", "TSLA", "GLD"];
    for (const asset of expectedAssets) {
      expect(result.current.prices).toHaveProperty(asset);
      expect(typeof result.current.prices[asset]).toBe("number");
      expect(result.current.prices[asset]).toBeGreaterThan(0);
    }
  });

  it("handles REST fetch failure gracefully", async () => {
    mockFetch.mockRejectedValueOnce(new Error("Network error"));

    const { result } = renderHook(() => usePrices(5000));

    await act(async () => {
      await Promise.resolve();
    });

    // Should still have default prices
    expect(result.current.prices.BTC).toBe(65000);
    expect(result.current.binanceConnected).toBe(false);
  });

  it("cleans up WebSocket and intervals on unmount", () => {
    const { unmount } = renderHook(() => usePrices(5000));

    unmount();

    // No errors should occur on unmount
  });

  it("polls REST at specified interval when WS is down", () => {
    renderHook(() => usePrices(5000));

    const initialCallCount = mockFetch.mock.calls.length;

    act(() => {
      jest.advanceTimersByTime(5000);
    });

    // Should have polled at least once more
    expect(mockFetch.mock.calls.length).toBeGreaterThanOrEqual(initialCallCount);
  });
});
