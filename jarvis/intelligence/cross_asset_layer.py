# =============================================================================
# JARVIS v6.1.0 -- CROSS-ASSET CORRELATION LAYER
# File:   jarvis/intelligence/cross_asset_layer.py
# Version: 1.0.0
# Session: S22
# =============================================================================
#
# SCOPE
# -----
# Misst Korrelation des Ziel-Assets zu anderen Assets.
# Hohe Korrelation zu Risiko-Assets + Markt faellt = erhoehtes Risiko.
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

from jarvis.core.regime import CorrelationRegimeState


# ---------------------------------------------------------------------------
# DATA CLASSES
# ---------------------------------------------------------------------------

@dataclass
class CrossAssetSignal:
    """Output des Cross-Asset Correlation Layers."""
    correlations:       Dict[str, float]         # Asset-Name -> Korrelation [-1,1]
    risk_on_exposure:   float                    # Exposure zu Risk-On Regime [0,1]
    correlation_regime: CorrelationRegimeState    # NORMAL, COUPLED, BREAKDOWN
    systemic_risk:      float                    # Systemisches Risiko [0,1]


# ---------------------------------------------------------------------------
# CROSS-ASSET LAYER
# ---------------------------------------------------------------------------

class CrossAssetLayer:
    """
    Layer 4: Cross-Asset Correlation Analysis.
    Erkennt systemische Risikoverbreitung zwischen Asset-Klassen.
    """

    CRISIS_CORRELATION_THRESHOLD = 0.85

    def compute(
        self,
        target_returns: List[float],
        reference_assets: Dict[str, List[float]],
        window: int = 60,
    ) -> CrossAssetSignal:
        """
        Berechnet rollierende Korrelationen zu Referenz-Assets.

        Args:
            target_returns:    Returns des Ziel-Assets (min `window` Elemente).
            reference_assets:  Dict[name -> returns] der Referenz-Assets.
            window:            Lookback-Fenster fuer Korrelationsberechnung.

        Returns:
            CrossAssetSignal mit Korrelationen, Risk-On Exposure,
            Correlation Regime und systemischem Risiko.

        Raises:
            ValueError: Zu wenig Target-Returns oder NaN/Inf enthalten.
        """
        if len(target_returns) < window:
            raise ValueError(f"Mindestens {window} Returns erforderlich")

        target_arr = np.array(target_returns[-window:])
        if not np.all(np.isfinite(target_arr)):
            raise ValueError("Target returns enthalten NaN/Inf")

        correlations: Dict[str, float] = {}
        for name, ref_returns in reference_assets.items():
            ref_arr = np.array(ref_returns[-window:])
            if len(ref_arr) < window or not np.all(np.isfinite(ref_arr)):
                correlations[name] = 0.0
                continue
            cov_mat = np.cov(target_arr, ref_arr)
            denom   = float(np.sqrt(max(cov_mat[0, 0] * cov_mat[1, 1], 1e-12)))
            corr    = float(cov_mat[0, 1] / denom)
            correlations[name] = float(np.clip(corr, -1.0, 1.0))

        # Risk-On Exposure: Mittelwert der Korrelationen zu Risk-Assets
        if correlations:
            risk_on = float(np.mean(list(correlations.values())))
            risk_on = float(np.clip((risk_on + 1.0) / 2.0, 0.0, 1.0))
        else:
            risk_on = 0.5

        # Correlation Regime (mapped to canonical CorrelationRegimeState)
        max_corr = max(abs(v) for v in correlations.values()) if correlations else 0.0
        if max_corr > self.CRISIS_CORRELATION_THRESHOLD:
            corr_regime = CorrelationRegimeState.BREAKDOWN
        elif max_corr > 0.6:
            corr_regime = CorrelationRegimeState.COUPLED
        else:
            corr_regime = CorrelationRegimeState.NORMAL

        # Systemisches Risiko
        systemic = float(max_corr * risk_on)
        systemic = float(np.clip(systemic, 0.0, 1.0))

        return CrossAssetSignal(
            correlations=correlations,
            risk_on_exposure=risk_on,
            correlation_regime=corr_regime,
            systemic_risk=systemic,
        )


__all__ = [
    "CrossAssetSignal",
    "CrossAssetLayer",
]
