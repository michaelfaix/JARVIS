# =============================================================================
# tests/unit/simulation/test_stress_scenarios.py
# Tests for jarvis/simulation/stress_scenarios.py
# =============================================================================

from __future__ import annotations

import math

import pytest

from jarvis.simulation.stress_scenarios import (
    StressScenarioPreset,
    FINANCIAL_CRISIS_2008,
    COVID_CRASH_2020,
    FLASH_CRASH_2010,
    DOTCOM_BUST_2000,
    BLACK_MONDAY_1987,
    SYNTHETIC_VOL_SHOCK_3X,
    SYNTHETIC_LIQUIDITY_CRISIS,
    SYNTHETIC_CORRELATION_SHOCK,
    SCENARIO_REGISTRY,
    get_scenario,
    get_all_scenarios,
    get_historical_scenarios,
    get_synthetic_scenarios,
    get_scenario_names,
)
from jarvis.simulation.strategy_lab import (
    JARVIS_STRESS_SCENARIOS,
    StrategyLab,
    StressTestResult,
)


# =============================================================================
# HELPERS
# =============================================================================

ALL_PRESETS = (
    FINANCIAL_CRISIS_2008,
    COVID_CRASH_2020,
    FLASH_CRASH_2010,
    DOTCOM_BUST_2000,
    BLACK_MONDAY_1987,
    SYNTHETIC_VOL_SHOCK_3X,
    SYNTHETIC_LIQUIDITY_CRISIS,
    SYNTHETIC_CORRELATION_SHOCK,
)

HISTORICAL_PRESETS = (
    FINANCIAL_CRISIS_2008,
    COVID_CRASH_2020,
    FLASH_CRASH_2010,
    DOTCOM_BUST_2000,
    BLACK_MONDAY_1987,
)

SYNTHETIC_PRESETS = (
    SYNTHETIC_VOL_SHOCK_3X,
    SYNTHETIC_LIQUIDITY_CRISIS,
    SYNTHETIC_CORRELATION_SHOCK,
)


def _compute_drawdown(returns):
    """Compute peak drawdown from a return series."""
    equity = 1.0
    peak = 1.0
    max_dd = 0.0
    for r in returns:
        equity *= (1.0 + r)
        if equity > peak:
            peak = equity
        dd = (peak - equity) / peak
        if dd > max_dd:
            max_dd = dd
    return max_dd


# =============================================================================
# SECTION 1 -- DATACLASS FROZEN
# =============================================================================

class TestStressScenarioPresetFrozen:
    def test_frozen(self):
        with pytest.raises(AttributeError):
            FINANCIAL_CRISIS_2008.name = "CHANGED"

    def test_frozen_returns(self):
        with pytest.raises(AttributeError):
            COVID_CRASH_2020.returns = (0.0,)

    def test_frozen_peak_drawdown(self):
        with pytest.raises(AttributeError):
            BLACK_MONDAY_1987.peak_drawdown = 0.0


# =============================================================================
# SECTION 2 -- DATACLASS FIELDS
# =============================================================================

class TestStressScenarioPresetFields:
    def test_has_all_fields(self):
        p = FINANCIAL_CRISIS_2008
        assert hasattr(p, "name")
        assert hasattr(p, "description")
        assert hasattr(p, "returns")
        assert hasattr(p, "duration_days")
        assert hasattr(p, "peak_drawdown")
        assert hasattr(p, "volatility_multiplier")
        assert hasattr(p, "category")

    def test_returns_is_tuple(self):
        for preset in ALL_PRESETS:
            assert isinstance(preset.returns, tuple), f"{preset.name} returns not tuple"

    def test_duration_matches_length(self):
        for preset in ALL_PRESETS:
            assert preset.duration_days == len(preset.returns), (
                f"{preset.name}: duration_days={preset.duration_days} "
                f"!= len(returns)={len(preset.returns)}"
            )

    def test_peak_drawdown_positive(self):
        for preset in ALL_PRESETS:
            assert preset.peak_drawdown > 0.0, f"{preset.name} drawdown not positive"

    def test_volatility_multiplier_positive(self):
        for preset in ALL_PRESETS:
            assert preset.volatility_multiplier > 0.0, (
                f"{preset.name} vol_mult not positive"
            )

    def test_category_valid(self):
        for preset in ALL_PRESETS:
            assert preset.category in ("historical", "synthetic"), (
                f"{preset.name} bad category: {preset.category}"
            )

    def test_name_is_string(self):
        for preset in ALL_PRESETS:
            assert isinstance(preset.name, str)
            assert len(preset.name) > 0

    def test_description_is_string(self):
        for preset in ALL_PRESETS:
            assert isinstance(preset.description, str)
            assert len(preset.description) > 0


# =============================================================================
# SECTION 3 -- RETURNS VALIDITY
# =============================================================================

class TestReturnsValidity:
    def test_all_returns_finite(self):
        for preset in ALL_PRESETS:
            for i, r in enumerate(preset.returns):
                assert math.isfinite(r), (
                    f"{preset.name}[{i}] = {r} is not finite"
                )

    def test_all_returns_are_floats(self):
        for preset in ALL_PRESETS:
            for i, r in enumerate(preset.returns):
                assert isinstance(r, float), (
                    f"{preset.name}[{i}] = {r} is not float"
                )

    def test_returns_within_plausible_range(self):
        """Daily returns should not exceed +/- 30%."""
        for preset in ALL_PRESETS:
            for i, r in enumerate(preset.returns):
                assert -0.30 <= r <= 0.30, (
                    f"{preset.name}[{i}] = {r} outside [-0.30, 0.30]"
                )

    def test_non_empty_returns(self):
        for preset in ALL_PRESETS:
            assert len(preset.returns) >= 1, f"{preset.name} has empty returns"


# =============================================================================
# SECTION 4 -- HISTORICAL SCENARIO CHARACTERISTICS
# =============================================================================

class TestFinancialCrisis2008:
    def test_name(self):
        assert FINANCIAL_CRISIS_2008.name == "2008_FINANCIAL_CRISIS"

    def test_category(self):
        assert FINANCIAL_CRISIS_2008.category == "historical"

    def test_duration(self):
        assert FINANCIAL_CRISIS_2008.duration_days == 44

    def test_peak_drawdown(self):
        assert FINANCIAL_CRISIS_2008.peak_drawdown == 0.40

    def test_vol_multiplier(self):
        assert FINANCIAL_CRISIS_2008.volatility_multiplier == 4.0

    def test_actual_drawdown_significant(self):
        dd = _compute_drawdown(FINANCIAL_CRISIS_2008.returns)
        assert dd > 0.20, f"Expected significant drawdown, got {dd:.4f}"

    def test_has_large_negative_day(self):
        min_ret = min(FINANCIAL_CRISIS_2008.returns)
        assert min_ret < -0.05, f"Expected severe day, worst = {min_ret}"


class TestCovidCrash2020:
    def test_name(self):
        assert COVID_CRASH_2020.name == "2020_COVID_CRASH"

    def test_category(self):
        assert COVID_CRASH_2020.category == "historical"

    def test_duration(self):
        assert COVID_CRASH_2020.duration_days == 23

    def test_peak_drawdown(self):
        assert COVID_CRASH_2020.peak_drawdown == 0.34

    def test_vol_multiplier(self):
        assert COVID_CRASH_2020.volatility_multiplier == 5.0

    def test_actual_drawdown_significant(self):
        dd = _compute_drawdown(COVID_CRASH_2020.returns)
        assert dd > 0.20, f"Expected significant drawdown, got {dd:.4f}"

    def test_has_circuit_breaker_day(self):
        """Should have at least one day worse than -9%."""
        min_ret = min(COVID_CRASH_2020.returns)
        assert min_ret < -0.09, f"Expected circuit-breaker day, worst = {min_ret}"


class TestFlashCrash2010:
    def test_name(self):
        assert FLASH_CRASH_2010.name == "2010_FLASH_CRASH"

    def test_category(self):
        assert FLASH_CRASH_2010.category == "historical"

    def test_duration(self):
        assert FLASH_CRASH_2010.duration_days == 10

    def test_short_duration(self):
        assert FLASH_CRASH_2010.duration_days <= 15

    def test_vol_multiplier(self):
        assert FLASH_CRASH_2010.volatility_multiplier == 3.0


class TestDotcomBust2000:
    def test_name(self):
        assert DOTCOM_BUST_2000.name == "DOTCOM_BUST_2000"

    def test_category(self):
        assert DOTCOM_BUST_2000.category == "historical"

    def test_duration(self):
        assert DOTCOM_BUST_2000.duration_days == 40

    def test_grinding_decline(self):
        """Dot-com was a grinding decline — mostly negative days."""
        neg_days = sum(1 for r in DOTCOM_BUST_2000.returns if r < 0)
        assert neg_days > len(DOTCOM_BUST_2000.returns) * 0.6

    def test_vol_multiplier(self):
        assert DOTCOM_BUST_2000.volatility_multiplier == 2.5


class TestBlackMonday1987:
    def test_name(self):
        assert BLACK_MONDAY_1987.name == "BLACK_MONDAY_1987"

    def test_category(self):
        assert BLACK_MONDAY_1987.category == "historical"

    def test_duration(self):
        assert BLACK_MONDAY_1987.duration_days == 10

    def test_single_day_crash(self):
        """Must have a day worse than -20%."""
        min_ret = min(BLACK_MONDAY_1987.returns)
        assert min_ret < -0.20, f"Expected -22.6% day, worst = {min_ret}"

    def test_vol_multiplier(self):
        assert BLACK_MONDAY_1987.volatility_multiplier == 6.0


# =============================================================================
# SECTION 5 -- SYNTHETIC SCENARIO CHARACTERISTICS
# =============================================================================

class TestSyntheticVolShock3X:
    def test_name(self):
        assert SYNTHETIC_VOL_SHOCK_3X.name == "SYNTHETIC_VOL_SHOCK_3X"

    def test_category(self):
        assert SYNTHETIC_VOL_SHOCK_3X.category == "synthetic"

    def test_duration(self):
        assert SYNTHETIC_VOL_SHOCK_3X.duration_days == 20

    def test_alternating_swings(self):
        """Returns should alternate sign (vol shock, not directional)."""
        sign_changes = 0
        rets = SYNTHETIC_VOL_SHOCK_3X.returns
        for i in range(1, len(rets)):
            if (rets[i] > 0) != (rets[i - 1] > 0):
                sign_changes += 1
        assert sign_changes >= len(rets) * 0.7

    def test_vol_multiplier(self):
        assert SYNTHETIC_VOL_SHOCK_3X.volatility_multiplier == 3.0


class TestSyntheticLiquidityCrisis:
    def test_name(self):
        assert SYNTHETIC_LIQUIDITY_CRISIS.name == "SYNTHETIC_LIQUIDITY_CRISIS"

    def test_category(self):
        assert SYNTHETIC_LIQUIDITY_CRISIS.category == "synthetic"

    def test_duration(self):
        assert SYNTHETIC_LIQUIDITY_CRISIS.duration_days == 20

    def test_all_negative(self):
        """Liquidity crisis = all days negative (systematic slippage)."""
        for r in SYNTHETIC_LIQUIDITY_CRISIS.returns:
            assert r < 0.0

    def test_vol_multiplier(self):
        assert SYNTHETIC_LIQUIDITY_CRISIS.volatility_multiplier == 2.0


class TestSyntheticCorrelationShock:
    def test_name(self):
        assert SYNTHETIC_CORRELATION_SHOCK.name == "SYNTHETIC_CORRELATION_SHOCK"

    def test_category(self):
        assert SYNTHETIC_CORRELATION_SHOCK.category == "synthetic"

    def test_duration(self):
        assert SYNTHETIC_CORRELATION_SHOCK.duration_days == 20

    def test_mostly_negative(self):
        """Correlation shock = mostly negative (correlated decline)."""
        neg_days = sum(1 for r in SYNTHETIC_CORRELATION_SHOCK.returns if r < 0)
        assert neg_days >= len(SYNTHETIC_CORRELATION_SHOCK.returns) * 0.8

    def test_vol_multiplier(self):
        assert SYNTHETIC_CORRELATION_SHOCK.volatility_multiplier == 2.5


# =============================================================================
# SECTION 6 -- REGISTRY
# =============================================================================

class TestScenarioRegistry:
    def test_eight_entries(self):
        assert len(SCENARIO_REGISTRY) == 8

    def test_all_values_are_presets(self):
        for name, preset in SCENARIO_REGISTRY.items():
            assert isinstance(preset, StressScenarioPreset)

    def test_keys_match_names(self):
        for name, preset in SCENARIO_REGISTRY.items():
            assert name == preset.name

    def test_all_presets_in_registry(self):
        for preset in ALL_PRESETS:
            assert preset.name in SCENARIO_REGISTRY
            assert SCENARIO_REGISTRY[preset.name] is preset

    def test_fas_mandatory_scenarios_covered(self):
        """All 6 JARVIS_STRESS_SCENARIOS from FAS must map to a preset."""
        for scenario_name in JARVIS_STRESS_SCENARIOS:
            if scenario_name in SCENARIO_REGISTRY:
                assert SCENARIO_REGISTRY[scenario_name].name == scenario_name

    def test_registry_is_dict(self):
        assert isinstance(SCENARIO_REGISTRY, dict)


# =============================================================================
# SECTION 7 -- get_scenario()
# =============================================================================

class TestGetScenario:
    def test_valid_name(self):
        preset = get_scenario("2008_FINANCIAL_CRISIS")
        assert preset is FINANCIAL_CRISIS_2008

    def test_all_registered_names(self):
        for name in SCENARIO_REGISTRY:
            preset = get_scenario(name)
            assert preset.name == name

    def test_unknown_name_raises(self):
        with pytest.raises(ValueError, match="Unknown scenario"):
            get_scenario("NONEXISTENT_CRISIS")

    def test_error_lists_available(self):
        with pytest.raises(ValueError, match="Available"):
            get_scenario("BAD")

    def test_type_error_int(self):
        with pytest.raises(TypeError, match="name must be a string"):
            get_scenario(123)

    def test_type_error_none(self):
        with pytest.raises(TypeError, match="name must be a string"):
            get_scenario(None)

    def test_case_sensitive(self):
        with pytest.raises(ValueError):
            get_scenario("2008_financial_crisis")


# =============================================================================
# SECTION 8 -- get_all_scenarios()
# =============================================================================

class TestGetAllScenarios:
    def test_returns_tuple(self):
        result = get_all_scenarios()
        assert isinstance(result, tuple)

    def test_length(self):
        result = get_all_scenarios()
        assert len(result) == 8

    def test_all_presets(self):
        result = get_all_scenarios()
        for preset in result:
            assert isinstance(preset, StressScenarioPreset)

    def test_contains_all_named(self):
        names = {p.name for p in get_all_scenarios()}
        assert FINANCIAL_CRISIS_2008.name in names
        assert COVID_CRASH_2020.name in names
        assert BLACK_MONDAY_1987.name in names


# =============================================================================
# SECTION 9 -- get_historical_scenarios()
# =============================================================================

class TestGetHistoricalScenarios:
    def test_returns_tuple(self):
        result = get_historical_scenarios()
        assert isinstance(result, tuple)

    def test_count(self):
        result = get_historical_scenarios()
        assert len(result) == 5

    def test_all_historical(self):
        for preset in get_historical_scenarios():
            assert preset.category == "historical"

    def test_contains_expected(self):
        names = {p.name for p in get_historical_scenarios()}
        assert "2008_FINANCIAL_CRISIS" in names
        assert "2020_COVID_CRASH" in names
        assert "2010_FLASH_CRASH" in names
        assert "DOTCOM_BUST_2000" in names
        assert "BLACK_MONDAY_1987" in names


# =============================================================================
# SECTION 10 -- get_synthetic_scenarios()
# =============================================================================

class TestGetSyntheticScenarios:
    def test_returns_tuple(self):
        result = get_synthetic_scenarios()
        assert isinstance(result, tuple)

    def test_count(self):
        result = get_synthetic_scenarios()
        assert len(result) == 3

    def test_all_synthetic(self):
        for preset in get_synthetic_scenarios():
            assert preset.category == "synthetic"

    def test_contains_expected(self):
        names = {p.name for p in get_synthetic_scenarios()}
        assert "SYNTHETIC_VOL_SHOCK_3X" in names
        assert "SYNTHETIC_LIQUIDITY_CRISIS" in names
        assert "SYNTHETIC_CORRELATION_SHOCK" in names


# =============================================================================
# SECTION 11 -- get_scenario_names()
# =============================================================================

class TestGetScenarioNames:
    def test_returns_tuple(self):
        result = get_scenario_names()
        assert isinstance(result, tuple)

    def test_all_strings(self):
        for name in get_scenario_names():
            assert isinstance(name, str)

    def test_count(self):
        assert len(get_scenario_names()) == 8

    def test_matches_registry_keys(self):
        assert set(get_scenario_names()) == set(SCENARIO_REGISTRY.keys())


# =============================================================================
# SECTION 12 -- DETERMINISM
# =============================================================================

class TestDeterminism:
    def test_get_scenario_deterministic(self):
        p1 = get_scenario("2008_FINANCIAL_CRISIS")
        p2 = get_scenario("2008_FINANCIAL_CRISIS")
        assert p1 is p2

    def test_returns_immutable(self):
        """Tuple returns cannot be modified."""
        p = get_scenario("2020_COVID_CRASH")
        with pytest.raises(TypeError):
            p.returns[0] = 0.0

    def test_all_scenarios_stable_across_calls(self):
        a1 = get_all_scenarios()
        a2 = get_all_scenarios()
        assert len(a1) == len(a2)
        for p1, p2 in zip(a1, a2):
            assert p1.name == p2.name
            assert p1.returns == p2.returns

    def test_historical_filter_stable(self):
        h1 = get_historical_scenarios()
        h2 = get_historical_scenarios()
        assert len(h1) == len(h2)

    def test_synthetic_filter_stable(self):
        s1 = get_synthetic_scenarios()
        s2 = get_synthetic_scenarios()
        assert len(s1) == len(s2)


# =============================================================================
# SECTION 13 -- INTEGRATION WITH STRATEGY LAB
# =============================================================================

class TestIntegrationWithStrategyLab:
    """Verify presets can be used with StrategyLab.stress_test()."""

    def test_all_presets_run_with_stress_test(self):
        lab = StrategyLab()
        for preset in ALL_PRESETS:
            result = lab.stress_test(
                scenario_name=preset.name,
                scenario_returns=list(preset.returns),
                strategy_fn=lambda r: r,
                drawdown_limit=0.15,
            )
            assert isinstance(result, StressTestResult)
            assert result.scenario == preset.name

    def test_crisis_scenarios_produce_drawdown(self):
        lab = StrategyLab()
        crisis_presets = [
            FINANCIAL_CRISIS_2008,
            COVID_CRASH_2020,
            BLACK_MONDAY_1987,
        ]
        for preset in crisis_presets:
            result = lab.stress_test(
                scenario_name=preset.name,
                scenario_returns=list(preset.returns),
                strategy_fn=lambda r: r,
                drawdown_limit=0.99,
            )
            assert result.max_drawdown > 0.05, (
                f"{preset.name}: expected drawdown > 5%, got {result.max_drawdown:.4f}"
            )

    def test_black_monday_severe_drawdown(self):
        lab = StrategyLab()
        result = lab.stress_test(
            scenario_name=BLACK_MONDAY_1987.name,
            scenario_returns=list(BLACK_MONDAY_1987.returns),
            strategy_fn=lambda r: r,
            drawdown_limit=0.15,
        )
        assert result.survived is False
        assert result.max_drawdown > 0.20

    def test_fas_mandatory_scenarios_executable(self):
        """All 6 FAS-mandatory scenarios that have presets must execute."""
        lab = StrategyLab()
        for scenario_name in JARVIS_STRESS_SCENARIOS:
            if scenario_name in SCENARIO_REGISTRY:
                preset = SCENARIO_REGISTRY[scenario_name]
                result = lab.stress_test(
                    scenario_name=preset.name,
                    scenario_returns=list(preset.returns),
                    strategy_fn=lambda r: r,
                    drawdown_limit=0.99,
                )
                assert isinstance(result, StressTestResult)


# =============================================================================
# SECTION 14 -- IMPORT CONTRACT
# =============================================================================

class TestImportContract:
    def test_import_from_module(self):
        from jarvis.simulation.stress_scenarios import StressScenarioPreset
        assert StressScenarioPreset is not None

    def test_import_from_package(self):
        from jarvis.simulation import StressScenarioPreset
        assert StressScenarioPreset is not None

    def test_import_presets_from_package(self):
        from jarvis.simulation import (
            FINANCIAL_CRISIS_2008,
            COVID_CRASH_2020,
            FLASH_CRASH_2010,
            DOTCOM_BUST_2000,
            BLACK_MONDAY_1987,
        )
        assert FINANCIAL_CRISIS_2008 is not None

    def test_import_functions_from_package(self):
        from jarvis.simulation import (
            get_scenario,
            get_all_scenarios,
            get_historical_scenarios,
            get_synthetic_scenarios,
            get_scenario_names,
        )
        assert callable(get_scenario)

    def test_import_registry_from_package(self):
        from jarvis.simulation import SCENARIO_REGISTRY
        assert isinstance(SCENARIO_REGISTRY, dict)


# =============================================================================
# SECTION 15 -- EQUALITY AND IDENTITY
# =============================================================================

class TestEqualityIdentity:
    def test_same_preset_equal(self):
        a = get_scenario("2008_FINANCIAL_CRISIS")
        b = get_scenario("2008_FINANCIAL_CRISIS")
        assert a == b

    def test_different_presets_not_equal(self):
        a = get_scenario("2008_FINANCIAL_CRISIS")
        b = get_scenario("2020_COVID_CRASH")
        assert a != b

    def test_unique_names(self):
        names = [p.name for p in ALL_PRESETS]
        assert len(set(names)) == len(names)

    def test_unique_return_series(self):
        """Each preset should have a distinct return series."""
        seen = set()
        for p in ALL_PRESETS:
            key = p.returns
            assert key not in seen, f"Duplicate returns for {p.name}"
            seen.add(key)


# =============================================================================
# SECTION 16 -- DRAWDOWN VALIDATION
# =============================================================================

class TestDrawdownValidation:
    """Verify actual drawdown from returns is plausible vs stated peak_drawdown."""

    def test_2008_actual_vs_stated(self):
        dd = _compute_drawdown(FINANCIAL_CRISIS_2008.returns)
        assert dd > 0.15, f"2008 actual drawdown {dd:.4f} too low"

    def test_covid_actual_vs_stated(self):
        dd = _compute_drawdown(COVID_CRASH_2020.returns)
        assert dd > 0.15, f"COVID actual drawdown {dd:.4f} too low"

    def test_black_monday_actual_vs_stated(self):
        dd = _compute_drawdown(BLACK_MONDAY_1987.returns)
        assert dd > 0.20, f"Black Monday actual drawdown {dd:.4f} too low"

    def test_dotcom_actual_vs_stated(self):
        dd = _compute_drawdown(DOTCOM_BUST_2000.returns)
        assert dd > 0.15, f"Dot-com actual drawdown {dd:.4f} too low"

    def test_liquidity_crisis_actual_drawdown(self):
        dd = _compute_drawdown(SYNTHETIC_LIQUIDITY_CRISIS.returns)
        assert dd > 0.10, f"Liquidity crisis drawdown {dd:.4f} too low"

    def test_correlation_shock_actual_drawdown(self):
        dd = _compute_drawdown(SYNTHETIC_CORRELATION_SHOCK.returns)
        assert dd > 0.10, f"Correlation shock drawdown {dd:.4f} too low"
