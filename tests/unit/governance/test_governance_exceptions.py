# tests/unit/governance/test_governance_exceptions.py
# Coverage target: jarvis/governance/exceptions.py -> 95%+
# Missing lines: 23-31

import pytest

from jarvis.governance.exceptions import GovernanceViolationError
from jarvis.governance.policy_validator import validate_pipeline_config
from jarvis.core.regime import GlobalRegimeState


class TestGovernanceViolationError:
    def test_construction_with_violations(self):
        result = validate_pipeline_config(
            meta_uncertainty=2.0,  # GOV-01 violation
            initial_capital=100000.0,
            window=20,
            step=1,
            regime=GlobalRegimeState.RISK_ON,
        )
        assert not result.is_compliant
        err = GovernanceViolationError(result)
        assert err.result is result
        assert err.blocking_violations == result.blocking_violations
        msg = str(err)
        assert "Governance policy violated" in msg
        assert "blocking violation" in msg

    def test_error_message_includes_rule_ids(self):
        result = validate_pipeline_config(
            meta_uncertainty=-1.0,  # GOV-01
            initial_capital=-1.0,   # GOV-02
            window=20,
            step=1,
            regime=GlobalRegimeState.RISK_ON,
        )
        err = GovernanceViolationError(result)
        msg = str(err)
        assert "GOV-01" in msg or "GOV-02" in msg

    def test_is_exception(self):
        result = validate_pipeline_config(
            meta_uncertainty=5.0,
            initial_capital=100000.0,
            window=20,
            step=1,
            regime=GlobalRegimeState.RISK_ON,
        )
        err = GovernanceViolationError(result)
        assert isinstance(err, Exception)

    def test_single_violation_message(self):
        result = validate_pipeline_config(
            meta_uncertainty=1.5,
            initial_capital=100000.0,
            window=20,
            step=1,
            regime=GlobalRegimeState.RISK_ON,
        )
        err = GovernanceViolationError(result)
        msg = str(err)
        assert "1 blocking violation" in msg

    def test_can_be_raised_and_caught(self):
        result = validate_pipeline_config(
            meta_uncertainty=2.0,
            initial_capital=100000.0,
            window=20,
            step=1,
            regime=GlobalRegimeState.RISK_ON,
        )
        with pytest.raises(GovernanceViolationError):
            raise GovernanceViolationError(result)
