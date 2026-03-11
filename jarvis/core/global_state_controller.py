# =============================================================================
# jarvis/core/global_state_controller.py
# Authority: FAS v6.0.1 -- S35, S37 SYSTEM ADDENDUM
# ARCHITECTURE.md Section 12 (Module State Write Permission Matrix)
# =============================================================================
#
# SCOPE
# -----
# Singleton GlobalSystemStateController.  Single canonical mutation path
# for all system state.  All state changes route through ctrl.update().
# Direct field assignment on state objects is a P1-level violation.
#
# Public symbols:
#   VALID_GLOBAL_MODES            Tuple of valid GlobalState.mode values
#   VALID_OOD_STATUSES            Tuple of valid ood_status values
#   VALID_RISK_MODES              Tuple of valid risk_mode values
#   VALID_VOL_REGIMES             Tuple of valid vol_regime values
#   UPDATABLE_FIELDS              FrozenSet of all field names accepted by update()
#   MAX_HISTORY                   Maximum state history snapshots (1000)
#   GlobalState                   Frozen dataclass -- system state snapshot
#   GlobalSystemStateController   Singleton controller class
#
# CLASSIFICATION
# --------------
# P1 — Governance Control, below P0.
# Thread-safe singleton.  All reads return immutable snapshots.
# All mutations are atomic under lock.
#
# DEPENDENCIES
# ------------
#   stdlib:    dataclasses, threading, typing, copy
#   internal:  NONE
#   PROHIBITED: numpy, logging, random, file IO, network IO, datetime.now()
#
# DETERMINISM
# -----------
# DET-01  No stochastic operations.
# DET-02  All inputs passed explicitly to update().
# DET-03  No side effects beyond internal state (encapsulated).
# DET-05  No datetime.now() / time.time().
# DET-07  Same sequence of update() calls = identical state.
# =============================================================================

from __future__ import annotations

import copy
import threading
from dataclasses import dataclass, field, fields
from typing import Any, Callable, Dict, FrozenSet, List, Optional, Tuple

__all__ = [
    "VALID_GLOBAL_MODES",
    "VALID_OOD_STATUSES",
    "VALID_RISK_MODES",
    "VALID_VOL_REGIMES",
    "UPDATABLE_FIELDS",
    "MAX_HISTORY",
    "GlobalState",
    "GlobalSystemStateController",
]


# =============================================================================
# SECTION 1 -- CONSTANTS
# =============================================================================

VALID_GLOBAL_MODES: Tuple[str, ...] = (
    "RUNNING", "DEGRADED", "EMERGENCY", "SHUTDOWN",
)

VALID_OOD_STATUSES: Tuple[str, ...] = (
    "NORMAL", "ELEVATED", "CRITICAL", "BLOCKED",
)

VALID_RISK_MODES: Tuple[str, ...] = (
    "NORMAL", "ELEVATED", "CRITICAL", "DEFENSIVE",
)

VALID_VOL_REGIMES: Tuple[str, ...] = (
    "QUIET", "NORMAL", "ELEVATED", "SPIKE",
)

MAX_HISTORY: int = 1000

# All field names accepted by update().  Unknown fields raise ValueError.
UPDATABLE_FIELDS: FrozenSet[str] = frozenset({
    # GlobalState core
    "mode", "ood_status", "risk_mode", "meta_uncertainty",
    "regime", "risk_compression", "deployment_blocked",
    # RegimeState
    "regime_confidence", "regime_probs", "regime_age_bars",
    "regime_transition_flag",
    # VolatilityState
    "realized_vol", "forecast_vol", "vol_regime",
    "vol_percentile", "vol_spike_flag",
    # StrategyState
    "strategy_mode", "weight_scalar",
    # PortfolioState
    "gross_exposure", "net_exposure",
})


# =============================================================================
# SECTION 2 -- STATE DATACLASS
# =============================================================================

@dataclass(frozen=True)
class GlobalState:
    """
    Immutable system state snapshot.  All reads return instances of this class.
    No module may hold a mutable reference to state.

    Fields map to the 5 canonical states from FAS:
      GlobalState core, RegimeState, VolatilityState, StrategyState,
      PortfolioState -- flattened into a single frozen dataclass for
      simplicity and atomicity.
    """
    # -- GlobalState core --
    mode:                str   = "RUNNING"
    ood_status:          str   = "NORMAL"
    risk_mode:           str   = "NORMAL"
    meta_uncertainty:    float = 0.0
    regime:              str   = "UNKNOWN"
    risk_compression:    bool  = False
    deployment_blocked:  bool  = False

    # -- RegimeState --
    regime_confidence:       float = 0.0
    regime_probs:            Tuple[Tuple[str, float], ...] = ()
    regime_age_bars:         int   = 0
    regime_transition_flag:  bool  = False

    # -- VolatilityState --
    realized_vol:    float = 0.0
    forecast_vol:    float = 0.0
    vol_regime:      str   = "NORMAL"
    vol_percentile:  float = 0.0
    vol_spike_flag:  bool  = False

    # -- StrategyState --
    strategy_mode:  str   = "MOMENTUM"
    weight_scalar:  float = 1.0

    # -- PortfolioState --
    gross_exposure: float = 0.0
    net_exposure:   float = 0.0

    # -- Metadata --
    version:        int   = 0


# =============================================================================
# SECTION 3 -- VALIDATION
# =============================================================================

def _validate_update_fields(kwargs: Dict[str, Any]) -> None:
    """Raise ValueError if any key is not in UPDATABLE_FIELDS."""
    unknown = set(kwargs.keys()) - UPDATABLE_FIELDS
    if unknown:
        raise ValueError(
            f"Unknown fields in update(): {sorted(unknown)}. "
            f"Valid fields: {sorted(UPDATABLE_FIELDS)}"
        )


def _validate_field_values(kwargs: Dict[str, Any]) -> None:
    """Validate individual field value constraints."""
    if "mode" in kwargs:
        if kwargs["mode"] not in VALID_GLOBAL_MODES:
            raise ValueError(
                f"mode must be one of {VALID_GLOBAL_MODES}, "
                f"got {kwargs['mode']!r}"
            )

    if "ood_status" in kwargs:
        if kwargs["ood_status"] not in VALID_OOD_STATUSES:
            raise ValueError(
                f"ood_status must be one of {VALID_OOD_STATUSES}, "
                f"got {kwargs['ood_status']!r}"
            )

    if "risk_mode" in kwargs:
        if kwargs["risk_mode"] not in VALID_RISK_MODES:
            raise ValueError(
                f"risk_mode must be one of {VALID_RISK_MODES}, "
                f"got {kwargs['risk_mode']!r}"
            )

    if "vol_regime" in kwargs:
        if kwargs["vol_regime"] not in VALID_VOL_REGIMES:
            raise ValueError(
                f"vol_regime must be one of {VALID_VOL_REGIMES}, "
                f"got {kwargs['vol_regime']!r}"
            )

    if "meta_uncertainty" in kwargs:
        mu = kwargs["meta_uncertainty"]
        if not isinstance(mu, (int, float)):
            raise TypeError(
                f"meta_uncertainty must be numeric, got {type(mu).__name__}"
            )
        if not (0.0 <= mu <= 1.0):
            raise ValueError(
                f"meta_uncertainty must be in [0.0, 1.0], got {mu!r}"
            )

    if "regime_confidence" in kwargs:
        rc = kwargs["regime_confidence"]
        if not isinstance(rc, (int, float)):
            raise TypeError(
                f"regime_confidence must be numeric, got {type(rc).__name__}"
            )
        if not (0.0 <= rc <= 1.0):
            raise ValueError(
                f"regime_confidence must be in [0.0, 1.0], got {rc!r}"
            )

    if "vol_percentile" in kwargs:
        vp = kwargs["vol_percentile"]
        if not isinstance(vp, (int, float)):
            raise TypeError(
                f"vol_percentile must be numeric, got {type(vp).__name__}"
            )
        if not (0.0 <= vp <= 1.0):
            raise ValueError(
                f"vol_percentile must be in [0.0, 1.0], got {vp!r}"
            )

    if "weight_scalar" in kwargs:
        ws = kwargs["weight_scalar"]
        if not isinstance(ws, (int, float)):
            raise TypeError(
                f"weight_scalar must be numeric, got {type(ws).__name__}"
            )
        if not (0.0 <= ws <= 1.0):
            raise ValueError(
                f"weight_scalar must be in [0.0, 1.0], got {ws!r}"
            )

    if "regime_age_bars" in kwargs:
        rab = kwargs["regime_age_bars"]
        if not isinstance(rab, int) or isinstance(rab, bool):
            raise TypeError(
                f"regime_age_bars must be int, got {type(rab).__name__}"
            )
        if rab < 0:
            raise ValueError(
                f"regime_age_bars must be >= 0, got {rab}"
            )


# =============================================================================
# SECTION 4 -- CONTROLLER (SINGLETON)
# =============================================================================

class GlobalSystemStateController:
    """
    Singleton controller for all system state mutations.

    Thread-safe via RLock.  All reads return frozen GlobalState snapshots.
    All mutations go through update() which validates fields, creates a
    new frozen snapshot, archives the old state, and fires callbacks.

    Pattern:
        ctrl = GlobalSystemStateController.get_instance()
        state = ctrl.get_state()           # immutable snapshot
        ctrl.update(regime="RISK_ON", regime_confidence=0.82)

    Forbidden:
        state.regime = "RISK_ON"           # frozen dataclass -> AttributeError
        GlobalState.regime = "RISK_ON"     # class-level -> error
    """

    _instance: Optional[GlobalSystemStateController] = None
    _creation_lock: threading.Lock = threading.Lock()

    def __init__(self) -> None:
        """
        Initialize controller with default state.
        Use get_instance() for singleton access.
        """
        self._lock: threading.RLock = threading.RLock()
        self._state: GlobalState = GlobalState(version=1)
        self._history: List[GlobalState] = []
        self._callbacks: List[Callable] = []

    @classmethod
    def get_instance(cls) -> GlobalSystemStateController:
        """
        Thread-safe singleton access.

        Returns:
            The singleton GlobalSystemStateController instance.
        """
        if cls._instance is None:
            with cls._creation_lock:
                if cls._instance is None:
                    cls._instance = cls()
        return cls._instance

    @classmethod
    def _reset_singleton(cls) -> None:
        """
        Reset the singleton for testing purposes ONLY.
        Not part of the public API.
        """
        with cls._creation_lock:
            cls._instance = None

    def get_state(self) -> GlobalState:
        """
        Return an immutable snapshot of the current state.

        Thread-safe.  The returned GlobalState is frozen (dataclass frozen=True),
        so no consumer can mutate it.

        Returns:
            GlobalState snapshot.
        """
        with self._lock:
            return self._state

    def update(self, **kwargs: Any) -> GlobalState:
        """
        Atomic state mutation.  The ONLY permitted mutation path.

        Validates all field names and values, creates a new frozen GlobalState
        with the updated values, archives the old state, and fires callbacks.

        Args:
            **kwargs: Field name -> new value.  Must be in UPDATABLE_FIELDS.

        Returns:
            New GlobalState snapshot after update.

        Raises:
            ValueError: If unknown fields or invalid field values.
            TypeError:  If field value has wrong type.
        """
        if not kwargs:
            raise ValueError("update() requires at least one field")

        _validate_update_fields(kwargs)
        _validate_field_values(kwargs)

        with self._lock:
            old_state = self._state

            # Build new state dict from current + updates
            current_dict = {
                f.name: getattr(old_state, f.name)
                for f in fields(old_state)
            }
            current_dict.update(kwargs)
            current_dict["version"] = old_state.version + 1

            new_state = GlobalState(**current_dict)
            self._state = new_state

            # Archive old state (rolling window)
            self._history.append(old_state)
            if len(self._history) > MAX_HISTORY:
                self._history = self._history[-MAX_HISTORY:]

            # Fire callbacks (non-blocking: exceptions suppressed)
            callbacks = list(self._callbacks)

        for cb in callbacks:
            try:
                cb(old_state, new_state)
            except Exception:
                pass

        return new_state

    def emergency_shutdown(self, reason: str) -> GlobalState:
        """
        Irreversible emergency halt.

        Sets mode=EMERGENCY, deployment_blocked=True, risk_compression=True.
        Requires operator restart to recover.

        Args:
            reason: Human-readable reason for shutdown.

        Returns:
            New GlobalState after shutdown.

        Raises:
            TypeError: If reason is not a string.
            ValueError: If reason is empty.
        """
        if not isinstance(reason, str):
            raise TypeError(
                f"reason must be a string, got {type(reason).__name__}"
            )
        if not reason:
            raise ValueError("reason must not be empty")

        return self.update(
            mode="EMERGENCY",
            deployment_blocked=True,
            risk_compression=True,
        )

    def register_callback(self, callback: Callable) -> None:
        """
        Register a transition callback.

        Called with (old_state, new_state) on every update().
        Callbacks must not block state updates; exceptions are suppressed.

        Args:
            callback: Callable accepting (old_state, new_state).

        Raises:
            TypeError: If callback is not callable.
        """
        if not callable(callback):
            raise TypeError(
                f"callback must be callable, got {type(callback).__name__}"
            )
        with self._lock:
            self._callbacks.append(callback)

    def get_history(self, last_n: int = 10) -> List[GlobalState]:
        """
        Return the last N state snapshots from history.

        Args:
            last_n: Number of snapshots to return. Default 10.

        Returns:
            List of GlobalState snapshots (oldest first).

        Raises:
            TypeError:  If last_n is not an int.
            ValueError: If last_n < 1.
        """
        if not isinstance(last_n, int) or isinstance(last_n, bool):
            raise TypeError(
                f"last_n must be int, got {type(last_n).__name__}"
            )
        if last_n < 1:
            raise ValueError(f"last_n must be >= 1, got {last_n}")

        with self._lock:
            return list(self._history[-last_n:])

    @property
    def history_depth(self) -> int:
        """Current number of archived state snapshots."""
        with self._lock:
            return len(self._history)

    @property
    def version(self) -> int:
        """Current state version number."""
        with self._lock:
            return self._state.version
