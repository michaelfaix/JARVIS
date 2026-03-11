# =============================================================================
# tests/unit/execution/test_session_aware_executor.py
#
# Comprehensive tests for jarvis/execution/session_aware_executor.py (MA-6).
# Covers: constants, session detection, per-asset-class execution logic,
#         forex illiquid period, indices auction/defer, algo selection,
#         determinism, immutability, edge cases.
# =============================================================================

import pytest

from jarvis.core.regime import AssetClass
from jarvis.core.data_structures import (
    CRYPTO_MICROSTRUCTURE,
    FOREX_MICROSTRUCTURE,
    INDICES_MICROSTRUCTURE,
    COMMODITIES_MICROSTRUCTURE,
    RATES_MICROSTRUCTURE,
)
from jarvis.execution.session_aware_executor import (
    # Constants
    MICROSTRUCTURE_REGISTRY,
    NEAR_CLOSE_MINUTES,
    LOW_LIQUIDITY_SPREAD_MULTIPLIER,
    ILLIQUID_SPREAD_MULTIPLIER,
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
# SHARED FIXTURES
# ---------------------------------------------------------------------------

def _exec(asset_class=AssetClass.CRYPTO, symbol="BTC", hour=14, minute=0,
          weekday=2, urgency=0.5, **kwargs):
    """Helper to call executor with defaults."""
    return SessionAwareExecutor().execute(
        symbol=symbol,
        asset_class=asset_class,
        order_size=1.0,
        current_hour=hour,
        current_minute=minute,
        current_weekday=weekday,
        urgency=urgency,
        **kwargs,
    )


# ---------------------------------------------------------------------------
# CONSTANTS (DET-06)
# ---------------------------------------------------------------------------

class TestConstants:
    def test_registry_all_classes(self):
        for ac in AssetClass:
            assert ac in MICROSTRUCTURE_REGISTRY

    def test_near_close_minutes(self):
        assert NEAR_CLOSE_MINUTES == 15

    def test_low_liquidity_multiplier(self):
        assert LOW_LIQUIDITY_SPREAD_MULTIPLIER == 2.0

    def test_illiquid_multiplier(self):
        assert ILLIQUID_SPREAD_MULTIPLIER == 3.0

    def test_slippage_factor(self):
        assert SLIPPAGE_BASE_FACTOR == 0.5


# ---------------------------------------------------------------------------
# TIME HELPERS
# ---------------------------------------------------------------------------

class TestTimeHelpers:
    def test_parse_time(self):
        assert _parse_time("09:30") == (9, 30)
        assert _parse_time("00:00") == (0, 0)
        assert _parse_time("23:59") == (23, 59)

    def test_time_to_minutes(self):
        assert _time_to_minutes(0, 0) == 0
        assert _time_to_minutes(9, 30) == 570
        assert _time_to_minutes(16, 0) == 960
        assert _time_to_minutes(23, 59) == 1439

    def test_is_in_session_normal(self):
        assert _is_in_session(600, 570, 960) is True   # 10:00 in 9:30-16:00
        assert _is_in_session(500, 570, 960) is False   # 8:20 before 9:30
        assert _is_in_session(960, 570, 960) is False   # 16:00 = end, exclusive

    def test_is_in_session_overnight(self):
        # Session from 22:00 (1320) to 06:00 (360)
        assert _is_in_session(1380, 1320, 360) is True   # 23:00
        assert _is_in_session(120, 1320, 360) is True     # 02:00
        assert _is_in_session(600, 1320, 360) is False    # 10:00

    def test_minutes_until_end(self):
        assert _minutes_until_end(570, 960) == 390   # 9:30 to 16:00
        assert _minutes_until_end(950, 960) == 10    # 15:50 to 16:00
        assert _minutes_until_end(960, 960) == 1440  # Edge: at end -> wraps


# ---------------------------------------------------------------------------
# FOREX ILLIQUID DETECTION
# ---------------------------------------------------------------------------

class TestForexIlliquid:
    def test_friday_before_20_open(self):
        assert _is_forex_illiquid(4, 19) is False

    def test_friday_20_illiquid(self):
        assert _is_forex_illiquid(4, 20) is True

    def test_saturday_always_illiquid(self):
        assert _is_forex_illiquid(5, 0) is True
        assert _is_forex_illiquid(5, 12) is True
        assert _is_forex_illiquid(5, 23) is True

    def test_sunday_before_22_illiquid(self):
        assert _is_forex_illiquid(6, 0) is True
        assert _is_forex_illiquid(6, 21) is True

    def test_sunday_22_open(self):
        assert _is_forex_illiquid(6, 22) is False

    def test_weekday_open(self):
        assert _is_forex_illiquid(0, 12) is False  # Monday
        assert _is_forex_illiquid(1, 8) is False   # Tuesday
        assert _is_forex_illiquid(3, 15) is False  # Thursday


# ---------------------------------------------------------------------------
# DETECT SESSION
# ---------------------------------------------------------------------------

class TestDetectSession:
    def test_crypto_always_open(self):
        s = detect_session(
            current_hour=3, current_minute=30, current_weekday=5,
            microstructure=CRYPTO_MICROSTRUCTURE,
        )
        assert s.is_open is True
        assert s.session_name == "continuous"

    def test_forex_asia_session(self):
        s = detect_session(
            current_hour=3, current_minute=0, current_weekday=2,
            microstructure=FOREX_MICROSTRUCTURE,
        )
        assert s.is_open is True
        assert s.session_name == "asia"
        assert s.liquidity == "low"

    def test_forex_europe_session(self):
        s = detect_session(
            current_hour=10, current_minute=0, current_weekday=2,
            microstructure=FOREX_MICROSTRUCTURE,
        )
        assert s.is_open is True
        # Could be europe or us overlap depending on session definitions
        assert s.session_name in ("europe", "us")

    def test_forex_weekend_closed(self):
        s = detect_session(
            current_hour=12, current_minute=0, current_weekday=5,
            microstructure=FOREX_MICROSTRUCTURE,
        )
        assert s.is_open is False
        assert s.session_name == "weekend_closed"

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

    def test_indices_closed_overnight(self):
        s = detect_session(
            current_hour=2, current_minute=0, current_weekday=2,
            microstructure=INDICES_MICROSTRUCTURE,
        )
        assert s.is_open is False
        assert s.session_name == "closed"

    def test_indices_near_close(self):
        # Regular session ends at 16:00, near_close = within 15 min
        s = detect_session(
            current_hour=15, current_minute=50, current_weekday=2,
            microstructure=INDICES_MICROSTRUCTURE,
        )
        assert s.near_close is True
        assert s.minutes_to_close == 10

    def test_commodities_regular(self):
        s = detect_session(
            current_hour=12, current_minute=0, current_weekday=1,
            microstructure=COMMODITIES_MICROSTRUCTURE,
        )
        assert s.is_open is True
        assert s.session_name == "regular"

    def test_rates_regular(self):
        s = detect_session(
            current_hour=10, current_minute=0, current_weekday=1,
            microstructure=RATES_MICROSTRUCTURE,
        )
        assert s.is_open is True
        assert s.session_name == "regular"


# ---------------------------------------------------------------------------
# CRYPTO EXECUTION
# ---------------------------------------------------------------------------

class TestCryptoExecution:
    def test_always_filled(self):
        d = _exec(asset_class=AssetClass.CRYPTO, hour=3, weekday=6)
        assert d.status == STATUS_FILLED
        assert d.size_adjustment_factor == 1.0

    def test_any_time_of_day(self):
        for h in [0, 6, 12, 18, 23]:
            d = _exec(asset_class=AssetClass.CRYPTO, hour=h)
            assert d.status == STATUS_FILLED

    def test_spread_matches_micro(self):
        d = _exec(asset_class=AssetClass.CRYPTO)
        assert d.estimated_spread_bps == CRYPTO_MICROSTRUCTURE.typical_spread_bps

    def test_slippage_is_half_spread(self):
        d = _exec(asset_class=AssetClass.CRYPTO)
        expected = CRYPTO_MICROSTRUCTURE.typical_spread_bps * SLIPPAGE_BASE_FACTOR
        assert abs(d.estimated_slippage_bps - expected) < 1e-10


# ---------------------------------------------------------------------------
# FOREX EXECUTION
# ---------------------------------------------------------------------------

class TestForexExecution:
    def test_europe_session_filled(self):
        d = _exec(asset_class=AssetClass.FOREX, symbol="EURUSD",
                   hour=10, weekday=2)
        assert d.status == STATUS_FILLED

    def test_asia_low_liquidity(self):
        d = _exec(asset_class=AssetClass.FOREX, symbol="EURUSD",
                   hour=3, weekday=2)
        assert d.status == STATUS_FILLED
        assert d.size_adjustment_factor == 0.7  # Reduced in low liquidity
        assert "Low liquidity" in d.reason

    def test_weekend_deferred(self):
        d = _exec(asset_class=AssetClass.FOREX, symbol="EURUSD",
                   hour=12, weekday=5)  # Saturday
        assert d.status == STATUS_DEFERRED
        assert d.size_adjustment_factor == 0.0

    def test_friday_evening_deferred(self):
        d = _exec(asset_class=AssetClass.FOREX, symbol="EURUSD",
                   hour=21, weekday=4)  # Friday 21:00
        assert d.status == STATUS_DEFERRED

    def test_sunday_evening_open(self):
        d = _exec(asset_class=AssetClass.FOREX, symbol="EURUSD",
                   hour=23, weekday=6)  # Sunday 23:00 (after 22:00)
        assert d.status == STATUS_FILLED


# ---------------------------------------------------------------------------
# INDICES EXECUTION
# ---------------------------------------------------------------------------

class TestIndicesExecution:
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

    def test_post_market_filled(self):
        d = _exec(asset_class=AssetClass.INDICES, symbol="SPY",
                   hour=17, weekday=2)
        assert d.status == STATUS_FILLED
        assert d.session_info.session_name == "post_market"


# ---------------------------------------------------------------------------
# COMMODITIES / RATES EXECUTION
# ---------------------------------------------------------------------------

class TestCommoditiesExecution:
    def test_regular_hours_filled(self):
        d = _exec(asset_class=AssetClass.COMMODITIES, symbol="GOLD",
                   hour=12, weekday=2)
        assert d.status == STATUS_FILLED

    def test_outside_hours_deferred(self):
        d = _exec(asset_class=AssetClass.COMMODITIES, symbol="GOLD",
                   hour=3, weekday=2)
        assert d.status == STATUS_DEFERRED


class TestRatesExecution:
    def test_regular_hours_filled(self):
        d = _exec(asset_class=AssetClass.RATES, symbol="TLT",
                   hour=10, weekday=2)
        assert d.status == STATUS_FILLED

    def test_outside_hours_deferred(self):
        d = _exec(asset_class=AssetClass.RATES, symbol="TLT",
                   hour=3, weekday=2)
        assert d.status == STATUS_DEFERRED


# ---------------------------------------------------------------------------
# ALGO SELECTION
# ---------------------------------------------------------------------------

class TestAlgoSelection:
    def test_high_urgency_aggressive(self):
        d = _exec(asset_class=AssetClass.CRYPTO, urgency=0.9)
        assert d.recommended_algo == "AGGRESSIVE"

    def test_high_liquidity_vwap(self):
        d = _exec(asset_class=AssetClass.INDICES, symbol="SPY",
                   hour=12, weekday=2, urgency=0.5)
        assert d.recommended_algo == "VWAP"

    def test_low_liquidity_limit(self):
        d = _exec(asset_class=AssetClass.FOREX, symbol="EURUSD",
                   hour=3, weekday=2, urgency=0.3)
        assert d.recommended_algo == "LIMIT"


# ---------------------------------------------------------------------------
# SPREAD AND SLIPPAGE
# ---------------------------------------------------------------------------

class TestSpreadSlippage:
    def test_spread_multiplier_applied(self):
        # Asia forex session has 1.5x spread multiplier
        d = _exec(asset_class=AssetClass.FOREX, symbol="EURUSD",
                   hour=3, weekday=2)
        expected_spread = FOREX_MICROSTRUCTURE.typical_spread_bps * 1.5
        assert abs(d.estimated_spread_bps - expected_spread) < 1e-10

    def test_pre_market_spread_multiplier(self):
        d = _exec(asset_class=AssetClass.INDICES, symbol="SPY",
                   hour=5, weekday=2)
        expected_spread = INDICES_MICROSTRUCTURE.typical_spread_bps * 2.0
        assert abs(d.estimated_spread_bps - expected_spread) < 1e-10

    def test_auction_slippage_premium(self):
        d = _exec(asset_class=AssetClass.INDICES, symbol="SPY",
                   hour=5, weekday=2)
        base_spread = INDICES_MICROSTRUCTURE.typical_spread_bps * 2.0
        expected_slippage = base_spread * SLIPPAGE_BASE_FACTOR * 1.5
        assert abs(d.estimated_slippage_bps - expected_slippage) < 1e-10


# ---------------------------------------------------------------------------
# RESULT HASH
# ---------------------------------------------------------------------------

class TestResultHash:
    def test_hash_hex(self):
        d = _exec()
        assert len(d.result_hash) == 16
        assert all(c in "0123456789abcdef" for c in d.result_hash)


# ---------------------------------------------------------------------------
# IMMUTABILITY
# ---------------------------------------------------------------------------

class TestImmutability:
    def test_decision_frozen(self):
        d = _exec()
        with pytest.raises(AttributeError):
            d.status = "REJECTED"

    def test_session_info_frozen(self):
        d = _exec()
        with pytest.raises(AttributeError):
            d.session_info.is_open = False


# ---------------------------------------------------------------------------
# DETERMINISM (DET-05)
# ---------------------------------------------------------------------------

class TestDeterminism:
    def test_same_inputs_same_hash(self):
        d1 = _exec(hour=12, minute=0, weekday=2)
        d2 = _exec(hour=12, minute=0, weekday=2)
        assert d1.result_hash == d2.result_hash

    def test_same_status(self):
        d1 = _exec(asset_class=AssetClass.INDICES, symbol="SPY",
                     hour=12, weekday=2)
        d2 = _exec(asset_class=AssetClass.INDICES, symbol="SPY",
                     hour=12, weekday=2)
        assert d1.status == d2.status
        assert d1.estimated_spread_bps == d2.estimated_spread_bps

    def test_different_time_different_hash(self):
        d1 = _exec(hour=12, weekday=2)
        d2 = _exec(hour=3, weekday=5)
        # Different times may produce different sessions/statuses
        # (crypto: same hash since always filled; test with forex)
        d3 = _exec(asset_class=AssetClass.FOREX, symbol="EUR", hour=10, weekday=2)
        d4 = _exec(asset_class=AssetClass.FOREX, symbol="EUR", hour=12, weekday=5)
        assert d3.result_hash != d4.result_hash

    def test_fresh_instance_same_result(self):
        d1 = SessionAwareExecutor().execute(
            symbol="BTC", asset_class=AssetClass.CRYPTO,
            order_size=1.0, current_hour=12, current_minute=0, current_weekday=2,
        )
        d2 = SessionAwareExecutor().execute(
            symbol="BTC", asset_class=AssetClass.CRYPTO,
            order_size=1.0, current_hour=12, current_minute=0, current_weekday=2,
        )
        assert d1.result_hash == d2.result_hash


# ---------------------------------------------------------------------------
# EDGE CASES
# ---------------------------------------------------------------------------

class TestEdgeCases:
    def test_midnight(self):
        d = _exec(hour=0, minute=0, weekday=2)
        assert d.status == STATUS_FILLED  # Crypto 24/7

    def test_end_of_day(self):
        d = _exec(hour=23, minute=59, weekday=2)
        assert d.status == STATUS_FILLED  # Crypto 24/7

    def test_all_asset_classes_produce_result(self):
        for ac in AssetClass:
            d = _exec(asset_class=ac, hour=12, weekday=2)
            assert d.status in (STATUS_FILLED, STATUS_DEFERRED,
                                STATUS_REJECTED, STATUS_AUCTION)
            assert d.asset_class == ac

    def test_negative_order_size(self):
        d = SessionAwareExecutor().execute(
            symbol="BTC", asset_class=AssetClass.CRYPTO,
            order_size=-5.0, current_hour=12, current_minute=0, current_weekday=2,
        )
        assert d.status == STATUS_FILLED

    def test_zero_urgency(self):
        d = _exec(urgency=0.0)
        assert d.recommended_algo != "AGGRESSIVE"

    def test_max_urgency(self):
        d = _exec(urgency=1.0)
        assert d.recommended_algo == "AGGRESSIVE"


# ---------------------------------------------------------------------------
# PACKAGE IMPORT
# ---------------------------------------------------------------------------

class TestPackageImport:
    def test_import_all(self):
        from jarvis.execution.session_aware_executor import (
            SessionAwareExecutor,
            ExecutionDecision,
            SessionInfo,
            detect_session,
        )
        assert SessionAwareExecutor is not None
        assert detect_session is not None
