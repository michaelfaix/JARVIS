// =============================================================================
// Tests: use-sidebar.ts — Sidebar expand/collapse state
// =============================================================================

import { renderHook, act } from "@testing-library/react";
import { useSidebar } from "@/hooks/use-sidebar";

describe("useSidebar", () => {
  beforeEach(() => {
    localStorage.clear();
    jest.clearAllMocks();
  });

  it("defaults to collapsed (not expanded)", () => {
    const { result } = renderHook(() => useSidebar());
    expect(result.current.collapsed).toBe(true);
    expect(result.current.expanded).toBe(false);
  });

  it("toggles expanded state", () => {
    const { result } = renderHook(() => useSidebar());

    act(() => {
      result.current.toggle();
    });

    expect(result.current.expanded).toBe(true);
    expect(result.current.collapsed).toBe(false);

    act(() => {
      result.current.toggle();
    });

    expect(result.current.expanded).toBe(false);
    expect(result.current.collapsed).toBe(true);
  });

  it("persists expanded state to localStorage", () => {
    const { result } = renderHook(() => useSidebar());

    act(() => {
      result.current.toggle();
    });

    expect(localStorage.setItem).toHaveBeenCalledWith(
      "jarvis-sidebar-expanded",
      "true"
    );
  });

  it("loads expanded state from localStorage", () => {
    localStorage.setItem("jarvis-sidebar-expanded", "true");

    const { result } = renderHook(() => useSidebar());

    act(() => {}); // flush effects

    expect(result.current.expanded).toBe(true);
    expect(result.current.collapsed).toBe(false);
  });
});
