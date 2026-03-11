# =============================================================================
# jarvis/execution/session_aware_executor.py -- Session-Aware Executor (MA-6)
#
# Asset-class-aware simulated execution with session detection, spread
# adjustment, and market-close deferral logic.
#
# P0: SANDBOXED. No broker contact. No real order flow.
# All outputs are hypothetical scenarios for backtesting and research.
#
# =============================================================================
# FAS COMPLIANCE DECLARATION
# =============================================================================
#
# Dependency matrix:
#   session_aware_executor.py -> jarvis.core.regime (AssetClass)
#   session_aware_executor.py -> jarvis.core.data_structures
#       (MarketMicrostructure, SessionDefinition, TradingHours,
#        CRYPTO_MICROSTRUCTURE, FOREX_MICROSTRUCTURE,
#        INDICES_MICROSTRUCTURE, COMMODITIES_MICROSTRUCTURE,
#        RATES_MICROSTRUCTURE)
#   session_aware_executor.py -> (stdlib only)
#
# DETERMINISM GUARANTEES: DET-01 through DET-07 enforced.
#   DET-01  No stochastic operations.
#   DET-02  All inputs passed explicitly (including current_time_utc).
#   DET-03  No side effects.
#   DET-05  Same inputs -> same outputs.
#   DET-06  Fixed literals not parameterizable.
#
# PROHIBITED ACTIONS CONFIRMED ABSENT:
#   PROHIBITED-01: No numpy, no scipy. Pure stdlib math.
#   PROHIBITED-02: No file I/O.
#   PROHIBITED-03: No logging/print.
#   PROHIBITED-04: No environment variable access.
#   PROHIBITED-05: No global mutable state.
#   PROHIBITED-08: No new Enum definitions.
#   PROHIBITED-09: No string-based regime branching.
#
# ASCII COMPLIANCE: All literals are 7-bit ASCII.
# =============================================================================

from __future__ import annotations

import hashlib
import json
import math
from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple

from jarvis.core.regime import AssetClass
from jarvis.core.data_structures import (
    MarketMicrostructure,
    SessionDefinition,
    TradingHours,
    CRYPTO_MICROSTRUCTURE,
    FOREX_MICROSTRUCTURE,
    INDICES_MICROSTRUCTURE,
    COMMODITIES_MICROSTRUCTURE,
    RATES_MICROSTRUCTURE,
)


# =============================================================================
# SECTION 1 -- CONSTANTS (DET-06: fixed literals)
# =============================================================================

# Microstructure registry keyed by AssetClass
MICROSTRUCTURE_REGISTRY: Dict[AssetClass, MarketMicrostructure] = {
    AssetClass.CRYPTO: CRYPTO_MICROSTRUCTURE,
    AssetClass.FOREX: FOREX_MICROSTRUCTURE,
    AssetClass.INDICES: INDICES_MICROSTRUCTURE,
    AssetClass.COMMODITIES: COMMODITIES_MICROSTRUCTURE,
    AssetClass.RATES: RATES_MICROSTRUCTURE,
}

# Near-close deferral window: 15 minutes before session end (in minutes)
NEAR_CLOSE_MINUTES: int = 15

# Forex illiquid period: Friday 20:00 UTC to Sunday 22:00 UTC
# Represented as (weekday, hour): weekday 4=Friday, 6=Sunday
FOREX_ILLIQUID_START_DAY: int = 4   # Friday
FOREX_ILLIQUID_START_HOUR: int = 20
FOREX_ILLIQUID_END_DAY: int = 6     # Sunday
FOREX_ILLIQUID_END_HOUR: int = 22

# Spread multiplier for low-liquidity sessions
LOW_LIQUIDITY_SPREAD_MULTIPLIER: float = 2.0

# Spread multiplier for illiquid periods (weekend gap)
ILLIQUID_SPREAD_MULTIPLIER: float = 3.0

# Execution statuses
STATUS_FILLED: str = "FILLED"
STATUS_DEFERRED: str = "DEFERRED"
STATUS_REJECTED: str = "REJECTED"
STATUS_AUCTION: str = "AUCTION"

# Slippage base factor
SLIPPAGE_BASE_FACTOR: float = 0.5  # Half-spread slippage


# =============================================================================
# SECTION 2 -- RESULT DATACLASSES
# =============================================================================

@dataclass(frozen=True)
class SessionInfo:
    """Current session detection result.

    Attributes:
        session_name: Name of current session (or "closed" if outside hours).
        is_open: Whether the market is currently open.
        liquidity: Liquidity level of current session.
        spread_multiplier: Spread multiplier for current session.
        near_close: Whether we are within NEAR_CLOSE_MINUTES of session end.
        near_open: Whether we are in pre-market / near session open.
        minutes_to_close: Minutes remaining until session end (-1 if not applicable).
    """
    session_name: str
    is_open: bool
    liquidity: str
    spread_multiplier: float
    near_close: bool
    near_open: bool
    minutes_to_close: int


@dataclass(frozen=True)
class ExecutionDecision:
    """Simulated execution decision result.

    P0: Hypothetical. No real orders. No broker contact.

    Attributes:
        symbol: Asset symbol.
        asset_class: Asset class.
        status: Execution status (FILLED, DEFERRED, REJECTED, AUCTION).
        reason: Human-readable reason for the decision.
        session_info: Session detection result.
        estimated_spread_bps: Estimated spread in basis points.
        estimated_slippage_bps: Estimated slippage in basis points.
        size_adjustment_factor: Size reduction factor [0, 1] for liquidity.
        recommended_algo: Recommended execution algorithm.
        result_hash: SHA-256[:16] for determinism verification.
    """
    symbol: str
    asset_class: AssetClass
    status: str
    reason: str
    session_info: SessionInfo
    estimated_spread_bps: float
    estimated_slippage_bps: float
    size_adjustment_factor: float
    recommended_algo: str
    result_hash: str


# =============================================================================
# SECTION 3 -- SESSION DETECTION (pure functions)
# =============================================================================

def _parse_time(time_str: str) -> Tuple[int, int]:
    """Parse 'HH:MM' string to (hour, minute) tuple.

    Args:
        time_str: Time string in HH:MM format.

    Returns:
        (hour, minute) tuple.
    """
    parts = time_str.split(":")
    return int(parts[0]), int(parts[1])


def _time_to_minutes(hour: int, minute: int) -> int:
    """Convert (hour, minute) to minutes since midnight."""
    return hour * 60 + minute


def _is_in_session(
    current_minutes: int,
    start_minutes: int,
    end_minutes: int,
) -> bool:
    """Check if current time is within a session window.

    Handles overnight sessions (start > end).

    Args:
        current_minutes: Current time in minutes since midnight.
        start_minutes: Session start in minutes since midnight.
        end_minutes: Session end in minutes since midnight.

    Returns:
        True if within session.
    """
    if start_minutes <= end_minutes:
        return start_minutes <= current_minutes < end_minutes
    else:
        # Overnight session
        return current_minutes >= start_minutes or current_minutes < end_minutes


def _minutes_until_end(
    current_minutes: int,
    end_minutes: int,
) -> int:
    """Compute minutes until session end.

    Args:
        current_minutes: Current time in minutes since midnight.
        end_minutes: Session end in minutes since midnight.

    Returns:
        Minutes remaining (always >= 0).
    """
    if end_minutes > current_minutes:
        return end_minutes - current_minutes
    else:
        return (1440 - current_minutes) + end_minutes


def detect_session(
    *,
    current_hour: int,
    current_minute: int,
    current_weekday: int,
    microstructure: MarketMicrostructure,
) -> SessionInfo:
    """Detect current trading session for an asset class.

    Args:
        current_hour: Current UTC hour (0-23).
        current_minute: Current UTC minute (0-59).
        current_weekday: Current weekday (0=Monday, 6=Sunday).
        microstructure: Asset class microstructure configuration.

    Returns:
        SessionInfo with session detection result.
    """
    mode = microstructure.trading_hours.mode
    current_minutes = _time_to_minutes(current_hour, current_minute)

    # 24/7: Always open (crypto)
    if mode == "24/7":
        return SessionInfo(
            session_name="continuous",
            is_open=True,
            liquidity="normal",
            spread_multiplier=1.0,
            near_close=False,
            near_open=False,
            minutes_to_close=-1,
        )

    # 24/5: Open Mon-Fri (forex)
    if mode == "24/5":
        # Check forex illiquid period
        is_illiquid = _is_forex_illiquid(current_weekday, current_hour)
        if is_illiquid:
            return SessionInfo(
                session_name="weekend_closed",
                is_open=False,
                liquidity="closed",
                spread_multiplier=ILLIQUID_SPREAD_MULTIPLIER,
                near_close=False,
                near_open=False,
                minutes_to_close=-1,
            )

        # Determine which forex session we're in
        return _detect_forex_session(
            current_minutes, microstructure,
        )

    # Session-based: indices, commodities, rates
    return _detect_session_based(
        current_minutes, microstructure,
    )


def _is_forex_illiquid(weekday: int, hour: int) -> bool:
    """Check if in forex illiquid period (Fri 20:00 - Sun 22:00 UTC).

    Args:
        weekday: 0=Monday, 6=Sunday.
        hour: UTC hour.

    Returns:
        True if in illiquid period.
    """
    # Saturday: always illiquid
    if weekday == 5:
        return True
    # Friday after 20:00
    if weekday == FOREX_ILLIQUID_START_DAY and hour >= FOREX_ILLIQUID_START_HOUR:
        return True
    # Sunday before 22:00
    if weekday == FOREX_ILLIQUID_END_DAY and hour < FOREX_ILLIQUID_END_HOUR:
        return True
    return False


def _detect_forex_session(
    current_minutes: int,
    microstructure: MarketMicrostructure,
) -> SessionInfo:
    """Detect which forex session is active.

    Args:
        current_minutes: Minutes since midnight UTC.
        microstructure: Forex microstructure.

    Returns:
        SessionInfo for the active forex session.
    """
    sessions = microstructure.session_structure.sessions
    spread_mults = dict(microstructure.spread_model.session_multipliers)

    for sess in sessions:
        start_h, start_m = _parse_time(sess.start_utc)
        end_h, end_m = _parse_time(sess.end_utc)
        start_min = _time_to_minutes(start_h, start_m)
        end_min = _time_to_minutes(end_h, end_m)

        if _is_in_session(current_minutes, start_min, end_min):
            mins_to_close = _minutes_until_end(current_minutes, end_min)
            near_close = mins_to_close <= NEAR_CLOSE_MINUTES
            spread_mult = spread_mults.get(sess.name, 1.0)

            return SessionInfo(
                session_name=sess.name,
                is_open=True,
                liquidity=sess.liquidity,
                spread_multiplier=spread_mult,
                near_close=near_close,
                near_open=False,
                minutes_to_close=mins_to_close,
            )

    # Between sessions but still 24/5 day — use last known or default
    return SessionInfo(
        session_name="inter_session",
        is_open=True,
        liquidity="low",
        spread_multiplier=LOW_LIQUIDITY_SPREAD_MULTIPLIER,
        near_close=False,
        near_open=False,
        minutes_to_close=-1,
    )


def _detect_session_based(
    current_minutes: int,
    microstructure: MarketMicrostructure,
) -> SessionInfo:
    """Detect session for session-based markets (indices, commodities, rates).

    Args:
        current_minutes: Minutes since midnight UTC.
        microstructure: Asset class microstructure.

    Returns:
        SessionInfo for the current session.
    """
    sessions = microstructure.session_structure.sessions
    spread_mults = dict(microstructure.spread_model.session_multipliers)

    for sess in sessions:
        start_h, start_m = _parse_time(sess.start_utc)
        end_h, end_m = _parse_time(sess.end_utc)
        start_min = _time_to_minutes(start_h, start_m)
        end_min = _time_to_minutes(end_h, end_m)

        if _is_in_session(current_minutes, start_min, end_min):
            mins_to_close = _minutes_until_end(current_minutes, end_min)
            near_close = mins_to_close <= NEAR_CLOSE_MINUTES
            near_open = sess.name in ("pre_market",)
            spread_mult = spread_mults.get(sess.name, 1.0)

            return SessionInfo(
                session_name=sess.name,
                is_open=True,
                liquidity=sess.liquidity,
                spread_multiplier=spread_mult,
                near_close=near_close,
                near_open=near_open,
                minutes_to_close=mins_to_close,
            )

    # Outside all sessions -> market closed
    return SessionInfo(
        session_name="closed",
        is_open=False,
        liquidity="closed",
        spread_multiplier=0.0,
        near_close=False,
        near_open=False,
        minutes_to_close=-1,
    )


# =============================================================================
# SECTION 4 -- SESSION-AWARE EXECUTOR
# =============================================================================

class SessionAwareExecutor:
    """Session-aware simulated execution engine.

    P0: SANDBOXED. No broker contact. No real order flow.
    All outputs are hypothetical scenarios for research and backtesting.

    Execution logic per asset class:
    - Crypto (24/7): Always execute immediately.
    - Forex (24/5): Session-aware; wider spreads in Asia/low-liquidity.
    - Indices (session): Auction at open; defer near close; gap risk avoidance.
    - Commodities (session): Standard session logic.
    - Rates (session): Standard session logic.

    All inputs are explicit parameters (DET-02).
    No internal state retained between calls (DET-03, PROHIBITED-05).
    """

    def execute(
        self,
        *,
        symbol: str,
        asset_class: AssetClass,
        order_size: float,
        current_hour: int,
        current_minute: int,
        current_weekday: int,
        urgency: float = 0.5,
    ) -> ExecutionDecision:
        """Determine simulated execution decision for an order.

        Args:
            symbol: Asset symbol.
            asset_class: Asset class.
            order_size: Order size (units, can be negative for sells).
            current_hour: Current UTC hour (0-23).
            current_minute: Current UTC minute (0-59).
            current_weekday: Current weekday (0=Mon, 6=Sun).
            urgency: Execution urgency [0, 1].

        Returns:
            ExecutionDecision with status and session info.
        """
        micro = MICROSTRUCTURE_REGISTRY.get(asset_class)
        if micro is None:
            return self._rejected(symbol, asset_class, "Unknown asset class")

        # Detect session
        session_info = detect_session(
            current_hour=current_hour,
            current_minute=current_minute,
            current_weekday=current_weekday,
            microstructure=micro,
        )

        # Dispatch by trading hours mode
        mode = micro.trading_hours.mode
        if mode == "24/7":
            return self._execute_crypto(symbol, asset_class, micro, session_info, urgency)
        elif mode == "24/5":
            return self._execute_forex(symbol, asset_class, micro, session_info, urgency)
        else:
            return self._execute_session_based(symbol, asset_class, micro, session_info, urgency)

    def _execute_crypto(
        self,
        symbol: str,
        asset_class: AssetClass,
        micro: MarketMicrostructure,
        session: SessionInfo,
        urgency: float,
    ) -> ExecutionDecision:
        """Crypto: always execute immediately. 24/7/365."""
        spread = micro.typical_spread_bps
        slippage = spread * SLIPPAGE_BASE_FACTOR
        algo = self._select_algo(urgency, "normal")

        return self._make_decision(
            symbol=symbol,
            asset_class=asset_class,
            status=STATUS_FILLED,
            reason="24/7 market - immediate execution",
            session_info=session,
            spread=spread,
            slippage=slippage,
            size_factor=1.0,
            algo=algo,
        )

    def _execute_forex(
        self,
        symbol: str,
        asset_class: AssetClass,
        micro: MarketMicrostructure,
        session: SessionInfo,
        urgency: float,
    ) -> ExecutionDecision:
        """Forex: session-aware. Wider spreads in low-liquidity sessions."""
        if not session.is_open:
            return self._make_decision(
                symbol=symbol,
                asset_class=asset_class,
                status=STATUS_DEFERRED,
                reason="Forex market closed (weekend illiquid period)",
                session_info=session,
                spread=micro.typical_spread_bps * ILLIQUID_SPREAD_MULTIPLIER,
                slippage=0.0,
                size_factor=0.0,
                algo="HOLD",
            )

        # Low liquidity: wider spreads, reduced size
        if session.liquidity == "low":
            spread = micro.typical_spread_bps * session.spread_multiplier
            slippage = spread * SLIPPAGE_BASE_FACTOR
            algo = self._select_algo(urgency, "low")
            size_factor = 0.7  # Reduce size in low liquidity

            return self._make_decision(
                symbol=symbol,
                asset_class=asset_class,
                status=STATUS_FILLED,
                reason=f"Low liquidity session ({session.session_name}) - wider spreads",
                session_info=session,
                spread=spread,
                slippage=slippage,
                size_factor=size_factor,
                algo=algo,
            )

        # Normal/high liquidity
        spread = micro.typical_spread_bps * session.spread_multiplier
        slippage = spread * SLIPPAGE_BASE_FACTOR
        algo = self._select_algo(urgency, session.liquidity)

        return self._make_decision(
            symbol=symbol,
            asset_class=asset_class,
            status=STATUS_FILLED,
            reason=f"Normal execution in {session.session_name} session",
            session_info=session,
            spread=spread,
            slippage=slippage,
            size_factor=1.0,
            algo=algo,
        )

    def _execute_session_based(
        self,
        symbol: str,
        asset_class: AssetClass,
        micro: MarketMicrostructure,
        session: SessionInfo,
        urgency: float,
    ) -> ExecutionDecision:
        """Session-based markets: indices, commodities, rates."""
        # Market closed
        if not session.is_open:
            return self._make_decision(
                symbol=symbol,
                asset_class=asset_class,
                status=STATUS_DEFERRED,
                reason="Market closed - defer to next session",
                session_info=session,
                spread=0.0,
                slippage=0.0,
                size_factor=0.0,
                algo="HOLD",
            )

        # Near market close: defer to avoid gap risk
        if session.near_close:
            return self._make_decision(
                symbol=symbol,
                asset_class=asset_class,
                status=STATUS_DEFERRED,
                reason=f"Near session close ({session.minutes_to_close}min remaining) - defer for gap risk avoidance",
                session_info=session,
                spread=micro.typical_spread_bps * session.spread_multiplier,
                slippage=0.0,
                size_factor=0.0,
                algo="HOLD",
            )

        # Near market open / pre-market: execute at auction
        if session.near_open:
            spread = micro.typical_spread_bps * session.spread_multiplier
            slippage = spread * SLIPPAGE_BASE_FACTOR * 1.5  # Auction premium
            return self._make_decision(
                symbol=symbol,
                asset_class=asset_class,
                status=STATUS_AUCTION,
                reason="Pre-market session - execute at opening auction",
                session_info=session,
                spread=spread,
                slippage=slippage,
                size_factor=0.8,  # Reduced size for auction
                algo="AUCTION",
            )

        # Regular session
        spread = micro.typical_spread_bps * session.spread_multiplier
        slippage = spread * SLIPPAGE_BASE_FACTOR
        algo = self._select_algo(urgency, session.liquidity)

        return self._make_decision(
            symbol=symbol,
            asset_class=asset_class,
            status=STATUS_FILLED,
            reason=f"Regular session execution ({session.session_name})",
            session_info=session,
            spread=spread,
            slippage=slippage,
            size_factor=1.0,
            algo=algo,
        )

    def _select_algo(self, urgency: float, liquidity: str) -> str:
        """Select execution algorithm based on urgency and liquidity.

        Args:
            urgency: Urgency score [0, 1].
            liquidity: Liquidity level ("high", "normal", "low").

        Returns:
            Algorithm name.
        """
        if urgency > 0.8:
            return "AGGRESSIVE"
        elif liquidity == "high":
            return "VWAP"
        elif liquidity == "low":
            return "LIMIT"
        else:
            return "TWAP"

    def _rejected(
        self,
        symbol: str,
        asset_class: AssetClass,
        reason: str,
    ) -> ExecutionDecision:
        """Create a REJECTED execution decision."""
        session = SessionInfo(
            session_name="unknown",
            is_open=False,
            liquidity="unknown",
            spread_multiplier=0.0,
            near_close=False,
            near_open=False,
            minutes_to_close=-1,
        )
        return self._make_decision(
            symbol=symbol,
            asset_class=asset_class,
            status=STATUS_REJECTED,
            reason=reason,
            session_info=session,
            spread=0.0,
            slippage=0.0,
            size_factor=0.0,
            algo="HOLD",
        )

    def _make_decision(
        self,
        *,
        symbol: str,
        asset_class: AssetClass,
        status: str,
        reason: str,
        session_info: SessionInfo,
        spread: float,
        slippage: float,
        size_factor: float,
        algo: str,
    ) -> ExecutionDecision:
        """Build ExecutionDecision with deterministic hash."""
        payload = {
            "symbol": symbol,
            "ac": asset_class.value,
            "status": status,
            "session": session_info.session_name,
            "spread": round(spread, 8),
            "slippage": round(slippage, 8),
            "size_factor": round(size_factor, 8),
            "algo": algo,
        }
        result_hash = hashlib.sha256(
            json.dumps(payload, sort_keys=True).encode("utf-8")
        ).hexdigest()[:16]

        return ExecutionDecision(
            symbol=symbol,
            asset_class=asset_class,
            status=status,
            reason=reason,
            session_info=session_info,
            estimated_spread_bps=spread,
            estimated_slippage_bps=slippage,
            size_adjustment_factor=size_factor,
            recommended_algo=algo,
            result_hash=result_hash,
        )
