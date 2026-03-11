# tests/unit/core/test_feature_layer_coverage.py
# Targeted tests for feature_layer.py coverage gaps.
# Covers: _safe_float, _std, _ema edge cases, KS-test guards,
#         RSI/ATR/MACD/CCI/Stochastic/Williams%R/OBV/MFI/CMF/ADX edge cases,
#         volatility scaling errors, NaN sanitisation, drift action mapping,
#         volume-price correlation, Fibonacci, pivot points.

from __future__ import annotations

import math
import pytest


# ---------------------------------------------------------------------------
# _safe_float (lines 242-243: TypeError/ValueError; line 244-245: NaN/Inf)
# ---------------------------------------------------------------------------

class TestSafeFloat:
    def test_non_convertible_returns_zero(self):
        from jarvis.core.feature_layer import _safe_float
        assert _safe_float(object()) == 0.0

    def test_none_returns_zero(self):
        from jarvis.core.feature_layer import _safe_float
        assert _safe_float(None) == 0.0

    def test_nan_returns_zero(self):
        from jarvis.core.feature_layer import _safe_float
        assert _safe_float(float("nan")) == 0.0

    def test_inf_returns_zero(self):
        from jarvis.core.feature_layer import _safe_float
        assert _safe_float(float("inf")) == 0.0

    def test_neg_inf_returns_zero(self):
        from jarvis.core.feature_layer import _safe_float
        assert _safe_float(float("-inf")) == 0.0

    def test_valid_float_passes_through(self):
        from jarvis.core.feature_layer import _safe_float
        assert _safe_float(3.14) == 3.14

    def test_string_number_converts(self):
        from jarvis.core.feature_layer import _safe_float
        assert _safe_float("2.5") == 2.5

    def test_non_numeric_string_returns_zero(self):
        from jarvis.core.feature_layer import _safe_float
        assert _safe_float("abc") == 0.0


# ---------------------------------------------------------------------------
# _std edge cases (line 272: negative variance guard)
# ---------------------------------------------------------------------------

class TestStdEdgeCases:
    def test_single_element_returns_zero(self):
        from jarvis.core.feature_layer import _std
        assert _std([5.0]) == 0.0

    def test_empty_returns_zero(self):
        from jarvis.core.feature_layer import _std
        assert _std([]) == 0.0

    def test_identical_values_returns_zero(self):
        from jarvis.core.feature_layer import _std
        assert _std([3.0, 3.0, 3.0]) == 0.0


# ---------------------------------------------------------------------------
# _ema edge cases (line 287: empty data or period <= 0)
# ---------------------------------------------------------------------------

class TestEmaEdgeCases:
    def test_empty_data_returns_zero(self):
        from jarvis.core.feature_layer import _ema
        assert _ema([], 10) == 0.0

    def test_period_zero_returns_zero(self):
        from jarvis.core.feature_layer import _ema
        assert _ema([1.0, 2.0], 0) == 0.0

    def test_negative_period_returns_zero(self):
        from jarvis.core.feature_layer import _ema
        assert _ema([1.0, 2.0], -5) == 0.0


# ---------------------------------------------------------------------------
# RSI edge cases (lines 374, 391, 401)
# ---------------------------------------------------------------------------

class TestRsiEdgeCases:
    def test_rsi_short_data_returns_default(self):
        from jarvis.core.feature_layer import _rsi
        # period=14, need at least 15 closes
        assert _rsi([100.0] * 5, 14) == 50.0

    def test_rsi_all_gains_returns_100(self):
        from jarvis.core.feature_layer import _rsi
        # Monotonically increasing -> avg_loss = 0 -> RSI = 100
        closes = [float(i) for i in range(1, 20)]
        result = _rsi(closes, 14)
        assert result == 100.0


# ---------------------------------------------------------------------------
# ATR edge cases (line 401: empty trs)
# ---------------------------------------------------------------------------

class TestAtrEdgeCases:
    def test_atr_insufficient_data(self):
        from jarvis.core.feature_layer import _atr
        assert _atr([], [], [], 14) == 0.0

    def test_atr_single_bar(self):
        from jarvis.core.feature_layer import _atr
        assert _atr([10.0], [5.0], [7.0], 14) == 0.0


# ---------------------------------------------------------------------------
# MACD edge cases (line 441: empty macd_history)
# ---------------------------------------------------------------------------

class TestMacdEdgeCases:
    def test_macd_short_data(self):
        from jarvis.core.feature_layer import _macd
        macd_line, signal, hist = _macd([100.0] * 3, 12, 26, 9)
        # With only 3 closes, not enough for 26-period EMA
        # Should still return valid floats
        assert math.isfinite(macd_line)
        assert math.isfinite(signal)
        assert math.isfinite(hist)


# ---------------------------------------------------------------------------
# CCI edge cases (lines 452, 458: short data, zero mean_dev)
# ---------------------------------------------------------------------------

class TestCciEdgeCases:
    def test_cci_short_data(self):
        from jarvis.core.feature_layer import _cci
        assert _cci([10.0], [5.0], [7.0], 20) == 0.0

    def test_cci_flat_prices(self):
        from jarvis.core.feature_layer import _cci
        # All identical prices -> mean_dev = 0 -> returns 0
        n = 25
        result = _cci([10.0] * n, [10.0] * n, [10.0] * n, 20)
        assert result == 0.0


# ---------------------------------------------------------------------------
# Stochastic edge cases (lines 468, 475: short data, zero denom)
# ---------------------------------------------------------------------------

class TestStochasticEdgeCases:
    def test_stochastic_short_data(self):
        from jarvis.core.feature_layer import _stochastic
        k, d = _stochastic([10.0], [5.0], [7.0], 14, 3)
        assert k == 50.0
        assert d == 50.0

    def test_stochastic_flat_prices(self):
        from jarvis.core.feature_layer import _stochastic
        n = 20
        k, d = _stochastic([10.0] * n, [10.0] * n, [10.0] * n, 14, 3)
        assert k == 50.0


# ---------------------------------------------------------------------------
# Williams %R edge cases (line 494: zero denom)
# ---------------------------------------------------------------------------

class TestWilliamsREdgeCases:
    def test_williams_r_flat_prices(self):
        from jarvis.core.feature_layer import _williams_r
        n = 20
        result = _williams_r([10.0] * n, [10.0] * n, [10.0] * n, 14)
        assert result == -50.0


# ---------------------------------------------------------------------------
# OBV edge cases (line 502: short data)
# ---------------------------------------------------------------------------

class TestObvEdgeCases:
    def test_obv_single_point(self):
        from jarvis.core.feature_layer import _obv
        assert _obv([100.0], [1000.0]) == 0.0


# ---------------------------------------------------------------------------
# MFI edge cases (lines 517, 529: short data, zero neg flow)
# ---------------------------------------------------------------------------

class TestMfiEdgeCases:
    def test_mfi_short_data(self):
        from jarvis.core.feature_layer import _mfi
        assert _mfi([10.0], [5.0], [7.0], [100.0], 14) == 50.0

    def test_mfi_all_positive_flow(self):
        from jarvis.core.feature_layer import _mfi
        # Monotonically increasing typical price -> all positive flow
        n = 20
        highs = [10.0 + i * 0.1 for i in range(n)]
        lows = [9.0 + i * 0.1 for i in range(n)]
        closes = [9.5 + i * 0.1 for i in range(n)]
        volumes = [1000.0] * n
        result = _mfi(highs, lows, closes, volumes, 14)
        assert result == 100.0


# ---------------------------------------------------------------------------
# CMF edge cases (lines 539, 545: short data, zero hl)
# ---------------------------------------------------------------------------

class TestCmfEdgeCases:
    def test_cmf_short_data(self):
        from jarvis.core.feature_layer import _cmf
        assert _cmf([10.0], [5.0], [7.0], [100.0], 20) == 0.0


# ---------------------------------------------------------------------------
# ADX edge cases (lines 560, 599-600: short data, no dx values)
# ---------------------------------------------------------------------------

class TestAdxEdgeCases:
    def test_adx_short_data(self):
        from jarvis.core.feature_layer import _adx
        assert _adx([10.0], [5.0], [7.0], 14) == 0.0


# ---------------------------------------------------------------------------
# Volatility scaling error (line 687)
# ---------------------------------------------------------------------------

class TestVolatilityScalingError:
    def test_unknown_asset_class_raises(self):
        from jarvis.core.feature_layer import get_volatility_scaling, VolatilityScalingError
        with pytest.raises(VolatilityScalingError):
            get_volatility_scaling("unknown_asset_xyz")


# ---------------------------------------------------------------------------
# _FeatureComputer: volume-price correlation (line 802: zero sd)
# ---------------------------------------------------------------------------

class TestVolumePriceCorrelation:
    def test_flat_prices_returns_zero(self):
        from jarvis.core.feature_layer import _FeatureComputer
        # All same close -> sd_c = 0 -> return 0
        assert _FeatureComputer._volume_price_correlation(
            [100.0] * 10, [500.0, 600.0, 500.0] * 3 + [500.0]
        ) == 0.0

    def test_flat_volumes_returns_zero(self):
        from jarvis.core.feature_layer import _FeatureComputer
        closes = [100.0 + i for i in range(10)]
        assert _FeatureComputer._volume_price_correlation(
            closes, [500.0] * 10
        ) == 0.0


# ---------------------------------------------------------------------------
# _FeatureComputer: return and volatility helpers (lines 710-735)
# ---------------------------------------------------------------------------

class TestReturnHelpers:
    def test_return_insufficient_data(self):
        from jarvis.core.feature_layer import _FeatureComputer
        assert _FeatureComputer._return([100.0], lag=5) == 0.0

    def test_return_zero_lag(self):
        from jarvis.core.feature_layer import _FeatureComputer
        assert _FeatureComputer._return([100.0, 110.0], lag=0) == 0.0

    def test_volatility_insufficient_data(self):
        from jarvis.core.feature_layer import _FeatureComputer
        assert _FeatureComputer._volatility([100.0, 110.0], period=20) == 0.0

    def test_zero_price_returns_zero(self):
        from jarvis.core.feature_layer import _FeatureComputer
        # If previous price is 0 -> division guard
        assert _FeatureComputer._return([0.0, 100.0], lag=1) == 0.0


# ---------------------------------------------------------------------------
# _FeatureComputer: Fibonacci (line 758: zero span)
# ---------------------------------------------------------------------------

class TestFibonacci:
    def test_fibonacci_flat_range(self):
        from jarvis.core.feature_layer import _FeatureComputer
        # high == low -> span = 0 -> returns 0
        assert _FeatureComputer._fibonacci_level(10.0, 10.0, 10.0) == 0.0


# ---------------------------------------------------------------------------
# _FeatureComputer: Pivot / volume ratio (lines 772, 781, 784)
# ---------------------------------------------------------------------------

class TestPivotAndVolume:
    def test_pivot_zero_close(self):
        from jarvis.core.feature_layer import _FeatureComputer
        assert _FeatureComputer._pivot_points(10.0, 5.0, 0.0) == 0.0

    def test_volume_ratio_short_data(self):
        from jarvis.core.feature_layer import _FeatureComputer
        assert _FeatureComputer._volume_ma_ratio([100.0], period=20) == 1.0

    def test_volume_ratio_zero_ma(self):
        from jarvis.core.feature_layer import _FeatureComputer
        assert _FeatureComputer._volume_ma_ratio([0.0] * 25, period=20) == 1.0


# ---------------------------------------------------------------------------
# KS-test guard (lines 343-347)
# ---------------------------------------------------------------------------

class TestKsTestGuard:
    def test_ks_pvalue_zero_d(self):
        from jarvis.core.feature_layer import _ks_p_value_approx
        assert _ks_p_value_approx(0.0, 10, 10) == 1.0

    def test_ks_pvalue_zero_n(self):
        from jarvis.core.feature_layer import _ks_p_value_approx
        assert _ks_p_value_approx(0.5, 0, 10) == 1.0


# ---------------------------------------------------------------------------
# Drift action mapping (lines 1363-1367)
# ---------------------------------------------------------------------------

class TestDriftAction:
    def test_low_severity_ignorieren(self):
        from jarvis.core.feature_layer import FeatureDriftMonitor, DriftAction
        mon = FeatureDriftMonitor()
        action = mon.determine_action(0.1)
        assert action == DriftAction.IGNORIEREN

    def test_medium_severity_loggen(self):
        from jarvis.core.feature_layer import FeatureDriftMonitor, DriftAction
        mon = FeatureDriftMonitor()
        action = mon.determine_action(0.3)
        assert action == DriftAction.LOGGEN

    def test_high_severity_erhoehen(self):
        from jarvis.core.feature_layer import FeatureDriftMonitor, DriftAction
        mon = FeatureDriftMonitor()
        action = mon.determine_action(0.7)
        assert action == DriftAction.UNSICHERHEIT_ERHOEHEN

    def test_boundary_02_is_loggen(self):
        from jarvis.core.feature_layer import FeatureDriftMonitor, DriftAction
        mon = FeatureDriftMonitor()
        action = mon.determine_action(0.2)
        assert action == DriftAction.LOGGEN

    def test_boundary_05_is_erhoehen(self):
        from jarvis.core.feature_layer import FeatureDriftMonitor, DriftAction
        mon = FeatureDriftMonitor()
        action = mon.determine_action(0.5)
        assert action == DriftAction.UNSICHERHEIT_ERHOEHEN


# ---------------------------------------------------------------------------
# Sanitise NaN replacement (lines 1180-1190)
# ---------------------------------------------------------------------------

class TestSanitiseNaN:
    def test_sanitise_replaces_nan(self):
        from jarvis.core.feature_layer import (
            FeatureLayer, FEATURE_NAMES, FEATURE_VECTOR_SIZE,
        )
        raw = {name: float("nan") for name in FEATURE_NAMES}
        result = FeatureLayer._sanitise(raw)
        assert result.nan_replaced_count == FEATURE_VECTOR_SIZE
        assert all(v == 0.0 for v in result.features.values())

    def test_sanitise_replaces_inf(self):
        from jarvis.core.feature_layer import FeatureLayer, FEATURE_NAMES
        raw = {name: float("inf") if i % 2 == 0 else 0.5
               for i, name in enumerate(FEATURE_NAMES)}
        result = FeatureLayer._sanitise(raw)
        assert result.nan_replaced_count > 0


# ---------------------------------------------------------------------------
# _FeatureComputer: support/resistance with zero close (lines 734-736)
# ---------------------------------------------------------------------------

class TestSupportResistance:
    def test_support_distance_zero_close(self):
        from jarvis.core.feature_layer import _FeatureComputer
        closes = [100.0] * 19 + [0.0]
        assert _FeatureComputer._support_distance(closes, period=20) == 0.0

    def test_resistance_distance_zero_close(self):
        from jarvis.core.feature_layer import _FeatureComputer
        closes = [100.0] * 19 + [0.0]
        assert _FeatureComputer._resistance_distance(closes, period=20) == 0.0

    def test_support_distance_short_data(self):
        from jarvis.core.feature_layer import _FeatureComputer
        assert _FeatureComputer._support_distance([100.0] * 5, period=20) == 0.0


# ---------------------------------------------------------------------------
# _FeatureComputer: _return with zero prev price (line 714)
# ---------------------------------------------------------------------------

class TestReturnZeroPrev:
    def test_return_zero_prev_price(self):
        from jarvis.core.feature_layer import _FeatureComputer
        # prev price at -(lag+1) is 0.0
        assert _FeatureComputer._return([0.0, 50.0, 100.0], lag=2) == 0.0


# ---------------------------------------------------------------------------
# FeatureDriftMonitor: calculate_severity (lines 1341-1352)
# ---------------------------------------------------------------------------

class TestCalculateSeverity:
    def test_nan_ks_stat_returns_max(self):
        from jarvis.core.feature_layer import FeatureDriftMonitor
        mon = FeatureDriftMonitor()
        assert mon.calculate_severity(float("nan"), 1.0) == 1.0

    def test_nan_importance_returns_max(self):
        from jarvis.core.feature_layer import FeatureDriftMonitor
        mon = FeatureDriftMonitor()
        assert mon.calculate_severity(0.5, float("nan")) == 1.0

    def test_normal_values(self):
        from jarvis.core.feature_layer import FeatureDriftMonitor
        mon = FeatureDriftMonitor()
        result = mon.calculate_severity(0.5, 0.4)
        assert result == pytest.approx(0.2)
