# =============================================================================
# jarvis/intelligence/bayesian_confidence.py
# Authority: FAS v6.0.1 -- S37 SYSTEM ADDENDUM, lines 8789-8908
# =============================================================================
#
# SCOPE
# -----
# Deterministic Bayesian posterior confidence update.  Uses LIKELIHOOD_TABLE
# mapping (regime, data_quality_band) to likelihood values.  No sampling.
#
# Public symbols:
#   LIKELIHOOD_TABLE             Canonical likelihood table (5 regimes × 3 bands)
#   SPIKE_UP_MIN_QUALITY         Minimum quality for spike-up (0.70)
#   BayesianConfidenceUpdate     Frozen dataclass for update result
#   data_quality_band            Classify quality score to band
#   BayesianConfidenceEngine     Engine class
#
# GOVERNANCE
# ----------
# Spike-up (posterior > prior) requires: regime_stable AND NOT fm_active
# AND quality_score >= 0.70.  Output feeds ConfidenceBundle.Q only.
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
# DET-06  Fixed literals (LIKELIHOOD_TABLE, thresholds) not parametrisable.
# DET-07  Same inputs = identical output.
# =============================================================================

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict

import numpy as np

__all__ = [
    "LIKELIHOOD_TABLE",
    "SPIKE_UP_MIN_QUALITY",
    "BayesianConfidenceUpdate",
    "data_quality_band",
    "BayesianConfidenceEngine",
]


# =============================================================================
# SECTION 1 -- CONSTANTS (DET-06: fixed literals)
# =============================================================================

LIKELIHOOD_TABLE: Dict[str, Dict[str, float]] = {
    "TRENDING":  {"high": 0.85, "medium": 0.65, "low": 0.40},
    "RANGING":   {"high": 0.75, "medium": 0.55, "low": 0.35},
    "HIGH_VOL":  {"high": 0.50, "medium": 0.35, "low": 0.20},
    "SHOCK":     {"high": 0.30, "medium": 0.20, "low": 0.10},
    "UNKNOWN":   {"high": 0.25, "medium": 0.15, "low": 0.08},
}
"""Canonical likelihood table: regime × data_quality_band → likelihood."""

SPIKE_UP_MIN_QUALITY: float = 0.70
"""Minimum quality_score for spike-up permission."""


# =============================================================================
# SECTION 2 -- DATA TYPES
# =============================================================================

@dataclass(frozen=True)
class BayesianConfidenceUpdate:
    """
    Result of a Bayesian confidence update.

    Fields:
        prior_confidence:     ConfidenceBundle.Q before update [0, 1].
        likelihood:           P(data | hypothesis) from LIKELIHOOD_TABLE [0, 1].
        evidence:             Normalising constant [0+].
        posterior_confidence:  Computed posterior [0, 1].
        regime_stable:        Whether current regime permits spike-up.
        fm_active:            Whether any Failure Mode is active.
        update_permitted:     True if posterior was applied without cap.
    """
    prior_confidence: float
    likelihood: float
    evidence: float
    posterior_confidence: float
    regime_stable: bool
    fm_active: bool
    update_permitted: bool


# =============================================================================
# SECTION 3 -- CLASSIFICATION
# =============================================================================

def data_quality_band(quality_score: float) -> str:
    """
    Classify quality score into data quality band.

    Thresholds (DET-06 fixed literals):
        high:   quality_score >= 0.75
        medium: quality_score >= 0.50
        low:    quality_score < 0.50

    Args:
        quality_score: Quality score in [0, 1].

    Returns:
        Band string ("high", "medium", "low").

    Raises:
        TypeError: If quality_score is not numeric.
    """
    if not isinstance(quality_score, (int, float)):
        raise TypeError(
            f"quality_score must be numeric, "
            f"got {type(quality_score).__name__}"
        )
    if quality_score >= 0.75:
        return "high"
    elif quality_score >= 0.50:
        return "medium"
    else:
        return "low"


# =============================================================================
# SECTION 4 -- ENGINE
# =============================================================================

class BayesianConfidenceEngine:
    """
    Computes Bayesian posterior confidence from prior and current evidence.

    Uses LIKELIHOOD_TABLE; no sampling.  Spike-up constraint enforced.
    """

    def update(
        self,
        prior_confidence: float,
        regime: str,
        quality_score: float,
        fm_active: bool,
        regime_stable: bool,
        joint_multiplier: float = 1.0,
    ) -> BayesianConfidenceUpdate:
        """
        Compute Bayesian posterior confidence.

        Formula: posterior = clip((prior * likelihood) / evidence, 0, 1)

        Spike-up constraint: posterior > prior requires:
          regime_stable AND NOT fm_active AND quality_score >= 0.70

        Args:
            prior_confidence: Prior Q in [0, 1].
            regime:           Current regime string.
            quality_score:    Data quality score in [0, 1].
            fm_active:        Whether any Failure Mode is active.
            regime_stable:    Whether regime is stable.
            joint_multiplier: JRM for likelihood reduction (default 1.0).

        Returns:
            BayesianConfidenceUpdate.

        Raises:
            TypeError: If arguments have wrong types.
            ValueError: If numeric arguments out of range.
        """
        if not isinstance(prior_confidence, (int, float)):
            raise TypeError(
                f"prior_confidence must be numeric, "
                f"got {type(prior_confidence).__name__}"
            )
        if not (0.0 <= prior_confidence <= 1.0):
            raise ValueError(
                f"prior_confidence must be in [0, 1], got {prior_confidence}"
            )
        if not isinstance(quality_score, (int, float)):
            raise TypeError(
                f"quality_score must be numeric, "
                f"got {type(quality_score).__name__}"
            )
        if not isinstance(fm_active, bool):
            raise TypeError(
                f"fm_active must be bool, got {type(fm_active).__name__}"
            )
        if not isinstance(regime_stable, bool):
            raise TypeError(
                f"regime_stable must be bool, got {type(regime_stable).__name__}"
            )
        if not isinstance(joint_multiplier, (int, float)):
            raise TypeError(
                f"joint_multiplier must be numeric, "
                f"got {type(joint_multiplier).__name__}"
            )
        if joint_multiplier <= 0:
            raise ValueError(
                f"joint_multiplier must be > 0, got {joint_multiplier}"
            )

        # Lookup base likelihood
        band = data_quality_band(quality_score)
        regime_entry = LIKELIHOOD_TABLE.get(regime, LIKELIHOOD_TABLE["UNKNOWN"])
        l_base = regime_entry[band]

        # Adjust for joint multiplier
        likelihood = float(np.clip(
            l_base / max(joint_multiplier, 1e-10), 0.0, 1.0
        ))

        # Compute evidence (uniform prior over regimes)
        evidence = 0.0
        for r_entry in LIKELIHOOD_TABLE.values():
            evidence += (1.0 / len(LIKELIHOOD_TABLE)) * r_entry[band]

        # Bayesian update
        if evidence > 0:
            raw_posterior = float(np.clip(
                (prior_confidence * likelihood) / evidence, 0.0, 1.0
            ))
        else:
            raw_posterior = prior_confidence

        # Spike-up constraint
        spike_up_permitted = (
            regime_stable
            and not fm_active
            and quality_score >= SPIKE_UP_MIN_QUALITY
        )

        if spike_up_permitted:
            posterior = raw_posterior
        else:
            posterior = min(prior_confidence, raw_posterior)

        return BayesianConfidenceUpdate(
            prior_confidence=prior_confidence,
            likelihood=likelihood,
            evidence=evidence,
            posterior_confidence=posterior,
            regime_stable=regime_stable,
            fm_active=fm_active,
            update_permitted=spike_up_permitted,
        )
