# =============================================================================
# tests/unit/core/test_feature_registry.py -- Feature Registry Tests (Phase MA-2)
#
# Comprehensive tests for jarvis/core/feature_registry.py.
# Covers: index ranges, feature classification, masks, FeatureEncoder,
#         FeatureRegistry, metadata, catalogs, determinism, immutability.
# =============================================================================

import math
import pytest

from jarvis.core.feature_layer import FEATURE_NAMES, FEATURE_VECTOR_SIZE
from jarvis.core.data_structures import VALID_ASSET_CLASSES
from jarvis.core.feature_registry import (
    # Index ranges
    UNIVERSAL_START,
    UNIVERSAL_END,
    ASSET_SPECIFIC_START,
    ASSET_SPECIFIC_END,
    CROSS_ASSET_START,
    CROSS_ASSET_END,
    UNIVERSAL_COUNT,
    ASSET_SPECIFIC_COUNT,
    CROSS_ASSET_COUNT,
    # Feature lists
    UNIVERSAL_FEATURES,
    CROSS_ASSET_FEATURES,
    ALL_ASSET_SPECIFIC_NAMES,
    # Asset catalogs
    CRYPTO_SPECIFIC_FEATURES,
    FOREX_SPECIFIC_FEATURES,
    INDICES_SPECIFIC_FEATURES,
    COMMODITIES_SPECIFIC_FEATURES,
    RATES_SPECIFIC_FEATURES,
    ASSET_SPECIFIC_CATALOG,
    # Cross-asset availability
    CRYPTO_ONLY_CROSS_ASSET,
    CROSS_ASSET_ACTIVE,
    # Mask functions
    generate_feature_mask,
    get_feature_mask,
    FEATURE_MASKS,
    # Metadata
    FeatureMetadata,
    build_feature_catalog,
    FEATURE_CATALOG,
    # Encoder
    FeatureEncoder,
    # Registry
    FeatureRegistry,
    # Internal
    _FEATURE_INDEX,
)


# ---------------------------------------------------------------------------
# INDEX RANGES (DET-06)
# ---------------------------------------------------------------------------

class TestIndexRanges:
    def test_universal_range(self):
        assert UNIVERSAL_START == 0
        assert UNIVERSAL_END == 40

    def test_asset_specific_range(self):
        assert ASSET_SPECIFIC_START == 40
        assert ASSET_SPECIFIC_END == 70

    def test_cross_asset_range(self):
        assert CROSS_ASSET_START == 70
        assert CROSS_ASSET_END == 99

    def test_counts(self):
        assert UNIVERSAL_COUNT == 40
        assert ASSET_SPECIFIC_COUNT == 30
        assert CROSS_ASSET_COUNT == 29

    def test_total_equals_99(self):
        assert UNIVERSAL_COUNT + ASSET_SPECIFIC_COUNT + CROSS_ASSET_COUNT == 99

    def test_contiguous_ranges(self):
        assert UNIVERSAL_END == ASSET_SPECIFIC_START
        assert ASSET_SPECIFIC_END == CROSS_ASSET_START
        assert CROSS_ASSET_END == FEATURE_VECTOR_SIZE


# ---------------------------------------------------------------------------
# FEATURE CLASSIFICATION
# ---------------------------------------------------------------------------

class TestFeatureClassification:
    def test_universal_features_count(self):
        assert len(UNIVERSAL_FEATURES) == 40

    def test_cross_asset_features_count(self):
        assert len(CROSS_ASSET_FEATURES) == 29

    def test_asset_specific_names_count(self):
        assert len(ALL_ASSET_SPECIFIC_NAMES) == 30

    def test_universal_starts_with_returns_1m(self):
        assert UNIVERSAL_FEATURES[0] == "returns_1m"

    def test_universal_matches_feature_names(self):
        for i, name in enumerate(UNIVERSAL_FEATURES):
            assert name == FEATURE_NAMES[i]

    def test_cross_asset_matches_feature_names(self):
        for i, name in enumerate(CROSS_ASSET_FEATURES):
            assert name == FEATURE_NAMES[CROSS_ASSET_START + i]

    def test_asset_specific_matches_feature_names(self):
        for i, name in enumerate(ALL_ASSET_SPECIFIC_NAMES):
            assert name == FEATURE_NAMES[ASSET_SPECIFIC_START + i]

    def test_no_overlap_between_groups(self):
        u = set(UNIVERSAL_FEATURES)
        a = set(ALL_ASSET_SPECIFIC_NAMES)
        c = set(CROSS_ASSET_FEATURES)
        assert len(u & a) == 0
        assert len(u & c) == 0
        assert len(a & c) == 0

    def test_all_features_covered(self):
        all_features = set(UNIVERSAL_FEATURES) | set(ALL_ASSET_SPECIFIC_NAMES) | set(CROSS_ASSET_FEATURES)
        assert all_features == set(FEATURE_NAMES)


# ---------------------------------------------------------------------------
# ASSET-SPECIFIC CATALOGS
# ---------------------------------------------------------------------------

class TestAssetSpecificCatalogs:
    def test_catalog_covers_all_asset_classes(self):
        assert set(ASSET_SPECIFIC_CATALOG.keys()) == VALID_ASSET_CLASSES

    def test_crypto_has_on_chain_features(self):
        assert "exchange_net_flow" in CRYPTO_SPECIFIC_FEATURES
        assert "whale_transaction_count" in CRYPTO_SPECIFIC_FEATURES
        assert "mvrv_ratio" in CRYPTO_SPECIFIC_FEATURES

    def test_forex_has_no_on_chain(self):
        for feat in ("exchange_net_flow", "whale_transaction_count", "mvrv_ratio"):
            assert feat not in FOREX_SPECIFIC_FEATURES

    def test_indices_has_no_on_chain(self):
        for feat in ("exchange_net_flow", "whale_transaction_count"):
            assert feat not in INDICES_SPECIFIC_FEATURES

    def test_all_catalogs_have_technical_tail(self):
        for ac, catalog in ASSET_SPECIFIC_CATALOG.items():
            assert "williams_r" in catalog, f"{ac} missing williams_r"
            assert "mfi_14" in catalog, f"{ac} missing mfi_14"

    def test_all_catalogs_have_microstructure(self):
        for ac, catalog in ASSET_SPECIFIC_CATALOG.items():
            assert "tick_direction" in catalog, f"{ac} missing tick_direction"
            assert "kyle_lambda" in catalog, f"{ac} missing kyle_lambda"

    def test_crypto_has_most_features(self):
        """Crypto (original design) should have the most asset-specific features."""
        for ac in ("forex", "indices", "commodities", "rates"):
            assert len(CRYPTO_SPECIFIC_FEATURES) >= len(ASSET_SPECIFIC_CATALOG[ac])

    def test_catalog_features_are_in_feature_names(self):
        """All catalog features must be canonical FEATURE_NAMES."""
        all_names = set(FEATURE_NAMES)
        for ac, catalog in ASSET_SPECIFIC_CATALOG.items():
            for feat in catalog:
                assert feat in all_names, f"{ac}: '{feat}' not in FEATURE_NAMES"

    def test_catalog_features_in_asset_specific_range(self):
        """Catalog features must be in indices 40-69."""
        for ac, catalog in ASSET_SPECIFIC_CATALOG.items():
            for feat in catalog:
                idx = _FEATURE_INDEX[feat]
                assert ASSET_SPECIFIC_START <= idx < ASSET_SPECIFIC_END, (
                    f"{ac}: '{feat}' at index {idx} not in asset-specific range"
                )


# ---------------------------------------------------------------------------
# CROSS-ASSET AVAILABILITY
# ---------------------------------------------------------------------------

class TestCrossAssetAvailability:
    def test_crypto_only_features_exist(self):
        for feat in CRYPTO_ONLY_CROSS_ASSET:
            assert feat in FEATURE_NAMES

    def test_crypto_has_all_cross_asset(self):
        assert CROSS_ASSET_ACTIVE["crypto"] == frozenset(CROSS_ASSET_FEATURES)

    def test_non_crypto_excludes_crypto_only(self):
        for ac in ("forex", "indices", "commodities", "rates"):
            active = CROSS_ASSET_ACTIVE[ac]
            for feat in CRYPTO_ONLY_CROSS_ASSET:
                assert feat not in active, f"{ac} should not have {feat}"

    def test_non_crypto_has_regime_features(self):
        for ac in ("forex", "indices", "commodities", "rates"):
            active = CROSS_ASSET_ACTIVE[ac]
            assert "regime_hmm" in active
            assert "stress_level" in active

    def test_all_asset_classes_covered(self):
        assert set(CROSS_ASSET_ACTIVE.keys()) == VALID_ASSET_CLASSES


# ---------------------------------------------------------------------------
# FEATURE MASK GENERATION
# ---------------------------------------------------------------------------

class TestFeatureMaskGeneration:
    def test_mask_length(self):
        for ac in VALID_ASSET_CLASSES:
            mask = generate_feature_mask(ac)
            assert len(mask) == 99

    def test_mask_values_binary(self):
        for ac in VALID_ASSET_CLASSES:
            mask = generate_feature_mask(ac)
            for v in mask:
                assert v in (0.0, 1.0)

    def test_universal_always_active(self):
        """Universal features (0-39) must be 1.0 for all asset classes."""
        for ac in VALID_ASSET_CLASSES:
            mask = generate_feature_mask(ac)
            for i in range(UNIVERSAL_START, UNIVERSAL_END):
                assert mask[i] == 1.0, f"{ac}: universal feature {i} not active"

    def test_crypto_has_on_chain_active(self):
        mask = generate_feature_mask("crypto")
        idx = _FEATURE_INDEX["exchange_net_flow"]
        assert mask[idx] == 1.0

    def test_forex_has_on_chain_inactive(self):
        mask = generate_feature_mask("forex")
        idx = _FEATURE_INDEX["exchange_net_flow"]
        assert mask[idx] == 0.0

    def test_crypto_has_hash_rate_active(self):
        mask = generate_feature_mask("crypto")
        idx = _FEATURE_INDEX["hash_rate"]
        assert mask[idx] == 1.0

    def test_forex_has_hash_rate_inactive(self):
        mask = generate_feature_mask("forex")
        idx = _FEATURE_INDEX["hash_rate"]
        assert mask[idx] == 0.0

    def test_unknown_asset_raises(self):
        with pytest.raises(ValueError, match="Unknown asset_class"):
            generate_feature_mask("bonds")

    def test_crypto_most_active(self):
        """Crypto should have the most active features."""
        crypto_count = sum(1 for v in generate_feature_mask("crypto") if v == 1.0)
        for ac in ("forex", "indices", "commodities", "rates"):
            ac_count = sum(1 for v in generate_feature_mask(ac) if v == 1.0)
            assert crypto_count >= ac_count


# ---------------------------------------------------------------------------
# PRE-COMPUTED MASKS
# ---------------------------------------------------------------------------

class TestPreComputedMasks:
    def test_all_asset_classes_present(self):
        assert set(FEATURE_MASKS.keys()) == VALID_ASSET_CLASSES

    def test_masks_are_tuples(self):
        for ac, mask in FEATURE_MASKS.items():
            assert isinstance(mask, tuple), f"{ac} mask is not a tuple"

    def test_masks_length(self):
        for ac, mask in FEATURE_MASKS.items():
            assert len(mask) == 99

    def test_get_feature_mask_returns_precomputed(self):
        for ac in VALID_ASSET_CLASSES:
            assert get_feature_mask(ac) is FEATURE_MASKS[ac]

    def test_get_feature_mask_unknown_raises(self):
        with pytest.raises(ValueError, match="Unknown asset_class"):
            get_feature_mask("bonds")

    def test_masks_match_generated(self):
        for ac in VALID_ASSET_CLASSES:
            generated = tuple(generate_feature_mask(ac))
            assert FEATURE_MASKS[ac] == generated


# ---------------------------------------------------------------------------
# FEATURE INDEX
# ---------------------------------------------------------------------------

class TestFeatureIndex:
    def test_all_features_indexed(self):
        assert len(_FEATURE_INDEX) == 99

    def test_index_correct(self):
        for name, idx in _FEATURE_INDEX.items():
            assert FEATURE_NAMES[idx] == name

    def test_returns_1m_at_zero(self):
        assert _FEATURE_INDEX["returns_1m"] == 0

    def test_prediction_confidence_at_98(self):
        assert _FEATURE_INDEX["prediction_confidence_lagged"] == 98


# ---------------------------------------------------------------------------
# FEATURE METADATA
# ---------------------------------------------------------------------------

class TestFeatureMetadata:
    def test_catalog_length(self):
        assert len(FEATURE_CATALOG) == 99

    def test_catalog_order_matches_feature_names(self):
        for i, fm in enumerate(FEATURE_CATALOG):
            assert fm.index == i
            assert fm.name == FEATURE_NAMES[i]

    def test_universal_category(self):
        for i in range(UNIVERSAL_START, UNIVERSAL_END):
            assert FEATURE_CATALOG[i].category == "universal"

    def test_asset_specific_category(self):
        for i in range(ASSET_SPECIFIC_START, ASSET_SPECIFIC_END):
            assert FEATURE_CATALOG[i].category == "asset_specific"

    def test_cross_asset_category(self):
        for i in range(CROSS_ASSET_START, CROSS_ASSET_END):
            assert FEATURE_CATALOG[i].category == "cross_asset"

    def test_price_action_group(self):
        for i in range(0, 15):
            assert FEATURE_CATALOG[i].group == "price_action"

    def test_technical_group(self):
        for i in range(27, 45):
            assert FEATURE_CATALOG[i].group == "technical"

    def test_on_chain_group(self):
        for i in range(63, 75):
            assert FEATURE_CATALOG[i].group == "on_chain"

    def test_metadata_frozen(self):
        fm = FEATURE_CATALOG[0]
        with pytest.raises(AttributeError):
            fm.name = "changed"

    def test_build_catalog_deterministic(self):
        c1 = build_feature_catalog()
        c2 = build_feature_catalog()
        assert c1 == c2


# ---------------------------------------------------------------------------
# FEATURE ENCODER
# ---------------------------------------------------------------------------

class TestFeatureEncoder:
    def _make_full_features(self, val=1.0):
        return {name: val for name in FEATURE_NAMES}

    def test_encode_length(self):
        enc = FeatureEncoder()
        features = self._make_full_features()
        result = enc.encode(features, "crypto")
        assert len(result) == 99

    def test_encode_all_ones_crypto(self):
        enc = FeatureEncoder()
        features = self._make_full_features(1.0)
        result = enc.encode(features, "crypto")
        mask = get_feature_mask("crypto")
        for i in range(99):
            if mask[i] == 1.0:
                assert result[i] == 1.0, f"index {i} should be 1.0"
            else:
                assert result[i] == 0.0, f"index {i} should be 0.0 (masked)"

    def test_encode_masks_inactive_features(self):
        enc = FeatureEncoder()
        features = self._make_full_features(5.0)
        result = enc.encode(features, "forex")
        # On-chain features should be masked
        idx = _FEATURE_INDEX["exchange_net_flow"]
        assert result[idx] == 0.0

    def test_encode_missing_features_default_zero(self):
        enc = FeatureEncoder()
        result = enc.encode({}, "crypto")
        assert all(v == 0.0 for v in result)

    def test_encode_partial_features(self):
        enc = FeatureEncoder()
        features = {"returns_1m": 0.05, "rsi_14": 55.0}
        result = enc.encode(features, "crypto")
        assert result[0] == 0.05  # returns_1m
        assert result[_FEATURE_INDEX["rsi_14"]] == 55.0

    def test_encode_sanitizes_nan(self):
        enc = FeatureEncoder()
        features = {"returns_1m": float("nan")}
        result = enc.encode(features, "crypto")
        assert result[0] == 0.0

    def test_encode_sanitizes_inf(self):
        enc = FeatureEncoder()
        features = {"returns_1m": float("inf")}
        result = enc.encode(features, "crypto")
        assert result[0] == 0.0

    def test_encode_sanitizes_neg_inf(self):
        enc = FeatureEncoder()
        features = {"returns_1m": float("-inf")}
        result = enc.encode(features, "crypto")
        assert result[0] == 0.0

    def test_encode_unknown_asset_raises(self):
        enc = FeatureEncoder()
        with pytest.raises(ValueError, match="Unknown asset_class"):
            enc.encode({}, "bonds")

    def test_encode_with_mask_returns_tuple(self):
        enc = FeatureEncoder()
        features = self._make_full_features()
        encoded, mask = enc.encode_with_mask(features, "crypto")
        assert len(encoded) == 99
        assert len(mask) == 99

    def test_get_mask(self):
        enc = FeatureEncoder()
        mask = enc.get_mask("crypto")
        assert mask is FEATURE_MASKS["crypto"]

    def test_count_active_crypto(self):
        enc = FeatureEncoder()
        count = enc.count_active("crypto")
        assert count > 0
        assert count <= 99

    def test_count_active_forex_less_than_crypto(self):
        enc = FeatureEncoder()
        assert enc.count_active("forex") <= enc.count_active("crypto")

    def test_target_dim(self):
        assert FeatureEncoder.TARGET_DIM == 99

    def test_encode_deterministic(self):
        """DET-05: Same inputs -> same outputs."""
        enc = FeatureEncoder()
        features = {"returns_1m": 0.03, "rsi_14": 60.0}
        r1 = enc.encode(features, "forex")
        r2 = enc.encode(features, "forex")
        assert r1 == r2

    def test_all_encoded_values_finite(self):
        enc = FeatureEncoder()
        features = {name: float("nan") if i % 3 == 0 else 1.0
                     for i, name in enumerate(FEATURE_NAMES)}
        for ac in VALID_ASSET_CLASSES:
            result = enc.encode(features, ac)
            for v in result:
                assert math.isfinite(v), f"{ac}: non-finite value in encoded output"


# ---------------------------------------------------------------------------
# FEATURE REGISTRY
# ---------------------------------------------------------------------------

class TestFeatureRegistry:
    def test_instantiation(self):
        reg = FeatureRegistry()
        assert reg is not None

    def test_get_active_features_returns_list(self):
        reg = FeatureRegistry()
        active = reg.get_active_features("crypto")
        assert isinstance(active, list)
        assert len(active) > 0

    def test_get_inactive_features_returns_list(self):
        reg = FeatureRegistry()
        inactive = reg.get_inactive_features("crypto")
        assert isinstance(inactive, list)

    def test_active_plus_inactive_equals_99(self):
        reg = FeatureRegistry()
        for ac in VALID_ASSET_CLASSES:
            active = reg.get_active_features(ac)
            inactive = reg.get_inactive_features(ac)
            assert len(active) + len(inactive) == 99, f"{ac}: sum != 99"

    def test_no_overlap_active_inactive(self):
        reg = FeatureRegistry()
        for ac in VALID_ASSET_CLASSES:
            active = set(reg.get_active_features(ac))
            inactive = set(reg.get_inactive_features(ac))
            assert len(active & inactive) == 0

    def test_encode(self):
        reg = FeatureRegistry()
        features = {name: 1.0 for name in FEATURE_NAMES}
        result = reg.encode(features, "crypto")
        assert len(result) == 99

    def test_encode_with_mask(self):
        reg = FeatureRegistry()
        features = {name: 1.0 for name in FEATURE_NAMES}
        encoded, mask = reg.encode_with_mask(features, "forex")
        assert len(encoded) == 99
        assert len(mask) == 99

    def test_apply_mask(self):
        reg = FeatureRegistry()
        raw = [1.0] * 99
        masked = reg.apply_mask(raw, "forex")
        assert len(masked) == 99
        # On-chain should be zeroed for forex
        idx = _FEATURE_INDEX["exchange_net_flow"]
        assert masked[idx] == 0.0

    def test_apply_mask_wrong_length_raises(self):
        reg = FeatureRegistry()
        with pytest.raises(ValueError, match="must have 99"):
            reg.apply_mask([1.0] * 50, "crypto")

    def test_apply_mask_preserves_active(self):
        reg = FeatureRegistry()
        raw = [2.5] * 99
        masked = reg.apply_mask(raw, "crypto")
        mask = get_feature_mask("crypto")
        for i in range(99):
            if mask[i] == 1.0:
                assert masked[i] == 2.5
            else:
                assert masked[i] == 0.0

    def test_get_feature_index(self):
        reg = FeatureRegistry()
        assert reg.get_feature_index("returns_1m") == 0
        assert reg.get_feature_index("rsi_14") == _FEATURE_INDEX["rsi_14"]

    def test_get_feature_index_unknown_raises(self):
        reg = FeatureRegistry()
        with pytest.raises(ValueError, match="Unknown feature"):
            reg.get_feature_index("nonexistent_feature")

    def test_get_feature_metadata(self):
        reg = FeatureRegistry()
        md = reg.get_feature_metadata("returns_1m")
        assert md.index == 0
        assert md.name == "returns_1m"
        assert md.category == "universal"
        assert md.group == "price_action"

    def test_get_category_features_universal(self):
        reg = FeatureRegistry()
        universal = reg.get_category_features("universal")
        assert len(universal) == 40

    def test_get_category_features_asset_specific(self):
        reg = FeatureRegistry()
        specific = reg.get_category_features("asset_specific")
        assert len(specific) == 30

    def test_get_category_features_cross_asset(self):
        reg = FeatureRegistry()
        cross = reg.get_category_features("cross_asset")
        assert len(cross) == 29

    def test_get_category_invalid_raises(self):
        reg = FeatureRegistry()
        with pytest.raises(ValueError, match="Invalid category"):
            reg.get_category_features("other")

    def test_get_group_features_price_action(self):
        reg = FeatureRegistry()
        pa = reg.get_group_features("price_action")
        assert len(pa) == 15
        assert "returns_1m" in pa

    def test_get_group_features_on_chain(self):
        reg = FeatureRegistry()
        oc = reg.get_group_features("on_chain")
        assert len(oc) == 12
        assert "exchange_net_flow" in oc

    def test_count_active(self):
        reg = FeatureRegistry()
        for ac in VALID_ASSET_CLASSES:
            count = reg.count_active(ac)
            assert 0 < count <= 99

    def test_is_feature_active_crypto_on_chain(self):
        reg = FeatureRegistry()
        assert reg.is_feature_active("exchange_net_flow", "crypto") is True
        assert reg.is_feature_active("exchange_net_flow", "forex") is False

    def test_is_feature_active_universal(self):
        reg = FeatureRegistry()
        for ac in VALID_ASSET_CLASSES:
            assert reg.is_feature_active("returns_1m", ac) is True

    def test_get_asset_specific_catalog(self):
        reg = FeatureRegistry()
        crypto_cat = reg.get_asset_specific_catalog("crypto")
        assert crypto_cat is CRYPTO_SPECIFIC_FEATURES

    def test_get_asset_specific_catalog_unknown_raises(self):
        reg = FeatureRegistry()
        with pytest.raises(ValueError, match="Unknown asset_class"):
            reg.get_asset_specific_catalog("bonds")


# ---------------------------------------------------------------------------
# FEATURE ISOLATION (FAS: no feature leakage)
# ---------------------------------------------------------------------------

class TestFeatureIsolation:
    """FAS: Crypto features must NOT leak into FX models and vice versa."""

    def test_on_chain_only_crypto(self):
        """On-chain features (exchange_net_flow, etc.) only active for crypto."""
        on_chain = [
            "exchange_net_flow", "whale_transaction_count", "mvrv_ratio",
            "nvt_ratio", "active_addresses", "transaction_volume", "fees_total",
        ]
        reg = FeatureRegistry()
        for feat in on_chain:
            assert reg.is_feature_active(feat, "crypto") is True
            for ac in ("forex", "indices", "commodities", "rates"):
                assert reg.is_feature_active(feat, ac) is False, (
                    f"'{feat}' should not be active for {ac}"
                )

    def test_crypto_only_cross_asset(self):
        """hash_rate, mining_difficulty etc. only active for crypto."""
        reg = FeatureRegistry()
        for feat in CRYPTO_ONLY_CROSS_ASSET:
            assert reg.is_feature_active(feat, "crypto") is True
            for ac in ("forex", "indices", "commodities", "rates"):
                assert reg.is_feature_active(feat, ac) is False

    def test_encoding_respects_isolation(self):
        """Encoding with non-crypto asset must zero crypto-only features."""
        enc = FeatureEncoder()
        features = {name: 1.0 for name in FEATURE_NAMES}
        for ac in ("forex", "indices", "commodities", "rates"):
            result = enc.encode(features, ac)
            for feat in CRYPTO_ONLY_CROSS_ASSET:
                idx = _FEATURE_INDEX[feat]
                assert result[idx] == 0.0, (
                    f"'{feat}' should be zeroed for {ac}"
                )

    def test_mask_isolates_on_chain_for_forex(self):
        features = {name: 99.0 for name in FEATURE_NAMES}
        enc = FeatureEncoder()
        result = enc.encode(features, "forex")
        for feat in ("exchange_net_flow", "whale_transaction_count", "hash_rate"):
            idx = _FEATURE_INDEX[feat]
            assert result[idx] == 0.0


# ---------------------------------------------------------------------------
# DIMENSION CONSISTENCY (FAS: always 99)
# ---------------------------------------------------------------------------

class TestDimensionConsistency:
    def test_encode_always_99_all_asset_classes(self):
        enc = FeatureEncoder()
        for ac in VALID_ASSET_CLASSES:
            result = enc.encode({}, ac)
            assert len(result) == 99

    def test_encode_full_features_always_99(self):
        enc = FeatureEncoder()
        features = {name: 1.0 for name in FEATURE_NAMES}
        for ac in VALID_ASSET_CLASSES:
            result = enc.encode(features, ac)
            assert len(result) == 99

    def test_mask_always_99(self):
        for ac in VALID_ASSET_CLASSES:
            mask = get_feature_mask(ac)
            assert len(mask) == 99

    def test_catalog_always_99(self):
        assert len(FEATURE_CATALOG) == 99


# ---------------------------------------------------------------------------
# DETERMINISM (DET-05)
# ---------------------------------------------------------------------------

class TestDeterminism:
    def test_mask_deterministic(self):
        m1 = generate_feature_mask("crypto")
        m2 = generate_feature_mask("crypto")
        assert m1 == m2

    def test_encode_deterministic(self):
        enc = FeatureEncoder()
        features = {"returns_1m": 0.03, "rsi_14": 45.0, "adx_14": 22.0}
        r1 = enc.encode(features, "indices")
        r2 = enc.encode(features, "indices")
        assert r1 == r2

    def test_registry_active_deterministic(self):
        reg = FeatureRegistry()
        a1 = reg.get_active_features("forex")
        a2 = reg.get_active_features("forex")
        assert a1 == a2

    def test_different_asset_class_different_mask(self):
        m_crypto = get_feature_mask("crypto")
        m_forex = get_feature_mask("forex")
        assert m_crypto != m_forex


# ---------------------------------------------------------------------------
# NO GLOBAL MUTABLE STATE (PROHIBITED-05)
# ---------------------------------------------------------------------------

class TestImmutability:
    def test_masks_are_tuples(self):
        """Tuples are immutable -> no accidental mutation."""
        for ac, mask in FEATURE_MASKS.items():
            assert isinstance(mask, tuple)

    def test_catalog_is_tuple(self):
        assert isinstance(FEATURE_CATALOG, tuple)

    def test_universal_features_is_tuple(self):
        assert isinstance(UNIVERSAL_FEATURES, tuple)

    def test_cross_asset_features_is_tuple(self):
        assert isinstance(CROSS_ASSET_FEATURES, tuple)

    def test_metadata_frozen(self):
        fm = FEATURE_CATALOG[0]
        with pytest.raises(AttributeError):
            fm.name = "hacked"


# ---------------------------------------------------------------------------
# EDGE CASES
# ---------------------------------------------------------------------------

class TestEdgeCases:
    def test_encode_extra_keys_ignored(self):
        enc = FeatureEncoder()
        features = {"nonexistent_feature": 999.0}
        result = enc.encode(features, "crypto")
        assert all(v == 0.0 for v in result)

    def test_encode_negative_values(self):
        enc = FeatureEncoder()
        features = {"returns_1m": -0.05}
        result = enc.encode(features, "crypto")
        assert result[0] == -0.05

    def test_encode_large_values(self):
        enc = FeatureEncoder()
        features = {"returns_1m": 1e10}
        result = enc.encode(features, "crypto")
        assert result[0] == 1e10

    def test_encode_zero_values(self):
        enc = FeatureEncoder()
        features = {"returns_1m": 0.0}
        result = enc.encode(features, "crypto")
        assert result[0] == 0.0

    def test_registry_empty_group(self):
        reg = FeatureRegistry()
        result = reg.get_group_features("nonexistent_group")
        assert result == []


# ---------------------------------------------------------------------------
# PACKAGE IMPORT
# ---------------------------------------------------------------------------

class TestPackageImport:
    def test_import_all_public(self):
        from jarvis.core.feature_registry import (
            FeatureRegistry,
            FeatureEncoder,
            FeatureMetadata,
            UNIVERSAL_FEATURES,
            CROSS_ASSET_FEATURES,
            FEATURE_MASKS,
            FEATURE_CATALOG,
            generate_feature_mask,
            get_feature_mask,
        )
        assert FeatureRegistry is not None
        assert FeatureEncoder is not None
