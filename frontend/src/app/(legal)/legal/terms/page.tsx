export const metadata = { title: "Terms of Service — JARVIS Trader" };

export default function TermsPage() {
  return (
    <article className="prose prose-invert prose-sm max-w-none">
      <h1 className="text-2xl font-bold text-white">Terms of Service</h1>
      <p className="text-muted-foreground text-sm">Last updated: March 2026</p>

      <h2 className="text-lg font-semibold text-white mt-8">1. Service Description</h2>
      <p className="text-muted-foreground">
        JARVIS Trader is an AI-powered trading intelligence platform that provides market
        regime detection, trading signals, paper trading simulation, and strategy backtesting.
        The service is provided &quot;as is&quot; for research and educational purposes.
      </p>

      <h2 className="text-lg font-semibold text-white mt-8">2. Eligibility</h2>
      <p className="text-muted-foreground">
        You must be at least 18 years old to use this service. By creating an account,
        you confirm that you meet this requirement.
      </p>

      <h2 className="text-lg font-semibold text-white mt-8">3. Account</h2>
      <p className="text-muted-foreground">
        You are responsible for maintaining the security of your account credentials.
        You must not share your account with others or create multiple accounts.
      </p>

      <h2 className="text-lg font-semibold text-white mt-8">4. Subscription Tiers</h2>
      <ul className="text-muted-foreground space-y-1">
        <li><strong className="text-white">Free:</strong> Limited features (3 assets, $10k paper trading, delayed signals)</li>
        <li><strong className="text-white">Pro (&euro;29/month):</strong> Full features including AI Chat, all assets, real-time signals</li>
        <li><strong className="text-white">Enterprise (&euro;199/month):</strong> Everything in Pro plus API access and priority support</li>
      </ul>
      <p className="text-muted-foreground">
        Subscriptions auto-renew monthly. You may cancel at any time; access continues
        until the end of the billing period.
      </p>

      <h2 className="text-lg font-semibold text-white mt-8">5. Disclaimer</h2>
      <p className="text-muted-foreground">
        See our full <a href="/legal/disclaimer" className="text-blue-400 hover:underline">Disclaimer</a>.
        JARVIS Trader does not provide financial advice. All trading is simulated.
      </p>

      <h2 className="text-lg font-semibold text-white mt-8">6. Limitation of Liability</h2>
      <p className="text-muted-foreground">
        To the maximum extent permitted by law, JARVIS Trader and its operators shall not
        be liable for any indirect, incidental, or consequential damages arising from your
        use of the platform. Our total liability is limited to the amount you paid for the
        service in the 12 months preceding the claim.
      </p>

      <h2 className="text-lg font-semibold text-white mt-8">7. Termination</h2>
      <p className="text-muted-foreground">
        We may suspend or terminate your account for violations of these terms, abuse of
        the service, or fraudulent activity. You may delete your account at any time via
        Settings.
      </p>

      <h2 className="text-lg font-semibold text-white mt-8">8. Governing Law</h2>
      <p className="text-muted-foreground">
        These terms are governed by the laws of the Federal Republic of Germany.
        The courts of Germany shall have exclusive jurisdiction.
      </p>
    </article>
  );
}
