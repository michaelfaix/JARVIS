// =============================================================================
// src/components/dashboard/widget-layout.tsx — Draggable widget grid
// =============================================================================

"use client";

import { useEffect, useMemo, useRef, useState } from "react";
import { GridLayout, verticalCompactor, type Layout, type LayoutItem } from "react-grid-layout";
import "react-grid-layout/css/styles.css";
import { X } from "lucide-react";

interface WidgetLayoutProps {
  layouts: LayoutItem[];
  activeWidgets: string[];
  onLayoutChange: (layout: Layout) => void;
  children: React.ReactNode;
}

export function WidgetLayout({
  layouts,
  activeWidgets,
  onLayoutChange,
  children,
}: WidgetLayoutProps) {
  const containerRef = useRef<HTMLDivElement>(null);
  const [width, setWidth] = useState(800);

  useEffect(() => {
    if (!containerRef.current) return;
    const observer = new ResizeObserver((entries) => {
      for (const entry of entries) {
        setWidth(entry.contentRect.width);
      }
    });
    observer.observe(containerRef.current);
    return () => observer.disconnect();
  }, []);

  const filteredLayouts = useMemo(
    () => layouts.filter((l) => activeWidgets.includes(l.i)),
    [layouts, activeWidgets]
  );

  return (
    <div ref={containerRef}>
      <GridLayout
        layout={filteredLayouts}
        onLayoutChange={onLayoutChange}
        width={width}
        gridConfig={{
          cols: 10,
          rowHeight: 60,
          margin: [8, 8] as const,
          containerPadding: [0, 0] as const,
          maxRows: Infinity,
        }}
        dragConfig={{
          enabled: true,
          handle: ".widget-drag-handle",
        }}
        resizeConfig={{
          enabled: true,
        }}
        compactor={verticalCompactor}
        className="widget-grid"
      >
        {children}
      </GridLayout>
    </div>
  );
}

interface WidgetWrapperProps {
  id: string;
  title: string;
  onRemove: (id: string) => void;
  children: React.ReactNode;
}

export function WidgetWrapper({ id, title, onRemove, children }: WidgetWrapperProps) {
  return (
    <div className="h-full flex flex-col rounded border border-hud-border bg-hud-panel/80 overflow-hidden">
      <div className="widget-drag-handle flex items-center justify-between px-2 py-1 border-b border-hud-border/50 cursor-grab active:cursor-grabbing shrink-0">
        <div className="flex items-center gap-1.5">
          <div className="h-1 w-1 rounded-full bg-hud-cyan animate-pulse-live" />
          <span className="hud-label">{title}</span>
        </div>
        <button
          onClick={(e) => { e.stopPropagation(); onRemove(id); }}
          className="text-muted-foreground/40 hover:text-hud-red transition-colors p-0.5"
        >
          <X className="h-2.5 w-2.5" />
        </button>
      </div>
      <div className="flex-1 overflow-auto">
        {children}
      </div>
    </div>
  );
}
