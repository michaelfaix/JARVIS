# =============================================================================
# tests/unit/simulation/test_regime_aware_stress.py
#
# Tests for RegimeAwareScenario, regime sequences, get_regime_aware_scenario(),
# and run_regime_aware_stress_test() in jarvis/simulation/stress_scenarios.py.
# =============================================================================

from __future__ import annotations

import math

import pytest

from jarvis.core.regime import GlobalRegimeState
from jarvis.simulation.stress_scenarios import (
    # Original presets (for cross-reference)
    FINANCIAL_CRISIS_2008,
    COVID_CRASH_2020,
    FLASH_CRASH_2010,
    DOTCOM_BUST_2000,
    BLACK_MONDAY_1987,
    SYNTHETIC_VOL_SHOCK_3X,
    SYNTHETIC_LIQUIDITY_CRISIS,
    SYNTHETIC_CORRELATION_SHOCK,
    SCENARIO_REGISTRY,
    # Regime-aware types
    RegimeAwareScenario,
    RegimeAwareStressResult,
    REGIME_AWARE_REGISTRY,
    get_regime_aware_scenario,
    run_regime_aware_stress_test,
    # Individual presets
    REGIME_AWARE_2008,
    REGIME_AWARE_COVID,
    REGIME_AWARE_FLASH,
    REGIME_AWARE_DOTCOM,
    REGIME_AWARE_BLACK_MONDAY,
    REGIME_AWARE_VOL_SHOCK,
    REGIME_AWARE_LIQUIDITY,
    REGIME_AWARE_CORR_SHOCK,
)


ALL_REGIME_AWARE = (
    REGIME_AWARE_2008,
    REGIME_AWARE_COVID,
    REGIME_AWARE_FLASH,
    REGIME_AWARE_DOTCOM,
    REGIME_AWARE_BLACK_MONDAY,
    REGIME_AWARE_VOL_SHOCK,
    REGIME_AWARE_LIQUIDITY,
    REGIME_AWARE_CORR_SHOCK,
)

_RS = GlobalRegimeState


# =============================================================================
# SECTION 1 -- RegimeAwareScenario DATACLASS
# =============================================================================

class TestRegimeAwareScenarioFrozen:
    def test_frozen_preset(self):
        with pytest.raises(AttributeError):
            REGIME_AWARE_2008.preset = FINANCIAL_CRISIS_2008

    def test_frozen_regime_sequence(self):
        with pytest.raises(AttributeError):
            REGIME_AWARE_2008.regime_sequence = ()

    def test_regime_sequence_is_tuple(self):
        for ra in ALL_REGIME_AWARE:
            assert isinstance(ra.regime_sequence, tuple), ra.preset.name


class TestRegimeAwareScenarioFields:
    def test_preset_is_stress_preset(self):
        for ra in ALL_REGIME_AWARE:
            assert ra.preset.name in SCENARIO_REGISTRY

    def test_regime_sequence_length_matches_returns(self):
        for ra in ALL_REGIME_AWARE:
            assert len(ra.regime_sequence) == len(ra.preset.returns), (
                f"{ra.preset.name}: regime len={len(ra.regime_sequence)} "
                f"!= returns len={len(ra.preset.returns)}"
            )

    def test_all_regime_entries_are_global_regime_state(self):
        for ra in ALL_REGIME_AWARE:
            for i, regime in enumerate(ra.regime_sequence):
                assert isinstance(regime, GlobalRegimeState), (
                    f"{ra.preset.name}[{i}]: {regime} not GlobalRegimeState"
                )


# =============================================================================
# SECTION 2 -- REGIME SEQUENCE CHARACTERISTICS
# =============================================================================

class TestRegimeSequence2008:
    def test_starts_risk_on(self):
        assert REGIME_AWARE_2008.regime_sequence[0] == _RS.RISK_ON

    def test_contains_crisis(self):
        assert _RS.CRISIS in REGIME_AWARE_2008.regime_sequence

    def test_contains_risk_off(self):
        assert _RS.RISK_OFF in REGIME_AWARE_2008.regime_sequence

    def test_has_transitions(self):
        seq = REGIME_AWARE_2008.regime_sequence
        changes = sum(1 for i in range(1, len(seq)) if seq[i] != seq[i - 1])
        assert changes >= 2

    def test_length_44(self):
        assert len(REGIME_AWARE_2008.regime_sequence) == 44


class TestRegimeSequenceCovid:
    def test_starts_risk_on(self):
        assert REGIME_AWARE_COVID.regime_sequence[0] == _RS.RISK_ON

    def test_contains_crisis(self):
        assert _RS.CRISIS in REGIME_AWARE_COVID.regime_sequence

    def test_ends_risk_off(self):
        assert REGIME_AWARE_COVID.regime_sequence[-1] == _RS.RISK_OFF

    def test_length_23(self):
        assert len(REGIME_AWARE_COVID.regime_sequence) == 23


class TestRegimeSequenceFlash:
    def test_contains_crisis(self):
        assert _RS.CRISIS in REGIME_AWARE_FLASH.regime_sequence

    def test_short_crisis_phase(self):
        crisis_count = sum(
            1 for r in REGIME_AWARE_FLASH.regime_sequence if r == _RS.CRISIS
        )
        assert crisis_count <= 3

    def test_length_10(self):
        assert len(REGIME_AWARE_FLASH.regime_sequence) == 10


class TestRegimeSequenceDotcom:
    def test_contains_transition(self):
        assert _RS.TRANSITION in REGIME_AWARE_DOTCOM.regime_sequence

    def test_contains_crisis(self):
        assert _RS.CRISIS in REGIME_AWARE_DOTCOM.regime_sequence

    def test_length_40(self):
        assert len(REGIME_AWARE_DOTCOM.regime_sequence) == 40


class TestRegimeSequenceBlackMonday:
    def test_contains_crisis(self):
        assert _RS.CRISIS in REGIME_AWARE_BLACK_MONDAY.regime_sequence

    def test_starts_risk_on(self):
        assert REGIME_AWARE_BLACK_MONDAY.regime_sequence[0] == _RS.RISK_ON

    def test_length_10(self):
        assert len(REGIME_AWARE_BLACK_MONDAY.regime_sequence) == 10


class TestRegimeSequenceSynthetic:
    def test_vol_shock_uniform_risk_off(self):
        assert all(
            r == _RS.RISK_OFF for r in REGIME_AWARE_VOL_SHOCK.regime_sequence
        )

    def test_liquidity_uniform_crisis(self):
        assert all(
            r == _RS.CRISIS for r in REGIME_AWARE_LIQUIDITY.regime_sequence
        )

    def test_corr_shock_uniform_crisis(self):
        assert all(
            r == _RS.CRISIS for r in REGIME_AWARE_CORR_SHOCK.regime_sequence
        )


# =============================================================================
# SECTION 3 -- REGIME-AWARE REGISTRY
# =============================================================================

class TestRegimeAwareRegistry:
    def test_eight_entries(self):
        assert len(REGIME_AWARE_REGISTRY) == 8

    def test_keys_match_scenario_registry(self):
        assert set(REGIME_AWARE_REGISTRY.keys()) == set(SCENARIO_REGISTRY.keys())

    def test_all_values_are_regime_aware(self):
        for name, ra in REGIME_AWARE_REGISTRY.items():
            assert isinstance(ra, RegimeAwareScenario)

    def test_preset_names_match_keys(self):
        for name, ra in REGIME_AWARE_REGISTRY.items():
            assert ra.preset.name == name


# =============================================================================
# SECTION 4 -- get_regime_aware_scenario()
# =============================================================================

class TestGetRegimeAwareScenario:
    def test_valid_name(self):
        ra = get_regime_aware_scenario("2008_FINANCIAL_CRISIS")
        assert ra is REGIME_AWARE_2008

    def test_all_registered(self):
        for name in REGIME_AWARE_REGISTRY:
            ra = get_regime_aware_scenario(name)
            assert ra.preset.name == name

    def test_unknown_raises_value_error(self):
        with pytest.raises(ValueError, match="Unknown regime-aware scenario"):
            get_regime_aware_scenario("NONEXISTENT")

    def test_error_lists_available(self):
        with pytest.raises(ValueError, match="Available"):
            get_regime_aware_scenario("BAD_NAME")

    def test_type_error_int(self):
        with pytest.raises(TypeError, match="name must be a string"):
            get_regime_aware_scenario(123)

    def test_type_error_none(self):
        with pytest.raises(TypeError, match="name must be a string"):
            get_regime_aware_scenario(None)

    def test_case_sensitive(self):
        with pytest.raises(ValueError):
            get_regime_aware_scenario("2008_financial_crisis")


# =============================================================================
# SECTION 5 -- RegimeAwareStressResult DATACLASS
# =============================================================================

class TestRegimeAwareStressResultFrozen:
    def test_frozen(self):
        result = run_regime_aware_stress_test(REGIME_AWARE_2008)
        with pytest.raises(AttributeError):
            result.scenario_name = "CHANGED"

    def test_frozen_equity(self):
        result = run_regime_aware_stress_test(REGIME_AWARE_2008)
        with pytest.raises(AttributeError):
            result.equity_curve = ()


class TestRegimeAwareStressResultFields:
    def test_all_fields_present(self):
        result = run_regime_aware_stress_test(REGIME_AWARE_2008)
        assert isinstance(result.scenario_name, str)
        assert isinstance(result.equity_curve, tuple)
        assert isinstance(result.regime_sequence, tuple)
        assert isinstance(result.peak_drawdown, float)
        assert isinstance(result.final_equity, float)
        assert isinstance(result.n_regime_changes, int)

    def test_scenario_name_matches(self):
        result = run_regime_aware_stress_test(REGIME_AWARE_2008)
        assert result.scenario_name == "2008_FINANCIAL_CRISIS"

    def test_regime_sequence_matches_input(self):
        result = run_regime_aware_stress_test(REGIME_AWARE_2008)
        assert result.regime_sequence == REGIME_AWARE_2008.regime_sequence


# =============================================================================
# SECTION 6 -- run_regime_aware_stress_test() VALIDATION
# =============================================================================

class TestRunValidation:
    def test_type_error_non_scenario(self):
        with pytest.raises(TypeError, match="RegimeAwareScenario"):
            run_regime_aware_stress_test("not_a_scenario")

    def test_type_error_plain_preset(self):
        with pytest.raises(TypeError):
            run_regime_aware_stress_test(FINANCIAL_CRISIS_2008)

    def test_window_too_small(self):
        with pytest.raises(ValueError, match="window must be >= 20"):
            run_regime_aware_stress_test(REGIME_AWARE_2008, window=5)

    def test_negative_capital(self):
        with pytest.raises(ValueError, match="initial_capital must be > 0"):
            run_regime_aware_stress_test(
                REGIME_AWARE_2008, initial_capital=-100.0
            )

    def test_zero_capital(self):
        with pytest.raises(ValueError, match="initial_capital must be > 0"):
            run_regime_aware_stress_test(
                REGIME_AWARE_2008, initial_capital=0.0
            )

    def test_meta_uncertainty_below_range(self):
        with pytest.raises(ValueError, match="meta_uncertainty"):
            run_regime_aware_stress_test(
                REGIME_AWARE_2008, meta_uncertainty=-0.1
            )

    def test_meta_uncertainty_above_range(self):
        with pytest.raises(ValueError, match="meta_uncertainty"):
            run_regime_aware_stress_test(
                REGIME_AWARE_2008, meta_uncertainty=1.5
            )

    def test_asset_price_start_zero(self):
        with pytest.raises(ValueError, match="asset_price_start"):
            run_regime_aware_stress_test(
                REGIME_AWARE_2008, asset_price_start=0.0
            )

    def test_mismatched_lengths(self):
        bad = RegimeAwareScenario(
            preset=FINANCIAL_CRISIS_2008,
            regime_sequence=(_RS.RISK_ON, _RS.CRISIS),  # wrong length
        )
        with pytest.raises(ValueError, match="regime_sequence length"):
            run_regime_aware_stress_test(bad)


# =============================================================================
# SECTION 7 -- run_regime_aware_stress_test() EXECUTION
# =============================================================================

class TestRunExecution2008:
    """2008 Financial Crisis: 44 days, window=20, yields 24 equity points."""

    def test_equity_curve_nonempty(self):
        result = run_regime_aware_stress_test(REGIME_AWARE_2008)
        assert len(result.equity_curve) > 0

    def test_equity_curve_length(self):
        result = run_regime_aware_stress_test(REGIME_AWARE_2008)
        expected = len(REGIME_AWARE_2008.preset.returns) - 20
        assert len(result.equity_curve) == expected

    def test_equity_values_positive(self):
        result = run_regime_aware_stress_test(REGIME_AWARE_2008)
        for v in result.equity_curve:
            assert v > 0.0

    def test_equity_values_finite(self):
        result = run_regime_aware_stress_test(REGIME_AWARE_2008)
        for v in result.equity_curve:
            assert math.isfinite(v)

    def test_peak_drawdown_positive(self):
        result = run_regime_aware_stress_test(REGIME_AWARE_2008)
        assert result.peak_drawdown > 0.0

    def test_peak_drawdown_bounded(self):
        result = run_regime_aware_stress_test(REGIME_AWARE_2008)
        assert result.peak_drawdown <= 1.0

    def test_final_equity_positive(self):
        result = run_regime_aware_stress_test(REGIME_AWARE_2008)
        assert result.final_equity > 0.0

    def test_n_regime_changes_positive(self):
        result = run_regime_aware_stress_test(REGIME_AWARE_2008)
        assert result.n_regime_changes >= 2


class TestRunExecutionCovid:
    def test_runs_successfully(self):
        result = run_regime_aware_stress_test(REGIME_AWARE_COVID)
        assert result.scenario_name == "2020_COVID_CRASH"

    def test_equity_curve_length(self):
        result = run_regime_aware_stress_test(REGIME_AWARE_COVID)
        expected = len(REGIME_AWARE_COVID.preset.returns) - 20
        assert len(result.equity_curve) == expected

    def test_drawdown_positive(self):
        result = run_regime_aware_stress_test(REGIME_AWARE_COVID)
        assert result.peak_drawdown > 0.0


class TestRunExecutionAllScenarios:
    """Every regime-aware scenario must execute without error."""

    @pytest.mark.parametrize("name", list(REGIME_AWARE_REGISTRY.keys()))
    def test_scenario_runs(self, name):
        ra = get_regime_aware_scenario(name)
        # Some short scenarios (10 days) have 0 equity points with window=20
        # — skip those (Flash Crash, Black Monday have only 10 days)
        if len(ra.preset.returns) <= 20:
            result = run_regime_aware_stress_test(ra)
            assert isinstance(result, RegimeAwareStressResult)
            # Equity curve is empty for scenarios shorter than window
            assert len(result.equity_curve) == max(
                0, len(ra.preset.returns) - 20
            )
        else:
            result = run_regime_aware_stress_test(ra)
            assert isinstance(result, RegimeAwareStressResult)
            assert len(result.equity_curve) > 0

    @pytest.mark.parametrize("name", list(REGIME_AWARE_REGISTRY.keys()))
    def test_scenario_name_in_result(self, name):
        ra = get_regime_aware_scenario(name)
        result = run_regime_aware_stress_test(ra)
        assert result.scenario_name == name


# =============================================================================
# SECTION 8 -- REGIME CHANGES IN RESULT
# =============================================================================

class TestRegimeChangesCount:
    def test_2008_multiple_changes(self):
        result = run_regime_aware_stress_test(REGIME_AWARE_2008)
        assert result.n_regime_changes >= 2

    def test_vol_shock_no_changes(self):
        """Uniform RISK_OFF sequence has 0 transitions."""
        result = run_regime_aware_stress_test(REGIME_AWARE_VOL_SHOCK)
        assert result.n_regime_changes == 0

    def test_liquidity_no_changes(self):
        """Uniform CRISIS sequence has 0 transitions."""
        result = run_regime_aware_stress_test(REGIME_AWARE_LIQUIDITY)
        assert result.n_regime_changes == 0


# =============================================================================
# SECTION 9 -- REGIME-AWARE vs STATIC REGIME DIFFER
# =============================================================================

class TestRegimeAwareVsStatic:
    """Regime-aware results should differ from static-regime backtest."""

    def test_2008_regime_aware_differs_from_static_crisis(self):
        """Dynamic regime sequence produces different equity than static CRISIS."""
        from jarvis.backtest.engine import run_backtest
        ra = REGIME_AWARE_2008
        returns = list(ra.preset.returns)
        prices = [100.0]
        for r in returns[:-1]:
            prices.append(prices[-1] * (1.0 + r))

        static_ec = run_backtest(
            returns_series=returns,
            window=20,
            initial_capital=100_000.0,
            asset_price_series=prices,
            regime=_RS.CRISIS,
            meta_uncertainty=0.3,
        )

        dynamic_result = run_regime_aware_stress_test(
            ra, window=20, initial_capital=100_000.0, meta_uncertainty=0.3,
        )

        # They should differ because static uses CRISIS throughout
        # while dynamic starts RISK_ON -> RISK_OFF -> CRISIS -> RISK_OFF
        if len(static_ec) > 0 and len(dynamic_result.equity_curve) > 0:
            assert list(dynamic_result.equity_curve) != static_ec


# =============================================================================
# SECTION 10 -- CUSTOM PARAMETERS
# =============================================================================

class TestCustomParameters:
    def test_custom_initial_capital(self):
        result = run_regime_aware_stress_test(
            REGIME_AWARE_2008, initial_capital=50_000.0
        )
        # Equity values should be smaller than with 100k
        default = run_regime_aware_stress_test(REGIME_AWARE_2008)
        if len(result.equity_curve) > 0 and len(default.equity_curve) > 0:
            assert result.equity_curve[0] != default.equity_curve[0]

    def test_custom_meta_uncertainty_low(self):
        """Low meta_uncertainty runs successfully."""
        r = run_regime_aware_stress_test(
            REGIME_AWARE_2008, meta_uncertainty=0.1
        )
        assert isinstance(r, RegimeAwareStressResult)
        assert len(r.equity_curve) > 0

    def test_custom_meta_uncertainty_high(self):
        """High meta_uncertainty runs successfully."""
        r = run_regime_aware_stress_test(
            REGIME_AWARE_2008, meta_uncertainty=0.9
        )
        assert isinstance(r, RegimeAwareStressResult)
        assert len(r.equity_curve) > 0

    def test_custom_asset_price_start(self):
        r1 = run_regime_aware_stress_test(
            REGIME_AWARE_2008, asset_price_start=50.0
        )
        r2 = run_regime_aware_stress_test(
            REGIME_AWARE_2008, asset_price_start=500.0
        )
        if len(r1.equity_curve) > 0 and len(r2.equity_curve) > 0:
            assert r1.equity_curve != r2.equity_curve

    def test_boundary_meta_uncertainty_zero(self):
        result = run_regime_aware_stress_test(
            REGIME_AWARE_2008, meta_uncertainty=0.0
        )
        assert isinstance(result, RegimeAwareStressResult)

    def test_boundary_meta_uncertainty_one(self):
        result = run_regime_aware_stress_test(
            REGIME_AWARE_2008, meta_uncertainty=1.0
        )
        assert isinstance(result, RegimeAwareStressResult)


# =============================================================================
# SECTION 11 -- DETERMINISM (DET-07)
# =============================================================================

class TestDeterminism:
    def test_same_inputs_same_result(self):
        r1 = run_regime_aware_stress_test(REGIME_AWARE_2008)
        r2 = run_regime_aware_stress_test(REGIME_AWARE_2008)
        assert r1.equity_curve == r2.equity_curve
        assert r1.peak_drawdown == r2.peak_drawdown
        assert r1.final_equity == r2.final_equity
        assert r1.n_regime_changes == r2.n_regime_changes

    def test_covid_deterministic(self):
        r1 = run_regime_aware_stress_test(REGIME_AWARE_COVID)
        r2 = run_regime_aware_stress_test(REGIME_AWARE_COVID)
        assert r1.equity_curve == r2.equity_curve

    def test_dotcom_deterministic(self):
        r1 = run_regime_aware_stress_test(REGIME_AWARE_DOTCOM)
        r2 = run_regime_aware_stress_test(REGIME_AWARE_DOTCOM)
        assert r1.equity_curve == r2.equity_curve

    def test_registry_lookup_deterministic(self):
        a = get_regime_aware_scenario("2008_FINANCIAL_CRISIS")
        b = get_regime_aware_scenario("2008_FINANCIAL_CRISIS")
        assert a is b


# =============================================================================
# SECTION 12 -- SHORT SCENARIOS (duration <= window)
# =============================================================================

class TestShortScenarios:
    """Flash Crash and Black Monday have 10 days < window=20."""

    def test_flash_crash_empty_equity(self):
        result = run_regime_aware_stress_test(REGIME_AWARE_FLASH)
        assert len(result.equity_curve) == 0

    def test_flash_crash_final_equity_is_initial(self):
        result = run_regime_aware_stress_test(REGIME_AWARE_FLASH)
        assert result.final_equity == 100_000.0

    def test_flash_crash_zero_drawdown(self):
        result = run_regime_aware_stress_test(REGIME_AWARE_FLASH)
        assert result.peak_drawdown == 0.0

    def test_black_monday_empty_equity(self):
        result = run_regime_aware_stress_test(REGIME_AWARE_BLACK_MONDAY)
        assert len(result.equity_curve) == 0


# =============================================================================
# SECTION 13 -- IMPORT CONTRACT
# =============================================================================

class TestImportContract:
    def test_import_from_module(self):
        from jarvis.simulation.stress_scenarios import (
            RegimeAwareScenario,
            RegimeAwareStressResult,
            REGIME_AWARE_REGISTRY,
            get_regime_aware_scenario,
            run_regime_aware_stress_test,
        )
        assert RegimeAwareScenario is not None
        assert callable(run_regime_aware_stress_test)

    def test_import_from_package(self):
        from jarvis.simulation import (
            RegimeAwareScenario,
            RegimeAwareStressResult,
            REGIME_AWARE_REGISTRY,
            get_regime_aware_scenario,
            run_regime_aware_stress_test,
        )
        assert isinstance(REGIME_AWARE_REGISTRY, dict)

    def test_import_presets_from_module(self):
        from jarvis.simulation.stress_scenarios import (
            REGIME_AWARE_2008,
            REGIME_AWARE_COVID,
            REGIME_AWARE_FLASH,
            REGIME_AWARE_DOTCOM,
            REGIME_AWARE_BLACK_MONDAY,
            REGIME_AWARE_VOL_SHOCK,
            REGIME_AWARE_LIQUIDITY,
            REGIME_AWARE_CORR_SHOCK,
        )
        assert REGIME_AWARE_2008 is not None
