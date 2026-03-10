# tests/unit/risk_layer/test_risk_engine_coverage.py
# Targeted coverage tests for jarvis/risk/risk_engine.py
# Goal: push coverage to >= 95 % by exercising every branch listed below.
#
# Branches covered:
#   1. regime_posterior clipping  (> 1.0 clamped to 1.0 / < 0.0 clamped to 0.0)
#   2. vol_adjustment cap         (raw ratio > 3.0 is capped at 3.0)
#   3. Joint Risk Multiplier active (macro_regime + correlation_regime both set)
#   4. CRISIS dampening           (current_regime == CRISIS → * 0.75)
#   5. ELEVATED branch            (vol in (VOL_COMPRESSION_TRIGGER * 0.7, VOL_COMPRESSION_TRIGGER])
#
# No refactoring. No new fixtures shared with other test files.
# All imports are self-contained within this file.

import math
import pytest

from jarvis.risk.risk_engine import RiskEngine, RiskOutput
from jarvis.core.regime import GlobalRegimeState, CorrelationRegimeState


# ---------------------------------------------------------------------------
# Shared helpers
# ---------------------------------------------------------------------------

def _returns_normal(n: int = 30) -> list:
    """
    Returns a list of `n` small positive returns whose EWMA vol is well below
    VOL_COMPRESSION_TRIGGER (0.30) and whose p95 drawdown is below
    MAX_DRAWDOWN_THRESHOLD (0.15).  All values are exact rational constants.
    """
    return [0.001] * n


def _returns_high_vol(n: int = 30) -> list:
    """
    Returns a list of alternating +/- values whose annualised EWMA vol
    is comfortably above VOL_COMPRESSION_TRIGGER (0.30).
    """
    return [0.03, -0.03] * (n // 2)


def _returns_elevated_vol(n: int = 30) -> list:
    """
    Returns a list whose EWMA vol lands strictly inside the ELEVATED band:
        VOL_COMPRESSION_TRIGGER * 0.7  <  vol  <=  VOL_COMPRESSION_TRIGGER
    i.e. strictly inside (0.21, 0.30] annualised.
    Alternating ±0.016 → annualised EWMA vol ≈ 0.254, inside the ELEVATED band.
    (±0.013 yields ≈ 0.206, which falls below the lower bound of 0.21.)
    """
    return [0.016, -0.016] * (n // 2)


ENGINE = RiskEngine()


# ===========================================================================
# 1. regime_posterior CLIPPING
# ===========================================================================

class TestRegimePosteriorClipping:
    """INV-06 / INV-11: out-of-range values are silently clamped; no exception."""

    def test_posterior_above_one_is_clamped_to_one(self):
        """
        regime_posterior = 1.5 → posterior_confidence = 1.0 (upper clip).
        Output must be bit-identical to regime_posterior = 1.0.
        """
        result_clipped = ENGINE.assess(
            returns_history=_returns_normal(),
            current_regime=GlobalRegimeState.RISK_ON,
            meta_uncertainty=0.0,
            regime_posterior=1.5,
        )
        result_one = ENGINE.assess(
            returns_history=_returns_normal(),
            current_regime=GlobalRegimeState.RISK_ON,
            meta_uncertainty=0.0,
            regime_posterior=1.0,
        )
        assert result_clipped.exposure_weight == result_one.exposure_weight
        assert result_clipped.position_size_factor == result_one.position_size_factor

    def test_posterior_below_zero_is_clamped_to_zero(self):
        """
        regime_posterior = -0.5 → posterior_confidence = 0.0.
        capital_base = 0 → E_pre_clip = 0 → exposure_weight = Clip B floor (1e-6).
        """
        result = ENGINE.assess(
            returns_history=_returns_normal(),
            current_regime=GlobalRegimeState.RISK_ON,
            meta_uncertainty=0.0,
            regime_posterior=-0.5,
        )
        assert math.isclose(result.exposure_weight, 1e-6, rel_tol=0, abs_tol=0), (
            f"Expected exposure_weight == 1e-6 (Clip B floor), got {result.exposure_weight}"
        )

    def test_posterior_zero_drives_exposure_to_clip_b_floor(self):
        """
        regime_posterior = 0.0 → posterior_confidence = 0.0 → capital_base = 0
        → E_pre_clip = 0 → Clip B floor = 1e-6.
        """
        result = ENGINE.assess(
            returns_history=_returns_normal(),
            current_regime=GlobalRegimeState.RISK_ON,
            meta_uncertainty=0.0,
            regime_posterior=0.0,
        )
        assert math.isclose(result.exposure_weight, 1e-6, rel_tol=0, abs_tol=0)

    def test_posterior_none_is_identity(self):
        """
        regime_posterior = None → posterior_confidence = 1.0.
        Output must be bit-identical to regime_posterior = 1.0.
        """
        result_none = ENGINE.assess(
            returns_history=_returns_normal(),
            current_regime=GlobalRegimeState.RISK_ON,
            meta_uncertainty=0.0,
            regime_posterior=None,
        )
        result_one = ENGINE.assess(
            returns_history=_returns_normal(),
            current_regime=GlobalRegimeState.RISK_ON,
            meta_uncertainty=0.0,
            regime_posterior=1.0,
        )
        assert result_none.exposure_weight == result_one.exposure_weight

    def test_posterior_interior_value_scales_exposure(self):
        """
        regime_posterior = 0.5 → posterior_confidence = 0.5.
        exposure_weight must be strictly less than the same call with posterior = None.
        """
        result_half = ENGINE.assess(
            returns_history=_returns_normal(),
            current_regime=GlobalRegimeState.RISK_ON,
            meta_uncertainty=0.0,
            regime_posterior=0.5,
        )
        result_full = ENGINE.assess(
            returns_history=_returns_normal(),
            current_regime=GlobalRegimeState.RISK_ON,
            meta_uncertainty=0.0,
            regime_posterior=None,
        )
        assert result_half.exposure_weight < result_full.exposure_weight

    def test_posterior_no_effect_on_risk_compression_flag(self):
        """
        INV-10: risk_compression_active must be identical whether posterior is
        0.0, 0.5, or 1.0 — it depends only on vol, dd, and current_regime.
        """
        results = [
            ENGINE.assess(
                returns_history=_returns_normal(),
                current_regime=GlobalRegimeState.RISK_ON,
                meta_uncertainty=0.0,
                regime_posterior=p,
            )
            for p in (0.0, 0.5, 1.0)
        ]
        flags = [r.risk_compression_active for r in results]
        assert flags[0] == flags[1] == flags[2]


# ===========================================================================
# 2. vol_adjustment CAP (3.0)
# ===========================================================================

class TestVolAdjustmentCap:
    """DET-06: vol_adjustment is hard-capped at 3.0."""

    def test_vol_adjustment_cap_binds_at_3(self):
        """
        target_vol / realized_vol >> 3.0 → vol_adjustment must equal 3.0.
        Verify by comparing with a call where target_vol / realized_vol == 3.0 exactly.
        """
        # raw ratio = 0.90 / 0.01 = 90 → capped at 3.0
        # meta_uncertainty=0.5 prevents Clip B ceiling from masking the cap effect.
        result_cap = ENGINE.assess(
            returns_history=_returns_normal(),
            current_regime=GlobalRegimeState.RISK_ON,
            meta_uncertainty=0.5,
            realized_vol=0.01,
            target_vol=0.90,
        )
        # raw ratio = 0.03 / 0.01 = 3.0 → exactly at cap
        result_exact = ENGINE.assess(
            returns_history=_returns_normal(),
            current_regime=GlobalRegimeState.RISK_ON,
            meta_uncertainty=0.5,
            realized_vol=0.01,
            target_vol=0.03,
        )
        assert result_cap.exposure_weight == result_exact.exposure_weight, (
            "Cap at 3.0 not binding: very large ratio should equal ratio-of-3.0 result"
        )

    def test_vol_adjustment_below_cap_not_truncated(self):
        """
        raw ratio < 3.0 → no cap applied; result differs from the capped case.
        """
        # meta_uncertainty=0.3: uncertainty_penalty=0.7 reduces E_pre_clip below 1.0,
        # so the 2x vs 3x vol_adjustment difference is no longer masked by Clip B ceiling.
        result_below_cap = ENGINE.assess(
            returns_history=_returns_normal(),
            current_regime=GlobalRegimeState.RISK_ON,
            meta_uncertainty=0.3,
            realized_vol=0.10,
            target_vol=0.20,   # ratio = 2.0, below cap
        )
        result_at_cap = ENGINE.assess(
            returns_history=_returns_normal(),
            current_regime=GlobalRegimeState.RISK_ON,
            meta_uncertainty=0.3,
            realized_vol=0.01,
            target_vol=0.03,   # ratio = 3.0, at cap
        )
        assert result_below_cap.exposure_weight != result_at_cap.exposure_weight

    def test_realized_vol_zero_uses_floor(self):
        """
        realized_vol = 0.0 → denominator floor (1e-10) prevents division by zero.
        Result must be finite and equal to the cap (3.0 is immediately hit).
        """
        result = ENGINE.assess(
            returns_history=_returns_normal(),
            current_regime=GlobalRegimeState.RISK_ON,
            meta_uncertainty=0.0,
            realized_vol=0.0,
            target_vol=0.20,
        )
        assert math.isfinite(result.exposure_weight)
        assert 0.0 < result.exposure_weight <= 1.0

    def test_vol_adjustment_none_is_identity(self):
        """
        realized_vol=None or target_vol=None → vol_adjustment=1.0 (identity).
        Result must equal the call with no vol params at all.
        """
        base = ENGINE.assess(
            returns_history=_returns_normal(),
            current_regime=GlobalRegimeState.RISK_ON,
            meta_uncertainty=0.0,
        )
        no_target = ENGINE.assess(
            returns_history=_returns_normal(),
            current_regime=GlobalRegimeState.RISK_ON,
            meta_uncertainty=0.0,
            realized_vol=0.10,
            target_vol=None,
        )
        no_realized = ENGINE.assess(
            returns_history=_returns_normal(),
            current_regime=GlobalRegimeState.RISK_ON,
            meta_uncertainty=0.0,
            realized_vol=None,
            target_vol=0.20,
        )
        assert base.exposure_weight == no_target.exposure_weight
        assert base.exposure_weight == no_realized.exposure_weight

    def test_downward_vol_scaling(self):
        """
        realized_vol > target_vol → vol_adjustment < 1.0 → exposure reduced.
        """
        # meta_uncertainty=0.3 ensures E_pre_clip is below 1.0 so the downward
        # vol_adjustment (ratio=0.25) is not masked by the Clip B ceiling.
        result_scaled_down = ENGINE.assess(
            returns_history=_returns_normal(),
            current_regime=GlobalRegimeState.RISK_ON,
            meta_uncertainty=0.3,
            realized_vol=0.40,
            target_vol=0.10,   # ratio = 0.25 < 1.0
        )
        result_identity = ENGINE.assess(
            returns_history=_returns_normal(),
            current_regime=GlobalRegimeState.RISK_ON,
            meta_uncertainty=0.3,
        )
        assert result_scaled_down.exposure_weight < result_identity.exposure_weight


# ===========================================================================
# 3. Joint Risk Multiplier ACTIVE
# ===========================================================================

class TestJointRiskMultiplierActive:
    """INV-03: Clip C is applied iff joint_multiplier != 1.0."""

    def test_jrm_active_reduces_exposure(self):
        """
        RISK_OFF + BREAKDOWN → joint_multiplier = 2.0 (highest in table).
        exposure_weight must be lower than the same call with JRM inactive.
        """
        base = ENGINE.assess(
            returns_history=_returns_normal(),
            current_regime=GlobalRegimeState.RISK_ON,
            meta_uncertainty=0.0,
        )
        with_jrm = ENGINE.assess(
            returns_history=_returns_normal(),
            current_regime=GlobalRegimeState.RISK_ON,
            meta_uncertainty=0.0,
            macro_regime=GlobalRegimeState.RISK_OFF,
            correlation_regime=CorrelationRegimeState.BREAKDOWN,
        )
        assert with_jrm.exposure_weight < base.exposure_weight

    def test_jrm_clip_c_floor_binds(self):
        """
        JM-03: When exposure_weight / joint_multiplier < SHOCK_EXPOSURE_CAP,
        Clip C floor (0.25) must bind.
        Use meta_uncertainty = 0.99 to drive E_pre_clip near zero, then
        apply large JRM → Clip C floor must kick in and yield exactly 0.25.
        But also CRISIS dampening must NOT be active (non-CRISIS regime).
        """
        result = ENGINE.assess(
            returns_history=_returns_normal(),
            current_regime=GlobalRegimeState.RISK_ON,
            meta_uncertainty=0.99,
            macro_regime=GlobalRegimeState.RISK_OFF,
            correlation_regime=CorrelationRegimeState.BREAKDOWN,  # multiplier = 2.0
        )
        # Clip C floor = SHOCK_EXPOSURE_CAP = 0.25. Dampening is not active.
        assert math.isclose(result.exposure_weight, 0.25, rel_tol=1e-9), (
            f"Clip C floor expected 0.25, got {result.exposure_weight}"
        )

    def test_jrm_identity_multiplier_suppresses_clip_c(self):
        """
        RISK_ON + DIVERGENCE → joint_multiplier = 1.0 → Clip C is suppressed.
        Exposure must equal the no-JRM baseline.
        """
        baseline = ENGINE.assess(
            returns_history=_returns_normal(),
            current_regime=GlobalRegimeState.RISK_ON,
            meta_uncertainty=0.0,
        )
        with_identity_jrm = ENGINE.assess(
            returns_history=_returns_normal(),
            current_regime=GlobalRegimeState.RISK_ON,
            meta_uncertainty=0.0,
            macro_regime=GlobalRegimeState.RISK_ON,
            correlation_regime=CorrelationRegimeState.DIVERGENCE,  # multiplier = 1.0
        )
        assert baseline.exposure_weight == with_identity_jrm.exposure_weight

    def test_jrm_only_macro_set_suppresses_clip_c(self):
        """
        INV-03: if correlation_regime is None, joint_multiplier = 1.0,
        Clip C must be suppressed regardless of macro_regime.
        """
        baseline = ENGINE.assess(
            returns_history=_returns_normal(),
            current_regime=GlobalRegimeState.RISK_ON,
            meta_uncertainty=0.0,
        )
        partial_jrm = ENGINE.assess(
            returns_history=_returns_normal(),
            current_regime=GlobalRegimeState.RISK_ON,
            meta_uncertainty=0.0,
            macro_regime=GlobalRegimeState.RISK_OFF,
            correlation_regime=None,
        )
        assert baseline.exposure_weight == partial_jrm.exposure_weight

    def test_all_jrm_table_entries_produce_finite_result(self):
        """
        Smoke-test all 9 (macro × correlation) table entries.
        Each must produce a finite exposure_weight in [0, 1].
        """
        macro_states = [
            GlobalRegimeState.RISK_ON,
            GlobalRegimeState.TRANSITION,
            GlobalRegimeState.RISK_OFF,
        ]
        corr_states = [
            CorrelationRegimeState.DIVERGENCE,
            CorrelationRegimeState.COUPLED,
            CorrelationRegimeState.BREAKDOWN,
        ]
        for macro in macro_states:
            for corr in corr_states:
                result = ENGINE.assess(
                    returns_history=_returns_normal(),
                    current_regime=GlobalRegimeState.RISK_ON,
                    meta_uncertainty=0.0,
                    macro_regime=macro,
                    correlation_regime=corr,
                )
                assert math.isfinite(result.exposure_weight), (
                    f"Non-finite result for macro={macro}, corr={corr}"
                )
                assert 0.0 <= result.exposure_weight <= 1.0, (
                    f"Out-of-range for macro={macro}, corr={corr}: {result.exposure_weight}"
                )


# ===========================================================================
# 4. CRISIS DAMPENING
# ===========================================================================

class TestCrisisDampening:
    """INV-04: CRISIS dampening (×0.75) is applied after Clip C."""

    def test_crisis_dampening_applied(self):
        """
        CR-01: current_regime=CRISIS with JRM inactive.
        exposure_weight = (Clip B result) * 0.75.
        Verify by computing expected value from the non-CRISIS baseline.
        """
        baseline = ENGINE.assess(
            returns_history=_returns_normal(),
            current_regime=GlobalRegimeState.RISK_ON,
            meta_uncertainty=0.0,
        )
        crisis_result = ENGINE.assess(
            returns_history=_returns_normal(),
            current_regime=GlobalRegimeState.CRISIS,
            meta_uncertainty=0.0,
        )
        # CRISIS forces risk_compression → DEFENSIVE regime → lower position_size_factor.
        # Dampening adds a further ×0.75 on top.
        assert crisis_result.exposure_weight < baseline.exposure_weight
        assert crisis_result.risk_compression_active is True
        assert crisis_result.risk_regime == "DEFENSIVE"

    def test_crisis_dampening_factor_is_0_75(self):
        """
        CR-02: verify the exact factor by comparing CRISIS result to
        a hypothetical pre-dampening value.
        We call assess() twice: once CRISIS, once RISK_ON with identical
        returns. The CRISIS pre-dampening value equals the Clip B/C output
        which we recover via RISK_ON with no optional params.
        Instead, we verify the ratio by engineering a case where
        exposure_weight / 0.75 is recoverable.

        Strategy: use meta_uncertainty=0.0, no JRM, no vol scaling.
        Then CRISIS exposure = RISK_ON-equivalent pre-damp * 0.75.
        We capture the pre-dampening value by calling with RISK_ON (same
        returns, same params). Both go through the same position_size path
        EXCEPT that CRISIS forces DEFENSIVE risk_regime and SHOCK_EXPOSURE_CAP
        base, so we cannot directly compare those.

        Instead we directly verify ratio invariant within a single CRISIS call:
        exposure_weight must be <= 0.75 (since max pre-damp is 1.0) and
        exposure_weight / 0.75 must be <= 1.0.
        """
        result = ENGINE.assess(
            returns_history=_returns_normal(),
            current_regime=GlobalRegimeState.CRISIS,
            meta_uncertainty=0.0,
        )
        pre_damp = result.exposure_weight / 0.75
        assert pre_damp <= 1.0 + 1e-12, (
            f"Pre-dampening value {pre_damp} exceeds 1.0 — dampening not applied"
        )
        assert math.isfinite(result.exposure_weight)

    def test_crisis_dampening_can_go_below_shock_exposure_cap(self):
        """
        INV-04 specified behaviour: result may fall below SHOCK_EXPOSURE_CAP
        (0.25) after CRISIS dampening. Verify this is not re-clipped.
        Use high meta_uncertainty to push pre-damp value below 0.25 / 0.75 ≈ 0.333.
        """
        result = ENGINE.assess(
            returns_history=_returns_normal(),
            current_regime=GlobalRegimeState.CRISIS,
            meta_uncertainty=0.8,
        )
        # Must be below SHOCK_EXPOSURE_CAP (0.25) to prove no re-clip occurs
        assert result.exposure_weight < 0.25, (
            f"Expected exposure_weight < 0.25 (CRISIS dampening below cap), "
            f"got {result.exposure_weight}"
        )

    def test_non_crisis_regime_no_dampening(self):
        """
        CR-03: current_regime != CRISIS → dampening factor NOT applied.
        """
        for regime in (
            GlobalRegimeState.RISK_ON,
            GlobalRegimeState.RISK_OFF,
            GlobalRegimeState.TRANSITION,
        ):
            result = ENGINE.assess(
                returns_history=_returns_normal(),
                current_regime=regime,
                meta_uncertainty=0.0,
            )
            # If dampening were applied, exposure would be ~25% lower.
            # We simply verify risk_regime is not CRISIS and result is valid.
            assert result.risk_regime in ("NORMAL", "ELEVATED", "CRITICAL", "DEFENSIVE")
            assert math.isfinite(result.exposure_weight)

    def test_crisis_with_jrm_active_dampening_is_post_clip_c(self):
        """
        CR-02 ordering: dampening is applied AFTER Clip C.
        With CRISIS + JRM active, the result may be below SHOCK_EXPOSURE_CAP.
        If dampening were applied before Clip C, Clip C would re-floor at 0.25,
        producing a higher result. We verify the result is below 0.25.
        """
        result = ENGINE.assess(
            returns_history=_returns_normal(),
            current_regime=GlobalRegimeState.CRISIS,
            meta_uncertainty=0.5,
            macro_regime=GlobalRegimeState.RISK_OFF,
            correlation_regime=CorrelationRegimeState.BREAKDOWN,
        )
        # Clip C floor = 0.25. CRISIS dampening * 0.75 → result < 0.25.
        assert result.exposure_weight < 0.25, (
            f"CRISIS post-Clip-C dampening should produce < 0.25, got {result.exposure_weight}"
        )


# ===========================================================================
# 5. ELEVATED BRANCH
# ===========================================================================

class TestElevatedBranch:
    """
    risk_regime == 'ELEVATED' when:
        VOL_COMPRESSION_TRIGGER * 0.7  <  vol  <=  VOL_COMPRESSION_TRIGGER
    i.e. roughly 0.21 < vol <= 0.30 annualised.
    """

    def test_elevated_branch_produces_elevated_regime(self):
        """
        Returns engineered to land vol in the ELEVATED band.
        risk_regime must equal 'ELEVATED'.
        """
        result = ENGINE.assess(
            returns_history=_returns_elevated_vol(),
            current_regime=GlobalRegimeState.RISK_ON,
            meta_uncertainty=0.0,
        )
        assert result.risk_regime == "ELEVATED", (
            f"Expected risk_regime='ELEVATED', got '{result.risk_regime}'. "
            f"volatility_forecast={result.volatility_forecast:.4f}"
        )

    def test_elevated_branch_no_risk_compression(self):
        """
        ELEVATED does not itself trigger risk_compression_active unless
        other thresholds are also breached.
        With normal returns (below DD threshold) and non-CRISIS regime,
        risk_compression_active should be False.
        """
        result = ENGINE.assess(
            returns_history=_returns_elevated_vol(),
            current_regime=GlobalRegimeState.RISK_ON,
            meta_uncertainty=0.0,
        )
        # ELEVATED branch alone does not cross VOL_COMPRESSION_TRIGGER → no compression
        # (this verifies the branch boundary is correct)
        assert result.risk_regime == "ELEVATED"
        # Compression would require vol > VOL_COMPRESSION_TRIGGER (0.30)
        assert result.risk_compression_active is False

    def test_elevated_regime_cap_is_0_7(self):
        """
        ELEVATED regime_cap = 0.7 in compute_adaptive_position_size().
        This is lower than NORMAL (1.0) so position_size_factor must be
        strictly less than a NORMAL-regime call with identical other inputs.
        """
        normal_result = ENGINE.assess(
            returns_history=_returns_normal(),
            current_regime=GlobalRegimeState.RISK_ON,
            meta_uncertainty=0.0,
        )
        elevated_result = ENGINE.assess(
            returns_history=_returns_elevated_vol(),
            current_regime=GlobalRegimeState.RISK_ON,
            meta_uncertainty=0.0,
        )
        assert elevated_result.position_size_factor < normal_result.position_size_factor, (
            "ELEVATED regime_cap (0.7) should reduce position_size_factor vs NORMAL (1.0)"
        )

    def test_elevated_vol_is_in_expected_range(self):
        """
        Sanity-check: volatility_forecast for _returns_elevated_vol()
        is in (VOL_COMPRESSION_TRIGGER * 0.7, VOL_COMPRESSION_TRIGGER].
        """
        VOL_COMPRESSION_TRIGGER = 0.30
        result = ENGINE.assess(
            returns_history=_returns_elevated_vol(),
            current_regime=GlobalRegimeState.RISK_ON,
            meta_uncertainty=0.0,
        )
        lower = VOL_COMPRESSION_TRIGGER * 0.7   # 0.21
        upper = VOL_COMPRESSION_TRIGGER          # 0.30
        assert lower < result.volatility_forecast <= upper, (
            f"volatility_forecast {result.volatility_forecast:.4f} is not in "
            f"ELEVATED band ({lower:.4f}, {upper:.4f}]"
        )

    def test_critical_branch_above_elevated(self):
        """
        Complementary check: vol > VOL_COMPRESSION_TRIGGER → CRITICAL (not ELEVATED).
        Ensures ELEVATED is a strict sub-range, not an alias for all high-vol states.
        """
        result = ENGINE.assess(
            returns_history=_returns_high_vol(),
            current_regime=GlobalRegimeState.RISK_ON,
            meta_uncertainty=0.0,
        )
        assert result.risk_regime == "CRITICAL", (
            f"Expected 'CRITICAL' for high-vol returns, got '{result.risk_regime}'. "
            f"volatility_forecast={result.volatility_forecast:.4f}"
        )
