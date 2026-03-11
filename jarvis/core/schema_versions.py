# =============================================================================
# jarvis/core/schema_versions.py
# Authority: FAS v6.0.1 -- S37 SYSTEM ADDENDUM, lines 7517-7530
# =============================================================================
#
# SCOPE
# -----
# Single authoritative source for all schema version tags in the JARVIS system.
# All version constants are defined HERE and NOWHERE else.
# Any module needing a version tag MUST import from this file.
#
# INVARIANTS
# ----------
# 1. Changes require explicit version bump + migration documentation.
# 2. STRATEGY_OBJECT_VERSION must equal STRATEGY_SCHEMA_VERSION (99_REFERENCE).
#    Any divergence is a build error.
# 3. No silent schema mutation -- all changes require version bump.
#
# Public symbols:
#   GLOBAL_STATE_VERSION        GlobalSystemState dataclass schema version
#   STRATEGY_OBJECT_VERSION     StrategyObject schema version
#   CONFIDENCE_BUNDLE_VERSION   ConfidenceBundle {mu, sigma2, Q, S, U, R}
#   EVENT_LOG_VERSION           EventLog and EventLogEntry schema version
#   CHECKPOINT_VERSION          StateCheckpoint schema version
#   ALL_VERSIONS                Dict mapping name -> version for introspection
#
# DEPENDENCIES
# ------------
#   stdlib:    NONE
#   internal:  NONE
#   PROHIBITED: numpy, logging, random, file IO, network IO, datetime.now()
#
# DETERMINISM
# -----------
# DET-06  Fixed literals are not parametrisable.
# DET-07  Values are immutable string constants.
# =============================================================================

from __future__ import annotations

from typing import Dict

__all__ = [
    "GLOBAL_STATE_VERSION",
    "STRATEGY_OBJECT_VERSION",
    "CONFIDENCE_BUNDLE_VERSION",
    "EVENT_LOG_VERSION",
    "CHECKPOINT_VERSION",
    "ALL_VERSIONS",
]


# =============================================================================
# VERSION CONSTANTS (IMMUTABLE -- changes require version bump + migration)
# =============================================================================

GLOBAL_STATE_VERSION: str = "1.0.0"
"""GlobalSystemState dataclass schema version."""

STRATEGY_OBJECT_VERSION: str = "1.0.0"
"""StrategyObject schema version.  Must equal STRATEGY_SCHEMA_VERSION."""

CONFIDENCE_BUNDLE_VERSION: str = "1.0.0"
"""ConfidenceBundle {mu, sigma2, Q, S, U, R} schema version."""

EVENT_LOG_VERSION: str = "1.0.0"
"""EventLog and EventLogEntry schema version."""

CHECKPOINT_VERSION: str = "1.0.0"
"""StateCheckpoint schema version."""


# =============================================================================
# INTROSPECTION
# =============================================================================

ALL_VERSIONS: Dict[str, str] = {
    "GLOBAL_STATE_VERSION": GLOBAL_STATE_VERSION,
    "STRATEGY_OBJECT_VERSION": STRATEGY_OBJECT_VERSION,
    "CONFIDENCE_BUNDLE_VERSION": CONFIDENCE_BUNDLE_VERSION,
    "EVENT_LOG_VERSION": EVENT_LOG_VERSION,
    "CHECKPOINT_VERSION": CHECKPOINT_VERSION,
}
"""All version constants as a dict for programmatic access."""
