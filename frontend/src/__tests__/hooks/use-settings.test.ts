// =============================================================================
// Tests: use-settings.ts — Application settings hook
// =============================================================================

import { renderHook, act } from "@testing-library/react";
import { useSettings } from "@/hooks/use-settings";

// Mock Supabase
jest.mock("@/lib/supabase/client", () => ({
  createClient: () => ({
    from: () => ({
      select: () => ({
        eq: () => ({
          single: () => Promise.resolve({ data: null }),
        }),
      }),
      upsert: jest.fn().mockReturnValue({ then: (cb: () => void) => cb() }),
    }),
  }),
}));

// Mock useAuth
jest.mock("@/hooks/use-auth", () => ({
  useAuth: () => ({ user: null, loading: false, signOut: jest.fn() }),
}));

describe("useSettings", () => {
  beforeEach(() => {
    localStorage.clear();
    jest.clearAllMocks();
  });

  it("initializes with default settings", () => {
    const { result } = renderHook(() => useSettings());

    expect(result.current.settings.paperCapital).toBe(100_000);
    expect(result.current.settings.strategy).toBe("momentum");
    expect(result.current.settings.theme).toBe("dark");
    expect(result.current.settings.pollIntervalMs).toBe(10000);
    expect(result.current.settings.trackedAssets).toBeInstanceOf(Array);
  });

  it("updates a single setting", () => {
    const { result } = renderHook(() => useSettings());

    act(() => {
      result.current.update({ strategy: "mean_reversion" });
    });

    expect(result.current.settings.strategy).toBe("mean_reversion");
    // Other settings unchanged
    expect(result.current.settings.theme).toBe("dark");
    expect(result.current.settings.paperCapital).toBe(100_000);
  });

  it("updates multiple settings at once", () => {
    const { result } = renderHook(() => useSettings());

    act(() => {
      result.current.update({
        strategy: "combined",
        theme: "light",
        pollIntervalMs: 5000,
      });
    });

    expect(result.current.settings.strategy).toBe("combined");
    expect(result.current.settings.theme).toBe("light");
    expect(result.current.settings.pollIntervalMs).toBe(5000);
  });

  it("persists settings to localStorage on update", () => {
    const { result } = renderHook(() => useSettings());

    act(() => {
      result.current.update({ theme: "light" });
    });

    expect(localStorage.setItem).toHaveBeenCalledWith(
      "jarvis-settings",
      expect.any(String)
    );

    const stored = JSON.parse(
      (localStorage.setItem as jest.Mock).mock.calls.find(
        (c: string[]) => c[0] === "jarvis-settings"
      )[1]
    );
    expect(stored.theme).toBe("light");
  });

  it("resets settings to defaults", () => {
    const { result } = renderHook(() => useSettings());

    act(() => {
      result.current.update({ strategy: "combined", theme: "light" });
    });

    act(() => {
      result.current.reset();
    });

    expect(result.current.settings.strategy).toBe("momentum");
    expect(result.current.settings.theme).toBe("dark");
  });

  it("loads settings from localStorage on mount", () => {
    const customSettings = {
      paperCapital: 50000,
      strategy: "combined",
      theme: "light",
      pollIntervalMs: 3000,
      trackedAssets: ["BTC", "ETH"],
    };
    localStorage.setItem("jarvis-settings", JSON.stringify(customSettings));

    const { result } = renderHook(() => useSettings());

    expect(result.current.settings.paperCapital).toBe(50000);
    expect(result.current.settings.strategy).toBe("combined");
    expect(result.current.settings.theme).toBe("light");
  });

  it("handles missing localStorage gracefully", () => {
    // No localStorage set → defaults
    const { result } = renderHook(() => useSettings());
    expect(result.current.settings.paperCapital).toBe(100_000);
  });

  it("tracked assets defaults to first assets from DEFAULT_ASSETS", () => {
    const { result } = renderHook(() => useSettings());
    expect(result.current.settings.trackedAssets.length).toBeGreaterThan(0);
    expect(result.current.settings.trackedAssets).toContain("BTC");
  });
});
