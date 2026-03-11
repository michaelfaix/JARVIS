# =============================================================================
# jarvis/core/event_bus.py
# Authority: FAS v6.0.1 -- S37 SYSTEM ADDENDUM, EVENT BUS FORMALIZATION
# ARCHITECTURE.md Section 13
# =============================================================================
#
# SCOPE
# -----
# Immutable event dataclasses for the analytical event system.
# Six event types covering all inter-layer state change communication.
#
# CLASSIFICATION
# --------------
# Analytical and research only. No execution triggers. No order events.
# All events are immutable (frozen dataclasses). All state mutation
# routes through ctrl.update(). The event system is the sole mechanism
# for communicating state changes between layers.
#
# DEPENDENCIES
# ------------
#   stdlib:    dataclasses, enum, typing
#   internal:  NONE
#   PROHIBITED: numpy, logging, random, file IO, network IO
#
# DETERMINISM
# -----------
# DET-01  No stochastic operations.
# DET-02  All inputs passed explicitly. event_id provided by caller.
# DET-03  No side effects. All dataclasses are frozen.
# DET-04  No arithmetic operations.
# DET-05  No datetime.now() / time.time() calls. Timestamps are caller-provided.
# DET-06  No parameterisable literals.
#
# FORBIDDEN EVENT PATTERNS (from S37)
# ------------------------------------
# The following event types must NEVER be defined or emitted:
#   OrderEvent, BrokerConnectEvent, ExecutionEvent,
#   CapitalMutationEvent, AccountStateEvent
# Any event type not listed in EventType is rejected at construction.
# =============================================================================

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, Optional, Tuple

__all__ = [
    "EventType",
    "BaseEvent",
    "MarketDataEvent",
    "RegimeChangeEvent",
    "FailureModeEvent",
    "ExposureEvent",
    "StrategyWeightChangeEvent",
    "ConfidenceUpdateEvent",
    "VALID_FAILURE_MODE_CODES",
    "VALID_DATA_SOURCES",
]


# =============================================================================
# SECTION 1 -- EVENT TYPE ENUM
# =============================================================================

class EventType(str, Enum):
    """
    Exhaustive enumeration of permitted analytical event types.

    Any event type not listed here must NEVER enter the event queue.
    This enum is the enforcement gate for the forbidden-event-patterns
    rule from S37.
    """
    MARKET_DATA       = "market_data"
    REGIME_CHANGE     = "regime_change"
    FAILURE_MODE      = "failure_mode"
    EXPOSURE          = "exposure"
    STRATEGY_WEIGHT   = "strategy_weight_change"
    CONFIDENCE_UPDATE = "confidence_update"


# =============================================================================
# SECTION 2 -- CONSTANTS
# =============================================================================

VALID_FAILURE_MODE_CODES: Tuple[str, ...] = (
    "FM-01", "FM-02", "FM-03", "FM-04", "FM-05", "FM-06",
)

VALID_DATA_SOURCES: Tuple[str, ...] = (
    "historical", "live", "hybrid_backfill", "hybrid_live",
)


# =============================================================================
# SECTION 3 -- VALIDATION HELPERS
# =============================================================================

def _validate_base_fields(
    event_id: str,
    event_type: EventType,
    sequence_id: int,
) -> None:
    """
    Fail-fast validation for BaseEvent fields.
    Called from __post_init__ of every event subclass (via BaseEvent).
    """
    if not isinstance(event_id, str) or not event_id:
        raise ValueError(
            f"event_id must be a non-empty string, got {event_id!r}"
        )
    if not isinstance(event_type, EventType):
        raise TypeError(
            f"event_type must be an EventType member, got {event_type!r}"
        )
    if not isinstance(sequence_id, int) or isinstance(sequence_id, bool):
        raise TypeError(
            f"sequence_id must be an int, got {type(sequence_id).__name__}"
        )
    if sequence_id < 0:
        raise ValueError(
            f"sequence_id must be >= 0, got {sequence_id}"
        )


# =============================================================================
# SECTION 4 -- BASE EVENT
# =============================================================================

@dataclass(frozen=True)
class BaseEvent:
    """
    Base for all analytical events. Immutable after creation.

    Fields:
        event_id:    Unique identifier string (caller-provided).
        event_type:  Must be a valid EventType member.
        timestamp:   Caller-provided timestamp (float, e.g. epoch seconds).
                     Module does NOT call datetime.now() (DET-05).
        sequence_id: Global monotonic sequence number for replay ordering.
        asset_id:    Optional asset identifier. None means system-wide event.
    """
    event_id:    str
    event_type:  EventType
    timestamp:   float
    sequence_id: int
    asset_id:    Optional[str] = None

    def __post_init__(self) -> None:
        _validate_base_fields(self.event_id, self.event_type, self.sequence_id)


# =============================================================================
# SECTION 5 -- CONCRETE EVENT TYPES
# =============================================================================

@dataclass(frozen=True)
class MarketDataEvent(BaseEvent):
    """
    Emitted when a StandardizedMarketDataObject is admitted through
    the Live Data Integrity Gate or loaded from historical store.
    """
    symbol:        str   = ""
    timeframe:     str   = ""
    close:         float = 0.0
    quality_score: float = 1.0
    gap_detected:  bool  = False
    is_stale:      bool  = False
    data_source:   str   = "historical"

    def __post_init__(self) -> None:
        super().__post_init__()
        if self.event_type != EventType.MARKET_DATA:
            raise ValueError(
                f"MarketDataEvent requires event_type=MARKET_DATA, "
                f"got {self.event_type!r}"
            )
        if self.data_source not in VALID_DATA_SOURCES:
            raise ValueError(
                f"data_source must be one of {VALID_DATA_SOURCES}, "
                f"got {self.data_source!r}"
            )


@dataclass(frozen=True)
class RegimeChangeEvent(BaseEvent):
    """
    Emitted when RegimeState.regime changes value.
    """
    from_regime:     str   = ""
    to_regime:       str   = ""
    confidence:      float = 0.0
    transition_flag: bool  = True

    def __post_init__(self) -> None:
        super().__post_init__()
        if self.event_type != EventType.REGIME_CHANGE:
            raise ValueError(
                f"RegimeChangeEvent requires event_type=REGIME_CHANGE, "
                f"got {self.event_type!r}"
            )


@dataclass(frozen=True)
class FailureModeEvent(BaseEvent):
    """
    Emitted when a Failure Mode (FM-01..FM-06) is activated or resolved.
    """
    failure_mode_code: str              = ""
    activated:         bool             = True
    trigger_condition: str              = ""
    confidence_impact: Dict[str, float] = field(default_factory=dict)

    def __post_init__(self) -> None:
        super().__post_init__()
        if self.event_type != EventType.FAILURE_MODE:
            raise ValueError(
                f"FailureModeEvent requires event_type=FAILURE_MODE, "
                f"got {self.event_type!r}"
            )
        if self.failure_mode_code not in VALID_FAILURE_MODE_CODES:
            raise ValueError(
                f"failure_mode_code must be one of {VALID_FAILURE_MODE_CODES}, "
                f"got {self.failure_mode_code!r}"
            )


@dataclass(frozen=True)
class ExposureEvent(BaseEvent):
    """
    Emitted when PortfolioState.gross_exposure or net_exposure changes
    beyond EXPOSURE_DELTA_THRESHOLD.
    """
    prior_gross_exposure:   float = 0.0
    current_gross_exposure: float = 0.0
    prior_net_exposure:     float = 0.0
    current_net_exposure:   float = 0.0
    trigger_source:         str   = ""

    def __post_init__(self) -> None:
        super().__post_init__()
        if self.event_type != EventType.EXPOSURE:
            raise ValueError(
                f"ExposureEvent requires event_type=EXPOSURE, "
                f"got {self.event_type!r}"
            )


@dataclass(frozen=True)
class StrategyWeightChangeEvent(BaseEvent):
    """
    Emitted when StrategyState.weight_scalar changes.
    Weight may ONLY change via StrategyObject.Weight_Model.
    """
    strategy_id:    str   = ""
    prior_weight:   float = 0.0
    new_weight:     float = 0.0
    regime_trigger: str   = ""

    def __post_init__(self) -> None:
        super().__post_init__()
        if self.event_type != EventType.STRATEGY_WEIGHT:
            raise ValueError(
                f"StrategyWeightChangeEvent requires event_type=STRATEGY_WEIGHT, "
                f"got {self.event_type!r}"
            )


@dataclass(frozen=True)
class ConfidenceUpdateEvent(BaseEvent):
    """
    Emitted when ConfidenceBundle values change.
    Only emitted on permitted refresh triggers (see CONFIDENCE REFRESH LOGIC).
    """
    prior_mu: float = 0.0
    new_mu:   float = 0.0
    prior_Q:  float = 0.0
    new_Q:    float = 0.0
    prior_U:  float = 0.0
    new_U:    float = 0.0
    trigger:  str   = ""

    def __post_init__(self) -> None:
        super().__post_init__()
        if self.event_type != EventType.CONFIDENCE_UPDATE:
            raise ValueError(
                f"ConfidenceUpdateEvent requires event_type=CONFIDENCE_UPDATE, "
                f"got {self.event_type!r}"
            )
