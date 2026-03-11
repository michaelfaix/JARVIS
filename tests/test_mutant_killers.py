# =============================================================================
# Mutant Killer Tests — Targets surviving mutants from mutation testing
# =============================================================================
#
# Organized by module. Each test is annotated with the mutant ID it kills.
#
# EQUIVALENT MUTANTS (cannot be killed — identical observable behavior):
#   131: penalty += → = (first penalty, starts at 0)
#   208: dict.get default 0.40 → 1.4 (all valid enums are in the map)
#   294: loss_rate <= → < at exact threshold (penalty = 0 in both branches)
#   298: max(0.4, 1e-9) → max(0.4, 2e-9) (0.4 always dominates)
#   300: min(1.0, x) → min(2.0, x) (x never exceeds 1.0)

from unittest.mock import MagicMock

import pytest

from jarvis.core.decision_context_state import (
    DecisionRecord,
    DecisionContextSnapshot,
)
from jarvis.core.regime import CorrelationRegimeState
from jarvis.intelligence.regime_duration_model import (
    RegimeDurationModel,
    RegimeDurationResult,
)
from jarvis.strategy.signal_fragility_analyzer import (
    SignalFragilityAnalyzer,
    SignalFragilityResult,
)
from jarvis.confidence.adaptive_selectivity_model import (
    AdaptiveSelectivityModel,
    AdaptiveSelectivityResult,
    BASE_SELECTIVITY_THRESHOLD,
)
from jarvis.intelligence.decision_quality_engine import (
    DecisionQualityBundle,
    DecisionQualityEngine,
)


# ---------------------------------------------------------------------------
# HELPERS
# ---------------------------------------------------------------------------

def _rdm():
    return RegimeDurationModel()


def _asm():
    return AdaptiveSelectivityModel()


def _asm_compute(**overrides) -> AdaptiveSelectivityResult:
    defaults = dict(
        regime_stability_score=0.8,
        total_uncertainty=0.2,
        correlation_regime=CorrelationRegimeState.NORMAL,
        active_failure_modes=frozenset(),
        transition_acceleration_flag=False,
    )
    defaults.update(overrides)
    return _asm().compute_threshold(**defaults)


def _sfa():
    return SignalFragilityAnalyzer()


def _dqe():
    return DecisionQualityEngine()


def _duration(z=0.0, flag=False):
    return RegimeDurationResult(
        regime_age_ratio=1.0,
        duration_z_score=z,
        transition_acceleration_flag=flag,
    )


def _fragility(index=0.0):
    return SignalFragilityResult(
        parameter_sensitivity_score=index,
        volatility_sensitivity_score=index,
        spread_sensitivity_score=index,
        correlation_sensitivity_score=index,
        fragility_index=index,
    )


def _snapshot(records=None):
    if records is None:
        records = ()
    return DecisionContextSnapshot(
        records=tuple(records),
        total_appended=len(records),
    )


def _rec(seq=0, regime="RISK_ON", conf=0.5, outcome="NEUTRAL", strategy="s"):
    return DecisionRecord(
        sequence_id=seq,
        regime_at_decision=regime,
        confidence_at_decision=conf,
        outcome=outcome,
        strategy_id=strategy,
    )


def _calm_compute(**overrides) -> DecisionQualityBundle:
    defaults = dict(
        regime_transition_diagonal_mean=0.9,
        duration_result=_duration(z=0.0, flag=False),
        fragility_result=_fragility(0.0),
        correlation_regime=CorrelationRegimeState.NORMAL,
        overfitting_risk_score=0.0,
        total_uncertainty=0.1,
        decision_snapshot=_snapshot(),
        active_failure_modes=frozenset(),
    )
    defaults.update(overrides)
    return _dqe().compute(**defaults)


# ---------------------------------------------------------------------------
# NON-LINEAR SIGNAL FUNCTIONS (for floor mutation detection)
# ---------------------------------------------------------------------------

def _cubic_vol_signal(**kwargs):
    """Cubic in volatility only: sensitivity = d^2 at base≈0."""
    return kwargs.get("volatility", 0.0) ** 3


def _cubic_spread_signal(**kwargs):
    """Cubic in spread only: sensitivity = d^2 at base≈0."""
    return kwargs.get("spread", 0.0) ** 3


def _cubic_param_signal(**kwargs):
    """Cubic in lookback param only: sensitivity = d^2 at base=0."""
    return kwargs.get("lookback", 0.0) ** 3


# ===================================================================
# REGIME DURATION MODEL — Mutants 7, 8, 11, 12
# Error message text assertions (detect XX prefix/suffix)
# ===================================================================

class TestRDMErrorMessages:
    """Kill mutants 7,8,11,12: error message string mutations (XX prefix)."""

    def test_timestamp_error_starts_correctly(self):
        """Mutants 7,8: message must start with 'current_timestamp' and
        contain '. Got' (not '. XXGot')."""
        with pytest.raises(ValueError) as exc_info:
            _rdm().compute(
                regime_start_timestamp=200.0,
                current_timestamp=100.0,
                historical_avg_duration=50.0,
                historical_std_duration=10.0,
            )
        msg = str(exc_info.value)
        assert msg.startswith("current_timestamp")  # kills mutant 7
        assert ". Got current=" in msg  # kills mutant 8 (". XXGot" fails)

    def test_avg_duration_error_starts_correctly(self):
        """Mutants 11,12: message must start with 'historical_avg_duration'
        and end with the value (not 'valueXX')."""
        with pytest.raises(ValueError) as exc_info:
            _rdm().compute(
                regime_start_timestamp=100.0,
                current_timestamp=200.0,
                historical_avg_duration=-1.0,
                historical_std_duration=10.0,
            )
        msg = str(exc_info.value)
        assert msg.startswith("historical_avg_duration")  # kills mutant 11
        assert msg.endswith("-1.0")  # kills mutant 12 (would end "XX")


# ===================================================================
# SIGNAL FRAGILITY ANALYZER — Mutants 68, 70, 75, 79, 87
# ===================================================================

class TestSFAErrorMessages:
    """Kill mutants 68, 70: error message string mutations."""

    def test_vol_error_starts_correctly(self):
        """Mutant 68: msg must start with 'base_volatility'."""
        with pytest.raises(ValueError) as exc_info:
            _sfa().compute(
                signal_fn=_cubic_vol_signal,
                base_volatility=-0.5,
                base_spread=0.01,
                base_correlation=0.3,
                strategy_params={"lookback": 20.0},
            )
        assert str(exc_info.value).startswith("base_volatility")

    def test_empty_params_error_starts_correctly(self):
        """Mutant 70: msg must start with 'strategy_params'."""
        with pytest.raises(ValueError) as exc_info:
            _sfa().compute(
                signal_fn=_cubic_vol_signal,
                base_volatility=0.2,
                base_spread=0.01,
                base_correlation=0.3,
                strategy_params={},
            )
        assert str(exc_info.value).startswith("strategy_params")


class TestSFAFloorValues:
    """Kill mutants 75, 79, 87: _safe_delta floor values at call sites.

    Uses cubic signal where sensitivity = d^2 at base≈0.
    Different floors → different sensitivities → detectable.
    """

    def test_vol_floor_001_via_cubic(self):
        """Mutant 75: floor 0.01 → 1.01. Cubic vol sensitivity at base≈0:
        original d=0.01 → sens=d^2=0.0001; mutant d=1.01 → sens≈1.0."""
        result = _sfa().compute(
            signal_fn=_cubic_vol_signal,
            base_volatility=1e-10,  # near-zero → uses floor for delta
            base_spread=0.01,
            base_correlation=0.0,
            strategy_params={"lookback": 20.0},
        )
        # vol sensitivity = d^2 = 0.01^2 = 0.0001
        assert result.volatility_sensitivity_score < 0.01  # kills mutant 75

    def test_spread_floor_00001_via_cubic(self):
        """Mutant 79: floor 0.0001 → 1.0001. Cubic spread sensitivity at base≈0:
        original d=0.0001 → sens≈1e-8; mutant d=1.0001 → sens≈1.0."""
        result = _sfa().compute(
            signal_fn=_cubic_spread_signal,
            base_volatility=0.5,
            base_spread=1e-15,  # near-zero → uses floor
            base_correlation=0.0,
            strategy_params={"lookback": 10.0},
        )
        # spread sensitivity = d^2 = 0.0001^2 = 1e-8 ≈ 0
        assert result.spread_sensitivity_score < 0.001  # kills mutant 79

    def test_param_floor_1e6_via_cubic(self):
        """Mutant 87: floor 1e-6 → 2e-6. Cubic param sensitivity at base=0:
        original d=1e-6 → sens=(1e-6)^2=1e-12; mutant d=2e-6 → sens=4e-12.
        Uses param-only signal to avoid floating-point cancellation."""
        result = _sfa().compute(
            signal_fn=_cubic_param_signal,
            base_volatility=0.5,
            base_spread=0.5,
            base_correlation=0.0,
            strategy_params={"lookback": 0.0},  # zero → uses floor
        )
        # param sensitivity = d^2 = (1e-6)^2 = 1e-12
        # Mutant would give (2e-6)^2 = 4e-12
        assert abs(result.parameter_sensitivity_score - 1e-12) < 2e-12


# ===================================================================
# ADAPTIVE SELECTIVITY MODEL — Mutants 125-126, 133, 137, 141, 149, 152, 156
# ===================================================================

class TestASMErrorMessages:
    """Kill mutants 125, 126: TypeError message text (XX prefix/suffix)."""

    def test_type_error_starts_correctly(self):
        """Mutant 125: msg must start with 'correlation_regime'."""
        with pytest.raises(TypeError) as exc_info:
            _asm_compute(correlation_regime="NORMAL")
        msg = str(exc_info.value)
        assert msg.startswith("correlation_regime")  # kills mutant 125

    def test_type_error_ends_correctly(self):
        """Mutant 126: msg must end with type name (no XX suffix)."""
        with pytest.raises(TypeError) as exc_info:
            _asm_compute(correlation_regime="NORMAL")
        msg = str(exc_info.value)
        assert msg.endswith("str")  # kills mutant 126


class TestASMReasonStrings:
    """Kill mutants 133, 137, 141, 149, 152, 156: reason strings with XX."""

    def test_low_regime_stability_reason_no_xx(self):
        """Mutant 133: reason must NOT contain 'XX' prefix/suffix."""
        r = _asm_compute(regime_stability_score=0.2)
        assert "XX" not in r.adjustment_reason  # kills mutant 133
        assert "LOW_REGIME_STABILITY(0.200)" in r.adjustment_reason

    def test_high_uncertainty_reason_no_xx(self):
        """Mutant 137: reason must NOT contain 'XX'."""
        r = _asm_compute(total_uncertainty=0.7)
        assert "XX" not in r.adjustment_reason  # kills mutant 137

    def test_correlation_stress_reason_no_xx(self):
        """Mutant 141: exact string without XX."""
        r = _asm_compute(correlation_regime=CorrelationRegimeState.BREAKDOWN)
        assert "XX" not in r.adjustment_reason  # kills mutant 141

    def test_active_fm_reason_no_xx(self):
        """Mutant 149: reason must NOT contain 'XX'."""
        r = _asm_compute(active_failure_modes=frozenset({"FM-01", "FM-02"}))
        assert "XX" not in r.adjustment_reason  # kills mutant 149

    def test_duration_stress_flag_reason_no_xx(self):
        """Mutant 152: exact string without XX."""
        r = _asm_compute(transition_acceleration_flag=True)
        assert "XX" not in r.adjustment_reason  # kills mutant 152

    def test_no_adjustment_reason_exact(self):
        """Mutant 156: calm inputs → reason is exactly 'NO_ADJUSTMENT'."""
        r = _asm_compute()
        assert r.adjustment_reason == "NO_ADJUSTMENT"

    def test_multiple_reasons_separator_no_xx(self):
        """Mutant 156: separator '; ' mutated to 'XX; XX'.
        Check that joined string has no 'XX'."""
        r = _asm_compute(
            regime_stability_score=0.2,
            total_uncertainty=0.7,
        )
        assert "XX" not in r.adjustment_reason  # kills mutant 156
        assert "; " in r.adjustment_reason
        # Verify exact format: each part starts correctly
        parts = r.adjustment_reason.split("; ")
        assert any(p.startswith("LOW_REGIME_STABILITY(") for p in parts)
        assert any(p.startswith("HIGH_UNCERTAINTY(") for p in parts)


# ===================================================================
# DECISION QUALITY ENGINE — Mutants 255
# ===================================================================

class TestDQEPassFailExactBoundary:
    """Kill mutant 255: composite >= threshold changed to >."""

    def test_composite_exactly_equals_threshold_passes(self):
        """Mutant 255: >= vs >. When composite == threshold, must pass.

        Strategy: compute once to get exact FP composite value, then mock
        the selectivity model to return that exact value as threshold.
        This guarantees bit-exact composite == threshold in FP arithmetic.

        With >=: composite >= composite → True
        With > : composite > composite → False (mutant killed)
        """
        engine = _dqe()
        kwargs = dict(
            regime_transition_diagonal_mean=0.9,
            duration_result=_duration(z=0.0, flag=False),
            fragility_result=_fragility(0.0),
            correlation_regime=CorrelationRegimeState.NORMAL,
            overfitting_risk_score=0.0,
            total_uncertainty=0.0,
            decision_snapshot=_snapshot(),
            active_failure_modes=frozenset(),
        )
        # Step 1: compute to get exact FP composite value
        b1 = engine.compute(**kwargs)
        composite = b1.composite_quality_score

        # Step 2: mock selectivity model to return threshold == composite
        mock_result = AdaptiveSelectivityResult(
            resolved_threshold=composite,
            adjustment_reason="MOCK_EXACT_BOUNDARY",
            base_used=BASE_SELECTIVITY_THRESHOLD,
        )
        mock_model = MagicMock()
        mock_model.compute_threshold.return_value = mock_result
        engine._selectivity_model = mock_model

        # Step 3: recompute — composite unchanged, threshold == composite
        b2 = engine.compute(**kwargs)
        assert b2.composite_quality_score == composite
        assert b2.selectivity_threshold == composite
        assert b2.signal_passes_selectivity is True  # kills mutant 255


# ===================================================================
# RETAINED: streak and misalignment tests (already killing mutants)
# ===================================================================

class TestDQEStreakLenBoundary:
    """Kill mutants 260, 261: len(recent) < 2 boundary."""

    def test_single_record_streak_is_zero(self):
        b = _calm_compute(
            decision_snapshot=_snapshot([_rec(seq=0, outcome="WIN")])
        )
        assert b.streak_instability == 0.0

    def test_two_records_different_gives_nonzero_streak(self):
        recs = [
            _rec(seq=0, outcome="WIN"),
            _rec(seq=1, outcome="LOSS"),
        ]
        b = _calm_compute(decision_snapshot=_snapshot(recs))
        assert abs(b.streak_instability - 1.0) < 1e-9

    def test_two_records_same_gives_zero_streak(self):
        recs = [
            _rec(seq=0, outcome="WIN"),
            _rec(seq=1, outcome="WIN"),
        ]
        b = _calm_compute(decision_snapshot=_snapshot(recs))
        assert b.streak_instability == 0.0


class TestDQESmallWeightTerms:
    """Kill mutants 239, 241, 243: streak/misalignment weight contributions."""

    def test_streak_instability_affects_composite(self):
        alternating = [
            _rec(seq=i, outcome="WIN" if i % 2 == 0 else "LOSS")
            for i in range(10)
        ]
        b_alt = _calm_compute(decision_snapshot=_snapshot(alternating))
        same = [_rec(seq=i, outcome="WIN") for i in range(10)]
        b_same = _calm_compute(decision_snapshot=_snapshot(same))
        diff = b_same.composite_quality_score - b_alt.composite_quality_score
        assert abs(diff - 0.05) < 1e-9

    def test_regime_misalignment_affects_composite(self):
        recs = [
            _rec(seq=i, regime="RISK_OFF") for i in range(19)
        ] + [_rec(seq=19, regime="RISK_ON")]
        b_mis = _calm_compute(decision_snapshot=_snapshot(recs))
        recs_same = [_rec(seq=i, regime="RISK_ON") for i in range(20)]
        b_same = _calm_compute(decision_snapshot=_snapshot(recs_same))
        expected_diff = 0.03 * 0.95
        actual_diff = b_same.composite_quality_score - b_mis.composite_quality_score
        assert abs(actual_diff - expected_diff) < 1e-9

    def test_misalignment_value_is_exact(self):
        recs = [
            _rec(seq=i, regime="RISK_OFF") for i in range(19)
        ] + [_rec(seq=19, regime="RISK_ON")]
        b = _calm_compute(decision_snapshot=_snapshot(recs))
        assert abs(b.regime_misalignment - 0.95) < 1e-9


class TestDQEFailureWindow:
    """Kill mutant 194: FAILURE_WINDOW = 10."""

    def test_failure_window_exactly_10_records(self):
        records_10 = [_rec(seq=i, outcome="LOSS") for i in range(10)]
        b10 = _calm_compute(decision_snapshot=_snapshot(records_10))
        assert abs(b10.repeated_failure_penalty - 1.0) < 1e-9

        records_11 = [_rec(seq=0, outcome="NEUTRAL")] + [
            _rec(seq=i + 1, outcome="LOSS") for i in range(10)
        ]
        b11 = _calm_compute(decision_snapshot=_snapshot(records_11))
        assert abs(b11.repeated_failure_penalty - 1.0) < 1e-9

        records_11b = [
            _rec(seq=i, outcome="LOSS") for i in range(10)
        ] + [_rec(seq=10, outcome="NEUTRAL")]
        b11b = _calm_compute(decision_snapshot=_snapshot(records_11b))
        assert abs(b11b.repeated_failure_penalty - 0.75) < 1e-9


# ===================================================================
# ROUND 2: Mutant killers from custom mutation testing script
# ===================================================================

import math
import numpy as np


# ---------------------------------------------------------------------------
# fragility_index: compute_from_correlations boundary (L262, L266)
# total_components=1 and max_recovery_bars=1 should NOT raise
# ---------------------------------------------------------------------------

class TestFragilityBoundaryValues:
    def test_total_components_exactly_one_valid(self):
        from jarvis.metrics.fragility_index import StructuralFragilityIndex
        sfi = StructuralFragilityIndex()
        result = sfi.compute_from_correlations(
            pairwise_correlations=[0.5],
            failure_count=0,
            total_components=1,
            recovery_time_bars=5,
            max_recovery_bars=10,
        )
        assert result.fragility_index >= 0.0

    def test_max_recovery_bars_exactly_one_valid(self):
        from jarvis.metrics.fragility_index import StructuralFragilityIndex
        sfi = StructuralFragilityIndex()
        result = sfi.compute_from_correlations(
            pairwise_correlations=[0.5],
            failure_count=0,
            total_components=5,
            recovery_time_bars=1,
            max_recovery_bars=1,
        )
        assert result.fragility_index >= 0.0

    def test_total_components_zero_raises(self):
        from jarvis.metrics.fragility_index import StructuralFragilityIndex
        sfi = StructuralFragilityIndex()
        with pytest.raises(ValueError, match="total_components must be >= 1"):
            sfi.compute_from_correlations(
                pairwise_correlations=[0.5],
                failure_count=0,
                total_components=0,
                recovery_time_bars=5,
                max_recovery_bars=10,
            )

    def test_max_recovery_bars_zero_raises(self):
        from jarvis.metrics.fragility_index import StructuralFragilityIndex
        sfi = StructuralFragilityIndex()
        with pytest.raises(ValueError, match="max_recovery_bars must be >= 1"):
            sfi.compute_from_correlations(
                pairwise_correlations=[0.5],
                failure_count=0,
                total_components=5,
                recovery_time_bars=5,
                max_recovery_bars=0,
            )


# ---------------------------------------------------------------------------
# trust_score: _clip01 boundary at exactly 0.0 and 1.0 (L142, L144)
# ---------------------------------------------------------------------------

class TestTrustScoreClip01Exact:
    def test_clip01_exactly_zero(self):
        from jarvis.metrics.trust_score import _clip01
        assert _clip01(0.0) == 0.0

    def test_clip01_exactly_one(self):
        from jarvis.metrics.trust_score import _clip01
        assert _clip01(1.0) == 1.0

    def test_clip01_tiny_negative(self):
        from jarvis.metrics.trust_score import _clip01
        assert _clip01(-1e-10) == 0.0

    def test_clip01_just_above_one(self):
        from jarvis.metrics.trust_score import _clip01
        assert _clip01(1.0 + 1e-10) == 1.0


# ---------------------------------------------------------------------------
# event_log: get_entries(last_n=0) boundary (L382: > 0 -> >= 0)
# ---------------------------------------------------------------------------

class TestEventLogLastNZero:
    def _make_log_with_entries(self):
        from jarvis.core.event_log import EventLog, EventLogEntry
        log = EventLog(session_id="test", operating_mode="historical",
                       start_time=1000.0)
        log.set_genesis_state_hash("genesis_hash")
        e1 = EventLogEntry(
            sequence_id=0, timestamp=1001.0, event_type="market_data",
            event_payload={"x": 1},
            state_hash_before="h0", state_hash_after="h1",
        )
        e2 = EventLogEntry(
            sequence_id=1, timestamp=1002.0, event_type="market_data",
            event_payload={"x": 2},
            state_hash_before="h1", state_hash_after="h2",
        )
        log.append(e1)
        log.append(e2)
        return log

    def test_get_entries_last_n_zero_returns_all(self):
        log = self._make_log_with_entries()
        # Original (> 0): 0 > 0 is False -> returns all entries
        # Mutant (>= 0): 0 >= 0 is True -> returns [] (empty)
        entries = log.get_entries(last_n=0)
        assert len(entries) == 2

    def test_get_entries_last_n_1(self):
        log = self._make_log_with_entries()
        entries = log.get_entries(last_n=1)
        assert len(entries) == 1
        assert entries[0].event_type == "market_data"


# ---------------------------------------------------------------------------
# event_log: integrity hash encoding (L351: "utf-8" -> "utf+8")
# ---------------------------------------------------------------------------

class TestEventLogHashEncoding:
    def test_integrity_hash_valid_hex(self):
        from jarvis.core.event_log import EventLog, EventLogEntry
        log = EventLog(session_id="test", operating_mode="historical",
                       start_time=1000.0)
        log.set_genesis_state_hash("genesis_hash")
        e = EventLogEntry(
            sequence_id=0, timestamp=1001.0, event_type="market_data",
            event_payload={"key": "val"},
            state_hash_before="h0", state_hash_after="h1",
        )
        log.append(e)
        h = log.compute_integrity_hash()
        assert len(h) == 64
        assert all(c in "0123456789abcdef" for c in h)


# ---------------------------------------------------------------------------
# reproducibility: tolerance boundary (L193: >= -> >)
# ---------------------------------------------------------------------------

class TestReproducibilityTolerance:
    def test_diff_exactly_at_tolerance_is_mismatch(self):
        from jarvis.systems.reproducibility import (
            ReproducibilityController, TOLERANCE_FLOAT_COMPARE,
        )
        ctrl = ReproducibilityController()
        # Use small base so tolerance is distinguishable in FP
        a = 0.0
        b = TOLERANCE_FLOAT_COMPARE  # diff == tolerance exactly
        result = ctrl.verify_reproducibility({"val": a}, {"val": b})
        # abs(0.0 - tol) >= tol is True -> mismatch
        assert not result.reproducible

    def test_diff_below_tolerance_is_identical(self):
        from jarvis.systems.reproducibility import (
            ReproducibilityController, TOLERANCE_FLOAT_COMPARE,
        )
        ctrl = ReproducibilityController()
        a = 0.0
        b = TOLERANCE_FLOAT_COMPARE * 0.5
        result = ctrl.verify_reproducibility({"val": a}, {"val": b})
        assert result.reproducible


# ---------------------------------------------------------------------------
# reproducibility: shape mismatch (L198: != -> ==)
# ---------------------------------------------------------------------------

class TestReproducibilityShapeMismatch:
    def test_array_shape_mismatch_detected(self):
        from jarvis.systems.reproducibility import ReproducibilityController
        checker = ReproducibilityController()
        a = np.array([1.0, 2.0])
        b = np.array([1.0, 2.0, 3.0])
        result = checker.verify_reproducibility({"arr": a}, {"arr": b})
        assert not result.reproducible
        assert any("shape" in m for m in result.mismatches)


# ---------------------------------------------------------------------------
# reproducibility: array diff (L203: a - b -> a + b)
# ---------------------------------------------------------------------------

class TestReproducibilityArrayDiff:
    def test_array_value_mismatch_detected(self):
        from jarvis.systems.reproducibility import ReproducibilityController
        checker = ReproducibilityController()
        a = np.array([1.0, 2.0])
        b = np.array([1.0, 999.0])
        result = checker.verify_reproducibility({"arr": a}, {"arr": b})
        assert not result.reproducible


# ---------------------------------------------------------------------------
# reproducibility: fingerprint encoding (L246: "utf-8" -> "utf+8")
# ---------------------------------------------------------------------------

class TestReproducibilityFingerprint:
    def test_fingerprint_valid_hex(self):
        from jarvis.systems.reproducibility import ReproducibilityController
        checker = ReproducibilityController()
        fp = checker.get_system_fingerprint()
        assert len(fp) == 16
        assert all(c in "0123456789abcdef" for c in fp)

    def test_fingerprint_deterministic(self):
        from jarvis.systems.reproducibility import ReproducibilityController
        assert (ReproducibilityController().get_system_fingerprint()
                == ReproducibilityController().get_system_fingerprint())


# ---------------------------------------------------------------------------
# regime_transition: default laplace_smoothing (L187: 0.1 -> 0.2)
# ---------------------------------------------------------------------------

class TestRegimeTransitionDefaultSmoothing:
    def test_default_matches_explicit_01(self):
        from jarvis.intelligence.regime_transition import RegimeTransitionEstimator
        est = RegimeTransitionEstimator()
        # Use a longer sequence with many transitions so smoothing matters
        seq = (["TRENDING", "TRENDING", "RANGING", "TRENDING"] * 20 +
               ["HIGH_VOL", "SHOCK", "UNKNOWN", "TRENDING"] * 5)
        result_default = est.estimate(seq)
        result_01 = est.estimate(seq, laplace_smoothing=0.1)
        result_02 = est.estimate(seq, laplace_smoothing=0.2)
        # Default should match 0.1, not 0.2
        assert result_default.matrix == result_01.matrix
        assert result_default.matrix != result_02.matrix


# ---------------------------------------------------------------------------
# bayesian_confidence: evidence=0 boundary (L225: > 0 -> >= 0)
# and formula (L227: prior * likelihood -> prior / likelihood)
# ---------------------------------------------------------------------------

class TestBayesianConfidenceFormula:
    def test_high_quality_gives_higher_posterior(self):
        from jarvis.intelligence.bayesian_confidence import BayesianConfidenceEngine
        eng = BayesianConfidenceEngine()
        result_high = eng.update(
            prior_confidence=0.8,
            regime="TRENDING",
            quality_score=0.95,
            fm_active=False,
            regime_stable=True,
        )
        result_low = eng.update(
            prior_confidence=0.8,
            regime="TRENDING",
            quality_score=0.1,
            fm_active=False,
            regime_stable=True,
        )
        # With * formula: high quality -> higher likelihood -> higher posterior
        # With / formula: high quality -> lower (inverted) -> LOWER posterior
        assert result_high.posterior_confidence >= result_low.posterior_confidence

    def test_formula_produces_reasonable_posterior(self):
        from jarvis.intelligence.bayesian_confidence import BayesianConfidenceEngine
        eng = BayesianConfidenceEngine()
        result = eng.update(
            prior_confidence=0.8,
            regime="TRENDING",
            quality_score=0.9,
            fm_active=False,
            regime_stable=True,
        )
        # With correct formula, posterior should be close to prior
        assert 0.3 < result.posterior_confidence <= 1.0


# ---------------------------------------------------------------------------
# validation_gates: reason string operator content (L163, L219, L249, L302)
# ---------------------------------------------------------------------------

class TestValidationGatesReasonContent:
    def test_quality_gate_fail_reason_has_lt(self):
        from jarvis.systems.validation_gates import QualityGate
        gate = QualityGate()
        result = gate.check(quality_score=0.01)  # well below threshold
        assert not result.passed
        assert "<" in result.reason
        assert "<=" not in result.reason  # mutant would use "<="

    def test_kalman_gate_fail_reason_has_gte(self):
        from jarvis.systems.validation_gates import KalmanGate
        gate = KalmanGate()
        result = gate.check(condition_number=1e12)  # well above threshold
        assert not result.passed
        assert ">=" in result.reason

    def test_ece_gate_fail_reason_has_gte(self):
        from jarvis.systems.validation_gates import ECEGate
        gate = ECEGate()
        result = gate.check(ece=0.5)  # well above threshold
        assert not result.passed
        assert ">=" in result.reason

    def test_risk_gate_fail_reason_has_lt(self):
        from jarvis.systems.validation_gates import RiskGate
        gate = RiskGate()
        result = gate.check(var=-1.0)  # well below threshold
        assert not result.passed
        assert "<" in result.reason
        assert "<=" not in result.reason
