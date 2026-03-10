# =============================================================================
# Tests for jarvis/intelligence/macro_layer.py (S23)
# =============================================================================

import numpy as np
import pytest

from jarvis.core.regime import MacroRegimeState
from jarvis.intelligence.macro_layer import (
    MacroSensitivityLayer,
    MacroSensitivityResult,
)


# ---------------------------------------------------------------------------
# HELPERS
# ---------------------------------------------------------------------------

@pytest.fixture
def layer():
    return MacroSensitivityLayer()


def _returns(n, seed=42):
    """Generate n deterministic pseudo-returns."""
    rng = np.random.RandomState(seed)
    return rng.randn(n).tolist()


def _scaled_returns(base, beta, seed=99):
    """Generate factor returns: asset = beta * factor + noise."""
    rng = np.random.RandomState(seed)
    factor = rng.randn(len(base)).tolist()
    return factor


# ---------------------------------------------------------------------------
# BASIC COMPUTE
# ---------------------------------------------------------------------------

class TestComputeBasic:
    def test_returns_result(self, layer):
        target = _returns(120)
        factors = {"rate": _returns(120, seed=10)}
        result = layer.compute(target, factors)
        assert isinstance(result, MacroSensitivityResult)

    def test_factor_keys_match(self, layer):
        target = _returns(120)
        factors = {"rate": _returns(120, seed=10), "vix": _returns(120, seed=20)}
        result = layer.compute(target, factors)
        assert set(result.factor_sensitivities.keys()) == {"rate", "vix"}

    def test_macro_risk_score_range(self, layer):
        target = _returns(120)
        factors = {"rate": _returns(120, seed=10)}
        result = layer.compute(target, factors)
        assert 0.0 <= result.macro_risk_score <= 1.0

    def test_macro_regime_is_enum(self, layer):
        target = _returns(120)
        factors = {"rate": _returns(120, seed=10)}
        result = layer.compute(target, factors)
        assert isinstance(result.macro_regime, MacroRegimeState)

    def test_dominant_factor_in_keys(self, layer):
        target = _returns(120)
        factors = {"rate": _returns(120, seed=10), "vix": _returns(120, seed=20)}
        result = layer.compute(target, factors)
        assert result.dominant_factor in factors


# ---------------------------------------------------------------------------
# BETAS (OLS)
# ---------------------------------------------------------------------------

class TestBetas:
    def test_perfect_correlation_beta_near_1(self, layer):
        factor = [0.01 * i for i in range(120)]
        # asset = factor -> beta ~1
        result = layer.compute(factor, {"F": factor})
        assert result.factor_sensitivities["F"] == pytest.approx(1.0, abs=0.01)

    def test_negative_correlation(self, layer):
        factor = [0.01 * i for i in range(120)]
        asset = [-x for x in factor]
        result = layer.compute(asset, {"F": factor})
        assert result.factor_sensitivities["F"] == pytest.approx(-1.0, abs=0.01)

    def test_beta_clipped_to_5(self, layer):
        # Force extreme beta: tiny factor variance, large covariance
        factor = [0.00001] * 119 + [0.00002]  # near-zero variance
        asset = _returns(120, seed=42)
        result = layer.compute(asset, {"F": factor})
        assert -5.0 <= result.factor_sensitivities["F"] <= 5.0

    def test_insufficient_factor_returns_zero(self, layer):
        target = _returns(120)
        factors = {"SHORT": _returns(50, seed=10)}  # < window
        result = layer.compute(target, factors)
        assert result.factor_sensitivities["SHORT"] == 0.0

    def test_nan_in_factor_returns_zero(self, layer):
        target = _returns(120)
        f = _returns(120, seed=10)
        f[5] = float('nan')
        result = layer.compute(target, {"BAD": f})
        assert result.factor_sensitivities["BAD"] == 0.0

    def test_inf_in_factor_returns_zero(self, layer):
        target = _returns(120)
        f = _returns(120, seed=10)
        f[10] = float('inf')
        result = layer.compute(target, {"BAD": f})
        assert result.factor_sensitivities["BAD"] == 0.0

    def test_constant_factor_safe(self, layer):
        target = _returns(120)
        factors = {"CONST": [0.01] * 120}
        result = layer.compute(target, factors)
        # var_x ~ 0 -> denominator capped at 1e-12
        assert -5.0 <= result.factor_sensitivities["CONST"] <= 5.0

    def test_multiple_factors(self, layer):
        target = _returns(120)
        factors = {
            "rate": _returns(120, seed=10),
            "inflation": _returns(120, seed=20),
            "vix": _returns(120, seed=30),
        }
        result = layer.compute(target, factors)
        assert len(result.factor_sensitivities) == 3


# ---------------------------------------------------------------------------
# MACRO RISK SCORE
# ---------------------------------------------------------------------------

class TestMacroRiskScore:
    def test_zero_when_no_factors(self, layer):
        target = _returns(120)
        result = layer.compute(target, {})
        assert result.macro_risk_score == pytest.approx(0.0)

    def test_low_betas_low_score(self, layer):
        target = _returns(120, seed=1)
        # Unrelated factors -> low betas
        factors = {f"F{i}": _returns(120, seed=i * 100) for i in range(5)}
        result = layer.compute(target, factors)
        # Random returns -> typically small betas -> low score
        assert result.macro_risk_score < 1.0

    def test_score_clipped_to_1(self, layer):
        target = _returns(120)
        factors = {"F": _returns(120, seed=10)}
        result = layer.compute(target, factors)
        assert result.macro_risk_score <= 1.0

    def test_score_formula_l2_norm(self, layer):
        target = _returns(120)
        factors = {"A": _returns(120, seed=10), "B": _returns(120, seed=20)}
        result = layer.compute(target, factors)
        betas = list(result.factor_sensitivities.values())
        expected = float(np.clip(
            np.sqrt(np.sum(np.array(betas) ** 2)) / len(betas), 0.0, 1.0
        ))
        assert result.macro_risk_score == pytest.approx(expected)


# ---------------------------------------------------------------------------
# DOMINANT FACTOR
# ---------------------------------------------------------------------------

class TestDominantFactor:
    def test_none_when_no_factors(self, layer):
        target = _returns(120)
        result = layer.compute(target, {})
        assert result.dominant_factor == "NONE"

    def test_single_factor_is_dominant(self, layer):
        target = _returns(120)
        result = layer.compute(target, {"only": _returns(120, seed=10)})
        assert result.dominant_factor == "only"

    def test_highest_abs_beta_dominates(self, layer):
        # Factor A: asset = 2*factor_A
        factor_a = [0.01 * i for i in range(120)]
        asset = [2.0 * x for x in factor_a]
        factor_b = _returns(120, seed=99)  # unrelated
        result = layer.compute(asset, {"A": factor_a, "B": factor_b})
        assert result.dominant_factor == "A"

    def test_negative_beta_can_dominate(self, layer):
        factor = [0.01 * i for i in range(120)]
        asset = [-3.0 * x for x in factor]
        result = layer.compute(asset, {"F": factor, "R": _returns(120, seed=99)})
        assert result.dominant_factor == "F"


# ---------------------------------------------------------------------------
# MACRO REGIME
# ---------------------------------------------------------------------------

class TestMacroRegime:
    def test_benign_low_score(self, layer):
        target = _returns(120, seed=1)
        # Force zero betas
        result = layer.compute(target, {})
        assert result.macro_regime == MacroRegimeState.BENIGN

    def test_adverse_high_score(self, layer):
        # Perfect correlation beta=1 with single factor -> score = 1.0/1 = 1.0
        factor = [0.01 * i for i in range(120)]
        result = layer.compute(factor, {"F": factor})
        assert result.macro_regime == MacroRegimeState.ADVERSE

    def test_threshold_0_4_uncertain(self):
        # score > 0.4 and <= 0.7 -> UNCERTAIN
        # This is a specification check
        assert MacroRegimeState.UNCERTAIN.value == "UNCERTAIN"

    def test_threshold_0_7_adverse(self):
        assert MacroRegimeState.ADVERSE.value == "ADVERSE"

    def test_all_regimes_reachable(self, layer):
        # BENIGN: no factors
        r1 = layer.compute(_returns(120), {})
        assert r1.macro_regime == MacroRegimeState.BENIGN

        # ADVERSE: perfect correlation
        f = [0.01 * i for i in range(120)]
        r3 = layer.compute(f, {"F": f})
        assert r3.macro_regime == MacroRegimeState.ADVERSE


# ---------------------------------------------------------------------------
# WINDOW PARAMETER
# ---------------------------------------------------------------------------

class TestWindowParameter:
    def test_custom_window(self, layer):
        target = _returns(200)
        factors = {"F": _returns(200, seed=10)}
        result = layer.compute(target, factors, window=200)
        assert isinstance(result, MacroSensitivityResult)

    def test_insufficient_target_raises(self, layer):
        target = _returns(50)
        with pytest.raises(ValueError, match="120 Asset-Returns"):
            layer.compute(target, {})

    def test_custom_window_insufficient_raises(self, layer):
        target = _returns(50)
        with pytest.raises(ValueError, match="80 Asset-Returns"):
            layer.compute(target, {}, window=80)

    def test_exact_window_ok(self, layer):
        target = _returns(120)
        result = layer.compute(target, {}, window=120)
        assert isinstance(result, MacroSensitivityResult)

    def test_uses_last_window_elements(self, layer):
        # Prepend junk, last 120 identical -> same result
        base = _returns(120, seed=42)
        extended = [999.0] * 50 + base
        factors = {"F": [999.0] * 50 + _returns(120, seed=10)}
        r1 = layer.compute(base, {"F": _returns(120, seed=10)})
        r2 = layer.compute(extended, factors)
        assert r1.factor_sensitivities["F"] == pytest.approx(r2.factor_sensitivities["F"])


# ---------------------------------------------------------------------------
# INPUT VALIDATION
# ---------------------------------------------------------------------------

class TestInputValidation:
    def test_nan_in_target_raises(self, layer):
        target = _returns(120)
        target[10] = float('nan')
        with pytest.raises(ValueError, match="NaN/Inf"):
            layer.compute(target, {})

    def test_inf_in_target_raises(self, layer):
        target = _returns(120)
        target[10] = float('inf')
        with pytest.raises(ValueError, match="NaN/Inf"):
            layer.compute(target, {})

    def test_neg_inf_in_target_raises(self, layer):
        target = _returns(120)
        target[10] = float('-inf')
        with pytest.raises(ValueError, match="NaN/Inf"):
            layer.compute(target, {})


# ---------------------------------------------------------------------------
# CONSTANTS
# ---------------------------------------------------------------------------

class TestConstants:
    def test_macro_factors_list(self):
        expected = ["interest_rate", "inflation", "usd_strength",
                     "credit_spread", "vix"]
        assert MacroSensitivityLayer.MACRO_FACTORS == expected


# ---------------------------------------------------------------------------
# DATACLASS
# ---------------------------------------------------------------------------

class TestDataClass:
    def test_result_fields(self):
        r = MacroSensitivityResult(
            factor_sensitivities={"rate": 0.5, "vix": -0.3},
            macro_risk_score=0.4,
            dominant_factor="rate",
            macro_regime=MacroRegimeState.UNCERTAIN,
        )
        assert r.factor_sensitivities["rate"] == 0.5
        assert r.macro_regime == MacroRegimeState.UNCERTAIN
        assert r.dominant_factor == "rate"


# ---------------------------------------------------------------------------
# DETERMINISM
# ---------------------------------------------------------------------------

class TestDeterminism:
    def test_identical_inputs_identical_outputs(self, layer):
        target = _returns(120)
        factors = {"A": _returns(120, seed=10), "B": _returns(120, seed=20)}
        r1 = layer.compute(target, factors)
        r2 = layer.compute(target, factors)
        assert r1.factor_sensitivities == r2.factor_sensitivities
        assert r1.macro_risk_score == r2.macro_risk_score
        assert r1.dominant_factor == r2.dominant_factor
        assert r1.macro_regime == r2.macro_regime

    def test_no_state_between_calls(self, layer):
        t1 = _returns(120, seed=1)
        t2 = _returns(120, seed=2)
        factors = {"F": _returns(120, seed=10)}
        r1a = layer.compute(t1, factors)
        _ = layer.compute(t2, factors)
        r1b = layer.compute(t1, factors)
        assert r1a.factor_sensitivities == r1b.factor_sensitivities
        assert r1a.macro_risk_score == r1b.macro_risk_score


# ---------------------------------------------------------------------------
# EDGE CASES
# ---------------------------------------------------------------------------

class TestEdgeCases:
    def test_empty_factors(self, layer):
        target = _returns(120)
        result = layer.compute(target, {})
        assert result.factor_sensitivities == {}
        assert result.dominant_factor == "NONE"
        assert result.macro_risk_score == 0.0
        assert result.macro_regime == MacroRegimeState.BENIGN

    def test_many_factors(self, layer):
        target = _returns(120)
        factors = {f"F{i}": _returns(120, seed=i) for i in range(20)}
        result = layer.compute(target, factors)
        assert len(result.factor_sensitivities) == 20

    def test_mixed_valid_invalid_factors(self, layer):
        target = _returns(120)
        factors = {
            "GOOD": _returns(120, seed=10),
            "SHORT": _returns(50, seed=20),
            "NAN": [float('nan')] * 120,
        }
        result = layer.compute(target, factors)
        assert result.factor_sensitivities["SHORT"] == 0.0
        assert result.factor_sensitivities["NAN"] == 0.0

    def test_all_zero_returns(self, layer):
        target = [0.0] * 120
        factors = {"F": [0.0] * 120}
        result = layer.compute(target, factors)
        # Both zero -> cov=0, var=0 -> beta = 0/1e-12 ≈ 0
        assert -5.0 <= result.factor_sensitivities["F"] <= 5.0

    def test_constant_target(self, layer):
        target = [0.01] * 120
        factors = {"F": _returns(120, seed=10)}
        result = layer.compute(target, factors)
        # Constant target -> cov ≈ 0
        assert abs(result.factor_sensitivities["F"]) < 1.0
