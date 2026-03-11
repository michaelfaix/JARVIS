# =============================================================================
# jarvis/intelligence/asset_regimes.py -- Asset-Class Regime Detectors (Phase MA-3)
#
# Tier 2 of the 3-Tier Hierarchical Regime System.
# Per-asset-class regime detection conditioned on Tier 1 (GlobalMacroResult).
#
# Detectors:
#   CryptoRegimeDetector   (5 internal states -> AssetRegimeState)
#   ForexRegimeDetector    (4 internal states -> AssetRegimeState)
#   IndicesRegimeDetector  (5 internal states -> AssetRegimeState)
#   CommoditiesRegimeDetector (4 internal states -> AssetRegimeState)
#
# PROHIBITED-08: No new Regime-Enum definitions here.
# Internal states are string literals stored in sub_regime metadata.
# Canonical output uses AssetRegimeState from regime.py.
#
# =============================================================================
# FAS COMPLIANCE DECLARATION
# =============================================================================
#
# Dependency matrix:
#   asset_regimes.py -> jarvis.core.regime (AssetRegimeState)
#   asset_regimes.py -> jarvis.intelligence.global_regime (GlobalMacroResult)
#   asset_regimes.py -> (stdlib only otherwise)
#
# DETERMINISM GUARANTEES:
#   DET-01 through DET-07: All enforced. Pure deterministic scoring.
#
# PROHIBITED ACTIONS CONFIRMED ABSENT:
#   PROHIBITED-01 through PROHIBITED-10: All confirmed absent.
#   PROHIBITED-02: No file I/O (no HMM weight loading).
#   PROHIBITED-08: No new Regime-Enum definitions.
#   PROHIBITED-09: No string-based regime branching (Enum output only).
#
# ASCII COMPLIANCE: All literals are 7-bit ASCII.
# =============================================================================

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, Tuple

from jarvis.core.regime import AssetRegimeState
from jarvis.intelligence.global_regime import GlobalMacroResult


# =============================================================================
# SECTION 1 -- INTERNAL STATE DEFINITIONS (metadata strings, not Enums)
# =============================================================================

# FAS Tier 2: CryptoRegimeDetector (5 states)
CRYPTO_STATES: Tuple[str, ...] = (
    "leverage_mania",
    "retail_fomo",
    "institutional",
    "deleveraging",
    "capitulation",
)

# FAS Tier 2: ForexRegimeDetector (4 states)
FOREX_STATES: Tuple[str, ...] = (
    "carry_trade",
    "trend_following",
    "range_bound",
    "risk_off_flight",
)

# FAS Tier 2: IndicesRegimeDetector (5 states)
INDICES_STATES: Tuple[str, ...] = (
    "bull_market",
    "bear_market",
    "sector_rotation",
    "defensive",
    "panic",
)

# FAS Tier 2: CommoditiesRegimeDetector (4 states)
COMMODITIES_STATES: Tuple[str, ...] = (
    "contango",
    "backwardation",
    "supply_shock",
    "demand_shock",
)


# =============================================================================
# SECTION 2 -- STATE-TO-CANONICAL MAPPINGS
# =============================================================================

# Maps internal detector states to canonical AssetRegimeState.
# sub_regime string stored separately for metadata.

_CRYPTO_TO_CANONICAL: Dict[str, AssetRegimeState] = {
    "leverage_mania":  AssetRegimeState.TRENDING_UP,
    "retail_fomo":     AssetRegimeState.TRENDING_UP,
    "institutional":   AssetRegimeState.RANGING_TIGHT,
    "deleveraging":    AssetRegimeState.TRENDING_DOWN,
    "capitulation":    AssetRegimeState.SHOCK,
}

_FOREX_TO_CANONICAL: Dict[str, AssetRegimeState] = {
    "carry_trade":      AssetRegimeState.RANGING_TIGHT,
    "trend_following":  AssetRegimeState.TRENDING_UP,
    "range_bound":      AssetRegimeState.RANGING_TIGHT,
    "risk_off_flight":  AssetRegimeState.HIGH_VOLATILITY,
}

_INDICES_TO_CANONICAL: Dict[str, AssetRegimeState] = {
    "bull_market":       AssetRegimeState.TRENDING_UP,
    "bear_market":       AssetRegimeState.TRENDING_DOWN,
    "sector_rotation":   AssetRegimeState.RANGING_WIDE,
    "defensive":         AssetRegimeState.RANGING_TIGHT,
    "panic":             AssetRegimeState.SHOCK,
}

_COMMODITIES_TO_CANONICAL: Dict[str, AssetRegimeState] = {
    "contango":         AssetRegimeState.RANGING_TIGHT,
    "backwardation":    AssetRegimeState.TRENDING_UP,
    "supply_shock":     AssetRegimeState.SHOCK,
    "demand_shock":     AssetRegimeState.HIGH_VOLATILITY,
}


# =============================================================================
# SECTION 3 -- DETECTION THRESHOLDS (DET-06: fixed literals)
# =============================================================================

# Crypto thresholds
CRYPTO_HIGH_FUNDING_RATE: float = 0.001       # 0.1% per 8h = high leverage
CRYPTO_NEGATIVE_FUNDING: float = -0.0005      # negative = shorts dominate
CRYPTO_EXTREME_LIQUIDATION: float = 0.8       # normalized liquidation score
CRYPTO_HIGH_SOCIAL_SENTIMENT: float = 0.7     # retail FOMO indicator
CRYPTO_LOW_SOCIAL_SENTIMENT: float = 0.3      # despair indicator

# Forex thresholds
FOREX_HIGH_RATE_DIFF: float = 0.02            # 2% rate differential
FOREX_CB_PROXIMITY_DAYS: float = 3.0          # days until CB meeting
FOREX_TREND_THRESHOLD: float = 0.6            # trend strength score

# Indices thresholds
INDICES_VIX_PANIC: float = 40.0
INDICES_VIX_DEFENSIVE: float = 25.0
INDICES_VIX_BULL: float = 18.0
INDICES_BREADTH_BULL: float = 0.6             # market breadth score
INDICES_BREADTH_BEAR: float = 0.3

# Commodities thresholds
COMMODITIES_CONTANGO_THRESHOLD: float = 0.02   # 2% contango
COMMODITIES_BACKWARDATION_THRESHOLD: float = -0.02
COMMODITIES_SHOCK_VOL: float = 0.8             # vol score for shock

# Global conditioning multipliers (FAS: conditioning on global regime)
RISK_OFF_SUPPRESS_FACTOR: float = 0.2          # suppress bullish in risk-off
RISK_OFF_BOOST_FACTOR: float = 2.0             # boost bearish in risk-off
PANIC_CAPITULATION_FORCE: float = 0.8          # force capitulation in panic
TIGHTENING_TREND_BOOST: float = 1.5            # boost trend in tightening


# =============================================================================
# SECTION 4 -- ASSET REGIME RESULT
# =============================================================================

@dataclass(frozen=True)
class AssetRegimeResult:
    """Result from an asset-class-specific regime detector.

    Attributes:
        asset_class: Canonical asset class identifier string.
        internal_state: Detector-internal state string (for sub_regime metadata).
        canonical_state: Mapped AssetRegimeState for downstream consumption.
        probabilities: State probability distribution (internal states).
        confidence: Detection confidence [0.0, 1.0].
        conditioned_on_global: True if global regime conditioning was applied.
    """
    asset_class: str
    internal_state: str
    canonical_state: AssetRegimeState
    probabilities: Dict[str, float]
    confidence: float
    conditioned_on_global: bool


# =============================================================================
# SECTION 5 -- PROBABILITY HELPERS
# =============================================================================

def _normalize_probs(probs: Dict[str, float]) -> Dict[str, float]:
    """Normalize probability dict to sum to 1.0. Pure function."""
    total = sum(probs.values())
    if total <= 0:
        # Uniform fallback
        n = len(probs)
        return {k: 1.0 / n for k in probs}
    return {k: v / total for k, v in probs.items()}


def _max_state(probs: Dict[str, float]) -> str:
    """Return state with highest probability. Deterministic tie-break by key."""
    return max(probs.keys(), key=lambda k: (probs[k], k))


# =============================================================================
# SECTION 6 -- CRYPTO REGIME DETECTOR
# =============================================================================

class CryptoRegimeDetector:
    """Crypto-specific regime detector (5 states).

    FAS: Uses funding_rate, open_interest_change, liquidation_score,
    social_sentiment. Conditioned on global regime.
    """

    def detect(
        self,
        *,
        funding_rate: float,
        open_interest_change: float,
        liquidation_score: float,
        social_sentiment: float,
        global_macro: GlobalMacroResult,
    ) -> AssetRegimeResult:
        """Detect crypto regime from explicit inputs.

        Args:
            funding_rate: Funding rate (positive = longs pay shorts).
            open_interest_change: Change in open interest (positive = rising).
            liquidation_score: Normalized liquidation intensity [0, 1].
            social_sentiment: Social media sentiment score [0, 1].
            global_macro: Tier 1 global macro result.

        Returns:
            AssetRegimeResult with internal state and canonical mapping.
        """
        # Base scoring
        probs: Dict[str, float] = {s: 0.1 for s in CRYPTO_STATES}

        # leverage_mania: high funding + rising OI + low liquidations
        if funding_rate > CRYPTO_HIGH_FUNDING_RATE and open_interest_change > 0:
            probs["leverage_mania"] += 0.5
        if funding_rate > CRYPTO_HIGH_FUNDING_RATE:
            probs["leverage_mania"] += 0.2

        # retail_fomo: high social sentiment + rising prices
        if social_sentiment > CRYPTO_HIGH_SOCIAL_SENTIMENT:
            probs["retail_fomo"] += 0.4
        if open_interest_change > 0 and social_sentiment > 0.5:
            probs["retail_fomo"] += 0.2

        # institutional: low funding + stable OI
        if abs(funding_rate) < CRYPTO_HIGH_FUNDING_RATE and abs(open_interest_change) < 0.1:
            probs["institutional"] += 0.5

        # deleveraging: falling OI + negative funding + high liquidations
        if open_interest_change < 0 and funding_rate < 0:
            probs["deleveraging"] += 0.4
        if liquidation_score > 0.4:
            probs["deleveraging"] += 0.3

        # capitulation: extreme liquidations + despair
        if liquidation_score > CRYPTO_EXTREME_LIQUIDATION:
            probs["capitulation"] += 0.6
        if social_sentiment < CRYPTO_LOW_SOCIAL_SENTIMENT and liquidation_score > 0.5:
            probs["capitulation"] += 0.3

        # CRITICAL: Condition on global regime (FAS lines 17669-17681)
        conditioned = False
        risk_state = global_macro.risk_sentiment.state

        if risk_state == "risk_off":
            probs["leverage_mania"] *= RISK_OFF_SUPPRESS_FACTOR
            if funding_rate < 0 and open_interest_change < 0:
                probs["deleveraging"] *= RISK_OFF_BOOST_FACTOR
            conditioned = True

        if risk_state == "panic":
            if liquidation_score > CRYPTO_EXTREME_LIQUIDATION:
                probs["capitulation"] = PANIC_CAPITULATION_FORCE
                # Suppress competing states when capitulation is forced
                probs["deleveraging"] *= 0.3
                probs["leverage_mania"] *= 0.1
            conditioned = True

        probs = _normalize_probs(probs)
        state = _max_state(probs)

        return AssetRegimeResult(
            asset_class="crypto",
            internal_state=state,
            canonical_state=_CRYPTO_TO_CANONICAL[state],
            probabilities=probs,
            confidence=probs[state],
            conditioned_on_global=conditioned,
        )


# =============================================================================
# SECTION 7 -- FOREX REGIME DETECTOR
# =============================================================================

class ForexRegimeDetector:
    """Forex-specific regime detector (4 states).

    FAS: Uses rate_differential, carry_signal, cb_meeting_proximity,
    trend_strength. Conditioned on global regime.
    """

    def detect(
        self,
        *,
        rate_differential: float,
        carry_signal: float,
        cb_meeting_proximity_days: float,
        trend_strength: float,
        global_macro: GlobalMacroResult,
    ) -> AssetRegimeResult:
        """Detect forex regime from explicit inputs.

        Args:
            rate_differential: Interest rate differential between currencies.
            carry_signal: Carry trade attractiveness score.
            cb_meeting_proximity_days: Days until next central bank meeting.
            trend_strength: Directional trend strength [0, 1].
            global_macro: Tier 1 global macro result.

        Returns:
            AssetRegimeResult with internal state and canonical mapping.
        """
        probs: Dict[str, float] = {s: 0.1 for s in FOREX_STATES}

        # carry_trade: high rate differential + low vol
        if rate_differential > FOREX_HIGH_RATE_DIFF and carry_signal > 0:
            probs["carry_trade"] += 0.5
        if carry_signal > 0.5:
            probs["carry_trade"] += 0.2

        # trend_following: strong directional move
        if trend_strength > FOREX_TREND_THRESHOLD:
            probs["trend_following"] += 0.5
        if trend_strength > 0.4:
            probs["trend_following"] += 0.2

        # range_bound: low trend strength
        if trend_strength < 0.3:
            probs["range_bound"] += 0.4
        if abs(rate_differential) < 0.01:
            probs["range_bound"] += 0.2

        # risk_off_flight: flight to safety
        if carry_signal < -0.3:
            probs["risk_off_flight"] += 0.4

        # CRITICAL: Condition on global regime (FAS lines 17729-17751)
        conditioned = False
        risk_state = global_macro.risk_sentiment.state

        if risk_state in ("risk_off", "panic"):
            probs["risk_off_flight"] = 0.7
            probs["carry_trade"] = 0.05
            conditioned = True

        monetary_state = global_macro.monetary_policy.state
        if monetary_state == "tightening":
            probs["trend_following"] *= TIGHTENING_TREND_BOOST
            conditioned = True

        # CB meeting proximity suppresses carry
        if cb_meeting_proximity_days < FOREX_CB_PROXIMITY_DAYS:
            probs["carry_trade"] *= 0.5
            probs["range_bound"] *= 1.5
            conditioned = True

        probs = _normalize_probs(probs)
        state = _max_state(probs)

        return AssetRegimeResult(
            asset_class="forex",
            internal_state=state,
            canonical_state=_FOREX_TO_CANONICAL[state],
            probabilities=probs,
            confidence=probs[state],
            conditioned_on_global=conditioned,
        )


# =============================================================================
# SECTION 8 -- INDICES REGIME DETECTOR
# =============================================================================

class IndicesRegimeDetector:
    """Indices-specific regime detector (5 states).

    FAS: Uses vix_level, market_breadth, credit_spread, trend_strength.
    Conditioned on global regime.
    """

    def detect(
        self,
        *,
        vix_level: float,
        market_breadth: float,
        credit_spread_bps: float,
        trend_strength: float,
        global_macro: GlobalMacroResult,
    ) -> AssetRegimeResult:
        """Detect indices regime from explicit inputs.

        Args:
            vix_level: VIX index level.
            market_breadth: Market breadth score [0, 1].
            credit_spread_bps: Credit spread in basis points.
            trend_strength: Directional trend strength [-1, 1].
                Positive = up, negative = down.
            global_macro: Tier 1 global macro result.

        Returns:
            AssetRegimeResult with internal state and canonical mapping.
        """
        probs: Dict[str, float] = {s: 0.1 for s in INDICES_STATES}

        # panic: extreme VIX
        if vix_level > INDICES_VIX_PANIC:
            probs["panic"] += 0.7
        elif vix_level > INDICES_VIX_DEFENSIVE:
            probs["panic"] += 0.2

        # defensive: elevated VIX + narrow breadth
        if INDICES_VIX_BULL < vix_level <= INDICES_VIX_DEFENSIVE:
            probs["defensive"] += 0.4
        if market_breadth < INDICES_BREADTH_BEAR:
            probs["defensive"] += 0.3

        # bull_market: low VIX + broad breadth + positive trend
        if vix_level < INDICES_VIX_BULL and market_breadth > INDICES_BREADTH_BULL:
            probs["bull_market"] += 0.5
        if trend_strength > 0.3:
            probs["bull_market"] += 0.3

        # bear_market: negative trend + narrowing breadth
        if trend_strength < -0.3:
            probs["bear_market"] += 0.5
        if market_breadth < INDICES_BREADTH_BEAR and trend_strength < 0:
            probs["bear_market"] += 0.3

        # sector_rotation: mixed signals
        if 0.3 <= market_breadth <= 0.6 and abs(trend_strength) < 0.3:
            probs["sector_rotation"] += 0.4

        # Condition on global regime
        conditioned = False
        risk_state = global_macro.risk_sentiment.state

        if risk_state == "panic":
            probs["panic"] = 0.8
            probs["bull_market"] *= 0.1
            conditioned = True
        elif risk_state == "risk_off":
            probs["defensive"] *= 2.0
            probs["bull_market"] *= 0.3
            conditioned = True

        probs = _normalize_probs(probs)
        state = _max_state(probs)

        return AssetRegimeResult(
            asset_class="indices",
            internal_state=state,
            canonical_state=_INDICES_TO_CANONICAL[state],
            probabilities=probs,
            confidence=probs[state],
            conditioned_on_global=conditioned,
        )


# =============================================================================
# SECTION 9 -- COMMODITIES REGIME DETECTOR
# =============================================================================

class CommoditiesRegimeDetector:
    """Commodities-specific regime detector (4 states).

    FAS: Uses contango_backwardation, inventory_change, volatility_score.
    Conditioned on global regime.
    """

    def detect(
        self,
        *,
        contango_backwardation: float,
        inventory_change: float,
        volatility_score: float,
        global_macro: GlobalMacroResult,
    ) -> AssetRegimeResult:
        """Detect commodities regime from explicit inputs.

        Args:
            contango_backwardation: Futures curve slope.
                Positive = contango, negative = backwardation.
            inventory_change: Normalized inventory change [-1, 1].
            volatility_score: Normalized volatility [0, 1].
            global_macro: Tier 1 global macro result.

        Returns:
            AssetRegimeResult with internal state and canonical mapping.
        """
        probs: Dict[str, float] = {s: 0.1 for s in COMMODITIES_STATES}

        # contango: positive curve slope, stable inventories
        if contango_backwardation > COMMODITIES_CONTANGO_THRESHOLD:
            probs["contango"] += 0.5
        if inventory_change > 0 and contango_backwardation > 0:
            probs["contango"] += 0.2

        # backwardation: negative curve slope, depleting inventories
        if contango_backwardation < COMMODITIES_BACKWARDATION_THRESHOLD:
            probs["backwardation"] += 0.5
        if inventory_change < -0.3:
            probs["backwardation"] += 0.3

        # supply_shock: extreme vol + depleting inventories
        if volatility_score > COMMODITIES_SHOCK_VOL and inventory_change < -0.5:
            probs["supply_shock"] += 0.6
        elif volatility_score > COMMODITIES_SHOCK_VOL:
            probs["supply_shock"] += 0.3

        # demand_shock: high vol + rising inventories (demand collapse)
        if volatility_score > 0.5 and inventory_change > 0.3:
            probs["demand_shock"] += 0.5

        # Condition on global regime
        conditioned = False
        risk_state = global_macro.risk_sentiment.state

        if risk_state == "panic":
            probs["supply_shock"] *= 1.5
            probs["demand_shock"] *= 1.5
            conditioned = True
        elif risk_state == "risk_off":
            probs["demand_shock"] *= 1.3
            conditioned = True

        probs = _normalize_probs(probs)
        state = _max_state(probs)

        return AssetRegimeResult(
            asset_class="commodities",
            internal_state=state,
            canonical_state=_COMMODITIES_TO_CANONICAL[state],
            probabilities=probs,
            confidence=probs[state],
            conditioned_on_global=conditioned,
        )
