# =============================================================================
# jarvis/research/feature_pipeline.py — Feature Research Pipeline (S33)
#
# No uncontrolled feature creep.
# Features are versioned, decaying features are automatically removed.
# Each feature has a registry entry.
#
# DET-06: PRUNE_THRESHOLD, MAX_DECAY_PER_DAY are fixed literals.
# PROHIBITED-05: No global mutable state.
# =============================================================================

from __future__ import annotations

import hashlib
import json
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

import numpy as np


# ---------------------------------------------------------------------------
# DATA CLASSES
# ---------------------------------------------------------------------------

@dataclass
class FeatureEntry:
    """Registry entry for a feature."""

    feature_id: str
    name: str
    version: str
    created_at: str
    last_validated: str
    importance_score: float  # [0,1]: 0=unimportant, 1=very important
    decay_rate: float  # Daily: how quickly feature loses relevance
    is_active: bool
    regime_valid: List[str]  # In which regimes valid
    hash: str  # SHA-256 of feature definition


@dataclass
class FeatureImportanceResult:
    """Result of decayed importance computation."""

    feature_id: str
    current_score: float
    decayed_score: float
    days_since_valid: int
    should_prune: bool
    reason: str


# ---------------------------------------------------------------------------
# FEATURE REGISTRY
# ---------------------------------------------------------------------------

class FeatureRegistry:
    """Formal feature management.

    All features must be registered.
    Automatic pruning on decay.
    """

    PRUNE_THRESHOLD = 0.10  # Features under 10% are pruned
    MAX_DECAY_PER_DAY = 0.02  # Max 2% decay per day

    def __init__(self, registry_path: Optional[Path] = None) -> None:
        self._registry: Dict[str, FeatureEntry] = {}
        self._path = registry_path

    def register(
        self,
        feature_id: str,
        name: str,
        version: str,
        regime_valid: List[str],
        importance: float = 0.5,
        decay_rate: float = 0.005,
    ) -> FeatureEntry:
        """Register a new feature.

        Raises if feature_id already exists (no silent duplicates).

        Args:
            feature_id: Unique identifier for the feature.
            name: Human-readable name.
            version: Semantic version string.
            regime_valid: List of regime names where feature is valid.
            importance: Initial importance score in [0, 1].
            decay_rate: Daily decay rate in [0, MAX_DECAY_PER_DAY].

        Returns:
            The registered FeatureEntry.

        Raises:
            ValueError: If feature_id already exists, importance out of range,
                        or decay_rate out of range.
        """
        if feature_id in self._registry:
            raise ValueError(
                f"Feature '{feature_id}' already registered. "
                "Use update_importance() for updates."
            )
        if not (0.0 <= importance <= 1.0):
            raise ValueError(f"importance must be in [0,1]: {importance}")
        if not (0.0 <= decay_rate <= self.MAX_DECAY_PER_DAY):
            raise ValueError(
                f"decay_rate must be in [0, {self.MAX_DECAY_PER_DAY}]: {decay_rate}"
            )

        feature_def = f"{feature_id}{name}{version}{regime_valid}"
        feat_hash = hashlib.sha256(feature_def.encode()).hexdigest()[:16]
        now = datetime.now(timezone.utc).isoformat()

        entry = FeatureEntry(
            feature_id=feature_id,
            name=name,
            version=version,
            created_at=now,
            last_validated=now,
            importance_score=float(np.clip(importance, 0.0, 1.0)),
            decay_rate=decay_rate,
            is_active=True,
            regime_valid=regime_valid,
            hash=feat_hash,
        )
        self._registry[feature_id] = entry
        return entry

    def update_importance(
        self,
        feature_id: str,
        new_importance: float,
    ) -> FeatureEntry:
        """Update importance score after revalidation backtesting.

        Args:
            feature_id: The feature to update.
            new_importance: New importance score (will be clipped to [0, 1]).

        Returns:
            The updated FeatureEntry.

        Raises:
            KeyError: If feature_id not in registry.
        """
        if feature_id not in self._registry:
            raise KeyError(f"Feature '{feature_id}' not in registry")
        entry = self._registry[feature_id]
        entry.importance_score = float(np.clip(new_importance, 0.0, 1.0))
        entry.last_validated = datetime.now(timezone.utc).isoformat()
        return entry

    def compute_decayed_importance(
        self,
        feature_id: str,
        days_elapsed: int,
    ) -> FeatureImportanceResult:
        """Compute worn-down importance score.

        Exponential decay: score * (1 - decay_rate)^days

        Args:
            feature_id: The feature to evaluate.
            days_elapsed: Number of days since last validation.

        Returns:
            FeatureImportanceResult with decay analysis.

        Raises:
            KeyError: If feature_id not in registry.
        """
        if feature_id not in self._registry:
            raise KeyError(f"Feature '{feature_id}' not in registry")

        entry = self._registry[feature_id]
        decayed = entry.importance_score * ((1.0 - entry.decay_rate) ** days_elapsed)
        decayed = float(max(decayed, 0.0))

        should_prune = decayed < self.PRUNE_THRESHOLD
        reason = ""
        if should_prune:
            reason = (
                f"Decayed score {decayed:.3f} < threshold {self.PRUNE_THRESHOLD}. "
                f"Days elapsed: {days_elapsed}"
            )

        return FeatureImportanceResult(
            feature_id=feature_id,
            current_score=entry.importance_score,
            decayed_score=decayed,
            days_since_valid=days_elapsed,
            should_prune=should_prune,
            reason=reason,
        )

    def prune_stale_features(
        self,
        days_threshold: int = 30,
    ) -> List[str]:
        """Deactivate features whose decayed importance falls below threshold.

        Args:
            days_threshold: Number of days to compute decay over.

        Returns:
            List of pruned feature IDs.
        """
        pruned: List[str] = []
        for fid, entry in self._registry.items():
            result = self.compute_decayed_importance(fid, days_threshold)
            if result.should_prune and entry.is_active:
                entry.is_active = False
                pruned.append(fid)
        return pruned

    def get_active_features(
        self,
        regime: Optional[str] = None,
    ) -> List[FeatureEntry]:
        """Return all active features, optionally filtered by regime.

        Args:
            regime: If provided, only return features valid for this regime.

        Returns:
            List of active FeatureEntry objects, sorted by importance (descending).
        """
        features = [e for e in self._registry.values() if e.is_active]
        if regime:
            features = [
                e for e in features
                if not e.regime_valid or regime in e.regime_valid
            ]
        return sorted(features, key=lambda e: -e.importance_score)

    def save(self, path: Optional[Path] = None) -> None:
        """Save registry as JSON.

        Args:
            path: Target path. Falls back to registry_path from constructor.

        Raises:
            ValueError: If no path specified.
        """
        target = path or self._path
        if not target:
            raise ValueError("No registry path specified")
        data = {fid: asdict(entry) for fid, entry in self._registry.items()}
        with open(target, "w") as f:
            json.dump(data, f, indent=2)

    def load(self, path: Optional[Path] = None) -> None:
        """Load registry from JSON.

        Args:
            path: Source path. Falls back to registry_path from constructor.
        """
        target = path or self._path
        if not target or not target.exists():
            return
        with open(target) as f:
            data = json.load(f)
        for fid, d in data.items():
            self._registry[fid] = FeatureEntry(**d)
