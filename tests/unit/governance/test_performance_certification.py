# =============================================================================
# tests/unit/governance/test_performance_certification.py — S36
#
# Comprehensive tests for PerformanceCertificationEngine.
# 8 mandatory certification criteria. Hard-block on any failure.
# =============================================================================

import dataclasses
import pytest

from jarvis.governance.performance_certification import (
    CertificationResult,
    PerformanceCertificationEngine,
)


# ---------------------------------------------------------------------------
# SHARED FIXTURES
# ---------------------------------------------------------------------------

REQUIRED_SCENARIOS = [
    "2008_CRASH",
    "COVID",
    "FLASH_CRASH",
    "SYNTHETIC_VOL",
]

PASSING_KWARGS = dict(
    model_id="m1",
    ece=0.03,
    ood_recall_historical=0.92,
    ood_recall_synthetic=0.91,
    stress_scenarios_passed=REQUIRED_SCENARIOS,
    stress_scenarios_required=REQUIRED_SCENARIOS,
    monte_carlo_var95=-0.12,
    avg_slippage_pct=0.005,
    capital_alloc_validated=True,
    reproducibility_hash="abc123",
    integrity_hash="hash_ok",
    expected_integrity_hash="hash_ok",
)


def _certify_ok():
    eng = PerformanceCertificationEngine()
    return eng.certify(**PASSING_KWARGS)


def _certify_with(**overrides):
    """Certify with overrides. Returns (engine, kwargs) for direct call."""
    eng = PerformanceCertificationEngine()
    kwargs = {**PASSING_KWARGS, **overrides}
    return eng.certify(**kwargs)


# ---------------------------------------------------------------------------
# CONSTANTS (DET-06)
# ---------------------------------------------------------------------------

class TestConstants:
    def test_ece_limit(self):
        assert PerformanceCertificationEngine.ECE_LIMIT == 0.05

    def test_ood_recall_limit(self):
        assert PerformanceCertificationEngine.OOD_RECALL_LIMIT == 0.90

    def test_monte_carlo_var_limit(self):
        assert PerformanceCertificationEngine.MONTE_CARLO_VAR_LIMIT == -0.20

    def test_max_slippage_pct(self):
        assert PerformanceCertificationEngine.MAX_SLIPPAGE_PCT == 0.01

    def test_constants_not_parameterizable(self):
        """DET-06: Constants are class-level fixed literals."""
        eng = PerformanceCertificationEngine()
        assert eng.ECE_LIMIT == 0.05
        assert eng.OOD_RECALL_LIMIT == 0.90
        assert eng.MONTE_CARLO_VAR_LIMIT == -0.20
        assert eng.MAX_SLIPPAGE_PCT == 0.01


# ---------------------------------------------------------------------------
# CERTIFICATION RESULT DATACLASS
# ---------------------------------------------------------------------------

class TestCertificationResult:
    def test_field_count(self):
        fields = dataclasses.fields(CertificationResult)
        assert len(fields) == 14

    def test_all_fields_present(self):
        result = _certify_ok()
        assert result.model_id == "m1"
        assert result.timestamp != ""
        assert result.calibration_ok is True
        assert result.ood_ok is True
        assert result.stress_ok is True
        assert result.monte_carlo_ok is True
        assert result.slippage_ok is True
        assert result.capital_alloc_ok is True
        assert result.reproducibility_ok is True
        assert result.integrity_ok is True
        assert result.all_passed is True
        assert result.deployment_cleared is True
        assert result.failures == []
        assert len(result.certification_hash) == 16


# ---------------------------------------------------------------------------
# FULL PASS
# ---------------------------------------------------------------------------

class TestFullPass:
    """FAS test: all 8 criteria pass."""

    def test_full_pass(self):
        result = _certify_ok()
        assert result.all_passed is True
        assert result.deployment_cleared is True
        assert result.failures == []

    def test_deployment_cleared_equals_all_passed(self):
        result = _certify_ok()
        assert result.deployment_cleared == result.all_passed

    def test_certification_hash_is_hex(self):
        result = _certify_ok()
        assert all(c in "0123456789abcdef" for c in result.certification_hash)

    def test_certification_hash_deterministic(self):
        """DET-05: Same inputs → same hash."""
        r1 = _certify_ok()
        r2 = _certify_ok()
        assert r1.certification_hash == r2.certification_hash


# ---------------------------------------------------------------------------
# GATE 1: CALIBRATION (ECE)
# ---------------------------------------------------------------------------

class TestCalibrationGate:
    def test_ece_failure_blocks(self):
        with pytest.raises(RuntimeError, match="DEPLOYMENT_BLOCKED"):
            _certify_with(ece=0.08)

    def test_ece_failure_message(self):
        with pytest.raises(RuntimeError, match="CALIBRATION"):
            _certify_with(ece=0.08)

    def test_ece_boundary_exactly_005_fails(self):
        """ECE must be strictly < 0.05."""
        with pytest.raises(RuntimeError, match="DEPLOYMENT_BLOCKED"):
            _certify_with(ece=0.05)

    def test_ece_just_below_005_passes(self):
        result = _certify_with(ece=0.0499)
        assert result.calibration_ok is True

    def test_ece_zero_passes(self):
        result = _certify_with(ece=0.0)
        assert result.calibration_ok is True


# ---------------------------------------------------------------------------
# GATE 2: OOD RECALL
# ---------------------------------------------------------------------------

class TestOODGate:
    def test_ood_historical_failure(self):
        with pytest.raises(RuntimeError, match="OOD"):
            _certify_with(ood_recall_historical=0.80)

    def test_ood_synthetic_failure(self):
        with pytest.raises(RuntimeError, match="OOD"):
            _certify_with(ood_recall_synthetic=0.85)

    def test_ood_both_failure(self):
        with pytest.raises(RuntimeError, match="OOD"):
            _certify_with(ood_recall_historical=0.80, ood_recall_synthetic=0.70)

    def test_ood_boundary_exactly_090_passes(self):
        """Recall >= 0.90 is OK."""
        result = _certify_with(
            ood_recall_historical=0.90, ood_recall_synthetic=0.90
        )
        assert result.ood_ok is True

    def test_ood_just_below_090_fails(self):
        with pytest.raises(RuntimeError):
            _certify_with(ood_recall_historical=0.899)


# ---------------------------------------------------------------------------
# GATE 3: STRESS TESTS
# ---------------------------------------------------------------------------

class TestStressGate:
    def test_missing_scenarios_blocks(self):
        """FAS test: missing stress scenarios block deployment."""
        with pytest.raises(RuntimeError, match="DEPLOYMENT_BLOCKED"):
            _certify_with(stress_scenarios_passed=["2008_CRASH"])

    def test_stress_failure_mentions_missing(self):
        with pytest.raises(RuntimeError, match="STRESS"):
            _certify_with(stress_scenarios_passed=["2008_CRASH"])

    def test_all_scenarios_passed(self):
        result = _certify_ok()
        assert result.stress_ok is True

    def test_extra_scenarios_ok(self):
        """Extra passed scenarios beyond required is fine."""
        result = _certify_with(
            stress_scenarios_passed=REQUIRED_SCENARIOS + ["EXTRA_SCENARIO"]
        )
        assert result.stress_ok is True

    def test_empty_required_always_passes(self):
        result = _certify_with(
            stress_scenarios_passed=[],
            stress_scenarios_required=[],
        )
        assert result.stress_ok is True

    def test_empty_passed_with_required_fails(self):
        with pytest.raises(RuntimeError, match="STRESS"):
            _certify_with(stress_scenarios_passed=[])


# ---------------------------------------------------------------------------
# GATE 4: MONTE CARLO VAR
# ---------------------------------------------------------------------------

class TestMonteCarloGate:
    def test_var_too_negative_fails(self):
        with pytest.raises(RuntimeError, match="MONTE_CARLO"):
            _certify_with(monte_carlo_var95=-0.25)

    def test_var_boundary_exactly_minus_020_passes(self):
        """VaR95 >= -0.20 is OK."""
        result = _certify_with(monte_carlo_var95=-0.20)
        assert result.monte_carlo_ok is True

    def test_var_just_below_minus_020_fails(self):
        with pytest.raises(RuntimeError):
            _certify_with(monte_carlo_var95=-0.201)

    def test_var_positive_passes(self):
        result = _certify_with(monte_carlo_var95=0.05)
        assert result.monte_carlo_ok is True

    def test_var_zero_passes(self):
        result = _certify_with(monte_carlo_var95=0.0)
        assert result.monte_carlo_ok is True


# ---------------------------------------------------------------------------
# GATE 5: SLIPPAGE
# ---------------------------------------------------------------------------

class TestSlippageGate:
    def test_slippage_too_high_fails(self):
        with pytest.raises(RuntimeError, match="SLIPPAGE"):
            _certify_with(avg_slippage_pct=0.02)

    def test_slippage_boundary_exactly_001_passes(self):
        """Slippage <= 0.01 is OK."""
        result = _certify_with(avg_slippage_pct=0.01)
        assert result.slippage_ok is True

    def test_slippage_just_above_001_fails(self):
        with pytest.raises(RuntimeError):
            _certify_with(avg_slippage_pct=0.0101)

    def test_slippage_zero_passes(self):
        result = _certify_with(avg_slippage_pct=0.0)
        assert result.slippage_ok is True


# ---------------------------------------------------------------------------
# GATE 6: CAPITAL ALLOCATION
# ---------------------------------------------------------------------------

class TestCapitalAllocationGate:
    def test_not_validated_fails(self):
        with pytest.raises(RuntimeError, match="CAPITAL_ALLOCATION"):
            _certify_with(capital_alloc_validated=False)

    def test_validated_passes(self):
        result = _certify_ok()
        assert result.capital_alloc_ok is True


# ---------------------------------------------------------------------------
# GATE 7: REPRODUCIBILITY
# ---------------------------------------------------------------------------

class TestReproducibilityGate:
    def test_empty_hash_fails(self):
        with pytest.raises(RuntimeError, match="REPRODUCIBILITY"):
            _certify_with(reproducibility_hash="")

    def test_valid_hash_passes(self):
        result = _certify_ok()
        assert result.reproducibility_ok is True

    def test_any_nonempty_hash_passes(self):
        result = _certify_with(reproducibility_hash="x")
        assert result.reproducibility_ok is True


# ---------------------------------------------------------------------------
# GATE 8: INTEGRITY
# ---------------------------------------------------------------------------

class TestIntegrityGate:
    def test_hash_mismatch_blocks(self):
        """FAS test: integrity hash mismatch blocks deployment."""
        with pytest.raises(RuntimeError, match="DEPLOYMENT_BLOCKED"):
            _certify_with(
                integrity_hash="WRONG_HASH",
                expected_integrity_hash="CORRECT_HASH",
            )

    def test_integrity_failure_message(self):
        with pytest.raises(RuntimeError, match="INTEGRITY"):
            _certify_with(
                integrity_hash="WRONG_HASH",
                expected_integrity_hash="CORRECT_HASH",
            )

    def test_matching_hashes_pass(self):
        result = _certify_ok()
        assert result.integrity_ok is True


# ---------------------------------------------------------------------------
# MULTIPLE FAILURES
# ---------------------------------------------------------------------------

class TestMultipleFailures:
    def test_all_gates_fail(self):
        with pytest.raises(RuntimeError) as exc_info:
            PerformanceCertificationEngine().certify(
                model_id="fail_all",
                ece=0.10,
                ood_recall_historical=0.50,
                ood_recall_synthetic=0.50,
                stress_scenarios_passed=[],
                stress_scenarios_required=REQUIRED_SCENARIOS,
                monte_carlo_var95=-0.50,
                avg_slippage_pct=0.05,
                capital_alloc_validated=False,
                reproducibility_hash="",
                integrity_hash="bad",
                expected_integrity_hash="good",
            )
        msg = str(exc_info.value)
        assert "CALIBRATION" in msg
        assert "OOD" in msg
        assert "STRESS" in msg
        assert "MONTE_CARLO" in msg
        assert "SLIPPAGE" in msg
        assert "CAPITAL_ALLOCATION" in msg
        assert "REPRODUCIBILITY" in msg
        assert "INTEGRITY" in msg

    def test_failure_count_in_message(self):
        with pytest.raises(RuntimeError, match="8"):
            PerformanceCertificationEngine().certify(
                model_id="fail_all",
                ece=0.10,
                ood_recall_historical=0.50,
                ood_recall_synthetic=0.50,
                stress_scenarios_passed=[],
                stress_scenarios_required=REQUIRED_SCENARIOS,
                monte_carlo_var95=-0.50,
                avg_slippage_pct=0.05,
                capital_alloc_validated=False,
                reproducibility_hash="",
                integrity_hash="bad",
                expected_integrity_hash="good",
            )

    def test_two_failures(self):
        with pytest.raises(RuntimeError) as exc_info:
            _certify_with(ece=0.08, avg_slippage_pct=0.02)
        msg = str(exc_info.value)
        assert "CALIBRATION" in msg
        assert "SLIPPAGE" in msg
        assert "2" in msg  # 2 failures


# ---------------------------------------------------------------------------
# HARD-BLOCK — NO SOFT WARNING
# ---------------------------------------------------------------------------

class TestHardBlock:
    """Verify: RuntimeError on ANY failure, never soft warning."""

    def test_single_failure_is_runtime_error(self):
        with pytest.raises(RuntimeError):
            _certify_with(ece=0.10)

    def test_error_type_is_runtime_error(self):
        """Must be RuntimeError, not ValueError or Warning."""
        with pytest.raises(RuntimeError):
            _certify_with(capital_alloc_validated=False)

    def test_success_returns_result_not_none(self):
        result = _certify_ok()
        assert result is not None
        assert isinstance(result, CertificationResult)


# ---------------------------------------------------------------------------
# DETERMINISM (DET-05)
# ---------------------------------------------------------------------------

class TestDeterminism:
    def test_same_inputs_same_result(self):
        r1 = _certify_ok()
        r2 = _certify_ok()
        assert r1.calibration_ok == r2.calibration_ok
        assert r1.ood_ok == r2.ood_ok
        assert r1.stress_ok == r2.stress_ok
        assert r1.monte_carlo_ok == r2.monte_carlo_ok
        assert r1.slippage_ok == r2.slippage_ok
        assert r1.capital_alloc_ok == r2.capital_alloc_ok
        assert r1.reproducibility_ok == r2.reproducibility_ok
        assert r1.integrity_ok == r2.integrity_ok
        assert r1.all_passed == r2.all_passed
        assert r1.certification_hash == r2.certification_hash

    def test_different_model_id_different_hash(self):
        r1 = _certify_ok()
        r2 = _certify_with(model_id="m2")
        assert r1.certification_hash != r2.certification_hash


# ---------------------------------------------------------------------------
# INTEGRATION
# ---------------------------------------------------------------------------

class TestIntegration:
    def test_full_certification_workflow(self):
        """Complete happy-path certification."""
        eng = PerformanceCertificationEngine()
        result = eng.certify(
            model_id="production_v3",
            ece=0.025,
            ood_recall_historical=0.95,
            ood_recall_synthetic=0.93,
            stress_scenarios_passed=[
                "2008_CRASH", "COVID", "FLASH_CRASH",
                "SYNTHETIC_VOL", "EXTRA_CUSTOM",
            ],
            stress_scenarios_required=REQUIRED_SCENARIOS,
            monte_carlo_var95=-0.08,
            avg_slippage_pct=0.003,
            capital_alloc_validated=True,
            reproducibility_hash="sha256_abc_full_run",
            integrity_hash="manifest_hash_v3",
            expected_integrity_hash="manifest_hash_v3",
        )
        assert result.all_passed is True
        assert result.deployment_cleared is True
        assert result.model_id == "production_v3"
        assert len(result.certification_hash) == 16

    def test_near_boundary_all_pass(self):
        """All gates at boundary values — should pass."""
        eng = PerformanceCertificationEngine()
        result = eng.certify(
            model_id="boundary",
            ece=0.0499,  # < 0.05
            ood_recall_historical=0.90,  # >= 0.90
            ood_recall_synthetic=0.90,  # >= 0.90
            stress_scenarios_passed=REQUIRED_SCENARIOS,
            stress_scenarios_required=REQUIRED_SCENARIOS,
            monte_carlo_var95=-0.20,  # >= -0.20
            avg_slippage_pct=0.01,  # <= 0.01
            capital_alloc_validated=True,
            reproducibility_hash="x",
            integrity_hash="h",
            expected_integrity_hash="h",
        )
        assert result.all_passed is True


# ---------------------------------------------------------------------------
# PACKAGE IMPORT
# ---------------------------------------------------------------------------

class TestPackageImport:
    def test_import_from_package(self):
        from jarvis.governance import (
            CertificationResult,
            PerformanceCertificationEngine,
        )
        assert PerformanceCertificationEngine is not None
        assert CertificationResult is not None
