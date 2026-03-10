# =============================================================================
# Unit Tests for jarvis/core/decision_context_state.py
# =============================================================================

import pytest
from collections import deque

from jarvis.core.decision_context_state import (
    MAX_DECISION_CONTEXT,
    DecisionRecord,
    DecisionContextState,
    DecisionContextSnapshot,
    _VALID_OUTCOMES,
)


# ---------------------------------------------------------------------------
# HELPERS
# ---------------------------------------------------------------------------

def _rec(seq=0, regime="RISK_ON", conf=0.5, outcome="NEUTRAL", strategy="strat_a"):
    return DecisionRecord(
        sequence_id=seq,
        regime_at_decision=regime,
        confidence_at_decision=conf,
        outcome=outcome,
        strategy_id=strategy,
    )


# ===================================================================
# TestConstants
# ===================================================================

class TestConstants:
    def test_max_decision_context_value(self):
        assert MAX_DECISION_CONTEXT == 200

    def test_valid_outcomes(self):
        assert _VALID_OUTCOMES == frozenset({"WIN", "LOSS", "NEUTRAL"})


# ===================================================================
# TestDecisionRecord
# ===================================================================

class TestDecisionRecord:
    def test_creation(self):
        r = _rec(seq=1, regime="RISK_ON", conf=0.8, outcome="WIN", strategy="momentum")
        assert r.sequence_id == 1
        assert r.regime_at_decision == "RISK_ON"
        assert r.confidence_at_decision == 0.8
        assert r.outcome == "WIN"
        assert r.strategy_id == "momentum"

    def test_frozen(self):
        r = _rec()
        with pytest.raises(AttributeError):
            r.outcome = "WIN"

    def test_equality(self):
        a = _rec(seq=1, outcome="WIN")
        b = _rec(seq=1, outcome="WIN")
        assert a == b

    def test_inequality(self):
        a = _rec(seq=1, outcome="WIN")
        b = _rec(seq=1, outcome="LOSS")
        assert a != b

    def test_hashable(self):
        r = _rec()
        s = {r}
        assert len(s) == 1

    # --- Validation ---
    def test_negative_sequence_id_raises(self):
        with pytest.raises(ValueError, match="sequence_id must be >= 0"):
            _rec(seq=-1)

    def test_sequence_id_zero_valid(self):
        r = _rec(seq=0)
        assert r.sequence_id == 0

    def test_confidence_below_zero_raises(self):
        with pytest.raises(ValueError, match="confidence_at_decision must be in"):
            _rec(conf=-0.1)

    def test_confidence_above_one_raises(self):
        with pytest.raises(ValueError, match="confidence_at_decision must be in"):
            _rec(conf=1.1)

    def test_confidence_zero_valid(self):
        r = _rec(conf=0.0)
        assert r.confidence_at_decision == 0.0

    def test_confidence_one_valid(self):
        r = _rec(conf=1.0)
        assert r.confidence_at_decision == 1.0

    def test_invalid_outcome_raises(self):
        with pytest.raises(ValueError, match="outcome must be one of"):
            _rec(outcome="DRAW")

    def test_empty_strategy_id_raises(self):
        with pytest.raises(ValueError, match="strategy_id must be a non-empty"):
            _rec(strategy="")

    def test_all_valid_outcomes(self):
        for oc in ("WIN", "LOSS", "NEUTRAL"):
            r = _rec(outcome=oc)
            assert r.outcome == oc


# ===================================================================
# TestDecisionContextSnapshot
# ===================================================================

class TestDecisionContextSnapshot:
    def test_creation(self):
        r = _rec(seq=0)
        snap = DecisionContextSnapshot(records=(r,), total_appended=1)
        assert len(snap.records) == 1
        assert snap.total_appended == 1

    def test_frozen(self):
        snap = DecisionContextSnapshot(records=(), total_appended=0)
        with pytest.raises(AttributeError):
            snap.total_appended = 5

    def test_empty(self):
        snap = DecisionContextSnapshot(records=(), total_appended=0)
        assert len(snap.records) == 0

    def test_records_is_tuple(self):
        snap = DecisionContextSnapshot(records=(_rec(),), total_appended=1)
        assert isinstance(snap.records, tuple)

    def test_equality(self):
        r = _rec(seq=0)
        a = DecisionContextSnapshot(records=(r,), total_appended=1)
        b = DecisionContextSnapshot(records=(r,), total_appended=1)
        assert a == b


# ===================================================================
# TestDecisionContextState
# ===================================================================

class TestDecisionContextState:
    def test_default_construction(self):
        state = DecisionContextState()
        assert len(state.records) == 0
        assert state.total_appended == 0

    def test_records_is_deque(self):
        state = DecisionContextState()
        assert isinstance(state.records, deque)

    def test_deque_maxlen(self):
        state = DecisionContextState()
        assert state.records.maxlen == MAX_DECISION_CONTEXT

    # --- append_record ---
    def test_append_record(self):
        state = DecisionContextState()
        r = _rec(seq=0)
        state.append_record(r)
        assert len(state.records) == 1
        assert state.total_appended == 1

    def test_append_multiple(self):
        state = DecisionContextState()
        for i in range(5):
            state.append_record(_rec(seq=i))
        assert len(state.records) == 5
        assert state.total_appended == 5

    def test_append_preserves_order(self):
        state = DecisionContextState()
        for i in range(3):
            state.append_record(_rec(seq=i))
        assert state.records[0].sequence_id == 0
        assert state.records[2].sequence_id == 2

    def test_append_evicts_oldest_at_max(self):
        state = DecisionContextState()
        for i in range(MAX_DECISION_CONTEXT + 5):
            state.append_record(_rec(seq=i))
        assert len(state.records) == MAX_DECISION_CONTEXT
        assert state.total_appended == MAX_DECISION_CONTEXT + 5
        # Oldest 5 evicted
        assert state.records[0].sequence_id == 5

    def test_append_non_record_raises(self):
        state = DecisionContextState()
        with pytest.raises(TypeError, match="record must be a DecisionRecord"):
            state.append_record({"not": "a record"})

    def test_total_appended_monotonic(self):
        state = DecisionContextState()
        for i in range(10):
            state.append_record(_rec(seq=i))
            assert state.total_appended == i + 1

    # --- snapshot ---
    def test_snapshot_returns_snapshot_type(self):
        state = DecisionContextState()
        snap = state.snapshot()
        assert isinstance(snap, DecisionContextSnapshot)

    def test_snapshot_empty(self):
        state = DecisionContextState()
        snap = state.snapshot()
        assert len(snap.records) == 0
        assert snap.total_appended == 0

    def test_snapshot_contains_records(self):
        state = DecisionContextState()
        state.append_record(_rec(seq=0))
        state.append_record(_rec(seq=1))
        snap = state.snapshot()
        assert len(snap.records) == 2
        assert snap.total_appended == 2

    def test_snapshot_is_frozen(self):
        state = DecisionContextState()
        state.append_record(_rec(seq=0))
        snap = state.snapshot()
        with pytest.raises(AttributeError):
            snap.total_appended = 99

    def test_snapshot_is_copy(self):
        """Snapshot does not reference the live deque."""
        state = DecisionContextState()
        state.append_record(_rec(seq=0))
        snap = state.snapshot()
        state.append_record(_rec(seq=1))
        assert len(snap.records) == 1  # snapshot unchanged
        assert len(state.records) == 2

    def test_snapshot_records_is_tuple(self):
        state = DecisionContextState()
        state.append_record(_rec(seq=0))
        snap = state.snapshot()
        assert isinstance(snap.records, tuple)

    # --- update_outcome ---
    def test_update_outcome_found(self):
        state = DecisionContextState()
        state.append_record(_rec(seq=0, outcome="NEUTRAL"))
        found = state.update_outcome(0, "WIN")
        assert found is True
        assert state.records[0].outcome == "WIN"

    def test_update_outcome_not_found(self):
        state = DecisionContextState()
        state.append_record(_rec(seq=0))
        found = state.update_outcome(99, "WIN")
        assert found is False

    def test_update_outcome_preserves_other_fields(self):
        state = DecisionContextState()
        state.append_record(_rec(seq=5, regime="CRISIS", conf=0.3, strategy="mean_rev"))
        state.update_outcome(5, "LOSS")
        r = state.records[0]
        assert r.sequence_id == 5
        assert r.regime_at_decision == "CRISIS"
        assert r.confidence_at_decision == 0.3
        assert r.strategy_id == "mean_rev"
        assert r.outcome == "LOSS"

    def test_update_outcome_invalid_raises(self):
        state = DecisionContextState()
        state.append_record(_rec(seq=0))
        with pytest.raises(ValueError, match="new_outcome must be one of"):
            state.update_outcome(0, "INVALID")

    def test_update_outcome_multiple_records(self):
        state = DecisionContextState()
        for i in range(5):
            state.append_record(_rec(seq=i, outcome="NEUTRAL"))
        state.update_outcome(2, "WIN")
        assert state.records[2].outcome == "WIN"
        # Others unchanged
        assert state.records[0].outcome == "NEUTRAL"
        assert state.records[4].outcome == "NEUTRAL"

    def test_update_outcome_preserves_order(self):
        state = DecisionContextState()
        for i in range(3):
            state.append_record(_rec(seq=i))
        state.update_outcome(1, "LOSS")
        assert [r.sequence_id for r in state.records] == [0, 1, 2]

    def test_update_does_not_change_total_appended(self):
        state = DecisionContextState()
        state.append_record(_rec(seq=0))
        state.update_outcome(0, "WIN")
        assert state.total_appended == 1


# ===================================================================
# TestDecisionContextStateDeterminism
# ===================================================================

class TestDecisionContextStateDeterminism:
    def test_snapshot_determinism(self):
        state = DecisionContextState()
        for i in range(5):
            state.append_record(_rec(seq=i, outcome="WIN" if i % 2 == 0 else "LOSS"))
        s1 = state.snapshot()
        s2 = state.snapshot()
        assert s1 == s2

    def test_fresh_state_per_instance(self):
        a = DecisionContextState()
        b = DecisionContextState()
        a.append_record(_rec(seq=0))
        assert len(a.records) == 1
        assert len(b.records) == 0


# ===================================================================
# TestGovernanceConstraints
# ===================================================================

class TestGovernanceConstraints:
    """Verify FAS governance constraints are encoded."""

    def test_no_capital_fields(self):
        """DecisionRecord must not have capital/PnL/account fields."""
        field_names = {f.name for f in DecisionRecord.__dataclass_fields__.values()}
        forbidden = {"capital", "pnl", "balance", "broker_id", "order_id", "account_id"}
        assert field_names.isdisjoint(forbidden)

    def test_decision_record_is_frozen(self):
        assert DecisionRecord.__dataclass_params__.frozen is True

    def test_decision_context_snapshot_is_frozen(self):
        assert DecisionContextSnapshot.__dataclass_params__.frozen is True

    def test_decision_context_state_is_mutable(self):
        assert DecisionContextState.__dataclass_params__.frozen is False

    def test_max_context_is_200(self):
        assert MAX_DECISION_CONTEXT == 200


# ===================================================================
# TestModuleAll
# ===================================================================

class TestModuleAll:
    def test_contains_max_decision_context(self):
        from jarvis.core.decision_context_state import __all__
        assert "MAX_DECISION_CONTEXT" in __all__

    def test_contains_outcome_classification(self):
        from jarvis.core.decision_context_state import __all__
        assert "OutcomeClassification" in __all__

    def test_contains_decision_record(self):
        from jarvis.core.decision_context_state import __all__
        assert "DecisionRecord" in __all__

    def test_contains_decision_context_state(self):
        from jarvis.core.decision_context_state import __all__
        assert "DecisionContextState" in __all__

    def test_contains_decision_context_snapshot(self):
        from jarvis.core.decision_context_state import __all__
        assert "DecisionContextSnapshot" in __all__

    def test_all_length(self):
        from jarvis.core.decision_context_state import __all__
        assert len(__all__) == 5
