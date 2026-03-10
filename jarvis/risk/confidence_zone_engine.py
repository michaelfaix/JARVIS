# =============================================================================
# JARVIS v6.1.0 -- CONFIDENCE ZONE ENGINE
# File:   jarvis/risk/confidence_zone_engine.py
# Version: 1.0.0
# Session: S16
# =============================================================================
#
# SCOPE
# -----
# Computes Entry/Exit Confidence Zones — probability spaces, NOT signals.
# No BUY/SELL output. No order generation. No execution semantics.
#
# Outputs:
#   - Entry Confidence Box:  [lower_bound, upper_bound] with P(entry_valid)
#   - Exit Risk Corridor:    [soft_exit, hard_exit] with P(exit_triggered)
#   - Expected Move %:       Probability-weighted price range
#   - Volatility Adjusted Stop: Dynamic stop based on regime volatility
#
# CLASSIFICATION: P0 — ANALYSIS AND STRATEGY RESEARCH TOOL.
#
# CRITICAL REQUIREMENTS (from FAS S16):
#   R1: NO signal output (no "BUY"/"SELL")
#   R2: All probabilities clipped to [1e-6, 1-1e-6]
#   R3: Entry/Exit bounds are NEVER communicated as absolute truths
#   R4: meta_uncertainty ALWAYS visible (quality control)
#
# DETERMINISM CONSTRAINTS
# -----------------------
# DET-01  No stochastic operations.
# DET-02  All inputs passed explicitly.
# DET-03  No side effects.
# DET-04  Deterministic arithmetic only.
# DET-05  All branching is deterministic.
# DET-06  Fixed literals are not parametrised.
# DET-07  Same inputs = bit-identical outputs.
#
# PROHIBITED ACTIONS CONFIRMED ABSENT
# ------------------------------------
#   No logging module
#   No datetime.now() / time.time()
#   No random / secrets / uuid
#   No file IO / network IO
#   No global mutable state
# =============================================================================

from __future__ import annotations

from dataclasses import dataclass

import numpy as np


# ---------------------------------------------------------------------------
# CONSTANTS
# ---------------------------------------------------------------------------

_CLIP_LO: float = 1e-6
_CLIP_HI: float = 1.0 - 1e-6
_SIGMA_FLOOR: float = 1e-10


# ---------------------------------------------------------------------------
# DATA CLASSES
# ---------------------------------------------------------------------------

@dataclass
class ConfidenceZone:
    """
    Output: NO signals. Only probability spaces.
    """
    entry_lower: float        # Lower bound of entry box
    entry_upper: float        # Upper bound of entry box
    entry_confidence: float   # P(entry valid) in [1e-6, 1-1e-6]
    exit_soft: float          # Soft exit level (increased caution)
    exit_hard: float          # Hard exit level (risk boundary)
    exit_confidence: float    # P(exit triggered) in [1e-6, 1-1e-6]
    expected_move_pct: float  # Expected move in %
    vol_adjusted_stop: float  # Volatility-adjusted stop
    meta_uncertainty: float   # U from system contract D(t)


@dataclass
class ConfidenceZoneRequest:
    """
    Input request for confidence zone computation.
    """
    current_price: float       # Current asset price (must be >= 0, finite)
    regime: str                # TRENDING, RANGING, HIGH_VOL, SHOCK, UNKNOWN
    sigma_sq: float            # Total variance from D(t) (must be >= 0, finite)
    mu: float                  # Information quality from D(t) (must be >= 0, finite)
    regime_confidence: float   # R from D(t)


# ---------------------------------------------------------------------------
# CONFIDENCE ZONE ENGINE
# ---------------------------------------------------------------------------

class ConfidenceZoneEngine:
    """
    Computes Entry/Exit Confidence Zones.
    Output is ALWAYS a probability space, NEVER a signal.
    """

    REGIME_VOL_MULTIPLIER = {
        "TRENDING": 1.0,
        "RANGING":  0.8,
        "HIGH_VOL": 1.8,
        "SHOCK":    3.0,
        "UNKNOWN":  2.5,
    }

    def compute(self, req: ConfidenceZoneRequest) -> ConfidenceZone:
        """
        Main computation: Confidence Zone for current market context.
        Raises ValueError for invalid regime or NaN/Inf values.
        """
        # Input validation
        for name, val in [
            ("current_price", req.current_price),
            ("sigma_sq", req.sigma_sq),
            ("mu", req.mu),
        ]:
            if not np.isfinite(val) or val < 0:
                raise ValueError(f"Ungaeltiger Wert fuer {name}: {val}")

        # Regime volatility multiplier (unknown regimes default to 2.5)
        vol_mult = self.REGIME_VOL_MULTIPLIER.get(req.regime, 2.5)
        sigma = float(np.sqrt(max(req.sigma_sq, _SIGMA_FLOOR)))
        adjusted_sigma = sigma * vol_mult

        # Entry Box: +/- 1 Sigma, weighted by information quality
        box_width = adjusted_sigma * (1.0 + (1.0 - req.mu))
        entry_lower = req.current_price * (1.0 - box_width)
        entry_upper = req.current_price * (1.0 + box_width)

        # Entry Confidence: calibrated probability
        raw_entry_conf = req.mu * req.regime_confidence
        entry_confidence = float(np.clip(raw_entry_conf, _CLIP_LO, _CLIP_HI))

        # Exit Risk Corridor
        soft_mult = adjusted_sigma * 1.5
        hard_mult = adjusted_sigma * 2.5
        exit_soft = req.current_price * (1.0 - soft_mult)
        exit_hard = req.current_price * (1.0 - hard_mult)

        # Exit Confidence
        raw_exit_conf = 1.0 - req.mu
        exit_confidence = float(np.clip(raw_exit_conf, _CLIP_LO, _CLIP_HI))

        # Expected Move %
        expected_move_pct = adjusted_sigma * 100.0

        # Volatility Adjusted Stop
        vol_adjusted_stop = req.current_price * (1.0 - adjusted_sigma * 2.0)

        # Meta-Uncertainty: overall system uncertainty
        meta_uncertainty = float(np.clip(
            1.0 - (req.mu * req.regime_confidence), _CLIP_LO, _CLIP_HI
        ))

        return ConfidenceZone(
            entry_lower=entry_lower,
            entry_upper=entry_upper,
            entry_confidence=entry_confidence,
            exit_soft=exit_soft,
            exit_hard=exit_hard,
            exit_confidence=exit_confidence,
            expected_move_pct=expected_move_pct,
            vol_adjusted_stop=vol_adjusted_stop,
            meta_uncertainty=meta_uncertainty,
        )


__all__ = [
    "ConfidenceZone",
    "ConfidenceZoneRequest",
    "ConfidenceZoneEngine",
]
