# =============================================================================
# jarvis/intelligence/weight_posterior.py
# Authority: FAS v6.0.1 -- S37 SYSTEM ADDENDUM, lines 8915-8991
# =============================================================================
#
# SCOPE
# -----
# Posterior weight distribution over strategy candidates.  posterior_mean feeds
# Weight_Model.  Deterministic — no random sampling.
#
# Public symbols:
#   HISTORY_WINDOW             Max historical observations (20)
#   FM_DEFENSIVE_CAP           FM cap factor (0.5)
#   WeightPosteriorModel       Frozen dataclass
#   WeightPosteriorEstimator   Estimator class
#
# GOVERNANCE
# ----------
# posterior_mean is the ONLY consumed field.  No adaptive execution.
# May not trigger position changes directly.
# If FM active: cap posterior_mean at prior_weight × 0.5 (defensive).
#
# DEPENDENCIES
# ------------
#   stdlib:    dataclasses, typing
#   external:  numpy
#   internal:  NONE
#   PROHIBITED: logging, random, file IO, network IO, datetime.now()
#
# DETERMINISM
# -----------
# DET-01  No stochastic operations.
# DET-02  All inputs passed explicitly.
# DET-03  No side effects.
# DET-07  Same inputs = identical output.
# =============================================================================

from __future__ import annotations

from dataclasses import dataclass
from typing import List

import numpy as np

__all__ = [
    "HISTORY_WINDOW",
    "FM_DEFENSIVE_CAP",
    "WeightPosteriorModel",
    "WeightPosteriorEstimator",
]


# =============================================================================
# SECTION 1 -- CONSTANTS
# =============================================================================

HISTORY_WINDOW: int = 20
"""Maximum historical observations used for estimation."""

FM_DEFENSIVE_CAP: float = 0.5
"""FM cap: posterior_mean <= prior_weight × this factor when FM active."""


# =============================================================================
# SECTION 2 -- DATA TYPES
# =============================================================================

@dataclass(frozen=True)
class WeightPosteriorModel:
    """
    Posterior weight distribution for a strategy candidate.

    Fields:
        strategy_id:        Strategy identifier.
        prior_weight:       Prior weight from previous cycle [0, 1].
        posterior_mean:     Posterior mean — ONLY consumed field [0, 1].
        posterior_std:      Uncertainty in weight estimate [0, 0.5].
        evidence_count:     Number of observations used (>= 0).
        regime_alignment:   How well strategy fits regime [0, 1].
        confidence_factor:  ConfidenceBundle.Q at time of update [0, 1].
    """
    strategy_id: str
    prior_weight: float
    posterior_mean: float
    posterior_std: float
    evidence_count: int
    regime_alignment: float
    confidence_factor: float


# =============================================================================
# SECTION 3 -- ESTIMATOR
# =============================================================================

class WeightPosteriorEstimator:
    """
    Estimates posterior weight distribution for strategy candidates.

    Uses regime alignment + Bayesian combination + confidence scaling.
    Deterministic — no random sampling.
    """

    def estimate(
        self,
        strategy_id: str,
        prior_weight: float,
        historical_weights: List[float],
        regime_alignment: float,
        confidence_q: float,
        fm_active: bool,
    ) -> WeightPosteriorModel:
        """
        Compute posterior weight for a strategy.

        With < 2 observations: posterior_mean = prior * alignment * confidence.
        With >= 2 observations: Bayesian combination of prior and observed mean,
        scaled by alignment and confidence.

        FM defensive cap: if fm_active, posterior_mean <= prior_weight * 0.5.

        Args:
            strategy_id:        Strategy identifier.
            prior_weight:       Prior weight [0, 1].
            historical_weights: Historical weight observations.
            regime_alignment:   Regime alignment score [0, 1].
            confidence_q:       Confidence Q value [0, 1].
            fm_active:          Whether any Failure Mode is active.

        Returns:
            WeightPosteriorModel.

        Raises:
            TypeError: If arguments have wrong types.
            ValueError: If numeric arguments out of range.
        """
        if not isinstance(strategy_id, str):
            raise TypeError(
                f"strategy_id must be a string, "
                f"got {type(strategy_id).__name__}"
            )
        if not strategy_id:
            raise ValueError("strategy_id must not be empty")
        if not isinstance(prior_weight, (int, float)):
            raise TypeError(
                f"prior_weight must be numeric, "
                f"got {type(prior_weight).__name__}"
            )
        if not isinstance(historical_weights, list):
            raise TypeError(
                f"historical_weights must be a list, "
                f"got {type(historical_weights).__name__}"
            )
        if not isinstance(regime_alignment, (int, float)):
            raise TypeError(
                f"regime_alignment must be numeric, "
                f"got {type(regime_alignment).__name__}"
            )
        if not isinstance(confidence_q, (int, float)):
            raise TypeError(
                f"confidence_q must be numeric, "
                f"got {type(confidence_q).__name__}"
            )
        if not isinstance(fm_active, bool):
            raise TypeError(
                f"fm_active must be bool, got {type(fm_active).__name__}"
            )

        prior_w = float(np.clip(prior_weight, 0.0, 1.0))
        ra = float(np.clip(regime_alignment, 0.0, 1.0))
        cq = float(np.clip(confidence_q, 0.0, 1.0))

        if len(historical_weights) < 2:
            posterior_mean = prior_w * ra * cq
            posterior_std = 0.5
        else:
            arr = np.array(
                historical_weights[-HISTORY_WINDOW:], dtype=np.float64
            )
            obs_mean = float(np.mean(arr))
            obs_std = float(np.std(arr))

            # Bayesian combination: equal weight prior and observation
            posterior_mean = 0.5 * prior_w + 0.5 * obs_mean
            posterior_mean *= ra * cq
            posterior_std = obs_std / max(float(np.sqrt(len(arr))), 1.0)

        # FM defensive cap
        if fm_active:
            posterior_mean = min(posterior_mean, prior_w * FM_DEFENSIVE_CAP)

        # Final clipping
        return WeightPosteriorModel(
            strategy_id=strategy_id,
            prior_weight=prior_w,
            posterior_mean=float(np.clip(posterior_mean, 0.0, 1.0)),
            posterior_std=float(np.clip(posterior_std, 0.0, 0.5)),
            evidence_count=len(historical_weights),
            regime_alignment=ra,
            confidence_factor=cq,
        )
