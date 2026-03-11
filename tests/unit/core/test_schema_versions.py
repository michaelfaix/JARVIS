# =============================================================================
# tests/unit/core/test_schema_versions.py
# Tests for jarvis/core/schema_versions.py
# =============================================================================

import pytest

from jarvis.core.schema_versions import (
    GLOBAL_STATE_VERSION,
    STRATEGY_OBJECT_VERSION,
    CONFIDENCE_BUNDLE_VERSION,
    EVENT_LOG_VERSION,
    CHECKPOINT_VERSION,
    ALL_VERSIONS,
)


# =============================================================================
# SECTION 1 -- VERSION VALUES
# =============================================================================

class TestVersionValues:
    """Test that all version constants have correct values."""

    def test_global_state_version(self):
        assert GLOBAL_STATE_VERSION == "1.0.0"

    def test_strategy_object_version(self):
        assert STRATEGY_OBJECT_VERSION == "1.0.0"

    def test_confidence_bundle_version(self):
        assert CONFIDENCE_BUNDLE_VERSION == "1.0.0"

    def test_event_log_version(self):
        assert EVENT_LOG_VERSION == "1.0.0"

    def test_checkpoint_version(self):
        assert CHECKPOINT_VERSION == "1.0.0"


# =============================================================================
# SECTION 2 -- TYPES
# =============================================================================

class TestVersionTypes:
    """Test that all version constants are strings."""

    def test_global_state_version_is_str(self):
        assert isinstance(GLOBAL_STATE_VERSION, str)

    def test_strategy_object_version_is_str(self):
        assert isinstance(STRATEGY_OBJECT_VERSION, str)

    def test_confidence_bundle_version_is_str(self):
        assert isinstance(CONFIDENCE_BUNDLE_VERSION, str)

    def test_event_log_version_is_str(self):
        assert isinstance(EVENT_LOG_VERSION, str)

    def test_checkpoint_version_is_str(self):
        assert isinstance(CHECKPOINT_VERSION, str)


# =============================================================================
# SECTION 3 -- SEMVER FORMAT
# =============================================================================

class TestSemVerFormat:
    """Test that all versions follow semantic versioning (MAJOR.MINOR.PATCH)."""

    @pytest.mark.parametrize("version", [
        GLOBAL_STATE_VERSION,
        STRATEGY_OBJECT_VERSION,
        CONFIDENCE_BUNDLE_VERSION,
        EVENT_LOG_VERSION,
        CHECKPOINT_VERSION,
    ])
    def test_semver_format(self, version):
        parts = version.split(".")
        assert len(parts) == 3, f"Expected 3 parts, got {len(parts)}"
        for part in parts:
            assert part.isdigit(), f"Part {part!r} is not a digit"


# =============================================================================
# SECTION 4 -- ALL_VERSIONS DICT
# =============================================================================

class TestAllVersions:
    """Test the ALL_VERSIONS introspection dict."""

    def test_is_dict(self):
        assert isinstance(ALL_VERSIONS, dict)

    def test_contains_all_five_versions(self):
        expected_keys = {
            "GLOBAL_STATE_VERSION",
            "STRATEGY_OBJECT_VERSION",
            "CONFIDENCE_BUNDLE_VERSION",
            "EVENT_LOG_VERSION",
            "CHECKPOINT_VERSION",
        }
        assert set(ALL_VERSIONS.keys()) == expected_keys

    def test_count(self):
        assert len(ALL_VERSIONS) == 5

    def test_values_match_constants(self):
        assert ALL_VERSIONS["GLOBAL_STATE_VERSION"] == GLOBAL_STATE_VERSION
        assert ALL_VERSIONS["STRATEGY_OBJECT_VERSION"] == STRATEGY_OBJECT_VERSION
        assert ALL_VERSIONS["CONFIDENCE_BUNDLE_VERSION"] == CONFIDENCE_BUNDLE_VERSION
        assert ALL_VERSIONS["EVENT_LOG_VERSION"] == EVENT_LOG_VERSION
        assert ALL_VERSIONS["CHECKPOINT_VERSION"] == CHECKPOINT_VERSION

    def test_all_values_are_strings(self):
        for key, val in ALL_VERSIONS.items():
            assert isinstance(val, str), f"{key} value is not a string"


# =============================================================================
# SECTION 5 -- CROSS-REFERENCE INVARIANTS
# =============================================================================

class TestCrossReferences:
    """Test FAS cross-reference invariants."""

    def test_strategy_schema_consistency(self):
        """STRATEGY_OBJECT_VERSION must equal STRATEGY_SCHEMA_VERSION (FAS)."""
        # In this codebase, STRATEGY_OBJECT_VERSION IS the canonical source.
        # This test documents the invariant.
        assert STRATEGY_OBJECT_VERSION == "1.0.0"

    def test_checkpoint_imports_match(self):
        """state_checkpoint.py should use versions from schema_versions.py."""
        from jarvis.core.state_checkpoint import (
            CHECKPOINT_SCHEMA_VERSION,
            GLOBAL_STATE_VERSION as CP_GSV,
            STRATEGY_OBJECT_VERSION as CP_SOV,
            CONFIDENCE_BUNDLE_VERSION as CP_CBV,
        )
        assert CHECKPOINT_SCHEMA_VERSION == CHECKPOINT_VERSION
        assert CP_GSV == GLOBAL_STATE_VERSION
        assert CP_SOV == STRATEGY_OBJECT_VERSION
        assert CP_CBV == CONFIDENCE_BUNDLE_VERSION


# =============================================================================
# SECTION 6 -- DETERMINISM
# =============================================================================

class TestDeterminism:
    """Test deterministic behavior (DET-07)."""

    def test_versions_are_stable(self):
        """Repeated access returns identical values."""
        for _ in range(10):
            assert GLOBAL_STATE_VERSION == "1.0.0"
            assert EVENT_LOG_VERSION == "1.0.0"
            assert CHECKPOINT_VERSION == "1.0.0"
