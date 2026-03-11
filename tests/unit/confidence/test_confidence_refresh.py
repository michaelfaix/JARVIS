# =============================================================================
# Tests for jarvis.confidence.confidence_refresh
# =============================================================================

import dataclasses

import pytest

from jarvis.confidence.confidence_refresh import (
    ConfidenceRefreshState,
    should_refresh_confidence,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_state(**overrides):
    """Create a default ConfidenceRefreshState with optional overrides."""
    defaults = dict(
        regime="RISK_ON",
        risk_mode="NORMAL",
        strategy_mode="MOMENTUM",
        ood_status=False,
        meta_uncertainty=0.2,
    )
    defaults.update(overrides)
    return ConfidenceRefreshState(**defaults)


# ---------------------------------------------------------------------------
# 1. HISTORICAL mode always returns True
# ---------------------------------------------------------------------------

class TestHistoricalMode:
    def test_always_true_same_state(self):
        s = _make_state()
        assert should_refresh_confidence(s, s, "historical") is True

    def test_always_true_different_state(self):
        s1 = _make_state(regime="RISK_ON")
        s2 = _make_state(regime="RISK_OFF")
        assert should_refresh_confidence(s1, s2, "historical") is True


# ---------------------------------------------------------------------------
# 2. LIVE mode with no state change returns False
# ---------------------------------------------------------------------------

class TestLiveNoChange:
    def test_no_change_returns_false(self):
        s = _make_state()
        assert should_refresh_confidence(s, s, "live_analytical") is False

    def test_identical_copies_returns_false(self):
        s1 = _make_state()
        s2 = _make_state()
        assert should_refresh_confidence(s1, s2, "live_analytical") is False


# ---------------------------------------------------------------------------
# 3. LIVE mode with regime change returns True
# ---------------------------------------------------------------------------

class TestLiveRegimeChange:
    def test_regime_change(self):
        s1 = _make_state(regime="RISK_ON")
        s2 = _make_state(regime="CRISIS")
        assert should_refresh_confidence(s1, s2, "live_analytical") is True


# ---------------------------------------------------------------------------
# 4. LIVE mode with risk_mode change returns True
# ---------------------------------------------------------------------------

class TestLiveRiskModeChange:
    def test_risk_mode_change(self):
        s1 = _make_state(risk_mode="NORMAL")
        s2 = _make_state(risk_mode="ELEVATED")
        assert should_refresh_confidence(s1, s2, "live_analytical") is True


# ---------------------------------------------------------------------------
# 5. LIVE mode with strategy_mode change returns True
# ---------------------------------------------------------------------------

class TestLiveStrategyModeChange:
    def test_strategy_mode_change(self):
        s1 = _make_state(strategy_mode="MOMENTUM")
        s2 = _make_state(strategy_mode="MEAN_REVERSION")
        assert should_refresh_confidence(s1, s2, "live_analytical") is True


# ---------------------------------------------------------------------------
# 6. LIVE mode with ood_status change returns True
# ---------------------------------------------------------------------------

class TestLiveOodStatusChange:
    def test_ood_status_change(self):
        s1 = _make_state(ood_status=False)
        s2 = _make_state(ood_status=True)
        assert should_refresh_confidence(s1, s2, "live_analytical") is True


# ---------------------------------------------------------------------------
# 7. LIVE mode with meta_uncertainty change returns True
# ---------------------------------------------------------------------------

class TestLiveMetaUncertaintyChange:
    def test_meta_uncertainty_change(self):
        s1 = _make_state(meta_uncertainty=0.2)
        s2 = _make_state(meta_uncertainty=0.8)
        assert should_refresh_confidence(s1, s2, "live_analytical") is True


# ---------------------------------------------------------------------------
# 8. HYBRID mode behaves like LIVE
# ---------------------------------------------------------------------------

class TestHybridMode:
    def test_no_change_returns_false(self):
        s = _make_state()
        assert should_refresh_confidence(s, s, "hybrid") is False

    def test_regime_change_returns_true(self):
        s1 = _make_state(regime="RISK_ON")
        s2 = _make_state(regime="RISK_OFF")
        assert should_refresh_confidence(s1, s2, "hybrid") is True

    def test_risk_mode_change_returns_true(self):
        s1 = _make_state(risk_mode="NORMAL")
        s2 = _make_state(risk_mode="CRITICAL")
        assert should_refresh_confidence(s1, s2, "hybrid") is True


# ---------------------------------------------------------------------------
# 9. ConfidenceRefreshState is frozen
# ---------------------------------------------------------------------------

class TestFrozenDataclass:
    def test_frozen(self):
        s = _make_state()
        with pytest.raises(dataclasses.FrozenInstanceError):
            s.regime = "CHANGED"

    def test_frozen_risk_mode(self):
        s = _make_state()
        with pytest.raises(dataclasses.FrozenInstanceError):
            s.risk_mode = "CHANGED"


# ---------------------------------------------------------------------------
# 10. Determinism -- same inputs produce same outputs
# ---------------------------------------------------------------------------

class TestDeterminism:
    def test_deterministic_historical(self):
        s1 = _make_state()
        s2 = _make_state()
        results = [should_refresh_confidence(s1, s2, "historical") for _ in range(100)]
        assert all(r is True for r in results)

    def test_deterministic_live_no_change(self):
        s1 = _make_state()
        s2 = _make_state()
        results = [should_refresh_confidence(s1, s2, "live_analytical") for _ in range(100)]
        assert all(r is False for r in results)

    def test_deterministic_live_change(self):
        s1 = _make_state(regime="RISK_ON")
        s2 = _make_state(regime="CRISIS")
        results = [should_refresh_confidence(s1, s2, "live_analytical") for _ in range(100)]
        assert all(r is True for r in results)


# ---------------------------------------------------------------------------
# 11. Import contract
# ---------------------------------------------------------------------------

class TestImportContract:
    def test_import_from_module(self):
        from jarvis.confidence.confidence_refresh import (
            ConfidenceRefreshState,
            should_refresh_confidence,
        )
        assert ConfidenceRefreshState is not None
        assert should_refresh_confidence is not None

    def test_import_from_package(self):
        from jarvis.confidence import (
            ConfidenceRefreshState,
            should_refresh_confidence,
        )
        assert ConfidenceRefreshState is not None
        assert should_refresh_confidence is not None
