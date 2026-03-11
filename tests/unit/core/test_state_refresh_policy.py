# =============================================================================
# tests/unit/core/test_state_refresh_policy.py
# Tests for jarvis/core/state_refresh_policy.py
# =============================================================================

import pytest

from jarvis.core.system_mode import SystemMode
from jarvis.core.state_refresh_policy import (
    RefreshPolicy,
    REFRESH_POLICIES,
    get_refresh_policy,
    is_recompute_allowed,
    is_incremental_only,
)


# =============================================================================
# SECTION 1 -- REFRESH POLICY DATACLASS
# =============================================================================

class TestRefreshPolicy:
    """Test RefreshPolicy frozen dataclass."""

    def test_frozen(self):
        policy = REFRESH_POLICIES[SystemMode.HISTORICAL]
        with pytest.raises(AttributeError):
            policy.mode = SystemMode.LIVE_ANALYTICAL

    def test_all_fields_present(self):
        from dataclasses import fields as dc_fields
        names = {f.name for f in dc_fields(RefreshPolicy)}
        expected = {
            "mode", "full_recompute_allowed", "backtest_loop_allowed",
            "incremental_only", "rolling_window_updates",
            "deterministic_cycle", "backfill_allowed",
            "live_sync_point_required",
        }
        assert names == expected

    def test_field_count(self):
        from dataclasses import fields as dc_fields
        assert len(dc_fields(RefreshPolicy)) == 8

    def test_equality(self):
        p1 = RefreshPolicy(
            mode=SystemMode.HISTORICAL,
            full_recompute_allowed=True,
            backtest_loop_allowed=True,
            incremental_only=False,
            rolling_window_updates=False,
            deterministic_cycle=True,
            backfill_allowed=True,
            live_sync_point_required=False,
        )
        p2 = REFRESH_POLICIES[SystemMode.HISTORICAL]
        assert p1 == p2


# =============================================================================
# SECTION 2 -- REFRESH POLICIES TABLE
# =============================================================================

class TestRefreshPoliciesTable:
    """Test REFRESH_POLICIES mapping completeness."""

    def test_all_modes_covered(self):
        for mode in SystemMode:
            assert mode in REFRESH_POLICIES

    def test_is_dict(self):
        assert isinstance(REFRESH_POLICIES, dict)

    def test_count(self):
        assert len(REFRESH_POLICIES) == 3

    def test_values_are_refresh_policies(self):
        for mode, policy in REFRESH_POLICIES.items():
            assert isinstance(policy, RefreshPolicy)

    def test_mode_field_matches_key(self):
        for mode, policy in REFRESH_POLICIES.items():
            assert policy.mode == mode


# =============================================================================
# SECTION 3 -- HISTORICAL MODE
# =============================================================================

class TestHistoricalPolicy:
    """Test HISTORICAL mode policy (FAS lines 6942-6953)."""

    @pytest.fixture
    def policy(self):
        return REFRESH_POLICIES[SystemMode.HISTORICAL]

    def test_full_recompute_allowed(self, policy):
        assert policy.full_recompute_allowed is True

    def test_backtest_loop_allowed(self, policy):
        assert policy.backtest_loop_allowed is True

    def test_not_incremental_only(self, policy):
        assert policy.incremental_only is False

    def test_no_rolling_window(self, policy):
        assert policy.rolling_window_updates is False

    def test_deterministic_cycle(self, policy):
        assert policy.deterministic_cycle is True

    def test_backfill_allowed(self, policy):
        assert policy.backfill_allowed is True

    def test_no_sync_point_required(self, policy):
        assert policy.live_sync_point_required is False


# =============================================================================
# SECTION 4 -- LIVE_ANALYTICAL MODE
# =============================================================================

class TestLiveAnalyticalPolicy:
    """Test LIVE_ANALYTICAL mode policy (FAS lines 6954-6963)."""

    @pytest.fixture
    def policy(self):
        return REFRESH_POLICIES[SystemMode.LIVE_ANALYTICAL]

    def test_no_full_recompute(self, policy):
        assert policy.full_recompute_allowed is False

    def test_no_backtest_loop(self, policy):
        assert policy.backtest_loop_allowed is False

    def test_incremental_only(self, policy):
        assert policy.incremental_only is True

    def test_rolling_window_updates(self, policy):
        assert policy.rolling_window_updates is True

    def test_deterministic_cycle(self, policy):
        assert policy.deterministic_cycle is True

    def test_no_backfill(self, policy):
        assert policy.backfill_allowed is False

    def test_no_sync_point_required(self, policy):
        assert policy.live_sync_point_required is False


# =============================================================================
# SECTION 5 -- HYBRID MODE
# =============================================================================

class TestHybridPolicy:
    """Test HYBRID mode policy (FAS lines 6964-6973)."""

    @pytest.fixture
    def policy(self):
        return REFRESH_POLICIES[SystemMode.HYBRID]

    def test_full_recompute_allowed(self, policy):
        assert policy.full_recompute_allowed is True

    def test_backtest_loop_allowed(self, policy):
        assert policy.backtest_loop_allowed is True

    def test_not_incremental_only(self, policy):
        """Before sync_point, batch is allowed."""
        assert policy.incremental_only is False

    def test_rolling_window_updates(self, policy):
        assert policy.rolling_window_updates is True

    def test_deterministic_cycle(self, policy):
        assert policy.deterministic_cycle is True

    def test_backfill_allowed(self, policy):
        assert policy.backfill_allowed is True

    def test_sync_point_required(self, policy):
        assert policy.live_sync_point_required is True


# =============================================================================
# SECTION 6 -- get_refresh_policy()
# =============================================================================

class TestGetRefreshPolicy:
    """Test get_refresh_policy lookup function."""

    def test_historical(self):
        p = get_refresh_policy(SystemMode.HISTORICAL)
        assert p.mode == SystemMode.HISTORICAL

    def test_live_analytical(self):
        p = get_refresh_policy(SystemMode.LIVE_ANALYTICAL)
        assert p.mode == SystemMode.LIVE_ANALYTICAL

    def test_hybrid(self):
        p = get_refresh_policy(SystemMode.HYBRID)
        assert p.mode == SystemMode.HYBRID

    def test_returns_same_as_dict(self):
        for mode in SystemMode:
            assert get_refresh_policy(mode) == REFRESH_POLICIES[mode]

    def test_type_error_string(self):
        with pytest.raises(TypeError, match="must be a SystemMode"):
            get_refresh_policy("HISTORICAL")

    def test_type_error_int(self):
        with pytest.raises(TypeError, match="must be a SystemMode"):
            get_refresh_policy(1)

    def test_type_error_none(self):
        with pytest.raises(TypeError, match="must be a SystemMode"):
            get_refresh_policy(None)


# =============================================================================
# SECTION 7 -- is_recompute_allowed()
# =============================================================================

class TestIsRecomputeAllowed:
    """Test is_recompute_allowed predicate."""

    def test_historical_true(self):
        assert is_recompute_allowed(SystemMode.HISTORICAL) is True

    def test_live_analytical_false(self):
        assert is_recompute_allowed(SystemMode.LIVE_ANALYTICAL) is False

    def test_hybrid_true(self):
        assert is_recompute_allowed(SystemMode.HYBRID) is True

    def test_type_error(self):
        with pytest.raises(TypeError, match="must be a SystemMode"):
            is_recompute_allowed("HISTORICAL")


# =============================================================================
# SECTION 8 -- is_incremental_only()
# =============================================================================

class TestIsIncrementalOnly:
    """Test is_incremental_only predicate."""

    def test_historical_false(self):
        assert is_incremental_only(SystemMode.HISTORICAL) is False

    def test_live_analytical_true(self):
        assert is_incremental_only(SystemMode.LIVE_ANALYTICAL) is True

    def test_hybrid_false(self):
        assert is_incremental_only(SystemMode.HYBRID) is False

    def test_type_error(self):
        with pytest.raises(TypeError, match="must be a SystemMode"):
            is_incremental_only("LIVE_ANALYTICAL")


# =============================================================================
# SECTION 9 -- DETERMINISM
# =============================================================================

class TestDeterminism:
    """Test deterministic behavior (DET-07)."""

    def test_policies_stable(self):
        """Same mode always returns identical policy."""
        for mode in SystemMode:
            p1 = get_refresh_policy(mode)
            p2 = get_refresh_policy(mode)
            assert p1 == p2

    def test_all_modes_deterministic_cycle(self):
        """FAS: deterministic_cycle is True for ALL modes."""
        for mode in SystemMode:
            assert get_refresh_policy(mode).deterministic_cycle is True


# =============================================================================
# SECTION 10 -- MODE CONSTRAINT INVARIANTS
# =============================================================================

class TestModeConstraints:
    """Test FAS mode constraint invariants."""

    def test_historical_allows_batch(self):
        """HISTORICAL must allow batch processing."""
        p = get_refresh_policy(SystemMode.HISTORICAL)
        assert p.full_recompute_allowed is True
        assert p.incremental_only is False

    def test_live_prohibits_recompute(self):
        """LIVE_ANALYTICAL must prohibit full recompute."""
        p = get_refresh_policy(SystemMode.LIVE_ANALYTICAL)
        assert p.full_recompute_allowed is False
        assert p.backtest_loop_allowed is False
        assert p.backfill_allowed is False

    def test_hybrid_requires_sync_point(self):
        """HYBRID must require sync_point for window separation."""
        p = get_refresh_policy(SystemMode.HYBRID)
        assert p.live_sync_point_required is True

    def test_only_hybrid_requires_sync_point(self):
        """Only HYBRID should require sync_point."""
        for mode in SystemMode:
            p = get_refresh_policy(mode)
            if mode == SystemMode.HYBRID:
                assert p.live_sync_point_required is True
            else:
                assert p.live_sync_point_required is False

    def test_only_live_is_incremental_only(self):
        """Only LIVE_ANALYTICAL should be incremental_only."""
        for mode in SystemMode:
            p = get_refresh_policy(mode)
            if mode == SystemMode.LIVE_ANALYTICAL:
                assert p.incremental_only is True
            else:
                assert p.incremental_only is False
