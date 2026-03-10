from .domain import PortfolioState, PositionSpec, RiskParameters
from .evaluator import evaluate_position_risk
from .sizing import PositionSizingResult, size_position
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


def assess_trade(
    position:  PositionSpec,
    portfolio: PortfolioState,
    params:    RiskParameters,
) -> PositionSizingResult:
    args = [position, portfolio, params]# type: ignore
    kwargs = {}# type: ignore
    return _mutmut_trampoline(x_assess_trade__mutmut_orig, x_assess_trade__mutmut_mutants, args, kwargs, None)


def x_assess_trade__mutmut_orig(
    position:  PositionSpec,
    portfolio: PortfolioState,
    params:    RiskParameters,
) -> PositionSizingResult:
    """
    Orchestrate a full risk assessment and position sizing in one call.

    Delegates entirely to the evaluation and sizing layers:
        1. evaluate_position_risk(position, portfolio, params) -> RiskDecision
        2. size_position(position, portfolio, params, decision) -> PositionSizingResult

    Pure, deterministic, stateless, non-mutating.
    No branching, no validation, no threshold computation.
    All logic resides in evaluator.py and sizing.py.
    """
    decision = evaluate_position_risk(position, portfolio, params)
    return size_position(position, portfolio, params, decision)


def x_assess_trade__mutmut_1(
    position:  PositionSpec,
    portfolio: PortfolioState,
    params:    RiskParameters,
) -> PositionSizingResult:
    """
    Orchestrate a full risk assessment and position sizing in one call.

    Delegates entirely to the evaluation and sizing layers:
        1. evaluate_position_risk(position, portfolio, params) -> RiskDecision
        2. size_position(position, portfolio, params, decision) -> PositionSizingResult

    Pure, deterministic, stateless, non-mutating.
    No branching, no validation, no threshold computation.
    All logic resides in evaluator.py and sizing.py.
    """
    decision = None
    return size_position(position, portfolio, params, decision)


def x_assess_trade__mutmut_2(
    position:  PositionSpec,
    portfolio: PortfolioState,
    params:    RiskParameters,
) -> PositionSizingResult:
    """
    Orchestrate a full risk assessment and position sizing in one call.

    Delegates entirely to the evaluation and sizing layers:
        1. evaluate_position_risk(position, portfolio, params) -> RiskDecision
        2. size_position(position, portfolio, params, decision) -> PositionSizingResult

    Pure, deterministic, stateless, non-mutating.
    No branching, no validation, no threshold computation.
    All logic resides in evaluator.py and sizing.py.
    """
    decision = evaluate_position_risk(None, portfolio, params)
    return size_position(position, portfolio, params, decision)


def x_assess_trade__mutmut_3(
    position:  PositionSpec,
    portfolio: PortfolioState,
    params:    RiskParameters,
) -> PositionSizingResult:
    """
    Orchestrate a full risk assessment and position sizing in one call.

    Delegates entirely to the evaluation and sizing layers:
        1. evaluate_position_risk(position, portfolio, params) -> RiskDecision
        2. size_position(position, portfolio, params, decision) -> PositionSizingResult

    Pure, deterministic, stateless, non-mutating.
    No branching, no validation, no threshold computation.
    All logic resides in evaluator.py and sizing.py.
    """
    decision = evaluate_position_risk(position, None, params)
    return size_position(position, portfolio, params, decision)


def x_assess_trade__mutmut_4(
    position:  PositionSpec,
    portfolio: PortfolioState,
    params:    RiskParameters,
) -> PositionSizingResult:
    """
    Orchestrate a full risk assessment and position sizing in one call.

    Delegates entirely to the evaluation and sizing layers:
        1. evaluate_position_risk(position, portfolio, params) -> RiskDecision
        2. size_position(position, portfolio, params, decision) -> PositionSizingResult

    Pure, deterministic, stateless, non-mutating.
    No branching, no validation, no threshold computation.
    All logic resides in evaluator.py and sizing.py.
    """
    decision = evaluate_position_risk(position, portfolio, None)
    return size_position(position, portfolio, params, decision)


def x_assess_trade__mutmut_5(
    position:  PositionSpec,
    portfolio: PortfolioState,
    params:    RiskParameters,
) -> PositionSizingResult:
    """
    Orchestrate a full risk assessment and position sizing in one call.

    Delegates entirely to the evaluation and sizing layers:
        1. evaluate_position_risk(position, portfolio, params) -> RiskDecision
        2. size_position(position, portfolio, params, decision) -> PositionSizingResult

    Pure, deterministic, stateless, non-mutating.
    No branching, no validation, no threshold computation.
    All logic resides in evaluator.py and sizing.py.
    """
    decision = evaluate_position_risk(portfolio, params)
    return size_position(position, portfolio, params, decision)


def x_assess_trade__mutmut_6(
    position:  PositionSpec,
    portfolio: PortfolioState,
    params:    RiskParameters,
) -> PositionSizingResult:
    """
    Orchestrate a full risk assessment and position sizing in one call.

    Delegates entirely to the evaluation and sizing layers:
        1. evaluate_position_risk(position, portfolio, params) -> RiskDecision
        2. size_position(position, portfolio, params, decision) -> PositionSizingResult

    Pure, deterministic, stateless, non-mutating.
    No branching, no validation, no threshold computation.
    All logic resides in evaluator.py and sizing.py.
    """
    decision = evaluate_position_risk(position, params)
    return size_position(position, portfolio, params, decision)


def x_assess_trade__mutmut_7(
    position:  PositionSpec,
    portfolio: PortfolioState,
    params:    RiskParameters,
) -> PositionSizingResult:
    """
    Orchestrate a full risk assessment and position sizing in one call.

    Delegates entirely to the evaluation and sizing layers:
        1. evaluate_position_risk(position, portfolio, params) -> RiskDecision
        2. size_position(position, portfolio, params, decision) -> PositionSizingResult

    Pure, deterministic, stateless, non-mutating.
    No branching, no validation, no threshold computation.
    All logic resides in evaluator.py and sizing.py.
    """
    decision = evaluate_position_risk(position, portfolio, )
    return size_position(position, portfolio, params, decision)


def x_assess_trade__mutmut_8(
    position:  PositionSpec,
    portfolio: PortfolioState,
    params:    RiskParameters,
) -> PositionSizingResult:
    """
    Orchestrate a full risk assessment and position sizing in one call.

    Delegates entirely to the evaluation and sizing layers:
        1. evaluate_position_risk(position, portfolio, params) -> RiskDecision
        2. size_position(position, portfolio, params, decision) -> PositionSizingResult

    Pure, deterministic, stateless, non-mutating.
    No branching, no validation, no threshold computation.
    All logic resides in evaluator.py and sizing.py.
    """
    decision = evaluate_position_risk(position, portfolio, params)
    return size_position(None, portfolio, params, decision)


def x_assess_trade__mutmut_9(
    position:  PositionSpec,
    portfolio: PortfolioState,
    params:    RiskParameters,
) -> PositionSizingResult:
    """
    Orchestrate a full risk assessment and position sizing in one call.

    Delegates entirely to the evaluation and sizing layers:
        1. evaluate_position_risk(position, portfolio, params) -> RiskDecision
        2. size_position(position, portfolio, params, decision) -> PositionSizingResult

    Pure, deterministic, stateless, non-mutating.
    No branching, no validation, no threshold computation.
    All logic resides in evaluator.py and sizing.py.
    """
    decision = evaluate_position_risk(position, portfolio, params)
    return size_position(position, None, params, decision)


def x_assess_trade__mutmut_10(
    position:  PositionSpec,
    portfolio: PortfolioState,
    params:    RiskParameters,
) -> PositionSizingResult:
    """
    Orchestrate a full risk assessment and position sizing in one call.

    Delegates entirely to the evaluation and sizing layers:
        1. evaluate_position_risk(position, portfolio, params) -> RiskDecision
        2. size_position(position, portfolio, params, decision) -> PositionSizingResult

    Pure, deterministic, stateless, non-mutating.
    No branching, no validation, no threshold computation.
    All logic resides in evaluator.py and sizing.py.
    """
    decision = evaluate_position_risk(position, portfolio, params)
    return size_position(position, portfolio, None, decision)


def x_assess_trade__mutmut_11(
    position:  PositionSpec,
    portfolio: PortfolioState,
    params:    RiskParameters,
) -> PositionSizingResult:
    """
    Orchestrate a full risk assessment and position sizing in one call.

    Delegates entirely to the evaluation and sizing layers:
        1. evaluate_position_risk(position, portfolio, params) -> RiskDecision
        2. size_position(position, portfolio, params, decision) -> PositionSizingResult

    Pure, deterministic, stateless, non-mutating.
    No branching, no validation, no threshold computation.
    All logic resides in evaluator.py and sizing.py.
    """
    decision = evaluate_position_risk(position, portfolio, params)
    return size_position(position, portfolio, params, None)


def x_assess_trade__mutmut_12(
    position:  PositionSpec,
    portfolio: PortfolioState,
    params:    RiskParameters,
) -> PositionSizingResult:
    """
    Orchestrate a full risk assessment and position sizing in one call.

    Delegates entirely to the evaluation and sizing layers:
        1. evaluate_position_risk(position, portfolio, params) -> RiskDecision
        2. size_position(position, portfolio, params, decision) -> PositionSizingResult

    Pure, deterministic, stateless, non-mutating.
    No branching, no validation, no threshold computation.
    All logic resides in evaluator.py and sizing.py.
    """
    decision = evaluate_position_risk(position, portfolio, params)
    return size_position(portfolio, params, decision)


def x_assess_trade__mutmut_13(
    position:  PositionSpec,
    portfolio: PortfolioState,
    params:    RiskParameters,
) -> PositionSizingResult:
    """
    Orchestrate a full risk assessment and position sizing in one call.

    Delegates entirely to the evaluation and sizing layers:
        1. evaluate_position_risk(position, portfolio, params) -> RiskDecision
        2. size_position(position, portfolio, params, decision) -> PositionSizingResult

    Pure, deterministic, stateless, non-mutating.
    No branching, no validation, no threshold computation.
    All logic resides in evaluator.py and sizing.py.
    """
    decision = evaluate_position_risk(position, portfolio, params)
    return size_position(position, params, decision)


def x_assess_trade__mutmut_14(
    position:  PositionSpec,
    portfolio: PortfolioState,
    params:    RiskParameters,
) -> PositionSizingResult:
    """
    Orchestrate a full risk assessment and position sizing in one call.

    Delegates entirely to the evaluation and sizing layers:
        1. evaluate_position_risk(position, portfolio, params) -> RiskDecision
        2. size_position(position, portfolio, params, decision) -> PositionSizingResult

    Pure, deterministic, stateless, non-mutating.
    No branching, no validation, no threshold computation.
    All logic resides in evaluator.py and sizing.py.
    """
    decision = evaluate_position_risk(position, portfolio, params)
    return size_position(position, portfolio, decision)


def x_assess_trade__mutmut_15(
    position:  PositionSpec,
    portfolio: PortfolioState,
    params:    RiskParameters,
) -> PositionSizingResult:
    """
    Orchestrate a full risk assessment and position sizing in one call.

    Delegates entirely to the evaluation and sizing layers:
        1. evaluate_position_risk(position, portfolio, params) -> RiskDecision
        2. size_position(position, portfolio, params, decision) -> PositionSizingResult

    Pure, deterministic, stateless, non-mutating.
    No branching, no validation, no threshold computation.
    All logic resides in evaluator.py and sizing.py.
    """
    decision = evaluate_position_risk(position, portfolio, params)
    return size_position(position, portfolio, params, )

x_assess_trade__mutmut_mutants : ClassVar[MutantDict] = { # type: ignore
'x_assess_trade__mutmut_1': x_assess_trade__mutmut_1, 
    'x_assess_trade__mutmut_2': x_assess_trade__mutmut_2, 
    'x_assess_trade__mutmut_3': x_assess_trade__mutmut_3, 
    'x_assess_trade__mutmut_4': x_assess_trade__mutmut_4, 
    'x_assess_trade__mutmut_5': x_assess_trade__mutmut_5, 
    'x_assess_trade__mutmut_6': x_assess_trade__mutmut_6, 
    'x_assess_trade__mutmut_7': x_assess_trade__mutmut_7, 
    'x_assess_trade__mutmut_8': x_assess_trade__mutmut_8, 
    'x_assess_trade__mutmut_9': x_assess_trade__mutmut_9, 
    'x_assess_trade__mutmut_10': x_assess_trade__mutmut_10, 
    'x_assess_trade__mutmut_11': x_assess_trade__mutmut_11, 
    'x_assess_trade__mutmut_12': x_assess_trade__mutmut_12, 
    'x_assess_trade__mutmut_13': x_assess_trade__mutmut_13, 
    'x_assess_trade__mutmut_14': x_assess_trade__mutmut_14, 
    'x_assess_trade__mutmut_15': x_assess_trade__mutmut_15
}
x_assess_trade__mutmut_orig.__name__ = 'x_assess_trade'


__all__ = ["assess_trade"]
