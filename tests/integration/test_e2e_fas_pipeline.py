# =============================================================================
# tests/integration/test_e2e_fas_pipeline.py
#
# End-to-end integration test exercising the full FAS module chain:
#
#   IntegrityLayer (hash-chain boot)
#   → GlobalSystemStateController (state mutations)
#   → EventBus (event creation & routing)
#   → ControlFlow (11-layer pipeline execution)
#   → ValidationGates (per-gate checks)
#   → GovernanceMonitor (mutation permission audit)
#   → TrustScore (composite system health)
#   → FragilityIndex (structural fragility)
#
# Simulates a realistic analytical cycle:
#   1. System boot:   Verify threshold integrity, init hash chain.
#   2. Normal cycle:  Good data, all gates pass, HIGH trust.
#   3. Stress cycle:  Regime shift, elevated vol, OOD detected.
#   4. Recovery:      System returns to normal via mode transitions.
#   5. Determinism:   Entire sequence is bit-identical on replay.
# =============================================================================

import pytest

# --- Core ---
from jarvis.core.integrity_layer import IntegrityLayer
from jarvis.core.global_state_controller import (
    GlobalSystemStateController,
    GlobalState,
)
from jarvis.core.event_bus import (
    EventType,
    MarketDataEvent,
    RegimeChangeEvent,
    FailureModeEvent,
    ConfidenceUpdateEvent,
)
from jarvis.core.governance_monitor import (
    GovernanceMonitor,
    PERMITTED_CALLERS,
)

# --- Systems ---
from jarvis.systems.control_flow import (
    ControlSignal,
    SystemControlFlow,
)
from jarvis.systems.validation_gates import (
    QualityGate,
    DriftGate,
    KalmanGate,
    ECEGate,
    OODGate,
    RiskGate,
    GateResult,
)
from jarvis.systems.mode_controller import (
    OperationalMode,
    ModeController,
)

# --- Metrics ---
from jarvis.metrics.trust_score import TrustScoreEngine, TRUST_HIGH
from jarvis.metrics.fragility_index import (
    StructuralFragilityIndex,
    FRAGILITY_LOW_THRESHOLD,
)


# =============================================================================
# FIXTURES
# =============================================================================

@pytest.fixture(autouse=True)
def _reset_global_state():
    """Reset the singleton before and after each test."""
    GlobalSystemStateController._reset_singleton()
    yield
    GlobalSystemStateController._reset_singleton()


# =============================================================================
# HELPERS
# =============================================================================

def _run_all_gates(
    quality: float,
    drift: float,
    condition: float,
    ece: float,
    is_ood: bool,
    var: float,
) -> dict:
    """Run all 6 validation gates and return name→GateResult map."""
    return {
        "quality": QualityGate().check(quality),
        "drift": DriftGate().check(drift),
        "kalman": KalmanGate().check(condition),
        "ece": ECEGate().check(ece),
        "ood": OODGate().check(is_ood),
        "risk": RiskGate().check(var),
    }


# =============================================================================
# SCENARIO 1 -- SYSTEM BOOT & INTEGRITY CHECK
# =============================================================================

class TestSystemBoot:
    """Verify system can boot: threshold integrity, hash chain init, state init."""

    def test_threshold_manifest_round_trip(self):
        il = IntegrityLayer()
        manifest = il.create_threshold_manifest(version="6.1.0")
        # Must not raise — thresholds are intact
        il.verify_threshold_manifest(manifest)

    def test_hash_chain_init_and_append(self):
        il = IntegrityLayer()
        chain = il.init_hash_chain("SYSTEM_BOOT")
        assert len(chain.events) == 0

        il.append_to_chain(chain, "BOOT_COMPLETE", {"version": "6.1.0"})
        assert len(chain.events) == 1

        verification = il.verify_chain(chain)
        assert verification.valid is True

    def test_global_state_initial(self):
        ctrl = GlobalSystemStateController.get_instance()
        state = ctrl.get_state()
        assert isinstance(state, GlobalState)
        assert state.mode == "RUNNING"
        assert state.risk_mode == "NORMAL"
        assert state.ood_status == "NORMAL"
        assert state.version == 1


# =============================================================================
# SCENARIO 2 -- NORMAL ANALYTICAL CYCLE
# =============================================================================

class TestNormalCycle:
    """
    Simulate a healthy cycle: good data quality, no OOD, low vol.
    All gates pass, pipeline completes, trust is HIGH, fragility LOW.
    """

    def test_full_normal_cycle(self):
        # ---- 1. Global state: normal conditions ----
        ctrl = GlobalSystemStateController.get_instance()
        ctrl.update(
            regime="RISK_ON",
            regime_confidence=0.85,
            meta_uncertainty=0.1,
            vol_regime="NORMAL",
            realized_vol=0.15,
            forecast_vol=0.16,
        )
        state = ctrl.get_state()
        assert state.regime == "RISK_ON"
        assert state.version == 2

        # ---- 2. Market data event ----
        evt = MarketDataEvent(
            event_id="MD-001",
            event_type=EventType.MARKET_DATA,
            timestamp=1000.0,
            sequence_id=1,
            asset_id="BTC",
            symbol="BTCUSD",
            timeframe="1H",
            close=65000.0,
            quality_score=0.95,
            data_source="historical",
        )
        assert evt.quality_score == 0.95

        # ---- 3. Validation gates (all pass) ----
        gates = _run_all_gates(
            quality=0.95,
            drift=0.20,
            condition=50.0,
            ece=0.02,
            is_ood=False,
            var=-0.05,
        )
        for name, gate_result in gates.items():
            assert gate_result.passed is True, f"Gate {name} should pass"

        # ---- 4. Pipeline control flow ----
        flow_states = SystemControlFlow().execute(
            quality_score=0.95,
            drift_severity=0.20,
            condition_number=50.0,
            ece=0.02,
            is_ood=False,
            var=-0.05,
        )
        # All 11 layers should execute
        assert len(flow_states) == 11
        assert all(
            fs.signal == ControlSignal.CONTINUE
            for fs in flow_states
        )

        # ---- 5. Governance: permitted mutation ----
        mon = GovernanceMonitor()
        audit = mon.check_update_permission(
            "regime_engine", ("regime_confidence",)
        )
        assert audit.permitted is True

        # ---- 6. Trust score ----
        trust = TrustScoreEngine().compute(
            ece=0.02,
            ood_recall=0.95,
            prediction_variance=0.01,
            drawdown=0.03,
            uptime=0.99,
        )
        assert trust.trust_score >= TRUST_HIGH
        assert trust.classification == "HIGH"

        # ---- 7. Fragility index ----
        fragility = StructuralFragilityIndex().compute(
            coupling_score=0.1,
            propagation_score=0.05,
            recovery_score=0.1,
            cascade_score=0.02,
        )
        assert fragility.fragility_index < FRAGILITY_LOW_THRESHOLD
        assert fragility.classification == "LOW"

    def test_governance_confidence_emitter_enforced(self):
        """Only confidence_engine may emit ConfidenceUpdateEvent."""
        mon = GovernanceMonitor()

        # Permitted
        assert mon.check_confidence_emitter("confidence_engine") is None

        # Blocked
        violation = mon.check_confidence_emitter("risk_engine")
        assert violation is not None
        assert violation.rule_name == "confidence_trigger_required"


# =============================================================================
# SCENARIO 3 -- STRESS CYCLE (REGIME SHIFT + OOD + VOL SPIKE)
# =============================================================================

class TestStressCycle:
    """
    Simulate a stress event: regime shift to CRISIS, OOD detected,
    vol spike.  Pipeline degrades, trust drops, fragility rises.
    """

    def test_full_stress_cycle(self):
        ctrl = GlobalSystemStateController.get_instance()

        # ---- 1. Regime shift event ----
        regime_evt = RegimeChangeEvent(
            event_id="RC-001",
            event_type=EventType.REGIME_CHANGE,
            timestamp=2000.0,
            sequence_id=10,
            from_regime="RISK_ON",
            to_regime="CRISIS",
            confidence=0.75,
            transition_flag=True,
        )
        assert regime_evt.to_regime == "CRISIS"

        # ---- 2. Update state: stress conditions ----
        ctrl.update(
            regime="CRISIS",
            regime_confidence=0.75,
            regime_transition_flag=True,
            meta_uncertainty=0.7,
            vol_regime="SPIKE",
            vol_spike_flag=True,
            realized_vol=0.45,
            forecast_vol=0.50,
            ood_status="ELEVATED",
            risk_mode="ELEVATED",
        )
        state = ctrl.get_state()
        assert state.regime == "CRISIS"
        assert state.vol_spike_flag is True
        assert state.ood_status == "ELEVATED"

        # ---- 3. Failure mode event (FM-02: vol spike) ----
        fm_evt = FailureModeEvent(
            event_id="FM-002",
            event_type=EventType.FAILURE_MODE,
            timestamp=2001.0,
            sequence_id=11,
            failure_mode_code="FM-02",
            activated=True,
            trigger_condition="NVU > 3.0",
            confidence_impact={"mu": -0.10, "Q": -0.15},
        )
        assert fm_evt.failure_mode_code == "FM-02"

        # ---- 4. Gates: OOD fails, quality degraded ----
        gates = _run_all_gates(
            quality=0.60,
            drift=0.50,
            condition=200.0,
            ece=0.03,
            is_ood=True,
            var=-0.10,
        )
        assert gates["quality"].passed is True   # 0.60 >= 0.50
        assert gates["ood"].passed is False       # is_ood=True → fail
        assert gates["risk"].passed is True       # -0.10 >= -0.15

        # ---- 5. Pipeline: OOD gate at layer 7 → DEGRADE + early exit ----
        flow_states = SystemControlFlow().execute(
            quality_score=0.60,
            drift_severity=0.50,
            condition_number=200.0,
            ece=0.03,
            is_ood=True,
            var=-0.10,
        )
        # Pipeline halts at layer 7 (DEGRADE triggers early exit)
        assert len(flow_states) == 7
        ood_layer = flow_states[-1]
        assert ood_layer.layer_name == "ood_detection"
        assert ood_layer.signal == ControlSignal.DEGRADE
        assert ood_layer.gate_passed is False

        # ---- 6. Mode transition: NORMAL → DEFENSIVE ----
        mc = ModeController()
        transition = mc.transition(OperationalMode.NORMAL, "ood_detected")
        assert transition.accepted is True
        assert transition.new_mode == OperationalMode.DEFENSIVE

        # ---- 7. Governance: unauthorized mutation blocked ----
        mon = GovernanceMonitor()
        audit = mon.check_update_permission(
            "unknown_module", ("regime_confidence",)
        )
        assert audit.permitted is False
        assert audit.violation.rule_name == "single_ctrl_update"

        # ---- 8. Trust drops significantly ----
        trust = TrustScoreEngine().compute(
            ece=0.04,
            ood_recall=0.50,
            prediction_variance=0.08,
            drawdown=0.12,
            uptime=0.90,
        )
        assert trust.trust_score < TRUST_HIGH
        assert trust.classification in ("MEDIUM", "LOW", "CRITICAL")

        # ---- 9. Fragility rises ----
        fragility = StructuralFragilityIndex().compute(
            coupling_score=0.7,
            propagation_score=0.6,
            recovery_score=0.5,
            cascade_score=0.4,
        )
        assert fragility.fragility_index > FRAGILITY_LOW_THRESHOLD
        assert fragility.classification in ("MEDIUM", "HIGH", "CRITICAL")

    def test_confidence_update_event_during_stress(self):
        """ConfidenceUpdateEvent tracks degradation."""
        conf_evt = ConfidenceUpdateEvent(
            event_id="CU-001",
            event_type=EventType.CONFIDENCE_UPDATE,
            timestamp=2002.0,
            sequence_id=12,
            prior_mu=0.80,
            new_mu=0.60,
            prior_Q=0.85,
            new_Q=0.65,
            prior_U=0.15,
            new_U=0.40,
            trigger="FM-02_activated",
        )
        assert conf_evt.new_mu < conf_evt.prior_mu
        assert conf_evt.new_Q < conf_evt.prior_Q
        assert conf_evt.new_U > conf_evt.prior_U


# =============================================================================
# SCENARIO 4 -- RECOVERY CYCLE
# =============================================================================

class TestRecoveryCycle:
    """
    Simulate recovery: OOD clears, vol normalizes, mode returns to NORMAL.
    Trust recovers, fragility drops.
    """

    def test_full_recovery_cycle(self):
        ctrl = GlobalSystemStateController.get_instance()

        # Start from stress state
        ctrl.update(
            regime="CRISIS",
            meta_uncertainty=0.7,
            vol_regime="SPIKE",
            ood_status="ELEVATED",
            risk_mode="ELEVATED",
        )

        # ---- 1. Recovery: vol normalizes, OOD clears ----
        ctrl.update(
            regime="RISK_ON",
            regime_confidence=0.80,
            regime_transition_flag=False,
            meta_uncertainty=0.15,
            vol_regime="NORMAL",
            vol_spike_flag=False,
            realized_vol=0.18,
            forecast_vol=0.19,
            ood_status="NORMAL",
            risk_mode="NORMAL",
        )
        state = ctrl.get_state()
        assert state.regime == "RISK_ON"
        assert state.vol_spike_flag is False
        assert state.ood_status == "NORMAL"

        # ---- 2. Mode: DEFENSIVE → NORMAL ----
        mc = ModeController()
        transition = mc.transition(OperationalMode.DEFENSIVE, "ood_cleared")
        assert transition.accepted is True
        assert transition.new_mode == OperationalMode.NORMAL

        # ---- 3. All gates pass again ----
        gates = _run_all_gates(
            quality=0.90,
            drift=0.15,
            condition=30.0,
            ece=0.01,
            is_ood=False,
            var=-0.03,
        )
        assert all(g.passed for g in gates.values())

        # ---- 4. Pipeline: all CONTINUE ----
        flow = SystemControlFlow().execute(
            quality_score=0.90,
            drift_severity=0.15,
            condition_number=30.0,
            ece=0.01,
            is_ood=False,
            var=-0.03,
        )
        assert len(flow) == 11
        assert all(fs.signal == ControlSignal.CONTINUE for fs in flow)

        # ---- 5. Trust recovers ----
        trust = TrustScoreEngine().compute(
            ece=0.01,
            ood_recall=0.95,
            prediction_variance=0.02,
            drawdown=0.04,
            uptime=0.98,
        )
        assert trust.trust_score >= TRUST_HIGH

        # ---- 6. Fragility drops ----
        fragility = StructuralFragilityIndex().compute(
            coupling_score=0.15,
            propagation_score=0.05,
            recovery_score=0.10,
            cascade_score=0.02,
        )
        assert fragility.fragility_index < FRAGILITY_LOW_THRESHOLD
        assert fragility.classification == "LOW"


# =============================================================================
# SCENARIO 5 -- EMERGENCY SHUTDOWN PATH
# =============================================================================

class TestEmergencyPath:
    """
    Simulate critical failure → emergency shutdown.
    Pipeline STOPs, trust collapses, mode goes EMERGENCY.
    """

    def test_emergency_shutdown_chain(self):
        ctrl = GlobalSystemStateController.get_instance()

        # ---- 1. Risk gate fails: VaR breach ----
        risk_gate = RiskGate().check(-0.25)
        assert risk_gate.passed is False

        # ---- 2. Pipeline: risk layer 8 → EMERGENCY ----
        flow = SystemControlFlow().execute(
            quality_score=0.30,
            drift_severity=0.90,
            condition_number=1e6,
            ece=0.08,
            is_ood=True,
            var=-0.25,
        )
        # Pipeline stops early at layer 1 (quality < 0.50 → STOP)
        stopped_at = next(
            fs for fs in flow if fs.signal == ControlSignal.STOP
        )
        assert stopped_at is not None

        # ---- 3. Mode: NORMAL → EMERGENCY ----
        mc = ModeController()
        transition = mc.transition(
            OperationalMode.NORMAL, "critical_failure"
        )
        assert transition.new_mode == OperationalMode.EMERGENCY

        # EMERGENCY requires manual_recovery
        available = mc.get_available_triggers(OperationalMode.EMERGENCY)
        assert "manual_recovery" in available
        assert "stability_restored" not in available

        # ---- 4. Emergency shutdown on controller ----
        ctrl.emergency_shutdown("VaR breach + OOD + critical failure")
        state = ctrl.get_state()
        assert state.mode == "EMERGENCY"
        assert state.deployment_blocked is True
        assert state.risk_compression is True

        # ---- 5. Trust: CRITICAL ----
        trust = TrustScoreEngine().compute(
            ece=0.05,
            ood_recall=0.10,
            prediction_variance=0.10,
            drawdown=0.15,
            uptime=0.50,
        )
        assert trust.classification == "CRITICAL"

        # ---- 6. Fragility: CRITICAL ----
        fragility = StructuralFragilityIndex().compute(
            coupling_score=0.9,
            propagation_score=0.9,
            recovery_score=0.8,
            cascade_score=0.8,
        )
        assert fragility.classification == "CRITICAL"

        # ---- 7. Sync point immutability enforced ----
        mon = GovernanceMonitor()
        v = mon.check_sync_point_immutability(
            already_set=True, caller_module="hybrid_coordinator"
        )
        assert v is not None
        assert v.rule_name == "sync_point_immutability"


# =============================================================================
# SCENARIO 6 -- GOVERNANCE BATCH AUDIT
# =============================================================================

class TestGovernanceBatchAudit:
    """
    Validate a batch of state mutation requests against PERMITTED_CALLERS.
    Mix of legitimate and unauthorized callers.
    """

    def test_batch_audit(self):
        mon = GovernanceMonitor()
        entries = [
            # Permitted
            ("regime_engine", ("regime_confidence", "regime_probs")),
            ("risk_engine", ("risk_mode", "risk_compression")),
            ("confidence_engine", ("meta_uncertainty",)),
            ("replay_engine", ("regime", "vol_regime", "mode")),
            # Violations
            ("rogue_module", ("regime_confidence",)),
            ("risk_engine", ("meta_uncertainty",)),  # wrong field for risk
            ("strategy_selector", ("regime_confidence",)),  # wrong field
        ]

        results = mon.validate_batch(entries)
        assert len(results) == 7

        # First 4 permitted
        assert all(r.permitted for r in results[:4])

        # Last 3 violations
        assert all(not r.permitted for r in results[4:])

        # Violation details
        assert results[4].violation.caller_module == "rogue_module"
        assert results[5].violation.attempted_field == "meta_uncertainty"


# =============================================================================
# SCENARIO 7 -- STATE HISTORY & CALLBACK INTEGRATION
# =============================================================================

class TestStateHistory:
    """
    Verify state versioning, history tracking, and callback invocation
    work correctly through a multi-step mutation sequence.
    """

    def test_version_increments(self):
        ctrl = GlobalSystemStateController.get_instance()
        assert ctrl.version == 1

        ctrl.update(regime="RISK_ON", regime_confidence=0.80)
        assert ctrl.version == 2

        ctrl.update(vol_regime="SPIKE", vol_spike_flag=True)
        assert ctrl.version == 3

        ctrl.update(risk_mode="ELEVATED")
        assert ctrl.version == 4

    def test_history_tracks_changes(self):
        ctrl = GlobalSystemStateController.get_instance()
        ctrl.update(regime="RISK_ON")
        ctrl.update(regime="CRISIS")
        ctrl.update(regime="RISK_ON")

        history = ctrl.get_history(last_n=3)
        assert len(history) == 3
        assert history[0].regime == "UNKNOWN"   # initial
        assert history[1].regime == "RISK_ON"   # after first update
        assert history[2].regime == "CRISIS"    # after second update

    def test_callback_fires_on_update(self):
        ctrl = GlobalSystemStateController.get_instance()
        captured = []

        def on_change(old: GlobalState, new: GlobalState):
            captured.append((old.regime, new.regime))

        ctrl.register_callback(on_change)
        ctrl.update(regime="RISK_ON")
        ctrl.update(regime="CRISIS")

        assert len(captured) == 2
        assert captured[0] == ("UNKNOWN", "RISK_ON")
        assert captured[1] == ("RISK_ON", "CRISIS")


# =============================================================================
# SCENARIO 8 -- INTEGRITY HASH CHAIN ACROSS CYCLE
# =============================================================================

class TestHashChainAcrossCycle:
    """
    Verify hash chain integrity across a full analytical cycle.
    Append events for each phase, then verify the chain.
    """

    def test_chain_integrity_across_phases(self):
        il = IntegrityLayer()
        chain = il.init_hash_chain("CYCLE_START")

        # Phase 1: boot
        il.append_to_chain(chain, "BOOT", {"status": "ok"})

        # Phase 2: normal cycle
        il.append_to_chain(chain, "NORMAL_CYCLE", {
            "regime": "RISK_ON",
            "gates_passed": 6,
        })

        # Phase 3: stress
        il.append_to_chain(chain, "STRESS_EVENT", {
            "regime": "CRISIS",
            "ood_detected": True,
        })

        # Phase 4: recovery
        il.append_to_chain(chain, "RECOVERY", {
            "regime": "RISK_ON",
            "trust_classification": "HIGH",
        })

        assert len(chain.events) == 4

        # Full chain verification
        result = il.verify_chain(chain)
        assert result.valid is True
        assert result.broken_at is None

        # Events are linked: each references the previous hash
        for i in range(1, len(chain.events)):
            assert chain.events[i].previous_hash == chain.events[i - 1].current_hash


# =============================================================================
# SCENARIO 9 -- DETERMINISM: IDENTICAL REPLAY
# =============================================================================

class TestDeterministicReplay:
    """
    Run the exact same analytical cycle twice and verify bit-identical results.
    This is the DET-07 guarantee at integration level.
    """

    def _run_cycle(self):
        """Run one full analytical cycle, return all computed results."""
        results = {}

        # Gates
        results["gates"] = _run_all_gates(
            quality=0.85, drift=0.30, condition=80.0,
            ece=0.025, is_ood=False, var=-0.08,
        )

        # Pipeline
        results["flow"] = SystemControlFlow().execute(
            quality_score=0.85, drift_severity=0.30,
            condition_number=80.0, ece=0.025,
            is_ood=False, var=-0.08,
        )

        # Trust
        results["trust"] = TrustScoreEngine().compute(
            ece=0.025, ood_recall=0.85,
            prediction_variance=0.03, drawdown=0.06,
            uptime=0.95,
        )

        # Fragility
        results["fragility"] = StructuralFragilityIndex().compute(
            coupling_score=0.3, propagation_score=0.2,
            recovery_score=0.15, cascade_score=0.1,
        )

        # Governance
        mon = GovernanceMonitor()
        results["audit"] = mon.check_update_permission(
            "risk_engine", ("risk_mode",)
        )
        results["conf_check"] = mon.check_confidence_emitter("confidence_engine")

        # Mode
        results["mode_transition"] = ModeController().transition(
            OperationalMode.NORMAL, "high_uncertainty"
        )

        return results

    def test_bit_identical_replay(self):
        run1 = self._run_cycle()
        run2 = self._run_cycle()

        # Gates
        for name in run1["gates"]:
            assert run1["gates"][name] == run2["gates"][name], (
                f"Gate {name} not deterministic"
            )

        # Pipeline
        assert len(run1["flow"]) == len(run2["flow"])
        for s1, s2 in zip(run1["flow"], run2["flow"]):
            assert s1 == s2

        # Trust
        assert run1["trust"] == run2["trust"]

        # Fragility
        assert run1["fragility"] == run2["fragility"]

        # Governance
        assert run1["audit"] == run2["audit"]
        assert run1["conf_check"] == run2["conf_check"]

        # Mode
        assert run1["mode_transition"] == run2["mode_transition"]


# =============================================================================
# SCENARIO 10 -- CROSS-MODULE DATA FLOW CONSISTENCY
# =============================================================================

class TestCrossModuleConsistency:
    """
    Verify that metrics computed from gate results are consistent
    with control flow decisions and trust/fragility classifications.
    """

    def test_gates_match_control_flow(self):
        """If all gates pass individually, pipeline should all-CONTINUE."""
        params = dict(
            quality=0.80, drift=0.40,
            condition=500.0, ece=0.03,
            is_ood=False, var=-0.10,
        )
        gates = _run_all_gates(**params)
        all_passed = all(g.passed for g in gates.values())

        flow = SystemControlFlow().execute(
            quality_score=params["quality"],
            drift_severity=params["drift"],
            condition_number=params["condition"],
            ece=params["ece"],
            is_ood=params["is_ood"],
            var=params["var"],
        )
        all_continue = all(
            fs.signal == ControlSignal.CONTINUE for fs in flow
        )

        assert all_passed == all_continue

    def test_trust_fragility_inverse_correlation(self):
        """
        Under normal conditions: high trust, low fragility.
        Under stress: low trust, high fragility.
        """
        trust_eng = TrustScoreEngine()
        frag_eng = StructuralFragilityIndex()

        # Normal
        t_normal = trust_eng.compute(
            ece=0.01, ood_recall=0.95,
            prediction_variance=0.01, drawdown=0.02, uptime=0.99,
        )
        f_normal = frag_eng.compute(0.1, 0.05, 0.05, 0.02)

        # Stress
        t_stress = trust_eng.compute(
            ece=0.04, ood_recall=0.30,
            prediction_variance=0.08, drawdown=0.12, uptime=0.70,
        )
        f_stress = frag_eng.compute(0.8, 0.7, 0.6, 0.5)

        # Normal: high trust, low fragility
        assert t_normal.trust_score > t_stress.trust_score
        assert f_normal.fragility_index < f_stress.fragility_index

        # Classifications should reflect this
        assert t_normal.classification == "HIGH"
        assert f_normal.classification == "LOW"
        assert f_stress.classification in ("HIGH", "CRITICAL")

    def test_governance_enforces_permitted_callers_match(self):
        """
        Every caller in PERMITTED_CALLERS can pass governance check
        for its own fields. No caller can pass for another's fields.
        """
        mon = GovernanceMonitor()

        for caller, allowed_fields in PERMITTED_CALLERS.items():
            if "ALL" in allowed_fields:
                continue

            # Permitted: own fields
            for field in sorted(allowed_fields):
                audit = mon.check_update_permission(caller, (field,))
                assert audit.permitted is True, (
                    f"{caller} should be permitted for {field}"
                )

            # Forbidden: a field not in own set
            other_fields = {"mode", "regime", "meta_uncertainty"} - allowed_fields
            if other_fields:
                forbidden_field = sorted(other_fields)[0]
                audit = mon.check_update_permission(caller, (forbidden_field,))
                assert audit.permitted is False, (
                    f"{caller} should NOT be permitted for {forbidden_field}"
                )
