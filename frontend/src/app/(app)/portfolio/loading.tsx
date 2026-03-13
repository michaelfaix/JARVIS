export default function PortfolioLoading() {
  return (
    <div className="p-4 space-y-4 animate-pulse">
      {/* Summary cards skeleton */}
      <div className="grid grid-cols-2 md:grid-cols-5 gap-3">
        {Array.from({ length: 5 }).map((_, i) => (
          <div
            key={i}
            className="bg-card/30 border border-border/30 rounded p-3 space-y-2"
          >
            <div className="h-3 w-20 rounded bg-muted/40" />
            <div className="h-7 w-24 rounded bg-muted/50" />
            <div className="h-3 w-16 rounded bg-muted/20" />
          </div>
        ))}
      </div>

      {/* Allocation + Positions skeleton */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-3">
        <div className="rounded-xl border border-border/30 bg-card/30 p-4 space-y-3">
          <div className="h-4 w-28 rounded bg-muted/40" />
          {Array.from({ length: 3 }).map((_, i) => (
            <div key={i} className="space-y-1">
              <div className="flex justify-between">
                <div className="h-3 w-12 rounded bg-muted/30" />
                <div className="h-3 w-8 rounded bg-muted/20" />
              </div>
              <div className="h-2 w-full rounded-full bg-muted/20" />
            </div>
          ))}
        </div>
        <div className="lg:col-span-2 rounded-xl border border-border/30 bg-card/30 p-4 space-y-3">
          <div className="h-4 w-32 rounded bg-muted/40" />
          {Array.from({ length: 4 }).map((_, i) => (
            <div key={i} className="flex gap-4">
              <div className="h-4 w-14 rounded bg-muted/30" />
              <div className="h-4 w-12 rounded bg-muted/20" />
              <div className="h-4 w-16 rounded bg-muted/30" />
              <div className="h-4 w-16 rounded bg-muted/20" />
              <div className="h-4 flex-1 rounded bg-muted/10" />
            </div>
          ))}
        </div>
      </div>

      {/* Equity curve skeleton */}
      <div className="rounded-xl border border-border/30 bg-card/30 p-4">
        <div className="h-4 w-24 rounded bg-muted/40 mb-3" />
        <div className="h-48 w-full rounded bg-muted/15" />
      </div>

      {/* Trade stats skeleton */}
      <div className="grid grid-cols-2 md:grid-cols-5 gap-3">
        {Array.from({ length: 5 }).map((_, i) => (
          <div
            key={i}
            className="bg-card/30 border border-border/30 rounded p-3 space-y-2"
          >
            <div className="h-3 w-16 rounded bg-muted/40" />
            <div className="h-6 w-14 rounded bg-muted/50" />
          </div>
        ))}
      </div>
    </div>
  );
}
