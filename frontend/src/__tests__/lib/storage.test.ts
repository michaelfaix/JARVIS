// =============================================================================
// Tests: lib/storage.ts — localStorage helpers
// =============================================================================

import { loadJSON, saveJSON } from "@/lib/storage";

describe("storage helpers", () => {
  beforeEach(() => {
    localStorage.clear();
    jest.clearAllMocks();
  });

  describe("loadJSON", () => {
    it("returns fallback when key does not exist", () => {
      const result = loadJSON("nonexistent", { default: true });
      expect(result).toEqual({ default: true });
    });

    it("returns parsed value when key exists", () => {
      localStorage.setItem("test-key", JSON.stringify({ value: 42 }));
      const result = loadJSON("test-key", { value: 0 });
      expect(result).toEqual({ value: 42 });
    });

    it("returns fallback on invalid JSON", () => {
      localStorage.setItem("bad-json", "not-json{{{");
      const result = loadJSON("bad-json", "fallback");
      expect(result).toBe("fallback");
    });

    it("handles primitive values", () => {
      localStorage.setItem("bool-key", "true");
      expect(loadJSON("bool-key", false)).toBe(true);

      localStorage.setItem("num-key", "42");
      expect(loadJSON("num-key", 0)).toBe(42);

      localStorage.setItem("str-key", '"hello"');
      expect(loadJSON("str-key", "")).toBe("hello");
    });

    it("handles arrays", () => {
      localStorage.setItem("arr-key", JSON.stringify([1, 2, 3]));
      expect(loadJSON("arr-key", [])).toEqual([1, 2, 3]);
    });
  });

  describe("saveJSON", () => {
    it("saves value to localStorage as JSON string", () => {
      saveJSON("test-save", { foo: "bar" });
      expect(localStorage.setItem).toHaveBeenCalledWith(
        "test-save",
        '{"foo":"bar"}'
      );
    });

    it("saves primitive values", () => {
      saveJSON("bool", true);
      expect(localStorage.setItem).toHaveBeenCalledWith("bool", "true");

      saveJSON("num", 42);
      expect(localStorage.setItem).toHaveBeenCalledWith("num", "42");
    });

    it("saves arrays", () => {
      saveJSON("arr", [1, 2, 3]);
      expect(localStorage.setItem).toHaveBeenCalledWith("arr", "[1,2,3]");
    });
  });

  describe("roundtrip", () => {
    it("save then load returns the same object", () => {
      const original = {
        positions: [{ asset: "BTC", price: 65000 }],
        capital: 100000,
      };
      saveJSON("roundtrip", original);

      // Get what was actually saved
      const saved = (localStorage.setItem as jest.Mock).mock.calls.find(
        (c: string[]) => c[0] === "roundtrip"
      )?.[1];
      (localStorage.getItem as jest.Mock).mockReturnValueOnce(saved);

      const loaded = loadJSON("roundtrip", {});
      expect(loaded).toEqual(original);
    });
  });
});
