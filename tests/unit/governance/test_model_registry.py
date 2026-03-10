# =============================================================================
# tests/unit/governance/test_model_registry.py — S34 Model Governance Framework
#
# Comprehensive tests for:
#   Part 1: FullModelRegistry, ModelVersion, ValidationReport, Enums
#   Part 2: BacktestGovernance, BacktestConfig
#   Part 3: SR11_7_Compliance
#   Part 4: ModelRegistry (simplified), ModelEntry
# =============================================================================

import json
import pytest
from datetime import datetime, timedelta
from pathlib import Path

from jarvis.governance.model_registry import (
    BacktestConfig,
    BacktestGovernance,
    FullModelRegistry,
    ModelEntry,
    ModelRegistry,
    ModelRiskTier,
    ModelStatus,
    ModelVersion,
    SR11_7_Compliance,
    ValidationReport,
)


# ---------------------------------------------------------------------------
# HELPERS
# ---------------------------------------------------------------------------

def _make_validation_report(
    model_id: str = "m1",
    version: str = "1.0",
    validator: str = "validator_a",
    recommendation: str = "APPROVE",
    all_gates_passed: bool = True,
    failed_gates: list = None,
) -> ValidationReport:
    return ValidationReport(
        model_id=model_id,
        version=version,
        validator_name=validator,
        validation_date=datetime.utcnow(),
        conceptual_soundness=True,
        data_quality_verified=True,
        implementation_correct=True,
        performance_adequate=True,
        sensitivity_analyzed=True,
        ece_score=0.03,
        ood_recall=0.95,
        backtest_sharpe=1.5,
        max_drawdown=0.10,
        all_gates_passed=all_gates_passed,
        failed_gates=failed_gates or [],
        recommendation=recommendation,
        conditions=[],
        notes="Test report",
    )


def _full_registry_with_model(tmp_path, model_id="m1", version="1.0"):
    """Create a FullModelRegistry with a registered model."""
    path = str(tmp_path / "registry.json")
    reg = FullModelRegistry(path)
    reg.register_model(
        model_id=model_id,
        version=version,
        code_hash="abc123",
        config_hash="def456",
        created_by="developer_a",
        risk_tier=ModelRiskTier.TIER_1_HIGH,
    )
    return reg


def _submit_and_validate(reg, model_id="m1", version="1.0"):
    """Submit for validation and add a passing report."""
    reg.submit_for_validation(
        model_id=model_id,
        version=version,
        validation_metrics={"ece": 0.03, "ood_recall": 0.95, "calibration_error": 0.02},
        backtest_metrics={"sharpe_ratio": 1.5, "max_drawdown": 0.10, "win_rate": 0.55},
        oos_metrics={"oos_sharpe": 1.2, "oos_return": 0.08, "oos_volatility": 0.12},
    )
    report = _make_validation_report(model_id, version)
    reg.add_validation_report(model_id, version, "validator_a", report)


# =============================================================================
# PART 1: ENUMS
# =============================================================================

class TestModelStatus:
    def test_all_values(self):
        assert ModelStatus.DEVELOPMENT.value == "development"
        assert ModelStatus.VALIDATION.value == "validation"
        assert ModelStatus.APPROVED.value == "approved"
        assert ModelStatus.DEPLOYED.value == "deployed"
        assert ModelStatus.DEPRECATED.value == "deprecated"
        assert ModelStatus.SUSPENDED.value == "suspended"

    def test_count(self):
        assert len(ModelStatus) == 6


class TestModelRiskTier:
    def test_all_values(self):
        assert ModelRiskTier.TIER_1_HIGH.value == "tier_1_high"
        assert ModelRiskTier.TIER_2_MODERATE.value == "tier_2_moderate"
        assert ModelRiskTier.TIER_3_LOW.value == "tier_3_low"

    def test_count(self):
        assert len(ModelRiskTier) == 3


# =============================================================================
# PART 1: MODELVERSION DATACLASS
# =============================================================================

class TestModelVersion:
    def test_post_init_defaults(self):
        mv = ModelVersion(
            model_id="m1", version="1.0",
            created_at=datetime.utcnow(), created_by="dev",
            status=ModelStatus.DEVELOPMENT,
            risk_tier=ModelRiskTier.TIER_1_HIGH,
            code_hash="abc", config_hash="def", dependency_hash="ghi",
            validation_metrics={}, backtest_metrics={}, oos_metrics={},
        )
        assert mv.change_log == []
        assert mv.assumptions == []
        assert mv.limitations == []

    def test_optional_fields_none(self):
        mv = ModelVersion(
            model_id="m1", version="1.0",
            created_at=datetime.utcnow(), created_by="dev",
            status=ModelStatus.DEVELOPMENT,
            risk_tier=ModelRiskTier.TIER_1_HIGH,
            code_hash="abc", config_hash="def", dependency_hash="ghi",
            validation_metrics={}, backtest_metrics={}, oos_metrics={},
        )
        assert mv.validator_name is None
        assert mv.validation_date is None
        assert mv.approval_date is None
        assert mv.approved_by is None


# =============================================================================
# PART 1: VALIDATION REPORT DATACLASS
# =============================================================================

class TestValidationReport:
    def test_fields(self):
        r = _make_validation_report()
        assert r.model_id == "m1"
        assert r.recommendation == "APPROVE"
        assert r.all_gates_passed is True
        assert r.failed_gates == []


# =============================================================================
# PART 1: FULL MODEL REGISTRY
# =============================================================================

class TestFullModelRegistryRegister:
    def test_register_model(self, tmp_path):
        reg = _full_registry_with_model(tmp_path)
        v = reg._get_version("m1", "1.0")
        assert v.model_id == "m1"
        assert v.status == ModelStatus.DEVELOPMENT
        assert v.risk_tier == ModelRiskTier.TIER_1_HIGH

    def test_register_duplicate_code_hash_raises(self, tmp_path):
        reg = _full_registry_with_model(tmp_path)
        with pytest.raises(ValueError, match="identischem Code-Hash"):
            reg.register_model(
                "m1", "2.0", "abc123", "xyz", "dev_b",
                ModelRiskTier.TIER_1_HIGH,
            )

    def test_register_different_hash_ok(self, tmp_path):
        reg = _full_registry_with_model(tmp_path)
        v2 = reg.register_model(
            "m1", "2.0", "different_hash", "xyz", "dev_b",
            ModelRiskTier.TIER_2_MODERATE,
        )
        assert v2.version == "2.0"

    def test_dependency_hash_computed(self, tmp_path):
        reg = _full_registry_with_model(tmp_path)
        v = reg._get_version("m1", "1.0")
        assert len(v.dependency_hash) == 16

    def test_unknown_model_raises(self, tmp_path):
        path = str(tmp_path / "reg.json")
        reg = FullModelRegistry(path)
        with pytest.raises(KeyError, match="nicht in Registry"):
            reg._get_version("nonexistent", "1.0")

    def test_unknown_version_raises(self, tmp_path):
        reg = _full_registry_with_model(tmp_path)
        with pytest.raises(KeyError, match="nicht gefunden"):
            reg._get_version("m1", "99.0")


class TestFullModelRegistryValidation:
    def test_submit_for_validation(self, tmp_path):
        reg = _full_registry_with_model(tmp_path)
        reg.submit_for_validation(
            "m1", "1.0",
            {"ece": 0.03, "ood_recall": 0.95, "calibration_error": 0.02},
            {"sharpe_ratio": 1.5, "max_drawdown": 0.10, "win_rate": 0.55},
            {"oos_sharpe": 1.2, "oos_return": 0.08, "oos_volatility": 0.12},
        )
        v = reg._get_version("m1", "1.0")
        assert v.status == ModelStatus.VALIDATION
        assert v.validation_metrics["ece"] == 0.03

    def test_submit_missing_metric_raises(self, tmp_path):
        reg = _full_registry_with_model(tmp_path)
        with pytest.raises(ValueError, match="Missing validation metric"):
            reg.submit_for_validation(
                "m1", "1.0",
                {"ece": 0.03},  # missing ood_recall, calibration_error
                {}, {},
            )

    def test_add_validation_report(self, tmp_path):
        reg = _full_registry_with_model(tmp_path)
        report = _make_validation_report()
        reg.add_validation_report("m1", "1.0", "validator_a", report)
        v = reg._get_version("m1", "1.0")
        assert v.validator_name == "validator_a"
        assert v.validation_date is not None

    def test_validator_same_as_developer_raises(self, tmp_path):
        reg = _full_registry_with_model(tmp_path)
        report = _make_validation_report(validator="developer_a")
        with pytest.raises(ValueError, match="Validator darf nicht identisch"):
            reg.add_validation_report("m1", "1.0", "developer_a", report)


class TestFullModelRegistryApproval:
    def test_approve_model(self, tmp_path):
        reg = _full_registry_with_model(tmp_path)
        _submit_and_validate(reg)
        reg.approve_model("m1", "1.0", "approver_x")
        v = reg._get_version("m1", "1.0")
        assert v.status == ModelStatus.APPROVED
        assert v.approved_by == "approver_x"

    def test_approve_without_validation_raises(self, tmp_path):
        reg = _full_registry_with_model(tmp_path)
        with pytest.raises(ValueError, match="keine Validation"):
            reg.approve_model("m1", "1.0", "approver_x")

    def test_approve_reject_recommendation_raises(self, tmp_path):
        reg = _full_registry_with_model(tmp_path)
        reg.submit_for_validation(
            "m1", "1.0",
            {"ece": 0.03, "ood_recall": 0.95, "calibration_error": 0.02},
            {}, {},
        )
        report = _make_validation_report(recommendation="REJECT")
        reg.add_validation_report("m1", "1.0", "validator_a", report)
        with pytest.raises(ValueError, match="REJECT"):
            reg.approve_model("m1", "1.0", "approver_x")

    def test_approve_failed_gates_raises(self, tmp_path):
        reg = _full_registry_with_model(tmp_path)
        reg.submit_for_validation(
            "m1", "1.0",
            {"ece": 0.03, "ood_recall": 0.95, "calibration_error": 0.02},
            {}, {},
        )
        report = _make_validation_report(
            all_gates_passed=False, failed_gates=["ece_gate"]
        )
        reg.add_validation_report("m1", "1.0", "validator_a", report)
        with pytest.raises(ValueError, match="Governance Gates"):
            reg.approve_model("m1", "1.0", "approver_x")

    def test_approve_with_conditions(self, tmp_path):
        reg = _full_registry_with_model(tmp_path)
        _submit_and_validate(reg)
        reg.approve_model("m1", "1.0", "approver_x", conditions=["Monitor ECE weekly"])
        v = reg._get_version("m1", "1.0")
        assert any("conditions" in log for log in v.change_log)


class TestFullModelRegistryDeploy:
    def test_deploy_model(self, tmp_path):
        reg = _full_registry_with_model(tmp_path)
        _submit_and_validate(reg)
        reg.approve_model("m1", "1.0", "approver_x")
        reg.deploy_model("m1", "1.0")
        v = reg._get_version("m1", "1.0")
        assert v.status == ModelStatus.DEPLOYED

    def test_deploy_not_approved_raises(self, tmp_path):
        reg = _full_registry_with_model(tmp_path)
        with pytest.raises(ValueError, match="nicht approved"):
            reg.deploy_model("m1", "1.0")

    def test_deploy_deprecates_old_version(self, tmp_path):
        path = str(tmp_path / "reg.json")
        reg = FullModelRegistry(path)

        # Register and deploy v1
        reg.register_model("m1", "1.0", "h1", "c1", "dev_a", ModelRiskTier.TIER_1_HIGH)
        _submit_and_validate(reg, "m1", "1.0")
        reg.approve_model("m1", "1.0", "approver")
        reg.deploy_model("m1", "1.0")

        # Register and deploy v2
        reg.register_model("m1", "2.0", "h2", "c2", "dev_a", ModelRiskTier.TIER_1_HIGH)
        reg.submit_for_validation(
            "m1", "2.0",
            {"ece": 0.02, "ood_recall": 0.96, "calibration_error": 0.01},
            {}, {},
        )
        report_v2 = _make_validation_report("m1", "2.0")
        reg.add_validation_report("m1", "2.0", "validator_a", report_v2)
        reg.approve_model("m1", "2.0", "approver")
        reg.deploy_model("m1", "2.0")

        v1 = reg._get_version("m1", "1.0")
        v2 = reg._get_version("m1", "2.0")
        assert v1.status == ModelStatus.DEPRECATED
        assert v2.status == ModelStatus.DEPLOYED

    def test_get_deployed_version(self, tmp_path):
        reg = _full_registry_with_model(tmp_path)
        _submit_and_validate(reg)
        reg.approve_model("m1", "1.0", "approver")
        reg.deploy_model("m1", "1.0")
        deployed = reg.get_deployed_version("m1")
        assert deployed is not None
        assert deployed.version == "1.0"

    def test_get_deployed_none_when_not_deployed(self, tmp_path):
        reg = _full_registry_with_model(tmp_path)
        assert reg.get_deployed_version("m1") is None

    def test_get_deployed_unknown_model(self, tmp_path):
        path = str(tmp_path / "reg.json")
        reg = FullModelRegistry(path)
        assert reg.get_deployed_version("nonexistent") is None


class TestFullModelRegistryRollback:
    def test_rollback(self, tmp_path):
        path = str(tmp_path / "reg.json")
        reg = FullModelRegistry(path)

        # Deploy v1
        reg.register_model("m1", "1.0", "h1", "c1", "dev_a", ModelRiskTier.TIER_1_HIGH)
        _submit_and_validate(reg, "m1", "1.0")
        reg.approve_model("m1", "1.0", "approver")
        reg.deploy_model("m1", "1.0")

        # Deploy v2
        reg.register_model("m1", "2.0", "h2", "c2", "dev_a", ModelRiskTier.TIER_1_HIGH)
        reg.submit_for_validation(
            "m1", "2.0",
            {"ece": 0.02, "ood_recall": 0.96, "calibration_error": 0.01},
            {}, {},
        )
        r2 = _make_validation_report("m1", "2.0")
        reg.add_validation_report("m1", "2.0", "validator_a", r2)
        reg.approve_model("m1", "2.0", "approver")
        reg.deploy_model("m1", "2.0")

        # Rollback from v2 to v1 — v1 is DEPRECATED, need APPROVED
        # Re-approve v1 for rollback target
        v1 = reg._get_version("m1", "1.0")
        v1.status = ModelStatus.APPROVED

        reg.rollback_model("m1", "2.0", "1.0", "performance regression")
        v2 = reg._get_version("m1", "2.0")
        v1_after = reg._get_version("m1", "1.0")
        assert v2.status == ModelStatus.SUSPENDED
        assert v1_after.status == ModelStatus.DEPLOYED

    def test_rollback_wrong_target_status_raises(self, tmp_path):
        reg = _full_registry_with_model(tmp_path)
        reg.register_model("m1", "2.0", "h2", "c2", "dev_a", ModelRiskTier.TIER_1_HIGH)
        with pytest.raises(ValueError, match="DEPLOYED oder APPROVED"):
            reg.rollback_model("m1", "2.0", "1.0", "reason")


class TestFullModelRegistrySaveLoad:
    def test_save_creates_file(self, tmp_path):
        path = str(tmp_path / "reg.json")
        reg = FullModelRegistry(path)
        reg.register_model("m1", "1.0", "h1", "c1", "dev", ModelRiskTier.TIER_1_HIGH)
        assert Path(path).exists()

    def test_save_valid_json(self, tmp_path):
        path = str(tmp_path / "reg.json")
        reg = FullModelRegistry(path)
        reg.register_model("m1", "1.0", "h1", "c1", "dev", ModelRiskTier.TIER_1_HIGH)
        data = json.loads(Path(path).read_text())
        assert "models" in data
        assert "validations" in data

    def test_load_nonexistent_no_error(self, tmp_path):
        path = str(tmp_path / "nonexistent.json")
        reg = FullModelRegistry(path)
        assert len(reg.models) == 0


# =============================================================================
# PART 2: BACKTEST GOVERNANCE
# =============================================================================

class TestBacktestConfig:
    def test_fields(self):
        cfg = BacktestConfig(
            start_date=datetime(2020, 1, 1),
            end_date=datetime(2022, 1, 1),
            initial_capital=100000.0,
            transaction_costs=0.001,
            slippage_model="fixed",
            random_seed=42,
            config_hash="abc123",
        )
        assert cfg.initial_capital == 100000.0
        assert cfg.approved_by is None


class TestBacktestGovernanceConstants:
    def test_train_window_min(self):
        assert BacktestGovernance.TRAIN_WINDOW_MIN == 365

    def test_test_window(self):
        assert BacktestGovernance.TEST_WINDOW == 90

    def test_min_trades(self):
        assert BacktestGovernance.MIN_TRADES == 30


class TestBacktestGovernanceValidation:
    def test_valid_config(self):
        gov = BacktestGovernance()
        cfg = BacktestConfig(
            start_date=datetime(2020, 1, 1),
            end_date=datetime(2022, 1, 1),
            initial_capital=100000.0,
            transaction_costs=0.001,
            slippage_model="fixed",
            random_seed=42,
            config_hash="abc",
        )
        assert gov.validate_backtest_config(cfg) is True

    def test_train_window_too_short_raises(self):
        gov = BacktestGovernance()
        cfg = BacktestConfig(
            start_date=datetime(2022, 1, 1),
            end_date=datetime(2022, 6, 1),  # ~150 days < 365
            initial_capital=100000.0,
            transaction_costs=0.001,
            slippage_model="fixed",
            random_seed=42,
            config_hash="abc",
        )
        with pytest.raises(ValueError, match="Train window"):
            gov.validate_backtest_config(cfg)

    def test_transaction_costs_too_low_raises(self):
        gov = BacktestGovernance()
        cfg = BacktestConfig(
            start_date=datetime(2020, 1, 1),
            end_date=datetime(2022, 1, 1),
            initial_capital=100000.0,
            transaction_costs=0.00001,  # < 1 bps
            slippage_model="fixed",
            random_seed=42,
            config_hash="abc",
        )
        with pytest.raises(ValueError, match="Transaction costs"):
            gov.validate_backtest_config(cfg)

    def test_boundary_exactly_365_days(self):
        gov = BacktestGovernance()
        start = datetime(2020, 1, 1)
        end = start + timedelta(days=365)
        cfg = BacktestConfig(
            start_date=start, end_date=end,
            initial_capital=100000.0,
            transaction_costs=0.0001,  # exactly 1 bps
            slippage_model="fixed",
            random_seed=42,
            config_hash="abc",
        )
        assert gov.validate_backtest_config(cfg) is True

    def test_boundary_364_days_raises(self):
        gov = BacktestGovernance()
        start = datetime(2020, 1, 1)
        end = start + timedelta(days=364)
        cfg = BacktestConfig(
            start_date=start, end_date=end,
            initial_capital=100000.0,
            transaction_costs=0.001,
            slippage_model="fixed",
            random_seed=42,
            config_hash="abc",
        )
        with pytest.raises(ValueError, match="Train window"):
            gov.validate_backtest_config(cfg)


class TestBacktestGovernanceWalkForward:
    def test_walk_forward_splits(self):
        gov = BacktestGovernance()
        splits = gov.enforce_walk_forward(total_data_days=1000)
        assert len(splits) > 0
        for train_start, train_end, test_start, test_end in splits:
            assert train_end - train_start == 365
            assert test_end - test_start == 90
            assert test_start == train_end

    def test_walk_forward_slides_by_test_window(self):
        gov = BacktestGovernance()
        splits = gov.enforce_walk_forward(total_data_days=1000)
        for i in range(1, len(splits)):
            assert splits[i][0] - splits[i - 1][0] == 90

    def test_walk_forward_too_short(self):
        gov = BacktestGovernance()
        splits = gov.enforce_walk_forward(total_data_days=400)
        # 400 < 365 + 90 = 455
        assert splits == []

    def test_walk_forward_exact_boundary(self):
        gov = BacktestGovernance()
        splits = gov.enforce_walk_forward(total_data_days=455)
        assert len(splits) == 1
        assert splits[0] == (0, 365, 365, 455)

    def test_walk_forward_multiple_splits(self):
        gov = BacktestGovernance()
        # 365 + 90*n <= 2000
        splits = gov.enforce_walk_forward(total_data_days=2000)
        assert len(splits) >= 2


# =============================================================================
# PART 3: SR 11-7 COMPLIANCE
# =============================================================================

class TestSR11_7_Compliance:
    def test_required_components_count(self):
        assert len(SR11_7_Compliance.REQUIRED_COMPONENTS) == 10

    def test_no_deployed_model_all_false(self, tmp_path):
        path = str(tmp_path / "reg.json")
        reg = FullModelRegistry(path)
        comp = SR11_7_Compliance()
        result = comp.check_compliance("m1", reg)
        assert all(v is False for v in result.values())

    def test_deployed_model_partial_compliance(self, tmp_path):
        path = str(tmp_path / "reg.json")
        reg = FullModelRegistry(path)
        reg.register_model("m1", "1.0", "h1", "c1", "dev_a", ModelRiskTier.TIER_1_HIGH)
        _submit_and_validate(reg, "m1", "1.0")
        reg.approve_model("m1", "1.0", "approver_x")
        reg.deploy_model("m1", "1.0")

        comp = SR11_7_Compliance()
        result = comp.check_compliance("m1", reg)

        # model_validation: validator != developer → True
        assert result["model_validation"] is True
        # governance_and_controls: deployed + approved_by → True
        assert result["governance_and_controls"] is True
        # model_inventory: always True
        assert result["model_inventory"] is True
        # model_risk_rating: risk_tier exists → True
        assert result["model_risk_rating"] is True
        # ongoing_monitoring: always True
        assert result["ongoing_monitoring"] is True

    def test_documentation_compliance(self, tmp_path):
        path = str(tmp_path / "reg.json")
        reg = FullModelRegistry(path)
        reg.register_model("m1", "1.0", "h1", "c1", "dev_a", ModelRiskTier.TIER_1_HIGH)
        v = reg._get_version("m1", "1.0")
        v.assumptions = ["Linear relationship"]
        v.limitations = ["Only equity markets"]
        v.change_log = ["Initial version"]
        _submit_and_validate(reg, "m1", "1.0")
        reg.approve_model("m1", "1.0", "approver_x")
        reg.deploy_model("m1", "1.0")

        comp = SR11_7_Compliance()
        result = comp.check_compliance("m1", reg)
        assert result["model_development_documentation"] is True

    def test_missing_documentation_false(self, tmp_path):
        path = str(tmp_path / "reg.json")
        reg = FullModelRegistry(path)
        reg.register_model("m1", "1.0", "h1", "c1", "dev_a", ModelRiskTier.TIER_1_HIGH)
        _submit_and_validate(reg, "m1", "1.0")
        reg.approve_model("m1", "1.0", "approver_x")
        reg.deploy_model("m1", "1.0")

        comp = SR11_7_Compliance()
        result = comp.check_compliance("m1", reg)
        # change_log has "Deployed at..." but assumptions and limitations are empty
        assert result["model_development_documentation"] is False


# =============================================================================
# PART 4: SIMPLIFIED MODEL REGISTRY — CONSTANTS
# =============================================================================

class TestModelRegistryConstants:
    def test_required_ece(self):
        assert ModelRegistry.REQUIRED_ECE == 0.05

    def test_required_ood_recall(self):
        assert ModelRegistry.REQUIRED_OOD_RECALL == 0.90

    def test_required_stress_pass(self):
        assert ModelRegistry.REQUIRED_STRESS_PASS is True


# =============================================================================
# PART 4: MODEL ENTRY DATACLASS
# =============================================================================

class TestModelEntry:
    def test_fields(self):
        entry = ModelEntry(
            model_id="m1", version="1.0", created_at="2026-01-01",
            deployed_at=None, status="CANDIDATE", ece=1.0, ood_recall=0.0,
            stress_passed=False, monte_carlo_var95=-1.0,
            model_hash="abc", is_active=False, notes="",
        )
        assert entry.model_id == "m1"
        assert entry.status == "CANDIDATE"
        assert entry.is_active is False


# =============================================================================
# PART 4: REGISTER CANDIDATE
# =============================================================================

class TestRegisterCandidate:
    def test_register_basic(self):
        reg = ModelRegistry()
        entry = reg.register_candidate("m1", "1.0", {"lr": 0.01})
        assert entry.model_id == "m1"
        assert entry.version == "1.0"
        assert entry.status == "CANDIDATE"
        assert entry.is_active is False
        assert entry.deployed_at is None

    def test_register_defaults(self):
        reg = ModelRegistry()
        entry = reg.register_candidate("m1", "1.0", {})
        assert entry.ece == 1.0
        assert entry.ood_recall == 0.0
        assert entry.stress_passed is False
        assert entry.monte_carlo_var95 == -1.0

    def test_register_hash_deterministic(self):
        reg1 = ModelRegistry()
        reg2 = ModelRegistry()
        e1 = reg1.register_candidate("m1", "1.0", {"lr": 0.01, "layers": 3})
        e2 = reg2.register_candidate("m1", "1.0", {"lr": 0.01, "layers": 3})
        assert e1.model_hash == e2.model_hash

    def test_register_different_params_different_hash(self):
        reg = ModelRegistry()
        e1 = reg.register_candidate("m1", "1.0", {"lr": 0.01})
        e2 = reg.register_candidate("m2", "1.0", {"lr": 0.02})
        assert e1.model_hash != e2.model_hash

    def test_register_hash_length(self):
        reg = ModelRegistry()
        entry = reg.register_candidate("m1", "1.0", {"x": 1})
        assert len(entry.model_hash) == 16


# =============================================================================
# PART 4: CERTIFY
# =============================================================================

class TestCertify:
    def test_certify_passes(self):
        reg = ModelRegistry()
        reg.register_candidate("m1", "1.0", {})
        entry = reg.certify("m1", ece=0.03, ood_recall=0.95,
                             stress_passed=True, monte_carlo_var95=-0.05)
        assert entry.status == "SHADOW"
        assert entry.ece == 0.03
        assert entry.ood_recall == 0.95
        assert entry.stress_passed is True

    def test_certify_ece_too_high_raises(self):
        reg = ModelRegistry()
        reg.register_candidate("m1", "1.0", {})
        with pytest.raises(RuntimeError, match="MODEL_CERTIFICATION_FAILED"):
            reg.certify("m1", ece=0.08, ood_recall=0.95,
                         stress_passed=True, monte_carlo_var95=-0.05)

    def test_certify_ece_failure_sets_failed(self):
        reg = ModelRegistry()
        reg.register_candidate("m1", "1.0", {})
        try:
            reg.certify("m1", ece=0.08, ood_recall=0.95,
                         stress_passed=True, monte_carlo_var95=-0.05)
        except RuntimeError:
            pass
        assert reg._models["m1"].status == "FAILED"

    def test_certify_ood_recall_too_low_raises(self):
        reg = ModelRegistry()
        reg.register_candidate("m1", "1.0", {})
        with pytest.raises(RuntimeError, match="OOD_Recall"):
            reg.certify("m1", ece=0.03, ood_recall=0.80,
                         stress_passed=True, monte_carlo_var95=-0.05)

    def test_certify_stress_failed_raises(self):
        reg = ModelRegistry()
        reg.register_candidate("m1", "1.0", {})
        with pytest.raises(RuntimeError, match="Stress-Test"):
            reg.certify("m1", ece=0.03, ood_recall=0.95,
                         stress_passed=False, monte_carlo_var95=-0.05)

    def test_certify_multiple_failures(self):
        reg = ModelRegistry()
        reg.register_candidate("m1", "1.0", {})
        with pytest.raises(RuntimeError) as exc_info:
            reg.certify("m1", ece=0.08, ood_recall=0.80,
                         stress_passed=False, monte_carlo_var95=-0.05)
        msg = str(exc_info.value)
        assert "ECE" in msg
        assert "OOD_Recall" in msg
        assert "Stress-Test" in msg

    def test_certify_unknown_model_raises(self):
        reg = ModelRegistry()
        with pytest.raises(KeyError, match="nicht in Registry"):
            reg.certify("nonexistent", ece=0.03, ood_recall=0.95,
                         stress_passed=True, monte_carlo_var95=-0.05)

    def test_certify_boundary_ece_exactly_005(self):
        reg = ModelRegistry()
        reg.register_candidate("m1", "1.0", {})
        entry = reg.certify("m1", ece=0.05, ood_recall=0.95,
                             stress_passed=True, monte_carlo_var95=-0.05)
        assert entry.status == "SHADOW"

    def test_certify_boundary_ood_exactly_090(self):
        reg = ModelRegistry()
        reg.register_candidate("m1", "1.0", {})
        entry = reg.certify("m1", ece=0.03, ood_recall=0.90,
                             stress_passed=True, monte_carlo_var95=-0.05)
        assert entry.status == "SHADOW"

    def test_certify_notes_stored(self):
        reg = ModelRegistry()
        reg.register_candidate("m1", "1.0", {})
        entry = reg.certify("m1", ece=0.03, ood_recall=0.95,
                             stress_passed=True, monte_carlo_var95=-0.05,
                             notes="Good performance")
        assert entry.notes == "Good performance"


# =============================================================================
# PART 4: PROMOTE TO ACTIVE
# =============================================================================

class TestPromoteToActive:
    def test_promote_shadow_to_active(self):
        reg = ModelRegistry()
        reg.register_candidate("m1", "1.0", {})
        reg.certify("m1", ece=0.03, ood_recall=0.95,
                      stress_passed=True, monte_carlo_var95=-0.05)
        entry = reg.promote_to_active("m1")
        assert entry.status == "ACTIVE"
        assert entry.is_active is True
        assert entry.deployed_at is not None

    def test_promote_non_shadow_raises(self):
        reg = ModelRegistry()
        reg.register_candidate("m1", "1.0", {})
        with pytest.raises(RuntimeError, match="SHADOW"):
            reg.promote_to_active("m1")

    def test_promote_archives_old_active(self):
        reg = ModelRegistry()
        reg.register_candidate("m1", "1.0", {})
        reg.certify("m1", ece=0.03, ood_recall=0.95,
                      stress_passed=True, monte_carlo_var95=-0.05)
        reg.promote_to_active("m1")

        reg.register_candidate("m2", "1.0", {"new": True})
        reg.certify("m2", ece=0.02, ood_recall=0.96,
                      stress_passed=True, monte_carlo_var95=-0.03)
        reg.promote_to_active("m2")

        assert reg._models["m1"].status == "ARCHIVED"
        assert reg._models["m1"].is_active is False
        assert reg._models["m2"].status == "ACTIVE"
        assert reg._models["m2"].is_active is True

    def test_promote_unknown_raises(self):
        reg = ModelRegistry()
        with pytest.raises(KeyError, match="nicht in Registry"):
            reg.promote_to_active("nonexistent")


# =============================================================================
# PART 4: ROLLBACK
# =============================================================================

class TestRollback:
    def test_rollback_to_archived(self):
        reg = ModelRegistry()
        reg.register_candidate("m1", "1.0", {})
        reg.certify("m1", ece=0.03, ood_recall=0.95,
                      stress_passed=True, monte_carlo_var95=-0.05)
        reg.promote_to_active("m1")

        reg.register_candidate("m2", "1.0", {"new": True})
        reg.certify("m2", ece=0.02, ood_recall=0.96,
                      stress_passed=True, monte_carlo_var95=-0.03)
        reg.promote_to_active("m2")

        # m1 is now ARCHIVED, m2 is ACTIVE
        result = reg.rollback()
        assert result is not None
        assert result.model_id == "m1"
        assert result.status == "ACTIVE"
        assert reg._models["m2"].status == "ARCHIVED"

    def test_rollback_no_archived_returns_none(self):
        reg = ModelRegistry()
        reg.register_candidate("m1", "1.0", {})
        reg.certify("m1", ece=0.03, ood_recall=0.95,
                      stress_passed=True, monte_carlo_var95=-0.05)
        reg.promote_to_active("m1")
        result = reg.rollback()
        assert result is None

    def test_rollback_only_stress_passed(self):
        reg = ModelRegistry()
        reg.register_candidate("m1", "1.0", {})
        reg.certify("m1", ece=0.03, ood_recall=0.95,
                      stress_passed=True, monte_carlo_var95=-0.05)
        reg.promote_to_active("m1")

        reg.register_candidate("m2", "1.0", {"x": 1})
        reg.certify("m2", ece=0.02, ood_recall=0.96,
                      stress_passed=True, monte_carlo_var95=-0.03)
        reg.promote_to_active("m2")

        # Manually set m1 stress_passed=False
        reg._models["m1"].stress_passed = False
        result = reg.rollback()
        assert result is None  # No valid archived model


# =============================================================================
# PART 4: A/B COMPARE
# =============================================================================

class TestABCompare:
    def test_ab_compare_basic(self):
        reg = ModelRegistry()
        reg.register_candidate("m1", "1.0", {})
        reg.certify("m1", ece=0.04, ood_recall=0.92,
                      stress_passed=True, monte_carlo_var95=-0.05)
        reg.register_candidate("m2", "1.0", {"x": 1})
        reg.certify("m2", ece=0.02, ood_recall=0.96,
                      stress_passed=True, monte_carlo_var95=-0.03)

        result = reg.ab_compare("m1", "m2")
        assert result["winner"] == "m2"  # Lower ECE
        assert result["ece_diff"] == pytest.approx(0.02)
        assert result["model_a"]["ece"] == 0.04
        assert result["model_b"]["ece"] == 0.02

    def test_ab_compare_unknown_raises(self):
        reg = ModelRegistry()
        reg.register_candidate("m1", "1.0", {})
        with pytest.raises(KeyError, match="nicht in Registry"):
            reg.ab_compare("m1", "nonexistent")

    def test_ab_compare_equal_ece(self):
        reg = ModelRegistry()
        reg.register_candidate("m1", "1.0", {})
        reg.certify("m1", ece=0.03, ood_recall=0.95,
                      stress_passed=True, monte_carlo_var95=-0.05)
        reg.register_candidate("m2", "1.0", {"x": 1})
        reg.certify("m2", ece=0.03, ood_recall=0.93,
                      stress_passed=True, monte_carlo_var95=-0.04)

        result = reg.ab_compare("m1", "m2")
        assert result["ece_diff"] == pytest.approx(0.0)


# =============================================================================
# GOVERNANCE FLOW — NO SOFT WARNINGS
# =============================================================================

class TestGovernanceHardErrors:
    """Verify: Hard RuntimeError on gate failure, never soft warnings."""

    def test_certification_failure_is_runtime_error(self):
        reg = ModelRegistry()
        reg.register_candidate("m1", "1.0", {})
        with pytest.raises(RuntimeError):
            reg.certify("m1", ece=0.10, ood_recall=0.50,
                         stress_passed=False, monte_carlo_var95=-0.05)

    def test_deployment_without_approval_is_value_error(self, tmp_path):
        reg = _full_registry_with_model(tmp_path)
        with pytest.raises(ValueError, match="VERBOTEN"):
            reg.deploy_model("m1", "1.0")


# =============================================================================
# STATUS FLOW
# =============================================================================

class TestStatusFlow:
    """Verify: DEVELOPMENT → VALIDATION → APPROVED → DEPLOYED."""

    def test_full_lifecycle(self, tmp_path):
        path = str(tmp_path / "reg.json")
        reg = FullModelRegistry(path)
        reg.register_model("m1", "1.0", "h1", "c1", "dev_a", ModelRiskTier.TIER_1_HIGH)

        v = reg._get_version("m1", "1.0")
        assert v.status == ModelStatus.DEVELOPMENT

        reg.submit_for_validation(
            "m1", "1.0",
            {"ece": 0.03, "ood_recall": 0.95, "calibration_error": 0.02},
            {"sharpe_ratio": 1.5, "max_drawdown": 0.10, "win_rate": 0.55},
            {"oos_sharpe": 1.2, "oos_return": 0.08, "oos_volatility": 0.12},
        )
        assert v.status == ModelStatus.VALIDATION

        report = _make_validation_report()
        reg.add_validation_report("m1", "1.0", "validator_a", report)

        reg.approve_model("m1", "1.0", "approver_x")
        assert v.status == ModelStatus.APPROVED

        reg.deploy_model("m1", "1.0")
        assert v.status == ModelStatus.DEPLOYED

    def test_simplified_lifecycle(self):
        """CANDIDATE → SHADOW → ACTIVE."""
        reg = ModelRegistry()
        entry = reg.register_candidate("m1", "1.0", {})
        assert entry.status == "CANDIDATE"

        entry = reg.certify("m1", ece=0.03, ood_recall=0.95,
                             stress_passed=True, monte_carlo_var95=-0.05)
        assert entry.status == "SHADOW"

        entry = reg.promote_to_active("m1")
        assert entry.status == "ACTIVE"


# =============================================================================
# PACKAGE IMPORT
# =============================================================================

class TestPackageImport:
    def test_import_all(self):
        from jarvis.governance import (
            BacktestConfig,
            BacktestGovernance,
            FullModelRegistry,
            ModelEntry,
            ModelRegistry,
            ModelRiskTier,
            ModelStatus,
            ModelVersion,
            SR11_7_Compliance,
            ValidationReport,
        )
        assert ModelRegistry is not None
        assert FullModelRegistry is not None
        assert SR11_7_Compliance is not None
        assert BacktestGovernance is not None
