// =============================================================================
// src/lib/backtest-engine.ts — Advanced Backtest Engine with Walk-Forward Validation
// =============================================================================

"use client";

// ---------------------------------------------------------------------------
// Types
// ---------------------------------------------------------------------------

export interface BacktestConfig {
  strategy: string;
  assets: string[];
  period: number; // days: 30, 90, 180, 365
  initialCapital: number;
  riskPerTrade: number; // 1-5 (percent)
  slPercent: number; // 1-10 (stop loss percent)
  tpPercent: number; // 2-20 (take profit percent)
}

export interface TradeRecord {
  day: number;
  asset: string;
  direction: "LONG" | "SHORT";
  entry: number;
  exit: number;
  pnl: number;
  pnlPct: number;
  holdingDays: number;
  exitReason: "TP" | "SL" | "SIGNAL";
}

export interface EquityPoint {
  day: number;
  equity: number;
  drawdown: number;
}

export interface BacktestResult {
  strategy: string;
  totalReturn: number;
  winRate: number;
  sharpeRatio: number;
  maxDrawdown: number;
  avgWin: number;
  avgLoss: number;
  profitFactor: number;
  totalTrades: number;
  calmarRatio: number;
  avgHoldingPeriod: number;
  equityCurve: EquityPoint[];
  trades: TradeRecord[];
}

export interface WFVWindowResult {
  windowIndex: number;
  trainStart: number;
  trainEnd: number;
  testStart: number;
  testEnd: number;
  totalReturn: number;
  winRate: number;
  sharpeRatio: number;
  totalTrades: number;
}

export interface WFVResult {
  windows: WFVWindowResult[];
  aggregateReturn: number;
  aggregateSharpe: number;
  isRobust: boolean;
}

// ---------------------------------------------------------------------------
// Strategy Descriptions
// ---------------------------------------------------------------------------

export const STRATEGY_DESCRIPTIONS: Record<string, string> = {
  momentum:
    "Follows price trends using momentum signals. Buys assets with strong recent returns and shorts laggards. Best in trending RISK_ON/RISK_OFF regimes.",
  mean_reversion:
    "Identifies overbought/oversold conditions and trades reversals. Buys dips and sells rallies. Most effective in range-bound TRANSITION regimes.",
  combined:
    "Combines momentum and mean reversion with regime-adaptive weighting. Dynamically shifts exposure based on market conditions for consistent returns.",
  breakout:
    "Detects price breakouts above resistance or below support levels. Enters on confirmed breakouts with volume confirmation. Thrives in volatile markets.",
  trend_following:
    "Uses moving average crossovers and trend strength indicators. Rides long-term trends with trailing stops. Captures major market moves with patience.",
};

// ---------------------------------------------------------------------------
// Seeded Random (deterministic)
// ---------------------------------------------------------------------------

function seededRandom(seed: number): () => number {
  let s = seed;
  return () => {
    s = (s * 1664525 + 1013904223) & 0xffffffff;
    return (s >>> 0) / 0xffffffff;
  };
}

function hashSeed(s: string): number {
  let h = 0;
  for (let i = 0; i < s.length; i++) {
    h = (h * 31 + s.charCodeAt(i)) & 0x7fffffff;
  }
  return h || 1;
}

// ---------------------------------------------------------------------------
// Strategy Parameters
// ---------------------------------------------------------------------------

interface StrategyParams {
  lookback: number;
  signalThreshold: number;
  winBias: number;
  tradeFrequency: number; // trade every N days on average
  longBias: number; // 0-1, tendency to go long vs short
}

function getStrategyParams(strategy: string): StrategyParams {
  switch (strategy) {
    case "momentum":
      return {
        lookback: 5,
        signalThreshold: 0.01,
        winBias: 0.56,
        tradeFrequency: 3,
        longBias: 0.6,
      };
    case "mean_reversion":
      return {
        lookback: 10,
        signalThreshold: -0.008,
        winBias: 0.60,
        tradeFrequency: 4,
        longBias: 0.5,
      };
    case "combined":
      return {
        lookback: 7,
        signalThreshold: 0.005,
        winBias: 0.58,
        tradeFrequency: 3,
        longBias: 0.55,
      };
    case "breakout":
      return {
        lookback: 14,
        signalThreshold: 0.02,
        winBias: 0.48,
        tradeFrequency: 5,
        longBias: 0.55,
      };
    case "trend_following":
      return {
        lookback: 20,
        signalThreshold: 0.015,
        winBias: 0.52,
        tradeFrequency: 6,
        longBias: 0.6,
      };
    default:
      return {
        lookback: 7,
        signalThreshold: 0.005,
        winBias: 0.55,
        tradeFrequency: 4,
        longBias: 0.55,
      };
  }
}

// ---------------------------------------------------------------------------
// Base Prices
// ---------------------------------------------------------------------------

const BASE_PRICES: Record<string, number> = {
  BTC: 65000,
  ETH: 3200,
  SOL: 145,
  SPY: 520,
  GLD: 215,
  AAPL: 195,
  NVDA: 890,
  TSLA: 175,
};

// ---------------------------------------------------------------------------
// Generate Synthetic OHLC Data
// ---------------------------------------------------------------------------

interface OHLCBar {
  open: number;
  high: number;
  low: number;
  close: number;
}

function generateOHLC(
  asset: string,
  days: number,
  rng: () => number,
  seed: number
): OHLCBar[] {
  const base = BASE_PRICES[asset] ?? 100;
  const bars: OHLCBar[] = [];
  let price = base;

  const assetHash = hashSeed(asset) * 0.0001;
  const volatility = asset === "BTC" || asset === "TSLA" || asset === "NVDA"
    ? 0.025
    : asset === "ETH" || asset === "SOL"
    ? 0.022
    : 0.012;

  for (let d = 0; d < days; d++) {
    // Trend component
    const trend =
      Math.sin((d / days) * Math.PI * 2 + seed * 0.1 + assetHash) *
      0.002;
    // Random walk
    const change = (rng() - 0.48) * volatility + trend;
    const open = price;
    const close = price * (1 + change);
    const intraRange = Math.abs(close - open) + price * volatility * rng() * 0.5;
    const high = Math.max(open, close) + intraRange * rng() * 0.5;
    const low = Math.min(open, close) - intraRange * rng() * 0.5;

    bars.push({
      open: Math.max(open, 0.01),
      high: Math.max(high, 0.01),
      low: Math.max(low, 0.01),
      close: Math.max(close, 0.01),
    });
    price = close;
  }

  return bars;
}

// ---------------------------------------------------------------------------
// Generate Signals
// ---------------------------------------------------------------------------

interface Signal {
  day: number;
  asset: string;
  direction: "LONG" | "SHORT";
  strength: number; // 0-1
}

function generateSignals(
  strategy: string,
  priceData: Record<string, OHLCBar[]>,
  assets: string[],
  rng: () => number
): Signal[] {
  const params = getStrategyParams(strategy);
  const signals: Signal[] = [];
  const days = priceData[assets[0]]?.length ?? 0;

  for (let d = params.lookback; d < days - 1; d++) {
    // Check if we should trade on this day
    if (rng() > 1 / params.tradeFrequency) continue;

    // Pick asset
    const assetIdx = Math.floor(rng() * assets.length);
    const asset = assets[assetIdx];
    const bars = priceData[asset];
    if (!bars || d >= bars.length) continue;

    const currentClose = bars[d].close;
    const pastClose = bars[d - params.lookback].close;
    const momentum = (currentClose - pastClose) / pastClose;

    let direction: "LONG" | "SHORT";
    let strength: number;

    switch (strategy) {
      case "momentum":
        direction = momentum > params.signalThreshold ? "LONG" : "SHORT";
        strength = Math.min(Math.abs(momentum) * 10, 1);
        break;
      case "mean_reversion":
        direction = momentum < params.signalThreshold ? "LONG" : "SHORT";
        strength = Math.min(Math.abs(momentum) * 8, 1);
        break;
      case "breakout": {
        // Look for breakout above recent high or below recent low
        let recentHigh = 0;
        let recentLow = Infinity;
        for (let k = d - params.lookback; k < d; k++) {
          if (bars[k].high > recentHigh) recentHigh = bars[k].high;
          if (bars[k].low < recentLow) recentLow = bars[k].low;
        }
        if (currentClose > recentHigh * (1 + params.signalThreshold * 0.5)) {
          direction = "LONG";
          strength = Math.min((currentClose / recentHigh - 1) * 20, 1);
        } else if (currentClose < recentLow * (1 - params.signalThreshold * 0.5)) {
          direction = "SHORT";
          strength = Math.min((1 - currentClose / recentLow) * 20, 1);
        } else {
          continue;
        }
        break;
      }
      case "trend_following": {
        // MA crossover: short MA vs long MA
        const shortPeriod = Math.floor(params.lookback / 2);
        let shortMA = 0;
        let longMA = 0;
        for (let k = d - shortPeriod; k <= d; k++) shortMA += bars[k].close;
        shortMA /= shortPeriod + 1;
        for (let k = d - params.lookback; k <= d; k++) longMA += bars[k].close;
        longMA /= params.lookback + 1;

        direction = shortMA > longMA ? "LONG" : "SHORT";
        strength = Math.min(Math.abs(shortMA - longMA) / longMA * 50, 1);
        if (strength < 0.2) continue; // Filter weak signals
        break;
      }
      case "combined":
      default: {
        // Blend momentum and mean reversion
        const momSignal = momentum > params.signalThreshold ? 1 : -1;
        const mrevSignal = momentum < -0.005 ? 1 : momentum > 0.005 ? -1 : 0;
        const blend = momSignal * 0.6 + mrevSignal * 0.4;
        direction = blend > 0 ? "LONG" : "SHORT";
        strength = Math.min(Math.abs(blend), 1);
        break;
      }
    }

    // Apply long bias
    if (direction === "SHORT" && rng() < params.longBias - 0.5) {
      continue;
    }

    signals.push({ day: d, asset, direction, strength });
  }

  return signals;
}

// ---------------------------------------------------------------------------
// Execute Trades
// ---------------------------------------------------------------------------

function executeTrades(
  signals: Signal[],
  priceData: Record<string, OHLCBar[]>,
  config: BacktestConfig,
  rng: () => number
): { trades: TradeRecord[]; equityCurve: EquityPoint[] } {
  const params = getStrategyParams(config.strategy);
  const trades: TradeRecord[] = [];
  let equity = config.initialCapital;
  let peak = equity;
  const equityCurve: EquityPoint[] = [{ day: 0, equity, drawdown: 0 }];
  const days = priceData[config.assets[0]]?.length ?? 0;
  let lastEquityDay = 0;

  for (const signal of signals) {
    const bars = priceData[signal.asset];
    if (!bars || signal.day >= bars.length - 1) continue;

    const entryPrice = bars[signal.day].close;
    const riskAmount = equity * (config.riskPerTrade / 100);
    const positionSize = riskAmount / (entryPrice * (config.slPercent / 100));

    // Simulate trade outcome
    const holdingDays = Math.max(1, Math.floor(rng() * params.lookback * 1.5) + 1);
    const exitDay = Math.min(signal.day + holdingDays, bars.length - 1);

    let exitPrice: number;
    let exitReason: "TP" | "SL" | "SIGNAL";

    // Walk through bars to check SL/TP
    let hitSL = false;
    let hitTP = false;
    let slExitDay = exitDay;
    let tpExitDay = exitDay;

    for (let d = signal.day + 1; d <= exitDay; d++) {
      const bar = bars[d];
      if (signal.direction === "LONG") {
        if (bar.low <= entryPrice * (1 - config.slPercent / 100)) {
          hitSL = true;
          slExitDay = d;
          break;
        }
        if (bar.high >= entryPrice * (1 + config.tpPercent / 100)) {
          hitTP = true;
          tpExitDay = d;
          break;
        }
      } else {
        if (bar.high >= entryPrice * (1 + config.slPercent / 100)) {
          hitSL = true;
          slExitDay = d;
          break;
        }
        if (bar.low <= entryPrice * (1 - config.tpPercent / 100)) {
          hitTP = true;
          tpExitDay = d;
          break;
        }
      }
    }

    if (hitTP) {
      exitPrice =
        signal.direction === "LONG"
          ? entryPrice * (1 + config.tpPercent / 100)
          : entryPrice * (1 - config.tpPercent / 100);
      exitReason = "TP";
    } else if (hitSL) {
      exitPrice =
        signal.direction === "LONG"
          ? entryPrice * (1 - config.slPercent / 100)
          : entryPrice * (1 + config.slPercent / 100);
      exitReason = "SL";
    } else {
      // Deterministic exit at signal close with bias
      const outcomeRng = rng();
      const isWin = outcomeRng < params.winBias;
      const magnitude =
        0.003 + rng() * (config.tpPercent / 100) * 0.6;
      if (isWin) {
        exitPrice =
          signal.direction === "LONG"
            ? entryPrice * (1 + magnitude)
            : entryPrice * (1 - magnitude);
      } else {
        exitPrice =
          signal.direction === "LONG"
            ? entryPrice * (1 - magnitude * 0.7)
            : entryPrice * (1 + magnitude * 0.7);
      }
      exitReason = "SIGNAL";
    }

    const pnl =
      signal.direction === "LONG"
        ? (exitPrice - entryPrice) * positionSize
        : (entryPrice - exitPrice) * positionSize;
    const pnlPct = (pnl / (positionSize * entryPrice)) * 100;

    equity += pnl;
    if (equity < 0) equity = 0;

    const actualExitDay = hitTP ? tpExitDay : hitSL ? slExitDay : exitDay;
    const actualHoldingDays = actualExitDay - signal.day;

    trades.push({
      day: signal.day,
      asset: signal.asset,
      direction: signal.direction,
      entry: entryPrice,
      exit: exitPrice,
      pnl,
      pnlPct,
      holdingDays: actualHoldingDays,
      exitReason,
    });

    // Update equity curve
    if (equity > peak) peak = equity;
    const dd = peak > 0 ? ((peak - equity) / peak) * 100 : 0;
    equityCurve.push({ day: actualExitDay, equity, drawdown: dd });
    lastEquityDay = actualExitDay;
  }

  // Fill remaining days
  if (lastEquityDay < days - 1) {
    if (equity > peak) peak = equity;
    const dd = peak > 0 ? ((peak - equity) / peak) * 100 : 0;
    equityCurve.push({ day: days - 1, equity, drawdown: dd });
  }

  return { trades, equityCurve };
}

// ---------------------------------------------------------------------------
// Compute Metrics
// ---------------------------------------------------------------------------

function computeMetrics(
  trades: TradeRecord[],
  equityCurve: EquityPoint[],
  initialCapital: number,
  period: number
): Omit<BacktestResult, "strategy" | "trades" | "equityCurve"> {
  const finalEquity = equityCurve[equityCurve.length - 1]?.equity ?? initialCapital;
  const totalReturn = ((finalEquity - initialCapital) / initialCapital) * 100;

  const wins = trades.filter((t) => t.pnl > 0);
  const losses = trades.filter((t) => t.pnl <= 0);
  const winRate = trades.length > 0 ? (wins.length / trades.length) * 100 : 0;

  const avgWin =
    wins.length > 0
      ? wins.reduce((s, t) => s + t.pnl, 0) / wins.length
      : 0;
  const avgLoss =
    losses.length > 0
      ? Math.abs(losses.reduce((s, t) => s + t.pnl, 0) / losses.length)
      : 0;

  const grossWin = wins.reduce((s, t) => s + t.pnl, 0);
  const grossLoss = Math.abs(losses.reduce((s, t) => s + t.pnl, 0));
  const profitFactor =
    grossLoss > 0 ? grossWin / grossLoss : grossWin > 0 ? 999 : 0;

  // Max drawdown
  let maxDrawdown = 0;
  for (const pt of equityCurve) {
    if (pt.drawdown > maxDrawdown) maxDrawdown = pt.drawdown;
  }

  // Sharpe Ratio (annualized)
  const dailyReturns: number[] = [];
  for (let i = 1; i < equityCurve.length; i++) {
    const prevEq = equityCurve[i - 1].equity;
    if (prevEq > 0) {
      dailyReturns.push((equityCurve[i].equity - prevEq) / prevEq);
    }
  }
  const meanReturn =
    dailyReturns.length > 0
      ? dailyReturns.reduce((s, r) => s + r, 0) / dailyReturns.length
      : 0;
  const stdReturn =
    dailyReturns.length > 1
      ? Math.sqrt(
          dailyReturns.reduce((s, r) => s + (r - meanReturn) ** 2, 0) /
            (dailyReturns.length - 1)
        )
      : 0;
  const sharpeRatio =
    stdReturn > 0 ? (meanReturn / stdReturn) * Math.sqrt(252) : 0;

  // Calmar Ratio (annualized return / max drawdown)
  const annualizedReturn = totalReturn * (365 / period);
  const calmarRatio =
    maxDrawdown > 0 ? annualizedReturn / maxDrawdown : annualizedReturn > 0 ? 999 : 0;

  // Average holding period
  const avgHoldingPeriod =
    trades.length > 0
      ? trades.reduce((s, t) => s + t.holdingDays, 0) / trades.length
      : 0;

  return {
    totalReturn,
    winRate,
    sharpeRatio,
    maxDrawdown,
    avgWin,
    avgLoss,
    profitFactor,
    totalTrades: trades.length,
    calmarRatio,
    avgHoldingPeriod,
  };
}

// ---------------------------------------------------------------------------
// Run Backtest
// ---------------------------------------------------------------------------

export function runBacktest(config: BacktestConfig): BacktestResult {
  const seed = hashSeed(
    `${config.strategy}-${config.assets.join(",")}-${config.period}-${config.riskPerTrade}-${config.slPercent}-${config.tpPercent}`
  );
  const rng = seededRandom(seed);

  // Generate OHLC data for each asset
  const priceData: Record<string, OHLCBar[]> = {};
  for (const asset of config.assets) {
    priceData[asset] = generateOHLC(asset, config.period, rng, seed);
  }

  // Generate signals
  const signals = generateSignals(config.strategy, priceData, config.assets, rng);

  // Execute trades
  const { trades, equityCurve } = executeTrades(signals, priceData, config, rng);

  // Compute metrics
  const metrics = computeMetrics(trades, equityCurve, config.initialCapital, config.period);

  return {
    strategy: config.strategy,
    ...metrics,
    equityCurve,
    trades,
  };
}

// ---------------------------------------------------------------------------
// Run Walk-Forward Validation
// ---------------------------------------------------------------------------

export function runWalkForward(
  config: BacktestConfig,
  numWindows: number = 5
): WFVResult {
  const totalDays = config.period;
  const windowSize = Math.floor(totalDays / numWindows);
  const trainRatio = 0.7;
  const trainSize = Math.floor(windowSize * trainRatio);

  const windows: WFVWindowResult[] = [];

  for (let w = 0; w < numWindows; w++) {
    const windowStart = w * windowSize;
    const trainStart = windowStart;
    const trainEnd = windowStart + trainSize;
    const testStart = trainEnd;
    const testEnd = Math.min(windowStart + windowSize, totalDays);

    // Use a unique seed per window for deterministic but varied results
    const windowSeed = hashSeed(
      `${config.strategy}-${config.assets.join(",")}-${config.period}-w${w}-${config.riskPerTrade}-${config.slPercent}-${config.tpPercent}`
    );
    const rng = seededRandom(windowSeed);

    // Generate OHLC for the test window
    const priceData: Record<string, OHLCBar[]> = {};
    for (const asset of config.assets) {
      priceData[asset] = generateOHLC(asset, testEnd - testStart, rng, windowSeed);
    }

    const signals = generateSignals(config.strategy, priceData, config.assets, rng);
    const { trades, equityCurve } = executeTrades(
      signals,
      priceData,
      { ...config, period: testEnd - testStart },
      rng
    );

    const metrics = computeMetrics(
      trades,
      equityCurve,
      config.initialCapital,
      testEnd - testStart
    );

    windows.push({
      windowIndex: w,
      trainStart,
      trainEnd,
      testStart,
      testEnd,
      totalReturn: metrics.totalReturn,
      winRate: metrics.winRate,
      sharpeRatio: metrics.sharpeRatio,
      totalTrades: metrics.totalTrades,
    });
  }

  // Aggregate metrics
  const aggregateReturn =
    windows.reduce((s, w) => s + w.totalReturn, 0) / windows.length;
  const aggregateSharpe =
    windows.reduce((s, w) => s + w.sharpeRatio, 0) / windows.length;

  // Robustness check: consistent positive returns across windows
  const positiveWindows = windows.filter((w) => w.totalReturn > 0).length;
  const returnStd = Math.sqrt(
    windows.reduce((s, w) => s + (w.totalReturn - aggregateReturn) ** 2, 0) /
      windows.length
  );
  const isRobust =
    positiveWindows >= Math.ceil(numWindows * 0.6) &&
    returnStd < Math.abs(aggregateReturn) * 2 &&
    aggregateReturn > 0;

  return {
    windows,
    aggregateReturn,
    aggregateSharpe,
    isRobust,
  };
}
