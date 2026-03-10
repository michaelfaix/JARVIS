# =============================================================================
# JARVIS v6.1.0 -- MACRO SENSITIVITY LAYER
# File:   jarvis/intelligence/macro_layer.py
# Version: 1.0.0
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
#   No logging module
#   No datetime.now() / time.time()
#   No random / secrets / uuid
#   No file IO / network IO
#   No global mutable state
# =============================================================================

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List

import numpy as np

from jarvis.core.regime import MacroRegimeState


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

        target = np.array(asset_returns[-window:])
        if not np.all(np.isfinite(target)):
            raise ValueError("Asset returns enthalten NaN/Inf")

        betas: Dict[str, float] = {}
        for factor_name, f_returns in factor_returns.items():
            f_arr = np.array(f_returns[-window:])
            if len(f_arr) < window or not np.all(np.isfinite(f_arr)):
                betas[factor_name] = 0.0
                continue
            # Einfache OLS-Beta: Cov(y,x)/Var(x)
            cov    = float(np.cov(target, f_arr)[0, 1])
            var_x  = float(np.var(f_arr))
            beta   = cov / max(var_x, 1e-12)
            betas[factor_name] = float(np.clip(beta, -5.0, 5.0))

        # Makro-Risiko-Score: L2-Norm der Betas normalisiert
        beta_arr = np.array(list(betas.values()))
        macro_score = float(np.clip(
            np.sqrt(np.sum(beta_arr ** 2)) / max(len(betas), 1), 0.0, 1.0
        ))

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
