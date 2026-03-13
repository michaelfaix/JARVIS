// =============================================================================
// src/components/layout/footer.tsx — HUD-styled footer
// =============================================================================

export function Footer() {
  return (
    <footer className="border-t border-hud-border px-4 py-2">
      <div className="flex flex-wrap justify-between gap-2 font-mono text-[9px] text-muted-foreground/60 uppercase tracking-wider">
        <span>JARVIS MASP v7.1 · Not a trading system · No real money · No broker API</span>
        <span>Analysis & Research Platform</span>
      </div>
    </footer>
  );
}
