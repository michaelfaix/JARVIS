# =============================================================================
# jarvis/core/feature_registry.py -- Asset-Class-Aware Feature Registry (Phase MA-2)
#
# Multi-Asset Feature Registry: classifies, masks, and encodes the 99-dim
# feature vector defined in feature_layer.py for asset-class-aware usage.
#
# This module does NOT compute features. Computation stays in feature_layer.py.
# This module provides:
#   - Asset-class feature classification (Universal / Asset-Specific / Cross-Asset)
#   - Feature masks per asset class (which features are active/meaningful)
#   - FeatureEncoder for consistent 99-dim encoding with masking
#   - Asset-specific feature catalogs
#
# =============================================================================
# FAS COMPLIANCE DECLARATION
# =============================================================================
#
# Dependency matrix (binding):
#   feature_registry.py -> feature_layer.py  (FEATURE_NAMES, FEATURE_VECTOR_SIZE)
#   feature_registry.py -> data_structures.py (VALID_ASSET_CLASSES)
#
# Import rules: core/ -> (stdlib + core/ only). No external layer imports.
#
# DETERMINISM GUARANTEES:
#   DET-01  No stochastic operations.
#   DET-02  All inputs passed explicitly. No module-level mutable reads.
#   DET-03  No side effects in computational functions.
#   DET-04  All branches deterministic functions of explicit inputs.
#   DET-05  Same inputs -> same outputs.
#   DET-06  Fixed literals not parameterizable.
#
# PROHIBITED ACTIONS CONFIRMED ABSENT:
#   PROHIBITED-01 through PROHIBITED-10: All confirmed absent.
#
# ASCII COMPLIANCE: All literals are 7-bit ASCII.
# =============================================================================

from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Dict, FrozenSet, List, Tuple

from jarvis.core.feature_layer import FEATURE_NAMES, FEATURE_VECTOR_SIZE
from jarvis.core.data_structures import VALID_ASSET_CLASSES


# =============================================================================
# SECTION 1 -- INDEX RANGES (DET-06: fixed literals)
# =============================================================================

# FAS: 99-dim feature vector partitioned into three blocks.
UNIVERSAL_START: int = 0
UNIVERSAL_END: int = 40      # exclusive -> indices 0..39
ASSET_SPECIFIC_START: int = 40
ASSET_SPECIFIC_END: int = 70  # exclusive -> indices 40..69
CROSS_ASSET_START: int = 70
CROSS_ASSET_END: int = 99     # exclusive -> indices 70..98

UNIVERSAL_COUNT: int = UNIVERSAL_END - UNIVERSAL_START          # 40
ASSET_SPECIFIC_COUNT: int = ASSET_SPECIFIC_END - ASSET_SPECIFIC_START  # 30
CROSS_ASSET_COUNT: int = CROSS_ASSET_END - CROSS_ASSET_START    # 29

# Compile-time check
assert UNIVERSAL_COUNT + ASSET_SPECIFIC_COUNT + CROSS_ASSET_COUNT == FEATURE_VECTOR_SIZE, (
    f"Feature partition mismatch: {UNIVERSAL_COUNT}+{ASSET_SPECIFIC_COUNT}"
    f"+{CROSS_ASSET_COUNT} != {FEATURE_VECTOR_SIZE}"
)


# =============================================================================
# SECTION 2 -- FEATURE CLASSIFICATION
# =============================================================================

# Universal features (indices 0-39): active for ALL asset classes.
# Covers Price Action [0-14], Volume & Liquidity [15-26], and most Technical [27-39].
UNIVERSAL_FEATURES: Tuple[str, ...] = tuple(FEATURE_NAMES[UNIVERSAL_START:UNIVERSAL_END])

# Cross-Asset features (indices 70-98): active for ALL asset classes.
# Covers the tail of On-Chain [70-74], Regime [75-82], Sentiment [83-92], Meta [93-98].
CROSS_ASSET_FEATURES: Tuple[str, ...] = tuple(FEATURE_NAMES[CROSS_ASSET_START:CROSS_ASSET_END])

# Asset-Specific features (indices 40-69): active features VARY by asset class.
# The underlying feature_layer.py stores all features at fixed positions.
# The registry defines which positions are MEANINGFUL per asset class via masks.
ALL_ASSET_SPECIFIC_NAMES: Tuple[str, ...] = tuple(
    FEATURE_NAMES[ASSET_SPECIFIC_START:ASSET_SPECIFIC_END]
)


# =============================================================================
# SECTION 3 -- ASSET-SPECIFIC FEATURE CATALOGS
# =============================================================================

# FAS: Each asset class has its own set of meaningful features in the 40-69 range.
# Features NOT in the catalog for an asset class are masked to 0.0.

# Crypto: All 30 features in 40-69 range are meaningful (crypto-first design)
CRYPTO_SPECIFIC_FEATURES: Tuple[str, ...] = (
    # Technical tail [40-44]
    "williams_r", "mfi_14", "obv", "cmf_20", "vwap_distance",
    # Microstructure [45-54]
    "tick_direction", "trade_classification", "order_flow_imbalance",
    "vpin", "micro_effective_spread", "price_impact",
    "kyle_lambda", "roll_spread", "adverse_selection_component",
    "market_quality_index",
    # Cross-Asset correlations [55-62]
    "btc_eth_correlation", "btc_gold_spread", "btc_sp500_correlation",
    "crypto_index_performance", "sector_momentum",
    "alt_season_indicator", "dominance_btc", "stablecoin_flow",
    # On-Chain [63-69]
    "exchange_net_flow", "whale_transaction_count", "mvrv_ratio",
    "nvt_ratio", "active_addresses", "transaction_volume", "fees_total",
)

# Forex: Technical tail + microstructure meaningful; crypto cross-asset & on-chain not
FOREX_SPECIFIC_FEATURES: Tuple[str, ...] = (
    # Technical tail [40-44]
    "williams_r", "mfi_14", "obv", "cmf_20", "vwap_distance",
    # Microstructure [45-54]
    "tick_direction", "trade_classification", "order_flow_imbalance",
    "vpin", "micro_effective_spread", "price_impact",
    "kyle_lambda", "roll_spread", "adverse_selection_component",
    "market_quality_index",
)

# Indices: Technical tail + microstructure + some cross-asset meaningful
INDICES_SPECIFIC_FEATURES: Tuple[str, ...] = (
    # Technical tail [40-44]
    "williams_r", "mfi_14", "obv", "cmf_20", "vwap_distance",
    # Microstructure [45-54]
    "tick_direction", "trade_classification", "order_flow_imbalance",
    "vpin", "micro_effective_spread", "price_impact",
    "kyle_lambda", "roll_spread", "adverse_selection_component",
    "market_quality_index",
    # Cross-Asset [55-59]
    "btc_eth_correlation", "btc_gold_spread", "btc_sp500_correlation",
    "crypto_index_performance", "sector_momentum",
)

# Commodities: Technical tail + microstructure meaningful
COMMODITIES_SPECIFIC_FEATURES: Tuple[str, ...] = (
    # Technical tail [40-44]
    "williams_r", "mfi_14", "obv", "cmf_20", "vwap_distance",
    # Microstructure [45-54]
    "tick_direction", "trade_classification", "order_flow_imbalance",
    "vpin", "micro_effective_spread", "price_impact",
    "kyle_lambda", "roll_spread", "adverse_selection_component",
    "market_quality_index",
)

# Rates: Technical tail + microstructure meaningful
RATES_SPECIFIC_FEATURES: Tuple[str, ...] = (
    # Technical tail [40-44]
    "williams_r", "mfi_14", "obv", "cmf_20", "vwap_distance",
    # Microstructure [45-54]
    "tick_direction", "trade_classification", "order_flow_imbalance",
    "vpin", "micro_effective_spread", "price_impact",
    "kyle_lambda", "roll_spread", "adverse_selection_component",
    "market_quality_index",
)

# Catalog lookup
ASSET_SPECIFIC_CATALOG: Dict[str, Tuple[str, ...]] = {
    "crypto":      CRYPTO_SPECIFIC_FEATURES,
    "forex":       FOREX_SPECIFIC_FEATURES,
    "indices":     INDICES_SPECIFIC_FEATURES,
    "commodities": COMMODITIES_SPECIFIC_FEATURES,
    "rates":       RATES_SPECIFIC_FEATURES,
}


# =============================================================================
# SECTION 4 -- CROSS-ASSET FEATURE AVAILABILITY
# =============================================================================

# FAS: Cross-asset features (70-98) are computed for ALL asset classes,
# but some features are more meaningful for certain asset classes.
# On-Chain features (hash_rate, mining_difficulty, etc.) are crypto-only.

# Cross-asset features that are crypto-only (masked for other asset classes)
CRYPTO_ONLY_CROSS_ASSET: FrozenSet[str] = frozenset({
    "hash_rate",
    "mining_difficulty",
    "realized_cap",
    "utxo_age_distribution",
    "holder_composition",
})

# Cross-asset features active per asset class
CROSS_ASSET_ACTIVE: Dict[str, FrozenSet[str]] = {
    "crypto": frozenset(CROSS_ASSET_FEATURES),
    "forex": frozenset(CROSS_ASSET_FEATURES) - CRYPTO_ONLY_CROSS_ASSET,
    "indices": frozenset(CROSS_ASSET_FEATURES) - CRYPTO_ONLY_CROSS_ASSET,
    "commodities": frozenset(CROSS_ASSET_FEATURES) - CRYPTO_ONLY_CROSS_ASSET,
    "rates": frozenset(CROSS_ASSET_FEATURES) - CRYPTO_ONLY_CROSS_ASSET,
}


# =============================================================================
# SECTION 5 -- FEATURE MASK GENERATION
# =============================================================================

def _build_feature_name_to_index() -> Dict[str, int]:
    """Build name -> index mapping from canonical FEATURE_NAMES."""
    return {name: idx for idx, name in enumerate(FEATURE_NAMES)}


_FEATURE_INDEX: Dict[str, int] = _build_feature_name_to_index()


def generate_feature_mask(asset_class: str) -> List[float]:
    """Generate a 99-dim feature mask for the given asset class.

    Mask values:
        1.0 = feature is active/meaningful for this asset class.
        0.0 = feature is inactive/not meaningful (should be zeroed).

    Universal features (0-39) are always active.
    Asset-specific features (40-69) depend on asset class catalog.
    Cross-asset features (70-98) exclude crypto-only for non-crypto.

    Args:
        asset_class: Canonical asset class identifier.

    Returns:
        List of 99 floats (1.0 or 0.0).

    Raises:
        ValueError: If asset_class is not recognized.
    """
    if asset_class not in VALID_ASSET_CLASSES:
        raise ValueError(
            f"Unknown asset_class: '{asset_class}'. "
            f"Must be one of {sorted(VALID_ASSET_CLASSES)}."
        )

    mask = [0.0] * FEATURE_VECTOR_SIZE

    # Universal features: always active
    for i in range(UNIVERSAL_START, UNIVERSAL_END):
        mask[i] = 1.0

    # Asset-specific features: only those in the catalog
    catalog = ASSET_SPECIFIC_CATALOG.get(asset_class, ())
    catalog_set = frozenset(catalog)
    for i in range(ASSET_SPECIFIC_START, ASSET_SPECIFIC_END):
        if FEATURE_NAMES[i] in catalog_set:
            mask[i] = 1.0

    # Cross-asset features: active per asset class
    active_cross = CROSS_ASSET_ACTIVE.get(asset_class, frozenset())
    for i in range(CROSS_ASSET_START, CROSS_ASSET_END):
        if FEATURE_NAMES[i] in active_cross:
            mask[i] = 1.0

    return mask


# Pre-computed masks (DET-06: fixed at module load, immutable)
FEATURE_MASKS: Dict[str, Tuple[float, ...]] = {
    ac: tuple(generate_feature_mask(ac)) for ac in VALID_ASSET_CLASSES
}


def get_feature_mask(asset_class: str) -> Tuple[float, ...]:
    """Retrieve pre-computed feature mask for an asset class.

    Args:
        asset_class: Canonical asset class identifier.

    Returns:
        Tuple of 99 floats (1.0 or 0.0).

    Raises:
        ValueError: If asset_class is not recognized.
    """
    if asset_class not in FEATURE_MASKS:
        raise ValueError(
            f"Unknown asset_class: '{asset_class}'. "
            f"Must be one of {sorted(FEATURE_MASKS.keys())}."
        )
    return FEATURE_MASKS[asset_class]


# =============================================================================
# SECTION 6 -- FEATURE METADATA
# =============================================================================

@dataclass(frozen=True)
class FeatureMetadata:
    """Metadata for a single feature in the 99-dim vector.

    Attributes:
        index: Position in the 99-dim vector.
        name: Canonical feature name.
        category: One of 'universal', 'asset_specific', 'cross_asset'.
        group: Semantic group (e.g. 'price_action', 'technical', ...).
        description: Short description.
    """

    index: int
    name: str
    category: str      # "universal" | "asset_specific" | "cross_asset"
    group: str
    description: str


def _classify_category(index: int) -> str:
    """Classify feature category by index."""
    if UNIVERSAL_START <= index < UNIVERSAL_END:
        return "universal"
    if ASSET_SPECIFIC_START <= index < ASSET_SPECIFIC_END:
        return "asset_specific"
    return "cross_asset"


def _classify_group(index: int) -> str:
    """Classify semantic group by index."""
    if index <= 14:
        return "price_action"
    if index <= 26:
        return "volume_liquidity"
    if index <= 44:
        return "technical"
    if index <= 54:
        return "microstructure"
    if index <= 62:
        return "cross_asset_correlation"
    if index <= 74:
        return "on_chain"
    if index <= 82:
        return "regime_state"
    if index <= 92:
        return "sentiment"
    return "meta"


# Group descriptions (short, for metadata)
_GROUP_DESCRIPTIONS: Dict[str, str] = {
    "price_action": "Price returns, volatility, trend, support/resistance",
    "volume_liquidity": "Volume ratios, spreads, liquidity metrics",
    "technical": "RSI, MACD, Bollinger, ATR, ADX, CCI, Stochastic, etc.",
    "microstructure": "Tick direction, order flow, price impact, Kyle lambda",
    "cross_asset_correlation": "Cross-asset correlations and relative performance",
    "on_chain": "Blockchain metrics (crypto-only)",
    "regime_state": "Regime detection, stress, crisis probability",
    "sentiment": "Fear/greed, social sentiment, funding rate, OI",
    "meta": "Data quality, drift, completeness, staleness",
}


def build_feature_catalog() -> Tuple[FeatureMetadata, ...]:
    """Build complete metadata catalog for all 99 features.

    Returns:
        Tuple of 99 FeatureMetadata objects in canonical order.
    """
    catalog = []
    for i, name in enumerate(FEATURE_NAMES):
        cat = _classify_category(i)
        grp = _classify_group(i)
        desc = _GROUP_DESCRIPTIONS.get(grp, "")
        catalog.append(FeatureMetadata(
            index=i,
            name=name,
            category=cat,
            group=grp,
            description=desc,
        ))
    return tuple(catalog)


# Pre-built catalog (immutable)
FEATURE_CATALOG: Tuple[FeatureMetadata, ...] = build_feature_catalog()


# =============================================================================
# SECTION 7 -- FEATURE ENCODER
# =============================================================================

class FeatureEncoder:
    """Encodes feature dicts to fixed 99-dim lists with asset-class masking.

    FAS: FeatureEncoder ensures consistent feature dimensions across assets.
    Unused slots are set to 0.0. Feature mask tracks active features.
    No NaN/Inf allowed in output.

    Usage:
        encoder = FeatureEncoder()
        encoded = encoder.encode(features_dict, "crypto")
        mask = encoder.get_mask("crypto")
    """

    TARGET_DIM: int = FEATURE_VECTOR_SIZE  # 99, DET-06

    def encode(
        self,
        features: Dict[str, float],
        asset_class: str,
    ) -> List[float]:
        """Convert feature dict to 99-dim list with asset-class masking.

        Universal features (0-39) are always included.
        Asset-specific features (40-69) are masked per asset class.
        Cross-asset features (70-98) exclude crypto-only for non-crypto.
        Missing features default to 0.0.
        NaN/Inf values are replaced with 0.0.

        Args:
            features: Dict mapping feature names to float values.
            asset_class: Canonical asset class identifier.

        Returns:
            List of exactly 99 floats.

        Raises:
            ValueError: If asset_class is not recognized.
        """
        if asset_class not in VALID_ASSET_CLASSES:
            raise ValueError(
                f"Unknown asset_class: '{asset_class}'. "
                f"Must be one of {sorted(VALID_ASSET_CLASSES)}."
            )

        mask = FEATURE_MASKS[asset_class]
        encoded = [0.0] * self.TARGET_DIM

        for i, name in enumerate(FEATURE_NAMES):
            if mask[i] == 0.0:
                continue  # feature not active for this asset class
            val = features.get(name, 0.0)
            # Sanitize NaN/Inf
            if not math.isfinite(val):
                val = 0.0
            encoded[i] = val

        return encoded

    def encode_with_mask(
        self,
        features: Dict[str, float],
        asset_class: str,
    ) -> Tuple[List[float], Tuple[float, ...]]:
        """Encode features and return (encoded, mask) tuple.

        Args:
            features: Dict mapping feature names to float values.
            asset_class: Canonical asset class identifier.

        Returns:
            Tuple of (encoded_features, feature_mask).
        """
        encoded = self.encode(features, asset_class)
        mask = get_feature_mask(asset_class)
        return encoded, mask

    def get_mask(self, asset_class: str) -> Tuple[float, ...]:
        """Get pre-computed feature mask for asset class.

        Args:
            asset_class: Canonical asset class identifier.

        Returns:
            Tuple of 99 floats (1.0 or 0.0).
        """
        return get_feature_mask(asset_class)

    def count_active(self, asset_class: str) -> int:
        """Count active features for an asset class.

        Args:
            asset_class: Canonical asset class identifier.

        Returns:
            Number of active features (mask == 1.0).
        """
        mask = get_feature_mask(asset_class)
        return sum(1 for v in mask if v == 1.0)


# =============================================================================
# SECTION 8 -- FEATURE REGISTRY (main orchestrator)
# =============================================================================

class FeatureRegistry:
    """Asset-class-aware feature registry.

    Provides the central API for:
    - Querying which features are active per asset class
    - Encoding feature dicts to 99-dim vectors with masking
    - Retrieving feature metadata and catalogs
    - Applying feature masks to raw feature vectors

    FAS: FeatureRegistry.get_features(asset_class, features_dict)
    returns asset-appropriate feature set.

    This class does NOT compute features. Use feature_layer.FeatureLayer
    for computation, then pass results through this registry for masking.
    """

    def __init__(self) -> None:
        self._encoder = FeatureEncoder()

    def get_active_features(self, asset_class: str) -> List[str]:
        """Get list of active feature names for an asset class.

        Args:
            asset_class: Canonical asset class identifier.

        Returns:
            List of feature names where mask == 1.0, in canonical order.
        """
        mask = get_feature_mask(asset_class)
        return [
            FEATURE_NAMES[i]
            for i in range(FEATURE_VECTOR_SIZE)
            if mask[i] == 1.0
        ]

    def get_inactive_features(self, asset_class: str) -> List[str]:
        """Get list of inactive feature names for an asset class.

        Args:
            asset_class: Canonical asset class identifier.

        Returns:
            List of feature names where mask == 0.0, in canonical order.
        """
        mask = get_feature_mask(asset_class)
        return [
            FEATURE_NAMES[i]
            for i in range(FEATURE_VECTOR_SIZE)
            if mask[i] == 0.0
        ]

    def encode(
        self,
        features: Dict[str, float],
        asset_class: str,
    ) -> List[float]:
        """Encode feature dict to 99-dim list with asset-class masking.

        Args:
            features: Dict mapping feature names to float values.
            asset_class: Canonical asset class identifier.

        Returns:
            List of exactly 99 floats.
        """
        return self._encoder.encode(features, asset_class)

    def encode_with_mask(
        self,
        features: Dict[str, float],
        asset_class: str,
    ) -> Tuple[List[float], Tuple[float, ...]]:
        """Encode features and return (encoded, mask) tuple.

        Args:
            features: Dict mapping feature names to float values.
            asset_class: Canonical asset class identifier.

        Returns:
            Tuple of (encoded_features, feature_mask).
        """
        return self._encoder.encode_with_mask(features, asset_class)

    def apply_mask(
        self,
        features: List[float],
        asset_class: str,
    ) -> List[float]:
        """Apply asset-class mask to a raw 99-dim feature vector.

        Zeroes out features that are not active for the given asset class.

        Args:
            features: List of 99 floats (raw feature vector).
            asset_class: Canonical asset class identifier.

        Returns:
            List of 99 floats with inactive features zeroed.

        Raises:
            ValueError: If features length != 99 or asset_class unknown.
        """
        if len(features) != FEATURE_VECTOR_SIZE:
            raise ValueError(
                f"Feature vector must have {FEATURE_VECTOR_SIZE} elements, "
                f"got {len(features)}."
            )
        mask = get_feature_mask(asset_class)
        return [v * m for v, m in zip(features, mask)]

    def get_feature_index(self, feature_name: str) -> int:
        """Get the index of a feature by name.

        Args:
            feature_name: Canonical feature name.

        Returns:
            Integer index (0-98).

        Raises:
            ValueError: If feature_name is not recognized.
        """
        if feature_name not in _FEATURE_INDEX:
            raise ValueError(
                f"Unknown feature: '{feature_name}'. "
                f"Must be one of the 99 canonical features."
            )
        return _FEATURE_INDEX[feature_name]

    def get_feature_metadata(self, feature_name: str) -> FeatureMetadata:
        """Get metadata for a single feature.

        Args:
            feature_name: Canonical feature name.

        Returns:
            FeatureMetadata object.

        Raises:
            ValueError: If feature_name is not recognized.
        """
        idx = self.get_feature_index(feature_name)
        return FEATURE_CATALOG[idx]

    def get_category_features(self, category: str) -> List[str]:
        """Get all features in a category.

        Args:
            category: One of 'universal', 'asset_specific', 'cross_asset'.

        Returns:
            List of feature names.
        """
        valid = ("universal", "asset_specific", "cross_asset")
        if category not in valid:
            raise ValueError(
                f"Invalid category: '{category}'. Must be one of {valid}."
            )
        return [fm.name for fm in FEATURE_CATALOG if fm.category == category]

    def get_group_features(self, group: str) -> List[str]:
        """Get all features in a semantic group.

        Args:
            group: E.g. 'price_action', 'technical', 'on_chain', etc.

        Returns:
            List of feature names.
        """
        return [fm.name for fm in FEATURE_CATALOG if fm.group == group]

    def count_active(self, asset_class: str) -> int:
        """Count active features for an asset class."""
        return self._encoder.count_active(asset_class)

    def is_feature_active(self, feature_name: str, asset_class: str) -> bool:
        """Check if a feature is active for a given asset class.

        Args:
            feature_name: Canonical feature name.
            asset_class: Canonical asset class identifier.

        Returns:
            True if the feature is active (mask == 1.0).
        """
        idx = self.get_feature_index(feature_name)
        mask = get_feature_mask(asset_class)
        return mask[idx] == 1.0

    def get_asset_specific_catalog(self, asset_class: str) -> Tuple[str, ...]:
        """Get the asset-specific feature catalog.

        Args:
            asset_class: Canonical asset class identifier.

        Returns:
            Tuple of feature names in the 40-69 range that are active.

        Raises:
            ValueError: If asset_class is not recognized.
        """
        if asset_class not in ASSET_SPECIFIC_CATALOG:
            raise ValueError(
                f"Unknown asset_class: '{asset_class}'. "
                f"Must be one of {sorted(ASSET_SPECIFIC_CATALOG.keys())}."
            )
        return ASSET_SPECIFIC_CATALOG[asset_class]
