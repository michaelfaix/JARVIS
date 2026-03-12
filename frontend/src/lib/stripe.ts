// =============================================================================
// src/lib/stripe.ts — Stripe client configuration
// =============================================================================

import { loadStripe, type Stripe as StripeClient } from "@stripe/stripe-js";

let stripePromise: Promise<StripeClient | null> | null = null;

/**
 * Lazy-load the Stripe.js client (browser-side).
 * Returns null if the publishable key is not configured.
 */
export function getStripe() {
  if (!stripePromise) {
    const key = process.env.NEXT_PUBLIC_STRIPE_PUBLISHABLE_KEY;
    if (!key || key === "pk_test_placeholder") {
      return null;
    }
    stripePromise = loadStripe(key);
  }
  return stripePromise;
}

/**
 * Server-side Stripe instance.
 * Only import this in server code (API routes, server actions).
 */
export function getStripeServer() {
  // Dynamic import to avoid bundling stripe in client code
  // eslint-disable-next-line @typescript-eslint/no-require-imports
  const Stripe = require("stripe").default;
  const key = process.env.STRIPE_SECRET_KEY;
  if (!key || key === "sk_test_placeholder") {
    return null;
  }
  return new Stripe(key, {
    apiVersion: "2026-02-25.clover",
    typescript: true,
  });
}
