# =============================================================================
# jarvis/intelligence/global_regime.py -- Global Macro Regime Detector (Phase MA-3)
#
# Tier 1 of the 3-Tier Hierarchical Regime System.
# Detects global macro conditions across three sub-dimensions:
#   1. Monetary Policy (easing/neutral/tightening/emergency)
#   2. Risk Sentiment (risk_on/risk_off/transition/panic)
#   3. Liquidity (abundant/normal/tight/crisis)
#
# Outputs map to canonical GlobalRegimeState from jarvis/core/regime.py.
# PROHIBITED-08: No new regime Enum definitions here. Uses regime.py enums.
#
# =============================================================================
# FAS COMPLIANCE DECLARATION
# =============================================================================
#
# Dependency matrix:
#   global_regime.py -> jarvis.core.regime (GlobalRegimeState, MacroRegimeState)
#   global_regime.py -> (stdlib only otherwise)
#
# DETERMINISM GUARANTEES:
#   DET-01  No stochastic operations.
#   DET-02  All inputs passed explicitly. No module-level mutable reads.
#   DET-03  No side effects.
#   DET-04  All branches are deterministic functions of explicit inputs.
#   DET-05  Same inputs -> same outputs.
#   DET-06  Fixed literals not parameterizable.
#
# PROHIBITED ACTIONS CONFIRMED ABSENT:
#   PROHIBITED-01 through PROHIBITED-10: All confirmed absent.
#   PROHIBITED-08: No new Regime-Enum definitions (uses regime.py enums).
#   PROHIBITED-09: No string-based regime branching (Enum instances only).
#
# ASCII COMPLIANCE: All literals are 7-bit ASCII.
# =============================================================================

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from typing import Dict

from jarvis.core.regime import GlobalRegimeState


# =============================================================================
# SECTION 1 -- MONETARY POLICY STATES (string literals, not Enums per P-08)
# =============================================================================

# Internal detector states for monetary policy classification.
# These are metadata strings stored in sub_regime, NOT regime Enums.
MONETARY_STATES = ("easing", "neutral", "tightening", "emergency")

# Risk sentiment states (map to GlobalRegimeState)
RISK_SENTIMENT_STATES = ("risk_on", "risk_off", "transition", "panic")

# Liquidity states
LIQUIDITY_STATES = ("abundant", "normal", "tight", "crisis")


# =============================================================================
# SECTION 2 -- DETECTION THRESHOLDS (DET-06: fixed literals)
# =============================================================================

# Risk Sentiment thresholds (FAS: VIX-based classification)
VIX_PANIC_THRESHOLD: float = 40.0
VIX_RISK_OFF_THRESHOLD: float = 30.0
VIX_RISK_ON_THRESHOLD: float = 15.0
VIX_TERM_PANIC_THRESHOLD: float = -0.1    # negative = backwardation = fear
VIX_TERM_RISK_ON_THRESHOLD: float = 0.05  # positive = contango = calm

# Liquidity thresholds
REPO_RATE_CRISIS_THRESHOLD: float = 2.0    # bps above normal
REPO_RATE_TIGHT_THRESHOLD: float = 0.5
TED_SPREAD_CRISIS_THRESHOLD: float = 1.0   # percentage points
TED_SPREAD_TIGHT_THRESHOLD: float = 0.35

# Monetary policy thresholds
RATE_EMERGENCY_THRESHOLD: float = 0.25  # near-zero emergency cuts
RATE_EASING_DIRECTION: str = "cutting"
RATE_TIGHTENING_DIRECTION: str = "hiking"


# =============================================================================
# SECTION 3 -- RESULT DATACLASSES
# =============================================================================

@dataclass(frozen=True)
class MonetaryPolicyResult:
    """Monetary policy sub-regime detection result.

    Attributes:
        state: One of MONETARY_STATES.
        fed_rate: Federal funds rate (explicit input).
        fed_direction: 'cutting', 'holding', or 'hiking'.
        confidence: Detection confidence [0.0, 1.0].
    """
    state: str
    fed_rate: float
    fed_direction: str
    confidence: float


@dataclass(frozen=True)
class RiskSentimentResult:
    """Risk sentiment sub-regime detection result.

    Attributes:
        state: One of RISK_SENTIMENT_STATES.
        vix_level: VIX index level (explicit input).
        vix_term_structure: VIX term structure slope.
        credit_spread_bps: Credit spread in basis points.
        confidence: Detection confidence [0.0, 1.0].
    """
    state: str
    vix_level: float
    vix_term_structure: float
    credit_spread_bps: float
    confidence: float


@dataclass(frozen=True)
class LiquidityResult:
    """Liquidity sub-regime detection result.

    Attributes:
        state: One of LIQUIDITY_STATES.
        repo_rate_spread: Repo rate spread above normal (bps).
        ted_spread: TED spread (LIBOR-OIS) in percentage points.
        confidence: Detection confidence [0.0, 1.0].
    """
    state: str
    repo_rate_spread: float
    ted_spread: float
    confidence: float


@dataclass(frozen=True)
class GlobalMacroResult:
    """Complete Tier 1 global macro regime detection result.

    Attributes:
        monetary_policy: Monetary policy sub-result.
        risk_sentiment: Risk sentiment sub-result.
        liquidity: Liquidity sub-result.
        global_regime_state: Canonical GlobalRegimeState for downstream.
        confidence: Overall detection confidence [0.0, 1.0].
        result_hash: SHA-256[:16] of content for determinism verification.
    """
    monetary_policy: MonetaryPolicyResult
    risk_sentiment: RiskSentimentResult
    liquidity: LiquidityResult
    global_regime_state: GlobalRegimeState
    confidence: float
    result_hash: str


# =============================================================================
# SECTION 4 -- RISK SENTIMENT MAPPING TO CANONICAL ENUM
# =============================================================================

_RISK_SENTIMENT_TO_GLOBAL: Dict[str, GlobalRegimeState] = {
    "risk_on":    GlobalRegimeState.RISK_ON,
    "risk_off":   GlobalRegimeState.RISK_OFF,
    "transition": GlobalRegimeState.TRANSITION,
    "panic":      GlobalRegimeState.CRISIS,
}


# =============================================================================
# SECTION 5 -- GLOBAL MACRO DETECTOR
# =============================================================================

class GlobalMacroDetector:
    """Tier 1: Global macro regime detector.

    Detects three sub-dimensions of the global macro environment:
    1. Monetary Policy (central bank stance)
    2. Risk Sentiment (VIX-based market fear/greed)
    3. Liquidity (system-wide funding conditions)

    All inputs are explicit parameters (DET-02).
    No internal state is retained between calls (DET-03, PROHIBITED-05).
    """

    def detect(
        self,
        *,
        vix_level: float,
        vix_term_structure: float,
        credit_spread_bps: float,
        fed_rate: float,
        fed_direction: str,
        repo_rate_spread: float,
        ted_spread: float,
    ) -> GlobalMacroResult:
        """Detect global macro regime from explicit inputs.

        Args:
            vix_level: Current VIX index level.
            vix_term_structure: VIX term structure slope.
                Positive = contango (calm), negative = backwardation (fear).
            credit_spread_bps: Credit spread in basis points.
            fed_rate: Federal funds rate.
            fed_direction: 'cutting', 'holding', or 'hiking'.
            repo_rate_spread: Repo rate spread above normal (bps).
            ted_spread: TED spread (LIBOR-OIS) in percentage points.

        Returns:
            GlobalMacroResult with all sub-results and canonical regime state.
        """
        monetary = self._detect_monetary_policy(fed_rate, fed_direction)
        risk_sentiment = self._detect_risk_sentiment(
            vix_level, vix_term_structure, credit_spread_bps
        )
        liquidity = self._detect_liquidity(repo_rate_spread, ted_spread)

        # Map to canonical GlobalRegimeState
        global_state = self._determine_global_state(
            monetary, risk_sentiment, liquidity
        )

        # Overall confidence = weighted average of sub-confidences
        confidence = (
            0.2 * monetary.confidence
            + 0.5 * risk_sentiment.confidence
            + 0.3 * liquidity.confidence
        )

        # Compute deterministic hash
        payload = {
            "monetary_state": monetary.state,
            "risk_state": risk_sentiment.state,
            "liquidity_state": liquidity.state,
            "global_regime": global_state.value,
            "confidence": round(confidence, 8),
        }
        result_hash = hashlib.sha256(
            json.dumps(payload, sort_keys=True).encode("utf-8")
        ).hexdigest()[:16]

        return GlobalMacroResult(
            monetary_policy=monetary,
            risk_sentiment=risk_sentiment,
            liquidity=liquidity,
            global_regime_state=global_state,
            confidence=confidence,
            result_hash=result_hash,
        )

    def _detect_monetary_policy(
        self,
        fed_rate: float,
        fed_direction: str,
    ) -> MonetaryPolicyResult:
        """Classify monetary policy regime.

        FAS states: easing, neutral, tightening, emergency.
        """
        if fed_rate <= RATE_EMERGENCY_THRESHOLD and fed_direction == RATE_EASING_DIRECTION:
            state = "emergency"
            confidence = 0.9
        elif fed_direction == RATE_EASING_DIRECTION:
            state = "easing"
            confidence = 0.8
        elif fed_direction == RATE_TIGHTENING_DIRECTION:
            state = "tightening"
            confidence = 0.8
        else:
            state = "neutral"
            confidence = 0.7

        return MonetaryPolicyResult(
            state=state,
            fed_rate=fed_rate,
            fed_direction=fed_direction,
            confidence=confidence,
        )

    def _detect_risk_sentiment(
        self,
        vix_level: float,
        vix_term_structure: float,
        credit_spread_bps: float,
    ) -> RiskSentimentResult:
        """Classify risk sentiment regime.

        FAS (lines 17614-17621):
        - vix > 40 AND vix_term < -0.1 -> panic
        - vix > 30 -> risk_off
        - vix < 15 AND vix_term > 0.05 -> risk_on
        - else -> transition
        """
        if vix_level > VIX_PANIC_THRESHOLD and vix_term_structure < VIX_TERM_PANIC_THRESHOLD:
            state = "panic"
            confidence = 0.95
        elif vix_level > VIX_RISK_OFF_THRESHOLD:
            state = "risk_off"
            confidence = 0.85
        elif vix_level < VIX_RISK_ON_THRESHOLD and vix_term_structure > VIX_TERM_RISK_ON_THRESHOLD:
            state = "risk_on"
            confidence = 0.8
        else:
            state = "transition"
            confidence = 0.6

        return RiskSentimentResult(
            state=state,
            vix_level=vix_level,
            vix_term_structure=vix_term_structure,
            credit_spread_bps=credit_spread_bps,
            confidence=confidence,
        )

    def _detect_liquidity(
        self,
        repo_rate_spread: float,
        ted_spread: float,
    ) -> LiquidityResult:
        """Classify liquidity regime.

        FAS states: abundant, normal, tight, crisis.
        """
        if (repo_rate_spread > REPO_RATE_CRISIS_THRESHOLD
                or ted_spread > TED_SPREAD_CRISIS_THRESHOLD):
            state = "crisis"
            confidence = 0.9
        elif (repo_rate_spread > REPO_RATE_TIGHT_THRESHOLD
              or ted_spread > TED_SPREAD_TIGHT_THRESHOLD):
            state = "tight"
            confidence = 0.75
        elif repo_rate_spread < 0.0:
            state = "abundant"
            confidence = 0.7
        else:
            state = "normal"
            confidence = 0.7

        return LiquidityResult(
            state=state,
            repo_rate_spread=repo_rate_spread,
            ted_spread=ted_spread,
            confidence=confidence,
        )

    def _determine_global_state(
        self,
        monetary: MonetaryPolicyResult,
        risk_sentiment: RiskSentimentResult,
        liquidity: LiquidityResult,
    ) -> GlobalRegimeState:
        """Map sub-regime results to canonical GlobalRegimeState.

        Priority order (FAS Crisis Priority Order):
        1. Panic risk sentiment -> CRISIS
        2. Liquidity crisis -> CRISIS
        3. Emergency monetary + crisis liquidity -> CRISIS
        4. Risk-off sentiment -> RISK_OFF
        5. Risk-on sentiment -> RISK_ON
        6. Otherwise -> TRANSITION
        """
        # Priority 1: Panic -> CRISIS
        if risk_sentiment.state == "panic":
            return GlobalRegimeState.CRISIS

        # Priority 2: Liquidity crisis -> CRISIS
        if liquidity.state == "crisis":
            return GlobalRegimeState.CRISIS

        # Priority 3: Emergency + tight/crisis liquidity -> CRISIS
        if monetary.state == "emergency" and liquidity.state in ("tight", "crisis"):
            return GlobalRegimeState.CRISIS

        # Standard mapping from risk sentiment
        return _RISK_SENTIMENT_TO_GLOBAL.get(
            risk_sentiment.state, GlobalRegimeState.TRANSITION
        )
