# =============================================================================
# tests/unit/intelligence/test_regime_memory.py -- Regime Memory Tests
#
# Comprehensive tests for jarvis/intelligence/regime_memory.py (Phase MA-3).
# Covers: MultiAssetRegimeMemory, deque histories, transition detection,
#         transition counts, breakdown alerts, persistence, distribution,
#         determinism, edge cases.
# =============================================================================

import pytest

from jarvis.core.regime import (
    AssetClass,
    AssetRegimeState,
    CorrelationRegimeState,
    GlobalRegimeState,
    HierarchicalRegime,
)
from jarvis.intelligence.regime_memory import (
    # Constants
    DEFAULT_LOOKBACK_DAYS,
    ENTRIES_PER_DAY,
    # Dataclasses
    RegimeTransitionRecord,
    BreakdownAlert,
    # Main class
    MultiAssetRegimeMemory,
)


# ---------------------------------------------------------------------------
# SHARED FIXTURES
# ---------------------------------------------------------------------------

def _make_regime(
    global_regime: GlobalRegimeState = GlobalRegimeState.RISK_ON,
    correlation: CorrelationRegimeState = CorrelationRegimeState.NORMAL,
    asset_state: AssetRegimeState = AssetRegimeState.TRENDING_UP,
    sequence_id: int = 0,
) -> HierarchicalRegime:
    """Create a HierarchicalRegime with consistent defaults."""
    # CRISIS override invariant: if CRISIS, all assets must be SHOCK + correlation BREAKDOWN
    if global_regime == GlobalRegimeState.CRISIS:
        asset_state = AssetRegimeState.SHOCK
        correlation = CorrelationRegimeState.BREAKDOWN

    asset_regimes = {
        ac: asset_state for ac in AssetClass
    }
    asset_confidences = {
        ac: 0.8 for ac in AssetClass
    }
    sub_regime = {
        ac: "test_state" for ac in AssetClass
    }

    return HierarchicalRegime.create(
        global_regime=global_regime,
        asset_regimes=asset_regimes,
        correlation_regime=correlation,
        global_confidence=0.8,
        asset_confidences=asset_confidences,
        sub_regime=sub_regime,
        sequence_id=sequence_id,
    )


def _make_memory() -> MultiAssetRegimeMemory:
    return MultiAssetRegimeMemory()


# ---------------------------------------------------------------------------
# CONSTANTS
# ---------------------------------------------------------------------------

class TestConstants:
    def test_default_lookback_days(self):
        assert DEFAULT_LOOKBACK_DAYS == 365

    def test_entries_per_day(self):
        assert ENTRIES_PER_DAY == 24


# ---------------------------------------------------------------------------
# INITIALIZATION
# ---------------------------------------------------------------------------

class TestInitialization:
    def test_default_lookback(self):
        mem = _make_memory()
        assert mem.lookback_days == 365

    def test_custom_lookback(self):
        mem = MultiAssetRegimeMemory(lookback_days=30)
        assert mem.lookback_days == 30

    def test_empty_histories(self):
        mem = _make_memory()
        assert len(mem.global_history) == 0
        assert len(mem.correlation_history) == 0
        for ac in AssetClass:
            assert len(mem.asset_histories[ac]) == 0

    def test_empty_transitions(self):
        mem = _make_memory()
        assert len(mem.last_transition) == 0
        assert len(mem.transition_counts) == 0
        assert len(mem.transition_log) == 0

    def test_total_updates_zero(self):
        mem = _make_memory()
        assert mem.total_updates == 0

    def test_maxlen_correct(self):
        mem = MultiAssetRegimeMemory(lookback_days=10)
        assert mem.global_history.maxlen == 10 * 24

    def test_all_asset_histories_created(self):
        mem = _make_memory()
        for ac in AssetClass:
            assert ac in mem.asset_histories


# ---------------------------------------------------------------------------
# UPDATE
# ---------------------------------------------------------------------------

class TestUpdate:
    def test_single_update(self):
        mem = _make_memory()
        regime = _make_regime()
        alerts = mem.update(regime)
        assert mem.total_updates == 1
        assert len(alerts) == 0

    def test_global_history_appended(self):
        mem = _make_memory()
        mem.update(_make_regime(global_regime=GlobalRegimeState.RISK_ON))
        assert mem.global_history[-1] == GlobalRegimeState.RISK_ON

    def test_asset_history_appended(self):
        mem = _make_memory()
        mem.update(_make_regime(asset_state=AssetRegimeState.TRENDING_UP))
        for ac in AssetClass:
            assert mem.asset_histories[ac][-1] == AssetRegimeState.TRENDING_UP

    def test_correlation_history_appended(self):
        mem = _make_memory()
        mem.update(_make_regime(correlation=CorrelationRegimeState.NORMAL))
        assert mem.correlation_history[-1] == CorrelationRegimeState.NORMAL

    def test_multiple_updates(self):
        mem = _make_memory()
        for i in range(5):
            mem.update(_make_regime(sequence_id=i))
        assert mem.total_updates == 5

    def test_deque_maxlen_enforced(self):
        mem = MultiAssetRegimeMemory(lookback_days=1)
        # maxlen = 24
        for i in range(30):
            mem.update(_make_regime(sequence_id=i))
        assert len(mem.global_history) == 24

    def test_returns_empty_alerts_normally(self):
        mem = _make_memory()
        alerts = mem.update(_make_regime())
        assert alerts == []


# ---------------------------------------------------------------------------
# TRANSITION DETECTION -- GLOBAL
# ---------------------------------------------------------------------------

class TestGlobalTransitions:
    def test_no_transition_on_first_update(self):
        mem = _make_memory()
        mem.update(_make_regime(global_regime=GlobalRegimeState.RISK_ON))
        assert len(mem.transition_log) == 0

    def test_no_transition_same_state(self):
        mem = _make_memory()
        mem.update(_make_regime(global_regime=GlobalRegimeState.RISK_ON, sequence_id=0))
        mem.update(_make_regime(global_regime=GlobalRegimeState.RISK_ON, sequence_id=1))
        assert mem.get_transition_count("global_RISK_ON_to_RISK_OFF") == 0

    def test_transition_detected(self):
        mem = _make_memory()
        mem.update(_make_regime(global_regime=GlobalRegimeState.RISK_ON, sequence_id=0))
        mem.update(_make_regime(global_regime=GlobalRegimeState.RISK_OFF, sequence_id=1))
        key = "global_RISK_ON_to_RISK_OFF"
        assert mem.get_transition_count(key) == 1

    def test_transition_count_increments(self):
        mem = _make_memory()
        for i in range(6):
            state = GlobalRegimeState.RISK_ON if i % 2 == 0 else GlobalRegimeState.RISK_OFF
            mem.update(_make_regime(global_regime=state, sequence_id=i))
        assert mem.get_transition_count("global_RISK_ON_to_RISK_OFF") == 3
        assert mem.get_transition_count("global_RISK_OFF_to_RISK_ON") == 2

    def test_last_transition_stored(self):
        mem = _make_memory()
        mem.update(_make_regime(global_regime=GlobalRegimeState.RISK_ON, sequence_id=0))
        mem.update(_make_regime(global_regime=GlobalRegimeState.RISK_OFF, sequence_id=1))
        last = mem.get_last_transition("global")
        assert last is not None
        assert last.from_state == "RISK_ON"
        assert last.to_state == "RISK_OFF"
        assert last.dimension == "global"
        assert last.sequence_id == 1

    def test_transition_log_appended(self):
        mem = _make_memory()
        mem.update(_make_regime(global_regime=GlobalRegimeState.RISK_ON, sequence_id=0))
        mem.update(_make_regime(global_regime=GlobalRegimeState.RISK_OFF, sequence_id=1))
        log = mem.get_transition_log()
        assert len(log) >= 1
        global_transitions = [t for t in log if t.dimension == "global"]
        assert len(global_transitions) == 1


# ---------------------------------------------------------------------------
# TRANSITION DETECTION -- ASSET
# ---------------------------------------------------------------------------

class TestAssetTransitions:
    def test_asset_transition_detected(self):
        mem = _make_memory()
        mem.update(_make_regime(asset_state=AssetRegimeState.TRENDING_UP, sequence_id=0))
        mem.update(_make_regime(asset_state=AssetRegimeState.RANGING_TIGHT, sequence_id=1))
        # Should detect transitions for all 5 asset classes
        for ac in AssetClass:
            key = f"{ac.value}_TRENDING_UP_to_RANGING_TIGHT"
            assert mem.get_transition_count(key) == 1

    def test_asset_last_transition(self):
        mem = _make_memory()
        mem.update(_make_regime(asset_state=AssetRegimeState.TRENDING_UP, sequence_id=0))
        mem.update(_make_regime(asset_state=AssetRegimeState.HIGH_VOLATILITY, sequence_id=1))
        last = mem.get_last_transition("crypto")
        assert last is not None
        assert last.from_state == "TRENDING_UP"
        assert last.to_state == "HIGH_VOLATILITY"


# ---------------------------------------------------------------------------
# TRANSITION DETECTION -- CORRELATION
# ---------------------------------------------------------------------------

class TestCorrelationTransitions:
    def test_correlation_transition(self):
        mem = _make_memory()
        mem.update(_make_regime(correlation=CorrelationRegimeState.NORMAL, sequence_id=0))
        mem.update(_make_regime(correlation=CorrelationRegimeState.DIVERGENCE, sequence_id=1))
        key = "correlation_NORMAL_to_DIVERGENCE"
        assert mem.get_transition_count(key) == 1

    def test_correlation_last_transition(self):
        mem = _make_memory()
        mem.update(_make_regime(correlation=CorrelationRegimeState.NORMAL, sequence_id=0))
        mem.update(_make_regime(correlation=CorrelationRegimeState.COUPLED, sequence_id=1))
        last = mem.get_last_transition("correlation")
        assert last is not None
        assert last.from_state == "NORMAL"
        assert last.to_state == "COUPLED"


# ---------------------------------------------------------------------------
# BREAKDOWN ALERTS
# ---------------------------------------------------------------------------

class TestBreakdownAlerts:
    def test_breakdown_alert_generated(self):
        mem = _make_memory()
        mem.update(_make_regime(correlation=CorrelationRegimeState.NORMAL, sequence_id=0))
        # Transition to BREAKDOWN requires CRISIS global + SHOCK assets
        alerts = mem.update(_make_regime(
            global_regime=GlobalRegimeState.CRISIS,
            sequence_id=1,
        ))
        assert len(alerts) == 1
        assert isinstance(alerts[0], BreakdownAlert)
        assert alerts[0].previous_state == "NORMAL"
        assert alerts[0].sequence_id == 1

    def test_no_alert_if_already_breakdown(self):
        mem = _make_memory()
        mem.update(_make_regime(
            global_regime=GlobalRegimeState.CRISIS,
            sequence_id=0,
        ))
        # Same state, no transition
        alerts = mem.update(_make_regime(
            global_regime=GlobalRegimeState.CRISIS,
            sequence_id=1,
        ))
        assert len(alerts) == 0

    def test_no_alert_for_non_breakdown_transition(self):
        mem = _make_memory()
        mem.update(_make_regime(correlation=CorrelationRegimeState.NORMAL, sequence_id=0))
        alerts = mem.update(_make_regime(correlation=CorrelationRegimeState.DIVERGENCE, sequence_id=1))
        assert len(alerts) == 0

    def test_alert_not_persisted_between_updates(self):
        mem = _make_memory()
        mem.update(_make_regime(correlation=CorrelationRegimeState.NORMAL, sequence_id=0))
        mem.update(_make_regime(
            global_regime=GlobalRegimeState.CRISIS,
            sequence_id=1,
        ))
        # Next update with same state should not re-alert
        alerts = mem.update(_make_regime(
            global_regime=GlobalRegimeState.CRISIS,
            sequence_id=2,
        ))
        assert len(alerts) == 0


# ---------------------------------------------------------------------------
# GET HISTORY
# ---------------------------------------------------------------------------

class TestGetHistory:
    def test_get_global_history(self):
        mem = _make_memory()
        mem.update(_make_regime(global_regime=GlobalRegimeState.RISK_ON, sequence_id=0))
        mem.update(_make_regime(global_regime=GlobalRegimeState.RISK_OFF, sequence_id=1))
        hist = mem.get_global_history()
        assert hist == [GlobalRegimeState.RISK_ON, GlobalRegimeState.RISK_OFF]

    def test_get_asset_history(self):
        mem = _make_memory()
        mem.update(_make_regime(asset_state=AssetRegimeState.TRENDING_UP, sequence_id=0))
        hist = mem.get_asset_history(AssetClass.CRYPTO)
        assert hist == [AssetRegimeState.TRENDING_UP]

    def test_get_correlation_history(self):
        mem = _make_memory()
        mem.update(_make_regime(correlation=CorrelationRegimeState.NORMAL, sequence_id=0))
        hist = mem.get_correlation_history()
        assert hist == [CorrelationRegimeState.NORMAL]

    def test_history_returns_list_copy(self):
        mem = _make_memory()
        mem.update(_make_regime(sequence_id=0))
        hist = mem.get_global_history()
        hist.append(GlobalRegimeState.CRISIS)
        assert len(mem.global_history) == 1  # Original unchanged


# ---------------------------------------------------------------------------
# REGIME PERSISTENCE
# ---------------------------------------------------------------------------

class TestRegimePersistence:
    def test_persistence_empty(self):
        mem = _make_memory()
        assert mem.get_regime_persistence("global") == 0

    def test_persistence_single(self):
        mem = _make_memory()
        mem.update(_make_regime(sequence_id=0))
        assert mem.get_regime_persistence("global") == 1

    def test_persistence_consecutive(self):
        mem = _make_memory()
        for i in range(5):
            mem.update(_make_regime(global_regime=GlobalRegimeState.RISK_ON, sequence_id=i))
        assert mem.get_regime_persistence("global") == 5

    def test_persistence_after_change(self):
        mem = _make_memory()
        for i in range(3):
            mem.update(_make_regime(global_regime=GlobalRegimeState.RISK_ON, sequence_id=i))
        for i in range(2):
            mem.update(_make_regime(global_regime=GlobalRegimeState.RISK_OFF, sequence_id=3 + i))
        assert mem.get_regime_persistence("global") == 2

    def test_persistence_asset(self):
        mem = _make_memory()
        for i in range(4):
            mem.update(_make_regime(asset_state=AssetRegimeState.TRENDING_UP, sequence_id=i))
        assert mem.get_regime_persistence("crypto") == 4

    def test_persistence_correlation(self):
        mem = _make_memory()
        for i in range(3):
            mem.update(_make_regime(correlation=CorrelationRegimeState.NORMAL, sequence_id=i))
        assert mem.get_regime_persistence("correlation") == 3

    def test_persistence_unknown_dimension(self):
        mem = _make_memory()
        assert mem.get_regime_persistence("nonexistent") == 0


# ---------------------------------------------------------------------------
# STATE DISTRIBUTION
# ---------------------------------------------------------------------------

class TestStateDistribution:
    def test_empty_distribution(self):
        mem = _make_memory()
        assert mem.get_state_distribution("global") == {}

    def test_single_state(self):
        mem = _make_memory()
        mem.update(_make_regime(global_regime=GlobalRegimeState.RISK_ON, sequence_id=0))
        dist = mem.get_state_distribution("global")
        assert dist == {"RISK_ON": 1.0}

    def test_even_distribution(self):
        mem = _make_memory()
        mem.update(_make_regime(global_regime=GlobalRegimeState.RISK_ON, sequence_id=0))
        mem.update(_make_regime(global_regime=GlobalRegimeState.RISK_OFF, sequence_id=1))
        dist = mem.get_state_distribution("global")
        assert abs(dist["RISK_ON"] - 0.5) < 1e-10
        assert abs(dist["RISK_OFF"] - 0.5) < 1e-10

    def test_distribution_sums_to_one(self):
        mem = _make_memory()
        for i in range(10):
            state = [GlobalRegimeState.RISK_ON, GlobalRegimeState.RISK_OFF, GlobalRegimeState.TRANSITION][i % 3]
            mem.update(_make_regime(global_regime=state, sequence_id=i))
        dist = mem.get_state_distribution("global")
        assert abs(sum(dist.values()) - 1.0) < 1e-10

    def test_distribution_correlation(self):
        mem = _make_memory()
        mem.update(_make_regime(correlation=CorrelationRegimeState.NORMAL, sequence_id=0))
        mem.update(_make_regime(correlation=CorrelationRegimeState.NORMAL, sequence_id=1))
        mem.update(_make_regime(correlation=CorrelationRegimeState.DIVERGENCE, sequence_id=2))
        dist = mem.get_state_distribution("correlation")
        assert abs(dist["NORMAL"] - 2.0 / 3.0) < 1e-10
        assert abs(dist["DIVERGENCE"] - 1.0 / 3.0) < 1e-10

    def test_distribution_unknown_dimension(self):
        mem = _make_memory()
        assert mem.get_state_distribution("nonexistent") == {}


# ---------------------------------------------------------------------------
# TRANSITION RECORD DATACLASS
# ---------------------------------------------------------------------------

class TestRegimeTransitionRecord:
    def test_frozen(self):
        record = RegimeTransitionRecord(
            dimension="global",
            from_state="RISK_ON",
            to_state="RISK_OFF",
            timestamp="2026-01-01T00:00:00",
            sequence_id=1,
        )
        with pytest.raises(AttributeError):
            record.dimension = "other"

    def test_fields(self):
        record = RegimeTransitionRecord(
            dimension="crypto",
            from_state="TRENDING_UP",
            to_state="SHOCK",
            timestamp="2026-03-11T12:00:00",
            sequence_id=42,
        )
        assert record.dimension == "crypto"
        assert record.from_state == "TRENDING_UP"
        assert record.to_state == "SHOCK"
        assert record.sequence_id == 42


# ---------------------------------------------------------------------------
# BREAKDOWN ALERT DATACLASS
# ---------------------------------------------------------------------------

class TestBreakdownAlertDataclass:
    def test_frozen(self):
        alert = BreakdownAlert(
            timestamp="2026-01-01T00:00:00",
            sequence_id=5,
            previous_state="NORMAL",
        )
        with pytest.raises(AttributeError):
            alert.sequence_id = 10

    def test_fields(self):
        alert = BreakdownAlert(
            timestamp="2026-03-11T12:00:00",
            sequence_id=99,
            previous_state="COUPLED",
        )
        assert alert.timestamp == "2026-03-11T12:00:00"
        assert alert.sequence_id == 99
        assert alert.previous_state == "COUPLED"


# ---------------------------------------------------------------------------
# DETERMINISM (DET-05)
# ---------------------------------------------------------------------------

class TestDeterminism:
    def test_same_sequence_same_state(self):
        mem1 = _make_memory()
        mem2 = _make_memory()

        regimes = [
            _make_regime(global_regime=GlobalRegimeState.RISK_ON, sequence_id=0),
            _make_regime(global_regime=GlobalRegimeState.RISK_OFF, sequence_id=1),
            _make_regime(global_regime=GlobalRegimeState.RISK_ON, sequence_id=2),
        ]

        for r in regimes:
            mem1.update(r)
            mem2.update(r)

        assert mem1.get_global_history() == mem2.get_global_history()
        assert mem1.get_transition_count("global_RISK_ON_to_RISK_OFF") == \
               mem2.get_transition_count("global_RISK_ON_to_RISK_OFF")

    def test_independent_instances(self):
        mem1 = _make_memory()
        mem2 = _make_memory()
        mem1.update(_make_regime(sequence_id=0))
        assert mem1.total_updates == 1
        assert mem2.total_updates == 0


# ---------------------------------------------------------------------------
# EDGE CASES
# ---------------------------------------------------------------------------

class TestEdgeCases:
    def test_lookback_one_day(self):
        mem = MultiAssetRegimeMemory(lookback_days=1)
        assert mem.global_history.maxlen == 24

    def test_many_transitions_in_log(self):
        mem = _make_memory()
        states = [GlobalRegimeState.RISK_ON, GlobalRegimeState.RISK_OFF]
        for i in range(20):
            mem.update(_make_regime(global_regime=states[i % 2], sequence_id=i))
        log = mem.get_transition_log()
        # All asset transitions + global + correlation transitions counted
        assert len(log) > 0

    def test_get_transition_count_nonexistent(self):
        mem = _make_memory()
        assert mem.get_transition_count("nonexistent_key") == 0

    def test_get_last_transition_nonexistent(self):
        mem = _make_memory()
        assert mem.get_last_transition("nonexistent") is None


# ---------------------------------------------------------------------------
# PACKAGE IMPORT
# ---------------------------------------------------------------------------

class TestPackageImport:
    def test_import_all(self):
        from jarvis.intelligence.regime_memory import (
            MultiAssetRegimeMemory,
            RegimeTransitionRecord,
            BreakdownAlert,
            DEFAULT_LOOKBACK_DAYS,
            ENTRIES_PER_DAY,
        )
        assert MultiAssetRegimeMemory is not None
        assert RegimeTransitionRecord is not None
        assert BreakdownAlert is not None
