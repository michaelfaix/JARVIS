# =============================================================================
# JARVIS v6.1.0 -- MACRO SENSITIVITY LAYER
# File:   jarvis/intelligence/macro_layer.py
# Version: 1.1.0
# Session: S23
# =============================================================================
#
# SCOPE
# -----
# Bewertet Sensitivitaet des Assets zu makrooekonomischen Faktoren.
# Zins, Inflation, Waehrung -> Impact auf Asset-Klasse.
#
# CLASSIFICATION: P0 — ANALYSIS AND STRATEGY RESEARCH TOOL.
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
#   No numpy / scipy
#   No logging module
#   No datetime.now() / time.time()
#   No random / secrets / uuid
#   No file IO / network IO
#   No global mutable state
# =============================================================================

from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Dict, List

from jarvis.core.regime import MacroRegimeState


# ---------------------------------------------------------------------------
# HELPERS (stdlib-only replacements for numpy operations)
# ---------------------------------------------------------------------------

def _mean(values: List[float]) -> float:
    return sum(values) / len(values)


def _var(values: List[float]) -> float:
    """Population variance (ddof=0), matching numpy.var default."""
    n = len(values)
    if n < 1:
        return 0.0
    m = _mean(values)
    return sum((x - m) ** 2 for x in values) / n


def _cov(xs: List[float], ys: List[float]) -> float:
    """Sample covariance (ddof=1), matching numpy.cov default."""
    n = len(xs)
    if n < 2:
        return 0.0
    mx = _mean(xs)
    my = _mean(ys)
    return sum((x - mx) * (y - my) for x, y in zip(xs, ys)) / (n - 1)


def _clip(value: float, lo: float, hi: float) -> float:
    if value < lo:
        return lo
    if value > hi:
        return hi
    return value


def _all_finite(values: List[float]) -> bool:
    return all(math.isfinite(x) for x in values)


# ---------------------------------------------------------------------------
# DATA CLASSES
# ---------------------------------------------------------------------------

@dataclass
class MacroSensitivityResult:
    """Output des Macro Sensitivity Layers."""
    factor_sensitivities: Dict[str, float]  # Faktor -> Beta
    macro_risk_score:     float             # Gesamt-Makro-Risiko [0,1]
    dominant_factor:      str               # Dominantester Makro-Faktor
    macro_regime:         MacroRegimeState   # BENIGN, UNCERTAIN, ADVERSE


# ---------------------------------------------------------------------------
# MACRO SENSITIVITY LAYER
# ---------------------------------------------------------------------------

class MacroSensitivityLayer:
    """
    Layer 5: Macro Sensitivity Assessment.
    Bewertet wie stark das Asset auf Makro-Faktoren reagiert.
    """

    MACRO_FACTORS = ["interest_rate", "inflation", "usd_strength",
                     "credit_spread", "vix"]

    def compute(
        self,
        asset_returns: List[float],
        factor_returns: Dict[str, List[float]],
        window: int = 120,
    ) -> MacroSensitivityResult:
        """
        OLS-Regression: Asset gegen Makro-Faktoren.

        Args:
            asset_returns:   Returns des Assets (min `window` Elemente).
            factor_returns:  Dict[factor_name -> returns] der Makro-Faktoren.
            window:          Lookback-Fenster fuer Regression.

        Returns:
            MacroSensitivityResult mit Betas, Risiko-Score, dominantem Faktor
            und Makro-Regime.

        Raises:
            ValueError: Zu wenig Asset-Returns oder NaN/Inf enthalten.
        """
        if len(asset_returns) < window:
            raise ValueError(f"Mindestens {window} Asset-Returns erforderlich")

        target = asset_returns[-window:]
        if not _all_finite(target):
            raise ValueError("Asset returns enthalten NaN/Inf")

        betas: Dict[str, float] = {}
        for factor_name, f_returns in factor_returns.items():
            f_slice = f_returns[-window:]
            if len(f_slice) < window or not _all_finite(f_slice):
                betas[factor_name] = 0.0
                continue
            # Einfache OLS-Beta: Cov(y,x)/Var(x)
            cov   = _cov(target, f_slice)
            var_x = _var(f_slice)
            beta  = cov / max(var_x, 1e-12)
            betas[factor_name] = _clip(beta, -5.0, 5.0)

        # Makro-Risiko-Score: L2-Norm der Betas normalisiert
        beta_values = list(betas.values())
        if beta_values:
            l2 = math.sqrt(sum(b ** 2 for b in beta_values))
            macro_score = _clip(l2 / max(len(betas), 1), 0.0, 1.0)
        else:
            macro_score = 0.0

        # Dominanter Faktor
        dominant = max(betas, key=lambda k: abs(betas[k])) if betas else "NONE"

        # Makro-Regime
        if macro_score > 0.7:
            macro_regime = MacroRegimeState.ADVERSE
        elif macro_score > 0.4:
            macro_regime = MacroRegimeState.UNCERTAIN
        else:
            macro_regime = MacroRegimeState.BENIGN

        return MacroSensitivityResult(
            factor_sensitivities=betas,
            macro_risk_score=macro_score,
            dominant_factor=dominant,
            macro_regime=macro_regime,
        )


__all__ = [
    "MacroSensitivityResult",
    "MacroSensitivityLayer",
]
