# =============================================================================
# jarvis/core/governance_monitor.py
# Authority: FAS v6.0.1 -- Governance Monitoring & Policy Enforcement
# =============================================================================
#
# SCOPE
# -----
# Governance monitor for policy enforcement and violation detection.
# Tracks state mutation calls, enforces permitted caller rules, and
# produces GovernanceViolation records for audit.  Pure analytical —
# no state mutation itself.
#
# Public symbols:
#   GOVERNANCE_CHECKS             Dict of governance rule descriptions
#   PERMITTED_CALLERS             Dict of module → permitted field sets
#   GovernanceViolation           Frozen dataclass for violation record
#   GovernanceAuditEntry          Frozen dataclass for audit trail entry
#   GovernanceMonitor             Monitor class
#
# DEPENDENCIES
# ------------
#   stdlib:    dataclasses, typing
#   external:  NONE
#   internal:  NONE
#   PROHIBITED: logging, random, file IO, network IO, datetime.now(), numpy
#
# DETERMINISM
# -----------
# DET-01  No stochastic operations.
# DET-02  All inputs passed explicitly.
# DET-03  No side effects (returns new records, does not mutate).
# DET-06  Fixed literals not parametrisable.
# DET-07  Same inputs = identical output.
# =============================================================================

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, FrozenSet, List, Optional, Tuple

__all__ = [
    "GOVERNANCE_CHECKS",
    "PERMITTED_CALLERS",
    "GovernanceViolation",
    "GovernanceAuditEntry",
    "GovernanceMonitor",
]


# =============================================================================
# SECTION 1 -- CONSTANTS (DET-06: fixed literals)
# =============================================================================

GOVERNANCE_CHECKS: Dict[str, str] = {
    "no_recursive_emit": (
        "EventDispatcher tracks active dispatch flag. "
        "emit() during active drain() raises RuntimeError immediately."
    ),
    "single_ctrl_update": (
        "ctrl.update() logs caller module and line. "
        "If called from outside permitted modules: violation recorded."
    ),
    "no_sandbox_ctrl_access": (
        "ScenarioSandboxEngine constructor does not accept ctrl reference. "
        "Any attempt to inject ctrl raises TypeError at construction."
    ),
    "confidence_trigger_required": (
        "ConfidenceUpdateEvent is only emitted by confidence_engine.py. "
        "Any other module emitting ConfidenceUpdateEvent is a violation."
    ),
    "sync_point_immutability": (
        "hybrid_sync_point in GlobalSystemState is set once. "
        "Any subsequent update attempt is a violation."
    ),
}
"""Governance rule descriptions."""

PERMITTED_CALLERS: Dict[str, FrozenSet[str]] = {
    "regime_engine": frozenset({
        "regime_state", "regime_confidence", "regime_probs",
    }),
    "volatility_layer": frozenset({
        "vol_regime", "vol_percentile", "vol_spike_flag", "nvu_normalized",
    }),
    "strategy_selector": frozenset({
        "strategy_mode", "weight_scalar", "active_strategy_id",
    }),
    "risk_engine": frozenset({
        "risk_mode", "risk_compression",
    }),
    "portfolio_context": frozenset({
        "positions", "gross_exposure", "net_exposure", "correlation_matrix",
    }),
    "confidence_engine": frozenset({
        "meta_uncertainty",
    }),
    "failure_handler": frozenset({
        "meta_uncertainty",
    }),
    "hybrid_coordinator": frozenset({
        "hybrid_sync_point", "operating_mode",
    }),
    "replay_engine": frozenset({
        "ALL",
    }),
}
"""Mapping of module name → set of fields that module may update."""


# =============================================================================
# SECTION 2 -- DATA TYPES
# =============================================================================

@dataclass(frozen=True)
class GovernanceViolation:
    """
    Record of a governance rule violation.

    Fields:
        rule_name:       Which governance rule was violated.
        caller_module:   Module that triggered the violation.
        attempted_field: Field the caller attempted to modify (if applicable).
        description:     Human-readable description of violation.
    """
    rule_name: str
    caller_module: str
    attempted_field: Optional[str]
    description: str


@dataclass(frozen=True)
class GovernanceAuditEntry:
    """
    Audit trail entry for a state mutation call.

    Fields:
        caller_module:  Module that called ctrl.update().
        fields_modified: Tuple of field names modified.
        permitted:       Whether the call was permitted.
        violation:       GovernanceViolation if not permitted, else None.
    """
    caller_module: str
    fields_modified: Tuple[str, ...]
    permitted: bool
    violation: Optional[GovernanceViolation]


# =============================================================================
# SECTION 3 -- MONITOR
# =============================================================================

class GovernanceMonitor:
    """
    Governance policy enforcement monitor.

    Validates state mutation calls against PERMITTED_CALLERS.
    Returns GovernanceAuditEntry and GovernanceViolation records.

    Stateless per call: does not accumulate internal state.
    All inputs passed explicitly.
    """

    def check_update_permission(
        self,
        caller_module: str,
        fields: Tuple[str, ...],
    ) -> GovernanceAuditEntry:
        """
        Check whether a caller module is permitted to update given fields.

        Args:
            caller_module: Name of the calling module.
            fields:        Tuple of field names being updated.

        Returns:
            GovernanceAuditEntry with permitted=True/False.

        Raises:
            TypeError: If arguments have wrong types.
            ValueError: If fields is empty.
        """
        if not isinstance(caller_module, str):
            raise TypeError(
                f"caller_module must be a string, "
                f"got {type(caller_module).__name__}"
            )
        if not isinstance(fields, tuple):
            raise TypeError(
                f"fields must be a tuple, "
                f"got {type(fields).__name__}"
            )
        if len(fields) == 0:
            raise ValueError("fields must not be empty")

        permitted_fields = PERMITTED_CALLERS.get(caller_module)

        # Unknown caller → violation
        if permitted_fields is None:
            violation = GovernanceViolation(
                rule_name="single_ctrl_update",
                caller_module=caller_module,
                attempted_field=fields[0] if len(fields) == 1 else None,
                description=(
                    f"Module '{caller_module}' is not in PERMITTED_CALLERS. "
                    f"Attempted to modify: {fields}"
                ),
            )
            return GovernanceAuditEntry(
                caller_module=caller_module,
                fields_modified=fields,
                permitted=False,
                violation=violation,
            )

        # replay_engine has ALL access
        if "ALL" in permitted_fields:
            return GovernanceAuditEntry(
                caller_module=caller_module,
                fields_modified=fields,
                permitted=True,
                violation=None,
            )

        # Check each field
        unauthorized = [f for f in fields if f not in permitted_fields]
        if unauthorized:
            violation = GovernanceViolation(
                rule_name="single_ctrl_update",
                caller_module=caller_module,
                attempted_field=unauthorized[0],
                description=(
                    f"Module '{caller_module}' attempted to modify "
                    f"unauthorized fields: {unauthorized}. "
                    f"Permitted: {sorted(permitted_fields)}"
                ),
            )
            return GovernanceAuditEntry(
                caller_module=caller_module,
                fields_modified=fields,
                permitted=False,
                violation=violation,
            )

        return GovernanceAuditEntry(
            caller_module=caller_module,
            fields_modified=fields,
            permitted=True,
            violation=None,
        )

    def check_sync_point_immutability(
        self,
        already_set: bool,
        caller_module: str,
    ) -> Optional[GovernanceViolation]:
        """
        Check if hybrid_sync_point is being set more than once.

        Args:
            already_set:    Whether sync_point has already been set.
            caller_module:  Module attempting the update.

        Returns:
            GovernanceViolation if already_set is True, else None.

        Raises:
            TypeError: If arguments have wrong types.
        """
        if not isinstance(already_set, bool):
            raise TypeError(
                f"already_set must be bool, "
                f"got {type(already_set).__name__}"
            )
        if not isinstance(caller_module, str):
            raise TypeError(
                f"caller_module must be a string, "
                f"got {type(caller_module).__name__}"
            )

        if already_set:
            return GovernanceViolation(
                rule_name="sync_point_immutability",
                caller_module=caller_module,
                attempted_field="hybrid_sync_point",
                description=(
                    f"hybrid_sync_point is already set. "
                    f"Module '{caller_module}' attempted to modify it again."
                ),
            )
        return None

    def check_confidence_emitter(
        self,
        emitter_module: str,
    ) -> Optional[GovernanceViolation]:
        """
        Check if a module is authorized to emit ConfidenceUpdateEvent.

        Only confidence_engine is permitted.

        Args:
            emitter_module: Module attempting to emit the event.

        Returns:
            GovernanceViolation if not authorized, else None.

        Raises:
            TypeError: If emitter_module is not a string.
        """
        if not isinstance(emitter_module, str):
            raise TypeError(
                f"emitter_module must be a string, "
                f"got {type(emitter_module).__name__}"
            )

        if emitter_module != "confidence_engine":
            return GovernanceViolation(
                rule_name="confidence_trigger_required",
                caller_module=emitter_module,
                attempted_field="meta_uncertainty",
                description=(
                    f"Only confidence_engine may emit ConfidenceUpdateEvent. "
                    f"Module '{emitter_module}' is unauthorized."
                ),
            )
        return None

    def validate_batch(
        self,
        entries: List[Tuple[str, Tuple[str, ...]]],
    ) -> List[GovernanceAuditEntry]:
        """
        Validate a batch of (caller_module, fields) pairs.

        Args:
            entries: List of (caller_module, fields) tuples.

        Returns:
            List of GovernanceAuditEntry, one per entry.

        Raises:
            TypeError: If entries is not a list.
        """
        if not isinstance(entries, list):
            raise TypeError(
                f"entries must be a list, "
                f"got {type(entries).__name__}"
            )

        results: List[GovernanceAuditEntry] = []
        for caller, fields in entries:
            results.append(self.check_update_permission(caller, fields))
        return results
