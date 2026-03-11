# jarvis/risk/fx_exposure_manager.py
# Version: 6.1.0
# FX Exposure Manager for multi-currency position netting and risk scoring.
#
# Part of the Multi-Asset Risk Engine (LAYER 8) per FAS v6.0.1 Phase 6A.
# Provides currency decomposition, exposure netting, and concentration risk scoring
# for forex pair positions.
#
# DETERMINISM GUARANTEE (DET-01 through DET-07):
#   DET-01  No stochastic operations.
#   DET-02  No external state reads. All inputs passed explicitly.
#   DET-03  No side effects. Methods do not write to any external state.
#   DET-04  All arithmetic operations are deterministic floating-point.
#   DET-05  All conditional branches are deterministic functions of explicit inputs.
#   DET-06  Fixed literals are not parameterised.
#   DET-07  Same inputs produce identical outputs.
#
# SYSTEM CLASSIFICATION (P0):
#   Pure analysis module. No trading, no broker API, no real money management.
#
# Standard import:
#   from jarvis.risk.fx_exposure_manager import (
#       FXExposureManager, CurrencyExposure, FXExposureResult,
#   )

from dataclasses import dataclass
from typing import Dict, Tuple
import math

__all__ = [
    "CurrencyExposure",
    "FXExposureResult",
    "FXExposureManager",
]


# ---------------------------------------------------------------------------
# SUPPORTED CURRENCY PAIRS — canonical decomposition table
# ---------------------------------------------------------------------------
# Each pair maps to (base_currency, quote_currency).
# Convention: pair name "XXXYYY" means buy XXX / sell YYY when position > 0.

_PAIR_DECOMPOSITION: Dict[str, Tuple[str, str]] = {
    "EURUSD": ("EUR", "USD"),
    "GBPUSD": ("GBP", "USD"),
    "USDJPY": ("USD", "JPY"),
    "AUDUSD": ("AUD", "USD"),
    "USDCHF": ("USD", "CHF"),
    "USDCAD": ("USD", "CAD"),
    "NZDUSD": ("NZD", "USD"),
    "EURGBP": ("EUR", "GBP"),
    "EURJPY": ("EUR", "JPY"),
    "GBPJPY": ("GBP", "JPY"),
}


# ---------------------------------------------------------------------------
# OUTPUT DATA CLASSES (frozen — immutability contract)
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class CurrencyExposure:
    """
    Exposure summary for a single currency.

    Fields:
        currency    -- ISO 4217 currency code (e.g. "EUR", "USD").
        gross_long  -- Sum of all long exposures in this currency (>= 0).
        gross_short -- Sum of all short exposures in this currency (>= 0, stored positive).
        net_exposure -- gross_long - gross_short (can be negative).
        hedge_ratio  -- Fraction of gross exposure that is hedged (netted).
                        Defined as 1 - abs(net) / gross when gross > 0, else 0.0.
                        Range: [0.0, 1.0].
    """
    currency: str
    gross_long: float
    gross_short: float
    net_exposure: float
    hedge_ratio: float


@dataclass(frozen=True)
class FXExposureResult:
    """
    Aggregate FX exposure result across all currencies.

    Fields:
        exposures          -- Tuple of CurrencyExposure, one per currency found.
        total_gross_exposure -- Sum of abs(position_size) across all pair legs.
        total_net_exposure   -- Sum of abs(net_exposure) across all currencies.
        netting_benefit      -- 1 - (total_net / total_gross) when total_gross > 0.
                                Range: [0.0, 1.0]. Higher = more netting.
        risk_score           -- Concentration-based risk score in [0.0, 1.0].
                                Higher = more concentrated (less diversified).
    """
    exposures: Tuple[CurrencyExposure, ...]
    total_gross_exposure: float
    total_net_exposure: float
    netting_benefit: float
    risk_score: float


# ---------------------------------------------------------------------------
# FX EXPOSURE MANAGER
# ---------------------------------------------------------------------------

class FXExposureManager:
    """
    FX Exposure Manager for multi-currency position analysis.

    Decomposes forex pair positions into individual currency exposures,
    computes netting benefits, and produces a concentration risk score.

    This is a pure analysis component — no live rates, no trading.
    Position sizes are used as exposure proxies (no FX rate conversion).

    Usage:
        manager = FXExposureManager()
        result = manager.compute_exposure(
            positions={"EURUSD": 100000.0, "EURGBP": -50000.0},
            base_currency="USD",
        )
    """

    def compute_exposure(
        self,
        positions: Dict[str, float],
        base_currency: str = "USD",
    ) -> FXExposureResult:
        """
        Compute FX exposure from a dict of forex pair positions.

        Parameters:
            positions     -- Dict mapping pair name (e.g. "EURUSD") to position
                             size. Positive = long the base currency of the pair,
                             negative = short. Zero positions are included but
                             contribute nothing.
            base_currency -- Reference currency for reporting (e.g. "USD").
                             Used for context only; no rate conversion is applied.

        Returns:
            FXExposureResult with per-currency breakdown and aggregate metrics.

        Raises:
            ValueError -- If any pair name is not in the supported set.
            TypeError  -- If positions is not a dict.
        """
        if not isinstance(positions, dict):
            raise TypeError(
                f"positions must be a dict, got {type(positions).__name__}"
            )

        # Validate all pairs before processing
        for pair in positions:
            if pair not in _PAIR_DECOMPOSITION:
                raise ValueError(
                    f"Unknown currency pair: '{pair}'. "
                    f"Supported pairs: {sorted(_PAIR_DECOMPOSITION.keys())}"
                )

        # ---- Step 1: Decompose pairs into per-currency long/short buckets ----
        currency_longs: Dict[str, float] = {}
        currency_shorts: Dict[str, float] = {}

        for pair, size in positions.items():
            base_ccy, quote_ccy = _PAIR_DECOMPOSITION[pair]
            abs_size = abs(size)

            if size > 0.0:
                # Long the pair = long base_ccy, short quote_ccy
                currency_longs[base_ccy] = currency_longs.get(base_ccy, 0.0) + abs_size
                currency_shorts[quote_ccy] = currency_shorts.get(quote_ccy, 0.0) + abs_size
            elif size < 0.0:
                # Short the pair = short base_ccy, long quote_ccy
                currency_shorts[base_ccy] = currency_shorts.get(base_ccy, 0.0) + abs_size
                currency_longs[quote_ccy] = currency_longs.get(quote_ccy, 0.0) + abs_size
            # size == 0.0: no contribution

        # ---- Step 2: Build per-currency exposure objects ----
        all_currencies = sorted(set(currency_longs.keys()) | set(currency_shorts.keys()))

        exposures = []
        for ccy in all_currencies:
            gross_long = currency_longs.get(ccy, 0.0)
            gross_short = currency_shorts.get(ccy, 0.0)
            net = gross_long - gross_short
            gross = gross_long + gross_short

            if gross > 0.0:
                hedge_ratio = 1.0 - abs(net) / gross
            else:
                hedge_ratio = 0.0

            exposures.append(CurrencyExposure(
                currency=ccy,
                gross_long=gross_long,
                gross_short=gross_short,
                net_exposure=net,
                hedge_ratio=hedge_ratio,
            ))

        # ---- Step 3: Aggregate metrics ----
        total_gross = sum(e.gross_long + e.gross_short for e in exposures)
        total_net = sum(abs(e.net_exposure) for e in exposures)

        if total_gross > 0.0:
            netting_benefit = 1.0 - total_net / total_gross
        else:
            netting_benefit = 0.0

        # ---- Step 4: Concentration risk score (Herfindahl-based) ----
        risk_score = self._compute_risk_score(exposures, total_net)

        return FXExposureResult(
            exposures=tuple(exposures),
            total_gross_exposure=total_gross,
            total_net_exposure=total_net,
            netting_benefit=netting_benefit,
            risk_score=risk_score,
        )

    # ------------------------------------------------------------------
    # INTERNAL: Concentration risk scoring
    # ------------------------------------------------------------------

    @staticmethod
    def _compute_risk_score(
        exposures: list,
        total_net: float,
    ) -> float:
        """
        Herfindahl-Hirschman-based concentration score.

        Returns a value in [0.0, 1.0]:
          - 0.0 when there is no net exposure or perfect diversification.
          - 1.0 when all net exposure is concentrated in a single currency.

        The HHI is normalised: HHI_norm = (HHI - 1/N) / (1 - 1/N)
        for N currencies with nonzero net exposure, clamped to [0, 1].
        """
        if total_net <= 0.0:
            return 0.0

        # Compute weight of each currency's abs(net) in total_net
        weights = []
        for exp in exposures:
            w = abs(exp.net_exposure) / total_net
            if w > 0.0:
                weights.append(w)

        n = len(weights)
        if n <= 1:
            # Single currency or none: maximum concentration
            return 1.0 if n == 1 else 0.0

        hhi = sum(w * w for w in weights)

        # Normalise HHI to [0, 1]
        hhi_min = 1.0 / n
        hhi_max = 1.0
        if hhi_max - hhi_min < 1e-12:
            return 0.0

        hhi_norm = (hhi - hhi_min) / (hhi_max - hhi_min)

        # Clamp to [0, 1] for safety
        return max(0.0, min(1.0, hhi_norm))
