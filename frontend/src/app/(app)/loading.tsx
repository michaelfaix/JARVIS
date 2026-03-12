export default function AppLoading() {
  return (
    <div className="p-6 space-y-6 animate-pulse">
      {/* Header skeleton */}
      <div className="h-14 flex items-center gap-4 border-b border-border/30 pb-4">
        <div className="h-6 w-32 rounded bg-muted/50" />
        <div className="h-4 w-48 rounded bg-muted/30" />
      </div>

      {/* Cards skeleton */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        {Array.from({ length: 4 }).map((_, i) => (
          <div key={i} className="rounded-xl border border-border/30 bg-card/30 p-4 space-y-2">
            <div className="h-3 w-20 rounded bg-muted/40" />
            <div className="h-7 w-24 rounded bg-muted/50" />
          </div>
        ))}
      </div>

      {/* Main content skeleton */}
      <div className="rounded-xl border border-border/30 bg-card/30 p-6">
        <div className="h-5 w-40 rounded bg-muted/40 mb-4" />
        <div className="h-64 w-full rounded bg-muted/20" />
      </div>

      {/* Table skeleton */}
      <div className="rounded-xl border border-border/30 bg-card/30 p-6 space-y-3">
        <div className="h-5 w-32 rounded bg-muted/40" />
        {Array.from({ length: 5 }).map((_, i) => (
          <div key={i} className="flex gap-4">
            <div className="h-4 w-16 rounded bg-muted/30" />
            <div className="h-4 w-12 rounded bg-muted/20" />
            <div className="h-4 w-20 rounded bg-muted/30" />
            <div className="h-4 w-16 rounded bg-muted/20" />
            <div className="h-4 flex-1 rounded bg-muted/10" />
          </div>
        ))}
      </div>
    </div>
  );
}
