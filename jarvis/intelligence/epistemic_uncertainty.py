# =============================================================================
# jarvis/intelligence/epistemic_uncertainty.py
# Authority: FAS v6.0.1 -- S37 SYSTEM ADDENDUM, lines 8598-8617, 15738-16024
# =============================================================================
#
# SCOPE
# -----
# Epistemic uncertainty estimation assembling model uncertainty, data sparsity,
# confidence decay, and aleatoric components into a single UncertaintyBundle.
#
# Public symbols:
#   MUS_WEIGHT_REGIME                ModelUncertaintyScore weight for regime
#   MUS_WEIGHT_SPARSITY              ModelUncertaintyScore weight for sparsity
#   MUS_WEIGHT_FM_FREQ               ModelUncertaintyScore weight for FM freq
#   DATA_SPARSITY_THRESHOLD          Minimum valid fraction (0.60)
#   DATA_SPARSITY_MAX_PENALTY        Maximum confidence reduction (0.40)
#   CONFIDENCE_DECAY_FACTOR          Per-bar decay rate (0.02)
#   CONFIDENCE_DECAY_MAX             Max decay per cycle (0.10)
#   CONFIDENCE_DECAY_MIN_VALUE       Minimum Q after decay (0.30)
#   UNCERTAINTY_WEIGHT_MODEL         total_uncertainty weight for model (0.45)
#   UNCERTAINTY_WEIGHT_DATA          total_uncertainty weight for data (0.35)
#   UNCERTAINTY_WEIGHT_ALEATORIC     total_uncertainty weight for aleatoric (0.20)
#   ModelUncertaintyScore            Frozen dataclass
#   DataSparsityPenalty              Frozen dataclass
#   ConfidenceDecayResult            Frozen dataclass
#   UncertaintyBundle                Frozen dataclass (output)
#   EpistemicUncertaintyEngine       Engine class
#
# GOVERNANCE
# ----------
# Output is frozen and read-only downstream.  No layer may modify it.
# No execution triggers.
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
from typing import Tuple

import numpy as np

__all__ = [
    "MUS_WEIGHT_REGIME",
    "MUS_WEIGHT_SPARSITY",
    "MUS_WEIGHT_FM_FREQ",
    "DATA_SPARSITY_THRESHOLD",
    "DATA_SPARSITY_MAX_PENALTY",
    "CONFIDENCE_DECAY_FACTOR",
    "CONFIDENCE_DECAY_MAX",
    "CONFIDENCE_DECAY_MIN_VALUE",
    "UNCERTAINTY_WEIGHT_MODEL",
    "UNCERTAINTY_WEIGHT_DATA",
    "UNCERTAINTY_WEIGHT_ALEATORIC",
    "ModelUncertaintyScore",
    "DataSparsityPenalty",
    "ConfidenceDecayResult",
    "UncertaintyBundle",
    "EpistemicUncertaintyEngine",
]


# =============================================================================
# SECTION 1 -- CONSTANTS (DET-06: fixed literals)
# =============================================================================

MUS_WEIGHT_REGIME: float = 0.40
MUS_WEIGHT_SPARSITY: float = 0.35
MUS_WEIGHT_FM_FREQ: float = 0.25

DATA_SPARSITY_THRESHOLD: float = 0.60
DATA_SPARSITY_MAX_PENALTY: float = 0.40

CONFIDENCE_DECAY_FACTOR: float = 0.02
CONFIDENCE_DECAY_MAX: float = 0.10
CONFIDENCE_DECAY_MIN_VALUE: float = 0.30

UNCERTAINTY_WEIGHT_MODEL: float = 0.45
UNCERTAINTY_WEIGHT_DATA: float = 0.35
UNCERTAINTY_WEIGHT_ALEATORIC: float = 0.20


# =============================================================================
# SECTION 2 -- DATA TYPES
# =============================================================================

@dataclass(frozen=True)
class ModelUncertaintyScore:
    """
    Model uncertainty from regime instability, data sparsity, and FM frequency.

    Fields:
        regime_instability_score: Normalised regime changes / 10.0 [0, 1].
        data_sparsity_score:      1.0 - fill_rate [0, 1].
        fm_frequency_score:       Normalised FM activations / 6.0 [0, 1].
        model_uncertainty_score:  Weighted sum [0, 1].
    """
    regime_instability_score: float
    data_sparsity_score: float
    fm_frequency_score: float
    model_uncertainty_score: float

    def __post_init__(self) -> None:
        for name in ("regime_instability_score", "data_sparsity_score",
                      "fm_frequency_score", "model_uncertainty_score"):
            val = getattr(self, name)
            if not isinstance(val, (int, float)):
                raise TypeError(f"{name} must be numeric, got {type(val).__name__}")
            if not (0.0 <= val <= 1.0):
                raise ValueError(f"{name} must be in [0, 1], got {val}")


@dataclass(frozen=True)
class DataSparsityPenalty:
    """
    Data sparsity penalty when valid fraction falls below threshold.

    Fields:
        valid_fraction:          Valid samples / window size [0, 1].
        below_threshold:         True if valid_fraction < 0.60.
        confidence_multiplier:   [0.60, 1.0].
        sparsity_penalty:        Absolute reduction amount [0, 0.40].
    """
    valid_fraction: float
    below_threshold: bool
    confidence_multiplier: float
    sparsity_penalty: float


@dataclass(frozen=True)
class ConfidenceDecayResult:
    """
    Confidence decay from elapsed bars since last confirmation signal.

    Fields:
        prior_Q:              Prior confidence value [0, 1].
        bars_since_signal:    Bars since last confirmation.
        decay_applied:        Actual decay magnitude [0, 0.10].
        new_Q:                Q after decay [0.30, 1.0].
        decay_was_active:     True if decay was applied.
    """
    prior_Q: float
    bars_since_signal: int
    decay_applied: float
    new_Q: float
    decay_was_active: bool


@dataclass(frozen=True)
class UncertaintyBundle:
    """
    Complete epistemic uncertainty output.

    Fields:
        epistemic_model:           Model uncertainty [0, 1].
        epistemic_data:            Data uncertainty [0, 1].
        aleatoric:                 Irreducible volatility component [0, 1].
        total_uncertainty:         Weighted composite [0, 1].
        model_uncertainty_score:   Specific model uncertainty score [0, 1].
        data_sparsity_penalty:     Sparsity penalty applied [0, 1].
        confidence_decay_applied:  Decay applied this cycle [0, 0.30].
    """
    epistemic_model: float
    epistemic_data: float
    aleatoric: float
    total_uncertainty: float
    model_uncertainty_score: float
    data_sparsity_penalty: float
    confidence_decay_applied: float

    def __post_init__(self) -> None:
        for name in ("epistemic_model", "epistemic_data",
                      "aleatoric", "total_uncertainty"):
            val = getattr(self, name)
            if not isinstance(val, (int, float)):
                raise TypeError(f"{name} must be numeric, got {type(val).__name__}")
            if not (0.0 <= val <= 1.0):
                raise ValueError(f"{name} must be in [0, 1], got {val}")


# =============================================================================
# SECTION 3 -- ENGINE
# =============================================================================

class EpistemicUncertaintyEngine:
    """
    Assembles the full UncertaintyBundle from all epistemic components.

    Methods:
        compute_model_uncertainty   Compute ModelUncertaintyScore.
        compute_sparsity_penalty    Compute DataSparsityPenalty.
        compute_confidence_decay    Compute ConfidenceDecayResult.
        compute                     Assemble full UncertaintyBundle.
    """

    def compute_model_uncertainty(
        self,
        n_regime_changes: int,
        n_valid_samples: int,
        window_size: int,
        n_fm_activations: int,
    ) -> ModelUncertaintyScore:
        """
        Compute model uncertainty from regime instability, data sparsity, FM freq.

        Args:
            n_regime_changes:  Regime changes in last 20 bars.
            n_valid_samples:   Valid samples in rolling window.
            window_size:       Rolling window size.
            n_fm_activations:  FM activations in last 20 bars.

        Returns:
            ModelUncertaintyScore with weighted sum.
        """
        regime_score = float(np.clip(n_regime_changes / 10.0, 0.0, 1.0))
        fill_rate = float(np.clip(
            n_valid_samples / max(window_size, 1), 0.0, 1.0
        ))
        sparsity_score = 1.0 - fill_rate
        fm_score = float(np.clip(n_fm_activations / 6.0, 0.0, 1.0))

        total = (
            MUS_WEIGHT_REGIME * regime_score
            + MUS_WEIGHT_SPARSITY * sparsity_score
            + MUS_WEIGHT_FM_FREQ * fm_score
        )
        total = float(np.clip(total, 0.0, 1.0))

        return ModelUncertaintyScore(
            regime_instability_score=regime_score,
            data_sparsity_score=sparsity_score,
            fm_frequency_score=fm_score,
            model_uncertainty_score=total,
        )

    def compute_sparsity_penalty(
        self,
        n_valid: int,
        window_size: int,
    ) -> DataSparsityPenalty:
        """
        Compute data sparsity penalty.

        Args:
            n_valid:     Number of valid samples.
            window_size: Window size.

        Returns:
            DataSparsityPenalty.
        """
        valid_frac = float(np.clip(n_valid / max(window_size, 1), 0.0, 1.0))
        below = valid_frac < DATA_SPARSITY_THRESHOLD

        if below:
            deficit = DATA_SPARSITY_THRESHOLD - valid_frac
            penalty = float(np.clip(
                deficit * DATA_SPARSITY_MAX_PENALTY / DATA_SPARSITY_THRESHOLD,
                0.0, DATA_SPARSITY_MAX_PENALTY,
            ))
            multiplier = 1.0 - penalty
        else:
            penalty = 0.0
            multiplier = 1.0

        multiplier = float(np.clip(multiplier, 1.0 - DATA_SPARSITY_MAX_PENALTY, 1.0))

        return DataSparsityPenalty(
            valid_fraction=valid_frac,
            below_threshold=below,
            confidence_multiplier=multiplier,
            sparsity_penalty=penalty,
        )

    def compute_confidence_decay(
        self,
        prior_Q: float,
        bars_since_signal: int,
        has_confirmation_signal: bool,
    ) -> ConfidenceDecayResult:
        """
        Compute confidence decay.

        Args:
            prior_Q:                  Prior confidence [0, 1].
            bars_since_signal:        Bars since last confirmation.
            has_confirmation_signal:  Whether a signal was received.

        Returns:
            ConfidenceDecayResult.
        """
        if has_confirmation_signal or bars_since_signal == 0:
            return ConfidenceDecayResult(
                prior_Q=prior_Q,
                bars_since_signal=bars_since_signal,
                decay_applied=0.0,
                new_Q=prior_Q,
                decay_was_active=False,
            )

        raw_decay = CONFIDENCE_DECAY_FACTOR * bars_since_signal
        decay_applied = float(np.clip(raw_decay, 0.0, CONFIDENCE_DECAY_MAX))
        new_Q = float(np.clip(
            prior_Q - decay_applied,
            CONFIDENCE_DECAY_MIN_VALUE, 1.0,
        ))

        return ConfidenceDecayResult(
            prior_Q=prior_Q,
            bars_since_signal=bars_since_signal,
            decay_applied=decay_applied,
            new_Q=new_Q,
            decay_was_active=True,
        )

    def compute(
        self,
        model_uncertainty: ModelUncertaintyScore,
        sparsity_penalty: DataSparsityPenalty,
        decay_result: ConfidenceDecayResult,
        realized_vol_nvu: float,
    ) -> UncertaintyBundle:
        """
        Assemble full UncertaintyBundle from all components.

        Args:
            model_uncertainty: ModelUncertaintyScore.
            sparsity_penalty:  DataSparsityPenalty.
            decay_result:      ConfidenceDecayResult.
            realized_vol_nvu:  NVU-normalised realized volatility [0+].

        Returns:
            UncertaintyBundle with computed total_uncertainty.
        """
        epistemic_model = model_uncertainty.model_uncertainty_score

        epistemic_data = float(np.clip(
            sparsity_penalty.sparsity_penalty + decay_result.decay_applied,
            0.0, 1.0,
        ))

        aleatoric = float(np.clip(realized_vol_nvu / 5.0, 0.0, 1.0))

        total = float(np.clip(
            UNCERTAINTY_WEIGHT_MODEL * epistemic_model
            + UNCERTAINTY_WEIGHT_DATA * epistemic_data
            + UNCERTAINTY_WEIGHT_ALEATORIC * aleatoric,
            0.0, 1.0,
        ))

        return UncertaintyBundle(
            epistemic_model=epistemic_model,
            epistemic_data=epistemic_data,
            aleatoric=aleatoric,
            total_uncertainty=total,
            model_uncertainty_score=model_uncertainty.model_uncertainty_score,
            data_sparsity_penalty=sparsity_penalty.sparsity_penalty,
            confidence_decay_applied=decay_result.decay_applied,
        )
