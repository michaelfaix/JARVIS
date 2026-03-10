# =============================================================================
# JARVIS v6.1.0 -- STRATEGY REGISTRY
# File:   jarvis/core/strategy_registry.py
# Version: 1.0.0
# Session: S26
# =============================================================================
#
# Central registry for StrategyObject instances.
# Registration requires validation + schema version match.
# No silent migration. Version mismatch = hard error.
#
# CLASSIFICATION: P0 — ANALYSIS AND STRATEGY RESEARCH TOOL.
# =============================================================================

from __future__ import annotations

from typing import Dict, List

from jarvis.core.strategy_schema import (
    STRATEGY_SCHEMA_VERSION,
    StrategyObject,
)


# ---------------------------------------------------------------------------
# REGISTRY STATE
# ---------------------------------------------------------------------------

_REGISTRY: Dict[str, StrategyObject] = {}


# ---------------------------------------------------------------------------
# PUBLIC API
# ---------------------------------------------------------------------------

def register(obj: StrategyObject) -> None:
    """
    Registriert StrategyObject. Wirft bei Duplikat oder Validierungsfehler.
    """
    obj.validate()
    if obj.Strategy_ID in _REGISTRY:
        raise ValueError(f"Duplicate Strategy_ID: {obj.Strategy_ID}")
    if obj.version != STRATEGY_SCHEMA_VERSION:
        raise ValueError(
            f"Schema version mismatch: {obj.version} != {STRATEGY_SCHEMA_VERSION}"
        )
    _REGISTRY[obj.Strategy_ID] = obj


def get(strategy_id: str) -> StrategyObject:
    """
    Gibt registriertes StrategyObject zurueck. KeyError bei unbekannter ID.
    """
    if strategy_id not in _REGISTRY:
        raise KeyError(f"Unregistered strategy: {strategy_id}")
    return _REGISTRY[strategy_id]


def list_ids() -> List[str]:
    """Gibt alle registrierten Strategy-IDs zurueck."""
    return list(_REGISTRY.keys())


def clear() -> None:
    """Leert die gesamte Registry. Nur fuer Tests gedacht."""
    _REGISTRY.clear()


__all__ = [
    "register",
    "get",
    "list_ids",
    "clear",
]
