# =============================================================================
# JARVIS v6.1.0 -- MULTI-TIMEFRAME CALIBRATOR
# File:   jarvis/risk/multi_timeframe.py
# Version: 1.0.0
# Session: S18
# =============================================================================
#
# SCOPE
# -----
# Enforces complete recalibration on timeframe switches.
# No timeframe switch without full recalibration of:
#   1. Regime detection  (S05)
#   2. Risk assessment   (S17)
#   3. Confidence zones  (S16)
#   4. Timeframe-dependent threshold scaling
#
# CLASSIFICATION: P0 — ANALYSIS AND STRATEGY RESEARCH TOOL.
#
# CRITICAL REQUIREMENTS (from FAS S18):
#   R1: No timeframe switch without full recalibration
#   R2: Timeframe scaling factors are immutable (TIMEFRAME_CONFIGS)
#   R3: Every timeframe switch logged in BUILD_LOG.json
#   R4: UI must not be operable during recalibration (load-lock)
#
# DEPENDENCIES
# ------------
#   S03: Data Layer (returns data)
#   S05: Regime Detection (regime_detector.detect)
#   S16: Confidence Zone Engine (confidence_engine.compute)
#   S17: Risk Engine (risk_engine.assess)
#
# DETERMINISM CONSTRAINTS
# -----------------------
# DET-01  No stochastic operations.
# DET-02  All inputs passed explicitly.
# DET-03  No side effects beyond internal timeframe tracking.
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
from enum import Enum, unique
from typing import Any, Dict, List, Optional, Protocol

from jarvis.risk.confidence_zone_engine import ConfidenceZoneRequest


# ---------------------------------------------------------------------------
# TIMEFRAME ENUM
# ---------------------------------------------------------------------------

@unique
class Timeframe(Enum):
    """Canonical timeframe identifiers."""
    TF_5M = "5m"
    TF_15M = "15m"
    TF_1H = "1h"
    TF_4H = "4h"
    TF_1D = "1D"


# ---------------------------------------------------------------------------
# TIMEFRAME CONFIGURATION
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class TimeframeConfig:
    """Configuration per timeframe. Immutable (R2)."""
    label: str              # Display label
    bars_per_day: int       # Bars per trading day
    regime_lookback: int    # Bars for regime detection
    vol_halflife: int       # EWMA halflife in bars
    risk_scale: float       # Risk scaling factor relative to 1D


TIMEFRAME_CONFIGS: Dict[Timeframe, TimeframeConfig] = {
    Timeframe.TF_5M:  TimeframeConfig("5m",  288, 60, 20, 0.08),
    Timeframe.TF_15M: TimeframeConfig("15m",  96, 40, 20, 0.15),
    Timeframe.TF_1H:  TimeframeConfig("1h",   24, 30, 20, 0.30),
    Timeframe.TF_4H:  TimeframeConfig("4h",    6, 20, 15, 0.60),
    Timeframe.TF_1D:  TimeframeConfig("1D",    1, 20, 20, 1.00),
}


# ---------------------------------------------------------------------------
# RECALIBRATION RESULT
# ---------------------------------------------------------------------------

@dataclass
class RecalibrationResult:
    """Result of a timeframe switch recalibration."""
    timeframe: str          # TimeframeConfig.label
    regime: Any             # Regime from regime_detector
    risk: Any               # RiskOutput from risk_engine
    zone: Any               # ConfidenceZone from confidence_engine
    risk_scale: float       # Scaling factor applied
    recalibrated: bool      # Always True on success


# ---------------------------------------------------------------------------
# PROTOCOLS FOR DEPENDENCIES (duck-typed interfaces)
# ---------------------------------------------------------------------------

class _RegimeResult(Protocol):
    @property
    def regime(self) -> Any: ...

    @property
    def confidence(self) -> float: ...


class _RegimeDetector(Protocol):
    def detect(self, data: List[float]) -> _RegimeResult: ...


class _RiskEngine(Protocol):
    def assess(
        self,
        returns_history: List[float],
        current_regime: Any,
        meta_uncertainty: float,
    ) -> Any: ...


class _ConfidenceEngine(Protocol):
    def compute(self, req: ConfidenceZoneRequest) -> Any: ...


# ---------------------------------------------------------------------------
# MULTI-TIMEFRAME CALIBRATOR
# ---------------------------------------------------------------------------

class MultiTimeframeCalibrator:
    """
    Enforces complete recalibration on timeframe switch.

    Injected dependencies:
      - regime_detector:   must implement .detect(data) -> obj with .regime, .confidence
      - risk_engine:       must implement .assess(returns_history, current_regime, meta_uncertainty)
      - confidence_engine: must implement .compute(ConfidenceZoneRequest)
    """

    def __init__(
        self,
        regime_detector: Any,
        risk_engine: Any,
        confidence_engine: Any,
    ) -> None:
        self.regime_detector = regime_detector
        self.risk_engine = risk_engine
        self.confidence_engine = confidence_engine
        self._current_tf: Optional[Timeframe] = None

    @property
    def current_timeframe(self) -> Optional[Timeframe]:
        """Currently active timeframe, None if not yet set."""
        return self._current_tf

    def switch_timeframe(
        self,
        new_tf: Timeframe,
        returns_data: List[float],
        current_price: float,
        meta_uncertainty: float,
    ) -> RecalibrationResult:
        """
        Complete recalibration on timeframe switch.
        No soft-fail: raises on error.

        Args:
            new_tf:            Target timeframe.
            returns_data:      Full returns history (sliced internally by lookback).
            current_price:     Current asset price.
            meta_uncertainty:  System meta-uncertainty [0, 1].

        Returns:
            RecalibrationResult with regime, risk, zone, and scale.

        Raises:
            ValueError: Unknown timeframe or insufficient data.
        """
        if not isinstance(new_tf, Timeframe):
            raise TypeError(
                f"new_tf must be a Timeframe enum; got {type(new_tf).__name__}"
            )

        if new_tf not in TIMEFRAME_CONFIGS:
            raise ValueError(f"Unbekannter Timeframe: {new_tf}")

        cfg = TIMEFRAME_CONFIGS[new_tf]

        # Validate sufficient data for regime lookback
        if len(returns_data) < cfg.regime_lookback:
            raise ValueError(
                f"Insufficient data for {cfg.label}: need {cfg.regime_lookback} bars, "
                f"got {len(returns_data)}"
            )

        # Step 1: Regime detection with lookback-sliced data
        regime_result = self.regime_detector.detect(
            returns_data[-cfg.regime_lookback:]
        )

        # Step 2: Risk assessment on full returns
        risk_result = self.risk_engine.assess(
            returns_history=returns_data,
            current_regime=regime_result.regime,
            meta_uncertainty=meta_uncertainty,
        )

        # Step 3: Confidence zone recalibration with timeframe-scaled variance
        zone_req = ConfidenceZoneRequest(
            current_price=current_price,
            regime=regime_result.regime,
            sigma_sq=risk_result.volatility_forecast ** 2 * cfg.risk_scale ** 2,
            mu=1.0 - meta_uncertainty,
            regime_confidence=regime_result.confidence,
        )
        zone_result = self.confidence_engine.compute(zone_req)

        # Update current timeframe
        self._current_tf = new_tf

        return RecalibrationResult(
            timeframe=cfg.label,
            regime=regime_result.regime,
            risk=risk_result,
            zone=zone_result,
            risk_scale=cfg.risk_scale,
            recalibrated=True,
        )


__all__ = [
    "Timeframe",
    "TimeframeConfig",
    "TIMEFRAME_CONFIGS",
    "RecalibrationResult",
    "MultiTimeframeCalibrator",
]
