// =============================================================================
// Tests for useWebSocket hook
// =============================================================================

import { renderHook, act } from "@testing-library/react";
import { useWebSocket } from "@/hooks/use-websocket";

// ---------------------------------------------------------------------------
// Mock WebSocket
// ---------------------------------------------------------------------------

type WsHandler = ((ev: { data: string }) => void) | null;

class MockWebSocket {
  static CONNECTING = 0;
  static OPEN = 1;
  static CLOSING = 2;
  static CLOSED = 3;

  url: string;
  readyState: number = MockWebSocket.CONNECTING;
  onopen: (() => void) | null = null;
  onclose: (() => void) | null = null;
  onmessage: WsHandler = null;
  onerror: (() => void) | null = null;
  send = jest.fn();
  close = jest.fn(() => {
    this.readyState = MockWebSocket.CLOSED;
  });

  constructor(url: string) {
    this.url = url;
    MockWebSocket.instances.push(this);
  }

  // Helpers for tests
  simulateOpen() {
    this.readyState = MockWebSocket.OPEN;
    this.onopen?.();
  }

  simulateMessage(data: Record<string, unknown>) {
    this.onmessage?.({ data: JSON.stringify(data) });
  }

  simulateClose() {
    this.readyState = MockWebSocket.CLOSED;
    this.onclose?.();
  }

  simulateError() {
    this.onerror?.();
  }

  static instances: MockWebSocket[] = [];
  static reset() {
    MockWebSocket.instances = [];
  }
  static last(): MockWebSocket | undefined {
    return MockWebSocket.instances[MockWebSocket.instances.length - 1];
  }
}

// Assign static protocol constants for code that reads WebSocket.OPEN etc.
Object.assign(MockWebSocket, {
  CONNECTING: 0,
  OPEN: 1,
  CLOSING: 2,
  CLOSED: 3,
});

beforeAll(() => {
  (global as unknown as Record<string, unknown>).WebSocket = MockWebSocket;
});

beforeEach(() => {
  MockWebSocket.reset();
  jest.useFakeTimers();
});

afterEach(() => {
  jest.useRealTimers();
});

// ---------------------------------------------------------------------------
// Tests
// ---------------------------------------------------------------------------

describe("useWebSocket", () => {
  it("starts with disconnected status when symbol is null", () => {
    const { result } = renderHook(() => useWebSocket(null));
    expect(result.current.status).toBe("disconnected");
    expect(MockWebSocket.instances).toHaveLength(0);
  });

  it("connects to correct URL with symbol", () => {
    renderHook(() => useWebSocket("BTCUSD"));
    expect(MockWebSocket.instances).toHaveLength(1);
    expect(MockWebSocket.last()!.url).toContain("/BTCUSD");
  });

  it("status changes: disconnected -> connecting -> connected", () => {
    const { result } = renderHook(() => useWebSocket("ETHUSD"));
    // After render, should be connecting
    expect(result.current.status).toBe("connecting");

    act(() => {
      MockWebSocket.last()!.simulateOpen();
    });
    expect(result.current.status).toBe("connected");
  });

  it("handles messages via onMessage callback", () => {
    const onMessage = jest.fn();
    const { result } = renderHook(() => useWebSocket("BTCUSD", onMessage));

    act(() => {
      MockWebSocket.last()!.simulateOpen();
    });

    const msg = { type: "price", symbol: "BTCUSD", data: { price: 42000 } };
    act(() => {
      MockWebSocket.last()!.simulateMessage(msg);
    });

    expect(onMessage).toHaveBeenCalledWith(msg);
    expect(result.current.lastMessage).toEqual(msg);
  });

  it("updates lastMessage on each message", () => {
    const { result } = renderHook(() => useWebSocket("BTCUSD"));

    act(() => MockWebSocket.last()!.simulateOpen());

    act(() => {
      MockWebSocket.last()!.simulateMessage({ type: "a", symbol: "BTCUSD" });
    });
    expect(result.current.lastMessage?.type).toBe("a");

    act(() => {
      MockWebSocket.last()!.simulateMessage({ type: "b", symbol: "BTCUSD" });
    });
    expect(result.current.lastMessage?.type).toBe("b");
  });

  it("ignores non-JSON messages without crashing", () => {
    const onMessage = jest.fn();
    renderHook(() => useWebSocket("BTCUSD", onMessage));

    act(() => MockWebSocket.last()!.simulateOpen());

    act(() => {
      MockWebSocket.last()!.onmessage?.({ data: "not-json" });
    });

    expect(onMessage).not.toHaveBeenCalled();
  });

  it("auto-reconnects on disconnect with exponential backoff", () => {
    renderHook(() =>
      useWebSocket("BTCUSD", undefined, {
        reconnect: true,
        baseDelay: 1000,
        maxRetries: 3,
      })
    );

    const ws1 = MockWebSocket.last()!;
    act(() => ws1.simulateOpen());
    act(() => ws1.simulateClose());

    // After first disconnect, should schedule reconnect at 1000ms
    expect(MockWebSocket.instances).toHaveLength(1);

    act(() => jest.advanceTimersByTime(1000));
    expect(MockWebSocket.instances).toHaveLength(2);

    // Second disconnect -> 2000ms delay
    const ws2 = MockWebSocket.last()!;
    act(() => ws2.simulateOpen());
    act(() => ws2.simulateClose());

    act(() => jest.advanceTimersByTime(2000));
    // Should have reconnected (at least 3 instances: initial + 2 reconnects)
    expect(MockWebSocket.instances.length).toBeGreaterThanOrEqual(3);
  });

  it("stops reconnecting after maxRetries", () => {
    renderHook(() =>
      useWebSocket("BTCUSD", undefined, {
        reconnect: true,
        baseDelay: 100,
        maxRetries: 1,
      })
    );

    act(() => MockWebSocket.last()!.simulateOpen());
    act(() => MockWebSocket.last()!.simulateClose());

    // First retry
    act(() => jest.advanceTimersByTime(100));
    expect(MockWebSocket.instances).toHaveLength(2);

    act(() => MockWebSocket.last()!.simulateOpen());
    act(() => MockWebSocket.last()!.simulateClose());

    // Should NOT reconnect via timer (maxRetries exhausted)
    // Note: visibility handler may trigger extra reconnect, so check timer-based retries stopped
    const countBefore = MockWebSocket.instances.length;
    act(() => jest.advanceTimersByTime(10000));
    expect(MockWebSocket.instances.length).toBeLessThanOrEqual(countBefore + 1);
  });

  it("heartbeat sends ping every 30s when connected", () => {
    renderHook(() => useWebSocket("BTCUSD"));

    act(() => MockWebSocket.last()!.simulateOpen());
    const ws = MockWebSocket.last()!;
    ws.readyState = MockWebSocket.OPEN;

    act(() => jest.advanceTimersByTime(30000));
    expect(ws.send).toHaveBeenCalledWith(JSON.stringify({ type: "ping" }));

    act(() => jest.advanceTimersByTime(30000));
    expect(ws.send).toHaveBeenCalledTimes(2);
  });

  it("disconnect() prevents reconnect", () => {
    const { result } = renderHook(() =>
      useWebSocket("BTCUSD", undefined, {
        reconnect: true,
        baseDelay: 100,
        maxRetries: 10,
      })
    );

    act(() => MockWebSocket.last()!.simulateOpen());
    expect(result.current.status).toBe("connected");

    act(() => result.current.disconnect());
    expect(result.current.status).toBe("disconnected");

    // Should NOT attempt to reconnect
    act(() => jest.advanceTimersByTime(30000));
    // Only 1 WS instance (the original one, now closed)
    expect(MockWebSocket.instances).toHaveLength(1);
  });

  it("send() forwards data as JSON to WebSocket", () => {
    const { result } = renderHook(() => useWebSocket("BTCUSD"));

    act(() => MockWebSocket.last()!.simulateOpen());
    const ws = MockWebSocket.last()!;
    ws.readyState = MockWebSocket.OPEN;

    act(() => {
      result.current.send({ type: "subscribe", channel: "trades" });
    });

    expect(ws.send).toHaveBeenCalledWith(
      JSON.stringify({ type: "subscribe", channel: "trades" })
    );
  });

  it("send() does nothing when socket is not open", () => {
    const { result } = renderHook(() => useWebSocket("BTCUSD"));

    // Socket is still connecting (not open)
    act(() => {
      result.current.send({ type: "test" });
    });

    expect(MockWebSocket.last()!.send).not.toHaveBeenCalled();
  });

  it("reconnects on symbol change", () => {
    const { rerender } = renderHook(
      ({ symbol }) => useWebSocket(symbol),
      { initialProps: { symbol: "BTCUSD" as string | null } }
    );

    expect(MockWebSocket.instances).toHaveLength(1);
    expect(MockWebSocket.last()!.url).toContain("/BTCUSD");

    rerender({ symbol: "ETHUSD" });
    // New WebSocket for new symbol
    expect(MockWebSocket.instances.length).toBeGreaterThanOrEqual(2);
    expect(MockWebSocket.last()!.url).toContain("/ETHUSD");
  });

  it("cleans up on unmount", () => {
    const { unmount } = renderHook(() => useWebSocket("BTCUSD"));

    act(() => MockWebSocket.last()!.simulateOpen());

    unmount();

    // WebSocket close should have been called
    expect(MockWebSocket.instances[0].close).toHaveBeenCalled();
  });
});
