"use client";

export default function Error({
  error,
  reset,
}: {
  error: Error & { digest?: string };
  reset: () => void;
}) {
  return (
    <div className="flex items-center justify-center min-h-[50vh] p-4">
      <div className="text-center space-y-4">
        <h2 className="text-lg font-mono text-hud-red">Something went wrong</h2>
        <p className="text-sm font-mono text-muted-foreground">{error.message}</p>
        <button
          onClick={reset}
          className="px-4 py-2 border border-hud-cyan text-hud-cyan rounded hover:bg-hud-cyan/10 transition-colors font-mono text-sm"
        >
          Try again
        </button>
      </div>
    </div>
  );
}
