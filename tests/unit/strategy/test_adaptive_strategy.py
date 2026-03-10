# =============================================================================
# Tests for jarvis/strategy/adaptive_strategy.py (S26)
# =============================================================================

import pytest

from jarvis.core.regime import GlobalRegimeState, NewsRegimeState
from jarvis.strategy.adaptive_strategy import (
    AdaptiveStrategySelector,
    STRATEGY_CONFIGS,
    StrategyMode,
    StrategyModeConfig,
    StrategySelection,
)


# ---------------------------------------------------------------------------
# HELPERS
# ---------------------------------------------------------------------------

@pytest.fixture
def selector():
    return AdaptiveStrategySelector()


# ---------------------------------------------------------------------------
# STRATEGY MODE ENUM
# ---------------------------------------------------------------------------

class TestStrategyModeEnum:
    def test_all_modes(self):
        assert StrategyMode.MOMENTUM.value == "MOMENTUM"
        assert StrategyMode.MEAN_REVERSION.value == "MEAN_REVERSION"
        assert StrategyMode.RISK_REDUCTION.value == "RISK_REDUCTION"
        assert StrategyMode.DEFENSIVE.value == "DEFENSIVE"
        assert StrategyMode.MINIMAL_EXPOSURE.value == "MINIMAL_EXPOSURE"

    def test_five_modes(self):
        assert len(StrategyMode) == 5


# ---------------------------------------------------------------------------
# STRATEGY CONFIGS
# ---------------------------------------------------------------------------

class TestStrategyConfigs:
    def test_all_modes_have_config(self):
        for mode in StrategyMode:
            assert mode in STRATEGY_CONFIGS

    def test_configs_immutable(self):
        cfg = STRATEGY_CONFIGS[StrategyMode.MOMENTUM]
        with pytest.raises(AttributeError):
            cfg.label = "CHANGED"

    def test_momentum_config(self):
        cfg = STRATEGY_CONFIGS[StrategyMode.MOMENTUM]
        assert cfg.label == "MOMENTUM"
        assert cfg.confidence_box_scale == 1.0
        assert cfg.max_exposure_pct == 0.80
        assert cfg.position_size_cap == 0.9
        assert cfg.recalibration_priority == "LOW"

    def test_mean_reversion_config(self):
        cfg = STRATEGY_CONFIGS[StrategyMode.MEAN_REVERSION]
        assert cfg.label == "MEAN_REVERSION"
        assert cfg.confidence_box_scale == 0.7
        assert cfg.max_exposure_pct == 0.65
        assert cfg.position_size_cap == 0.7
        assert cfg.recalibration_priority == "MEDIUM"

    def test_risk_reduction_config(self):
        cfg = STRATEGY_CONFIGS[StrategyMode.RISK_REDUCTION]
        assert cfg.label == "RISK_REDUCTION"
        assert cfg.confidence_box_scale == 1.4
        assert cfg.max_exposure_pct == 0.40
        assert cfg.position_size_cap == 0.45
        assert cfg.recalibration_priority == "HIGH"

    def test_defensive_config(self):
        cfg = STRATEGY_CONFIGS[StrategyMode.DEFENSIVE]
        assert cfg.label == "DEFENSIVE"
        assert cfg.confidence_box_scale == 2.0
        assert cfg.max_exposure_pct == 0.20
        assert cfg.position_size_cap == 0.2
        assert cfg.recalibration_priority == "CRITICAL"

    def test_minimal_exposure_config(self):
        cfg = STRATEGY_CONFIGS[StrategyMode.MINIMAL_EXPOSURE]
        assert cfg.label == "MINIMAL_EXPOSURE"
        assert cfg.confidence_box_scale == 2.5
        assert cfg.max_exposure_pct == 0.10
        assert cfg.position_size_cap == 0.1
        assert cfg.recalibration_priority == "CRITICAL"

    def test_exposure_decreasing_by_risk(self):
        """More defensive modes should have lower max exposure."""
        assert (STRATEGY_CONFIGS[StrategyMode.MOMENTUM].max_exposure_pct
                > STRATEGY_CONFIGS[StrategyMode.MEAN_REVERSION].max_exposure_pct
                > STRATEGY_CONFIGS[StrategyMode.RISK_REDUCTION].max_exposure_pct
                > STRATEGY_CONFIGS[StrategyMode.DEFENSIVE].max_exposure_pct
                > STRATEGY_CONFIGS[StrategyMode.MINIMAL_EXPOSURE].max_exposure_pct)


# ---------------------------------------------------------------------------
# SELECT — REGIME MAPPING
# ---------------------------------------------------------------------------

class TestSelectRegimeMapping:
    def test_trending_to_momentum(self, selector):
        result = selector.select("TRENDING", False, 0.2)
        assert result.mode == StrategyMode.MOMENTUM

    def test_ranging_to_mean_reversion(self, selector):
        result = selector.select("RANGING", False, 0.2)
        assert result.mode == StrategyMode.MEAN_REVERSION

    def test_high_vol_to_risk_reduction(self, selector):
        result = selector.select("HIGH_VOL", False, 0.5)
        assert result.mode == StrategyMode.RISK_REDUCTION

    def test_shock_to_defensive(self, selector):
        result = selector.select("SHOCK", False, 0.8)
        assert result.mode == StrategyMode.DEFENSIVE

    def test_unknown_to_minimal_exposure(self, selector):
        result = selector.select("UNKNOWN", False, 0.3)
        assert result.mode == StrategyMode.MINIMAL_EXPOSURE

    def test_unrecognized_regime_to_minimal(self, selector):
        result = selector.select("SOME_NEW_REGIME", False, 0.3)
        assert result.mode == StrategyMode.MINIMAL_EXPOSURE


# ---------------------------------------------------------------------------
# SELECT — PRIORITY: RISK COMPRESSION
# ---------------------------------------------------------------------------

class TestSelectRiskCompression:
    def test_risk_compression_overrides_trending(self, selector):
        result = selector.select("TRENDING", True, 0.1)
        assert result.mode == StrategyMode.DEFENSIVE

    def test_risk_compression_overrides_ranging(self, selector):
        result = selector.select("RANGING", True, 0.1)
        assert result.mode == StrategyMode.DEFENSIVE

    def test_risk_compression_reason(self, selector):
        result = selector.select("TRENDING", True, 0.1)
        assert "Risk compression" in result.activation_reason
        assert "active=True" in result.activation_reason


# ---------------------------------------------------------------------------
# SELECT — PRIORITY: NEWS SHOCK
# ---------------------------------------------------------------------------

class TestSelectNewsShock:
    def test_shock_news_overrides_trending(self, selector):
        result = selector.select("TRENDING", False, 0.1, news_regime="SHOCK")
        assert result.mode == StrategyMode.DEFENSIVE

    def test_shock_news_reason(self, selector):
        result = selector.select("TRENDING", False, 0.1, news_regime="SHOCK")
        assert "news_regime=SHOCK" in result.activation_reason

    def test_non_shock_news_no_override(self, selector):
        result = selector.select("TRENDING", False, 0.1, news_regime="QUIET")
        assert result.mode == StrategyMode.MOMENTUM

    def test_active_news_no_override(self, selector):
        result = selector.select("TRENDING", False, 0.1, news_regime="ACTIVE")
        assert result.mode == StrategyMode.MOMENTUM


# ---------------------------------------------------------------------------
# SELECT — PRIORITY: CRITICAL LIQUIDITY
# ---------------------------------------------------------------------------

class TestSelectCriticalLiquidity:
    def test_low_liquidity_defensive(self, selector):
        result = selector.select("TRENDING", False, 0.1, liquidity_score=0.1)
        assert result.mode == StrategyMode.DEFENSIVE

    def test_low_liquidity_reason(self, selector):
        result = selector.select("TRENDING", False, 0.1, liquidity_score=0.15)
        assert "Critical liquidity" in result.activation_reason
        assert "0.150" in result.activation_reason

    def test_boundary_0_2_not_triggered(self, selector):
        result = selector.select("TRENDING", False, 0.1, liquidity_score=0.2)
        assert result.mode == StrategyMode.MOMENTUM

    def test_risk_compression_higher_priority_than_liquidity(self, selector):
        result = selector.select("TRENDING", True, 0.1, liquidity_score=0.1)
        assert "Risk compression" in result.activation_reason


# ---------------------------------------------------------------------------
# SELECT — PRIORITY: UNKNOWN REGIME
# ---------------------------------------------------------------------------

class TestSelectUnknownRegime:
    def test_unknown_minimal_exposure(self, selector):
        result = selector.select("UNKNOWN", False, 0.3)
        assert result.mode == StrategyMode.MINIMAL_EXPOSURE
        assert "unbekannt" in result.activation_reason.lower()

    def test_risk_compression_higher_than_unknown(self, selector):
        result = selector.select("UNKNOWN", True, 0.3)
        assert result.mode == StrategyMode.DEFENSIVE


# ---------------------------------------------------------------------------
# SELECT — OVERRIDE LOCKED
# ---------------------------------------------------------------------------

class TestOverrideLocked:
    def test_always_locked(self, selector):
        for regime in ["TRENDING", "RANGING", "HIGH_VOL", "SHOCK", "UNKNOWN"]:
            result = selector.select(regime, False, 0.2)
            assert result.override_locked is True

    def test_locked_with_risk_compression(self, selector):
        result = selector.select("TRENDING", True, 0.2)
        assert result.override_locked is True

    def test_locked_with_shock_news(self, selector):
        result = selector.select("TRENDING", False, 0.2, news_regime="SHOCK")
        assert result.override_locked is True


# ---------------------------------------------------------------------------
# SELECT — CONFIG ATTACHMENT
# ---------------------------------------------------------------------------

class TestSelectConfig:
    def test_config_matches_mode(self, selector):
        for regime, expected_mode in [
            ("TRENDING", StrategyMode.MOMENTUM),
            ("RANGING", StrategyMode.MEAN_REVERSION),
            ("HIGH_VOL", StrategyMode.RISK_REDUCTION),
            ("SHOCK", StrategyMode.DEFENSIVE),
            ("UNKNOWN", StrategyMode.MINIMAL_EXPOSURE),
        ]:
            result = selector.select(regime, False, 0.2)
            assert result.config is STRATEGY_CONFIGS[expected_mode]


# ---------------------------------------------------------------------------
# STRATEGY SELECTION DATACLASS
# ---------------------------------------------------------------------------

class TestStrategySelection:
    def test_fields(self):
        sel = StrategySelection(
            mode=StrategyMode.MOMENTUM,
            config=STRATEGY_CONFIGS[StrategyMode.MOMENTUM],
            activation_reason="test",
        )
        assert sel.mode == StrategyMode.MOMENTUM
        assert sel.override_locked is True

    def test_default_override_locked(self):
        sel = StrategySelection(
            mode=StrategyMode.DEFENSIVE,
            config=STRATEGY_CONFIGS[StrategyMode.DEFENSIVE],
            activation_reason="reason",
        )
        assert sel.override_locked is True


# ---------------------------------------------------------------------------
# DETERMINISM
# ---------------------------------------------------------------------------

class TestDeterminism:
    def test_same_inputs_same_output(self, selector):
        r1 = selector.select("TRENDING", False, 0.2, "QUIET", 0.8)
        r2 = selector.select("TRENDING", False, 0.2, "QUIET", 0.8)
        assert r1.mode == r2.mode
        assert r1.activation_reason == r2.activation_reason

    def test_no_state_between_calls(self, selector):
        selector.select("SHOCK", True, 0.9, "SHOCK", 0.1)
        result = selector.select("TRENDING", False, 0.1)
        assert result.mode == StrategyMode.MOMENTUM


# ---------------------------------------------------------------------------
# REGIME_TO_STRATEGY MAP
# ---------------------------------------------------------------------------

class TestRegimeToStrategyMap:
    def test_all_entries(self):
        expected = {
            "TRENDING": StrategyMode.MOMENTUM,
            "RANGING": StrategyMode.MEAN_REVERSION,
            "HIGH_VOL": StrategyMode.RISK_REDUCTION,
            "SHOCK": StrategyMode.DEFENSIVE,
            "UNKNOWN": StrategyMode.MINIMAL_EXPOSURE,
        }
        assert AdaptiveStrategySelector.REGIME_TO_STRATEGY == expected
