# =============================================================================
# tests/unit/report/test_enriched_report.py
# =============================================================================
#
# Tests for generate_enriched_report() and ReportResult in
# jarvis/report/engine.py.
#
# Sections:
#   1. ReportResult frozen dataclass
#   2. Minimal call (equity_curve only)
#   3. Regime-conditional returns integration
#   4. Stress test results integration
#   5. TrustScoreEngine integration
#   6. Full enriched report (all sections)
#   7. Validation / error handling
#   8. Backward compatibility (generate_report unchanged)
#   9. Determinism
#  10. Import contract
#
# =============================================================================

import pytest

from jarvis.report.engine import (
    ReportResult,
    generate_enriched_report,
    generate_report,
)
from jarvis.metrics.trust_score import TrustScoreResult
from jarvis.simulation.strategy_lab import StressTestResult


# =============================================================================
# FIXTURES
# =============================================================================

@pytest.fixture
def equity_curve():
    """Simple equity curve with 10 values."""
    return [100.0, 102.0, 101.0, 104.0, 103.0, 106.0, 105.0, 108.0, 107.0, 110.0]


@pytest.fixture
def returns_and_labels():
    """Returns and regime labels for regime-conditional analysis."""
    returns = [0.02, -0.01, 0.03, -0.01, 0.03, -0.01, 0.03, -0.01, 0.03]
    labels = [
        "RISK_ON", "RISK_ON", "RISK_ON",
        "RISK_OFF", "RISK_OFF", "RISK_OFF",
        "CRISIS", "CRISIS", "CRISIS",
    ]
    return returns, labels


@pytest.fixture
def stress_results():
    """Two pre-computed stress test results."""
    return [
        StressTestResult(
            scenario="2008_FINANCIAL_CRISIS",
            pnl_impact=-0.35,
            max_drawdown=0.45,
            recovery_periods=120,
            survived=True,
        ),
        StressTestResult(
            scenario="2020_COVID_CRASH",
            pnl_impact=-0.25,
            max_drawdown=0.30,
            recovery_periods=60,
            survived=True,
        ),
    ]


@pytest.fixture
def trust_params():
    """Trust score input parameters."""
    return {
        "trust_ece": 0.03,
        "trust_ood_recall": 0.85,
        "trust_prediction_variance": 0.05,
        "trust_drawdown": 0.10,
        "trust_uptime": 0.99,
    }


# =============================================================================
# SECTION 1 -- ReportResult FROZEN DATACLASS
# =============================================================================

class TestReportResultDataclass:
    """Verify ReportResult is a frozen dataclass with correct fields."""

    def test_frozen(self, equity_curve):
        result = generate_enriched_report(equity_curve)
        with pytest.raises(AttributeError):
            result.metrics = {}

    def test_equity_curve_is_tuple(self, equity_curve):
        result = generate_enriched_report(equity_curve)
        assert isinstance(result.equity_curve, tuple)

    def test_equity_curve_values_preserved(self, equity_curve):
        result = generate_enriched_report(equity_curve)
        assert list(result.equity_curve) == equity_curve

    def test_has_all_fields(self, equity_curve):
        result = generate_enriched_report(equity_curve)
        assert hasattr(result, "equity_curve")
        assert hasattr(result, "metrics")
        assert hasattr(result, "regime_returns")
        assert hasattr(result, "stress_results")
        assert hasattr(result, "trust_score")
        assert hasattr(result, "periods_per_year")

    def test_type_is_report_result(self, equity_curve):
        result = generate_enriched_report(equity_curve)
        assert isinstance(result, ReportResult)


# =============================================================================
# SECTION 2 -- MINIMAL CALL (equity_curve only)
# =============================================================================

class TestMinimalCall:
    """generate_enriched_report with only equity_curve."""

    def test_returns_report_result(self, equity_curve):
        result = generate_enriched_report(equity_curve)
        assert isinstance(result, ReportResult)

    def test_metrics_present(self, equity_curve):
        result = generate_enriched_report(equity_curve)
        assert "total_return" in result.metrics
        assert "cagr" in result.metrics
        assert "volatility" in result.metrics
        assert "sharpe" in result.metrics
        assert "max_drawdown" in result.metrics

    def test_optional_fields_are_none(self, equity_curve):
        result = generate_enriched_report(equity_curve)
        assert result.regime_returns is None
        assert result.stress_results is None
        assert result.trust_score is None

    def test_default_periods_per_year(self, equity_curve):
        result = generate_enriched_report(equity_curve)
        assert result.periods_per_year == 252

    def test_custom_periods_per_year(self, equity_curve):
        result = generate_enriched_report(equity_curve, periods_per_year=12)
        assert result.periods_per_year == 12

    def test_two_values_minimum(self):
        result = generate_enriched_report([100.0, 110.0])
        assert isinstance(result, ReportResult)
        assert result.metrics["total_return"] == pytest.approx(0.1)


# =============================================================================
# SECTION 3 -- REGIME-CONDITIONAL RETURNS
# =============================================================================

class TestRegimeReturns:
    """Test regime_conditional_returns integration."""

    def test_regime_returns_present(self, equity_curve, returns_and_labels):
        returns, labels = returns_and_labels
        result = generate_enriched_report(
            equity_curve,
            returns=returns,
            regime_labels=labels,
        )
        assert result.regime_returns is not None

    def test_regime_keys(self, equity_curve, returns_and_labels):
        returns, labels = returns_and_labels
        result = generate_enriched_report(
            equity_curve, returns=returns, regime_labels=labels,
        )
        assert "RISK_ON" in result.regime_returns
        assert "RISK_OFF" in result.regime_returns
        assert "CRISIS" in result.regime_returns

    def test_regime_inner_keys(self, equity_curve, returns_and_labels):
        returns, labels = returns_and_labels
        result = generate_enriched_report(
            equity_curve, returns=returns, regime_labels=labels,
        )
        for regime_data in result.regime_returns.values():
            assert "mean" in regime_data
            assert "count" in regime_data
            assert "total" in regime_data

    def test_regime_count_matches(self, equity_curve, returns_and_labels):
        returns, labels = returns_and_labels
        result = generate_enriched_report(
            equity_curve, returns=returns, regime_labels=labels,
        )
        assert result.regime_returns["RISK_ON"]["count"] == 3.0
        assert result.regime_returns["RISK_OFF"]["count"] == 3.0
        assert result.regime_returns["CRISIS"]["count"] == 3.0

    def test_other_fields_still_none(self, equity_curve, returns_and_labels):
        returns, labels = returns_and_labels
        result = generate_enriched_report(
            equity_curve, returns=returns, regime_labels=labels,
        )
        assert result.stress_results is None
        assert result.trust_score is None


# =============================================================================
# SECTION 4 -- STRESS TEST RESULTS
# =============================================================================

class TestStressResults:
    """Test stress test results integration."""

    def test_stress_results_present(self, equity_curve, stress_results):
        result = generate_enriched_report(
            equity_curve, stress_results=stress_results,
        )
        assert result.stress_results is not None

    def test_stress_results_is_tuple(self, equity_curve, stress_results):
        result = generate_enriched_report(
            equity_curve, stress_results=stress_results,
        )
        assert isinstance(result.stress_results, tuple)

    def test_stress_results_count(self, equity_curve, stress_results):
        result = generate_enriched_report(
            equity_curve, stress_results=stress_results,
        )
        assert len(result.stress_results) == 2

    def test_stress_results_fields(self, equity_curve, stress_results):
        result = generate_enriched_report(
            equity_curve, stress_results=stress_results,
        )
        first = result.stress_results[0]
        assert first.scenario == "2008_FINANCIAL_CRISIS"
        assert first.pnl_impact == -0.35
        assert first.max_drawdown == 0.45
        assert first.recovery_periods == 120
        assert first.survived is True

    def test_empty_stress_list(self, equity_curve):
        result = generate_enriched_report(
            equity_curve, stress_results=[],
        )
        assert result.stress_results == ()

    def test_other_fields_none(self, equity_curve, stress_results):
        result = generate_enriched_report(
            equity_curve, stress_results=stress_results,
        )
        assert result.regime_returns is None
        assert result.trust_score is None


# =============================================================================
# SECTION 5 -- TRUST SCORE ENGINE
# =============================================================================

class TestTrustScore:
    """Test TrustScoreEngine integration."""

    def test_trust_score_present(self, equity_curve, trust_params):
        result = generate_enriched_report(equity_curve, **trust_params)
        assert result.trust_score is not None

    def test_trust_score_type(self, equity_curve, trust_params):
        result = generate_enriched_report(equity_curve, **trust_params)
        assert isinstance(result.trust_score, TrustScoreResult)

    def test_trust_score_fields(self, equity_curve, trust_params):
        result = generate_enriched_report(equity_curve, **trust_params)
        ts = result.trust_score
        assert 0.0 <= ts.calibration_score <= 1.0
        assert 0.0 <= ts.ood_score <= 1.0
        assert 0.0 <= ts.stability_score <= 1.0
        assert 0.0 <= ts.risk_score <= 1.0
        assert 0.0 <= ts.operational_score <= 1.0
        assert 0.0 <= ts.trust_score <= 1.0
        assert ts.classification in ("HIGH", "MEDIUM", "LOW", "CRITICAL")

    def test_trust_classification(self, equity_curve, trust_params):
        result = generate_enriched_report(equity_curve, **trust_params)
        assert result.trust_score.classification in ("HIGH", "MEDIUM", "LOW", "CRITICAL")

    def test_other_fields_none(self, equity_curve, trust_params):
        result = generate_enriched_report(equity_curve, **trust_params)
        assert result.regime_returns is None
        assert result.stress_results is None


# =============================================================================
# SECTION 6 -- FULL ENRICHED REPORT (all sections)
# =============================================================================

class TestFullEnrichedReport:
    """Test with all optional inputs provided."""

    def test_all_sections_present(
        self, equity_curve, returns_and_labels, stress_results, trust_params
    ):
        returns, labels = returns_and_labels
        result = generate_enriched_report(
            equity_curve,
            returns=returns,
            regime_labels=labels,
            stress_results=stress_results,
            **trust_params,
        )
        assert result.metrics is not None
        assert result.regime_returns is not None
        assert result.stress_results is not None
        assert result.trust_score is not None

    def test_metrics_keys_complete(
        self, equity_curve, returns_and_labels, stress_results, trust_params
    ):
        returns, labels = returns_and_labels
        result = generate_enriched_report(
            equity_curve,
            returns=returns,
            regime_labels=labels,
            stress_results=stress_results,
            **trust_params,
        )
        expected = {"total_return", "cagr", "volatility", "sharpe", "max_drawdown"}
        assert set(result.metrics.keys()) == expected

    def test_full_report_frozen(
        self, equity_curve, returns_and_labels, stress_results, trust_params
    ):
        returns, labels = returns_and_labels
        result = generate_enriched_report(
            equity_curve,
            returns=returns,
            regime_labels=labels,
            stress_results=stress_results,
            **trust_params,
        )
        with pytest.raises(AttributeError):
            result.trust_score = None

    def test_equity_curve_tuple_in_full(
        self, equity_curve, returns_and_labels, stress_results, trust_params
    ):
        returns, labels = returns_and_labels
        result = generate_enriched_report(
            equity_curve,
            returns=returns,
            regime_labels=labels,
            stress_results=stress_results,
            **trust_params,
        )
        assert isinstance(result.equity_curve, tuple)
        assert len(result.equity_curve) == len(equity_curve)


# =============================================================================
# SECTION 7 -- VALIDATION / ERROR HANDLING
# =============================================================================

class TestValidation:
    """Input validation and error handling."""

    def test_empty_equity_curve_raises(self):
        with pytest.raises(ValueError, match="at least 2 values"):
            generate_enriched_report([])

    def test_single_value_raises(self):
        with pytest.raises(ValueError, match="at least 2 values"):
            generate_enriched_report([100.0])

    def test_returns_without_labels_raises(self, equity_curve):
        with pytest.raises(ValueError, match="both be provided"):
            generate_enriched_report(equity_curve, returns=[0.01, 0.02])

    def test_labels_without_returns_raises(self, equity_curve):
        with pytest.raises(ValueError, match="both be provided"):
            generate_enriched_report(
                equity_curve, regime_labels=["RISK_ON", "RISK_OFF"],
            )

    def test_mismatched_returns_labels_raises(self, equity_curve):
        with pytest.raises(ValueError):
            generate_enriched_report(
                equity_curve,
                returns=[0.01, 0.02],
                regime_labels=["RISK_ON"],
            )

    def test_partial_trust_params_raises(self, equity_curve):
        with pytest.raises(ValueError, match="All five trust"):
            generate_enriched_report(
                equity_curve, trust_ece=0.03,
            )

    def test_partial_trust_params_two_raises(self, equity_curve):
        with pytest.raises(ValueError, match="All five trust"):
            generate_enriched_report(
                equity_curve, trust_ece=0.03, trust_ood_recall=0.85,
            )

    def test_partial_trust_params_four_raises(self, equity_curve):
        with pytest.raises(ValueError, match="All five trust"):
            generate_enriched_report(
                equity_curve,
                trust_ece=0.03,
                trust_ood_recall=0.85,
                trust_prediction_variance=0.05,
                trust_drawdown=0.10,
                # trust_uptime missing
            )

    def test_zero_equity_propagates(self):
        with pytest.raises(ValueError):
            generate_enriched_report([100.0, 0.0, 50.0])


# =============================================================================
# SECTION 8 -- BACKWARD COMPATIBILITY
# =============================================================================

class TestBackwardCompatibility:
    """generate_report still works unchanged."""

    def test_generate_report_unchanged(self, equity_curve):
        result = generate_report(equity_curve)
        assert isinstance(result, dict)
        assert "equity_curve" in result
        assert "metrics" in result
        assert "periods_per_year" in result

    def test_generate_report_metrics(self, equity_curve):
        result = generate_report(equity_curve)
        assert "total_return" in result["metrics"]
        assert "sharpe" in result["metrics"]

    def test_generate_report_dict_type(self, equity_curve):
        """generate_report returns dict, not ReportResult."""
        result = generate_report(equity_curve)
        assert not isinstance(result, ReportResult)


# =============================================================================
# SECTION 9 -- DETERMINISM
# =============================================================================

class TestDeterminism:
    """Same inputs produce identical outputs (DET-05)."""

    def test_minimal_deterministic(self, equity_curve):
        r1 = generate_enriched_report(equity_curve)
        r2 = generate_enriched_report(equity_curve)
        assert r1.metrics == r2.metrics
        assert r1.equity_curve == r2.equity_curve

    def test_full_deterministic(
        self, equity_curve, returns_and_labels, stress_results, trust_params
    ):
        returns, labels = returns_and_labels
        r1 = generate_enriched_report(
            equity_curve,
            returns=returns,
            regime_labels=labels,
            stress_results=stress_results,
            **trust_params,
        )
        r2 = generate_enriched_report(
            equity_curve,
            returns=returns,
            regime_labels=labels,
            stress_results=stress_results,
            **trust_params,
        )
        assert r1.metrics == r2.metrics
        assert r1.regime_returns == r2.regime_returns
        assert r1.stress_results == r2.stress_results
        assert r1.trust_score == r2.trust_score

    def test_trust_score_deterministic(self, equity_curve, trust_params):
        r1 = generate_enriched_report(equity_curve, **trust_params)
        r2 = generate_enriched_report(equity_curve, **trust_params)
        assert r1.trust_score.trust_score == r2.trust_score.trust_score
        assert r1.trust_score.classification == r2.trust_score.classification


# =============================================================================
# SECTION 10 -- IMPORT CONTRACT
# =============================================================================

class TestImportContract:
    """Verify public symbols are importable from expected locations."""

    def test_import_from_engine(self):
        from jarvis.report.engine import (
            generate_enriched_report,
            generate_report,
            ReportResult,
        )
        assert callable(generate_enriched_report)
        assert callable(generate_report)

    def test_import_from_package(self):
        from jarvis.report import (
            generate_enriched_report,
            generate_report,
            ReportResult,
        )
        assert callable(generate_enriched_report)
        assert callable(generate_report)

    def test_report_result_in_all(self):
        from jarvis.report import engine
        assert "ReportResult" in engine.__all__
        assert "generate_enriched_report" in engine.__all__
        assert "generate_report" in engine.__all__
