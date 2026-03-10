# =============================================================================
# JARVIS v6.1.0 -- PHASE 7D: RISK & CAPITAL MANAGEMENT LAYER
# File:   jarvis/core/risk_layer/sizing.py
# Authority: JARVIS FAS v6.1.0 -- Phase 7D, Position Sizing
# =============================================================================
#
# SCOPE
# -----
# Implements deterministic position sizing for Phase 7D.
# Exactly two public symbols are defined:
#
#   PositionSizingResult  -- frozen dataclass; output of size_position().
#   size_position()       -- pure sizing function; consumes a RiskDecision.
#
# CHANGES FROM PHASE 7C
# ---------------------
#   A) REDUCE verdict multiplier: when verdict == REDUCE, an additional
#      liquidity_haircut_floor multiplier is applied to the Kelly-sized target.
#
#   B) Kelly fraction sizing: target *= params.kelly_fraction.
#      Applied after cap, before REDUCE multiplier.
#      Guard: kelly_fraction validated in (0.0, 1.0] by domain.
#
#   C) Volatility-adjusted cap: effective_cap = base_cap * vol_cap_scalar,
#      where vol_cap_scalar = min(volatility_target_ann / max(position_vol, 1e-8), 1.0).
#      When position_vol is None -> vol_cap_scalar = 1.0 (identity, backward compatible).
#
#   D) Liquidity floor guarantee: target >= requested * liquidity_haircut_floor.
#      Applied last; prevents pathological compression to near-zero.
#
# SIZING PIPELINE ORDER (deterministic, fixed):
#   1. HALT branch       -> return immediately (allowed=False, target=None).
#   2. requested_notional = position.quantity * position.current_price
#   3. base_cap           = portfolio.nav * params.max_position_pct_nav
#   4. vol_cap_scalar     = min(params.volatility_target_ann / max(position_vol, 1e-8), 1.0)
#                           if position_vol is not None else 1.0
#   5. effective_cap      = min(base_cap, base_cap * vol_cap_scalar)
#   6. raw_target         = min(requested_notional, effective_cap)
#   7. kelly_target       = raw_target * params.kelly_fraction
#   8. reduce_target      = kelly_target * params.liquidity_haircut_floor  (REDUCE only)
#                           kelly_target  (APPROVE)
#   9. liquidity_floor    = requested_notional * params.liquidity_haircut_floor
#  10. target             = max(reduce_target, liquidity_floor)
#
# INVARIANTS
# ----------
# INV-SZ-01: target_notional is None whenever allowed is False.
# INV-SZ-02: target_notional is a finite positive float whenever allowed is True.
# INV-SZ-03: target_notional <= effective_cap (before liquidity floor) whenever allowed is True.
# INV-SZ-04: result is frozen; no field may be mutated after construction.
# INV-SZ-05: target_notional >= requested_notional * liquidity_haircut_floor
#            whenever allowed is True (liquidity floor guarantee).
#
# BACKWARD COMPATIBILITY
# ----------------------
# position_vol=None, kelly_fraction=1.0, verdict=APPROVE:
#   -> vol_cap_scalar=1.0, kelly multiplier=1.0, no REDUCE -> Phase 7C arithmetic.
#
# DETERMINISM CONSTRAINTS
# -----------------------
# DET-01  No stochastic operations.
# DET-02  All inputs passed explicitly. No module-level mutable reads.
# DET-03  No side effects. PositionSizingResult is frozen; inputs never mutated.
# DET-04  All arithmetic is deterministic: *, min(), max(), guarded division.
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
#   No float rounding / coercion
#   No circular imports
# =============================================================================

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

from .domain import (
    PortfolioState,
    PositionSpec,
    RiskParameters,
    RiskVerdict,
)
from .evaluator import RiskDecision
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
# SECTION 1 -- POSITION SIZING RESULT (OUTPUT CONTRACT)
# =============================================================================

@dataclass(frozen=True)
class PositionSizingResult:
    """
    Immutable output of size_position().

    Attributes:
        allowed:          True when the position may proceed (verdict is not
                          HALT). False when all new risk-taking is suspended.
        target_notional:  The approved USD notional size for this position.
                          None when allowed is False.
                          A finite positive float when allowed is True.
        reason:           The RiskVerdict that drove this sizing decision.
                          Echoed directly from the input RiskDecision.verdict.

    Invariants:
        INV-SZ-01  target_notional is None when allowed is False.
        INV-SZ-02  target_notional is a finite positive float when allowed is True.
        INV-SZ-04  frozen=True -- no field may be mutated after construction.

    No validation in __post_init__. Correctness is size_position()'s responsibility.
    """

    allowed:          bool
    target_notional:  Optional[float]
    reason:           RiskVerdict


# =============================================================================
# SECTION 2 -- SIZE POSITION
# =============================================================================

def size_position(
    position:     PositionSpec,
    portfolio:    PortfolioState,
    params:       RiskParameters,
    decision:     RiskDecision,
    position_vol: Optional[float] = None,
) -> PositionSizingResult:
    args = [position, portfolio, params, decision, position_vol]# type: ignore
    kwargs = {}# type: ignore
    return _mutmut_trampoline(x_size_position__mutmut_orig, x_size_position__mutmut_mutants, args, kwargs, None)


# =============================================================================
# SECTION 2 -- SIZE POSITION
# =============================================================================

def x_size_position__mutmut_orig(
    position:     PositionSpec,
    portfolio:    PortfolioState,
    params:       RiskParameters,
    decision:     RiskDecision,
    position_vol: Optional[float] = None,
) -> PositionSizingResult:
    """
    Compute the allowed position size given a pre-evaluated RiskDecision.

    Pure function: reads arguments, returns PositionSizingResult.
    No mutation, no global state, no I/O, no side effects.

    Sizing pipeline (fixed order):
        1.  HALT -> return immediately.
        2.  requested_notional = quantity * current_price
        3.  base_cap = nav * max_position_pct_nav
        4.  vol_cap_scalar = min(volatility_target_ann / max(position_vol, 1e-8), 1.0)
                             if position_vol is not None else 1.0
        5.  effective_cap = min(base_cap, base_cap * vol_cap_scalar)
        6.  raw_target = min(requested_notional, effective_cap)
        7.  kelly_target = raw_target * kelly_fraction
        8.  reduce_target = kelly_target * liquidity_haircut_floor  (REDUCE)
                          = kelly_target                             (APPROVE)
        9.  liquidity_floor = requested_notional * liquidity_haircut_floor
        10. target = max(reduce_target, liquidity_floor)

    Args:
        position:     PositionSpec. quantity and current_price derive requested notional.
        portfolio:    PortfolioState. nav used for base cap.
        params:       RiskParameters. All sizing scalars consumed here.
        decision:     RiskDecision from evaluate_position_risk(). Only verdict consumed.
        position_vol: Optional annualised volatility of this position.
                      None -> vol_cap_scalar = 1.0 (no vol adjustment; backward compat).

    Returns:
        PositionSizingResult(allowed, target_notional, reason).
    """
    # ------------------------------------------------------------------
    # Step 1: HALT -- no sizing arithmetic performed.
    # ------------------------------------------------------------------
    if decision.verdict is RiskVerdict.HALT:
        return PositionSizingResult(
            allowed=False,
            target_notional=None,
            reason=decision.verdict,
        )

    # ------------------------------------------------------------------
    # Step 2: Requested notional.
    # quantity and current_price are finite and > 0 (domain-validated).
    # ------------------------------------------------------------------
    requested_notional: float = position.quantity * position.current_price

    # ------------------------------------------------------------------
    # Step 3: Base position cap.
    # nav and max_position_pct_nav are finite and > 0 (domain-validated).
    # ------------------------------------------------------------------
    base_cap: float = portfolio.nav * params.max_position_pct_nav

    # ------------------------------------------------------------------
    # Step 4: Volatility-adjusted cap scalar.
    # position_vol=None -> scalar=1.0 (identity; preserves Phase 7C output).
    # max(position_vol, 1e-8) guards against division by zero or near-zero.
    # min(..., 1.0) prevents the scalar from exceeding 1 (no vol-based leverage).
    # ------------------------------------------------------------------
    if position_vol is not None:
        vol_cap_scalar: float = min(
            params.volatility_target_ann / max(position_vol, 1e-8),
            1.0,
        )
    else:
        vol_cap_scalar = 1.0

    # ------------------------------------------------------------------
    # Step 5: Effective cap.
    # vol_cap = base_cap * scalar. effective_cap = min(base_cap, vol_cap).
    # When scalar=1.0: vol_cap == base_cap -> effective_cap == base_cap.
    # ------------------------------------------------------------------
    effective_cap: float = min(base_cap, base_cap * vol_cap_scalar)

    # ------------------------------------------------------------------
    # Step 6: Raw target capped at effective_cap.
    # ------------------------------------------------------------------
    raw_target: float = min(requested_notional, effective_cap)

    # ------------------------------------------------------------------
    # Step 7: Kelly fraction.
    # kelly_fraction is validated in (0.0, 1.0] by RiskParameters.
    # No guard needed; always reduces or preserves raw_target.
    # ------------------------------------------------------------------
    kelly_target: float = raw_target * params.kelly_fraction

    # ------------------------------------------------------------------
    # Step 8: REDUCE multiplier (conditional on clamping).
    # REDUCE applies liquidity_haircut_floor only when the position was
    # clamped by the cap (raw_target < requested_notional).
    # When not clamped (position already within cap), REDUCE passes
    # kelly_target through unchanged -- no additional compression.
    # APPROVE always passes kelly_target through unchanged.
    # liquidity_haircut_floor validated in (0.0, 1.0] by RiskParameters.
    # ------------------------------------------------------------------
    _was_clamped: bool = raw_target < requested_notional
    if decision.verdict is RiskVerdict.REDUCE and _was_clamped:
        reduce_target: float = kelly_target * params.liquidity_haircut_floor
    else:
        reduce_target = kelly_target

    # ------------------------------------------------------------------
    # Step 9: Liquidity floor guarantee (INV-SZ-05).
    # Even after Kelly and REDUCE compression, target must be at least
    # liquidity_haircut_floor fraction of the original requested notional.
    # This prevents compound discounting from compressing to near-zero.
    # ------------------------------------------------------------------
    liquidity_floor_value: float = requested_notional * params.liquidity_haircut_floor
    target: float = max(reduce_target, liquidity_floor_value)

    return PositionSizingResult(
        allowed=True,
        target_notional=target,
        reason=decision.verdict,
    )


# =============================================================================
# SECTION 2 -- SIZE POSITION
# =============================================================================

def x_size_position__mutmut_1(
    position:     PositionSpec,
    portfolio:    PortfolioState,
    params:       RiskParameters,
    decision:     RiskDecision,
    position_vol: Optional[float] = None,
) -> PositionSizingResult:
    """
    Compute the allowed position size given a pre-evaluated RiskDecision.

    Pure function: reads arguments, returns PositionSizingResult.
    No mutation, no global state, no I/O, no side effects.

    Sizing pipeline (fixed order):
        1.  HALT -> return immediately.
        2.  requested_notional = quantity * current_price
        3.  base_cap = nav * max_position_pct_nav
        4.  vol_cap_scalar = min(volatility_target_ann / max(position_vol, 1e-8), 1.0)
                             if position_vol is not None else 1.0
        5.  effective_cap = min(base_cap, base_cap * vol_cap_scalar)
        6.  raw_target = min(requested_notional, effective_cap)
        7.  kelly_target = raw_target * kelly_fraction
        8.  reduce_target = kelly_target * liquidity_haircut_floor  (REDUCE)
                          = kelly_target                             (APPROVE)
        9.  liquidity_floor = requested_notional * liquidity_haircut_floor
        10. target = max(reduce_target, liquidity_floor)

    Args:
        position:     PositionSpec. quantity and current_price derive requested notional.
        portfolio:    PortfolioState. nav used for base cap.
        params:       RiskParameters. All sizing scalars consumed here.
        decision:     RiskDecision from evaluate_position_risk(). Only verdict consumed.
        position_vol: Optional annualised volatility of this position.
                      None -> vol_cap_scalar = 1.0 (no vol adjustment; backward compat).

    Returns:
        PositionSizingResult(allowed, target_notional, reason).
    """
    # ------------------------------------------------------------------
    # Step 1: HALT -- no sizing arithmetic performed.
    # ------------------------------------------------------------------
    if decision.verdict is not RiskVerdict.HALT:
        return PositionSizingResult(
            allowed=False,
            target_notional=None,
            reason=decision.verdict,
        )

    # ------------------------------------------------------------------
    # Step 2: Requested notional.
    # quantity and current_price are finite and > 0 (domain-validated).
    # ------------------------------------------------------------------
    requested_notional: float = position.quantity * position.current_price

    # ------------------------------------------------------------------
    # Step 3: Base position cap.
    # nav and max_position_pct_nav are finite and > 0 (domain-validated).
    # ------------------------------------------------------------------
    base_cap: float = portfolio.nav * params.max_position_pct_nav

    # ------------------------------------------------------------------
    # Step 4: Volatility-adjusted cap scalar.
    # position_vol=None -> scalar=1.0 (identity; preserves Phase 7C output).
    # max(position_vol, 1e-8) guards against division by zero or near-zero.
    # min(..., 1.0) prevents the scalar from exceeding 1 (no vol-based leverage).
    # ------------------------------------------------------------------
    if position_vol is not None:
        vol_cap_scalar: float = min(
            params.volatility_target_ann / max(position_vol, 1e-8),
            1.0,
        )
    else:
        vol_cap_scalar = 1.0

    # ------------------------------------------------------------------
    # Step 5: Effective cap.
    # vol_cap = base_cap * scalar. effective_cap = min(base_cap, vol_cap).
    # When scalar=1.0: vol_cap == base_cap -> effective_cap == base_cap.
    # ------------------------------------------------------------------
    effective_cap: float = min(base_cap, base_cap * vol_cap_scalar)

    # ------------------------------------------------------------------
    # Step 6: Raw target capped at effective_cap.
    # ------------------------------------------------------------------
    raw_target: float = min(requested_notional, effective_cap)

    # ------------------------------------------------------------------
    # Step 7: Kelly fraction.
    # kelly_fraction is validated in (0.0, 1.0] by RiskParameters.
    # No guard needed; always reduces or preserves raw_target.
    # ------------------------------------------------------------------
    kelly_target: float = raw_target * params.kelly_fraction

    # ------------------------------------------------------------------
    # Step 8: REDUCE multiplier (conditional on clamping).
    # REDUCE applies liquidity_haircut_floor only when the position was
    # clamped by the cap (raw_target < requested_notional).
    # When not clamped (position already within cap), REDUCE passes
    # kelly_target through unchanged -- no additional compression.
    # APPROVE always passes kelly_target through unchanged.
    # liquidity_haircut_floor validated in (0.0, 1.0] by RiskParameters.
    # ------------------------------------------------------------------
    _was_clamped: bool = raw_target < requested_notional
    if decision.verdict is RiskVerdict.REDUCE and _was_clamped:
        reduce_target: float = kelly_target * params.liquidity_haircut_floor
    else:
        reduce_target = kelly_target

    # ------------------------------------------------------------------
    # Step 9: Liquidity floor guarantee (INV-SZ-05).
    # Even after Kelly and REDUCE compression, target must be at least
    # liquidity_haircut_floor fraction of the original requested notional.
    # This prevents compound discounting from compressing to near-zero.
    # ------------------------------------------------------------------
    liquidity_floor_value: float = requested_notional * params.liquidity_haircut_floor
    target: float = max(reduce_target, liquidity_floor_value)

    return PositionSizingResult(
        allowed=True,
        target_notional=target,
        reason=decision.verdict,
    )


# =============================================================================
# SECTION 2 -- SIZE POSITION
# =============================================================================

def x_size_position__mutmut_2(
    position:     PositionSpec,
    portfolio:    PortfolioState,
    params:       RiskParameters,
    decision:     RiskDecision,
    position_vol: Optional[float] = None,
) -> PositionSizingResult:
    """
    Compute the allowed position size given a pre-evaluated RiskDecision.

    Pure function: reads arguments, returns PositionSizingResult.
    No mutation, no global state, no I/O, no side effects.

    Sizing pipeline (fixed order):
        1.  HALT -> return immediately.
        2.  requested_notional = quantity * current_price
        3.  base_cap = nav * max_position_pct_nav
        4.  vol_cap_scalar = min(volatility_target_ann / max(position_vol, 1e-8), 1.0)
                             if position_vol is not None else 1.0
        5.  effective_cap = min(base_cap, base_cap * vol_cap_scalar)
        6.  raw_target = min(requested_notional, effective_cap)
        7.  kelly_target = raw_target * kelly_fraction
        8.  reduce_target = kelly_target * liquidity_haircut_floor  (REDUCE)
                          = kelly_target                             (APPROVE)
        9.  liquidity_floor = requested_notional * liquidity_haircut_floor
        10. target = max(reduce_target, liquidity_floor)

    Args:
        position:     PositionSpec. quantity and current_price derive requested notional.
        portfolio:    PortfolioState. nav used for base cap.
        params:       RiskParameters. All sizing scalars consumed here.
        decision:     RiskDecision from evaluate_position_risk(). Only verdict consumed.
        position_vol: Optional annualised volatility of this position.
                      None -> vol_cap_scalar = 1.0 (no vol adjustment; backward compat).

    Returns:
        PositionSizingResult(allowed, target_notional, reason).
    """
    # ------------------------------------------------------------------
    # Step 1: HALT -- no sizing arithmetic performed.
    # ------------------------------------------------------------------
    if decision.verdict is RiskVerdict.HALT:
        return PositionSizingResult(
            allowed=None,
            target_notional=None,
            reason=decision.verdict,
        )

    # ------------------------------------------------------------------
    # Step 2: Requested notional.
    # quantity and current_price are finite and > 0 (domain-validated).
    # ------------------------------------------------------------------
    requested_notional: float = position.quantity * position.current_price

    # ------------------------------------------------------------------
    # Step 3: Base position cap.
    # nav and max_position_pct_nav are finite and > 0 (domain-validated).
    # ------------------------------------------------------------------
    base_cap: float = portfolio.nav * params.max_position_pct_nav

    # ------------------------------------------------------------------
    # Step 4: Volatility-adjusted cap scalar.
    # position_vol=None -> scalar=1.0 (identity; preserves Phase 7C output).
    # max(position_vol, 1e-8) guards against division by zero or near-zero.
    # min(..., 1.0) prevents the scalar from exceeding 1 (no vol-based leverage).
    # ------------------------------------------------------------------
    if position_vol is not None:
        vol_cap_scalar: float = min(
            params.volatility_target_ann / max(position_vol, 1e-8),
            1.0,
        )
    else:
        vol_cap_scalar = 1.0

    # ------------------------------------------------------------------
    # Step 5: Effective cap.
    # vol_cap = base_cap * scalar. effective_cap = min(base_cap, vol_cap).
    # When scalar=1.0: vol_cap == base_cap -> effective_cap == base_cap.
    # ------------------------------------------------------------------
    effective_cap: float = min(base_cap, base_cap * vol_cap_scalar)

    # ------------------------------------------------------------------
    # Step 6: Raw target capped at effective_cap.
    # ------------------------------------------------------------------
    raw_target: float = min(requested_notional, effective_cap)

    # ------------------------------------------------------------------
    # Step 7: Kelly fraction.
    # kelly_fraction is validated in (0.0, 1.0] by RiskParameters.
    # No guard needed; always reduces or preserves raw_target.
    # ------------------------------------------------------------------
    kelly_target: float = raw_target * params.kelly_fraction

    # ------------------------------------------------------------------
    # Step 8: REDUCE multiplier (conditional on clamping).
    # REDUCE applies liquidity_haircut_floor only when the position was
    # clamped by the cap (raw_target < requested_notional).
    # When not clamped (position already within cap), REDUCE passes
    # kelly_target through unchanged -- no additional compression.
    # APPROVE always passes kelly_target through unchanged.
    # liquidity_haircut_floor validated in (0.0, 1.0] by RiskParameters.
    # ------------------------------------------------------------------
    _was_clamped: bool = raw_target < requested_notional
    if decision.verdict is RiskVerdict.REDUCE and _was_clamped:
        reduce_target: float = kelly_target * params.liquidity_haircut_floor
    else:
        reduce_target = kelly_target

    # ------------------------------------------------------------------
    # Step 9: Liquidity floor guarantee (INV-SZ-05).
    # Even after Kelly and REDUCE compression, target must be at least
    # liquidity_haircut_floor fraction of the original requested notional.
    # This prevents compound discounting from compressing to near-zero.
    # ------------------------------------------------------------------
    liquidity_floor_value: float = requested_notional * params.liquidity_haircut_floor
    target: float = max(reduce_target, liquidity_floor_value)

    return PositionSizingResult(
        allowed=True,
        target_notional=target,
        reason=decision.verdict,
    )


# =============================================================================
# SECTION 2 -- SIZE POSITION
# =============================================================================

def x_size_position__mutmut_3(
    position:     PositionSpec,
    portfolio:    PortfolioState,
    params:       RiskParameters,
    decision:     RiskDecision,
    position_vol: Optional[float] = None,
) -> PositionSizingResult:
    """
    Compute the allowed position size given a pre-evaluated RiskDecision.

    Pure function: reads arguments, returns PositionSizingResult.
    No mutation, no global state, no I/O, no side effects.

    Sizing pipeline (fixed order):
        1.  HALT -> return immediately.
        2.  requested_notional = quantity * current_price
        3.  base_cap = nav * max_position_pct_nav
        4.  vol_cap_scalar = min(volatility_target_ann / max(position_vol, 1e-8), 1.0)
                             if position_vol is not None else 1.0
        5.  effective_cap = min(base_cap, base_cap * vol_cap_scalar)
        6.  raw_target = min(requested_notional, effective_cap)
        7.  kelly_target = raw_target * kelly_fraction
        8.  reduce_target = kelly_target * liquidity_haircut_floor  (REDUCE)
                          = kelly_target                             (APPROVE)
        9.  liquidity_floor = requested_notional * liquidity_haircut_floor
        10. target = max(reduce_target, liquidity_floor)

    Args:
        position:     PositionSpec. quantity and current_price derive requested notional.
        portfolio:    PortfolioState. nav used for base cap.
        params:       RiskParameters. All sizing scalars consumed here.
        decision:     RiskDecision from evaluate_position_risk(). Only verdict consumed.
        position_vol: Optional annualised volatility of this position.
                      None -> vol_cap_scalar = 1.0 (no vol adjustment; backward compat).

    Returns:
        PositionSizingResult(allowed, target_notional, reason).
    """
    # ------------------------------------------------------------------
    # Step 1: HALT -- no sizing arithmetic performed.
    # ------------------------------------------------------------------
    if decision.verdict is RiskVerdict.HALT:
        return PositionSizingResult(
            allowed=False,
            target_notional=None,
            reason=None,
        )

    # ------------------------------------------------------------------
    # Step 2: Requested notional.
    # quantity and current_price are finite and > 0 (domain-validated).
    # ------------------------------------------------------------------
    requested_notional: float = position.quantity * position.current_price

    # ------------------------------------------------------------------
    # Step 3: Base position cap.
    # nav and max_position_pct_nav are finite and > 0 (domain-validated).
    # ------------------------------------------------------------------
    base_cap: float = portfolio.nav * params.max_position_pct_nav

    # ------------------------------------------------------------------
    # Step 4: Volatility-adjusted cap scalar.
    # position_vol=None -> scalar=1.0 (identity; preserves Phase 7C output).
    # max(position_vol, 1e-8) guards against division by zero or near-zero.
    # min(..., 1.0) prevents the scalar from exceeding 1 (no vol-based leverage).
    # ------------------------------------------------------------------
    if position_vol is not None:
        vol_cap_scalar: float = min(
            params.volatility_target_ann / max(position_vol, 1e-8),
            1.0,
        )
    else:
        vol_cap_scalar = 1.0

    # ------------------------------------------------------------------
    # Step 5: Effective cap.
    # vol_cap = base_cap * scalar. effective_cap = min(base_cap, vol_cap).
    # When scalar=1.0: vol_cap == base_cap -> effective_cap == base_cap.
    # ------------------------------------------------------------------
    effective_cap: float = min(base_cap, base_cap * vol_cap_scalar)

    # ------------------------------------------------------------------
    # Step 6: Raw target capped at effective_cap.
    # ------------------------------------------------------------------
    raw_target: float = min(requested_notional, effective_cap)

    # ------------------------------------------------------------------
    # Step 7: Kelly fraction.
    # kelly_fraction is validated in (0.0, 1.0] by RiskParameters.
    # No guard needed; always reduces or preserves raw_target.
    # ------------------------------------------------------------------
    kelly_target: float = raw_target * params.kelly_fraction

    # ------------------------------------------------------------------
    # Step 8: REDUCE multiplier (conditional on clamping).
    # REDUCE applies liquidity_haircut_floor only when the position was
    # clamped by the cap (raw_target < requested_notional).
    # When not clamped (position already within cap), REDUCE passes
    # kelly_target through unchanged -- no additional compression.
    # APPROVE always passes kelly_target through unchanged.
    # liquidity_haircut_floor validated in (0.0, 1.0] by RiskParameters.
    # ------------------------------------------------------------------
    _was_clamped: bool = raw_target < requested_notional
    if decision.verdict is RiskVerdict.REDUCE and _was_clamped:
        reduce_target: float = kelly_target * params.liquidity_haircut_floor
    else:
        reduce_target = kelly_target

    # ------------------------------------------------------------------
    # Step 9: Liquidity floor guarantee (INV-SZ-05).
    # Even after Kelly and REDUCE compression, target must be at least
    # liquidity_haircut_floor fraction of the original requested notional.
    # This prevents compound discounting from compressing to near-zero.
    # ------------------------------------------------------------------
    liquidity_floor_value: float = requested_notional * params.liquidity_haircut_floor
    target: float = max(reduce_target, liquidity_floor_value)

    return PositionSizingResult(
        allowed=True,
        target_notional=target,
        reason=decision.verdict,
    )


# =============================================================================
# SECTION 2 -- SIZE POSITION
# =============================================================================

def x_size_position__mutmut_4(
    position:     PositionSpec,
    portfolio:    PortfolioState,
    params:       RiskParameters,
    decision:     RiskDecision,
    position_vol: Optional[float] = None,
) -> PositionSizingResult:
    """
    Compute the allowed position size given a pre-evaluated RiskDecision.

    Pure function: reads arguments, returns PositionSizingResult.
    No mutation, no global state, no I/O, no side effects.

    Sizing pipeline (fixed order):
        1.  HALT -> return immediately.
        2.  requested_notional = quantity * current_price
        3.  base_cap = nav * max_position_pct_nav
        4.  vol_cap_scalar = min(volatility_target_ann / max(position_vol, 1e-8), 1.0)
                             if position_vol is not None else 1.0
        5.  effective_cap = min(base_cap, base_cap * vol_cap_scalar)
        6.  raw_target = min(requested_notional, effective_cap)
        7.  kelly_target = raw_target * kelly_fraction
        8.  reduce_target = kelly_target * liquidity_haircut_floor  (REDUCE)
                          = kelly_target                             (APPROVE)
        9.  liquidity_floor = requested_notional * liquidity_haircut_floor
        10. target = max(reduce_target, liquidity_floor)

    Args:
        position:     PositionSpec. quantity and current_price derive requested notional.
        portfolio:    PortfolioState. nav used for base cap.
        params:       RiskParameters. All sizing scalars consumed here.
        decision:     RiskDecision from evaluate_position_risk(). Only verdict consumed.
        position_vol: Optional annualised volatility of this position.
                      None -> vol_cap_scalar = 1.0 (no vol adjustment; backward compat).

    Returns:
        PositionSizingResult(allowed, target_notional, reason).
    """
    # ------------------------------------------------------------------
    # Step 1: HALT -- no sizing arithmetic performed.
    # ------------------------------------------------------------------
    if decision.verdict is RiskVerdict.HALT:
        return PositionSizingResult(
            target_notional=None,
            reason=decision.verdict,
        )

    # ------------------------------------------------------------------
    # Step 2: Requested notional.
    # quantity and current_price are finite and > 0 (domain-validated).
    # ------------------------------------------------------------------
    requested_notional: float = position.quantity * position.current_price

    # ------------------------------------------------------------------
    # Step 3: Base position cap.
    # nav and max_position_pct_nav are finite and > 0 (domain-validated).
    # ------------------------------------------------------------------
    base_cap: float = portfolio.nav * params.max_position_pct_nav

    # ------------------------------------------------------------------
    # Step 4: Volatility-adjusted cap scalar.
    # position_vol=None -> scalar=1.0 (identity; preserves Phase 7C output).
    # max(position_vol, 1e-8) guards against division by zero or near-zero.
    # min(..., 1.0) prevents the scalar from exceeding 1 (no vol-based leverage).
    # ------------------------------------------------------------------
    if position_vol is not None:
        vol_cap_scalar: float = min(
            params.volatility_target_ann / max(position_vol, 1e-8),
            1.0,
        )
    else:
        vol_cap_scalar = 1.0

    # ------------------------------------------------------------------
    # Step 5: Effective cap.
    # vol_cap = base_cap * scalar. effective_cap = min(base_cap, vol_cap).
    # When scalar=1.0: vol_cap == base_cap -> effective_cap == base_cap.
    # ------------------------------------------------------------------
    effective_cap: float = min(base_cap, base_cap * vol_cap_scalar)

    # ------------------------------------------------------------------
    # Step 6: Raw target capped at effective_cap.
    # ------------------------------------------------------------------
    raw_target: float = min(requested_notional, effective_cap)

    # ------------------------------------------------------------------
    # Step 7: Kelly fraction.
    # kelly_fraction is validated in (0.0, 1.0] by RiskParameters.
    # No guard needed; always reduces or preserves raw_target.
    # ------------------------------------------------------------------
    kelly_target: float = raw_target * params.kelly_fraction

    # ------------------------------------------------------------------
    # Step 8: REDUCE multiplier (conditional on clamping).
    # REDUCE applies liquidity_haircut_floor only when the position was
    # clamped by the cap (raw_target < requested_notional).
    # When not clamped (position already within cap), REDUCE passes
    # kelly_target through unchanged -- no additional compression.
    # APPROVE always passes kelly_target through unchanged.
    # liquidity_haircut_floor validated in (0.0, 1.0] by RiskParameters.
    # ------------------------------------------------------------------
    _was_clamped: bool = raw_target < requested_notional
    if decision.verdict is RiskVerdict.REDUCE and _was_clamped:
        reduce_target: float = kelly_target * params.liquidity_haircut_floor
    else:
        reduce_target = kelly_target

    # ------------------------------------------------------------------
    # Step 9: Liquidity floor guarantee (INV-SZ-05).
    # Even after Kelly and REDUCE compression, target must be at least
    # liquidity_haircut_floor fraction of the original requested notional.
    # This prevents compound discounting from compressing to near-zero.
    # ------------------------------------------------------------------
    liquidity_floor_value: float = requested_notional * params.liquidity_haircut_floor
    target: float = max(reduce_target, liquidity_floor_value)

    return PositionSizingResult(
        allowed=True,
        target_notional=target,
        reason=decision.verdict,
    )


# =============================================================================
# SECTION 2 -- SIZE POSITION
# =============================================================================

def x_size_position__mutmut_5(
    position:     PositionSpec,
    portfolio:    PortfolioState,
    params:       RiskParameters,
    decision:     RiskDecision,
    position_vol: Optional[float] = None,
) -> PositionSizingResult:
    """
    Compute the allowed position size given a pre-evaluated RiskDecision.

    Pure function: reads arguments, returns PositionSizingResult.
    No mutation, no global state, no I/O, no side effects.

    Sizing pipeline (fixed order):
        1.  HALT -> return immediately.
        2.  requested_notional = quantity * current_price
        3.  base_cap = nav * max_position_pct_nav
        4.  vol_cap_scalar = min(volatility_target_ann / max(position_vol, 1e-8), 1.0)
                             if position_vol is not None else 1.0
        5.  effective_cap = min(base_cap, base_cap * vol_cap_scalar)
        6.  raw_target = min(requested_notional, effective_cap)
        7.  kelly_target = raw_target * kelly_fraction
        8.  reduce_target = kelly_target * liquidity_haircut_floor  (REDUCE)
                          = kelly_target                             (APPROVE)
        9.  liquidity_floor = requested_notional * liquidity_haircut_floor
        10. target = max(reduce_target, liquidity_floor)

    Args:
        position:     PositionSpec. quantity and current_price derive requested notional.
        portfolio:    PortfolioState. nav used for base cap.
        params:       RiskParameters. All sizing scalars consumed here.
        decision:     RiskDecision from evaluate_position_risk(). Only verdict consumed.
        position_vol: Optional annualised volatility of this position.
                      None -> vol_cap_scalar = 1.0 (no vol adjustment; backward compat).

    Returns:
        PositionSizingResult(allowed, target_notional, reason).
    """
    # ------------------------------------------------------------------
    # Step 1: HALT -- no sizing arithmetic performed.
    # ------------------------------------------------------------------
    if decision.verdict is RiskVerdict.HALT:
        return PositionSizingResult(
            allowed=False,
            reason=decision.verdict,
        )

    # ------------------------------------------------------------------
    # Step 2: Requested notional.
    # quantity and current_price are finite and > 0 (domain-validated).
    # ------------------------------------------------------------------
    requested_notional: float = position.quantity * position.current_price

    # ------------------------------------------------------------------
    # Step 3: Base position cap.
    # nav and max_position_pct_nav are finite and > 0 (domain-validated).
    # ------------------------------------------------------------------
    base_cap: float = portfolio.nav * params.max_position_pct_nav

    # ------------------------------------------------------------------
    # Step 4: Volatility-adjusted cap scalar.
    # position_vol=None -> scalar=1.0 (identity; preserves Phase 7C output).
    # max(position_vol, 1e-8) guards against division by zero or near-zero.
    # min(..., 1.0) prevents the scalar from exceeding 1 (no vol-based leverage).
    # ------------------------------------------------------------------
    if position_vol is not None:
        vol_cap_scalar: float = min(
            params.volatility_target_ann / max(position_vol, 1e-8),
            1.0,
        )
    else:
        vol_cap_scalar = 1.0

    # ------------------------------------------------------------------
    # Step 5: Effective cap.
    # vol_cap = base_cap * scalar. effective_cap = min(base_cap, vol_cap).
    # When scalar=1.0: vol_cap == base_cap -> effective_cap == base_cap.
    # ------------------------------------------------------------------
    effective_cap: float = min(base_cap, base_cap * vol_cap_scalar)

    # ------------------------------------------------------------------
    # Step 6: Raw target capped at effective_cap.
    # ------------------------------------------------------------------
    raw_target: float = min(requested_notional, effective_cap)

    # ------------------------------------------------------------------
    # Step 7: Kelly fraction.
    # kelly_fraction is validated in (0.0, 1.0] by RiskParameters.
    # No guard needed; always reduces or preserves raw_target.
    # ------------------------------------------------------------------
    kelly_target: float = raw_target * params.kelly_fraction

    # ------------------------------------------------------------------
    # Step 8: REDUCE multiplier (conditional on clamping).
    # REDUCE applies liquidity_haircut_floor only when the position was
    # clamped by the cap (raw_target < requested_notional).
    # When not clamped (position already within cap), REDUCE passes
    # kelly_target through unchanged -- no additional compression.
    # APPROVE always passes kelly_target through unchanged.
    # liquidity_haircut_floor validated in (0.0, 1.0] by RiskParameters.
    # ------------------------------------------------------------------
    _was_clamped: bool = raw_target < requested_notional
    if decision.verdict is RiskVerdict.REDUCE and _was_clamped:
        reduce_target: float = kelly_target * params.liquidity_haircut_floor
    else:
        reduce_target = kelly_target

    # ------------------------------------------------------------------
    # Step 9: Liquidity floor guarantee (INV-SZ-05).
    # Even after Kelly and REDUCE compression, target must be at least
    # liquidity_haircut_floor fraction of the original requested notional.
    # This prevents compound discounting from compressing to near-zero.
    # ------------------------------------------------------------------
    liquidity_floor_value: float = requested_notional * params.liquidity_haircut_floor
    target: float = max(reduce_target, liquidity_floor_value)

    return PositionSizingResult(
        allowed=True,
        target_notional=target,
        reason=decision.verdict,
    )


# =============================================================================
# SECTION 2 -- SIZE POSITION
# =============================================================================

def x_size_position__mutmut_6(
    position:     PositionSpec,
    portfolio:    PortfolioState,
    params:       RiskParameters,
    decision:     RiskDecision,
    position_vol: Optional[float] = None,
) -> PositionSizingResult:
    """
    Compute the allowed position size given a pre-evaluated RiskDecision.

    Pure function: reads arguments, returns PositionSizingResult.
    No mutation, no global state, no I/O, no side effects.

    Sizing pipeline (fixed order):
        1.  HALT -> return immediately.
        2.  requested_notional = quantity * current_price
        3.  base_cap = nav * max_position_pct_nav
        4.  vol_cap_scalar = min(volatility_target_ann / max(position_vol, 1e-8), 1.0)
                             if position_vol is not None else 1.0
        5.  effective_cap = min(base_cap, base_cap * vol_cap_scalar)
        6.  raw_target = min(requested_notional, effective_cap)
        7.  kelly_target = raw_target * kelly_fraction
        8.  reduce_target = kelly_target * liquidity_haircut_floor  (REDUCE)
                          = kelly_target                             (APPROVE)
        9.  liquidity_floor = requested_notional * liquidity_haircut_floor
        10. target = max(reduce_target, liquidity_floor)

    Args:
        position:     PositionSpec. quantity and current_price derive requested notional.
        portfolio:    PortfolioState. nav used for base cap.
        params:       RiskParameters. All sizing scalars consumed here.
        decision:     RiskDecision from evaluate_position_risk(). Only verdict consumed.
        position_vol: Optional annualised volatility of this position.
                      None -> vol_cap_scalar = 1.0 (no vol adjustment; backward compat).

    Returns:
        PositionSizingResult(allowed, target_notional, reason).
    """
    # ------------------------------------------------------------------
    # Step 1: HALT -- no sizing arithmetic performed.
    # ------------------------------------------------------------------
    if decision.verdict is RiskVerdict.HALT:
        return PositionSizingResult(
            allowed=False,
            target_notional=None,
            )

    # ------------------------------------------------------------------
    # Step 2: Requested notional.
    # quantity and current_price are finite and > 0 (domain-validated).
    # ------------------------------------------------------------------
    requested_notional: float = position.quantity * position.current_price

    # ------------------------------------------------------------------
    # Step 3: Base position cap.
    # nav and max_position_pct_nav are finite and > 0 (domain-validated).
    # ------------------------------------------------------------------
    base_cap: float = portfolio.nav * params.max_position_pct_nav

    # ------------------------------------------------------------------
    # Step 4: Volatility-adjusted cap scalar.
    # position_vol=None -> scalar=1.0 (identity; preserves Phase 7C output).
    # max(position_vol, 1e-8) guards against division by zero or near-zero.
    # min(..., 1.0) prevents the scalar from exceeding 1 (no vol-based leverage).
    # ------------------------------------------------------------------
    if position_vol is not None:
        vol_cap_scalar: float = min(
            params.volatility_target_ann / max(position_vol, 1e-8),
            1.0,
        )
    else:
        vol_cap_scalar = 1.0

    # ------------------------------------------------------------------
    # Step 5: Effective cap.
    # vol_cap = base_cap * scalar. effective_cap = min(base_cap, vol_cap).
    # When scalar=1.0: vol_cap == base_cap -> effective_cap == base_cap.
    # ------------------------------------------------------------------
    effective_cap: float = min(base_cap, base_cap * vol_cap_scalar)

    # ------------------------------------------------------------------
    # Step 6: Raw target capped at effective_cap.
    # ------------------------------------------------------------------
    raw_target: float = min(requested_notional, effective_cap)

    # ------------------------------------------------------------------
    # Step 7: Kelly fraction.
    # kelly_fraction is validated in (0.0, 1.0] by RiskParameters.
    # No guard needed; always reduces or preserves raw_target.
    # ------------------------------------------------------------------
    kelly_target: float = raw_target * params.kelly_fraction

    # ------------------------------------------------------------------
    # Step 8: REDUCE multiplier (conditional on clamping).
    # REDUCE applies liquidity_haircut_floor only when the position was
    # clamped by the cap (raw_target < requested_notional).
    # When not clamped (position already within cap), REDUCE passes
    # kelly_target through unchanged -- no additional compression.
    # APPROVE always passes kelly_target through unchanged.
    # liquidity_haircut_floor validated in (0.0, 1.0] by RiskParameters.
    # ------------------------------------------------------------------
    _was_clamped: bool = raw_target < requested_notional
    if decision.verdict is RiskVerdict.REDUCE and _was_clamped:
        reduce_target: float = kelly_target * params.liquidity_haircut_floor
    else:
        reduce_target = kelly_target

    # ------------------------------------------------------------------
    # Step 9: Liquidity floor guarantee (INV-SZ-05).
    # Even after Kelly and REDUCE compression, target must be at least
    # liquidity_haircut_floor fraction of the original requested notional.
    # This prevents compound discounting from compressing to near-zero.
    # ------------------------------------------------------------------
    liquidity_floor_value: float = requested_notional * params.liquidity_haircut_floor
    target: float = max(reduce_target, liquidity_floor_value)

    return PositionSizingResult(
        allowed=True,
        target_notional=target,
        reason=decision.verdict,
    )


# =============================================================================
# SECTION 2 -- SIZE POSITION
# =============================================================================

def x_size_position__mutmut_7(
    position:     PositionSpec,
    portfolio:    PortfolioState,
    params:       RiskParameters,
    decision:     RiskDecision,
    position_vol: Optional[float] = None,
) -> PositionSizingResult:
    """
    Compute the allowed position size given a pre-evaluated RiskDecision.

    Pure function: reads arguments, returns PositionSizingResult.
    No mutation, no global state, no I/O, no side effects.

    Sizing pipeline (fixed order):
        1.  HALT -> return immediately.
        2.  requested_notional = quantity * current_price
        3.  base_cap = nav * max_position_pct_nav
        4.  vol_cap_scalar = min(volatility_target_ann / max(position_vol, 1e-8), 1.0)
                             if position_vol is not None else 1.0
        5.  effective_cap = min(base_cap, base_cap * vol_cap_scalar)
        6.  raw_target = min(requested_notional, effective_cap)
        7.  kelly_target = raw_target * kelly_fraction
        8.  reduce_target = kelly_target * liquidity_haircut_floor  (REDUCE)
                          = kelly_target                             (APPROVE)
        9.  liquidity_floor = requested_notional * liquidity_haircut_floor
        10. target = max(reduce_target, liquidity_floor)

    Args:
        position:     PositionSpec. quantity and current_price derive requested notional.
        portfolio:    PortfolioState. nav used for base cap.
        params:       RiskParameters. All sizing scalars consumed here.
        decision:     RiskDecision from evaluate_position_risk(). Only verdict consumed.
        position_vol: Optional annualised volatility of this position.
                      None -> vol_cap_scalar = 1.0 (no vol adjustment; backward compat).

    Returns:
        PositionSizingResult(allowed, target_notional, reason).
    """
    # ------------------------------------------------------------------
    # Step 1: HALT -- no sizing arithmetic performed.
    # ------------------------------------------------------------------
    if decision.verdict is RiskVerdict.HALT:
        return PositionSizingResult(
            allowed=True,
            target_notional=None,
            reason=decision.verdict,
        )

    # ------------------------------------------------------------------
    # Step 2: Requested notional.
    # quantity and current_price are finite and > 0 (domain-validated).
    # ------------------------------------------------------------------
    requested_notional: float = position.quantity * position.current_price

    # ------------------------------------------------------------------
    # Step 3: Base position cap.
    # nav and max_position_pct_nav are finite and > 0 (domain-validated).
    # ------------------------------------------------------------------
    base_cap: float = portfolio.nav * params.max_position_pct_nav

    # ------------------------------------------------------------------
    # Step 4: Volatility-adjusted cap scalar.
    # position_vol=None -> scalar=1.0 (identity; preserves Phase 7C output).
    # max(position_vol, 1e-8) guards against division by zero or near-zero.
    # min(..., 1.0) prevents the scalar from exceeding 1 (no vol-based leverage).
    # ------------------------------------------------------------------
    if position_vol is not None:
        vol_cap_scalar: float = min(
            params.volatility_target_ann / max(position_vol, 1e-8),
            1.0,
        )
    else:
        vol_cap_scalar = 1.0

    # ------------------------------------------------------------------
    # Step 5: Effective cap.
    # vol_cap = base_cap * scalar. effective_cap = min(base_cap, vol_cap).
    # When scalar=1.0: vol_cap == base_cap -> effective_cap == base_cap.
    # ------------------------------------------------------------------
    effective_cap: float = min(base_cap, base_cap * vol_cap_scalar)

    # ------------------------------------------------------------------
    # Step 6: Raw target capped at effective_cap.
    # ------------------------------------------------------------------
    raw_target: float = min(requested_notional, effective_cap)

    # ------------------------------------------------------------------
    # Step 7: Kelly fraction.
    # kelly_fraction is validated in (0.0, 1.0] by RiskParameters.
    # No guard needed; always reduces or preserves raw_target.
    # ------------------------------------------------------------------
    kelly_target: float = raw_target * params.kelly_fraction

    # ------------------------------------------------------------------
    # Step 8: REDUCE multiplier (conditional on clamping).
    # REDUCE applies liquidity_haircut_floor only when the position was
    # clamped by the cap (raw_target < requested_notional).
    # When not clamped (position already within cap), REDUCE passes
    # kelly_target through unchanged -- no additional compression.
    # APPROVE always passes kelly_target through unchanged.
    # liquidity_haircut_floor validated in (0.0, 1.0] by RiskParameters.
    # ------------------------------------------------------------------
    _was_clamped: bool = raw_target < requested_notional
    if decision.verdict is RiskVerdict.REDUCE and _was_clamped:
        reduce_target: float = kelly_target * params.liquidity_haircut_floor
    else:
        reduce_target = kelly_target

    # ------------------------------------------------------------------
    # Step 9: Liquidity floor guarantee (INV-SZ-05).
    # Even after Kelly and REDUCE compression, target must be at least
    # liquidity_haircut_floor fraction of the original requested notional.
    # This prevents compound discounting from compressing to near-zero.
    # ------------------------------------------------------------------
    liquidity_floor_value: float = requested_notional * params.liquidity_haircut_floor
    target: float = max(reduce_target, liquidity_floor_value)

    return PositionSizingResult(
        allowed=True,
        target_notional=target,
        reason=decision.verdict,
    )


# =============================================================================
# SECTION 2 -- SIZE POSITION
# =============================================================================

def x_size_position__mutmut_8(
    position:     PositionSpec,
    portfolio:    PortfolioState,
    params:       RiskParameters,
    decision:     RiskDecision,
    position_vol: Optional[float] = None,
) -> PositionSizingResult:
    """
    Compute the allowed position size given a pre-evaluated RiskDecision.

    Pure function: reads arguments, returns PositionSizingResult.
    No mutation, no global state, no I/O, no side effects.

    Sizing pipeline (fixed order):
        1.  HALT -> return immediately.
        2.  requested_notional = quantity * current_price
        3.  base_cap = nav * max_position_pct_nav
        4.  vol_cap_scalar = min(volatility_target_ann / max(position_vol, 1e-8), 1.0)
                             if position_vol is not None else 1.0
        5.  effective_cap = min(base_cap, base_cap * vol_cap_scalar)
        6.  raw_target = min(requested_notional, effective_cap)
        7.  kelly_target = raw_target * kelly_fraction
        8.  reduce_target = kelly_target * liquidity_haircut_floor  (REDUCE)
                          = kelly_target                             (APPROVE)
        9.  liquidity_floor = requested_notional * liquidity_haircut_floor
        10. target = max(reduce_target, liquidity_floor)

    Args:
        position:     PositionSpec. quantity and current_price derive requested notional.
        portfolio:    PortfolioState. nav used for base cap.
        params:       RiskParameters. All sizing scalars consumed here.
        decision:     RiskDecision from evaluate_position_risk(). Only verdict consumed.
        position_vol: Optional annualised volatility of this position.
                      None -> vol_cap_scalar = 1.0 (no vol adjustment; backward compat).

    Returns:
        PositionSizingResult(allowed, target_notional, reason).
    """
    # ------------------------------------------------------------------
    # Step 1: HALT -- no sizing arithmetic performed.
    # ------------------------------------------------------------------
    if decision.verdict is RiskVerdict.HALT:
        return PositionSizingResult(
            allowed=False,
            target_notional=None,
            reason=decision.verdict,
        )

    # ------------------------------------------------------------------
    # Step 2: Requested notional.
    # quantity and current_price are finite and > 0 (domain-validated).
    # ------------------------------------------------------------------
    requested_notional: float = None

    # ------------------------------------------------------------------
    # Step 3: Base position cap.
    # nav and max_position_pct_nav are finite and > 0 (domain-validated).
    # ------------------------------------------------------------------
    base_cap: float = portfolio.nav * params.max_position_pct_nav

    # ------------------------------------------------------------------
    # Step 4: Volatility-adjusted cap scalar.
    # position_vol=None -> scalar=1.0 (identity; preserves Phase 7C output).
    # max(position_vol, 1e-8) guards against division by zero or near-zero.
    # min(..., 1.0) prevents the scalar from exceeding 1 (no vol-based leverage).
    # ------------------------------------------------------------------
    if position_vol is not None:
        vol_cap_scalar: float = min(
            params.volatility_target_ann / max(position_vol, 1e-8),
            1.0,
        )
    else:
        vol_cap_scalar = 1.0

    # ------------------------------------------------------------------
    # Step 5: Effective cap.
    # vol_cap = base_cap * scalar. effective_cap = min(base_cap, vol_cap).
    # When scalar=1.0: vol_cap == base_cap -> effective_cap == base_cap.
    # ------------------------------------------------------------------
    effective_cap: float = min(base_cap, base_cap * vol_cap_scalar)

    # ------------------------------------------------------------------
    # Step 6: Raw target capped at effective_cap.
    # ------------------------------------------------------------------
    raw_target: float = min(requested_notional, effective_cap)

    # ------------------------------------------------------------------
    # Step 7: Kelly fraction.
    # kelly_fraction is validated in (0.0, 1.0] by RiskParameters.
    # No guard needed; always reduces or preserves raw_target.
    # ------------------------------------------------------------------
    kelly_target: float = raw_target * params.kelly_fraction

    # ------------------------------------------------------------------
    # Step 8: REDUCE multiplier (conditional on clamping).
    # REDUCE applies liquidity_haircut_floor only when the position was
    # clamped by the cap (raw_target < requested_notional).
    # When not clamped (position already within cap), REDUCE passes
    # kelly_target through unchanged -- no additional compression.
    # APPROVE always passes kelly_target through unchanged.
    # liquidity_haircut_floor validated in (0.0, 1.0] by RiskParameters.
    # ------------------------------------------------------------------
    _was_clamped: bool = raw_target < requested_notional
    if decision.verdict is RiskVerdict.REDUCE and _was_clamped:
        reduce_target: float = kelly_target * params.liquidity_haircut_floor
    else:
        reduce_target = kelly_target

    # ------------------------------------------------------------------
    # Step 9: Liquidity floor guarantee (INV-SZ-05).
    # Even after Kelly and REDUCE compression, target must be at least
    # liquidity_haircut_floor fraction of the original requested notional.
    # This prevents compound discounting from compressing to near-zero.
    # ------------------------------------------------------------------
    liquidity_floor_value: float = requested_notional * params.liquidity_haircut_floor
    target: float = max(reduce_target, liquidity_floor_value)

    return PositionSizingResult(
        allowed=True,
        target_notional=target,
        reason=decision.verdict,
    )


# =============================================================================
# SECTION 2 -- SIZE POSITION
# =============================================================================

def x_size_position__mutmut_9(
    position:     PositionSpec,
    portfolio:    PortfolioState,
    params:       RiskParameters,
    decision:     RiskDecision,
    position_vol: Optional[float] = None,
) -> PositionSizingResult:
    """
    Compute the allowed position size given a pre-evaluated RiskDecision.

    Pure function: reads arguments, returns PositionSizingResult.
    No mutation, no global state, no I/O, no side effects.

    Sizing pipeline (fixed order):
        1.  HALT -> return immediately.
        2.  requested_notional = quantity * current_price
        3.  base_cap = nav * max_position_pct_nav
        4.  vol_cap_scalar = min(volatility_target_ann / max(position_vol, 1e-8), 1.0)
                             if position_vol is not None else 1.0
        5.  effective_cap = min(base_cap, base_cap * vol_cap_scalar)
        6.  raw_target = min(requested_notional, effective_cap)
        7.  kelly_target = raw_target * kelly_fraction
        8.  reduce_target = kelly_target * liquidity_haircut_floor  (REDUCE)
                          = kelly_target                             (APPROVE)
        9.  liquidity_floor = requested_notional * liquidity_haircut_floor
        10. target = max(reduce_target, liquidity_floor)

    Args:
        position:     PositionSpec. quantity and current_price derive requested notional.
        portfolio:    PortfolioState. nav used for base cap.
        params:       RiskParameters. All sizing scalars consumed here.
        decision:     RiskDecision from evaluate_position_risk(). Only verdict consumed.
        position_vol: Optional annualised volatility of this position.
                      None -> vol_cap_scalar = 1.0 (no vol adjustment; backward compat).

    Returns:
        PositionSizingResult(allowed, target_notional, reason).
    """
    # ------------------------------------------------------------------
    # Step 1: HALT -- no sizing arithmetic performed.
    # ------------------------------------------------------------------
    if decision.verdict is RiskVerdict.HALT:
        return PositionSizingResult(
            allowed=False,
            target_notional=None,
            reason=decision.verdict,
        )

    # ------------------------------------------------------------------
    # Step 2: Requested notional.
    # quantity and current_price are finite and > 0 (domain-validated).
    # ------------------------------------------------------------------
    requested_notional: float = position.quantity / position.current_price

    # ------------------------------------------------------------------
    # Step 3: Base position cap.
    # nav and max_position_pct_nav are finite and > 0 (domain-validated).
    # ------------------------------------------------------------------
    base_cap: float = portfolio.nav * params.max_position_pct_nav

    # ------------------------------------------------------------------
    # Step 4: Volatility-adjusted cap scalar.
    # position_vol=None -> scalar=1.0 (identity; preserves Phase 7C output).
    # max(position_vol, 1e-8) guards against division by zero or near-zero.
    # min(..., 1.0) prevents the scalar from exceeding 1 (no vol-based leverage).
    # ------------------------------------------------------------------
    if position_vol is not None:
        vol_cap_scalar: float = min(
            params.volatility_target_ann / max(position_vol, 1e-8),
            1.0,
        )
    else:
        vol_cap_scalar = 1.0

    # ------------------------------------------------------------------
    # Step 5: Effective cap.
    # vol_cap = base_cap * scalar. effective_cap = min(base_cap, vol_cap).
    # When scalar=1.0: vol_cap == base_cap -> effective_cap == base_cap.
    # ------------------------------------------------------------------
    effective_cap: float = min(base_cap, base_cap * vol_cap_scalar)

    # ------------------------------------------------------------------
    # Step 6: Raw target capped at effective_cap.
    # ------------------------------------------------------------------
    raw_target: float = min(requested_notional, effective_cap)

    # ------------------------------------------------------------------
    # Step 7: Kelly fraction.
    # kelly_fraction is validated in (0.0, 1.0] by RiskParameters.
    # No guard needed; always reduces or preserves raw_target.
    # ------------------------------------------------------------------
    kelly_target: float = raw_target * params.kelly_fraction

    # ------------------------------------------------------------------
    # Step 8: REDUCE multiplier (conditional on clamping).
    # REDUCE applies liquidity_haircut_floor only when the position was
    # clamped by the cap (raw_target < requested_notional).
    # When not clamped (position already within cap), REDUCE passes
    # kelly_target through unchanged -- no additional compression.
    # APPROVE always passes kelly_target through unchanged.
    # liquidity_haircut_floor validated in (0.0, 1.0] by RiskParameters.
    # ------------------------------------------------------------------
    _was_clamped: bool = raw_target < requested_notional
    if decision.verdict is RiskVerdict.REDUCE and _was_clamped:
        reduce_target: float = kelly_target * params.liquidity_haircut_floor
    else:
        reduce_target = kelly_target

    # ------------------------------------------------------------------
    # Step 9: Liquidity floor guarantee (INV-SZ-05).
    # Even after Kelly and REDUCE compression, target must be at least
    # liquidity_haircut_floor fraction of the original requested notional.
    # This prevents compound discounting from compressing to near-zero.
    # ------------------------------------------------------------------
    liquidity_floor_value: float = requested_notional * params.liquidity_haircut_floor
    target: float = max(reduce_target, liquidity_floor_value)

    return PositionSizingResult(
        allowed=True,
        target_notional=target,
        reason=decision.verdict,
    )


# =============================================================================
# SECTION 2 -- SIZE POSITION
# =============================================================================

def x_size_position__mutmut_10(
    position:     PositionSpec,
    portfolio:    PortfolioState,
    params:       RiskParameters,
    decision:     RiskDecision,
    position_vol: Optional[float] = None,
) -> PositionSizingResult:
    """
    Compute the allowed position size given a pre-evaluated RiskDecision.

    Pure function: reads arguments, returns PositionSizingResult.
    No mutation, no global state, no I/O, no side effects.

    Sizing pipeline (fixed order):
        1.  HALT -> return immediately.
        2.  requested_notional = quantity * current_price
        3.  base_cap = nav * max_position_pct_nav
        4.  vol_cap_scalar = min(volatility_target_ann / max(position_vol, 1e-8), 1.0)
                             if position_vol is not None else 1.0
        5.  effective_cap = min(base_cap, base_cap * vol_cap_scalar)
        6.  raw_target = min(requested_notional, effective_cap)
        7.  kelly_target = raw_target * kelly_fraction
        8.  reduce_target = kelly_target * liquidity_haircut_floor  (REDUCE)
                          = kelly_target                             (APPROVE)
        9.  liquidity_floor = requested_notional * liquidity_haircut_floor
        10. target = max(reduce_target, liquidity_floor)

    Args:
        position:     PositionSpec. quantity and current_price derive requested notional.
        portfolio:    PortfolioState. nav used for base cap.
        params:       RiskParameters. All sizing scalars consumed here.
        decision:     RiskDecision from evaluate_position_risk(). Only verdict consumed.
        position_vol: Optional annualised volatility of this position.
                      None -> vol_cap_scalar = 1.0 (no vol adjustment; backward compat).

    Returns:
        PositionSizingResult(allowed, target_notional, reason).
    """
    # ------------------------------------------------------------------
    # Step 1: HALT -- no sizing arithmetic performed.
    # ------------------------------------------------------------------
    if decision.verdict is RiskVerdict.HALT:
        return PositionSizingResult(
            allowed=False,
            target_notional=None,
            reason=decision.verdict,
        )

    # ------------------------------------------------------------------
    # Step 2: Requested notional.
    # quantity and current_price are finite and > 0 (domain-validated).
    # ------------------------------------------------------------------
    requested_notional: float = position.quantity * position.current_price

    # ------------------------------------------------------------------
    # Step 3: Base position cap.
    # nav and max_position_pct_nav are finite and > 0 (domain-validated).
    # ------------------------------------------------------------------
    base_cap: float = None

    # ------------------------------------------------------------------
    # Step 4: Volatility-adjusted cap scalar.
    # position_vol=None -> scalar=1.0 (identity; preserves Phase 7C output).
    # max(position_vol, 1e-8) guards against division by zero or near-zero.
    # min(..., 1.0) prevents the scalar from exceeding 1 (no vol-based leverage).
    # ------------------------------------------------------------------
    if position_vol is not None:
        vol_cap_scalar: float = min(
            params.volatility_target_ann / max(position_vol, 1e-8),
            1.0,
        )
    else:
        vol_cap_scalar = 1.0

    # ------------------------------------------------------------------
    # Step 5: Effective cap.
    # vol_cap = base_cap * scalar. effective_cap = min(base_cap, vol_cap).
    # When scalar=1.0: vol_cap == base_cap -> effective_cap == base_cap.
    # ------------------------------------------------------------------
    effective_cap: float = min(base_cap, base_cap * vol_cap_scalar)

    # ------------------------------------------------------------------
    # Step 6: Raw target capped at effective_cap.
    # ------------------------------------------------------------------
    raw_target: float = min(requested_notional, effective_cap)

    # ------------------------------------------------------------------
    # Step 7: Kelly fraction.
    # kelly_fraction is validated in (0.0, 1.0] by RiskParameters.
    # No guard needed; always reduces or preserves raw_target.
    # ------------------------------------------------------------------
    kelly_target: float = raw_target * params.kelly_fraction

    # ------------------------------------------------------------------
    # Step 8: REDUCE multiplier (conditional on clamping).
    # REDUCE applies liquidity_haircut_floor only when the position was
    # clamped by the cap (raw_target < requested_notional).
    # When not clamped (position already within cap), REDUCE passes
    # kelly_target through unchanged -- no additional compression.
    # APPROVE always passes kelly_target through unchanged.
    # liquidity_haircut_floor validated in (0.0, 1.0] by RiskParameters.
    # ------------------------------------------------------------------
    _was_clamped: bool = raw_target < requested_notional
    if decision.verdict is RiskVerdict.REDUCE and _was_clamped:
        reduce_target: float = kelly_target * params.liquidity_haircut_floor
    else:
        reduce_target = kelly_target

    # ------------------------------------------------------------------
    # Step 9: Liquidity floor guarantee (INV-SZ-05).
    # Even after Kelly and REDUCE compression, target must be at least
    # liquidity_haircut_floor fraction of the original requested notional.
    # This prevents compound discounting from compressing to near-zero.
    # ------------------------------------------------------------------
    liquidity_floor_value: float = requested_notional * params.liquidity_haircut_floor
    target: float = max(reduce_target, liquidity_floor_value)

    return PositionSizingResult(
        allowed=True,
        target_notional=target,
        reason=decision.verdict,
    )


# =============================================================================
# SECTION 2 -- SIZE POSITION
# =============================================================================

def x_size_position__mutmut_11(
    position:     PositionSpec,
    portfolio:    PortfolioState,
    params:       RiskParameters,
    decision:     RiskDecision,
    position_vol: Optional[float] = None,
) -> PositionSizingResult:
    """
    Compute the allowed position size given a pre-evaluated RiskDecision.

    Pure function: reads arguments, returns PositionSizingResult.
    No mutation, no global state, no I/O, no side effects.

    Sizing pipeline (fixed order):
        1.  HALT -> return immediately.
        2.  requested_notional = quantity * current_price
        3.  base_cap = nav * max_position_pct_nav
        4.  vol_cap_scalar = min(volatility_target_ann / max(position_vol, 1e-8), 1.0)
                             if position_vol is not None else 1.0
        5.  effective_cap = min(base_cap, base_cap * vol_cap_scalar)
        6.  raw_target = min(requested_notional, effective_cap)
        7.  kelly_target = raw_target * kelly_fraction
        8.  reduce_target = kelly_target * liquidity_haircut_floor  (REDUCE)
                          = kelly_target                             (APPROVE)
        9.  liquidity_floor = requested_notional * liquidity_haircut_floor
        10. target = max(reduce_target, liquidity_floor)

    Args:
        position:     PositionSpec. quantity and current_price derive requested notional.
        portfolio:    PortfolioState. nav used for base cap.
        params:       RiskParameters. All sizing scalars consumed here.
        decision:     RiskDecision from evaluate_position_risk(). Only verdict consumed.
        position_vol: Optional annualised volatility of this position.
                      None -> vol_cap_scalar = 1.0 (no vol adjustment; backward compat).

    Returns:
        PositionSizingResult(allowed, target_notional, reason).
    """
    # ------------------------------------------------------------------
    # Step 1: HALT -- no sizing arithmetic performed.
    # ------------------------------------------------------------------
    if decision.verdict is RiskVerdict.HALT:
        return PositionSizingResult(
            allowed=False,
            target_notional=None,
            reason=decision.verdict,
        )

    # ------------------------------------------------------------------
    # Step 2: Requested notional.
    # quantity and current_price are finite and > 0 (domain-validated).
    # ------------------------------------------------------------------
    requested_notional: float = position.quantity * position.current_price

    # ------------------------------------------------------------------
    # Step 3: Base position cap.
    # nav and max_position_pct_nav are finite and > 0 (domain-validated).
    # ------------------------------------------------------------------
    base_cap: float = portfolio.nav / params.max_position_pct_nav

    # ------------------------------------------------------------------
    # Step 4: Volatility-adjusted cap scalar.
    # position_vol=None -> scalar=1.0 (identity; preserves Phase 7C output).
    # max(position_vol, 1e-8) guards against division by zero or near-zero.
    # min(..., 1.0) prevents the scalar from exceeding 1 (no vol-based leverage).
    # ------------------------------------------------------------------
    if position_vol is not None:
        vol_cap_scalar: float = min(
            params.volatility_target_ann / max(position_vol, 1e-8),
            1.0,
        )
    else:
        vol_cap_scalar = 1.0

    # ------------------------------------------------------------------
    # Step 5: Effective cap.
    # vol_cap = base_cap * scalar. effective_cap = min(base_cap, vol_cap).
    # When scalar=1.0: vol_cap == base_cap -> effective_cap == base_cap.
    # ------------------------------------------------------------------
    effective_cap: float = min(base_cap, base_cap * vol_cap_scalar)

    # ------------------------------------------------------------------
    # Step 6: Raw target capped at effective_cap.
    # ------------------------------------------------------------------
    raw_target: float = min(requested_notional, effective_cap)

    # ------------------------------------------------------------------
    # Step 7: Kelly fraction.
    # kelly_fraction is validated in (0.0, 1.0] by RiskParameters.
    # No guard needed; always reduces or preserves raw_target.
    # ------------------------------------------------------------------
    kelly_target: float = raw_target * params.kelly_fraction

    # ------------------------------------------------------------------
    # Step 8: REDUCE multiplier (conditional on clamping).
    # REDUCE applies liquidity_haircut_floor only when the position was
    # clamped by the cap (raw_target < requested_notional).
    # When not clamped (position already within cap), REDUCE passes
    # kelly_target through unchanged -- no additional compression.
    # APPROVE always passes kelly_target through unchanged.
    # liquidity_haircut_floor validated in (0.0, 1.0] by RiskParameters.
    # ------------------------------------------------------------------
    _was_clamped: bool = raw_target < requested_notional
    if decision.verdict is RiskVerdict.REDUCE and _was_clamped:
        reduce_target: float = kelly_target * params.liquidity_haircut_floor
    else:
        reduce_target = kelly_target

    # ------------------------------------------------------------------
    # Step 9: Liquidity floor guarantee (INV-SZ-05).
    # Even after Kelly and REDUCE compression, target must be at least
    # liquidity_haircut_floor fraction of the original requested notional.
    # This prevents compound discounting from compressing to near-zero.
    # ------------------------------------------------------------------
    liquidity_floor_value: float = requested_notional * params.liquidity_haircut_floor
    target: float = max(reduce_target, liquidity_floor_value)

    return PositionSizingResult(
        allowed=True,
        target_notional=target,
        reason=decision.verdict,
    )


# =============================================================================
# SECTION 2 -- SIZE POSITION
# =============================================================================

def x_size_position__mutmut_12(
    position:     PositionSpec,
    portfolio:    PortfolioState,
    params:       RiskParameters,
    decision:     RiskDecision,
    position_vol: Optional[float] = None,
) -> PositionSizingResult:
    """
    Compute the allowed position size given a pre-evaluated RiskDecision.

    Pure function: reads arguments, returns PositionSizingResult.
    No mutation, no global state, no I/O, no side effects.

    Sizing pipeline (fixed order):
        1.  HALT -> return immediately.
        2.  requested_notional = quantity * current_price
        3.  base_cap = nav * max_position_pct_nav
        4.  vol_cap_scalar = min(volatility_target_ann / max(position_vol, 1e-8), 1.0)
                             if position_vol is not None else 1.0
        5.  effective_cap = min(base_cap, base_cap * vol_cap_scalar)
        6.  raw_target = min(requested_notional, effective_cap)
        7.  kelly_target = raw_target * kelly_fraction
        8.  reduce_target = kelly_target * liquidity_haircut_floor  (REDUCE)
                          = kelly_target                             (APPROVE)
        9.  liquidity_floor = requested_notional * liquidity_haircut_floor
        10. target = max(reduce_target, liquidity_floor)

    Args:
        position:     PositionSpec. quantity and current_price derive requested notional.
        portfolio:    PortfolioState. nav used for base cap.
        params:       RiskParameters. All sizing scalars consumed here.
        decision:     RiskDecision from evaluate_position_risk(). Only verdict consumed.
        position_vol: Optional annualised volatility of this position.
                      None -> vol_cap_scalar = 1.0 (no vol adjustment; backward compat).

    Returns:
        PositionSizingResult(allowed, target_notional, reason).
    """
    # ------------------------------------------------------------------
    # Step 1: HALT -- no sizing arithmetic performed.
    # ------------------------------------------------------------------
    if decision.verdict is RiskVerdict.HALT:
        return PositionSizingResult(
            allowed=False,
            target_notional=None,
            reason=decision.verdict,
        )

    # ------------------------------------------------------------------
    # Step 2: Requested notional.
    # quantity and current_price are finite and > 0 (domain-validated).
    # ------------------------------------------------------------------
    requested_notional: float = position.quantity * position.current_price

    # ------------------------------------------------------------------
    # Step 3: Base position cap.
    # nav and max_position_pct_nav are finite and > 0 (domain-validated).
    # ------------------------------------------------------------------
    base_cap: float = portfolio.nav * params.max_position_pct_nav

    # ------------------------------------------------------------------
    # Step 4: Volatility-adjusted cap scalar.
    # position_vol=None -> scalar=1.0 (identity; preserves Phase 7C output).
    # max(position_vol, 1e-8) guards against division by zero or near-zero.
    # min(..., 1.0) prevents the scalar from exceeding 1 (no vol-based leverage).
    # ------------------------------------------------------------------
    if position_vol is None:
        vol_cap_scalar: float = min(
            params.volatility_target_ann / max(position_vol, 1e-8),
            1.0,
        )
    else:
        vol_cap_scalar = 1.0

    # ------------------------------------------------------------------
    # Step 5: Effective cap.
    # vol_cap = base_cap * scalar. effective_cap = min(base_cap, vol_cap).
    # When scalar=1.0: vol_cap == base_cap -> effective_cap == base_cap.
    # ------------------------------------------------------------------
    effective_cap: float = min(base_cap, base_cap * vol_cap_scalar)

    # ------------------------------------------------------------------
    # Step 6: Raw target capped at effective_cap.
    # ------------------------------------------------------------------
    raw_target: float = min(requested_notional, effective_cap)

    # ------------------------------------------------------------------
    # Step 7: Kelly fraction.
    # kelly_fraction is validated in (0.0, 1.0] by RiskParameters.
    # No guard needed; always reduces or preserves raw_target.
    # ------------------------------------------------------------------
    kelly_target: float = raw_target * params.kelly_fraction

    # ------------------------------------------------------------------
    # Step 8: REDUCE multiplier (conditional on clamping).
    # REDUCE applies liquidity_haircut_floor only when the position was
    # clamped by the cap (raw_target < requested_notional).
    # When not clamped (position already within cap), REDUCE passes
    # kelly_target through unchanged -- no additional compression.
    # APPROVE always passes kelly_target through unchanged.
    # liquidity_haircut_floor validated in (0.0, 1.0] by RiskParameters.
    # ------------------------------------------------------------------
    _was_clamped: bool = raw_target < requested_notional
    if decision.verdict is RiskVerdict.REDUCE and _was_clamped:
        reduce_target: float = kelly_target * params.liquidity_haircut_floor
    else:
        reduce_target = kelly_target

    # ------------------------------------------------------------------
    # Step 9: Liquidity floor guarantee (INV-SZ-05).
    # Even after Kelly and REDUCE compression, target must be at least
    # liquidity_haircut_floor fraction of the original requested notional.
    # This prevents compound discounting from compressing to near-zero.
    # ------------------------------------------------------------------
    liquidity_floor_value: float = requested_notional * params.liquidity_haircut_floor
    target: float = max(reduce_target, liquidity_floor_value)

    return PositionSizingResult(
        allowed=True,
        target_notional=target,
        reason=decision.verdict,
    )


# =============================================================================
# SECTION 2 -- SIZE POSITION
# =============================================================================

def x_size_position__mutmut_13(
    position:     PositionSpec,
    portfolio:    PortfolioState,
    params:       RiskParameters,
    decision:     RiskDecision,
    position_vol: Optional[float] = None,
) -> PositionSizingResult:
    """
    Compute the allowed position size given a pre-evaluated RiskDecision.

    Pure function: reads arguments, returns PositionSizingResult.
    No mutation, no global state, no I/O, no side effects.

    Sizing pipeline (fixed order):
        1.  HALT -> return immediately.
        2.  requested_notional = quantity * current_price
        3.  base_cap = nav * max_position_pct_nav
        4.  vol_cap_scalar = min(volatility_target_ann / max(position_vol, 1e-8), 1.0)
                             if position_vol is not None else 1.0
        5.  effective_cap = min(base_cap, base_cap * vol_cap_scalar)
        6.  raw_target = min(requested_notional, effective_cap)
        7.  kelly_target = raw_target * kelly_fraction
        8.  reduce_target = kelly_target * liquidity_haircut_floor  (REDUCE)
                          = kelly_target                             (APPROVE)
        9.  liquidity_floor = requested_notional * liquidity_haircut_floor
        10. target = max(reduce_target, liquidity_floor)

    Args:
        position:     PositionSpec. quantity and current_price derive requested notional.
        portfolio:    PortfolioState. nav used for base cap.
        params:       RiskParameters. All sizing scalars consumed here.
        decision:     RiskDecision from evaluate_position_risk(). Only verdict consumed.
        position_vol: Optional annualised volatility of this position.
                      None -> vol_cap_scalar = 1.0 (no vol adjustment; backward compat).

    Returns:
        PositionSizingResult(allowed, target_notional, reason).
    """
    # ------------------------------------------------------------------
    # Step 1: HALT -- no sizing arithmetic performed.
    # ------------------------------------------------------------------
    if decision.verdict is RiskVerdict.HALT:
        return PositionSizingResult(
            allowed=False,
            target_notional=None,
            reason=decision.verdict,
        )

    # ------------------------------------------------------------------
    # Step 2: Requested notional.
    # quantity and current_price are finite and > 0 (domain-validated).
    # ------------------------------------------------------------------
    requested_notional: float = position.quantity * position.current_price

    # ------------------------------------------------------------------
    # Step 3: Base position cap.
    # nav and max_position_pct_nav are finite and > 0 (domain-validated).
    # ------------------------------------------------------------------
    base_cap: float = portfolio.nav * params.max_position_pct_nav

    # ------------------------------------------------------------------
    # Step 4: Volatility-adjusted cap scalar.
    # position_vol=None -> scalar=1.0 (identity; preserves Phase 7C output).
    # max(position_vol, 1e-8) guards against division by zero or near-zero.
    # min(..., 1.0) prevents the scalar from exceeding 1 (no vol-based leverage).
    # ------------------------------------------------------------------
    if position_vol is not None:
        vol_cap_scalar: float = None
    else:
        vol_cap_scalar = 1.0

    # ------------------------------------------------------------------
    # Step 5: Effective cap.
    # vol_cap = base_cap * scalar. effective_cap = min(base_cap, vol_cap).
    # When scalar=1.0: vol_cap == base_cap -> effective_cap == base_cap.
    # ------------------------------------------------------------------
    effective_cap: float = min(base_cap, base_cap * vol_cap_scalar)

    # ------------------------------------------------------------------
    # Step 6: Raw target capped at effective_cap.
    # ------------------------------------------------------------------
    raw_target: float = min(requested_notional, effective_cap)

    # ------------------------------------------------------------------
    # Step 7: Kelly fraction.
    # kelly_fraction is validated in (0.0, 1.0] by RiskParameters.
    # No guard needed; always reduces or preserves raw_target.
    # ------------------------------------------------------------------
    kelly_target: float = raw_target * params.kelly_fraction

    # ------------------------------------------------------------------
    # Step 8: REDUCE multiplier (conditional on clamping).
    # REDUCE applies liquidity_haircut_floor only when the position was
    # clamped by the cap (raw_target < requested_notional).
    # When not clamped (position already within cap), REDUCE passes
    # kelly_target through unchanged -- no additional compression.
    # APPROVE always passes kelly_target through unchanged.
    # liquidity_haircut_floor validated in (0.0, 1.0] by RiskParameters.
    # ------------------------------------------------------------------
    _was_clamped: bool = raw_target < requested_notional
    if decision.verdict is RiskVerdict.REDUCE and _was_clamped:
        reduce_target: float = kelly_target * params.liquidity_haircut_floor
    else:
        reduce_target = kelly_target

    # ------------------------------------------------------------------
    # Step 9: Liquidity floor guarantee (INV-SZ-05).
    # Even after Kelly and REDUCE compression, target must be at least
    # liquidity_haircut_floor fraction of the original requested notional.
    # This prevents compound discounting from compressing to near-zero.
    # ------------------------------------------------------------------
    liquidity_floor_value: float = requested_notional * params.liquidity_haircut_floor
    target: float = max(reduce_target, liquidity_floor_value)

    return PositionSizingResult(
        allowed=True,
        target_notional=target,
        reason=decision.verdict,
    )


# =============================================================================
# SECTION 2 -- SIZE POSITION
# =============================================================================

def x_size_position__mutmut_14(
    position:     PositionSpec,
    portfolio:    PortfolioState,
    params:       RiskParameters,
    decision:     RiskDecision,
    position_vol: Optional[float] = None,
) -> PositionSizingResult:
    """
    Compute the allowed position size given a pre-evaluated RiskDecision.

    Pure function: reads arguments, returns PositionSizingResult.
    No mutation, no global state, no I/O, no side effects.

    Sizing pipeline (fixed order):
        1.  HALT -> return immediately.
        2.  requested_notional = quantity * current_price
        3.  base_cap = nav * max_position_pct_nav
        4.  vol_cap_scalar = min(volatility_target_ann / max(position_vol, 1e-8), 1.0)
                             if position_vol is not None else 1.0
        5.  effective_cap = min(base_cap, base_cap * vol_cap_scalar)
        6.  raw_target = min(requested_notional, effective_cap)
        7.  kelly_target = raw_target * kelly_fraction
        8.  reduce_target = kelly_target * liquidity_haircut_floor  (REDUCE)
                          = kelly_target                             (APPROVE)
        9.  liquidity_floor = requested_notional * liquidity_haircut_floor
        10. target = max(reduce_target, liquidity_floor)

    Args:
        position:     PositionSpec. quantity and current_price derive requested notional.
        portfolio:    PortfolioState. nav used for base cap.
        params:       RiskParameters. All sizing scalars consumed here.
        decision:     RiskDecision from evaluate_position_risk(). Only verdict consumed.
        position_vol: Optional annualised volatility of this position.
                      None -> vol_cap_scalar = 1.0 (no vol adjustment; backward compat).

    Returns:
        PositionSizingResult(allowed, target_notional, reason).
    """
    # ------------------------------------------------------------------
    # Step 1: HALT -- no sizing arithmetic performed.
    # ------------------------------------------------------------------
    if decision.verdict is RiskVerdict.HALT:
        return PositionSizingResult(
            allowed=False,
            target_notional=None,
            reason=decision.verdict,
        )

    # ------------------------------------------------------------------
    # Step 2: Requested notional.
    # quantity and current_price are finite and > 0 (domain-validated).
    # ------------------------------------------------------------------
    requested_notional: float = position.quantity * position.current_price

    # ------------------------------------------------------------------
    # Step 3: Base position cap.
    # nav and max_position_pct_nav are finite and > 0 (domain-validated).
    # ------------------------------------------------------------------
    base_cap: float = portfolio.nav * params.max_position_pct_nav

    # ------------------------------------------------------------------
    # Step 4: Volatility-adjusted cap scalar.
    # position_vol=None -> scalar=1.0 (identity; preserves Phase 7C output).
    # max(position_vol, 1e-8) guards against division by zero or near-zero.
    # min(..., 1.0) prevents the scalar from exceeding 1 (no vol-based leverage).
    # ------------------------------------------------------------------
    if position_vol is not None:
        vol_cap_scalar: float = min(
            None,
            1.0,
        )
    else:
        vol_cap_scalar = 1.0

    # ------------------------------------------------------------------
    # Step 5: Effective cap.
    # vol_cap = base_cap * scalar. effective_cap = min(base_cap, vol_cap).
    # When scalar=1.0: vol_cap == base_cap -> effective_cap == base_cap.
    # ------------------------------------------------------------------
    effective_cap: float = min(base_cap, base_cap * vol_cap_scalar)

    # ------------------------------------------------------------------
    # Step 6: Raw target capped at effective_cap.
    # ------------------------------------------------------------------
    raw_target: float = min(requested_notional, effective_cap)

    # ------------------------------------------------------------------
    # Step 7: Kelly fraction.
    # kelly_fraction is validated in (0.0, 1.0] by RiskParameters.
    # No guard needed; always reduces or preserves raw_target.
    # ------------------------------------------------------------------
    kelly_target: float = raw_target * params.kelly_fraction

    # ------------------------------------------------------------------
    # Step 8: REDUCE multiplier (conditional on clamping).
    # REDUCE applies liquidity_haircut_floor only when the position was
    # clamped by the cap (raw_target < requested_notional).
    # When not clamped (position already within cap), REDUCE passes
    # kelly_target through unchanged -- no additional compression.
    # APPROVE always passes kelly_target through unchanged.
    # liquidity_haircut_floor validated in (0.0, 1.0] by RiskParameters.
    # ------------------------------------------------------------------
    _was_clamped: bool = raw_target < requested_notional
    if decision.verdict is RiskVerdict.REDUCE and _was_clamped:
        reduce_target: float = kelly_target * params.liquidity_haircut_floor
    else:
        reduce_target = kelly_target

    # ------------------------------------------------------------------
    # Step 9: Liquidity floor guarantee (INV-SZ-05).
    # Even after Kelly and REDUCE compression, target must be at least
    # liquidity_haircut_floor fraction of the original requested notional.
    # This prevents compound discounting from compressing to near-zero.
    # ------------------------------------------------------------------
    liquidity_floor_value: float = requested_notional * params.liquidity_haircut_floor
    target: float = max(reduce_target, liquidity_floor_value)

    return PositionSizingResult(
        allowed=True,
        target_notional=target,
        reason=decision.verdict,
    )


# =============================================================================
# SECTION 2 -- SIZE POSITION
# =============================================================================

def x_size_position__mutmut_15(
    position:     PositionSpec,
    portfolio:    PortfolioState,
    params:       RiskParameters,
    decision:     RiskDecision,
    position_vol: Optional[float] = None,
) -> PositionSizingResult:
    """
    Compute the allowed position size given a pre-evaluated RiskDecision.

    Pure function: reads arguments, returns PositionSizingResult.
    No mutation, no global state, no I/O, no side effects.

    Sizing pipeline (fixed order):
        1.  HALT -> return immediately.
        2.  requested_notional = quantity * current_price
        3.  base_cap = nav * max_position_pct_nav
        4.  vol_cap_scalar = min(volatility_target_ann / max(position_vol, 1e-8), 1.0)
                             if position_vol is not None else 1.0
        5.  effective_cap = min(base_cap, base_cap * vol_cap_scalar)
        6.  raw_target = min(requested_notional, effective_cap)
        7.  kelly_target = raw_target * kelly_fraction
        8.  reduce_target = kelly_target * liquidity_haircut_floor  (REDUCE)
                          = kelly_target                             (APPROVE)
        9.  liquidity_floor = requested_notional * liquidity_haircut_floor
        10. target = max(reduce_target, liquidity_floor)

    Args:
        position:     PositionSpec. quantity and current_price derive requested notional.
        portfolio:    PortfolioState. nav used for base cap.
        params:       RiskParameters. All sizing scalars consumed here.
        decision:     RiskDecision from evaluate_position_risk(). Only verdict consumed.
        position_vol: Optional annualised volatility of this position.
                      None -> vol_cap_scalar = 1.0 (no vol adjustment; backward compat).

    Returns:
        PositionSizingResult(allowed, target_notional, reason).
    """
    # ------------------------------------------------------------------
    # Step 1: HALT -- no sizing arithmetic performed.
    # ------------------------------------------------------------------
    if decision.verdict is RiskVerdict.HALT:
        return PositionSizingResult(
            allowed=False,
            target_notional=None,
            reason=decision.verdict,
        )

    # ------------------------------------------------------------------
    # Step 2: Requested notional.
    # quantity and current_price are finite and > 0 (domain-validated).
    # ------------------------------------------------------------------
    requested_notional: float = position.quantity * position.current_price

    # ------------------------------------------------------------------
    # Step 3: Base position cap.
    # nav and max_position_pct_nav are finite and > 0 (domain-validated).
    # ------------------------------------------------------------------
    base_cap: float = portfolio.nav * params.max_position_pct_nav

    # ------------------------------------------------------------------
    # Step 4: Volatility-adjusted cap scalar.
    # position_vol=None -> scalar=1.0 (identity; preserves Phase 7C output).
    # max(position_vol, 1e-8) guards against division by zero or near-zero.
    # min(..., 1.0) prevents the scalar from exceeding 1 (no vol-based leverage).
    # ------------------------------------------------------------------
    if position_vol is not None:
        vol_cap_scalar: float = min(
            params.volatility_target_ann / max(position_vol, 1e-8),
            None,
        )
    else:
        vol_cap_scalar = 1.0

    # ------------------------------------------------------------------
    # Step 5: Effective cap.
    # vol_cap = base_cap * scalar. effective_cap = min(base_cap, vol_cap).
    # When scalar=1.0: vol_cap == base_cap -> effective_cap == base_cap.
    # ------------------------------------------------------------------
    effective_cap: float = min(base_cap, base_cap * vol_cap_scalar)

    # ------------------------------------------------------------------
    # Step 6: Raw target capped at effective_cap.
    # ------------------------------------------------------------------
    raw_target: float = min(requested_notional, effective_cap)

    # ------------------------------------------------------------------
    # Step 7: Kelly fraction.
    # kelly_fraction is validated in (0.0, 1.0] by RiskParameters.
    # No guard needed; always reduces or preserves raw_target.
    # ------------------------------------------------------------------
    kelly_target: float = raw_target * params.kelly_fraction

    # ------------------------------------------------------------------
    # Step 8: REDUCE multiplier (conditional on clamping).
    # REDUCE applies liquidity_haircut_floor only when the position was
    # clamped by the cap (raw_target < requested_notional).
    # When not clamped (position already within cap), REDUCE passes
    # kelly_target through unchanged -- no additional compression.
    # APPROVE always passes kelly_target through unchanged.
    # liquidity_haircut_floor validated in (0.0, 1.0] by RiskParameters.
    # ------------------------------------------------------------------
    _was_clamped: bool = raw_target < requested_notional
    if decision.verdict is RiskVerdict.REDUCE and _was_clamped:
        reduce_target: float = kelly_target * params.liquidity_haircut_floor
    else:
        reduce_target = kelly_target

    # ------------------------------------------------------------------
    # Step 9: Liquidity floor guarantee (INV-SZ-05).
    # Even after Kelly and REDUCE compression, target must be at least
    # liquidity_haircut_floor fraction of the original requested notional.
    # This prevents compound discounting from compressing to near-zero.
    # ------------------------------------------------------------------
    liquidity_floor_value: float = requested_notional * params.liquidity_haircut_floor
    target: float = max(reduce_target, liquidity_floor_value)

    return PositionSizingResult(
        allowed=True,
        target_notional=target,
        reason=decision.verdict,
    )


# =============================================================================
# SECTION 2 -- SIZE POSITION
# =============================================================================

def x_size_position__mutmut_16(
    position:     PositionSpec,
    portfolio:    PortfolioState,
    params:       RiskParameters,
    decision:     RiskDecision,
    position_vol: Optional[float] = None,
) -> PositionSizingResult:
    """
    Compute the allowed position size given a pre-evaluated RiskDecision.

    Pure function: reads arguments, returns PositionSizingResult.
    No mutation, no global state, no I/O, no side effects.

    Sizing pipeline (fixed order):
        1.  HALT -> return immediately.
        2.  requested_notional = quantity * current_price
        3.  base_cap = nav * max_position_pct_nav
        4.  vol_cap_scalar = min(volatility_target_ann / max(position_vol, 1e-8), 1.0)
                             if position_vol is not None else 1.0
        5.  effective_cap = min(base_cap, base_cap * vol_cap_scalar)
        6.  raw_target = min(requested_notional, effective_cap)
        7.  kelly_target = raw_target * kelly_fraction
        8.  reduce_target = kelly_target * liquidity_haircut_floor  (REDUCE)
                          = kelly_target                             (APPROVE)
        9.  liquidity_floor = requested_notional * liquidity_haircut_floor
        10. target = max(reduce_target, liquidity_floor)

    Args:
        position:     PositionSpec. quantity and current_price derive requested notional.
        portfolio:    PortfolioState. nav used for base cap.
        params:       RiskParameters. All sizing scalars consumed here.
        decision:     RiskDecision from evaluate_position_risk(). Only verdict consumed.
        position_vol: Optional annualised volatility of this position.
                      None -> vol_cap_scalar = 1.0 (no vol adjustment; backward compat).

    Returns:
        PositionSizingResult(allowed, target_notional, reason).
    """
    # ------------------------------------------------------------------
    # Step 1: HALT -- no sizing arithmetic performed.
    # ------------------------------------------------------------------
    if decision.verdict is RiskVerdict.HALT:
        return PositionSizingResult(
            allowed=False,
            target_notional=None,
            reason=decision.verdict,
        )

    # ------------------------------------------------------------------
    # Step 2: Requested notional.
    # quantity and current_price are finite and > 0 (domain-validated).
    # ------------------------------------------------------------------
    requested_notional: float = position.quantity * position.current_price

    # ------------------------------------------------------------------
    # Step 3: Base position cap.
    # nav and max_position_pct_nav are finite and > 0 (domain-validated).
    # ------------------------------------------------------------------
    base_cap: float = portfolio.nav * params.max_position_pct_nav

    # ------------------------------------------------------------------
    # Step 4: Volatility-adjusted cap scalar.
    # position_vol=None -> scalar=1.0 (identity; preserves Phase 7C output).
    # max(position_vol, 1e-8) guards against division by zero or near-zero.
    # min(..., 1.0) prevents the scalar from exceeding 1 (no vol-based leverage).
    # ------------------------------------------------------------------
    if position_vol is not None:
        vol_cap_scalar: float = min(
            1.0,
        )
    else:
        vol_cap_scalar = 1.0

    # ------------------------------------------------------------------
    # Step 5: Effective cap.
    # vol_cap = base_cap * scalar. effective_cap = min(base_cap, vol_cap).
    # When scalar=1.0: vol_cap == base_cap -> effective_cap == base_cap.
    # ------------------------------------------------------------------
    effective_cap: float = min(base_cap, base_cap * vol_cap_scalar)

    # ------------------------------------------------------------------
    # Step 6: Raw target capped at effective_cap.
    # ------------------------------------------------------------------
    raw_target: float = min(requested_notional, effective_cap)

    # ------------------------------------------------------------------
    # Step 7: Kelly fraction.
    # kelly_fraction is validated in (0.0, 1.0] by RiskParameters.
    # No guard needed; always reduces or preserves raw_target.
    # ------------------------------------------------------------------
    kelly_target: float = raw_target * params.kelly_fraction

    # ------------------------------------------------------------------
    # Step 8: REDUCE multiplier (conditional on clamping).
    # REDUCE applies liquidity_haircut_floor only when the position was
    # clamped by the cap (raw_target < requested_notional).
    # When not clamped (position already within cap), REDUCE passes
    # kelly_target through unchanged -- no additional compression.
    # APPROVE always passes kelly_target through unchanged.
    # liquidity_haircut_floor validated in (0.0, 1.0] by RiskParameters.
    # ------------------------------------------------------------------
    _was_clamped: bool = raw_target < requested_notional
    if decision.verdict is RiskVerdict.REDUCE and _was_clamped:
        reduce_target: float = kelly_target * params.liquidity_haircut_floor
    else:
        reduce_target = kelly_target

    # ------------------------------------------------------------------
    # Step 9: Liquidity floor guarantee (INV-SZ-05).
    # Even after Kelly and REDUCE compression, target must be at least
    # liquidity_haircut_floor fraction of the original requested notional.
    # This prevents compound discounting from compressing to near-zero.
    # ------------------------------------------------------------------
    liquidity_floor_value: float = requested_notional * params.liquidity_haircut_floor
    target: float = max(reduce_target, liquidity_floor_value)

    return PositionSizingResult(
        allowed=True,
        target_notional=target,
        reason=decision.verdict,
    )


# =============================================================================
# SECTION 2 -- SIZE POSITION
# =============================================================================

def x_size_position__mutmut_17(
    position:     PositionSpec,
    portfolio:    PortfolioState,
    params:       RiskParameters,
    decision:     RiskDecision,
    position_vol: Optional[float] = None,
) -> PositionSizingResult:
    """
    Compute the allowed position size given a pre-evaluated RiskDecision.

    Pure function: reads arguments, returns PositionSizingResult.
    No mutation, no global state, no I/O, no side effects.

    Sizing pipeline (fixed order):
        1.  HALT -> return immediately.
        2.  requested_notional = quantity * current_price
        3.  base_cap = nav * max_position_pct_nav
        4.  vol_cap_scalar = min(volatility_target_ann / max(position_vol, 1e-8), 1.0)
                             if position_vol is not None else 1.0
        5.  effective_cap = min(base_cap, base_cap * vol_cap_scalar)
        6.  raw_target = min(requested_notional, effective_cap)
        7.  kelly_target = raw_target * kelly_fraction
        8.  reduce_target = kelly_target * liquidity_haircut_floor  (REDUCE)
                          = kelly_target                             (APPROVE)
        9.  liquidity_floor = requested_notional * liquidity_haircut_floor
        10. target = max(reduce_target, liquidity_floor)

    Args:
        position:     PositionSpec. quantity and current_price derive requested notional.
        portfolio:    PortfolioState. nav used for base cap.
        params:       RiskParameters. All sizing scalars consumed here.
        decision:     RiskDecision from evaluate_position_risk(). Only verdict consumed.
        position_vol: Optional annualised volatility of this position.
                      None -> vol_cap_scalar = 1.0 (no vol adjustment; backward compat).

    Returns:
        PositionSizingResult(allowed, target_notional, reason).
    """
    # ------------------------------------------------------------------
    # Step 1: HALT -- no sizing arithmetic performed.
    # ------------------------------------------------------------------
    if decision.verdict is RiskVerdict.HALT:
        return PositionSizingResult(
            allowed=False,
            target_notional=None,
            reason=decision.verdict,
        )

    # ------------------------------------------------------------------
    # Step 2: Requested notional.
    # quantity and current_price are finite and > 0 (domain-validated).
    # ------------------------------------------------------------------
    requested_notional: float = position.quantity * position.current_price

    # ------------------------------------------------------------------
    # Step 3: Base position cap.
    # nav and max_position_pct_nav are finite and > 0 (domain-validated).
    # ------------------------------------------------------------------
    base_cap: float = portfolio.nav * params.max_position_pct_nav

    # ------------------------------------------------------------------
    # Step 4: Volatility-adjusted cap scalar.
    # position_vol=None -> scalar=1.0 (identity; preserves Phase 7C output).
    # max(position_vol, 1e-8) guards against division by zero or near-zero.
    # min(..., 1.0) prevents the scalar from exceeding 1 (no vol-based leverage).
    # ------------------------------------------------------------------
    if position_vol is not None:
        vol_cap_scalar: float = min(
            params.volatility_target_ann / max(position_vol, 1e-8),
            )
    else:
        vol_cap_scalar = 1.0

    # ------------------------------------------------------------------
    # Step 5: Effective cap.
    # vol_cap = base_cap * scalar. effective_cap = min(base_cap, vol_cap).
    # When scalar=1.0: vol_cap == base_cap -> effective_cap == base_cap.
    # ------------------------------------------------------------------
    effective_cap: float = min(base_cap, base_cap * vol_cap_scalar)

    # ------------------------------------------------------------------
    # Step 6: Raw target capped at effective_cap.
    # ------------------------------------------------------------------
    raw_target: float = min(requested_notional, effective_cap)

    # ------------------------------------------------------------------
    # Step 7: Kelly fraction.
    # kelly_fraction is validated in (0.0, 1.0] by RiskParameters.
    # No guard needed; always reduces or preserves raw_target.
    # ------------------------------------------------------------------
    kelly_target: float = raw_target * params.kelly_fraction

    # ------------------------------------------------------------------
    # Step 8: REDUCE multiplier (conditional on clamping).
    # REDUCE applies liquidity_haircut_floor only when the position was
    # clamped by the cap (raw_target < requested_notional).
    # When not clamped (position already within cap), REDUCE passes
    # kelly_target through unchanged -- no additional compression.
    # APPROVE always passes kelly_target through unchanged.
    # liquidity_haircut_floor validated in (0.0, 1.0] by RiskParameters.
    # ------------------------------------------------------------------
    _was_clamped: bool = raw_target < requested_notional
    if decision.verdict is RiskVerdict.REDUCE and _was_clamped:
        reduce_target: float = kelly_target * params.liquidity_haircut_floor
    else:
        reduce_target = kelly_target

    # ------------------------------------------------------------------
    # Step 9: Liquidity floor guarantee (INV-SZ-05).
    # Even after Kelly and REDUCE compression, target must be at least
    # liquidity_haircut_floor fraction of the original requested notional.
    # This prevents compound discounting from compressing to near-zero.
    # ------------------------------------------------------------------
    liquidity_floor_value: float = requested_notional * params.liquidity_haircut_floor
    target: float = max(reduce_target, liquidity_floor_value)

    return PositionSizingResult(
        allowed=True,
        target_notional=target,
        reason=decision.verdict,
    )


# =============================================================================
# SECTION 2 -- SIZE POSITION
# =============================================================================

def x_size_position__mutmut_18(
    position:     PositionSpec,
    portfolio:    PortfolioState,
    params:       RiskParameters,
    decision:     RiskDecision,
    position_vol: Optional[float] = None,
) -> PositionSizingResult:
    """
    Compute the allowed position size given a pre-evaluated RiskDecision.

    Pure function: reads arguments, returns PositionSizingResult.
    No mutation, no global state, no I/O, no side effects.

    Sizing pipeline (fixed order):
        1.  HALT -> return immediately.
        2.  requested_notional = quantity * current_price
        3.  base_cap = nav * max_position_pct_nav
        4.  vol_cap_scalar = min(volatility_target_ann / max(position_vol, 1e-8), 1.0)
                             if position_vol is not None else 1.0
        5.  effective_cap = min(base_cap, base_cap * vol_cap_scalar)
        6.  raw_target = min(requested_notional, effective_cap)
        7.  kelly_target = raw_target * kelly_fraction
        8.  reduce_target = kelly_target * liquidity_haircut_floor  (REDUCE)
                          = kelly_target                             (APPROVE)
        9.  liquidity_floor = requested_notional * liquidity_haircut_floor
        10. target = max(reduce_target, liquidity_floor)

    Args:
        position:     PositionSpec. quantity and current_price derive requested notional.
        portfolio:    PortfolioState. nav used for base cap.
        params:       RiskParameters. All sizing scalars consumed here.
        decision:     RiskDecision from evaluate_position_risk(). Only verdict consumed.
        position_vol: Optional annualised volatility of this position.
                      None -> vol_cap_scalar = 1.0 (no vol adjustment; backward compat).

    Returns:
        PositionSizingResult(allowed, target_notional, reason).
    """
    # ------------------------------------------------------------------
    # Step 1: HALT -- no sizing arithmetic performed.
    # ------------------------------------------------------------------
    if decision.verdict is RiskVerdict.HALT:
        return PositionSizingResult(
            allowed=False,
            target_notional=None,
            reason=decision.verdict,
        )

    # ------------------------------------------------------------------
    # Step 2: Requested notional.
    # quantity and current_price are finite and > 0 (domain-validated).
    # ------------------------------------------------------------------
    requested_notional: float = position.quantity * position.current_price

    # ------------------------------------------------------------------
    # Step 3: Base position cap.
    # nav and max_position_pct_nav are finite and > 0 (domain-validated).
    # ------------------------------------------------------------------
    base_cap: float = portfolio.nav * params.max_position_pct_nav

    # ------------------------------------------------------------------
    # Step 4: Volatility-adjusted cap scalar.
    # position_vol=None -> scalar=1.0 (identity; preserves Phase 7C output).
    # max(position_vol, 1e-8) guards against division by zero or near-zero.
    # min(..., 1.0) prevents the scalar from exceeding 1 (no vol-based leverage).
    # ------------------------------------------------------------------
    if position_vol is not None:
        vol_cap_scalar: float = min(
            params.volatility_target_ann * max(position_vol, 1e-8),
            1.0,
        )
    else:
        vol_cap_scalar = 1.0

    # ------------------------------------------------------------------
    # Step 5: Effective cap.
    # vol_cap = base_cap * scalar. effective_cap = min(base_cap, vol_cap).
    # When scalar=1.0: vol_cap == base_cap -> effective_cap == base_cap.
    # ------------------------------------------------------------------
    effective_cap: float = min(base_cap, base_cap * vol_cap_scalar)

    # ------------------------------------------------------------------
    # Step 6: Raw target capped at effective_cap.
    # ------------------------------------------------------------------
    raw_target: float = min(requested_notional, effective_cap)

    # ------------------------------------------------------------------
    # Step 7: Kelly fraction.
    # kelly_fraction is validated in (0.0, 1.0] by RiskParameters.
    # No guard needed; always reduces or preserves raw_target.
    # ------------------------------------------------------------------
    kelly_target: float = raw_target * params.kelly_fraction

    # ------------------------------------------------------------------
    # Step 8: REDUCE multiplier (conditional on clamping).
    # REDUCE applies liquidity_haircut_floor only when the position was
    # clamped by the cap (raw_target < requested_notional).
    # When not clamped (position already within cap), REDUCE passes
    # kelly_target through unchanged -- no additional compression.
    # APPROVE always passes kelly_target through unchanged.
    # liquidity_haircut_floor validated in (0.0, 1.0] by RiskParameters.
    # ------------------------------------------------------------------
    _was_clamped: bool = raw_target < requested_notional
    if decision.verdict is RiskVerdict.REDUCE and _was_clamped:
        reduce_target: float = kelly_target * params.liquidity_haircut_floor
    else:
        reduce_target = kelly_target

    # ------------------------------------------------------------------
    # Step 9: Liquidity floor guarantee (INV-SZ-05).
    # Even after Kelly and REDUCE compression, target must be at least
    # liquidity_haircut_floor fraction of the original requested notional.
    # This prevents compound discounting from compressing to near-zero.
    # ------------------------------------------------------------------
    liquidity_floor_value: float = requested_notional * params.liquidity_haircut_floor
    target: float = max(reduce_target, liquidity_floor_value)

    return PositionSizingResult(
        allowed=True,
        target_notional=target,
        reason=decision.verdict,
    )


# =============================================================================
# SECTION 2 -- SIZE POSITION
# =============================================================================

def x_size_position__mutmut_19(
    position:     PositionSpec,
    portfolio:    PortfolioState,
    params:       RiskParameters,
    decision:     RiskDecision,
    position_vol: Optional[float] = None,
) -> PositionSizingResult:
    """
    Compute the allowed position size given a pre-evaluated RiskDecision.

    Pure function: reads arguments, returns PositionSizingResult.
    No mutation, no global state, no I/O, no side effects.

    Sizing pipeline (fixed order):
        1.  HALT -> return immediately.
        2.  requested_notional = quantity * current_price
        3.  base_cap = nav * max_position_pct_nav
        4.  vol_cap_scalar = min(volatility_target_ann / max(position_vol, 1e-8), 1.0)
                             if position_vol is not None else 1.0
        5.  effective_cap = min(base_cap, base_cap * vol_cap_scalar)
        6.  raw_target = min(requested_notional, effective_cap)
        7.  kelly_target = raw_target * kelly_fraction
        8.  reduce_target = kelly_target * liquidity_haircut_floor  (REDUCE)
                          = kelly_target                             (APPROVE)
        9.  liquidity_floor = requested_notional * liquidity_haircut_floor
        10. target = max(reduce_target, liquidity_floor)

    Args:
        position:     PositionSpec. quantity and current_price derive requested notional.
        portfolio:    PortfolioState. nav used for base cap.
        params:       RiskParameters. All sizing scalars consumed here.
        decision:     RiskDecision from evaluate_position_risk(). Only verdict consumed.
        position_vol: Optional annualised volatility of this position.
                      None -> vol_cap_scalar = 1.0 (no vol adjustment; backward compat).

    Returns:
        PositionSizingResult(allowed, target_notional, reason).
    """
    # ------------------------------------------------------------------
    # Step 1: HALT -- no sizing arithmetic performed.
    # ------------------------------------------------------------------
    if decision.verdict is RiskVerdict.HALT:
        return PositionSizingResult(
            allowed=False,
            target_notional=None,
            reason=decision.verdict,
        )

    # ------------------------------------------------------------------
    # Step 2: Requested notional.
    # quantity and current_price are finite and > 0 (domain-validated).
    # ------------------------------------------------------------------
    requested_notional: float = position.quantity * position.current_price

    # ------------------------------------------------------------------
    # Step 3: Base position cap.
    # nav and max_position_pct_nav are finite and > 0 (domain-validated).
    # ------------------------------------------------------------------
    base_cap: float = portfolio.nav * params.max_position_pct_nav

    # ------------------------------------------------------------------
    # Step 4: Volatility-adjusted cap scalar.
    # position_vol=None -> scalar=1.0 (identity; preserves Phase 7C output).
    # max(position_vol, 1e-8) guards against division by zero or near-zero.
    # min(..., 1.0) prevents the scalar from exceeding 1 (no vol-based leverage).
    # ------------------------------------------------------------------
    if position_vol is not None:
        vol_cap_scalar: float = min(
            params.volatility_target_ann / max(None, 1e-8),
            1.0,
        )
    else:
        vol_cap_scalar = 1.0

    # ------------------------------------------------------------------
    # Step 5: Effective cap.
    # vol_cap = base_cap * scalar. effective_cap = min(base_cap, vol_cap).
    # When scalar=1.0: vol_cap == base_cap -> effective_cap == base_cap.
    # ------------------------------------------------------------------
    effective_cap: float = min(base_cap, base_cap * vol_cap_scalar)

    # ------------------------------------------------------------------
    # Step 6: Raw target capped at effective_cap.
    # ------------------------------------------------------------------
    raw_target: float = min(requested_notional, effective_cap)

    # ------------------------------------------------------------------
    # Step 7: Kelly fraction.
    # kelly_fraction is validated in (0.0, 1.0] by RiskParameters.
    # No guard needed; always reduces or preserves raw_target.
    # ------------------------------------------------------------------
    kelly_target: float = raw_target * params.kelly_fraction

    # ------------------------------------------------------------------
    # Step 8: REDUCE multiplier (conditional on clamping).
    # REDUCE applies liquidity_haircut_floor only when the position was
    # clamped by the cap (raw_target < requested_notional).
    # When not clamped (position already within cap), REDUCE passes
    # kelly_target through unchanged -- no additional compression.
    # APPROVE always passes kelly_target through unchanged.
    # liquidity_haircut_floor validated in (0.0, 1.0] by RiskParameters.
    # ------------------------------------------------------------------
    _was_clamped: bool = raw_target < requested_notional
    if decision.verdict is RiskVerdict.REDUCE and _was_clamped:
        reduce_target: float = kelly_target * params.liquidity_haircut_floor
    else:
        reduce_target = kelly_target

    # ------------------------------------------------------------------
    # Step 9: Liquidity floor guarantee (INV-SZ-05).
    # Even after Kelly and REDUCE compression, target must be at least
    # liquidity_haircut_floor fraction of the original requested notional.
    # This prevents compound discounting from compressing to near-zero.
    # ------------------------------------------------------------------
    liquidity_floor_value: float = requested_notional * params.liquidity_haircut_floor
    target: float = max(reduce_target, liquidity_floor_value)

    return PositionSizingResult(
        allowed=True,
        target_notional=target,
        reason=decision.verdict,
    )


# =============================================================================
# SECTION 2 -- SIZE POSITION
# =============================================================================

def x_size_position__mutmut_20(
    position:     PositionSpec,
    portfolio:    PortfolioState,
    params:       RiskParameters,
    decision:     RiskDecision,
    position_vol: Optional[float] = None,
) -> PositionSizingResult:
    """
    Compute the allowed position size given a pre-evaluated RiskDecision.

    Pure function: reads arguments, returns PositionSizingResult.
    No mutation, no global state, no I/O, no side effects.

    Sizing pipeline (fixed order):
        1.  HALT -> return immediately.
        2.  requested_notional = quantity * current_price
        3.  base_cap = nav * max_position_pct_nav
        4.  vol_cap_scalar = min(volatility_target_ann / max(position_vol, 1e-8), 1.0)
                             if position_vol is not None else 1.0
        5.  effective_cap = min(base_cap, base_cap * vol_cap_scalar)
        6.  raw_target = min(requested_notional, effective_cap)
        7.  kelly_target = raw_target * kelly_fraction
        8.  reduce_target = kelly_target * liquidity_haircut_floor  (REDUCE)
                          = kelly_target                             (APPROVE)
        9.  liquidity_floor = requested_notional * liquidity_haircut_floor
        10. target = max(reduce_target, liquidity_floor)

    Args:
        position:     PositionSpec. quantity and current_price derive requested notional.
        portfolio:    PortfolioState. nav used for base cap.
        params:       RiskParameters. All sizing scalars consumed here.
        decision:     RiskDecision from evaluate_position_risk(). Only verdict consumed.
        position_vol: Optional annualised volatility of this position.
                      None -> vol_cap_scalar = 1.0 (no vol adjustment; backward compat).

    Returns:
        PositionSizingResult(allowed, target_notional, reason).
    """
    # ------------------------------------------------------------------
    # Step 1: HALT -- no sizing arithmetic performed.
    # ------------------------------------------------------------------
    if decision.verdict is RiskVerdict.HALT:
        return PositionSizingResult(
            allowed=False,
            target_notional=None,
            reason=decision.verdict,
        )

    # ------------------------------------------------------------------
    # Step 2: Requested notional.
    # quantity and current_price are finite and > 0 (domain-validated).
    # ------------------------------------------------------------------
    requested_notional: float = position.quantity * position.current_price

    # ------------------------------------------------------------------
    # Step 3: Base position cap.
    # nav and max_position_pct_nav are finite and > 0 (domain-validated).
    # ------------------------------------------------------------------
    base_cap: float = portfolio.nav * params.max_position_pct_nav

    # ------------------------------------------------------------------
    # Step 4: Volatility-adjusted cap scalar.
    # position_vol=None -> scalar=1.0 (identity; preserves Phase 7C output).
    # max(position_vol, 1e-8) guards against division by zero or near-zero.
    # min(..., 1.0) prevents the scalar from exceeding 1 (no vol-based leverage).
    # ------------------------------------------------------------------
    if position_vol is not None:
        vol_cap_scalar: float = min(
            params.volatility_target_ann / max(position_vol, None),
            1.0,
        )
    else:
        vol_cap_scalar = 1.0

    # ------------------------------------------------------------------
    # Step 5: Effective cap.
    # vol_cap = base_cap * scalar. effective_cap = min(base_cap, vol_cap).
    # When scalar=1.0: vol_cap == base_cap -> effective_cap == base_cap.
    # ------------------------------------------------------------------
    effective_cap: float = min(base_cap, base_cap * vol_cap_scalar)

    # ------------------------------------------------------------------
    # Step 6: Raw target capped at effective_cap.
    # ------------------------------------------------------------------
    raw_target: float = min(requested_notional, effective_cap)

    # ------------------------------------------------------------------
    # Step 7: Kelly fraction.
    # kelly_fraction is validated in (0.0, 1.0] by RiskParameters.
    # No guard needed; always reduces or preserves raw_target.
    # ------------------------------------------------------------------
    kelly_target: float = raw_target * params.kelly_fraction

    # ------------------------------------------------------------------
    # Step 8: REDUCE multiplier (conditional on clamping).
    # REDUCE applies liquidity_haircut_floor only when the position was
    # clamped by the cap (raw_target < requested_notional).
    # When not clamped (position already within cap), REDUCE passes
    # kelly_target through unchanged -- no additional compression.
    # APPROVE always passes kelly_target through unchanged.
    # liquidity_haircut_floor validated in (0.0, 1.0] by RiskParameters.
    # ------------------------------------------------------------------
    _was_clamped: bool = raw_target < requested_notional
    if decision.verdict is RiskVerdict.REDUCE and _was_clamped:
        reduce_target: float = kelly_target * params.liquidity_haircut_floor
    else:
        reduce_target = kelly_target

    # ------------------------------------------------------------------
    # Step 9: Liquidity floor guarantee (INV-SZ-05).
    # Even after Kelly and REDUCE compression, target must be at least
    # liquidity_haircut_floor fraction of the original requested notional.
    # This prevents compound discounting from compressing to near-zero.
    # ------------------------------------------------------------------
    liquidity_floor_value: float = requested_notional * params.liquidity_haircut_floor
    target: float = max(reduce_target, liquidity_floor_value)

    return PositionSizingResult(
        allowed=True,
        target_notional=target,
        reason=decision.verdict,
    )


# =============================================================================
# SECTION 2 -- SIZE POSITION
# =============================================================================

def x_size_position__mutmut_21(
    position:     PositionSpec,
    portfolio:    PortfolioState,
    params:       RiskParameters,
    decision:     RiskDecision,
    position_vol: Optional[float] = None,
) -> PositionSizingResult:
    """
    Compute the allowed position size given a pre-evaluated RiskDecision.

    Pure function: reads arguments, returns PositionSizingResult.
    No mutation, no global state, no I/O, no side effects.

    Sizing pipeline (fixed order):
        1.  HALT -> return immediately.
        2.  requested_notional = quantity * current_price
        3.  base_cap = nav * max_position_pct_nav
        4.  vol_cap_scalar = min(volatility_target_ann / max(position_vol, 1e-8), 1.0)
                             if position_vol is not None else 1.0
        5.  effective_cap = min(base_cap, base_cap * vol_cap_scalar)
        6.  raw_target = min(requested_notional, effective_cap)
        7.  kelly_target = raw_target * kelly_fraction
        8.  reduce_target = kelly_target * liquidity_haircut_floor  (REDUCE)
                          = kelly_target                             (APPROVE)
        9.  liquidity_floor = requested_notional * liquidity_haircut_floor
        10. target = max(reduce_target, liquidity_floor)

    Args:
        position:     PositionSpec. quantity and current_price derive requested notional.
        portfolio:    PortfolioState. nav used for base cap.
        params:       RiskParameters. All sizing scalars consumed here.
        decision:     RiskDecision from evaluate_position_risk(). Only verdict consumed.
        position_vol: Optional annualised volatility of this position.
                      None -> vol_cap_scalar = 1.0 (no vol adjustment; backward compat).

    Returns:
        PositionSizingResult(allowed, target_notional, reason).
    """
    # ------------------------------------------------------------------
    # Step 1: HALT -- no sizing arithmetic performed.
    # ------------------------------------------------------------------
    if decision.verdict is RiskVerdict.HALT:
        return PositionSizingResult(
            allowed=False,
            target_notional=None,
            reason=decision.verdict,
        )

    # ------------------------------------------------------------------
    # Step 2: Requested notional.
    # quantity and current_price are finite and > 0 (domain-validated).
    # ------------------------------------------------------------------
    requested_notional: float = position.quantity * position.current_price

    # ------------------------------------------------------------------
    # Step 3: Base position cap.
    # nav and max_position_pct_nav are finite and > 0 (domain-validated).
    # ------------------------------------------------------------------
    base_cap: float = portfolio.nav * params.max_position_pct_nav

    # ------------------------------------------------------------------
    # Step 4: Volatility-adjusted cap scalar.
    # position_vol=None -> scalar=1.0 (identity; preserves Phase 7C output).
    # max(position_vol, 1e-8) guards against division by zero or near-zero.
    # min(..., 1.0) prevents the scalar from exceeding 1 (no vol-based leverage).
    # ------------------------------------------------------------------
    if position_vol is not None:
        vol_cap_scalar: float = min(
            params.volatility_target_ann / max(1e-8),
            1.0,
        )
    else:
        vol_cap_scalar = 1.0

    # ------------------------------------------------------------------
    # Step 5: Effective cap.
    # vol_cap = base_cap * scalar. effective_cap = min(base_cap, vol_cap).
    # When scalar=1.0: vol_cap == base_cap -> effective_cap == base_cap.
    # ------------------------------------------------------------------
    effective_cap: float = min(base_cap, base_cap * vol_cap_scalar)

    # ------------------------------------------------------------------
    # Step 6: Raw target capped at effective_cap.
    # ------------------------------------------------------------------
    raw_target: float = min(requested_notional, effective_cap)

    # ------------------------------------------------------------------
    # Step 7: Kelly fraction.
    # kelly_fraction is validated in (0.0, 1.0] by RiskParameters.
    # No guard needed; always reduces or preserves raw_target.
    # ------------------------------------------------------------------
    kelly_target: float = raw_target * params.kelly_fraction

    # ------------------------------------------------------------------
    # Step 8: REDUCE multiplier (conditional on clamping).
    # REDUCE applies liquidity_haircut_floor only when the position was
    # clamped by the cap (raw_target < requested_notional).
    # When not clamped (position already within cap), REDUCE passes
    # kelly_target through unchanged -- no additional compression.
    # APPROVE always passes kelly_target through unchanged.
    # liquidity_haircut_floor validated in (0.0, 1.0] by RiskParameters.
    # ------------------------------------------------------------------
    _was_clamped: bool = raw_target < requested_notional
    if decision.verdict is RiskVerdict.REDUCE and _was_clamped:
        reduce_target: float = kelly_target * params.liquidity_haircut_floor
    else:
        reduce_target = kelly_target

    # ------------------------------------------------------------------
    # Step 9: Liquidity floor guarantee (INV-SZ-05).
    # Even after Kelly and REDUCE compression, target must be at least
    # liquidity_haircut_floor fraction of the original requested notional.
    # This prevents compound discounting from compressing to near-zero.
    # ------------------------------------------------------------------
    liquidity_floor_value: float = requested_notional * params.liquidity_haircut_floor
    target: float = max(reduce_target, liquidity_floor_value)

    return PositionSizingResult(
        allowed=True,
        target_notional=target,
        reason=decision.verdict,
    )


# =============================================================================
# SECTION 2 -- SIZE POSITION
# =============================================================================

def x_size_position__mutmut_22(
    position:     PositionSpec,
    portfolio:    PortfolioState,
    params:       RiskParameters,
    decision:     RiskDecision,
    position_vol: Optional[float] = None,
) -> PositionSizingResult:
    """
    Compute the allowed position size given a pre-evaluated RiskDecision.

    Pure function: reads arguments, returns PositionSizingResult.
    No mutation, no global state, no I/O, no side effects.

    Sizing pipeline (fixed order):
        1.  HALT -> return immediately.
        2.  requested_notional = quantity * current_price
        3.  base_cap = nav * max_position_pct_nav
        4.  vol_cap_scalar = min(volatility_target_ann / max(position_vol, 1e-8), 1.0)
                             if position_vol is not None else 1.0
        5.  effective_cap = min(base_cap, base_cap * vol_cap_scalar)
        6.  raw_target = min(requested_notional, effective_cap)
        7.  kelly_target = raw_target * kelly_fraction
        8.  reduce_target = kelly_target * liquidity_haircut_floor  (REDUCE)
                          = kelly_target                             (APPROVE)
        9.  liquidity_floor = requested_notional * liquidity_haircut_floor
        10. target = max(reduce_target, liquidity_floor)

    Args:
        position:     PositionSpec. quantity and current_price derive requested notional.
        portfolio:    PortfolioState. nav used for base cap.
        params:       RiskParameters. All sizing scalars consumed here.
        decision:     RiskDecision from evaluate_position_risk(). Only verdict consumed.
        position_vol: Optional annualised volatility of this position.
                      None -> vol_cap_scalar = 1.0 (no vol adjustment; backward compat).

    Returns:
        PositionSizingResult(allowed, target_notional, reason).
    """
    # ------------------------------------------------------------------
    # Step 1: HALT -- no sizing arithmetic performed.
    # ------------------------------------------------------------------
    if decision.verdict is RiskVerdict.HALT:
        return PositionSizingResult(
            allowed=False,
            target_notional=None,
            reason=decision.verdict,
        )

    # ------------------------------------------------------------------
    # Step 2: Requested notional.
    # quantity and current_price are finite and > 0 (domain-validated).
    # ------------------------------------------------------------------
    requested_notional: float = position.quantity * position.current_price

    # ------------------------------------------------------------------
    # Step 3: Base position cap.
    # nav and max_position_pct_nav are finite and > 0 (domain-validated).
    # ------------------------------------------------------------------
    base_cap: float = portfolio.nav * params.max_position_pct_nav

    # ------------------------------------------------------------------
    # Step 4: Volatility-adjusted cap scalar.
    # position_vol=None -> scalar=1.0 (identity; preserves Phase 7C output).
    # max(position_vol, 1e-8) guards against division by zero or near-zero.
    # min(..., 1.0) prevents the scalar from exceeding 1 (no vol-based leverage).
    # ------------------------------------------------------------------
    if position_vol is not None:
        vol_cap_scalar: float = min(
            params.volatility_target_ann / max(position_vol, ),
            1.0,
        )
    else:
        vol_cap_scalar = 1.0

    # ------------------------------------------------------------------
    # Step 5: Effective cap.
    # vol_cap = base_cap * scalar. effective_cap = min(base_cap, vol_cap).
    # When scalar=1.0: vol_cap == base_cap -> effective_cap == base_cap.
    # ------------------------------------------------------------------
    effective_cap: float = min(base_cap, base_cap * vol_cap_scalar)

    # ------------------------------------------------------------------
    # Step 6: Raw target capped at effective_cap.
    # ------------------------------------------------------------------
    raw_target: float = min(requested_notional, effective_cap)

    # ------------------------------------------------------------------
    # Step 7: Kelly fraction.
    # kelly_fraction is validated in (0.0, 1.0] by RiskParameters.
    # No guard needed; always reduces or preserves raw_target.
    # ------------------------------------------------------------------
    kelly_target: float = raw_target * params.kelly_fraction

    # ------------------------------------------------------------------
    # Step 8: REDUCE multiplier (conditional on clamping).
    # REDUCE applies liquidity_haircut_floor only when the position was
    # clamped by the cap (raw_target < requested_notional).
    # When not clamped (position already within cap), REDUCE passes
    # kelly_target through unchanged -- no additional compression.
    # APPROVE always passes kelly_target through unchanged.
    # liquidity_haircut_floor validated in (0.0, 1.0] by RiskParameters.
    # ------------------------------------------------------------------
    _was_clamped: bool = raw_target < requested_notional
    if decision.verdict is RiskVerdict.REDUCE and _was_clamped:
        reduce_target: float = kelly_target * params.liquidity_haircut_floor
    else:
        reduce_target = kelly_target

    # ------------------------------------------------------------------
    # Step 9: Liquidity floor guarantee (INV-SZ-05).
    # Even after Kelly and REDUCE compression, target must be at least
    # liquidity_haircut_floor fraction of the original requested notional.
    # This prevents compound discounting from compressing to near-zero.
    # ------------------------------------------------------------------
    liquidity_floor_value: float = requested_notional * params.liquidity_haircut_floor
    target: float = max(reduce_target, liquidity_floor_value)

    return PositionSizingResult(
        allowed=True,
        target_notional=target,
        reason=decision.verdict,
    )


# =============================================================================
# SECTION 2 -- SIZE POSITION
# =============================================================================

def x_size_position__mutmut_23(
    position:     PositionSpec,
    portfolio:    PortfolioState,
    params:       RiskParameters,
    decision:     RiskDecision,
    position_vol: Optional[float] = None,
) -> PositionSizingResult:
    """
    Compute the allowed position size given a pre-evaluated RiskDecision.

    Pure function: reads arguments, returns PositionSizingResult.
    No mutation, no global state, no I/O, no side effects.

    Sizing pipeline (fixed order):
        1.  HALT -> return immediately.
        2.  requested_notional = quantity * current_price
        3.  base_cap = nav * max_position_pct_nav
        4.  vol_cap_scalar = min(volatility_target_ann / max(position_vol, 1e-8), 1.0)
                             if position_vol is not None else 1.0
        5.  effective_cap = min(base_cap, base_cap * vol_cap_scalar)
        6.  raw_target = min(requested_notional, effective_cap)
        7.  kelly_target = raw_target * kelly_fraction
        8.  reduce_target = kelly_target * liquidity_haircut_floor  (REDUCE)
                          = kelly_target                             (APPROVE)
        9.  liquidity_floor = requested_notional * liquidity_haircut_floor
        10. target = max(reduce_target, liquidity_floor)

    Args:
        position:     PositionSpec. quantity and current_price derive requested notional.
        portfolio:    PortfolioState. nav used for base cap.
        params:       RiskParameters. All sizing scalars consumed here.
        decision:     RiskDecision from evaluate_position_risk(). Only verdict consumed.
        position_vol: Optional annualised volatility of this position.
                      None -> vol_cap_scalar = 1.0 (no vol adjustment; backward compat).

    Returns:
        PositionSizingResult(allowed, target_notional, reason).
    """
    # ------------------------------------------------------------------
    # Step 1: HALT -- no sizing arithmetic performed.
    # ------------------------------------------------------------------
    if decision.verdict is RiskVerdict.HALT:
        return PositionSizingResult(
            allowed=False,
            target_notional=None,
            reason=decision.verdict,
        )

    # ------------------------------------------------------------------
    # Step 2: Requested notional.
    # quantity and current_price are finite and > 0 (domain-validated).
    # ------------------------------------------------------------------
    requested_notional: float = position.quantity * position.current_price

    # ------------------------------------------------------------------
    # Step 3: Base position cap.
    # nav and max_position_pct_nav are finite and > 0 (domain-validated).
    # ------------------------------------------------------------------
    base_cap: float = portfolio.nav * params.max_position_pct_nav

    # ------------------------------------------------------------------
    # Step 4: Volatility-adjusted cap scalar.
    # position_vol=None -> scalar=1.0 (identity; preserves Phase 7C output).
    # max(position_vol, 1e-8) guards against division by zero or near-zero.
    # min(..., 1.0) prevents the scalar from exceeding 1 (no vol-based leverage).
    # ------------------------------------------------------------------
    if position_vol is not None:
        vol_cap_scalar: float = min(
            params.volatility_target_ann / max(position_vol, 1.00000001),
            1.0,
        )
    else:
        vol_cap_scalar = 1.0

    # ------------------------------------------------------------------
    # Step 5: Effective cap.
    # vol_cap = base_cap * scalar. effective_cap = min(base_cap, vol_cap).
    # When scalar=1.0: vol_cap == base_cap -> effective_cap == base_cap.
    # ------------------------------------------------------------------
    effective_cap: float = min(base_cap, base_cap * vol_cap_scalar)

    # ------------------------------------------------------------------
    # Step 6: Raw target capped at effective_cap.
    # ------------------------------------------------------------------
    raw_target: float = min(requested_notional, effective_cap)

    # ------------------------------------------------------------------
    # Step 7: Kelly fraction.
    # kelly_fraction is validated in (0.0, 1.0] by RiskParameters.
    # No guard needed; always reduces or preserves raw_target.
    # ------------------------------------------------------------------
    kelly_target: float = raw_target * params.kelly_fraction

    # ------------------------------------------------------------------
    # Step 8: REDUCE multiplier (conditional on clamping).
    # REDUCE applies liquidity_haircut_floor only when the position was
    # clamped by the cap (raw_target < requested_notional).
    # When not clamped (position already within cap), REDUCE passes
    # kelly_target through unchanged -- no additional compression.
    # APPROVE always passes kelly_target through unchanged.
    # liquidity_haircut_floor validated in (0.0, 1.0] by RiskParameters.
    # ------------------------------------------------------------------
    _was_clamped: bool = raw_target < requested_notional
    if decision.verdict is RiskVerdict.REDUCE and _was_clamped:
        reduce_target: float = kelly_target * params.liquidity_haircut_floor
    else:
        reduce_target = kelly_target

    # ------------------------------------------------------------------
    # Step 9: Liquidity floor guarantee (INV-SZ-05).
    # Even after Kelly and REDUCE compression, target must be at least
    # liquidity_haircut_floor fraction of the original requested notional.
    # This prevents compound discounting from compressing to near-zero.
    # ------------------------------------------------------------------
    liquidity_floor_value: float = requested_notional * params.liquidity_haircut_floor
    target: float = max(reduce_target, liquidity_floor_value)

    return PositionSizingResult(
        allowed=True,
        target_notional=target,
        reason=decision.verdict,
    )


# =============================================================================
# SECTION 2 -- SIZE POSITION
# =============================================================================

def x_size_position__mutmut_24(
    position:     PositionSpec,
    portfolio:    PortfolioState,
    params:       RiskParameters,
    decision:     RiskDecision,
    position_vol: Optional[float] = None,
) -> PositionSizingResult:
    """
    Compute the allowed position size given a pre-evaluated RiskDecision.

    Pure function: reads arguments, returns PositionSizingResult.
    No mutation, no global state, no I/O, no side effects.

    Sizing pipeline (fixed order):
        1.  HALT -> return immediately.
        2.  requested_notional = quantity * current_price
        3.  base_cap = nav * max_position_pct_nav
        4.  vol_cap_scalar = min(volatility_target_ann / max(position_vol, 1e-8), 1.0)
                             if position_vol is not None else 1.0
        5.  effective_cap = min(base_cap, base_cap * vol_cap_scalar)
        6.  raw_target = min(requested_notional, effective_cap)
        7.  kelly_target = raw_target * kelly_fraction
        8.  reduce_target = kelly_target * liquidity_haircut_floor  (REDUCE)
                          = kelly_target                             (APPROVE)
        9.  liquidity_floor = requested_notional * liquidity_haircut_floor
        10. target = max(reduce_target, liquidity_floor)

    Args:
        position:     PositionSpec. quantity and current_price derive requested notional.
        portfolio:    PortfolioState. nav used for base cap.
        params:       RiskParameters. All sizing scalars consumed here.
        decision:     RiskDecision from evaluate_position_risk(). Only verdict consumed.
        position_vol: Optional annualised volatility of this position.
                      None -> vol_cap_scalar = 1.0 (no vol adjustment; backward compat).

    Returns:
        PositionSizingResult(allowed, target_notional, reason).
    """
    # ------------------------------------------------------------------
    # Step 1: HALT -- no sizing arithmetic performed.
    # ------------------------------------------------------------------
    if decision.verdict is RiskVerdict.HALT:
        return PositionSizingResult(
            allowed=False,
            target_notional=None,
            reason=decision.verdict,
        )

    # ------------------------------------------------------------------
    # Step 2: Requested notional.
    # quantity and current_price are finite and > 0 (domain-validated).
    # ------------------------------------------------------------------
    requested_notional: float = position.quantity * position.current_price

    # ------------------------------------------------------------------
    # Step 3: Base position cap.
    # nav and max_position_pct_nav are finite and > 0 (domain-validated).
    # ------------------------------------------------------------------
    base_cap: float = portfolio.nav * params.max_position_pct_nav

    # ------------------------------------------------------------------
    # Step 4: Volatility-adjusted cap scalar.
    # position_vol=None -> scalar=1.0 (identity; preserves Phase 7C output).
    # max(position_vol, 1e-8) guards against division by zero or near-zero.
    # min(..., 1.0) prevents the scalar from exceeding 1 (no vol-based leverage).
    # ------------------------------------------------------------------
    if position_vol is not None:
        vol_cap_scalar: float = min(
            params.volatility_target_ann / max(position_vol, 1e-8),
            2.0,
        )
    else:
        vol_cap_scalar = 1.0

    # ------------------------------------------------------------------
    # Step 5: Effective cap.
    # vol_cap = base_cap * scalar. effective_cap = min(base_cap, vol_cap).
    # When scalar=1.0: vol_cap == base_cap -> effective_cap == base_cap.
    # ------------------------------------------------------------------
    effective_cap: float = min(base_cap, base_cap * vol_cap_scalar)

    # ------------------------------------------------------------------
    # Step 6: Raw target capped at effective_cap.
    # ------------------------------------------------------------------
    raw_target: float = min(requested_notional, effective_cap)

    # ------------------------------------------------------------------
    # Step 7: Kelly fraction.
    # kelly_fraction is validated in (0.0, 1.0] by RiskParameters.
    # No guard needed; always reduces or preserves raw_target.
    # ------------------------------------------------------------------
    kelly_target: float = raw_target * params.kelly_fraction

    # ------------------------------------------------------------------
    # Step 8: REDUCE multiplier (conditional on clamping).
    # REDUCE applies liquidity_haircut_floor only when the position was
    # clamped by the cap (raw_target < requested_notional).
    # When not clamped (position already within cap), REDUCE passes
    # kelly_target through unchanged -- no additional compression.
    # APPROVE always passes kelly_target through unchanged.
    # liquidity_haircut_floor validated in (0.0, 1.0] by RiskParameters.
    # ------------------------------------------------------------------
    _was_clamped: bool = raw_target < requested_notional
    if decision.verdict is RiskVerdict.REDUCE and _was_clamped:
        reduce_target: float = kelly_target * params.liquidity_haircut_floor
    else:
        reduce_target = kelly_target

    # ------------------------------------------------------------------
    # Step 9: Liquidity floor guarantee (INV-SZ-05).
    # Even after Kelly and REDUCE compression, target must be at least
    # liquidity_haircut_floor fraction of the original requested notional.
    # This prevents compound discounting from compressing to near-zero.
    # ------------------------------------------------------------------
    liquidity_floor_value: float = requested_notional * params.liquidity_haircut_floor
    target: float = max(reduce_target, liquidity_floor_value)

    return PositionSizingResult(
        allowed=True,
        target_notional=target,
        reason=decision.verdict,
    )


# =============================================================================
# SECTION 2 -- SIZE POSITION
# =============================================================================

def x_size_position__mutmut_25(
    position:     PositionSpec,
    portfolio:    PortfolioState,
    params:       RiskParameters,
    decision:     RiskDecision,
    position_vol: Optional[float] = None,
) -> PositionSizingResult:
    """
    Compute the allowed position size given a pre-evaluated RiskDecision.

    Pure function: reads arguments, returns PositionSizingResult.
    No mutation, no global state, no I/O, no side effects.

    Sizing pipeline (fixed order):
        1.  HALT -> return immediately.
        2.  requested_notional = quantity * current_price
        3.  base_cap = nav * max_position_pct_nav
        4.  vol_cap_scalar = min(volatility_target_ann / max(position_vol, 1e-8), 1.0)
                             if position_vol is not None else 1.0
        5.  effective_cap = min(base_cap, base_cap * vol_cap_scalar)
        6.  raw_target = min(requested_notional, effective_cap)
        7.  kelly_target = raw_target * kelly_fraction
        8.  reduce_target = kelly_target * liquidity_haircut_floor  (REDUCE)
                          = kelly_target                             (APPROVE)
        9.  liquidity_floor = requested_notional * liquidity_haircut_floor
        10. target = max(reduce_target, liquidity_floor)

    Args:
        position:     PositionSpec. quantity and current_price derive requested notional.
        portfolio:    PortfolioState. nav used for base cap.
        params:       RiskParameters. All sizing scalars consumed here.
        decision:     RiskDecision from evaluate_position_risk(). Only verdict consumed.
        position_vol: Optional annualised volatility of this position.
                      None -> vol_cap_scalar = 1.0 (no vol adjustment; backward compat).

    Returns:
        PositionSizingResult(allowed, target_notional, reason).
    """
    # ------------------------------------------------------------------
    # Step 1: HALT -- no sizing arithmetic performed.
    # ------------------------------------------------------------------
    if decision.verdict is RiskVerdict.HALT:
        return PositionSizingResult(
            allowed=False,
            target_notional=None,
            reason=decision.verdict,
        )

    # ------------------------------------------------------------------
    # Step 2: Requested notional.
    # quantity and current_price are finite and > 0 (domain-validated).
    # ------------------------------------------------------------------
    requested_notional: float = position.quantity * position.current_price

    # ------------------------------------------------------------------
    # Step 3: Base position cap.
    # nav and max_position_pct_nav are finite and > 0 (domain-validated).
    # ------------------------------------------------------------------
    base_cap: float = portfolio.nav * params.max_position_pct_nav

    # ------------------------------------------------------------------
    # Step 4: Volatility-adjusted cap scalar.
    # position_vol=None -> scalar=1.0 (identity; preserves Phase 7C output).
    # max(position_vol, 1e-8) guards against division by zero or near-zero.
    # min(..., 1.0) prevents the scalar from exceeding 1 (no vol-based leverage).
    # ------------------------------------------------------------------
    if position_vol is not None:
        vol_cap_scalar: float = min(
            params.volatility_target_ann / max(position_vol, 1e-8),
            1.0,
        )
    else:
        vol_cap_scalar = None

    # ------------------------------------------------------------------
    # Step 5: Effective cap.
    # vol_cap = base_cap * scalar. effective_cap = min(base_cap, vol_cap).
    # When scalar=1.0: vol_cap == base_cap -> effective_cap == base_cap.
    # ------------------------------------------------------------------
    effective_cap: float = min(base_cap, base_cap * vol_cap_scalar)

    # ------------------------------------------------------------------
    # Step 6: Raw target capped at effective_cap.
    # ------------------------------------------------------------------
    raw_target: float = min(requested_notional, effective_cap)

    # ------------------------------------------------------------------
    # Step 7: Kelly fraction.
    # kelly_fraction is validated in (0.0, 1.0] by RiskParameters.
    # No guard needed; always reduces or preserves raw_target.
    # ------------------------------------------------------------------
    kelly_target: float = raw_target * params.kelly_fraction

    # ------------------------------------------------------------------
    # Step 8: REDUCE multiplier (conditional on clamping).
    # REDUCE applies liquidity_haircut_floor only when the position was
    # clamped by the cap (raw_target < requested_notional).
    # When not clamped (position already within cap), REDUCE passes
    # kelly_target through unchanged -- no additional compression.
    # APPROVE always passes kelly_target through unchanged.
    # liquidity_haircut_floor validated in (0.0, 1.0] by RiskParameters.
    # ------------------------------------------------------------------
    _was_clamped: bool = raw_target < requested_notional
    if decision.verdict is RiskVerdict.REDUCE and _was_clamped:
        reduce_target: float = kelly_target * params.liquidity_haircut_floor
    else:
        reduce_target = kelly_target

    # ------------------------------------------------------------------
    # Step 9: Liquidity floor guarantee (INV-SZ-05).
    # Even after Kelly and REDUCE compression, target must be at least
    # liquidity_haircut_floor fraction of the original requested notional.
    # This prevents compound discounting from compressing to near-zero.
    # ------------------------------------------------------------------
    liquidity_floor_value: float = requested_notional * params.liquidity_haircut_floor
    target: float = max(reduce_target, liquidity_floor_value)

    return PositionSizingResult(
        allowed=True,
        target_notional=target,
        reason=decision.verdict,
    )


# =============================================================================
# SECTION 2 -- SIZE POSITION
# =============================================================================

def x_size_position__mutmut_26(
    position:     PositionSpec,
    portfolio:    PortfolioState,
    params:       RiskParameters,
    decision:     RiskDecision,
    position_vol: Optional[float] = None,
) -> PositionSizingResult:
    """
    Compute the allowed position size given a pre-evaluated RiskDecision.

    Pure function: reads arguments, returns PositionSizingResult.
    No mutation, no global state, no I/O, no side effects.

    Sizing pipeline (fixed order):
        1.  HALT -> return immediately.
        2.  requested_notional = quantity * current_price
        3.  base_cap = nav * max_position_pct_nav
        4.  vol_cap_scalar = min(volatility_target_ann / max(position_vol, 1e-8), 1.0)
                             if position_vol is not None else 1.0
        5.  effective_cap = min(base_cap, base_cap * vol_cap_scalar)
        6.  raw_target = min(requested_notional, effective_cap)
        7.  kelly_target = raw_target * kelly_fraction
        8.  reduce_target = kelly_target * liquidity_haircut_floor  (REDUCE)
                          = kelly_target                             (APPROVE)
        9.  liquidity_floor = requested_notional * liquidity_haircut_floor
        10. target = max(reduce_target, liquidity_floor)

    Args:
        position:     PositionSpec. quantity and current_price derive requested notional.
        portfolio:    PortfolioState. nav used for base cap.
        params:       RiskParameters. All sizing scalars consumed here.
        decision:     RiskDecision from evaluate_position_risk(). Only verdict consumed.
        position_vol: Optional annualised volatility of this position.
                      None -> vol_cap_scalar = 1.0 (no vol adjustment; backward compat).

    Returns:
        PositionSizingResult(allowed, target_notional, reason).
    """
    # ------------------------------------------------------------------
    # Step 1: HALT -- no sizing arithmetic performed.
    # ------------------------------------------------------------------
    if decision.verdict is RiskVerdict.HALT:
        return PositionSizingResult(
            allowed=False,
            target_notional=None,
            reason=decision.verdict,
        )

    # ------------------------------------------------------------------
    # Step 2: Requested notional.
    # quantity and current_price are finite and > 0 (domain-validated).
    # ------------------------------------------------------------------
    requested_notional: float = position.quantity * position.current_price

    # ------------------------------------------------------------------
    # Step 3: Base position cap.
    # nav and max_position_pct_nav are finite and > 0 (domain-validated).
    # ------------------------------------------------------------------
    base_cap: float = portfolio.nav * params.max_position_pct_nav

    # ------------------------------------------------------------------
    # Step 4: Volatility-adjusted cap scalar.
    # position_vol=None -> scalar=1.0 (identity; preserves Phase 7C output).
    # max(position_vol, 1e-8) guards against division by zero or near-zero.
    # min(..., 1.0) prevents the scalar from exceeding 1 (no vol-based leverage).
    # ------------------------------------------------------------------
    if position_vol is not None:
        vol_cap_scalar: float = min(
            params.volatility_target_ann / max(position_vol, 1e-8),
            1.0,
        )
    else:
        vol_cap_scalar = 2.0

    # ------------------------------------------------------------------
    # Step 5: Effective cap.
    # vol_cap = base_cap * scalar. effective_cap = min(base_cap, vol_cap).
    # When scalar=1.0: vol_cap == base_cap -> effective_cap == base_cap.
    # ------------------------------------------------------------------
    effective_cap: float = min(base_cap, base_cap * vol_cap_scalar)

    # ------------------------------------------------------------------
    # Step 6: Raw target capped at effective_cap.
    # ------------------------------------------------------------------
    raw_target: float = min(requested_notional, effective_cap)

    # ------------------------------------------------------------------
    # Step 7: Kelly fraction.
    # kelly_fraction is validated in (0.0, 1.0] by RiskParameters.
    # No guard needed; always reduces or preserves raw_target.
    # ------------------------------------------------------------------
    kelly_target: float = raw_target * params.kelly_fraction

    # ------------------------------------------------------------------
    # Step 8: REDUCE multiplier (conditional on clamping).
    # REDUCE applies liquidity_haircut_floor only when the position was
    # clamped by the cap (raw_target < requested_notional).
    # When not clamped (position already within cap), REDUCE passes
    # kelly_target through unchanged -- no additional compression.
    # APPROVE always passes kelly_target through unchanged.
    # liquidity_haircut_floor validated in (0.0, 1.0] by RiskParameters.
    # ------------------------------------------------------------------
    _was_clamped: bool = raw_target < requested_notional
    if decision.verdict is RiskVerdict.REDUCE and _was_clamped:
        reduce_target: float = kelly_target * params.liquidity_haircut_floor
    else:
        reduce_target = kelly_target

    # ------------------------------------------------------------------
    # Step 9: Liquidity floor guarantee (INV-SZ-05).
    # Even after Kelly and REDUCE compression, target must be at least
    # liquidity_haircut_floor fraction of the original requested notional.
    # This prevents compound discounting from compressing to near-zero.
    # ------------------------------------------------------------------
    liquidity_floor_value: float = requested_notional * params.liquidity_haircut_floor
    target: float = max(reduce_target, liquidity_floor_value)

    return PositionSizingResult(
        allowed=True,
        target_notional=target,
        reason=decision.verdict,
    )


# =============================================================================
# SECTION 2 -- SIZE POSITION
# =============================================================================

def x_size_position__mutmut_27(
    position:     PositionSpec,
    portfolio:    PortfolioState,
    params:       RiskParameters,
    decision:     RiskDecision,
    position_vol: Optional[float] = None,
) -> PositionSizingResult:
    """
    Compute the allowed position size given a pre-evaluated RiskDecision.

    Pure function: reads arguments, returns PositionSizingResult.
    No mutation, no global state, no I/O, no side effects.

    Sizing pipeline (fixed order):
        1.  HALT -> return immediately.
        2.  requested_notional = quantity * current_price
        3.  base_cap = nav * max_position_pct_nav
        4.  vol_cap_scalar = min(volatility_target_ann / max(position_vol, 1e-8), 1.0)
                             if position_vol is not None else 1.0
        5.  effective_cap = min(base_cap, base_cap * vol_cap_scalar)
        6.  raw_target = min(requested_notional, effective_cap)
        7.  kelly_target = raw_target * kelly_fraction
        8.  reduce_target = kelly_target * liquidity_haircut_floor  (REDUCE)
                          = kelly_target                             (APPROVE)
        9.  liquidity_floor = requested_notional * liquidity_haircut_floor
        10. target = max(reduce_target, liquidity_floor)

    Args:
        position:     PositionSpec. quantity and current_price derive requested notional.
        portfolio:    PortfolioState. nav used for base cap.
        params:       RiskParameters. All sizing scalars consumed here.
        decision:     RiskDecision from evaluate_position_risk(). Only verdict consumed.
        position_vol: Optional annualised volatility of this position.
                      None -> vol_cap_scalar = 1.0 (no vol adjustment; backward compat).

    Returns:
        PositionSizingResult(allowed, target_notional, reason).
    """
    # ------------------------------------------------------------------
    # Step 1: HALT -- no sizing arithmetic performed.
    # ------------------------------------------------------------------
    if decision.verdict is RiskVerdict.HALT:
        return PositionSizingResult(
            allowed=False,
            target_notional=None,
            reason=decision.verdict,
        )

    # ------------------------------------------------------------------
    # Step 2: Requested notional.
    # quantity and current_price are finite and > 0 (domain-validated).
    # ------------------------------------------------------------------
    requested_notional: float = position.quantity * position.current_price

    # ------------------------------------------------------------------
    # Step 3: Base position cap.
    # nav and max_position_pct_nav are finite and > 0 (domain-validated).
    # ------------------------------------------------------------------
    base_cap: float = portfolio.nav * params.max_position_pct_nav

    # ------------------------------------------------------------------
    # Step 4: Volatility-adjusted cap scalar.
    # position_vol=None -> scalar=1.0 (identity; preserves Phase 7C output).
    # max(position_vol, 1e-8) guards against division by zero or near-zero.
    # min(..., 1.0) prevents the scalar from exceeding 1 (no vol-based leverage).
    # ------------------------------------------------------------------
    if position_vol is not None:
        vol_cap_scalar: float = min(
            params.volatility_target_ann / max(position_vol, 1e-8),
            1.0,
        )
    else:
        vol_cap_scalar = 1.0

    # ------------------------------------------------------------------
    # Step 5: Effective cap.
    # vol_cap = base_cap * scalar. effective_cap = min(base_cap, vol_cap).
    # When scalar=1.0: vol_cap == base_cap -> effective_cap == base_cap.
    # ------------------------------------------------------------------
    effective_cap: float = None

    # ------------------------------------------------------------------
    # Step 6: Raw target capped at effective_cap.
    # ------------------------------------------------------------------
    raw_target: float = min(requested_notional, effective_cap)

    # ------------------------------------------------------------------
    # Step 7: Kelly fraction.
    # kelly_fraction is validated in (0.0, 1.0] by RiskParameters.
    # No guard needed; always reduces or preserves raw_target.
    # ------------------------------------------------------------------
    kelly_target: float = raw_target * params.kelly_fraction

    # ------------------------------------------------------------------
    # Step 8: REDUCE multiplier (conditional on clamping).
    # REDUCE applies liquidity_haircut_floor only when the position was
    # clamped by the cap (raw_target < requested_notional).
    # When not clamped (position already within cap), REDUCE passes
    # kelly_target through unchanged -- no additional compression.
    # APPROVE always passes kelly_target through unchanged.
    # liquidity_haircut_floor validated in (0.0, 1.0] by RiskParameters.
    # ------------------------------------------------------------------
    _was_clamped: bool = raw_target < requested_notional
    if decision.verdict is RiskVerdict.REDUCE and _was_clamped:
        reduce_target: float = kelly_target * params.liquidity_haircut_floor
    else:
        reduce_target = kelly_target

    # ------------------------------------------------------------------
    # Step 9: Liquidity floor guarantee (INV-SZ-05).
    # Even after Kelly and REDUCE compression, target must be at least
    # liquidity_haircut_floor fraction of the original requested notional.
    # This prevents compound discounting from compressing to near-zero.
    # ------------------------------------------------------------------
    liquidity_floor_value: float = requested_notional * params.liquidity_haircut_floor
    target: float = max(reduce_target, liquidity_floor_value)

    return PositionSizingResult(
        allowed=True,
        target_notional=target,
        reason=decision.verdict,
    )


# =============================================================================
# SECTION 2 -- SIZE POSITION
# =============================================================================

def x_size_position__mutmut_28(
    position:     PositionSpec,
    portfolio:    PortfolioState,
    params:       RiskParameters,
    decision:     RiskDecision,
    position_vol: Optional[float] = None,
) -> PositionSizingResult:
    """
    Compute the allowed position size given a pre-evaluated RiskDecision.

    Pure function: reads arguments, returns PositionSizingResult.
    No mutation, no global state, no I/O, no side effects.

    Sizing pipeline (fixed order):
        1.  HALT -> return immediately.
        2.  requested_notional = quantity * current_price
        3.  base_cap = nav * max_position_pct_nav
        4.  vol_cap_scalar = min(volatility_target_ann / max(position_vol, 1e-8), 1.0)
                             if position_vol is not None else 1.0
        5.  effective_cap = min(base_cap, base_cap * vol_cap_scalar)
        6.  raw_target = min(requested_notional, effective_cap)
        7.  kelly_target = raw_target * kelly_fraction
        8.  reduce_target = kelly_target * liquidity_haircut_floor  (REDUCE)
                          = kelly_target                             (APPROVE)
        9.  liquidity_floor = requested_notional * liquidity_haircut_floor
        10. target = max(reduce_target, liquidity_floor)

    Args:
        position:     PositionSpec. quantity and current_price derive requested notional.
        portfolio:    PortfolioState. nav used for base cap.
        params:       RiskParameters. All sizing scalars consumed here.
        decision:     RiskDecision from evaluate_position_risk(). Only verdict consumed.
        position_vol: Optional annualised volatility of this position.
                      None -> vol_cap_scalar = 1.0 (no vol adjustment; backward compat).

    Returns:
        PositionSizingResult(allowed, target_notional, reason).
    """
    # ------------------------------------------------------------------
    # Step 1: HALT -- no sizing arithmetic performed.
    # ------------------------------------------------------------------
    if decision.verdict is RiskVerdict.HALT:
        return PositionSizingResult(
            allowed=False,
            target_notional=None,
            reason=decision.verdict,
        )

    # ------------------------------------------------------------------
    # Step 2: Requested notional.
    # quantity and current_price are finite and > 0 (domain-validated).
    # ------------------------------------------------------------------
    requested_notional: float = position.quantity * position.current_price

    # ------------------------------------------------------------------
    # Step 3: Base position cap.
    # nav and max_position_pct_nav are finite and > 0 (domain-validated).
    # ------------------------------------------------------------------
    base_cap: float = portfolio.nav * params.max_position_pct_nav

    # ------------------------------------------------------------------
    # Step 4: Volatility-adjusted cap scalar.
    # position_vol=None -> scalar=1.0 (identity; preserves Phase 7C output).
    # max(position_vol, 1e-8) guards against division by zero or near-zero.
    # min(..., 1.0) prevents the scalar from exceeding 1 (no vol-based leverage).
    # ------------------------------------------------------------------
    if position_vol is not None:
        vol_cap_scalar: float = min(
            params.volatility_target_ann / max(position_vol, 1e-8),
            1.0,
        )
    else:
        vol_cap_scalar = 1.0

    # ------------------------------------------------------------------
    # Step 5: Effective cap.
    # vol_cap = base_cap * scalar. effective_cap = min(base_cap, vol_cap).
    # When scalar=1.0: vol_cap == base_cap -> effective_cap == base_cap.
    # ------------------------------------------------------------------
    effective_cap: float = min(None, base_cap * vol_cap_scalar)

    # ------------------------------------------------------------------
    # Step 6: Raw target capped at effective_cap.
    # ------------------------------------------------------------------
    raw_target: float = min(requested_notional, effective_cap)

    # ------------------------------------------------------------------
    # Step 7: Kelly fraction.
    # kelly_fraction is validated in (0.0, 1.0] by RiskParameters.
    # No guard needed; always reduces or preserves raw_target.
    # ------------------------------------------------------------------
    kelly_target: float = raw_target * params.kelly_fraction

    # ------------------------------------------------------------------
    # Step 8: REDUCE multiplier (conditional on clamping).
    # REDUCE applies liquidity_haircut_floor only when the position was
    # clamped by the cap (raw_target < requested_notional).
    # When not clamped (position already within cap), REDUCE passes
    # kelly_target through unchanged -- no additional compression.
    # APPROVE always passes kelly_target through unchanged.
    # liquidity_haircut_floor validated in (0.0, 1.0] by RiskParameters.
    # ------------------------------------------------------------------
    _was_clamped: bool = raw_target < requested_notional
    if decision.verdict is RiskVerdict.REDUCE and _was_clamped:
        reduce_target: float = kelly_target * params.liquidity_haircut_floor
    else:
        reduce_target = kelly_target

    # ------------------------------------------------------------------
    # Step 9: Liquidity floor guarantee (INV-SZ-05).
    # Even after Kelly and REDUCE compression, target must be at least
    # liquidity_haircut_floor fraction of the original requested notional.
    # This prevents compound discounting from compressing to near-zero.
    # ------------------------------------------------------------------
    liquidity_floor_value: float = requested_notional * params.liquidity_haircut_floor
    target: float = max(reduce_target, liquidity_floor_value)

    return PositionSizingResult(
        allowed=True,
        target_notional=target,
        reason=decision.verdict,
    )


# =============================================================================
# SECTION 2 -- SIZE POSITION
# =============================================================================

def x_size_position__mutmut_29(
    position:     PositionSpec,
    portfolio:    PortfolioState,
    params:       RiskParameters,
    decision:     RiskDecision,
    position_vol: Optional[float] = None,
) -> PositionSizingResult:
    """
    Compute the allowed position size given a pre-evaluated RiskDecision.

    Pure function: reads arguments, returns PositionSizingResult.
    No mutation, no global state, no I/O, no side effects.

    Sizing pipeline (fixed order):
        1.  HALT -> return immediately.
        2.  requested_notional = quantity * current_price
        3.  base_cap = nav * max_position_pct_nav
        4.  vol_cap_scalar = min(volatility_target_ann / max(position_vol, 1e-8), 1.0)
                             if position_vol is not None else 1.0
        5.  effective_cap = min(base_cap, base_cap * vol_cap_scalar)
        6.  raw_target = min(requested_notional, effective_cap)
        7.  kelly_target = raw_target * kelly_fraction
        8.  reduce_target = kelly_target * liquidity_haircut_floor  (REDUCE)
                          = kelly_target                             (APPROVE)
        9.  liquidity_floor = requested_notional * liquidity_haircut_floor
        10. target = max(reduce_target, liquidity_floor)

    Args:
        position:     PositionSpec. quantity and current_price derive requested notional.
        portfolio:    PortfolioState. nav used for base cap.
        params:       RiskParameters. All sizing scalars consumed here.
        decision:     RiskDecision from evaluate_position_risk(). Only verdict consumed.
        position_vol: Optional annualised volatility of this position.
                      None -> vol_cap_scalar = 1.0 (no vol adjustment; backward compat).

    Returns:
        PositionSizingResult(allowed, target_notional, reason).
    """
    # ------------------------------------------------------------------
    # Step 1: HALT -- no sizing arithmetic performed.
    # ------------------------------------------------------------------
    if decision.verdict is RiskVerdict.HALT:
        return PositionSizingResult(
            allowed=False,
            target_notional=None,
            reason=decision.verdict,
        )

    # ------------------------------------------------------------------
    # Step 2: Requested notional.
    # quantity and current_price are finite and > 0 (domain-validated).
    # ------------------------------------------------------------------
    requested_notional: float = position.quantity * position.current_price

    # ------------------------------------------------------------------
    # Step 3: Base position cap.
    # nav and max_position_pct_nav are finite and > 0 (domain-validated).
    # ------------------------------------------------------------------
    base_cap: float = portfolio.nav * params.max_position_pct_nav

    # ------------------------------------------------------------------
    # Step 4: Volatility-adjusted cap scalar.
    # position_vol=None -> scalar=1.0 (identity; preserves Phase 7C output).
    # max(position_vol, 1e-8) guards against division by zero or near-zero.
    # min(..., 1.0) prevents the scalar from exceeding 1 (no vol-based leverage).
    # ------------------------------------------------------------------
    if position_vol is not None:
        vol_cap_scalar: float = min(
            params.volatility_target_ann / max(position_vol, 1e-8),
            1.0,
        )
    else:
        vol_cap_scalar = 1.0

    # ------------------------------------------------------------------
    # Step 5: Effective cap.
    # vol_cap = base_cap * scalar. effective_cap = min(base_cap, vol_cap).
    # When scalar=1.0: vol_cap == base_cap -> effective_cap == base_cap.
    # ------------------------------------------------------------------
    effective_cap: float = min(base_cap, None)

    # ------------------------------------------------------------------
    # Step 6: Raw target capped at effective_cap.
    # ------------------------------------------------------------------
    raw_target: float = min(requested_notional, effective_cap)

    # ------------------------------------------------------------------
    # Step 7: Kelly fraction.
    # kelly_fraction is validated in (0.0, 1.0] by RiskParameters.
    # No guard needed; always reduces or preserves raw_target.
    # ------------------------------------------------------------------
    kelly_target: float = raw_target * params.kelly_fraction

    # ------------------------------------------------------------------
    # Step 8: REDUCE multiplier (conditional on clamping).
    # REDUCE applies liquidity_haircut_floor only when the position was
    # clamped by the cap (raw_target < requested_notional).
    # When not clamped (position already within cap), REDUCE passes
    # kelly_target through unchanged -- no additional compression.
    # APPROVE always passes kelly_target through unchanged.
    # liquidity_haircut_floor validated in (0.0, 1.0] by RiskParameters.
    # ------------------------------------------------------------------
    _was_clamped: bool = raw_target < requested_notional
    if decision.verdict is RiskVerdict.REDUCE and _was_clamped:
        reduce_target: float = kelly_target * params.liquidity_haircut_floor
    else:
        reduce_target = kelly_target

    # ------------------------------------------------------------------
    # Step 9: Liquidity floor guarantee (INV-SZ-05).
    # Even after Kelly and REDUCE compression, target must be at least
    # liquidity_haircut_floor fraction of the original requested notional.
    # This prevents compound discounting from compressing to near-zero.
    # ------------------------------------------------------------------
    liquidity_floor_value: float = requested_notional * params.liquidity_haircut_floor
    target: float = max(reduce_target, liquidity_floor_value)

    return PositionSizingResult(
        allowed=True,
        target_notional=target,
        reason=decision.verdict,
    )


# =============================================================================
# SECTION 2 -- SIZE POSITION
# =============================================================================

def x_size_position__mutmut_30(
    position:     PositionSpec,
    portfolio:    PortfolioState,
    params:       RiskParameters,
    decision:     RiskDecision,
    position_vol: Optional[float] = None,
) -> PositionSizingResult:
    """
    Compute the allowed position size given a pre-evaluated RiskDecision.

    Pure function: reads arguments, returns PositionSizingResult.
    No mutation, no global state, no I/O, no side effects.

    Sizing pipeline (fixed order):
        1.  HALT -> return immediately.
        2.  requested_notional = quantity * current_price
        3.  base_cap = nav * max_position_pct_nav
        4.  vol_cap_scalar = min(volatility_target_ann / max(position_vol, 1e-8), 1.0)
                             if position_vol is not None else 1.0
        5.  effective_cap = min(base_cap, base_cap * vol_cap_scalar)
        6.  raw_target = min(requested_notional, effective_cap)
        7.  kelly_target = raw_target * kelly_fraction
        8.  reduce_target = kelly_target * liquidity_haircut_floor  (REDUCE)
                          = kelly_target                             (APPROVE)
        9.  liquidity_floor = requested_notional * liquidity_haircut_floor
        10. target = max(reduce_target, liquidity_floor)

    Args:
        position:     PositionSpec. quantity and current_price derive requested notional.
        portfolio:    PortfolioState. nav used for base cap.
        params:       RiskParameters. All sizing scalars consumed here.
        decision:     RiskDecision from evaluate_position_risk(). Only verdict consumed.
        position_vol: Optional annualised volatility of this position.
                      None -> vol_cap_scalar = 1.0 (no vol adjustment; backward compat).

    Returns:
        PositionSizingResult(allowed, target_notional, reason).
    """
    # ------------------------------------------------------------------
    # Step 1: HALT -- no sizing arithmetic performed.
    # ------------------------------------------------------------------
    if decision.verdict is RiskVerdict.HALT:
        return PositionSizingResult(
            allowed=False,
            target_notional=None,
            reason=decision.verdict,
        )

    # ------------------------------------------------------------------
    # Step 2: Requested notional.
    # quantity and current_price are finite and > 0 (domain-validated).
    # ------------------------------------------------------------------
    requested_notional: float = position.quantity * position.current_price

    # ------------------------------------------------------------------
    # Step 3: Base position cap.
    # nav and max_position_pct_nav are finite and > 0 (domain-validated).
    # ------------------------------------------------------------------
    base_cap: float = portfolio.nav * params.max_position_pct_nav

    # ------------------------------------------------------------------
    # Step 4: Volatility-adjusted cap scalar.
    # position_vol=None -> scalar=1.0 (identity; preserves Phase 7C output).
    # max(position_vol, 1e-8) guards against division by zero or near-zero.
    # min(..., 1.0) prevents the scalar from exceeding 1 (no vol-based leverage).
    # ------------------------------------------------------------------
    if position_vol is not None:
        vol_cap_scalar: float = min(
            params.volatility_target_ann / max(position_vol, 1e-8),
            1.0,
        )
    else:
        vol_cap_scalar = 1.0

    # ------------------------------------------------------------------
    # Step 5: Effective cap.
    # vol_cap = base_cap * scalar. effective_cap = min(base_cap, vol_cap).
    # When scalar=1.0: vol_cap == base_cap -> effective_cap == base_cap.
    # ------------------------------------------------------------------
    effective_cap: float = min(base_cap * vol_cap_scalar)

    # ------------------------------------------------------------------
    # Step 6: Raw target capped at effective_cap.
    # ------------------------------------------------------------------
    raw_target: float = min(requested_notional, effective_cap)

    # ------------------------------------------------------------------
    # Step 7: Kelly fraction.
    # kelly_fraction is validated in (0.0, 1.0] by RiskParameters.
    # No guard needed; always reduces or preserves raw_target.
    # ------------------------------------------------------------------
    kelly_target: float = raw_target * params.kelly_fraction

    # ------------------------------------------------------------------
    # Step 8: REDUCE multiplier (conditional on clamping).
    # REDUCE applies liquidity_haircut_floor only when the position was
    # clamped by the cap (raw_target < requested_notional).
    # When not clamped (position already within cap), REDUCE passes
    # kelly_target through unchanged -- no additional compression.
    # APPROVE always passes kelly_target through unchanged.
    # liquidity_haircut_floor validated in (0.0, 1.0] by RiskParameters.
    # ------------------------------------------------------------------
    _was_clamped: bool = raw_target < requested_notional
    if decision.verdict is RiskVerdict.REDUCE and _was_clamped:
        reduce_target: float = kelly_target * params.liquidity_haircut_floor
    else:
        reduce_target = kelly_target

    # ------------------------------------------------------------------
    # Step 9: Liquidity floor guarantee (INV-SZ-05).
    # Even after Kelly and REDUCE compression, target must be at least
    # liquidity_haircut_floor fraction of the original requested notional.
    # This prevents compound discounting from compressing to near-zero.
    # ------------------------------------------------------------------
    liquidity_floor_value: float = requested_notional * params.liquidity_haircut_floor
    target: float = max(reduce_target, liquidity_floor_value)

    return PositionSizingResult(
        allowed=True,
        target_notional=target,
        reason=decision.verdict,
    )


# =============================================================================
# SECTION 2 -- SIZE POSITION
# =============================================================================

def x_size_position__mutmut_31(
    position:     PositionSpec,
    portfolio:    PortfolioState,
    params:       RiskParameters,
    decision:     RiskDecision,
    position_vol: Optional[float] = None,
) -> PositionSizingResult:
    """
    Compute the allowed position size given a pre-evaluated RiskDecision.

    Pure function: reads arguments, returns PositionSizingResult.
    No mutation, no global state, no I/O, no side effects.

    Sizing pipeline (fixed order):
        1.  HALT -> return immediately.
        2.  requested_notional = quantity * current_price
        3.  base_cap = nav * max_position_pct_nav
        4.  vol_cap_scalar = min(volatility_target_ann / max(position_vol, 1e-8), 1.0)
                             if position_vol is not None else 1.0
        5.  effective_cap = min(base_cap, base_cap * vol_cap_scalar)
        6.  raw_target = min(requested_notional, effective_cap)
        7.  kelly_target = raw_target * kelly_fraction
        8.  reduce_target = kelly_target * liquidity_haircut_floor  (REDUCE)
                          = kelly_target                             (APPROVE)
        9.  liquidity_floor = requested_notional * liquidity_haircut_floor
        10. target = max(reduce_target, liquidity_floor)

    Args:
        position:     PositionSpec. quantity and current_price derive requested notional.
        portfolio:    PortfolioState. nav used for base cap.
        params:       RiskParameters. All sizing scalars consumed here.
        decision:     RiskDecision from evaluate_position_risk(). Only verdict consumed.
        position_vol: Optional annualised volatility of this position.
                      None -> vol_cap_scalar = 1.0 (no vol adjustment; backward compat).

    Returns:
        PositionSizingResult(allowed, target_notional, reason).
    """
    # ------------------------------------------------------------------
    # Step 1: HALT -- no sizing arithmetic performed.
    # ------------------------------------------------------------------
    if decision.verdict is RiskVerdict.HALT:
        return PositionSizingResult(
            allowed=False,
            target_notional=None,
            reason=decision.verdict,
        )

    # ------------------------------------------------------------------
    # Step 2: Requested notional.
    # quantity and current_price are finite and > 0 (domain-validated).
    # ------------------------------------------------------------------
    requested_notional: float = position.quantity * position.current_price

    # ------------------------------------------------------------------
    # Step 3: Base position cap.
    # nav and max_position_pct_nav are finite and > 0 (domain-validated).
    # ------------------------------------------------------------------
    base_cap: float = portfolio.nav * params.max_position_pct_nav

    # ------------------------------------------------------------------
    # Step 4: Volatility-adjusted cap scalar.
    # position_vol=None -> scalar=1.0 (identity; preserves Phase 7C output).
    # max(position_vol, 1e-8) guards against division by zero or near-zero.
    # min(..., 1.0) prevents the scalar from exceeding 1 (no vol-based leverage).
    # ------------------------------------------------------------------
    if position_vol is not None:
        vol_cap_scalar: float = min(
            params.volatility_target_ann / max(position_vol, 1e-8),
            1.0,
        )
    else:
        vol_cap_scalar = 1.0

    # ------------------------------------------------------------------
    # Step 5: Effective cap.
    # vol_cap = base_cap * scalar. effective_cap = min(base_cap, vol_cap).
    # When scalar=1.0: vol_cap == base_cap -> effective_cap == base_cap.
    # ------------------------------------------------------------------
    effective_cap: float = min(base_cap, )

    # ------------------------------------------------------------------
    # Step 6: Raw target capped at effective_cap.
    # ------------------------------------------------------------------
    raw_target: float = min(requested_notional, effective_cap)

    # ------------------------------------------------------------------
    # Step 7: Kelly fraction.
    # kelly_fraction is validated in (0.0, 1.0] by RiskParameters.
    # No guard needed; always reduces or preserves raw_target.
    # ------------------------------------------------------------------
    kelly_target: float = raw_target * params.kelly_fraction

    # ------------------------------------------------------------------
    # Step 8: REDUCE multiplier (conditional on clamping).
    # REDUCE applies liquidity_haircut_floor only when the position was
    # clamped by the cap (raw_target < requested_notional).
    # When not clamped (position already within cap), REDUCE passes
    # kelly_target through unchanged -- no additional compression.
    # APPROVE always passes kelly_target through unchanged.
    # liquidity_haircut_floor validated in (0.0, 1.0] by RiskParameters.
    # ------------------------------------------------------------------
    _was_clamped: bool = raw_target < requested_notional
    if decision.verdict is RiskVerdict.REDUCE and _was_clamped:
        reduce_target: float = kelly_target * params.liquidity_haircut_floor
    else:
        reduce_target = kelly_target

    # ------------------------------------------------------------------
    # Step 9: Liquidity floor guarantee (INV-SZ-05).
    # Even after Kelly and REDUCE compression, target must be at least
    # liquidity_haircut_floor fraction of the original requested notional.
    # This prevents compound discounting from compressing to near-zero.
    # ------------------------------------------------------------------
    liquidity_floor_value: float = requested_notional * params.liquidity_haircut_floor
    target: float = max(reduce_target, liquidity_floor_value)

    return PositionSizingResult(
        allowed=True,
        target_notional=target,
        reason=decision.verdict,
    )


# =============================================================================
# SECTION 2 -- SIZE POSITION
# =============================================================================

def x_size_position__mutmut_32(
    position:     PositionSpec,
    portfolio:    PortfolioState,
    params:       RiskParameters,
    decision:     RiskDecision,
    position_vol: Optional[float] = None,
) -> PositionSizingResult:
    """
    Compute the allowed position size given a pre-evaluated RiskDecision.

    Pure function: reads arguments, returns PositionSizingResult.
    No mutation, no global state, no I/O, no side effects.

    Sizing pipeline (fixed order):
        1.  HALT -> return immediately.
        2.  requested_notional = quantity * current_price
        3.  base_cap = nav * max_position_pct_nav
        4.  vol_cap_scalar = min(volatility_target_ann / max(position_vol, 1e-8), 1.0)
                             if position_vol is not None else 1.0
        5.  effective_cap = min(base_cap, base_cap * vol_cap_scalar)
        6.  raw_target = min(requested_notional, effective_cap)
        7.  kelly_target = raw_target * kelly_fraction
        8.  reduce_target = kelly_target * liquidity_haircut_floor  (REDUCE)
                          = kelly_target                             (APPROVE)
        9.  liquidity_floor = requested_notional * liquidity_haircut_floor
        10. target = max(reduce_target, liquidity_floor)

    Args:
        position:     PositionSpec. quantity and current_price derive requested notional.
        portfolio:    PortfolioState. nav used for base cap.
        params:       RiskParameters. All sizing scalars consumed here.
        decision:     RiskDecision from evaluate_position_risk(). Only verdict consumed.
        position_vol: Optional annualised volatility of this position.
                      None -> vol_cap_scalar = 1.0 (no vol adjustment; backward compat).

    Returns:
        PositionSizingResult(allowed, target_notional, reason).
    """
    # ------------------------------------------------------------------
    # Step 1: HALT -- no sizing arithmetic performed.
    # ------------------------------------------------------------------
    if decision.verdict is RiskVerdict.HALT:
        return PositionSizingResult(
            allowed=False,
            target_notional=None,
            reason=decision.verdict,
        )

    # ------------------------------------------------------------------
    # Step 2: Requested notional.
    # quantity and current_price are finite and > 0 (domain-validated).
    # ------------------------------------------------------------------
    requested_notional: float = position.quantity * position.current_price

    # ------------------------------------------------------------------
    # Step 3: Base position cap.
    # nav and max_position_pct_nav are finite and > 0 (domain-validated).
    # ------------------------------------------------------------------
    base_cap: float = portfolio.nav * params.max_position_pct_nav

    # ------------------------------------------------------------------
    # Step 4: Volatility-adjusted cap scalar.
    # position_vol=None -> scalar=1.0 (identity; preserves Phase 7C output).
    # max(position_vol, 1e-8) guards against division by zero or near-zero.
    # min(..., 1.0) prevents the scalar from exceeding 1 (no vol-based leverage).
    # ------------------------------------------------------------------
    if position_vol is not None:
        vol_cap_scalar: float = min(
            params.volatility_target_ann / max(position_vol, 1e-8),
            1.0,
        )
    else:
        vol_cap_scalar = 1.0

    # ------------------------------------------------------------------
    # Step 5: Effective cap.
    # vol_cap = base_cap * scalar. effective_cap = min(base_cap, vol_cap).
    # When scalar=1.0: vol_cap == base_cap -> effective_cap == base_cap.
    # ------------------------------------------------------------------
    effective_cap: float = min(base_cap, base_cap / vol_cap_scalar)

    # ------------------------------------------------------------------
    # Step 6: Raw target capped at effective_cap.
    # ------------------------------------------------------------------
    raw_target: float = min(requested_notional, effective_cap)

    # ------------------------------------------------------------------
    # Step 7: Kelly fraction.
    # kelly_fraction is validated in (0.0, 1.0] by RiskParameters.
    # No guard needed; always reduces or preserves raw_target.
    # ------------------------------------------------------------------
    kelly_target: float = raw_target * params.kelly_fraction

    # ------------------------------------------------------------------
    # Step 8: REDUCE multiplier (conditional on clamping).
    # REDUCE applies liquidity_haircut_floor only when the position was
    # clamped by the cap (raw_target < requested_notional).
    # When not clamped (position already within cap), REDUCE passes
    # kelly_target through unchanged -- no additional compression.
    # APPROVE always passes kelly_target through unchanged.
    # liquidity_haircut_floor validated in (0.0, 1.0] by RiskParameters.
    # ------------------------------------------------------------------
    _was_clamped: bool = raw_target < requested_notional
    if decision.verdict is RiskVerdict.REDUCE and _was_clamped:
        reduce_target: float = kelly_target * params.liquidity_haircut_floor
    else:
        reduce_target = kelly_target

    # ------------------------------------------------------------------
    # Step 9: Liquidity floor guarantee (INV-SZ-05).
    # Even after Kelly and REDUCE compression, target must be at least
    # liquidity_haircut_floor fraction of the original requested notional.
    # This prevents compound discounting from compressing to near-zero.
    # ------------------------------------------------------------------
    liquidity_floor_value: float = requested_notional * params.liquidity_haircut_floor
    target: float = max(reduce_target, liquidity_floor_value)

    return PositionSizingResult(
        allowed=True,
        target_notional=target,
        reason=decision.verdict,
    )


# =============================================================================
# SECTION 2 -- SIZE POSITION
# =============================================================================

def x_size_position__mutmut_33(
    position:     PositionSpec,
    portfolio:    PortfolioState,
    params:       RiskParameters,
    decision:     RiskDecision,
    position_vol: Optional[float] = None,
) -> PositionSizingResult:
    """
    Compute the allowed position size given a pre-evaluated RiskDecision.

    Pure function: reads arguments, returns PositionSizingResult.
    No mutation, no global state, no I/O, no side effects.

    Sizing pipeline (fixed order):
        1.  HALT -> return immediately.
        2.  requested_notional = quantity * current_price
        3.  base_cap = nav * max_position_pct_nav
        4.  vol_cap_scalar = min(volatility_target_ann / max(position_vol, 1e-8), 1.0)
                             if position_vol is not None else 1.0
        5.  effective_cap = min(base_cap, base_cap * vol_cap_scalar)
        6.  raw_target = min(requested_notional, effective_cap)
        7.  kelly_target = raw_target * kelly_fraction
        8.  reduce_target = kelly_target * liquidity_haircut_floor  (REDUCE)
                          = kelly_target                             (APPROVE)
        9.  liquidity_floor = requested_notional * liquidity_haircut_floor
        10. target = max(reduce_target, liquidity_floor)

    Args:
        position:     PositionSpec. quantity and current_price derive requested notional.
        portfolio:    PortfolioState. nav used for base cap.
        params:       RiskParameters. All sizing scalars consumed here.
        decision:     RiskDecision from evaluate_position_risk(). Only verdict consumed.
        position_vol: Optional annualised volatility of this position.
                      None -> vol_cap_scalar = 1.0 (no vol adjustment; backward compat).

    Returns:
        PositionSizingResult(allowed, target_notional, reason).
    """
    # ------------------------------------------------------------------
    # Step 1: HALT -- no sizing arithmetic performed.
    # ------------------------------------------------------------------
    if decision.verdict is RiskVerdict.HALT:
        return PositionSizingResult(
            allowed=False,
            target_notional=None,
            reason=decision.verdict,
        )

    # ------------------------------------------------------------------
    # Step 2: Requested notional.
    # quantity and current_price are finite and > 0 (domain-validated).
    # ------------------------------------------------------------------
    requested_notional: float = position.quantity * position.current_price

    # ------------------------------------------------------------------
    # Step 3: Base position cap.
    # nav and max_position_pct_nav are finite and > 0 (domain-validated).
    # ------------------------------------------------------------------
    base_cap: float = portfolio.nav * params.max_position_pct_nav

    # ------------------------------------------------------------------
    # Step 4: Volatility-adjusted cap scalar.
    # position_vol=None -> scalar=1.0 (identity; preserves Phase 7C output).
    # max(position_vol, 1e-8) guards against division by zero or near-zero.
    # min(..., 1.0) prevents the scalar from exceeding 1 (no vol-based leverage).
    # ------------------------------------------------------------------
    if position_vol is not None:
        vol_cap_scalar: float = min(
            params.volatility_target_ann / max(position_vol, 1e-8),
            1.0,
        )
    else:
        vol_cap_scalar = 1.0

    # ------------------------------------------------------------------
    # Step 5: Effective cap.
    # vol_cap = base_cap * scalar. effective_cap = min(base_cap, vol_cap).
    # When scalar=1.0: vol_cap == base_cap -> effective_cap == base_cap.
    # ------------------------------------------------------------------
    effective_cap: float = min(base_cap, base_cap * vol_cap_scalar)

    # ------------------------------------------------------------------
    # Step 6: Raw target capped at effective_cap.
    # ------------------------------------------------------------------
    raw_target: float = None

    # ------------------------------------------------------------------
    # Step 7: Kelly fraction.
    # kelly_fraction is validated in (0.0, 1.0] by RiskParameters.
    # No guard needed; always reduces or preserves raw_target.
    # ------------------------------------------------------------------
    kelly_target: float = raw_target * params.kelly_fraction

    # ------------------------------------------------------------------
    # Step 8: REDUCE multiplier (conditional on clamping).
    # REDUCE applies liquidity_haircut_floor only when the position was
    # clamped by the cap (raw_target < requested_notional).
    # When not clamped (position already within cap), REDUCE passes
    # kelly_target through unchanged -- no additional compression.
    # APPROVE always passes kelly_target through unchanged.
    # liquidity_haircut_floor validated in (0.0, 1.0] by RiskParameters.
    # ------------------------------------------------------------------
    _was_clamped: bool = raw_target < requested_notional
    if decision.verdict is RiskVerdict.REDUCE and _was_clamped:
        reduce_target: float = kelly_target * params.liquidity_haircut_floor
    else:
        reduce_target = kelly_target

    # ------------------------------------------------------------------
    # Step 9: Liquidity floor guarantee (INV-SZ-05).
    # Even after Kelly and REDUCE compression, target must be at least
    # liquidity_haircut_floor fraction of the original requested notional.
    # This prevents compound discounting from compressing to near-zero.
    # ------------------------------------------------------------------
    liquidity_floor_value: float = requested_notional * params.liquidity_haircut_floor
    target: float = max(reduce_target, liquidity_floor_value)

    return PositionSizingResult(
        allowed=True,
        target_notional=target,
        reason=decision.verdict,
    )


# =============================================================================
# SECTION 2 -- SIZE POSITION
# =============================================================================

def x_size_position__mutmut_34(
    position:     PositionSpec,
    portfolio:    PortfolioState,
    params:       RiskParameters,
    decision:     RiskDecision,
    position_vol: Optional[float] = None,
) -> PositionSizingResult:
    """
    Compute the allowed position size given a pre-evaluated RiskDecision.

    Pure function: reads arguments, returns PositionSizingResult.
    No mutation, no global state, no I/O, no side effects.

    Sizing pipeline (fixed order):
        1.  HALT -> return immediately.
        2.  requested_notional = quantity * current_price
        3.  base_cap = nav * max_position_pct_nav
        4.  vol_cap_scalar = min(volatility_target_ann / max(position_vol, 1e-8), 1.0)
                             if position_vol is not None else 1.0
        5.  effective_cap = min(base_cap, base_cap * vol_cap_scalar)
        6.  raw_target = min(requested_notional, effective_cap)
        7.  kelly_target = raw_target * kelly_fraction
        8.  reduce_target = kelly_target * liquidity_haircut_floor  (REDUCE)
                          = kelly_target                             (APPROVE)
        9.  liquidity_floor = requested_notional * liquidity_haircut_floor
        10. target = max(reduce_target, liquidity_floor)

    Args:
        position:     PositionSpec. quantity and current_price derive requested notional.
        portfolio:    PortfolioState. nav used for base cap.
        params:       RiskParameters. All sizing scalars consumed here.
        decision:     RiskDecision from evaluate_position_risk(). Only verdict consumed.
        position_vol: Optional annualised volatility of this position.
                      None -> vol_cap_scalar = 1.0 (no vol adjustment; backward compat).

    Returns:
        PositionSizingResult(allowed, target_notional, reason).
    """
    # ------------------------------------------------------------------
    # Step 1: HALT -- no sizing arithmetic performed.
    # ------------------------------------------------------------------
    if decision.verdict is RiskVerdict.HALT:
        return PositionSizingResult(
            allowed=False,
            target_notional=None,
            reason=decision.verdict,
        )

    # ------------------------------------------------------------------
    # Step 2: Requested notional.
    # quantity and current_price are finite and > 0 (domain-validated).
    # ------------------------------------------------------------------
    requested_notional: float = position.quantity * position.current_price

    # ------------------------------------------------------------------
    # Step 3: Base position cap.
    # nav and max_position_pct_nav are finite and > 0 (domain-validated).
    # ------------------------------------------------------------------
    base_cap: float = portfolio.nav * params.max_position_pct_nav

    # ------------------------------------------------------------------
    # Step 4: Volatility-adjusted cap scalar.
    # position_vol=None -> scalar=1.0 (identity; preserves Phase 7C output).
    # max(position_vol, 1e-8) guards against division by zero or near-zero.
    # min(..., 1.0) prevents the scalar from exceeding 1 (no vol-based leverage).
    # ------------------------------------------------------------------
    if position_vol is not None:
        vol_cap_scalar: float = min(
            params.volatility_target_ann / max(position_vol, 1e-8),
            1.0,
        )
    else:
        vol_cap_scalar = 1.0

    # ------------------------------------------------------------------
    # Step 5: Effective cap.
    # vol_cap = base_cap * scalar. effective_cap = min(base_cap, vol_cap).
    # When scalar=1.0: vol_cap == base_cap -> effective_cap == base_cap.
    # ------------------------------------------------------------------
    effective_cap: float = min(base_cap, base_cap * vol_cap_scalar)

    # ------------------------------------------------------------------
    # Step 6: Raw target capped at effective_cap.
    # ------------------------------------------------------------------
    raw_target: float = min(None, effective_cap)

    # ------------------------------------------------------------------
    # Step 7: Kelly fraction.
    # kelly_fraction is validated in (0.0, 1.0] by RiskParameters.
    # No guard needed; always reduces or preserves raw_target.
    # ------------------------------------------------------------------
    kelly_target: float = raw_target * params.kelly_fraction

    # ------------------------------------------------------------------
    # Step 8: REDUCE multiplier (conditional on clamping).
    # REDUCE applies liquidity_haircut_floor only when the position was
    # clamped by the cap (raw_target < requested_notional).
    # When not clamped (position already within cap), REDUCE passes
    # kelly_target through unchanged -- no additional compression.
    # APPROVE always passes kelly_target through unchanged.
    # liquidity_haircut_floor validated in (0.0, 1.0] by RiskParameters.
    # ------------------------------------------------------------------
    _was_clamped: bool = raw_target < requested_notional
    if decision.verdict is RiskVerdict.REDUCE and _was_clamped:
        reduce_target: float = kelly_target * params.liquidity_haircut_floor
    else:
        reduce_target = kelly_target

    # ------------------------------------------------------------------
    # Step 9: Liquidity floor guarantee (INV-SZ-05).
    # Even after Kelly and REDUCE compression, target must be at least
    # liquidity_haircut_floor fraction of the original requested notional.
    # This prevents compound discounting from compressing to near-zero.
    # ------------------------------------------------------------------
    liquidity_floor_value: float = requested_notional * params.liquidity_haircut_floor
    target: float = max(reduce_target, liquidity_floor_value)

    return PositionSizingResult(
        allowed=True,
        target_notional=target,
        reason=decision.verdict,
    )


# =============================================================================
# SECTION 2 -- SIZE POSITION
# =============================================================================

def x_size_position__mutmut_35(
    position:     PositionSpec,
    portfolio:    PortfolioState,
    params:       RiskParameters,
    decision:     RiskDecision,
    position_vol: Optional[float] = None,
) -> PositionSizingResult:
    """
    Compute the allowed position size given a pre-evaluated RiskDecision.

    Pure function: reads arguments, returns PositionSizingResult.
    No mutation, no global state, no I/O, no side effects.

    Sizing pipeline (fixed order):
        1.  HALT -> return immediately.
        2.  requested_notional = quantity * current_price
        3.  base_cap = nav * max_position_pct_nav
        4.  vol_cap_scalar = min(volatility_target_ann / max(position_vol, 1e-8), 1.0)
                             if position_vol is not None else 1.0
        5.  effective_cap = min(base_cap, base_cap * vol_cap_scalar)
        6.  raw_target = min(requested_notional, effective_cap)
        7.  kelly_target = raw_target * kelly_fraction
        8.  reduce_target = kelly_target * liquidity_haircut_floor  (REDUCE)
                          = kelly_target                             (APPROVE)
        9.  liquidity_floor = requested_notional * liquidity_haircut_floor
        10. target = max(reduce_target, liquidity_floor)

    Args:
        position:     PositionSpec. quantity and current_price derive requested notional.
        portfolio:    PortfolioState. nav used for base cap.
        params:       RiskParameters. All sizing scalars consumed here.
        decision:     RiskDecision from evaluate_position_risk(). Only verdict consumed.
        position_vol: Optional annualised volatility of this position.
                      None -> vol_cap_scalar = 1.0 (no vol adjustment; backward compat).

    Returns:
        PositionSizingResult(allowed, target_notional, reason).
    """
    # ------------------------------------------------------------------
    # Step 1: HALT -- no sizing arithmetic performed.
    # ------------------------------------------------------------------
    if decision.verdict is RiskVerdict.HALT:
        return PositionSizingResult(
            allowed=False,
            target_notional=None,
            reason=decision.verdict,
        )

    # ------------------------------------------------------------------
    # Step 2: Requested notional.
    # quantity and current_price are finite and > 0 (domain-validated).
    # ------------------------------------------------------------------
    requested_notional: float = position.quantity * position.current_price

    # ------------------------------------------------------------------
    # Step 3: Base position cap.
    # nav and max_position_pct_nav are finite and > 0 (domain-validated).
    # ------------------------------------------------------------------
    base_cap: float = portfolio.nav * params.max_position_pct_nav

    # ------------------------------------------------------------------
    # Step 4: Volatility-adjusted cap scalar.
    # position_vol=None -> scalar=1.0 (identity; preserves Phase 7C output).
    # max(position_vol, 1e-8) guards against division by zero or near-zero.
    # min(..., 1.0) prevents the scalar from exceeding 1 (no vol-based leverage).
    # ------------------------------------------------------------------
    if position_vol is not None:
        vol_cap_scalar: float = min(
            params.volatility_target_ann / max(position_vol, 1e-8),
            1.0,
        )
    else:
        vol_cap_scalar = 1.0

    # ------------------------------------------------------------------
    # Step 5: Effective cap.
    # vol_cap = base_cap * scalar. effective_cap = min(base_cap, vol_cap).
    # When scalar=1.0: vol_cap == base_cap -> effective_cap == base_cap.
    # ------------------------------------------------------------------
    effective_cap: float = min(base_cap, base_cap * vol_cap_scalar)

    # ------------------------------------------------------------------
    # Step 6: Raw target capped at effective_cap.
    # ------------------------------------------------------------------
    raw_target: float = min(requested_notional, None)

    # ------------------------------------------------------------------
    # Step 7: Kelly fraction.
    # kelly_fraction is validated in (0.0, 1.0] by RiskParameters.
    # No guard needed; always reduces or preserves raw_target.
    # ------------------------------------------------------------------
    kelly_target: float = raw_target * params.kelly_fraction

    # ------------------------------------------------------------------
    # Step 8: REDUCE multiplier (conditional on clamping).
    # REDUCE applies liquidity_haircut_floor only when the position was
    # clamped by the cap (raw_target < requested_notional).
    # When not clamped (position already within cap), REDUCE passes
    # kelly_target through unchanged -- no additional compression.
    # APPROVE always passes kelly_target through unchanged.
    # liquidity_haircut_floor validated in (0.0, 1.0] by RiskParameters.
    # ------------------------------------------------------------------
    _was_clamped: bool = raw_target < requested_notional
    if decision.verdict is RiskVerdict.REDUCE and _was_clamped:
        reduce_target: float = kelly_target * params.liquidity_haircut_floor
    else:
        reduce_target = kelly_target

    # ------------------------------------------------------------------
    # Step 9: Liquidity floor guarantee (INV-SZ-05).
    # Even after Kelly and REDUCE compression, target must be at least
    # liquidity_haircut_floor fraction of the original requested notional.
    # This prevents compound discounting from compressing to near-zero.
    # ------------------------------------------------------------------
    liquidity_floor_value: float = requested_notional * params.liquidity_haircut_floor
    target: float = max(reduce_target, liquidity_floor_value)

    return PositionSizingResult(
        allowed=True,
        target_notional=target,
        reason=decision.verdict,
    )


# =============================================================================
# SECTION 2 -- SIZE POSITION
# =============================================================================

def x_size_position__mutmut_36(
    position:     PositionSpec,
    portfolio:    PortfolioState,
    params:       RiskParameters,
    decision:     RiskDecision,
    position_vol: Optional[float] = None,
) -> PositionSizingResult:
    """
    Compute the allowed position size given a pre-evaluated RiskDecision.

    Pure function: reads arguments, returns PositionSizingResult.
    No mutation, no global state, no I/O, no side effects.

    Sizing pipeline (fixed order):
        1.  HALT -> return immediately.
        2.  requested_notional = quantity * current_price
        3.  base_cap = nav * max_position_pct_nav
        4.  vol_cap_scalar = min(volatility_target_ann / max(position_vol, 1e-8), 1.0)
                             if position_vol is not None else 1.0
        5.  effective_cap = min(base_cap, base_cap * vol_cap_scalar)
        6.  raw_target = min(requested_notional, effective_cap)
        7.  kelly_target = raw_target * kelly_fraction
        8.  reduce_target = kelly_target * liquidity_haircut_floor  (REDUCE)
                          = kelly_target                             (APPROVE)
        9.  liquidity_floor = requested_notional * liquidity_haircut_floor
        10. target = max(reduce_target, liquidity_floor)

    Args:
        position:     PositionSpec. quantity and current_price derive requested notional.
        portfolio:    PortfolioState. nav used for base cap.
        params:       RiskParameters. All sizing scalars consumed here.
        decision:     RiskDecision from evaluate_position_risk(). Only verdict consumed.
        position_vol: Optional annualised volatility of this position.
                      None -> vol_cap_scalar = 1.0 (no vol adjustment; backward compat).

    Returns:
        PositionSizingResult(allowed, target_notional, reason).
    """
    # ------------------------------------------------------------------
    # Step 1: HALT -- no sizing arithmetic performed.
    # ------------------------------------------------------------------
    if decision.verdict is RiskVerdict.HALT:
        return PositionSizingResult(
            allowed=False,
            target_notional=None,
            reason=decision.verdict,
        )

    # ------------------------------------------------------------------
    # Step 2: Requested notional.
    # quantity and current_price are finite and > 0 (domain-validated).
    # ------------------------------------------------------------------
    requested_notional: float = position.quantity * position.current_price

    # ------------------------------------------------------------------
    # Step 3: Base position cap.
    # nav and max_position_pct_nav are finite and > 0 (domain-validated).
    # ------------------------------------------------------------------
    base_cap: float = portfolio.nav * params.max_position_pct_nav

    # ------------------------------------------------------------------
    # Step 4: Volatility-adjusted cap scalar.
    # position_vol=None -> scalar=1.0 (identity; preserves Phase 7C output).
    # max(position_vol, 1e-8) guards against division by zero or near-zero.
    # min(..., 1.0) prevents the scalar from exceeding 1 (no vol-based leverage).
    # ------------------------------------------------------------------
    if position_vol is not None:
        vol_cap_scalar: float = min(
            params.volatility_target_ann / max(position_vol, 1e-8),
            1.0,
        )
    else:
        vol_cap_scalar = 1.0

    # ------------------------------------------------------------------
    # Step 5: Effective cap.
    # vol_cap = base_cap * scalar. effective_cap = min(base_cap, vol_cap).
    # When scalar=1.0: vol_cap == base_cap -> effective_cap == base_cap.
    # ------------------------------------------------------------------
    effective_cap: float = min(base_cap, base_cap * vol_cap_scalar)

    # ------------------------------------------------------------------
    # Step 6: Raw target capped at effective_cap.
    # ------------------------------------------------------------------
    raw_target: float = min(effective_cap)

    # ------------------------------------------------------------------
    # Step 7: Kelly fraction.
    # kelly_fraction is validated in (0.0, 1.0] by RiskParameters.
    # No guard needed; always reduces or preserves raw_target.
    # ------------------------------------------------------------------
    kelly_target: float = raw_target * params.kelly_fraction

    # ------------------------------------------------------------------
    # Step 8: REDUCE multiplier (conditional on clamping).
    # REDUCE applies liquidity_haircut_floor only when the position was
    # clamped by the cap (raw_target < requested_notional).
    # When not clamped (position already within cap), REDUCE passes
    # kelly_target through unchanged -- no additional compression.
    # APPROVE always passes kelly_target through unchanged.
    # liquidity_haircut_floor validated in (0.0, 1.0] by RiskParameters.
    # ------------------------------------------------------------------
    _was_clamped: bool = raw_target < requested_notional
    if decision.verdict is RiskVerdict.REDUCE and _was_clamped:
        reduce_target: float = kelly_target * params.liquidity_haircut_floor
    else:
        reduce_target = kelly_target

    # ------------------------------------------------------------------
    # Step 9: Liquidity floor guarantee (INV-SZ-05).
    # Even after Kelly and REDUCE compression, target must be at least
    # liquidity_haircut_floor fraction of the original requested notional.
    # This prevents compound discounting from compressing to near-zero.
    # ------------------------------------------------------------------
    liquidity_floor_value: float = requested_notional * params.liquidity_haircut_floor
    target: float = max(reduce_target, liquidity_floor_value)

    return PositionSizingResult(
        allowed=True,
        target_notional=target,
        reason=decision.verdict,
    )


# =============================================================================
# SECTION 2 -- SIZE POSITION
# =============================================================================

def x_size_position__mutmut_37(
    position:     PositionSpec,
    portfolio:    PortfolioState,
    params:       RiskParameters,
    decision:     RiskDecision,
    position_vol: Optional[float] = None,
) -> PositionSizingResult:
    """
    Compute the allowed position size given a pre-evaluated RiskDecision.

    Pure function: reads arguments, returns PositionSizingResult.
    No mutation, no global state, no I/O, no side effects.

    Sizing pipeline (fixed order):
        1.  HALT -> return immediately.
        2.  requested_notional = quantity * current_price
        3.  base_cap = nav * max_position_pct_nav
        4.  vol_cap_scalar = min(volatility_target_ann / max(position_vol, 1e-8), 1.0)
                             if position_vol is not None else 1.0
        5.  effective_cap = min(base_cap, base_cap * vol_cap_scalar)
        6.  raw_target = min(requested_notional, effective_cap)
        7.  kelly_target = raw_target * kelly_fraction
        8.  reduce_target = kelly_target * liquidity_haircut_floor  (REDUCE)
                          = kelly_target                             (APPROVE)
        9.  liquidity_floor = requested_notional * liquidity_haircut_floor
        10. target = max(reduce_target, liquidity_floor)

    Args:
        position:     PositionSpec. quantity and current_price derive requested notional.
        portfolio:    PortfolioState. nav used for base cap.
        params:       RiskParameters. All sizing scalars consumed here.
        decision:     RiskDecision from evaluate_position_risk(). Only verdict consumed.
        position_vol: Optional annualised volatility of this position.
                      None -> vol_cap_scalar = 1.0 (no vol adjustment; backward compat).

    Returns:
        PositionSizingResult(allowed, target_notional, reason).
    """
    # ------------------------------------------------------------------
    # Step 1: HALT -- no sizing arithmetic performed.
    # ------------------------------------------------------------------
    if decision.verdict is RiskVerdict.HALT:
        return PositionSizingResult(
            allowed=False,
            target_notional=None,
            reason=decision.verdict,
        )

    # ------------------------------------------------------------------
    # Step 2: Requested notional.
    # quantity and current_price are finite and > 0 (domain-validated).
    # ------------------------------------------------------------------
    requested_notional: float = position.quantity * position.current_price

    # ------------------------------------------------------------------
    # Step 3: Base position cap.
    # nav and max_position_pct_nav are finite and > 0 (domain-validated).
    # ------------------------------------------------------------------
    base_cap: float = portfolio.nav * params.max_position_pct_nav

    # ------------------------------------------------------------------
    # Step 4: Volatility-adjusted cap scalar.
    # position_vol=None -> scalar=1.0 (identity; preserves Phase 7C output).
    # max(position_vol, 1e-8) guards against division by zero or near-zero.
    # min(..., 1.0) prevents the scalar from exceeding 1 (no vol-based leverage).
    # ------------------------------------------------------------------
    if position_vol is not None:
        vol_cap_scalar: float = min(
            params.volatility_target_ann / max(position_vol, 1e-8),
            1.0,
        )
    else:
        vol_cap_scalar = 1.0

    # ------------------------------------------------------------------
    # Step 5: Effective cap.
    # vol_cap = base_cap * scalar. effective_cap = min(base_cap, vol_cap).
    # When scalar=1.0: vol_cap == base_cap -> effective_cap == base_cap.
    # ------------------------------------------------------------------
    effective_cap: float = min(base_cap, base_cap * vol_cap_scalar)

    # ------------------------------------------------------------------
    # Step 6: Raw target capped at effective_cap.
    # ------------------------------------------------------------------
    raw_target: float = min(requested_notional, )

    # ------------------------------------------------------------------
    # Step 7: Kelly fraction.
    # kelly_fraction is validated in (0.0, 1.0] by RiskParameters.
    # No guard needed; always reduces or preserves raw_target.
    # ------------------------------------------------------------------
    kelly_target: float = raw_target * params.kelly_fraction

    # ------------------------------------------------------------------
    # Step 8: REDUCE multiplier (conditional on clamping).
    # REDUCE applies liquidity_haircut_floor only when the position was
    # clamped by the cap (raw_target < requested_notional).
    # When not clamped (position already within cap), REDUCE passes
    # kelly_target through unchanged -- no additional compression.
    # APPROVE always passes kelly_target through unchanged.
    # liquidity_haircut_floor validated in (0.0, 1.0] by RiskParameters.
    # ------------------------------------------------------------------
    _was_clamped: bool = raw_target < requested_notional
    if decision.verdict is RiskVerdict.REDUCE and _was_clamped:
        reduce_target: float = kelly_target * params.liquidity_haircut_floor
    else:
        reduce_target = kelly_target

    # ------------------------------------------------------------------
    # Step 9: Liquidity floor guarantee (INV-SZ-05).
    # Even after Kelly and REDUCE compression, target must be at least
    # liquidity_haircut_floor fraction of the original requested notional.
    # This prevents compound discounting from compressing to near-zero.
    # ------------------------------------------------------------------
    liquidity_floor_value: float = requested_notional * params.liquidity_haircut_floor
    target: float = max(reduce_target, liquidity_floor_value)

    return PositionSizingResult(
        allowed=True,
        target_notional=target,
        reason=decision.verdict,
    )


# =============================================================================
# SECTION 2 -- SIZE POSITION
# =============================================================================

def x_size_position__mutmut_38(
    position:     PositionSpec,
    portfolio:    PortfolioState,
    params:       RiskParameters,
    decision:     RiskDecision,
    position_vol: Optional[float] = None,
) -> PositionSizingResult:
    """
    Compute the allowed position size given a pre-evaluated RiskDecision.

    Pure function: reads arguments, returns PositionSizingResult.
    No mutation, no global state, no I/O, no side effects.

    Sizing pipeline (fixed order):
        1.  HALT -> return immediately.
        2.  requested_notional = quantity * current_price
        3.  base_cap = nav * max_position_pct_nav
        4.  vol_cap_scalar = min(volatility_target_ann / max(position_vol, 1e-8), 1.0)
                             if position_vol is not None else 1.0
        5.  effective_cap = min(base_cap, base_cap * vol_cap_scalar)
        6.  raw_target = min(requested_notional, effective_cap)
        7.  kelly_target = raw_target * kelly_fraction
        8.  reduce_target = kelly_target * liquidity_haircut_floor  (REDUCE)
                          = kelly_target                             (APPROVE)
        9.  liquidity_floor = requested_notional * liquidity_haircut_floor
        10. target = max(reduce_target, liquidity_floor)

    Args:
        position:     PositionSpec. quantity and current_price derive requested notional.
        portfolio:    PortfolioState. nav used for base cap.
        params:       RiskParameters. All sizing scalars consumed here.
        decision:     RiskDecision from evaluate_position_risk(). Only verdict consumed.
        position_vol: Optional annualised volatility of this position.
                      None -> vol_cap_scalar = 1.0 (no vol adjustment; backward compat).

    Returns:
        PositionSizingResult(allowed, target_notional, reason).
    """
    # ------------------------------------------------------------------
    # Step 1: HALT -- no sizing arithmetic performed.
    # ------------------------------------------------------------------
    if decision.verdict is RiskVerdict.HALT:
        return PositionSizingResult(
            allowed=False,
            target_notional=None,
            reason=decision.verdict,
        )

    # ------------------------------------------------------------------
    # Step 2: Requested notional.
    # quantity and current_price are finite and > 0 (domain-validated).
    # ------------------------------------------------------------------
    requested_notional: float = position.quantity * position.current_price

    # ------------------------------------------------------------------
    # Step 3: Base position cap.
    # nav and max_position_pct_nav are finite and > 0 (domain-validated).
    # ------------------------------------------------------------------
    base_cap: float = portfolio.nav * params.max_position_pct_nav

    # ------------------------------------------------------------------
    # Step 4: Volatility-adjusted cap scalar.
    # position_vol=None -> scalar=1.0 (identity; preserves Phase 7C output).
    # max(position_vol, 1e-8) guards against division by zero or near-zero.
    # min(..., 1.0) prevents the scalar from exceeding 1 (no vol-based leverage).
    # ------------------------------------------------------------------
    if position_vol is not None:
        vol_cap_scalar: float = min(
            params.volatility_target_ann / max(position_vol, 1e-8),
            1.0,
        )
    else:
        vol_cap_scalar = 1.0

    # ------------------------------------------------------------------
    # Step 5: Effective cap.
    # vol_cap = base_cap * scalar. effective_cap = min(base_cap, vol_cap).
    # When scalar=1.0: vol_cap == base_cap -> effective_cap == base_cap.
    # ------------------------------------------------------------------
    effective_cap: float = min(base_cap, base_cap * vol_cap_scalar)

    # ------------------------------------------------------------------
    # Step 6: Raw target capped at effective_cap.
    # ------------------------------------------------------------------
    raw_target: float = min(requested_notional, effective_cap)

    # ------------------------------------------------------------------
    # Step 7: Kelly fraction.
    # kelly_fraction is validated in (0.0, 1.0] by RiskParameters.
    # No guard needed; always reduces or preserves raw_target.
    # ------------------------------------------------------------------
    kelly_target: float = None

    # ------------------------------------------------------------------
    # Step 8: REDUCE multiplier (conditional on clamping).
    # REDUCE applies liquidity_haircut_floor only when the position was
    # clamped by the cap (raw_target < requested_notional).
    # When not clamped (position already within cap), REDUCE passes
    # kelly_target through unchanged -- no additional compression.
    # APPROVE always passes kelly_target through unchanged.
    # liquidity_haircut_floor validated in (0.0, 1.0] by RiskParameters.
    # ------------------------------------------------------------------
    _was_clamped: bool = raw_target < requested_notional
    if decision.verdict is RiskVerdict.REDUCE and _was_clamped:
        reduce_target: float = kelly_target * params.liquidity_haircut_floor
    else:
        reduce_target = kelly_target

    # ------------------------------------------------------------------
    # Step 9: Liquidity floor guarantee (INV-SZ-05).
    # Even after Kelly and REDUCE compression, target must be at least
    # liquidity_haircut_floor fraction of the original requested notional.
    # This prevents compound discounting from compressing to near-zero.
    # ------------------------------------------------------------------
    liquidity_floor_value: float = requested_notional * params.liquidity_haircut_floor
    target: float = max(reduce_target, liquidity_floor_value)

    return PositionSizingResult(
        allowed=True,
        target_notional=target,
        reason=decision.verdict,
    )


# =============================================================================
# SECTION 2 -- SIZE POSITION
# =============================================================================

def x_size_position__mutmut_39(
    position:     PositionSpec,
    portfolio:    PortfolioState,
    params:       RiskParameters,
    decision:     RiskDecision,
    position_vol: Optional[float] = None,
) -> PositionSizingResult:
    """
    Compute the allowed position size given a pre-evaluated RiskDecision.

    Pure function: reads arguments, returns PositionSizingResult.
    No mutation, no global state, no I/O, no side effects.

    Sizing pipeline (fixed order):
        1.  HALT -> return immediately.
        2.  requested_notional = quantity * current_price
        3.  base_cap = nav * max_position_pct_nav
        4.  vol_cap_scalar = min(volatility_target_ann / max(position_vol, 1e-8), 1.0)
                             if position_vol is not None else 1.0
        5.  effective_cap = min(base_cap, base_cap * vol_cap_scalar)
        6.  raw_target = min(requested_notional, effective_cap)
        7.  kelly_target = raw_target * kelly_fraction
        8.  reduce_target = kelly_target * liquidity_haircut_floor  (REDUCE)
                          = kelly_target                             (APPROVE)
        9.  liquidity_floor = requested_notional * liquidity_haircut_floor
        10. target = max(reduce_target, liquidity_floor)

    Args:
        position:     PositionSpec. quantity and current_price derive requested notional.
        portfolio:    PortfolioState. nav used for base cap.
        params:       RiskParameters. All sizing scalars consumed here.
        decision:     RiskDecision from evaluate_position_risk(). Only verdict consumed.
        position_vol: Optional annualised volatility of this position.
                      None -> vol_cap_scalar = 1.0 (no vol adjustment; backward compat).

    Returns:
        PositionSizingResult(allowed, target_notional, reason).
    """
    # ------------------------------------------------------------------
    # Step 1: HALT -- no sizing arithmetic performed.
    # ------------------------------------------------------------------
    if decision.verdict is RiskVerdict.HALT:
        return PositionSizingResult(
            allowed=False,
            target_notional=None,
            reason=decision.verdict,
        )

    # ------------------------------------------------------------------
    # Step 2: Requested notional.
    # quantity and current_price are finite and > 0 (domain-validated).
    # ------------------------------------------------------------------
    requested_notional: float = position.quantity * position.current_price

    # ------------------------------------------------------------------
    # Step 3: Base position cap.
    # nav and max_position_pct_nav are finite and > 0 (domain-validated).
    # ------------------------------------------------------------------
    base_cap: float = portfolio.nav * params.max_position_pct_nav

    # ------------------------------------------------------------------
    # Step 4: Volatility-adjusted cap scalar.
    # position_vol=None -> scalar=1.0 (identity; preserves Phase 7C output).
    # max(position_vol, 1e-8) guards against division by zero or near-zero.
    # min(..., 1.0) prevents the scalar from exceeding 1 (no vol-based leverage).
    # ------------------------------------------------------------------
    if position_vol is not None:
        vol_cap_scalar: float = min(
            params.volatility_target_ann / max(position_vol, 1e-8),
            1.0,
        )
    else:
        vol_cap_scalar = 1.0

    # ------------------------------------------------------------------
    # Step 5: Effective cap.
    # vol_cap = base_cap * scalar. effective_cap = min(base_cap, vol_cap).
    # When scalar=1.0: vol_cap == base_cap -> effective_cap == base_cap.
    # ------------------------------------------------------------------
    effective_cap: float = min(base_cap, base_cap * vol_cap_scalar)

    # ------------------------------------------------------------------
    # Step 6: Raw target capped at effective_cap.
    # ------------------------------------------------------------------
    raw_target: float = min(requested_notional, effective_cap)

    # ------------------------------------------------------------------
    # Step 7: Kelly fraction.
    # kelly_fraction is validated in (0.0, 1.0] by RiskParameters.
    # No guard needed; always reduces or preserves raw_target.
    # ------------------------------------------------------------------
    kelly_target: float = raw_target / params.kelly_fraction

    # ------------------------------------------------------------------
    # Step 8: REDUCE multiplier (conditional on clamping).
    # REDUCE applies liquidity_haircut_floor only when the position was
    # clamped by the cap (raw_target < requested_notional).
    # When not clamped (position already within cap), REDUCE passes
    # kelly_target through unchanged -- no additional compression.
    # APPROVE always passes kelly_target through unchanged.
    # liquidity_haircut_floor validated in (0.0, 1.0] by RiskParameters.
    # ------------------------------------------------------------------
    _was_clamped: bool = raw_target < requested_notional
    if decision.verdict is RiskVerdict.REDUCE and _was_clamped:
        reduce_target: float = kelly_target * params.liquidity_haircut_floor
    else:
        reduce_target = kelly_target

    # ------------------------------------------------------------------
    # Step 9: Liquidity floor guarantee (INV-SZ-05).
    # Even after Kelly and REDUCE compression, target must be at least
    # liquidity_haircut_floor fraction of the original requested notional.
    # This prevents compound discounting from compressing to near-zero.
    # ------------------------------------------------------------------
    liquidity_floor_value: float = requested_notional * params.liquidity_haircut_floor
    target: float = max(reduce_target, liquidity_floor_value)

    return PositionSizingResult(
        allowed=True,
        target_notional=target,
        reason=decision.verdict,
    )


# =============================================================================
# SECTION 2 -- SIZE POSITION
# =============================================================================

def x_size_position__mutmut_40(
    position:     PositionSpec,
    portfolio:    PortfolioState,
    params:       RiskParameters,
    decision:     RiskDecision,
    position_vol: Optional[float] = None,
) -> PositionSizingResult:
    """
    Compute the allowed position size given a pre-evaluated RiskDecision.

    Pure function: reads arguments, returns PositionSizingResult.
    No mutation, no global state, no I/O, no side effects.

    Sizing pipeline (fixed order):
        1.  HALT -> return immediately.
        2.  requested_notional = quantity * current_price
        3.  base_cap = nav * max_position_pct_nav
        4.  vol_cap_scalar = min(volatility_target_ann / max(position_vol, 1e-8), 1.0)
                             if position_vol is not None else 1.0
        5.  effective_cap = min(base_cap, base_cap * vol_cap_scalar)
        6.  raw_target = min(requested_notional, effective_cap)
        7.  kelly_target = raw_target * kelly_fraction
        8.  reduce_target = kelly_target * liquidity_haircut_floor  (REDUCE)
                          = kelly_target                             (APPROVE)
        9.  liquidity_floor = requested_notional * liquidity_haircut_floor
        10. target = max(reduce_target, liquidity_floor)

    Args:
        position:     PositionSpec. quantity and current_price derive requested notional.
        portfolio:    PortfolioState. nav used for base cap.
        params:       RiskParameters. All sizing scalars consumed here.
        decision:     RiskDecision from evaluate_position_risk(). Only verdict consumed.
        position_vol: Optional annualised volatility of this position.
                      None -> vol_cap_scalar = 1.0 (no vol adjustment; backward compat).

    Returns:
        PositionSizingResult(allowed, target_notional, reason).
    """
    # ------------------------------------------------------------------
    # Step 1: HALT -- no sizing arithmetic performed.
    # ------------------------------------------------------------------
    if decision.verdict is RiskVerdict.HALT:
        return PositionSizingResult(
            allowed=False,
            target_notional=None,
            reason=decision.verdict,
        )

    # ------------------------------------------------------------------
    # Step 2: Requested notional.
    # quantity and current_price are finite and > 0 (domain-validated).
    # ------------------------------------------------------------------
    requested_notional: float = position.quantity * position.current_price

    # ------------------------------------------------------------------
    # Step 3: Base position cap.
    # nav and max_position_pct_nav are finite and > 0 (domain-validated).
    # ------------------------------------------------------------------
    base_cap: float = portfolio.nav * params.max_position_pct_nav

    # ------------------------------------------------------------------
    # Step 4: Volatility-adjusted cap scalar.
    # position_vol=None -> scalar=1.0 (identity; preserves Phase 7C output).
    # max(position_vol, 1e-8) guards against division by zero or near-zero.
    # min(..., 1.0) prevents the scalar from exceeding 1 (no vol-based leverage).
    # ------------------------------------------------------------------
    if position_vol is not None:
        vol_cap_scalar: float = min(
            params.volatility_target_ann / max(position_vol, 1e-8),
            1.0,
        )
    else:
        vol_cap_scalar = 1.0

    # ------------------------------------------------------------------
    # Step 5: Effective cap.
    # vol_cap = base_cap * scalar. effective_cap = min(base_cap, vol_cap).
    # When scalar=1.0: vol_cap == base_cap -> effective_cap == base_cap.
    # ------------------------------------------------------------------
    effective_cap: float = min(base_cap, base_cap * vol_cap_scalar)

    # ------------------------------------------------------------------
    # Step 6: Raw target capped at effective_cap.
    # ------------------------------------------------------------------
    raw_target: float = min(requested_notional, effective_cap)

    # ------------------------------------------------------------------
    # Step 7: Kelly fraction.
    # kelly_fraction is validated in (0.0, 1.0] by RiskParameters.
    # No guard needed; always reduces or preserves raw_target.
    # ------------------------------------------------------------------
    kelly_target: float = raw_target * params.kelly_fraction

    # ------------------------------------------------------------------
    # Step 8: REDUCE multiplier (conditional on clamping).
    # REDUCE applies liquidity_haircut_floor only when the position was
    # clamped by the cap (raw_target < requested_notional).
    # When not clamped (position already within cap), REDUCE passes
    # kelly_target through unchanged -- no additional compression.
    # APPROVE always passes kelly_target through unchanged.
    # liquidity_haircut_floor validated in (0.0, 1.0] by RiskParameters.
    # ------------------------------------------------------------------
    _was_clamped: bool = None
    if decision.verdict is RiskVerdict.REDUCE and _was_clamped:
        reduce_target: float = kelly_target * params.liquidity_haircut_floor
    else:
        reduce_target = kelly_target

    # ------------------------------------------------------------------
    # Step 9: Liquidity floor guarantee (INV-SZ-05).
    # Even after Kelly and REDUCE compression, target must be at least
    # liquidity_haircut_floor fraction of the original requested notional.
    # This prevents compound discounting from compressing to near-zero.
    # ------------------------------------------------------------------
    liquidity_floor_value: float = requested_notional * params.liquidity_haircut_floor
    target: float = max(reduce_target, liquidity_floor_value)

    return PositionSizingResult(
        allowed=True,
        target_notional=target,
        reason=decision.verdict,
    )


# =============================================================================
# SECTION 2 -- SIZE POSITION
# =============================================================================

def x_size_position__mutmut_41(
    position:     PositionSpec,
    portfolio:    PortfolioState,
    params:       RiskParameters,
    decision:     RiskDecision,
    position_vol: Optional[float] = None,
) -> PositionSizingResult:
    """
    Compute the allowed position size given a pre-evaluated RiskDecision.

    Pure function: reads arguments, returns PositionSizingResult.
    No mutation, no global state, no I/O, no side effects.

    Sizing pipeline (fixed order):
        1.  HALT -> return immediately.
        2.  requested_notional = quantity * current_price
        3.  base_cap = nav * max_position_pct_nav
        4.  vol_cap_scalar = min(volatility_target_ann / max(position_vol, 1e-8), 1.0)
                             if position_vol is not None else 1.0
        5.  effective_cap = min(base_cap, base_cap * vol_cap_scalar)
        6.  raw_target = min(requested_notional, effective_cap)
        7.  kelly_target = raw_target * kelly_fraction
        8.  reduce_target = kelly_target * liquidity_haircut_floor  (REDUCE)
                          = kelly_target                             (APPROVE)
        9.  liquidity_floor = requested_notional * liquidity_haircut_floor
        10. target = max(reduce_target, liquidity_floor)

    Args:
        position:     PositionSpec. quantity and current_price derive requested notional.
        portfolio:    PortfolioState. nav used for base cap.
        params:       RiskParameters. All sizing scalars consumed here.
        decision:     RiskDecision from evaluate_position_risk(). Only verdict consumed.
        position_vol: Optional annualised volatility of this position.
                      None -> vol_cap_scalar = 1.0 (no vol adjustment; backward compat).

    Returns:
        PositionSizingResult(allowed, target_notional, reason).
    """
    # ------------------------------------------------------------------
    # Step 1: HALT -- no sizing arithmetic performed.
    # ------------------------------------------------------------------
    if decision.verdict is RiskVerdict.HALT:
        return PositionSizingResult(
            allowed=False,
            target_notional=None,
            reason=decision.verdict,
        )

    # ------------------------------------------------------------------
    # Step 2: Requested notional.
    # quantity and current_price are finite and > 0 (domain-validated).
    # ------------------------------------------------------------------
    requested_notional: float = position.quantity * position.current_price

    # ------------------------------------------------------------------
    # Step 3: Base position cap.
    # nav and max_position_pct_nav are finite and > 0 (domain-validated).
    # ------------------------------------------------------------------
    base_cap: float = portfolio.nav * params.max_position_pct_nav

    # ------------------------------------------------------------------
    # Step 4: Volatility-adjusted cap scalar.
    # position_vol=None -> scalar=1.0 (identity; preserves Phase 7C output).
    # max(position_vol, 1e-8) guards against division by zero or near-zero.
    # min(..., 1.0) prevents the scalar from exceeding 1 (no vol-based leverage).
    # ------------------------------------------------------------------
    if position_vol is not None:
        vol_cap_scalar: float = min(
            params.volatility_target_ann / max(position_vol, 1e-8),
            1.0,
        )
    else:
        vol_cap_scalar = 1.0

    # ------------------------------------------------------------------
    # Step 5: Effective cap.
    # vol_cap = base_cap * scalar. effective_cap = min(base_cap, vol_cap).
    # When scalar=1.0: vol_cap == base_cap -> effective_cap == base_cap.
    # ------------------------------------------------------------------
    effective_cap: float = min(base_cap, base_cap * vol_cap_scalar)

    # ------------------------------------------------------------------
    # Step 6: Raw target capped at effective_cap.
    # ------------------------------------------------------------------
    raw_target: float = min(requested_notional, effective_cap)

    # ------------------------------------------------------------------
    # Step 7: Kelly fraction.
    # kelly_fraction is validated in (0.0, 1.0] by RiskParameters.
    # No guard needed; always reduces or preserves raw_target.
    # ------------------------------------------------------------------
    kelly_target: float = raw_target * params.kelly_fraction

    # ------------------------------------------------------------------
    # Step 8: REDUCE multiplier (conditional on clamping).
    # REDUCE applies liquidity_haircut_floor only when the position was
    # clamped by the cap (raw_target < requested_notional).
    # When not clamped (position already within cap), REDUCE passes
    # kelly_target through unchanged -- no additional compression.
    # APPROVE always passes kelly_target through unchanged.
    # liquidity_haircut_floor validated in (0.0, 1.0] by RiskParameters.
    # ------------------------------------------------------------------
    _was_clamped: bool = raw_target <= requested_notional
    if decision.verdict is RiskVerdict.REDUCE and _was_clamped:
        reduce_target: float = kelly_target * params.liquidity_haircut_floor
    else:
        reduce_target = kelly_target

    # ------------------------------------------------------------------
    # Step 9: Liquidity floor guarantee (INV-SZ-05).
    # Even after Kelly and REDUCE compression, target must be at least
    # liquidity_haircut_floor fraction of the original requested notional.
    # This prevents compound discounting from compressing to near-zero.
    # ------------------------------------------------------------------
    liquidity_floor_value: float = requested_notional * params.liquidity_haircut_floor
    target: float = max(reduce_target, liquidity_floor_value)

    return PositionSizingResult(
        allowed=True,
        target_notional=target,
        reason=decision.verdict,
    )


# =============================================================================
# SECTION 2 -- SIZE POSITION
# =============================================================================

def x_size_position__mutmut_42(
    position:     PositionSpec,
    portfolio:    PortfolioState,
    params:       RiskParameters,
    decision:     RiskDecision,
    position_vol: Optional[float] = None,
) -> PositionSizingResult:
    """
    Compute the allowed position size given a pre-evaluated RiskDecision.

    Pure function: reads arguments, returns PositionSizingResult.
    No mutation, no global state, no I/O, no side effects.

    Sizing pipeline (fixed order):
        1.  HALT -> return immediately.
        2.  requested_notional = quantity * current_price
        3.  base_cap = nav * max_position_pct_nav
        4.  vol_cap_scalar = min(volatility_target_ann / max(position_vol, 1e-8), 1.0)
                             if position_vol is not None else 1.0
        5.  effective_cap = min(base_cap, base_cap * vol_cap_scalar)
        6.  raw_target = min(requested_notional, effective_cap)
        7.  kelly_target = raw_target * kelly_fraction
        8.  reduce_target = kelly_target * liquidity_haircut_floor  (REDUCE)
                          = kelly_target                             (APPROVE)
        9.  liquidity_floor = requested_notional * liquidity_haircut_floor
        10. target = max(reduce_target, liquidity_floor)

    Args:
        position:     PositionSpec. quantity and current_price derive requested notional.
        portfolio:    PortfolioState. nav used for base cap.
        params:       RiskParameters. All sizing scalars consumed here.
        decision:     RiskDecision from evaluate_position_risk(). Only verdict consumed.
        position_vol: Optional annualised volatility of this position.
                      None -> vol_cap_scalar = 1.0 (no vol adjustment; backward compat).

    Returns:
        PositionSizingResult(allowed, target_notional, reason).
    """
    # ------------------------------------------------------------------
    # Step 1: HALT -- no sizing arithmetic performed.
    # ------------------------------------------------------------------
    if decision.verdict is RiskVerdict.HALT:
        return PositionSizingResult(
            allowed=False,
            target_notional=None,
            reason=decision.verdict,
        )

    # ------------------------------------------------------------------
    # Step 2: Requested notional.
    # quantity and current_price are finite and > 0 (domain-validated).
    # ------------------------------------------------------------------
    requested_notional: float = position.quantity * position.current_price

    # ------------------------------------------------------------------
    # Step 3: Base position cap.
    # nav and max_position_pct_nav are finite and > 0 (domain-validated).
    # ------------------------------------------------------------------
    base_cap: float = portfolio.nav * params.max_position_pct_nav

    # ------------------------------------------------------------------
    # Step 4: Volatility-adjusted cap scalar.
    # position_vol=None -> scalar=1.0 (identity; preserves Phase 7C output).
    # max(position_vol, 1e-8) guards against division by zero or near-zero.
    # min(..., 1.0) prevents the scalar from exceeding 1 (no vol-based leverage).
    # ------------------------------------------------------------------
    if position_vol is not None:
        vol_cap_scalar: float = min(
            params.volatility_target_ann / max(position_vol, 1e-8),
            1.0,
        )
    else:
        vol_cap_scalar = 1.0

    # ------------------------------------------------------------------
    # Step 5: Effective cap.
    # vol_cap = base_cap * scalar. effective_cap = min(base_cap, vol_cap).
    # When scalar=1.0: vol_cap == base_cap -> effective_cap == base_cap.
    # ------------------------------------------------------------------
    effective_cap: float = min(base_cap, base_cap * vol_cap_scalar)

    # ------------------------------------------------------------------
    # Step 6: Raw target capped at effective_cap.
    # ------------------------------------------------------------------
    raw_target: float = min(requested_notional, effective_cap)

    # ------------------------------------------------------------------
    # Step 7: Kelly fraction.
    # kelly_fraction is validated in (0.0, 1.0] by RiskParameters.
    # No guard needed; always reduces or preserves raw_target.
    # ------------------------------------------------------------------
    kelly_target: float = raw_target * params.kelly_fraction

    # ------------------------------------------------------------------
    # Step 8: REDUCE multiplier (conditional on clamping).
    # REDUCE applies liquidity_haircut_floor only when the position was
    # clamped by the cap (raw_target < requested_notional).
    # When not clamped (position already within cap), REDUCE passes
    # kelly_target through unchanged -- no additional compression.
    # APPROVE always passes kelly_target through unchanged.
    # liquidity_haircut_floor validated in (0.0, 1.0] by RiskParameters.
    # ------------------------------------------------------------------
    _was_clamped: bool = raw_target < requested_notional
    if decision.verdict is RiskVerdict.REDUCE or _was_clamped:
        reduce_target: float = kelly_target * params.liquidity_haircut_floor
    else:
        reduce_target = kelly_target

    # ------------------------------------------------------------------
    # Step 9: Liquidity floor guarantee (INV-SZ-05).
    # Even after Kelly and REDUCE compression, target must be at least
    # liquidity_haircut_floor fraction of the original requested notional.
    # This prevents compound discounting from compressing to near-zero.
    # ------------------------------------------------------------------
    liquidity_floor_value: float = requested_notional * params.liquidity_haircut_floor
    target: float = max(reduce_target, liquidity_floor_value)

    return PositionSizingResult(
        allowed=True,
        target_notional=target,
        reason=decision.verdict,
    )


# =============================================================================
# SECTION 2 -- SIZE POSITION
# =============================================================================

def x_size_position__mutmut_43(
    position:     PositionSpec,
    portfolio:    PortfolioState,
    params:       RiskParameters,
    decision:     RiskDecision,
    position_vol: Optional[float] = None,
) -> PositionSizingResult:
    """
    Compute the allowed position size given a pre-evaluated RiskDecision.

    Pure function: reads arguments, returns PositionSizingResult.
    No mutation, no global state, no I/O, no side effects.

    Sizing pipeline (fixed order):
        1.  HALT -> return immediately.
        2.  requested_notional = quantity * current_price
        3.  base_cap = nav * max_position_pct_nav
        4.  vol_cap_scalar = min(volatility_target_ann / max(position_vol, 1e-8), 1.0)
                             if position_vol is not None else 1.0
        5.  effective_cap = min(base_cap, base_cap * vol_cap_scalar)
        6.  raw_target = min(requested_notional, effective_cap)
        7.  kelly_target = raw_target * kelly_fraction
        8.  reduce_target = kelly_target * liquidity_haircut_floor  (REDUCE)
                          = kelly_target                             (APPROVE)
        9.  liquidity_floor = requested_notional * liquidity_haircut_floor
        10. target = max(reduce_target, liquidity_floor)

    Args:
        position:     PositionSpec. quantity and current_price derive requested notional.
        portfolio:    PortfolioState. nav used for base cap.
        params:       RiskParameters. All sizing scalars consumed here.
        decision:     RiskDecision from evaluate_position_risk(). Only verdict consumed.
        position_vol: Optional annualised volatility of this position.
                      None -> vol_cap_scalar = 1.0 (no vol adjustment; backward compat).

    Returns:
        PositionSizingResult(allowed, target_notional, reason).
    """
    # ------------------------------------------------------------------
    # Step 1: HALT -- no sizing arithmetic performed.
    # ------------------------------------------------------------------
    if decision.verdict is RiskVerdict.HALT:
        return PositionSizingResult(
            allowed=False,
            target_notional=None,
            reason=decision.verdict,
        )

    # ------------------------------------------------------------------
    # Step 2: Requested notional.
    # quantity and current_price are finite and > 0 (domain-validated).
    # ------------------------------------------------------------------
    requested_notional: float = position.quantity * position.current_price

    # ------------------------------------------------------------------
    # Step 3: Base position cap.
    # nav and max_position_pct_nav are finite and > 0 (domain-validated).
    # ------------------------------------------------------------------
    base_cap: float = portfolio.nav * params.max_position_pct_nav

    # ------------------------------------------------------------------
    # Step 4: Volatility-adjusted cap scalar.
    # position_vol=None -> scalar=1.0 (identity; preserves Phase 7C output).
    # max(position_vol, 1e-8) guards against division by zero or near-zero.
    # min(..., 1.0) prevents the scalar from exceeding 1 (no vol-based leverage).
    # ------------------------------------------------------------------
    if position_vol is not None:
        vol_cap_scalar: float = min(
            params.volatility_target_ann / max(position_vol, 1e-8),
            1.0,
        )
    else:
        vol_cap_scalar = 1.0

    # ------------------------------------------------------------------
    # Step 5: Effective cap.
    # vol_cap = base_cap * scalar. effective_cap = min(base_cap, vol_cap).
    # When scalar=1.0: vol_cap == base_cap -> effective_cap == base_cap.
    # ------------------------------------------------------------------
    effective_cap: float = min(base_cap, base_cap * vol_cap_scalar)

    # ------------------------------------------------------------------
    # Step 6: Raw target capped at effective_cap.
    # ------------------------------------------------------------------
    raw_target: float = min(requested_notional, effective_cap)

    # ------------------------------------------------------------------
    # Step 7: Kelly fraction.
    # kelly_fraction is validated in (0.0, 1.0] by RiskParameters.
    # No guard needed; always reduces or preserves raw_target.
    # ------------------------------------------------------------------
    kelly_target: float = raw_target * params.kelly_fraction

    # ------------------------------------------------------------------
    # Step 8: REDUCE multiplier (conditional on clamping).
    # REDUCE applies liquidity_haircut_floor only when the position was
    # clamped by the cap (raw_target < requested_notional).
    # When not clamped (position already within cap), REDUCE passes
    # kelly_target through unchanged -- no additional compression.
    # APPROVE always passes kelly_target through unchanged.
    # liquidity_haircut_floor validated in (0.0, 1.0] by RiskParameters.
    # ------------------------------------------------------------------
    _was_clamped: bool = raw_target < requested_notional
    if decision.verdict is not RiskVerdict.REDUCE and _was_clamped:
        reduce_target: float = kelly_target * params.liquidity_haircut_floor
    else:
        reduce_target = kelly_target

    # ------------------------------------------------------------------
    # Step 9: Liquidity floor guarantee (INV-SZ-05).
    # Even after Kelly and REDUCE compression, target must be at least
    # liquidity_haircut_floor fraction of the original requested notional.
    # This prevents compound discounting from compressing to near-zero.
    # ------------------------------------------------------------------
    liquidity_floor_value: float = requested_notional * params.liquidity_haircut_floor
    target: float = max(reduce_target, liquidity_floor_value)

    return PositionSizingResult(
        allowed=True,
        target_notional=target,
        reason=decision.verdict,
    )


# =============================================================================
# SECTION 2 -- SIZE POSITION
# =============================================================================

def x_size_position__mutmut_44(
    position:     PositionSpec,
    portfolio:    PortfolioState,
    params:       RiskParameters,
    decision:     RiskDecision,
    position_vol: Optional[float] = None,
) -> PositionSizingResult:
    """
    Compute the allowed position size given a pre-evaluated RiskDecision.

    Pure function: reads arguments, returns PositionSizingResult.
    No mutation, no global state, no I/O, no side effects.

    Sizing pipeline (fixed order):
        1.  HALT -> return immediately.
        2.  requested_notional = quantity * current_price
        3.  base_cap = nav * max_position_pct_nav
        4.  vol_cap_scalar = min(volatility_target_ann / max(position_vol, 1e-8), 1.0)
                             if position_vol is not None else 1.0
        5.  effective_cap = min(base_cap, base_cap * vol_cap_scalar)
        6.  raw_target = min(requested_notional, effective_cap)
        7.  kelly_target = raw_target * kelly_fraction
        8.  reduce_target = kelly_target * liquidity_haircut_floor  (REDUCE)
                          = kelly_target                             (APPROVE)
        9.  liquidity_floor = requested_notional * liquidity_haircut_floor
        10. target = max(reduce_target, liquidity_floor)

    Args:
        position:     PositionSpec. quantity and current_price derive requested notional.
        portfolio:    PortfolioState. nav used for base cap.
        params:       RiskParameters. All sizing scalars consumed here.
        decision:     RiskDecision from evaluate_position_risk(). Only verdict consumed.
        position_vol: Optional annualised volatility of this position.
                      None -> vol_cap_scalar = 1.0 (no vol adjustment; backward compat).

    Returns:
        PositionSizingResult(allowed, target_notional, reason).
    """
    # ------------------------------------------------------------------
    # Step 1: HALT -- no sizing arithmetic performed.
    # ------------------------------------------------------------------
    if decision.verdict is RiskVerdict.HALT:
        return PositionSizingResult(
            allowed=False,
            target_notional=None,
            reason=decision.verdict,
        )

    # ------------------------------------------------------------------
    # Step 2: Requested notional.
    # quantity and current_price are finite and > 0 (domain-validated).
    # ------------------------------------------------------------------
    requested_notional: float = position.quantity * position.current_price

    # ------------------------------------------------------------------
    # Step 3: Base position cap.
    # nav and max_position_pct_nav are finite and > 0 (domain-validated).
    # ------------------------------------------------------------------
    base_cap: float = portfolio.nav * params.max_position_pct_nav

    # ------------------------------------------------------------------
    # Step 4: Volatility-adjusted cap scalar.
    # position_vol=None -> scalar=1.0 (identity; preserves Phase 7C output).
    # max(position_vol, 1e-8) guards against division by zero or near-zero.
    # min(..., 1.0) prevents the scalar from exceeding 1 (no vol-based leverage).
    # ------------------------------------------------------------------
    if position_vol is not None:
        vol_cap_scalar: float = min(
            params.volatility_target_ann / max(position_vol, 1e-8),
            1.0,
        )
    else:
        vol_cap_scalar = 1.0

    # ------------------------------------------------------------------
    # Step 5: Effective cap.
    # vol_cap = base_cap * scalar. effective_cap = min(base_cap, vol_cap).
    # When scalar=1.0: vol_cap == base_cap -> effective_cap == base_cap.
    # ------------------------------------------------------------------
    effective_cap: float = min(base_cap, base_cap * vol_cap_scalar)

    # ------------------------------------------------------------------
    # Step 6: Raw target capped at effective_cap.
    # ------------------------------------------------------------------
    raw_target: float = min(requested_notional, effective_cap)

    # ------------------------------------------------------------------
    # Step 7: Kelly fraction.
    # kelly_fraction is validated in (0.0, 1.0] by RiskParameters.
    # No guard needed; always reduces or preserves raw_target.
    # ------------------------------------------------------------------
    kelly_target: float = raw_target * params.kelly_fraction

    # ------------------------------------------------------------------
    # Step 8: REDUCE multiplier (conditional on clamping).
    # REDUCE applies liquidity_haircut_floor only when the position was
    # clamped by the cap (raw_target < requested_notional).
    # When not clamped (position already within cap), REDUCE passes
    # kelly_target through unchanged -- no additional compression.
    # APPROVE always passes kelly_target through unchanged.
    # liquidity_haircut_floor validated in (0.0, 1.0] by RiskParameters.
    # ------------------------------------------------------------------
    _was_clamped: bool = raw_target < requested_notional
    if decision.verdict is RiskVerdict.REDUCE and _was_clamped:
        reduce_target: float = None
    else:
        reduce_target = kelly_target

    # ------------------------------------------------------------------
    # Step 9: Liquidity floor guarantee (INV-SZ-05).
    # Even after Kelly and REDUCE compression, target must be at least
    # liquidity_haircut_floor fraction of the original requested notional.
    # This prevents compound discounting from compressing to near-zero.
    # ------------------------------------------------------------------
    liquidity_floor_value: float = requested_notional * params.liquidity_haircut_floor
    target: float = max(reduce_target, liquidity_floor_value)

    return PositionSizingResult(
        allowed=True,
        target_notional=target,
        reason=decision.verdict,
    )


# =============================================================================
# SECTION 2 -- SIZE POSITION
# =============================================================================

def x_size_position__mutmut_45(
    position:     PositionSpec,
    portfolio:    PortfolioState,
    params:       RiskParameters,
    decision:     RiskDecision,
    position_vol: Optional[float] = None,
) -> PositionSizingResult:
    """
    Compute the allowed position size given a pre-evaluated RiskDecision.

    Pure function: reads arguments, returns PositionSizingResult.
    No mutation, no global state, no I/O, no side effects.

    Sizing pipeline (fixed order):
        1.  HALT -> return immediately.
        2.  requested_notional = quantity * current_price
        3.  base_cap = nav * max_position_pct_nav
        4.  vol_cap_scalar = min(volatility_target_ann / max(position_vol, 1e-8), 1.0)
                             if position_vol is not None else 1.0
        5.  effective_cap = min(base_cap, base_cap * vol_cap_scalar)
        6.  raw_target = min(requested_notional, effective_cap)
        7.  kelly_target = raw_target * kelly_fraction
        8.  reduce_target = kelly_target * liquidity_haircut_floor  (REDUCE)
                          = kelly_target                             (APPROVE)
        9.  liquidity_floor = requested_notional * liquidity_haircut_floor
        10. target = max(reduce_target, liquidity_floor)

    Args:
        position:     PositionSpec. quantity and current_price derive requested notional.
        portfolio:    PortfolioState. nav used for base cap.
        params:       RiskParameters. All sizing scalars consumed here.
        decision:     RiskDecision from evaluate_position_risk(). Only verdict consumed.
        position_vol: Optional annualised volatility of this position.
                      None -> vol_cap_scalar = 1.0 (no vol adjustment; backward compat).

    Returns:
        PositionSizingResult(allowed, target_notional, reason).
    """
    # ------------------------------------------------------------------
    # Step 1: HALT -- no sizing arithmetic performed.
    # ------------------------------------------------------------------
    if decision.verdict is RiskVerdict.HALT:
        return PositionSizingResult(
            allowed=False,
            target_notional=None,
            reason=decision.verdict,
        )

    # ------------------------------------------------------------------
    # Step 2: Requested notional.
    # quantity and current_price are finite and > 0 (domain-validated).
    # ------------------------------------------------------------------
    requested_notional: float = position.quantity * position.current_price

    # ------------------------------------------------------------------
    # Step 3: Base position cap.
    # nav and max_position_pct_nav are finite and > 0 (domain-validated).
    # ------------------------------------------------------------------
    base_cap: float = portfolio.nav * params.max_position_pct_nav

    # ------------------------------------------------------------------
    # Step 4: Volatility-adjusted cap scalar.
    # position_vol=None -> scalar=1.0 (identity; preserves Phase 7C output).
    # max(position_vol, 1e-8) guards against division by zero or near-zero.
    # min(..., 1.0) prevents the scalar from exceeding 1 (no vol-based leverage).
    # ------------------------------------------------------------------
    if position_vol is not None:
        vol_cap_scalar: float = min(
            params.volatility_target_ann / max(position_vol, 1e-8),
            1.0,
        )
    else:
        vol_cap_scalar = 1.0

    # ------------------------------------------------------------------
    # Step 5: Effective cap.
    # vol_cap = base_cap * scalar. effective_cap = min(base_cap, vol_cap).
    # When scalar=1.0: vol_cap == base_cap -> effective_cap == base_cap.
    # ------------------------------------------------------------------
    effective_cap: float = min(base_cap, base_cap * vol_cap_scalar)

    # ------------------------------------------------------------------
    # Step 6: Raw target capped at effective_cap.
    # ------------------------------------------------------------------
    raw_target: float = min(requested_notional, effective_cap)

    # ------------------------------------------------------------------
    # Step 7: Kelly fraction.
    # kelly_fraction is validated in (0.0, 1.0] by RiskParameters.
    # No guard needed; always reduces or preserves raw_target.
    # ------------------------------------------------------------------
    kelly_target: float = raw_target * params.kelly_fraction

    # ------------------------------------------------------------------
    # Step 8: REDUCE multiplier (conditional on clamping).
    # REDUCE applies liquidity_haircut_floor only when the position was
    # clamped by the cap (raw_target < requested_notional).
    # When not clamped (position already within cap), REDUCE passes
    # kelly_target through unchanged -- no additional compression.
    # APPROVE always passes kelly_target through unchanged.
    # liquidity_haircut_floor validated in (0.0, 1.0] by RiskParameters.
    # ------------------------------------------------------------------
    _was_clamped: bool = raw_target < requested_notional
    if decision.verdict is RiskVerdict.REDUCE and _was_clamped:
        reduce_target: float = kelly_target / params.liquidity_haircut_floor
    else:
        reduce_target = kelly_target

    # ------------------------------------------------------------------
    # Step 9: Liquidity floor guarantee (INV-SZ-05).
    # Even after Kelly and REDUCE compression, target must be at least
    # liquidity_haircut_floor fraction of the original requested notional.
    # This prevents compound discounting from compressing to near-zero.
    # ------------------------------------------------------------------
    liquidity_floor_value: float = requested_notional * params.liquidity_haircut_floor
    target: float = max(reduce_target, liquidity_floor_value)

    return PositionSizingResult(
        allowed=True,
        target_notional=target,
        reason=decision.verdict,
    )


# =============================================================================
# SECTION 2 -- SIZE POSITION
# =============================================================================

def x_size_position__mutmut_46(
    position:     PositionSpec,
    portfolio:    PortfolioState,
    params:       RiskParameters,
    decision:     RiskDecision,
    position_vol: Optional[float] = None,
) -> PositionSizingResult:
    """
    Compute the allowed position size given a pre-evaluated RiskDecision.

    Pure function: reads arguments, returns PositionSizingResult.
    No mutation, no global state, no I/O, no side effects.

    Sizing pipeline (fixed order):
        1.  HALT -> return immediately.
        2.  requested_notional = quantity * current_price
        3.  base_cap = nav * max_position_pct_nav
        4.  vol_cap_scalar = min(volatility_target_ann / max(position_vol, 1e-8), 1.0)
                             if position_vol is not None else 1.0
        5.  effective_cap = min(base_cap, base_cap * vol_cap_scalar)
        6.  raw_target = min(requested_notional, effective_cap)
        7.  kelly_target = raw_target * kelly_fraction
        8.  reduce_target = kelly_target * liquidity_haircut_floor  (REDUCE)
                          = kelly_target                             (APPROVE)
        9.  liquidity_floor = requested_notional * liquidity_haircut_floor
        10. target = max(reduce_target, liquidity_floor)

    Args:
        position:     PositionSpec. quantity and current_price derive requested notional.
        portfolio:    PortfolioState. nav used for base cap.
        params:       RiskParameters. All sizing scalars consumed here.
        decision:     RiskDecision from evaluate_position_risk(). Only verdict consumed.
        position_vol: Optional annualised volatility of this position.
                      None -> vol_cap_scalar = 1.0 (no vol adjustment; backward compat).

    Returns:
        PositionSizingResult(allowed, target_notional, reason).
    """
    # ------------------------------------------------------------------
    # Step 1: HALT -- no sizing arithmetic performed.
    # ------------------------------------------------------------------
    if decision.verdict is RiskVerdict.HALT:
        return PositionSizingResult(
            allowed=False,
            target_notional=None,
            reason=decision.verdict,
        )

    # ------------------------------------------------------------------
    # Step 2: Requested notional.
    # quantity and current_price are finite and > 0 (domain-validated).
    # ------------------------------------------------------------------
    requested_notional: float = position.quantity * position.current_price

    # ------------------------------------------------------------------
    # Step 3: Base position cap.
    # nav and max_position_pct_nav are finite and > 0 (domain-validated).
    # ------------------------------------------------------------------
    base_cap: float = portfolio.nav * params.max_position_pct_nav

    # ------------------------------------------------------------------
    # Step 4: Volatility-adjusted cap scalar.
    # position_vol=None -> scalar=1.0 (identity; preserves Phase 7C output).
    # max(position_vol, 1e-8) guards against division by zero or near-zero.
    # min(..., 1.0) prevents the scalar from exceeding 1 (no vol-based leverage).
    # ------------------------------------------------------------------
    if position_vol is not None:
        vol_cap_scalar: float = min(
            params.volatility_target_ann / max(position_vol, 1e-8),
            1.0,
        )
    else:
        vol_cap_scalar = 1.0

    # ------------------------------------------------------------------
    # Step 5: Effective cap.
    # vol_cap = base_cap * scalar. effective_cap = min(base_cap, vol_cap).
    # When scalar=1.0: vol_cap == base_cap -> effective_cap == base_cap.
    # ------------------------------------------------------------------
    effective_cap: float = min(base_cap, base_cap * vol_cap_scalar)

    # ------------------------------------------------------------------
    # Step 6: Raw target capped at effective_cap.
    # ------------------------------------------------------------------
    raw_target: float = min(requested_notional, effective_cap)

    # ------------------------------------------------------------------
    # Step 7: Kelly fraction.
    # kelly_fraction is validated in (0.0, 1.0] by RiskParameters.
    # No guard needed; always reduces or preserves raw_target.
    # ------------------------------------------------------------------
    kelly_target: float = raw_target * params.kelly_fraction

    # ------------------------------------------------------------------
    # Step 8: REDUCE multiplier (conditional on clamping).
    # REDUCE applies liquidity_haircut_floor only when the position was
    # clamped by the cap (raw_target < requested_notional).
    # When not clamped (position already within cap), REDUCE passes
    # kelly_target through unchanged -- no additional compression.
    # APPROVE always passes kelly_target through unchanged.
    # liquidity_haircut_floor validated in (0.0, 1.0] by RiskParameters.
    # ------------------------------------------------------------------
    _was_clamped: bool = raw_target < requested_notional
    if decision.verdict is RiskVerdict.REDUCE and _was_clamped:
        reduce_target: float = kelly_target * params.liquidity_haircut_floor
    else:
        reduce_target = None

    # ------------------------------------------------------------------
    # Step 9: Liquidity floor guarantee (INV-SZ-05).
    # Even after Kelly and REDUCE compression, target must be at least
    # liquidity_haircut_floor fraction of the original requested notional.
    # This prevents compound discounting from compressing to near-zero.
    # ------------------------------------------------------------------
    liquidity_floor_value: float = requested_notional * params.liquidity_haircut_floor
    target: float = max(reduce_target, liquidity_floor_value)

    return PositionSizingResult(
        allowed=True,
        target_notional=target,
        reason=decision.verdict,
    )


# =============================================================================
# SECTION 2 -- SIZE POSITION
# =============================================================================

def x_size_position__mutmut_47(
    position:     PositionSpec,
    portfolio:    PortfolioState,
    params:       RiskParameters,
    decision:     RiskDecision,
    position_vol: Optional[float] = None,
) -> PositionSizingResult:
    """
    Compute the allowed position size given a pre-evaluated RiskDecision.

    Pure function: reads arguments, returns PositionSizingResult.
    No mutation, no global state, no I/O, no side effects.

    Sizing pipeline (fixed order):
        1.  HALT -> return immediately.
        2.  requested_notional = quantity * current_price
        3.  base_cap = nav * max_position_pct_nav
        4.  vol_cap_scalar = min(volatility_target_ann / max(position_vol, 1e-8), 1.0)
                             if position_vol is not None else 1.0
        5.  effective_cap = min(base_cap, base_cap * vol_cap_scalar)
        6.  raw_target = min(requested_notional, effective_cap)
        7.  kelly_target = raw_target * kelly_fraction
        8.  reduce_target = kelly_target * liquidity_haircut_floor  (REDUCE)
                          = kelly_target                             (APPROVE)
        9.  liquidity_floor = requested_notional * liquidity_haircut_floor
        10. target = max(reduce_target, liquidity_floor)

    Args:
        position:     PositionSpec. quantity and current_price derive requested notional.
        portfolio:    PortfolioState. nav used for base cap.
        params:       RiskParameters. All sizing scalars consumed here.
        decision:     RiskDecision from evaluate_position_risk(). Only verdict consumed.
        position_vol: Optional annualised volatility of this position.
                      None -> vol_cap_scalar = 1.0 (no vol adjustment; backward compat).

    Returns:
        PositionSizingResult(allowed, target_notional, reason).
    """
    # ------------------------------------------------------------------
    # Step 1: HALT -- no sizing arithmetic performed.
    # ------------------------------------------------------------------
    if decision.verdict is RiskVerdict.HALT:
        return PositionSizingResult(
            allowed=False,
            target_notional=None,
            reason=decision.verdict,
        )

    # ------------------------------------------------------------------
    # Step 2: Requested notional.
    # quantity and current_price are finite and > 0 (domain-validated).
    # ------------------------------------------------------------------
    requested_notional: float = position.quantity * position.current_price

    # ------------------------------------------------------------------
    # Step 3: Base position cap.
    # nav and max_position_pct_nav are finite and > 0 (domain-validated).
    # ------------------------------------------------------------------
    base_cap: float = portfolio.nav * params.max_position_pct_nav

    # ------------------------------------------------------------------
    # Step 4: Volatility-adjusted cap scalar.
    # position_vol=None -> scalar=1.0 (identity; preserves Phase 7C output).
    # max(position_vol, 1e-8) guards against division by zero or near-zero.
    # min(..., 1.0) prevents the scalar from exceeding 1 (no vol-based leverage).
    # ------------------------------------------------------------------
    if position_vol is not None:
        vol_cap_scalar: float = min(
            params.volatility_target_ann / max(position_vol, 1e-8),
            1.0,
        )
    else:
        vol_cap_scalar = 1.0

    # ------------------------------------------------------------------
    # Step 5: Effective cap.
    # vol_cap = base_cap * scalar. effective_cap = min(base_cap, vol_cap).
    # When scalar=1.0: vol_cap == base_cap -> effective_cap == base_cap.
    # ------------------------------------------------------------------
    effective_cap: float = min(base_cap, base_cap * vol_cap_scalar)

    # ------------------------------------------------------------------
    # Step 6: Raw target capped at effective_cap.
    # ------------------------------------------------------------------
    raw_target: float = min(requested_notional, effective_cap)

    # ------------------------------------------------------------------
    # Step 7: Kelly fraction.
    # kelly_fraction is validated in (0.0, 1.0] by RiskParameters.
    # No guard needed; always reduces or preserves raw_target.
    # ------------------------------------------------------------------
    kelly_target: float = raw_target * params.kelly_fraction

    # ------------------------------------------------------------------
    # Step 8: REDUCE multiplier (conditional on clamping).
    # REDUCE applies liquidity_haircut_floor only when the position was
    # clamped by the cap (raw_target < requested_notional).
    # When not clamped (position already within cap), REDUCE passes
    # kelly_target through unchanged -- no additional compression.
    # APPROVE always passes kelly_target through unchanged.
    # liquidity_haircut_floor validated in (0.0, 1.0] by RiskParameters.
    # ------------------------------------------------------------------
    _was_clamped: bool = raw_target < requested_notional
    if decision.verdict is RiskVerdict.REDUCE and _was_clamped:
        reduce_target: float = kelly_target * params.liquidity_haircut_floor
    else:
        reduce_target = kelly_target

    # ------------------------------------------------------------------
    # Step 9: Liquidity floor guarantee (INV-SZ-05).
    # Even after Kelly and REDUCE compression, target must be at least
    # liquidity_haircut_floor fraction of the original requested notional.
    # This prevents compound discounting from compressing to near-zero.
    # ------------------------------------------------------------------
    liquidity_floor_value: float = None
    target: float = max(reduce_target, liquidity_floor_value)

    return PositionSizingResult(
        allowed=True,
        target_notional=target,
        reason=decision.verdict,
    )


# =============================================================================
# SECTION 2 -- SIZE POSITION
# =============================================================================

def x_size_position__mutmut_48(
    position:     PositionSpec,
    portfolio:    PortfolioState,
    params:       RiskParameters,
    decision:     RiskDecision,
    position_vol: Optional[float] = None,
) -> PositionSizingResult:
    """
    Compute the allowed position size given a pre-evaluated RiskDecision.

    Pure function: reads arguments, returns PositionSizingResult.
    No mutation, no global state, no I/O, no side effects.

    Sizing pipeline (fixed order):
        1.  HALT -> return immediately.
        2.  requested_notional = quantity * current_price
        3.  base_cap = nav * max_position_pct_nav
        4.  vol_cap_scalar = min(volatility_target_ann / max(position_vol, 1e-8), 1.0)
                             if position_vol is not None else 1.0
        5.  effective_cap = min(base_cap, base_cap * vol_cap_scalar)
        6.  raw_target = min(requested_notional, effective_cap)
        7.  kelly_target = raw_target * kelly_fraction
        8.  reduce_target = kelly_target * liquidity_haircut_floor  (REDUCE)
                          = kelly_target                             (APPROVE)
        9.  liquidity_floor = requested_notional * liquidity_haircut_floor
        10. target = max(reduce_target, liquidity_floor)

    Args:
        position:     PositionSpec. quantity and current_price derive requested notional.
        portfolio:    PortfolioState. nav used for base cap.
        params:       RiskParameters. All sizing scalars consumed here.
        decision:     RiskDecision from evaluate_position_risk(). Only verdict consumed.
        position_vol: Optional annualised volatility of this position.
                      None -> vol_cap_scalar = 1.0 (no vol adjustment; backward compat).

    Returns:
        PositionSizingResult(allowed, target_notional, reason).
    """
    # ------------------------------------------------------------------
    # Step 1: HALT -- no sizing arithmetic performed.
    # ------------------------------------------------------------------
    if decision.verdict is RiskVerdict.HALT:
        return PositionSizingResult(
            allowed=False,
            target_notional=None,
            reason=decision.verdict,
        )

    # ------------------------------------------------------------------
    # Step 2: Requested notional.
    # quantity and current_price are finite and > 0 (domain-validated).
    # ------------------------------------------------------------------
    requested_notional: float = position.quantity * position.current_price

    # ------------------------------------------------------------------
    # Step 3: Base position cap.
    # nav and max_position_pct_nav are finite and > 0 (domain-validated).
    # ------------------------------------------------------------------
    base_cap: float = portfolio.nav * params.max_position_pct_nav

    # ------------------------------------------------------------------
    # Step 4: Volatility-adjusted cap scalar.
    # position_vol=None -> scalar=1.0 (identity; preserves Phase 7C output).
    # max(position_vol, 1e-8) guards against division by zero or near-zero.
    # min(..., 1.0) prevents the scalar from exceeding 1 (no vol-based leverage).
    # ------------------------------------------------------------------
    if position_vol is not None:
        vol_cap_scalar: float = min(
            params.volatility_target_ann / max(position_vol, 1e-8),
            1.0,
        )
    else:
        vol_cap_scalar = 1.0

    # ------------------------------------------------------------------
    # Step 5: Effective cap.
    # vol_cap = base_cap * scalar. effective_cap = min(base_cap, vol_cap).
    # When scalar=1.0: vol_cap == base_cap -> effective_cap == base_cap.
    # ------------------------------------------------------------------
    effective_cap: float = min(base_cap, base_cap * vol_cap_scalar)

    # ------------------------------------------------------------------
    # Step 6: Raw target capped at effective_cap.
    # ------------------------------------------------------------------
    raw_target: float = min(requested_notional, effective_cap)

    # ------------------------------------------------------------------
    # Step 7: Kelly fraction.
    # kelly_fraction is validated in (0.0, 1.0] by RiskParameters.
    # No guard needed; always reduces or preserves raw_target.
    # ------------------------------------------------------------------
    kelly_target: float = raw_target * params.kelly_fraction

    # ------------------------------------------------------------------
    # Step 8: REDUCE multiplier (conditional on clamping).
    # REDUCE applies liquidity_haircut_floor only when the position was
    # clamped by the cap (raw_target < requested_notional).
    # When not clamped (position already within cap), REDUCE passes
    # kelly_target through unchanged -- no additional compression.
    # APPROVE always passes kelly_target through unchanged.
    # liquidity_haircut_floor validated in (0.0, 1.0] by RiskParameters.
    # ------------------------------------------------------------------
    _was_clamped: bool = raw_target < requested_notional
    if decision.verdict is RiskVerdict.REDUCE and _was_clamped:
        reduce_target: float = kelly_target * params.liquidity_haircut_floor
    else:
        reduce_target = kelly_target

    # ------------------------------------------------------------------
    # Step 9: Liquidity floor guarantee (INV-SZ-05).
    # Even after Kelly and REDUCE compression, target must be at least
    # liquidity_haircut_floor fraction of the original requested notional.
    # This prevents compound discounting from compressing to near-zero.
    # ------------------------------------------------------------------
    liquidity_floor_value: float = requested_notional / params.liquidity_haircut_floor
    target: float = max(reduce_target, liquidity_floor_value)

    return PositionSizingResult(
        allowed=True,
        target_notional=target,
        reason=decision.verdict,
    )


# =============================================================================
# SECTION 2 -- SIZE POSITION
# =============================================================================

def x_size_position__mutmut_49(
    position:     PositionSpec,
    portfolio:    PortfolioState,
    params:       RiskParameters,
    decision:     RiskDecision,
    position_vol: Optional[float] = None,
) -> PositionSizingResult:
    """
    Compute the allowed position size given a pre-evaluated RiskDecision.

    Pure function: reads arguments, returns PositionSizingResult.
    No mutation, no global state, no I/O, no side effects.

    Sizing pipeline (fixed order):
        1.  HALT -> return immediately.
        2.  requested_notional = quantity * current_price
        3.  base_cap = nav * max_position_pct_nav
        4.  vol_cap_scalar = min(volatility_target_ann / max(position_vol, 1e-8), 1.0)
                             if position_vol is not None else 1.0
        5.  effective_cap = min(base_cap, base_cap * vol_cap_scalar)
        6.  raw_target = min(requested_notional, effective_cap)
        7.  kelly_target = raw_target * kelly_fraction
        8.  reduce_target = kelly_target * liquidity_haircut_floor  (REDUCE)
                          = kelly_target                             (APPROVE)
        9.  liquidity_floor = requested_notional * liquidity_haircut_floor
        10. target = max(reduce_target, liquidity_floor)

    Args:
        position:     PositionSpec. quantity and current_price derive requested notional.
        portfolio:    PortfolioState. nav used for base cap.
        params:       RiskParameters. All sizing scalars consumed here.
        decision:     RiskDecision from evaluate_position_risk(). Only verdict consumed.
        position_vol: Optional annualised volatility of this position.
                      None -> vol_cap_scalar = 1.0 (no vol adjustment; backward compat).

    Returns:
        PositionSizingResult(allowed, target_notional, reason).
    """
    # ------------------------------------------------------------------
    # Step 1: HALT -- no sizing arithmetic performed.
    # ------------------------------------------------------------------
    if decision.verdict is RiskVerdict.HALT:
        return PositionSizingResult(
            allowed=False,
            target_notional=None,
            reason=decision.verdict,
        )

    # ------------------------------------------------------------------
    # Step 2: Requested notional.
    # quantity and current_price are finite and > 0 (domain-validated).
    # ------------------------------------------------------------------
    requested_notional: float = position.quantity * position.current_price

    # ------------------------------------------------------------------
    # Step 3: Base position cap.
    # nav and max_position_pct_nav are finite and > 0 (domain-validated).
    # ------------------------------------------------------------------
    base_cap: float = portfolio.nav * params.max_position_pct_nav

    # ------------------------------------------------------------------
    # Step 4: Volatility-adjusted cap scalar.
    # position_vol=None -> scalar=1.0 (identity; preserves Phase 7C output).
    # max(position_vol, 1e-8) guards against division by zero or near-zero.
    # min(..., 1.0) prevents the scalar from exceeding 1 (no vol-based leverage).
    # ------------------------------------------------------------------
    if position_vol is not None:
        vol_cap_scalar: float = min(
            params.volatility_target_ann / max(position_vol, 1e-8),
            1.0,
        )
    else:
        vol_cap_scalar = 1.0

    # ------------------------------------------------------------------
    # Step 5: Effective cap.
    # vol_cap = base_cap * scalar. effective_cap = min(base_cap, vol_cap).
    # When scalar=1.0: vol_cap == base_cap -> effective_cap == base_cap.
    # ------------------------------------------------------------------
    effective_cap: float = min(base_cap, base_cap * vol_cap_scalar)

    # ------------------------------------------------------------------
    # Step 6: Raw target capped at effective_cap.
    # ------------------------------------------------------------------
    raw_target: float = min(requested_notional, effective_cap)

    # ------------------------------------------------------------------
    # Step 7: Kelly fraction.
    # kelly_fraction is validated in (0.0, 1.0] by RiskParameters.
    # No guard needed; always reduces or preserves raw_target.
    # ------------------------------------------------------------------
    kelly_target: float = raw_target * params.kelly_fraction

    # ------------------------------------------------------------------
    # Step 8: REDUCE multiplier (conditional on clamping).
    # REDUCE applies liquidity_haircut_floor only when the position was
    # clamped by the cap (raw_target < requested_notional).
    # When not clamped (position already within cap), REDUCE passes
    # kelly_target through unchanged -- no additional compression.
    # APPROVE always passes kelly_target through unchanged.
    # liquidity_haircut_floor validated in (0.0, 1.0] by RiskParameters.
    # ------------------------------------------------------------------
    _was_clamped: bool = raw_target < requested_notional
    if decision.verdict is RiskVerdict.REDUCE and _was_clamped:
        reduce_target: float = kelly_target * params.liquidity_haircut_floor
    else:
        reduce_target = kelly_target

    # ------------------------------------------------------------------
    # Step 9: Liquidity floor guarantee (INV-SZ-05).
    # Even after Kelly and REDUCE compression, target must be at least
    # liquidity_haircut_floor fraction of the original requested notional.
    # This prevents compound discounting from compressing to near-zero.
    # ------------------------------------------------------------------
    liquidity_floor_value: float = requested_notional * params.liquidity_haircut_floor
    target: float = None

    return PositionSizingResult(
        allowed=True,
        target_notional=target,
        reason=decision.verdict,
    )


# =============================================================================
# SECTION 2 -- SIZE POSITION
# =============================================================================

def x_size_position__mutmut_50(
    position:     PositionSpec,
    portfolio:    PortfolioState,
    params:       RiskParameters,
    decision:     RiskDecision,
    position_vol: Optional[float] = None,
) -> PositionSizingResult:
    """
    Compute the allowed position size given a pre-evaluated RiskDecision.

    Pure function: reads arguments, returns PositionSizingResult.
    No mutation, no global state, no I/O, no side effects.

    Sizing pipeline (fixed order):
        1.  HALT -> return immediately.
        2.  requested_notional = quantity * current_price
        3.  base_cap = nav * max_position_pct_nav
        4.  vol_cap_scalar = min(volatility_target_ann / max(position_vol, 1e-8), 1.0)
                             if position_vol is not None else 1.0
        5.  effective_cap = min(base_cap, base_cap * vol_cap_scalar)
        6.  raw_target = min(requested_notional, effective_cap)
        7.  kelly_target = raw_target * kelly_fraction
        8.  reduce_target = kelly_target * liquidity_haircut_floor  (REDUCE)
                          = kelly_target                             (APPROVE)
        9.  liquidity_floor = requested_notional * liquidity_haircut_floor
        10. target = max(reduce_target, liquidity_floor)

    Args:
        position:     PositionSpec. quantity and current_price derive requested notional.
        portfolio:    PortfolioState. nav used for base cap.
        params:       RiskParameters. All sizing scalars consumed here.
        decision:     RiskDecision from evaluate_position_risk(). Only verdict consumed.
        position_vol: Optional annualised volatility of this position.
                      None -> vol_cap_scalar = 1.0 (no vol adjustment; backward compat).

    Returns:
        PositionSizingResult(allowed, target_notional, reason).
    """
    # ------------------------------------------------------------------
    # Step 1: HALT -- no sizing arithmetic performed.
    # ------------------------------------------------------------------
    if decision.verdict is RiskVerdict.HALT:
        return PositionSizingResult(
            allowed=False,
            target_notional=None,
            reason=decision.verdict,
        )

    # ------------------------------------------------------------------
    # Step 2: Requested notional.
    # quantity and current_price are finite and > 0 (domain-validated).
    # ------------------------------------------------------------------
    requested_notional: float = position.quantity * position.current_price

    # ------------------------------------------------------------------
    # Step 3: Base position cap.
    # nav and max_position_pct_nav are finite and > 0 (domain-validated).
    # ------------------------------------------------------------------
    base_cap: float = portfolio.nav * params.max_position_pct_nav

    # ------------------------------------------------------------------
    # Step 4: Volatility-adjusted cap scalar.
    # position_vol=None -> scalar=1.0 (identity; preserves Phase 7C output).
    # max(position_vol, 1e-8) guards against division by zero or near-zero.
    # min(..., 1.0) prevents the scalar from exceeding 1 (no vol-based leverage).
    # ------------------------------------------------------------------
    if position_vol is not None:
        vol_cap_scalar: float = min(
            params.volatility_target_ann / max(position_vol, 1e-8),
            1.0,
        )
    else:
        vol_cap_scalar = 1.0

    # ------------------------------------------------------------------
    # Step 5: Effective cap.
    # vol_cap = base_cap * scalar. effective_cap = min(base_cap, vol_cap).
    # When scalar=1.0: vol_cap == base_cap -> effective_cap == base_cap.
    # ------------------------------------------------------------------
    effective_cap: float = min(base_cap, base_cap * vol_cap_scalar)

    # ------------------------------------------------------------------
    # Step 6: Raw target capped at effective_cap.
    # ------------------------------------------------------------------
    raw_target: float = min(requested_notional, effective_cap)

    # ------------------------------------------------------------------
    # Step 7: Kelly fraction.
    # kelly_fraction is validated in (0.0, 1.0] by RiskParameters.
    # No guard needed; always reduces or preserves raw_target.
    # ------------------------------------------------------------------
    kelly_target: float = raw_target * params.kelly_fraction

    # ------------------------------------------------------------------
    # Step 8: REDUCE multiplier (conditional on clamping).
    # REDUCE applies liquidity_haircut_floor only when the position was
    # clamped by the cap (raw_target < requested_notional).
    # When not clamped (position already within cap), REDUCE passes
    # kelly_target through unchanged -- no additional compression.
    # APPROVE always passes kelly_target through unchanged.
    # liquidity_haircut_floor validated in (0.0, 1.0] by RiskParameters.
    # ------------------------------------------------------------------
    _was_clamped: bool = raw_target < requested_notional
    if decision.verdict is RiskVerdict.REDUCE and _was_clamped:
        reduce_target: float = kelly_target * params.liquidity_haircut_floor
    else:
        reduce_target = kelly_target

    # ------------------------------------------------------------------
    # Step 9: Liquidity floor guarantee (INV-SZ-05).
    # Even after Kelly and REDUCE compression, target must be at least
    # liquidity_haircut_floor fraction of the original requested notional.
    # This prevents compound discounting from compressing to near-zero.
    # ------------------------------------------------------------------
    liquidity_floor_value: float = requested_notional * params.liquidity_haircut_floor
    target: float = max(None, liquidity_floor_value)

    return PositionSizingResult(
        allowed=True,
        target_notional=target,
        reason=decision.verdict,
    )


# =============================================================================
# SECTION 2 -- SIZE POSITION
# =============================================================================

def x_size_position__mutmut_51(
    position:     PositionSpec,
    portfolio:    PortfolioState,
    params:       RiskParameters,
    decision:     RiskDecision,
    position_vol: Optional[float] = None,
) -> PositionSizingResult:
    """
    Compute the allowed position size given a pre-evaluated RiskDecision.

    Pure function: reads arguments, returns PositionSizingResult.
    No mutation, no global state, no I/O, no side effects.

    Sizing pipeline (fixed order):
        1.  HALT -> return immediately.
        2.  requested_notional = quantity * current_price
        3.  base_cap = nav * max_position_pct_nav
        4.  vol_cap_scalar = min(volatility_target_ann / max(position_vol, 1e-8), 1.0)
                             if position_vol is not None else 1.0
        5.  effective_cap = min(base_cap, base_cap * vol_cap_scalar)
        6.  raw_target = min(requested_notional, effective_cap)
        7.  kelly_target = raw_target * kelly_fraction
        8.  reduce_target = kelly_target * liquidity_haircut_floor  (REDUCE)
                          = kelly_target                             (APPROVE)
        9.  liquidity_floor = requested_notional * liquidity_haircut_floor
        10. target = max(reduce_target, liquidity_floor)

    Args:
        position:     PositionSpec. quantity and current_price derive requested notional.
        portfolio:    PortfolioState. nav used for base cap.
        params:       RiskParameters. All sizing scalars consumed here.
        decision:     RiskDecision from evaluate_position_risk(). Only verdict consumed.
        position_vol: Optional annualised volatility of this position.
                      None -> vol_cap_scalar = 1.0 (no vol adjustment; backward compat).

    Returns:
        PositionSizingResult(allowed, target_notional, reason).
    """
    # ------------------------------------------------------------------
    # Step 1: HALT -- no sizing arithmetic performed.
    # ------------------------------------------------------------------
    if decision.verdict is RiskVerdict.HALT:
        return PositionSizingResult(
            allowed=False,
            target_notional=None,
            reason=decision.verdict,
        )

    # ------------------------------------------------------------------
    # Step 2: Requested notional.
    # quantity and current_price are finite and > 0 (domain-validated).
    # ------------------------------------------------------------------
    requested_notional: float = position.quantity * position.current_price

    # ------------------------------------------------------------------
    # Step 3: Base position cap.
    # nav and max_position_pct_nav are finite and > 0 (domain-validated).
    # ------------------------------------------------------------------
    base_cap: float = portfolio.nav * params.max_position_pct_nav

    # ------------------------------------------------------------------
    # Step 4: Volatility-adjusted cap scalar.
    # position_vol=None -> scalar=1.0 (identity; preserves Phase 7C output).
    # max(position_vol, 1e-8) guards against division by zero or near-zero.
    # min(..., 1.0) prevents the scalar from exceeding 1 (no vol-based leverage).
    # ------------------------------------------------------------------
    if position_vol is not None:
        vol_cap_scalar: float = min(
            params.volatility_target_ann / max(position_vol, 1e-8),
            1.0,
        )
    else:
        vol_cap_scalar = 1.0

    # ------------------------------------------------------------------
    # Step 5: Effective cap.
    # vol_cap = base_cap * scalar. effective_cap = min(base_cap, vol_cap).
    # When scalar=1.0: vol_cap == base_cap -> effective_cap == base_cap.
    # ------------------------------------------------------------------
    effective_cap: float = min(base_cap, base_cap * vol_cap_scalar)

    # ------------------------------------------------------------------
    # Step 6: Raw target capped at effective_cap.
    # ------------------------------------------------------------------
    raw_target: float = min(requested_notional, effective_cap)

    # ------------------------------------------------------------------
    # Step 7: Kelly fraction.
    # kelly_fraction is validated in (0.0, 1.0] by RiskParameters.
    # No guard needed; always reduces or preserves raw_target.
    # ------------------------------------------------------------------
    kelly_target: float = raw_target * params.kelly_fraction

    # ------------------------------------------------------------------
    # Step 8: REDUCE multiplier (conditional on clamping).
    # REDUCE applies liquidity_haircut_floor only when the position was
    # clamped by the cap (raw_target < requested_notional).
    # When not clamped (position already within cap), REDUCE passes
    # kelly_target through unchanged -- no additional compression.
    # APPROVE always passes kelly_target through unchanged.
    # liquidity_haircut_floor validated in (0.0, 1.0] by RiskParameters.
    # ------------------------------------------------------------------
    _was_clamped: bool = raw_target < requested_notional
    if decision.verdict is RiskVerdict.REDUCE and _was_clamped:
        reduce_target: float = kelly_target * params.liquidity_haircut_floor
    else:
        reduce_target = kelly_target

    # ------------------------------------------------------------------
    # Step 9: Liquidity floor guarantee (INV-SZ-05).
    # Even after Kelly and REDUCE compression, target must be at least
    # liquidity_haircut_floor fraction of the original requested notional.
    # This prevents compound discounting from compressing to near-zero.
    # ------------------------------------------------------------------
    liquidity_floor_value: float = requested_notional * params.liquidity_haircut_floor
    target: float = max(reduce_target, None)

    return PositionSizingResult(
        allowed=True,
        target_notional=target,
        reason=decision.verdict,
    )


# =============================================================================
# SECTION 2 -- SIZE POSITION
# =============================================================================

def x_size_position__mutmut_52(
    position:     PositionSpec,
    portfolio:    PortfolioState,
    params:       RiskParameters,
    decision:     RiskDecision,
    position_vol: Optional[float] = None,
) -> PositionSizingResult:
    """
    Compute the allowed position size given a pre-evaluated RiskDecision.

    Pure function: reads arguments, returns PositionSizingResult.
    No mutation, no global state, no I/O, no side effects.

    Sizing pipeline (fixed order):
        1.  HALT -> return immediately.
        2.  requested_notional = quantity * current_price
        3.  base_cap = nav * max_position_pct_nav
        4.  vol_cap_scalar = min(volatility_target_ann / max(position_vol, 1e-8), 1.0)
                             if position_vol is not None else 1.0
        5.  effective_cap = min(base_cap, base_cap * vol_cap_scalar)
        6.  raw_target = min(requested_notional, effective_cap)
        7.  kelly_target = raw_target * kelly_fraction
        8.  reduce_target = kelly_target * liquidity_haircut_floor  (REDUCE)
                          = kelly_target                             (APPROVE)
        9.  liquidity_floor = requested_notional * liquidity_haircut_floor
        10. target = max(reduce_target, liquidity_floor)

    Args:
        position:     PositionSpec. quantity and current_price derive requested notional.
        portfolio:    PortfolioState. nav used for base cap.
        params:       RiskParameters. All sizing scalars consumed here.
        decision:     RiskDecision from evaluate_position_risk(). Only verdict consumed.
        position_vol: Optional annualised volatility of this position.
                      None -> vol_cap_scalar = 1.0 (no vol adjustment; backward compat).

    Returns:
        PositionSizingResult(allowed, target_notional, reason).
    """
    # ------------------------------------------------------------------
    # Step 1: HALT -- no sizing arithmetic performed.
    # ------------------------------------------------------------------
    if decision.verdict is RiskVerdict.HALT:
        return PositionSizingResult(
            allowed=False,
            target_notional=None,
            reason=decision.verdict,
        )

    # ------------------------------------------------------------------
    # Step 2: Requested notional.
    # quantity and current_price are finite and > 0 (domain-validated).
    # ------------------------------------------------------------------
    requested_notional: float = position.quantity * position.current_price

    # ------------------------------------------------------------------
    # Step 3: Base position cap.
    # nav and max_position_pct_nav are finite and > 0 (domain-validated).
    # ------------------------------------------------------------------
    base_cap: float = portfolio.nav * params.max_position_pct_nav

    # ------------------------------------------------------------------
    # Step 4: Volatility-adjusted cap scalar.
    # position_vol=None -> scalar=1.0 (identity; preserves Phase 7C output).
    # max(position_vol, 1e-8) guards against division by zero or near-zero.
    # min(..., 1.0) prevents the scalar from exceeding 1 (no vol-based leverage).
    # ------------------------------------------------------------------
    if position_vol is not None:
        vol_cap_scalar: float = min(
            params.volatility_target_ann / max(position_vol, 1e-8),
            1.0,
        )
    else:
        vol_cap_scalar = 1.0

    # ------------------------------------------------------------------
    # Step 5: Effective cap.
    # vol_cap = base_cap * scalar. effective_cap = min(base_cap, vol_cap).
    # When scalar=1.0: vol_cap == base_cap -> effective_cap == base_cap.
    # ------------------------------------------------------------------
    effective_cap: float = min(base_cap, base_cap * vol_cap_scalar)

    # ------------------------------------------------------------------
    # Step 6: Raw target capped at effective_cap.
    # ------------------------------------------------------------------
    raw_target: float = min(requested_notional, effective_cap)

    # ------------------------------------------------------------------
    # Step 7: Kelly fraction.
    # kelly_fraction is validated in (0.0, 1.0] by RiskParameters.
    # No guard needed; always reduces or preserves raw_target.
    # ------------------------------------------------------------------
    kelly_target: float = raw_target * params.kelly_fraction

    # ------------------------------------------------------------------
    # Step 8: REDUCE multiplier (conditional on clamping).
    # REDUCE applies liquidity_haircut_floor only when the position was
    # clamped by the cap (raw_target < requested_notional).
    # When not clamped (position already within cap), REDUCE passes
    # kelly_target through unchanged -- no additional compression.
    # APPROVE always passes kelly_target through unchanged.
    # liquidity_haircut_floor validated in (0.0, 1.0] by RiskParameters.
    # ------------------------------------------------------------------
    _was_clamped: bool = raw_target < requested_notional
    if decision.verdict is RiskVerdict.REDUCE and _was_clamped:
        reduce_target: float = kelly_target * params.liquidity_haircut_floor
    else:
        reduce_target = kelly_target

    # ------------------------------------------------------------------
    # Step 9: Liquidity floor guarantee (INV-SZ-05).
    # Even after Kelly and REDUCE compression, target must be at least
    # liquidity_haircut_floor fraction of the original requested notional.
    # This prevents compound discounting from compressing to near-zero.
    # ------------------------------------------------------------------
    liquidity_floor_value: float = requested_notional * params.liquidity_haircut_floor
    target: float = max(liquidity_floor_value)

    return PositionSizingResult(
        allowed=True,
        target_notional=target,
        reason=decision.verdict,
    )


# =============================================================================
# SECTION 2 -- SIZE POSITION
# =============================================================================

def x_size_position__mutmut_53(
    position:     PositionSpec,
    portfolio:    PortfolioState,
    params:       RiskParameters,
    decision:     RiskDecision,
    position_vol: Optional[float] = None,
) -> PositionSizingResult:
    """
    Compute the allowed position size given a pre-evaluated RiskDecision.

    Pure function: reads arguments, returns PositionSizingResult.
    No mutation, no global state, no I/O, no side effects.

    Sizing pipeline (fixed order):
        1.  HALT -> return immediately.
        2.  requested_notional = quantity * current_price
        3.  base_cap = nav * max_position_pct_nav
        4.  vol_cap_scalar = min(volatility_target_ann / max(position_vol, 1e-8), 1.0)
                             if position_vol is not None else 1.0
        5.  effective_cap = min(base_cap, base_cap * vol_cap_scalar)
        6.  raw_target = min(requested_notional, effective_cap)
        7.  kelly_target = raw_target * kelly_fraction
        8.  reduce_target = kelly_target * liquidity_haircut_floor  (REDUCE)
                          = kelly_target                             (APPROVE)
        9.  liquidity_floor = requested_notional * liquidity_haircut_floor
        10. target = max(reduce_target, liquidity_floor)

    Args:
        position:     PositionSpec. quantity and current_price derive requested notional.
        portfolio:    PortfolioState. nav used for base cap.
        params:       RiskParameters. All sizing scalars consumed here.
        decision:     RiskDecision from evaluate_position_risk(). Only verdict consumed.
        position_vol: Optional annualised volatility of this position.
                      None -> vol_cap_scalar = 1.0 (no vol adjustment; backward compat).

    Returns:
        PositionSizingResult(allowed, target_notional, reason).
    """
    # ------------------------------------------------------------------
    # Step 1: HALT -- no sizing arithmetic performed.
    # ------------------------------------------------------------------
    if decision.verdict is RiskVerdict.HALT:
        return PositionSizingResult(
            allowed=False,
            target_notional=None,
            reason=decision.verdict,
        )

    # ------------------------------------------------------------------
    # Step 2: Requested notional.
    # quantity and current_price are finite and > 0 (domain-validated).
    # ------------------------------------------------------------------
    requested_notional: float = position.quantity * position.current_price

    # ------------------------------------------------------------------
    # Step 3: Base position cap.
    # nav and max_position_pct_nav are finite and > 0 (domain-validated).
    # ------------------------------------------------------------------
    base_cap: float = portfolio.nav * params.max_position_pct_nav

    # ------------------------------------------------------------------
    # Step 4: Volatility-adjusted cap scalar.
    # position_vol=None -> scalar=1.0 (identity; preserves Phase 7C output).
    # max(position_vol, 1e-8) guards against division by zero or near-zero.
    # min(..., 1.0) prevents the scalar from exceeding 1 (no vol-based leverage).
    # ------------------------------------------------------------------
    if position_vol is not None:
        vol_cap_scalar: float = min(
            params.volatility_target_ann / max(position_vol, 1e-8),
            1.0,
        )
    else:
        vol_cap_scalar = 1.0

    # ------------------------------------------------------------------
    # Step 5: Effective cap.
    # vol_cap = base_cap * scalar. effective_cap = min(base_cap, vol_cap).
    # When scalar=1.0: vol_cap == base_cap -> effective_cap == base_cap.
    # ------------------------------------------------------------------
    effective_cap: float = min(base_cap, base_cap * vol_cap_scalar)

    # ------------------------------------------------------------------
    # Step 6: Raw target capped at effective_cap.
    # ------------------------------------------------------------------
    raw_target: float = min(requested_notional, effective_cap)

    # ------------------------------------------------------------------
    # Step 7: Kelly fraction.
    # kelly_fraction is validated in (0.0, 1.0] by RiskParameters.
    # No guard needed; always reduces or preserves raw_target.
    # ------------------------------------------------------------------
    kelly_target: float = raw_target * params.kelly_fraction

    # ------------------------------------------------------------------
    # Step 8: REDUCE multiplier (conditional on clamping).
    # REDUCE applies liquidity_haircut_floor only when the position was
    # clamped by the cap (raw_target < requested_notional).
    # When not clamped (position already within cap), REDUCE passes
    # kelly_target through unchanged -- no additional compression.
    # APPROVE always passes kelly_target through unchanged.
    # liquidity_haircut_floor validated in (0.0, 1.0] by RiskParameters.
    # ------------------------------------------------------------------
    _was_clamped: bool = raw_target < requested_notional
    if decision.verdict is RiskVerdict.REDUCE and _was_clamped:
        reduce_target: float = kelly_target * params.liquidity_haircut_floor
    else:
        reduce_target = kelly_target

    # ------------------------------------------------------------------
    # Step 9: Liquidity floor guarantee (INV-SZ-05).
    # Even after Kelly and REDUCE compression, target must be at least
    # liquidity_haircut_floor fraction of the original requested notional.
    # This prevents compound discounting from compressing to near-zero.
    # ------------------------------------------------------------------
    liquidity_floor_value: float = requested_notional * params.liquidity_haircut_floor
    target: float = max(reduce_target, )

    return PositionSizingResult(
        allowed=True,
        target_notional=target,
        reason=decision.verdict,
    )


# =============================================================================
# SECTION 2 -- SIZE POSITION
# =============================================================================

def x_size_position__mutmut_54(
    position:     PositionSpec,
    portfolio:    PortfolioState,
    params:       RiskParameters,
    decision:     RiskDecision,
    position_vol: Optional[float] = None,
) -> PositionSizingResult:
    """
    Compute the allowed position size given a pre-evaluated RiskDecision.

    Pure function: reads arguments, returns PositionSizingResult.
    No mutation, no global state, no I/O, no side effects.

    Sizing pipeline (fixed order):
        1.  HALT -> return immediately.
        2.  requested_notional = quantity * current_price
        3.  base_cap = nav * max_position_pct_nav
        4.  vol_cap_scalar = min(volatility_target_ann / max(position_vol, 1e-8), 1.0)
                             if position_vol is not None else 1.0
        5.  effective_cap = min(base_cap, base_cap * vol_cap_scalar)
        6.  raw_target = min(requested_notional, effective_cap)
        7.  kelly_target = raw_target * kelly_fraction
        8.  reduce_target = kelly_target * liquidity_haircut_floor  (REDUCE)
                          = kelly_target                             (APPROVE)
        9.  liquidity_floor = requested_notional * liquidity_haircut_floor
        10. target = max(reduce_target, liquidity_floor)

    Args:
        position:     PositionSpec. quantity and current_price derive requested notional.
        portfolio:    PortfolioState. nav used for base cap.
        params:       RiskParameters. All sizing scalars consumed here.
        decision:     RiskDecision from evaluate_position_risk(). Only verdict consumed.
        position_vol: Optional annualised volatility of this position.
                      None -> vol_cap_scalar = 1.0 (no vol adjustment; backward compat).

    Returns:
        PositionSizingResult(allowed, target_notional, reason).
    """
    # ------------------------------------------------------------------
    # Step 1: HALT -- no sizing arithmetic performed.
    # ------------------------------------------------------------------
    if decision.verdict is RiskVerdict.HALT:
        return PositionSizingResult(
            allowed=False,
            target_notional=None,
            reason=decision.verdict,
        )

    # ------------------------------------------------------------------
    # Step 2: Requested notional.
    # quantity and current_price are finite and > 0 (domain-validated).
    # ------------------------------------------------------------------
    requested_notional: float = position.quantity * position.current_price

    # ------------------------------------------------------------------
    # Step 3: Base position cap.
    # nav and max_position_pct_nav are finite and > 0 (domain-validated).
    # ------------------------------------------------------------------
    base_cap: float = portfolio.nav * params.max_position_pct_nav

    # ------------------------------------------------------------------
    # Step 4: Volatility-adjusted cap scalar.
    # position_vol=None -> scalar=1.0 (identity; preserves Phase 7C output).
    # max(position_vol, 1e-8) guards against division by zero or near-zero.
    # min(..., 1.0) prevents the scalar from exceeding 1 (no vol-based leverage).
    # ------------------------------------------------------------------
    if position_vol is not None:
        vol_cap_scalar: float = min(
            params.volatility_target_ann / max(position_vol, 1e-8),
            1.0,
        )
    else:
        vol_cap_scalar = 1.0

    # ------------------------------------------------------------------
    # Step 5: Effective cap.
    # vol_cap = base_cap * scalar. effective_cap = min(base_cap, vol_cap).
    # When scalar=1.0: vol_cap == base_cap -> effective_cap == base_cap.
    # ------------------------------------------------------------------
    effective_cap: float = min(base_cap, base_cap * vol_cap_scalar)

    # ------------------------------------------------------------------
    # Step 6: Raw target capped at effective_cap.
    # ------------------------------------------------------------------
    raw_target: float = min(requested_notional, effective_cap)

    # ------------------------------------------------------------------
    # Step 7: Kelly fraction.
    # kelly_fraction is validated in (0.0, 1.0] by RiskParameters.
    # No guard needed; always reduces or preserves raw_target.
    # ------------------------------------------------------------------
    kelly_target: float = raw_target * params.kelly_fraction

    # ------------------------------------------------------------------
    # Step 8: REDUCE multiplier (conditional on clamping).
    # REDUCE applies liquidity_haircut_floor only when the position was
    # clamped by the cap (raw_target < requested_notional).
    # When not clamped (position already within cap), REDUCE passes
    # kelly_target through unchanged -- no additional compression.
    # APPROVE always passes kelly_target through unchanged.
    # liquidity_haircut_floor validated in (0.0, 1.0] by RiskParameters.
    # ------------------------------------------------------------------
    _was_clamped: bool = raw_target < requested_notional
    if decision.verdict is RiskVerdict.REDUCE and _was_clamped:
        reduce_target: float = kelly_target * params.liquidity_haircut_floor
    else:
        reduce_target = kelly_target

    # ------------------------------------------------------------------
    # Step 9: Liquidity floor guarantee (INV-SZ-05).
    # Even after Kelly and REDUCE compression, target must be at least
    # liquidity_haircut_floor fraction of the original requested notional.
    # This prevents compound discounting from compressing to near-zero.
    # ------------------------------------------------------------------
    liquidity_floor_value: float = requested_notional * params.liquidity_haircut_floor
    target: float = max(reduce_target, liquidity_floor_value)

    return PositionSizingResult(
        allowed=None,
        target_notional=target,
        reason=decision.verdict,
    )


# =============================================================================
# SECTION 2 -- SIZE POSITION
# =============================================================================

def x_size_position__mutmut_55(
    position:     PositionSpec,
    portfolio:    PortfolioState,
    params:       RiskParameters,
    decision:     RiskDecision,
    position_vol: Optional[float] = None,
) -> PositionSizingResult:
    """
    Compute the allowed position size given a pre-evaluated RiskDecision.

    Pure function: reads arguments, returns PositionSizingResult.
    No mutation, no global state, no I/O, no side effects.

    Sizing pipeline (fixed order):
        1.  HALT -> return immediately.
        2.  requested_notional = quantity * current_price
        3.  base_cap = nav * max_position_pct_nav
        4.  vol_cap_scalar = min(volatility_target_ann / max(position_vol, 1e-8), 1.0)
                             if position_vol is not None else 1.0
        5.  effective_cap = min(base_cap, base_cap * vol_cap_scalar)
        6.  raw_target = min(requested_notional, effective_cap)
        7.  kelly_target = raw_target * kelly_fraction
        8.  reduce_target = kelly_target * liquidity_haircut_floor  (REDUCE)
                          = kelly_target                             (APPROVE)
        9.  liquidity_floor = requested_notional * liquidity_haircut_floor
        10. target = max(reduce_target, liquidity_floor)

    Args:
        position:     PositionSpec. quantity and current_price derive requested notional.
        portfolio:    PortfolioState. nav used for base cap.
        params:       RiskParameters. All sizing scalars consumed here.
        decision:     RiskDecision from evaluate_position_risk(). Only verdict consumed.
        position_vol: Optional annualised volatility of this position.
                      None -> vol_cap_scalar = 1.0 (no vol adjustment; backward compat).

    Returns:
        PositionSizingResult(allowed, target_notional, reason).
    """
    # ------------------------------------------------------------------
    # Step 1: HALT -- no sizing arithmetic performed.
    # ------------------------------------------------------------------
    if decision.verdict is RiskVerdict.HALT:
        return PositionSizingResult(
            allowed=False,
            target_notional=None,
            reason=decision.verdict,
        )

    # ------------------------------------------------------------------
    # Step 2: Requested notional.
    # quantity and current_price are finite and > 0 (domain-validated).
    # ------------------------------------------------------------------
    requested_notional: float = position.quantity * position.current_price

    # ------------------------------------------------------------------
    # Step 3: Base position cap.
    # nav and max_position_pct_nav are finite and > 0 (domain-validated).
    # ------------------------------------------------------------------
    base_cap: float = portfolio.nav * params.max_position_pct_nav

    # ------------------------------------------------------------------
    # Step 4: Volatility-adjusted cap scalar.
    # position_vol=None -> scalar=1.0 (identity; preserves Phase 7C output).
    # max(position_vol, 1e-8) guards against division by zero or near-zero.
    # min(..., 1.0) prevents the scalar from exceeding 1 (no vol-based leverage).
    # ------------------------------------------------------------------
    if position_vol is not None:
        vol_cap_scalar: float = min(
            params.volatility_target_ann / max(position_vol, 1e-8),
            1.0,
        )
    else:
        vol_cap_scalar = 1.0

    # ------------------------------------------------------------------
    # Step 5: Effective cap.
    # vol_cap = base_cap * scalar. effective_cap = min(base_cap, vol_cap).
    # When scalar=1.0: vol_cap == base_cap -> effective_cap == base_cap.
    # ------------------------------------------------------------------
    effective_cap: float = min(base_cap, base_cap * vol_cap_scalar)

    # ------------------------------------------------------------------
    # Step 6: Raw target capped at effective_cap.
    # ------------------------------------------------------------------
    raw_target: float = min(requested_notional, effective_cap)

    # ------------------------------------------------------------------
    # Step 7: Kelly fraction.
    # kelly_fraction is validated in (0.0, 1.0] by RiskParameters.
    # No guard needed; always reduces or preserves raw_target.
    # ------------------------------------------------------------------
    kelly_target: float = raw_target * params.kelly_fraction

    # ------------------------------------------------------------------
    # Step 8: REDUCE multiplier (conditional on clamping).
    # REDUCE applies liquidity_haircut_floor only when the position was
    # clamped by the cap (raw_target < requested_notional).
    # When not clamped (position already within cap), REDUCE passes
    # kelly_target through unchanged -- no additional compression.
    # APPROVE always passes kelly_target through unchanged.
    # liquidity_haircut_floor validated in (0.0, 1.0] by RiskParameters.
    # ------------------------------------------------------------------
    _was_clamped: bool = raw_target < requested_notional
    if decision.verdict is RiskVerdict.REDUCE and _was_clamped:
        reduce_target: float = kelly_target * params.liquidity_haircut_floor
    else:
        reduce_target = kelly_target

    # ------------------------------------------------------------------
    # Step 9: Liquidity floor guarantee (INV-SZ-05).
    # Even after Kelly and REDUCE compression, target must be at least
    # liquidity_haircut_floor fraction of the original requested notional.
    # This prevents compound discounting from compressing to near-zero.
    # ------------------------------------------------------------------
    liquidity_floor_value: float = requested_notional * params.liquidity_haircut_floor
    target: float = max(reduce_target, liquidity_floor_value)

    return PositionSizingResult(
        allowed=True,
        target_notional=None,
        reason=decision.verdict,
    )


# =============================================================================
# SECTION 2 -- SIZE POSITION
# =============================================================================

def x_size_position__mutmut_56(
    position:     PositionSpec,
    portfolio:    PortfolioState,
    params:       RiskParameters,
    decision:     RiskDecision,
    position_vol: Optional[float] = None,
) -> PositionSizingResult:
    """
    Compute the allowed position size given a pre-evaluated RiskDecision.

    Pure function: reads arguments, returns PositionSizingResult.
    No mutation, no global state, no I/O, no side effects.

    Sizing pipeline (fixed order):
        1.  HALT -> return immediately.
        2.  requested_notional = quantity * current_price
        3.  base_cap = nav * max_position_pct_nav
        4.  vol_cap_scalar = min(volatility_target_ann / max(position_vol, 1e-8), 1.0)
                             if position_vol is not None else 1.0
        5.  effective_cap = min(base_cap, base_cap * vol_cap_scalar)
        6.  raw_target = min(requested_notional, effective_cap)
        7.  kelly_target = raw_target * kelly_fraction
        8.  reduce_target = kelly_target * liquidity_haircut_floor  (REDUCE)
                          = kelly_target                             (APPROVE)
        9.  liquidity_floor = requested_notional * liquidity_haircut_floor
        10. target = max(reduce_target, liquidity_floor)

    Args:
        position:     PositionSpec. quantity and current_price derive requested notional.
        portfolio:    PortfolioState. nav used for base cap.
        params:       RiskParameters. All sizing scalars consumed here.
        decision:     RiskDecision from evaluate_position_risk(). Only verdict consumed.
        position_vol: Optional annualised volatility of this position.
                      None -> vol_cap_scalar = 1.0 (no vol adjustment; backward compat).

    Returns:
        PositionSizingResult(allowed, target_notional, reason).
    """
    # ------------------------------------------------------------------
    # Step 1: HALT -- no sizing arithmetic performed.
    # ------------------------------------------------------------------
    if decision.verdict is RiskVerdict.HALT:
        return PositionSizingResult(
            allowed=False,
            target_notional=None,
            reason=decision.verdict,
        )

    # ------------------------------------------------------------------
    # Step 2: Requested notional.
    # quantity and current_price are finite and > 0 (domain-validated).
    # ------------------------------------------------------------------
    requested_notional: float = position.quantity * position.current_price

    # ------------------------------------------------------------------
    # Step 3: Base position cap.
    # nav and max_position_pct_nav are finite and > 0 (domain-validated).
    # ------------------------------------------------------------------
    base_cap: float = portfolio.nav * params.max_position_pct_nav

    # ------------------------------------------------------------------
    # Step 4: Volatility-adjusted cap scalar.
    # position_vol=None -> scalar=1.0 (identity; preserves Phase 7C output).
    # max(position_vol, 1e-8) guards against division by zero or near-zero.
    # min(..., 1.0) prevents the scalar from exceeding 1 (no vol-based leverage).
    # ------------------------------------------------------------------
    if position_vol is not None:
        vol_cap_scalar: float = min(
            params.volatility_target_ann / max(position_vol, 1e-8),
            1.0,
        )
    else:
        vol_cap_scalar = 1.0

    # ------------------------------------------------------------------
    # Step 5: Effective cap.
    # vol_cap = base_cap * scalar. effective_cap = min(base_cap, vol_cap).
    # When scalar=1.0: vol_cap == base_cap -> effective_cap == base_cap.
    # ------------------------------------------------------------------
    effective_cap: float = min(base_cap, base_cap * vol_cap_scalar)

    # ------------------------------------------------------------------
    # Step 6: Raw target capped at effective_cap.
    # ------------------------------------------------------------------
    raw_target: float = min(requested_notional, effective_cap)

    # ------------------------------------------------------------------
    # Step 7: Kelly fraction.
    # kelly_fraction is validated in (0.0, 1.0] by RiskParameters.
    # No guard needed; always reduces or preserves raw_target.
    # ------------------------------------------------------------------
    kelly_target: float = raw_target * params.kelly_fraction

    # ------------------------------------------------------------------
    # Step 8: REDUCE multiplier (conditional on clamping).
    # REDUCE applies liquidity_haircut_floor only when the position was
    # clamped by the cap (raw_target < requested_notional).
    # When not clamped (position already within cap), REDUCE passes
    # kelly_target through unchanged -- no additional compression.
    # APPROVE always passes kelly_target through unchanged.
    # liquidity_haircut_floor validated in (0.0, 1.0] by RiskParameters.
    # ------------------------------------------------------------------
    _was_clamped: bool = raw_target < requested_notional
    if decision.verdict is RiskVerdict.REDUCE and _was_clamped:
        reduce_target: float = kelly_target * params.liquidity_haircut_floor
    else:
        reduce_target = kelly_target

    # ------------------------------------------------------------------
    # Step 9: Liquidity floor guarantee (INV-SZ-05).
    # Even after Kelly and REDUCE compression, target must be at least
    # liquidity_haircut_floor fraction of the original requested notional.
    # This prevents compound discounting from compressing to near-zero.
    # ------------------------------------------------------------------
    liquidity_floor_value: float = requested_notional * params.liquidity_haircut_floor
    target: float = max(reduce_target, liquidity_floor_value)

    return PositionSizingResult(
        allowed=True,
        target_notional=target,
        reason=None,
    )


# =============================================================================
# SECTION 2 -- SIZE POSITION
# =============================================================================

def x_size_position__mutmut_57(
    position:     PositionSpec,
    portfolio:    PortfolioState,
    params:       RiskParameters,
    decision:     RiskDecision,
    position_vol: Optional[float] = None,
) -> PositionSizingResult:
    """
    Compute the allowed position size given a pre-evaluated RiskDecision.

    Pure function: reads arguments, returns PositionSizingResult.
    No mutation, no global state, no I/O, no side effects.

    Sizing pipeline (fixed order):
        1.  HALT -> return immediately.
        2.  requested_notional = quantity * current_price
        3.  base_cap = nav * max_position_pct_nav
        4.  vol_cap_scalar = min(volatility_target_ann / max(position_vol, 1e-8), 1.0)
                             if position_vol is not None else 1.0
        5.  effective_cap = min(base_cap, base_cap * vol_cap_scalar)
        6.  raw_target = min(requested_notional, effective_cap)
        7.  kelly_target = raw_target * kelly_fraction
        8.  reduce_target = kelly_target * liquidity_haircut_floor  (REDUCE)
                          = kelly_target                             (APPROVE)
        9.  liquidity_floor = requested_notional * liquidity_haircut_floor
        10. target = max(reduce_target, liquidity_floor)

    Args:
        position:     PositionSpec. quantity and current_price derive requested notional.
        portfolio:    PortfolioState. nav used for base cap.
        params:       RiskParameters. All sizing scalars consumed here.
        decision:     RiskDecision from evaluate_position_risk(). Only verdict consumed.
        position_vol: Optional annualised volatility of this position.
                      None -> vol_cap_scalar = 1.0 (no vol adjustment; backward compat).

    Returns:
        PositionSizingResult(allowed, target_notional, reason).
    """
    # ------------------------------------------------------------------
    # Step 1: HALT -- no sizing arithmetic performed.
    # ------------------------------------------------------------------
    if decision.verdict is RiskVerdict.HALT:
        return PositionSizingResult(
            allowed=False,
            target_notional=None,
            reason=decision.verdict,
        )

    # ------------------------------------------------------------------
    # Step 2: Requested notional.
    # quantity and current_price are finite and > 0 (domain-validated).
    # ------------------------------------------------------------------
    requested_notional: float = position.quantity * position.current_price

    # ------------------------------------------------------------------
    # Step 3: Base position cap.
    # nav and max_position_pct_nav are finite and > 0 (domain-validated).
    # ------------------------------------------------------------------
    base_cap: float = portfolio.nav * params.max_position_pct_nav

    # ------------------------------------------------------------------
    # Step 4: Volatility-adjusted cap scalar.
    # position_vol=None -> scalar=1.0 (identity; preserves Phase 7C output).
    # max(position_vol, 1e-8) guards against division by zero or near-zero.
    # min(..., 1.0) prevents the scalar from exceeding 1 (no vol-based leverage).
    # ------------------------------------------------------------------
    if position_vol is not None:
        vol_cap_scalar: float = min(
            params.volatility_target_ann / max(position_vol, 1e-8),
            1.0,
        )
    else:
        vol_cap_scalar = 1.0

    # ------------------------------------------------------------------
    # Step 5: Effective cap.
    # vol_cap = base_cap * scalar. effective_cap = min(base_cap, vol_cap).
    # When scalar=1.0: vol_cap == base_cap -> effective_cap == base_cap.
    # ------------------------------------------------------------------
    effective_cap: float = min(base_cap, base_cap * vol_cap_scalar)

    # ------------------------------------------------------------------
    # Step 6: Raw target capped at effective_cap.
    # ------------------------------------------------------------------
    raw_target: float = min(requested_notional, effective_cap)

    # ------------------------------------------------------------------
    # Step 7: Kelly fraction.
    # kelly_fraction is validated in (0.0, 1.0] by RiskParameters.
    # No guard needed; always reduces or preserves raw_target.
    # ------------------------------------------------------------------
    kelly_target: float = raw_target * params.kelly_fraction

    # ------------------------------------------------------------------
    # Step 8: REDUCE multiplier (conditional on clamping).
    # REDUCE applies liquidity_haircut_floor only when the position was
    # clamped by the cap (raw_target < requested_notional).
    # When not clamped (position already within cap), REDUCE passes
    # kelly_target through unchanged -- no additional compression.
    # APPROVE always passes kelly_target through unchanged.
    # liquidity_haircut_floor validated in (0.0, 1.0] by RiskParameters.
    # ------------------------------------------------------------------
    _was_clamped: bool = raw_target < requested_notional
    if decision.verdict is RiskVerdict.REDUCE and _was_clamped:
        reduce_target: float = kelly_target * params.liquidity_haircut_floor
    else:
        reduce_target = kelly_target

    # ------------------------------------------------------------------
    # Step 9: Liquidity floor guarantee (INV-SZ-05).
    # Even after Kelly and REDUCE compression, target must be at least
    # liquidity_haircut_floor fraction of the original requested notional.
    # This prevents compound discounting from compressing to near-zero.
    # ------------------------------------------------------------------
    liquidity_floor_value: float = requested_notional * params.liquidity_haircut_floor
    target: float = max(reduce_target, liquidity_floor_value)

    return PositionSizingResult(
        target_notional=target,
        reason=decision.verdict,
    )


# =============================================================================
# SECTION 2 -- SIZE POSITION
# =============================================================================

def x_size_position__mutmut_58(
    position:     PositionSpec,
    portfolio:    PortfolioState,
    params:       RiskParameters,
    decision:     RiskDecision,
    position_vol: Optional[float] = None,
) -> PositionSizingResult:
    """
    Compute the allowed position size given a pre-evaluated RiskDecision.

    Pure function: reads arguments, returns PositionSizingResult.
    No mutation, no global state, no I/O, no side effects.

    Sizing pipeline (fixed order):
        1.  HALT -> return immediately.
        2.  requested_notional = quantity * current_price
        3.  base_cap = nav * max_position_pct_nav
        4.  vol_cap_scalar = min(volatility_target_ann / max(position_vol, 1e-8), 1.0)
                             if position_vol is not None else 1.0
        5.  effective_cap = min(base_cap, base_cap * vol_cap_scalar)
        6.  raw_target = min(requested_notional, effective_cap)
        7.  kelly_target = raw_target * kelly_fraction
        8.  reduce_target = kelly_target * liquidity_haircut_floor  (REDUCE)
                          = kelly_target                             (APPROVE)
        9.  liquidity_floor = requested_notional * liquidity_haircut_floor
        10. target = max(reduce_target, liquidity_floor)

    Args:
        position:     PositionSpec. quantity and current_price derive requested notional.
        portfolio:    PortfolioState. nav used for base cap.
        params:       RiskParameters. All sizing scalars consumed here.
        decision:     RiskDecision from evaluate_position_risk(). Only verdict consumed.
        position_vol: Optional annualised volatility of this position.
                      None -> vol_cap_scalar = 1.0 (no vol adjustment; backward compat).

    Returns:
        PositionSizingResult(allowed, target_notional, reason).
    """
    # ------------------------------------------------------------------
    # Step 1: HALT -- no sizing arithmetic performed.
    # ------------------------------------------------------------------
    if decision.verdict is RiskVerdict.HALT:
        return PositionSizingResult(
            allowed=False,
            target_notional=None,
            reason=decision.verdict,
        )

    # ------------------------------------------------------------------
    # Step 2: Requested notional.
    # quantity and current_price are finite and > 0 (domain-validated).
    # ------------------------------------------------------------------
    requested_notional: float = position.quantity * position.current_price

    # ------------------------------------------------------------------
    # Step 3: Base position cap.
    # nav and max_position_pct_nav are finite and > 0 (domain-validated).
    # ------------------------------------------------------------------
    base_cap: float = portfolio.nav * params.max_position_pct_nav

    # ------------------------------------------------------------------
    # Step 4: Volatility-adjusted cap scalar.
    # position_vol=None -> scalar=1.0 (identity; preserves Phase 7C output).
    # max(position_vol, 1e-8) guards against division by zero or near-zero.
    # min(..., 1.0) prevents the scalar from exceeding 1 (no vol-based leverage).
    # ------------------------------------------------------------------
    if position_vol is not None:
        vol_cap_scalar: float = min(
            params.volatility_target_ann / max(position_vol, 1e-8),
            1.0,
        )
    else:
        vol_cap_scalar = 1.0

    # ------------------------------------------------------------------
    # Step 5: Effective cap.
    # vol_cap = base_cap * scalar. effective_cap = min(base_cap, vol_cap).
    # When scalar=1.0: vol_cap == base_cap -> effective_cap == base_cap.
    # ------------------------------------------------------------------
    effective_cap: float = min(base_cap, base_cap * vol_cap_scalar)

    # ------------------------------------------------------------------
    # Step 6: Raw target capped at effective_cap.
    # ------------------------------------------------------------------
    raw_target: float = min(requested_notional, effective_cap)

    # ------------------------------------------------------------------
    # Step 7: Kelly fraction.
    # kelly_fraction is validated in (0.0, 1.0] by RiskParameters.
    # No guard needed; always reduces or preserves raw_target.
    # ------------------------------------------------------------------
    kelly_target: float = raw_target * params.kelly_fraction

    # ------------------------------------------------------------------
    # Step 8: REDUCE multiplier (conditional on clamping).
    # REDUCE applies liquidity_haircut_floor only when the position was
    # clamped by the cap (raw_target < requested_notional).
    # When not clamped (position already within cap), REDUCE passes
    # kelly_target through unchanged -- no additional compression.
    # APPROVE always passes kelly_target through unchanged.
    # liquidity_haircut_floor validated in (0.0, 1.0] by RiskParameters.
    # ------------------------------------------------------------------
    _was_clamped: bool = raw_target < requested_notional
    if decision.verdict is RiskVerdict.REDUCE and _was_clamped:
        reduce_target: float = kelly_target * params.liquidity_haircut_floor
    else:
        reduce_target = kelly_target

    # ------------------------------------------------------------------
    # Step 9: Liquidity floor guarantee (INV-SZ-05).
    # Even after Kelly and REDUCE compression, target must be at least
    # liquidity_haircut_floor fraction of the original requested notional.
    # This prevents compound discounting from compressing to near-zero.
    # ------------------------------------------------------------------
    liquidity_floor_value: float = requested_notional * params.liquidity_haircut_floor
    target: float = max(reduce_target, liquidity_floor_value)

    return PositionSizingResult(
        allowed=True,
        reason=decision.verdict,
    )


# =============================================================================
# SECTION 2 -- SIZE POSITION
# =============================================================================

def x_size_position__mutmut_59(
    position:     PositionSpec,
    portfolio:    PortfolioState,
    params:       RiskParameters,
    decision:     RiskDecision,
    position_vol: Optional[float] = None,
) -> PositionSizingResult:
    """
    Compute the allowed position size given a pre-evaluated RiskDecision.

    Pure function: reads arguments, returns PositionSizingResult.
    No mutation, no global state, no I/O, no side effects.

    Sizing pipeline (fixed order):
        1.  HALT -> return immediately.
        2.  requested_notional = quantity * current_price
        3.  base_cap = nav * max_position_pct_nav
        4.  vol_cap_scalar = min(volatility_target_ann / max(position_vol, 1e-8), 1.0)
                             if position_vol is not None else 1.0
        5.  effective_cap = min(base_cap, base_cap * vol_cap_scalar)
        6.  raw_target = min(requested_notional, effective_cap)
        7.  kelly_target = raw_target * kelly_fraction
        8.  reduce_target = kelly_target * liquidity_haircut_floor  (REDUCE)
                          = kelly_target                             (APPROVE)
        9.  liquidity_floor = requested_notional * liquidity_haircut_floor
        10. target = max(reduce_target, liquidity_floor)

    Args:
        position:     PositionSpec. quantity and current_price derive requested notional.
        portfolio:    PortfolioState. nav used for base cap.
        params:       RiskParameters. All sizing scalars consumed here.
        decision:     RiskDecision from evaluate_position_risk(). Only verdict consumed.
        position_vol: Optional annualised volatility of this position.
                      None -> vol_cap_scalar = 1.0 (no vol adjustment; backward compat).

    Returns:
        PositionSizingResult(allowed, target_notional, reason).
    """
    # ------------------------------------------------------------------
    # Step 1: HALT -- no sizing arithmetic performed.
    # ------------------------------------------------------------------
    if decision.verdict is RiskVerdict.HALT:
        return PositionSizingResult(
            allowed=False,
            target_notional=None,
            reason=decision.verdict,
        )

    # ------------------------------------------------------------------
    # Step 2: Requested notional.
    # quantity and current_price are finite and > 0 (domain-validated).
    # ------------------------------------------------------------------
    requested_notional: float = position.quantity * position.current_price

    # ------------------------------------------------------------------
    # Step 3: Base position cap.
    # nav and max_position_pct_nav are finite and > 0 (domain-validated).
    # ------------------------------------------------------------------
    base_cap: float = portfolio.nav * params.max_position_pct_nav

    # ------------------------------------------------------------------
    # Step 4: Volatility-adjusted cap scalar.
    # position_vol=None -> scalar=1.0 (identity; preserves Phase 7C output).
    # max(position_vol, 1e-8) guards against division by zero or near-zero.
    # min(..., 1.0) prevents the scalar from exceeding 1 (no vol-based leverage).
    # ------------------------------------------------------------------
    if position_vol is not None:
        vol_cap_scalar: float = min(
            params.volatility_target_ann / max(position_vol, 1e-8),
            1.0,
        )
    else:
        vol_cap_scalar = 1.0

    # ------------------------------------------------------------------
    # Step 5: Effective cap.
    # vol_cap = base_cap * scalar. effective_cap = min(base_cap, vol_cap).
    # When scalar=1.0: vol_cap == base_cap -> effective_cap == base_cap.
    # ------------------------------------------------------------------
    effective_cap: float = min(base_cap, base_cap * vol_cap_scalar)

    # ------------------------------------------------------------------
    # Step 6: Raw target capped at effective_cap.
    # ------------------------------------------------------------------
    raw_target: float = min(requested_notional, effective_cap)

    # ------------------------------------------------------------------
    # Step 7: Kelly fraction.
    # kelly_fraction is validated in (0.0, 1.0] by RiskParameters.
    # No guard needed; always reduces or preserves raw_target.
    # ------------------------------------------------------------------
    kelly_target: float = raw_target * params.kelly_fraction

    # ------------------------------------------------------------------
    # Step 8: REDUCE multiplier (conditional on clamping).
    # REDUCE applies liquidity_haircut_floor only when the position was
    # clamped by the cap (raw_target < requested_notional).
    # When not clamped (position already within cap), REDUCE passes
    # kelly_target through unchanged -- no additional compression.
    # APPROVE always passes kelly_target through unchanged.
    # liquidity_haircut_floor validated in (0.0, 1.0] by RiskParameters.
    # ------------------------------------------------------------------
    _was_clamped: bool = raw_target < requested_notional
    if decision.verdict is RiskVerdict.REDUCE and _was_clamped:
        reduce_target: float = kelly_target * params.liquidity_haircut_floor
    else:
        reduce_target = kelly_target

    # ------------------------------------------------------------------
    # Step 9: Liquidity floor guarantee (INV-SZ-05).
    # Even after Kelly and REDUCE compression, target must be at least
    # liquidity_haircut_floor fraction of the original requested notional.
    # This prevents compound discounting from compressing to near-zero.
    # ------------------------------------------------------------------
    liquidity_floor_value: float = requested_notional * params.liquidity_haircut_floor
    target: float = max(reduce_target, liquidity_floor_value)

    return PositionSizingResult(
        allowed=True,
        target_notional=target,
        )


# =============================================================================
# SECTION 2 -- SIZE POSITION
# =============================================================================

def x_size_position__mutmut_60(
    position:     PositionSpec,
    portfolio:    PortfolioState,
    params:       RiskParameters,
    decision:     RiskDecision,
    position_vol: Optional[float] = None,
) -> PositionSizingResult:
    """
    Compute the allowed position size given a pre-evaluated RiskDecision.

    Pure function: reads arguments, returns PositionSizingResult.
    No mutation, no global state, no I/O, no side effects.

    Sizing pipeline (fixed order):
        1.  HALT -> return immediately.
        2.  requested_notional = quantity * current_price
        3.  base_cap = nav * max_position_pct_nav
        4.  vol_cap_scalar = min(volatility_target_ann / max(position_vol, 1e-8), 1.0)
                             if position_vol is not None else 1.0
        5.  effective_cap = min(base_cap, base_cap * vol_cap_scalar)
        6.  raw_target = min(requested_notional, effective_cap)
        7.  kelly_target = raw_target * kelly_fraction
        8.  reduce_target = kelly_target * liquidity_haircut_floor  (REDUCE)
                          = kelly_target                             (APPROVE)
        9.  liquidity_floor = requested_notional * liquidity_haircut_floor
        10. target = max(reduce_target, liquidity_floor)

    Args:
        position:     PositionSpec. quantity and current_price derive requested notional.
        portfolio:    PortfolioState. nav used for base cap.
        params:       RiskParameters. All sizing scalars consumed here.
        decision:     RiskDecision from evaluate_position_risk(). Only verdict consumed.
        position_vol: Optional annualised volatility of this position.
                      None -> vol_cap_scalar = 1.0 (no vol adjustment; backward compat).

    Returns:
        PositionSizingResult(allowed, target_notional, reason).
    """
    # ------------------------------------------------------------------
    # Step 1: HALT -- no sizing arithmetic performed.
    # ------------------------------------------------------------------
    if decision.verdict is RiskVerdict.HALT:
        return PositionSizingResult(
            allowed=False,
            target_notional=None,
            reason=decision.verdict,
        )

    # ------------------------------------------------------------------
    # Step 2: Requested notional.
    # quantity and current_price are finite and > 0 (domain-validated).
    # ------------------------------------------------------------------
    requested_notional: float = position.quantity * position.current_price

    # ------------------------------------------------------------------
    # Step 3: Base position cap.
    # nav and max_position_pct_nav are finite and > 0 (domain-validated).
    # ------------------------------------------------------------------
    base_cap: float = portfolio.nav * params.max_position_pct_nav

    # ------------------------------------------------------------------
    # Step 4: Volatility-adjusted cap scalar.
    # position_vol=None -> scalar=1.0 (identity; preserves Phase 7C output).
    # max(position_vol, 1e-8) guards against division by zero or near-zero.
    # min(..., 1.0) prevents the scalar from exceeding 1 (no vol-based leverage).
    # ------------------------------------------------------------------
    if position_vol is not None:
        vol_cap_scalar: float = min(
            params.volatility_target_ann / max(position_vol, 1e-8),
            1.0,
        )
    else:
        vol_cap_scalar = 1.0

    # ------------------------------------------------------------------
    # Step 5: Effective cap.
    # vol_cap = base_cap * scalar. effective_cap = min(base_cap, vol_cap).
    # When scalar=1.0: vol_cap == base_cap -> effective_cap == base_cap.
    # ------------------------------------------------------------------
    effective_cap: float = min(base_cap, base_cap * vol_cap_scalar)

    # ------------------------------------------------------------------
    # Step 6: Raw target capped at effective_cap.
    # ------------------------------------------------------------------
    raw_target: float = min(requested_notional, effective_cap)

    # ------------------------------------------------------------------
    # Step 7: Kelly fraction.
    # kelly_fraction is validated in (0.0, 1.0] by RiskParameters.
    # No guard needed; always reduces or preserves raw_target.
    # ------------------------------------------------------------------
    kelly_target: float = raw_target * params.kelly_fraction

    # ------------------------------------------------------------------
    # Step 8: REDUCE multiplier (conditional on clamping).
    # REDUCE applies liquidity_haircut_floor only when the position was
    # clamped by the cap (raw_target < requested_notional).
    # When not clamped (position already within cap), REDUCE passes
    # kelly_target through unchanged -- no additional compression.
    # APPROVE always passes kelly_target through unchanged.
    # liquidity_haircut_floor validated in (0.0, 1.0] by RiskParameters.
    # ------------------------------------------------------------------
    _was_clamped: bool = raw_target < requested_notional
    if decision.verdict is RiskVerdict.REDUCE and _was_clamped:
        reduce_target: float = kelly_target * params.liquidity_haircut_floor
    else:
        reduce_target = kelly_target

    # ------------------------------------------------------------------
    # Step 9: Liquidity floor guarantee (INV-SZ-05).
    # Even after Kelly and REDUCE compression, target must be at least
    # liquidity_haircut_floor fraction of the original requested notional.
    # This prevents compound discounting from compressing to near-zero.
    # ------------------------------------------------------------------
    liquidity_floor_value: float = requested_notional * params.liquidity_haircut_floor
    target: float = max(reduce_target, liquidity_floor_value)

    return PositionSizingResult(
        allowed=False,
        target_notional=target,
        reason=decision.verdict,
    )

x_size_position__mutmut_mutants : ClassVar[MutantDict] = { # type: ignore
'x_size_position__mutmut_1': x_size_position__mutmut_1, 
    'x_size_position__mutmut_2': x_size_position__mutmut_2, 
    'x_size_position__mutmut_3': x_size_position__mutmut_3, 
    'x_size_position__mutmut_4': x_size_position__mutmut_4, 
    'x_size_position__mutmut_5': x_size_position__mutmut_5, 
    'x_size_position__mutmut_6': x_size_position__mutmut_6, 
    'x_size_position__mutmut_7': x_size_position__mutmut_7, 
    'x_size_position__mutmut_8': x_size_position__mutmut_8, 
    'x_size_position__mutmut_9': x_size_position__mutmut_9, 
    'x_size_position__mutmut_10': x_size_position__mutmut_10, 
    'x_size_position__mutmut_11': x_size_position__mutmut_11, 
    'x_size_position__mutmut_12': x_size_position__mutmut_12, 
    'x_size_position__mutmut_13': x_size_position__mutmut_13, 
    'x_size_position__mutmut_14': x_size_position__mutmut_14, 
    'x_size_position__mutmut_15': x_size_position__mutmut_15, 
    'x_size_position__mutmut_16': x_size_position__mutmut_16, 
    'x_size_position__mutmut_17': x_size_position__mutmut_17, 
    'x_size_position__mutmut_18': x_size_position__mutmut_18, 
    'x_size_position__mutmut_19': x_size_position__mutmut_19, 
    'x_size_position__mutmut_20': x_size_position__mutmut_20, 
    'x_size_position__mutmut_21': x_size_position__mutmut_21, 
    'x_size_position__mutmut_22': x_size_position__mutmut_22, 
    'x_size_position__mutmut_23': x_size_position__mutmut_23, 
    'x_size_position__mutmut_24': x_size_position__mutmut_24, 
    'x_size_position__mutmut_25': x_size_position__mutmut_25, 
    'x_size_position__mutmut_26': x_size_position__mutmut_26, 
    'x_size_position__mutmut_27': x_size_position__mutmut_27, 
    'x_size_position__mutmut_28': x_size_position__mutmut_28, 
    'x_size_position__mutmut_29': x_size_position__mutmut_29, 
    'x_size_position__mutmut_30': x_size_position__mutmut_30, 
    'x_size_position__mutmut_31': x_size_position__mutmut_31, 
    'x_size_position__mutmut_32': x_size_position__mutmut_32, 
    'x_size_position__mutmut_33': x_size_position__mutmut_33, 
    'x_size_position__mutmut_34': x_size_position__mutmut_34, 
    'x_size_position__mutmut_35': x_size_position__mutmut_35, 
    'x_size_position__mutmut_36': x_size_position__mutmut_36, 
    'x_size_position__mutmut_37': x_size_position__mutmut_37, 
    'x_size_position__mutmut_38': x_size_position__mutmut_38, 
    'x_size_position__mutmut_39': x_size_position__mutmut_39, 
    'x_size_position__mutmut_40': x_size_position__mutmut_40, 
    'x_size_position__mutmut_41': x_size_position__mutmut_41, 
    'x_size_position__mutmut_42': x_size_position__mutmut_42, 
    'x_size_position__mutmut_43': x_size_position__mutmut_43, 
    'x_size_position__mutmut_44': x_size_position__mutmut_44, 
    'x_size_position__mutmut_45': x_size_position__mutmut_45, 
    'x_size_position__mutmut_46': x_size_position__mutmut_46, 
    'x_size_position__mutmut_47': x_size_position__mutmut_47, 
    'x_size_position__mutmut_48': x_size_position__mutmut_48, 
    'x_size_position__mutmut_49': x_size_position__mutmut_49, 
    'x_size_position__mutmut_50': x_size_position__mutmut_50, 
    'x_size_position__mutmut_51': x_size_position__mutmut_51, 
    'x_size_position__mutmut_52': x_size_position__mutmut_52, 
    'x_size_position__mutmut_53': x_size_position__mutmut_53, 
    'x_size_position__mutmut_54': x_size_position__mutmut_54, 
    'x_size_position__mutmut_55': x_size_position__mutmut_55, 
    'x_size_position__mutmut_56': x_size_position__mutmut_56, 
    'x_size_position__mutmut_57': x_size_position__mutmut_57, 
    'x_size_position__mutmut_58': x_size_position__mutmut_58, 
    'x_size_position__mutmut_59': x_size_position__mutmut_59, 
    'x_size_position__mutmut_60': x_size_position__mutmut_60
}
x_size_position__mutmut_orig.__name__ = 'x_size_position'


# =============================================================================
# SECTION 3 -- MODULE __all__
# =============================================================================

__all__ = [
    "PositionSizingResult",
    "size_position",
]
