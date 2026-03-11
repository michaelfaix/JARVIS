# =============================================================================
# tests/unit/research/test_scenario_sandbox.py
# Tests for jarvis/research/scenario_sandbox.py
# =============================================================================

import pytest

from jarvis.research.scenario_sandbox import (
    SCENARIO_TYPES,
    CORR_FM04_THRESHOLD,
    VOL_FM02_THRESHOLD,
    MODE_MAP,
    ScenarioConfig,
    ScenarioResult,
    ScenarioSandboxEngine,
    _clip,
)


# =============================================================================
# SECTION 1 -- CONSTANTS
# =============================================================================

class TestConstants:
    def test_scenario_types(self):
        assert "regime_shift" in SCENARIO_TYPES
        assert "vol_spike" in SCENARIO_TYPES
        assert "corr_shock" in SCENARIO_TYPES
        assert "confidence_shift" in SCENARIO_TYPES
        assert "ev_shift" in SCENARIO_TYPES
        assert len(SCENARIO_TYPES) == 5

    def test_corr_fm04_threshold(self):
        assert CORR_FM04_THRESHOLD == 0.85

    def test_vol_fm02_threshold(self):
        assert VOL_FM02_THRESHOLD == 3.0

    def test_mode_map_keys(self):
        assert set(MODE_MAP.keys()) == {
            "TRENDING", "RANGING", "HIGH_VOL", "SHOCK", "UNKNOWN",
        }

    def test_mode_map_values(self):
        assert MODE_MAP["TRENDING"] == "MOMENTUM"
        assert MODE_MAP["RANGING"] == "MEAN_REVERSION"
        assert MODE_MAP["HIGH_VOL"] == "RISK_REDUCTION"
        assert MODE_MAP["SHOCK"] == "DEFENSIVE"
        assert MODE_MAP["UNKNOWN"] == "MINIMAL_EXPOSURE"


# =============================================================================
# SECTION 2 -- CLIP HELPER
# =============================================================================

class TestClip:
    def test_within_range(self):
        assert _clip(0.5, 0.0, 1.0) == 0.5

    def test_below_lo(self):
        assert _clip(-0.5, 0.0, 1.0) == 0.0

    def test_above_hi(self):
        assert _clip(1.5, 0.0, 1.0) == 1.0

    def test_at_lo(self):
        assert _clip(0.0, 0.0, 1.0) == 0.0

    def test_at_hi(self):
        assert _clip(1.0, 0.0, 1.0) == 1.0


# =============================================================================
# SECTION 3 -- SCENARIO CONFIG DATACLASS
# =============================================================================

class TestScenarioConfig:
    def test_frozen(self):
        cfg = ScenarioConfig("S1", "regime_shift", 0.5, 10, ("BTC",))
        with pytest.raises(AttributeError):
            cfg.magnitude = 0.9

    def test_fields(self):
        cfg = ScenarioConfig(
            scenario_id="S1",
            scenario_type="vol_spike",
            magnitude=0.7,
            duration_bars=20,
            asset_scope=("ETH", "BTC"),
        )
        assert cfg.scenario_id == "S1"
        assert cfg.scenario_type == "vol_spike"
        assert cfg.magnitude == 0.7
        assert cfg.duration_bars == 20
        assert cfg.asset_scope == ("ETH", "BTC")

    def test_equality(self):
        a = ScenarioConfig("S1", "corr_shock", 0.5, 10, ("A",))
        b = ScenarioConfig("S1", "corr_shock", 0.5, 10, ("A",))
        assert a == b


# =============================================================================
# SECTION 4 -- SCENARIO RESULT DATACLASS
# =============================================================================

class TestScenarioResult:
    def test_frozen(self):
        r = ScenarioResult("R1", "SHOCK", -0.3, "DEFENSIVE", 10.0, -0.5, -50.0, 5, "note")
        with pytest.raises(AttributeError):
            r.regime_impact = "TRENDING"

    def test_fields(self):
        r = ScenarioResult(
            scenario_id="R1",
            regime_impact="HIGH_VOL",
            confidence_delta=-0.2,
            strategy_mode_shift="RISK_REDUCTION",
            expected_vol_change=15.0,
            portfolio_heat_change=-0.3,
            ev_shift=-40.0,
            recovery_bars_estimate=8,
            notes="test note",
        )
        assert r.scenario_id == "R1"
        assert r.regime_impact == "HIGH_VOL"
        assert r.confidence_delta == -0.2
        assert r.strategy_mode_shift == "RISK_REDUCTION"
        assert r.expected_vol_change == 15.0
        assert r.portfolio_heat_change == -0.3
        assert r.ev_shift == -40.0
        assert r.recovery_bars_estimate == 8
        assert r.notes == "test note"

    def test_equality(self):
        r1 = ScenarioResult("R1", "SHOCK", -0.3, "D", 10.0, -0.5, -50.0, 5, "n")
        r2 = ScenarioResult("R1", "SHOCK", -0.3, "D", 10.0, -0.5, -50.0, 5, "n")
        assert r1 == r2


# =============================================================================
# SECTION 5 -- SIMULATE REGIME SHIFT
# =============================================================================

class TestSimulateRegimeShift:
    def test_basic_shift(self):
        eng = ScenarioSandboxEngine()
        r = eng.simulate_regime_shift("TRENDING", "SHOCK", 0.8, 0.5)
        assert isinstance(r, ScenarioResult)
        assert r.regime_impact == "SHOCK"
        assert r.strategy_mode_shift == "DEFENSIVE"

    def test_confidence_delta_negative(self):
        eng = ScenarioSandboxEngine()
        r = eng.simulate_regime_shift("TRENDING", "HIGH_VOL", 0.9, 0.8)
        assert r.confidence_delta < 0.0

    def test_confidence_delta_clipped(self):
        eng = ScenarioSandboxEngine()
        r = eng.simulate_regime_shift("A", "B", 0.5, 1.0)
        assert r.confidence_delta >= -1.0

    def test_mode_map_lookup(self):
        eng = ScenarioSandboxEngine()
        r = eng.simulate_regime_shift("A", "RANGING", 0.5, 0.5)
        assert r.strategy_mode_shift == "MEAN_REVERSION"

    def test_unknown_regime_fallback(self):
        eng = ScenarioSandboxEngine()
        r = eng.simulate_regime_shift("A", "NONEXISTENT", 0.5, 0.5)
        assert r.strategy_mode_shift == "MINIMAL_EXPOSURE"

    def test_magnitude_zero(self):
        eng = ScenarioSandboxEngine()
        r = eng.simulate_regime_shift("A", "SHOCK", 0.5, 0.0)
        assert r.confidence_delta == 0.0
        assert r.expected_vol_change == 0.0
        assert r.recovery_bars_estimate == 0

    def test_magnitude_one(self):
        eng = ScenarioSandboxEngine()
        r = eng.simulate_regime_shift("A", "B", 0.5, 1.0)
        assert r.confidence_delta == pytest.approx(-0.4)
        assert r.expected_vol_change == pytest.approx(0.3)
        assert r.recovery_bars_estimate == 20

    def test_scenario_id_format(self):
        eng = ScenarioSandboxEngine()
        r = eng.simulate_regime_shift("TRENDING", "SHOCK", 0.5, 0.5)
        assert r.scenario_id == "REGIME_SHIFT_TRENDING_TO_SHOCK"

    def test_ev_shift_proportional(self):
        eng = ScenarioSandboxEngine()
        r = eng.simulate_regime_shift("A", "B", 0.5, 0.5)
        assert r.ev_shift == pytest.approx(-25.0)

    def test_portfolio_heat_change_clipped(self):
        eng = ScenarioSandboxEngine()
        r = eng.simulate_regime_shift("A", "B", 0.5, 1.0)
        assert -1.0 <= r.portfolio_heat_change <= 1.0

    def test_notes_contain_info(self):
        eng = ScenarioSandboxEngine()
        r = eng.simulate_regime_shift("TRENDING", "SHOCK", 0.5, 0.5)
        assert "TRENDING" in r.notes
        assert "SHOCK" in r.notes
        assert "0.50" in r.notes


# =============================================================================
# SECTION 6 -- SIMULATE REGIME SHIFT VALIDATION
# =============================================================================

class TestSimulateRegimeShiftValidation:
    def test_from_regime_type_error(self):
        eng = ScenarioSandboxEngine()
        with pytest.raises(TypeError, match="from_regime must be a string"):
            eng.simulate_regime_shift(123, "B", 0.5, 0.5)

    def test_to_regime_type_error(self):
        eng = ScenarioSandboxEngine()
        with pytest.raises(TypeError, match="to_regime must be a string"):
            eng.simulate_regime_shift("A", 123, 0.5, 0.5)

    def test_confidence_type_error(self):
        eng = ScenarioSandboxEngine()
        with pytest.raises(TypeError, match="current_confidence must be numeric"):
            eng.simulate_regime_shift("A", "B", "bad", 0.5)

    def test_magnitude_type_error(self):
        eng = ScenarioSandboxEngine()
        with pytest.raises(TypeError, match="magnitude must be numeric"):
            eng.simulate_regime_shift("A", "B", 0.5, "bad")

    def test_magnitude_below_range(self):
        eng = ScenarioSandboxEngine()
        with pytest.raises(ValueError, match="magnitude must be in"):
            eng.simulate_regime_shift("A", "B", 0.5, -0.1)

    def test_magnitude_above_range(self):
        eng = ScenarioSandboxEngine()
        with pytest.raises(ValueError, match="magnitude must be in"):
            eng.simulate_regime_shift("A", "B", 0.5, 1.1)

    def test_int_magnitude_accepted(self):
        eng = ScenarioSandboxEngine()
        r = eng.simulate_regime_shift("A", "B", 1, 1)
        assert isinstance(r, ScenarioResult)


# =============================================================================
# SECTION 7 -- SIMULATE VOL SPIKE
# =============================================================================

class TestSimulateVolSpike:
    def test_basic_spike(self):
        eng = ScenarioSandboxEngine()
        r = eng.simulate_vol_spike(1.0, 3.5)
        assert isinstance(r, ScenarioResult)

    def test_triggers_fm02(self):
        eng = ScenarioSandboxEngine()
        r = eng.simulate_vol_spike(1.0, 4.0)
        # simulated_nvu = 4.0 > 3.0
        assert r.regime_impact == "HIGH_VOL"
        assert r.confidence_delta == -0.3
        assert r.strategy_mode_shift == "RISK_REDUCTION"

    def test_no_fm02(self):
        eng = ScenarioSandboxEngine()
        r = eng.simulate_vol_spike(1.0, 2.0)
        # simulated_nvu = 2.0, not > 3.0
        assert r.regime_impact == "ELEVATED_VOL"
        assert r.confidence_delta == -0.1
        assert r.strategy_mode_shift == "MEAN_REVERSION"

    def test_at_threshold(self):
        """simulated_nvu = 3.0 exactly → NOT > 3.0."""
        eng = ScenarioSandboxEngine()
        r = eng.simulate_vol_spike(1.0, 3.0)
        assert r.regime_impact == "ELEVATED_VOL"

    def test_just_above_threshold(self):
        eng = ScenarioSandboxEngine()
        r = eng.simulate_vol_spike(1.0, 3.1)
        assert r.regime_impact == "HIGH_VOL"

    def test_expected_vol_change(self):
        eng = ScenarioSandboxEngine()
        r = eng.simulate_vol_spike(1.0, 3.0)
        assert r.expected_vol_change == pytest.approx(200.0)

    def test_scenario_id_format(self):
        eng = ScenarioSandboxEngine()
        r = eng.simulate_vol_spike(1.0, 2.0)
        assert "VOL_SPIKE_NVU_2.0" in r.scenario_id

    def test_notes_contain_fm02(self):
        eng = ScenarioSandboxEngine()
        r = eng.simulate_vol_spike(1.0, 4.0)
        assert "FM-02: True" in r.notes

    def test_spike_factor_one(self):
        eng = ScenarioSandboxEngine()
        r = eng.simulate_vol_spike(2.0, 1.0)
        assert r.expected_vol_change == pytest.approx(0.0)

    def test_high_nvu_input(self):
        eng = ScenarioSandboxEngine()
        r = eng.simulate_vol_spike(2.0, 2.0)
        # simulated_nvu = 4.0 > 3.0
        assert r.regime_impact == "HIGH_VOL"


# =============================================================================
# SECTION 8 -- SIMULATE VOL SPIKE VALIDATION
# =============================================================================

class TestSimulateVolSpikeValidation:
    def test_nvu_type_error(self):
        eng = ScenarioSandboxEngine()
        with pytest.raises(TypeError, match="current_nvu must be numeric"):
            eng.simulate_vol_spike("bad", 2.0)

    def test_spike_factor_type_error(self):
        eng = ScenarioSandboxEngine()
        with pytest.raises(TypeError, match="spike_factor must be numeric"):
            eng.simulate_vol_spike(1.0, "bad")

    def test_nvu_zero(self):
        eng = ScenarioSandboxEngine()
        with pytest.raises(ValueError, match="current_nvu must be > 0"):
            eng.simulate_vol_spike(0, 2.0)

    def test_nvu_negative(self):
        eng = ScenarioSandboxEngine()
        with pytest.raises(ValueError, match="current_nvu must be > 0"):
            eng.simulate_vol_spike(-1.0, 2.0)

    def test_spike_factor_below_one(self):
        eng = ScenarioSandboxEngine()
        with pytest.raises(ValueError, match="spike_factor must be >= 1.0"):
            eng.simulate_vol_spike(1.0, 0.5)

    def test_int_args_accepted(self):
        eng = ScenarioSandboxEngine()
        r = eng.simulate_vol_spike(1, 2)
        assert isinstance(r, ScenarioResult)


# =============================================================================
# SECTION 9 -- SIMULATE CORRELATION SHOCK
# =============================================================================

class TestSimulateCorrelationShock:
    def test_basic_shock(self):
        eng = ScenarioSandboxEngine()
        r = eng.simulate_correlation_shock(5, 0.90)
        assert isinstance(r, ScenarioResult)
        assert r.regime_impact == "SHOCK"
        assert r.strategy_mode_shift == "DEFENSIVE"

    def test_triggers_fm04(self):
        eng = ScenarioSandboxEngine()
        r = eng.simulate_correlation_shock(3, 0.90)
        # 0.90 > 0.85
        assert r.confidence_delta == -0.5

    def test_no_fm04(self):
        eng = ScenarioSandboxEngine()
        r = eng.simulate_correlation_shock(3, 0.80)
        # 0.80 not > 0.85
        assert r.confidence_delta == -0.2

    def test_at_fm04_threshold(self):
        """0.85 exactly → NOT > 0.85."""
        eng = ScenarioSandboxEngine()
        r = eng.simulate_correlation_shock(3, 0.85)
        assert r.confidence_delta == -0.2

    def test_just_above_fm04(self):
        eng = ScenarioSandboxEngine()
        r = eng.simulate_correlation_shock(3, 0.86)
        assert r.confidence_delta == -0.5

    def test_expected_vol_change(self):
        eng = ScenarioSandboxEngine()
        r = eng.simulate_correlation_shock(3, 0.50)
        assert r.expected_vol_change == pytest.approx(10.0)

    def test_ev_shift(self):
        eng = ScenarioSandboxEngine()
        r = eng.simulate_correlation_shock(3, 0.50)
        assert r.ev_shift == pytest.approx(-50.0)

    def test_recovery_bars(self):
        eng = ScenarioSandboxEngine()
        r = eng.simulate_correlation_shock(3, 0.50)
        assert r.recovery_bars_estimate == 10

    def test_portfolio_heat_change_clipped(self):
        eng = ScenarioSandboxEngine()
        r = eng.simulate_correlation_shock(3, 1.0)
        assert r.portfolio_heat_change >= -1.0

    def test_scenario_id_format(self):
        eng = ScenarioSandboxEngine()
        r = eng.simulate_correlation_shock(3, 0.90)
        assert "CORR_SHOCK_0.90" in r.scenario_id

    def test_notes_contain_fm04(self):
        eng = ScenarioSandboxEngine()
        r = eng.simulate_correlation_shock(3, 0.90)
        assert "FM-04: True" in r.notes
        assert "3 assets" in r.notes

    def test_zero_correlation(self):
        eng = ScenarioSandboxEngine()
        r = eng.simulate_correlation_shock(3, 0.0)
        assert r.expected_vol_change == pytest.approx(0.0)
        assert r.ev_shift == pytest.approx(0.0)
        assert r.recovery_bars_estimate == 0


# =============================================================================
# SECTION 10 -- SIMULATE CORRELATION SHOCK VALIDATION
# =============================================================================

class TestSimulateCorrelationShockValidation:
    def test_n_assets_type_error(self):
        eng = ScenarioSandboxEngine()
        with pytest.raises(TypeError, match="n_assets must be int"):
            eng.simulate_correlation_shock(3.0, 0.5)

    def test_correlation_type_error(self):
        eng = ScenarioSandboxEngine()
        with pytest.raises(TypeError, match="shock_correlation must be numeric"):
            eng.simulate_correlation_shock(3, "bad")

    def test_n_assets_zero(self):
        eng = ScenarioSandboxEngine()
        with pytest.raises(ValueError, match="n_assets must be >= 1"):
            eng.simulate_correlation_shock(0, 0.5)

    def test_n_assets_negative(self):
        eng = ScenarioSandboxEngine()
        with pytest.raises(ValueError, match="n_assets must be >= 1"):
            eng.simulate_correlation_shock(-1, 0.5)

    def test_correlation_below_range(self):
        eng = ScenarioSandboxEngine()
        with pytest.raises(ValueError, match="shock_correlation must be in"):
            eng.simulate_correlation_shock(3, -0.1)

    def test_correlation_above_range(self):
        eng = ScenarioSandboxEngine()
        with pytest.raises(ValueError, match="shock_correlation must be in"):
            eng.simulate_correlation_shock(3, 1.1)


# =============================================================================
# SECTION 11 -- DETERMINISM
# =============================================================================

class TestDeterminism:
    def test_regime_shift_deterministic(self):
        eng = ScenarioSandboxEngine()
        results = [eng.simulate_regime_shift("A", "SHOCK", 0.5, 0.8) for _ in range(10)]
        assert all(r == results[0] for r in results)

    def test_vol_spike_deterministic(self):
        eng = ScenarioSandboxEngine()
        results = [eng.simulate_vol_spike(1.0, 3.5) for _ in range(10)]
        assert all(r == results[0] for r in results)

    def test_corr_shock_deterministic(self):
        eng = ScenarioSandboxEngine()
        results = [eng.simulate_correlation_shock(3, 0.9) for _ in range(10)]
        assert all(r == results[0] for r in results)

    def test_independent_engines(self):
        r1 = ScenarioSandboxEngine().simulate_regime_shift("A", "B", 0.5, 0.5)
        r2 = ScenarioSandboxEngine().simulate_regime_shift("A", "B", 0.5, 0.5)
        assert r1 == r2
