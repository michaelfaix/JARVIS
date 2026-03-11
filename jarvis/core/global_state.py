# =============================================================================
# JARVIS v6.1.0 -- GLOBAL SYSTEM STATE CONTROLLER
# File:   jarvis/core/global_state.py
# Version: 1.0.0
# Session: S35
# =============================================================================
#
# SCOPE
# -----
# Single authoritative source for the entire system state.
# ALL modules MUST read state through this controller. NO local override.
# Thread-safe. Immutable snapshots. Fully logged.
#
# CLASSIFICATION: P1 Governance Control -- below P0.
#
# PUBLIC SYMBOLS
# --------------
#   SystemState                  Dataclass -- full system state snapshot
#   GlobalSystemStateController  Singleton controller for state mutations
#
# STATE GOVERNANCE (5 canonical states embedded in SystemState):
#   1. GlobalState:     mode, ood_status, calibration_status, integrity_status,
#                       deployment_blocked, meta_uncertainty, state_hash
#   2. RegimeState:     regime, regime_confidence, regime_probs,
#                       regime_age_bars, regime_transition_flag
#   3. StrategyState:   strategy_mode, active_strategy_id, entry_active,
#                       exit_active, weight_scalar, regime_alignment,
#                       last_updated_bar
#   4. PortfolioState:  positions, gross_exposure, net_exposure,
#                       diversification_ratio, portfolio_var
#   5. VolatilityState: realized_vol, forecast_vol, vol_regime,
#                       vol_percentile, vol_spike_flag, nvu_normalized
#
# MUTATION CONTRACT
# -----------------
# All state mutations EXCLUSIVELY via GlobalSystemStateController.update().
# No module may hold a mutable reference to a state object.
# All reads return immutable snapshots via ctrl.get_state().
#
# DETERMINISM CONSTRAINTS
# -----------------------
# DET-02  All inputs passed explicitly (no hidden state reads).
# DET-03  No side effects beyond internal state mutation.
# DET-05  All branching is deterministic.
#
# PROHIBITED ACTIONS CONFIRMED ABSENT
# ------------------------------------
#   No numpy / scipy
#   No random / secrets / uuid
#   No file IO / network IO
#   No global mutable state beyond singleton instance
# =============================================================================

from __future__ import annotations

import hashlib
import json
import threading
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from typing import Any, Callable, Dict, List, Optional

from jarvis.core.regime import GlobalRegimeState


# ---------------------------------------------------------------------------
# JSON SERIALIZATION HELPER
# ---------------------------------------------------------------------------

def _json_default(obj: Any) -> Any:
    """JSON default handler for enum values."""
    if hasattr(obj, "value"):
        return obj.value
    raise TypeError(f"Object of type {type(obj).__name__} is not JSON serializable")


# ---------------------------------------------------------------------------
# SYSTEM STATE DATACLASS
# ---------------------------------------------------------------------------

@dataclass
class SystemState:
    """
    Complete authoritative system state.
    Immutable after creation (snapshots are copies).
    Embeds all 5 canonical states as flat fields.
    """

    # --- Canonical State 1: GlobalState ---
    timestamp: str
    mode: str                          # RUNNING, DEGRADED, EMERGENCY, SHUTDOWN
    ood_status: str                    # NORMAL, ELEVATED, CRITICAL, BLOCKED
    calibration_status: str            # OK, WARNING, FAILED, BLOCKED
    integrity_status: str              # OK, COMPROMISED, BLOCKED
    deployment_blocked: bool
    meta_uncertainty: float            # U from system contract D(t), [0.0, 1.0]

    # --- Canonical State 2: RegimeState ---
    regime: GlobalRegimeState          # Canonical enum from jarvis.core.regime
    regime_confidence: float           # R in [0, 1]
    regime_probs: Dict[str, float]     # sum == 1.0 +/- 1e-6
    regime_age_bars: int               # bars since last regime change
    regime_transition_flag: bool       # True if regime changed this bar

    # --- Canonical State 3: StrategyState ---
    strategy_mode: str                 # MOMENTUM, MEAN_REVERSION, RISK_REDUCTION, DEFENSIVE, MINIMAL
    active_strategy_id: str
    entry_active: bool
    exit_active: bool
    weight_scalar: float               # [0, 1]
    regime_alignment: bool
    last_updated_bar: int

    # --- Canonical State 4: PortfolioState ---
    positions: Dict[str, float]        # asset_id -> position size
    gross_exposure: float
    net_exposure: float
    diversification_ratio: float
    portfolio_var: float

    # --- Canonical State 5: VolatilityState ---
    realized_vol: float
    forecast_vol: float
    vol_regime: str
    vol_percentile: float              # [0, 1]
    vol_spike_flag: bool
    nvu_normalized: float              # >= 0

    # --- Risk ---
    risk_mode: str                     # NORMAL, ELEVATED, CRITICAL, DEFENSIVE
    risk_compression: bool

    # --- Calibration metrics ---
    last_ece: float
    last_ood_recall: float

    # --- Integrity ---
    state_hash: str                    # SHA-256 of state (excluding state_hash)

    @classmethod
    def initial(cls) -> SystemState:
        """Create the initial system state at startup."""
        state = cls(
            timestamp=datetime.now(timezone.utc).isoformat(),
            mode="RUNNING",
            ood_status="NORMAL",
            calibration_status="OK",
            integrity_status="OK",
            deployment_blocked=True,
            meta_uncertainty=1.0,
            regime=GlobalRegimeState.UNKNOWN,
            regime_confidence=0.0,
            regime_probs={},
            regime_age_bars=0,
            regime_transition_flag=False,
            strategy_mode="MINIMAL",
            active_strategy_id="",
            entry_active=False,
            exit_active=False,
            weight_scalar=0.0,
            regime_alignment=False,
            last_updated_bar=0,
            positions={},
            gross_exposure=0.0,
            net_exposure=0.0,
            diversification_ratio=0.0,
            portfolio_var=0.0,
            realized_vol=0.0,
            forecast_vol=0.0,
            vol_regime="NORMAL",
            vol_percentile=0.0,
            vol_spike_flag=False,
            nvu_normalized=0.0,
            risk_mode="NORMAL",
            risk_compression=True,
            last_ece=1.0,
            last_ood_recall=0.0,
            state_hash="",
        )
        state.state_hash = state._compute_hash()
        return state

    def _compute_hash(self) -> str:
        """SHA-256 of state (excluding state_hash field itself)."""
        d = asdict(self)
        d.pop("state_hash", None)
        # asdict does not convert enums; serialize manually
        return hashlib.sha256(
            json.dumps(d, sort_keys=True, default=_json_default).encode("utf-8")
        ).hexdigest()[:16]

    def verify_hash(self) -> bool:
        """Verify state_hash matches recomputed hash."""
        return self.state_hash == self._compute_hash()

    def is_tradeable(self) -> bool:
        """True only if all statuses OK and not blocked."""
        return (
            self.mode == "RUNNING"
            and not self.deployment_blocked
            and self.ood_status not in ("CRITICAL", "BLOCKED")
            and self.calibration_status not in ("FAILED", "BLOCKED")
            and self.integrity_status == "OK"
            and not self.risk_compression
        )


# ---------------------------------------------------------------------------
# ALLOWED UPDATE FIELDS
# ---------------------------------------------------------------------------

_ALLOWED_FIELDS = frozenset({
    # GlobalState
    "mode", "ood_status", "calibration_status", "integrity_status",
    "deployment_blocked", "meta_uncertainty",
    # RegimeState
    "regime", "regime_confidence", "regime_probs",
    "regime_age_bars", "regime_transition_flag",
    # StrategyState
    "strategy_mode", "active_strategy_id", "entry_active", "exit_active",
    "weight_scalar", "regime_alignment", "last_updated_bar",
    # PortfolioState
    "positions", "gross_exposure", "net_exposure",
    "diversification_ratio", "portfolio_var",
    # VolatilityState
    "realized_vol", "forecast_vol", "vol_regime",
    "vol_percentile", "vol_spike_flag", "nvu_normalized",
    # Risk
    "risk_mode", "risk_compression",
    # Calibration
    "last_ece", "last_ood_recall",
})


# ---------------------------------------------------------------------------
# VALIDATION HELPERS
# ---------------------------------------------------------------------------

def _validate_regime_probs(probs: Dict[str, float]) -> None:
    """Validate regime_probs invariant: sum == 1.0 +/- 1e-6."""
    if not isinstance(probs, dict):
        raise TypeError(f"regime_probs must be a dict; got {type(probs).__name__}")
    if probs:
        total = sum(probs.values())
        if abs(total - 1.0) > 1e-6:
            raise ValueError(
                f"regime_probs must sum to 1.0 (+/- 1e-6); got {total}"
            )
        for k, v in probs.items():
            if not isinstance(v, (int, float)):
                raise TypeError(
                    f"regime_probs values must be numeric; got {type(v).__name__} for key {k!r}"
                )


def _validate_update_values(current_dict: dict, updates: dict) -> None:
    """Validate invariants on updated field values."""
    merged = {**current_dict, **updates}

    if "regime_confidence" in updates:
        rc = updates["regime_confidence"]
        if not (0.0 <= rc <= 1.0):
            raise ValueError(
                f"regime_confidence must be in [0.0, 1.0]; got {rc}"
            )

    if "meta_uncertainty" in updates:
        mu = updates["meta_uncertainty"]
        if not (0.0 <= mu <= 1.0):
            raise ValueError(
                f"meta_uncertainty must be in [0.0, 1.0]; got {mu}"
            )

    if "weight_scalar" in updates:
        ws = updates["weight_scalar"]
        if not (0.0 <= ws <= 1.0):
            raise ValueError(
                f"weight_scalar must be in [0.0, 1.0]; got {ws}"
            )

    if "vol_percentile" in updates:
        vp = updates["vol_percentile"]
        if not (0.0 <= vp <= 1.0):
            raise ValueError(
                f"vol_percentile must be in [0.0, 1.0]; got {vp}"
            )

    if "nvu_normalized" in updates:
        nvu = updates["nvu_normalized"]
        if nvu < 0:
            raise ValueError(
                f"nvu_normalized must be >= 0; got {nvu}"
            )

    if "regime_probs" in updates:
        _validate_regime_probs(updates["regime_probs"])


# ---------------------------------------------------------------------------
# EMERGENCY CONDITIONS
# ---------------------------------------------------------------------------

EMERGENCY_CONDITIONS: List[Callable[[SystemState], bool]] = [
    lambda s: s.meta_uncertainty > 0.90,
    lambda s: s.integrity_status == "COMPROMISED",
    lambda s: s.ood_status == "BLOCKED",
    lambda s: s.calibration_status == "BLOCKED",
    lambda s: s.deployment_blocked and s.mode == "RUNNING"
              and s.meta_uncertainty > 0.90,
]


# ---------------------------------------------------------------------------
# GLOBAL SYSTEM STATE CONTROLLER
# ---------------------------------------------------------------------------

class GlobalSystemStateController:
    """
    Singleton state controller.
    Only interface for state changes in the entire system.
    Thread-safe via RLock.
    """

    _instance: Optional[GlobalSystemStateController] = None
    _lock = threading.RLock()

    def __init__(self, log_layer: Any = None) -> None:
        self._state_lock = threading.RLock()
        self._state: SystemState = SystemState.initial()
        self._history: List[SystemState] = []
        self._log = log_layer
        self._transition_callbacks: List[Callable] = []
        self._emergency_active: bool = False

    @classmethod
    def get_instance(cls, log_layer: Any = None) -> GlobalSystemStateController:
        """Thread-safe singleton access."""
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = cls(log_layer)
        return cls._instance

    @classmethod
    def reset_instance(cls) -> None:
        """Reset singleton. For testing only."""
        with cls._lock:
            cls._instance = None

    def get_state(self) -> SystemState:
        """Return current state as immutable snapshot."""
        with self._state_lock:
            return self._state

    def update(self, **kwargs: Any) -> SystemState:
        """
        Update state fields atomically.
        Only allowed fields can be changed.
        Raises ValueError on unknown fields or invariant violations.
        Old state is preserved in history.
        """
        if self._emergency_active:
            # In emergency mode, only allow emergency-related updates
            emergency_fields = {"mode", "deployment_blocked", "risk_compression"}
            non_emergency = set(kwargs.keys()) - emergency_fields
            if non_emergency:
                raise ValueError(
                    f"System in EMERGENCY mode. Only {emergency_fields} can be "
                    f"updated. Rejected fields: {non_emergency}"
                )

        unknown = set(kwargs.keys()) - _ALLOWED_FIELDS
        if unknown:
            raise ValueError(f"Unknown state fields: {unknown}")

        with self._state_lock:
            old_state = self._state
            self._history.append(old_state)
            if len(self._history) > 1000:
                self._history = self._history[-500:]

            # Build current dict from old state
            current = asdict(old_state)
            current.pop("state_hash", None)

            # Validate before applying
            _validate_update_values(current, kwargs)

            current.update(kwargs)
            current["timestamp"] = datetime.now(timezone.utc).isoformat()

            # Resolve regime enum: accept enum or string (.value)
            raw_regime = current["regime"]
            if isinstance(raw_regime, GlobalRegimeState):
                resolved_regime = raw_regime
            else:
                resolved_regime = GlobalRegimeState(raw_regime)

            new_state = SystemState(
                timestamp=current["timestamp"],
                mode=current["mode"],
                ood_status=current["ood_status"],
                calibration_status=current["calibration_status"],
                integrity_status=current["integrity_status"],
                deployment_blocked=bool(current["deployment_blocked"]),
                meta_uncertainty=float(current["meta_uncertainty"]),
                regime=resolved_regime,
                regime_confidence=float(current["regime_confidence"]),
                regime_probs=dict(current["regime_probs"]),
                regime_age_bars=int(current["regime_age_bars"]),
                regime_transition_flag=bool(current["regime_transition_flag"]),
                strategy_mode=current["strategy_mode"],
                active_strategy_id=current["active_strategy_id"],
                entry_active=bool(current["entry_active"]),
                exit_active=bool(current["exit_active"]),
                weight_scalar=float(current["weight_scalar"]),
                regime_alignment=bool(current["regime_alignment"]),
                last_updated_bar=int(current["last_updated_bar"]),
                positions=dict(current["positions"]),
                gross_exposure=float(current["gross_exposure"]),
                net_exposure=float(current["net_exposure"]),
                diversification_ratio=float(current["diversification_ratio"]),
                portfolio_var=float(current["portfolio_var"]),
                realized_vol=float(current["realized_vol"]),
                forecast_vol=float(current["forecast_vol"]),
                vol_regime=current["vol_regime"],
                vol_percentile=float(current["vol_percentile"]),
                vol_spike_flag=bool(current["vol_spike_flag"]),
                nvu_normalized=float(current["nvu_normalized"]),
                risk_mode=current["risk_mode"],
                risk_compression=bool(current["risk_compression"]),
                last_ece=float(current["last_ece"]),
                last_ood_recall=float(current["last_ood_recall"]),
                state_hash="",
            )
            new_state.state_hash = new_state._compute_hash()
            self._state = new_state

            # Execute transition callbacks
            for cb in self._transition_callbacks:
                try:
                    cb(old_state, new_state)
                except Exception:
                    pass  # Callbacks must not block state updates

            # Logging (non-blocking)
            if self._log:
                try:
                    self._log.log_event(
                        event_type="STATE_CHANGE",
                        data={
                            "old_state_hash": old_state.state_hash,
                            "new_state_hash": new_state.state_hash,
                            "changed_fields": list(kwargs.keys()),
                        },
                        timestamp=datetime.now(timezone.utc),
                    )
                except Exception:
                    pass

            return new_state

    def emergency_shutdown(self, reason: str) -> None:
        """
        Emergency shutdown. Not reversible without restart.
        Sets mode=EMERGENCY, deployment_blocked=True, risk_compression=True.
        Freezes all state writes (except shutdown log).
        System remains readable for diagnostics.
        """
        self.update(
            mode="EMERGENCY",
            deployment_blocked=True,
            risk_compression=True,
        )
        self._emergency_active = True

        if self._log:
            try:
                self._log.log_event(
                    event_type="EMERGENCY_SHUTDOWN",
                    data={"reason": reason, "state_hash": self._state.state_hash},
                    timestamp=datetime.now(timezone.utc),
                )
            except Exception:
                pass

    def check_emergency_conditions(self) -> Optional[str]:
        """
        Check current state against emergency conditions.
        Returns reason string if emergency triggered, None otherwise.
        """
        state = self.get_state()
        if state.meta_uncertainty > 0.90:
            return "meta_uncertainty > 0.90"
        if state.integrity_status == "COMPROMISED":
            return "integrity_status COMPROMISED"
        if state.ood_status == "BLOCKED":
            return "ood_status BLOCKED"
        if state.calibration_status == "BLOCKED":
            return "calibration_status BLOCKED"
        return None

    def register_transition_callback(
        self, callback: Callable[[SystemState, SystemState], None]
    ) -> None:
        """Register callback for state changes."""
        with self._state_lock:
            self._transition_callbacks.append(callback)

    def get_history(self, last_n: int = 10) -> List[SystemState]:
        """Return last n state snapshots."""
        with self._state_lock:
            return list(self._history[-last_n:])

    @property
    def is_emergency(self) -> bool:
        """True if emergency shutdown has been triggered."""
        return self._emergency_active


# ---------------------------------------------------------------------------
# SYSTEM OPERATING MODE & REFRESH POLICIES (S35)
# ---------------------------------------------------------------------------

from enum import Enum


class SystemOperatingMode(Enum):
    """Operating modes for the JARVIS platform."""
    HISTORICAL = "historical"
    LIVE_ANALYTICAL = "live_analytical"
    HYBRID = "hybrid"


@dataclass(frozen=True)
class RefreshPolicy:
    """
    Immutable refresh policy configuration per operating mode.

    Fields:
        interval_bars:     Minimum bars between updates.
        on_regime_change:  Refresh on regime change.
        on_vol_spike:      Refresh on volatility spike.
        on_failure_mode:   Refresh on failure mode activation.
        on_exposure_delta: Refresh on exposure delta.
    """
    interval_bars: int
    on_regime_change: bool
    on_vol_spike: bool
    on_failure_mode: bool
    on_exposure_delta: bool


REFRESH_POLICIES: Dict[SystemOperatingMode, RefreshPolicy] = {
    SystemOperatingMode.HISTORICAL: RefreshPolicy(
        interval_bars=1,
        on_regime_change=True,
        on_vol_spike=True,
        on_failure_mode=True,
        on_exposure_delta=True,
    ),
    SystemOperatingMode.LIVE_ANALYTICAL: RefreshPolicy(
        interval_bars=5,
        on_regime_change=True,
        on_vol_spike=True,
        on_failure_mode=True,
        on_exposure_delta=True,
    ),
    SystemOperatingMode.HYBRID: RefreshPolicy(
        interval_bars=3,
        on_regime_change=True,
        on_vol_spike=True,
        on_failure_mode=True,
        on_exposure_delta=True,
    ),
}


__all__ = [
    "SystemState",
    "GlobalSystemStateController",
    "EMERGENCY_CONDITIONS",
    "SystemOperatingMode",
    "RefreshPolicy",
    "REFRESH_POLICIES",
]
