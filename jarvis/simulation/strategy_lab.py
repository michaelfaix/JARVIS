# =============================================================================
# jarvis/simulation/strategy_lab.py — Simulation & Strategy Lab (S28)
#
# Vollstaendiges Simulations-Labor:
#   1. Monte Carlo Simulation (Bootstrap, seed-deterministisch)
#   2. Slippage Modeling (base + vol + size)
#   3. Walk-Forward Validation (rollierende OOS-Fenster)
#   4. Stress Test Engine (historisch + synthetisch)
#
# Pflicht vor jedem Deployment.
# =============================================================================

from __future__ import annotations

from dataclasses import dataclass
from typing import Callable, Dict, List, Optional

import numpy as np


# ---------------------------------------------------------------------------
# DATACLASSES
# ---------------------------------------------------------------------------

@dataclass
class MonteCarloResult:
    """Result of a Monte Carlo bootstrap simulation."""

    n_paths: int
    mean_final_pnl: float
    std_final_pnl: float
    var_95: float
    cvar_95: float
    max_drawdown_mean: float
    max_drawdown_p95: float
    win_rate: float


@dataclass
class SlippageModel:
    """Slippage model parameters."""

    base_slippage_pct: float
    vol_multiplier: float
    size_impact: float


@dataclass
class WalkForwardResult:
    """Result of walk-forward validation."""

    n_windows: int
    oos_sharpe_mean: float
    oos_sharpe_std: float
    oos_win_rate: float
    degradation_score: float


@dataclass
class StressTestResult:
    """Result of a stress test scenario."""

    scenario: str
    pnl_impact: float
    max_drawdown: float
    recovery_periods: int
    survived: bool


# ---------------------------------------------------------------------------
# MANDATORY STRESS SCENARIOS
# ---------------------------------------------------------------------------

JARVIS_STRESS_SCENARIOS: List[str] = [
    "2008_FINANCIAL_CRISIS",
    "2020_COVID_CRASH",
    "2010_FLASH_CRASH",
    "SYNTHETIC_VOL_SHOCK_3X",
    "SYNTHETIC_LIQUIDITY_CRISIS",
    "SYNTHETIC_CORRELATION_SHOCK",
]


# ---------------------------------------------------------------------------
# STRATEGY LAB
# ---------------------------------------------------------------------------

class StrategyLab:
    """Vollstaendiges Simulations-Labor. Pflicht vor jedem Deployment."""

    def monte_carlo(
        self,
        strategy_returns: List[float],
        n_paths: int = 10_000,
        n_periods: int = 252,
        seed: int = 42,
    ) -> MonteCarloResult:
        """Monte Carlo Simulation via Bootstrap.

        Seed fix fuer Reproduzierbarkeit (Systemvertrag: deterministisch).

        Args:
            strategy_returns: Historical returns for bootstrapping.
            n_paths: Number of simulation paths.
            n_periods: Number of periods per path.
            seed: Random seed for reproducibility.

        Returns:
            MonteCarloResult with VaR, CVaR, drawdown statistics.

        Raises:
            ValueError: If returns contain NaN/Inf.
        """
        rng = np.random.RandomState(seed)
        arr = np.array(strategy_returns, dtype=float)
        if not np.all(np.isfinite(arr)):
            raise ValueError("Returns enthalten NaN/Inf")

        # Bootstrap: ziehe n_periods aus historischen Returns (mit Zuruecklegen)
        paths = rng.choice(arr, size=(n_paths, n_periods), replace=True)
        cum_returns = np.cumprod(1.0 + paths, axis=1)
        final_pnl = cum_returns[:, -1] - 1.0

        # Drawdown pro Pfad
        running_max = np.maximum.accumulate(cum_returns, axis=1)
        drawdowns = (running_max - cum_returns) / np.maximum(running_max, 1e-10)
        max_dd_per_path = drawdowns.max(axis=1)

        var_95 = float(np.percentile(final_pnl, 5))
        cvar_95 = float(np.mean(final_pnl[final_pnl <= var_95]))

        return MonteCarloResult(
            n_paths=n_paths,
            mean_final_pnl=float(np.mean(final_pnl)),
            std_final_pnl=float(np.std(final_pnl)),
            var_95=var_95,
            cvar_95=cvar_95,
            max_drawdown_mean=float(np.mean(max_dd_per_path)),
            max_drawdown_p95=float(np.percentile(max_dd_per_path, 95)),
            win_rate=float(np.mean(final_pnl > 0)),
        )

    def compute_slippage(
        self,
        model: SlippageModel,
        position_size_pct: float,
        current_volatility: float,
    ) -> float:
        """Slippage-Schaetzung: base + vol-Anteil + Size-Impact.

        Args:
            model: SlippageModel with base, vol, size parameters.
            position_size_pct: Position size in percent.
            current_volatility: Current annualized volatility.

        Returns:
            Total slippage in percent (non-negative).

        Raises:
            ValueError: If inputs are non-finite or negative.
        """
        if not np.isfinite(position_size_pct) or position_size_pct < 0:
            raise ValueError(f"Ungaeltige position_size_pct: {position_size_pct}")
        if not np.isfinite(current_volatility) or current_volatility < 0:
            raise ValueError(f"Ungaeltige Volatilitaet: {current_volatility}")

        vol_component = model.vol_multiplier * current_volatility
        size_component = model.size_impact * position_size_pct
        total_slippage = model.base_slippage_pct + vol_component + size_component
        return float(max(total_slippage, 0.0))

    def walk_forward(
        self,
        returns: List[float],
        strategy_fn: Callable[[List[float]], List[float]],
        n_windows: int = 10,
        train_pct: float = 0.7,
        seed: int = 42,
    ) -> WalkForwardResult:
        """Walk-Forward Validation: rollierendes Trainingsfenster.

        Misst OOS-Performance (Out-of-Sample).

        Args:
            returns: Full return series.
            strategy_fn: Callable that takes train returns, returns OOS returns.
            n_windows: Number of rolling windows.
            train_pct: Fraction of each window used for training.
            seed: Random seed (unused but reserved for consistency).

        Returns:
            WalkForwardResult with OOS Sharpe statistics.

        Raises:
            ValueError: If returns contain NaN/Inf.
            RuntimeError: If no valid windows can be constructed.
        """
        arr = np.array(returns, dtype=float)
        if not np.all(np.isfinite(arr)):
            raise ValueError("Returns enthalten NaN/Inf")

        n_total = len(arr)
        if n_total == 0:
            raise RuntimeError("Walk-Forward: keine gueltigen Fenster")
        window_sz = n_total // n_windows
        oos_sharpes: List[float] = []

        for i in range(n_windows):
            start = i * window_sz
            split = start + int(window_sz * train_pct)
            end = start + window_sz

            if end > n_total:
                break

            train_r = arr[start:split].tolist()
            oos_r = arr[split:end].tolist()

            try:
                strat_oos = strategy_fn(train_r)
                # Sharpe (annualisiert, vereinfacht)
                if len(strat_oos) > 1:
                    oos_arr = np.array(strat_oos)
                    sharpe = (np.mean(oos_arr) / max(np.std(oos_arr), 1e-10)) * np.sqrt(252)
                else:
                    sharpe = 0.0
            except Exception:
                sharpe = -999.0  # Strategie-Fehler = schlechtester Sharpe

            oos_sharpes.append(float(sharpe))

        if not oos_sharpes:
            raise RuntimeError("Walk-Forward: keine gueltigen Fenster")

        oos_arr = np.array(oos_sharpes)
        degrad = float(max(0.0, -np.mean(oos_arr)))

        return WalkForwardResult(
            n_windows=len(oos_sharpes),
            oos_sharpe_mean=float(np.mean(oos_arr)),
            oos_sharpe_std=float(np.std(oos_arr)),
            oos_win_rate=float(np.mean(oos_arr > 0)),
            degradation_score=degrad,
        )

    def stress_test(
        self,
        scenario_name: str,
        scenario_returns: List[float],
        strategy_fn: Callable[[List[float]], List[float]],
        drawdown_limit: float = 0.15,
    ) -> StressTestResult:
        """Stress-Test mit historischen oder synthetischen Krisen-Szenarien.

        Args:
            scenario_name: Name of the stress scenario.
            scenario_returns: Return series representing the crisis.
            strategy_fn: Callable that processes returns.
            drawdown_limit: Maximum allowed drawdown (default 15%).

        Returns:
            StressTestResult with survival assessment.
        """
        try:
            strat_returns = strategy_fn(scenario_returns)
        except Exception:
            return StressTestResult(
                scenario=scenario_name,
                pnl_impact=-1.0,
                max_drawdown=1.0,
                recovery_periods=-1,
                survived=False,
            )

        arr = np.array(strat_returns, dtype=float)
        if not np.all(np.isfinite(arr)):
            arr = np.zeros_like(arr)

        cum = np.cumprod(1.0 + arr)
        run_max = np.maximum.accumulate(cum)
        dd = (run_max - cum) / np.maximum(run_max, 1e-10)
        max_dd = float(np.max(dd))
        pnl = float(cum[-1] - 1.0) if len(cum) > 0 else -1.0

        # Recovery-Perioden: wann ist cum wieder ueber letztem Peak?
        recovery = -1
        peak_val = float(run_max[-1])
        for idx in range(len(cum)):
            if float(cum[idx]) >= peak_val:
                recovery = idx
                break

        return StressTestResult(
            scenario=scenario_name,
            pnl_impact=pnl,
            max_drawdown=max_dd,
            recovery_periods=recovery,
            survived=max_dd < drawdown_limit,
        )
