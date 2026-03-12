export const metadata = { title: "Privacy Policy — JARVIS Trader" };

export default function PrivacyPage() {
  return (
    <article className="prose prose-invert prose-sm max-w-none">
      <h1 className="text-2xl font-bold text-white">Privacy Policy (DSGVO)</h1>
      <p className="text-muted-foreground text-sm">Last updated: March 2026</p>

      <h2 className="text-lg font-semibold text-white mt-8">1. Controller</h2>
      <p className="text-muted-foreground">
        Michael Faix (see <a href="/legal/imprint" className="text-blue-400 hover:underline">Imprint</a> for contact details).
      </p>

      <h2 className="text-lg font-semibold text-white mt-8">2. Data We Collect</h2>
      <ul className="text-muted-foreground space-y-1">
        <li><strong className="text-white">Account data:</strong> Email address, hashed password (via Supabase Auth)</li>
        <li><strong className="text-white">Usage data:</strong> Paper trading positions, settings, trade history</li>
        <li><strong className="text-white">Technical data:</strong> IP address, browser type, device info (server logs)</li>
        <li><strong className="text-white">OAuth data:</strong> Google profile name (if you use Google Sign-In)</li>
      </ul>

      <h2 className="text-lg font-semibold text-white mt-8">3. Legal Basis (Art. 6 GDPR)</h2>
      <ul className="text-muted-foreground space-y-1">
        <li>Contract performance (Art. 6(1)(b)) — providing the service you signed up for</li>
        <li>Legitimate interest (Art. 6(1)(f)) — analytics, security, fraud prevention</li>
        <li>Consent (Art. 6(1)(a)) — optional cookies, marketing emails</li>
      </ul>

      <h2 className="text-lg font-semibold text-white mt-8">4. Data Storage</h2>
      <p className="text-muted-foreground">
        Your data is stored in Supabase (PostgreSQL) hosted in the EU (Frankfurt region).
        Row-Level Security ensures you can only access your own data. We do not sell
        your data to third parties.
      </p>

      <h2 className="text-lg font-semibold text-white mt-8">5. Your Rights</h2>
      <p className="text-muted-foreground">Under GDPR you have the right to:</p>
      <ul className="text-muted-foreground space-y-1">
        <li>Access your personal data (Art. 15)</li>
        <li>Rectify inaccurate data (Art. 16)</li>
        <li>Delete your account and data (Art. 17)</li>
        <li>Restrict processing (Art. 18)</li>
        <li>Data portability — export your trades as CSV (Art. 20)</li>
        <li>Object to processing (Art. 21)</li>
      </ul>
      <p className="text-muted-foreground">
        To exercise these rights, email us at the address listed in the Imprint.
      </p>

      <h2 className="text-lg font-semibold text-white mt-8">6. Cookies</h2>
      <p className="text-muted-foreground">
        We use essential cookies for authentication (Supabase session). No third-party
        tracking cookies are used. Analytics cookies are only set with your consent.
      </p>

      <h2 className="text-lg font-semibold text-white mt-8">7. Data Retention</h2>
      <p className="text-muted-foreground">
        Account data is retained while your account is active. You may delete your
        account at any time, which removes all associated data within 30 days.
        Server logs are retained for 90 days.
      </p>
    </article>
  );
}
