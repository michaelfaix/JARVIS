# =============================================================================
# Tests for jarvis.core.global_state -- SystemOperatingMode & RefreshPolicy
# =============================================================================

import dataclasses

import pytest

from jarvis.core.global_state import (
    RefreshPolicy,
    REFRESH_POLICIES,
    SystemOperatingMode,
)


# ---------------------------------------------------------------------------
# 1. SystemOperatingMode enum has 3 values
# ---------------------------------------------------------------------------

class TestSystemOperatingMode:
    def test_has_three_members(self):
        assert len(SystemOperatingMode) == 3

    def test_historical_value(self):
        assert SystemOperatingMode.HISTORICAL.value == "historical"

    def test_live_analytical_value(self):
        assert SystemOperatingMode.LIVE_ANALYTICAL.value == "live_analytical"

    def test_hybrid_value(self):
        assert SystemOperatingMode.HYBRID.value == "hybrid"


# ---------------------------------------------------------------------------
# 2. RefreshPolicy is frozen
# ---------------------------------------------------------------------------

class TestRefreshPolicyFrozen:
    def test_frozen(self):
        policy = RefreshPolicy(
            interval_bars=1,
            on_regime_change=True,
            on_vol_spike=True,
            on_failure_mode=True,
            on_exposure_delta=True,
        )
        with pytest.raises(dataclasses.FrozenInstanceError):
            policy.interval_bars = 99

    def test_frozen_boolean_field(self):
        policy = RefreshPolicy(
            interval_bars=1,
            on_regime_change=True,
            on_vol_spike=True,
            on_failure_mode=True,
            on_exposure_delta=True,
        )
        with pytest.raises(dataclasses.FrozenInstanceError):
            policy.on_regime_change = False


# ---------------------------------------------------------------------------
# 3. REFRESH_POLICIES has 3 entries
# ---------------------------------------------------------------------------

class TestRefreshPoliciesDict:
    def test_has_three_entries(self):
        assert len(REFRESH_POLICIES) == 3

    def test_keys_are_operating_modes(self):
        assert set(REFRESH_POLICIES.keys()) == set(SystemOperatingMode)


# ---------------------------------------------------------------------------
# 4. HISTORICAL policy interval_bars=1
# ---------------------------------------------------------------------------

class TestHistoricalPolicy:
    def test_interval_bars(self):
        policy = REFRESH_POLICIES[SystemOperatingMode.HISTORICAL]
        assert policy.interval_bars == 1


# ---------------------------------------------------------------------------
# 5. LIVE_ANALYTICAL policy interval_bars=5
# ---------------------------------------------------------------------------

class TestLiveAnalyticalPolicy:
    def test_interval_bars(self):
        policy = REFRESH_POLICIES[SystemOperatingMode.LIVE_ANALYTICAL]
        assert policy.interval_bars == 5


# ---------------------------------------------------------------------------
# 6. HYBRID policy interval_bars=3
# ---------------------------------------------------------------------------

class TestHybridPolicy:
    def test_interval_bars(self):
        policy = REFRESH_POLICIES[SystemOperatingMode.HYBRID]
        assert policy.interval_bars == 3


# ---------------------------------------------------------------------------
# 7. All policies have all boolean flags True
# ---------------------------------------------------------------------------

class TestAllPoliciesBooleanFlags:
    @pytest.mark.parametrize("mode", list(SystemOperatingMode))
    def test_on_regime_change_true(self, mode):
        assert REFRESH_POLICIES[mode].on_regime_change is True

    @pytest.mark.parametrize("mode", list(SystemOperatingMode))
    def test_on_vol_spike_true(self, mode):
        assert REFRESH_POLICIES[mode].on_vol_spike is True

    @pytest.mark.parametrize("mode", list(SystemOperatingMode))
    def test_on_failure_mode_true(self, mode):
        assert REFRESH_POLICIES[mode].on_failure_mode is True

    @pytest.mark.parametrize("mode", list(SystemOperatingMode))
    def test_on_exposure_delta_true(self, mode):
        assert REFRESH_POLICIES[mode].on_exposure_delta is True
