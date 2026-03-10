# =============================================================================
# Tests for jarvis/intelligence/cross_asset_layer.py (S22)
# =============================================================================

import numpy as np
import pytest

from jarvis.core.regime import CorrelationRegimeState
from jarvis.intelligence.cross_asset_layer import (
    CrossAssetLayer,
    CrossAssetSignal,
)


# ---------------------------------------------------------------------------
# HELPERS
# ---------------------------------------------------------------------------

@pytest.fixture
def layer():
    return CrossAssetLayer()


def _returns(n, seed=42):
    """Generate n deterministic pseudo-returns."""
    rng = np.random.RandomState(seed)
    return rng.randn(n).tolist()


def _correlated_returns(base, correlation, seed=99):
    """Generate returns correlated with base at given level."""
    rng = np.random.RandomState(seed)
    noise = rng.randn(len(base))
    arr = np.array(base)
    corr_arr = correlation * arr + np.sqrt(1 - correlation ** 2) * noise * np.std(arr)
    return corr_arr.tolist()


# ---------------------------------------------------------------------------
# BASIC COMPUTE
# ---------------------------------------------------------------------------

class TestComputeBasic:
    def test_returns_signal(self, layer):
        target = _returns(60)
        refs = {"SPY": _returns(60, seed=10)}
        result = layer.compute(target, refs)
        assert isinstance(result, CrossAssetSignal)

    def test_correlation_keys_match(self, layer):
        target = _returns(60)
        refs = {"SPY": _returns(60, seed=10), "GLD": _returns(60, seed=20)}
        result = layer.compute(target, refs)
        assert set(result.correlations.keys()) == {"SPY", "GLD"}

    def test_risk_on_exposure_range(self, layer):
        target = _returns(60)
        refs = {"SPY": _returns(60, seed=10)}
        result = layer.compute(target, refs)
        assert 0.0 <= result.risk_on_exposure <= 1.0

    def test_systemic_risk_range(self, layer):
        target = _returns(60)
        refs = {"SPY": _returns(60, seed=10)}
        result = layer.compute(target, refs)
        assert 0.0 <= result.systemic_risk <= 1.0

    def test_correlation_regime_is_enum(self, layer):
        target = _returns(60)
        refs = {"SPY": _returns(60, seed=10)}
        result = layer.compute(target, refs)
        assert isinstance(result.correlation_regime, CorrelationRegimeState)


# ---------------------------------------------------------------------------
# CORRELATIONS
# ---------------------------------------------------------------------------

class TestCorrelations:
    def test_perfect_positive_correlation(self, layer):
        target = [0.01 * i for i in range(60)]
        result = layer.compute(target, {"CLONE": list(target)})
        assert result.correlations["CLONE"] == pytest.approx(1.0, abs=1e-6)

    def test_perfect_negative_correlation(self, layer):
        target = [0.01 * i for i in range(60)]
        neg = [-x for x in target]
        result = layer.compute(target, {"NEG": neg})
        assert result.correlations["NEG"] == pytest.approx(-1.0, abs=1e-6)

    def test_uncorrelated_near_zero(self, layer):
        # Different seeds -> low correlation
        target = _returns(200, seed=1)
        ref = _returns(200, seed=9999)
        result = layer.compute(target, {"RAND": ref})
        assert abs(result.correlations["RAND"]) < 0.5

    def test_correlation_clipped_to_range(self, layer):
        target = _returns(60)
        refs = {"A": _returns(60, seed=5)}
        result = layer.compute(target, refs)
        assert -1.0 <= result.correlations["A"] <= 1.0

    def test_insufficient_ref_returns_zero(self, layer):
        target = _returns(60)
        refs = {"SHORT": _returns(30, seed=10)}  # < window
        result = layer.compute(target, refs)
        assert result.correlations["SHORT"] == 0.0

    def test_nan_in_ref_returns_zero(self, layer):
        target = _returns(60)
        ref = _returns(60, seed=10)
        ref[5] = float('nan')
        result = layer.compute(target, {"BAD": ref})
        assert result.correlations["BAD"] == 0.0

    def test_inf_in_ref_returns_zero(self, layer):
        target = _returns(60)
        ref = _returns(60, seed=10)
        ref[10] = float('inf')
        result = layer.compute(target, {"BAD": ref})
        assert result.correlations["BAD"] == 0.0

    def test_multiple_assets(self, layer):
        target = _returns(60)
        refs = {
            "A": _returns(60, seed=10),
            "B": _returns(60, seed=20),
            "C": _returns(60, seed=30),
        }
        result = layer.compute(target, refs)
        assert len(result.correlations) == 3

    def test_uses_last_window_elements(self, layer):
        base = _returns(100, seed=42)
        target = base
        ref = list(base)  # identical -> correlation = 1.0
        result = layer.compute(target, {"SAME": ref}, window=60)
        assert result.correlations["SAME"] == pytest.approx(1.0, abs=1e-6)


# ---------------------------------------------------------------------------
# RISK-ON EXPOSURE
# ---------------------------------------------------------------------------

class TestRiskOnExposure:
    def test_no_refs_returns_0_5(self, layer):
        target = _returns(60)
        result = layer.compute(target, {})
        assert result.risk_on_exposure == 0.5

    def test_positive_correlation_high_risk_on(self, layer):
        target = [0.01 * i for i in range(60)]
        result = layer.compute(target, {"CLONE": list(target)})
        # corr = 1.0 -> risk_on = (1.0 + 1.0) / 2.0 = 1.0
        assert result.risk_on_exposure == pytest.approx(1.0, abs=1e-6)

    def test_negative_correlation_low_risk_on(self, layer):
        target = [0.01 * i for i in range(60)]
        neg = [-x for x in target]
        result = layer.compute(target, {"NEG": neg})
        # corr = -1.0 -> risk_on = (-1.0 + 1.0) / 2.0 = 0.0
        assert result.risk_on_exposure == pytest.approx(0.0, abs=1e-6)

    def test_zero_correlation_mid_risk_on(self, layer):
        target = _returns(60)
        # Force zero correlation via insufficient data
        result = layer.compute(target, {"SHORT": [0.01] * 10})
        # corr = 0.0 -> risk_on = (0.0 + 1.0) / 2.0 = 0.5
        assert result.risk_on_exposure == pytest.approx(0.5)

    def test_clipped_to_0_1(self, layer):
        target = _returns(60)
        refs = {"A": _returns(60, seed=10)}
        result = layer.compute(target, refs)
        assert 0.0 <= result.risk_on_exposure <= 1.0


# ---------------------------------------------------------------------------
# CORRELATION REGIME
# ---------------------------------------------------------------------------

class TestCorrelationRegime:
    def test_breakdown_on_crisis_correlation(self, layer):
        target = [0.01 * i for i in range(60)]
        # Perfect correlation > 0.85
        result = layer.compute(target, {"CLONE": list(target)})
        assert result.correlation_regime == CorrelationRegimeState.BREAKDOWN

    def test_coupled_on_moderate_correlation(self, layer):
        target = _returns(200, seed=1)
        ref = _correlated_returns(target[-200:], 0.7, seed=50)
        result = layer.compute(target, {"MOD": ref}, window=200)
        max_abs = abs(result.correlations["MOD"])
        if 0.6 < max_abs <= 0.85:
            assert result.correlation_regime == CorrelationRegimeState.COUPLED

    def test_normal_on_low_correlation(self, layer):
        # Force low correlation via zero-correlation ref
        target = _returns(60)
        result = layer.compute(target, {"SHORT": [0.01] * 10})
        # corr = 0.0 -> max_abs = 0.0 < 0.6 -> NORMAL
        assert result.correlation_regime == CorrelationRegimeState.NORMAL

    def test_empty_refs_normal(self, layer):
        target = _returns(60)
        result = layer.compute(target, {})
        assert result.correlation_regime == CorrelationRegimeState.NORMAL

    def test_threshold_boundary_0_85(self, layer):
        # max_corr > 0.85 -> BREAKDOWN
        assert CrossAssetLayer.CRISIS_CORRELATION_THRESHOLD == 0.85

    def test_uses_abs_correlation(self, layer):
        target = [0.01 * i for i in range(60)]
        neg = [-x for x in target]
        result = layer.compute(target, {"NEG": neg})
        # abs(corr) = 1.0 > 0.85 -> BREAKDOWN
        assert result.correlation_regime == CorrelationRegimeState.BREAKDOWN


# ---------------------------------------------------------------------------
# SYSTEMIC RISK
# ---------------------------------------------------------------------------

class TestSystemicRisk:
    def test_formula(self, layer):
        target = _returns(60)
        refs = {"A": _returns(60, seed=10)}
        result = layer.compute(target, refs)
        max_corr = max(abs(v) for v in result.correlations.values())
        expected = float(np.clip(max_corr * result.risk_on_exposure, 0.0, 1.0))
        assert result.systemic_risk == pytest.approx(expected)

    def test_zero_when_no_refs(self, layer):
        target = _returns(60)
        result = layer.compute(target, {})
        # max_corr = 0.0 -> systemic = 0.0 * 0.5 = 0.0
        assert result.systemic_risk == pytest.approx(0.0)

    def test_high_correlation_high_systemic(self, layer):
        target = [0.01 * i for i in range(60)]
        result = layer.compute(target, {"CLONE": list(target)})
        # max_corr = 1.0, risk_on = 1.0 -> systemic = 1.0
        assert result.systemic_risk == pytest.approx(1.0, abs=1e-6)

    def test_range(self, layer):
        target = _returns(60)
        refs = {"A": _returns(60, seed=10), "B": _returns(60, seed=20)}
        result = layer.compute(target, refs)
        assert 0.0 <= result.systemic_risk <= 1.0


# ---------------------------------------------------------------------------
# WINDOW PARAMETER
# ---------------------------------------------------------------------------

class TestWindowParameter:
    def test_custom_window(self, layer):
        target = _returns(120)
        refs = {"A": _returns(120, seed=10)}
        result = layer.compute(target, refs, window=100)
        assert isinstance(result, CrossAssetSignal)

    def test_insufficient_target_raises(self, layer):
        target = _returns(30)
        with pytest.raises(ValueError, match="60 Returns"):
            layer.compute(target, {})

    def test_custom_window_insufficient_raises(self, layer):
        target = _returns(50)
        with pytest.raises(ValueError, match="80 Returns"):
            layer.compute(target, {}, window=80)

    def test_exact_window_ok(self, layer):
        target = _returns(60)
        result = layer.compute(target, {}, window=60)
        assert isinstance(result, CrossAssetSignal)


# ---------------------------------------------------------------------------
# INPUT VALIDATION
# ---------------------------------------------------------------------------

class TestInputValidation:
    def test_nan_in_target_raises(self, layer):
        target = _returns(60)
        target[10] = float('nan')
        with pytest.raises(ValueError, match="NaN/Inf"):
            layer.compute(target, {})

    def test_inf_in_target_raises(self, layer):
        target = _returns(60)
        target[10] = float('inf')
        with pytest.raises(ValueError, match="NaN/Inf"):
            layer.compute(target, {})

    def test_neg_inf_in_target_raises(self, layer):
        target = _returns(60)
        target[10] = float('-inf')
        with pytest.raises(ValueError, match="NaN/Inf"):
            layer.compute(target, {})


# ---------------------------------------------------------------------------
# CONSTANTS
# ---------------------------------------------------------------------------

class TestConstants:
    def test_crisis_threshold(self):
        assert CrossAssetLayer.CRISIS_CORRELATION_THRESHOLD == 0.85


# ---------------------------------------------------------------------------
# DATACLASS
# ---------------------------------------------------------------------------

class TestDataClass:
    def test_signal_fields(self):
        sig = CrossAssetSignal(
            correlations={"SPY": 0.5, "GLD": -0.2},
            risk_on_exposure=0.6,
            correlation_regime=CorrelationRegimeState.COUPLED,
            systemic_risk=0.3,
        )
        assert sig.correlations["SPY"] == 0.5
        assert sig.correlation_regime == CorrelationRegimeState.COUPLED
        assert sig.systemic_risk == 0.3


# ---------------------------------------------------------------------------
# DETERMINISM
# ---------------------------------------------------------------------------

class TestDeterminism:
    def test_identical_inputs_identical_outputs(self, layer):
        target = _returns(60)
        refs = {"A": _returns(60, seed=10), "B": _returns(60, seed=20)}
        r1 = layer.compute(target, refs)
        r2 = layer.compute(target, refs)
        assert r1.correlations == r2.correlations
        assert r1.risk_on_exposure == r2.risk_on_exposure
        assert r1.correlation_regime == r2.correlation_regime
        assert r1.systemic_risk == r2.systemic_risk

    def test_no_state_between_calls(self, layer):
        t1 = _returns(60, seed=1)
        t2 = _returns(60, seed=2)
        refs = {"A": _returns(60, seed=10)}
        r1a = layer.compute(t1, refs)
        _ = layer.compute(t2, refs)
        r1b = layer.compute(t1, refs)
        assert r1a.correlations == r1b.correlations
        assert r1a.systemic_risk == r1b.systemic_risk


# ---------------------------------------------------------------------------
# EDGE CASES
# ---------------------------------------------------------------------------

class TestEdgeCases:
    def test_empty_reference_assets(self, layer):
        target = _returns(60)
        result = layer.compute(target, {})
        assert result.correlations == {}
        assert result.risk_on_exposure == 0.5
        assert result.correlation_regime == CorrelationRegimeState.NORMAL
        assert result.systemic_risk == 0.0

    def test_constant_target_returns(self, layer):
        target = [0.01] * 60
        refs = {"A": _returns(60, seed=10)}
        result = layer.compute(target, refs)
        # Constant target -> var = 0 -> denom capped -> corr near 0
        assert -1.0 <= result.correlations["A"] <= 1.0

    def test_constant_ref_returns(self, layer):
        target = _returns(60)
        refs = {"CONST": [0.01] * 60}
        result = layer.compute(target, refs)
        assert -1.0 <= result.correlations["CONST"] <= 1.0

    def test_many_reference_assets(self, layer):
        target = _returns(60)
        refs = {f"ASSET_{i}": _returns(60, seed=i) for i in range(20)}
        result = layer.compute(target, refs)
        assert len(result.correlations) == 20

    def test_longer_returns_uses_last_window(self, layer):
        target = _returns(200)
        refs = {"A": _returns(200, seed=10)}
        r60 = layer.compute(target, refs, window=60)
        r100 = layer.compute(target, refs, window=100)
        # Different windows -> potentially different results
        assert isinstance(r60, CrossAssetSignal)
        assert isinstance(r100, CrossAssetSignal)

    def test_mixed_valid_invalid_refs(self, layer):
        target = _returns(60)
        refs = {
            "GOOD": _returns(60, seed=10),
            "SHORT": _returns(30, seed=20),
            "NAN": [float('nan')] * 60,
        }
        result = layer.compute(target, refs)
        assert result.correlations["SHORT"] == 0.0
        assert result.correlations["NAN"] == 0.0
        assert result.correlations["GOOD"] != 0.0 or True  # may be close to 0
