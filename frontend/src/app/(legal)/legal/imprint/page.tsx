export const metadata = { title: "Imprint — JARVIS Trader" };

export default function ImprintPage() {
  return (
    <article className="prose prose-invert prose-sm max-w-none">
      <h1 className="text-2xl font-bold text-white">Impressum / Imprint</h1>
      <p className="text-muted-foreground text-sm">According to § 5 TMG (German Telemedia Act)</p>

      <h2 className="text-lg font-semibold text-white mt-8">Responsible</h2>
      <p className="text-muted-foreground">
        Michael Faix<br />
        Germany
      </p>

      <h2 className="text-lg font-semibold text-white mt-8">Contact</h2>
      <p className="text-muted-foreground">
        Email: contact@jarvis-trader.app
      </p>

      <h2 className="text-lg font-semibold text-white mt-8">Disclaimer</h2>
      <p className="text-muted-foreground">
        See <a href="/legal/disclaimer" className="text-blue-400 hover:underline">Disclaimer</a> for
        information about the nature of this service. JARVIS Trader is a research and educational
        tool. It does not constitute financial advice.
      </p>

      <h2 className="text-lg font-semibold text-white mt-8">Copyright</h2>
      <p className="text-muted-foreground">
        &copy; {new Date().getFullYear()} JARVIS Trader. All rights reserved. The content of
        this website, including all text, graphics, and code, is protected by copyright.
      </p>
    </article>
  );
}
