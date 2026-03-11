# =============================================================================
# jarvis/systems/learning_engine.py — S12 Learning Engine
#
# Authority: FAS v6.0.1, S12
#
# Hybrid labeling from user + market feedback, online learning accumulation,
# and bias monitoring across expert, market, and regime dimensions.
#
# Entry points:
#   HybridesLabeling.create_label()    -> Label
#   OnlineLearner.process_feedback()   -> Label
#   BiasMonitor.detect_bias()          -> BiasReport
#
# CLASSIFICATION: Tier 6 — ANALYSIS AND STRATEGY RESEARCH TOOL.
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
#   No numpy / scipy / sklearn / torch
#   No logging module
#   No datetime.now() / time.time()
#   No random / secrets / uuid
#   No file IO / network IO
#   No global mutable state
#
# DEPENDENCIES
# ------------
#   stdlib:   dataclasses, enum, math
#   internal: NONE
#   external: NONE (pure Python)
# =============================================================================

from __future__ import annotations

import math
from dataclasses import dataclass
from enum import Enum

__all__ = [
    # Constants
    "USER_WEIGHT",
    "MARKET_WEIGHT",
    "ONLINE_UPDATE_THRESHOLD",
    "BIAS_CHECK_INTERVAL",
    "BIAS_THRESHOLD",
    "PREDICTION_ERROR_FLOOR",
    # Enums
    "BenutzerAktion",
    "Ergebnis",
    # Dataclasses
    "BenutzerFeedback",
    "MarktFeedback",
    "Label",
    "BiasReport",
    # Classes
    "HybridesLabeling",
    "OnlineLearner",
    "BiasMonitor",
]


# =============================================================================
# SECTION 1 -- CONSTANTS (DET-06: fixed literals, not parametrisable)
# =============================================================================

USER_WEIGHT: float = 0.6
"""Weight for user feedback in hybrid labeling."""

MARKET_WEIGHT: float = 0.4
"""Weight for market feedback in hybrid labeling."""

ONLINE_UPDATE_THRESHOLD: int = 100
"""Samples before triggering online update."""

BIAS_CHECK_INTERVAL: int = 500
"""Samples between bias checks."""

BIAS_THRESHOLD: float = 0.1
"""Bias magnitude threshold for alarm."""

PREDICTION_ERROR_FLOOR: float = 1e-10
"""Minimum prediction error for safe division."""


# =============================================================================
# SECTION 2 -- ENUMS
# =============================================================================

class BenutzerAktion(Enum):
    """User action on a prediction."""
    GEFOLGT = "GEFOLGT"
    IGNORIERT = "IGNORIERT"
    GEGENTEIL = "GEGENTEIL"


class Ergebnis(Enum):
    """Outcome of a prediction."""
    ERFOLG = "ERFOLG"
    NEUTRAL = "NEUTRAL"
    FEHLER = "FEHLER"


# =============================================================================
# SECTION 3 -- DATACLASSES
# =============================================================================

@dataclass(frozen=True)
class BenutzerFeedback:
    """User feedback on a prediction."""
    prediction_id: str
    benutzer_aktion: BenutzerAktion
    ergebnis: Ergebnis
    konfidenz: float

    def __post_init__(self) -> None:
        if not isinstance(self.prediction_id, str):
            raise TypeError(
                f"prediction_id must be str, got {type(self.prediction_id).__name__}"
            )
        if not isinstance(self.benutzer_aktion, BenutzerAktion):
            raise TypeError(
                f"benutzer_aktion must be BenutzerAktion, "
                f"got {type(self.benutzer_aktion).__name__}"
            )
        if not isinstance(self.ergebnis, Ergebnis):
            raise TypeError(
                f"ergebnis must be Ergebnis, got {type(self.ergebnis).__name__}"
            )
        if not isinstance(self.konfidenz, (int, float)):
            raise TypeError(
                f"konfidenz must be numeric, got {type(self.konfidenz).__name__}"
            )
        if not math.isfinite(self.konfidenz):
            raise ValueError(f"konfidenz must be finite, got {self.konfidenz!r}")
        if self.konfidenz < 0.0 or self.konfidenz > 1.0:
            raise ValueError(
                f"konfidenz must be in [0, 1], got {self.konfidenz!r}"
            )


@dataclass(frozen=True)
class MarktFeedback:
    """Market feedback on a prediction."""
    prediction_id: str
    tatsaechliches_ergebnis: float
    vorhersage_fehler: float

    def __post_init__(self) -> None:
        if not isinstance(self.prediction_id, str):
            raise TypeError(
                f"prediction_id must be str, got {type(self.prediction_id).__name__}"
            )
        if not isinstance(self.tatsaechliches_ergebnis, (int, float)):
            raise TypeError(
                f"tatsaechliches_ergebnis must be numeric, "
                f"got {type(self.tatsaechliches_ergebnis).__name__}"
            )
        if not math.isfinite(self.tatsaechliches_ergebnis):
            raise ValueError(
                f"tatsaechliches_ergebnis must be finite, "
                f"got {self.tatsaechliches_ergebnis!r}"
            )
        if not isinstance(self.vorhersage_fehler, (int, float)):
            raise TypeError(
                f"vorhersage_fehler must be numeric, "
                f"got {type(self.vorhersage_fehler).__name__}"
            )
        if not math.isfinite(self.vorhersage_fehler):
            raise ValueError(
                f"vorhersage_fehler must be finite, "
                f"got {self.vorhersage_fehler!r}"
            )
        if self.vorhersage_fehler < 0.0:
            raise ValueError(
                f"vorhersage_fehler must be >= 0, got {self.vorhersage_fehler!r}"
            )


@dataclass(frozen=True)
class Label:
    """Hybrid label combining user and market feedback."""
    wert: float
    unsicherheit: float

    def __post_init__(self) -> None:
        if not isinstance(self.wert, (int, float)):
            raise TypeError(
                f"wert must be numeric, got {type(self.wert).__name__}"
            )
        if not math.isfinite(self.wert):
            raise ValueError(f"wert must be finite, got {self.wert!r}")
        if self.wert < -1.0 or self.wert > 1.0:
            raise ValueError(f"wert must be in [-1, 1], got {self.wert!r}")
        if not isinstance(self.unsicherheit, (int, float)):
            raise TypeError(
                f"unsicherheit must be numeric, "
                f"got {type(self.unsicherheit).__name__}"
            )
        if not math.isfinite(self.unsicherheit):
            raise ValueError(
                f"unsicherheit must be finite, got {self.unsicherheit!r}"
            )
        if self.unsicherheit < 0.0 or self.unsicherheit > 1.0:
            raise ValueError(
                f"unsicherheit must be in [0, 1], got {self.unsicherheit!r}"
            )


@dataclass(frozen=True)
class BiasReport:
    """Report from bias monitoring."""
    experten_bias: float
    markt_bias: float
    regime_bias: float
    is_biased: bool
    dominant_bias: str

    def __post_init__(self) -> None:
        for name, val in [
            ("experten_bias", self.experten_bias),
            ("markt_bias", self.markt_bias),
            ("regime_bias", self.regime_bias),
        ]:
            if not isinstance(val, (int, float)):
                raise TypeError(
                    f"BiasReport.{name} must be numeric, "
                    f"got {type(val).__name__}"
                )
            if not math.isfinite(val):
                raise ValueError(
                    f"BiasReport.{name} must be finite, got {val!r}"
                )
        if not isinstance(self.is_biased, bool):
            raise TypeError(
                f"BiasReport.is_biased must be bool, "
                f"got {type(self.is_biased).__name__}"
            )
        if not isinstance(self.dominant_bias, str):
            raise TypeError(
                f"BiasReport.dominant_bias must be str, "
                f"got {type(self.dominant_bias).__name__}"
            )
        valid_dominant = ("EXPERTEN", "MARKT", "REGIME", "NONE")
        if self.dominant_bias not in valid_dominant:
            raise ValueError(
                f"BiasReport.dominant_bias must be one of {valid_dominant}, "
                f"got {self.dominant_bias!r}"
            )


# =============================================================================
# SECTION 4 -- HELPERS
# =============================================================================

def _clamp(value: float, lo: float, hi: float) -> float:
    """Clamp a value to [lo, hi]."""
    if value < lo:
        return lo
    if value > hi:
        return hi
    return value


def _outcome_score(ergebnis: Ergebnis) -> float:
    """Map Ergebnis enum to numeric score."""
    if ergebnis == Ergebnis.ERFOLG:
        return 1.0
    if ergebnis == Ergebnis.NEUTRAL:
        return 0.0
    # FEHLER
    return -1.0


# =============================================================================
# SECTION 5 -- HYBRIDES LABELING
# =============================================================================

class HybridesLabeling:
    """
    Creates hybrid labels from user and market feedback.

    Combines user action/outcome signals with market prediction error
    using fixed weights (USER_WEIGHT, MARKET_WEIGHT).
    """

    def create_label(
        self,
        benutzer_fb: BenutzerFeedback,
        markt_fb: MarktFeedback,
    ) -> Label:
        """
        Combine user and market feedback into a hybrid label.

        User signal mapping:
          GEFOLGT + ERFOLG   -> +1.0
          GEFOLGT + FEHLER   -> -0.5
          GEFOLGT + NEUTRAL  -> +0.5  (scaled by 0.5)
          IGNORIERT          ->  0.0
          GEGENTEIL + ERFOLG -> -1.0  (user was right to oppose)
          GEGENTEIL + FEHLER -> +0.5
          GEGENTEIL + NEUTRAL -> -0.5 (scaled by 0.5)

        Market signal: -vorhersage_fehler, clipped to [-1, 1].

        wert = USER_WEIGHT * user_signal + MARKET_WEIGHT * market_signal
        unsicherheit = 1.0 - konfidenz * (1.0 - vorhersage_fehler)
        Both clipped to valid ranges.

        Args:
            benutzer_fb: User feedback.
            markt_fb:    Market feedback.

        Returns:
            Label with wert in [-1, 1] and unsicherheit in [0, 1].
        """
        user_signal = self._compute_user_signal(
            benutzer_fb.benutzer_aktion, benutzer_fb.ergebnis
        )
        market_signal = self._compute_market_signal(markt_fb.vorhersage_fehler)

        raw_wert = USER_WEIGHT * user_signal + MARKET_WEIGHT * market_signal
        wert = _clamp(raw_wert, -1.0, 1.0)

        # NaN/Inf guard
        if not math.isfinite(wert):
            wert = 0.0

        # Uncertainty: higher when low confidence or high prediction error
        raw_unsicherheit = 1.0 - benutzer_fb.konfidenz * (
            1.0 - markt_fb.vorhersage_fehler
        )
        unsicherheit = _clamp(raw_unsicherheit, 0.0, 1.0)

        # NaN/Inf guard
        if not math.isfinite(unsicherheit):
            unsicherheit = 1.0

        return Label(wert=wert, unsicherheit=unsicherheit)

    def _compute_user_signal(
        self, aktion: BenutzerAktion, ergebnis: Ergebnis
    ) -> float:
        """Compute user signal from action and outcome."""
        if aktion == BenutzerAktion.IGNORIERT:
            return 0.0

        if aktion == BenutzerAktion.GEFOLGT:
            if ergebnis == Ergebnis.ERFOLG:
                return 1.0
            if ergebnis == Ergebnis.FEHLER:
                return -0.5
            # NEUTRAL
            return 0.5

        # GEGENTEIL
        if ergebnis == Ergebnis.ERFOLG:
            return -1.0
        if ergebnis == Ergebnis.FEHLER:
            return 0.5
        # NEUTRAL
        return -0.5

    def _compute_market_signal(self, vorhersage_fehler: float) -> float:
        """Compute market signal from prediction error."""
        raw = -vorhersage_fehler
        return _clamp(raw, -1.0, 1.0)


# =============================================================================
# SECTION 6 -- ONLINE LEARNER
# =============================================================================

class OnlineLearner:
    """
    Processes feedback and triggers recalibration when needed.

    Accumulates hybrid labels from user+market feedback. Signals
    when ONLINE_UPDATE_THRESHOLD new samples have arrived since
    the last update.

    Instance state is per-object (no global mutable state). A fresh
    OnlineLearner should be created per session (DET-02).
    """

    def __init__(self) -> None:
        self._labels: list = []
        self._sample_count: int = 0
        self._last_update_count: int = 0
        self._labeler: HybridesLabeling = HybridesLabeling()

    def process_feedback(
        self,
        benutzer_fb: BenutzerFeedback,
        markt_fb: MarktFeedback,
    ) -> Label:
        """
        Create hybrid label and store it.

        Args:
            benutzer_fb: User feedback.
            markt_fb:    Market feedback.

        Returns:
            The created Label.
        """
        label = self._labeler.create_label(benutzer_fb, markt_fb)
        self._labels.append(label)
        self._sample_count += 1
        return label

    def should_update(self) -> bool:
        """True if ONLINE_UPDATE_THRESHOLD new samples since last update."""
        return (
            self._sample_count - self._last_update_count
            >= ONLINE_UPDATE_THRESHOLD
        )

    def get_recent_labels(self, n: int = 100) -> tuple:
        """Return last n labels as tuple."""
        if n <= 0:
            return ()
        return tuple(self._labels[-n:])

    def get_mean_label_value(self) -> float:
        """Mean of recent label values. 0.0 if empty."""
        if len(self._labels) == 0:
            return 0.0
        total = sum(label.wert for label in self._labels)
        result = total / len(self._labels)
        if not math.isfinite(result):
            return 0.0
        return result

    def get_mean_uncertainty(self) -> float:
        """Mean of recent label uncertainties. 1.0 if empty."""
        if len(self._labels) == 0:
            return 1.0
        total = sum(label.unsicherheit for label in self._labels)
        result = total / len(self._labels)
        if not math.isfinite(result):
            return 1.0
        return result

    def mark_updated(self) -> None:
        """Record that an update was performed."""
        self._last_update_count = self._sample_count


# =============================================================================
# SECTION 7 -- BIAS MONITOR
# =============================================================================

class BiasMonitor:
    """
    Monitors for systematic biases in predictions.

    Tracks user outcomes, market errors, and regime-specific errors
    to detect expert bias, market bias, and regime-dependent bias.

    Instance state is per-object (no global mutable state). A fresh
    BiasMonitor should be created per session (DET-02).
    """

    def __init__(self) -> None:
        self._user_outcomes: list = []      # (action, outcome) pairs
        self._market_errors: list = []      # prediction errors
        self._regime_errors: dict = {}      # {regime: [errors]}
        self._total_samples: int = 0

    def record(
        self,
        benutzer_fb: BenutzerFeedback,
        markt_fb: MarktFeedback,
        regime: str = "UNKNOWN",
    ) -> None:
        """
        Record feedback for bias tracking.

        Args:
            benutzer_fb: User feedback.
            markt_fb:    Market feedback.
            regime:      Regime string (default "UNKNOWN").
        """
        self._user_outcomes.append(
            (benutzer_fb.benutzer_aktion, benutzer_fb.ergebnis)
        )
        self._market_errors.append(markt_fb.vorhersage_fehler)

        if regime not in self._regime_errors:
            self._regime_errors[regime] = []
        self._regime_errors[regime].append(markt_fb.vorhersage_fehler)

        self._total_samples += 1

    def should_check(self) -> bool:
        """True if BIAS_CHECK_INTERVAL samples accumulated."""
        return self._total_samples >= BIAS_CHECK_INTERVAL

    def detect_bias(self) -> BiasReport:
        """
        Detect biases across three dimensions.

        experten_bias: mean(outcome_score for GEFOLGT) -
                       mean(outcome_score for GEGENTEIL)
          where ERFOLG=1, NEUTRAL=0, FEHLER=-1.
          Returns 0.0 if either group is empty.

        markt_bias: mean(market_errors) (deviation from expected 0.0).

        regime_bias: max |mean_error_i - mean_error_j| across regime pairs.
          Returns 0.0 if fewer than 2 regimes.

        is_biased: any magnitude > BIAS_THRESHOLD.
        dominant_bias: whichever has highest magnitude, or "NONE".

        Returns:
            BiasReport with all bias dimensions.
        """
        experten_bias = self._compute_experten_bias()
        markt_bias = self._compute_markt_bias()
        regime_bias = self._compute_regime_bias()

        # NaN/Inf guards
        if not math.isfinite(experten_bias):
            experten_bias = 0.0
        if not math.isfinite(markt_bias):
            markt_bias = 0.0
        if not math.isfinite(regime_bias):
            regime_bias = 0.0

        abs_exp = abs(experten_bias)
        abs_mkt = abs(markt_bias)
        abs_reg = abs(regime_bias)

        is_biased = (
            abs_exp > BIAS_THRESHOLD
            or abs_mkt > BIAS_THRESHOLD
            or abs_reg > BIAS_THRESHOLD
        )

        # Determine dominant bias
        if not is_biased:
            dominant_bias = "NONE"
        else:
            max_bias = max(abs_exp, abs_mkt, abs_reg)
            if max_bias == abs_exp:
                dominant_bias = "EXPERTEN"
            elif max_bias == abs_mkt:
                dominant_bias = "MARKT"
            else:
                dominant_bias = "REGIME"

        return BiasReport(
            experten_bias=experten_bias,
            markt_bias=markt_bias,
            regime_bias=regime_bias,
            is_biased=is_biased,
            dominant_bias=dominant_bias,
        )

    def _compute_experten_bias(self) -> float:
        """Compute expert bias: mean(GEFOLGT scores) - mean(GEGENTEIL scores)."""
        gefolgt_scores: list = []
        gegenteil_scores: list = []

        for aktion, ergebnis in self._user_outcomes:
            score = _outcome_score(ergebnis)
            if aktion == BenutzerAktion.GEFOLGT:
                gefolgt_scores.append(score)
            elif aktion == BenutzerAktion.GEGENTEIL:
                gegenteil_scores.append(score)

        if len(gefolgt_scores) == 0 or len(gegenteil_scores) == 0:
            return 0.0

        mean_gefolgt = sum(gefolgt_scores) / len(gefolgt_scores)
        mean_gegenteil = sum(gegenteil_scores) / len(gegenteil_scores)

        result = mean_gefolgt - mean_gegenteil
        if not math.isfinite(result):
            return 0.0
        return result

    def _compute_markt_bias(self) -> float:
        """Compute market bias: mean(market_errors)."""
        if len(self._market_errors) == 0:
            return 0.0
        result = sum(self._market_errors) / len(self._market_errors)
        if not math.isfinite(result):
            return 0.0
        return result

    def _compute_regime_bias(self) -> float:
        """Compute regime bias: max |mean_error_i - mean_error_j| across regimes."""
        if len(self._regime_errors) < 2:
            return 0.0

        # Compute mean error per regime
        regime_means: list = []
        for regime, errors in sorted(self._regime_errors.items()):
            if len(errors) == 0:
                continue
            mean_err = sum(errors) / len(errors)
            if math.isfinite(mean_err):
                regime_means.append(mean_err)

        if len(regime_means) < 2:
            return 0.0

        # Max absolute difference between any pair
        max_diff = 0.0
        for i in range(len(regime_means)):
            for j in range(i + 1, len(regime_means)):
                diff = abs(regime_means[i] - regime_means[j])
                if diff > max_diff:
                    max_diff = diff

        if not math.isfinite(max_diff):
            return 0.0
        return max_diff
