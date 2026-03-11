// =============================================================================
// src/app/api/chat/route.ts — AI Chat API Route (server-side)
//
// Proxies chat requests to Anthropic Claude API. API key stays server-side.
// Falls back to helpful offline responses if no API key is configured.
// =============================================================================

import { NextRequest, NextResponse } from "next/server";

const ANTHROPIC_API_KEY = process.env.ANTHROPIC_API_KEY;

const SYSTEM_PROMPT = `You are JARVIS, an AI trading intelligence assistant integrated into the JARVIS-Trader platform. You help users understand markets, analyze trading signals, and make informed decisions.

Your capabilities:
- Market analysis and regime detection (RISK_ON, RISK_OFF, CRISIS, TRANSITION)
- Signal interpretation (LONG/SHORT with confidence scores, quality scores, OOD warnings)
- Portfolio risk assessment (drawdown, exposure, position sizing)
- Strategy explanation (momentum, mean reversion, combined)
- Technical concepts (volatility, correlation, Sharpe ratio, calibration)

Rules:
- You are a research and analysis tool, NOT a financial advisor
- Always include the disclaimer that this is for educational/research purposes only
- Never recommend specific buy/sell actions — present analysis and let users decide
- Be concise and use trading terminology appropriately
- Format responses with markdown for readability`;

interface ChatMessage {
  role: "user" | "assistant";
  content: string;
}

export async function POST(req: NextRequest) {
  try {
    const body = await req.json();
    const messages: ChatMessage[] = body.messages ?? [];
    const context: string = body.context ?? "";

    if (!messages.length) {
      return NextResponse.json({ error: "No messages provided" }, { status: 400 });
    }

    if (!ANTHROPIC_API_KEY) {
      return NextResponse.json({
        response: generateOfflineResponse(messages[messages.length - 1].content),
      });
    }

    const systemMessage = context
      ? `${SYSTEM_PROMPT}\n\nCurrent market context:\n${context}`
      : SYSTEM_PROMPT;

    const apiResponse = await fetch("https://api.anthropic.com/v1/messages", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        "x-api-key": ANTHROPIC_API_KEY,
        "anthropic-version": "2023-06-01",
      },
      body: JSON.stringify({
        model: "claude-sonnet-4-20250514",
        max_tokens: 1024,
        system: systemMessage,
        messages: messages.map((m) => ({ role: m.role, content: m.content })),
      }),
    });

    if (!apiResponse.ok) {
      return NextResponse.json({
        response: generateOfflineResponse(messages[messages.length - 1].content),
      });
    }

    const data = await apiResponse.json();
    const text = data.content?.[0]?.text ?? "I couldn't generate a response.";
    return NextResponse.json({ response: text });
  } catch {
    return NextResponse.json({ error: "Internal server error" }, { status: 500 });
  }
}

function generateOfflineResponse(question: string): string {
  const q = question.toLowerCase();

  if (q.includes("regime") || q.includes("market")) {
    return "## Market Regime Analysis\n\nJARVIS uses a 5-state regime detection system:\n\n- **RISK_ON** — Bullish conditions, momentum strategies favored\n- **RISK_OFF** — Defensive positioning, reduced exposure\n- **CRISIS** — Maximum caution, minimal trading\n- **TRANSITION** — Regime change, mean reversion may work\n- **UNKNOWN** — Insufficient data\n\nThe regime influences signal generation, position sizing, and strategy selection.\n\n*Add `ANTHROPIC_API_KEY` to `.env.local` for full Claude-powered analysis.*\n\n---\n*JARVIS — Research & Analysis Tool. Not financial advice.*";
  }

  if (q.includes("signal") || q.includes("confidence")) {
    return "## Signal Interpretation\n\nJARVIS signals include:\n\n- **Direction**: LONG or SHORT\n- **Confidence**: 0-100% model certainty\n- **Quality Score**: Composite of calibration, stability, data quality\n- **OOD Warning**: Out-of-Distribution flag\n\n**High-quality**: Confidence > 70%, Quality > 70, no OOD\n**Caution**: OOD flagged, low confidence, or CRISIS regime\n\n*Add `ANTHROPIC_API_KEY` to `.env.local` for full Claude-powered analysis.*\n\n---\n*JARVIS — Research & Analysis Tool. Not financial advice.*";
  }

  if (q.includes("risk") || q.includes("drawdown") || q.includes("position")) {
    return "## Risk Management\n\nJARVIS Risk Guardian monitors:\n\n- **Position Sizing**: Max 25% in a single asset\n- **Drawdown**: Warning at 10% portfolio drawdown\n- **Cash Reserve**: Minimum 20% in cash\n- **Open Positions**: Maximum 6 concurrent\n\n*Add `ANTHROPIC_API_KEY` to `.env.local` for full Claude-powered analysis.*\n\n---\n*JARVIS — Research & Analysis Tool. Not financial advice.*";
  }

  if (q.includes("strateg") || q.includes("backtest") || q.includes("momentum")) {
    return "## Strategy Overview\n\n| Strategy | Best Regime | Win Rate | Sharpe |\n|----------|------------|---------|--------|\n| **Momentum** | RISK_ON | ~58% | 1.8 |\n| **Mean Reversion** | TRANSITION | ~62% | 1.5 |\n| **Combined** | All | ~60% | 2.1 |\n\nThe Combined strategy dynamically weights based on detected regime.\n\n*Add `ANTHROPIC_API_KEY` to `.env.local` for full Claude-powered analysis.*\n\n---\n*JARVIS — Research & Analysis Tool. Not financial advice.*";
  }

  return "## JARVIS AI Assistant\n\nI can help you with:\n\n- **Market Analysis** — \"What does RISK_ON regime mean?\"\n- **Signal Interpretation** — \"How do I read confidence scores?\"\n- **Risk Management** — \"What's a safe position size?\"\n- **Strategy Selection** — \"Which strategy works in a crisis?\"\n\nAsk a specific question about markets, signals, or risk management.\n\n*Add `ANTHROPIC_API_KEY` to `.env.local` for full Claude-powered AI analysis.*\n\n---\n*JARVIS — Research & Analysis Tool. Not financial advice.*";
}
