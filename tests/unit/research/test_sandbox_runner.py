# =============================================================================
# tests/unit/research/test_sandbox_runner.py
# Tests for jarvis/research/sandbox_runner.py
# =============================================================================

import pytest

from jarvis.research.sandbox_runner import (
    SUPPORTED_SCENARIO_DISPATCHES,
    SandboxRunnerResult,
    run_scenario_safely,
)
from jarvis.research.scenario_sandbox import (
    ScenarioResult,
    ScenarioSandboxEngine,
)


# =============================================================================
# SECTION 1 -- CONSTANTS
# =============================================================================

class TestConstants:
    def test_supported_dispatches_keys(self):
        assert set(SUPPORTED_SCENARIO_DISPATCHES.keys()) == {
            "regime_shift", "vol_spike", "corr_shock",
        }

    def test_dispatch_regime_shift(self):
        assert SUPPORTED_SCENARIO_DISPATCHES["regime_shift"] == "simulate_regime_shift"

    def test_dispatch_vol_spike(self):
        assert SUPPORTED_SCENARIO_DISPATCHES["vol_spike"] == "simulate_vol_spike"

    def test_dispatch_corr_shock(self):
        assert SUPPORTED_SCENARIO_DISPATCHES["corr_shock"] == "simulate_correlation_shock"


# =============================================================================
# SECTION 2 -- SANDBOX RUNNER RESULT DATACLASS
# =============================================================================

class TestSandboxRunnerResult:
    def test_frozen(self):
        r = SandboxRunnerResult("regime_shift", True, None, None)
        with pytest.raises(AttributeError):
            r.success = False

    def test_fields_success(self):
        sr = ScenarioResult("R1", "SHOCK", -0.3, "D", 10.0, -0.5, -50.0, 5, "n")
        r = SandboxRunnerResult("regime_shift", True, sr, None)
        assert r.scenario_type == "regime_shift"
        assert r.success is True
        assert r.result == sr
        assert r.error_message is None

    def test_fields_failure(self):
        r = SandboxRunnerResult("vol_spike", False, None, "error msg")
        assert r.success is False
        assert r.result is None
        assert r.error_message == "error msg"

    def test_equality(self):
        r1 = SandboxRunnerResult("corr_shock", True, None, None)
        r2 = SandboxRunnerResult("corr_shock", True, None, None)
        assert r1 == r2


# =============================================================================
# SECTION 3 -- RUN SCENARIO SAFELY: REGIME SHIFT
# =============================================================================

class TestRunRegimeShift:
    def test_basic(self):
        eng = ScenarioSandboxEngine()
        r = run_scenario_safely(
            eng, "regime_shift",
            from_regime="TRENDING", to_regime="SHOCK",
            current_confidence=0.8, magnitude=0.5,
        )
        assert r.success is True
        assert isinstance(r.result, ScenarioResult)
        assert r.result.regime_impact == "SHOCK"
        assert r.error_message is None

    def test_with_defaults(self):
        eng = ScenarioSandboxEngine()
        r = run_scenario_safely(
            eng, "regime_shift",
            from_regime="A", to_regime="B",
            current_confidence=0.5,
        )
        assert r.success is True

    def test_scenario_type_stored(self):
        eng = ScenarioSandboxEngine()
        r = run_scenario_safely(
            eng, "regime_shift",
            from_regime="A", to_regime="B",
            current_confidence=0.5,
        )
        assert r.scenario_type == "regime_shift"


# =============================================================================
# SECTION 4 -- RUN SCENARIO SAFELY: VOL SPIKE
# =============================================================================

class TestRunVolSpike:
    def test_basic(self):
        eng = ScenarioSandboxEngine()
        r = run_scenario_safely(
            eng, "vol_spike",
            current_nvu=1.0, spike_factor=3.5,
        )
        assert r.success is True
        assert isinstance(r.result, ScenarioResult)

    def test_with_defaults(self):
        eng = ScenarioSandboxEngine()
        r = run_scenario_safely(
            eng, "vol_spike",
            current_nvu=1.0,
        )
        assert r.success is True


# =============================================================================
# SECTION 5 -- RUN SCENARIO SAFELY: CORR SHOCK
# =============================================================================

class TestRunCorrShock:
    def test_basic(self):
        eng = ScenarioSandboxEngine()
        r = run_scenario_safely(
            eng, "corr_shock",
            n_assets=5, shock_correlation=0.90,
        )
        assert r.success is True
        assert isinstance(r.result, ScenarioResult)

    def test_with_defaults(self):
        eng = ScenarioSandboxEngine()
        r = run_scenario_safely(
            eng, "corr_shock",
            n_assets=3,
        )
        assert r.success is True


# =============================================================================
# SECTION 6 -- RUN SCENARIO SAFELY: ERROR CAPTURE
# =============================================================================

class TestRunErrorCapture:
    def test_invalid_magnitude_captured(self):
        eng = ScenarioSandboxEngine()
        r = run_scenario_safely(
            eng, "regime_shift",
            from_regime="A", to_regime="B",
            current_confidence=0.5, magnitude=2.0,
        )
        assert r.success is False
        assert r.result is None
        assert "magnitude" in r.error_message

    def test_invalid_nvu_captured(self):
        eng = ScenarioSandboxEngine()
        r = run_scenario_safely(
            eng, "vol_spike",
            current_nvu=-1.0,
        )
        assert r.success is False
        assert "current_nvu" in r.error_message

    def test_invalid_correlation_captured(self):
        eng = ScenarioSandboxEngine()
        r = run_scenario_safely(
            eng, "corr_shock",
            n_assets=3, shock_correlation=1.5,
        )
        assert r.success is False
        assert "shock_correlation" in r.error_message

    def test_type_error_captured(self):
        eng = ScenarioSandboxEngine()
        r = run_scenario_safely(
            eng, "regime_shift",
            from_regime=123, to_regime="B",
            current_confidence=0.5,
        )
        assert r.success is False
        assert "from_regime" in r.error_message

    def test_missing_required_kwarg_captured(self):
        eng = ScenarioSandboxEngine()
        r = run_scenario_safely(eng, "regime_shift")
        assert r.success is False
        assert r.error_message is not None


# =============================================================================
# SECTION 7 -- RUN SCENARIO SAFELY: INPUT VALIDATION
# =============================================================================

class TestRunValidation:
    def test_engine_type_error(self):
        with pytest.raises(TypeError, match="engine must be a ScenarioSandboxEngine"):
            run_scenario_safely("not_engine", "regime_shift")

    def test_scenario_type_type_error(self):
        eng = ScenarioSandboxEngine()
        with pytest.raises(TypeError, match="scenario_type must be a string"):
            run_scenario_safely(eng, 123)

    def test_unknown_scenario_type(self):
        eng = ScenarioSandboxEngine()
        with pytest.raises(ValueError, match="Unknown scenario_type"):
            run_scenario_safely(eng, "unknown_type")

    def test_error_message_lists_supported(self):
        eng = ScenarioSandboxEngine()
        with pytest.raises(ValueError, match="corr_shock"):
            run_scenario_safely(eng, "bad")


# =============================================================================
# SECTION 8 -- DETERMINISM
# =============================================================================

class TestDeterminism:
    def test_regime_shift_deterministic(self):
        eng = ScenarioSandboxEngine()
        results = [
            run_scenario_safely(
                eng, "regime_shift",
                from_regime="A", to_regime="B",
                current_confidence=0.5, magnitude=0.5,
            )
            for _ in range(10)
        ]
        assert all(r == results[0] for r in results)

    def test_vol_spike_deterministic(self):
        eng = ScenarioSandboxEngine()
        results = [
            run_scenario_safely(eng, "vol_spike", current_nvu=1.0, spike_factor=2.0)
            for _ in range(10)
        ]
        assert all(r == results[0] for r in results)

    def test_independent_runs(self):
        r1 = run_scenario_safely(
            ScenarioSandboxEngine(), "corr_shock",
            n_assets=3, shock_correlation=0.9,
        )
        r2 = run_scenario_safely(
            ScenarioSandboxEngine(), "corr_shock",
            n_assets=3, shock_correlation=0.9,
        )
        assert r1 == r2
