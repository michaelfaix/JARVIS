# jarvis/orchestrator/pipeline.py
# Version: 1.2.1  (Governance Gate -- Pipeline-scoped validation only)
# External orchestration layer.
#
# GOVERNANCE GATE (pipeline-scoped):
#   Validates ONLY what downstream modules do NOT already validate:
#     GOV-01: meta_uncertainty in [0.0, 1.0]
#     GOV-05: regime must be a GlobalRegimeState instance
#
#   INTENTIONALLY EXCLUDED from gate (downstream owns these):
#     GOV-02: initial_capital  -> allocate_positions() raises ValueError
#     GOV-03: window size      -> RiskEngine.assess()  raises ValueError
#     GOV-06: CRISIS + meta    -> CRISIS is a valid runtime regime;
#                                 meta_uncertainty=0.1 is legitimate
#
# Standard import:
#   from jarvis.orchestrator.pipeline import run_full_pipeline

import math

from jarvis.core.regime import GlobalRegimeState
from jarvis.core.regime_detector import RegimeDetector
from jarvis.core.state_layer import LatentState
from jarvis.core.state_estimator import StateEstimator
from jarvis.core.volatility_tracker import VolatilityTracker
from jarvis.governance.exceptions import GovernanceViolationError
from jarvis.governance.policy_validator import validate_pipeline_config
from jarvis.risk.risk_engine import RiskEngine
from jarvis.execution.exposure_router import route_exposure_to_positions
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
# Internal helpers (unchanged from v1.1.0)
# ---------------------------------------------------------------------------

def _extract_regime_features(returns_history: list) -> dict:
    args = [returns_history]# type: ignore
    kwargs = {}# type: ignore
    return _mutmut_trampoline(x__extract_regime_features__mutmut_orig, x__extract_regime_features__mutmut_mutants, args, kwargs, None)


# ---------------------------------------------------------------------------
# Internal helpers (unchanged from v1.1.0)
# ---------------------------------------------------------------------------

def x__extract_regime_features__mutmut_orig(returns_history: list) -> dict:
    clean = [r if math.isfinite(r) else 0.0 for r in returns_history]
    n = len(clean)
    mean_r = sum(clean) / n
    variance = sum((r - mean_r) ** 2 for r in clean) / max(n - 1, 1)
    volatility = math.sqrt(max(variance, 0.0))
    window = min(5, n)
    recent = clean[-window:]
    recent_mean = sum(recent) / window
    trend_strength = recent_mean / max(volatility, 1e-8)
    if n >= 2:
        pairs = [(clean[i], clean[i + 1]) for i in range(n - 1)]
        num = sum((a - mean_r) * (b - mean_r) for a, b in pairs)
        denom = sum((r - mean_r) ** 2 for r in clean)
        lag1_autocorr = num / max(denom, 1e-15)
        mean_reversion = max(-1.0, min(1.0, -lag1_autocorr))
    else:
        mean_reversion = 0.0
    short_window = min(10, n)
    short_clean = clean[-short_window:]
    short_mean = sum(short_clean) / len(short_clean)
    short_var = sum((r - short_mean) ** 2 for r in short_clean) / max(len(short_clean) - 1, 1)
    short_vol = math.sqrt(max(short_var, 0.0))
    full_vol = max(volatility, 1e-8)
    stress_raw = (short_vol / full_vol) - 1.0
    stress = max(0.0, min(1.0, stress_raw * 0.5 + 0.5))
    momentum = max(-1.0, min(1.0, recent_mean / max(full_vol, 1e-8)))
    liquidity = 1.0 - stress
    return {
        "volatility":     volatility,
        "trend_strength": trend_strength,
        "mean_reversion": mean_reversion,
        "stress":         stress,
        "momentum":       momentum,
        "liquidity":      liquidity,
    }


# ---------------------------------------------------------------------------
# Internal helpers (unchanged from v1.1.0)
# ---------------------------------------------------------------------------

def x__extract_regime_features__mutmut_1(returns_history: list) -> dict:
    clean = None
    n = len(clean)
    mean_r = sum(clean) / n
    variance = sum((r - mean_r) ** 2 for r in clean) / max(n - 1, 1)
    volatility = math.sqrt(max(variance, 0.0))
    window = min(5, n)
    recent = clean[-window:]
    recent_mean = sum(recent) / window
    trend_strength = recent_mean / max(volatility, 1e-8)
    if n >= 2:
        pairs = [(clean[i], clean[i + 1]) for i in range(n - 1)]
        num = sum((a - mean_r) * (b - mean_r) for a, b in pairs)
        denom = sum((r - mean_r) ** 2 for r in clean)
        lag1_autocorr = num / max(denom, 1e-15)
        mean_reversion = max(-1.0, min(1.0, -lag1_autocorr))
    else:
        mean_reversion = 0.0
    short_window = min(10, n)
    short_clean = clean[-short_window:]
    short_mean = sum(short_clean) / len(short_clean)
    short_var = sum((r - short_mean) ** 2 for r in short_clean) / max(len(short_clean) - 1, 1)
    short_vol = math.sqrt(max(short_var, 0.0))
    full_vol = max(volatility, 1e-8)
    stress_raw = (short_vol / full_vol) - 1.0
    stress = max(0.0, min(1.0, stress_raw * 0.5 + 0.5))
    momentum = max(-1.0, min(1.0, recent_mean / max(full_vol, 1e-8)))
    liquidity = 1.0 - stress
    return {
        "volatility":     volatility,
        "trend_strength": trend_strength,
        "mean_reversion": mean_reversion,
        "stress":         stress,
        "momentum":       momentum,
        "liquidity":      liquidity,
    }


# ---------------------------------------------------------------------------
# Internal helpers (unchanged from v1.1.0)
# ---------------------------------------------------------------------------

def x__extract_regime_features__mutmut_2(returns_history: list) -> dict:
    clean = [r if math.isfinite(None) else 0.0 for r in returns_history]
    n = len(clean)
    mean_r = sum(clean) / n
    variance = sum((r - mean_r) ** 2 for r in clean) / max(n - 1, 1)
    volatility = math.sqrt(max(variance, 0.0))
    window = min(5, n)
    recent = clean[-window:]
    recent_mean = sum(recent) / window
    trend_strength = recent_mean / max(volatility, 1e-8)
    if n >= 2:
        pairs = [(clean[i], clean[i + 1]) for i in range(n - 1)]
        num = sum((a - mean_r) * (b - mean_r) for a, b in pairs)
        denom = sum((r - mean_r) ** 2 for r in clean)
        lag1_autocorr = num / max(denom, 1e-15)
        mean_reversion = max(-1.0, min(1.0, -lag1_autocorr))
    else:
        mean_reversion = 0.0
    short_window = min(10, n)
    short_clean = clean[-short_window:]
    short_mean = sum(short_clean) / len(short_clean)
    short_var = sum((r - short_mean) ** 2 for r in short_clean) / max(len(short_clean) - 1, 1)
    short_vol = math.sqrt(max(short_var, 0.0))
    full_vol = max(volatility, 1e-8)
    stress_raw = (short_vol / full_vol) - 1.0
    stress = max(0.0, min(1.0, stress_raw * 0.5 + 0.5))
    momentum = max(-1.0, min(1.0, recent_mean / max(full_vol, 1e-8)))
    liquidity = 1.0 - stress
    return {
        "volatility":     volatility,
        "trend_strength": trend_strength,
        "mean_reversion": mean_reversion,
        "stress":         stress,
        "momentum":       momentum,
        "liquidity":      liquidity,
    }


# ---------------------------------------------------------------------------
# Internal helpers (unchanged from v1.1.0)
# ---------------------------------------------------------------------------

def x__extract_regime_features__mutmut_3(returns_history: list) -> dict:
    clean = [r if math.isfinite(r) else 1.0 for r in returns_history]
    n = len(clean)
    mean_r = sum(clean) / n
    variance = sum((r - mean_r) ** 2 for r in clean) / max(n - 1, 1)
    volatility = math.sqrt(max(variance, 0.0))
    window = min(5, n)
    recent = clean[-window:]
    recent_mean = sum(recent) / window
    trend_strength = recent_mean / max(volatility, 1e-8)
    if n >= 2:
        pairs = [(clean[i], clean[i + 1]) for i in range(n - 1)]
        num = sum((a - mean_r) * (b - mean_r) for a, b in pairs)
        denom = sum((r - mean_r) ** 2 for r in clean)
        lag1_autocorr = num / max(denom, 1e-15)
        mean_reversion = max(-1.0, min(1.0, -lag1_autocorr))
    else:
        mean_reversion = 0.0
    short_window = min(10, n)
    short_clean = clean[-short_window:]
    short_mean = sum(short_clean) / len(short_clean)
    short_var = sum((r - short_mean) ** 2 for r in short_clean) / max(len(short_clean) - 1, 1)
    short_vol = math.sqrt(max(short_var, 0.0))
    full_vol = max(volatility, 1e-8)
    stress_raw = (short_vol / full_vol) - 1.0
    stress = max(0.0, min(1.0, stress_raw * 0.5 + 0.5))
    momentum = max(-1.0, min(1.0, recent_mean / max(full_vol, 1e-8)))
    liquidity = 1.0 - stress
    return {
        "volatility":     volatility,
        "trend_strength": trend_strength,
        "mean_reversion": mean_reversion,
        "stress":         stress,
        "momentum":       momentum,
        "liquidity":      liquidity,
    }


# ---------------------------------------------------------------------------
# Internal helpers (unchanged from v1.1.0)
# ---------------------------------------------------------------------------

def x__extract_regime_features__mutmut_4(returns_history: list) -> dict:
    clean = [r if math.isfinite(r) else 0.0 for r in returns_history]
    n = None
    mean_r = sum(clean) / n
    variance = sum((r - mean_r) ** 2 for r in clean) / max(n - 1, 1)
    volatility = math.sqrt(max(variance, 0.0))
    window = min(5, n)
    recent = clean[-window:]
    recent_mean = sum(recent) / window
    trend_strength = recent_mean / max(volatility, 1e-8)
    if n >= 2:
        pairs = [(clean[i], clean[i + 1]) for i in range(n - 1)]
        num = sum((a - mean_r) * (b - mean_r) for a, b in pairs)
        denom = sum((r - mean_r) ** 2 for r in clean)
        lag1_autocorr = num / max(denom, 1e-15)
        mean_reversion = max(-1.0, min(1.0, -lag1_autocorr))
    else:
        mean_reversion = 0.0
    short_window = min(10, n)
    short_clean = clean[-short_window:]
    short_mean = sum(short_clean) / len(short_clean)
    short_var = sum((r - short_mean) ** 2 for r in short_clean) / max(len(short_clean) - 1, 1)
    short_vol = math.sqrt(max(short_var, 0.0))
    full_vol = max(volatility, 1e-8)
    stress_raw = (short_vol / full_vol) - 1.0
    stress = max(0.0, min(1.0, stress_raw * 0.5 + 0.5))
    momentum = max(-1.0, min(1.0, recent_mean / max(full_vol, 1e-8)))
    liquidity = 1.0 - stress
    return {
        "volatility":     volatility,
        "trend_strength": trend_strength,
        "mean_reversion": mean_reversion,
        "stress":         stress,
        "momentum":       momentum,
        "liquidity":      liquidity,
    }


# ---------------------------------------------------------------------------
# Internal helpers (unchanged from v1.1.0)
# ---------------------------------------------------------------------------

def x__extract_regime_features__mutmut_5(returns_history: list) -> dict:
    clean = [r if math.isfinite(r) else 0.0 for r in returns_history]
    n = len(clean)
    mean_r = None
    variance = sum((r - mean_r) ** 2 for r in clean) / max(n - 1, 1)
    volatility = math.sqrt(max(variance, 0.0))
    window = min(5, n)
    recent = clean[-window:]
    recent_mean = sum(recent) / window
    trend_strength = recent_mean / max(volatility, 1e-8)
    if n >= 2:
        pairs = [(clean[i], clean[i + 1]) for i in range(n - 1)]
        num = sum((a - mean_r) * (b - mean_r) for a, b in pairs)
        denom = sum((r - mean_r) ** 2 for r in clean)
        lag1_autocorr = num / max(denom, 1e-15)
        mean_reversion = max(-1.0, min(1.0, -lag1_autocorr))
    else:
        mean_reversion = 0.0
    short_window = min(10, n)
    short_clean = clean[-short_window:]
    short_mean = sum(short_clean) / len(short_clean)
    short_var = sum((r - short_mean) ** 2 for r in short_clean) / max(len(short_clean) - 1, 1)
    short_vol = math.sqrt(max(short_var, 0.0))
    full_vol = max(volatility, 1e-8)
    stress_raw = (short_vol / full_vol) - 1.0
    stress = max(0.0, min(1.0, stress_raw * 0.5 + 0.5))
    momentum = max(-1.0, min(1.0, recent_mean / max(full_vol, 1e-8)))
    liquidity = 1.0 - stress
    return {
        "volatility":     volatility,
        "trend_strength": trend_strength,
        "mean_reversion": mean_reversion,
        "stress":         stress,
        "momentum":       momentum,
        "liquidity":      liquidity,
    }


# ---------------------------------------------------------------------------
# Internal helpers (unchanged from v1.1.0)
# ---------------------------------------------------------------------------

def x__extract_regime_features__mutmut_6(returns_history: list) -> dict:
    clean = [r if math.isfinite(r) else 0.0 for r in returns_history]
    n = len(clean)
    mean_r = sum(clean) * n
    variance = sum((r - mean_r) ** 2 for r in clean) / max(n - 1, 1)
    volatility = math.sqrt(max(variance, 0.0))
    window = min(5, n)
    recent = clean[-window:]
    recent_mean = sum(recent) / window
    trend_strength = recent_mean / max(volatility, 1e-8)
    if n >= 2:
        pairs = [(clean[i], clean[i + 1]) for i in range(n - 1)]
        num = sum((a - mean_r) * (b - mean_r) for a, b in pairs)
        denom = sum((r - mean_r) ** 2 for r in clean)
        lag1_autocorr = num / max(denom, 1e-15)
        mean_reversion = max(-1.0, min(1.0, -lag1_autocorr))
    else:
        mean_reversion = 0.0
    short_window = min(10, n)
    short_clean = clean[-short_window:]
    short_mean = sum(short_clean) / len(short_clean)
    short_var = sum((r - short_mean) ** 2 for r in short_clean) / max(len(short_clean) - 1, 1)
    short_vol = math.sqrt(max(short_var, 0.0))
    full_vol = max(volatility, 1e-8)
    stress_raw = (short_vol / full_vol) - 1.0
    stress = max(0.0, min(1.0, stress_raw * 0.5 + 0.5))
    momentum = max(-1.0, min(1.0, recent_mean / max(full_vol, 1e-8)))
    liquidity = 1.0 - stress
    return {
        "volatility":     volatility,
        "trend_strength": trend_strength,
        "mean_reversion": mean_reversion,
        "stress":         stress,
        "momentum":       momentum,
        "liquidity":      liquidity,
    }


# ---------------------------------------------------------------------------
# Internal helpers (unchanged from v1.1.0)
# ---------------------------------------------------------------------------

def x__extract_regime_features__mutmut_7(returns_history: list) -> dict:
    clean = [r if math.isfinite(r) else 0.0 for r in returns_history]
    n = len(clean)
    mean_r = sum(None) / n
    variance = sum((r - mean_r) ** 2 for r in clean) / max(n - 1, 1)
    volatility = math.sqrt(max(variance, 0.0))
    window = min(5, n)
    recent = clean[-window:]
    recent_mean = sum(recent) / window
    trend_strength = recent_mean / max(volatility, 1e-8)
    if n >= 2:
        pairs = [(clean[i], clean[i + 1]) for i in range(n - 1)]
        num = sum((a - mean_r) * (b - mean_r) for a, b in pairs)
        denom = sum((r - mean_r) ** 2 for r in clean)
        lag1_autocorr = num / max(denom, 1e-15)
        mean_reversion = max(-1.0, min(1.0, -lag1_autocorr))
    else:
        mean_reversion = 0.0
    short_window = min(10, n)
    short_clean = clean[-short_window:]
    short_mean = sum(short_clean) / len(short_clean)
    short_var = sum((r - short_mean) ** 2 for r in short_clean) / max(len(short_clean) - 1, 1)
    short_vol = math.sqrt(max(short_var, 0.0))
    full_vol = max(volatility, 1e-8)
    stress_raw = (short_vol / full_vol) - 1.0
    stress = max(0.0, min(1.0, stress_raw * 0.5 + 0.5))
    momentum = max(-1.0, min(1.0, recent_mean / max(full_vol, 1e-8)))
    liquidity = 1.0 - stress
    return {
        "volatility":     volatility,
        "trend_strength": trend_strength,
        "mean_reversion": mean_reversion,
        "stress":         stress,
        "momentum":       momentum,
        "liquidity":      liquidity,
    }


# ---------------------------------------------------------------------------
# Internal helpers (unchanged from v1.1.0)
# ---------------------------------------------------------------------------

def x__extract_regime_features__mutmut_8(returns_history: list) -> dict:
    clean = [r if math.isfinite(r) else 0.0 for r in returns_history]
    n = len(clean)
    mean_r = sum(clean) / n
    variance = None
    volatility = math.sqrt(max(variance, 0.0))
    window = min(5, n)
    recent = clean[-window:]
    recent_mean = sum(recent) / window
    trend_strength = recent_mean / max(volatility, 1e-8)
    if n >= 2:
        pairs = [(clean[i], clean[i + 1]) for i in range(n - 1)]
        num = sum((a - mean_r) * (b - mean_r) for a, b in pairs)
        denom = sum((r - mean_r) ** 2 for r in clean)
        lag1_autocorr = num / max(denom, 1e-15)
        mean_reversion = max(-1.0, min(1.0, -lag1_autocorr))
    else:
        mean_reversion = 0.0
    short_window = min(10, n)
    short_clean = clean[-short_window:]
    short_mean = sum(short_clean) / len(short_clean)
    short_var = sum((r - short_mean) ** 2 for r in short_clean) / max(len(short_clean) - 1, 1)
    short_vol = math.sqrt(max(short_var, 0.0))
    full_vol = max(volatility, 1e-8)
    stress_raw = (short_vol / full_vol) - 1.0
    stress = max(0.0, min(1.0, stress_raw * 0.5 + 0.5))
    momentum = max(-1.0, min(1.0, recent_mean / max(full_vol, 1e-8)))
    liquidity = 1.0 - stress
    return {
        "volatility":     volatility,
        "trend_strength": trend_strength,
        "mean_reversion": mean_reversion,
        "stress":         stress,
        "momentum":       momentum,
        "liquidity":      liquidity,
    }


# ---------------------------------------------------------------------------
# Internal helpers (unchanged from v1.1.0)
# ---------------------------------------------------------------------------

def x__extract_regime_features__mutmut_9(returns_history: list) -> dict:
    clean = [r if math.isfinite(r) else 0.0 for r in returns_history]
    n = len(clean)
    mean_r = sum(clean) / n
    variance = sum((r - mean_r) ** 2 for r in clean) * max(n - 1, 1)
    volatility = math.sqrt(max(variance, 0.0))
    window = min(5, n)
    recent = clean[-window:]
    recent_mean = sum(recent) / window
    trend_strength = recent_mean / max(volatility, 1e-8)
    if n >= 2:
        pairs = [(clean[i], clean[i + 1]) for i in range(n - 1)]
        num = sum((a - mean_r) * (b - mean_r) for a, b in pairs)
        denom = sum((r - mean_r) ** 2 for r in clean)
        lag1_autocorr = num / max(denom, 1e-15)
        mean_reversion = max(-1.0, min(1.0, -lag1_autocorr))
    else:
        mean_reversion = 0.0
    short_window = min(10, n)
    short_clean = clean[-short_window:]
    short_mean = sum(short_clean) / len(short_clean)
    short_var = sum((r - short_mean) ** 2 for r in short_clean) / max(len(short_clean) - 1, 1)
    short_vol = math.sqrt(max(short_var, 0.0))
    full_vol = max(volatility, 1e-8)
    stress_raw = (short_vol / full_vol) - 1.0
    stress = max(0.0, min(1.0, stress_raw * 0.5 + 0.5))
    momentum = max(-1.0, min(1.0, recent_mean / max(full_vol, 1e-8)))
    liquidity = 1.0 - stress
    return {
        "volatility":     volatility,
        "trend_strength": trend_strength,
        "mean_reversion": mean_reversion,
        "stress":         stress,
        "momentum":       momentum,
        "liquidity":      liquidity,
    }


# ---------------------------------------------------------------------------
# Internal helpers (unchanged from v1.1.0)
# ---------------------------------------------------------------------------

def x__extract_regime_features__mutmut_10(returns_history: list) -> dict:
    clean = [r if math.isfinite(r) else 0.0 for r in returns_history]
    n = len(clean)
    mean_r = sum(clean) / n
    variance = sum(None) / max(n - 1, 1)
    volatility = math.sqrt(max(variance, 0.0))
    window = min(5, n)
    recent = clean[-window:]
    recent_mean = sum(recent) / window
    trend_strength = recent_mean / max(volatility, 1e-8)
    if n >= 2:
        pairs = [(clean[i], clean[i + 1]) for i in range(n - 1)]
        num = sum((a - mean_r) * (b - mean_r) for a, b in pairs)
        denom = sum((r - mean_r) ** 2 for r in clean)
        lag1_autocorr = num / max(denom, 1e-15)
        mean_reversion = max(-1.0, min(1.0, -lag1_autocorr))
    else:
        mean_reversion = 0.0
    short_window = min(10, n)
    short_clean = clean[-short_window:]
    short_mean = sum(short_clean) / len(short_clean)
    short_var = sum((r - short_mean) ** 2 for r in short_clean) / max(len(short_clean) - 1, 1)
    short_vol = math.sqrt(max(short_var, 0.0))
    full_vol = max(volatility, 1e-8)
    stress_raw = (short_vol / full_vol) - 1.0
    stress = max(0.0, min(1.0, stress_raw * 0.5 + 0.5))
    momentum = max(-1.0, min(1.0, recent_mean / max(full_vol, 1e-8)))
    liquidity = 1.0 - stress
    return {
        "volatility":     volatility,
        "trend_strength": trend_strength,
        "mean_reversion": mean_reversion,
        "stress":         stress,
        "momentum":       momentum,
        "liquidity":      liquidity,
    }


# ---------------------------------------------------------------------------
# Internal helpers (unchanged from v1.1.0)
# ---------------------------------------------------------------------------

def x__extract_regime_features__mutmut_11(returns_history: list) -> dict:
    clean = [r if math.isfinite(r) else 0.0 for r in returns_history]
    n = len(clean)
    mean_r = sum(clean) / n
    variance = sum((r - mean_r) * 2 for r in clean) / max(n - 1, 1)
    volatility = math.sqrt(max(variance, 0.0))
    window = min(5, n)
    recent = clean[-window:]
    recent_mean = sum(recent) / window
    trend_strength = recent_mean / max(volatility, 1e-8)
    if n >= 2:
        pairs = [(clean[i], clean[i + 1]) for i in range(n - 1)]
        num = sum((a - mean_r) * (b - mean_r) for a, b in pairs)
        denom = sum((r - mean_r) ** 2 for r in clean)
        lag1_autocorr = num / max(denom, 1e-15)
        mean_reversion = max(-1.0, min(1.0, -lag1_autocorr))
    else:
        mean_reversion = 0.0
    short_window = min(10, n)
    short_clean = clean[-short_window:]
    short_mean = sum(short_clean) / len(short_clean)
    short_var = sum((r - short_mean) ** 2 for r in short_clean) / max(len(short_clean) - 1, 1)
    short_vol = math.sqrt(max(short_var, 0.0))
    full_vol = max(volatility, 1e-8)
    stress_raw = (short_vol / full_vol) - 1.0
    stress = max(0.0, min(1.0, stress_raw * 0.5 + 0.5))
    momentum = max(-1.0, min(1.0, recent_mean / max(full_vol, 1e-8)))
    liquidity = 1.0 - stress
    return {
        "volatility":     volatility,
        "trend_strength": trend_strength,
        "mean_reversion": mean_reversion,
        "stress":         stress,
        "momentum":       momentum,
        "liquidity":      liquidity,
    }


# ---------------------------------------------------------------------------
# Internal helpers (unchanged from v1.1.0)
# ---------------------------------------------------------------------------

def x__extract_regime_features__mutmut_12(returns_history: list) -> dict:
    clean = [r if math.isfinite(r) else 0.0 for r in returns_history]
    n = len(clean)
    mean_r = sum(clean) / n
    variance = sum((r + mean_r) ** 2 for r in clean) / max(n - 1, 1)
    volatility = math.sqrt(max(variance, 0.0))
    window = min(5, n)
    recent = clean[-window:]
    recent_mean = sum(recent) / window
    trend_strength = recent_mean / max(volatility, 1e-8)
    if n >= 2:
        pairs = [(clean[i], clean[i + 1]) for i in range(n - 1)]
        num = sum((a - mean_r) * (b - mean_r) for a, b in pairs)
        denom = sum((r - mean_r) ** 2 for r in clean)
        lag1_autocorr = num / max(denom, 1e-15)
        mean_reversion = max(-1.0, min(1.0, -lag1_autocorr))
    else:
        mean_reversion = 0.0
    short_window = min(10, n)
    short_clean = clean[-short_window:]
    short_mean = sum(short_clean) / len(short_clean)
    short_var = sum((r - short_mean) ** 2 for r in short_clean) / max(len(short_clean) - 1, 1)
    short_vol = math.sqrt(max(short_var, 0.0))
    full_vol = max(volatility, 1e-8)
    stress_raw = (short_vol / full_vol) - 1.0
    stress = max(0.0, min(1.0, stress_raw * 0.5 + 0.5))
    momentum = max(-1.0, min(1.0, recent_mean / max(full_vol, 1e-8)))
    liquidity = 1.0 - stress
    return {
        "volatility":     volatility,
        "trend_strength": trend_strength,
        "mean_reversion": mean_reversion,
        "stress":         stress,
        "momentum":       momentum,
        "liquidity":      liquidity,
    }


# ---------------------------------------------------------------------------
# Internal helpers (unchanged from v1.1.0)
# ---------------------------------------------------------------------------

def x__extract_regime_features__mutmut_13(returns_history: list) -> dict:
    clean = [r if math.isfinite(r) else 0.0 for r in returns_history]
    n = len(clean)
    mean_r = sum(clean) / n
    variance = sum((r - mean_r) ** 3 for r in clean) / max(n - 1, 1)
    volatility = math.sqrt(max(variance, 0.0))
    window = min(5, n)
    recent = clean[-window:]
    recent_mean = sum(recent) / window
    trend_strength = recent_mean / max(volatility, 1e-8)
    if n >= 2:
        pairs = [(clean[i], clean[i + 1]) for i in range(n - 1)]
        num = sum((a - mean_r) * (b - mean_r) for a, b in pairs)
        denom = sum((r - mean_r) ** 2 for r in clean)
        lag1_autocorr = num / max(denom, 1e-15)
        mean_reversion = max(-1.0, min(1.0, -lag1_autocorr))
    else:
        mean_reversion = 0.0
    short_window = min(10, n)
    short_clean = clean[-short_window:]
    short_mean = sum(short_clean) / len(short_clean)
    short_var = sum((r - short_mean) ** 2 for r in short_clean) / max(len(short_clean) - 1, 1)
    short_vol = math.sqrt(max(short_var, 0.0))
    full_vol = max(volatility, 1e-8)
    stress_raw = (short_vol / full_vol) - 1.0
    stress = max(0.0, min(1.0, stress_raw * 0.5 + 0.5))
    momentum = max(-1.0, min(1.0, recent_mean / max(full_vol, 1e-8)))
    liquidity = 1.0 - stress
    return {
        "volatility":     volatility,
        "trend_strength": trend_strength,
        "mean_reversion": mean_reversion,
        "stress":         stress,
        "momentum":       momentum,
        "liquidity":      liquidity,
    }


# ---------------------------------------------------------------------------
# Internal helpers (unchanged from v1.1.0)
# ---------------------------------------------------------------------------

def x__extract_regime_features__mutmut_14(returns_history: list) -> dict:
    clean = [r if math.isfinite(r) else 0.0 for r in returns_history]
    n = len(clean)
    mean_r = sum(clean) / n
    variance = sum((r - mean_r) ** 2 for r in clean) / max(None, 1)
    volatility = math.sqrt(max(variance, 0.0))
    window = min(5, n)
    recent = clean[-window:]
    recent_mean = sum(recent) / window
    trend_strength = recent_mean / max(volatility, 1e-8)
    if n >= 2:
        pairs = [(clean[i], clean[i + 1]) for i in range(n - 1)]
        num = sum((a - mean_r) * (b - mean_r) for a, b in pairs)
        denom = sum((r - mean_r) ** 2 for r in clean)
        lag1_autocorr = num / max(denom, 1e-15)
        mean_reversion = max(-1.0, min(1.0, -lag1_autocorr))
    else:
        mean_reversion = 0.0
    short_window = min(10, n)
    short_clean = clean[-short_window:]
    short_mean = sum(short_clean) / len(short_clean)
    short_var = sum((r - short_mean) ** 2 for r in short_clean) / max(len(short_clean) - 1, 1)
    short_vol = math.sqrt(max(short_var, 0.0))
    full_vol = max(volatility, 1e-8)
    stress_raw = (short_vol / full_vol) - 1.0
    stress = max(0.0, min(1.0, stress_raw * 0.5 + 0.5))
    momentum = max(-1.0, min(1.0, recent_mean / max(full_vol, 1e-8)))
    liquidity = 1.0 - stress
    return {
        "volatility":     volatility,
        "trend_strength": trend_strength,
        "mean_reversion": mean_reversion,
        "stress":         stress,
        "momentum":       momentum,
        "liquidity":      liquidity,
    }


# ---------------------------------------------------------------------------
# Internal helpers (unchanged from v1.1.0)
# ---------------------------------------------------------------------------

def x__extract_regime_features__mutmut_15(returns_history: list) -> dict:
    clean = [r if math.isfinite(r) else 0.0 for r in returns_history]
    n = len(clean)
    mean_r = sum(clean) / n
    variance = sum((r - mean_r) ** 2 for r in clean) / max(n - 1, None)
    volatility = math.sqrt(max(variance, 0.0))
    window = min(5, n)
    recent = clean[-window:]
    recent_mean = sum(recent) / window
    trend_strength = recent_mean / max(volatility, 1e-8)
    if n >= 2:
        pairs = [(clean[i], clean[i + 1]) for i in range(n - 1)]
        num = sum((a - mean_r) * (b - mean_r) for a, b in pairs)
        denom = sum((r - mean_r) ** 2 for r in clean)
        lag1_autocorr = num / max(denom, 1e-15)
        mean_reversion = max(-1.0, min(1.0, -lag1_autocorr))
    else:
        mean_reversion = 0.0
    short_window = min(10, n)
    short_clean = clean[-short_window:]
    short_mean = sum(short_clean) / len(short_clean)
    short_var = sum((r - short_mean) ** 2 for r in short_clean) / max(len(short_clean) - 1, 1)
    short_vol = math.sqrt(max(short_var, 0.0))
    full_vol = max(volatility, 1e-8)
    stress_raw = (short_vol / full_vol) - 1.0
    stress = max(0.0, min(1.0, stress_raw * 0.5 + 0.5))
    momentum = max(-1.0, min(1.0, recent_mean / max(full_vol, 1e-8)))
    liquidity = 1.0 - stress
    return {
        "volatility":     volatility,
        "trend_strength": trend_strength,
        "mean_reversion": mean_reversion,
        "stress":         stress,
        "momentum":       momentum,
        "liquidity":      liquidity,
    }


# ---------------------------------------------------------------------------
# Internal helpers (unchanged from v1.1.0)
# ---------------------------------------------------------------------------

def x__extract_regime_features__mutmut_16(returns_history: list) -> dict:
    clean = [r if math.isfinite(r) else 0.0 for r in returns_history]
    n = len(clean)
    mean_r = sum(clean) / n
    variance = sum((r - mean_r) ** 2 for r in clean) / max(1)
    volatility = math.sqrt(max(variance, 0.0))
    window = min(5, n)
    recent = clean[-window:]
    recent_mean = sum(recent) / window
    trend_strength = recent_mean / max(volatility, 1e-8)
    if n >= 2:
        pairs = [(clean[i], clean[i + 1]) for i in range(n - 1)]
        num = sum((a - mean_r) * (b - mean_r) for a, b in pairs)
        denom = sum((r - mean_r) ** 2 for r in clean)
        lag1_autocorr = num / max(denom, 1e-15)
        mean_reversion = max(-1.0, min(1.0, -lag1_autocorr))
    else:
        mean_reversion = 0.0
    short_window = min(10, n)
    short_clean = clean[-short_window:]
    short_mean = sum(short_clean) / len(short_clean)
    short_var = sum((r - short_mean) ** 2 for r in short_clean) / max(len(short_clean) - 1, 1)
    short_vol = math.sqrt(max(short_var, 0.0))
    full_vol = max(volatility, 1e-8)
    stress_raw = (short_vol / full_vol) - 1.0
    stress = max(0.0, min(1.0, stress_raw * 0.5 + 0.5))
    momentum = max(-1.0, min(1.0, recent_mean / max(full_vol, 1e-8)))
    liquidity = 1.0 - stress
    return {
        "volatility":     volatility,
        "trend_strength": trend_strength,
        "mean_reversion": mean_reversion,
        "stress":         stress,
        "momentum":       momentum,
        "liquidity":      liquidity,
    }


# ---------------------------------------------------------------------------
# Internal helpers (unchanged from v1.1.0)
# ---------------------------------------------------------------------------

def x__extract_regime_features__mutmut_17(returns_history: list) -> dict:
    clean = [r if math.isfinite(r) else 0.0 for r in returns_history]
    n = len(clean)
    mean_r = sum(clean) / n
    variance = sum((r - mean_r) ** 2 for r in clean) / max(n - 1, )
    volatility = math.sqrt(max(variance, 0.0))
    window = min(5, n)
    recent = clean[-window:]
    recent_mean = sum(recent) / window
    trend_strength = recent_mean / max(volatility, 1e-8)
    if n >= 2:
        pairs = [(clean[i], clean[i + 1]) for i in range(n - 1)]
        num = sum((a - mean_r) * (b - mean_r) for a, b in pairs)
        denom = sum((r - mean_r) ** 2 for r in clean)
        lag1_autocorr = num / max(denom, 1e-15)
        mean_reversion = max(-1.0, min(1.0, -lag1_autocorr))
    else:
        mean_reversion = 0.0
    short_window = min(10, n)
    short_clean = clean[-short_window:]
    short_mean = sum(short_clean) / len(short_clean)
    short_var = sum((r - short_mean) ** 2 for r in short_clean) / max(len(short_clean) - 1, 1)
    short_vol = math.sqrt(max(short_var, 0.0))
    full_vol = max(volatility, 1e-8)
    stress_raw = (short_vol / full_vol) - 1.0
    stress = max(0.0, min(1.0, stress_raw * 0.5 + 0.5))
    momentum = max(-1.0, min(1.0, recent_mean / max(full_vol, 1e-8)))
    liquidity = 1.0 - stress
    return {
        "volatility":     volatility,
        "trend_strength": trend_strength,
        "mean_reversion": mean_reversion,
        "stress":         stress,
        "momentum":       momentum,
        "liquidity":      liquidity,
    }


# ---------------------------------------------------------------------------
# Internal helpers (unchanged from v1.1.0)
# ---------------------------------------------------------------------------

def x__extract_regime_features__mutmut_18(returns_history: list) -> dict:
    clean = [r if math.isfinite(r) else 0.0 for r in returns_history]
    n = len(clean)
    mean_r = sum(clean) / n
    variance = sum((r - mean_r) ** 2 for r in clean) / max(n + 1, 1)
    volatility = math.sqrt(max(variance, 0.0))
    window = min(5, n)
    recent = clean[-window:]
    recent_mean = sum(recent) / window
    trend_strength = recent_mean / max(volatility, 1e-8)
    if n >= 2:
        pairs = [(clean[i], clean[i + 1]) for i in range(n - 1)]
        num = sum((a - mean_r) * (b - mean_r) for a, b in pairs)
        denom = sum((r - mean_r) ** 2 for r in clean)
        lag1_autocorr = num / max(denom, 1e-15)
        mean_reversion = max(-1.0, min(1.0, -lag1_autocorr))
    else:
        mean_reversion = 0.0
    short_window = min(10, n)
    short_clean = clean[-short_window:]
    short_mean = sum(short_clean) / len(short_clean)
    short_var = sum((r - short_mean) ** 2 for r in short_clean) / max(len(short_clean) - 1, 1)
    short_vol = math.sqrt(max(short_var, 0.0))
    full_vol = max(volatility, 1e-8)
    stress_raw = (short_vol / full_vol) - 1.0
    stress = max(0.0, min(1.0, stress_raw * 0.5 + 0.5))
    momentum = max(-1.0, min(1.0, recent_mean / max(full_vol, 1e-8)))
    liquidity = 1.0 - stress
    return {
        "volatility":     volatility,
        "trend_strength": trend_strength,
        "mean_reversion": mean_reversion,
        "stress":         stress,
        "momentum":       momentum,
        "liquidity":      liquidity,
    }


# ---------------------------------------------------------------------------
# Internal helpers (unchanged from v1.1.0)
# ---------------------------------------------------------------------------

def x__extract_regime_features__mutmut_19(returns_history: list) -> dict:
    clean = [r if math.isfinite(r) else 0.0 for r in returns_history]
    n = len(clean)
    mean_r = sum(clean) / n
    variance = sum((r - mean_r) ** 2 for r in clean) / max(n - 2, 1)
    volatility = math.sqrt(max(variance, 0.0))
    window = min(5, n)
    recent = clean[-window:]
    recent_mean = sum(recent) / window
    trend_strength = recent_mean / max(volatility, 1e-8)
    if n >= 2:
        pairs = [(clean[i], clean[i + 1]) for i in range(n - 1)]
        num = sum((a - mean_r) * (b - mean_r) for a, b in pairs)
        denom = sum((r - mean_r) ** 2 for r in clean)
        lag1_autocorr = num / max(denom, 1e-15)
        mean_reversion = max(-1.0, min(1.0, -lag1_autocorr))
    else:
        mean_reversion = 0.0
    short_window = min(10, n)
    short_clean = clean[-short_window:]
    short_mean = sum(short_clean) / len(short_clean)
    short_var = sum((r - short_mean) ** 2 for r in short_clean) / max(len(short_clean) - 1, 1)
    short_vol = math.sqrt(max(short_var, 0.0))
    full_vol = max(volatility, 1e-8)
    stress_raw = (short_vol / full_vol) - 1.0
    stress = max(0.0, min(1.0, stress_raw * 0.5 + 0.5))
    momentum = max(-1.0, min(1.0, recent_mean / max(full_vol, 1e-8)))
    liquidity = 1.0 - stress
    return {
        "volatility":     volatility,
        "trend_strength": trend_strength,
        "mean_reversion": mean_reversion,
        "stress":         stress,
        "momentum":       momentum,
        "liquidity":      liquidity,
    }


# ---------------------------------------------------------------------------
# Internal helpers (unchanged from v1.1.0)
# ---------------------------------------------------------------------------

def x__extract_regime_features__mutmut_20(returns_history: list) -> dict:
    clean = [r if math.isfinite(r) else 0.0 for r in returns_history]
    n = len(clean)
    mean_r = sum(clean) / n
    variance = sum((r - mean_r) ** 2 for r in clean) / max(n - 1, 2)
    volatility = math.sqrt(max(variance, 0.0))
    window = min(5, n)
    recent = clean[-window:]
    recent_mean = sum(recent) / window
    trend_strength = recent_mean / max(volatility, 1e-8)
    if n >= 2:
        pairs = [(clean[i], clean[i + 1]) for i in range(n - 1)]
        num = sum((a - mean_r) * (b - mean_r) for a, b in pairs)
        denom = sum((r - mean_r) ** 2 for r in clean)
        lag1_autocorr = num / max(denom, 1e-15)
        mean_reversion = max(-1.0, min(1.0, -lag1_autocorr))
    else:
        mean_reversion = 0.0
    short_window = min(10, n)
    short_clean = clean[-short_window:]
    short_mean = sum(short_clean) / len(short_clean)
    short_var = sum((r - short_mean) ** 2 for r in short_clean) / max(len(short_clean) - 1, 1)
    short_vol = math.sqrt(max(short_var, 0.0))
    full_vol = max(volatility, 1e-8)
    stress_raw = (short_vol / full_vol) - 1.0
    stress = max(0.0, min(1.0, stress_raw * 0.5 + 0.5))
    momentum = max(-1.0, min(1.0, recent_mean / max(full_vol, 1e-8)))
    liquidity = 1.0 - stress
    return {
        "volatility":     volatility,
        "trend_strength": trend_strength,
        "mean_reversion": mean_reversion,
        "stress":         stress,
        "momentum":       momentum,
        "liquidity":      liquidity,
    }


# ---------------------------------------------------------------------------
# Internal helpers (unchanged from v1.1.0)
# ---------------------------------------------------------------------------

def x__extract_regime_features__mutmut_21(returns_history: list) -> dict:
    clean = [r if math.isfinite(r) else 0.0 for r in returns_history]
    n = len(clean)
    mean_r = sum(clean) / n
    variance = sum((r - mean_r) ** 2 for r in clean) / max(n - 1, 1)
    volatility = None
    window = min(5, n)
    recent = clean[-window:]
    recent_mean = sum(recent) / window
    trend_strength = recent_mean / max(volatility, 1e-8)
    if n >= 2:
        pairs = [(clean[i], clean[i + 1]) for i in range(n - 1)]
        num = sum((a - mean_r) * (b - mean_r) for a, b in pairs)
        denom = sum((r - mean_r) ** 2 for r in clean)
        lag1_autocorr = num / max(denom, 1e-15)
        mean_reversion = max(-1.0, min(1.0, -lag1_autocorr))
    else:
        mean_reversion = 0.0
    short_window = min(10, n)
    short_clean = clean[-short_window:]
    short_mean = sum(short_clean) / len(short_clean)
    short_var = sum((r - short_mean) ** 2 for r in short_clean) / max(len(short_clean) - 1, 1)
    short_vol = math.sqrt(max(short_var, 0.0))
    full_vol = max(volatility, 1e-8)
    stress_raw = (short_vol / full_vol) - 1.0
    stress = max(0.0, min(1.0, stress_raw * 0.5 + 0.5))
    momentum = max(-1.0, min(1.0, recent_mean / max(full_vol, 1e-8)))
    liquidity = 1.0 - stress
    return {
        "volatility":     volatility,
        "trend_strength": trend_strength,
        "mean_reversion": mean_reversion,
        "stress":         stress,
        "momentum":       momentum,
        "liquidity":      liquidity,
    }


# ---------------------------------------------------------------------------
# Internal helpers (unchanged from v1.1.0)
# ---------------------------------------------------------------------------

def x__extract_regime_features__mutmut_22(returns_history: list) -> dict:
    clean = [r if math.isfinite(r) else 0.0 for r in returns_history]
    n = len(clean)
    mean_r = sum(clean) / n
    variance = sum((r - mean_r) ** 2 for r in clean) / max(n - 1, 1)
    volatility = math.sqrt(None)
    window = min(5, n)
    recent = clean[-window:]
    recent_mean = sum(recent) / window
    trend_strength = recent_mean / max(volatility, 1e-8)
    if n >= 2:
        pairs = [(clean[i], clean[i + 1]) for i in range(n - 1)]
        num = sum((a - mean_r) * (b - mean_r) for a, b in pairs)
        denom = sum((r - mean_r) ** 2 for r in clean)
        lag1_autocorr = num / max(denom, 1e-15)
        mean_reversion = max(-1.0, min(1.0, -lag1_autocorr))
    else:
        mean_reversion = 0.0
    short_window = min(10, n)
    short_clean = clean[-short_window:]
    short_mean = sum(short_clean) / len(short_clean)
    short_var = sum((r - short_mean) ** 2 for r in short_clean) / max(len(short_clean) - 1, 1)
    short_vol = math.sqrt(max(short_var, 0.0))
    full_vol = max(volatility, 1e-8)
    stress_raw = (short_vol / full_vol) - 1.0
    stress = max(0.0, min(1.0, stress_raw * 0.5 + 0.5))
    momentum = max(-1.0, min(1.0, recent_mean / max(full_vol, 1e-8)))
    liquidity = 1.0 - stress
    return {
        "volatility":     volatility,
        "trend_strength": trend_strength,
        "mean_reversion": mean_reversion,
        "stress":         stress,
        "momentum":       momentum,
        "liquidity":      liquidity,
    }


# ---------------------------------------------------------------------------
# Internal helpers (unchanged from v1.1.0)
# ---------------------------------------------------------------------------

def x__extract_regime_features__mutmut_23(returns_history: list) -> dict:
    clean = [r if math.isfinite(r) else 0.0 for r in returns_history]
    n = len(clean)
    mean_r = sum(clean) / n
    variance = sum((r - mean_r) ** 2 for r in clean) / max(n - 1, 1)
    volatility = math.sqrt(max(None, 0.0))
    window = min(5, n)
    recent = clean[-window:]
    recent_mean = sum(recent) / window
    trend_strength = recent_mean / max(volatility, 1e-8)
    if n >= 2:
        pairs = [(clean[i], clean[i + 1]) for i in range(n - 1)]
        num = sum((a - mean_r) * (b - mean_r) for a, b in pairs)
        denom = sum((r - mean_r) ** 2 for r in clean)
        lag1_autocorr = num / max(denom, 1e-15)
        mean_reversion = max(-1.0, min(1.0, -lag1_autocorr))
    else:
        mean_reversion = 0.0
    short_window = min(10, n)
    short_clean = clean[-short_window:]
    short_mean = sum(short_clean) / len(short_clean)
    short_var = sum((r - short_mean) ** 2 for r in short_clean) / max(len(short_clean) - 1, 1)
    short_vol = math.sqrt(max(short_var, 0.0))
    full_vol = max(volatility, 1e-8)
    stress_raw = (short_vol / full_vol) - 1.0
    stress = max(0.0, min(1.0, stress_raw * 0.5 + 0.5))
    momentum = max(-1.0, min(1.0, recent_mean / max(full_vol, 1e-8)))
    liquidity = 1.0 - stress
    return {
        "volatility":     volatility,
        "trend_strength": trend_strength,
        "mean_reversion": mean_reversion,
        "stress":         stress,
        "momentum":       momentum,
        "liquidity":      liquidity,
    }


# ---------------------------------------------------------------------------
# Internal helpers (unchanged from v1.1.0)
# ---------------------------------------------------------------------------

def x__extract_regime_features__mutmut_24(returns_history: list) -> dict:
    clean = [r if math.isfinite(r) else 0.0 for r in returns_history]
    n = len(clean)
    mean_r = sum(clean) / n
    variance = sum((r - mean_r) ** 2 for r in clean) / max(n - 1, 1)
    volatility = math.sqrt(max(variance, None))
    window = min(5, n)
    recent = clean[-window:]
    recent_mean = sum(recent) / window
    trend_strength = recent_mean / max(volatility, 1e-8)
    if n >= 2:
        pairs = [(clean[i], clean[i + 1]) for i in range(n - 1)]
        num = sum((a - mean_r) * (b - mean_r) for a, b in pairs)
        denom = sum((r - mean_r) ** 2 for r in clean)
        lag1_autocorr = num / max(denom, 1e-15)
        mean_reversion = max(-1.0, min(1.0, -lag1_autocorr))
    else:
        mean_reversion = 0.0
    short_window = min(10, n)
    short_clean = clean[-short_window:]
    short_mean = sum(short_clean) / len(short_clean)
    short_var = sum((r - short_mean) ** 2 for r in short_clean) / max(len(short_clean) - 1, 1)
    short_vol = math.sqrt(max(short_var, 0.0))
    full_vol = max(volatility, 1e-8)
    stress_raw = (short_vol / full_vol) - 1.0
    stress = max(0.0, min(1.0, stress_raw * 0.5 + 0.5))
    momentum = max(-1.0, min(1.0, recent_mean / max(full_vol, 1e-8)))
    liquidity = 1.0 - stress
    return {
        "volatility":     volatility,
        "trend_strength": trend_strength,
        "mean_reversion": mean_reversion,
        "stress":         stress,
        "momentum":       momentum,
        "liquidity":      liquidity,
    }


# ---------------------------------------------------------------------------
# Internal helpers (unchanged from v1.1.0)
# ---------------------------------------------------------------------------

def x__extract_regime_features__mutmut_25(returns_history: list) -> dict:
    clean = [r if math.isfinite(r) else 0.0 for r in returns_history]
    n = len(clean)
    mean_r = sum(clean) / n
    variance = sum((r - mean_r) ** 2 for r in clean) / max(n - 1, 1)
    volatility = math.sqrt(max(0.0))
    window = min(5, n)
    recent = clean[-window:]
    recent_mean = sum(recent) / window
    trend_strength = recent_mean / max(volatility, 1e-8)
    if n >= 2:
        pairs = [(clean[i], clean[i + 1]) for i in range(n - 1)]
        num = sum((a - mean_r) * (b - mean_r) for a, b in pairs)
        denom = sum((r - mean_r) ** 2 for r in clean)
        lag1_autocorr = num / max(denom, 1e-15)
        mean_reversion = max(-1.0, min(1.0, -lag1_autocorr))
    else:
        mean_reversion = 0.0
    short_window = min(10, n)
    short_clean = clean[-short_window:]
    short_mean = sum(short_clean) / len(short_clean)
    short_var = sum((r - short_mean) ** 2 for r in short_clean) / max(len(short_clean) - 1, 1)
    short_vol = math.sqrt(max(short_var, 0.0))
    full_vol = max(volatility, 1e-8)
    stress_raw = (short_vol / full_vol) - 1.0
    stress = max(0.0, min(1.0, stress_raw * 0.5 + 0.5))
    momentum = max(-1.0, min(1.0, recent_mean / max(full_vol, 1e-8)))
    liquidity = 1.0 - stress
    return {
        "volatility":     volatility,
        "trend_strength": trend_strength,
        "mean_reversion": mean_reversion,
        "stress":         stress,
        "momentum":       momentum,
        "liquidity":      liquidity,
    }


# ---------------------------------------------------------------------------
# Internal helpers (unchanged from v1.1.0)
# ---------------------------------------------------------------------------

def x__extract_regime_features__mutmut_26(returns_history: list) -> dict:
    clean = [r if math.isfinite(r) else 0.0 for r in returns_history]
    n = len(clean)
    mean_r = sum(clean) / n
    variance = sum((r - mean_r) ** 2 for r in clean) / max(n - 1, 1)
    volatility = math.sqrt(max(variance, ))
    window = min(5, n)
    recent = clean[-window:]
    recent_mean = sum(recent) / window
    trend_strength = recent_mean / max(volatility, 1e-8)
    if n >= 2:
        pairs = [(clean[i], clean[i + 1]) for i in range(n - 1)]
        num = sum((a - mean_r) * (b - mean_r) for a, b in pairs)
        denom = sum((r - mean_r) ** 2 for r in clean)
        lag1_autocorr = num / max(denom, 1e-15)
        mean_reversion = max(-1.0, min(1.0, -lag1_autocorr))
    else:
        mean_reversion = 0.0
    short_window = min(10, n)
    short_clean = clean[-short_window:]
    short_mean = sum(short_clean) / len(short_clean)
    short_var = sum((r - short_mean) ** 2 for r in short_clean) / max(len(short_clean) - 1, 1)
    short_vol = math.sqrt(max(short_var, 0.0))
    full_vol = max(volatility, 1e-8)
    stress_raw = (short_vol / full_vol) - 1.0
    stress = max(0.0, min(1.0, stress_raw * 0.5 + 0.5))
    momentum = max(-1.0, min(1.0, recent_mean / max(full_vol, 1e-8)))
    liquidity = 1.0 - stress
    return {
        "volatility":     volatility,
        "trend_strength": trend_strength,
        "mean_reversion": mean_reversion,
        "stress":         stress,
        "momentum":       momentum,
        "liquidity":      liquidity,
    }


# ---------------------------------------------------------------------------
# Internal helpers (unchanged from v1.1.0)
# ---------------------------------------------------------------------------

def x__extract_regime_features__mutmut_27(returns_history: list) -> dict:
    clean = [r if math.isfinite(r) else 0.0 for r in returns_history]
    n = len(clean)
    mean_r = sum(clean) / n
    variance = sum((r - mean_r) ** 2 for r in clean) / max(n - 1, 1)
    volatility = math.sqrt(max(variance, 1.0))
    window = min(5, n)
    recent = clean[-window:]
    recent_mean = sum(recent) / window
    trend_strength = recent_mean / max(volatility, 1e-8)
    if n >= 2:
        pairs = [(clean[i], clean[i + 1]) for i in range(n - 1)]
        num = sum((a - mean_r) * (b - mean_r) for a, b in pairs)
        denom = sum((r - mean_r) ** 2 for r in clean)
        lag1_autocorr = num / max(denom, 1e-15)
        mean_reversion = max(-1.0, min(1.0, -lag1_autocorr))
    else:
        mean_reversion = 0.0
    short_window = min(10, n)
    short_clean = clean[-short_window:]
    short_mean = sum(short_clean) / len(short_clean)
    short_var = sum((r - short_mean) ** 2 for r in short_clean) / max(len(short_clean) - 1, 1)
    short_vol = math.sqrt(max(short_var, 0.0))
    full_vol = max(volatility, 1e-8)
    stress_raw = (short_vol / full_vol) - 1.0
    stress = max(0.0, min(1.0, stress_raw * 0.5 + 0.5))
    momentum = max(-1.0, min(1.0, recent_mean / max(full_vol, 1e-8)))
    liquidity = 1.0 - stress
    return {
        "volatility":     volatility,
        "trend_strength": trend_strength,
        "mean_reversion": mean_reversion,
        "stress":         stress,
        "momentum":       momentum,
        "liquidity":      liquidity,
    }


# ---------------------------------------------------------------------------
# Internal helpers (unchanged from v1.1.0)
# ---------------------------------------------------------------------------

def x__extract_regime_features__mutmut_28(returns_history: list) -> dict:
    clean = [r if math.isfinite(r) else 0.0 for r in returns_history]
    n = len(clean)
    mean_r = sum(clean) / n
    variance = sum((r - mean_r) ** 2 for r in clean) / max(n - 1, 1)
    volatility = math.sqrt(max(variance, 0.0))
    window = None
    recent = clean[-window:]
    recent_mean = sum(recent) / window
    trend_strength = recent_mean / max(volatility, 1e-8)
    if n >= 2:
        pairs = [(clean[i], clean[i + 1]) for i in range(n - 1)]
        num = sum((a - mean_r) * (b - mean_r) for a, b in pairs)
        denom = sum((r - mean_r) ** 2 for r in clean)
        lag1_autocorr = num / max(denom, 1e-15)
        mean_reversion = max(-1.0, min(1.0, -lag1_autocorr))
    else:
        mean_reversion = 0.0
    short_window = min(10, n)
    short_clean = clean[-short_window:]
    short_mean = sum(short_clean) / len(short_clean)
    short_var = sum((r - short_mean) ** 2 for r in short_clean) / max(len(short_clean) - 1, 1)
    short_vol = math.sqrt(max(short_var, 0.0))
    full_vol = max(volatility, 1e-8)
    stress_raw = (short_vol / full_vol) - 1.0
    stress = max(0.0, min(1.0, stress_raw * 0.5 + 0.5))
    momentum = max(-1.0, min(1.0, recent_mean / max(full_vol, 1e-8)))
    liquidity = 1.0 - stress
    return {
        "volatility":     volatility,
        "trend_strength": trend_strength,
        "mean_reversion": mean_reversion,
        "stress":         stress,
        "momentum":       momentum,
        "liquidity":      liquidity,
    }


# ---------------------------------------------------------------------------
# Internal helpers (unchanged from v1.1.0)
# ---------------------------------------------------------------------------

def x__extract_regime_features__mutmut_29(returns_history: list) -> dict:
    clean = [r if math.isfinite(r) else 0.0 for r in returns_history]
    n = len(clean)
    mean_r = sum(clean) / n
    variance = sum((r - mean_r) ** 2 for r in clean) / max(n - 1, 1)
    volatility = math.sqrt(max(variance, 0.0))
    window = min(None, n)
    recent = clean[-window:]
    recent_mean = sum(recent) / window
    trend_strength = recent_mean / max(volatility, 1e-8)
    if n >= 2:
        pairs = [(clean[i], clean[i + 1]) for i in range(n - 1)]
        num = sum((a - mean_r) * (b - mean_r) for a, b in pairs)
        denom = sum((r - mean_r) ** 2 for r in clean)
        lag1_autocorr = num / max(denom, 1e-15)
        mean_reversion = max(-1.0, min(1.0, -lag1_autocorr))
    else:
        mean_reversion = 0.0
    short_window = min(10, n)
    short_clean = clean[-short_window:]
    short_mean = sum(short_clean) / len(short_clean)
    short_var = sum((r - short_mean) ** 2 for r in short_clean) / max(len(short_clean) - 1, 1)
    short_vol = math.sqrt(max(short_var, 0.0))
    full_vol = max(volatility, 1e-8)
    stress_raw = (short_vol / full_vol) - 1.0
    stress = max(0.0, min(1.0, stress_raw * 0.5 + 0.5))
    momentum = max(-1.0, min(1.0, recent_mean / max(full_vol, 1e-8)))
    liquidity = 1.0 - stress
    return {
        "volatility":     volatility,
        "trend_strength": trend_strength,
        "mean_reversion": mean_reversion,
        "stress":         stress,
        "momentum":       momentum,
        "liquidity":      liquidity,
    }


# ---------------------------------------------------------------------------
# Internal helpers (unchanged from v1.1.0)
# ---------------------------------------------------------------------------

def x__extract_regime_features__mutmut_30(returns_history: list) -> dict:
    clean = [r if math.isfinite(r) else 0.0 for r in returns_history]
    n = len(clean)
    mean_r = sum(clean) / n
    variance = sum((r - mean_r) ** 2 for r in clean) / max(n - 1, 1)
    volatility = math.sqrt(max(variance, 0.0))
    window = min(5, None)
    recent = clean[-window:]
    recent_mean = sum(recent) / window
    trend_strength = recent_mean / max(volatility, 1e-8)
    if n >= 2:
        pairs = [(clean[i], clean[i + 1]) for i in range(n - 1)]
        num = sum((a - mean_r) * (b - mean_r) for a, b in pairs)
        denom = sum((r - mean_r) ** 2 for r in clean)
        lag1_autocorr = num / max(denom, 1e-15)
        mean_reversion = max(-1.0, min(1.0, -lag1_autocorr))
    else:
        mean_reversion = 0.0
    short_window = min(10, n)
    short_clean = clean[-short_window:]
    short_mean = sum(short_clean) / len(short_clean)
    short_var = sum((r - short_mean) ** 2 for r in short_clean) / max(len(short_clean) - 1, 1)
    short_vol = math.sqrt(max(short_var, 0.0))
    full_vol = max(volatility, 1e-8)
    stress_raw = (short_vol / full_vol) - 1.0
    stress = max(0.0, min(1.0, stress_raw * 0.5 + 0.5))
    momentum = max(-1.0, min(1.0, recent_mean / max(full_vol, 1e-8)))
    liquidity = 1.0 - stress
    return {
        "volatility":     volatility,
        "trend_strength": trend_strength,
        "mean_reversion": mean_reversion,
        "stress":         stress,
        "momentum":       momentum,
        "liquidity":      liquidity,
    }


# ---------------------------------------------------------------------------
# Internal helpers (unchanged from v1.1.0)
# ---------------------------------------------------------------------------

def x__extract_regime_features__mutmut_31(returns_history: list) -> dict:
    clean = [r if math.isfinite(r) else 0.0 for r in returns_history]
    n = len(clean)
    mean_r = sum(clean) / n
    variance = sum((r - mean_r) ** 2 for r in clean) / max(n - 1, 1)
    volatility = math.sqrt(max(variance, 0.0))
    window = min(n)
    recent = clean[-window:]
    recent_mean = sum(recent) / window
    trend_strength = recent_mean / max(volatility, 1e-8)
    if n >= 2:
        pairs = [(clean[i], clean[i + 1]) for i in range(n - 1)]
        num = sum((a - mean_r) * (b - mean_r) for a, b in pairs)
        denom = sum((r - mean_r) ** 2 for r in clean)
        lag1_autocorr = num / max(denom, 1e-15)
        mean_reversion = max(-1.0, min(1.0, -lag1_autocorr))
    else:
        mean_reversion = 0.0
    short_window = min(10, n)
    short_clean = clean[-short_window:]
    short_mean = sum(short_clean) / len(short_clean)
    short_var = sum((r - short_mean) ** 2 for r in short_clean) / max(len(short_clean) - 1, 1)
    short_vol = math.sqrt(max(short_var, 0.0))
    full_vol = max(volatility, 1e-8)
    stress_raw = (short_vol / full_vol) - 1.0
    stress = max(0.0, min(1.0, stress_raw * 0.5 + 0.5))
    momentum = max(-1.0, min(1.0, recent_mean / max(full_vol, 1e-8)))
    liquidity = 1.0 - stress
    return {
        "volatility":     volatility,
        "trend_strength": trend_strength,
        "mean_reversion": mean_reversion,
        "stress":         stress,
        "momentum":       momentum,
        "liquidity":      liquidity,
    }


# ---------------------------------------------------------------------------
# Internal helpers (unchanged from v1.1.0)
# ---------------------------------------------------------------------------

def x__extract_regime_features__mutmut_32(returns_history: list) -> dict:
    clean = [r if math.isfinite(r) else 0.0 for r in returns_history]
    n = len(clean)
    mean_r = sum(clean) / n
    variance = sum((r - mean_r) ** 2 for r in clean) / max(n - 1, 1)
    volatility = math.sqrt(max(variance, 0.0))
    window = min(5, )
    recent = clean[-window:]
    recent_mean = sum(recent) / window
    trend_strength = recent_mean / max(volatility, 1e-8)
    if n >= 2:
        pairs = [(clean[i], clean[i + 1]) for i in range(n - 1)]
        num = sum((a - mean_r) * (b - mean_r) for a, b in pairs)
        denom = sum((r - mean_r) ** 2 for r in clean)
        lag1_autocorr = num / max(denom, 1e-15)
        mean_reversion = max(-1.0, min(1.0, -lag1_autocorr))
    else:
        mean_reversion = 0.0
    short_window = min(10, n)
    short_clean = clean[-short_window:]
    short_mean = sum(short_clean) / len(short_clean)
    short_var = sum((r - short_mean) ** 2 for r in short_clean) / max(len(short_clean) - 1, 1)
    short_vol = math.sqrt(max(short_var, 0.0))
    full_vol = max(volatility, 1e-8)
    stress_raw = (short_vol / full_vol) - 1.0
    stress = max(0.0, min(1.0, stress_raw * 0.5 + 0.5))
    momentum = max(-1.0, min(1.0, recent_mean / max(full_vol, 1e-8)))
    liquidity = 1.0 - stress
    return {
        "volatility":     volatility,
        "trend_strength": trend_strength,
        "mean_reversion": mean_reversion,
        "stress":         stress,
        "momentum":       momentum,
        "liquidity":      liquidity,
    }


# ---------------------------------------------------------------------------
# Internal helpers (unchanged from v1.1.0)
# ---------------------------------------------------------------------------

def x__extract_regime_features__mutmut_33(returns_history: list) -> dict:
    clean = [r if math.isfinite(r) else 0.0 for r in returns_history]
    n = len(clean)
    mean_r = sum(clean) / n
    variance = sum((r - mean_r) ** 2 for r in clean) / max(n - 1, 1)
    volatility = math.sqrt(max(variance, 0.0))
    window = min(6, n)
    recent = clean[-window:]
    recent_mean = sum(recent) / window
    trend_strength = recent_mean / max(volatility, 1e-8)
    if n >= 2:
        pairs = [(clean[i], clean[i + 1]) for i in range(n - 1)]
        num = sum((a - mean_r) * (b - mean_r) for a, b in pairs)
        denom = sum((r - mean_r) ** 2 for r in clean)
        lag1_autocorr = num / max(denom, 1e-15)
        mean_reversion = max(-1.0, min(1.0, -lag1_autocorr))
    else:
        mean_reversion = 0.0
    short_window = min(10, n)
    short_clean = clean[-short_window:]
    short_mean = sum(short_clean) / len(short_clean)
    short_var = sum((r - short_mean) ** 2 for r in short_clean) / max(len(short_clean) - 1, 1)
    short_vol = math.sqrt(max(short_var, 0.0))
    full_vol = max(volatility, 1e-8)
    stress_raw = (short_vol / full_vol) - 1.0
    stress = max(0.0, min(1.0, stress_raw * 0.5 + 0.5))
    momentum = max(-1.0, min(1.0, recent_mean / max(full_vol, 1e-8)))
    liquidity = 1.0 - stress
    return {
        "volatility":     volatility,
        "trend_strength": trend_strength,
        "mean_reversion": mean_reversion,
        "stress":         stress,
        "momentum":       momentum,
        "liquidity":      liquidity,
    }


# ---------------------------------------------------------------------------
# Internal helpers (unchanged from v1.1.0)
# ---------------------------------------------------------------------------

def x__extract_regime_features__mutmut_34(returns_history: list) -> dict:
    clean = [r if math.isfinite(r) else 0.0 for r in returns_history]
    n = len(clean)
    mean_r = sum(clean) / n
    variance = sum((r - mean_r) ** 2 for r in clean) / max(n - 1, 1)
    volatility = math.sqrt(max(variance, 0.0))
    window = min(5, n)
    recent = None
    recent_mean = sum(recent) / window
    trend_strength = recent_mean / max(volatility, 1e-8)
    if n >= 2:
        pairs = [(clean[i], clean[i + 1]) for i in range(n - 1)]
        num = sum((a - mean_r) * (b - mean_r) for a, b in pairs)
        denom = sum((r - mean_r) ** 2 for r in clean)
        lag1_autocorr = num / max(denom, 1e-15)
        mean_reversion = max(-1.0, min(1.0, -lag1_autocorr))
    else:
        mean_reversion = 0.0
    short_window = min(10, n)
    short_clean = clean[-short_window:]
    short_mean = sum(short_clean) / len(short_clean)
    short_var = sum((r - short_mean) ** 2 for r in short_clean) / max(len(short_clean) - 1, 1)
    short_vol = math.sqrt(max(short_var, 0.0))
    full_vol = max(volatility, 1e-8)
    stress_raw = (short_vol / full_vol) - 1.0
    stress = max(0.0, min(1.0, stress_raw * 0.5 + 0.5))
    momentum = max(-1.0, min(1.0, recent_mean / max(full_vol, 1e-8)))
    liquidity = 1.0 - stress
    return {
        "volatility":     volatility,
        "trend_strength": trend_strength,
        "mean_reversion": mean_reversion,
        "stress":         stress,
        "momentum":       momentum,
        "liquidity":      liquidity,
    }


# ---------------------------------------------------------------------------
# Internal helpers (unchanged from v1.1.0)
# ---------------------------------------------------------------------------

def x__extract_regime_features__mutmut_35(returns_history: list) -> dict:
    clean = [r if math.isfinite(r) else 0.0 for r in returns_history]
    n = len(clean)
    mean_r = sum(clean) / n
    variance = sum((r - mean_r) ** 2 for r in clean) / max(n - 1, 1)
    volatility = math.sqrt(max(variance, 0.0))
    window = min(5, n)
    recent = clean[+window:]
    recent_mean = sum(recent) / window
    trend_strength = recent_mean / max(volatility, 1e-8)
    if n >= 2:
        pairs = [(clean[i], clean[i + 1]) for i in range(n - 1)]
        num = sum((a - mean_r) * (b - mean_r) for a, b in pairs)
        denom = sum((r - mean_r) ** 2 for r in clean)
        lag1_autocorr = num / max(denom, 1e-15)
        mean_reversion = max(-1.0, min(1.0, -lag1_autocorr))
    else:
        mean_reversion = 0.0
    short_window = min(10, n)
    short_clean = clean[-short_window:]
    short_mean = sum(short_clean) / len(short_clean)
    short_var = sum((r - short_mean) ** 2 for r in short_clean) / max(len(short_clean) - 1, 1)
    short_vol = math.sqrt(max(short_var, 0.0))
    full_vol = max(volatility, 1e-8)
    stress_raw = (short_vol / full_vol) - 1.0
    stress = max(0.0, min(1.0, stress_raw * 0.5 + 0.5))
    momentum = max(-1.0, min(1.0, recent_mean / max(full_vol, 1e-8)))
    liquidity = 1.0 - stress
    return {
        "volatility":     volatility,
        "trend_strength": trend_strength,
        "mean_reversion": mean_reversion,
        "stress":         stress,
        "momentum":       momentum,
        "liquidity":      liquidity,
    }


# ---------------------------------------------------------------------------
# Internal helpers (unchanged from v1.1.0)
# ---------------------------------------------------------------------------

def x__extract_regime_features__mutmut_36(returns_history: list) -> dict:
    clean = [r if math.isfinite(r) else 0.0 for r in returns_history]
    n = len(clean)
    mean_r = sum(clean) / n
    variance = sum((r - mean_r) ** 2 for r in clean) / max(n - 1, 1)
    volatility = math.sqrt(max(variance, 0.0))
    window = min(5, n)
    recent = clean[-window:]
    recent_mean = None
    trend_strength = recent_mean / max(volatility, 1e-8)
    if n >= 2:
        pairs = [(clean[i], clean[i + 1]) for i in range(n - 1)]
        num = sum((a - mean_r) * (b - mean_r) for a, b in pairs)
        denom = sum((r - mean_r) ** 2 for r in clean)
        lag1_autocorr = num / max(denom, 1e-15)
        mean_reversion = max(-1.0, min(1.0, -lag1_autocorr))
    else:
        mean_reversion = 0.0
    short_window = min(10, n)
    short_clean = clean[-short_window:]
    short_mean = sum(short_clean) / len(short_clean)
    short_var = sum((r - short_mean) ** 2 for r in short_clean) / max(len(short_clean) - 1, 1)
    short_vol = math.sqrt(max(short_var, 0.0))
    full_vol = max(volatility, 1e-8)
    stress_raw = (short_vol / full_vol) - 1.0
    stress = max(0.0, min(1.0, stress_raw * 0.5 + 0.5))
    momentum = max(-1.0, min(1.0, recent_mean / max(full_vol, 1e-8)))
    liquidity = 1.0 - stress
    return {
        "volatility":     volatility,
        "trend_strength": trend_strength,
        "mean_reversion": mean_reversion,
        "stress":         stress,
        "momentum":       momentum,
        "liquidity":      liquidity,
    }


# ---------------------------------------------------------------------------
# Internal helpers (unchanged from v1.1.0)
# ---------------------------------------------------------------------------

def x__extract_regime_features__mutmut_37(returns_history: list) -> dict:
    clean = [r if math.isfinite(r) else 0.0 for r in returns_history]
    n = len(clean)
    mean_r = sum(clean) / n
    variance = sum((r - mean_r) ** 2 for r in clean) / max(n - 1, 1)
    volatility = math.sqrt(max(variance, 0.0))
    window = min(5, n)
    recent = clean[-window:]
    recent_mean = sum(recent) * window
    trend_strength = recent_mean / max(volatility, 1e-8)
    if n >= 2:
        pairs = [(clean[i], clean[i + 1]) for i in range(n - 1)]
        num = sum((a - mean_r) * (b - mean_r) for a, b in pairs)
        denom = sum((r - mean_r) ** 2 for r in clean)
        lag1_autocorr = num / max(denom, 1e-15)
        mean_reversion = max(-1.0, min(1.0, -lag1_autocorr))
    else:
        mean_reversion = 0.0
    short_window = min(10, n)
    short_clean = clean[-short_window:]
    short_mean = sum(short_clean) / len(short_clean)
    short_var = sum((r - short_mean) ** 2 for r in short_clean) / max(len(short_clean) - 1, 1)
    short_vol = math.sqrt(max(short_var, 0.0))
    full_vol = max(volatility, 1e-8)
    stress_raw = (short_vol / full_vol) - 1.0
    stress = max(0.0, min(1.0, stress_raw * 0.5 + 0.5))
    momentum = max(-1.0, min(1.0, recent_mean / max(full_vol, 1e-8)))
    liquidity = 1.0 - stress
    return {
        "volatility":     volatility,
        "trend_strength": trend_strength,
        "mean_reversion": mean_reversion,
        "stress":         stress,
        "momentum":       momentum,
        "liquidity":      liquidity,
    }


# ---------------------------------------------------------------------------
# Internal helpers (unchanged from v1.1.0)
# ---------------------------------------------------------------------------

def x__extract_regime_features__mutmut_38(returns_history: list) -> dict:
    clean = [r if math.isfinite(r) else 0.0 for r in returns_history]
    n = len(clean)
    mean_r = sum(clean) / n
    variance = sum((r - mean_r) ** 2 for r in clean) / max(n - 1, 1)
    volatility = math.sqrt(max(variance, 0.0))
    window = min(5, n)
    recent = clean[-window:]
    recent_mean = sum(None) / window
    trend_strength = recent_mean / max(volatility, 1e-8)
    if n >= 2:
        pairs = [(clean[i], clean[i + 1]) for i in range(n - 1)]
        num = sum((a - mean_r) * (b - mean_r) for a, b in pairs)
        denom = sum((r - mean_r) ** 2 for r in clean)
        lag1_autocorr = num / max(denom, 1e-15)
        mean_reversion = max(-1.0, min(1.0, -lag1_autocorr))
    else:
        mean_reversion = 0.0
    short_window = min(10, n)
    short_clean = clean[-short_window:]
    short_mean = sum(short_clean) / len(short_clean)
    short_var = sum((r - short_mean) ** 2 for r in short_clean) / max(len(short_clean) - 1, 1)
    short_vol = math.sqrt(max(short_var, 0.0))
    full_vol = max(volatility, 1e-8)
    stress_raw = (short_vol / full_vol) - 1.0
    stress = max(0.0, min(1.0, stress_raw * 0.5 + 0.5))
    momentum = max(-1.0, min(1.0, recent_mean / max(full_vol, 1e-8)))
    liquidity = 1.0 - stress
    return {
        "volatility":     volatility,
        "trend_strength": trend_strength,
        "mean_reversion": mean_reversion,
        "stress":         stress,
        "momentum":       momentum,
        "liquidity":      liquidity,
    }


# ---------------------------------------------------------------------------
# Internal helpers (unchanged from v1.1.0)
# ---------------------------------------------------------------------------

def x__extract_regime_features__mutmut_39(returns_history: list) -> dict:
    clean = [r if math.isfinite(r) else 0.0 for r in returns_history]
    n = len(clean)
    mean_r = sum(clean) / n
    variance = sum((r - mean_r) ** 2 for r in clean) / max(n - 1, 1)
    volatility = math.sqrt(max(variance, 0.0))
    window = min(5, n)
    recent = clean[-window:]
    recent_mean = sum(recent) / window
    trend_strength = None
    if n >= 2:
        pairs = [(clean[i], clean[i + 1]) for i in range(n - 1)]
        num = sum((a - mean_r) * (b - mean_r) for a, b in pairs)
        denom = sum((r - mean_r) ** 2 for r in clean)
        lag1_autocorr = num / max(denom, 1e-15)
        mean_reversion = max(-1.0, min(1.0, -lag1_autocorr))
    else:
        mean_reversion = 0.0
    short_window = min(10, n)
    short_clean = clean[-short_window:]
    short_mean = sum(short_clean) / len(short_clean)
    short_var = sum((r - short_mean) ** 2 for r in short_clean) / max(len(short_clean) - 1, 1)
    short_vol = math.sqrt(max(short_var, 0.0))
    full_vol = max(volatility, 1e-8)
    stress_raw = (short_vol / full_vol) - 1.0
    stress = max(0.0, min(1.0, stress_raw * 0.5 + 0.5))
    momentum = max(-1.0, min(1.0, recent_mean / max(full_vol, 1e-8)))
    liquidity = 1.0 - stress
    return {
        "volatility":     volatility,
        "trend_strength": trend_strength,
        "mean_reversion": mean_reversion,
        "stress":         stress,
        "momentum":       momentum,
        "liquidity":      liquidity,
    }


# ---------------------------------------------------------------------------
# Internal helpers (unchanged from v1.1.0)
# ---------------------------------------------------------------------------

def x__extract_regime_features__mutmut_40(returns_history: list) -> dict:
    clean = [r if math.isfinite(r) else 0.0 for r in returns_history]
    n = len(clean)
    mean_r = sum(clean) / n
    variance = sum((r - mean_r) ** 2 for r in clean) / max(n - 1, 1)
    volatility = math.sqrt(max(variance, 0.0))
    window = min(5, n)
    recent = clean[-window:]
    recent_mean = sum(recent) / window
    trend_strength = recent_mean * max(volatility, 1e-8)
    if n >= 2:
        pairs = [(clean[i], clean[i + 1]) for i in range(n - 1)]
        num = sum((a - mean_r) * (b - mean_r) for a, b in pairs)
        denom = sum((r - mean_r) ** 2 for r in clean)
        lag1_autocorr = num / max(denom, 1e-15)
        mean_reversion = max(-1.0, min(1.0, -lag1_autocorr))
    else:
        mean_reversion = 0.0
    short_window = min(10, n)
    short_clean = clean[-short_window:]
    short_mean = sum(short_clean) / len(short_clean)
    short_var = sum((r - short_mean) ** 2 for r in short_clean) / max(len(short_clean) - 1, 1)
    short_vol = math.sqrt(max(short_var, 0.0))
    full_vol = max(volatility, 1e-8)
    stress_raw = (short_vol / full_vol) - 1.0
    stress = max(0.0, min(1.0, stress_raw * 0.5 + 0.5))
    momentum = max(-1.0, min(1.0, recent_mean / max(full_vol, 1e-8)))
    liquidity = 1.0 - stress
    return {
        "volatility":     volatility,
        "trend_strength": trend_strength,
        "mean_reversion": mean_reversion,
        "stress":         stress,
        "momentum":       momentum,
        "liquidity":      liquidity,
    }


# ---------------------------------------------------------------------------
# Internal helpers (unchanged from v1.1.0)
# ---------------------------------------------------------------------------

def x__extract_regime_features__mutmut_41(returns_history: list) -> dict:
    clean = [r if math.isfinite(r) else 0.0 for r in returns_history]
    n = len(clean)
    mean_r = sum(clean) / n
    variance = sum((r - mean_r) ** 2 for r in clean) / max(n - 1, 1)
    volatility = math.sqrt(max(variance, 0.0))
    window = min(5, n)
    recent = clean[-window:]
    recent_mean = sum(recent) / window
    trend_strength = recent_mean / max(None, 1e-8)
    if n >= 2:
        pairs = [(clean[i], clean[i + 1]) for i in range(n - 1)]
        num = sum((a - mean_r) * (b - mean_r) for a, b in pairs)
        denom = sum((r - mean_r) ** 2 for r in clean)
        lag1_autocorr = num / max(denom, 1e-15)
        mean_reversion = max(-1.0, min(1.0, -lag1_autocorr))
    else:
        mean_reversion = 0.0
    short_window = min(10, n)
    short_clean = clean[-short_window:]
    short_mean = sum(short_clean) / len(short_clean)
    short_var = sum((r - short_mean) ** 2 for r in short_clean) / max(len(short_clean) - 1, 1)
    short_vol = math.sqrt(max(short_var, 0.0))
    full_vol = max(volatility, 1e-8)
    stress_raw = (short_vol / full_vol) - 1.0
    stress = max(0.0, min(1.0, stress_raw * 0.5 + 0.5))
    momentum = max(-1.0, min(1.0, recent_mean / max(full_vol, 1e-8)))
    liquidity = 1.0 - stress
    return {
        "volatility":     volatility,
        "trend_strength": trend_strength,
        "mean_reversion": mean_reversion,
        "stress":         stress,
        "momentum":       momentum,
        "liquidity":      liquidity,
    }


# ---------------------------------------------------------------------------
# Internal helpers (unchanged from v1.1.0)
# ---------------------------------------------------------------------------

def x__extract_regime_features__mutmut_42(returns_history: list) -> dict:
    clean = [r if math.isfinite(r) else 0.0 for r in returns_history]
    n = len(clean)
    mean_r = sum(clean) / n
    variance = sum((r - mean_r) ** 2 for r in clean) / max(n - 1, 1)
    volatility = math.sqrt(max(variance, 0.0))
    window = min(5, n)
    recent = clean[-window:]
    recent_mean = sum(recent) / window
    trend_strength = recent_mean / max(volatility, None)
    if n >= 2:
        pairs = [(clean[i], clean[i + 1]) for i in range(n - 1)]
        num = sum((a - mean_r) * (b - mean_r) for a, b in pairs)
        denom = sum((r - mean_r) ** 2 for r in clean)
        lag1_autocorr = num / max(denom, 1e-15)
        mean_reversion = max(-1.0, min(1.0, -lag1_autocorr))
    else:
        mean_reversion = 0.0
    short_window = min(10, n)
    short_clean = clean[-short_window:]
    short_mean = sum(short_clean) / len(short_clean)
    short_var = sum((r - short_mean) ** 2 for r in short_clean) / max(len(short_clean) - 1, 1)
    short_vol = math.sqrt(max(short_var, 0.0))
    full_vol = max(volatility, 1e-8)
    stress_raw = (short_vol / full_vol) - 1.0
    stress = max(0.0, min(1.0, stress_raw * 0.5 + 0.5))
    momentum = max(-1.0, min(1.0, recent_mean / max(full_vol, 1e-8)))
    liquidity = 1.0 - stress
    return {
        "volatility":     volatility,
        "trend_strength": trend_strength,
        "mean_reversion": mean_reversion,
        "stress":         stress,
        "momentum":       momentum,
        "liquidity":      liquidity,
    }


# ---------------------------------------------------------------------------
# Internal helpers (unchanged from v1.1.0)
# ---------------------------------------------------------------------------

def x__extract_regime_features__mutmut_43(returns_history: list) -> dict:
    clean = [r if math.isfinite(r) else 0.0 for r in returns_history]
    n = len(clean)
    mean_r = sum(clean) / n
    variance = sum((r - mean_r) ** 2 for r in clean) / max(n - 1, 1)
    volatility = math.sqrt(max(variance, 0.0))
    window = min(5, n)
    recent = clean[-window:]
    recent_mean = sum(recent) / window
    trend_strength = recent_mean / max(1e-8)
    if n >= 2:
        pairs = [(clean[i], clean[i + 1]) for i in range(n - 1)]
        num = sum((a - mean_r) * (b - mean_r) for a, b in pairs)
        denom = sum((r - mean_r) ** 2 for r in clean)
        lag1_autocorr = num / max(denom, 1e-15)
        mean_reversion = max(-1.0, min(1.0, -lag1_autocorr))
    else:
        mean_reversion = 0.0
    short_window = min(10, n)
    short_clean = clean[-short_window:]
    short_mean = sum(short_clean) / len(short_clean)
    short_var = sum((r - short_mean) ** 2 for r in short_clean) / max(len(short_clean) - 1, 1)
    short_vol = math.sqrt(max(short_var, 0.0))
    full_vol = max(volatility, 1e-8)
    stress_raw = (short_vol / full_vol) - 1.0
    stress = max(0.0, min(1.0, stress_raw * 0.5 + 0.5))
    momentum = max(-1.0, min(1.0, recent_mean / max(full_vol, 1e-8)))
    liquidity = 1.0 - stress
    return {
        "volatility":     volatility,
        "trend_strength": trend_strength,
        "mean_reversion": mean_reversion,
        "stress":         stress,
        "momentum":       momentum,
        "liquidity":      liquidity,
    }


# ---------------------------------------------------------------------------
# Internal helpers (unchanged from v1.1.0)
# ---------------------------------------------------------------------------

def x__extract_regime_features__mutmut_44(returns_history: list) -> dict:
    clean = [r if math.isfinite(r) else 0.0 for r in returns_history]
    n = len(clean)
    mean_r = sum(clean) / n
    variance = sum((r - mean_r) ** 2 for r in clean) / max(n - 1, 1)
    volatility = math.sqrt(max(variance, 0.0))
    window = min(5, n)
    recent = clean[-window:]
    recent_mean = sum(recent) / window
    trend_strength = recent_mean / max(volatility, )
    if n >= 2:
        pairs = [(clean[i], clean[i + 1]) for i in range(n - 1)]
        num = sum((a - mean_r) * (b - mean_r) for a, b in pairs)
        denom = sum((r - mean_r) ** 2 for r in clean)
        lag1_autocorr = num / max(denom, 1e-15)
        mean_reversion = max(-1.0, min(1.0, -lag1_autocorr))
    else:
        mean_reversion = 0.0
    short_window = min(10, n)
    short_clean = clean[-short_window:]
    short_mean = sum(short_clean) / len(short_clean)
    short_var = sum((r - short_mean) ** 2 for r in short_clean) / max(len(short_clean) - 1, 1)
    short_vol = math.sqrt(max(short_var, 0.0))
    full_vol = max(volatility, 1e-8)
    stress_raw = (short_vol / full_vol) - 1.0
    stress = max(0.0, min(1.0, stress_raw * 0.5 + 0.5))
    momentum = max(-1.0, min(1.0, recent_mean / max(full_vol, 1e-8)))
    liquidity = 1.0 - stress
    return {
        "volatility":     volatility,
        "trend_strength": trend_strength,
        "mean_reversion": mean_reversion,
        "stress":         stress,
        "momentum":       momentum,
        "liquidity":      liquidity,
    }


# ---------------------------------------------------------------------------
# Internal helpers (unchanged from v1.1.0)
# ---------------------------------------------------------------------------

def x__extract_regime_features__mutmut_45(returns_history: list) -> dict:
    clean = [r if math.isfinite(r) else 0.0 for r in returns_history]
    n = len(clean)
    mean_r = sum(clean) / n
    variance = sum((r - mean_r) ** 2 for r in clean) / max(n - 1, 1)
    volatility = math.sqrt(max(variance, 0.0))
    window = min(5, n)
    recent = clean[-window:]
    recent_mean = sum(recent) / window
    trend_strength = recent_mean / max(volatility, 1.00000001)
    if n >= 2:
        pairs = [(clean[i], clean[i + 1]) for i in range(n - 1)]
        num = sum((a - mean_r) * (b - mean_r) for a, b in pairs)
        denom = sum((r - mean_r) ** 2 for r in clean)
        lag1_autocorr = num / max(denom, 1e-15)
        mean_reversion = max(-1.0, min(1.0, -lag1_autocorr))
    else:
        mean_reversion = 0.0
    short_window = min(10, n)
    short_clean = clean[-short_window:]
    short_mean = sum(short_clean) / len(short_clean)
    short_var = sum((r - short_mean) ** 2 for r in short_clean) / max(len(short_clean) - 1, 1)
    short_vol = math.sqrt(max(short_var, 0.0))
    full_vol = max(volatility, 1e-8)
    stress_raw = (short_vol / full_vol) - 1.0
    stress = max(0.0, min(1.0, stress_raw * 0.5 + 0.5))
    momentum = max(-1.0, min(1.0, recent_mean / max(full_vol, 1e-8)))
    liquidity = 1.0 - stress
    return {
        "volatility":     volatility,
        "trend_strength": trend_strength,
        "mean_reversion": mean_reversion,
        "stress":         stress,
        "momentum":       momentum,
        "liquidity":      liquidity,
    }


# ---------------------------------------------------------------------------
# Internal helpers (unchanged from v1.1.0)
# ---------------------------------------------------------------------------

def x__extract_regime_features__mutmut_46(returns_history: list) -> dict:
    clean = [r if math.isfinite(r) else 0.0 for r in returns_history]
    n = len(clean)
    mean_r = sum(clean) / n
    variance = sum((r - mean_r) ** 2 for r in clean) / max(n - 1, 1)
    volatility = math.sqrt(max(variance, 0.0))
    window = min(5, n)
    recent = clean[-window:]
    recent_mean = sum(recent) / window
    trend_strength = recent_mean / max(volatility, 1e-8)
    if n > 2:
        pairs = [(clean[i], clean[i + 1]) for i in range(n - 1)]
        num = sum((a - mean_r) * (b - mean_r) for a, b in pairs)
        denom = sum((r - mean_r) ** 2 for r in clean)
        lag1_autocorr = num / max(denom, 1e-15)
        mean_reversion = max(-1.0, min(1.0, -lag1_autocorr))
    else:
        mean_reversion = 0.0
    short_window = min(10, n)
    short_clean = clean[-short_window:]
    short_mean = sum(short_clean) / len(short_clean)
    short_var = sum((r - short_mean) ** 2 for r in short_clean) / max(len(short_clean) - 1, 1)
    short_vol = math.sqrt(max(short_var, 0.0))
    full_vol = max(volatility, 1e-8)
    stress_raw = (short_vol / full_vol) - 1.0
    stress = max(0.0, min(1.0, stress_raw * 0.5 + 0.5))
    momentum = max(-1.0, min(1.0, recent_mean / max(full_vol, 1e-8)))
    liquidity = 1.0 - stress
    return {
        "volatility":     volatility,
        "trend_strength": trend_strength,
        "mean_reversion": mean_reversion,
        "stress":         stress,
        "momentum":       momentum,
        "liquidity":      liquidity,
    }


# ---------------------------------------------------------------------------
# Internal helpers (unchanged from v1.1.0)
# ---------------------------------------------------------------------------

def x__extract_regime_features__mutmut_47(returns_history: list) -> dict:
    clean = [r if math.isfinite(r) else 0.0 for r in returns_history]
    n = len(clean)
    mean_r = sum(clean) / n
    variance = sum((r - mean_r) ** 2 for r in clean) / max(n - 1, 1)
    volatility = math.sqrt(max(variance, 0.0))
    window = min(5, n)
    recent = clean[-window:]
    recent_mean = sum(recent) / window
    trend_strength = recent_mean / max(volatility, 1e-8)
    if n >= 3:
        pairs = [(clean[i], clean[i + 1]) for i in range(n - 1)]
        num = sum((a - mean_r) * (b - mean_r) for a, b in pairs)
        denom = sum((r - mean_r) ** 2 for r in clean)
        lag1_autocorr = num / max(denom, 1e-15)
        mean_reversion = max(-1.0, min(1.0, -lag1_autocorr))
    else:
        mean_reversion = 0.0
    short_window = min(10, n)
    short_clean = clean[-short_window:]
    short_mean = sum(short_clean) / len(short_clean)
    short_var = sum((r - short_mean) ** 2 for r in short_clean) / max(len(short_clean) - 1, 1)
    short_vol = math.sqrt(max(short_var, 0.0))
    full_vol = max(volatility, 1e-8)
    stress_raw = (short_vol / full_vol) - 1.0
    stress = max(0.0, min(1.0, stress_raw * 0.5 + 0.5))
    momentum = max(-1.0, min(1.0, recent_mean / max(full_vol, 1e-8)))
    liquidity = 1.0 - stress
    return {
        "volatility":     volatility,
        "trend_strength": trend_strength,
        "mean_reversion": mean_reversion,
        "stress":         stress,
        "momentum":       momentum,
        "liquidity":      liquidity,
    }


# ---------------------------------------------------------------------------
# Internal helpers (unchanged from v1.1.0)
# ---------------------------------------------------------------------------

def x__extract_regime_features__mutmut_48(returns_history: list) -> dict:
    clean = [r if math.isfinite(r) else 0.0 for r in returns_history]
    n = len(clean)
    mean_r = sum(clean) / n
    variance = sum((r - mean_r) ** 2 for r in clean) / max(n - 1, 1)
    volatility = math.sqrt(max(variance, 0.0))
    window = min(5, n)
    recent = clean[-window:]
    recent_mean = sum(recent) / window
    trend_strength = recent_mean / max(volatility, 1e-8)
    if n >= 2:
        pairs = None
        num = sum((a - mean_r) * (b - mean_r) for a, b in pairs)
        denom = sum((r - mean_r) ** 2 for r in clean)
        lag1_autocorr = num / max(denom, 1e-15)
        mean_reversion = max(-1.0, min(1.0, -lag1_autocorr))
    else:
        mean_reversion = 0.0
    short_window = min(10, n)
    short_clean = clean[-short_window:]
    short_mean = sum(short_clean) / len(short_clean)
    short_var = sum((r - short_mean) ** 2 for r in short_clean) / max(len(short_clean) - 1, 1)
    short_vol = math.sqrt(max(short_var, 0.0))
    full_vol = max(volatility, 1e-8)
    stress_raw = (short_vol / full_vol) - 1.0
    stress = max(0.0, min(1.0, stress_raw * 0.5 + 0.5))
    momentum = max(-1.0, min(1.0, recent_mean / max(full_vol, 1e-8)))
    liquidity = 1.0 - stress
    return {
        "volatility":     volatility,
        "trend_strength": trend_strength,
        "mean_reversion": mean_reversion,
        "stress":         stress,
        "momentum":       momentum,
        "liquidity":      liquidity,
    }


# ---------------------------------------------------------------------------
# Internal helpers (unchanged from v1.1.0)
# ---------------------------------------------------------------------------

def x__extract_regime_features__mutmut_49(returns_history: list) -> dict:
    clean = [r if math.isfinite(r) else 0.0 for r in returns_history]
    n = len(clean)
    mean_r = sum(clean) / n
    variance = sum((r - mean_r) ** 2 for r in clean) / max(n - 1, 1)
    volatility = math.sqrt(max(variance, 0.0))
    window = min(5, n)
    recent = clean[-window:]
    recent_mean = sum(recent) / window
    trend_strength = recent_mean / max(volatility, 1e-8)
    if n >= 2:
        pairs = [(clean[i], clean[i - 1]) for i in range(n - 1)]
        num = sum((a - mean_r) * (b - mean_r) for a, b in pairs)
        denom = sum((r - mean_r) ** 2 for r in clean)
        lag1_autocorr = num / max(denom, 1e-15)
        mean_reversion = max(-1.0, min(1.0, -lag1_autocorr))
    else:
        mean_reversion = 0.0
    short_window = min(10, n)
    short_clean = clean[-short_window:]
    short_mean = sum(short_clean) / len(short_clean)
    short_var = sum((r - short_mean) ** 2 for r in short_clean) / max(len(short_clean) - 1, 1)
    short_vol = math.sqrt(max(short_var, 0.0))
    full_vol = max(volatility, 1e-8)
    stress_raw = (short_vol / full_vol) - 1.0
    stress = max(0.0, min(1.0, stress_raw * 0.5 + 0.5))
    momentum = max(-1.0, min(1.0, recent_mean / max(full_vol, 1e-8)))
    liquidity = 1.0 - stress
    return {
        "volatility":     volatility,
        "trend_strength": trend_strength,
        "mean_reversion": mean_reversion,
        "stress":         stress,
        "momentum":       momentum,
        "liquidity":      liquidity,
    }


# ---------------------------------------------------------------------------
# Internal helpers (unchanged from v1.1.0)
# ---------------------------------------------------------------------------

def x__extract_regime_features__mutmut_50(returns_history: list) -> dict:
    clean = [r if math.isfinite(r) else 0.0 for r in returns_history]
    n = len(clean)
    mean_r = sum(clean) / n
    variance = sum((r - mean_r) ** 2 for r in clean) / max(n - 1, 1)
    volatility = math.sqrt(max(variance, 0.0))
    window = min(5, n)
    recent = clean[-window:]
    recent_mean = sum(recent) / window
    trend_strength = recent_mean / max(volatility, 1e-8)
    if n >= 2:
        pairs = [(clean[i], clean[i + 2]) for i in range(n - 1)]
        num = sum((a - mean_r) * (b - mean_r) for a, b in pairs)
        denom = sum((r - mean_r) ** 2 for r in clean)
        lag1_autocorr = num / max(denom, 1e-15)
        mean_reversion = max(-1.0, min(1.0, -lag1_autocorr))
    else:
        mean_reversion = 0.0
    short_window = min(10, n)
    short_clean = clean[-short_window:]
    short_mean = sum(short_clean) / len(short_clean)
    short_var = sum((r - short_mean) ** 2 for r in short_clean) / max(len(short_clean) - 1, 1)
    short_vol = math.sqrt(max(short_var, 0.0))
    full_vol = max(volatility, 1e-8)
    stress_raw = (short_vol / full_vol) - 1.0
    stress = max(0.0, min(1.0, stress_raw * 0.5 + 0.5))
    momentum = max(-1.0, min(1.0, recent_mean / max(full_vol, 1e-8)))
    liquidity = 1.0 - stress
    return {
        "volatility":     volatility,
        "trend_strength": trend_strength,
        "mean_reversion": mean_reversion,
        "stress":         stress,
        "momentum":       momentum,
        "liquidity":      liquidity,
    }


# ---------------------------------------------------------------------------
# Internal helpers (unchanged from v1.1.0)
# ---------------------------------------------------------------------------

def x__extract_regime_features__mutmut_51(returns_history: list) -> dict:
    clean = [r if math.isfinite(r) else 0.0 for r in returns_history]
    n = len(clean)
    mean_r = sum(clean) / n
    variance = sum((r - mean_r) ** 2 for r in clean) / max(n - 1, 1)
    volatility = math.sqrt(max(variance, 0.0))
    window = min(5, n)
    recent = clean[-window:]
    recent_mean = sum(recent) / window
    trend_strength = recent_mean / max(volatility, 1e-8)
    if n >= 2:
        pairs = [(clean[i], clean[i + 1]) for i in range(None)]
        num = sum((a - mean_r) * (b - mean_r) for a, b in pairs)
        denom = sum((r - mean_r) ** 2 for r in clean)
        lag1_autocorr = num / max(denom, 1e-15)
        mean_reversion = max(-1.0, min(1.0, -lag1_autocorr))
    else:
        mean_reversion = 0.0
    short_window = min(10, n)
    short_clean = clean[-short_window:]
    short_mean = sum(short_clean) / len(short_clean)
    short_var = sum((r - short_mean) ** 2 for r in short_clean) / max(len(short_clean) - 1, 1)
    short_vol = math.sqrt(max(short_var, 0.0))
    full_vol = max(volatility, 1e-8)
    stress_raw = (short_vol / full_vol) - 1.0
    stress = max(0.0, min(1.0, stress_raw * 0.5 + 0.5))
    momentum = max(-1.0, min(1.0, recent_mean / max(full_vol, 1e-8)))
    liquidity = 1.0 - stress
    return {
        "volatility":     volatility,
        "trend_strength": trend_strength,
        "mean_reversion": mean_reversion,
        "stress":         stress,
        "momentum":       momentum,
        "liquidity":      liquidity,
    }


# ---------------------------------------------------------------------------
# Internal helpers (unchanged from v1.1.0)
# ---------------------------------------------------------------------------

def x__extract_regime_features__mutmut_52(returns_history: list) -> dict:
    clean = [r if math.isfinite(r) else 0.0 for r in returns_history]
    n = len(clean)
    mean_r = sum(clean) / n
    variance = sum((r - mean_r) ** 2 for r in clean) / max(n - 1, 1)
    volatility = math.sqrt(max(variance, 0.0))
    window = min(5, n)
    recent = clean[-window:]
    recent_mean = sum(recent) / window
    trend_strength = recent_mean / max(volatility, 1e-8)
    if n >= 2:
        pairs = [(clean[i], clean[i + 1]) for i in range(n + 1)]
        num = sum((a - mean_r) * (b - mean_r) for a, b in pairs)
        denom = sum((r - mean_r) ** 2 for r in clean)
        lag1_autocorr = num / max(denom, 1e-15)
        mean_reversion = max(-1.0, min(1.0, -lag1_autocorr))
    else:
        mean_reversion = 0.0
    short_window = min(10, n)
    short_clean = clean[-short_window:]
    short_mean = sum(short_clean) / len(short_clean)
    short_var = sum((r - short_mean) ** 2 for r in short_clean) / max(len(short_clean) - 1, 1)
    short_vol = math.sqrt(max(short_var, 0.0))
    full_vol = max(volatility, 1e-8)
    stress_raw = (short_vol / full_vol) - 1.0
    stress = max(0.0, min(1.0, stress_raw * 0.5 + 0.5))
    momentum = max(-1.0, min(1.0, recent_mean / max(full_vol, 1e-8)))
    liquidity = 1.0 - stress
    return {
        "volatility":     volatility,
        "trend_strength": trend_strength,
        "mean_reversion": mean_reversion,
        "stress":         stress,
        "momentum":       momentum,
        "liquidity":      liquidity,
    }


# ---------------------------------------------------------------------------
# Internal helpers (unchanged from v1.1.0)
# ---------------------------------------------------------------------------

def x__extract_regime_features__mutmut_53(returns_history: list) -> dict:
    clean = [r if math.isfinite(r) else 0.0 for r in returns_history]
    n = len(clean)
    mean_r = sum(clean) / n
    variance = sum((r - mean_r) ** 2 for r in clean) / max(n - 1, 1)
    volatility = math.sqrt(max(variance, 0.0))
    window = min(5, n)
    recent = clean[-window:]
    recent_mean = sum(recent) / window
    trend_strength = recent_mean / max(volatility, 1e-8)
    if n >= 2:
        pairs = [(clean[i], clean[i + 1]) for i in range(n - 2)]
        num = sum((a - mean_r) * (b - mean_r) for a, b in pairs)
        denom = sum((r - mean_r) ** 2 for r in clean)
        lag1_autocorr = num / max(denom, 1e-15)
        mean_reversion = max(-1.0, min(1.0, -lag1_autocorr))
    else:
        mean_reversion = 0.0
    short_window = min(10, n)
    short_clean = clean[-short_window:]
    short_mean = sum(short_clean) / len(short_clean)
    short_var = sum((r - short_mean) ** 2 for r in short_clean) / max(len(short_clean) - 1, 1)
    short_vol = math.sqrt(max(short_var, 0.0))
    full_vol = max(volatility, 1e-8)
    stress_raw = (short_vol / full_vol) - 1.0
    stress = max(0.0, min(1.0, stress_raw * 0.5 + 0.5))
    momentum = max(-1.0, min(1.0, recent_mean / max(full_vol, 1e-8)))
    liquidity = 1.0 - stress
    return {
        "volatility":     volatility,
        "trend_strength": trend_strength,
        "mean_reversion": mean_reversion,
        "stress":         stress,
        "momentum":       momentum,
        "liquidity":      liquidity,
    }


# ---------------------------------------------------------------------------
# Internal helpers (unchanged from v1.1.0)
# ---------------------------------------------------------------------------

def x__extract_regime_features__mutmut_54(returns_history: list) -> dict:
    clean = [r if math.isfinite(r) else 0.0 for r in returns_history]
    n = len(clean)
    mean_r = sum(clean) / n
    variance = sum((r - mean_r) ** 2 for r in clean) / max(n - 1, 1)
    volatility = math.sqrt(max(variance, 0.0))
    window = min(5, n)
    recent = clean[-window:]
    recent_mean = sum(recent) / window
    trend_strength = recent_mean / max(volatility, 1e-8)
    if n >= 2:
        pairs = [(clean[i], clean[i + 1]) for i in range(n - 1)]
        num = None
        denom = sum((r - mean_r) ** 2 for r in clean)
        lag1_autocorr = num / max(denom, 1e-15)
        mean_reversion = max(-1.0, min(1.0, -lag1_autocorr))
    else:
        mean_reversion = 0.0
    short_window = min(10, n)
    short_clean = clean[-short_window:]
    short_mean = sum(short_clean) / len(short_clean)
    short_var = sum((r - short_mean) ** 2 for r in short_clean) / max(len(short_clean) - 1, 1)
    short_vol = math.sqrt(max(short_var, 0.0))
    full_vol = max(volatility, 1e-8)
    stress_raw = (short_vol / full_vol) - 1.0
    stress = max(0.0, min(1.0, stress_raw * 0.5 + 0.5))
    momentum = max(-1.0, min(1.0, recent_mean / max(full_vol, 1e-8)))
    liquidity = 1.0 - stress
    return {
        "volatility":     volatility,
        "trend_strength": trend_strength,
        "mean_reversion": mean_reversion,
        "stress":         stress,
        "momentum":       momentum,
        "liquidity":      liquidity,
    }


# ---------------------------------------------------------------------------
# Internal helpers (unchanged from v1.1.0)
# ---------------------------------------------------------------------------

def x__extract_regime_features__mutmut_55(returns_history: list) -> dict:
    clean = [r if math.isfinite(r) else 0.0 for r in returns_history]
    n = len(clean)
    mean_r = sum(clean) / n
    variance = sum((r - mean_r) ** 2 for r in clean) / max(n - 1, 1)
    volatility = math.sqrt(max(variance, 0.0))
    window = min(5, n)
    recent = clean[-window:]
    recent_mean = sum(recent) / window
    trend_strength = recent_mean / max(volatility, 1e-8)
    if n >= 2:
        pairs = [(clean[i], clean[i + 1]) for i in range(n - 1)]
        num = sum(None)
        denom = sum((r - mean_r) ** 2 for r in clean)
        lag1_autocorr = num / max(denom, 1e-15)
        mean_reversion = max(-1.0, min(1.0, -lag1_autocorr))
    else:
        mean_reversion = 0.0
    short_window = min(10, n)
    short_clean = clean[-short_window:]
    short_mean = sum(short_clean) / len(short_clean)
    short_var = sum((r - short_mean) ** 2 for r in short_clean) / max(len(short_clean) - 1, 1)
    short_vol = math.sqrt(max(short_var, 0.0))
    full_vol = max(volatility, 1e-8)
    stress_raw = (short_vol / full_vol) - 1.0
    stress = max(0.0, min(1.0, stress_raw * 0.5 + 0.5))
    momentum = max(-1.0, min(1.0, recent_mean / max(full_vol, 1e-8)))
    liquidity = 1.0 - stress
    return {
        "volatility":     volatility,
        "trend_strength": trend_strength,
        "mean_reversion": mean_reversion,
        "stress":         stress,
        "momentum":       momentum,
        "liquidity":      liquidity,
    }


# ---------------------------------------------------------------------------
# Internal helpers (unchanged from v1.1.0)
# ---------------------------------------------------------------------------

def x__extract_regime_features__mutmut_56(returns_history: list) -> dict:
    clean = [r if math.isfinite(r) else 0.0 for r in returns_history]
    n = len(clean)
    mean_r = sum(clean) / n
    variance = sum((r - mean_r) ** 2 for r in clean) / max(n - 1, 1)
    volatility = math.sqrt(max(variance, 0.0))
    window = min(5, n)
    recent = clean[-window:]
    recent_mean = sum(recent) / window
    trend_strength = recent_mean / max(volatility, 1e-8)
    if n >= 2:
        pairs = [(clean[i], clean[i + 1]) for i in range(n - 1)]
        num = sum((a - mean_r) / (b - mean_r) for a, b in pairs)
        denom = sum((r - mean_r) ** 2 for r in clean)
        lag1_autocorr = num / max(denom, 1e-15)
        mean_reversion = max(-1.0, min(1.0, -lag1_autocorr))
    else:
        mean_reversion = 0.0
    short_window = min(10, n)
    short_clean = clean[-short_window:]
    short_mean = sum(short_clean) / len(short_clean)
    short_var = sum((r - short_mean) ** 2 for r in short_clean) / max(len(short_clean) - 1, 1)
    short_vol = math.sqrt(max(short_var, 0.0))
    full_vol = max(volatility, 1e-8)
    stress_raw = (short_vol / full_vol) - 1.0
    stress = max(0.0, min(1.0, stress_raw * 0.5 + 0.5))
    momentum = max(-1.0, min(1.0, recent_mean / max(full_vol, 1e-8)))
    liquidity = 1.0 - stress
    return {
        "volatility":     volatility,
        "trend_strength": trend_strength,
        "mean_reversion": mean_reversion,
        "stress":         stress,
        "momentum":       momentum,
        "liquidity":      liquidity,
    }


# ---------------------------------------------------------------------------
# Internal helpers (unchanged from v1.1.0)
# ---------------------------------------------------------------------------

def x__extract_regime_features__mutmut_57(returns_history: list) -> dict:
    clean = [r if math.isfinite(r) else 0.0 for r in returns_history]
    n = len(clean)
    mean_r = sum(clean) / n
    variance = sum((r - mean_r) ** 2 for r in clean) / max(n - 1, 1)
    volatility = math.sqrt(max(variance, 0.0))
    window = min(5, n)
    recent = clean[-window:]
    recent_mean = sum(recent) / window
    trend_strength = recent_mean / max(volatility, 1e-8)
    if n >= 2:
        pairs = [(clean[i], clean[i + 1]) for i in range(n - 1)]
        num = sum((a + mean_r) * (b - mean_r) for a, b in pairs)
        denom = sum((r - mean_r) ** 2 for r in clean)
        lag1_autocorr = num / max(denom, 1e-15)
        mean_reversion = max(-1.0, min(1.0, -lag1_autocorr))
    else:
        mean_reversion = 0.0
    short_window = min(10, n)
    short_clean = clean[-short_window:]
    short_mean = sum(short_clean) / len(short_clean)
    short_var = sum((r - short_mean) ** 2 for r in short_clean) / max(len(short_clean) - 1, 1)
    short_vol = math.sqrt(max(short_var, 0.0))
    full_vol = max(volatility, 1e-8)
    stress_raw = (short_vol / full_vol) - 1.0
    stress = max(0.0, min(1.0, stress_raw * 0.5 + 0.5))
    momentum = max(-1.0, min(1.0, recent_mean / max(full_vol, 1e-8)))
    liquidity = 1.0 - stress
    return {
        "volatility":     volatility,
        "trend_strength": trend_strength,
        "mean_reversion": mean_reversion,
        "stress":         stress,
        "momentum":       momentum,
        "liquidity":      liquidity,
    }


# ---------------------------------------------------------------------------
# Internal helpers (unchanged from v1.1.0)
# ---------------------------------------------------------------------------

def x__extract_regime_features__mutmut_58(returns_history: list) -> dict:
    clean = [r if math.isfinite(r) else 0.0 for r in returns_history]
    n = len(clean)
    mean_r = sum(clean) / n
    variance = sum((r - mean_r) ** 2 for r in clean) / max(n - 1, 1)
    volatility = math.sqrt(max(variance, 0.0))
    window = min(5, n)
    recent = clean[-window:]
    recent_mean = sum(recent) / window
    trend_strength = recent_mean / max(volatility, 1e-8)
    if n >= 2:
        pairs = [(clean[i], clean[i + 1]) for i in range(n - 1)]
        num = sum((a - mean_r) * (b + mean_r) for a, b in pairs)
        denom = sum((r - mean_r) ** 2 for r in clean)
        lag1_autocorr = num / max(denom, 1e-15)
        mean_reversion = max(-1.0, min(1.0, -lag1_autocorr))
    else:
        mean_reversion = 0.0
    short_window = min(10, n)
    short_clean = clean[-short_window:]
    short_mean = sum(short_clean) / len(short_clean)
    short_var = sum((r - short_mean) ** 2 for r in short_clean) / max(len(short_clean) - 1, 1)
    short_vol = math.sqrt(max(short_var, 0.0))
    full_vol = max(volatility, 1e-8)
    stress_raw = (short_vol / full_vol) - 1.0
    stress = max(0.0, min(1.0, stress_raw * 0.5 + 0.5))
    momentum = max(-1.0, min(1.0, recent_mean / max(full_vol, 1e-8)))
    liquidity = 1.0 - stress
    return {
        "volatility":     volatility,
        "trend_strength": trend_strength,
        "mean_reversion": mean_reversion,
        "stress":         stress,
        "momentum":       momentum,
        "liquidity":      liquidity,
    }


# ---------------------------------------------------------------------------
# Internal helpers (unchanged from v1.1.0)
# ---------------------------------------------------------------------------

def x__extract_regime_features__mutmut_59(returns_history: list) -> dict:
    clean = [r if math.isfinite(r) else 0.0 for r in returns_history]
    n = len(clean)
    mean_r = sum(clean) / n
    variance = sum((r - mean_r) ** 2 for r in clean) / max(n - 1, 1)
    volatility = math.sqrt(max(variance, 0.0))
    window = min(5, n)
    recent = clean[-window:]
    recent_mean = sum(recent) / window
    trend_strength = recent_mean / max(volatility, 1e-8)
    if n >= 2:
        pairs = [(clean[i], clean[i + 1]) for i in range(n - 1)]
        num = sum((a - mean_r) * (b - mean_r) for a, b in pairs)
        denom = None
        lag1_autocorr = num / max(denom, 1e-15)
        mean_reversion = max(-1.0, min(1.0, -lag1_autocorr))
    else:
        mean_reversion = 0.0
    short_window = min(10, n)
    short_clean = clean[-short_window:]
    short_mean = sum(short_clean) / len(short_clean)
    short_var = sum((r - short_mean) ** 2 for r in short_clean) / max(len(short_clean) - 1, 1)
    short_vol = math.sqrt(max(short_var, 0.0))
    full_vol = max(volatility, 1e-8)
    stress_raw = (short_vol / full_vol) - 1.0
    stress = max(0.0, min(1.0, stress_raw * 0.5 + 0.5))
    momentum = max(-1.0, min(1.0, recent_mean / max(full_vol, 1e-8)))
    liquidity = 1.0 - stress
    return {
        "volatility":     volatility,
        "trend_strength": trend_strength,
        "mean_reversion": mean_reversion,
        "stress":         stress,
        "momentum":       momentum,
        "liquidity":      liquidity,
    }


# ---------------------------------------------------------------------------
# Internal helpers (unchanged from v1.1.0)
# ---------------------------------------------------------------------------

def x__extract_regime_features__mutmut_60(returns_history: list) -> dict:
    clean = [r if math.isfinite(r) else 0.0 for r in returns_history]
    n = len(clean)
    mean_r = sum(clean) / n
    variance = sum((r - mean_r) ** 2 for r in clean) / max(n - 1, 1)
    volatility = math.sqrt(max(variance, 0.0))
    window = min(5, n)
    recent = clean[-window:]
    recent_mean = sum(recent) / window
    trend_strength = recent_mean / max(volatility, 1e-8)
    if n >= 2:
        pairs = [(clean[i], clean[i + 1]) for i in range(n - 1)]
        num = sum((a - mean_r) * (b - mean_r) for a, b in pairs)
        denom = sum(None)
        lag1_autocorr = num / max(denom, 1e-15)
        mean_reversion = max(-1.0, min(1.0, -lag1_autocorr))
    else:
        mean_reversion = 0.0
    short_window = min(10, n)
    short_clean = clean[-short_window:]
    short_mean = sum(short_clean) / len(short_clean)
    short_var = sum((r - short_mean) ** 2 for r in short_clean) / max(len(short_clean) - 1, 1)
    short_vol = math.sqrt(max(short_var, 0.0))
    full_vol = max(volatility, 1e-8)
    stress_raw = (short_vol / full_vol) - 1.0
    stress = max(0.0, min(1.0, stress_raw * 0.5 + 0.5))
    momentum = max(-1.0, min(1.0, recent_mean / max(full_vol, 1e-8)))
    liquidity = 1.0 - stress
    return {
        "volatility":     volatility,
        "trend_strength": trend_strength,
        "mean_reversion": mean_reversion,
        "stress":         stress,
        "momentum":       momentum,
        "liquidity":      liquidity,
    }


# ---------------------------------------------------------------------------
# Internal helpers (unchanged from v1.1.0)
# ---------------------------------------------------------------------------

def x__extract_regime_features__mutmut_61(returns_history: list) -> dict:
    clean = [r if math.isfinite(r) else 0.0 for r in returns_history]
    n = len(clean)
    mean_r = sum(clean) / n
    variance = sum((r - mean_r) ** 2 for r in clean) / max(n - 1, 1)
    volatility = math.sqrt(max(variance, 0.0))
    window = min(5, n)
    recent = clean[-window:]
    recent_mean = sum(recent) / window
    trend_strength = recent_mean / max(volatility, 1e-8)
    if n >= 2:
        pairs = [(clean[i], clean[i + 1]) for i in range(n - 1)]
        num = sum((a - mean_r) * (b - mean_r) for a, b in pairs)
        denom = sum((r - mean_r) * 2 for r in clean)
        lag1_autocorr = num / max(denom, 1e-15)
        mean_reversion = max(-1.0, min(1.0, -lag1_autocorr))
    else:
        mean_reversion = 0.0
    short_window = min(10, n)
    short_clean = clean[-short_window:]
    short_mean = sum(short_clean) / len(short_clean)
    short_var = sum((r - short_mean) ** 2 for r in short_clean) / max(len(short_clean) - 1, 1)
    short_vol = math.sqrt(max(short_var, 0.0))
    full_vol = max(volatility, 1e-8)
    stress_raw = (short_vol / full_vol) - 1.0
    stress = max(0.0, min(1.0, stress_raw * 0.5 + 0.5))
    momentum = max(-1.0, min(1.0, recent_mean / max(full_vol, 1e-8)))
    liquidity = 1.0 - stress
    return {
        "volatility":     volatility,
        "trend_strength": trend_strength,
        "mean_reversion": mean_reversion,
        "stress":         stress,
        "momentum":       momentum,
        "liquidity":      liquidity,
    }


# ---------------------------------------------------------------------------
# Internal helpers (unchanged from v1.1.0)
# ---------------------------------------------------------------------------

def x__extract_regime_features__mutmut_62(returns_history: list) -> dict:
    clean = [r if math.isfinite(r) else 0.0 for r in returns_history]
    n = len(clean)
    mean_r = sum(clean) / n
    variance = sum((r - mean_r) ** 2 for r in clean) / max(n - 1, 1)
    volatility = math.sqrt(max(variance, 0.0))
    window = min(5, n)
    recent = clean[-window:]
    recent_mean = sum(recent) / window
    trend_strength = recent_mean / max(volatility, 1e-8)
    if n >= 2:
        pairs = [(clean[i], clean[i + 1]) for i in range(n - 1)]
        num = sum((a - mean_r) * (b - mean_r) for a, b in pairs)
        denom = sum((r + mean_r) ** 2 for r in clean)
        lag1_autocorr = num / max(denom, 1e-15)
        mean_reversion = max(-1.0, min(1.0, -lag1_autocorr))
    else:
        mean_reversion = 0.0
    short_window = min(10, n)
    short_clean = clean[-short_window:]
    short_mean = sum(short_clean) / len(short_clean)
    short_var = sum((r - short_mean) ** 2 for r in short_clean) / max(len(short_clean) - 1, 1)
    short_vol = math.sqrt(max(short_var, 0.0))
    full_vol = max(volatility, 1e-8)
    stress_raw = (short_vol / full_vol) - 1.0
    stress = max(0.0, min(1.0, stress_raw * 0.5 + 0.5))
    momentum = max(-1.0, min(1.0, recent_mean / max(full_vol, 1e-8)))
    liquidity = 1.0 - stress
    return {
        "volatility":     volatility,
        "trend_strength": trend_strength,
        "mean_reversion": mean_reversion,
        "stress":         stress,
        "momentum":       momentum,
        "liquidity":      liquidity,
    }


# ---------------------------------------------------------------------------
# Internal helpers (unchanged from v1.1.0)
# ---------------------------------------------------------------------------

def x__extract_regime_features__mutmut_63(returns_history: list) -> dict:
    clean = [r if math.isfinite(r) else 0.0 for r in returns_history]
    n = len(clean)
    mean_r = sum(clean) / n
    variance = sum((r - mean_r) ** 2 for r in clean) / max(n - 1, 1)
    volatility = math.sqrt(max(variance, 0.0))
    window = min(5, n)
    recent = clean[-window:]
    recent_mean = sum(recent) / window
    trend_strength = recent_mean / max(volatility, 1e-8)
    if n >= 2:
        pairs = [(clean[i], clean[i + 1]) for i in range(n - 1)]
        num = sum((a - mean_r) * (b - mean_r) for a, b in pairs)
        denom = sum((r - mean_r) ** 3 for r in clean)
        lag1_autocorr = num / max(denom, 1e-15)
        mean_reversion = max(-1.0, min(1.0, -lag1_autocorr))
    else:
        mean_reversion = 0.0
    short_window = min(10, n)
    short_clean = clean[-short_window:]
    short_mean = sum(short_clean) / len(short_clean)
    short_var = sum((r - short_mean) ** 2 for r in short_clean) / max(len(short_clean) - 1, 1)
    short_vol = math.sqrt(max(short_var, 0.0))
    full_vol = max(volatility, 1e-8)
    stress_raw = (short_vol / full_vol) - 1.0
    stress = max(0.0, min(1.0, stress_raw * 0.5 + 0.5))
    momentum = max(-1.0, min(1.0, recent_mean / max(full_vol, 1e-8)))
    liquidity = 1.0 - stress
    return {
        "volatility":     volatility,
        "trend_strength": trend_strength,
        "mean_reversion": mean_reversion,
        "stress":         stress,
        "momentum":       momentum,
        "liquidity":      liquidity,
    }


# ---------------------------------------------------------------------------
# Internal helpers (unchanged from v1.1.0)
# ---------------------------------------------------------------------------

def x__extract_regime_features__mutmut_64(returns_history: list) -> dict:
    clean = [r if math.isfinite(r) else 0.0 for r in returns_history]
    n = len(clean)
    mean_r = sum(clean) / n
    variance = sum((r - mean_r) ** 2 for r in clean) / max(n - 1, 1)
    volatility = math.sqrt(max(variance, 0.0))
    window = min(5, n)
    recent = clean[-window:]
    recent_mean = sum(recent) / window
    trend_strength = recent_mean / max(volatility, 1e-8)
    if n >= 2:
        pairs = [(clean[i], clean[i + 1]) for i in range(n - 1)]
        num = sum((a - mean_r) * (b - mean_r) for a, b in pairs)
        denom = sum((r - mean_r) ** 2 for r in clean)
        lag1_autocorr = None
        mean_reversion = max(-1.0, min(1.0, -lag1_autocorr))
    else:
        mean_reversion = 0.0
    short_window = min(10, n)
    short_clean = clean[-short_window:]
    short_mean = sum(short_clean) / len(short_clean)
    short_var = sum((r - short_mean) ** 2 for r in short_clean) / max(len(short_clean) - 1, 1)
    short_vol = math.sqrt(max(short_var, 0.0))
    full_vol = max(volatility, 1e-8)
    stress_raw = (short_vol / full_vol) - 1.0
    stress = max(0.0, min(1.0, stress_raw * 0.5 + 0.5))
    momentum = max(-1.0, min(1.0, recent_mean / max(full_vol, 1e-8)))
    liquidity = 1.0 - stress
    return {
        "volatility":     volatility,
        "trend_strength": trend_strength,
        "mean_reversion": mean_reversion,
        "stress":         stress,
        "momentum":       momentum,
        "liquidity":      liquidity,
    }


# ---------------------------------------------------------------------------
# Internal helpers (unchanged from v1.1.0)
# ---------------------------------------------------------------------------

def x__extract_regime_features__mutmut_65(returns_history: list) -> dict:
    clean = [r if math.isfinite(r) else 0.0 for r in returns_history]
    n = len(clean)
    mean_r = sum(clean) / n
    variance = sum((r - mean_r) ** 2 for r in clean) / max(n - 1, 1)
    volatility = math.sqrt(max(variance, 0.0))
    window = min(5, n)
    recent = clean[-window:]
    recent_mean = sum(recent) / window
    trend_strength = recent_mean / max(volatility, 1e-8)
    if n >= 2:
        pairs = [(clean[i], clean[i + 1]) for i in range(n - 1)]
        num = sum((a - mean_r) * (b - mean_r) for a, b in pairs)
        denom = sum((r - mean_r) ** 2 for r in clean)
        lag1_autocorr = num * max(denom, 1e-15)
        mean_reversion = max(-1.0, min(1.0, -lag1_autocorr))
    else:
        mean_reversion = 0.0
    short_window = min(10, n)
    short_clean = clean[-short_window:]
    short_mean = sum(short_clean) / len(short_clean)
    short_var = sum((r - short_mean) ** 2 for r in short_clean) / max(len(short_clean) - 1, 1)
    short_vol = math.sqrt(max(short_var, 0.0))
    full_vol = max(volatility, 1e-8)
    stress_raw = (short_vol / full_vol) - 1.0
    stress = max(0.0, min(1.0, stress_raw * 0.5 + 0.5))
    momentum = max(-1.0, min(1.0, recent_mean / max(full_vol, 1e-8)))
    liquidity = 1.0 - stress
    return {
        "volatility":     volatility,
        "trend_strength": trend_strength,
        "mean_reversion": mean_reversion,
        "stress":         stress,
        "momentum":       momentum,
        "liquidity":      liquidity,
    }


# ---------------------------------------------------------------------------
# Internal helpers (unchanged from v1.1.0)
# ---------------------------------------------------------------------------

def x__extract_regime_features__mutmut_66(returns_history: list) -> dict:
    clean = [r if math.isfinite(r) else 0.0 for r in returns_history]
    n = len(clean)
    mean_r = sum(clean) / n
    variance = sum((r - mean_r) ** 2 for r in clean) / max(n - 1, 1)
    volatility = math.sqrt(max(variance, 0.0))
    window = min(5, n)
    recent = clean[-window:]
    recent_mean = sum(recent) / window
    trend_strength = recent_mean / max(volatility, 1e-8)
    if n >= 2:
        pairs = [(clean[i], clean[i + 1]) for i in range(n - 1)]
        num = sum((a - mean_r) * (b - mean_r) for a, b in pairs)
        denom = sum((r - mean_r) ** 2 for r in clean)
        lag1_autocorr = num / max(None, 1e-15)
        mean_reversion = max(-1.0, min(1.0, -lag1_autocorr))
    else:
        mean_reversion = 0.0
    short_window = min(10, n)
    short_clean = clean[-short_window:]
    short_mean = sum(short_clean) / len(short_clean)
    short_var = sum((r - short_mean) ** 2 for r in short_clean) / max(len(short_clean) - 1, 1)
    short_vol = math.sqrt(max(short_var, 0.0))
    full_vol = max(volatility, 1e-8)
    stress_raw = (short_vol / full_vol) - 1.0
    stress = max(0.0, min(1.0, stress_raw * 0.5 + 0.5))
    momentum = max(-1.0, min(1.0, recent_mean / max(full_vol, 1e-8)))
    liquidity = 1.0 - stress
    return {
        "volatility":     volatility,
        "trend_strength": trend_strength,
        "mean_reversion": mean_reversion,
        "stress":         stress,
        "momentum":       momentum,
        "liquidity":      liquidity,
    }


# ---------------------------------------------------------------------------
# Internal helpers (unchanged from v1.1.0)
# ---------------------------------------------------------------------------

def x__extract_regime_features__mutmut_67(returns_history: list) -> dict:
    clean = [r if math.isfinite(r) else 0.0 for r in returns_history]
    n = len(clean)
    mean_r = sum(clean) / n
    variance = sum((r - mean_r) ** 2 for r in clean) / max(n - 1, 1)
    volatility = math.sqrt(max(variance, 0.0))
    window = min(5, n)
    recent = clean[-window:]
    recent_mean = sum(recent) / window
    trend_strength = recent_mean / max(volatility, 1e-8)
    if n >= 2:
        pairs = [(clean[i], clean[i + 1]) for i in range(n - 1)]
        num = sum((a - mean_r) * (b - mean_r) for a, b in pairs)
        denom = sum((r - mean_r) ** 2 for r in clean)
        lag1_autocorr = num / max(denom, None)
        mean_reversion = max(-1.0, min(1.0, -lag1_autocorr))
    else:
        mean_reversion = 0.0
    short_window = min(10, n)
    short_clean = clean[-short_window:]
    short_mean = sum(short_clean) / len(short_clean)
    short_var = sum((r - short_mean) ** 2 for r in short_clean) / max(len(short_clean) - 1, 1)
    short_vol = math.sqrt(max(short_var, 0.0))
    full_vol = max(volatility, 1e-8)
    stress_raw = (short_vol / full_vol) - 1.0
    stress = max(0.0, min(1.0, stress_raw * 0.5 + 0.5))
    momentum = max(-1.0, min(1.0, recent_mean / max(full_vol, 1e-8)))
    liquidity = 1.0 - stress
    return {
        "volatility":     volatility,
        "trend_strength": trend_strength,
        "mean_reversion": mean_reversion,
        "stress":         stress,
        "momentum":       momentum,
        "liquidity":      liquidity,
    }


# ---------------------------------------------------------------------------
# Internal helpers (unchanged from v1.1.0)
# ---------------------------------------------------------------------------

def x__extract_regime_features__mutmut_68(returns_history: list) -> dict:
    clean = [r if math.isfinite(r) else 0.0 for r in returns_history]
    n = len(clean)
    mean_r = sum(clean) / n
    variance = sum((r - mean_r) ** 2 for r in clean) / max(n - 1, 1)
    volatility = math.sqrt(max(variance, 0.0))
    window = min(5, n)
    recent = clean[-window:]
    recent_mean = sum(recent) / window
    trend_strength = recent_mean / max(volatility, 1e-8)
    if n >= 2:
        pairs = [(clean[i], clean[i + 1]) for i in range(n - 1)]
        num = sum((a - mean_r) * (b - mean_r) for a, b in pairs)
        denom = sum((r - mean_r) ** 2 for r in clean)
        lag1_autocorr = num / max(1e-15)
        mean_reversion = max(-1.0, min(1.0, -lag1_autocorr))
    else:
        mean_reversion = 0.0
    short_window = min(10, n)
    short_clean = clean[-short_window:]
    short_mean = sum(short_clean) / len(short_clean)
    short_var = sum((r - short_mean) ** 2 for r in short_clean) / max(len(short_clean) - 1, 1)
    short_vol = math.sqrt(max(short_var, 0.0))
    full_vol = max(volatility, 1e-8)
    stress_raw = (short_vol / full_vol) - 1.0
    stress = max(0.0, min(1.0, stress_raw * 0.5 + 0.5))
    momentum = max(-1.0, min(1.0, recent_mean / max(full_vol, 1e-8)))
    liquidity = 1.0 - stress
    return {
        "volatility":     volatility,
        "trend_strength": trend_strength,
        "mean_reversion": mean_reversion,
        "stress":         stress,
        "momentum":       momentum,
        "liquidity":      liquidity,
    }


# ---------------------------------------------------------------------------
# Internal helpers (unchanged from v1.1.0)
# ---------------------------------------------------------------------------

def x__extract_regime_features__mutmut_69(returns_history: list) -> dict:
    clean = [r if math.isfinite(r) else 0.0 for r in returns_history]
    n = len(clean)
    mean_r = sum(clean) / n
    variance = sum((r - mean_r) ** 2 for r in clean) / max(n - 1, 1)
    volatility = math.sqrt(max(variance, 0.0))
    window = min(5, n)
    recent = clean[-window:]
    recent_mean = sum(recent) / window
    trend_strength = recent_mean / max(volatility, 1e-8)
    if n >= 2:
        pairs = [(clean[i], clean[i + 1]) for i in range(n - 1)]
        num = sum((a - mean_r) * (b - mean_r) for a, b in pairs)
        denom = sum((r - mean_r) ** 2 for r in clean)
        lag1_autocorr = num / max(denom, )
        mean_reversion = max(-1.0, min(1.0, -lag1_autocorr))
    else:
        mean_reversion = 0.0
    short_window = min(10, n)
    short_clean = clean[-short_window:]
    short_mean = sum(short_clean) / len(short_clean)
    short_var = sum((r - short_mean) ** 2 for r in short_clean) / max(len(short_clean) - 1, 1)
    short_vol = math.sqrt(max(short_var, 0.0))
    full_vol = max(volatility, 1e-8)
    stress_raw = (short_vol / full_vol) - 1.0
    stress = max(0.0, min(1.0, stress_raw * 0.5 + 0.5))
    momentum = max(-1.0, min(1.0, recent_mean / max(full_vol, 1e-8)))
    liquidity = 1.0 - stress
    return {
        "volatility":     volatility,
        "trend_strength": trend_strength,
        "mean_reversion": mean_reversion,
        "stress":         stress,
        "momentum":       momentum,
        "liquidity":      liquidity,
    }


# ---------------------------------------------------------------------------
# Internal helpers (unchanged from v1.1.0)
# ---------------------------------------------------------------------------

def x__extract_regime_features__mutmut_70(returns_history: list) -> dict:
    clean = [r if math.isfinite(r) else 0.0 for r in returns_history]
    n = len(clean)
    mean_r = sum(clean) / n
    variance = sum((r - mean_r) ** 2 for r in clean) / max(n - 1, 1)
    volatility = math.sqrt(max(variance, 0.0))
    window = min(5, n)
    recent = clean[-window:]
    recent_mean = sum(recent) / window
    trend_strength = recent_mean / max(volatility, 1e-8)
    if n >= 2:
        pairs = [(clean[i], clean[i + 1]) for i in range(n - 1)]
        num = sum((a - mean_r) * (b - mean_r) for a, b in pairs)
        denom = sum((r - mean_r) ** 2 for r in clean)
        lag1_autocorr = num / max(denom, 1.000000000000001)
        mean_reversion = max(-1.0, min(1.0, -lag1_autocorr))
    else:
        mean_reversion = 0.0
    short_window = min(10, n)
    short_clean = clean[-short_window:]
    short_mean = sum(short_clean) / len(short_clean)
    short_var = sum((r - short_mean) ** 2 for r in short_clean) / max(len(short_clean) - 1, 1)
    short_vol = math.sqrt(max(short_var, 0.0))
    full_vol = max(volatility, 1e-8)
    stress_raw = (short_vol / full_vol) - 1.0
    stress = max(0.0, min(1.0, stress_raw * 0.5 + 0.5))
    momentum = max(-1.0, min(1.0, recent_mean / max(full_vol, 1e-8)))
    liquidity = 1.0 - stress
    return {
        "volatility":     volatility,
        "trend_strength": trend_strength,
        "mean_reversion": mean_reversion,
        "stress":         stress,
        "momentum":       momentum,
        "liquidity":      liquidity,
    }


# ---------------------------------------------------------------------------
# Internal helpers (unchanged from v1.1.0)
# ---------------------------------------------------------------------------

def x__extract_regime_features__mutmut_71(returns_history: list) -> dict:
    clean = [r if math.isfinite(r) else 0.0 for r in returns_history]
    n = len(clean)
    mean_r = sum(clean) / n
    variance = sum((r - mean_r) ** 2 for r in clean) / max(n - 1, 1)
    volatility = math.sqrt(max(variance, 0.0))
    window = min(5, n)
    recent = clean[-window:]
    recent_mean = sum(recent) / window
    trend_strength = recent_mean / max(volatility, 1e-8)
    if n >= 2:
        pairs = [(clean[i], clean[i + 1]) for i in range(n - 1)]
        num = sum((a - mean_r) * (b - mean_r) for a, b in pairs)
        denom = sum((r - mean_r) ** 2 for r in clean)
        lag1_autocorr = num / max(denom, 1e-15)
        mean_reversion = None
    else:
        mean_reversion = 0.0
    short_window = min(10, n)
    short_clean = clean[-short_window:]
    short_mean = sum(short_clean) / len(short_clean)
    short_var = sum((r - short_mean) ** 2 for r in short_clean) / max(len(short_clean) - 1, 1)
    short_vol = math.sqrt(max(short_var, 0.0))
    full_vol = max(volatility, 1e-8)
    stress_raw = (short_vol / full_vol) - 1.0
    stress = max(0.0, min(1.0, stress_raw * 0.5 + 0.5))
    momentum = max(-1.0, min(1.0, recent_mean / max(full_vol, 1e-8)))
    liquidity = 1.0 - stress
    return {
        "volatility":     volatility,
        "trend_strength": trend_strength,
        "mean_reversion": mean_reversion,
        "stress":         stress,
        "momentum":       momentum,
        "liquidity":      liquidity,
    }


# ---------------------------------------------------------------------------
# Internal helpers (unchanged from v1.1.0)
# ---------------------------------------------------------------------------

def x__extract_regime_features__mutmut_72(returns_history: list) -> dict:
    clean = [r if math.isfinite(r) else 0.0 for r in returns_history]
    n = len(clean)
    mean_r = sum(clean) / n
    variance = sum((r - mean_r) ** 2 for r in clean) / max(n - 1, 1)
    volatility = math.sqrt(max(variance, 0.0))
    window = min(5, n)
    recent = clean[-window:]
    recent_mean = sum(recent) / window
    trend_strength = recent_mean / max(volatility, 1e-8)
    if n >= 2:
        pairs = [(clean[i], clean[i + 1]) for i in range(n - 1)]
        num = sum((a - mean_r) * (b - mean_r) for a, b in pairs)
        denom = sum((r - mean_r) ** 2 for r in clean)
        lag1_autocorr = num / max(denom, 1e-15)
        mean_reversion = max(None, min(1.0, -lag1_autocorr))
    else:
        mean_reversion = 0.0
    short_window = min(10, n)
    short_clean = clean[-short_window:]
    short_mean = sum(short_clean) / len(short_clean)
    short_var = sum((r - short_mean) ** 2 for r in short_clean) / max(len(short_clean) - 1, 1)
    short_vol = math.sqrt(max(short_var, 0.0))
    full_vol = max(volatility, 1e-8)
    stress_raw = (short_vol / full_vol) - 1.0
    stress = max(0.0, min(1.0, stress_raw * 0.5 + 0.5))
    momentum = max(-1.0, min(1.0, recent_mean / max(full_vol, 1e-8)))
    liquidity = 1.0 - stress
    return {
        "volatility":     volatility,
        "trend_strength": trend_strength,
        "mean_reversion": mean_reversion,
        "stress":         stress,
        "momentum":       momentum,
        "liquidity":      liquidity,
    }


# ---------------------------------------------------------------------------
# Internal helpers (unchanged from v1.1.0)
# ---------------------------------------------------------------------------

def x__extract_regime_features__mutmut_73(returns_history: list) -> dict:
    clean = [r if math.isfinite(r) else 0.0 for r in returns_history]
    n = len(clean)
    mean_r = sum(clean) / n
    variance = sum((r - mean_r) ** 2 for r in clean) / max(n - 1, 1)
    volatility = math.sqrt(max(variance, 0.0))
    window = min(5, n)
    recent = clean[-window:]
    recent_mean = sum(recent) / window
    trend_strength = recent_mean / max(volatility, 1e-8)
    if n >= 2:
        pairs = [(clean[i], clean[i + 1]) for i in range(n - 1)]
        num = sum((a - mean_r) * (b - mean_r) for a, b in pairs)
        denom = sum((r - mean_r) ** 2 for r in clean)
        lag1_autocorr = num / max(denom, 1e-15)
        mean_reversion = max(-1.0, None)
    else:
        mean_reversion = 0.0
    short_window = min(10, n)
    short_clean = clean[-short_window:]
    short_mean = sum(short_clean) / len(short_clean)
    short_var = sum((r - short_mean) ** 2 for r in short_clean) / max(len(short_clean) - 1, 1)
    short_vol = math.sqrt(max(short_var, 0.0))
    full_vol = max(volatility, 1e-8)
    stress_raw = (short_vol / full_vol) - 1.0
    stress = max(0.0, min(1.0, stress_raw * 0.5 + 0.5))
    momentum = max(-1.0, min(1.0, recent_mean / max(full_vol, 1e-8)))
    liquidity = 1.0 - stress
    return {
        "volatility":     volatility,
        "trend_strength": trend_strength,
        "mean_reversion": mean_reversion,
        "stress":         stress,
        "momentum":       momentum,
        "liquidity":      liquidity,
    }


# ---------------------------------------------------------------------------
# Internal helpers (unchanged from v1.1.0)
# ---------------------------------------------------------------------------

def x__extract_regime_features__mutmut_74(returns_history: list) -> dict:
    clean = [r if math.isfinite(r) else 0.0 for r in returns_history]
    n = len(clean)
    mean_r = sum(clean) / n
    variance = sum((r - mean_r) ** 2 for r in clean) / max(n - 1, 1)
    volatility = math.sqrt(max(variance, 0.0))
    window = min(5, n)
    recent = clean[-window:]
    recent_mean = sum(recent) / window
    trend_strength = recent_mean / max(volatility, 1e-8)
    if n >= 2:
        pairs = [(clean[i], clean[i + 1]) for i in range(n - 1)]
        num = sum((a - mean_r) * (b - mean_r) for a, b in pairs)
        denom = sum((r - mean_r) ** 2 for r in clean)
        lag1_autocorr = num / max(denom, 1e-15)
        mean_reversion = max(min(1.0, -lag1_autocorr))
    else:
        mean_reversion = 0.0
    short_window = min(10, n)
    short_clean = clean[-short_window:]
    short_mean = sum(short_clean) / len(short_clean)
    short_var = sum((r - short_mean) ** 2 for r in short_clean) / max(len(short_clean) - 1, 1)
    short_vol = math.sqrt(max(short_var, 0.0))
    full_vol = max(volatility, 1e-8)
    stress_raw = (short_vol / full_vol) - 1.0
    stress = max(0.0, min(1.0, stress_raw * 0.5 + 0.5))
    momentum = max(-1.0, min(1.0, recent_mean / max(full_vol, 1e-8)))
    liquidity = 1.0 - stress
    return {
        "volatility":     volatility,
        "trend_strength": trend_strength,
        "mean_reversion": mean_reversion,
        "stress":         stress,
        "momentum":       momentum,
        "liquidity":      liquidity,
    }


# ---------------------------------------------------------------------------
# Internal helpers (unchanged from v1.1.0)
# ---------------------------------------------------------------------------

def x__extract_regime_features__mutmut_75(returns_history: list) -> dict:
    clean = [r if math.isfinite(r) else 0.0 for r in returns_history]
    n = len(clean)
    mean_r = sum(clean) / n
    variance = sum((r - mean_r) ** 2 for r in clean) / max(n - 1, 1)
    volatility = math.sqrt(max(variance, 0.0))
    window = min(5, n)
    recent = clean[-window:]
    recent_mean = sum(recent) / window
    trend_strength = recent_mean / max(volatility, 1e-8)
    if n >= 2:
        pairs = [(clean[i], clean[i + 1]) for i in range(n - 1)]
        num = sum((a - mean_r) * (b - mean_r) for a, b in pairs)
        denom = sum((r - mean_r) ** 2 for r in clean)
        lag1_autocorr = num / max(denom, 1e-15)
        mean_reversion = max(-1.0, )
    else:
        mean_reversion = 0.0
    short_window = min(10, n)
    short_clean = clean[-short_window:]
    short_mean = sum(short_clean) / len(short_clean)
    short_var = sum((r - short_mean) ** 2 for r in short_clean) / max(len(short_clean) - 1, 1)
    short_vol = math.sqrt(max(short_var, 0.0))
    full_vol = max(volatility, 1e-8)
    stress_raw = (short_vol / full_vol) - 1.0
    stress = max(0.0, min(1.0, stress_raw * 0.5 + 0.5))
    momentum = max(-1.0, min(1.0, recent_mean / max(full_vol, 1e-8)))
    liquidity = 1.0 - stress
    return {
        "volatility":     volatility,
        "trend_strength": trend_strength,
        "mean_reversion": mean_reversion,
        "stress":         stress,
        "momentum":       momentum,
        "liquidity":      liquidity,
    }


# ---------------------------------------------------------------------------
# Internal helpers (unchanged from v1.1.0)
# ---------------------------------------------------------------------------

def x__extract_regime_features__mutmut_76(returns_history: list) -> dict:
    clean = [r if math.isfinite(r) else 0.0 for r in returns_history]
    n = len(clean)
    mean_r = sum(clean) / n
    variance = sum((r - mean_r) ** 2 for r in clean) / max(n - 1, 1)
    volatility = math.sqrt(max(variance, 0.0))
    window = min(5, n)
    recent = clean[-window:]
    recent_mean = sum(recent) / window
    trend_strength = recent_mean / max(volatility, 1e-8)
    if n >= 2:
        pairs = [(clean[i], clean[i + 1]) for i in range(n - 1)]
        num = sum((a - mean_r) * (b - mean_r) for a, b in pairs)
        denom = sum((r - mean_r) ** 2 for r in clean)
        lag1_autocorr = num / max(denom, 1e-15)
        mean_reversion = max(+1.0, min(1.0, -lag1_autocorr))
    else:
        mean_reversion = 0.0
    short_window = min(10, n)
    short_clean = clean[-short_window:]
    short_mean = sum(short_clean) / len(short_clean)
    short_var = sum((r - short_mean) ** 2 for r in short_clean) / max(len(short_clean) - 1, 1)
    short_vol = math.sqrt(max(short_var, 0.0))
    full_vol = max(volatility, 1e-8)
    stress_raw = (short_vol / full_vol) - 1.0
    stress = max(0.0, min(1.0, stress_raw * 0.5 + 0.5))
    momentum = max(-1.0, min(1.0, recent_mean / max(full_vol, 1e-8)))
    liquidity = 1.0 - stress
    return {
        "volatility":     volatility,
        "trend_strength": trend_strength,
        "mean_reversion": mean_reversion,
        "stress":         stress,
        "momentum":       momentum,
        "liquidity":      liquidity,
    }


# ---------------------------------------------------------------------------
# Internal helpers (unchanged from v1.1.0)
# ---------------------------------------------------------------------------

def x__extract_regime_features__mutmut_77(returns_history: list) -> dict:
    clean = [r if math.isfinite(r) else 0.0 for r in returns_history]
    n = len(clean)
    mean_r = sum(clean) / n
    variance = sum((r - mean_r) ** 2 for r in clean) / max(n - 1, 1)
    volatility = math.sqrt(max(variance, 0.0))
    window = min(5, n)
    recent = clean[-window:]
    recent_mean = sum(recent) / window
    trend_strength = recent_mean / max(volatility, 1e-8)
    if n >= 2:
        pairs = [(clean[i], clean[i + 1]) for i in range(n - 1)]
        num = sum((a - mean_r) * (b - mean_r) for a, b in pairs)
        denom = sum((r - mean_r) ** 2 for r in clean)
        lag1_autocorr = num / max(denom, 1e-15)
        mean_reversion = max(-2.0, min(1.0, -lag1_autocorr))
    else:
        mean_reversion = 0.0
    short_window = min(10, n)
    short_clean = clean[-short_window:]
    short_mean = sum(short_clean) / len(short_clean)
    short_var = sum((r - short_mean) ** 2 for r in short_clean) / max(len(short_clean) - 1, 1)
    short_vol = math.sqrt(max(short_var, 0.0))
    full_vol = max(volatility, 1e-8)
    stress_raw = (short_vol / full_vol) - 1.0
    stress = max(0.0, min(1.0, stress_raw * 0.5 + 0.5))
    momentum = max(-1.0, min(1.0, recent_mean / max(full_vol, 1e-8)))
    liquidity = 1.0 - stress
    return {
        "volatility":     volatility,
        "trend_strength": trend_strength,
        "mean_reversion": mean_reversion,
        "stress":         stress,
        "momentum":       momentum,
        "liquidity":      liquidity,
    }


# ---------------------------------------------------------------------------
# Internal helpers (unchanged from v1.1.0)
# ---------------------------------------------------------------------------

def x__extract_regime_features__mutmut_78(returns_history: list) -> dict:
    clean = [r if math.isfinite(r) else 0.0 for r in returns_history]
    n = len(clean)
    mean_r = sum(clean) / n
    variance = sum((r - mean_r) ** 2 for r in clean) / max(n - 1, 1)
    volatility = math.sqrt(max(variance, 0.0))
    window = min(5, n)
    recent = clean[-window:]
    recent_mean = sum(recent) / window
    trend_strength = recent_mean / max(volatility, 1e-8)
    if n >= 2:
        pairs = [(clean[i], clean[i + 1]) for i in range(n - 1)]
        num = sum((a - mean_r) * (b - mean_r) for a, b in pairs)
        denom = sum((r - mean_r) ** 2 for r in clean)
        lag1_autocorr = num / max(denom, 1e-15)
        mean_reversion = max(-1.0, min(None, -lag1_autocorr))
    else:
        mean_reversion = 0.0
    short_window = min(10, n)
    short_clean = clean[-short_window:]
    short_mean = sum(short_clean) / len(short_clean)
    short_var = sum((r - short_mean) ** 2 for r in short_clean) / max(len(short_clean) - 1, 1)
    short_vol = math.sqrt(max(short_var, 0.0))
    full_vol = max(volatility, 1e-8)
    stress_raw = (short_vol / full_vol) - 1.0
    stress = max(0.0, min(1.0, stress_raw * 0.5 + 0.5))
    momentum = max(-1.0, min(1.0, recent_mean / max(full_vol, 1e-8)))
    liquidity = 1.0 - stress
    return {
        "volatility":     volatility,
        "trend_strength": trend_strength,
        "mean_reversion": mean_reversion,
        "stress":         stress,
        "momentum":       momentum,
        "liquidity":      liquidity,
    }


# ---------------------------------------------------------------------------
# Internal helpers (unchanged from v1.1.0)
# ---------------------------------------------------------------------------

def x__extract_regime_features__mutmut_79(returns_history: list) -> dict:
    clean = [r if math.isfinite(r) else 0.0 for r in returns_history]
    n = len(clean)
    mean_r = sum(clean) / n
    variance = sum((r - mean_r) ** 2 for r in clean) / max(n - 1, 1)
    volatility = math.sqrt(max(variance, 0.0))
    window = min(5, n)
    recent = clean[-window:]
    recent_mean = sum(recent) / window
    trend_strength = recent_mean / max(volatility, 1e-8)
    if n >= 2:
        pairs = [(clean[i], clean[i + 1]) for i in range(n - 1)]
        num = sum((a - mean_r) * (b - mean_r) for a, b in pairs)
        denom = sum((r - mean_r) ** 2 for r in clean)
        lag1_autocorr = num / max(denom, 1e-15)
        mean_reversion = max(-1.0, min(1.0, None))
    else:
        mean_reversion = 0.0
    short_window = min(10, n)
    short_clean = clean[-short_window:]
    short_mean = sum(short_clean) / len(short_clean)
    short_var = sum((r - short_mean) ** 2 for r in short_clean) / max(len(short_clean) - 1, 1)
    short_vol = math.sqrt(max(short_var, 0.0))
    full_vol = max(volatility, 1e-8)
    stress_raw = (short_vol / full_vol) - 1.0
    stress = max(0.0, min(1.0, stress_raw * 0.5 + 0.5))
    momentum = max(-1.0, min(1.0, recent_mean / max(full_vol, 1e-8)))
    liquidity = 1.0 - stress
    return {
        "volatility":     volatility,
        "trend_strength": trend_strength,
        "mean_reversion": mean_reversion,
        "stress":         stress,
        "momentum":       momentum,
        "liquidity":      liquidity,
    }


# ---------------------------------------------------------------------------
# Internal helpers (unchanged from v1.1.0)
# ---------------------------------------------------------------------------

def x__extract_regime_features__mutmut_80(returns_history: list) -> dict:
    clean = [r if math.isfinite(r) else 0.0 for r in returns_history]
    n = len(clean)
    mean_r = sum(clean) / n
    variance = sum((r - mean_r) ** 2 for r in clean) / max(n - 1, 1)
    volatility = math.sqrt(max(variance, 0.0))
    window = min(5, n)
    recent = clean[-window:]
    recent_mean = sum(recent) / window
    trend_strength = recent_mean / max(volatility, 1e-8)
    if n >= 2:
        pairs = [(clean[i], clean[i + 1]) for i in range(n - 1)]
        num = sum((a - mean_r) * (b - mean_r) for a, b in pairs)
        denom = sum((r - mean_r) ** 2 for r in clean)
        lag1_autocorr = num / max(denom, 1e-15)
        mean_reversion = max(-1.0, min(-lag1_autocorr))
    else:
        mean_reversion = 0.0
    short_window = min(10, n)
    short_clean = clean[-short_window:]
    short_mean = sum(short_clean) / len(short_clean)
    short_var = sum((r - short_mean) ** 2 for r in short_clean) / max(len(short_clean) - 1, 1)
    short_vol = math.sqrt(max(short_var, 0.0))
    full_vol = max(volatility, 1e-8)
    stress_raw = (short_vol / full_vol) - 1.0
    stress = max(0.0, min(1.0, stress_raw * 0.5 + 0.5))
    momentum = max(-1.0, min(1.0, recent_mean / max(full_vol, 1e-8)))
    liquidity = 1.0 - stress
    return {
        "volatility":     volatility,
        "trend_strength": trend_strength,
        "mean_reversion": mean_reversion,
        "stress":         stress,
        "momentum":       momentum,
        "liquidity":      liquidity,
    }


# ---------------------------------------------------------------------------
# Internal helpers (unchanged from v1.1.0)
# ---------------------------------------------------------------------------

def x__extract_regime_features__mutmut_81(returns_history: list) -> dict:
    clean = [r if math.isfinite(r) else 0.0 for r in returns_history]
    n = len(clean)
    mean_r = sum(clean) / n
    variance = sum((r - mean_r) ** 2 for r in clean) / max(n - 1, 1)
    volatility = math.sqrt(max(variance, 0.0))
    window = min(5, n)
    recent = clean[-window:]
    recent_mean = sum(recent) / window
    trend_strength = recent_mean / max(volatility, 1e-8)
    if n >= 2:
        pairs = [(clean[i], clean[i + 1]) for i in range(n - 1)]
        num = sum((a - mean_r) * (b - mean_r) for a, b in pairs)
        denom = sum((r - mean_r) ** 2 for r in clean)
        lag1_autocorr = num / max(denom, 1e-15)
        mean_reversion = max(-1.0, min(1.0, ))
    else:
        mean_reversion = 0.0
    short_window = min(10, n)
    short_clean = clean[-short_window:]
    short_mean = sum(short_clean) / len(short_clean)
    short_var = sum((r - short_mean) ** 2 for r in short_clean) / max(len(short_clean) - 1, 1)
    short_vol = math.sqrt(max(short_var, 0.0))
    full_vol = max(volatility, 1e-8)
    stress_raw = (short_vol / full_vol) - 1.0
    stress = max(0.0, min(1.0, stress_raw * 0.5 + 0.5))
    momentum = max(-1.0, min(1.0, recent_mean / max(full_vol, 1e-8)))
    liquidity = 1.0 - stress
    return {
        "volatility":     volatility,
        "trend_strength": trend_strength,
        "mean_reversion": mean_reversion,
        "stress":         stress,
        "momentum":       momentum,
        "liquidity":      liquidity,
    }


# ---------------------------------------------------------------------------
# Internal helpers (unchanged from v1.1.0)
# ---------------------------------------------------------------------------

def x__extract_regime_features__mutmut_82(returns_history: list) -> dict:
    clean = [r if math.isfinite(r) else 0.0 for r in returns_history]
    n = len(clean)
    mean_r = sum(clean) / n
    variance = sum((r - mean_r) ** 2 for r in clean) / max(n - 1, 1)
    volatility = math.sqrt(max(variance, 0.0))
    window = min(5, n)
    recent = clean[-window:]
    recent_mean = sum(recent) / window
    trend_strength = recent_mean / max(volatility, 1e-8)
    if n >= 2:
        pairs = [(clean[i], clean[i + 1]) for i in range(n - 1)]
        num = sum((a - mean_r) * (b - mean_r) for a, b in pairs)
        denom = sum((r - mean_r) ** 2 for r in clean)
        lag1_autocorr = num / max(denom, 1e-15)
        mean_reversion = max(-1.0, min(2.0, -lag1_autocorr))
    else:
        mean_reversion = 0.0
    short_window = min(10, n)
    short_clean = clean[-short_window:]
    short_mean = sum(short_clean) / len(short_clean)
    short_var = sum((r - short_mean) ** 2 for r in short_clean) / max(len(short_clean) - 1, 1)
    short_vol = math.sqrt(max(short_var, 0.0))
    full_vol = max(volatility, 1e-8)
    stress_raw = (short_vol / full_vol) - 1.0
    stress = max(0.0, min(1.0, stress_raw * 0.5 + 0.5))
    momentum = max(-1.0, min(1.0, recent_mean / max(full_vol, 1e-8)))
    liquidity = 1.0 - stress
    return {
        "volatility":     volatility,
        "trend_strength": trend_strength,
        "mean_reversion": mean_reversion,
        "stress":         stress,
        "momentum":       momentum,
        "liquidity":      liquidity,
    }


# ---------------------------------------------------------------------------
# Internal helpers (unchanged from v1.1.0)
# ---------------------------------------------------------------------------

def x__extract_regime_features__mutmut_83(returns_history: list) -> dict:
    clean = [r if math.isfinite(r) else 0.0 for r in returns_history]
    n = len(clean)
    mean_r = sum(clean) / n
    variance = sum((r - mean_r) ** 2 for r in clean) / max(n - 1, 1)
    volatility = math.sqrt(max(variance, 0.0))
    window = min(5, n)
    recent = clean[-window:]
    recent_mean = sum(recent) / window
    trend_strength = recent_mean / max(volatility, 1e-8)
    if n >= 2:
        pairs = [(clean[i], clean[i + 1]) for i in range(n - 1)]
        num = sum((a - mean_r) * (b - mean_r) for a, b in pairs)
        denom = sum((r - mean_r) ** 2 for r in clean)
        lag1_autocorr = num / max(denom, 1e-15)
        mean_reversion = max(-1.0, min(1.0, +lag1_autocorr))
    else:
        mean_reversion = 0.0
    short_window = min(10, n)
    short_clean = clean[-short_window:]
    short_mean = sum(short_clean) / len(short_clean)
    short_var = sum((r - short_mean) ** 2 for r in short_clean) / max(len(short_clean) - 1, 1)
    short_vol = math.sqrt(max(short_var, 0.0))
    full_vol = max(volatility, 1e-8)
    stress_raw = (short_vol / full_vol) - 1.0
    stress = max(0.0, min(1.0, stress_raw * 0.5 + 0.5))
    momentum = max(-1.0, min(1.0, recent_mean / max(full_vol, 1e-8)))
    liquidity = 1.0 - stress
    return {
        "volatility":     volatility,
        "trend_strength": trend_strength,
        "mean_reversion": mean_reversion,
        "stress":         stress,
        "momentum":       momentum,
        "liquidity":      liquidity,
    }


# ---------------------------------------------------------------------------
# Internal helpers (unchanged from v1.1.0)
# ---------------------------------------------------------------------------

def x__extract_regime_features__mutmut_84(returns_history: list) -> dict:
    clean = [r if math.isfinite(r) else 0.0 for r in returns_history]
    n = len(clean)
    mean_r = sum(clean) / n
    variance = sum((r - mean_r) ** 2 for r in clean) / max(n - 1, 1)
    volatility = math.sqrt(max(variance, 0.0))
    window = min(5, n)
    recent = clean[-window:]
    recent_mean = sum(recent) / window
    trend_strength = recent_mean / max(volatility, 1e-8)
    if n >= 2:
        pairs = [(clean[i], clean[i + 1]) for i in range(n - 1)]
        num = sum((a - mean_r) * (b - mean_r) for a, b in pairs)
        denom = sum((r - mean_r) ** 2 for r in clean)
        lag1_autocorr = num / max(denom, 1e-15)
        mean_reversion = max(-1.0, min(1.0, -lag1_autocorr))
    else:
        mean_reversion = None
    short_window = min(10, n)
    short_clean = clean[-short_window:]
    short_mean = sum(short_clean) / len(short_clean)
    short_var = sum((r - short_mean) ** 2 for r in short_clean) / max(len(short_clean) - 1, 1)
    short_vol = math.sqrt(max(short_var, 0.0))
    full_vol = max(volatility, 1e-8)
    stress_raw = (short_vol / full_vol) - 1.0
    stress = max(0.0, min(1.0, stress_raw * 0.5 + 0.5))
    momentum = max(-1.0, min(1.0, recent_mean / max(full_vol, 1e-8)))
    liquidity = 1.0 - stress
    return {
        "volatility":     volatility,
        "trend_strength": trend_strength,
        "mean_reversion": mean_reversion,
        "stress":         stress,
        "momentum":       momentum,
        "liquidity":      liquidity,
    }


# ---------------------------------------------------------------------------
# Internal helpers (unchanged from v1.1.0)
# ---------------------------------------------------------------------------

def x__extract_regime_features__mutmut_85(returns_history: list) -> dict:
    clean = [r if math.isfinite(r) else 0.0 for r in returns_history]
    n = len(clean)
    mean_r = sum(clean) / n
    variance = sum((r - mean_r) ** 2 for r in clean) / max(n - 1, 1)
    volatility = math.sqrt(max(variance, 0.0))
    window = min(5, n)
    recent = clean[-window:]
    recent_mean = sum(recent) / window
    trend_strength = recent_mean / max(volatility, 1e-8)
    if n >= 2:
        pairs = [(clean[i], clean[i + 1]) for i in range(n - 1)]
        num = sum((a - mean_r) * (b - mean_r) for a, b in pairs)
        denom = sum((r - mean_r) ** 2 for r in clean)
        lag1_autocorr = num / max(denom, 1e-15)
        mean_reversion = max(-1.0, min(1.0, -lag1_autocorr))
    else:
        mean_reversion = 1.0
    short_window = min(10, n)
    short_clean = clean[-short_window:]
    short_mean = sum(short_clean) / len(short_clean)
    short_var = sum((r - short_mean) ** 2 for r in short_clean) / max(len(short_clean) - 1, 1)
    short_vol = math.sqrt(max(short_var, 0.0))
    full_vol = max(volatility, 1e-8)
    stress_raw = (short_vol / full_vol) - 1.0
    stress = max(0.0, min(1.0, stress_raw * 0.5 + 0.5))
    momentum = max(-1.0, min(1.0, recent_mean / max(full_vol, 1e-8)))
    liquidity = 1.0 - stress
    return {
        "volatility":     volatility,
        "trend_strength": trend_strength,
        "mean_reversion": mean_reversion,
        "stress":         stress,
        "momentum":       momentum,
        "liquidity":      liquidity,
    }


# ---------------------------------------------------------------------------
# Internal helpers (unchanged from v1.1.0)
# ---------------------------------------------------------------------------

def x__extract_regime_features__mutmut_86(returns_history: list) -> dict:
    clean = [r if math.isfinite(r) else 0.0 for r in returns_history]
    n = len(clean)
    mean_r = sum(clean) / n
    variance = sum((r - mean_r) ** 2 for r in clean) / max(n - 1, 1)
    volatility = math.sqrt(max(variance, 0.0))
    window = min(5, n)
    recent = clean[-window:]
    recent_mean = sum(recent) / window
    trend_strength = recent_mean / max(volatility, 1e-8)
    if n >= 2:
        pairs = [(clean[i], clean[i + 1]) for i in range(n - 1)]
        num = sum((a - mean_r) * (b - mean_r) for a, b in pairs)
        denom = sum((r - mean_r) ** 2 for r in clean)
        lag1_autocorr = num / max(denom, 1e-15)
        mean_reversion = max(-1.0, min(1.0, -lag1_autocorr))
    else:
        mean_reversion = 0.0
    short_window = None
    short_clean = clean[-short_window:]
    short_mean = sum(short_clean) / len(short_clean)
    short_var = sum((r - short_mean) ** 2 for r in short_clean) / max(len(short_clean) - 1, 1)
    short_vol = math.sqrt(max(short_var, 0.0))
    full_vol = max(volatility, 1e-8)
    stress_raw = (short_vol / full_vol) - 1.0
    stress = max(0.0, min(1.0, stress_raw * 0.5 + 0.5))
    momentum = max(-1.0, min(1.0, recent_mean / max(full_vol, 1e-8)))
    liquidity = 1.0 - stress
    return {
        "volatility":     volatility,
        "trend_strength": trend_strength,
        "mean_reversion": mean_reversion,
        "stress":         stress,
        "momentum":       momentum,
        "liquidity":      liquidity,
    }


# ---------------------------------------------------------------------------
# Internal helpers (unchanged from v1.1.0)
# ---------------------------------------------------------------------------

def x__extract_regime_features__mutmut_87(returns_history: list) -> dict:
    clean = [r if math.isfinite(r) else 0.0 for r in returns_history]
    n = len(clean)
    mean_r = sum(clean) / n
    variance = sum((r - mean_r) ** 2 for r in clean) / max(n - 1, 1)
    volatility = math.sqrt(max(variance, 0.0))
    window = min(5, n)
    recent = clean[-window:]
    recent_mean = sum(recent) / window
    trend_strength = recent_mean / max(volatility, 1e-8)
    if n >= 2:
        pairs = [(clean[i], clean[i + 1]) for i in range(n - 1)]
        num = sum((a - mean_r) * (b - mean_r) for a, b in pairs)
        denom = sum((r - mean_r) ** 2 for r in clean)
        lag1_autocorr = num / max(denom, 1e-15)
        mean_reversion = max(-1.0, min(1.0, -lag1_autocorr))
    else:
        mean_reversion = 0.0
    short_window = min(None, n)
    short_clean = clean[-short_window:]
    short_mean = sum(short_clean) / len(short_clean)
    short_var = sum((r - short_mean) ** 2 for r in short_clean) / max(len(short_clean) - 1, 1)
    short_vol = math.sqrt(max(short_var, 0.0))
    full_vol = max(volatility, 1e-8)
    stress_raw = (short_vol / full_vol) - 1.0
    stress = max(0.0, min(1.0, stress_raw * 0.5 + 0.5))
    momentum = max(-1.0, min(1.0, recent_mean / max(full_vol, 1e-8)))
    liquidity = 1.0 - stress
    return {
        "volatility":     volatility,
        "trend_strength": trend_strength,
        "mean_reversion": mean_reversion,
        "stress":         stress,
        "momentum":       momentum,
        "liquidity":      liquidity,
    }


# ---------------------------------------------------------------------------
# Internal helpers (unchanged from v1.1.0)
# ---------------------------------------------------------------------------

def x__extract_regime_features__mutmut_88(returns_history: list) -> dict:
    clean = [r if math.isfinite(r) else 0.0 for r in returns_history]
    n = len(clean)
    mean_r = sum(clean) / n
    variance = sum((r - mean_r) ** 2 for r in clean) / max(n - 1, 1)
    volatility = math.sqrt(max(variance, 0.0))
    window = min(5, n)
    recent = clean[-window:]
    recent_mean = sum(recent) / window
    trend_strength = recent_mean / max(volatility, 1e-8)
    if n >= 2:
        pairs = [(clean[i], clean[i + 1]) for i in range(n - 1)]
        num = sum((a - mean_r) * (b - mean_r) for a, b in pairs)
        denom = sum((r - mean_r) ** 2 for r in clean)
        lag1_autocorr = num / max(denom, 1e-15)
        mean_reversion = max(-1.0, min(1.0, -lag1_autocorr))
    else:
        mean_reversion = 0.0
    short_window = min(10, None)
    short_clean = clean[-short_window:]
    short_mean = sum(short_clean) / len(short_clean)
    short_var = sum((r - short_mean) ** 2 for r in short_clean) / max(len(short_clean) - 1, 1)
    short_vol = math.sqrt(max(short_var, 0.0))
    full_vol = max(volatility, 1e-8)
    stress_raw = (short_vol / full_vol) - 1.0
    stress = max(0.0, min(1.0, stress_raw * 0.5 + 0.5))
    momentum = max(-1.0, min(1.0, recent_mean / max(full_vol, 1e-8)))
    liquidity = 1.0 - stress
    return {
        "volatility":     volatility,
        "trend_strength": trend_strength,
        "mean_reversion": mean_reversion,
        "stress":         stress,
        "momentum":       momentum,
        "liquidity":      liquidity,
    }


# ---------------------------------------------------------------------------
# Internal helpers (unchanged from v1.1.0)
# ---------------------------------------------------------------------------

def x__extract_regime_features__mutmut_89(returns_history: list) -> dict:
    clean = [r if math.isfinite(r) else 0.0 for r in returns_history]
    n = len(clean)
    mean_r = sum(clean) / n
    variance = sum((r - mean_r) ** 2 for r in clean) / max(n - 1, 1)
    volatility = math.sqrt(max(variance, 0.0))
    window = min(5, n)
    recent = clean[-window:]
    recent_mean = sum(recent) / window
    trend_strength = recent_mean / max(volatility, 1e-8)
    if n >= 2:
        pairs = [(clean[i], clean[i + 1]) for i in range(n - 1)]
        num = sum((a - mean_r) * (b - mean_r) for a, b in pairs)
        denom = sum((r - mean_r) ** 2 for r in clean)
        lag1_autocorr = num / max(denom, 1e-15)
        mean_reversion = max(-1.0, min(1.0, -lag1_autocorr))
    else:
        mean_reversion = 0.0
    short_window = min(n)
    short_clean = clean[-short_window:]
    short_mean = sum(short_clean) / len(short_clean)
    short_var = sum((r - short_mean) ** 2 for r in short_clean) / max(len(short_clean) - 1, 1)
    short_vol = math.sqrt(max(short_var, 0.0))
    full_vol = max(volatility, 1e-8)
    stress_raw = (short_vol / full_vol) - 1.0
    stress = max(0.0, min(1.0, stress_raw * 0.5 + 0.5))
    momentum = max(-1.0, min(1.0, recent_mean / max(full_vol, 1e-8)))
    liquidity = 1.0 - stress
    return {
        "volatility":     volatility,
        "trend_strength": trend_strength,
        "mean_reversion": mean_reversion,
        "stress":         stress,
        "momentum":       momentum,
        "liquidity":      liquidity,
    }


# ---------------------------------------------------------------------------
# Internal helpers (unchanged from v1.1.0)
# ---------------------------------------------------------------------------

def x__extract_regime_features__mutmut_90(returns_history: list) -> dict:
    clean = [r if math.isfinite(r) else 0.0 for r in returns_history]
    n = len(clean)
    mean_r = sum(clean) / n
    variance = sum((r - mean_r) ** 2 for r in clean) / max(n - 1, 1)
    volatility = math.sqrt(max(variance, 0.0))
    window = min(5, n)
    recent = clean[-window:]
    recent_mean = sum(recent) / window
    trend_strength = recent_mean / max(volatility, 1e-8)
    if n >= 2:
        pairs = [(clean[i], clean[i + 1]) for i in range(n - 1)]
        num = sum((a - mean_r) * (b - mean_r) for a, b in pairs)
        denom = sum((r - mean_r) ** 2 for r in clean)
        lag1_autocorr = num / max(denom, 1e-15)
        mean_reversion = max(-1.0, min(1.0, -lag1_autocorr))
    else:
        mean_reversion = 0.0
    short_window = min(10, )
    short_clean = clean[-short_window:]
    short_mean = sum(short_clean) / len(short_clean)
    short_var = sum((r - short_mean) ** 2 for r in short_clean) / max(len(short_clean) - 1, 1)
    short_vol = math.sqrt(max(short_var, 0.0))
    full_vol = max(volatility, 1e-8)
    stress_raw = (short_vol / full_vol) - 1.0
    stress = max(0.0, min(1.0, stress_raw * 0.5 + 0.5))
    momentum = max(-1.0, min(1.0, recent_mean / max(full_vol, 1e-8)))
    liquidity = 1.0 - stress
    return {
        "volatility":     volatility,
        "trend_strength": trend_strength,
        "mean_reversion": mean_reversion,
        "stress":         stress,
        "momentum":       momentum,
        "liquidity":      liquidity,
    }


# ---------------------------------------------------------------------------
# Internal helpers (unchanged from v1.1.0)
# ---------------------------------------------------------------------------

def x__extract_regime_features__mutmut_91(returns_history: list) -> dict:
    clean = [r if math.isfinite(r) else 0.0 for r in returns_history]
    n = len(clean)
    mean_r = sum(clean) / n
    variance = sum((r - mean_r) ** 2 for r in clean) / max(n - 1, 1)
    volatility = math.sqrt(max(variance, 0.0))
    window = min(5, n)
    recent = clean[-window:]
    recent_mean = sum(recent) / window
    trend_strength = recent_mean / max(volatility, 1e-8)
    if n >= 2:
        pairs = [(clean[i], clean[i + 1]) for i in range(n - 1)]
        num = sum((a - mean_r) * (b - mean_r) for a, b in pairs)
        denom = sum((r - mean_r) ** 2 for r in clean)
        lag1_autocorr = num / max(denom, 1e-15)
        mean_reversion = max(-1.0, min(1.0, -lag1_autocorr))
    else:
        mean_reversion = 0.0
    short_window = min(11, n)
    short_clean = clean[-short_window:]
    short_mean = sum(short_clean) / len(short_clean)
    short_var = sum((r - short_mean) ** 2 for r in short_clean) / max(len(short_clean) - 1, 1)
    short_vol = math.sqrt(max(short_var, 0.0))
    full_vol = max(volatility, 1e-8)
    stress_raw = (short_vol / full_vol) - 1.0
    stress = max(0.0, min(1.0, stress_raw * 0.5 + 0.5))
    momentum = max(-1.0, min(1.0, recent_mean / max(full_vol, 1e-8)))
    liquidity = 1.0 - stress
    return {
        "volatility":     volatility,
        "trend_strength": trend_strength,
        "mean_reversion": mean_reversion,
        "stress":         stress,
        "momentum":       momentum,
        "liquidity":      liquidity,
    }


# ---------------------------------------------------------------------------
# Internal helpers (unchanged from v1.1.0)
# ---------------------------------------------------------------------------

def x__extract_regime_features__mutmut_92(returns_history: list) -> dict:
    clean = [r if math.isfinite(r) else 0.0 for r in returns_history]
    n = len(clean)
    mean_r = sum(clean) / n
    variance = sum((r - mean_r) ** 2 for r in clean) / max(n - 1, 1)
    volatility = math.sqrt(max(variance, 0.0))
    window = min(5, n)
    recent = clean[-window:]
    recent_mean = sum(recent) / window
    trend_strength = recent_mean / max(volatility, 1e-8)
    if n >= 2:
        pairs = [(clean[i], clean[i + 1]) for i in range(n - 1)]
        num = sum((a - mean_r) * (b - mean_r) for a, b in pairs)
        denom = sum((r - mean_r) ** 2 for r in clean)
        lag1_autocorr = num / max(denom, 1e-15)
        mean_reversion = max(-1.0, min(1.0, -lag1_autocorr))
    else:
        mean_reversion = 0.0
    short_window = min(10, n)
    short_clean = None
    short_mean = sum(short_clean) / len(short_clean)
    short_var = sum((r - short_mean) ** 2 for r in short_clean) / max(len(short_clean) - 1, 1)
    short_vol = math.sqrt(max(short_var, 0.0))
    full_vol = max(volatility, 1e-8)
    stress_raw = (short_vol / full_vol) - 1.0
    stress = max(0.0, min(1.0, stress_raw * 0.5 + 0.5))
    momentum = max(-1.0, min(1.0, recent_mean / max(full_vol, 1e-8)))
    liquidity = 1.0 - stress
    return {
        "volatility":     volatility,
        "trend_strength": trend_strength,
        "mean_reversion": mean_reversion,
        "stress":         stress,
        "momentum":       momentum,
        "liquidity":      liquidity,
    }


# ---------------------------------------------------------------------------
# Internal helpers (unchanged from v1.1.0)
# ---------------------------------------------------------------------------

def x__extract_regime_features__mutmut_93(returns_history: list) -> dict:
    clean = [r if math.isfinite(r) else 0.0 for r in returns_history]
    n = len(clean)
    mean_r = sum(clean) / n
    variance = sum((r - mean_r) ** 2 for r in clean) / max(n - 1, 1)
    volatility = math.sqrt(max(variance, 0.0))
    window = min(5, n)
    recent = clean[-window:]
    recent_mean = sum(recent) / window
    trend_strength = recent_mean / max(volatility, 1e-8)
    if n >= 2:
        pairs = [(clean[i], clean[i + 1]) for i in range(n - 1)]
        num = sum((a - mean_r) * (b - mean_r) for a, b in pairs)
        denom = sum((r - mean_r) ** 2 for r in clean)
        lag1_autocorr = num / max(denom, 1e-15)
        mean_reversion = max(-1.0, min(1.0, -lag1_autocorr))
    else:
        mean_reversion = 0.0
    short_window = min(10, n)
    short_clean = clean[+short_window:]
    short_mean = sum(short_clean) / len(short_clean)
    short_var = sum((r - short_mean) ** 2 for r in short_clean) / max(len(short_clean) - 1, 1)
    short_vol = math.sqrt(max(short_var, 0.0))
    full_vol = max(volatility, 1e-8)
    stress_raw = (short_vol / full_vol) - 1.0
    stress = max(0.0, min(1.0, stress_raw * 0.5 + 0.5))
    momentum = max(-1.0, min(1.0, recent_mean / max(full_vol, 1e-8)))
    liquidity = 1.0 - stress
    return {
        "volatility":     volatility,
        "trend_strength": trend_strength,
        "mean_reversion": mean_reversion,
        "stress":         stress,
        "momentum":       momentum,
        "liquidity":      liquidity,
    }


# ---------------------------------------------------------------------------
# Internal helpers (unchanged from v1.1.0)
# ---------------------------------------------------------------------------

def x__extract_regime_features__mutmut_94(returns_history: list) -> dict:
    clean = [r if math.isfinite(r) else 0.0 for r in returns_history]
    n = len(clean)
    mean_r = sum(clean) / n
    variance = sum((r - mean_r) ** 2 for r in clean) / max(n - 1, 1)
    volatility = math.sqrt(max(variance, 0.0))
    window = min(5, n)
    recent = clean[-window:]
    recent_mean = sum(recent) / window
    trend_strength = recent_mean / max(volatility, 1e-8)
    if n >= 2:
        pairs = [(clean[i], clean[i + 1]) for i in range(n - 1)]
        num = sum((a - mean_r) * (b - mean_r) for a, b in pairs)
        denom = sum((r - mean_r) ** 2 for r in clean)
        lag1_autocorr = num / max(denom, 1e-15)
        mean_reversion = max(-1.0, min(1.0, -lag1_autocorr))
    else:
        mean_reversion = 0.0
    short_window = min(10, n)
    short_clean = clean[-short_window:]
    short_mean = None
    short_var = sum((r - short_mean) ** 2 for r in short_clean) / max(len(short_clean) - 1, 1)
    short_vol = math.sqrt(max(short_var, 0.0))
    full_vol = max(volatility, 1e-8)
    stress_raw = (short_vol / full_vol) - 1.0
    stress = max(0.0, min(1.0, stress_raw * 0.5 + 0.5))
    momentum = max(-1.0, min(1.0, recent_mean / max(full_vol, 1e-8)))
    liquidity = 1.0 - stress
    return {
        "volatility":     volatility,
        "trend_strength": trend_strength,
        "mean_reversion": mean_reversion,
        "stress":         stress,
        "momentum":       momentum,
        "liquidity":      liquidity,
    }


# ---------------------------------------------------------------------------
# Internal helpers (unchanged from v1.1.0)
# ---------------------------------------------------------------------------

def x__extract_regime_features__mutmut_95(returns_history: list) -> dict:
    clean = [r if math.isfinite(r) else 0.0 for r in returns_history]
    n = len(clean)
    mean_r = sum(clean) / n
    variance = sum((r - mean_r) ** 2 for r in clean) / max(n - 1, 1)
    volatility = math.sqrt(max(variance, 0.0))
    window = min(5, n)
    recent = clean[-window:]
    recent_mean = sum(recent) / window
    trend_strength = recent_mean / max(volatility, 1e-8)
    if n >= 2:
        pairs = [(clean[i], clean[i + 1]) for i in range(n - 1)]
        num = sum((a - mean_r) * (b - mean_r) for a, b in pairs)
        denom = sum((r - mean_r) ** 2 for r in clean)
        lag1_autocorr = num / max(denom, 1e-15)
        mean_reversion = max(-1.0, min(1.0, -lag1_autocorr))
    else:
        mean_reversion = 0.0
    short_window = min(10, n)
    short_clean = clean[-short_window:]
    short_mean = sum(short_clean) * len(short_clean)
    short_var = sum((r - short_mean) ** 2 for r in short_clean) / max(len(short_clean) - 1, 1)
    short_vol = math.sqrt(max(short_var, 0.0))
    full_vol = max(volatility, 1e-8)
    stress_raw = (short_vol / full_vol) - 1.0
    stress = max(0.0, min(1.0, stress_raw * 0.5 + 0.5))
    momentum = max(-1.0, min(1.0, recent_mean / max(full_vol, 1e-8)))
    liquidity = 1.0 - stress
    return {
        "volatility":     volatility,
        "trend_strength": trend_strength,
        "mean_reversion": mean_reversion,
        "stress":         stress,
        "momentum":       momentum,
        "liquidity":      liquidity,
    }


# ---------------------------------------------------------------------------
# Internal helpers (unchanged from v1.1.0)
# ---------------------------------------------------------------------------

def x__extract_regime_features__mutmut_96(returns_history: list) -> dict:
    clean = [r if math.isfinite(r) else 0.0 for r in returns_history]
    n = len(clean)
    mean_r = sum(clean) / n
    variance = sum((r - mean_r) ** 2 for r in clean) / max(n - 1, 1)
    volatility = math.sqrt(max(variance, 0.0))
    window = min(5, n)
    recent = clean[-window:]
    recent_mean = sum(recent) / window
    trend_strength = recent_mean / max(volatility, 1e-8)
    if n >= 2:
        pairs = [(clean[i], clean[i + 1]) for i in range(n - 1)]
        num = sum((a - mean_r) * (b - mean_r) for a, b in pairs)
        denom = sum((r - mean_r) ** 2 for r in clean)
        lag1_autocorr = num / max(denom, 1e-15)
        mean_reversion = max(-1.0, min(1.0, -lag1_autocorr))
    else:
        mean_reversion = 0.0
    short_window = min(10, n)
    short_clean = clean[-short_window:]
    short_mean = sum(None) / len(short_clean)
    short_var = sum((r - short_mean) ** 2 for r in short_clean) / max(len(short_clean) - 1, 1)
    short_vol = math.sqrt(max(short_var, 0.0))
    full_vol = max(volatility, 1e-8)
    stress_raw = (short_vol / full_vol) - 1.0
    stress = max(0.0, min(1.0, stress_raw * 0.5 + 0.5))
    momentum = max(-1.0, min(1.0, recent_mean / max(full_vol, 1e-8)))
    liquidity = 1.0 - stress
    return {
        "volatility":     volatility,
        "trend_strength": trend_strength,
        "mean_reversion": mean_reversion,
        "stress":         stress,
        "momentum":       momentum,
        "liquidity":      liquidity,
    }


# ---------------------------------------------------------------------------
# Internal helpers (unchanged from v1.1.0)
# ---------------------------------------------------------------------------

def x__extract_regime_features__mutmut_97(returns_history: list) -> dict:
    clean = [r if math.isfinite(r) else 0.0 for r in returns_history]
    n = len(clean)
    mean_r = sum(clean) / n
    variance = sum((r - mean_r) ** 2 for r in clean) / max(n - 1, 1)
    volatility = math.sqrt(max(variance, 0.0))
    window = min(5, n)
    recent = clean[-window:]
    recent_mean = sum(recent) / window
    trend_strength = recent_mean / max(volatility, 1e-8)
    if n >= 2:
        pairs = [(clean[i], clean[i + 1]) for i in range(n - 1)]
        num = sum((a - mean_r) * (b - mean_r) for a, b in pairs)
        denom = sum((r - mean_r) ** 2 for r in clean)
        lag1_autocorr = num / max(denom, 1e-15)
        mean_reversion = max(-1.0, min(1.0, -lag1_autocorr))
    else:
        mean_reversion = 0.0
    short_window = min(10, n)
    short_clean = clean[-short_window:]
    short_mean = sum(short_clean) / len(short_clean)
    short_var = None
    short_vol = math.sqrt(max(short_var, 0.0))
    full_vol = max(volatility, 1e-8)
    stress_raw = (short_vol / full_vol) - 1.0
    stress = max(0.0, min(1.0, stress_raw * 0.5 + 0.5))
    momentum = max(-1.0, min(1.0, recent_mean / max(full_vol, 1e-8)))
    liquidity = 1.0 - stress
    return {
        "volatility":     volatility,
        "trend_strength": trend_strength,
        "mean_reversion": mean_reversion,
        "stress":         stress,
        "momentum":       momentum,
        "liquidity":      liquidity,
    }


# ---------------------------------------------------------------------------
# Internal helpers (unchanged from v1.1.0)
# ---------------------------------------------------------------------------

def x__extract_regime_features__mutmut_98(returns_history: list) -> dict:
    clean = [r if math.isfinite(r) else 0.0 for r in returns_history]
    n = len(clean)
    mean_r = sum(clean) / n
    variance = sum((r - mean_r) ** 2 for r in clean) / max(n - 1, 1)
    volatility = math.sqrt(max(variance, 0.0))
    window = min(5, n)
    recent = clean[-window:]
    recent_mean = sum(recent) / window
    trend_strength = recent_mean / max(volatility, 1e-8)
    if n >= 2:
        pairs = [(clean[i], clean[i + 1]) for i in range(n - 1)]
        num = sum((a - mean_r) * (b - mean_r) for a, b in pairs)
        denom = sum((r - mean_r) ** 2 for r in clean)
        lag1_autocorr = num / max(denom, 1e-15)
        mean_reversion = max(-1.0, min(1.0, -lag1_autocorr))
    else:
        mean_reversion = 0.0
    short_window = min(10, n)
    short_clean = clean[-short_window:]
    short_mean = sum(short_clean) / len(short_clean)
    short_var = sum((r - short_mean) ** 2 for r in short_clean) * max(len(short_clean) - 1, 1)
    short_vol = math.sqrt(max(short_var, 0.0))
    full_vol = max(volatility, 1e-8)
    stress_raw = (short_vol / full_vol) - 1.0
    stress = max(0.0, min(1.0, stress_raw * 0.5 + 0.5))
    momentum = max(-1.0, min(1.0, recent_mean / max(full_vol, 1e-8)))
    liquidity = 1.0 - stress
    return {
        "volatility":     volatility,
        "trend_strength": trend_strength,
        "mean_reversion": mean_reversion,
        "stress":         stress,
        "momentum":       momentum,
        "liquidity":      liquidity,
    }


# ---------------------------------------------------------------------------
# Internal helpers (unchanged from v1.1.0)
# ---------------------------------------------------------------------------

def x__extract_regime_features__mutmut_99(returns_history: list) -> dict:
    clean = [r if math.isfinite(r) else 0.0 for r in returns_history]
    n = len(clean)
    mean_r = sum(clean) / n
    variance = sum((r - mean_r) ** 2 for r in clean) / max(n - 1, 1)
    volatility = math.sqrt(max(variance, 0.0))
    window = min(5, n)
    recent = clean[-window:]
    recent_mean = sum(recent) / window
    trend_strength = recent_mean / max(volatility, 1e-8)
    if n >= 2:
        pairs = [(clean[i], clean[i + 1]) for i in range(n - 1)]
        num = sum((a - mean_r) * (b - mean_r) for a, b in pairs)
        denom = sum((r - mean_r) ** 2 for r in clean)
        lag1_autocorr = num / max(denom, 1e-15)
        mean_reversion = max(-1.0, min(1.0, -lag1_autocorr))
    else:
        mean_reversion = 0.0
    short_window = min(10, n)
    short_clean = clean[-short_window:]
    short_mean = sum(short_clean) / len(short_clean)
    short_var = sum(None) / max(len(short_clean) - 1, 1)
    short_vol = math.sqrt(max(short_var, 0.0))
    full_vol = max(volatility, 1e-8)
    stress_raw = (short_vol / full_vol) - 1.0
    stress = max(0.0, min(1.0, stress_raw * 0.5 + 0.5))
    momentum = max(-1.0, min(1.0, recent_mean / max(full_vol, 1e-8)))
    liquidity = 1.0 - stress
    return {
        "volatility":     volatility,
        "trend_strength": trend_strength,
        "mean_reversion": mean_reversion,
        "stress":         stress,
        "momentum":       momentum,
        "liquidity":      liquidity,
    }


# ---------------------------------------------------------------------------
# Internal helpers (unchanged from v1.1.0)
# ---------------------------------------------------------------------------

def x__extract_regime_features__mutmut_100(returns_history: list) -> dict:
    clean = [r if math.isfinite(r) else 0.0 for r in returns_history]
    n = len(clean)
    mean_r = sum(clean) / n
    variance = sum((r - mean_r) ** 2 for r in clean) / max(n - 1, 1)
    volatility = math.sqrt(max(variance, 0.0))
    window = min(5, n)
    recent = clean[-window:]
    recent_mean = sum(recent) / window
    trend_strength = recent_mean / max(volatility, 1e-8)
    if n >= 2:
        pairs = [(clean[i], clean[i + 1]) for i in range(n - 1)]
        num = sum((a - mean_r) * (b - mean_r) for a, b in pairs)
        denom = sum((r - mean_r) ** 2 for r in clean)
        lag1_autocorr = num / max(denom, 1e-15)
        mean_reversion = max(-1.0, min(1.0, -lag1_autocorr))
    else:
        mean_reversion = 0.0
    short_window = min(10, n)
    short_clean = clean[-short_window:]
    short_mean = sum(short_clean) / len(short_clean)
    short_var = sum((r - short_mean) * 2 for r in short_clean) / max(len(short_clean) - 1, 1)
    short_vol = math.sqrt(max(short_var, 0.0))
    full_vol = max(volatility, 1e-8)
    stress_raw = (short_vol / full_vol) - 1.0
    stress = max(0.0, min(1.0, stress_raw * 0.5 + 0.5))
    momentum = max(-1.0, min(1.0, recent_mean / max(full_vol, 1e-8)))
    liquidity = 1.0 - stress
    return {
        "volatility":     volatility,
        "trend_strength": trend_strength,
        "mean_reversion": mean_reversion,
        "stress":         stress,
        "momentum":       momentum,
        "liquidity":      liquidity,
    }


# ---------------------------------------------------------------------------
# Internal helpers (unchanged from v1.1.0)
# ---------------------------------------------------------------------------

def x__extract_regime_features__mutmut_101(returns_history: list) -> dict:
    clean = [r if math.isfinite(r) else 0.0 for r in returns_history]
    n = len(clean)
    mean_r = sum(clean) / n
    variance = sum((r - mean_r) ** 2 for r in clean) / max(n - 1, 1)
    volatility = math.sqrt(max(variance, 0.0))
    window = min(5, n)
    recent = clean[-window:]
    recent_mean = sum(recent) / window
    trend_strength = recent_mean / max(volatility, 1e-8)
    if n >= 2:
        pairs = [(clean[i], clean[i + 1]) for i in range(n - 1)]
        num = sum((a - mean_r) * (b - mean_r) for a, b in pairs)
        denom = sum((r - mean_r) ** 2 for r in clean)
        lag1_autocorr = num / max(denom, 1e-15)
        mean_reversion = max(-1.0, min(1.0, -lag1_autocorr))
    else:
        mean_reversion = 0.0
    short_window = min(10, n)
    short_clean = clean[-short_window:]
    short_mean = sum(short_clean) / len(short_clean)
    short_var = sum((r + short_mean) ** 2 for r in short_clean) / max(len(short_clean) - 1, 1)
    short_vol = math.sqrt(max(short_var, 0.0))
    full_vol = max(volatility, 1e-8)
    stress_raw = (short_vol / full_vol) - 1.0
    stress = max(0.0, min(1.0, stress_raw * 0.5 + 0.5))
    momentum = max(-1.0, min(1.0, recent_mean / max(full_vol, 1e-8)))
    liquidity = 1.0 - stress
    return {
        "volatility":     volatility,
        "trend_strength": trend_strength,
        "mean_reversion": mean_reversion,
        "stress":         stress,
        "momentum":       momentum,
        "liquidity":      liquidity,
    }


# ---------------------------------------------------------------------------
# Internal helpers (unchanged from v1.1.0)
# ---------------------------------------------------------------------------

def x__extract_regime_features__mutmut_102(returns_history: list) -> dict:
    clean = [r if math.isfinite(r) else 0.0 for r in returns_history]
    n = len(clean)
    mean_r = sum(clean) / n
    variance = sum((r - mean_r) ** 2 for r in clean) / max(n - 1, 1)
    volatility = math.sqrt(max(variance, 0.0))
    window = min(5, n)
    recent = clean[-window:]
    recent_mean = sum(recent) / window
    trend_strength = recent_mean / max(volatility, 1e-8)
    if n >= 2:
        pairs = [(clean[i], clean[i + 1]) for i in range(n - 1)]
        num = sum((a - mean_r) * (b - mean_r) for a, b in pairs)
        denom = sum((r - mean_r) ** 2 for r in clean)
        lag1_autocorr = num / max(denom, 1e-15)
        mean_reversion = max(-1.0, min(1.0, -lag1_autocorr))
    else:
        mean_reversion = 0.0
    short_window = min(10, n)
    short_clean = clean[-short_window:]
    short_mean = sum(short_clean) / len(short_clean)
    short_var = sum((r - short_mean) ** 3 for r in short_clean) / max(len(short_clean) - 1, 1)
    short_vol = math.sqrt(max(short_var, 0.0))
    full_vol = max(volatility, 1e-8)
    stress_raw = (short_vol / full_vol) - 1.0
    stress = max(0.0, min(1.0, stress_raw * 0.5 + 0.5))
    momentum = max(-1.0, min(1.0, recent_mean / max(full_vol, 1e-8)))
    liquidity = 1.0 - stress
    return {
        "volatility":     volatility,
        "trend_strength": trend_strength,
        "mean_reversion": mean_reversion,
        "stress":         stress,
        "momentum":       momentum,
        "liquidity":      liquidity,
    }


# ---------------------------------------------------------------------------
# Internal helpers (unchanged from v1.1.0)
# ---------------------------------------------------------------------------

def x__extract_regime_features__mutmut_103(returns_history: list) -> dict:
    clean = [r if math.isfinite(r) else 0.0 for r in returns_history]
    n = len(clean)
    mean_r = sum(clean) / n
    variance = sum((r - mean_r) ** 2 for r in clean) / max(n - 1, 1)
    volatility = math.sqrt(max(variance, 0.0))
    window = min(5, n)
    recent = clean[-window:]
    recent_mean = sum(recent) / window
    trend_strength = recent_mean / max(volatility, 1e-8)
    if n >= 2:
        pairs = [(clean[i], clean[i + 1]) for i in range(n - 1)]
        num = sum((a - mean_r) * (b - mean_r) for a, b in pairs)
        denom = sum((r - mean_r) ** 2 for r in clean)
        lag1_autocorr = num / max(denom, 1e-15)
        mean_reversion = max(-1.0, min(1.0, -lag1_autocorr))
    else:
        mean_reversion = 0.0
    short_window = min(10, n)
    short_clean = clean[-short_window:]
    short_mean = sum(short_clean) / len(short_clean)
    short_var = sum((r - short_mean) ** 2 for r in short_clean) / max(None, 1)
    short_vol = math.sqrt(max(short_var, 0.0))
    full_vol = max(volatility, 1e-8)
    stress_raw = (short_vol / full_vol) - 1.0
    stress = max(0.0, min(1.0, stress_raw * 0.5 + 0.5))
    momentum = max(-1.0, min(1.0, recent_mean / max(full_vol, 1e-8)))
    liquidity = 1.0 - stress
    return {
        "volatility":     volatility,
        "trend_strength": trend_strength,
        "mean_reversion": mean_reversion,
        "stress":         stress,
        "momentum":       momentum,
        "liquidity":      liquidity,
    }


# ---------------------------------------------------------------------------
# Internal helpers (unchanged from v1.1.0)
# ---------------------------------------------------------------------------

def x__extract_regime_features__mutmut_104(returns_history: list) -> dict:
    clean = [r if math.isfinite(r) else 0.0 for r in returns_history]
    n = len(clean)
    mean_r = sum(clean) / n
    variance = sum((r - mean_r) ** 2 for r in clean) / max(n - 1, 1)
    volatility = math.sqrt(max(variance, 0.0))
    window = min(5, n)
    recent = clean[-window:]
    recent_mean = sum(recent) / window
    trend_strength = recent_mean / max(volatility, 1e-8)
    if n >= 2:
        pairs = [(clean[i], clean[i + 1]) for i in range(n - 1)]
        num = sum((a - mean_r) * (b - mean_r) for a, b in pairs)
        denom = sum((r - mean_r) ** 2 for r in clean)
        lag1_autocorr = num / max(denom, 1e-15)
        mean_reversion = max(-1.0, min(1.0, -lag1_autocorr))
    else:
        mean_reversion = 0.0
    short_window = min(10, n)
    short_clean = clean[-short_window:]
    short_mean = sum(short_clean) / len(short_clean)
    short_var = sum((r - short_mean) ** 2 for r in short_clean) / max(len(short_clean) - 1, None)
    short_vol = math.sqrt(max(short_var, 0.0))
    full_vol = max(volatility, 1e-8)
    stress_raw = (short_vol / full_vol) - 1.0
    stress = max(0.0, min(1.0, stress_raw * 0.5 + 0.5))
    momentum = max(-1.0, min(1.0, recent_mean / max(full_vol, 1e-8)))
    liquidity = 1.0 - stress
    return {
        "volatility":     volatility,
        "trend_strength": trend_strength,
        "mean_reversion": mean_reversion,
        "stress":         stress,
        "momentum":       momentum,
        "liquidity":      liquidity,
    }


# ---------------------------------------------------------------------------
# Internal helpers (unchanged from v1.1.0)
# ---------------------------------------------------------------------------

def x__extract_regime_features__mutmut_105(returns_history: list) -> dict:
    clean = [r if math.isfinite(r) else 0.0 for r in returns_history]
    n = len(clean)
    mean_r = sum(clean) / n
    variance = sum((r - mean_r) ** 2 for r in clean) / max(n - 1, 1)
    volatility = math.sqrt(max(variance, 0.0))
    window = min(5, n)
    recent = clean[-window:]
    recent_mean = sum(recent) / window
    trend_strength = recent_mean / max(volatility, 1e-8)
    if n >= 2:
        pairs = [(clean[i], clean[i + 1]) for i in range(n - 1)]
        num = sum((a - mean_r) * (b - mean_r) for a, b in pairs)
        denom = sum((r - mean_r) ** 2 for r in clean)
        lag1_autocorr = num / max(denom, 1e-15)
        mean_reversion = max(-1.0, min(1.0, -lag1_autocorr))
    else:
        mean_reversion = 0.0
    short_window = min(10, n)
    short_clean = clean[-short_window:]
    short_mean = sum(short_clean) / len(short_clean)
    short_var = sum((r - short_mean) ** 2 for r in short_clean) / max(1)
    short_vol = math.sqrt(max(short_var, 0.0))
    full_vol = max(volatility, 1e-8)
    stress_raw = (short_vol / full_vol) - 1.0
    stress = max(0.0, min(1.0, stress_raw * 0.5 + 0.5))
    momentum = max(-1.0, min(1.0, recent_mean / max(full_vol, 1e-8)))
    liquidity = 1.0 - stress
    return {
        "volatility":     volatility,
        "trend_strength": trend_strength,
        "mean_reversion": mean_reversion,
        "stress":         stress,
        "momentum":       momentum,
        "liquidity":      liquidity,
    }


# ---------------------------------------------------------------------------
# Internal helpers (unchanged from v1.1.0)
# ---------------------------------------------------------------------------

def x__extract_regime_features__mutmut_106(returns_history: list) -> dict:
    clean = [r if math.isfinite(r) else 0.0 for r in returns_history]
    n = len(clean)
    mean_r = sum(clean) / n
    variance = sum((r - mean_r) ** 2 for r in clean) / max(n - 1, 1)
    volatility = math.sqrt(max(variance, 0.0))
    window = min(5, n)
    recent = clean[-window:]
    recent_mean = sum(recent) / window
    trend_strength = recent_mean / max(volatility, 1e-8)
    if n >= 2:
        pairs = [(clean[i], clean[i + 1]) for i in range(n - 1)]
        num = sum((a - mean_r) * (b - mean_r) for a, b in pairs)
        denom = sum((r - mean_r) ** 2 for r in clean)
        lag1_autocorr = num / max(denom, 1e-15)
        mean_reversion = max(-1.0, min(1.0, -lag1_autocorr))
    else:
        mean_reversion = 0.0
    short_window = min(10, n)
    short_clean = clean[-short_window:]
    short_mean = sum(short_clean) / len(short_clean)
    short_var = sum((r - short_mean) ** 2 for r in short_clean) / max(len(short_clean) - 1, )
    short_vol = math.sqrt(max(short_var, 0.0))
    full_vol = max(volatility, 1e-8)
    stress_raw = (short_vol / full_vol) - 1.0
    stress = max(0.0, min(1.0, stress_raw * 0.5 + 0.5))
    momentum = max(-1.0, min(1.0, recent_mean / max(full_vol, 1e-8)))
    liquidity = 1.0 - stress
    return {
        "volatility":     volatility,
        "trend_strength": trend_strength,
        "mean_reversion": mean_reversion,
        "stress":         stress,
        "momentum":       momentum,
        "liquidity":      liquidity,
    }


# ---------------------------------------------------------------------------
# Internal helpers (unchanged from v1.1.0)
# ---------------------------------------------------------------------------

def x__extract_regime_features__mutmut_107(returns_history: list) -> dict:
    clean = [r if math.isfinite(r) else 0.0 for r in returns_history]
    n = len(clean)
    mean_r = sum(clean) / n
    variance = sum((r - mean_r) ** 2 for r in clean) / max(n - 1, 1)
    volatility = math.sqrt(max(variance, 0.0))
    window = min(5, n)
    recent = clean[-window:]
    recent_mean = sum(recent) / window
    trend_strength = recent_mean / max(volatility, 1e-8)
    if n >= 2:
        pairs = [(clean[i], clean[i + 1]) for i in range(n - 1)]
        num = sum((a - mean_r) * (b - mean_r) for a, b in pairs)
        denom = sum((r - mean_r) ** 2 for r in clean)
        lag1_autocorr = num / max(denom, 1e-15)
        mean_reversion = max(-1.0, min(1.0, -lag1_autocorr))
    else:
        mean_reversion = 0.0
    short_window = min(10, n)
    short_clean = clean[-short_window:]
    short_mean = sum(short_clean) / len(short_clean)
    short_var = sum((r - short_mean) ** 2 for r in short_clean) / max(len(short_clean) + 1, 1)
    short_vol = math.sqrt(max(short_var, 0.0))
    full_vol = max(volatility, 1e-8)
    stress_raw = (short_vol / full_vol) - 1.0
    stress = max(0.0, min(1.0, stress_raw * 0.5 + 0.5))
    momentum = max(-1.0, min(1.0, recent_mean / max(full_vol, 1e-8)))
    liquidity = 1.0 - stress
    return {
        "volatility":     volatility,
        "trend_strength": trend_strength,
        "mean_reversion": mean_reversion,
        "stress":         stress,
        "momentum":       momentum,
        "liquidity":      liquidity,
    }


# ---------------------------------------------------------------------------
# Internal helpers (unchanged from v1.1.0)
# ---------------------------------------------------------------------------

def x__extract_regime_features__mutmut_108(returns_history: list) -> dict:
    clean = [r if math.isfinite(r) else 0.0 for r in returns_history]
    n = len(clean)
    mean_r = sum(clean) / n
    variance = sum((r - mean_r) ** 2 for r in clean) / max(n - 1, 1)
    volatility = math.sqrt(max(variance, 0.0))
    window = min(5, n)
    recent = clean[-window:]
    recent_mean = sum(recent) / window
    trend_strength = recent_mean / max(volatility, 1e-8)
    if n >= 2:
        pairs = [(clean[i], clean[i + 1]) for i in range(n - 1)]
        num = sum((a - mean_r) * (b - mean_r) for a, b in pairs)
        denom = sum((r - mean_r) ** 2 for r in clean)
        lag1_autocorr = num / max(denom, 1e-15)
        mean_reversion = max(-1.0, min(1.0, -lag1_autocorr))
    else:
        mean_reversion = 0.0
    short_window = min(10, n)
    short_clean = clean[-short_window:]
    short_mean = sum(short_clean) / len(short_clean)
    short_var = sum((r - short_mean) ** 2 for r in short_clean) / max(len(short_clean) - 2, 1)
    short_vol = math.sqrt(max(short_var, 0.0))
    full_vol = max(volatility, 1e-8)
    stress_raw = (short_vol / full_vol) - 1.0
    stress = max(0.0, min(1.0, stress_raw * 0.5 + 0.5))
    momentum = max(-1.0, min(1.0, recent_mean / max(full_vol, 1e-8)))
    liquidity = 1.0 - stress
    return {
        "volatility":     volatility,
        "trend_strength": trend_strength,
        "mean_reversion": mean_reversion,
        "stress":         stress,
        "momentum":       momentum,
        "liquidity":      liquidity,
    }


# ---------------------------------------------------------------------------
# Internal helpers (unchanged from v1.1.0)
# ---------------------------------------------------------------------------

def x__extract_regime_features__mutmut_109(returns_history: list) -> dict:
    clean = [r if math.isfinite(r) else 0.0 for r in returns_history]
    n = len(clean)
    mean_r = sum(clean) / n
    variance = sum((r - mean_r) ** 2 for r in clean) / max(n - 1, 1)
    volatility = math.sqrt(max(variance, 0.0))
    window = min(5, n)
    recent = clean[-window:]
    recent_mean = sum(recent) / window
    trend_strength = recent_mean / max(volatility, 1e-8)
    if n >= 2:
        pairs = [(clean[i], clean[i + 1]) for i in range(n - 1)]
        num = sum((a - mean_r) * (b - mean_r) for a, b in pairs)
        denom = sum((r - mean_r) ** 2 for r in clean)
        lag1_autocorr = num / max(denom, 1e-15)
        mean_reversion = max(-1.0, min(1.0, -lag1_autocorr))
    else:
        mean_reversion = 0.0
    short_window = min(10, n)
    short_clean = clean[-short_window:]
    short_mean = sum(short_clean) / len(short_clean)
    short_var = sum((r - short_mean) ** 2 for r in short_clean) / max(len(short_clean) - 1, 2)
    short_vol = math.sqrt(max(short_var, 0.0))
    full_vol = max(volatility, 1e-8)
    stress_raw = (short_vol / full_vol) - 1.0
    stress = max(0.0, min(1.0, stress_raw * 0.5 + 0.5))
    momentum = max(-1.0, min(1.0, recent_mean / max(full_vol, 1e-8)))
    liquidity = 1.0 - stress
    return {
        "volatility":     volatility,
        "trend_strength": trend_strength,
        "mean_reversion": mean_reversion,
        "stress":         stress,
        "momentum":       momentum,
        "liquidity":      liquidity,
    }


# ---------------------------------------------------------------------------
# Internal helpers (unchanged from v1.1.0)
# ---------------------------------------------------------------------------

def x__extract_regime_features__mutmut_110(returns_history: list) -> dict:
    clean = [r if math.isfinite(r) else 0.0 for r in returns_history]
    n = len(clean)
    mean_r = sum(clean) / n
    variance = sum((r - mean_r) ** 2 for r in clean) / max(n - 1, 1)
    volatility = math.sqrt(max(variance, 0.0))
    window = min(5, n)
    recent = clean[-window:]
    recent_mean = sum(recent) / window
    trend_strength = recent_mean / max(volatility, 1e-8)
    if n >= 2:
        pairs = [(clean[i], clean[i + 1]) for i in range(n - 1)]
        num = sum((a - mean_r) * (b - mean_r) for a, b in pairs)
        denom = sum((r - mean_r) ** 2 for r in clean)
        lag1_autocorr = num / max(denom, 1e-15)
        mean_reversion = max(-1.0, min(1.0, -lag1_autocorr))
    else:
        mean_reversion = 0.0
    short_window = min(10, n)
    short_clean = clean[-short_window:]
    short_mean = sum(short_clean) / len(short_clean)
    short_var = sum((r - short_mean) ** 2 for r in short_clean) / max(len(short_clean) - 1, 1)
    short_vol = None
    full_vol = max(volatility, 1e-8)
    stress_raw = (short_vol / full_vol) - 1.0
    stress = max(0.0, min(1.0, stress_raw * 0.5 + 0.5))
    momentum = max(-1.0, min(1.0, recent_mean / max(full_vol, 1e-8)))
    liquidity = 1.0 - stress
    return {
        "volatility":     volatility,
        "trend_strength": trend_strength,
        "mean_reversion": mean_reversion,
        "stress":         stress,
        "momentum":       momentum,
        "liquidity":      liquidity,
    }


# ---------------------------------------------------------------------------
# Internal helpers (unchanged from v1.1.0)
# ---------------------------------------------------------------------------

def x__extract_regime_features__mutmut_111(returns_history: list) -> dict:
    clean = [r if math.isfinite(r) else 0.0 for r in returns_history]
    n = len(clean)
    mean_r = sum(clean) / n
    variance = sum((r - mean_r) ** 2 for r in clean) / max(n - 1, 1)
    volatility = math.sqrt(max(variance, 0.0))
    window = min(5, n)
    recent = clean[-window:]
    recent_mean = sum(recent) / window
    trend_strength = recent_mean / max(volatility, 1e-8)
    if n >= 2:
        pairs = [(clean[i], clean[i + 1]) for i in range(n - 1)]
        num = sum((a - mean_r) * (b - mean_r) for a, b in pairs)
        denom = sum((r - mean_r) ** 2 for r in clean)
        lag1_autocorr = num / max(denom, 1e-15)
        mean_reversion = max(-1.0, min(1.0, -lag1_autocorr))
    else:
        mean_reversion = 0.0
    short_window = min(10, n)
    short_clean = clean[-short_window:]
    short_mean = sum(short_clean) / len(short_clean)
    short_var = sum((r - short_mean) ** 2 for r in short_clean) / max(len(short_clean) - 1, 1)
    short_vol = math.sqrt(None)
    full_vol = max(volatility, 1e-8)
    stress_raw = (short_vol / full_vol) - 1.0
    stress = max(0.0, min(1.0, stress_raw * 0.5 + 0.5))
    momentum = max(-1.0, min(1.0, recent_mean / max(full_vol, 1e-8)))
    liquidity = 1.0 - stress
    return {
        "volatility":     volatility,
        "trend_strength": trend_strength,
        "mean_reversion": mean_reversion,
        "stress":         stress,
        "momentum":       momentum,
        "liquidity":      liquidity,
    }


# ---------------------------------------------------------------------------
# Internal helpers (unchanged from v1.1.0)
# ---------------------------------------------------------------------------

def x__extract_regime_features__mutmut_112(returns_history: list) -> dict:
    clean = [r if math.isfinite(r) else 0.0 for r in returns_history]
    n = len(clean)
    mean_r = sum(clean) / n
    variance = sum((r - mean_r) ** 2 for r in clean) / max(n - 1, 1)
    volatility = math.sqrt(max(variance, 0.0))
    window = min(5, n)
    recent = clean[-window:]
    recent_mean = sum(recent) / window
    trend_strength = recent_mean / max(volatility, 1e-8)
    if n >= 2:
        pairs = [(clean[i], clean[i + 1]) for i in range(n - 1)]
        num = sum((a - mean_r) * (b - mean_r) for a, b in pairs)
        denom = sum((r - mean_r) ** 2 for r in clean)
        lag1_autocorr = num / max(denom, 1e-15)
        mean_reversion = max(-1.0, min(1.0, -lag1_autocorr))
    else:
        mean_reversion = 0.0
    short_window = min(10, n)
    short_clean = clean[-short_window:]
    short_mean = sum(short_clean) / len(short_clean)
    short_var = sum((r - short_mean) ** 2 for r in short_clean) / max(len(short_clean) - 1, 1)
    short_vol = math.sqrt(max(None, 0.0))
    full_vol = max(volatility, 1e-8)
    stress_raw = (short_vol / full_vol) - 1.0
    stress = max(0.0, min(1.0, stress_raw * 0.5 + 0.5))
    momentum = max(-1.0, min(1.0, recent_mean / max(full_vol, 1e-8)))
    liquidity = 1.0 - stress
    return {
        "volatility":     volatility,
        "trend_strength": trend_strength,
        "mean_reversion": mean_reversion,
        "stress":         stress,
        "momentum":       momentum,
        "liquidity":      liquidity,
    }


# ---------------------------------------------------------------------------
# Internal helpers (unchanged from v1.1.0)
# ---------------------------------------------------------------------------

def x__extract_regime_features__mutmut_113(returns_history: list) -> dict:
    clean = [r if math.isfinite(r) else 0.0 for r in returns_history]
    n = len(clean)
    mean_r = sum(clean) / n
    variance = sum((r - mean_r) ** 2 for r in clean) / max(n - 1, 1)
    volatility = math.sqrt(max(variance, 0.0))
    window = min(5, n)
    recent = clean[-window:]
    recent_mean = sum(recent) / window
    trend_strength = recent_mean / max(volatility, 1e-8)
    if n >= 2:
        pairs = [(clean[i], clean[i + 1]) for i in range(n - 1)]
        num = sum((a - mean_r) * (b - mean_r) for a, b in pairs)
        denom = sum((r - mean_r) ** 2 for r in clean)
        lag1_autocorr = num / max(denom, 1e-15)
        mean_reversion = max(-1.0, min(1.0, -lag1_autocorr))
    else:
        mean_reversion = 0.0
    short_window = min(10, n)
    short_clean = clean[-short_window:]
    short_mean = sum(short_clean) / len(short_clean)
    short_var = sum((r - short_mean) ** 2 for r in short_clean) / max(len(short_clean) - 1, 1)
    short_vol = math.sqrt(max(short_var, None))
    full_vol = max(volatility, 1e-8)
    stress_raw = (short_vol / full_vol) - 1.0
    stress = max(0.0, min(1.0, stress_raw * 0.5 + 0.5))
    momentum = max(-1.0, min(1.0, recent_mean / max(full_vol, 1e-8)))
    liquidity = 1.0 - stress
    return {
        "volatility":     volatility,
        "trend_strength": trend_strength,
        "mean_reversion": mean_reversion,
        "stress":         stress,
        "momentum":       momentum,
        "liquidity":      liquidity,
    }


# ---------------------------------------------------------------------------
# Internal helpers (unchanged from v1.1.0)
# ---------------------------------------------------------------------------

def x__extract_regime_features__mutmut_114(returns_history: list) -> dict:
    clean = [r if math.isfinite(r) else 0.0 for r in returns_history]
    n = len(clean)
    mean_r = sum(clean) / n
    variance = sum((r - mean_r) ** 2 for r in clean) / max(n - 1, 1)
    volatility = math.sqrt(max(variance, 0.0))
    window = min(5, n)
    recent = clean[-window:]
    recent_mean = sum(recent) / window
    trend_strength = recent_mean / max(volatility, 1e-8)
    if n >= 2:
        pairs = [(clean[i], clean[i + 1]) for i in range(n - 1)]
        num = sum((a - mean_r) * (b - mean_r) for a, b in pairs)
        denom = sum((r - mean_r) ** 2 for r in clean)
        lag1_autocorr = num / max(denom, 1e-15)
        mean_reversion = max(-1.0, min(1.0, -lag1_autocorr))
    else:
        mean_reversion = 0.0
    short_window = min(10, n)
    short_clean = clean[-short_window:]
    short_mean = sum(short_clean) / len(short_clean)
    short_var = sum((r - short_mean) ** 2 for r in short_clean) / max(len(short_clean) - 1, 1)
    short_vol = math.sqrt(max(0.0))
    full_vol = max(volatility, 1e-8)
    stress_raw = (short_vol / full_vol) - 1.0
    stress = max(0.0, min(1.0, stress_raw * 0.5 + 0.5))
    momentum = max(-1.0, min(1.0, recent_mean / max(full_vol, 1e-8)))
    liquidity = 1.0 - stress
    return {
        "volatility":     volatility,
        "trend_strength": trend_strength,
        "mean_reversion": mean_reversion,
        "stress":         stress,
        "momentum":       momentum,
        "liquidity":      liquidity,
    }


# ---------------------------------------------------------------------------
# Internal helpers (unchanged from v1.1.0)
# ---------------------------------------------------------------------------

def x__extract_regime_features__mutmut_115(returns_history: list) -> dict:
    clean = [r if math.isfinite(r) else 0.0 for r in returns_history]
    n = len(clean)
    mean_r = sum(clean) / n
    variance = sum((r - mean_r) ** 2 for r in clean) / max(n - 1, 1)
    volatility = math.sqrt(max(variance, 0.0))
    window = min(5, n)
    recent = clean[-window:]
    recent_mean = sum(recent) / window
    trend_strength = recent_mean / max(volatility, 1e-8)
    if n >= 2:
        pairs = [(clean[i], clean[i + 1]) for i in range(n - 1)]
        num = sum((a - mean_r) * (b - mean_r) for a, b in pairs)
        denom = sum((r - mean_r) ** 2 for r in clean)
        lag1_autocorr = num / max(denom, 1e-15)
        mean_reversion = max(-1.0, min(1.0, -lag1_autocorr))
    else:
        mean_reversion = 0.0
    short_window = min(10, n)
    short_clean = clean[-short_window:]
    short_mean = sum(short_clean) / len(short_clean)
    short_var = sum((r - short_mean) ** 2 for r in short_clean) / max(len(short_clean) - 1, 1)
    short_vol = math.sqrt(max(short_var, ))
    full_vol = max(volatility, 1e-8)
    stress_raw = (short_vol / full_vol) - 1.0
    stress = max(0.0, min(1.0, stress_raw * 0.5 + 0.5))
    momentum = max(-1.0, min(1.0, recent_mean / max(full_vol, 1e-8)))
    liquidity = 1.0 - stress
    return {
        "volatility":     volatility,
        "trend_strength": trend_strength,
        "mean_reversion": mean_reversion,
        "stress":         stress,
        "momentum":       momentum,
        "liquidity":      liquidity,
    }


# ---------------------------------------------------------------------------
# Internal helpers (unchanged from v1.1.0)
# ---------------------------------------------------------------------------

def x__extract_regime_features__mutmut_116(returns_history: list) -> dict:
    clean = [r if math.isfinite(r) else 0.0 for r in returns_history]
    n = len(clean)
    mean_r = sum(clean) / n
    variance = sum((r - mean_r) ** 2 for r in clean) / max(n - 1, 1)
    volatility = math.sqrt(max(variance, 0.0))
    window = min(5, n)
    recent = clean[-window:]
    recent_mean = sum(recent) / window
    trend_strength = recent_mean / max(volatility, 1e-8)
    if n >= 2:
        pairs = [(clean[i], clean[i + 1]) for i in range(n - 1)]
        num = sum((a - mean_r) * (b - mean_r) for a, b in pairs)
        denom = sum((r - mean_r) ** 2 for r in clean)
        lag1_autocorr = num / max(denom, 1e-15)
        mean_reversion = max(-1.0, min(1.0, -lag1_autocorr))
    else:
        mean_reversion = 0.0
    short_window = min(10, n)
    short_clean = clean[-short_window:]
    short_mean = sum(short_clean) / len(short_clean)
    short_var = sum((r - short_mean) ** 2 for r in short_clean) / max(len(short_clean) - 1, 1)
    short_vol = math.sqrt(max(short_var, 1.0))
    full_vol = max(volatility, 1e-8)
    stress_raw = (short_vol / full_vol) - 1.0
    stress = max(0.0, min(1.0, stress_raw * 0.5 + 0.5))
    momentum = max(-1.0, min(1.0, recent_mean / max(full_vol, 1e-8)))
    liquidity = 1.0 - stress
    return {
        "volatility":     volatility,
        "trend_strength": trend_strength,
        "mean_reversion": mean_reversion,
        "stress":         stress,
        "momentum":       momentum,
        "liquidity":      liquidity,
    }


# ---------------------------------------------------------------------------
# Internal helpers (unchanged from v1.1.0)
# ---------------------------------------------------------------------------

def x__extract_regime_features__mutmut_117(returns_history: list) -> dict:
    clean = [r if math.isfinite(r) else 0.0 for r in returns_history]
    n = len(clean)
    mean_r = sum(clean) / n
    variance = sum((r - mean_r) ** 2 for r in clean) / max(n - 1, 1)
    volatility = math.sqrt(max(variance, 0.0))
    window = min(5, n)
    recent = clean[-window:]
    recent_mean = sum(recent) / window
    trend_strength = recent_mean / max(volatility, 1e-8)
    if n >= 2:
        pairs = [(clean[i], clean[i + 1]) for i in range(n - 1)]
        num = sum((a - mean_r) * (b - mean_r) for a, b in pairs)
        denom = sum((r - mean_r) ** 2 for r in clean)
        lag1_autocorr = num / max(denom, 1e-15)
        mean_reversion = max(-1.0, min(1.0, -lag1_autocorr))
    else:
        mean_reversion = 0.0
    short_window = min(10, n)
    short_clean = clean[-short_window:]
    short_mean = sum(short_clean) / len(short_clean)
    short_var = sum((r - short_mean) ** 2 for r in short_clean) / max(len(short_clean) - 1, 1)
    short_vol = math.sqrt(max(short_var, 0.0))
    full_vol = None
    stress_raw = (short_vol / full_vol) - 1.0
    stress = max(0.0, min(1.0, stress_raw * 0.5 + 0.5))
    momentum = max(-1.0, min(1.0, recent_mean / max(full_vol, 1e-8)))
    liquidity = 1.0 - stress
    return {
        "volatility":     volatility,
        "trend_strength": trend_strength,
        "mean_reversion": mean_reversion,
        "stress":         stress,
        "momentum":       momentum,
        "liquidity":      liquidity,
    }


# ---------------------------------------------------------------------------
# Internal helpers (unchanged from v1.1.0)
# ---------------------------------------------------------------------------

def x__extract_regime_features__mutmut_118(returns_history: list) -> dict:
    clean = [r if math.isfinite(r) else 0.0 for r in returns_history]
    n = len(clean)
    mean_r = sum(clean) / n
    variance = sum((r - mean_r) ** 2 for r in clean) / max(n - 1, 1)
    volatility = math.sqrt(max(variance, 0.0))
    window = min(5, n)
    recent = clean[-window:]
    recent_mean = sum(recent) / window
    trend_strength = recent_mean / max(volatility, 1e-8)
    if n >= 2:
        pairs = [(clean[i], clean[i + 1]) for i in range(n - 1)]
        num = sum((a - mean_r) * (b - mean_r) for a, b in pairs)
        denom = sum((r - mean_r) ** 2 for r in clean)
        lag1_autocorr = num / max(denom, 1e-15)
        mean_reversion = max(-1.0, min(1.0, -lag1_autocorr))
    else:
        mean_reversion = 0.0
    short_window = min(10, n)
    short_clean = clean[-short_window:]
    short_mean = sum(short_clean) / len(short_clean)
    short_var = sum((r - short_mean) ** 2 for r in short_clean) / max(len(short_clean) - 1, 1)
    short_vol = math.sqrt(max(short_var, 0.0))
    full_vol = max(None, 1e-8)
    stress_raw = (short_vol / full_vol) - 1.0
    stress = max(0.0, min(1.0, stress_raw * 0.5 + 0.5))
    momentum = max(-1.0, min(1.0, recent_mean / max(full_vol, 1e-8)))
    liquidity = 1.0 - stress
    return {
        "volatility":     volatility,
        "trend_strength": trend_strength,
        "mean_reversion": mean_reversion,
        "stress":         stress,
        "momentum":       momentum,
        "liquidity":      liquidity,
    }


# ---------------------------------------------------------------------------
# Internal helpers (unchanged from v1.1.0)
# ---------------------------------------------------------------------------

def x__extract_regime_features__mutmut_119(returns_history: list) -> dict:
    clean = [r if math.isfinite(r) else 0.0 for r in returns_history]
    n = len(clean)
    mean_r = sum(clean) / n
    variance = sum((r - mean_r) ** 2 for r in clean) / max(n - 1, 1)
    volatility = math.sqrt(max(variance, 0.0))
    window = min(5, n)
    recent = clean[-window:]
    recent_mean = sum(recent) / window
    trend_strength = recent_mean / max(volatility, 1e-8)
    if n >= 2:
        pairs = [(clean[i], clean[i + 1]) for i in range(n - 1)]
        num = sum((a - mean_r) * (b - mean_r) for a, b in pairs)
        denom = sum((r - mean_r) ** 2 for r in clean)
        lag1_autocorr = num / max(denom, 1e-15)
        mean_reversion = max(-1.0, min(1.0, -lag1_autocorr))
    else:
        mean_reversion = 0.0
    short_window = min(10, n)
    short_clean = clean[-short_window:]
    short_mean = sum(short_clean) / len(short_clean)
    short_var = sum((r - short_mean) ** 2 for r in short_clean) / max(len(short_clean) - 1, 1)
    short_vol = math.sqrt(max(short_var, 0.0))
    full_vol = max(volatility, None)
    stress_raw = (short_vol / full_vol) - 1.0
    stress = max(0.0, min(1.0, stress_raw * 0.5 + 0.5))
    momentum = max(-1.0, min(1.0, recent_mean / max(full_vol, 1e-8)))
    liquidity = 1.0 - stress
    return {
        "volatility":     volatility,
        "trend_strength": trend_strength,
        "mean_reversion": mean_reversion,
        "stress":         stress,
        "momentum":       momentum,
        "liquidity":      liquidity,
    }


# ---------------------------------------------------------------------------
# Internal helpers (unchanged from v1.1.0)
# ---------------------------------------------------------------------------

def x__extract_regime_features__mutmut_120(returns_history: list) -> dict:
    clean = [r if math.isfinite(r) else 0.0 for r in returns_history]
    n = len(clean)
    mean_r = sum(clean) / n
    variance = sum((r - mean_r) ** 2 for r in clean) / max(n - 1, 1)
    volatility = math.sqrt(max(variance, 0.0))
    window = min(5, n)
    recent = clean[-window:]
    recent_mean = sum(recent) / window
    trend_strength = recent_mean / max(volatility, 1e-8)
    if n >= 2:
        pairs = [(clean[i], clean[i + 1]) for i in range(n - 1)]
        num = sum((a - mean_r) * (b - mean_r) for a, b in pairs)
        denom = sum((r - mean_r) ** 2 for r in clean)
        lag1_autocorr = num / max(denom, 1e-15)
        mean_reversion = max(-1.0, min(1.0, -lag1_autocorr))
    else:
        mean_reversion = 0.0
    short_window = min(10, n)
    short_clean = clean[-short_window:]
    short_mean = sum(short_clean) / len(short_clean)
    short_var = sum((r - short_mean) ** 2 for r in short_clean) / max(len(short_clean) - 1, 1)
    short_vol = math.sqrt(max(short_var, 0.0))
    full_vol = max(1e-8)
    stress_raw = (short_vol / full_vol) - 1.0
    stress = max(0.0, min(1.0, stress_raw * 0.5 + 0.5))
    momentum = max(-1.0, min(1.0, recent_mean / max(full_vol, 1e-8)))
    liquidity = 1.0 - stress
    return {
        "volatility":     volatility,
        "trend_strength": trend_strength,
        "mean_reversion": mean_reversion,
        "stress":         stress,
        "momentum":       momentum,
        "liquidity":      liquidity,
    }


# ---------------------------------------------------------------------------
# Internal helpers (unchanged from v1.1.0)
# ---------------------------------------------------------------------------

def x__extract_regime_features__mutmut_121(returns_history: list) -> dict:
    clean = [r if math.isfinite(r) else 0.0 for r in returns_history]
    n = len(clean)
    mean_r = sum(clean) / n
    variance = sum((r - mean_r) ** 2 for r in clean) / max(n - 1, 1)
    volatility = math.sqrt(max(variance, 0.0))
    window = min(5, n)
    recent = clean[-window:]
    recent_mean = sum(recent) / window
    trend_strength = recent_mean / max(volatility, 1e-8)
    if n >= 2:
        pairs = [(clean[i], clean[i + 1]) for i in range(n - 1)]
        num = sum((a - mean_r) * (b - mean_r) for a, b in pairs)
        denom = sum((r - mean_r) ** 2 for r in clean)
        lag1_autocorr = num / max(denom, 1e-15)
        mean_reversion = max(-1.0, min(1.0, -lag1_autocorr))
    else:
        mean_reversion = 0.0
    short_window = min(10, n)
    short_clean = clean[-short_window:]
    short_mean = sum(short_clean) / len(short_clean)
    short_var = sum((r - short_mean) ** 2 for r in short_clean) / max(len(short_clean) - 1, 1)
    short_vol = math.sqrt(max(short_var, 0.0))
    full_vol = max(volatility, )
    stress_raw = (short_vol / full_vol) - 1.0
    stress = max(0.0, min(1.0, stress_raw * 0.5 + 0.5))
    momentum = max(-1.0, min(1.0, recent_mean / max(full_vol, 1e-8)))
    liquidity = 1.0 - stress
    return {
        "volatility":     volatility,
        "trend_strength": trend_strength,
        "mean_reversion": mean_reversion,
        "stress":         stress,
        "momentum":       momentum,
        "liquidity":      liquidity,
    }


# ---------------------------------------------------------------------------
# Internal helpers (unchanged from v1.1.0)
# ---------------------------------------------------------------------------

def x__extract_regime_features__mutmut_122(returns_history: list) -> dict:
    clean = [r if math.isfinite(r) else 0.0 for r in returns_history]
    n = len(clean)
    mean_r = sum(clean) / n
    variance = sum((r - mean_r) ** 2 for r in clean) / max(n - 1, 1)
    volatility = math.sqrt(max(variance, 0.0))
    window = min(5, n)
    recent = clean[-window:]
    recent_mean = sum(recent) / window
    trend_strength = recent_mean / max(volatility, 1e-8)
    if n >= 2:
        pairs = [(clean[i], clean[i + 1]) for i in range(n - 1)]
        num = sum((a - mean_r) * (b - mean_r) for a, b in pairs)
        denom = sum((r - mean_r) ** 2 for r in clean)
        lag1_autocorr = num / max(denom, 1e-15)
        mean_reversion = max(-1.0, min(1.0, -lag1_autocorr))
    else:
        mean_reversion = 0.0
    short_window = min(10, n)
    short_clean = clean[-short_window:]
    short_mean = sum(short_clean) / len(short_clean)
    short_var = sum((r - short_mean) ** 2 for r in short_clean) / max(len(short_clean) - 1, 1)
    short_vol = math.sqrt(max(short_var, 0.0))
    full_vol = max(volatility, 1.00000001)
    stress_raw = (short_vol / full_vol) - 1.0
    stress = max(0.0, min(1.0, stress_raw * 0.5 + 0.5))
    momentum = max(-1.0, min(1.0, recent_mean / max(full_vol, 1e-8)))
    liquidity = 1.0 - stress
    return {
        "volatility":     volatility,
        "trend_strength": trend_strength,
        "mean_reversion": mean_reversion,
        "stress":         stress,
        "momentum":       momentum,
        "liquidity":      liquidity,
    }


# ---------------------------------------------------------------------------
# Internal helpers (unchanged from v1.1.0)
# ---------------------------------------------------------------------------

def x__extract_regime_features__mutmut_123(returns_history: list) -> dict:
    clean = [r if math.isfinite(r) else 0.0 for r in returns_history]
    n = len(clean)
    mean_r = sum(clean) / n
    variance = sum((r - mean_r) ** 2 for r in clean) / max(n - 1, 1)
    volatility = math.sqrt(max(variance, 0.0))
    window = min(5, n)
    recent = clean[-window:]
    recent_mean = sum(recent) / window
    trend_strength = recent_mean / max(volatility, 1e-8)
    if n >= 2:
        pairs = [(clean[i], clean[i + 1]) for i in range(n - 1)]
        num = sum((a - mean_r) * (b - mean_r) for a, b in pairs)
        denom = sum((r - mean_r) ** 2 for r in clean)
        lag1_autocorr = num / max(denom, 1e-15)
        mean_reversion = max(-1.0, min(1.0, -lag1_autocorr))
    else:
        mean_reversion = 0.0
    short_window = min(10, n)
    short_clean = clean[-short_window:]
    short_mean = sum(short_clean) / len(short_clean)
    short_var = sum((r - short_mean) ** 2 for r in short_clean) / max(len(short_clean) - 1, 1)
    short_vol = math.sqrt(max(short_var, 0.0))
    full_vol = max(volatility, 1e-8)
    stress_raw = None
    stress = max(0.0, min(1.0, stress_raw * 0.5 + 0.5))
    momentum = max(-1.0, min(1.0, recent_mean / max(full_vol, 1e-8)))
    liquidity = 1.0 - stress
    return {
        "volatility":     volatility,
        "trend_strength": trend_strength,
        "mean_reversion": mean_reversion,
        "stress":         stress,
        "momentum":       momentum,
        "liquidity":      liquidity,
    }


# ---------------------------------------------------------------------------
# Internal helpers (unchanged from v1.1.0)
# ---------------------------------------------------------------------------

def x__extract_regime_features__mutmut_124(returns_history: list) -> dict:
    clean = [r if math.isfinite(r) else 0.0 for r in returns_history]
    n = len(clean)
    mean_r = sum(clean) / n
    variance = sum((r - mean_r) ** 2 for r in clean) / max(n - 1, 1)
    volatility = math.sqrt(max(variance, 0.0))
    window = min(5, n)
    recent = clean[-window:]
    recent_mean = sum(recent) / window
    trend_strength = recent_mean / max(volatility, 1e-8)
    if n >= 2:
        pairs = [(clean[i], clean[i + 1]) for i in range(n - 1)]
        num = sum((a - mean_r) * (b - mean_r) for a, b in pairs)
        denom = sum((r - mean_r) ** 2 for r in clean)
        lag1_autocorr = num / max(denom, 1e-15)
        mean_reversion = max(-1.0, min(1.0, -lag1_autocorr))
    else:
        mean_reversion = 0.0
    short_window = min(10, n)
    short_clean = clean[-short_window:]
    short_mean = sum(short_clean) / len(short_clean)
    short_var = sum((r - short_mean) ** 2 for r in short_clean) / max(len(short_clean) - 1, 1)
    short_vol = math.sqrt(max(short_var, 0.0))
    full_vol = max(volatility, 1e-8)
    stress_raw = (short_vol / full_vol) + 1.0
    stress = max(0.0, min(1.0, stress_raw * 0.5 + 0.5))
    momentum = max(-1.0, min(1.0, recent_mean / max(full_vol, 1e-8)))
    liquidity = 1.0 - stress
    return {
        "volatility":     volatility,
        "trend_strength": trend_strength,
        "mean_reversion": mean_reversion,
        "stress":         stress,
        "momentum":       momentum,
        "liquidity":      liquidity,
    }


# ---------------------------------------------------------------------------
# Internal helpers (unchanged from v1.1.0)
# ---------------------------------------------------------------------------

def x__extract_regime_features__mutmut_125(returns_history: list) -> dict:
    clean = [r if math.isfinite(r) else 0.0 for r in returns_history]
    n = len(clean)
    mean_r = sum(clean) / n
    variance = sum((r - mean_r) ** 2 for r in clean) / max(n - 1, 1)
    volatility = math.sqrt(max(variance, 0.0))
    window = min(5, n)
    recent = clean[-window:]
    recent_mean = sum(recent) / window
    trend_strength = recent_mean / max(volatility, 1e-8)
    if n >= 2:
        pairs = [(clean[i], clean[i + 1]) for i in range(n - 1)]
        num = sum((a - mean_r) * (b - mean_r) for a, b in pairs)
        denom = sum((r - mean_r) ** 2 for r in clean)
        lag1_autocorr = num / max(denom, 1e-15)
        mean_reversion = max(-1.0, min(1.0, -lag1_autocorr))
    else:
        mean_reversion = 0.0
    short_window = min(10, n)
    short_clean = clean[-short_window:]
    short_mean = sum(short_clean) / len(short_clean)
    short_var = sum((r - short_mean) ** 2 for r in short_clean) / max(len(short_clean) - 1, 1)
    short_vol = math.sqrt(max(short_var, 0.0))
    full_vol = max(volatility, 1e-8)
    stress_raw = (short_vol * full_vol) - 1.0
    stress = max(0.0, min(1.0, stress_raw * 0.5 + 0.5))
    momentum = max(-1.0, min(1.0, recent_mean / max(full_vol, 1e-8)))
    liquidity = 1.0 - stress
    return {
        "volatility":     volatility,
        "trend_strength": trend_strength,
        "mean_reversion": mean_reversion,
        "stress":         stress,
        "momentum":       momentum,
        "liquidity":      liquidity,
    }


# ---------------------------------------------------------------------------
# Internal helpers (unchanged from v1.1.0)
# ---------------------------------------------------------------------------

def x__extract_regime_features__mutmut_126(returns_history: list) -> dict:
    clean = [r if math.isfinite(r) else 0.0 for r in returns_history]
    n = len(clean)
    mean_r = sum(clean) / n
    variance = sum((r - mean_r) ** 2 for r in clean) / max(n - 1, 1)
    volatility = math.sqrt(max(variance, 0.0))
    window = min(5, n)
    recent = clean[-window:]
    recent_mean = sum(recent) / window
    trend_strength = recent_mean / max(volatility, 1e-8)
    if n >= 2:
        pairs = [(clean[i], clean[i + 1]) for i in range(n - 1)]
        num = sum((a - mean_r) * (b - mean_r) for a, b in pairs)
        denom = sum((r - mean_r) ** 2 for r in clean)
        lag1_autocorr = num / max(denom, 1e-15)
        mean_reversion = max(-1.0, min(1.0, -lag1_autocorr))
    else:
        mean_reversion = 0.0
    short_window = min(10, n)
    short_clean = clean[-short_window:]
    short_mean = sum(short_clean) / len(short_clean)
    short_var = sum((r - short_mean) ** 2 for r in short_clean) / max(len(short_clean) - 1, 1)
    short_vol = math.sqrt(max(short_var, 0.0))
    full_vol = max(volatility, 1e-8)
    stress_raw = (short_vol / full_vol) - 2.0
    stress = max(0.0, min(1.0, stress_raw * 0.5 + 0.5))
    momentum = max(-1.0, min(1.0, recent_mean / max(full_vol, 1e-8)))
    liquidity = 1.0 - stress
    return {
        "volatility":     volatility,
        "trend_strength": trend_strength,
        "mean_reversion": mean_reversion,
        "stress":         stress,
        "momentum":       momentum,
        "liquidity":      liquidity,
    }


# ---------------------------------------------------------------------------
# Internal helpers (unchanged from v1.1.0)
# ---------------------------------------------------------------------------

def x__extract_regime_features__mutmut_127(returns_history: list) -> dict:
    clean = [r if math.isfinite(r) else 0.0 for r in returns_history]
    n = len(clean)
    mean_r = sum(clean) / n
    variance = sum((r - mean_r) ** 2 for r in clean) / max(n - 1, 1)
    volatility = math.sqrt(max(variance, 0.0))
    window = min(5, n)
    recent = clean[-window:]
    recent_mean = sum(recent) / window
    trend_strength = recent_mean / max(volatility, 1e-8)
    if n >= 2:
        pairs = [(clean[i], clean[i + 1]) for i in range(n - 1)]
        num = sum((a - mean_r) * (b - mean_r) for a, b in pairs)
        denom = sum((r - mean_r) ** 2 for r in clean)
        lag1_autocorr = num / max(denom, 1e-15)
        mean_reversion = max(-1.0, min(1.0, -lag1_autocorr))
    else:
        mean_reversion = 0.0
    short_window = min(10, n)
    short_clean = clean[-short_window:]
    short_mean = sum(short_clean) / len(short_clean)
    short_var = sum((r - short_mean) ** 2 for r in short_clean) / max(len(short_clean) - 1, 1)
    short_vol = math.sqrt(max(short_var, 0.0))
    full_vol = max(volatility, 1e-8)
    stress_raw = (short_vol / full_vol) - 1.0
    stress = None
    momentum = max(-1.0, min(1.0, recent_mean / max(full_vol, 1e-8)))
    liquidity = 1.0 - stress
    return {
        "volatility":     volatility,
        "trend_strength": trend_strength,
        "mean_reversion": mean_reversion,
        "stress":         stress,
        "momentum":       momentum,
        "liquidity":      liquidity,
    }


# ---------------------------------------------------------------------------
# Internal helpers (unchanged from v1.1.0)
# ---------------------------------------------------------------------------

def x__extract_regime_features__mutmut_128(returns_history: list) -> dict:
    clean = [r if math.isfinite(r) else 0.0 for r in returns_history]
    n = len(clean)
    mean_r = sum(clean) / n
    variance = sum((r - mean_r) ** 2 for r in clean) / max(n - 1, 1)
    volatility = math.sqrt(max(variance, 0.0))
    window = min(5, n)
    recent = clean[-window:]
    recent_mean = sum(recent) / window
    trend_strength = recent_mean / max(volatility, 1e-8)
    if n >= 2:
        pairs = [(clean[i], clean[i + 1]) for i in range(n - 1)]
        num = sum((a - mean_r) * (b - mean_r) for a, b in pairs)
        denom = sum((r - mean_r) ** 2 for r in clean)
        lag1_autocorr = num / max(denom, 1e-15)
        mean_reversion = max(-1.0, min(1.0, -lag1_autocorr))
    else:
        mean_reversion = 0.0
    short_window = min(10, n)
    short_clean = clean[-short_window:]
    short_mean = sum(short_clean) / len(short_clean)
    short_var = sum((r - short_mean) ** 2 for r in short_clean) / max(len(short_clean) - 1, 1)
    short_vol = math.sqrt(max(short_var, 0.0))
    full_vol = max(volatility, 1e-8)
    stress_raw = (short_vol / full_vol) - 1.0
    stress = max(None, min(1.0, stress_raw * 0.5 + 0.5))
    momentum = max(-1.0, min(1.0, recent_mean / max(full_vol, 1e-8)))
    liquidity = 1.0 - stress
    return {
        "volatility":     volatility,
        "trend_strength": trend_strength,
        "mean_reversion": mean_reversion,
        "stress":         stress,
        "momentum":       momentum,
        "liquidity":      liquidity,
    }


# ---------------------------------------------------------------------------
# Internal helpers (unchanged from v1.1.0)
# ---------------------------------------------------------------------------

def x__extract_regime_features__mutmut_129(returns_history: list) -> dict:
    clean = [r if math.isfinite(r) else 0.0 for r in returns_history]
    n = len(clean)
    mean_r = sum(clean) / n
    variance = sum((r - mean_r) ** 2 for r in clean) / max(n - 1, 1)
    volatility = math.sqrt(max(variance, 0.0))
    window = min(5, n)
    recent = clean[-window:]
    recent_mean = sum(recent) / window
    trend_strength = recent_mean / max(volatility, 1e-8)
    if n >= 2:
        pairs = [(clean[i], clean[i + 1]) for i in range(n - 1)]
        num = sum((a - mean_r) * (b - mean_r) for a, b in pairs)
        denom = sum((r - mean_r) ** 2 for r in clean)
        lag1_autocorr = num / max(denom, 1e-15)
        mean_reversion = max(-1.0, min(1.0, -lag1_autocorr))
    else:
        mean_reversion = 0.0
    short_window = min(10, n)
    short_clean = clean[-short_window:]
    short_mean = sum(short_clean) / len(short_clean)
    short_var = sum((r - short_mean) ** 2 for r in short_clean) / max(len(short_clean) - 1, 1)
    short_vol = math.sqrt(max(short_var, 0.0))
    full_vol = max(volatility, 1e-8)
    stress_raw = (short_vol / full_vol) - 1.0
    stress = max(0.0, None)
    momentum = max(-1.0, min(1.0, recent_mean / max(full_vol, 1e-8)))
    liquidity = 1.0 - stress
    return {
        "volatility":     volatility,
        "trend_strength": trend_strength,
        "mean_reversion": mean_reversion,
        "stress":         stress,
        "momentum":       momentum,
        "liquidity":      liquidity,
    }


# ---------------------------------------------------------------------------
# Internal helpers (unchanged from v1.1.0)
# ---------------------------------------------------------------------------

def x__extract_regime_features__mutmut_130(returns_history: list) -> dict:
    clean = [r if math.isfinite(r) else 0.0 for r in returns_history]
    n = len(clean)
    mean_r = sum(clean) / n
    variance = sum((r - mean_r) ** 2 for r in clean) / max(n - 1, 1)
    volatility = math.sqrt(max(variance, 0.0))
    window = min(5, n)
    recent = clean[-window:]
    recent_mean = sum(recent) / window
    trend_strength = recent_mean / max(volatility, 1e-8)
    if n >= 2:
        pairs = [(clean[i], clean[i + 1]) for i in range(n - 1)]
        num = sum((a - mean_r) * (b - mean_r) for a, b in pairs)
        denom = sum((r - mean_r) ** 2 for r in clean)
        lag1_autocorr = num / max(denom, 1e-15)
        mean_reversion = max(-1.0, min(1.0, -lag1_autocorr))
    else:
        mean_reversion = 0.0
    short_window = min(10, n)
    short_clean = clean[-short_window:]
    short_mean = sum(short_clean) / len(short_clean)
    short_var = sum((r - short_mean) ** 2 for r in short_clean) / max(len(short_clean) - 1, 1)
    short_vol = math.sqrt(max(short_var, 0.0))
    full_vol = max(volatility, 1e-8)
    stress_raw = (short_vol / full_vol) - 1.0
    stress = max(min(1.0, stress_raw * 0.5 + 0.5))
    momentum = max(-1.0, min(1.0, recent_mean / max(full_vol, 1e-8)))
    liquidity = 1.0 - stress
    return {
        "volatility":     volatility,
        "trend_strength": trend_strength,
        "mean_reversion": mean_reversion,
        "stress":         stress,
        "momentum":       momentum,
        "liquidity":      liquidity,
    }


# ---------------------------------------------------------------------------
# Internal helpers (unchanged from v1.1.0)
# ---------------------------------------------------------------------------

def x__extract_regime_features__mutmut_131(returns_history: list) -> dict:
    clean = [r if math.isfinite(r) else 0.0 for r in returns_history]
    n = len(clean)
    mean_r = sum(clean) / n
    variance = sum((r - mean_r) ** 2 for r in clean) / max(n - 1, 1)
    volatility = math.sqrt(max(variance, 0.0))
    window = min(5, n)
    recent = clean[-window:]
    recent_mean = sum(recent) / window
    trend_strength = recent_mean / max(volatility, 1e-8)
    if n >= 2:
        pairs = [(clean[i], clean[i + 1]) for i in range(n - 1)]
        num = sum((a - mean_r) * (b - mean_r) for a, b in pairs)
        denom = sum((r - mean_r) ** 2 for r in clean)
        lag1_autocorr = num / max(denom, 1e-15)
        mean_reversion = max(-1.0, min(1.0, -lag1_autocorr))
    else:
        mean_reversion = 0.0
    short_window = min(10, n)
    short_clean = clean[-short_window:]
    short_mean = sum(short_clean) / len(short_clean)
    short_var = sum((r - short_mean) ** 2 for r in short_clean) / max(len(short_clean) - 1, 1)
    short_vol = math.sqrt(max(short_var, 0.0))
    full_vol = max(volatility, 1e-8)
    stress_raw = (short_vol / full_vol) - 1.0
    stress = max(0.0, )
    momentum = max(-1.0, min(1.0, recent_mean / max(full_vol, 1e-8)))
    liquidity = 1.0 - stress
    return {
        "volatility":     volatility,
        "trend_strength": trend_strength,
        "mean_reversion": mean_reversion,
        "stress":         stress,
        "momentum":       momentum,
        "liquidity":      liquidity,
    }


# ---------------------------------------------------------------------------
# Internal helpers (unchanged from v1.1.0)
# ---------------------------------------------------------------------------

def x__extract_regime_features__mutmut_132(returns_history: list) -> dict:
    clean = [r if math.isfinite(r) else 0.0 for r in returns_history]
    n = len(clean)
    mean_r = sum(clean) / n
    variance = sum((r - mean_r) ** 2 for r in clean) / max(n - 1, 1)
    volatility = math.sqrt(max(variance, 0.0))
    window = min(5, n)
    recent = clean[-window:]
    recent_mean = sum(recent) / window
    trend_strength = recent_mean / max(volatility, 1e-8)
    if n >= 2:
        pairs = [(clean[i], clean[i + 1]) for i in range(n - 1)]
        num = sum((a - mean_r) * (b - mean_r) for a, b in pairs)
        denom = sum((r - mean_r) ** 2 for r in clean)
        lag1_autocorr = num / max(denom, 1e-15)
        mean_reversion = max(-1.0, min(1.0, -lag1_autocorr))
    else:
        mean_reversion = 0.0
    short_window = min(10, n)
    short_clean = clean[-short_window:]
    short_mean = sum(short_clean) / len(short_clean)
    short_var = sum((r - short_mean) ** 2 for r in short_clean) / max(len(short_clean) - 1, 1)
    short_vol = math.sqrt(max(short_var, 0.0))
    full_vol = max(volatility, 1e-8)
    stress_raw = (short_vol / full_vol) - 1.0
    stress = max(1.0, min(1.0, stress_raw * 0.5 + 0.5))
    momentum = max(-1.0, min(1.0, recent_mean / max(full_vol, 1e-8)))
    liquidity = 1.0 - stress
    return {
        "volatility":     volatility,
        "trend_strength": trend_strength,
        "mean_reversion": mean_reversion,
        "stress":         stress,
        "momentum":       momentum,
        "liquidity":      liquidity,
    }


# ---------------------------------------------------------------------------
# Internal helpers (unchanged from v1.1.0)
# ---------------------------------------------------------------------------

def x__extract_regime_features__mutmut_133(returns_history: list) -> dict:
    clean = [r if math.isfinite(r) else 0.0 for r in returns_history]
    n = len(clean)
    mean_r = sum(clean) / n
    variance = sum((r - mean_r) ** 2 for r in clean) / max(n - 1, 1)
    volatility = math.sqrt(max(variance, 0.0))
    window = min(5, n)
    recent = clean[-window:]
    recent_mean = sum(recent) / window
    trend_strength = recent_mean / max(volatility, 1e-8)
    if n >= 2:
        pairs = [(clean[i], clean[i + 1]) for i in range(n - 1)]
        num = sum((a - mean_r) * (b - mean_r) for a, b in pairs)
        denom = sum((r - mean_r) ** 2 for r in clean)
        lag1_autocorr = num / max(denom, 1e-15)
        mean_reversion = max(-1.0, min(1.0, -lag1_autocorr))
    else:
        mean_reversion = 0.0
    short_window = min(10, n)
    short_clean = clean[-short_window:]
    short_mean = sum(short_clean) / len(short_clean)
    short_var = sum((r - short_mean) ** 2 for r in short_clean) / max(len(short_clean) - 1, 1)
    short_vol = math.sqrt(max(short_var, 0.0))
    full_vol = max(volatility, 1e-8)
    stress_raw = (short_vol / full_vol) - 1.0
    stress = max(0.0, min(None, stress_raw * 0.5 + 0.5))
    momentum = max(-1.0, min(1.0, recent_mean / max(full_vol, 1e-8)))
    liquidity = 1.0 - stress
    return {
        "volatility":     volatility,
        "trend_strength": trend_strength,
        "mean_reversion": mean_reversion,
        "stress":         stress,
        "momentum":       momentum,
        "liquidity":      liquidity,
    }


# ---------------------------------------------------------------------------
# Internal helpers (unchanged from v1.1.0)
# ---------------------------------------------------------------------------

def x__extract_regime_features__mutmut_134(returns_history: list) -> dict:
    clean = [r if math.isfinite(r) else 0.0 for r in returns_history]
    n = len(clean)
    mean_r = sum(clean) / n
    variance = sum((r - mean_r) ** 2 for r in clean) / max(n - 1, 1)
    volatility = math.sqrt(max(variance, 0.0))
    window = min(5, n)
    recent = clean[-window:]
    recent_mean = sum(recent) / window
    trend_strength = recent_mean / max(volatility, 1e-8)
    if n >= 2:
        pairs = [(clean[i], clean[i + 1]) for i in range(n - 1)]
        num = sum((a - mean_r) * (b - mean_r) for a, b in pairs)
        denom = sum((r - mean_r) ** 2 for r in clean)
        lag1_autocorr = num / max(denom, 1e-15)
        mean_reversion = max(-1.0, min(1.0, -lag1_autocorr))
    else:
        mean_reversion = 0.0
    short_window = min(10, n)
    short_clean = clean[-short_window:]
    short_mean = sum(short_clean) / len(short_clean)
    short_var = sum((r - short_mean) ** 2 for r in short_clean) / max(len(short_clean) - 1, 1)
    short_vol = math.sqrt(max(short_var, 0.0))
    full_vol = max(volatility, 1e-8)
    stress_raw = (short_vol / full_vol) - 1.0
    stress = max(0.0, min(1.0, None))
    momentum = max(-1.0, min(1.0, recent_mean / max(full_vol, 1e-8)))
    liquidity = 1.0 - stress
    return {
        "volatility":     volatility,
        "trend_strength": trend_strength,
        "mean_reversion": mean_reversion,
        "stress":         stress,
        "momentum":       momentum,
        "liquidity":      liquidity,
    }


# ---------------------------------------------------------------------------
# Internal helpers (unchanged from v1.1.0)
# ---------------------------------------------------------------------------

def x__extract_regime_features__mutmut_135(returns_history: list) -> dict:
    clean = [r if math.isfinite(r) else 0.0 for r in returns_history]
    n = len(clean)
    mean_r = sum(clean) / n
    variance = sum((r - mean_r) ** 2 for r in clean) / max(n - 1, 1)
    volatility = math.sqrt(max(variance, 0.0))
    window = min(5, n)
    recent = clean[-window:]
    recent_mean = sum(recent) / window
    trend_strength = recent_mean / max(volatility, 1e-8)
    if n >= 2:
        pairs = [(clean[i], clean[i + 1]) for i in range(n - 1)]
        num = sum((a - mean_r) * (b - mean_r) for a, b in pairs)
        denom = sum((r - mean_r) ** 2 for r in clean)
        lag1_autocorr = num / max(denom, 1e-15)
        mean_reversion = max(-1.0, min(1.0, -lag1_autocorr))
    else:
        mean_reversion = 0.0
    short_window = min(10, n)
    short_clean = clean[-short_window:]
    short_mean = sum(short_clean) / len(short_clean)
    short_var = sum((r - short_mean) ** 2 for r in short_clean) / max(len(short_clean) - 1, 1)
    short_vol = math.sqrt(max(short_var, 0.0))
    full_vol = max(volatility, 1e-8)
    stress_raw = (short_vol / full_vol) - 1.0
    stress = max(0.0, min(stress_raw * 0.5 + 0.5))
    momentum = max(-1.0, min(1.0, recent_mean / max(full_vol, 1e-8)))
    liquidity = 1.0 - stress
    return {
        "volatility":     volatility,
        "trend_strength": trend_strength,
        "mean_reversion": mean_reversion,
        "stress":         stress,
        "momentum":       momentum,
        "liquidity":      liquidity,
    }


# ---------------------------------------------------------------------------
# Internal helpers (unchanged from v1.1.0)
# ---------------------------------------------------------------------------

def x__extract_regime_features__mutmut_136(returns_history: list) -> dict:
    clean = [r if math.isfinite(r) else 0.0 for r in returns_history]
    n = len(clean)
    mean_r = sum(clean) / n
    variance = sum((r - mean_r) ** 2 for r in clean) / max(n - 1, 1)
    volatility = math.sqrt(max(variance, 0.0))
    window = min(5, n)
    recent = clean[-window:]
    recent_mean = sum(recent) / window
    trend_strength = recent_mean / max(volatility, 1e-8)
    if n >= 2:
        pairs = [(clean[i], clean[i + 1]) for i in range(n - 1)]
        num = sum((a - mean_r) * (b - mean_r) for a, b in pairs)
        denom = sum((r - mean_r) ** 2 for r in clean)
        lag1_autocorr = num / max(denom, 1e-15)
        mean_reversion = max(-1.0, min(1.0, -lag1_autocorr))
    else:
        mean_reversion = 0.0
    short_window = min(10, n)
    short_clean = clean[-short_window:]
    short_mean = sum(short_clean) / len(short_clean)
    short_var = sum((r - short_mean) ** 2 for r in short_clean) / max(len(short_clean) - 1, 1)
    short_vol = math.sqrt(max(short_var, 0.0))
    full_vol = max(volatility, 1e-8)
    stress_raw = (short_vol / full_vol) - 1.0
    stress = max(0.0, min(1.0, ))
    momentum = max(-1.0, min(1.0, recent_mean / max(full_vol, 1e-8)))
    liquidity = 1.0 - stress
    return {
        "volatility":     volatility,
        "trend_strength": trend_strength,
        "mean_reversion": mean_reversion,
        "stress":         stress,
        "momentum":       momentum,
        "liquidity":      liquidity,
    }


# ---------------------------------------------------------------------------
# Internal helpers (unchanged from v1.1.0)
# ---------------------------------------------------------------------------

def x__extract_regime_features__mutmut_137(returns_history: list) -> dict:
    clean = [r if math.isfinite(r) else 0.0 for r in returns_history]
    n = len(clean)
    mean_r = sum(clean) / n
    variance = sum((r - mean_r) ** 2 for r in clean) / max(n - 1, 1)
    volatility = math.sqrt(max(variance, 0.0))
    window = min(5, n)
    recent = clean[-window:]
    recent_mean = sum(recent) / window
    trend_strength = recent_mean / max(volatility, 1e-8)
    if n >= 2:
        pairs = [(clean[i], clean[i + 1]) for i in range(n - 1)]
        num = sum((a - mean_r) * (b - mean_r) for a, b in pairs)
        denom = sum((r - mean_r) ** 2 for r in clean)
        lag1_autocorr = num / max(denom, 1e-15)
        mean_reversion = max(-1.0, min(1.0, -lag1_autocorr))
    else:
        mean_reversion = 0.0
    short_window = min(10, n)
    short_clean = clean[-short_window:]
    short_mean = sum(short_clean) / len(short_clean)
    short_var = sum((r - short_mean) ** 2 for r in short_clean) / max(len(short_clean) - 1, 1)
    short_vol = math.sqrt(max(short_var, 0.0))
    full_vol = max(volatility, 1e-8)
    stress_raw = (short_vol / full_vol) - 1.0
    stress = max(0.0, min(2.0, stress_raw * 0.5 + 0.5))
    momentum = max(-1.0, min(1.0, recent_mean / max(full_vol, 1e-8)))
    liquidity = 1.0 - stress
    return {
        "volatility":     volatility,
        "trend_strength": trend_strength,
        "mean_reversion": mean_reversion,
        "stress":         stress,
        "momentum":       momentum,
        "liquidity":      liquidity,
    }


# ---------------------------------------------------------------------------
# Internal helpers (unchanged from v1.1.0)
# ---------------------------------------------------------------------------

def x__extract_regime_features__mutmut_138(returns_history: list) -> dict:
    clean = [r if math.isfinite(r) else 0.0 for r in returns_history]
    n = len(clean)
    mean_r = sum(clean) / n
    variance = sum((r - mean_r) ** 2 for r in clean) / max(n - 1, 1)
    volatility = math.sqrt(max(variance, 0.0))
    window = min(5, n)
    recent = clean[-window:]
    recent_mean = sum(recent) / window
    trend_strength = recent_mean / max(volatility, 1e-8)
    if n >= 2:
        pairs = [(clean[i], clean[i + 1]) for i in range(n - 1)]
        num = sum((a - mean_r) * (b - mean_r) for a, b in pairs)
        denom = sum((r - mean_r) ** 2 for r in clean)
        lag1_autocorr = num / max(denom, 1e-15)
        mean_reversion = max(-1.0, min(1.0, -lag1_autocorr))
    else:
        mean_reversion = 0.0
    short_window = min(10, n)
    short_clean = clean[-short_window:]
    short_mean = sum(short_clean) / len(short_clean)
    short_var = sum((r - short_mean) ** 2 for r in short_clean) / max(len(short_clean) - 1, 1)
    short_vol = math.sqrt(max(short_var, 0.0))
    full_vol = max(volatility, 1e-8)
    stress_raw = (short_vol / full_vol) - 1.0
    stress = max(0.0, min(1.0, stress_raw * 0.5 - 0.5))
    momentum = max(-1.0, min(1.0, recent_mean / max(full_vol, 1e-8)))
    liquidity = 1.0 - stress
    return {
        "volatility":     volatility,
        "trend_strength": trend_strength,
        "mean_reversion": mean_reversion,
        "stress":         stress,
        "momentum":       momentum,
        "liquidity":      liquidity,
    }


# ---------------------------------------------------------------------------
# Internal helpers (unchanged from v1.1.0)
# ---------------------------------------------------------------------------

def x__extract_regime_features__mutmut_139(returns_history: list) -> dict:
    clean = [r if math.isfinite(r) else 0.0 for r in returns_history]
    n = len(clean)
    mean_r = sum(clean) / n
    variance = sum((r - mean_r) ** 2 for r in clean) / max(n - 1, 1)
    volatility = math.sqrt(max(variance, 0.0))
    window = min(5, n)
    recent = clean[-window:]
    recent_mean = sum(recent) / window
    trend_strength = recent_mean / max(volatility, 1e-8)
    if n >= 2:
        pairs = [(clean[i], clean[i + 1]) for i in range(n - 1)]
        num = sum((a - mean_r) * (b - mean_r) for a, b in pairs)
        denom = sum((r - mean_r) ** 2 for r in clean)
        lag1_autocorr = num / max(denom, 1e-15)
        mean_reversion = max(-1.0, min(1.0, -lag1_autocorr))
    else:
        mean_reversion = 0.0
    short_window = min(10, n)
    short_clean = clean[-short_window:]
    short_mean = sum(short_clean) / len(short_clean)
    short_var = sum((r - short_mean) ** 2 for r in short_clean) / max(len(short_clean) - 1, 1)
    short_vol = math.sqrt(max(short_var, 0.0))
    full_vol = max(volatility, 1e-8)
    stress_raw = (short_vol / full_vol) - 1.0
    stress = max(0.0, min(1.0, stress_raw / 0.5 + 0.5))
    momentum = max(-1.0, min(1.0, recent_mean / max(full_vol, 1e-8)))
    liquidity = 1.0 - stress
    return {
        "volatility":     volatility,
        "trend_strength": trend_strength,
        "mean_reversion": mean_reversion,
        "stress":         stress,
        "momentum":       momentum,
        "liquidity":      liquidity,
    }


# ---------------------------------------------------------------------------
# Internal helpers (unchanged from v1.1.0)
# ---------------------------------------------------------------------------

def x__extract_regime_features__mutmut_140(returns_history: list) -> dict:
    clean = [r if math.isfinite(r) else 0.0 for r in returns_history]
    n = len(clean)
    mean_r = sum(clean) / n
    variance = sum((r - mean_r) ** 2 for r in clean) / max(n - 1, 1)
    volatility = math.sqrt(max(variance, 0.0))
    window = min(5, n)
    recent = clean[-window:]
    recent_mean = sum(recent) / window
    trend_strength = recent_mean / max(volatility, 1e-8)
    if n >= 2:
        pairs = [(clean[i], clean[i + 1]) for i in range(n - 1)]
        num = sum((a - mean_r) * (b - mean_r) for a, b in pairs)
        denom = sum((r - mean_r) ** 2 for r in clean)
        lag1_autocorr = num / max(denom, 1e-15)
        mean_reversion = max(-1.0, min(1.0, -lag1_autocorr))
    else:
        mean_reversion = 0.0
    short_window = min(10, n)
    short_clean = clean[-short_window:]
    short_mean = sum(short_clean) / len(short_clean)
    short_var = sum((r - short_mean) ** 2 for r in short_clean) / max(len(short_clean) - 1, 1)
    short_vol = math.sqrt(max(short_var, 0.0))
    full_vol = max(volatility, 1e-8)
    stress_raw = (short_vol / full_vol) - 1.0
    stress = max(0.0, min(1.0, stress_raw * 1.5 + 0.5))
    momentum = max(-1.0, min(1.0, recent_mean / max(full_vol, 1e-8)))
    liquidity = 1.0 - stress
    return {
        "volatility":     volatility,
        "trend_strength": trend_strength,
        "mean_reversion": mean_reversion,
        "stress":         stress,
        "momentum":       momentum,
        "liquidity":      liquidity,
    }


# ---------------------------------------------------------------------------
# Internal helpers (unchanged from v1.1.0)
# ---------------------------------------------------------------------------

def x__extract_regime_features__mutmut_141(returns_history: list) -> dict:
    clean = [r if math.isfinite(r) else 0.0 for r in returns_history]
    n = len(clean)
    mean_r = sum(clean) / n
    variance = sum((r - mean_r) ** 2 for r in clean) / max(n - 1, 1)
    volatility = math.sqrt(max(variance, 0.0))
    window = min(5, n)
    recent = clean[-window:]
    recent_mean = sum(recent) / window
    trend_strength = recent_mean / max(volatility, 1e-8)
    if n >= 2:
        pairs = [(clean[i], clean[i + 1]) for i in range(n - 1)]
        num = sum((a - mean_r) * (b - mean_r) for a, b in pairs)
        denom = sum((r - mean_r) ** 2 for r in clean)
        lag1_autocorr = num / max(denom, 1e-15)
        mean_reversion = max(-1.0, min(1.0, -lag1_autocorr))
    else:
        mean_reversion = 0.0
    short_window = min(10, n)
    short_clean = clean[-short_window:]
    short_mean = sum(short_clean) / len(short_clean)
    short_var = sum((r - short_mean) ** 2 for r in short_clean) / max(len(short_clean) - 1, 1)
    short_vol = math.sqrt(max(short_var, 0.0))
    full_vol = max(volatility, 1e-8)
    stress_raw = (short_vol / full_vol) - 1.0
    stress = max(0.0, min(1.0, stress_raw * 0.5 + 1.5))
    momentum = max(-1.0, min(1.0, recent_mean / max(full_vol, 1e-8)))
    liquidity = 1.0 - stress
    return {
        "volatility":     volatility,
        "trend_strength": trend_strength,
        "mean_reversion": mean_reversion,
        "stress":         stress,
        "momentum":       momentum,
        "liquidity":      liquidity,
    }


# ---------------------------------------------------------------------------
# Internal helpers (unchanged from v1.1.0)
# ---------------------------------------------------------------------------

def x__extract_regime_features__mutmut_142(returns_history: list) -> dict:
    clean = [r if math.isfinite(r) else 0.0 for r in returns_history]
    n = len(clean)
    mean_r = sum(clean) / n
    variance = sum((r - mean_r) ** 2 for r in clean) / max(n - 1, 1)
    volatility = math.sqrt(max(variance, 0.0))
    window = min(5, n)
    recent = clean[-window:]
    recent_mean = sum(recent) / window
    trend_strength = recent_mean / max(volatility, 1e-8)
    if n >= 2:
        pairs = [(clean[i], clean[i + 1]) for i in range(n - 1)]
        num = sum((a - mean_r) * (b - mean_r) for a, b in pairs)
        denom = sum((r - mean_r) ** 2 for r in clean)
        lag1_autocorr = num / max(denom, 1e-15)
        mean_reversion = max(-1.0, min(1.0, -lag1_autocorr))
    else:
        mean_reversion = 0.0
    short_window = min(10, n)
    short_clean = clean[-short_window:]
    short_mean = sum(short_clean) / len(short_clean)
    short_var = sum((r - short_mean) ** 2 for r in short_clean) / max(len(short_clean) - 1, 1)
    short_vol = math.sqrt(max(short_var, 0.0))
    full_vol = max(volatility, 1e-8)
    stress_raw = (short_vol / full_vol) - 1.0
    stress = max(0.0, min(1.0, stress_raw * 0.5 + 0.5))
    momentum = None
    liquidity = 1.0 - stress
    return {
        "volatility":     volatility,
        "trend_strength": trend_strength,
        "mean_reversion": mean_reversion,
        "stress":         stress,
        "momentum":       momentum,
        "liquidity":      liquidity,
    }


# ---------------------------------------------------------------------------
# Internal helpers (unchanged from v1.1.0)
# ---------------------------------------------------------------------------

def x__extract_regime_features__mutmut_143(returns_history: list) -> dict:
    clean = [r if math.isfinite(r) else 0.0 for r in returns_history]
    n = len(clean)
    mean_r = sum(clean) / n
    variance = sum((r - mean_r) ** 2 for r in clean) / max(n - 1, 1)
    volatility = math.sqrt(max(variance, 0.0))
    window = min(5, n)
    recent = clean[-window:]
    recent_mean = sum(recent) / window
    trend_strength = recent_mean / max(volatility, 1e-8)
    if n >= 2:
        pairs = [(clean[i], clean[i + 1]) for i in range(n - 1)]
        num = sum((a - mean_r) * (b - mean_r) for a, b in pairs)
        denom = sum((r - mean_r) ** 2 for r in clean)
        lag1_autocorr = num / max(denom, 1e-15)
        mean_reversion = max(-1.0, min(1.0, -lag1_autocorr))
    else:
        mean_reversion = 0.0
    short_window = min(10, n)
    short_clean = clean[-short_window:]
    short_mean = sum(short_clean) / len(short_clean)
    short_var = sum((r - short_mean) ** 2 for r in short_clean) / max(len(short_clean) - 1, 1)
    short_vol = math.sqrt(max(short_var, 0.0))
    full_vol = max(volatility, 1e-8)
    stress_raw = (short_vol / full_vol) - 1.0
    stress = max(0.0, min(1.0, stress_raw * 0.5 + 0.5))
    momentum = max(None, min(1.0, recent_mean / max(full_vol, 1e-8)))
    liquidity = 1.0 - stress
    return {
        "volatility":     volatility,
        "trend_strength": trend_strength,
        "mean_reversion": mean_reversion,
        "stress":         stress,
        "momentum":       momentum,
        "liquidity":      liquidity,
    }


# ---------------------------------------------------------------------------
# Internal helpers (unchanged from v1.1.0)
# ---------------------------------------------------------------------------

def x__extract_regime_features__mutmut_144(returns_history: list) -> dict:
    clean = [r if math.isfinite(r) else 0.0 for r in returns_history]
    n = len(clean)
    mean_r = sum(clean) / n
    variance = sum((r - mean_r) ** 2 for r in clean) / max(n - 1, 1)
    volatility = math.sqrt(max(variance, 0.0))
    window = min(5, n)
    recent = clean[-window:]
    recent_mean = sum(recent) / window
    trend_strength = recent_mean / max(volatility, 1e-8)
    if n >= 2:
        pairs = [(clean[i], clean[i + 1]) for i in range(n - 1)]
        num = sum((a - mean_r) * (b - mean_r) for a, b in pairs)
        denom = sum((r - mean_r) ** 2 for r in clean)
        lag1_autocorr = num / max(denom, 1e-15)
        mean_reversion = max(-1.0, min(1.0, -lag1_autocorr))
    else:
        mean_reversion = 0.0
    short_window = min(10, n)
    short_clean = clean[-short_window:]
    short_mean = sum(short_clean) / len(short_clean)
    short_var = sum((r - short_mean) ** 2 for r in short_clean) / max(len(short_clean) - 1, 1)
    short_vol = math.sqrt(max(short_var, 0.0))
    full_vol = max(volatility, 1e-8)
    stress_raw = (short_vol / full_vol) - 1.0
    stress = max(0.0, min(1.0, stress_raw * 0.5 + 0.5))
    momentum = max(-1.0, None)
    liquidity = 1.0 - stress
    return {
        "volatility":     volatility,
        "trend_strength": trend_strength,
        "mean_reversion": mean_reversion,
        "stress":         stress,
        "momentum":       momentum,
        "liquidity":      liquidity,
    }


# ---------------------------------------------------------------------------
# Internal helpers (unchanged from v1.1.0)
# ---------------------------------------------------------------------------

def x__extract_regime_features__mutmut_145(returns_history: list) -> dict:
    clean = [r if math.isfinite(r) else 0.0 for r in returns_history]
    n = len(clean)
    mean_r = sum(clean) / n
    variance = sum((r - mean_r) ** 2 for r in clean) / max(n - 1, 1)
    volatility = math.sqrt(max(variance, 0.0))
    window = min(5, n)
    recent = clean[-window:]
    recent_mean = sum(recent) / window
    trend_strength = recent_mean / max(volatility, 1e-8)
    if n >= 2:
        pairs = [(clean[i], clean[i + 1]) for i in range(n - 1)]
        num = sum((a - mean_r) * (b - mean_r) for a, b in pairs)
        denom = sum((r - mean_r) ** 2 for r in clean)
        lag1_autocorr = num / max(denom, 1e-15)
        mean_reversion = max(-1.0, min(1.0, -lag1_autocorr))
    else:
        mean_reversion = 0.0
    short_window = min(10, n)
    short_clean = clean[-short_window:]
    short_mean = sum(short_clean) / len(short_clean)
    short_var = sum((r - short_mean) ** 2 for r in short_clean) / max(len(short_clean) - 1, 1)
    short_vol = math.sqrt(max(short_var, 0.0))
    full_vol = max(volatility, 1e-8)
    stress_raw = (short_vol / full_vol) - 1.0
    stress = max(0.0, min(1.0, stress_raw * 0.5 + 0.5))
    momentum = max(min(1.0, recent_mean / max(full_vol, 1e-8)))
    liquidity = 1.0 - stress
    return {
        "volatility":     volatility,
        "trend_strength": trend_strength,
        "mean_reversion": mean_reversion,
        "stress":         stress,
        "momentum":       momentum,
        "liquidity":      liquidity,
    }


# ---------------------------------------------------------------------------
# Internal helpers (unchanged from v1.1.0)
# ---------------------------------------------------------------------------

def x__extract_regime_features__mutmut_146(returns_history: list) -> dict:
    clean = [r if math.isfinite(r) else 0.0 for r in returns_history]
    n = len(clean)
    mean_r = sum(clean) / n
    variance = sum((r - mean_r) ** 2 for r in clean) / max(n - 1, 1)
    volatility = math.sqrt(max(variance, 0.0))
    window = min(5, n)
    recent = clean[-window:]
    recent_mean = sum(recent) / window
    trend_strength = recent_mean / max(volatility, 1e-8)
    if n >= 2:
        pairs = [(clean[i], clean[i + 1]) for i in range(n - 1)]
        num = sum((a - mean_r) * (b - mean_r) for a, b in pairs)
        denom = sum((r - mean_r) ** 2 for r in clean)
        lag1_autocorr = num / max(denom, 1e-15)
        mean_reversion = max(-1.0, min(1.0, -lag1_autocorr))
    else:
        mean_reversion = 0.0
    short_window = min(10, n)
    short_clean = clean[-short_window:]
    short_mean = sum(short_clean) / len(short_clean)
    short_var = sum((r - short_mean) ** 2 for r in short_clean) / max(len(short_clean) - 1, 1)
    short_vol = math.sqrt(max(short_var, 0.0))
    full_vol = max(volatility, 1e-8)
    stress_raw = (short_vol / full_vol) - 1.0
    stress = max(0.0, min(1.0, stress_raw * 0.5 + 0.5))
    momentum = max(-1.0, )
    liquidity = 1.0 - stress
    return {
        "volatility":     volatility,
        "trend_strength": trend_strength,
        "mean_reversion": mean_reversion,
        "stress":         stress,
        "momentum":       momentum,
        "liquidity":      liquidity,
    }


# ---------------------------------------------------------------------------
# Internal helpers (unchanged from v1.1.0)
# ---------------------------------------------------------------------------

def x__extract_regime_features__mutmut_147(returns_history: list) -> dict:
    clean = [r if math.isfinite(r) else 0.0 for r in returns_history]
    n = len(clean)
    mean_r = sum(clean) / n
    variance = sum((r - mean_r) ** 2 for r in clean) / max(n - 1, 1)
    volatility = math.sqrt(max(variance, 0.0))
    window = min(5, n)
    recent = clean[-window:]
    recent_mean = sum(recent) / window
    trend_strength = recent_mean / max(volatility, 1e-8)
    if n >= 2:
        pairs = [(clean[i], clean[i + 1]) for i in range(n - 1)]
        num = sum((a - mean_r) * (b - mean_r) for a, b in pairs)
        denom = sum((r - mean_r) ** 2 for r in clean)
        lag1_autocorr = num / max(denom, 1e-15)
        mean_reversion = max(-1.0, min(1.0, -lag1_autocorr))
    else:
        mean_reversion = 0.0
    short_window = min(10, n)
    short_clean = clean[-short_window:]
    short_mean = sum(short_clean) / len(short_clean)
    short_var = sum((r - short_mean) ** 2 for r in short_clean) / max(len(short_clean) - 1, 1)
    short_vol = math.sqrt(max(short_var, 0.0))
    full_vol = max(volatility, 1e-8)
    stress_raw = (short_vol / full_vol) - 1.0
    stress = max(0.0, min(1.0, stress_raw * 0.5 + 0.5))
    momentum = max(+1.0, min(1.0, recent_mean / max(full_vol, 1e-8)))
    liquidity = 1.0 - stress
    return {
        "volatility":     volatility,
        "trend_strength": trend_strength,
        "mean_reversion": mean_reversion,
        "stress":         stress,
        "momentum":       momentum,
        "liquidity":      liquidity,
    }


# ---------------------------------------------------------------------------
# Internal helpers (unchanged from v1.1.0)
# ---------------------------------------------------------------------------

def x__extract_regime_features__mutmut_148(returns_history: list) -> dict:
    clean = [r if math.isfinite(r) else 0.0 for r in returns_history]
    n = len(clean)
    mean_r = sum(clean) / n
    variance = sum((r - mean_r) ** 2 for r in clean) / max(n - 1, 1)
    volatility = math.sqrt(max(variance, 0.0))
    window = min(5, n)
    recent = clean[-window:]
    recent_mean = sum(recent) / window
    trend_strength = recent_mean / max(volatility, 1e-8)
    if n >= 2:
        pairs = [(clean[i], clean[i + 1]) for i in range(n - 1)]
        num = sum((a - mean_r) * (b - mean_r) for a, b in pairs)
        denom = sum((r - mean_r) ** 2 for r in clean)
        lag1_autocorr = num / max(denom, 1e-15)
        mean_reversion = max(-1.0, min(1.0, -lag1_autocorr))
    else:
        mean_reversion = 0.0
    short_window = min(10, n)
    short_clean = clean[-short_window:]
    short_mean = sum(short_clean) / len(short_clean)
    short_var = sum((r - short_mean) ** 2 for r in short_clean) / max(len(short_clean) - 1, 1)
    short_vol = math.sqrt(max(short_var, 0.0))
    full_vol = max(volatility, 1e-8)
    stress_raw = (short_vol / full_vol) - 1.0
    stress = max(0.0, min(1.0, stress_raw * 0.5 + 0.5))
    momentum = max(-2.0, min(1.0, recent_mean / max(full_vol, 1e-8)))
    liquidity = 1.0 - stress
    return {
        "volatility":     volatility,
        "trend_strength": trend_strength,
        "mean_reversion": mean_reversion,
        "stress":         stress,
        "momentum":       momentum,
        "liquidity":      liquidity,
    }


# ---------------------------------------------------------------------------
# Internal helpers (unchanged from v1.1.0)
# ---------------------------------------------------------------------------

def x__extract_regime_features__mutmut_149(returns_history: list) -> dict:
    clean = [r if math.isfinite(r) else 0.0 for r in returns_history]
    n = len(clean)
    mean_r = sum(clean) / n
    variance = sum((r - mean_r) ** 2 for r in clean) / max(n - 1, 1)
    volatility = math.sqrt(max(variance, 0.0))
    window = min(5, n)
    recent = clean[-window:]
    recent_mean = sum(recent) / window
    trend_strength = recent_mean / max(volatility, 1e-8)
    if n >= 2:
        pairs = [(clean[i], clean[i + 1]) for i in range(n - 1)]
        num = sum((a - mean_r) * (b - mean_r) for a, b in pairs)
        denom = sum((r - mean_r) ** 2 for r in clean)
        lag1_autocorr = num / max(denom, 1e-15)
        mean_reversion = max(-1.0, min(1.0, -lag1_autocorr))
    else:
        mean_reversion = 0.0
    short_window = min(10, n)
    short_clean = clean[-short_window:]
    short_mean = sum(short_clean) / len(short_clean)
    short_var = sum((r - short_mean) ** 2 for r in short_clean) / max(len(short_clean) - 1, 1)
    short_vol = math.sqrt(max(short_var, 0.0))
    full_vol = max(volatility, 1e-8)
    stress_raw = (short_vol / full_vol) - 1.0
    stress = max(0.0, min(1.0, stress_raw * 0.5 + 0.5))
    momentum = max(-1.0, min(None, recent_mean / max(full_vol, 1e-8)))
    liquidity = 1.0 - stress
    return {
        "volatility":     volatility,
        "trend_strength": trend_strength,
        "mean_reversion": mean_reversion,
        "stress":         stress,
        "momentum":       momentum,
        "liquidity":      liquidity,
    }


# ---------------------------------------------------------------------------
# Internal helpers (unchanged from v1.1.0)
# ---------------------------------------------------------------------------

def x__extract_regime_features__mutmut_150(returns_history: list) -> dict:
    clean = [r if math.isfinite(r) else 0.0 for r in returns_history]
    n = len(clean)
    mean_r = sum(clean) / n
    variance = sum((r - mean_r) ** 2 for r in clean) / max(n - 1, 1)
    volatility = math.sqrt(max(variance, 0.0))
    window = min(5, n)
    recent = clean[-window:]
    recent_mean = sum(recent) / window
    trend_strength = recent_mean / max(volatility, 1e-8)
    if n >= 2:
        pairs = [(clean[i], clean[i + 1]) for i in range(n - 1)]
        num = sum((a - mean_r) * (b - mean_r) for a, b in pairs)
        denom = sum((r - mean_r) ** 2 for r in clean)
        lag1_autocorr = num / max(denom, 1e-15)
        mean_reversion = max(-1.0, min(1.0, -lag1_autocorr))
    else:
        mean_reversion = 0.0
    short_window = min(10, n)
    short_clean = clean[-short_window:]
    short_mean = sum(short_clean) / len(short_clean)
    short_var = sum((r - short_mean) ** 2 for r in short_clean) / max(len(short_clean) - 1, 1)
    short_vol = math.sqrt(max(short_var, 0.0))
    full_vol = max(volatility, 1e-8)
    stress_raw = (short_vol / full_vol) - 1.0
    stress = max(0.0, min(1.0, stress_raw * 0.5 + 0.5))
    momentum = max(-1.0, min(1.0, None))
    liquidity = 1.0 - stress
    return {
        "volatility":     volatility,
        "trend_strength": trend_strength,
        "mean_reversion": mean_reversion,
        "stress":         stress,
        "momentum":       momentum,
        "liquidity":      liquidity,
    }


# ---------------------------------------------------------------------------
# Internal helpers (unchanged from v1.1.0)
# ---------------------------------------------------------------------------

def x__extract_regime_features__mutmut_151(returns_history: list) -> dict:
    clean = [r if math.isfinite(r) else 0.0 for r in returns_history]
    n = len(clean)
    mean_r = sum(clean) / n
    variance = sum((r - mean_r) ** 2 for r in clean) / max(n - 1, 1)
    volatility = math.sqrt(max(variance, 0.0))
    window = min(5, n)
    recent = clean[-window:]
    recent_mean = sum(recent) / window
    trend_strength = recent_mean / max(volatility, 1e-8)
    if n >= 2:
        pairs = [(clean[i], clean[i + 1]) for i in range(n - 1)]
        num = sum((a - mean_r) * (b - mean_r) for a, b in pairs)
        denom = sum((r - mean_r) ** 2 for r in clean)
        lag1_autocorr = num / max(denom, 1e-15)
        mean_reversion = max(-1.0, min(1.0, -lag1_autocorr))
    else:
        mean_reversion = 0.0
    short_window = min(10, n)
    short_clean = clean[-short_window:]
    short_mean = sum(short_clean) / len(short_clean)
    short_var = sum((r - short_mean) ** 2 for r in short_clean) / max(len(short_clean) - 1, 1)
    short_vol = math.sqrt(max(short_var, 0.0))
    full_vol = max(volatility, 1e-8)
    stress_raw = (short_vol / full_vol) - 1.0
    stress = max(0.0, min(1.0, stress_raw * 0.5 + 0.5))
    momentum = max(-1.0, min(recent_mean / max(full_vol, 1e-8)))
    liquidity = 1.0 - stress
    return {
        "volatility":     volatility,
        "trend_strength": trend_strength,
        "mean_reversion": mean_reversion,
        "stress":         stress,
        "momentum":       momentum,
        "liquidity":      liquidity,
    }


# ---------------------------------------------------------------------------
# Internal helpers (unchanged from v1.1.0)
# ---------------------------------------------------------------------------

def x__extract_regime_features__mutmut_152(returns_history: list) -> dict:
    clean = [r if math.isfinite(r) else 0.0 for r in returns_history]
    n = len(clean)
    mean_r = sum(clean) / n
    variance = sum((r - mean_r) ** 2 for r in clean) / max(n - 1, 1)
    volatility = math.sqrt(max(variance, 0.0))
    window = min(5, n)
    recent = clean[-window:]
    recent_mean = sum(recent) / window
    trend_strength = recent_mean / max(volatility, 1e-8)
    if n >= 2:
        pairs = [(clean[i], clean[i + 1]) for i in range(n - 1)]
        num = sum((a - mean_r) * (b - mean_r) for a, b in pairs)
        denom = sum((r - mean_r) ** 2 for r in clean)
        lag1_autocorr = num / max(denom, 1e-15)
        mean_reversion = max(-1.0, min(1.0, -lag1_autocorr))
    else:
        mean_reversion = 0.0
    short_window = min(10, n)
    short_clean = clean[-short_window:]
    short_mean = sum(short_clean) / len(short_clean)
    short_var = sum((r - short_mean) ** 2 for r in short_clean) / max(len(short_clean) - 1, 1)
    short_vol = math.sqrt(max(short_var, 0.0))
    full_vol = max(volatility, 1e-8)
    stress_raw = (short_vol / full_vol) - 1.0
    stress = max(0.0, min(1.0, stress_raw * 0.5 + 0.5))
    momentum = max(-1.0, min(1.0, ))
    liquidity = 1.0 - stress
    return {
        "volatility":     volatility,
        "trend_strength": trend_strength,
        "mean_reversion": mean_reversion,
        "stress":         stress,
        "momentum":       momentum,
        "liquidity":      liquidity,
    }


# ---------------------------------------------------------------------------
# Internal helpers (unchanged from v1.1.0)
# ---------------------------------------------------------------------------

def x__extract_regime_features__mutmut_153(returns_history: list) -> dict:
    clean = [r if math.isfinite(r) else 0.0 for r in returns_history]
    n = len(clean)
    mean_r = sum(clean) / n
    variance = sum((r - mean_r) ** 2 for r in clean) / max(n - 1, 1)
    volatility = math.sqrt(max(variance, 0.0))
    window = min(5, n)
    recent = clean[-window:]
    recent_mean = sum(recent) / window
    trend_strength = recent_mean / max(volatility, 1e-8)
    if n >= 2:
        pairs = [(clean[i], clean[i + 1]) for i in range(n - 1)]
        num = sum((a - mean_r) * (b - mean_r) for a, b in pairs)
        denom = sum((r - mean_r) ** 2 for r in clean)
        lag1_autocorr = num / max(denom, 1e-15)
        mean_reversion = max(-1.0, min(1.0, -lag1_autocorr))
    else:
        mean_reversion = 0.0
    short_window = min(10, n)
    short_clean = clean[-short_window:]
    short_mean = sum(short_clean) / len(short_clean)
    short_var = sum((r - short_mean) ** 2 for r in short_clean) / max(len(short_clean) - 1, 1)
    short_vol = math.sqrt(max(short_var, 0.0))
    full_vol = max(volatility, 1e-8)
    stress_raw = (short_vol / full_vol) - 1.0
    stress = max(0.0, min(1.0, stress_raw * 0.5 + 0.5))
    momentum = max(-1.0, min(2.0, recent_mean / max(full_vol, 1e-8)))
    liquidity = 1.0 - stress
    return {
        "volatility":     volatility,
        "trend_strength": trend_strength,
        "mean_reversion": mean_reversion,
        "stress":         stress,
        "momentum":       momentum,
        "liquidity":      liquidity,
    }


# ---------------------------------------------------------------------------
# Internal helpers (unchanged from v1.1.0)
# ---------------------------------------------------------------------------

def x__extract_regime_features__mutmut_154(returns_history: list) -> dict:
    clean = [r if math.isfinite(r) else 0.0 for r in returns_history]
    n = len(clean)
    mean_r = sum(clean) / n
    variance = sum((r - mean_r) ** 2 for r in clean) / max(n - 1, 1)
    volatility = math.sqrt(max(variance, 0.0))
    window = min(5, n)
    recent = clean[-window:]
    recent_mean = sum(recent) / window
    trend_strength = recent_mean / max(volatility, 1e-8)
    if n >= 2:
        pairs = [(clean[i], clean[i + 1]) for i in range(n - 1)]
        num = sum((a - mean_r) * (b - mean_r) for a, b in pairs)
        denom = sum((r - mean_r) ** 2 for r in clean)
        lag1_autocorr = num / max(denom, 1e-15)
        mean_reversion = max(-1.0, min(1.0, -lag1_autocorr))
    else:
        mean_reversion = 0.0
    short_window = min(10, n)
    short_clean = clean[-short_window:]
    short_mean = sum(short_clean) / len(short_clean)
    short_var = sum((r - short_mean) ** 2 for r in short_clean) / max(len(short_clean) - 1, 1)
    short_vol = math.sqrt(max(short_var, 0.0))
    full_vol = max(volatility, 1e-8)
    stress_raw = (short_vol / full_vol) - 1.0
    stress = max(0.0, min(1.0, stress_raw * 0.5 + 0.5))
    momentum = max(-1.0, min(1.0, recent_mean * max(full_vol, 1e-8)))
    liquidity = 1.0 - stress
    return {
        "volatility":     volatility,
        "trend_strength": trend_strength,
        "mean_reversion": mean_reversion,
        "stress":         stress,
        "momentum":       momentum,
        "liquidity":      liquidity,
    }


# ---------------------------------------------------------------------------
# Internal helpers (unchanged from v1.1.0)
# ---------------------------------------------------------------------------

def x__extract_regime_features__mutmut_155(returns_history: list) -> dict:
    clean = [r if math.isfinite(r) else 0.0 for r in returns_history]
    n = len(clean)
    mean_r = sum(clean) / n
    variance = sum((r - mean_r) ** 2 for r in clean) / max(n - 1, 1)
    volatility = math.sqrt(max(variance, 0.0))
    window = min(5, n)
    recent = clean[-window:]
    recent_mean = sum(recent) / window
    trend_strength = recent_mean / max(volatility, 1e-8)
    if n >= 2:
        pairs = [(clean[i], clean[i + 1]) for i in range(n - 1)]
        num = sum((a - mean_r) * (b - mean_r) for a, b in pairs)
        denom = sum((r - mean_r) ** 2 for r in clean)
        lag1_autocorr = num / max(denom, 1e-15)
        mean_reversion = max(-1.0, min(1.0, -lag1_autocorr))
    else:
        mean_reversion = 0.0
    short_window = min(10, n)
    short_clean = clean[-short_window:]
    short_mean = sum(short_clean) / len(short_clean)
    short_var = sum((r - short_mean) ** 2 for r in short_clean) / max(len(short_clean) - 1, 1)
    short_vol = math.sqrt(max(short_var, 0.0))
    full_vol = max(volatility, 1e-8)
    stress_raw = (short_vol / full_vol) - 1.0
    stress = max(0.0, min(1.0, stress_raw * 0.5 + 0.5))
    momentum = max(-1.0, min(1.0, recent_mean / max(None, 1e-8)))
    liquidity = 1.0 - stress
    return {
        "volatility":     volatility,
        "trend_strength": trend_strength,
        "mean_reversion": mean_reversion,
        "stress":         stress,
        "momentum":       momentum,
        "liquidity":      liquidity,
    }


# ---------------------------------------------------------------------------
# Internal helpers (unchanged from v1.1.0)
# ---------------------------------------------------------------------------

def x__extract_regime_features__mutmut_156(returns_history: list) -> dict:
    clean = [r if math.isfinite(r) else 0.0 for r in returns_history]
    n = len(clean)
    mean_r = sum(clean) / n
    variance = sum((r - mean_r) ** 2 for r in clean) / max(n - 1, 1)
    volatility = math.sqrt(max(variance, 0.0))
    window = min(5, n)
    recent = clean[-window:]
    recent_mean = sum(recent) / window
    trend_strength = recent_mean / max(volatility, 1e-8)
    if n >= 2:
        pairs = [(clean[i], clean[i + 1]) for i in range(n - 1)]
        num = sum((a - mean_r) * (b - mean_r) for a, b in pairs)
        denom = sum((r - mean_r) ** 2 for r in clean)
        lag1_autocorr = num / max(denom, 1e-15)
        mean_reversion = max(-1.0, min(1.0, -lag1_autocorr))
    else:
        mean_reversion = 0.0
    short_window = min(10, n)
    short_clean = clean[-short_window:]
    short_mean = sum(short_clean) / len(short_clean)
    short_var = sum((r - short_mean) ** 2 for r in short_clean) / max(len(short_clean) - 1, 1)
    short_vol = math.sqrt(max(short_var, 0.0))
    full_vol = max(volatility, 1e-8)
    stress_raw = (short_vol / full_vol) - 1.0
    stress = max(0.0, min(1.0, stress_raw * 0.5 + 0.5))
    momentum = max(-1.0, min(1.0, recent_mean / max(full_vol, None)))
    liquidity = 1.0 - stress
    return {
        "volatility":     volatility,
        "trend_strength": trend_strength,
        "mean_reversion": mean_reversion,
        "stress":         stress,
        "momentum":       momentum,
        "liquidity":      liquidity,
    }


# ---------------------------------------------------------------------------
# Internal helpers (unchanged from v1.1.0)
# ---------------------------------------------------------------------------

def x__extract_regime_features__mutmut_157(returns_history: list) -> dict:
    clean = [r if math.isfinite(r) else 0.0 for r in returns_history]
    n = len(clean)
    mean_r = sum(clean) / n
    variance = sum((r - mean_r) ** 2 for r in clean) / max(n - 1, 1)
    volatility = math.sqrt(max(variance, 0.0))
    window = min(5, n)
    recent = clean[-window:]
    recent_mean = sum(recent) / window
    trend_strength = recent_mean / max(volatility, 1e-8)
    if n >= 2:
        pairs = [(clean[i], clean[i + 1]) for i in range(n - 1)]
        num = sum((a - mean_r) * (b - mean_r) for a, b in pairs)
        denom = sum((r - mean_r) ** 2 for r in clean)
        lag1_autocorr = num / max(denom, 1e-15)
        mean_reversion = max(-1.0, min(1.0, -lag1_autocorr))
    else:
        mean_reversion = 0.0
    short_window = min(10, n)
    short_clean = clean[-short_window:]
    short_mean = sum(short_clean) / len(short_clean)
    short_var = sum((r - short_mean) ** 2 for r in short_clean) / max(len(short_clean) - 1, 1)
    short_vol = math.sqrt(max(short_var, 0.0))
    full_vol = max(volatility, 1e-8)
    stress_raw = (short_vol / full_vol) - 1.0
    stress = max(0.0, min(1.0, stress_raw * 0.5 + 0.5))
    momentum = max(-1.0, min(1.0, recent_mean / max(1e-8)))
    liquidity = 1.0 - stress
    return {
        "volatility":     volatility,
        "trend_strength": trend_strength,
        "mean_reversion": mean_reversion,
        "stress":         stress,
        "momentum":       momentum,
        "liquidity":      liquidity,
    }


# ---------------------------------------------------------------------------
# Internal helpers (unchanged from v1.1.0)
# ---------------------------------------------------------------------------

def x__extract_regime_features__mutmut_158(returns_history: list) -> dict:
    clean = [r if math.isfinite(r) else 0.0 for r in returns_history]
    n = len(clean)
    mean_r = sum(clean) / n
    variance = sum((r - mean_r) ** 2 for r in clean) / max(n - 1, 1)
    volatility = math.sqrt(max(variance, 0.0))
    window = min(5, n)
    recent = clean[-window:]
    recent_mean = sum(recent) / window
    trend_strength = recent_mean / max(volatility, 1e-8)
    if n >= 2:
        pairs = [(clean[i], clean[i + 1]) for i in range(n - 1)]
        num = sum((a - mean_r) * (b - mean_r) for a, b in pairs)
        denom = sum((r - mean_r) ** 2 for r in clean)
        lag1_autocorr = num / max(denom, 1e-15)
        mean_reversion = max(-1.0, min(1.0, -lag1_autocorr))
    else:
        mean_reversion = 0.0
    short_window = min(10, n)
    short_clean = clean[-short_window:]
    short_mean = sum(short_clean) / len(short_clean)
    short_var = sum((r - short_mean) ** 2 for r in short_clean) / max(len(short_clean) - 1, 1)
    short_vol = math.sqrt(max(short_var, 0.0))
    full_vol = max(volatility, 1e-8)
    stress_raw = (short_vol / full_vol) - 1.0
    stress = max(0.0, min(1.0, stress_raw * 0.5 + 0.5))
    momentum = max(-1.0, min(1.0, recent_mean / max(full_vol, )))
    liquidity = 1.0 - stress
    return {
        "volatility":     volatility,
        "trend_strength": trend_strength,
        "mean_reversion": mean_reversion,
        "stress":         stress,
        "momentum":       momentum,
        "liquidity":      liquidity,
    }


# ---------------------------------------------------------------------------
# Internal helpers (unchanged from v1.1.0)
# ---------------------------------------------------------------------------

def x__extract_regime_features__mutmut_159(returns_history: list) -> dict:
    clean = [r if math.isfinite(r) else 0.0 for r in returns_history]
    n = len(clean)
    mean_r = sum(clean) / n
    variance = sum((r - mean_r) ** 2 for r in clean) / max(n - 1, 1)
    volatility = math.sqrt(max(variance, 0.0))
    window = min(5, n)
    recent = clean[-window:]
    recent_mean = sum(recent) / window
    trend_strength = recent_mean / max(volatility, 1e-8)
    if n >= 2:
        pairs = [(clean[i], clean[i + 1]) for i in range(n - 1)]
        num = sum((a - mean_r) * (b - mean_r) for a, b in pairs)
        denom = sum((r - mean_r) ** 2 for r in clean)
        lag1_autocorr = num / max(denom, 1e-15)
        mean_reversion = max(-1.0, min(1.0, -lag1_autocorr))
    else:
        mean_reversion = 0.0
    short_window = min(10, n)
    short_clean = clean[-short_window:]
    short_mean = sum(short_clean) / len(short_clean)
    short_var = sum((r - short_mean) ** 2 for r in short_clean) / max(len(short_clean) - 1, 1)
    short_vol = math.sqrt(max(short_var, 0.0))
    full_vol = max(volatility, 1e-8)
    stress_raw = (short_vol / full_vol) - 1.0
    stress = max(0.0, min(1.0, stress_raw * 0.5 + 0.5))
    momentum = max(-1.0, min(1.0, recent_mean / max(full_vol, 1.00000001)))
    liquidity = 1.0 - stress
    return {
        "volatility":     volatility,
        "trend_strength": trend_strength,
        "mean_reversion": mean_reversion,
        "stress":         stress,
        "momentum":       momentum,
        "liquidity":      liquidity,
    }


# ---------------------------------------------------------------------------
# Internal helpers (unchanged from v1.1.0)
# ---------------------------------------------------------------------------

def x__extract_regime_features__mutmut_160(returns_history: list) -> dict:
    clean = [r if math.isfinite(r) else 0.0 for r in returns_history]
    n = len(clean)
    mean_r = sum(clean) / n
    variance = sum((r - mean_r) ** 2 for r in clean) / max(n - 1, 1)
    volatility = math.sqrt(max(variance, 0.0))
    window = min(5, n)
    recent = clean[-window:]
    recent_mean = sum(recent) / window
    trend_strength = recent_mean / max(volatility, 1e-8)
    if n >= 2:
        pairs = [(clean[i], clean[i + 1]) for i in range(n - 1)]
        num = sum((a - mean_r) * (b - mean_r) for a, b in pairs)
        denom = sum((r - mean_r) ** 2 for r in clean)
        lag1_autocorr = num / max(denom, 1e-15)
        mean_reversion = max(-1.0, min(1.0, -lag1_autocorr))
    else:
        mean_reversion = 0.0
    short_window = min(10, n)
    short_clean = clean[-short_window:]
    short_mean = sum(short_clean) / len(short_clean)
    short_var = sum((r - short_mean) ** 2 for r in short_clean) / max(len(short_clean) - 1, 1)
    short_vol = math.sqrt(max(short_var, 0.0))
    full_vol = max(volatility, 1e-8)
    stress_raw = (short_vol / full_vol) - 1.0
    stress = max(0.0, min(1.0, stress_raw * 0.5 + 0.5))
    momentum = max(-1.0, min(1.0, recent_mean / max(full_vol, 1e-8)))
    liquidity = None
    return {
        "volatility":     volatility,
        "trend_strength": trend_strength,
        "mean_reversion": mean_reversion,
        "stress":         stress,
        "momentum":       momentum,
        "liquidity":      liquidity,
    }


# ---------------------------------------------------------------------------
# Internal helpers (unchanged from v1.1.0)
# ---------------------------------------------------------------------------

def x__extract_regime_features__mutmut_161(returns_history: list) -> dict:
    clean = [r if math.isfinite(r) else 0.0 for r in returns_history]
    n = len(clean)
    mean_r = sum(clean) / n
    variance = sum((r - mean_r) ** 2 for r in clean) / max(n - 1, 1)
    volatility = math.sqrt(max(variance, 0.0))
    window = min(5, n)
    recent = clean[-window:]
    recent_mean = sum(recent) / window
    trend_strength = recent_mean / max(volatility, 1e-8)
    if n >= 2:
        pairs = [(clean[i], clean[i + 1]) for i in range(n - 1)]
        num = sum((a - mean_r) * (b - mean_r) for a, b in pairs)
        denom = sum((r - mean_r) ** 2 for r in clean)
        lag1_autocorr = num / max(denom, 1e-15)
        mean_reversion = max(-1.0, min(1.0, -lag1_autocorr))
    else:
        mean_reversion = 0.0
    short_window = min(10, n)
    short_clean = clean[-short_window:]
    short_mean = sum(short_clean) / len(short_clean)
    short_var = sum((r - short_mean) ** 2 for r in short_clean) / max(len(short_clean) - 1, 1)
    short_vol = math.sqrt(max(short_var, 0.0))
    full_vol = max(volatility, 1e-8)
    stress_raw = (short_vol / full_vol) - 1.0
    stress = max(0.0, min(1.0, stress_raw * 0.5 + 0.5))
    momentum = max(-1.0, min(1.0, recent_mean / max(full_vol, 1e-8)))
    liquidity = 1.0 + stress
    return {
        "volatility":     volatility,
        "trend_strength": trend_strength,
        "mean_reversion": mean_reversion,
        "stress":         stress,
        "momentum":       momentum,
        "liquidity":      liquidity,
    }


# ---------------------------------------------------------------------------
# Internal helpers (unchanged from v1.1.0)
# ---------------------------------------------------------------------------

def x__extract_regime_features__mutmut_162(returns_history: list) -> dict:
    clean = [r if math.isfinite(r) else 0.0 for r in returns_history]
    n = len(clean)
    mean_r = sum(clean) / n
    variance = sum((r - mean_r) ** 2 for r in clean) / max(n - 1, 1)
    volatility = math.sqrt(max(variance, 0.0))
    window = min(5, n)
    recent = clean[-window:]
    recent_mean = sum(recent) / window
    trend_strength = recent_mean / max(volatility, 1e-8)
    if n >= 2:
        pairs = [(clean[i], clean[i + 1]) for i in range(n - 1)]
        num = sum((a - mean_r) * (b - mean_r) for a, b in pairs)
        denom = sum((r - mean_r) ** 2 for r in clean)
        lag1_autocorr = num / max(denom, 1e-15)
        mean_reversion = max(-1.0, min(1.0, -lag1_autocorr))
    else:
        mean_reversion = 0.0
    short_window = min(10, n)
    short_clean = clean[-short_window:]
    short_mean = sum(short_clean) / len(short_clean)
    short_var = sum((r - short_mean) ** 2 for r in short_clean) / max(len(short_clean) - 1, 1)
    short_vol = math.sqrt(max(short_var, 0.0))
    full_vol = max(volatility, 1e-8)
    stress_raw = (short_vol / full_vol) - 1.0
    stress = max(0.0, min(1.0, stress_raw * 0.5 + 0.5))
    momentum = max(-1.0, min(1.0, recent_mean / max(full_vol, 1e-8)))
    liquidity = 2.0 - stress
    return {
        "volatility":     volatility,
        "trend_strength": trend_strength,
        "mean_reversion": mean_reversion,
        "stress":         stress,
        "momentum":       momentum,
        "liquidity":      liquidity,
    }


# ---------------------------------------------------------------------------
# Internal helpers (unchanged from v1.1.0)
# ---------------------------------------------------------------------------

def x__extract_regime_features__mutmut_163(returns_history: list) -> dict:
    clean = [r if math.isfinite(r) else 0.0 for r in returns_history]
    n = len(clean)
    mean_r = sum(clean) / n
    variance = sum((r - mean_r) ** 2 for r in clean) / max(n - 1, 1)
    volatility = math.sqrt(max(variance, 0.0))
    window = min(5, n)
    recent = clean[-window:]
    recent_mean = sum(recent) / window
    trend_strength = recent_mean / max(volatility, 1e-8)
    if n >= 2:
        pairs = [(clean[i], clean[i + 1]) for i in range(n - 1)]
        num = sum((a - mean_r) * (b - mean_r) for a, b in pairs)
        denom = sum((r - mean_r) ** 2 for r in clean)
        lag1_autocorr = num / max(denom, 1e-15)
        mean_reversion = max(-1.0, min(1.0, -lag1_autocorr))
    else:
        mean_reversion = 0.0
    short_window = min(10, n)
    short_clean = clean[-short_window:]
    short_mean = sum(short_clean) / len(short_clean)
    short_var = sum((r - short_mean) ** 2 for r in short_clean) / max(len(short_clean) - 1, 1)
    short_vol = math.sqrt(max(short_var, 0.0))
    full_vol = max(volatility, 1e-8)
    stress_raw = (short_vol / full_vol) - 1.0
    stress = max(0.0, min(1.0, stress_raw * 0.5 + 0.5))
    momentum = max(-1.0, min(1.0, recent_mean / max(full_vol, 1e-8)))
    liquidity = 1.0 - stress
    return {
        "XXvolatilityXX":     volatility,
        "trend_strength": trend_strength,
        "mean_reversion": mean_reversion,
        "stress":         stress,
        "momentum":       momentum,
        "liquidity":      liquidity,
    }


# ---------------------------------------------------------------------------
# Internal helpers (unchanged from v1.1.0)
# ---------------------------------------------------------------------------

def x__extract_regime_features__mutmut_164(returns_history: list) -> dict:
    clean = [r if math.isfinite(r) else 0.0 for r in returns_history]
    n = len(clean)
    mean_r = sum(clean) / n
    variance = sum((r - mean_r) ** 2 for r in clean) / max(n - 1, 1)
    volatility = math.sqrt(max(variance, 0.0))
    window = min(5, n)
    recent = clean[-window:]
    recent_mean = sum(recent) / window
    trend_strength = recent_mean / max(volatility, 1e-8)
    if n >= 2:
        pairs = [(clean[i], clean[i + 1]) for i in range(n - 1)]
        num = sum((a - mean_r) * (b - mean_r) for a, b in pairs)
        denom = sum((r - mean_r) ** 2 for r in clean)
        lag1_autocorr = num / max(denom, 1e-15)
        mean_reversion = max(-1.0, min(1.0, -lag1_autocorr))
    else:
        mean_reversion = 0.0
    short_window = min(10, n)
    short_clean = clean[-short_window:]
    short_mean = sum(short_clean) / len(short_clean)
    short_var = sum((r - short_mean) ** 2 for r in short_clean) / max(len(short_clean) - 1, 1)
    short_vol = math.sqrt(max(short_var, 0.0))
    full_vol = max(volatility, 1e-8)
    stress_raw = (short_vol / full_vol) - 1.0
    stress = max(0.0, min(1.0, stress_raw * 0.5 + 0.5))
    momentum = max(-1.0, min(1.0, recent_mean / max(full_vol, 1e-8)))
    liquidity = 1.0 - stress
    return {
        "VOLATILITY":     volatility,
        "trend_strength": trend_strength,
        "mean_reversion": mean_reversion,
        "stress":         stress,
        "momentum":       momentum,
        "liquidity":      liquidity,
    }


# ---------------------------------------------------------------------------
# Internal helpers (unchanged from v1.1.0)
# ---------------------------------------------------------------------------

def x__extract_regime_features__mutmut_165(returns_history: list) -> dict:
    clean = [r if math.isfinite(r) else 0.0 for r in returns_history]
    n = len(clean)
    mean_r = sum(clean) / n
    variance = sum((r - mean_r) ** 2 for r in clean) / max(n - 1, 1)
    volatility = math.sqrt(max(variance, 0.0))
    window = min(5, n)
    recent = clean[-window:]
    recent_mean = sum(recent) / window
    trend_strength = recent_mean / max(volatility, 1e-8)
    if n >= 2:
        pairs = [(clean[i], clean[i + 1]) for i in range(n - 1)]
        num = sum((a - mean_r) * (b - mean_r) for a, b in pairs)
        denom = sum((r - mean_r) ** 2 for r in clean)
        lag1_autocorr = num / max(denom, 1e-15)
        mean_reversion = max(-1.0, min(1.0, -lag1_autocorr))
    else:
        mean_reversion = 0.0
    short_window = min(10, n)
    short_clean = clean[-short_window:]
    short_mean = sum(short_clean) / len(short_clean)
    short_var = sum((r - short_mean) ** 2 for r in short_clean) / max(len(short_clean) - 1, 1)
    short_vol = math.sqrt(max(short_var, 0.0))
    full_vol = max(volatility, 1e-8)
    stress_raw = (short_vol / full_vol) - 1.0
    stress = max(0.0, min(1.0, stress_raw * 0.5 + 0.5))
    momentum = max(-1.0, min(1.0, recent_mean / max(full_vol, 1e-8)))
    liquidity = 1.0 - stress
    return {
        "volatility":     volatility,
        "XXtrend_strengthXX": trend_strength,
        "mean_reversion": mean_reversion,
        "stress":         stress,
        "momentum":       momentum,
        "liquidity":      liquidity,
    }


# ---------------------------------------------------------------------------
# Internal helpers (unchanged from v1.1.0)
# ---------------------------------------------------------------------------

def x__extract_regime_features__mutmut_166(returns_history: list) -> dict:
    clean = [r if math.isfinite(r) else 0.0 for r in returns_history]
    n = len(clean)
    mean_r = sum(clean) / n
    variance = sum((r - mean_r) ** 2 for r in clean) / max(n - 1, 1)
    volatility = math.sqrt(max(variance, 0.0))
    window = min(5, n)
    recent = clean[-window:]
    recent_mean = sum(recent) / window
    trend_strength = recent_mean / max(volatility, 1e-8)
    if n >= 2:
        pairs = [(clean[i], clean[i + 1]) for i in range(n - 1)]
        num = sum((a - mean_r) * (b - mean_r) for a, b in pairs)
        denom = sum((r - mean_r) ** 2 for r in clean)
        lag1_autocorr = num / max(denom, 1e-15)
        mean_reversion = max(-1.0, min(1.0, -lag1_autocorr))
    else:
        mean_reversion = 0.0
    short_window = min(10, n)
    short_clean = clean[-short_window:]
    short_mean = sum(short_clean) / len(short_clean)
    short_var = sum((r - short_mean) ** 2 for r in short_clean) / max(len(short_clean) - 1, 1)
    short_vol = math.sqrt(max(short_var, 0.0))
    full_vol = max(volatility, 1e-8)
    stress_raw = (short_vol / full_vol) - 1.0
    stress = max(0.0, min(1.0, stress_raw * 0.5 + 0.5))
    momentum = max(-1.0, min(1.0, recent_mean / max(full_vol, 1e-8)))
    liquidity = 1.0 - stress
    return {
        "volatility":     volatility,
        "TREND_STRENGTH": trend_strength,
        "mean_reversion": mean_reversion,
        "stress":         stress,
        "momentum":       momentum,
        "liquidity":      liquidity,
    }


# ---------------------------------------------------------------------------
# Internal helpers (unchanged from v1.1.0)
# ---------------------------------------------------------------------------

def x__extract_regime_features__mutmut_167(returns_history: list) -> dict:
    clean = [r if math.isfinite(r) else 0.0 for r in returns_history]
    n = len(clean)
    mean_r = sum(clean) / n
    variance = sum((r - mean_r) ** 2 for r in clean) / max(n - 1, 1)
    volatility = math.sqrt(max(variance, 0.0))
    window = min(5, n)
    recent = clean[-window:]
    recent_mean = sum(recent) / window
    trend_strength = recent_mean / max(volatility, 1e-8)
    if n >= 2:
        pairs = [(clean[i], clean[i + 1]) for i in range(n - 1)]
        num = sum((a - mean_r) * (b - mean_r) for a, b in pairs)
        denom = sum((r - mean_r) ** 2 for r in clean)
        lag1_autocorr = num / max(denom, 1e-15)
        mean_reversion = max(-1.0, min(1.0, -lag1_autocorr))
    else:
        mean_reversion = 0.0
    short_window = min(10, n)
    short_clean = clean[-short_window:]
    short_mean = sum(short_clean) / len(short_clean)
    short_var = sum((r - short_mean) ** 2 for r in short_clean) / max(len(short_clean) - 1, 1)
    short_vol = math.sqrt(max(short_var, 0.0))
    full_vol = max(volatility, 1e-8)
    stress_raw = (short_vol / full_vol) - 1.0
    stress = max(0.0, min(1.0, stress_raw * 0.5 + 0.5))
    momentum = max(-1.0, min(1.0, recent_mean / max(full_vol, 1e-8)))
    liquidity = 1.0 - stress
    return {
        "volatility":     volatility,
        "trend_strength": trend_strength,
        "XXmean_reversionXX": mean_reversion,
        "stress":         stress,
        "momentum":       momentum,
        "liquidity":      liquidity,
    }


# ---------------------------------------------------------------------------
# Internal helpers (unchanged from v1.1.0)
# ---------------------------------------------------------------------------

def x__extract_regime_features__mutmut_168(returns_history: list) -> dict:
    clean = [r if math.isfinite(r) else 0.0 for r in returns_history]
    n = len(clean)
    mean_r = sum(clean) / n
    variance = sum((r - mean_r) ** 2 for r in clean) / max(n - 1, 1)
    volatility = math.sqrt(max(variance, 0.0))
    window = min(5, n)
    recent = clean[-window:]
    recent_mean = sum(recent) / window
    trend_strength = recent_mean / max(volatility, 1e-8)
    if n >= 2:
        pairs = [(clean[i], clean[i + 1]) for i in range(n - 1)]
        num = sum((a - mean_r) * (b - mean_r) for a, b in pairs)
        denom = sum((r - mean_r) ** 2 for r in clean)
        lag1_autocorr = num / max(denom, 1e-15)
        mean_reversion = max(-1.0, min(1.0, -lag1_autocorr))
    else:
        mean_reversion = 0.0
    short_window = min(10, n)
    short_clean = clean[-short_window:]
    short_mean = sum(short_clean) / len(short_clean)
    short_var = sum((r - short_mean) ** 2 for r in short_clean) / max(len(short_clean) - 1, 1)
    short_vol = math.sqrt(max(short_var, 0.0))
    full_vol = max(volatility, 1e-8)
    stress_raw = (short_vol / full_vol) - 1.0
    stress = max(0.0, min(1.0, stress_raw * 0.5 + 0.5))
    momentum = max(-1.0, min(1.0, recent_mean / max(full_vol, 1e-8)))
    liquidity = 1.0 - stress
    return {
        "volatility":     volatility,
        "trend_strength": trend_strength,
        "MEAN_REVERSION": mean_reversion,
        "stress":         stress,
        "momentum":       momentum,
        "liquidity":      liquidity,
    }


# ---------------------------------------------------------------------------
# Internal helpers (unchanged from v1.1.0)
# ---------------------------------------------------------------------------

def x__extract_regime_features__mutmut_169(returns_history: list) -> dict:
    clean = [r if math.isfinite(r) else 0.0 for r in returns_history]
    n = len(clean)
    mean_r = sum(clean) / n
    variance = sum((r - mean_r) ** 2 for r in clean) / max(n - 1, 1)
    volatility = math.sqrt(max(variance, 0.0))
    window = min(5, n)
    recent = clean[-window:]
    recent_mean = sum(recent) / window
    trend_strength = recent_mean / max(volatility, 1e-8)
    if n >= 2:
        pairs = [(clean[i], clean[i + 1]) for i in range(n - 1)]
        num = sum((a - mean_r) * (b - mean_r) for a, b in pairs)
        denom = sum((r - mean_r) ** 2 for r in clean)
        lag1_autocorr = num / max(denom, 1e-15)
        mean_reversion = max(-1.0, min(1.0, -lag1_autocorr))
    else:
        mean_reversion = 0.0
    short_window = min(10, n)
    short_clean = clean[-short_window:]
    short_mean = sum(short_clean) / len(short_clean)
    short_var = sum((r - short_mean) ** 2 for r in short_clean) / max(len(short_clean) - 1, 1)
    short_vol = math.sqrt(max(short_var, 0.0))
    full_vol = max(volatility, 1e-8)
    stress_raw = (short_vol / full_vol) - 1.0
    stress = max(0.0, min(1.0, stress_raw * 0.5 + 0.5))
    momentum = max(-1.0, min(1.0, recent_mean / max(full_vol, 1e-8)))
    liquidity = 1.0 - stress
    return {
        "volatility":     volatility,
        "trend_strength": trend_strength,
        "mean_reversion": mean_reversion,
        "XXstressXX":         stress,
        "momentum":       momentum,
        "liquidity":      liquidity,
    }


# ---------------------------------------------------------------------------
# Internal helpers (unchanged from v1.1.0)
# ---------------------------------------------------------------------------

def x__extract_regime_features__mutmut_170(returns_history: list) -> dict:
    clean = [r if math.isfinite(r) else 0.0 for r in returns_history]
    n = len(clean)
    mean_r = sum(clean) / n
    variance = sum((r - mean_r) ** 2 for r in clean) / max(n - 1, 1)
    volatility = math.sqrt(max(variance, 0.0))
    window = min(5, n)
    recent = clean[-window:]
    recent_mean = sum(recent) / window
    trend_strength = recent_mean / max(volatility, 1e-8)
    if n >= 2:
        pairs = [(clean[i], clean[i + 1]) for i in range(n - 1)]
        num = sum((a - mean_r) * (b - mean_r) for a, b in pairs)
        denom = sum((r - mean_r) ** 2 for r in clean)
        lag1_autocorr = num / max(denom, 1e-15)
        mean_reversion = max(-1.0, min(1.0, -lag1_autocorr))
    else:
        mean_reversion = 0.0
    short_window = min(10, n)
    short_clean = clean[-short_window:]
    short_mean = sum(short_clean) / len(short_clean)
    short_var = sum((r - short_mean) ** 2 for r in short_clean) / max(len(short_clean) - 1, 1)
    short_vol = math.sqrt(max(short_var, 0.0))
    full_vol = max(volatility, 1e-8)
    stress_raw = (short_vol / full_vol) - 1.0
    stress = max(0.0, min(1.0, stress_raw * 0.5 + 0.5))
    momentum = max(-1.0, min(1.0, recent_mean / max(full_vol, 1e-8)))
    liquidity = 1.0 - stress
    return {
        "volatility":     volatility,
        "trend_strength": trend_strength,
        "mean_reversion": mean_reversion,
        "STRESS":         stress,
        "momentum":       momentum,
        "liquidity":      liquidity,
    }


# ---------------------------------------------------------------------------
# Internal helpers (unchanged from v1.1.0)
# ---------------------------------------------------------------------------

def x__extract_regime_features__mutmut_171(returns_history: list) -> dict:
    clean = [r if math.isfinite(r) else 0.0 for r in returns_history]
    n = len(clean)
    mean_r = sum(clean) / n
    variance = sum((r - mean_r) ** 2 for r in clean) / max(n - 1, 1)
    volatility = math.sqrt(max(variance, 0.0))
    window = min(5, n)
    recent = clean[-window:]
    recent_mean = sum(recent) / window
    trend_strength = recent_mean / max(volatility, 1e-8)
    if n >= 2:
        pairs = [(clean[i], clean[i + 1]) for i in range(n - 1)]
        num = sum((a - mean_r) * (b - mean_r) for a, b in pairs)
        denom = sum((r - mean_r) ** 2 for r in clean)
        lag1_autocorr = num / max(denom, 1e-15)
        mean_reversion = max(-1.0, min(1.0, -lag1_autocorr))
    else:
        mean_reversion = 0.0
    short_window = min(10, n)
    short_clean = clean[-short_window:]
    short_mean = sum(short_clean) / len(short_clean)
    short_var = sum((r - short_mean) ** 2 for r in short_clean) / max(len(short_clean) - 1, 1)
    short_vol = math.sqrt(max(short_var, 0.0))
    full_vol = max(volatility, 1e-8)
    stress_raw = (short_vol / full_vol) - 1.0
    stress = max(0.0, min(1.0, stress_raw * 0.5 + 0.5))
    momentum = max(-1.0, min(1.0, recent_mean / max(full_vol, 1e-8)))
    liquidity = 1.0 - stress
    return {
        "volatility":     volatility,
        "trend_strength": trend_strength,
        "mean_reversion": mean_reversion,
        "stress":         stress,
        "XXmomentumXX":       momentum,
        "liquidity":      liquidity,
    }


# ---------------------------------------------------------------------------
# Internal helpers (unchanged from v1.1.0)
# ---------------------------------------------------------------------------

def x__extract_regime_features__mutmut_172(returns_history: list) -> dict:
    clean = [r if math.isfinite(r) else 0.0 for r in returns_history]
    n = len(clean)
    mean_r = sum(clean) / n
    variance = sum((r - mean_r) ** 2 for r in clean) / max(n - 1, 1)
    volatility = math.sqrt(max(variance, 0.0))
    window = min(5, n)
    recent = clean[-window:]
    recent_mean = sum(recent) / window
    trend_strength = recent_mean / max(volatility, 1e-8)
    if n >= 2:
        pairs = [(clean[i], clean[i + 1]) for i in range(n - 1)]
        num = sum((a - mean_r) * (b - mean_r) for a, b in pairs)
        denom = sum((r - mean_r) ** 2 for r in clean)
        lag1_autocorr = num / max(denom, 1e-15)
        mean_reversion = max(-1.0, min(1.0, -lag1_autocorr))
    else:
        mean_reversion = 0.0
    short_window = min(10, n)
    short_clean = clean[-short_window:]
    short_mean = sum(short_clean) / len(short_clean)
    short_var = sum((r - short_mean) ** 2 for r in short_clean) / max(len(short_clean) - 1, 1)
    short_vol = math.sqrt(max(short_var, 0.0))
    full_vol = max(volatility, 1e-8)
    stress_raw = (short_vol / full_vol) - 1.0
    stress = max(0.0, min(1.0, stress_raw * 0.5 + 0.5))
    momentum = max(-1.0, min(1.0, recent_mean / max(full_vol, 1e-8)))
    liquidity = 1.0 - stress
    return {
        "volatility":     volatility,
        "trend_strength": trend_strength,
        "mean_reversion": mean_reversion,
        "stress":         stress,
        "MOMENTUM":       momentum,
        "liquidity":      liquidity,
    }


# ---------------------------------------------------------------------------
# Internal helpers (unchanged from v1.1.0)
# ---------------------------------------------------------------------------

def x__extract_regime_features__mutmut_173(returns_history: list) -> dict:
    clean = [r if math.isfinite(r) else 0.0 for r in returns_history]
    n = len(clean)
    mean_r = sum(clean) / n
    variance = sum((r - mean_r) ** 2 for r in clean) / max(n - 1, 1)
    volatility = math.sqrt(max(variance, 0.0))
    window = min(5, n)
    recent = clean[-window:]
    recent_mean = sum(recent) / window
    trend_strength = recent_mean / max(volatility, 1e-8)
    if n >= 2:
        pairs = [(clean[i], clean[i + 1]) for i in range(n - 1)]
        num = sum((a - mean_r) * (b - mean_r) for a, b in pairs)
        denom = sum((r - mean_r) ** 2 for r in clean)
        lag1_autocorr = num / max(denom, 1e-15)
        mean_reversion = max(-1.0, min(1.0, -lag1_autocorr))
    else:
        mean_reversion = 0.0
    short_window = min(10, n)
    short_clean = clean[-short_window:]
    short_mean = sum(short_clean) / len(short_clean)
    short_var = sum((r - short_mean) ** 2 for r in short_clean) / max(len(short_clean) - 1, 1)
    short_vol = math.sqrt(max(short_var, 0.0))
    full_vol = max(volatility, 1e-8)
    stress_raw = (short_vol / full_vol) - 1.0
    stress = max(0.0, min(1.0, stress_raw * 0.5 + 0.5))
    momentum = max(-1.0, min(1.0, recent_mean / max(full_vol, 1e-8)))
    liquidity = 1.0 - stress
    return {
        "volatility":     volatility,
        "trend_strength": trend_strength,
        "mean_reversion": mean_reversion,
        "stress":         stress,
        "momentum":       momentum,
        "XXliquidityXX":      liquidity,
    }


# ---------------------------------------------------------------------------
# Internal helpers (unchanged from v1.1.0)
# ---------------------------------------------------------------------------

def x__extract_regime_features__mutmut_174(returns_history: list) -> dict:
    clean = [r if math.isfinite(r) else 0.0 for r in returns_history]
    n = len(clean)
    mean_r = sum(clean) / n
    variance = sum((r - mean_r) ** 2 for r in clean) / max(n - 1, 1)
    volatility = math.sqrt(max(variance, 0.0))
    window = min(5, n)
    recent = clean[-window:]
    recent_mean = sum(recent) / window
    trend_strength = recent_mean / max(volatility, 1e-8)
    if n >= 2:
        pairs = [(clean[i], clean[i + 1]) for i in range(n - 1)]
        num = sum((a - mean_r) * (b - mean_r) for a, b in pairs)
        denom = sum((r - mean_r) ** 2 for r in clean)
        lag1_autocorr = num / max(denom, 1e-15)
        mean_reversion = max(-1.0, min(1.0, -lag1_autocorr))
    else:
        mean_reversion = 0.0
    short_window = min(10, n)
    short_clean = clean[-short_window:]
    short_mean = sum(short_clean) / len(short_clean)
    short_var = sum((r - short_mean) ** 2 for r in short_clean) / max(len(short_clean) - 1, 1)
    short_vol = math.sqrt(max(short_var, 0.0))
    full_vol = max(volatility, 1e-8)
    stress_raw = (short_vol / full_vol) - 1.0
    stress = max(0.0, min(1.0, stress_raw * 0.5 + 0.5))
    momentum = max(-1.0, min(1.0, recent_mean / max(full_vol, 1e-8)))
    liquidity = 1.0 - stress
    return {
        "volatility":     volatility,
        "trend_strength": trend_strength,
        "mean_reversion": mean_reversion,
        "stress":         stress,
        "momentum":       momentum,
        "LIQUIDITY":      liquidity,
    }

x__extract_regime_features__mutmut_mutants : ClassVar[MutantDict] = { # type: ignore
'x__extract_regime_features__mutmut_1': x__extract_regime_features__mutmut_1, 
    'x__extract_regime_features__mutmut_2': x__extract_regime_features__mutmut_2, 
    'x__extract_regime_features__mutmut_3': x__extract_regime_features__mutmut_3, 
    'x__extract_regime_features__mutmut_4': x__extract_regime_features__mutmut_4, 
    'x__extract_regime_features__mutmut_5': x__extract_regime_features__mutmut_5, 
    'x__extract_regime_features__mutmut_6': x__extract_regime_features__mutmut_6, 
    'x__extract_regime_features__mutmut_7': x__extract_regime_features__mutmut_7, 
    'x__extract_regime_features__mutmut_8': x__extract_regime_features__mutmut_8, 
    'x__extract_regime_features__mutmut_9': x__extract_regime_features__mutmut_9, 
    'x__extract_regime_features__mutmut_10': x__extract_regime_features__mutmut_10, 
    'x__extract_regime_features__mutmut_11': x__extract_regime_features__mutmut_11, 
    'x__extract_regime_features__mutmut_12': x__extract_regime_features__mutmut_12, 
    'x__extract_regime_features__mutmut_13': x__extract_regime_features__mutmut_13, 
    'x__extract_regime_features__mutmut_14': x__extract_regime_features__mutmut_14, 
    'x__extract_regime_features__mutmut_15': x__extract_regime_features__mutmut_15, 
    'x__extract_regime_features__mutmut_16': x__extract_regime_features__mutmut_16, 
    'x__extract_regime_features__mutmut_17': x__extract_regime_features__mutmut_17, 
    'x__extract_regime_features__mutmut_18': x__extract_regime_features__mutmut_18, 
    'x__extract_regime_features__mutmut_19': x__extract_regime_features__mutmut_19, 
    'x__extract_regime_features__mutmut_20': x__extract_regime_features__mutmut_20, 
    'x__extract_regime_features__mutmut_21': x__extract_regime_features__mutmut_21, 
    'x__extract_regime_features__mutmut_22': x__extract_regime_features__mutmut_22, 
    'x__extract_regime_features__mutmut_23': x__extract_regime_features__mutmut_23, 
    'x__extract_regime_features__mutmut_24': x__extract_regime_features__mutmut_24, 
    'x__extract_regime_features__mutmut_25': x__extract_regime_features__mutmut_25, 
    'x__extract_regime_features__mutmut_26': x__extract_regime_features__mutmut_26, 
    'x__extract_regime_features__mutmut_27': x__extract_regime_features__mutmut_27, 
    'x__extract_regime_features__mutmut_28': x__extract_regime_features__mutmut_28, 
    'x__extract_regime_features__mutmut_29': x__extract_regime_features__mutmut_29, 
    'x__extract_regime_features__mutmut_30': x__extract_regime_features__mutmut_30, 
    'x__extract_regime_features__mutmut_31': x__extract_regime_features__mutmut_31, 
    'x__extract_regime_features__mutmut_32': x__extract_regime_features__mutmut_32, 
    'x__extract_regime_features__mutmut_33': x__extract_regime_features__mutmut_33, 
    'x__extract_regime_features__mutmut_34': x__extract_regime_features__mutmut_34, 
    'x__extract_regime_features__mutmut_35': x__extract_regime_features__mutmut_35, 
    'x__extract_regime_features__mutmut_36': x__extract_regime_features__mutmut_36, 
    'x__extract_regime_features__mutmut_37': x__extract_regime_features__mutmut_37, 
    'x__extract_regime_features__mutmut_38': x__extract_regime_features__mutmut_38, 
    'x__extract_regime_features__mutmut_39': x__extract_regime_features__mutmut_39, 
    'x__extract_regime_features__mutmut_40': x__extract_regime_features__mutmut_40, 
    'x__extract_regime_features__mutmut_41': x__extract_regime_features__mutmut_41, 
    'x__extract_regime_features__mutmut_42': x__extract_regime_features__mutmut_42, 
    'x__extract_regime_features__mutmut_43': x__extract_regime_features__mutmut_43, 
    'x__extract_regime_features__mutmut_44': x__extract_regime_features__mutmut_44, 
    'x__extract_regime_features__mutmut_45': x__extract_regime_features__mutmut_45, 
    'x__extract_regime_features__mutmut_46': x__extract_regime_features__mutmut_46, 
    'x__extract_regime_features__mutmut_47': x__extract_regime_features__mutmut_47, 
    'x__extract_regime_features__mutmut_48': x__extract_regime_features__mutmut_48, 
    'x__extract_regime_features__mutmut_49': x__extract_regime_features__mutmut_49, 
    'x__extract_regime_features__mutmut_50': x__extract_regime_features__mutmut_50, 
    'x__extract_regime_features__mutmut_51': x__extract_regime_features__mutmut_51, 
    'x__extract_regime_features__mutmut_52': x__extract_regime_features__mutmut_52, 
    'x__extract_regime_features__mutmut_53': x__extract_regime_features__mutmut_53, 
    'x__extract_regime_features__mutmut_54': x__extract_regime_features__mutmut_54, 
    'x__extract_regime_features__mutmut_55': x__extract_regime_features__mutmut_55, 
    'x__extract_regime_features__mutmut_56': x__extract_regime_features__mutmut_56, 
    'x__extract_regime_features__mutmut_57': x__extract_regime_features__mutmut_57, 
    'x__extract_regime_features__mutmut_58': x__extract_regime_features__mutmut_58, 
    'x__extract_regime_features__mutmut_59': x__extract_regime_features__mutmut_59, 
    'x__extract_regime_features__mutmut_60': x__extract_regime_features__mutmut_60, 
    'x__extract_regime_features__mutmut_61': x__extract_regime_features__mutmut_61, 
    'x__extract_regime_features__mutmut_62': x__extract_regime_features__mutmut_62, 
    'x__extract_regime_features__mutmut_63': x__extract_regime_features__mutmut_63, 
    'x__extract_regime_features__mutmut_64': x__extract_regime_features__mutmut_64, 
    'x__extract_regime_features__mutmut_65': x__extract_regime_features__mutmut_65, 
    'x__extract_regime_features__mutmut_66': x__extract_regime_features__mutmut_66, 
    'x__extract_regime_features__mutmut_67': x__extract_regime_features__mutmut_67, 
    'x__extract_regime_features__mutmut_68': x__extract_regime_features__mutmut_68, 
    'x__extract_regime_features__mutmut_69': x__extract_regime_features__mutmut_69, 
    'x__extract_regime_features__mutmut_70': x__extract_regime_features__mutmut_70, 
    'x__extract_regime_features__mutmut_71': x__extract_regime_features__mutmut_71, 
    'x__extract_regime_features__mutmut_72': x__extract_regime_features__mutmut_72, 
    'x__extract_regime_features__mutmut_73': x__extract_regime_features__mutmut_73, 
    'x__extract_regime_features__mutmut_74': x__extract_regime_features__mutmut_74, 
    'x__extract_regime_features__mutmut_75': x__extract_regime_features__mutmut_75, 
    'x__extract_regime_features__mutmut_76': x__extract_regime_features__mutmut_76, 
    'x__extract_regime_features__mutmut_77': x__extract_regime_features__mutmut_77, 
    'x__extract_regime_features__mutmut_78': x__extract_regime_features__mutmut_78, 
    'x__extract_regime_features__mutmut_79': x__extract_regime_features__mutmut_79, 
    'x__extract_regime_features__mutmut_80': x__extract_regime_features__mutmut_80, 
    'x__extract_regime_features__mutmut_81': x__extract_regime_features__mutmut_81, 
    'x__extract_regime_features__mutmut_82': x__extract_regime_features__mutmut_82, 
    'x__extract_regime_features__mutmut_83': x__extract_regime_features__mutmut_83, 
    'x__extract_regime_features__mutmut_84': x__extract_regime_features__mutmut_84, 
    'x__extract_regime_features__mutmut_85': x__extract_regime_features__mutmut_85, 
    'x__extract_regime_features__mutmut_86': x__extract_regime_features__mutmut_86, 
    'x__extract_regime_features__mutmut_87': x__extract_regime_features__mutmut_87, 
    'x__extract_regime_features__mutmut_88': x__extract_regime_features__mutmut_88, 
    'x__extract_regime_features__mutmut_89': x__extract_regime_features__mutmut_89, 
    'x__extract_regime_features__mutmut_90': x__extract_regime_features__mutmut_90, 
    'x__extract_regime_features__mutmut_91': x__extract_regime_features__mutmut_91, 
    'x__extract_regime_features__mutmut_92': x__extract_regime_features__mutmut_92, 
    'x__extract_regime_features__mutmut_93': x__extract_regime_features__mutmut_93, 
    'x__extract_regime_features__mutmut_94': x__extract_regime_features__mutmut_94, 
    'x__extract_regime_features__mutmut_95': x__extract_regime_features__mutmut_95, 
    'x__extract_regime_features__mutmut_96': x__extract_regime_features__mutmut_96, 
    'x__extract_regime_features__mutmut_97': x__extract_regime_features__mutmut_97, 
    'x__extract_regime_features__mutmut_98': x__extract_regime_features__mutmut_98, 
    'x__extract_regime_features__mutmut_99': x__extract_regime_features__mutmut_99, 
    'x__extract_regime_features__mutmut_100': x__extract_regime_features__mutmut_100, 
    'x__extract_regime_features__mutmut_101': x__extract_regime_features__mutmut_101, 
    'x__extract_regime_features__mutmut_102': x__extract_regime_features__mutmut_102, 
    'x__extract_regime_features__mutmut_103': x__extract_regime_features__mutmut_103, 
    'x__extract_regime_features__mutmut_104': x__extract_regime_features__mutmut_104, 
    'x__extract_regime_features__mutmut_105': x__extract_regime_features__mutmut_105, 
    'x__extract_regime_features__mutmut_106': x__extract_regime_features__mutmut_106, 
    'x__extract_regime_features__mutmut_107': x__extract_regime_features__mutmut_107, 
    'x__extract_regime_features__mutmut_108': x__extract_regime_features__mutmut_108, 
    'x__extract_regime_features__mutmut_109': x__extract_regime_features__mutmut_109, 
    'x__extract_regime_features__mutmut_110': x__extract_regime_features__mutmut_110, 
    'x__extract_regime_features__mutmut_111': x__extract_regime_features__mutmut_111, 
    'x__extract_regime_features__mutmut_112': x__extract_regime_features__mutmut_112, 
    'x__extract_regime_features__mutmut_113': x__extract_regime_features__mutmut_113, 
    'x__extract_regime_features__mutmut_114': x__extract_regime_features__mutmut_114, 
    'x__extract_regime_features__mutmut_115': x__extract_regime_features__mutmut_115, 
    'x__extract_regime_features__mutmut_116': x__extract_regime_features__mutmut_116, 
    'x__extract_regime_features__mutmut_117': x__extract_regime_features__mutmut_117, 
    'x__extract_regime_features__mutmut_118': x__extract_regime_features__mutmut_118, 
    'x__extract_regime_features__mutmut_119': x__extract_regime_features__mutmut_119, 
    'x__extract_regime_features__mutmut_120': x__extract_regime_features__mutmut_120, 
    'x__extract_regime_features__mutmut_121': x__extract_regime_features__mutmut_121, 
    'x__extract_regime_features__mutmut_122': x__extract_regime_features__mutmut_122, 
    'x__extract_regime_features__mutmut_123': x__extract_regime_features__mutmut_123, 
    'x__extract_regime_features__mutmut_124': x__extract_regime_features__mutmut_124, 
    'x__extract_regime_features__mutmut_125': x__extract_regime_features__mutmut_125, 
    'x__extract_regime_features__mutmut_126': x__extract_regime_features__mutmut_126, 
    'x__extract_regime_features__mutmut_127': x__extract_regime_features__mutmut_127, 
    'x__extract_regime_features__mutmut_128': x__extract_regime_features__mutmut_128, 
    'x__extract_regime_features__mutmut_129': x__extract_regime_features__mutmut_129, 
    'x__extract_regime_features__mutmut_130': x__extract_regime_features__mutmut_130, 
    'x__extract_regime_features__mutmut_131': x__extract_regime_features__mutmut_131, 
    'x__extract_regime_features__mutmut_132': x__extract_regime_features__mutmut_132, 
    'x__extract_regime_features__mutmut_133': x__extract_regime_features__mutmut_133, 
    'x__extract_regime_features__mutmut_134': x__extract_regime_features__mutmut_134, 
    'x__extract_regime_features__mutmut_135': x__extract_regime_features__mutmut_135, 
    'x__extract_regime_features__mutmut_136': x__extract_regime_features__mutmut_136, 
    'x__extract_regime_features__mutmut_137': x__extract_regime_features__mutmut_137, 
    'x__extract_regime_features__mutmut_138': x__extract_regime_features__mutmut_138, 
    'x__extract_regime_features__mutmut_139': x__extract_regime_features__mutmut_139, 
    'x__extract_regime_features__mutmut_140': x__extract_regime_features__mutmut_140, 
    'x__extract_regime_features__mutmut_141': x__extract_regime_features__mutmut_141, 
    'x__extract_regime_features__mutmut_142': x__extract_regime_features__mutmut_142, 
    'x__extract_regime_features__mutmut_143': x__extract_regime_features__mutmut_143, 
    'x__extract_regime_features__mutmut_144': x__extract_regime_features__mutmut_144, 
    'x__extract_regime_features__mutmut_145': x__extract_regime_features__mutmut_145, 
    'x__extract_regime_features__mutmut_146': x__extract_regime_features__mutmut_146, 
    'x__extract_regime_features__mutmut_147': x__extract_regime_features__mutmut_147, 
    'x__extract_regime_features__mutmut_148': x__extract_regime_features__mutmut_148, 
    'x__extract_regime_features__mutmut_149': x__extract_regime_features__mutmut_149, 
    'x__extract_regime_features__mutmut_150': x__extract_regime_features__mutmut_150, 
    'x__extract_regime_features__mutmut_151': x__extract_regime_features__mutmut_151, 
    'x__extract_regime_features__mutmut_152': x__extract_regime_features__mutmut_152, 
    'x__extract_regime_features__mutmut_153': x__extract_regime_features__mutmut_153, 
    'x__extract_regime_features__mutmut_154': x__extract_regime_features__mutmut_154, 
    'x__extract_regime_features__mutmut_155': x__extract_regime_features__mutmut_155, 
    'x__extract_regime_features__mutmut_156': x__extract_regime_features__mutmut_156, 
    'x__extract_regime_features__mutmut_157': x__extract_regime_features__mutmut_157, 
    'x__extract_regime_features__mutmut_158': x__extract_regime_features__mutmut_158, 
    'x__extract_regime_features__mutmut_159': x__extract_regime_features__mutmut_159, 
    'x__extract_regime_features__mutmut_160': x__extract_regime_features__mutmut_160, 
    'x__extract_regime_features__mutmut_161': x__extract_regime_features__mutmut_161, 
    'x__extract_regime_features__mutmut_162': x__extract_regime_features__mutmut_162, 
    'x__extract_regime_features__mutmut_163': x__extract_regime_features__mutmut_163, 
    'x__extract_regime_features__mutmut_164': x__extract_regime_features__mutmut_164, 
    'x__extract_regime_features__mutmut_165': x__extract_regime_features__mutmut_165, 
    'x__extract_regime_features__mutmut_166': x__extract_regime_features__mutmut_166, 
    'x__extract_regime_features__mutmut_167': x__extract_regime_features__mutmut_167, 
    'x__extract_regime_features__mutmut_168': x__extract_regime_features__mutmut_168, 
    'x__extract_regime_features__mutmut_169': x__extract_regime_features__mutmut_169, 
    'x__extract_regime_features__mutmut_170': x__extract_regime_features__mutmut_170, 
    'x__extract_regime_features__mutmut_171': x__extract_regime_features__mutmut_171, 
    'x__extract_regime_features__mutmut_172': x__extract_regime_features__mutmut_172, 
    'x__extract_regime_features__mutmut_173': x__extract_regime_features__mutmut_173, 
    'x__extract_regime_features__mutmut_174': x__extract_regime_features__mutmut_174
}
x__extract_regime_features__mutmut_orig.__name__ = 'x__extract_regime_features'


def _build_observation_vector(regime_result, vol_result) -> dict:
    args = [regime_result, vol_result]# type: ignore
    kwargs = {}# type: ignore
    return _mutmut_trampoline(x__build_observation_vector__mutmut_orig, x__build_observation_vector__mutmut_mutants, args, kwargs, None)


def x__build_observation_vector__mutmut_orig(regime_result, vol_result) -> dict:
    stress_ratio = vol_result.volatility / max(vol_result.long_run_volatility, 1e-8)
    stress_obs = max(0.0, min(1.0, (stress_ratio - 1.0) * 0.5 + 0.5))
    stability_obs = 1.0 - stress_obs
    pred_uncertainty_obs = max(0.0, vol_result.variance)
    return {
        "regime":                 int(regime_result.hmm_index),
        "volatility":             vol_result.volatility,
        "stress":                 stress_obs,
        "regime_confidence":      regime_result.confidence,
        "stability":              stability_obs,
        "prediction_uncertainty": pred_uncertainty_obs,
    }


def x__build_observation_vector__mutmut_1(regime_result, vol_result) -> dict:
    stress_ratio = None
    stress_obs = max(0.0, min(1.0, (stress_ratio - 1.0) * 0.5 + 0.5))
    stability_obs = 1.0 - stress_obs
    pred_uncertainty_obs = max(0.0, vol_result.variance)
    return {
        "regime":                 int(regime_result.hmm_index),
        "volatility":             vol_result.volatility,
        "stress":                 stress_obs,
        "regime_confidence":      regime_result.confidence,
        "stability":              stability_obs,
        "prediction_uncertainty": pred_uncertainty_obs,
    }


def x__build_observation_vector__mutmut_2(regime_result, vol_result) -> dict:
    stress_ratio = vol_result.volatility * max(vol_result.long_run_volatility, 1e-8)
    stress_obs = max(0.0, min(1.0, (stress_ratio - 1.0) * 0.5 + 0.5))
    stability_obs = 1.0 - stress_obs
    pred_uncertainty_obs = max(0.0, vol_result.variance)
    return {
        "regime":                 int(regime_result.hmm_index),
        "volatility":             vol_result.volatility,
        "stress":                 stress_obs,
        "regime_confidence":      regime_result.confidence,
        "stability":              stability_obs,
        "prediction_uncertainty": pred_uncertainty_obs,
    }


def x__build_observation_vector__mutmut_3(regime_result, vol_result) -> dict:
    stress_ratio = vol_result.volatility / max(None, 1e-8)
    stress_obs = max(0.0, min(1.0, (stress_ratio - 1.0) * 0.5 + 0.5))
    stability_obs = 1.0 - stress_obs
    pred_uncertainty_obs = max(0.0, vol_result.variance)
    return {
        "regime":                 int(regime_result.hmm_index),
        "volatility":             vol_result.volatility,
        "stress":                 stress_obs,
        "regime_confidence":      regime_result.confidence,
        "stability":              stability_obs,
        "prediction_uncertainty": pred_uncertainty_obs,
    }


def x__build_observation_vector__mutmut_4(regime_result, vol_result) -> dict:
    stress_ratio = vol_result.volatility / max(vol_result.long_run_volatility, None)
    stress_obs = max(0.0, min(1.0, (stress_ratio - 1.0) * 0.5 + 0.5))
    stability_obs = 1.0 - stress_obs
    pred_uncertainty_obs = max(0.0, vol_result.variance)
    return {
        "regime":                 int(regime_result.hmm_index),
        "volatility":             vol_result.volatility,
        "stress":                 stress_obs,
        "regime_confidence":      regime_result.confidence,
        "stability":              stability_obs,
        "prediction_uncertainty": pred_uncertainty_obs,
    }


def x__build_observation_vector__mutmut_5(regime_result, vol_result) -> dict:
    stress_ratio = vol_result.volatility / max(1e-8)
    stress_obs = max(0.0, min(1.0, (stress_ratio - 1.0) * 0.5 + 0.5))
    stability_obs = 1.0 - stress_obs
    pred_uncertainty_obs = max(0.0, vol_result.variance)
    return {
        "regime":                 int(regime_result.hmm_index),
        "volatility":             vol_result.volatility,
        "stress":                 stress_obs,
        "regime_confidence":      regime_result.confidence,
        "stability":              stability_obs,
        "prediction_uncertainty": pred_uncertainty_obs,
    }


def x__build_observation_vector__mutmut_6(regime_result, vol_result) -> dict:
    stress_ratio = vol_result.volatility / max(vol_result.long_run_volatility, )
    stress_obs = max(0.0, min(1.0, (stress_ratio - 1.0) * 0.5 + 0.5))
    stability_obs = 1.0 - stress_obs
    pred_uncertainty_obs = max(0.0, vol_result.variance)
    return {
        "regime":                 int(regime_result.hmm_index),
        "volatility":             vol_result.volatility,
        "stress":                 stress_obs,
        "regime_confidence":      regime_result.confidence,
        "stability":              stability_obs,
        "prediction_uncertainty": pred_uncertainty_obs,
    }


def x__build_observation_vector__mutmut_7(regime_result, vol_result) -> dict:
    stress_ratio = vol_result.volatility / max(vol_result.long_run_volatility, 1.00000001)
    stress_obs = max(0.0, min(1.0, (stress_ratio - 1.0) * 0.5 + 0.5))
    stability_obs = 1.0 - stress_obs
    pred_uncertainty_obs = max(0.0, vol_result.variance)
    return {
        "regime":                 int(regime_result.hmm_index),
        "volatility":             vol_result.volatility,
        "stress":                 stress_obs,
        "regime_confidence":      regime_result.confidence,
        "stability":              stability_obs,
        "prediction_uncertainty": pred_uncertainty_obs,
    }


def x__build_observation_vector__mutmut_8(regime_result, vol_result) -> dict:
    stress_ratio = vol_result.volatility / max(vol_result.long_run_volatility, 1e-8)
    stress_obs = None
    stability_obs = 1.0 - stress_obs
    pred_uncertainty_obs = max(0.0, vol_result.variance)
    return {
        "regime":                 int(regime_result.hmm_index),
        "volatility":             vol_result.volatility,
        "stress":                 stress_obs,
        "regime_confidence":      regime_result.confidence,
        "stability":              stability_obs,
        "prediction_uncertainty": pred_uncertainty_obs,
    }


def x__build_observation_vector__mutmut_9(regime_result, vol_result) -> dict:
    stress_ratio = vol_result.volatility / max(vol_result.long_run_volatility, 1e-8)
    stress_obs = max(None, min(1.0, (stress_ratio - 1.0) * 0.5 + 0.5))
    stability_obs = 1.0 - stress_obs
    pred_uncertainty_obs = max(0.0, vol_result.variance)
    return {
        "regime":                 int(regime_result.hmm_index),
        "volatility":             vol_result.volatility,
        "stress":                 stress_obs,
        "regime_confidence":      regime_result.confidence,
        "stability":              stability_obs,
        "prediction_uncertainty": pred_uncertainty_obs,
    }


def x__build_observation_vector__mutmut_10(regime_result, vol_result) -> dict:
    stress_ratio = vol_result.volatility / max(vol_result.long_run_volatility, 1e-8)
    stress_obs = max(0.0, None)
    stability_obs = 1.0 - stress_obs
    pred_uncertainty_obs = max(0.0, vol_result.variance)
    return {
        "regime":                 int(regime_result.hmm_index),
        "volatility":             vol_result.volatility,
        "stress":                 stress_obs,
        "regime_confidence":      regime_result.confidence,
        "stability":              stability_obs,
        "prediction_uncertainty": pred_uncertainty_obs,
    }


def x__build_observation_vector__mutmut_11(regime_result, vol_result) -> dict:
    stress_ratio = vol_result.volatility / max(vol_result.long_run_volatility, 1e-8)
    stress_obs = max(min(1.0, (stress_ratio - 1.0) * 0.5 + 0.5))
    stability_obs = 1.0 - stress_obs
    pred_uncertainty_obs = max(0.0, vol_result.variance)
    return {
        "regime":                 int(regime_result.hmm_index),
        "volatility":             vol_result.volatility,
        "stress":                 stress_obs,
        "regime_confidence":      regime_result.confidence,
        "stability":              stability_obs,
        "prediction_uncertainty": pred_uncertainty_obs,
    }


def x__build_observation_vector__mutmut_12(regime_result, vol_result) -> dict:
    stress_ratio = vol_result.volatility / max(vol_result.long_run_volatility, 1e-8)
    stress_obs = max(0.0, )
    stability_obs = 1.0 - stress_obs
    pred_uncertainty_obs = max(0.0, vol_result.variance)
    return {
        "regime":                 int(regime_result.hmm_index),
        "volatility":             vol_result.volatility,
        "stress":                 stress_obs,
        "regime_confidence":      regime_result.confidence,
        "stability":              stability_obs,
        "prediction_uncertainty": pred_uncertainty_obs,
    }


def x__build_observation_vector__mutmut_13(regime_result, vol_result) -> dict:
    stress_ratio = vol_result.volatility / max(vol_result.long_run_volatility, 1e-8)
    stress_obs = max(1.0, min(1.0, (stress_ratio - 1.0) * 0.5 + 0.5))
    stability_obs = 1.0 - stress_obs
    pred_uncertainty_obs = max(0.0, vol_result.variance)
    return {
        "regime":                 int(regime_result.hmm_index),
        "volatility":             vol_result.volatility,
        "stress":                 stress_obs,
        "regime_confidence":      regime_result.confidence,
        "stability":              stability_obs,
        "prediction_uncertainty": pred_uncertainty_obs,
    }


def x__build_observation_vector__mutmut_14(regime_result, vol_result) -> dict:
    stress_ratio = vol_result.volatility / max(vol_result.long_run_volatility, 1e-8)
    stress_obs = max(0.0, min(None, (stress_ratio - 1.0) * 0.5 + 0.5))
    stability_obs = 1.0 - stress_obs
    pred_uncertainty_obs = max(0.0, vol_result.variance)
    return {
        "regime":                 int(regime_result.hmm_index),
        "volatility":             vol_result.volatility,
        "stress":                 stress_obs,
        "regime_confidence":      regime_result.confidence,
        "stability":              stability_obs,
        "prediction_uncertainty": pred_uncertainty_obs,
    }


def x__build_observation_vector__mutmut_15(regime_result, vol_result) -> dict:
    stress_ratio = vol_result.volatility / max(vol_result.long_run_volatility, 1e-8)
    stress_obs = max(0.0, min(1.0, None))
    stability_obs = 1.0 - stress_obs
    pred_uncertainty_obs = max(0.0, vol_result.variance)
    return {
        "regime":                 int(regime_result.hmm_index),
        "volatility":             vol_result.volatility,
        "stress":                 stress_obs,
        "regime_confidence":      regime_result.confidence,
        "stability":              stability_obs,
        "prediction_uncertainty": pred_uncertainty_obs,
    }


def x__build_observation_vector__mutmut_16(regime_result, vol_result) -> dict:
    stress_ratio = vol_result.volatility / max(vol_result.long_run_volatility, 1e-8)
    stress_obs = max(0.0, min((stress_ratio - 1.0) * 0.5 + 0.5))
    stability_obs = 1.0 - stress_obs
    pred_uncertainty_obs = max(0.0, vol_result.variance)
    return {
        "regime":                 int(regime_result.hmm_index),
        "volatility":             vol_result.volatility,
        "stress":                 stress_obs,
        "regime_confidence":      regime_result.confidence,
        "stability":              stability_obs,
        "prediction_uncertainty": pred_uncertainty_obs,
    }


def x__build_observation_vector__mutmut_17(regime_result, vol_result) -> dict:
    stress_ratio = vol_result.volatility / max(vol_result.long_run_volatility, 1e-8)
    stress_obs = max(0.0, min(1.0, ))
    stability_obs = 1.0 - stress_obs
    pred_uncertainty_obs = max(0.0, vol_result.variance)
    return {
        "regime":                 int(regime_result.hmm_index),
        "volatility":             vol_result.volatility,
        "stress":                 stress_obs,
        "regime_confidence":      regime_result.confidence,
        "stability":              stability_obs,
        "prediction_uncertainty": pred_uncertainty_obs,
    }


def x__build_observation_vector__mutmut_18(regime_result, vol_result) -> dict:
    stress_ratio = vol_result.volatility / max(vol_result.long_run_volatility, 1e-8)
    stress_obs = max(0.0, min(2.0, (stress_ratio - 1.0) * 0.5 + 0.5))
    stability_obs = 1.0 - stress_obs
    pred_uncertainty_obs = max(0.0, vol_result.variance)
    return {
        "regime":                 int(regime_result.hmm_index),
        "volatility":             vol_result.volatility,
        "stress":                 stress_obs,
        "regime_confidence":      regime_result.confidence,
        "stability":              stability_obs,
        "prediction_uncertainty": pred_uncertainty_obs,
    }


def x__build_observation_vector__mutmut_19(regime_result, vol_result) -> dict:
    stress_ratio = vol_result.volatility / max(vol_result.long_run_volatility, 1e-8)
    stress_obs = max(0.0, min(1.0, (stress_ratio - 1.0) * 0.5 - 0.5))
    stability_obs = 1.0 - stress_obs
    pred_uncertainty_obs = max(0.0, vol_result.variance)
    return {
        "regime":                 int(regime_result.hmm_index),
        "volatility":             vol_result.volatility,
        "stress":                 stress_obs,
        "regime_confidence":      regime_result.confidence,
        "stability":              stability_obs,
        "prediction_uncertainty": pred_uncertainty_obs,
    }


def x__build_observation_vector__mutmut_20(regime_result, vol_result) -> dict:
    stress_ratio = vol_result.volatility / max(vol_result.long_run_volatility, 1e-8)
    stress_obs = max(0.0, min(1.0, (stress_ratio - 1.0) / 0.5 + 0.5))
    stability_obs = 1.0 - stress_obs
    pred_uncertainty_obs = max(0.0, vol_result.variance)
    return {
        "regime":                 int(regime_result.hmm_index),
        "volatility":             vol_result.volatility,
        "stress":                 stress_obs,
        "regime_confidence":      regime_result.confidence,
        "stability":              stability_obs,
        "prediction_uncertainty": pred_uncertainty_obs,
    }


def x__build_observation_vector__mutmut_21(regime_result, vol_result) -> dict:
    stress_ratio = vol_result.volatility / max(vol_result.long_run_volatility, 1e-8)
    stress_obs = max(0.0, min(1.0, (stress_ratio + 1.0) * 0.5 + 0.5))
    stability_obs = 1.0 - stress_obs
    pred_uncertainty_obs = max(0.0, vol_result.variance)
    return {
        "regime":                 int(regime_result.hmm_index),
        "volatility":             vol_result.volatility,
        "stress":                 stress_obs,
        "regime_confidence":      regime_result.confidence,
        "stability":              stability_obs,
        "prediction_uncertainty": pred_uncertainty_obs,
    }


def x__build_observation_vector__mutmut_22(regime_result, vol_result) -> dict:
    stress_ratio = vol_result.volatility / max(vol_result.long_run_volatility, 1e-8)
    stress_obs = max(0.0, min(1.0, (stress_ratio - 2.0) * 0.5 + 0.5))
    stability_obs = 1.0 - stress_obs
    pred_uncertainty_obs = max(0.0, vol_result.variance)
    return {
        "regime":                 int(regime_result.hmm_index),
        "volatility":             vol_result.volatility,
        "stress":                 stress_obs,
        "regime_confidence":      regime_result.confidence,
        "stability":              stability_obs,
        "prediction_uncertainty": pred_uncertainty_obs,
    }


def x__build_observation_vector__mutmut_23(regime_result, vol_result) -> dict:
    stress_ratio = vol_result.volatility / max(vol_result.long_run_volatility, 1e-8)
    stress_obs = max(0.0, min(1.0, (stress_ratio - 1.0) * 1.5 + 0.5))
    stability_obs = 1.0 - stress_obs
    pred_uncertainty_obs = max(0.0, vol_result.variance)
    return {
        "regime":                 int(regime_result.hmm_index),
        "volatility":             vol_result.volatility,
        "stress":                 stress_obs,
        "regime_confidence":      regime_result.confidence,
        "stability":              stability_obs,
        "prediction_uncertainty": pred_uncertainty_obs,
    }


def x__build_observation_vector__mutmut_24(regime_result, vol_result) -> dict:
    stress_ratio = vol_result.volatility / max(vol_result.long_run_volatility, 1e-8)
    stress_obs = max(0.0, min(1.0, (stress_ratio - 1.0) * 0.5 + 1.5))
    stability_obs = 1.0 - stress_obs
    pred_uncertainty_obs = max(0.0, vol_result.variance)
    return {
        "regime":                 int(regime_result.hmm_index),
        "volatility":             vol_result.volatility,
        "stress":                 stress_obs,
        "regime_confidence":      regime_result.confidence,
        "stability":              stability_obs,
        "prediction_uncertainty": pred_uncertainty_obs,
    }


def x__build_observation_vector__mutmut_25(regime_result, vol_result) -> dict:
    stress_ratio = vol_result.volatility / max(vol_result.long_run_volatility, 1e-8)
    stress_obs = max(0.0, min(1.0, (stress_ratio - 1.0) * 0.5 + 0.5))
    stability_obs = None
    pred_uncertainty_obs = max(0.0, vol_result.variance)
    return {
        "regime":                 int(regime_result.hmm_index),
        "volatility":             vol_result.volatility,
        "stress":                 stress_obs,
        "regime_confidence":      regime_result.confidence,
        "stability":              stability_obs,
        "prediction_uncertainty": pred_uncertainty_obs,
    }


def x__build_observation_vector__mutmut_26(regime_result, vol_result) -> dict:
    stress_ratio = vol_result.volatility / max(vol_result.long_run_volatility, 1e-8)
    stress_obs = max(0.0, min(1.0, (stress_ratio - 1.0) * 0.5 + 0.5))
    stability_obs = 1.0 + stress_obs
    pred_uncertainty_obs = max(0.0, vol_result.variance)
    return {
        "regime":                 int(regime_result.hmm_index),
        "volatility":             vol_result.volatility,
        "stress":                 stress_obs,
        "regime_confidence":      regime_result.confidence,
        "stability":              stability_obs,
        "prediction_uncertainty": pred_uncertainty_obs,
    }


def x__build_observation_vector__mutmut_27(regime_result, vol_result) -> dict:
    stress_ratio = vol_result.volatility / max(vol_result.long_run_volatility, 1e-8)
    stress_obs = max(0.0, min(1.0, (stress_ratio - 1.0) * 0.5 + 0.5))
    stability_obs = 2.0 - stress_obs
    pred_uncertainty_obs = max(0.0, vol_result.variance)
    return {
        "regime":                 int(regime_result.hmm_index),
        "volatility":             vol_result.volatility,
        "stress":                 stress_obs,
        "regime_confidence":      regime_result.confidence,
        "stability":              stability_obs,
        "prediction_uncertainty": pred_uncertainty_obs,
    }


def x__build_observation_vector__mutmut_28(regime_result, vol_result) -> dict:
    stress_ratio = vol_result.volatility / max(vol_result.long_run_volatility, 1e-8)
    stress_obs = max(0.0, min(1.0, (stress_ratio - 1.0) * 0.5 + 0.5))
    stability_obs = 1.0 - stress_obs
    pred_uncertainty_obs = None
    return {
        "regime":                 int(regime_result.hmm_index),
        "volatility":             vol_result.volatility,
        "stress":                 stress_obs,
        "regime_confidence":      regime_result.confidence,
        "stability":              stability_obs,
        "prediction_uncertainty": pred_uncertainty_obs,
    }


def x__build_observation_vector__mutmut_29(regime_result, vol_result) -> dict:
    stress_ratio = vol_result.volatility / max(vol_result.long_run_volatility, 1e-8)
    stress_obs = max(0.0, min(1.0, (stress_ratio - 1.0) * 0.5 + 0.5))
    stability_obs = 1.0 - stress_obs
    pred_uncertainty_obs = max(None, vol_result.variance)
    return {
        "regime":                 int(regime_result.hmm_index),
        "volatility":             vol_result.volatility,
        "stress":                 stress_obs,
        "regime_confidence":      regime_result.confidence,
        "stability":              stability_obs,
        "prediction_uncertainty": pred_uncertainty_obs,
    }


def x__build_observation_vector__mutmut_30(regime_result, vol_result) -> dict:
    stress_ratio = vol_result.volatility / max(vol_result.long_run_volatility, 1e-8)
    stress_obs = max(0.0, min(1.0, (stress_ratio - 1.0) * 0.5 + 0.5))
    stability_obs = 1.0 - stress_obs
    pred_uncertainty_obs = max(0.0, None)
    return {
        "regime":                 int(regime_result.hmm_index),
        "volatility":             vol_result.volatility,
        "stress":                 stress_obs,
        "regime_confidence":      regime_result.confidence,
        "stability":              stability_obs,
        "prediction_uncertainty": pred_uncertainty_obs,
    }


def x__build_observation_vector__mutmut_31(regime_result, vol_result) -> dict:
    stress_ratio = vol_result.volatility / max(vol_result.long_run_volatility, 1e-8)
    stress_obs = max(0.0, min(1.0, (stress_ratio - 1.0) * 0.5 + 0.5))
    stability_obs = 1.0 - stress_obs
    pred_uncertainty_obs = max(vol_result.variance)
    return {
        "regime":                 int(regime_result.hmm_index),
        "volatility":             vol_result.volatility,
        "stress":                 stress_obs,
        "regime_confidence":      regime_result.confidence,
        "stability":              stability_obs,
        "prediction_uncertainty": pred_uncertainty_obs,
    }


def x__build_observation_vector__mutmut_32(regime_result, vol_result) -> dict:
    stress_ratio = vol_result.volatility / max(vol_result.long_run_volatility, 1e-8)
    stress_obs = max(0.0, min(1.0, (stress_ratio - 1.0) * 0.5 + 0.5))
    stability_obs = 1.0 - stress_obs
    pred_uncertainty_obs = max(0.0, )
    return {
        "regime":                 int(regime_result.hmm_index),
        "volatility":             vol_result.volatility,
        "stress":                 stress_obs,
        "regime_confidence":      regime_result.confidence,
        "stability":              stability_obs,
        "prediction_uncertainty": pred_uncertainty_obs,
    }


def x__build_observation_vector__mutmut_33(regime_result, vol_result) -> dict:
    stress_ratio = vol_result.volatility / max(vol_result.long_run_volatility, 1e-8)
    stress_obs = max(0.0, min(1.0, (stress_ratio - 1.0) * 0.5 + 0.5))
    stability_obs = 1.0 - stress_obs
    pred_uncertainty_obs = max(1.0, vol_result.variance)
    return {
        "regime":                 int(regime_result.hmm_index),
        "volatility":             vol_result.volatility,
        "stress":                 stress_obs,
        "regime_confidence":      regime_result.confidence,
        "stability":              stability_obs,
        "prediction_uncertainty": pred_uncertainty_obs,
    }


def x__build_observation_vector__mutmut_34(regime_result, vol_result) -> dict:
    stress_ratio = vol_result.volatility / max(vol_result.long_run_volatility, 1e-8)
    stress_obs = max(0.0, min(1.0, (stress_ratio - 1.0) * 0.5 + 0.5))
    stability_obs = 1.0 - stress_obs
    pred_uncertainty_obs = max(0.0, vol_result.variance)
    return {
        "XXregimeXX":                 int(regime_result.hmm_index),
        "volatility":             vol_result.volatility,
        "stress":                 stress_obs,
        "regime_confidence":      regime_result.confidence,
        "stability":              stability_obs,
        "prediction_uncertainty": pred_uncertainty_obs,
    }


def x__build_observation_vector__mutmut_35(regime_result, vol_result) -> dict:
    stress_ratio = vol_result.volatility / max(vol_result.long_run_volatility, 1e-8)
    stress_obs = max(0.0, min(1.0, (stress_ratio - 1.0) * 0.5 + 0.5))
    stability_obs = 1.0 - stress_obs
    pred_uncertainty_obs = max(0.0, vol_result.variance)
    return {
        "REGIME":                 int(regime_result.hmm_index),
        "volatility":             vol_result.volatility,
        "stress":                 stress_obs,
        "regime_confidence":      regime_result.confidence,
        "stability":              stability_obs,
        "prediction_uncertainty": pred_uncertainty_obs,
    }


def x__build_observation_vector__mutmut_36(regime_result, vol_result) -> dict:
    stress_ratio = vol_result.volatility / max(vol_result.long_run_volatility, 1e-8)
    stress_obs = max(0.0, min(1.0, (stress_ratio - 1.0) * 0.5 + 0.5))
    stability_obs = 1.0 - stress_obs
    pred_uncertainty_obs = max(0.0, vol_result.variance)
    return {
        "regime":                 int(None),
        "volatility":             vol_result.volatility,
        "stress":                 stress_obs,
        "regime_confidence":      regime_result.confidence,
        "stability":              stability_obs,
        "prediction_uncertainty": pred_uncertainty_obs,
    }


def x__build_observation_vector__mutmut_37(regime_result, vol_result) -> dict:
    stress_ratio = vol_result.volatility / max(vol_result.long_run_volatility, 1e-8)
    stress_obs = max(0.0, min(1.0, (stress_ratio - 1.0) * 0.5 + 0.5))
    stability_obs = 1.0 - stress_obs
    pred_uncertainty_obs = max(0.0, vol_result.variance)
    return {
        "regime":                 int(regime_result.hmm_index),
        "XXvolatilityXX":             vol_result.volatility,
        "stress":                 stress_obs,
        "regime_confidence":      regime_result.confidence,
        "stability":              stability_obs,
        "prediction_uncertainty": pred_uncertainty_obs,
    }


def x__build_observation_vector__mutmut_38(regime_result, vol_result) -> dict:
    stress_ratio = vol_result.volatility / max(vol_result.long_run_volatility, 1e-8)
    stress_obs = max(0.0, min(1.0, (stress_ratio - 1.0) * 0.5 + 0.5))
    stability_obs = 1.0 - stress_obs
    pred_uncertainty_obs = max(0.0, vol_result.variance)
    return {
        "regime":                 int(regime_result.hmm_index),
        "VOLATILITY":             vol_result.volatility,
        "stress":                 stress_obs,
        "regime_confidence":      regime_result.confidence,
        "stability":              stability_obs,
        "prediction_uncertainty": pred_uncertainty_obs,
    }


def x__build_observation_vector__mutmut_39(regime_result, vol_result) -> dict:
    stress_ratio = vol_result.volatility / max(vol_result.long_run_volatility, 1e-8)
    stress_obs = max(0.0, min(1.0, (stress_ratio - 1.0) * 0.5 + 0.5))
    stability_obs = 1.0 - stress_obs
    pred_uncertainty_obs = max(0.0, vol_result.variance)
    return {
        "regime":                 int(regime_result.hmm_index),
        "volatility":             vol_result.volatility,
        "XXstressXX":                 stress_obs,
        "regime_confidence":      regime_result.confidence,
        "stability":              stability_obs,
        "prediction_uncertainty": pred_uncertainty_obs,
    }


def x__build_observation_vector__mutmut_40(regime_result, vol_result) -> dict:
    stress_ratio = vol_result.volatility / max(vol_result.long_run_volatility, 1e-8)
    stress_obs = max(0.0, min(1.0, (stress_ratio - 1.0) * 0.5 + 0.5))
    stability_obs = 1.0 - stress_obs
    pred_uncertainty_obs = max(0.0, vol_result.variance)
    return {
        "regime":                 int(regime_result.hmm_index),
        "volatility":             vol_result.volatility,
        "STRESS":                 stress_obs,
        "regime_confidence":      regime_result.confidence,
        "stability":              stability_obs,
        "prediction_uncertainty": pred_uncertainty_obs,
    }


def x__build_observation_vector__mutmut_41(regime_result, vol_result) -> dict:
    stress_ratio = vol_result.volatility / max(vol_result.long_run_volatility, 1e-8)
    stress_obs = max(0.0, min(1.0, (stress_ratio - 1.0) * 0.5 + 0.5))
    stability_obs = 1.0 - stress_obs
    pred_uncertainty_obs = max(0.0, vol_result.variance)
    return {
        "regime":                 int(regime_result.hmm_index),
        "volatility":             vol_result.volatility,
        "stress":                 stress_obs,
        "XXregime_confidenceXX":      regime_result.confidence,
        "stability":              stability_obs,
        "prediction_uncertainty": pred_uncertainty_obs,
    }


def x__build_observation_vector__mutmut_42(regime_result, vol_result) -> dict:
    stress_ratio = vol_result.volatility / max(vol_result.long_run_volatility, 1e-8)
    stress_obs = max(0.0, min(1.0, (stress_ratio - 1.0) * 0.5 + 0.5))
    stability_obs = 1.0 - stress_obs
    pred_uncertainty_obs = max(0.0, vol_result.variance)
    return {
        "regime":                 int(regime_result.hmm_index),
        "volatility":             vol_result.volatility,
        "stress":                 stress_obs,
        "REGIME_CONFIDENCE":      regime_result.confidence,
        "stability":              stability_obs,
        "prediction_uncertainty": pred_uncertainty_obs,
    }


def x__build_observation_vector__mutmut_43(regime_result, vol_result) -> dict:
    stress_ratio = vol_result.volatility / max(vol_result.long_run_volatility, 1e-8)
    stress_obs = max(0.0, min(1.0, (stress_ratio - 1.0) * 0.5 + 0.5))
    stability_obs = 1.0 - stress_obs
    pred_uncertainty_obs = max(0.0, vol_result.variance)
    return {
        "regime":                 int(regime_result.hmm_index),
        "volatility":             vol_result.volatility,
        "stress":                 stress_obs,
        "regime_confidence":      regime_result.confidence,
        "XXstabilityXX":              stability_obs,
        "prediction_uncertainty": pred_uncertainty_obs,
    }


def x__build_observation_vector__mutmut_44(regime_result, vol_result) -> dict:
    stress_ratio = vol_result.volatility / max(vol_result.long_run_volatility, 1e-8)
    stress_obs = max(0.0, min(1.0, (stress_ratio - 1.0) * 0.5 + 0.5))
    stability_obs = 1.0 - stress_obs
    pred_uncertainty_obs = max(0.0, vol_result.variance)
    return {
        "regime":                 int(regime_result.hmm_index),
        "volatility":             vol_result.volatility,
        "stress":                 stress_obs,
        "regime_confidence":      regime_result.confidence,
        "STABILITY":              stability_obs,
        "prediction_uncertainty": pred_uncertainty_obs,
    }


def x__build_observation_vector__mutmut_45(regime_result, vol_result) -> dict:
    stress_ratio = vol_result.volatility / max(vol_result.long_run_volatility, 1e-8)
    stress_obs = max(0.0, min(1.0, (stress_ratio - 1.0) * 0.5 + 0.5))
    stability_obs = 1.0 - stress_obs
    pred_uncertainty_obs = max(0.0, vol_result.variance)
    return {
        "regime":                 int(regime_result.hmm_index),
        "volatility":             vol_result.volatility,
        "stress":                 stress_obs,
        "regime_confidence":      regime_result.confidence,
        "stability":              stability_obs,
        "XXprediction_uncertaintyXX": pred_uncertainty_obs,
    }


def x__build_observation_vector__mutmut_46(regime_result, vol_result) -> dict:
    stress_ratio = vol_result.volatility / max(vol_result.long_run_volatility, 1e-8)
    stress_obs = max(0.0, min(1.0, (stress_ratio - 1.0) * 0.5 + 0.5))
    stability_obs = 1.0 - stress_obs
    pred_uncertainty_obs = max(0.0, vol_result.variance)
    return {
        "regime":                 int(regime_result.hmm_index),
        "volatility":             vol_result.volatility,
        "stress":                 stress_obs,
        "regime_confidence":      regime_result.confidence,
        "stability":              stability_obs,
        "PREDICTION_UNCERTAINTY": pred_uncertainty_obs,
    }

x__build_observation_vector__mutmut_mutants : ClassVar[MutantDict] = { # type: ignore
'x__build_observation_vector__mutmut_1': x__build_observation_vector__mutmut_1, 
    'x__build_observation_vector__mutmut_2': x__build_observation_vector__mutmut_2, 
    'x__build_observation_vector__mutmut_3': x__build_observation_vector__mutmut_3, 
    'x__build_observation_vector__mutmut_4': x__build_observation_vector__mutmut_4, 
    'x__build_observation_vector__mutmut_5': x__build_observation_vector__mutmut_5, 
    'x__build_observation_vector__mutmut_6': x__build_observation_vector__mutmut_6, 
    'x__build_observation_vector__mutmut_7': x__build_observation_vector__mutmut_7, 
    'x__build_observation_vector__mutmut_8': x__build_observation_vector__mutmut_8, 
    'x__build_observation_vector__mutmut_9': x__build_observation_vector__mutmut_9, 
    'x__build_observation_vector__mutmut_10': x__build_observation_vector__mutmut_10, 
    'x__build_observation_vector__mutmut_11': x__build_observation_vector__mutmut_11, 
    'x__build_observation_vector__mutmut_12': x__build_observation_vector__mutmut_12, 
    'x__build_observation_vector__mutmut_13': x__build_observation_vector__mutmut_13, 
    'x__build_observation_vector__mutmut_14': x__build_observation_vector__mutmut_14, 
    'x__build_observation_vector__mutmut_15': x__build_observation_vector__mutmut_15, 
    'x__build_observation_vector__mutmut_16': x__build_observation_vector__mutmut_16, 
    'x__build_observation_vector__mutmut_17': x__build_observation_vector__mutmut_17, 
    'x__build_observation_vector__mutmut_18': x__build_observation_vector__mutmut_18, 
    'x__build_observation_vector__mutmut_19': x__build_observation_vector__mutmut_19, 
    'x__build_observation_vector__mutmut_20': x__build_observation_vector__mutmut_20, 
    'x__build_observation_vector__mutmut_21': x__build_observation_vector__mutmut_21, 
    'x__build_observation_vector__mutmut_22': x__build_observation_vector__mutmut_22, 
    'x__build_observation_vector__mutmut_23': x__build_observation_vector__mutmut_23, 
    'x__build_observation_vector__mutmut_24': x__build_observation_vector__mutmut_24, 
    'x__build_observation_vector__mutmut_25': x__build_observation_vector__mutmut_25, 
    'x__build_observation_vector__mutmut_26': x__build_observation_vector__mutmut_26, 
    'x__build_observation_vector__mutmut_27': x__build_observation_vector__mutmut_27, 
    'x__build_observation_vector__mutmut_28': x__build_observation_vector__mutmut_28, 
    'x__build_observation_vector__mutmut_29': x__build_observation_vector__mutmut_29, 
    'x__build_observation_vector__mutmut_30': x__build_observation_vector__mutmut_30, 
    'x__build_observation_vector__mutmut_31': x__build_observation_vector__mutmut_31, 
    'x__build_observation_vector__mutmut_32': x__build_observation_vector__mutmut_32, 
    'x__build_observation_vector__mutmut_33': x__build_observation_vector__mutmut_33, 
    'x__build_observation_vector__mutmut_34': x__build_observation_vector__mutmut_34, 
    'x__build_observation_vector__mutmut_35': x__build_observation_vector__mutmut_35, 
    'x__build_observation_vector__mutmut_36': x__build_observation_vector__mutmut_36, 
    'x__build_observation_vector__mutmut_37': x__build_observation_vector__mutmut_37, 
    'x__build_observation_vector__mutmut_38': x__build_observation_vector__mutmut_38, 
    'x__build_observation_vector__mutmut_39': x__build_observation_vector__mutmut_39, 
    'x__build_observation_vector__mutmut_40': x__build_observation_vector__mutmut_40, 
    'x__build_observation_vector__mutmut_41': x__build_observation_vector__mutmut_41, 
    'x__build_observation_vector__mutmut_42': x__build_observation_vector__mutmut_42, 
    'x__build_observation_vector__mutmut_43': x__build_observation_vector__mutmut_43, 
    'x__build_observation_vector__mutmut_44': x__build_observation_vector__mutmut_44, 
    'x__build_observation_vector__mutmut_45': x__build_observation_vector__mutmut_45, 
    'x__build_observation_vector__mutmut_46': x__build_observation_vector__mutmut_46
}
x__build_observation_vector__mutmut_orig.__name__ = 'x__build_observation_vector'


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def run_full_pipeline(
    returns_history: list,
    current_regime: GlobalRegimeState,
    meta_uncertainty: float,
    total_capital: float,
    asset_prices: dict,
) -> dict:
    args = [returns_history, current_regime, meta_uncertainty, total_capital, asset_prices]# type: ignore
    kwargs = {}# type: ignore
    return _mutmut_trampoline(x_run_full_pipeline__mutmut_orig, x_run_full_pipeline__mutmut_mutants, args, kwargs, None)


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def x_run_full_pipeline__mutmut_orig(
    returns_history: list,
    current_regime: GlobalRegimeState,
    meta_uncertainty: float,
    total_capital: float,
    asset_prices: dict,
) -> dict:
    """
    Full deterministic pipeline from returns history to final positions.

    Step 0: Governance gate (GOV-01 + GOV-05 only).
    Steps 1-11: Unchanged from v1.1.0.

    Raises
    ------
    GovernanceViolationError
        meta_uncertainty out of [0.0, 1.0] or regime not GlobalRegimeState.
    ValueError
        Propagated from RiskEngine (invalid returns_history).
        Propagated from route_exposure_to_positions (invalid capital/prices).
    """
    # ------------------------------------------------------------------
    # Step 0: Governance Gate -- GOV-01 and GOV-05 only
    # ------------------------------------------------------------------

    # GOV-01: meta_uncertainty must be in [0.0, 1.0]
    _meta_invalid = (
        not isinstance(meta_uncertainty, (int, float))
        or not (0.0 <= float(meta_uncertainty) <= 1.0)
    )

    # GOV-05: regime must be a GlobalRegimeState instance
    _regime_invalid = not isinstance(current_regime, GlobalRegimeState)

    if _meta_invalid or _regime_invalid:
        # Build a minimal result via validate_pipeline_config using safe
        # stand-in values for parameters owned by downstream modules.
        _safe_capital = total_capital if (
            isinstance(total_capital, (int, float)) and float(total_capital) > 0
        ) else 1.0
        _safe_regime = current_regime if isinstance(
            current_regime, GlobalRegimeState
        ) else GlobalRegimeState.UNKNOWN
        _safe_meta = meta_uncertainty if (
            isinstance(meta_uncertainty, (int, float))
            and 0.0 <= float(meta_uncertainty) <= 1.0
        ) else 0.5

        _gov_result = validate_pipeline_config(
            meta_uncertainty=_safe_meta if not _meta_invalid else meta_uncertainty,
            initial_capital=_safe_capital,
            window=20,
            step=1,
            regime=_safe_regime,
            periods_per_year=252,
        )
        # Only raise for the rules we gate on
        _gated_rules = {"GOV-01", "GOV-05"}
        _gated = [v for v in _gov_result.blocking_violations if v.rule_id in _gated_rules]
        # Also run with the actual bad value so the error message is accurate
        _real_result = validate_pipeline_config(
            meta_uncertainty=meta_uncertainty if isinstance(meta_uncertainty, (int, float)) else 999,
            initial_capital=_safe_capital,
            window=20,
            step=1,
            regime=current_regime,
            periods_per_year=252,
        )
        _real_gated = [v for v in _real_result.blocking_violations if v.rule_id in _gated_rules]
        if _real_gated:
            raise GovernanceViolationError(_real_result)

    # ------------------------------------------------------------------
    # Step 1: Instantiate all components fresh per call
    # ------------------------------------------------------------------
    engine: RiskEngine = RiskEngine()
    regime_detector: RegimeDetector = RegimeDetector()
    vol_tracker: VolatilityTracker = VolatilityTracker()
    state_estimator: StateEstimator = StateEstimator()

    # ------------------------------------------------------------------
    # Steps 2-7: State pipeline
    # ------------------------------------------------------------------
    if len(returns_history) > 0:
        features: dict = _extract_regime_features(returns_history)
        regime_result = regime_detector.detect_regime(features)
        vol_result = vol_tracker.estimate_volatility(returns_history)
        previous_state: LatentState = LatentState.default()
        predicted_state: LatentState = state_estimator.predict(previous_state)
        observation: dict = _build_observation_vector(regime_result, vol_result)
        _latent_state: LatentState = state_estimator.update(predicted_state, observation)

    # ------------------------------------------------------------------
    # Step 8: Risk assessment
    # ------------------------------------------------------------------
    risk_output = engine.assess(
        returns_history=returns_history,
        current_regime=current_regime,
        meta_uncertainty=meta_uncertainty,
    )

    # ------------------------------------------------------------------
    # Steps 9-11: Exposure -> positions -> return
    # ------------------------------------------------------------------
    exposure_weight: float = risk_output.exposure_weight
    positions: dict = route_exposure_to_positions(
        total_capital=total_capital,
        exposure_fraction=exposure_weight,
        asset_prices=asset_prices,
    )
    return positions


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def x_run_full_pipeline__mutmut_1(
    returns_history: list,
    current_regime: GlobalRegimeState,
    meta_uncertainty: float,
    total_capital: float,
    asset_prices: dict,
) -> dict:
    """
    Full deterministic pipeline from returns history to final positions.

    Step 0: Governance gate (GOV-01 + GOV-05 only).
    Steps 1-11: Unchanged from v1.1.0.

    Raises
    ------
    GovernanceViolationError
        meta_uncertainty out of [0.0, 1.0] or regime not GlobalRegimeState.
    ValueError
        Propagated from RiskEngine (invalid returns_history).
        Propagated from route_exposure_to_positions (invalid capital/prices).
    """
    # ------------------------------------------------------------------
    # Step 0: Governance Gate -- GOV-01 and GOV-05 only
    # ------------------------------------------------------------------

    # GOV-01: meta_uncertainty must be in [0.0, 1.0]
    _meta_invalid = None

    # GOV-05: regime must be a GlobalRegimeState instance
    _regime_invalid = not isinstance(current_regime, GlobalRegimeState)

    if _meta_invalid or _regime_invalid:
        # Build a minimal result via validate_pipeline_config using safe
        # stand-in values for parameters owned by downstream modules.
        _safe_capital = total_capital if (
            isinstance(total_capital, (int, float)) and float(total_capital) > 0
        ) else 1.0
        _safe_regime = current_regime if isinstance(
            current_regime, GlobalRegimeState
        ) else GlobalRegimeState.UNKNOWN
        _safe_meta = meta_uncertainty if (
            isinstance(meta_uncertainty, (int, float))
            and 0.0 <= float(meta_uncertainty) <= 1.0
        ) else 0.5

        _gov_result = validate_pipeline_config(
            meta_uncertainty=_safe_meta if not _meta_invalid else meta_uncertainty,
            initial_capital=_safe_capital,
            window=20,
            step=1,
            regime=_safe_regime,
            periods_per_year=252,
        )
        # Only raise for the rules we gate on
        _gated_rules = {"GOV-01", "GOV-05"}
        _gated = [v for v in _gov_result.blocking_violations if v.rule_id in _gated_rules]
        # Also run with the actual bad value so the error message is accurate
        _real_result = validate_pipeline_config(
            meta_uncertainty=meta_uncertainty if isinstance(meta_uncertainty, (int, float)) else 999,
            initial_capital=_safe_capital,
            window=20,
            step=1,
            regime=current_regime,
            periods_per_year=252,
        )
        _real_gated = [v for v in _real_result.blocking_violations if v.rule_id in _gated_rules]
        if _real_gated:
            raise GovernanceViolationError(_real_result)

    # ------------------------------------------------------------------
    # Step 1: Instantiate all components fresh per call
    # ------------------------------------------------------------------
    engine: RiskEngine = RiskEngine()
    regime_detector: RegimeDetector = RegimeDetector()
    vol_tracker: VolatilityTracker = VolatilityTracker()
    state_estimator: StateEstimator = StateEstimator()

    # ------------------------------------------------------------------
    # Steps 2-7: State pipeline
    # ------------------------------------------------------------------
    if len(returns_history) > 0:
        features: dict = _extract_regime_features(returns_history)
        regime_result = regime_detector.detect_regime(features)
        vol_result = vol_tracker.estimate_volatility(returns_history)
        previous_state: LatentState = LatentState.default()
        predicted_state: LatentState = state_estimator.predict(previous_state)
        observation: dict = _build_observation_vector(regime_result, vol_result)
        _latent_state: LatentState = state_estimator.update(predicted_state, observation)

    # ------------------------------------------------------------------
    # Step 8: Risk assessment
    # ------------------------------------------------------------------
    risk_output = engine.assess(
        returns_history=returns_history,
        current_regime=current_regime,
        meta_uncertainty=meta_uncertainty,
    )

    # ------------------------------------------------------------------
    # Steps 9-11: Exposure -> positions -> return
    # ------------------------------------------------------------------
    exposure_weight: float = risk_output.exposure_weight
    positions: dict = route_exposure_to_positions(
        total_capital=total_capital,
        exposure_fraction=exposure_weight,
        asset_prices=asset_prices,
    )
    return positions


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def x_run_full_pipeline__mutmut_2(
    returns_history: list,
    current_regime: GlobalRegimeState,
    meta_uncertainty: float,
    total_capital: float,
    asset_prices: dict,
) -> dict:
    """
    Full deterministic pipeline from returns history to final positions.

    Step 0: Governance gate (GOV-01 + GOV-05 only).
    Steps 1-11: Unchanged from v1.1.0.

    Raises
    ------
    GovernanceViolationError
        meta_uncertainty out of [0.0, 1.0] or regime not GlobalRegimeState.
    ValueError
        Propagated from RiskEngine (invalid returns_history).
        Propagated from route_exposure_to_positions (invalid capital/prices).
    """
    # ------------------------------------------------------------------
    # Step 0: Governance Gate -- GOV-01 and GOV-05 only
    # ------------------------------------------------------------------

    # GOV-01: meta_uncertainty must be in [0.0, 1.0]
    _meta_invalid = (
        not isinstance(meta_uncertainty, (int, float)) and not (0.0 <= float(meta_uncertainty) <= 1.0)
    )

    # GOV-05: regime must be a GlobalRegimeState instance
    _regime_invalid = not isinstance(current_regime, GlobalRegimeState)

    if _meta_invalid or _regime_invalid:
        # Build a minimal result via validate_pipeline_config using safe
        # stand-in values for parameters owned by downstream modules.
        _safe_capital = total_capital if (
            isinstance(total_capital, (int, float)) and float(total_capital) > 0
        ) else 1.0
        _safe_regime = current_regime if isinstance(
            current_regime, GlobalRegimeState
        ) else GlobalRegimeState.UNKNOWN
        _safe_meta = meta_uncertainty if (
            isinstance(meta_uncertainty, (int, float))
            and 0.0 <= float(meta_uncertainty) <= 1.0
        ) else 0.5

        _gov_result = validate_pipeline_config(
            meta_uncertainty=_safe_meta if not _meta_invalid else meta_uncertainty,
            initial_capital=_safe_capital,
            window=20,
            step=1,
            regime=_safe_regime,
            periods_per_year=252,
        )
        # Only raise for the rules we gate on
        _gated_rules = {"GOV-01", "GOV-05"}
        _gated = [v for v in _gov_result.blocking_violations if v.rule_id in _gated_rules]
        # Also run with the actual bad value so the error message is accurate
        _real_result = validate_pipeline_config(
            meta_uncertainty=meta_uncertainty if isinstance(meta_uncertainty, (int, float)) else 999,
            initial_capital=_safe_capital,
            window=20,
            step=1,
            regime=current_regime,
            periods_per_year=252,
        )
        _real_gated = [v for v in _real_result.blocking_violations if v.rule_id in _gated_rules]
        if _real_gated:
            raise GovernanceViolationError(_real_result)

    # ------------------------------------------------------------------
    # Step 1: Instantiate all components fresh per call
    # ------------------------------------------------------------------
    engine: RiskEngine = RiskEngine()
    regime_detector: RegimeDetector = RegimeDetector()
    vol_tracker: VolatilityTracker = VolatilityTracker()
    state_estimator: StateEstimator = StateEstimator()

    # ------------------------------------------------------------------
    # Steps 2-7: State pipeline
    # ------------------------------------------------------------------
    if len(returns_history) > 0:
        features: dict = _extract_regime_features(returns_history)
        regime_result = regime_detector.detect_regime(features)
        vol_result = vol_tracker.estimate_volatility(returns_history)
        previous_state: LatentState = LatentState.default()
        predicted_state: LatentState = state_estimator.predict(previous_state)
        observation: dict = _build_observation_vector(regime_result, vol_result)
        _latent_state: LatentState = state_estimator.update(predicted_state, observation)

    # ------------------------------------------------------------------
    # Step 8: Risk assessment
    # ------------------------------------------------------------------
    risk_output = engine.assess(
        returns_history=returns_history,
        current_regime=current_regime,
        meta_uncertainty=meta_uncertainty,
    )

    # ------------------------------------------------------------------
    # Steps 9-11: Exposure -> positions -> return
    # ------------------------------------------------------------------
    exposure_weight: float = risk_output.exposure_weight
    positions: dict = route_exposure_to_positions(
        total_capital=total_capital,
        exposure_fraction=exposure_weight,
        asset_prices=asset_prices,
    )
    return positions


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def x_run_full_pipeline__mutmut_3(
    returns_history: list,
    current_regime: GlobalRegimeState,
    meta_uncertainty: float,
    total_capital: float,
    asset_prices: dict,
) -> dict:
    """
    Full deterministic pipeline from returns history to final positions.

    Step 0: Governance gate (GOV-01 + GOV-05 only).
    Steps 1-11: Unchanged from v1.1.0.

    Raises
    ------
    GovernanceViolationError
        meta_uncertainty out of [0.0, 1.0] or regime not GlobalRegimeState.
    ValueError
        Propagated from RiskEngine (invalid returns_history).
        Propagated from route_exposure_to_positions (invalid capital/prices).
    """
    # ------------------------------------------------------------------
    # Step 0: Governance Gate -- GOV-01 and GOV-05 only
    # ------------------------------------------------------------------

    # GOV-01: meta_uncertainty must be in [0.0, 1.0]
    _meta_invalid = (
        isinstance(meta_uncertainty, (int, float))
        or not (0.0 <= float(meta_uncertainty) <= 1.0)
    )

    # GOV-05: regime must be a GlobalRegimeState instance
    _regime_invalid = not isinstance(current_regime, GlobalRegimeState)

    if _meta_invalid or _regime_invalid:
        # Build a minimal result via validate_pipeline_config using safe
        # stand-in values for parameters owned by downstream modules.
        _safe_capital = total_capital if (
            isinstance(total_capital, (int, float)) and float(total_capital) > 0
        ) else 1.0
        _safe_regime = current_regime if isinstance(
            current_regime, GlobalRegimeState
        ) else GlobalRegimeState.UNKNOWN
        _safe_meta = meta_uncertainty if (
            isinstance(meta_uncertainty, (int, float))
            and 0.0 <= float(meta_uncertainty) <= 1.0
        ) else 0.5

        _gov_result = validate_pipeline_config(
            meta_uncertainty=_safe_meta if not _meta_invalid else meta_uncertainty,
            initial_capital=_safe_capital,
            window=20,
            step=1,
            regime=_safe_regime,
            periods_per_year=252,
        )
        # Only raise for the rules we gate on
        _gated_rules = {"GOV-01", "GOV-05"}
        _gated = [v for v in _gov_result.blocking_violations if v.rule_id in _gated_rules]
        # Also run with the actual bad value so the error message is accurate
        _real_result = validate_pipeline_config(
            meta_uncertainty=meta_uncertainty if isinstance(meta_uncertainty, (int, float)) else 999,
            initial_capital=_safe_capital,
            window=20,
            step=1,
            regime=current_regime,
            periods_per_year=252,
        )
        _real_gated = [v for v in _real_result.blocking_violations if v.rule_id in _gated_rules]
        if _real_gated:
            raise GovernanceViolationError(_real_result)

    # ------------------------------------------------------------------
    # Step 1: Instantiate all components fresh per call
    # ------------------------------------------------------------------
    engine: RiskEngine = RiskEngine()
    regime_detector: RegimeDetector = RegimeDetector()
    vol_tracker: VolatilityTracker = VolatilityTracker()
    state_estimator: StateEstimator = StateEstimator()

    # ------------------------------------------------------------------
    # Steps 2-7: State pipeline
    # ------------------------------------------------------------------
    if len(returns_history) > 0:
        features: dict = _extract_regime_features(returns_history)
        regime_result = regime_detector.detect_regime(features)
        vol_result = vol_tracker.estimate_volatility(returns_history)
        previous_state: LatentState = LatentState.default()
        predicted_state: LatentState = state_estimator.predict(previous_state)
        observation: dict = _build_observation_vector(regime_result, vol_result)
        _latent_state: LatentState = state_estimator.update(predicted_state, observation)

    # ------------------------------------------------------------------
    # Step 8: Risk assessment
    # ------------------------------------------------------------------
    risk_output = engine.assess(
        returns_history=returns_history,
        current_regime=current_regime,
        meta_uncertainty=meta_uncertainty,
    )

    # ------------------------------------------------------------------
    # Steps 9-11: Exposure -> positions -> return
    # ------------------------------------------------------------------
    exposure_weight: float = risk_output.exposure_weight
    positions: dict = route_exposure_to_positions(
        total_capital=total_capital,
        exposure_fraction=exposure_weight,
        asset_prices=asset_prices,
    )
    return positions


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def x_run_full_pipeline__mutmut_4(
    returns_history: list,
    current_regime: GlobalRegimeState,
    meta_uncertainty: float,
    total_capital: float,
    asset_prices: dict,
) -> dict:
    """
    Full deterministic pipeline from returns history to final positions.

    Step 0: Governance gate (GOV-01 + GOV-05 only).
    Steps 1-11: Unchanged from v1.1.0.

    Raises
    ------
    GovernanceViolationError
        meta_uncertainty out of [0.0, 1.0] or regime not GlobalRegimeState.
    ValueError
        Propagated from RiskEngine (invalid returns_history).
        Propagated from route_exposure_to_positions (invalid capital/prices).
    """
    # ------------------------------------------------------------------
    # Step 0: Governance Gate -- GOV-01 and GOV-05 only
    # ------------------------------------------------------------------

    # GOV-01: meta_uncertainty must be in [0.0, 1.0]
    _meta_invalid = (
        not isinstance(meta_uncertainty, (int, float))
        or (0.0 <= float(meta_uncertainty) <= 1.0)
    )

    # GOV-05: regime must be a GlobalRegimeState instance
    _regime_invalid = not isinstance(current_regime, GlobalRegimeState)

    if _meta_invalid or _regime_invalid:
        # Build a minimal result via validate_pipeline_config using safe
        # stand-in values for parameters owned by downstream modules.
        _safe_capital = total_capital if (
            isinstance(total_capital, (int, float)) and float(total_capital) > 0
        ) else 1.0
        _safe_regime = current_regime if isinstance(
            current_regime, GlobalRegimeState
        ) else GlobalRegimeState.UNKNOWN
        _safe_meta = meta_uncertainty if (
            isinstance(meta_uncertainty, (int, float))
            and 0.0 <= float(meta_uncertainty) <= 1.0
        ) else 0.5

        _gov_result = validate_pipeline_config(
            meta_uncertainty=_safe_meta if not _meta_invalid else meta_uncertainty,
            initial_capital=_safe_capital,
            window=20,
            step=1,
            regime=_safe_regime,
            periods_per_year=252,
        )
        # Only raise for the rules we gate on
        _gated_rules = {"GOV-01", "GOV-05"}
        _gated = [v for v in _gov_result.blocking_violations if v.rule_id in _gated_rules]
        # Also run with the actual bad value so the error message is accurate
        _real_result = validate_pipeline_config(
            meta_uncertainty=meta_uncertainty if isinstance(meta_uncertainty, (int, float)) else 999,
            initial_capital=_safe_capital,
            window=20,
            step=1,
            regime=current_regime,
            periods_per_year=252,
        )
        _real_gated = [v for v in _real_result.blocking_violations if v.rule_id in _gated_rules]
        if _real_gated:
            raise GovernanceViolationError(_real_result)

    # ------------------------------------------------------------------
    # Step 1: Instantiate all components fresh per call
    # ------------------------------------------------------------------
    engine: RiskEngine = RiskEngine()
    regime_detector: RegimeDetector = RegimeDetector()
    vol_tracker: VolatilityTracker = VolatilityTracker()
    state_estimator: StateEstimator = StateEstimator()

    # ------------------------------------------------------------------
    # Steps 2-7: State pipeline
    # ------------------------------------------------------------------
    if len(returns_history) > 0:
        features: dict = _extract_regime_features(returns_history)
        regime_result = regime_detector.detect_regime(features)
        vol_result = vol_tracker.estimate_volatility(returns_history)
        previous_state: LatentState = LatentState.default()
        predicted_state: LatentState = state_estimator.predict(previous_state)
        observation: dict = _build_observation_vector(regime_result, vol_result)
        _latent_state: LatentState = state_estimator.update(predicted_state, observation)

    # ------------------------------------------------------------------
    # Step 8: Risk assessment
    # ------------------------------------------------------------------
    risk_output = engine.assess(
        returns_history=returns_history,
        current_regime=current_regime,
        meta_uncertainty=meta_uncertainty,
    )

    # ------------------------------------------------------------------
    # Steps 9-11: Exposure -> positions -> return
    # ------------------------------------------------------------------
    exposure_weight: float = risk_output.exposure_weight
    positions: dict = route_exposure_to_positions(
        total_capital=total_capital,
        exposure_fraction=exposure_weight,
        asset_prices=asset_prices,
    )
    return positions


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def x_run_full_pipeline__mutmut_5(
    returns_history: list,
    current_regime: GlobalRegimeState,
    meta_uncertainty: float,
    total_capital: float,
    asset_prices: dict,
) -> dict:
    """
    Full deterministic pipeline from returns history to final positions.

    Step 0: Governance gate (GOV-01 + GOV-05 only).
    Steps 1-11: Unchanged from v1.1.0.

    Raises
    ------
    GovernanceViolationError
        meta_uncertainty out of [0.0, 1.0] or regime not GlobalRegimeState.
    ValueError
        Propagated from RiskEngine (invalid returns_history).
        Propagated from route_exposure_to_positions (invalid capital/prices).
    """
    # ------------------------------------------------------------------
    # Step 0: Governance Gate -- GOV-01 and GOV-05 only
    # ------------------------------------------------------------------

    # GOV-01: meta_uncertainty must be in [0.0, 1.0]
    _meta_invalid = (
        not isinstance(meta_uncertainty, (int, float))
        or not (1.0 <= float(meta_uncertainty) <= 1.0)
    )

    # GOV-05: regime must be a GlobalRegimeState instance
    _regime_invalid = not isinstance(current_regime, GlobalRegimeState)

    if _meta_invalid or _regime_invalid:
        # Build a minimal result via validate_pipeline_config using safe
        # stand-in values for parameters owned by downstream modules.
        _safe_capital = total_capital if (
            isinstance(total_capital, (int, float)) and float(total_capital) > 0
        ) else 1.0
        _safe_regime = current_regime if isinstance(
            current_regime, GlobalRegimeState
        ) else GlobalRegimeState.UNKNOWN
        _safe_meta = meta_uncertainty if (
            isinstance(meta_uncertainty, (int, float))
            and 0.0 <= float(meta_uncertainty) <= 1.0
        ) else 0.5

        _gov_result = validate_pipeline_config(
            meta_uncertainty=_safe_meta if not _meta_invalid else meta_uncertainty,
            initial_capital=_safe_capital,
            window=20,
            step=1,
            regime=_safe_regime,
            periods_per_year=252,
        )
        # Only raise for the rules we gate on
        _gated_rules = {"GOV-01", "GOV-05"}
        _gated = [v for v in _gov_result.blocking_violations if v.rule_id in _gated_rules]
        # Also run with the actual bad value so the error message is accurate
        _real_result = validate_pipeline_config(
            meta_uncertainty=meta_uncertainty if isinstance(meta_uncertainty, (int, float)) else 999,
            initial_capital=_safe_capital,
            window=20,
            step=1,
            regime=current_regime,
            periods_per_year=252,
        )
        _real_gated = [v for v in _real_result.blocking_violations if v.rule_id in _gated_rules]
        if _real_gated:
            raise GovernanceViolationError(_real_result)

    # ------------------------------------------------------------------
    # Step 1: Instantiate all components fresh per call
    # ------------------------------------------------------------------
    engine: RiskEngine = RiskEngine()
    regime_detector: RegimeDetector = RegimeDetector()
    vol_tracker: VolatilityTracker = VolatilityTracker()
    state_estimator: StateEstimator = StateEstimator()

    # ------------------------------------------------------------------
    # Steps 2-7: State pipeline
    # ------------------------------------------------------------------
    if len(returns_history) > 0:
        features: dict = _extract_regime_features(returns_history)
        regime_result = regime_detector.detect_regime(features)
        vol_result = vol_tracker.estimate_volatility(returns_history)
        previous_state: LatentState = LatentState.default()
        predicted_state: LatentState = state_estimator.predict(previous_state)
        observation: dict = _build_observation_vector(regime_result, vol_result)
        _latent_state: LatentState = state_estimator.update(predicted_state, observation)

    # ------------------------------------------------------------------
    # Step 8: Risk assessment
    # ------------------------------------------------------------------
    risk_output = engine.assess(
        returns_history=returns_history,
        current_regime=current_regime,
        meta_uncertainty=meta_uncertainty,
    )

    # ------------------------------------------------------------------
    # Steps 9-11: Exposure -> positions -> return
    # ------------------------------------------------------------------
    exposure_weight: float = risk_output.exposure_weight
    positions: dict = route_exposure_to_positions(
        total_capital=total_capital,
        exposure_fraction=exposure_weight,
        asset_prices=asset_prices,
    )
    return positions


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def x_run_full_pipeline__mutmut_6(
    returns_history: list,
    current_regime: GlobalRegimeState,
    meta_uncertainty: float,
    total_capital: float,
    asset_prices: dict,
) -> dict:
    """
    Full deterministic pipeline from returns history to final positions.

    Step 0: Governance gate (GOV-01 + GOV-05 only).
    Steps 1-11: Unchanged from v1.1.0.

    Raises
    ------
    GovernanceViolationError
        meta_uncertainty out of [0.0, 1.0] or regime not GlobalRegimeState.
    ValueError
        Propagated from RiskEngine (invalid returns_history).
        Propagated from route_exposure_to_positions (invalid capital/prices).
    """
    # ------------------------------------------------------------------
    # Step 0: Governance Gate -- GOV-01 and GOV-05 only
    # ------------------------------------------------------------------

    # GOV-01: meta_uncertainty must be in [0.0, 1.0]
    _meta_invalid = (
        not isinstance(meta_uncertainty, (int, float))
        or not (0.0 < float(meta_uncertainty) <= 1.0)
    )

    # GOV-05: regime must be a GlobalRegimeState instance
    _regime_invalid = not isinstance(current_regime, GlobalRegimeState)

    if _meta_invalid or _regime_invalid:
        # Build a minimal result via validate_pipeline_config using safe
        # stand-in values for parameters owned by downstream modules.
        _safe_capital = total_capital if (
            isinstance(total_capital, (int, float)) and float(total_capital) > 0
        ) else 1.0
        _safe_regime = current_regime if isinstance(
            current_regime, GlobalRegimeState
        ) else GlobalRegimeState.UNKNOWN
        _safe_meta = meta_uncertainty if (
            isinstance(meta_uncertainty, (int, float))
            and 0.0 <= float(meta_uncertainty) <= 1.0
        ) else 0.5

        _gov_result = validate_pipeline_config(
            meta_uncertainty=_safe_meta if not _meta_invalid else meta_uncertainty,
            initial_capital=_safe_capital,
            window=20,
            step=1,
            regime=_safe_regime,
            periods_per_year=252,
        )
        # Only raise for the rules we gate on
        _gated_rules = {"GOV-01", "GOV-05"}
        _gated = [v for v in _gov_result.blocking_violations if v.rule_id in _gated_rules]
        # Also run with the actual bad value so the error message is accurate
        _real_result = validate_pipeline_config(
            meta_uncertainty=meta_uncertainty if isinstance(meta_uncertainty, (int, float)) else 999,
            initial_capital=_safe_capital,
            window=20,
            step=1,
            regime=current_regime,
            periods_per_year=252,
        )
        _real_gated = [v for v in _real_result.blocking_violations if v.rule_id in _gated_rules]
        if _real_gated:
            raise GovernanceViolationError(_real_result)

    # ------------------------------------------------------------------
    # Step 1: Instantiate all components fresh per call
    # ------------------------------------------------------------------
    engine: RiskEngine = RiskEngine()
    regime_detector: RegimeDetector = RegimeDetector()
    vol_tracker: VolatilityTracker = VolatilityTracker()
    state_estimator: StateEstimator = StateEstimator()

    # ------------------------------------------------------------------
    # Steps 2-7: State pipeline
    # ------------------------------------------------------------------
    if len(returns_history) > 0:
        features: dict = _extract_regime_features(returns_history)
        regime_result = regime_detector.detect_regime(features)
        vol_result = vol_tracker.estimate_volatility(returns_history)
        previous_state: LatentState = LatentState.default()
        predicted_state: LatentState = state_estimator.predict(previous_state)
        observation: dict = _build_observation_vector(regime_result, vol_result)
        _latent_state: LatentState = state_estimator.update(predicted_state, observation)

    # ------------------------------------------------------------------
    # Step 8: Risk assessment
    # ------------------------------------------------------------------
    risk_output = engine.assess(
        returns_history=returns_history,
        current_regime=current_regime,
        meta_uncertainty=meta_uncertainty,
    )

    # ------------------------------------------------------------------
    # Steps 9-11: Exposure -> positions -> return
    # ------------------------------------------------------------------
    exposure_weight: float = risk_output.exposure_weight
    positions: dict = route_exposure_to_positions(
        total_capital=total_capital,
        exposure_fraction=exposure_weight,
        asset_prices=asset_prices,
    )
    return positions


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def x_run_full_pipeline__mutmut_7(
    returns_history: list,
    current_regime: GlobalRegimeState,
    meta_uncertainty: float,
    total_capital: float,
    asset_prices: dict,
) -> dict:
    """
    Full deterministic pipeline from returns history to final positions.

    Step 0: Governance gate (GOV-01 + GOV-05 only).
    Steps 1-11: Unchanged from v1.1.0.

    Raises
    ------
    GovernanceViolationError
        meta_uncertainty out of [0.0, 1.0] or regime not GlobalRegimeState.
    ValueError
        Propagated from RiskEngine (invalid returns_history).
        Propagated from route_exposure_to_positions (invalid capital/prices).
    """
    # ------------------------------------------------------------------
    # Step 0: Governance Gate -- GOV-01 and GOV-05 only
    # ------------------------------------------------------------------

    # GOV-01: meta_uncertainty must be in [0.0, 1.0]
    _meta_invalid = (
        not isinstance(meta_uncertainty, (int, float))
        or not (0.0 <= float(None) <= 1.0)
    )

    # GOV-05: regime must be a GlobalRegimeState instance
    _regime_invalid = not isinstance(current_regime, GlobalRegimeState)

    if _meta_invalid or _regime_invalid:
        # Build a minimal result via validate_pipeline_config using safe
        # stand-in values for parameters owned by downstream modules.
        _safe_capital = total_capital if (
            isinstance(total_capital, (int, float)) and float(total_capital) > 0
        ) else 1.0
        _safe_regime = current_regime if isinstance(
            current_regime, GlobalRegimeState
        ) else GlobalRegimeState.UNKNOWN
        _safe_meta = meta_uncertainty if (
            isinstance(meta_uncertainty, (int, float))
            and 0.0 <= float(meta_uncertainty) <= 1.0
        ) else 0.5

        _gov_result = validate_pipeline_config(
            meta_uncertainty=_safe_meta if not _meta_invalid else meta_uncertainty,
            initial_capital=_safe_capital,
            window=20,
            step=1,
            regime=_safe_regime,
            periods_per_year=252,
        )
        # Only raise for the rules we gate on
        _gated_rules = {"GOV-01", "GOV-05"}
        _gated = [v for v in _gov_result.blocking_violations if v.rule_id in _gated_rules]
        # Also run with the actual bad value so the error message is accurate
        _real_result = validate_pipeline_config(
            meta_uncertainty=meta_uncertainty if isinstance(meta_uncertainty, (int, float)) else 999,
            initial_capital=_safe_capital,
            window=20,
            step=1,
            regime=current_regime,
            periods_per_year=252,
        )
        _real_gated = [v for v in _real_result.blocking_violations if v.rule_id in _gated_rules]
        if _real_gated:
            raise GovernanceViolationError(_real_result)

    # ------------------------------------------------------------------
    # Step 1: Instantiate all components fresh per call
    # ------------------------------------------------------------------
    engine: RiskEngine = RiskEngine()
    regime_detector: RegimeDetector = RegimeDetector()
    vol_tracker: VolatilityTracker = VolatilityTracker()
    state_estimator: StateEstimator = StateEstimator()

    # ------------------------------------------------------------------
    # Steps 2-7: State pipeline
    # ------------------------------------------------------------------
    if len(returns_history) > 0:
        features: dict = _extract_regime_features(returns_history)
        regime_result = regime_detector.detect_regime(features)
        vol_result = vol_tracker.estimate_volatility(returns_history)
        previous_state: LatentState = LatentState.default()
        predicted_state: LatentState = state_estimator.predict(previous_state)
        observation: dict = _build_observation_vector(regime_result, vol_result)
        _latent_state: LatentState = state_estimator.update(predicted_state, observation)

    # ------------------------------------------------------------------
    # Step 8: Risk assessment
    # ------------------------------------------------------------------
    risk_output = engine.assess(
        returns_history=returns_history,
        current_regime=current_regime,
        meta_uncertainty=meta_uncertainty,
    )

    # ------------------------------------------------------------------
    # Steps 9-11: Exposure -> positions -> return
    # ------------------------------------------------------------------
    exposure_weight: float = risk_output.exposure_weight
    positions: dict = route_exposure_to_positions(
        total_capital=total_capital,
        exposure_fraction=exposure_weight,
        asset_prices=asset_prices,
    )
    return positions


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def x_run_full_pipeline__mutmut_8(
    returns_history: list,
    current_regime: GlobalRegimeState,
    meta_uncertainty: float,
    total_capital: float,
    asset_prices: dict,
) -> dict:
    """
    Full deterministic pipeline from returns history to final positions.

    Step 0: Governance gate (GOV-01 + GOV-05 only).
    Steps 1-11: Unchanged from v1.1.0.

    Raises
    ------
    GovernanceViolationError
        meta_uncertainty out of [0.0, 1.0] or regime not GlobalRegimeState.
    ValueError
        Propagated from RiskEngine (invalid returns_history).
        Propagated from route_exposure_to_positions (invalid capital/prices).
    """
    # ------------------------------------------------------------------
    # Step 0: Governance Gate -- GOV-01 and GOV-05 only
    # ------------------------------------------------------------------

    # GOV-01: meta_uncertainty must be in [0.0, 1.0]
    _meta_invalid = (
        not isinstance(meta_uncertainty, (int, float))
        or not (0.0 <= float(meta_uncertainty) < 1.0)
    )

    # GOV-05: regime must be a GlobalRegimeState instance
    _regime_invalid = not isinstance(current_regime, GlobalRegimeState)

    if _meta_invalid or _regime_invalid:
        # Build a minimal result via validate_pipeline_config using safe
        # stand-in values for parameters owned by downstream modules.
        _safe_capital = total_capital if (
            isinstance(total_capital, (int, float)) and float(total_capital) > 0
        ) else 1.0
        _safe_regime = current_regime if isinstance(
            current_regime, GlobalRegimeState
        ) else GlobalRegimeState.UNKNOWN
        _safe_meta = meta_uncertainty if (
            isinstance(meta_uncertainty, (int, float))
            and 0.0 <= float(meta_uncertainty) <= 1.0
        ) else 0.5

        _gov_result = validate_pipeline_config(
            meta_uncertainty=_safe_meta if not _meta_invalid else meta_uncertainty,
            initial_capital=_safe_capital,
            window=20,
            step=1,
            regime=_safe_regime,
            periods_per_year=252,
        )
        # Only raise for the rules we gate on
        _gated_rules = {"GOV-01", "GOV-05"}
        _gated = [v for v in _gov_result.blocking_violations if v.rule_id in _gated_rules]
        # Also run with the actual bad value so the error message is accurate
        _real_result = validate_pipeline_config(
            meta_uncertainty=meta_uncertainty if isinstance(meta_uncertainty, (int, float)) else 999,
            initial_capital=_safe_capital,
            window=20,
            step=1,
            regime=current_regime,
            periods_per_year=252,
        )
        _real_gated = [v for v in _real_result.blocking_violations if v.rule_id in _gated_rules]
        if _real_gated:
            raise GovernanceViolationError(_real_result)

    # ------------------------------------------------------------------
    # Step 1: Instantiate all components fresh per call
    # ------------------------------------------------------------------
    engine: RiskEngine = RiskEngine()
    regime_detector: RegimeDetector = RegimeDetector()
    vol_tracker: VolatilityTracker = VolatilityTracker()
    state_estimator: StateEstimator = StateEstimator()

    # ------------------------------------------------------------------
    # Steps 2-7: State pipeline
    # ------------------------------------------------------------------
    if len(returns_history) > 0:
        features: dict = _extract_regime_features(returns_history)
        regime_result = regime_detector.detect_regime(features)
        vol_result = vol_tracker.estimate_volatility(returns_history)
        previous_state: LatentState = LatentState.default()
        predicted_state: LatentState = state_estimator.predict(previous_state)
        observation: dict = _build_observation_vector(regime_result, vol_result)
        _latent_state: LatentState = state_estimator.update(predicted_state, observation)

    # ------------------------------------------------------------------
    # Step 8: Risk assessment
    # ------------------------------------------------------------------
    risk_output = engine.assess(
        returns_history=returns_history,
        current_regime=current_regime,
        meta_uncertainty=meta_uncertainty,
    )

    # ------------------------------------------------------------------
    # Steps 9-11: Exposure -> positions -> return
    # ------------------------------------------------------------------
    exposure_weight: float = risk_output.exposure_weight
    positions: dict = route_exposure_to_positions(
        total_capital=total_capital,
        exposure_fraction=exposure_weight,
        asset_prices=asset_prices,
    )
    return positions


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def x_run_full_pipeline__mutmut_9(
    returns_history: list,
    current_regime: GlobalRegimeState,
    meta_uncertainty: float,
    total_capital: float,
    asset_prices: dict,
) -> dict:
    """
    Full deterministic pipeline from returns history to final positions.

    Step 0: Governance gate (GOV-01 + GOV-05 only).
    Steps 1-11: Unchanged from v1.1.0.

    Raises
    ------
    GovernanceViolationError
        meta_uncertainty out of [0.0, 1.0] or regime not GlobalRegimeState.
    ValueError
        Propagated from RiskEngine (invalid returns_history).
        Propagated from route_exposure_to_positions (invalid capital/prices).
    """
    # ------------------------------------------------------------------
    # Step 0: Governance Gate -- GOV-01 and GOV-05 only
    # ------------------------------------------------------------------

    # GOV-01: meta_uncertainty must be in [0.0, 1.0]
    _meta_invalid = (
        not isinstance(meta_uncertainty, (int, float))
        or not (0.0 <= float(meta_uncertainty) <= 2.0)
    )

    # GOV-05: regime must be a GlobalRegimeState instance
    _regime_invalid = not isinstance(current_regime, GlobalRegimeState)

    if _meta_invalid or _regime_invalid:
        # Build a minimal result via validate_pipeline_config using safe
        # stand-in values for parameters owned by downstream modules.
        _safe_capital = total_capital if (
            isinstance(total_capital, (int, float)) and float(total_capital) > 0
        ) else 1.0
        _safe_regime = current_regime if isinstance(
            current_regime, GlobalRegimeState
        ) else GlobalRegimeState.UNKNOWN
        _safe_meta = meta_uncertainty if (
            isinstance(meta_uncertainty, (int, float))
            and 0.0 <= float(meta_uncertainty) <= 1.0
        ) else 0.5

        _gov_result = validate_pipeline_config(
            meta_uncertainty=_safe_meta if not _meta_invalid else meta_uncertainty,
            initial_capital=_safe_capital,
            window=20,
            step=1,
            regime=_safe_regime,
            periods_per_year=252,
        )
        # Only raise for the rules we gate on
        _gated_rules = {"GOV-01", "GOV-05"}
        _gated = [v for v in _gov_result.blocking_violations if v.rule_id in _gated_rules]
        # Also run with the actual bad value so the error message is accurate
        _real_result = validate_pipeline_config(
            meta_uncertainty=meta_uncertainty if isinstance(meta_uncertainty, (int, float)) else 999,
            initial_capital=_safe_capital,
            window=20,
            step=1,
            regime=current_regime,
            periods_per_year=252,
        )
        _real_gated = [v for v in _real_result.blocking_violations if v.rule_id in _gated_rules]
        if _real_gated:
            raise GovernanceViolationError(_real_result)

    # ------------------------------------------------------------------
    # Step 1: Instantiate all components fresh per call
    # ------------------------------------------------------------------
    engine: RiskEngine = RiskEngine()
    regime_detector: RegimeDetector = RegimeDetector()
    vol_tracker: VolatilityTracker = VolatilityTracker()
    state_estimator: StateEstimator = StateEstimator()

    # ------------------------------------------------------------------
    # Steps 2-7: State pipeline
    # ------------------------------------------------------------------
    if len(returns_history) > 0:
        features: dict = _extract_regime_features(returns_history)
        regime_result = regime_detector.detect_regime(features)
        vol_result = vol_tracker.estimate_volatility(returns_history)
        previous_state: LatentState = LatentState.default()
        predicted_state: LatentState = state_estimator.predict(previous_state)
        observation: dict = _build_observation_vector(regime_result, vol_result)
        _latent_state: LatentState = state_estimator.update(predicted_state, observation)

    # ------------------------------------------------------------------
    # Step 8: Risk assessment
    # ------------------------------------------------------------------
    risk_output = engine.assess(
        returns_history=returns_history,
        current_regime=current_regime,
        meta_uncertainty=meta_uncertainty,
    )

    # ------------------------------------------------------------------
    # Steps 9-11: Exposure -> positions -> return
    # ------------------------------------------------------------------
    exposure_weight: float = risk_output.exposure_weight
    positions: dict = route_exposure_to_positions(
        total_capital=total_capital,
        exposure_fraction=exposure_weight,
        asset_prices=asset_prices,
    )
    return positions


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def x_run_full_pipeline__mutmut_10(
    returns_history: list,
    current_regime: GlobalRegimeState,
    meta_uncertainty: float,
    total_capital: float,
    asset_prices: dict,
) -> dict:
    """
    Full deterministic pipeline from returns history to final positions.

    Step 0: Governance gate (GOV-01 + GOV-05 only).
    Steps 1-11: Unchanged from v1.1.0.

    Raises
    ------
    GovernanceViolationError
        meta_uncertainty out of [0.0, 1.0] or regime not GlobalRegimeState.
    ValueError
        Propagated from RiskEngine (invalid returns_history).
        Propagated from route_exposure_to_positions (invalid capital/prices).
    """
    # ------------------------------------------------------------------
    # Step 0: Governance Gate -- GOV-01 and GOV-05 only
    # ------------------------------------------------------------------

    # GOV-01: meta_uncertainty must be in [0.0, 1.0]
    _meta_invalid = (
        not isinstance(meta_uncertainty, (int, float))
        or not (0.0 <= float(meta_uncertainty) <= 1.0)
    )

    # GOV-05: regime must be a GlobalRegimeState instance
    _regime_invalid = None

    if _meta_invalid or _regime_invalid:
        # Build a minimal result via validate_pipeline_config using safe
        # stand-in values for parameters owned by downstream modules.
        _safe_capital = total_capital if (
            isinstance(total_capital, (int, float)) and float(total_capital) > 0
        ) else 1.0
        _safe_regime = current_regime if isinstance(
            current_regime, GlobalRegimeState
        ) else GlobalRegimeState.UNKNOWN
        _safe_meta = meta_uncertainty if (
            isinstance(meta_uncertainty, (int, float))
            and 0.0 <= float(meta_uncertainty) <= 1.0
        ) else 0.5

        _gov_result = validate_pipeline_config(
            meta_uncertainty=_safe_meta if not _meta_invalid else meta_uncertainty,
            initial_capital=_safe_capital,
            window=20,
            step=1,
            regime=_safe_regime,
            periods_per_year=252,
        )
        # Only raise for the rules we gate on
        _gated_rules = {"GOV-01", "GOV-05"}
        _gated = [v for v in _gov_result.blocking_violations if v.rule_id in _gated_rules]
        # Also run with the actual bad value so the error message is accurate
        _real_result = validate_pipeline_config(
            meta_uncertainty=meta_uncertainty if isinstance(meta_uncertainty, (int, float)) else 999,
            initial_capital=_safe_capital,
            window=20,
            step=1,
            regime=current_regime,
            periods_per_year=252,
        )
        _real_gated = [v for v in _real_result.blocking_violations if v.rule_id in _gated_rules]
        if _real_gated:
            raise GovernanceViolationError(_real_result)

    # ------------------------------------------------------------------
    # Step 1: Instantiate all components fresh per call
    # ------------------------------------------------------------------
    engine: RiskEngine = RiskEngine()
    regime_detector: RegimeDetector = RegimeDetector()
    vol_tracker: VolatilityTracker = VolatilityTracker()
    state_estimator: StateEstimator = StateEstimator()

    # ------------------------------------------------------------------
    # Steps 2-7: State pipeline
    # ------------------------------------------------------------------
    if len(returns_history) > 0:
        features: dict = _extract_regime_features(returns_history)
        regime_result = regime_detector.detect_regime(features)
        vol_result = vol_tracker.estimate_volatility(returns_history)
        previous_state: LatentState = LatentState.default()
        predicted_state: LatentState = state_estimator.predict(previous_state)
        observation: dict = _build_observation_vector(regime_result, vol_result)
        _latent_state: LatentState = state_estimator.update(predicted_state, observation)

    # ------------------------------------------------------------------
    # Step 8: Risk assessment
    # ------------------------------------------------------------------
    risk_output = engine.assess(
        returns_history=returns_history,
        current_regime=current_regime,
        meta_uncertainty=meta_uncertainty,
    )

    # ------------------------------------------------------------------
    # Steps 9-11: Exposure -> positions -> return
    # ------------------------------------------------------------------
    exposure_weight: float = risk_output.exposure_weight
    positions: dict = route_exposure_to_positions(
        total_capital=total_capital,
        exposure_fraction=exposure_weight,
        asset_prices=asset_prices,
    )
    return positions


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def x_run_full_pipeline__mutmut_11(
    returns_history: list,
    current_regime: GlobalRegimeState,
    meta_uncertainty: float,
    total_capital: float,
    asset_prices: dict,
) -> dict:
    """
    Full deterministic pipeline from returns history to final positions.

    Step 0: Governance gate (GOV-01 + GOV-05 only).
    Steps 1-11: Unchanged from v1.1.0.

    Raises
    ------
    GovernanceViolationError
        meta_uncertainty out of [0.0, 1.0] or regime not GlobalRegimeState.
    ValueError
        Propagated from RiskEngine (invalid returns_history).
        Propagated from route_exposure_to_positions (invalid capital/prices).
    """
    # ------------------------------------------------------------------
    # Step 0: Governance Gate -- GOV-01 and GOV-05 only
    # ------------------------------------------------------------------

    # GOV-01: meta_uncertainty must be in [0.0, 1.0]
    _meta_invalid = (
        not isinstance(meta_uncertainty, (int, float))
        or not (0.0 <= float(meta_uncertainty) <= 1.0)
    )

    # GOV-05: regime must be a GlobalRegimeState instance
    _regime_invalid = isinstance(current_regime, GlobalRegimeState)

    if _meta_invalid or _regime_invalid:
        # Build a minimal result via validate_pipeline_config using safe
        # stand-in values for parameters owned by downstream modules.
        _safe_capital = total_capital if (
            isinstance(total_capital, (int, float)) and float(total_capital) > 0
        ) else 1.0
        _safe_regime = current_regime if isinstance(
            current_regime, GlobalRegimeState
        ) else GlobalRegimeState.UNKNOWN
        _safe_meta = meta_uncertainty if (
            isinstance(meta_uncertainty, (int, float))
            and 0.0 <= float(meta_uncertainty) <= 1.0
        ) else 0.5

        _gov_result = validate_pipeline_config(
            meta_uncertainty=_safe_meta if not _meta_invalid else meta_uncertainty,
            initial_capital=_safe_capital,
            window=20,
            step=1,
            regime=_safe_regime,
            periods_per_year=252,
        )
        # Only raise for the rules we gate on
        _gated_rules = {"GOV-01", "GOV-05"}
        _gated = [v for v in _gov_result.blocking_violations if v.rule_id in _gated_rules]
        # Also run with the actual bad value so the error message is accurate
        _real_result = validate_pipeline_config(
            meta_uncertainty=meta_uncertainty if isinstance(meta_uncertainty, (int, float)) else 999,
            initial_capital=_safe_capital,
            window=20,
            step=1,
            regime=current_regime,
            periods_per_year=252,
        )
        _real_gated = [v for v in _real_result.blocking_violations if v.rule_id in _gated_rules]
        if _real_gated:
            raise GovernanceViolationError(_real_result)

    # ------------------------------------------------------------------
    # Step 1: Instantiate all components fresh per call
    # ------------------------------------------------------------------
    engine: RiskEngine = RiskEngine()
    regime_detector: RegimeDetector = RegimeDetector()
    vol_tracker: VolatilityTracker = VolatilityTracker()
    state_estimator: StateEstimator = StateEstimator()

    # ------------------------------------------------------------------
    # Steps 2-7: State pipeline
    # ------------------------------------------------------------------
    if len(returns_history) > 0:
        features: dict = _extract_regime_features(returns_history)
        regime_result = regime_detector.detect_regime(features)
        vol_result = vol_tracker.estimate_volatility(returns_history)
        previous_state: LatentState = LatentState.default()
        predicted_state: LatentState = state_estimator.predict(previous_state)
        observation: dict = _build_observation_vector(regime_result, vol_result)
        _latent_state: LatentState = state_estimator.update(predicted_state, observation)

    # ------------------------------------------------------------------
    # Step 8: Risk assessment
    # ------------------------------------------------------------------
    risk_output = engine.assess(
        returns_history=returns_history,
        current_regime=current_regime,
        meta_uncertainty=meta_uncertainty,
    )

    # ------------------------------------------------------------------
    # Steps 9-11: Exposure -> positions -> return
    # ------------------------------------------------------------------
    exposure_weight: float = risk_output.exposure_weight
    positions: dict = route_exposure_to_positions(
        total_capital=total_capital,
        exposure_fraction=exposure_weight,
        asset_prices=asset_prices,
    )
    return positions


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def x_run_full_pipeline__mutmut_12(
    returns_history: list,
    current_regime: GlobalRegimeState,
    meta_uncertainty: float,
    total_capital: float,
    asset_prices: dict,
) -> dict:
    """
    Full deterministic pipeline from returns history to final positions.

    Step 0: Governance gate (GOV-01 + GOV-05 only).
    Steps 1-11: Unchanged from v1.1.0.

    Raises
    ------
    GovernanceViolationError
        meta_uncertainty out of [0.0, 1.0] or regime not GlobalRegimeState.
    ValueError
        Propagated from RiskEngine (invalid returns_history).
        Propagated from route_exposure_to_positions (invalid capital/prices).
    """
    # ------------------------------------------------------------------
    # Step 0: Governance Gate -- GOV-01 and GOV-05 only
    # ------------------------------------------------------------------

    # GOV-01: meta_uncertainty must be in [0.0, 1.0]
    _meta_invalid = (
        not isinstance(meta_uncertainty, (int, float))
        or not (0.0 <= float(meta_uncertainty) <= 1.0)
    )

    # GOV-05: regime must be a GlobalRegimeState instance
    _regime_invalid = not isinstance(current_regime, GlobalRegimeState)

    if _meta_invalid and _regime_invalid:
        # Build a minimal result via validate_pipeline_config using safe
        # stand-in values for parameters owned by downstream modules.
        _safe_capital = total_capital if (
            isinstance(total_capital, (int, float)) and float(total_capital) > 0
        ) else 1.0
        _safe_regime = current_regime if isinstance(
            current_regime, GlobalRegimeState
        ) else GlobalRegimeState.UNKNOWN
        _safe_meta = meta_uncertainty if (
            isinstance(meta_uncertainty, (int, float))
            and 0.0 <= float(meta_uncertainty) <= 1.0
        ) else 0.5

        _gov_result = validate_pipeline_config(
            meta_uncertainty=_safe_meta if not _meta_invalid else meta_uncertainty,
            initial_capital=_safe_capital,
            window=20,
            step=1,
            regime=_safe_regime,
            periods_per_year=252,
        )
        # Only raise for the rules we gate on
        _gated_rules = {"GOV-01", "GOV-05"}
        _gated = [v for v in _gov_result.blocking_violations if v.rule_id in _gated_rules]
        # Also run with the actual bad value so the error message is accurate
        _real_result = validate_pipeline_config(
            meta_uncertainty=meta_uncertainty if isinstance(meta_uncertainty, (int, float)) else 999,
            initial_capital=_safe_capital,
            window=20,
            step=1,
            regime=current_regime,
            periods_per_year=252,
        )
        _real_gated = [v for v in _real_result.blocking_violations if v.rule_id in _gated_rules]
        if _real_gated:
            raise GovernanceViolationError(_real_result)

    # ------------------------------------------------------------------
    # Step 1: Instantiate all components fresh per call
    # ------------------------------------------------------------------
    engine: RiskEngine = RiskEngine()
    regime_detector: RegimeDetector = RegimeDetector()
    vol_tracker: VolatilityTracker = VolatilityTracker()
    state_estimator: StateEstimator = StateEstimator()

    # ------------------------------------------------------------------
    # Steps 2-7: State pipeline
    # ------------------------------------------------------------------
    if len(returns_history) > 0:
        features: dict = _extract_regime_features(returns_history)
        regime_result = regime_detector.detect_regime(features)
        vol_result = vol_tracker.estimate_volatility(returns_history)
        previous_state: LatentState = LatentState.default()
        predicted_state: LatentState = state_estimator.predict(previous_state)
        observation: dict = _build_observation_vector(regime_result, vol_result)
        _latent_state: LatentState = state_estimator.update(predicted_state, observation)

    # ------------------------------------------------------------------
    # Step 8: Risk assessment
    # ------------------------------------------------------------------
    risk_output = engine.assess(
        returns_history=returns_history,
        current_regime=current_regime,
        meta_uncertainty=meta_uncertainty,
    )

    # ------------------------------------------------------------------
    # Steps 9-11: Exposure -> positions -> return
    # ------------------------------------------------------------------
    exposure_weight: float = risk_output.exposure_weight
    positions: dict = route_exposure_to_positions(
        total_capital=total_capital,
        exposure_fraction=exposure_weight,
        asset_prices=asset_prices,
    )
    return positions


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def x_run_full_pipeline__mutmut_13(
    returns_history: list,
    current_regime: GlobalRegimeState,
    meta_uncertainty: float,
    total_capital: float,
    asset_prices: dict,
) -> dict:
    """
    Full deterministic pipeline from returns history to final positions.

    Step 0: Governance gate (GOV-01 + GOV-05 only).
    Steps 1-11: Unchanged from v1.1.0.

    Raises
    ------
    GovernanceViolationError
        meta_uncertainty out of [0.0, 1.0] or regime not GlobalRegimeState.
    ValueError
        Propagated from RiskEngine (invalid returns_history).
        Propagated from route_exposure_to_positions (invalid capital/prices).
    """
    # ------------------------------------------------------------------
    # Step 0: Governance Gate -- GOV-01 and GOV-05 only
    # ------------------------------------------------------------------

    # GOV-01: meta_uncertainty must be in [0.0, 1.0]
    _meta_invalid = (
        not isinstance(meta_uncertainty, (int, float))
        or not (0.0 <= float(meta_uncertainty) <= 1.0)
    )

    # GOV-05: regime must be a GlobalRegimeState instance
    _regime_invalid = not isinstance(current_regime, GlobalRegimeState)

    if _meta_invalid or _regime_invalid:
        # Build a minimal result via validate_pipeline_config using safe
        # stand-in values for parameters owned by downstream modules.
        _safe_capital = None
        _safe_regime = current_regime if isinstance(
            current_regime, GlobalRegimeState
        ) else GlobalRegimeState.UNKNOWN
        _safe_meta = meta_uncertainty if (
            isinstance(meta_uncertainty, (int, float))
            and 0.0 <= float(meta_uncertainty) <= 1.0
        ) else 0.5

        _gov_result = validate_pipeline_config(
            meta_uncertainty=_safe_meta if not _meta_invalid else meta_uncertainty,
            initial_capital=_safe_capital,
            window=20,
            step=1,
            regime=_safe_regime,
            periods_per_year=252,
        )
        # Only raise for the rules we gate on
        _gated_rules = {"GOV-01", "GOV-05"}
        _gated = [v for v in _gov_result.blocking_violations if v.rule_id in _gated_rules]
        # Also run with the actual bad value so the error message is accurate
        _real_result = validate_pipeline_config(
            meta_uncertainty=meta_uncertainty if isinstance(meta_uncertainty, (int, float)) else 999,
            initial_capital=_safe_capital,
            window=20,
            step=1,
            regime=current_regime,
            periods_per_year=252,
        )
        _real_gated = [v for v in _real_result.blocking_violations if v.rule_id in _gated_rules]
        if _real_gated:
            raise GovernanceViolationError(_real_result)

    # ------------------------------------------------------------------
    # Step 1: Instantiate all components fresh per call
    # ------------------------------------------------------------------
    engine: RiskEngine = RiskEngine()
    regime_detector: RegimeDetector = RegimeDetector()
    vol_tracker: VolatilityTracker = VolatilityTracker()
    state_estimator: StateEstimator = StateEstimator()

    # ------------------------------------------------------------------
    # Steps 2-7: State pipeline
    # ------------------------------------------------------------------
    if len(returns_history) > 0:
        features: dict = _extract_regime_features(returns_history)
        regime_result = regime_detector.detect_regime(features)
        vol_result = vol_tracker.estimate_volatility(returns_history)
        previous_state: LatentState = LatentState.default()
        predicted_state: LatentState = state_estimator.predict(previous_state)
        observation: dict = _build_observation_vector(regime_result, vol_result)
        _latent_state: LatentState = state_estimator.update(predicted_state, observation)

    # ------------------------------------------------------------------
    # Step 8: Risk assessment
    # ------------------------------------------------------------------
    risk_output = engine.assess(
        returns_history=returns_history,
        current_regime=current_regime,
        meta_uncertainty=meta_uncertainty,
    )

    # ------------------------------------------------------------------
    # Steps 9-11: Exposure -> positions -> return
    # ------------------------------------------------------------------
    exposure_weight: float = risk_output.exposure_weight
    positions: dict = route_exposure_to_positions(
        total_capital=total_capital,
        exposure_fraction=exposure_weight,
        asset_prices=asset_prices,
    )
    return positions


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def x_run_full_pipeline__mutmut_14(
    returns_history: list,
    current_regime: GlobalRegimeState,
    meta_uncertainty: float,
    total_capital: float,
    asset_prices: dict,
) -> dict:
    """
    Full deterministic pipeline from returns history to final positions.

    Step 0: Governance gate (GOV-01 + GOV-05 only).
    Steps 1-11: Unchanged from v1.1.0.

    Raises
    ------
    GovernanceViolationError
        meta_uncertainty out of [0.0, 1.0] or regime not GlobalRegimeState.
    ValueError
        Propagated from RiskEngine (invalid returns_history).
        Propagated from route_exposure_to_positions (invalid capital/prices).
    """
    # ------------------------------------------------------------------
    # Step 0: Governance Gate -- GOV-01 and GOV-05 only
    # ------------------------------------------------------------------

    # GOV-01: meta_uncertainty must be in [0.0, 1.0]
    _meta_invalid = (
        not isinstance(meta_uncertainty, (int, float))
        or not (0.0 <= float(meta_uncertainty) <= 1.0)
    )

    # GOV-05: regime must be a GlobalRegimeState instance
    _regime_invalid = not isinstance(current_regime, GlobalRegimeState)

    if _meta_invalid or _regime_invalid:
        # Build a minimal result via validate_pipeline_config using safe
        # stand-in values for parameters owned by downstream modules.
        _safe_capital = total_capital if (
            isinstance(total_capital, (int, float)) or float(total_capital) > 0
        ) else 1.0
        _safe_regime = current_regime if isinstance(
            current_regime, GlobalRegimeState
        ) else GlobalRegimeState.UNKNOWN
        _safe_meta = meta_uncertainty if (
            isinstance(meta_uncertainty, (int, float))
            and 0.0 <= float(meta_uncertainty) <= 1.0
        ) else 0.5

        _gov_result = validate_pipeline_config(
            meta_uncertainty=_safe_meta if not _meta_invalid else meta_uncertainty,
            initial_capital=_safe_capital,
            window=20,
            step=1,
            regime=_safe_regime,
            periods_per_year=252,
        )
        # Only raise for the rules we gate on
        _gated_rules = {"GOV-01", "GOV-05"}
        _gated = [v for v in _gov_result.blocking_violations if v.rule_id in _gated_rules]
        # Also run with the actual bad value so the error message is accurate
        _real_result = validate_pipeline_config(
            meta_uncertainty=meta_uncertainty if isinstance(meta_uncertainty, (int, float)) else 999,
            initial_capital=_safe_capital,
            window=20,
            step=1,
            regime=current_regime,
            periods_per_year=252,
        )
        _real_gated = [v for v in _real_result.blocking_violations if v.rule_id in _gated_rules]
        if _real_gated:
            raise GovernanceViolationError(_real_result)

    # ------------------------------------------------------------------
    # Step 1: Instantiate all components fresh per call
    # ------------------------------------------------------------------
    engine: RiskEngine = RiskEngine()
    regime_detector: RegimeDetector = RegimeDetector()
    vol_tracker: VolatilityTracker = VolatilityTracker()
    state_estimator: StateEstimator = StateEstimator()

    # ------------------------------------------------------------------
    # Steps 2-7: State pipeline
    # ------------------------------------------------------------------
    if len(returns_history) > 0:
        features: dict = _extract_regime_features(returns_history)
        regime_result = regime_detector.detect_regime(features)
        vol_result = vol_tracker.estimate_volatility(returns_history)
        previous_state: LatentState = LatentState.default()
        predicted_state: LatentState = state_estimator.predict(previous_state)
        observation: dict = _build_observation_vector(regime_result, vol_result)
        _latent_state: LatentState = state_estimator.update(predicted_state, observation)

    # ------------------------------------------------------------------
    # Step 8: Risk assessment
    # ------------------------------------------------------------------
    risk_output = engine.assess(
        returns_history=returns_history,
        current_regime=current_regime,
        meta_uncertainty=meta_uncertainty,
    )

    # ------------------------------------------------------------------
    # Steps 9-11: Exposure -> positions -> return
    # ------------------------------------------------------------------
    exposure_weight: float = risk_output.exposure_weight
    positions: dict = route_exposure_to_positions(
        total_capital=total_capital,
        exposure_fraction=exposure_weight,
        asset_prices=asset_prices,
    )
    return positions


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def x_run_full_pipeline__mutmut_15(
    returns_history: list,
    current_regime: GlobalRegimeState,
    meta_uncertainty: float,
    total_capital: float,
    asset_prices: dict,
) -> dict:
    """
    Full deterministic pipeline from returns history to final positions.

    Step 0: Governance gate (GOV-01 + GOV-05 only).
    Steps 1-11: Unchanged from v1.1.0.

    Raises
    ------
    GovernanceViolationError
        meta_uncertainty out of [0.0, 1.0] or regime not GlobalRegimeState.
    ValueError
        Propagated from RiskEngine (invalid returns_history).
        Propagated from route_exposure_to_positions (invalid capital/prices).
    """
    # ------------------------------------------------------------------
    # Step 0: Governance Gate -- GOV-01 and GOV-05 only
    # ------------------------------------------------------------------

    # GOV-01: meta_uncertainty must be in [0.0, 1.0]
    _meta_invalid = (
        not isinstance(meta_uncertainty, (int, float))
        or not (0.0 <= float(meta_uncertainty) <= 1.0)
    )

    # GOV-05: regime must be a GlobalRegimeState instance
    _regime_invalid = not isinstance(current_regime, GlobalRegimeState)

    if _meta_invalid or _regime_invalid:
        # Build a minimal result via validate_pipeline_config using safe
        # stand-in values for parameters owned by downstream modules.
        _safe_capital = total_capital if (
            isinstance(total_capital, (int, float)) and float(None) > 0
        ) else 1.0
        _safe_regime = current_regime if isinstance(
            current_regime, GlobalRegimeState
        ) else GlobalRegimeState.UNKNOWN
        _safe_meta = meta_uncertainty if (
            isinstance(meta_uncertainty, (int, float))
            and 0.0 <= float(meta_uncertainty) <= 1.0
        ) else 0.5

        _gov_result = validate_pipeline_config(
            meta_uncertainty=_safe_meta if not _meta_invalid else meta_uncertainty,
            initial_capital=_safe_capital,
            window=20,
            step=1,
            regime=_safe_regime,
            periods_per_year=252,
        )
        # Only raise for the rules we gate on
        _gated_rules = {"GOV-01", "GOV-05"}
        _gated = [v for v in _gov_result.blocking_violations if v.rule_id in _gated_rules]
        # Also run with the actual bad value so the error message is accurate
        _real_result = validate_pipeline_config(
            meta_uncertainty=meta_uncertainty if isinstance(meta_uncertainty, (int, float)) else 999,
            initial_capital=_safe_capital,
            window=20,
            step=1,
            regime=current_regime,
            periods_per_year=252,
        )
        _real_gated = [v for v in _real_result.blocking_violations if v.rule_id in _gated_rules]
        if _real_gated:
            raise GovernanceViolationError(_real_result)

    # ------------------------------------------------------------------
    # Step 1: Instantiate all components fresh per call
    # ------------------------------------------------------------------
    engine: RiskEngine = RiskEngine()
    regime_detector: RegimeDetector = RegimeDetector()
    vol_tracker: VolatilityTracker = VolatilityTracker()
    state_estimator: StateEstimator = StateEstimator()

    # ------------------------------------------------------------------
    # Steps 2-7: State pipeline
    # ------------------------------------------------------------------
    if len(returns_history) > 0:
        features: dict = _extract_regime_features(returns_history)
        regime_result = regime_detector.detect_regime(features)
        vol_result = vol_tracker.estimate_volatility(returns_history)
        previous_state: LatentState = LatentState.default()
        predicted_state: LatentState = state_estimator.predict(previous_state)
        observation: dict = _build_observation_vector(regime_result, vol_result)
        _latent_state: LatentState = state_estimator.update(predicted_state, observation)

    # ------------------------------------------------------------------
    # Step 8: Risk assessment
    # ------------------------------------------------------------------
    risk_output = engine.assess(
        returns_history=returns_history,
        current_regime=current_regime,
        meta_uncertainty=meta_uncertainty,
    )

    # ------------------------------------------------------------------
    # Steps 9-11: Exposure -> positions -> return
    # ------------------------------------------------------------------
    exposure_weight: float = risk_output.exposure_weight
    positions: dict = route_exposure_to_positions(
        total_capital=total_capital,
        exposure_fraction=exposure_weight,
        asset_prices=asset_prices,
    )
    return positions


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def x_run_full_pipeline__mutmut_16(
    returns_history: list,
    current_regime: GlobalRegimeState,
    meta_uncertainty: float,
    total_capital: float,
    asset_prices: dict,
) -> dict:
    """
    Full deterministic pipeline from returns history to final positions.

    Step 0: Governance gate (GOV-01 + GOV-05 only).
    Steps 1-11: Unchanged from v1.1.0.

    Raises
    ------
    GovernanceViolationError
        meta_uncertainty out of [0.0, 1.0] or regime not GlobalRegimeState.
    ValueError
        Propagated from RiskEngine (invalid returns_history).
        Propagated from route_exposure_to_positions (invalid capital/prices).
    """
    # ------------------------------------------------------------------
    # Step 0: Governance Gate -- GOV-01 and GOV-05 only
    # ------------------------------------------------------------------

    # GOV-01: meta_uncertainty must be in [0.0, 1.0]
    _meta_invalid = (
        not isinstance(meta_uncertainty, (int, float))
        or not (0.0 <= float(meta_uncertainty) <= 1.0)
    )

    # GOV-05: regime must be a GlobalRegimeState instance
    _regime_invalid = not isinstance(current_regime, GlobalRegimeState)

    if _meta_invalid or _regime_invalid:
        # Build a minimal result via validate_pipeline_config using safe
        # stand-in values for parameters owned by downstream modules.
        _safe_capital = total_capital if (
            isinstance(total_capital, (int, float)) and float(total_capital) >= 0
        ) else 1.0
        _safe_regime = current_regime if isinstance(
            current_regime, GlobalRegimeState
        ) else GlobalRegimeState.UNKNOWN
        _safe_meta = meta_uncertainty if (
            isinstance(meta_uncertainty, (int, float))
            and 0.0 <= float(meta_uncertainty) <= 1.0
        ) else 0.5

        _gov_result = validate_pipeline_config(
            meta_uncertainty=_safe_meta if not _meta_invalid else meta_uncertainty,
            initial_capital=_safe_capital,
            window=20,
            step=1,
            regime=_safe_regime,
            periods_per_year=252,
        )
        # Only raise for the rules we gate on
        _gated_rules = {"GOV-01", "GOV-05"}
        _gated = [v for v in _gov_result.blocking_violations if v.rule_id in _gated_rules]
        # Also run with the actual bad value so the error message is accurate
        _real_result = validate_pipeline_config(
            meta_uncertainty=meta_uncertainty if isinstance(meta_uncertainty, (int, float)) else 999,
            initial_capital=_safe_capital,
            window=20,
            step=1,
            regime=current_regime,
            periods_per_year=252,
        )
        _real_gated = [v for v in _real_result.blocking_violations if v.rule_id in _gated_rules]
        if _real_gated:
            raise GovernanceViolationError(_real_result)

    # ------------------------------------------------------------------
    # Step 1: Instantiate all components fresh per call
    # ------------------------------------------------------------------
    engine: RiskEngine = RiskEngine()
    regime_detector: RegimeDetector = RegimeDetector()
    vol_tracker: VolatilityTracker = VolatilityTracker()
    state_estimator: StateEstimator = StateEstimator()

    # ------------------------------------------------------------------
    # Steps 2-7: State pipeline
    # ------------------------------------------------------------------
    if len(returns_history) > 0:
        features: dict = _extract_regime_features(returns_history)
        regime_result = regime_detector.detect_regime(features)
        vol_result = vol_tracker.estimate_volatility(returns_history)
        previous_state: LatentState = LatentState.default()
        predicted_state: LatentState = state_estimator.predict(previous_state)
        observation: dict = _build_observation_vector(regime_result, vol_result)
        _latent_state: LatentState = state_estimator.update(predicted_state, observation)

    # ------------------------------------------------------------------
    # Step 8: Risk assessment
    # ------------------------------------------------------------------
    risk_output = engine.assess(
        returns_history=returns_history,
        current_regime=current_regime,
        meta_uncertainty=meta_uncertainty,
    )

    # ------------------------------------------------------------------
    # Steps 9-11: Exposure -> positions -> return
    # ------------------------------------------------------------------
    exposure_weight: float = risk_output.exposure_weight
    positions: dict = route_exposure_to_positions(
        total_capital=total_capital,
        exposure_fraction=exposure_weight,
        asset_prices=asset_prices,
    )
    return positions


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def x_run_full_pipeline__mutmut_17(
    returns_history: list,
    current_regime: GlobalRegimeState,
    meta_uncertainty: float,
    total_capital: float,
    asset_prices: dict,
) -> dict:
    """
    Full deterministic pipeline from returns history to final positions.

    Step 0: Governance gate (GOV-01 + GOV-05 only).
    Steps 1-11: Unchanged from v1.1.0.

    Raises
    ------
    GovernanceViolationError
        meta_uncertainty out of [0.0, 1.0] or regime not GlobalRegimeState.
    ValueError
        Propagated from RiskEngine (invalid returns_history).
        Propagated from route_exposure_to_positions (invalid capital/prices).
    """
    # ------------------------------------------------------------------
    # Step 0: Governance Gate -- GOV-01 and GOV-05 only
    # ------------------------------------------------------------------

    # GOV-01: meta_uncertainty must be in [0.0, 1.0]
    _meta_invalid = (
        not isinstance(meta_uncertainty, (int, float))
        or not (0.0 <= float(meta_uncertainty) <= 1.0)
    )

    # GOV-05: regime must be a GlobalRegimeState instance
    _regime_invalid = not isinstance(current_regime, GlobalRegimeState)

    if _meta_invalid or _regime_invalid:
        # Build a minimal result via validate_pipeline_config using safe
        # stand-in values for parameters owned by downstream modules.
        _safe_capital = total_capital if (
            isinstance(total_capital, (int, float)) and float(total_capital) > 1
        ) else 1.0
        _safe_regime = current_regime if isinstance(
            current_regime, GlobalRegimeState
        ) else GlobalRegimeState.UNKNOWN
        _safe_meta = meta_uncertainty if (
            isinstance(meta_uncertainty, (int, float))
            and 0.0 <= float(meta_uncertainty) <= 1.0
        ) else 0.5

        _gov_result = validate_pipeline_config(
            meta_uncertainty=_safe_meta if not _meta_invalid else meta_uncertainty,
            initial_capital=_safe_capital,
            window=20,
            step=1,
            regime=_safe_regime,
            periods_per_year=252,
        )
        # Only raise for the rules we gate on
        _gated_rules = {"GOV-01", "GOV-05"}
        _gated = [v for v in _gov_result.blocking_violations if v.rule_id in _gated_rules]
        # Also run with the actual bad value so the error message is accurate
        _real_result = validate_pipeline_config(
            meta_uncertainty=meta_uncertainty if isinstance(meta_uncertainty, (int, float)) else 999,
            initial_capital=_safe_capital,
            window=20,
            step=1,
            regime=current_regime,
            periods_per_year=252,
        )
        _real_gated = [v for v in _real_result.blocking_violations if v.rule_id in _gated_rules]
        if _real_gated:
            raise GovernanceViolationError(_real_result)

    # ------------------------------------------------------------------
    # Step 1: Instantiate all components fresh per call
    # ------------------------------------------------------------------
    engine: RiskEngine = RiskEngine()
    regime_detector: RegimeDetector = RegimeDetector()
    vol_tracker: VolatilityTracker = VolatilityTracker()
    state_estimator: StateEstimator = StateEstimator()

    # ------------------------------------------------------------------
    # Steps 2-7: State pipeline
    # ------------------------------------------------------------------
    if len(returns_history) > 0:
        features: dict = _extract_regime_features(returns_history)
        regime_result = regime_detector.detect_regime(features)
        vol_result = vol_tracker.estimate_volatility(returns_history)
        previous_state: LatentState = LatentState.default()
        predicted_state: LatentState = state_estimator.predict(previous_state)
        observation: dict = _build_observation_vector(regime_result, vol_result)
        _latent_state: LatentState = state_estimator.update(predicted_state, observation)

    # ------------------------------------------------------------------
    # Step 8: Risk assessment
    # ------------------------------------------------------------------
    risk_output = engine.assess(
        returns_history=returns_history,
        current_regime=current_regime,
        meta_uncertainty=meta_uncertainty,
    )

    # ------------------------------------------------------------------
    # Steps 9-11: Exposure -> positions -> return
    # ------------------------------------------------------------------
    exposure_weight: float = risk_output.exposure_weight
    positions: dict = route_exposure_to_positions(
        total_capital=total_capital,
        exposure_fraction=exposure_weight,
        asset_prices=asset_prices,
    )
    return positions


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def x_run_full_pipeline__mutmut_18(
    returns_history: list,
    current_regime: GlobalRegimeState,
    meta_uncertainty: float,
    total_capital: float,
    asset_prices: dict,
) -> dict:
    """
    Full deterministic pipeline from returns history to final positions.

    Step 0: Governance gate (GOV-01 + GOV-05 only).
    Steps 1-11: Unchanged from v1.1.0.

    Raises
    ------
    GovernanceViolationError
        meta_uncertainty out of [0.0, 1.0] or regime not GlobalRegimeState.
    ValueError
        Propagated from RiskEngine (invalid returns_history).
        Propagated from route_exposure_to_positions (invalid capital/prices).
    """
    # ------------------------------------------------------------------
    # Step 0: Governance Gate -- GOV-01 and GOV-05 only
    # ------------------------------------------------------------------

    # GOV-01: meta_uncertainty must be in [0.0, 1.0]
    _meta_invalid = (
        not isinstance(meta_uncertainty, (int, float))
        or not (0.0 <= float(meta_uncertainty) <= 1.0)
    )

    # GOV-05: regime must be a GlobalRegimeState instance
    _regime_invalid = not isinstance(current_regime, GlobalRegimeState)

    if _meta_invalid or _regime_invalid:
        # Build a minimal result via validate_pipeline_config using safe
        # stand-in values for parameters owned by downstream modules.
        _safe_capital = total_capital if (
            isinstance(total_capital, (int, float)) and float(total_capital) > 0
        ) else 2.0
        _safe_regime = current_regime if isinstance(
            current_regime, GlobalRegimeState
        ) else GlobalRegimeState.UNKNOWN
        _safe_meta = meta_uncertainty if (
            isinstance(meta_uncertainty, (int, float))
            and 0.0 <= float(meta_uncertainty) <= 1.0
        ) else 0.5

        _gov_result = validate_pipeline_config(
            meta_uncertainty=_safe_meta if not _meta_invalid else meta_uncertainty,
            initial_capital=_safe_capital,
            window=20,
            step=1,
            regime=_safe_regime,
            periods_per_year=252,
        )
        # Only raise for the rules we gate on
        _gated_rules = {"GOV-01", "GOV-05"}
        _gated = [v for v in _gov_result.blocking_violations if v.rule_id in _gated_rules]
        # Also run with the actual bad value so the error message is accurate
        _real_result = validate_pipeline_config(
            meta_uncertainty=meta_uncertainty if isinstance(meta_uncertainty, (int, float)) else 999,
            initial_capital=_safe_capital,
            window=20,
            step=1,
            regime=current_regime,
            periods_per_year=252,
        )
        _real_gated = [v for v in _real_result.blocking_violations if v.rule_id in _gated_rules]
        if _real_gated:
            raise GovernanceViolationError(_real_result)

    # ------------------------------------------------------------------
    # Step 1: Instantiate all components fresh per call
    # ------------------------------------------------------------------
    engine: RiskEngine = RiskEngine()
    regime_detector: RegimeDetector = RegimeDetector()
    vol_tracker: VolatilityTracker = VolatilityTracker()
    state_estimator: StateEstimator = StateEstimator()

    # ------------------------------------------------------------------
    # Steps 2-7: State pipeline
    # ------------------------------------------------------------------
    if len(returns_history) > 0:
        features: dict = _extract_regime_features(returns_history)
        regime_result = regime_detector.detect_regime(features)
        vol_result = vol_tracker.estimate_volatility(returns_history)
        previous_state: LatentState = LatentState.default()
        predicted_state: LatentState = state_estimator.predict(previous_state)
        observation: dict = _build_observation_vector(regime_result, vol_result)
        _latent_state: LatentState = state_estimator.update(predicted_state, observation)

    # ------------------------------------------------------------------
    # Step 8: Risk assessment
    # ------------------------------------------------------------------
    risk_output = engine.assess(
        returns_history=returns_history,
        current_regime=current_regime,
        meta_uncertainty=meta_uncertainty,
    )

    # ------------------------------------------------------------------
    # Steps 9-11: Exposure -> positions -> return
    # ------------------------------------------------------------------
    exposure_weight: float = risk_output.exposure_weight
    positions: dict = route_exposure_to_positions(
        total_capital=total_capital,
        exposure_fraction=exposure_weight,
        asset_prices=asset_prices,
    )
    return positions


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def x_run_full_pipeline__mutmut_19(
    returns_history: list,
    current_regime: GlobalRegimeState,
    meta_uncertainty: float,
    total_capital: float,
    asset_prices: dict,
) -> dict:
    """
    Full deterministic pipeline from returns history to final positions.

    Step 0: Governance gate (GOV-01 + GOV-05 only).
    Steps 1-11: Unchanged from v1.1.0.

    Raises
    ------
    GovernanceViolationError
        meta_uncertainty out of [0.0, 1.0] or regime not GlobalRegimeState.
    ValueError
        Propagated from RiskEngine (invalid returns_history).
        Propagated from route_exposure_to_positions (invalid capital/prices).
    """
    # ------------------------------------------------------------------
    # Step 0: Governance Gate -- GOV-01 and GOV-05 only
    # ------------------------------------------------------------------

    # GOV-01: meta_uncertainty must be in [0.0, 1.0]
    _meta_invalid = (
        not isinstance(meta_uncertainty, (int, float))
        or not (0.0 <= float(meta_uncertainty) <= 1.0)
    )

    # GOV-05: regime must be a GlobalRegimeState instance
    _regime_invalid = not isinstance(current_regime, GlobalRegimeState)

    if _meta_invalid or _regime_invalid:
        # Build a minimal result via validate_pipeline_config using safe
        # stand-in values for parameters owned by downstream modules.
        _safe_capital = total_capital if (
            isinstance(total_capital, (int, float)) and float(total_capital) > 0
        ) else 1.0
        _safe_regime = None
        _safe_meta = meta_uncertainty if (
            isinstance(meta_uncertainty, (int, float))
            and 0.0 <= float(meta_uncertainty) <= 1.0
        ) else 0.5

        _gov_result = validate_pipeline_config(
            meta_uncertainty=_safe_meta if not _meta_invalid else meta_uncertainty,
            initial_capital=_safe_capital,
            window=20,
            step=1,
            regime=_safe_regime,
            periods_per_year=252,
        )
        # Only raise for the rules we gate on
        _gated_rules = {"GOV-01", "GOV-05"}
        _gated = [v for v in _gov_result.blocking_violations if v.rule_id in _gated_rules]
        # Also run with the actual bad value so the error message is accurate
        _real_result = validate_pipeline_config(
            meta_uncertainty=meta_uncertainty if isinstance(meta_uncertainty, (int, float)) else 999,
            initial_capital=_safe_capital,
            window=20,
            step=1,
            regime=current_regime,
            periods_per_year=252,
        )
        _real_gated = [v for v in _real_result.blocking_violations if v.rule_id in _gated_rules]
        if _real_gated:
            raise GovernanceViolationError(_real_result)

    # ------------------------------------------------------------------
    # Step 1: Instantiate all components fresh per call
    # ------------------------------------------------------------------
    engine: RiskEngine = RiskEngine()
    regime_detector: RegimeDetector = RegimeDetector()
    vol_tracker: VolatilityTracker = VolatilityTracker()
    state_estimator: StateEstimator = StateEstimator()

    # ------------------------------------------------------------------
    # Steps 2-7: State pipeline
    # ------------------------------------------------------------------
    if len(returns_history) > 0:
        features: dict = _extract_regime_features(returns_history)
        regime_result = regime_detector.detect_regime(features)
        vol_result = vol_tracker.estimate_volatility(returns_history)
        previous_state: LatentState = LatentState.default()
        predicted_state: LatentState = state_estimator.predict(previous_state)
        observation: dict = _build_observation_vector(regime_result, vol_result)
        _latent_state: LatentState = state_estimator.update(predicted_state, observation)

    # ------------------------------------------------------------------
    # Step 8: Risk assessment
    # ------------------------------------------------------------------
    risk_output = engine.assess(
        returns_history=returns_history,
        current_regime=current_regime,
        meta_uncertainty=meta_uncertainty,
    )

    # ------------------------------------------------------------------
    # Steps 9-11: Exposure -> positions -> return
    # ------------------------------------------------------------------
    exposure_weight: float = risk_output.exposure_weight
    positions: dict = route_exposure_to_positions(
        total_capital=total_capital,
        exposure_fraction=exposure_weight,
        asset_prices=asset_prices,
    )
    return positions


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def x_run_full_pipeline__mutmut_20(
    returns_history: list,
    current_regime: GlobalRegimeState,
    meta_uncertainty: float,
    total_capital: float,
    asset_prices: dict,
) -> dict:
    """
    Full deterministic pipeline from returns history to final positions.

    Step 0: Governance gate (GOV-01 + GOV-05 only).
    Steps 1-11: Unchanged from v1.1.0.

    Raises
    ------
    GovernanceViolationError
        meta_uncertainty out of [0.0, 1.0] or regime not GlobalRegimeState.
    ValueError
        Propagated from RiskEngine (invalid returns_history).
        Propagated from route_exposure_to_positions (invalid capital/prices).
    """
    # ------------------------------------------------------------------
    # Step 0: Governance Gate -- GOV-01 and GOV-05 only
    # ------------------------------------------------------------------

    # GOV-01: meta_uncertainty must be in [0.0, 1.0]
    _meta_invalid = (
        not isinstance(meta_uncertainty, (int, float))
        or not (0.0 <= float(meta_uncertainty) <= 1.0)
    )

    # GOV-05: regime must be a GlobalRegimeState instance
    _regime_invalid = not isinstance(current_regime, GlobalRegimeState)

    if _meta_invalid or _regime_invalid:
        # Build a minimal result via validate_pipeline_config using safe
        # stand-in values for parameters owned by downstream modules.
        _safe_capital = total_capital if (
            isinstance(total_capital, (int, float)) and float(total_capital) > 0
        ) else 1.0
        _safe_regime = current_regime if isinstance(
            current_regime, GlobalRegimeState
        ) else GlobalRegimeState.UNKNOWN
        _safe_meta = None

        _gov_result = validate_pipeline_config(
            meta_uncertainty=_safe_meta if not _meta_invalid else meta_uncertainty,
            initial_capital=_safe_capital,
            window=20,
            step=1,
            regime=_safe_regime,
            periods_per_year=252,
        )
        # Only raise for the rules we gate on
        _gated_rules = {"GOV-01", "GOV-05"}
        _gated = [v for v in _gov_result.blocking_violations if v.rule_id in _gated_rules]
        # Also run with the actual bad value so the error message is accurate
        _real_result = validate_pipeline_config(
            meta_uncertainty=meta_uncertainty if isinstance(meta_uncertainty, (int, float)) else 999,
            initial_capital=_safe_capital,
            window=20,
            step=1,
            regime=current_regime,
            periods_per_year=252,
        )
        _real_gated = [v for v in _real_result.blocking_violations if v.rule_id in _gated_rules]
        if _real_gated:
            raise GovernanceViolationError(_real_result)

    # ------------------------------------------------------------------
    # Step 1: Instantiate all components fresh per call
    # ------------------------------------------------------------------
    engine: RiskEngine = RiskEngine()
    regime_detector: RegimeDetector = RegimeDetector()
    vol_tracker: VolatilityTracker = VolatilityTracker()
    state_estimator: StateEstimator = StateEstimator()

    # ------------------------------------------------------------------
    # Steps 2-7: State pipeline
    # ------------------------------------------------------------------
    if len(returns_history) > 0:
        features: dict = _extract_regime_features(returns_history)
        regime_result = regime_detector.detect_regime(features)
        vol_result = vol_tracker.estimate_volatility(returns_history)
        previous_state: LatentState = LatentState.default()
        predicted_state: LatentState = state_estimator.predict(previous_state)
        observation: dict = _build_observation_vector(regime_result, vol_result)
        _latent_state: LatentState = state_estimator.update(predicted_state, observation)

    # ------------------------------------------------------------------
    # Step 8: Risk assessment
    # ------------------------------------------------------------------
    risk_output = engine.assess(
        returns_history=returns_history,
        current_regime=current_regime,
        meta_uncertainty=meta_uncertainty,
    )

    # ------------------------------------------------------------------
    # Steps 9-11: Exposure -> positions -> return
    # ------------------------------------------------------------------
    exposure_weight: float = risk_output.exposure_weight
    positions: dict = route_exposure_to_positions(
        total_capital=total_capital,
        exposure_fraction=exposure_weight,
        asset_prices=asset_prices,
    )
    return positions


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def x_run_full_pipeline__mutmut_21(
    returns_history: list,
    current_regime: GlobalRegimeState,
    meta_uncertainty: float,
    total_capital: float,
    asset_prices: dict,
) -> dict:
    """
    Full deterministic pipeline from returns history to final positions.

    Step 0: Governance gate (GOV-01 + GOV-05 only).
    Steps 1-11: Unchanged from v1.1.0.

    Raises
    ------
    GovernanceViolationError
        meta_uncertainty out of [0.0, 1.0] or regime not GlobalRegimeState.
    ValueError
        Propagated from RiskEngine (invalid returns_history).
        Propagated from route_exposure_to_positions (invalid capital/prices).
    """
    # ------------------------------------------------------------------
    # Step 0: Governance Gate -- GOV-01 and GOV-05 only
    # ------------------------------------------------------------------

    # GOV-01: meta_uncertainty must be in [0.0, 1.0]
    _meta_invalid = (
        not isinstance(meta_uncertainty, (int, float))
        or not (0.0 <= float(meta_uncertainty) <= 1.0)
    )

    # GOV-05: regime must be a GlobalRegimeState instance
    _regime_invalid = not isinstance(current_regime, GlobalRegimeState)

    if _meta_invalid or _regime_invalid:
        # Build a minimal result via validate_pipeline_config using safe
        # stand-in values for parameters owned by downstream modules.
        _safe_capital = total_capital if (
            isinstance(total_capital, (int, float)) and float(total_capital) > 0
        ) else 1.0
        _safe_regime = current_regime if isinstance(
            current_regime, GlobalRegimeState
        ) else GlobalRegimeState.UNKNOWN
        _safe_meta = meta_uncertainty if (
            isinstance(meta_uncertainty, (int, float)) or 0.0 <= float(meta_uncertainty) <= 1.0
        ) else 0.5

        _gov_result = validate_pipeline_config(
            meta_uncertainty=_safe_meta if not _meta_invalid else meta_uncertainty,
            initial_capital=_safe_capital,
            window=20,
            step=1,
            regime=_safe_regime,
            periods_per_year=252,
        )
        # Only raise for the rules we gate on
        _gated_rules = {"GOV-01", "GOV-05"}
        _gated = [v for v in _gov_result.blocking_violations if v.rule_id in _gated_rules]
        # Also run with the actual bad value so the error message is accurate
        _real_result = validate_pipeline_config(
            meta_uncertainty=meta_uncertainty if isinstance(meta_uncertainty, (int, float)) else 999,
            initial_capital=_safe_capital,
            window=20,
            step=1,
            regime=current_regime,
            periods_per_year=252,
        )
        _real_gated = [v for v in _real_result.blocking_violations if v.rule_id in _gated_rules]
        if _real_gated:
            raise GovernanceViolationError(_real_result)

    # ------------------------------------------------------------------
    # Step 1: Instantiate all components fresh per call
    # ------------------------------------------------------------------
    engine: RiskEngine = RiskEngine()
    regime_detector: RegimeDetector = RegimeDetector()
    vol_tracker: VolatilityTracker = VolatilityTracker()
    state_estimator: StateEstimator = StateEstimator()

    # ------------------------------------------------------------------
    # Steps 2-7: State pipeline
    # ------------------------------------------------------------------
    if len(returns_history) > 0:
        features: dict = _extract_regime_features(returns_history)
        regime_result = regime_detector.detect_regime(features)
        vol_result = vol_tracker.estimate_volatility(returns_history)
        previous_state: LatentState = LatentState.default()
        predicted_state: LatentState = state_estimator.predict(previous_state)
        observation: dict = _build_observation_vector(regime_result, vol_result)
        _latent_state: LatentState = state_estimator.update(predicted_state, observation)

    # ------------------------------------------------------------------
    # Step 8: Risk assessment
    # ------------------------------------------------------------------
    risk_output = engine.assess(
        returns_history=returns_history,
        current_regime=current_regime,
        meta_uncertainty=meta_uncertainty,
    )

    # ------------------------------------------------------------------
    # Steps 9-11: Exposure -> positions -> return
    # ------------------------------------------------------------------
    exposure_weight: float = risk_output.exposure_weight
    positions: dict = route_exposure_to_positions(
        total_capital=total_capital,
        exposure_fraction=exposure_weight,
        asset_prices=asset_prices,
    )
    return positions


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def x_run_full_pipeline__mutmut_22(
    returns_history: list,
    current_regime: GlobalRegimeState,
    meta_uncertainty: float,
    total_capital: float,
    asset_prices: dict,
) -> dict:
    """
    Full deterministic pipeline from returns history to final positions.

    Step 0: Governance gate (GOV-01 + GOV-05 only).
    Steps 1-11: Unchanged from v1.1.0.

    Raises
    ------
    GovernanceViolationError
        meta_uncertainty out of [0.0, 1.0] or regime not GlobalRegimeState.
    ValueError
        Propagated from RiskEngine (invalid returns_history).
        Propagated from route_exposure_to_positions (invalid capital/prices).
    """
    # ------------------------------------------------------------------
    # Step 0: Governance Gate -- GOV-01 and GOV-05 only
    # ------------------------------------------------------------------

    # GOV-01: meta_uncertainty must be in [0.0, 1.0]
    _meta_invalid = (
        not isinstance(meta_uncertainty, (int, float))
        or not (0.0 <= float(meta_uncertainty) <= 1.0)
    )

    # GOV-05: regime must be a GlobalRegimeState instance
    _regime_invalid = not isinstance(current_regime, GlobalRegimeState)

    if _meta_invalid or _regime_invalid:
        # Build a minimal result via validate_pipeline_config using safe
        # stand-in values for parameters owned by downstream modules.
        _safe_capital = total_capital if (
            isinstance(total_capital, (int, float)) and float(total_capital) > 0
        ) else 1.0
        _safe_regime = current_regime if isinstance(
            current_regime, GlobalRegimeState
        ) else GlobalRegimeState.UNKNOWN
        _safe_meta = meta_uncertainty if (
            isinstance(meta_uncertainty, (int, float))
            and 1.0 <= float(meta_uncertainty) <= 1.0
        ) else 0.5

        _gov_result = validate_pipeline_config(
            meta_uncertainty=_safe_meta if not _meta_invalid else meta_uncertainty,
            initial_capital=_safe_capital,
            window=20,
            step=1,
            regime=_safe_regime,
            periods_per_year=252,
        )
        # Only raise for the rules we gate on
        _gated_rules = {"GOV-01", "GOV-05"}
        _gated = [v for v in _gov_result.blocking_violations if v.rule_id in _gated_rules]
        # Also run with the actual bad value so the error message is accurate
        _real_result = validate_pipeline_config(
            meta_uncertainty=meta_uncertainty if isinstance(meta_uncertainty, (int, float)) else 999,
            initial_capital=_safe_capital,
            window=20,
            step=1,
            regime=current_regime,
            periods_per_year=252,
        )
        _real_gated = [v for v in _real_result.blocking_violations if v.rule_id in _gated_rules]
        if _real_gated:
            raise GovernanceViolationError(_real_result)

    # ------------------------------------------------------------------
    # Step 1: Instantiate all components fresh per call
    # ------------------------------------------------------------------
    engine: RiskEngine = RiskEngine()
    regime_detector: RegimeDetector = RegimeDetector()
    vol_tracker: VolatilityTracker = VolatilityTracker()
    state_estimator: StateEstimator = StateEstimator()

    # ------------------------------------------------------------------
    # Steps 2-7: State pipeline
    # ------------------------------------------------------------------
    if len(returns_history) > 0:
        features: dict = _extract_regime_features(returns_history)
        regime_result = regime_detector.detect_regime(features)
        vol_result = vol_tracker.estimate_volatility(returns_history)
        previous_state: LatentState = LatentState.default()
        predicted_state: LatentState = state_estimator.predict(previous_state)
        observation: dict = _build_observation_vector(regime_result, vol_result)
        _latent_state: LatentState = state_estimator.update(predicted_state, observation)

    # ------------------------------------------------------------------
    # Step 8: Risk assessment
    # ------------------------------------------------------------------
    risk_output = engine.assess(
        returns_history=returns_history,
        current_regime=current_regime,
        meta_uncertainty=meta_uncertainty,
    )

    # ------------------------------------------------------------------
    # Steps 9-11: Exposure -> positions -> return
    # ------------------------------------------------------------------
    exposure_weight: float = risk_output.exposure_weight
    positions: dict = route_exposure_to_positions(
        total_capital=total_capital,
        exposure_fraction=exposure_weight,
        asset_prices=asset_prices,
    )
    return positions


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def x_run_full_pipeline__mutmut_23(
    returns_history: list,
    current_regime: GlobalRegimeState,
    meta_uncertainty: float,
    total_capital: float,
    asset_prices: dict,
) -> dict:
    """
    Full deterministic pipeline from returns history to final positions.

    Step 0: Governance gate (GOV-01 + GOV-05 only).
    Steps 1-11: Unchanged from v1.1.0.

    Raises
    ------
    GovernanceViolationError
        meta_uncertainty out of [0.0, 1.0] or regime not GlobalRegimeState.
    ValueError
        Propagated from RiskEngine (invalid returns_history).
        Propagated from route_exposure_to_positions (invalid capital/prices).
    """
    # ------------------------------------------------------------------
    # Step 0: Governance Gate -- GOV-01 and GOV-05 only
    # ------------------------------------------------------------------

    # GOV-01: meta_uncertainty must be in [0.0, 1.0]
    _meta_invalid = (
        not isinstance(meta_uncertainty, (int, float))
        or not (0.0 <= float(meta_uncertainty) <= 1.0)
    )

    # GOV-05: regime must be a GlobalRegimeState instance
    _regime_invalid = not isinstance(current_regime, GlobalRegimeState)

    if _meta_invalid or _regime_invalid:
        # Build a minimal result via validate_pipeline_config using safe
        # stand-in values for parameters owned by downstream modules.
        _safe_capital = total_capital if (
            isinstance(total_capital, (int, float)) and float(total_capital) > 0
        ) else 1.0
        _safe_regime = current_regime if isinstance(
            current_regime, GlobalRegimeState
        ) else GlobalRegimeState.UNKNOWN
        _safe_meta = meta_uncertainty if (
            isinstance(meta_uncertainty, (int, float))
            and 0.0 < float(meta_uncertainty) <= 1.0
        ) else 0.5

        _gov_result = validate_pipeline_config(
            meta_uncertainty=_safe_meta if not _meta_invalid else meta_uncertainty,
            initial_capital=_safe_capital,
            window=20,
            step=1,
            regime=_safe_regime,
            periods_per_year=252,
        )
        # Only raise for the rules we gate on
        _gated_rules = {"GOV-01", "GOV-05"}
        _gated = [v for v in _gov_result.blocking_violations if v.rule_id in _gated_rules]
        # Also run with the actual bad value so the error message is accurate
        _real_result = validate_pipeline_config(
            meta_uncertainty=meta_uncertainty if isinstance(meta_uncertainty, (int, float)) else 999,
            initial_capital=_safe_capital,
            window=20,
            step=1,
            regime=current_regime,
            periods_per_year=252,
        )
        _real_gated = [v for v in _real_result.blocking_violations if v.rule_id in _gated_rules]
        if _real_gated:
            raise GovernanceViolationError(_real_result)

    # ------------------------------------------------------------------
    # Step 1: Instantiate all components fresh per call
    # ------------------------------------------------------------------
    engine: RiskEngine = RiskEngine()
    regime_detector: RegimeDetector = RegimeDetector()
    vol_tracker: VolatilityTracker = VolatilityTracker()
    state_estimator: StateEstimator = StateEstimator()

    # ------------------------------------------------------------------
    # Steps 2-7: State pipeline
    # ------------------------------------------------------------------
    if len(returns_history) > 0:
        features: dict = _extract_regime_features(returns_history)
        regime_result = regime_detector.detect_regime(features)
        vol_result = vol_tracker.estimate_volatility(returns_history)
        previous_state: LatentState = LatentState.default()
        predicted_state: LatentState = state_estimator.predict(previous_state)
        observation: dict = _build_observation_vector(regime_result, vol_result)
        _latent_state: LatentState = state_estimator.update(predicted_state, observation)

    # ------------------------------------------------------------------
    # Step 8: Risk assessment
    # ------------------------------------------------------------------
    risk_output = engine.assess(
        returns_history=returns_history,
        current_regime=current_regime,
        meta_uncertainty=meta_uncertainty,
    )

    # ------------------------------------------------------------------
    # Steps 9-11: Exposure -> positions -> return
    # ------------------------------------------------------------------
    exposure_weight: float = risk_output.exposure_weight
    positions: dict = route_exposure_to_positions(
        total_capital=total_capital,
        exposure_fraction=exposure_weight,
        asset_prices=asset_prices,
    )
    return positions


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def x_run_full_pipeline__mutmut_24(
    returns_history: list,
    current_regime: GlobalRegimeState,
    meta_uncertainty: float,
    total_capital: float,
    asset_prices: dict,
) -> dict:
    """
    Full deterministic pipeline from returns history to final positions.

    Step 0: Governance gate (GOV-01 + GOV-05 only).
    Steps 1-11: Unchanged from v1.1.0.

    Raises
    ------
    GovernanceViolationError
        meta_uncertainty out of [0.0, 1.0] or regime not GlobalRegimeState.
    ValueError
        Propagated from RiskEngine (invalid returns_history).
        Propagated from route_exposure_to_positions (invalid capital/prices).
    """
    # ------------------------------------------------------------------
    # Step 0: Governance Gate -- GOV-01 and GOV-05 only
    # ------------------------------------------------------------------

    # GOV-01: meta_uncertainty must be in [0.0, 1.0]
    _meta_invalid = (
        not isinstance(meta_uncertainty, (int, float))
        or not (0.0 <= float(meta_uncertainty) <= 1.0)
    )

    # GOV-05: regime must be a GlobalRegimeState instance
    _regime_invalid = not isinstance(current_regime, GlobalRegimeState)

    if _meta_invalid or _regime_invalid:
        # Build a minimal result via validate_pipeline_config using safe
        # stand-in values for parameters owned by downstream modules.
        _safe_capital = total_capital if (
            isinstance(total_capital, (int, float)) and float(total_capital) > 0
        ) else 1.0
        _safe_regime = current_regime if isinstance(
            current_regime, GlobalRegimeState
        ) else GlobalRegimeState.UNKNOWN
        _safe_meta = meta_uncertainty if (
            isinstance(meta_uncertainty, (int, float))
            and 0.0 <= float(None) <= 1.0
        ) else 0.5

        _gov_result = validate_pipeline_config(
            meta_uncertainty=_safe_meta if not _meta_invalid else meta_uncertainty,
            initial_capital=_safe_capital,
            window=20,
            step=1,
            regime=_safe_regime,
            periods_per_year=252,
        )
        # Only raise for the rules we gate on
        _gated_rules = {"GOV-01", "GOV-05"}
        _gated = [v for v in _gov_result.blocking_violations if v.rule_id in _gated_rules]
        # Also run with the actual bad value so the error message is accurate
        _real_result = validate_pipeline_config(
            meta_uncertainty=meta_uncertainty if isinstance(meta_uncertainty, (int, float)) else 999,
            initial_capital=_safe_capital,
            window=20,
            step=1,
            regime=current_regime,
            periods_per_year=252,
        )
        _real_gated = [v for v in _real_result.blocking_violations if v.rule_id in _gated_rules]
        if _real_gated:
            raise GovernanceViolationError(_real_result)

    # ------------------------------------------------------------------
    # Step 1: Instantiate all components fresh per call
    # ------------------------------------------------------------------
    engine: RiskEngine = RiskEngine()
    regime_detector: RegimeDetector = RegimeDetector()
    vol_tracker: VolatilityTracker = VolatilityTracker()
    state_estimator: StateEstimator = StateEstimator()

    # ------------------------------------------------------------------
    # Steps 2-7: State pipeline
    # ------------------------------------------------------------------
    if len(returns_history) > 0:
        features: dict = _extract_regime_features(returns_history)
        regime_result = regime_detector.detect_regime(features)
        vol_result = vol_tracker.estimate_volatility(returns_history)
        previous_state: LatentState = LatentState.default()
        predicted_state: LatentState = state_estimator.predict(previous_state)
        observation: dict = _build_observation_vector(regime_result, vol_result)
        _latent_state: LatentState = state_estimator.update(predicted_state, observation)

    # ------------------------------------------------------------------
    # Step 8: Risk assessment
    # ------------------------------------------------------------------
    risk_output = engine.assess(
        returns_history=returns_history,
        current_regime=current_regime,
        meta_uncertainty=meta_uncertainty,
    )

    # ------------------------------------------------------------------
    # Steps 9-11: Exposure -> positions -> return
    # ------------------------------------------------------------------
    exposure_weight: float = risk_output.exposure_weight
    positions: dict = route_exposure_to_positions(
        total_capital=total_capital,
        exposure_fraction=exposure_weight,
        asset_prices=asset_prices,
    )
    return positions


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def x_run_full_pipeline__mutmut_25(
    returns_history: list,
    current_regime: GlobalRegimeState,
    meta_uncertainty: float,
    total_capital: float,
    asset_prices: dict,
) -> dict:
    """
    Full deterministic pipeline from returns history to final positions.

    Step 0: Governance gate (GOV-01 + GOV-05 only).
    Steps 1-11: Unchanged from v1.1.0.

    Raises
    ------
    GovernanceViolationError
        meta_uncertainty out of [0.0, 1.0] or regime not GlobalRegimeState.
    ValueError
        Propagated from RiskEngine (invalid returns_history).
        Propagated from route_exposure_to_positions (invalid capital/prices).
    """
    # ------------------------------------------------------------------
    # Step 0: Governance Gate -- GOV-01 and GOV-05 only
    # ------------------------------------------------------------------

    # GOV-01: meta_uncertainty must be in [0.0, 1.0]
    _meta_invalid = (
        not isinstance(meta_uncertainty, (int, float))
        or not (0.0 <= float(meta_uncertainty) <= 1.0)
    )

    # GOV-05: regime must be a GlobalRegimeState instance
    _regime_invalid = not isinstance(current_regime, GlobalRegimeState)

    if _meta_invalid or _regime_invalid:
        # Build a minimal result via validate_pipeline_config using safe
        # stand-in values for parameters owned by downstream modules.
        _safe_capital = total_capital if (
            isinstance(total_capital, (int, float)) and float(total_capital) > 0
        ) else 1.0
        _safe_regime = current_regime if isinstance(
            current_regime, GlobalRegimeState
        ) else GlobalRegimeState.UNKNOWN
        _safe_meta = meta_uncertainty if (
            isinstance(meta_uncertainty, (int, float))
            and 0.0 <= float(meta_uncertainty) < 1.0
        ) else 0.5

        _gov_result = validate_pipeline_config(
            meta_uncertainty=_safe_meta if not _meta_invalid else meta_uncertainty,
            initial_capital=_safe_capital,
            window=20,
            step=1,
            regime=_safe_regime,
            periods_per_year=252,
        )
        # Only raise for the rules we gate on
        _gated_rules = {"GOV-01", "GOV-05"}
        _gated = [v for v in _gov_result.blocking_violations if v.rule_id in _gated_rules]
        # Also run with the actual bad value so the error message is accurate
        _real_result = validate_pipeline_config(
            meta_uncertainty=meta_uncertainty if isinstance(meta_uncertainty, (int, float)) else 999,
            initial_capital=_safe_capital,
            window=20,
            step=1,
            regime=current_regime,
            periods_per_year=252,
        )
        _real_gated = [v for v in _real_result.blocking_violations if v.rule_id in _gated_rules]
        if _real_gated:
            raise GovernanceViolationError(_real_result)

    # ------------------------------------------------------------------
    # Step 1: Instantiate all components fresh per call
    # ------------------------------------------------------------------
    engine: RiskEngine = RiskEngine()
    regime_detector: RegimeDetector = RegimeDetector()
    vol_tracker: VolatilityTracker = VolatilityTracker()
    state_estimator: StateEstimator = StateEstimator()

    # ------------------------------------------------------------------
    # Steps 2-7: State pipeline
    # ------------------------------------------------------------------
    if len(returns_history) > 0:
        features: dict = _extract_regime_features(returns_history)
        regime_result = regime_detector.detect_regime(features)
        vol_result = vol_tracker.estimate_volatility(returns_history)
        previous_state: LatentState = LatentState.default()
        predicted_state: LatentState = state_estimator.predict(previous_state)
        observation: dict = _build_observation_vector(regime_result, vol_result)
        _latent_state: LatentState = state_estimator.update(predicted_state, observation)

    # ------------------------------------------------------------------
    # Step 8: Risk assessment
    # ------------------------------------------------------------------
    risk_output = engine.assess(
        returns_history=returns_history,
        current_regime=current_regime,
        meta_uncertainty=meta_uncertainty,
    )

    # ------------------------------------------------------------------
    # Steps 9-11: Exposure -> positions -> return
    # ------------------------------------------------------------------
    exposure_weight: float = risk_output.exposure_weight
    positions: dict = route_exposure_to_positions(
        total_capital=total_capital,
        exposure_fraction=exposure_weight,
        asset_prices=asset_prices,
    )
    return positions


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def x_run_full_pipeline__mutmut_26(
    returns_history: list,
    current_regime: GlobalRegimeState,
    meta_uncertainty: float,
    total_capital: float,
    asset_prices: dict,
) -> dict:
    """
    Full deterministic pipeline from returns history to final positions.

    Step 0: Governance gate (GOV-01 + GOV-05 only).
    Steps 1-11: Unchanged from v1.1.0.

    Raises
    ------
    GovernanceViolationError
        meta_uncertainty out of [0.0, 1.0] or regime not GlobalRegimeState.
    ValueError
        Propagated from RiskEngine (invalid returns_history).
        Propagated from route_exposure_to_positions (invalid capital/prices).
    """
    # ------------------------------------------------------------------
    # Step 0: Governance Gate -- GOV-01 and GOV-05 only
    # ------------------------------------------------------------------

    # GOV-01: meta_uncertainty must be in [0.0, 1.0]
    _meta_invalid = (
        not isinstance(meta_uncertainty, (int, float))
        or not (0.0 <= float(meta_uncertainty) <= 1.0)
    )

    # GOV-05: regime must be a GlobalRegimeState instance
    _regime_invalid = not isinstance(current_regime, GlobalRegimeState)

    if _meta_invalid or _regime_invalid:
        # Build a minimal result via validate_pipeline_config using safe
        # stand-in values for parameters owned by downstream modules.
        _safe_capital = total_capital if (
            isinstance(total_capital, (int, float)) and float(total_capital) > 0
        ) else 1.0
        _safe_regime = current_regime if isinstance(
            current_regime, GlobalRegimeState
        ) else GlobalRegimeState.UNKNOWN
        _safe_meta = meta_uncertainty if (
            isinstance(meta_uncertainty, (int, float))
            and 0.0 <= float(meta_uncertainty) <= 2.0
        ) else 0.5

        _gov_result = validate_pipeline_config(
            meta_uncertainty=_safe_meta if not _meta_invalid else meta_uncertainty,
            initial_capital=_safe_capital,
            window=20,
            step=1,
            regime=_safe_regime,
            periods_per_year=252,
        )
        # Only raise for the rules we gate on
        _gated_rules = {"GOV-01", "GOV-05"}
        _gated = [v for v in _gov_result.blocking_violations if v.rule_id in _gated_rules]
        # Also run with the actual bad value so the error message is accurate
        _real_result = validate_pipeline_config(
            meta_uncertainty=meta_uncertainty if isinstance(meta_uncertainty, (int, float)) else 999,
            initial_capital=_safe_capital,
            window=20,
            step=1,
            regime=current_regime,
            periods_per_year=252,
        )
        _real_gated = [v for v in _real_result.blocking_violations if v.rule_id in _gated_rules]
        if _real_gated:
            raise GovernanceViolationError(_real_result)

    # ------------------------------------------------------------------
    # Step 1: Instantiate all components fresh per call
    # ------------------------------------------------------------------
    engine: RiskEngine = RiskEngine()
    regime_detector: RegimeDetector = RegimeDetector()
    vol_tracker: VolatilityTracker = VolatilityTracker()
    state_estimator: StateEstimator = StateEstimator()

    # ------------------------------------------------------------------
    # Steps 2-7: State pipeline
    # ------------------------------------------------------------------
    if len(returns_history) > 0:
        features: dict = _extract_regime_features(returns_history)
        regime_result = regime_detector.detect_regime(features)
        vol_result = vol_tracker.estimate_volatility(returns_history)
        previous_state: LatentState = LatentState.default()
        predicted_state: LatentState = state_estimator.predict(previous_state)
        observation: dict = _build_observation_vector(regime_result, vol_result)
        _latent_state: LatentState = state_estimator.update(predicted_state, observation)

    # ------------------------------------------------------------------
    # Step 8: Risk assessment
    # ------------------------------------------------------------------
    risk_output = engine.assess(
        returns_history=returns_history,
        current_regime=current_regime,
        meta_uncertainty=meta_uncertainty,
    )

    # ------------------------------------------------------------------
    # Steps 9-11: Exposure -> positions -> return
    # ------------------------------------------------------------------
    exposure_weight: float = risk_output.exposure_weight
    positions: dict = route_exposure_to_positions(
        total_capital=total_capital,
        exposure_fraction=exposure_weight,
        asset_prices=asset_prices,
    )
    return positions


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def x_run_full_pipeline__mutmut_27(
    returns_history: list,
    current_regime: GlobalRegimeState,
    meta_uncertainty: float,
    total_capital: float,
    asset_prices: dict,
) -> dict:
    """
    Full deterministic pipeline from returns history to final positions.

    Step 0: Governance gate (GOV-01 + GOV-05 only).
    Steps 1-11: Unchanged from v1.1.0.

    Raises
    ------
    GovernanceViolationError
        meta_uncertainty out of [0.0, 1.0] or regime not GlobalRegimeState.
    ValueError
        Propagated from RiskEngine (invalid returns_history).
        Propagated from route_exposure_to_positions (invalid capital/prices).
    """
    # ------------------------------------------------------------------
    # Step 0: Governance Gate -- GOV-01 and GOV-05 only
    # ------------------------------------------------------------------

    # GOV-01: meta_uncertainty must be in [0.0, 1.0]
    _meta_invalid = (
        not isinstance(meta_uncertainty, (int, float))
        or not (0.0 <= float(meta_uncertainty) <= 1.0)
    )

    # GOV-05: regime must be a GlobalRegimeState instance
    _regime_invalid = not isinstance(current_regime, GlobalRegimeState)

    if _meta_invalid or _regime_invalid:
        # Build a minimal result via validate_pipeline_config using safe
        # stand-in values for parameters owned by downstream modules.
        _safe_capital = total_capital if (
            isinstance(total_capital, (int, float)) and float(total_capital) > 0
        ) else 1.0
        _safe_regime = current_regime if isinstance(
            current_regime, GlobalRegimeState
        ) else GlobalRegimeState.UNKNOWN
        _safe_meta = meta_uncertainty if (
            isinstance(meta_uncertainty, (int, float))
            and 0.0 <= float(meta_uncertainty) <= 1.0
        ) else 1.5

        _gov_result = validate_pipeline_config(
            meta_uncertainty=_safe_meta if not _meta_invalid else meta_uncertainty,
            initial_capital=_safe_capital,
            window=20,
            step=1,
            regime=_safe_regime,
            periods_per_year=252,
        )
        # Only raise for the rules we gate on
        _gated_rules = {"GOV-01", "GOV-05"}
        _gated = [v for v in _gov_result.blocking_violations if v.rule_id in _gated_rules]
        # Also run with the actual bad value so the error message is accurate
        _real_result = validate_pipeline_config(
            meta_uncertainty=meta_uncertainty if isinstance(meta_uncertainty, (int, float)) else 999,
            initial_capital=_safe_capital,
            window=20,
            step=1,
            regime=current_regime,
            periods_per_year=252,
        )
        _real_gated = [v for v in _real_result.blocking_violations if v.rule_id in _gated_rules]
        if _real_gated:
            raise GovernanceViolationError(_real_result)

    # ------------------------------------------------------------------
    # Step 1: Instantiate all components fresh per call
    # ------------------------------------------------------------------
    engine: RiskEngine = RiskEngine()
    regime_detector: RegimeDetector = RegimeDetector()
    vol_tracker: VolatilityTracker = VolatilityTracker()
    state_estimator: StateEstimator = StateEstimator()

    # ------------------------------------------------------------------
    # Steps 2-7: State pipeline
    # ------------------------------------------------------------------
    if len(returns_history) > 0:
        features: dict = _extract_regime_features(returns_history)
        regime_result = regime_detector.detect_regime(features)
        vol_result = vol_tracker.estimate_volatility(returns_history)
        previous_state: LatentState = LatentState.default()
        predicted_state: LatentState = state_estimator.predict(previous_state)
        observation: dict = _build_observation_vector(regime_result, vol_result)
        _latent_state: LatentState = state_estimator.update(predicted_state, observation)

    # ------------------------------------------------------------------
    # Step 8: Risk assessment
    # ------------------------------------------------------------------
    risk_output = engine.assess(
        returns_history=returns_history,
        current_regime=current_regime,
        meta_uncertainty=meta_uncertainty,
    )

    # ------------------------------------------------------------------
    # Steps 9-11: Exposure -> positions -> return
    # ------------------------------------------------------------------
    exposure_weight: float = risk_output.exposure_weight
    positions: dict = route_exposure_to_positions(
        total_capital=total_capital,
        exposure_fraction=exposure_weight,
        asset_prices=asset_prices,
    )
    return positions


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def x_run_full_pipeline__mutmut_28(
    returns_history: list,
    current_regime: GlobalRegimeState,
    meta_uncertainty: float,
    total_capital: float,
    asset_prices: dict,
) -> dict:
    """
    Full deterministic pipeline from returns history to final positions.

    Step 0: Governance gate (GOV-01 + GOV-05 only).
    Steps 1-11: Unchanged from v1.1.0.

    Raises
    ------
    GovernanceViolationError
        meta_uncertainty out of [0.0, 1.0] or regime not GlobalRegimeState.
    ValueError
        Propagated from RiskEngine (invalid returns_history).
        Propagated from route_exposure_to_positions (invalid capital/prices).
    """
    # ------------------------------------------------------------------
    # Step 0: Governance Gate -- GOV-01 and GOV-05 only
    # ------------------------------------------------------------------

    # GOV-01: meta_uncertainty must be in [0.0, 1.0]
    _meta_invalid = (
        not isinstance(meta_uncertainty, (int, float))
        or not (0.0 <= float(meta_uncertainty) <= 1.0)
    )

    # GOV-05: regime must be a GlobalRegimeState instance
    _regime_invalid = not isinstance(current_regime, GlobalRegimeState)

    if _meta_invalid or _regime_invalid:
        # Build a minimal result via validate_pipeline_config using safe
        # stand-in values for parameters owned by downstream modules.
        _safe_capital = total_capital if (
            isinstance(total_capital, (int, float)) and float(total_capital) > 0
        ) else 1.0
        _safe_regime = current_regime if isinstance(
            current_regime, GlobalRegimeState
        ) else GlobalRegimeState.UNKNOWN
        _safe_meta = meta_uncertainty if (
            isinstance(meta_uncertainty, (int, float))
            and 0.0 <= float(meta_uncertainty) <= 1.0
        ) else 0.5

        _gov_result = None
        # Only raise for the rules we gate on
        _gated_rules = {"GOV-01", "GOV-05"}
        _gated = [v for v in _gov_result.blocking_violations if v.rule_id in _gated_rules]
        # Also run with the actual bad value so the error message is accurate
        _real_result = validate_pipeline_config(
            meta_uncertainty=meta_uncertainty if isinstance(meta_uncertainty, (int, float)) else 999,
            initial_capital=_safe_capital,
            window=20,
            step=1,
            regime=current_regime,
            periods_per_year=252,
        )
        _real_gated = [v for v in _real_result.blocking_violations if v.rule_id in _gated_rules]
        if _real_gated:
            raise GovernanceViolationError(_real_result)

    # ------------------------------------------------------------------
    # Step 1: Instantiate all components fresh per call
    # ------------------------------------------------------------------
    engine: RiskEngine = RiskEngine()
    regime_detector: RegimeDetector = RegimeDetector()
    vol_tracker: VolatilityTracker = VolatilityTracker()
    state_estimator: StateEstimator = StateEstimator()

    # ------------------------------------------------------------------
    # Steps 2-7: State pipeline
    # ------------------------------------------------------------------
    if len(returns_history) > 0:
        features: dict = _extract_regime_features(returns_history)
        regime_result = regime_detector.detect_regime(features)
        vol_result = vol_tracker.estimate_volatility(returns_history)
        previous_state: LatentState = LatentState.default()
        predicted_state: LatentState = state_estimator.predict(previous_state)
        observation: dict = _build_observation_vector(regime_result, vol_result)
        _latent_state: LatentState = state_estimator.update(predicted_state, observation)

    # ------------------------------------------------------------------
    # Step 8: Risk assessment
    # ------------------------------------------------------------------
    risk_output = engine.assess(
        returns_history=returns_history,
        current_regime=current_regime,
        meta_uncertainty=meta_uncertainty,
    )

    # ------------------------------------------------------------------
    # Steps 9-11: Exposure -> positions -> return
    # ------------------------------------------------------------------
    exposure_weight: float = risk_output.exposure_weight
    positions: dict = route_exposure_to_positions(
        total_capital=total_capital,
        exposure_fraction=exposure_weight,
        asset_prices=asset_prices,
    )
    return positions


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def x_run_full_pipeline__mutmut_29(
    returns_history: list,
    current_regime: GlobalRegimeState,
    meta_uncertainty: float,
    total_capital: float,
    asset_prices: dict,
) -> dict:
    """
    Full deterministic pipeline from returns history to final positions.

    Step 0: Governance gate (GOV-01 + GOV-05 only).
    Steps 1-11: Unchanged from v1.1.0.

    Raises
    ------
    GovernanceViolationError
        meta_uncertainty out of [0.0, 1.0] or regime not GlobalRegimeState.
    ValueError
        Propagated from RiskEngine (invalid returns_history).
        Propagated from route_exposure_to_positions (invalid capital/prices).
    """
    # ------------------------------------------------------------------
    # Step 0: Governance Gate -- GOV-01 and GOV-05 only
    # ------------------------------------------------------------------

    # GOV-01: meta_uncertainty must be in [0.0, 1.0]
    _meta_invalid = (
        not isinstance(meta_uncertainty, (int, float))
        or not (0.0 <= float(meta_uncertainty) <= 1.0)
    )

    # GOV-05: regime must be a GlobalRegimeState instance
    _regime_invalid = not isinstance(current_regime, GlobalRegimeState)

    if _meta_invalid or _regime_invalid:
        # Build a minimal result via validate_pipeline_config using safe
        # stand-in values for parameters owned by downstream modules.
        _safe_capital = total_capital if (
            isinstance(total_capital, (int, float)) and float(total_capital) > 0
        ) else 1.0
        _safe_regime = current_regime if isinstance(
            current_regime, GlobalRegimeState
        ) else GlobalRegimeState.UNKNOWN
        _safe_meta = meta_uncertainty if (
            isinstance(meta_uncertainty, (int, float))
            and 0.0 <= float(meta_uncertainty) <= 1.0
        ) else 0.5

        _gov_result = validate_pipeline_config(
            meta_uncertainty=None,
            initial_capital=_safe_capital,
            window=20,
            step=1,
            regime=_safe_regime,
            periods_per_year=252,
        )
        # Only raise for the rules we gate on
        _gated_rules = {"GOV-01", "GOV-05"}
        _gated = [v for v in _gov_result.blocking_violations if v.rule_id in _gated_rules]
        # Also run with the actual bad value so the error message is accurate
        _real_result = validate_pipeline_config(
            meta_uncertainty=meta_uncertainty if isinstance(meta_uncertainty, (int, float)) else 999,
            initial_capital=_safe_capital,
            window=20,
            step=1,
            regime=current_regime,
            periods_per_year=252,
        )
        _real_gated = [v for v in _real_result.blocking_violations if v.rule_id in _gated_rules]
        if _real_gated:
            raise GovernanceViolationError(_real_result)

    # ------------------------------------------------------------------
    # Step 1: Instantiate all components fresh per call
    # ------------------------------------------------------------------
    engine: RiskEngine = RiskEngine()
    regime_detector: RegimeDetector = RegimeDetector()
    vol_tracker: VolatilityTracker = VolatilityTracker()
    state_estimator: StateEstimator = StateEstimator()

    # ------------------------------------------------------------------
    # Steps 2-7: State pipeline
    # ------------------------------------------------------------------
    if len(returns_history) > 0:
        features: dict = _extract_regime_features(returns_history)
        regime_result = regime_detector.detect_regime(features)
        vol_result = vol_tracker.estimate_volatility(returns_history)
        previous_state: LatentState = LatentState.default()
        predicted_state: LatentState = state_estimator.predict(previous_state)
        observation: dict = _build_observation_vector(regime_result, vol_result)
        _latent_state: LatentState = state_estimator.update(predicted_state, observation)

    # ------------------------------------------------------------------
    # Step 8: Risk assessment
    # ------------------------------------------------------------------
    risk_output = engine.assess(
        returns_history=returns_history,
        current_regime=current_regime,
        meta_uncertainty=meta_uncertainty,
    )

    # ------------------------------------------------------------------
    # Steps 9-11: Exposure -> positions -> return
    # ------------------------------------------------------------------
    exposure_weight: float = risk_output.exposure_weight
    positions: dict = route_exposure_to_positions(
        total_capital=total_capital,
        exposure_fraction=exposure_weight,
        asset_prices=asset_prices,
    )
    return positions


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def x_run_full_pipeline__mutmut_30(
    returns_history: list,
    current_regime: GlobalRegimeState,
    meta_uncertainty: float,
    total_capital: float,
    asset_prices: dict,
) -> dict:
    """
    Full deterministic pipeline from returns history to final positions.

    Step 0: Governance gate (GOV-01 + GOV-05 only).
    Steps 1-11: Unchanged from v1.1.0.

    Raises
    ------
    GovernanceViolationError
        meta_uncertainty out of [0.0, 1.0] or regime not GlobalRegimeState.
    ValueError
        Propagated from RiskEngine (invalid returns_history).
        Propagated from route_exposure_to_positions (invalid capital/prices).
    """
    # ------------------------------------------------------------------
    # Step 0: Governance Gate -- GOV-01 and GOV-05 only
    # ------------------------------------------------------------------

    # GOV-01: meta_uncertainty must be in [0.0, 1.0]
    _meta_invalid = (
        not isinstance(meta_uncertainty, (int, float))
        or not (0.0 <= float(meta_uncertainty) <= 1.0)
    )

    # GOV-05: regime must be a GlobalRegimeState instance
    _regime_invalid = not isinstance(current_regime, GlobalRegimeState)

    if _meta_invalid or _regime_invalid:
        # Build a minimal result via validate_pipeline_config using safe
        # stand-in values for parameters owned by downstream modules.
        _safe_capital = total_capital if (
            isinstance(total_capital, (int, float)) and float(total_capital) > 0
        ) else 1.0
        _safe_regime = current_regime if isinstance(
            current_regime, GlobalRegimeState
        ) else GlobalRegimeState.UNKNOWN
        _safe_meta = meta_uncertainty if (
            isinstance(meta_uncertainty, (int, float))
            and 0.0 <= float(meta_uncertainty) <= 1.0
        ) else 0.5

        _gov_result = validate_pipeline_config(
            meta_uncertainty=_safe_meta if not _meta_invalid else meta_uncertainty,
            initial_capital=None,
            window=20,
            step=1,
            regime=_safe_regime,
            periods_per_year=252,
        )
        # Only raise for the rules we gate on
        _gated_rules = {"GOV-01", "GOV-05"}
        _gated = [v for v in _gov_result.blocking_violations if v.rule_id in _gated_rules]
        # Also run with the actual bad value so the error message is accurate
        _real_result = validate_pipeline_config(
            meta_uncertainty=meta_uncertainty if isinstance(meta_uncertainty, (int, float)) else 999,
            initial_capital=_safe_capital,
            window=20,
            step=1,
            regime=current_regime,
            periods_per_year=252,
        )
        _real_gated = [v for v in _real_result.blocking_violations if v.rule_id in _gated_rules]
        if _real_gated:
            raise GovernanceViolationError(_real_result)

    # ------------------------------------------------------------------
    # Step 1: Instantiate all components fresh per call
    # ------------------------------------------------------------------
    engine: RiskEngine = RiskEngine()
    regime_detector: RegimeDetector = RegimeDetector()
    vol_tracker: VolatilityTracker = VolatilityTracker()
    state_estimator: StateEstimator = StateEstimator()

    # ------------------------------------------------------------------
    # Steps 2-7: State pipeline
    # ------------------------------------------------------------------
    if len(returns_history) > 0:
        features: dict = _extract_regime_features(returns_history)
        regime_result = regime_detector.detect_regime(features)
        vol_result = vol_tracker.estimate_volatility(returns_history)
        previous_state: LatentState = LatentState.default()
        predicted_state: LatentState = state_estimator.predict(previous_state)
        observation: dict = _build_observation_vector(regime_result, vol_result)
        _latent_state: LatentState = state_estimator.update(predicted_state, observation)

    # ------------------------------------------------------------------
    # Step 8: Risk assessment
    # ------------------------------------------------------------------
    risk_output = engine.assess(
        returns_history=returns_history,
        current_regime=current_regime,
        meta_uncertainty=meta_uncertainty,
    )

    # ------------------------------------------------------------------
    # Steps 9-11: Exposure -> positions -> return
    # ------------------------------------------------------------------
    exposure_weight: float = risk_output.exposure_weight
    positions: dict = route_exposure_to_positions(
        total_capital=total_capital,
        exposure_fraction=exposure_weight,
        asset_prices=asset_prices,
    )
    return positions


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def x_run_full_pipeline__mutmut_31(
    returns_history: list,
    current_regime: GlobalRegimeState,
    meta_uncertainty: float,
    total_capital: float,
    asset_prices: dict,
) -> dict:
    """
    Full deterministic pipeline from returns history to final positions.

    Step 0: Governance gate (GOV-01 + GOV-05 only).
    Steps 1-11: Unchanged from v1.1.0.

    Raises
    ------
    GovernanceViolationError
        meta_uncertainty out of [0.0, 1.0] or regime not GlobalRegimeState.
    ValueError
        Propagated from RiskEngine (invalid returns_history).
        Propagated from route_exposure_to_positions (invalid capital/prices).
    """
    # ------------------------------------------------------------------
    # Step 0: Governance Gate -- GOV-01 and GOV-05 only
    # ------------------------------------------------------------------

    # GOV-01: meta_uncertainty must be in [0.0, 1.0]
    _meta_invalid = (
        not isinstance(meta_uncertainty, (int, float))
        or not (0.0 <= float(meta_uncertainty) <= 1.0)
    )

    # GOV-05: regime must be a GlobalRegimeState instance
    _regime_invalid = not isinstance(current_regime, GlobalRegimeState)

    if _meta_invalid or _regime_invalid:
        # Build a minimal result via validate_pipeline_config using safe
        # stand-in values for parameters owned by downstream modules.
        _safe_capital = total_capital if (
            isinstance(total_capital, (int, float)) and float(total_capital) > 0
        ) else 1.0
        _safe_regime = current_regime if isinstance(
            current_regime, GlobalRegimeState
        ) else GlobalRegimeState.UNKNOWN
        _safe_meta = meta_uncertainty if (
            isinstance(meta_uncertainty, (int, float))
            and 0.0 <= float(meta_uncertainty) <= 1.0
        ) else 0.5

        _gov_result = validate_pipeline_config(
            meta_uncertainty=_safe_meta if not _meta_invalid else meta_uncertainty,
            initial_capital=_safe_capital,
            window=None,
            step=1,
            regime=_safe_regime,
            periods_per_year=252,
        )
        # Only raise for the rules we gate on
        _gated_rules = {"GOV-01", "GOV-05"}
        _gated = [v for v in _gov_result.blocking_violations if v.rule_id in _gated_rules]
        # Also run with the actual bad value so the error message is accurate
        _real_result = validate_pipeline_config(
            meta_uncertainty=meta_uncertainty if isinstance(meta_uncertainty, (int, float)) else 999,
            initial_capital=_safe_capital,
            window=20,
            step=1,
            regime=current_regime,
            periods_per_year=252,
        )
        _real_gated = [v for v in _real_result.blocking_violations if v.rule_id in _gated_rules]
        if _real_gated:
            raise GovernanceViolationError(_real_result)

    # ------------------------------------------------------------------
    # Step 1: Instantiate all components fresh per call
    # ------------------------------------------------------------------
    engine: RiskEngine = RiskEngine()
    regime_detector: RegimeDetector = RegimeDetector()
    vol_tracker: VolatilityTracker = VolatilityTracker()
    state_estimator: StateEstimator = StateEstimator()

    # ------------------------------------------------------------------
    # Steps 2-7: State pipeline
    # ------------------------------------------------------------------
    if len(returns_history) > 0:
        features: dict = _extract_regime_features(returns_history)
        regime_result = regime_detector.detect_regime(features)
        vol_result = vol_tracker.estimate_volatility(returns_history)
        previous_state: LatentState = LatentState.default()
        predicted_state: LatentState = state_estimator.predict(previous_state)
        observation: dict = _build_observation_vector(regime_result, vol_result)
        _latent_state: LatentState = state_estimator.update(predicted_state, observation)

    # ------------------------------------------------------------------
    # Step 8: Risk assessment
    # ------------------------------------------------------------------
    risk_output = engine.assess(
        returns_history=returns_history,
        current_regime=current_regime,
        meta_uncertainty=meta_uncertainty,
    )

    # ------------------------------------------------------------------
    # Steps 9-11: Exposure -> positions -> return
    # ------------------------------------------------------------------
    exposure_weight: float = risk_output.exposure_weight
    positions: dict = route_exposure_to_positions(
        total_capital=total_capital,
        exposure_fraction=exposure_weight,
        asset_prices=asset_prices,
    )
    return positions


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def x_run_full_pipeline__mutmut_32(
    returns_history: list,
    current_regime: GlobalRegimeState,
    meta_uncertainty: float,
    total_capital: float,
    asset_prices: dict,
) -> dict:
    """
    Full deterministic pipeline from returns history to final positions.

    Step 0: Governance gate (GOV-01 + GOV-05 only).
    Steps 1-11: Unchanged from v1.1.0.

    Raises
    ------
    GovernanceViolationError
        meta_uncertainty out of [0.0, 1.0] or regime not GlobalRegimeState.
    ValueError
        Propagated from RiskEngine (invalid returns_history).
        Propagated from route_exposure_to_positions (invalid capital/prices).
    """
    # ------------------------------------------------------------------
    # Step 0: Governance Gate -- GOV-01 and GOV-05 only
    # ------------------------------------------------------------------

    # GOV-01: meta_uncertainty must be in [0.0, 1.0]
    _meta_invalid = (
        not isinstance(meta_uncertainty, (int, float))
        or not (0.0 <= float(meta_uncertainty) <= 1.0)
    )

    # GOV-05: regime must be a GlobalRegimeState instance
    _regime_invalid = not isinstance(current_regime, GlobalRegimeState)

    if _meta_invalid or _regime_invalid:
        # Build a minimal result via validate_pipeline_config using safe
        # stand-in values for parameters owned by downstream modules.
        _safe_capital = total_capital if (
            isinstance(total_capital, (int, float)) and float(total_capital) > 0
        ) else 1.0
        _safe_regime = current_regime if isinstance(
            current_regime, GlobalRegimeState
        ) else GlobalRegimeState.UNKNOWN
        _safe_meta = meta_uncertainty if (
            isinstance(meta_uncertainty, (int, float))
            and 0.0 <= float(meta_uncertainty) <= 1.0
        ) else 0.5

        _gov_result = validate_pipeline_config(
            meta_uncertainty=_safe_meta if not _meta_invalid else meta_uncertainty,
            initial_capital=_safe_capital,
            window=20,
            step=None,
            regime=_safe_regime,
            periods_per_year=252,
        )
        # Only raise for the rules we gate on
        _gated_rules = {"GOV-01", "GOV-05"}
        _gated = [v for v in _gov_result.blocking_violations if v.rule_id in _gated_rules]
        # Also run with the actual bad value so the error message is accurate
        _real_result = validate_pipeline_config(
            meta_uncertainty=meta_uncertainty if isinstance(meta_uncertainty, (int, float)) else 999,
            initial_capital=_safe_capital,
            window=20,
            step=1,
            regime=current_regime,
            periods_per_year=252,
        )
        _real_gated = [v for v in _real_result.blocking_violations if v.rule_id in _gated_rules]
        if _real_gated:
            raise GovernanceViolationError(_real_result)

    # ------------------------------------------------------------------
    # Step 1: Instantiate all components fresh per call
    # ------------------------------------------------------------------
    engine: RiskEngine = RiskEngine()
    regime_detector: RegimeDetector = RegimeDetector()
    vol_tracker: VolatilityTracker = VolatilityTracker()
    state_estimator: StateEstimator = StateEstimator()

    # ------------------------------------------------------------------
    # Steps 2-7: State pipeline
    # ------------------------------------------------------------------
    if len(returns_history) > 0:
        features: dict = _extract_regime_features(returns_history)
        regime_result = regime_detector.detect_regime(features)
        vol_result = vol_tracker.estimate_volatility(returns_history)
        previous_state: LatentState = LatentState.default()
        predicted_state: LatentState = state_estimator.predict(previous_state)
        observation: dict = _build_observation_vector(regime_result, vol_result)
        _latent_state: LatentState = state_estimator.update(predicted_state, observation)

    # ------------------------------------------------------------------
    # Step 8: Risk assessment
    # ------------------------------------------------------------------
    risk_output = engine.assess(
        returns_history=returns_history,
        current_regime=current_regime,
        meta_uncertainty=meta_uncertainty,
    )

    # ------------------------------------------------------------------
    # Steps 9-11: Exposure -> positions -> return
    # ------------------------------------------------------------------
    exposure_weight: float = risk_output.exposure_weight
    positions: dict = route_exposure_to_positions(
        total_capital=total_capital,
        exposure_fraction=exposure_weight,
        asset_prices=asset_prices,
    )
    return positions


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def x_run_full_pipeline__mutmut_33(
    returns_history: list,
    current_regime: GlobalRegimeState,
    meta_uncertainty: float,
    total_capital: float,
    asset_prices: dict,
) -> dict:
    """
    Full deterministic pipeline from returns history to final positions.

    Step 0: Governance gate (GOV-01 + GOV-05 only).
    Steps 1-11: Unchanged from v1.1.0.

    Raises
    ------
    GovernanceViolationError
        meta_uncertainty out of [0.0, 1.0] or regime not GlobalRegimeState.
    ValueError
        Propagated from RiskEngine (invalid returns_history).
        Propagated from route_exposure_to_positions (invalid capital/prices).
    """
    # ------------------------------------------------------------------
    # Step 0: Governance Gate -- GOV-01 and GOV-05 only
    # ------------------------------------------------------------------

    # GOV-01: meta_uncertainty must be in [0.0, 1.0]
    _meta_invalid = (
        not isinstance(meta_uncertainty, (int, float))
        or not (0.0 <= float(meta_uncertainty) <= 1.0)
    )

    # GOV-05: regime must be a GlobalRegimeState instance
    _regime_invalid = not isinstance(current_regime, GlobalRegimeState)

    if _meta_invalid or _regime_invalid:
        # Build a minimal result via validate_pipeline_config using safe
        # stand-in values for parameters owned by downstream modules.
        _safe_capital = total_capital if (
            isinstance(total_capital, (int, float)) and float(total_capital) > 0
        ) else 1.0
        _safe_regime = current_regime if isinstance(
            current_regime, GlobalRegimeState
        ) else GlobalRegimeState.UNKNOWN
        _safe_meta = meta_uncertainty if (
            isinstance(meta_uncertainty, (int, float))
            and 0.0 <= float(meta_uncertainty) <= 1.0
        ) else 0.5

        _gov_result = validate_pipeline_config(
            meta_uncertainty=_safe_meta if not _meta_invalid else meta_uncertainty,
            initial_capital=_safe_capital,
            window=20,
            step=1,
            regime=None,
            periods_per_year=252,
        )
        # Only raise for the rules we gate on
        _gated_rules = {"GOV-01", "GOV-05"}
        _gated = [v for v in _gov_result.blocking_violations if v.rule_id in _gated_rules]
        # Also run with the actual bad value so the error message is accurate
        _real_result = validate_pipeline_config(
            meta_uncertainty=meta_uncertainty if isinstance(meta_uncertainty, (int, float)) else 999,
            initial_capital=_safe_capital,
            window=20,
            step=1,
            regime=current_regime,
            periods_per_year=252,
        )
        _real_gated = [v for v in _real_result.blocking_violations if v.rule_id in _gated_rules]
        if _real_gated:
            raise GovernanceViolationError(_real_result)

    # ------------------------------------------------------------------
    # Step 1: Instantiate all components fresh per call
    # ------------------------------------------------------------------
    engine: RiskEngine = RiskEngine()
    regime_detector: RegimeDetector = RegimeDetector()
    vol_tracker: VolatilityTracker = VolatilityTracker()
    state_estimator: StateEstimator = StateEstimator()

    # ------------------------------------------------------------------
    # Steps 2-7: State pipeline
    # ------------------------------------------------------------------
    if len(returns_history) > 0:
        features: dict = _extract_regime_features(returns_history)
        regime_result = regime_detector.detect_regime(features)
        vol_result = vol_tracker.estimate_volatility(returns_history)
        previous_state: LatentState = LatentState.default()
        predicted_state: LatentState = state_estimator.predict(previous_state)
        observation: dict = _build_observation_vector(regime_result, vol_result)
        _latent_state: LatentState = state_estimator.update(predicted_state, observation)

    # ------------------------------------------------------------------
    # Step 8: Risk assessment
    # ------------------------------------------------------------------
    risk_output = engine.assess(
        returns_history=returns_history,
        current_regime=current_regime,
        meta_uncertainty=meta_uncertainty,
    )

    # ------------------------------------------------------------------
    # Steps 9-11: Exposure -> positions -> return
    # ------------------------------------------------------------------
    exposure_weight: float = risk_output.exposure_weight
    positions: dict = route_exposure_to_positions(
        total_capital=total_capital,
        exposure_fraction=exposure_weight,
        asset_prices=asset_prices,
    )
    return positions


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def x_run_full_pipeline__mutmut_34(
    returns_history: list,
    current_regime: GlobalRegimeState,
    meta_uncertainty: float,
    total_capital: float,
    asset_prices: dict,
) -> dict:
    """
    Full deterministic pipeline from returns history to final positions.

    Step 0: Governance gate (GOV-01 + GOV-05 only).
    Steps 1-11: Unchanged from v1.1.0.

    Raises
    ------
    GovernanceViolationError
        meta_uncertainty out of [0.0, 1.0] or regime not GlobalRegimeState.
    ValueError
        Propagated from RiskEngine (invalid returns_history).
        Propagated from route_exposure_to_positions (invalid capital/prices).
    """
    # ------------------------------------------------------------------
    # Step 0: Governance Gate -- GOV-01 and GOV-05 only
    # ------------------------------------------------------------------

    # GOV-01: meta_uncertainty must be in [0.0, 1.0]
    _meta_invalid = (
        not isinstance(meta_uncertainty, (int, float))
        or not (0.0 <= float(meta_uncertainty) <= 1.0)
    )

    # GOV-05: regime must be a GlobalRegimeState instance
    _regime_invalid = not isinstance(current_regime, GlobalRegimeState)

    if _meta_invalid or _regime_invalid:
        # Build a minimal result via validate_pipeline_config using safe
        # stand-in values for parameters owned by downstream modules.
        _safe_capital = total_capital if (
            isinstance(total_capital, (int, float)) and float(total_capital) > 0
        ) else 1.0
        _safe_regime = current_regime if isinstance(
            current_regime, GlobalRegimeState
        ) else GlobalRegimeState.UNKNOWN
        _safe_meta = meta_uncertainty if (
            isinstance(meta_uncertainty, (int, float))
            and 0.0 <= float(meta_uncertainty) <= 1.0
        ) else 0.5

        _gov_result = validate_pipeline_config(
            meta_uncertainty=_safe_meta if not _meta_invalid else meta_uncertainty,
            initial_capital=_safe_capital,
            window=20,
            step=1,
            regime=_safe_regime,
            periods_per_year=None,
        )
        # Only raise for the rules we gate on
        _gated_rules = {"GOV-01", "GOV-05"}
        _gated = [v for v in _gov_result.blocking_violations if v.rule_id in _gated_rules]
        # Also run with the actual bad value so the error message is accurate
        _real_result = validate_pipeline_config(
            meta_uncertainty=meta_uncertainty if isinstance(meta_uncertainty, (int, float)) else 999,
            initial_capital=_safe_capital,
            window=20,
            step=1,
            regime=current_regime,
            periods_per_year=252,
        )
        _real_gated = [v for v in _real_result.blocking_violations if v.rule_id in _gated_rules]
        if _real_gated:
            raise GovernanceViolationError(_real_result)

    # ------------------------------------------------------------------
    # Step 1: Instantiate all components fresh per call
    # ------------------------------------------------------------------
    engine: RiskEngine = RiskEngine()
    regime_detector: RegimeDetector = RegimeDetector()
    vol_tracker: VolatilityTracker = VolatilityTracker()
    state_estimator: StateEstimator = StateEstimator()

    # ------------------------------------------------------------------
    # Steps 2-7: State pipeline
    # ------------------------------------------------------------------
    if len(returns_history) > 0:
        features: dict = _extract_regime_features(returns_history)
        regime_result = regime_detector.detect_regime(features)
        vol_result = vol_tracker.estimate_volatility(returns_history)
        previous_state: LatentState = LatentState.default()
        predicted_state: LatentState = state_estimator.predict(previous_state)
        observation: dict = _build_observation_vector(regime_result, vol_result)
        _latent_state: LatentState = state_estimator.update(predicted_state, observation)

    # ------------------------------------------------------------------
    # Step 8: Risk assessment
    # ------------------------------------------------------------------
    risk_output = engine.assess(
        returns_history=returns_history,
        current_regime=current_regime,
        meta_uncertainty=meta_uncertainty,
    )

    # ------------------------------------------------------------------
    # Steps 9-11: Exposure -> positions -> return
    # ------------------------------------------------------------------
    exposure_weight: float = risk_output.exposure_weight
    positions: dict = route_exposure_to_positions(
        total_capital=total_capital,
        exposure_fraction=exposure_weight,
        asset_prices=asset_prices,
    )
    return positions


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def x_run_full_pipeline__mutmut_35(
    returns_history: list,
    current_regime: GlobalRegimeState,
    meta_uncertainty: float,
    total_capital: float,
    asset_prices: dict,
) -> dict:
    """
    Full deterministic pipeline from returns history to final positions.

    Step 0: Governance gate (GOV-01 + GOV-05 only).
    Steps 1-11: Unchanged from v1.1.0.

    Raises
    ------
    GovernanceViolationError
        meta_uncertainty out of [0.0, 1.0] or regime not GlobalRegimeState.
    ValueError
        Propagated from RiskEngine (invalid returns_history).
        Propagated from route_exposure_to_positions (invalid capital/prices).
    """
    # ------------------------------------------------------------------
    # Step 0: Governance Gate -- GOV-01 and GOV-05 only
    # ------------------------------------------------------------------

    # GOV-01: meta_uncertainty must be in [0.0, 1.0]
    _meta_invalid = (
        not isinstance(meta_uncertainty, (int, float))
        or not (0.0 <= float(meta_uncertainty) <= 1.0)
    )

    # GOV-05: regime must be a GlobalRegimeState instance
    _regime_invalid = not isinstance(current_regime, GlobalRegimeState)

    if _meta_invalid or _regime_invalid:
        # Build a minimal result via validate_pipeline_config using safe
        # stand-in values for parameters owned by downstream modules.
        _safe_capital = total_capital if (
            isinstance(total_capital, (int, float)) and float(total_capital) > 0
        ) else 1.0
        _safe_regime = current_regime if isinstance(
            current_regime, GlobalRegimeState
        ) else GlobalRegimeState.UNKNOWN
        _safe_meta = meta_uncertainty if (
            isinstance(meta_uncertainty, (int, float))
            and 0.0 <= float(meta_uncertainty) <= 1.0
        ) else 0.5

        _gov_result = validate_pipeline_config(
            initial_capital=_safe_capital,
            window=20,
            step=1,
            regime=_safe_regime,
            periods_per_year=252,
        )
        # Only raise for the rules we gate on
        _gated_rules = {"GOV-01", "GOV-05"}
        _gated = [v for v in _gov_result.blocking_violations if v.rule_id in _gated_rules]
        # Also run with the actual bad value so the error message is accurate
        _real_result = validate_pipeline_config(
            meta_uncertainty=meta_uncertainty if isinstance(meta_uncertainty, (int, float)) else 999,
            initial_capital=_safe_capital,
            window=20,
            step=1,
            regime=current_regime,
            periods_per_year=252,
        )
        _real_gated = [v for v in _real_result.blocking_violations if v.rule_id in _gated_rules]
        if _real_gated:
            raise GovernanceViolationError(_real_result)

    # ------------------------------------------------------------------
    # Step 1: Instantiate all components fresh per call
    # ------------------------------------------------------------------
    engine: RiskEngine = RiskEngine()
    regime_detector: RegimeDetector = RegimeDetector()
    vol_tracker: VolatilityTracker = VolatilityTracker()
    state_estimator: StateEstimator = StateEstimator()

    # ------------------------------------------------------------------
    # Steps 2-7: State pipeline
    # ------------------------------------------------------------------
    if len(returns_history) > 0:
        features: dict = _extract_regime_features(returns_history)
        regime_result = regime_detector.detect_regime(features)
        vol_result = vol_tracker.estimate_volatility(returns_history)
        previous_state: LatentState = LatentState.default()
        predicted_state: LatentState = state_estimator.predict(previous_state)
        observation: dict = _build_observation_vector(regime_result, vol_result)
        _latent_state: LatentState = state_estimator.update(predicted_state, observation)

    # ------------------------------------------------------------------
    # Step 8: Risk assessment
    # ------------------------------------------------------------------
    risk_output = engine.assess(
        returns_history=returns_history,
        current_regime=current_regime,
        meta_uncertainty=meta_uncertainty,
    )

    # ------------------------------------------------------------------
    # Steps 9-11: Exposure -> positions -> return
    # ------------------------------------------------------------------
    exposure_weight: float = risk_output.exposure_weight
    positions: dict = route_exposure_to_positions(
        total_capital=total_capital,
        exposure_fraction=exposure_weight,
        asset_prices=asset_prices,
    )
    return positions


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def x_run_full_pipeline__mutmut_36(
    returns_history: list,
    current_regime: GlobalRegimeState,
    meta_uncertainty: float,
    total_capital: float,
    asset_prices: dict,
) -> dict:
    """
    Full deterministic pipeline from returns history to final positions.

    Step 0: Governance gate (GOV-01 + GOV-05 only).
    Steps 1-11: Unchanged from v1.1.0.

    Raises
    ------
    GovernanceViolationError
        meta_uncertainty out of [0.0, 1.0] or regime not GlobalRegimeState.
    ValueError
        Propagated from RiskEngine (invalid returns_history).
        Propagated from route_exposure_to_positions (invalid capital/prices).
    """
    # ------------------------------------------------------------------
    # Step 0: Governance Gate -- GOV-01 and GOV-05 only
    # ------------------------------------------------------------------

    # GOV-01: meta_uncertainty must be in [0.0, 1.0]
    _meta_invalid = (
        not isinstance(meta_uncertainty, (int, float))
        or not (0.0 <= float(meta_uncertainty) <= 1.0)
    )

    # GOV-05: regime must be a GlobalRegimeState instance
    _regime_invalid = not isinstance(current_regime, GlobalRegimeState)

    if _meta_invalid or _regime_invalid:
        # Build a minimal result via validate_pipeline_config using safe
        # stand-in values for parameters owned by downstream modules.
        _safe_capital = total_capital if (
            isinstance(total_capital, (int, float)) and float(total_capital) > 0
        ) else 1.0
        _safe_regime = current_regime if isinstance(
            current_regime, GlobalRegimeState
        ) else GlobalRegimeState.UNKNOWN
        _safe_meta = meta_uncertainty if (
            isinstance(meta_uncertainty, (int, float))
            and 0.0 <= float(meta_uncertainty) <= 1.0
        ) else 0.5

        _gov_result = validate_pipeline_config(
            meta_uncertainty=_safe_meta if not _meta_invalid else meta_uncertainty,
            window=20,
            step=1,
            regime=_safe_regime,
            periods_per_year=252,
        )
        # Only raise for the rules we gate on
        _gated_rules = {"GOV-01", "GOV-05"}
        _gated = [v for v in _gov_result.blocking_violations if v.rule_id in _gated_rules]
        # Also run with the actual bad value so the error message is accurate
        _real_result = validate_pipeline_config(
            meta_uncertainty=meta_uncertainty if isinstance(meta_uncertainty, (int, float)) else 999,
            initial_capital=_safe_capital,
            window=20,
            step=1,
            regime=current_regime,
            periods_per_year=252,
        )
        _real_gated = [v for v in _real_result.blocking_violations if v.rule_id in _gated_rules]
        if _real_gated:
            raise GovernanceViolationError(_real_result)

    # ------------------------------------------------------------------
    # Step 1: Instantiate all components fresh per call
    # ------------------------------------------------------------------
    engine: RiskEngine = RiskEngine()
    regime_detector: RegimeDetector = RegimeDetector()
    vol_tracker: VolatilityTracker = VolatilityTracker()
    state_estimator: StateEstimator = StateEstimator()

    # ------------------------------------------------------------------
    # Steps 2-7: State pipeline
    # ------------------------------------------------------------------
    if len(returns_history) > 0:
        features: dict = _extract_regime_features(returns_history)
        regime_result = regime_detector.detect_regime(features)
        vol_result = vol_tracker.estimate_volatility(returns_history)
        previous_state: LatentState = LatentState.default()
        predicted_state: LatentState = state_estimator.predict(previous_state)
        observation: dict = _build_observation_vector(regime_result, vol_result)
        _latent_state: LatentState = state_estimator.update(predicted_state, observation)

    # ------------------------------------------------------------------
    # Step 8: Risk assessment
    # ------------------------------------------------------------------
    risk_output = engine.assess(
        returns_history=returns_history,
        current_regime=current_regime,
        meta_uncertainty=meta_uncertainty,
    )

    # ------------------------------------------------------------------
    # Steps 9-11: Exposure -> positions -> return
    # ------------------------------------------------------------------
    exposure_weight: float = risk_output.exposure_weight
    positions: dict = route_exposure_to_positions(
        total_capital=total_capital,
        exposure_fraction=exposure_weight,
        asset_prices=asset_prices,
    )
    return positions


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def x_run_full_pipeline__mutmut_37(
    returns_history: list,
    current_regime: GlobalRegimeState,
    meta_uncertainty: float,
    total_capital: float,
    asset_prices: dict,
) -> dict:
    """
    Full deterministic pipeline from returns history to final positions.

    Step 0: Governance gate (GOV-01 + GOV-05 only).
    Steps 1-11: Unchanged from v1.1.0.

    Raises
    ------
    GovernanceViolationError
        meta_uncertainty out of [0.0, 1.0] or regime not GlobalRegimeState.
    ValueError
        Propagated from RiskEngine (invalid returns_history).
        Propagated from route_exposure_to_positions (invalid capital/prices).
    """
    # ------------------------------------------------------------------
    # Step 0: Governance Gate -- GOV-01 and GOV-05 only
    # ------------------------------------------------------------------

    # GOV-01: meta_uncertainty must be in [0.0, 1.0]
    _meta_invalid = (
        not isinstance(meta_uncertainty, (int, float))
        or not (0.0 <= float(meta_uncertainty) <= 1.0)
    )

    # GOV-05: regime must be a GlobalRegimeState instance
    _regime_invalid = not isinstance(current_regime, GlobalRegimeState)

    if _meta_invalid or _regime_invalid:
        # Build a minimal result via validate_pipeline_config using safe
        # stand-in values for parameters owned by downstream modules.
        _safe_capital = total_capital if (
            isinstance(total_capital, (int, float)) and float(total_capital) > 0
        ) else 1.0
        _safe_regime = current_regime if isinstance(
            current_regime, GlobalRegimeState
        ) else GlobalRegimeState.UNKNOWN
        _safe_meta = meta_uncertainty if (
            isinstance(meta_uncertainty, (int, float))
            and 0.0 <= float(meta_uncertainty) <= 1.0
        ) else 0.5

        _gov_result = validate_pipeline_config(
            meta_uncertainty=_safe_meta if not _meta_invalid else meta_uncertainty,
            initial_capital=_safe_capital,
            step=1,
            regime=_safe_regime,
            periods_per_year=252,
        )
        # Only raise for the rules we gate on
        _gated_rules = {"GOV-01", "GOV-05"}
        _gated = [v for v in _gov_result.blocking_violations if v.rule_id in _gated_rules]
        # Also run with the actual bad value so the error message is accurate
        _real_result = validate_pipeline_config(
            meta_uncertainty=meta_uncertainty if isinstance(meta_uncertainty, (int, float)) else 999,
            initial_capital=_safe_capital,
            window=20,
            step=1,
            regime=current_regime,
            periods_per_year=252,
        )
        _real_gated = [v for v in _real_result.blocking_violations if v.rule_id in _gated_rules]
        if _real_gated:
            raise GovernanceViolationError(_real_result)

    # ------------------------------------------------------------------
    # Step 1: Instantiate all components fresh per call
    # ------------------------------------------------------------------
    engine: RiskEngine = RiskEngine()
    regime_detector: RegimeDetector = RegimeDetector()
    vol_tracker: VolatilityTracker = VolatilityTracker()
    state_estimator: StateEstimator = StateEstimator()

    # ------------------------------------------------------------------
    # Steps 2-7: State pipeline
    # ------------------------------------------------------------------
    if len(returns_history) > 0:
        features: dict = _extract_regime_features(returns_history)
        regime_result = regime_detector.detect_regime(features)
        vol_result = vol_tracker.estimate_volatility(returns_history)
        previous_state: LatentState = LatentState.default()
        predicted_state: LatentState = state_estimator.predict(previous_state)
        observation: dict = _build_observation_vector(regime_result, vol_result)
        _latent_state: LatentState = state_estimator.update(predicted_state, observation)

    # ------------------------------------------------------------------
    # Step 8: Risk assessment
    # ------------------------------------------------------------------
    risk_output = engine.assess(
        returns_history=returns_history,
        current_regime=current_regime,
        meta_uncertainty=meta_uncertainty,
    )

    # ------------------------------------------------------------------
    # Steps 9-11: Exposure -> positions -> return
    # ------------------------------------------------------------------
    exposure_weight: float = risk_output.exposure_weight
    positions: dict = route_exposure_to_positions(
        total_capital=total_capital,
        exposure_fraction=exposure_weight,
        asset_prices=asset_prices,
    )
    return positions


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def x_run_full_pipeline__mutmut_38(
    returns_history: list,
    current_regime: GlobalRegimeState,
    meta_uncertainty: float,
    total_capital: float,
    asset_prices: dict,
) -> dict:
    """
    Full deterministic pipeline from returns history to final positions.

    Step 0: Governance gate (GOV-01 + GOV-05 only).
    Steps 1-11: Unchanged from v1.1.0.

    Raises
    ------
    GovernanceViolationError
        meta_uncertainty out of [0.0, 1.0] or regime not GlobalRegimeState.
    ValueError
        Propagated from RiskEngine (invalid returns_history).
        Propagated from route_exposure_to_positions (invalid capital/prices).
    """
    # ------------------------------------------------------------------
    # Step 0: Governance Gate -- GOV-01 and GOV-05 only
    # ------------------------------------------------------------------

    # GOV-01: meta_uncertainty must be in [0.0, 1.0]
    _meta_invalid = (
        not isinstance(meta_uncertainty, (int, float))
        or not (0.0 <= float(meta_uncertainty) <= 1.0)
    )

    # GOV-05: regime must be a GlobalRegimeState instance
    _regime_invalid = not isinstance(current_regime, GlobalRegimeState)

    if _meta_invalid or _regime_invalid:
        # Build a minimal result via validate_pipeline_config using safe
        # stand-in values for parameters owned by downstream modules.
        _safe_capital = total_capital if (
            isinstance(total_capital, (int, float)) and float(total_capital) > 0
        ) else 1.0
        _safe_regime = current_regime if isinstance(
            current_regime, GlobalRegimeState
        ) else GlobalRegimeState.UNKNOWN
        _safe_meta = meta_uncertainty if (
            isinstance(meta_uncertainty, (int, float))
            and 0.0 <= float(meta_uncertainty) <= 1.0
        ) else 0.5

        _gov_result = validate_pipeline_config(
            meta_uncertainty=_safe_meta if not _meta_invalid else meta_uncertainty,
            initial_capital=_safe_capital,
            window=20,
            regime=_safe_regime,
            periods_per_year=252,
        )
        # Only raise for the rules we gate on
        _gated_rules = {"GOV-01", "GOV-05"}
        _gated = [v for v in _gov_result.blocking_violations if v.rule_id in _gated_rules]
        # Also run with the actual bad value so the error message is accurate
        _real_result = validate_pipeline_config(
            meta_uncertainty=meta_uncertainty if isinstance(meta_uncertainty, (int, float)) else 999,
            initial_capital=_safe_capital,
            window=20,
            step=1,
            regime=current_regime,
            periods_per_year=252,
        )
        _real_gated = [v for v in _real_result.blocking_violations if v.rule_id in _gated_rules]
        if _real_gated:
            raise GovernanceViolationError(_real_result)

    # ------------------------------------------------------------------
    # Step 1: Instantiate all components fresh per call
    # ------------------------------------------------------------------
    engine: RiskEngine = RiskEngine()
    regime_detector: RegimeDetector = RegimeDetector()
    vol_tracker: VolatilityTracker = VolatilityTracker()
    state_estimator: StateEstimator = StateEstimator()

    # ------------------------------------------------------------------
    # Steps 2-7: State pipeline
    # ------------------------------------------------------------------
    if len(returns_history) > 0:
        features: dict = _extract_regime_features(returns_history)
        regime_result = regime_detector.detect_regime(features)
        vol_result = vol_tracker.estimate_volatility(returns_history)
        previous_state: LatentState = LatentState.default()
        predicted_state: LatentState = state_estimator.predict(previous_state)
        observation: dict = _build_observation_vector(regime_result, vol_result)
        _latent_state: LatentState = state_estimator.update(predicted_state, observation)

    # ------------------------------------------------------------------
    # Step 8: Risk assessment
    # ------------------------------------------------------------------
    risk_output = engine.assess(
        returns_history=returns_history,
        current_regime=current_regime,
        meta_uncertainty=meta_uncertainty,
    )

    # ------------------------------------------------------------------
    # Steps 9-11: Exposure -> positions -> return
    # ------------------------------------------------------------------
    exposure_weight: float = risk_output.exposure_weight
    positions: dict = route_exposure_to_positions(
        total_capital=total_capital,
        exposure_fraction=exposure_weight,
        asset_prices=asset_prices,
    )
    return positions


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def x_run_full_pipeline__mutmut_39(
    returns_history: list,
    current_regime: GlobalRegimeState,
    meta_uncertainty: float,
    total_capital: float,
    asset_prices: dict,
) -> dict:
    """
    Full deterministic pipeline from returns history to final positions.

    Step 0: Governance gate (GOV-01 + GOV-05 only).
    Steps 1-11: Unchanged from v1.1.0.

    Raises
    ------
    GovernanceViolationError
        meta_uncertainty out of [0.0, 1.0] or regime not GlobalRegimeState.
    ValueError
        Propagated from RiskEngine (invalid returns_history).
        Propagated from route_exposure_to_positions (invalid capital/prices).
    """
    # ------------------------------------------------------------------
    # Step 0: Governance Gate -- GOV-01 and GOV-05 only
    # ------------------------------------------------------------------

    # GOV-01: meta_uncertainty must be in [0.0, 1.0]
    _meta_invalid = (
        not isinstance(meta_uncertainty, (int, float))
        or not (0.0 <= float(meta_uncertainty) <= 1.0)
    )

    # GOV-05: regime must be a GlobalRegimeState instance
    _regime_invalid = not isinstance(current_regime, GlobalRegimeState)

    if _meta_invalid or _regime_invalid:
        # Build a minimal result via validate_pipeline_config using safe
        # stand-in values for parameters owned by downstream modules.
        _safe_capital = total_capital if (
            isinstance(total_capital, (int, float)) and float(total_capital) > 0
        ) else 1.0
        _safe_regime = current_regime if isinstance(
            current_regime, GlobalRegimeState
        ) else GlobalRegimeState.UNKNOWN
        _safe_meta = meta_uncertainty if (
            isinstance(meta_uncertainty, (int, float))
            and 0.0 <= float(meta_uncertainty) <= 1.0
        ) else 0.5

        _gov_result = validate_pipeline_config(
            meta_uncertainty=_safe_meta if not _meta_invalid else meta_uncertainty,
            initial_capital=_safe_capital,
            window=20,
            step=1,
            periods_per_year=252,
        )
        # Only raise for the rules we gate on
        _gated_rules = {"GOV-01", "GOV-05"}
        _gated = [v for v in _gov_result.blocking_violations if v.rule_id in _gated_rules]
        # Also run with the actual bad value so the error message is accurate
        _real_result = validate_pipeline_config(
            meta_uncertainty=meta_uncertainty if isinstance(meta_uncertainty, (int, float)) else 999,
            initial_capital=_safe_capital,
            window=20,
            step=1,
            regime=current_regime,
            periods_per_year=252,
        )
        _real_gated = [v for v in _real_result.blocking_violations if v.rule_id in _gated_rules]
        if _real_gated:
            raise GovernanceViolationError(_real_result)

    # ------------------------------------------------------------------
    # Step 1: Instantiate all components fresh per call
    # ------------------------------------------------------------------
    engine: RiskEngine = RiskEngine()
    regime_detector: RegimeDetector = RegimeDetector()
    vol_tracker: VolatilityTracker = VolatilityTracker()
    state_estimator: StateEstimator = StateEstimator()

    # ------------------------------------------------------------------
    # Steps 2-7: State pipeline
    # ------------------------------------------------------------------
    if len(returns_history) > 0:
        features: dict = _extract_regime_features(returns_history)
        regime_result = regime_detector.detect_regime(features)
        vol_result = vol_tracker.estimate_volatility(returns_history)
        previous_state: LatentState = LatentState.default()
        predicted_state: LatentState = state_estimator.predict(previous_state)
        observation: dict = _build_observation_vector(regime_result, vol_result)
        _latent_state: LatentState = state_estimator.update(predicted_state, observation)

    # ------------------------------------------------------------------
    # Step 8: Risk assessment
    # ------------------------------------------------------------------
    risk_output = engine.assess(
        returns_history=returns_history,
        current_regime=current_regime,
        meta_uncertainty=meta_uncertainty,
    )

    # ------------------------------------------------------------------
    # Steps 9-11: Exposure -> positions -> return
    # ------------------------------------------------------------------
    exposure_weight: float = risk_output.exposure_weight
    positions: dict = route_exposure_to_positions(
        total_capital=total_capital,
        exposure_fraction=exposure_weight,
        asset_prices=asset_prices,
    )
    return positions


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def x_run_full_pipeline__mutmut_40(
    returns_history: list,
    current_regime: GlobalRegimeState,
    meta_uncertainty: float,
    total_capital: float,
    asset_prices: dict,
) -> dict:
    """
    Full deterministic pipeline from returns history to final positions.

    Step 0: Governance gate (GOV-01 + GOV-05 only).
    Steps 1-11: Unchanged from v1.1.0.

    Raises
    ------
    GovernanceViolationError
        meta_uncertainty out of [0.0, 1.0] or regime not GlobalRegimeState.
    ValueError
        Propagated from RiskEngine (invalid returns_history).
        Propagated from route_exposure_to_positions (invalid capital/prices).
    """
    # ------------------------------------------------------------------
    # Step 0: Governance Gate -- GOV-01 and GOV-05 only
    # ------------------------------------------------------------------

    # GOV-01: meta_uncertainty must be in [0.0, 1.0]
    _meta_invalid = (
        not isinstance(meta_uncertainty, (int, float))
        or not (0.0 <= float(meta_uncertainty) <= 1.0)
    )

    # GOV-05: regime must be a GlobalRegimeState instance
    _regime_invalid = not isinstance(current_regime, GlobalRegimeState)

    if _meta_invalid or _regime_invalid:
        # Build a minimal result via validate_pipeline_config using safe
        # stand-in values for parameters owned by downstream modules.
        _safe_capital = total_capital if (
            isinstance(total_capital, (int, float)) and float(total_capital) > 0
        ) else 1.0
        _safe_regime = current_regime if isinstance(
            current_regime, GlobalRegimeState
        ) else GlobalRegimeState.UNKNOWN
        _safe_meta = meta_uncertainty if (
            isinstance(meta_uncertainty, (int, float))
            and 0.0 <= float(meta_uncertainty) <= 1.0
        ) else 0.5

        _gov_result = validate_pipeline_config(
            meta_uncertainty=_safe_meta if not _meta_invalid else meta_uncertainty,
            initial_capital=_safe_capital,
            window=20,
            step=1,
            regime=_safe_regime,
            )
        # Only raise for the rules we gate on
        _gated_rules = {"GOV-01", "GOV-05"}
        _gated = [v for v in _gov_result.blocking_violations if v.rule_id in _gated_rules]
        # Also run with the actual bad value so the error message is accurate
        _real_result = validate_pipeline_config(
            meta_uncertainty=meta_uncertainty if isinstance(meta_uncertainty, (int, float)) else 999,
            initial_capital=_safe_capital,
            window=20,
            step=1,
            regime=current_regime,
            periods_per_year=252,
        )
        _real_gated = [v for v in _real_result.blocking_violations if v.rule_id in _gated_rules]
        if _real_gated:
            raise GovernanceViolationError(_real_result)

    # ------------------------------------------------------------------
    # Step 1: Instantiate all components fresh per call
    # ------------------------------------------------------------------
    engine: RiskEngine = RiskEngine()
    regime_detector: RegimeDetector = RegimeDetector()
    vol_tracker: VolatilityTracker = VolatilityTracker()
    state_estimator: StateEstimator = StateEstimator()

    # ------------------------------------------------------------------
    # Steps 2-7: State pipeline
    # ------------------------------------------------------------------
    if len(returns_history) > 0:
        features: dict = _extract_regime_features(returns_history)
        regime_result = regime_detector.detect_regime(features)
        vol_result = vol_tracker.estimate_volatility(returns_history)
        previous_state: LatentState = LatentState.default()
        predicted_state: LatentState = state_estimator.predict(previous_state)
        observation: dict = _build_observation_vector(regime_result, vol_result)
        _latent_state: LatentState = state_estimator.update(predicted_state, observation)

    # ------------------------------------------------------------------
    # Step 8: Risk assessment
    # ------------------------------------------------------------------
    risk_output = engine.assess(
        returns_history=returns_history,
        current_regime=current_regime,
        meta_uncertainty=meta_uncertainty,
    )

    # ------------------------------------------------------------------
    # Steps 9-11: Exposure -> positions -> return
    # ------------------------------------------------------------------
    exposure_weight: float = risk_output.exposure_weight
    positions: dict = route_exposure_to_positions(
        total_capital=total_capital,
        exposure_fraction=exposure_weight,
        asset_prices=asset_prices,
    )
    return positions


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def x_run_full_pipeline__mutmut_41(
    returns_history: list,
    current_regime: GlobalRegimeState,
    meta_uncertainty: float,
    total_capital: float,
    asset_prices: dict,
) -> dict:
    """
    Full deterministic pipeline from returns history to final positions.

    Step 0: Governance gate (GOV-01 + GOV-05 only).
    Steps 1-11: Unchanged from v1.1.0.

    Raises
    ------
    GovernanceViolationError
        meta_uncertainty out of [0.0, 1.0] or regime not GlobalRegimeState.
    ValueError
        Propagated from RiskEngine (invalid returns_history).
        Propagated from route_exposure_to_positions (invalid capital/prices).
    """
    # ------------------------------------------------------------------
    # Step 0: Governance Gate -- GOV-01 and GOV-05 only
    # ------------------------------------------------------------------

    # GOV-01: meta_uncertainty must be in [0.0, 1.0]
    _meta_invalid = (
        not isinstance(meta_uncertainty, (int, float))
        or not (0.0 <= float(meta_uncertainty) <= 1.0)
    )

    # GOV-05: regime must be a GlobalRegimeState instance
    _regime_invalid = not isinstance(current_regime, GlobalRegimeState)

    if _meta_invalid or _regime_invalid:
        # Build a minimal result via validate_pipeline_config using safe
        # stand-in values for parameters owned by downstream modules.
        _safe_capital = total_capital if (
            isinstance(total_capital, (int, float)) and float(total_capital) > 0
        ) else 1.0
        _safe_regime = current_regime if isinstance(
            current_regime, GlobalRegimeState
        ) else GlobalRegimeState.UNKNOWN
        _safe_meta = meta_uncertainty if (
            isinstance(meta_uncertainty, (int, float))
            and 0.0 <= float(meta_uncertainty) <= 1.0
        ) else 0.5

        _gov_result = validate_pipeline_config(
            meta_uncertainty=_safe_meta if _meta_invalid else meta_uncertainty,
            initial_capital=_safe_capital,
            window=20,
            step=1,
            regime=_safe_regime,
            periods_per_year=252,
        )
        # Only raise for the rules we gate on
        _gated_rules = {"GOV-01", "GOV-05"}
        _gated = [v for v in _gov_result.blocking_violations if v.rule_id in _gated_rules]
        # Also run with the actual bad value so the error message is accurate
        _real_result = validate_pipeline_config(
            meta_uncertainty=meta_uncertainty if isinstance(meta_uncertainty, (int, float)) else 999,
            initial_capital=_safe_capital,
            window=20,
            step=1,
            regime=current_regime,
            periods_per_year=252,
        )
        _real_gated = [v for v in _real_result.blocking_violations if v.rule_id in _gated_rules]
        if _real_gated:
            raise GovernanceViolationError(_real_result)

    # ------------------------------------------------------------------
    # Step 1: Instantiate all components fresh per call
    # ------------------------------------------------------------------
    engine: RiskEngine = RiskEngine()
    regime_detector: RegimeDetector = RegimeDetector()
    vol_tracker: VolatilityTracker = VolatilityTracker()
    state_estimator: StateEstimator = StateEstimator()

    # ------------------------------------------------------------------
    # Steps 2-7: State pipeline
    # ------------------------------------------------------------------
    if len(returns_history) > 0:
        features: dict = _extract_regime_features(returns_history)
        regime_result = regime_detector.detect_regime(features)
        vol_result = vol_tracker.estimate_volatility(returns_history)
        previous_state: LatentState = LatentState.default()
        predicted_state: LatentState = state_estimator.predict(previous_state)
        observation: dict = _build_observation_vector(regime_result, vol_result)
        _latent_state: LatentState = state_estimator.update(predicted_state, observation)

    # ------------------------------------------------------------------
    # Step 8: Risk assessment
    # ------------------------------------------------------------------
    risk_output = engine.assess(
        returns_history=returns_history,
        current_regime=current_regime,
        meta_uncertainty=meta_uncertainty,
    )

    # ------------------------------------------------------------------
    # Steps 9-11: Exposure -> positions -> return
    # ------------------------------------------------------------------
    exposure_weight: float = risk_output.exposure_weight
    positions: dict = route_exposure_to_positions(
        total_capital=total_capital,
        exposure_fraction=exposure_weight,
        asset_prices=asset_prices,
    )
    return positions


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def x_run_full_pipeline__mutmut_42(
    returns_history: list,
    current_regime: GlobalRegimeState,
    meta_uncertainty: float,
    total_capital: float,
    asset_prices: dict,
) -> dict:
    """
    Full deterministic pipeline from returns history to final positions.

    Step 0: Governance gate (GOV-01 + GOV-05 only).
    Steps 1-11: Unchanged from v1.1.0.

    Raises
    ------
    GovernanceViolationError
        meta_uncertainty out of [0.0, 1.0] or regime not GlobalRegimeState.
    ValueError
        Propagated from RiskEngine (invalid returns_history).
        Propagated from route_exposure_to_positions (invalid capital/prices).
    """
    # ------------------------------------------------------------------
    # Step 0: Governance Gate -- GOV-01 and GOV-05 only
    # ------------------------------------------------------------------

    # GOV-01: meta_uncertainty must be in [0.0, 1.0]
    _meta_invalid = (
        not isinstance(meta_uncertainty, (int, float))
        or not (0.0 <= float(meta_uncertainty) <= 1.0)
    )

    # GOV-05: regime must be a GlobalRegimeState instance
    _regime_invalid = not isinstance(current_regime, GlobalRegimeState)

    if _meta_invalid or _regime_invalid:
        # Build a minimal result via validate_pipeline_config using safe
        # stand-in values for parameters owned by downstream modules.
        _safe_capital = total_capital if (
            isinstance(total_capital, (int, float)) and float(total_capital) > 0
        ) else 1.0
        _safe_regime = current_regime if isinstance(
            current_regime, GlobalRegimeState
        ) else GlobalRegimeState.UNKNOWN
        _safe_meta = meta_uncertainty if (
            isinstance(meta_uncertainty, (int, float))
            and 0.0 <= float(meta_uncertainty) <= 1.0
        ) else 0.5

        _gov_result = validate_pipeline_config(
            meta_uncertainty=_safe_meta if not _meta_invalid else meta_uncertainty,
            initial_capital=_safe_capital,
            window=21,
            step=1,
            regime=_safe_regime,
            periods_per_year=252,
        )
        # Only raise for the rules we gate on
        _gated_rules = {"GOV-01", "GOV-05"}
        _gated = [v for v in _gov_result.blocking_violations if v.rule_id in _gated_rules]
        # Also run with the actual bad value so the error message is accurate
        _real_result = validate_pipeline_config(
            meta_uncertainty=meta_uncertainty if isinstance(meta_uncertainty, (int, float)) else 999,
            initial_capital=_safe_capital,
            window=20,
            step=1,
            regime=current_regime,
            periods_per_year=252,
        )
        _real_gated = [v for v in _real_result.blocking_violations if v.rule_id in _gated_rules]
        if _real_gated:
            raise GovernanceViolationError(_real_result)

    # ------------------------------------------------------------------
    # Step 1: Instantiate all components fresh per call
    # ------------------------------------------------------------------
    engine: RiskEngine = RiskEngine()
    regime_detector: RegimeDetector = RegimeDetector()
    vol_tracker: VolatilityTracker = VolatilityTracker()
    state_estimator: StateEstimator = StateEstimator()

    # ------------------------------------------------------------------
    # Steps 2-7: State pipeline
    # ------------------------------------------------------------------
    if len(returns_history) > 0:
        features: dict = _extract_regime_features(returns_history)
        regime_result = regime_detector.detect_regime(features)
        vol_result = vol_tracker.estimate_volatility(returns_history)
        previous_state: LatentState = LatentState.default()
        predicted_state: LatentState = state_estimator.predict(previous_state)
        observation: dict = _build_observation_vector(regime_result, vol_result)
        _latent_state: LatentState = state_estimator.update(predicted_state, observation)

    # ------------------------------------------------------------------
    # Step 8: Risk assessment
    # ------------------------------------------------------------------
    risk_output = engine.assess(
        returns_history=returns_history,
        current_regime=current_regime,
        meta_uncertainty=meta_uncertainty,
    )

    # ------------------------------------------------------------------
    # Steps 9-11: Exposure -> positions -> return
    # ------------------------------------------------------------------
    exposure_weight: float = risk_output.exposure_weight
    positions: dict = route_exposure_to_positions(
        total_capital=total_capital,
        exposure_fraction=exposure_weight,
        asset_prices=asset_prices,
    )
    return positions


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def x_run_full_pipeline__mutmut_43(
    returns_history: list,
    current_regime: GlobalRegimeState,
    meta_uncertainty: float,
    total_capital: float,
    asset_prices: dict,
) -> dict:
    """
    Full deterministic pipeline from returns history to final positions.

    Step 0: Governance gate (GOV-01 + GOV-05 only).
    Steps 1-11: Unchanged from v1.1.0.

    Raises
    ------
    GovernanceViolationError
        meta_uncertainty out of [0.0, 1.0] or regime not GlobalRegimeState.
    ValueError
        Propagated from RiskEngine (invalid returns_history).
        Propagated from route_exposure_to_positions (invalid capital/prices).
    """
    # ------------------------------------------------------------------
    # Step 0: Governance Gate -- GOV-01 and GOV-05 only
    # ------------------------------------------------------------------

    # GOV-01: meta_uncertainty must be in [0.0, 1.0]
    _meta_invalid = (
        not isinstance(meta_uncertainty, (int, float))
        or not (0.0 <= float(meta_uncertainty) <= 1.0)
    )

    # GOV-05: regime must be a GlobalRegimeState instance
    _regime_invalid = not isinstance(current_regime, GlobalRegimeState)

    if _meta_invalid or _regime_invalid:
        # Build a minimal result via validate_pipeline_config using safe
        # stand-in values for parameters owned by downstream modules.
        _safe_capital = total_capital if (
            isinstance(total_capital, (int, float)) and float(total_capital) > 0
        ) else 1.0
        _safe_regime = current_regime if isinstance(
            current_regime, GlobalRegimeState
        ) else GlobalRegimeState.UNKNOWN
        _safe_meta = meta_uncertainty if (
            isinstance(meta_uncertainty, (int, float))
            and 0.0 <= float(meta_uncertainty) <= 1.0
        ) else 0.5

        _gov_result = validate_pipeline_config(
            meta_uncertainty=_safe_meta if not _meta_invalid else meta_uncertainty,
            initial_capital=_safe_capital,
            window=20,
            step=2,
            regime=_safe_regime,
            periods_per_year=252,
        )
        # Only raise for the rules we gate on
        _gated_rules = {"GOV-01", "GOV-05"}
        _gated = [v for v in _gov_result.blocking_violations if v.rule_id in _gated_rules]
        # Also run with the actual bad value so the error message is accurate
        _real_result = validate_pipeline_config(
            meta_uncertainty=meta_uncertainty if isinstance(meta_uncertainty, (int, float)) else 999,
            initial_capital=_safe_capital,
            window=20,
            step=1,
            regime=current_regime,
            periods_per_year=252,
        )
        _real_gated = [v for v in _real_result.blocking_violations if v.rule_id in _gated_rules]
        if _real_gated:
            raise GovernanceViolationError(_real_result)

    # ------------------------------------------------------------------
    # Step 1: Instantiate all components fresh per call
    # ------------------------------------------------------------------
    engine: RiskEngine = RiskEngine()
    regime_detector: RegimeDetector = RegimeDetector()
    vol_tracker: VolatilityTracker = VolatilityTracker()
    state_estimator: StateEstimator = StateEstimator()

    # ------------------------------------------------------------------
    # Steps 2-7: State pipeline
    # ------------------------------------------------------------------
    if len(returns_history) > 0:
        features: dict = _extract_regime_features(returns_history)
        regime_result = regime_detector.detect_regime(features)
        vol_result = vol_tracker.estimate_volatility(returns_history)
        previous_state: LatentState = LatentState.default()
        predicted_state: LatentState = state_estimator.predict(previous_state)
        observation: dict = _build_observation_vector(regime_result, vol_result)
        _latent_state: LatentState = state_estimator.update(predicted_state, observation)

    # ------------------------------------------------------------------
    # Step 8: Risk assessment
    # ------------------------------------------------------------------
    risk_output = engine.assess(
        returns_history=returns_history,
        current_regime=current_regime,
        meta_uncertainty=meta_uncertainty,
    )

    # ------------------------------------------------------------------
    # Steps 9-11: Exposure -> positions -> return
    # ------------------------------------------------------------------
    exposure_weight: float = risk_output.exposure_weight
    positions: dict = route_exposure_to_positions(
        total_capital=total_capital,
        exposure_fraction=exposure_weight,
        asset_prices=asset_prices,
    )
    return positions


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def x_run_full_pipeline__mutmut_44(
    returns_history: list,
    current_regime: GlobalRegimeState,
    meta_uncertainty: float,
    total_capital: float,
    asset_prices: dict,
) -> dict:
    """
    Full deterministic pipeline from returns history to final positions.

    Step 0: Governance gate (GOV-01 + GOV-05 only).
    Steps 1-11: Unchanged from v1.1.0.

    Raises
    ------
    GovernanceViolationError
        meta_uncertainty out of [0.0, 1.0] or regime not GlobalRegimeState.
    ValueError
        Propagated from RiskEngine (invalid returns_history).
        Propagated from route_exposure_to_positions (invalid capital/prices).
    """
    # ------------------------------------------------------------------
    # Step 0: Governance Gate -- GOV-01 and GOV-05 only
    # ------------------------------------------------------------------

    # GOV-01: meta_uncertainty must be in [0.0, 1.0]
    _meta_invalid = (
        not isinstance(meta_uncertainty, (int, float))
        or not (0.0 <= float(meta_uncertainty) <= 1.0)
    )

    # GOV-05: regime must be a GlobalRegimeState instance
    _regime_invalid = not isinstance(current_regime, GlobalRegimeState)

    if _meta_invalid or _regime_invalid:
        # Build a minimal result via validate_pipeline_config using safe
        # stand-in values for parameters owned by downstream modules.
        _safe_capital = total_capital if (
            isinstance(total_capital, (int, float)) and float(total_capital) > 0
        ) else 1.0
        _safe_regime = current_regime if isinstance(
            current_regime, GlobalRegimeState
        ) else GlobalRegimeState.UNKNOWN
        _safe_meta = meta_uncertainty if (
            isinstance(meta_uncertainty, (int, float))
            and 0.0 <= float(meta_uncertainty) <= 1.0
        ) else 0.5

        _gov_result = validate_pipeline_config(
            meta_uncertainty=_safe_meta if not _meta_invalid else meta_uncertainty,
            initial_capital=_safe_capital,
            window=20,
            step=1,
            regime=_safe_regime,
            periods_per_year=253,
        )
        # Only raise for the rules we gate on
        _gated_rules = {"GOV-01", "GOV-05"}
        _gated = [v for v in _gov_result.blocking_violations if v.rule_id in _gated_rules]
        # Also run with the actual bad value so the error message is accurate
        _real_result = validate_pipeline_config(
            meta_uncertainty=meta_uncertainty if isinstance(meta_uncertainty, (int, float)) else 999,
            initial_capital=_safe_capital,
            window=20,
            step=1,
            regime=current_regime,
            periods_per_year=252,
        )
        _real_gated = [v for v in _real_result.blocking_violations if v.rule_id in _gated_rules]
        if _real_gated:
            raise GovernanceViolationError(_real_result)

    # ------------------------------------------------------------------
    # Step 1: Instantiate all components fresh per call
    # ------------------------------------------------------------------
    engine: RiskEngine = RiskEngine()
    regime_detector: RegimeDetector = RegimeDetector()
    vol_tracker: VolatilityTracker = VolatilityTracker()
    state_estimator: StateEstimator = StateEstimator()

    # ------------------------------------------------------------------
    # Steps 2-7: State pipeline
    # ------------------------------------------------------------------
    if len(returns_history) > 0:
        features: dict = _extract_regime_features(returns_history)
        regime_result = regime_detector.detect_regime(features)
        vol_result = vol_tracker.estimate_volatility(returns_history)
        previous_state: LatentState = LatentState.default()
        predicted_state: LatentState = state_estimator.predict(previous_state)
        observation: dict = _build_observation_vector(regime_result, vol_result)
        _latent_state: LatentState = state_estimator.update(predicted_state, observation)

    # ------------------------------------------------------------------
    # Step 8: Risk assessment
    # ------------------------------------------------------------------
    risk_output = engine.assess(
        returns_history=returns_history,
        current_regime=current_regime,
        meta_uncertainty=meta_uncertainty,
    )

    # ------------------------------------------------------------------
    # Steps 9-11: Exposure -> positions -> return
    # ------------------------------------------------------------------
    exposure_weight: float = risk_output.exposure_weight
    positions: dict = route_exposure_to_positions(
        total_capital=total_capital,
        exposure_fraction=exposure_weight,
        asset_prices=asset_prices,
    )
    return positions


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def x_run_full_pipeline__mutmut_45(
    returns_history: list,
    current_regime: GlobalRegimeState,
    meta_uncertainty: float,
    total_capital: float,
    asset_prices: dict,
) -> dict:
    """
    Full deterministic pipeline from returns history to final positions.

    Step 0: Governance gate (GOV-01 + GOV-05 only).
    Steps 1-11: Unchanged from v1.1.0.

    Raises
    ------
    GovernanceViolationError
        meta_uncertainty out of [0.0, 1.0] or regime not GlobalRegimeState.
    ValueError
        Propagated from RiskEngine (invalid returns_history).
        Propagated from route_exposure_to_positions (invalid capital/prices).
    """
    # ------------------------------------------------------------------
    # Step 0: Governance Gate -- GOV-01 and GOV-05 only
    # ------------------------------------------------------------------

    # GOV-01: meta_uncertainty must be in [0.0, 1.0]
    _meta_invalid = (
        not isinstance(meta_uncertainty, (int, float))
        or not (0.0 <= float(meta_uncertainty) <= 1.0)
    )

    # GOV-05: regime must be a GlobalRegimeState instance
    _regime_invalid = not isinstance(current_regime, GlobalRegimeState)

    if _meta_invalid or _regime_invalid:
        # Build a minimal result via validate_pipeline_config using safe
        # stand-in values for parameters owned by downstream modules.
        _safe_capital = total_capital if (
            isinstance(total_capital, (int, float)) and float(total_capital) > 0
        ) else 1.0
        _safe_regime = current_regime if isinstance(
            current_regime, GlobalRegimeState
        ) else GlobalRegimeState.UNKNOWN
        _safe_meta = meta_uncertainty if (
            isinstance(meta_uncertainty, (int, float))
            and 0.0 <= float(meta_uncertainty) <= 1.0
        ) else 0.5

        _gov_result = validate_pipeline_config(
            meta_uncertainty=_safe_meta if not _meta_invalid else meta_uncertainty,
            initial_capital=_safe_capital,
            window=20,
            step=1,
            regime=_safe_regime,
            periods_per_year=252,
        )
        # Only raise for the rules we gate on
        _gated_rules = None
        _gated = [v for v in _gov_result.blocking_violations if v.rule_id in _gated_rules]
        # Also run with the actual bad value so the error message is accurate
        _real_result = validate_pipeline_config(
            meta_uncertainty=meta_uncertainty if isinstance(meta_uncertainty, (int, float)) else 999,
            initial_capital=_safe_capital,
            window=20,
            step=1,
            regime=current_regime,
            periods_per_year=252,
        )
        _real_gated = [v for v in _real_result.blocking_violations if v.rule_id in _gated_rules]
        if _real_gated:
            raise GovernanceViolationError(_real_result)

    # ------------------------------------------------------------------
    # Step 1: Instantiate all components fresh per call
    # ------------------------------------------------------------------
    engine: RiskEngine = RiskEngine()
    regime_detector: RegimeDetector = RegimeDetector()
    vol_tracker: VolatilityTracker = VolatilityTracker()
    state_estimator: StateEstimator = StateEstimator()

    # ------------------------------------------------------------------
    # Steps 2-7: State pipeline
    # ------------------------------------------------------------------
    if len(returns_history) > 0:
        features: dict = _extract_regime_features(returns_history)
        regime_result = regime_detector.detect_regime(features)
        vol_result = vol_tracker.estimate_volatility(returns_history)
        previous_state: LatentState = LatentState.default()
        predicted_state: LatentState = state_estimator.predict(previous_state)
        observation: dict = _build_observation_vector(regime_result, vol_result)
        _latent_state: LatentState = state_estimator.update(predicted_state, observation)

    # ------------------------------------------------------------------
    # Step 8: Risk assessment
    # ------------------------------------------------------------------
    risk_output = engine.assess(
        returns_history=returns_history,
        current_regime=current_regime,
        meta_uncertainty=meta_uncertainty,
    )

    # ------------------------------------------------------------------
    # Steps 9-11: Exposure -> positions -> return
    # ------------------------------------------------------------------
    exposure_weight: float = risk_output.exposure_weight
    positions: dict = route_exposure_to_positions(
        total_capital=total_capital,
        exposure_fraction=exposure_weight,
        asset_prices=asset_prices,
    )
    return positions


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def x_run_full_pipeline__mutmut_46(
    returns_history: list,
    current_regime: GlobalRegimeState,
    meta_uncertainty: float,
    total_capital: float,
    asset_prices: dict,
) -> dict:
    """
    Full deterministic pipeline from returns history to final positions.

    Step 0: Governance gate (GOV-01 + GOV-05 only).
    Steps 1-11: Unchanged from v1.1.0.

    Raises
    ------
    GovernanceViolationError
        meta_uncertainty out of [0.0, 1.0] or regime not GlobalRegimeState.
    ValueError
        Propagated from RiskEngine (invalid returns_history).
        Propagated from route_exposure_to_positions (invalid capital/prices).
    """
    # ------------------------------------------------------------------
    # Step 0: Governance Gate -- GOV-01 and GOV-05 only
    # ------------------------------------------------------------------

    # GOV-01: meta_uncertainty must be in [0.0, 1.0]
    _meta_invalid = (
        not isinstance(meta_uncertainty, (int, float))
        or not (0.0 <= float(meta_uncertainty) <= 1.0)
    )

    # GOV-05: regime must be a GlobalRegimeState instance
    _regime_invalid = not isinstance(current_regime, GlobalRegimeState)

    if _meta_invalid or _regime_invalid:
        # Build a minimal result via validate_pipeline_config using safe
        # stand-in values for parameters owned by downstream modules.
        _safe_capital = total_capital if (
            isinstance(total_capital, (int, float)) and float(total_capital) > 0
        ) else 1.0
        _safe_regime = current_regime if isinstance(
            current_regime, GlobalRegimeState
        ) else GlobalRegimeState.UNKNOWN
        _safe_meta = meta_uncertainty if (
            isinstance(meta_uncertainty, (int, float))
            and 0.0 <= float(meta_uncertainty) <= 1.0
        ) else 0.5

        _gov_result = validate_pipeline_config(
            meta_uncertainty=_safe_meta if not _meta_invalid else meta_uncertainty,
            initial_capital=_safe_capital,
            window=20,
            step=1,
            regime=_safe_regime,
            periods_per_year=252,
        )
        # Only raise for the rules we gate on
        _gated_rules = {"XXGOV-01XX", "GOV-05"}
        _gated = [v for v in _gov_result.blocking_violations if v.rule_id in _gated_rules]
        # Also run with the actual bad value so the error message is accurate
        _real_result = validate_pipeline_config(
            meta_uncertainty=meta_uncertainty if isinstance(meta_uncertainty, (int, float)) else 999,
            initial_capital=_safe_capital,
            window=20,
            step=1,
            regime=current_regime,
            periods_per_year=252,
        )
        _real_gated = [v for v in _real_result.blocking_violations if v.rule_id in _gated_rules]
        if _real_gated:
            raise GovernanceViolationError(_real_result)

    # ------------------------------------------------------------------
    # Step 1: Instantiate all components fresh per call
    # ------------------------------------------------------------------
    engine: RiskEngine = RiskEngine()
    regime_detector: RegimeDetector = RegimeDetector()
    vol_tracker: VolatilityTracker = VolatilityTracker()
    state_estimator: StateEstimator = StateEstimator()

    # ------------------------------------------------------------------
    # Steps 2-7: State pipeline
    # ------------------------------------------------------------------
    if len(returns_history) > 0:
        features: dict = _extract_regime_features(returns_history)
        regime_result = regime_detector.detect_regime(features)
        vol_result = vol_tracker.estimate_volatility(returns_history)
        previous_state: LatentState = LatentState.default()
        predicted_state: LatentState = state_estimator.predict(previous_state)
        observation: dict = _build_observation_vector(regime_result, vol_result)
        _latent_state: LatentState = state_estimator.update(predicted_state, observation)

    # ------------------------------------------------------------------
    # Step 8: Risk assessment
    # ------------------------------------------------------------------
    risk_output = engine.assess(
        returns_history=returns_history,
        current_regime=current_regime,
        meta_uncertainty=meta_uncertainty,
    )

    # ------------------------------------------------------------------
    # Steps 9-11: Exposure -> positions -> return
    # ------------------------------------------------------------------
    exposure_weight: float = risk_output.exposure_weight
    positions: dict = route_exposure_to_positions(
        total_capital=total_capital,
        exposure_fraction=exposure_weight,
        asset_prices=asset_prices,
    )
    return positions


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def x_run_full_pipeline__mutmut_47(
    returns_history: list,
    current_regime: GlobalRegimeState,
    meta_uncertainty: float,
    total_capital: float,
    asset_prices: dict,
) -> dict:
    """
    Full deterministic pipeline from returns history to final positions.

    Step 0: Governance gate (GOV-01 + GOV-05 only).
    Steps 1-11: Unchanged from v1.1.0.

    Raises
    ------
    GovernanceViolationError
        meta_uncertainty out of [0.0, 1.0] or regime not GlobalRegimeState.
    ValueError
        Propagated from RiskEngine (invalid returns_history).
        Propagated from route_exposure_to_positions (invalid capital/prices).
    """
    # ------------------------------------------------------------------
    # Step 0: Governance Gate -- GOV-01 and GOV-05 only
    # ------------------------------------------------------------------

    # GOV-01: meta_uncertainty must be in [0.0, 1.0]
    _meta_invalid = (
        not isinstance(meta_uncertainty, (int, float))
        or not (0.0 <= float(meta_uncertainty) <= 1.0)
    )

    # GOV-05: regime must be a GlobalRegimeState instance
    _regime_invalid = not isinstance(current_regime, GlobalRegimeState)

    if _meta_invalid or _regime_invalid:
        # Build a minimal result via validate_pipeline_config using safe
        # stand-in values for parameters owned by downstream modules.
        _safe_capital = total_capital if (
            isinstance(total_capital, (int, float)) and float(total_capital) > 0
        ) else 1.0
        _safe_regime = current_regime if isinstance(
            current_regime, GlobalRegimeState
        ) else GlobalRegimeState.UNKNOWN
        _safe_meta = meta_uncertainty if (
            isinstance(meta_uncertainty, (int, float))
            and 0.0 <= float(meta_uncertainty) <= 1.0
        ) else 0.5

        _gov_result = validate_pipeline_config(
            meta_uncertainty=_safe_meta if not _meta_invalid else meta_uncertainty,
            initial_capital=_safe_capital,
            window=20,
            step=1,
            regime=_safe_regime,
            periods_per_year=252,
        )
        # Only raise for the rules we gate on
        _gated_rules = {"gov-01", "GOV-05"}
        _gated = [v for v in _gov_result.blocking_violations if v.rule_id in _gated_rules]
        # Also run with the actual bad value so the error message is accurate
        _real_result = validate_pipeline_config(
            meta_uncertainty=meta_uncertainty if isinstance(meta_uncertainty, (int, float)) else 999,
            initial_capital=_safe_capital,
            window=20,
            step=1,
            regime=current_regime,
            periods_per_year=252,
        )
        _real_gated = [v for v in _real_result.blocking_violations if v.rule_id in _gated_rules]
        if _real_gated:
            raise GovernanceViolationError(_real_result)

    # ------------------------------------------------------------------
    # Step 1: Instantiate all components fresh per call
    # ------------------------------------------------------------------
    engine: RiskEngine = RiskEngine()
    regime_detector: RegimeDetector = RegimeDetector()
    vol_tracker: VolatilityTracker = VolatilityTracker()
    state_estimator: StateEstimator = StateEstimator()

    # ------------------------------------------------------------------
    # Steps 2-7: State pipeline
    # ------------------------------------------------------------------
    if len(returns_history) > 0:
        features: dict = _extract_regime_features(returns_history)
        regime_result = regime_detector.detect_regime(features)
        vol_result = vol_tracker.estimate_volatility(returns_history)
        previous_state: LatentState = LatentState.default()
        predicted_state: LatentState = state_estimator.predict(previous_state)
        observation: dict = _build_observation_vector(regime_result, vol_result)
        _latent_state: LatentState = state_estimator.update(predicted_state, observation)

    # ------------------------------------------------------------------
    # Step 8: Risk assessment
    # ------------------------------------------------------------------
    risk_output = engine.assess(
        returns_history=returns_history,
        current_regime=current_regime,
        meta_uncertainty=meta_uncertainty,
    )

    # ------------------------------------------------------------------
    # Steps 9-11: Exposure -> positions -> return
    # ------------------------------------------------------------------
    exposure_weight: float = risk_output.exposure_weight
    positions: dict = route_exposure_to_positions(
        total_capital=total_capital,
        exposure_fraction=exposure_weight,
        asset_prices=asset_prices,
    )
    return positions


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def x_run_full_pipeline__mutmut_48(
    returns_history: list,
    current_regime: GlobalRegimeState,
    meta_uncertainty: float,
    total_capital: float,
    asset_prices: dict,
) -> dict:
    """
    Full deterministic pipeline from returns history to final positions.

    Step 0: Governance gate (GOV-01 + GOV-05 only).
    Steps 1-11: Unchanged from v1.1.0.

    Raises
    ------
    GovernanceViolationError
        meta_uncertainty out of [0.0, 1.0] or regime not GlobalRegimeState.
    ValueError
        Propagated from RiskEngine (invalid returns_history).
        Propagated from route_exposure_to_positions (invalid capital/prices).
    """
    # ------------------------------------------------------------------
    # Step 0: Governance Gate -- GOV-01 and GOV-05 only
    # ------------------------------------------------------------------

    # GOV-01: meta_uncertainty must be in [0.0, 1.0]
    _meta_invalid = (
        not isinstance(meta_uncertainty, (int, float))
        or not (0.0 <= float(meta_uncertainty) <= 1.0)
    )

    # GOV-05: regime must be a GlobalRegimeState instance
    _regime_invalid = not isinstance(current_regime, GlobalRegimeState)

    if _meta_invalid or _regime_invalid:
        # Build a minimal result via validate_pipeline_config using safe
        # stand-in values for parameters owned by downstream modules.
        _safe_capital = total_capital if (
            isinstance(total_capital, (int, float)) and float(total_capital) > 0
        ) else 1.0
        _safe_regime = current_regime if isinstance(
            current_regime, GlobalRegimeState
        ) else GlobalRegimeState.UNKNOWN
        _safe_meta = meta_uncertainty if (
            isinstance(meta_uncertainty, (int, float))
            and 0.0 <= float(meta_uncertainty) <= 1.0
        ) else 0.5

        _gov_result = validate_pipeline_config(
            meta_uncertainty=_safe_meta if not _meta_invalid else meta_uncertainty,
            initial_capital=_safe_capital,
            window=20,
            step=1,
            regime=_safe_regime,
            periods_per_year=252,
        )
        # Only raise for the rules we gate on
        _gated_rules = {"GOV-01", "XXGOV-05XX"}
        _gated = [v for v in _gov_result.blocking_violations if v.rule_id in _gated_rules]
        # Also run with the actual bad value so the error message is accurate
        _real_result = validate_pipeline_config(
            meta_uncertainty=meta_uncertainty if isinstance(meta_uncertainty, (int, float)) else 999,
            initial_capital=_safe_capital,
            window=20,
            step=1,
            regime=current_regime,
            periods_per_year=252,
        )
        _real_gated = [v for v in _real_result.blocking_violations if v.rule_id in _gated_rules]
        if _real_gated:
            raise GovernanceViolationError(_real_result)

    # ------------------------------------------------------------------
    # Step 1: Instantiate all components fresh per call
    # ------------------------------------------------------------------
    engine: RiskEngine = RiskEngine()
    regime_detector: RegimeDetector = RegimeDetector()
    vol_tracker: VolatilityTracker = VolatilityTracker()
    state_estimator: StateEstimator = StateEstimator()

    # ------------------------------------------------------------------
    # Steps 2-7: State pipeline
    # ------------------------------------------------------------------
    if len(returns_history) > 0:
        features: dict = _extract_regime_features(returns_history)
        regime_result = regime_detector.detect_regime(features)
        vol_result = vol_tracker.estimate_volatility(returns_history)
        previous_state: LatentState = LatentState.default()
        predicted_state: LatentState = state_estimator.predict(previous_state)
        observation: dict = _build_observation_vector(regime_result, vol_result)
        _latent_state: LatentState = state_estimator.update(predicted_state, observation)

    # ------------------------------------------------------------------
    # Step 8: Risk assessment
    # ------------------------------------------------------------------
    risk_output = engine.assess(
        returns_history=returns_history,
        current_regime=current_regime,
        meta_uncertainty=meta_uncertainty,
    )

    # ------------------------------------------------------------------
    # Steps 9-11: Exposure -> positions -> return
    # ------------------------------------------------------------------
    exposure_weight: float = risk_output.exposure_weight
    positions: dict = route_exposure_to_positions(
        total_capital=total_capital,
        exposure_fraction=exposure_weight,
        asset_prices=asset_prices,
    )
    return positions


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def x_run_full_pipeline__mutmut_49(
    returns_history: list,
    current_regime: GlobalRegimeState,
    meta_uncertainty: float,
    total_capital: float,
    asset_prices: dict,
) -> dict:
    """
    Full deterministic pipeline from returns history to final positions.

    Step 0: Governance gate (GOV-01 + GOV-05 only).
    Steps 1-11: Unchanged from v1.1.0.

    Raises
    ------
    GovernanceViolationError
        meta_uncertainty out of [0.0, 1.0] or regime not GlobalRegimeState.
    ValueError
        Propagated from RiskEngine (invalid returns_history).
        Propagated from route_exposure_to_positions (invalid capital/prices).
    """
    # ------------------------------------------------------------------
    # Step 0: Governance Gate -- GOV-01 and GOV-05 only
    # ------------------------------------------------------------------

    # GOV-01: meta_uncertainty must be in [0.0, 1.0]
    _meta_invalid = (
        not isinstance(meta_uncertainty, (int, float))
        or not (0.0 <= float(meta_uncertainty) <= 1.0)
    )

    # GOV-05: regime must be a GlobalRegimeState instance
    _regime_invalid = not isinstance(current_regime, GlobalRegimeState)

    if _meta_invalid or _regime_invalid:
        # Build a minimal result via validate_pipeline_config using safe
        # stand-in values for parameters owned by downstream modules.
        _safe_capital = total_capital if (
            isinstance(total_capital, (int, float)) and float(total_capital) > 0
        ) else 1.0
        _safe_regime = current_regime if isinstance(
            current_regime, GlobalRegimeState
        ) else GlobalRegimeState.UNKNOWN
        _safe_meta = meta_uncertainty if (
            isinstance(meta_uncertainty, (int, float))
            and 0.0 <= float(meta_uncertainty) <= 1.0
        ) else 0.5

        _gov_result = validate_pipeline_config(
            meta_uncertainty=_safe_meta if not _meta_invalid else meta_uncertainty,
            initial_capital=_safe_capital,
            window=20,
            step=1,
            regime=_safe_regime,
            periods_per_year=252,
        )
        # Only raise for the rules we gate on
        _gated_rules = {"GOV-01", "gov-05"}
        _gated = [v for v in _gov_result.blocking_violations if v.rule_id in _gated_rules]
        # Also run with the actual bad value so the error message is accurate
        _real_result = validate_pipeline_config(
            meta_uncertainty=meta_uncertainty if isinstance(meta_uncertainty, (int, float)) else 999,
            initial_capital=_safe_capital,
            window=20,
            step=1,
            regime=current_regime,
            periods_per_year=252,
        )
        _real_gated = [v for v in _real_result.blocking_violations if v.rule_id in _gated_rules]
        if _real_gated:
            raise GovernanceViolationError(_real_result)

    # ------------------------------------------------------------------
    # Step 1: Instantiate all components fresh per call
    # ------------------------------------------------------------------
    engine: RiskEngine = RiskEngine()
    regime_detector: RegimeDetector = RegimeDetector()
    vol_tracker: VolatilityTracker = VolatilityTracker()
    state_estimator: StateEstimator = StateEstimator()

    # ------------------------------------------------------------------
    # Steps 2-7: State pipeline
    # ------------------------------------------------------------------
    if len(returns_history) > 0:
        features: dict = _extract_regime_features(returns_history)
        regime_result = regime_detector.detect_regime(features)
        vol_result = vol_tracker.estimate_volatility(returns_history)
        previous_state: LatentState = LatentState.default()
        predicted_state: LatentState = state_estimator.predict(previous_state)
        observation: dict = _build_observation_vector(regime_result, vol_result)
        _latent_state: LatentState = state_estimator.update(predicted_state, observation)

    # ------------------------------------------------------------------
    # Step 8: Risk assessment
    # ------------------------------------------------------------------
    risk_output = engine.assess(
        returns_history=returns_history,
        current_regime=current_regime,
        meta_uncertainty=meta_uncertainty,
    )

    # ------------------------------------------------------------------
    # Steps 9-11: Exposure -> positions -> return
    # ------------------------------------------------------------------
    exposure_weight: float = risk_output.exposure_weight
    positions: dict = route_exposure_to_positions(
        total_capital=total_capital,
        exposure_fraction=exposure_weight,
        asset_prices=asset_prices,
    )
    return positions


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def x_run_full_pipeline__mutmut_50(
    returns_history: list,
    current_regime: GlobalRegimeState,
    meta_uncertainty: float,
    total_capital: float,
    asset_prices: dict,
) -> dict:
    """
    Full deterministic pipeline from returns history to final positions.

    Step 0: Governance gate (GOV-01 + GOV-05 only).
    Steps 1-11: Unchanged from v1.1.0.

    Raises
    ------
    GovernanceViolationError
        meta_uncertainty out of [0.0, 1.0] or regime not GlobalRegimeState.
    ValueError
        Propagated from RiskEngine (invalid returns_history).
        Propagated from route_exposure_to_positions (invalid capital/prices).
    """
    # ------------------------------------------------------------------
    # Step 0: Governance Gate -- GOV-01 and GOV-05 only
    # ------------------------------------------------------------------

    # GOV-01: meta_uncertainty must be in [0.0, 1.0]
    _meta_invalid = (
        not isinstance(meta_uncertainty, (int, float))
        or not (0.0 <= float(meta_uncertainty) <= 1.0)
    )

    # GOV-05: regime must be a GlobalRegimeState instance
    _regime_invalid = not isinstance(current_regime, GlobalRegimeState)

    if _meta_invalid or _regime_invalid:
        # Build a minimal result via validate_pipeline_config using safe
        # stand-in values for parameters owned by downstream modules.
        _safe_capital = total_capital if (
            isinstance(total_capital, (int, float)) and float(total_capital) > 0
        ) else 1.0
        _safe_regime = current_regime if isinstance(
            current_regime, GlobalRegimeState
        ) else GlobalRegimeState.UNKNOWN
        _safe_meta = meta_uncertainty if (
            isinstance(meta_uncertainty, (int, float))
            and 0.0 <= float(meta_uncertainty) <= 1.0
        ) else 0.5

        _gov_result = validate_pipeline_config(
            meta_uncertainty=_safe_meta if not _meta_invalid else meta_uncertainty,
            initial_capital=_safe_capital,
            window=20,
            step=1,
            regime=_safe_regime,
            periods_per_year=252,
        )
        # Only raise for the rules we gate on
        _gated_rules = {"GOV-01", "GOV-05"}
        _gated = None
        # Also run with the actual bad value so the error message is accurate
        _real_result = validate_pipeline_config(
            meta_uncertainty=meta_uncertainty if isinstance(meta_uncertainty, (int, float)) else 999,
            initial_capital=_safe_capital,
            window=20,
            step=1,
            regime=current_regime,
            periods_per_year=252,
        )
        _real_gated = [v for v in _real_result.blocking_violations if v.rule_id in _gated_rules]
        if _real_gated:
            raise GovernanceViolationError(_real_result)

    # ------------------------------------------------------------------
    # Step 1: Instantiate all components fresh per call
    # ------------------------------------------------------------------
    engine: RiskEngine = RiskEngine()
    regime_detector: RegimeDetector = RegimeDetector()
    vol_tracker: VolatilityTracker = VolatilityTracker()
    state_estimator: StateEstimator = StateEstimator()

    # ------------------------------------------------------------------
    # Steps 2-7: State pipeline
    # ------------------------------------------------------------------
    if len(returns_history) > 0:
        features: dict = _extract_regime_features(returns_history)
        regime_result = regime_detector.detect_regime(features)
        vol_result = vol_tracker.estimate_volatility(returns_history)
        previous_state: LatentState = LatentState.default()
        predicted_state: LatentState = state_estimator.predict(previous_state)
        observation: dict = _build_observation_vector(regime_result, vol_result)
        _latent_state: LatentState = state_estimator.update(predicted_state, observation)

    # ------------------------------------------------------------------
    # Step 8: Risk assessment
    # ------------------------------------------------------------------
    risk_output = engine.assess(
        returns_history=returns_history,
        current_regime=current_regime,
        meta_uncertainty=meta_uncertainty,
    )

    # ------------------------------------------------------------------
    # Steps 9-11: Exposure -> positions -> return
    # ------------------------------------------------------------------
    exposure_weight: float = risk_output.exposure_weight
    positions: dict = route_exposure_to_positions(
        total_capital=total_capital,
        exposure_fraction=exposure_weight,
        asset_prices=asset_prices,
    )
    return positions


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def x_run_full_pipeline__mutmut_51(
    returns_history: list,
    current_regime: GlobalRegimeState,
    meta_uncertainty: float,
    total_capital: float,
    asset_prices: dict,
) -> dict:
    """
    Full deterministic pipeline from returns history to final positions.

    Step 0: Governance gate (GOV-01 + GOV-05 only).
    Steps 1-11: Unchanged from v1.1.0.

    Raises
    ------
    GovernanceViolationError
        meta_uncertainty out of [0.0, 1.0] or regime not GlobalRegimeState.
    ValueError
        Propagated from RiskEngine (invalid returns_history).
        Propagated from route_exposure_to_positions (invalid capital/prices).
    """
    # ------------------------------------------------------------------
    # Step 0: Governance Gate -- GOV-01 and GOV-05 only
    # ------------------------------------------------------------------

    # GOV-01: meta_uncertainty must be in [0.0, 1.0]
    _meta_invalid = (
        not isinstance(meta_uncertainty, (int, float))
        or not (0.0 <= float(meta_uncertainty) <= 1.0)
    )

    # GOV-05: regime must be a GlobalRegimeState instance
    _regime_invalid = not isinstance(current_regime, GlobalRegimeState)

    if _meta_invalid or _regime_invalid:
        # Build a minimal result via validate_pipeline_config using safe
        # stand-in values for parameters owned by downstream modules.
        _safe_capital = total_capital if (
            isinstance(total_capital, (int, float)) and float(total_capital) > 0
        ) else 1.0
        _safe_regime = current_regime if isinstance(
            current_regime, GlobalRegimeState
        ) else GlobalRegimeState.UNKNOWN
        _safe_meta = meta_uncertainty if (
            isinstance(meta_uncertainty, (int, float))
            and 0.0 <= float(meta_uncertainty) <= 1.0
        ) else 0.5

        _gov_result = validate_pipeline_config(
            meta_uncertainty=_safe_meta if not _meta_invalid else meta_uncertainty,
            initial_capital=_safe_capital,
            window=20,
            step=1,
            regime=_safe_regime,
            periods_per_year=252,
        )
        # Only raise for the rules we gate on
        _gated_rules = {"GOV-01", "GOV-05"}
        _gated = [v for v in _gov_result.blocking_violations if v.rule_id not in _gated_rules]
        # Also run with the actual bad value so the error message is accurate
        _real_result = validate_pipeline_config(
            meta_uncertainty=meta_uncertainty if isinstance(meta_uncertainty, (int, float)) else 999,
            initial_capital=_safe_capital,
            window=20,
            step=1,
            regime=current_regime,
            periods_per_year=252,
        )
        _real_gated = [v for v in _real_result.blocking_violations if v.rule_id in _gated_rules]
        if _real_gated:
            raise GovernanceViolationError(_real_result)

    # ------------------------------------------------------------------
    # Step 1: Instantiate all components fresh per call
    # ------------------------------------------------------------------
    engine: RiskEngine = RiskEngine()
    regime_detector: RegimeDetector = RegimeDetector()
    vol_tracker: VolatilityTracker = VolatilityTracker()
    state_estimator: StateEstimator = StateEstimator()

    # ------------------------------------------------------------------
    # Steps 2-7: State pipeline
    # ------------------------------------------------------------------
    if len(returns_history) > 0:
        features: dict = _extract_regime_features(returns_history)
        regime_result = regime_detector.detect_regime(features)
        vol_result = vol_tracker.estimate_volatility(returns_history)
        previous_state: LatentState = LatentState.default()
        predicted_state: LatentState = state_estimator.predict(previous_state)
        observation: dict = _build_observation_vector(regime_result, vol_result)
        _latent_state: LatentState = state_estimator.update(predicted_state, observation)

    # ------------------------------------------------------------------
    # Step 8: Risk assessment
    # ------------------------------------------------------------------
    risk_output = engine.assess(
        returns_history=returns_history,
        current_regime=current_regime,
        meta_uncertainty=meta_uncertainty,
    )

    # ------------------------------------------------------------------
    # Steps 9-11: Exposure -> positions -> return
    # ------------------------------------------------------------------
    exposure_weight: float = risk_output.exposure_weight
    positions: dict = route_exposure_to_positions(
        total_capital=total_capital,
        exposure_fraction=exposure_weight,
        asset_prices=asset_prices,
    )
    return positions


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def x_run_full_pipeline__mutmut_52(
    returns_history: list,
    current_regime: GlobalRegimeState,
    meta_uncertainty: float,
    total_capital: float,
    asset_prices: dict,
) -> dict:
    """
    Full deterministic pipeline from returns history to final positions.

    Step 0: Governance gate (GOV-01 + GOV-05 only).
    Steps 1-11: Unchanged from v1.1.0.

    Raises
    ------
    GovernanceViolationError
        meta_uncertainty out of [0.0, 1.0] or regime not GlobalRegimeState.
    ValueError
        Propagated from RiskEngine (invalid returns_history).
        Propagated from route_exposure_to_positions (invalid capital/prices).
    """
    # ------------------------------------------------------------------
    # Step 0: Governance Gate -- GOV-01 and GOV-05 only
    # ------------------------------------------------------------------

    # GOV-01: meta_uncertainty must be in [0.0, 1.0]
    _meta_invalid = (
        not isinstance(meta_uncertainty, (int, float))
        or not (0.0 <= float(meta_uncertainty) <= 1.0)
    )

    # GOV-05: regime must be a GlobalRegimeState instance
    _regime_invalid = not isinstance(current_regime, GlobalRegimeState)

    if _meta_invalid or _regime_invalid:
        # Build a minimal result via validate_pipeline_config using safe
        # stand-in values for parameters owned by downstream modules.
        _safe_capital = total_capital if (
            isinstance(total_capital, (int, float)) and float(total_capital) > 0
        ) else 1.0
        _safe_regime = current_regime if isinstance(
            current_regime, GlobalRegimeState
        ) else GlobalRegimeState.UNKNOWN
        _safe_meta = meta_uncertainty if (
            isinstance(meta_uncertainty, (int, float))
            and 0.0 <= float(meta_uncertainty) <= 1.0
        ) else 0.5

        _gov_result = validate_pipeline_config(
            meta_uncertainty=_safe_meta if not _meta_invalid else meta_uncertainty,
            initial_capital=_safe_capital,
            window=20,
            step=1,
            regime=_safe_regime,
            periods_per_year=252,
        )
        # Only raise for the rules we gate on
        _gated_rules = {"GOV-01", "GOV-05"}
        _gated = [v for v in _gov_result.blocking_violations if v.rule_id in _gated_rules]
        # Also run with the actual bad value so the error message is accurate
        _real_result = None
        _real_gated = [v for v in _real_result.blocking_violations if v.rule_id in _gated_rules]
        if _real_gated:
            raise GovernanceViolationError(_real_result)

    # ------------------------------------------------------------------
    # Step 1: Instantiate all components fresh per call
    # ------------------------------------------------------------------
    engine: RiskEngine = RiskEngine()
    regime_detector: RegimeDetector = RegimeDetector()
    vol_tracker: VolatilityTracker = VolatilityTracker()
    state_estimator: StateEstimator = StateEstimator()

    # ------------------------------------------------------------------
    # Steps 2-7: State pipeline
    # ------------------------------------------------------------------
    if len(returns_history) > 0:
        features: dict = _extract_regime_features(returns_history)
        regime_result = regime_detector.detect_regime(features)
        vol_result = vol_tracker.estimate_volatility(returns_history)
        previous_state: LatentState = LatentState.default()
        predicted_state: LatentState = state_estimator.predict(previous_state)
        observation: dict = _build_observation_vector(regime_result, vol_result)
        _latent_state: LatentState = state_estimator.update(predicted_state, observation)

    # ------------------------------------------------------------------
    # Step 8: Risk assessment
    # ------------------------------------------------------------------
    risk_output = engine.assess(
        returns_history=returns_history,
        current_regime=current_regime,
        meta_uncertainty=meta_uncertainty,
    )

    # ------------------------------------------------------------------
    # Steps 9-11: Exposure -> positions -> return
    # ------------------------------------------------------------------
    exposure_weight: float = risk_output.exposure_weight
    positions: dict = route_exposure_to_positions(
        total_capital=total_capital,
        exposure_fraction=exposure_weight,
        asset_prices=asset_prices,
    )
    return positions


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def x_run_full_pipeline__mutmut_53(
    returns_history: list,
    current_regime: GlobalRegimeState,
    meta_uncertainty: float,
    total_capital: float,
    asset_prices: dict,
) -> dict:
    """
    Full deterministic pipeline from returns history to final positions.

    Step 0: Governance gate (GOV-01 + GOV-05 only).
    Steps 1-11: Unchanged from v1.1.0.

    Raises
    ------
    GovernanceViolationError
        meta_uncertainty out of [0.0, 1.0] or regime not GlobalRegimeState.
    ValueError
        Propagated from RiskEngine (invalid returns_history).
        Propagated from route_exposure_to_positions (invalid capital/prices).
    """
    # ------------------------------------------------------------------
    # Step 0: Governance Gate -- GOV-01 and GOV-05 only
    # ------------------------------------------------------------------

    # GOV-01: meta_uncertainty must be in [0.0, 1.0]
    _meta_invalid = (
        not isinstance(meta_uncertainty, (int, float))
        or not (0.0 <= float(meta_uncertainty) <= 1.0)
    )

    # GOV-05: regime must be a GlobalRegimeState instance
    _regime_invalid = not isinstance(current_regime, GlobalRegimeState)

    if _meta_invalid or _regime_invalid:
        # Build a minimal result via validate_pipeline_config using safe
        # stand-in values for parameters owned by downstream modules.
        _safe_capital = total_capital if (
            isinstance(total_capital, (int, float)) and float(total_capital) > 0
        ) else 1.0
        _safe_regime = current_regime if isinstance(
            current_regime, GlobalRegimeState
        ) else GlobalRegimeState.UNKNOWN
        _safe_meta = meta_uncertainty if (
            isinstance(meta_uncertainty, (int, float))
            and 0.0 <= float(meta_uncertainty) <= 1.0
        ) else 0.5

        _gov_result = validate_pipeline_config(
            meta_uncertainty=_safe_meta if not _meta_invalid else meta_uncertainty,
            initial_capital=_safe_capital,
            window=20,
            step=1,
            regime=_safe_regime,
            periods_per_year=252,
        )
        # Only raise for the rules we gate on
        _gated_rules = {"GOV-01", "GOV-05"}
        _gated = [v for v in _gov_result.blocking_violations if v.rule_id in _gated_rules]
        # Also run with the actual bad value so the error message is accurate
        _real_result = validate_pipeline_config(
            meta_uncertainty=None,
            initial_capital=_safe_capital,
            window=20,
            step=1,
            regime=current_regime,
            periods_per_year=252,
        )
        _real_gated = [v for v in _real_result.blocking_violations if v.rule_id in _gated_rules]
        if _real_gated:
            raise GovernanceViolationError(_real_result)

    # ------------------------------------------------------------------
    # Step 1: Instantiate all components fresh per call
    # ------------------------------------------------------------------
    engine: RiskEngine = RiskEngine()
    regime_detector: RegimeDetector = RegimeDetector()
    vol_tracker: VolatilityTracker = VolatilityTracker()
    state_estimator: StateEstimator = StateEstimator()

    # ------------------------------------------------------------------
    # Steps 2-7: State pipeline
    # ------------------------------------------------------------------
    if len(returns_history) > 0:
        features: dict = _extract_regime_features(returns_history)
        regime_result = regime_detector.detect_regime(features)
        vol_result = vol_tracker.estimate_volatility(returns_history)
        previous_state: LatentState = LatentState.default()
        predicted_state: LatentState = state_estimator.predict(previous_state)
        observation: dict = _build_observation_vector(regime_result, vol_result)
        _latent_state: LatentState = state_estimator.update(predicted_state, observation)

    # ------------------------------------------------------------------
    # Step 8: Risk assessment
    # ------------------------------------------------------------------
    risk_output = engine.assess(
        returns_history=returns_history,
        current_regime=current_regime,
        meta_uncertainty=meta_uncertainty,
    )

    # ------------------------------------------------------------------
    # Steps 9-11: Exposure -> positions -> return
    # ------------------------------------------------------------------
    exposure_weight: float = risk_output.exposure_weight
    positions: dict = route_exposure_to_positions(
        total_capital=total_capital,
        exposure_fraction=exposure_weight,
        asset_prices=asset_prices,
    )
    return positions


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def x_run_full_pipeline__mutmut_54(
    returns_history: list,
    current_regime: GlobalRegimeState,
    meta_uncertainty: float,
    total_capital: float,
    asset_prices: dict,
) -> dict:
    """
    Full deterministic pipeline from returns history to final positions.

    Step 0: Governance gate (GOV-01 + GOV-05 only).
    Steps 1-11: Unchanged from v1.1.0.

    Raises
    ------
    GovernanceViolationError
        meta_uncertainty out of [0.0, 1.0] or regime not GlobalRegimeState.
    ValueError
        Propagated from RiskEngine (invalid returns_history).
        Propagated from route_exposure_to_positions (invalid capital/prices).
    """
    # ------------------------------------------------------------------
    # Step 0: Governance Gate -- GOV-01 and GOV-05 only
    # ------------------------------------------------------------------

    # GOV-01: meta_uncertainty must be in [0.0, 1.0]
    _meta_invalid = (
        not isinstance(meta_uncertainty, (int, float))
        or not (0.0 <= float(meta_uncertainty) <= 1.0)
    )

    # GOV-05: regime must be a GlobalRegimeState instance
    _regime_invalid = not isinstance(current_regime, GlobalRegimeState)

    if _meta_invalid or _regime_invalid:
        # Build a minimal result via validate_pipeline_config using safe
        # stand-in values for parameters owned by downstream modules.
        _safe_capital = total_capital if (
            isinstance(total_capital, (int, float)) and float(total_capital) > 0
        ) else 1.0
        _safe_regime = current_regime if isinstance(
            current_regime, GlobalRegimeState
        ) else GlobalRegimeState.UNKNOWN
        _safe_meta = meta_uncertainty if (
            isinstance(meta_uncertainty, (int, float))
            and 0.0 <= float(meta_uncertainty) <= 1.0
        ) else 0.5

        _gov_result = validate_pipeline_config(
            meta_uncertainty=_safe_meta if not _meta_invalid else meta_uncertainty,
            initial_capital=_safe_capital,
            window=20,
            step=1,
            regime=_safe_regime,
            periods_per_year=252,
        )
        # Only raise for the rules we gate on
        _gated_rules = {"GOV-01", "GOV-05"}
        _gated = [v for v in _gov_result.blocking_violations if v.rule_id in _gated_rules]
        # Also run with the actual bad value so the error message is accurate
        _real_result = validate_pipeline_config(
            meta_uncertainty=meta_uncertainty if isinstance(meta_uncertainty, (int, float)) else 999,
            initial_capital=None,
            window=20,
            step=1,
            regime=current_regime,
            periods_per_year=252,
        )
        _real_gated = [v for v in _real_result.blocking_violations if v.rule_id in _gated_rules]
        if _real_gated:
            raise GovernanceViolationError(_real_result)

    # ------------------------------------------------------------------
    # Step 1: Instantiate all components fresh per call
    # ------------------------------------------------------------------
    engine: RiskEngine = RiskEngine()
    regime_detector: RegimeDetector = RegimeDetector()
    vol_tracker: VolatilityTracker = VolatilityTracker()
    state_estimator: StateEstimator = StateEstimator()

    # ------------------------------------------------------------------
    # Steps 2-7: State pipeline
    # ------------------------------------------------------------------
    if len(returns_history) > 0:
        features: dict = _extract_regime_features(returns_history)
        regime_result = regime_detector.detect_regime(features)
        vol_result = vol_tracker.estimate_volatility(returns_history)
        previous_state: LatentState = LatentState.default()
        predicted_state: LatentState = state_estimator.predict(previous_state)
        observation: dict = _build_observation_vector(regime_result, vol_result)
        _latent_state: LatentState = state_estimator.update(predicted_state, observation)

    # ------------------------------------------------------------------
    # Step 8: Risk assessment
    # ------------------------------------------------------------------
    risk_output = engine.assess(
        returns_history=returns_history,
        current_regime=current_regime,
        meta_uncertainty=meta_uncertainty,
    )

    # ------------------------------------------------------------------
    # Steps 9-11: Exposure -> positions -> return
    # ------------------------------------------------------------------
    exposure_weight: float = risk_output.exposure_weight
    positions: dict = route_exposure_to_positions(
        total_capital=total_capital,
        exposure_fraction=exposure_weight,
        asset_prices=asset_prices,
    )
    return positions


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def x_run_full_pipeline__mutmut_55(
    returns_history: list,
    current_regime: GlobalRegimeState,
    meta_uncertainty: float,
    total_capital: float,
    asset_prices: dict,
) -> dict:
    """
    Full deterministic pipeline from returns history to final positions.

    Step 0: Governance gate (GOV-01 + GOV-05 only).
    Steps 1-11: Unchanged from v1.1.0.

    Raises
    ------
    GovernanceViolationError
        meta_uncertainty out of [0.0, 1.0] or regime not GlobalRegimeState.
    ValueError
        Propagated from RiskEngine (invalid returns_history).
        Propagated from route_exposure_to_positions (invalid capital/prices).
    """
    # ------------------------------------------------------------------
    # Step 0: Governance Gate -- GOV-01 and GOV-05 only
    # ------------------------------------------------------------------

    # GOV-01: meta_uncertainty must be in [0.0, 1.0]
    _meta_invalid = (
        not isinstance(meta_uncertainty, (int, float))
        or not (0.0 <= float(meta_uncertainty) <= 1.0)
    )

    # GOV-05: regime must be a GlobalRegimeState instance
    _regime_invalid = not isinstance(current_regime, GlobalRegimeState)

    if _meta_invalid or _regime_invalid:
        # Build a minimal result via validate_pipeline_config using safe
        # stand-in values for parameters owned by downstream modules.
        _safe_capital = total_capital if (
            isinstance(total_capital, (int, float)) and float(total_capital) > 0
        ) else 1.0
        _safe_regime = current_regime if isinstance(
            current_regime, GlobalRegimeState
        ) else GlobalRegimeState.UNKNOWN
        _safe_meta = meta_uncertainty if (
            isinstance(meta_uncertainty, (int, float))
            and 0.0 <= float(meta_uncertainty) <= 1.0
        ) else 0.5

        _gov_result = validate_pipeline_config(
            meta_uncertainty=_safe_meta if not _meta_invalid else meta_uncertainty,
            initial_capital=_safe_capital,
            window=20,
            step=1,
            regime=_safe_regime,
            periods_per_year=252,
        )
        # Only raise for the rules we gate on
        _gated_rules = {"GOV-01", "GOV-05"}
        _gated = [v for v in _gov_result.blocking_violations if v.rule_id in _gated_rules]
        # Also run with the actual bad value so the error message is accurate
        _real_result = validate_pipeline_config(
            meta_uncertainty=meta_uncertainty if isinstance(meta_uncertainty, (int, float)) else 999,
            initial_capital=_safe_capital,
            window=None,
            step=1,
            regime=current_regime,
            periods_per_year=252,
        )
        _real_gated = [v for v in _real_result.blocking_violations if v.rule_id in _gated_rules]
        if _real_gated:
            raise GovernanceViolationError(_real_result)

    # ------------------------------------------------------------------
    # Step 1: Instantiate all components fresh per call
    # ------------------------------------------------------------------
    engine: RiskEngine = RiskEngine()
    regime_detector: RegimeDetector = RegimeDetector()
    vol_tracker: VolatilityTracker = VolatilityTracker()
    state_estimator: StateEstimator = StateEstimator()

    # ------------------------------------------------------------------
    # Steps 2-7: State pipeline
    # ------------------------------------------------------------------
    if len(returns_history) > 0:
        features: dict = _extract_regime_features(returns_history)
        regime_result = regime_detector.detect_regime(features)
        vol_result = vol_tracker.estimate_volatility(returns_history)
        previous_state: LatentState = LatentState.default()
        predicted_state: LatentState = state_estimator.predict(previous_state)
        observation: dict = _build_observation_vector(regime_result, vol_result)
        _latent_state: LatentState = state_estimator.update(predicted_state, observation)

    # ------------------------------------------------------------------
    # Step 8: Risk assessment
    # ------------------------------------------------------------------
    risk_output = engine.assess(
        returns_history=returns_history,
        current_regime=current_regime,
        meta_uncertainty=meta_uncertainty,
    )

    # ------------------------------------------------------------------
    # Steps 9-11: Exposure -> positions -> return
    # ------------------------------------------------------------------
    exposure_weight: float = risk_output.exposure_weight
    positions: dict = route_exposure_to_positions(
        total_capital=total_capital,
        exposure_fraction=exposure_weight,
        asset_prices=asset_prices,
    )
    return positions


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def x_run_full_pipeline__mutmut_56(
    returns_history: list,
    current_regime: GlobalRegimeState,
    meta_uncertainty: float,
    total_capital: float,
    asset_prices: dict,
) -> dict:
    """
    Full deterministic pipeline from returns history to final positions.

    Step 0: Governance gate (GOV-01 + GOV-05 only).
    Steps 1-11: Unchanged from v1.1.0.

    Raises
    ------
    GovernanceViolationError
        meta_uncertainty out of [0.0, 1.0] or regime not GlobalRegimeState.
    ValueError
        Propagated from RiskEngine (invalid returns_history).
        Propagated from route_exposure_to_positions (invalid capital/prices).
    """
    # ------------------------------------------------------------------
    # Step 0: Governance Gate -- GOV-01 and GOV-05 only
    # ------------------------------------------------------------------

    # GOV-01: meta_uncertainty must be in [0.0, 1.0]
    _meta_invalid = (
        not isinstance(meta_uncertainty, (int, float))
        or not (0.0 <= float(meta_uncertainty) <= 1.0)
    )

    # GOV-05: regime must be a GlobalRegimeState instance
    _regime_invalid = not isinstance(current_regime, GlobalRegimeState)

    if _meta_invalid or _regime_invalid:
        # Build a minimal result via validate_pipeline_config using safe
        # stand-in values for parameters owned by downstream modules.
        _safe_capital = total_capital if (
            isinstance(total_capital, (int, float)) and float(total_capital) > 0
        ) else 1.0
        _safe_regime = current_regime if isinstance(
            current_regime, GlobalRegimeState
        ) else GlobalRegimeState.UNKNOWN
        _safe_meta = meta_uncertainty if (
            isinstance(meta_uncertainty, (int, float))
            and 0.0 <= float(meta_uncertainty) <= 1.0
        ) else 0.5

        _gov_result = validate_pipeline_config(
            meta_uncertainty=_safe_meta if not _meta_invalid else meta_uncertainty,
            initial_capital=_safe_capital,
            window=20,
            step=1,
            regime=_safe_regime,
            periods_per_year=252,
        )
        # Only raise for the rules we gate on
        _gated_rules = {"GOV-01", "GOV-05"}
        _gated = [v for v in _gov_result.blocking_violations if v.rule_id in _gated_rules]
        # Also run with the actual bad value so the error message is accurate
        _real_result = validate_pipeline_config(
            meta_uncertainty=meta_uncertainty if isinstance(meta_uncertainty, (int, float)) else 999,
            initial_capital=_safe_capital,
            window=20,
            step=None,
            regime=current_regime,
            periods_per_year=252,
        )
        _real_gated = [v for v in _real_result.blocking_violations if v.rule_id in _gated_rules]
        if _real_gated:
            raise GovernanceViolationError(_real_result)

    # ------------------------------------------------------------------
    # Step 1: Instantiate all components fresh per call
    # ------------------------------------------------------------------
    engine: RiskEngine = RiskEngine()
    regime_detector: RegimeDetector = RegimeDetector()
    vol_tracker: VolatilityTracker = VolatilityTracker()
    state_estimator: StateEstimator = StateEstimator()

    # ------------------------------------------------------------------
    # Steps 2-7: State pipeline
    # ------------------------------------------------------------------
    if len(returns_history) > 0:
        features: dict = _extract_regime_features(returns_history)
        regime_result = regime_detector.detect_regime(features)
        vol_result = vol_tracker.estimate_volatility(returns_history)
        previous_state: LatentState = LatentState.default()
        predicted_state: LatentState = state_estimator.predict(previous_state)
        observation: dict = _build_observation_vector(regime_result, vol_result)
        _latent_state: LatentState = state_estimator.update(predicted_state, observation)

    # ------------------------------------------------------------------
    # Step 8: Risk assessment
    # ------------------------------------------------------------------
    risk_output = engine.assess(
        returns_history=returns_history,
        current_regime=current_regime,
        meta_uncertainty=meta_uncertainty,
    )

    # ------------------------------------------------------------------
    # Steps 9-11: Exposure -> positions -> return
    # ------------------------------------------------------------------
    exposure_weight: float = risk_output.exposure_weight
    positions: dict = route_exposure_to_positions(
        total_capital=total_capital,
        exposure_fraction=exposure_weight,
        asset_prices=asset_prices,
    )
    return positions


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def x_run_full_pipeline__mutmut_57(
    returns_history: list,
    current_regime: GlobalRegimeState,
    meta_uncertainty: float,
    total_capital: float,
    asset_prices: dict,
) -> dict:
    """
    Full deterministic pipeline from returns history to final positions.

    Step 0: Governance gate (GOV-01 + GOV-05 only).
    Steps 1-11: Unchanged from v1.1.0.

    Raises
    ------
    GovernanceViolationError
        meta_uncertainty out of [0.0, 1.0] or regime not GlobalRegimeState.
    ValueError
        Propagated from RiskEngine (invalid returns_history).
        Propagated from route_exposure_to_positions (invalid capital/prices).
    """
    # ------------------------------------------------------------------
    # Step 0: Governance Gate -- GOV-01 and GOV-05 only
    # ------------------------------------------------------------------

    # GOV-01: meta_uncertainty must be in [0.0, 1.0]
    _meta_invalid = (
        not isinstance(meta_uncertainty, (int, float))
        or not (0.0 <= float(meta_uncertainty) <= 1.0)
    )

    # GOV-05: regime must be a GlobalRegimeState instance
    _regime_invalid = not isinstance(current_regime, GlobalRegimeState)

    if _meta_invalid or _regime_invalid:
        # Build a minimal result via validate_pipeline_config using safe
        # stand-in values for parameters owned by downstream modules.
        _safe_capital = total_capital if (
            isinstance(total_capital, (int, float)) and float(total_capital) > 0
        ) else 1.0
        _safe_regime = current_regime if isinstance(
            current_regime, GlobalRegimeState
        ) else GlobalRegimeState.UNKNOWN
        _safe_meta = meta_uncertainty if (
            isinstance(meta_uncertainty, (int, float))
            and 0.0 <= float(meta_uncertainty) <= 1.0
        ) else 0.5

        _gov_result = validate_pipeline_config(
            meta_uncertainty=_safe_meta if not _meta_invalid else meta_uncertainty,
            initial_capital=_safe_capital,
            window=20,
            step=1,
            regime=_safe_regime,
            periods_per_year=252,
        )
        # Only raise for the rules we gate on
        _gated_rules = {"GOV-01", "GOV-05"}
        _gated = [v for v in _gov_result.blocking_violations if v.rule_id in _gated_rules]
        # Also run with the actual bad value so the error message is accurate
        _real_result = validate_pipeline_config(
            meta_uncertainty=meta_uncertainty if isinstance(meta_uncertainty, (int, float)) else 999,
            initial_capital=_safe_capital,
            window=20,
            step=1,
            regime=None,
            periods_per_year=252,
        )
        _real_gated = [v for v in _real_result.blocking_violations if v.rule_id in _gated_rules]
        if _real_gated:
            raise GovernanceViolationError(_real_result)

    # ------------------------------------------------------------------
    # Step 1: Instantiate all components fresh per call
    # ------------------------------------------------------------------
    engine: RiskEngine = RiskEngine()
    regime_detector: RegimeDetector = RegimeDetector()
    vol_tracker: VolatilityTracker = VolatilityTracker()
    state_estimator: StateEstimator = StateEstimator()

    # ------------------------------------------------------------------
    # Steps 2-7: State pipeline
    # ------------------------------------------------------------------
    if len(returns_history) > 0:
        features: dict = _extract_regime_features(returns_history)
        regime_result = regime_detector.detect_regime(features)
        vol_result = vol_tracker.estimate_volatility(returns_history)
        previous_state: LatentState = LatentState.default()
        predicted_state: LatentState = state_estimator.predict(previous_state)
        observation: dict = _build_observation_vector(regime_result, vol_result)
        _latent_state: LatentState = state_estimator.update(predicted_state, observation)

    # ------------------------------------------------------------------
    # Step 8: Risk assessment
    # ------------------------------------------------------------------
    risk_output = engine.assess(
        returns_history=returns_history,
        current_regime=current_regime,
        meta_uncertainty=meta_uncertainty,
    )

    # ------------------------------------------------------------------
    # Steps 9-11: Exposure -> positions -> return
    # ------------------------------------------------------------------
    exposure_weight: float = risk_output.exposure_weight
    positions: dict = route_exposure_to_positions(
        total_capital=total_capital,
        exposure_fraction=exposure_weight,
        asset_prices=asset_prices,
    )
    return positions


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def x_run_full_pipeline__mutmut_58(
    returns_history: list,
    current_regime: GlobalRegimeState,
    meta_uncertainty: float,
    total_capital: float,
    asset_prices: dict,
) -> dict:
    """
    Full deterministic pipeline from returns history to final positions.

    Step 0: Governance gate (GOV-01 + GOV-05 only).
    Steps 1-11: Unchanged from v1.1.0.

    Raises
    ------
    GovernanceViolationError
        meta_uncertainty out of [0.0, 1.0] or regime not GlobalRegimeState.
    ValueError
        Propagated from RiskEngine (invalid returns_history).
        Propagated from route_exposure_to_positions (invalid capital/prices).
    """
    # ------------------------------------------------------------------
    # Step 0: Governance Gate -- GOV-01 and GOV-05 only
    # ------------------------------------------------------------------

    # GOV-01: meta_uncertainty must be in [0.0, 1.0]
    _meta_invalid = (
        not isinstance(meta_uncertainty, (int, float))
        or not (0.0 <= float(meta_uncertainty) <= 1.0)
    )

    # GOV-05: regime must be a GlobalRegimeState instance
    _regime_invalid = not isinstance(current_regime, GlobalRegimeState)

    if _meta_invalid or _regime_invalid:
        # Build a minimal result via validate_pipeline_config using safe
        # stand-in values for parameters owned by downstream modules.
        _safe_capital = total_capital if (
            isinstance(total_capital, (int, float)) and float(total_capital) > 0
        ) else 1.0
        _safe_regime = current_regime if isinstance(
            current_regime, GlobalRegimeState
        ) else GlobalRegimeState.UNKNOWN
        _safe_meta = meta_uncertainty if (
            isinstance(meta_uncertainty, (int, float))
            and 0.0 <= float(meta_uncertainty) <= 1.0
        ) else 0.5

        _gov_result = validate_pipeline_config(
            meta_uncertainty=_safe_meta if not _meta_invalid else meta_uncertainty,
            initial_capital=_safe_capital,
            window=20,
            step=1,
            regime=_safe_regime,
            periods_per_year=252,
        )
        # Only raise for the rules we gate on
        _gated_rules = {"GOV-01", "GOV-05"}
        _gated = [v for v in _gov_result.blocking_violations if v.rule_id in _gated_rules]
        # Also run with the actual bad value so the error message is accurate
        _real_result = validate_pipeline_config(
            meta_uncertainty=meta_uncertainty if isinstance(meta_uncertainty, (int, float)) else 999,
            initial_capital=_safe_capital,
            window=20,
            step=1,
            regime=current_regime,
            periods_per_year=None,
        )
        _real_gated = [v for v in _real_result.blocking_violations if v.rule_id in _gated_rules]
        if _real_gated:
            raise GovernanceViolationError(_real_result)

    # ------------------------------------------------------------------
    # Step 1: Instantiate all components fresh per call
    # ------------------------------------------------------------------
    engine: RiskEngine = RiskEngine()
    regime_detector: RegimeDetector = RegimeDetector()
    vol_tracker: VolatilityTracker = VolatilityTracker()
    state_estimator: StateEstimator = StateEstimator()

    # ------------------------------------------------------------------
    # Steps 2-7: State pipeline
    # ------------------------------------------------------------------
    if len(returns_history) > 0:
        features: dict = _extract_regime_features(returns_history)
        regime_result = regime_detector.detect_regime(features)
        vol_result = vol_tracker.estimate_volatility(returns_history)
        previous_state: LatentState = LatentState.default()
        predicted_state: LatentState = state_estimator.predict(previous_state)
        observation: dict = _build_observation_vector(regime_result, vol_result)
        _latent_state: LatentState = state_estimator.update(predicted_state, observation)

    # ------------------------------------------------------------------
    # Step 8: Risk assessment
    # ------------------------------------------------------------------
    risk_output = engine.assess(
        returns_history=returns_history,
        current_regime=current_regime,
        meta_uncertainty=meta_uncertainty,
    )

    # ------------------------------------------------------------------
    # Steps 9-11: Exposure -> positions -> return
    # ------------------------------------------------------------------
    exposure_weight: float = risk_output.exposure_weight
    positions: dict = route_exposure_to_positions(
        total_capital=total_capital,
        exposure_fraction=exposure_weight,
        asset_prices=asset_prices,
    )
    return positions


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def x_run_full_pipeline__mutmut_59(
    returns_history: list,
    current_regime: GlobalRegimeState,
    meta_uncertainty: float,
    total_capital: float,
    asset_prices: dict,
) -> dict:
    """
    Full deterministic pipeline from returns history to final positions.

    Step 0: Governance gate (GOV-01 + GOV-05 only).
    Steps 1-11: Unchanged from v1.1.0.

    Raises
    ------
    GovernanceViolationError
        meta_uncertainty out of [0.0, 1.0] or regime not GlobalRegimeState.
    ValueError
        Propagated from RiskEngine (invalid returns_history).
        Propagated from route_exposure_to_positions (invalid capital/prices).
    """
    # ------------------------------------------------------------------
    # Step 0: Governance Gate -- GOV-01 and GOV-05 only
    # ------------------------------------------------------------------

    # GOV-01: meta_uncertainty must be in [0.0, 1.0]
    _meta_invalid = (
        not isinstance(meta_uncertainty, (int, float))
        or not (0.0 <= float(meta_uncertainty) <= 1.0)
    )

    # GOV-05: regime must be a GlobalRegimeState instance
    _regime_invalid = not isinstance(current_regime, GlobalRegimeState)

    if _meta_invalid or _regime_invalid:
        # Build a minimal result via validate_pipeline_config using safe
        # stand-in values for parameters owned by downstream modules.
        _safe_capital = total_capital if (
            isinstance(total_capital, (int, float)) and float(total_capital) > 0
        ) else 1.0
        _safe_regime = current_regime if isinstance(
            current_regime, GlobalRegimeState
        ) else GlobalRegimeState.UNKNOWN
        _safe_meta = meta_uncertainty if (
            isinstance(meta_uncertainty, (int, float))
            and 0.0 <= float(meta_uncertainty) <= 1.0
        ) else 0.5

        _gov_result = validate_pipeline_config(
            meta_uncertainty=_safe_meta if not _meta_invalid else meta_uncertainty,
            initial_capital=_safe_capital,
            window=20,
            step=1,
            regime=_safe_regime,
            periods_per_year=252,
        )
        # Only raise for the rules we gate on
        _gated_rules = {"GOV-01", "GOV-05"}
        _gated = [v for v in _gov_result.blocking_violations if v.rule_id in _gated_rules]
        # Also run with the actual bad value so the error message is accurate
        _real_result = validate_pipeline_config(
            initial_capital=_safe_capital,
            window=20,
            step=1,
            regime=current_regime,
            periods_per_year=252,
        )
        _real_gated = [v for v in _real_result.blocking_violations if v.rule_id in _gated_rules]
        if _real_gated:
            raise GovernanceViolationError(_real_result)

    # ------------------------------------------------------------------
    # Step 1: Instantiate all components fresh per call
    # ------------------------------------------------------------------
    engine: RiskEngine = RiskEngine()
    regime_detector: RegimeDetector = RegimeDetector()
    vol_tracker: VolatilityTracker = VolatilityTracker()
    state_estimator: StateEstimator = StateEstimator()

    # ------------------------------------------------------------------
    # Steps 2-7: State pipeline
    # ------------------------------------------------------------------
    if len(returns_history) > 0:
        features: dict = _extract_regime_features(returns_history)
        regime_result = regime_detector.detect_regime(features)
        vol_result = vol_tracker.estimate_volatility(returns_history)
        previous_state: LatentState = LatentState.default()
        predicted_state: LatentState = state_estimator.predict(previous_state)
        observation: dict = _build_observation_vector(regime_result, vol_result)
        _latent_state: LatentState = state_estimator.update(predicted_state, observation)

    # ------------------------------------------------------------------
    # Step 8: Risk assessment
    # ------------------------------------------------------------------
    risk_output = engine.assess(
        returns_history=returns_history,
        current_regime=current_regime,
        meta_uncertainty=meta_uncertainty,
    )

    # ------------------------------------------------------------------
    # Steps 9-11: Exposure -> positions -> return
    # ------------------------------------------------------------------
    exposure_weight: float = risk_output.exposure_weight
    positions: dict = route_exposure_to_positions(
        total_capital=total_capital,
        exposure_fraction=exposure_weight,
        asset_prices=asset_prices,
    )
    return positions


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def x_run_full_pipeline__mutmut_60(
    returns_history: list,
    current_regime: GlobalRegimeState,
    meta_uncertainty: float,
    total_capital: float,
    asset_prices: dict,
) -> dict:
    """
    Full deterministic pipeline from returns history to final positions.

    Step 0: Governance gate (GOV-01 + GOV-05 only).
    Steps 1-11: Unchanged from v1.1.0.

    Raises
    ------
    GovernanceViolationError
        meta_uncertainty out of [0.0, 1.0] or regime not GlobalRegimeState.
    ValueError
        Propagated from RiskEngine (invalid returns_history).
        Propagated from route_exposure_to_positions (invalid capital/prices).
    """
    # ------------------------------------------------------------------
    # Step 0: Governance Gate -- GOV-01 and GOV-05 only
    # ------------------------------------------------------------------

    # GOV-01: meta_uncertainty must be in [0.0, 1.0]
    _meta_invalid = (
        not isinstance(meta_uncertainty, (int, float))
        or not (0.0 <= float(meta_uncertainty) <= 1.0)
    )

    # GOV-05: regime must be a GlobalRegimeState instance
    _regime_invalid = not isinstance(current_regime, GlobalRegimeState)

    if _meta_invalid or _regime_invalid:
        # Build a minimal result via validate_pipeline_config using safe
        # stand-in values for parameters owned by downstream modules.
        _safe_capital = total_capital if (
            isinstance(total_capital, (int, float)) and float(total_capital) > 0
        ) else 1.0
        _safe_regime = current_regime if isinstance(
            current_regime, GlobalRegimeState
        ) else GlobalRegimeState.UNKNOWN
        _safe_meta = meta_uncertainty if (
            isinstance(meta_uncertainty, (int, float))
            and 0.0 <= float(meta_uncertainty) <= 1.0
        ) else 0.5

        _gov_result = validate_pipeline_config(
            meta_uncertainty=_safe_meta if not _meta_invalid else meta_uncertainty,
            initial_capital=_safe_capital,
            window=20,
            step=1,
            regime=_safe_regime,
            periods_per_year=252,
        )
        # Only raise for the rules we gate on
        _gated_rules = {"GOV-01", "GOV-05"}
        _gated = [v for v in _gov_result.blocking_violations if v.rule_id in _gated_rules]
        # Also run with the actual bad value so the error message is accurate
        _real_result = validate_pipeline_config(
            meta_uncertainty=meta_uncertainty if isinstance(meta_uncertainty, (int, float)) else 999,
            window=20,
            step=1,
            regime=current_regime,
            periods_per_year=252,
        )
        _real_gated = [v for v in _real_result.blocking_violations if v.rule_id in _gated_rules]
        if _real_gated:
            raise GovernanceViolationError(_real_result)

    # ------------------------------------------------------------------
    # Step 1: Instantiate all components fresh per call
    # ------------------------------------------------------------------
    engine: RiskEngine = RiskEngine()
    regime_detector: RegimeDetector = RegimeDetector()
    vol_tracker: VolatilityTracker = VolatilityTracker()
    state_estimator: StateEstimator = StateEstimator()

    # ------------------------------------------------------------------
    # Steps 2-7: State pipeline
    # ------------------------------------------------------------------
    if len(returns_history) > 0:
        features: dict = _extract_regime_features(returns_history)
        regime_result = regime_detector.detect_regime(features)
        vol_result = vol_tracker.estimate_volatility(returns_history)
        previous_state: LatentState = LatentState.default()
        predicted_state: LatentState = state_estimator.predict(previous_state)
        observation: dict = _build_observation_vector(regime_result, vol_result)
        _latent_state: LatentState = state_estimator.update(predicted_state, observation)

    # ------------------------------------------------------------------
    # Step 8: Risk assessment
    # ------------------------------------------------------------------
    risk_output = engine.assess(
        returns_history=returns_history,
        current_regime=current_regime,
        meta_uncertainty=meta_uncertainty,
    )

    # ------------------------------------------------------------------
    # Steps 9-11: Exposure -> positions -> return
    # ------------------------------------------------------------------
    exposure_weight: float = risk_output.exposure_weight
    positions: dict = route_exposure_to_positions(
        total_capital=total_capital,
        exposure_fraction=exposure_weight,
        asset_prices=asset_prices,
    )
    return positions


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def x_run_full_pipeline__mutmut_61(
    returns_history: list,
    current_regime: GlobalRegimeState,
    meta_uncertainty: float,
    total_capital: float,
    asset_prices: dict,
) -> dict:
    """
    Full deterministic pipeline from returns history to final positions.

    Step 0: Governance gate (GOV-01 + GOV-05 only).
    Steps 1-11: Unchanged from v1.1.0.

    Raises
    ------
    GovernanceViolationError
        meta_uncertainty out of [0.0, 1.0] or regime not GlobalRegimeState.
    ValueError
        Propagated from RiskEngine (invalid returns_history).
        Propagated from route_exposure_to_positions (invalid capital/prices).
    """
    # ------------------------------------------------------------------
    # Step 0: Governance Gate -- GOV-01 and GOV-05 only
    # ------------------------------------------------------------------

    # GOV-01: meta_uncertainty must be in [0.0, 1.0]
    _meta_invalid = (
        not isinstance(meta_uncertainty, (int, float))
        or not (0.0 <= float(meta_uncertainty) <= 1.0)
    )

    # GOV-05: regime must be a GlobalRegimeState instance
    _regime_invalid = not isinstance(current_regime, GlobalRegimeState)

    if _meta_invalid or _regime_invalid:
        # Build a minimal result via validate_pipeline_config using safe
        # stand-in values for parameters owned by downstream modules.
        _safe_capital = total_capital if (
            isinstance(total_capital, (int, float)) and float(total_capital) > 0
        ) else 1.0
        _safe_regime = current_regime if isinstance(
            current_regime, GlobalRegimeState
        ) else GlobalRegimeState.UNKNOWN
        _safe_meta = meta_uncertainty if (
            isinstance(meta_uncertainty, (int, float))
            and 0.0 <= float(meta_uncertainty) <= 1.0
        ) else 0.5

        _gov_result = validate_pipeline_config(
            meta_uncertainty=_safe_meta if not _meta_invalid else meta_uncertainty,
            initial_capital=_safe_capital,
            window=20,
            step=1,
            regime=_safe_regime,
            periods_per_year=252,
        )
        # Only raise for the rules we gate on
        _gated_rules = {"GOV-01", "GOV-05"}
        _gated = [v for v in _gov_result.blocking_violations if v.rule_id in _gated_rules]
        # Also run with the actual bad value so the error message is accurate
        _real_result = validate_pipeline_config(
            meta_uncertainty=meta_uncertainty if isinstance(meta_uncertainty, (int, float)) else 999,
            initial_capital=_safe_capital,
            step=1,
            regime=current_regime,
            periods_per_year=252,
        )
        _real_gated = [v for v in _real_result.blocking_violations if v.rule_id in _gated_rules]
        if _real_gated:
            raise GovernanceViolationError(_real_result)

    # ------------------------------------------------------------------
    # Step 1: Instantiate all components fresh per call
    # ------------------------------------------------------------------
    engine: RiskEngine = RiskEngine()
    regime_detector: RegimeDetector = RegimeDetector()
    vol_tracker: VolatilityTracker = VolatilityTracker()
    state_estimator: StateEstimator = StateEstimator()

    # ------------------------------------------------------------------
    # Steps 2-7: State pipeline
    # ------------------------------------------------------------------
    if len(returns_history) > 0:
        features: dict = _extract_regime_features(returns_history)
        regime_result = regime_detector.detect_regime(features)
        vol_result = vol_tracker.estimate_volatility(returns_history)
        previous_state: LatentState = LatentState.default()
        predicted_state: LatentState = state_estimator.predict(previous_state)
        observation: dict = _build_observation_vector(regime_result, vol_result)
        _latent_state: LatentState = state_estimator.update(predicted_state, observation)

    # ------------------------------------------------------------------
    # Step 8: Risk assessment
    # ------------------------------------------------------------------
    risk_output = engine.assess(
        returns_history=returns_history,
        current_regime=current_regime,
        meta_uncertainty=meta_uncertainty,
    )

    # ------------------------------------------------------------------
    # Steps 9-11: Exposure -> positions -> return
    # ------------------------------------------------------------------
    exposure_weight: float = risk_output.exposure_weight
    positions: dict = route_exposure_to_positions(
        total_capital=total_capital,
        exposure_fraction=exposure_weight,
        asset_prices=asset_prices,
    )
    return positions


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def x_run_full_pipeline__mutmut_62(
    returns_history: list,
    current_regime: GlobalRegimeState,
    meta_uncertainty: float,
    total_capital: float,
    asset_prices: dict,
) -> dict:
    """
    Full deterministic pipeline from returns history to final positions.

    Step 0: Governance gate (GOV-01 + GOV-05 only).
    Steps 1-11: Unchanged from v1.1.0.

    Raises
    ------
    GovernanceViolationError
        meta_uncertainty out of [0.0, 1.0] or regime not GlobalRegimeState.
    ValueError
        Propagated from RiskEngine (invalid returns_history).
        Propagated from route_exposure_to_positions (invalid capital/prices).
    """
    # ------------------------------------------------------------------
    # Step 0: Governance Gate -- GOV-01 and GOV-05 only
    # ------------------------------------------------------------------

    # GOV-01: meta_uncertainty must be in [0.0, 1.0]
    _meta_invalid = (
        not isinstance(meta_uncertainty, (int, float))
        or not (0.0 <= float(meta_uncertainty) <= 1.0)
    )

    # GOV-05: regime must be a GlobalRegimeState instance
    _regime_invalid = not isinstance(current_regime, GlobalRegimeState)

    if _meta_invalid or _regime_invalid:
        # Build a minimal result via validate_pipeline_config using safe
        # stand-in values for parameters owned by downstream modules.
        _safe_capital = total_capital if (
            isinstance(total_capital, (int, float)) and float(total_capital) > 0
        ) else 1.0
        _safe_regime = current_regime if isinstance(
            current_regime, GlobalRegimeState
        ) else GlobalRegimeState.UNKNOWN
        _safe_meta = meta_uncertainty if (
            isinstance(meta_uncertainty, (int, float))
            and 0.0 <= float(meta_uncertainty) <= 1.0
        ) else 0.5

        _gov_result = validate_pipeline_config(
            meta_uncertainty=_safe_meta if not _meta_invalid else meta_uncertainty,
            initial_capital=_safe_capital,
            window=20,
            step=1,
            regime=_safe_regime,
            periods_per_year=252,
        )
        # Only raise for the rules we gate on
        _gated_rules = {"GOV-01", "GOV-05"}
        _gated = [v for v in _gov_result.blocking_violations if v.rule_id in _gated_rules]
        # Also run with the actual bad value so the error message is accurate
        _real_result = validate_pipeline_config(
            meta_uncertainty=meta_uncertainty if isinstance(meta_uncertainty, (int, float)) else 999,
            initial_capital=_safe_capital,
            window=20,
            regime=current_regime,
            periods_per_year=252,
        )
        _real_gated = [v for v in _real_result.blocking_violations if v.rule_id in _gated_rules]
        if _real_gated:
            raise GovernanceViolationError(_real_result)

    # ------------------------------------------------------------------
    # Step 1: Instantiate all components fresh per call
    # ------------------------------------------------------------------
    engine: RiskEngine = RiskEngine()
    regime_detector: RegimeDetector = RegimeDetector()
    vol_tracker: VolatilityTracker = VolatilityTracker()
    state_estimator: StateEstimator = StateEstimator()

    # ------------------------------------------------------------------
    # Steps 2-7: State pipeline
    # ------------------------------------------------------------------
    if len(returns_history) > 0:
        features: dict = _extract_regime_features(returns_history)
        regime_result = regime_detector.detect_regime(features)
        vol_result = vol_tracker.estimate_volatility(returns_history)
        previous_state: LatentState = LatentState.default()
        predicted_state: LatentState = state_estimator.predict(previous_state)
        observation: dict = _build_observation_vector(regime_result, vol_result)
        _latent_state: LatentState = state_estimator.update(predicted_state, observation)

    # ------------------------------------------------------------------
    # Step 8: Risk assessment
    # ------------------------------------------------------------------
    risk_output = engine.assess(
        returns_history=returns_history,
        current_regime=current_regime,
        meta_uncertainty=meta_uncertainty,
    )

    # ------------------------------------------------------------------
    # Steps 9-11: Exposure -> positions -> return
    # ------------------------------------------------------------------
    exposure_weight: float = risk_output.exposure_weight
    positions: dict = route_exposure_to_positions(
        total_capital=total_capital,
        exposure_fraction=exposure_weight,
        asset_prices=asset_prices,
    )
    return positions


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def x_run_full_pipeline__mutmut_63(
    returns_history: list,
    current_regime: GlobalRegimeState,
    meta_uncertainty: float,
    total_capital: float,
    asset_prices: dict,
) -> dict:
    """
    Full deterministic pipeline from returns history to final positions.

    Step 0: Governance gate (GOV-01 + GOV-05 only).
    Steps 1-11: Unchanged from v1.1.0.

    Raises
    ------
    GovernanceViolationError
        meta_uncertainty out of [0.0, 1.0] or regime not GlobalRegimeState.
    ValueError
        Propagated from RiskEngine (invalid returns_history).
        Propagated from route_exposure_to_positions (invalid capital/prices).
    """
    # ------------------------------------------------------------------
    # Step 0: Governance Gate -- GOV-01 and GOV-05 only
    # ------------------------------------------------------------------

    # GOV-01: meta_uncertainty must be in [0.0, 1.0]
    _meta_invalid = (
        not isinstance(meta_uncertainty, (int, float))
        or not (0.0 <= float(meta_uncertainty) <= 1.0)
    )

    # GOV-05: regime must be a GlobalRegimeState instance
    _regime_invalid = not isinstance(current_regime, GlobalRegimeState)

    if _meta_invalid or _regime_invalid:
        # Build a minimal result via validate_pipeline_config using safe
        # stand-in values for parameters owned by downstream modules.
        _safe_capital = total_capital if (
            isinstance(total_capital, (int, float)) and float(total_capital) > 0
        ) else 1.0
        _safe_regime = current_regime if isinstance(
            current_regime, GlobalRegimeState
        ) else GlobalRegimeState.UNKNOWN
        _safe_meta = meta_uncertainty if (
            isinstance(meta_uncertainty, (int, float))
            and 0.0 <= float(meta_uncertainty) <= 1.0
        ) else 0.5

        _gov_result = validate_pipeline_config(
            meta_uncertainty=_safe_meta if not _meta_invalid else meta_uncertainty,
            initial_capital=_safe_capital,
            window=20,
            step=1,
            regime=_safe_regime,
            periods_per_year=252,
        )
        # Only raise for the rules we gate on
        _gated_rules = {"GOV-01", "GOV-05"}
        _gated = [v for v in _gov_result.blocking_violations if v.rule_id in _gated_rules]
        # Also run with the actual bad value so the error message is accurate
        _real_result = validate_pipeline_config(
            meta_uncertainty=meta_uncertainty if isinstance(meta_uncertainty, (int, float)) else 999,
            initial_capital=_safe_capital,
            window=20,
            step=1,
            periods_per_year=252,
        )
        _real_gated = [v for v in _real_result.blocking_violations if v.rule_id in _gated_rules]
        if _real_gated:
            raise GovernanceViolationError(_real_result)

    # ------------------------------------------------------------------
    # Step 1: Instantiate all components fresh per call
    # ------------------------------------------------------------------
    engine: RiskEngine = RiskEngine()
    regime_detector: RegimeDetector = RegimeDetector()
    vol_tracker: VolatilityTracker = VolatilityTracker()
    state_estimator: StateEstimator = StateEstimator()

    # ------------------------------------------------------------------
    # Steps 2-7: State pipeline
    # ------------------------------------------------------------------
    if len(returns_history) > 0:
        features: dict = _extract_regime_features(returns_history)
        regime_result = regime_detector.detect_regime(features)
        vol_result = vol_tracker.estimate_volatility(returns_history)
        previous_state: LatentState = LatentState.default()
        predicted_state: LatentState = state_estimator.predict(previous_state)
        observation: dict = _build_observation_vector(regime_result, vol_result)
        _latent_state: LatentState = state_estimator.update(predicted_state, observation)

    # ------------------------------------------------------------------
    # Step 8: Risk assessment
    # ------------------------------------------------------------------
    risk_output = engine.assess(
        returns_history=returns_history,
        current_regime=current_regime,
        meta_uncertainty=meta_uncertainty,
    )

    # ------------------------------------------------------------------
    # Steps 9-11: Exposure -> positions -> return
    # ------------------------------------------------------------------
    exposure_weight: float = risk_output.exposure_weight
    positions: dict = route_exposure_to_positions(
        total_capital=total_capital,
        exposure_fraction=exposure_weight,
        asset_prices=asset_prices,
    )
    return positions


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def x_run_full_pipeline__mutmut_64(
    returns_history: list,
    current_regime: GlobalRegimeState,
    meta_uncertainty: float,
    total_capital: float,
    asset_prices: dict,
) -> dict:
    """
    Full deterministic pipeline from returns history to final positions.

    Step 0: Governance gate (GOV-01 + GOV-05 only).
    Steps 1-11: Unchanged from v1.1.0.

    Raises
    ------
    GovernanceViolationError
        meta_uncertainty out of [0.0, 1.0] or regime not GlobalRegimeState.
    ValueError
        Propagated from RiskEngine (invalid returns_history).
        Propagated from route_exposure_to_positions (invalid capital/prices).
    """
    # ------------------------------------------------------------------
    # Step 0: Governance Gate -- GOV-01 and GOV-05 only
    # ------------------------------------------------------------------

    # GOV-01: meta_uncertainty must be in [0.0, 1.0]
    _meta_invalid = (
        not isinstance(meta_uncertainty, (int, float))
        or not (0.0 <= float(meta_uncertainty) <= 1.0)
    )

    # GOV-05: regime must be a GlobalRegimeState instance
    _regime_invalid = not isinstance(current_regime, GlobalRegimeState)

    if _meta_invalid or _regime_invalid:
        # Build a minimal result via validate_pipeline_config using safe
        # stand-in values for parameters owned by downstream modules.
        _safe_capital = total_capital if (
            isinstance(total_capital, (int, float)) and float(total_capital) > 0
        ) else 1.0
        _safe_regime = current_regime if isinstance(
            current_regime, GlobalRegimeState
        ) else GlobalRegimeState.UNKNOWN
        _safe_meta = meta_uncertainty if (
            isinstance(meta_uncertainty, (int, float))
            and 0.0 <= float(meta_uncertainty) <= 1.0
        ) else 0.5

        _gov_result = validate_pipeline_config(
            meta_uncertainty=_safe_meta if not _meta_invalid else meta_uncertainty,
            initial_capital=_safe_capital,
            window=20,
            step=1,
            regime=_safe_regime,
            periods_per_year=252,
        )
        # Only raise for the rules we gate on
        _gated_rules = {"GOV-01", "GOV-05"}
        _gated = [v for v in _gov_result.blocking_violations if v.rule_id in _gated_rules]
        # Also run with the actual bad value so the error message is accurate
        _real_result = validate_pipeline_config(
            meta_uncertainty=meta_uncertainty if isinstance(meta_uncertainty, (int, float)) else 999,
            initial_capital=_safe_capital,
            window=20,
            step=1,
            regime=current_regime,
            )
        _real_gated = [v for v in _real_result.blocking_violations if v.rule_id in _gated_rules]
        if _real_gated:
            raise GovernanceViolationError(_real_result)

    # ------------------------------------------------------------------
    # Step 1: Instantiate all components fresh per call
    # ------------------------------------------------------------------
    engine: RiskEngine = RiskEngine()
    regime_detector: RegimeDetector = RegimeDetector()
    vol_tracker: VolatilityTracker = VolatilityTracker()
    state_estimator: StateEstimator = StateEstimator()

    # ------------------------------------------------------------------
    # Steps 2-7: State pipeline
    # ------------------------------------------------------------------
    if len(returns_history) > 0:
        features: dict = _extract_regime_features(returns_history)
        regime_result = regime_detector.detect_regime(features)
        vol_result = vol_tracker.estimate_volatility(returns_history)
        previous_state: LatentState = LatentState.default()
        predicted_state: LatentState = state_estimator.predict(previous_state)
        observation: dict = _build_observation_vector(regime_result, vol_result)
        _latent_state: LatentState = state_estimator.update(predicted_state, observation)

    # ------------------------------------------------------------------
    # Step 8: Risk assessment
    # ------------------------------------------------------------------
    risk_output = engine.assess(
        returns_history=returns_history,
        current_regime=current_regime,
        meta_uncertainty=meta_uncertainty,
    )

    # ------------------------------------------------------------------
    # Steps 9-11: Exposure -> positions -> return
    # ------------------------------------------------------------------
    exposure_weight: float = risk_output.exposure_weight
    positions: dict = route_exposure_to_positions(
        total_capital=total_capital,
        exposure_fraction=exposure_weight,
        asset_prices=asset_prices,
    )
    return positions


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def x_run_full_pipeline__mutmut_65(
    returns_history: list,
    current_regime: GlobalRegimeState,
    meta_uncertainty: float,
    total_capital: float,
    asset_prices: dict,
) -> dict:
    """
    Full deterministic pipeline from returns history to final positions.

    Step 0: Governance gate (GOV-01 + GOV-05 only).
    Steps 1-11: Unchanged from v1.1.0.

    Raises
    ------
    GovernanceViolationError
        meta_uncertainty out of [0.0, 1.0] or regime not GlobalRegimeState.
    ValueError
        Propagated from RiskEngine (invalid returns_history).
        Propagated from route_exposure_to_positions (invalid capital/prices).
    """
    # ------------------------------------------------------------------
    # Step 0: Governance Gate -- GOV-01 and GOV-05 only
    # ------------------------------------------------------------------

    # GOV-01: meta_uncertainty must be in [0.0, 1.0]
    _meta_invalid = (
        not isinstance(meta_uncertainty, (int, float))
        or not (0.0 <= float(meta_uncertainty) <= 1.0)
    )

    # GOV-05: regime must be a GlobalRegimeState instance
    _regime_invalid = not isinstance(current_regime, GlobalRegimeState)

    if _meta_invalid or _regime_invalid:
        # Build a minimal result via validate_pipeline_config using safe
        # stand-in values for parameters owned by downstream modules.
        _safe_capital = total_capital if (
            isinstance(total_capital, (int, float)) and float(total_capital) > 0
        ) else 1.0
        _safe_regime = current_regime if isinstance(
            current_regime, GlobalRegimeState
        ) else GlobalRegimeState.UNKNOWN
        _safe_meta = meta_uncertainty if (
            isinstance(meta_uncertainty, (int, float))
            and 0.0 <= float(meta_uncertainty) <= 1.0
        ) else 0.5

        _gov_result = validate_pipeline_config(
            meta_uncertainty=_safe_meta if not _meta_invalid else meta_uncertainty,
            initial_capital=_safe_capital,
            window=20,
            step=1,
            regime=_safe_regime,
            periods_per_year=252,
        )
        # Only raise for the rules we gate on
        _gated_rules = {"GOV-01", "GOV-05"}
        _gated = [v for v in _gov_result.blocking_violations if v.rule_id in _gated_rules]
        # Also run with the actual bad value so the error message is accurate
        _real_result = validate_pipeline_config(
            meta_uncertainty=meta_uncertainty if isinstance(meta_uncertainty, (int, float)) else 1000,
            initial_capital=_safe_capital,
            window=20,
            step=1,
            regime=current_regime,
            periods_per_year=252,
        )
        _real_gated = [v for v in _real_result.blocking_violations if v.rule_id in _gated_rules]
        if _real_gated:
            raise GovernanceViolationError(_real_result)

    # ------------------------------------------------------------------
    # Step 1: Instantiate all components fresh per call
    # ------------------------------------------------------------------
    engine: RiskEngine = RiskEngine()
    regime_detector: RegimeDetector = RegimeDetector()
    vol_tracker: VolatilityTracker = VolatilityTracker()
    state_estimator: StateEstimator = StateEstimator()

    # ------------------------------------------------------------------
    # Steps 2-7: State pipeline
    # ------------------------------------------------------------------
    if len(returns_history) > 0:
        features: dict = _extract_regime_features(returns_history)
        regime_result = regime_detector.detect_regime(features)
        vol_result = vol_tracker.estimate_volatility(returns_history)
        previous_state: LatentState = LatentState.default()
        predicted_state: LatentState = state_estimator.predict(previous_state)
        observation: dict = _build_observation_vector(regime_result, vol_result)
        _latent_state: LatentState = state_estimator.update(predicted_state, observation)

    # ------------------------------------------------------------------
    # Step 8: Risk assessment
    # ------------------------------------------------------------------
    risk_output = engine.assess(
        returns_history=returns_history,
        current_regime=current_regime,
        meta_uncertainty=meta_uncertainty,
    )

    # ------------------------------------------------------------------
    # Steps 9-11: Exposure -> positions -> return
    # ------------------------------------------------------------------
    exposure_weight: float = risk_output.exposure_weight
    positions: dict = route_exposure_to_positions(
        total_capital=total_capital,
        exposure_fraction=exposure_weight,
        asset_prices=asset_prices,
    )
    return positions


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def x_run_full_pipeline__mutmut_66(
    returns_history: list,
    current_regime: GlobalRegimeState,
    meta_uncertainty: float,
    total_capital: float,
    asset_prices: dict,
) -> dict:
    """
    Full deterministic pipeline from returns history to final positions.

    Step 0: Governance gate (GOV-01 + GOV-05 only).
    Steps 1-11: Unchanged from v1.1.0.

    Raises
    ------
    GovernanceViolationError
        meta_uncertainty out of [0.0, 1.0] or regime not GlobalRegimeState.
    ValueError
        Propagated from RiskEngine (invalid returns_history).
        Propagated from route_exposure_to_positions (invalid capital/prices).
    """
    # ------------------------------------------------------------------
    # Step 0: Governance Gate -- GOV-01 and GOV-05 only
    # ------------------------------------------------------------------

    # GOV-01: meta_uncertainty must be in [0.0, 1.0]
    _meta_invalid = (
        not isinstance(meta_uncertainty, (int, float))
        or not (0.0 <= float(meta_uncertainty) <= 1.0)
    )

    # GOV-05: regime must be a GlobalRegimeState instance
    _regime_invalid = not isinstance(current_regime, GlobalRegimeState)

    if _meta_invalid or _regime_invalid:
        # Build a minimal result via validate_pipeline_config using safe
        # stand-in values for parameters owned by downstream modules.
        _safe_capital = total_capital if (
            isinstance(total_capital, (int, float)) and float(total_capital) > 0
        ) else 1.0
        _safe_regime = current_regime if isinstance(
            current_regime, GlobalRegimeState
        ) else GlobalRegimeState.UNKNOWN
        _safe_meta = meta_uncertainty if (
            isinstance(meta_uncertainty, (int, float))
            and 0.0 <= float(meta_uncertainty) <= 1.0
        ) else 0.5

        _gov_result = validate_pipeline_config(
            meta_uncertainty=_safe_meta if not _meta_invalid else meta_uncertainty,
            initial_capital=_safe_capital,
            window=20,
            step=1,
            regime=_safe_regime,
            periods_per_year=252,
        )
        # Only raise for the rules we gate on
        _gated_rules = {"GOV-01", "GOV-05"}
        _gated = [v for v in _gov_result.blocking_violations if v.rule_id in _gated_rules]
        # Also run with the actual bad value so the error message is accurate
        _real_result = validate_pipeline_config(
            meta_uncertainty=meta_uncertainty if isinstance(meta_uncertainty, (int, float)) else 999,
            initial_capital=_safe_capital,
            window=21,
            step=1,
            regime=current_regime,
            periods_per_year=252,
        )
        _real_gated = [v for v in _real_result.blocking_violations if v.rule_id in _gated_rules]
        if _real_gated:
            raise GovernanceViolationError(_real_result)

    # ------------------------------------------------------------------
    # Step 1: Instantiate all components fresh per call
    # ------------------------------------------------------------------
    engine: RiskEngine = RiskEngine()
    regime_detector: RegimeDetector = RegimeDetector()
    vol_tracker: VolatilityTracker = VolatilityTracker()
    state_estimator: StateEstimator = StateEstimator()

    # ------------------------------------------------------------------
    # Steps 2-7: State pipeline
    # ------------------------------------------------------------------
    if len(returns_history) > 0:
        features: dict = _extract_regime_features(returns_history)
        regime_result = regime_detector.detect_regime(features)
        vol_result = vol_tracker.estimate_volatility(returns_history)
        previous_state: LatentState = LatentState.default()
        predicted_state: LatentState = state_estimator.predict(previous_state)
        observation: dict = _build_observation_vector(regime_result, vol_result)
        _latent_state: LatentState = state_estimator.update(predicted_state, observation)

    # ------------------------------------------------------------------
    # Step 8: Risk assessment
    # ------------------------------------------------------------------
    risk_output = engine.assess(
        returns_history=returns_history,
        current_regime=current_regime,
        meta_uncertainty=meta_uncertainty,
    )

    # ------------------------------------------------------------------
    # Steps 9-11: Exposure -> positions -> return
    # ------------------------------------------------------------------
    exposure_weight: float = risk_output.exposure_weight
    positions: dict = route_exposure_to_positions(
        total_capital=total_capital,
        exposure_fraction=exposure_weight,
        asset_prices=asset_prices,
    )
    return positions


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def x_run_full_pipeline__mutmut_67(
    returns_history: list,
    current_regime: GlobalRegimeState,
    meta_uncertainty: float,
    total_capital: float,
    asset_prices: dict,
) -> dict:
    """
    Full deterministic pipeline from returns history to final positions.

    Step 0: Governance gate (GOV-01 + GOV-05 only).
    Steps 1-11: Unchanged from v1.1.0.

    Raises
    ------
    GovernanceViolationError
        meta_uncertainty out of [0.0, 1.0] or regime not GlobalRegimeState.
    ValueError
        Propagated from RiskEngine (invalid returns_history).
        Propagated from route_exposure_to_positions (invalid capital/prices).
    """
    # ------------------------------------------------------------------
    # Step 0: Governance Gate -- GOV-01 and GOV-05 only
    # ------------------------------------------------------------------

    # GOV-01: meta_uncertainty must be in [0.0, 1.0]
    _meta_invalid = (
        not isinstance(meta_uncertainty, (int, float))
        or not (0.0 <= float(meta_uncertainty) <= 1.0)
    )

    # GOV-05: regime must be a GlobalRegimeState instance
    _regime_invalid = not isinstance(current_regime, GlobalRegimeState)

    if _meta_invalid or _regime_invalid:
        # Build a minimal result via validate_pipeline_config using safe
        # stand-in values for parameters owned by downstream modules.
        _safe_capital = total_capital if (
            isinstance(total_capital, (int, float)) and float(total_capital) > 0
        ) else 1.0
        _safe_regime = current_regime if isinstance(
            current_regime, GlobalRegimeState
        ) else GlobalRegimeState.UNKNOWN
        _safe_meta = meta_uncertainty if (
            isinstance(meta_uncertainty, (int, float))
            and 0.0 <= float(meta_uncertainty) <= 1.0
        ) else 0.5

        _gov_result = validate_pipeline_config(
            meta_uncertainty=_safe_meta if not _meta_invalid else meta_uncertainty,
            initial_capital=_safe_capital,
            window=20,
            step=1,
            regime=_safe_regime,
            periods_per_year=252,
        )
        # Only raise for the rules we gate on
        _gated_rules = {"GOV-01", "GOV-05"}
        _gated = [v for v in _gov_result.blocking_violations if v.rule_id in _gated_rules]
        # Also run with the actual bad value so the error message is accurate
        _real_result = validate_pipeline_config(
            meta_uncertainty=meta_uncertainty if isinstance(meta_uncertainty, (int, float)) else 999,
            initial_capital=_safe_capital,
            window=20,
            step=2,
            regime=current_regime,
            periods_per_year=252,
        )
        _real_gated = [v for v in _real_result.blocking_violations if v.rule_id in _gated_rules]
        if _real_gated:
            raise GovernanceViolationError(_real_result)

    # ------------------------------------------------------------------
    # Step 1: Instantiate all components fresh per call
    # ------------------------------------------------------------------
    engine: RiskEngine = RiskEngine()
    regime_detector: RegimeDetector = RegimeDetector()
    vol_tracker: VolatilityTracker = VolatilityTracker()
    state_estimator: StateEstimator = StateEstimator()

    # ------------------------------------------------------------------
    # Steps 2-7: State pipeline
    # ------------------------------------------------------------------
    if len(returns_history) > 0:
        features: dict = _extract_regime_features(returns_history)
        regime_result = regime_detector.detect_regime(features)
        vol_result = vol_tracker.estimate_volatility(returns_history)
        previous_state: LatentState = LatentState.default()
        predicted_state: LatentState = state_estimator.predict(previous_state)
        observation: dict = _build_observation_vector(regime_result, vol_result)
        _latent_state: LatentState = state_estimator.update(predicted_state, observation)

    # ------------------------------------------------------------------
    # Step 8: Risk assessment
    # ------------------------------------------------------------------
    risk_output = engine.assess(
        returns_history=returns_history,
        current_regime=current_regime,
        meta_uncertainty=meta_uncertainty,
    )

    # ------------------------------------------------------------------
    # Steps 9-11: Exposure -> positions -> return
    # ------------------------------------------------------------------
    exposure_weight: float = risk_output.exposure_weight
    positions: dict = route_exposure_to_positions(
        total_capital=total_capital,
        exposure_fraction=exposure_weight,
        asset_prices=asset_prices,
    )
    return positions


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def x_run_full_pipeline__mutmut_68(
    returns_history: list,
    current_regime: GlobalRegimeState,
    meta_uncertainty: float,
    total_capital: float,
    asset_prices: dict,
) -> dict:
    """
    Full deterministic pipeline from returns history to final positions.

    Step 0: Governance gate (GOV-01 + GOV-05 only).
    Steps 1-11: Unchanged from v1.1.0.

    Raises
    ------
    GovernanceViolationError
        meta_uncertainty out of [0.0, 1.0] or regime not GlobalRegimeState.
    ValueError
        Propagated from RiskEngine (invalid returns_history).
        Propagated from route_exposure_to_positions (invalid capital/prices).
    """
    # ------------------------------------------------------------------
    # Step 0: Governance Gate -- GOV-01 and GOV-05 only
    # ------------------------------------------------------------------

    # GOV-01: meta_uncertainty must be in [0.0, 1.0]
    _meta_invalid = (
        not isinstance(meta_uncertainty, (int, float))
        or not (0.0 <= float(meta_uncertainty) <= 1.0)
    )

    # GOV-05: regime must be a GlobalRegimeState instance
    _regime_invalid = not isinstance(current_regime, GlobalRegimeState)

    if _meta_invalid or _regime_invalid:
        # Build a minimal result via validate_pipeline_config using safe
        # stand-in values for parameters owned by downstream modules.
        _safe_capital = total_capital if (
            isinstance(total_capital, (int, float)) and float(total_capital) > 0
        ) else 1.0
        _safe_regime = current_regime if isinstance(
            current_regime, GlobalRegimeState
        ) else GlobalRegimeState.UNKNOWN
        _safe_meta = meta_uncertainty if (
            isinstance(meta_uncertainty, (int, float))
            and 0.0 <= float(meta_uncertainty) <= 1.0
        ) else 0.5

        _gov_result = validate_pipeline_config(
            meta_uncertainty=_safe_meta if not _meta_invalid else meta_uncertainty,
            initial_capital=_safe_capital,
            window=20,
            step=1,
            regime=_safe_regime,
            periods_per_year=252,
        )
        # Only raise for the rules we gate on
        _gated_rules = {"GOV-01", "GOV-05"}
        _gated = [v for v in _gov_result.blocking_violations if v.rule_id in _gated_rules]
        # Also run with the actual bad value so the error message is accurate
        _real_result = validate_pipeline_config(
            meta_uncertainty=meta_uncertainty if isinstance(meta_uncertainty, (int, float)) else 999,
            initial_capital=_safe_capital,
            window=20,
            step=1,
            regime=current_regime,
            periods_per_year=253,
        )
        _real_gated = [v for v in _real_result.blocking_violations if v.rule_id in _gated_rules]
        if _real_gated:
            raise GovernanceViolationError(_real_result)

    # ------------------------------------------------------------------
    # Step 1: Instantiate all components fresh per call
    # ------------------------------------------------------------------
    engine: RiskEngine = RiskEngine()
    regime_detector: RegimeDetector = RegimeDetector()
    vol_tracker: VolatilityTracker = VolatilityTracker()
    state_estimator: StateEstimator = StateEstimator()

    # ------------------------------------------------------------------
    # Steps 2-7: State pipeline
    # ------------------------------------------------------------------
    if len(returns_history) > 0:
        features: dict = _extract_regime_features(returns_history)
        regime_result = regime_detector.detect_regime(features)
        vol_result = vol_tracker.estimate_volatility(returns_history)
        previous_state: LatentState = LatentState.default()
        predicted_state: LatentState = state_estimator.predict(previous_state)
        observation: dict = _build_observation_vector(regime_result, vol_result)
        _latent_state: LatentState = state_estimator.update(predicted_state, observation)

    # ------------------------------------------------------------------
    # Step 8: Risk assessment
    # ------------------------------------------------------------------
    risk_output = engine.assess(
        returns_history=returns_history,
        current_regime=current_regime,
        meta_uncertainty=meta_uncertainty,
    )

    # ------------------------------------------------------------------
    # Steps 9-11: Exposure -> positions -> return
    # ------------------------------------------------------------------
    exposure_weight: float = risk_output.exposure_weight
    positions: dict = route_exposure_to_positions(
        total_capital=total_capital,
        exposure_fraction=exposure_weight,
        asset_prices=asset_prices,
    )
    return positions


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def x_run_full_pipeline__mutmut_69(
    returns_history: list,
    current_regime: GlobalRegimeState,
    meta_uncertainty: float,
    total_capital: float,
    asset_prices: dict,
) -> dict:
    """
    Full deterministic pipeline from returns history to final positions.

    Step 0: Governance gate (GOV-01 + GOV-05 only).
    Steps 1-11: Unchanged from v1.1.0.

    Raises
    ------
    GovernanceViolationError
        meta_uncertainty out of [0.0, 1.0] or regime not GlobalRegimeState.
    ValueError
        Propagated from RiskEngine (invalid returns_history).
        Propagated from route_exposure_to_positions (invalid capital/prices).
    """
    # ------------------------------------------------------------------
    # Step 0: Governance Gate -- GOV-01 and GOV-05 only
    # ------------------------------------------------------------------

    # GOV-01: meta_uncertainty must be in [0.0, 1.0]
    _meta_invalid = (
        not isinstance(meta_uncertainty, (int, float))
        or not (0.0 <= float(meta_uncertainty) <= 1.0)
    )

    # GOV-05: regime must be a GlobalRegimeState instance
    _regime_invalid = not isinstance(current_regime, GlobalRegimeState)

    if _meta_invalid or _regime_invalid:
        # Build a minimal result via validate_pipeline_config using safe
        # stand-in values for parameters owned by downstream modules.
        _safe_capital = total_capital if (
            isinstance(total_capital, (int, float)) and float(total_capital) > 0
        ) else 1.0
        _safe_regime = current_regime if isinstance(
            current_regime, GlobalRegimeState
        ) else GlobalRegimeState.UNKNOWN
        _safe_meta = meta_uncertainty if (
            isinstance(meta_uncertainty, (int, float))
            and 0.0 <= float(meta_uncertainty) <= 1.0
        ) else 0.5

        _gov_result = validate_pipeline_config(
            meta_uncertainty=_safe_meta if not _meta_invalid else meta_uncertainty,
            initial_capital=_safe_capital,
            window=20,
            step=1,
            regime=_safe_regime,
            periods_per_year=252,
        )
        # Only raise for the rules we gate on
        _gated_rules = {"GOV-01", "GOV-05"}
        _gated = [v for v in _gov_result.blocking_violations if v.rule_id in _gated_rules]
        # Also run with the actual bad value so the error message is accurate
        _real_result = validate_pipeline_config(
            meta_uncertainty=meta_uncertainty if isinstance(meta_uncertainty, (int, float)) else 999,
            initial_capital=_safe_capital,
            window=20,
            step=1,
            regime=current_regime,
            periods_per_year=252,
        )
        _real_gated = None
        if _real_gated:
            raise GovernanceViolationError(_real_result)

    # ------------------------------------------------------------------
    # Step 1: Instantiate all components fresh per call
    # ------------------------------------------------------------------
    engine: RiskEngine = RiskEngine()
    regime_detector: RegimeDetector = RegimeDetector()
    vol_tracker: VolatilityTracker = VolatilityTracker()
    state_estimator: StateEstimator = StateEstimator()

    # ------------------------------------------------------------------
    # Steps 2-7: State pipeline
    # ------------------------------------------------------------------
    if len(returns_history) > 0:
        features: dict = _extract_regime_features(returns_history)
        regime_result = regime_detector.detect_regime(features)
        vol_result = vol_tracker.estimate_volatility(returns_history)
        previous_state: LatentState = LatentState.default()
        predicted_state: LatentState = state_estimator.predict(previous_state)
        observation: dict = _build_observation_vector(regime_result, vol_result)
        _latent_state: LatentState = state_estimator.update(predicted_state, observation)

    # ------------------------------------------------------------------
    # Step 8: Risk assessment
    # ------------------------------------------------------------------
    risk_output = engine.assess(
        returns_history=returns_history,
        current_regime=current_regime,
        meta_uncertainty=meta_uncertainty,
    )

    # ------------------------------------------------------------------
    # Steps 9-11: Exposure -> positions -> return
    # ------------------------------------------------------------------
    exposure_weight: float = risk_output.exposure_weight
    positions: dict = route_exposure_to_positions(
        total_capital=total_capital,
        exposure_fraction=exposure_weight,
        asset_prices=asset_prices,
    )
    return positions


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def x_run_full_pipeline__mutmut_70(
    returns_history: list,
    current_regime: GlobalRegimeState,
    meta_uncertainty: float,
    total_capital: float,
    asset_prices: dict,
) -> dict:
    """
    Full deterministic pipeline from returns history to final positions.

    Step 0: Governance gate (GOV-01 + GOV-05 only).
    Steps 1-11: Unchanged from v1.1.0.

    Raises
    ------
    GovernanceViolationError
        meta_uncertainty out of [0.0, 1.0] or regime not GlobalRegimeState.
    ValueError
        Propagated from RiskEngine (invalid returns_history).
        Propagated from route_exposure_to_positions (invalid capital/prices).
    """
    # ------------------------------------------------------------------
    # Step 0: Governance Gate -- GOV-01 and GOV-05 only
    # ------------------------------------------------------------------

    # GOV-01: meta_uncertainty must be in [0.0, 1.0]
    _meta_invalid = (
        not isinstance(meta_uncertainty, (int, float))
        or not (0.0 <= float(meta_uncertainty) <= 1.0)
    )

    # GOV-05: regime must be a GlobalRegimeState instance
    _regime_invalid = not isinstance(current_regime, GlobalRegimeState)

    if _meta_invalid or _regime_invalid:
        # Build a minimal result via validate_pipeline_config using safe
        # stand-in values for parameters owned by downstream modules.
        _safe_capital = total_capital if (
            isinstance(total_capital, (int, float)) and float(total_capital) > 0
        ) else 1.0
        _safe_regime = current_regime if isinstance(
            current_regime, GlobalRegimeState
        ) else GlobalRegimeState.UNKNOWN
        _safe_meta = meta_uncertainty if (
            isinstance(meta_uncertainty, (int, float))
            and 0.0 <= float(meta_uncertainty) <= 1.0
        ) else 0.5

        _gov_result = validate_pipeline_config(
            meta_uncertainty=_safe_meta if not _meta_invalid else meta_uncertainty,
            initial_capital=_safe_capital,
            window=20,
            step=1,
            regime=_safe_regime,
            periods_per_year=252,
        )
        # Only raise for the rules we gate on
        _gated_rules = {"GOV-01", "GOV-05"}
        _gated = [v for v in _gov_result.blocking_violations if v.rule_id in _gated_rules]
        # Also run with the actual bad value so the error message is accurate
        _real_result = validate_pipeline_config(
            meta_uncertainty=meta_uncertainty if isinstance(meta_uncertainty, (int, float)) else 999,
            initial_capital=_safe_capital,
            window=20,
            step=1,
            regime=current_regime,
            periods_per_year=252,
        )
        _real_gated = [v for v in _real_result.blocking_violations if v.rule_id not in _gated_rules]
        if _real_gated:
            raise GovernanceViolationError(_real_result)

    # ------------------------------------------------------------------
    # Step 1: Instantiate all components fresh per call
    # ------------------------------------------------------------------
    engine: RiskEngine = RiskEngine()
    regime_detector: RegimeDetector = RegimeDetector()
    vol_tracker: VolatilityTracker = VolatilityTracker()
    state_estimator: StateEstimator = StateEstimator()

    # ------------------------------------------------------------------
    # Steps 2-7: State pipeline
    # ------------------------------------------------------------------
    if len(returns_history) > 0:
        features: dict = _extract_regime_features(returns_history)
        regime_result = regime_detector.detect_regime(features)
        vol_result = vol_tracker.estimate_volatility(returns_history)
        previous_state: LatentState = LatentState.default()
        predicted_state: LatentState = state_estimator.predict(previous_state)
        observation: dict = _build_observation_vector(regime_result, vol_result)
        _latent_state: LatentState = state_estimator.update(predicted_state, observation)

    # ------------------------------------------------------------------
    # Step 8: Risk assessment
    # ------------------------------------------------------------------
    risk_output = engine.assess(
        returns_history=returns_history,
        current_regime=current_regime,
        meta_uncertainty=meta_uncertainty,
    )

    # ------------------------------------------------------------------
    # Steps 9-11: Exposure -> positions -> return
    # ------------------------------------------------------------------
    exposure_weight: float = risk_output.exposure_weight
    positions: dict = route_exposure_to_positions(
        total_capital=total_capital,
        exposure_fraction=exposure_weight,
        asset_prices=asset_prices,
    )
    return positions


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def x_run_full_pipeline__mutmut_71(
    returns_history: list,
    current_regime: GlobalRegimeState,
    meta_uncertainty: float,
    total_capital: float,
    asset_prices: dict,
) -> dict:
    """
    Full deterministic pipeline from returns history to final positions.

    Step 0: Governance gate (GOV-01 + GOV-05 only).
    Steps 1-11: Unchanged from v1.1.0.

    Raises
    ------
    GovernanceViolationError
        meta_uncertainty out of [0.0, 1.0] or regime not GlobalRegimeState.
    ValueError
        Propagated from RiskEngine (invalid returns_history).
        Propagated from route_exposure_to_positions (invalid capital/prices).
    """
    # ------------------------------------------------------------------
    # Step 0: Governance Gate -- GOV-01 and GOV-05 only
    # ------------------------------------------------------------------

    # GOV-01: meta_uncertainty must be in [0.0, 1.0]
    _meta_invalid = (
        not isinstance(meta_uncertainty, (int, float))
        or not (0.0 <= float(meta_uncertainty) <= 1.0)
    )

    # GOV-05: regime must be a GlobalRegimeState instance
    _regime_invalid = not isinstance(current_regime, GlobalRegimeState)

    if _meta_invalid or _regime_invalid:
        # Build a minimal result via validate_pipeline_config using safe
        # stand-in values for parameters owned by downstream modules.
        _safe_capital = total_capital if (
            isinstance(total_capital, (int, float)) and float(total_capital) > 0
        ) else 1.0
        _safe_regime = current_regime if isinstance(
            current_regime, GlobalRegimeState
        ) else GlobalRegimeState.UNKNOWN
        _safe_meta = meta_uncertainty if (
            isinstance(meta_uncertainty, (int, float))
            and 0.0 <= float(meta_uncertainty) <= 1.0
        ) else 0.5

        _gov_result = validate_pipeline_config(
            meta_uncertainty=_safe_meta if not _meta_invalid else meta_uncertainty,
            initial_capital=_safe_capital,
            window=20,
            step=1,
            regime=_safe_regime,
            periods_per_year=252,
        )
        # Only raise for the rules we gate on
        _gated_rules = {"GOV-01", "GOV-05"}
        _gated = [v for v in _gov_result.blocking_violations if v.rule_id in _gated_rules]
        # Also run with the actual bad value so the error message is accurate
        _real_result = validate_pipeline_config(
            meta_uncertainty=meta_uncertainty if isinstance(meta_uncertainty, (int, float)) else 999,
            initial_capital=_safe_capital,
            window=20,
            step=1,
            regime=current_regime,
            periods_per_year=252,
        )
        _real_gated = [v for v in _real_result.blocking_violations if v.rule_id in _gated_rules]
        if _real_gated:
            raise GovernanceViolationError(None)

    # ------------------------------------------------------------------
    # Step 1: Instantiate all components fresh per call
    # ------------------------------------------------------------------
    engine: RiskEngine = RiskEngine()
    regime_detector: RegimeDetector = RegimeDetector()
    vol_tracker: VolatilityTracker = VolatilityTracker()
    state_estimator: StateEstimator = StateEstimator()

    # ------------------------------------------------------------------
    # Steps 2-7: State pipeline
    # ------------------------------------------------------------------
    if len(returns_history) > 0:
        features: dict = _extract_regime_features(returns_history)
        regime_result = regime_detector.detect_regime(features)
        vol_result = vol_tracker.estimate_volatility(returns_history)
        previous_state: LatentState = LatentState.default()
        predicted_state: LatentState = state_estimator.predict(previous_state)
        observation: dict = _build_observation_vector(regime_result, vol_result)
        _latent_state: LatentState = state_estimator.update(predicted_state, observation)

    # ------------------------------------------------------------------
    # Step 8: Risk assessment
    # ------------------------------------------------------------------
    risk_output = engine.assess(
        returns_history=returns_history,
        current_regime=current_regime,
        meta_uncertainty=meta_uncertainty,
    )

    # ------------------------------------------------------------------
    # Steps 9-11: Exposure -> positions -> return
    # ------------------------------------------------------------------
    exposure_weight: float = risk_output.exposure_weight
    positions: dict = route_exposure_to_positions(
        total_capital=total_capital,
        exposure_fraction=exposure_weight,
        asset_prices=asset_prices,
    )
    return positions


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def x_run_full_pipeline__mutmut_72(
    returns_history: list,
    current_regime: GlobalRegimeState,
    meta_uncertainty: float,
    total_capital: float,
    asset_prices: dict,
) -> dict:
    """
    Full deterministic pipeline from returns history to final positions.

    Step 0: Governance gate (GOV-01 + GOV-05 only).
    Steps 1-11: Unchanged from v1.1.0.

    Raises
    ------
    GovernanceViolationError
        meta_uncertainty out of [0.0, 1.0] or regime not GlobalRegimeState.
    ValueError
        Propagated from RiskEngine (invalid returns_history).
        Propagated from route_exposure_to_positions (invalid capital/prices).
    """
    # ------------------------------------------------------------------
    # Step 0: Governance Gate -- GOV-01 and GOV-05 only
    # ------------------------------------------------------------------

    # GOV-01: meta_uncertainty must be in [0.0, 1.0]
    _meta_invalid = (
        not isinstance(meta_uncertainty, (int, float))
        or not (0.0 <= float(meta_uncertainty) <= 1.0)
    )

    # GOV-05: regime must be a GlobalRegimeState instance
    _regime_invalid = not isinstance(current_regime, GlobalRegimeState)

    if _meta_invalid or _regime_invalid:
        # Build a minimal result via validate_pipeline_config using safe
        # stand-in values for parameters owned by downstream modules.
        _safe_capital = total_capital if (
            isinstance(total_capital, (int, float)) and float(total_capital) > 0
        ) else 1.0
        _safe_regime = current_regime if isinstance(
            current_regime, GlobalRegimeState
        ) else GlobalRegimeState.UNKNOWN
        _safe_meta = meta_uncertainty if (
            isinstance(meta_uncertainty, (int, float))
            and 0.0 <= float(meta_uncertainty) <= 1.0
        ) else 0.5

        _gov_result = validate_pipeline_config(
            meta_uncertainty=_safe_meta if not _meta_invalid else meta_uncertainty,
            initial_capital=_safe_capital,
            window=20,
            step=1,
            regime=_safe_regime,
            periods_per_year=252,
        )
        # Only raise for the rules we gate on
        _gated_rules = {"GOV-01", "GOV-05"}
        _gated = [v for v in _gov_result.blocking_violations if v.rule_id in _gated_rules]
        # Also run with the actual bad value so the error message is accurate
        _real_result = validate_pipeline_config(
            meta_uncertainty=meta_uncertainty if isinstance(meta_uncertainty, (int, float)) else 999,
            initial_capital=_safe_capital,
            window=20,
            step=1,
            regime=current_regime,
            periods_per_year=252,
        )
        _real_gated = [v for v in _real_result.blocking_violations if v.rule_id in _gated_rules]
        if _real_gated:
            raise GovernanceViolationError(_real_result)

    # ------------------------------------------------------------------
    # Step 1: Instantiate all components fresh per call
    # ------------------------------------------------------------------
    engine: RiskEngine = None
    regime_detector: RegimeDetector = RegimeDetector()
    vol_tracker: VolatilityTracker = VolatilityTracker()
    state_estimator: StateEstimator = StateEstimator()

    # ------------------------------------------------------------------
    # Steps 2-7: State pipeline
    # ------------------------------------------------------------------
    if len(returns_history) > 0:
        features: dict = _extract_regime_features(returns_history)
        regime_result = regime_detector.detect_regime(features)
        vol_result = vol_tracker.estimate_volatility(returns_history)
        previous_state: LatentState = LatentState.default()
        predicted_state: LatentState = state_estimator.predict(previous_state)
        observation: dict = _build_observation_vector(regime_result, vol_result)
        _latent_state: LatentState = state_estimator.update(predicted_state, observation)

    # ------------------------------------------------------------------
    # Step 8: Risk assessment
    # ------------------------------------------------------------------
    risk_output = engine.assess(
        returns_history=returns_history,
        current_regime=current_regime,
        meta_uncertainty=meta_uncertainty,
    )

    # ------------------------------------------------------------------
    # Steps 9-11: Exposure -> positions -> return
    # ------------------------------------------------------------------
    exposure_weight: float = risk_output.exposure_weight
    positions: dict = route_exposure_to_positions(
        total_capital=total_capital,
        exposure_fraction=exposure_weight,
        asset_prices=asset_prices,
    )
    return positions


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def x_run_full_pipeline__mutmut_73(
    returns_history: list,
    current_regime: GlobalRegimeState,
    meta_uncertainty: float,
    total_capital: float,
    asset_prices: dict,
) -> dict:
    """
    Full deterministic pipeline from returns history to final positions.

    Step 0: Governance gate (GOV-01 + GOV-05 only).
    Steps 1-11: Unchanged from v1.1.0.

    Raises
    ------
    GovernanceViolationError
        meta_uncertainty out of [0.0, 1.0] or regime not GlobalRegimeState.
    ValueError
        Propagated from RiskEngine (invalid returns_history).
        Propagated from route_exposure_to_positions (invalid capital/prices).
    """
    # ------------------------------------------------------------------
    # Step 0: Governance Gate -- GOV-01 and GOV-05 only
    # ------------------------------------------------------------------

    # GOV-01: meta_uncertainty must be in [0.0, 1.0]
    _meta_invalid = (
        not isinstance(meta_uncertainty, (int, float))
        or not (0.0 <= float(meta_uncertainty) <= 1.0)
    )

    # GOV-05: regime must be a GlobalRegimeState instance
    _regime_invalid = not isinstance(current_regime, GlobalRegimeState)

    if _meta_invalid or _regime_invalid:
        # Build a minimal result via validate_pipeline_config using safe
        # stand-in values for parameters owned by downstream modules.
        _safe_capital = total_capital if (
            isinstance(total_capital, (int, float)) and float(total_capital) > 0
        ) else 1.0
        _safe_regime = current_regime if isinstance(
            current_regime, GlobalRegimeState
        ) else GlobalRegimeState.UNKNOWN
        _safe_meta = meta_uncertainty if (
            isinstance(meta_uncertainty, (int, float))
            and 0.0 <= float(meta_uncertainty) <= 1.0
        ) else 0.5

        _gov_result = validate_pipeline_config(
            meta_uncertainty=_safe_meta if not _meta_invalid else meta_uncertainty,
            initial_capital=_safe_capital,
            window=20,
            step=1,
            regime=_safe_regime,
            periods_per_year=252,
        )
        # Only raise for the rules we gate on
        _gated_rules = {"GOV-01", "GOV-05"}
        _gated = [v for v in _gov_result.blocking_violations if v.rule_id in _gated_rules]
        # Also run with the actual bad value so the error message is accurate
        _real_result = validate_pipeline_config(
            meta_uncertainty=meta_uncertainty if isinstance(meta_uncertainty, (int, float)) else 999,
            initial_capital=_safe_capital,
            window=20,
            step=1,
            regime=current_regime,
            periods_per_year=252,
        )
        _real_gated = [v for v in _real_result.blocking_violations if v.rule_id in _gated_rules]
        if _real_gated:
            raise GovernanceViolationError(_real_result)

    # ------------------------------------------------------------------
    # Step 1: Instantiate all components fresh per call
    # ------------------------------------------------------------------
    engine: RiskEngine = RiskEngine()
    regime_detector: RegimeDetector = None
    vol_tracker: VolatilityTracker = VolatilityTracker()
    state_estimator: StateEstimator = StateEstimator()

    # ------------------------------------------------------------------
    # Steps 2-7: State pipeline
    # ------------------------------------------------------------------
    if len(returns_history) > 0:
        features: dict = _extract_regime_features(returns_history)
        regime_result = regime_detector.detect_regime(features)
        vol_result = vol_tracker.estimate_volatility(returns_history)
        previous_state: LatentState = LatentState.default()
        predicted_state: LatentState = state_estimator.predict(previous_state)
        observation: dict = _build_observation_vector(regime_result, vol_result)
        _latent_state: LatentState = state_estimator.update(predicted_state, observation)

    # ------------------------------------------------------------------
    # Step 8: Risk assessment
    # ------------------------------------------------------------------
    risk_output = engine.assess(
        returns_history=returns_history,
        current_regime=current_regime,
        meta_uncertainty=meta_uncertainty,
    )

    # ------------------------------------------------------------------
    # Steps 9-11: Exposure -> positions -> return
    # ------------------------------------------------------------------
    exposure_weight: float = risk_output.exposure_weight
    positions: dict = route_exposure_to_positions(
        total_capital=total_capital,
        exposure_fraction=exposure_weight,
        asset_prices=asset_prices,
    )
    return positions


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def x_run_full_pipeline__mutmut_74(
    returns_history: list,
    current_regime: GlobalRegimeState,
    meta_uncertainty: float,
    total_capital: float,
    asset_prices: dict,
) -> dict:
    """
    Full deterministic pipeline from returns history to final positions.

    Step 0: Governance gate (GOV-01 + GOV-05 only).
    Steps 1-11: Unchanged from v1.1.0.

    Raises
    ------
    GovernanceViolationError
        meta_uncertainty out of [0.0, 1.0] or regime not GlobalRegimeState.
    ValueError
        Propagated from RiskEngine (invalid returns_history).
        Propagated from route_exposure_to_positions (invalid capital/prices).
    """
    # ------------------------------------------------------------------
    # Step 0: Governance Gate -- GOV-01 and GOV-05 only
    # ------------------------------------------------------------------

    # GOV-01: meta_uncertainty must be in [0.0, 1.0]
    _meta_invalid = (
        not isinstance(meta_uncertainty, (int, float))
        or not (0.0 <= float(meta_uncertainty) <= 1.0)
    )

    # GOV-05: regime must be a GlobalRegimeState instance
    _regime_invalid = not isinstance(current_regime, GlobalRegimeState)

    if _meta_invalid or _regime_invalid:
        # Build a minimal result via validate_pipeline_config using safe
        # stand-in values for parameters owned by downstream modules.
        _safe_capital = total_capital if (
            isinstance(total_capital, (int, float)) and float(total_capital) > 0
        ) else 1.0
        _safe_regime = current_regime if isinstance(
            current_regime, GlobalRegimeState
        ) else GlobalRegimeState.UNKNOWN
        _safe_meta = meta_uncertainty if (
            isinstance(meta_uncertainty, (int, float))
            and 0.0 <= float(meta_uncertainty) <= 1.0
        ) else 0.5

        _gov_result = validate_pipeline_config(
            meta_uncertainty=_safe_meta if not _meta_invalid else meta_uncertainty,
            initial_capital=_safe_capital,
            window=20,
            step=1,
            regime=_safe_regime,
            periods_per_year=252,
        )
        # Only raise for the rules we gate on
        _gated_rules = {"GOV-01", "GOV-05"}
        _gated = [v for v in _gov_result.blocking_violations if v.rule_id in _gated_rules]
        # Also run with the actual bad value so the error message is accurate
        _real_result = validate_pipeline_config(
            meta_uncertainty=meta_uncertainty if isinstance(meta_uncertainty, (int, float)) else 999,
            initial_capital=_safe_capital,
            window=20,
            step=1,
            regime=current_regime,
            periods_per_year=252,
        )
        _real_gated = [v for v in _real_result.blocking_violations if v.rule_id in _gated_rules]
        if _real_gated:
            raise GovernanceViolationError(_real_result)

    # ------------------------------------------------------------------
    # Step 1: Instantiate all components fresh per call
    # ------------------------------------------------------------------
    engine: RiskEngine = RiskEngine()
    regime_detector: RegimeDetector = RegimeDetector()
    vol_tracker: VolatilityTracker = None
    state_estimator: StateEstimator = StateEstimator()

    # ------------------------------------------------------------------
    # Steps 2-7: State pipeline
    # ------------------------------------------------------------------
    if len(returns_history) > 0:
        features: dict = _extract_regime_features(returns_history)
        regime_result = regime_detector.detect_regime(features)
        vol_result = vol_tracker.estimate_volatility(returns_history)
        previous_state: LatentState = LatentState.default()
        predicted_state: LatentState = state_estimator.predict(previous_state)
        observation: dict = _build_observation_vector(regime_result, vol_result)
        _latent_state: LatentState = state_estimator.update(predicted_state, observation)

    # ------------------------------------------------------------------
    # Step 8: Risk assessment
    # ------------------------------------------------------------------
    risk_output = engine.assess(
        returns_history=returns_history,
        current_regime=current_regime,
        meta_uncertainty=meta_uncertainty,
    )

    # ------------------------------------------------------------------
    # Steps 9-11: Exposure -> positions -> return
    # ------------------------------------------------------------------
    exposure_weight: float = risk_output.exposure_weight
    positions: dict = route_exposure_to_positions(
        total_capital=total_capital,
        exposure_fraction=exposure_weight,
        asset_prices=asset_prices,
    )
    return positions


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def x_run_full_pipeline__mutmut_75(
    returns_history: list,
    current_regime: GlobalRegimeState,
    meta_uncertainty: float,
    total_capital: float,
    asset_prices: dict,
) -> dict:
    """
    Full deterministic pipeline from returns history to final positions.

    Step 0: Governance gate (GOV-01 + GOV-05 only).
    Steps 1-11: Unchanged from v1.1.0.

    Raises
    ------
    GovernanceViolationError
        meta_uncertainty out of [0.0, 1.0] or regime not GlobalRegimeState.
    ValueError
        Propagated from RiskEngine (invalid returns_history).
        Propagated from route_exposure_to_positions (invalid capital/prices).
    """
    # ------------------------------------------------------------------
    # Step 0: Governance Gate -- GOV-01 and GOV-05 only
    # ------------------------------------------------------------------

    # GOV-01: meta_uncertainty must be in [0.0, 1.0]
    _meta_invalid = (
        not isinstance(meta_uncertainty, (int, float))
        or not (0.0 <= float(meta_uncertainty) <= 1.0)
    )

    # GOV-05: regime must be a GlobalRegimeState instance
    _regime_invalid = not isinstance(current_regime, GlobalRegimeState)

    if _meta_invalid or _regime_invalid:
        # Build a minimal result via validate_pipeline_config using safe
        # stand-in values for parameters owned by downstream modules.
        _safe_capital = total_capital if (
            isinstance(total_capital, (int, float)) and float(total_capital) > 0
        ) else 1.0
        _safe_regime = current_regime if isinstance(
            current_regime, GlobalRegimeState
        ) else GlobalRegimeState.UNKNOWN
        _safe_meta = meta_uncertainty if (
            isinstance(meta_uncertainty, (int, float))
            and 0.0 <= float(meta_uncertainty) <= 1.0
        ) else 0.5

        _gov_result = validate_pipeline_config(
            meta_uncertainty=_safe_meta if not _meta_invalid else meta_uncertainty,
            initial_capital=_safe_capital,
            window=20,
            step=1,
            regime=_safe_regime,
            periods_per_year=252,
        )
        # Only raise for the rules we gate on
        _gated_rules = {"GOV-01", "GOV-05"}
        _gated = [v for v in _gov_result.blocking_violations if v.rule_id in _gated_rules]
        # Also run with the actual bad value so the error message is accurate
        _real_result = validate_pipeline_config(
            meta_uncertainty=meta_uncertainty if isinstance(meta_uncertainty, (int, float)) else 999,
            initial_capital=_safe_capital,
            window=20,
            step=1,
            regime=current_regime,
            periods_per_year=252,
        )
        _real_gated = [v for v in _real_result.blocking_violations if v.rule_id in _gated_rules]
        if _real_gated:
            raise GovernanceViolationError(_real_result)

    # ------------------------------------------------------------------
    # Step 1: Instantiate all components fresh per call
    # ------------------------------------------------------------------
    engine: RiskEngine = RiskEngine()
    regime_detector: RegimeDetector = RegimeDetector()
    vol_tracker: VolatilityTracker = VolatilityTracker()
    state_estimator: StateEstimator = None

    # ------------------------------------------------------------------
    # Steps 2-7: State pipeline
    # ------------------------------------------------------------------
    if len(returns_history) > 0:
        features: dict = _extract_regime_features(returns_history)
        regime_result = regime_detector.detect_regime(features)
        vol_result = vol_tracker.estimate_volatility(returns_history)
        previous_state: LatentState = LatentState.default()
        predicted_state: LatentState = state_estimator.predict(previous_state)
        observation: dict = _build_observation_vector(regime_result, vol_result)
        _latent_state: LatentState = state_estimator.update(predicted_state, observation)

    # ------------------------------------------------------------------
    # Step 8: Risk assessment
    # ------------------------------------------------------------------
    risk_output = engine.assess(
        returns_history=returns_history,
        current_regime=current_regime,
        meta_uncertainty=meta_uncertainty,
    )

    # ------------------------------------------------------------------
    # Steps 9-11: Exposure -> positions -> return
    # ------------------------------------------------------------------
    exposure_weight: float = risk_output.exposure_weight
    positions: dict = route_exposure_to_positions(
        total_capital=total_capital,
        exposure_fraction=exposure_weight,
        asset_prices=asset_prices,
    )
    return positions


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def x_run_full_pipeline__mutmut_76(
    returns_history: list,
    current_regime: GlobalRegimeState,
    meta_uncertainty: float,
    total_capital: float,
    asset_prices: dict,
) -> dict:
    """
    Full deterministic pipeline from returns history to final positions.

    Step 0: Governance gate (GOV-01 + GOV-05 only).
    Steps 1-11: Unchanged from v1.1.0.

    Raises
    ------
    GovernanceViolationError
        meta_uncertainty out of [0.0, 1.0] or regime not GlobalRegimeState.
    ValueError
        Propagated from RiskEngine (invalid returns_history).
        Propagated from route_exposure_to_positions (invalid capital/prices).
    """
    # ------------------------------------------------------------------
    # Step 0: Governance Gate -- GOV-01 and GOV-05 only
    # ------------------------------------------------------------------

    # GOV-01: meta_uncertainty must be in [0.0, 1.0]
    _meta_invalid = (
        not isinstance(meta_uncertainty, (int, float))
        or not (0.0 <= float(meta_uncertainty) <= 1.0)
    )

    # GOV-05: regime must be a GlobalRegimeState instance
    _regime_invalid = not isinstance(current_regime, GlobalRegimeState)

    if _meta_invalid or _regime_invalid:
        # Build a minimal result via validate_pipeline_config using safe
        # stand-in values for parameters owned by downstream modules.
        _safe_capital = total_capital if (
            isinstance(total_capital, (int, float)) and float(total_capital) > 0
        ) else 1.0
        _safe_regime = current_regime if isinstance(
            current_regime, GlobalRegimeState
        ) else GlobalRegimeState.UNKNOWN
        _safe_meta = meta_uncertainty if (
            isinstance(meta_uncertainty, (int, float))
            and 0.0 <= float(meta_uncertainty) <= 1.0
        ) else 0.5

        _gov_result = validate_pipeline_config(
            meta_uncertainty=_safe_meta if not _meta_invalid else meta_uncertainty,
            initial_capital=_safe_capital,
            window=20,
            step=1,
            regime=_safe_regime,
            periods_per_year=252,
        )
        # Only raise for the rules we gate on
        _gated_rules = {"GOV-01", "GOV-05"}
        _gated = [v for v in _gov_result.blocking_violations if v.rule_id in _gated_rules]
        # Also run with the actual bad value so the error message is accurate
        _real_result = validate_pipeline_config(
            meta_uncertainty=meta_uncertainty if isinstance(meta_uncertainty, (int, float)) else 999,
            initial_capital=_safe_capital,
            window=20,
            step=1,
            regime=current_regime,
            periods_per_year=252,
        )
        _real_gated = [v for v in _real_result.blocking_violations if v.rule_id in _gated_rules]
        if _real_gated:
            raise GovernanceViolationError(_real_result)

    # ------------------------------------------------------------------
    # Step 1: Instantiate all components fresh per call
    # ------------------------------------------------------------------
    engine: RiskEngine = RiskEngine()
    regime_detector: RegimeDetector = RegimeDetector()
    vol_tracker: VolatilityTracker = VolatilityTracker()
    state_estimator: StateEstimator = StateEstimator()

    # ------------------------------------------------------------------
    # Steps 2-7: State pipeline
    # ------------------------------------------------------------------
    if len(returns_history) >= 0:
        features: dict = _extract_regime_features(returns_history)
        regime_result = regime_detector.detect_regime(features)
        vol_result = vol_tracker.estimate_volatility(returns_history)
        previous_state: LatentState = LatentState.default()
        predicted_state: LatentState = state_estimator.predict(previous_state)
        observation: dict = _build_observation_vector(regime_result, vol_result)
        _latent_state: LatentState = state_estimator.update(predicted_state, observation)

    # ------------------------------------------------------------------
    # Step 8: Risk assessment
    # ------------------------------------------------------------------
    risk_output = engine.assess(
        returns_history=returns_history,
        current_regime=current_regime,
        meta_uncertainty=meta_uncertainty,
    )

    # ------------------------------------------------------------------
    # Steps 9-11: Exposure -> positions -> return
    # ------------------------------------------------------------------
    exposure_weight: float = risk_output.exposure_weight
    positions: dict = route_exposure_to_positions(
        total_capital=total_capital,
        exposure_fraction=exposure_weight,
        asset_prices=asset_prices,
    )
    return positions


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def x_run_full_pipeline__mutmut_77(
    returns_history: list,
    current_regime: GlobalRegimeState,
    meta_uncertainty: float,
    total_capital: float,
    asset_prices: dict,
) -> dict:
    """
    Full deterministic pipeline from returns history to final positions.

    Step 0: Governance gate (GOV-01 + GOV-05 only).
    Steps 1-11: Unchanged from v1.1.0.

    Raises
    ------
    GovernanceViolationError
        meta_uncertainty out of [0.0, 1.0] or regime not GlobalRegimeState.
    ValueError
        Propagated from RiskEngine (invalid returns_history).
        Propagated from route_exposure_to_positions (invalid capital/prices).
    """
    # ------------------------------------------------------------------
    # Step 0: Governance Gate -- GOV-01 and GOV-05 only
    # ------------------------------------------------------------------

    # GOV-01: meta_uncertainty must be in [0.0, 1.0]
    _meta_invalid = (
        not isinstance(meta_uncertainty, (int, float))
        or not (0.0 <= float(meta_uncertainty) <= 1.0)
    )

    # GOV-05: regime must be a GlobalRegimeState instance
    _regime_invalid = not isinstance(current_regime, GlobalRegimeState)

    if _meta_invalid or _regime_invalid:
        # Build a minimal result via validate_pipeline_config using safe
        # stand-in values for parameters owned by downstream modules.
        _safe_capital = total_capital if (
            isinstance(total_capital, (int, float)) and float(total_capital) > 0
        ) else 1.0
        _safe_regime = current_regime if isinstance(
            current_regime, GlobalRegimeState
        ) else GlobalRegimeState.UNKNOWN
        _safe_meta = meta_uncertainty if (
            isinstance(meta_uncertainty, (int, float))
            and 0.0 <= float(meta_uncertainty) <= 1.0
        ) else 0.5

        _gov_result = validate_pipeline_config(
            meta_uncertainty=_safe_meta if not _meta_invalid else meta_uncertainty,
            initial_capital=_safe_capital,
            window=20,
            step=1,
            regime=_safe_regime,
            periods_per_year=252,
        )
        # Only raise for the rules we gate on
        _gated_rules = {"GOV-01", "GOV-05"}
        _gated = [v for v in _gov_result.blocking_violations if v.rule_id in _gated_rules]
        # Also run with the actual bad value so the error message is accurate
        _real_result = validate_pipeline_config(
            meta_uncertainty=meta_uncertainty if isinstance(meta_uncertainty, (int, float)) else 999,
            initial_capital=_safe_capital,
            window=20,
            step=1,
            regime=current_regime,
            periods_per_year=252,
        )
        _real_gated = [v for v in _real_result.blocking_violations if v.rule_id in _gated_rules]
        if _real_gated:
            raise GovernanceViolationError(_real_result)

    # ------------------------------------------------------------------
    # Step 1: Instantiate all components fresh per call
    # ------------------------------------------------------------------
    engine: RiskEngine = RiskEngine()
    regime_detector: RegimeDetector = RegimeDetector()
    vol_tracker: VolatilityTracker = VolatilityTracker()
    state_estimator: StateEstimator = StateEstimator()

    # ------------------------------------------------------------------
    # Steps 2-7: State pipeline
    # ------------------------------------------------------------------
    if len(returns_history) > 1:
        features: dict = _extract_regime_features(returns_history)
        regime_result = regime_detector.detect_regime(features)
        vol_result = vol_tracker.estimate_volatility(returns_history)
        previous_state: LatentState = LatentState.default()
        predicted_state: LatentState = state_estimator.predict(previous_state)
        observation: dict = _build_observation_vector(regime_result, vol_result)
        _latent_state: LatentState = state_estimator.update(predicted_state, observation)

    # ------------------------------------------------------------------
    # Step 8: Risk assessment
    # ------------------------------------------------------------------
    risk_output = engine.assess(
        returns_history=returns_history,
        current_regime=current_regime,
        meta_uncertainty=meta_uncertainty,
    )

    # ------------------------------------------------------------------
    # Steps 9-11: Exposure -> positions -> return
    # ------------------------------------------------------------------
    exposure_weight: float = risk_output.exposure_weight
    positions: dict = route_exposure_to_positions(
        total_capital=total_capital,
        exposure_fraction=exposure_weight,
        asset_prices=asset_prices,
    )
    return positions


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def x_run_full_pipeline__mutmut_78(
    returns_history: list,
    current_regime: GlobalRegimeState,
    meta_uncertainty: float,
    total_capital: float,
    asset_prices: dict,
) -> dict:
    """
    Full deterministic pipeline from returns history to final positions.

    Step 0: Governance gate (GOV-01 + GOV-05 only).
    Steps 1-11: Unchanged from v1.1.0.

    Raises
    ------
    GovernanceViolationError
        meta_uncertainty out of [0.0, 1.0] or regime not GlobalRegimeState.
    ValueError
        Propagated from RiskEngine (invalid returns_history).
        Propagated from route_exposure_to_positions (invalid capital/prices).
    """
    # ------------------------------------------------------------------
    # Step 0: Governance Gate -- GOV-01 and GOV-05 only
    # ------------------------------------------------------------------

    # GOV-01: meta_uncertainty must be in [0.0, 1.0]
    _meta_invalid = (
        not isinstance(meta_uncertainty, (int, float))
        or not (0.0 <= float(meta_uncertainty) <= 1.0)
    )

    # GOV-05: regime must be a GlobalRegimeState instance
    _regime_invalid = not isinstance(current_regime, GlobalRegimeState)

    if _meta_invalid or _regime_invalid:
        # Build a minimal result via validate_pipeline_config using safe
        # stand-in values for parameters owned by downstream modules.
        _safe_capital = total_capital if (
            isinstance(total_capital, (int, float)) and float(total_capital) > 0
        ) else 1.0
        _safe_regime = current_regime if isinstance(
            current_regime, GlobalRegimeState
        ) else GlobalRegimeState.UNKNOWN
        _safe_meta = meta_uncertainty if (
            isinstance(meta_uncertainty, (int, float))
            and 0.0 <= float(meta_uncertainty) <= 1.0
        ) else 0.5

        _gov_result = validate_pipeline_config(
            meta_uncertainty=_safe_meta if not _meta_invalid else meta_uncertainty,
            initial_capital=_safe_capital,
            window=20,
            step=1,
            regime=_safe_regime,
            periods_per_year=252,
        )
        # Only raise for the rules we gate on
        _gated_rules = {"GOV-01", "GOV-05"}
        _gated = [v for v in _gov_result.blocking_violations if v.rule_id in _gated_rules]
        # Also run with the actual bad value so the error message is accurate
        _real_result = validate_pipeline_config(
            meta_uncertainty=meta_uncertainty if isinstance(meta_uncertainty, (int, float)) else 999,
            initial_capital=_safe_capital,
            window=20,
            step=1,
            regime=current_regime,
            periods_per_year=252,
        )
        _real_gated = [v for v in _real_result.blocking_violations if v.rule_id in _gated_rules]
        if _real_gated:
            raise GovernanceViolationError(_real_result)

    # ------------------------------------------------------------------
    # Step 1: Instantiate all components fresh per call
    # ------------------------------------------------------------------
    engine: RiskEngine = RiskEngine()
    regime_detector: RegimeDetector = RegimeDetector()
    vol_tracker: VolatilityTracker = VolatilityTracker()
    state_estimator: StateEstimator = StateEstimator()

    # ------------------------------------------------------------------
    # Steps 2-7: State pipeline
    # ------------------------------------------------------------------
    if len(returns_history) > 0:
        features: dict = None
        regime_result = regime_detector.detect_regime(features)
        vol_result = vol_tracker.estimate_volatility(returns_history)
        previous_state: LatentState = LatentState.default()
        predicted_state: LatentState = state_estimator.predict(previous_state)
        observation: dict = _build_observation_vector(regime_result, vol_result)
        _latent_state: LatentState = state_estimator.update(predicted_state, observation)

    # ------------------------------------------------------------------
    # Step 8: Risk assessment
    # ------------------------------------------------------------------
    risk_output = engine.assess(
        returns_history=returns_history,
        current_regime=current_regime,
        meta_uncertainty=meta_uncertainty,
    )

    # ------------------------------------------------------------------
    # Steps 9-11: Exposure -> positions -> return
    # ------------------------------------------------------------------
    exposure_weight: float = risk_output.exposure_weight
    positions: dict = route_exposure_to_positions(
        total_capital=total_capital,
        exposure_fraction=exposure_weight,
        asset_prices=asset_prices,
    )
    return positions


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def x_run_full_pipeline__mutmut_79(
    returns_history: list,
    current_regime: GlobalRegimeState,
    meta_uncertainty: float,
    total_capital: float,
    asset_prices: dict,
) -> dict:
    """
    Full deterministic pipeline from returns history to final positions.

    Step 0: Governance gate (GOV-01 + GOV-05 only).
    Steps 1-11: Unchanged from v1.1.0.

    Raises
    ------
    GovernanceViolationError
        meta_uncertainty out of [0.0, 1.0] or regime not GlobalRegimeState.
    ValueError
        Propagated from RiskEngine (invalid returns_history).
        Propagated from route_exposure_to_positions (invalid capital/prices).
    """
    # ------------------------------------------------------------------
    # Step 0: Governance Gate -- GOV-01 and GOV-05 only
    # ------------------------------------------------------------------

    # GOV-01: meta_uncertainty must be in [0.0, 1.0]
    _meta_invalid = (
        not isinstance(meta_uncertainty, (int, float))
        or not (0.0 <= float(meta_uncertainty) <= 1.0)
    )

    # GOV-05: regime must be a GlobalRegimeState instance
    _regime_invalid = not isinstance(current_regime, GlobalRegimeState)

    if _meta_invalid or _regime_invalid:
        # Build a minimal result via validate_pipeline_config using safe
        # stand-in values for parameters owned by downstream modules.
        _safe_capital = total_capital if (
            isinstance(total_capital, (int, float)) and float(total_capital) > 0
        ) else 1.0
        _safe_regime = current_regime if isinstance(
            current_regime, GlobalRegimeState
        ) else GlobalRegimeState.UNKNOWN
        _safe_meta = meta_uncertainty if (
            isinstance(meta_uncertainty, (int, float))
            and 0.0 <= float(meta_uncertainty) <= 1.0
        ) else 0.5

        _gov_result = validate_pipeline_config(
            meta_uncertainty=_safe_meta if not _meta_invalid else meta_uncertainty,
            initial_capital=_safe_capital,
            window=20,
            step=1,
            regime=_safe_regime,
            periods_per_year=252,
        )
        # Only raise for the rules we gate on
        _gated_rules = {"GOV-01", "GOV-05"}
        _gated = [v for v in _gov_result.blocking_violations if v.rule_id in _gated_rules]
        # Also run with the actual bad value so the error message is accurate
        _real_result = validate_pipeline_config(
            meta_uncertainty=meta_uncertainty if isinstance(meta_uncertainty, (int, float)) else 999,
            initial_capital=_safe_capital,
            window=20,
            step=1,
            regime=current_regime,
            periods_per_year=252,
        )
        _real_gated = [v for v in _real_result.blocking_violations if v.rule_id in _gated_rules]
        if _real_gated:
            raise GovernanceViolationError(_real_result)

    # ------------------------------------------------------------------
    # Step 1: Instantiate all components fresh per call
    # ------------------------------------------------------------------
    engine: RiskEngine = RiskEngine()
    regime_detector: RegimeDetector = RegimeDetector()
    vol_tracker: VolatilityTracker = VolatilityTracker()
    state_estimator: StateEstimator = StateEstimator()

    # ------------------------------------------------------------------
    # Steps 2-7: State pipeline
    # ------------------------------------------------------------------
    if len(returns_history) > 0:
        features: dict = _extract_regime_features(None)
        regime_result = regime_detector.detect_regime(features)
        vol_result = vol_tracker.estimate_volatility(returns_history)
        previous_state: LatentState = LatentState.default()
        predicted_state: LatentState = state_estimator.predict(previous_state)
        observation: dict = _build_observation_vector(regime_result, vol_result)
        _latent_state: LatentState = state_estimator.update(predicted_state, observation)

    # ------------------------------------------------------------------
    # Step 8: Risk assessment
    # ------------------------------------------------------------------
    risk_output = engine.assess(
        returns_history=returns_history,
        current_regime=current_regime,
        meta_uncertainty=meta_uncertainty,
    )

    # ------------------------------------------------------------------
    # Steps 9-11: Exposure -> positions -> return
    # ------------------------------------------------------------------
    exposure_weight: float = risk_output.exposure_weight
    positions: dict = route_exposure_to_positions(
        total_capital=total_capital,
        exposure_fraction=exposure_weight,
        asset_prices=asset_prices,
    )
    return positions


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def x_run_full_pipeline__mutmut_80(
    returns_history: list,
    current_regime: GlobalRegimeState,
    meta_uncertainty: float,
    total_capital: float,
    asset_prices: dict,
) -> dict:
    """
    Full deterministic pipeline from returns history to final positions.

    Step 0: Governance gate (GOV-01 + GOV-05 only).
    Steps 1-11: Unchanged from v1.1.0.

    Raises
    ------
    GovernanceViolationError
        meta_uncertainty out of [0.0, 1.0] or regime not GlobalRegimeState.
    ValueError
        Propagated from RiskEngine (invalid returns_history).
        Propagated from route_exposure_to_positions (invalid capital/prices).
    """
    # ------------------------------------------------------------------
    # Step 0: Governance Gate -- GOV-01 and GOV-05 only
    # ------------------------------------------------------------------

    # GOV-01: meta_uncertainty must be in [0.0, 1.0]
    _meta_invalid = (
        not isinstance(meta_uncertainty, (int, float))
        or not (0.0 <= float(meta_uncertainty) <= 1.0)
    )

    # GOV-05: regime must be a GlobalRegimeState instance
    _regime_invalid = not isinstance(current_regime, GlobalRegimeState)

    if _meta_invalid or _regime_invalid:
        # Build a minimal result via validate_pipeline_config using safe
        # stand-in values for parameters owned by downstream modules.
        _safe_capital = total_capital if (
            isinstance(total_capital, (int, float)) and float(total_capital) > 0
        ) else 1.0
        _safe_regime = current_regime if isinstance(
            current_regime, GlobalRegimeState
        ) else GlobalRegimeState.UNKNOWN
        _safe_meta = meta_uncertainty if (
            isinstance(meta_uncertainty, (int, float))
            and 0.0 <= float(meta_uncertainty) <= 1.0
        ) else 0.5

        _gov_result = validate_pipeline_config(
            meta_uncertainty=_safe_meta if not _meta_invalid else meta_uncertainty,
            initial_capital=_safe_capital,
            window=20,
            step=1,
            regime=_safe_regime,
            periods_per_year=252,
        )
        # Only raise for the rules we gate on
        _gated_rules = {"GOV-01", "GOV-05"}
        _gated = [v for v in _gov_result.blocking_violations if v.rule_id in _gated_rules]
        # Also run with the actual bad value so the error message is accurate
        _real_result = validate_pipeline_config(
            meta_uncertainty=meta_uncertainty if isinstance(meta_uncertainty, (int, float)) else 999,
            initial_capital=_safe_capital,
            window=20,
            step=1,
            regime=current_regime,
            periods_per_year=252,
        )
        _real_gated = [v for v in _real_result.blocking_violations if v.rule_id in _gated_rules]
        if _real_gated:
            raise GovernanceViolationError(_real_result)

    # ------------------------------------------------------------------
    # Step 1: Instantiate all components fresh per call
    # ------------------------------------------------------------------
    engine: RiskEngine = RiskEngine()
    regime_detector: RegimeDetector = RegimeDetector()
    vol_tracker: VolatilityTracker = VolatilityTracker()
    state_estimator: StateEstimator = StateEstimator()

    # ------------------------------------------------------------------
    # Steps 2-7: State pipeline
    # ------------------------------------------------------------------
    if len(returns_history) > 0:
        features: dict = _extract_regime_features(returns_history)
        regime_result = None
        vol_result = vol_tracker.estimate_volatility(returns_history)
        previous_state: LatentState = LatentState.default()
        predicted_state: LatentState = state_estimator.predict(previous_state)
        observation: dict = _build_observation_vector(regime_result, vol_result)
        _latent_state: LatentState = state_estimator.update(predicted_state, observation)

    # ------------------------------------------------------------------
    # Step 8: Risk assessment
    # ------------------------------------------------------------------
    risk_output = engine.assess(
        returns_history=returns_history,
        current_regime=current_regime,
        meta_uncertainty=meta_uncertainty,
    )

    # ------------------------------------------------------------------
    # Steps 9-11: Exposure -> positions -> return
    # ------------------------------------------------------------------
    exposure_weight: float = risk_output.exposure_weight
    positions: dict = route_exposure_to_positions(
        total_capital=total_capital,
        exposure_fraction=exposure_weight,
        asset_prices=asset_prices,
    )
    return positions


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def x_run_full_pipeline__mutmut_81(
    returns_history: list,
    current_regime: GlobalRegimeState,
    meta_uncertainty: float,
    total_capital: float,
    asset_prices: dict,
) -> dict:
    """
    Full deterministic pipeline from returns history to final positions.

    Step 0: Governance gate (GOV-01 + GOV-05 only).
    Steps 1-11: Unchanged from v1.1.0.

    Raises
    ------
    GovernanceViolationError
        meta_uncertainty out of [0.0, 1.0] or regime not GlobalRegimeState.
    ValueError
        Propagated from RiskEngine (invalid returns_history).
        Propagated from route_exposure_to_positions (invalid capital/prices).
    """
    # ------------------------------------------------------------------
    # Step 0: Governance Gate -- GOV-01 and GOV-05 only
    # ------------------------------------------------------------------

    # GOV-01: meta_uncertainty must be in [0.0, 1.0]
    _meta_invalid = (
        not isinstance(meta_uncertainty, (int, float))
        or not (0.0 <= float(meta_uncertainty) <= 1.0)
    )

    # GOV-05: regime must be a GlobalRegimeState instance
    _regime_invalid = not isinstance(current_regime, GlobalRegimeState)

    if _meta_invalid or _regime_invalid:
        # Build a minimal result via validate_pipeline_config using safe
        # stand-in values for parameters owned by downstream modules.
        _safe_capital = total_capital if (
            isinstance(total_capital, (int, float)) and float(total_capital) > 0
        ) else 1.0
        _safe_regime = current_regime if isinstance(
            current_regime, GlobalRegimeState
        ) else GlobalRegimeState.UNKNOWN
        _safe_meta = meta_uncertainty if (
            isinstance(meta_uncertainty, (int, float))
            and 0.0 <= float(meta_uncertainty) <= 1.0
        ) else 0.5

        _gov_result = validate_pipeline_config(
            meta_uncertainty=_safe_meta if not _meta_invalid else meta_uncertainty,
            initial_capital=_safe_capital,
            window=20,
            step=1,
            regime=_safe_regime,
            periods_per_year=252,
        )
        # Only raise for the rules we gate on
        _gated_rules = {"GOV-01", "GOV-05"}
        _gated = [v for v in _gov_result.blocking_violations if v.rule_id in _gated_rules]
        # Also run with the actual bad value so the error message is accurate
        _real_result = validate_pipeline_config(
            meta_uncertainty=meta_uncertainty if isinstance(meta_uncertainty, (int, float)) else 999,
            initial_capital=_safe_capital,
            window=20,
            step=1,
            regime=current_regime,
            periods_per_year=252,
        )
        _real_gated = [v for v in _real_result.blocking_violations if v.rule_id in _gated_rules]
        if _real_gated:
            raise GovernanceViolationError(_real_result)

    # ------------------------------------------------------------------
    # Step 1: Instantiate all components fresh per call
    # ------------------------------------------------------------------
    engine: RiskEngine = RiskEngine()
    regime_detector: RegimeDetector = RegimeDetector()
    vol_tracker: VolatilityTracker = VolatilityTracker()
    state_estimator: StateEstimator = StateEstimator()

    # ------------------------------------------------------------------
    # Steps 2-7: State pipeline
    # ------------------------------------------------------------------
    if len(returns_history) > 0:
        features: dict = _extract_regime_features(returns_history)
        regime_result = regime_detector.detect_regime(None)
        vol_result = vol_tracker.estimate_volatility(returns_history)
        previous_state: LatentState = LatentState.default()
        predicted_state: LatentState = state_estimator.predict(previous_state)
        observation: dict = _build_observation_vector(regime_result, vol_result)
        _latent_state: LatentState = state_estimator.update(predicted_state, observation)

    # ------------------------------------------------------------------
    # Step 8: Risk assessment
    # ------------------------------------------------------------------
    risk_output = engine.assess(
        returns_history=returns_history,
        current_regime=current_regime,
        meta_uncertainty=meta_uncertainty,
    )

    # ------------------------------------------------------------------
    # Steps 9-11: Exposure -> positions -> return
    # ------------------------------------------------------------------
    exposure_weight: float = risk_output.exposure_weight
    positions: dict = route_exposure_to_positions(
        total_capital=total_capital,
        exposure_fraction=exposure_weight,
        asset_prices=asset_prices,
    )
    return positions


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def x_run_full_pipeline__mutmut_82(
    returns_history: list,
    current_regime: GlobalRegimeState,
    meta_uncertainty: float,
    total_capital: float,
    asset_prices: dict,
) -> dict:
    """
    Full deterministic pipeline from returns history to final positions.

    Step 0: Governance gate (GOV-01 + GOV-05 only).
    Steps 1-11: Unchanged from v1.1.0.

    Raises
    ------
    GovernanceViolationError
        meta_uncertainty out of [0.0, 1.0] or regime not GlobalRegimeState.
    ValueError
        Propagated from RiskEngine (invalid returns_history).
        Propagated from route_exposure_to_positions (invalid capital/prices).
    """
    # ------------------------------------------------------------------
    # Step 0: Governance Gate -- GOV-01 and GOV-05 only
    # ------------------------------------------------------------------

    # GOV-01: meta_uncertainty must be in [0.0, 1.0]
    _meta_invalid = (
        not isinstance(meta_uncertainty, (int, float))
        or not (0.0 <= float(meta_uncertainty) <= 1.0)
    )

    # GOV-05: regime must be a GlobalRegimeState instance
    _regime_invalid = not isinstance(current_regime, GlobalRegimeState)

    if _meta_invalid or _regime_invalid:
        # Build a minimal result via validate_pipeline_config using safe
        # stand-in values for parameters owned by downstream modules.
        _safe_capital = total_capital if (
            isinstance(total_capital, (int, float)) and float(total_capital) > 0
        ) else 1.0
        _safe_regime = current_regime if isinstance(
            current_regime, GlobalRegimeState
        ) else GlobalRegimeState.UNKNOWN
        _safe_meta = meta_uncertainty if (
            isinstance(meta_uncertainty, (int, float))
            and 0.0 <= float(meta_uncertainty) <= 1.0
        ) else 0.5

        _gov_result = validate_pipeline_config(
            meta_uncertainty=_safe_meta if not _meta_invalid else meta_uncertainty,
            initial_capital=_safe_capital,
            window=20,
            step=1,
            regime=_safe_regime,
            periods_per_year=252,
        )
        # Only raise for the rules we gate on
        _gated_rules = {"GOV-01", "GOV-05"}
        _gated = [v for v in _gov_result.blocking_violations if v.rule_id in _gated_rules]
        # Also run with the actual bad value so the error message is accurate
        _real_result = validate_pipeline_config(
            meta_uncertainty=meta_uncertainty if isinstance(meta_uncertainty, (int, float)) else 999,
            initial_capital=_safe_capital,
            window=20,
            step=1,
            regime=current_regime,
            periods_per_year=252,
        )
        _real_gated = [v for v in _real_result.blocking_violations if v.rule_id in _gated_rules]
        if _real_gated:
            raise GovernanceViolationError(_real_result)

    # ------------------------------------------------------------------
    # Step 1: Instantiate all components fresh per call
    # ------------------------------------------------------------------
    engine: RiskEngine = RiskEngine()
    regime_detector: RegimeDetector = RegimeDetector()
    vol_tracker: VolatilityTracker = VolatilityTracker()
    state_estimator: StateEstimator = StateEstimator()

    # ------------------------------------------------------------------
    # Steps 2-7: State pipeline
    # ------------------------------------------------------------------
    if len(returns_history) > 0:
        features: dict = _extract_regime_features(returns_history)
        regime_result = regime_detector.detect_regime(features)
        vol_result = None
        previous_state: LatentState = LatentState.default()
        predicted_state: LatentState = state_estimator.predict(previous_state)
        observation: dict = _build_observation_vector(regime_result, vol_result)
        _latent_state: LatentState = state_estimator.update(predicted_state, observation)

    # ------------------------------------------------------------------
    # Step 8: Risk assessment
    # ------------------------------------------------------------------
    risk_output = engine.assess(
        returns_history=returns_history,
        current_regime=current_regime,
        meta_uncertainty=meta_uncertainty,
    )

    # ------------------------------------------------------------------
    # Steps 9-11: Exposure -> positions -> return
    # ------------------------------------------------------------------
    exposure_weight: float = risk_output.exposure_weight
    positions: dict = route_exposure_to_positions(
        total_capital=total_capital,
        exposure_fraction=exposure_weight,
        asset_prices=asset_prices,
    )
    return positions


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def x_run_full_pipeline__mutmut_83(
    returns_history: list,
    current_regime: GlobalRegimeState,
    meta_uncertainty: float,
    total_capital: float,
    asset_prices: dict,
) -> dict:
    """
    Full deterministic pipeline from returns history to final positions.

    Step 0: Governance gate (GOV-01 + GOV-05 only).
    Steps 1-11: Unchanged from v1.1.0.

    Raises
    ------
    GovernanceViolationError
        meta_uncertainty out of [0.0, 1.0] or regime not GlobalRegimeState.
    ValueError
        Propagated from RiskEngine (invalid returns_history).
        Propagated from route_exposure_to_positions (invalid capital/prices).
    """
    # ------------------------------------------------------------------
    # Step 0: Governance Gate -- GOV-01 and GOV-05 only
    # ------------------------------------------------------------------

    # GOV-01: meta_uncertainty must be in [0.0, 1.0]
    _meta_invalid = (
        not isinstance(meta_uncertainty, (int, float))
        or not (0.0 <= float(meta_uncertainty) <= 1.0)
    )

    # GOV-05: regime must be a GlobalRegimeState instance
    _regime_invalid = not isinstance(current_regime, GlobalRegimeState)

    if _meta_invalid or _regime_invalid:
        # Build a minimal result via validate_pipeline_config using safe
        # stand-in values for parameters owned by downstream modules.
        _safe_capital = total_capital if (
            isinstance(total_capital, (int, float)) and float(total_capital) > 0
        ) else 1.0
        _safe_regime = current_regime if isinstance(
            current_regime, GlobalRegimeState
        ) else GlobalRegimeState.UNKNOWN
        _safe_meta = meta_uncertainty if (
            isinstance(meta_uncertainty, (int, float))
            and 0.0 <= float(meta_uncertainty) <= 1.0
        ) else 0.5

        _gov_result = validate_pipeline_config(
            meta_uncertainty=_safe_meta if not _meta_invalid else meta_uncertainty,
            initial_capital=_safe_capital,
            window=20,
            step=1,
            regime=_safe_regime,
            periods_per_year=252,
        )
        # Only raise for the rules we gate on
        _gated_rules = {"GOV-01", "GOV-05"}
        _gated = [v for v in _gov_result.blocking_violations if v.rule_id in _gated_rules]
        # Also run with the actual bad value so the error message is accurate
        _real_result = validate_pipeline_config(
            meta_uncertainty=meta_uncertainty if isinstance(meta_uncertainty, (int, float)) else 999,
            initial_capital=_safe_capital,
            window=20,
            step=1,
            regime=current_regime,
            periods_per_year=252,
        )
        _real_gated = [v for v in _real_result.blocking_violations if v.rule_id in _gated_rules]
        if _real_gated:
            raise GovernanceViolationError(_real_result)

    # ------------------------------------------------------------------
    # Step 1: Instantiate all components fresh per call
    # ------------------------------------------------------------------
    engine: RiskEngine = RiskEngine()
    regime_detector: RegimeDetector = RegimeDetector()
    vol_tracker: VolatilityTracker = VolatilityTracker()
    state_estimator: StateEstimator = StateEstimator()

    # ------------------------------------------------------------------
    # Steps 2-7: State pipeline
    # ------------------------------------------------------------------
    if len(returns_history) > 0:
        features: dict = _extract_regime_features(returns_history)
        regime_result = regime_detector.detect_regime(features)
        vol_result = vol_tracker.estimate_volatility(None)
        previous_state: LatentState = LatentState.default()
        predicted_state: LatentState = state_estimator.predict(previous_state)
        observation: dict = _build_observation_vector(regime_result, vol_result)
        _latent_state: LatentState = state_estimator.update(predicted_state, observation)

    # ------------------------------------------------------------------
    # Step 8: Risk assessment
    # ------------------------------------------------------------------
    risk_output = engine.assess(
        returns_history=returns_history,
        current_regime=current_regime,
        meta_uncertainty=meta_uncertainty,
    )

    # ------------------------------------------------------------------
    # Steps 9-11: Exposure -> positions -> return
    # ------------------------------------------------------------------
    exposure_weight: float = risk_output.exposure_weight
    positions: dict = route_exposure_to_positions(
        total_capital=total_capital,
        exposure_fraction=exposure_weight,
        asset_prices=asset_prices,
    )
    return positions


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def x_run_full_pipeline__mutmut_84(
    returns_history: list,
    current_regime: GlobalRegimeState,
    meta_uncertainty: float,
    total_capital: float,
    asset_prices: dict,
) -> dict:
    """
    Full deterministic pipeline from returns history to final positions.

    Step 0: Governance gate (GOV-01 + GOV-05 only).
    Steps 1-11: Unchanged from v1.1.0.

    Raises
    ------
    GovernanceViolationError
        meta_uncertainty out of [0.0, 1.0] or regime not GlobalRegimeState.
    ValueError
        Propagated from RiskEngine (invalid returns_history).
        Propagated from route_exposure_to_positions (invalid capital/prices).
    """
    # ------------------------------------------------------------------
    # Step 0: Governance Gate -- GOV-01 and GOV-05 only
    # ------------------------------------------------------------------

    # GOV-01: meta_uncertainty must be in [0.0, 1.0]
    _meta_invalid = (
        not isinstance(meta_uncertainty, (int, float))
        or not (0.0 <= float(meta_uncertainty) <= 1.0)
    )

    # GOV-05: regime must be a GlobalRegimeState instance
    _regime_invalid = not isinstance(current_regime, GlobalRegimeState)

    if _meta_invalid or _regime_invalid:
        # Build a minimal result via validate_pipeline_config using safe
        # stand-in values for parameters owned by downstream modules.
        _safe_capital = total_capital if (
            isinstance(total_capital, (int, float)) and float(total_capital) > 0
        ) else 1.0
        _safe_regime = current_regime if isinstance(
            current_regime, GlobalRegimeState
        ) else GlobalRegimeState.UNKNOWN
        _safe_meta = meta_uncertainty if (
            isinstance(meta_uncertainty, (int, float))
            and 0.0 <= float(meta_uncertainty) <= 1.0
        ) else 0.5

        _gov_result = validate_pipeline_config(
            meta_uncertainty=_safe_meta if not _meta_invalid else meta_uncertainty,
            initial_capital=_safe_capital,
            window=20,
            step=1,
            regime=_safe_regime,
            periods_per_year=252,
        )
        # Only raise for the rules we gate on
        _gated_rules = {"GOV-01", "GOV-05"}
        _gated = [v for v in _gov_result.blocking_violations if v.rule_id in _gated_rules]
        # Also run with the actual bad value so the error message is accurate
        _real_result = validate_pipeline_config(
            meta_uncertainty=meta_uncertainty if isinstance(meta_uncertainty, (int, float)) else 999,
            initial_capital=_safe_capital,
            window=20,
            step=1,
            regime=current_regime,
            periods_per_year=252,
        )
        _real_gated = [v for v in _real_result.blocking_violations if v.rule_id in _gated_rules]
        if _real_gated:
            raise GovernanceViolationError(_real_result)

    # ------------------------------------------------------------------
    # Step 1: Instantiate all components fresh per call
    # ------------------------------------------------------------------
    engine: RiskEngine = RiskEngine()
    regime_detector: RegimeDetector = RegimeDetector()
    vol_tracker: VolatilityTracker = VolatilityTracker()
    state_estimator: StateEstimator = StateEstimator()

    # ------------------------------------------------------------------
    # Steps 2-7: State pipeline
    # ------------------------------------------------------------------
    if len(returns_history) > 0:
        features: dict = _extract_regime_features(returns_history)
        regime_result = regime_detector.detect_regime(features)
        vol_result = vol_tracker.estimate_volatility(returns_history)
        previous_state: LatentState = None
        predicted_state: LatentState = state_estimator.predict(previous_state)
        observation: dict = _build_observation_vector(regime_result, vol_result)
        _latent_state: LatentState = state_estimator.update(predicted_state, observation)

    # ------------------------------------------------------------------
    # Step 8: Risk assessment
    # ------------------------------------------------------------------
    risk_output = engine.assess(
        returns_history=returns_history,
        current_regime=current_regime,
        meta_uncertainty=meta_uncertainty,
    )

    # ------------------------------------------------------------------
    # Steps 9-11: Exposure -> positions -> return
    # ------------------------------------------------------------------
    exposure_weight: float = risk_output.exposure_weight
    positions: dict = route_exposure_to_positions(
        total_capital=total_capital,
        exposure_fraction=exposure_weight,
        asset_prices=asset_prices,
    )
    return positions


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def x_run_full_pipeline__mutmut_85(
    returns_history: list,
    current_regime: GlobalRegimeState,
    meta_uncertainty: float,
    total_capital: float,
    asset_prices: dict,
) -> dict:
    """
    Full deterministic pipeline from returns history to final positions.

    Step 0: Governance gate (GOV-01 + GOV-05 only).
    Steps 1-11: Unchanged from v1.1.0.

    Raises
    ------
    GovernanceViolationError
        meta_uncertainty out of [0.0, 1.0] or regime not GlobalRegimeState.
    ValueError
        Propagated from RiskEngine (invalid returns_history).
        Propagated from route_exposure_to_positions (invalid capital/prices).
    """
    # ------------------------------------------------------------------
    # Step 0: Governance Gate -- GOV-01 and GOV-05 only
    # ------------------------------------------------------------------

    # GOV-01: meta_uncertainty must be in [0.0, 1.0]
    _meta_invalid = (
        not isinstance(meta_uncertainty, (int, float))
        or not (0.0 <= float(meta_uncertainty) <= 1.0)
    )

    # GOV-05: regime must be a GlobalRegimeState instance
    _regime_invalid = not isinstance(current_regime, GlobalRegimeState)

    if _meta_invalid or _regime_invalid:
        # Build a minimal result via validate_pipeline_config using safe
        # stand-in values for parameters owned by downstream modules.
        _safe_capital = total_capital if (
            isinstance(total_capital, (int, float)) and float(total_capital) > 0
        ) else 1.0
        _safe_regime = current_regime if isinstance(
            current_regime, GlobalRegimeState
        ) else GlobalRegimeState.UNKNOWN
        _safe_meta = meta_uncertainty if (
            isinstance(meta_uncertainty, (int, float))
            and 0.0 <= float(meta_uncertainty) <= 1.0
        ) else 0.5

        _gov_result = validate_pipeline_config(
            meta_uncertainty=_safe_meta if not _meta_invalid else meta_uncertainty,
            initial_capital=_safe_capital,
            window=20,
            step=1,
            regime=_safe_regime,
            periods_per_year=252,
        )
        # Only raise for the rules we gate on
        _gated_rules = {"GOV-01", "GOV-05"}
        _gated = [v for v in _gov_result.blocking_violations if v.rule_id in _gated_rules]
        # Also run with the actual bad value so the error message is accurate
        _real_result = validate_pipeline_config(
            meta_uncertainty=meta_uncertainty if isinstance(meta_uncertainty, (int, float)) else 999,
            initial_capital=_safe_capital,
            window=20,
            step=1,
            regime=current_regime,
            periods_per_year=252,
        )
        _real_gated = [v for v in _real_result.blocking_violations if v.rule_id in _gated_rules]
        if _real_gated:
            raise GovernanceViolationError(_real_result)

    # ------------------------------------------------------------------
    # Step 1: Instantiate all components fresh per call
    # ------------------------------------------------------------------
    engine: RiskEngine = RiskEngine()
    regime_detector: RegimeDetector = RegimeDetector()
    vol_tracker: VolatilityTracker = VolatilityTracker()
    state_estimator: StateEstimator = StateEstimator()

    # ------------------------------------------------------------------
    # Steps 2-7: State pipeline
    # ------------------------------------------------------------------
    if len(returns_history) > 0:
        features: dict = _extract_regime_features(returns_history)
        regime_result = regime_detector.detect_regime(features)
        vol_result = vol_tracker.estimate_volatility(returns_history)
        previous_state: LatentState = LatentState.default()
        predicted_state: LatentState = None
        observation: dict = _build_observation_vector(regime_result, vol_result)
        _latent_state: LatentState = state_estimator.update(predicted_state, observation)

    # ------------------------------------------------------------------
    # Step 8: Risk assessment
    # ------------------------------------------------------------------
    risk_output = engine.assess(
        returns_history=returns_history,
        current_regime=current_regime,
        meta_uncertainty=meta_uncertainty,
    )

    # ------------------------------------------------------------------
    # Steps 9-11: Exposure -> positions -> return
    # ------------------------------------------------------------------
    exposure_weight: float = risk_output.exposure_weight
    positions: dict = route_exposure_to_positions(
        total_capital=total_capital,
        exposure_fraction=exposure_weight,
        asset_prices=asset_prices,
    )
    return positions


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def x_run_full_pipeline__mutmut_86(
    returns_history: list,
    current_regime: GlobalRegimeState,
    meta_uncertainty: float,
    total_capital: float,
    asset_prices: dict,
) -> dict:
    """
    Full deterministic pipeline from returns history to final positions.

    Step 0: Governance gate (GOV-01 + GOV-05 only).
    Steps 1-11: Unchanged from v1.1.0.

    Raises
    ------
    GovernanceViolationError
        meta_uncertainty out of [0.0, 1.0] or regime not GlobalRegimeState.
    ValueError
        Propagated from RiskEngine (invalid returns_history).
        Propagated from route_exposure_to_positions (invalid capital/prices).
    """
    # ------------------------------------------------------------------
    # Step 0: Governance Gate -- GOV-01 and GOV-05 only
    # ------------------------------------------------------------------

    # GOV-01: meta_uncertainty must be in [0.0, 1.0]
    _meta_invalid = (
        not isinstance(meta_uncertainty, (int, float))
        or not (0.0 <= float(meta_uncertainty) <= 1.0)
    )

    # GOV-05: regime must be a GlobalRegimeState instance
    _regime_invalid = not isinstance(current_regime, GlobalRegimeState)

    if _meta_invalid or _regime_invalid:
        # Build a minimal result via validate_pipeline_config using safe
        # stand-in values for parameters owned by downstream modules.
        _safe_capital = total_capital if (
            isinstance(total_capital, (int, float)) and float(total_capital) > 0
        ) else 1.0
        _safe_regime = current_regime if isinstance(
            current_regime, GlobalRegimeState
        ) else GlobalRegimeState.UNKNOWN
        _safe_meta = meta_uncertainty if (
            isinstance(meta_uncertainty, (int, float))
            and 0.0 <= float(meta_uncertainty) <= 1.0
        ) else 0.5

        _gov_result = validate_pipeline_config(
            meta_uncertainty=_safe_meta if not _meta_invalid else meta_uncertainty,
            initial_capital=_safe_capital,
            window=20,
            step=1,
            regime=_safe_regime,
            periods_per_year=252,
        )
        # Only raise for the rules we gate on
        _gated_rules = {"GOV-01", "GOV-05"}
        _gated = [v for v in _gov_result.blocking_violations if v.rule_id in _gated_rules]
        # Also run with the actual bad value so the error message is accurate
        _real_result = validate_pipeline_config(
            meta_uncertainty=meta_uncertainty if isinstance(meta_uncertainty, (int, float)) else 999,
            initial_capital=_safe_capital,
            window=20,
            step=1,
            regime=current_regime,
            periods_per_year=252,
        )
        _real_gated = [v for v in _real_result.blocking_violations if v.rule_id in _gated_rules]
        if _real_gated:
            raise GovernanceViolationError(_real_result)

    # ------------------------------------------------------------------
    # Step 1: Instantiate all components fresh per call
    # ------------------------------------------------------------------
    engine: RiskEngine = RiskEngine()
    regime_detector: RegimeDetector = RegimeDetector()
    vol_tracker: VolatilityTracker = VolatilityTracker()
    state_estimator: StateEstimator = StateEstimator()

    # ------------------------------------------------------------------
    # Steps 2-7: State pipeline
    # ------------------------------------------------------------------
    if len(returns_history) > 0:
        features: dict = _extract_regime_features(returns_history)
        regime_result = regime_detector.detect_regime(features)
        vol_result = vol_tracker.estimate_volatility(returns_history)
        previous_state: LatentState = LatentState.default()
        predicted_state: LatentState = state_estimator.predict(None)
        observation: dict = _build_observation_vector(regime_result, vol_result)
        _latent_state: LatentState = state_estimator.update(predicted_state, observation)

    # ------------------------------------------------------------------
    # Step 8: Risk assessment
    # ------------------------------------------------------------------
    risk_output = engine.assess(
        returns_history=returns_history,
        current_regime=current_regime,
        meta_uncertainty=meta_uncertainty,
    )

    # ------------------------------------------------------------------
    # Steps 9-11: Exposure -> positions -> return
    # ------------------------------------------------------------------
    exposure_weight: float = risk_output.exposure_weight
    positions: dict = route_exposure_to_positions(
        total_capital=total_capital,
        exposure_fraction=exposure_weight,
        asset_prices=asset_prices,
    )
    return positions


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def x_run_full_pipeline__mutmut_87(
    returns_history: list,
    current_regime: GlobalRegimeState,
    meta_uncertainty: float,
    total_capital: float,
    asset_prices: dict,
) -> dict:
    """
    Full deterministic pipeline from returns history to final positions.

    Step 0: Governance gate (GOV-01 + GOV-05 only).
    Steps 1-11: Unchanged from v1.1.0.

    Raises
    ------
    GovernanceViolationError
        meta_uncertainty out of [0.0, 1.0] or regime not GlobalRegimeState.
    ValueError
        Propagated from RiskEngine (invalid returns_history).
        Propagated from route_exposure_to_positions (invalid capital/prices).
    """
    # ------------------------------------------------------------------
    # Step 0: Governance Gate -- GOV-01 and GOV-05 only
    # ------------------------------------------------------------------

    # GOV-01: meta_uncertainty must be in [0.0, 1.0]
    _meta_invalid = (
        not isinstance(meta_uncertainty, (int, float))
        or not (0.0 <= float(meta_uncertainty) <= 1.0)
    )

    # GOV-05: regime must be a GlobalRegimeState instance
    _regime_invalid = not isinstance(current_regime, GlobalRegimeState)

    if _meta_invalid or _regime_invalid:
        # Build a minimal result via validate_pipeline_config using safe
        # stand-in values for parameters owned by downstream modules.
        _safe_capital = total_capital if (
            isinstance(total_capital, (int, float)) and float(total_capital) > 0
        ) else 1.0
        _safe_regime = current_regime if isinstance(
            current_regime, GlobalRegimeState
        ) else GlobalRegimeState.UNKNOWN
        _safe_meta = meta_uncertainty if (
            isinstance(meta_uncertainty, (int, float))
            and 0.0 <= float(meta_uncertainty) <= 1.0
        ) else 0.5

        _gov_result = validate_pipeline_config(
            meta_uncertainty=_safe_meta if not _meta_invalid else meta_uncertainty,
            initial_capital=_safe_capital,
            window=20,
            step=1,
            regime=_safe_regime,
            periods_per_year=252,
        )
        # Only raise for the rules we gate on
        _gated_rules = {"GOV-01", "GOV-05"}
        _gated = [v for v in _gov_result.blocking_violations if v.rule_id in _gated_rules]
        # Also run with the actual bad value so the error message is accurate
        _real_result = validate_pipeline_config(
            meta_uncertainty=meta_uncertainty if isinstance(meta_uncertainty, (int, float)) else 999,
            initial_capital=_safe_capital,
            window=20,
            step=1,
            regime=current_regime,
            periods_per_year=252,
        )
        _real_gated = [v for v in _real_result.blocking_violations if v.rule_id in _gated_rules]
        if _real_gated:
            raise GovernanceViolationError(_real_result)

    # ------------------------------------------------------------------
    # Step 1: Instantiate all components fresh per call
    # ------------------------------------------------------------------
    engine: RiskEngine = RiskEngine()
    regime_detector: RegimeDetector = RegimeDetector()
    vol_tracker: VolatilityTracker = VolatilityTracker()
    state_estimator: StateEstimator = StateEstimator()

    # ------------------------------------------------------------------
    # Steps 2-7: State pipeline
    # ------------------------------------------------------------------
    if len(returns_history) > 0:
        features: dict = _extract_regime_features(returns_history)
        regime_result = regime_detector.detect_regime(features)
        vol_result = vol_tracker.estimate_volatility(returns_history)
        previous_state: LatentState = LatentState.default()
        predicted_state: LatentState = state_estimator.predict(previous_state)
        observation: dict = None
        _latent_state: LatentState = state_estimator.update(predicted_state, observation)

    # ------------------------------------------------------------------
    # Step 8: Risk assessment
    # ------------------------------------------------------------------
    risk_output = engine.assess(
        returns_history=returns_history,
        current_regime=current_regime,
        meta_uncertainty=meta_uncertainty,
    )

    # ------------------------------------------------------------------
    # Steps 9-11: Exposure -> positions -> return
    # ------------------------------------------------------------------
    exposure_weight: float = risk_output.exposure_weight
    positions: dict = route_exposure_to_positions(
        total_capital=total_capital,
        exposure_fraction=exposure_weight,
        asset_prices=asset_prices,
    )
    return positions


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def x_run_full_pipeline__mutmut_88(
    returns_history: list,
    current_regime: GlobalRegimeState,
    meta_uncertainty: float,
    total_capital: float,
    asset_prices: dict,
) -> dict:
    """
    Full deterministic pipeline from returns history to final positions.

    Step 0: Governance gate (GOV-01 + GOV-05 only).
    Steps 1-11: Unchanged from v1.1.0.

    Raises
    ------
    GovernanceViolationError
        meta_uncertainty out of [0.0, 1.0] or regime not GlobalRegimeState.
    ValueError
        Propagated from RiskEngine (invalid returns_history).
        Propagated from route_exposure_to_positions (invalid capital/prices).
    """
    # ------------------------------------------------------------------
    # Step 0: Governance Gate -- GOV-01 and GOV-05 only
    # ------------------------------------------------------------------

    # GOV-01: meta_uncertainty must be in [0.0, 1.0]
    _meta_invalid = (
        not isinstance(meta_uncertainty, (int, float))
        or not (0.0 <= float(meta_uncertainty) <= 1.0)
    )

    # GOV-05: regime must be a GlobalRegimeState instance
    _regime_invalid = not isinstance(current_regime, GlobalRegimeState)

    if _meta_invalid or _regime_invalid:
        # Build a minimal result via validate_pipeline_config using safe
        # stand-in values for parameters owned by downstream modules.
        _safe_capital = total_capital if (
            isinstance(total_capital, (int, float)) and float(total_capital) > 0
        ) else 1.0
        _safe_regime = current_regime if isinstance(
            current_regime, GlobalRegimeState
        ) else GlobalRegimeState.UNKNOWN
        _safe_meta = meta_uncertainty if (
            isinstance(meta_uncertainty, (int, float))
            and 0.0 <= float(meta_uncertainty) <= 1.0
        ) else 0.5

        _gov_result = validate_pipeline_config(
            meta_uncertainty=_safe_meta if not _meta_invalid else meta_uncertainty,
            initial_capital=_safe_capital,
            window=20,
            step=1,
            regime=_safe_regime,
            periods_per_year=252,
        )
        # Only raise for the rules we gate on
        _gated_rules = {"GOV-01", "GOV-05"}
        _gated = [v for v in _gov_result.blocking_violations if v.rule_id in _gated_rules]
        # Also run with the actual bad value so the error message is accurate
        _real_result = validate_pipeline_config(
            meta_uncertainty=meta_uncertainty if isinstance(meta_uncertainty, (int, float)) else 999,
            initial_capital=_safe_capital,
            window=20,
            step=1,
            regime=current_regime,
            periods_per_year=252,
        )
        _real_gated = [v for v in _real_result.blocking_violations if v.rule_id in _gated_rules]
        if _real_gated:
            raise GovernanceViolationError(_real_result)

    # ------------------------------------------------------------------
    # Step 1: Instantiate all components fresh per call
    # ------------------------------------------------------------------
    engine: RiskEngine = RiskEngine()
    regime_detector: RegimeDetector = RegimeDetector()
    vol_tracker: VolatilityTracker = VolatilityTracker()
    state_estimator: StateEstimator = StateEstimator()

    # ------------------------------------------------------------------
    # Steps 2-7: State pipeline
    # ------------------------------------------------------------------
    if len(returns_history) > 0:
        features: dict = _extract_regime_features(returns_history)
        regime_result = regime_detector.detect_regime(features)
        vol_result = vol_tracker.estimate_volatility(returns_history)
        previous_state: LatentState = LatentState.default()
        predicted_state: LatentState = state_estimator.predict(previous_state)
        observation: dict = _build_observation_vector(None, vol_result)
        _latent_state: LatentState = state_estimator.update(predicted_state, observation)

    # ------------------------------------------------------------------
    # Step 8: Risk assessment
    # ------------------------------------------------------------------
    risk_output = engine.assess(
        returns_history=returns_history,
        current_regime=current_regime,
        meta_uncertainty=meta_uncertainty,
    )

    # ------------------------------------------------------------------
    # Steps 9-11: Exposure -> positions -> return
    # ------------------------------------------------------------------
    exposure_weight: float = risk_output.exposure_weight
    positions: dict = route_exposure_to_positions(
        total_capital=total_capital,
        exposure_fraction=exposure_weight,
        asset_prices=asset_prices,
    )
    return positions


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def x_run_full_pipeline__mutmut_89(
    returns_history: list,
    current_regime: GlobalRegimeState,
    meta_uncertainty: float,
    total_capital: float,
    asset_prices: dict,
) -> dict:
    """
    Full deterministic pipeline from returns history to final positions.

    Step 0: Governance gate (GOV-01 + GOV-05 only).
    Steps 1-11: Unchanged from v1.1.0.

    Raises
    ------
    GovernanceViolationError
        meta_uncertainty out of [0.0, 1.0] or regime not GlobalRegimeState.
    ValueError
        Propagated from RiskEngine (invalid returns_history).
        Propagated from route_exposure_to_positions (invalid capital/prices).
    """
    # ------------------------------------------------------------------
    # Step 0: Governance Gate -- GOV-01 and GOV-05 only
    # ------------------------------------------------------------------

    # GOV-01: meta_uncertainty must be in [0.0, 1.0]
    _meta_invalid = (
        not isinstance(meta_uncertainty, (int, float))
        or not (0.0 <= float(meta_uncertainty) <= 1.0)
    )

    # GOV-05: regime must be a GlobalRegimeState instance
    _regime_invalid = not isinstance(current_regime, GlobalRegimeState)

    if _meta_invalid or _regime_invalid:
        # Build a minimal result via validate_pipeline_config using safe
        # stand-in values for parameters owned by downstream modules.
        _safe_capital = total_capital if (
            isinstance(total_capital, (int, float)) and float(total_capital) > 0
        ) else 1.0
        _safe_regime = current_regime if isinstance(
            current_regime, GlobalRegimeState
        ) else GlobalRegimeState.UNKNOWN
        _safe_meta = meta_uncertainty if (
            isinstance(meta_uncertainty, (int, float))
            and 0.0 <= float(meta_uncertainty) <= 1.0
        ) else 0.5

        _gov_result = validate_pipeline_config(
            meta_uncertainty=_safe_meta if not _meta_invalid else meta_uncertainty,
            initial_capital=_safe_capital,
            window=20,
            step=1,
            regime=_safe_regime,
            periods_per_year=252,
        )
        # Only raise for the rules we gate on
        _gated_rules = {"GOV-01", "GOV-05"}
        _gated = [v for v in _gov_result.blocking_violations if v.rule_id in _gated_rules]
        # Also run with the actual bad value so the error message is accurate
        _real_result = validate_pipeline_config(
            meta_uncertainty=meta_uncertainty if isinstance(meta_uncertainty, (int, float)) else 999,
            initial_capital=_safe_capital,
            window=20,
            step=1,
            regime=current_regime,
            periods_per_year=252,
        )
        _real_gated = [v for v in _real_result.blocking_violations if v.rule_id in _gated_rules]
        if _real_gated:
            raise GovernanceViolationError(_real_result)

    # ------------------------------------------------------------------
    # Step 1: Instantiate all components fresh per call
    # ------------------------------------------------------------------
    engine: RiskEngine = RiskEngine()
    regime_detector: RegimeDetector = RegimeDetector()
    vol_tracker: VolatilityTracker = VolatilityTracker()
    state_estimator: StateEstimator = StateEstimator()

    # ------------------------------------------------------------------
    # Steps 2-7: State pipeline
    # ------------------------------------------------------------------
    if len(returns_history) > 0:
        features: dict = _extract_regime_features(returns_history)
        regime_result = regime_detector.detect_regime(features)
        vol_result = vol_tracker.estimate_volatility(returns_history)
        previous_state: LatentState = LatentState.default()
        predicted_state: LatentState = state_estimator.predict(previous_state)
        observation: dict = _build_observation_vector(regime_result, None)
        _latent_state: LatentState = state_estimator.update(predicted_state, observation)

    # ------------------------------------------------------------------
    # Step 8: Risk assessment
    # ------------------------------------------------------------------
    risk_output = engine.assess(
        returns_history=returns_history,
        current_regime=current_regime,
        meta_uncertainty=meta_uncertainty,
    )

    # ------------------------------------------------------------------
    # Steps 9-11: Exposure -> positions -> return
    # ------------------------------------------------------------------
    exposure_weight: float = risk_output.exposure_weight
    positions: dict = route_exposure_to_positions(
        total_capital=total_capital,
        exposure_fraction=exposure_weight,
        asset_prices=asset_prices,
    )
    return positions


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def x_run_full_pipeline__mutmut_90(
    returns_history: list,
    current_regime: GlobalRegimeState,
    meta_uncertainty: float,
    total_capital: float,
    asset_prices: dict,
) -> dict:
    """
    Full deterministic pipeline from returns history to final positions.

    Step 0: Governance gate (GOV-01 + GOV-05 only).
    Steps 1-11: Unchanged from v1.1.0.

    Raises
    ------
    GovernanceViolationError
        meta_uncertainty out of [0.0, 1.0] or regime not GlobalRegimeState.
    ValueError
        Propagated from RiskEngine (invalid returns_history).
        Propagated from route_exposure_to_positions (invalid capital/prices).
    """
    # ------------------------------------------------------------------
    # Step 0: Governance Gate -- GOV-01 and GOV-05 only
    # ------------------------------------------------------------------

    # GOV-01: meta_uncertainty must be in [0.0, 1.0]
    _meta_invalid = (
        not isinstance(meta_uncertainty, (int, float))
        or not (0.0 <= float(meta_uncertainty) <= 1.0)
    )

    # GOV-05: regime must be a GlobalRegimeState instance
    _regime_invalid = not isinstance(current_regime, GlobalRegimeState)

    if _meta_invalid or _regime_invalid:
        # Build a minimal result via validate_pipeline_config using safe
        # stand-in values for parameters owned by downstream modules.
        _safe_capital = total_capital if (
            isinstance(total_capital, (int, float)) and float(total_capital) > 0
        ) else 1.0
        _safe_regime = current_regime if isinstance(
            current_regime, GlobalRegimeState
        ) else GlobalRegimeState.UNKNOWN
        _safe_meta = meta_uncertainty if (
            isinstance(meta_uncertainty, (int, float))
            and 0.0 <= float(meta_uncertainty) <= 1.0
        ) else 0.5

        _gov_result = validate_pipeline_config(
            meta_uncertainty=_safe_meta if not _meta_invalid else meta_uncertainty,
            initial_capital=_safe_capital,
            window=20,
            step=1,
            regime=_safe_regime,
            periods_per_year=252,
        )
        # Only raise for the rules we gate on
        _gated_rules = {"GOV-01", "GOV-05"}
        _gated = [v for v in _gov_result.blocking_violations if v.rule_id in _gated_rules]
        # Also run with the actual bad value so the error message is accurate
        _real_result = validate_pipeline_config(
            meta_uncertainty=meta_uncertainty if isinstance(meta_uncertainty, (int, float)) else 999,
            initial_capital=_safe_capital,
            window=20,
            step=1,
            regime=current_regime,
            periods_per_year=252,
        )
        _real_gated = [v for v in _real_result.blocking_violations if v.rule_id in _gated_rules]
        if _real_gated:
            raise GovernanceViolationError(_real_result)

    # ------------------------------------------------------------------
    # Step 1: Instantiate all components fresh per call
    # ------------------------------------------------------------------
    engine: RiskEngine = RiskEngine()
    regime_detector: RegimeDetector = RegimeDetector()
    vol_tracker: VolatilityTracker = VolatilityTracker()
    state_estimator: StateEstimator = StateEstimator()

    # ------------------------------------------------------------------
    # Steps 2-7: State pipeline
    # ------------------------------------------------------------------
    if len(returns_history) > 0:
        features: dict = _extract_regime_features(returns_history)
        regime_result = regime_detector.detect_regime(features)
        vol_result = vol_tracker.estimate_volatility(returns_history)
        previous_state: LatentState = LatentState.default()
        predicted_state: LatentState = state_estimator.predict(previous_state)
        observation: dict = _build_observation_vector(vol_result)
        _latent_state: LatentState = state_estimator.update(predicted_state, observation)

    # ------------------------------------------------------------------
    # Step 8: Risk assessment
    # ------------------------------------------------------------------
    risk_output = engine.assess(
        returns_history=returns_history,
        current_regime=current_regime,
        meta_uncertainty=meta_uncertainty,
    )

    # ------------------------------------------------------------------
    # Steps 9-11: Exposure -> positions -> return
    # ------------------------------------------------------------------
    exposure_weight: float = risk_output.exposure_weight
    positions: dict = route_exposure_to_positions(
        total_capital=total_capital,
        exposure_fraction=exposure_weight,
        asset_prices=asset_prices,
    )
    return positions


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def x_run_full_pipeline__mutmut_91(
    returns_history: list,
    current_regime: GlobalRegimeState,
    meta_uncertainty: float,
    total_capital: float,
    asset_prices: dict,
) -> dict:
    """
    Full deterministic pipeline from returns history to final positions.

    Step 0: Governance gate (GOV-01 + GOV-05 only).
    Steps 1-11: Unchanged from v1.1.0.

    Raises
    ------
    GovernanceViolationError
        meta_uncertainty out of [0.0, 1.0] or regime not GlobalRegimeState.
    ValueError
        Propagated from RiskEngine (invalid returns_history).
        Propagated from route_exposure_to_positions (invalid capital/prices).
    """
    # ------------------------------------------------------------------
    # Step 0: Governance Gate -- GOV-01 and GOV-05 only
    # ------------------------------------------------------------------

    # GOV-01: meta_uncertainty must be in [0.0, 1.0]
    _meta_invalid = (
        not isinstance(meta_uncertainty, (int, float))
        or not (0.0 <= float(meta_uncertainty) <= 1.0)
    )

    # GOV-05: regime must be a GlobalRegimeState instance
    _regime_invalid = not isinstance(current_regime, GlobalRegimeState)

    if _meta_invalid or _regime_invalid:
        # Build a minimal result via validate_pipeline_config using safe
        # stand-in values for parameters owned by downstream modules.
        _safe_capital = total_capital if (
            isinstance(total_capital, (int, float)) and float(total_capital) > 0
        ) else 1.0
        _safe_regime = current_regime if isinstance(
            current_regime, GlobalRegimeState
        ) else GlobalRegimeState.UNKNOWN
        _safe_meta = meta_uncertainty if (
            isinstance(meta_uncertainty, (int, float))
            and 0.0 <= float(meta_uncertainty) <= 1.0
        ) else 0.5

        _gov_result = validate_pipeline_config(
            meta_uncertainty=_safe_meta if not _meta_invalid else meta_uncertainty,
            initial_capital=_safe_capital,
            window=20,
            step=1,
            regime=_safe_regime,
            periods_per_year=252,
        )
        # Only raise for the rules we gate on
        _gated_rules = {"GOV-01", "GOV-05"}
        _gated = [v for v in _gov_result.blocking_violations if v.rule_id in _gated_rules]
        # Also run with the actual bad value so the error message is accurate
        _real_result = validate_pipeline_config(
            meta_uncertainty=meta_uncertainty if isinstance(meta_uncertainty, (int, float)) else 999,
            initial_capital=_safe_capital,
            window=20,
            step=1,
            regime=current_regime,
            periods_per_year=252,
        )
        _real_gated = [v for v in _real_result.blocking_violations if v.rule_id in _gated_rules]
        if _real_gated:
            raise GovernanceViolationError(_real_result)

    # ------------------------------------------------------------------
    # Step 1: Instantiate all components fresh per call
    # ------------------------------------------------------------------
    engine: RiskEngine = RiskEngine()
    regime_detector: RegimeDetector = RegimeDetector()
    vol_tracker: VolatilityTracker = VolatilityTracker()
    state_estimator: StateEstimator = StateEstimator()

    # ------------------------------------------------------------------
    # Steps 2-7: State pipeline
    # ------------------------------------------------------------------
    if len(returns_history) > 0:
        features: dict = _extract_regime_features(returns_history)
        regime_result = regime_detector.detect_regime(features)
        vol_result = vol_tracker.estimate_volatility(returns_history)
        previous_state: LatentState = LatentState.default()
        predicted_state: LatentState = state_estimator.predict(previous_state)
        observation: dict = _build_observation_vector(regime_result, )
        _latent_state: LatentState = state_estimator.update(predicted_state, observation)

    # ------------------------------------------------------------------
    # Step 8: Risk assessment
    # ------------------------------------------------------------------
    risk_output = engine.assess(
        returns_history=returns_history,
        current_regime=current_regime,
        meta_uncertainty=meta_uncertainty,
    )

    # ------------------------------------------------------------------
    # Steps 9-11: Exposure -> positions -> return
    # ------------------------------------------------------------------
    exposure_weight: float = risk_output.exposure_weight
    positions: dict = route_exposure_to_positions(
        total_capital=total_capital,
        exposure_fraction=exposure_weight,
        asset_prices=asset_prices,
    )
    return positions


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def x_run_full_pipeline__mutmut_92(
    returns_history: list,
    current_regime: GlobalRegimeState,
    meta_uncertainty: float,
    total_capital: float,
    asset_prices: dict,
) -> dict:
    """
    Full deterministic pipeline from returns history to final positions.

    Step 0: Governance gate (GOV-01 + GOV-05 only).
    Steps 1-11: Unchanged from v1.1.0.

    Raises
    ------
    GovernanceViolationError
        meta_uncertainty out of [0.0, 1.0] or regime not GlobalRegimeState.
    ValueError
        Propagated from RiskEngine (invalid returns_history).
        Propagated from route_exposure_to_positions (invalid capital/prices).
    """
    # ------------------------------------------------------------------
    # Step 0: Governance Gate -- GOV-01 and GOV-05 only
    # ------------------------------------------------------------------

    # GOV-01: meta_uncertainty must be in [0.0, 1.0]
    _meta_invalid = (
        not isinstance(meta_uncertainty, (int, float))
        or not (0.0 <= float(meta_uncertainty) <= 1.0)
    )

    # GOV-05: regime must be a GlobalRegimeState instance
    _regime_invalid = not isinstance(current_regime, GlobalRegimeState)

    if _meta_invalid or _regime_invalid:
        # Build a minimal result via validate_pipeline_config using safe
        # stand-in values for parameters owned by downstream modules.
        _safe_capital = total_capital if (
            isinstance(total_capital, (int, float)) and float(total_capital) > 0
        ) else 1.0
        _safe_regime = current_regime if isinstance(
            current_regime, GlobalRegimeState
        ) else GlobalRegimeState.UNKNOWN
        _safe_meta = meta_uncertainty if (
            isinstance(meta_uncertainty, (int, float))
            and 0.0 <= float(meta_uncertainty) <= 1.0
        ) else 0.5

        _gov_result = validate_pipeline_config(
            meta_uncertainty=_safe_meta if not _meta_invalid else meta_uncertainty,
            initial_capital=_safe_capital,
            window=20,
            step=1,
            regime=_safe_regime,
            periods_per_year=252,
        )
        # Only raise for the rules we gate on
        _gated_rules = {"GOV-01", "GOV-05"}
        _gated = [v for v in _gov_result.blocking_violations if v.rule_id in _gated_rules]
        # Also run with the actual bad value so the error message is accurate
        _real_result = validate_pipeline_config(
            meta_uncertainty=meta_uncertainty if isinstance(meta_uncertainty, (int, float)) else 999,
            initial_capital=_safe_capital,
            window=20,
            step=1,
            regime=current_regime,
            periods_per_year=252,
        )
        _real_gated = [v for v in _real_result.blocking_violations if v.rule_id in _gated_rules]
        if _real_gated:
            raise GovernanceViolationError(_real_result)

    # ------------------------------------------------------------------
    # Step 1: Instantiate all components fresh per call
    # ------------------------------------------------------------------
    engine: RiskEngine = RiskEngine()
    regime_detector: RegimeDetector = RegimeDetector()
    vol_tracker: VolatilityTracker = VolatilityTracker()
    state_estimator: StateEstimator = StateEstimator()

    # ------------------------------------------------------------------
    # Steps 2-7: State pipeline
    # ------------------------------------------------------------------
    if len(returns_history) > 0:
        features: dict = _extract_regime_features(returns_history)
        regime_result = regime_detector.detect_regime(features)
        vol_result = vol_tracker.estimate_volatility(returns_history)
        previous_state: LatentState = LatentState.default()
        predicted_state: LatentState = state_estimator.predict(previous_state)
        observation: dict = _build_observation_vector(regime_result, vol_result)
        _latent_state: LatentState = None

    # ------------------------------------------------------------------
    # Step 8: Risk assessment
    # ------------------------------------------------------------------
    risk_output = engine.assess(
        returns_history=returns_history,
        current_regime=current_regime,
        meta_uncertainty=meta_uncertainty,
    )

    # ------------------------------------------------------------------
    # Steps 9-11: Exposure -> positions -> return
    # ------------------------------------------------------------------
    exposure_weight: float = risk_output.exposure_weight
    positions: dict = route_exposure_to_positions(
        total_capital=total_capital,
        exposure_fraction=exposure_weight,
        asset_prices=asset_prices,
    )
    return positions


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def x_run_full_pipeline__mutmut_93(
    returns_history: list,
    current_regime: GlobalRegimeState,
    meta_uncertainty: float,
    total_capital: float,
    asset_prices: dict,
) -> dict:
    """
    Full deterministic pipeline from returns history to final positions.

    Step 0: Governance gate (GOV-01 + GOV-05 only).
    Steps 1-11: Unchanged from v1.1.0.

    Raises
    ------
    GovernanceViolationError
        meta_uncertainty out of [0.0, 1.0] or regime not GlobalRegimeState.
    ValueError
        Propagated from RiskEngine (invalid returns_history).
        Propagated from route_exposure_to_positions (invalid capital/prices).
    """
    # ------------------------------------------------------------------
    # Step 0: Governance Gate -- GOV-01 and GOV-05 only
    # ------------------------------------------------------------------

    # GOV-01: meta_uncertainty must be in [0.0, 1.0]
    _meta_invalid = (
        not isinstance(meta_uncertainty, (int, float))
        or not (0.0 <= float(meta_uncertainty) <= 1.0)
    )

    # GOV-05: regime must be a GlobalRegimeState instance
    _regime_invalid = not isinstance(current_regime, GlobalRegimeState)

    if _meta_invalid or _regime_invalid:
        # Build a minimal result via validate_pipeline_config using safe
        # stand-in values for parameters owned by downstream modules.
        _safe_capital = total_capital if (
            isinstance(total_capital, (int, float)) and float(total_capital) > 0
        ) else 1.0
        _safe_regime = current_regime if isinstance(
            current_regime, GlobalRegimeState
        ) else GlobalRegimeState.UNKNOWN
        _safe_meta = meta_uncertainty if (
            isinstance(meta_uncertainty, (int, float))
            and 0.0 <= float(meta_uncertainty) <= 1.0
        ) else 0.5

        _gov_result = validate_pipeline_config(
            meta_uncertainty=_safe_meta if not _meta_invalid else meta_uncertainty,
            initial_capital=_safe_capital,
            window=20,
            step=1,
            regime=_safe_regime,
            periods_per_year=252,
        )
        # Only raise for the rules we gate on
        _gated_rules = {"GOV-01", "GOV-05"}
        _gated = [v for v in _gov_result.blocking_violations if v.rule_id in _gated_rules]
        # Also run with the actual bad value so the error message is accurate
        _real_result = validate_pipeline_config(
            meta_uncertainty=meta_uncertainty if isinstance(meta_uncertainty, (int, float)) else 999,
            initial_capital=_safe_capital,
            window=20,
            step=1,
            regime=current_regime,
            periods_per_year=252,
        )
        _real_gated = [v for v in _real_result.blocking_violations if v.rule_id in _gated_rules]
        if _real_gated:
            raise GovernanceViolationError(_real_result)

    # ------------------------------------------------------------------
    # Step 1: Instantiate all components fresh per call
    # ------------------------------------------------------------------
    engine: RiskEngine = RiskEngine()
    regime_detector: RegimeDetector = RegimeDetector()
    vol_tracker: VolatilityTracker = VolatilityTracker()
    state_estimator: StateEstimator = StateEstimator()

    # ------------------------------------------------------------------
    # Steps 2-7: State pipeline
    # ------------------------------------------------------------------
    if len(returns_history) > 0:
        features: dict = _extract_regime_features(returns_history)
        regime_result = regime_detector.detect_regime(features)
        vol_result = vol_tracker.estimate_volatility(returns_history)
        previous_state: LatentState = LatentState.default()
        predicted_state: LatentState = state_estimator.predict(previous_state)
        observation: dict = _build_observation_vector(regime_result, vol_result)
        _latent_state: LatentState = state_estimator.update(None, observation)

    # ------------------------------------------------------------------
    # Step 8: Risk assessment
    # ------------------------------------------------------------------
    risk_output = engine.assess(
        returns_history=returns_history,
        current_regime=current_regime,
        meta_uncertainty=meta_uncertainty,
    )

    # ------------------------------------------------------------------
    # Steps 9-11: Exposure -> positions -> return
    # ------------------------------------------------------------------
    exposure_weight: float = risk_output.exposure_weight
    positions: dict = route_exposure_to_positions(
        total_capital=total_capital,
        exposure_fraction=exposure_weight,
        asset_prices=asset_prices,
    )
    return positions


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def x_run_full_pipeline__mutmut_94(
    returns_history: list,
    current_regime: GlobalRegimeState,
    meta_uncertainty: float,
    total_capital: float,
    asset_prices: dict,
) -> dict:
    """
    Full deterministic pipeline from returns history to final positions.

    Step 0: Governance gate (GOV-01 + GOV-05 only).
    Steps 1-11: Unchanged from v1.1.0.

    Raises
    ------
    GovernanceViolationError
        meta_uncertainty out of [0.0, 1.0] or regime not GlobalRegimeState.
    ValueError
        Propagated from RiskEngine (invalid returns_history).
        Propagated from route_exposure_to_positions (invalid capital/prices).
    """
    # ------------------------------------------------------------------
    # Step 0: Governance Gate -- GOV-01 and GOV-05 only
    # ------------------------------------------------------------------

    # GOV-01: meta_uncertainty must be in [0.0, 1.0]
    _meta_invalid = (
        not isinstance(meta_uncertainty, (int, float))
        or not (0.0 <= float(meta_uncertainty) <= 1.0)
    )

    # GOV-05: regime must be a GlobalRegimeState instance
    _regime_invalid = not isinstance(current_regime, GlobalRegimeState)

    if _meta_invalid or _regime_invalid:
        # Build a minimal result via validate_pipeline_config using safe
        # stand-in values for parameters owned by downstream modules.
        _safe_capital = total_capital if (
            isinstance(total_capital, (int, float)) and float(total_capital) > 0
        ) else 1.0
        _safe_regime = current_regime if isinstance(
            current_regime, GlobalRegimeState
        ) else GlobalRegimeState.UNKNOWN
        _safe_meta = meta_uncertainty if (
            isinstance(meta_uncertainty, (int, float))
            and 0.0 <= float(meta_uncertainty) <= 1.0
        ) else 0.5

        _gov_result = validate_pipeline_config(
            meta_uncertainty=_safe_meta if not _meta_invalid else meta_uncertainty,
            initial_capital=_safe_capital,
            window=20,
            step=1,
            regime=_safe_regime,
            periods_per_year=252,
        )
        # Only raise for the rules we gate on
        _gated_rules = {"GOV-01", "GOV-05"}
        _gated = [v for v in _gov_result.blocking_violations if v.rule_id in _gated_rules]
        # Also run with the actual bad value so the error message is accurate
        _real_result = validate_pipeline_config(
            meta_uncertainty=meta_uncertainty if isinstance(meta_uncertainty, (int, float)) else 999,
            initial_capital=_safe_capital,
            window=20,
            step=1,
            regime=current_regime,
            periods_per_year=252,
        )
        _real_gated = [v for v in _real_result.blocking_violations if v.rule_id in _gated_rules]
        if _real_gated:
            raise GovernanceViolationError(_real_result)

    # ------------------------------------------------------------------
    # Step 1: Instantiate all components fresh per call
    # ------------------------------------------------------------------
    engine: RiskEngine = RiskEngine()
    regime_detector: RegimeDetector = RegimeDetector()
    vol_tracker: VolatilityTracker = VolatilityTracker()
    state_estimator: StateEstimator = StateEstimator()

    # ------------------------------------------------------------------
    # Steps 2-7: State pipeline
    # ------------------------------------------------------------------
    if len(returns_history) > 0:
        features: dict = _extract_regime_features(returns_history)
        regime_result = regime_detector.detect_regime(features)
        vol_result = vol_tracker.estimate_volatility(returns_history)
        previous_state: LatentState = LatentState.default()
        predicted_state: LatentState = state_estimator.predict(previous_state)
        observation: dict = _build_observation_vector(regime_result, vol_result)
        _latent_state: LatentState = state_estimator.update(predicted_state, None)

    # ------------------------------------------------------------------
    # Step 8: Risk assessment
    # ------------------------------------------------------------------
    risk_output = engine.assess(
        returns_history=returns_history,
        current_regime=current_regime,
        meta_uncertainty=meta_uncertainty,
    )

    # ------------------------------------------------------------------
    # Steps 9-11: Exposure -> positions -> return
    # ------------------------------------------------------------------
    exposure_weight: float = risk_output.exposure_weight
    positions: dict = route_exposure_to_positions(
        total_capital=total_capital,
        exposure_fraction=exposure_weight,
        asset_prices=asset_prices,
    )
    return positions


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def x_run_full_pipeline__mutmut_95(
    returns_history: list,
    current_regime: GlobalRegimeState,
    meta_uncertainty: float,
    total_capital: float,
    asset_prices: dict,
) -> dict:
    """
    Full deterministic pipeline from returns history to final positions.

    Step 0: Governance gate (GOV-01 + GOV-05 only).
    Steps 1-11: Unchanged from v1.1.0.

    Raises
    ------
    GovernanceViolationError
        meta_uncertainty out of [0.0, 1.0] or regime not GlobalRegimeState.
    ValueError
        Propagated from RiskEngine (invalid returns_history).
        Propagated from route_exposure_to_positions (invalid capital/prices).
    """
    # ------------------------------------------------------------------
    # Step 0: Governance Gate -- GOV-01 and GOV-05 only
    # ------------------------------------------------------------------

    # GOV-01: meta_uncertainty must be in [0.0, 1.0]
    _meta_invalid = (
        not isinstance(meta_uncertainty, (int, float))
        or not (0.0 <= float(meta_uncertainty) <= 1.0)
    )

    # GOV-05: regime must be a GlobalRegimeState instance
    _regime_invalid = not isinstance(current_regime, GlobalRegimeState)

    if _meta_invalid or _regime_invalid:
        # Build a minimal result via validate_pipeline_config using safe
        # stand-in values for parameters owned by downstream modules.
        _safe_capital = total_capital if (
            isinstance(total_capital, (int, float)) and float(total_capital) > 0
        ) else 1.0
        _safe_regime = current_regime if isinstance(
            current_regime, GlobalRegimeState
        ) else GlobalRegimeState.UNKNOWN
        _safe_meta = meta_uncertainty if (
            isinstance(meta_uncertainty, (int, float))
            and 0.0 <= float(meta_uncertainty) <= 1.0
        ) else 0.5

        _gov_result = validate_pipeline_config(
            meta_uncertainty=_safe_meta if not _meta_invalid else meta_uncertainty,
            initial_capital=_safe_capital,
            window=20,
            step=1,
            regime=_safe_regime,
            periods_per_year=252,
        )
        # Only raise for the rules we gate on
        _gated_rules = {"GOV-01", "GOV-05"}
        _gated = [v for v in _gov_result.blocking_violations if v.rule_id in _gated_rules]
        # Also run with the actual bad value so the error message is accurate
        _real_result = validate_pipeline_config(
            meta_uncertainty=meta_uncertainty if isinstance(meta_uncertainty, (int, float)) else 999,
            initial_capital=_safe_capital,
            window=20,
            step=1,
            regime=current_regime,
            periods_per_year=252,
        )
        _real_gated = [v for v in _real_result.blocking_violations if v.rule_id in _gated_rules]
        if _real_gated:
            raise GovernanceViolationError(_real_result)

    # ------------------------------------------------------------------
    # Step 1: Instantiate all components fresh per call
    # ------------------------------------------------------------------
    engine: RiskEngine = RiskEngine()
    regime_detector: RegimeDetector = RegimeDetector()
    vol_tracker: VolatilityTracker = VolatilityTracker()
    state_estimator: StateEstimator = StateEstimator()

    # ------------------------------------------------------------------
    # Steps 2-7: State pipeline
    # ------------------------------------------------------------------
    if len(returns_history) > 0:
        features: dict = _extract_regime_features(returns_history)
        regime_result = regime_detector.detect_regime(features)
        vol_result = vol_tracker.estimate_volatility(returns_history)
        previous_state: LatentState = LatentState.default()
        predicted_state: LatentState = state_estimator.predict(previous_state)
        observation: dict = _build_observation_vector(regime_result, vol_result)
        _latent_state: LatentState = state_estimator.update(observation)

    # ------------------------------------------------------------------
    # Step 8: Risk assessment
    # ------------------------------------------------------------------
    risk_output = engine.assess(
        returns_history=returns_history,
        current_regime=current_regime,
        meta_uncertainty=meta_uncertainty,
    )

    # ------------------------------------------------------------------
    # Steps 9-11: Exposure -> positions -> return
    # ------------------------------------------------------------------
    exposure_weight: float = risk_output.exposure_weight
    positions: dict = route_exposure_to_positions(
        total_capital=total_capital,
        exposure_fraction=exposure_weight,
        asset_prices=asset_prices,
    )
    return positions


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def x_run_full_pipeline__mutmut_96(
    returns_history: list,
    current_regime: GlobalRegimeState,
    meta_uncertainty: float,
    total_capital: float,
    asset_prices: dict,
) -> dict:
    """
    Full deterministic pipeline from returns history to final positions.

    Step 0: Governance gate (GOV-01 + GOV-05 only).
    Steps 1-11: Unchanged from v1.1.0.

    Raises
    ------
    GovernanceViolationError
        meta_uncertainty out of [0.0, 1.0] or regime not GlobalRegimeState.
    ValueError
        Propagated from RiskEngine (invalid returns_history).
        Propagated from route_exposure_to_positions (invalid capital/prices).
    """
    # ------------------------------------------------------------------
    # Step 0: Governance Gate -- GOV-01 and GOV-05 only
    # ------------------------------------------------------------------

    # GOV-01: meta_uncertainty must be in [0.0, 1.0]
    _meta_invalid = (
        not isinstance(meta_uncertainty, (int, float))
        or not (0.0 <= float(meta_uncertainty) <= 1.0)
    )

    # GOV-05: regime must be a GlobalRegimeState instance
    _regime_invalid = not isinstance(current_regime, GlobalRegimeState)

    if _meta_invalid or _regime_invalid:
        # Build a minimal result via validate_pipeline_config using safe
        # stand-in values for parameters owned by downstream modules.
        _safe_capital = total_capital if (
            isinstance(total_capital, (int, float)) and float(total_capital) > 0
        ) else 1.0
        _safe_regime = current_regime if isinstance(
            current_regime, GlobalRegimeState
        ) else GlobalRegimeState.UNKNOWN
        _safe_meta = meta_uncertainty if (
            isinstance(meta_uncertainty, (int, float))
            and 0.0 <= float(meta_uncertainty) <= 1.0
        ) else 0.5

        _gov_result = validate_pipeline_config(
            meta_uncertainty=_safe_meta if not _meta_invalid else meta_uncertainty,
            initial_capital=_safe_capital,
            window=20,
            step=1,
            regime=_safe_regime,
            periods_per_year=252,
        )
        # Only raise for the rules we gate on
        _gated_rules = {"GOV-01", "GOV-05"}
        _gated = [v for v in _gov_result.blocking_violations if v.rule_id in _gated_rules]
        # Also run with the actual bad value so the error message is accurate
        _real_result = validate_pipeline_config(
            meta_uncertainty=meta_uncertainty if isinstance(meta_uncertainty, (int, float)) else 999,
            initial_capital=_safe_capital,
            window=20,
            step=1,
            regime=current_regime,
            periods_per_year=252,
        )
        _real_gated = [v for v in _real_result.blocking_violations if v.rule_id in _gated_rules]
        if _real_gated:
            raise GovernanceViolationError(_real_result)

    # ------------------------------------------------------------------
    # Step 1: Instantiate all components fresh per call
    # ------------------------------------------------------------------
    engine: RiskEngine = RiskEngine()
    regime_detector: RegimeDetector = RegimeDetector()
    vol_tracker: VolatilityTracker = VolatilityTracker()
    state_estimator: StateEstimator = StateEstimator()

    # ------------------------------------------------------------------
    # Steps 2-7: State pipeline
    # ------------------------------------------------------------------
    if len(returns_history) > 0:
        features: dict = _extract_regime_features(returns_history)
        regime_result = regime_detector.detect_regime(features)
        vol_result = vol_tracker.estimate_volatility(returns_history)
        previous_state: LatentState = LatentState.default()
        predicted_state: LatentState = state_estimator.predict(previous_state)
        observation: dict = _build_observation_vector(regime_result, vol_result)
        _latent_state: LatentState = state_estimator.update(predicted_state, )

    # ------------------------------------------------------------------
    # Step 8: Risk assessment
    # ------------------------------------------------------------------
    risk_output = engine.assess(
        returns_history=returns_history,
        current_regime=current_regime,
        meta_uncertainty=meta_uncertainty,
    )

    # ------------------------------------------------------------------
    # Steps 9-11: Exposure -> positions -> return
    # ------------------------------------------------------------------
    exposure_weight: float = risk_output.exposure_weight
    positions: dict = route_exposure_to_positions(
        total_capital=total_capital,
        exposure_fraction=exposure_weight,
        asset_prices=asset_prices,
    )
    return positions


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def x_run_full_pipeline__mutmut_97(
    returns_history: list,
    current_regime: GlobalRegimeState,
    meta_uncertainty: float,
    total_capital: float,
    asset_prices: dict,
) -> dict:
    """
    Full deterministic pipeline from returns history to final positions.

    Step 0: Governance gate (GOV-01 + GOV-05 only).
    Steps 1-11: Unchanged from v1.1.0.

    Raises
    ------
    GovernanceViolationError
        meta_uncertainty out of [0.0, 1.0] or regime not GlobalRegimeState.
    ValueError
        Propagated from RiskEngine (invalid returns_history).
        Propagated from route_exposure_to_positions (invalid capital/prices).
    """
    # ------------------------------------------------------------------
    # Step 0: Governance Gate -- GOV-01 and GOV-05 only
    # ------------------------------------------------------------------

    # GOV-01: meta_uncertainty must be in [0.0, 1.0]
    _meta_invalid = (
        not isinstance(meta_uncertainty, (int, float))
        or not (0.0 <= float(meta_uncertainty) <= 1.0)
    )

    # GOV-05: regime must be a GlobalRegimeState instance
    _regime_invalid = not isinstance(current_regime, GlobalRegimeState)

    if _meta_invalid or _regime_invalid:
        # Build a minimal result via validate_pipeline_config using safe
        # stand-in values for parameters owned by downstream modules.
        _safe_capital = total_capital if (
            isinstance(total_capital, (int, float)) and float(total_capital) > 0
        ) else 1.0
        _safe_regime = current_regime if isinstance(
            current_regime, GlobalRegimeState
        ) else GlobalRegimeState.UNKNOWN
        _safe_meta = meta_uncertainty if (
            isinstance(meta_uncertainty, (int, float))
            and 0.0 <= float(meta_uncertainty) <= 1.0
        ) else 0.5

        _gov_result = validate_pipeline_config(
            meta_uncertainty=_safe_meta if not _meta_invalid else meta_uncertainty,
            initial_capital=_safe_capital,
            window=20,
            step=1,
            regime=_safe_regime,
            periods_per_year=252,
        )
        # Only raise for the rules we gate on
        _gated_rules = {"GOV-01", "GOV-05"}
        _gated = [v for v in _gov_result.blocking_violations if v.rule_id in _gated_rules]
        # Also run with the actual bad value so the error message is accurate
        _real_result = validate_pipeline_config(
            meta_uncertainty=meta_uncertainty if isinstance(meta_uncertainty, (int, float)) else 999,
            initial_capital=_safe_capital,
            window=20,
            step=1,
            regime=current_regime,
            periods_per_year=252,
        )
        _real_gated = [v for v in _real_result.blocking_violations if v.rule_id in _gated_rules]
        if _real_gated:
            raise GovernanceViolationError(_real_result)

    # ------------------------------------------------------------------
    # Step 1: Instantiate all components fresh per call
    # ------------------------------------------------------------------
    engine: RiskEngine = RiskEngine()
    regime_detector: RegimeDetector = RegimeDetector()
    vol_tracker: VolatilityTracker = VolatilityTracker()
    state_estimator: StateEstimator = StateEstimator()

    # ------------------------------------------------------------------
    # Steps 2-7: State pipeline
    # ------------------------------------------------------------------
    if len(returns_history) > 0:
        features: dict = _extract_regime_features(returns_history)
        regime_result = regime_detector.detect_regime(features)
        vol_result = vol_tracker.estimate_volatility(returns_history)
        previous_state: LatentState = LatentState.default()
        predicted_state: LatentState = state_estimator.predict(previous_state)
        observation: dict = _build_observation_vector(regime_result, vol_result)
        _latent_state: LatentState = state_estimator.update(predicted_state, observation)

    # ------------------------------------------------------------------
    # Step 8: Risk assessment
    # ------------------------------------------------------------------
    risk_output = None

    # ------------------------------------------------------------------
    # Steps 9-11: Exposure -> positions -> return
    # ------------------------------------------------------------------
    exposure_weight: float = risk_output.exposure_weight
    positions: dict = route_exposure_to_positions(
        total_capital=total_capital,
        exposure_fraction=exposure_weight,
        asset_prices=asset_prices,
    )
    return positions


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def x_run_full_pipeline__mutmut_98(
    returns_history: list,
    current_regime: GlobalRegimeState,
    meta_uncertainty: float,
    total_capital: float,
    asset_prices: dict,
) -> dict:
    """
    Full deterministic pipeline from returns history to final positions.

    Step 0: Governance gate (GOV-01 + GOV-05 only).
    Steps 1-11: Unchanged from v1.1.0.

    Raises
    ------
    GovernanceViolationError
        meta_uncertainty out of [0.0, 1.0] or regime not GlobalRegimeState.
    ValueError
        Propagated from RiskEngine (invalid returns_history).
        Propagated from route_exposure_to_positions (invalid capital/prices).
    """
    # ------------------------------------------------------------------
    # Step 0: Governance Gate -- GOV-01 and GOV-05 only
    # ------------------------------------------------------------------

    # GOV-01: meta_uncertainty must be in [0.0, 1.0]
    _meta_invalid = (
        not isinstance(meta_uncertainty, (int, float))
        or not (0.0 <= float(meta_uncertainty) <= 1.0)
    )

    # GOV-05: regime must be a GlobalRegimeState instance
    _regime_invalid = not isinstance(current_regime, GlobalRegimeState)

    if _meta_invalid or _regime_invalid:
        # Build a minimal result via validate_pipeline_config using safe
        # stand-in values for parameters owned by downstream modules.
        _safe_capital = total_capital if (
            isinstance(total_capital, (int, float)) and float(total_capital) > 0
        ) else 1.0
        _safe_regime = current_regime if isinstance(
            current_regime, GlobalRegimeState
        ) else GlobalRegimeState.UNKNOWN
        _safe_meta = meta_uncertainty if (
            isinstance(meta_uncertainty, (int, float))
            and 0.0 <= float(meta_uncertainty) <= 1.0
        ) else 0.5

        _gov_result = validate_pipeline_config(
            meta_uncertainty=_safe_meta if not _meta_invalid else meta_uncertainty,
            initial_capital=_safe_capital,
            window=20,
            step=1,
            regime=_safe_regime,
            periods_per_year=252,
        )
        # Only raise for the rules we gate on
        _gated_rules = {"GOV-01", "GOV-05"}
        _gated = [v for v in _gov_result.blocking_violations if v.rule_id in _gated_rules]
        # Also run with the actual bad value so the error message is accurate
        _real_result = validate_pipeline_config(
            meta_uncertainty=meta_uncertainty if isinstance(meta_uncertainty, (int, float)) else 999,
            initial_capital=_safe_capital,
            window=20,
            step=1,
            regime=current_regime,
            periods_per_year=252,
        )
        _real_gated = [v for v in _real_result.blocking_violations if v.rule_id in _gated_rules]
        if _real_gated:
            raise GovernanceViolationError(_real_result)

    # ------------------------------------------------------------------
    # Step 1: Instantiate all components fresh per call
    # ------------------------------------------------------------------
    engine: RiskEngine = RiskEngine()
    regime_detector: RegimeDetector = RegimeDetector()
    vol_tracker: VolatilityTracker = VolatilityTracker()
    state_estimator: StateEstimator = StateEstimator()

    # ------------------------------------------------------------------
    # Steps 2-7: State pipeline
    # ------------------------------------------------------------------
    if len(returns_history) > 0:
        features: dict = _extract_regime_features(returns_history)
        regime_result = regime_detector.detect_regime(features)
        vol_result = vol_tracker.estimate_volatility(returns_history)
        previous_state: LatentState = LatentState.default()
        predicted_state: LatentState = state_estimator.predict(previous_state)
        observation: dict = _build_observation_vector(regime_result, vol_result)
        _latent_state: LatentState = state_estimator.update(predicted_state, observation)

    # ------------------------------------------------------------------
    # Step 8: Risk assessment
    # ------------------------------------------------------------------
    risk_output = engine.assess(
        returns_history=None,
        current_regime=current_regime,
        meta_uncertainty=meta_uncertainty,
    )

    # ------------------------------------------------------------------
    # Steps 9-11: Exposure -> positions -> return
    # ------------------------------------------------------------------
    exposure_weight: float = risk_output.exposure_weight
    positions: dict = route_exposure_to_positions(
        total_capital=total_capital,
        exposure_fraction=exposure_weight,
        asset_prices=asset_prices,
    )
    return positions


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def x_run_full_pipeline__mutmut_99(
    returns_history: list,
    current_regime: GlobalRegimeState,
    meta_uncertainty: float,
    total_capital: float,
    asset_prices: dict,
) -> dict:
    """
    Full deterministic pipeline from returns history to final positions.

    Step 0: Governance gate (GOV-01 + GOV-05 only).
    Steps 1-11: Unchanged from v1.1.0.

    Raises
    ------
    GovernanceViolationError
        meta_uncertainty out of [0.0, 1.0] or regime not GlobalRegimeState.
    ValueError
        Propagated from RiskEngine (invalid returns_history).
        Propagated from route_exposure_to_positions (invalid capital/prices).
    """
    # ------------------------------------------------------------------
    # Step 0: Governance Gate -- GOV-01 and GOV-05 only
    # ------------------------------------------------------------------

    # GOV-01: meta_uncertainty must be in [0.0, 1.0]
    _meta_invalid = (
        not isinstance(meta_uncertainty, (int, float))
        or not (0.0 <= float(meta_uncertainty) <= 1.0)
    )

    # GOV-05: regime must be a GlobalRegimeState instance
    _regime_invalid = not isinstance(current_regime, GlobalRegimeState)

    if _meta_invalid or _regime_invalid:
        # Build a minimal result via validate_pipeline_config using safe
        # stand-in values for parameters owned by downstream modules.
        _safe_capital = total_capital if (
            isinstance(total_capital, (int, float)) and float(total_capital) > 0
        ) else 1.0
        _safe_regime = current_regime if isinstance(
            current_regime, GlobalRegimeState
        ) else GlobalRegimeState.UNKNOWN
        _safe_meta = meta_uncertainty if (
            isinstance(meta_uncertainty, (int, float))
            and 0.0 <= float(meta_uncertainty) <= 1.0
        ) else 0.5

        _gov_result = validate_pipeline_config(
            meta_uncertainty=_safe_meta if not _meta_invalid else meta_uncertainty,
            initial_capital=_safe_capital,
            window=20,
            step=1,
            regime=_safe_regime,
            periods_per_year=252,
        )
        # Only raise for the rules we gate on
        _gated_rules = {"GOV-01", "GOV-05"}
        _gated = [v for v in _gov_result.blocking_violations if v.rule_id in _gated_rules]
        # Also run with the actual bad value so the error message is accurate
        _real_result = validate_pipeline_config(
            meta_uncertainty=meta_uncertainty if isinstance(meta_uncertainty, (int, float)) else 999,
            initial_capital=_safe_capital,
            window=20,
            step=1,
            regime=current_regime,
            periods_per_year=252,
        )
        _real_gated = [v for v in _real_result.blocking_violations if v.rule_id in _gated_rules]
        if _real_gated:
            raise GovernanceViolationError(_real_result)

    # ------------------------------------------------------------------
    # Step 1: Instantiate all components fresh per call
    # ------------------------------------------------------------------
    engine: RiskEngine = RiskEngine()
    regime_detector: RegimeDetector = RegimeDetector()
    vol_tracker: VolatilityTracker = VolatilityTracker()
    state_estimator: StateEstimator = StateEstimator()

    # ------------------------------------------------------------------
    # Steps 2-7: State pipeline
    # ------------------------------------------------------------------
    if len(returns_history) > 0:
        features: dict = _extract_regime_features(returns_history)
        regime_result = regime_detector.detect_regime(features)
        vol_result = vol_tracker.estimate_volatility(returns_history)
        previous_state: LatentState = LatentState.default()
        predicted_state: LatentState = state_estimator.predict(previous_state)
        observation: dict = _build_observation_vector(regime_result, vol_result)
        _latent_state: LatentState = state_estimator.update(predicted_state, observation)

    # ------------------------------------------------------------------
    # Step 8: Risk assessment
    # ------------------------------------------------------------------
    risk_output = engine.assess(
        returns_history=returns_history,
        current_regime=None,
        meta_uncertainty=meta_uncertainty,
    )

    # ------------------------------------------------------------------
    # Steps 9-11: Exposure -> positions -> return
    # ------------------------------------------------------------------
    exposure_weight: float = risk_output.exposure_weight
    positions: dict = route_exposure_to_positions(
        total_capital=total_capital,
        exposure_fraction=exposure_weight,
        asset_prices=asset_prices,
    )
    return positions


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def x_run_full_pipeline__mutmut_100(
    returns_history: list,
    current_regime: GlobalRegimeState,
    meta_uncertainty: float,
    total_capital: float,
    asset_prices: dict,
) -> dict:
    """
    Full deterministic pipeline from returns history to final positions.

    Step 0: Governance gate (GOV-01 + GOV-05 only).
    Steps 1-11: Unchanged from v1.1.0.

    Raises
    ------
    GovernanceViolationError
        meta_uncertainty out of [0.0, 1.0] or regime not GlobalRegimeState.
    ValueError
        Propagated from RiskEngine (invalid returns_history).
        Propagated from route_exposure_to_positions (invalid capital/prices).
    """
    # ------------------------------------------------------------------
    # Step 0: Governance Gate -- GOV-01 and GOV-05 only
    # ------------------------------------------------------------------

    # GOV-01: meta_uncertainty must be in [0.0, 1.0]
    _meta_invalid = (
        not isinstance(meta_uncertainty, (int, float))
        or not (0.0 <= float(meta_uncertainty) <= 1.0)
    )

    # GOV-05: regime must be a GlobalRegimeState instance
    _regime_invalid = not isinstance(current_regime, GlobalRegimeState)

    if _meta_invalid or _regime_invalid:
        # Build a minimal result via validate_pipeline_config using safe
        # stand-in values for parameters owned by downstream modules.
        _safe_capital = total_capital if (
            isinstance(total_capital, (int, float)) and float(total_capital) > 0
        ) else 1.0
        _safe_regime = current_regime if isinstance(
            current_regime, GlobalRegimeState
        ) else GlobalRegimeState.UNKNOWN
        _safe_meta = meta_uncertainty if (
            isinstance(meta_uncertainty, (int, float))
            and 0.0 <= float(meta_uncertainty) <= 1.0
        ) else 0.5

        _gov_result = validate_pipeline_config(
            meta_uncertainty=_safe_meta if not _meta_invalid else meta_uncertainty,
            initial_capital=_safe_capital,
            window=20,
            step=1,
            regime=_safe_regime,
            periods_per_year=252,
        )
        # Only raise for the rules we gate on
        _gated_rules = {"GOV-01", "GOV-05"}
        _gated = [v for v in _gov_result.blocking_violations if v.rule_id in _gated_rules]
        # Also run with the actual bad value so the error message is accurate
        _real_result = validate_pipeline_config(
            meta_uncertainty=meta_uncertainty if isinstance(meta_uncertainty, (int, float)) else 999,
            initial_capital=_safe_capital,
            window=20,
            step=1,
            regime=current_regime,
            periods_per_year=252,
        )
        _real_gated = [v for v in _real_result.blocking_violations if v.rule_id in _gated_rules]
        if _real_gated:
            raise GovernanceViolationError(_real_result)

    # ------------------------------------------------------------------
    # Step 1: Instantiate all components fresh per call
    # ------------------------------------------------------------------
    engine: RiskEngine = RiskEngine()
    regime_detector: RegimeDetector = RegimeDetector()
    vol_tracker: VolatilityTracker = VolatilityTracker()
    state_estimator: StateEstimator = StateEstimator()

    # ------------------------------------------------------------------
    # Steps 2-7: State pipeline
    # ------------------------------------------------------------------
    if len(returns_history) > 0:
        features: dict = _extract_regime_features(returns_history)
        regime_result = regime_detector.detect_regime(features)
        vol_result = vol_tracker.estimate_volatility(returns_history)
        previous_state: LatentState = LatentState.default()
        predicted_state: LatentState = state_estimator.predict(previous_state)
        observation: dict = _build_observation_vector(regime_result, vol_result)
        _latent_state: LatentState = state_estimator.update(predicted_state, observation)

    # ------------------------------------------------------------------
    # Step 8: Risk assessment
    # ------------------------------------------------------------------
    risk_output = engine.assess(
        returns_history=returns_history,
        current_regime=current_regime,
        meta_uncertainty=None,
    )

    # ------------------------------------------------------------------
    # Steps 9-11: Exposure -> positions -> return
    # ------------------------------------------------------------------
    exposure_weight: float = risk_output.exposure_weight
    positions: dict = route_exposure_to_positions(
        total_capital=total_capital,
        exposure_fraction=exposure_weight,
        asset_prices=asset_prices,
    )
    return positions


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def x_run_full_pipeline__mutmut_101(
    returns_history: list,
    current_regime: GlobalRegimeState,
    meta_uncertainty: float,
    total_capital: float,
    asset_prices: dict,
) -> dict:
    """
    Full deterministic pipeline from returns history to final positions.

    Step 0: Governance gate (GOV-01 + GOV-05 only).
    Steps 1-11: Unchanged from v1.1.0.

    Raises
    ------
    GovernanceViolationError
        meta_uncertainty out of [0.0, 1.0] or regime not GlobalRegimeState.
    ValueError
        Propagated from RiskEngine (invalid returns_history).
        Propagated from route_exposure_to_positions (invalid capital/prices).
    """
    # ------------------------------------------------------------------
    # Step 0: Governance Gate -- GOV-01 and GOV-05 only
    # ------------------------------------------------------------------

    # GOV-01: meta_uncertainty must be in [0.0, 1.0]
    _meta_invalid = (
        not isinstance(meta_uncertainty, (int, float))
        or not (0.0 <= float(meta_uncertainty) <= 1.0)
    )

    # GOV-05: regime must be a GlobalRegimeState instance
    _regime_invalid = not isinstance(current_regime, GlobalRegimeState)

    if _meta_invalid or _regime_invalid:
        # Build a minimal result via validate_pipeline_config using safe
        # stand-in values for parameters owned by downstream modules.
        _safe_capital = total_capital if (
            isinstance(total_capital, (int, float)) and float(total_capital) > 0
        ) else 1.0
        _safe_regime = current_regime if isinstance(
            current_regime, GlobalRegimeState
        ) else GlobalRegimeState.UNKNOWN
        _safe_meta = meta_uncertainty if (
            isinstance(meta_uncertainty, (int, float))
            and 0.0 <= float(meta_uncertainty) <= 1.0
        ) else 0.5

        _gov_result = validate_pipeline_config(
            meta_uncertainty=_safe_meta if not _meta_invalid else meta_uncertainty,
            initial_capital=_safe_capital,
            window=20,
            step=1,
            regime=_safe_regime,
            periods_per_year=252,
        )
        # Only raise for the rules we gate on
        _gated_rules = {"GOV-01", "GOV-05"}
        _gated = [v for v in _gov_result.blocking_violations if v.rule_id in _gated_rules]
        # Also run with the actual bad value so the error message is accurate
        _real_result = validate_pipeline_config(
            meta_uncertainty=meta_uncertainty if isinstance(meta_uncertainty, (int, float)) else 999,
            initial_capital=_safe_capital,
            window=20,
            step=1,
            regime=current_regime,
            periods_per_year=252,
        )
        _real_gated = [v for v in _real_result.blocking_violations if v.rule_id in _gated_rules]
        if _real_gated:
            raise GovernanceViolationError(_real_result)

    # ------------------------------------------------------------------
    # Step 1: Instantiate all components fresh per call
    # ------------------------------------------------------------------
    engine: RiskEngine = RiskEngine()
    regime_detector: RegimeDetector = RegimeDetector()
    vol_tracker: VolatilityTracker = VolatilityTracker()
    state_estimator: StateEstimator = StateEstimator()

    # ------------------------------------------------------------------
    # Steps 2-7: State pipeline
    # ------------------------------------------------------------------
    if len(returns_history) > 0:
        features: dict = _extract_regime_features(returns_history)
        regime_result = regime_detector.detect_regime(features)
        vol_result = vol_tracker.estimate_volatility(returns_history)
        previous_state: LatentState = LatentState.default()
        predicted_state: LatentState = state_estimator.predict(previous_state)
        observation: dict = _build_observation_vector(regime_result, vol_result)
        _latent_state: LatentState = state_estimator.update(predicted_state, observation)

    # ------------------------------------------------------------------
    # Step 8: Risk assessment
    # ------------------------------------------------------------------
    risk_output = engine.assess(
        current_regime=current_regime,
        meta_uncertainty=meta_uncertainty,
    )

    # ------------------------------------------------------------------
    # Steps 9-11: Exposure -> positions -> return
    # ------------------------------------------------------------------
    exposure_weight: float = risk_output.exposure_weight
    positions: dict = route_exposure_to_positions(
        total_capital=total_capital,
        exposure_fraction=exposure_weight,
        asset_prices=asset_prices,
    )
    return positions


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def x_run_full_pipeline__mutmut_102(
    returns_history: list,
    current_regime: GlobalRegimeState,
    meta_uncertainty: float,
    total_capital: float,
    asset_prices: dict,
) -> dict:
    """
    Full deterministic pipeline from returns history to final positions.

    Step 0: Governance gate (GOV-01 + GOV-05 only).
    Steps 1-11: Unchanged from v1.1.0.

    Raises
    ------
    GovernanceViolationError
        meta_uncertainty out of [0.0, 1.0] or regime not GlobalRegimeState.
    ValueError
        Propagated from RiskEngine (invalid returns_history).
        Propagated from route_exposure_to_positions (invalid capital/prices).
    """
    # ------------------------------------------------------------------
    # Step 0: Governance Gate -- GOV-01 and GOV-05 only
    # ------------------------------------------------------------------

    # GOV-01: meta_uncertainty must be in [0.0, 1.0]
    _meta_invalid = (
        not isinstance(meta_uncertainty, (int, float))
        or not (0.0 <= float(meta_uncertainty) <= 1.0)
    )

    # GOV-05: regime must be a GlobalRegimeState instance
    _regime_invalid = not isinstance(current_regime, GlobalRegimeState)

    if _meta_invalid or _regime_invalid:
        # Build a minimal result via validate_pipeline_config using safe
        # stand-in values for parameters owned by downstream modules.
        _safe_capital = total_capital if (
            isinstance(total_capital, (int, float)) and float(total_capital) > 0
        ) else 1.0
        _safe_regime = current_regime if isinstance(
            current_regime, GlobalRegimeState
        ) else GlobalRegimeState.UNKNOWN
        _safe_meta = meta_uncertainty if (
            isinstance(meta_uncertainty, (int, float))
            and 0.0 <= float(meta_uncertainty) <= 1.0
        ) else 0.5

        _gov_result = validate_pipeline_config(
            meta_uncertainty=_safe_meta if not _meta_invalid else meta_uncertainty,
            initial_capital=_safe_capital,
            window=20,
            step=1,
            regime=_safe_regime,
            periods_per_year=252,
        )
        # Only raise for the rules we gate on
        _gated_rules = {"GOV-01", "GOV-05"}
        _gated = [v for v in _gov_result.blocking_violations if v.rule_id in _gated_rules]
        # Also run with the actual bad value so the error message is accurate
        _real_result = validate_pipeline_config(
            meta_uncertainty=meta_uncertainty if isinstance(meta_uncertainty, (int, float)) else 999,
            initial_capital=_safe_capital,
            window=20,
            step=1,
            regime=current_regime,
            periods_per_year=252,
        )
        _real_gated = [v for v in _real_result.blocking_violations if v.rule_id in _gated_rules]
        if _real_gated:
            raise GovernanceViolationError(_real_result)

    # ------------------------------------------------------------------
    # Step 1: Instantiate all components fresh per call
    # ------------------------------------------------------------------
    engine: RiskEngine = RiskEngine()
    regime_detector: RegimeDetector = RegimeDetector()
    vol_tracker: VolatilityTracker = VolatilityTracker()
    state_estimator: StateEstimator = StateEstimator()

    # ------------------------------------------------------------------
    # Steps 2-7: State pipeline
    # ------------------------------------------------------------------
    if len(returns_history) > 0:
        features: dict = _extract_regime_features(returns_history)
        regime_result = regime_detector.detect_regime(features)
        vol_result = vol_tracker.estimate_volatility(returns_history)
        previous_state: LatentState = LatentState.default()
        predicted_state: LatentState = state_estimator.predict(previous_state)
        observation: dict = _build_observation_vector(regime_result, vol_result)
        _latent_state: LatentState = state_estimator.update(predicted_state, observation)

    # ------------------------------------------------------------------
    # Step 8: Risk assessment
    # ------------------------------------------------------------------
    risk_output = engine.assess(
        returns_history=returns_history,
        meta_uncertainty=meta_uncertainty,
    )

    # ------------------------------------------------------------------
    # Steps 9-11: Exposure -> positions -> return
    # ------------------------------------------------------------------
    exposure_weight: float = risk_output.exposure_weight
    positions: dict = route_exposure_to_positions(
        total_capital=total_capital,
        exposure_fraction=exposure_weight,
        asset_prices=asset_prices,
    )
    return positions


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def x_run_full_pipeline__mutmut_103(
    returns_history: list,
    current_regime: GlobalRegimeState,
    meta_uncertainty: float,
    total_capital: float,
    asset_prices: dict,
) -> dict:
    """
    Full deterministic pipeline from returns history to final positions.

    Step 0: Governance gate (GOV-01 + GOV-05 only).
    Steps 1-11: Unchanged from v1.1.0.

    Raises
    ------
    GovernanceViolationError
        meta_uncertainty out of [0.0, 1.0] or regime not GlobalRegimeState.
    ValueError
        Propagated from RiskEngine (invalid returns_history).
        Propagated from route_exposure_to_positions (invalid capital/prices).
    """
    # ------------------------------------------------------------------
    # Step 0: Governance Gate -- GOV-01 and GOV-05 only
    # ------------------------------------------------------------------

    # GOV-01: meta_uncertainty must be in [0.0, 1.0]
    _meta_invalid = (
        not isinstance(meta_uncertainty, (int, float))
        or not (0.0 <= float(meta_uncertainty) <= 1.0)
    )

    # GOV-05: regime must be a GlobalRegimeState instance
    _regime_invalid = not isinstance(current_regime, GlobalRegimeState)

    if _meta_invalid or _regime_invalid:
        # Build a minimal result via validate_pipeline_config using safe
        # stand-in values for parameters owned by downstream modules.
        _safe_capital = total_capital if (
            isinstance(total_capital, (int, float)) and float(total_capital) > 0
        ) else 1.0
        _safe_regime = current_regime if isinstance(
            current_regime, GlobalRegimeState
        ) else GlobalRegimeState.UNKNOWN
        _safe_meta = meta_uncertainty if (
            isinstance(meta_uncertainty, (int, float))
            and 0.0 <= float(meta_uncertainty) <= 1.0
        ) else 0.5

        _gov_result = validate_pipeline_config(
            meta_uncertainty=_safe_meta if not _meta_invalid else meta_uncertainty,
            initial_capital=_safe_capital,
            window=20,
            step=1,
            regime=_safe_regime,
            periods_per_year=252,
        )
        # Only raise for the rules we gate on
        _gated_rules = {"GOV-01", "GOV-05"}
        _gated = [v for v in _gov_result.blocking_violations if v.rule_id in _gated_rules]
        # Also run with the actual bad value so the error message is accurate
        _real_result = validate_pipeline_config(
            meta_uncertainty=meta_uncertainty if isinstance(meta_uncertainty, (int, float)) else 999,
            initial_capital=_safe_capital,
            window=20,
            step=1,
            regime=current_regime,
            periods_per_year=252,
        )
        _real_gated = [v for v in _real_result.blocking_violations if v.rule_id in _gated_rules]
        if _real_gated:
            raise GovernanceViolationError(_real_result)

    # ------------------------------------------------------------------
    # Step 1: Instantiate all components fresh per call
    # ------------------------------------------------------------------
    engine: RiskEngine = RiskEngine()
    regime_detector: RegimeDetector = RegimeDetector()
    vol_tracker: VolatilityTracker = VolatilityTracker()
    state_estimator: StateEstimator = StateEstimator()

    # ------------------------------------------------------------------
    # Steps 2-7: State pipeline
    # ------------------------------------------------------------------
    if len(returns_history) > 0:
        features: dict = _extract_regime_features(returns_history)
        regime_result = regime_detector.detect_regime(features)
        vol_result = vol_tracker.estimate_volatility(returns_history)
        previous_state: LatentState = LatentState.default()
        predicted_state: LatentState = state_estimator.predict(previous_state)
        observation: dict = _build_observation_vector(regime_result, vol_result)
        _latent_state: LatentState = state_estimator.update(predicted_state, observation)

    # ------------------------------------------------------------------
    # Step 8: Risk assessment
    # ------------------------------------------------------------------
    risk_output = engine.assess(
        returns_history=returns_history,
        current_regime=current_regime,
        )

    # ------------------------------------------------------------------
    # Steps 9-11: Exposure -> positions -> return
    # ------------------------------------------------------------------
    exposure_weight: float = risk_output.exposure_weight
    positions: dict = route_exposure_to_positions(
        total_capital=total_capital,
        exposure_fraction=exposure_weight,
        asset_prices=asset_prices,
    )
    return positions


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def x_run_full_pipeline__mutmut_104(
    returns_history: list,
    current_regime: GlobalRegimeState,
    meta_uncertainty: float,
    total_capital: float,
    asset_prices: dict,
) -> dict:
    """
    Full deterministic pipeline from returns history to final positions.

    Step 0: Governance gate (GOV-01 + GOV-05 only).
    Steps 1-11: Unchanged from v1.1.0.

    Raises
    ------
    GovernanceViolationError
        meta_uncertainty out of [0.0, 1.0] or regime not GlobalRegimeState.
    ValueError
        Propagated from RiskEngine (invalid returns_history).
        Propagated from route_exposure_to_positions (invalid capital/prices).
    """
    # ------------------------------------------------------------------
    # Step 0: Governance Gate -- GOV-01 and GOV-05 only
    # ------------------------------------------------------------------

    # GOV-01: meta_uncertainty must be in [0.0, 1.0]
    _meta_invalid = (
        not isinstance(meta_uncertainty, (int, float))
        or not (0.0 <= float(meta_uncertainty) <= 1.0)
    )

    # GOV-05: regime must be a GlobalRegimeState instance
    _regime_invalid = not isinstance(current_regime, GlobalRegimeState)

    if _meta_invalid or _regime_invalid:
        # Build a minimal result via validate_pipeline_config using safe
        # stand-in values for parameters owned by downstream modules.
        _safe_capital = total_capital if (
            isinstance(total_capital, (int, float)) and float(total_capital) > 0
        ) else 1.0
        _safe_regime = current_regime if isinstance(
            current_regime, GlobalRegimeState
        ) else GlobalRegimeState.UNKNOWN
        _safe_meta = meta_uncertainty if (
            isinstance(meta_uncertainty, (int, float))
            and 0.0 <= float(meta_uncertainty) <= 1.0
        ) else 0.5

        _gov_result = validate_pipeline_config(
            meta_uncertainty=_safe_meta if not _meta_invalid else meta_uncertainty,
            initial_capital=_safe_capital,
            window=20,
            step=1,
            regime=_safe_regime,
            periods_per_year=252,
        )
        # Only raise for the rules we gate on
        _gated_rules = {"GOV-01", "GOV-05"}
        _gated = [v for v in _gov_result.blocking_violations if v.rule_id in _gated_rules]
        # Also run with the actual bad value so the error message is accurate
        _real_result = validate_pipeline_config(
            meta_uncertainty=meta_uncertainty if isinstance(meta_uncertainty, (int, float)) else 999,
            initial_capital=_safe_capital,
            window=20,
            step=1,
            regime=current_regime,
            periods_per_year=252,
        )
        _real_gated = [v for v in _real_result.blocking_violations if v.rule_id in _gated_rules]
        if _real_gated:
            raise GovernanceViolationError(_real_result)

    # ------------------------------------------------------------------
    # Step 1: Instantiate all components fresh per call
    # ------------------------------------------------------------------
    engine: RiskEngine = RiskEngine()
    regime_detector: RegimeDetector = RegimeDetector()
    vol_tracker: VolatilityTracker = VolatilityTracker()
    state_estimator: StateEstimator = StateEstimator()

    # ------------------------------------------------------------------
    # Steps 2-7: State pipeline
    # ------------------------------------------------------------------
    if len(returns_history) > 0:
        features: dict = _extract_regime_features(returns_history)
        regime_result = regime_detector.detect_regime(features)
        vol_result = vol_tracker.estimate_volatility(returns_history)
        previous_state: LatentState = LatentState.default()
        predicted_state: LatentState = state_estimator.predict(previous_state)
        observation: dict = _build_observation_vector(regime_result, vol_result)
        _latent_state: LatentState = state_estimator.update(predicted_state, observation)

    # ------------------------------------------------------------------
    # Step 8: Risk assessment
    # ------------------------------------------------------------------
    risk_output = engine.assess(
        returns_history=returns_history,
        current_regime=current_regime,
        meta_uncertainty=meta_uncertainty,
    )

    # ------------------------------------------------------------------
    # Steps 9-11: Exposure -> positions -> return
    # ------------------------------------------------------------------
    exposure_weight: float = None
    positions: dict = route_exposure_to_positions(
        total_capital=total_capital,
        exposure_fraction=exposure_weight,
        asset_prices=asset_prices,
    )
    return positions


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def x_run_full_pipeline__mutmut_105(
    returns_history: list,
    current_regime: GlobalRegimeState,
    meta_uncertainty: float,
    total_capital: float,
    asset_prices: dict,
) -> dict:
    """
    Full deterministic pipeline from returns history to final positions.

    Step 0: Governance gate (GOV-01 + GOV-05 only).
    Steps 1-11: Unchanged from v1.1.0.

    Raises
    ------
    GovernanceViolationError
        meta_uncertainty out of [0.0, 1.0] or regime not GlobalRegimeState.
    ValueError
        Propagated from RiskEngine (invalid returns_history).
        Propagated from route_exposure_to_positions (invalid capital/prices).
    """
    # ------------------------------------------------------------------
    # Step 0: Governance Gate -- GOV-01 and GOV-05 only
    # ------------------------------------------------------------------

    # GOV-01: meta_uncertainty must be in [0.0, 1.0]
    _meta_invalid = (
        not isinstance(meta_uncertainty, (int, float))
        or not (0.0 <= float(meta_uncertainty) <= 1.0)
    )

    # GOV-05: regime must be a GlobalRegimeState instance
    _regime_invalid = not isinstance(current_regime, GlobalRegimeState)

    if _meta_invalid or _regime_invalid:
        # Build a minimal result via validate_pipeline_config using safe
        # stand-in values for parameters owned by downstream modules.
        _safe_capital = total_capital if (
            isinstance(total_capital, (int, float)) and float(total_capital) > 0
        ) else 1.0
        _safe_regime = current_regime if isinstance(
            current_regime, GlobalRegimeState
        ) else GlobalRegimeState.UNKNOWN
        _safe_meta = meta_uncertainty if (
            isinstance(meta_uncertainty, (int, float))
            and 0.0 <= float(meta_uncertainty) <= 1.0
        ) else 0.5

        _gov_result = validate_pipeline_config(
            meta_uncertainty=_safe_meta if not _meta_invalid else meta_uncertainty,
            initial_capital=_safe_capital,
            window=20,
            step=1,
            regime=_safe_regime,
            periods_per_year=252,
        )
        # Only raise for the rules we gate on
        _gated_rules = {"GOV-01", "GOV-05"}
        _gated = [v for v in _gov_result.blocking_violations if v.rule_id in _gated_rules]
        # Also run with the actual bad value so the error message is accurate
        _real_result = validate_pipeline_config(
            meta_uncertainty=meta_uncertainty if isinstance(meta_uncertainty, (int, float)) else 999,
            initial_capital=_safe_capital,
            window=20,
            step=1,
            regime=current_regime,
            periods_per_year=252,
        )
        _real_gated = [v for v in _real_result.blocking_violations if v.rule_id in _gated_rules]
        if _real_gated:
            raise GovernanceViolationError(_real_result)

    # ------------------------------------------------------------------
    # Step 1: Instantiate all components fresh per call
    # ------------------------------------------------------------------
    engine: RiskEngine = RiskEngine()
    regime_detector: RegimeDetector = RegimeDetector()
    vol_tracker: VolatilityTracker = VolatilityTracker()
    state_estimator: StateEstimator = StateEstimator()

    # ------------------------------------------------------------------
    # Steps 2-7: State pipeline
    # ------------------------------------------------------------------
    if len(returns_history) > 0:
        features: dict = _extract_regime_features(returns_history)
        regime_result = regime_detector.detect_regime(features)
        vol_result = vol_tracker.estimate_volatility(returns_history)
        previous_state: LatentState = LatentState.default()
        predicted_state: LatentState = state_estimator.predict(previous_state)
        observation: dict = _build_observation_vector(regime_result, vol_result)
        _latent_state: LatentState = state_estimator.update(predicted_state, observation)

    # ------------------------------------------------------------------
    # Step 8: Risk assessment
    # ------------------------------------------------------------------
    risk_output = engine.assess(
        returns_history=returns_history,
        current_regime=current_regime,
        meta_uncertainty=meta_uncertainty,
    )

    # ------------------------------------------------------------------
    # Steps 9-11: Exposure -> positions -> return
    # ------------------------------------------------------------------
    exposure_weight: float = risk_output.exposure_weight
    positions: dict = None
    return positions


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def x_run_full_pipeline__mutmut_106(
    returns_history: list,
    current_regime: GlobalRegimeState,
    meta_uncertainty: float,
    total_capital: float,
    asset_prices: dict,
) -> dict:
    """
    Full deterministic pipeline from returns history to final positions.

    Step 0: Governance gate (GOV-01 + GOV-05 only).
    Steps 1-11: Unchanged from v1.1.0.

    Raises
    ------
    GovernanceViolationError
        meta_uncertainty out of [0.0, 1.0] or regime not GlobalRegimeState.
    ValueError
        Propagated from RiskEngine (invalid returns_history).
        Propagated from route_exposure_to_positions (invalid capital/prices).
    """
    # ------------------------------------------------------------------
    # Step 0: Governance Gate -- GOV-01 and GOV-05 only
    # ------------------------------------------------------------------

    # GOV-01: meta_uncertainty must be in [0.0, 1.0]
    _meta_invalid = (
        not isinstance(meta_uncertainty, (int, float))
        or not (0.0 <= float(meta_uncertainty) <= 1.0)
    )

    # GOV-05: regime must be a GlobalRegimeState instance
    _regime_invalid = not isinstance(current_regime, GlobalRegimeState)

    if _meta_invalid or _regime_invalid:
        # Build a minimal result via validate_pipeline_config using safe
        # stand-in values for parameters owned by downstream modules.
        _safe_capital = total_capital if (
            isinstance(total_capital, (int, float)) and float(total_capital) > 0
        ) else 1.0
        _safe_regime = current_regime if isinstance(
            current_regime, GlobalRegimeState
        ) else GlobalRegimeState.UNKNOWN
        _safe_meta = meta_uncertainty if (
            isinstance(meta_uncertainty, (int, float))
            and 0.0 <= float(meta_uncertainty) <= 1.0
        ) else 0.5

        _gov_result = validate_pipeline_config(
            meta_uncertainty=_safe_meta if not _meta_invalid else meta_uncertainty,
            initial_capital=_safe_capital,
            window=20,
            step=1,
            regime=_safe_regime,
            periods_per_year=252,
        )
        # Only raise for the rules we gate on
        _gated_rules = {"GOV-01", "GOV-05"}
        _gated = [v for v in _gov_result.blocking_violations if v.rule_id in _gated_rules]
        # Also run with the actual bad value so the error message is accurate
        _real_result = validate_pipeline_config(
            meta_uncertainty=meta_uncertainty if isinstance(meta_uncertainty, (int, float)) else 999,
            initial_capital=_safe_capital,
            window=20,
            step=1,
            regime=current_regime,
            periods_per_year=252,
        )
        _real_gated = [v for v in _real_result.blocking_violations if v.rule_id in _gated_rules]
        if _real_gated:
            raise GovernanceViolationError(_real_result)

    # ------------------------------------------------------------------
    # Step 1: Instantiate all components fresh per call
    # ------------------------------------------------------------------
    engine: RiskEngine = RiskEngine()
    regime_detector: RegimeDetector = RegimeDetector()
    vol_tracker: VolatilityTracker = VolatilityTracker()
    state_estimator: StateEstimator = StateEstimator()

    # ------------------------------------------------------------------
    # Steps 2-7: State pipeline
    # ------------------------------------------------------------------
    if len(returns_history) > 0:
        features: dict = _extract_regime_features(returns_history)
        regime_result = regime_detector.detect_regime(features)
        vol_result = vol_tracker.estimate_volatility(returns_history)
        previous_state: LatentState = LatentState.default()
        predicted_state: LatentState = state_estimator.predict(previous_state)
        observation: dict = _build_observation_vector(regime_result, vol_result)
        _latent_state: LatentState = state_estimator.update(predicted_state, observation)

    # ------------------------------------------------------------------
    # Step 8: Risk assessment
    # ------------------------------------------------------------------
    risk_output = engine.assess(
        returns_history=returns_history,
        current_regime=current_regime,
        meta_uncertainty=meta_uncertainty,
    )

    # ------------------------------------------------------------------
    # Steps 9-11: Exposure -> positions -> return
    # ------------------------------------------------------------------
    exposure_weight: float = risk_output.exposure_weight
    positions: dict = route_exposure_to_positions(
        total_capital=None,
        exposure_fraction=exposure_weight,
        asset_prices=asset_prices,
    )
    return positions


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def x_run_full_pipeline__mutmut_107(
    returns_history: list,
    current_regime: GlobalRegimeState,
    meta_uncertainty: float,
    total_capital: float,
    asset_prices: dict,
) -> dict:
    """
    Full deterministic pipeline from returns history to final positions.

    Step 0: Governance gate (GOV-01 + GOV-05 only).
    Steps 1-11: Unchanged from v1.1.0.

    Raises
    ------
    GovernanceViolationError
        meta_uncertainty out of [0.0, 1.0] or regime not GlobalRegimeState.
    ValueError
        Propagated from RiskEngine (invalid returns_history).
        Propagated from route_exposure_to_positions (invalid capital/prices).
    """
    # ------------------------------------------------------------------
    # Step 0: Governance Gate -- GOV-01 and GOV-05 only
    # ------------------------------------------------------------------

    # GOV-01: meta_uncertainty must be in [0.0, 1.0]
    _meta_invalid = (
        not isinstance(meta_uncertainty, (int, float))
        or not (0.0 <= float(meta_uncertainty) <= 1.0)
    )

    # GOV-05: regime must be a GlobalRegimeState instance
    _regime_invalid = not isinstance(current_regime, GlobalRegimeState)

    if _meta_invalid or _regime_invalid:
        # Build a minimal result via validate_pipeline_config using safe
        # stand-in values for parameters owned by downstream modules.
        _safe_capital = total_capital if (
            isinstance(total_capital, (int, float)) and float(total_capital) > 0
        ) else 1.0
        _safe_regime = current_regime if isinstance(
            current_regime, GlobalRegimeState
        ) else GlobalRegimeState.UNKNOWN
        _safe_meta = meta_uncertainty if (
            isinstance(meta_uncertainty, (int, float))
            and 0.0 <= float(meta_uncertainty) <= 1.0
        ) else 0.5

        _gov_result = validate_pipeline_config(
            meta_uncertainty=_safe_meta if not _meta_invalid else meta_uncertainty,
            initial_capital=_safe_capital,
            window=20,
            step=1,
            regime=_safe_regime,
            periods_per_year=252,
        )
        # Only raise for the rules we gate on
        _gated_rules = {"GOV-01", "GOV-05"}
        _gated = [v for v in _gov_result.blocking_violations if v.rule_id in _gated_rules]
        # Also run with the actual bad value so the error message is accurate
        _real_result = validate_pipeline_config(
            meta_uncertainty=meta_uncertainty if isinstance(meta_uncertainty, (int, float)) else 999,
            initial_capital=_safe_capital,
            window=20,
            step=1,
            regime=current_regime,
            periods_per_year=252,
        )
        _real_gated = [v for v in _real_result.blocking_violations if v.rule_id in _gated_rules]
        if _real_gated:
            raise GovernanceViolationError(_real_result)

    # ------------------------------------------------------------------
    # Step 1: Instantiate all components fresh per call
    # ------------------------------------------------------------------
    engine: RiskEngine = RiskEngine()
    regime_detector: RegimeDetector = RegimeDetector()
    vol_tracker: VolatilityTracker = VolatilityTracker()
    state_estimator: StateEstimator = StateEstimator()

    # ------------------------------------------------------------------
    # Steps 2-7: State pipeline
    # ------------------------------------------------------------------
    if len(returns_history) > 0:
        features: dict = _extract_regime_features(returns_history)
        regime_result = regime_detector.detect_regime(features)
        vol_result = vol_tracker.estimate_volatility(returns_history)
        previous_state: LatentState = LatentState.default()
        predicted_state: LatentState = state_estimator.predict(previous_state)
        observation: dict = _build_observation_vector(regime_result, vol_result)
        _latent_state: LatentState = state_estimator.update(predicted_state, observation)

    # ------------------------------------------------------------------
    # Step 8: Risk assessment
    # ------------------------------------------------------------------
    risk_output = engine.assess(
        returns_history=returns_history,
        current_regime=current_regime,
        meta_uncertainty=meta_uncertainty,
    )

    # ------------------------------------------------------------------
    # Steps 9-11: Exposure -> positions -> return
    # ------------------------------------------------------------------
    exposure_weight: float = risk_output.exposure_weight
    positions: dict = route_exposure_to_positions(
        total_capital=total_capital,
        exposure_fraction=None,
        asset_prices=asset_prices,
    )
    return positions


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def x_run_full_pipeline__mutmut_108(
    returns_history: list,
    current_regime: GlobalRegimeState,
    meta_uncertainty: float,
    total_capital: float,
    asset_prices: dict,
) -> dict:
    """
    Full deterministic pipeline from returns history to final positions.

    Step 0: Governance gate (GOV-01 + GOV-05 only).
    Steps 1-11: Unchanged from v1.1.0.

    Raises
    ------
    GovernanceViolationError
        meta_uncertainty out of [0.0, 1.0] or regime not GlobalRegimeState.
    ValueError
        Propagated from RiskEngine (invalid returns_history).
        Propagated from route_exposure_to_positions (invalid capital/prices).
    """
    # ------------------------------------------------------------------
    # Step 0: Governance Gate -- GOV-01 and GOV-05 only
    # ------------------------------------------------------------------

    # GOV-01: meta_uncertainty must be in [0.0, 1.0]
    _meta_invalid = (
        not isinstance(meta_uncertainty, (int, float))
        or not (0.0 <= float(meta_uncertainty) <= 1.0)
    )

    # GOV-05: regime must be a GlobalRegimeState instance
    _regime_invalid = not isinstance(current_regime, GlobalRegimeState)

    if _meta_invalid or _regime_invalid:
        # Build a minimal result via validate_pipeline_config using safe
        # stand-in values for parameters owned by downstream modules.
        _safe_capital = total_capital if (
            isinstance(total_capital, (int, float)) and float(total_capital) > 0
        ) else 1.0
        _safe_regime = current_regime if isinstance(
            current_regime, GlobalRegimeState
        ) else GlobalRegimeState.UNKNOWN
        _safe_meta = meta_uncertainty if (
            isinstance(meta_uncertainty, (int, float))
            and 0.0 <= float(meta_uncertainty) <= 1.0
        ) else 0.5

        _gov_result = validate_pipeline_config(
            meta_uncertainty=_safe_meta if not _meta_invalid else meta_uncertainty,
            initial_capital=_safe_capital,
            window=20,
            step=1,
            regime=_safe_regime,
            periods_per_year=252,
        )
        # Only raise for the rules we gate on
        _gated_rules = {"GOV-01", "GOV-05"}
        _gated = [v for v in _gov_result.blocking_violations if v.rule_id in _gated_rules]
        # Also run with the actual bad value so the error message is accurate
        _real_result = validate_pipeline_config(
            meta_uncertainty=meta_uncertainty if isinstance(meta_uncertainty, (int, float)) else 999,
            initial_capital=_safe_capital,
            window=20,
            step=1,
            regime=current_regime,
            periods_per_year=252,
        )
        _real_gated = [v for v in _real_result.blocking_violations if v.rule_id in _gated_rules]
        if _real_gated:
            raise GovernanceViolationError(_real_result)

    # ------------------------------------------------------------------
    # Step 1: Instantiate all components fresh per call
    # ------------------------------------------------------------------
    engine: RiskEngine = RiskEngine()
    regime_detector: RegimeDetector = RegimeDetector()
    vol_tracker: VolatilityTracker = VolatilityTracker()
    state_estimator: StateEstimator = StateEstimator()

    # ------------------------------------------------------------------
    # Steps 2-7: State pipeline
    # ------------------------------------------------------------------
    if len(returns_history) > 0:
        features: dict = _extract_regime_features(returns_history)
        regime_result = regime_detector.detect_regime(features)
        vol_result = vol_tracker.estimate_volatility(returns_history)
        previous_state: LatentState = LatentState.default()
        predicted_state: LatentState = state_estimator.predict(previous_state)
        observation: dict = _build_observation_vector(regime_result, vol_result)
        _latent_state: LatentState = state_estimator.update(predicted_state, observation)

    # ------------------------------------------------------------------
    # Step 8: Risk assessment
    # ------------------------------------------------------------------
    risk_output = engine.assess(
        returns_history=returns_history,
        current_regime=current_regime,
        meta_uncertainty=meta_uncertainty,
    )

    # ------------------------------------------------------------------
    # Steps 9-11: Exposure -> positions -> return
    # ------------------------------------------------------------------
    exposure_weight: float = risk_output.exposure_weight
    positions: dict = route_exposure_to_positions(
        total_capital=total_capital,
        exposure_fraction=exposure_weight,
        asset_prices=None,
    )
    return positions


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def x_run_full_pipeline__mutmut_109(
    returns_history: list,
    current_regime: GlobalRegimeState,
    meta_uncertainty: float,
    total_capital: float,
    asset_prices: dict,
) -> dict:
    """
    Full deterministic pipeline from returns history to final positions.

    Step 0: Governance gate (GOV-01 + GOV-05 only).
    Steps 1-11: Unchanged from v1.1.0.

    Raises
    ------
    GovernanceViolationError
        meta_uncertainty out of [0.0, 1.0] or regime not GlobalRegimeState.
    ValueError
        Propagated from RiskEngine (invalid returns_history).
        Propagated from route_exposure_to_positions (invalid capital/prices).
    """
    # ------------------------------------------------------------------
    # Step 0: Governance Gate -- GOV-01 and GOV-05 only
    # ------------------------------------------------------------------

    # GOV-01: meta_uncertainty must be in [0.0, 1.0]
    _meta_invalid = (
        not isinstance(meta_uncertainty, (int, float))
        or not (0.0 <= float(meta_uncertainty) <= 1.0)
    )

    # GOV-05: regime must be a GlobalRegimeState instance
    _regime_invalid = not isinstance(current_regime, GlobalRegimeState)

    if _meta_invalid or _regime_invalid:
        # Build a minimal result via validate_pipeline_config using safe
        # stand-in values for parameters owned by downstream modules.
        _safe_capital = total_capital if (
            isinstance(total_capital, (int, float)) and float(total_capital) > 0
        ) else 1.0
        _safe_regime = current_regime if isinstance(
            current_regime, GlobalRegimeState
        ) else GlobalRegimeState.UNKNOWN
        _safe_meta = meta_uncertainty if (
            isinstance(meta_uncertainty, (int, float))
            and 0.0 <= float(meta_uncertainty) <= 1.0
        ) else 0.5

        _gov_result = validate_pipeline_config(
            meta_uncertainty=_safe_meta if not _meta_invalid else meta_uncertainty,
            initial_capital=_safe_capital,
            window=20,
            step=1,
            regime=_safe_regime,
            periods_per_year=252,
        )
        # Only raise for the rules we gate on
        _gated_rules = {"GOV-01", "GOV-05"}
        _gated = [v for v in _gov_result.blocking_violations if v.rule_id in _gated_rules]
        # Also run with the actual bad value so the error message is accurate
        _real_result = validate_pipeline_config(
            meta_uncertainty=meta_uncertainty if isinstance(meta_uncertainty, (int, float)) else 999,
            initial_capital=_safe_capital,
            window=20,
            step=1,
            regime=current_regime,
            periods_per_year=252,
        )
        _real_gated = [v for v in _real_result.blocking_violations if v.rule_id in _gated_rules]
        if _real_gated:
            raise GovernanceViolationError(_real_result)

    # ------------------------------------------------------------------
    # Step 1: Instantiate all components fresh per call
    # ------------------------------------------------------------------
    engine: RiskEngine = RiskEngine()
    regime_detector: RegimeDetector = RegimeDetector()
    vol_tracker: VolatilityTracker = VolatilityTracker()
    state_estimator: StateEstimator = StateEstimator()

    # ------------------------------------------------------------------
    # Steps 2-7: State pipeline
    # ------------------------------------------------------------------
    if len(returns_history) > 0:
        features: dict = _extract_regime_features(returns_history)
        regime_result = regime_detector.detect_regime(features)
        vol_result = vol_tracker.estimate_volatility(returns_history)
        previous_state: LatentState = LatentState.default()
        predicted_state: LatentState = state_estimator.predict(previous_state)
        observation: dict = _build_observation_vector(regime_result, vol_result)
        _latent_state: LatentState = state_estimator.update(predicted_state, observation)

    # ------------------------------------------------------------------
    # Step 8: Risk assessment
    # ------------------------------------------------------------------
    risk_output = engine.assess(
        returns_history=returns_history,
        current_regime=current_regime,
        meta_uncertainty=meta_uncertainty,
    )

    # ------------------------------------------------------------------
    # Steps 9-11: Exposure -> positions -> return
    # ------------------------------------------------------------------
    exposure_weight: float = risk_output.exposure_weight
    positions: dict = route_exposure_to_positions(
        exposure_fraction=exposure_weight,
        asset_prices=asset_prices,
    )
    return positions


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def x_run_full_pipeline__mutmut_110(
    returns_history: list,
    current_regime: GlobalRegimeState,
    meta_uncertainty: float,
    total_capital: float,
    asset_prices: dict,
) -> dict:
    """
    Full deterministic pipeline from returns history to final positions.

    Step 0: Governance gate (GOV-01 + GOV-05 only).
    Steps 1-11: Unchanged from v1.1.0.

    Raises
    ------
    GovernanceViolationError
        meta_uncertainty out of [0.0, 1.0] or regime not GlobalRegimeState.
    ValueError
        Propagated from RiskEngine (invalid returns_history).
        Propagated from route_exposure_to_positions (invalid capital/prices).
    """
    # ------------------------------------------------------------------
    # Step 0: Governance Gate -- GOV-01 and GOV-05 only
    # ------------------------------------------------------------------

    # GOV-01: meta_uncertainty must be in [0.0, 1.0]
    _meta_invalid = (
        not isinstance(meta_uncertainty, (int, float))
        or not (0.0 <= float(meta_uncertainty) <= 1.0)
    )

    # GOV-05: regime must be a GlobalRegimeState instance
    _regime_invalid = not isinstance(current_regime, GlobalRegimeState)

    if _meta_invalid or _regime_invalid:
        # Build a minimal result via validate_pipeline_config using safe
        # stand-in values for parameters owned by downstream modules.
        _safe_capital = total_capital if (
            isinstance(total_capital, (int, float)) and float(total_capital) > 0
        ) else 1.0
        _safe_regime = current_regime if isinstance(
            current_regime, GlobalRegimeState
        ) else GlobalRegimeState.UNKNOWN
        _safe_meta = meta_uncertainty if (
            isinstance(meta_uncertainty, (int, float))
            and 0.0 <= float(meta_uncertainty) <= 1.0
        ) else 0.5

        _gov_result = validate_pipeline_config(
            meta_uncertainty=_safe_meta if not _meta_invalid else meta_uncertainty,
            initial_capital=_safe_capital,
            window=20,
            step=1,
            regime=_safe_regime,
            periods_per_year=252,
        )
        # Only raise for the rules we gate on
        _gated_rules = {"GOV-01", "GOV-05"}
        _gated = [v for v in _gov_result.blocking_violations if v.rule_id in _gated_rules]
        # Also run with the actual bad value so the error message is accurate
        _real_result = validate_pipeline_config(
            meta_uncertainty=meta_uncertainty if isinstance(meta_uncertainty, (int, float)) else 999,
            initial_capital=_safe_capital,
            window=20,
            step=1,
            regime=current_regime,
            periods_per_year=252,
        )
        _real_gated = [v for v in _real_result.blocking_violations if v.rule_id in _gated_rules]
        if _real_gated:
            raise GovernanceViolationError(_real_result)

    # ------------------------------------------------------------------
    # Step 1: Instantiate all components fresh per call
    # ------------------------------------------------------------------
    engine: RiskEngine = RiskEngine()
    regime_detector: RegimeDetector = RegimeDetector()
    vol_tracker: VolatilityTracker = VolatilityTracker()
    state_estimator: StateEstimator = StateEstimator()

    # ------------------------------------------------------------------
    # Steps 2-7: State pipeline
    # ------------------------------------------------------------------
    if len(returns_history) > 0:
        features: dict = _extract_regime_features(returns_history)
        regime_result = regime_detector.detect_regime(features)
        vol_result = vol_tracker.estimate_volatility(returns_history)
        previous_state: LatentState = LatentState.default()
        predicted_state: LatentState = state_estimator.predict(previous_state)
        observation: dict = _build_observation_vector(regime_result, vol_result)
        _latent_state: LatentState = state_estimator.update(predicted_state, observation)

    # ------------------------------------------------------------------
    # Step 8: Risk assessment
    # ------------------------------------------------------------------
    risk_output = engine.assess(
        returns_history=returns_history,
        current_regime=current_regime,
        meta_uncertainty=meta_uncertainty,
    )

    # ------------------------------------------------------------------
    # Steps 9-11: Exposure -> positions -> return
    # ------------------------------------------------------------------
    exposure_weight: float = risk_output.exposure_weight
    positions: dict = route_exposure_to_positions(
        total_capital=total_capital,
        asset_prices=asset_prices,
    )
    return positions


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def x_run_full_pipeline__mutmut_111(
    returns_history: list,
    current_regime: GlobalRegimeState,
    meta_uncertainty: float,
    total_capital: float,
    asset_prices: dict,
) -> dict:
    """
    Full deterministic pipeline from returns history to final positions.

    Step 0: Governance gate (GOV-01 + GOV-05 only).
    Steps 1-11: Unchanged from v1.1.0.

    Raises
    ------
    GovernanceViolationError
        meta_uncertainty out of [0.0, 1.0] or regime not GlobalRegimeState.
    ValueError
        Propagated from RiskEngine (invalid returns_history).
        Propagated from route_exposure_to_positions (invalid capital/prices).
    """
    # ------------------------------------------------------------------
    # Step 0: Governance Gate -- GOV-01 and GOV-05 only
    # ------------------------------------------------------------------

    # GOV-01: meta_uncertainty must be in [0.0, 1.0]
    _meta_invalid = (
        not isinstance(meta_uncertainty, (int, float))
        or not (0.0 <= float(meta_uncertainty) <= 1.0)
    )

    # GOV-05: regime must be a GlobalRegimeState instance
    _regime_invalid = not isinstance(current_regime, GlobalRegimeState)

    if _meta_invalid or _regime_invalid:
        # Build a minimal result via validate_pipeline_config using safe
        # stand-in values for parameters owned by downstream modules.
        _safe_capital = total_capital if (
            isinstance(total_capital, (int, float)) and float(total_capital) > 0
        ) else 1.0
        _safe_regime = current_regime if isinstance(
            current_regime, GlobalRegimeState
        ) else GlobalRegimeState.UNKNOWN
        _safe_meta = meta_uncertainty if (
            isinstance(meta_uncertainty, (int, float))
            and 0.0 <= float(meta_uncertainty) <= 1.0
        ) else 0.5

        _gov_result = validate_pipeline_config(
            meta_uncertainty=_safe_meta if not _meta_invalid else meta_uncertainty,
            initial_capital=_safe_capital,
            window=20,
            step=1,
            regime=_safe_regime,
            periods_per_year=252,
        )
        # Only raise for the rules we gate on
        _gated_rules = {"GOV-01", "GOV-05"}
        _gated = [v for v in _gov_result.blocking_violations if v.rule_id in _gated_rules]
        # Also run with the actual bad value so the error message is accurate
        _real_result = validate_pipeline_config(
            meta_uncertainty=meta_uncertainty if isinstance(meta_uncertainty, (int, float)) else 999,
            initial_capital=_safe_capital,
            window=20,
            step=1,
            regime=current_regime,
            periods_per_year=252,
        )
        _real_gated = [v for v in _real_result.blocking_violations if v.rule_id in _gated_rules]
        if _real_gated:
            raise GovernanceViolationError(_real_result)

    # ------------------------------------------------------------------
    # Step 1: Instantiate all components fresh per call
    # ------------------------------------------------------------------
    engine: RiskEngine = RiskEngine()
    regime_detector: RegimeDetector = RegimeDetector()
    vol_tracker: VolatilityTracker = VolatilityTracker()
    state_estimator: StateEstimator = StateEstimator()

    # ------------------------------------------------------------------
    # Steps 2-7: State pipeline
    # ------------------------------------------------------------------
    if len(returns_history) > 0:
        features: dict = _extract_regime_features(returns_history)
        regime_result = regime_detector.detect_regime(features)
        vol_result = vol_tracker.estimate_volatility(returns_history)
        previous_state: LatentState = LatentState.default()
        predicted_state: LatentState = state_estimator.predict(previous_state)
        observation: dict = _build_observation_vector(regime_result, vol_result)
        _latent_state: LatentState = state_estimator.update(predicted_state, observation)

    # ------------------------------------------------------------------
    # Step 8: Risk assessment
    # ------------------------------------------------------------------
    risk_output = engine.assess(
        returns_history=returns_history,
        current_regime=current_regime,
        meta_uncertainty=meta_uncertainty,
    )

    # ------------------------------------------------------------------
    # Steps 9-11: Exposure -> positions -> return
    # ------------------------------------------------------------------
    exposure_weight: float = risk_output.exposure_weight
    positions: dict = route_exposure_to_positions(
        total_capital=total_capital,
        exposure_fraction=exposure_weight,
        )
    return positions

x_run_full_pipeline__mutmut_mutants : ClassVar[MutantDict] = { # type: ignore
'x_run_full_pipeline__mutmut_1': x_run_full_pipeline__mutmut_1, 
    'x_run_full_pipeline__mutmut_2': x_run_full_pipeline__mutmut_2, 
    'x_run_full_pipeline__mutmut_3': x_run_full_pipeline__mutmut_3, 
    'x_run_full_pipeline__mutmut_4': x_run_full_pipeline__mutmut_4, 
    'x_run_full_pipeline__mutmut_5': x_run_full_pipeline__mutmut_5, 
    'x_run_full_pipeline__mutmut_6': x_run_full_pipeline__mutmut_6, 
    'x_run_full_pipeline__mutmut_7': x_run_full_pipeline__mutmut_7, 
    'x_run_full_pipeline__mutmut_8': x_run_full_pipeline__mutmut_8, 
    'x_run_full_pipeline__mutmut_9': x_run_full_pipeline__mutmut_9, 
    'x_run_full_pipeline__mutmut_10': x_run_full_pipeline__mutmut_10, 
    'x_run_full_pipeline__mutmut_11': x_run_full_pipeline__mutmut_11, 
    'x_run_full_pipeline__mutmut_12': x_run_full_pipeline__mutmut_12, 
    'x_run_full_pipeline__mutmut_13': x_run_full_pipeline__mutmut_13, 
    'x_run_full_pipeline__mutmut_14': x_run_full_pipeline__mutmut_14, 
    'x_run_full_pipeline__mutmut_15': x_run_full_pipeline__mutmut_15, 
    'x_run_full_pipeline__mutmut_16': x_run_full_pipeline__mutmut_16, 
    'x_run_full_pipeline__mutmut_17': x_run_full_pipeline__mutmut_17, 
    'x_run_full_pipeline__mutmut_18': x_run_full_pipeline__mutmut_18, 
    'x_run_full_pipeline__mutmut_19': x_run_full_pipeline__mutmut_19, 
    'x_run_full_pipeline__mutmut_20': x_run_full_pipeline__mutmut_20, 
    'x_run_full_pipeline__mutmut_21': x_run_full_pipeline__mutmut_21, 
    'x_run_full_pipeline__mutmut_22': x_run_full_pipeline__mutmut_22, 
    'x_run_full_pipeline__mutmut_23': x_run_full_pipeline__mutmut_23, 
    'x_run_full_pipeline__mutmut_24': x_run_full_pipeline__mutmut_24, 
    'x_run_full_pipeline__mutmut_25': x_run_full_pipeline__mutmut_25, 
    'x_run_full_pipeline__mutmut_26': x_run_full_pipeline__mutmut_26, 
    'x_run_full_pipeline__mutmut_27': x_run_full_pipeline__mutmut_27, 
    'x_run_full_pipeline__mutmut_28': x_run_full_pipeline__mutmut_28, 
    'x_run_full_pipeline__mutmut_29': x_run_full_pipeline__mutmut_29, 
    'x_run_full_pipeline__mutmut_30': x_run_full_pipeline__mutmut_30, 
    'x_run_full_pipeline__mutmut_31': x_run_full_pipeline__mutmut_31, 
    'x_run_full_pipeline__mutmut_32': x_run_full_pipeline__mutmut_32, 
    'x_run_full_pipeline__mutmut_33': x_run_full_pipeline__mutmut_33, 
    'x_run_full_pipeline__mutmut_34': x_run_full_pipeline__mutmut_34, 
    'x_run_full_pipeline__mutmut_35': x_run_full_pipeline__mutmut_35, 
    'x_run_full_pipeline__mutmut_36': x_run_full_pipeline__mutmut_36, 
    'x_run_full_pipeline__mutmut_37': x_run_full_pipeline__mutmut_37, 
    'x_run_full_pipeline__mutmut_38': x_run_full_pipeline__mutmut_38, 
    'x_run_full_pipeline__mutmut_39': x_run_full_pipeline__mutmut_39, 
    'x_run_full_pipeline__mutmut_40': x_run_full_pipeline__mutmut_40, 
    'x_run_full_pipeline__mutmut_41': x_run_full_pipeline__mutmut_41, 
    'x_run_full_pipeline__mutmut_42': x_run_full_pipeline__mutmut_42, 
    'x_run_full_pipeline__mutmut_43': x_run_full_pipeline__mutmut_43, 
    'x_run_full_pipeline__mutmut_44': x_run_full_pipeline__mutmut_44, 
    'x_run_full_pipeline__mutmut_45': x_run_full_pipeline__mutmut_45, 
    'x_run_full_pipeline__mutmut_46': x_run_full_pipeline__mutmut_46, 
    'x_run_full_pipeline__mutmut_47': x_run_full_pipeline__mutmut_47, 
    'x_run_full_pipeline__mutmut_48': x_run_full_pipeline__mutmut_48, 
    'x_run_full_pipeline__mutmut_49': x_run_full_pipeline__mutmut_49, 
    'x_run_full_pipeline__mutmut_50': x_run_full_pipeline__mutmut_50, 
    'x_run_full_pipeline__mutmut_51': x_run_full_pipeline__mutmut_51, 
    'x_run_full_pipeline__mutmut_52': x_run_full_pipeline__mutmut_52, 
    'x_run_full_pipeline__mutmut_53': x_run_full_pipeline__mutmut_53, 
    'x_run_full_pipeline__mutmut_54': x_run_full_pipeline__mutmut_54, 
    'x_run_full_pipeline__mutmut_55': x_run_full_pipeline__mutmut_55, 
    'x_run_full_pipeline__mutmut_56': x_run_full_pipeline__mutmut_56, 
    'x_run_full_pipeline__mutmut_57': x_run_full_pipeline__mutmut_57, 
    'x_run_full_pipeline__mutmut_58': x_run_full_pipeline__mutmut_58, 
    'x_run_full_pipeline__mutmut_59': x_run_full_pipeline__mutmut_59, 
    'x_run_full_pipeline__mutmut_60': x_run_full_pipeline__mutmut_60, 
    'x_run_full_pipeline__mutmut_61': x_run_full_pipeline__mutmut_61, 
    'x_run_full_pipeline__mutmut_62': x_run_full_pipeline__mutmut_62, 
    'x_run_full_pipeline__mutmut_63': x_run_full_pipeline__mutmut_63, 
    'x_run_full_pipeline__mutmut_64': x_run_full_pipeline__mutmut_64, 
    'x_run_full_pipeline__mutmut_65': x_run_full_pipeline__mutmut_65, 
    'x_run_full_pipeline__mutmut_66': x_run_full_pipeline__mutmut_66, 
    'x_run_full_pipeline__mutmut_67': x_run_full_pipeline__mutmut_67, 
    'x_run_full_pipeline__mutmut_68': x_run_full_pipeline__mutmut_68, 
    'x_run_full_pipeline__mutmut_69': x_run_full_pipeline__mutmut_69, 
    'x_run_full_pipeline__mutmut_70': x_run_full_pipeline__mutmut_70, 
    'x_run_full_pipeline__mutmut_71': x_run_full_pipeline__mutmut_71, 
    'x_run_full_pipeline__mutmut_72': x_run_full_pipeline__mutmut_72, 
    'x_run_full_pipeline__mutmut_73': x_run_full_pipeline__mutmut_73, 
    'x_run_full_pipeline__mutmut_74': x_run_full_pipeline__mutmut_74, 
    'x_run_full_pipeline__mutmut_75': x_run_full_pipeline__mutmut_75, 
    'x_run_full_pipeline__mutmut_76': x_run_full_pipeline__mutmut_76, 
    'x_run_full_pipeline__mutmut_77': x_run_full_pipeline__mutmut_77, 
    'x_run_full_pipeline__mutmut_78': x_run_full_pipeline__mutmut_78, 
    'x_run_full_pipeline__mutmut_79': x_run_full_pipeline__mutmut_79, 
    'x_run_full_pipeline__mutmut_80': x_run_full_pipeline__mutmut_80, 
    'x_run_full_pipeline__mutmut_81': x_run_full_pipeline__mutmut_81, 
    'x_run_full_pipeline__mutmut_82': x_run_full_pipeline__mutmut_82, 
    'x_run_full_pipeline__mutmut_83': x_run_full_pipeline__mutmut_83, 
    'x_run_full_pipeline__mutmut_84': x_run_full_pipeline__mutmut_84, 
    'x_run_full_pipeline__mutmut_85': x_run_full_pipeline__mutmut_85, 
    'x_run_full_pipeline__mutmut_86': x_run_full_pipeline__mutmut_86, 
    'x_run_full_pipeline__mutmut_87': x_run_full_pipeline__mutmut_87, 
    'x_run_full_pipeline__mutmut_88': x_run_full_pipeline__mutmut_88, 
    'x_run_full_pipeline__mutmut_89': x_run_full_pipeline__mutmut_89, 
    'x_run_full_pipeline__mutmut_90': x_run_full_pipeline__mutmut_90, 
    'x_run_full_pipeline__mutmut_91': x_run_full_pipeline__mutmut_91, 
    'x_run_full_pipeline__mutmut_92': x_run_full_pipeline__mutmut_92, 
    'x_run_full_pipeline__mutmut_93': x_run_full_pipeline__mutmut_93, 
    'x_run_full_pipeline__mutmut_94': x_run_full_pipeline__mutmut_94, 
    'x_run_full_pipeline__mutmut_95': x_run_full_pipeline__mutmut_95, 
    'x_run_full_pipeline__mutmut_96': x_run_full_pipeline__mutmut_96, 
    'x_run_full_pipeline__mutmut_97': x_run_full_pipeline__mutmut_97, 
    'x_run_full_pipeline__mutmut_98': x_run_full_pipeline__mutmut_98, 
    'x_run_full_pipeline__mutmut_99': x_run_full_pipeline__mutmut_99, 
    'x_run_full_pipeline__mutmut_100': x_run_full_pipeline__mutmut_100, 
    'x_run_full_pipeline__mutmut_101': x_run_full_pipeline__mutmut_101, 
    'x_run_full_pipeline__mutmut_102': x_run_full_pipeline__mutmut_102, 
    'x_run_full_pipeline__mutmut_103': x_run_full_pipeline__mutmut_103, 
    'x_run_full_pipeline__mutmut_104': x_run_full_pipeline__mutmut_104, 
    'x_run_full_pipeline__mutmut_105': x_run_full_pipeline__mutmut_105, 
    'x_run_full_pipeline__mutmut_106': x_run_full_pipeline__mutmut_106, 
    'x_run_full_pipeline__mutmut_107': x_run_full_pipeline__mutmut_107, 
    'x_run_full_pipeline__mutmut_108': x_run_full_pipeline__mutmut_108, 
    'x_run_full_pipeline__mutmut_109': x_run_full_pipeline__mutmut_109, 
    'x_run_full_pipeline__mutmut_110': x_run_full_pipeline__mutmut_110, 
    'x_run_full_pipeline__mutmut_111': x_run_full_pipeline__mutmut_111
}
x_run_full_pipeline__mutmut_orig.__name__ = 'x_run_full_pipeline'
