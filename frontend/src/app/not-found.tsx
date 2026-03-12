import Link from "next/link";

export default function NotFound() {
  return (
    <div className="flex min-h-screen flex-col items-center justify-center bg-background px-6 text-center">
      <div className="mb-6 flex h-16 w-16 items-center justify-center rounded-2xl bg-blue-600/20">
        <span className="text-3xl font-bold text-blue-400">?</span>
      </div>
      <h1 className="text-4xl font-bold text-white">404</h1>
      <p className="mt-2 text-sm text-muted-foreground">
        This page doesn&apos;t exist or has been moved.
      </p>
      <div className="mt-6 flex gap-3">
        <Link
          href="/"
          className="rounded-lg bg-blue-600 px-5 py-2.5 text-sm font-medium text-white hover:bg-blue-700 transition-colors"
        >
          Go to Dashboard
        </Link>
        <Link
          href="/landing"
          className="rounded-lg border border-border/50 px-5 py-2.5 text-sm font-medium text-muted-foreground hover:text-white hover:border-border transition-colors"
        >
          Landing Page
        </Link>
      </div>
    </div>
  );
}
