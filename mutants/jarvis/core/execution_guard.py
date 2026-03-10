# =============================================================================
# JARVIS v6.1.0 -- PHASE 8: EXECUTION GUARD
# File:   jarvis/core/execution_guard.py
# =============================================================================
#
# PURPOSE
# -------
# Strict boundary adapter between strategy output and the risk subsystem.
# Translates a PositionSizingResult into an ExecutionOrder, or suppresses
# the order entirely when the risk layer disallows the trade.
#
# This module contains no risk logic. It has no knowledge of drawdown
# thresholds, position caps, or sizing arithmetic. All policy decisions are
# delegated entirely to assess_trade() in jarvis.core.risk_layer.engine.
#
# WHAT IS NOT IN THIS FILE
# ------------------------
#   No cap calculations.
#   No threshold knowledge.
#   No exception wrapping.
#   No logging.
#   No mutation of inputs.
#   No reimplementation of evaluator or sizing logic.
#
# DETERMINISM CONSTRAINTS
# -----------------------
# DET-01  No stochastic operations.
# DET-02  All inputs passed explicitly. No module-level mutable reads.
# DET-03  No side effects. ExecutionOrder is frozen; inputs never mutated.
# DET-04  No datetime.now() / time.time().
# DET-05  No random / secrets / uuid.
# =============================================================================

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

from jarvis.core.risk_layer import (
    PortfolioState,
    PositionSpec,
    RiskParameters,
    Side,
)
from jarvis.core.risk_layer.engine import assess_trade
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
# SECTION 1 -- EXECUTION ORDER
# =============================================================================

@dataclass(frozen=True)
class ExecutionOrder:
    """
    Immutable instruction for downstream execution infrastructure.

    Produced by build_execution_order() when the risk layer approves the trade.
    Contains only the information required to route and size the order.

    Attributes:
        symbol:           Instrument identifier. Echoed from PositionSpec.
        side:             Trade direction. Echoed from PositionSpec.
        target_notional:  Approved USD notional. Sourced from PositionSizingResult.
                          Always finite and > 0 when this object exists.
    """

    symbol:           str
    side:             Side
    target_notional:  float


# =============================================================================
# SECTION 2 -- BUILD EXECUTION ORDER
# =============================================================================

def build_execution_order(
    position:  PositionSpec,
    portfolio: PortfolioState,
    params:    RiskParameters,
) -> Optional[ExecutionOrder]:
    args = [position, portfolio, params]# type: ignore
    kwargs = {}# type: ignore
    return _mutmut_trampoline(x_build_execution_order__mutmut_orig, x_build_execution_order__mutmut_mutants, args, kwargs, None)


# =============================================================================
# SECTION 2 -- BUILD EXECUTION ORDER
# =============================================================================

def x_build_execution_order__mutmut_orig(
    position:  PositionSpec,
    portfolio: PortfolioState,
    params:    RiskParameters,
) -> Optional[ExecutionOrder]:
    """
    Translate a proposed position into an ExecutionOrder, subject to risk approval.

    Delegates all risk evaluation and sizing to assess_trade(). This function
    contains no policy knowledge; it only routes the result.

    Args:
        position:  The proposed position to evaluate.
        portfolio: Current portfolio snapshot.
        params:    Risk configuration.

    Returns:
        ExecutionOrder if the trade is allowed (result.allowed is True).
        None           if the trade is blocked  (result.allowed is False).
    """
    result = assess_trade(position, portfolio, params)

    if not result.allowed:
        return None

    return ExecutionOrder(
        symbol=position.symbol,
        side=position.side,
        target_notional=result.target_notional,
    )


# =============================================================================
# SECTION 2 -- BUILD EXECUTION ORDER
# =============================================================================

def x_build_execution_order__mutmut_1(
    position:  PositionSpec,
    portfolio: PortfolioState,
    params:    RiskParameters,
) -> Optional[ExecutionOrder]:
    """
    Translate a proposed position into an ExecutionOrder, subject to risk approval.

    Delegates all risk evaluation and sizing to assess_trade(). This function
    contains no policy knowledge; it only routes the result.

    Args:
        position:  The proposed position to evaluate.
        portfolio: Current portfolio snapshot.
        params:    Risk configuration.

    Returns:
        ExecutionOrder if the trade is allowed (result.allowed is True).
        None           if the trade is blocked  (result.allowed is False).
    """
    result = None

    if not result.allowed:
        return None

    return ExecutionOrder(
        symbol=position.symbol,
        side=position.side,
        target_notional=result.target_notional,
    )


# =============================================================================
# SECTION 2 -- BUILD EXECUTION ORDER
# =============================================================================

def x_build_execution_order__mutmut_2(
    position:  PositionSpec,
    portfolio: PortfolioState,
    params:    RiskParameters,
) -> Optional[ExecutionOrder]:
    """
    Translate a proposed position into an ExecutionOrder, subject to risk approval.

    Delegates all risk evaluation and sizing to assess_trade(). This function
    contains no policy knowledge; it only routes the result.

    Args:
        position:  The proposed position to evaluate.
        portfolio: Current portfolio snapshot.
        params:    Risk configuration.

    Returns:
        ExecutionOrder if the trade is allowed (result.allowed is True).
        None           if the trade is blocked  (result.allowed is False).
    """
    result = assess_trade(None, portfolio, params)

    if not result.allowed:
        return None

    return ExecutionOrder(
        symbol=position.symbol,
        side=position.side,
        target_notional=result.target_notional,
    )


# =============================================================================
# SECTION 2 -- BUILD EXECUTION ORDER
# =============================================================================

def x_build_execution_order__mutmut_3(
    position:  PositionSpec,
    portfolio: PortfolioState,
    params:    RiskParameters,
) -> Optional[ExecutionOrder]:
    """
    Translate a proposed position into an ExecutionOrder, subject to risk approval.

    Delegates all risk evaluation and sizing to assess_trade(). This function
    contains no policy knowledge; it only routes the result.

    Args:
        position:  The proposed position to evaluate.
        portfolio: Current portfolio snapshot.
        params:    Risk configuration.

    Returns:
        ExecutionOrder if the trade is allowed (result.allowed is True).
        None           if the trade is blocked  (result.allowed is False).
    """
    result = assess_trade(position, None, params)

    if not result.allowed:
        return None

    return ExecutionOrder(
        symbol=position.symbol,
        side=position.side,
        target_notional=result.target_notional,
    )


# =============================================================================
# SECTION 2 -- BUILD EXECUTION ORDER
# =============================================================================

def x_build_execution_order__mutmut_4(
    position:  PositionSpec,
    portfolio: PortfolioState,
    params:    RiskParameters,
) -> Optional[ExecutionOrder]:
    """
    Translate a proposed position into an ExecutionOrder, subject to risk approval.

    Delegates all risk evaluation and sizing to assess_trade(). This function
    contains no policy knowledge; it only routes the result.

    Args:
        position:  The proposed position to evaluate.
        portfolio: Current portfolio snapshot.
        params:    Risk configuration.

    Returns:
        ExecutionOrder if the trade is allowed (result.allowed is True).
        None           if the trade is blocked  (result.allowed is False).
    """
    result = assess_trade(position, portfolio, None)

    if not result.allowed:
        return None

    return ExecutionOrder(
        symbol=position.symbol,
        side=position.side,
        target_notional=result.target_notional,
    )


# =============================================================================
# SECTION 2 -- BUILD EXECUTION ORDER
# =============================================================================

def x_build_execution_order__mutmut_5(
    position:  PositionSpec,
    portfolio: PortfolioState,
    params:    RiskParameters,
) -> Optional[ExecutionOrder]:
    """
    Translate a proposed position into an ExecutionOrder, subject to risk approval.

    Delegates all risk evaluation and sizing to assess_trade(). This function
    contains no policy knowledge; it only routes the result.

    Args:
        position:  The proposed position to evaluate.
        portfolio: Current portfolio snapshot.
        params:    Risk configuration.

    Returns:
        ExecutionOrder if the trade is allowed (result.allowed is True).
        None           if the trade is blocked  (result.allowed is False).
    """
    result = assess_trade(portfolio, params)

    if not result.allowed:
        return None

    return ExecutionOrder(
        symbol=position.symbol,
        side=position.side,
        target_notional=result.target_notional,
    )


# =============================================================================
# SECTION 2 -- BUILD EXECUTION ORDER
# =============================================================================

def x_build_execution_order__mutmut_6(
    position:  PositionSpec,
    portfolio: PortfolioState,
    params:    RiskParameters,
) -> Optional[ExecutionOrder]:
    """
    Translate a proposed position into an ExecutionOrder, subject to risk approval.

    Delegates all risk evaluation and sizing to assess_trade(). This function
    contains no policy knowledge; it only routes the result.

    Args:
        position:  The proposed position to evaluate.
        portfolio: Current portfolio snapshot.
        params:    Risk configuration.

    Returns:
        ExecutionOrder if the trade is allowed (result.allowed is True).
        None           if the trade is blocked  (result.allowed is False).
    """
    result = assess_trade(position, params)

    if not result.allowed:
        return None

    return ExecutionOrder(
        symbol=position.symbol,
        side=position.side,
        target_notional=result.target_notional,
    )


# =============================================================================
# SECTION 2 -- BUILD EXECUTION ORDER
# =============================================================================

def x_build_execution_order__mutmut_7(
    position:  PositionSpec,
    portfolio: PortfolioState,
    params:    RiskParameters,
) -> Optional[ExecutionOrder]:
    """
    Translate a proposed position into an ExecutionOrder, subject to risk approval.

    Delegates all risk evaluation and sizing to assess_trade(). This function
    contains no policy knowledge; it only routes the result.

    Args:
        position:  The proposed position to evaluate.
        portfolio: Current portfolio snapshot.
        params:    Risk configuration.

    Returns:
        ExecutionOrder if the trade is allowed (result.allowed is True).
        None           if the trade is blocked  (result.allowed is False).
    """
    result = assess_trade(position, portfolio, )

    if not result.allowed:
        return None

    return ExecutionOrder(
        symbol=position.symbol,
        side=position.side,
        target_notional=result.target_notional,
    )


# =============================================================================
# SECTION 2 -- BUILD EXECUTION ORDER
# =============================================================================

def x_build_execution_order__mutmut_8(
    position:  PositionSpec,
    portfolio: PortfolioState,
    params:    RiskParameters,
) -> Optional[ExecutionOrder]:
    """
    Translate a proposed position into an ExecutionOrder, subject to risk approval.

    Delegates all risk evaluation and sizing to assess_trade(). This function
    contains no policy knowledge; it only routes the result.

    Args:
        position:  The proposed position to evaluate.
        portfolio: Current portfolio snapshot.
        params:    Risk configuration.

    Returns:
        ExecutionOrder if the trade is allowed (result.allowed is True).
        None           if the trade is blocked  (result.allowed is False).
    """
    result = assess_trade(position, portfolio, params)

    if result.allowed:
        return None

    return ExecutionOrder(
        symbol=position.symbol,
        side=position.side,
        target_notional=result.target_notional,
    )


# =============================================================================
# SECTION 2 -- BUILD EXECUTION ORDER
# =============================================================================

def x_build_execution_order__mutmut_9(
    position:  PositionSpec,
    portfolio: PortfolioState,
    params:    RiskParameters,
) -> Optional[ExecutionOrder]:
    """
    Translate a proposed position into an ExecutionOrder, subject to risk approval.

    Delegates all risk evaluation and sizing to assess_trade(). This function
    contains no policy knowledge; it only routes the result.

    Args:
        position:  The proposed position to evaluate.
        portfolio: Current portfolio snapshot.
        params:    Risk configuration.

    Returns:
        ExecutionOrder if the trade is allowed (result.allowed is True).
        None           if the trade is blocked  (result.allowed is False).
    """
    result = assess_trade(position, portfolio, params)

    if not result.allowed:
        return None

    return ExecutionOrder(
        symbol=None,
        side=position.side,
        target_notional=result.target_notional,
    )


# =============================================================================
# SECTION 2 -- BUILD EXECUTION ORDER
# =============================================================================

def x_build_execution_order__mutmut_10(
    position:  PositionSpec,
    portfolio: PortfolioState,
    params:    RiskParameters,
) -> Optional[ExecutionOrder]:
    """
    Translate a proposed position into an ExecutionOrder, subject to risk approval.

    Delegates all risk evaluation and sizing to assess_trade(). This function
    contains no policy knowledge; it only routes the result.

    Args:
        position:  The proposed position to evaluate.
        portfolio: Current portfolio snapshot.
        params:    Risk configuration.

    Returns:
        ExecutionOrder if the trade is allowed (result.allowed is True).
        None           if the trade is blocked  (result.allowed is False).
    """
    result = assess_trade(position, portfolio, params)

    if not result.allowed:
        return None

    return ExecutionOrder(
        symbol=position.symbol,
        side=None,
        target_notional=result.target_notional,
    )


# =============================================================================
# SECTION 2 -- BUILD EXECUTION ORDER
# =============================================================================

def x_build_execution_order__mutmut_11(
    position:  PositionSpec,
    portfolio: PortfolioState,
    params:    RiskParameters,
) -> Optional[ExecutionOrder]:
    """
    Translate a proposed position into an ExecutionOrder, subject to risk approval.

    Delegates all risk evaluation and sizing to assess_trade(). This function
    contains no policy knowledge; it only routes the result.

    Args:
        position:  The proposed position to evaluate.
        portfolio: Current portfolio snapshot.
        params:    Risk configuration.

    Returns:
        ExecutionOrder if the trade is allowed (result.allowed is True).
        None           if the trade is blocked  (result.allowed is False).
    """
    result = assess_trade(position, portfolio, params)

    if not result.allowed:
        return None

    return ExecutionOrder(
        symbol=position.symbol,
        side=position.side,
        target_notional=None,
    )


# =============================================================================
# SECTION 2 -- BUILD EXECUTION ORDER
# =============================================================================

def x_build_execution_order__mutmut_12(
    position:  PositionSpec,
    portfolio: PortfolioState,
    params:    RiskParameters,
) -> Optional[ExecutionOrder]:
    """
    Translate a proposed position into an ExecutionOrder, subject to risk approval.

    Delegates all risk evaluation and sizing to assess_trade(). This function
    contains no policy knowledge; it only routes the result.

    Args:
        position:  The proposed position to evaluate.
        portfolio: Current portfolio snapshot.
        params:    Risk configuration.

    Returns:
        ExecutionOrder if the trade is allowed (result.allowed is True).
        None           if the trade is blocked  (result.allowed is False).
    """
    result = assess_trade(position, portfolio, params)

    if not result.allowed:
        return None

    return ExecutionOrder(
        side=position.side,
        target_notional=result.target_notional,
    )


# =============================================================================
# SECTION 2 -- BUILD EXECUTION ORDER
# =============================================================================

def x_build_execution_order__mutmut_13(
    position:  PositionSpec,
    portfolio: PortfolioState,
    params:    RiskParameters,
) -> Optional[ExecutionOrder]:
    """
    Translate a proposed position into an ExecutionOrder, subject to risk approval.

    Delegates all risk evaluation and sizing to assess_trade(). This function
    contains no policy knowledge; it only routes the result.

    Args:
        position:  The proposed position to evaluate.
        portfolio: Current portfolio snapshot.
        params:    Risk configuration.

    Returns:
        ExecutionOrder if the trade is allowed (result.allowed is True).
        None           if the trade is blocked  (result.allowed is False).
    """
    result = assess_trade(position, portfolio, params)

    if not result.allowed:
        return None

    return ExecutionOrder(
        symbol=position.symbol,
        target_notional=result.target_notional,
    )


# =============================================================================
# SECTION 2 -- BUILD EXECUTION ORDER
# =============================================================================

def x_build_execution_order__mutmut_14(
    position:  PositionSpec,
    portfolio: PortfolioState,
    params:    RiskParameters,
) -> Optional[ExecutionOrder]:
    """
    Translate a proposed position into an ExecutionOrder, subject to risk approval.

    Delegates all risk evaluation and sizing to assess_trade(). This function
    contains no policy knowledge; it only routes the result.

    Args:
        position:  The proposed position to evaluate.
        portfolio: Current portfolio snapshot.
        params:    Risk configuration.

    Returns:
        ExecutionOrder if the trade is allowed (result.allowed is True).
        None           if the trade is blocked  (result.allowed is False).
    """
    result = assess_trade(position, portfolio, params)

    if not result.allowed:
        return None

    return ExecutionOrder(
        symbol=position.symbol,
        side=position.side,
        )

x_build_execution_order__mutmut_mutants : ClassVar[MutantDict] = { # type: ignore
'x_build_execution_order__mutmut_1': x_build_execution_order__mutmut_1, 
    'x_build_execution_order__mutmut_2': x_build_execution_order__mutmut_2, 
    'x_build_execution_order__mutmut_3': x_build_execution_order__mutmut_3, 
    'x_build_execution_order__mutmut_4': x_build_execution_order__mutmut_4, 
    'x_build_execution_order__mutmut_5': x_build_execution_order__mutmut_5, 
    'x_build_execution_order__mutmut_6': x_build_execution_order__mutmut_6, 
    'x_build_execution_order__mutmut_7': x_build_execution_order__mutmut_7, 
    'x_build_execution_order__mutmut_8': x_build_execution_order__mutmut_8, 
    'x_build_execution_order__mutmut_9': x_build_execution_order__mutmut_9, 
    'x_build_execution_order__mutmut_10': x_build_execution_order__mutmut_10, 
    'x_build_execution_order__mutmut_11': x_build_execution_order__mutmut_11, 
    'x_build_execution_order__mutmut_12': x_build_execution_order__mutmut_12, 
    'x_build_execution_order__mutmut_13': x_build_execution_order__mutmut_13, 
    'x_build_execution_order__mutmut_14': x_build_execution_order__mutmut_14
}
x_build_execution_order__mutmut_orig.__name__ = 'x_build_execution_order'


# =============================================================================
# SECTION 3 -- MODULE __all__
# =============================================================================

__all__ = [
    "ExecutionOrder",
    "build_execution_order",
]
