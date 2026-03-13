// =============================================================================
// src/app/api/quotes/route.ts — Server-side stock/commodity quote proxy
//
// Fetches real-time quotes for non-crypto assets (SPY, AAPL, NVDA, TSLA, GLD)
// via Yahoo Finance v8 quote endpoint. Caches for 30s to stay within limits.
// =============================================================================

import { NextResponse } from "next/server";

// ---------------------------------------------------------------------------
// In-memory cache (per serverless instance)
// ---------------------------------------------------------------------------

interface CacheEntry {
  prices: Record<string, number>;
  ts: number;
}

const CACHE_TTL = 30_000; // 30s — Yahoo allows frequent requests
let cache: CacheEntry | null = null;

// Rate limiter
const RATE_WINDOW = 60_000;
const RATE_LIMIT = 30;
let rateWindowStart = Date.now();
let rateCount = 0;

function isRateLimited(): boolean {
  const now = Date.now();
  if (now - rateWindowStart > RATE_WINDOW) {
    rateWindowStart = now;
    rateCount = 0;
  }
  rateCount++;
  return rateCount > RATE_LIMIT;
}

// Symbols to fetch (non-crypto — crypto comes from Binance directly)
const SYMBOLS = ["SPY", "AAPL", "NVDA", "TSLA", "GLD"];

// ---------------------------------------------------------------------------
// Yahoo Finance quote fetcher
// ---------------------------------------------------------------------------

interface YahooQuoteResult {
  symbol: string;
  regularMarketPrice?: number;
}

async function fetchYahooQuotes(): Promise<Record<string, number>> {
  if (cache && Date.now() - cache.ts < CACHE_TTL) return cache.prices;

  const symbolList = SYMBOLS.join(",");
  const url = `https://query1.finance.yahoo.com/v7/finance/quote?symbols=${symbolList}&fields=regularMarketPrice`;

  const res = await fetch(url, {
    signal: AbortSignal.timeout(8000),
    headers: {
      "User-Agent": "JARVIS-Trader/1.0",
    },
  });

  if (!res.ok) throw new Error(`Yahoo ${res.status}`);
  const json = await res.json();

  const results: YahooQuoteResult[] = json?.quoteResponse?.result ?? [];
  const prices: Record<string, number> = {};

  for (const quote of results) {
    if (quote.symbol && typeof quote.regularMarketPrice === "number") {
      prices[quote.symbol] = quote.regularMarketPrice;
    }
  }

  if (Object.keys(prices).length === 0) {
    throw new Error("No valid quotes returned");
  }

  cache = { prices, ts: Date.now() };
  return prices;
}

// ---------------------------------------------------------------------------
// GET /api/quotes
// ---------------------------------------------------------------------------

export async function GET() {
  if (isRateLimited()) {
    return NextResponse.json(
      { error: "Too many requests" },
      { status: 429, headers: { "Retry-After": "30" } }
    );
  }

  try {
    const prices = await fetchYahooQuotes();
    return NextResponse.json({
      prices,
      cached: cache ? Date.now() - cache.ts < CACHE_TTL : false,
      source: "yahoo",
    });
  } catch {
    return NextResponse.json({
      prices: null,
      error: "Quote service unavailable",
      cached: false,
      source: "yahoo",
    });
  }
}
