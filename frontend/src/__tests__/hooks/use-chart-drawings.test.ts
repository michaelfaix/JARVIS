// =============================================================================
// Tests: use-chart-drawings.ts — Chart drawing state management
// =============================================================================

import { renderHook, act } from "@testing-library/react";
import {
  useChartDrawings,
  DRAWING_COLORS,
  type ChartDrawing,
  type DrawingTool,
} from "@/hooks/use-chart-drawings";

describe("useChartDrawings", () => {
  beforeEach(() => {
    localStorage.clear();
    jest.clearAllMocks();
  });

  const makeDraw = (overrides?: Partial<ChartDrawing>): ChartDrawing => ({
    id: `draw-${Date.now()}`,
    type: "trendline",
    points: [
      { price: 65000, time: 1700000000 },
      { price: 66000, time: 1700003600 },
    ],
    color: DRAWING_COLORS.trendline,
    style: "solid",
    ...overrides,
  });

  it("initializes with no drawings and activeTool='none'", () => {
    const { result } = renderHook(() => useChartDrawings("BTCUSDT"));
    expect(result.current.drawings).toHaveLength(0);
    expect(result.current.activeTool).toBe("none");
  });

  it("adds a drawing", () => {
    const { result } = renderHook(() => useChartDrawings("BTCUSDT"));
    const drawing = makeDraw({ id: "d1" });

    act(() => {
      result.current.addDrawing(drawing);
    });

    expect(result.current.drawings).toHaveLength(1);
    expect(result.current.drawings[0].id).toBe("d1");
    expect(result.current.drawings[0].type).toBe("trendline");
  });

  it("adds multiple drawings", () => {
    const { result } = renderHook(() => useChartDrawings("BTCUSDT"));

    act(() => {
      result.current.addDrawing(makeDraw({ id: "d1", type: "trendline" }));
      result.current.addDrawing(makeDraw({ id: "d2", type: "horizontal" }));
      result.current.addDrawing(makeDraw({ id: "d3", type: "fibonacci" }));
    });

    expect(result.current.drawings).toHaveLength(3);
  });

  it("removes a drawing by id", () => {
    const { result } = renderHook(() => useChartDrawings("BTCUSDT"));

    act(() => {
      result.current.addDrawing(makeDraw({ id: "d1" }));
      result.current.addDrawing(makeDraw({ id: "d2" }));
    });

    act(() => {
      result.current.removeDrawing("d1");
    });

    expect(result.current.drawings).toHaveLength(1);
    expect(result.current.drawings[0].id).toBe("d2");
  });

  it("does nothing when removing non-existent id", () => {
    const { result } = renderHook(() => useChartDrawings("BTCUSDT"));

    act(() => {
      result.current.addDrawing(makeDraw({ id: "d1" }));
    });

    act(() => {
      result.current.removeDrawing("non-existent");
    });

    expect(result.current.drawings).toHaveLength(1);
  });

  it("clears all drawings", () => {
    const { result } = renderHook(() => useChartDrawings("BTCUSDT"));

    act(() => {
      result.current.addDrawing(makeDraw({ id: "d1" }));
      result.current.addDrawing(makeDraw({ id: "d2" }));
      result.current.addDrawing(makeDraw({ id: "d3" }));
    });

    expect(result.current.drawings).toHaveLength(3);

    act(() => {
      result.current.clearAll();
    });

    expect(result.current.drawings).toHaveLength(0);
  });

  it("undoes the last drawing", () => {
    const { result } = renderHook(() => useChartDrawings("BTCUSDT"));

    act(() => {
      result.current.addDrawing(makeDraw({ id: "d1" }));
      result.current.addDrawing(makeDraw({ id: "d2" }));
    });

    act(() => {
      result.current.undoLast();
    });

    expect(result.current.drawings).toHaveLength(1);
    expect(result.current.drawings[0].id).toBe("d1");
  });

  it("undoLast on empty drawings does not error", () => {
    const { result } = renderHook(() => useChartDrawings("BTCUSDT"));

    act(() => {
      result.current.undoLast();
    });

    expect(result.current.drawings).toHaveLength(0);
  });

  it("sets the active tool", () => {
    const { result } = renderHook(() => useChartDrawings("BTCUSDT"));

    act(() => {
      result.current.setActiveTool("fibonacci");
    });

    expect(result.current.activeTool).toBe("fibonacci");
  });

  it("persists drawings to localStorage", () => {
    const { result } = renderHook(() => useChartDrawings("BTCUSDT"));

    act(() => {
      result.current.addDrawing(makeDraw({ id: "d1" }));
    });

    expect(localStorage.setItem).toHaveBeenCalledWith(
      "jarvis-chart-drawings",
      expect.any(String)
    );
  });

  it("loads drawings from localStorage per symbol", () => {
    const stored = {
      BTCUSDT: [makeDraw({ id: "btc-draw" })],
      ETHUSDT: [makeDraw({ id: "eth-draw" })],
    };
    localStorage.setItem("jarvis-chart-drawings", JSON.stringify(stored));

    const { result } = renderHook(() => useChartDrawings("BTCUSDT"));
    expect(result.current.drawings).toHaveLength(1);
    expect(result.current.drawings[0].id).toBe("btc-draw");
  });

  it("returns empty array for unknown symbol", () => {
    const stored = { BTCUSDT: [makeDraw({ id: "btc-draw" })] };
    localStorage.setItem("jarvis-chart-drawings", JSON.stringify(stored));

    const { result } = renderHook(() => useChartDrawings("DOGEUSDT"));
    expect(result.current.drawings).toHaveLength(0);
  });

  it("handles corrupt localStorage data gracefully", () => {
    localStorage.setItem("jarvis-chart-drawings", "not-json{{{");

    const { result } = renderHook(() => useChartDrawings("BTCUSDT"));
    expect(result.current.drawings).toHaveLength(0);
  });
});

describe("DRAWING_COLORS", () => {
  it("has colors for all drawing tool types except none", () => {
    const toolTypes: Exclude<DrawingTool, "none">[] = [
      "trendline",
      "horizontal",
      "fibonacci",
      "rectangle",
    ];
    for (const tool of toolTypes) {
      expect(DRAWING_COLORS[tool]).toBeDefined();
      expect(typeof DRAWING_COLORS[tool]).toBe("string");
      expect(DRAWING_COLORS[tool]).toMatch(/^#[0-9a-f]{6}$/i);
    }
  });
});
