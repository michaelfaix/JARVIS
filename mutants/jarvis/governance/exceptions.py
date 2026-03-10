# jarvis/governance/exceptions.py
# Version: 1.0.0
# Authority: Master FAS v6.1.0-G -- Governance Integration Layer

from __future__ import annotations
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from jarvis.governance.policy_validator import PolicyValidationResult
from typing import Annotated
from typing import Callable
from typing import ClassVar

MutantDict = Annotated[dict[str, Callable], "Mutant"] # type: ignore


def _mutmut_trampoline(orig, mutants, call_args, call_kwargs, self_arg = None): # type: ignore
    """Forward call to original or mutated function, depending on the environment"""
    import os # type: ignore
    mutant_under_test = os.environ['MUTANT_UNDER_TEST'] # type: ignore
    if mutant_under_test == 'fail': # type: ignore
        from mutmut.__main__ import MutmutProgrammaticFailException # type: ignore
        raise MutmutProgrammaticFailException('Failed programmatically')       # type: ignore
    elif mutant_under_test == 'stats': # type: ignore
        from mutmut.__main__ import record_trampoline_hit # type: ignore
        record_trampoline_hit(orig.__module__ + '.' + orig.__name__) # type: ignore
        # (for class methods, orig is bound and thus does not need the explicit self argument)
        result = orig(*call_args, **call_kwargs) # type: ignore
        return result # type: ignore
    prefix = orig.__module__ + '.' + orig.__name__ + '__mutmut_' # type: ignore
    if not mutant_under_test.startswith(prefix): # type: ignore
        result = orig(*call_args, **call_kwargs) # type: ignore
        return result # type: ignore
    mutant_name = mutant_under_test.rpartition('.')[-1] # type: ignore
    if self_arg is not None: # type: ignore
        # call to a class method where self is not bound
        result = mutants[mutant_name](self_arg, *call_args, **call_kwargs) # type: ignore
    else:
        result = mutants[mutant_name](*call_args, **call_kwargs) # type: ignore
    return result # type: ignore


class GovernanceViolationError(Exception):
    """
    Raised when validate_pipeline_config() returns blocking violations.

    Attributes
    ----------
    result : PolicyValidationResult
    blocking_violations : tuple
    """

    def __init__(self, result: "PolicyValidationResult") -> None:
        args = [result]# type: ignore
        kwargs = {}# type: ignore
        return _mutmut_trampoline(object.__getattribute__(self, 'xǁGovernanceViolationErrorǁ__init____mutmut_orig'), object.__getattribute__(self, 'xǁGovernanceViolationErrorǁ__init____mutmut_mutants'), args, kwargs, self)

    def xǁGovernanceViolationErrorǁ__init____mutmut_orig(self, result: "PolicyValidationResult") -> None:
        self.result = result
        self.blocking_violations = result.blocking_violations
        lines = [
            f"Governance policy violated: "
            f"{len(result.blocking_violations)} blocking violation(s) detected.",
        ]
        for v in result.blocking_violations:
            lines.append(f"  [{v.rule_id}] {v.field_name}: {v.message}")
        super().__init__("\n".join(lines))

    def xǁGovernanceViolationErrorǁ__init____mutmut_1(self, result: "PolicyValidationResult") -> None:
        self.result = None
        self.blocking_violations = result.blocking_violations
        lines = [
            f"Governance policy violated: "
            f"{len(result.blocking_violations)} blocking violation(s) detected.",
        ]
        for v in result.blocking_violations:
            lines.append(f"  [{v.rule_id}] {v.field_name}: {v.message}")
        super().__init__("\n".join(lines))

    def xǁGovernanceViolationErrorǁ__init____mutmut_2(self, result: "PolicyValidationResult") -> None:
        self.result = result
        self.blocking_violations = None
        lines = [
            f"Governance policy violated: "
            f"{len(result.blocking_violations)} blocking violation(s) detected.",
        ]
        for v in result.blocking_violations:
            lines.append(f"  [{v.rule_id}] {v.field_name}: {v.message}")
        super().__init__("\n".join(lines))

    def xǁGovernanceViolationErrorǁ__init____mutmut_3(self, result: "PolicyValidationResult") -> None:
        self.result = result
        self.blocking_violations = result.blocking_violations
        lines = None
        for v in result.blocking_violations:
            lines.append(f"  [{v.rule_id}] {v.field_name}: {v.message}")
        super().__init__("\n".join(lines))

    def xǁGovernanceViolationErrorǁ__init____mutmut_4(self, result: "PolicyValidationResult") -> None:
        self.result = result
        self.blocking_violations = result.blocking_violations
        lines = [
            f"Governance policy violated: "
            f"{len(result.blocking_violations)} blocking violation(s) detected.",
        ]
        for v in result.blocking_violations:
            lines.append(None)
        super().__init__("\n".join(lines))

    def xǁGovernanceViolationErrorǁ__init____mutmut_5(self, result: "PolicyValidationResult") -> None:
        self.result = result
        self.blocking_violations = result.blocking_violations
        lines = [
            f"Governance policy violated: "
            f"{len(result.blocking_violations)} blocking violation(s) detected.",
        ]
        for v in result.blocking_violations:
            lines.append(f"  [{v.rule_id}] {v.field_name}: {v.message}")
        super().__init__(None)

    def xǁGovernanceViolationErrorǁ__init____mutmut_6(self, result: "PolicyValidationResult") -> None:
        self.result = result
        self.blocking_violations = result.blocking_violations
        lines = [
            f"Governance policy violated: "
            f"{len(result.blocking_violations)} blocking violation(s) detected.",
        ]
        for v in result.blocking_violations:
            lines.append(f"  [{v.rule_id}] {v.field_name}: {v.message}")
        super().__init__("\n".join(None))

    def xǁGovernanceViolationErrorǁ__init____mutmut_7(self, result: "PolicyValidationResult") -> None:
        self.result = result
        self.blocking_violations = result.blocking_violations
        lines = [
            f"Governance policy violated: "
            f"{len(result.blocking_violations)} blocking violation(s) detected.",
        ]
        for v in result.blocking_violations:
            lines.append(f"  [{v.rule_id}] {v.field_name}: {v.message}")
        super().__init__("XX\nXX".join(lines))
    
    xǁGovernanceViolationErrorǁ__init____mutmut_mutants : ClassVar[MutantDict] = { # type: ignore
    'xǁGovernanceViolationErrorǁ__init____mutmut_1': xǁGovernanceViolationErrorǁ__init____mutmut_1, 
        'xǁGovernanceViolationErrorǁ__init____mutmut_2': xǁGovernanceViolationErrorǁ__init____mutmut_2, 
        'xǁGovernanceViolationErrorǁ__init____mutmut_3': xǁGovernanceViolationErrorǁ__init____mutmut_3, 
        'xǁGovernanceViolationErrorǁ__init____mutmut_4': xǁGovernanceViolationErrorǁ__init____mutmut_4, 
        'xǁGovernanceViolationErrorǁ__init____mutmut_5': xǁGovernanceViolationErrorǁ__init____mutmut_5, 
        'xǁGovernanceViolationErrorǁ__init____mutmut_6': xǁGovernanceViolationErrorǁ__init____mutmut_6, 
        'xǁGovernanceViolationErrorǁ__init____mutmut_7': xǁGovernanceViolationErrorǁ__init____mutmut_7
    }
    xǁGovernanceViolationErrorǁ__init____mutmut_orig.__name__ = 'xǁGovernanceViolationErrorǁ__init__'
