# tests/unit/core/test_live_data_integrity_gate.py
# Coverage target: jarvis/core/live_data_integrity_gate.py -> 95%+
# Tests all 5 checks, gate orchestrator, constants, data types, edge cases.

import math
import pytest

from jarvis.core.live_data_integrity_gate import (
    VALID_OPERATING_MODES,
    GAP_MULTIPLIERS,
    OUTLIER_Z_THRESHOLD,
    OUTLIER_WINDOW,
    OUTLIER_QUALITY_PENALTY,
    SPREAD_ANOMALY_FACTOR,
    VALID_SESSION_TAGS_PER_ASSET_CLASS,
    CheckResult,
    GateVerdict,
    IntegrityViolation,
    check_missing_data,
    check_timestamp_continuity,
    check_spread_anomaly,
    check_outlier_filter,
    check_asset_class,
    run_integrity_gate,
)


# =============================================================================
# Helpers
# =============================================================================

def _gate(**kwargs):
    """Build run_integrity_gate call with sensible defaults."""
    defaults = dict(
        operating_mode="live_analytical",
        open_=100.0,
        high=105.0,
        low=95.0,
        close=102.0,
        volume=1000.0,
        quality_score=0.9,
        spread_bps=5.0,
        max_entry_spread_bps=10.0,
        asset_class="crypto",
        session_tag="CRYPTO_24_7",
        prev_sequence_id=1,
        curr_sequence_id=2,
        time_gap_seconds=60.0,
        timeframe_seconds=60.0,
        rolling_closes=None,
    )
    defaults.update(kwargs)
    return run_integrity_gate(**defaults)


# =============================================================================
# Constants
# =============================================================================

class TestConstants:
    def test_valid_operating_modes(self):
        assert VALID_OPERATING_MODES == ("historical", "live_analytical", "hybrid")

    def test_gap_multipliers_keys(self):
        assert set(GAP_MULTIPLIERS.keys()) == {
            "crypto", "forex", "indices", "commodities", "rates",
        }

    def test_gap_multiplier_values(self):
        assert GAP_MULTIPLIERS["crypto"] == 2
        assert GAP_MULTIPLIERS["forex"] == 5
        assert GAP_MULTIPLIERS["indices"] == 1
        assert GAP_MULTIPLIERS["commodities"] == 3

    def test_outlier_z_threshold(self):
        assert OUTLIER_Z_THRESHOLD == 5.0

    def test_outlier_window(self):
        assert OUTLIER_WINDOW == 20

    def test_outlier_quality_penalty(self):
        assert OUTLIER_QUALITY_PENALTY == 0.30

    def test_spread_anomaly_factor(self):
        assert SPREAD_ANOMALY_FACTOR == 2.0

    def test_valid_session_tags_per_asset_class(self):
        assert "CRYPTO_24_7" in VALID_SESSION_TAGS_PER_ASSET_CLASS["crypto"]
        assert "LONDON" in VALID_SESSION_TAGS_PER_ASSET_CLASS["forex"]
        assert "NEW_YORK" in VALID_SESSION_TAGS_PER_ASSET_CLASS["indices"]


# =============================================================================
# Data Types
# =============================================================================

class TestIntegrityViolation:
    def test_construction(self):
        v = IntegrityViolation(
            check_name="missing_data",
            failure_mode="FM-03",
            field_name="close",
            message="close is None",
        )
        assert v.check_name == "missing_data"
        assert v.failure_mode == "FM-03"
        assert v.field_name == "close"

    def test_frozen(self):
        v = IntegrityViolation("a", "FM-03", "b", "c")
        with pytest.raises(AttributeError):
            v.check_name = "x"


class TestCheckResult:
    def test_passed(self):
        cr = CheckResult(passed=True, degraded=False, violations=[], quality_penalty=0.0)
        assert cr.passed is True
        assert cr.degraded is False

    def test_frozen(self):
        cr = CheckResult(passed=True, degraded=False, violations=[], quality_penalty=0.0)
        with pytest.raises(AttributeError):
            cr.passed = False


class TestGateVerdict:
    def test_construction(self):
        gv = GateVerdict(
            admitted=True,
            operating_mode="live_analytical",
            quality_score_adj=0.9,
            is_stale=False,
            spread_flagged=False,
            violations=[],
            checks_passed=5,
            reason="all good",
        )
        assert gv.admitted is True
        assert gv.checks_total == 5

    def test_frozen(self):
        gv = GateVerdict(
            admitted=True, operating_mode="live_analytical",
            quality_score_adj=0.9, is_stale=False, spread_flagged=False,
            violations=[], checks_passed=5,
        )
        with pytest.raises(AttributeError):
            gv.admitted = False


# =============================================================================
# CHECK 1 -- Missing Data
# =============================================================================

class TestCheckMissingData:
    def test_all_valid(self):
        r = check_missing_data(100.0, 105.0, 95.0, 102.0, 1000.0)
        assert r.passed is True
        assert r.violations == []

    def test_none_field(self):
        r = check_missing_data(None, 105.0, 95.0, 102.0, 1000.0)
        assert r.passed is False
        assert len(r.violations) == 1
        assert r.violations[0].field_name == "open"
        assert r.violations[0].failure_mode == "FM-03"

    def test_nan_field(self):
        r = check_missing_data(100.0, float("nan"), 95.0, 102.0, 1000.0)
        assert r.passed is False
        assert r.violations[0].field_name == "high"

    def test_inf_field(self):
        r = check_missing_data(100.0, 105.0, float("inf"), 102.0, 1000.0)
        assert r.passed is False
        assert r.violations[0].field_name == "low"

    def test_negative_inf(self):
        r = check_missing_data(100.0, 105.0, 95.0, float("-inf"), 1000.0)
        assert r.passed is False
        assert r.violations[0].field_name == "close"

    def test_zero_volume(self):
        r = check_missing_data(100.0, 105.0, 95.0, 102.0, 0.0)
        assert r.passed is False
        assert r.violations[0].field_name == "volume"

    def test_negative_price(self):
        r = check_missing_data(-1.0, 105.0, 95.0, 102.0, 1000.0)
        assert r.passed is False
        assert r.violations[0].field_name == "open"

    def test_multiple_invalid(self):
        r = check_missing_data(None, float("nan"), -1.0, 0.0, float("inf"))
        assert r.passed is False
        assert len(r.violations) == 5

    def test_string_field(self):
        r = check_missing_data("abc", 105.0, 95.0, 102.0, 1000.0)
        assert r.passed is False
        assert "not numeric" in r.violations[0].message

    def test_int_values_valid(self):
        r = check_missing_data(100, 105, 95, 102, 1000)
        assert r.passed is True


# =============================================================================
# CHECK 2 -- Timestamp Continuity
# =============================================================================

class TestCheckTimestampContinuity:
    def test_normal_sequence(self):
        r = check_timestamp_continuity(1, 2, 60.0, 60.0, "crypto")
        assert r.passed is True
        assert r.violations == []

    def test_first_tick_none_prev(self):
        r = check_timestamp_continuity(None, 1, 60.0, 60.0, "crypto")
        assert r.passed is True

    def test_sequence_regression(self):
        r = check_timestamp_continuity(5, 3, 60.0, 60.0, "crypto")
        assert r.passed is False
        assert r.violations[0].field_name == "sequence_id"
        assert r.violations[0].failure_mode == "FM-03"

    def test_sequence_duplicate(self):
        r = check_timestamp_continuity(5, 5, 60.0, 60.0, "crypto")
        assert r.passed is False

    def test_gap_exceeds_crypto_threshold(self):
        # crypto: 2 * 60 = 120s max gap
        r = check_timestamp_continuity(1, 2, 130.0, 60.0, "crypto")
        assert r.passed is False
        assert any(v.field_name == "time_gap" for v in r.violations)

    def test_gap_within_crypto_threshold(self):
        r = check_timestamp_continuity(1, 2, 110.0, 60.0, "crypto")
        assert r.passed is True

    def test_gap_exceeds_indices_threshold(self):
        # indices: 1 * 60 = 60s max gap
        r = check_timestamp_continuity(1, 2, 65.0, 60.0, "indices")
        assert r.passed is False

    def test_gap_within_forex_threshold(self):
        # forex: 5 * 60 = 300s max gap
        r = check_timestamp_continuity(1, 2, 290.0, 60.0, "forex")
        assert r.passed is True

    def test_gap_exceeds_commodities_threshold(self):
        # commodities: 3 * 3600 = 10800s max gap
        r = check_timestamp_continuity(1, 2, 11000.0, 3600.0, "commodities")
        assert r.passed is False

    def test_both_regression_and_gap(self):
        r = check_timestamp_continuity(5, 3, 200.0, 60.0, "crypto")
        assert r.passed is False
        assert len(r.violations) == 2


# =============================================================================
# CHECK 3 -- Spread Anomaly
# =============================================================================

class TestCheckSpreadAnomaly:
    def test_normal_spread(self):
        r = check_spread_anomaly(5.0, 10.0)
        assert r.passed is True
        assert r.degraded is False
        assert r.violations == []

    def test_spread_at_threshold(self):
        # threshold = 10 * 2.0 = 20.0; spread_bps = 20.0 -> flagged
        r = check_spread_anomaly(20.0, 10.0)
        assert r.passed is True
        assert r.degraded is True
        assert r.violations[0].failure_mode == "FM-06"

    def test_spread_above_threshold(self):
        r = check_spread_anomaly(25.0, 10.0)
        assert r.passed is True
        assert r.degraded is True

    def test_spread_just_below_threshold(self):
        r = check_spread_anomaly(19.99, 10.0)
        assert r.passed is True
        assert r.degraded is False

    def test_spread_nan(self):
        r = check_spread_anomaly(float("nan"), 10.0)
        assert r.passed is False
        assert r.violations[0].failure_mode == "FM-03"

    def test_spread_inf(self):
        r = check_spread_anomaly(float("inf"), 10.0)
        assert r.passed is False

    def test_spread_none(self):
        r = check_spread_anomaly(None, 10.0)
        assert r.passed is False

    def test_zero_spread_valid(self):
        r = check_spread_anomaly(0.0, 10.0)
        assert r.passed is True
        assert r.degraded is False


# =============================================================================
# CHECK 4 -- Outlier Filter
# =============================================================================

class TestCheckOutlierFilter:
    def test_insufficient_history(self):
        r = check_outlier_filter(100.0, [100.0] * 10)
        assert r.passed is True
        assert r.degraded is False
        assert r.quality_penalty == 0.0

    def test_empty_history(self):
        r = check_outlier_filter(100.0, [])
        assert r.passed is True

    def test_normal_close_within_z(self):
        # 20 identical values: median=100, MAD=0 -> close=100 is fine
        r = check_outlier_filter(100.0, [100.0] * 20)
        assert r.passed is True
        assert r.degraded is False

    def test_outlier_detected(self):
        # 20 values around 100, close = 1000 (extreme outlier)
        closes = [100.0 + i * 0.1 for i in range(20)]
        r = check_outlier_filter(1000.0, closes)
        assert r.passed is True
        assert r.degraded is True
        assert r.quality_penalty == OUTLIER_QUALITY_PENALTY
        assert r.violations[0].failure_mode == "FM-03"

    def test_non_outlier_close(self):
        closes = [100.0 + i * 0.1 for i in range(20)]
        r = check_outlier_filter(101.0, closes)
        assert r.passed is True
        assert r.degraded is False

    def test_mad_zero_different_close(self):
        # All 20 values identical, close differs -> outlier
        r = check_outlier_filter(200.0, [100.0] * 20)
        assert r.passed is True
        assert r.degraded is True
        assert r.quality_penalty == OUTLIER_QUALITY_PENALTY

    def test_mad_zero_same_close(self):
        # All values and close identical -> not an outlier
        r = check_outlier_filter(100.0, [100.0] * 20)
        assert r.passed is True
        assert r.degraded is False

    def test_uses_last_window_values(self):
        # 30 values, but only last 20 used
        closes = [100.0] * 10 + [200.0 + i * 0.1 for i in range(20)]
        r = check_outlier_filter(201.0, closes)
        assert r.passed is True
        assert r.degraded is False

    def test_borderline_z_score(self):
        # Create values where z-score is exactly at threshold
        # median of [1..20] = 10.5, MAD = 5.0
        # z = |close - 10.5| / 5.0 -> for z >= 5.0: close >= 35.5
        closes = list(range(1, 21))
        closes_float = [float(c) for c in closes]
        r = check_outlier_filter(35.5, closes_float)
        assert r.degraded is True

    def test_just_below_z_threshold(self):
        closes = [float(c) for c in range(1, 21)]
        # z = |close - 10.5| / 5.0 < 5.0 -> close < 35.5
        r = check_outlier_filter(35.0, closes)
        assert r.degraded is False


# =============================================================================
# CHECK 5 -- Asset Class
# =============================================================================

class TestCheckAssetClass:
    def test_valid_crypto(self):
        r = check_asset_class("crypto", "CRYPTO_24_7")
        assert r.passed is True
        assert r.violations == []

    def test_valid_forex_london(self):
        r = check_asset_class("forex", "LONDON")
        assert r.passed is True

    def test_valid_indices_new_york(self):
        r = check_asset_class("indices", "NEW_YORK")
        assert r.passed is True

    def test_invalid_asset_class(self):
        r = check_asset_class("options", "LONDON")
        assert r.passed is False
        assert r.violations[0].failure_mode == "FM-03"
        assert r.violations[0].field_name == "asset_class"

    def test_invalid_session_tag_for_asset_class(self):
        # CRYPTO_24_7 not valid for forex
        r = check_asset_class("forex", "CRYPTO_24_7")
        assert r.passed is False
        assert r.violations[0].field_name == "session_tag"

    def test_unknown_session_tag(self):
        r = check_asset_class("crypto", "MARS_SESSION")
        assert r.passed is False
        assert r.violations[0].field_name == "session_tag"

    def test_commodities_tokyo(self):
        r = check_asset_class("commodities", "TOKYO")
        assert r.passed is True

    def test_rates_london(self):
        r = check_asset_class("rates", "LONDON")
        assert r.passed is True

    def test_indices_pre_market(self):
        r = check_asset_class("indices", "PRE_MARKET")
        assert r.passed is True

    def test_indices_auction(self):
        r = check_asset_class("indices", "AUCTION")
        assert r.passed is True


# =============================================================================
# run_integrity_gate -- Historical bypass
# =============================================================================

class TestGateHistorical:
    def test_always_admitted(self):
        v = _gate(operating_mode="historical")
        assert v.admitted is True
        assert v.checks_passed == 5
        assert v.violations == []
        assert "historical" in v.reason

    def test_historical_ignores_bad_data(self):
        v = _gate(
            operating_mode="historical",
            open_=float("nan"),
            quality_score=0.1,
        )
        assert v.admitted is True


# =============================================================================
# run_integrity_gate -- Validation
# =============================================================================

class TestGateValidation:
    def test_invalid_mode_raises_value_error(self):
        with pytest.raises(ValueError, match="operating_mode"):
            _gate(operating_mode="bad_mode")

    def test_non_string_mode_raises_type_error(self):
        with pytest.raises(TypeError, match="operating_mode"):
            _gate(operating_mode=42)


# =============================================================================
# run_integrity_gate -- Live mode, all checks pass
# =============================================================================

class TestGateAllPass:
    def test_clean_data_admitted(self):
        v = _gate()
        assert v.admitted is True
        assert v.checks_passed == 5
        assert v.violations == []
        assert v.is_stale is False
        assert v.spread_flagged is False
        assert v.quality_score_adj == 0.9
        assert "all 5 checks passed" in v.reason

    def test_hybrid_mode_runs_checks(self):
        v = _gate(operating_mode="hybrid")
        assert v.admitted is True
        assert v.operating_mode == "hybrid"


# =============================================================================
# run_integrity_gate -- CHECK 1 failure rejects
# =============================================================================

class TestGateMissingDataReject:
    def test_nan_close_rejects(self):
        v = _gate(close=float("nan"))
        assert v.admitted is False
        assert "missing_data" in v.reason

    def test_zero_volume_rejects(self):
        v = _gate(volume=0.0)
        assert v.admitted is False


# =============================================================================
# run_integrity_gate -- CHECK 2 continuity
# =============================================================================

class TestGateContinuity:
    def test_sequence_regression_rejects(self):
        v = _gate(prev_sequence_id=10, curr_sequence_id=5)
        assert v.admitted is False

    def test_time_gap_sets_stale(self):
        v = _gate(time_gap_seconds=200.0, timeframe_seconds=60.0)
        assert v.is_stale is True

    def test_time_gap_fail_rejects(self):
        # sequence regression causes hard fail
        v = _gate(prev_sequence_id=5, curr_sequence_id=3)
        assert v.admitted is False


# =============================================================================
# run_integrity_gate -- CHECK 3 spread anomaly
# =============================================================================

class TestGateSpreadAnomaly:
    def test_spread_anomaly_flagged_but_admitted(self):
        v = _gate(spread_bps=25.0, max_entry_spread_bps=10.0)
        assert v.admitted is True
        assert v.spread_flagged is True
        assert any(vi.failure_mode == "FM-06" for vi in v.violations)

    def test_nan_spread_rejects(self):
        v = _gate(spread_bps=float("nan"))
        assert v.admitted is False


# =============================================================================
# run_integrity_gate -- CHECK 4 outlier
# =============================================================================

class TestGateOutlier:
    def test_outlier_degrades_quality(self):
        closes = [100.0 + i * 0.1 for i in range(20)]
        v = _gate(close=1000.0, rolling_closes=closes, quality_score=0.9)
        # quality_score 0.9 - 0.3 = 0.6 >= 0.5 -> admitted
        assert v.admitted is True
        assert v.quality_score_adj == pytest.approx(0.6)

    def test_outlier_drops_quality_below_gate(self):
        closes = [100.0 + i * 0.1 for i in range(20)]
        v = _gate(close=1000.0, rolling_closes=closes, quality_score=0.7)
        # quality_score 0.7 - 0.3 = 0.4 < 0.5 -> rejected
        assert v.admitted is False
        assert "quality_score" in v.reason

    def test_no_outlier_no_penalty(self):
        closes = [100.0 + i * 0.1 for i in range(20)]
        v = _gate(close=101.0, rolling_closes=closes, quality_score=0.9)
        assert v.quality_score_adj == 0.9


# =============================================================================
# run_integrity_gate -- CHECK 5 asset class
# =============================================================================

class TestGateAssetClass:
    def test_unknown_asset_class_rejects(self):
        v = _gate(asset_class="options", session_tag="LONDON")
        assert v.admitted is False

    def test_mismatched_session_rejects(self):
        v = _gate(asset_class="forex", session_tag="CRYPTO_24_7")
        assert v.admitted is False


# =============================================================================
# run_integrity_gate -- Multiple failures
# =============================================================================

class TestGateMultipleFailures:
    def test_multiple_violations_aggregated(self):
        v = _gate(
            open_=float("nan"),
            asset_class="options",
            session_tag="MARS",
        )
        assert v.admitted is False
        assert len(v.violations) >= 2

    def test_spread_anomaly_plus_stale(self):
        v = _gate(
            spread_bps=25.0,
            max_entry_spread_bps=10.0,
            time_gap_seconds=200.0,
            timeframe_seconds=60.0,
        )
        # time_gap violation makes it fail (CHECK 2 returns passed=False)
        # Actually CHECK 2 gap violation is passed=False only for sequence regression
        # Gap threshold violation is also a fail
        assert v.is_stale is True
        assert v.spread_flagged is True


# =============================================================================
# run_integrity_gate -- rolling_closes=None default
# =============================================================================

class TestGateDefaultRollingCloses:
    def test_none_rolling_closes_defaults_to_empty(self):
        v = _gate(rolling_closes=None)
        assert v.admitted is True
        assert v.quality_score_adj == 0.9


# =============================================================================
# Determinism
# =============================================================================

# =============================================================================
# Internal helpers (median odd-length path)
# =============================================================================

class TestMedianHelper:
    def test_odd_length_median(self):
        from jarvis.core.live_data_integrity_gate import _median
        assert _median([1.0, 2.0, 3.0]) == 2.0

    def test_even_length_median(self):
        from jarvis.core.live_data_integrity_gate import _median
        assert _median([1.0, 2.0, 3.0, 4.0]) == 2.5

    def test_single_element(self):
        from jarvis.core.live_data_integrity_gate import _median
        assert _median([42.0]) == 42.0


# =============================================================================
# Determinism
# =============================================================================

class TestDeterminism:
    def test_same_inputs_same_output(self):
        kwargs = dict(
            operating_mode="live_analytical",
            open_=100.0, high=105.0, low=95.0, close=102.0, volume=1000.0,
            quality_score=0.9, spread_bps=5.0, max_entry_spread_bps=10.0,
            asset_class="crypto", session_tag="CRYPTO_24_7",
            prev_sequence_id=1, curr_sequence_id=2,
            time_gap_seconds=60.0, timeframe_seconds=60.0,
        )
        v1 = run_integrity_gate(**kwargs)
        v2 = run_integrity_gate(**kwargs)
        assert v1.admitted == v2.admitted
        assert v1.quality_score_adj == v2.quality_score_adj
        assert v1.is_stale == v2.is_stale
        assert v1.spread_flagged == v2.spread_flagged
        assert len(v1.violations) == len(v2.violations)

    def test_deterministic_outlier(self):
        closes = [100.0 + i * 0.1 for i in range(20)]
        v1 = _gate(close=1000.0, rolling_closes=closes)
        v2 = _gate(close=1000.0, rolling_closes=closes)
        assert v1.quality_score_adj == v2.quality_score_adj
