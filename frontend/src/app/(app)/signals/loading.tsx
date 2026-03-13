export default function SignalsLoading() {
  return (
    <div className="p-4 space-y-4 animate-pulse">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div className="h-6 w-36 rounded bg-muted/50" />
        <div className="h-8 w-24 rounded bg-muted/30" />
      </div>

      {/* Filter bar skeleton */}
      <div className="rounded-xl border border-border/30 bg-card/30 p-3 flex items-center gap-3">
        <div className="h-7 w-20 rounded bg-muted/30" />
        <div className="h-7 w-20 rounded bg-muted/30" />
        <div className="h-7 w-20 rounded bg-muted/30" />
        <div className="flex-1" />
        <div className="h-7 w-16 rounded bg-muted/20" />
      </div>

      {/* Signal cards skeleton */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-3">
        {Array.from({ length: 6 }).map((_, i) => (
          <div
            key={i}
            className="rounded-xl border border-border/30 bg-card/30 p-4 space-y-3"
          >
            <div className="flex items-center justify-between">
              <div className="h-5 w-16 rounded bg-muted/50" />
              <div className="h-5 w-14 rounded bg-muted/30" />
            </div>
            <div className="h-4 w-24 rounded bg-muted/30" />
            <div className="flex gap-2">
              <div className="h-3 w-16 rounded bg-muted/20" />
              <div className="h-3 w-16 rounded bg-muted/20" />
              <div className="h-3 w-16 rounded bg-muted/20" />
            </div>
            <div className="h-8 w-full rounded bg-muted/20" />
          </div>
        ))}
      </div>
    </div>
  );
}
