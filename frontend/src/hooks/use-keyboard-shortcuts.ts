"use client";

import { useEffect } from "react";

export interface Shortcut {
  key: string;
  ctrl?: boolean;
  shift?: boolean;
  description: string;
  action: () => void;
}

function isEditableTarget(target: EventTarget | null): boolean {
  if (!target || !(target instanceof HTMLElement)) return false;
  const tag = target.tagName.toLowerCase();
  if (tag === "input" || tag === "textarea" || tag === "select") return true;
  if (target.isContentEditable) return true;
  return false;
}

export function useKeyboardShortcuts(shortcuts: Shortcut[]) {
  useEffect(() => {
    const handler = (e: KeyboardEvent) => {
      if (isEditableTarget(e.target)) return;

      for (const s of shortcuts) {
        if (s.ctrl && !e.ctrlKey && !e.metaKey) continue;
        if (s.shift && !e.shiftKey) continue;
        if (!s.ctrl && (e.ctrlKey || e.metaKey)) continue;
        if (!s.shift && e.shiftKey && s.key !== "?") continue;

        if (e.key.toLowerCase() === s.key.toLowerCase() || e.key === s.key) {
          e.preventDefault();
          s.action();
          return;
        }
      }
    };

    document.addEventListener("keydown", handler);
    return () => document.removeEventListener("keydown", handler);
  }, [shortcuts]);

  return shortcuts;
}
