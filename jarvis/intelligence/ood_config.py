# =============================================================================
# jarvis/intelligence/ood_config.py -- Asset-Specific OOD Configurations (Phase MA-4)
#
# Defines per-asset-class OOD detection thresholds, component weights,
# and macro sensitivity matrices.
#
# =============================================================================
# FAS COMPLIANCE DECLARATION
# =============================================================================
#
# Dependency matrix:
#   ood_config.py -> jarvis.core.regime (AssetClass)
#   ood_config.py -> (stdlib only otherwise)
#
# DETERMINISM GUARANTEES: DET-01 through DET-07 enforced.
#   DET-06: All thresholds are fixed literals, not parameterizable.
#
# PROHIBITED ACTIONS CONFIRMED ABSENT:
#   PROHIBITED-01: No numpy.
#   PROHIBITED-02: No file I/O.
#   PROHIBITED-03: No logging/print.
#   PROHIBITED-08: No new Enum definitions. Severity uses string constants.
#   PROHIBITED-09: No string-based regime branching.
#
# ASCII COMPLIANCE: All literals are 7-bit ASCII.
# =============================================================================

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, Tuple

from jarvis.core.regime import AssetClass


# =============================================================================
# SECTION 1 -- SEVERITY CONSTANTS (string-based metadata, not Enums per P-08)
# =============================================================================

SEVERITY_CRITICAL: str = "CRITICAL"
SEVERITY_HIGH: str = "HIGH"
SEVERITY_MEDIUM: str = "MEDIUM"
SEVERITY_LOW: str = "LOW"

SEVERITY_LEVELS: Tuple[str, ...] = (
    SEVERITY_LOW,
    SEVERITY_MEDIUM,
    SEVERITY_HIGH,
    SEVERITY_CRITICAL,
)

# OOD score -> severity thresholds (DET-06: fixed literals)
SEVERITY_CRITICAL_THRESHOLD: float = 0.8
SEVERITY_HIGH_THRESHOLD: float = 0.6
SEVERITY_MEDIUM_THRESHOLD: float = 0.4

# Sensor detection threshold for consensus voting (DET-06)
SENSOR_DETECTION_THRESHOLD: float = 0.5

# OOD consensus minimum (matches THRESHOLD_MANIFEST.json)
OOD_CONSENSUS_MINIMUM: int = 3

# Regime OOD weight (fixed across all asset classes)
REGIME_OOD_WEIGHT: float = 0.1

# Macro event types (FAS canonical list)
MACRO_EVENT_TYPES: Tuple[str, ...] = (
    "fed_meeting",
    "ecb_meeting",
    "nonfarm_payrolls",
    "cpi_release",
    "geopolitical_shock",
    "credit_event",
    "earnings_season",
)


# =============================================================================
# SECTION 2 -- ASSET OOD CONFIG DATACLASS
# =============================================================================

@dataclass(frozen=True)
class AssetOODConfig:
    """OOD configuration per asset class.

    Attributes:
        asset_class: Canonical AssetClass.
        ood_threshold: Overall OOD decision threshold [0, 1].
        flash_crash_threshold: Price move magnitude for flash crash [0, 1].
        volatility_spike_threshold: Vol multiplier for spike detection.
        liquidity_drain_threshold: Liquidity drop fraction for drain [0, 1].
        distribution_weight: Weight for distribution OOD component.
        event_weight: Weight for event OOD component.
        macro_weight: Weight for macro OOD component.
        macro_sensitivity: Dict mapping macro event type -> sensitivity [0, 1].
    """
    asset_class: AssetClass
    ood_threshold: float
    flash_crash_threshold: float
    volatility_spike_threshold: float
    liquidity_drain_threshold: float
    distribution_weight: float
    event_weight: float
    macro_weight: float
    macro_sensitivity: Dict[str, float]


# =============================================================================
# SECTION 3 -- CANONICAL ASSET OOD CONFIGS (DET-06: fixed literals)
# =============================================================================

CRYPTO_OOD = AssetOODConfig(
    asset_class=AssetClass.CRYPTO,
    ood_threshold=0.7,              # More tolerant (crypto is volatile)
    flash_crash_threshold=0.15,     # 15% move = normal for crypto
    volatility_spike_threshold=2.0, # 200% vol increase
    liquidity_drain_threshold=0.3,  # 70% liquidity drop
    distribution_weight=0.4,
    event_weight=0.4,
    macro_weight=0.2,               # Less macro-sensitive
    macro_sensitivity={
        "fed_meeting": 0.5,
        "ecb_meeting": 0.2,
        "nonfarm_payrolls": 0.3,
        "cpi_release": 0.4,
        "geopolitical_shock": 0.6,
        "credit_event": 0.7,
        "earnings_season": 0.1,
    },
)

FOREX_OOD = AssetOODConfig(
    asset_class=AssetClass.FOREX,
    ood_threshold=0.5,              # Very sensitive (FX is stable)
    flash_crash_threshold=0.03,     # 3% move = extreme for FX
    volatility_spike_threshold=0.8, # 80% vol increase
    liquidity_drain_threshold=0.5,  # 50% liquidity drop
    distribution_weight=0.3,
    event_weight=0.3,
    macro_weight=0.4,               # Very macro-sensitive
    macro_sensitivity={
        "fed_meeting": 0.9,
        "ecb_meeting": 0.9,
        "nonfarm_payrolls": 0.8,
        "cpi_release": 0.8,
        "geopolitical_shock": 0.7,
        "credit_event": 0.6,
        "earnings_season": 0.2,
    },
)

INDICES_OOD = AssetOODConfig(
    asset_class=AssetClass.INDICES,
    ood_threshold=0.6,
    flash_crash_threshold=0.05,     # 5% move significant
    volatility_spike_threshold=1.2, # 120% vol increase
    liquidity_drain_threshold=0.4,  # 60% liquidity drop
    distribution_weight=0.35,
    event_weight=0.35,
    macro_weight=0.3,
    macro_sensitivity={
        "fed_meeting": 0.8,
        "ecb_meeting": 0.6,
        "nonfarm_payrolls": 0.7,
        "cpi_release": 0.7,
        "geopolitical_shock": 0.9,
        "credit_event": 0.9,
        "earnings_season": 0.6,
    },
)

COMMODITIES_OOD = AssetOODConfig(
    asset_class=AssetClass.COMMODITIES,
    ood_threshold=0.6,
    flash_crash_threshold=0.08,     # 8% move significant
    volatility_spike_threshold=1.5, # 150% vol increase
    liquidity_drain_threshold=0.4,  # 60% liquidity drop
    distribution_weight=0.35,
    event_weight=0.4,
    macro_weight=0.25,
    macro_sensitivity={
        "fed_meeting": 0.5,
        "ecb_meeting": 0.3,
        "nonfarm_payrolls": 0.4,
        "cpi_release": 0.5,
        "geopolitical_shock": 0.9,
        "credit_event": 0.6,
        "earnings_season": 0.2,
    },
)

RATES_OOD = AssetOODConfig(
    asset_class=AssetClass.RATES,
    ood_threshold=0.5,              # Very sensitive (rates are stable)
    flash_crash_threshold=0.02,     # 2% move = extreme for rates
    volatility_spike_threshold=0.8, # 80% vol increase
    liquidity_drain_threshold=0.5,  # 50% liquidity drop
    distribution_weight=0.3,
    event_weight=0.3,
    macro_weight=0.4,               # Very macro-sensitive
    macro_sensitivity={
        "fed_meeting": 0.95,
        "ecb_meeting": 0.85,
        "nonfarm_payrolls": 0.7,
        "cpi_release": 0.8,
        "geopolitical_shock": 0.5,
        "credit_event": 0.8,
        "earnings_season": 0.1,
    },
)


# =============================================================================
# SECTION 4 -- CONFIG REGISTRY
# =============================================================================

OOD_CONFIG_REGISTRY: Dict[AssetClass, AssetOODConfig] = {
    AssetClass.CRYPTO: CRYPTO_OOD,
    AssetClass.FOREX: FOREX_OOD,
    AssetClass.INDICES: INDICES_OOD,
    AssetClass.COMMODITIES: COMMODITIES_OOD,
    AssetClass.RATES: RATES_OOD,
}


def get_ood_config(asset_class: AssetClass) -> AssetOODConfig:
    """Look up canonical OOD config for an asset class.

    Args:
        asset_class: AssetClass enum instance.

    Returns:
        AssetOODConfig for the given asset class.

    Raises:
        KeyError: If asset_class not in registry.
    """
    return OOD_CONFIG_REGISTRY[asset_class]


def classify_severity(ood_score: float) -> str:
    """Map OOD score to severity string.

    FAS severity thresholds:
        > 0.8 -> CRITICAL
        > 0.6 -> HIGH
        > 0.4 -> MEDIUM
        else  -> LOW

    Args:
        ood_score: Combined OOD score [0, 1].

    Returns:
        Severity string.
    """
    if ood_score > SEVERITY_CRITICAL_THRESHOLD:
        return SEVERITY_CRITICAL
    if ood_score > SEVERITY_HIGH_THRESHOLD:
        return SEVERITY_HIGH
    if ood_score > SEVERITY_MEDIUM_THRESHOLD:
        return SEVERITY_MEDIUM
    return SEVERITY_LOW
