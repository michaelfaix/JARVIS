# =============================================================================
# tests/unit/risk/test_failure_mode_handler.py
# =============================================================================
"""Unit tests for jarvis.risk.failure_mode_handler (FM-01..FM-06 + SIMULTANEOUS_FM_RULES)."""

import pytest

from jarvis.risk.failure_mode_handler import (
    FailureMode,
    FailureModeStatus,
    detect_failure_modes,
    SIMULTANEOUS_FM_RULES,
    FM01_KALMAN_THRESHOLD,
    FM02_VOL_SPIKE_FACTOR,
    FM03_REGIME_CHANGE_LIMIT,
    FM04_CORRELATION_THRESHOLD,
    FM06_ECE_THRESHOLD,
)


# =============================================================================
# Helpers -- default kwargs for detect_failure_modes (all-safe values)
# =============================================================================

def _safe_kwargs():
    """Return kwargs that trigger NO failure modes."""
    return dict(
        kalman_condition_number=100.0,
        current_volatility=0.10,
        baseline_volatility=0.10,
        regime_changes_in_window=0,
        avg_correlation=0.30,
        ood_score=0.01,
        ood_threshold=0.50,
        current_ece=0.01,
    )


# =============================================================================
# 1. FailureMode enum has 6 values
# =============================================================================

class TestFailureModeEnum:
    def test_has_six_members(self):
        assert len(FailureMode) == 6

    def test_member_values(self):
        assert FailureMode.FM_01.value == "FM-01"
        assert FailureMode.FM_02.value == "FM-02"
        assert FailureMode.FM_03.value == "FM-03"
        assert FailureMode.FM_04.value == "FM-04"
        assert FailureMode.FM_05.value == "FM-05"
        assert FailureMode.FM_06.value == "FM-06"


# =============================================================================
# 2. FailureModeStatus is frozen
# =============================================================================

class TestFailureModeStatusFrozen:
    def test_frozen(self):
        status = FailureModeStatus(
            active_modes=(),
            severity=0.0,
            simultaneous_count=0,
            recommended_action="NORMAL",
        )
        with pytest.raises(AttributeError):
            status.severity = 0.5  # type: ignore[misc]

        with pytest.raises(AttributeError):
            status.recommended_action = "HALT"  # type: ignore[misc]


# =============================================================================
# 3. No failure modes → NORMAL
# =============================================================================

class TestNoFailureModes:
    def test_all_safe_returns_normal(self):
        result = detect_failure_modes(**_safe_kwargs())
        assert result.active_modes == ()
        assert result.severity == 0.0
        assert result.simultaneous_count == 0
        assert result.recommended_action == "NORMAL"


# =============================================================================
# 4. FM-01: Kalman divergence
# =============================================================================

class TestFM01:
    def test_triggered_by_high_condition_number(self):
        kw = _safe_kwargs()
        kw["kalman_condition_number"] = 2e6
        result = detect_failure_modes(**kw)
        assert FailureMode.FM_01 in result.active_modes
        assert result.simultaneous_count == 1

    def test_not_triggered_at_threshold(self):
        kw = _safe_kwargs()
        kw["kalman_condition_number"] = FM01_KALMAN_THRESHOLD
        result = detect_failure_modes(**kw)
        assert FailureMode.FM_01 not in result.active_modes

    def test_severity_scales(self):
        kw = _safe_kwargs()
        kw["kalman_condition_number"] = 5.5e6  # midpoint of 1e6..10e6
        result = detect_failure_modes(**kw)
        assert 0.0 < result.severity < 1.0


# =============================================================================
# 5. FM-02: Volatility spike
# =============================================================================

class TestFM02:
    def test_triggered_by_vol_spike(self):
        kw = _safe_kwargs()
        kw["current_volatility"] = 0.40
        kw["baseline_volatility"] = 0.10
        result = detect_failure_modes(**kw)
        assert FailureMode.FM_02 in result.active_modes

    def test_not_triggered_below_factor(self):
        kw = _safe_kwargs()
        kw["current_volatility"] = 0.29
        kw["baseline_volatility"] = 0.10
        result = detect_failure_modes(**kw)
        assert FailureMode.FM_02 not in result.active_modes

    def test_just_below_boundary_not_triggered(self):
        kw = _safe_kwargs()
        kw["current_volatility"] = FM02_VOL_SPIKE_FACTOR * 0.10 - 1e-9
        kw["baseline_volatility"] = 0.10
        result = detect_failure_modes(**kw)
        assert FailureMode.FM_02 not in result.active_modes


# =============================================================================
# 6. FM-03: Regime oscillation
# =============================================================================

class TestFM03:
    def test_triggered_by_regime_oscillation(self):
        kw = _safe_kwargs()
        kw["regime_changes_in_window"] = 5
        result = detect_failure_modes(**kw)
        assert FailureMode.FM_03 in result.active_modes

    def test_not_triggered_at_limit(self):
        kw = _safe_kwargs()
        kw["regime_changes_in_window"] = FM03_REGIME_CHANGE_LIMIT
        result = detect_failure_modes(**kw)
        assert FailureMode.FM_03 not in result.active_modes


# =============================================================================
# 7. FM-04: Correlation breakdown
# =============================================================================

class TestFM04:
    def test_triggered_by_high_correlation(self):
        kw = _safe_kwargs()
        kw["avg_correlation"] = 0.90
        result = detect_failure_modes(**kw)
        assert FailureMode.FM_04 in result.active_modes

    def test_not_triggered_at_threshold(self):
        kw = _safe_kwargs()
        kw["avg_correlation"] = FM04_CORRELATION_THRESHOLD
        result = detect_failure_modes(**kw)
        assert FailureMode.FM_04 not in result.active_modes


# =============================================================================
# 8. FM-05: OOD detection
# =============================================================================

class TestFM05:
    def test_triggered_by_ood_score(self):
        kw = _safe_kwargs()
        kw["ood_score"] = 0.80
        kw["ood_threshold"] = 0.50
        result = detect_failure_modes(**kw)
        assert FailureMode.FM_05 in result.active_modes

    def test_not_triggered_below_threshold(self):
        kw = _safe_kwargs()
        kw["ood_score"] = 0.49
        kw["ood_threshold"] = 0.50
        result = detect_failure_modes(**kw)
        assert FailureMode.FM_05 not in result.active_modes


# =============================================================================
# 9. FM-06: ECE calibration violation
# =============================================================================

class TestFM06:
    def test_triggered_by_high_ece(self):
        kw = _safe_kwargs()
        kw["current_ece"] = 0.10
        result = detect_failure_modes(**kw)
        assert FailureMode.FM_06 in result.active_modes

    def test_not_triggered_at_threshold(self):
        kw = _safe_kwargs()
        kw["current_ece"] = FM06_ECE_THRESHOLD
        result = detect_failure_modes(**kw)
        assert FailureMode.FM_06 not in result.active_modes


# =============================================================================
# 10. Simultaneous rules: 1 FM → REDUCE_EXPOSURE
# =============================================================================

class TestSimultaneousOneFM:
    def test_single_fm_reduce_exposure(self):
        kw = _safe_kwargs()
        kw["kalman_condition_number"] = 2e6
        result = detect_failure_modes(**kw)
        assert result.simultaneous_count == 1
        assert result.recommended_action == "REDUCE_EXPOSURE"


# =============================================================================
# 11. Simultaneous rules: 2 FMs → DEFENSIVE
# =============================================================================

class TestSimultaneousTwoFMs:
    def test_two_fms_defensive(self):
        kw = _safe_kwargs()
        kw["kalman_condition_number"] = 2e6   # FM-01
        kw["current_volatility"] = 0.40       # FM-02
        kw["baseline_volatility"] = 0.10
        result = detect_failure_modes(**kw)
        assert result.simultaneous_count == 2
        assert result.recommended_action == "DEFENSIVE"


# =============================================================================
# 12. Simultaneous rules: 3+ FMs → HALT
# =============================================================================

class TestSimultaneousThreePlusFMs:
    def test_three_fms_halt(self):
        kw = _safe_kwargs()
        kw["kalman_condition_number"] = 2e6   # FM-01
        kw["current_volatility"] = 0.40       # FM-02
        kw["baseline_volatility"] = 0.10
        kw["regime_changes_in_window"] = 5    # FM-03
        result = detect_failure_modes(**kw)
        assert result.simultaneous_count == 3
        assert result.recommended_action == "HALT"

    def test_four_fms_halt(self):
        kw = _safe_kwargs()
        kw["kalman_condition_number"] = 2e6   # FM-01
        kw["current_volatility"] = 0.40       # FM-02
        kw["baseline_volatility"] = 0.10
        kw["regime_changes_in_window"] = 5    # FM-03
        kw["avg_correlation"] = 0.95          # FM-04
        result = detect_failure_modes(**kw)
        assert result.simultaneous_count == 4
        assert result.recommended_action == "HALT"

    def test_all_six_fms_halt(self):
        result = detect_failure_modes(
            kalman_condition_number=2e6,       # FM-01
            current_volatility=0.40,           # FM-02
            baseline_volatility=0.10,
            regime_changes_in_window=5,        # FM-03
            avg_correlation=0.95,              # FM-04
            ood_score=0.80,                    # FM-05
            ood_threshold=0.50,
            current_ece=0.10,                  # FM-06
        )
        assert result.simultaneous_count == 6
        assert result.recommended_action == "HALT"
        assert len(result.active_modes) == 6


# =============================================================================
# 13. Severity is max of individual severities
# =============================================================================

class TestSeverityIsMax:
    def test_severity_max_of_individuals(self):
        # FM-01 with huge condition number → high severity
        # FM-06 with barely-over ECE → low severity
        result = detect_failure_modes(
            kalman_condition_number=10e6,       # FM-01, severity ~1.0
            current_volatility=0.10,
            baseline_volatility=0.10,
            regime_changes_in_window=0,
            avg_correlation=0.30,
            ood_score=0.01,
            ood_threshold=0.50,
            current_ece=0.051,                 # FM-06, severity ~0.005
        )
        assert result.simultaneous_count == 2
        # Severity should be close to 1.0 (from FM-01), not ~0.005 (from FM-06)
        assert result.severity > 0.9


# =============================================================================
# 14. Determinism
# =============================================================================

class TestDeterminism:
    def test_identical_inputs_identical_outputs(self):
        kw = dict(
            kalman_condition_number=2e6,
            current_volatility=0.35,
            baseline_volatility=0.10,
            regime_changes_in_window=4,
            avg_correlation=0.90,
            ood_score=0.60,
            ood_threshold=0.50,
            current_ece=0.08,
        )
        r1 = detect_failure_modes(**kw)
        r2 = detect_failure_modes(**kw)
        assert r1.active_modes == r2.active_modes
        assert r1.severity == r2.severity
        assert r1.simultaneous_count == r2.simultaneous_count
        assert r1.recommended_action == r2.recommended_action


# =============================================================================
# 15. Constants match expected values
# =============================================================================

class TestConstants:
    def test_fm01_threshold(self):
        assert FM01_KALMAN_THRESHOLD == 1e6

    def test_fm02_factor(self):
        assert FM02_VOL_SPIKE_FACTOR == 3.0

    def test_fm03_limit(self):
        assert FM03_REGIME_CHANGE_LIMIT == 3

    def test_fm04_threshold(self):
        assert FM04_CORRELATION_THRESHOLD == 0.85

    def test_fm06_threshold(self):
        assert FM06_ECE_THRESHOLD == 0.05

    def test_simultaneous_rules_mapping(self):
        assert SIMULTANEOUS_FM_RULES[0] == "NORMAL"
        assert SIMULTANEOUS_FM_RULES[1] == "REDUCE_EXPOSURE"
        assert SIMULTANEOUS_FM_RULES[2] == "DEFENSIVE"


# =============================================================================
# 16. Import contract
# =============================================================================

class TestImportContract:
    def test_all_public_symbols_importable(self):
        from jarvis.risk import failure_mode_handler
        for name in failure_mode_handler.__all__:
            assert hasattr(failure_mode_handler, name), f"Missing: {name}"

    def test_module_has_no_prohibited_imports(self):
        """Verify the module does not import logging, random, or os."""
        import jarvis.risk.failure_mode_handler as mod
        import inspect
        source = inspect.getsource(mod)
        assert "import logging" not in source
        assert "import random" not in source
        assert "import os" not in source
        assert "open(" not in source


# =============================================================================
# 17. Validation / error handling
# =============================================================================

class TestValidation:
    def test_non_numeric_kalman_raises_type_error(self):
        kw = _safe_kwargs()
        kw["kalman_condition_number"] = "bad"
        with pytest.raises(TypeError):
            detect_failure_modes(**kw)

    def test_non_int_regime_changes_raises_type_error(self):
        kw = _safe_kwargs()
        kw["regime_changes_in_window"] = 3.5
        with pytest.raises(TypeError):
            detect_failure_modes(**kw)

    def test_zero_baseline_volatility_raises_value_error(self):
        kw = _safe_kwargs()
        kw["baseline_volatility"] = 0.0
        with pytest.raises(ValueError):
            detect_failure_modes(**kw)

    def test_zero_ood_threshold_raises_value_error(self):
        kw = _safe_kwargs()
        kw["ood_threshold"] = 0.0
        with pytest.raises(ValueError):
            detect_failure_modes(**kw)
