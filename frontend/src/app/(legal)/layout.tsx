import Link from "next/link";

export default function LegalLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <div className="min-h-screen bg-background">
      <nav className="border-b border-border/30 bg-card/50">
        <div className="mx-auto flex h-14 max-w-4xl items-center justify-between px-6">
          <Link href="/landing" className="flex items-center gap-2">
            <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-blue-600 text-sm font-bold text-white">
              J
            </div>
            <span className="text-sm font-bold text-white">JARVIS Trader</span>
          </Link>
          <div className="flex items-center gap-4 text-xs text-muted-foreground">
            <Link href="/legal/terms" className="hover:text-white transition-colors">Terms</Link>
            <Link href="/legal/privacy" className="hover:text-white transition-colors">Privacy</Link>
            <Link href="/legal/disclaimer" className="hover:text-white transition-colors">Disclaimer</Link>
            <Link href="/legal/imprint" className="hover:text-white transition-colors">Imprint</Link>
          </div>
        </div>
      </nav>
      <main className="mx-auto max-w-4xl px-6 py-12">
        {children}
      </main>
    </div>
  );
}
