# =============================================================================
# tests/unit/intelligence/test_ood_config.py -- OOD Config Tests
#
# Comprehensive tests for jarvis/intelligence/ood_config.py (Phase MA-4).
# Covers: AssetOODConfig, canonical configs, registry, severity classification,
#         thresholds, macro sensitivity, determinism, immutability.
# =============================================================================

import pytest

from jarvis.core.regime import AssetClass
from jarvis.intelligence.ood_config import (
    # Severity constants
    SEVERITY_CRITICAL,
    SEVERITY_HIGH,
    SEVERITY_MEDIUM,
    SEVERITY_LOW,
    SEVERITY_LEVELS,
    SEVERITY_CRITICAL_THRESHOLD,
    SEVERITY_HIGH_THRESHOLD,
    SEVERITY_MEDIUM_THRESHOLD,
    # Other constants
    SENSOR_DETECTION_THRESHOLD,
    OOD_CONSENSUS_MINIMUM,
    REGIME_OOD_WEIGHT,
    MACRO_EVENT_TYPES,
    # Config dataclass
    AssetOODConfig,
    # Canonical configs
    CRYPTO_OOD,
    FOREX_OOD,
    INDICES_OOD,
    COMMODITIES_OOD,
    RATES_OOD,
    # Registry + functions
    OOD_CONFIG_REGISTRY,
    get_ood_config,
    classify_severity,
)


# ---------------------------------------------------------------------------
# CONSTANTS (DET-06)
# ---------------------------------------------------------------------------

class TestConstants:
    def test_severity_strings(self):
        assert SEVERITY_CRITICAL == "CRITICAL"
        assert SEVERITY_HIGH == "HIGH"
        assert SEVERITY_MEDIUM == "MEDIUM"
        assert SEVERITY_LOW == "LOW"

    def test_severity_levels_tuple(self):
        assert SEVERITY_LEVELS == ("LOW", "MEDIUM", "HIGH", "CRITICAL")

    def test_severity_thresholds(self):
        assert SEVERITY_CRITICAL_THRESHOLD == 0.8
        assert SEVERITY_HIGH_THRESHOLD == 0.6
        assert SEVERITY_MEDIUM_THRESHOLD == 0.4

    def test_sensor_detection_threshold(self):
        assert SENSOR_DETECTION_THRESHOLD == 0.5

    def test_ood_consensus_minimum(self):
        assert OOD_CONSENSUS_MINIMUM == 3

    def test_regime_ood_weight(self):
        assert REGIME_OOD_WEIGHT == 0.1

    def test_macro_event_types(self):
        assert "fed_meeting" in MACRO_EVENT_TYPES
        assert "ecb_meeting" in MACRO_EVENT_TYPES
        assert "nonfarm_payrolls" in MACRO_EVENT_TYPES
        assert "cpi_release" in MACRO_EVENT_TYPES
        assert "geopolitical_shock" in MACRO_EVENT_TYPES
        assert "credit_event" in MACRO_EVENT_TYPES
        assert "earnings_season" in MACRO_EVENT_TYPES
        assert len(MACRO_EVENT_TYPES) == 7


# ---------------------------------------------------------------------------
# ASSET OOD CONFIG DATACLASS
# ---------------------------------------------------------------------------

class TestAssetOODConfig:
    def test_frozen(self):
        with pytest.raises(AttributeError):
            CRYPTO_OOD.ood_threshold = 0.5

    def test_fields_present(self):
        cfg = CRYPTO_OOD
        assert isinstance(cfg.asset_class, AssetClass)
        assert isinstance(cfg.ood_threshold, float)
        assert isinstance(cfg.flash_crash_threshold, float)
        assert isinstance(cfg.volatility_spike_threshold, float)
        assert isinstance(cfg.liquidity_drain_threshold, float)
        assert isinstance(cfg.distribution_weight, float)
        assert isinstance(cfg.event_weight, float)
        assert isinstance(cfg.macro_weight, float)
        assert isinstance(cfg.macro_sensitivity, dict)


# ---------------------------------------------------------------------------
# CRYPTO OOD CONFIG
# ---------------------------------------------------------------------------

class TestCryptoOOD:
    def test_asset_class(self):
        assert CRYPTO_OOD.asset_class == AssetClass.CRYPTO

    def test_ood_threshold(self):
        assert CRYPTO_OOD.ood_threshold == 0.7

    def test_flash_crash_threshold(self):
        assert CRYPTO_OOD.flash_crash_threshold == 0.15

    def test_volatility_spike_threshold(self):
        assert CRYPTO_OOD.volatility_spike_threshold == 2.0

    def test_liquidity_drain_threshold(self):
        assert CRYPTO_OOD.liquidity_drain_threshold == 0.3

    def test_weights(self):
        assert CRYPTO_OOD.distribution_weight == 0.4
        assert CRYPTO_OOD.event_weight == 0.4
        assert CRYPTO_OOD.macro_weight == 0.2

    def test_macro_sensitivity(self):
        assert CRYPTO_OOD.macro_sensitivity["fed_meeting"] == 0.5
        assert CRYPTO_OOD.macro_sensitivity["credit_event"] == 0.7
        assert CRYPTO_OOD.macro_sensitivity["geopolitical_shock"] == 0.6

    def test_less_macro_sensitive_than_forex(self):
        assert CRYPTO_OOD.macro_weight < FOREX_OOD.macro_weight


# ---------------------------------------------------------------------------
# FOREX OOD CONFIG
# ---------------------------------------------------------------------------

class TestForexOOD:
    def test_asset_class(self):
        assert FOREX_OOD.asset_class == AssetClass.FOREX

    def test_ood_threshold(self):
        assert FOREX_OOD.ood_threshold == 0.5

    def test_flash_crash_threshold(self):
        assert FOREX_OOD.flash_crash_threshold == 0.03

    def test_more_sensitive_than_crypto(self):
        assert FOREX_OOD.ood_threshold < CRYPTO_OOD.ood_threshold
        assert FOREX_OOD.flash_crash_threshold < CRYPTO_OOD.flash_crash_threshold

    def test_macro_sensitivity_high(self):
        assert FOREX_OOD.macro_sensitivity["fed_meeting"] == 0.9
        assert FOREX_OOD.macro_sensitivity["ecb_meeting"] == 0.9

    def test_weights(self):
        assert FOREX_OOD.distribution_weight == 0.3
        assert FOREX_OOD.event_weight == 0.3
        assert FOREX_OOD.macro_weight == 0.4


# ---------------------------------------------------------------------------
# INDICES OOD CONFIG
# ---------------------------------------------------------------------------

class TestIndicesOOD:
    def test_asset_class(self):
        assert INDICES_OOD.asset_class == AssetClass.INDICES

    def test_ood_threshold(self):
        assert INDICES_OOD.ood_threshold == 0.6

    def test_flash_crash_threshold(self):
        assert INDICES_OOD.flash_crash_threshold == 0.05

    def test_credit_event_sensitivity(self):
        assert INDICES_OOD.macro_sensitivity["credit_event"] == 0.9

    def test_weights(self):
        assert INDICES_OOD.distribution_weight == 0.35
        assert INDICES_OOD.event_weight == 0.35
        assert INDICES_OOD.macro_weight == 0.3


# ---------------------------------------------------------------------------
# COMMODITIES OOD CONFIG
# ---------------------------------------------------------------------------

class TestCommoditiesOOD:
    def test_asset_class(self):
        assert COMMODITIES_OOD.asset_class == AssetClass.COMMODITIES

    def test_ood_threshold(self):
        assert COMMODITIES_OOD.ood_threshold == 0.6

    def test_flash_crash_threshold(self):
        assert COMMODITIES_OOD.flash_crash_threshold == 0.08

    def test_geopolitical_sensitivity(self):
        assert COMMODITIES_OOD.macro_sensitivity["geopolitical_shock"] == 0.9

    def test_weights(self):
        assert COMMODITIES_OOD.distribution_weight == 0.35
        assert COMMODITIES_OOD.event_weight == 0.4
        assert COMMODITIES_OOD.macro_weight == 0.25


# ---------------------------------------------------------------------------
# RATES OOD CONFIG
# ---------------------------------------------------------------------------

class TestRatesOOD:
    def test_asset_class(self):
        assert RATES_OOD.asset_class == AssetClass.RATES

    def test_ood_threshold(self):
        assert RATES_OOD.ood_threshold == 0.5

    def test_flash_crash_threshold(self):
        assert RATES_OOD.flash_crash_threshold == 0.02

    def test_fed_meeting_very_sensitive(self):
        assert RATES_OOD.macro_sensitivity["fed_meeting"] == 0.95

    def test_most_sensitive_to_fed(self):
        for cfg in [CRYPTO_OOD, FOREX_OOD, INDICES_OOD, COMMODITIES_OOD]:
            assert RATES_OOD.macro_sensitivity["fed_meeting"] >= cfg.macro_sensitivity["fed_meeting"]


# ---------------------------------------------------------------------------
# OOD CONFIG REGISTRY
# ---------------------------------------------------------------------------

class TestRegistry:
    def test_all_asset_classes_present(self):
        for ac in AssetClass:
            assert ac in OOD_CONFIG_REGISTRY

    def test_registry_values_match_configs(self):
        assert OOD_CONFIG_REGISTRY[AssetClass.CRYPTO] is CRYPTO_OOD
        assert OOD_CONFIG_REGISTRY[AssetClass.FOREX] is FOREX_OOD
        assert OOD_CONFIG_REGISTRY[AssetClass.INDICES] is INDICES_OOD
        assert OOD_CONFIG_REGISTRY[AssetClass.COMMODITIES] is COMMODITIES_OOD
        assert OOD_CONFIG_REGISTRY[AssetClass.RATES] is RATES_OOD

    def test_get_ood_config(self):
        cfg = get_ood_config(AssetClass.CRYPTO)
        assert cfg is CRYPTO_OOD

    def test_get_ood_config_all(self):
        for ac in AssetClass:
            cfg = get_ood_config(ac)
            assert cfg.asset_class == ac


# ---------------------------------------------------------------------------
# SEVERITY CLASSIFICATION
# ---------------------------------------------------------------------------

class TestSeverityClassification:
    def test_critical(self):
        assert classify_severity(0.85) == SEVERITY_CRITICAL

    def test_high(self):
        assert classify_severity(0.65) == SEVERITY_HIGH

    def test_medium(self):
        assert classify_severity(0.45) == SEVERITY_MEDIUM

    def test_low(self):
        assert classify_severity(0.2) == SEVERITY_LOW

    def test_boundary_critical(self):
        assert classify_severity(0.801) == SEVERITY_CRITICAL

    def test_boundary_at_critical(self):
        # > 0.8, not >=
        assert classify_severity(0.8) == SEVERITY_HIGH

    def test_boundary_at_high(self):
        assert classify_severity(0.6) == SEVERITY_MEDIUM

    def test_boundary_at_medium(self):
        assert classify_severity(0.4) == SEVERITY_LOW

    def test_zero(self):
        assert classify_severity(0.0) == SEVERITY_LOW

    def test_one(self):
        assert classify_severity(1.0) == SEVERITY_CRITICAL


# ---------------------------------------------------------------------------
# CROSS-ASSET CONSISTENCY
# ---------------------------------------------------------------------------

class TestCrossAssetConsistency:
    def test_all_thresholds_in_range(self):
        for ac in AssetClass:
            cfg = get_ood_config(ac)
            assert 0.0 < cfg.ood_threshold <= 1.0
            assert 0.0 < cfg.flash_crash_threshold <= 1.0
            assert cfg.volatility_spike_threshold > 0.0
            assert 0.0 < cfg.liquidity_drain_threshold <= 1.0

    def test_all_weights_positive(self):
        for ac in AssetClass:
            cfg = get_ood_config(ac)
            assert cfg.distribution_weight > 0.0
            assert cfg.event_weight > 0.0
            assert cfg.macro_weight > 0.0

    def test_weight_sum_approximately_one(self):
        """Component weights (excl. regime) should sum to ~1.0."""
        for ac in AssetClass:
            cfg = get_ood_config(ac)
            total = cfg.distribution_weight + cfg.event_weight + cfg.macro_weight
            assert abs(total - 1.0) < 0.05

    def test_all_macro_sensitivities_in_range(self):
        for ac in AssetClass:
            cfg = get_ood_config(ac)
            for event_type, sensitivity in cfg.macro_sensitivity.items():
                assert 0.0 <= sensitivity <= 1.0, \
                    f"{ac.value}/{event_type}: {sensitivity}"

    def test_crypto_most_tolerant(self):
        """Crypto should have highest ood_threshold (most tolerant)."""
        for ac in [AssetClass.FOREX, AssetClass.RATES]:
            assert CRYPTO_OOD.ood_threshold > get_ood_config(ac).ood_threshold

    def test_forex_rates_most_sensitive_flash_crash(self):
        """FX and rates have lowest flash crash thresholds."""
        for ac in [AssetClass.CRYPTO, AssetClass.INDICES, AssetClass.COMMODITIES]:
            assert FOREX_OOD.flash_crash_threshold < get_ood_config(ac).flash_crash_threshold
            assert RATES_OOD.flash_crash_threshold < get_ood_config(ac).flash_crash_threshold


# ---------------------------------------------------------------------------
# DETERMINISM (DET-05)
# ---------------------------------------------------------------------------

class TestDeterminism:
    def test_severity_deterministic(self):
        assert classify_severity(0.7) == classify_severity(0.7)

    def test_config_values_stable(self):
        c1 = get_ood_config(AssetClass.CRYPTO)
        c2 = get_ood_config(AssetClass.CRYPTO)
        assert c1.ood_threshold == c2.ood_threshold
        assert c1.flash_crash_threshold == c2.flash_crash_threshold


# ---------------------------------------------------------------------------
# PACKAGE IMPORT
# ---------------------------------------------------------------------------

class TestPackageImport:
    def test_import_all(self):
        from jarvis.intelligence.ood_config import (
            AssetOODConfig,
            CRYPTO_OOD,
            FOREX_OOD,
            INDICES_OOD,
            COMMODITIES_OOD,
            RATES_OOD,
            OOD_CONFIG_REGISTRY,
            get_ood_config,
            classify_severity,
        )
        assert AssetOODConfig is not None
