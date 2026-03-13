// =============================================================================
// src/app/api/sentiment/route.ts — Server-side sentiment proxy
//
// Fetches CNN Fear & Greed (bypasses CORS) and CoinGecko global data.
// Caches results for 60s to avoid rate limits.
// =============================================================================

import { NextResponse } from "next/server";

// ---------------------------------------------------------------------------
// In-memory cache (per serverless instance)
// ---------------------------------------------------------------------------

interface CacheEntry<T> {
  data: T;
  ts: number;
}

const CACHE_TTL = 60_000; // 60s
let cnnCache: CacheEntry<CnnData> | null = null;
let geckoCache: CacheEntry<GeckoData> | null = null;

interface CnnData {
  score: number;
  rating: string;
  history: number[];
}

interface GeckoData {
  btcDominance: number;
  totalMarketCap: number;
  totalVolume: number;
}

// ---------------------------------------------------------------------------
// Fetch helpers
// ---------------------------------------------------------------------------

async function fetchCnn(): Promise<CnnData> {
  if (cnnCache && Date.now() - cnnCache.ts < CACHE_TTL) return cnnCache.data;

  const res = await fetch(
    "https://production.dataviz.cnn.io/index/fearandgreed/graphdata",
    {
      signal: AbortSignal.timeout(8000),
      headers: { "User-Agent": "JARVIS-Trader/1.0" },
    }
  );
  if (!res.ok) throw new Error(`CNN ${res.status}`);
  const json = await res.json();

  const fng = json?.fear_and_greed;
  if (!fng || typeof fng.score !== "number") throw new Error("Invalid CNN data");

  const histData = json?.fear_and_greed_historical?.data ?? [];
  const history = histData
    .slice(-7)
    .map((d: { x: number; y: number }) => Math.round(d.y))
    .filter((v: number) => !isNaN(v));

  const data: CnnData = {
    score: Math.round(fng.score),
    rating: typeof fng.rating === "string" ? fng.rating : "",
    history,
  };

  cnnCache = { data, ts: Date.now() };
  return data;
}

async function fetchGecko(): Promise<GeckoData> {
  if (geckoCache && Date.now() - geckoCache.ts < CACHE_TTL)
    return geckoCache.data;

  const res = await fetch("https://api.coingecko.com/api/v3/global", {
    signal: AbortSignal.timeout(8000),
  });
  if (!res.ok) throw new Error(`CoinGecko ${res.status}`);
  const json = await res.json();

  const d = json?.data;
  const data: GeckoData = {
    btcDominance:
      typeof d?.market_cap_percentage?.btc === "number"
        ? Math.round(d.market_cap_percentage.btc * 10) / 10
        : 0,
    totalMarketCap: d?.total_market_cap?.usd ?? 0,
    totalVolume: d?.total_volume?.usd ?? 0,
  };

  geckoCache = { data, ts: Date.now() };
  return data;
}

// ---------------------------------------------------------------------------
// Simple rate limiter (per serverless instance)
// ---------------------------------------------------------------------------

const RATE_WINDOW = 60_000; // 1 minute
const RATE_LIMIT = 30; // max requests per window
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

/** Sanitize error — never expose stack traces or internal details */
function sanitizeError(err: unknown): string {
  if (err instanceof Error) {
    // Only pass through known safe error messages (HTTP status codes)
    const match = err.message.match(/^(CNN|CoinGecko|API|Proxy)\s+\d{3}$/);
    if (match) return err.message;
    if (err.message === "Invalid CNN data") return "Invalid upstream data";
  }
  return "Upstream service unavailable";
}

// ---------------------------------------------------------------------------
// GET /api/sentiment
// ---------------------------------------------------------------------------

export async function GET() {
  if (isRateLimited()) {
    return NextResponse.json(
      { error: "Too many requests" },
      { status: 429, headers: { "Retry-After": "60" } }
    );
  }

  const [cnn, gecko] = await Promise.allSettled([fetchCnn(), fetchGecko()]);

  return NextResponse.json({
    cnn: cnn.status === "fulfilled" ? cnn.value : null,
    cnnError:
      cnn.status === "rejected" ? sanitizeError(cnn.reason) : null,
    gecko: gecko.status === "fulfilled" ? gecko.value : null,
    geckoError:
      gecko.status === "rejected" ? sanitizeError(gecko.reason) : null,
    cached: {
      cnn: cnnCache ? Date.now() - cnnCache.ts < CACHE_TTL : false,
      gecko: geckoCache ? Date.now() - geckoCache.ts < CACHE_TTL : false,
    },
  });
}
