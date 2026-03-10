# =============================================================================
# JARVIS v6.1.0 -- SELECTION ENGINE (SCAFFOLD)
# File:   jarvis/selection/engine.py
# Version: 1.1.0
# =============================================================================
#
# SCOPE
# -----
# Minimal deterministic instrument selection scaffold. Ranks candidates by
# a caller-supplied score function and applies configurable filters.
# No external data calls. Pure functions only.
#
# PUBLIC FUNCTIONS
# ----------------
#   rank_candidates(candidates, score_fn, descending) -> List[str]
#   filter_by_threshold(candidates, scores, threshold) -> List[str]
#   select_top_n(candidates, scores, n) -> List[str]
#
# DETERMINISM CONSTRAINTS
# -----------------------
# All functions are pure. Tie-breaking uses lexicographic sort on symbol.
# score_fn must be deterministic (caller's responsibility).
# =============================================================================

from __future__ import annotations

from typing import Callable, Dict, List, Sequence
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


def rank_candidates(
    candidates:  Sequence[str],
    score_fn:    Callable[[str], float],
    descending:  bool = True,
) -> List[str]:
    args = [candidates, score_fn, descending]# type: ignore
    kwargs = {}# type: ignore
    return _mutmut_trampoline(x_rank_candidates__mutmut_orig, x_rank_candidates__mutmut_mutants, args, kwargs, None)


def x_rank_candidates__mutmut_orig(
    candidates:  Sequence[str],
    score_fn:    Callable[[str], float],
    descending:  bool = True,
) -> List[str]:
    """
    Rank instrument symbols by a deterministic score function.

    Ties are broken lexicographically (ascending symbol name) to ensure
    deterministic output regardless of input order.

    Args:
        candidates:  Sequence of instrument symbol strings.
        score_fn:    Pure function mapping symbol -> float score.
        descending:  If True, highest score ranked first (default: True).

    Returns:
        List of symbols sorted by score, then by symbol for tie-breaking.
    """
    scored = [(score_fn(sym), sym) for sym in candidates]
    scored.sort(key=lambda x: (-x[0] if descending else x[0], x[1]))
    return [sym for _, sym in scored]


def x_rank_candidates__mutmut_1(
    candidates:  Sequence[str],
    score_fn:    Callable[[str], float],
    descending:  bool = False,
) -> List[str]:
    """
    Rank instrument symbols by a deterministic score function.

    Ties are broken lexicographically (ascending symbol name) to ensure
    deterministic output regardless of input order.

    Args:
        candidates:  Sequence of instrument symbol strings.
        score_fn:    Pure function mapping symbol -> float score.
        descending:  If True, highest score ranked first (default: True).

    Returns:
        List of symbols sorted by score, then by symbol for tie-breaking.
    """
    scored = [(score_fn(sym), sym) for sym in candidates]
    scored.sort(key=lambda x: (-x[0] if descending else x[0], x[1]))
    return [sym for _, sym in scored]


def x_rank_candidates__mutmut_2(
    candidates:  Sequence[str],
    score_fn:    Callable[[str], float],
    descending:  bool = True,
) -> List[str]:
    """
    Rank instrument symbols by a deterministic score function.

    Ties are broken lexicographically (ascending symbol name) to ensure
    deterministic output regardless of input order.

    Args:
        candidates:  Sequence of instrument symbol strings.
        score_fn:    Pure function mapping symbol -> float score.
        descending:  If True, highest score ranked first (default: True).

    Returns:
        List of symbols sorted by score, then by symbol for tie-breaking.
    """
    scored = None
    scored.sort(key=lambda x: (-x[0] if descending else x[0], x[1]))
    return [sym for _, sym in scored]


def x_rank_candidates__mutmut_3(
    candidates:  Sequence[str],
    score_fn:    Callable[[str], float],
    descending:  bool = True,
) -> List[str]:
    """
    Rank instrument symbols by a deterministic score function.

    Ties are broken lexicographically (ascending symbol name) to ensure
    deterministic output regardless of input order.

    Args:
        candidates:  Sequence of instrument symbol strings.
        score_fn:    Pure function mapping symbol -> float score.
        descending:  If True, highest score ranked first (default: True).

    Returns:
        List of symbols sorted by score, then by symbol for tie-breaking.
    """
    scored = [(score_fn(None), sym) for sym in candidates]
    scored.sort(key=lambda x: (-x[0] if descending else x[0], x[1]))
    return [sym for _, sym in scored]


def x_rank_candidates__mutmut_4(
    candidates:  Sequence[str],
    score_fn:    Callable[[str], float],
    descending:  bool = True,
) -> List[str]:
    """
    Rank instrument symbols by a deterministic score function.

    Ties are broken lexicographically (ascending symbol name) to ensure
    deterministic output regardless of input order.

    Args:
        candidates:  Sequence of instrument symbol strings.
        score_fn:    Pure function mapping symbol -> float score.
        descending:  If True, highest score ranked first (default: True).

    Returns:
        List of symbols sorted by score, then by symbol for tie-breaking.
    """
    scored = [(score_fn(sym), sym) for sym in candidates]
    scored.sort(key=None)
    return [sym for _, sym in scored]


def x_rank_candidates__mutmut_5(
    candidates:  Sequence[str],
    score_fn:    Callable[[str], float],
    descending:  bool = True,
) -> List[str]:
    """
    Rank instrument symbols by a deterministic score function.

    Ties are broken lexicographically (ascending symbol name) to ensure
    deterministic output regardless of input order.

    Args:
        candidates:  Sequence of instrument symbol strings.
        score_fn:    Pure function mapping symbol -> float score.
        descending:  If True, highest score ranked first (default: True).

    Returns:
        List of symbols sorted by score, then by symbol for tie-breaking.
    """
    scored = [(score_fn(sym), sym) for sym in candidates]
    scored.sort(key=lambda x: None)
    return [sym for _, sym in scored]


def x_rank_candidates__mutmut_6(
    candidates:  Sequence[str],
    score_fn:    Callable[[str], float],
    descending:  bool = True,
) -> List[str]:
    """
    Rank instrument symbols by a deterministic score function.

    Ties are broken lexicographically (ascending symbol name) to ensure
    deterministic output regardless of input order.

    Args:
        candidates:  Sequence of instrument symbol strings.
        score_fn:    Pure function mapping symbol -> float score.
        descending:  If True, highest score ranked first (default: True).

    Returns:
        List of symbols sorted by score, then by symbol for tie-breaking.
    """
    scored = [(score_fn(sym), sym) for sym in candidates]
    scored.sort(key=lambda x: (+x[0] if descending else x[0], x[1]))
    return [sym for _, sym in scored]


def x_rank_candidates__mutmut_7(
    candidates:  Sequence[str],
    score_fn:    Callable[[str], float],
    descending:  bool = True,
) -> List[str]:
    """
    Rank instrument symbols by a deterministic score function.

    Ties are broken lexicographically (ascending symbol name) to ensure
    deterministic output regardless of input order.

    Args:
        candidates:  Sequence of instrument symbol strings.
        score_fn:    Pure function mapping symbol -> float score.
        descending:  If True, highest score ranked first (default: True).

    Returns:
        List of symbols sorted by score, then by symbol for tie-breaking.
    """
    scored = [(score_fn(sym), sym) for sym in candidates]
    scored.sort(key=lambda x: (-x[1] if descending else x[0], x[1]))
    return [sym for _, sym in scored]


def x_rank_candidates__mutmut_8(
    candidates:  Sequence[str],
    score_fn:    Callable[[str], float],
    descending:  bool = True,
) -> List[str]:
    """
    Rank instrument symbols by a deterministic score function.

    Ties are broken lexicographically (ascending symbol name) to ensure
    deterministic output regardless of input order.

    Args:
        candidates:  Sequence of instrument symbol strings.
        score_fn:    Pure function mapping symbol -> float score.
        descending:  If True, highest score ranked first (default: True).

    Returns:
        List of symbols sorted by score, then by symbol for tie-breaking.
    """
    scored = [(score_fn(sym), sym) for sym in candidates]
    scored.sort(key=lambda x: (-x[0] if descending else x[1], x[1]))
    return [sym for _, sym in scored]


def x_rank_candidates__mutmut_9(
    candidates:  Sequence[str],
    score_fn:    Callable[[str], float],
    descending:  bool = True,
) -> List[str]:
    """
    Rank instrument symbols by a deterministic score function.

    Ties are broken lexicographically (ascending symbol name) to ensure
    deterministic output regardless of input order.

    Args:
        candidates:  Sequence of instrument symbol strings.
        score_fn:    Pure function mapping symbol -> float score.
        descending:  If True, highest score ranked first (default: True).

    Returns:
        List of symbols sorted by score, then by symbol for tie-breaking.
    """
    scored = [(score_fn(sym), sym) for sym in candidates]
    scored.sort(key=lambda x: (-x[0] if descending else x[0], x[2]))
    return [sym for _, sym in scored]

x_rank_candidates__mutmut_mutants : ClassVar[MutantDict] = { # type: ignore
'x_rank_candidates__mutmut_1': x_rank_candidates__mutmut_1, 
    'x_rank_candidates__mutmut_2': x_rank_candidates__mutmut_2, 
    'x_rank_candidates__mutmut_3': x_rank_candidates__mutmut_3, 
    'x_rank_candidates__mutmut_4': x_rank_candidates__mutmut_4, 
    'x_rank_candidates__mutmut_5': x_rank_candidates__mutmut_5, 
    'x_rank_candidates__mutmut_6': x_rank_candidates__mutmut_6, 
    'x_rank_candidates__mutmut_7': x_rank_candidates__mutmut_7, 
    'x_rank_candidates__mutmut_8': x_rank_candidates__mutmut_8, 
    'x_rank_candidates__mutmut_9': x_rank_candidates__mutmut_9
}
x_rank_candidates__mutmut_orig.__name__ = 'x_rank_candidates'


def filter_by_threshold(
    candidates:  Sequence[str],
    scores:      Dict[str, float],
    threshold:   float,
) -> List[str]:
    args = [candidates, scores, threshold]# type: ignore
    kwargs = {}# type: ignore
    return _mutmut_trampoline(x_filter_by_threshold__mutmut_orig, x_filter_by_threshold__mutmut_mutants, args, kwargs, None)


def x_filter_by_threshold__mutmut_orig(
    candidates:  Sequence[str],
    scores:      Dict[str, float],
    threshold:   float,
) -> List[str]:
    """
    Filter candidates to those whose score >= threshold.

    Returns list sorted by descending score, then ascending symbol (deterministic).

    Args:
        candidates:  Sequence of candidate symbols.
        scores:      Mapping of symbol -> score. Symbols not in scores receive 0.0.
        threshold:   Minimum score (inclusive).

    Returns:
        Filtered and sorted list of symbols.
    """
    qualified = [
        (scores.get(sym, 0.0), sym)
        for sym in candidates
        if scores.get(sym, 0.0) >= threshold
    ]
    qualified.sort(key=lambda x: (-x[0], x[1]))
    return [sym for _, sym in qualified]


def x_filter_by_threshold__mutmut_1(
    candidates:  Sequence[str],
    scores:      Dict[str, float],
    threshold:   float,
) -> List[str]:
    """
    Filter candidates to those whose score >= threshold.

    Returns list sorted by descending score, then ascending symbol (deterministic).

    Args:
        candidates:  Sequence of candidate symbols.
        scores:      Mapping of symbol -> score. Symbols not in scores receive 0.0.
        threshold:   Minimum score (inclusive).

    Returns:
        Filtered and sorted list of symbols.
    """
    qualified = None
    qualified.sort(key=lambda x: (-x[0], x[1]))
    return [sym for _, sym in qualified]


def x_filter_by_threshold__mutmut_2(
    candidates:  Sequence[str],
    scores:      Dict[str, float],
    threshold:   float,
) -> List[str]:
    """
    Filter candidates to those whose score >= threshold.

    Returns list sorted by descending score, then ascending symbol (deterministic).

    Args:
        candidates:  Sequence of candidate symbols.
        scores:      Mapping of symbol -> score. Symbols not in scores receive 0.0.
        threshold:   Minimum score (inclusive).

    Returns:
        Filtered and sorted list of symbols.
    """
    qualified = [
        (scores.get(None, 0.0), sym)
        for sym in candidates
        if scores.get(sym, 0.0) >= threshold
    ]
    qualified.sort(key=lambda x: (-x[0], x[1]))
    return [sym for _, sym in qualified]


def x_filter_by_threshold__mutmut_3(
    candidates:  Sequence[str],
    scores:      Dict[str, float],
    threshold:   float,
) -> List[str]:
    """
    Filter candidates to those whose score >= threshold.

    Returns list sorted by descending score, then ascending symbol (deterministic).

    Args:
        candidates:  Sequence of candidate symbols.
        scores:      Mapping of symbol -> score. Symbols not in scores receive 0.0.
        threshold:   Minimum score (inclusive).

    Returns:
        Filtered and sorted list of symbols.
    """
    qualified = [
        (scores.get(sym, None), sym)
        for sym in candidates
        if scores.get(sym, 0.0) >= threshold
    ]
    qualified.sort(key=lambda x: (-x[0], x[1]))
    return [sym for _, sym in qualified]


def x_filter_by_threshold__mutmut_4(
    candidates:  Sequence[str],
    scores:      Dict[str, float],
    threshold:   float,
) -> List[str]:
    """
    Filter candidates to those whose score >= threshold.

    Returns list sorted by descending score, then ascending symbol (deterministic).

    Args:
        candidates:  Sequence of candidate symbols.
        scores:      Mapping of symbol -> score. Symbols not in scores receive 0.0.
        threshold:   Minimum score (inclusive).

    Returns:
        Filtered and sorted list of symbols.
    """
    qualified = [
        (scores.get(0.0), sym)
        for sym in candidates
        if scores.get(sym, 0.0) >= threshold
    ]
    qualified.sort(key=lambda x: (-x[0], x[1]))
    return [sym for _, sym in qualified]


def x_filter_by_threshold__mutmut_5(
    candidates:  Sequence[str],
    scores:      Dict[str, float],
    threshold:   float,
) -> List[str]:
    """
    Filter candidates to those whose score >= threshold.

    Returns list sorted by descending score, then ascending symbol (deterministic).

    Args:
        candidates:  Sequence of candidate symbols.
        scores:      Mapping of symbol -> score. Symbols not in scores receive 0.0.
        threshold:   Minimum score (inclusive).

    Returns:
        Filtered and sorted list of symbols.
    """
    qualified = [
        (scores.get(sym, ), sym)
        for sym in candidates
        if scores.get(sym, 0.0) >= threshold
    ]
    qualified.sort(key=lambda x: (-x[0], x[1]))
    return [sym for _, sym in qualified]


def x_filter_by_threshold__mutmut_6(
    candidates:  Sequence[str],
    scores:      Dict[str, float],
    threshold:   float,
) -> List[str]:
    """
    Filter candidates to those whose score >= threshold.

    Returns list sorted by descending score, then ascending symbol (deterministic).

    Args:
        candidates:  Sequence of candidate symbols.
        scores:      Mapping of symbol -> score. Symbols not in scores receive 0.0.
        threshold:   Minimum score (inclusive).

    Returns:
        Filtered and sorted list of symbols.
    """
    qualified = [
        (scores.get(sym, 1.0), sym)
        for sym in candidates
        if scores.get(sym, 0.0) >= threshold
    ]
    qualified.sort(key=lambda x: (-x[0], x[1]))
    return [sym for _, sym in qualified]


def x_filter_by_threshold__mutmut_7(
    candidates:  Sequence[str],
    scores:      Dict[str, float],
    threshold:   float,
) -> List[str]:
    """
    Filter candidates to those whose score >= threshold.

    Returns list sorted by descending score, then ascending symbol (deterministic).

    Args:
        candidates:  Sequence of candidate symbols.
        scores:      Mapping of symbol -> score. Symbols not in scores receive 0.0.
        threshold:   Minimum score (inclusive).

    Returns:
        Filtered and sorted list of symbols.
    """
    qualified = [
        (scores.get(sym, 0.0), sym)
        for sym in candidates
        if scores.get(None, 0.0) >= threshold
    ]
    qualified.sort(key=lambda x: (-x[0], x[1]))
    return [sym for _, sym in qualified]


def x_filter_by_threshold__mutmut_8(
    candidates:  Sequence[str],
    scores:      Dict[str, float],
    threshold:   float,
) -> List[str]:
    """
    Filter candidates to those whose score >= threshold.

    Returns list sorted by descending score, then ascending symbol (deterministic).

    Args:
        candidates:  Sequence of candidate symbols.
        scores:      Mapping of symbol -> score. Symbols not in scores receive 0.0.
        threshold:   Minimum score (inclusive).

    Returns:
        Filtered and sorted list of symbols.
    """
    qualified = [
        (scores.get(sym, 0.0), sym)
        for sym in candidates
        if scores.get(sym, None) >= threshold
    ]
    qualified.sort(key=lambda x: (-x[0], x[1]))
    return [sym for _, sym in qualified]


def x_filter_by_threshold__mutmut_9(
    candidates:  Sequence[str],
    scores:      Dict[str, float],
    threshold:   float,
) -> List[str]:
    """
    Filter candidates to those whose score >= threshold.

    Returns list sorted by descending score, then ascending symbol (deterministic).

    Args:
        candidates:  Sequence of candidate symbols.
        scores:      Mapping of symbol -> score. Symbols not in scores receive 0.0.
        threshold:   Minimum score (inclusive).

    Returns:
        Filtered and sorted list of symbols.
    """
    qualified = [
        (scores.get(sym, 0.0), sym)
        for sym in candidates
        if scores.get(0.0) >= threshold
    ]
    qualified.sort(key=lambda x: (-x[0], x[1]))
    return [sym for _, sym in qualified]


def x_filter_by_threshold__mutmut_10(
    candidates:  Sequence[str],
    scores:      Dict[str, float],
    threshold:   float,
) -> List[str]:
    """
    Filter candidates to those whose score >= threshold.

    Returns list sorted by descending score, then ascending symbol (deterministic).

    Args:
        candidates:  Sequence of candidate symbols.
        scores:      Mapping of symbol -> score. Symbols not in scores receive 0.0.
        threshold:   Minimum score (inclusive).

    Returns:
        Filtered and sorted list of symbols.
    """
    qualified = [
        (scores.get(sym, 0.0), sym)
        for sym in candidates
        if scores.get(sym, ) >= threshold
    ]
    qualified.sort(key=lambda x: (-x[0], x[1]))
    return [sym for _, sym in qualified]


def x_filter_by_threshold__mutmut_11(
    candidates:  Sequence[str],
    scores:      Dict[str, float],
    threshold:   float,
) -> List[str]:
    """
    Filter candidates to those whose score >= threshold.

    Returns list sorted by descending score, then ascending symbol (deterministic).

    Args:
        candidates:  Sequence of candidate symbols.
        scores:      Mapping of symbol -> score. Symbols not in scores receive 0.0.
        threshold:   Minimum score (inclusive).

    Returns:
        Filtered and sorted list of symbols.
    """
    qualified = [
        (scores.get(sym, 0.0), sym)
        for sym in candidates
        if scores.get(sym, 1.0) >= threshold
    ]
    qualified.sort(key=lambda x: (-x[0], x[1]))
    return [sym for _, sym in qualified]


def x_filter_by_threshold__mutmut_12(
    candidates:  Sequence[str],
    scores:      Dict[str, float],
    threshold:   float,
) -> List[str]:
    """
    Filter candidates to those whose score >= threshold.

    Returns list sorted by descending score, then ascending symbol (deterministic).

    Args:
        candidates:  Sequence of candidate symbols.
        scores:      Mapping of symbol -> score. Symbols not in scores receive 0.0.
        threshold:   Minimum score (inclusive).

    Returns:
        Filtered and sorted list of symbols.
    """
    qualified = [
        (scores.get(sym, 0.0), sym)
        for sym in candidates
        if scores.get(sym, 0.0) > threshold
    ]
    qualified.sort(key=lambda x: (-x[0], x[1]))
    return [sym for _, sym in qualified]


def x_filter_by_threshold__mutmut_13(
    candidates:  Sequence[str],
    scores:      Dict[str, float],
    threshold:   float,
) -> List[str]:
    """
    Filter candidates to those whose score >= threshold.

    Returns list sorted by descending score, then ascending symbol (deterministic).

    Args:
        candidates:  Sequence of candidate symbols.
        scores:      Mapping of symbol -> score. Symbols not in scores receive 0.0.
        threshold:   Minimum score (inclusive).

    Returns:
        Filtered and sorted list of symbols.
    """
    qualified = [
        (scores.get(sym, 0.0), sym)
        for sym in candidates
        if scores.get(sym, 0.0) >= threshold
    ]
    qualified.sort(key=None)
    return [sym for _, sym in qualified]


def x_filter_by_threshold__mutmut_14(
    candidates:  Sequence[str],
    scores:      Dict[str, float],
    threshold:   float,
) -> List[str]:
    """
    Filter candidates to those whose score >= threshold.

    Returns list sorted by descending score, then ascending symbol (deterministic).

    Args:
        candidates:  Sequence of candidate symbols.
        scores:      Mapping of symbol -> score. Symbols not in scores receive 0.0.
        threshold:   Minimum score (inclusive).

    Returns:
        Filtered and sorted list of symbols.
    """
    qualified = [
        (scores.get(sym, 0.0), sym)
        for sym in candidates
        if scores.get(sym, 0.0) >= threshold
    ]
    qualified.sort(key=lambda x: None)
    return [sym for _, sym in qualified]


def x_filter_by_threshold__mutmut_15(
    candidates:  Sequence[str],
    scores:      Dict[str, float],
    threshold:   float,
) -> List[str]:
    """
    Filter candidates to those whose score >= threshold.

    Returns list sorted by descending score, then ascending symbol (deterministic).

    Args:
        candidates:  Sequence of candidate symbols.
        scores:      Mapping of symbol -> score. Symbols not in scores receive 0.0.
        threshold:   Minimum score (inclusive).

    Returns:
        Filtered and sorted list of symbols.
    """
    qualified = [
        (scores.get(sym, 0.0), sym)
        for sym in candidates
        if scores.get(sym, 0.0) >= threshold
    ]
    qualified.sort(key=lambda x: (+x[0], x[1]))
    return [sym for _, sym in qualified]


def x_filter_by_threshold__mutmut_16(
    candidates:  Sequence[str],
    scores:      Dict[str, float],
    threshold:   float,
) -> List[str]:
    """
    Filter candidates to those whose score >= threshold.

    Returns list sorted by descending score, then ascending symbol (deterministic).

    Args:
        candidates:  Sequence of candidate symbols.
        scores:      Mapping of symbol -> score. Symbols not in scores receive 0.0.
        threshold:   Minimum score (inclusive).

    Returns:
        Filtered and sorted list of symbols.
    """
    qualified = [
        (scores.get(sym, 0.0), sym)
        for sym in candidates
        if scores.get(sym, 0.0) >= threshold
    ]
    qualified.sort(key=lambda x: (-x[1], x[1]))
    return [sym for _, sym in qualified]


def x_filter_by_threshold__mutmut_17(
    candidates:  Sequence[str],
    scores:      Dict[str, float],
    threshold:   float,
) -> List[str]:
    """
    Filter candidates to those whose score >= threshold.

    Returns list sorted by descending score, then ascending symbol (deterministic).

    Args:
        candidates:  Sequence of candidate symbols.
        scores:      Mapping of symbol -> score. Symbols not in scores receive 0.0.
        threshold:   Minimum score (inclusive).

    Returns:
        Filtered and sorted list of symbols.
    """
    qualified = [
        (scores.get(sym, 0.0), sym)
        for sym in candidates
        if scores.get(sym, 0.0) >= threshold
    ]
    qualified.sort(key=lambda x: (-x[0], x[2]))
    return [sym for _, sym in qualified]

x_filter_by_threshold__mutmut_mutants : ClassVar[MutantDict] = { # type: ignore
'x_filter_by_threshold__mutmut_1': x_filter_by_threshold__mutmut_1, 
    'x_filter_by_threshold__mutmut_2': x_filter_by_threshold__mutmut_2, 
    'x_filter_by_threshold__mutmut_3': x_filter_by_threshold__mutmut_3, 
    'x_filter_by_threshold__mutmut_4': x_filter_by_threshold__mutmut_4, 
    'x_filter_by_threshold__mutmut_5': x_filter_by_threshold__mutmut_5, 
    'x_filter_by_threshold__mutmut_6': x_filter_by_threshold__mutmut_6, 
    'x_filter_by_threshold__mutmut_7': x_filter_by_threshold__mutmut_7, 
    'x_filter_by_threshold__mutmut_8': x_filter_by_threshold__mutmut_8, 
    'x_filter_by_threshold__mutmut_9': x_filter_by_threshold__mutmut_9, 
    'x_filter_by_threshold__mutmut_10': x_filter_by_threshold__mutmut_10, 
    'x_filter_by_threshold__mutmut_11': x_filter_by_threshold__mutmut_11, 
    'x_filter_by_threshold__mutmut_12': x_filter_by_threshold__mutmut_12, 
    'x_filter_by_threshold__mutmut_13': x_filter_by_threshold__mutmut_13, 
    'x_filter_by_threshold__mutmut_14': x_filter_by_threshold__mutmut_14, 
    'x_filter_by_threshold__mutmut_15': x_filter_by_threshold__mutmut_15, 
    'x_filter_by_threshold__mutmut_16': x_filter_by_threshold__mutmut_16, 
    'x_filter_by_threshold__mutmut_17': x_filter_by_threshold__mutmut_17
}
x_filter_by_threshold__mutmut_orig.__name__ = 'x_filter_by_threshold'


def select_top_n(
    candidates:  Sequence[str],
    scores:      Dict[str, float],
    n:           int,
) -> List[str]:
    args = [candidates, scores, n]# type: ignore
    kwargs = {}# type: ignore
    return _mutmut_trampoline(x_select_top_n__mutmut_orig, x_select_top_n__mutmut_mutants, args, kwargs, None)


def x_select_top_n__mutmut_orig(
    candidates:  Sequence[str],
    scores:      Dict[str, float],
    n:           int,
) -> List[str]:
    """
    Select top-n candidates by score.

    Args:
        candidates:  Sequence of candidate symbols.
        scores:      Mapping of symbol -> score. Missing symbols scored 0.0.
        n:           Number of candidates to select. If n >= len(candidates),
                     all candidates are returned (sorted).

    Returns:
        List of up to n symbols, sorted by descending score then ascending symbol.

    Raises:
        ValueError if n < 0.
    """
    if n < 0:
        raise ValueError(f"n must be >= 0; got {n}")
    ranked = filter_by_threshold(candidates, scores, threshold=float('-inf'))
    return ranked[:n]


def x_select_top_n__mutmut_1(
    candidates:  Sequence[str],
    scores:      Dict[str, float],
    n:           int,
) -> List[str]:
    """
    Select top-n candidates by score.

    Args:
        candidates:  Sequence of candidate symbols.
        scores:      Mapping of symbol -> score. Missing symbols scored 0.0.
        n:           Number of candidates to select. If n >= len(candidates),
                     all candidates are returned (sorted).

    Returns:
        List of up to n symbols, sorted by descending score then ascending symbol.

    Raises:
        ValueError if n < 0.
    """
    if n <= 0:
        raise ValueError(f"n must be >= 0; got {n}")
    ranked = filter_by_threshold(candidates, scores, threshold=float('-inf'))
    return ranked[:n]


def x_select_top_n__mutmut_2(
    candidates:  Sequence[str],
    scores:      Dict[str, float],
    n:           int,
) -> List[str]:
    """
    Select top-n candidates by score.

    Args:
        candidates:  Sequence of candidate symbols.
        scores:      Mapping of symbol -> score. Missing symbols scored 0.0.
        n:           Number of candidates to select. If n >= len(candidates),
                     all candidates are returned (sorted).

    Returns:
        List of up to n symbols, sorted by descending score then ascending symbol.

    Raises:
        ValueError if n < 0.
    """
    if n < 1:
        raise ValueError(f"n must be >= 0; got {n}")
    ranked = filter_by_threshold(candidates, scores, threshold=float('-inf'))
    return ranked[:n]


def x_select_top_n__mutmut_3(
    candidates:  Sequence[str],
    scores:      Dict[str, float],
    n:           int,
) -> List[str]:
    """
    Select top-n candidates by score.

    Args:
        candidates:  Sequence of candidate symbols.
        scores:      Mapping of symbol -> score. Missing symbols scored 0.0.
        n:           Number of candidates to select. If n >= len(candidates),
                     all candidates are returned (sorted).

    Returns:
        List of up to n symbols, sorted by descending score then ascending symbol.

    Raises:
        ValueError if n < 0.
    """
    if n < 0:
        raise ValueError(None)
    ranked = filter_by_threshold(candidates, scores, threshold=float('-inf'))
    return ranked[:n]


def x_select_top_n__mutmut_4(
    candidates:  Sequence[str],
    scores:      Dict[str, float],
    n:           int,
) -> List[str]:
    """
    Select top-n candidates by score.

    Args:
        candidates:  Sequence of candidate symbols.
        scores:      Mapping of symbol -> score. Missing symbols scored 0.0.
        n:           Number of candidates to select. If n >= len(candidates),
                     all candidates are returned (sorted).

    Returns:
        List of up to n symbols, sorted by descending score then ascending symbol.

    Raises:
        ValueError if n < 0.
    """
    if n < 0:
        raise ValueError(f"n must be >= 0; got {n}")
    ranked = None
    return ranked[:n]


def x_select_top_n__mutmut_5(
    candidates:  Sequence[str],
    scores:      Dict[str, float],
    n:           int,
) -> List[str]:
    """
    Select top-n candidates by score.

    Args:
        candidates:  Sequence of candidate symbols.
        scores:      Mapping of symbol -> score. Missing symbols scored 0.0.
        n:           Number of candidates to select. If n >= len(candidates),
                     all candidates are returned (sorted).

    Returns:
        List of up to n symbols, sorted by descending score then ascending symbol.

    Raises:
        ValueError if n < 0.
    """
    if n < 0:
        raise ValueError(f"n must be >= 0; got {n}")
    ranked = filter_by_threshold(None, scores, threshold=float('-inf'))
    return ranked[:n]


def x_select_top_n__mutmut_6(
    candidates:  Sequence[str],
    scores:      Dict[str, float],
    n:           int,
) -> List[str]:
    """
    Select top-n candidates by score.

    Args:
        candidates:  Sequence of candidate symbols.
        scores:      Mapping of symbol -> score. Missing symbols scored 0.0.
        n:           Number of candidates to select. If n >= len(candidates),
                     all candidates are returned (sorted).

    Returns:
        List of up to n symbols, sorted by descending score then ascending symbol.

    Raises:
        ValueError if n < 0.
    """
    if n < 0:
        raise ValueError(f"n must be >= 0; got {n}")
    ranked = filter_by_threshold(candidates, None, threshold=float('-inf'))
    return ranked[:n]


def x_select_top_n__mutmut_7(
    candidates:  Sequence[str],
    scores:      Dict[str, float],
    n:           int,
) -> List[str]:
    """
    Select top-n candidates by score.

    Args:
        candidates:  Sequence of candidate symbols.
        scores:      Mapping of symbol -> score. Missing symbols scored 0.0.
        n:           Number of candidates to select. If n >= len(candidates),
                     all candidates are returned (sorted).

    Returns:
        List of up to n symbols, sorted by descending score then ascending symbol.

    Raises:
        ValueError if n < 0.
    """
    if n < 0:
        raise ValueError(f"n must be >= 0; got {n}")
    ranked = filter_by_threshold(candidates, scores, threshold=None)
    return ranked[:n]


def x_select_top_n__mutmut_8(
    candidates:  Sequence[str],
    scores:      Dict[str, float],
    n:           int,
) -> List[str]:
    """
    Select top-n candidates by score.

    Args:
        candidates:  Sequence of candidate symbols.
        scores:      Mapping of symbol -> score. Missing symbols scored 0.0.
        n:           Number of candidates to select. If n >= len(candidates),
                     all candidates are returned (sorted).

    Returns:
        List of up to n symbols, sorted by descending score then ascending symbol.

    Raises:
        ValueError if n < 0.
    """
    if n < 0:
        raise ValueError(f"n must be >= 0; got {n}")
    ranked = filter_by_threshold(scores, threshold=float('-inf'))
    return ranked[:n]


def x_select_top_n__mutmut_9(
    candidates:  Sequence[str],
    scores:      Dict[str, float],
    n:           int,
) -> List[str]:
    """
    Select top-n candidates by score.

    Args:
        candidates:  Sequence of candidate symbols.
        scores:      Mapping of symbol -> score. Missing symbols scored 0.0.
        n:           Number of candidates to select. If n >= len(candidates),
                     all candidates are returned (sorted).

    Returns:
        List of up to n symbols, sorted by descending score then ascending symbol.

    Raises:
        ValueError if n < 0.
    """
    if n < 0:
        raise ValueError(f"n must be >= 0; got {n}")
    ranked = filter_by_threshold(candidates, threshold=float('-inf'))
    return ranked[:n]


def x_select_top_n__mutmut_10(
    candidates:  Sequence[str],
    scores:      Dict[str, float],
    n:           int,
) -> List[str]:
    """
    Select top-n candidates by score.

    Args:
        candidates:  Sequence of candidate symbols.
        scores:      Mapping of symbol -> score. Missing symbols scored 0.0.
        n:           Number of candidates to select. If n >= len(candidates),
                     all candidates are returned (sorted).

    Returns:
        List of up to n symbols, sorted by descending score then ascending symbol.

    Raises:
        ValueError if n < 0.
    """
    if n < 0:
        raise ValueError(f"n must be >= 0; got {n}")
    ranked = filter_by_threshold(candidates, scores, )
    return ranked[:n]


def x_select_top_n__mutmut_11(
    candidates:  Sequence[str],
    scores:      Dict[str, float],
    n:           int,
) -> List[str]:
    """
    Select top-n candidates by score.

    Args:
        candidates:  Sequence of candidate symbols.
        scores:      Mapping of symbol -> score. Missing symbols scored 0.0.
        n:           Number of candidates to select. If n >= len(candidates),
                     all candidates are returned (sorted).

    Returns:
        List of up to n symbols, sorted by descending score then ascending symbol.

    Raises:
        ValueError if n < 0.
    """
    if n < 0:
        raise ValueError(f"n must be >= 0; got {n}")
    ranked = filter_by_threshold(candidates, scores, threshold=float(None))
    return ranked[:n]


def x_select_top_n__mutmut_12(
    candidates:  Sequence[str],
    scores:      Dict[str, float],
    n:           int,
) -> List[str]:
    """
    Select top-n candidates by score.

    Args:
        candidates:  Sequence of candidate symbols.
        scores:      Mapping of symbol -> score. Missing symbols scored 0.0.
        n:           Number of candidates to select. If n >= len(candidates),
                     all candidates are returned (sorted).

    Returns:
        List of up to n symbols, sorted by descending score then ascending symbol.

    Raises:
        ValueError if n < 0.
    """
    if n < 0:
        raise ValueError(f"n must be >= 0; got {n}")
    ranked = filter_by_threshold(candidates, scores, threshold=float('XX-infXX'))
    return ranked[:n]


def x_select_top_n__mutmut_13(
    candidates:  Sequence[str],
    scores:      Dict[str, float],
    n:           int,
) -> List[str]:
    """
    Select top-n candidates by score.

    Args:
        candidates:  Sequence of candidate symbols.
        scores:      Mapping of symbol -> score. Missing symbols scored 0.0.
        n:           Number of candidates to select. If n >= len(candidates),
                     all candidates are returned (sorted).

    Returns:
        List of up to n symbols, sorted by descending score then ascending symbol.

    Raises:
        ValueError if n < 0.
    """
    if n < 0:
        raise ValueError(f"n must be >= 0; got {n}")
    ranked = filter_by_threshold(candidates, scores, threshold=float('-INF'))
    return ranked[:n]

x_select_top_n__mutmut_mutants : ClassVar[MutantDict] = { # type: ignore
'x_select_top_n__mutmut_1': x_select_top_n__mutmut_1, 
    'x_select_top_n__mutmut_2': x_select_top_n__mutmut_2, 
    'x_select_top_n__mutmut_3': x_select_top_n__mutmut_3, 
    'x_select_top_n__mutmut_4': x_select_top_n__mutmut_4, 
    'x_select_top_n__mutmut_5': x_select_top_n__mutmut_5, 
    'x_select_top_n__mutmut_6': x_select_top_n__mutmut_6, 
    'x_select_top_n__mutmut_7': x_select_top_n__mutmut_7, 
    'x_select_top_n__mutmut_8': x_select_top_n__mutmut_8, 
    'x_select_top_n__mutmut_9': x_select_top_n__mutmut_9, 
    'x_select_top_n__mutmut_10': x_select_top_n__mutmut_10, 
    'x_select_top_n__mutmut_11': x_select_top_n__mutmut_11, 
    'x_select_top_n__mutmut_12': x_select_top_n__mutmut_12, 
    'x_select_top_n__mutmut_13': x_select_top_n__mutmut_13
}
x_select_top_n__mutmut_orig.__name__ = 'x_select_top_n'


__all__ = [
    "rank_candidates",
    "filter_by_threshold",
    "select_top_n",
]
