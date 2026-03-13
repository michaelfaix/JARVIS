// =============================================================================
// Tests: use-social-trading.ts — Social trading state management
// =============================================================================

import { renderHook, act } from "@testing-library/react";
import { useSocialTrading } from "@/hooks/use-social-trading";

// Mock Supabase
jest.mock("@/lib/supabase/client", () => ({
  createClient: () => ({
    from: () => ({
      select: () => ({
        eq: () => ({ single: () => Promise.resolve({ data: null }) }),
      }),
    }),
  }),
}));

// Mock useAuth
jest.mock("@/hooks/use-auth", () => ({
  useAuth: () => ({ user: null, loading: false, signOut: jest.fn() }),
}));

// Default: free tier (isPro = false)
let mockIsPro = false;
jest.mock("@/hooks/use-profile", () => ({
  useProfile: () => ({
    profile: null,
    loading: false,
    isPro: mockIsPro,
    isEnterprise: false,
    tier: mockIsPro ? "pro" : "free",
  }),
}));

describe("useSocialTrading", () => {
  beforeEach(() => {
    localStorage.clear();
    jest.clearAllMocks();
    mockIsPro = false;
  });

  it("starts with empty followed traders", () => {
    const { result } = renderHook(() => useSocialTrading());
    expect(result.current.followedTraders).toHaveLength(0);
    expect(result.current.followCount).toBe(0);
    expect(result.current.canFollow).toBe(true);
  });

  it("follows a trader", () => {
    const { result } = renderHook(() => useSocialTrading());

    act(() => {
      result.current.followTrader("trader-1");
    });

    expect(result.current.followedTraders).toContain("trader-1");
    expect(result.current.followCount).toBe(1);
  });

  it("does not duplicate a followed trader", () => {
    const { result } = renderHook(() => useSocialTrading());

    act(() => {
      result.current.followTrader("trader-1");
    });

    act(() => {
      result.current.followTrader("trader-1");
    });

    expect(result.current.followedTraders).toHaveLength(1);
  });

  it("unfollows a trader", () => {
    const { result } = renderHook(() => useSocialTrading());

    act(() => {
      result.current.followTrader("trader-1");
      result.current.followTrader("trader-2");
    });

    act(() => {
      result.current.unfollowTrader("trader-1");
    });

    expect(result.current.followedTraders).not.toContain("trader-1");
    expect(result.current.followedTraders).toContain("trader-2");
    expect(result.current.followCount).toBe(1);
  });

  it("isFollowing returns correct boolean", () => {
    const { result } = renderHook(() => useSocialTrading());

    act(() => {
      result.current.followTrader("trader-1");
    });

    expect(result.current.isFollowing("trader-1")).toBe(true);
    expect(result.current.isFollowing("trader-2")).toBe(false);
  });

  it("creates default copy settings when following", () => {
    const { result } = renderHook(() => useSocialTrading());

    act(() => {
      result.current.followTrader("trader-1");
    });

    const settings = result.current.copySettings["trader-1"];
    expect(settings).toBeDefined();
    expect(settings.enabled).toBe(false);
    expect(settings.maxCapitalPercent).toBe(5);
    expect(settings.autoFollow).toBe(false);
  });

  it("updates copy settings for a trader", () => {
    const { result } = renderHook(() => useSocialTrading());

    act(() => {
      result.current.followTrader("trader-1");
    });

    act(() => {
      result.current.setCopySettings("trader-1", {
        enabled: true,
        maxCapitalPercent: 10,
      });
    });

    const settings = result.current.copySettings["trader-1"];
    expect(settings.enabled).toBe(true);
    expect(settings.maxCapitalPercent).toBe(10);
    expect(settings.autoFollow).toBe(false); // unchanged
  });

  it("enforces max 10 follows for free tier", () => {
    const { result } = renderHook(() => useSocialTrading());

    // Follow 10 traders
    act(() => {
      for (let i = 0; i < 10; i++) {
        result.current.followTrader(`trader-${i}`);
      }
    });

    expect(result.current.followCount).toBe(10);
    expect(result.current.canFollow).toBe(false);

    // 11th follow should be rejected
    act(() => {
      result.current.followTrader("trader-11");
    });

    expect(result.current.followCount).toBe(10);
    expect(result.current.followedTraders).not.toContain("trader-11");
  });

  it("persists state to localStorage", () => {
    const { result } = renderHook(() => useSocialTrading());

    act(() => {
      result.current.followTrader("trader-1");
    });

    expect(localStorage.setItem).toHaveBeenCalledWith(
      "jarvis-social",
      expect.any(String)
    );
  });

  it("preserves copy settings after unfollow", () => {
    const { result } = renderHook(() => useSocialTrading());

    act(() => {
      result.current.followTrader("trader-1");
    });

    act(() => {
      result.current.setCopySettings("trader-1", { enabled: true });
    });

    act(() => {
      result.current.unfollowTrader("trader-1");
    });

    // Copy settings should still exist in state
    expect(result.current.copySettings["trader-1"]).toBeDefined();
    expect(result.current.copySettings["trader-1"].enabled).toBe(true);
  });
});
