# tests/unit/core/test_pipeline_cov.py
# Coverage target: jarvis/orchestrator/pipeline.py -> 95%+
# Missing lines: 53, 130-163
#
# Line 53: mean_reversion = 0.0 when returns_history has < 2 elements
# Lines 130-163: Governance gate error path (invalid meta_uncertainty or regime)

import pytest

from jarvis.orchestrator.pipeline import run_full_pipeline, _extract_regime_features
from jarvis.core.regime import GlobalRegimeState
from jarvis.governance.exceptions import GovernanceViolationError


# Minimal valid returns history (20 elements required by RiskEngine)
_RETURNS_20 = [0.01, -0.02, 0.015, -0.005, 0.02,
               0.01, -0.01, 0.005, -0.015, 0.02,
               0.01, -0.02, 0.015, -0.005, 0.02,
               0.01, -0.01, 0.005, -0.015, 0.02]

_CAPITAL = 100_000.0
_ASSET_PRICES = {"ASSET": 500.0}


# =============================================================================
# Line 53: _extract_regime_features with single-element returns (n < 2)
# =============================================================================

class TestExtractRegimeFeaturesSingleElement:
    def test_single_return_mean_reversion_zero(self):
        # line 53: n < 2 → mean_reversion = 0.0
        features = _extract_regime_features([0.05])
        assert features["mean_reversion"] == 0.0
        assert "volatility" in features
        assert "stress" in features

    def test_single_return_all_keys_present(self):
        features = _extract_regime_features([0.01])
        expected_keys = {"volatility", "trend_strength", "mean_reversion",
                         "stress", "momentum", "liquidity"}
        assert set(features.keys()) == expected_keys


# =============================================================================
# Lines 130-163: Governance gate error path
# =============================================================================

class TestGovernanceGate:
    def test_meta_uncertainty_above_one_raises_governance_error(self):
        # GOV-01 violation: meta_uncertainty > 1.0
        with pytest.raises(GovernanceViolationError):
            run_full_pipeline(
                returns_history=_RETURNS_20,
                current_regime=GlobalRegimeState.RISK_ON,
                meta_uncertainty=2.0,
                total_capital=_CAPITAL,
                asset_prices=_ASSET_PRICES,
            )

    def test_meta_uncertainty_negative_raises_governance_error(self):
        # GOV-01 violation: meta_uncertainty < 0.0
        with pytest.raises(GovernanceViolationError):
            run_full_pipeline(
                returns_history=_RETURNS_20,
                current_regime=GlobalRegimeState.RISK_ON,
                meta_uncertainty=-0.5,
                total_capital=_CAPITAL,
                asset_prices=_ASSET_PRICES,
            )

    def test_invalid_regime_type_raises_governance_error(self):
        # GOV-05 violation: regime is not GlobalRegimeState
        with pytest.raises(GovernanceViolationError):
            run_full_pipeline(
                returns_history=_RETURNS_20,
                current_regime="RISK_ON",
                meta_uncertainty=0.2,
                total_capital=_CAPITAL,
                asset_prices=_ASSET_PRICES,
            )

    def test_both_meta_and_regime_invalid_raises(self):
        # Both GOV-01 and GOV-05 violated
        with pytest.raises(GovernanceViolationError):
            run_full_pipeline(
                returns_history=_RETURNS_20,
                current_regime="INVALID",
                meta_uncertainty=5.0,
                total_capital=_CAPITAL,
                asset_prices=_ASSET_PRICES,
            )

    def test_invalid_regime_with_bad_capital(self):
        # GOV-05 violated, capital also bad → safe_capital fallback to 1.0
        with pytest.raises(GovernanceViolationError):
            run_full_pipeline(
                returns_history=_RETURNS_20,
                current_regime="BAD",
                meta_uncertainty=0.2,
                total_capital=-1.0,
                asset_prices=_ASSET_PRICES,
            )

    def test_non_numeric_meta_raises(self):
        # meta_uncertainty is not a number
        with pytest.raises((GovernanceViolationError, TypeError)):
            run_full_pipeline(
                returns_history=_RETURNS_20,
                current_regime=GlobalRegimeState.RISK_ON,
                meta_uncertainty="high",
                total_capital=_CAPITAL,
                asset_prices=_ASSET_PRICES,
            )

    def test_valid_inputs_pass_gate(self):
        # Confirm valid inputs pass governance gate
        result = run_full_pipeline(
            returns_history=_RETURNS_20,
            current_regime=GlobalRegimeState.RISK_ON,
            meta_uncertainty=0.5,
            total_capital=_CAPITAL,
            asset_prices=_ASSET_PRICES,
        )
        assert isinstance(result, dict)
        assert "ASSET" in result
