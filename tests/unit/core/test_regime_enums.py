# tests/unit/core/test_regime_enums.py
# Coverage target: jarvis/core/regime.py -> 95%+
# Missing lines: 237, 242, 246, 252, 257, 292, 296, 300, 307, 332-337, 354-358

import pytest

from jarvis.core.regime import (
    GlobalRegimeState,
    AssetRegimeState,
    AssetClass,
    CorrelationRegimeState,
    HierarchicalRegime,
    map_s05_to_canonical,
    map_latent_int_to_canonical,
)


def _default_args(**overrides):
    base = dict(
        global_regime=GlobalRegimeState.RISK_ON,
        asset_regimes={ac: AssetRegimeState.TRENDING_UP for ac in AssetClass},
        correlation_regime=CorrelationRegimeState.NORMAL,
        global_confidence=0.8,
        asset_confidences={ac: 0.8 for ac in AssetClass},
        sub_regime={ac: "default" for ac in AssetClass},
        sequence_id=1,
    )
    base.update(overrides)
    return base


# =============================================================================
# HierarchicalRegime.create validation (lines 237, 242, 246, 252, 257)
# =============================================================================

class TestHierarchicalRegimeCreate:
    def test_valid_creation(self):
        hr = HierarchicalRegime.create(**_default_args())
        assert hr.global_regime == GlobalRegimeState.RISK_ON
        assert hr.global_confidence == 0.8
        assert len(hr.regime_hash) == 16

    def test_confidence_below_zero_raises(self):
        # line 237
        with pytest.raises(ValueError, match="global_confidence"):
            HierarchicalRegime.create(**_default_args(global_confidence=-0.1))

    def test_confidence_above_one_raises(self):
        # line 237
        with pytest.raises(ValueError, match="global_confidence"):
            HierarchicalRegime.create(**_default_args(global_confidence=1.5))

    def test_asset_confidence_out_of_range_raises(self):
        # line 242
        bad_conf = {ac: 0.8 for ac in AssetClass}
        bad_conf[AssetClass.CRYPTO] = 2.0
        with pytest.raises(ValueError, match="asset_confidence"):
            HierarchicalRegime.create(**_default_args(asset_confidences=bad_conf))

    def test_negative_sequence_id_raises(self):
        # line 246
        with pytest.raises(ValueError, match="sequence_id"):
            HierarchicalRegime.create(**_default_args(sequence_id=-1))

    def test_crisis_without_shock_raises(self):
        # line 252
        ar = {ac: AssetRegimeState.TRENDING_UP for ac in AssetClass}
        with pytest.raises(ValueError, match="CRISIS override"):
            HierarchicalRegime.create(**_default_args(
                global_regime=GlobalRegimeState.CRISIS,
                asset_regimes=ar,
                correlation_regime=CorrelationRegimeState.BREAKDOWN,
            ))

    def test_crisis_without_breakdown_raises(self):
        # line 257
        ar = {ac: AssetRegimeState.SHOCK for ac in AssetClass}
        with pytest.raises(ValueError, match="CRISIS override"):
            HierarchicalRegime.create(**_default_args(
                global_regime=GlobalRegimeState.CRISIS,
                asset_regimes=ar,
                correlation_regime=CorrelationRegimeState.NORMAL,
            ))

    def test_valid_crisis(self):
        ar = {ac: AssetRegimeState.SHOCK for ac in AssetClass}
        hr = HierarchicalRegime.create(**_default_args(
            global_regime=GlobalRegimeState.CRISIS,
            asset_regimes=ar,
            correlation_regime=CorrelationRegimeState.BREAKDOWN,
        ))
        assert hr.global_regime == GlobalRegimeState.CRISIS


# =============================================================================
# HierarchicalRegime accessor methods (lines 292, 296, 300, 307)
# =============================================================================

class TestHierarchicalRegimeAccessors:
    def test_get_asset_regime_existing(self):
        hr = HierarchicalRegime.create(**_default_args())
        assert hr.get_asset_regime(AssetClass.CRYPTO) == AssetRegimeState.TRENDING_UP

    def test_get_asset_regime_missing_returns_unknown(self):
        # line 292
        hr = HierarchicalRegime.create(**_default_args(
            asset_regimes={AssetClass.CRYPTO: AssetRegimeState.TRENDING_UP},
        ))
        assert hr.get_asset_regime(AssetClass.FOREX) == AssetRegimeState.UNKNOWN

    def test_get_asset_confidence_existing(self):
        hr = HierarchicalRegime.create(**_default_args())
        assert hr.get_asset_confidence(AssetClass.CRYPTO) == 0.8

    def test_get_asset_confidence_missing_returns_zero(self):
        # line 296
        hr = HierarchicalRegime.create(**_default_args(
            asset_confidences={AssetClass.CRYPTO: 0.9},
        ))
        assert hr.get_asset_confidence(AssetClass.FOREX) == 0.0

    def test_is_crisis_true(self):
        # line 300
        ar = {ac: AssetRegimeState.SHOCK for ac in AssetClass}
        hr = HierarchicalRegime.create(**_default_args(
            global_regime=GlobalRegimeState.CRISIS,
            asset_regimes=ar,
            correlation_regime=CorrelationRegimeState.BREAKDOWN,
        ))
        assert hr.is_crisis() is True

    def test_is_crisis_false(self):
        hr = HierarchicalRegime.create(**_default_args())
        assert hr.is_crisis() is False

    def test_to_global_state_string(self):
        # line 307
        hr = HierarchicalRegime.create(**_default_args())
        assert hr.to_global_state_string() == "RISK_ON"


# =============================================================================
# map_s05_to_canonical (lines 332-337)
# =============================================================================

class TestMapS05ToCanonical:
    def test_low_v_trend(self):
        g, a = map_s05_to_canonical("LOW_V_TREND")
        assert g == GlobalRegimeState.RISK_ON
        assert a == AssetRegimeState.TRENDING_UP

    def test_high_v_trend(self):
        g, a = map_s05_to_canonical("HIGH_V_TREND")
        assert g == GlobalRegimeState.TRANSITION

    def test_low_v_rev(self):
        g, a = map_s05_to_canonical("LOW_V_REV")
        assert a == AssetRegimeState.RANGING_TIGHT

    def test_high_v_rev(self):
        g, a = map_s05_to_canonical("HIGH_V_REV")
        assert g == GlobalRegimeState.RISK_OFF
        assert a == AssetRegimeState.RANGING_WIDE

    def test_crisis(self):
        g, a = map_s05_to_canonical("CRISIS")
        assert g == GlobalRegimeState.CRISIS
        assert a == AssetRegimeState.SHOCK

    def test_unknown_raises_key_error(self):
        # lines 332-337
        with pytest.raises(KeyError, match="Unknown S05"):
            map_s05_to_canonical("INVALID_REGIME")


# =============================================================================
# map_latent_int_to_canonical (lines 354-358)
# =============================================================================

class TestMapLatentIntToCanonical:
    def test_valid_mappings(self):
        assert map_latent_int_to_canonical(0) == AssetRegimeState.TRENDING_UP
        assert map_latent_int_to_canonical(1) == AssetRegimeState.HIGH_VOLATILITY
        assert map_latent_int_to_canonical(2) == AssetRegimeState.RANGING_TIGHT
        assert map_latent_int_to_canonical(3) == AssetRegimeState.RANGING_WIDE
        assert map_latent_int_to_canonical(4) == AssetRegimeState.SHOCK

    def test_out_of_range_raises(self):
        # lines 354-358
        with pytest.raises(KeyError, match="out of range"):
            map_latent_int_to_canonical(5)

    def test_negative_raises(self):
        with pytest.raises(KeyError, match="out of range"):
            map_latent_int_to_canonical(-1)
