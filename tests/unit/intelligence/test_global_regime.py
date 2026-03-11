# =============================================================================
# tests/unit/intelligence/test_global_regime.py -- Global Macro Detector Tests
#
# Comprehensive tests for jarvis/intelligence/global_regime.py (Phase MA-3).
# Covers: MonetaryPolicy, RiskSentiment, Liquidity detection, GlobalMacroResult,
#         threshold boundaries, global state mapping, determinism, immutability.
# =============================================================================

import pytest

from jarvis.core.regime import GlobalRegimeState
from jarvis.intelligence.global_regime import (
    # Constants
    MONETARY_STATES,
    RISK_SENTIMENT_STATES,
    LIQUIDITY_STATES,
    VIX_PANIC_THRESHOLD,
    VIX_RISK_OFF_THRESHOLD,
    VIX_RISK_ON_THRESHOLD,
    VIX_TERM_PANIC_THRESHOLD,
    VIX_TERM_RISK_ON_THRESHOLD,
    REPO_RATE_CRISIS_THRESHOLD,
    TED_SPREAD_CRISIS_THRESHOLD,
    RATE_EMERGENCY_THRESHOLD,
    # Results
    MonetaryPolicyResult,
    RiskSentimentResult,
    LiquidityResult,
    GlobalMacroResult,
    # Detector
    GlobalMacroDetector,
)


# ---------------------------------------------------------------------------
# SHARED FIXTURES
# ---------------------------------------------------------------------------

CALM_KWARGS = dict(
    vix_level=12.0,
    vix_term_structure=0.1,
    credit_spread_bps=100.0,
    fed_rate=5.0,
    fed_direction="holding",
    repo_rate_spread=0.1,
    ted_spread=0.1,
)


def _detect(**overrides):
    kwargs = {**CALM_KWARGS, **overrides}
    return GlobalMacroDetector().detect(**kwargs)


# ---------------------------------------------------------------------------
# CONSTANTS (DET-06)
# ---------------------------------------------------------------------------

class TestConstants:
    def test_monetary_states(self):
        assert MONETARY_STATES == ("easing", "neutral", "tightening", "emergency")

    def test_risk_sentiment_states(self):
        assert RISK_SENTIMENT_STATES == ("risk_on", "risk_off", "transition", "panic")

    def test_liquidity_states(self):
        assert LIQUIDITY_STATES == ("abundant", "normal", "tight", "crisis")

    def test_vix_thresholds(self):
        assert VIX_PANIC_THRESHOLD == 40.0
        assert VIX_RISK_OFF_THRESHOLD == 30.0
        assert VIX_RISK_ON_THRESHOLD == 15.0

    def test_vix_term_thresholds(self):
        assert VIX_TERM_PANIC_THRESHOLD == -0.1
        assert VIX_TERM_RISK_ON_THRESHOLD == 0.05


# ---------------------------------------------------------------------------
# MONETARY POLICY DETECTION
# ---------------------------------------------------------------------------

class TestMonetaryPolicy:
    def test_neutral(self):
        r = _detect(fed_direction="holding")
        assert r.monetary_policy.state == "neutral"

    def test_easing(self):
        r = _detect(fed_direction="cutting", fed_rate=3.0)
        assert r.monetary_policy.state == "easing"

    def test_tightening(self):
        r = _detect(fed_direction="hiking")
        assert r.monetary_policy.state == "tightening"

    def test_emergency(self):
        r = _detect(fed_direction="cutting", fed_rate=0.1)
        assert r.monetary_policy.state == "emergency"

    def test_emergency_boundary(self):
        r = _detect(fed_direction="cutting", fed_rate=RATE_EMERGENCY_THRESHOLD)
        assert r.monetary_policy.state == "emergency"

    def test_easing_above_emergency(self):
        r = _detect(fed_direction="cutting", fed_rate=RATE_EMERGENCY_THRESHOLD + 0.01)
        assert r.monetary_policy.state == "easing"

    def test_fed_rate_stored(self):
        r = _detect(fed_rate=3.5)
        assert r.monetary_policy.fed_rate == 3.5

    def test_fed_direction_stored(self):
        r = _detect(fed_direction="hiking")
        assert r.monetary_policy.fed_direction == "hiking"

    def test_confidence_range(self):
        r = _detect()
        assert 0.0 <= r.monetary_policy.confidence <= 1.0

    def test_result_frozen(self):
        r = _detect()
        with pytest.raises(AttributeError):
            r.monetary_policy.state = "panic"


# ---------------------------------------------------------------------------
# RISK SENTIMENT DETECTION
# ---------------------------------------------------------------------------

class TestRiskSentiment:
    def test_risk_on(self):
        r = _detect(vix_level=12.0, vix_term_structure=0.1)
        assert r.risk_sentiment.state == "risk_on"

    def test_risk_off(self):
        r = _detect(vix_level=32.0, vix_term_structure=0.0)
        assert r.risk_sentiment.state == "risk_off"

    def test_transition(self):
        r = _detect(vix_level=20.0, vix_term_structure=0.02)
        assert r.risk_sentiment.state == "transition"

    def test_panic(self):
        r = _detect(vix_level=45.0, vix_term_structure=-0.2)
        assert r.risk_sentiment.state == "panic"

    def test_panic_boundary_vix(self):
        """VIX > 40 AND term < -0.1 -> panic."""
        r = _detect(vix_level=40.01, vix_term_structure=-0.11)
        assert r.risk_sentiment.state == "panic"

    def test_not_panic_if_term_positive(self):
        """VIX > 40 but term > -0.1 -> risk_off (not panic)."""
        r = _detect(vix_level=45.0, vix_term_structure=0.0)
        assert r.risk_sentiment.state == "risk_off"

    def test_risk_on_boundary(self):
        """VIX < 15 AND term > 0.05 -> risk_on."""
        r = _detect(vix_level=14.99, vix_term_structure=0.051)
        assert r.risk_sentiment.state == "risk_on"

    def test_not_risk_on_if_vix_high(self):
        """VIX >= 15 -> not risk_on."""
        r = _detect(vix_level=15.0, vix_term_structure=0.1)
        assert r.risk_sentiment.state == "transition"

    def test_vix_stored(self):
        r = _detect(vix_level=25.0)
        assert r.risk_sentiment.vix_level == 25.0

    def test_credit_spread_stored(self):
        r = _detect(credit_spread_bps=200.0)
        assert r.risk_sentiment.credit_spread_bps == 200.0

    def test_confidence_range(self):
        r = _detect()
        assert 0.0 <= r.risk_sentiment.confidence <= 1.0


# ---------------------------------------------------------------------------
# LIQUIDITY DETECTION
# ---------------------------------------------------------------------------

class TestLiquidity:
    def test_normal(self):
        r = _detect(repo_rate_spread=0.1, ted_spread=0.1)
        assert r.liquidity.state == "normal"

    def test_abundant(self):
        r = _detect(repo_rate_spread=-0.5, ted_spread=0.1)
        assert r.liquidity.state == "abundant"

    def test_tight(self):
        r = _detect(repo_rate_spread=0.6, ted_spread=0.1)
        assert r.liquidity.state == "tight"

    def test_crisis_by_repo(self):
        r = _detect(repo_rate_spread=3.0, ted_spread=0.1)
        assert r.liquidity.state == "crisis"

    def test_crisis_by_ted(self):
        r = _detect(repo_rate_spread=0.1, ted_spread=1.5)
        assert r.liquidity.state == "crisis"

    def test_crisis_boundary_repo(self):
        r = _detect(repo_rate_spread=REPO_RATE_CRISIS_THRESHOLD + 0.01, ted_spread=0.0)
        assert r.liquidity.state == "crisis"

    def test_tight_boundary_repo(self):
        r = _detect(repo_rate_spread=0.51, ted_spread=0.1)
        assert r.liquidity.state == "tight"

    def test_values_stored(self):
        r = _detect(repo_rate_spread=1.5, ted_spread=0.8)
        assert r.liquidity.repo_rate_spread == 1.5
        assert r.liquidity.ted_spread == 0.8

    def test_confidence_range(self):
        r = _detect()
        assert 0.0 <= r.liquidity.confidence <= 1.0


# ---------------------------------------------------------------------------
# GLOBAL STATE MAPPING
# ---------------------------------------------------------------------------

class TestGlobalStateMapping:
    def test_calm_is_risk_on(self):
        r = _detect()
        assert r.global_regime_state == GlobalRegimeState.RISK_ON

    def test_panic_is_crisis(self):
        r = _detect(vix_level=45.0, vix_term_structure=-0.2)
        assert r.global_regime_state == GlobalRegimeState.CRISIS

    def test_risk_off(self):
        r = _detect(vix_level=32.0)
        assert r.global_regime_state == GlobalRegimeState.RISK_OFF

    def test_transition(self):
        r = _detect(vix_level=20.0, vix_term_structure=0.02)
        assert r.global_regime_state == GlobalRegimeState.TRANSITION

    def test_liquidity_crisis_forces_crisis(self):
        """Liquidity crisis overrides risk sentiment."""
        r = _detect(vix_level=12.0, vix_term_structure=0.1, ted_spread=2.0)
        assert r.global_regime_state == GlobalRegimeState.CRISIS

    def test_emergency_monetary_with_tight_liquidity(self):
        r = _detect(
            fed_direction="cutting", fed_rate=0.1,
            repo_rate_spread=0.6, ted_spread=0.4,
        )
        assert r.global_regime_state == GlobalRegimeState.CRISIS

    def test_emergency_monetary_with_normal_liquidity_not_crisis(self):
        """Emergency monetary alone doesn't force CRISIS."""
        r = _detect(
            fed_direction="cutting", fed_rate=0.1,
            repo_rate_spread=0.1, ted_spread=0.1,
        )
        assert r.global_regime_state != GlobalRegimeState.CRISIS


# ---------------------------------------------------------------------------
# GLOBAL MACRO RESULT
# ---------------------------------------------------------------------------

class TestGlobalMacroResult:
    def test_all_fields_present(self):
        r = _detect()
        assert r.monetary_policy is not None
        assert r.risk_sentiment is not None
        assert r.liquidity is not None
        assert r.global_regime_state is not None
        assert isinstance(r.confidence, float)
        assert isinstance(r.result_hash, str)

    def test_confidence_range(self):
        r = _detect()
        assert 0.0 <= r.confidence <= 1.0

    def test_result_hash_hex(self):
        r = _detect()
        assert len(r.result_hash) == 16
        assert all(c in "0123456789abcdef" for c in r.result_hash)

    def test_result_frozen(self):
        r = _detect()
        with pytest.raises(AttributeError):
            r.confidence = 0.0


# ---------------------------------------------------------------------------
# DETERMINISM (DET-05)
# ---------------------------------------------------------------------------

class TestDeterminism:
    def test_same_inputs_same_result(self):
        r1 = _detect()
        r2 = _detect()
        assert r1.global_regime_state == r2.global_regime_state
        assert r1.risk_sentiment.state == r2.risk_sentiment.state
        assert r1.monetary_policy.state == r2.monetary_policy.state
        assert r1.liquidity.state == r2.liquidity.state
        assert r1.result_hash == r2.result_hash

    def test_different_inputs_different_hash(self):
        r1 = _detect(vix_level=12.0)
        r2 = _detect(vix_level=45.0, vix_term_structure=-0.2)
        assert r1.result_hash != r2.result_hash

    def test_fresh_instance_per_call(self):
        """DET-02: No cached state between calls."""
        d = GlobalMacroDetector()
        r1 = d.detect(**CALM_KWARGS)
        kwargs2 = {**CALM_KWARGS, "vix_level": 45.0, "vix_term_structure": -0.2}
        r2 = d.detect(**kwargs2)
        assert r1.global_regime_state != r2.global_regime_state


# ---------------------------------------------------------------------------
# EDGE CASES
# ---------------------------------------------------------------------------

class TestEdgeCases:
    def test_zero_vix(self):
        r = _detect(vix_level=0.0, vix_term_structure=0.1)
        assert r.risk_sentiment.state == "risk_on"

    def test_extreme_vix(self):
        r = _detect(vix_level=100.0, vix_term_structure=-0.5)
        assert r.risk_sentiment.state == "panic"
        assert r.global_regime_state == GlobalRegimeState.CRISIS

    def test_negative_repo_rate(self):
        r = _detect(repo_rate_spread=-1.0)
        assert r.liquidity.state == "abundant"

    def test_zero_ted_spread(self):
        r = _detect(ted_spread=0.0)
        # Should not be crisis
        assert r.liquidity.state != "crisis"


# ---------------------------------------------------------------------------
# PACKAGE IMPORT
# ---------------------------------------------------------------------------

class TestPackageImport:
    def test_import_all(self):
        from jarvis.intelligence.global_regime import (
            GlobalMacroDetector,
            GlobalMacroResult,
            MonetaryPolicyResult,
            RiskSentimentResult,
            LiquidityResult,
        )
        assert GlobalMacroDetector is not None
        assert GlobalMacroResult is not None
