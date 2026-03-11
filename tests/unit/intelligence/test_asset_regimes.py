# =============================================================================
# tests/unit/intelligence/test_asset_regimes.py -- Asset Regime Detector Tests
#
# Comprehensive tests for jarvis/intelligence/asset_regimes.py (Phase MA-3).
# Covers: CryptoRegimeDetector, ForexRegimeDetector, IndicesRegimeDetector,
#         CommoditiesRegimeDetector, global conditioning, canonical mappings,
#         determinism, immutability.
# =============================================================================

import pytest

from jarvis.core.regime import AssetRegimeState, GlobalRegimeState
from jarvis.intelligence.global_regime import GlobalMacroDetector
from jarvis.intelligence.asset_regimes import (
    # State definitions
    CRYPTO_STATES,
    FOREX_STATES,
    INDICES_STATES,
    COMMODITIES_STATES,
    # Mappings
    _CRYPTO_TO_CANONICAL,
    _FOREX_TO_CANONICAL,
    _INDICES_TO_CANONICAL,
    _COMMODITIES_TO_CANONICAL,
    # Result
    AssetRegimeResult,
    # Detectors
    CryptoRegimeDetector,
    ForexRegimeDetector,
    IndicesRegimeDetector,
    CommoditiesRegimeDetector,
    # Helpers
    _normalize_probs,
    _max_state,
    # Thresholds
    CRYPTO_HIGH_FUNDING_RATE,
    CRYPTO_EXTREME_LIQUIDATION,
    FOREX_CB_PROXIMITY_DAYS,
    INDICES_VIX_PANIC,
)


# ---------------------------------------------------------------------------
# SHARED FIXTURES
# ---------------------------------------------------------------------------

def _calm_global():
    """Create a calm global macro result (risk_on)."""
    return GlobalMacroDetector().detect(
        vix_level=12.0, vix_term_structure=0.1, credit_spread_bps=100.0,
        fed_rate=5.0, fed_direction="holding",
        repo_rate_spread=0.1, ted_spread=0.1,
    )


def _risk_off_global():
    """Create a risk_off global macro result."""
    return GlobalMacroDetector().detect(
        vix_level=32.0, vix_term_structure=0.0, credit_spread_bps=300.0,
        fed_rate=5.0, fed_direction="holding",
        repo_rate_spread=0.3, ted_spread=0.2,
    )


def _panic_global():
    """Create a panic global macro result."""
    return GlobalMacroDetector().detect(
        vix_level=50.0, vix_term_structure=-0.3, credit_spread_bps=500.0,
        fed_rate=5.0, fed_direction="holding",
        repo_rate_spread=0.3, ted_spread=0.2,
    )


# ---------------------------------------------------------------------------
# STATE DEFINITIONS
# ---------------------------------------------------------------------------

class TestStateDefinitions:
    def test_crypto_5_states(self):
        assert len(CRYPTO_STATES) == 5
        assert "leverage_mania" in CRYPTO_STATES
        assert "capitulation" in CRYPTO_STATES

    def test_forex_4_states(self):
        assert len(FOREX_STATES) == 4
        assert "carry_trade" in FOREX_STATES
        assert "risk_off_flight" in FOREX_STATES

    def test_indices_5_states(self):
        assert len(INDICES_STATES) == 5
        assert "bull_market" in INDICES_STATES
        assert "panic" in INDICES_STATES

    def test_commodities_4_states(self):
        assert len(COMMODITIES_STATES) == 4
        assert "contango" in COMMODITIES_STATES
        assert "supply_shock" in COMMODITIES_STATES


# ---------------------------------------------------------------------------
# CANONICAL MAPPINGS
# ---------------------------------------------------------------------------

class TestCanonicalMappings:
    def test_crypto_all_states_mapped(self):
        for s in CRYPTO_STATES:
            assert s in _CRYPTO_TO_CANONICAL

    def test_forex_all_states_mapped(self):
        for s in FOREX_STATES:
            assert s in _FOREX_TO_CANONICAL

    def test_indices_all_states_mapped(self):
        for s in INDICES_STATES:
            assert s in _INDICES_TO_CANONICAL

    def test_commodities_all_states_mapped(self):
        for s in COMMODITIES_STATES:
            assert s in _COMMODITIES_TO_CANONICAL

    def test_crypto_capitulation_is_shock(self):
        assert _CRYPTO_TO_CANONICAL["capitulation"] == AssetRegimeState.SHOCK

    def test_crypto_leverage_mania_is_trending_up(self):
        assert _CRYPTO_TO_CANONICAL["leverage_mania"] == AssetRegimeState.TRENDING_UP

    def test_forex_risk_off_flight_is_high_vol(self):
        assert _FOREX_TO_CANONICAL["risk_off_flight"] == AssetRegimeState.HIGH_VOLATILITY

    def test_indices_panic_is_shock(self):
        assert _INDICES_TO_CANONICAL["panic"] == AssetRegimeState.SHOCK

    def test_indices_bull_is_trending_up(self):
        assert _INDICES_TO_CANONICAL["bull_market"] == AssetRegimeState.TRENDING_UP

    def test_commodities_supply_shock_is_shock(self):
        assert _COMMODITIES_TO_CANONICAL["supply_shock"] == AssetRegimeState.SHOCK

    def test_all_mappings_produce_valid_enum(self):
        for mapping in (_CRYPTO_TO_CANONICAL, _FOREX_TO_CANONICAL,
                        _INDICES_TO_CANONICAL, _COMMODITIES_TO_CANONICAL):
            for state in mapping.values():
                assert isinstance(state, AssetRegimeState)


# ---------------------------------------------------------------------------
# HELPERS
# ---------------------------------------------------------------------------

class TestHelpers:
    def test_normalize_probs_sums_to_one(self):
        probs = {"a": 0.3, "b": 0.6, "c": 0.1}
        normalized = _normalize_probs(probs)
        assert abs(sum(normalized.values()) - 1.0) < 1e-10

    def test_normalize_probs_zero_total(self):
        probs = {"a": 0.0, "b": 0.0}
        normalized = _normalize_probs(probs)
        assert abs(sum(normalized.values()) - 1.0) < 1e-10
        assert normalized["a"] == 0.5

    def test_max_state(self):
        probs = {"a": 0.1, "b": 0.6, "c": 0.3}
        assert _max_state(probs) == "b"

    def test_max_state_tie_breaks_alphabetically(self):
        probs = {"b": 0.5, "a": 0.5}
        assert _max_state(probs) == "b"  # both equal, "b" > "a" alphabetically


# ---------------------------------------------------------------------------
# CRYPTO REGIME DETECTOR
# ---------------------------------------------------------------------------

class TestCryptoRegimeDetector:
    def test_leverage_mania(self):
        r = CryptoRegimeDetector().detect(
            funding_rate=0.005, open_interest_change=0.3,
            liquidation_score=0.1, social_sentiment=0.5,
            global_macro=_calm_global(),
        )
        assert r.internal_state == "leverage_mania"
        assert r.canonical_state == AssetRegimeState.TRENDING_UP

    def test_retail_fomo(self):
        r = CryptoRegimeDetector().detect(
            funding_rate=0.0005, open_interest_change=0.1,
            liquidation_score=0.1, social_sentiment=0.9,
            global_macro=_calm_global(),
        )
        assert r.internal_state == "retail_fomo"

    def test_institutional(self):
        r = CryptoRegimeDetector().detect(
            funding_rate=0.0001, open_interest_change=0.01,
            liquidation_score=0.05, social_sentiment=0.5,
            global_macro=_calm_global(),
        )
        assert r.internal_state == "institutional"
        assert r.canonical_state == AssetRegimeState.RANGING_TIGHT

    def test_deleveraging(self):
        r = CryptoRegimeDetector().detect(
            funding_rate=-0.003, open_interest_change=-0.3,
            liquidation_score=0.5, social_sentiment=0.4,
            global_macro=_calm_global(),
        )
        assert r.internal_state == "deleveraging"
        assert r.canonical_state == AssetRegimeState.TRENDING_DOWN

    def test_capitulation(self):
        r = CryptoRegimeDetector().detect(
            funding_rate=-0.005, open_interest_change=-0.5,
            liquidation_score=0.9, social_sentiment=0.1,
            global_macro=_calm_global(),
        )
        assert r.internal_state == "capitulation"
        assert r.canonical_state == AssetRegimeState.SHOCK

    def test_conditioning_risk_off_suppresses_leverage_mania(self):
        """FAS: In risk-off, suppress leverage_mania probability."""
        r_calm = CryptoRegimeDetector().detect(
            funding_rate=0.005, open_interest_change=0.3,
            liquidation_score=0.1, social_sentiment=0.5,
            global_macro=_calm_global(),
        )
        r_off = CryptoRegimeDetector().detect(
            funding_rate=0.005, open_interest_change=0.3,
            liquidation_score=0.1, social_sentiment=0.5,
            global_macro=_risk_off_global(),
        )
        assert r_off.conditioned_on_global is True
        assert r_off.probabilities["leverage_mania"] < r_calm.probabilities["leverage_mania"]

    def test_conditioning_panic_forces_capitulation(self):
        """FAS: In panic, force capitulation if liquidations extreme."""
        r = CryptoRegimeDetector().detect(
            funding_rate=-0.001, open_interest_change=-0.1,
            liquidation_score=0.9, social_sentiment=0.2,
            global_macro=_panic_global(),
        )
        assert r.internal_state == "capitulation"
        assert r.conditioned_on_global is True

    def test_asset_class_is_crypto(self):
        r = CryptoRegimeDetector().detect(
            funding_rate=0.0, open_interest_change=0.0,
            liquidation_score=0.0, social_sentiment=0.5,
            global_macro=_calm_global(),
        )
        assert r.asset_class == "crypto"

    def test_probabilities_sum_to_one(self):
        r = CryptoRegimeDetector().detect(
            funding_rate=0.001, open_interest_change=0.1,
            liquidation_score=0.2, social_sentiment=0.5,
            global_macro=_calm_global(),
        )
        assert abs(sum(r.probabilities.values()) - 1.0) < 1e-10

    def test_confidence_range(self):
        r = CryptoRegimeDetector().detect(
            funding_rate=0.001, open_interest_change=0.1,
            liquidation_score=0.2, social_sentiment=0.5,
            global_macro=_calm_global(),
        )
        assert 0.0 <= r.confidence <= 1.0

    def test_result_frozen(self):
        r = CryptoRegimeDetector().detect(
            funding_rate=0.0, open_interest_change=0.0,
            liquidation_score=0.0, social_sentiment=0.5,
            global_macro=_calm_global(),
        )
        with pytest.raises(AttributeError):
            r.internal_state = "hacked"


# ---------------------------------------------------------------------------
# FOREX REGIME DETECTOR
# ---------------------------------------------------------------------------

class TestForexRegimeDetector:
    def test_carry_trade(self):
        r = ForexRegimeDetector().detect(
            rate_differential=0.03, carry_signal=0.6,
            cb_meeting_proximity_days=30.0, trend_strength=0.2,
            global_macro=_calm_global(),
        )
        assert r.internal_state == "carry_trade"
        assert r.canonical_state == AssetRegimeState.RANGING_TIGHT

    def test_trend_following(self):
        r = ForexRegimeDetector().detect(
            rate_differential=0.01, carry_signal=0.1,
            cb_meeting_proximity_days=30.0, trend_strength=0.8,
            global_macro=_calm_global(),
        )
        assert r.internal_state == "trend_following"
        assert r.canonical_state == AssetRegimeState.TRENDING_UP

    def test_range_bound(self):
        r = ForexRegimeDetector().detect(
            rate_differential=0.005, carry_signal=0.1,
            cb_meeting_proximity_days=30.0, trend_strength=0.1,
            global_macro=_calm_global(),
        )
        assert r.internal_state == "range_bound"

    def test_risk_off_flight_conditioning(self):
        """FAS: In risk-off, force risk_off_flight."""
        r = ForexRegimeDetector().detect(
            rate_differential=0.03, carry_signal=0.6,
            cb_meeting_proximity_days=30.0, trend_strength=0.2,
            global_macro=_risk_off_global(),
        )
        assert r.internal_state == "risk_off_flight"
        assert r.conditioned_on_global is True

    def test_panic_forces_risk_off_flight(self):
        r = ForexRegimeDetector().detect(
            rate_differential=0.03, carry_signal=0.6,
            cb_meeting_proximity_days=30.0, trend_strength=0.2,
            global_macro=_panic_global(),
        )
        assert r.internal_state == "risk_off_flight"

    def test_tightening_boosts_trend(self):
        """FAS: Monetary tightening boosts trend_following."""
        tight_global = GlobalMacroDetector().detect(
            vix_level=12.0, vix_term_structure=0.1, credit_spread_bps=100.0,
            fed_rate=5.0, fed_direction="hiking",
            repo_rate_spread=0.1, ted_spread=0.1,
        )
        r = ForexRegimeDetector().detect(
            rate_differential=0.01, carry_signal=0.1,
            cb_meeting_proximity_days=30.0, trend_strength=0.5,
            global_macro=tight_global,
        )
        assert r.conditioned_on_global is True
        assert r.probabilities["trend_following"] > 0

    def test_cb_proximity_suppresses_carry(self):
        """FAS: CB meeting < 3 days suppresses carry_trade."""
        r_far = ForexRegimeDetector().detect(
            rate_differential=0.03, carry_signal=0.6,
            cb_meeting_proximity_days=30.0, trend_strength=0.2,
            global_macro=_calm_global(),
        )
        r_near = ForexRegimeDetector().detect(
            rate_differential=0.03, carry_signal=0.6,
            cb_meeting_proximity_days=1.0, trend_strength=0.2,
            global_macro=_calm_global(),
        )
        assert r_near.probabilities["carry_trade"] < r_far.probabilities["carry_trade"]
        assert r_near.conditioned_on_global is True

    def test_asset_class_is_forex(self):
        r = ForexRegimeDetector().detect(
            rate_differential=0.0, carry_signal=0.0,
            cb_meeting_proximity_days=30.0, trend_strength=0.0,
            global_macro=_calm_global(),
        )
        assert r.asset_class == "forex"

    def test_probabilities_sum_to_one(self):
        r = ForexRegimeDetector().detect(
            rate_differential=0.01, carry_signal=0.3,
            cb_meeting_proximity_days=10.0, trend_strength=0.4,
            global_macro=_calm_global(),
        )
        assert abs(sum(r.probabilities.values()) - 1.0) < 1e-10


# ---------------------------------------------------------------------------
# INDICES REGIME DETECTOR
# ---------------------------------------------------------------------------

class TestIndicesRegimeDetector:
    def test_bull_market(self):
        r = IndicesRegimeDetector().detect(
            vix_level=12.0, market_breadth=0.8,
            credit_spread_bps=80.0, trend_strength=0.5,
            global_macro=_calm_global(),
        )
        assert r.internal_state == "bull_market"
        assert r.canonical_state == AssetRegimeState.TRENDING_UP

    def test_bear_market(self):
        r = IndicesRegimeDetector().detect(
            vix_level=22.0, market_breadth=0.2,
            credit_spread_bps=250.0, trend_strength=-0.6,
            global_macro=_calm_global(),
        )
        assert r.internal_state == "bear_market"
        assert r.canonical_state == AssetRegimeState.TRENDING_DOWN

    def test_panic(self):
        r = IndicesRegimeDetector().detect(
            vix_level=50.0, market_breadth=0.1,
            credit_spread_bps=500.0, trend_strength=-0.1,
            global_macro=_calm_global(),
        )
        assert r.internal_state == "panic"
        assert r.canonical_state == AssetRegimeState.SHOCK

    def test_defensive(self):
        r = IndicesRegimeDetector().detect(
            vix_level=22.0, market_breadth=0.25,
            credit_spread_bps=200.0, trend_strength=0.0,
            global_macro=_calm_global(),
        )
        assert r.internal_state == "defensive"

    def test_sector_rotation(self):
        r = IndicesRegimeDetector().detect(
            vix_level=16.0, market_breadth=0.45,
            credit_spread_bps=120.0, trend_strength=0.1,
            global_macro=_calm_global(),
        )
        assert r.internal_state == "sector_rotation"
        assert r.canonical_state == AssetRegimeState.RANGING_WIDE

    def test_conditioning_panic_global(self):
        """FAS: Global panic forces indices panic."""
        r = IndicesRegimeDetector().detect(
            vix_level=12.0, market_breadth=0.8,
            credit_spread_bps=80.0, trend_strength=0.5,
            global_macro=_panic_global(),
        )
        assert r.internal_state == "panic"
        assert r.conditioned_on_global is True

    def test_conditioning_risk_off_boosts_defensive(self):
        r_calm = IndicesRegimeDetector().detect(
            vix_level=20.0, market_breadth=0.4,
            credit_spread_bps=150.0, trend_strength=0.1,
            global_macro=_calm_global(),
        )
        r_off = IndicesRegimeDetector().detect(
            vix_level=20.0, market_breadth=0.4,
            credit_spread_bps=150.0, trend_strength=0.1,
            global_macro=_risk_off_global(),
        )
        assert r_off.probabilities["defensive"] > r_calm.probabilities["defensive"]

    def test_asset_class_is_indices(self):
        r = IndicesRegimeDetector().detect(
            vix_level=15.0, market_breadth=0.5,
            credit_spread_bps=100.0, trend_strength=0.0,
            global_macro=_calm_global(),
        )
        assert r.asset_class == "indices"

    def test_probabilities_sum_to_one(self):
        r = IndicesRegimeDetector().detect(
            vix_level=20.0, market_breadth=0.5,
            credit_spread_bps=150.0, trend_strength=0.2,
            global_macro=_calm_global(),
        )
        assert abs(sum(r.probabilities.values()) - 1.0) < 1e-10


# ---------------------------------------------------------------------------
# COMMODITIES REGIME DETECTOR
# ---------------------------------------------------------------------------

class TestCommoditiesRegimeDetector:
    def test_contango(self):
        r = CommoditiesRegimeDetector().detect(
            contango_backwardation=0.05, inventory_change=0.2,
            volatility_score=0.2, global_macro=_calm_global(),
        )
        assert r.internal_state == "contango"
        assert r.canonical_state == AssetRegimeState.RANGING_TIGHT

    def test_backwardation(self):
        r = CommoditiesRegimeDetector().detect(
            contango_backwardation=-0.05, inventory_change=-0.4,
            volatility_score=0.3, global_macro=_calm_global(),
        )
        assert r.internal_state == "backwardation"
        assert r.canonical_state == AssetRegimeState.TRENDING_UP

    def test_supply_shock(self):
        r = CommoditiesRegimeDetector().detect(
            contango_backwardation=0.0, inventory_change=-0.7,
            volatility_score=0.95, global_macro=_calm_global(),
        )
        assert r.internal_state == "supply_shock"
        assert r.canonical_state == AssetRegimeState.SHOCK

    def test_demand_shock(self):
        r = CommoditiesRegimeDetector().detect(
            contango_backwardation=0.01, inventory_change=0.5,
            volatility_score=0.7, global_macro=_calm_global(),
        )
        assert r.internal_state == "demand_shock"
        assert r.canonical_state == AssetRegimeState.HIGH_VOLATILITY

    def test_conditioning_panic(self):
        r = CommoditiesRegimeDetector().detect(
            contango_backwardation=0.01, inventory_change=0.0,
            volatility_score=0.5, global_macro=_panic_global(),
        )
        assert r.conditioned_on_global is True

    def test_asset_class_is_commodities(self):
        r = CommoditiesRegimeDetector().detect(
            contango_backwardation=0.0, inventory_change=0.0,
            volatility_score=0.2, global_macro=_calm_global(),
        )
        assert r.asset_class == "commodities"

    def test_probabilities_sum_to_one(self):
        r = CommoditiesRegimeDetector().detect(
            contango_backwardation=0.03, inventory_change=-0.1,
            volatility_score=0.4, global_macro=_calm_global(),
        )
        assert abs(sum(r.probabilities.values()) - 1.0) < 1e-10


# ---------------------------------------------------------------------------
# ASSET REGIME RESULT
# ---------------------------------------------------------------------------

class TestAssetRegimeResult:
    def test_all_fields(self):
        r = CryptoRegimeDetector().detect(
            funding_rate=0.0, open_interest_change=0.0,
            liquidation_score=0.0, social_sentiment=0.5,
            global_macro=_calm_global(),
        )
        assert isinstance(r.asset_class, str)
        assert isinstance(r.internal_state, str)
        assert isinstance(r.canonical_state, AssetRegimeState)
        assert isinstance(r.probabilities, dict)
        assert isinstance(r.confidence, float)
        assert isinstance(r.conditioned_on_global, bool)

    def test_frozen(self):
        r = CryptoRegimeDetector().detect(
            funding_rate=0.0, open_interest_change=0.0,
            liquidation_score=0.0, social_sentiment=0.5,
            global_macro=_calm_global(),
        )
        with pytest.raises(AttributeError):
            r.canonical_state = AssetRegimeState.UNKNOWN


# ---------------------------------------------------------------------------
# DETERMINISM (DET-05)
# ---------------------------------------------------------------------------

class TestDeterminism:
    def test_crypto_deterministic(self):
        kwargs = dict(
            funding_rate=0.002, open_interest_change=0.1,
            liquidation_score=0.2, social_sentiment=0.6,
            global_macro=_calm_global(),
        )
        r1 = CryptoRegimeDetector().detect(**kwargs)
        r2 = CryptoRegimeDetector().detect(**kwargs)
        assert r1.internal_state == r2.internal_state
        assert r1.canonical_state == r2.canonical_state
        assert r1.probabilities == r2.probabilities

    def test_forex_deterministic(self):
        kwargs = dict(
            rate_differential=0.02, carry_signal=0.4,
            cb_meeting_proximity_days=15.0, trend_strength=0.5,
            global_macro=_calm_global(),
        )
        r1 = ForexRegimeDetector().detect(**kwargs)
        r2 = ForexRegimeDetector().detect(**kwargs)
        assert r1.internal_state == r2.internal_state

    def test_indices_deterministic(self):
        kwargs = dict(
            vix_level=18.0, market_breadth=0.6,
            credit_spread_bps=120.0, trend_strength=0.3,
            global_macro=_calm_global(),
        )
        r1 = IndicesRegimeDetector().detect(**kwargs)
        r2 = IndicesRegimeDetector().detect(**kwargs)
        assert r1.internal_state == r2.internal_state

    def test_commodities_deterministic(self):
        kwargs = dict(
            contango_backwardation=0.03, inventory_change=-0.2,
            volatility_score=0.3, global_macro=_calm_global(),
        )
        r1 = CommoditiesRegimeDetector().detect(**kwargs)
        r2 = CommoditiesRegimeDetector().detect(**kwargs)
        assert r1.internal_state == r2.internal_state


# ---------------------------------------------------------------------------
# CROSS-DETECTOR CONSISTENCY
# ---------------------------------------------------------------------------

class TestCrossDetectorConsistency:
    def test_all_detectors_return_asset_regime_result(self):
        g = _calm_global()
        results = [
            CryptoRegimeDetector().detect(
                funding_rate=0.0, open_interest_change=0.0,
                liquidation_score=0.0, social_sentiment=0.5, global_macro=g,
            ),
            ForexRegimeDetector().detect(
                rate_differential=0.01, carry_signal=0.2,
                cb_meeting_proximity_days=20.0, trend_strength=0.3, global_macro=g,
            ),
            IndicesRegimeDetector().detect(
                vix_level=15.0, market_breadth=0.5,
                credit_spread_bps=100.0, trend_strength=0.2, global_macro=g,
            ),
            CommoditiesRegimeDetector().detect(
                contango_backwardation=0.02, inventory_change=0.0,
                volatility_score=0.2, global_macro=g,
            ),
        ]
        for r in results:
            assert isinstance(r, AssetRegimeResult)
            assert 0.0 <= r.confidence <= 1.0
            assert abs(sum(r.probabilities.values()) - 1.0) < 1e-10
            assert r.internal_state in r.probabilities

    def test_all_internal_states_are_valid(self):
        """Each detector's internal state must be from its state tuple."""
        g = _calm_global()
        crypto_r = CryptoRegimeDetector().detect(
            funding_rate=0.0, open_interest_change=0.0,
            liquidation_score=0.0, social_sentiment=0.5, global_macro=g,
        )
        assert crypto_r.internal_state in CRYPTO_STATES

        forex_r = ForexRegimeDetector().detect(
            rate_differential=0.01, carry_signal=0.2,
            cb_meeting_proximity_days=20.0, trend_strength=0.3, global_macro=g,
        )
        assert forex_r.internal_state in FOREX_STATES

        indices_r = IndicesRegimeDetector().detect(
            vix_level=15.0, market_breadth=0.5,
            credit_spread_bps=100.0, trend_strength=0.2, global_macro=g,
        )
        assert indices_r.internal_state in INDICES_STATES

        commodities_r = CommoditiesRegimeDetector().detect(
            contango_backwardation=0.02, inventory_change=0.0,
            volatility_score=0.2, global_macro=g,
        )
        assert commodities_r.internal_state in COMMODITIES_STATES

    def test_correct_asset_class_labels(self):
        g = _calm_global()
        assert CryptoRegimeDetector().detect(
            funding_rate=0.0, open_interest_change=0.0,
            liquidation_score=0.0, social_sentiment=0.5, global_macro=g,
        ).asset_class == "crypto"
        assert ForexRegimeDetector().detect(
            rate_differential=0.0, carry_signal=0.0,
            cb_meeting_proximity_days=30.0, trend_strength=0.0, global_macro=g,
        ).asset_class == "forex"
        assert IndicesRegimeDetector().detect(
            vix_level=15.0, market_breadth=0.5,
            credit_spread_bps=100.0, trend_strength=0.0, global_macro=g,
        ).asset_class == "indices"
        assert CommoditiesRegimeDetector().detect(
            contango_backwardation=0.0, inventory_change=0.0,
            volatility_score=0.2, global_macro=g,
        ).asset_class == "commodities"


# ---------------------------------------------------------------------------
# PACKAGE IMPORT
# ---------------------------------------------------------------------------

class TestPackageImport:
    def test_import_all(self):
        from jarvis.intelligence.asset_regimes import (
            CryptoRegimeDetector,
            ForexRegimeDetector,
            IndicesRegimeDetector,
            CommoditiesRegimeDetector,
            AssetRegimeResult,
            CRYPTO_STATES,
            FOREX_STATES,
            INDICES_STATES,
            COMMODITIES_STATES,
        )
        assert CryptoRegimeDetector is not None
        assert AssetRegimeResult is not None
