# =============================================================================
# tests/unit/core/test_data_structures.py -- Multi-Asset Data Structures Tests
#
# Comprehensive tests for jarvis/core/data_structures.py (Phase 1).
# Covers: TradingHours, SessionDefinition, SessionStructure, SpreadModel,
#         LiquidityProfile, MarketMicrostructure, normalize_volatility,
#         canonical configs, and MICROSTRUCTURE_REGISTRY.
# =============================================================================

import pytest

from jarvis.core.data_structures import (
    VALID_ASSET_CLASSES,
    VOLATILITY_SCALING,
    TradingHours,
    SessionDefinition,
    SessionStructure,
    SpreadModel,
    LiquidityProfile,
    MarketMicrostructure,
    normalize_volatility,
    get_microstructure,
    CRYPTO_MICROSTRUCTURE,
    FOREX_MICROSTRUCTURE,
    INDICES_MICROSTRUCTURE,
    COMMODITIES_MICROSTRUCTURE,
    RATES_MICROSTRUCTURE,
    FOREX_SESSIONS,
    INDICES_SESSIONS,
    MICROSTRUCTURE_REGISTRY,
)


# ---------------------------------------------------------------------------
# VALID_ASSET_CLASSES
# ---------------------------------------------------------------------------

class TestValidAssetClasses:
    def test_contains_all_five(self):
        expected = {"crypto", "forex", "indices", "commodities", "rates"}
        assert VALID_ASSET_CLASSES == expected

    def test_is_frozenset(self):
        assert isinstance(VALID_ASSET_CLASSES, frozenset)

    def test_immutable(self):
        with pytest.raises(AttributeError):
            VALID_ASSET_CLASSES.add("bonds")


# ---------------------------------------------------------------------------
# VOLATILITY_SCALING
# ---------------------------------------------------------------------------

class TestVolatilityScaling:
    def test_crypto_baseline(self):
        assert VOLATILITY_SCALING["crypto"] == 1.0

    def test_forex_scaling(self):
        assert VOLATILITY_SCALING["forex"] == 0.3

    def test_indices_scaling(self):
        assert VOLATILITY_SCALING["indices"] == 0.6

    def test_commodities_scaling(self):
        assert VOLATILITY_SCALING["commodities"] == 0.8

    def test_rates_scaling(self):
        assert VOLATILITY_SCALING["rates"] == 0.25

    def test_all_positive(self):
        for ac, scale in VOLATILITY_SCALING.items():
            assert scale > 0, f"{ac} scaling must be positive"

    def test_covers_all_asset_classes(self):
        assert set(VOLATILITY_SCALING.keys()) == VALID_ASSET_CLASSES


# ---------------------------------------------------------------------------
# TRADING HOURS
# ---------------------------------------------------------------------------

class TestTradingHours:
    def test_24_7(self):
        th = TradingHours(mode="24/7", has_gaps=False)
        assert th.mode == "24/7"
        assert th.has_gaps is False

    def test_24_5(self):
        th = TradingHours(mode="24/5", has_gaps=False)
        assert th.mode == "24/5"

    def test_session(self):
        th = TradingHours(mode="session", has_gaps=True)
        assert th.mode == "session"
        assert th.has_gaps is True

    def test_invalid_mode_raises(self):
        with pytest.raises(ValueError, match="Invalid trading hours mode"):
            TradingHours(mode="12/5", has_gaps=False)

    def test_frozen(self):
        th = TradingHours(mode="24/7", has_gaps=False)
        with pytest.raises(AttributeError):
            th.mode = "24/5"


# ---------------------------------------------------------------------------
# SESSION DEFINITION
# ---------------------------------------------------------------------------

class TestSessionDefinition:
    def test_valid_session(self):
        sd = SessionDefinition(
            name="asia", start_utc="00:00", end_utc="09:00", liquidity="low"
        )
        assert sd.name == "asia"
        assert sd.start_utc == "00:00"
        assert sd.end_utc == "09:00"
        assert sd.liquidity == "low"

    def test_high_liquidity(self):
        sd = SessionDefinition(
            name="us", start_utc="13:00", end_utc="22:00", liquidity="high"
        )
        assert sd.liquidity == "high"

    def test_normal_liquidity(self):
        sd = SessionDefinition(
            name="overlap", start_utc="08:00", end_utc="13:00", liquidity="normal"
        )
        assert sd.liquidity == "normal"

    def test_invalid_liquidity_raises(self):
        with pytest.raises(ValueError, match="Invalid liquidity level"):
            SessionDefinition(
                name="bad", start_utc="00:00", end_utc="01:00", liquidity="medium"
            )

    def test_invalid_time_format_raises(self):
        with pytest.raises(ValueError, match="Invalid time value"):
            SessionDefinition(
                name="bad", start_utc="25:00", end_utc="09:00", liquidity="low"
            )

    def test_invalid_time_no_colon_raises(self):
        with pytest.raises(ValueError, match="Invalid time format"):
            SessionDefinition(
                name="bad", start_utc="0900", end_utc="1700", liquidity="low"
            )

    def test_invalid_time_non_numeric_raises(self):
        with pytest.raises(ValueError, match="Invalid time format"):
            SessionDefinition(
                name="bad", start_utc="ab:cd", end_utc="09:00", liquidity="low"
            )

    def test_frozen(self):
        sd = SessionDefinition(
            name="asia", start_utc="00:00", end_utc="09:00", liquidity="low"
        )
        with pytest.raises(AttributeError):
            sd.name = "europe"

    def test_midnight_boundary(self):
        sd = SessionDefinition(
            name="night", start_utc="23:59", end_utc="00:00", liquidity="low"
        )
        assert sd.start_utc == "23:59"
        assert sd.end_utc == "00:00"

    def test_invalid_minutes_raises(self):
        with pytest.raises(ValueError, match="Invalid time value"):
            SessionDefinition(
                name="bad", start_utc="12:60", end_utc="13:00", liquidity="low"
            )


# ---------------------------------------------------------------------------
# SESSION STRUCTURE
# ---------------------------------------------------------------------------

class TestSessionStructure:
    def test_empty_sessions(self):
        ss = SessionStructure(sessions=())
        assert ss.sessions == ()
        assert ss.get_session_names() == []

    def test_with_sessions(self):
        s1 = SessionDefinition(name="a", start_utc="00:00", end_utc="08:00", liquidity="low")
        s2 = SessionDefinition(name="b", start_utc="08:00", end_utc="16:00", liquidity="high")
        ss = SessionStructure(sessions=(s1, s2))
        assert len(ss.sessions) == 2
        assert ss.get_session_names() == ["a", "b"]

    def test_invalid_type_raises(self):
        with pytest.raises(TypeError, match="must be a tuple"):
            SessionStructure(sessions=["not", "a", "tuple"])

    def test_invalid_element_raises(self):
        with pytest.raises(TypeError, match="must be a SessionDefinition"):
            SessionStructure(sessions=("not_a_session",))

    def test_frozen(self):
        ss = SessionStructure(sessions=())
        with pytest.raises(AttributeError):
            ss.sessions = ()


# ---------------------------------------------------------------------------
# SPREAD MODEL
# ---------------------------------------------------------------------------

class TestSpreadModel:
    def test_basic_spread(self):
        sm = SpreadModel(typical_spread_bps=10.0, session_multipliers=())
        assert sm.typical_spread_bps == 10.0
        assert sm.get_spread_bps() == 10.0

    def test_session_multiplier(self):
        sm = SpreadModel(
            typical_spread_bps=5.0,
            session_multipliers=(("pre_market", 2.0), ("regular", 1.0)),
        )
        assert sm.get_spread_bps("pre_market") == 10.0
        assert sm.get_spread_bps("regular") == 5.0

    def test_unknown_session_returns_typical(self):
        sm = SpreadModel(
            typical_spread_bps=5.0,
            session_multipliers=(("regular", 1.0),),
        )
        assert sm.get_spread_bps("unknown_session") == 5.0

    def test_empty_session_name_returns_typical(self):
        sm = SpreadModel(typical_spread_bps=3.0, session_multipliers=())
        assert sm.get_spread_bps("") == 3.0

    def test_negative_spread_raises(self):
        with pytest.raises(ValueError, match="must be >= 0"):
            SpreadModel(typical_spread_bps=-1.0, session_multipliers=())

    def test_zero_spread_ok(self):
        sm = SpreadModel(typical_spread_bps=0.0, session_multipliers=())
        assert sm.get_spread_bps() == 0.0

    def test_frozen(self):
        sm = SpreadModel(typical_spread_bps=10.0, session_multipliers=())
        with pytest.raises(AttributeError):
            sm.typical_spread_bps = 20.0


# ---------------------------------------------------------------------------
# LIQUIDITY PROFILE
# ---------------------------------------------------------------------------

class TestLiquidityProfile:
    def test_valid_high(self):
        lp = LiquidityProfile(
            base_liquidity="high", session_dependent=False, quality_minimum=0.6
        )
        assert lp.base_liquidity == "high"
        assert lp.session_dependent is False
        assert lp.quality_minimum == 0.6

    def test_valid_low(self):
        lp = LiquidityProfile(
            base_liquidity="low", session_dependent=True, quality_minimum=0.5
        )
        assert lp.base_liquidity == "low"

    def test_invalid_base_liquidity_raises(self):
        with pytest.raises(ValueError, match="Invalid base_liquidity"):
            LiquidityProfile(
                base_liquidity="medium", session_dependent=False, quality_minimum=0.6
            )

    def test_quality_minimum_below_zero_raises(self):
        with pytest.raises(ValueError, match="quality_minimum must be in"):
            LiquidityProfile(
                base_liquidity="high", session_dependent=False, quality_minimum=-0.1
            )

    def test_quality_minimum_above_one_raises(self):
        with pytest.raises(ValueError, match="quality_minimum must be in"):
            LiquidityProfile(
                base_liquidity="high", session_dependent=False, quality_minimum=1.1
            )

    def test_quality_minimum_boundary_zero(self):
        lp = LiquidityProfile(
            base_liquidity="high", session_dependent=False, quality_minimum=0.0
        )
        assert lp.quality_minimum == 0.0

    def test_quality_minimum_boundary_one(self):
        lp = LiquidityProfile(
            base_liquidity="high", session_dependent=False, quality_minimum=1.0
        )
        assert lp.quality_minimum == 1.0

    def test_frozen(self):
        lp = LiquidityProfile(
            base_liquidity="high", session_dependent=False, quality_minimum=0.6
        )
        with pytest.raises(AttributeError):
            lp.base_liquidity = "low"


# ---------------------------------------------------------------------------
# MARKET MICROSTRUCTURE
# ---------------------------------------------------------------------------

class TestMarketMicrostructure:
    def _make_minimal(self, **overrides):
        defaults = dict(
            asset_class="crypto",
            trading_hours=TradingHours(mode="24/7", has_gaps=False),
            gap_detection=False,
            typical_spread_bps=10.0,
            volatility_scaling=1.0,
            ood_threshold=0.7,
            margin_requirement=0.05,
            session_structure=SessionStructure(sessions=()),
            spread_model=SpreadModel(typical_spread_bps=10.0, session_multipliers=()),
            liquidity_profile=LiquidityProfile(
                base_liquidity="normal", session_dependent=False, quality_minimum=0.6
            ),
            specific_features=("funding_rate",),
        )
        defaults.update(overrides)
        return MarketMicrostructure(**defaults)

    def test_valid_crypto(self):
        mm = self._make_minimal()
        assert mm.asset_class == "crypto"
        assert mm.volatility_scaling == 1.0

    def test_invalid_asset_class_raises(self):
        with pytest.raises(ValueError, match="Invalid asset_class"):
            self._make_minimal(asset_class="bonds")

    def test_zero_volatility_scaling_raises(self):
        with pytest.raises(ValueError, match="volatility_scaling must be > 0"):
            self._make_minimal(volatility_scaling=0.0)

    def test_negative_volatility_scaling_raises(self):
        with pytest.raises(ValueError, match="volatility_scaling must be > 0"):
            self._make_minimal(volatility_scaling=-1.0)

    def test_ood_threshold_out_of_range_raises(self):
        with pytest.raises(ValueError, match="ood_threshold must be in"):
            self._make_minimal(ood_threshold=1.5)

    def test_ood_threshold_negative_raises(self):
        with pytest.raises(ValueError, match="ood_threshold must be in"):
            self._make_minimal(ood_threshold=-0.1)

    def test_margin_requirement_zero_raises(self):
        with pytest.raises(ValueError, match="margin_requirement must be > 0"):
            self._make_minimal(margin_requirement=0.0)

    def test_negative_spread_raises(self):
        with pytest.raises(ValueError, match="typical_spread_bps must be >= 0"):
            self._make_minimal(typical_spread_bps=-1.0)

    def test_frozen(self):
        mm = self._make_minimal()
        with pytest.raises(AttributeError):
            mm.asset_class = "forex"

    def test_specific_features_tuple(self):
        mm = self._make_minimal(specific_features=("a", "b", "c"))
        assert mm.specific_features == ("a", "b", "c")

    def test_all_valid_asset_classes(self):
        for ac in VALID_ASSET_CLASSES:
            mm = self._make_minimal(asset_class=ac)
            assert mm.asset_class == ac

    def test_ood_threshold_boundary_zero(self):
        mm = self._make_minimal(ood_threshold=0.0)
        assert mm.ood_threshold == 0.0

    def test_ood_threshold_boundary_one(self):
        mm = self._make_minimal(ood_threshold=1.0)
        assert mm.ood_threshold == 1.0


# ---------------------------------------------------------------------------
# NORMALIZE VOLATILITY
# ---------------------------------------------------------------------------

class TestNormalizeVolatility:
    def test_crypto_no_change(self):
        assert normalize_volatility(0.05, "crypto") == 0.05

    def test_forex_scales_up(self):
        result = normalize_volatility(0.05, "forex")
        assert abs(result - 0.05 / 0.3) < 1e-10

    def test_indices_scales_up(self):
        result = normalize_volatility(0.05, "indices")
        assert abs(result - 0.05 / 0.6) < 1e-10

    def test_commodities_scales_up(self):
        result = normalize_volatility(0.05, "commodities")
        assert abs(result - 0.05 / 0.8) < 1e-10

    def test_rates_scales_up(self):
        result = normalize_volatility(0.05, "rates")
        assert abs(result - 0.05 / 0.25) < 1e-10

    def test_unknown_asset_raises(self):
        with pytest.raises(ValueError, match="Unknown asset_class"):
            normalize_volatility(0.05, "bonds")

    def test_zero_vol(self):
        assert normalize_volatility(0.0, "crypto") == 0.0

    def test_negative_vol(self):
        result = normalize_volatility(-0.05, "crypto")
        assert result == -0.05

    def test_deterministic(self):
        """DET-05: Same inputs -> same outputs."""
        r1 = normalize_volatility(0.03, "forex")
        r2 = normalize_volatility(0.03, "forex")
        assert r1 == r2

    def test_cross_asset_comparison(self):
        """FAS: 5% crypto vol = normal, 5% FX vol = crisis."""
        crypto_norm = normalize_volatility(0.05, "crypto")
        fx_norm = normalize_volatility(0.05, "forex")
        assert fx_norm > crypto_norm  # FX 5% is more extreme


# ---------------------------------------------------------------------------
# CANONICAL CONFIGS
# ---------------------------------------------------------------------------

class TestCryptoMicrostructure:
    def test_asset_class(self):
        assert CRYPTO_MICROSTRUCTURE.asset_class == "crypto"

    def test_trading_hours_24_7(self):
        assert CRYPTO_MICROSTRUCTURE.trading_hours.mode == "24/7"
        assert CRYPTO_MICROSTRUCTURE.trading_hours.has_gaps is False

    def test_no_gap_detection(self):
        assert CRYPTO_MICROSTRUCTURE.gap_detection is False

    def test_spread_bps(self):
        assert CRYPTO_MICROSTRUCTURE.typical_spread_bps == 10.0

    def test_volatility_scaling(self):
        assert CRYPTO_MICROSTRUCTURE.volatility_scaling == 1.0

    def test_ood_threshold(self):
        assert CRYPTO_MICROSTRUCTURE.ood_threshold == 0.7

    def test_margin_requirement(self):
        assert CRYPTO_MICROSTRUCTURE.margin_requirement == 0.05

    def test_no_sessions(self):
        assert len(CRYPTO_MICROSTRUCTURE.session_structure.sessions) == 0

    def test_specific_features(self):
        expected = ("funding_rate", "open_interest", "liquidations", "orderbook_imbalance")
        assert CRYPTO_MICROSTRUCTURE.specific_features == expected


class TestForexMicrostructure:
    def test_asset_class(self):
        assert FOREX_MICROSTRUCTURE.asset_class == "forex"

    def test_trading_hours_24_5(self):
        assert FOREX_MICROSTRUCTURE.trading_hours.mode == "24/5"

    def test_no_gap_detection(self):
        assert FOREX_MICROSTRUCTURE.gap_detection is False

    def test_spread_bps(self):
        assert FOREX_MICROSTRUCTURE.typical_spread_bps == 1.0

    def test_volatility_scaling(self):
        assert FOREX_MICROSTRUCTURE.volatility_scaling == 0.3

    def test_ood_threshold(self):
        assert FOREX_MICROSTRUCTURE.ood_threshold == 0.5

    def test_margin_requirement(self):
        assert FOREX_MICROSTRUCTURE.margin_requirement == 0.01

    def test_three_sessions(self):
        names = FOREX_SESSIONS.get_session_names()
        assert names == ["asia", "europe", "us"]

    def test_asia_session_low_liquidity(self):
        asia = FOREX_SESSIONS.sessions[0]
        assert asia.name == "asia"
        assert asia.liquidity == "low"
        assert asia.start_utc == "00:00"
        assert asia.end_utc == "09:00"

    def test_europe_session_high_liquidity(self):
        europe = FOREX_SESSIONS.sessions[1]
        assert europe.name == "europe"
        assert europe.liquidity == "high"

    def test_us_session_high_liquidity(self):
        us = FOREX_SESSIONS.sessions[2]
        assert us.name == "us"
        assert us.liquidity == "high"

    def test_spread_multiplier_asia(self):
        sm = FOREX_MICROSTRUCTURE.spread_model
        assert sm.get_spread_bps("asia") == 1.5  # 1.0 * 1.5

    def test_spread_multiplier_europe(self):
        sm = FOREX_MICROSTRUCTURE.spread_model
        assert sm.get_spread_bps("europe") == 1.0

    def test_specific_features(self):
        expected = ("rate_differential", "dxy_correlation", "carry_signal", "cb_meeting_proximity")
        assert FOREX_MICROSTRUCTURE.specific_features == expected


class TestIndicesMicrostructure:
    def test_asset_class(self):
        assert INDICES_MICROSTRUCTURE.asset_class == "indices"

    def test_trading_hours_session(self):
        assert INDICES_MICROSTRUCTURE.trading_hours.mode == "session"
        assert INDICES_MICROSTRUCTURE.trading_hours.has_gaps is True

    def test_gap_detection_enabled(self):
        assert INDICES_MICROSTRUCTURE.gap_detection is True

    def test_spread_bps(self):
        assert INDICES_MICROSTRUCTURE.typical_spread_bps == 5.0

    def test_volatility_scaling(self):
        assert INDICES_MICROSTRUCTURE.volatility_scaling == 0.6

    def test_three_sessions(self):
        names = INDICES_SESSIONS.get_session_names()
        assert names == ["pre_market", "regular", "post_market"]

    def test_pre_market_wide_spreads(self):
        sm = INDICES_MICROSTRUCTURE.spread_model
        assert sm.get_spread_bps("pre_market") == 10.0  # 5.0 * 2.0

    def test_regular_normal_spreads(self):
        sm = INDICES_MICROSTRUCTURE.spread_model
        assert sm.get_spread_bps("regular") == 5.0

    def test_post_market_wider_spreads(self):
        sm = INDICES_MICROSTRUCTURE.spread_model
        assert sm.get_spread_bps("post_market") == 9.0  # 5.0 * 1.8

    def test_specific_features(self):
        expected = ("vix_level", "vix_term_structure", "put_call_ratio",
                     "credit_spread", "sector_rotation")
        assert INDICES_MICROSTRUCTURE.specific_features == expected


class TestCommoditiesMicrostructure:
    def test_asset_class(self):
        assert COMMODITIES_MICROSTRUCTURE.asset_class == "commodities"

    def test_trading_hours_session(self):
        assert COMMODITIES_MICROSTRUCTURE.trading_hours.mode == "session"
        assert COMMODITIES_MICROSTRUCTURE.trading_hours.has_gaps is True

    def test_gap_detection_enabled(self):
        assert COMMODITIES_MICROSTRUCTURE.gap_detection is True

    def test_spread_bps(self):
        assert COMMODITIES_MICROSTRUCTURE.typical_spread_bps == 8.0

    def test_volatility_scaling(self):
        assert COMMODITIES_MICROSTRUCTURE.volatility_scaling == 0.8

    def test_one_session(self):
        names = COMMODITIES_MICROSTRUCTURE.session_structure.get_session_names()
        assert names == ["regular"]

    def test_specific_features(self):
        expected = ("contango_backwardation", "inventory_levels", "seasonal_pattern")
        assert COMMODITIES_MICROSTRUCTURE.specific_features == expected


class TestRatesMicrostructure:
    def test_asset_class(self):
        assert RATES_MICROSTRUCTURE.asset_class == "rates"

    def test_trading_hours_session(self):
        assert RATES_MICROSTRUCTURE.trading_hours.mode == "session"

    def test_gap_detection_enabled(self):
        assert RATES_MICROSTRUCTURE.gap_detection is True

    def test_spread_bps(self):
        assert RATES_MICROSTRUCTURE.typical_spread_bps == 0.5

    def test_volatility_scaling(self):
        assert RATES_MICROSTRUCTURE.volatility_scaling == 0.25

    def test_specific_features(self):
        expected = ("yield_curve_slope", "term_premium", "central_bank_rate")
        assert RATES_MICROSTRUCTURE.specific_features == expected


# ---------------------------------------------------------------------------
# MICROSTRUCTURE REGISTRY
# ---------------------------------------------------------------------------

class TestMicrostructureRegistry:
    def test_all_asset_classes_present(self):
        assert set(MICROSTRUCTURE_REGISTRY.keys()) == VALID_ASSET_CLASSES

    def test_get_crypto(self):
        mm = get_microstructure("crypto")
        assert mm is CRYPTO_MICROSTRUCTURE

    def test_get_forex(self):
        mm = get_microstructure("forex")
        assert mm is FOREX_MICROSTRUCTURE

    def test_get_indices(self):
        mm = get_microstructure("indices")
        assert mm is INDICES_MICROSTRUCTURE

    def test_get_commodities(self):
        mm = get_microstructure("commodities")
        assert mm is COMMODITIES_MICROSTRUCTURE

    def test_get_rates(self):
        mm = get_microstructure("rates")
        assert mm is RATES_MICROSTRUCTURE

    def test_get_unknown_raises(self):
        with pytest.raises(ValueError, match="Unknown asset_class"):
            get_microstructure("bonds")

    def test_get_empty_raises(self):
        with pytest.raises(ValueError, match="Unknown asset_class"):
            get_microstructure("")

    def test_registry_values_match_constants(self):
        assert MICROSTRUCTURE_REGISTRY["crypto"] is CRYPTO_MICROSTRUCTURE
        assert MICROSTRUCTURE_REGISTRY["forex"] is FOREX_MICROSTRUCTURE
        assert MICROSTRUCTURE_REGISTRY["indices"] is INDICES_MICROSTRUCTURE
        assert MICROSTRUCTURE_REGISTRY["commodities"] is COMMODITIES_MICROSTRUCTURE
        assert MICROSTRUCTURE_REGISTRY["rates"] is RATES_MICROSTRUCTURE


# ---------------------------------------------------------------------------
# CROSS-ASSET CONSISTENCY
# ---------------------------------------------------------------------------

class TestCrossAssetConsistency:
    def test_gap_detection_matches_trading_hours(self):
        """Session-based markets should have gap detection enabled."""
        for ac, mm in MICROSTRUCTURE_REGISTRY.items():
            if mm.trading_hours.mode == "session":
                assert mm.gap_detection is True, (
                    f"{ac}: session-based market must have gap_detection=True"
                )
            if mm.trading_hours.mode == "24/7":
                assert mm.gap_detection is False, (
                    f"{ac}: 24/7 market must have gap_detection=False"
                )

    def test_session_structure_nonempty_for_session_markets(self):
        """Markets with sessions defined should have non-empty session structure."""
        for ac, mm in MICROSTRUCTURE_REGISTRY.items():
            if mm.trading_hours.mode == "session":
                assert len(mm.session_structure.sessions) > 0, (
                    f"{ac}: session-based market must have sessions defined"
                )

    def test_24_7_markets_have_no_sessions(self):
        for ac, mm in MICROSTRUCTURE_REGISTRY.items():
            if mm.trading_hours.mode == "24/7":
                assert len(mm.session_structure.sessions) == 0, (
                    f"{ac}: 24/7 market must have no sessions"
                )

    def test_all_volatility_scalings_match_constant(self):
        """Canonical configs must match VOLATILITY_SCALING dict."""
        for ac, mm in MICROSTRUCTURE_REGISTRY.items():
            assert mm.volatility_scaling == VOLATILITY_SCALING[ac], (
                f"{ac}: volatility_scaling mismatch"
            )

    def test_each_asset_has_unique_features(self):
        """No two asset classes should share specific features."""
        all_features = []
        for mm in MICROSTRUCTURE_REGISTRY.values():
            all_features.extend(mm.specific_features)
        assert len(all_features) == len(set(all_features)), (
            "Specific features must be unique across asset classes"
        )

    def test_all_spread_models_consistent(self):
        """Spread model typical_spread_bps matches microstructure."""
        for ac, mm in MICROSTRUCTURE_REGISTRY.items():
            assert mm.spread_model.typical_spread_bps == mm.typical_spread_bps, (
                f"{ac}: spread model bps mismatch"
            )


# ---------------------------------------------------------------------------
# DETERMINISM (DET-05)
# ---------------------------------------------------------------------------

class TestDeterminism:
    def test_get_microstructure_same_result(self):
        r1 = get_microstructure("crypto")
        r2 = get_microstructure("crypto")
        assert r1 is r2

    def test_normalize_vol_deterministic(self):
        r1 = normalize_volatility(0.05, "forex")
        r2 = normalize_volatility(0.05, "forex")
        assert r1 == r2

    def test_spread_model_deterministic(self):
        sm = FOREX_MICROSTRUCTURE.spread_model
        r1 = sm.get_spread_bps("asia")
        r2 = sm.get_spread_bps("asia")
        assert r1 == r2


# ---------------------------------------------------------------------------
# IMMUTABILITY (DET-06, PROHIBITED-05)
# ---------------------------------------------------------------------------

class TestImmutability:
    def test_crypto_frozen(self):
        with pytest.raises(AttributeError):
            CRYPTO_MICROSTRUCTURE.asset_class = "forex"

    def test_forex_frozen(self):
        with pytest.raises(AttributeError):
            FOREX_MICROSTRUCTURE.volatility_scaling = 0.5

    def test_indices_frozen(self):
        with pytest.raises(AttributeError):
            INDICES_MICROSTRUCTURE.gap_detection = False

    def test_commodities_frozen(self):
        with pytest.raises(AttributeError):
            COMMODITIES_MICROSTRUCTURE.ood_threshold = 0.9

    def test_rates_frozen(self):
        with pytest.raises(AttributeError):
            RATES_MICROSTRUCTURE.margin_requirement = 0.1


# ---------------------------------------------------------------------------
# PACKAGE IMPORT
# ---------------------------------------------------------------------------

class TestPackageImport:
    def test_import_from_core(self):
        from jarvis.core.data_structures import (
            MarketMicrostructure,
            TradingHours,
            SessionDefinition,
            SessionStructure,
            SpreadModel,
            LiquidityProfile,
            normalize_volatility,
            get_microstructure,
            VOLATILITY_SCALING,
            MICROSTRUCTURE_REGISTRY,
        )
        assert MarketMicrostructure is not None
        assert TradingHours is not None
        assert normalize_volatility is not None
        assert get_microstructure is not None
