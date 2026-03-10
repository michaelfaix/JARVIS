# =============================================================================
# JARVIS v6.1.0 -- WALK-FORWARD ENGINE
# File:   jarvis/walkforward/engine.py
# Version: 1.1.0
# =============================================================================
#
# SCOPE
# -----
# Deterministic rolling-window walk-forward validation.
# Generates train/test splits; applies a caller-supplied evaluation function.
# No randomness. No file I/O. Fully unit-testable.
#
# PUBLIC FUNCTIONS
# ----------------
#   generate_windows(n, train_size, test_size, step) -> List[WalkForwardWindow]
#   run_walkforward(data, train_size, test_size, step, evaluate_fn) -> List[dict]
#
# DETERMINISM CONSTRAINTS
# -----------------------
# DET-01  No stochastic operations.
# DET-02  All inputs passed explicitly.
# DET-03  No side effects. evaluate_fn must be deterministic (caller's responsibility).
# DET-04  No I/O, no logging, no datetime.now().
# =============================================================================

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable, Dict, List, Sequence
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
# DATA MODEL
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class WalkForwardWindow:
    """
    Single train/test split descriptor.

    Attributes:
        fold:        Zero-based fold index.
        train_start: Inclusive start index of training slice.
        train_end:   Exclusive end index of training slice.
        test_start:  Inclusive start index of test slice.
        test_end:    Exclusive end index of test slice.
    """
    fold:        int
    train_start: int
    train_end:   int
    test_start:  int
    test_end:    int


# ---------------------------------------------------------------------------
# GENERATE WINDOWS
# ---------------------------------------------------------------------------

def generate_windows(
    n:          int,
    train_size: int,
    test_size:  int,
    step:       int,
) -> List[WalkForwardWindow]:
    args = [n, train_size, test_size, step]# type: ignore
    kwargs = {}# type: ignore
    return _mutmut_trampoline(x_generate_windows__mutmut_orig, x_generate_windows__mutmut_mutants, args, kwargs, None)


# ---------------------------------------------------------------------------
# GENERATE WINDOWS
# ---------------------------------------------------------------------------

def x_generate_windows__mutmut_orig(
    n:          int,
    train_size: int,
    test_size:  int,
    step:       int,
) -> List[WalkForwardWindow]:
    """
    Generate deterministic rolling walk-forward windows.

    Args:
        n:          Total number of data points.
        train_size: Number of points in each training window.
        test_size:  Number of points in each test window.
        step:       Number of points to advance per fold.

    Returns:
        List of WalkForwardWindow. Empty list when no complete fold fits.

    Raises:
        ValueError if any argument < 1 or train_size + test_size > n.
    """
    if n < 1:
        raise ValueError(f"n must be >= 1; got {n}")
    if train_size < 1:
        raise ValueError(f"train_size must be >= 1; got {train_size}")
    if test_size < 1:
        raise ValueError(f"test_size must be >= 1; got {test_size}")
    if step < 1:
        raise ValueError(f"step must be >= 1; got {step}")

    windows: List[WalkForwardWindow] = []
    fold = 0
    train_start = 0
    while True:
        train_end = train_start + train_size
        test_start = train_end
        test_end = test_start + test_size
        if test_end > n:
            break
        windows.append(WalkForwardWindow(
            fold=fold,
            train_start=train_start,
            train_end=train_end,
            test_start=test_start,
            test_end=test_end,
        ))
        fold += 1
        train_start += step
    return windows


# ---------------------------------------------------------------------------
# GENERATE WINDOWS
# ---------------------------------------------------------------------------

def x_generate_windows__mutmut_1(
    n:          int,
    train_size: int,
    test_size:  int,
    step:       int,
) -> List[WalkForwardWindow]:
    """
    Generate deterministic rolling walk-forward windows.

    Args:
        n:          Total number of data points.
        train_size: Number of points in each training window.
        test_size:  Number of points in each test window.
        step:       Number of points to advance per fold.

    Returns:
        List of WalkForwardWindow. Empty list when no complete fold fits.

    Raises:
        ValueError if any argument < 1 or train_size + test_size > n.
    """
    if n <= 1:
        raise ValueError(f"n must be >= 1; got {n}")
    if train_size < 1:
        raise ValueError(f"train_size must be >= 1; got {train_size}")
    if test_size < 1:
        raise ValueError(f"test_size must be >= 1; got {test_size}")
    if step < 1:
        raise ValueError(f"step must be >= 1; got {step}")

    windows: List[WalkForwardWindow] = []
    fold = 0
    train_start = 0
    while True:
        train_end = train_start + train_size
        test_start = train_end
        test_end = test_start + test_size
        if test_end > n:
            break
        windows.append(WalkForwardWindow(
            fold=fold,
            train_start=train_start,
            train_end=train_end,
            test_start=test_start,
            test_end=test_end,
        ))
        fold += 1
        train_start += step
    return windows


# ---------------------------------------------------------------------------
# GENERATE WINDOWS
# ---------------------------------------------------------------------------

def x_generate_windows__mutmut_2(
    n:          int,
    train_size: int,
    test_size:  int,
    step:       int,
) -> List[WalkForwardWindow]:
    """
    Generate deterministic rolling walk-forward windows.

    Args:
        n:          Total number of data points.
        train_size: Number of points in each training window.
        test_size:  Number of points in each test window.
        step:       Number of points to advance per fold.

    Returns:
        List of WalkForwardWindow. Empty list when no complete fold fits.

    Raises:
        ValueError if any argument < 1 or train_size + test_size > n.
    """
    if n < 2:
        raise ValueError(f"n must be >= 1; got {n}")
    if train_size < 1:
        raise ValueError(f"train_size must be >= 1; got {train_size}")
    if test_size < 1:
        raise ValueError(f"test_size must be >= 1; got {test_size}")
    if step < 1:
        raise ValueError(f"step must be >= 1; got {step}")

    windows: List[WalkForwardWindow] = []
    fold = 0
    train_start = 0
    while True:
        train_end = train_start + train_size
        test_start = train_end
        test_end = test_start + test_size
        if test_end > n:
            break
        windows.append(WalkForwardWindow(
            fold=fold,
            train_start=train_start,
            train_end=train_end,
            test_start=test_start,
            test_end=test_end,
        ))
        fold += 1
        train_start += step
    return windows


# ---------------------------------------------------------------------------
# GENERATE WINDOWS
# ---------------------------------------------------------------------------

def x_generate_windows__mutmut_3(
    n:          int,
    train_size: int,
    test_size:  int,
    step:       int,
) -> List[WalkForwardWindow]:
    """
    Generate deterministic rolling walk-forward windows.

    Args:
        n:          Total number of data points.
        train_size: Number of points in each training window.
        test_size:  Number of points in each test window.
        step:       Number of points to advance per fold.

    Returns:
        List of WalkForwardWindow. Empty list when no complete fold fits.

    Raises:
        ValueError if any argument < 1 or train_size + test_size > n.
    """
    if n < 1:
        raise ValueError(None)
    if train_size < 1:
        raise ValueError(f"train_size must be >= 1; got {train_size}")
    if test_size < 1:
        raise ValueError(f"test_size must be >= 1; got {test_size}")
    if step < 1:
        raise ValueError(f"step must be >= 1; got {step}")

    windows: List[WalkForwardWindow] = []
    fold = 0
    train_start = 0
    while True:
        train_end = train_start + train_size
        test_start = train_end
        test_end = test_start + test_size
        if test_end > n:
            break
        windows.append(WalkForwardWindow(
            fold=fold,
            train_start=train_start,
            train_end=train_end,
            test_start=test_start,
            test_end=test_end,
        ))
        fold += 1
        train_start += step
    return windows


# ---------------------------------------------------------------------------
# GENERATE WINDOWS
# ---------------------------------------------------------------------------

def x_generate_windows__mutmut_4(
    n:          int,
    train_size: int,
    test_size:  int,
    step:       int,
) -> List[WalkForwardWindow]:
    """
    Generate deterministic rolling walk-forward windows.

    Args:
        n:          Total number of data points.
        train_size: Number of points in each training window.
        test_size:  Number of points in each test window.
        step:       Number of points to advance per fold.

    Returns:
        List of WalkForwardWindow. Empty list when no complete fold fits.

    Raises:
        ValueError if any argument < 1 or train_size + test_size > n.
    """
    if n < 1:
        raise ValueError(f"n must be >= 1; got {n}")
    if train_size <= 1:
        raise ValueError(f"train_size must be >= 1; got {train_size}")
    if test_size < 1:
        raise ValueError(f"test_size must be >= 1; got {test_size}")
    if step < 1:
        raise ValueError(f"step must be >= 1; got {step}")

    windows: List[WalkForwardWindow] = []
    fold = 0
    train_start = 0
    while True:
        train_end = train_start + train_size
        test_start = train_end
        test_end = test_start + test_size
        if test_end > n:
            break
        windows.append(WalkForwardWindow(
            fold=fold,
            train_start=train_start,
            train_end=train_end,
            test_start=test_start,
            test_end=test_end,
        ))
        fold += 1
        train_start += step
    return windows


# ---------------------------------------------------------------------------
# GENERATE WINDOWS
# ---------------------------------------------------------------------------

def x_generate_windows__mutmut_5(
    n:          int,
    train_size: int,
    test_size:  int,
    step:       int,
) -> List[WalkForwardWindow]:
    """
    Generate deterministic rolling walk-forward windows.

    Args:
        n:          Total number of data points.
        train_size: Number of points in each training window.
        test_size:  Number of points in each test window.
        step:       Number of points to advance per fold.

    Returns:
        List of WalkForwardWindow. Empty list when no complete fold fits.

    Raises:
        ValueError if any argument < 1 or train_size + test_size > n.
    """
    if n < 1:
        raise ValueError(f"n must be >= 1; got {n}")
    if train_size < 2:
        raise ValueError(f"train_size must be >= 1; got {train_size}")
    if test_size < 1:
        raise ValueError(f"test_size must be >= 1; got {test_size}")
    if step < 1:
        raise ValueError(f"step must be >= 1; got {step}")

    windows: List[WalkForwardWindow] = []
    fold = 0
    train_start = 0
    while True:
        train_end = train_start + train_size
        test_start = train_end
        test_end = test_start + test_size
        if test_end > n:
            break
        windows.append(WalkForwardWindow(
            fold=fold,
            train_start=train_start,
            train_end=train_end,
            test_start=test_start,
            test_end=test_end,
        ))
        fold += 1
        train_start += step
    return windows


# ---------------------------------------------------------------------------
# GENERATE WINDOWS
# ---------------------------------------------------------------------------

def x_generate_windows__mutmut_6(
    n:          int,
    train_size: int,
    test_size:  int,
    step:       int,
) -> List[WalkForwardWindow]:
    """
    Generate deterministic rolling walk-forward windows.

    Args:
        n:          Total number of data points.
        train_size: Number of points in each training window.
        test_size:  Number of points in each test window.
        step:       Number of points to advance per fold.

    Returns:
        List of WalkForwardWindow. Empty list when no complete fold fits.

    Raises:
        ValueError if any argument < 1 or train_size + test_size > n.
    """
    if n < 1:
        raise ValueError(f"n must be >= 1; got {n}")
    if train_size < 1:
        raise ValueError(None)
    if test_size < 1:
        raise ValueError(f"test_size must be >= 1; got {test_size}")
    if step < 1:
        raise ValueError(f"step must be >= 1; got {step}")

    windows: List[WalkForwardWindow] = []
    fold = 0
    train_start = 0
    while True:
        train_end = train_start + train_size
        test_start = train_end
        test_end = test_start + test_size
        if test_end > n:
            break
        windows.append(WalkForwardWindow(
            fold=fold,
            train_start=train_start,
            train_end=train_end,
            test_start=test_start,
            test_end=test_end,
        ))
        fold += 1
        train_start += step
    return windows


# ---------------------------------------------------------------------------
# GENERATE WINDOWS
# ---------------------------------------------------------------------------

def x_generate_windows__mutmut_7(
    n:          int,
    train_size: int,
    test_size:  int,
    step:       int,
) -> List[WalkForwardWindow]:
    """
    Generate deterministic rolling walk-forward windows.

    Args:
        n:          Total number of data points.
        train_size: Number of points in each training window.
        test_size:  Number of points in each test window.
        step:       Number of points to advance per fold.

    Returns:
        List of WalkForwardWindow. Empty list when no complete fold fits.

    Raises:
        ValueError if any argument < 1 or train_size + test_size > n.
    """
    if n < 1:
        raise ValueError(f"n must be >= 1; got {n}")
    if train_size < 1:
        raise ValueError(f"train_size must be >= 1; got {train_size}")
    if test_size <= 1:
        raise ValueError(f"test_size must be >= 1; got {test_size}")
    if step < 1:
        raise ValueError(f"step must be >= 1; got {step}")

    windows: List[WalkForwardWindow] = []
    fold = 0
    train_start = 0
    while True:
        train_end = train_start + train_size
        test_start = train_end
        test_end = test_start + test_size
        if test_end > n:
            break
        windows.append(WalkForwardWindow(
            fold=fold,
            train_start=train_start,
            train_end=train_end,
            test_start=test_start,
            test_end=test_end,
        ))
        fold += 1
        train_start += step
    return windows


# ---------------------------------------------------------------------------
# GENERATE WINDOWS
# ---------------------------------------------------------------------------

def x_generate_windows__mutmut_8(
    n:          int,
    train_size: int,
    test_size:  int,
    step:       int,
) -> List[WalkForwardWindow]:
    """
    Generate deterministic rolling walk-forward windows.

    Args:
        n:          Total number of data points.
        train_size: Number of points in each training window.
        test_size:  Number of points in each test window.
        step:       Number of points to advance per fold.

    Returns:
        List of WalkForwardWindow. Empty list when no complete fold fits.

    Raises:
        ValueError if any argument < 1 or train_size + test_size > n.
    """
    if n < 1:
        raise ValueError(f"n must be >= 1; got {n}")
    if train_size < 1:
        raise ValueError(f"train_size must be >= 1; got {train_size}")
    if test_size < 2:
        raise ValueError(f"test_size must be >= 1; got {test_size}")
    if step < 1:
        raise ValueError(f"step must be >= 1; got {step}")

    windows: List[WalkForwardWindow] = []
    fold = 0
    train_start = 0
    while True:
        train_end = train_start + train_size
        test_start = train_end
        test_end = test_start + test_size
        if test_end > n:
            break
        windows.append(WalkForwardWindow(
            fold=fold,
            train_start=train_start,
            train_end=train_end,
            test_start=test_start,
            test_end=test_end,
        ))
        fold += 1
        train_start += step
    return windows


# ---------------------------------------------------------------------------
# GENERATE WINDOWS
# ---------------------------------------------------------------------------

def x_generate_windows__mutmut_9(
    n:          int,
    train_size: int,
    test_size:  int,
    step:       int,
) -> List[WalkForwardWindow]:
    """
    Generate deterministic rolling walk-forward windows.

    Args:
        n:          Total number of data points.
        train_size: Number of points in each training window.
        test_size:  Number of points in each test window.
        step:       Number of points to advance per fold.

    Returns:
        List of WalkForwardWindow. Empty list when no complete fold fits.

    Raises:
        ValueError if any argument < 1 or train_size + test_size > n.
    """
    if n < 1:
        raise ValueError(f"n must be >= 1; got {n}")
    if train_size < 1:
        raise ValueError(f"train_size must be >= 1; got {train_size}")
    if test_size < 1:
        raise ValueError(None)
    if step < 1:
        raise ValueError(f"step must be >= 1; got {step}")

    windows: List[WalkForwardWindow] = []
    fold = 0
    train_start = 0
    while True:
        train_end = train_start + train_size
        test_start = train_end
        test_end = test_start + test_size
        if test_end > n:
            break
        windows.append(WalkForwardWindow(
            fold=fold,
            train_start=train_start,
            train_end=train_end,
            test_start=test_start,
            test_end=test_end,
        ))
        fold += 1
        train_start += step
    return windows


# ---------------------------------------------------------------------------
# GENERATE WINDOWS
# ---------------------------------------------------------------------------

def x_generate_windows__mutmut_10(
    n:          int,
    train_size: int,
    test_size:  int,
    step:       int,
) -> List[WalkForwardWindow]:
    """
    Generate deterministic rolling walk-forward windows.

    Args:
        n:          Total number of data points.
        train_size: Number of points in each training window.
        test_size:  Number of points in each test window.
        step:       Number of points to advance per fold.

    Returns:
        List of WalkForwardWindow. Empty list when no complete fold fits.

    Raises:
        ValueError if any argument < 1 or train_size + test_size > n.
    """
    if n < 1:
        raise ValueError(f"n must be >= 1; got {n}")
    if train_size < 1:
        raise ValueError(f"train_size must be >= 1; got {train_size}")
    if test_size < 1:
        raise ValueError(f"test_size must be >= 1; got {test_size}")
    if step <= 1:
        raise ValueError(f"step must be >= 1; got {step}")

    windows: List[WalkForwardWindow] = []
    fold = 0
    train_start = 0
    while True:
        train_end = train_start + train_size
        test_start = train_end
        test_end = test_start + test_size
        if test_end > n:
            break
        windows.append(WalkForwardWindow(
            fold=fold,
            train_start=train_start,
            train_end=train_end,
            test_start=test_start,
            test_end=test_end,
        ))
        fold += 1
        train_start += step
    return windows


# ---------------------------------------------------------------------------
# GENERATE WINDOWS
# ---------------------------------------------------------------------------

def x_generate_windows__mutmut_11(
    n:          int,
    train_size: int,
    test_size:  int,
    step:       int,
) -> List[WalkForwardWindow]:
    """
    Generate deterministic rolling walk-forward windows.

    Args:
        n:          Total number of data points.
        train_size: Number of points in each training window.
        test_size:  Number of points in each test window.
        step:       Number of points to advance per fold.

    Returns:
        List of WalkForwardWindow. Empty list when no complete fold fits.

    Raises:
        ValueError if any argument < 1 or train_size + test_size > n.
    """
    if n < 1:
        raise ValueError(f"n must be >= 1; got {n}")
    if train_size < 1:
        raise ValueError(f"train_size must be >= 1; got {train_size}")
    if test_size < 1:
        raise ValueError(f"test_size must be >= 1; got {test_size}")
    if step < 2:
        raise ValueError(f"step must be >= 1; got {step}")

    windows: List[WalkForwardWindow] = []
    fold = 0
    train_start = 0
    while True:
        train_end = train_start + train_size
        test_start = train_end
        test_end = test_start + test_size
        if test_end > n:
            break
        windows.append(WalkForwardWindow(
            fold=fold,
            train_start=train_start,
            train_end=train_end,
            test_start=test_start,
            test_end=test_end,
        ))
        fold += 1
        train_start += step
    return windows


# ---------------------------------------------------------------------------
# GENERATE WINDOWS
# ---------------------------------------------------------------------------

def x_generate_windows__mutmut_12(
    n:          int,
    train_size: int,
    test_size:  int,
    step:       int,
) -> List[WalkForwardWindow]:
    """
    Generate deterministic rolling walk-forward windows.

    Args:
        n:          Total number of data points.
        train_size: Number of points in each training window.
        test_size:  Number of points in each test window.
        step:       Number of points to advance per fold.

    Returns:
        List of WalkForwardWindow. Empty list when no complete fold fits.

    Raises:
        ValueError if any argument < 1 or train_size + test_size > n.
    """
    if n < 1:
        raise ValueError(f"n must be >= 1; got {n}")
    if train_size < 1:
        raise ValueError(f"train_size must be >= 1; got {train_size}")
    if test_size < 1:
        raise ValueError(f"test_size must be >= 1; got {test_size}")
    if step < 1:
        raise ValueError(None)

    windows: List[WalkForwardWindow] = []
    fold = 0
    train_start = 0
    while True:
        train_end = train_start + train_size
        test_start = train_end
        test_end = test_start + test_size
        if test_end > n:
            break
        windows.append(WalkForwardWindow(
            fold=fold,
            train_start=train_start,
            train_end=train_end,
            test_start=test_start,
            test_end=test_end,
        ))
        fold += 1
        train_start += step
    return windows


# ---------------------------------------------------------------------------
# GENERATE WINDOWS
# ---------------------------------------------------------------------------

def x_generate_windows__mutmut_13(
    n:          int,
    train_size: int,
    test_size:  int,
    step:       int,
) -> List[WalkForwardWindow]:
    """
    Generate deterministic rolling walk-forward windows.

    Args:
        n:          Total number of data points.
        train_size: Number of points in each training window.
        test_size:  Number of points in each test window.
        step:       Number of points to advance per fold.

    Returns:
        List of WalkForwardWindow. Empty list when no complete fold fits.

    Raises:
        ValueError if any argument < 1 or train_size + test_size > n.
    """
    if n < 1:
        raise ValueError(f"n must be >= 1; got {n}")
    if train_size < 1:
        raise ValueError(f"train_size must be >= 1; got {train_size}")
    if test_size < 1:
        raise ValueError(f"test_size must be >= 1; got {test_size}")
    if step < 1:
        raise ValueError(f"step must be >= 1; got {step}")

    windows: List[WalkForwardWindow] = None
    fold = 0
    train_start = 0
    while True:
        train_end = train_start + train_size
        test_start = train_end
        test_end = test_start + test_size
        if test_end > n:
            break
        windows.append(WalkForwardWindow(
            fold=fold,
            train_start=train_start,
            train_end=train_end,
            test_start=test_start,
            test_end=test_end,
        ))
        fold += 1
        train_start += step
    return windows


# ---------------------------------------------------------------------------
# GENERATE WINDOWS
# ---------------------------------------------------------------------------

def x_generate_windows__mutmut_14(
    n:          int,
    train_size: int,
    test_size:  int,
    step:       int,
) -> List[WalkForwardWindow]:
    """
    Generate deterministic rolling walk-forward windows.

    Args:
        n:          Total number of data points.
        train_size: Number of points in each training window.
        test_size:  Number of points in each test window.
        step:       Number of points to advance per fold.

    Returns:
        List of WalkForwardWindow. Empty list when no complete fold fits.

    Raises:
        ValueError if any argument < 1 or train_size + test_size > n.
    """
    if n < 1:
        raise ValueError(f"n must be >= 1; got {n}")
    if train_size < 1:
        raise ValueError(f"train_size must be >= 1; got {train_size}")
    if test_size < 1:
        raise ValueError(f"test_size must be >= 1; got {test_size}")
    if step < 1:
        raise ValueError(f"step must be >= 1; got {step}")

    windows: List[WalkForwardWindow] = []
    fold = None
    train_start = 0
    while True:
        train_end = train_start + train_size
        test_start = train_end
        test_end = test_start + test_size
        if test_end > n:
            break
        windows.append(WalkForwardWindow(
            fold=fold,
            train_start=train_start,
            train_end=train_end,
            test_start=test_start,
            test_end=test_end,
        ))
        fold += 1
        train_start += step
    return windows


# ---------------------------------------------------------------------------
# GENERATE WINDOWS
# ---------------------------------------------------------------------------

def x_generate_windows__mutmut_15(
    n:          int,
    train_size: int,
    test_size:  int,
    step:       int,
) -> List[WalkForwardWindow]:
    """
    Generate deterministic rolling walk-forward windows.

    Args:
        n:          Total number of data points.
        train_size: Number of points in each training window.
        test_size:  Number of points in each test window.
        step:       Number of points to advance per fold.

    Returns:
        List of WalkForwardWindow. Empty list when no complete fold fits.

    Raises:
        ValueError if any argument < 1 or train_size + test_size > n.
    """
    if n < 1:
        raise ValueError(f"n must be >= 1; got {n}")
    if train_size < 1:
        raise ValueError(f"train_size must be >= 1; got {train_size}")
    if test_size < 1:
        raise ValueError(f"test_size must be >= 1; got {test_size}")
    if step < 1:
        raise ValueError(f"step must be >= 1; got {step}")

    windows: List[WalkForwardWindow] = []
    fold = 1
    train_start = 0
    while True:
        train_end = train_start + train_size
        test_start = train_end
        test_end = test_start + test_size
        if test_end > n:
            break
        windows.append(WalkForwardWindow(
            fold=fold,
            train_start=train_start,
            train_end=train_end,
            test_start=test_start,
            test_end=test_end,
        ))
        fold += 1
        train_start += step
    return windows


# ---------------------------------------------------------------------------
# GENERATE WINDOWS
# ---------------------------------------------------------------------------

def x_generate_windows__mutmut_16(
    n:          int,
    train_size: int,
    test_size:  int,
    step:       int,
) -> List[WalkForwardWindow]:
    """
    Generate deterministic rolling walk-forward windows.

    Args:
        n:          Total number of data points.
        train_size: Number of points in each training window.
        test_size:  Number of points in each test window.
        step:       Number of points to advance per fold.

    Returns:
        List of WalkForwardWindow. Empty list when no complete fold fits.

    Raises:
        ValueError if any argument < 1 or train_size + test_size > n.
    """
    if n < 1:
        raise ValueError(f"n must be >= 1; got {n}")
    if train_size < 1:
        raise ValueError(f"train_size must be >= 1; got {train_size}")
    if test_size < 1:
        raise ValueError(f"test_size must be >= 1; got {test_size}")
    if step < 1:
        raise ValueError(f"step must be >= 1; got {step}")

    windows: List[WalkForwardWindow] = []
    fold = 0
    train_start = None
    while True:
        train_end = train_start + train_size
        test_start = train_end
        test_end = test_start + test_size
        if test_end > n:
            break
        windows.append(WalkForwardWindow(
            fold=fold,
            train_start=train_start,
            train_end=train_end,
            test_start=test_start,
            test_end=test_end,
        ))
        fold += 1
        train_start += step
    return windows


# ---------------------------------------------------------------------------
# GENERATE WINDOWS
# ---------------------------------------------------------------------------

def x_generate_windows__mutmut_17(
    n:          int,
    train_size: int,
    test_size:  int,
    step:       int,
) -> List[WalkForwardWindow]:
    """
    Generate deterministic rolling walk-forward windows.

    Args:
        n:          Total number of data points.
        train_size: Number of points in each training window.
        test_size:  Number of points in each test window.
        step:       Number of points to advance per fold.

    Returns:
        List of WalkForwardWindow. Empty list when no complete fold fits.

    Raises:
        ValueError if any argument < 1 or train_size + test_size > n.
    """
    if n < 1:
        raise ValueError(f"n must be >= 1; got {n}")
    if train_size < 1:
        raise ValueError(f"train_size must be >= 1; got {train_size}")
    if test_size < 1:
        raise ValueError(f"test_size must be >= 1; got {test_size}")
    if step < 1:
        raise ValueError(f"step must be >= 1; got {step}")

    windows: List[WalkForwardWindow] = []
    fold = 0
    train_start = 1
    while True:
        train_end = train_start + train_size
        test_start = train_end
        test_end = test_start + test_size
        if test_end > n:
            break
        windows.append(WalkForwardWindow(
            fold=fold,
            train_start=train_start,
            train_end=train_end,
            test_start=test_start,
            test_end=test_end,
        ))
        fold += 1
        train_start += step
    return windows


# ---------------------------------------------------------------------------
# GENERATE WINDOWS
# ---------------------------------------------------------------------------

def x_generate_windows__mutmut_18(
    n:          int,
    train_size: int,
    test_size:  int,
    step:       int,
) -> List[WalkForwardWindow]:
    """
    Generate deterministic rolling walk-forward windows.

    Args:
        n:          Total number of data points.
        train_size: Number of points in each training window.
        test_size:  Number of points in each test window.
        step:       Number of points to advance per fold.

    Returns:
        List of WalkForwardWindow. Empty list when no complete fold fits.

    Raises:
        ValueError if any argument < 1 or train_size + test_size > n.
    """
    if n < 1:
        raise ValueError(f"n must be >= 1; got {n}")
    if train_size < 1:
        raise ValueError(f"train_size must be >= 1; got {train_size}")
    if test_size < 1:
        raise ValueError(f"test_size must be >= 1; got {test_size}")
    if step < 1:
        raise ValueError(f"step must be >= 1; got {step}")

    windows: List[WalkForwardWindow] = []
    fold = 0
    train_start = 0
    while False:
        train_end = train_start + train_size
        test_start = train_end
        test_end = test_start + test_size
        if test_end > n:
            break
        windows.append(WalkForwardWindow(
            fold=fold,
            train_start=train_start,
            train_end=train_end,
            test_start=test_start,
            test_end=test_end,
        ))
        fold += 1
        train_start += step
    return windows


# ---------------------------------------------------------------------------
# GENERATE WINDOWS
# ---------------------------------------------------------------------------

def x_generate_windows__mutmut_19(
    n:          int,
    train_size: int,
    test_size:  int,
    step:       int,
) -> List[WalkForwardWindow]:
    """
    Generate deterministic rolling walk-forward windows.

    Args:
        n:          Total number of data points.
        train_size: Number of points in each training window.
        test_size:  Number of points in each test window.
        step:       Number of points to advance per fold.

    Returns:
        List of WalkForwardWindow. Empty list when no complete fold fits.

    Raises:
        ValueError if any argument < 1 or train_size + test_size > n.
    """
    if n < 1:
        raise ValueError(f"n must be >= 1; got {n}")
    if train_size < 1:
        raise ValueError(f"train_size must be >= 1; got {train_size}")
    if test_size < 1:
        raise ValueError(f"test_size must be >= 1; got {test_size}")
    if step < 1:
        raise ValueError(f"step must be >= 1; got {step}")

    windows: List[WalkForwardWindow] = []
    fold = 0
    train_start = 0
    while True:
        train_end = None
        test_start = train_end
        test_end = test_start + test_size
        if test_end > n:
            break
        windows.append(WalkForwardWindow(
            fold=fold,
            train_start=train_start,
            train_end=train_end,
            test_start=test_start,
            test_end=test_end,
        ))
        fold += 1
        train_start += step
    return windows


# ---------------------------------------------------------------------------
# GENERATE WINDOWS
# ---------------------------------------------------------------------------

def x_generate_windows__mutmut_20(
    n:          int,
    train_size: int,
    test_size:  int,
    step:       int,
) -> List[WalkForwardWindow]:
    """
    Generate deterministic rolling walk-forward windows.

    Args:
        n:          Total number of data points.
        train_size: Number of points in each training window.
        test_size:  Number of points in each test window.
        step:       Number of points to advance per fold.

    Returns:
        List of WalkForwardWindow. Empty list when no complete fold fits.

    Raises:
        ValueError if any argument < 1 or train_size + test_size > n.
    """
    if n < 1:
        raise ValueError(f"n must be >= 1; got {n}")
    if train_size < 1:
        raise ValueError(f"train_size must be >= 1; got {train_size}")
    if test_size < 1:
        raise ValueError(f"test_size must be >= 1; got {test_size}")
    if step < 1:
        raise ValueError(f"step must be >= 1; got {step}")

    windows: List[WalkForwardWindow] = []
    fold = 0
    train_start = 0
    while True:
        train_end = train_start - train_size
        test_start = train_end
        test_end = test_start + test_size
        if test_end > n:
            break
        windows.append(WalkForwardWindow(
            fold=fold,
            train_start=train_start,
            train_end=train_end,
            test_start=test_start,
            test_end=test_end,
        ))
        fold += 1
        train_start += step
    return windows


# ---------------------------------------------------------------------------
# GENERATE WINDOWS
# ---------------------------------------------------------------------------

def x_generate_windows__mutmut_21(
    n:          int,
    train_size: int,
    test_size:  int,
    step:       int,
) -> List[WalkForwardWindow]:
    """
    Generate deterministic rolling walk-forward windows.

    Args:
        n:          Total number of data points.
        train_size: Number of points in each training window.
        test_size:  Number of points in each test window.
        step:       Number of points to advance per fold.

    Returns:
        List of WalkForwardWindow. Empty list when no complete fold fits.

    Raises:
        ValueError if any argument < 1 or train_size + test_size > n.
    """
    if n < 1:
        raise ValueError(f"n must be >= 1; got {n}")
    if train_size < 1:
        raise ValueError(f"train_size must be >= 1; got {train_size}")
    if test_size < 1:
        raise ValueError(f"test_size must be >= 1; got {test_size}")
    if step < 1:
        raise ValueError(f"step must be >= 1; got {step}")

    windows: List[WalkForwardWindow] = []
    fold = 0
    train_start = 0
    while True:
        train_end = train_start + train_size
        test_start = None
        test_end = test_start + test_size
        if test_end > n:
            break
        windows.append(WalkForwardWindow(
            fold=fold,
            train_start=train_start,
            train_end=train_end,
            test_start=test_start,
            test_end=test_end,
        ))
        fold += 1
        train_start += step
    return windows


# ---------------------------------------------------------------------------
# GENERATE WINDOWS
# ---------------------------------------------------------------------------

def x_generate_windows__mutmut_22(
    n:          int,
    train_size: int,
    test_size:  int,
    step:       int,
) -> List[WalkForwardWindow]:
    """
    Generate deterministic rolling walk-forward windows.

    Args:
        n:          Total number of data points.
        train_size: Number of points in each training window.
        test_size:  Number of points in each test window.
        step:       Number of points to advance per fold.

    Returns:
        List of WalkForwardWindow. Empty list when no complete fold fits.

    Raises:
        ValueError if any argument < 1 or train_size + test_size > n.
    """
    if n < 1:
        raise ValueError(f"n must be >= 1; got {n}")
    if train_size < 1:
        raise ValueError(f"train_size must be >= 1; got {train_size}")
    if test_size < 1:
        raise ValueError(f"test_size must be >= 1; got {test_size}")
    if step < 1:
        raise ValueError(f"step must be >= 1; got {step}")

    windows: List[WalkForwardWindow] = []
    fold = 0
    train_start = 0
    while True:
        train_end = train_start + train_size
        test_start = train_end
        test_end = None
        if test_end > n:
            break
        windows.append(WalkForwardWindow(
            fold=fold,
            train_start=train_start,
            train_end=train_end,
            test_start=test_start,
            test_end=test_end,
        ))
        fold += 1
        train_start += step
    return windows


# ---------------------------------------------------------------------------
# GENERATE WINDOWS
# ---------------------------------------------------------------------------

def x_generate_windows__mutmut_23(
    n:          int,
    train_size: int,
    test_size:  int,
    step:       int,
) -> List[WalkForwardWindow]:
    """
    Generate deterministic rolling walk-forward windows.

    Args:
        n:          Total number of data points.
        train_size: Number of points in each training window.
        test_size:  Number of points in each test window.
        step:       Number of points to advance per fold.

    Returns:
        List of WalkForwardWindow. Empty list when no complete fold fits.

    Raises:
        ValueError if any argument < 1 or train_size + test_size > n.
    """
    if n < 1:
        raise ValueError(f"n must be >= 1; got {n}")
    if train_size < 1:
        raise ValueError(f"train_size must be >= 1; got {train_size}")
    if test_size < 1:
        raise ValueError(f"test_size must be >= 1; got {test_size}")
    if step < 1:
        raise ValueError(f"step must be >= 1; got {step}")

    windows: List[WalkForwardWindow] = []
    fold = 0
    train_start = 0
    while True:
        train_end = train_start + train_size
        test_start = train_end
        test_end = test_start - test_size
        if test_end > n:
            break
        windows.append(WalkForwardWindow(
            fold=fold,
            train_start=train_start,
            train_end=train_end,
            test_start=test_start,
            test_end=test_end,
        ))
        fold += 1
        train_start += step
    return windows


# ---------------------------------------------------------------------------
# GENERATE WINDOWS
# ---------------------------------------------------------------------------

def x_generate_windows__mutmut_24(
    n:          int,
    train_size: int,
    test_size:  int,
    step:       int,
) -> List[WalkForwardWindow]:
    """
    Generate deterministic rolling walk-forward windows.

    Args:
        n:          Total number of data points.
        train_size: Number of points in each training window.
        test_size:  Number of points in each test window.
        step:       Number of points to advance per fold.

    Returns:
        List of WalkForwardWindow. Empty list when no complete fold fits.

    Raises:
        ValueError if any argument < 1 or train_size + test_size > n.
    """
    if n < 1:
        raise ValueError(f"n must be >= 1; got {n}")
    if train_size < 1:
        raise ValueError(f"train_size must be >= 1; got {train_size}")
    if test_size < 1:
        raise ValueError(f"test_size must be >= 1; got {test_size}")
    if step < 1:
        raise ValueError(f"step must be >= 1; got {step}")

    windows: List[WalkForwardWindow] = []
    fold = 0
    train_start = 0
    while True:
        train_end = train_start + train_size
        test_start = train_end
        test_end = test_start + test_size
        if test_end >= n:
            break
        windows.append(WalkForwardWindow(
            fold=fold,
            train_start=train_start,
            train_end=train_end,
            test_start=test_start,
            test_end=test_end,
        ))
        fold += 1
        train_start += step
    return windows


# ---------------------------------------------------------------------------
# GENERATE WINDOWS
# ---------------------------------------------------------------------------

def x_generate_windows__mutmut_25(
    n:          int,
    train_size: int,
    test_size:  int,
    step:       int,
) -> List[WalkForwardWindow]:
    """
    Generate deterministic rolling walk-forward windows.

    Args:
        n:          Total number of data points.
        train_size: Number of points in each training window.
        test_size:  Number of points in each test window.
        step:       Number of points to advance per fold.

    Returns:
        List of WalkForwardWindow. Empty list when no complete fold fits.

    Raises:
        ValueError if any argument < 1 or train_size + test_size > n.
    """
    if n < 1:
        raise ValueError(f"n must be >= 1; got {n}")
    if train_size < 1:
        raise ValueError(f"train_size must be >= 1; got {train_size}")
    if test_size < 1:
        raise ValueError(f"test_size must be >= 1; got {test_size}")
    if step < 1:
        raise ValueError(f"step must be >= 1; got {step}")

    windows: List[WalkForwardWindow] = []
    fold = 0
    train_start = 0
    while True:
        train_end = train_start + train_size
        test_start = train_end
        test_end = test_start + test_size
        if test_end > n:
            return
        windows.append(WalkForwardWindow(
            fold=fold,
            train_start=train_start,
            train_end=train_end,
            test_start=test_start,
            test_end=test_end,
        ))
        fold += 1
        train_start += step
    return windows


# ---------------------------------------------------------------------------
# GENERATE WINDOWS
# ---------------------------------------------------------------------------

def x_generate_windows__mutmut_26(
    n:          int,
    train_size: int,
    test_size:  int,
    step:       int,
) -> List[WalkForwardWindow]:
    """
    Generate deterministic rolling walk-forward windows.

    Args:
        n:          Total number of data points.
        train_size: Number of points in each training window.
        test_size:  Number of points in each test window.
        step:       Number of points to advance per fold.

    Returns:
        List of WalkForwardWindow. Empty list when no complete fold fits.

    Raises:
        ValueError if any argument < 1 or train_size + test_size > n.
    """
    if n < 1:
        raise ValueError(f"n must be >= 1; got {n}")
    if train_size < 1:
        raise ValueError(f"train_size must be >= 1; got {train_size}")
    if test_size < 1:
        raise ValueError(f"test_size must be >= 1; got {test_size}")
    if step < 1:
        raise ValueError(f"step must be >= 1; got {step}")

    windows: List[WalkForwardWindow] = []
    fold = 0
    train_start = 0
    while True:
        train_end = train_start + train_size
        test_start = train_end
        test_end = test_start + test_size
        if test_end > n:
            break
        windows.append(None)
        fold += 1
        train_start += step
    return windows


# ---------------------------------------------------------------------------
# GENERATE WINDOWS
# ---------------------------------------------------------------------------

def x_generate_windows__mutmut_27(
    n:          int,
    train_size: int,
    test_size:  int,
    step:       int,
) -> List[WalkForwardWindow]:
    """
    Generate deterministic rolling walk-forward windows.

    Args:
        n:          Total number of data points.
        train_size: Number of points in each training window.
        test_size:  Number of points in each test window.
        step:       Number of points to advance per fold.

    Returns:
        List of WalkForwardWindow. Empty list when no complete fold fits.

    Raises:
        ValueError if any argument < 1 or train_size + test_size > n.
    """
    if n < 1:
        raise ValueError(f"n must be >= 1; got {n}")
    if train_size < 1:
        raise ValueError(f"train_size must be >= 1; got {train_size}")
    if test_size < 1:
        raise ValueError(f"test_size must be >= 1; got {test_size}")
    if step < 1:
        raise ValueError(f"step must be >= 1; got {step}")

    windows: List[WalkForwardWindow] = []
    fold = 0
    train_start = 0
    while True:
        train_end = train_start + train_size
        test_start = train_end
        test_end = test_start + test_size
        if test_end > n:
            break
        windows.append(WalkForwardWindow(
            fold=None,
            train_start=train_start,
            train_end=train_end,
            test_start=test_start,
            test_end=test_end,
        ))
        fold += 1
        train_start += step
    return windows


# ---------------------------------------------------------------------------
# GENERATE WINDOWS
# ---------------------------------------------------------------------------

def x_generate_windows__mutmut_28(
    n:          int,
    train_size: int,
    test_size:  int,
    step:       int,
) -> List[WalkForwardWindow]:
    """
    Generate deterministic rolling walk-forward windows.

    Args:
        n:          Total number of data points.
        train_size: Number of points in each training window.
        test_size:  Number of points in each test window.
        step:       Number of points to advance per fold.

    Returns:
        List of WalkForwardWindow. Empty list when no complete fold fits.

    Raises:
        ValueError if any argument < 1 or train_size + test_size > n.
    """
    if n < 1:
        raise ValueError(f"n must be >= 1; got {n}")
    if train_size < 1:
        raise ValueError(f"train_size must be >= 1; got {train_size}")
    if test_size < 1:
        raise ValueError(f"test_size must be >= 1; got {test_size}")
    if step < 1:
        raise ValueError(f"step must be >= 1; got {step}")

    windows: List[WalkForwardWindow] = []
    fold = 0
    train_start = 0
    while True:
        train_end = train_start + train_size
        test_start = train_end
        test_end = test_start + test_size
        if test_end > n:
            break
        windows.append(WalkForwardWindow(
            fold=fold,
            train_start=None,
            train_end=train_end,
            test_start=test_start,
            test_end=test_end,
        ))
        fold += 1
        train_start += step
    return windows


# ---------------------------------------------------------------------------
# GENERATE WINDOWS
# ---------------------------------------------------------------------------

def x_generate_windows__mutmut_29(
    n:          int,
    train_size: int,
    test_size:  int,
    step:       int,
) -> List[WalkForwardWindow]:
    """
    Generate deterministic rolling walk-forward windows.

    Args:
        n:          Total number of data points.
        train_size: Number of points in each training window.
        test_size:  Number of points in each test window.
        step:       Number of points to advance per fold.

    Returns:
        List of WalkForwardWindow. Empty list when no complete fold fits.

    Raises:
        ValueError if any argument < 1 or train_size + test_size > n.
    """
    if n < 1:
        raise ValueError(f"n must be >= 1; got {n}")
    if train_size < 1:
        raise ValueError(f"train_size must be >= 1; got {train_size}")
    if test_size < 1:
        raise ValueError(f"test_size must be >= 1; got {test_size}")
    if step < 1:
        raise ValueError(f"step must be >= 1; got {step}")

    windows: List[WalkForwardWindow] = []
    fold = 0
    train_start = 0
    while True:
        train_end = train_start + train_size
        test_start = train_end
        test_end = test_start + test_size
        if test_end > n:
            break
        windows.append(WalkForwardWindow(
            fold=fold,
            train_start=train_start,
            train_end=None,
            test_start=test_start,
            test_end=test_end,
        ))
        fold += 1
        train_start += step
    return windows


# ---------------------------------------------------------------------------
# GENERATE WINDOWS
# ---------------------------------------------------------------------------

def x_generate_windows__mutmut_30(
    n:          int,
    train_size: int,
    test_size:  int,
    step:       int,
) -> List[WalkForwardWindow]:
    """
    Generate deterministic rolling walk-forward windows.

    Args:
        n:          Total number of data points.
        train_size: Number of points in each training window.
        test_size:  Number of points in each test window.
        step:       Number of points to advance per fold.

    Returns:
        List of WalkForwardWindow. Empty list when no complete fold fits.

    Raises:
        ValueError if any argument < 1 or train_size + test_size > n.
    """
    if n < 1:
        raise ValueError(f"n must be >= 1; got {n}")
    if train_size < 1:
        raise ValueError(f"train_size must be >= 1; got {train_size}")
    if test_size < 1:
        raise ValueError(f"test_size must be >= 1; got {test_size}")
    if step < 1:
        raise ValueError(f"step must be >= 1; got {step}")

    windows: List[WalkForwardWindow] = []
    fold = 0
    train_start = 0
    while True:
        train_end = train_start + train_size
        test_start = train_end
        test_end = test_start + test_size
        if test_end > n:
            break
        windows.append(WalkForwardWindow(
            fold=fold,
            train_start=train_start,
            train_end=train_end,
            test_start=None,
            test_end=test_end,
        ))
        fold += 1
        train_start += step
    return windows


# ---------------------------------------------------------------------------
# GENERATE WINDOWS
# ---------------------------------------------------------------------------

def x_generate_windows__mutmut_31(
    n:          int,
    train_size: int,
    test_size:  int,
    step:       int,
) -> List[WalkForwardWindow]:
    """
    Generate deterministic rolling walk-forward windows.

    Args:
        n:          Total number of data points.
        train_size: Number of points in each training window.
        test_size:  Number of points in each test window.
        step:       Number of points to advance per fold.

    Returns:
        List of WalkForwardWindow. Empty list when no complete fold fits.

    Raises:
        ValueError if any argument < 1 or train_size + test_size > n.
    """
    if n < 1:
        raise ValueError(f"n must be >= 1; got {n}")
    if train_size < 1:
        raise ValueError(f"train_size must be >= 1; got {train_size}")
    if test_size < 1:
        raise ValueError(f"test_size must be >= 1; got {test_size}")
    if step < 1:
        raise ValueError(f"step must be >= 1; got {step}")

    windows: List[WalkForwardWindow] = []
    fold = 0
    train_start = 0
    while True:
        train_end = train_start + train_size
        test_start = train_end
        test_end = test_start + test_size
        if test_end > n:
            break
        windows.append(WalkForwardWindow(
            fold=fold,
            train_start=train_start,
            train_end=train_end,
            test_start=test_start,
            test_end=None,
        ))
        fold += 1
        train_start += step
    return windows


# ---------------------------------------------------------------------------
# GENERATE WINDOWS
# ---------------------------------------------------------------------------

def x_generate_windows__mutmut_32(
    n:          int,
    train_size: int,
    test_size:  int,
    step:       int,
) -> List[WalkForwardWindow]:
    """
    Generate deterministic rolling walk-forward windows.

    Args:
        n:          Total number of data points.
        train_size: Number of points in each training window.
        test_size:  Number of points in each test window.
        step:       Number of points to advance per fold.

    Returns:
        List of WalkForwardWindow. Empty list when no complete fold fits.

    Raises:
        ValueError if any argument < 1 or train_size + test_size > n.
    """
    if n < 1:
        raise ValueError(f"n must be >= 1; got {n}")
    if train_size < 1:
        raise ValueError(f"train_size must be >= 1; got {train_size}")
    if test_size < 1:
        raise ValueError(f"test_size must be >= 1; got {test_size}")
    if step < 1:
        raise ValueError(f"step must be >= 1; got {step}")

    windows: List[WalkForwardWindow] = []
    fold = 0
    train_start = 0
    while True:
        train_end = train_start + train_size
        test_start = train_end
        test_end = test_start + test_size
        if test_end > n:
            break
        windows.append(WalkForwardWindow(
            train_start=train_start,
            train_end=train_end,
            test_start=test_start,
            test_end=test_end,
        ))
        fold += 1
        train_start += step
    return windows


# ---------------------------------------------------------------------------
# GENERATE WINDOWS
# ---------------------------------------------------------------------------

def x_generate_windows__mutmut_33(
    n:          int,
    train_size: int,
    test_size:  int,
    step:       int,
) -> List[WalkForwardWindow]:
    """
    Generate deterministic rolling walk-forward windows.

    Args:
        n:          Total number of data points.
        train_size: Number of points in each training window.
        test_size:  Number of points in each test window.
        step:       Number of points to advance per fold.

    Returns:
        List of WalkForwardWindow. Empty list when no complete fold fits.

    Raises:
        ValueError if any argument < 1 or train_size + test_size > n.
    """
    if n < 1:
        raise ValueError(f"n must be >= 1; got {n}")
    if train_size < 1:
        raise ValueError(f"train_size must be >= 1; got {train_size}")
    if test_size < 1:
        raise ValueError(f"test_size must be >= 1; got {test_size}")
    if step < 1:
        raise ValueError(f"step must be >= 1; got {step}")

    windows: List[WalkForwardWindow] = []
    fold = 0
    train_start = 0
    while True:
        train_end = train_start + train_size
        test_start = train_end
        test_end = test_start + test_size
        if test_end > n:
            break
        windows.append(WalkForwardWindow(
            fold=fold,
            train_end=train_end,
            test_start=test_start,
            test_end=test_end,
        ))
        fold += 1
        train_start += step
    return windows


# ---------------------------------------------------------------------------
# GENERATE WINDOWS
# ---------------------------------------------------------------------------

def x_generate_windows__mutmut_34(
    n:          int,
    train_size: int,
    test_size:  int,
    step:       int,
) -> List[WalkForwardWindow]:
    """
    Generate deterministic rolling walk-forward windows.

    Args:
        n:          Total number of data points.
        train_size: Number of points in each training window.
        test_size:  Number of points in each test window.
        step:       Number of points to advance per fold.

    Returns:
        List of WalkForwardWindow. Empty list when no complete fold fits.

    Raises:
        ValueError if any argument < 1 or train_size + test_size > n.
    """
    if n < 1:
        raise ValueError(f"n must be >= 1; got {n}")
    if train_size < 1:
        raise ValueError(f"train_size must be >= 1; got {train_size}")
    if test_size < 1:
        raise ValueError(f"test_size must be >= 1; got {test_size}")
    if step < 1:
        raise ValueError(f"step must be >= 1; got {step}")

    windows: List[WalkForwardWindow] = []
    fold = 0
    train_start = 0
    while True:
        train_end = train_start + train_size
        test_start = train_end
        test_end = test_start + test_size
        if test_end > n:
            break
        windows.append(WalkForwardWindow(
            fold=fold,
            train_start=train_start,
            test_start=test_start,
            test_end=test_end,
        ))
        fold += 1
        train_start += step
    return windows


# ---------------------------------------------------------------------------
# GENERATE WINDOWS
# ---------------------------------------------------------------------------

def x_generate_windows__mutmut_35(
    n:          int,
    train_size: int,
    test_size:  int,
    step:       int,
) -> List[WalkForwardWindow]:
    """
    Generate deterministic rolling walk-forward windows.

    Args:
        n:          Total number of data points.
        train_size: Number of points in each training window.
        test_size:  Number of points in each test window.
        step:       Number of points to advance per fold.

    Returns:
        List of WalkForwardWindow. Empty list when no complete fold fits.

    Raises:
        ValueError if any argument < 1 or train_size + test_size > n.
    """
    if n < 1:
        raise ValueError(f"n must be >= 1; got {n}")
    if train_size < 1:
        raise ValueError(f"train_size must be >= 1; got {train_size}")
    if test_size < 1:
        raise ValueError(f"test_size must be >= 1; got {test_size}")
    if step < 1:
        raise ValueError(f"step must be >= 1; got {step}")

    windows: List[WalkForwardWindow] = []
    fold = 0
    train_start = 0
    while True:
        train_end = train_start + train_size
        test_start = train_end
        test_end = test_start + test_size
        if test_end > n:
            break
        windows.append(WalkForwardWindow(
            fold=fold,
            train_start=train_start,
            train_end=train_end,
            test_end=test_end,
        ))
        fold += 1
        train_start += step
    return windows


# ---------------------------------------------------------------------------
# GENERATE WINDOWS
# ---------------------------------------------------------------------------

def x_generate_windows__mutmut_36(
    n:          int,
    train_size: int,
    test_size:  int,
    step:       int,
) -> List[WalkForwardWindow]:
    """
    Generate deterministic rolling walk-forward windows.

    Args:
        n:          Total number of data points.
        train_size: Number of points in each training window.
        test_size:  Number of points in each test window.
        step:       Number of points to advance per fold.

    Returns:
        List of WalkForwardWindow. Empty list when no complete fold fits.

    Raises:
        ValueError if any argument < 1 or train_size + test_size > n.
    """
    if n < 1:
        raise ValueError(f"n must be >= 1; got {n}")
    if train_size < 1:
        raise ValueError(f"train_size must be >= 1; got {train_size}")
    if test_size < 1:
        raise ValueError(f"test_size must be >= 1; got {test_size}")
    if step < 1:
        raise ValueError(f"step must be >= 1; got {step}")

    windows: List[WalkForwardWindow] = []
    fold = 0
    train_start = 0
    while True:
        train_end = train_start + train_size
        test_start = train_end
        test_end = test_start + test_size
        if test_end > n:
            break
        windows.append(WalkForwardWindow(
            fold=fold,
            train_start=train_start,
            train_end=train_end,
            test_start=test_start,
            ))
        fold += 1
        train_start += step
    return windows


# ---------------------------------------------------------------------------
# GENERATE WINDOWS
# ---------------------------------------------------------------------------

def x_generate_windows__mutmut_37(
    n:          int,
    train_size: int,
    test_size:  int,
    step:       int,
) -> List[WalkForwardWindow]:
    """
    Generate deterministic rolling walk-forward windows.

    Args:
        n:          Total number of data points.
        train_size: Number of points in each training window.
        test_size:  Number of points in each test window.
        step:       Number of points to advance per fold.

    Returns:
        List of WalkForwardWindow. Empty list when no complete fold fits.

    Raises:
        ValueError if any argument < 1 or train_size + test_size > n.
    """
    if n < 1:
        raise ValueError(f"n must be >= 1; got {n}")
    if train_size < 1:
        raise ValueError(f"train_size must be >= 1; got {train_size}")
    if test_size < 1:
        raise ValueError(f"test_size must be >= 1; got {test_size}")
    if step < 1:
        raise ValueError(f"step must be >= 1; got {step}")

    windows: List[WalkForwardWindow] = []
    fold = 0
    train_start = 0
    while True:
        train_end = train_start + train_size
        test_start = train_end
        test_end = test_start + test_size
        if test_end > n:
            break
        windows.append(WalkForwardWindow(
            fold=fold,
            train_start=train_start,
            train_end=train_end,
            test_start=test_start,
            test_end=test_end,
        ))
        fold = 1
        train_start += step
    return windows


# ---------------------------------------------------------------------------
# GENERATE WINDOWS
# ---------------------------------------------------------------------------

def x_generate_windows__mutmut_38(
    n:          int,
    train_size: int,
    test_size:  int,
    step:       int,
) -> List[WalkForwardWindow]:
    """
    Generate deterministic rolling walk-forward windows.

    Args:
        n:          Total number of data points.
        train_size: Number of points in each training window.
        test_size:  Number of points in each test window.
        step:       Number of points to advance per fold.

    Returns:
        List of WalkForwardWindow. Empty list when no complete fold fits.

    Raises:
        ValueError if any argument < 1 or train_size + test_size > n.
    """
    if n < 1:
        raise ValueError(f"n must be >= 1; got {n}")
    if train_size < 1:
        raise ValueError(f"train_size must be >= 1; got {train_size}")
    if test_size < 1:
        raise ValueError(f"test_size must be >= 1; got {test_size}")
    if step < 1:
        raise ValueError(f"step must be >= 1; got {step}")

    windows: List[WalkForwardWindow] = []
    fold = 0
    train_start = 0
    while True:
        train_end = train_start + train_size
        test_start = train_end
        test_end = test_start + test_size
        if test_end > n:
            break
        windows.append(WalkForwardWindow(
            fold=fold,
            train_start=train_start,
            train_end=train_end,
            test_start=test_start,
            test_end=test_end,
        ))
        fold -= 1
        train_start += step
    return windows


# ---------------------------------------------------------------------------
# GENERATE WINDOWS
# ---------------------------------------------------------------------------

def x_generate_windows__mutmut_39(
    n:          int,
    train_size: int,
    test_size:  int,
    step:       int,
) -> List[WalkForwardWindow]:
    """
    Generate deterministic rolling walk-forward windows.

    Args:
        n:          Total number of data points.
        train_size: Number of points in each training window.
        test_size:  Number of points in each test window.
        step:       Number of points to advance per fold.

    Returns:
        List of WalkForwardWindow. Empty list when no complete fold fits.

    Raises:
        ValueError if any argument < 1 or train_size + test_size > n.
    """
    if n < 1:
        raise ValueError(f"n must be >= 1; got {n}")
    if train_size < 1:
        raise ValueError(f"train_size must be >= 1; got {train_size}")
    if test_size < 1:
        raise ValueError(f"test_size must be >= 1; got {test_size}")
    if step < 1:
        raise ValueError(f"step must be >= 1; got {step}")

    windows: List[WalkForwardWindow] = []
    fold = 0
    train_start = 0
    while True:
        train_end = train_start + train_size
        test_start = train_end
        test_end = test_start + test_size
        if test_end > n:
            break
        windows.append(WalkForwardWindow(
            fold=fold,
            train_start=train_start,
            train_end=train_end,
            test_start=test_start,
            test_end=test_end,
        ))
        fold += 2
        train_start += step
    return windows


# ---------------------------------------------------------------------------
# GENERATE WINDOWS
# ---------------------------------------------------------------------------

def x_generate_windows__mutmut_40(
    n:          int,
    train_size: int,
    test_size:  int,
    step:       int,
) -> List[WalkForwardWindow]:
    """
    Generate deterministic rolling walk-forward windows.

    Args:
        n:          Total number of data points.
        train_size: Number of points in each training window.
        test_size:  Number of points in each test window.
        step:       Number of points to advance per fold.

    Returns:
        List of WalkForwardWindow. Empty list when no complete fold fits.

    Raises:
        ValueError if any argument < 1 or train_size + test_size > n.
    """
    if n < 1:
        raise ValueError(f"n must be >= 1; got {n}")
    if train_size < 1:
        raise ValueError(f"train_size must be >= 1; got {train_size}")
    if test_size < 1:
        raise ValueError(f"test_size must be >= 1; got {test_size}")
    if step < 1:
        raise ValueError(f"step must be >= 1; got {step}")

    windows: List[WalkForwardWindow] = []
    fold = 0
    train_start = 0
    while True:
        train_end = train_start + train_size
        test_start = train_end
        test_end = test_start + test_size
        if test_end > n:
            break
        windows.append(WalkForwardWindow(
            fold=fold,
            train_start=train_start,
            train_end=train_end,
            test_start=test_start,
            test_end=test_end,
        ))
        fold += 1
        train_start = step
    return windows


# ---------------------------------------------------------------------------
# GENERATE WINDOWS
# ---------------------------------------------------------------------------

def x_generate_windows__mutmut_41(
    n:          int,
    train_size: int,
    test_size:  int,
    step:       int,
) -> List[WalkForwardWindow]:
    """
    Generate deterministic rolling walk-forward windows.

    Args:
        n:          Total number of data points.
        train_size: Number of points in each training window.
        test_size:  Number of points in each test window.
        step:       Number of points to advance per fold.

    Returns:
        List of WalkForwardWindow. Empty list when no complete fold fits.

    Raises:
        ValueError if any argument < 1 or train_size + test_size > n.
    """
    if n < 1:
        raise ValueError(f"n must be >= 1; got {n}")
    if train_size < 1:
        raise ValueError(f"train_size must be >= 1; got {train_size}")
    if test_size < 1:
        raise ValueError(f"test_size must be >= 1; got {test_size}")
    if step < 1:
        raise ValueError(f"step must be >= 1; got {step}")

    windows: List[WalkForwardWindow] = []
    fold = 0
    train_start = 0
    while True:
        train_end = train_start + train_size
        test_start = train_end
        test_end = test_start + test_size
        if test_end > n:
            break
        windows.append(WalkForwardWindow(
            fold=fold,
            train_start=train_start,
            train_end=train_end,
            test_start=test_start,
            test_end=test_end,
        ))
        fold += 1
        train_start -= step
    return windows

x_generate_windows__mutmut_mutants : ClassVar[MutantDict] = { # type: ignore
'x_generate_windows__mutmut_1': x_generate_windows__mutmut_1, 
    'x_generate_windows__mutmut_2': x_generate_windows__mutmut_2, 
    'x_generate_windows__mutmut_3': x_generate_windows__mutmut_3, 
    'x_generate_windows__mutmut_4': x_generate_windows__mutmut_4, 
    'x_generate_windows__mutmut_5': x_generate_windows__mutmut_5, 
    'x_generate_windows__mutmut_6': x_generate_windows__mutmut_6, 
    'x_generate_windows__mutmut_7': x_generate_windows__mutmut_7, 
    'x_generate_windows__mutmut_8': x_generate_windows__mutmut_8, 
    'x_generate_windows__mutmut_9': x_generate_windows__mutmut_9, 
    'x_generate_windows__mutmut_10': x_generate_windows__mutmut_10, 
    'x_generate_windows__mutmut_11': x_generate_windows__mutmut_11, 
    'x_generate_windows__mutmut_12': x_generate_windows__mutmut_12, 
    'x_generate_windows__mutmut_13': x_generate_windows__mutmut_13, 
    'x_generate_windows__mutmut_14': x_generate_windows__mutmut_14, 
    'x_generate_windows__mutmut_15': x_generate_windows__mutmut_15, 
    'x_generate_windows__mutmut_16': x_generate_windows__mutmut_16, 
    'x_generate_windows__mutmut_17': x_generate_windows__mutmut_17, 
    'x_generate_windows__mutmut_18': x_generate_windows__mutmut_18, 
    'x_generate_windows__mutmut_19': x_generate_windows__mutmut_19, 
    'x_generate_windows__mutmut_20': x_generate_windows__mutmut_20, 
    'x_generate_windows__mutmut_21': x_generate_windows__mutmut_21, 
    'x_generate_windows__mutmut_22': x_generate_windows__mutmut_22, 
    'x_generate_windows__mutmut_23': x_generate_windows__mutmut_23, 
    'x_generate_windows__mutmut_24': x_generate_windows__mutmut_24, 
    'x_generate_windows__mutmut_25': x_generate_windows__mutmut_25, 
    'x_generate_windows__mutmut_26': x_generate_windows__mutmut_26, 
    'x_generate_windows__mutmut_27': x_generate_windows__mutmut_27, 
    'x_generate_windows__mutmut_28': x_generate_windows__mutmut_28, 
    'x_generate_windows__mutmut_29': x_generate_windows__mutmut_29, 
    'x_generate_windows__mutmut_30': x_generate_windows__mutmut_30, 
    'x_generate_windows__mutmut_31': x_generate_windows__mutmut_31, 
    'x_generate_windows__mutmut_32': x_generate_windows__mutmut_32, 
    'x_generate_windows__mutmut_33': x_generate_windows__mutmut_33, 
    'x_generate_windows__mutmut_34': x_generate_windows__mutmut_34, 
    'x_generate_windows__mutmut_35': x_generate_windows__mutmut_35, 
    'x_generate_windows__mutmut_36': x_generate_windows__mutmut_36, 
    'x_generate_windows__mutmut_37': x_generate_windows__mutmut_37, 
    'x_generate_windows__mutmut_38': x_generate_windows__mutmut_38, 
    'x_generate_windows__mutmut_39': x_generate_windows__mutmut_39, 
    'x_generate_windows__mutmut_40': x_generate_windows__mutmut_40, 
    'x_generate_windows__mutmut_41': x_generate_windows__mutmut_41
}
x_generate_windows__mutmut_orig.__name__ = 'x_generate_windows'


# ---------------------------------------------------------------------------
# RUN WALK-FORWARD
# ---------------------------------------------------------------------------

def run_walkforward(
    data:        Sequence[Any],
    train_size:  int,
    test_size:   int,
    step:        int,
    evaluate_fn: Callable[[Sequence[Any], Sequence[Any]], Dict[str, Any]],
) -> List[Dict[str, Any]]:
    args = [data, train_size, test_size, step, evaluate_fn]# type: ignore
    kwargs = {}# type: ignore
    return _mutmut_trampoline(x_run_walkforward__mutmut_orig, x_run_walkforward__mutmut_mutants, args, kwargs, None)


# ---------------------------------------------------------------------------
# RUN WALK-FORWARD
# ---------------------------------------------------------------------------

def x_run_walkforward__mutmut_orig(
    data:        Sequence[Any],
    train_size:  int,
    test_size:   int,
    step:        int,
    evaluate_fn: Callable[[Sequence[Any], Sequence[Any]], Dict[str, Any]],
) -> List[Dict[str, Any]]:
    """
    Run deterministic walk-forward validation.

    For each window generated by generate_windows():
        train_slice = data[window.train_start : window.train_end]
        test_slice  = data[window.test_start  : window.test_end]
        result      = evaluate_fn(train_slice, test_slice)

    evaluate_fn must be a pure, deterministic function. Its signature:
        evaluate_fn(train: Sequence[Any], test: Sequence[Any]) -> Dict[str, Any]

    Args:
        data:        Full dataset as a sequence.
        train_size:  Training window size.
        test_size:   Test window size.
        step:        Step size per fold.
        evaluate_fn: Caller-supplied deterministic evaluation function.

    Returns:
        List of dicts, one per fold, each containing:
            'fold':   fold index (int)
            'window': WalkForwardWindow
            **result: all keys from evaluate_fn's return dict
    """
    windows = generate_windows(len(data), train_size, test_size, step)
    results: List[Dict[str, Any]] = []
    for window in windows:
        train_slice = data[window.train_start : window.train_end]
        test_slice  = data[window.test_start  : window.test_end]
        fold_result = evaluate_fn(train_slice, test_slice)
        entry: Dict[str, Any] = {
            "fold":   window.fold,
            "window": window,
        }
        entry.update(fold_result)
        results.append(entry)
    return results


# ---------------------------------------------------------------------------
# RUN WALK-FORWARD
# ---------------------------------------------------------------------------

def x_run_walkforward__mutmut_1(
    data:        Sequence[Any],
    train_size:  int,
    test_size:   int,
    step:        int,
    evaluate_fn: Callable[[Sequence[Any], Sequence[Any]], Dict[str, Any]],
) -> List[Dict[str, Any]]:
    """
    Run deterministic walk-forward validation.

    For each window generated by generate_windows():
        train_slice = data[window.train_start : window.train_end]
        test_slice  = data[window.test_start  : window.test_end]
        result      = evaluate_fn(train_slice, test_slice)

    evaluate_fn must be a pure, deterministic function. Its signature:
        evaluate_fn(train: Sequence[Any], test: Sequence[Any]) -> Dict[str, Any]

    Args:
        data:        Full dataset as a sequence.
        train_size:  Training window size.
        test_size:   Test window size.
        step:        Step size per fold.
        evaluate_fn: Caller-supplied deterministic evaluation function.

    Returns:
        List of dicts, one per fold, each containing:
            'fold':   fold index (int)
            'window': WalkForwardWindow
            **result: all keys from evaluate_fn's return dict
    """
    windows = None
    results: List[Dict[str, Any]] = []
    for window in windows:
        train_slice = data[window.train_start : window.train_end]
        test_slice  = data[window.test_start  : window.test_end]
        fold_result = evaluate_fn(train_slice, test_slice)
        entry: Dict[str, Any] = {
            "fold":   window.fold,
            "window": window,
        }
        entry.update(fold_result)
        results.append(entry)
    return results


# ---------------------------------------------------------------------------
# RUN WALK-FORWARD
# ---------------------------------------------------------------------------

def x_run_walkforward__mutmut_2(
    data:        Sequence[Any],
    train_size:  int,
    test_size:   int,
    step:        int,
    evaluate_fn: Callable[[Sequence[Any], Sequence[Any]], Dict[str, Any]],
) -> List[Dict[str, Any]]:
    """
    Run deterministic walk-forward validation.

    For each window generated by generate_windows():
        train_slice = data[window.train_start : window.train_end]
        test_slice  = data[window.test_start  : window.test_end]
        result      = evaluate_fn(train_slice, test_slice)

    evaluate_fn must be a pure, deterministic function. Its signature:
        evaluate_fn(train: Sequence[Any], test: Sequence[Any]) -> Dict[str, Any]

    Args:
        data:        Full dataset as a sequence.
        train_size:  Training window size.
        test_size:   Test window size.
        step:        Step size per fold.
        evaluate_fn: Caller-supplied deterministic evaluation function.

    Returns:
        List of dicts, one per fold, each containing:
            'fold':   fold index (int)
            'window': WalkForwardWindow
            **result: all keys from evaluate_fn's return dict
    """
    windows = generate_windows(None, train_size, test_size, step)
    results: List[Dict[str, Any]] = []
    for window in windows:
        train_slice = data[window.train_start : window.train_end]
        test_slice  = data[window.test_start  : window.test_end]
        fold_result = evaluate_fn(train_slice, test_slice)
        entry: Dict[str, Any] = {
            "fold":   window.fold,
            "window": window,
        }
        entry.update(fold_result)
        results.append(entry)
    return results


# ---------------------------------------------------------------------------
# RUN WALK-FORWARD
# ---------------------------------------------------------------------------

def x_run_walkforward__mutmut_3(
    data:        Sequence[Any],
    train_size:  int,
    test_size:   int,
    step:        int,
    evaluate_fn: Callable[[Sequence[Any], Sequence[Any]], Dict[str, Any]],
) -> List[Dict[str, Any]]:
    """
    Run deterministic walk-forward validation.

    For each window generated by generate_windows():
        train_slice = data[window.train_start : window.train_end]
        test_slice  = data[window.test_start  : window.test_end]
        result      = evaluate_fn(train_slice, test_slice)

    evaluate_fn must be a pure, deterministic function. Its signature:
        evaluate_fn(train: Sequence[Any], test: Sequence[Any]) -> Dict[str, Any]

    Args:
        data:        Full dataset as a sequence.
        train_size:  Training window size.
        test_size:   Test window size.
        step:        Step size per fold.
        evaluate_fn: Caller-supplied deterministic evaluation function.

    Returns:
        List of dicts, one per fold, each containing:
            'fold':   fold index (int)
            'window': WalkForwardWindow
            **result: all keys from evaluate_fn's return dict
    """
    windows = generate_windows(len(data), None, test_size, step)
    results: List[Dict[str, Any]] = []
    for window in windows:
        train_slice = data[window.train_start : window.train_end]
        test_slice  = data[window.test_start  : window.test_end]
        fold_result = evaluate_fn(train_slice, test_slice)
        entry: Dict[str, Any] = {
            "fold":   window.fold,
            "window": window,
        }
        entry.update(fold_result)
        results.append(entry)
    return results


# ---------------------------------------------------------------------------
# RUN WALK-FORWARD
# ---------------------------------------------------------------------------

def x_run_walkforward__mutmut_4(
    data:        Sequence[Any],
    train_size:  int,
    test_size:   int,
    step:        int,
    evaluate_fn: Callable[[Sequence[Any], Sequence[Any]], Dict[str, Any]],
) -> List[Dict[str, Any]]:
    """
    Run deterministic walk-forward validation.

    For each window generated by generate_windows():
        train_slice = data[window.train_start : window.train_end]
        test_slice  = data[window.test_start  : window.test_end]
        result      = evaluate_fn(train_slice, test_slice)

    evaluate_fn must be a pure, deterministic function. Its signature:
        evaluate_fn(train: Sequence[Any], test: Sequence[Any]) -> Dict[str, Any]

    Args:
        data:        Full dataset as a sequence.
        train_size:  Training window size.
        test_size:   Test window size.
        step:        Step size per fold.
        evaluate_fn: Caller-supplied deterministic evaluation function.

    Returns:
        List of dicts, one per fold, each containing:
            'fold':   fold index (int)
            'window': WalkForwardWindow
            **result: all keys from evaluate_fn's return dict
    """
    windows = generate_windows(len(data), train_size, None, step)
    results: List[Dict[str, Any]] = []
    for window in windows:
        train_slice = data[window.train_start : window.train_end]
        test_slice  = data[window.test_start  : window.test_end]
        fold_result = evaluate_fn(train_slice, test_slice)
        entry: Dict[str, Any] = {
            "fold":   window.fold,
            "window": window,
        }
        entry.update(fold_result)
        results.append(entry)
    return results


# ---------------------------------------------------------------------------
# RUN WALK-FORWARD
# ---------------------------------------------------------------------------

def x_run_walkforward__mutmut_5(
    data:        Sequence[Any],
    train_size:  int,
    test_size:   int,
    step:        int,
    evaluate_fn: Callable[[Sequence[Any], Sequence[Any]], Dict[str, Any]],
) -> List[Dict[str, Any]]:
    """
    Run deterministic walk-forward validation.

    For each window generated by generate_windows():
        train_slice = data[window.train_start : window.train_end]
        test_slice  = data[window.test_start  : window.test_end]
        result      = evaluate_fn(train_slice, test_slice)

    evaluate_fn must be a pure, deterministic function. Its signature:
        evaluate_fn(train: Sequence[Any], test: Sequence[Any]) -> Dict[str, Any]

    Args:
        data:        Full dataset as a sequence.
        train_size:  Training window size.
        test_size:   Test window size.
        step:        Step size per fold.
        evaluate_fn: Caller-supplied deterministic evaluation function.

    Returns:
        List of dicts, one per fold, each containing:
            'fold':   fold index (int)
            'window': WalkForwardWindow
            **result: all keys from evaluate_fn's return dict
    """
    windows = generate_windows(len(data), train_size, test_size, None)
    results: List[Dict[str, Any]] = []
    for window in windows:
        train_slice = data[window.train_start : window.train_end]
        test_slice  = data[window.test_start  : window.test_end]
        fold_result = evaluate_fn(train_slice, test_slice)
        entry: Dict[str, Any] = {
            "fold":   window.fold,
            "window": window,
        }
        entry.update(fold_result)
        results.append(entry)
    return results


# ---------------------------------------------------------------------------
# RUN WALK-FORWARD
# ---------------------------------------------------------------------------

def x_run_walkforward__mutmut_6(
    data:        Sequence[Any],
    train_size:  int,
    test_size:   int,
    step:        int,
    evaluate_fn: Callable[[Sequence[Any], Sequence[Any]], Dict[str, Any]],
) -> List[Dict[str, Any]]:
    """
    Run deterministic walk-forward validation.

    For each window generated by generate_windows():
        train_slice = data[window.train_start : window.train_end]
        test_slice  = data[window.test_start  : window.test_end]
        result      = evaluate_fn(train_slice, test_slice)

    evaluate_fn must be a pure, deterministic function. Its signature:
        evaluate_fn(train: Sequence[Any], test: Sequence[Any]) -> Dict[str, Any]

    Args:
        data:        Full dataset as a sequence.
        train_size:  Training window size.
        test_size:   Test window size.
        step:        Step size per fold.
        evaluate_fn: Caller-supplied deterministic evaluation function.

    Returns:
        List of dicts, one per fold, each containing:
            'fold':   fold index (int)
            'window': WalkForwardWindow
            **result: all keys from evaluate_fn's return dict
    """
    windows = generate_windows(train_size, test_size, step)
    results: List[Dict[str, Any]] = []
    for window in windows:
        train_slice = data[window.train_start : window.train_end]
        test_slice  = data[window.test_start  : window.test_end]
        fold_result = evaluate_fn(train_slice, test_slice)
        entry: Dict[str, Any] = {
            "fold":   window.fold,
            "window": window,
        }
        entry.update(fold_result)
        results.append(entry)
    return results


# ---------------------------------------------------------------------------
# RUN WALK-FORWARD
# ---------------------------------------------------------------------------

def x_run_walkforward__mutmut_7(
    data:        Sequence[Any],
    train_size:  int,
    test_size:   int,
    step:        int,
    evaluate_fn: Callable[[Sequence[Any], Sequence[Any]], Dict[str, Any]],
) -> List[Dict[str, Any]]:
    """
    Run deterministic walk-forward validation.

    For each window generated by generate_windows():
        train_slice = data[window.train_start : window.train_end]
        test_slice  = data[window.test_start  : window.test_end]
        result      = evaluate_fn(train_slice, test_slice)

    evaluate_fn must be a pure, deterministic function. Its signature:
        evaluate_fn(train: Sequence[Any], test: Sequence[Any]) -> Dict[str, Any]

    Args:
        data:        Full dataset as a sequence.
        train_size:  Training window size.
        test_size:   Test window size.
        step:        Step size per fold.
        evaluate_fn: Caller-supplied deterministic evaluation function.

    Returns:
        List of dicts, one per fold, each containing:
            'fold':   fold index (int)
            'window': WalkForwardWindow
            **result: all keys from evaluate_fn's return dict
    """
    windows = generate_windows(len(data), test_size, step)
    results: List[Dict[str, Any]] = []
    for window in windows:
        train_slice = data[window.train_start : window.train_end]
        test_slice  = data[window.test_start  : window.test_end]
        fold_result = evaluate_fn(train_slice, test_slice)
        entry: Dict[str, Any] = {
            "fold":   window.fold,
            "window": window,
        }
        entry.update(fold_result)
        results.append(entry)
    return results


# ---------------------------------------------------------------------------
# RUN WALK-FORWARD
# ---------------------------------------------------------------------------

def x_run_walkforward__mutmut_8(
    data:        Sequence[Any],
    train_size:  int,
    test_size:   int,
    step:        int,
    evaluate_fn: Callable[[Sequence[Any], Sequence[Any]], Dict[str, Any]],
) -> List[Dict[str, Any]]:
    """
    Run deterministic walk-forward validation.

    For each window generated by generate_windows():
        train_slice = data[window.train_start : window.train_end]
        test_slice  = data[window.test_start  : window.test_end]
        result      = evaluate_fn(train_slice, test_slice)

    evaluate_fn must be a pure, deterministic function. Its signature:
        evaluate_fn(train: Sequence[Any], test: Sequence[Any]) -> Dict[str, Any]

    Args:
        data:        Full dataset as a sequence.
        train_size:  Training window size.
        test_size:   Test window size.
        step:        Step size per fold.
        evaluate_fn: Caller-supplied deterministic evaluation function.

    Returns:
        List of dicts, one per fold, each containing:
            'fold':   fold index (int)
            'window': WalkForwardWindow
            **result: all keys from evaluate_fn's return dict
    """
    windows = generate_windows(len(data), train_size, step)
    results: List[Dict[str, Any]] = []
    for window in windows:
        train_slice = data[window.train_start : window.train_end]
        test_slice  = data[window.test_start  : window.test_end]
        fold_result = evaluate_fn(train_slice, test_slice)
        entry: Dict[str, Any] = {
            "fold":   window.fold,
            "window": window,
        }
        entry.update(fold_result)
        results.append(entry)
    return results


# ---------------------------------------------------------------------------
# RUN WALK-FORWARD
# ---------------------------------------------------------------------------

def x_run_walkforward__mutmut_9(
    data:        Sequence[Any],
    train_size:  int,
    test_size:   int,
    step:        int,
    evaluate_fn: Callable[[Sequence[Any], Sequence[Any]], Dict[str, Any]],
) -> List[Dict[str, Any]]:
    """
    Run deterministic walk-forward validation.

    For each window generated by generate_windows():
        train_slice = data[window.train_start : window.train_end]
        test_slice  = data[window.test_start  : window.test_end]
        result      = evaluate_fn(train_slice, test_slice)

    evaluate_fn must be a pure, deterministic function. Its signature:
        evaluate_fn(train: Sequence[Any], test: Sequence[Any]) -> Dict[str, Any]

    Args:
        data:        Full dataset as a sequence.
        train_size:  Training window size.
        test_size:   Test window size.
        step:        Step size per fold.
        evaluate_fn: Caller-supplied deterministic evaluation function.

    Returns:
        List of dicts, one per fold, each containing:
            'fold':   fold index (int)
            'window': WalkForwardWindow
            **result: all keys from evaluate_fn's return dict
    """
    windows = generate_windows(len(data), train_size, test_size, )
    results: List[Dict[str, Any]] = []
    for window in windows:
        train_slice = data[window.train_start : window.train_end]
        test_slice  = data[window.test_start  : window.test_end]
        fold_result = evaluate_fn(train_slice, test_slice)
        entry: Dict[str, Any] = {
            "fold":   window.fold,
            "window": window,
        }
        entry.update(fold_result)
        results.append(entry)
    return results


# ---------------------------------------------------------------------------
# RUN WALK-FORWARD
# ---------------------------------------------------------------------------

def x_run_walkforward__mutmut_10(
    data:        Sequence[Any],
    train_size:  int,
    test_size:   int,
    step:        int,
    evaluate_fn: Callable[[Sequence[Any], Sequence[Any]], Dict[str, Any]],
) -> List[Dict[str, Any]]:
    """
    Run deterministic walk-forward validation.

    For each window generated by generate_windows():
        train_slice = data[window.train_start : window.train_end]
        test_slice  = data[window.test_start  : window.test_end]
        result      = evaluate_fn(train_slice, test_slice)

    evaluate_fn must be a pure, deterministic function. Its signature:
        evaluate_fn(train: Sequence[Any], test: Sequence[Any]) -> Dict[str, Any]

    Args:
        data:        Full dataset as a sequence.
        train_size:  Training window size.
        test_size:   Test window size.
        step:        Step size per fold.
        evaluate_fn: Caller-supplied deterministic evaluation function.

    Returns:
        List of dicts, one per fold, each containing:
            'fold':   fold index (int)
            'window': WalkForwardWindow
            **result: all keys from evaluate_fn's return dict
    """
    windows = generate_windows(len(data), train_size, test_size, step)
    results: List[Dict[str, Any]] = None
    for window in windows:
        train_slice = data[window.train_start : window.train_end]
        test_slice  = data[window.test_start  : window.test_end]
        fold_result = evaluate_fn(train_slice, test_slice)
        entry: Dict[str, Any] = {
            "fold":   window.fold,
            "window": window,
        }
        entry.update(fold_result)
        results.append(entry)
    return results


# ---------------------------------------------------------------------------
# RUN WALK-FORWARD
# ---------------------------------------------------------------------------

def x_run_walkforward__mutmut_11(
    data:        Sequence[Any],
    train_size:  int,
    test_size:   int,
    step:        int,
    evaluate_fn: Callable[[Sequence[Any], Sequence[Any]], Dict[str, Any]],
) -> List[Dict[str, Any]]:
    """
    Run deterministic walk-forward validation.

    For each window generated by generate_windows():
        train_slice = data[window.train_start : window.train_end]
        test_slice  = data[window.test_start  : window.test_end]
        result      = evaluate_fn(train_slice, test_slice)

    evaluate_fn must be a pure, deterministic function. Its signature:
        evaluate_fn(train: Sequence[Any], test: Sequence[Any]) -> Dict[str, Any]

    Args:
        data:        Full dataset as a sequence.
        train_size:  Training window size.
        test_size:   Test window size.
        step:        Step size per fold.
        evaluate_fn: Caller-supplied deterministic evaluation function.

    Returns:
        List of dicts, one per fold, each containing:
            'fold':   fold index (int)
            'window': WalkForwardWindow
            **result: all keys from evaluate_fn's return dict
    """
    windows = generate_windows(len(data), train_size, test_size, step)
    results: List[Dict[str, Any]] = []
    for window in windows:
        train_slice = None
        test_slice  = data[window.test_start  : window.test_end]
        fold_result = evaluate_fn(train_slice, test_slice)
        entry: Dict[str, Any] = {
            "fold":   window.fold,
            "window": window,
        }
        entry.update(fold_result)
        results.append(entry)
    return results


# ---------------------------------------------------------------------------
# RUN WALK-FORWARD
# ---------------------------------------------------------------------------

def x_run_walkforward__mutmut_12(
    data:        Sequence[Any],
    train_size:  int,
    test_size:   int,
    step:        int,
    evaluate_fn: Callable[[Sequence[Any], Sequence[Any]], Dict[str, Any]],
) -> List[Dict[str, Any]]:
    """
    Run deterministic walk-forward validation.

    For each window generated by generate_windows():
        train_slice = data[window.train_start : window.train_end]
        test_slice  = data[window.test_start  : window.test_end]
        result      = evaluate_fn(train_slice, test_slice)

    evaluate_fn must be a pure, deterministic function. Its signature:
        evaluate_fn(train: Sequence[Any], test: Sequence[Any]) -> Dict[str, Any]

    Args:
        data:        Full dataset as a sequence.
        train_size:  Training window size.
        test_size:   Test window size.
        step:        Step size per fold.
        evaluate_fn: Caller-supplied deterministic evaluation function.

    Returns:
        List of dicts, one per fold, each containing:
            'fold':   fold index (int)
            'window': WalkForwardWindow
            **result: all keys from evaluate_fn's return dict
    """
    windows = generate_windows(len(data), train_size, test_size, step)
    results: List[Dict[str, Any]] = []
    for window in windows:
        train_slice = data[window.train_start : window.train_end]
        test_slice  = None
        fold_result = evaluate_fn(train_slice, test_slice)
        entry: Dict[str, Any] = {
            "fold":   window.fold,
            "window": window,
        }
        entry.update(fold_result)
        results.append(entry)
    return results


# ---------------------------------------------------------------------------
# RUN WALK-FORWARD
# ---------------------------------------------------------------------------

def x_run_walkforward__mutmut_13(
    data:        Sequence[Any],
    train_size:  int,
    test_size:   int,
    step:        int,
    evaluate_fn: Callable[[Sequence[Any], Sequence[Any]], Dict[str, Any]],
) -> List[Dict[str, Any]]:
    """
    Run deterministic walk-forward validation.

    For each window generated by generate_windows():
        train_slice = data[window.train_start : window.train_end]
        test_slice  = data[window.test_start  : window.test_end]
        result      = evaluate_fn(train_slice, test_slice)

    evaluate_fn must be a pure, deterministic function. Its signature:
        evaluate_fn(train: Sequence[Any], test: Sequence[Any]) -> Dict[str, Any]

    Args:
        data:        Full dataset as a sequence.
        train_size:  Training window size.
        test_size:   Test window size.
        step:        Step size per fold.
        evaluate_fn: Caller-supplied deterministic evaluation function.

    Returns:
        List of dicts, one per fold, each containing:
            'fold':   fold index (int)
            'window': WalkForwardWindow
            **result: all keys from evaluate_fn's return dict
    """
    windows = generate_windows(len(data), train_size, test_size, step)
    results: List[Dict[str, Any]] = []
    for window in windows:
        train_slice = data[window.train_start : window.train_end]
        test_slice  = data[window.test_start  : window.test_end]
        fold_result = None
        entry: Dict[str, Any] = {
            "fold":   window.fold,
            "window": window,
        }
        entry.update(fold_result)
        results.append(entry)
    return results


# ---------------------------------------------------------------------------
# RUN WALK-FORWARD
# ---------------------------------------------------------------------------

def x_run_walkforward__mutmut_14(
    data:        Sequence[Any],
    train_size:  int,
    test_size:   int,
    step:        int,
    evaluate_fn: Callable[[Sequence[Any], Sequence[Any]], Dict[str, Any]],
) -> List[Dict[str, Any]]:
    """
    Run deterministic walk-forward validation.

    For each window generated by generate_windows():
        train_slice = data[window.train_start : window.train_end]
        test_slice  = data[window.test_start  : window.test_end]
        result      = evaluate_fn(train_slice, test_slice)

    evaluate_fn must be a pure, deterministic function. Its signature:
        evaluate_fn(train: Sequence[Any], test: Sequence[Any]) -> Dict[str, Any]

    Args:
        data:        Full dataset as a sequence.
        train_size:  Training window size.
        test_size:   Test window size.
        step:        Step size per fold.
        evaluate_fn: Caller-supplied deterministic evaluation function.

    Returns:
        List of dicts, one per fold, each containing:
            'fold':   fold index (int)
            'window': WalkForwardWindow
            **result: all keys from evaluate_fn's return dict
    """
    windows = generate_windows(len(data), train_size, test_size, step)
    results: List[Dict[str, Any]] = []
    for window in windows:
        train_slice = data[window.train_start : window.train_end]
        test_slice  = data[window.test_start  : window.test_end]
        fold_result = evaluate_fn(None, test_slice)
        entry: Dict[str, Any] = {
            "fold":   window.fold,
            "window": window,
        }
        entry.update(fold_result)
        results.append(entry)
    return results


# ---------------------------------------------------------------------------
# RUN WALK-FORWARD
# ---------------------------------------------------------------------------

def x_run_walkforward__mutmut_15(
    data:        Sequence[Any],
    train_size:  int,
    test_size:   int,
    step:        int,
    evaluate_fn: Callable[[Sequence[Any], Sequence[Any]], Dict[str, Any]],
) -> List[Dict[str, Any]]:
    """
    Run deterministic walk-forward validation.

    For each window generated by generate_windows():
        train_slice = data[window.train_start : window.train_end]
        test_slice  = data[window.test_start  : window.test_end]
        result      = evaluate_fn(train_slice, test_slice)

    evaluate_fn must be a pure, deterministic function. Its signature:
        evaluate_fn(train: Sequence[Any], test: Sequence[Any]) -> Dict[str, Any]

    Args:
        data:        Full dataset as a sequence.
        train_size:  Training window size.
        test_size:   Test window size.
        step:        Step size per fold.
        evaluate_fn: Caller-supplied deterministic evaluation function.

    Returns:
        List of dicts, one per fold, each containing:
            'fold':   fold index (int)
            'window': WalkForwardWindow
            **result: all keys from evaluate_fn's return dict
    """
    windows = generate_windows(len(data), train_size, test_size, step)
    results: List[Dict[str, Any]] = []
    for window in windows:
        train_slice = data[window.train_start : window.train_end]
        test_slice  = data[window.test_start  : window.test_end]
        fold_result = evaluate_fn(train_slice, None)
        entry: Dict[str, Any] = {
            "fold":   window.fold,
            "window": window,
        }
        entry.update(fold_result)
        results.append(entry)
    return results


# ---------------------------------------------------------------------------
# RUN WALK-FORWARD
# ---------------------------------------------------------------------------

def x_run_walkforward__mutmut_16(
    data:        Sequence[Any],
    train_size:  int,
    test_size:   int,
    step:        int,
    evaluate_fn: Callable[[Sequence[Any], Sequence[Any]], Dict[str, Any]],
) -> List[Dict[str, Any]]:
    """
    Run deterministic walk-forward validation.

    For each window generated by generate_windows():
        train_slice = data[window.train_start : window.train_end]
        test_slice  = data[window.test_start  : window.test_end]
        result      = evaluate_fn(train_slice, test_slice)

    evaluate_fn must be a pure, deterministic function. Its signature:
        evaluate_fn(train: Sequence[Any], test: Sequence[Any]) -> Dict[str, Any]

    Args:
        data:        Full dataset as a sequence.
        train_size:  Training window size.
        test_size:   Test window size.
        step:        Step size per fold.
        evaluate_fn: Caller-supplied deterministic evaluation function.

    Returns:
        List of dicts, one per fold, each containing:
            'fold':   fold index (int)
            'window': WalkForwardWindow
            **result: all keys from evaluate_fn's return dict
    """
    windows = generate_windows(len(data), train_size, test_size, step)
    results: List[Dict[str, Any]] = []
    for window in windows:
        train_slice = data[window.train_start : window.train_end]
        test_slice  = data[window.test_start  : window.test_end]
        fold_result = evaluate_fn(test_slice)
        entry: Dict[str, Any] = {
            "fold":   window.fold,
            "window": window,
        }
        entry.update(fold_result)
        results.append(entry)
    return results


# ---------------------------------------------------------------------------
# RUN WALK-FORWARD
# ---------------------------------------------------------------------------

def x_run_walkforward__mutmut_17(
    data:        Sequence[Any],
    train_size:  int,
    test_size:   int,
    step:        int,
    evaluate_fn: Callable[[Sequence[Any], Sequence[Any]], Dict[str, Any]],
) -> List[Dict[str, Any]]:
    """
    Run deterministic walk-forward validation.

    For each window generated by generate_windows():
        train_slice = data[window.train_start : window.train_end]
        test_slice  = data[window.test_start  : window.test_end]
        result      = evaluate_fn(train_slice, test_slice)

    evaluate_fn must be a pure, deterministic function. Its signature:
        evaluate_fn(train: Sequence[Any], test: Sequence[Any]) -> Dict[str, Any]

    Args:
        data:        Full dataset as a sequence.
        train_size:  Training window size.
        test_size:   Test window size.
        step:        Step size per fold.
        evaluate_fn: Caller-supplied deterministic evaluation function.

    Returns:
        List of dicts, one per fold, each containing:
            'fold':   fold index (int)
            'window': WalkForwardWindow
            **result: all keys from evaluate_fn's return dict
    """
    windows = generate_windows(len(data), train_size, test_size, step)
    results: List[Dict[str, Any]] = []
    for window in windows:
        train_slice = data[window.train_start : window.train_end]
        test_slice  = data[window.test_start  : window.test_end]
        fold_result = evaluate_fn(train_slice, )
        entry: Dict[str, Any] = {
            "fold":   window.fold,
            "window": window,
        }
        entry.update(fold_result)
        results.append(entry)
    return results


# ---------------------------------------------------------------------------
# RUN WALK-FORWARD
# ---------------------------------------------------------------------------

def x_run_walkforward__mutmut_18(
    data:        Sequence[Any],
    train_size:  int,
    test_size:   int,
    step:        int,
    evaluate_fn: Callable[[Sequence[Any], Sequence[Any]], Dict[str, Any]],
) -> List[Dict[str, Any]]:
    """
    Run deterministic walk-forward validation.

    For each window generated by generate_windows():
        train_slice = data[window.train_start : window.train_end]
        test_slice  = data[window.test_start  : window.test_end]
        result      = evaluate_fn(train_slice, test_slice)

    evaluate_fn must be a pure, deterministic function. Its signature:
        evaluate_fn(train: Sequence[Any], test: Sequence[Any]) -> Dict[str, Any]

    Args:
        data:        Full dataset as a sequence.
        train_size:  Training window size.
        test_size:   Test window size.
        step:        Step size per fold.
        evaluate_fn: Caller-supplied deterministic evaluation function.

    Returns:
        List of dicts, one per fold, each containing:
            'fold':   fold index (int)
            'window': WalkForwardWindow
            **result: all keys from evaluate_fn's return dict
    """
    windows = generate_windows(len(data), train_size, test_size, step)
    results: List[Dict[str, Any]] = []
    for window in windows:
        train_slice = data[window.train_start : window.train_end]
        test_slice  = data[window.test_start  : window.test_end]
        fold_result = evaluate_fn(train_slice, test_slice)
        entry: Dict[str, Any] = None
        entry.update(fold_result)
        results.append(entry)
    return results


# ---------------------------------------------------------------------------
# RUN WALK-FORWARD
# ---------------------------------------------------------------------------

def x_run_walkforward__mutmut_19(
    data:        Sequence[Any],
    train_size:  int,
    test_size:   int,
    step:        int,
    evaluate_fn: Callable[[Sequence[Any], Sequence[Any]], Dict[str, Any]],
) -> List[Dict[str, Any]]:
    """
    Run deterministic walk-forward validation.

    For each window generated by generate_windows():
        train_slice = data[window.train_start : window.train_end]
        test_slice  = data[window.test_start  : window.test_end]
        result      = evaluate_fn(train_slice, test_slice)

    evaluate_fn must be a pure, deterministic function. Its signature:
        evaluate_fn(train: Sequence[Any], test: Sequence[Any]) -> Dict[str, Any]

    Args:
        data:        Full dataset as a sequence.
        train_size:  Training window size.
        test_size:   Test window size.
        step:        Step size per fold.
        evaluate_fn: Caller-supplied deterministic evaluation function.

    Returns:
        List of dicts, one per fold, each containing:
            'fold':   fold index (int)
            'window': WalkForwardWindow
            **result: all keys from evaluate_fn's return dict
    """
    windows = generate_windows(len(data), train_size, test_size, step)
    results: List[Dict[str, Any]] = []
    for window in windows:
        train_slice = data[window.train_start : window.train_end]
        test_slice  = data[window.test_start  : window.test_end]
        fold_result = evaluate_fn(train_slice, test_slice)
        entry: Dict[str, Any] = {
            "XXfoldXX":   window.fold,
            "window": window,
        }
        entry.update(fold_result)
        results.append(entry)
    return results


# ---------------------------------------------------------------------------
# RUN WALK-FORWARD
# ---------------------------------------------------------------------------

def x_run_walkforward__mutmut_20(
    data:        Sequence[Any],
    train_size:  int,
    test_size:   int,
    step:        int,
    evaluate_fn: Callable[[Sequence[Any], Sequence[Any]], Dict[str, Any]],
) -> List[Dict[str, Any]]:
    """
    Run deterministic walk-forward validation.

    For each window generated by generate_windows():
        train_slice = data[window.train_start : window.train_end]
        test_slice  = data[window.test_start  : window.test_end]
        result      = evaluate_fn(train_slice, test_slice)

    evaluate_fn must be a pure, deterministic function. Its signature:
        evaluate_fn(train: Sequence[Any], test: Sequence[Any]) -> Dict[str, Any]

    Args:
        data:        Full dataset as a sequence.
        train_size:  Training window size.
        test_size:   Test window size.
        step:        Step size per fold.
        evaluate_fn: Caller-supplied deterministic evaluation function.

    Returns:
        List of dicts, one per fold, each containing:
            'fold':   fold index (int)
            'window': WalkForwardWindow
            **result: all keys from evaluate_fn's return dict
    """
    windows = generate_windows(len(data), train_size, test_size, step)
    results: List[Dict[str, Any]] = []
    for window in windows:
        train_slice = data[window.train_start : window.train_end]
        test_slice  = data[window.test_start  : window.test_end]
        fold_result = evaluate_fn(train_slice, test_slice)
        entry: Dict[str, Any] = {
            "FOLD":   window.fold,
            "window": window,
        }
        entry.update(fold_result)
        results.append(entry)
    return results


# ---------------------------------------------------------------------------
# RUN WALK-FORWARD
# ---------------------------------------------------------------------------

def x_run_walkforward__mutmut_21(
    data:        Sequence[Any],
    train_size:  int,
    test_size:   int,
    step:        int,
    evaluate_fn: Callable[[Sequence[Any], Sequence[Any]], Dict[str, Any]],
) -> List[Dict[str, Any]]:
    """
    Run deterministic walk-forward validation.

    For each window generated by generate_windows():
        train_slice = data[window.train_start : window.train_end]
        test_slice  = data[window.test_start  : window.test_end]
        result      = evaluate_fn(train_slice, test_slice)

    evaluate_fn must be a pure, deterministic function. Its signature:
        evaluate_fn(train: Sequence[Any], test: Sequence[Any]) -> Dict[str, Any]

    Args:
        data:        Full dataset as a sequence.
        train_size:  Training window size.
        test_size:   Test window size.
        step:        Step size per fold.
        evaluate_fn: Caller-supplied deterministic evaluation function.

    Returns:
        List of dicts, one per fold, each containing:
            'fold':   fold index (int)
            'window': WalkForwardWindow
            **result: all keys from evaluate_fn's return dict
    """
    windows = generate_windows(len(data), train_size, test_size, step)
    results: List[Dict[str, Any]] = []
    for window in windows:
        train_slice = data[window.train_start : window.train_end]
        test_slice  = data[window.test_start  : window.test_end]
        fold_result = evaluate_fn(train_slice, test_slice)
        entry: Dict[str, Any] = {
            "fold":   window.fold,
            "XXwindowXX": window,
        }
        entry.update(fold_result)
        results.append(entry)
    return results


# ---------------------------------------------------------------------------
# RUN WALK-FORWARD
# ---------------------------------------------------------------------------

def x_run_walkforward__mutmut_22(
    data:        Sequence[Any],
    train_size:  int,
    test_size:   int,
    step:        int,
    evaluate_fn: Callable[[Sequence[Any], Sequence[Any]], Dict[str, Any]],
) -> List[Dict[str, Any]]:
    """
    Run deterministic walk-forward validation.

    For each window generated by generate_windows():
        train_slice = data[window.train_start : window.train_end]
        test_slice  = data[window.test_start  : window.test_end]
        result      = evaluate_fn(train_slice, test_slice)

    evaluate_fn must be a pure, deterministic function. Its signature:
        evaluate_fn(train: Sequence[Any], test: Sequence[Any]) -> Dict[str, Any]

    Args:
        data:        Full dataset as a sequence.
        train_size:  Training window size.
        test_size:   Test window size.
        step:        Step size per fold.
        evaluate_fn: Caller-supplied deterministic evaluation function.

    Returns:
        List of dicts, one per fold, each containing:
            'fold':   fold index (int)
            'window': WalkForwardWindow
            **result: all keys from evaluate_fn's return dict
    """
    windows = generate_windows(len(data), train_size, test_size, step)
    results: List[Dict[str, Any]] = []
    for window in windows:
        train_slice = data[window.train_start : window.train_end]
        test_slice  = data[window.test_start  : window.test_end]
        fold_result = evaluate_fn(train_slice, test_slice)
        entry: Dict[str, Any] = {
            "fold":   window.fold,
            "WINDOW": window,
        }
        entry.update(fold_result)
        results.append(entry)
    return results


# ---------------------------------------------------------------------------
# RUN WALK-FORWARD
# ---------------------------------------------------------------------------

def x_run_walkforward__mutmut_23(
    data:        Sequence[Any],
    train_size:  int,
    test_size:   int,
    step:        int,
    evaluate_fn: Callable[[Sequence[Any], Sequence[Any]], Dict[str, Any]],
) -> List[Dict[str, Any]]:
    """
    Run deterministic walk-forward validation.

    For each window generated by generate_windows():
        train_slice = data[window.train_start : window.train_end]
        test_slice  = data[window.test_start  : window.test_end]
        result      = evaluate_fn(train_slice, test_slice)

    evaluate_fn must be a pure, deterministic function. Its signature:
        evaluate_fn(train: Sequence[Any], test: Sequence[Any]) -> Dict[str, Any]

    Args:
        data:        Full dataset as a sequence.
        train_size:  Training window size.
        test_size:   Test window size.
        step:        Step size per fold.
        evaluate_fn: Caller-supplied deterministic evaluation function.

    Returns:
        List of dicts, one per fold, each containing:
            'fold':   fold index (int)
            'window': WalkForwardWindow
            **result: all keys from evaluate_fn's return dict
    """
    windows = generate_windows(len(data), train_size, test_size, step)
    results: List[Dict[str, Any]] = []
    for window in windows:
        train_slice = data[window.train_start : window.train_end]
        test_slice  = data[window.test_start  : window.test_end]
        fold_result = evaluate_fn(train_slice, test_slice)
        entry: Dict[str, Any] = {
            "fold":   window.fold,
            "window": window,
        }
        entry.update(None)
        results.append(entry)
    return results


# ---------------------------------------------------------------------------
# RUN WALK-FORWARD
# ---------------------------------------------------------------------------

def x_run_walkforward__mutmut_24(
    data:        Sequence[Any],
    train_size:  int,
    test_size:   int,
    step:        int,
    evaluate_fn: Callable[[Sequence[Any], Sequence[Any]], Dict[str, Any]],
) -> List[Dict[str, Any]]:
    """
    Run deterministic walk-forward validation.

    For each window generated by generate_windows():
        train_slice = data[window.train_start : window.train_end]
        test_slice  = data[window.test_start  : window.test_end]
        result      = evaluate_fn(train_slice, test_slice)

    evaluate_fn must be a pure, deterministic function. Its signature:
        evaluate_fn(train: Sequence[Any], test: Sequence[Any]) -> Dict[str, Any]

    Args:
        data:        Full dataset as a sequence.
        train_size:  Training window size.
        test_size:   Test window size.
        step:        Step size per fold.
        evaluate_fn: Caller-supplied deterministic evaluation function.

    Returns:
        List of dicts, one per fold, each containing:
            'fold':   fold index (int)
            'window': WalkForwardWindow
            **result: all keys from evaluate_fn's return dict
    """
    windows = generate_windows(len(data), train_size, test_size, step)
    results: List[Dict[str, Any]] = []
    for window in windows:
        train_slice = data[window.train_start : window.train_end]
        test_slice  = data[window.test_start  : window.test_end]
        fold_result = evaluate_fn(train_slice, test_slice)
        entry: Dict[str, Any] = {
            "fold":   window.fold,
            "window": window,
        }
        entry.update(fold_result)
        results.append(None)
    return results

x_run_walkforward__mutmut_mutants : ClassVar[MutantDict] = { # type: ignore
'x_run_walkforward__mutmut_1': x_run_walkforward__mutmut_1, 
    'x_run_walkforward__mutmut_2': x_run_walkforward__mutmut_2, 
    'x_run_walkforward__mutmut_3': x_run_walkforward__mutmut_3, 
    'x_run_walkforward__mutmut_4': x_run_walkforward__mutmut_4, 
    'x_run_walkforward__mutmut_5': x_run_walkforward__mutmut_5, 
    'x_run_walkforward__mutmut_6': x_run_walkforward__mutmut_6, 
    'x_run_walkforward__mutmut_7': x_run_walkforward__mutmut_7, 
    'x_run_walkforward__mutmut_8': x_run_walkforward__mutmut_8, 
    'x_run_walkforward__mutmut_9': x_run_walkforward__mutmut_9, 
    'x_run_walkforward__mutmut_10': x_run_walkforward__mutmut_10, 
    'x_run_walkforward__mutmut_11': x_run_walkforward__mutmut_11, 
    'x_run_walkforward__mutmut_12': x_run_walkforward__mutmut_12, 
    'x_run_walkforward__mutmut_13': x_run_walkforward__mutmut_13, 
    'x_run_walkforward__mutmut_14': x_run_walkforward__mutmut_14, 
    'x_run_walkforward__mutmut_15': x_run_walkforward__mutmut_15, 
    'x_run_walkforward__mutmut_16': x_run_walkforward__mutmut_16, 
    'x_run_walkforward__mutmut_17': x_run_walkforward__mutmut_17, 
    'x_run_walkforward__mutmut_18': x_run_walkforward__mutmut_18, 
    'x_run_walkforward__mutmut_19': x_run_walkforward__mutmut_19, 
    'x_run_walkforward__mutmut_20': x_run_walkforward__mutmut_20, 
    'x_run_walkforward__mutmut_21': x_run_walkforward__mutmut_21, 
    'x_run_walkforward__mutmut_22': x_run_walkforward__mutmut_22, 
    'x_run_walkforward__mutmut_23': x_run_walkforward__mutmut_23, 
    'x_run_walkforward__mutmut_24': x_run_walkforward__mutmut_24
}
x_run_walkforward__mutmut_orig.__name__ = 'x_run_walkforward'


__all__ = [
    "WalkForwardWindow",
    "generate_windows",
    "run_walkforward",
]
