// =============================================================================
// Tests: use-keyboard-shortcuts.ts — Keyboard shortcut registration
// =============================================================================

import { renderHook } from "@testing-library/react";
import { useKeyboardShortcuts, type Shortcut } from "@/hooks/use-keyboard-shortcuts";
import { fireEvent } from "@testing-library/react";

describe("useKeyboardShortcuts", () => {
  it("returns the shortcuts array", () => {
    const shortcuts: Shortcut[] = [
      { key: "k", description: "Test", action: jest.fn() },
    ];
    const { result } = renderHook(() => useKeyboardShortcuts(shortcuts));
    expect(result.current).toEqual(shortcuts);
  });

  it("fires action on matching key press", () => {
    const action = jest.fn();
    const shortcuts: Shortcut[] = [
      { key: "k", description: "Open search", action },
    ];
    renderHook(() => useKeyboardShortcuts(shortcuts));

    fireEvent.keyDown(document, { key: "k" });
    expect(action).toHaveBeenCalledTimes(1);
  });

  it("fires action on matching key with ctrl", () => {
    const action = jest.fn();
    const shortcuts: Shortcut[] = [
      { key: "k", ctrl: true, description: "Search", action },
    ];
    renderHook(() => useKeyboardShortcuts(shortcuts));

    fireEvent.keyDown(document, { key: "k", ctrlKey: true });
    expect(action).toHaveBeenCalledTimes(1);
  });

  it("does not fire action when ctrl is required but not pressed", () => {
    const action = jest.fn();
    const shortcuts: Shortcut[] = [
      { key: "k", ctrl: true, description: "Search", action },
    ];
    renderHook(() => useKeyboardShortcuts(shortcuts));

    fireEvent.keyDown(document, { key: "k" });
    expect(action).not.toHaveBeenCalled();
  });

  it("fires action on matching key with shift", () => {
    const action = jest.fn();
    const shortcuts: Shortcut[] = [
      { key: "?", shift: true, description: "Help", action },
    ];
    renderHook(() => useKeyboardShortcuts(shortcuts));

    fireEvent.keyDown(document, { key: "?", shiftKey: true });
    expect(action).toHaveBeenCalledTimes(1);
  });

  it("does not fire when key does not match", () => {
    const action = jest.fn();
    const shortcuts: Shortcut[] = [
      { key: "k", description: "Test", action },
    ];
    renderHook(() => useKeyboardShortcuts(shortcuts));

    fireEvent.keyDown(document, { key: "j" });
    expect(action).not.toHaveBeenCalled();
  });

  it("does not fire when target is an input element", () => {
    const action = jest.fn();
    const shortcuts: Shortcut[] = [
      { key: "k", description: "Test", action },
    ];
    renderHook(() => useKeyboardShortcuts(shortcuts));

    const input = document.createElement("input");
    document.body.appendChild(input);
    fireEvent.keyDown(input, { key: "k" });
    expect(action).not.toHaveBeenCalled();
    document.body.removeChild(input);
  });

  it("does not fire when target is a textarea", () => {
    const action = jest.fn();
    const shortcuts: Shortcut[] = [
      { key: "k", description: "Test", action },
    ];
    renderHook(() => useKeyboardShortcuts(shortcuts));

    const textarea = document.createElement("textarea");
    document.body.appendChild(textarea);
    fireEvent.keyDown(textarea, { key: "k" });
    expect(action).not.toHaveBeenCalled();
    document.body.removeChild(textarea);
  });

  it("handles multiple shortcuts", () => {
    const actionA = jest.fn();
    const actionB = jest.fn();
    const shortcuts: Shortcut[] = [
      { key: "a", description: "Action A", action: actionA },
      { key: "b", description: "Action B", action: actionB },
    ];
    renderHook(() => useKeyboardShortcuts(shortcuts));

    fireEvent.keyDown(document, { key: "b" });
    expect(actionA).not.toHaveBeenCalled();
    expect(actionB).toHaveBeenCalledTimes(1);
  });

  it("prevents default on matched shortcut", () => {
    const action = jest.fn();
    const shortcuts: Shortcut[] = [
      { key: "k", description: "Test", action },
    ];
    renderHook(() => useKeyboardShortcuts(shortcuts));

    const event = new KeyboardEvent("keydown", {
      key: "k",
      bubbles: true,
      cancelable: true,
    });
    const spy = jest.spyOn(event, "preventDefault");
    document.dispatchEvent(event);
    expect(spy).toHaveBeenCalled();
  });

  it("cleans up event listener on unmount", () => {
    const action = jest.fn();
    const shortcuts: Shortcut[] = [
      { key: "k", description: "Test", action },
    ];
    const { unmount } = renderHook(() => useKeyboardShortcuts(shortcuts));

    unmount();

    fireEvent.keyDown(document, { key: "k" });
    expect(action).not.toHaveBeenCalled();
  });
});
