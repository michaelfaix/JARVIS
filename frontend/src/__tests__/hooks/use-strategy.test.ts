import { renderHook, act } from "@testing-library/react";
import { useStrategy } from "@/hooks/use-strategy";

describe("useStrategy", () => {
  beforeEach(() => {
    localStorage.clear();
  });

  it("initializes with default strategy", () => {
    const { result } = renderHook(() => useStrategy());
    expect(result.current.state.selectedStrategy).toBeDefined();
    expect(typeof result.current.state.selectedStrategy).toBe("string");
  });

  it("can select a different strategy", () => {
    const { result } = renderHook(() => useStrategy());
    act(() => {
      result.current.selectStrategy("momentum");
    });
    expect(result.current.state.selectedStrategy).toBe("momentum");
  });

  it("updates slPercent param", () => {
    const { result } = renderHook(() => useStrategy());
    act(() => {
      result.current.updateParam("slPercent", 5);
    });
    expect(result.current.state.params.slPercent).toBe(5);
  });

  it("updates tpPercent param", () => {
    const { result } = renderHook(() => useStrategy());
    act(() => {
      result.current.updateParam("tpPercent", 10);
    });
    expect(result.current.state.params.tpPercent).toBe(10);
  });

  it("updates rsiLength param", () => {
    const { result } = renderHook(() => useStrategy());
    act(() => {
      result.current.updateParam("rsiLength", 21);
    });
    expect(result.current.state.params.rsiLength).toBe(21);
  });

  it("adds custom rules", () => {
    const { result } = renderHook(() => useStrategy());
    act(() => {
      result.current.addRule({
        id: "rule-1",
        indicator: "RSI",
        operator: ">",
        value: 70,
        logic: "AND",
        action: "SELL",
      });
    });
    expect(result.current.state.customRules).toHaveLength(1);
    expect(result.current.state.customRules[0].indicator).toBe("RSI");
  });

  it("removes custom rules", () => {
    const { result } = renderHook(() => useStrategy());
    act(() => {
      result.current.addRule({
        id: "rule-1",
        indicator: "RSI",
        operator: ">",
        value: 70,
        logic: "AND",
        action: "SELL",
      });
    });
    expect(result.current.state.customRules).toHaveLength(1);
    act(() => {
      result.current.removeRule("rule-1");
    });
    expect(result.current.state.customRules).toHaveLength(0);
  });

  it("provides executeBacktest function", () => {
    const { result } = renderHook(() => useStrategy());
    expect(typeof result.current.executeBacktest).toBe("function");
  });

  it("runs backtest without throwing", () => {
    const { result } = renderHook(() => useStrategy());
    expect(() => {
      act(() => {
        result.current.executeBacktest(["BTC", "ETH"], 90);
      });
    }).not.toThrow();
  });
});
