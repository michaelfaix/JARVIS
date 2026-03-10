# =============================================================================
# JARVIS v6.0.1 — SESSION 05, PHASE 5.4: VOLATILITY TRACKER
# File:   jarvis/core/volatility_tracker.py
# Authority: JARVIS FAS v6.0.1 — 02-05_CORE.md, S05 section
# Phase:  5.4 — VolatilityTracker (GARCH(1,1) volatility estimation)
# =============================================================================
#
# SCOPE (Phase 5.4)
# -----------------
# Implements:
#   - VolResult   dataclass (frozen=True)
#   - VolatilityTracker class
#       * estimate_volatility(returns) -> VolResult
#       * predict_volatility(horizon)  -> float
#
# CONSTRAINTS
# -----------
# stdlib only: dataclasses, math, typing.
# No numpy. No scipy. No pandas. No random. No datetime.now().
# No file I/O. No logging. No global mutable state (beyond internal state).
#
# DETERMINISM GUARANTEES
# ----------------------
# DET-01  No stochastic operations.
# DET-02  All inputs passed explicitly.
# DET-03  No side effects beyond updating internal GARCH state.
# DET-04  All arithmetic deterministic.
# DET-05  All branches pure functions of explicit inputs.
# DET-06  No datetime.now().
#
# GARCH(1,1) MODEL SPECIFICATION
# --------------------------------
# sigma^2_t = omega + alpha * r_{t-1}^2 + beta * sigma^2_{t-1}
#
# where:
#   omega = long-run variance component (> 0)
#   alpha = ARCH coefficient (shock sensitivity)
#   beta  = GARCH coefficient (variance persistence)
#   alpha + beta < 1 (stationarity constraint, enforced)
#
# Default parameters calibrated for daily financial returns:
#   omega = 1e-6  (very small constant to maintain positivity)
#   alpha = 0.10  (10% weight on squared shock)
#   beta  = 0.85  (85% variance persistence)
#
# Volatility = sqrt(sigma^2_t), floored at EPSILON = 1e-8.
#
# Predict horizon h:
#   sigma^2_{t+h} = omega/(1-alpha-beta) + (alpha+beta)^h * (sigma^2_t - omega/(1-alpha-beta))
#
# INVARIANTS
# ----------
# INV-P54-01  estimate_volatility() raises ValueError for empty or
#             all-non-finite returns lists.
# INV-P54-02  Volatility is always > 0 (EPSILON floor applied everywhere).
# INV-P54-03  predict_volatility(horizon) requires horizon >= 1.
# INV-P54-04  Non-finite return values are replaced with 0.0 before processing.
# INV-P54-05  VolResult.volatility > 0 always.
# INV-P54-06  VolResult.variance > 0 always.
# INV-P54-07  VolResult.n_clean_returns >= 0.
# =============================================================================

from __future__ import annotations

import math
from dataclasses import dataclass
from typing import List


# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

#: Epsilon floor for volatility to guarantee strict positivity.
_VOL_EPSILON: float = 1e-8

#: Default GARCH(1,1) parameters.
_DEFAULT_OMEGA: float = 1e-6
_DEFAULT_ALPHA: float = 0.10
_DEFAULT_BETA: float  = 0.85

#: Minimum number of returns required for a meaningful GARCH estimate.
_MIN_RETURNS: int = 2

#: Initial variance guess (used before any data is seen).
_INIT_VARIANCE: float = 1e-4
from typing import Annotated
from typing import Callable
from typing import ClassVar

MutantDict = Annotated[dict[str, Callable], "Mutant"] # type: ignore


def _mutmut_trampoline(orig, mutants, call_args, call_kwargs, self_arg = None): # type: ignore
    """Forward call to original or mutated function, depending on the environment"""
    import os # type: ignore
    mutant_under_test = os.environ['MUTANT_UNDER_TEST'] # type: ignore
    if mutant_under_test == 'fail': # type: ignore
        from mutmut.__main__ import MutmutProgrammaticFailException # type: ignore
        raise MutmutProgrammaticFailException('Failed programmatically')       # type: ignore
    elif mutant_under_test == 'stats': # type: ignore
        from mutmut.__main__ import record_trampoline_hit # type: ignore
        record_trampoline_hit(orig.__module__ + '.' + orig.__name__) # type: ignore
        # (for class methods, orig is bound and thus does not need the explicit self argument)
        result = orig(*call_args, **call_kwargs) # type: ignore
        return result # type: ignore
    prefix = orig.__module__ + '.' + orig.__name__ + '__mutmut_' # type: ignore
    if not mutant_under_test.startswith(prefix): # type: ignore
        result = orig(*call_args, **call_kwargs) # type: ignore
        return result # type: ignore
    mutant_name = mutant_under_test.rpartition('.')[-1] # type: ignore
    if self_arg is not None: # type: ignore
        # call to a class method where self is not bound
        result = mutants[mutant_name](self_arg, *call_args, **call_kwargs) # type: ignore
    else:
        result = mutants[mutant_name](*call_args, **call_kwargs) # type: ignore
    return result # type: ignore


# ---------------------------------------------------------------------------
# VolResult
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class VolResult:
    """
    Immutable result of a GARCH(1,1) volatility estimation step.

    Fields
    ------
    volatility : float
        Current conditional volatility = sqrt(variance). Always > 0.
    variance : float
        Current conditional variance sigma^2_t. Always > 0.
    long_run_volatility : float
        Unconditional (long-run) volatility = sqrt(omega / (1-alpha-beta)).
        Always > 0. Valid only when alpha + beta < 1.
    n_clean_returns : int
        Number of finite return observations used in this estimate.
    nan_replaced : int
        Number of non-finite return values replaced with 0.0.
    """
    volatility: float
    variance: float
    long_run_volatility: float
    n_clean_returns: int
    nan_replaced: int

    def __post_init__(self) -> None:
        if not math.isfinite(self.volatility) or self.volatility <= 0.0:
            raise ValueError(
                f"VolResult.volatility must be finite and > 0, "
                f"got {self.volatility!r}."
            )
        if not math.isfinite(self.variance) or self.variance <= 0.0:
            raise ValueError(
                f"VolResult.variance must be finite and > 0, "
                f"got {self.variance!r}."
            )
        if not math.isfinite(self.long_run_volatility) or self.long_run_volatility <= 0.0:
            raise ValueError(
                f"VolResult.long_run_volatility must be finite and > 0, "
                f"got {self.long_run_volatility!r}."
            )
        if self.n_clean_returns < 0:
            raise ValueError(
                f"VolResult.n_clean_returns must be >= 0, "
                f"got {self.n_clean_returns!r}."
            )
        if self.nan_replaced < 0:
            raise ValueError(
                f"VolResult.nan_replaced must be >= 0, "
                f"got {self.nan_replaced!r}."
            )


# ---------------------------------------------------------------------------
# VolatilityTracker
# ---------------------------------------------------------------------------

class VolatilityTracker:
    """
    GARCH(1,1) volatility tracker.

    Maintains a running conditional variance estimate and updates it
    sequentially as new return observations arrive.

    GARCH(1,1) EQUATION:
      sigma^2_t = omega + alpha * r_{t-1}^2 + beta * sigma^2_{t-1}

    STATIONARITY CONSTRAINT (enforced on construction):
      alpha + beta must be < 1.0.
      If the supplied parameters violate this, they are rescaled to
      satisfy alpha + beta = 0.95 while preserving their ratio.

    MUTABLE STATE:
      self._current_variance tracks the most recent conditional variance.
      Only estimate_volatility() mutates this state.

    STDLIB ONLY: no numpy, no scipy, no random.
    """

    def __init__(
        self,
        omega: float = _DEFAULT_OMEGA,
        alpha: float = _DEFAULT_ALPHA,
        beta: float  = _DEFAULT_BETA,
    ) -> None:
        args = [omega, alpha, beta]# type: ignore
        kwargs = {}# type: ignore
        return _mutmut_trampoline(object.__getattribute__(self, 'xǁVolatilityTrackerǁ__init____mutmut_orig'), object.__getattribute__(self, 'xǁVolatilityTrackerǁ__init____mutmut_mutants'), args, kwargs, self)

    def xǁVolatilityTrackerǁ__init____mutmut_orig(
        self,
        omega: float = _DEFAULT_OMEGA,
        alpha: float = _DEFAULT_ALPHA,
        beta: float  = _DEFAULT_BETA,
    ) -> None:
        """
        Initialise the GARCH(1,1) tracker.

        Parameters
        ----------
        omega : float
            Long-run variance component. Must be > 0.
        alpha : float
            ARCH coefficient (shock sensitivity). Must be in (0, 1).
        beta : float
            GARCH coefficient (persistence). Must be in (0, 1).

        Notes
        -----
        If alpha + beta >= 1.0, parameters are rescaled so that
        alpha + beta = 0.95 (the stationarity boundary with margin),
        preserving the ratio alpha / beta.
        """
        if omega <= 0.0 or not math.isfinite(omega):
            raise ValueError(f"omega must be > 0, got {omega!r}.")
        if not (0.0 < alpha < 1.0):
            raise ValueError(f"alpha must be in (0, 1), got {alpha!r}.")
        if not (0.0 < beta < 1.0):
            raise ValueError(f"beta must be in (0, 1), got {beta!r}.")

        # Enforce stationarity: alpha + beta < 1.
        if alpha + beta >= 1.0:
            scale: float = 0.95 / (alpha + beta)
            alpha = alpha * scale
            beta  = beta  * scale

        self._omega: float = omega
        self._alpha: float = alpha
        self._beta:  float = beta

        # Compute long-run variance: omega / (1 - alpha - beta)
        persistence: float = self._alpha + self._beta
        denom: float = 1.0 - persistence
        self._long_run_variance: float = max(
            _VOL_EPSILON ** 2,
            self._omega / denom,
        )

        # Initialise current variance to the long-run variance.
        self._current_variance: float = self._long_run_variance

    def xǁVolatilityTrackerǁ__init____mutmut_1(
        self,
        omega: float = _DEFAULT_OMEGA,
        alpha: float = _DEFAULT_ALPHA,
        beta: float  = _DEFAULT_BETA,
    ) -> None:
        """
        Initialise the GARCH(1,1) tracker.

        Parameters
        ----------
        omega : float
            Long-run variance component. Must be > 0.
        alpha : float
            ARCH coefficient (shock sensitivity). Must be in (0, 1).
        beta : float
            GARCH coefficient (persistence). Must be in (0, 1).

        Notes
        -----
        If alpha + beta >= 1.0, parameters are rescaled so that
        alpha + beta = 0.95 (the stationarity boundary with margin),
        preserving the ratio alpha / beta.
        """
        if omega <= 0.0 and not math.isfinite(omega):
            raise ValueError(f"omega must be > 0, got {omega!r}.")
        if not (0.0 < alpha < 1.0):
            raise ValueError(f"alpha must be in (0, 1), got {alpha!r}.")
        if not (0.0 < beta < 1.0):
            raise ValueError(f"beta must be in (0, 1), got {beta!r}.")

        # Enforce stationarity: alpha + beta < 1.
        if alpha + beta >= 1.0:
            scale: float = 0.95 / (alpha + beta)
            alpha = alpha * scale
            beta  = beta  * scale

        self._omega: float = omega
        self._alpha: float = alpha
        self._beta:  float = beta

        # Compute long-run variance: omega / (1 - alpha - beta)
        persistence: float = self._alpha + self._beta
        denom: float = 1.0 - persistence
        self._long_run_variance: float = max(
            _VOL_EPSILON ** 2,
            self._omega / denom,
        )

        # Initialise current variance to the long-run variance.
        self._current_variance: float = self._long_run_variance

    def xǁVolatilityTrackerǁ__init____mutmut_2(
        self,
        omega: float = _DEFAULT_OMEGA,
        alpha: float = _DEFAULT_ALPHA,
        beta: float  = _DEFAULT_BETA,
    ) -> None:
        """
        Initialise the GARCH(1,1) tracker.

        Parameters
        ----------
        omega : float
            Long-run variance component. Must be > 0.
        alpha : float
            ARCH coefficient (shock sensitivity). Must be in (0, 1).
        beta : float
            GARCH coefficient (persistence). Must be in (0, 1).

        Notes
        -----
        If alpha + beta >= 1.0, parameters are rescaled so that
        alpha + beta = 0.95 (the stationarity boundary with margin),
        preserving the ratio alpha / beta.
        """
        if omega < 0.0 or not math.isfinite(omega):
            raise ValueError(f"omega must be > 0, got {omega!r}.")
        if not (0.0 < alpha < 1.0):
            raise ValueError(f"alpha must be in (0, 1), got {alpha!r}.")
        if not (0.0 < beta < 1.0):
            raise ValueError(f"beta must be in (0, 1), got {beta!r}.")

        # Enforce stationarity: alpha + beta < 1.
        if alpha + beta >= 1.0:
            scale: float = 0.95 / (alpha + beta)
            alpha = alpha * scale
            beta  = beta  * scale

        self._omega: float = omega
        self._alpha: float = alpha
        self._beta:  float = beta

        # Compute long-run variance: omega / (1 - alpha - beta)
        persistence: float = self._alpha + self._beta
        denom: float = 1.0 - persistence
        self._long_run_variance: float = max(
            _VOL_EPSILON ** 2,
            self._omega / denom,
        )

        # Initialise current variance to the long-run variance.
        self._current_variance: float = self._long_run_variance

    def xǁVolatilityTrackerǁ__init____mutmut_3(
        self,
        omega: float = _DEFAULT_OMEGA,
        alpha: float = _DEFAULT_ALPHA,
        beta: float  = _DEFAULT_BETA,
    ) -> None:
        """
        Initialise the GARCH(1,1) tracker.

        Parameters
        ----------
        omega : float
            Long-run variance component. Must be > 0.
        alpha : float
            ARCH coefficient (shock sensitivity). Must be in (0, 1).
        beta : float
            GARCH coefficient (persistence). Must be in (0, 1).

        Notes
        -----
        If alpha + beta >= 1.0, parameters are rescaled so that
        alpha + beta = 0.95 (the stationarity boundary with margin),
        preserving the ratio alpha / beta.
        """
        if omega <= 1.0 or not math.isfinite(omega):
            raise ValueError(f"omega must be > 0, got {omega!r}.")
        if not (0.0 < alpha < 1.0):
            raise ValueError(f"alpha must be in (0, 1), got {alpha!r}.")
        if not (0.0 < beta < 1.0):
            raise ValueError(f"beta must be in (0, 1), got {beta!r}.")

        # Enforce stationarity: alpha + beta < 1.
        if alpha + beta >= 1.0:
            scale: float = 0.95 / (alpha + beta)
            alpha = alpha * scale
            beta  = beta  * scale

        self._omega: float = omega
        self._alpha: float = alpha
        self._beta:  float = beta

        # Compute long-run variance: omega / (1 - alpha - beta)
        persistence: float = self._alpha + self._beta
        denom: float = 1.0 - persistence
        self._long_run_variance: float = max(
            _VOL_EPSILON ** 2,
            self._omega / denom,
        )

        # Initialise current variance to the long-run variance.
        self._current_variance: float = self._long_run_variance

    def xǁVolatilityTrackerǁ__init____mutmut_4(
        self,
        omega: float = _DEFAULT_OMEGA,
        alpha: float = _DEFAULT_ALPHA,
        beta: float  = _DEFAULT_BETA,
    ) -> None:
        """
        Initialise the GARCH(1,1) tracker.

        Parameters
        ----------
        omega : float
            Long-run variance component. Must be > 0.
        alpha : float
            ARCH coefficient (shock sensitivity). Must be in (0, 1).
        beta : float
            GARCH coefficient (persistence). Must be in (0, 1).

        Notes
        -----
        If alpha + beta >= 1.0, parameters are rescaled so that
        alpha + beta = 0.95 (the stationarity boundary with margin),
        preserving the ratio alpha / beta.
        """
        if omega <= 0.0 or math.isfinite(omega):
            raise ValueError(f"omega must be > 0, got {omega!r}.")
        if not (0.0 < alpha < 1.0):
            raise ValueError(f"alpha must be in (0, 1), got {alpha!r}.")
        if not (0.0 < beta < 1.0):
            raise ValueError(f"beta must be in (0, 1), got {beta!r}.")

        # Enforce stationarity: alpha + beta < 1.
        if alpha + beta >= 1.0:
            scale: float = 0.95 / (alpha + beta)
            alpha = alpha * scale
            beta  = beta  * scale

        self._omega: float = omega
        self._alpha: float = alpha
        self._beta:  float = beta

        # Compute long-run variance: omega / (1 - alpha - beta)
        persistence: float = self._alpha + self._beta
        denom: float = 1.0 - persistence
        self._long_run_variance: float = max(
            _VOL_EPSILON ** 2,
            self._omega / denom,
        )

        # Initialise current variance to the long-run variance.
        self._current_variance: float = self._long_run_variance

    def xǁVolatilityTrackerǁ__init____mutmut_5(
        self,
        omega: float = _DEFAULT_OMEGA,
        alpha: float = _DEFAULT_ALPHA,
        beta: float  = _DEFAULT_BETA,
    ) -> None:
        """
        Initialise the GARCH(1,1) tracker.

        Parameters
        ----------
        omega : float
            Long-run variance component. Must be > 0.
        alpha : float
            ARCH coefficient (shock sensitivity). Must be in (0, 1).
        beta : float
            GARCH coefficient (persistence). Must be in (0, 1).

        Notes
        -----
        If alpha + beta >= 1.0, parameters are rescaled so that
        alpha + beta = 0.95 (the stationarity boundary with margin),
        preserving the ratio alpha / beta.
        """
        if omega <= 0.0 or not math.isfinite(None):
            raise ValueError(f"omega must be > 0, got {omega!r}.")
        if not (0.0 < alpha < 1.0):
            raise ValueError(f"alpha must be in (0, 1), got {alpha!r}.")
        if not (0.0 < beta < 1.0):
            raise ValueError(f"beta must be in (0, 1), got {beta!r}.")

        # Enforce stationarity: alpha + beta < 1.
        if alpha + beta >= 1.0:
            scale: float = 0.95 / (alpha + beta)
            alpha = alpha * scale
            beta  = beta  * scale

        self._omega: float = omega
        self._alpha: float = alpha
        self._beta:  float = beta

        # Compute long-run variance: omega / (1 - alpha - beta)
        persistence: float = self._alpha + self._beta
        denom: float = 1.0 - persistence
        self._long_run_variance: float = max(
            _VOL_EPSILON ** 2,
            self._omega / denom,
        )

        # Initialise current variance to the long-run variance.
        self._current_variance: float = self._long_run_variance

    def xǁVolatilityTrackerǁ__init____mutmut_6(
        self,
        omega: float = _DEFAULT_OMEGA,
        alpha: float = _DEFAULT_ALPHA,
        beta: float  = _DEFAULT_BETA,
    ) -> None:
        """
        Initialise the GARCH(1,1) tracker.

        Parameters
        ----------
        omega : float
            Long-run variance component. Must be > 0.
        alpha : float
            ARCH coefficient (shock sensitivity). Must be in (0, 1).
        beta : float
            GARCH coefficient (persistence). Must be in (0, 1).

        Notes
        -----
        If alpha + beta >= 1.0, parameters are rescaled so that
        alpha + beta = 0.95 (the stationarity boundary with margin),
        preserving the ratio alpha / beta.
        """
        if omega <= 0.0 or not math.isfinite(omega):
            raise ValueError(None)
        if not (0.0 < alpha < 1.0):
            raise ValueError(f"alpha must be in (0, 1), got {alpha!r}.")
        if not (0.0 < beta < 1.0):
            raise ValueError(f"beta must be in (0, 1), got {beta!r}.")

        # Enforce stationarity: alpha + beta < 1.
        if alpha + beta >= 1.0:
            scale: float = 0.95 / (alpha + beta)
            alpha = alpha * scale
            beta  = beta  * scale

        self._omega: float = omega
        self._alpha: float = alpha
        self._beta:  float = beta

        # Compute long-run variance: omega / (1 - alpha - beta)
        persistence: float = self._alpha + self._beta
        denom: float = 1.0 - persistence
        self._long_run_variance: float = max(
            _VOL_EPSILON ** 2,
            self._omega / denom,
        )

        # Initialise current variance to the long-run variance.
        self._current_variance: float = self._long_run_variance

    def xǁVolatilityTrackerǁ__init____mutmut_7(
        self,
        omega: float = _DEFAULT_OMEGA,
        alpha: float = _DEFAULT_ALPHA,
        beta: float  = _DEFAULT_BETA,
    ) -> None:
        """
        Initialise the GARCH(1,1) tracker.

        Parameters
        ----------
        omega : float
            Long-run variance component. Must be > 0.
        alpha : float
            ARCH coefficient (shock sensitivity). Must be in (0, 1).
        beta : float
            GARCH coefficient (persistence). Must be in (0, 1).

        Notes
        -----
        If alpha + beta >= 1.0, parameters are rescaled so that
        alpha + beta = 0.95 (the stationarity boundary with margin),
        preserving the ratio alpha / beta.
        """
        if omega <= 0.0 or not math.isfinite(omega):
            raise ValueError(f"omega must be > 0, got {omega!r}.")
        if (0.0 < alpha < 1.0):
            raise ValueError(f"alpha must be in (0, 1), got {alpha!r}.")
        if not (0.0 < beta < 1.0):
            raise ValueError(f"beta must be in (0, 1), got {beta!r}.")

        # Enforce stationarity: alpha + beta < 1.
        if alpha + beta >= 1.0:
            scale: float = 0.95 / (alpha + beta)
            alpha = alpha * scale
            beta  = beta  * scale

        self._omega: float = omega
        self._alpha: float = alpha
        self._beta:  float = beta

        # Compute long-run variance: omega / (1 - alpha - beta)
        persistence: float = self._alpha + self._beta
        denom: float = 1.0 - persistence
        self._long_run_variance: float = max(
            _VOL_EPSILON ** 2,
            self._omega / denom,
        )

        # Initialise current variance to the long-run variance.
        self._current_variance: float = self._long_run_variance

    def xǁVolatilityTrackerǁ__init____mutmut_8(
        self,
        omega: float = _DEFAULT_OMEGA,
        alpha: float = _DEFAULT_ALPHA,
        beta: float  = _DEFAULT_BETA,
    ) -> None:
        """
        Initialise the GARCH(1,1) tracker.

        Parameters
        ----------
        omega : float
            Long-run variance component. Must be > 0.
        alpha : float
            ARCH coefficient (shock sensitivity). Must be in (0, 1).
        beta : float
            GARCH coefficient (persistence). Must be in (0, 1).

        Notes
        -----
        If alpha + beta >= 1.0, parameters are rescaled so that
        alpha + beta = 0.95 (the stationarity boundary with margin),
        preserving the ratio alpha / beta.
        """
        if omega <= 0.0 or not math.isfinite(omega):
            raise ValueError(f"omega must be > 0, got {omega!r}.")
        if not (1.0 < alpha < 1.0):
            raise ValueError(f"alpha must be in (0, 1), got {alpha!r}.")
        if not (0.0 < beta < 1.0):
            raise ValueError(f"beta must be in (0, 1), got {beta!r}.")

        # Enforce stationarity: alpha + beta < 1.
        if alpha + beta >= 1.0:
            scale: float = 0.95 / (alpha + beta)
            alpha = alpha * scale
            beta  = beta  * scale

        self._omega: float = omega
        self._alpha: float = alpha
        self._beta:  float = beta

        # Compute long-run variance: omega / (1 - alpha - beta)
        persistence: float = self._alpha + self._beta
        denom: float = 1.0 - persistence
        self._long_run_variance: float = max(
            _VOL_EPSILON ** 2,
            self._omega / denom,
        )

        # Initialise current variance to the long-run variance.
        self._current_variance: float = self._long_run_variance

    def xǁVolatilityTrackerǁ__init____mutmut_9(
        self,
        omega: float = _DEFAULT_OMEGA,
        alpha: float = _DEFAULT_ALPHA,
        beta: float  = _DEFAULT_BETA,
    ) -> None:
        """
        Initialise the GARCH(1,1) tracker.

        Parameters
        ----------
        omega : float
            Long-run variance component. Must be > 0.
        alpha : float
            ARCH coefficient (shock sensitivity). Must be in (0, 1).
        beta : float
            GARCH coefficient (persistence). Must be in (0, 1).

        Notes
        -----
        If alpha + beta >= 1.0, parameters are rescaled so that
        alpha + beta = 0.95 (the stationarity boundary with margin),
        preserving the ratio alpha / beta.
        """
        if omega <= 0.0 or not math.isfinite(omega):
            raise ValueError(f"omega must be > 0, got {omega!r}.")
        if not (0.0 <= alpha < 1.0):
            raise ValueError(f"alpha must be in (0, 1), got {alpha!r}.")
        if not (0.0 < beta < 1.0):
            raise ValueError(f"beta must be in (0, 1), got {beta!r}.")

        # Enforce stationarity: alpha + beta < 1.
        if alpha + beta >= 1.0:
            scale: float = 0.95 / (alpha + beta)
            alpha = alpha * scale
            beta  = beta  * scale

        self._omega: float = omega
        self._alpha: float = alpha
        self._beta:  float = beta

        # Compute long-run variance: omega / (1 - alpha - beta)
        persistence: float = self._alpha + self._beta
        denom: float = 1.0 - persistence
        self._long_run_variance: float = max(
            _VOL_EPSILON ** 2,
            self._omega / denom,
        )

        # Initialise current variance to the long-run variance.
        self._current_variance: float = self._long_run_variance

    def xǁVolatilityTrackerǁ__init____mutmut_10(
        self,
        omega: float = _DEFAULT_OMEGA,
        alpha: float = _DEFAULT_ALPHA,
        beta: float  = _DEFAULT_BETA,
    ) -> None:
        """
        Initialise the GARCH(1,1) tracker.

        Parameters
        ----------
        omega : float
            Long-run variance component. Must be > 0.
        alpha : float
            ARCH coefficient (shock sensitivity). Must be in (0, 1).
        beta : float
            GARCH coefficient (persistence). Must be in (0, 1).

        Notes
        -----
        If alpha + beta >= 1.0, parameters are rescaled so that
        alpha + beta = 0.95 (the stationarity boundary with margin),
        preserving the ratio alpha / beta.
        """
        if omega <= 0.0 or not math.isfinite(omega):
            raise ValueError(f"omega must be > 0, got {omega!r}.")
        if not (0.0 < alpha <= 1.0):
            raise ValueError(f"alpha must be in (0, 1), got {alpha!r}.")
        if not (0.0 < beta < 1.0):
            raise ValueError(f"beta must be in (0, 1), got {beta!r}.")

        # Enforce stationarity: alpha + beta < 1.
        if alpha + beta >= 1.0:
            scale: float = 0.95 / (alpha + beta)
            alpha = alpha * scale
            beta  = beta  * scale

        self._omega: float = omega
        self._alpha: float = alpha
        self._beta:  float = beta

        # Compute long-run variance: omega / (1 - alpha - beta)
        persistence: float = self._alpha + self._beta
        denom: float = 1.0 - persistence
        self._long_run_variance: float = max(
            _VOL_EPSILON ** 2,
            self._omega / denom,
        )

        # Initialise current variance to the long-run variance.
        self._current_variance: float = self._long_run_variance

    def xǁVolatilityTrackerǁ__init____mutmut_11(
        self,
        omega: float = _DEFAULT_OMEGA,
        alpha: float = _DEFAULT_ALPHA,
        beta: float  = _DEFAULT_BETA,
    ) -> None:
        """
        Initialise the GARCH(1,1) tracker.

        Parameters
        ----------
        omega : float
            Long-run variance component. Must be > 0.
        alpha : float
            ARCH coefficient (shock sensitivity). Must be in (0, 1).
        beta : float
            GARCH coefficient (persistence). Must be in (0, 1).

        Notes
        -----
        If alpha + beta >= 1.0, parameters are rescaled so that
        alpha + beta = 0.95 (the stationarity boundary with margin),
        preserving the ratio alpha / beta.
        """
        if omega <= 0.0 or not math.isfinite(omega):
            raise ValueError(f"omega must be > 0, got {omega!r}.")
        if not (0.0 < alpha < 2.0):
            raise ValueError(f"alpha must be in (0, 1), got {alpha!r}.")
        if not (0.0 < beta < 1.0):
            raise ValueError(f"beta must be in (0, 1), got {beta!r}.")

        # Enforce stationarity: alpha + beta < 1.
        if alpha + beta >= 1.0:
            scale: float = 0.95 / (alpha + beta)
            alpha = alpha * scale
            beta  = beta  * scale

        self._omega: float = omega
        self._alpha: float = alpha
        self._beta:  float = beta

        # Compute long-run variance: omega / (1 - alpha - beta)
        persistence: float = self._alpha + self._beta
        denom: float = 1.0 - persistence
        self._long_run_variance: float = max(
            _VOL_EPSILON ** 2,
            self._omega / denom,
        )

        # Initialise current variance to the long-run variance.
        self._current_variance: float = self._long_run_variance

    def xǁVolatilityTrackerǁ__init____mutmut_12(
        self,
        omega: float = _DEFAULT_OMEGA,
        alpha: float = _DEFAULT_ALPHA,
        beta: float  = _DEFAULT_BETA,
    ) -> None:
        """
        Initialise the GARCH(1,1) tracker.

        Parameters
        ----------
        omega : float
            Long-run variance component. Must be > 0.
        alpha : float
            ARCH coefficient (shock sensitivity). Must be in (0, 1).
        beta : float
            GARCH coefficient (persistence). Must be in (0, 1).

        Notes
        -----
        If alpha + beta >= 1.0, parameters are rescaled so that
        alpha + beta = 0.95 (the stationarity boundary with margin),
        preserving the ratio alpha / beta.
        """
        if omega <= 0.0 or not math.isfinite(omega):
            raise ValueError(f"omega must be > 0, got {omega!r}.")
        if not (0.0 < alpha < 1.0):
            raise ValueError(None)
        if not (0.0 < beta < 1.0):
            raise ValueError(f"beta must be in (0, 1), got {beta!r}.")

        # Enforce stationarity: alpha + beta < 1.
        if alpha + beta >= 1.0:
            scale: float = 0.95 / (alpha + beta)
            alpha = alpha * scale
            beta  = beta  * scale

        self._omega: float = omega
        self._alpha: float = alpha
        self._beta:  float = beta

        # Compute long-run variance: omega / (1 - alpha - beta)
        persistence: float = self._alpha + self._beta
        denom: float = 1.0 - persistence
        self._long_run_variance: float = max(
            _VOL_EPSILON ** 2,
            self._omega / denom,
        )

        # Initialise current variance to the long-run variance.
        self._current_variance: float = self._long_run_variance

    def xǁVolatilityTrackerǁ__init____mutmut_13(
        self,
        omega: float = _DEFAULT_OMEGA,
        alpha: float = _DEFAULT_ALPHA,
        beta: float  = _DEFAULT_BETA,
    ) -> None:
        """
        Initialise the GARCH(1,1) tracker.

        Parameters
        ----------
        omega : float
            Long-run variance component. Must be > 0.
        alpha : float
            ARCH coefficient (shock sensitivity). Must be in (0, 1).
        beta : float
            GARCH coefficient (persistence). Must be in (0, 1).

        Notes
        -----
        If alpha + beta >= 1.0, parameters are rescaled so that
        alpha + beta = 0.95 (the stationarity boundary with margin),
        preserving the ratio alpha / beta.
        """
        if omega <= 0.0 or not math.isfinite(omega):
            raise ValueError(f"omega must be > 0, got {omega!r}.")
        if not (0.0 < alpha < 1.0):
            raise ValueError(f"alpha must be in (0, 1), got {alpha!r}.")
        if (0.0 < beta < 1.0):
            raise ValueError(f"beta must be in (0, 1), got {beta!r}.")

        # Enforce stationarity: alpha + beta < 1.
        if alpha + beta >= 1.0:
            scale: float = 0.95 / (alpha + beta)
            alpha = alpha * scale
            beta  = beta  * scale

        self._omega: float = omega
        self._alpha: float = alpha
        self._beta:  float = beta

        # Compute long-run variance: omega / (1 - alpha - beta)
        persistence: float = self._alpha + self._beta
        denom: float = 1.0 - persistence
        self._long_run_variance: float = max(
            _VOL_EPSILON ** 2,
            self._omega / denom,
        )

        # Initialise current variance to the long-run variance.
        self._current_variance: float = self._long_run_variance

    def xǁVolatilityTrackerǁ__init____mutmut_14(
        self,
        omega: float = _DEFAULT_OMEGA,
        alpha: float = _DEFAULT_ALPHA,
        beta: float  = _DEFAULT_BETA,
    ) -> None:
        """
        Initialise the GARCH(1,1) tracker.

        Parameters
        ----------
        omega : float
            Long-run variance component. Must be > 0.
        alpha : float
            ARCH coefficient (shock sensitivity). Must be in (0, 1).
        beta : float
            GARCH coefficient (persistence). Must be in (0, 1).

        Notes
        -----
        If alpha + beta >= 1.0, parameters are rescaled so that
        alpha + beta = 0.95 (the stationarity boundary with margin),
        preserving the ratio alpha / beta.
        """
        if omega <= 0.0 or not math.isfinite(omega):
            raise ValueError(f"omega must be > 0, got {omega!r}.")
        if not (0.0 < alpha < 1.0):
            raise ValueError(f"alpha must be in (0, 1), got {alpha!r}.")
        if not (1.0 < beta < 1.0):
            raise ValueError(f"beta must be in (0, 1), got {beta!r}.")

        # Enforce stationarity: alpha + beta < 1.
        if alpha + beta >= 1.0:
            scale: float = 0.95 / (alpha + beta)
            alpha = alpha * scale
            beta  = beta  * scale

        self._omega: float = omega
        self._alpha: float = alpha
        self._beta:  float = beta

        # Compute long-run variance: omega / (1 - alpha - beta)
        persistence: float = self._alpha + self._beta
        denom: float = 1.0 - persistence
        self._long_run_variance: float = max(
            _VOL_EPSILON ** 2,
            self._omega / denom,
        )

        # Initialise current variance to the long-run variance.
        self._current_variance: float = self._long_run_variance

    def xǁVolatilityTrackerǁ__init____mutmut_15(
        self,
        omega: float = _DEFAULT_OMEGA,
        alpha: float = _DEFAULT_ALPHA,
        beta: float  = _DEFAULT_BETA,
    ) -> None:
        """
        Initialise the GARCH(1,1) tracker.

        Parameters
        ----------
        omega : float
            Long-run variance component. Must be > 0.
        alpha : float
            ARCH coefficient (shock sensitivity). Must be in (0, 1).
        beta : float
            GARCH coefficient (persistence). Must be in (0, 1).

        Notes
        -----
        If alpha + beta >= 1.0, parameters are rescaled so that
        alpha + beta = 0.95 (the stationarity boundary with margin),
        preserving the ratio alpha / beta.
        """
        if omega <= 0.0 or not math.isfinite(omega):
            raise ValueError(f"omega must be > 0, got {omega!r}.")
        if not (0.0 < alpha < 1.0):
            raise ValueError(f"alpha must be in (0, 1), got {alpha!r}.")
        if not (0.0 <= beta < 1.0):
            raise ValueError(f"beta must be in (0, 1), got {beta!r}.")

        # Enforce stationarity: alpha + beta < 1.
        if alpha + beta >= 1.0:
            scale: float = 0.95 / (alpha + beta)
            alpha = alpha * scale
            beta  = beta  * scale

        self._omega: float = omega
        self._alpha: float = alpha
        self._beta:  float = beta

        # Compute long-run variance: omega / (1 - alpha - beta)
        persistence: float = self._alpha + self._beta
        denom: float = 1.0 - persistence
        self._long_run_variance: float = max(
            _VOL_EPSILON ** 2,
            self._omega / denom,
        )

        # Initialise current variance to the long-run variance.
        self._current_variance: float = self._long_run_variance

    def xǁVolatilityTrackerǁ__init____mutmut_16(
        self,
        omega: float = _DEFAULT_OMEGA,
        alpha: float = _DEFAULT_ALPHA,
        beta: float  = _DEFAULT_BETA,
    ) -> None:
        """
        Initialise the GARCH(1,1) tracker.

        Parameters
        ----------
        omega : float
            Long-run variance component. Must be > 0.
        alpha : float
            ARCH coefficient (shock sensitivity). Must be in (0, 1).
        beta : float
            GARCH coefficient (persistence). Must be in (0, 1).

        Notes
        -----
        If alpha + beta >= 1.0, parameters are rescaled so that
        alpha + beta = 0.95 (the stationarity boundary with margin),
        preserving the ratio alpha / beta.
        """
        if omega <= 0.0 or not math.isfinite(omega):
            raise ValueError(f"omega must be > 0, got {omega!r}.")
        if not (0.0 < alpha < 1.0):
            raise ValueError(f"alpha must be in (0, 1), got {alpha!r}.")
        if not (0.0 < beta <= 1.0):
            raise ValueError(f"beta must be in (0, 1), got {beta!r}.")

        # Enforce stationarity: alpha + beta < 1.
        if alpha + beta >= 1.0:
            scale: float = 0.95 / (alpha + beta)
            alpha = alpha * scale
            beta  = beta  * scale

        self._omega: float = omega
        self._alpha: float = alpha
        self._beta:  float = beta

        # Compute long-run variance: omega / (1 - alpha - beta)
        persistence: float = self._alpha + self._beta
        denom: float = 1.0 - persistence
        self._long_run_variance: float = max(
            _VOL_EPSILON ** 2,
            self._omega / denom,
        )

        # Initialise current variance to the long-run variance.
        self._current_variance: float = self._long_run_variance

    def xǁVolatilityTrackerǁ__init____mutmut_17(
        self,
        omega: float = _DEFAULT_OMEGA,
        alpha: float = _DEFAULT_ALPHA,
        beta: float  = _DEFAULT_BETA,
    ) -> None:
        """
        Initialise the GARCH(1,1) tracker.

        Parameters
        ----------
        omega : float
            Long-run variance component. Must be > 0.
        alpha : float
            ARCH coefficient (shock sensitivity). Must be in (0, 1).
        beta : float
            GARCH coefficient (persistence). Must be in (0, 1).

        Notes
        -----
        If alpha + beta >= 1.0, parameters are rescaled so that
        alpha + beta = 0.95 (the stationarity boundary with margin),
        preserving the ratio alpha / beta.
        """
        if omega <= 0.0 or not math.isfinite(omega):
            raise ValueError(f"omega must be > 0, got {omega!r}.")
        if not (0.0 < alpha < 1.0):
            raise ValueError(f"alpha must be in (0, 1), got {alpha!r}.")
        if not (0.0 < beta < 2.0):
            raise ValueError(f"beta must be in (0, 1), got {beta!r}.")

        # Enforce stationarity: alpha + beta < 1.
        if alpha + beta >= 1.0:
            scale: float = 0.95 / (alpha + beta)
            alpha = alpha * scale
            beta  = beta  * scale

        self._omega: float = omega
        self._alpha: float = alpha
        self._beta:  float = beta

        # Compute long-run variance: omega / (1 - alpha - beta)
        persistence: float = self._alpha + self._beta
        denom: float = 1.0 - persistence
        self._long_run_variance: float = max(
            _VOL_EPSILON ** 2,
            self._omega / denom,
        )

        # Initialise current variance to the long-run variance.
        self._current_variance: float = self._long_run_variance

    def xǁVolatilityTrackerǁ__init____mutmut_18(
        self,
        omega: float = _DEFAULT_OMEGA,
        alpha: float = _DEFAULT_ALPHA,
        beta: float  = _DEFAULT_BETA,
    ) -> None:
        """
        Initialise the GARCH(1,1) tracker.

        Parameters
        ----------
        omega : float
            Long-run variance component. Must be > 0.
        alpha : float
            ARCH coefficient (shock sensitivity). Must be in (0, 1).
        beta : float
            GARCH coefficient (persistence). Must be in (0, 1).

        Notes
        -----
        If alpha + beta >= 1.0, parameters are rescaled so that
        alpha + beta = 0.95 (the stationarity boundary with margin),
        preserving the ratio alpha / beta.
        """
        if omega <= 0.0 or not math.isfinite(omega):
            raise ValueError(f"omega must be > 0, got {omega!r}.")
        if not (0.0 < alpha < 1.0):
            raise ValueError(f"alpha must be in (0, 1), got {alpha!r}.")
        if not (0.0 < beta < 1.0):
            raise ValueError(None)

        # Enforce stationarity: alpha + beta < 1.
        if alpha + beta >= 1.0:
            scale: float = 0.95 / (alpha + beta)
            alpha = alpha * scale
            beta  = beta  * scale

        self._omega: float = omega
        self._alpha: float = alpha
        self._beta:  float = beta

        # Compute long-run variance: omega / (1 - alpha - beta)
        persistence: float = self._alpha + self._beta
        denom: float = 1.0 - persistence
        self._long_run_variance: float = max(
            _VOL_EPSILON ** 2,
            self._omega / denom,
        )

        # Initialise current variance to the long-run variance.
        self._current_variance: float = self._long_run_variance

    def xǁVolatilityTrackerǁ__init____mutmut_19(
        self,
        omega: float = _DEFAULT_OMEGA,
        alpha: float = _DEFAULT_ALPHA,
        beta: float  = _DEFAULT_BETA,
    ) -> None:
        """
        Initialise the GARCH(1,1) tracker.

        Parameters
        ----------
        omega : float
            Long-run variance component. Must be > 0.
        alpha : float
            ARCH coefficient (shock sensitivity). Must be in (0, 1).
        beta : float
            GARCH coefficient (persistence). Must be in (0, 1).

        Notes
        -----
        If alpha + beta >= 1.0, parameters are rescaled so that
        alpha + beta = 0.95 (the stationarity boundary with margin),
        preserving the ratio alpha / beta.
        """
        if omega <= 0.0 or not math.isfinite(omega):
            raise ValueError(f"omega must be > 0, got {omega!r}.")
        if not (0.0 < alpha < 1.0):
            raise ValueError(f"alpha must be in (0, 1), got {alpha!r}.")
        if not (0.0 < beta < 1.0):
            raise ValueError(f"beta must be in (0, 1), got {beta!r}.")

        # Enforce stationarity: alpha + beta < 1.
        if alpha - beta >= 1.0:
            scale: float = 0.95 / (alpha + beta)
            alpha = alpha * scale
            beta  = beta  * scale

        self._omega: float = omega
        self._alpha: float = alpha
        self._beta:  float = beta

        # Compute long-run variance: omega / (1 - alpha - beta)
        persistence: float = self._alpha + self._beta
        denom: float = 1.0 - persistence
        self._long_run_variance: float = max(
            _VOL_EPSILON ** 2,
            self._omega / denom,
        )

        # Initialise current variance to the long-run variance.
        self._current_variance: float = self._long_run_variance

    def xǁVolatilityTrackerǁ__init____mutmut_20(
        self,
        omega: float = _DEFAULT_OMEGA,
        alpha: float = _DEFAULT_ALPHA,
        beta: float  = _DEFAULT_BETA,
    ) -> None:
        """
        Initialise the GARCH(1,1) tracker.

        Parameters
        ----------
        omega : float
            Long-run variance component. Must be > 0.
        alpha : float
            ARCH coefficient (shock sensitivity). Must be in (0, 1).
        beta : float
            GARCH coefficient (persistence). Must be in (0, 1).

        Notes
        -----
        If alpha + beta >= 1.0, parameters are rescaled so that
        alpha + beta = 0.95 (the stationarity boundary with margin),
        preserving the ratio alpha / beta.
        """
        if omega <= 0.0 or not math.isfinite(omega):
            raise ValueError(f"omega must be > 0, got {omega!r}.")
        if not (0.0 < alpha < 1.0):
            raise ValueError(f"alpha must be in (0, 1), got {alpha!r}.")
        if not (0.0 < beta < 1.0):
            raise ValueError(f"beta must be in (0, 1), got {beta!r}.")

        # Enforce stationarity: alpha + beta < 1.
        if alpha + beta > 1.0:
            scale: float = 0.95 / (alpha + beta)
            alpha = alpha * scale
            beta  = beta  * scale

        self._omega: float = omega
        self._alpha: float = alpha
        self._beta:  float = beta

        # Compute long-run variance: omega / (1 - alpha - beta)
        persistence: float = self._alpha + self._beta
        denom: float = 1.0 - persistence
        self._long_run_variance: float = max(
            _VOL_EPSILON ** 2,
            self._omega / denom,
        )

        # Initialise current variance to the long-run variance.
        self._current_variance: float = self._long_run_variance

    def xǁVolatilityTrackerǁ__init____mutmut_21(
        self,
        omega: float = _DEFAULT_OMEGA,
        alpha: float = _DEFAULT_ALPHA,
        beta: float  = _DEFAULT_BETA,
    ) -> None:
        """
        Initialise the GARCH(1,1) tracker.

        Parameters
        ----------
        omega : float
            Long-run variance component. Must be > 0.
        alpha : float
            ARCH coefficient (shock sensitivity). Must be in (0, 1).
        beta : float
            GARCH coefficient (persistence). Must be in (0, 1).

        Notes
        -----
        If alpha + beta >= 1.0, parameters are rescaled so that
        alpha + beta = 0.95 (the stationarity boundary with margin),
        preserving the ratio alpha / beta.
        """
        if omega <= 0.0 or not math.isfinite(omega):
            raise ValueError(f"omega must be > 0, got {omega!r}.")
        if not (0.0 < alpha < 1.0):
            raise ValueError(f"alpha must be in (0, 1), got {alpha!r}.")
        if not (0.0 < beta < 1.0):
            raise ValueError(f"beta must be in (0, 1), got {beta!r}.")

        # Enforce stationarity: alpha + beta < 1.
        if alpha + beta >= 2.0:
            scale: float = 0.95 / (alpha + beta)
            alpha = alpha * scale
            beta  = beta  * scale

        self._omega: float = omega
        self._alpha: float = alpha
        self._beta:  float = beta

        # Compute long-run variance: omega / (1 - alpha - beta)
        persistence: float = self._alpha + self._beta
        denom: float = 1.0 - persistence
        self._long_run_variance: float = max(
            _VOL_EPSILON ** 2,
            self._omega / denom,
        )

        # Initialise current variance to the long-run variance.
        self._current_variance: float = self._long_run_variance

    def xǁVolatilityTrackerǁ__init____mutmut_22(
        self,
        omega: float = _DEFAULT_OMEGA,
        alpha: float = _DEFAULT_ALPHA,
        beta: float  = _DEFAULT_BETA,
    ) -> None:
        """
        Initialise the GARCH(1,1) tracker.

        Parameters
        ----------
        omega : float
            Long-run variance component. Must be > 0.
        alpha : float
            ARCH coefficient (shock sensitivity). Must be in (0, 1).
        beta : float
            GARCH coefficient (persistence). Must be in (0, 1).

        Notes
        -----
        If alpha + beta >= 1.0, parameters are rescaled so that
        alpha + beta = 0.95 (the stationarity boundary with margin),
        preserving the ratio alpha / beta.
        """
        if omega <= 0.0 or not math.isfinite(omega):
            raise ValueError(f"omega must be > 0, got {omega!r}.")
        if not (0.0 < alpha < 1.0):
            raise ValueError(f"alpha must be in (0, 1), got {alpha!r}.")
        if not (0.0 < beta < 1.0):
            raise ValueError(f"beta must be in (0, 1), got {beta!r}.")

        # Enforce stationarity: alpha + beta < 1.
        if alpha + beta >= 1.0:
            scale: float = None
            alpha = alpha * scale
            beta  = beta  * scale

        self._omega: float = omega
        self._alpha: float = alpha
        self._beta:  float = beta

        # Compute long-run variance: omega / (1 - alpha - beta)
        persistence: float = self._alpha + self._beta
        denom: float = 1.0 - persistence
        self._long_run_variance: float = max(
            _VOL_EPSILON ** 2,
            self._omega / denom,
        )

        # Initialise current variance to the long-run variance.
        self._current_variance: float = self._long_run_variance

    def xǁVolatilityTrackerǁ__init____mutmut_23(
        self,
        omega: float = _DEFAULT_OMEGA,
        alpha: float = _DEFAULT_ALPHA,
        beta: float  = _DEFAULT_BETA,
    ) -> None:
        """
        Initialise the GARCH(1,1) tracker.

        Parameters
        ----------
        omega : float
            Long-run variance component. Must be > 0.
        alpha : float
            ARCH coefficient (shock sensitivity). Must be in (0, 1).
        beta : float
            GARCH coefficient (persistence). Must be in (0, 1).

        Notes
        -----
        If alpha + beta >= 1.0, parameters are rescaled so that
        alpha + beta = 0.95 (the stationarity boundary with margin),
        preserving the ratio alpha / beta.
        """
        if omega <= 0.0 or not math.isfinite(omega):
            raise ValueError(f"omega must be > 0, got {omega!r}.")
        if not (0.0 < alpha < 1.0):
            raise ValueError(f"alpha must be in (0, 1), got {alpha!r}.")
        if not (0.0 < beta < 1.0):
            raise ValueError(f"beta must be in (0, 1), got {beta!r}.")

        # Enforce stationarity: alpha + beta < 1.
        if alpha + beta >= 1.0:
            scale: float = 0.95 * (alpha + beta)
            alpha = alpha * scale
            beta  = beta  * scale

        self._omega: float = omega
        self._alpha: float = alpha
        self._beta:  float = beta

        # Compute long-run variance: omega / (1 - alpha - beta)
        persistence: float = self._alpha + self._beta
        denom: float = 1.0 - persistence
        self._long_run_variance: float = max(
            _VOL_EPSILON ** 2,
            self._omega / denom,
        )

        # Initialise current variance to the long-run variance.
        self._current_variance: float = self._long_run_variance

    def xǁVolatilityTrackerǁ__init____mutmut_24(
        self,
        omega: float = _DEFAULT_OMEGA,
        alpha: float = _DEFAULT_ALPHA,
        beta: float  = _DEFAULT_BETA,
    ) -> None:
        """
        Initialise the GARCH(1,1) tracker.

        Parameters
        ----------
        omega : float
            Long-run variance component. Must be > 0.
        alpha : float
            ARCH coefficient (shock sensitivity). Must be in (0, 1).
        beta : float
            GARCH coefficient (persistence). Must be in (0, 1).

        Notes
        -----
        If alpha + beta >= 1.0, parameters are rescaled so that
        alpha + beta = 0.95 (the stationarity boundary with margin),
        preserving the ratio alpha / beta.
        """
        if omega <= 0.0 or not math.isfinite(omega):
            raise ValueError(f"omega must be > 0, got {omega!r}.")
        if not (0.0 < alpha < 1.0):
            raise ValueError(f"alpha must be in (0, 1), got {alpha!r}.")
        if not (0.0 < beta < 1.0):
            raise ValueError(f"beta must be in (0, 1), got {beta!r}.")

        # Enforce stationarity: alpha + beta < 1.
        if alpha + beta >= 1.0:
            scale: float = 1.95 / (alpha + beta)
            alpha = alpha * scale
            beta  = beta  * scale

        self._omega: float = omega
        self._alpha: float = alpha
        self._beta:  float = beta

        # Compute long-run variance: omega / (1 - alpha - beta)
        persistence: float = self._alpha + self._beta
        denom: float = 1.0 - persistence
        self._long_run_variance: float = max(
            _VOL_EPSILON ** 2,
            self._omega / denom,
        )

        # Initialise current variance to the long-run variance.
        self._current_variance: float = self._long_run_variance

    def xǁVolatilityTrackerǁ__init____mutmut_25(
        self,
        omega: float = _DEFAULT_OMEGA,
        alpha: float = _DEFAULT_ALPHA,
        beta: float  = _DEFAULT_BETA,
    ) -> None:
        """
        Initialise the GARCH(1,1) tracker.

        Parameters
        ----------
        omega : float
            Long-run variance component. Must be > 0.
        alpha : float
            ARCH coefficient (shock sensitivity). Must be in (0, 1).
        beta : float
            GARCH coefficient (persistence). Must be in (0, 1).

        Notes
        -----
        If alpha + beta >= 1.0, parameters are rescaled so that
        alpha + beta = 0.95 (the stationarity boundary with margin),
        preserving the ratio alpha / beta.
        """
        if omega <= 0.0 or not math.isfinite(omega):
            raise ValueError(f"omega must be > 0, got {omega!r}.")
        if not (0.0 < alpha < 1.0):
            raise ValueError(f"alpha must be in (0, 1), got {alpha!r}.")
        if not (0.0 < beta < 1.0):
            raise ValueError(f"beta must be in (0, 1), got {beta!r}.")

        # Enforce stationarity: alpha + beta < 1.
        if alpha + beta >= 1.0:
            scale: float = 0.95 / (alpha - beta)
            alpha = alpha * scale
            beta  = beta  * scale

        self._omega: float = omega
        self._alpha: float = alpha
        self._beta:  float = beta

        # Compute long-run variance: omega / (1 - alpha - beta)
        persistence: float = self._alpha + self._beta
        denom: float = 1.0 - persistence
        self._long_run_variance: float = max(
            _VOL_EPSILON ** 2,
            self._omega / denom,
        )

        # Initialise current variance to the long-run variance.
        self._current_variance: float = self._long_run_variance

    def xǁVolatilityTrackerǁ__init____mutmut_26(
        self,
        omega: float = _DEFAULT_OMEGA,
        alpha: float = _DEFAULT_ALPHA,
        beta: float  = _DEFAULT_BETA,
    ) -> None:
        """
        Initialise the GARCH(1,1) tracker.

        Parameters
        ----------
        omega : float
            Long-run variance component. Must be > 0.
        alpha : float
            ARCH coefficient (shock sensitivity). Must be in (0, 1).
        beta : float
            GARCH coefficient (persistence). Must be in (0, 1).

        Notes
        -----
        If alpha + beta >= 1.0, parameters are rescaled so that
        alpha + beta = 0.95 (the stationarity boundary with margin),
        preserving the ratio alpha / beta.
        """
        if omega <= 0.0 or not math.isfinite(omega):
            raise ValueError(f"omega must be > 0, got {omega!r}.")
        if not (0.0 < alpha < 1.0):
            raise ValueError(f"alpha must be in (0, 1), got {alpha!r}.")
        if not (0.0 < beta < 1.0):
            raise ValueError(f"beta must be in (0, 1), got {beta!r}.")

        # Enforce stationarity: alpha + beta < 1.
        if alpha + beta >= 1.0:
            scale: float = 0.95 / (alpha + beta)
            alpha = None
            beta  = beta  * scale

        self._omega: float = omega
        self._alpha: float = alpha
        self._beta:  float = beta

        # Compute long-run variance: omega / (1 - alpha - beta)
        persistence: float = self._alpha + self._beta
        denom: float = 1.0 - persistence
        self._long_run_variance: float = max(
            _VOL_EPSILON ** 2,
            self._omega / denom,
        )

        # Initialise current variance to the long-run variance.
        self._current_variance: float = self._long_run_variance

    def xǁVolatilityTrackerǁ__init____mutmut_27(
        self,
        omega: float = _DEFAULT_OMEGA,
        alpha: float = _DEFAULT_ALPHA,
        beta: float  = _DEFAULT_BETA,
    ) -> None:
        """
        Initialise the GARCH(1,1) tracker.

        Parameters
        ----------
        omega : float
            Long-run variance component. Must be > 0.
        alpha : float
            ARCH coefficient (shock sensitivity). Must be in (0, 1).
        beta : float
            GARCH coefficient (persistence). Must be in (0, 1).

        Notes
        -----
        If alpha + beta >= 1.0, parameters are rescaled so that
        alpha + beta = 0.95 (the stationarity boundary with margin),
        preserving the ratio alpha / beta.
        """
        if omega <= 0.0 or not math.isfinite(omega):
            raise ValueError(f"omega must be > 0, got {omega!r}.")
        if not (0.0 < alpha < 1.0):
            raise ValueError(f"alpha must be in (0, 1), got {alpha!r}.")
        if not (0.0 < beta < 1.0):
            raise ValueError(f"beta must be in (0, 1), got {beta!r}.")

        # Enforce stationarity: alpha + beta < 1.
        if alpha + beta >= 1.0:
            scale: float = 0.95 / (alpha + beta)
            alpha = alpha / scale
            beta  = beta  * scale

        self._omega: float = omega
        self._alpha: float = alpha
        self._beta:  float = beta

        # Compute long-run variance: omega / (1 - alpha - beta)
        persistence: float = self._alpha + self._beta
        denom: float = 1.0 - persistence
        self._long_run_variance: float = max(
            _VOL_EPSILON ** 2,
            self._omega / denom,
        )

        # Initialise current variance to the long-run variance.
        self._current_variance: float = self._long_run_variance

    def xǁVolatilityTrackerǁ__init____mutmut_28(
        self,
        omega: float = _DEFAULT_OMEGA,
        alpha: float = _DEFAULT_ALPHA,
        beta: float  = _DEFAULT_BETA,
    ) -> None:
        """
        Initialise the GARCH(1,1) tracker.

        Parameters
        ----------
        omega : float
            Long-run variance component. Must be > 0.
        alpha : float
            ARCH coefficient (shock sensitivity). Must be in (0, 1).
        beta : float
            GARCH coefficient (persistence). Must be in (0, 1).

        Notes
        -----
        If alpha + beta >= 1.0, parameters are rescaled so that
        alpha + beta = 0.95 (the stationarity boundary with margin),
        preserving the ratio alpha / beta.
        """
        if omega <= 0.0 or not math.isfinite(omega):
            raise ValueError(f"omega must be > 0, got {omega!r}.")
        if not (0.0 < alpha < 1.0):
            raise ValueError(f"alpha must be in (0, 1), got {alpha!r}.")
        if not (0.0 < beta < 1.0):
            raise ValueError(f"beta must be in (0, 1), got {beta!r}.")

        # Enforce stationarity: alpha + beta < 1.
        if alpha + beta >= 1.0:
            scale: float = 0.95 / (alpha + beta)
            alpha = alpha * scale
            beta  = None

        self._omega: float = omega
        self._alpha: float = alpha
        self._beta:  float = beta

        # Compute long-run variance: omega / (1 - alpha - beta)
        persistence: float = self._alpha + self._beta
        denom: float = 1.0 - persistence
        self._long_run_variance: float = max(
            _VOL_EPSILON ** 2,
            self._omega / denom,
        )

        # Initialise current variance to the long-run variance.
        self._current_variance: float = self._long_run_variance

    def xǁVolatilityTrackerǁ__init____mutmut_29(
        self,
        omega: float = _DEFAULT_OMEGA,
        alpha: float = _DEFAULT_ALPHA,
        beta: float  = _DEFAULT_BETA,
    ) -> None:
        """
        Initialise the GARCH(1,1) tracker.

        Parameters
        ----------
        omega : float
            Long-run variance component. Must be > 0.
        alpha : float
            ARCH coefficient (shock sensitivity). Must be in (0, 1).
        beta : float
            GARCH coefficient (persistence). Must be in (0, 1).

        Notes
        -----
        If alpha + beta >= 1.0, parameters are rescaled so that
        alpha + beta = 0.95 (the stationarity boundary with margin),
        preserving the ratio alpha / beta.
        """
        if omega <= 0.0 or not math.isfinite(omega):
            raise ValueError(f"omega must be > 0, got {omega!r}.")
        if not (0.0 < alpha < 1.0):
            raise ValueError(f"alpha must be in (0, 1), got {alpha!r}.")
        if not (0.0 < beta < 1.0):
            raise ValueError(f"beta must be in (0, 1), got {beta!r}.")

        # Enforce stationarity: alpha + beta < 1.
        if alpha + beta >= 1.0:
            scale: float = 0.95 / (alpha + beta)
            alpha = alpha * scale
            beta  = beta / scale

        self._omega: float = omega
        self._alpha: float = alpha
        self._beta:  float = beta

        # Compute long-run variance: omega / (1 - alpha - beta)
        persistence: float = self._alpha + self._beta
        denom: float = 1.0 - persistence
        self._long_run_variance: float = max(
            _VOL_EPSILON ** 2,
            self._omega / denom,
        )

        # Initialise current variance to the long-run variance.
        self._current_variance: float = self._long_run_variance

    def xǁVolatilityTrackerǁ__init____mutmut_30(
        self,
        omega: float = _DEFAULT_OMEGA,
        alpha: float = _DEFAULT_ALPHA,
        beta: float  = _DEFAULT_BETA,
    ) -> None:
        """
        Initialise the GARCH(1,1) tracker.

        Parameters
        ----------
        omega : float
            Long-run variance component. Must be > 0.
        alpha : float
            ARCH coefficient (shock sensitivity). Must be in (0, 1).
        beta : float
            GARCH coefficient (persistence). Must be in (0, 1).

        Notes
        -----
        If alpha + beta >= 1.0, parameters are rescaled so that
        alpha + beta = 0.95 (the stationarity boundary with margin),
        preserving the ratio alpha / beta.
        """
        if omega <= 0.0 or not math.isfinite(omega):
            raise ValueError(f"omega must be > 0, got {omega!r}.")
        if not (0.0 < alpha < 1.0):
            raise ValueError(f"alpha must be in (0, 1), got {alpha!r}.")
        if not (0.0 < beta < 1.0):
            raise ValueError(f"beta must be in (0, 1), got {beta!r}.")

        # Enforce stationarity: alpha + beta < 1.
        if alpha + beta >= 1.0:
            scale: float = 0.95 / (alpha + beta)
            alpha = alpha * scale
            beta  = beta  * scale

        self._omega: float = None
        self._alpha: float = alpha
        self._beta:  float = beta

        # Compute long-run variance: omega / (1 - alpha - beta)
        persistence: float = self._alpha + self._beta
        denom: float = 1.0 - persistence
        self._long_run_variance: float = max(
            _VOL_EPSILON ** 2,
            self._omega / denom,
        )

        # Initialise current variance to the long-run variance.
        self._current_variance: float = self._long_run_variance

    def xǁVolatilityTrackerǁ__init____mutmut_31(
        self,
        omega: float = _DEFAULT_OMEGA,
        alpha: float = _DEFAULT_ALPHA,
        beta: float  = _DEFAULT_BETA,
    ) -> None:
        """
        Initialise the GARCH(1,1) tracker.

        Parameters
        ----------
        omega : float
            Long-run variance component. Must be > 0.
        alpha : float
            ARCH coefficient (shock sensitivity). Must be in (0, 1).
        beta : float
            GARCH coefficient (persistence). Must be in (0, 1).

        Notes
        -----
        If alpha + beta >= 1.0, parameters are rescaled so that
        alpha + beta = 0.95 (the stationarity boundary with margin),
        preserving the ratio alpha / beta.
        """
        if omega <= 0.0 or not math.isfinite(omega):
            raise ValueError(f"omega must be > 0, got {omega!r}.")
        if not (0.0 < alpha < 1.0):
            raise ValueError(f"alpha must be in (0, 1), got {alpha!r}.")
        if not (0.0 < beta < 1.0):
            raise ValueError(f"beta must be in (0, 1), got {beta!r}.")

        # Enforce stationarity: alpha + beta < 1.
        if alpha + beta >= 1.0:
            scale: float = 0.95 / (alpha + beta)
            alpha = alpha * scale
            beta  = beta  * scale

        self._omega: float = omega
        self._alpha: float = None
        self._beta:  float = beta

        # Compute long-run variance: omega / (1 - alpha - beta)
        persistence: float = self._alpha + self._beta
        denom: float = 1.0 - persistence
        self._long_run_variance: float = max(
            _VOL_EPSILON ** 2,
            self._omega / denom,
        )

        # Initialise current variance to the long-run variance.
        self._current_variance: float = self._long_run_variance

    def xǁVolatilityTrackerǁ__init____mutmut_32(
        self,
        omega: float = _DEFAULT_OMEGA,
        alpha: float = _DEFAULT_ALPHA,
        beta: float  = _DEFAULT_BETA,
    ) -> None:
        """
        Initialise the GARCH(1,1) tracker.

        Parameters
        ----------
        omega : float
            Long-run variance component. Must be > 0.
        alpha : float
            ARCH coefficient (shock sensitivity). Must be in (0, 1).
        beta : float
            GARCH coefficient (persistence). Must be in (0, 1).

        Notes
        -----
        If alpha + beta >= 1.0, parameters are rescaled so that
        alpha + beta = 0.95 (the stationarity boundary with margin),
        preserving the ratio alpha / beta.
        """
        if omega <= 0.0 or not math.isfinite(omega):
            raise ValueError(f"omega must be > 0, got {omega!r}.")
        if not (0.0 < alpha < 1.0):
            raise ValueError(f"alpha must be in (0, 1), got {alpha!r}.")
        if not (0.0 < beta < 1.0):
            raise ValueError(f"beta must be in (0, 1), got {beta!r}.")

        # Enforce stationarity: alpha + beta < 1.
        if alpha + beta >= 1.0:
            scale: float = 0.95 / (alpha + beta)
            alpha = alpha * scale
            beta  = beta  * scale

        self._omega: float = omega
        self._alpha: float = alpha
        self._beta:  float = None

        # Compute long-run variance: omega / (1 - alpha - beta)
        persistence: float = self._alpha + self._beta
        denom: float = 1.0 - persistence
        self._long_run_variance: float = max(
            _VOL_EPSILON ** 2,
            self._omega / denom,
        )

        # Initialise current variance to the long-run variance.
        self._current_variance: float = self._long_run_variance

    def xǁVolatilityTrackerǁ__init____mutmut_33(
        self,
        omega: float = _DEFAULT_OMEGA,
        alpha: float = _DEFAULT_ALPHA,
        beta: float  = _DEFAULT_BETA,
    ) -> None:
        """
        Initialise the GARCH(1,1) tracker.

        Parameters
        ----------
        omega : float
            Long-run variance component. Must be > 0.
        alpha : float
            ARCH coefficient (shock sensitivity). Must be in (0, 1).
        beta : float
            GARCH coefficient (persistence). Must be in (0, 1).

        Notes
        -----
        If alpha + beta >= 1.0, parameters are rescaled so that
        alpha + beta = 0.95 (the stationarity boundary with margin),
        preserving the ratio alpha / beta.
        """
        if omega <= 0.0 or not math.isfinite(omega):
            raise ValueError(f"omega must be > 0, got {omega!r}.")
        if not (0.0 < alpha < 1.0):
            raise ValueError(f"alpha must be in (0, 1), got {alpha!r}.")
        if not (0.0 < beta < 1.0):
            raise ValueError(f"beta must be in (0, 1), got {beta!r}.")

        # Enforce stationarity: alpha + beta < 1.
        if alpha + beta >= 1.0:
            scale: float = 0.95 / (alpha + beta)
            alpha = alpha * scale
            beta  = beta  * scale

        self._omega: float = omega
        self._alpha: float = alpha
        self._beta:  float = beta

        # Compute long-run variance: omega / (1 - alpha - beta)
        persistence: float = None
        denom: float = 1.0 - persistence
        self._long_run_variance: float = max(
            _VOL_EPSILON ** 2,
            self._omega / denom,
        )

        # Initialise current variance to the long-run variance.
        self._current_variance: float = self._long_run_variance

    def xǁVolatilityTrackerǁ__init____mutmut_34(
        self,
        omega: float = _DEFAULT_OMEGA,
        alpha: float = _DEFAULT_ALPHA,
        beta: float  = _DEFAULT_BETA,
    ) -> None:
        """
        Initialise the GARCH(1,1) tracker.

        Parameters
        ----------
        omega : float
            Long-run variance component. Must be > 0.
        alpha : float
            ARCH coefficient (shock sensitivity). Must be in (0, 1).
        beta : float
            GARCH coefficient (persistence). Must be in (0, 1).

        Notes
        -----
        If alpha + beta >= 1.0, parameters are rescaled so that
        alpha + beta = 0.95 (the stationarity boundary with margin),
        preserving the ratio alpha / beta.
        """
        if omega <= 0.0 or not math.isfinite(omega):
            raise ValueError(f"omega must be > 0, got {omega!r}.")
        if not (0.0 < alpha < 1.0):
            raise ValueError(f"alpha must be in (0, 1), got {alpha!r}.")
        if not (0.0 < beta < 1.0):
            raise ValueError(f"beta must be in (0, 1), got {beta!r}.")

        # Enforce stationarity: alpha + beta < 1.
        if alpha + beta >= 1.0:
            scale: float = 0.95 / (alpha + beta)
            alpha = alpha * scale
            beta  = beta  * scale

        self._omega: float = omega
        self._alpha: float = alpha
        self._beta:  float = beta

        # Compute long-run variance: omega / (1 - alpha - beta)
        persistence: float = self._alpha - self._beta
        denom: float = 1.0 - persistence
        self._long_run_variance: float = max(
            _VOL_EPSILON ** 2,
            self._omega / denom,
        )

        # Initialise current variance to the long-run variance.
        self._current_variance: float = self._long_run_variance

    def xǁVolatilityTrackerǁ__init____mutmut_35(
        self,
        omega: float = _DEFAULT_OMEGA,
        alpha: float = _DEFAULT_ALPHA,
        beta: float  = _DEFAULT_BETA,
    ) -> None:
        """
        Initialise the GARCH(1,1) tracker.

        Parameters
        ----------
        omega : float
            Long-run variance component. Must be > 0.
        alpha : float
            ARCH coefficient (shock sensitivity). Must be in (0, 1).
        beta : float
            GARCH coefficient (persistence). Must be in (0, 1).

        Notes
        -----
        If alpha + beta >= 1.0, parameters are rescaled so that
        alpha + beta = 0.95 (the stationarity boundary with margin),
        preserving the ratio alpha / beta.
        """
        if omega <= 0.0 or not math.isfinite(omega):
            raise ValueError(f"omega must be > 0, got {omega!r}.")
        if not (0.0 < alpha < 1.0):
            raise ValueError(f"alpha must be in (0, 1), got {alpha!r}.")
        if not (0.0 < beta < 1.0):
            raise ValueError(f"beta must be in (0, 1), got {beta!r}.")

        # Enforce stationarity: alpha + beta < 1.
        if alpha + beta >= 1.0:
            scale: float = 0.95 / (alpha + beta)
            alpha = alpha * scale
            beta  = beta  * scale

        self._omega: float = omega
        self._alpha: float = alpha
        self._beta:  float = beta

        # Compute long-run variance: omega / (1 - alpha - beta)
        persistence: float = self._alpha + self._beta
        denom: float = None
        self._long_run_variance: float = max(
            _VOL_EPSILON ** 2,
            self._omega / denom,
        )

        # Initialise current variance to the long-run variance.
        self._current_variance: float = self._long_run_variance

    def xǁVolatilityTrackerǁ__init____mutmut_36(
        self,
        omega: float = _DEFAULT_OMEGA,
        alpha: float = _DEFAULT_ALPHA,
        beta: float  = _DEFAULT_BETA,
    ) -> None:
        """
        Initialise the GARCH(1,1) tracker.

        Parameters
        ----------
        omega : float
            Long-run variance component. Must be > 0.
        alpha : float
            ARCH coefficient (shock sensitivity). Must be in (0, 1).
        beta : float
            GARCH coefficient (persistence). Must be in (0, 1).

        Notes
        -----
        If alpha + beta >= 1.0, parameters are rescaled so that
        alpha + beta = 0.95 (the stationarity boundary with margin),
        preserving the ratio alpha / beta.
        """
        if omega <= 0.0 or not math.isfinite(omega):
            raise ValueError(f"omega must be > 0, got {omega!r}.")
        if not (0.0 < alpha < 1.0):
            raise ValueError(f"alpha must be in (0, 1), got {alpha!r}.")
        if not (0.0 < beta < 1.0):
            raise ValueError(f"beta must be in (0, 1), got {beta!r}.")

        # Enforce stationarity: alpha + beta < 1.
        if alpha + beta >= 1.0:
            scale: float = 0.95 / (alpha + beta)
            alpha = alpha * scale
            beta  = beta  * scale

        self._omega: float = omega
        self._alpha: float = alpha
        self._beta:  float = beta

        # Compute long-run variance: omega / (1 - alpha - beta)
        persistence: float = self._alpha + self._beta
        denom: float = 1.0 + persistence
        self._long_run_variance: float = max(
            _VOL_EPSILON ** 2,
            self._omega / denom,
        )

        # Initialise current variance to the long-run variance.
        self._current_variance: float = self._long_run_variance

    def xǁVolatilityTrackerǁ__init____mutmut_37(
        self,
        omega: float = _DEFAULT_OMEGA,
        alpha: float = _DEFAULT_ALPHA,
        beta: float  = _DEFAULT_BETA,
    ) -> None:
        """
        Initialise the GARCH(1,1) tracker.

        Parameters
        ----------
        omega : float
            Long-run variance component. Must be > 0.
        alpha : float
            ARCH coefficient (shock sensitivity). Must be in (0, 1).
        beta : float
            GARCH coefficient (persistence). Must be in (0, 1).

        Notes
        -----
        If alpha + beta >= 1.0, parameters are rescaled so that
        alpha + beta = 0.95 (the stationarity boundary with margin),
        preserving the ratio alpha / beta.
        """
        if omega <= 0.0 or not math.isfinite(omega):
            raise ValueError(f"omega must be > 0, got {omega!r}.")
        if not (0.0 < alpha < 1.0):
            raise ValueError(f"alpha must be in (0, 1), got {alpha!r}.")
        if not (0.0 < beta < 1.0):
            raise ValueError(f"beta must be in (0, 1), got {beta!r}.")

        # Enforce stationarity: alpha + beta < 1.
        if alpha + beta >= 1.0:
            scale: float = 0.95 / (alpha + beta)
            alpha = alpha * scale
            beta  = beta  * scale

        self._omega: float = omega
        self._alpha: float = alpha
        self._beta:  float = beta

        # Compute long-run variance: omega / (1 - alpha - beta)
        persistence: float = self._alpha + self._beta
        denom: float = 2.0 - persistence
        self._long_run_variance: float = max(
            _VOL_EPSILON ** 2,
            self._omega / denom,
        )

        # Initialise current variance to the long-run variance.
        self._current_variance: float = self._long_run_variance

    def xǁVolatilityTrackerǁ__init____mutmut_38(
        self,
        omega: float = _DEFAULT_OMEGA,
        alpha: float = _DEFAULT_ALPHA,
        beta: float  = _DEFAULT_BETA,
    ) -> None:
        """
        Initialise the GARCH(1,1) tracker.

        Parameters
        ----------
        omega : float
            Long-run variance component. Must be > 0.
        alpha : float
            ARCH coefficient (shock sensitivity). Must be in (0, 1).
        beta : float
            GARCH coefficient (persistence). Must be in (0, 1).

        Notes
        -----
        If alpha + beta >= 1.0, parameters are rescaled so that
        alpha + beta = 0.95 (the stationarity boundary with margin),
        preserving the ratio alpha / beta.
        """
        if omega <= 0.0 or not math.isfinite(omega):
            raise ValueError(f"omega must be > 0, got {omega!r}.")
        if not (0.0 < alpha < 1.0):
            raise ValueError(f"alpha must be in (0, 1), got {alpha!r}.")
        if not (0.0 < beta < 1.0):
            raise ValueError(f"beta must be in (0, 1), got {beta!r}.")

        # Enforce stationarity: alpha + beta < 1.
        if alpha + beta >= 1.0:
            scale: float = 0.95 / (alpha + beta)
            alpha = alpha * scale
            beta  = beta  * scale

        self._omega: float = omega
        self._alpha: float = alpha
        self._beta:  float = beta

        # Compute long-run variance: omega / (1 - alpha - beta)
        persistence: float = self._alpha + self._beta
        denom: float = 1.0 - persistence
        self._long_run_variance: float = None

        # Initialise current variance to the long-run variance.
        self._current_variance: float = self._long_run_variance

    def xǁVolatilityTrackerǁ__init____mutmut_39(
        self,
        omega: float = _DEFAULT_OMEGA,
        alpha: float = _DEFAULT_ALPHA,
        beta: float  = _DEFAULT_BETA,
    ) -> None:
        """
        Initialise the GARCH(1,1) tracker.

        Parameters
        ----------
        omega : float
            Long-run variance component. Must be > 0.
        alpha : float
            ARCH coefficient (shock sensitivity). Must be in (0, 1).
        beta : float
            GARCH coefficient (persistence). Must be in (0, 1).

        Notes
        -----
        If alpha + beta >= 1.0, parameters are rescaled so that
        alpha + beta = 0.95 (the stationarity boundary with margin),
        preserving the ratio alpha / beta.
        """
        if omega <= 0.0 or not math.isfinite(omega):
            raise ValueError(f"omega must be > 0, got {omega!r}.")
        if not (0.0 < alpha < 1.0):
            raise ValueError(f"alpha must be in (0, 1), got {alpha!r}.")
        if not (0.0 < beta < 1.0):
            raise ValueError(f"beta must be in (0, 1), got {beta!r}.")

        # Enforce stationarity: alpha + beta < 1.
        if alpha + beta >= 1.0:
            scale: float = 0.95 / (alpha + beta)
            alpha = alpha * scale
            beta  = beta  * scale

        self._omega: float = omega
        self._alpha: float = alpha
        self._beta:  float = beta

        # Compute long-run variance: omega / (1 - alpha - beta)
        persistence: float = self._alpha + self._beta
        denom: float = 1.0 - persistence
        self._long_run_variance: float = max(
            None,
            self._omega / denom,
        )

        # Initialise current variance to the long-run variance.
        self._current_variance: float = self._long_run_variance

    def xǁVolatilityTrackerǁ__init____mutmut_40(
        self,
        omega: float = _DEFAULT_OMEGA,
        alpha: float = _DEFAULT_ALPHA,
        beta: float  = _DEFAULT_BETA,
    ) -> None:
        """
        Initialise the GARCH(1,1) tracker.

        Parameters
        ----------
        omega : float
            Long-run variance component. Must be > 0.
        alpha : float
            ARCH coefficient (shock sensitivity). Must be in (0, 1).
        beta : float
            GARCH coefficient (persistence). Must be in (0, 1).

        Notes
        -----
        If alpha + beta >= 1.0, parameters are rescaled so that
        alpha + beta = 0.95 (the stationarity boundary with margin),
        preserving the ratio alpha / beta.
        """
        if omega <= 0.0 or not math.isfinite(omega):
            raise ValueError(f"omega must be > 0, got {omega!r}.")
        if not (0.0 < alpha < 1.0):
            raise ValueError(f"alpha must be in (0, 1), got {alpha!r}.")
        if not (0.0 < beta < 1.0):
            raise ValueError(f"beta must be in (0, 1), got {beta!r}.")

        # Enforce stationarity: alpha + beta < 1.
        if alpha + beta >= 1.0:
            scale: float = 0.95 / (alpha + beta)
            alpha = alpha * scale
            beta  = beta  * scale

        self._omega: float = omega
        self._alpha: float = alpha
        self._beta:  float = beta

        # Compute long-run variance: omega / (1 - alpha - beta)
        persistence: float = self._alpha + self._beta
        denom: float = 1.0 - persistence
        self._long_run_variance: float = max(
            _VOL_EPSILON ** 2,
            None,
        )

        # Initialise current variance to the long-run variance.
        self._current_variance: float = self._long_run_variance

    def xǁVolatilityTrackerǁ__init____mutmut_41(
        self,
        omega: float = _DEFAULT_OMEGA,
        alpha: float = _DEFAULT_ALPHA,
        beta: float  = _DEFAULT_BETA,
    ) -> None:
        """
        Initialise the GARCH(1,1) tracker.

        Parameters
        ----------
        omega : float
            Long-run variance component. Must be > 0.
        alpha : float
            ARCH coefficient (shock sensitivity). Must be in (0, 1).
        beta : float
            GARCH coefficient (persistence). Must be in (0, 1).

        Notes
        -----
        If alpha + beta >= 1.0, parameters are rescaled so that
        alpha + beta = 0.95 (the stationarity boundary with margin),
        preserving the ratio alpha / beta.
        """
        if omega <= 0.0 or not math.isfinite(omega):
            raise ValueError(f"omega must be > 0, got {omega!r}.")
        if not (0.0 < alpha < 1.0):
            raise ValueError(f"alpha must be in (0, 1), got {alpha!r}.")
        if not (0.0 < beta < 1.0):
            raise ValueError(f"beta must be in (0, 1), got {beta!r}.")

        # Enforce stationarity: alpha + beta < 1.
        if alpha + beta >= 1.0:
            scale: float = 0.95 / (alpha + beta)
            alpha = alpha * scale
            beta  = beta  * scale

        self._omega: float = omega
        self._alpha: float = alpha
        self._beta:  float = beta

        # Compute long-run variance: omega / (1 - alpha - beta)
        persistence: float = self._alpha + self._beta
        denom: float = 1.0 - persistence
        self._long_run_variance: float = max(
            self._omega / denom,
        )

        # Initialise current variance to the long-run variance.
        self._current_variance: float = self._long_run_variance

    def xǁVolatilityTrackerǁ__init____mutmut_42(
        self,
        omega: float = _DEFAULT_OMEGA,
        alpha: float = _DEFAULT_ALPHA,
        beta: float  = _DEFAULT_BETA,
    ) -> None:
        """
        Initialise the GARCH(1,1) tracker.

        Parameters
        ----------
        omega : float
            Long-run variance component. Must be > 0.
        alpha : float
            ARCH coefficient (shock sensitivity). Must be in (0, 1).
        beta : float
            GARCH coefficient (persistence). Must be in (0, 1).

        Notes
        -----
        If alpha + beta >= 1.0, parameters are rescaled so that
        alpha + beta = 0.95 (the stationarity boundary with margin),
        preserving the ratio alpha / beta.
        """
        if omega <= 0.0 or not math.isfinite(omega):
            raise ValueError(f"omega must be > 0, got {omega!r}.")
        if not (0.0 < alpha < 1.0):
            raise ValueError(f"alpha must be in (0, 1), got {alpha!r}.")
        if not (0.0 < beta < 1.0):
            raise ValueError(f"beta must be in (0, 1), got {beta!r}.")

        # Enforce stationarity: alpha + beta < 1.
        if alpha + beta >= 1.0:
            scale: float = 0.95 / (alpha + beta)
            alpha = alpha * scale
            beta  = beta  * scale

        self._omega: float = omega
        self._alpha: float = alpha
        self._beta:  float = beta

        # Compute long-run variance: omega / (1 - alpha - beta)
        persistence: float = self._alpha + self._beta
        denom: float = 1.0 - persistence
        self._long_run_variance: float = max(
            _VOL_EPSILON ** 2,
            )

        # Initialise current variance to the long-run variance.
        self._current_variance: float = self._long_run_variance

    def xǁVolatilityTrackerǁ__init____mutmut_43(
        self,
        omega: float = _DEFAULT_OMEGA,
        alpha: float = _DEFAULT_ALPHA,
        beta: float  = _DEFAULT_BETA,
    ) -> None:
        """
        Initialise the GARCH(1,1) tracker.

        Parameters
        ----------
        omega : float
            Long-run variance component. Must be > 0.
        alpha : float
            ARCH coefficient (shock sensitivity). Must be in (0, 1).
        beta : float
            GARCH coefficient (persistence). Must be in (0, 1).

        Notes
        -----
        If alpha + beta >= 1.0, parameters are rescaled so that
        alpha + beta = 0.95 (the stationarity boundary with margin),
        preserving the ratio alpha / beta.
        """
        if omega <= 0.0 or not math.isfinite(omega):
            raise ValueError(f"omega must be > 0, got {omega!r}.")
        if not (0.0 < alpha < 1.0):
            raise ValueError(f"alpha must be in (0, 1), got {alpha!r}.")
        if not (0.0 < beta < 1.0):
            raise ValueError(f"beta must be in (0, 1), got {beta!r}.")

        # Enforce stationarity: alpha + beta < 1.
        if alpha + beta >= 1.0:
            scale: float = 0.95 / (alpha + beta)
            alpha = alpha * scale
            beta  = beta  * scale

        self._omega: float = omega
        self._alpha: float = alpha
        self._beta:  float = beta

        # Compute long-run variance: omega / (1 - alpha - beta)
        persistence: float = self._alpha + self._beta
        denom: float = 1.0 - persistence
        self._long_run_variance: float = max(
            _VOL_EPSILON * 2,
            self._omega / denom,
        )

        # Initialise current variance to the long-run variance.
        self._current_variance: float = self._long_run_variance

    def xǁVolatilityTrackerǁ__init____mutmut_44(
        self,
        omega: float = _DEFAULT_OMEGA,
        alpha: float = _DEFAULT_ALPHA,
        beta: float  = _DEFAULT_BETA,
    ) -> None:
        """
        Initialise the GARCH(1,1) tracker.

        Parameters
        ----------
        omega : float
            Long-run variance component. Must be > 0.
        alpha : float
            ARCH coefficient (shock sensitivity). Must be in (0, 1).
        beta : float
            GARCH coefficient (persistence). Must be in (0, 1).

        Notes
        -----
        If alpha + beta >= 1.0, parameters are rescaled so that
        alpha + beta = 0.95 (the stationarity boundary with margin),
        preserving the ratio alpha / beta.
        """
        if omega <= 0.0 or not math.isfinite(omega):
            raise ValueError(f"omega must be > 0, got {omega!r}.")
        if not (0.0 < alpha < 1.0):
            raise ValueError(f"alpha must be in (0, 1), got {alpha!r}.")
        if not (0.0 < beta < 1.0):
            raise ValueError(f"beta must be in (0, 1), got {beta!r}.")

        # Enforce stationarity: alpha + beta < 1.
        if alpha + beta >= 1.0:
            scale: float = 0.95 / (alpha + beta)
            alpha = alpha * scale
            beta  = beta  * scale

        self._omega: float = omega
        self._alpha: float = alpha
        self._beta:  float = beta

        # Compute long-run variance: omega / (1 - alpha - beta)
        persistence: float = self._alpha + self._beta
        denom: float = 1.0 - persistence
        self._long_run_variance: float = max(
            _VOL_EPSILON ** 3,
            self._omega / denom,
        )

        # Initialise current variance to the long-run variance.
        self._current_variance: float = self._long_run_variance

    def xǁVolatilityTrackerǁ__init____mutmut_45(
        self,
        omega: float = _DEFAULT_OMEGA,
        alpha: float = _DEFAULT_ALPHA,
        beta: float  = _DEFAULT_BETA,
    ) -> None:
        """
        Initialise the GARCH(1,1) tracker.

        Parameters
        ----------
        omega : float
            Long-run variance component. Must be > 0.
        alpha : float
            ARCH coefficient (shock sensitivity). Must be in (0, 1).
        beta : float
            GARCH coefficient (persistence). Must be in (0, 1).

        Notes
        -----
        If alpha + beta >= 1.0, parameters are rescaled so that
        alpha + beta = 0.95 (the stationarity boundary with margin),
        preserving the ratio alpha / beta.
        """
        if omega <= 0.0 or not math.isfinite(omega):
            raise ValueError(f"omega must be > 0, got {omega!r}.")
        if not (0.0 < alpha < 1.0):
            raise ValueError(f"alpha must be in (0, 1), got {alpha!r}.")
        if not (0.0 < beta < 1.0):
            raise ValueError(f"beta must be in (0, 1), got {beta!r}.")

        # Enforce stationarity: alpha + beta < 1.
        if alpha + beta >= 1.0:
            scale: float = 0.95 / (alpha + beta)
            alpha = alpha * scale
            beta  = beta  * scale

        self._omega: float = omega
        self._alpha: float = alpha
        self._beta:  float = beta

        # Compute long-run variance: omega / (1 - alpha - beta)
        persistence: float = self._alpha + self._beta
        denom: float = 1.0 - persistence
        self._long_run_variance: float = max(
            _VOL_EPSILON ** 2,
            self._omega * denom,
        )

        # Initialise current variance to the long-run variance.
        self._current_variance: float = self._long_run_variance

    def xǁVolatilityTrackerǁ__init____mutmut_46(
        self,
        omega: float = _DEFAULT_OMEGA,
        alpha: float = _DEFAULT_ALPHA,
        beta: float  = _DEFAULT_BETA,
    ) -> None:
        """
        Initialise the GARCH(1,1) tracker.

        Parameters
        ----------
        omega : float
            Long-run variance component. Must be > 0.
        alpha : float
            ARCH coefficient (shock sensitivity). Must be in (0, 1).
        beta : float
            GARCH coefficient (persistence). Must be in (0, 1).

        Notes
        -----
        If alpha + beta >= 1.0, parameters are rescaled so that
        alpha + beta = 0.95 (the stationarity boundary with margin),
        preserving the ratio alpha / beta.
        """
        if omega <= 0.0 or not math.isfinite(omega):
            raise ValueError(f"omega must be > 0, got {omega!r}.")
        if not (0.0 < alpha < 1.0):
            raise ValueError(f"alpha must be in (0, 1), got {alpha!r}.")
        if not (0.0 < beta < 1.0):
            raise ValueError(f"beta must be in (0, 1), got {beta!r}.")

        # Enforce stationarity: alpha + beta < 1.
        if alpha + beta >= 1.0:
            scale: float = 0.95 / (alpha + beta)
            alpha = alpha * scale
            beta  = beta  * scale

        self._omega: float = omega
        self._alpha: float = alpha
        self._beta:  float = beta

        # Compute long-run variance: omega / (1 - alpha - beta)
        persistence: float = self._alpha + self._beta
        denom: float = 1.0 - persistence
        self._long_run_variance: float = max(
            _VOL_EPSILON ** 2,
            self._omega / denom,
        )

        # Initialise current variance to the long-run variance.
        self._current_variance: float = None
    
    xǁVolatilityTrackerǁ__init____mutmut_mutants : ClassVar[MutantDict] = { # type: ignore
    'xǁVolatilityTrackerǁ__init____mutmut_1': xǁVolatilityTrackerǁ__init____mutmut_1, 
        'xǁVolatilityTrackerǁ__init____mutmut_2': xǁVolatilityTrackerǁ__init____mutmut_2, 
        'xǁVolatilityTrackerǁ__init____mutmut_3': xǁVolatilityTrackerǁ__init____mutmut_3, 
        'xǁVolatilityTrackerǁ__init____mutmut_4': xǁVolatilityTrackerǁ__init____mutmut_4, 
        'xǁVolatilityTrackerǁ__init____mutmut_5': xǁVolatilityTrackerǁ__init____mutmut_5, 
        'xǁVolatilityTrackerǁ__init____mutmut_6': xǁVolatilityTrackerǁ__init____mutmut_6, 
        'xǁVolatilityTrackerǁ__init____mutmut_7': xǁVolatilityTrackerǁ__init____mutmut_7, 
        'xǁVolatilityTrackerǁ__init____mutmut_8': xǁVolatilityTrackerǁ__init____mutmut_8, 
        'xǁVolatilityTrackerǁ__init____mutmut_9': xǁVolatilityTrackerǁ__init____mutmut_9, 
        'xǁVolatilityTrackerǁ__init____mutmut_10': xǁVolatilityTrackerǁ__init____mutmut_10, 
        'xǁVolatilityTrackerǁ__init____mutmut_11': xǁVolatilityTrackerǁ__init____mutmut_11, 
        'xǁVolatilityTrackerǁ__init____mutmut_12': xǁVolatilityTrackerǁ__init____mutmut_12, 
        'xǁVolatilityTrackerǁ__init____mutmut_13': xǁVolatilityTrackerǁ__init____mutmut_13, 
        'xǁVolatilityTrackerǁ__init____mutmut_14': xǁVolatilityTrackerǁ__init____mutmut_14, 
        'xǁVolatilityTrackerǁ__init____mutmut_15': xǁVolatilityTrackerǁ__init____mutmut_15, 
        'xǁVolatilityTrackerǁ__init____mutmut_16': xǁVolatilityTrackerǁ__init____mutmut_16, 
        'xǁVolatilityTrackerǁ__init____mutmut_17': xǁVolatilityTrackerǁ__init____mutmut_17, 
        'xǁVolatilityTrackerǁ__init____mutmut_18': xǁVolatilityTrackerǁ__init____mutmut_18, 
        'xǁVolatilityTrackerǁ__init____mutmut_19': xǁVolatilityTrackerǁ__init____mutmut_19, 
        'xǁVolatilityTrackerǁ__init____mutmut_20': xǁVolatilityTrackerǁ__init____mutmut_20, 
        'xǁVolatilityTrackerǁ__init____mutmut_21': xǁVolatilityTrackerǁ__init____mutmut_21, 
        'xǁVolatilityTrackerǁ__init____mutmut_22': xǁVolatilityTrackerǁ__init____mutmut_22, 
        'xǁVolatilityTrackerǁ__init____mutmut_23': xǁVolatilityTrackerǁ__init____mutmut_23, 
        'xǁVolatilityTrackerǁ__init____mutmut_24': xǁVolatilityTrackerǁ__init____mutmut_24, 
        'xǁVolatilityTrackerǁ__init____mutmut_25': xǁVolatilityTrackerǁ__init____mutmut_25, 
        'xǁVolatilityTrackerǁ__init____mutmut_26': xǁVolatilityTrackerǁ__init____mutmut_26, 
        'xǁVolatilityTrackerǁ__init____mutmut_27': xǁVolatilityTrackerǁ__init____mutmut_27, 
        'xǁVolatilityTrackerǁ__init____mutmut_28': xǁVolatilityTrackerǁ__init____mutmut_28, 
        'xǁVolatilityTrackerǁ__init____mutmut_29': xǁVolatilityTrackerǁ__init____mutmut_29, 
        'xǁVolatilityTrackerǁ__init____mutmut_30': xǁVolatilityTrackerǁ__init____mutmut_30, 
        'xǁVolatilityTrackerǁ__init____mutmut_31': xǁVolatilityTrackerǁ__init____mutmut_31, 
        'xǁVolatilityTrackerǁ__init____mutmut_32': xǁVolatilityTrackerǁ__init____mutmut_32, 
        'xǁVolatilityTrackerǁ__init____mutmut_33': xǁVolatilityTrackerǁ__init____mutmut_33, 
        'xǁVolatilityTrackerǁ__init____mutmut_34': xǁVolatilityTrackerǁ__init____mutmut_34, 
        'xǁVolatilityTrackerǁ__init____mutmut_35': xǁVolatilityTrackerǁ__init____mutmut_35, 
        'xǁVolatilityTrackerǁ__init____mutmut_36': xǁVolatilityTrackerǁ__init____mutmut_36, 
        'xǁVolatilityTrackerǁ__init____mutmut_37': xǁVolatilityTrackerǁ__init____mutmut_37, 
        'xǁVolatilityTrackerǁ__init____mutmut_38': xǁVolatilityTrackerǁ__init____mutmut_38, 
        'xǁVolatilityTrackerǁ__init____mutmut_39': xǁVolatilityTrackerǁ__init____mutmut_39, 
        'xǁVolatilityTrackerǁ__init____mutmut_40': xǁVolatilityTrackerǁ__init____mutmut_40, 
        'xǁVolatilityTrackerǁ__init____mutmut_41': xǁVolatilityTrackerǁ__init____mutmut_41, 
        'xǁVolatilityTrackerǁ__init____mutmut_42': xǁVolatilityTrackerǁ__init____mutmut_42, 
        'xǁVolatilityTrackerǁ__init____mutmut_43': xǁVolatilityTrackerǁ__init____mutmut_43, 
        'xǁVolatilityTrackerǁ__init____mutmut_44': xǁVolatilityTrackerǁ__init____mutmut_44, 
        'xǁVolatilityTrackerǁ__init____mutmut_45': xǁVolatilityTrackerǁ__init____mutmut_45, 
        'xǁVolatilityTrackerǁ__init____mutmut_46': xǁVolatilityTrackerǁ__init____mutmut_46
    }
    xǁVolatilityTrackerǁ__init____mutmut_orig.__name__ = 'xǁVolatilityTrackerǁ__init__'

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def estimate_volatility(self, returns: List[float]) -> VolResult:
        args = [returns]# type: ignore
        kwargs = {}# type: ignore
        return _mutmut_trampoline(object.__getattribute__(self, 'xǁVolatilityTrackerǁestimate_volatility__mutmut_orig'), object.__getattribute__(self, 'xǁVolatilityTrackerǁestimate_volatility__mutmut_mutants'), args, kwargs, self)

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def xǁVolatilityTrackerǁestimate_volatility__mutmut_orig(self, returns: List[float]) -> VolResult:
        """
        Update the GARCH(1,1) model with a sequence of return observations
        and return the resulting volatility estimate.

        Non-finite values (NaN, Inf) are replaced with 0.0 and counted
        in nan_replaced. Empty or all-non-finite lists raise ValueError.

        The model is updated sequentially: for each return r_t,
          sigma^2_{t+1} = omega + alpha * r_t^2 + beta * sigma^2_t

        After processing all returns, self._current_variance holds the
        most recent conditional variance.

        Parameters
        ----------
        returns : List[float]
            Sequence of per-period returns. Must be non-empty.
            Non-finite values are replaced with 0.0.

        Returns
        -------
        VolResult
            Volatility estimate derived from the final variance state.

        Raises
        ------
        ValueError
            If returns is empty.
        TypeError
            If returns is None.
        """
        if returns is None:
            raise TypeError("returns must be a list, got None.")
        if len(returns) == 0:
            raise ValueError("returns must be non-empty.")

        # Clean returns: replace non-finite with 0.0.
        nan_replaced: int = 0
        clean: List[float] = []
        for r in returns:
            if math.isfinite(r):
                clean.append(r)
            else:
                clean.append(0.0)
                nan_replaced += 1

        n_clean: int = len(returns) - nan_replaced

        # Sequential GARCH update.
        variance: float = self._current_variance
        for r in clean:
            variance = (
                self._omega
                + self._alpha * r * r
                + self._beta * variance
            )
            # Floor to prevent numerical collapse.
            variance = max(_VOL_EPSILON ** 2, variance)

        # Update internal state.
        self._current_variance = variance

        volatility: float = max(_VOL_EPSILON, math.sqrt(variance))
        long_run_vol: float = max(_VOL_EPSILON, math.sqrt(self._long_run_variance))

        return VolResult(
            volatility=volatility,
            variance=variance,
            long_run_volatility=long_run_vol,
            n_clean_returns=n_clean,
            nan_replaced=nan_replaced,
        )

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def xǁVolatilityTrackerǁestimate_volatility__mutmut_1(self, returns: List[float]) -> VolResult:
        """
        Update the GARCH(1,1) model with a sequence of return observations
        and return the resulting volatility estimate.

        Non-finite values (NaN, Inf) are replaced with 0.0 and counted
        in nan_replaced. Empty or all-non-finite lists raise ValueError.

        The model is updated sequentially: for each return r_t,
          sigma^2_{t+1} = omega + alpha * r_t^2 + beta * sigma^2_t

        After processing all returns, self._current_variance holds the
        most recent conditional variance.

        Parameters
        ----------
        returns : List[float]
            Sequence of per-period returns. Must be non-empty.
            Non-finite values are replaced with 0.0.

        Returns
        -------
        VolResult
            Volatility estimate derived from the final variance state.

        Raises
        ------
        ValueError
            If returns is empty.
        TypeError
            If returns is None.
        """
        if returns is not None:
            raise TypeError("returns must be a list, got None.")
        if len(returns) == 0:
            raise ValueError("returns must be non-empty.")

        # Clean returns: replace non-finite with 0.0.
        nan_replaced: int = 0
        clean: List[float] = []
        for r in returns:
            if math.isfinite(r):
                clean.append(r)
            else:
                clean.append(0.0)
                nan_replaced += 1

        n_clean: int = len(returns) - nan_replaced

        # Sequential GARCH update.
        variance: float = self._current_variance
        for r in clean:
            variance = (
                self._omega
                + self._alpha * r * r
                + self._beta * variance
            )
            # Floor to prevent numerical collapse.
            variance = max(_VOL_EPSILON ** 2, variance)

        # Update internal state.
        self._current_variance = variance

        volatility: float = max(_VOL_EPSILON, math.sqrt(variance))
        long_run_vol: float = max(_VOL_EPSILON, math.sqrt(self._long_run_variance))

        return VolResult(
            volatility=volatility,
            variance=variance,
            long_run_volatility=long_run_vol,
            n_clean_returns=n_clean,
            nan_replaced=nan_replaced,
        )

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def xǁVolatilityTrackerǁestimate_volatility__mutmut_2(self, returns: List[float]) -> VolResult:
        """
        Update the GARCH(1,1) model with a sequence of return observations
        and return the resulting volatility estimate.

        Non-finite values (NaN, Inf) are replaced with 0.0 and counted
        in nan_replaced. Empty or all-non-finite lists raise ValueError.

        The model is updated sequentially: for each return r_t,
          sigma^2_{t+1} = omega + alpha * r_t^2 + beta * sigma^2_t

        After processing all returns, self._current_variance holds the
        most recent conditional variance.

        Parameters
        ----------
        returns : List[float]
            Sequence of per-period returns. Must be non-empty.
            Non-finite values are replaced with 0.0.

        Returns
        -------
        VolResult
            Volatility estimate derived from the final variance state.

        Raises
        ------
        ValueError
            If returns is empty.
        TypeError
            If returns is None.
        """
        if returns is None:
            raise TypeError(None)
        if len(returns) == 0:
            raise ValueError("returns must be non-empty.")

        # Clean returns: replace non-finite with 0.0.
        nan_replaced: int = 0
        clean: List[float] = []
        for r in returns:
            if math.isfinite(r):
                clean.append(r)
            else:
                clean.append(0.0)
                nan_replaced += 1

        n_clean: int = len(returns) - nan_replaced

        # Sequential GARCH update.
        variance: float = self._current_variance
        for r in clean:
            variance = (
                self._omega
                + self._alpha * r * r
                + self._beta * variance
            )
            # Floor to prevent numerical collapse.
            variance = max(_VOL_EPSILON ** 2, variance)

        # Update internal state.
        self._current_variance = variance

        volatility: float = max(_VOL_EPSILON, math.sqrt(variance))
        long_run_vol: float = max(_VOL_EPSILON, math.sqrt(self._long_run_variance))

        return VolResult(
            volatility=volatility,
            variance=variance,
            long_run_volatility=long_run_vol,
            n_clean_returns=n_clean,
            nan_replaced=nan_replaced,
        )

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def xǁVolatilityTrackerǁestimate_volatility__mutmut_3(self, returns: List[float]) -> VolResult:
        """
        Update the GARCH(1,1) model with a sequence of return observations
        and return the resulting volatility estimate.

        Non-finite values (NaN, Inf) are replaced with 0.0 and counted
        in nan_replaced. Empty or all-non-finite lists raise ValueError.

        The model is updated sequentially: for each return r_t,
          sigma^2_{t+1} = omega + alpha * r_t^2 + beta * sigma^2_t

        After processing all returns, self._current_variance holds the
        most recent conditional variance.

        Parameters
        ----------
        returns : List[float]
            Sequence of per-period returns. Must be non-empty.
            Non-finite values are replaced with 0.0.

        Returns
        -------
        VolResult
            Volatility estimate derived from the final variance state.

        Raises
        ------
        ValueError
            If returns is empty.
        TypeError
            If returns is None.
        """
        if returns is None:
            raise TypeError("XXreturns must be a list, got None.XX")
        if len(returns) == 0:
            raise ValueError("returns must be non-empty.")

        # Clean returns: replace non-finite with 0.0.
        nan_replaced: int = 0
        clean: List[float] = []
        for r in returns:
            if math.isfinite(r):
                clean.append(r)
            else:
                clean.append(0.0)
                nan_replaced += 1

        n_clean: int = len(returns) - nan_replaced

        # Sequential GARCH update.
        variance: float = self._current_variance
        for r in clean:
            variance = (
                self._omega
                + self._alpha * r * r
                + self._beta * variance
            )
            # Floor to prevent numerical collapse.
            variance = max(_VOL_EPSILON ** 2, variance)

        # Update internal state.
        self._current_variance = variance

        volatility: float = max(_VOL_EPSILON, math.sqrt(variance))
        long_run_vol: float = max(_VOL_EPSILON, math.sqrt(self._long_run_variance))

        return VolResult(
            volatility=volatility,
            variance=variance,
            long_run_volatility=long_run_vol,
            n_clean_returns=n_clean,
            nan_replaced=nan_replaced,
        )

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def xǁVolatilityTrackerǁestimate_volatility__mutmut_4(self, returns: List[float]) -> VolResult:
        """
        Update the GARCH(1,1) model with a sequence of return observations
        and return the resulting volatility estimate.

        Non-finite values (NaN, Inf) are replaced with 0.0 and counted
        in nan_replaced. Empty or all-non-finite lists raise ValueError.

        The model is updated sequentially: for each return r_t,
          sigma^2_{t+1} = omega + alpha * r_t^2 + beta * sigma^2_t

        After processing all returns, self._current_variance holds the
        most recent conditional variance.

        Parameters
        ----------
        returns : List[float]
            Sequence of per-period returns. Must be non-empty.
            Non-finite values are replaced with 0.0.

        Returns
        -------
        VolResult
            Volatility estimate derived from the final variance state.

        Raises
        ------
        ValueError
            If returns is empty.
        TypeError
            If returns is None.
        """
        if returns is None:
            raise TypeError("returns must be a list, got none.")
        if len(returns) == 0:
            raise ValueError("returns must be non-empty.")

        # Clean returns: replace non-finite with 0.0.
        nan_replaced: int = 0
        clean: List[float] = []
        for r in returns:
            if math.isfinite(r):
                clean.append(r)
            else:
                clean.append(0.0)
                nan_replaced += 1

        n_clean: int = len(returns) - nan_replaced

        # Sequential GARCH update.
        variance: float = self._current_variance
        for r in clean:
            variance = (
                self._omega
                + self._alpha * r * r
                + self._beta * variance
            )
            # Floor to prevent numerical collapse.
            variance = max(_VOL_EPSILON ** 2, variance)

        # Update internal state.
        self._current_variance = variance

        volatility: float = max(_VOL_EPSILON, math.sqrt(variance))
        long_run_vol: float = max(_VOL_EPSILON, math.sqrt(self._long_run_variance))

        return VolResult(
            volatility=volatility,
            variance=variance,
            long_run_volatility=long_run_vol,
            n_clean_returns=n_clean,
            nan_replaced=nan_replaced,
        )

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def xǁVolatilityTrackerǁestimate_volatility__mutmut_5(self, returns: List[float]) -> VolResult:
        """
        Update the GARCH(1,1) model with a sequence of return observations
        and return the resulting volatility estimate.

        Non-finite values (NaN, Inf) are replaced with 0.0 and counted
        in nan_replaced. Empty or all-non-finite lists raise ValueError.

        The model is updated sequentially: for each return r_t,
          sigma^2_{t+1} = omega + alpha * r_t^2 + beta * sigma^2_t

        After processing all returns, self._current_variance holds the
        most recent conditional variance.

        Parameters
        ----------
        returns : List[float]
            Sequence of per-period returns. Must be non-empty.
            Non-finite values are replaced with 0.0.

        Returns
        -------
        VolResult
            Volatility estimate derived from the final variance state.

        Raises
        ------
        ValueError
            If returns is empty.
        TypeError
            If returns is None.
        """
        if returns is None:
            raise TypeError("RETURNS MUST BE A LIST, GOT NONE.")
        if len(returns) == 0:
            raise ValueError("returns must be non-empty.")

        # Clean returns: replace non-finite with 0.0.
        nan_replaced: int = 0
        clean: List[float] = []
        for r in returns:
            if math.isfinite(r):
                clean.append(r)
            else:
                clean.append(0.0)
                nan_replaced += 1

        n_clean: int = len(returns) - nan_replaced

        # Sequential GARCH update.
        variance: float = self._current_variance
        for r in clean:
            variance = (
                self._omega
                + self._alpha * r * r
                + self._beta * variance
            )
            # Floor to prevent numerical collapse.
            variance = max(_VOL_EPSILON ** 2, variance)

        # Update internal state.
        self._current_variance = variance

        volatility: float = max(_VOL_EPSILON, math.sqrt(variance))
        long_run_vol: float = max(_VOL_EPSILON, math.sqrt(self._long_run_variance))

        return VolResult(
            volatility=volatility,
            variance=variance,
            long_run_volatility=long_run_vol,
            n_clean_returns=n_clean,
            nan_replaced=nan_replaced,
        )

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def xǁVolatilityTrackerǁestimate_volatility__mutmut_6(self, returns: List[float]) -> VolResult:
        """
        Update the GARCH(1,1) model with a sequence of return observations
        and return the resulting volatility estimate.

        Non-finite values (NaN, Inf) are replaced with 0.0 and counted
        in nan_replaced. Empty or all-non-finite lists raise ValueError.

        The model is updated sequentially: for each return r_t,
          sigma^2_{t+1} = omega + alpha * r_t^2 + beta * sigma^2_t

        After processing all returns, self._current_variance holds the
        most recent conditional variance.

        Parameters
        ----------
        returns : List[float]
            Sequence of per-period returns. Must be non-empty.
            Non-finite values are replaced with 0.0.

        Returns
        -------
        VolResult
            Volatility estimate derived from the final variance state.

        Raises
        ------
        ValueError
            If returns is empty.
        TypeError
            If returns is None.
        """
        if returns is None:
            raise TypeError("returns must be a list, got None.")
        if len(returns) != 0:
            raise ValueError("returns must be non-empty.")

        # Clean returns: replace non-finite with 0.0.
        nan_replaced: int = 0
        clean: List[float] = []
        for r in returns:
            if math.isfinite(r):
                clean.append(r)
            else:
                clean.append(0.0)
                nan_replaced += 1

        n_clean: int = len(returns) - nan_replaced

        # Sequential GARCH update.
        variance: float = self._current_variance
        for r in clean:
            variance = (
                self._omega
                + self._alpha * r * r
                + self._beta * variance
            )
            # Floor to prevent numerical collapse.
            variance = max(_VOL_EPSILON ** 2, variance)

        # Update internal state.
        self._current_variance = variance

        volatility: float = max(_VOL_EPSILON, math.sqrt(variance))
        long_run_vol: float = max(_VOL_EPSILON, math.sqrt(self._long_run_variance))

        return VolResult(
            volatility=volatility,
            variance=variance,
            long_run_volatility=long_run_vol,
            n_clean_returns=n_clean,
            nan_replaced=nan_replaced,
        )

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def xǁVolatilityTrackerǁestimate_volatility__mutmut_7(self, returns: List[float]) -> VolResult:
        """
        Update the GARCH(1,1) model with a sequence of return observations
        and return the resulting volatility estimate.

        Non-finite values (NaN, Inf) are replaced with 0.0 and counted
        in nan_replaced. Empty or all-non-finite lists raise ValueError.

        The model is updated sequentially: for each return r_t,
          sigma^2_{t+1} = omega + alpha * r_t^2 + beta * sigma^2_t

        After processing all returns, self._current_variance holds the
        most recent conditional variance.

        Parameters
        ----------
        returns : List[float]
            Sequence of per-period returns. Must be non-empty.
            Non-finite values are replaced with 0.0.

        Returns
        -------
        VolResult
            Volatility estimate derived from the final variance state.

        Raises
        ------
        ValueError
            If returns is empty.
        TypeError
            If returns is None.
        """
        if returns is None:
            raise TypeError("returns must be a list, got None.")
        if len(returns) == 1:
            raise ValueError("returns must be non-empty.")

        # Clean returns: replace non-finite with 0.0.
        nan_replaced: int = 0
        clean: List[float] = []
        for r in returns:
            if math.isfinite(r):
                clean.append(r)
            else:
                clean.append(0.0)
                nan_replaced += 1

        n_clean: int = len(returns) - nan_replaced

        # Sequential GARCH update.
        variance: float = self._current_variance
        for r in clean:
            variance = (
                self._omega
                + self._alpha * r * r
                + self._beta * variance
            )
            # Floor to prevent numerical collapse.
            variance = max(_VOL_EPSILON ** 2, variance)

        # Update internal state.
        self._current_variance = variance

        volatility: float = max(_VOL_EPSILON, math.sqrt(variance))
        long_run_vol: float = max(_VOL_EPSILON, math.sqrt(self._long_run_variance))

        return VolResult(
            volatility=volatility,
            variance=variance,
            long_run_volatility=long_run_vol,
            n_clean_returns=n_clean,
            nan_replaced=nan_replaced,
        )

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def xǁVolatilityTrackerǁestimate_volatility__mutmut_8(self, returns: List[float]) -> VolResult:
        """
        Update the GARCH(1,1) model with a sequence of return observations
        and return the resulting volatility estimate.

        Non-finite values (NaN, Inf) are replaced with 0.0 and counted
        in nan_replaced. Empty or all-non-finite lists raise ValueError.

        The model is updated sequentially: for each return r_t,
          sigma^2_{t+1} = omega + alpha * r_t^2 + beta * sigma^2_t

        After processing all returns, self._current_variance holds the
        most recent conditional variance.

        Parameters
        ----------
        returns : List[float]
            Sequence of per-period returns. Must be non-empty.
            Non-finite values are replaced with 0.0.

        Returns
        -------
        VolResult
            Volatility estimate derived from the final variance state.

        Raises
        ------
        ValueError
            If returns is empty.
        TypeError
            If returns is None.
        """
        if returns is None:
            raise TypeError("returns must be a list, got None.")
        if len(returns) == 0:
            raise ValueError(None)

        # Clean returns: replace non-finite with 0.0.
        nan_replaced: int = 0
        clean: List[float] = []
        for r in returns:
            if math.isfinite(r):
                clean.append(r)
            else:
                clean.append(0.0)
                nan_replaced += 1

        n_clean: int = len(returns) - nan_replaced

        # Sequential GARCH update.
        variance: float = self._current_variance
        for r in clean:
            variance = (
                self._omega
                + self._alpha * r * r
                + self._beta * variance
            )
            # Floor to prevent numerical collapse.
            variance = max(_VOL_EPSILON ** 2, variance)

        # Update internal state.
        self._current_variance = variance

        volatility: float = max(_VOL_EPSILON, math.sqrt(variance))
        long_run_vol: float = max(_VOL_EPSILON, math.sqrt(self._long_run_variance))

        return VolResult(
            volatility=volatility,
            variance=variance,
            long_run_volatility=long_run_vol,
            n_clean_returns=n_clean,
            nan_replaced=nan_replaced,
        )

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def xǁVolatilityTrackerǁestimate_volatility__mutmut_9(self, returns: List[float]) -> VolResult:
        """
        Update the GARCH(1,1) model with a sequence of return observations
        and return the resulting volatility estimate.

        Non-finite values (NaN, Inf) are replaced with 0.0 and counted
        in nan_replaced. Empty or all-non-finite lists raise ValueError.

        The model is updated sequentially: for each return r_t,
          sigma^2_{t+1} = omega + alpha * r_t^2 + beta * sigma^2_t

        After processing all returns, self._current_variance holds the
        most recent conditional variance.

        Parameters
        ----------
        returns : List[float]
            Sequence of per-period returns. Must be non-empty.
            Non-finite values are replaced with 0.0.

        Returns
        -------
        VolResult
            Volatility estimate derived from the final variance state.

        Raises
        ------
        ValueError
            If returns is empty.
        TypeError
            If returns is None.
        """
        if returns is None:
            raise TypeError("returns must be a list, got None.")
        if len(returns) == 0:
            raise ValueError("XXreturns must be non-empty.XX")

        # Clean returns: replace non-finite with 0.0.
        nan_replaced: int = 0
        clean: List[float] = []
        for r in returns:
            if math.isfinite(r):
                clean.append(r)
            else:
                clean.append(0.0)
                nan_replaced += 1

        n_clean: int = len(returns) - nan_replaced

        # Sequential GARCH update.
        variance: float = self._current_variance
        for r in clean:
            variance = (
                self._omega
                + self._alpha * r * r
                + self._beta * variance
            )
            # Floor to prevent numerical collapse.
            variance = max(_VOL_EPSILON ** 2, variance)

        # Update internal state.
        self._current_variance = variance

        volatility: float = max(_VOL_EPSILON, math.sqrt(variance))
        long_run_vol: float = max(_VOL_EPSILON, math.sqrt(self._long_run_variance))

        return VolResult(
            volatility=volatility,
            variance=variance,
            long_run_volatility=long_run_vol,
            n_clean_returns=n_clean,
            nan_replaced=nan_replaced,
        )

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def xǁVolatilityTrackerǁestimate_volatility__mutmut_10(self, returns: List[float]) -> VolResult:
        """
        Update the GARCH(1,1) model with a sequence of return observations
        and return the resulting volatility estimate.

        Non-finite values (NaN, Inf) are replaced with 0.0 and counted
        in nan_replaced. Empty or all-non-finite lists raise ValueError.

        The model is updated sequentially: for each return r_t,
          sigma^2_{t+1} = omega + alpha * r_t^2 + beta * sigma^2_t

        After processing all returns, self._current_variance holds the
        most recent conditional variance.

        Parameters
        ----------
        returns : List[float]
            Sequence of per-period returns. Must be non-empty.
            Non-finite values are replaced with 0.0.

        Returns
        -------
        VolResult
            Volatility estimate derived from the final variance state.

        Raises
        ------
        ValueError
            If returns is empty.
        TypeError
            If returns is None.
        """
        if returns is None:
            raise TypeError("returns must be a list, got None.")
        if len(returns) == 0:
            raise ValueError("RETURNS MUST BE NON-EMPTY.")

        # Clean returns: replace non-finite with 0.0.
        nan_replaced: int = 0
        clean: List[float] = []
        for r in returns:
            if math.isfinite(r):
                clean.append(r)
            else:
                clean.append(0.0)
                nan_replaced += 1

        n_clean: int = len(returns) - nan_replaced

        # Sequential GARCH update.
        variance: float = self._current_variance
        for r in clean:
            variance = (
                self._omega
                + self._alpha * r * r
                + self._beta * variance
            )
            # Floor to prevent numerical collapse.
            variance = max(_VOL_EPSILON ** 2, variance)

        # Update internal state.
        self._current_variance = variance

        volatility: float = max(_VOL_EPSILON, math.sqrt(variance))
        long_run_vol: float = max(_VOL_EPSILON, math.sqrt(self._long_run_variance))

        return VolResult(
            volatility=volatility,
            variance=variance,
            long_run_volatility=long_run_vol,
            n_clean_returns=n_clean,
            nan_replaced=nan_replaced,
        )

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def xǁVolatilityTrackerǁestimate_volatility__mutmut_11(self, returns: List[float]) -> VolResult:
        """
        Update the GARCH(1,1) model with a sequence of return observations
        and return the resulting volatility estimate.

        Non-finite values (NaN, Inf) are replaced with 0.0 and counted
        in nan_replaced. Empty or all-non-finite lists raise ValueError.

        The model is updated sequentially: for each return r_t,
          sigma^2_{t+1} = omega + alpha * r_t^2 + beta * sigma^2_t

        After processing all returns, self._current_variance holds the
        most recent conditional variance.

        Parameters
        ----------
        returns : List[float]
            Sequence of per-period returns. Must be non-empty.
            Non-finite values are replaced with 0.0.

        Returns
        -------
        VolResult
            Volatility estimate derived from the final variance state.

        Raises
        ------
        ValueError
            If returns is empty.
        TypeError
            If returns is None.
        """
        if returns is None:
            raise TypeError("returns must be a list, got None.")
        if len(returns) == 0:
            raise ValueError("returns must be non-empty.")

        # Clean returns: replace non-finite with 0.0.
        nan_replaced: int = None
        clean: List[float] = []
        for r in returns:
            if math.isfinite(r):
                clean.append(r)
            else:
                clean.append(0.0)
                nan_replaced += 1

        n_clean: int = len(returns) - nan_replaced

        # Sequential GARCH update.
        variance: float = self._current_variance
        for r in clean:
            variance = (
                self._omega
                + self._alpha * r * r
                + self._beta * variance
            )
            # Floor to prevent numerical collapse.
            variance = max(_VOL_EPSILON ** 2, variance)

        # Update internal state.
        self._current_variance = variance

        volatility: float = max(_VOL_EPSILON, math.sqrt(variance))
        long_run_vol: float = max(_VOL_EPSILON, math.sqrt(self._long_run_variance))

        return VolResult(
            volatility=volatility,
            variance=variance,
            long_run_volatility=long_run_vol,
            n_clean_returns=n_clean,
            nan_replaced=nan_replaced,
        )

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def xǁVolatilityTrackerǁestimate_volatility__mutmut_12(self, returns: List[float]) -> VolResult:
        """
        Update the GARCH(1,1) model with a sequence of return observations
        and return the resulting volatility estimate.

        Non-finite values (NaN, Inf) are replaced with 0.0 and counted
        in nan_replaced. Empty or all-non-finite lists raise ValueError.

        The model is updated sequentially: for each return r_t,
          sigma^2_{t+1} = omega + alpha * r_t^2 + beta * sigma^2_t

        After processing all returns, self._current_variance holds the
        most recent conditional variance.

        Parameters
        ----------
        returns : List[float]
            Sequence of per-period returns. Must be non-empty.
            Non-finite values are replaced with 0.0.

        Returns
        -------
        VolResult
            Volatility estimate derived from the final variance state.

        Raises
        ------
        ValueError
            If returns is empty.
        TypeError
            If returns is None.
        """
        if returns is None:
            raise TypeError("returns must be a list, got None.")
        if len(returns) == 0:
            raise ValueError("returns must be non-empty.")

        # Clean returns: replace non-finite with 0.0.
        nan_replaced: int = 1
        clean: List[float] = []
        for r in returns:
            if math.isfinite(r):
                clean.append(r)
            else:
                clean.append(0.0)
                nan_replaced += 1

        n_clean: int = len(returns) - nan_replaced

        # Sequential GARCH update.
        variance: float = self._current_variance
        for r in clean:
            variance = (
                self._omega
                + self._alpha * r * r
                + self._beta * variance
            )
            # Floor to prevent numerical collapse.
            variance = max(_VOL_EPSILON ** 2, variance)

        # Update internal state.
        self._current_variance = variance

        volatility: float = max(_VOL_EPSILON, math.sqrt(variance))
        long_run_vol: float = max(_VOL_EPSILON, math.sqrt(self._long_run_variance))

        return VolResult(
            volatility=volatility,
            variance=variance,
            long_run_volatility=long_run_vol,
            n_clean_returns=n_clean,
            nan_replaced=nan_replaced,
        )

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def xǁVolatilityTrackerǁestimate_volatility__mutmut_13(self, returns: List[float]) -> VolResult:
        """
        Update the GARCH(1,1) model with a sequence of return observations
        and return the resulting volatility estimate.

        Non-finite values (NaN, Inf) are replaced with 0.0 and counted
        in nan_replaced. Empty or all-non-finite lists raise ValueError.

        The model is updated sequentially: for each return r_t,
          sigma^2_{t+1} = omega + alpha * r_t^2 + beta * sigma^2_t

        After processing all returns, self._current_variance holds the
        most recent conditional variance.

        Parameters
        ----------
        returns : List[float]
            Sequence of per-period returns. Must be non-empty.
            Non-finite values are replaced with 0.0.

        Returns
        -------
        VolResult
            Volatility estimate derived from the final variance state.

        Raises
        ------
        ValueError
            If returns is empty.
        TypeError
            If returns is None.
        """
        if returns is None:
            raise TypeError("returns must be a list, got None.")
        if len(returns) == 0:
            raise ValueError("returns must be non-empty.")

        # Clean returns: replace non-finite with 0.0.
        nan_replaced: int = 0
        clean: List[float] = None
        for r in returns:
            if math.isfinite(r):
                clean.append(r)
            else:
                clean.append(0.0)
                nan_replaced += 1

        n_clean: int = len(returns) - nan_replaced

        # Sequential GARCH update.
        variance: float = self._current_variance
        for r in clean:
            variance = (
                self._omega
                + self._alpha * r * r
                + self._beta * variance
            )
            # Floor to prevent numerical collapse.
            variance = max(_VOL_EPSILON ** 2, variance)

        # Update internal state.
        self._current_variance = variance

        volatility: float = max(_VOL_EPSILON, math.sqrt(variance))
        long_run_vol: float = max(_VOL_EPSILON, math.sqrt(self._long_run_variance))

        return VolResult(
            volatility=volatility,
            variance=variance,
            long_run_volatility=long_run_vol,
            n_clean_returns=n_clean,
            nan_replaced=nan_replaced,
        )

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def xǁVolatilityTrackerǁestimate_volatility__mutmut_14(self, returns: List[float]) -> VolResult:
        """
        Update the GARCH(1,1) model with a sequence of return observations
        and return the resulting volatility estimate.

        Non-finite values (NaN, Inf) are replaced with 0.0 and counted
        in nan_replaced. Empty or all-non-finite lists raise ValueError.

        The model is updated sequentially: for each return r_t,
          sigma^2_{t+1} = omega + alpha * r_t^2 + beta * sigma^2_t

        After processing all returns, self._current_variance holds the
        most recent conditional variance.

        Parameters
        ----------
        returns : List[float]
            Sequence of per-period returns. Must be non-empty.
            Non-finite values are replaced with 0.0.

        Returns
        -------
        VolResult
            Volatility estimate derived from the final variance state.

        Raises
        ------
        ValueError
            If returns is empty.
        TypeError
            If returns is None.
        """
        if returns is None:
            raise TypeError("returns must be a list, got None.")
        if len(returns) == 0:
            raise ValueError("returns must be non-empty.")

        # Clean returns: replace non-finite with 0.0.
        nan_replaced: int = 0
        clean: List[float] = []
        for r in returns:
            if math.isfinite(None):
                clean.append(r)
            else:
                clean.append(0.0)
                nan_replaced += 1

        n_clean: int = len(returns) - nan_replaced

        # Sequential GARCH update.
        variance: float = self._current_variance
        for r in clean:
            variance = (
                self._omega
                + self._alpha * r * r
                + self._beta * variance
            )
            # Floor to prevent numerical collapse.
            variance = max(_VOL_EPSILON ** 2, variance)

        # Update internal state.
        self._current_variance = variance

        volatility: float = max(_VOL_EPSILON, math.sqrt(variance))
        long_run_vol: float = max(_VOL_EPSILON, math.sqrt(self._long_run_variance))

        return VolResult(
            volatility=volatility,
            variance=variance,
            long_run_volatility=long_run_vol,
            n_clean_returns=n_clean,
            nan_replaced=nan_replaced,
        )

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def xǁVolatilityTrackerǁestimate_volatility__mutmut_15(self, returns: List[float]) -> VolResult:
        """
        Update the GARCH(1,1) model with a sequence of return observations
        and return the resulting volatility estimate.

        Non-finite values (NaN, Inf) are replaced with 0.0 and counted
        in nan_replaced. Empty or all-non-finite lists raise ValueError.

        The model is updated sequentially: for each return r_t,
          sigma^2_{t+1} = omega + alpha * r_t^2 + beta * sigma^2_t

        After processing all returns, self._current_variance holds the
        most recent conditional variance.

        Parameters
        ----------
        returns : List[float]
            Sequence of per-period returns. Must be non-empty.
            Non-finite values are replaced with 0.0.

        Returns
        -------
        VolResult
            Volatility estimate derived from the final variance state.

        Raises
        ------
        ValueError
            If returns is empty.
        TypeError
            If returns is None.
        """
        if returns is None:
            raise TypeError("returns must be a list, got None.")
        if len(returns) == 0:
            raise ValueError("returns must be non-empty.")

        # Clean returns: replace non-finite with 0.0.
        nan_replaced: int = 0
        clean: List[float] = []
        for r in returns:
            if math.isfinite(r):
                clean.append(None)
            else:
                clean.append(0.0)
                nan_replaced += 1

        n_clean: int = len(returns) - nan_replaced

        # Sequential GARCH update.
        variance: float = self._current_variance
        for r in clean:
            variance = (
                self._omega
                + self._alpha * r * r
                + self._beta * variance
            )
            # Floor to prevent numerical collapse.
            variance = max(_VOL_EPSILON ** 2, variance)

        # Update internal state.
        self._current_variance = variance

        volatility: float = max(_VOL_EPSILON, math.sqrt(variance))
        long_run_vol: float = max(_VOL_EPSILON, math.sqrt(self._long_run_variance))

        return VolResult(
            volatility=volatility,
            variance=variance,
            long_run_volatility=long_run_vol,
            n_clean_returns=n_clean,
            nan_replaced=nan_replaced,
        )

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def xǁVolatilityTrackerǁestimate_volatility__mutmut_16(self, returns: List[float]) -> VolResult:
        """
        Update the GARCH(1,1) model with a sequence of return observations
        and return the resulting volatility estimate.

        Non-finite values (NaN, Inf) are replaced with 0.0 and counted
        in nan_replaced. Empty or all-non-finite lists raise ValueError.

        The model is updated sequentially: for each return r_t,
          sigma^2_{t+1} = omega + alpha * r_t^2 + beta * sigma^2_t

        After processing all returns, self._current_variance holds the
        most recent conditional variance.

        Parameters
        ----------
        returns : List[float]
            Sequence of per-period returns. Must be non-empty.
            Non-finite values are replaced with 0.0.

        Returns
        -------
        VolResult
            Volatility estimate derived from the final variance state.

        Raises
        ------
        ValueError
            If returns is empty.
        TypeError
            If returns is None.
        """
        if returns is None:
            raise TypeError("returns must be a list, got None.")
        if len(returns) == 0:
            raise ValueError("returns must be non-empty.")

        # Clean returns: replace non-finite with 0.0.
        nan_replaced: int = 0
        clean: List[float] = []
        for r in returns:
            if math.isfinite(r):
                clean.append(r)
            else:
                clean.append(None)
                nan_replaced += 1

        n_clean: int = len(returns) - nan_replaced

        # Sequential GARCH update.
        variance: float = self._current_variance
        for r in clean:
            variance = (
                self._omega
                + self._alpha * r * r
                + self._beta * variance
            )
            # Floor to prevent numerical collapse.
            variance = max(_VOL_EPSILON ** 2, variance)

        # Update internal state.
        self._current_variance = variance

        volatility: float = max(_VOL_EPSILON, math.sqrt(variance))
        long_run_vol: float = max(_VOL_EPSILON, math.sqrt(self._long_run_variance))

        return VolResult(
            volatility=volatility,
            variance=variance,
            long_run_volatility=long_run_vol,
            n_clean_returns=n_clean,
            nan_replaced=nan_replaced,
        )

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def xǁVolatilityTrackerǁestimate_volatility__mutmut_17(self, returns: List[float]) -> VolResult:
        """
        Update the GARCH(1,1) model with a sequence of return observations
        and return the resulting volatility estimate.

        Non-finite values (NaN, Inf) are replaced with 0.0 and counted
        in nan_replaced. Empty or all-non-finite lists raise ValueError.

        The model is updated sequentially: for each return r_t,
          sigma^2_{t+1} = omega + alpha * r_t^2 + beta * sigma^2_t

        After processing all returns, self._current_variance holds the
        most recent conditional variance.

        Parameters
        ----------
        returns : List[float]
            Sequence of per-period returns. Must be non-empty.
            Non-finite values are replaced with 0.0.

        Returns
        -------
        VolResult
            Volatility estimate derived from the final variance state.

        Raises
        ------
        ValueError
            If returns is empty.
        TypeError
            If returns is None.
        """
        if returns is None:
            raise TypeError("returns must be a list, got None.")
        if len(returns) == 0:
            raise ValueError("returns must be non-empty.")

        # Clean returns: replace non-finite with 0.0.
        nan_replaced: int = 0
        clean: List[float] = []
        for r in returns:
            if math.isfinite(r):
                clean.append(r)
            else:
                clean.append(1.0)
                nan_replaced += 1

        n_clean: int = len(returns) - nan_replaced

        # Sequential GARCH update.
        variance: float = self._current_variance
        for r in clean:
            variance = (
                self._omega
                + self._alpha * r * r
                + self._beta * variance
            )
            # Floor to prevent numerical collapse.
            variance = max(_VOL_EPSILON ** 2, variance)

        # Update internal state.
        self._current_variance = variance

        volatility: float = max(_VOL_EPSILON, math.sqrt(variance))
        long_run_vol: float = max(_VOL_EPSILON, math.sqrt(self._long_run_variance))

        return VolResult(
            volatility=volatility,
            variance=variance,
            long_run_volatility=long_run_vol,
            n_clean_returns=n_clean,
            nan_replaced=nan_replaced,
        )

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def xǁVolatilityTrackerǁestimate_volatility__mutmut_18(self, returns: List[float]) -> VolResult:
        """
        Update the GARCH(1,1) model with a sequence of return observations
        and return the resulting volatility estimate.

        Non-finite values (NaN, Inf) are replaced with 0.0 and counted
        in nan_replaced. Empty or all-non-finite lists raise ValueError.

        The model is updated sequentially: for each return r_t,
          sigma^2_{t+1} = omega + alpha * r_t^2 + beta * sigma^2_t

        After processing all returns, self._current_variance holds the
        most recent conditional variance.

        Parameters
        ----------
        returns : List[float]
            Sequence of per-period returns. Must be non-empty.
            Non-finite values are replaced with 0.0.

        Returns
        -------
        VolResult
            Volatility estimate derived from the final variance state.

        Raises
        ------
        ValueError
            If returns is empty.
        TypeError
            If returns is None.
        """
        if returns is None:
            raise TypeError("returns must be a list, got None.")
        if len(returns) == 0:
            raise ValueError("returns must be non-empty.")

        # Clean returns: replace non-finite with 0.0.
        nan_replaced: int = 0
        clean: List[float] = []
        for r in returns:
            if math.isfinite(r):
                clean.append(r)
            else:
                clean.append(0.0)
                nan_replaced = 1

        n_clean: int = len(returns) - nan_replaced

        # Sequential GARCH update.
        variance: float = self._current_variance
        for r in clean:
            variance = (
                self._omega
                + self._alpha * r * r
                + self._beta * variance
            )
            # Floor to prevent numerical collapse.
            variance = max(_VOL_EPSILON ** 2, variance)

        # Update internal state.
        self._current_variance = variance

        volatility: float = max(_VOL_EPSILON, math.sqrt(variance))
        long_run_vol: float = max(_VOL_EPSILON, math.sqrt(self._long_run_variance))

        return VolResult(
            volatility=volatility,
            variance=variance,
            long_run_volatility=long_run_vol,
            n_clean_returns=n_clean,
            nan_replaced=nan_replaced,
        )

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def xǁVolatilityTrackerǁestimate_volatility__mutmut_19(self, returns: List[float]) -> VolResult:
        """
        Update the GARCH(1,1) model with a sequence of return observations
        and return the resulting volatility estimate.

        Non-finite values (NaN, Inf) are replaced with 0.0 and counted
        in nan_replaced. Empty or all-non-finite lists raise ValueError.

        The model is updated sequentially: for each return r_t,
          sigma^2_{t+1} = omega + alpha * r_t^2 + beta * sigma^2_t

        After processing all returns, self._current_variance holds the
        most recent conditional variance.

        Parameters
        ----------
        returns : List[float]
            Sequence of per-period returns. Must be non-empty.
            Non-finite values are replaced with 0.0.

        Returns
        -------
        VolResult
            Volatility estimate derived from the final variance state.

        Raises
        ------
        ValueError
            If returns is empty.
        TypeError
            If returns is None.
        """
        if returns is None:
            raise TypeError("returns must be a list, got None.")
        if len(returns) == 0:
            raise ValueError("returns must be non-empty.")

        # Clean returns: replace non-finite with 0.0.
        nan_replaced: int = 0
        clean: List[float] = []
        for r in returns:
            if math.isfinite(r):
                clean.append(r)
            else:
                clean.append(0.0)
                nan_replaced -= 1

        n_clean: int = len(returns) - nan_replaced

        # Sequential GARCH update.
        variance: float = self._current_variance
        for r in clean:
            variance = (
                self._omega
                + self._alpha * r * r
                + self._beta * variance
            )
            # Floor to prevent numerical collapse.
            variance = max(_VOL_EPSILON ** 2, variance)

        # Update internal state.
        self._current_variance = variance

        volatility: float = max(_VOL_EPSILON, math.sqrt(variance))
        long_run_vol: float = max(_VOL_EPSILON, math.sqrt(self._long_run_variance))

        return VolResult(
            volatility=volatility,
            variance=variance,
            long_run_volatility=long_run_vol,
            n_clean_returns=n_clean,
            nan_replaced=nan_replaced,
        )

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def xǁVolatilityTrackerǁestimate_volatility__mutmut_20(self, returns: List[float]) -> VolResult:
        """
        Update the GARCH(1,1) model with a sequence of return observations
        and return the resulting volatility estimate.

        Non-finite values (NaN, Inf) are replaced with 0.0 and counted
        in nan_replaced. Empty or all-non-finite lists raise ValueError.

        The model is updated sequentially: for each return r_t,
          sigma^2_{t+1} = omega + alpha * r_t^2 + beta * sigma^2_t

        After processing all returns, self._current_variance holds the
        most recent conditional variance.

        Parameters
        ----------
        returns : List[float]
            Sequence of per-period returns. Must be non-empty.
            Non-finite values are replaced with 0.0.

        Returns
        -------
        VolResult
            Volatility estimate derived from the final variance state.

        Raises
        ------
        ValueError
            If returns is empty.
        TypeError
            If returns is None.
        """
        if returns is None:
            raise TypeError("returns must be a list, got None.")
        if len(returns) == 0:
            raise ValueError("returns must be non-empty.")

        # Clean returns: replace non-finite with 0.0.
        nan_replaced: int = 0
        clean: List[float] = []
        for r in returns:
            if math.isfinite(r):
                clean.append(r)
            else:
                clean.append(0.0)
                nan_replaced += 2

        n_clean: int = len(returns) - nan_replaced

        # Sequential GARCH update.
        variance: float = self._current_variance
        for r in clean:
            variance = (
                self._omega
                + self._alpha * r * r
                + self._beta * variance
            )
            # Floor to prevent numerical collapse.
            variance = max(_VOL_EPSILON ** 2, variance)

        # Update internal state.
        self._current_variance = variance

        volatility: float = max(_VOL_EPSILON, math.sqrt(variance))
        long_run_vol: float = max(_VOL_EPSILON, math.sqrt(self._long_run_variance))

        return VolResult(
            volatility=volatility,
            variance=variance,
            long_run_volatility=long_run_vol,
            n_clean_returns=n_clean,
            nan_replaced=nan_replaced,
        )

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def xǁVolatilityTrackerǁestimate_volatility__mutmut_21(self, returns: List[float]) -> VolResult:
        """
        Update the GARCH(1,1) model with a sequence of return observations
        and return the resulting volatility estimate.

        Non-finite values (NaN, Inf) are replaced with 0.0 and counted
        in nan_replaced. Empty or all-non-finite lists raise ValueError.

        The model is updated sequentially: for each return r_t,
          sigma^2_{t+1} = omega + alpha * r_t^2 + beta * sigma^2_t

        After processing all returns, self._current_variance holds the
        most recent conditional variance.

        Parameters
        ----------
        returns : List[float]
            Sequence of per-period returns. Must be non-empty.
            Non-finite values are replaced with 0.0.

        Returns
        -------
        VolResult
            Volatility estimate derived from the final variance state.

        Raises
        ------
        ValueError
            If returns is empty.
        TypeError
            If returns is None.
        """
        if returns is None:
            raise TypeError("returns must be a list, got None.")
        if len(returns) == 0:
            raise ValueError("returns must be non-empty.")

        # Clean returns: replace non-finite with 0.0.
        nan_replaced: int = 0
        clean: List[float] = []
        for r in returns:
            if math.isfinite(r):
                clean.append(r)
            else:
                clean.append(0.0)
                nan_replaced += 1

        n_clean: int = None

        # Sequential GARCH update.
        variance: float = self._current_variance
        for r in clean:
            variance = (
                self._omega
                + self._alpha * r * r
                + self._beta * variance
            )
            # Floor to prevent numerical collapse.
            variance = max(_VOL_EPSILON ** 2, variance)

        # Update internal state.
        self._current_variance = variance

        volatility: float = max(_VOL_EPSILON, math.sqrt(variance))
        long_run_vol: float = max(_VOL_EPSILON, math.sqrt(self._long_run_variance))

        return VolResult(
            volatility=volatility,
            variance=variance,
            long_run_volatility=long_run_vol,
            n_clean_returns=n_clean,
            nan_replaced=nan_replaced,
        )

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def xǁVolatilityTrackerǁestimate_volatility__mutmut_22(self, returns: List[float]) -> VolResult:
        """
        Update the GARCH(1,1) model with a sequence of return observations
        and return the resulting volatility estimate.

        Non-finite values (NaN, Inf) are replaced with 0.0 and counted
        in nan_replaced. Empty or all-non-finite lists raise ValueError.

        The model is updated sequentially: for each return r_t,
          sigma^2_{t+1} = omega + alpha * r_t^2 + beta * sigma^2_t

        After processing all returns, self._current_variance holds the
        most recent conditional variance.

        Parameters
        ----------
        returns : List[float]
            Sequence of per-period returns. Must be non-empty.
            Non-finite values are replaced with 0.0.

        Returns
        -------
        VolResult
            Volatility estimate derived from the final variance state.

        Raises
        ------
        ValueError
            If returns is empty.
        TypeError
            If returns is None.
        """
        if returns is None:
            raise TypeError("returns must be a list, got None.")
        if len(returns) == 0:
            raise ValueError("returns must be non-empty.")

        # Clean returns: replace non-finite with 0.0.
        nan_replaced: int = 0
        clean: List[float] = []
        for r in returns:
            if math.isfinite(r):
                clean.append(r)
            else:
                clean.append(0.0)
                nan_replaced += 1

        n_clean: int = len(returns) + nan_replaced

        # Sequential GARCH update.
        variance: float = self._current_variance
        for r in clean:
            variance = (
                self._omega
                + self._alpha * r * r
                + self._beta * variance
            )
            # Floor to prevent numerical collapse.
            variance = max(_VOL_EPSILON ** 2, variance)

        # Update internal state.
        self._current_variance = variance

        volatility: float = max(_VOL_EPSILON, math.sqrt(variance))
        long_run_vol: float = max(_VOL_EPSILON, math.sqrt(self._long_run_variance))

        return VolResult(
            volatility=volatility,
            variance=variance,
            long_run_volatility=long_run_vol,
            n_clean_returns=n_clean,
            nan_replaced=nan_replaced,
        )

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def xǁVolatilityTrackerǁestimate_volatility__mutmut_23(self, returns: List[float]) -> VolResult:
        """
        Update the GARCH(1,1) model with a sequence of return observations
        and return the resulting volatility estimate.

        Non-finite values (NaN, Inf) are replaced with 0.0 and counted
        in nan_replaced. Empty or all-non-finite lists raise ValueError.

        The model is updated sequentially: for each return r_t,
          sigma^2_{t+1} = omega + alpha * r_t^2 + beta * sigma^2_t

        After processing all returns, self._current_variance holds the
        most recent conditional variance.

        Parameters
        ----------
        returns : List[float]
            Sequence of per-period returns. Must be non-empty.
            Non-finite values are replaced with 0.0.

        Returns
        -------
        VolResult
            Volatility estimate derived from the final variance state.

        Raises
        ------
        ValueError
            If returns is empty.
        TypeError
            If returns is None.
        """
        if returns is None:
            raise TypeError("returns must be a list, got None.")
        if len(returns) == 0:
            raise ValueError("returns must be non-empty.")

        # Clean returns: replace non-finite with 0.0.
        nan_replaced: int = 0
        clean: List[float] = []
        for r in returns:
            if math.isfinite(r):
                clean.append(r)
            else:
                clean.append(0.0)
                nan_replaced += 1

        n_clean: int = len(returns) - nan_replaced

        # Sequential GARCH update.
        variance: float = None
        for r in clean:
            variance = (
                self._omega
                + self._alpha * r * r
                + self._beta * variance
            )
            # Floor to prevent numerical collapse.
            variance = max(_VOL_EPSILON ** 2, variance)

        # Update internal state.
        self._current_variance = variance

        volatility: float = max(_VOL_EPSILON, math.sqrt(variance))
        long_run_vol: float = max(_VOL_EPSILON, math.sqrt(self._long_run_variance))

        return VolResult(
            volatility=volatility,
            variance=variance,
            long_run_volatility=long_run_vol,
            n_clean_returns=n_clean,
            nan_replaced=nan_replaced,
        )

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def xǁVolatilityTrackerǁestimate_volatility__mutmut_24(self, returns: List[float]) -> VolResult:
        """
        Update the GARCH(1,1) model with a sequence of return observations
        and return the resulting volatility estimate.

        Non-finite values (NaN, Inf) are replaced with 0.0 and counted
        in nan_replaced. Empty or all-non-finite lists raise ValueError.

        The model is updated sequentially: for each return r_t,
          sigma^2_{t+1} = omega + alpha * r_t^2 + beta * sigma^2_t

        After processing all returns, self._current_variance holds the
        most recent conditional variance.

        Parameters
        ----------
        returns : List[float]
            Sequence of per-period returns. Must be non-empty.
            Non-finite values are replaced with 0.0.

        Returns
        -------
        VolResult
            Volatility estimate derived from the final variance state.

        Raises
        ------
        ValueError
            If returns is empty.
        TypeError
            If returns is None.
        """
        if returns is None:
            raise TypeError("returns must be a list, got None.")
        if len(returns) == 0:
            raise ValueError("returns must be non-empty.")

        # Clean returns: replace non-finite with 0.0.
        nan_replaced: int = 0
        clean: List[float] = []
        for r in returns:
            if math.isfinite(r):
                clean.append(r)
            else:
                clean.append(0.0)
                nan_replaced += 1

        n_clean: int = len(returns) - nan_replaced

        # Sequential GARCH update.
        variance: float = self._current_variance
        for r in clean:
            variance = None
            # Floor to prevent numerical collapse.
            variance = max(_VOL_EPSILON ** 2, variance)

        # Update internal state.
        self._current_variance = variance

        volatility: float = max(_VOL_EPSILON, math.sqrt(variance))
        long_run_vol: float = max(_VOL_EPSILON, math.sqrt(self._long_run_variance))

        return VolResult(
            volatility=volatility,
            variance=variance,
            long_run_volatility=long_run_vol,
            n_clean_returns=n_clean,
            nan_replaced=nan_replaced,
        )

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def xǁVolatilityTrackerǁestimate_volatility__mutmut_25(self, returns: List[float]) -> VolResult:
        """
        Update the GARCH(1,1) model with a sequence of return observations
        and return the resulting volatility estimate.

        Non-finite values (NaN, Inf) are replaced with 0.0 and counted
        in nan_replaced. Empty or all-non-finite lists raise ValueError.

        The model is updated sequentially: for each return r_t,
          sigma^2_{t+1} = omega + alpha * r_t^2 + beta * sigma^2_t

        After processing all returns, self._current_variance holds the
        most recent conditional variance.

        Parameters
        ----------
        returns : List[float]
            Sequence of per-period returns. Must be non-empty.
            Non-finite values are replaced with 0.0.

        Returns
        -------
        VolResult
            Volatility estimate derived from the final variance state.

        Raises
        ------
        ValueError
            If returns is empty.
        TypeError
            If returns is None.
        """
        if returns is None:
            raise TypeError("returns must be a list, got None.")
        if len(returns) == 0:
            raise ValueError("returns must be non-empty.")

        # Clean returns: replace non-finite with 0.0.
        nan_replaced: int = 0
        clean: List[float] = []
        for r in returns:
            if math.isfinite(r):
                clean.append(r)
            else:
                clean.append(0.0)
                nan_replaced += 1

        n_clean: int = len(returns) - nan_replaced

        # Sequential GARCH update.
        variance: float = self._current_variance
        for r in clean:
            variance = (
                self._omega
                + self._alpha * r * r - self._beta * variance
            )
            # Floor to prevent numerical collapse.
            variance = max(_VOL_EPSILON ** 2, variance)

        # Update internal state.
        self._current_variance = variance

        volatility: float = max(_VOL_EPSILON, math.sqrt(variance))
        long_run_vol: float = max(_VOL_EPSILON, math.sqrt(self._long_run_variance))

        return VolResult(
            volatility=volatility,
            variance=variance,
            long_run_volatility=long_run_vol,
            n_clean_returns=n_clean,
            nan_replaced=nan_replaced,
        )

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def xǁVolatilityTrackerǁestimate_volatility__mutmut_26(self, returns: List[float]) -> VolResult:
        """
        Update the GARCH(1,1) model with a sequence of return observations
        and return the resulting volatility estimate.

        Non-finite values (NaN, Inf) are replaced with 0.0 and counted
        in nan_replaced. Empty or all-non-finite lists raise ValueError.

        The model is updated sequentially: for each return r_t,
          sigma^2_{t+1} = omega + alpha * r_t^2 + beta * sigma^2_t

        After processing all returns, self._current_variance holds the
        most recent conditional variance.

        Parameters
        ----------
        returns : List[float]
            Sequence of per-period returns. Must be non-empty.
            Non-finite values are replaced with 0.0.

        Returns
        -------
        VolResult
            Volatility estimate derived from the final variance state.

        Raises
        ------
        ValueError
            If returns is empty.
        TypeError
            If returns is None.
        """
        if returns is None:
            raise TypeError("returns must be a list, got None.")
        if len(returns) == 0:
            raise ValueError("returns must be non-empty.")

        # Clean returns: replace non-finite with 0.0.
        nan_replaced: int = 0
        clean: List[float] = []
        for r in returns:
            if math.isfinite(r):
                clean.append(r)
            else:
                clean.append(0.0)
                nan_replaced += 1

        n_clean: int = len(returns) - nan_replaced

        # Sequential GARCH update.
        variance: float = self._current_variance
        for r in clean:
            variance = (
                self._omega - self._alpha * r * r
                + self._beta * variance
            )
            # Floor to prevent numerical collapse.
            variance = max(_VOL_EPSILON ** 2, variance)

        # Update internal state.
        self._current_variance = variance

        volatility: float = max(_VOL_EPSILON, math.sqrt(variance))
        long_run_vol: float = max(_VOL_EPSILON, math.sqrt(self._long_run_variance))

        return VolResult(
            volatility=volatility,
            variance=variance,
            long_run_volatility=long_run_vol,
            n_clean_returns=n_clean,
            nan_replaced=nan_replaced,
        )

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def xǁVolatilityTrackerǁestimate_volatility__mutmut_27(self, returns: List[float]) -> VolResult:
        """
        Update the GARCH(1,1) model with a sequence of return observations
        and return the resulting volatility estimate.

        Non-finite values (NaN, Inf) are replaced with 0.0 and counted
        in nan_replaced. Empty or all-non-finite lists raise ValueError.

        The model is updated sequentially: for each return r_t,
          sigma^2_{t+1} = omega + alpha * r_t^2 + beta * sigma^2_t

        After processing all returns, self._current_variance holds the
        most recent conditional variance.

        Parameters
        ----------
        returns : List[float]
            Sequence of per-period returns. Must be non-empty.
            Non-finite values are replaced with 0.0.

        Returns
        -------
        VolResult
            Volatility estimate derived from the final variance state.

        Raises
        ------
        ValueError
            If returns is empty.
        TypeError
            If returns is None.
        """
        if returns is None:
            raise TypeError("returns must be a list, got None.")
        if len(returns) == 0:
            raise ValueError("returns must be non-empty.")

        # Clean returns: replace non-finite with 0.0.
        nan_replaced: int = 0
        clean: List[float] = []
        for r in returns:
            if math.isfinite(r):
                clean.append(r)
            else:
                clean.append(0.0)
                nan_replaced += 1

        n_clean: int = len(returns) - nan_replaced

        # Sequential GARCH update.
        variance: float = self._current_variance
        for r in clean:
            variance = (
                self._omega
                + self._alpha * r / r
                + self._beta * variance
            )
            # Floor to prevent numerical collapse.
            variance = max(_VOL_EPSILON ** 2, variance)

        # Update internal state.
        self._current_variance = variance

        volatility: float = max(_VOL_EPSILON, math.sqrt(variance))
        long_run_vol: float = max(_VOL_EPSILON, math.sqrt(self._long_run_variance))

        return VolResult(
            volatility=volatility,
            variance=variance,
            long_run_volatility=long_run_vol,
            n_clean_returns=n_clean,
            nan_replaced=nan_replaced,
        )

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def xǁVolatilityTrackerǁestimate_volatility__mutmut_28(self, returns: List[float]) -> VolResult:
        """
        Update the GARCH(1,1) model with a sequence of return observations
        and return the resulting volatility estimate.

        Non-finite values (NaN, Inf) are replaced with 0.0 and counted
        in nan_replaced. Empty or all-non-finite lists raise ValueError.

        The model is updated sequentially: for each return r_t,
          sigma^2_{t+1} = omega + alpha * r_t^2 + beta * sigma^2_t

        After processing all returns, self._current_variance holds the
        most recent conditional variance.

        Parameters
        ----------
        returns : List[float]
            Sequence of per-period returns. Must be non-empty.
            Non-finite values are replaced with 0.0.

        Returns
        -------
        VolResult
            Volatility estimate derived from the final variance state.

        Raises
        ------
        ValueError
            If returns is empty.
        TypeError
            If returns is None.
        """
        if returns is None:
            raise TypeError("returns must be a list, got None.")
        if len(returns) == 0:
            raise ValueError("returns must be non-empty.")

        # Clean returns: replace non-finite with 0.0.
        nan_replaced: int = 0
        clean: List[float] = []
        for r in returns:
            if math.isfinite(r):
                clean.append(r)
            else:
                clean.append(0.0)
                nan_replaced += 1

        n_clean: int = len(returns) - nan_replaced

        # Sequential GARCH update.
        variance: float = self._current_variance
        for r in clean:
            variance = (
                self._omega
                + self._alpha / r * r
                + self._beta * variance
            )
            # Floor to prevent numerical collapse.
            variance = max(_VOL_EPSILON ** 2, variance)

        # Update internal state.
        self._current_variance = variance

        volatility: float = max(_VOL_EPSILON, math.sqrt(variance))
        long_run_vol: float = max(_VOL_EPSILON, math.sqrt(self._long_run_variance))

        return VolResult(
            volatility=volatility,
            variance=variance,
            long_run_volatility=long_run_vol,
            n_clean_returns=n_clean,
            nan_replaced=nan_replaced,
        )

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def xǁVolatilityTrackerǁestimate_volatility__mutmut_29(self, returns: List[float]) -> VolResult:
        """
        Update the GARCH(1,1) model with a sequence of return observations
        and return the resulting volatility estimate.

        Non-finite values (NaN, Inf) are replaced with 0.0 and counted
        in nan_replaced. Empty or all-non-finite lists raise ValueError.

        The model is updated sequentially: for each return r_t,
          sigma^2_{t+1} = omega + alpha * r_t^2 + beta * sigma^2_t

        After processing all returns, self._current_variance holds the
        most recent conditional variance.

        Parameters
        ----------
        returns : List[float]
            Sequence of per-period returns. Must be non-empty.
            Non-finite values are replaced with 0.0.

        Returns
        -------
        VolResult
            Volatility estimate derived from the final variance state.

        Raises
        ------
        ValueError
            If returns is empty.
        TypeError
            If returns is None.
        """
        if returns is None:
            raise TypeError("returns must be a list, got None.")
        if len(returns) == 0:
            raise ValueError("returns must be non-empty.")

        # Clean returns: replace non-finite with 0.0.
        nan_replaced: int = 0
        clean: List[float] = []
        for r in returns:
            if math.isfinite(r):
                clean.append(r)
            else:
                clean.append(0.0)
                nan_replaced += 1

        n_clean: int = len(returns) - nan_replaced

        # Sequential GARCH update.
        variance: float = self._current_variance
        for r in clean:
            variance = (
                self._omega
                + self._alpha * r * r
                + self._beta / variance
            )
            # Floor to prevent numerical collapse.
            variance = max(_VOL_EPSILON ** 2, variance)

        # Update internal state.
        self._current_variance = variance

        volatility: float = max(_VOL_EPSILON, math.sqrt(variance))
        long_run_vol: float = max(_VOL_EPSILON, math.sqrt(self._long_run_variance))

        return VolResult(
            volatility=volatility,
            variance=variance,
            long_run_volatility=long_run_vol,
            n_clean_returns=n_clean,
            nan_replaced=nan_replaced,
        )

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def xǁVolatilityTrackerǁestimate_volatility__mutmut_30(self, returns: List[float]) -> VolResult:
        """
        Update the GARCH(1,1) model with a sequence of return observations
        and return the resulting volatility estimate.

        Non-finite values (NaN, Inf) are replaced with 0.0 and counted
        in nan_replaced. Empty or all-non-finite lists raise ValueError.

        The model is updated sequentially: for each return r_t,
          sigma^2_{t+1} = omega + alpha * r_t^2 + beta * sigma^2_t

        After processing all returns, self._current_variance holds the
        most recent conditional variance.

        Parameters
        ----------
        returns : List[float]
            Sequence of per-period returns. Must be non-empty.
            Non-finite values are replaced with 0.0.

        Returns
        -------
        VolResult
            Volatility estimate derived from the final variance state.

        Raises
        ------
        ValueError
            If returns is empty.
        TypeError
            If returns is None.
        """
        if returns is None:
            raise TypeError("returns must be a list, got None.")
        if len(returns) == 0:
            raise ValueError("returns must be non-empty.")

        # Clean returns: replace non-finite with 0.0.
        nan_replaced: int = 0
        clean: List[float] = []
        for r in returns:
            if math.isfinite(r):
                clean.append(r)
            else:
                clean.append(0.0)
                nan_replaced += 1

        n_clean: int = len(returns) - nan_replaced

        # Sequential GARCH update.
        variance: float = self._current_variance
        for r in clean:
            variance = (
                self._omega
                + self._alpha * r * r
                + self._beta * variance
            )
            # Floor to prevent numerical collapse.
            variance = None

        # Update internal state.
        self._current_variance = variance

        volatility: float = max(_VOL_EPSILON, math.sqrt(variance))
        long_run_vol: float = max(_VOL_EPSILON, math.sqrt(self._long_run_variance))

        return VolResult(
            volatility=volatility,
            variance=variance,
            long_run_volatility=long_run_vol,
            n_clean_returns=n_clean,
            nan_replaced=nan_replaced,
        )

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def xǁVolatilityTrackerǁestimate_volatility__mutmut_31(self, returns: List[float]) -> VolResult:
        """
        Update the GARCH(1,1) model with a sequence of return observations
        and return the resulting volatility estimate.

        Non-finite values (NaN, Inf) are replaced with 0.0 and counted
        in nan_replaced. Empty or all-non-finite lists raise ValueError.

        The model is updated sequentially: for each return r_t,
          sigma^2_{t+1} = omega + alpha * r_t^2 + beta * sigma^2_t

        After processing all returns, self._current_variance holds the
        most recent conditional variance.

        Parameters
        ----------
        returns : List[float]
            Sequence of per-period returns. Must be non-empty.
            Non-finite values are replaced with 0.0.

        Returns
        -------
        VolResult
            Volatility estimate derived from the final variance state.

        Raises
        ------
        ValueError
            If returns is empty.
        TypeError
            If returns is None.
        """
        if returns is None:
            raise TypeError("returns must be a list, got None.")
        if len(returns) == 0:
            raise ValueError("returns must be non-empty.")

        # Clean returns: replace non-finite with 0.0.
        nan_replaced: int = 0
        clean: List[float] = []
        for r in returns:
            if math.isfinite(r):
                clean.append(r)
            else:
                clean.append(0.0)
                nan_replaced += 1

        n_clean: int = len(returns) - nan_replaced

        # Sequential GARCH update.
        variance: float = self._current_variance
        for r in clean:
            variance = (
                self._omega
                + self._alpha * r * r
                + self._beta * variance
            )
            # Floor to prevent numerical collapse.
            variance = max(None, variance)

        # Update internal state.
        self._current_variance = variance

        volatility: float = max(_VOL_EPSILON, math.sqrt(variance))
        long_run_vol: float = max(_VOL_EPSILON, math.sqrt(self._long_run_variance))

        return VolResult(
            volatility=volatility,
            variance=variance,
            long_run_volatility=long_run_vol,
            n_clean_returns=n_clean,
            nan_replaced=nan_replaced,
        )

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def xǁVolatilityTrackerǁestimate_volatility__mutmut_32(self, returns: List[float]) -> VolResult:
        """
        Update the GARCH(1,1) model with a sequence of return observations
        and return the resulting volatility estimate.

        Non-finite values (NaN, Inf) are replaced with 0.0 and counted
        in nan_replaced. Empty or all-non-finite lists raise ValueError.

        The model is updated sequentially: for each return r_t,
          sigma^2_{t+1} = omega + alpha * r_t^2 + beta * sigma^2_t

        After processing all returns, self._current_variance holds the
        most recent conditional variance.

        Parameters
        ----------
        returns : List[float]
            Sequence of per-period returns. Must be non-empty.
            Non-finite values are replaced with 0.0.

        Returns
        -------
        VolResult
            Volatility estimate derived from the final variance state.

        Raises
        ------
        ValueError
            If returns is empty.
        TypeError
            If returns is None.
        """
        if returns is None:
            raise TypeError("returns must be a list, got None.")
        if len(returns) == 0:
            raise ValueError("returns must be non-empty.")

        # Clean returns: replace non-finite with 0.0.
        nan_replaced: int = 0
        clean: List[float] = []
        for r in returns:
            if math.isfinite(r):
                clean.append(r)
            else:
                clean.append(0.0)
                nan_replaced += 1

        n_clean: int = len(returns) - nan_replaced

        # Sequential GARCH update.
        variance: float = self._current_variance
        for r in clean:
            variance = (
                self._omega
                + self._alpha * r * r
                + self._beta * variance
            )
            # Floor to prevent numerical collapse.
            variance = max(_VOL_EPSILON ** 2, None)

        # Update internal state.
        self._current_variance = variance

        volatility: float = max(_VOL_EPSILON, math.sqrt(variance))
        long_run_vol: float = max(_VOL_EPSILON, math.sqrt(self._long_run_variance))

        return VolResult(
            volatility=volatility,
            variance=variance,
            long_run_volatility=long_run_vol,
            n_clean_returns=n_clean,
            nan_replaced=nan_replaced,
        )

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def xǁVolatilityTrackerǁestimate_volatility__mutmut_33(self, returns: List[float]) -> VolResult:
        """
        Update the GARCH(1,1) model with a sequence of return observations
        and return the resulting volatility estimate.

        Non-finite values (NaN, Inf) are replaced with 0.0 and counted
        in nan_replaced. Empty or all-non-finite lists raise ValueError.

        The model is updated sequentially: for each return r_t,
          sigma^2_{t+1} = omega + alpha * r_t^2 + beta * sigma^2_t

        After processing all returns, self._current_variance holds the
        most recent conditional variance.

        Parameters
        ----------
        returns : List[float]
            Sequence of per-period returns. Must be non-empty.
            Non-finite values are replaced with 0.0.

        Returns
        -------
        VolResult
            Volatility estimate derived from the final variance state.

        Raises
        ------
        ValueError
            If returns is empty.
        TypeError
            If returns is None.
        """
        if returns is None:
            raise TypeError("returns must be a list, got None.")
        if len(returns) == 0:
            raise ValueError("returns must be non-empty.")

        # Clean returns: replace non-finite with 0.0.
        nan_replaced: int = 0
        clean: List[float] = []
        for r in returns:
            if math.isfinite(r):
                clean.append(r)
            else:
                clean.append(0.0)
                nan_replaced += 1

        n_clean: int = len(returns) - nan_replaced

        # Sequential GARCH update.
        variance: float = self._current_variance
        for r in clean:
            variance = (
                self._omega
                + self._alpha * r * r
                + self._beta * variance
            )
            # Floor to prevent numerical collapse.
            variance = max(variance)

        # Update internal state.
        self._current_variance = variance

        volatility: float = max(_VOL_EPSILON, math.sqrt(variance))
        long_run_vol: float = max(_VOL_EPSILON, math.sqrt(self._long_run_variance))

        return VolResult(
            volatility=volatility,
            variance=variance,
            long_run_volatility=long_run_vol,
            n_clean_returns=n_clean,
            nan_replaced=nan_replaced,
        )

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def xǁVolatilityTrackerǁestimate_volatility__mutmut_34(self, returns: List[float]) -> VolResult:
        """
        Update the GARCH(1,1) model with a sequence of return observations
        and return the resulting volatility estimate.

        Non-finite values (NaN, Inf) are replaced with 0.0 and counted
        in nan_replaced. Empty or all-non-finite lists raise ValueError.

        The model is updated sequentially: for each return r_t,
          sigma^2_{t+1} = omega + alpha * r_t^2 + beta * sigma^2_t

        After processing all returns, self._current_variance holds the
        most recent conditional variance.

        Parameters
        ----------
        returns : List[float]
            Sequence of per-period returns. Must be non-empty.
            Non-finite values are replaced with 0.0.

        Returns
        -------
        VolResult
            Volatility estimate derived from the final variance state.

        Raises
        ------
        ValueError
            If returns is empty.
        TypeError
            If returns is None.
        """
        if returns is None:
            raise TypeError("returns must be a list, got None.")
        if len(returns) == 0:
            raise ValueError("returns must be non-empty.")

        # Clean returns: replace non-finite with 0.0.
        nan_replaced: int = 0
        clean: List[float] = []
        for r in returns:
            if math.isfinite(r):
                clean.append(r)
            else:
                clean.append(0.0)
                nan_replaced += 1

        n_clean: int = len(returns) - nan_replaced

        # Sequential GARCH update.
        variance: float = self._current_variance
        for r in clean:
            variance = (
                self._omega
                + self._alpha * r * r
                + self._beta * variance
            )
            # Floor to prevent numerical collapse.
            variance = max(_VOL_EPSILON ** 2, )

        # Update internal state.
        self._current_variance = variance

        volatility: float = max(_VOL_EPSILON, math.sqrt(variance))
        long_run_vol: float = max(_VOL_EPSILON, math.sqrt(self._long_run_variance))

        return VolResult(
            volatility=volatility,
            variance=variance,
            long_run_volatility=long_run_vol,
            n_clean_returns=n_clean,
            nan_replaced=nan_replaced,
        )

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def xǁVolatilityTrackerǁestimate_volatility__mutmut_35(self, returns: List[float]) -> VolResult:
        """
        Update the GARCH(1,1) model with a sequence of return observations
        and return the resulting volatility estimate.

        Non-finite values (NaN, Inf) are replaced with 0.0 and counted
        in nan_replaced. Empty or all-non-finite lists raise ValueError.

        The model is updated sequentially: for each return r_t,
          sigma^2_{t+1} = omega + alpha * r_t^2 + beta * sigma^2_t

        After processing all returns, self._current_variance holds the
        most recent conditional variance.

        Parameters
        ----------
        returns : List[float]
            Sequence of per-period returns. Must be non-empty.
            Non-finite values are replaced with 0.0.

        Returns
        -------
        VolResult
            Volatility estimate derived from the final variance state.

        Raises
        ------
        ValueError
            If returns is empty.
        TypeError
            If returns is None.
        """
        if returns is None:
            raise TypeError("returns must be a list, got None.")
        if len(returns) == 0:
            raise ValueError("returns must be non-empty.")

        # Clean returns: replace non-finite with 0.0.
        nan_replaced: int = 0
        clean: List[float] = []
        for r in returns:
            if math.isfinite(r):
                clean.append(r)
            else:
                clean.append(0.0)
                nan_replaced += 1

        n_clean: int = len(returns) - nan_replaced

        # Sequential GARCH update.
        variance: float = self._current_variance
        for r in clean:
            variance = (
                self._omega
                + self._alpha * r * r
                + self._beta * variance
            )
            # Floor to prevent numerical collapse.
            variance = max(_VOL_EPSILON * 2, variance)

        # Update internal state.
        self._current_variance = variance

        volatility: float = max(_VOL_EPSILON, math.sqrt(variance))
        long_run_vol: float = max(_VOL_EPSILON, math.sqrt(self._long_run_variance))

        return VolResult(
            volatility=volatility,
            variance=variance,
            long_run_volatility=long_run_vol,
            n_clean_returns=n_clean,
            nan_replaced=nan_replaced,
        )

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def xǁVolatilityTrackerǁestimate_volatility__mutmut_36(self, returns: List[float]) -> VolResult:
        """
        Update the GARCH(1,1) model with a sequence of return observations
        and return the resulting volatility estimate.

        Non-finite values (NaN, Inf) are replaced with 0.0 and counted
        in nan_replaced. Empty or all-non-finite lists raise ValueError.

        The model is updated sequentially: for each return r_t,
          sigma^2_{t+1} = omega + alpha * r_t^2 + beta * sigma^2_t

        After processing all returns, self._current_variance holds the
        most recent conditional variance.

        Parameters
        ----------
        returns : List[float]
            Sequence of per-period returns. Must be non-empty.
            Non-finite values are replaced with 0.0.

        Returns
        -------
        VolResult
            Volatility estimate derived from the final variance state.

        Raises
        ------
        ValueError
            If returns is empty.
        TypeError
            If returns is None.
        """
        if returns is None:
            raise TypeError("returns must be a list, got None.")
        if len(returns) == 0:
            raise ValueError("returns must be non-empty.")

        # Clean returns: replace non-finite with 0.0.
        nan_replaced: int = 0
        clean: List[float] = []
        for r in returns:
            if math.isfinite(r):
                clean.append(r)
            else:
                clean.append(0.0)
                nan_replaced += 1

        n_clean: int = len(returns) - nan_replaced

        # Sequential GARCH update.
        variance: float = self._current_variance
        for r in clean:
            variance = (
                self._omega
                + self._alpha * r * r
                + self._beta * variance
            )
            # Floor to prevent numerical collapse.
            variance = max(_VOL_EPSILON ** 3, variance)

        # Update internal state.
        self._current_variance = variance

        volatility: float = max(_VOL_EPSILON, math.sqrt(variance))
        long_run_vol: float = max(_VOL_EPSILON, math.sqrt(self._long_run_variance))

        return VolResult(
            volatility=volatility,
            variance=variance,
            long_run_volatility=long_run_vol,
            n_clean_returns=n_clean,
            nan_replaced=nan_replaced,
        )

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def xǁVolatilityTrackerǁestimate_volatility__mutmut_37(self, returns: List[float]) -> VolResult:
        """
        Update the GARCH(1,1) model with a sequence of return observations
        and return the resulting volatility estimate.

        Non-finite values (NaN, Inf) are replaced with 0.0 and counted
        in nan_replaced. Empty or all-non-finite lists raise ValueError.

        The model is updated sequentially: for each return r_t,
          sigma^2_{t+1} = omega + alpha * r_t^2 + beta * sigma^2_t

        After processing all returns, self._current_variance holds the
        most recent conditional variance.

        Parameters
        ----------
        returns : List[float]
            Sequence of per-period returns. Must be non-empty.
            Non-finite values are replaced with 0.0.

        Returns
        -------
        VolResult
            Volatility estimate derived from the final variance state.

        Raises
        ------
        ValueError
            If returns is empty.
        TypeError
            If returns is None.
        """
        if returns is None:
            raise TypeError("returns must be a list, got None.")
        if len(returns) == 0:
            raise ValueError("returns must be non-empty.")

        # Clean returns: replace non-finite with 0.0.
        nan_replaced: int = 0
        clean: List[float] = []
        for r in returns:
            if math.isfinite(r):
                clean.append(r)
            else:
                clean.append(0.0)
                nan_replaced += 1

        n_clean: int = len(returns) - nan_replaced

        # Sequential GARCH update.
        variance: float = self._current_variance
        for r in clean:
            variance = (
                self._omega
                + self._alpha * r * r
                + self._beta * variance
            )
            # Floor to prevent numerical collapse.
            variance = max(_VOL_EPSILON ** 2, variance)

        # Update internal state.
        self._current_variance = None

        volatility: float = max(_VOL_EPSILON, math.sqrt(variance))
        long_run_vol: float = max(_VOL_EPSILON, math.sqrt(self._long_run_variance))

        return VolResult(
            volatility=volatility,
            variance=variance,
            long_run_volatility=long_run_vol,
            n_clean_returns=n_clean,
            nan_replaced=nan_replaced,
        )

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def xǁVolatilityTrackerǁestimate_volatility__mutmut_38(self, returns: List[float]) -> VolResult:
        """
        Update the GARCH(1,1) model with a sequence of return observations
        and return the resulting volatility estimate.

        Non-finite values (NaN, Inf) are replaced with 0.0 and counted
        in nan_replaced. Empty or all-non-finite lists raise ValueError.

        The model is updated sequentially: for each return r_t,
          sigma^2_{t+1} = omega + alpha * r_t^2 + beta * sigma^2_t

        After processing all returns, self._current_variance holds the
        most recent conditional variance.

        Parameters
        ----------
        returns : List[float]
            Sequence of per-period returns. Must be non-empty.
            Non-finite values are replaced with 0.0.

        Returns
        -------
        VolResult
            Volatility estimate derived from the final variance state.

        Raises
        ------
        ValueError
            If returns is empty.
        TypeError
            If returns is None.
        """
        if returns is None:
            raise TypeError("returns must be a list, got None.")
        if len(returns) == 0:
            raise ValueError("returns must be non-empty.")

        # Clean returns: replace non-finite with 0.0.
        nan_replaced: int = 0
        clean: List[float] = []
        for r in returns:
            if math.isfinite(r):
                clean.append(r)
            else:
                clean.append(0.0)
                nan_replaced += 1

        n_clean: int = len(returns) - nan_replaced

        # Sequential GARCH update.
        variance: float = self._current_variance
        for r in clean:
            variance = (
                self._omega
                + self._alpha * r * r
                + self._beta * variance
            )
            # Floor to prevent numerical collapse.
            variance = max(_VOL_EPSILON ** 2, variance)

        # Update internal state.
        self._current_variance = variance

        volatility: float = None
        long_run_vol: float = max(_VOL_EPSILON, math.sqrt(self._long_run_variance))

        return VolResult(
            volatility=volatility,
            variance=variance,
            long_run_volatility=long_run_vol,
            n_clean_returns=n_clean,
            nan_replaced=nan_replaced,
        )

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def xǁVolatilityTrackerǁestimate_volatility__mutmut_39(self, returns: List[float]) -> VolResult:
        """
        Update the GARCH(1,1) model with a sequence of return observations
        and return the resulting volatility estimate.

        Non-finite values (NaN, Inf) are replaced with 0.0 and counted
        in nan_replaced. Empty or all-non-finite lists raise ValueError.

        The model is updated sequentially: for each return r_t,
          sigma^2_{t+1} = omega + alpha * r_t^2 + beta * sigma^2_t

        After processing all returns, self._current_variance holds the
        most recent conditional variance.

        Parameters
        ----------
        returns : List[float]
            Sequence of per-period returns. Must be non-empty.
            Non-finite values are replaced with 0.0.

        Returns
        -------
        VolResult
            Volatility estimate derived from the final variance state.

        Raises
        ------
        ValueError
            If returns is empty.
        TypeError
            If returns is None.
        """
        if returns is None:
            raise TypeError("returns must be a list, got None.")
        if len(returns) == 0:
            raise ValueError("returns must be non-empty.")

        # Clean returns: replace non-finite with 0.0.
        nan_replaced: int = 0
        clean: List[float] = []
        for r in returns:
            if math.isfinite(r):
                clean.append(r)
            else:
                clean.append(0.0)
                nan_replaced += 1

        n_clean: int = len(returns) - nan_replaced

        # Sequential GARCH update.
        variance: float = self._current_variance
        for r in clean:
            variance = (
                self._omega
                + self._alpha * r * r
                + self._beta * variance
            )
            # Floor to prevent numerical collapse.
            variance = max(_VOL_EPSILON ** 2, variance)

        # Update internal state.
        self._current_variance = variance

        volatility: float = max(None, math.sqrt(variance))
        long_run_vol: float = max(_VOL_EPSILON, math.sqrt(self._long_run_variance))

        return VolResult(
            volatility=volatility,
            variance=variance,
            long_run_volatility=long_run_vol,
            n_clean_returns=n_clean,
            nan_replaced=nan_replaced,
        )

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def xǁVolatilityTrackerǁestimate_volatility__mutmut_40(self, returns: List[float]) -> VolResult:
        """
        Update the GARCH(1,1) model with a sequence of return observations
        and return the resulting volatility estimate.

        Non-finite values (NaN, Inf) are replaced with 0.0 and counted
        in nan_replaced. Empty or all-non-finite lists raise ValueError.

        The model is updated sequentially: for each return r_t,
          sigma^2_{t+1} = omega + alpha * r_t^2 + beta * sigma^2_t

        After processing all returns, self._current_variance holds the
        most recent conditional variance.

        Parameters
        ----------
        returns : List[float]
            Sequence of per-period returns. Must be non-empty.
            Non-finite values are replaced with 0.0.

        Returns
        -------
        VolResult
            Volatility estimate derived from the final variance state.

        Raises
        ------
        ValueError
            If returns is empty.
        TypeError
            If returns is None.
        """
        if returns is None:
            raise TypeError("returns must be a list, got None.")
        if len(returns) == 0:
            raise ValueError("returns must be non-empty.")

        # Clean returns: replace non-finite with 0.0.
        nan_replaced: int = 0
        clean: List[float] = []
        for r in returns:
            if math.isfinite(r):
                clean.append(r)
            else:
                clean.append(0.0)
                nan_replaced += 1

        n_clean: int = len(returns) - nan_replaced

        # Sequential GARCH update.
        variance: float = self._current_variance
        for r in clean:
            variance = (
                self._omega
                + self._alpha * r * r
                + self._beta * variance
            )
            # Floor to prevent numerical collapse.
            variance = max(_VOL_EPSILON ** 2, variance)

        # Update internal state.
        self._current_variance = variance

        volatility: float = max(_VOL_EPSILON, None)
        long_run_vol: float = max(_VOL_EPSILON, math.sqrt(self._long_run_variance))

        return VolResult(
            volatility=volatility,
            variance=variance,
            long_run_volatility=long_run_vol,
            n_clean_returns=n_clean,
            nan_replaced=nan_replaced,
        )

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def xǁVolatilityTrackerǁestimate_volatility__mutmut_41(self, returns: List[float]) -> VolResult:
        """
        Update the GARCH(1,1) model with a sequence of return observations
        and return the resulting volatility estimate.

        Non-finite values (NaN, Inf) are replaced with 0.0 and counted
        in nan_replaced. Empty or all-non-finite lists raise ValueError.

        The model is updated sequentially: for each return r_t,
          sigma^2_{t+1} = omega + alpha * r_t^2 + beta * sigma^2_t

        After processing all returns, self._current_variance holds the
        most recent conditional variance.

        Parameters
        ----------
        returns : List[float]
            Sequence of per-period returns. Must be non-empty.
            Non-finite values are replaced with 0.0.

        Returns
        -------
        VolResult
            Volatility estimate derived from the final variance state.

        Raises
        ------
        ValueError
            If returns is empty.
        TypeError
            If returns is None.
        """
        if returns is None:
            raise TypeError("returns must be a list, got None.")
        if len(returns) == 0:
            raise ValueError("returns must be non-empty.")

        # Clean returns: replace non-finite with 0.0.
        nan_replaced: int = 0
        clean: List[float] = []
        for r in returns:
            if math.isfinite(r):
                clean.append(r)
            else:
                clean.append(0.0)
                nan_replaced += 1

        n_clean: int = len(returns) - nan_replaced

        # Sequential GARCH update.
        variance: float = self._current_variance
        for r in clean:
            variance = (
                self._omega
                + self._alpha * r * r
                + self._beta * variance
            )
            # Floor to prevent numerical collapse.
            variance = max(_VOL_EPSILON ** 2, variance)

        # Update internal state.
        self._current_variance = variance

        volatility: float = max(math.sqrt(variance))
        long_run_vol: float = max(_VOL_EPSILON, math.sqrt(self._long_run_variance))

        return VolResult(
            volatility=volatility,
            variance=variance,
            long_run_volatility=long_run_vol,
            n_clean_returns=n_clean,
            nan_replaced=nan_replaced,
        )

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def xǁVolatilityTrackerǁestimate_volatility__mutmut_42(self, returns: List[float]) -> VolResult:
        """
        Update the GARCH(1,1) model with a sequence of return observations
        and return the resulting volatility estimate.

        Non-finite values (NaN, Inf) are replaced with 0.0 and counted
        in nan_replaced. Empty or all-non-finite lists raise ValueError.

        The model is updated sequentially: for each return r_t,
          sigma^2_{t+1} = omega + alpha * r_t^2 + beta * sigma^2_t

        After processing all returns, self._current_variance holds the
        most recent conditional variance.

        Parameters
        ----------
        returns : List[float]
            Sequence of per-period returns. Must be non-empty.
            Non-finite values are replaced with 0.0.

        Returns
        -------
        VolResult
            Volatility estimate derived from the final variance state.

        Raises
        ------
        ValueError
            If returns is empty.
        TypeError
            If returns is None.
        """
        if returns is None:
            raise TypeError("returns must be a list, got None.")
        if len(returns) == 0:
            raise ValueError("returns must be non-empty.")

        # Clean returns: replace non-finite with 0.0.
        nan_replaced: int = 0
        clean: List[float] = []
        for r in returns:
            if math.isfinite(r):
                clean.append(r)
            else:
                clean.append(0.0)
                nan_replaced += 1

        n_clean: int = len(returns) - nan_replaced

        # Sequential GARCH update.
        variance: float = self._current_variance
        for r in clean:
            variance = (
                self._omega
                + self._alpha * r * r
                + self._beta * variance
            )
            # Floor to prevent numerical collapse.
            variance = max(_VOL_EPSILON ** 2, variance)

        # Update internal state.
        self._current_variance = variance

        volatility: float = max(_VOL_EPSILON, )
        long_run_vol: float = max(_VOL_EPSILON, math.sqrt(self._long_run_variance))

        return VolResult(
            volatility=volatility,
            variance=variance,
            long_run_volatility=long_run_vol,
            n_clean_returns=n_clean,
            nan_replaced=nan_replaced,
        )

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def xǁVolatilityTrackerǁestimate_volatility__mutmut_43(self, returns: List[float]) -> VolResult:
        """
        Update the GARCH(1,1) model with a sequence of return observations
        and return the resulting volatility estimate.

        Non-finite values (NaN, Inf) are replaced with 0.0 and counted
        in nan_replaced. Empty or all-non-finite lists raise ValueError.

        The model is updated sequentially: for each return r_t,
          sigma^2_{t+1} = omega + alpha * r_t^2 + beta * sigma^2_t

        After processing all returns, self._current_variance holds the
        most recent conditional variance.

        Parameters
        ----------
        returns : List[float]
            Sequence of per-period returns. Must be non-empty.
            Non-finite values are replaced with 0.0.

        Returns
        -------
        VolResult
            Volatility estimate derived from the final variance state.

        Raises
        ------
        ValueError
            If returns is empty.
        TypeError
            If returns is None.
        """
        if returns is None:
            raise TypeError("returns must be a list, got None.")
        if len(returns) == 0:
            raise ValueError("returns must be non-empty.")

        # Clean returns: replace non-finite with 0.0.
        nan_replaced: int = 0
        clean: List[float] = []
        for r in returns:
            if math.isfinite(r):
                clean.append(r)
            else:
                clean.append(0.0)
                nan_replaced += 1

        n_clean: int = len(returns) - nan_replaced

        # Sequential GARCH update.
        variance: float = self._current_variance
        for r in clean:
            variance = (
                self._omega
                + self._alpha * r * r
                + self._beta * variance
            )
            # Floor to prevent numerical collapse.
            variance = max(_VOL_EPSILON ** 2, variance)

        # Update internal state.
        self._current_variance = variance

        volatility: float = max(_VOL_EPSILON, math.sqrt(None))
        long_run_vol: float = max(_VOL_EPSILON, math.sqrt(self._long_run_variance))

        return VolResult(
            volatility=volatility,
            variance=variance,
            long_run_volatility=long_run_vol,
            n_clean_returns=n_clean,
            nan_replaced=nan_replaced,
        )

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def xǁVolatilityTrackerǁestimate_volatility__mutmut_44(self, returns: List[float]) -> VolResult:
        """
        Update the GARCH(1,1) model with a sequence of return observations
        and return the resulting volatility estimate.

        Non-finite values (NaN, Inf) are replaced with 0.0 and counted
        in nan_replaced. Empty or all-non-finite lists raise ValueError.

        The model is updated sequentially: for each return r_t,
          sigma^2_{t+1} = omega + alpha * r_t^2 + beta * sigma^2_t

        After processing all returns, self._current_variance holds the
        most recent conditional variance.

        Parameters
        ----------
        returns : List[float]
            Sequence of per-period returns. Must be non-empty.
            Non-finite values are replaced with 0.0.

        Returns
        -------
        VolResult
            Volatility estimate derived from the final variance state.

        Raises
        ------
        ValueError
            If returns is empty.
        TypeError
            If returns is None.
        """
        if returns is None:
            raise TypeError("returns must be a list, got None.")
        if len(returns) == 0:
            raise ValueError("returns must be non-empty.")

        # Clean returns: replace non-finite with 0.0.
        nan_replaced: int = 0
        clean: List[float] = []
        for r in returns:
            if math.isfinite(r):
                clean.append(r)
            else:
                clean.append(0.0)
                nan_replaced += 1

        n_clean: int = len(returns) - nan_replaced

        # Sequential GARCH update.
        variance: float = self._current_variance
        for r in clean:
            variance = (
                self._omega
                + self._alpha * r * r
                + self._beta * variance
            )
            # Floor to prevent numerical collapse.
            variance = max(_VOL_EPSILON ** 2, variance)

        # Update internal state.
        self._current_variance = variance

        volatility: float = max(_VOL_EPSILON, math.sqrt(variance))
        long_run_vol: float = None

        return VolResult(
            volatility=volatility,
            variance=variance,
            long_run_volatility=long_run_vol,
            n_clean_returns=n_clean,
            nan_replaced=nan_replaced,
        )

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def xǁVolatilityTrackerǁestimate_volatility__mutmut_45(self, returns: List[float]) -> VolResult:
        """
        Update the GARCH(1,1) model with a sequence of return observations
        and return the resulting volatility estimate.

        Non-finite values (NaN, Inf) are replaced with 0.0 and counted
        in nan_replaced. Empty or all-non-finite lists raise ValueError.

        The model is updated sequentially: for each return r_t,
          sigma^2_{t+1} = omega + alpha * r_t^2 + beta * sigma^2_t

        After processing all returns, self._current_variance holds the
        most recent conditional variance.

        Parameters
        ----------
        returns : List[float]
            Sequence of per-period returns. Must be non-empty.
            Non-finite values are replaced with 0.0.

        Returns
        -------
        VolResult
            Volatility estimate derived from the final variance state.

        Raises
        ------
        ValueError
            If returns is empty.
        TypeError
            If returns is None.
        """
        if returns is None:
            raise TypeError("returns must be a list, got None.")
        if len(returns) == 0:
            raise ValueError("returns must be non-empty.")

        # Clean returns: replace non-finite with 0.0.
        nan_replaced: int = 0
        clean: List[float] = []
        for r in returns:
            if math.isfinite(r):
                clean.append(r)
            else:
                clean.append(0.0)
                nan_replaced += 1

        n_clean: int = len(returns) - nan_replaced

        # Sequential GARCH update.
        variance: float = self._current_variance
        for r in clean:
            variance = (
                self._omega
                + self._alpha * r * r
                + self._beta * variance
            )
            # Floor to prevent numerical collapse.
            variance = max(_VOL_EPSILON ** 2, variance)

        # Update internal state.
        self._current_variance = variance

        volatility: float = max(_VOL_EPSILON, math.sqrt(variance))
        long_run_vol: float = max(None, math.sqrt(self._long_run_variance))

        return VolResult(
            volatility=volatility,
            variance=variance,
            long_run_volatility=long_run_vol,
            n_clean_returns=n_clean,
            nan_replaced=nan_replaced,
        )

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def xǁVolatilityTrackerǁestimate_volatility__mutmut_46(self, returns: List[float]) -> VolResult:
        """
        Update the GARCH(1,1) model with a sequence of return observations
        and return the resulting volatility estimate.

        Non-finite values (NaN, Inf) are replaced with 0.0 and counted
        in nan_replaced. Empty or all-non-finite lists raise ValueError.

        The model is updated sequentially: for each return r_t,
          sigma^2_{t+1} = omega + alpha * r_t^2 + beta * sigma^2_t

        After processing all returns, self._current_variance holds the
        most recent conditional variance.

        Parameters
        ----------
        returns : List[float]
            Sequence of per-period returns. Must be non-empty.
            Non-finite values are replaced with 0.0.

        Returns
        -------
        VolResult
            Volatility estimate derived from the final variance state.

        Raises
        ------
        ValueError
            If returns is empty.
        TypeError
            If returns is None.
        """
        if returns is None:
            raise TypeError("returns must be a list, got None.")
        if len(returns) == 0:
            raise ValueError("returns must be non-empty.")

        # Clean returns: replace non-finite with 0.0.
        nan_replaced: int = 0
        clean: List[float] = []
        for r in returns:
            if math.isfinite(r):
                clean.append(r)
            else:
                clean.append(0.0)
                nan_replaced += 1

        n_clean: int = len(returns) - nan_replaced

        # Sequential GARCH update.
        variance: float = self._current_variance
        for r in clean:
            variance = (
                self._omega
                + self._alpha * r * r
                + self._beta * variance
            )
            # Floor to prevent numerical collapse.
            variance = max(_VOL_EPSILON ** 2, variance)

        # Update internal state.
        self._current_variance = variance

        volatility: float = max(_VOL_EPSILON, math.sqrt(variance))
        long_run_vol: float = max(_VOL_EPSILON, None)

        return VolResult(
            volatility=volatility,
            variance=variance,
            long_run_volatility=long_run_vol,
            n_clean_returns=n_clean,
            nan_replaced=nan_replaced,
        )

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def xǁVolatilityTrackerǁestimate_volatility__mutmut_47(self, returns: List[float]) -> VolResult:
        """
        Update the GARCH(1,1) model with a sequence of return observations
        and return the resulting volatility estimate.

        Non-finite values (NaN, Inf) are replaced with 0.0 and counted
        in nan_replaced. Empty or all-non-finite lists raise ValueError.

        The model is updated sequentially: for each return r_t,
          sigma^2_{t+1} = omega + alpha * r_t^2 + beta * sigma^2_t

        After processing all returns, self._current_variance holds the
        most recent conditional variance.

        Parameters
        ----------
        returns : List[float]
            Sequence of per-period returns. Must be non-empty.
            Non-finite values are replaced with 0.0.

        Returns
        -------
        VolResult
            Volatility estimate derived from the final variance state.

        Raises
        ------
        ValueError
            If returns is empty.
        TypeError
            If returns is None.
        """
        if returns is None:
            raise TypeError("returns must be a list, got None.")
        if len(returns) == 0:
            raise ValueError("returns must be non-empty.")

        # Clean returns: replace non-finite with 0.0.
        nan_replaced: int = 0
        clean: List[float] = []
        for r in returns:
            if math.isfinite(r):
                clean.append(r)
            else:
                clean.append(0.0)
                nan_replaced += 1

        n_clean: int = len(returns) - nan_replaced

        # Sequential GARCH update.
        variance: float = self._current_variance
        for r in clean:
            variance = (
                self._omega
                + self._alpha * r * r
                + self._beta * variance
            )
            # Floor to prevent numerical collapse.
            variance = max(_VOL_EPSILON ** 2, variance)

        # Update internal state.
        self._current_variance = variance

        volatility: float = max(_VOL_EPSILON, math.sqrt(variance))
        long_run_vol: float = max(math.sqrt(self._long_run_variance))

        return VolResult(
            volatility=volatility,
            variance=variance,
            long_run_volatility=long_run_vol,
            n_clean_returns=n_clean,
            nan_replaced=nan_replaced,
        )

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def xǁVolatilityTrackerǁestimate_volatility__mutmut_48(self, returns: List[float]) -> VolResult:
        """
        Update the GARCH(1,1) model with a sequence of return observations
        and return the resulting volatility estimate.

        Non-finite values (NaN, Inf) are replaced with 0.0 and counted
        in nan_replaced. Empty or all-non-finite lists raise ValueError.

        The model is updated sequentially: for each return r_t,
          sigma^2_{t+1} = omega + alpha * r_t^2 + beta * sigma^2_t

        After processing all returns, self._current_variance holds the
        most recent conditional variance.

        Parameters
        ----------
        returns : List[float]
            Sequence of per-period returns. Must be non-empty.
            Non-finite values are replaced with 0.0.

        Returns
        -------
        VolResult
            Volatility estimate derived from the final variance state.

        Raises
        ------
        ValueError
            If returns is empty.
        TypeError
            If returns is None.
        """
        if returns is None:
            raise TypeError("returns must be a list, got None.")
        if len(returns) == 0:
            raise ValueError("returns must be non-empty.")

        # Clean returns: replace non-finite with 0.0.
        nan_replaced: int = 0
        clean: List[float] = []
        for r in returns:
            if math.isfinite(r):
                clean.append(r)
            else:
                clean.append(0.0)
                nan_replaced += 1

        n_clean: int = len(returns) - nan_replaced

        # Sequential GARCH update.
        variance: float = self._current_variance
        for r in clean:
            variance = (
                self._omega
                + self._alpha * r * r
                + self._beta * variance
            )
            # Floor to prevent numerical collapse.
            variance = max(_VOL_EPSILON ** 2, variance)

        # Update internal state.
        self._current_variance = variance

        volatility: float = max(_VOL_EPSILON, math.sqrt(variance))
        long_run_vol: float = max(_VOL_EPSILON, )

        return VolResult(
            volatility=volatility,
            variance=variance,
            long_run_volatility=long_run_vol,
            n_clean_returns=n_clean,
            nan_replaced=nan_replaced,
        )

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def xǁVolatilityTrackerǁestimate_volatility__mutmut_49(self, returns: List[float]) -> VolResult:
        """
        Update the GARCH(1,1) model with a sequence of return observations
        and return the resulting volatility estimate.

        Non-finite values (NaN, Inf) are replaced with 0.0 and counted
        in nan_replaced. Empty or all-non-finite lists raise ValueError.

        The model is updated sequentially: for each return r_t,
          sigma^2_{t+1} = omega + alpha * r_t^2 + beta * sigma^2_t

        After processing all returns, self._current_variance holds the
        most recent conditional variance.

        Parameters
        ----------
        returns : List[float]
            Sequence of per-period returns. Must be non-empty.
            Non-finite values are replaced with 0.0.

        Returns
        -------
        VolResult
            Volatility estimate derived from the final variance state.

        Raises
        ------
        ValueError
            If returns is empty.
        TypeError
            If returns is None.
        """
        if returns is None:
            raise TypeError("returns must be a list, got None.")
        if len(returns) == 0:
            raise ValueError("returns must be non-empty.")

        # Clean returns: replace non-finite with 0.0.
        nan_replaced: int = 0
        clean: List[float] = []
        for r in returns:
            if math.isfinite(r):
                clean.append(r)
            else:
                clean.append(0.0)
                nan_replaced += 1

        n_clean: int = len(returns) - nan_replaced

        # Sequential GARCH update.
        variance: float = self._current_variance
        for r in clean:
            variance = (
                self._omega
                + self._alpha * r * r
                + self._beta * variance
            )
            # Floor to prevent numerical collapse.
            variance = max(_VOL_EPSILON ** 2, variance)

        # Update internal state.
        self._current_variance = variance

        volatility: float = max(_VOL_EPSILON, math.sqrt(variance))
        long_run_vol: float = max(_VOL_EPSILON, math.sqrt(None))

        return VolResult(
            volatility=volatility,
            variance=variance,
            long_run_volatility=long_run_vol,
            n_clean_returns=n_clean,
            nan_replaced=nan_replaced,
        )

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def xǁVolatilityTrackerǁestimate_volatility__mutmut_50(self, returns: List[float]) -> VolResult:
        """
        Update the GARCH(1,1) model with a sequence of return observations
        and return the resulting volatility estimate.

        Non-finite values (NaN, Inf) are replaced with 0.0 and counted
        in nan_replaced. Empty or all-non-finite lists raise ValueError.

        The model is updated sequentially: for each return r_t,
          sigma^2_{t+1} = omega + alpha * r_t^2 + beta * sigma^2_t

        After processing all returns, self._current_variance holds the
        most recent conditional variance.

        Parameters
        ----------
        returns : List[float]
            Sequence of per-period returns. Must be non-empty.
            Non-finite values are replaced with 0.0.

        Returns
        -------
        VolResult
            Volatility estimate derived from the final variance state.

        Raises
        ------
        ValueError
            If returns is empty.
        TypeError
            If returns is None.
        """
        if returns is None:
            raise TypeError("returns must be a list, got None.")
        if len(returns) == 0:
            raise ValueError("returns must be non-empty.")

        # Clean returns: replace non-finite with 0.0.
        nan_replaced: int = 0
        clean: List[float] = []
        for r in returns:
            if math.isfinite(r):
                clean.append(r)
            else:
                clean.append(0.0)
                nan_replaced += 1

        n_clean: int = len(returns) - nan_replaced

        # Sequential GARCH update.
        variance: float = self._current_variance
        for r in clean:
            variance = (
                self._omega
                + self._alpha * r * r
                + self._beta * variance
            )
            # Floor to prevent numerical collapse.
            variance = max(_VOL_EPSILON ** 2, variance)

        # Update internal state.
        self._current_variance = variance

        volatility: float = max(_VOL_EPSILON, math.sqrt(variance))
        long_run_vol: float = max(_VOL_EPSILON, math.sqrt(self._long_run_variance))

        return VolResult(
            volatility=None,
            variance=variance,
            long_run_volatility=long_run_vol,
            n_clean_returns=n_clean,
            nan_replaced=nan_replaced,
        )

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def xǁVolatilityTrackerǁestimate_volatility__mutmut_51(self, returns: List[float]) -> VolResult:
        """
        Update the GARCH(1,1) model with a sequence of return observations
        and return the resulting volatility estimate.

        Non-finite values (NaN, Inf) are replaced with 0.0 and counted
        in nan_replaced. Empty or all-non-finite lists raise ValueError.

        The model is updated sequentially: for each return r_t,
          sigma^2_{t+1} = omega + alpha * r_t^2 + beta * sigma^2_t

        After processing all returns, self._current_variance holds the
        most recent conditional variance.

        Parameters
        ----------
        returns : List[float]
            Sequence of per-period returns. Must be non-empty.
            Non-finite values are replaced with 0.0.

        Returns
        -------
        VolResult
            Volatility estimate derived from the final variance state.

        Raises
        ------
        ValueError
            If returns is empty.
        TypeError
            If returns is None.
        """
        if returns is None:
            raise TypeError("returns must be a list, got None.")
        if len(returns) == 0:
            raise ValueError("returns must be non-empty.")

        # Clean returns: replace non-finite with 0.0.
        nan_replaced: int = 0
        clean: List[float] = []
        for r in returns:
            if math.isfinite(r):
                clean.append(r)
            else:
                clean.append(0.0)
                nan_replaced += 1

        n_clean: int = len(returns) - nan_replaced

        # Sequential GARCH update.
        variance: float = self._current_variance
        for r in clean:
            variance = (
                self._omega
                + self._alpha * r * r
                + self._beta * variance
            )
            # Floor to prevent numerical collapse.
            variance = max(_VOL_EPSILON ** 2, variance)

        # Update internal state.
        self._current_variance = variance

        volatility: float = max(_VOL_EPSILON, math.sqrt(variance))
        long_run_vol: float = max(_VOL_EPSILON, math.sqrt(self._long_run_variance))

        return VolResult(
            volatility=volatility,
            variance=None,
            long_run_volatility=long_run_vol,
            n_clean_returns=n_clean,
            nan_replaced=nan_replaced,
        )

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def xǁVolatilityTrackerǁestimate_volatility__mutmut_52(self, returns: List[float]) -> VolResult:
        """
        Update the GARCH(1,1) model with a sequence of return observations
        and return the resulting volatility estimate.

        Non-finite values (NaN, Inf) are replaced with 0.0 and counted
        in nan_replaced. Empty or all-non-finite lists raise ValueError.

        The model is updated sequentially: for each return r_t,
          sigma^2_{t+1} = omega + alpha * r_t^2 + beta * sigma^2_t

        After processing all returns, self._current_variance holds the
        most recent conditional variance.

        Parameters
        ----------
        returns : List[float]
            Sequence of per-period returns. Must be non-empty.
            Non-finite values are replaced with 0.0.

        Returns
        -------
        VolResult
            Volatility estimate derived from the final variance state.

        Raises
        ------
        ValueError
            If returns is empty.
        TypeError
            If returns is None.
        """
        if returns is None:
            raise TypeError("returns must be a list, got None.")
        if len(returns) == 0:
            raise ValueError("returns must be non-empty.")

        # Clean returns: replace non-finite with 0.0.
        nan_replaced: int = 0
        clean: List[float] = []
        for r in returns:
            if math.isfinite(r):
                clean.append(r)
            else:
                clean.append(0.0)
                nan_replaced += 1

        n_clean: int = len(returns) - nan_replaced

        # Sequential GARCH update.
        variance: float = self._current_variance
        for r in clean:
            variance = (
                self._omega
                + self._alpha * r * r
                + self._beta * variance
            )
            # Floor to prevent numerical collapse.
            variance = max(_VOL_EPSILON ** 2, variance)

        # Update internal state.
        self._current_variance = variance

        volatility: float = max(_VOL_EPSILON, math.sqrt(variance))
        long_run_vol: float = max(_VOL_EPSILON, math.sqrt(self._long_run_variance))

        return VolResult(
            volatility=volatility,
            variance=variance,
            long_run_volatility=None,
            n_clean_returns=n_clean,
            nan_replaced=nan_replaced,
        )

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def xǁVolatilityTrackerǁestimate_volatility__mutmut_53(self, returns: List[float]) -> VolResult:
        """
        Update the GARCH(1,1) model with a sequence of return observations
        and return the resulting volatility estimate.

        Non-finite values (NaN, Inf) are replaced with 0.0 and counted
        in nan_replaced. Empty or all-non-finite lists raise ValueError.

        The model is updated sequentially: for each return r_t,
          sigma^2_{t+1} = omega + alpha * r_t^2 + beta * sigma^2_t

        After processing all returns, self._current_variance holds the
        most recent conditional variance.

        Parameters
        ----------
        returns : List[float]
            Sequence of per-period returns. Must be non-empty.
            Non-finite values are replaced with 0.0.

        Returns
        -------
        VolResult
            Volatility estimate derived from the final variance state.

        Raises
        ------
        ValueError
            If returns is empty.
        TypeError
            If returns is None.
        """
        if returns is None:
            raise TypeError("returns must be a list, got None.")
        if len(returns) == 0:
            raise ValueError("returns must be non-empty.")

        # Clean returns: replace non-finite with 0.0.
        nan_replaced: int = 0
        clean: List[float] = []
        for r in returns:
            if math.isfinite(r):
                clean.append(r)
            else:
                clean.append(0.0)
                nan_replaced += 1

        n_clean: int = len(returns) - nan_replaced

        # Sequential GARCH update.
        variance: float = self._current_variance
        for r in clean:
            variance = (
                self._omega
                + self._alpha * r * r
                + self._beta * variance
            )
            # Floor to prevent numerical collapse.
            variance = max(_VOL_EPSILON ** 2, variance)

        # Update internal state.
        self._current_variance = variance

        volatility: float = max(_VOL_EPSILON, math.sqrt(variance))
        long_run_vol: float = max(_VOL_EPSILON, math.sqrt(self._long_run_variance))

        return VolResult(
            volatility=volatility,
            variance=variance,
            long_run_volatility=long_run_vol,
            n_clean_returns=None,
            nan_replaced=nan_replaced,
        )

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def xǁVolatilityTrackerǁestimate_volatility__mutmut_54(self, returns: List[float]) -> VolResult:
        """
        Update the GARCH(1,1) model with a sequence of return observations
        and return the resulting volatility estimate.

        Non-finite values (NaN, Inf) are replaced with 0.0 and counted
        in nan_replaced. Empty or all-non-finite lists raise ValueError.

        The model is updated sequentially: for each return r_t,
          sigma^2_{t+1} = omega + alpha * r_t^2 + beta * sigma^2_t

        After processing all returns, self._current_variance holds the
        most recent conditional variance.

        Parameters
        ----------
        returns : List[float]
            Sequence of per-period returns. Must be non-empty.
            Non-finite values are replaced with 0.0.

        Returns
        -------
        VolResult
            Volatility estimate derived from the final variance state.

        Raises
        ------
        ValueError
            If returns is empty.
        TypeError
            If returns is None.
        """
        if returns is None:
            raise TypeError("returns must be a list, got None.")
        if len(returns) == 0:
            raise ValueError("returns must be non-empty.")

        # Clean returns: replace non-finite with 0.0.
        nan_replaced: int = 0
        clean: List[float] = []
        for r in returns:
            if math.isfinite(r):
                clean.append(r)
            else:
                clean.append(0.0)
                nan_replaced += 1

        n_clean: int = len(returns) - nan_replaced

        # Sequential GARCH update.
        variance: float = self._current_variance
        for r in clean:
            variance = (
                self._omega
                + self._alpha * r * r
                + self._beta * variance
            )
            # Floor to prevent numerical collapse.
            variance = max(_VOL_EPSILON ** 2, variance)

        # Update internal state.
        self._current_variance = variance

        volatility: float = max(_VOL_EPSILON, math.sqrt(variance))
        long_run_vol: float = max(_VOL_EPSILON, math.sqrt(self._long_run_variance))

        return VolResult(
            volatility=volatility,
            variance=variance,
            long_run_volatility=long_run_vol,
            n_clean_returns=n_clean,
            nan_replaced=None,
        )

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def xǁVolatilityTrackerǁestimate_volatility__mutmut_55(self, returns: List[float]) -> VolResult:
        """
        Update the GARCH(1,1) model with a sequence of return observations
        and return the resulting volatility estimate.

        Non-finite values (NaN, Inf) are replaced with 0.0 and counted
        in nan_replaced. Empty or all-non-finite lists raise ValueError.

        The model is updated sequentially: for each return r_t,
          sigma^2_{t+1} = omega + alpha * r_t^2 + beta * sigma^2_t

        After processing all returns, self._current_variance holds the
        most recent conditional variance.

        Parameters
        ----------
        returns : List[float]
            Sequence of per-period returns. Must be non-empty.
            Non-finite values are replaced with 0.0.

        Returns
        -------
        VolResult
            Volatility estimate derived from the final variance state.

        Raises
        ------
        ValueError
            If returns is empty.
        TypeError
            If returns is None.
        """
        if returns is None:
            raise TypeError("returns must be a list, got None.")
        if len(returns) == 0:
            raise ValueError("returns must be non-empty.")

        # Clean returns: replace non-finite with 0.0.
        nan_replaced: int = 0
        clean: List[float] = []
        for r in returns:
            if math.isfinite(r):
                clean.append(r)
            else:
                clean.append(0.0)
                nan_replaced += 1

        n_clean: int = len(returns) - nan_replaced

        # Sequential GARCH update.
        variance: float = self._current_variance
        for r in clean:
            variance = (
                self._omega
                + self._alpha * r * r
                + self._beta * variance
            )
            # Floor to prevent numerical collapse.
            variance = max(_VOL_EPSILON ** 2, variance)

        # Update internal state.
        self._current_variance = variance

        volatility: float = max(_VOL_EPSILON, math.sqrt(variance))
        long_run_vol: float = max(_VOL_EPSILON, math.sqrt(self._long_run_variance))

        return VolResult(
            variance=variance,
            long_run_volatility=long_run_vol,
            n_clean_returns=n_clean,
            nan_replaced=nan_replaced,
        )

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def xǁVolatilityTrackerǁestimate_volatility__mutmut_56(self, returns: List[float]) -> VolResult:
        """
        Update the GARCH(1,1) model with a sequence of return observations
        and return the resulting volatility estimate.

        Non-finite values (NaN, Inf) are replaced with 0.0 and counted
        in nan_replaced. Empty or all-non-finite lists raise ValueError.

        The model is updated sequentially: for each return r_t,
          sigma^2_{t+1} = omega + alpha * r_t^2 + beta * sigma^2_t

        After processing all returns, self._current_variance holds the
        most recent conditional variance.

        Parameters
        ----------
        returns : List[float]
            Sequence of per-period returns. Must be non-empty.
            Non-finite values are replaced with 0.0.

        Returns
        -------
        VolResult
            Volatility estimate derived from the final variance state.

        Raises
        ------
        ValueError
            If returns is empty.
        TypeError
            If returns is None.
        """
        if returns is None:
            raise TypeError("returns must be a list, got None.")
        if len(returns) == 0:
            raise ValueError("returns must be non-empty.")

        # Clean returns: replace non-finite with 0.0.
        nan_replaced: int = 0
        clean: List[float] = []
        for r in returns:
            if math.isfinite(r):
                clean.append(r)
            else:
                clean.append(0.0)
                nan_replaced += 1

        n_clean: int = len(returns) - nan_replaced

        # Sequential GARCH update.
        variance: float = self._current_variance
        for r in clean:
            variance = (
                self._omega
                + self._alpha * r * r
                + self._beta * variance
            )
            # Floor to prevent numerical collapse.
            variance = max(_VOL_EPSILON ** 2, variance)

        # Update internal state.
        self._current_variance = variance

        volatility: float = max(_VOL_EPSILON, math.sqrt(variance))
        long_run_vol: float = max(_VOL_EPSILON, math.sqrt(self._long_run_variance))

        return VolResult(
            volatility=volatility,
            long_run_volatility=long_run_vol,
            n_clean_returns=n_clean,
            nan_replaced=nan_replaced,
        )

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def xǁVolatilityTrackerǁestimate_volatility__mutmut_57(self, returns: List[float]) -> VolResult:
        """
        Update the GARCH(1,1) model with a sequence of return observations
        and return the resulting volatility estimate.

        Non-finite values (NaN, Inf) are replaced with 0.0 and counted
        in nan_replaced. Empty or all-non-finite lists raise ValueError.

        The model is updated sequentially: for each return r_t,
          sigma^2_{t+1} = omega + alpha * r_t^2 + beta * sigma^2_t

        After processing all returns, self._current_variance holds the
        most recent conditional variance.

        Parameters
        ----------
        returns : List[float]
            Sequence of per-period returns. Must be non-empty.
            Non-finite values are replaced with 0.0.

        Returns
        -------
        VolResult
            Volatility estimate derived from the final variance state.

        Raises
        ------
        ValueError
            If returns is empty.
        TypeError
            If returns is None.
        """
        if returns is None:
            raise TypeError("returns must be a list, got None.")
        if len(returns) == 0:
            raise ValueError("returns must be non-empty.")

        # Clean returns: replace non-finite with 0.0.
        nan_replaced: int = 0
        clean: List[float] = []
        for r in returns:
            if math.isfinite(r):
                clean.append(r)
            else:
                clean.append(0.0)
                nan_replaced += 1

        n_clean: int = len(returns) - nan_replaced

        # Sequential GARCH update.
        variance: float = self._current_variance
        for r in clean:
            variance = (
                self._omega
                + self._alpha * r * r
                + self._beta * variance
            )
            # Floor to prevent numerical collapse.
            variance = max(_VOL_EPSILON ** 2, variance)

        # Update internal state.
        self._current_variance = variance

        volatility: float = max(_VOL_EPSILON, math.sqrt(variance))
        long_run_vol: float = max(_VOL_EPSILON, math.sqrt(self._long_run_variance))

        return VolResult(
            volatility=volatility,
            variance=variance,
            n_clean_returns=n_clean,
            nan_replaced=nan_replaced,
        )

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def xǁVolatilityTrackerǁestimate_volatility__mutmut_58(self, returns: List[float]) -> VolResult:
        """
        Update the GARCH(1,1) model with a sequence of return observations
        and return the resulting volatility estimate.

        Non-finite values (NaN, Inf) are replaced with 0.0 and counted
        in nan_replaced. Empty or all-non-finite lists raise ValueError.

        The model is updated sequentially: for each return r_t,
          sigma^2_{t+1} = omega + alpha * r_t^2 + beta * sigma^2_t

        After processing all returns, self._current_variance holds the
        most recent conditional variance.

        Parameters
        ----------
        returns : List[float]
            Sequence of per-period returns. Must be non-empty.
            Non-finite values are replaced with 0.0.

        Returns
        -------
        VolResult
            Volatility estimate derived from the final variance state.

        Raises
        ------
        ValueError
            If returns is empty.
        TypeError
            If returns is None.
        """
        if returns is None:
            raise TypeError("returns must be a list, got None.")
        if len(returns) == 0:
            raise ValueError("returns must be non-empty.")

        # Clean returns: replace non-finite with 0.0.
        nan_replaced: int = 0
        clean: List[float] = []
        for r in returns:
            if math.isfinite(r):
                clean.append(r)
            else:
                clean.append(0.0)
                nan_replaced += 1

        n_clean: int = len(returns) - nan_replaced

        # Sequential GARCH update.
        variance: float = self._current_variance
        for r in clean:
            variance = (
                self._omega
                + self._alpha * r * r
                + self._beta * variance
            )
            # Floor to prevent numerical collapse.
            variance = max(_VOL_EPSILON ** 2, variance)

        # Update internal state.
        self._current_variance = variance

        volatility: float = max(_VOL_EPSILON, math.sqrt(variance))
        long_run_vol: float = max(_VOL_EPSILON, math.sqrt(self._long_run_variance))

        return VolResult(
            volatility=volatility,
            variance=variance,
            long_run_volatility=long_run_vol,
            nan_replaced=nan_replaced,
        )

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def xǁVolatilityTrackerǁestimate_volatility__mutmut_59(self, returns: List[float]) -> VolResult:
        """
        Update the GARCH(1,1) model with a sequence of return observations
        and return the resulting volatility estimate.

        Non-finite values (NaN, Inf) are replaced with 0.0 and counted
        in nan_replaced. Empty or all-non-finite lists raise ValueError.

        The model is updated sequentially: for each return r_t,
          sigma^2_{t+1} = omega + alpha * r_t^2 + beta * sigma^2_t

        After processing all returns, self._current_variance holds the
        most recent conditional variance.

        Parameters
        ----------
        returns : List[float]
            Sequence of per-period returns. Must be non-empty.
            Non-finite values are replaced with 0.0.

        Returns
        -------
        VolResult
            Volatility estimate derived from the final variance state.

        Raises
        ------
        ValueError
            If returns is empty.
        TypeError
            If returns is None.
        """
        if returns is None:
            raise TypeError("returns must be a list, got None.")
        if len(returns) == 0:
            raise ValueError("returns must be non-empty.")

        # Clean returns: replace non-finite with 0.0.
        nan_replaced: int = 0
        clean: List[float] = []
        for r in returns:
            if math.isfinite(r):
                clean.append(r)
            else:
                clean.append(0.0)
                nan_replaced += 1

        n_clean: int = len(returns) - nan_replaced

        # Sequential GARCH update.
        variance: float = self._current_variance
        for r in clean:
            variance = (
                self._omega
                + self._alpha * r * r
                + self._beta * variance
            )
            # Floor to prevent numerical collapse.
            variance = max(_VOL_EPSILON ** 2, variance)

        # Update internal state.
        self._current_variance = variance

        volatility: float = max(_VOL_EPSILON, math.sqrt(variance))
        long_run_vol: float = max(_VOL_EPSILON, math.sqrt(self._long_run_variance))

        return VolResult(
            volatility=volatility,
            variance=variance,
            long_run_volatility=long_run_vol,
            n_clean_returns=n_clean,
            )
    
    xǁVolatilityTrackerǁestimate_volatility__mutmut_mutants : ClassVar[MutantDict] = { # type: ignore
    'xǁVolatilityTrackerǁestimate_volatility__mutmut_1': xǁVolatilityTrackerǁestimate_volatility__mutmut_1, 
        'xǁVolatilityTrackerǁestimate_volatility__mutmut_2': xǁVolatilityTrackerǁestimate_volatility__mutmut_2, 
        'xǁVolatilityTrackerǁestimate_volatility__mutmut_3': xǁVolatilityTrackerǁestimate_volatility__mutmut_3, 
        'xǁVolatilityTrackerǁestimate_volatility__mutmut_4': xǁVolatilityTrackerǁestimate_volatility__mutmut_4, 
        'xǁVolatilityTrackerǁestimate_volatility__mutmut_5': xǁVolatilityTrackerǁestimate_volatility__mutmut_5, 
        'xǁVolatilityTrackerǁestimate_volatility__mutmut_6': xǁVolatilityTrackerǁestimate_volatility__mutmut_6, 
        'xǁVolatilityTrackerǁestimate_volatility__mutmut_7': xǁVolatilityTrackerǁestimate_volatility__mutmut_7, 
        'xǁVolatilityTrackerǁestimate_volatility__mutmut_8': xǁVolatilityTrackerǁestimate_volatility__mutmut_8, 
        'xǁVolatilityTrackerǁestimate_volatility__mutmut_9': xǁVolatilityTrackerǁestimate_volatility__mutmut_9, 
        'xǁVolatilityTrackerǁestimate_volatility__mutmut_10': xǁVolatilityTrackerǁestimate_volatility__mutmut_10, 
        'xǁVolatilityTrackerǁestimate_volatility__mutmut_11': xǁVolatilityTrackerǁestimate_volatility__mutmut_11, 
        'xǁVolatilityTrackerǁestimate_volatility__mutmut_12': xǁVolatilityTrackerǁestimate_volatility__mutmut_12, 
        'xǁVolatilityTrackerǁestimate_volatility__mutmut_13': xǁVolatilityTrackerǁestimate_volatility__mutmut_13, 
        'xǁVolatilityTrackerǁestimate_volatility__mutmut_14': xǁVolatilityTrackerǁestimate_volatility__mutmut_14, 
        'xǁVolatilityTrackerǁestimate_volatility__mutmut_15': xǁVolatilityTrackerǁestimate_volatility__mutmut_15, 
        'xǁVolatilityTrackerǁestimate_volatility__mutmut_16': xǁVolatilityTrackerǁestimate_volatility__mutmut_16, 
        'xǁVolatilityTrackerǁestimate_volatility__mutmut_17': xǁVolatilityTrackerǁestimate_volatility__mutmut_17, 
        'xǁVolatilityTrackerǁestimate_volatility__mutmut_18': xǁVolatilityTrackerǁestimate_volatility__mutmut_18, 
        'xǁVolatilityTrackerǁestimate_volatility__mutmut_19': xǁVolatilityTrackerǁestimate_volatility__mutmut_19, 
        'xǁVolatilityTrackerǁestimate_volatility__mutmut_20': xǁVolatilityTrackerǁestimate_volatility__mutmut_20, 
        'xǁVolatilityTrackerǁestimate_volatility__mutmut_21': xǁVolatilityTrackerǁestimate_volatility__mutmut_21, 
        'xǁVolatilityTrackerǁestimate_volatility__mutmut_22': xǁVolatilityTrackerǁestimate_volatility__mutmut_22, 
        'xǁVolatilityTrackerǁestimate_volatility__mutmut_23': xǁVolatilityTrackerǁestimate_volatility__mutmut_23, 
        'xǁVolatilityTrackerǁestimate_volatility__mutmut_24': xǁVolatilityTrackerǁestimate_volatility__mutmut_24, 
        'xǁVolatilityTrackerǁestimate_volatility__mutmut_25': xǁVolatilityTrackerǁestimate_volatility__mutmut_25, 
        'xǁVolatilityTrackerǁestimate_volatility__mutmut_26': xǁVolatilityTrackerǁestimate_volatility__mutmut_26, 
        'xǁVolatilityTrackerǁestimate_volatility__mutmut_27': xǁVolatilityTrackerǁestimate_volatility__mutmut_27, 
        'xǁVolatilityTrackerǁestimate_volatility__mutmut_28': xǁVolatilityTrackerǁestimate_volatility__mutmut_28, 
        'xǁVolatilityTrackerǁestimate_volatility__mutmut_29': xǁVolatilityTrackerǁestimate_volatility__mutmut_29, 
        'xǁVolatilityTrackerǁestimate_volatility__mutmut_30': xǁVolatilityTrackerǁestimate_volatility__mutmut_30, 
        'xǁVolatilityTrackerǁestimate_volatility__mutmut_31': xǁVolatilityTrackerǁestimate_volatility__mutmut_31, 
        'xǁVolatilityTrackerǁestimate_volatility__mutmut_32': xǁVolatilityTrackerǁestimate_volatility__mutmut_32, 
        'xǁVolatilityTrackerǁestimate_volatility__mutmut_33': xǁVolatilityTrackerǁestimate_volatility__mutmut_33, 
        'xǁVolatilityTrackerǁestimate_volatility__mutmut_34': xǁVolatilityTrackerǁestimate_volatility__mutmut_34, 
        'xǁVolatilityTrackerǁestimate_volatility__mutmut_35': xǁVolatilityTrackerǁestimate_volatility__mutmut_35, 
        'xǁVolatilityTrackerǁestimate_volatility__mutmut_36': xǁVolatilityTrackerǁestimate_volatility__mutmut_36, 
        'xǁVolatilityTrackerǁestimate_volatility__mutmut_37': xǁVolatilityTrackerǁestimate_volatility__mutmut_37, 
        'xǁVolatilityTrackerǁestimate_volatility__mutmut_38': xǁVolatilityTrackerǁestimate_volatility__mutmut_38, 
        'xǁVolatilityTrackerǁestimate_volatility__mutmut_39': xǁVolatilityTrackerǁestimate_volatility__mutmut_39, 
        'xǁVolatilityTrackerǁestimate_volatility__mutmut_40': xǁVolatilityTrackerǁestimate_volatility__mutmut_40, 
        'xǁVolatilityTrackerǁestimate_volatility__mutmut_41': xǁVolatilityTrackerǁestimate_volatility__mutmut_41, 
        'xǁVolatilityTrackerǁestimate_volatility__mutmut_42': xǁVolatilityTrackerǁestimate_volatility__mutmut_42, 
        'xǁVolatilityTrackerǁestimate_volatility__mutmut_43': xǁVolatilityTrackerǁestimate_volatility__mutmut_43, 
        'xǁVolatilityTrackerǁestimate_volatility__mutmut_44': xǁVolatilityTrackerǁestimate_volatility__mutmut_44, 
        'xǁVolatilityTrackerǁestimate_volatility__mutmut_45': xǁVolatilityTrackerǁestimate_volatility__mutmut_45, 
        'xǁVolatilityTrackerǁestimate_volatility__mutmut_46': xǁVolatilityTrackerǁestimate_volatility__mutmut_46, 
        'xǁVolatilityTrackerǁestimate_volatility__mutmut_47': xǁVolatilityTrackerǁestimate_volatility__mutmut_47, 
        'xǁVolatilityTrackerǁestimate_volatility__mutmut_48': xǁVolatilityTrackerǁestimate_volatility__mutmut_48, 
        'xǁVolatilityTrackerǁestimate_volatility__mutmut_49': xǁVolatilityTrackerǁestimate_volatility__mutmut_49, 
        'xǁVolatilityTrackerǁestimate_volatility__mutmut_50': xǁVolatilityTrackerǁestimate_volatility__mutmut_50, 
        'xǁVolatilityTrackerǁestimate_volatility__mutmut_51': xǁVolatilityTrackerǁestimate_volatility__mutmut_51, 
        'xǁVolatilityTrackerǁestimate_volatility__mutmut_52': xǁVolatilityTrackerǁestimate_volatility__mutmut_52, 
        'xǁVolatilityTrackerǁestimate_volatility__mutmut_53': xǁVolatilityTrackerǁestimate_volatility__mutmut_53, 
        'xǁVolatilityTrackerǁestimate_volatility__mutmut_54': xǁVolatilityTrackerǁestimate_volatility__mutmut_54, 
        'xǁVolatilityTrackerǁestimate_volatility__mutmut_55': xǁVolatilityTrackerǁestimate_volatility__mutmut_55, 
        'xǁVolatilityTrackerǁestimate_volatility__mutmut_56': xǁVolatilityTrackerǁestimate_volatility__mutmut_56, 
        'xǁVolatilityTrackerǁestimate_volatility__mutmut_57': xǁVolatilityTrackerǁestimate_volatility__mutmut_57, 
        'xǁVolatilityTrackerǁestimate_volatility__mutmut_58': xǁVolatilityTrackerǁestimate_volatility__mutmut_58, 
        'xǁVolatilityTrackerǁestimate_volatility__mutmut_59': xǁVolatilityTrackerǁestimate_volatility__mutmut_59
    }
    xǁVolatilityTrackerǁestimate_volatility__mutmut_orig.__name__ = 'xǁVolatilityTrackerǁestimate_volatility'

    def predict_volatility(self, horizon: int) -> float:
        args = [horizon]# type: ignore
        kwargs = {}# type: ignore
        return _mutmut_trampoline(object.__getattribute__(self, 'xǁVolatilityTrackerǁpredict_volatility__mutmut_orig'), object.__getattribute__(self, 'xǁVolatilityTrackerǁpredict_volatility__mutmut_mutants'), args, kwargs, self)

    def xǁVolatilityTrackerǁpredict_volatility__mutmut_orig(self, horizon: int) -> float:
        """
        Predict the conditional volatility h steps ahead using the
        GARCH(1,1) mean-reverting variance forecast:

          sigma^2_{t+h} = LR_var + (alpha+beta)^h * (sigma^2_t - LR_var)

        where LR_var = omega / (1 - alpha - beta).

        Parameters
        ----------
        horizon : int
            Number of steps ahead. Must be >= 1.

        Returns
        -------
        float
            Predicted volatility at horizon h. Always > 0.

        Raises
        ------
        ValueError
            If horizon < 1.
        """
        if horizon < 1:
            raise ValueError(
                f"horizon must be >= 1, got {horizon!r}."
            )

        persistence: float = self._alpha + self._beta
        sigma2_t: float = self._current_variance
        lr_var: float = self._long_run_variance

        # Mean-reverting GARCH forecast.
        predicted_variance: float = (
            lr_var + (persistence ** horizon) * (sigma2_t - lr_var)
        )

        # Floor for strict positivity.
        predicted_variance = max(_VOL_EPSILON ** 2, predicted_variance)

        return max(_VOL_EPSILON, math.sqrt(predicted_variance))

    def xǁVolatilityTrackerǁpredict_volatility__mutmut_1(self, horizon: int) -> float:
        """
        Predict the conditional volatility h steps ahead using the
        GARCH(1,1) mean-reverting variance forecast:

          sigma^2_{t+h} = LR_var + (alpha+beta)^h * (sigma^2_t - LR_var)

        where LR_var = omega / (1 - alpha - beta).

        Parameters
        ----------
        horizon : int
            Number of steps ahead. Must be >= 1.

        Returns
        -------
        float
            Predicted volatility at horizon h. Always > 0.

        Raises
        ------
        ValueError
            If horizon < 1.
        """
        if horizon <= 1:
            raise ValueError(
                f"horizon must be >= 1, got {horizon!r}."
            )

        persistence: float = self._alpha + self._beta
        sigma2_t: float = self._current_variance
        lr_var: float = self._long_run_variance

        # Mean-reverting GARCH forecast.
        predicted_variance: float = (
            lr_var + (persistence ** horizon) * (sigma2_t - lr_var)
        )

        # Floor for strict positivity.
        predicted_variance = max(_VOL_EPSILON ** 2, predicted_variance)

        return max(_VOL_EPSILON, math.sqrt(predicted_variance))

    def xǁVolatilityTrackerǁpredict_volatility__mutmut_2(self, horizon: int) -> float:
        """
        Predict the conditional volatility h steps ahead using the
        GARCH(1,1) mean-reverting variance forecast:

          sigma^2_{t+h} = LR_var + (alpha+beta)^h * (sigma^2_t - LR_var)

        where LR_var = omega / (1 - alpha - beta).

        Parameters
        ----------
        horizon : int
            Number of steps ahead. Must be >= 1.

        Returns
        -------
        float
            Predicted volatility at horizon h. Always > 0.

        Raises
        ------
        ValueError
            If horizon < 1.
        """
        if horizon < 2:
            raise ValueError(
                f"horizon must be >= 1, got {horizon!r}."
            )

        persistence: float = self._alpha + self._beta
        sigma2_t: float = self._current_variance
        lr_var: float = self._long_run_variance

        # Mean-reverting GARCH forecast.
        predicted_variance: float = (
            lr_var + (persistence ** horizon) * (sigma2_t - lr_var)
        )

        # Floor for strict positivity.
        predicted_variance = max(_VOL_EPSILON ** 2, predicted_variance)

        return max(_VOL_EPSILON, math.sqrt(predicted_variance))

    def xǁVolatilityTrackerǁpredict_volatility__mutmut_3(self, horizon: int) -> float:
        """
        Predict the conditional volatility h steps ahead using the
        GARCH(1,1) mean-reverting variance forecast:

          sigma^2_{t+h} = LR_var + (alpha+beta)^h * (sigma^2_t - LR_var)

        where LR_var = omega / (1 - alpha - beta).

        Parameters
        ----------
        horizon : int
            Number of steps ahead. Must be >= 1.

        Returns
        -------
        float
            Predicted volatility at horizon h. Always > 0.

        Raises
        ------
        ValueError
            If horizon < 1.
        """
        if horizon < 1:
            raise ValueError(
                None
            )

        persistence: float = self._alpha + self._beta
        sigma2_t: float = self._current_variance
        lr_var: float = self._long_run_variance

        # Mean-reverting GARCH forecast.
        predicted_variance: float = (
            lr_var + (persistence ** horizon) * (sigma2_t - lr_var)
        )

        # Floor for strict positivity.
        predicted_variance = max(_VOL_EPSILON ** 2, predicted_variance)

        return max(_VOL_EPSILON, math.sqrt(predicted_variance))

    def xǁVolatilityTrackerǁpredict_volatility__mutmut_4(self, horizon: int) -> float:
        """
        Predict the conditional volatility h steps ahead using the
        GARCH(1,1) mean-reverting variance forecast:

          sigma^2_{t+h} = LR_var + (alpha+beta)^h * (sigma^2_t - LR_var)

        where LR_var = omega / (1 - alpha - beta).

        Parameters
        ----------
        horizon : int
            Number of steps ahead. Must be >= 1.

        Returns
        -------
        float
            Predicted volatility at horizon h. Always > 0.

        Raises
        ------
        ValueError
            If horizon < 1.
        """
        if horizon < 1:
            raise ValueError(
                f"horizon must be >= 1, got {horizon!r}."
            )

        persistence: float = None
        sigma2_t: float = self._current_variance
        lr_var: float = self._long_run_variance

        # Mean-reverting GARCH forecast.
        predicted_variance: float = (
            lr_var + (persistence ** horizon) * (sigma2_t - lr_var)
        )

        # Floor for strict positivity.
        predicted_variance = max(_VOL_EPSILON ** 2, predicted_variance)

        return max(_VOL_EPSILON, math.sqrt(predicted_variance))

    def xǁVolatilityTrackerǁpredict_volatility__mutmut_5(self, horizon: int) -> float:
        """
        Predict the conditional volatility h steps ahead using the
        GARCH(1,1) mean-reverting variance forecast:

          sigma^2_{t+h} = LR_var + (alpha+beta)^h * (sigma^2_t - LR_var)

        where LR_var = omega / (1 - alpha - beta).

        Parameters
        ----------
        horizon : int
            Number of steps ahead. Must be >= 1.

        Returns
        -------
        float
            Predicted volatility at horizon h. Always > 0.

        Raises
        ------
        ValueError
            If horizon < 1.
        """
        if horizon < 1:
            raise ValueError(
                f"horizon must be >= 1, got {horizon!r}."
            )

        persistence: float = self._alpha - self._beta
        sigma2_t: float = self._current_variance
        lr_var: float = self._long_run_variance

        # Mean-reverting GARCH forecast.
        predicted_variance: float = (
            lr_var + (persistence ** horizon) * (sigma2_t - lr_var)
        )

        # Floor for strict positivity.
        predicted_variance = max(_VOL_EPSILON ** 2, predicted_variance)

        return max(_VOL_EPSILON, math.sqrt(predicted_variance))

    def xǁVolatilityTrackerǁpredict_volatility__mutmut_6(self, horizon: int) -> float:
        """
        Predict the conditional volatility h steps ahead using the
        GARCH(1,1) mean-reverting variance forecast:

          sigma^2_{t+h} = LR_var + (alpha+beta)^h * (sigma^2_t - LR_var)

        where LR_var = omega / (1 - alpha - beta).

        Parameters
        ----------
        horizon : int
            Number of steps ahead. Must be >= 1.

        Returns
        -------
        float
            Predicted volatility at horizon h. Always > 0.

        Raises
        ------
        ValueError
            If horizon < 1.
        """
        if horizon < 1:
            raise ValueError(
                f"horizon must be >= 1, got {horizon!r}."
            )

        persistence: float = self._alpha + self._beta
        sigma2_t: float = None
        lr_var: float = self._long_run_variance

        # Mean-reverting GARCH forecast.
        predicted_variance: float = (
            lr_var + (persistence ** horizon) * (sigma2_t - lr_var)
        )

        # Floor for strict positivity.
        predicted_variance = max(_VOL_EPSILON ** 2, predicted_variance)

        return max(_VOL_EPSILON, math.sqrt(predicted_variance))

    def xǁVolatilityTrackerǁpredict_volatility__mutmut_7(self, horizon: int) -> float:
        """
        Predict the conditional volatility h steps ahead using the
        GARCH(1,1) mean-reverting variance forecast:

          sigma^2_{t+h} = LR_var + (alpha+beta)^h * (sigma^2_t - LR_var)

        where LR_var = omega / (1 - alpha - beta).

        Parameters
        ----------
        horizon : int
            Number of steps ahead. Must be >= 1.

        Returns
        -------
        float
            Predicted volatility at horizon h. Always > 0.

        Raises
        ------
        ValueError
            If horizon < 1.
        """
        if horizon < 1:
            raise ValueError(
                f"horizon must be >= 1, got {horizon!r}."
            )

        persistence: float = self._alpha + self._beta
        sigma2_t: float = self._current_variance
        lr_var: float = None

        # Mean-reverting GARCH forecast.
        predicted_variance: float = (
            lr_var + (persistence ** horizon) * (sigma2_t - lr_var)
        )

        # Floor for strict positivity.
        predicted_variance = max(_VOL_EPSILON ** 2, predicted_variance)

        return max(_VOL_EPSILON, math.sqrt(predicted_variance))

    def xǁVolatilityTrackerǁpredict_volatility__mutmut_8(self, horizon: int) -> float:
        """
        Predict the conditional volatility h steps ahead using the
        GARCH(1,1) mean-reverting variance forecast:

          sigma^2_{t+h} = LR_var + (alpha+beta)^h * (sigma^2_t - LR_var)

        where LR_var = omega / (1 - alpha - beta).

        Parameters
        ----------
        horizon : int
            Number of steps ahead. Must be >= 1.

        Returns
        -------
        float
            Predicted volatility at horizon h. Always > 0.

        Raises
        ------
        ValueError
            If horizon < 1.
        """
        if horizon < 1:
            raise ValueError(
                f"horizon must be >= 1, got {horizon!r}."
            )

        persistence: float = self._alpha + self._beta
        sigma2_t: float = self._current_variance
        lr_var: float = self._long_run_variance

        # Mean-reverting GARCH forecast.
        predicted_variance: float = None

        # Floor for strict positivity.
        predicted_variance = max(_VOL_EPSILON ** 2, predicted_variance)

        return max(_VOL_EPSILON, math.sqrt(predicted_variance))

    def xǁVolatilityTrackerǁpredict_volatility__mutmut_9(self, horizon: int) -> float:
        """
        Predict the conditional volatility h steps ahead using the
        GARCH(1,1) mean-reverting variance forecast:

          sigma^2_{t+h} = LR_var + (alpha+beta)^h * (sigma^2_t - LR_var)

        where LR_var = omega / (1 - alpha - beta).

        Parameters
        ----------
        horizon : int
            Number of steps ahead. Must be >= 1.

        Returns
        -------
        float
            Predicted volatility at horizon h. Always > 0.

        Raises
        ------
        ValueError
            If horizon < 1.
        """
        if horizon < 1:
            raise ValueError(
                f"horizon must be >= 1, got {horizon!r}."
            )

        persistence: float = self._alpha + self._beta
        sigma2_t: float = self._current_variance
        lr_var: float = self._long_run_variance

        # Mean-reverting GARCH forecast.
        predicted_variance: float = (
            lr_var - (persistence ** horizon) * (sigma2_t - lr_var)
        )

        # Floor for strict positivity.
        predicted_variance = max(_VOL_EPSILON ** 2, predicted_variance)

        return max(_VOL_EPSILON, math.sqrt(predicted_variance))

    def xǁVolatilityTrackerǁpredict_volatility__mutmut_10(self, horizon: int) -> float:
        """
        Predict the conditional volatility h steps ahead using the
        GARCH(1,1) mean-reverting variance forecast:

          sigma^2_{t+h} = LR_var + (alpha+beta)^h * (sigma^2_t - LR_var)

        where LR_var = omega / (1 - alpha - beta).

        Parameters
        ----------
        horizon : int
            Number of steps ahead. Must be >= 1.

        Returns
        -------
        float
            Predicted volatility at horizon h. Always > 0.

        Raises
        ------
        ValueError
            If horizon < 1.
        """
        if horizon < 1:
            raise ValueError(
                f"horizon must be >= 1, got {horizon!r}."
            )

        persistence: float = self._alpha + self._beta
        sigma2_t: float = self._current_variance
        lr_var: float = self._long_run_variance

        # Mean-reverting GARCH forecast.
        predicted_variance: float = (
            lr_var + (persistence ** horizon) / (sigma2_t - lr_var)
        )

        # Floor for strict positivity.
        predicted_variance = max(_VOL_EPSILON ** 2, predicted_variance)

        return max(_VOL_EPSILON, math.sqrt(predicted_variance))

    def xǁVolatilityTrackerǁpredict_volatility__mutmut_11(self, horizon: int) -> float:
        """
        Predict the conditional volatility h steps ahead using the
        GARCH(1,1) mean-reverting variance forecast:

          sigma^2_{t+h} = LR_var + (alpha+beta)^h * (sigma^2_t - LR_var)

        where LR_var = omega / (1 - alpha - beta).

        Parameters
        ----------
        horizon : int
            Number of steps ahead. Must be >= 1.

        Returns
        -------
        float
            Predicted volatility at horizon h. Always > 0.

        Raises
        ------
        ValueError
            If horizon < 1.
        """
        if horizon < 1:
            raise ValueError(
                f"horizon must be >= 1, got {horizon!r}."
            )

        persistence: float = self._alpha + self._beta
        sigma2_t: float = self._current_variance
        lr_var: float = self._long_run_variance

        # Mean-reverting GARCH forecast.
        predicted_variance: float = (
            lr_var + (persistence * horizon) * (sigma2_t - lr_var)
        )

        # Floor for strict positivity.
        predicted_variance = max(_VOL_EPSILON ** 2, predicted_variance)

        return max(_VOL_EPSILON, math.sqrt(predicted_variance))

    def xǁVolatilityTrackerǁpredict_volatility__mutmut_12(self, horizon: int) -> float:
        """
        Predict the conditional volatility h steps ahead using the
        GARCH(1,1) mean-reverting variance forecast:

          sigma^2_{t+h} = LR_var + (alpha+beta)^h * (sigma^2_t - LR_var)

        where LR_var = omega / (1 - alpha - beta).

        Parameters
        ----------
        horizon : int
            Number of steps ahead. Must be >= 1.

        Returns
        -------
        float
            Predicted volatility at horizon h. Always > 0.

        Raises
        ------
        ValueError
            If horizon < 1.
        """
        if horizon < 1:
            raise ValueError(
                f"horizon must be >= 1, got {horizon!r}."
            )

        persistence: float = self._alpha + self._beta
        sigma2_t: float = self._current_variance
        lr_var: float = self._long_run_variance

        # Mean-reverting GARCH forecast.
        predicted_variance: float = (
            lr_var + (persistence ** horizon) * (sigma2_t + lr_var)
        )

        # Floor for strict positivity.
        predicted_variance = max(_VOL_EPSILON ** 2, predicted_variance)

        return max(_VOL_EPSILON, math.sqrt(predicted_variance))

    def xǁVolatilityTrackerǁpredict_volatility__mutmut_13(self, horizon: int) -> float:
        """
        Predict the conditional volatility h steps ahead using the
        GARCH(1,1) mean-reverting variance forecast:

          sigma^2_{t+h} = LR_var + (alpha+beta)^h * (sigma^2_t - LR_var)

        where LR_var = omega / (1 - alpha - beta).

        Parameters
        ----------
        horizon : int
            Number of steps ahead. Must be >= 1.

        Returns
        -------
        float
            Predicted volatility at horizon h. Always > 0.

        Raises
        ------
        ValueError
            If horizon < 1.
        """
        if horizon < 1:
            raise ValueError(
                f"horizon must be >= 1, got {horizon!r}."
            )

        persistence: float = self._alpha + self._beta
        sigma2_t: float = self._current_variance
        lr_var: float = self._long_run_variance

        # Mean-reverting GARCH forecast.
        predicted_variance: float = (
            lr_var + (persistence ** horizon) * (sigma2_t - lr_var)
        )

        # Floor for strict positivity.
        predicted_variance = None

        return max(_VOL_EPSILON, math.sqrt(predicted_variance))

    def xǁVolatilityTrackerǁpredict_volatility__mutmut_14(self, horizon: int) -> float:
        """
        Predict the conditional volatility h steps ahead using the
        GARCH(1,1) mean-reverting variance forecast:

          sigma^2_{t+h} = LR_var + (alpha+beta)^h * (sigma^2_t - LR_var)

        where LR_var = omega / (1 - alpha - beta).

        Parameters
        ----------
        horizon : int
            Number of steps ahead. Must be >= 1.

        Returns
        -------
        float
            Predicted volatility at horizon h. Always > 0.

        Raises
        ------
        ValueError
            If horizon < 1.
        """
        if horizon < 1:
            raise ValueError(
                f"horizon must be >= 1, got {horizon!r}."
            )

        persistence: float = self._alpha + self._beta
        sigma2_t: float = self._current_variance
        lr_var: float = self._long_run_variance

        # Mean-reverting GARCH forecast.
        predicted_variance: float = (
            lr_var + (persistence ** horizon) * (sigma2_t - lr_var)
        )

        # Floor for strict positivity.
        predicted_variance = max(None, predicted_variance)

        return max(_VOL_EPSILON, math.sqrt(predicted_variance))

    def xǁVolatilityTrackerǁpredict_volatility__mutmut_15(self, horizon: int) -> float:
        """
        Predict the conditional volatility h steps ahead using the
        GARCH(1,1) mean-reverting variance forecast:

          sigma^2_{t+h} = LR_var + (alpha+beta)^h * (sigma^2_t - LR_var)

        where LR_var = omega / (1 - alpha - beta).

        Parameters
        ----------
        horizon : int
            Number of steps ahead. Must be >= 1.

        Returns
        -------
        float
            Predicted volatility at horizon h. Always > 0.

        Raises
        ------
        ValueError
            If horizon < 1.
        """
        if horizon < 1:
            raise ValueError(
                f"horizon must be >= 1, got {horizon!r}."
            )

        persistence: float = self._alpha + self._beta
        sigma2_t: float = self._current_variance
        lr_var: float = self._long_run_variance

        # Mean-reverting GARCH forecast.
        predicted_variance: float = (
            lr_var + (persistence ** horizon) * (sigma2_t - lr_var)
        )

        # Floor for strict positivity.
        predicted_variance = max(_VOL_EPSILON ** 2, None)

        return max(_VOL_EPSILON, math.sqrt(predicted_variance))

    def xǁVolatilityTrackerǁpredict_volatility__mutmut_16(self, horizon: int) -> float:
        """
        Predict the conditional volatility h steps ahead using the
        GARCH(1,1) mean-reverting variance forecast:

          sigma^2_{t+h} = LR_var + (alpha+beta)^h * (sigma^2_t - LR_var)

        where LR_var = omega / (1 - alpha - beta).

        Parameters
        ----------
        horizon : int
            Number of steps ahead. Must be >= 1.

        Returns
        -------
        float
            Predicted volatility at horizon h. Always > 0.

        Raises
        ------
        ValueError
            If horizon < 1.
        """
        if horizon < 1:
            raise ValueError(
                f"horizon must be >= 1, got {horizon!r}."
            )

        persistence: float = self._alpha + self._beta
        sigma2_t: float = self._current_variance
        lr_var: float = self._long_run_variance

        # Mean-reverting GARCH forecast.
        predicted_variance: float = (
            lr_var + (persistence ** horizon) * (sigma2_t - lr_var)
        )

        # Floor for strict positivity.
        predicted_variance = max(predicted_variance)

        return max(_VOL_EPSILON, math.sqrt(predicted_variance))

    def xǁVolatilityTrackerǁpredict_volatility__mutmut_17(self, horizon: int) -> float:
        """
        Predict the conditional volatility h steps ahead using the
        GARCH(1,1) mean-reverting variance forecast:

          sigma^2_{t+h} = LR_var + (alpha+beta)^h * (sigma^2_t - LR_var)

        where LR_var = omega / (1 - alpha - beta).

        Parameters
        ----------
        horizon : int
            Number of steps ahead. Must be >= 1.

        Returns
        -------
        float
            Predicted volatility at horizon h. Always > 0.

        Raises
        ------
        ValueError
            If horizon < 1.
        """
        if horizon < 1:
            raise ValueError(
                f"horizon must be >= 1, got {horizon!r}."
            )

        persistence: float = self._alpha + self._beta
        sigma2_t: float = self._current_variance
        lr_var: float = self._long_run_variance

        # Mean-reverting GARCH forecast.
        predicted_variance: float = (
            lr_var + (persistence ** horizon) * (sigma2_t - lr_var)
        )

        # Floor for strict positivity.
        predicted_variance = max(_VOL_EPSILON ** 2, )

        return max(_VOL_EPSILON, math.sqrt(predicted_variance))

    def xǁVolatilityTrackerǁpredict_volatility__mutmut_18(self, horizon: int) -> float:
        """
        Predict the conditional volatility h steps ahead using the
        GARCH(1,1) mean-reverting variance forecast:

          sigma^2_{t+h} = LR_var + (alpha+beta)^h * (sigma^2_t - LR_var)

        where LR_var = omega / (1 - alpha - beta).

        Parameters
        ----------
        horizon : int
            Number of steps ahead. Must be >= 1.

        Returns
        -------
        float
            Predicted volatility at horizon h. Always > 0.

        Raises
        ------
        ValueError
            If horizon < 1.
        """
        if horizon < 1:
            raise ValueError(
                f"horizon must be >= 1, got {horizon!r}."
            )

        persistence: float = self._alpha + self._beta
        sigma2_t: float = self._current_variance
        lr_var: float = self._long_run_variance

        # Mean-reverting GARCH forecast.
        predicted_variance: float = (
            lr_var + (persistence ** horizon) * (sigma2_t - lr_var)
        )

        # Floor for strict positivity.
        predicted_variance = max(_VOL_EPSILON * 2, predicted_variance)

        return max(_VOL_EPSILON, math.sqrt(predicted_variance))

    def xǁVolatilityTrackerǁpredict_volatility__mutmut_19(self, horizon: int) -> float:
        """
        Predict the conditional volatility h steps ahead using the
        GARCH(1,1) mean-reverting variance forecast:

          sigma^2_{t+h} = LR_var + (alpha+beta)^h * (sigma^2_t - LR_var)

        where LR_var = omega / (1 - alpha - beta).

        Parameters
        ----------
        horizon : int
            Number of steps ahead. Must be >= 1.

        Returns
        -------
        float
            Predicted volatility at horizon h. Always > 0.

        Raises
        ------
        ValueError
            If horizon < 1.
        """
        if horizon < 1:
            raise ValueError(
                f"horizon must be >= 1, got {horizon!r}."
            )

        persistence: float = self._alpha + self._beta
        sigma2_t: float = self._current_variance
        lr_var: float = self._long_run_variance

        # Mean-reverting GARCH forecast.
        predicted_variance: float = (
            lr_var + (persistence ** horizon) * (sigma2_t - lr_var)
        )

        # Floor for strict positivity.
        predicted_variance = max(_VOL_EPSILON ** 3, predicted_variance)

        return max(_VOL_EPSILON, math.sqrt(predicted_variance))

    def xǁVolatilityTrackerǁpredict_volatility__mutmut_20(self, horizon: int) -> float:
        """
        Predict the conditional volatility h steps ahead using the
        GARCH(1,1) mean-reverting variance forecast:

          sigma^2_{t+h} = LR_var + (alpha+beta)^h * (sigma^2_t - LR_var)

        where LR_var = omega / (1 - alpha - beta).

        Parameters
        ----------
        horizon : int
            Number of steps ahead. Must be >= 1.

        Returns
        -------
        float
            Predicted volatility at horizon h. Always > 0.

        Raises
        ------
        ValueError
            If horizon < 1.
        """
        if horizon < 1:
            raise ValueError(
                f"horizon must be >= 1, got {horizon!r}."
            )

        persistence: float = self._alpha + self._beta
        sigma2_t: float = self._current_variance
        lr_var: float = self._long_run_variance

        # Mean-reverting GARCH forecast.
        predicted_variance: float = (
            lr_var + (persistence ** horizon) * (sigma2_t - lr_var)
        )

        # Floor for strict positivity.
        predicted_variance = max(_VOL_EPSILON ** 2, predicted_variance)

        return max(None, math.sqrt(predicted_variance))

    def xǁVolatilityTrackerǁpredict_volatility__mutmut_21(self, horizon: int) -> float:
        """
        Predict the conditional volatility h steps ahead using the
        GARCH(1,1) mean-reverting variance forecast:

          sigma^2_{t+h} = LR_var + (alpha+beta)^h * (sigma^2_t - LR_var)

        where LR_var = omega / (1 - alpha - beta).

        Parameters
        ----------
        horizon : int
            Number of steps ahead. Must be >= 1.

        Returns
        -------
        float
            Predicted volatility at horizon h. Always > 0.

        Raises
        ------
        ValueError
            If horizon < 1.
        """
        if horizon < 1:
            raise ValueError(
                f"horizon must be >= 1, got {horizon!r}."
            )

        persistence: float = self._alpha + self._beta
        sigma2_t: float = self._current_variance
        lr_var: float = self._long_run_variance

        # Mean-reverting GARCH forecast.
        predicted_variance: float = (
            lr_var + (persistence ** horizon) * (sigma2_t - lr_var)
        )

        # Floor for strict positivity.
        predicted_variance = max(_VOL_EPSILON ** 2, predicted_variance)

        return max(_VOL_EPSILON, None)

    def xǁVolatilityTrackerǁpredict_volatility__mutmut_22(self, horizon: int) -> float:
        """
        Predict the conditional volatility h steps ahead using the
        GARCH(1,1) mean-reverting variance forecast:

          sigma^2_{t+h} = LR_var + (alpha+beta)^h * (sigma^2_t - LR_var)

        where LR_var = omega / (1 - alpha - beta).

        Parameters
        ----------
        horizon : int
            Number of steps ahead. Must be >= 1.

        Returns
        -------
        float
            Predicted volatility at horizon h. Always > 0.

        Raises
        ------
        ValueError
            If horizon < 1.
        """
        if horizon < 1:
            raise ValueError(
                f"horizon must be >= 1, got {horizon!r}."
            )

        persistence: float = self._alpha + self._beta
        sigma2_t: float = self._current_variance
        lr_var: float = self._long_run_variance

        # Mean-reverting GARCH forecast.
        predicted_variance: float = (
            lr_var + (persistence ** horizon) * (sigma2_t - lr_var)
        )

        # Floor for strict positivity.
        predicted_variance = max(_VOL_EPSILON ** 2, predicted_variance)

        return max(math.sqrt(predicted_variance))

    def xǁVolatilityTrackerǁpredict_volatility__mutmut_23(self, horizon: int) -> float:
        """
        Predict the conditional volatility h steps ahead using the
        GARCH(1,1) mean-reverting variance forecast:

          sigma^2_{t+h} = LR_var + (alpha+beta)^h * (sigma^2_t - LR_var)

        where LR_var = omega / (1 - alpha - beta).

        Parameters
        ----------
        horizon : int
            Number of steps ahead. Must be >= 1.

        Returns
        -------
        float
            Predicted volatility at horizon h. Always > 0.

        Raises
        ------
        ValueError
            If horizon < 1.
        """
        if horizon < 1:
            raise ValueError(
                f"horizon must be >= 1, got {horizon!r}."
            )

        persistence: float = self._alpha + self._beta
        sigma2_t: float = self._current_variance
        lr_var: float = self._long_run_variance

        # Mean-reverting GARCH forecast.
        predicted_variance: float = (
            lr_var + (persistence ** horizon) * (sigma2_t - lr_var)
        )

        # Floor for strict positivity.
        predicted_variance = max(_VOL_EPSILON ** 2, predicted_variance)

        return max(_VOL_EPSILON, )

    def xǁVolatilityTrackerǁpredict_volatility__mutmut_24(self, horizon: int) -> float:
        """
        Predict the conditional volatility h steps ahead using the
        GARCH(1,1) mean-reverting variance forecast:

          sigma^2_{t+h} = LR_var + (alpha+beta)^h * (sigma^2_t - LR_var)

        where LR_var = omega / (1 - alpha - beta).

        Parameters
        ----------
        horizon : int
            Number of steps ahead. Must be >= 1.

        Returns
        -------
        float
            Predicted volatility at horizon h. Always > 0.

        Raises
        ------
        ValueError
            If horizon < 1.
        """
        if horizon < 1:
            raise ValueError(
                f"horizon must be >= 1, got {horizon!r}."
            )

        persistence: float = self._alpha + self._beta
        sigma2_t: float = self._current_variance
        lr_var: float = self._long_run_variance

        # Mean-reverting GARCH forecast.
        predicted_variance: float = (
            lr_var + (persistence ** horizon) * (sigma2_t - lr_var)
        )

        # Floor for strict positivity.
        predicted_variance = max(_VOL_EPSILON ** 2, predicted_variance)

        return max(_VOL_EPSILON, math.sqrt(None))
    
    xǁVolatilityTrackerǁpredict_volatility__mutmut_mutants : ClassVar[MutantDict] = { # type: ignore
    'xǁVolatilityTrackerǁpredict_volatility__mutmut_1': xǁVolatilityTrackerǁpredict_volatility__mutmut_1, 
        'xǁVolatilityTrackerǁpredict_volatility__mutmut_2': xǁVolatilityTrackerǁpredict_volatility__mutmut_2, 
        'xǁVolatilityTrackerǁpredict_volatility__mutmut_3': xǁVolatilityTrackerǁpredict_volatility__mutmut_3, 
        'xǁVolatilityTrackerǁpredict_volatility__mutmut_4': xǁVolatilityTrackerǁpredict_volatility__mutmut_4, 
        'xǁVolatilityTrackerǁpredict_volatility__mutmut_5': xǁVolatilityTrackerǁpredict_volatility__mutmut_5, 
        'xǁVolatilityTrackerǁpredict_volatility__mutmut_6': xǁVolatilityTrackerǁpredict_volatility__mutmut_6, 
        'xǁVolatilityTrackerǁpredict_volatility__mutmut_7': xǁVolatilityTrackerǁpredict_volatility__mutmut_7, 
        'xǁVolatilityTrackerǁpredict_volatility__mutmut_8': xǁVolatilityTrackerǁpredict_volatility__mutmut_8, 
        'xǁVolatilityTrackerǁpredict_volatility__mutmut_9': xǁVolatilityTrackerǁpredict_volatility__mutmut_9, 
        'xǁVolatilityTrackerǁpredict_volatility__mutmut_10': xǁVolatilityTrackerǁpredict_volatility__mutmut_10, 
        'xǁVolatilityTrackerǁpredict_volatility__mutmut_11': xǁVolatilityTrackerǁpredict_volatility__mutmut_11, 
        'xǁVolatilityTrackerǁpredict_volatility__mutmut_12': xǁVolatilityTrackerǁpredict_volatility__mutmut_12, 
        'xǁVolatilityTrackerǁpredict_volatility__mutmut_13': xǁVolatilityTrackerǁpredict_volatility__mutmut_13, 
        'xǁVolatilityTrackerǁpredict_volatility__mutmut_14': xǁVolatilityTrackerǁpredict_volatility__mutmut_14, 
        'xǁVolatilityTrackerǁpredict_volatility__mutmut_15': xǁVolatilityTrackerǁpredict_volatility__mutmut_15, 
        'xǁVolatilityTrackerǁpredict_volatility__mutmut_16': xǁVolatilityTrackerǁpredict_volatility__mutmut_16, 
        'xǁVolatilityTrackerǁpredict_volatility__mutmut_17': xǁVolatilityTrackerǁpredict_volatility__mutmut_17, 
        'xǁVolatilityTrackerǁpredict_volatility__mutmut_18': xǁVolatilityTrackerǁpredict_volatility__mutmut_18, 
        'xǁVolatilityTrackerǁpredict_volatility__mutmut_19': xǁVolatilityTrackerǁpredict_volatility__mutmut_19, 
        'xǁVolatilityTrackerǁpredict_volatility__mutmut_20': xǁVolatilityTrackerǁpredict_volatility__mutmut_20, 
        'xǁVolatilityTrackerǁpredict_volatility__mutmut_21': xǁVolatilityTrackerǁpredict_volatility__mutmut_21, 
        'xǁVolatilityTrackerǁpredict_volatility__mutmut_22': xǁVolatilityTrackerǁpredict_volatility__mutmut_22, 
        'xǁVolatilityTrackerǁpredict_volatility__mutmut_23': xǁVolatilityTrackerǁpredict_volatility__mutmut_23, 
        'xǁVolatilityTrackerǁpredict_volatility__mutmut_24': xǁVolatilityTrackerǁpredict_volatility__mutmut_24
    }
    xǁVolatilityTrackerǁpredict_volatility__mutmut_orig.__name__ = 'xǁVolatilityTrackerǁpredict_volatility'

    @property
    def current_variance(self) -> float:
        """Current conditional variance sigma^2_t. Always > 0."""
        return self._current_variance

    @property
    def current_volatility(self) -> float:
        """Current conditional volatility sqrt(sigma^2_t). Always > 0."""
        return max(_VOL_EPSILON, math.sqrt(self._current_variance))

    @property
    def long_run_variance(self) -> float:
        """Unconditional long-run variance omega / (1-alpha-beta). Always > 0."""
        return self._long_run_variance

    @property
    def parameters(self) -> dict:
        """Return GARCH parameters as a plain dict (read-only view)."""
        return {
            "omega": self._omega,
            "alpha": self._alpha,
            "beta":  self._beta,
        }

    def reset(self) -> None:
        args = []# type: ignore
        kwargs = {}# type: ignore
        return _mutmut_trampoline(object.__getattribute__(self, 'xǁVolatilityTrackerǁreset__mutmut_orig'), object.__getattribute__(self, 'xǁVolatilityTrackerǁreset__mutmut_mutants'), args, kwargs, self)

    def xǁVolatilityTrackerǁreset__mutmut_orig(self) -> None:
        """
        Reset the current variance to the long-run variance.
        Useful for re-initialising the tracker without creating a new instance.
        """
        self._current_variance = self._long_run_variance

    def xǁVolatilityTrackerǁreset__mutmut_1(self) -> None:
        """
        Reset the current variance to the long-run variance.
        Useful for re-initialising the tracker without creating a new instance.
        """
        self._current_variance = None
    
    xǁVolatilityTrackerǁreset__mutmut_mutants : ClassVar[MutantDict] = { # type: ignore
    'xǁVolatilityTrackerǁreset__mutmut_1': xǁVolatilityTrackerǁreset__mutmut_1
    }
    xǁVolatilityTrackerǁreset__mutmut_orig.__name__ = 'xǁVolatilityTrackerǁreset'
