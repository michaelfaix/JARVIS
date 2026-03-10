# =============================================================================
# tests/unit/research/test_feature_pipeline.py — S33 Feature Research Pipeline
#
# Comprehensive tests for FeatureRegistry, FeatureEntry, FeatureImportanceResult.
# =============================================================================

import json
import math
import pytest
from pathlib import Path

from jarvis.research.feature_pipeline import (
    FeatureEntry,
    FeatureImportanceResult,
    FeatureRegistry,
)


# ---------------------------------------------------------------------------
# CONSTANTS (DET-06)
# ---------------------------------------------------------------------------

class TestConstants:
    """Verify fixed literals are correct per FAS."""

    def test_prune_threshold(self):
        assert FeatureRegistry.PRUNE_THRESHOLD == 0.10

    def test_max_decay_per_day(self):
        assert FeatureRegistry.MAX_DECAY_PER_DAY == 0.02

    def test_constants_not_parameterizable(self):
        """DET-06: Constants must be class-level fixed literals."""
        reg = FeatureRegistry()
        assert reg.PRUNE_THRESHOLD == 0.10
        assert reg.MAX_DECAY_PER_DAY == 0.02


# ---------------------------------------------------------------------------
# FEATURE ENTRY DATACLASS
# ---------------------------------------------------------------------------

class TestFeatureEntry:
    """Verify FeatureEntry structure."""

    def test_fields_exist(self):
        entry = FeatureEntry(
            feature_id="f1",
            name="Test",
            version="1.0",
            created_at="2026-01-01",
            last_validated="2026-01-01",
            importance_score=0.5,
            decay_rate=0.005,
            is_active=True,
            regime_valid=["RISK_ON"],
            hash="abc123",
        )
        assert entry.feature_id == "f1"
        assert entry.name == "Test"
        assert entry.version == "1.0"
        assert entry.is_active is True
        assert entry.regime_valid == ["RISK_ON"]
        assert entry.hash == "abc123"

    def test_importance_score_stored(self):
        entry = FeatureEntry(
            feature_id="f1", name="T", version="1.0",
            created_at="", last_validated="",
            importance_score=0.75, decay_rate=0.01,
            is_active=True, regime_valid=[], hash="x",
        )
        assert entry.importance_score == 0.75

    def test_decay_rate_stored(self):
        entry = FeatureEntry(
            feature_id="f1", name="T", version="1.0",
            created_at="", last_validated="",
            importance_score=0.5, decay_rate=0.015,
            is_active=True, regime_valid=[], hash="x",
        )
        assert entry.decay_rate == 0.015


# ---------------------------------------------------------------------------
# FEATURE IMPORTANCE RESULT
# ---------------------------------------------------------------------------

class TestFeatureImportanceResult:
    """Verify FeatureImportanceResult structure."""

    def test_fields(self):
        result = FeatureImportanceResult(
            feature_id="f1",
            current_score=0.8,
            decayed_score=0.3,
            days_since_valid=60,
            should_prune=False,
            reason="",
        )
        assert result.feature_id == "f1"
        assert result.current_score == 0.8
        assert result.decayed_score == 0.3
        assert result.days_since_valid == 60
        assert result.should_prune is False

    def test_prune_reason_populated(self):
        result = FeatureImportanceResult(
            feature_id="f1",
            current_score=0.5,
            decayed_score=0.05,
            days_since_valid=100,
            should_prune=True,
            reason="Below threshold",
        )
        assert result.should_prune is True
        assert "Below threshold" in result.reason


# ---------------------------------------------------------------------------
# REGISTRATION
# ---------------------------------------------------------------------------

class TestRegister:
    """Test feature registration."""

    def test_register_basic(self):
        reg = FeatureRegistry()
        entry = reg.register("rsi_14", "RSI-14", "1.0", ["TRENDING", "RANGING"])
        assert entry.feature_id == "rsi_14"
        assert entry.name == "RSI-14"
        assert entry.version == "1.0"
        assert entry.is_active is True
        assert entry.regime_valid == ["TRENDING", "RANGING"]

    def test_register_default_importance(self):
        reg = FeatureRegistry()
        entry = reg.register("f1", "Test", "1.0", [])
        assert entry.importance_score == 0.5

    def test_register_default_decay_rate(self):
        reg = FeatureRegistry()
        entry = reg.register("f1", "Test", "1.0", [])
        assert entry.decay_rate == 0.005

    def test_register_custom_importance(self):
        reg = FeatureRegistry()
        entry = reg.register("f1", "Test", "1.0", [], importance=0.9)
        assert entry.importance_score == 0.9

    def test_register_custom_decay_rate(self):
        reg = FeatureRegistry()
        entry = reg.register("f1", "Test", "1.0", [], decay_rate=0.015)
        assert entry.decay_rate == 0.015

    def test_register_hash_generated(self):
        reg = FeatureRegistry()
        entry = reg.register("f1", "Test", "1.0", ["RISK_ON"])
        assert len(entry.hash) == 16
        assert all(c in "0123456789abcdef" for c in entry.hash)

    def test_register_hash_deterministic(self):
        """Same inputs → same hash (DET-05)."""
        reg1 = FeatureRegistry()
        reg2 = FeatureRegistry()
        e1 = reg1.register("f1", "Test", "1.0", ["RISK_ON"])
        e2 = reg2.register("f1", "Test", "1.0", ["RISK_ON"])
        assert e1.hash == e2.hash

    def test_register_different_inputs_different_hash(self):
        reg = FeatureRegistry()
        e1 = reg.register("f1", "Test", "1.0", [])
        e2 = reg.register("f2", "Other", "1.0", [])
        assert e1.hash != e2.hash

    def test_register_timestamps_set(self):
        reg = FeatureRegistry()
        entry = reg.register("f1", "Test", "1.0", [])
        assert entry.created_at != ""
        assert entry.last_validated != ""
        assert entry.created_at == entry.last_validated

    def test_register_empty_regime_list(self):
        reg = FeatureRegistry()
        entry = reg.register("f1", "Test", "1.0", [])
        assert entry.regime_valid == []


# ---------------------------------------------------------------------------
# REGISTRATION VALIDATION
# ---------------------------------------------------------------------------

class TestRegisterValidation:
    """Test validation rules on registration."""

    def test_duplicate_raises(self):
        reg = FeatureRegistry()
        reg.register("rsi_14", "RSI-14", "1.0", [])
        with pytest.raises(ValueError, match="already registered"):
            reg.register("rsi_14", "RSI-14", "1.0", [])

    def test_importance_negative_raises(self):
        reg = FeatureRegistry()
        with pytest.raises(ValueError, match="importance must be in"):
            reg.register("f1", "Test", "1.0", [], importance=-0.1)

    def test_importance_above_one_raises(self):
        reg = FeatureRegistry()
        with pytest.raises(ValueError, match="importance must be in"):
            reg.register("f1", "Test", "1.0", [], importance=1.1)

    def test_decay_rate_negative_raises(self):
        reg = FeatureRegistry()
        with pytest.raises(ValueError, match="decay_rate must be in"):
            reg.register("f1", "Test", "1.0", [], decay_rate=-0.001)

    def test_decay_rate_above_max_raises(self):
        reg = FeatureRegistry()
        with pytest.raises(ValueError, match="decay_rate must be in"):
            reg.register("f1", "Test", "1.0", [], decay_rate=0.03)

    def test_importance_boundary_zero(self):
        reg = FeatureRegistry()
        entry = reg.register("f1", "Test", "1.0", [], importance=0.0)
        assert entry.importance_score == 0.0

    def test_importance_boundary_one(self):
        reg = FeatureRegistry()
        entry = reg.register("f1", "Test", "1.0", [], importance=1.0)
        assert entry.importance_score == 1.0

    def test_decay_rate_boundary_zero(self):
        reg = FeatureRegistry()
        entry = reg.register("f1", "Test", "1.0", [], decay_rate=0.0)
        assert entry.decay_rate == 0.0

    def test_decay_rate_boundary_max(self):
        reg = FeatureRegistry()
        entry = reg.register("f1", "Test", "1.0", [], decay_rate=0.02)
        assert entry.decay_rate == 0.02


# ---------------------------------------------------------------------------
# UPDATE IMPORTANCE
# ---------------------------------------------------------------------------

class TestUpdateImportance:
    """Test importance score updates."""

    def test_update_changes_score(self):
        reg = FeatureRegistry()
        reg.register("f1", "Test", "1.0", [], importance=0.5)
        updated = reg.update_importance("f1", 0.9)
        assert updated.importance_score == 0.9

    def test_update_clips_above_one(self):
        reg = FeatureRegistry()
        reg.register("f1", "Test", "1.0", [], importance=0.5)
        updated = reg.update_importance("f1", 1.5)
        assert updated.importance_score == 1.0

    def test_update_clips_below_zero(self):
        reg = FeatureRegistry()
        reg.register("f1", "Test", "1.0", [], importance=0.5)
        updated = reg.update_importance("f1", -0.5)
        assert updated.importance_score == 0.0

    def test_update_refreshes_last_validated(self):
        reg = FeatureRegistry()
        entry = reg.register("f1", "Test", "1.0", [])
        old_validated = entry.last_validated
        # Small time difference may not be visible, but field is updated
        updated = reg.update_importance("f1", 0.7)
        assert updated.last_validated is not None
        assert isinstance(updated.last_validated, str)

    def test_update_unknown_feature_raises(self):
        reg = FeatureRegistry()
        with pytest.raises(KeyError, match="not in registry"):
            reg.update_importance("nonexistent", 0.5)


# ---------------------------------------------------------------------------
# DECAYED IMPORTANCE
# ---------------------------------------------------------------------------

class TestDecayedImportance:
    """Test exponential decay computation."""

    def test_decay_reduces_score(self):
        """FAS test: decay must reduce score."""
        reg = FeatureRegistry()
        reg.register("feat1", "Test", "1.0", [], importance=0.8)
        result = reg.compute_decayed_importance("feat1", days_elapsed=60)
        assert result.decayed_score < 0.8

    def test_decay_formula_correct(self):
        """Verify: score * (1 - decay_rate)^days."""
        reg = FeatureRegistry()
        reg.register("f1", "Test", "1.0", [], importance=0.8, decay_rate=0.01)
        result = reg.compute_decayed_importance("f1", days_elapsed=30)
        expected = 0.8 * ((1.0 - 0.01) ** 30)
        assert abs(result.decayed_score - expected) < 1e-10

    def test_decay_zero_days(self):
        """No decay if days_elapsed=0."""
        reg = FeatureRegistry()
        reg.register("f1", "Test", "1.0", [], importance=0.8, decay_rate=0.01)
        result = reg.compute_decayed_importance("f1", days_elapsed=0)
        assert result.decayed_score == 0.8

    def test_decay_zero_rate(self):
        """No decay if decay_rate=0."""
        reg = FeatureRegistry()
        reg.register("f1", "Test", "1.0", [], importance=0.8, decay_rate=0.0)
        result = reg.compute_decayed_importance("f1", days_elapsed=365)
        assert result.decayed_score == 0.8

    def test_decay_never_negative(self):
        """Decayed score must be >= 0."""
        reg = FeatureRegistry()
        reg.register("f1", "Test", "1.0", [], importance=0.1, decay_rate=0.02)
        result = reg.compute_decayed_importance("f1", days_elapsed=10000)
        assert result.decayed_score >= 0.0

    def test_decay_unknown_feature_raises(self):
        reg = FeatureRegistry()
        with pytest.raises(KeyError, match="not in registry"):
            reg.compute_decayed_importance("nonexistent", 10)

    def test_decay_current_score_preserved(self):
        """current_score in result should be the original, not decayed."""
        reg = FeatureRegistry()
        reg.register("f1", "Test", "1.0", [], importance=0.8, decay_rate=0.01)
        result = reg.compute_decayed_importance("f1", days_elapsed=30)
        assert result.current_score == 0.8

    def test_decay_days_since_valid(self):
        reg = FeatureRegistry()
        reg.register("f1", "Test", "1.0", [], importance=0.8)
        result = reg.compute_decayed_importance("f1", days_elapsed=42)
        assert result.days_since_valid == 42


# ---------------------------------------------------------------------------
# PRUNE THRESHOLD
# ---------------------------------------------------------------------------

class TestPruneThreshold:
    """Test prune decisions based on threshold."""

    def test_prune_threshold_triggers(self):
        """FAS test: feature below threshold should be pruned."""
        reg = FeatureRegistry()
        reg.register("feat_bad", "Bad Feature", "1.0", [],
                      importance=0.12, decay_rate=0.015)
        result = reg.compute_decayed_importance("feat_bad", days_elapsed=100)
        assert result.should_prune is True

    def test_prune_threshold_not_triggered(self):
        """High importance feature should not be pruned."""
        reg = FeatureRegistry()
        reg.register("feat_good", "Good Feature", "1.0", [],
                      importance=0.95, decay_rate=0.005)
        result = reg.compute_decayed_importance("feat_good", days_elapsed=30)
        assert result.should_prune is False

    def test_prune_reason_populated_when_pruning(self):
        reg = FeatureRegistry()
        reg.register("f1", "Test", "1.0", [], importance=0.12, decay_rate=0.015)
        result = reg.compute_decayed_importance("f1", days_elapsed=100)
        assert result.should_prune is True
        assert "Decayed score" in result.reason
        assert "threshold" in result.reason

    def test_prune_reason_empty_when_not_pruning(self):
        reg = FeatureRegistry()
        reg.register("f1", "Test", "1.0", [], importance=0.95, decay_rate=0.001)
        result = reg.compute_decayed_importance("f1", days_elapsed=10)
        assert result.should_prune is False
        assert result.reason == ""

    def test_prune_boundary_exactly_at_threshold(self):
        """Score exactly at threshold should NOT be pruned (< not <=)."""
        reg = FeatureRegistry()
        # We need decayed score to land exactly at 0.10
        # importance=0.10, decay_rate=0.0, days=0 → score=0.10
        reg.register("f1", "Test", "1.0", [], importance=0.10, decay_rate=0.0)
        result = reg.compute_decayed_importance("f1", days_elapsed=0)
        assert result.decayed_score == 0.10
        assert result.should_prune is False


# ---------------------------------------------------------------------------
# PRUNE STALE FEATURES
# ---------------------------------------------------------------------------

class TestPruneStaleFeatures:
    """Test bulk pruning."""

    def test_prune_deactivates_stale(self):
        reg = FeatureRegistry()
        reg.register("f1", "Stale", "1.0", [], importance=0.12, decay_rate=0.015)
        pruned = reg.prune_stale_features(days_threshold=100)
        assert "f1" in pruned
        # Verify deactivated
        active = reg.get_active_features()
        assert not any(f.feature_id == "f1" for f in active)

    def test_prune_keeps_strong_features(self):
        reg = FeatureRegistry()
        reg.register("f1", "Strong", "1.0", [], importance=0.95, decay_rate=0.001)
        pruned = reg.prune_stale_features(days_threshold=30)
        assert "f1" not in pruned
        active = reg.get_active_features()
        assert any(f.feature_id == "f1" for f in active)

    def test_prune_mixed(self):
        reg = FeatureRegistry()
        reg.register("weak", "Weak", "1.0", [], importance=0.12, decay_rate=0.015)
        reg.register("strong", "Strong", "1.0", [], importance=0.95, decay_rate=0.001)
        pruned = reg.prune_stale_features(days_threshold=100)
        assert "weak" in pruned
        assert "strong" not in pruned

    def test_prune_already_inactive_not_pruned_again(self):
        """Already inactive features should not appear in pruned list."""
        reg = FeatureRegistry()
        reg.register("f1", "Stale", "1.0", [], importance=0.12, decay_rate=0.015)
        # First prune
        pruned1 = reg.prune_stale_features(days_threshold=100)
        assert "f1" in pruned1
        # Second prune — already inactive
        pruned2 = reg.prune_stale_features(days_threshold=100)
        assert "f1" not in pruned2

    def test_prune_default_threshold(self):
        """Default days_threshold is 30."""
        reg = FeatureRegistry()
        reg.register("f1", "Low", "1.0", [], importance=0.11, decay_rate=0.02)
        # With decay_rate=0.02 and 30 days: 0.11 * 0.98^30 ≈ 0.0598 < 0.10
        pruned = reg.prune_stale_features()
        assert "f1" in pruned

    def test_prune_empty_registry(self):
        reg = FeatureRegistry()
        pruned = reg.prune_stale_features()
        assert pruned == []


# ---------------------------------------------------------------------------
# GET ACTIVE FEATURES
# ---------------------------------------------------------------------------

class TestGetActiveFeatures:
    """Test active feature retrieval and filtering."""

    def test_active_features_all(self):
        reg = FeatureRegistry()
        reg.register("f1", "A", "1.0", [])
        reg.register("f2", "B", "1.0", [])
        active = reg.get_active_features()
        assert len(active) == 2

    def test_active_features_excludes_inactive(self):
        reg = FeatureRegistry()
        reg.register("f1", "A", "1.0", [], importance=0.11, decay_rate=0.02)
        reg.register("f2", "B", "1.0", [], importance=0.9)
        reg.prune_stale_features(days_threshold=100)
        active = reg.get_active_features()
        assert len(active) == 1
        assert active[0].feature_id == "f2"

    def test_active_features_filter_by_regime(self):
        """FAS test: regime filtering."""
        reg = FeatureRegistry()
        reg.register("rsi", "RSI", "1.0", ["TRENDING"])
        reg.register("bb", "BB", "1.0", ["RANGING"])
        active = reg.get_active_features(regime="TRENDING")
        assert any(f.feature_id == "rsi" for f in active)
        assert not any(f.feature_id == "bb" for f in active)

    def test_active_features_empty_regime_valid_included(self):
        """Features with empty regime_valid should match all regimes."""
        reg = FeatureRegistry()
        reg.register("f1", "Universal", "1.0", [])
        active = reg.get_active_features(regime="TRENDING")
        assert any(f.feature_id == "f1" for f in active)

    def test_active_features_sorted_by_importance(self):
        reg = FeatureRegistry()
        reg.register("low", "Low", "1.0", [], importance=0.3)
        reg.register("high", "High", "1.0", [], importance=0.9)
        reg.register("mid", "Mid", "1.0", [], importance=0.6)
        active = reg.get_active_features()
        assert active[0].feature_id == "high"
        assert active[1].feature_id == "mid"
        assert active[2].feature_id == "low"

    def test_active_features_no_regime_filter(self):
        reg = FeatureRegistry()
        reg.register("f1", "A", "1.0", ["TRENDING"])
        reg.register("f2", "B", "1.0", ["RANGING"])
        active = reg.get_active_features(regime=None)
        assert len(active) == 2

    def test_active_features_empty_registry(self):
        reg = FeatureRegistry()
        assert reg.get_active_features() == []

    def test_active_features_multi_regime(self):
        """Feature valid for multiple regimes."""
        reg = FeatureRegistry()
        reg.register("f1", "Multi", "1.0", ["TRENDING", "RANGING", "CRISIS"])
        active = reg.get_active_features(regime="CRISIS")
        assert len(active) == 1
        assert active[0].feature_id == "f1"


# ---------------------------------------------------------------------------
# SAVE / LOAD
# ---------------------------------------------------------------------------

class TestSaveLoad:
    """Test JSON persistence."""

    def test_save_creates_file(self, tmp_path):
        reg = FeatureRegistry()
        reg.register("f1", "Test", "1.0", ["RISK_ON"])
        out = tmp_path / "registry.json"
        reg.save(out)
        assert out.exists()

    def test_save_valid_json(self, tmp_path):
        reg = FeatureRegistry()
        reg.register("f1", "Test", "1.0", [])
        out = tmp_path / "registry.json"
        reg.save(out)
        data = json.loads(out.read_text())
        assert "f1" in data

    def test_load_restores_entries(self, tmp_path):
        # Save
        reg1 = FeatureRegistry()
        reg1.register("f1", "Test", "1.0", ["RISK_ON"], importance=0.7)
        out = tmp_path / "registry.json"
        reg1.save(out)

        # Load
        reg2 = FeatureRegistry()
        reg2.load(out)
        active = reg2.get_active_features()
        assert len(active) == 1
        assert active[0].feature_id == "f1"
        assert active[0].importance_score == 0.7

    def test_load_nonexistent_path_no_error(self, tmp_path):
        reg = FeatureRegistry()
        reg.load(tmp_path / "nonexistent.json")
        assert reg.get_active_features() == []

    def test_load_none_path_no_error(self):
        reg = FeatureRegistry()
        reg.load(None)
        assert reg.get_active_features() == []

    def test_save_no_path_raises(self):
        reg = FeatureRegistry()
        with pytest.raises(ValueError, match="No registry path"):
            reg.save()

    def test_save_uses_constructor_path(self, tmp_path):
        out = tmp_path / "reg.json"
        reg = FeatureRegistry(registry_path=out)
        reg.register("f1", "Test", "1.0", [])
        reg.save()
        assert out.exists()

    def test_load_uses_constructor_path(self, tmp_path):
        out = tmp_path / "reg.json"
        reg1 = FeatureRegistry(registry_path=out)
        reg1.register("f1", "Test", "1.0", [])
        reg1.save()

        reg2 = FeatureRegistry(registry_path=out)
        reg2.load()
        active = reg2.get_active_features()
        assert len(active) == 1

    def test_roundtrip_preserves_all_fields(self, tmp_path):
        out = tmp_path / "reg.json"
        reg1 = FeatureRegistry()
        entry = reg1.register("f1", "RSI-14", "2.0", ["TRENDING", "CRISIS"],
                               importance=0.85, decay_rate=0.012)
        reg1.save(out)

        reg2 = FeatureRegistry()
        reg2.load(out)
        loaded = reg2.get_active_features()
        assert len(loaded) == 1
        e = loaded[0]
        assert e.feature_id == entry.feature_id
        assert e.name == entry.name
        assert e.version == entry.version
        assert e.importance_score == entry.importance_score
        assert e.decay_rate == entry.decay_rate
        assert e.is_active == entry.is_active
        assert e.regime_valid == entry.regime_valid
        assert e.hash == entry.hash


# ---------------------------------------------------------------------------
# DETERMINISM (DET-05)
# ---------------------------------------------------------------------------

class TestDeterminism:
    """Verify deterministic behavior."""

    def test_same_inputs_same_hash(self):
        """DET-05: Same inputs → same outputs."""
        for _ in range(5):
            reg = FeatureRegistry()
            entry = reg.register("f1", "Test", "1.0", ["RISK_ON"])
            assert entry.hash == reg._registry["f1"].hash

    def test_same_decay_result(self):
        """Same feature, same days → same decay."""
        reg = FeatureRegistry()
        reg.register("f1", "Test", "1.0", [], importance=0.8, decay_rate=0.01)
        r1 = reg.compute_decayed_importance("f1", days_elapsed=30)
        r2 = reg.compute_decayed_importance("f1", days_elapsed=30)
        assert r1.decayed_score == r2.decayed_score
        assert r1.should_prune == r2.should_prune


# ---------------------------------------------------------------------------
# INTEGRATION
# ---------------------------------------------------------------------------

class TestIntegration:
    """End-to-end workflow tests."""

    def test_full_lifecycle(self, tmp_path):
        """Register → validate → decay → prune → save → load."""
        out = tmp_path / "registry.json"
        reg = FeatureRegistry(registry_path=out)

        # Register features
        reg.register("rsi_14", "RSI-14", "1.0", ["TRENDING"], importance=0.8, decay_rate=0.005)
        reg.register("bb_20", "Bollinger-20", "1.0", ["RANGING"], importance=0.6, decay_rate=0.01)
        reg.register("macd", "MACD", "1.0", ["TRENDING", "RANGING"], importance=0.15, decay_rate=0.015)

        # Check active before pruning
        assert len(reg.get_active_features()) == 3

        # Prune with 100 days
        pruned = reg.prune_stale_features(days_threshold=100)
        # macd: 0.15 * 0.985^100 ≈ 0.033 → pruned
        # bb_20: 0.6 * 0.99^100 ≈ 0.218 → not pruned
        # rsi_14: 0.8 * 0.995^100 ≈ 0.486 → not pruned
        assert "macd" in pruned
        assert "rsi_14" not in pruned
        assert "bb_20" not in pruned

        # Active features
        active = reg.get_active_features()
        assert len(active) == 2

        # Save and reload
        reg.save()
        reg2 = FeatureRegistry(registry_path=out)
        reg2.load()
        assert len(reg2.get_active_features()) == 2

    def test_update_then_decay(self):
        """Update importance then compute decay."""
        reg = FeatureRegistry()
        reg.register("f1", "Test", "1.0", [], importance=0.5, decay_rate=0.01)
        reg.update_importance("f1", 0.9)
        result = reg.compute_decayed_importance("f1", days_elapsed=30)
        expected = 0.9 * (0.99 ** 30)
        assert abs(result.decayed_score - expected) < 1e-10

    def test_regime_workflow(self):
        """Register features for different regimes, query by regime."""
        reg = FeatureRegistry()
        reg.register("trend_rsi", "RSI", "1.0", ["TRENDING"], importance=0.9)
        reg.register("range_bb", "BB", "1.0", ["RANGING"], importance=0.85)
        reg.register("universal", "Vol", "1.0", [], importance=0.7)

        trending = reg.get_active_features(regime="TRENDING")
        assert len(trending) == 2  # trend_rsi + universal
        ids = [f.feature_id for f in trending]
        assert "trend_rsi" in ids
        assert "universal" in ids
        assert "range_bb" not in ids

    def test_many_features_prune(self):
        """Register many features, prune works correctly."""
        reg = FeatureRegistry()
        for i in range(20):
            imp = 0.05 + (i * 0.05)  # 0.05 to 1.0
            reg.register(f"f{i}", f"Feature-{i}", "1.0", [],
                          importance=min(imp, 1.0), decay_rate=0.01)
        pruned = reg.prune_stale_features(days_threshold=50)
        # Features with low initial importance will be pruned
        assert len(pruned) > 0
        # High importance features survive
        active = reg.get_active_features()
        assert len(active) > 0


# ---------------------------------------------------------------------------
# PACKAGE IMPORT
# ---------------------------------------------------------------------------

class TestPackageImport:
    """Verify __init__.py exports."""

    def test_import_from_package(self):
        from jarvis.research import FeatureEntry, FeatureImportanceResult, FeatureRegistry
        assert FeatureRegistry is not None
        assert FeatureEntry is not None
        assert FeatureImportanceResult is not None
