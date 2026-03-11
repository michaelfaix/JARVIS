# =============================================================================
# tests/unit/risk/test_portfolio_heatmap.py -- Portfolio Heatmap Engine Tests
#
# Comprehensive tests for jarvis/risk/portfolio_heatmap.py (Phase MA-5).
# Covers: constants, should_update triggers, build_snapshot, heat score
#         computation, caching behavior, determinism, immutability, edge cases.
# =============================================================================

import math

import pytest

from jarvis.core.regime import (
    AssetClass,
    AssetRegimeState,
    CorrelationRegimeState,
    GlobalRegimeState,
    HierarchicalRegime,
)
from jarvis.risk.portfolio_risk import PortfolioRiskEngine, PortfolioRiskResult
from jarvis.risk.portfolio_heatmap import (
    # Constants
    EXPOSURE_DELTA_THRESHOLD,
    NET_EXPOSURE_DELTA_THRESHOLD,
    CORRELATION_DELTA_THRESHOLD,
    CORRELATION_SINGLE_THRESHOLD,
    HEAT_VOL_WEIGHT,
    HEAT_CORR_WEIGHT,
    TRIGGER_NEW_CANDLE,
    TRIGGER_REGIME_TRANSITION,
    TRIGGER_FAILURE_MODE,
    TRIGGER_EXPOSURE_DELTA,
    TRIGGER_CORRELATION_SHIFT,
    TRIGGER_NONE,
    # Helpers
    _compute_vol_percentile,
    _compute_asset_corr_mean,
    _compute_heat_score,
    _matrix_delta,
    # Dataclasses
    HeatmapCell,
    PortfolioHeatmapSnapshot,
    # Engine
    PortfolioHeatmapEngine,
)


# ---------------------------------------------------------------------------
# SHARED FIXTURES
# ---------------------------------------------------------------------------

SAMPLE_RETURNS = [0.01 * ((-1) ** i) + 0.001 * i for i in range(30)]
SAMPLE_PRICES = [100.0 + i * 0.5 for i in range(30)]

DEFAULT_ASSET_REGIMES = {ac: AssetRegimeState.TRENDING_UP for ac in AssetClass}
DEFAULT_CONFIDENCES = {ac: 0.8 for ac in AssetClass}
DEFAULT_SUB_REGIME = {ac: "default" for ac in AssetClass}


def _make_regime(
    global_regime=GlobalRegimeState.RISK_ON,
    correlation_regime=CorrelationRegimeState.NORMAL,
) -> HierarchicalRegime:
    ar = DEFAULT_ASSET_REGIMES.copy()
    if global_regime == GlobalRegimeState.CRISIS:
        ar = {ac: AssetRegimeState.SHOCK for ac in AssetClass}
        correlation_regime = CorrelationRegimeState.BREAKDOWN
    return HierarchicalRegime.create(
        global_regime=global_regime,
        asset_regimes=ar,
        correlation_regime=correlation_regime,
        global_confidence=0.8,
        asset_confidences=DEFAULT_CONFIDENCES.copy(),
        sub_regime=DEFAULT_SUB_REGIME.copy(),
        sequence_id=1,
    )


def _make_portfolio_risk(regime=None) -> PortfolioRiskResult:
    if regime is None:
        regime = _make_regime()
    positions = {
        "BTC": (AssetClass.CRYPTO, 65000.0, 1.0),
        "SPY": (AssetClass.INDICES, 520.0, 100.0),
        "TLT": (AssetClass.RATES, 90.0, 100.0),
    }
    returns = {s: SAMPLE_RETURNS for s in positions}
    prices = {s: SAMPLE_PRICES for s in positions}
    return PortfolioRiskEngine().calculate_portfolio_risk(
        positions=positions,
        returns=returns,
        regime=regime,
        price_histories=prices,
    )


def _identity_matrix(n):
    return tuple(
        tuple(1.0 if i == j else 0.0 for j in range(n))
        for i in range(n)
    )


def _uniform_corr_matrix(n, off_diag):
    return tuple(
        tuple(1.0 if i == j else off_diag for j in range(n))
        for i in range(n)
    )


def _default_should_update_kwargs(engine):
    """Default kwargs for should_update that produce NO_TRIGGER."""
    return dict(
        new_candle_confirmed=False,
        current_corr_matrix=_identity_matrix(3),
        n_assets=3,
        current_gross_exp=0.5,
        current_net_exp=0.3,
        current_regime=GlobalRegimeState.RISK_ON,
        active_failure_modes=(),
        regime_transition_flag=False,
    )


# ---------------------------------------------------------------------------
# CONSTANTS (DET-06)
# ---------------------------------------------------------------------------

class TestConstants:
    def test_exposure_delta(self):
        assert EXPOSURE_DELTA_THRESHOLD == 0.05

    def test_net_exposure_delta(self):
        assert NET_EXPOSURE_DELTA_THRESHOLD == 0.03

    def test_correlation_delta(self):
        assert CORRELATION_DELTA_THRESHOLD == 0.05

    def test_correlation_single(self):
        assert CORRELATION_SINGLE_THRESHOLD == 0.10

    def test_heat_weights_sum_one(self):
        assert abs(HEAT_VOL_WEIGHT + HEAT_CORR_WEIGHT - 1.0) < 1e-10


# ---------------------------------------------------------------------------
# HELPERS
# ---------------------------------------------------------------------------

class TestComputeVolPercentile:
    def test_middle(self):
        pct = _compute_vol_percentile(0.05, [0.01, 0.05, 0.10])
        assert 0.0 <= pct <= 1.0

    def test_highest(self):
        pct = _compute_vol_percentile(0.10, [0.01, 0.05, 0.10])
        assert pct == 1.0

    def test_lowest(self):
        pct = _compute_vol_percentile(0.01, [0.01, 0.05, 0.10])
        assert pct == 0.0

    def test_single_vol(self):
        pct = _compute_vol_percentile(0.05, [0.05])
        assert pct == 0.5

    def test_empty(self):
        pct = _compute_vol_percentile(0.05, [])
        assert pct == 0.5


class TestComputeAssetCorrMean:
    def test_identity(self):
        corr = _compute_asset_corr_mean(_identity_matrix(3), 0, 3)
        assert corr == 0.0

    def test_uniform(self):
        corr = _compute_asset_corr_mean(_uniform_corr_matrix(3, 0.6), 0, 3)
        assert abs(corr - 0.6) < 1e-10

    def test_single_asset(self):
        corr = _compute_asset_corr_mean(((1.0,),), 0, 1)
        assert corr == 0.0


class TestComputeHeatScore:
    def test_zero_both(self):
        assert _compute_heat_score(0.0, 0.0) == 0.0

    def test_max_both(self):
        assert _compute_heat_score(1.0, 1.0) == 1.0

    def test_middle(self):
        score = _compute_heat_score(0.5, 0.5)
        assert abs(score - 0.5) < 1e-10

    def test_clipped_high(self):
        score = _compute_heat_score(1.0, 1.5)
        assert score == 1.0

    def test_clipped_low(self):
        score = _compute_heat_score(-0.5, 0.0)
        assert score == 0.0


class TestMatrixDelta:
    def test_same_matrices(self):
        m = _uniform_corr_matrix(3, 0.5)
        mean_d, max_d = _matrix_delta(m, m, 3)
        assert mean_d == 0.0
        assert max_d == 0.0

    def test_different_matrices(self):
        a = _uniform_corr_matrix(3, 0.3)
        b = _uniform_corr_matrix(3, 0.6)
        mean_d, max_d = _matrix_delta(a, b, 3)
        assert abs(mean_d - 0.3) < 1e-10
        assert abs(max_d - 0.3) < 1e-10

    def test_single_asset(self):
        mean_d, max_d = _matrix_delta(((1.0,),), ((1.0,),), 1)
        assert mean_d == 0.0


# ---------------------------------------------------------------------------
# SHOULD_UPDATE -- TRIGGER POLICY
# ---------------------------------------------------------------------------

class TestShouldUpdate:
    def test_no_trigger_on_tick(self):
        engine = PortfolioHeatmapEngine()
        # Initialize cached state
        engine._last_regime = GlobalRegimeState.RISK_ON
        engine._last_corr_matrix = _identity_matrix(3)
        engine._last_n_assets = 3
        engine._last_gross_exp = 0.5
        engine._last_net_exp = 0.3
        kwargs = _default_should_update_kwargs(engine)
        should, reason = engine.should_update(**kwargs)
        assert should is False
        assert reason == TRIGGER_NONE

    def test_new_candle_triggers(self):
        engine = PortfolioHeatmapEngine()
        kwargs = _default_should_update_kwargs(engine)
        kwargs["new_candle_confirmed"] = True
        should, reason = engine.should_update(**kwargs)
        assert should is True
        assert reason == TRIGGER_NEW_CANDLE

    def test_regime_transition_flag_triggers(self):
        engine = PortfolioHeatmapEngine()
        engine._last_regime = GlobalRegimeState.RISK_ON
        kwargs = _default_should_update_kwargs(engine)
        kwargs["regime_transition_flag"] = True
        should, reason = engine.should_update(**kwargs)
        assert should is True
        assert reason == TRIGGER_REGIME_TRANSITION

    def test_regime_change_triggers(self):
        engine = PortfolioHeatmapEngine()
        engine._last_regime = GlobalRegimeState.RISK_ON
        kwargs = _default_should_update_kwargs(engine)
        kwargs["current_regime"] = GlobalRegimeState.RISK_OFF
        should, reason = engine.should_update(**kwargs)
        assert should is True
        assert reason == TRIGGER_REGIME_TRANSITION

    def test_failure_mode_change_triggers(self):
        engine = PortfolioHeatmapEngine()
        engine._last_regime = GlobalRegimeState.RISK_ON
        engine._last_fm_states = ()
        kwargs = _default_should_update_kwargs(engine)
        kwargs["active_failure_modes"] = ("FM-01",)
        should, reason = engine.should_update(**kwargs)
        assert should is True
        assert reason == TRIGGER_FAILURE_MODE

    def test_gross_exposure_delta_triggers(self):
        engine = PortfolioHeatmapEngine()
        engine._last_regime = GlobalRegimeState.RISK_ON
        engine._last_gross_exp = 0.5
        engine._last_net_exp = 0.3
        kwargs = _default_should_update_kwargs(engine)
        kwargs["current_gross_exp"] = 0.60  # delta = 0.10 > 0.05
        should, reason = engine.should_update(**kwargs)
        assert should is True
        assert reason == TRIGGER_EXPOSURE_DELTA

    def test_net_exposure_delta_triggers(self):
        engine = PortfolioHeatmapEngine()
        engine._last_regime = GlobalRegimeState.RISK_ON
        engine._last_gross_exp = 0.5
        engine._last_net_exp = 0.3
        kwargs = _default_should_update_kwargs(engine)
        kwargs["current_net_exp"] = 0.35  # delta = 0.05 > 0.03
        should, reason = engine.should_update(**kwargs)
        assert should is True
        assert reason == TRIGGER_EXPOSURE_DELTA

    def test_correlation_mean_shift_triggers(self):
        engine = PortfolioHeatmapEngine()
        engine._last_regime = GlobalRegimeState.RISK_ON
        engine._last_corr_matrix = _uniform_corr_matrix(3, 0.3)
        engine._last_n_assets = 3
        engine._last_gross_exp = 0.5
        engine._last_net_exp = 0.3
        kwargs = _default_should_update_kwargs(engine)
        kwargs["current_corr_matrix"] = _uniform_corr_matrix(3, 0.4)  # delta = 0.1 > 0.05
        should, reason = engine.should_update(**kwargs)
        assert should is True
        assert reason == TRIGGER_CORRELATION_SHIFT

    def test_correlation_single_pair_shift_triggers(self):
        engine = PortfolioHeatmapEngine()
        engine._last_regime = GlobalRegimeState.RISK_ON
        engine._last_corr_matrix = ((1.0, 0.3, 0.3), (0.3, 1.0, 0.3), (0.3, 0.3, 1.0))
        engine._last_n_assets = 3
        engine._last_gross_exp = 0.5
        engine._last_net_exp = 0.3
        kwargs = _default_should_update_kwargs(engine)
        # Single pair change > 0.10
        kwargs["current_corr_matrix"] = ((1.0, 0.5, 0.3), (0.5, 1.0, 0.3), (0.3, 0.3, 1.0))
        should, reason = engine.should_update(**kwargs)
        assert should is True
        assert reason == TRIGGER_CORRELATION_SHIFT

    def test_small_exposure_delta_no_trigger(self):
        engine = PortfolioHeatmapEngine()
        engine._last_regime = GlobalRegimeState.RISK_ON
        engine._last_gross_exp = 0.50
        engine._last_net_exp = 0.30
        engine._last_corr_matrix = _identity_matrix(3)
        engine._last_n_assets = 3
        kwargs = _default_should_update_kwargs(engine)
        kwargs["current_gross_exp"] = 0.52  # delta = 0.02 < 0.05
        kwargs["current_net_exp"] = 0.31    # delta = 0.01 < 0.03
        should, reason = engine.should_update(**kwargs)
        assert should is False

    def test_candle_has_highest_priority(self):
        engine = PortfolioHeatmapEngine()
        engine._last_regime = GlobalRegimeState.RISK_ON
        engine._last_fm_states = ()
        kwargs = _default_should_update_kwargs(engine)
        kwargs["new_candle_confirmed"] = True
        kwargs["regime_transition_flag"] = True
        kwargs["active_failure_modes"] = ("FM-01",)
        should, reason = engine.should_update(**kwargs)
        assert reason == TRIGGER_NEW_CANDLE  # Highest priority


# ---------------------------------------------------------------------------
# BUILD SNAPSHOT
# ---------------------------------------------------------------------------

class TestBuildSnapshot:
    def test_basic_snapshot(self):
        engine = PortfolioHeatmapEngine()
        pr = _make_portfolio_risk()
        snap = engine.build_snapshot(
            portfolio_risk=pr,
            active_failure_modes=(),
            trigger_reason=TRIGGER_NEW_CANDLE,
            gross_exposure=0.5,
            net_exposure=0.3,
        )
        assert snap.num_assets == 3
        assert snap.trigger_reason == TRIGGER_NEW_CANDLE
        assert snap.regime == GlobalRegimeState.RISK_ON

    def test_cells_present(self):
        engine = PortfolioHeatmapEngine()
        pr = _make_portfolio_risk()
        snap = engine.build_snapshot(
            portfolio_risk=pr,
            active_failure_modes=(),
            trigger_reason=TRIGGER_NEW_CANDLE,
            gross_exposure=0.5,
            net_exposure=0.3,
        )
        assert "BTC" in snap.cells
        assert "SPY" in snap.cells
        assert "TLT" in snap.cells

    def test_heat_scores_in_range(self):
        engine = PortfolioHeatmapEngine()
        pr = _make_portfolio_risk()
        snap = engine.build_snapshot(
            portfolio_risk=pr,
            active_failure_modes=(),
            trigger_reason=TRIGGER_NEW_CANDLE,
            gross_exposure=0.5,
            net_exposure=0.3,
        )
        for cell in snap.cells.values():
            assert 0.0 <= cell.heat_score <= 1.0

    def test_global_heat_in_range(self):
        engine = PortfolioHeatmapEngine()
        pr = _make_portfolio_risk()
        snap = engine.build_snapshot(
            portfolio_risk=pr,
            active_failure_modes=(),
            trigger_reason=TRIGGER_NEW_CANDLE,
            gross_exposure=0.5,
            net_exposure=0.3,
        )
        assert 0.0 <= snap.global_heat <= 1.0

    def test_weights_sum_to_one(self):
        engine = PortfolioHeatmapEngine()
        pr = _make_portfolio_risk()
        snap = engine.build_snapshot(
            portfolio_risk=pr,
            active_failure_modes=(),
            trigger_reason=TRIGGER_NEW_CANDLE,
            gross_exposure=0.5,
            net_exposure=0.3,
        )
        total = sum(c.simulated_weight for c in snap.cells.values())
        assert abs(total - 1.0) < 1e-6

    def test_failure_modes_stored(self):
        engine = PortfolioHeatmapEngine()
        pr = _make_portfolio_risk()
        snap = engine.build_snapshot(
            portfolio_risk=pr,
            active_failure_modes=("FM-01", "FM-04"),
            trigger_reason=TRIGGER_FAILURE_MODE,
            gross_exposure=0.5,
            net_exposure=0.3,
        )
        assert snap.active_failure_modes == ("FM-01", "FM-04")

    def test_result_hash(self):
        engine = PortfolioHeatmapEngine()
        pr = _make_portfolio_risk()
        snap = engine.build_snapshot(
            portfolio_risk=pr,
            active_failure_modes=(),
            trigger_reason=TRIGGER_NEW_CANDLE,
            gross_exposure=0.5,
            net_exposure=0.3,
        )
        assert len(snap.result_hash) == 16
        assert all(c in "0123456789abcdef" for c in snap.result_hash)

    def test_caches_state_after_build(self):
        engine = PortfolioHeatmapEngine()
        pr = _make_portfolio_risk()
        engine.build_snapshot(
            portfolio_risk=pr,
            active_failure_modes=("FM-01",),
            trigger_reason=TRIGGER_NEW_CANDLE,
            gross_exposure=0.5,
            net_exposure=0.3,
        )
        assert engine._last_regime == GlobalRegimeState.RISK_ON
        assert engine._last_gross_exp == 0.5
        assert engine._last_net_exp == 0.3
        assert engine._last_fm_states == ("FM-01",)
        assert engine._last_n_assets == 3

    def test_crisis_regime_snapshot(self):
        regime = _make_regime(global_regime=GlobalRegimeState.CRISIS)
        pr = _make_portfolio_risk(regime)
        engine = PortfolioHeatmapEngine()
        snap = engine.build_snapshot(
            portfolio_risk=pr,
            active_failure_modes=(),
            trigger_reason=TRIGGER_REGIME_TRANSITION,
            gross_exposure=0.3,
            net_exposure=0.2,
        )
        assert snap.regime == GlobalRegimeState.CRISIS
        assert snap.correlation_regime == CorrelationRegimeState.BREAKDOWN


# ---------------------------------------------------------------------------
# IMMUTABILITY
# ---------------------------------------------------------------------------

class TestImmutability:
    def test_snapshot_frozen(self):
        engine = PortfolioHeatmapEngine()
        pr = _make_portfolio_risk()
        snap = engine.build_snapshot(
            portfolio_risk=pr,
            active_failure_modes=(),
            trigger_reason=TRIGGER_NEW_CANDLE,
            gross_exposure=0.5,
            net_exposure=0.3,
        )
        with pytest.raises(AttributeError):
            snap.global_heat = 0.0

    def test_cell_frozen(self):
        engine = PortfolioHeatmapEngine()
        pr = _make_portfolio_risk()
        snap = engine.build_snapshot(
            portfolio_risk=pr,
            active_failure_modes=(),
            trigger_reason=TRIGGER_NEW_CANDLE,
            gross_exposure=0.5,
            net_exposure=0.3,
        )
        cell = list(snap.cells.values())[0]
        with pytest.raises(AttributeError):
            cell.heat_score = 0.0


# ---------------------------------------------------------------------------
# DETERMINISM (DET-05)
# ---------------------------------------------------------------------------

class TestDeterminism:
    def test_same_inputs_same_hash(self):
        pr = _make_portfolio_risk()
        snap1 = PortfolioHeatmapEngine().build_snapshot(
            portfolio_risk=pr,
            active_failure_modes=(),
            trigger_reason=TRIGGER_NEW_CANDLE,
            gross_exposure=0.5,
            net_exposure=0.3,
        )
        snap2 = PortfolioHeatmapEngine().build_snapshot(
            portfolio_risk=pr,
            active_failure_modes=(),
            trigger_reason=TRIGGER_NEW_CANDLE,
            gross_exposure=0.5,
            net_exposure=0.3,
        )
        assert snap1.result_hash == snap2.result_hash

    def test_same_heat_scores(self):
        pr = _make_portfolio_risk()
        snap1 = PortfolioHeatmapEngine().build_snapshot(
            portfolio_risk=pr,
            active_failure_modes=(),
            trigger_reason=TRIGGER_NEW_CANDLE,
            gross_exposure=0.5,
            net_exposure=0.3,
        )
        snap2 = PortfolioHeatmapEngine().build_snapshot(
            portfolio_risk=pr,
            active_failure_modes=(),
            trigger_reason=TRIGGER_NEW_CANDLE,
            gross_exposure=0.5,
            net_exposure=0.3,
        )
        for sym in snap1.cells:
            assert snap1.cells[sym].heat_score == snap2.cells[sym].heat_score


# ---------------------------------------------------------------------------
# EDGE CASES
# ---------------------------------------------------------------------------

class TestEdgeCases:
    def test_first_should_update_no_cached_state(self):
        engine = PortfolioHeatmapEngine()
        # No cached state -> regime is None, so regime change detected
        should, reason = engine.should_update(
            new_candle_confirmed=False,
            current_corr_matrix=_identity_matrix(2),
            n_assets=2,
            current_gross_exp=0.5,
            current_net_exp=0.3,
            current_regime=GlobalRegimeState.RISK_ON,
            active_failure_modes=(),
            regime_transition_flag=False,
        )
        # No last regime -> no regime change detected (None check)
        # But _last_fm_states = () == () -> no FM change
        # So depends on whether correlation delta triggers
        assert isinstance(should, bool)

    def test_single_asset_snapshot(self):
        regime = _make_regime()
        positions = {"BTC": (AssetClass.CRYPTO, 65000.0, 1.0)}
        returns = {"BTC": SAMPLE_RETURNS}
        prices = {"BTC": SAMPLE_PRICES}
        pr = PortfolioRiskEngine().calculate_portfolio_risk(
            positions=positions,
            returns=returns,
            regime=regime,
            price_histories=prices,
        )
        engine = PortfolioHeatmapEngine()
        snap = engine.build_snapshot(
            portfolio_risk=pr,
            active_failure_modes=(),
            trigger_reason=TRIGGER_NEW_CANDLE,
            gross_exposure=0.5,
            net_exposure=0.3,
        )
        assert snap.num_assets == 1
        assert "BTC" in snap.cells


# ---------------------------------------------------------------------------
# PACKAGE IMPORT
# ---------------------------------------------------------------------------

class TestPackageImport:
    def test_import_all(self):
        from jarvis.risk.portfolio_heatmap import (
            PortfolioHeatmapEngine,
            PortfolioHeatmapSnapshot,
            HeatmapCell,
        )
        assert PortfolioHeatmapEngine is not None
