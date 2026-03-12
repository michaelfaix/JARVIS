// =============================================================================
// Tests: use-alerts.ts — Price alert system
// =============================================================================

import { renderHook, act } from "@testing-library/react";
import { useAlerts } from "@/hooks/use-alerts";

describe("useAlerts", () => {
  beforeEach(() => {
    localStorage.clear();
    jest.clearAllMocks();
  });

  it("starts with empty alerts", () => {
    const { result } = renderHook(() => useAlerts());
    expect(result.current.alerts).toHaveLength(0);
    expect(result.current.activeAlerts).toHaveLength(0);
    expect(result.current.triggeredAlerts).toHaveLength(0);
  });

  it("adds an alert", () => {
    const { result } = renderHook(() => useAlerts());

    act(() => {
      result.current.addAlert({
        asset: "BTC",
        condition: "above",
        targetPrice: 70000,
      });
    });

    expect(result.current.alerts).toHaveLength(1);
    expect(result.current.activeAlerts).toHaveLength(1);
    expect(result.current.alerts[0].asset).toBe("BTC");
    expect(result.current.alerts[0].condition).toBe("above");
    expect(result.current.alerts[0].targetPrice).toBe(70000);
    expect(result.current.alerts[0].triggered).toBe(false);
  });

  it("removes an alert", () => {
    const { result } = renderHook(() => useAlerts());

    let alertId: string;
    act(() => {
      const alert = result.current.addAlert({
        asset: "ETH",
        condition: "below",
        targetPrice: 3000,
      });
      alertId = alert.id;
    });

    expect(result.current.alerts).toHaveLength(1);

    act(() => {
      result.current.removeAlert(alertId!);
    });

    expect(result.current.alerts).toHaveLength(0);
  });

  it("triggers alert when price crosses above threshold", () => {
    const { result } = renderHook(() => useAlerts());

    act(() => {
      result.current.addAlert({
        asset: "BTC",
        condition: "above",
        targetPrice: 70000,
      });
    });

    act(() => {
      result.current.checkPrices({ BTC: 71000 });
    });

    expect(result.current.triggeredAlerts).toHaveLength(1);
    expect(result.current.activeAlerts).toHaveLength(0);
    expect(result.current.triggeredAlerts[0].triggered).toBe(true);
    expect(result.current.triggeredAlerts[0].triggeredAt).toBeDefined();
  });

  it("triggers alert when price crosses below threshold", () => {
    const { result } = renderHook(() => useAlerts());

    act(() => {
      result.current.addAlert({
        asset: "ETH",
        condition: "below",
        targetPrice: 3000,
      });
    });

    act(() => {
      result.current.checkPrices({ ETH: 2900 });
    });

    expect(result.current.triggeredAlerts).toHaveLength(1);
    expect(result.current.triggeredAlerts[0].asset).toBe("ETH");
  });

  it("does NOT trigger alert when price has NOT crossed threshold", () => {
    const { result } = renderHook(() => useAlerts());

    act(() => {
      result.current.addAlert({
        asset: "BTC",
        condition: "above",
        targetPrice: 70000,
      });
    });

    act(() => {
      result.current.checkPrices({ BTC: 65000 });
    });

    expect(result.current.triggeredAlerts).toHaveLength(0);
    expect(result.current.activeAlerts).toHaveLength(1);
  });

  it("does not re-trigger already triggered alerts", () => {
    const { result } = renderHook(() => useAlerts());

    act(() => {
      result.current.addAlert({
        asset: "BTC",
        condition: "above",
        targetPrice: 70000,
      });
    });

    act(() => {
      result.current.checkPrices({ BTC: 71000 });
    });

    // Check again — should not change
    act(() => {
      result.current.checkPrices({ BTC: 72000 });
    });

    expect(result.current.triggeredAlerts).toHaveLength(1);
  });

  it("clears triggered alerts", () => {
    const { result } = renderHook(() => useAlerts());

    act(() => {
      result.current.addAlert({
        asset: "BTC",
        condition: "above",
        targetPrice: 70000,
      });
    });

    act(() => {
      result.current.checkPrices({ BTC: 71000 });
    });

    expect(result.current.triggeredAlerts).toHaveLength(1);

    act(() => {
      result.current.clearTriggered();
    });

    expect(result.current.alerts).toHaveLength(0);
    expect(result.current.triggeredAlerts).toHaveLength(0);
  });

  it("persists alerts to localStorage", () => {
    const { result } = renderHook(() => useAlerts());

    act(() => {
      result.current.addAlert({
        asset: "SOL",
        condition: "above",
        targetPrice: 200,
      });
    });

    expect(localStorage.setItem).toHaveBeenCalledWith(
      "jarvis-price-alerts",
      expect.any(String)
    );

    const stored = JSON.parse(
      (localStorage.setItem as jest.Mock).mock.calls.find(
        (c: string[]) => c[0] === "jarvis-price-alerts"
      )[1]
    );
    expect(stored).toHaveLength(1);
    expect(stored[0].asset).toBe("SOL");
  });

  it("loads alerts from localStorage on mount", () => {
    const existing = [
      {
        id: "test-1",
        asset: "BTC",
        condition: "above",
        targetPrice: 80000,
        createdAt: new Date().toISOString(),
        triggered: false,
      },
    ];
    localStorage.setItem("jarvis-price-alerts", JSON.stringify(existing));

    const { result } = renderHook(() => useAlerts());
    expect(result.current.alerts).toHaveLength(1);
    expect(result.current.alerts[0].id).toBe("test-1");
  });

  it("handles multiple alerts for different assets", () => {
    const { result } = renderHook(() => useAlerts());

    act(() => {
      result.current.addAlert({
        asset: "BTC",
        condition: "above",
        targetPrice: 70000,
      });
      result.current.addAlert({
        asset: "ETH",
        condition: "below",
        targetPrice: 3000,
      });
    });

    // Only BTC triggers
    act(() => {
      result.current.checkPrices({ BTC: 71000, ETH: 3100 });
    });

    expect(result.current.triggeredAlerts).toHaveLength(1);
    expect(result.current.activeAlerts).toHaveLength(1);
    expect(result.current.triggeredAlerts[0].asset).toBe("BTC");
    expect(result.current.activeAlerts[0].asset).toBe("ETH");
  });

  it("ignores assets not in price map", () => {
    const { result } = renderHook(() => useAlerts());

    act(() => {
      result.current.addAlert({
        asset: "DOGE",
        condition: "above",
        targetPrice: 1,
      });
    });

    act(() => {
      result.current.checkPrices({ BTC: 65000 }); // DOGE not in prices
    });

    expect(result.current.triggeredAlerts).toHaveLength(0);
    expect(result.current.activeAlerts).toHaveLength(1);
  });
});
