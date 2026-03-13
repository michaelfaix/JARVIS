// =============================================================================
// Tests: use-trade-notes.ts — Per-trade notes, tags & self-assessment
// =============================================================================

import { renderHook, act } from "@testing-library/react";
import { useTradeNotes, TAG_SUGGESTIONS } from "@/hooks/use-trade-notes";

describe("useTradeNotes", () => {
  beforeEach(() => {
    localStorage.clear();
    jest.clearAllMocks();
  });

  it("starts with no notes", () => {
    const { result } = renderHook(() => useTradeNotes());
    expect(Object.keys(result.current.notes)).toHaveLength(0);
    expect(result.current.getAllNotes()).toHaveLength(0);
  });

  it("saves a note for a trade", () => {
    const { result } = renderHook(() => useTradeNotes());

    act(() => {
      result.current.saveNote("trade-1", "Good entry", ["momentum"], 4);
    });

    const note = result.current.getNote("trade-1");
    expect(note).toBeDefined();
    expect(note!.tradeId).toBe("trade-1");
    expect(note!.note).toBe("Good entry");
    expect(note!.tags).toEqual(["momentum"]);
    expect(note!.rating).toBe(4);
    expect(note!.updatedAt).toBeDefined();
  });

  it("saves multiple notes for different trades", () => {
    const { result } = renderHook(() => useTradeNotes());

    act(() => {
      result.current.saveNote("trade-1", "Note 1", ["momentum"], 3);
    });
    act(() => {
      result.current.saveNote("trade-2", "Note 2", ["breakout"], 5);
    });

    expect(result.current.getAllNotes()).toHaveLength(2);
    expect(result.current.getNote("trade-1")).toBeDefined();
    expect(result.current.getNote("trade-2")).toBeDefined();
  });

  it("updates an existing note (overwrite by tradeId)", () => {
    const { result } = renderHook(() => useTradeNotes());

    act(() => {
      result.current.saveNote("trade-1", "Original", ["momentum"], 3);
    });

    act(() => {
      result.current.saveNote("trade-1", "Updated", ["breakout", "planned"], 5);
    });

    const note = result.current.getNote("trade-1");
    expect(note!.note).toBe("Updated");
    expect(note!.tags).toEqual(["breakout", "planned"]);
    expect(note!.rating).toBe(5);
  });

  it("deletes a note", () => {
    const { result } = renderHook(() => useTradeNotes());

    act(() => {
      result.current.saveNote("trade-1", "Note 1", [], 3);
      result.current.saveNote("trade-2", "Note 2", [], 4);
    });

    act(() => {
      result.current.deleteNote("trade-1");
    });

    expect(result.current.getNote("trade-1")).toBeUndefined();
    expect(result.current.getNote("trade-2")).toBeDefined();
    expect(result.current.getAllNotes()).toHaveLength(1);
  });

  it("deleting non-existent note does not error", () => {
    const { result } = renderHook(() => useTradeNotes());

    act(() => {
      result.current.deleteNote("non-existent");
    });

    expect(result.current.getAllNotes()).toHaveLength(0);
  });

  it("clamps rating to 1-5 range", () => {
    const { result } = renderHook(() => useTradeNotes());

    act(() => {
      result.current.saveNote("trade-low", "Low rating", [], 0);
    });
    expect(result.current.getNote("trade-low")!.rating).toBe(1);

    act(() => {
      result.current.saveNote("trade-high", "High rating", [], 10);
    });
    expect(result.current.getNote("trade-high")!.rating).toBe(5);
  });

  it("persists notes to localStorage", () => {
    const { result } = renderHook(() => useTradeNotes());

    act(() => {
      result.current.saveNote("trade-1", "Persisted note", ["scalp"], 4);
    });

    expect(localStorage.setItem).toHaveBeenCalledWith(
      "jarvis-trade-notes",
      expect.any(String)
    );
  });

  it("loads notes from localStorage on mount", () => {
    const existing = {
      "trade-1": {
        tradeId: "trade-1",
        note: "Loaded note",
        tags: ["swing"],
        rating: 3,
        updatedAt: new Date().toISOString(),
      },
    };
    localStorage.setItem("jarvis-trade-notes", JSON.stringify(existing));

    const { result } = renderHook(() => useTradeNotes());
    expect(result.current.getAllNotes()).toHaveLength(1);
    expect(result.current.getNote("trade-1")!.note).toBe("Loaded note");
  });

  it("getNote returns undefined for unknown trade", () => {
    const { result } = renderHook(() => useTradeNotes());
    expect(result.current.getNote("unknown")).toBeUndefined();
  });
});

describe("TAG_SUGGESTIONS", () => {
  it("contains expected tag values", () => {
    expect(TAG_SUGGESTIONS).toContain("momentum");
    expect(TAG_SUGGESTIONS).toContain("breakout");
    expect(TAG_SUGGESTIONS).toContain("reversal");
    expect(TAG_SUGGESTIONS).toContain("scalp");
    expect(TAG_SUGGESTIONS).toContain("swing");
    expect(TAG_SUGGESTIONS.length).toBeGreaterThanOrEqual(8);
  });
});
