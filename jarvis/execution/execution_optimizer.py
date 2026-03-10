# =============================================================================
# jarvis/execution/execution_optimizer.py — Simulated Execution Optimizer (S30)
#
# SANDBOXED: Kein Broker-Kontakt. Kein echter Order-Flow.
# Alle Outputs sind hypothetische Szenarien fuer Backtesting und Forschung.
#
# P0 — Rein analytisch. Kein echtes Trading. Kein Broker-Interface.
#
# Capabilities:
#   1. Slippage-Modellierung (Spread + Vol + Liquiditaet)
#   2. Market-Impact-Schaetzung (Square-Root-Modell)
#   3. Algorithmische Selektion (TWAP / VWAP / LIMIT / AGGRESSIVE)
#   4. Latenz-Budget-Schaetzung
# =============================================================================

from __future__ import annotations

from dataclasses import dataclass

import numpy as np


# ---------------------------------------------------------------------------
# DATACLASS
# ---------------------------------------------------------------------------

@dataclass
class ExecutionPlan:
    """Simuliertes Ausfuehrungs-Modell fuer Research-Zwecke.

    Kein echtes Trading. Kein Broker-Interface. Rein analytisch.
    Alle Outputs sind hypothetische Szenarien fuer Forschung und Backtesting.
    """

    base_size: float
    adjusted_size: float
    estimated_slippage: float
    max_market_impact: float
    recommended_algo: str
    urgency_score: float
    latency_budget_ms: float
    abort_if_spread_pct: float
    risk_cleared: bool


# ---------------------------------------------------------------------------
# OPTIMIZER
# ---------------------------------------------------------------------------

class SimulatedExecutionOptimizer:
    """Simulated Execution Modeling Layer — Research Only.

    SANDBOXED: Kein Broker-Kontakt. Kein echter Order-Flow.
    Alle Outputs sind hypothetische Szenarien fuer Backtesting und Forschung.
    Outputs gehen NUR in Research-Layer und Visual-Output,
    nicht in Broker-Systeme.
    """

    # Immutable constants (DET-06)
    LATENCY_BUDGET_URGENT: float = 50.0
    LATENCY_BUDGET_NORMAL: float = 500.0
    LATENCY_BUDGET_PASSIVE: float = 5000.0

    MAX_SPREAD_ABORT_PCT: float = 0.005
    MAX_IMPACT_PCT: float = 0.002

    def estimate_slippage(
        self,
        order_size_pct: float,
        liquidity_score: float,
        current_vol: float,
        bid_ask_spread_pct: float,
    ) -> float:
        """Slippage-Schaetzung basierend auf Groesse, Liquiditaet, Vol, Spread.

        Formula:
            base = spread / 2
            vol_component = vol * 0.1 * order_size
            liq_factor = 1 + (1 - clip(liq_score, 0, 1)) * 2
            total = (base + vol_component) * liq_factor
            output = clip(total, 0, 0.05)

        Args:
            order_size_pct: Order size as fraction of portfolio.
            liquidity_score: Liquidity score [0, 1].
            current_vol: Current annualized volatility.
            bid_ask_spread_pct: Bid-ask spread in percent.

        Returns:
            Estimated slippage in percent [0, 0.05].

        Raises:
            ValueError: If any input is non-finite or negative.
        """
        for name, val in [
            ("order_size_pct", order_size_pct),
            ("liquidity_score", liquidity_score),
            ("current_vol", current_vol),
            ("bid_ask_spread_pct", bid_ask_spread_pct),
        ]:
            if not np.isfinite(val) or val < 0:
                raise ValueError(f"Ungaeltiger Wert: {name}={val}")

        # Basis-Slippage = halber Spread
        base_slippage = bid_ask_spread_pct / 2.0

        # Vol-Komponente: hoehere Vol = mehr Slippage
        vol_component = current_vol * 0.1 * order_size_pct

        # Liquiditaets-Faktor: schlechtere Liquiditaet = mehr Slippage
        liq_factor = 1.0 + (1.0 - float(np.clip(liquidity_score, 0.0, 1.0))) * 2.0

        total = (base_slippage + vol_component) * liq_factor
        return float(np.clip(total, 0.0, 0.05))

    def compute_market_impact(
        self,
        order_size_pct: float,
        avg_daily_vol_pct: float,
    ) -> float:
        """Market Impact: Square-Root-Modell.

        Impact ~ sqrt(order_size / avg_daily_vol).

        Args:
            order_size_pct: Order size as fraction.
            avg_daily_vol_pct: Average daily volume fraction.

        Returns:
            Market impact in percent [0, MAX_IMPACT_PCT].
        """
        if avg_daily_vol_pct < 1e-10:
            return self.MAX_IMPACT_PCT

        ratio = float(np.clip(order_size_pct / avg_daily_vol_pct, 0.0, 1.0))
        impact = 0.1 * float(np.sqrt(ratio))
        return float(np.clip(impact, 0.0, self.MAX_IMPACT_PCT))

    def select_algorithm(
        self,
        urgency_score: float,
        liquidity_score: float,
        time_horizon_s: float,
    ) -> str:
        """Waehlt optimalen Execution-Algorithmus.

        Decision tree:
            urgency > 0.8       → AGGRESSIVE
            time_horizon > 3600 → TWAP
            liquidity > 0.7     → VWAP
            else                → LIMIT

        Args:
            urgency_score: Urgency [0, 1].
            liquidity_score: Liquidity score [0, 1].
            time_horizon_s: Time horizon in seconds.

        Returns:
            Algorithm name string.
        """
        if urgency_score > 0.8:
            return "AGGRESSIVE"
        elif time_horizon_s > 3600:
            return "TWAP"
        elif liquidity_score > 0.7:
            return "VWAP"
        else:
            return "LIMIT"

    def optimize(
        self,
        base_size_pct: float,
        liquidity_score: float,
        bid_ask_spread_pct: float,
        current_vol: float,
        avg_daily_vol_pct: float,
        urgency_score: float,
        time_horizon_s: float,
        risk_cleared: bool,
    ) -> ExecutionPlan:
        """Vollstaendige Execution-Optimierung.

        Wenn risk_cleared=False: Plan mit size=0, algo=HOLD.

        Args:
            base_size_pct: Base position size as fraction.
            liquidity_score: Liquidity score [0, 1].
            bid_ask_spread_pct: Bid-ask spread in percent.
            current_vol: Current annualized volatility.
            avg_daily_vol_pct: Average daily volume fraction.
            urgency_score: Urgency [0, 1].
            time_horizon_s: Time horizon in seconds.
            risk_cleared: True if Risk Engine has cleared this execution.

        Returns:
            ExecutionPlan with all fields populated.
        """
        if not risk_cleared:
            return ExecutionPlan(
                base_size=base_size_pct,
                adjusted_size=0.0,
                estimated_slippage=0.0,
                max_market_impact=0.0,
                recommended_algo="HOLD",
                urgency_score=urgency_score,
                latency_budget_ms=self.LATENCY_BUDGET_NORMAL,
                abort_if_spread_pct=self.MAX_SPREAD_ABORT_PCT,
                risk_cleared=False,
            )

        # Liquiditaets-angepasste Groesse
        liq_factor = float(np.clip(liquidity_score, 0.1, 1.0))
        adjusted_size = base_size_pct * liq_factor

        # Slippage und Impact schaetzen
        slippage = self.estimate_slippage(
            adjusted_size, liquidity_score, current_vol, bid_ask_spread_pct
        )
        impact = self.compute_market_impact(adjusted_size, avg_daily_vol_pct)

        # Algo auswaehlen
        algo = self.select_algorithm(urgency_score, liquidity_score, time_horizon_s)

        # Latenz-Budget
        if urgency_score > 0.7:
            latency_budget = self.LATENCY_BUDGET_URGENT
        elif urgency_score > 0.3:
            latency_budget = self.LATENCY_BUDGET_NORMAL
        else:
            latency_budget = self.LATENCY_BUDGET_PASSIVE

        # Spread-Abbruch-Schwelle
        abort_spread = max(self.MAX_SPREAD_ABORT_PCT, bid_ask_spread_pct * 2.0)

        return ExecutionPlan(
            base_size=base_size_pct,
            adjusted_size=float(np.clip(adjusted_size, 0.0, 1.0)),
            estimated_slippage=slippage,
            max_market_impact=impact,
            recommended_algo=algo,
            urgency_score=float(np.clip(urgency_score, 0.0, 1.0)),
            latency_budget_ms=latency_budget,
            abort_if_spread_pct=abort_spread,
            risk_cleared=risk_cleared,
        )
