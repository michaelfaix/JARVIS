"use client";

import { useEffect, useRef } from "react";

interface ShortcutsHelpProps {
  open: boolean;
  onClose: () => void;
}

interface ShortcutEntry {
  keys: string[];
  description: string;
}

interface ShortcutGroup {
  category: string;
  items: ShortcutEntry[];
}

const shortcutGroups: ShortcutGroup[] = [
  {
    category: "Navigation",
    items: [
      { keys: ["G", "D"], description: "Dashboard" },
      { keys: ["G", "C"], description: "Charts" },
      { keys: ["G", "S"], description: "Signals" },
      { keys: ["G", "P"], description: "Portfolio" },
      { keys: ["G", "R"], description: "Risk" },
    ],
  },
  {
    category: "Actions",
    items: [
      { keys: ["N"], description: "New trade (signals page)" },
      { keys: ["Esc"], description: "Close any modal / dialog" },
    ],
  },
  {
    category: "General",
    items: [
      { keys: ["?"], description: "Show this help" },
      { keys: ["/"], description: "Focus search (future)" },
    ],
  },
];

function KeyBadge({ children }: { children: React.ReactNode }) {
  return (
    <kbd className="inline-flex items-center rounded border border-border/50 bg-muted/50 px-1.5 py-0.5 text-xs font-mono text-muted-foreground">
      {children}
    </kbd>
  );
}

export function ShortcutsHelp({ open, onClose }: ShortcutsHelpProps) {
  const backdropRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (!open) return;
    const handler = (e: KeyboardEvent) => {
      if (e.key === "Escape") {
        e.preventDefault();
        onClose();
      }
    };
    document.addEventListener("keydown", handler);
    return () => document.removeEventListener("keydown", handler);
  }, [open, onClose]);

  if (!open) return null;

  return (
    <div
      ref={backdropRef}
      className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 backdrop-blur-sm"
      onClick={(e) => {
        if (e.target === backdropRef.current) onClose();
      }}
    >
      <div className="w-full max-w-md rounded-xl border border-border/50 bg-card p-6 shadow-2xl">
        <div className="mb-5 flex items-center justify-between">
          <h2 className="text-lg font-semibold text-foreground">
            Keyboard Shortcuts
          </h2>
          <button
            onClick={onClose}
            className="rounded-md p-1 text-muted-foreground hover:text-foreground transition-colors"
          >
            <svg
              className="h-4 w-4"
              fill="none"
              stroke="currentColor"
              viewBox="0 0 24 24"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M6 18L18 6M6 6l12 12"
              />
            </svg>
          </button>
        </div>

        <div className="space-y-5">
          {shortcutGroups.map((group) => (
            <div key={group.category}>
              <h3 className="mb-2 text-xs font-medium uppercase tracking-wider text-muted-foreground">
                {group.category}
              </h3>
              <div className="space-y-1.5">
                {group.items.map((item) => (
                  <div
                    key={item.description}
                    className="flex items-center justify-between rounded-md px-2 py-1.5 text-sm"
                  >
                    <span className="text-foreground/80">
                      {item.description}
                    </span>
                    <div className="flex items-center gap-1">
                      {item.keys.map((k, i) => (
                        <span key={i} className="flex items-center gap-1">
                          {i > 0 && (
                            <span className="text-xs text-muted-foreground">
                              then
                            </span>
                          )}
                          <KeyBadge>{k}</KeyBadge>
                        </span>
                      ))}
                    </div>
                  </div>
                ))}
              </div>
            </div>
          ))}
        </div>

        <div className="mt-5 border-t border-border/30 pt-3">
          <p className="text-center text-xs text-muted-foreground">
            Press <KeyBadge>?</KeyBadge> to toggle this help
          </p>
        </div>
      </div>
    </div>
  );
}
