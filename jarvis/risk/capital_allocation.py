# =============================================================================
# jarvis/risk/capital_allocation.py — Capital Allocation Engine (S29)
#
# Portfolio-Level Capital Allocation.
# Optimiert KAPITAL, nicht Trades.
# Kein Kelly-Einsatz ohne Risk-Engine-Freigabe.
#
# Drei Saeulen:
#   1. Kelly Criterion (Quarter Kelly, confidence-adjustiert)
#   2. Risk Budget Allocation (vol-skaliert)
#   3. Volatility Targeting (konstantes Portfolio-Risiko)
#
# Endgueltige Allokation = min(Kelly, RiskBudget, VolTarget)
# =============================================================================

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, Optional

import numpy as np


# ---------------------------------------------------------------------------
# DATACLASSES
# ---------------------------------------------------------------------------

@dataclass
class AllocationResult:
    """Capital Allocation Output fuer eine Strategie."""

    kelly_fraction: float
    risk_budget_fraction: float
    vol_target_fraction: float
    final_allocation: float
    exposure_cap_applied: bool
    reason: str


@dataclass
class PortfolioAllocation:
    """Portfolio-weite Allokations-Entscheidung."""

    allocations: Dict[str, AllocationResult]
    total_gross_exposure: float
    portfolio_vol_est: float
    vol_target_met: bool
    rebalance_required: bool


# ---------------------------------------------------------------------------
# ENGINE
# ---------------------------------------------------------------------------

class CapitalAllocationEngine:
    """Portfolio-Level Capital Allocation.

    Optimiert Kapital-Allokation, nicht einzelne Trades.
    Risk Engine muss immer zuerst konsultiert werden.
    """

    # Immutable Limits (DET-06 — fixed literals)
    MAX_KELLY_FRACTION: float = 0.25
    MAX_TOTAL_EXPOSURE: float = 0.80
    VOLATILITY_TARGET: float = 0.15
    REBALANCE_THRESHOLD: float = 0.05

    def compute_kelly_fraction(
        self,
        win_rate: float,
        avg_win: float,
        avg_loss: float,
        confidence: float = 1.0,
    ) -> float:
        """Kelly-Kriterium: f* = (p*b - q) / b.

        Confidence-adjustiert und gecappt auf MAX_KELLY_FRACTION.

        Args:
            win_rate: Gewinnwahrscheinlichkeit [0, 1].
            avg_win: Durchschnittlicher Gewinn.
            avg_loss: Durchschnittlicher Verlust (positiv).
            confidence: Confidence-Faktor (0, 1].

        Returns:
            Kelly-Fraction [0, MAX_KELLY_FRACTION].

        Raises:
            ValueError: On invalid inputs.
        """
        if avg_loss < 1e-10:
            raise ValueError("avg_loss muss > 0 sein")
        if not (0.0 <= win_rate <= 1.0):
            raise ValueError(f"win_rate muss in [0,1] sein: {win_rate}")
        if not (0.0 < confidence <= 1.0):
            raise ValueError(f"confidence muss in (0,1]: {confidence}")

        b = avg_win / avg_loss
        p = win_rate
        q = 1.0 - p

        kelly = (p * b - q) / max(b, 1e-10)
        adjusted = kelly * confidence * self.MAX_KELLY_FRACTION
        return float(np.clip(adjusted, 0.0, self.MAX_KELLY_FRACTION))

    def compute_risk_budget_fraction(
        self,
        strategy_vol: float,
        portfolio_vol: float,
        risk_budget_pct: float = 0.20,
    ) -> float:
        """Risk-Budget-Allokation: vol-skaliert.

        Mehr Volatilitaet = weniger Allokation.

        Args:
            strategy_vol: Strategie-Volatilitaet (annualisiert).
            portfolio_vol: Portfolio-Volatilitaet (annualisiert).
            risk_budget_pct: Anteil des Risiko-Budgets fuer diese Strategie.

        Returns:
            Risk-Budget-Fraction [0, 1].

        Raises:
            ValueError: If portfolio_vol is near zero.
        """
        if strategy_vol < 1e-10:
            return 0.0
        if portfolio_vol < 1e-10:
            raise ValueError("portfolio_vol muss > 0 sein")

        vol_ratio = float(np.clip(strategy_vol / portfolio_vol, 0.1, 10.0))
        fraction = risk_budget_pct / vol_ratio
        return float(np.clip(fraction, 0.0, 1.0))

    def compute_vol_targeting_fraction(
        self,
        current_vol: float,
        target_vol: Optional[float] = None,
        base_fraction: float = 1.0,
    ) -> float:
        """Volatility Targeting: invers zur Volatilitaet skaliert.

        Ziel: konstante Risikoeinheit, nicht konstante Kapitaleinheit.

        Args:
            current_vol: Aktuelle realisierte Volatilitaet.
            target_vol: Ziel-Volatilitaet (default: VOLATILITY_TARGET).
            base_fraction: Basis-Fraction.

        Returns:
            Vol-Targeting-Fraction [0, 1].
        """
        target = target_vol or self.VOLATILITY_TARGET
        if current_vol < 1e-10:
            return float(np.clip(base_fraction, 0.0, 1.0))

        scaled = base_fraction * (target / current_vol)
        return float(np.clip(scaled, 0.0, 1.0))

    def allocate_single(
        self,
        strategy_id: str,
        win_rate: float,
        avg_win: float,
        avg_loss: float,
        strategy_vol: float,
        portfolio_vol: float,
        confidence: float,
        risk_compression: bool,
    ) -> AllocationResult:
        """Vollstaendige Allokation fuer eine Strategie.

        Endgueltige Allokation = min(Kelly, RiskBudget, VolTarget).
        Risk Compression reduziert auf 25% der normalen Allokation.

        Args:
            strategy_id: Strategie-Identifier.
            win_rate: Gewinnwahrscheinlichkeit [0, 1].
            avg_win: Durchschnittlicher Gewinn.
            avg_loss: Durchschnittlicher Verlust (positiv).
            strategy_vol: Strategie-Volatilitaet.
            portfolio_vol: Portfolio-Volatilitaet.
            confidence: Confidence-Faktor.
            risk_compression: True wenn Risk Compression aktiv.

        Returns:
            AllocationResult mit finaler Allokation.
        """
        kelly = self.compute_kelly_fraction(win_rate, avg_win, avg_loss, confidence)
        risk_budget = self.compute_risk_budget_fraction(strategy_vol, portfolio_vol)
        vol_target = self.compute_vol_targeting_fraction(strategy_vol)

        # Endgueltige Allokation: Minimum der drei Methoden (konservativste)
        raw_alloc = min(kelly, risk_budget, vol_target)

        # Risk Compression: drastische Reduzierung
        if risk_compression:
            raw_alloc *= 0.25
            reason = (
                f"Risk compression active. "
                f"Base: {raw_alloc / 0.25:.3f} -> {raw_alloc:.3f}"
            )
        else:
            reason = (
                f"Kelly={kelly:.3f} "
                f"RiskBudget={risk_budget:.3f} "
                f"VolTarget={vol_target:.3f}"
            )

        final = float(np.clip(raw_alloc, 0.0, self.MAX_KELLY_FRACTION))
        cap_applied = raw_alloc > final

        return AllocationResult(
            kelly_fraction=kelly,
            risk_budget_fraction=risk_budget,
            vol_target_fraction=vol_target,
            final_allocation=final,
            exposure_cap_applied=cap_applied,
            reason=reason,
        )

    def allocate_portfolio(
        self,
        strategies: Dict[str, Dict],
        portfolio_vol: float,
        risk_compression: bool,
    ) -> PortfolioAllocation:
        """Portfolio-weite Allokation.

        Prueft Gesamt-Exposure-Cap und Volatility-Target.

        Args:
            strategies: Dict mapping strategy_id to parameter dicts.
            portfolio_vol: Portfolio-Volatilitaet.
            risk_compression: True wenn Risk Compression aktiv.

        Returns:
            PortfolioAllocation with per-strategy allocations.
        """
        allocations: Dict[str, AllocationResult] = {}
        for sid, params in strategies.items():
            allocations[sid] = self.allocate_single(
                strategy_id=sid,
                win_rate=float(params.get("win_rate", 0.5)),
                avg_win=float(params.get("avg_win", 1.0)),
                avg_loss=float(params.get("avg_loss", 1.0)),
                strategy_vol=float(params.get("vol", 0.2)),
                portfolio_vol=portfolio_vol,
                confidence=float(params.get("confidence", 0.5)),
                risk_compression=risk_compression,
            )

        total_exposure = sum(r.final_allocation for r in allocations.values())
        total_exposure = float(np.clip(total_exposure, 0.0, self.MAX_TOTAL_EXPOSURE))

        # Portfolio Vol schaetzen (vereinfacht: gewichtetes Mittel)
        if allocations:
            weights = np.array([
                allocations[s].final_allocation / max(total_exposure, 1e-10)
                for s in allocations
            ])
            vols = np.array([
                float(strategies[s].get("vol", 0.2)) for s in allocations
            ])
            portfolio_vol_est = float(np.sum(weights * vols))
        else:
            portfolio_vol_est = 0.0

        vol_target_met = abs(portfolio_vol_est - self.VOLATILITY_TARGET) < 0.05
        rebalance = (
            abs(total_exposure - self.MAX_TOTAL_EXPOSURE * 0.8)
            > self.REBALANCE_THRESHOLD
        )

        return PortfolioAllocation(
            allocations=allocations,
            total_gross_exposure=total_exposure,
            portfolio_vol_est=portfolio_vol_est,
            vol_target_met=vol_target_met,
            rebalance_required=rebalance,
        )
