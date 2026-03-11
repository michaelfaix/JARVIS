# =============================================================================
# tests/unit/confidence/test_failure_impact.py
# Tests for jarvis/confidence/failure_impact.py
# =============================================================================

import pytest

from jarvis.confidence.failure_impact import (
    IMPACT_TABLE,
    ConfidenceBundle,
    FailureImpactResult,
    apply_failure_mode_impacts,
)


# =============================================================================
# SECTION 1 -- IMPACT_TABLE CONSTANTS
# =============================================================================

class TestImpactTableStructure:
    def test_six_failure_modes(self):
        assert len(IMPACT_TABLE) == 6

    def test_all_fm_keys(self):
        expected = {"FM-01", "FM-02", "FM-03", "FM-04", "FM-05", "FM-06"}
        assert set(IMPACT_TABLE.keys()) == expected

    def test_fm01_fields(self):
        assert set(IMPACT_TABLE["FM-01"].keys()) == {"R", "Q"}

    def test_fm02_fields(self):
        assert set(IMPACT_TABLE["FM-02"].keys()) == {"S", "Q"}

    def test_fm03_fields(self):
        assert set(IMPACT_TABLE["FM-03"].keys()) == {"mu", "U"}

    def test_fm04_fields(self):
        assert set(IMPACT_TABLE["FM-04"].keys()) == {"Q", "R"}

    def test_fm05_fields(self):
        assert set(IMPACT_TABLE["FM-05"].keys()) == {"S"}

    def test_fm06_fields(self):
        assert set(IMPACT_TABLE["FM-06"].keys()) == {"mu", "S"}


class TestImpactTableValues:
    def test_fm01_r(self):
        assert IMPACT_TABLE["FM-01"]["R"] == -0.40

    def test_fm01_q(self):
        assert IMPACT_TABLE["FM-01"]["Q"] == -0.40

    def test_fm02_s(self):
        assert IMPACT_TABLE["FM-02"]["S"] == -0.30

    def test_fm02_q(self):
        assert IMPACT_TABLE["FM-02"]["Q"] == -0.20

    def test_fm03_mu(self):
        assert IMPACT_TABLE["FM-03"]["mu"] == -0.20

    def test_fm03_u(self):
        assert IMPACT_TABLE["FM-03"]["U"] == +0.15

    def test_fm04_q(self):
        assert IMPACT_TABLE["FM-04"]["Q"] == -0.50

    def test_fm04_r(self):
        assert IMPACT_TABLE["FM-04"]["R"] == -0.20

    def test_fm05_s(self):
        assert IMPACT_TABLE["FM-05"]["S"] == -0.10

    def test_fm06_mu(self):
        assert IMPACT_TABLE["FM-06"]["mu"] == -0.15

    def test_fm06_s(self):
        assert IMPACT_TABLE["FM-06"]["S"] == -0.10

    def test_only_u_is_positive(self):
        """Only FM-03/U is a positive delta; all others are negative."""
        for fm, impacts in IMPACT_TABLE.items():
            for field, delta in impacts.items():
                if field == "U":
                    assert delta > 0, f"{fm}/{field}"
                else:
                    assert delta < 0, f"{fm}/{field}"


# =============================================================================
# SECTION 2 -- CONFIDENCE BUNDLE DATACLASS
# =============================================================================

class TestConfidenceBundle:
    def test_frozen(self):
        b = ConfidenceBundle(0.8, 0.3, 0.7, 0.6, 0.2, 0.9)
        with pytest.raises(AttributeError):
            b.mu = 0.5

    def test_fields(self):
        b = ConfidenceBundle(mu=0.8, sigma2=0.3, Q=0.7, S=0.6, U=0.2, R=0.9)
        assert b.mu == 0.8
        assert b.sigma2 == 0.3
        assert b.Q == 0.7
        assert b.S == 0.6
        assert b.U == 0.2
        assert b.R == 0.9

    def test_equality(self):
        b1 = ConfidenceBundle(0.8, 0.3, 0.7, 0.6, 0.2, 0.9)
        b2 = ConfidenceBundle(0.8, 0.3, 0.7, 0.6, 0.2, 0.9)
        assert b1 == b2

    def test_inequality(self):
        b1 = ConfidenceBundle(0.8, 0.3, 0.7, 0.6, 0.2, 0.9)
        b2 = ConfidenceBundle(0.8, 0.3, 0.7, 0.6, 0.2, 0.8)
        assert b1 != b2


# =============================================================================
# SECTION 3 -- FAILURE IMPACT RESULT DATACLASS
# =============================================================================

class TestFailureImpactResult:
    def test_frozen(self):
        b = ConfidenceBundle(0.8, 0.3, 0.7, 0.6, 0.2, 0.9)
        r = FailureImpactResult(b, b, (), ())
        with pytest.raises(AttributeError):
            r.applied_modes = ("FM-01",)

    def test_fields(self):
        b1 = ConfidenceBundle(0.8, 0.3, 0.7, 0.6, 0.2, 0.9)
        b2 = ConfidenceBundle(0.4, 0.3, 0.3, 0.6, 0.2, 0.5)
        r = FailureImpactResult(b1, b2, ("FM-01",), ("FM-99",))
        assert r.original == b1
        assert r.updated == b2
        assert r.applied_modes == ("FM-01",)
        assert r.ignored_modes == ("FM-99",)


# =============================================================================
# SECTION 4 -- SINGLE FAILURE MODE APPLICATION
# =============================================================================

class TestSingleFailureMode:
    def test_fm01(self):
        b = ConfidenceBundle(mu=0.8, sigma2=0.3, Q=0.7, S=0.6, U=0.2, R=0.9)
        result = apply_failure_mode_impacts(b, ["FM-01"])
        assert result.updated.R == pytest.approx(0.5)   # 0.9 - 0.4
        assert result.updated.Q == pytest.approx(0.3)   # 0.7 - 0.4
        assert result.updated.mu == 0.8  # untouched
        assert result.updated.S == 0.6   # untouched
        assert result.updated.U == 0.2   # untouched

    def test_fm02(self):
        b = ConfidenceBundle(mu=0.8, sigma2=0.3, Q=0.7, S=0.6, U=0.2, R=0.9)
        result = apply_failure_mode_impacts(b, ["FM-02"])
        assert result.updated.S == pytest.approx(0.3)   # 0.6 - 0.3
        assert result.updated.Q == pytest.approx(0.5)   # 0.7 - 0.2

    def test_fm03_mu_decreases(self):
        b = ConfidenceBundle(mu=0.8, sigma2=0.3, Q=0.7, S=0.6, U=0.2, R=0.9)
        result = apply_failure_mode_impacts(b, ["FM-03"])
        assert result.updated.mu == pytest.approx(0.6)  # 0.8 - 0.2

    def test_fm03_u_increases(self):
        b = ConfidenceBundle(mu=0.8, sigma2=0.3, Q=0.7, S=0.6, U=0.2, R=0.9)
        result = apply_failure_mode_impacts(b, ["FM-03"])
        assert result.updated.U == pytest.approx(0.35)  # 0.2 + 0.15

    def test_fm04(self):
        b = ConfidenceBundle(mu=0.8, sigma2=0.3, Q=0.7, S=0.6, U=0.2, R=0.9)
        result = apply_failure_mode_impacts(b, ["FM-04"])
        assert result.updated.Q == pytest.approx(0.2)   # 0.7 - 0.5
        assert result.updated.R == pytest.approx(0.7)   # 0.9 - 0.2

    def test_fm05(self):
        b = ConfidenceBundle(mu=0.8, sigma2=0.3, Q=0.7, S=0.6, U=0.2, R=0.9)
        result = apply_failure_mode_impacts(b, ["FM-05"])
        assert result.updated.S == pytest.approx(0.5)   # 0.6 - 0.1
        assert result.updated.mu == 0.8  # untouched

    def test_fm06(self):
        b = ConfidenceBundle(mu=0.8, sigma2=0.3, Q=0.7, S=0.6, U=0.2, R=0.9)
        result = apply_failure_mode_impacts(b, ["FM-06"])
        assert result.updated.mu == pytest.approx(0.65)  # 0.8 - 0.15
        assert result.updated.S == pytest.approx(0.5)    # 0.6 - 0.1

    def test_sigma2_never_modified(self):
        b = ConfidenceBundle(mu=0.8, sigma2=0.3, Q=0.7, S=0.6, U=0.2, R=0.9)
        for fm in IMPACT_TABLE:
            result = apply_failure_mode_impacts(b, [fm])
            assert result.updated.sigma2 == 0.3, f"{fm} modified sigma2"

    def test_original_preserved(self):
        b = ConfidenceBundle(mu=0.8, sigma2=0.3, Q=0.7, S=0.6, U=0.2, R=0.9)
        result = apply_failure_mode_impacts(b, ["FM-01"])
        assert result.original == b


# =============================================================================
# SECTION 5 -- MULTIPLE FAILURE MODES
# =============================================================================

class TestMultipleFailureModes:
    def test_two_modes(self):
        b = ConfidenceBundle(mu=0.8, sigma2=0.3, Q=0.7, S=0.6, U=0.2, R=0.9)
        result = apply_failure_mode_impacts(b, ["FM-01", "FM-04"])
        # Q: 0.7 - 0.4 (FM-01) - 0.5 (FM-04) = -0.2 → clipped to 0.0
        assert result.updated.Q == pytest.approx(0.0)
        # R: 0.9 - 0.4 (FM-01) - 0.2 (FM-04) = 0.3
        assert result.updated.R == pytest.approx(0.3)

    def test_all_modes(self):
        b = ConfidenceBundle(mu=0.8, sigma2=0.3, Q=0.7, S=0.6, U=0.2, R=0.9)
        result = apply_failure_mode_impacts(
            b, ["FM-01", "FM-02", "FM-03", "FM-04", "FM-05", "FM-06"]
        )
        assert len(result.applied_modes) == 6
        assert len(result.ignored_modes) == 0
        # All confidence fields should have decreased
        assert result.updated.mu < b.mu
        assert result.updated.Q < b.Q
        assert result.updated.S < b.S
        assert result.updated.R < b.R
        # U should have increased
        assert result.updated.U > b.U

    def test_order_matters_cumulative(self):
        """Impacts applied sequentially — order affects intermediate clipping."""
        b = ConfidenceBundle(mu=0.8, sigma2=0.3, Q=0.3, S=0.6, U=0.2, R=0.9)
        # FM-01 Q: 0.3 - 0.4 = -0.1 → 0.0, then FM-04 Q: 0.0 - 0.5 = -0.5 → 0.0
        r1 = apply_failure_mode_impacts(b, ["FM-01", "FM-04"])
        r2 = apply_failure_mode_impacts(b, ["FM-04", "FM-01"])
        # Both should produce same result since clipping floors at 0
        assert r1.updated.Q == pytest.approx(0.0)
        assert r2.updated.Q == pytest.approx(0.0)

    def test_duplicate_mode(self):
        """Same failure mode applied twice — double impact."""
        b = ConfidenceBundle(mu=0.8, sigma2=0.3, Q=0.7, S=0.6, U=0.2, R=0.9)
        result = apply_failure_mode_impacts(b, ["FM-05", "FM-05"])
        assert result.updated.S == pytest.approx(0.4)  # 0.6 - 0.1 - 0.1
        assert result.applied_modes == ("FM-05", "FM-05")


# =============================================================================
# SECTION 6 -- CLIPPING
# =============================================================================

class TestClipping:
    def test_confidence_clipped_at_zero(self):
        b = ConfidenceBundle(mu=0.1, sigma2=0.3, Q=0.1, S=0.1, U=0.2, R=0.1)
        result = apply_failure_mode_impacts(b, ["FM-01"])
        assert result.updated.R == pytest.approx(0.0)  # 0.1 - 0.4 → 0.0
        assert result.updated.Q == pytest.approx(0.0)  # 0.1 - 0.4 → 0.0

    def test_u_clipped_at_one(self):
        b = ConfidenceBundle(mu=0.8, sigma2=0.3, Q=0.7, S=0.6, U=0.95, R=0.9)
        result = apply_failure_mode_impacts(b, ["FM-03"])
        assert result.updated.U == pytest.approx(1.0)  # 0.95 + 0.15 → 1.0

    def test_all_outputs_in_range(self):
        b = ConfidenceBundle(mu=0.01, sigma2=0.01, Q=0.01, S=0.01, U=0.99, R=0.01)
        result = apply_failure_mode_impacts(
            b, ["FM-01", "FM-02", "FM-03", "FM-04", "FM-05", "FM-06"]
        )
        for field in ["mu", "sigma2", "Q", "S", "U", "R"]:
            val = getattr(result.updated, field)
            assert 0.0 <= val <= 1.0, f"{field} = {val}"

    def test_zero_bundle_stays_zero(self):
        b = ConfidenceBundle(mu=0.0, sigma2=0.0, Q=0.0, S=0.0, U=0.0, R=0.0)
        result = apply_failure_mode_impacts(b, ["FM-01"])
        assert result.updated.Q == 0.0
        assert result.updated.R == 0.0

    def test_one_bundle_u_stays_one(self):
        b = ConfidenceBundle(mu=1.0, sigma2=1.0, Q=1.0, S=1.0, U=1.0, R=1.0)
        result = apply_failure_mode_impacts(b, ["FM-03"])
        assert result.updated.U == 1.0  # already at max


# =============================================================================
# SECTION 7 -- MONOTONICITY GUARANTEE
# =============================================================================

class TestMonotonicity:
    def test_confidence_never_increases(self):
        """mu, Q, R, S can ONLY decrease or stay the same."""
        b = ConfidenceBundle(mu=0.8, sigma2=0.3, Q=0.7, S=0.6, U=0.2, R=0.9)
        for fm in IMPACT_TABLE:
            result = apply_failure_mode_impacts(b, [fm])
            assert result.updated.mu <= b.mu, f"{fm} increased mu"
            assert result.updated.Q <= b.Q, f"{fm} increased Q"
            assert result.updated.S <= b.S, f"{fm} increased S"
            assert result.updated.R <= b.R, f"{fm} increased R"

    def test_uncertainty_never_decreases(self):
        """U can ONLY increase or stay the same."""
        b = ConfidenceBundle(mu=0.8, sigma2=0.3, Q=0.7, S=0.6, U=0.2, R=0.9)
        for fm in IMPACT_TABLE:
            result = apply_failure_mode_impacts(b, [fm])
            assert result.updated.U >= b.U, f"{fm} decreased U"


# =============================================================================
# SECTION 8 -- EMPTY AND IGNORED MODES
# =============================================================================

class TestEmptyAndIgnored:
    def test_empty_modes(self):
        b = ConfidenceBundle(mu=0.8, sigma2=0.3, Q=0.7, S=0.6, U=0.2, R=0.9)
        result = apply_failure_mode_impacts(b, [])
        assert result.updated == b
        assert result.applied_modes == ()
        assert result.ignored_modes == ()

    def test_unknown_mode_ignored(self):
        b = ConfidenceBundle(mu=0.8, sigma2=0.3, Q=0.7, S=0.6, U=0.2, R=0.9)
        result = apply_failure_mode_impacts(b, ["FM-99"])
        assert result.updated == b
        assert result.applied_modes == ()
        assert result.ignored_modes == ("FM-99",)

    def test_mixed_known_unknown(self):
        b = ConfidenceBundle(mu=0.8, sigma2=0.3, Q=0.7, S=0.6, U=0.2, R=0.9)
        result = apply_failure_mode_impacts(b, ["FM-01", "FM-99", "FM-05"])
        assert result.applied_modes == ("FM-01", "FM-05")
        assert result.ignored_modes == ("FM-99",)
        assert result.updated.R == pytest.approx(0.5)  # FM-01 applied


# =============================================================================
# SECTION 9 -- VALIDATION
# =============================================================================

class TestValidation:
    def test_bundle_type_error(self):
        with pytest.raises(TypeError, match="bundle must be a ConfidenceBundle"):
            apply_failure_mode_impacts({"mu": 0.5}, ["FM-01"])

    def test_active_modes_type_error(self):
        b = ConfidenceBundle(0.8, 0.3, 0.7, 0.6, 0.2, 0.9)
        with pytest.raises(TypeError, match="active_modes must be a list"):
            apply_failure_mode_impacts(b, ("FM-01",))

    def test_mode_element_type_error(self):
        b = ConfidenceBundle(0.8, 0.3, 0.7, 0.6, 0.2, 0.9)
        with pytest.raises(TypeError, match="each mode must be a string"):
            apply_failure_mode_impacts(b, [1])


# =============================================================================
# SECTION 10 -- DETERMINISM
# =============================================================================

class TestDeterminism:
    def test_same_inputs_same_output(self):
        b = ConfidenceBundle(mu=0.8, sigma2=0.3, Q=0.7, S=0.6, U=0.2, R=0.9)
        modes = ["FM-01", "FM-03", "FM-05"]
        results = [apply_failure_mode_impacts(b, modes) for _ in range(10)]
        for r in results[1:]:
            assert r.updated == results[0].updated

    def test_independent_calls(self):
        b = ConfidenceBundle(mu=0.8, sigma2=0.3, Q=0.7, S=0.6, U=0.2, R=0.9)
        r1 = apply_failure_mode_impacts(b, ["FM-04"])
        r2 = apply_failure_mode_impacts(b, ["FM-04"])
        assert r1.updated == r2.updated
