# =============================================================================
# tests/unit/validation/test_stress.py — Unit tests for S15 stress testing
#
# 20+ tests for stress scenarios and certification.
# Self-contained — uses only synthetic data.
# =============================================================================

import math

import pytest

from jarvis.validation.stress import (
    StressScenario,
    StressResult,
    STRESS_CATEGORIES,
    SEVERITY_LEVELS,
    generate_stress_scenarios,
    run_stress_scenario,
    run_stress_certification,
    get_certification_summary,
)


# =============================================================================
# TestStressScenario
# =============================================================================

class TestStressScenario:
    """Tests for the StressScenario frozen dataclass."""

    def test_frozen(self):
        s = StressScenario(
            category="VOLATILITY", severity="LOW",
            description="test", parameters={"multiplier": 2.0},
        )
        with pytest.raises(AttributeError):
            s.category = "X"

    def test_all_fields(self):
        s = StressScenario(
            category="CORRELATION", severity="HIGH",
            description="High correlation stress",
            parameters={"avg_correlation": 0.95},
        )
        assert s.category == "CORRELATION"
        assert s.severity == "HIGH"
        assert s.description == "High correlation stress"
        assert s.parameters == {"avg_correlation": 0.95}

    def test_type_errors(self):
        with pytest.raises(TypeError):
            StressScenario(
                category=123, severity="LOW",
                description="test", parameters={},
            )
        with pytest.raises(TypeError):
            StressScenario(
                category="X", severity="LOW",
                description="test", parameters="not_dict",
            )


# =============================================================================
# TestStressResult
# =============================================================================

class TestStressResult:
    """Tests for the StressResult frozen dataclass."""

    def test_frozen(self):
        scenario = StressScenario(
            category="VOLATILITY", severity="LOW",
            description="test", parameters={},
        )
        r = StressResult(
            scenario=scenario, passed=True,
            score=0.8, details="ok",
        )
        with pytest.raises(AttributeError):
            r.passed = False

    def test_score_range(self):
        scenario = StressScenario(
            category="VOLATILITY", severity="LOW",
            description="test", parameters={},
        )
        r = StressResult(
            scenario=scenario, passed=True,
            score=0.75, details="ok",
        )
        assert 0.0 <= r.score <= 1.0

    def test_score_nan_raises(self):
        scenario = StressScenario(
            category="X", severity="LOW",
            description="test", parameters={},
        )
        with pytest.raises(ValueError):
            StressResult(
                scenario=scenario, passed=True,
                score=float("nan"), details="bad",
            )

    def test_scenario_type_error(self):
        with pytest.raises(TypeError):
            StressResult(
                scenario="not_a_scenario", passed=True,
                score=0.5, details="ok",
            )


# =============================================================================
# TestGenerateScenarios
# =============================================================================

class TestGenerateScenarios:
    """Tests for generate_stress_scenarios()."""

    def test_exactly_15_scenarios(self):
        scenarios = generate_stress_scenarios()
        assert len(scenarios) == 15

    def test_5_categories_3_severities(self):
        scenarios = generate_stress_scenarios()
        categories = set(s.category for s in scenarios)
        severities = set(s.severity for s in scenarios)
        assert categories == set(STRESS_CATEGORIES)
        assert severities == set(SEVERITY_LEVELS)

    def test_each_combination_exists(self):
        scenarios = generate_stress_scenarios()
        combos = {(s.category, s.severity) for s in scenarios}
        for cat in STRESS_CATEGORIES:
            for sev in SEVERITY_LEVELS:
                assert (cat, sev) in combos

    def test_all_have_descriptions(self):
        scenarios = generate_stress_scenarios()
        for s in scenarios:
            assert isinstance(s.description, str)
            assert len(s.description) > 0

    def test_all_have_parameters(self):
        scenarios = generate_stress_scenarios()
        for s in scenarios:
            assert isinstance(s.parameters, dict)
            assert len(s.parameters) > 0

    def test_deterministic(self):
        s1 = generate_stress_scenarios()
        s2 = generate_stress_scenarios()
        for a, b in zip(s1, s2):
            assert a.category == b.category
            assert a.severity == b.severity
            assert a.parameters == b.parameters


# =============================================================================
# TestRunScenario
# =============================================================================

class TestRunScenario:
    """Tests for run_stress_scenario()."""

    def test_pass_with_good_baseline(self):
        scenario = StressScenario(
            category="VOLATILITY", severity="LOW",
            description="test", parameters={"multiplier": 2.0},
        )
        baseline = {"quality": 1.0, "vol_resilience": 0.9}
        result = run_stress_scenario(scenario, baseline)
        assert result.passed is True
        assert result.score > 0.5

    def test_fail_with_poor_baseline(self):
        scenario = StressScenario(
            category="VOLATILITY", severity="HIGH",
            description="test", parameters={"multiplier": 10.0},
        )
        baseline = {"quality": 0.3, "vol_resilience": 0.2}
        result = run_stress_scenario(scenario, baseline)
        assert result.passed is False
        assert result.score < 0.5

    def test_score_in_range(self):
        scenarios = generate_stress_scenarios()
        baseline = {"quality": 0.8}
        for s in scenarios:
            r = run_stress_scenario(s, baseline)
            assert 0.0 <= r.score <= 1.0

    def test_type_error_scenario(self):
        with pytest.raises(TypeError):
            run_stress_scenario("not_scenario", {})

    def test_type_error_baseline(self):
        scenario = StressScenario(
            category="X", severity="LOW",
            description="test", parameters={},
        )
        with pytest.raises(TypeError):
            run_stress_scenario(scenario, "not_dict")

    def test_baseline_degradation_ordering(self):
        """Higher severity should yield lower scores."""
        baseline = {"quality": 1.0, "vol_resilience": 0.8}
        scenarios = generate_stress_scenarios()
        vol_scenarios = [s for s in scenarios if s.category == "VOLATILITY"]
        scores = {}
        for s in vol_scenarios:
            r = run_stress_scenario(s, baseline)
            scores[s.severity] = r.score
        assert scores["LOW"] >= scores["MEDIUM"]
        assert scores["MEDIUM"] >= scores["HIGH"]

    def test_empty_baseline(self):
        scenario = StressScenario(
            category="VOLATILITY", severity="LOW",
            description="test", parameters={"multiplier": 2.0},
        )
        result = run_stress_scenario(scenario, {})
        assert isinstance(result.score, float)
        assert math.isfinite(result.score)


# =============================================================================
# TestRunCertification
# =============================================================================

class TestRunCertification:
    """Tests for run_stress_certification()."""

    def test_all_15_run(self):
        results = run_stress_certification({"quality": 0.9})
        assert len(results) == 15

    def test_results_tuple(self):
        results = run_stress_certification({"quality": 0.9})
        assert isinstance(results, tuple)
        for r in results:
            assert isinstance(r, StressResult)

    def test_type_error(self):
        with pytest.raises(TypeError):
            run_stress_certification("bad")


# =============================================================================
# TestCertificationSummary
# =============================================================================

class TestCertificationSummary:
    """Tests for get_certification_summary()."""

    def test_counts(self):
        results = run_stress_certification({"quality": 1.0, "vol_resilience": 1.0,
                                             "diversification": 1.0, "liquidity_buffer": 1.0,
                                             "regime_detection": 1.0, "data_completeness": 1.0})
        summary = get_certification_summary(results)
        assert summary["total"] == 15
        assert summary["passed"] + summary["failed"] == 15

    def test_pass_rate(self):
        results = run_stress_certification({"quality": 0.9})
        summary = get_certification_summary(results)
        assert 0.0 <= summary["pass_rate"] <= 1.0
        expected_rate = summary["passed"] / summary["total"]
        assert abs(summary["pass_rate"] - expected_rate) < 1e-10

    def test_by_category(self):
        results = run_stress_certification({"quality": 0.9})
        summary = get_certification_summary(results)
        by_cat = summary["by_category"]
        for cat in STRESS_CATEGORIES:
            assert cat in by_cat
            assert by_cat[cat]["total"] == 3  # 3 severities per category

    def test_by_severity(self):
        results = run_stress_certification({"quality": 0.9})
        summary = get_certification_summary(results)
        by_sev = summary["by_severity"]
        for sev in SEVERITY_LEVELS:
            assert sev in by_sev
            assert by_sev[sev]["total"] == 5  # 5 categories per severity

    def test_type_error(self):
        with pytest.raises(TypeError):
            get_certification_summary([])  # must be tuple


# =============================================================================
# TestDeterminism
# =============================================================================

class TestDeterminism:
    """DET-07: Same inputs = same outputs."""

    def test_certification_deterministic(self):
        baseline = {"quality": 0.7, "vol_resilience": 0.6}
        r1 = run_stress_certification(baseline)
        r2 = run_stress_certification(baseline)
        for a, b in zip(r1, r2):
            assert a.score == b.score
            assert a.passed == b.passed


# =============================================================================
# TestImportContract
# =============================================================================

class TestImportContract:
    """Verify all expected names are importable."""

    def test_all_names_importable(self):
        from jarvis.validation.stress import __all__ as all_names
        import jarvis.validation.stress as mod
        for name in all_names:
            assert hasattr(mod, name), f"{name} not found in stress module"
