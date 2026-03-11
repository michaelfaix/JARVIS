# =============================================================================
# tests/unit/intelligence/test_ood_engine.py -- OOD Engine Tests
#
# Comprehensive tests for jarvis/intelligence/ood_engine.py (Phase MA-4).
# Covers: AssetConditionalOOD, 4-component scoring, asset-specific thresholds,
#         FAS invariant (10% crypto=normal vs FX=extreme), determinism,
#         immutability, edge cases.
# =============================================================================

import pytest

from jarvis.core.regime import (
    AssetClass,
    AssetRegimeState,
    CorrelationRegimeState,
    GlobalRegimeState,
    HierarchicalRegime,
)
from jarvis.intelligence.ood_config import (
    SEVERITY_CRITICAL,
    SEVERITY_HIGH,
    SEVERITY_MEDIUM,
    SEVERITY_LOW,
    REGIME_OOD_WEIGHT,
)
from jarvis.intelligence.ood_engine import (
    # Helpers
    _clip,
    _zscore_ood,
    # Dataclasses
    OODComponentScores,
    OODResult,
    # Detector
    AssetConditionalOOD,
)


# ---------------------------------------------------------------------------
# SHARED FIXTURES
# ---------------------------------------------------------------------------

def _make_regime(
    global_regime: GlobalRegimeState = GlobalRegimeState.RISK_ON,
    correlation: CorrelationRegimeState = CorrelationRegimeState.NORMAL,
    asset_state: AssetRegimeState = AssetRegimeState.TRENDING_UP,
) -> HierarchicalRegime:
    if global_regime == GlobalRegimeState.CRISIS:
        asset_state = AssetRegimeState.SHOCK
        correlation = CorrelationRegimeState.BREAKDOWN
    return HierarchicalRegime.create(
        global_regime=global_regime,
        asset_regimes={ac: asset_state for ac in AssetClass},
        correlation_regime=correlation,
        global_confidence=0.8,
        asset_confidences={ac: 0.8 for ac in AssetClass},
        sub_regime={ac: "test" for ac in AssetClass},
        sequence_id=0,
    )


CALM_REGIME = _make_regime()

# Normal feature vector: all features at their mean
CALM_FEATURES = [0.0] * 99
CALM_MEAN = [0.0] * 99
CALM_STD = [1.0] * 99

CALM_KWARGS = dict(
    features=CALM_FEATURES,
    reference_mean=CALM_MEAN,
    reference_std=CALM_STD,
    recent_return=0.001,
    current_volatility=0.2,
    historical_volatility=0.2,
    liquidity_score=0.9,
    macro_event_scores={},
    regime=CALM_REGIME,
)


def _detect(asset_class: AssetClass = AssetClass.CRYPTO, **overrides):
    kwargs = {**CALM_KWARGS, "asset_class": asset_class, **overrides}
    return AssetConditionalOOD().detect(**kwargs)


# ---------------------------------------------------------------------------
# CLIP HELPER
# ---------------------------------------------------------------------------

class TestClip:
    def test_within_range(self):
        assert _clip(0.5, 0.0, 1.0) == 0.5

    def test_below(self):
        assert _clip(-0.1, 0.0, 1.0) == 0.0

    def test_above(self):
        assert _clip(1.5, 0.0, 1.0) == 1.0

    def test_at_boundary(self):
        assert _clip(0.0, 0.0, 1.0) == 0.0
        assert _clip(1.0, 0.0, 1.0) == 1.0


# ---------------------------------------------------------------------------
# ZSCORE OOD
# ---------------------------------------------------------------------------

class TestZscoreOOD:
    def test_at_mean_is_zero(self):
        features = [0.0, 0.0, 0.0]
        mean = [0.0, 0.0, 0.0]
        std = [1.0, 1.0, 1.0]
        assert _zscore_ood(features, mean, std) == 0.0

    def test_outliers_increase_score(self):
        features = [5.0, 5.0, 5.0]  # 5 sigma
        mean = [0.0, 0.0, 0.0]
        std = [1.0, 1.0, 1.0]
        score = _zscore_ood(features, mean, std)
        assert score > 0.5

    def test_all_outliers_high_score(self):
        features = [10.0] * 20
        mean = [0.0] * 20
        std = [1.0] * 20
        score = _zscore_ood(features, mean, std)
        assert score > 0.8

    def test_empty_features(self):
        assert _zscore_ood([], [], []) == 0.0

    def test_zero_std_ignored(self):
        features = [5.0, 0.0]
        mean = [0.0, 0.0]
        std = [0.0, 1.0]  # First feature has zero std
        score = _zscore_ood(features, mean, std)
        # Only second feature counted (at mean, z=0)
        assert score == 0.0

    def test_all_zero_std(self):
        features = [5.0, 5.0]
        mean = [0.0, 0.0]
        std = [0.0, 0.0]
        assert _zscore_ood(features, mean, std) == 0.0

    def test_mismatched_lengths(self):
        features = [1.0, 2.0, 3.0]
        mean = [0.0, 0.0]
        std = [1.0]
        score = _zscore_ood(features, mean, std)
        # min(3, 2, 1) = 1 feature evaluated
        assert isinstance(score, float)


# ---------------------------------------------------------------------------
# OOD RESULT DATACLASS
# ---------------------------------------------------------------------------

class TestOODResult:
    def test_frozen(self):
        r = _detect()
        with pytest.raises(AttributeError):
            r.is_ood = True

    def test_all_fields_present(self):
        r = _detect()
        assert isinstance(r.is_ood, bool)
        assert isinstance(r.score, float)
        assert isinstance(r.severity, str)
        assert isinstance(r.components, OODComponentScores)
        assert isinstance(r.asset_class, AssetClass)
        assert isinstance(r.threshold, float)
        assert isinstance(r.result_hash, str)

    def test_result_hash_hex(self):
        r = _detect()
        assert len(r.result_hash) == 16
        assert all(c in "0123456789abcdef" for c in r.result_hash)


class TestOODComponentScores:
    def test_frozen(self):
        s = OODComponentScores(distribution=0.1, event=0.2, macro=0.3, regime=0.4)
        with pytest.raises(AttributeError):
            s.distribution = 0.5


# ---------------------------------------------------------------------------
# CALM MARKET (no OOD)
# ---------------------------------------------------------------------------

class TestCalmMarket:
    def test_calm_crypto_not_ood(self):
        r = _detect(asset_class=AssetClass.CRYPTO)
        assert r.is_ood is False
        assert r.score < 0.5

    def test_calm_forex_not_ood(self):
        r = _detect(asset_class=AssetClass.FOREX)
        assert r.is_ood is False

    def test_calm_indices_not_ood(self):
        r = _detect(asset_class=AssetClass.INDICES)
        assert r.is_ood is False

    def test_calm_commodities_not_ood(self):
        r = _detect(asset_class=AssetClass.COMMODITIES)
        assert r.is_ood is False

    def test_calm_rates_not_ood(self):
        r = _detect(asset_class=AssetClass.RATES)
        assert r.is_ood is False

    def test_calm_severity_low(self):
        r = _detect()
        assert r.severity == SEVERITY_LOW

    def test_calm_components_near_zero(self):
        r = _detect()
        assert r.components.distribution == 0.0
        assert r.components.macro == 0.0
        assert r.components.regime == 0.0


# ---------------------------------------------------------------------------
# FAS INVARIANT: 10% MOVE CRYPTO=NORMAL, FX=EXTREME
# ---------------------------------------------------------------------------

class TestAssetSensitivityDifference:
    def test_10pct_move_crypto_not_ood(self):
        """FAS: 10% move is normal for crypto (threshold=0.15)."""
        r = _detect(
            asset_class=AssetClass.CRYPTO,
            recent_return=-0.10,
        )
        # 0.10 < 0.15 threshold, event_ood low
        assert r.is_ood is False

    def test_10pct_move_forex_event_extreme(self):
        """FAS: 10% move is extreme for FX (threshold=0.03)."""
        r_fx = _detect(
            asset_class=AssetClass.FOREX,
            recent_return=-0.10,
        )
        r_crypto = _detect(
            asset_class=AssetClass.CRYPTO,
            recent_return=-0.10,
        )
        # FX event score much higher than crypto for same move
        assert r_fx.components.event > r_crypto.components.event
        # FX flash score maxed (0.10/0.03 >> 1.0)
        assert r_fx.components.event > 0.3

    def test_10pct_move_forex_with_stress_is_ood(self):
        """FAS: 10% flash crash + vol spike + macro event -> OOD for FX."""
        r = _detect(
            asset_class=AssetClass.FOREX,
            recent_return=-0.10,
            current_volatility=0.5,
            historical_volatility=0.1,
            liquidity_score=0.2,
            macro_event_scores={"fed_meeting": 0.8},
        )
        # event=1.0*0.3 + macro=0.72*0.4 + regime_ood*0.1 > 0.5
        assert r.is_ood is True

    def test_3pct_move_crypto_not_ood(self):
        r = _detect(asset_class=AssetClass.CRYPTO, recent_return=-0.03)
        assert r.is_ood is False

    def test_3pct_move_forex_event_score_high(self):
        r = _detect(asset_class=AssetClass.FOREX, recent_return=-0.03)
        # 0.03 / 0.03 = 1.0 flash score
        assert r.components.event > 0.2

    def test_2pct_move_rates_high_event(self):
        """FAS: 2% move is extreme for rates (threshold=0.02)."""
        r = _detect(asset_class=AssetClass.RATES, recent_return=-0.02)
        assert r.components.event > 0.2


# ---------------------------------------------------------------------------
# EVENT OOD COMPONENT
# ---------------------------------------------------------------------------

class TestEventOOD:
    def test_flash_crash_increases_score(self):
        calm = _detect(asset_class=AssetClass.CRYPTO, recent_return=0.001)
        crash = _detect(asset_class=AssetClass.CRYPTO, recent_return=-0.20)
        assert crash.components.event > calm.components.event

    def test_vol_spike_increases_score(self):
        calm = _detect(current_volatility=0.2, historical_volatility=0.2)
        spike = _detect(current_volatility=0.6, historical_volatility=0.2)
        assert spike.components.event > calm.components.event

    def test_liquidity_drain_increases_score(self):
        calm = _detect(liquidity_score=0.9)
        drain = _detect(liquidity_score=0.1)
        assert drain.components.event > calm.components.event

    def test_zero_volatility_safe(self):
        r = _detect(current_volatility=0.0, historical_volatility=0.0)
        assert isinstance(r.components.event, float)

    def test_negative_return_same_as_positive(self):
        r1 = _detect(recent_return=-0.05)
        r2 = _detect(recent_return=0.05)
        assert r1.components.event == r2.components.event


# ---------------------------------------------------------------------------
# MACRO OOD COMPONENT
# ---------------------------------------------------------------------------

class TestMacroOOD:
    def test_no_events_zero(self):
        r = _detect(macro_event_scores={})
        assert r.components.macro == 0.0

    def test_fed_meeting_crypto_moderate(self):
        r = _detect(
            asset_class=AssetClass.CRYPTO,
            macro_event_scores={"fed_meeting": 1.0},
        )
        # Crypto fed_meeting sensitivity = 0.5
        assert abs(r.components.macro - 0.5) < 1e-6

    def test_fed_meeting_forex_high(self):
        r = _detect(
            asset_class=AssetClass.FOREX,
            macro_event_scores={"fed_meeting": 1.0},
        )
        # Forex fed_meeting sensitivity = 0.9
        assert abs(r.components.macro - 0.9) < 1e-6

    def test_multiple_events_takes_max(self):
        r = _detect(
            asset_class=AssetClass.INDICES,
            macro_event_scores={
                "fed_meeting": 0.5,
                "credit_event": 1.0,
            },
        )
        # credit_event sensitivity = 0.9 -> 1.0 * 0.9 = 0.9
        # fed_meeting sensitivity = 0.8 -> 0.5 * 0.8 = 0.4
        assert abs(r.components.macro - 0.9) < 1e-6

    def test_unknown_event_zero_sensitivity(self):
        r = _detect(macro_event_scores={"unknown_event": 1.0})
        assert r.components.macro == 0.0

    def test_event_importance_scaled(self):
        r1 = _detect(
            asset_class=AssetClass.FOREX,
            macro_event_scores={"fed_meeting": 0.5},
        )
        r2 = _detect(
            asset_class=AssetClass.FOREX,
            macro_event_scores={"fed_meeting": 1.0},
        )
        assert r2.components.macro > r1.components.macro


# ---------------------------------------------------------------------------
# REGIME OOD COMPONENT
# ---------------------------------------------------------------------------

class TestRegimeOOD:
    def test_calm_regime_zero(self):
        r = _detect(regime=_make_regime())
        assert r.components.regime == 0.0

    def test_crisis_regime_max(self):
        r = _detect(regime=_make_regime(global_regime=GlobalRegimeState.CRISIS))
        assert r.components.regime == 1.0

    def test_breakdown_high(self):
        # BREAKDOWN requires CRISIS global per invariant
        r = _detect(regime=_make_regime(
            global_regime=GlobalRegimeState.CRISIS,
        ))
        # Both crisis (1.0) and breakdown (0.8) fire, max = 1.0
        assert r.components.regime == 1.0

    def test_risk_off_with_high_vol(self):
        r = _detect(
            asset_class=AssetClass.CRYPTO,
            regime=_make_regime(
                global_regime=GlobalRegimeState.RISK_OFF,
                asset_state=AssetRegimeState.HIGH_VOLATILITY,
            ),
        )
        assert r.components.regime == 0.5

    def test_risk_off_without_high_vol(self):
        r = _detect(
            regime=_make_regime(
                global_regime=GlobalRegimeState.RISK_OFF,
                asset_state=AssetRegimeState.TRENDING_DOWN,
            ),
        )
        assert r.components.regime == 0.0


# ---------------------------------------------------------------------------
# DISTRIBUTION OOD COMPONENT
# ---------------------------------------------------------------------------

class TestDistributionOOD:
    def test_normal_features_zero(self):
        r = _detect(features=[0.0] * 99)
        assert r.components.distribution == 0.0

    def test_extreme_features_high(self):
        r = _detect(features=[10.0] * 99)
        assert r.components.distribution > 0.5

    def test_mixed_features(self):
        features = [0.0] * 80 + [5.0] * 19  # ~20% outliers
        r = _detect(features=features)
        assert 0.0 < r.components.distribution < 1.0


# ---------------------------------------------------------------------------
# THRESHOLD BEHAVIOR
# ---------------------------------------------------------------------------

class TestThresholdBehavior:
    def test_crypto_threshold_stored(self):
        r = _detect(asset_class=AssetClass.CRYPTO)
        assert r.threshold == 0.7

    def test_forex_threshold_stored(self):
        r = _detect(asset_class=AssetClass.FOREX)
        assert r.threshold == 0.5

    def test_indices_threshold_stored(self):
        r = _detect(asset_class=AssetClass.INDICES)
        assert r.threshold == 0.6

    def test_score_above_threshold_is_ood(self):
        """Force high OOD score to exceed any threshold."""
        r = _detect(
            asset_class=AssetClass.CRYPTO,
            features=[10.0] * 99,
            recent_return=-0.30,
            current_volatility=1.0,
            historical_volatility=0.1,
            liquidity_score=0.0,
            macro_event_scores={"credit_event": 1.0},
            regime=_make_regime(global_regime=GlobalRegimeState.CRISIS),
        )
        assert r.is_ood is True
        assert r.severity in (SEVERITY_CRITICAL, SEVERITY_HIGH)


# ---------------------------------------------------------------------------
# ASSET CLASS STORED
# ---------------------------------------------------------------------------

class TestAssetClassStored:
    def test_crypto(self):
        assert _detect(asset_class=AssetClass.CRYPTO).asset_class == AssetClass.CRYPTO

    def test_forex(self):
        assert _detect(asset_class=AssetClass.FOREX).asset_class == AssetClass.FOREX

    def test_all_asset_classes(self):
        for ac in AssetClass:
            r = _detect(asset_class=ac)
            assert r.asset_class == ac


# ---------------------------------------------------------------------------
# SCORE RANGE
# ---------------------------------------------------------------------------

class TestScoreRange:
    def test_score_in_range(self):
        for ac in AssetClass:
            r = _detect(asset_class=ac)
            assert 0.0 <= r.score <= 1.0

    def test_extreme_score_capped(self):
        r = _detect(
            features=[10.0] * 99,
            recent_return=-0.50,
            current_volatility=2.0,
            historical_volatility=0.1,
            liquidity_score=0.0,
            macro_event_scores={"fed_meeting": 1.0, "credit_event": 1.0},
            regime=_make_regime(global_regime=GlobalRegimeState.CRISIS),
        )
        assert r.score <= 1.0


# ---------------------------------------------------------------------------
# DETERMINISM (DET-05)
# ---------------------------------------------------------------------------

class TestDeterminism:
    def test_same_inputs_same_result(self):
        r1 = _detect()
        r2 = _detect()
        assert r1.is_ood == r2.is_ood
        assert r1.score == r2.score
        assert r1.severity == r2.severity
        assert r1.result_hash == r2.result_hash

    def test_different_inputs_different_hash(self):
        r1 = _detect(recent_return=0.001)
        r2 = _detect(recent_return=-0.20)
        assert r1.result_hash != r2.result_hash

    def test_fresh_instance_per_call(self):
        d = AssetConditionalOOD()
        r1 = d.detect(**{**CALM_KWARGS, "asset_class": AssetClass.CRYPTO})
        r2 = d.detect(**{
            **CALM_KWARGS,
            "asset_class": AssetClass.CRYPTO,
            "recent_return": -0.30,
        })
        assert r1.score != r2.score


# ---------------------------------------------------------------------------
# EDGE CASES
# ---------------------------------------------------------------------------

class TestEdgeCases:
    def test_zero_return(self):
        r = _detect(recent_return=0.0)
        assert r.components.event >= 0.0

    def test_zero_volatility(self):
        r = _detect(current_volatility=0.0, historical_volatility=0.0)
        assert isinstance(r.score, float)

    def test_liquidity_score_zero(self):
        r = _detect(liquidity_score=0.0)
        assert r.components.event > 0.0

    def test_liquidity_score_one(self):
        r = _detect(liquidity_score=1.0)
        # No liquidity drain
        assert isinstance(r.score, float)

    def test_negative_return(self):
        r = _detect(recent_return=-0.5)
        assert r.components.event > 0.0

    def test_empty_features(self):
        r = _detect(features=[], reference_mean=[], reference_std=[])
        assert r.components.distribution == 0.0


# ---------------------------------------------------------------------------
# PACKAGE IMPORT
# ---------------------------------------------------------------------------

class TestPackageImport:
    def test_import_all(self):
        from jarvis.intelligence.ood_engine import (
            AssetConditionalOOD,
            OODResult,
            OODComponentScores,
        )
        assert AssetConditionalOOD is not None
        assert OODResult is not None
        assert OODComponentScores is not None
