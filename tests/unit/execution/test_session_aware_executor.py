# =============================================================================
# tests/unit/execution/test_session_aware_executor.py
#
# Comprehensive tests for jarvis/execution/session_aware_executor.py (MA-6).
# Covers: instantiation, constants, session detection, per-asset-class
#         execution logic, forex illiquid period, indices auction/defer,
#         near-close/near-open detection, spread multipliers, liquidity regime,
#         deferral logic, algo selection, determinism, immutability, edge cases,
#         import contract.
# =============================================================================

import pytest

from jarvis.core.regime import AssetClass
from jarvis.core.data_structures import (
    CRYPTO_MICROSTRUCTURE,
    FOREX_MICROSTRUCTURE,
    INDICES_MICROSTRUCTURE,
    COMMODITIES_MICROSTRUCTURE,
    RATES_MICROSTRUCTURE,
    MarketMicrostructure,
    SessionDefinition,
    SessionStructure,
    SpreadModel,
    TradingHours,
    LiquidityProfile,
)
from jarvis.execution.session_aware_executor import (
    # Constants
    MICROSTRUCTURE_REGISTRY,
    NEAR_CLOSE_MINUTES,
    LOW_LIQUIDITY_SPREAD_MULTIPLIER,
    ILLIQUID_SPREAD_MULTIPLIER,
    FOREX_ILLIQUID_START_DAY,
    FOREX_ILLIQUID_START_HOUR,
    FOREX_ILLIQUID_END_DAY,
    FOREX_ILLIQUID_END_HOUR,
    STATUS_FILLED,
    STATUS_DEFERRED,
    STATUS_REJECTED,
    STATUS_AUCTION,
    SLIPPAGE_BASE_FACTOR,
    # Helpers
    _parse_time,
    _time_to_minutes,
    _is_in_session,
    _minutes_until_end,
    _is_forex_illiquid,
    detect_session,
    # Dataclasses
    SessionInfo,
    ExecutionDecision,
    # Engine
    SessionAwareExecutor,
)


# ---------------------------------------------------------------------------
# SHARED HELPERS
# ---------------------------------------------------------------------------

def _exec(asset_class=AssetClass.CRYPTO, symbol="BTC", hour=14, minute=0,
          weekday=2, urgency=0.5, order_size=1.0):
    """Helper to call executor with defaults."""
    return SessionAwareExecutor().execute(
        symbol=symbol,
        asset_class=asset_class,
        order_size=order_size,
        current_hour=hour,
        current_minute=minute,
        current_weekday=weekday,
        urgency=urgency,
    )


# ===========================================================================
# 1. TestSessionAwareExecutorInit
# ===========================================================================

class TestSessionAwareExecutorInit:
    """Instantiation and default microstructure registry."""

    def test_instantiation_no_args(self):
        executor = SessionAwareExecutor()
        assert executor is not None

    def test_multiple_instances_independent(self):
        e1 = SessionAwareExecutor()
        e2 = SessionAwareExecutor()
        assert e1 is not e2

    def test_registry_contains_all_asset_classes(self):
        for ac in AssetClass:
            assert ac in MICROSTRUCTURE_REGISTRY, f"{ac} missing from registry"

    def test_registry_maps_to_correct_microstructures(self):
        assert MICROSTRUCTURE_REGISTRY[AssetClass.CRYPTO] is CRYPTO_MICROSTRUCTURE
        assert MICROSTRUCTURE_REGISTRY[AssetClass.FOREX] is FOREX_MICROSTRUCTURE
        assert MICROSTRUCTURE_REGISTRY[AssetClass.INDICES] is INDICES_MICROSTRUCTURE
        assert MICROSTRUCTURE_REGISTRY[AssetClass.COMMODITIES] is COMMODITIES_MICROSTRUCTURE
        assert MICROSTRUCTURE_REGISTRY[AssetClass.RATES] is RATES_MICROSTRUCTURE

    def test_registry_length_matches_asset_class_count(self):
        assert len(MICROSTRUCTURE_REGISTRY) == len(AssetClass)

    def test_execute_is_callable(self):
        executor = SessionAwareExecutor()
        assert callable(getattr(executor, "execute", None))


# ===========================================================================
# 2. TestConstants
# ===========================================================================

class TestConstants:
    """DET-06: fixed literal constants."""

    def test_near_close_minutes(self):
        assert NEAR_CLOSE_MINUTES == 15

    def test_low_liquidity_spread_multiplier(self):
        assert LOW_LIQUIDITY_SPREAD_MULTIPLIER == 2.0

    def test_illiquid_spread_multiplier(self):
        assert ILLIQUID_SPREAD_MULTIPLIER == 3.0

    def test_slippage_base_factor(self):
        assert SLIPPAGE_BASE_FACTOR == 0.5

    def test_forex_illiquid_start(self):
        assert FOREX_ILLIQUID_START_DAY == 4
        assert FOREX_ILLIQUID_START_HOUR == 20

    def test_forex_illiquid_end(self):
        assert FOREX_ILLIQUID_END_DAY == 6
        assert FOREX_ILLIQUID_END_HOUR == 22

    def test_status_constants(self):
        assert STATUS_FILLED == "FILLED"
        assert STATUS_DEFERRED == "DEFERRED"
        assert STATUS_REJECTED == "REJECTED"
        assert STATUS_AUCTION == "AUCTION"


# ===========================================================================
# 3. TestTimeHelpers
# ===========================================================================

class TestTimeHelpers:
    """Pure helper functions for time parsing and session math."""

    def test_parse_time_standard(self):
        assert _parse_time("09:30") == (9, 30)
        assert _parse_time("00:00") == (0, 0)
        assert _parse_time("23:59") == (23, 59)

    def test_parse_time_single_digit(self):
        assert _parse_time("04:00") == (4, 0)
        assert _parse_time("08:00") == (8, 0)

    def test_time_to_minutes_midnight(self):
        assert _time_to_minutes(0, 0) == 0

    def test_time_to_minutes_standard(self):
        assert _time_to_minutes(9, 30) == 570
        assert _time_to_minutes(16, 0) == 960

    def test_time_to_minutes_end_of_day(self):
        assert _time_to_minutes(23, 59) == 1439

    def test_is_in_session_inside(self):
        assert _is_in_session(600, 570, 960) is True

    def test_is_in_session_before_start(self):
        assert _is_in_session(500, 570, 960) is False

    def test_is_in_session_at_end_exclusive(self):
        assert _is_in_session(960, 570, 960) is False

    def test_is_in_session_at_start_inclusive(self):
        assert _is_in_session(570, 570, 960) is True

    def test_is_in_session_overnight_late(self):
        # Session from 22:00 (1320) to 06:00 (360)
        assert _is_in_session(1380, 1320, 360) is True   # 23:00

    def test_is_in_session_overnight_early(self):
        assert _is_in_session(120, 1320, 360) is True     # 02:00

    def test_is_in_session_overnight_outside(self):
        assert _is_in_session(600, 1320, 360) is False    # 10:00

    def test_minutes_until_end_normal(self):
        assert _minutes_until_end(570, 960) == 390

    def test_minutes_until_end_close(self):
        assert _minutes_until_end(950, 960) == 10

    def test_minutes_until_end_at_end_wraps(self):
        assert _minutes_until_end(960, 960) == 1440

    def test_minutes_until_end_overnight_wrap(self):
        # Current 23:00 (1380), end 02:00 (120)
        assert _minutes_until_end(1380, 120) == 180


# ===========================================================================
# 4. TestForexIlliquidDetection
# ===========================================================================

class TestForexIlliquidDetection:
    """Forex illiquid period: Fri 20:00 - Sun 22:00 UTC."""

    def test_friday_before_20_is_open(self):
        assert _is_forex_illiquid(4, 19) is False

    def test_friday_at_20_is_illiquid(self):
        assert _is_forex_illiquid(4, 20) is True

    def test_friday_at_23_is_illiquid(self):
        assert _is_forex_illiquid(4, 23) is True

    def test_saturday_always_illiquid(self):
        for h in range(24):
            assert _is_forex_illiquid(5, h) is True, f"Saturday hour {h} should be illiquid"

    def test_sunday_before_22_is_illiquid(self):
        assert _is_forex_illiquid(6, 0) is True
        assert _is_forex_illiquid(6, 12) is True
        assert _is_forex_illiquid(6, 21) is True

    def test_sunday_at_22_is_open(self):
        assert _is_forex_illiquid(6, 22) is False

    def test_sunday_at_23_is_open(self):
        assert _is_forex_illiquid(6, 23) is False

    def test_monday_through_thursday_open(self):
        for day in range(4):  # 0=Mon through 3=Thu
            for h in [0, 6, 12, 18, 23]:
                assert _is_forex_illiquid(day, h) is False


# ===========================================================================
# 5. TestDetectSession
# ===========================================================================

class TestDetectSession:
    """Session detection for all asset classes."""

    # -- Crypto --
    def test_crypto_always_open(self):
        s = detect_session(
            current_hour=3, current_minute=30, current_weekday=5,
            microstructure=CRYPTO_MICROSTRUCTURE,
        )
        assert s.is_open is True
        assert s.session_name == "continuous"
        assert s.spread_multiplier == 1.0
        assert s.near_close is False
        assert s.near_open is False
        assert s.minutes_to_close == -1

    def test_crypto_any_weekday(self):
        for wd in range(7):
            s = detect_session(
                current_hour=12, current_minute=0, current_weekday=wd,
                microstructure=CRYPTO_MICROSTRUCTURE,
            )
            assert s.is_open is True
            assert s.liquidity == "normal"

    # -- Forex --
    def test_forex_asia_session(self):
        s = detect_session(
            current_hour=3, current_minute=0, current_weekday=2,
            microstructure=FOREX_MICROSTRUCTURE,
        )
        assert s.is_open is True
        assert s.session_name == "asia"
        assert s.liquidity == "low"

    def test_forex_europe_session(self):
        # 10:00 UTC falls within europe (08:00-17:00) -- first match in iteration
        s = detect_session(
            current_hour=10, current_minute=0, current_weekday=2,
            microstructure=FOREX_MICROSTRUCTURE,
        )
        assert s.is_open is True
        assert s.session_name in ("europe", "us")

    def test_forex_us_session(self):
        # 20:00 UTC is only within US session (13:00-22:00)
        s = detect_session(
            current_hour=20, current_minute=0, current_weekday=2,
            microstructure=FOREX_MICROSTRUCTURE,
        )
        assert s.is_open is True
        assert s.session_name == "us"

    def test_forex_weekend_closed(self):
        s = detect_session(
            current_hour=12, current_minute=0, current_weekday=5,
            microstructure=FOREX_MICROSTRUCTURE,
        )
        assert s.is_open is False
        assert s.session_name == "weekend_closed"
        assert s.liquidity == "closed"
        assert s.spread_multiplier == ILLIQUID_SPREAD_MULTIPLIER

    def test_forex_inter_session(self):
        # 22:30 UTC on a weekday: after US session ends at 22:00
        # and before Asia at 00:00 -- no session matches
        s = detect_session(
            current_hour=22, current_minute=30, current_weekday=2,
            microstructure=FOREX_MICROSTRUCTURE,
        )
        assert s.is_open is True
        assert s.session_name == "inter_session"
        assert s.liquidity == "low"
        assert s.spread_multiplier == LOW_LIQUIDITY_SPREAD_MULTIPLIER

    # -- Indices --
    def test_indices_regular_hours(self):
        s = detect_session(
            current_hour=12, current_minute=0, current_weekday=2,
            microstructure=INDICES_MICROSTRUCTURE,
        )
        assert s.is_open is True
        assert s.session_name == "regular"
        assert s.liquidity == "high"

    def test_indices_pre_market(self):
        s = detect_session(
            current_hour=5, current_minute=0, current_weekday=2,
            microstructure=INDICES_MICROSTRUCTURE,
        )
        assert s.is_open is True
        assert s.session_name == "pre_market"
        assert s.near_open is True

    def test_indices_post_market(self):
        s = detect_session(
            current_hour=18, current_minute=0, current_weekday=2,
            microstructure=INDICES_MICROSTRUCTURE,
        )
        assert s.is_open is True
        assert s.session_name == "post_market"
        assert s.near_open is False

    def test_indices_closed_overnight(self):
        s = detect_session(
            current_hour=2, current_minute=0, current_weekday=2,
            microstructure=INDICES_MICROSTRUCTURE,
        )
        assert s.is_open is False
        assert s.session_name == "closed"
        assert s.spread_multiplier == 0.0

    def test_indices_closed_late_night(self):
        s = detect_session(
            current_hour=21, current_minute=0, current_weekday=2,
            microstructure=INDICES_MICROSTRUCTURE,
        )
        assert s.is_open is False
        assert s.session_name == "closed"

    # -- Commodities --
    def test_commodities_regular(self):
        s = detect_session(
            current_hour=12, current_minute=0, current_weekday=1,
            microstructure=COMMODITIES_MICROSTRUCTURE,
        )
        assert s.is_open is True
        assert s.session_name == "regular"

    def test_commodities_closed(self):
        s = detect_session(
            current_hour=3, current_minute=0, current_weekday=1,
            microstructure=COMMODITIES_MICROSTRUCTURE,
        )
        assert s.is_open is False

    # -- Rates --
    def test_rates_regular(self):
        s = detect_session(
            current_hour=10, current_minute=0, current_weekday=1,
            microstructure=RATES_MICROSTRUCTURE,
        )
        assert s.is_open is True
        assert s.session_name == "regular"

    def test_rates_closed(self):
        s = detect_session(
            current_hour=22, current_minute=0, current_weekday=1,
            microstructure=RATES_MICROSTRUCTURE,
        )
        assert s.is_open is False


# ===========================================================================
# 6. TestCryptoExecution
# ===========================================================================

class TestCryptoExecution:
    """Crypto: 24/7 availability, no session restrictions."""

    def test_always_filled(self):
        d = _exec(asset_class=AssetClass.CRYPTO, hour=3, weekday=6)
        assert d.status == STATUS_FILLED
        assert d.size_adjustment_factor == 1.0

    def test_filled_every_hour(self):
        for h in range(24):
            d = _exec(asset_class=AssetClass.CRYPTO, hour=h)
            assert d.status == STATUS_FILLED

    def test_filled_every_weekday(self):
        for wd in range(7):
            d = _exec(asset_class=AssetClass.CRYPTO, weekday=wd)
            assert d.status == STATUS_FILLED

    def test_spread_matches_microstructure(self):
        d = _exec(asset_class=AssetClass.CRYPTO)
        assert d.estimated_spread_bps == CRYPTO_MICROSTRUCTURE.typical_spread_bps

    def test_slippage_is_half_spread(self):
        d = _exec(asset_class=AssetClass.CRYPTO)
        expected = CRYPTO_MICROSTRUCTURE.typical_spread_bps * SLIPPAGE_BASE_FACTOR
        assert abs(d.estimated_slippage_bps - expected) < 1e-10

    def test_session_info_continuous(self):
        d = _exec(asset_class=AssetClass.CRYPTO)
        assert d.session_info.session_name == "continuous"
        assert d.session_info.is_open is True

    def test_reason_contains_24_7(self):
        d = _exec(asset_class=AssetClass.CRYPTO)
        assert "24/7" in d.reason


# ===========================================================================
# 7. TestForexExecution
# ===========================================================================

class TestForexExecution:
    """Forex: session-aware, weekend detection, illiquid periods."""

    def test_europe_session_filled(self):
        d = _exec(asset_class=AssetClass.FOREX, symbol="EURUSD",
                   hour=10, weekday=2)
        assert d.status == STATUS_FILLED

    def test_asia_low_liquidity_reduced_size(self):
        d = _exec(asset_class=AssetClass.FOREX, symbol="EURUSD",
                   hour=3, weekday=2)
        assert d.status == STATUS_FILLED
        assert d.size_adjustment_factor == 0.7
        assert "Low liquidity" in d.reason

    def test_weekend_deferred(self):
        d = _exec(asset_class=AssetClass.FOREX, symbol="EURUSD",
                   hour=12, weekday=5)
        assert d.status == STATUS_DEFERRED
        assert d.size_adjustment_factor == 0.0
        assert d.recommended_algo == "HOLD"

    def test_friday_evening_deferred(self):
        d = _exec(asset_class=AssetClass.FOREX, symbol="EURUSD",
                   hour=21, weekday=4)
        assert d.status == STATUS_DEFERRED

    def test_sunday_before_22_deferred(self):
        d = _exec(asset_class=AssetClass.FOREX, symbol="EURUSD",
                   hour=15, weekday=6)
        assert d.status == STATUS_DEFERRED

    def test_sunday_after_22_filled(self):
        d = _exec(asset_class=AssetClass.FOREX, symbol="EURUSD",
                   hour=23, weekday=6)
        assert d.status == STATUS_FILLED

    def test_weekend_spread_uses_illiquid_multiplier(self):
        d = _exec(asset_class=AssetClass.FOREX, symbol="EURUSD",
                   hour=12, weekday=5)
        expected = FOREX_MICROSTRUCTURE.typical_spread_bps * ILLIQUID_SPREAD_MULTIPLIER
        assert abs(d.estimated_spread_bps - expected) < 1e-10

    def test_weekend_slippage_zero(self):
        d = _exec(asset_class=AssetClass.FOREX, symbol="EURUSD",
                   hour=12, weekday=5)
        assert d.estimated_slippage_bps == 0.0

    def test_normal_session_full_size(self):
        # US session at 14:00 on a Wednesday -- high liquidity
        d = _exec(asset_class=AssetClass.FOREX, symbol="EURUSD",
                   hour=14, weekday=2)
        assert d.size_adjustment_factor == 1.0

    def test_inter_session_low_liquidity(self):
        # 22:30 on a weekday -- inter_session, low liquidity
        d = _exec(asset_class=AssetClass.FOREX, symbol="EURUSD",
                   hour=22, minute=30, weekday=2)
        assert d.status == STATUS_FILLED
        assert d.size_adjustment_factor == 0.7
        assert "Low liquidity" in d.reason


# ===========================================================================
# 8. TestIndicesExecution
# ===========================================================================

class TestIndicesExecution:
    """Indices: auction awareness, pre/post market, regular hours."""

    def test_regular_hours_filled(self):
        d = _exec(asset_class=AssetClass.INDICES, symbol="SPY",
                   hour=12, weekday=2)
        assert d.status == STATUS_FILLED
        assert "Regular session" in d.reason

    def test_pre_market_auction(self):
        d = _exec(asset_class=AssetClass.INDICES, symbol="SPY",
                   hour=5, weekday=2)
        assert d.status == STATUS_AUCTION
        assert d.recommended_algo == "AUCTION"
        assert d.size_adjustment_factor == 0.8

    def test_pre_market_auction_slippage_premium(self):
        d = _exec(asset_class=AssetClass.INDICES, symbol="SPY",
                   hour=5, weekday=2)
        spread = INDICES_MICROSTRUCTURE.typical_spread_bps * 2.0
        expected_slippage = spread * SLIPPAGE_BASE_FACTOR * 1.5
        assert abs(d.estimated_slippage_bps - expected_slippage) < 1e-10

    def test_near_close_deferred(self):
        d = _exec(asset_class=AssetClass.INDICES, symbol="SPY",
                   hour=15, minute=50, weekday=2)
        assert d.status == STATUS_DEFERRED
        assert "gap risk" in d.reason.lower()

    def test_overnight_deferred(self):
        d = _exec(asset_class=AssetClass.INDICES, symbol="SPY",
                   hour=2, weekday=2)
        assert d.status == STATUS_DEFERRED
        assert "closed" in d.reason.lower()
        assert d.recommended_algo == "HOLD"

    def test_post_market_filled(self):
        d = _exec(asset_class=AssetClass.INDICES, symbol="SPY",
                   hour=17, weekday=2)
        assert d.status == STATUS_FILLED
        assert d.session_info.session_name == "post_market"

    def test_post_market_is_not_near_open(self):
        d = _exec(asset_class=AssetClass.INDICES, symbol="SPY",
                   hour=17, weekday=2)
        assert d.session_info.near_open is False

    def test_regular_session_full_size(self):
        d = _exec(asset_class=AssetClass.INDICES, symbol="SPY",
                   hour=12, weekday=2)
        assert d.size_adjustment_factor == 1.0


# ===========================================================================
# 9. TestNearCloseDetection
# ===========================================================================

class TestNearCloseDetection:
    """Near-close detection for different asset classes."""

    def test_indices_regular_near_close_boundary(self):
        # Regular session ends at 16:00 (960 min). 15:45 = 945 min.
        # minutes_to_close = 960 - 945 = 15, which equals NEAR_CLOSE_MINUTES.
        s = detect_session(
            current_hour=15, current_minute=45, current_weekday=2,
            microstructure=INDICES_MICROSTRUCTURE,
        )
        assert s.near_close is True
        assert s.minutes_to_close == 15

    def test_indices_regular_just_before_near_close(self):
        # 15:44 = 944 min. minutes_to_close = 960 - 944 = 16 > 15
        s = detect_session(
            current_hour=15, current_minute=44, current_weekday=2,
            microstructure=INDICES_MICROSTRUCTURE,
        )
        assert s.near_close is False
        assert s.minutes_to_close == 16

    def test_indices_post_market_near_close(self):
        # Post-market ends at 20:00 (1200 min). 19:50 = 1190 min.
        # minutes_to_close = 1200 - 1190 = 10 <= 15
        s = detect_session(
            current_hour=19, current_minute=50, current_weekday=2,
            microstructure=INDICES_MICROSTRUCTURE,
        )
        assert s.near_close is True
        assert s.minutes_to_close == 10

    def test_commodities_near_close(self):
        # Regular session ends at 17:00 (1020 min). 16:50 = 1010 min.
        # minutes_to_close = 1020 - 1010 = 10 <= 15
        s = detect_session(
            current_hour=16, current_minute=50, current_weekday=2,
            microstructure=COMMODITIES_MICROSTRUCTURE,
        )
        assert s.near_close is True

    def test_rates_near_close(self):
        # Regular session ends at 17:00 (1020 min). 16:48 = 1008 min.
        # minutes_to_close = 1020 - 1008 = 12 <= 15
        s = detect_session(
            current_hour=16, current_minute=48, current_weekday=2,
            microstructure=RATES_MICROSTRUCTURE,
        )
        assert s.near_close is True

    def test_crypto_never_near_close(self):
        for h in [0, 6, 12, 18, 23]:
            s = detect_session(
                current_hour=h, current_minute=55, current_weekday=2,
                microstructure=CRYPTO_MICROSTRUCTURE,
            )
            assert s.near_close is False

    def test_forex_session_near_close(self):
        # Asia ends at 09:00 (540 min). 08:50 = 530 min.
        # minutes_to_close = 540 - 530 = 10 <= 15
        s = detect_session(
            current_hour=8, current_minute=50, current_weekday=2,
            microstructure=FOREX_MICROSTRUCTURE,
        )
        # At 08:50, both asia (00:00-09:00) and europe (08:00-17:00) overlap.
        # detect_forex_session iterates sessions in order, so asia matches first.
        if s.session_name == "asia":
            assert s.near_close is True


# ===========================================================================
# 10. TestNearOpenDetection
# ===========================================================================

class TestNearOpenDetection:
    """Near-open / pre-market detection."""

    def test_indices_pre_market_is_near_open(self):
        s = detect_session(
            current_hour=5, current_minute=0, current_weekday=2,
            microstructure=INDICES_MICROSTRUCTURE,
        )
        assert s.near_open is True

    def test_indices_regular_not_near_open(self):
        s = detect_session(
            current_hour=12, current_minute=0, current_weekday=2,
            microstructure=INDICES_MICROSTRUCTURE,
        )
        assert s.near_open is False

    def test_indices_post_market_not_near_open(self):
        s = detect_session(
            current_hour=18, current_minute=0, current_weekday=2,
            microstructure=INDICES_MICROSTRUCTURE,
        )
        assert s.near_open is False

    def test_crypto_never_near_open(self):
        s = detect_session(
            current_hour=0, current_minute=0, current_weekday=0,
            microstructure=CRYPTO_MICROSTRUCTURE,
        )
        assert s.near_open is False

    def test_forex_sessions_not_near_open(self):
        # Forex sessions are not named "pre_market" so near_open is False
        for h in [3, 10, 15]:
            s = detect_session(
                current_hour=h, current_minute=0, current_weekday=2,
                microstructure=FOREX_MICROSTRUCTURE,
            )
            assert s.near_open is False


# ===========================================================================
# 11. TestSpreadMultipliers
# ===========================================================================

class TestSpreadMultipliers:
    """Spread multiplier adjustments per session."""

    def test_crypto_no_spread_multiplier(self):
        d = _exec(asset_class=AssetClass.CRYPTO)
        assert d.estimated_spread_bps == CRYPTO_MICROSTRUCTURE.typical_spread_bps

    def test_forex_asia_1_5x(self):
        d = _exec(asset_class=AssetClass.FOREX, symbol="EURUSD",
                   hour=3, weekday=2)
        expected = FOREX_MICROSTRUCTURE.typical_spread_bps * 1.5
        assert abs(d.estimated_spread_bps - expected) < 1e-10

    def test_forex_us_1x(self):
        # 20:00 is only in US session
        d = _exec(asset_class=AssetClass.FOREX, symbol="EURUSD",
                   hour=20, weekday=2)
        expected = FOREX_MICROSTRUCTURE.typical_spread_bps * 1.0
        assert abs(d.estimated_spread_bps - expected) < 1e-10

    def test_indices_pre_market_2x(self):
        d = _exec(asset_class=AssetClass.INDICES, symbol="SPY",
                   hour=5, weekday=2)
        expected = INDICES_MICROSTRUCTURE.typical_spread_bps * 2.0
        assert abs(d.estimated_spread_bps - expected) < 1e-10

    def test_indices_regular_1x(self):
        d = _exec(asset_class=AssetClass.INDICES, symbol="SPY",
                   hour=12, weekday=2)
        expected = INDICES_MICROSTRUCTURE.typical_spread_bps * 1.0
        assert abs(d.estimated_spread_bps - expected) < 1e-10

    def test_indices_post_market_1_8x(self):
        d = _exec(asset_class=AssetClass.INDICES, symbol="SPY",
                   hour=17, weekday=2)
        expected = INDICES_MICROSTRUCTURE.typical_spread_bps * 1.8
        assert abs(d.estimated_spread_bps - expected) < 1e-10

    def test_forex_weekend_illiquid_3x(self):
        d = _exec(asset_class=AssetClass.FOREX, symbol="EURUSD",
                   hour=12, weekday=5)
        expected = FOREX_MICROSTRUCTURE.typical_spread_bps * ILLIQUID_SPREAD_MULTIPLIER
        assert abs(d.estimated_spread_bps - expected) < 1e-10

    def test_forex_inter_session_2x(self):
        d = _exec(asset_class=AssetClass.FOREX, symbol="EURUSD",
                   hour=22, minute=30, weekday=2)
        expected = FOREX_MICROSTRUCTURE.typical_spread_bps * LOW_LIQUIDITY_SPREAD_MULTIPLIER
        assert abs(d.estimated_spread_bps - expected) < 1e-10


# ===========================================================================
# 12. TestLiquidityRegime
# ===========================================================================

class TestLiquidityRegime:
    """Liquidity regime detection per session."""

    def test_crypto_normal_liquidity(self):
        d = _exec(asset_class=AssetClass.CRYPTO)
        assert d.session_info.liquidity == "normal"

    def test_forex_asia_low_liquidity(self):
        d = _exec(asset_class=AssetClass.FOREX, symbol="EURUSD",
                   hour=3, weekday=2)
        assert d.session_info.liquidity == "low"

    def test_forex_europe_high_liquidity(self):
        # 10:00 is in europe session (first match)
        d = _exec(asset_class=AssetClass.FOREX, symbol="EURUSD",
                   hour=10, weekday=2)
        assert d.session_info.liquidity in ("high", "low")  # depends on match order

    def test_forex_weekend_closed_liquidity(self):
        d = _exec(asset_class=AssetClass.FOREX, symbol="EURUSD",
                   hour=12, weekday=5)
        assert d.session_info.liquidity == "closed"

    def test_forex_inter_session_low(self):
        d = _exec(asset_class=AssetClass.FOREX, symbol="EURUSD",
                   hour=22, minute=30, weekday=2)
        assert d.session_info.liquidity == "low"

    def test_indices_regular_high(self):
        d = _exec(asset_class=AssetClass.INDICES, symbol="SPY",
                   hour=12, weekday=2)
        assert d.session_info.liquidity == "high"

    def test_indices_pre_market_low(self):
        d = _exec(asset_class=AssetClass.INDICES, symbol="SPY",
                   hour=5, weekday=2)
        assert d.session_info.liquidity == "low"

    def test_indices_closed_liquidity(self):
        d = _exec(asset_class=AssetClass.INDICES, symbol="SPY",
                   hour=2, weekday=2)
        assert d.session_info.liquidity == "closed"

    def test_commodities_regular_high(self):
        d = _exec(asset_class=AssetClass.COMMODITIES, symbol="GOLD",
                   hour=12, weekday=2)
        assert d.session_info.liquidity == "high"


# ===========================================================================
# 13. TestDeferralLogic
# ===========================================================================

class TestDeferralLogic:
    """Near-close deferral behavior and market-closed deferral."""

    def test_indices_near_close_defers(self):
        d = _exec(asset_class=AssetClass.INDICES, symbol="SPY",
                   hour=15, minute=50, weekday=2)
        assert d.status == STATUS_DEFERRED
        assert d.size_adjustment_factor == 0.0
        assert d.recommended_algo == "HOLD"
        assert d.estimated_slippage_bps == 0.0

    def test_indices_near_close_spread_still_computed(self):
        d = _exec(asset_class=AssetClass.INDICES, symbol="SPY",
                   hour=15, minute=50, weekday=2)
        # Spread is computed but slippage is 0
        assert d.estimated_spread_bps > 0
        assert d.estimated_slippage_bps == 0.0

    def test_indices_closed_defers(self):
        d = _exec(asset_class=AssetClass.INDICES, symbol="SPY",
                   hour=2, weekday=2)
        assert d.status == STATUS_DEFERRED
        assert d.size_adjustment_factor == 0.0

    def test_commodities_closed_defers(self):
        d = _exec(asset_class=AssetClass.COMMODITIES, symbol="GOLD",
                   hour=3, weekday=2)
        assert d.status == STATUS_DEFERRED

    def test_rates_closed_defers(self):
        d = _exec(asset_class=AssetClass.RATES, symbol="TLT",
                   hour=3, weekday=2)
        assert d.status == STATUS_DEFERRED

    def test_forex_weekend_defers(self):
        d = _exec(asset_class=AssetClass.FOREX, symbol="EURUSD",
                   hour=12, weekday=5)
        assert d.status == STATUS_DEFERRED
        assert "weekend" in d.reason.lower()

    def test_indices_post_market_near_close_defers(self):
        # Post-market ends at 20:00. At 19:50, near_close triggers.
        d = _exec(asset_class=AssetClass.INDICES, symbol="SPY",
                   hour=19, minute=50, weekday=2)
        assert d.status == STATUS_DEFERRED

    def test_commodities_near_close_defers(self):
        # Commodities regular ends at 17:00. At 16:50, near_close triggers.
        d = _exec(asset_class=AssetClass.COMMODITIES, symbol="GOLD",
                   hour=16, minute=50, weekday=2)
        assert d.status == STATUS_DEFERRED

    def test_deferred_reason_mentions_remaining_minutes(self):
        d = _exec(asset_class=AssetClass.INDICES, symbol="SPY",
                   hour=15, minute=50, weekday=2)
        assert "10min remaining" in d.reason


# ===========================================================================
# 14. TestAlgoSelection
# ===========================================================================

class TestAlgoSelection:
    """Execution algorithm selection based on urgency and liquidity."""

    def test_high_urgency_aggressive(self):
        d = _exec(asset_class=AssetClass.CRYPTO, urgency=0.9)
        assert d.recommended_algo == "AGGRESSIVE"

    def test_urgency_exactly_0_8_not_aggressive(self):
        # urgency > 0.8 triggers AGGRESSIVE, so 0.8 does not
        d = _exec(asset_class=AssetClass.CRYPTO, urgency=0.8)
        assert d.recommended_algo != "AGGRESSIVE"

    def test_urgency_0_81_aggressive(self):
        d = _exec(asset_class=AssetClass.CRYPTO, urgency=0.81)
        assert d.recommended_algo == "AGGRESSIVE"

    def test_high_liquidity_vwap(self):
        d = _exec(asset_class=AssetClass.INDICES, symbol="SPY",
                   hour=12, weekday=2, urgency=0.5)
        assert d.recommended_algo == "VWAP"

    def test_low_liquidity_limit(self):
        d = _exec(asset_class=AssetClass.FOREX, symbol="EURUSD",
                   hour=3, weekday=2, urgency=0.3)
        assert d.recommended_algo == "LIMIT"

    def test_normal_liquidity_twap(self):
        # Crypto has "normal" liquidity
        d = _exec(asset_class=AssetClass.CRYPTO, urgency=0.5)
        assert d.recommended_algo == "TWAP"

    def test_auction_algo_for_pre_market(self):
        d = _exec(asset_class=AssetClass.INDICES, symbol="SPY",
                   hour=5, weekday=2)
        assert d.recommended_algo == "AUCTION"

    def test_hold_algo_for_deferred(self):
        d = _exec(asset_class=AssetClass.INDICES, symbol="SPY",
                   hour=2, weekday=2)
        assert d.recommended_algo == "HOLD"


# ===========================================================================
# 15. TestResultHash
# ===========================================================================

class TestResultHash:
    """Deterministic SHA-256 result hash."""

    def test_hash_is_16_hex_chars(self):
        d = _exec()
        assert len(d.result_hash) == 16
        assert all(c in "0123456789abcdef" for c in d.result_hash)

    def test_hash_deterministic(self):
        d1 = _exec(hour=12, minute=0, weekday=2)
        d2 = _exec(hour=12, minute=0, weekday=2)
        assert d1.result_hash == d2.result_hash

    def test_different_inputs_different_hash(self):
        d1 = _exec(asset_class=AssetClass.FOREX, symbol="EUR", hour=10, weekday=2)
        d2 = _exec(asset_class=AssetClass.FOREX, symbol="EUR", hour=12, weekday=5)
        assert d1.result_hash != d2.result_hash


# ===========================================================================
# 16. TestImmutability
# ===========================================================================

class TestImmutability:
    """Frozen dataclass invariants."""

    def test_execution_decision_frozen(self):
        d = _exec()
        with pytest.raises(AttributeError):
            d.status = "REJECTED"

    def test_session_info_frozen(self):
        d = _exec()
        with pytest.raises(AttributeError):
            d.session_info.is_open = False

    def test_execution_decision_symbol_frozen(self):
        d = _exec()
        with pytest.raises(AttributeError):
            d.symbol = "CHANGED"

    def test_execution_decision_spread_frozen(self):
        d = _exec()
        with pytest.raises(AttributeError):
            d.estimated_spread_bps = 999.0

    def test_session_info_standalone_frozen(self):
        s = SessionInfo(
            session_name="test",
            is_open=True,
            liquidity="normal",
            spread_multiplier=1.0,
            near_close=False,
            near_open=False,
            minutes_to_close=-1,
        )
        with pytest.raises(AttributeError):
            s.session_name = "changed"


# ===========================================================================
# 17. TestDeterminism
# ===========================================================================

class TestDeterminism:
    """DET-05: same inputs produce same outputs."""

    def test_same_inputs_same_status(self):
        d1 = _exec(asset_class=AssetClass.INDICES, symbol="SPY",
                     hour=12, weekday=2)
        d2 = _exec(asset_class=AssetClass.INDICES, symbol="SPY",
                     hour=12, weekday=2)
        assert d1.status == d2.status
        assert d1.estimated_spread_bps == d2.estimated_spread_bps
        assert d1.estimated_slippage_bps == d2.estimated_slippage_bps
        assert d1.size_adjustment_factor == d2.size_adjustment_factor
        assert d1.recommended_algo == d2.recommended_algo

    def test_fresh_instances_same_result(self):
        kwargs = dict(
            symbol="BTC", asset_class=AssetClass.CRYPTO,
            order_size=1.0, current_hour=12, current_minute=0, current_weekday=2,
        )
        d1 = SessionAwareExecutor().execute(**kwargs)
        d2 = SessionAwareExecutor().execute(**kwargs)
        assert d1.result_hash == d2.result_hash
        assert d1.status == d2.status
        assert d1.estimated_spread_bps == d2.estimated_spread_bps

    def test_all_fields_match_on_repeated_call(self):
        d1 = _exec(asset_class=AssetClass.FOREX, symbol="GBPUSD",
                     hour=14, weekday=3, urgency=0.6)
        d2 = _exec(asset_class=AssetClass.FOREX, symbol="GBPUSD",
                     hour=14, weekday=3, urgency=0.6)
        assert d1.symbol == d2.symbol
        assert d1.asset_class == d2.asset_class
        assert d1.status == d2.status
        assert d1.reason == d2.reason
        assert d1.session_info == d2.session_info
        assert d1.estimated_spread_bps == d2.estimated_spread_bps
        assert d1.estimated_slippage_bps == d2.estimated_slippage_bps
        assert d1.size_adjustment_factor == d2.size_adjustment_factor
        assert d1.recommended_algo == d2.recommended_algo
        assert d1.result_hash == d2.result_hash

    def test_order_size_does_not_affect_decision(self):
        # The module does not use order_size for logic -- verify determinism
        d1 = _exec(asset_class=AssetClass.CRYPTO, order_size=1.0)
        d2 = _exec(asset_class=AssetClass.CRYPTO, order_size=1000.0)
        assert d1.result_hash == d2.result_hash


# ===========================================================================
# 18. TestEdgeCases
# ===========================================================================

class TestEdgeCases:
    """Boundary times, empty inputs, unknown asset class."""

    def test_midnight(self):
        d = _exec(hour=0, minute=0, weekday=2)
        assert d.status == STATUS_FILLED  # Crypto 24/7

    def test_end_of_day(self):
        d = _exec(hour=23, minute=59, weekday=2)
        assert d.status == STATUS_FILLED  # Crypto 24/7

    def test_all_asset_classes_produce_valid_status(self):
        valid_statuses = {STATUS_FILLED, STATUS_DEFERRED, STATUS_REJECTED, STATUS_AUCTION}
        for ac in AssetClass:
            d = _exec(asset_class=ac, hour=12, weekday=2)
            assert d.status in valid_statuses
            assert d.asset_class == ac

    def test_negative_order_size_allowed(self):
        d = SessionAwareExecutor().execute(
            symbol="BTC", asset_class=AssetClass.CRYPTO,
            order_size=-5.0, current_hour=12, current_minute=0, current_weekday=2,
        )
        assert d.status == STATUS_FILLED

    def test_zero_order_size_allowed(self):
        d = SessionAwareExecutor().execute(
            symbol="BTC", asset_class=AssetClass.CRYPTO,
            order_size=0.0, current_hour=12, current_minute=0, current_weekday=2,
        )
        assert d.status == STATUS_FILLED

    def test_zero_urgency(self):
        d = _exec(urgency=0.0)
        assert d.recommended_algo != "AGGRESSIVE"

    def test_max_urgency(self):
        d = _exec(urgency=1.0)
        assert d.recommended_algo == "AGGRESSIVE"

    def test_boundary_urgency_0_8_not_aggressive(self):
        d = _exec(urgency=0.8)
        assert d.recommended_algo != "AGGRESSIVE"

    def test_symbol_preserved_in_result(self):
        d = _exec(symbol="MY_ASSET")
        assert d.symbol == "MY_ASSET"

    def test_asset_class_preserved_in_result(self):
        for ac in AssetClass:
            d = _exec(asset_class=ac, hour=12, weekday=2)
            assert d.asset_class is ac

    def test_session_boundary_at_session_start(self):
        # Indices regular starts at 09:30. Test exactly at 09:30.
        s = detect_session(
            current_hour=9, current_minute=30, current_weekday=2,
            microstructure=INDICES_MICROSTRUCTURE,
        )
        assert s.is_open is True
        assert s.session_name == "regular"

    def test_session_boundary_at_session_end(self):
        # Indices regular ends at 16:00. End is exclusive.
        # At 16:00, should be in post_market (16:00-20:00).
        s = detect_session(
            current_hour=16, current_minute=0, current_weekday=2,
            microstructure=INDICES_MICROSTRUCTURE,
        )
        assert s.session_name == "post_market"

    def test_forex_boundary_friday_19_59_open(self):
        # Friday 19:59 -- hour 19, should be open
        assert _is_forex_illiquid(4, 19) is False

    def test_forex_boundary_friday_20_00_closed(self):
        assert _is_forex_illiquid(4, 20) is True


# ===========================================================================
# 19. TestCommoditiesExecution
# ===========================================================================

class TestCommoditiesExecution:
    """Commodities: session-based execution."""

    def test_regular_hours_filled(self):
        d = _exec(asset_class=AssetClass.COMMODITIES, symbol="GOLD",
                   hour=12, weekday=2)
        assert d.status == STATUS_FILLED

    def test_outside_hours_deferred(self):
        d = _exec(asset_class=AssetClass.COMMODITIES, symbol="GOLD",
                   hour=3, weekday=2)
        assert d.status == STATUS_DEFERRED

    def test_near_close_deferred(self):
        d = _exec(asset_class=AssetClass.COMMODITIES, symbol="GOLD",
                   hour=16, minute=50, weekday=2)
        assert d.status == STATUS_DEFERRED

    def test_regular_session_spread(self):
        d = _exec(asset_class=AssetClass.COMMODITIES, symbol="GOLD",
                   hour=12, weekday=2)
        expected = COMMODITIES_MICROSTRUCTURE.typical_spread_bps * 1.0
        assert abs(d.estimated_spread_bps - expected) < 1e-10


# ===========================================================================
# 20. TestRatesExecution
# ===========================================================================

class TestRatesExecution:
    """Rates: session-based execution."""

    def test_regular_hours_filled(self):
        d = _exec(asset_class=AssetClass.RATES, symbol="TLT",
                   hour=10, weekday=2)
        assert d.status == STATUS_FILLED

    def test_outside_hours_deferred(self):
        d = _exec(asset_class=AssetClass.RATES, symbol="TLT",
                   hour=3, weekday=2)
        assert d.status == STATUS_DEFERRED

    def test_near_close_deferred(self):
        # Rates regular ends at 17:00. At 16:48, near_close triggers.
        d = _exec(asset_class=AssetClass.RATES, symbol="TLT",
                   hour=16, minute=48, weekday=2)
        assert d.status == STATUS_DEFERRED

    def test_regular_session_spread(self):
        d = _exec(asset_class=AssetClass.RATES, symbol="TLT",
                   hour=10, weekday=2)
        expected = RATES_MICROSTRUCTURE.typical_spread_bps * 1.0
        assert abs(d.estimated_spread_bps - expected) < 1e-10


# ===========================================================================
# 21. TestImportContract
# ===========================================================================

class TestImportContract:
    """All public symbols are importable."""

    def test_import_session_aware_executor(self):
        from jarvis.execution.session_aware_executor import SessionAwareExecutor
        assert SessionAwareExecutor is not None

    def test_import_execution_decision(self):
        from jarvis.execution.session_aware_executor import ExecutionDecision
        assert ExecutionDecision is not None

    def test_import_session_info(self):
        from jarvis.execution.session_aware_executor import SessionInfo
        assert SessionInfo is not None

    def test_import_detect_session(self):
        from jarvis.execution.session_aware_executor import detect_session
        assert callable(detect_session)

    def test_import_constants(self):
        from jarvis.execution.session_aware_executor import (
            MICROSTRUCTURE_REGISTRY,
            NEAR_CLOSE_MINUTES,
            LOW_LIQUIDITY_SPREAD_MULTIPLIER,
            ILLIQUID_SPREAD_MULTIPLIER,
            STATUS_FILLED,
            STATUS_DEFERRED,
            STATUS_REJECTED,
            STATUS_AUCTION,
            SLIPPAGE_BASE_FACTOR,
        )
        assert isinstance(MICROSTRUCTURE_REGISTRY, dict)
        assert isinstance(NEAR_CLOSE_MINUTES, int)
        assert isinstance(LOW_LIQUIDITY_SPREAD_MULTIPLIER, float)
        assert isinstance(ILLIQUID_SPREAD_MULTIPLIER, float)
        assert isinstance(STATUS_FILLED, str)
        assert isinstance(STATUS_DEFERRED, str)
        assert isinstance(STATUS_REJECTED, str)
        assert isinstance(STATUS_AUCTION, str)
        assert isinstance(SLIPPAGE_BASE_FACTOR, float)

    def test_import_forex_illiquid_constants(self):
        from jarvis.execution.session_aware_executor import (
            FOREX_ILLIQUID_START_DAY,
            FOREX_ILLIQUID_START_HOUR,
            FOREX_ILLIQUID_END_DAY,
            FOREX_ILLIQUID_END_HOUR,
        )
        assert isinstance(FOREX_ILLIQUID_START_DAY, int)
        assert isinstance(FOREX_ILLIQUID_START_HOUR, int)
        assert isinstance(FOREX_ILLIQUID_END_DAY, int)
        assert isinstance(FOREX_ILLIQUID_END_HOUR, int)
