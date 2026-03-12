// =============================================================================
// src/components/chart/drawing-toolbar.tsx — Chart Drawing Toolbar
//
// Compact horizontal toolbar for selecting drawing tools, undo, and clear.
// =============================================================================

"use client";

import {
  Minus,
  TrendingUp,
  GitBranch,
  Square,
  Undo2,
  Trash2,
} from "lucide-react";
import type { DrawingTool } from "@/hooks/use-chart-drawings";

// ---------------------------------------------------------------------------
// Tool definitions
// ---------------------------------------------------------------------------

const TOOLS: {
  tool: DrawingTool;
  label: string;
  icon: React.ComponentType<{ className?: string }>;
}[] = [
  { tool: "trendline", label: "Trendline", icon: TrendingUp },
  { tool: "horizontal", label: "Horizontal", icon: Minus },
  { tool: "fibonacci", label: "Fibonacci", icon: GitBranch },
  { tool: "rectangle", label: "Rectangle", icon: Square },
];

// ---------------------------------------------------------------------------
// Component
// ---------------------------------------------------------------------------

interface DrawingToolbarProps {
  activeTool: DrawingTool;
  onToolChange: (tool: DrawingTool) => void;
  onUndo: () => void;
  onClearAll: () => void;
  drawingCount: number;
}

export function DrawingToolbar({
  activeTool,
  onToolChange,
  onUndo,
  onClearAll,
  drawingCount,
}: DrawingToolbarProps) {
  return (
    <div className="flex items-center gap-1 px-3 py-1.5 rounded-lg border border-border/50 bg-card/50">
      {/* Drawing tools */}
      {TOOLS.map(({ tool, label, icon: Icon }) => {
        const isActive = activeTool === tool;
        return (
          <button
            key={tool}
            onClick={() => onToolChange(isActive ? "none" : tool)}
            className={`flex items-center gap-1.5 px-2.5 py-1.5 rounded-md text-[11px] font-medium transition-colors ${
              isActive
                ? "bg-blue-600/20 text-blue-400"
                : "text-muted-foreground hover:bg-muted hover:text-foreground"
            }`}
            title={label}
          >
            <Icon className="h-3.5 w-3.5" />
            <span className="hidden sm:inline">{label}</span>
          </button>
        );
      })}

      {/* Separator */}
      <div className="w-px h-5 bg-border/50 mx-1" />

      {/* Undo */}
      <button
        onClick={onUndo}
        disabled={drawingCount === 0}
        className="flex items-center gap-1.5 px-2.5 py-1.5 rounded-md text-[11px] font-medium text-muted-foreground hover:bg-muted hover:text-foreground transition-colors disabled:opacity-30 disabled:pointer-events-none"
        title="Undo last drawing"
      >
        <Undo2 className="h-3.5 w-3.5" />
        <span className="hidden sm:inline">Undo</span>
      </button>

      {/* Clear All */}
      <button
        onClick={onClearAll}
        disabled={drawingCount === 0}
        className="flex items-center gap-1.5 px-2.5 py-1.5 rounded-md text-[11px] font-medium text-muted-foreground hover:bg-red-500/10 hover:text-red-400 transition-colors disabled:opacity-30 disabled:pointer-events-none"
        title="Clear all drawings"
      >
        <Trash2 className="h-3.5 w-3.5" />
        <span className="hidden sm:inline">Clear</span>
      </button>

      {/* Drawing count */}
      {drawingCount > 0 && (
        <span className="text-[10px] text-muted-foreground ml-1">
          {drawingCount} drawing{drawingCount !== 1 ? "s" : ""}
        </span>
      )}
    </div>
  );
}
