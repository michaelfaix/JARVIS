// =============================================================================
// Tests: use-sidebar.ts — Sidebar collapse state
// =============================================================================

import { renderHook, act } from "@testing-library/react";
import { useSidebar } from "@/hooks/use-sidebar";

describe("useSidebar", () => {
  beforeEach(() => {
    localStorage.clear();
    jest.clearAllMocks();
  });

  it("defaults to not collapsed", () => {
    const { result } = renderHook(() => useSidebar());
    expect(result.current.collapsed).toBe(false);
  });

  it("toggles collapsed state", () => {
    const { result } = renderHook(() => useSidebar());

    act(() => {
      result.current.toggle();
    });

    expect(result.current.collapsed).toBe(true);

    act(() => {
      result.current.toggle();
    });

    expect(result.current.collapsed).toBe(false);
  });

  it("persists collapsed state to localStorage", () => {
    const { result } = renderHook(() => useSidebar());

    act(() => {
      result.current.toggle();
    });

    expect(localStorage.setItem).toHaveBeenCalledWith(
      "jarvis-sidebar-collapsed",
      "true"
    );
  });

  it("loads collapsed state from localStorage", () => {
    localStorage.setItem("jarvis-sidebar-collapsed", "true");

    const { result } = renderHook(() => useSidebar());

    // After useEffect runs
    act(() => {}); // flush effects

    expect(result.current.collapsed).toBe(true);
  });
});
