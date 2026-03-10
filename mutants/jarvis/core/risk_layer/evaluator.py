# =============================================================================
# JARVIS v6.1.0 -- PHASE 7B: RISK & CAPITAL MANAGEMENT LAYER
# File:   jarvis/core/risk_layer/evaluator.py
# Authority: JARVIS FAS v6.1.0 -- Phase 7B, Risk Evaluation Engine
# =============================================================================
#
# SCOPE
# -----
# Implements the risk evaluation entry points for Phase 7B.
# Exactly three public symbols are defined:
#
#   RiskDecision            -- frozen dataclass; output of all evaluation calls.
#   evaluate_position_risk  -- position-level risk check.
#   evaluate_portfolio_risk -- portfolio-level risk check (no position input).
#
# WHAT IS NOT IN THIS FILE
# ------------------------
#   No sizing logic.
#   No order execution logic.
#   No volatility-adjusted caps (Phase 7C+).
#   No liquidity haircuts (Phase 7C+).
#   No Kelly sizing (Phase 7C+).
#   No I/O of any kind.
#   No logging.
#   No global mutable state.
#
# DRAWDOWN THRESHOLD DERIVATION
# ------------------------------
# PortfolioState carries nav, peak_nav, and realized_drawdown_pct.
# RiskParameters carries max_drawdown_hard_stop and max_drawdown_soft_warn
# as fractions of peak_nav (e.g. 0.10 = 10% drawdown from peak).
#
# The spec references hard_stop_nav and soft_warn_nav as absolute NAV levels.
# These are not stored fields; they are derived per evaluation call:
#
#   hard_stop_nav = peak_nav * (1.0 - max_drawdown_hard_stop)
#   soft_warn_nav = peak_nav * (1.0 - max_drawdown_soft_warn)
#
# Comparison is then:
#   nav <= hard_stop_nav  ->  HALT      (hard stop; all new risk halted)
#   nav <= soft_warn_nav  ->  REDUCE    (soft warn; reduce sizing)
#   otherwise             ->  APPROVE   (within limits)
#
# Hard stop is checked before soft warn (fail-fast; most severe wins).
#
# VERDICT MAPPING
# ---------------
# The spec names HARD_STOP and SOFT_WARN, which do not match the RiskVerdict
# enum defined in domain.py. The correct mapping is:
#
#   Spec HARD_STOP  ->  RiskVerdict.HALT
#   Spec SOFT_WARN  ->  RiskVerdict.REDUCE
#   Spec OK         ->  RiskVerdict.APPROVE
#
# RiskVerdict is the canonical enum; spec shorthand labels are not exposed.
#
# DETERMINISM CONSTRAINTS
# -----------------------
# DET-01  No stochastic operations.
# DET-02  All inputs passed explicitly. No module-level mutable reads.
# DET-03  No side effects. RiskDecision is frozen; inputs are never mutated.
# DET-04  All comparisons are deterministic arithmetic on validated floats.
# DET-05  No datetime.now() / time.time().
# DET-06  No random / secrets / uuid.
#
# PROHIBITED ACTIONS CONFIRMED ABSENT
# ------------------------------------
#   No numpy / scipy
#   No logging module
#   No datetime.now() / time.time()
#   No random / secrets / uuid
#   No file IO / network IO
#   No mutation of any input argument
#   No global or module-level mutable state
#   No circular imports (imports only from sibling modules and data_layer)
# =============================================================================

from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Optional, Tuple

from jarvis.core.data_layer import VALID_ASSET_CLASSES

from .domain import (
    PortfolioState,
    PositionSpec,
    RiskParameters,
    RiskVerdict,
)
from .exceptions import RiskValidationError
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


# =============================================================================
# SECTION 1 -- RISK DECISION (OUTPUT CONTRACT)
# =============================================================================

@dataclass(frozen=True)
class RiskDecision:
    """
    Immutable output of a risk evaluation call.

    Produced by evaluate_position_risk() and evaluate_portfolio_risk().
    Never constructed directly by callers of the public API; always returned
    by one of the evaluation functions.

    Attributes:
        verdict:             The risk engine's decision. Always a RiskVerdict
                             member. Never None.
        messages:            Ordered tuple of human-readable diagnostic strings.
                             Empty tuple when no messages apply. Never a list.
                             Each string is ASCII-safe and non-empty.
        max_position_size:   Optional USD cap on position size this cycle.
                             None when no explicit cap is being enforced by
                             this evaluation (e.g. cap logic is Phase 7C+).
                             When present: finite, > 0.
        requires_rebalance:  True when the portfolio state indicates that
                             existing positions should be rebalanced before
                             new risk is taken. False in the initial engine.

    Invariants:
        INV-RD-01  verdict is a RiskVerdict member (enforced by Python enum).
        INV-RD-02  messages is a tuple, never a list.
        INV-RD-03  frozen=True -- no field may be mutated after construction.
        INV-RD-04  max_position_size is None or a finite positive float.

    No validation is performed in __post_init__. RiskDecision is a pure
    value object; its correctness is the responsibility of the evaluation
    functions that construct it.
    """

    verdict:            RiskVerdict
    messages:           Tuple[str, ...]
    max_position_size:  Optional[float]
    requires_rebalance: bool


# =============================================================================
# SECTION 2 -- INTERNAL HELPERS (module-private)
# =============================================================================

def _compute_verdict(
    nav:                    float,
    peak_nav:               float,
    max_drawdown_hard_stop: float,
    max_drawdown_soft_warn: float,
) -> RiskVerdict:
    args = [nav, peak_nav, max_drawdown_hard_stop, max_drawdown_soft_warn]# type: ignore
    kwargs = {}# type: ignore
    return _mutmut_trampoline(x__compute_verdict__mutmut_orig, x__compute_verdict__mutmut_mutants, args, kwargs, None)


# =============================================================================
# SECTION 2 -- INTERNAL HELPERS (module-private)
# =============================================================================

def x__compute_verdict__mutmut_orig(
    nav:                    float,
    peak_nav:               float,
    max_drawdown_hard_stop: float,
    max_drawdown_soft_warn: float,
) -> RiskVerdict:
    """
    Derive a RiskVerdict from current NAV and drawdown thresholds.

    All arguments are assumed to have been validated by the domain layer
    prior to this call. No re-validation is performed here.

    Hard stop is evaluated before soft warn (most severe condition wins).

    Threshold derivation:
        hard_stop_nav = peak_nav * (1.0 - max_drawdown_hard_stop)
        soft_warn_nav = peak_nav * (1.0 - max_drawdown_soft_warn)

    Args:
        nav:                    Current portfolio net asset value. > 0.
        peak_nav:               High-water mark NAV. >= nav, > 0.
        max_drawdown_hard_stop: Hard stop fraction in (0, 1). > soft_warn.
        max_drawdown_soft_warn: Soft warn fraction in (0, 1). < hard_stop.

    Returns:
        RiskVerdict.HALT    if nav <= hard_stop_nav
        RiskVerdict.REDUCE  if nav <= soft_warn_nav
        RiskVerdict.APPROVE otherwise
    """
    hard_stop_nav: float = peak_nav * (1.0 - max_drawdown_hard_stop)
    soft_warn_nav: float = peak_nav * (1.0 - max_drawdown_soft_warn)

    if nav <= hard_stop_nav:
        return RiskVerdict.HALT
    if nav <= soft_warn_nav:
        return RiskVerdict.REDUCE
    return RiskVerdict.APPROVE


# =============================================================================
# SECTION 2 -- INTERNAL HELPERS (module-private)
# =============================================================================

def x__compute_verdict__mutmut_1(
    nav:                    float,
    peak_nav:               float,
    max_drawdown_hard_stop: float,
    max_drawdown_soft_warn: float,
) -> RiskVerdict:
    """
    Derive a RiskVerdict from current NAV and drawdown thresholds.

    All arguments are assumed to have been validated by the domain layer
    prior to this call. No re-validation is performed here.

    Hard stop is evaluated before soft warn (most severe condition wins).

    Threshold derivation:
        hard_stop_nav = peak_nav * (1.0 - max_drawdown_hard_stop)
        soft_warn_nav = peak_nav * (1.0 - max_drawdown_soft_warn)

    Args:
        nav:                    Current portfolio net asset value. > 0.
        peak_nav:               High-water mark NAV. >= nav, > 0.
        max_drawdown_hard_stop: Hard stop fraction in (0, 1). > soft_warn.
        max_drawdown_soft_warn: Soft warn fraction in (0, 1). < hard_stop.

    Returns:
        RiskVerdict.HALT    if nav <= hard_stop_nav
        RiskVerdict.REDUCE  if nav <= soft_warn_nav
        RiskVerdict.APPROVE otherwise
    """
    hard_stop_nav: float = None
    soft_warn_nav: float = peak_nav * (1.0 - max_drawdown_soft_warn)

    if nav <= hard_stop_nav:
        return RiskVerdict.HALT
    if nav <= soft_warn_nav:
        return RiskVerdict.REDUCE
    return RiskVerdict.APPROVE


# =============================================================================
# SECTION 2 -- INTERNAL HELPERS (module-private)
# =============================================================================

def x__compute_verdict__mutmut_2(
    nav:                    float,
    peak_nav:               float,
    max_drawdown_hard_stop: float,
    max_drawdown_soft_warn: float,
) -> RiskVerdict:
    """
    Derive a RiskVerdict from current NAV and drawdown thresholds.

    All arguments are assumed to have been validated by the domain layer
    prior to this call. No re-validation is performed here.

    Hard stop is evaluated before soft warn (most severe condition wins).

    Threshold derivation:
        hard_stop_nav = peak_nav * (1.0 - max_drawdown_hard_stop)
        soft_warn_nav = peak_nav * (1.0 - max_drawdown_soft_warn)

    Args:
        nav:                    Current portfolio net asset value. > 0.
        peak_nav:               High-water mark NAV. >= nav, > 0.
        max_drawdown_hard_stop: Hard stop fraction in (0, 1). > soft_warn.
        max_drawdown_soft_warn: Soft warn fraction in (0, 1). < hard_stop.

    Returns:
        RiskVerdict.HALT    if nav <= hard_stop_nav
        RiskVerdict.REDUCE  if nav <= soft_warn_nav
        RiskVerdict.APPROVE otherwise
    """
    hard_stop_nav: float = peak_nav / (1.0 - max_drawdown_hard_stop)
    soft_warn_nav: float = peak_nav * (1.0 - max_drawdown_soft_warn)

    if nav <= hard_stop_nav:
        return RiskVerdict.HALT
    if nav <= soft_warn_nav:
        return RiskVerdict.REDUCE
    return RiskVerdict.APPROVE


# =============================================================================
# SECTION 2 -- INTERNAL HELPERS (module-private)
# =============================================================================

def x__compute_verdict__mutmut_3(
    nav:                    float,
    peak_nav:               float,
    max_drawdown_hard_stop: float,
    max_drawdown_soft_warn: float,
) -> RiskVerdict:
    """
    Derive a RiskVerdict from current NAV and drawdown thresholds.

    All arguments are assumed to have been validated by the domain layer
    prior to this call. No re-validation is performed here.

    Hard stop is evaluated before soft warn (most severe condition wins).

    Threshold derivation:
        hard_stop_nav = peak_nav * (1.0 - max_drawdown_hard_stop)
        soft_warn_nav = peak_nav * (1.0 - max_drawdown_soft_warn)

    Args:
        nav:                    Current portfolio net asset value. > 0.
        peak_nav:               High-water mark NAV. >= nav, > 0.
        max_drawdown_hard_stop: Hard stop fraction in (0, 1). > soft_warn.
        max_drawdown_soft_warn: Soft warn fraction in (0, 1). < hard_stop.

    Returns:
        RiskVerdict.HALT    if nav <= hard_stop_nav
        RiskVerdict.REDUCE  if nav <= soft_warn_nav
        RiskVerdict.APPROVE otherwise
    """
    hard_stop_nav: float = peak_nav * (1.0 + max_drawdown_hard_stop)
    soft_warn_nav: float = peak_nav * (1.0 - max_drawdown_soft_warn)

    if nav <= hard_stop_nav:
        return RiskVerdict.HALT
    if nav <= soft_warn_nav:
        return RiskVerdict.REDUCE
    return RiskVerdict.APPROVE


# =============================================================================
# SECTION 2 -- INTERNAL HELPERS (module-private)
# =============================================================================

def x__compute_verdict__mutmut_4(
    nav:                    float,
    peak_nav:               float,
    max_drawdown_hard_stop: float,
    max_drawdown_soft_warn: float,
) -> RiskVerdict:
    """
    Derive a RiskVerdict from current NAV and drawdown thresholds.

    All arguments are assumed to have been validated by the domain layer
    prior to this call. No re-validation is performed here.

    Hard stop is evaluated before soft warn (most severe condition wins).

    Threshold derivation:
        hard_stop_nav = peak_nav * (1.0 - max_drawdown_hard_stop)
        soft_warn_nav = peak_nav * (1.0 - max_drawdown_soft_warn)

    Args:
        nav:                    Current portfolio net asset value. > 0.
        peak_nav:               High-water mark NAV. >= nav, > 0.
        max_drawdown_hard_stop: Hard stop fraction in (0, 1). > soft_warn.
        max_drawdown_soft_warn: Soft warn fraction in (0, 1). < hard_stop.

    Returns:
        RiskVerdict.HALT    if nav <= hard_stop_nav
        RiskVerdict.REDUCE  if nav <= soft_warn_nav
        RiskVerdict.APPROVE otherwise
    """
    hard_stop_nav: float = peak_nav * (2.0 - max_drawdown_hard_stop)
    soft_warn_nav: float = peak_nav * (1.0 - max_drawdown_soft_warn)

    if nav <= hard_stop_nav:
        return RiskVerdict.HALT
    if nav <= soft_warn_nav:
        return RiskVerdict.REDUCE
    return RiskVerdict.APPROVE


# =============================================================================
# SECTION 2 -- INTERNAL HELPERS (module-private)
# =============================================================================

def x__compute_verdict__mutmut_5(
    nav:                    float,
    peak_nav:               float,
    max_drawdown_hard_stop: float,
    max_drawdown_soft_warn: float,
) -> RiskVerdict:
    """
    Derive a RiskVerdict from current NAV and drawdown thresholds.

    All arguments are assumed to have been validated by the domain layer
    prior to this call. No re-validation is performed here.

    Hard stop is evaluated before soft warn (most severe condition wins).

    Threshold derivation:
        hard_stop_nav = peak_nav * (1.0 - max_drawdown_hard_stop)
        soft_warn_nav = peak_nav * (1.0 - max_drawdown_soft_warn)

    Args:
        nav:                    Current portfolio net asset value. > 0.
        peak_nav:               High-water mark NAV. >= nav, > 0.
        max_drawdown_hard_stop: Hard stop fraction in (0, 1). > soft_warn.
        max_drawdown_soft_warn: Soft warn fraction in (0, 1). < hard_stop.

    Returns:
        RiskVerdict.HALT    if nav <= hard_stop_nav
        RiskVerdict.REDUCE  if nav <= soft_warn_nav
        RiskVerdict.APPROVE otherwise
    """
    hard_stop_nav: float = peak_nav * (1.0 - max_drawdown_hard_stop)
    soft_warn_nav: float = None

    if nav <= hard_stop_nav:
        return RiskVerdict.HALT
    if nav <= soft_warn_nav:
        return RiskVerdict.REDUCE
    return RiskVerdict.APPROVE


# =============================================================================
# SECTION 2 -- INTERNAL HELPERS (module-private)
# =============================================================================

def x__compute_verdict__mutmut_6(
    nav:                    float,
    peak_nav:               float,
    max_drawdown_hard_stop: float,
    max_drawdown_soft_warn: float,
) -> RiskVerdict:
    """
    Derive a RiskVerdict from current NAV and drawdown thresholds.

    All arguments are assumed to have been validated by the domain layer
    prior to this call. No re-validation is performed here.

    Hard stop is evaluated before soft warn (most severe condition wins).

    Threshold derivation:
        hard_stop_nav = peak_nav * (1.0 - max_drawdown_hard_stop)
        soft_warn_nav = peak_nav * (1.0 - max_drawdown_soft_warn)

    Args:
        nav:                    Current portfolio net asset value. > 0.
        peak_nav:               High-water mark NAV. >= nav, > 0.
        max_drawdown_hard_stop: Hard stop fraction in (0, 1). > soft_warn.
        max_drawdown_soft_warn: Soft warn fraction in (0, 1). < hard_stop.

    Returns:
        RiskVerdict.HALT    if nav <= hard_stop_nav
        RiskVerdict.REDUCE  if nav <= soft_warn_nav
        RiskVerdict.APPROVE otherwise
    """
    hard_stop_nav: float = peak_nav * (1.0 - max_drawdown_hard_stop)
    soft_warn_nav: float = peak_nav / (1.0 - max_drawdown_soft_warn)

    if nav <= hard_stop_nav:
        return RiskVerdict.HALT
    if nav <= soft_warn_nav:
        return RiskVerdict.REDUCE
    return RiskVerdict.APPROVE


# =============================================================================
# SECTION 2 -- INTERNAL HELPERS (module-private)
# =============================================================================

def x__compute_verdict__mutmut_7(
    nav:                    float,
    peak_nav:               float,
    max_drawdown_hard_stop: float,
    max_drawdown_soft_warn: float,
) -> RiskVerdict:
    """
    Derive a RiskVerdict from current NAV and drawdown thresholds.

    All arguments are assumed to have been validated by the domain layer
    prior to this call. No re-validation is performed here.

    Hard stop is evaluated before soft warn (most severe condition wins).

    Threshold derivation:
        hard_stop_nav = peak_nav * (1.0 - max_drawdown_hard_stop)
        soft_warn_nav = peak_nav * (1.0 - max_drawdown_soft_warn)

    Args:
        nav:                    Current portfolio net asset value. > 0.
        peak_nav:               High-water mark NAV. >= nav, > 0.
        max_drawdown_hard_stop: Hard stop fraction in (0, 1). > soft_warn.
        max_drawdown_soft_warn: Soft warn fraction in (0, 1). < hard_stop.

    Returns:
        RiskVerdict.HALT    if nav <= hard_stop_nav
        RiskVerdict.REDUCE  if nav <= soft_warn_nav
        RiskVerdict.APPROVE otherwise
    """
    hard_stop_nav: float = peak_nav * (1.0 - max_drawdown_hard_stop)
    soft_warn_nav: float = peak_nav * (1.0 + max_drawdown_soft_warn)

    if nav <= hard_stop_nav:
        return RiskVerdict.HALT
    if nav <= soft_warn_nav:
        return RiskVerdict.REDUCE
    return RiskVerdict.APPROVE


# =============================================================================
# SECTION 2 -- INTERNAL HELPERS (module-private)
# =============================================================================

def x__compute_verdict__mutmut_8(
    nav:                    float,
    peak_nav:               float,
    max_drawdown_hard_stop: float,
    max_drawdown_soft_warn: float,
) -> RiskVerdict:
    """
    Derive a RiskVerdict from current NAV and drawdown thresholds.

    All arguments are assumed to have been validated by the domain layer
    prior to this call. No re-validation is performed here.

    Hard stop is evaluated before soft warn (most severe condition wins).

    Threshold derivation:
        hard_stop_nav = peak_nav * (1.0 - max_drawdown_hard_stop)
        soft_warn_nav = peak_nav * (1.0 - max_drawdown_soft_warn)

    Args:
        nav:                    Current portfolio net asset value. > 0.
        peak_nav:               High-water mark NAV. >= nav, > 0.
        max_drawdown_hard_stop: Hard stop fraction in (0, 1). > soft_warn.
        max_drawdown_soft_warn: Soft warn fraction in (0, 1). < hard_stop.

    Returns:
        RiskVerdict.HALT    if nav <= hard_stop_nav
        RiskVerdict.REDUCE  if nav <= soft_warn_nav
        RiskVerdict.APPROVE otherwise
    """
    hard_stop_nav: float = peak_nav * (1.0 - max_drawdown_hard_stop)
    soft_warn_nav: float = peak_nav * (2.0 - max_drawdown_soft_warn)

    if nav <= hard_stop_nav:
        return RiskVerdict.HALT
    if nav <= soft_warn_nav:
        return RiskVerdict.REDUCE
    return RiskVerdict.APPROVE


# =============================================================================
# SECTION 2 -- INTERNAL HELPERS (module-private)
# =============================================================================

def x__compute_verdict__mutmut_9(
    nav:                    float,
    peak_nav:               float,
    max_drawdown_hard_stop: float,
    max_drawdown_soft_warn: float,
) -> RiskVerdict:
    """
    Derive a RiskVerdict from current NAV and drawdown thresholds.

    All arguments are assumed to have been validated by the domain layer
    prior to this call. No re-validation is performed here.

    Hard stop is evaluated before soft warn (most severe condition wins).

    Threshold derivation:
        hard_stop_nav = peak_nav * (1.0 - max_drawdown_hard_stop)
        soft_warn_nav = peak_nav * (1.0 - max_drawdown_soft_warn)

    Args:
        nav:                    Current portfolio net asset value. > 0.
        peak_nav:               High-water mark NAV. >= nav, > 0.
        max_drawdown_hard_stop: Hard stop fraction in (0, 1). > soft_warn.
        max_drawdown_soft_warn: Soft warn fraction in (0, 1). < hard_stop.

    Returns:
        RiskVerdict.HALT    if nav <= hard_stop_nav
        RiskVerdict.REDUCE  if nav <= soft_warn_nav
        RiskVerdict.APPROVE otherwise
    """
    hard_stop_nav: float = peak_nav * (1.0 - max_drawdown_hard_stop)
    soft_warn_nav: float = peak_nav * (1.0 - max_drawdown_soft_warn)

    if nav < hard_stop_nav:
        return RiskVerdict.HALT
    if nav <= soft_warn_nav:
        return RiskVerdict.REDUCE
    return RiskVerdict.APPROVE


# =============================================================================
# SECTION 2 -- INTERNAL HELPERS (module-private)
# =============================================================================

def x__compute_verdict__mutmut_10(
    nav:                    float,
    peak_nav:               float,
    max_drawdown_hard_stop: float,
    max_drawdown_soft_warn: float,
) -> RiskVerdict:
    """
    Derive a RiskVerdict from current NAV and drawdown thresholds.

    All arguments are assumed to have been validated by the domain layer
    prior to this call. No re-validation is performed here.

    Hard stop is evaluated before soft warn (most severe condition wins).

    Threshold derivation:
        hard_stop_nav = peak_nav * (1.0 - max_drawdown_hard_stop)
        soft_warn_nav = peak_nav * (1.0 - max_drawdown_soft_warn)

    Args:
        nav:                    Current portfolio net asset value. > 0.
        peak_nav:               High-water mark NAV. >= nav, > 0.
        max_drawdown_hard_stop: Hard stop fraction in (0, 1). > soft_warn.
        max_drawdown_soft_warn: Soft warn fraction in (0, 1). < hard_stop.

    Returns:
        RiskVerdict.HALT    if nav <= hard_stop_nav
        RiskVerdict.REDUCE  if nav <= soft_warn_nav
        RiskVerdict.APPROVE otherwise
    """
    hard_stop_nav: float = peak_nav * (1.0 - max_drawdown_hard_stop)
    soft_warn_nav: float = peak_nav * (1.0 - max_drawdown_soft_warn)

    if nav <= hard_stop_nav:
        return RiskVerdict.HALT
    if nav < soft_warn_nav:
        return RiskVerdict.REDUCE
    return RiskVerdict.APPROVE

x__compute_verdict__mutmut_mutants : ClassVar[MutantDict] = { # type: ignore
'x__compute_verdict__mutmut_1': x__compute_verdict__mutmut_1, 
    'x__compute_verdict__mutmut_2': x__compute_verdict__mutmut_2, 
    'x__compute_verdict__mutmut_3': x__compute_verdict__mutmut_3, 
    'x__compute_verdict__mutmut_4': x__compute_verdict__mutmut_4, 
    'x__compute_verdict__mutmut_5': x__compute_verdict__mutmut_5, 
    'x__compute_verdict__mutmut_6': x__compute_verdict__mutmut_6, 
    'x__compute_verdict__mutmut_7': x__compute_verdict__mutmut_7, 
    'x__compute_verdict__mutmut_8': x__compute_verdict__mutmut_8, 
    'x__compute_verdict__mutmut_9': x__compute_verdict__mutmut_9, 
    'x__compute_verdict__mutmut_10': x__compute_verdict__mutmut_10
}
x__compute_verdict__mutmut_orig.__name__ = 'x__compute_verdict'


def _validate_asset_class(asset_class: str) -> None:
    args = [asset_class]# type: ignore
    kwargs = {}# type: ignore
    return _mutmut_trampoline(x__validate_asset_class__mutmut_orig, x__validate_asset_class__mutmut_mutants, args, kwargs, None)


def x__validate_asset_class__mutmut_orig(asset_class: str) -> None:
    """
    Raise RiskValidationError if asset_class is not in VALID_ASSET_CLASSES.

    This is a belt-and-suspenders check. PositionSpec.__post_init__ already
    enforces this; the check here guards against callers that construct
    PositionSpec via object.__setattr__ bypass or future refactoring.

    Args:
        asset_class: The asset_class string from a PositionSpec.

    Raises:
        RiskValidationError if asset_class is not a known asset class.
    """
    if asset_class not in VALID_ASSET_CLASSES:
        raise RiskValidationError(
            field_name="asset_class",
            value=asset_class,
            constraint=(
                "must be in VALID_ASSET_CLASSES: "
                + repr(sorted(VALID_ASSET_CLASSES))
            ),
        )


def x__validate_asset_class__mutmut_1(asset_class: str) -> None:
    """
    Raise RiskValidationError if asset_class is not in VALID_ASSET_CLASSES.

    This is a belt-and-suspenders check. PositionSpec.__post_init__ already
    enforces this; the check here guards against callers that construct
    PositionSpec via object.__setattr__ bypass or future refactoring.

    Args:
        asset_class: The asset_class string from a PositionSpec.

    Raises:
        RiskValidationError if asset_class is not a known asset class.
    """
    if asset_class in VALID_ASSET_CLASSES:
        raise RiskValidationError(
            field_name="asset_class",
            value=asset_class,
            constraint=(
                "must be in VALID_ASSET_CLASSES: "
                + repr(sorted(VALID_ASSET_CLASSES))
            ),
        )


def x__validate_asset_class__mutmut_2(asset_class: str) -> None:
    """
    Raise RiskValidationError if asset_class is not in VALID_ASSET_CLASSES.

    This is a belt-and-suspenders check. PositionSpec.__post_init__ already
    enforces this; the check here guards against callers that construct
    PositionSpec via object.__setattr__ bypass or future refactoring.

    Args:
        asset_class: The asset_class string from a PositionSpec.

    Raises:
        RiskValidationError if asset_class is not a known asset class.
    """
    if asset_class not in VALID_ASSET_CLASSES:
        raise RiskValidationError(
            field_name=None,
            value=asset_class,
            constraint=(
                "must be in VALID_ASSET_CLASSES: "
                + repr(sorted(VALID_ASSET_CLASSES))
            ),
        )


def x__validate_asset_class__mutmut_3(asset_class: str) -> None:
    """
    Raise RiskValidationError if asset_class is not in VALID_ASSET_CLASSES.

    This is a belt-and-suspenders check. PositionSpec.__post_init__ already
    enforces this; the check here guards against callers that construct
    PositionSpec via object.__setattr__ bypass or future refactoring.

    Args:
        asset_class: The asset_class string from a PositionSpec.

    Raises:
        RiskValidationError if asset_class is not a known asset class.
    """
    if asset_class not in VALID_ASSET_CLASSES:
        raise RiskValidationError(
            field_name="asset_class",
            value=None,
            constraint=(
                "must be in VALID_ASSET_CLASSES: "
                + repr(sorted(VALID_ASSET_CLASSES))
            ),
        )


def x__validate_asset_class__mutmut_4(asset_class: str) -> None:
    """
    Raise RiskValidationError if asset_class is not in VALID_ASSET_CLASSES.

    This is a belt-and-suspenders check. PositionSpec.__post_init__ already
    enforces this; the check here guards against callers that construct
    PositionSpec via object.__setattr__ bypass or future refactoring.

    Args:
        asset_class: The asset_class string from a PositionSpec.

    Raises:
        RiskValidationError if asset_class is not a known asset class.
    """
    if asset_class not in VALID_ASSET_CLASSES:
        raise RiskValidationError(
            field_name="asset_class",
            value=asset_class,
            constraint=None,
        )


def x__validate_asset_class__mutmut_5(asset_class: str) -> None:
    """
    Raise RiskValidationError if asset_class is not in VALID_ASSET_CLASSES.

    This is a belt-and-suspenders check. PositionSpec.__post_init__ already
    enforces this; the check here guards against callers that construct
    PositionSpec via object.__setattr__ bypass or future refactoring.

    Args:
        asset_class: The asset_class string from a PositionSpec.

    Raises:
        RiskValidationError if asset_class is not a known asset class.
    """
    if asset_class not in VALID_ASSET_CLASSES:
        raise RiskValidationError(
            value=asset_class,
            constraint=(
                "must be in VALID_ASSET_CLASSES: "
                + repr(sorted(VALID_ASSET_CLASSES))
            ),
        )


def x__validate_asset_class__mutmut_6(asset_class: str) -> None:
    """
    Raise RiskValidationError if asset_class is not in VALID_ASSET_CLASSES.

    This is a belt-and-suspenders check. PositionSpec.__post_init__ already
    enforces this; the check here guards against callers that construct
    PositionSpec via object.__setattr__ bypass or future refactoring.

    Args:
        asset_class: The asset_class string from a PositionSpec.

    Raises:
        RiskValidationError if asset_class is not a known asset class.
    """
    if asset_class not in VALID_ASSET_CLASSES:
        raise RiskValidationError(
            field_name="asset_class",
            constraint=(
                "must be in VALID_ASSET_CLASSES: "
                + repr(sorted(VALID_ASSET_CLASSES))
            ),
        )


def x__validate_asset_class__mutmut_7(asset_class: str) -> None:
    """
    Raise RiskValidationError if asset_class is not in VALID_ASSET_CLASSES.

    This is a belt-and-suspenders check. PositionSpec.__post_init__ already
    enforces this; the check here guards against callers that construct
    PositionSpec via object.__setattr__ bypass or future refactoring.

    Args:
        asset_class: The asset_class string from a PositionSpec.

    Raises:
        RiskValidationError if asset_class is not a known asset class.
    """
    if asset_class not in VALID_ASSET_CLASSES:
        raise RiskValidationError(
            field_name="asset_class",
            value=asset_class,
            )


def x__validate_asset_class__mutmut_8(asset_class: str) -> None:
    """
    Raise RiskValidationError if asset_class is not in VALID_ASSET_CLASSES.

    This is a belt-and-suspenders check. PositionSpec.__post_init__ already
    enforces this; the check here guards against callers that construct
    PositionSpec via object.__setattr__ bypass or future refactoring.

    Args:
        asset_class: The asset_class string from a PositionSpec.

    Raises:
        RiskValidationError if asset_class is not a known asset class.
    """
    if asset_class not in VALID_ASSET_CLASSES:
        raise RiskValidationError(
            field_name="XXasset_classXX",
            value=asset_class,
            constraint=(
                "must be in VALID_ASSET_CLASSES: "
                + repr(sorted(VALID_ASSET_CLASSES))
            ),
        )


def x__validate_asset_class__mutmut_9(asset_class: str) -> None:
    """
    Raise RiskValidationError if asset_class is not in VALID_ASSET_CLASSES.

    This is a belt-and-suspenders check. PositionSpec.__post_init__ already
    enforces this; the check here guards against callers that construct
    PositionSpec via object.__setattr__ bypass or future refactoring.

    Args:
        asset_class: The asset_class string from a PositionSpec.

    Raises:
        RiskValidationError if asset_class is not a known asset class.
    """
    if asset_class not in VALID_ASSET_CLASSES:
        raise RiskValidationError(
            field_name="ASSET_CLASS",
            value=asset_class,
            constraint=(
                "must be in VALID_ASSET_CLASSES: "
                + repr(sorted(VALID_ASSET_CLASSES))
            ),
        )


def x__validate_asset_class__mutmut_10(asset_class: str) -> None:
    """
    Raise RiskValidationError if asset_class is not in VALID_ASSET_CLASSES.

    This is a belt-and-suspenders check. PositionSpec.__post_init__ already
    enforces this; the check here guards against callers that construct
    PositionSpec via object.__setattr__ bypass or future refactoring.

    Args:
        asset_class: The asset_class string from a PositionSpec.

    Raises:
        RiskValidationError if asset_class is not a known asset class.
    """
    if asset_class not in VALID_ASSET_CLASSES:
        raise RiskValidationError(
            field_name="asset_class",
            value=asset_class,
            constraint=(
                "must be in VALID_ASSET_CLASSES: " - repr(sorted(VALID_ASSET_CLASSES))
            ),
        )


def x__validate_asset_class__mutmut_11(asset_class: str) -> None:
    """
    Raise RiskValidationError if asset_class is not in VALID_ASSET_CLASSES.

    This is a belt-and-suspenders check. PositionSpec.__post_init__ already
    enforces this; the check here guards against callers that construct
    PositionSpec via object.__setattr__ bypass or future refactoring.

    Args:
        asset_class: The asset_class string from a PositionSpec.

    Raises:
        RiskValidationError if asset_class is not a known asset class.
    """
    if asset_class not in VALID_ASSET_CLASSES:
        raise RiskValidationError(
            field_name="asset_class",
            value=asset_class,
            constraint=(
                "XXmust be in VALID_ASSET_CLASSES: XX"
                + repr(sorted(VALID_ASSET_CLASSES))
            ),
        )


def x__validate_asset_class__mutmut_12(asset_class: str) -> None:
    """
    Raise RiskValidationError if asset_class is not in VALID_ASSET_CLASSES.

    This is a belt-and-suspenders check. PositionSpec.__post_init__ already
    enforces this; the check here guards against callers that construct
    PositionSpec via object.__setattr__ bypass or future refactoring.

    Args:
        asset_class: The asset_class string from a PositionSpec.

    Raises:
        RiskValidationError if asset_class is not a known asset class.
    """
    if asset_class not in VALID_ASSET_CLASSES:
        raise RiskValidationError(
            field_name="asset_class",
            value=asset_class,
            constraint=(
                "must be in valid_asset_classes: "
                + repr(sorted(VALID_ASSET_CLASSES))
            ),
        )


def x__validate_asset_class__mutmut_13(asset_class: str) -> None:
    """
    Raise RiskValidationError if asset_class is not in VALID_ASSET_CLASSES.

    This is a belt-and-suspenders check. PositionSpec.__post_init__ already
    enforces this; the check here guards against callers that construct
    PositionSpec via object.__setattr__ bypass or future refactoring.

    Args:
        asset_class: The asset_class string from a PositionSpec.

    Raises:
        RiskValidationError if asset_class is not a known asset class.
    """
    if asset_class not in VALID_ASSET_CLASSES:
        raise RiskValidationError(
            field_name="asset_class",
            value=asset_class,
            constraint=(
                "MUST BE IN VALID_ASSET_CLASSES: "
                + repr(sorted(VALID_ASSET_CLASSES))
            ),
        )


def x__validate_asset_class__mutmut_14(asset_class: str) -> None:
    """
    Raise RiskValidationError if asset_class is not in VALID_ASSET_CLASSES.

    This is a belt-and-suspenders check. PositionSpec.__post_init__ already
    enforces this; the check here guards against callers that construct
    PositionSpec via object.__setattr__ bypass or future refactoring.

    Args:
        asset_class: The asset_class string from a PositionSpec.

    Raises:
        RiskValidationError if asset_class is not a known asset class.
    """
    if asset_class not in VALID_ASSET_CLASSES:
        raise RiskValidationError(
            field_name="asset_class",
            value=asset_class,
            constraint=(
                "must be in VALID_ASSET_CLASSES: "
                + repr(None)
            ),
        )


def x__validate_asset_class__mutmut_15(asset_class: str) -> None:
    """
    Raise RiskValidationError if asset_class is not in VALID_ASSET_CLASSES.

    This is a belt-and-suspenders check. PositionSpec.__post_init__ already
    enforces this; the check here guards against callers that construct
    PositionSpec via object.__setattr__ bypass or future refactoring.

    Args:
        asset_class: The asset_class string from a PositionSpec.

    Raises:
        RiskValidationError if asset_class is not a known asset class.
    """
    if asset_class not in VALID_ASSET_CLASSES:
        raise RiskValidationError(
            field_name="asset_class",
            value=asset_class,
            constraint=(
                "must be in VALID_ASSET_CLASSES: "
                + repr(sorted(None))
            ),
        )

x__validate_asset_class__mutmut_mutants : ClassVar[MutantDict] = { # type: ignore
'x__validate_asset_class__mutmut_1': x__validate_asset_class__mutmut_1, 
    'x__validate_asset_class__mutmut_2': x__validate_asset_class__mutmut_2, 
    'x__validate_asset_class__mutmut_3': x__validate_asset_class__mutmut_3, 
    'x__validate_asset_class__mutmut_4': x__validate_asset_class__mutmut_4, 
    'x__validate_asset_class__mutmut_5': x__validate_asset_class__mutmut_5, 
    'x__validate_asset_class__mutmut_6': x__validate_asset_class__mutmut_6, 
    'x__validate_asset_class__mutmut_7': x__validate_asset_class__mutmut_7, 
    'x__validate_asset_class__mutmut_8': x__validate_asset_class__mutmut_8, 
    'x__validate_asset_class__mutmut_9': x__validate_asset_class__mutmut_9, 
    'x__validate_asset_class__mutmut_10': x__validate_asset_class__mutmut_10, 
    'x__validate_asset_class__mutmut_11': x__validate_asset_class__mutmut_11, 
    'x__validate_asset_class__mutmut_12': x__validate_asset_class__mutmut_12, 
    'x__validate_asset_class__mutmut_13': x__validate_asset_class__mutmut_13, 
    'x__validate_asset_class__mutmut_14': x__validate_asset_class__mutmut_14, 
    'x__validate_asset_class__mutmut_15': x__validate_asset_class__mutmut_15
}
x__validate_asset_class__mutmut_orig.__name__ = 'x__validate_asset_class'


# =============================================================================
# SECTION 3 -- EVALUATE POSITION RISK
# =============================================================================

def evaluate_position_risk(
    position:  PositionSpec,
    portfolio: PortfolioState,
    params:    RiskParameters,
) -> RiskDecision:
    args = [position, portfolio, params]# type: ignore
    kwargs = {}# type: ignore
    return _mutmut_trampoline(x_evaluate_position_risk__mutmut_orig, x_evaluate_position_risk__mutmut_mutants, args, kwargs, None)


# =============================================================================
# SECTION 3 -- EVALUATE POSITION RISK
# =============================================================================

def x_evaluate_position_risk__mutmut_orig(
    position:  PositionSpec,
    portfolio: PortfolioState,
    params:    RiskParameters,
) -> RiskDecision:
    """
    Evaluate risk for a proposed position against the current portfolio state
    and risk parameter configuration.

    This is a pure function: it reads its three arguments and returns a
    RiskDecision. It does not mutate any input, access global state, perform
    I/O, or produce side effects.

    Evaluation order (fail-fast; first match wins for verdict):
        1. Asset class validation (raises RiskValidationError -- not a verdict).
        2. Hard stop check: if nav <= peak_nav * (1 - hard_stop) -> HALT.
        3. Soft warn check: if nav <= peak_nav * (1 - soft_warn) -> REDUCE.
        4. No breach: -> APPROVE.

    Note on asset class check:
        An invalid asset_class raises rather than returning a REJECT verdict
        because it indicates a programming error in the caller, not a market
        condition. A verdict implies the engine processed the request; an
        exception implies the request was malformed.

    Args:
        position:  The proposed position to evaluate. Must be a valid
                   PositionSpec (already validated by its constructor).
        portfolio: Current portfolio snapshot. Must be a valid PortfolioState.
        params:    Risk configuration. Must be a valid RiskParameters.

    Returns:
        RiskDecision with:
            verdict:            HALT | REDUCE | APPROVE
            messages:           () -- empty for Phase 7B; populated in 7C+.
            max_position_size:  None -- cap logic is Phase 7C+.
            requires_rebalance: False -- rebalance logic is Phase 7C+.

    Raises:
        RiskValidationError: if position.asset_class is not in VALID_ASSET_CLASSES.
    """
    # --- Step 1: Asset class validation ---
    # Raises RiskValidationError on unknown asset class.
    # Must be first: a malformed position should never reach verdict logic.
    _validate_asset_class(position.asset_class)

    # --- Steps 2-4: Drawdown verdict ---
    verdict: RiskVerdict = _compute_verdict(
        nav=portfolio.nav,
        peak_nav=portfolio.peak_nav,
        max_drawdown_hard_stop=params.max_drawdown_hard_stop,
        max_drawdown_soft_warn=params.max_drawdown_soft_warn,
    )

    return RiskDecision(
        verdict=verdict,
        messages=(),
        max_position_size=None,
        requires_rebalance=False,
    )


# =============================================================================
# SECTION 3 -- EVALUATE POSITION RISK
# =============================================================================

def x_evaluate_position_risk__mutmut_1(
    position:  PositionSpec,
    portfolio: PortfolioState,
    params:    RiskParameters,
) -> RiskDecision:
    """
    Evaluate risk for a proposed position against the current portfolio state
    and risk parameter configuration.

    This is a pure function: it reads its three arguments and returns a
    RiskDecision. It does not mutate any input, access global state, perform
    I/O, or produce side effects.

    Evaluation order (fail-fast; first match wins for verdict):
        1. Asset class validation (raises RiskValidationError -- not a verdict).
        2. Hard stop check: if nav <= peak_nav * (1 - hard_stop) -> HALT.
        3. Soft warn check: if nav <= peak_nav * (1 - soft_warn) -> REDUCE.
        4. No breach: -> APPROVE.

    Note on asset class check:
        An invalid asset_class raises rather than returning a REJECT verdict
        because it indicates a programming error in the caller, not a market
        condition. A verdict implies the engine processed the request; an
        exception implies the request was malformed.

    Args:
        position:  The proposed position to evaluate. Must be a valid
                   PositionSpec (already validated by its constructor).
        portfolio: Current portfolio snapshot. Must be a valid PortfolioState.
        params:    Risk configuration. Must be a valid RiskParameters.

    Returns:
        RiskDecision with:
            verdict:            HALT | REDUCE | APPROVE
            messages:           () -- empty for Phase 7B; populated in 7C+.
            max_position_size:  None -- cap logic is Phase 7C+.
            requires_rebalance: False -- rebalance logic is Phase 7C+.

    Raises:
        RiskValidationError: if position.asset_class is not in VALID_ASSET_CLASSES.
    """
    # --- Step 1: Asset class validation ---
    # Raises RiskValidationError on unknown asset class.
    # Must be first: a malformed position should never reach verdict logic.
    _validate_asset_class(None)

    # --- Steps 2-4: Drawdown verdict ---
    verdict: RiskVerdict = _compute_verdict(
        nav=portfolio.nav,
        peak_nav=portfolio.peak_nav,
        max_drawdown_hard_stop=params.max_drawdown_hard_stop,
        max_drawdown_soft_warn=params.max_drawdown_soft_warn,
    )

    return RiskDecision(
        verdict=verdict,
        messages=(),
        max_position_size=None,
        requires_rebalance=False,
    )


# =============================================================================
# SECTION 3 -- EVALUATE POSITION RISK
# =============================================================================

def x_evaluate_position_risk__mutmut_2(
    position:  PositionSpec,
    portfolio: PortfolioState,
    params:    RiskParameters,
) -> RiskDecision:
    """
    Evaluate risk for a proposed position against the current portfolio state
    and risk parameter configuration.

    This is a pure function: it reads its three arguments and returns a
    RiskDecision. It does not mutate any input, access global state, perform
    I/O, or produce side effects.

    Evaluation order (fail-fast; first match wins for verdict):
        1. Asset class validation (raises RiskValidationError -- not a verdict).
        2. Hard stop check: if nav <= peak_nav * (1 - hard_stop) -> HALT.
        3. Soft warn check: if nav <= peak_nav * (1 - soft_warn) -> REDUCE.
        4. No breach: -> APPROVE.

    Note on asset class check:
        An invalid asset_class raises rather than returning a REJECT verdict
        because it indicates a programming error in the caller, not a market
        condition. A verdict implies the engine processed the request; an
        exception implies the request was malformed.

    Args:
        position:  The proposed position to evaluate. Must be a valid
                   PositionSpec (already validated by its constructor).
        portfolio: Current portfolio snapshot. Must be a valid PortfolioState.
        params:    Risk configuration. Must be a valid RiskParameters.

    Returns:
        RiskDecision with:
            verdict:            HALT | REDUCE | APPROVE
            messages:           () -- empty for Phase 7B; populated in 7C+.
            max_position_size:  None -- cap logic is Phase 7C+.
            requires_rebalance: False -- rebalance logic is Phase 7C+.

    Raises:
        RiskValidationError: if position.asset_class is not in VALID_ASSET_CLASSES.
    """
    # --- Step 1: Asset class validation ---
    # Raises RiskValidationError on unknown asset class.
    # Must be first: a malformed position should never reach verdict logic.
    _validate_asset_class(position.asset_class)

    # --- Steps 2-4: Drawdown verdict ---
    verdict: RiskVerdict = None

    return RiskDecision(
        verdict=verdict,
        messages=(),
        max_position_size=None,
        requires_rebalance=False,
    )


# =============================================================================
# SECTION 3 -- EVALUATE POSITION RISK
# =============================================================================

def x_evaluate_position_risk__mutmut_3(
    position:  PositionSpec,
    portfolio: PortfolioState,
    params:    RiskParameters,
) -> RiskDecision:
    """
    Evaluate risk for a proposed position against the current portfolio state
    and risk parameter configuration.

    This is a pure function: it reads its three arguments and returns a
    RiskDecision. It does not mutate any input, access global state, perform
    I/O, or produce side effects.

    Evaluation order (fail-fast; first match wins for verdict):
        1. Asset class validation (raises RiskValidationError -- not a verdict).
        2. Hard stop check: if nav <= peak_nav * (1 - hard_stop) -> HALT.
        3. Soft warn check: if nav <= peak_nav * (1 - soft_warn) -> REDUCE.
        4. No breach: -> APPROVE.

    Note on asset class check:
        An invalid asset_class raises rather than returning a REJECT verdict
        because it indicates a programming error in the caller, not a market
        condition. A verdict implies the engine processed the request; an
        exception implies the request was malformed.

    Args:
        position:  The proposed position to evaluate. Must be a valid
                   PositionSpec (already validated by its constructor).
        portfolio: Current portfolio snapshot. Must be a valid PortfolioState.
        params:    Risk configuration. Must be a valid RiskParameters.

    Returns:
        RiskDecision with:
            verdict:            HALT | REDUCE | APPROVE
            messages:           () -- empty for Phase 7B; populated in 7C+.
            max_position_size:  None -- cap logic is Phase 7C+.
            requires_rebalance: False -- rebalance logic is Phase 7C+.

    Raises:
        RiskValidationError: if position.asset_class is not in VALID_ASSET_CLASSES.
    """
    # --- Step 1: Asset class validation ---
    # Raises RiskValidationError on unknown asset class.
    # Must be first: a malformed position should never reach verdict logic.
    _validate_asset_class(position.asset_class)

    # --- Steps 2-4: Drawdown verdict ---
    verdict: RiskVerdict = _compute_verdict(
        nav=None,
        peak_nav=portfolio.peak_nav,
        max_drawdown_hard_stop=params.max_drawdown_hard_stop,
        max_drawdown_soft_warn=params.max_drawdown_soft_warn,
    )

    return RiskDecision(
        verdict=verdict,
        messages=(),
        max_position_size=None,
        requires_rebalance=False,
    )


# =============================================================================
# SECTION 3 -- EVALUATE POSITION RISK
# =============================================================================

def x_evaluate_position_risk__mutmut_4(
    position:  PositionSpec,
    portfolio: PortfolioState,
    params:    RiskParameters,
) -> RiskDecision:
    """
    Evaluate risk for a proposed position against the current portfolio state
    and risk parameter configuration.

    This is a pure function: it reads its three arguments and returns a
    RiskDecision. It does not mutate any input, access global state, perform
    I/O, or produce side effects.

    Evaluation order (fail-fast; first match wins for verdict):
        1. Asset class validation (raises RiskValidationError -- not a verdict).
        2. Hard stop check: if nav <= peak_nav * (1 - hard_stop) -> HALT.
        3. Soft warn check: if nav <= peak_nav * (1 - soft_warn) -> REDUCE.
        4. No breach: -> APPROVE.

    Note on asset class check:
        An invalid asset_class raises rather than returning a REJECT verdict
        because it indicates a programming error in the caller, not a market
        condition. A verdict implies the engine processed the request; an
        exception implies the request was malformed.

    Args:
        position:  The proposed position to evaluate. Must be a valid
                   PositionSpec (already validated by its constructor).
        portfolio: Current portfolio snapshot. Must be a valid PortfolioState.
        params:    Risk configuration. Must be a valid RiskParameters.

    Returns:
        RiskDecision with:
            verdict:            HALT | REDUCE | APPROVE
            messages:           () -- empty for Phase 7B; populated in 7C+.
            max_position_size:  None -- cap logic is Phase 7C+.
            requires_rebalance: False -- rebalance logic is Phase 7C+.

    Raises:
        RiskValidationError: if position.asset_class is not in VALID_ASSET_CLASSES.
    """
    # --- Step 1: Asset class validation ---
    # Raises RiskValidationError on unknown asset class.
    # Must be first: a malformed position should never reach verdict logic.
    _validate_asset_class(position.asset_class)

    # --- Steps 2-4: Drawdown verdict ---
    verdict: RiskVerdict = _compute_verdict(
        nav=portfolio.nav,
        peak_nav=None,
        max_drawdown_hard_stop=params.max_drawdown_hard_stop,
        max_drawdown_soft_warn=params.max_drawdown_soft_warn,
    )

    return RiskDecision(
        verdict=verdict,
        messages=(),
        max_position_size=None,
        requires_rebalance=False,
    )


# =============================================================================
# SECTION 3 -- EVALUATE POSITION RISK
# =============================================================================

def x_evaluate_position_risk__mutmut_5(
    position:  PositionSpec,
    portfolio: PortfolioState,
    params:    RiskParameters,
) -> RiskDecision:
    """
    Evaluate risk for a proposed position against the current portfolio state
    and risk parameter configuration.

    This is a pure function: it reads its three arguments and returns a
    RiskDecision. It does not mutate any input, access global state, perform
    I/O, or produce side effects.

    Evaluation order (fail-fast; first match wins for verdict):
        1. Asset class validation (raises RiskValidationError -- not a verdict).
        2. Hard stop check: if nav <= peak_nav * (1 - hard_stop) -> HALT.
        3. Soft warn check: if nav <= peak_nav * (1 - soft_warn) -> REDUCE.
        4. No breach: -> APPROVE.

    Note on asset class check:
        An invalid asset_class raises rather than returning a REJECT verdict
        because it indicates a programming error in the caller, not a market
        condition. A verdict implies the engine processed the request; an
        exception implies the request was malformed.

    Args:
        position:  The proposed position to evaluate. Must be a valid
                   PositionSpec (already validated by its constructor).
        portfolio: Current portfolio snapshot. Must be a valid PortfolioState.
        params:    Risk configuration. Must be a valid RiskParameters.

    Returns:
        RiskDecision with:
            verdict:            HALT | REDUCE | APPROVE
            messages:           () -- empty for Phase 7B; populated in 7C+.
            max_position_size:  None -- cap logic is Phase 7C+.
            requires_rebalance: False -- rebalance logic is Phase 7C+.

    Raises:
        RiskValidationError: if position.asset_class is not in VALID_ASSET_CLASSES.
    """
    # --- Step 1: Asset class validation ---
    # Raises RiskValidationError on unknown asset class.
    # Must be first: a malformed position should never reach verdict logic.
    _validate_asset_class(position.asset_class)

    # --- Steps 2-4: Drawdown verdict ---
    verdict: RiskVerdict = _compute_verdict(
        nav=portfolio.nav,
        peak_nav=portfolio.peak_nav,
        max_drawdown_hard_stop=None,
        max_drawdown_soft_warn=params.max_drawdown_soft_warn,
    )

    return RiskDecision(
        verdict=verdict,
        messages=(),
        max_position_size=None,
        requires_rebalance=False,
    )


# =============================================================================
# SECTION 3 -- EVALUATE POSITION RISK
# =============================================================================

def x_evaluate_position_risk__mutmut_6(
    position:  PositionSpec,
    portfolio: PortfolioState,
    params:    RiskParameters,
) -> RiskDecision:
    """
    Evaluate risk for a proposed position against the current portfolio state
    and risk parameter configuration.

    This is a pure function: it reads its three arguments and returns a
    RiskDecision. It does not mutate any input, access global state, perform
    I/O, or produce side effects.

    Evaluation order (fail-fast; first match wins for verdict):
        1. Asset class validation (raises RiskValidationError -- not a verdict).
        2. Hard stop check: if nav <= peak_nav * (1 - hard_stop) -> HALT.
        3. Soft warn check: if nav <= peak_nav * (1 - soft_warn) -> REDUCE.
        4. No breach: -> APPROVE.

    Note on asset class check:
        An invalid asset_class raises rather than returning a REJECT verdict
        because it indicates a programming error in the caller, not a market
        condition. A verdict implies the engine processed the request; an
        exception implies the request was malformed.

    Args:
        position:  The proposed position to evaluate. Must be a valid
                   PositionSpec (already validated by its constructor).
        portfolio: Current portfolio snapshot. Must be a valid PortfolioState.
        params:    Risk configuration. Must be a valid RiskParameters.

    Returns:
        RiskDecision with:
            verdict:            HALT | REDUCE | APPROVE
            messages:           () -- empty for Phase 7B; populated in 7C+.
            max_position_size:  None -- cap logic is Phase 7C+.
            requires_rebalance: False -- rebalance logic is Phase 7C+.

    Raises:
        RiskValidationError: if position.asset_class is not in VALID_ASSET_CLASSES.
    """
    # --- Step 1: Asset class validation ---
    # Raises RiskValidationError on unknown asset class.
    # Must be first: a malformed position should never reach verdict logic.
    _validate_asset_class(position.asset_class)

    # --- Steps 2-4: Drawdown verdict ---
    verdict: RiskVerdict = _compute_verdict(
        nav=portfolio.nav,
        peak_nav=portfolio.peak_nav,
        max_drawdown_hard_stop=params.max_drawdown_hard_stop,
        max_drawdown_soft_warn=None,
    )

    return RiskDecision(
        verdict=verdict,
        messages=(),
        max_position_size=None,
        requires_rebalance=False,
    )


# =============================================================================
# SECTION 3 -- EVALUATE POSITION RISK
# =============================================================================

def x_evaluate_position_risk__mutmut_7(
    position:  PositionSpec,
    portfolio: PortfolioState,
    params:    RiskParameters,
) -> RiskDecision:
    """
    Evaluate risk for a proposed position against the current portfolio state
    and risk parameter configuration.

    This is a pure function: it reads its three arguments and returns a
    RiskDecision. It does not mutate any input, access global state, perform
    I/O, or produce side effects.

    Evaluation order (fail-fast; first match wins for verdict):
        1. Asset class validation (raises RiskValidationError -- not a verdict).
        2. Hard stop check: if nav <= peak_nav * (1 - hard_stop) -> HALT.
        3. Soft warn check: if nav <= peak_nav * (1 - soft_warn) -> REDUCE.
        4. No breach: -> APPROVE.

    Note on asset class check:
        An invalid asset_class raises rather than returning a REJECT verdict
        because it indicates a programming error in the caller, not a market
        condition. A verdict implies the engine processed the request; an
        exception implies the request was malformed.

    Args:
        position:  The proposed position to evaluate. Must be a valid
                   PositionSpec (already validated by its constructor).
        portfolio: Current portfolio snapshot. Must be a valid PortfolioState.
        params:    Risk configuration. Must be a valid RiskParameters.

    Returns:
        RiskDecision with:
            verdict:            HALT | REDUCE | APPROVE
            messages:           () -- empty for Phase 7B; populated in 7C+.
            max_position_size:  None -- cap logic is Phase 7C+.
            requires_rebalance: False -- rebalance logic is Phase 7C+.

    Raises:
        RiskValidationError: if position.asset_class is not in VALID_ASSET_CLASSES.
    """
    # --- Step 1: Asset class validation ---
    # Raises RiskValidationError on unknown asset class.
    # Must be first: a malformed position should never reach verdict logic.
    _validate_asset_class(position.asset_class)

    # --- Steps 2-4: Drawdown verdict ---
    verdict: RiskVerdict = _compute_verdict(
        peak_nav=portfolio.peak_nav,
        max_drawdown_hard_stop=params.max_drawdown_hard_stop,
        max_drawdown_soft_warn=params.max_drawdown_soft_warn,
    )

    return RiskDecision(
        verdict=verdict,
        messages=(),
        max_position_size=None,
        requires_rebalance=False,
    )


# =============================================================================
# SECTION 3 -- EVALUATE POSITION RISK
# =============================================================================

def x_evaluate_position_risk__mutmut_8(
    position:  PositionSpec,
    portfolio: PortfolioState,
    params:    RiskParameters,
) -> RiskDecision:
    """
    Evaluate risk for a proposed position against the current portfolio state
    and risk parameter configuration.

    This is a pure function: it reads its three arguments and returns a
    RiskDecision. It does not mutate any input, access global state, perform
    I/O, or produce side effects.

    Evaluation order (fail-fast; first match wins for verdict):
        1. Asset class validation (raises RiskValidationError -- not a verdict).
        2. Hard stop check: if nav <= peak_nav * (1 - hard_stop) -> HALT.
        3. Soft warn check: if nav <= peak_nav * (1 - soft_warn) -> REDUCE.
        4. No breach: -> APPROVE.

    Note on asset class check:
        An invalid asset_class raises rather than returning a REJECT verdict
        because it indicates a programming error in the caller, not a market
        condition. A verdict implies the engine processed the request; an
        exception implies the request was malformed.

    Args:
        position:  The proposed position to evaluate. Must be a valid
                   PositionSpec (already validated by its constructor).
        portfolio: Current portfolio snapshot. Must be a valid PortfolioState.
        params:    Risk configuration. Must be a valid RiskParameters.

    Returns:
        RiskDecision with:
            verdict:            HALT | REDUCE | APPROVE
            messages:           () -- empty for Phase 7B; populated in 7C+.
            max_position_size:  None -- cap logic is Phase 7C+.
            requires_rebalance: False -- rebalance logic is Phase 7C+.

    Raises:
        RiskValidationError: if position.asset_class is not in VALID_ASSET_CLASSES.
    """
    # --- Step 1: Asset class validation ---
    # Raises RiskValidationError on unknown asset class.
    # Must be first: a malformed position should never reach verdict logic.
    _validate_asset_class(position.asset_class)

    # --- Steps 2-4: Drawdown verdict ---
    verdict: RiskVerdict = _compute_verdict(
        nav=portfolio.nav,
        max_drawdown_hard_stop=params.max_drawdown_hard_stop,
        max_drawdown_soft_warn=params.max_drawdown_soft_warn,
    )

    return RiskDecision(
        verdict=verdict,
        messages=(),
        max_position_size=None,
        requires_rebalance=False,
    )


# =============================================================================
# SECTION 3 -- EVALUATE POSITION RISK
# =============================================================================

def x_evaluate_position_risk__mutmut_9(
    position:  PositionSpec,
    portfolio: PortfolioState,
    params:    RiskParameters,
) -> RiskDecision:
    """
    Evaluate risk for a proposed position against the current portfolio state
    and risk parameter configuration.

    This is a pure function: it reads its three arguments and returns a
    RiskDecision. It does not mutate any input, access global state, perform
    I/O, or produce side effects.

    Evaluation order (fail-fast; first match wins for verdict):
        1. Asset class validation (raises RiskValidationError -- not a verdict).
        2. Hard stop check: if nav <= peak_nav * (1 - hard_stop) -> HALT.
        3. Soft warn check: if nav <= peak_nav * (1 - soft_warn) -> REDUCE.
        4. No breach: -> APPROVE.

    Note on asset class check:
        An invalid asset_class raises rather than returning a REJECT verdict
        because it indicates a programming error in the caller, not a market
        condition. A verdict implies the engine processed the request; an
        exception implies the request was malformed.

    Args:
        position:  The proposed position to evaluate. Must be a valid
                   PositionSpec (already validated by its constructor).
        portfolio: Current portfolio snapshot. Must be a valid PortfolioState.
        params:    Risk configuration. Must be a valid RiskParameters.

    Returns:
        RiskDecision with:
            verdict:            HALT | REDUCE | APPROVE
            messages:           () -- empty for Phase 7B; populated in 7C+.
            max_position_size:  None -- cap logic is Phase 7C+.
            requires_rebalance: False -- rebalance logic is Phase 7C+.

    Raises:
        RiskValidationError: if position.asset_class is not in VALID_ASSET_CLASSES.
    """
    # --- Step 1: Asset class validation ---
    # Raises RiskValidationError on unknown asset class.
    # Must be first: a malformed position should never reach verdict logic.
    _validate_asset_class(position.asset_class)

    # --- Steps 2-4: Drawdown verdict ---
    verdict: RiskVerdict = _compute_verdict(
        nav=portfolio.nav,
        peak_nav=portfolio.peak_nav,
        max_drawdown_soft_warn=params.max_drawdown_soft_warn,
    )

    return RiskDecision(
        verdict=verdict,
        messages=(),
        max_position_size=None,
        requires_rebalance=False,
    )


# =============================================================================
# SECTION 3 -- EVALUATE POSITION RISK
# =============================================================================

def x_evaluate_position_risk__mutmut_10(
    position:  PositionSpec,
    portfolio: PortfolioState,
    params:    RiskParameters,
) -> RiskDecision:
    """
    Evaluate risk for a proposed position against the current portfolio state
    and risk parameter configuration.

    This is a pure function: it reads its three arguments and returns a
    RiskDecision. It does not mutate any input, access global state, perform
    I/O, or produce side effects.

    Evaluation order (fail-fast; first match wins for verdict):
        1. Asset class validation (raises RiskValidationError -- not a verdict).
        2. Hard stop check: if nav <= peak_nav * (1 - hard_stop) -> HALT.
        3. Soft warn check: if nav <= peak_nav * (1 - soft_warn) -> REDUCE.
        4. No breach: -> APPROVE.

    Note on asset class check:
        An invalid asset_class raises rather than returning a REJECT verdict
        because it indicates a programming error in the caller, not a market
        condition. A verdict implies the engine processed the request; an
        exception implies the request was malformed.

    Args:
        position:  The proposed position to evaluate. Must be a valid
                   PositionSpec (already validated by its constructor).
        portfolio: Current portfolio snapshot. Must be a valid PortfolioState.
        params:    Risk configuration. Must be a valid RiskParameters.

    Returns:
        RiskDecision with:
            verdict:            HALT | REDUCE | APPROVE
            messages:           () -- empty for Phase 7B; populated in 7C+.
            max_position_size:  None -- cap logic is Phase 7C+.
            requires_rebalance: False -- rebalance logic is Phase 7C+.

    Raises:
        RiskValidationError: if position.asset_class is not in VALID_ASSET_CLASSES.
    """
    # --- Step 1: Asset class validation ---
    # Raises RiskValidationError on unknown asset class.
    # Must be first: a malformed position should never reach verdict logic.
    _validate_asset_class(position.asset_class)

    # --- Steps 2-4: Drawdown verdict ---
    verdict: RiskVerdict = _compute_verdict(
        nav=portfolio.nav,
        peak_nav=portfolio.peak_nav,
        max_drawdown_hard_stop=params.max_drawdown_hard_stop,
        )

    return RiskDecision(
        verdict=verdict,
        messages=(),
        max_position_size=None,
        requires_rebalance=False,
    )


# =============================================================================
# SECTION 3 -- EVALUATE POSITION RISK
# =============================================================================

def x_evaluate_position_risk__mutmut_11(
    position:  PositionSpec,
    portfolio: PortfolioState,
    params:    RiskParameters,
) -> RiskDecision:
    """
    Evaluate risk for a proposed position against the current portfolio state
    and risk parameter configuration.

    This is a pure function: it reads its three arguments and returns a
    RiskDecision. It does not mutate any input, access global state, perform
    I/O, or produce side effects.

    Evaluation order (fail-fast; first match wins for verdict):
        1. Asset class validation (raises RiskValidationError -- not a verdict).
        2. Hard stop check: if nav <= peak_nav * (1 - hard_stop) -> HALT.
        3. Soft warn check: if nav <= peak_nav * (1 - soft_warn) -> REDUCE.
        4. No breach: -> APPROVE.

    Note on asset class check:
        An invalid asset_class raises rather than returning a REJECT verdict
        because it indicates a programming error in the caller, not a market
        condition. A verdict implies the engine processed the request; an
        exception implies the request was malformed.

    Args:
        position:  The proposed position to evaluate. Must be a valid
                   PositionSpec (already validated by its constructor).
        portfolio: Current portfolio snapshot. Must be a valid PortfolioState.
        params:    Risk configuration. Must be a valid RiskParameters.

    Returns:
        RiskDecision with:
            verdict:            HALT | REDUCE | APPROVE
            messages:           () -- empty for Phase 7B; populated in 7C+.
            max_position_size:  None -- cap logic is Phase 7C+.
            requires_rebalance: False -- rebalance logic is Phase 7C+.

    Raises:
        RiskValidationError: if position.asset_class is not in VALID_ASSET_CLASSES.
    """
    # --- Step 1: Asset class validation ---
    # Raises RiskValidationError on unknown asset class.
    # Must be first: a malformed position should never reach verdict logic.
    _validate_asset_class(position.asset_class)

    # --- Steps 2-4: Drawdown verdict ---
    verdict: RiskVerdict = _compute_verdict(
        nav=portfolio.nav,
        peak_nav=portfolio.peak_nav,
        max_drawdown_hard_stop=params.max_drawdown_hard_stop,
        max_drawdown_soft_warn=params.max_drawdown_soft_warn,
    )

    return RiskDecision(
        verdict=None,
        messages=(),
        max_position_size=None,
        requires_rebalance=False,
    )


# =============================================================================
# SECTION 3 -- EVALUATE POSITION RISK
# =============================================================================

def x_evaluate_position_risk__mutmut_12(
    position:  PositionSpec,
    portfolio: PortfolioState,
    params:    RiskParameters,
) -> RiskDecision:
    """
    Evaluate risk for a proposed position against the current portfolio state
    and risk parameter configuration.

    This is a pure function: it reads its three arguments and returns a
    RiskDecision. It does not mutate any input, access global state, perform
    I/O, or produce side effects.

    Evaluation order (fail-fast; first match wins for verdict):
        1. Asset class validation (raises RiskValidationError -- not a verdict).
        2. Hard stop check: if nav <= peak_nav * (1 - hard_stop) -> HALT.
        3. Soft warn check: if nav <= peak_nav * (1 - soft_warn) -> REDUCE.
        4. No breach: -> APPROVE.

    Note on asset class check:
        An invalid asset_class raises rather than returning a REJECT verdict
        because it indicates a programming error in the caller, not a market
        condition. A verdict implies the engine processed the request; an
        exception implies the request was malformed.

    Args:
        position:  The proposed position to evaluate. Must be a valid
                   PositionSpec (already validated by its constructor).
        portfolio: Current portfolio snapshot. Must be a valid PortfolioState.
        params:    Risk configuration. Must be a valid RiskParameters.

    Returns:
        RiskDecision with:
            verdict:            HALT | REDUCE | APPROVE
            messages:           () -- empty for Phase 7B; populated in 7C+.
            max_position_size:  None -- cap logic is Phase 7C+.
            requires_rebalance: False -- rebalance logic is Phase 7C+.

    Raises:
        RiskValidationError: if position.asset_class is not in VALID_ASSET_CLASSES.
    """
    # --- Step 1: Asset class validation ---
    # Raises RiskValidationError on unknown asset class.
    # Must be first: a malformed position should never reach verdict logic.
    _validate_asset_class(position.asset_class)

    # --- Steps 2-4: Drawdown verdict ---
    verdict: RiskVerdict = _compute_verdict(
        nav=portfolio.nav,
        peak_nav=portfolio.peak_nav,
        max_drawdown_hard_stop=params.max_drawdown_hard_stop,
        max_drawdown_soft_warn=params.max_drawdown_soft_warn,
    )

    return RiskDecision(
        verdict=verdict,
        messages=None,
        max_position_size=None,
        requires_rebalance=False,
    )


# =============================================================================
# SECTION 3 -- EVALUATE POSITION RISK
# =============================================================================

def x_evaluate_position_risk__mutmut_13(
    position:  PositionSpec,
    portfolio: PortfolioState,
    params:    RiskParameters,
) -> RiskDecision:
    """
    Evaluate risk for a proposed position against the current portfolio state
    and risk parameter configuration.

    This is a pure function: it reads its three arguments and returns a
    RiskDecision. It does not mutate any input, access global state, perform
    I/O, or produce side effects.

    Evaluation order (fail-fast; first match wins for verdict):
        1. Asset class validation (raises RiskValidationError -- not a verdict).
        2. Hard stop check: if nav <= peak_nav * (1 - hard_stop) -> HALT.
        3. Soft warn check: if nav <= peak_nav * (1 - soft_warn) -> REDUCE.
        4. No breach: -> APPROVE.

    Note on asset class check:
        An invalid asset_class raises rather than returning a REJECT verdict
        because it indicates a programming error in the caller, not a market
        condition. A verdict implies the engine processed the request; an
        exception implies the request was malformed.

    Args:
        position:  The proposed position to evaluate. Must be a valid
                   PositionSpec (already validated by its constructor).
        portfolio: Current portfolio snapshot. Must be a valid PortfolioState.
        params:    Risk configuration. Must be a valid RiskParameters.

    Returns:
        RiskDecision with:
            verdict:            HALT | REDUCE | APPROVE
            messages:           () -- empty for Phase 7B; populated in 7C+.
            max_position_size:  None -- cap logic is Phase 7C+.
            requires_rebalance: False -- rebalance logic is Phase 7C+.

    Raises:
        RiskValidationError: if position.asset_class is not in VALID_ASSET_CLASSES.
    """
    # --- Step 1: Asset class validation ---
    # Raises RiskValidationError on unknown asset class.
    # Must be first: a malformed position should never reach verdict logic.
    _validate_asset_class(position.asset_class)

    # --- Steps 2-4: Drawdown verdict ---
    verdict: RiskVerdict = _compute_verdict(
        nav=portfolio.nav,
        peak_nav=portfolio.peak_nav,
        max_drawdown_hard_stop=params.max_drawdown_hard_stop,
        max_drawdown_soft_warn=params.max_drawdown_soft_warn,
    )

    return RiskDecision(
        verdict=verdict,
        messages=(),
        max_position_size=None,
        requires_rebalance=None,
    )


# =============================================================================
# SECTION 3 -- EVALUATE POSITION RISK
# =============================================================================

def x_evaluate_position_risk__mutmut_14(
    position:  PositionSpec,
    portfolio: PortfolioState,
    params:    RiskParameters,
) -> RiskDecision:
    """
    Evaluate risk for a proposed position against the current portfolio state
    and risk parameter configuration.

    This is a pure function: it reads its three arguments and returns a
    RiskDecision. It does not mutate any input, access global state, perform
    I/O, or produce side effects.

    Evaluation order (fail-fast; first match wins for verdict):
        1. Asset class validation (raises RiskValidationError -- not a verdict).
        2. Hard stop check: if nav <= peak_nav * (1 - hard_stop) -> HALT.
        3. Soft warn check: if nav <= peak_nav * (1 - soft_warn) -> REDUCE.
        4. No breach: -> APPROVE.

    Note on asset class check:
        An invalid asset_class raises rather than returning a REJECT verdict
        because it indicates a programming error in the caller, not a market
        condition. A verdict implies the engine processed the request; an
        exception implies the request was malformed.

    Args:
        position:  The proposed position to evaluate. Must be a valid
                   PositionSpec (already validated by its constructor).
        portfolio: Current portfolio snapshot. Must be a valid PortfolioState.
        params:    Risk configuration. Must be a valid RiskParameters.

    Returns:
        RiskDecision with:
            verdict:            HALT | REDUCE | APPROVE
            messages:           () -- empty for Phase 7B; populated in 7C+.
            max_position_size:  None -- cap logic is Phase 7C+.
            requires_rebalance: False -- rebalance logic is Phase 7C+.

    Raises:
        RiskValidationError: if position.asset_class is not in VALID_ASSET_CLASSES.
    """
    # --- Step 1: Asset class validation ---
    # Raises RiskValidationError on unknown asset class.
    # Must be first: a malformed position should never reach verdict logic.
    _validate_asset_class(position.asset_class)

    # --- Steps 2-4: Drawdown verdict ---
    verdict: RiskVerdict = _compute_verdict(
        nav=portfolio.nav,
        peak_nav=portfolio.peak_nav,
        max_drawdown_hard_stop=params.max_drawdown_hard_stop,
        max_drawdown_soft_warn=params.max_drawdown_soft_warn,
    )

    return RiskDecision(
        messages=(),
        max_position_size=None,
        requires_rebalance=False,
    )


# =============================================================================
# SECTION 3 -- EVALUATE POSITION RISK
# =============================================================================

def x_evaluate_position_risk__mutmut_15(
    position:  PositionSpec,
    portfolio: PortfolioState,
    params:    RiskParameters,
) -> RiskDecision:
    """
    Evaluate risk for a proposed position against the current portfolio state
    and risk parameter configuration.

    This is a pure function: it reads its three arguments and returns a
    RiskDecision. It does not mutate any input, access global state, perform
    I/O, or produce side effects.

    Evaluation order (fail-fast; first match wins for verdict):
        1. Asset class validation (raises RiskValidationError -- not a verdict).
        2. Hard stop check: if nav <= peak_nav * (1 - hard_stop) -> HALT.
        3. Soft warn check: if nav <= peak_nav * (1 - soft_warn) -> REDUCE.
        4. No breach: -> APPROVE.

    Note on asset class check:
        An invalid asset_class raises rather than returning a REJECT verdict
        because it indicates a programming error in the caller, not a market
        condition. A verdict implies the engine processed the request; an
        exception implies the request was malformed.

    Args:
        position:  The proposed position to evaluate. Must be a valid
                   PositionSpec (already validated by its constructor).
        portfolio: Current portfolio snapshot. Must be a valid PortfolioState.
        params:    Risk configuration. Must be a valid RiskParameters.

    Returns:
        RiskDecision with:
            verdict:            HALT | REDUCE | APPROVE
            messages:           () -- empty for Phase 7B; populated in 7C+.
            max_position_size:  None -- cap logic is Phase 7C+.
            requires_rebalance: False -- rebalance logic is Phase 7C+.

    Raises:
        RiskValidationError: if position.asset_class is not in VALID_ASSET_CLASSES.
    """
    # --- Step 1: Asset class validation ---
    # Raises RiskValidationError on unknown asset class.
    # Must be first: a malformed position should never reach verdict logic.
    _validate_asset_class(position.asset_class)

    # --- Steps 2-4: Drawdown verdict ---
    verdict: RiskVerdict = _compute_verdict(
        nav=portfolio.nav,
        peak_nav=portfolio.peak_nav,
        max_drawdown_hard_stop=params.max_drawdown_hard_stop,
        max_drawdown_soft_warn=params.max_drawdown_soft_warn,
    )

    return RiskDecision(
        verdict=verdict,
        max_position_size=None,
        requires_rebalance=False,
    )


# =============================================================================
# SECTION 3 -- EVALUATE POSITION RISK
# =============================================================================

def x_evaluate_position_risk__mutmut_16(
    position:  PositionSpec,
    portfolio: PortfolioState,
    params:    RiskParameters,
) -> RiskDecision:
    """
    Evaluate risk for a proposed position against the current portfolio state
    and risk parameter configuration.

    This is a pure function: it reads its three arguments and returns a
    RiskDecision. It does not mutate any input, access global state, perform
    I/O, or produce side effects.

    Evaluation order (fail-fast; first match wins for verdict):
        1. Asset class validation (raises RiskValidationError -- not a verdict).
        2. Hard stop check: if nav <= peak_nav * (1 - hard_stop) -> HALT.
        3. Soft warn check: if nav <= peak_nav * (1 - soft_warn) -> REDUCE.
        4. No breach: -> APPROVE.

    Note on asset class check:
        An invalid asset_class raises rather than returning a REJECT verdict
        because it indicates a programming error in the caller, not a market
        condition. A verdict implies the engine processed the request; an
        exception implies the request was malformed.

    Args:
        position:  The proposed position to evaluate. Must be a valid
                   PositionSpec (already validated by its constructor).
        portfolio: Current portfolio snapshot. Must be a valid PortfolioState.
        params:    Risk configuration. Must be a valid RiskParameters.

    Returns:
        RiskDecision with:
            verdict:            HALT | REDUCE | APPROVE
            messages:           () -- empty for Phase 7B; populated in 7C+.
            max_position_size:  None -- cap logic is Phase 7C+.
            requires_rebalance: False -- rebalance logic is Phase 7C+.

    Raises:
        RiskValidationError: if position.asset_class is not in VALID_ASSET_CLASSES.
    """
    # --- Step 1: Asset class validation ---
    # Raises RiskValidationError on unknown asset class.
    # Must be first: a malformed position should never reach verdict logic.
    _validate_asset_class(position.asset_class)

    # --- Steps 2-4: Drawdown verdict ---
    verdict: RiskVerdict = _compute_verdict(
        nav=portfolio.nav,
        peak_nav=portfolio.peak_nav,
        max_drawdown_hard_stop=params.max_drawdown_hard_stop,
        max_drawdown_soft_warn=params.max_drawdown_soft_warn,
    )

    return RiskDecision(
        verdict=verdict,
        messages=(),
        requires_rebalance=False,
    )


# =============================================================================
# SECTION 3 -- EVALUATE POSITION RISK
# =============================================================================

def x_evaluate_position_risk__mutmut_17(
    position:  PositionSpec,
    portfolio: PortfolioState,
    params:    RiskParameters,
) -> RiskDecision:
    """
    Evaluate risk for a proposed position against the current portfolio state
    and risk parameter configuration.

    This is a pure function: it reads its three arguments and returns a
    RiskDecision. It does not mutate any input, access global state, perform
    I/O, or produce side effects.

    Evaluation order (fail-fast; first match wins for verdict):
        1. Asset class validation (raises RiskValidationError -- not a verdict).
        2. Hard stop check: if nav <= peak_nav * (1 - hard_stop) -> HALT.
        3. Soft warn check: if nav <= peak_nav * (1 - soft_warn) -> REDUCE.
        4. No breach: -> APPROVE.

    Note on asset class check:
        An invalid asset_class raises rather than returning a REJECT verdict
        because it indicates a programming error in the caller, not a market
        condition. A verdict implies the engine processed the request; an
        exception implies the request was malformed.

    Args:
        position:  The proposed position to evaluate. Must be a valid
                   PositionSpec (already validated by its constructor).
        portfolio: Current portfolio snapshot. Must be a valid PortfolioState.
        params:    Risk configuration. Must be a valid RiskParameters.

    Returns:
        RiskDecision with:
            verdict:            HALT | REDUCE | APPROVE
            messages:           () -- empty for Phase 7B; populated in 7C+.
            max_position_size:  None -- cap logic is Phase 7C+.
            requires_rebalance: False -- rebalance logic is Phase 7C+.

    Raises:
        RiskValidationError: if position.asset_class is not in VALID_ASSET_CLASSES.
    """
    # --- Step 1: Asset class validation ---
    # Raises RiskValidationError on unknown asset class.
    # Must be first: a malformed position should never reach verdict logic.
    _validate_asset_class(position.asset_class)

    # --- Steps 2-4: Drawdown verdict ---
    verdict: RiskVerdict = _compute_verdict(
        nav=portfolio.nav,
        peak_nav=portfolio.peak_nav,
        max_drawdown_hard_stop=params.max_drawdown_hard_stop,
        max_drawdown_soft_warn=params.max_drawdown_soft_warn,
    )

    return RiskDecision(
        verdict=verdict,
        messages=(),
        max_position_size=None,
        )


# =============================================================================
# SECTION 3 -- EVALUATE POSITION RISK
# =============================================================================

def x_evaluate_position_risk__mutmut_18(
    position:  PositionSpec,
    portfolio: PortfolioState,
    params:    RiskParameters,
) -> RiskDecision:
    """
    Evaluate risk for a proposed position against the current portfolio state
    and risk parameter configuration.

    This is a pure function: it reads its three arguments and returns a
    RiskDecision. It does not mutate any input, access global state, perform
    I/O, or produce side effects.

    Evaluation order (fail-fast; first match wins for verdict):
        1. Asset class validation (raises RiskValidationError -- not a verdict).
        2. Hard stop check: if nav <= peak_nav * (1 - hard_stop) -> HALT.
        3. Soft warn check: if nav <= peak_nav * (1 - soft_warn) -> REDUCE.
        4. No breach: -> APPROVE.

    Note on asset class check:
        An invalid asset_class raises rather than returning a REJECT verdict
        because it indicates a programming error in the caller, not a market
        condition. A verdict implies the engine processed the request; an
        exception implies the request was malformed.

    Args:
        position:  The proposed position to evaluate. Must be a valid
                   PositionSpec (already validated by its constructor).
        portfolio: Current portfolio snapshot. Must be a valid PortfolioState.
        params:    Risk configuration. Must be a valid RiskParameters.

    Returns:
        RiskDecision with:
            verdict:            HALT | REDUCE | APPROVE
            messages:           () -- empty for Phase 7B; populated in 7C+.
            max_position_size:  None -- cap logic is Phase 7C+.
            requires_rebalance: False -- rebalance logic is Phase 7C+.

    Raises:
        RiskValidationError: if position.asset_class is not in VALID_ASSET_CLASSES.
    """
    # --- Step 1: Asset class validation ---
    # Raises RiskValidationError on unknown asset class.
    # Must be first: a malformed position should never reach verdict logic.
    _validate_asset_class(position.asset_class)

    # --- Steps 2-4: Drawdown verdict ---
    verdict: RiskVerdict = _compute_verdict(
        nav=portfolio.nav,
        peak_nav=portfolio.peak_nav,
        max_drawdown_hard_stop=params.max_drawdown_hard_stop,
        max_drawdown_soft_warn=params.max_drawdown_soft_warn,
    )

    return RiskDecision(
        verdict=verdict,
        messages=(),
        max_position_size=None,
        requires_rebalance=True,
    )

x_evaluate_position_risk__mutmut_mutants : ClassVar[MutantDict] = { # type: ignore
'x_evaluate_position_risk__mutmut_1': x_evaluate_position_risk__mutmut_1, 
    'x_evaluate_position_risk__mutmut_2': x_evaluate_position_risk__mutmut_2, 
    'x_evaluate_position_risk__mutmut_3': x_evaluate_position_risk__mutmut_3, 
    'x_evaluate_position_risk__mutmut_4': x_evaluate_position_risk__mutmut_4, 
    'x_evaluate_position_risk__mutmut_5': x_evaluate_position_risk__mutmut_5, 
    'x_evaluate_position_risk__mutmut_6': x_evaluate_position_risk__mutmut_6, 
    'x_evaluate_position_risk__mutmut_7': x_evaluate_position_risk__mutmut_7, 
    'x_evaluate_position_risk__mutmut_8': x_evaluate_position_risk__mutmut_8, 
    'x_evaluate_position_risk__mutmut_9': x_evaluate_position_risk__mutmut_9, 
    'x_evaluate_position_risk__mutmut_10': x_evaluate_position_risk__mutmut_10, 
    'x_evaluate_position_risk__mutmut_11': x_evaluate_position_risk__mutmut_11, 
    'x_evaluate_position_risk__mutmut_12': x_evaluate_position_risk__mutmut_12, 
    'x_evaluate_position_risk__mutmut_13': x_evaluate_position_risk__mutmut_13, 
    'x_evaluate_position_risk__mutmut_14': x_evaluate_position_risk__mutmut_14, 
    'x_evaluate_position_risk__mutmut_15': x_evaluate_position_risk__mutmut_15, 
    'x_evaluate_position_risk__mutmut_16': x_evaluate_position_risk__mutmut_16, 
    'x_evaluate_position_risk__mutmut_17': x_evaluate_position_risk__mutmut_17, 
    'x_evaluate_position_risk__mutmut_18': x_evaluate_position_risk__mutmut_18
}
x_evaluate_position_risk__mutmut_orig.__name__ = 'x_evaluate_position_risk'


# =============================================================================
# SECTION 4 -- EVALUATE PORTFOLIO RISK
# =============================================================================

def evaluate_portfolio_risk(
    portfolio: PortfolioState,
    params:    RiskParameters,
) -> RiskDecision:
    args = [portfolio, params]# type: ignore
    kwargs = {}# type: ignore
    return _mutmut_trampoline(x_evaluate_portfolio_risk__mutmut_orig, x_evaluate_portfolio_risk__mutmut_mutants, args, kwargs, None)


# =============================================================================
# SECTION 4 -- EVALUATE PORTFOLIO RISK
# =============================================================================

def x_evaluate_portfolio_risk__mutmut_orig(
    portfolio: PortfolioState,
    params:    RiskParameters,
) -> RiskDecision:
    """
    Evaluate risk at the portfolio level, without reference to any specific
    proposed position.

    Used to determine the overall health of the portfolio before any position
    evaluation is attempted. Callers may check the portfolio verdict first
    and skip evaluate_position_risk entirely when verdict is HALT.

    This is a pure function with the same determinism and no-side-effect
    guarantees as evaluate_position_risk.

    Evaluation order:
        1. Hard stop check: if nav <= peak_nav * (1 - hard_stop) -> HALT.
        2. Soft warn check: if nav <= peak_nav * (1 - soft_warn) -> REDUCE.
        3. No breach: -> APPROVE.

    Args:
        portfolio: Current portfolio snapshot. Must be a valid PortfolioState.
        params:    Risk configuration. Must be a valid RiskParameters.

    Returns:
        RiskDecision with:
            verdict:            HALT | REDUCE | APPROVE
            messages:           () -- empty for Phase 7B; populated in 7C+.
            max_position_size:  None -- cap logic is Phase 7C+.
            requires_rebalance: False -- rebalance logic is Phase 7C+.

    Raises:
        Nothing beyond what PortfolioState and RiskParameters constructors
        already enforce. All inputs are pre-validated by their frozen
        dataclass constructors.
    """
    verdict: RiskVerdict = _compute_verdict(
        nav=portfolio.nav,
        peak_nav=portfolio.peak_nav,
        max_drawdown_hard_stop=params.max_drawdown_hard_stop,
        max_drawdown_soft_warn=params.max_drawdown_soft_warn,
    )

    return RiskDecision(
        verdict=verdict,
        messages=(),
        max_position_size=None,
        requires_rebalance=False,
    )


# =============================================================================
# SECTION 4 -- EVALUATE PORTFOLIO RISK
# =============================================================================

def x_evaluate_portfolio_risk__mutmut_1(
    portfolio: PortfolioState,
    params:    RiskParameters,
) -> RiskDecision:
    """
    Evaluate risk at the portfolio level, without reference to any specific
    proposed position.

    Used to determine the overall health of the portfolio before any position
    evaluation is attempted. Callers may check the portfolio verdict first
    and skip evaluate_position_risk entirely when verdict is HALT.

    This is a pure function with the same determinism and no-side-effect
    guarantees as evaluate_position_risk.

    Evaluation order:
        1. Hard stop check: if nav <= peak_nav * (1 - hard_stop) -> HALT.
        2. Soft warn check: if nav <= peak_nav * (1 - soft_warn) -> REDUCE.
        3. No breach: -> APPROVE.

    Args:
        portfolio: Current portfolio snapshot. Must be a valid PortfolioState.
        params:    Risk configuration. Must be a valid RiskParameters.

    Returns:
        RiskDecision with:
            verdict:            HALT | REDUCE | APPROVE
            messages:           () -- empty for Phase 7B; populated in 7C+.
            max_position_size:  None -- cap logic is Phase 7C+.
            requires_rebalance: False -- rebalance logic is Phase 7C+.

    Raises:
        Nothing beyond what PortfolioState and RiskParameters constructors
        already enforce. All inputs are pre-validated by their frozen
        dataclass constructors.
    """
    verdict: RiskVerdict = None

    return RiskDecision(
        verdict=verdict,
        messages=(),
        max_position_size=None,
        requires_rebalance=False,
    )


# =============================================================================
# SECTION 4 -- EVALUATE PORTFOLIO RISK
# =============================================================================

def x_evaluate_portfolio_risk__mutmut_2(
    portfolio: PortfolioState,
    params:    RiskParameters,
) -> RiskDecision:
    """
    Evaluate risk at the portfolio level, without reference to any specific
    proposed position.

    Used to determine the overall health of the portfolio before any position
    evaluation is attempted. Callers may check the portfolio verdict first
    and skip evaluate_position_risk entirely when verdict is HALT.

    This is a pure function with the same determinism and no-side-effect
    guarantees as evaluate_position_risk.

    Evaluation order:
        1. Hard stop check: if nav <= peak_nav * (1 - hard_stop) -> HALT.
        2. Soft warn check: if nav <= peak_nav * (1 - soft_warn) -> REDUCE.
        3. No breach: -> APPROVE.

    Args:
        portfolio: Current portfolio snapshot. Must be a valid PortfolioState.
        params:    Risk configuration. Must be a valid RiskParameters.

    Returns:
        RiskDecision with:
            verdict:            HALT | REDUCE | APPROVE
            messages:           () -- empty for Phase 7B; populated in 7C+.
            max_position_size:  None -- cap logic is Phase 7C+.
            requires_rebalance: False -- rebalance logic is Phase 7C+.

    Raises:
        Nothing beyond what PortfolioState and RiskParameters constructors
        already enforce. All inputs are pre-validated by their frozen
        dataclass constructors.
    """
    verdict: RiskVerdict = _compute_verdict(
        nav=None,
        peak_nav=portfolio.peak_nav,
        max_drawdown_hard_stop=params.max_drawdown_hard_stop,
        max_drawdown_soft_warn=params.max_drawdown_soft_warn,
    )

    return RiskDecision(
        verdict=verdict,
        messages=(),
        max_position_size=None,
        requires_rebalance=False,
    )


# =============================================================================
# SECTION 4 -- EVALUATE PORTFOLIO RISK
# =============================================================================

def x_evaluate_portfolio_risk__mutmut_3(
    portfolio: PortfolioState,
    params:    RiskParameters,
) -> RiskDecision:
    """
    Evaluate risk at the portfolio level, without reference to any specific
    proposed position.

    Used to determine the overall health of the portfolio before any position
    evaluation is attempted. Callers may check the portfolio verdict first
    and skip evaluate_position_risk entirely when verdict is HALT.

    This is a pure function with the same determinism and no-side-effect
    guarantees as evaluate_position_risk.

    Evaluation order:
        1. Hard stop check: if nav <= peak_nav * (1 - hard_stop) -> HALT.
        2. Soft warn check: if nav <= peak_nav * (1 - soft_warn) -> REDUCE.
        3. No breach: -> APPROVE.

    Args:
        portfolio: Current portfolio snapshot. Must be a valid PortfolioState.
        params:    Risk configuration. Must be a valid RiskParameters.

    Returns:
        RiskDecision with:
            verdict:            HALT | REDUCE | APPROVE
            messages:           () -- empty for Phase 7B; populated in 7C+.
            max_position_size:  None -- cap logic is Phase 7C+.
            requires_rebalance: False -- rebalance logic is Phase 7C+.

    Raises:
        Nothing beyond what PortfolioState and RiskParameters constructors
        already enforce. All inputs are pre-validated by their frozen
        dataclass constructors.
    """
    verdict: RiskVerdict = _compute_verdict(
        nav=portfolio.nav,
        peak_nav=None,
        max_drawdown_hard_stop=params.max_drawdown_hard_stop,
        max_drawdown_soft_warn=params.max_drawdown_soft_warn,
    )

    return RiskDecision(
        verdict=verdict,
        messages=(),
        max_position_size=None,
        requires_rebalance=False,
    )


# =============================================================================
# SECTION 4 -- EVALUATE PORTFOLIO RISK
# =============================================================================

def x_evaluate_portfolio_risk__mutmut_4(
    portfolio: PortfolioState,
    params:    RiskParameters,
) -> RiskDecision:
    """
    Evaluate risk at the portfolio level, without reference to any specific
    proposed position.

    Used to determine the overall health of the portfolio before any position
    evaluation is attempted. Callers may check the portfolio verdict first
    and skip evaluate_position_risk entirely when verdict is HALT.

    This is a pure function with the same determinism and no-side-effect
    guarantees as evaluate_position_risk.

    Evaluation order:
        1. Hard stop check: if nav <= peak_nav * (1 - hard_stop) -> HALT.
        2. Soft warn check: if nav <= peak_nav * (1 - soft_warn) -> REDUCE.
        3. No breach: -> APPROVE.

    Args:
        portfolio: Current portfolio snapshot. Must be a valid PortfolioState.
        params:    Risk configuration. Must be a valid RiskParameters.

    Returns:
        RiskDecision with:
            verdict:            HALT | REDUCE | APPROVE
            messages:           () -- empty for Phase 7B; populated in 7C+.
            max_position_size:  None -- cap logic is Phase 7C+.
            requires_rebalance: False -- rebalance logic is Phase 7C+.

    Raises:
        Nothing beyond what PortfolioState and RiskParameters constructors
        already enforce. All inputs are pre-validated by their frozen
        dataclass constructors.
    """
    verdict: RiskVerdict = _compute_verdict(
        nav=portfolio.nav,
        peak_nav=portfolio.peak_nav,
        max_drawdown_hard_stop=None,
        max_drawdown_soft_warn=params.max_drawdown_soft_warn,
    )

    return RiskDecision(
        verdict=verdict,
        messages=(),
        max_position_size=None,
        requires_rebalance=False,
    )


# =============================================================================
# SECTION 4 -- EVALUATE PORTFOLIO RISK
# =============================================================================

def x_evaluate_portfolio_risk__mutmut_5(
    portfolio: PortfolioState,
    params:    RiskParameters,
) -> RiskDecision:
    """
    Evaluate risk at the portfolio level, without reference to any specific
    proposed position.

    Used to determine the overall health of the portfolio before any position
    evaluation is attempted. Callers may check the portfolio verdict first
    and skip evaluate_position_risk entirely when verdict is HALT.

    This is a pure function with the same determinism and no-side-effect
    guarantees as evaluate_position_risk.

    Evaluation order:
        1. Hard stop check: if nav <= peak_nav * (1 - hard_stop) -> HALT.
        2. Soft warn check: if nav <= peak_nav * (1 - soft_warn) -> REDUCE.
        3. No breach: -> APPROVE.

    Args:
        portfolio: Current portfolio snapshot. Must be a valid PortfolioState.
        params:    Risk configuration. Must be a valid RiskParameters.

    Returns:
        RiskDecision with:
            verdict:            HALT | REDUCE | APPROVE
            messages:           () -- empty for Phase 7B; populated in 7C+.
            max_position_size:  None -- cap logic is Phase 7C+.
            requires_rebalance: False -- rebalance logic is Phase 7C+.

    Raises:
        Nothing beyond what PortfolioState and RiskParameters constructors
        already enforce. All inputs are pre-validated by their frozen
        dataclass constructors.
    """
    verdict: RiskVerdict = _compute_verdict(
        nav=portfolio.nav,
        peak_nav=portfolio.peak_nav,
        max_drawdown_hard_stop=params.max_drawdown_hard_stop,
        max_drawdown_soft_warn=None,
    )

    return RiskDecision(
        verdict=verdict,
        messages=(),
        max_position_size=None,
        requires_rebalance=False,
    )


# =============================================================================
# SECTION 4 -- EVALUATE PORTFOLIO RISK
# =============================================================================

def x_evaluate_portfolio_risk__mutmut_6(
    portfolio: PortfolioState,
    params:    RiskParameters,
) -> RiskDecision:
    """
    Evaluate risk at the portfolio level, without reference to any specific
    proposed position.

    Used to determine the overall health of the portfolio before any position
    evaluation is attempted. Callers may check the portfolio verdict first
    and skip evaluate_position_risk entirely when verdict is HALT.

    This is a pure function with the same determinism and no-side-effect
    guarantees as evaluate_position_risk.

    Evaluation order:
        1. Hard stop check: if nav <= peak_nav * (1 - hard_stop) -> HALT.
        2. Soft warn check: if nav <= peak_nav * (1 - soft_warn) -> REDUCE.
        3. No breach: -> APPROVE.

    Args:
        portfolio: Current portfolio snapshot. Must be a valid PortfolioState.
        params:    Risk configuration. Must be a valid RiskParameters.

    Returns:
        RiskDecision with:
            verdict:            HALT | REDUCE | APPROVE
            messages:           () -- empty for Phase 7B; populated in 7C+.
            max_position_size:  None -- cap logic is Phase 7C+.
            requires_rebalance: False -- rebalance logic is Phase 7C+.

    Raises:
        Nothing beyond what PortfolioState and RiskParameters constructors
        already enforce. All inputs are pre-validated by their frozen
        dataclass constructors.
    """
    verdict: RiskVerdict = _compute_verdict(
        peak_nav=portfolio.peak_nav,
        max_drawdown_hard_stop=params.max_drawdown_hard_stop,
        max_drawdown_soft_warn=params.max_drawdown_soft_warn,
    )

    return RiskDecision(
        verdict=verdict,
        messages=(),
        max_position_size=None,
        requires_rebalance=False,
    )


# =============================================================================
# SECTION 4 -- EVALUATE PORTFOLIO RISK
# =============================================================================

def x_evaluate_portfolio_risk__mutmut_7(
    portfolio: PortfolioState,
    params:    RiskParameters,
) -> RiskDecision:
    """
    Evaluate risk at the portfolio level, without reference to any specific
    proposed position.

    Used to determine the overall health of the portfolio before any position
    evaluation is attempted. Callers may check the portfolio verdict first
    and skip evaluate_position_risk entirely when verdict is HALT.

    This is a pure function with the same determinism and no-side-effect
    guarantees as evaluate_position_risk.

    Evaluation order:
        1. Hard stop check: if nav <= peak_nav * (1 - hard_stop) -> HALT.
        2. Soft warn check: if nav <= peak_nav * (1 - soft_warn) -> REDUCE.
        3. No breach: -> APPROVE.

    Args:
        portfolio: Current portfolio snapshot. Must be a valid PortfolioState.
        params:    Risk configuration. Must be a valid RiskParameters.

    Returns:
        RiskDecision with:
            verdict:            HALT | REDUCE | APPROVE
            messages:           () -- empty for Phase 7B; populated in 7C+.
            max_position_size:  None -- cap logic is Phase 7C+.
            requires_rebalance: False -- rebalance logic is Phase 7C+.

    Raises:
        Nothing beyond what PortfolioState and RiskParameters constructors
        already enforce. All inputs are pre-validated by their frozen
        dataclass constructors.
    """
    verdict: RiskVerdict = _compute_verdict(
        nav=portfolio.nav,
        max_drawdown_hard_stop=params.max_drawdown_hard_stop,
        max_drawdown_soft_warn=params.max_drawdown_soft_warn,
    )

    return RiskDecision(
        verdict=verdict,
        messages=(),
        max_position_size=None,
        requires_rebalance=False,
    )


# =============================================================================
# SECTION 4 -- EVALUATE PORTFOLIO RISK
# =============================================================================

def x_evaluate_portfolio_risk__mutmut_8(
    portfolio: PortfolioState,
    params:    RiskParameters,
) -> RiskDecision:
    """
    Evaluate risk at the portfolio level, without reference to any specific
    proposed position.

    Used to determine the overall health of the portfolio before any position
    evaluation is attempted. Callers may check the portfolio verdict first
    and skip evaluate_position_risk entirely when verdict is HALT.

    This is a pure function with the same determinism and no-side-effect
    guarantees as evaluate_position_risk.

    Evaluation order:
        1. Hard stop check: if nav <= peak_nav * (1 - hard_stop) -> HALT.
        2. Soft warn check: if nav <= peak_nav * (1 - soft_warn) -> REDUCE.
        3. No breach: -> APPROVE.

    Args:
        portfolio: Current portfolio snapshot. Must be a valid PortfolioState.
        params:    Risk configuration. Must be a valid RiskParameters.

    Returns:
        RiskDecision with:
            verdict:            HALT | REDUCE | APPROVE
            messages:           () -- empty for Phase 7B; populated in 7C+.
            max_position_size:  None -- cap logic is Phase 7C+.
            requires_rebalance: False -- rebalance logic is Phase 7C+.

    Raises:
        Nothing beyond what PortfolioState and RiskParameters constructors
        already enforce. All inputs are pre-validated by their frozen
        dataclass constructors.
    """
    verdict: RiskVerdict = _compute_verdict(
        nav=portfolio.nav,
        peak_nav=portfolio.peak_nav,
        max_drawdown_soft_warn=params.max_drawdown_soft_warn,
    )

    return RiskDecision(
        verdict=verdict,
        messages=(),
        max_position_size=None,
        requires_rebalance=False,
    )


# =============================================================================
# SECTION 4 -- EVALUATE PORTFOLIO RISK
# =============================================================================

def x_evaluate_portfolio_risk__mutmut_9(
    portfolio: PortfolioState,
    params:    RiskParameters,
) -> RiskDecision:
    """
    Evaluate risk at the portfolio level, without reference to any specific
    proposed position.

    Used to determine the overall health of the portfolio before any position
    evaluation is attempted. Callers may check the portfolio verdict first
    and skip evaluate_position_risk entirely when verdict is HALT.

    This is a pure function with the same determinism and no-side-effect
    guarantees as evaluate_position_risk.

    Evaluation order:
        1. Hard stop check: if nav <= peak_nav * (1 - hard_stop) -> HALT.
        2. Soft warn check: if nav <= peak_nav * (1 - soft_warn) -> REDUCE.
        3. No breach: -> APPROVE.

    Args:
        portfolio: Current portfolio snapshot. Must be a valid PortfolioState.
        params:    Risk configuration. Must be a valid RiskParameters.

    Returns:
        RiskDecision with:
            verdict:            HALT | REDUCE | APPROVE
            messages:           () -- empty for Phase 7B; populated in 7C+.
            max_position_size:  None -- cap logic is Phase 7C+.
            requires_rebalance: False -- rebalance logic is Phase 7C+.

    Raises:
        Nothing beyond what PortfolioState and RiskParameters constructors
        already enforce. All inputs are pre-validated by their frozen
        dataclass constructors.
    """
    verdict: RiskVerdict = _compute_verdict(
        nav=portfolio.nav,
        peak_nav=portfolio.peak_nav,
        max_drawdown_hard_stop=params.max_drawdown_hard_stop,
        )

    return RiskDecision(
        verdict=verdict,
        messages=(),
        max_position_size=None,
        requires_rebalance=False,
    )


# =============================================================================
# SECTION 4 -- EVALUATE PORTFOLIO RISK
# =============================================================================

def x_evaluate_portfolio_risk__mutmut_10(
    portfolio: PortfolioState,
    params:    RiskParameters,
) -> RiskDecision:
    """
    Evaluate risk at the portfolio level, without reference to any specific
    proposed position.

    Used to determine the overall health of the portfolio before any position
    evaluation is attempted. Callers may check the portfolio verdict first
    and skip evaluate_position_risk entirely when verdict is HALT.

    This is a pure function with the same determinism and no-side-effect
    guarantees as evaluate_position_risk.

    Evaluation order:
        1. Hard stop check: if nav <= peak_nav * (1 - hard_stop) -> HALT.
        2. Soft warn check: if nav <= peak_nav * (1 - soft_warn) -> REDUCE.
        3. No breach: -> APPROVE.

    Args:
        portfolio: Current portfolio snapshot. Must be a valid PortfolioState.
        params:    Risk configuration. Must be a valid RiskParameters.

    Returns:
        RiskDecision with:
            verdict:            HALT | REDUCE | APPROVE
            messages:           () -- empty for Phase 7B; populated in 7C+.
            max_position_size:  None -- cap logic is Phase 7C+.
            requires_rebalance: False -- rebalance logic is Phase 7C+.

    Raises:
        Nothing beyond what PortfolioState and RiskParameters constructors
        already enforce. All inputs are pre-validated by their frozen
        dataclass constructors.
    """
    verdict: RiskVerdict = _compute_verdict(
        nav=portfolio.nav,
        peak_nav=portfolio.peak_nav,
        max_drawdown_hard_stop=params.max_drawdown_hard_stop,
        max_drawdown_soft_warn=params.max_drawdown_soft_warn,
    )

    return RiskDecision(
        verdict=None,
        messages=(),
        max_position_size=None,
        requires_rebalance=False,
    )


# =============================================================================
# SECTION 4 -- EVALUATE PORTFOLIO RISK
# =============================================================================

def x_evaluate_portfolio_risk__mutmut_11(
    portfolio: PortfolioState,
    params:    RiskParameters,
) -> RiskDecision:
    """
    Evaluate risk at the portfolio level, without reference to any specific
    proposed position.

    Used to determine the overall health of the portfolio before any position
    evaluation is attempted. Callers may check the portfolio verdict first
    and skip evaluate_position_risk entirely when verdict is HALT.

    This is a pure function with the same determinism and no-side-effect
    guarantees as evaluate_position_risk.

    Evaluation order:
        1. Hard stop check: if nav <= peak_nav * (1 - hard_stop) -> HALT.
        2. Soft warn check: if nav <= peak_nav * (1 - soft_warn) -> REDUCE.
        3. No breach: -> APPROVE.

    Args:
        portfolio: Current portfolio snapshot. Must be a valid PortfolioState.
        params:    Risk configuration. Must be a valid RiskParameters.

    Returns:
        RiskDecision with:
            verdict:            HALT | REDUCE | APPROVE
            messages:           () -- empty for Phase 7B; populated in 7C+.
            max_position_size:  None -- cap logic is Phase 7C+.
            requires_rebalance: False -- rebalance logic is Phase 7C+.

    Raises:
        Nothing beyond what PortfolioState and RiskParameters constructors
        already enforce. All inputs are pre-validated by their frozen
        dataclass constructors.
    """
    verdict: RiskVerdict = _compute_verdict(
        nav=portfolio.nav,
        peak_nav=portfolio.peak_nav,
        max_drawdown_hard_stop=params.max_drawdown_hard_stop,
        max_drawdown_soft_warn=params.max_drawdown_soft_warn,
    )

    return RiskDecision(
        verdict=verdict,
        messages=None,
        max_position_size=None,
        requires_rebalance=False,
    )


# =============================================================================
# SECTION 4 -- EVALUATE PORTFOLIO RISK
# =============================================================================

def x_evaluate_portfolio_risk__mutmut_12(
    portfolio: PortfolioState,
    params:    RiskParameters,
) -> RiskDecision:
    """
    Evaluate risk at the portfolio level, without reference to any specific
    proposed position.

    Used to determine the overall health of the portfolio before any position
    evaluation is attempted. Callers may check the portfolio verdict first
    and skip evaluate_position_risk entirely when verdict is HALT.

    This is a pure function with the same determinism and no-side-effect
    guarantees as evaluate_position_risk.

    Evaluation order:
        1. Hard stop check: if nav <= peak_nav * (1 - hard_stop) -> HALT.
        2. Soft warn check: if nav <= peak_nav * (1 - soft_warn) -> REDUCE.
        3. No breach: -> APPROVE.

    Args:
        portfolio: Current portfolio snapshot. Must be a valid PortfolioState.
        params:    Risk configuration. Must be a valid RiskParameters.

    Returns:
        RiskDecision with:
            verdict:            HALT | REDUCE | APPROVE
            messages:           () -- empty for Phase 7B; populated in 7C+.
            max_position_size:  None -- cap logic is Phase 7C+.
            requires_rebalance: False -- rebalance logic is Phase 7C+.

    Raises:
        Nothing beyond what PortfolioState and RiskParameters constructors
        already enforce. All inputs are pre-validated by their frozen
        dataclass constructors.
    """
    verdict: RiskVerdict = _compute_verdict(
        nav=portfolio.nav,
        peak_nav=portfolio.peak_nav,
        max_drawdown_hard_stop=params.max_drawdown_hard_stop,
        max_drawdown_soft_warn=params.max_drawdown_soft_warn,
    )

    return RiskDecision(
        verdict=verdict,
        messages=(),
        max_position_size=None,
        requires_rebalance=None,
    )


# =============================================================================
# SECTION 4 -- EVALUATE PORTFOLIO RISK
# =============================================================================

def x_evaluate_portfolio_risk__mutmut_13(
    portfolio: PortfolioState,
    params:    RiskParameters,
) -> RiskDecision:
    """
    Evaluate risk at the portfolio level, without reference to any specific
    proposed position.

    Used to determine the overall health of the portfolio before any position
    evaluation is attempted. Callers may check the portfolio verdict first
    and skip evaluate_position_risk entirely when verdict is HALT.

    This is a pure function with the same determinism and no-side-effect
    guarantees as evaluate_position_risk.

    Evaluation order:
        1. Hard stop check: if nav <= peak_nav * (1 - hard_stop) -> HALT.
        2. Soft warn check: if nav <= peak_nav * (1 - soft_warn) -> REDUCE.
        3. No breach: -> APPROVE.

    Args:
        portfolio: Current portfolio snapshot. Must be a valid PortfolioState.
        params:    Risk configuration. Must be a valid RiskParameters.

    Returns:
        RiskDecision with:
            verdict:            HALT | REDUCE | APPROVE
            messages:           () -- empty for Phase 7B; populated in 7C+.
            max_position_size:  None -- cap logic is Phase 7C+.
            requires_rebalance: False -- rebalance logic is Phase 7C+.

    Raises:
        Nothing beyond what PortfolioState and RiskParameters constructors
        already enforce. All inputs are pre-validated by their frozen
        dataclass constructors.
    """
    verdict: RiskVerdict = _compute_verdict(
        nav=portfolio.nav,
        peak_nav=portfolio.peak_nav,
        max_drawdown_hard_stop=params.max_drawdown_hard_stop,
        max_drawdown_soft_warn=params.max_drawdown_soft_warn,
    )

    return RiskDecision(
        messages=(),
        max_position_size=None,
        requires_rebalance=False,
    )


# =============================================================================
# SECTION 4 -- EVALUATE PORTFOLIO RISK
# =============================================================================

def x_evaluate_portfolio_risk__mutmut_14(
    portfolio: PortfolioState,
    params:    RiskParameters,
) -> RiskDecision:
    """
    Evaluate risk at the portfolio level, without reference to any specific
    proposed position.

    Used to determine the overall health of the portfolio before any position
    evaluation is attempted. Callers may check the portfolio verdict first
    and skip evaluate_position_risk entirely when verdict is HALT.

    This is a pure function with the same determinism and no-side-effect
    guarantees as evaluate_position_risk.

    Evaluation order:
        1. Hard stop check: if nav <= peak_nav * (1 - hard_stop) -> HALT.
        2. Soft warn check: if nav <= peak_nav * (1 - soft_warn) -> REDUCE.
        3. No breach: -> APPROVE.

    Args:
        portfolio: Current portfolio snapshot. Must be a valid PortfolioState.
        params:    Risk configuration. Must be a valid RiskParameters.

    Returns:
        RiskDecision with:
            verdict:            HALT | REDUCE | APPROVE
            messages:           () -- empty for Phase 7B; populated in 7C+.
            max_position_size:  None -- cap logic is Phase 7C+.
            requires_rebalance: False -- rebalance logic is Phase 7C+.

    Raises:
        Nothing beyond what PortfolioState and RiskParameters constructors
        already enforce. All inputs are pre-validated by their frozen
        dataclass constructors.
    """
    verdict: RiskVerdict = _compute_verdict(
        nav=portfolio.nav,
        peak_nav=portfolio.peak_nav,
        max_drawdown_hard_stop=params.max_drawdown_hard_stop,
        max_drawdown_soft_warn=params.max_drawdown_soft_warn,
    )

    return RiskDecision(
        verdict=verdict,
        max_position_size=None,
        requires_rebalance=False,
    )


# =============================================================================
# SECTION 4 -- EVALUATE PORTFOLIO RISK
# =============================================================================

def x_evaluate_portfolio_risk__mutmut_15(
    portfolio: PortfolioState,
    params:    RiskParameters,
) -> RiskDecision:
    """
    Evaluate risk at the portfolio level, without reference to any specific
    proposed position.

    Used to determine the overall health of the portfolio before any position
    evaluation is attempted. Callers may check the portfolio verdict first
    and skip evaluate_position_risk entirely when verdict is HALT.

    This is a pure function with the same determinism and no-side-effect
    guarantees as evaluate_position_risk.

    Evaluation order:
        1. Hard stop check: if nav <= peak_nav * (1 - hard_stop) -> HALT.
        2. Soft warn check: if nav <= peak_nav * (1 - soft_warn) -> REDUCE.
        3. No breach: -> APPROVE.

    Args:
        portfolio: Current portfolio snapshot. Must be a valid PortfolioState.
        params:    Risk configuration. Must be a valid RiskParameters.

    Returns:
        RiskDecision with:
            verdict:            HALT | REDUCE | APPROVE
            messages:           () -- empty for Phase 7B; populated in 7C+.
            max_position_size:  None -- cap logic is Phase 7C+.
            requires_rebalance: False -- rebalance logic is Phase 7C+.

    Raises:
        Nothing beyond what PortfolioState and RiskParameters constructors
        already enforce. All inputs are pre-validated by their frozen
        dataclass constructors.
    """
    verdict: RiskVerdict = _compute_verdict(
        nav=portfolio.nav,
        peak_nav=portfolio.peak_nav,
        max_drawdown_hard_stop=params.max_drawdown_hard_stop,
        max_drawdown_soft_warn=params.max_drawdown_soft_warn,
    )

    return RiskDecision(
        verdict=verdict,
        messages=(),
        requires_rebalance=False,
    )


# =============================================================================
# SECTION 4 -- EVALUATE PORTFOLIO RISK
# =============================================================================

def x_evaluate_portfolio_risk__mutmut_16(
    portfolio: PortfolioState,
    params:    RiskParameters,
) -> RiskDecision:
    """
    Evaluate risk at the portfolio level, without reference to any specific
    proposed position.

    Used to determine the overall health of the portfolio before any position
    evaluation is attempted. Callers may check the portfolio verdict first
    and skip evaluate_position_risk entirely when verdict is HALT.

    This is a pure function with the same determinism and no-side-effect
    guarantees as evaluate_position_risk.

    Evaluation order:
        1. Hard stop check: if nav <= peak_nav * (1 - hard_stop) -> HALT.
        2. Soft warn check: if nav <= peak_nav * (1 - soft_warn) -> REDUCE.
        3. No breach: -> APPROVE.

    Args:
        portfolio: Current portfolio snapshot. Must be a valid PortfolioState.
        params:    Risk configuration. Must be a valid RiskParameters.

    Returns:
        RiskDecision with:
            verdict:            HALT | REDUCE | APPROVE
            messages:           () -- empty for Phase 7B; populated in 7C+.
            max_position_size:  None -- cap logic is Phase 7C+.
            requires_rebalance: False -- rebalance logic is Phase 7C+.

    Raises:
        Nothing beyond what PortfolioState and RiskParameters constructors
        already enforce. All inputs are pre-validated by their frozen
        dataclass constructors.
    """
    verdict: RiskVerdict = _compute_verdict(
        nav=portfolio.nav,
        peak_nav=portfolio.peak_nav,
        max_drawdown_hard_stop=params.max_drawdown_hard_stop,
        max_drawdown_soft_warn=params.max_drawdown_soft_warn,
    )

    return RiskDecision(
        verdict=verdict,
        messages=(),
        max_position_size=None,
        )


# =============================================================================
# SECTION 4 -- EVALUATE PORTFOLIO RISK
# =============================================================================

def x_evaluate_portfolio_risk__mutmut_17(
    portfolio: PortfolioState,
    params:    RiskParameters,
) -> RiskDecision:
    """
    Evaluate risk at the portfolio level, without reference to any specific
    proposed position.

    Used to determine the overall health of the portfolio before any position
    evaluation is attempted. Callers may check the portfolio verdict first
    and skip evaluate_position_risk entirely when verdict is HALT.

    This is a pure function with the same determinism and no-side-effect
    guarantees as evaluate_position_risk.

    Evaluation order:
        1. Hard stop check: if nav <= peak_nav * (1 - hard_stop) -> HALT.
        2. Soft warn check: if nav <= peak_nav * (1 - soft_warn) -> REDUCE.
        3. No breach: -> APPROVE.

    Args:
        portfolio: Current portfolio snapshot. Must be a valid PortfolioState.
        params:    Risk configuration. Must be a valid RiskParameters.

    Returns:
        RiskDecision with:
            verdict:            HALT | REDUCE | APPROVE
            messages:           () -- empty for Phase 7B; populated in 7C+.
            max_position_size:  None -- cap logic is Phase 7C+.
            requires_rebalance: False -- rebalance logic is Phase 7C+.

    Raises:
        Nothing beyond what PortfolioState and RiskParameters constructors
        already enforce. All inputs are pre-validated by their frozen
        dataclass constructors.
    """
    verdict: RiskVerdict = _compute_verdict(
        nav=portfolio.nav,
        peak_nav=portfolio.peak_nav,
        max_drawdown_hard_stop=params.max_drawdown_hard_stop,
        max_drawdown_soft_warn=params.max_drawdown_soft_warn,
    )

    return RiskDecision(
        verdict=verdict,
        messages=(),
        max_position_size=None,
        requires_rebalance=True,
    )

x_evaluate_portfolio_risk__mutmut_mutants : ClassVar[MutantDict] = { # type: ignore
'x_evaluate_portfolio_risk__mutmut_1': x_evaluate_portfolio_risk__mutmut_1, 
    'x_evaluate_portfolio_risk__mutmut_2': x_evaluate_portfolio_risk__mutmut_2, 
    'x_evaluate_portfolio_risk__mutmut_3': x_evaluate_portfolio_risk__mutmut_3, 
    'x_evaluate_portfolio_risk__mutmut_4': x_evaluate_portfolio_risk__mutmut_4, 
    'x_evaluate_portfolio_risk__mutmut_5': x_evaluate_portfolio_risk__mutmut_5, 
    'x_evaluate_portfolio_risk__mutmut_6': x_evaluate_portfolio_risk__mutmut_6, 
    'x_evaluate_portfolio_risk__mutmut_7': x_evaluate_portfolio_risk__mutmut_7, 
    'x_evaluate_portfolio_risk__mutmut_8': x_evaluate_portfolio_risk__mutmut_8, 
    'x_evaluate_portfolio_risk__mutmut_9': x_evaluate_portfolio_risk__mutmut_9, 
    'x_evaluate_portfolio_risk__mutmut_10': x_evaluate_portfolio_risk__mutmut_10, 
    'x_evaluate_portfolio_risk__mutmut_11': x_evaluate_portfolio_risk__mutmut_11, 
    'x_evaluate_portfolio_risk__mutmut_12': x_evaluate_portfolio_risk__mutmut_12, 
    'x_evaluate_portfolio_risk__mutmut_13': x_evaluate_portfolio_risk__mutmut_13, 
    'x_evaluate_portfolio_risk__mutmut_14': x_evaluate_portfolio_risk__mutmut_14, 
    'x_evaluate_portfolio_risk__mutmut_15': x_evaluate_portfolio_risk__mutmut_15, 
    'x_evaluate_portfolio_risk__mutmut_16': x_evaluate_portfolio_risk__mutmut_16, 
    'x_evaluate_portfolio_risk__mutmut_17': x_evaluate_portfolio_risk__mutmut_17
}
x_evaluate_portfolio_risk__mutmut_orig.__name__ = 'x_evaluate_portfolio_risk'


# =============================================================================
# SECTION 5 -- MODULE __all__
# =============================================================================

__all__ = [
    "RiskDecision",
    "evaluate_position_risk",
    "evaluate_portfolio_risk",
]
