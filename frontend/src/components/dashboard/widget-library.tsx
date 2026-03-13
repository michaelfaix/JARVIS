// =============================================================================
// src/components/dashboard/widget-library.tsx — Widget add/remove modal
// =============================================================================

"use client";

import { WIDGET_REGISTRY } from "@/lib/widget-registry";
import { X, Plus, Check } from "lucide-react";
import { cn } from "@/lib/utils";

interface WidgetLibraryProps {
  open: boolean;
  onClose: () => void;
  activeWidgets: string[];
  onAddWidget: (id: string) => void;
  onRemoveWidget: (id: string) => void;
  onReset: () => void;
}

export function WidgetLibrary({
  open,
  onClose,
  activeWidgets,
  onAddWidget,
  onRemoveWidget,
  onReset,
}: WidgetLibraryProps) {
  if (!open) return null;

  return (
    <>
      {/* Backdrop */}
      <div className="fixed inset-0 z-40 bg-black/60 backdrop-blur-sm" onClick={onClose} />

      {/* Modal */}
      <div className="fixed inset-x-4 top-16 z-50 mx-auto max-w-lg rounded border border-hud-border bg-hud-panel/95 backdrop-blur-md shadow-2xl">
        {/* Header */}
        <div className="flex items-center justify-between border-b border-hud-border px-4 py-3">
          <div className="flex items-center gap-2">
            <div className="h-1.5 w-1.5 rounded-full bg-hud-cyan animate-pulse-live" />
            <span className="font-mono text-xs uppercase tracking-widest text-hud-cyan">Widget Library</span>
          </div>
          <div className="flex items-center gap-2">
            <button
              onClick={onReset}
              className="text-[9px] font-mono text-muted-foreground hover:text-hud-amber transition-colors px-2 py-0.5 rounded border border-hud-border"
            >
              Reset Layout
            </button>
            <button onClick={onClose} className="text-muted-foreground hover:text-hud-cyan transition-colors">
              <X className="h-4 w-4" />
            </button>
          </div>
        </div>

        {/* Grid */}
        <div className="grid grid-cols-2 gap-2 p-4 max-h-[60vh] overflow-y-auto">
          {WIDGET_REGISTRY.map((widget) => {
            const isActive = activeWidgets.includes(widget.id);
            const Icon = widget.icon;
            return (
              <button
                key={widget.id}
                onClick={() => isActive ? onRemoveWidget(widget.id) : onAddWidget(widget.id)}
                className={cn(
                  "flex items-center gap-3 rounded border p-3 text-left transition-colors",
                  isActive
                    ? "border-hud-cyan/30 bg-hud-cyan/10"
                    : "border-hud-border bg-hud-bg/60 hover:border-hud-cyan/20 hover:bg-hud-cyan/5"
                )}
              >
                <div className={cn(
                  "flex h-8 w-8 shrink-0 items-center justify-center rounded",
                  isActive ? "bg-hud-cyan/20 text-hud-cyan" : "bg-hud-border/30 text-muted-foreground"
                )}>
                  <Icon className="h-4 w-4" />
                </div>
                <div className="flex-1 min-w-0">
                  <div className="text-xs font-mono font-medium text-white truncate">{widget.label}</div>
                  <div className="text-[9px] font-mono text-muted-foreground">
                    {widget.defaultSize.w}×{widget.defaultSize.h}
                  </div>
                </div>
                <div className="shrink-0">
                  {isActive ? (
                    <Check className="h-4 w-4 text-hud-green" />
                  ) : (
                    <Plus className="h-4 w-4 text-muted-foreground" />
                  )}
                </div>
              </button>
            );
          })}
        </div>
      </div>
    </>
  );
}
