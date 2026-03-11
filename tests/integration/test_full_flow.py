# =============================================================================
# tests/integration/test_full_flow.py — Full Flow Integration Tests
#
# Two integration scenarios verifying determinism across the entire chain:
#   Scenario 1: Single-Asset Pipeline → Backtest → Metrics → Report
#   Scenario 2: Multi-Asset → Walk-Forward → Stress-Scenarios → Report
#
# DETERMINISM: Each scenario is executed twice with identical inputs.
# Bit-identical outputs are asserted (DET-07).
# =============================================================================

from __future__ import annotations

import math
import pytest

from jarvis.core.regime import GlobalRegimeState
from jarvis.backtest.engine import run_backtest
from jarvis.backtest.multi_asset_engine import (
    run_multi_asset_backtest,
    run_multi_asset_walkforward,
    MultiAssetBacktestResult,
    MultiAssetWalkForwardResult,
)
from jarvis.metrics.engine import compute_metrics
from jarvis.report.engine import generate_report
from jarvis.simulation.stress_scenarios import get_scenario


# =============================================================================
# FIXTURES — deterministic data generators (DET-01, DET-06)
# =============================================================================

def _single_asset_returns(n: int = 60) -> list[float]:
    """Generate deterministic single-asset return series."""
    base = [
        0.008, -0.012, 0.015, -0.005, 0.010,
        -0.003, 0.007, -0.009, 0.011, -0.006,
        0.013, -0.008, 0.004, -0.014, 0.009,
        -0.002, 0.016, -0.011, 0.006, -0.007,
    ]
    result = []
    for i in range(n):
        result.append(base[i % len(base)])
    return result


def _single_asset_prices(n: int = 60, start: float = 100.0) -> list[float]:
    """Generate deterministic price series matching returns length."""
    returns = _single_asset_returns(n)
    prices = [start]
    for r in returns[:-1]:
        prices.append(prices[-1] * (1.0 + r))
    # Same length as returns
    assert len(prices) == n
    return prices


def _multi_asset_returns(n: int = 80) -> dict[str, list[float]]:
    """Generate deterministic multi-asset returns for 3 assets."""
    base_a = _single_asset_returns(n)
    # Asset B: shifted pattern
    base_b = [r * 1.2 + 0.001 for r in base_a]
    # Asset C: inverted pattern (low correlation)
    base_c = [-r * 0.8 + 0.002 for r in base_a]
    return {"ASSET_A": base_a, "ASSET_B": base_b, "ASSET_C": base_c}


def _multi_asset_prices(n: int = 80) -> dict[str, list[float]]:
    """Generate deterministic multi-asset price series (same length as returns)."""
    returns = _multi_asset_returns(n)
    prices: dict[str, list[float]] = {}
    starts = {"ASSET_A": 100.0, "ASSET_B": 50.0, "ASSET_C": 200.0}
    for symbol, rets in returns.items():
        p = [starts[symbol]]
        for r in rets[:-1]:
            p.append(p[-1] * (1.0 + r))
        assert len(p) == n
        prices[symbol] = p
    return prices


# =============================================================================
# SCENARIO 1: Single-Asset Pipeline → Backtest → Metrics → Report
# =============================================================================

class TestScenario1SingleAssetFlow:
    """Single-asset: backtest → metrics → report, with determinism check."""

    WINDOW = 20
    INITIAL_CAPITAL = 100_000.0
    REGIME = GlobalRegimeState.RISK_ON
    META_UNCERTAINTY = 0.2
    N = 60

    def _run_full_chain(self):
        """Execute the complete single-asset chain and return all outputs."""
        returns = _single_asset_returns(self.N)
        prices = _single_asset_prices(self.N)

        # Step 1: Backtest
        equity_curve = run_backtest(
            returns_series=returns,
            window=self.WINDOW,
            initial_capital=self.INITIAL_CAPITAL,
            asset_price_series=prices,
            regime=self.REGIME,
            meta_uncertainty=self.META_UNCERTAINTY,
        )

        # Step 2: Metrics
        metrics = compute_metrics(equity_curve=equity_curve)

        # Step 3: Report
        report = generate_report(equity_curve=equity_curve)

        return equity_curve, metrics, report

    # --- Backtest output ---

    def test_backtest_returns_list(self):
        equity_curve, _, _ = self._run_full_chain()
        assert isinstance(equity_curve, list)

    def test_backtest_nonempty(self):
        equity_curve, _, _ = self._run_full_chain()
        assert len(equity_curve) >= 2

    def test_backtest_values_positive(self):
        equity_curve, _, _ = self._run_full_chain()
        for v in equity_curve:
            assert v > 0.0

    def test_backtest_values_finite(self):
        equity_curve, _, _ = self._run_full_chain()
        for v in equity_curve:
            assert math.isfinite(v)

    def test_backtest_first_value_positive(self):
        equity_curve, _, _ = self._run_full_chain()
        assert equity_curve[0] > 0.0

    # --- Metrics output ---

    def test_metrics_keys(self):
        _, metrics, _ = self._run_full_chain()
        expected_keys = {"total_return", "cagr", "volatility", "sharpe", "max_drawdown"}
        assert set(metrics.keys()) == expected_keys

    def test_metrics_values_finite(self):
        _, metrics, _ = self._run_full_chain()
        for key, val in metrics.items():
            assert math.isfinite(val), f"metrics[{key!r}] = {val} is not finite"

    def test_max_drawdown_nonnegative(self):
        _, metrics, _ = self._run_full_chain()
        assert metrics["max_drawdown"] >= 0.0

    def test_max_drawdown_bounded(self):
        _, metrics, _ = self._run_full_chain()
        assert metrics["max_drawdown"] <= 1.0

    # --- Report output ---

    def test_report_keys(self):
        _, _, report = self._run_full_chain()
        assert "equity_curve" in report
        assert "metrics" in report
        assert "periods_per_year" in report

    def test_report_periods_per_year_default(self):
        _, _, report = self._run_full_chain()
        assert report["periods_per_year"] == 252

    def test_report_metrics_match_standalone(self):
        """Report metrics must equal standalone compute_metrics() output."""
        _, metrics, report = self._run_full_chain()
        for key in metrics:
            assert report["metrics"][key] == metrics[key], (
                f"Mismatch on {key}: report={report['metrics'][key]}, "
                f"standalone={metrics[key]}"
            )

    def test_report_equity_curve_matches_backtest(self):
        equity_curve, _, report = self._run_full_chain()
        assert report["equity_curve"] is equity_curve

    # --- Determinism (DET-07) ---

    def test_determinism_equity_curve(self):
        """Two runs with identical inputs must produce bit-identical equity curves."""
        ec1, _, _ = self._run_full_chain()
        ec2, _, _ = self._run_full_chain()
        assert ec1 == ec2

    def test_determinism_metrics(self):
        """Two runs must produce bit-identical metrics."""
        _, m1, _ = self._run_full_chain()
        _, m2, _ = self._run_full_chain()
        assert m1 == m2

    def test_determinism_report(self):
        """Two runs must produce bit-identical reports."""
        _, _, r1 = self._run_full_chain()
        _, _, r2 = self._run_full_chain()
        assert r1["metrics"] == r2["metrics"]
        assert r1["periods_per_year"] == r2["periods_per_year"]

    # --- Cross-layer consistency ---

    def test_equity_curve_length_consistent(self):
        """Equity curve and report equity curve have same length."""
        ec, _, report = self._run_full_chain()
        assert len(ec) == len(report["equity_curve"])


# =============================================================================
# SCENARIO 2: Multi-Asset → Walk-Forward → Stress-Scenarios → Report
# =============================================================================

class TestScenario2MultiAssetFlow:
    """Multi-asset: walk-forward → stress scenarios → report, with determinism."""

    WINDOW = 20
    TRAIN_SIZE = 40
    TEST_SIZE = 20
    STEP = 10
    INITIAL_CAPITAL = 100_000.0
    REGIME = GlobalRegimeState.RISK_ON
    META_UNCERTAINTY = 0.2
    N = 80

    def _run_walkforward_chain(self):
        """Execute multi-asset walk-forward and return result."""
        returns = _multi_asset_returns(self.N)
        prices = _multi_asset_prices(self.N)

        wf_result = run_multi_asset_walkforward(
            asset_returns=returns,
            asset_prices=prices,
            window=self.WINDOW,
            train_size=self.TRAIN_SIZE,
            test_size=self.TEST_SIZE,
            step=self.STEP,
            initial_capital=self.INITIAL_CAPITAL,
            regime=self.REGIME,
            meta_uncertainty=self.META_UNCERTAINTY,
        )
        return wf_result

    def _run_stress_chain(self, scenario_name: str = "2008_FINANCIAL_CRISIS"):
        """Run backtest on a stress scenario and generate report."""
        scenario = get_scenario(scenario_name)
        stress_returns = list(scenario.returns)

        # Need at least window+2 data points for >=2 equity values
        n_needed = self.WINDOW + 2
        if len(stress_returns) < n_needed:
            padding = [0.001] * (n_needed - len(stress_returns))
            stress_returns = padding + stress_returns

        # Build price series from stress returns (same length)
        prices = [100.0]
        for r in stress_returns[:-1]:
            prices.append(prices[-1] * (1.0 + r))
        assert len(prices) == len(stress_returns)

        equity_curve = run_backtest(
            returns_series=stress_returns,
            window=self.WINDOW,
            initial_capital=self.INITIAL_CAPITAL,
            asset_price_series=prices,
            regime=GlobalRegimeState.CRISIS,
            meta_uncertainty=0.5,
        )

        metrics = compute_metrics(equity_curve=equity_curve)
        report = generate_report(equity_curve=equity_curve)
        return scenario, equity_curve, metrics, report

    # --- Walk-forward structure ---

    def test_wf_returns_correct_type(self):
        result = self._run_walkforward_chain()
        assert isinstance(result, MultiAssetWalkForwardResult)

    def test_wf_has_folds(self):
        result = self._run_walkforward_chain()
        assert len(result.folds) >= 1

    def test_wf_folds_have_train_metrics(self):
        result = self._run_walkforward_chain()
        for fold in result.folds:
            assert "sharpe" in fold.train_metrics
            assert isinstance(fold.test_metrics, dict)

    def test_wf_mean_oos_sharpe_finite(self):
        result = self._run_walkforward_chain()
        assert math.isfinite(result.mean_oos_sharpe)

    def test_wf_std_oos_sharpe_nonnegative(self):
        result = self._run_walkforward_chain()
        assert result.std_oos_sharpe >= 0.0

    def test_wf_full_backtest_present(self):
        result = self._run_walkforward_chain()
        assert isinstance(result.full_backtest, MultiAssetBacktestResult)

    def test_wf_full_backtest_has_portfolio_equity(self):
        result = self._run_walkforward_chain()
        assert len(result.full_backtest.portfolio_equity) >= 2

    def test_wf_n_folds_matches_tuple(self):
        result = self._run_walkforward_chain()
        assert result.n_folds == len(result.folds)

    def test_wf_any_overfitting_is_bool(self):
        result = self._run_walkforward_chain()
        assert isinstance(result.any_overfitting, bool)

    # --- Walk-forward report ---

    def test_wf_report_from_full_backtest(self):
        result = self._run_walkforward_chain()
        eq = list(result.full_backtest.portfolio_equity)
        report = generate_report(equity_curve=eq)
        assert "metrics" in report
        assert "equity_curve" in report

    def test_wf_report_metrics_finite(self):
        result = self._run_walkforward_chain()
        eq = list(result.full_backtest.portfolio_equity)
        report = generate_report(equity_curve=eq)
        for key, val in report["metrics"].items():
            assert math.isfinite(val), f"report metrics[{key!r}] not finite"

    # --- Stress scenario ---

    def test_stress_scenario_loads(self):
        scenario = get_scenario("2008_FINANCIAL_CRISIS")
        assert scenario.name == "2008_FINANCIAL_CRISIS"
        assert len(scenario.returns) > 0

    def test_stress_backtest_runs(self):
        _, equity_curve, _, _ = self._run_stress_chain("2008_FINANCIAL_CRISIS")
        assert len(equity_curve) >= 2

    def test_stress_equity_positive(self):
        _, equity_curve, _, _ = self._run_stress_chain("2008_FINANCIAL_CRISIS")
        for v in equity_curve:
            assert v > 0.0

    def test_stress_metrics_valid(self):
        _, _, metrics, _ = self._run_stress_chain("2008_FINANCIAL_CRISIS")
        assert math.isfinite(metrics["sharpe"])
        assert metrics["max_drawdown"] >= 0.0

    def test_stress_report_structure(self):
        _, _, _, report = self._run_stress_chain("2008_FINANCIAL_CRISIS")
        assert "equity_curve" in report
        assert "metrics" in report
        assert "periods_per_year" in report

    def test_stress_covid_scenario(self):
        """COVID scenario also works end-to-end."""
        _, equity_curve, metrics, report = self._run_stress_chain("2020_COVID_CRASH")
        assert len(equity_curve) >= 2
        assert math.isfinite(metrics["sharpe"])
        assert "metrics" in report

    def test_stress_synthetic_vol_shock(self):
        """Synthetic scenario works end-to-end."""
        _, equity_curve, metrics, report = self._run_stress_chain("SYNTHETIC_VOL_SHOCK_3X")
        assert len(equity_curve) >= 2
        assert math.isfinite(metrics["max_drawdown"])

    # --- Determinism (DET-07) ---

    def test_determinism_walkforward(self):
        """Two walk-forward runs with identical inputs produce identical results."""
        r1 = self._run_walkforward_chain()
        r2 = self._run_walkforward_chain()
        assert r1.mean_oos_sharpe == r2.mean_oos_sharpe
        assert r1.std_oos_sharpe == r2.std_oos_sharpe
        assert r1.n_folds == r2.n_folds
        assert r1.any_overfitting == r2.any_overfitting
        # Fold-level
        for f1, f2 in zip(r1.folds, r2.folds):
            assert f1.oos_sharpe == f2.oos_sharpe
            assert f1.train_metrics == f2.train_metrics
            assert f1.test_metrics == f2.test_metrics

    def test_determinism_walkforward_full_backtest(self):
        """Full backtest within walk-forward is deterministic."""
        r1 = self._run_walkforward_chain()
        r2 = self._run_walkforward_chain()
        assert r1.full_backtest.portfolio_equity == r2.full_backtest.portfolio_equity
        assert r1.full_backtest.portfolio_metrics == r2.full_backtest.portfolio_metrics

    def test_determinism_stress_scenario(self):
        """Stress scenario chain is deterministic."""
        _, ec1, m1, rpt1 = self._run_stress_chain("2008_FINANCIAL_CRISIS")
        _, ec2, m2, rpt2 = self._run_stress_chain("2008_FINANCIAL_CRISIS")
        assert ec1 == ec2
        assert m1 == m2
        assert rpt1["metrics"] == rpt2["metrics"]

    def test_determinism_stress_report_exact(self):
        """Report from stress test is bit-identical across runs."""
        _, _, _, rpt1 = self._run_stress_chain("SYNTHETIC_LIQUIDITY_CRISIS")
        _, _, _, rpt2 = self._run_stress_chain("SYNTHETIC_LIQUIDITY_CRISIS")
        assert rpt1["metrics"] == rpt2["metrics"]
        assert rpt1["periods_per_year"] == rpt2["periods_per_year"]

    # --- Cross-scenario consistency ---

    def test_wf_full_backtest_metrics_keys_present(self):
        """Walk-forward full backtest metrics have expected keys."""
        result = self._run_walkforward_chain()
        expected_keys = {"total_return", "cagr", "volatility", "sharpe", "max_drawdown"}
        assert set(result.full_backtest.portfolio_metrics.keys()) == expected_keys

    def test_stress_different_scenarios_differ(self):
        """Different stress scenarios should produce different results."""
        _, ec_2008, _, _ = self._run_stress_chain("2008_FINANCIAL_CRISIS")
        _, ec_covid, _, _ = self._run_stress_chain("2020_COVID_CRASH")
        assert ec_2008 != ec_covid
