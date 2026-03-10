# jarvis/verification/manifest_validator.py
# ManifestValidator -- first component executed in the harness pipeline.
# Authority: DVH Implementation Blueprint v1.0.0 Section 12.
#
# NIC-03: This module does not modify any constant. Constants are read from
#         their authoritative source for comparison purposes only.
# No pipeline stage begins until ManifestValidator completes successfully.

import hashlib
import json
import struct
from pathlib import Path
from typing import Tuple, Dict, Any
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


class ManifestValidator:
    """
    Validates THRESHOLD_MANIFEST.json before any Risk Engine invocation.

    Implements MVI-01 through MVI-06 from DVH Implementation Blueprint Section 12.

    On any failure: raises RuntimeError with failure_type_id as the first word
    of the message. Caller (run_harness.py) converts to FailureRecord and exits.
    """

    # FAS v6.1.0 declared constant values (MVI-04).
    # Verified by struct-based bit pattern comparison.
    _EXPECTED_SHOCK_EXPOSURE_CAP:      float = 0.25
    _EXPECTED_MAX_DRAWDOWN_THRESHOLD:  float = 0.15
    _EXPECTED_VOL_COMPRESSION_TRIGGER: float = 0.30

    def __init__(self, manifest_path: Path):
        args = [manifest_path]# type: ignore
        kwargs = {}# type: ignore
        return _mutmut_trampoline(object.__getattribute__(self, 'xǁManifestValidatorǁ__init____mutmut_orig'), object.__getattribute__(self, 'xǁManifestValidatorǁ__init____mutmut_mutants'), args, kwargs, self)

    def xǁManifestValidatorǁ__init____mutmut_orig(self, manifest_path: Path):
        self.manifest_path = manifest_path

    def xǁManifestValidatorǁ__init____mutmut_1(self, manifest_path: Path):
        self.manifest_path = None
    
    xǁManifestValidatorǁ__init____mutmut_mutants : ClassVar[MutantDict] = { # type: ignore
    'xǁManifestValidatorǁ__init____mutmut_1': xǁManifestValidatorǁ__init____mutmut_1
    }
    xǁManifestValidatorǁ__init____mutmut_orig.__name__ = 'xǁManifestValidatorǁ__init__'

    @staticmethod
    def _float_bits(value: float) -> bytes:
        """Return 8-byte big-endian IEEE 754 representation."""
        return struct.pack(">d", value)

    @staticmethod
    def _floats_equal(a: float, b: float) -> bool:
        """
        Exact bit-pattern equality for floats.
        Distinguishes +0.0 from -0.0.
        """
        return struct.pack(">d", a) == struct.pack(">d", b)

    def validate(self) -> Tuple[str, Dict[str, Any]]:
        args = []# type: ignore
        kwargs = {}# type: ignore
        return _mutmut_trampoline(object.__getattribute__(self, 'xǁManifestValidatorǁvalidate__mutmut_orig'), object.__getattribute__(self, 'xǁManifestValidatorǁvalidate__mutmut_mutants'), args, kwargs, self)

    def xǁManifestValidatorǁvalidate__mutmut_orig(self) -> Tuple[str, Dict[str, Any]]:
        """
        Execute full manifest validation.

        Returns:
          (computed_hash, thresholds_dict)
          computed_hash -- SHA-256 hex digest of the manifest content.
          thresholds    -- dict from manifest["thresholds"] section.

        Raises RuntimeError with failure_type_id prefix on any hard failure.
        Failure types raised here:
          MANIFEST_HASH_MISMATCH    -- MVI-02
          MANIFEST_CONSTANT_MISMATCH -- MVI-04
          MANIFEST_TABLEHASH_PRESENT -- MVI-05
          INTEGRITY_FAILURE          -- missing file or parse error
        """
        # MVI-01: Load manifest file.
        if not self.manifest_path.exists():
            raise RuntimeError(
                "INTEGRITY_FAILURE: THRESHOLD_MANIFEST.json not found at "
                f"{self.manifest_path}. Harness cannot start without manifest."
            )

        try:
            with open(self.manifest_path, "r", encoding="utf-8") as f:
                raw = f.read()
            data = json.loads(raw)
        except Exception as exc:
            raise RuntimeError(
                f"INTEGRITY_FAILURE: Failed to load or parse THRESHOLD_MANIFEST.json: {exc}"
            ) from exc

        # MVI-01: Compute hash excluding manifest_hash field.
        data_for_hash = {k: v for k, v in data.items() if k != "manifest_hash"}
        computed_hash = hashlib.sha256(
            json.dumps(data_for_hash, sort_keys=True, separators=(",", ":")).encode("utf-8")
        ).hexdigest()

        # MVI-02: Verify computed hash matches stored manifest_hash.
        stored_hash = data.get("manifest_hash", "")
        if (
            stored_hash
            and stored_hash != "BUILD_TIME_PLACEHOLDER"
            and stored_hash != computed_hash
        ):
            raise RuntimeError(
                f"MANIFEST_HASH_MISMATCH: Computed hash {computed_hash[:16]}... "
                f"does not match stored hash {stored_hash[:16]}... "
                "System start denied. Possible tampering."
            )

        # MVI-05: Check for absence of table_hash in joint_risk_multiplier_table.
        jrmt = data.get("joint_risk_multiplier_table", {})
        if "table_hash" in jrmt:
            raise RuntimeError(
                "MANIFEST_TABLEHASH_PRESENT: joint_risk_multiplier_table must not "
                "contain a table_hash key per Manifest Authority Policy."
            )

        # MVI-03: Extract the three FAS v6.1.0 constants.
        try:
            thresholds = data["thresholds"]
            shock_cap  = float(thresholds["shock_exposure_cap"])
            max_dd     = float(thresholds["max_drawdown_threshold"])
            vol_trig   = float(thresholds["vol_compression_trigger"])
        except (KeyError, ValueError) as exc:
            raise RuntimeError(
                f"INTEGRITY_FAILURE: Missing or invalid threshold key in manifest: {exc}"
            ) from exc

        # MVI-04: Verify the three extracted constants equal FAS v6.1.0 values.
        if not self._floats_equal(shock_cap, self._EXPECTED_SHOCK_EXPOSURE_CAP):
            raise RuntimeError(
                f"MANIFEST_CONSTANT_MISMATCH: shock_exposure_cap={shock_cap} "
                f"expected {self._EXPECTED_SHOCK_EXPOSURE_CAP}."
            )
        if not self._floats_equal(max_dd, self._EXPECTED_MAX_DRAWDOWN_THRESHOLD):
            raise RuntimeError(
                f"MANIFEST_CONSTANT_MISMATCH: max_drawdown_threshold={max_dd} "
                f"expected {self._EXPECTED_MAX_DRAWDOWN_THRESHOLD}."
            )
        if not self._floats_equal(vol_trig, self._EXPECTED_VOL_COMPRESSION_TRIGGER):
            raise RuntimeError(
                f"MANIFEST_CONSTANT_MISMATCH: vol_compression_trigger={vol_trig} "
                f"expected {self._EXPECTED_VOL_COMPRESSION_TRIGGER}."
            )

        # MVI-06: Return computed hash for propagation into ExecutionRecords.
        return computed_hash, thresholds

    def xǁManifestValidatorǁvalidate__mutmut_1(self) -> Tuple[str, Dict[str, Any]]:
        """
        Execute full manifest validation.

        Returns:
          (computed_hash, thresholds_dict)
          computed_hash -- SHA-256 hex digest of the manifest content.
          thresholds    -- dict from manifest["thresholds"] section.

        Raises RuntimeError with failure_type_id prefix on any hard failure.
        Failure types raised here:
          MANIFEST_HASH_MISMATCH    -- MVI-02
          MANIFEST_CONSTANT_MISMATCH -- MVI-04
          MANIFEST_TABLEHASH_PRESENT -- MVI-05
          INTEGRITY_FAILURE          -- missing file or parse error
        """
        # MVI-01: Load manifest file.
        if self.manifest_path.exists():
            raise RuntimeError(
                "INTEGRITY_FAILURE: THRESHOLD_MANIFEST.json not found at "
                f"{self.manifest_path}. Harness cannot start without manifest."
            )

        try:
            with open(self.manifest_path, "r", encoding="utf-8") as f:
                raw = f.read()
            data = json.loads(raw)
        except Exception as exc:
            raise RuntimeError(
                f"INTEGRITY_FAILURE: Failed to load or parse THRESHOLD_MANIFEST.json: {exc}"
            ) from exc

        # MVI-01: Compute hash excluding manifest_hash field.
        data_for_hash = {k: v for k, v in data.items() if k != "manifest_hash"}
        computed_hash = hashlib.sha256(
            json.dumps(data_for_hash, sort_keys=True, separators=(",", ":")).encode("utf-8")
        ).hexdigest()

        # MVI-02: Verify computed hash matches stored manifest_hash.
        stored_hash = data.get("manifest_hash", "")
        if (
            stored_hash
            and stored_hash != "BUILD_TIME_PLACEHOLDER"
            and stored_hash != computed_hash
        ):
            raise RuntimeError(
                f"MANIFEST_HASH_MISMATCH: Computed hash {computed_hash[:16]}... "
                f"does not match stored hash {stored_hash[:16]}... "
                "System start denied. Possible tampering."
            )

        # MVI-05: Check for absence of table_hash in joint_risk_multiplier_table.
        jrmt = data.get("joint_risk_multiplier_table", {})
        if "table_hash" in jrmt:
            raise RuntimeError(
                "MANIFEST_TABLEHASH_PRESENT: joint_risk_multiplier_table must not "
                "contain a table_hash key per Manifest Authority Policy."
            )

        # MVI-03: Extract the three FAS v6.1.0 constants.
        try:
            thresholds = data["thresholds"]
            shock_cap  = float(thresholds["shock_exposure_cap"])
            max_dd     = float(thresholds["max_drawdown_threshold"])
            vol_trig   = float(thresholds["vol_compression_trigger"])
        except (KeyError, ValueError) as exc:
            raise RuntimeError(
                f"INTEGRITY_FAILURE: Missing or invalid threshold key in manifest: {exc}"
            ) from exc

        # MVI-04: Verify the three extracted constants equal FAS v6.1.0 values.
        if not self._floats_equal(shock_cap, self._EXPECTED_SHOCK_EXPOSURE_CAP):
            raise RuntimeError(
                f"MANIFEST_CONSTANT_MISMATCH: shock_exposure_cap={shock_cap} "
                f"expected {self._EXPECTED_SHOCK_EXPOSURE_CAP}."
            )
        if not self._floats_equal(max_dd, self._EXPECTED_MAX_DRAWDOWN_THRESHOLD):
            raise RuntimeError(
                f"MANIFEST_CONSTANT_MISMATCH: max_drawdown_threshold={max_dd} "
                f"expected {self._EXPECTED_MAX_DRAWDOWN_THRESHOLD}."
            )
        if not self._floats_equal(vol_trig, self._EXPECTED_VOL_COMPRESSION_TRIGGER):
            raise RuntimeError(
                f"MANIFEST_CONSTANT_MISMATCH: vol_compression_trigger={vol_trig} "
                f"expected {self._EXPECTED_VOL_COMPRESSION_TRIGGER}."
            )

        # MVI-06: Return computed hash for propagation into ExecutionRecords.
        return computed_hash, thresholds

    def xǁManifestValidatorǁvalidate__mutmut_2(self) -> Tuple[str, Dict[str, Any]]:
        """
        Execute full manifest validation.

        Returns:
          (computed_hash, thresholds_dict)
          computed_hash -- SHA-256 hex digest of the manifest content.
          thresholds    -- dict from manifest["thresholds"] section.

        Raises RuntimeError with failure_type_id prefix on any hard failure.
        Failure types raised here:
          MANIFEST_HASH_MISMATCH    -- MVI-02
          MANIFEST_CONSTANT_MISMATCH -- MVI-04
          MANIFEST_TABLEHASH_PRESENT -- MVI-05
          INTEGRITY_FAILURE          -- missing file or parse error
        """
        # MVI-01: Load manifest file.
        if not self.manifest_path.exists():
            raise RuntimeError(
                None
            )

        try:
            with open(self.manifest_path, "r", encoding="utf-8") as f:
                raw = f.read()
            data = json.loads(raw)
        except Exception as exc:
            raise RuntimeError(
                f"INTEGRITY_FAILURE: Failed to load or parse THRESHOLD_MANIFEST.json: {exc}"
            ) from exc

        # MVI-01: Compute hash excluding manifest_hash field.
        data_for_hash = {k: v for k, v in data.items() if k != "manifest_hash"}
        computed_hash = hashlib.sha256(
            json.dumps(data_for_hash, sort_keys=True, separators=(",", ":")).encode("utf-8")
        ).hexdigest()

        # MVI-02: Verify computed hash matches stored manifest_hash.
        stored_hash = data.get("manifest_hash", "")
        if (
            stored_hash
            and stored_hash != "BUILD_TIME_PLACEHOLDER"
            and stored_hash != computed_hash
        ):
            raise RuntimeError(
                f"MANIFEST_HASH_MISMATCH: Computed hash {computed_hash[:16]}... "
                f"does not match stored hash {stored_hash[:16]}... "
                "System start denied. Possible tampering."
            )

        # MVI-05: Check for absence of table_hash in joint_risk_multiplier_table.
        jrmt = data.get("joint_risk_multiplier_table", {})
        if "table_hash" in jrmt:
            raise RuntimeError(
                "MANIFEST_TABLEHASH_PRESENT: joint_risk_multiplier_table must not "
                "contain a table_hash key per Manifest Authority Policy."
            )

        # MVI-03: Extract the three FAS v6.1.0 constants.
        try:
            thresholds = data["thresholds"]
            shock_cap  = float(thresholds["shock_exposure_cap"])
            max_dd     = float(thresholds["max_drawdown_threshold"])
            vol_trig   = float(thresholds["vol_compression_trigger"])
        except (KeyError, ValueError) as exc:
            raise RuntimeError(
                f"INTEGRITY_FAILURE: Missing or invalid threshold key in manifest: {exc}"
            ) from exc

        # MVI-04: Verify the three extracted constants equal FAS v6.1.0 values.
        if not self._floats_equal(shock_cap, self._EXPECTED_SHOCK_EXPOSURE_CAP):
            raise RuntimeError(
                f"MANIFEST_CONSTANT_MISMATCH: shock_exposure_cap={shock_cap} "
                f"expected {self._EXPECTED_SHOCK_EXPOSURE_CAP}."
            )
        if not self._floats_equal(max_dd, self._EXPECTED_MAX_DRAWDOWN_THRESHOLD):
            raise RuntimeError(
                f"MANIFEST_CONSTANT_MISMATCH: max_drawdown_threshold={max_dd} "
                f"expected {self._EXPECTED_MAX_DRAWDOWN_THRESHOLD}."
            )
        if not self._floats_equal(vol_trig, self._EXPECTED_VOL_COMPRESSION_TRIGGER):
            raise RuntimeError(
                f"MANIFEST_CONSTANT_MISMATCH: vol_compression_trigger={vol_trig} "
                f"expected {self._EXPECTED_VOL_COMPRESSION_TRIGGER}."
            )

        # MVI-06: Return computed hash for propagation into ExecutionRecords.
        return computed_hash, thresholds

    def xǁManifestValidatorǁvalidate__mutmut_3(self) -> Tuple[str, Dict[str, Any]]:
        """
        Execute full manifest validation.

        Returns:
          (computed_hash, thresholds_dict)
          computed_hash -- SHA-256 hex digest of the manifest content.
          thresholds    -- dict from manifest["thresholds"] section.

        Raises RuntimeError with failure_type_id prefix on any hard failure.
        Failure types raised here:
          MANIFEST_HASH_MISMATCH    -- MVI-02
          MANIFEST_CONSTANT_MISMATCH -- MVI-04
          MANIFEST_TABLEHASH_PRESENT -- MVI-05
          INTEGRITY_FAILURE          -- missing file or parse error
        """
        # MVI-01: Load manifest file.
        if not self.manifest_path.exists():
            raise RuntimeError(
                "XXINTEGRITY_FAILURE: THRESHOLD_MANIFEST.json not found at XX"
                f"{self.manifest_path}. Harness cannot start without manifest."
            )

        try:
            with open(self.manifest_path, "r", encoding="utf-8") as f:
                raw = f.read()
            data = json.loads(raw)
        except Exception as exc:
            raise RuntimeError(
                f"INTEGRITY_FAILURE: Failed to load or parse THRESHOLD_MANIFEST.json: {exc}"
            ) from exc

        # MVI-01: Compute hash excluding manifest_hash field.
        data_for_hash = {k: v for k, v in data.items() if k != "manifest_hash"}
        computed_hash = hashlib.sha256(
            json.dumps(data_for_hash, sort_keys=True, separators=(",", ":")).encode("utf-8")
        ).hexdigest()

        # MVI-02: Verify computed hash matches stored manifest_hash.
        stored_hash = data.get("manifest_hash", "")
        if (
            stored_hash
            and stored_hash != "BUILD_TIME_PLACEHOLDER"
            and stored_hash != computed_hash
        ):
            raise RuntimeError(
                f"MANIFEST_HASH_MISMATCH: Computed hash {computed_hash[:16]}... "
                f"does not match stored hash {stored_hash[:16]}... "
                "System start denied. Possible tampering."
            )

        # MVI-05: Check for absence of table_hash in joint_risk_multiplier_table.
        jrmt = data.get("joint_risk_multiplier_table", {})
        if "table_hash" in jrmt:
            raise RuntimeError(
                "MANIFEST_TABLEHASH_PRESENT: joint_risk_multiplier_table must not "
                "contain a table_hash key per Manifest Authority Policy."
            )

        # MVI-03: Extract the three FAS v6.1.0 constants.
        try:
            thresholds = data["thresholds"]
            shock_cap  = float(thresholds["shock_exposure_cap"])
            max_dd     = float(thresholds["max_drawdown_threshold"])
            vol_trig   = float(thresholds["vol_compression_trigger"])
        except (KeyError, ValueError) as exc:
            raise RuntimeError(
                f"INTEGRITY_FAILURE: Missing or invalid threshold key in manifest: {exc}"
            ) from exc

        # MVI-04: Verify the three extracted constants equal FAS v6.1.0 values.
        if not self._floats_equal(shock_cap, self._EXPECTED_SHOCK_EXPOSURE_CAP):
            raise RuntimeError(
                f"MANIFEST_CONSTANT_MISMATCH: shock_exposure_cap={shock_cap} "
                f"expected {self._EXPECTED_SHOCK_EXPOSURE_CAP}."
            )
        if not self._floats_equal(max_dd, self._EXPECTED_MAX_DRAWDOWN_THRESHOLD):
            raise RuntimeError(
                f"MANIFEST_CONSTANT_MISMATCH: max_drawdown_threshold={max_dd} "
                f"expected {self._EXPECTED_MAX_DRAWDOWN_THRESHOLD}."
            )
        if not self._floats_equal(vol_trig, self._EXPECTED_VOL_COMPRESSION_TRIGGER):
            raise RuntimeError(
                f"MANIFEST_CONSTANT_MISMATCH: vol_compression_trigger={vol_trig} "
                f"expected {self._EXPECTED_VOL_COMPRESSION_TRIGGER}."
            )

        # MVI-06: Return computed hash for propagation into ExecutionRecords.
        return computed_hash, thresholds

    def xǁManifestValidatorǁvalidate__mutmut_4(self) -> Tuple[str, Dict[str, Any]]:
        """
        Execute full manifest validation.

        Returns:
          (computed_hash, thresholds_dict)
          computed_hash -- SHA-256 hex digest of the manifest content.
          thresholds    -- dict from manifest["thresholds"] section.

        Raises RuntimeError with failure_type_id prefix on any hard failure.
        Failure types raised here:
          MANIFEST_HASH_MISMATCH    -- MVI-02
          MANIFEST_CONSTANT_MISMATCH -- MVI-04
          MANIFEST_TABLEHASH_PRESENT -- MVI-05
          INTEGRITY_FAILURE          -- missing file or parse error
        """
        # MVI-01: Load manifest file.
        if not self.manifest_path.exists():
            raise RuntimeError(
                "integrity_failure: threshold_manifest.json not found at "
                f"{self.manifest_path}. Harness cannot start without manifest."
            )

        try:
            with open(self.manifest_path, "r", encoding="utf-8") as f:
                raw = f.read()
            data = json.loads(raw)
        except Exception as exc:
            raise RuntimeError(
                f"INTEGRITY_FAILURE: Failed to load or parse THRESHOLD_MANIFEST.json: {exc}"
            ) from exc

        # MVI-01: Compute hash excluding manifest_hash field.
        data_for_hash = {k: v for k, v in data.items() if k != "manifest_hash"}
        computed_hash = hashlib.sha256(
            json.dumps(data_for_hash, sort_keys=True, separators=(",", ":")).encode("utf-8")
        ).hexdigest()

        # MVI-02: Verify computed hash matches stored manifest_hash.
        stored_hash = data.get("manifest_hash", "")
        if (
            stored_hash
            and stored_hash != "BUILD_TIME_PLACEHOLDER"
            and stored_hash != computed_hash
        ):
            raise RuntimeError(
                f"MANIFEST_HASH_MISMATCH: Computed hash {computed_hash[:16]}... "
                f"does not match stored hash {stored_hash[:16]}... "
                "System start denied. Possible tampering."
            )

        # MVI-05: Check for absence of table_hash in joint_risk_multiplier_table.
        jrmt = data.get("joint_risk_multiplier_table", {})
        if "table_hash" in jrmt:
            raise RuntimeError(
                "MANIFEST_TABLEHASH_PRESENT: joint_risk_multiplier_table must not "
                "contain a table_hash key per Manifest Authority Policy."
            )

        # MVI-03: Extract the three FAS v6.1.0 constants.
        try:
            thresholds = data["thresholds"]
            shock_cap  = float(thresholds["shock_exposure_cap"])
            max_dd     = float(thresholds["max_drawdown_threshold"])
            vol_trig   = float(thresholds["vol_compression_trigger"])
        except (KeyError, ValueError) as exc:
            raise RuntimeError(
                f"INTEGRITY_FAILURE: Missing or invalid threshold key in manifest: {exc}"
            ) from exc

        # MVI-04: Verify the three extracted constants equal FAS v6.1.0 values.
        if not self._floats_equal(shock_cap, self._EXPECTED_SHOCK_EXPOSURE_CAP):
            raise RuntimeError(
                f"MANIFEST_CONSTANT_MISMATCH: shock_exposure_cap={shock_cap} "
                f"expected {self._EXPECTED_SHOCK_EXPOSURE_CAP}."
            )
        if not self._floats_equal(max_dd, self._EXPECTED_MAX_DRAWDOWN_THRESHOLD):
            raise RuntimeError(
                f"MANIFEST_CONSTANT_MISMATCH: max_drawdown_threshold={max_dd} "
                f"expected {self._EXPECTED_MAX_DRAWDOWN_THRESHOLD}."
            )
        if not self._floats_equal(vol_trig, self._EXPECTED_VOL_COMPRESSION_TRIGGER):
            raise RuntimeError(
                f"MANIFEST_CONSTANT_MISMATCH: vol_compression_trigger={vol_trig} "
                f"expected {self._EXPECTED_VOL_COMPRESSION_TRIGGER}."
            )

        # MVI-06: Return computed hash for propagation into ExecutionRecords.
        return computed_hash, thresholds

    def xǁManifestValidatorǁvalidate__mutmut_5(self) -> Tuple[str, Dict[str, Any]]:
        """
        Execute full manifest validation.

        Returns:
          (computed_hash, thresholds_dict)
          computed_hash -- SHA-256 hex digest of the manifest content.
          thresholds    -- dict from manifest["thresholds"] section.

        Raises RuntimeError with failure_type_id prefix on any hard failure.
        Failure types raised here:
          MANIFEST_HASH_MISMATCH    -- MVI-02
          MANIFEST_CONSTANT_MISMATCH -- MVI-04
          MANIFEST_TABLEHASH_PRESENT -- MVI-05
          INTEGRITY_FAILURE          -- missing file or parse error
        """
        # MVI-01: Load manifest file.
        if not self.manifest_path.exists():
            raise RuntimeError(
                "INTEGRITY_FAILURE: THRESHOLD_MANIFEST.JSON NOT FOUND AT "
                f"{self.manifest_path}. Harness cannot start without manifest."
            )

        try:
            with open(self.manifest_path, "r", encoding="utf-8") as f:
                raw = f.read()
            data = json.loads(raw)
        except Exception as exc:
            raise RuntimeError(
                f"INTEGRITY_FAILURE: Failed to load or parse THRESHOLD_MANIFEST.json: {exc}"
            ) from exc

        # MVI-01: Compute hash excluding manifest_hash field.
        data_for_hash = {k: v for k, v in data.items() if k != "manifest_hash"}
        computed_hash = hashlib.sha256(
            json.dumps(data_for_hash, sort_keys=True, separators=(",", ":")).encode("utf-8")
        ).hexdigest()

        # MVI-02: Verify computed hash matches stored manifest_hash.
        stored_hash = data.get("manifest_hash", "")
        if (
            stored_hash
            and stored_hash != "BUILD_TIME_PLACEHOLDER"
            and stored_hash != computed_hash
        ):
            raise RuntimeError(
                f"MANIFEST_HASH_MISMATCH: Computed hash {computed_hash[:16]}... "
                f"does not match stored hash {stored_hash[:16]}... "
                "System start denied. Possible tampering."
            )

        # MVI-05: Check for absence of table_hash in joint_risk_multiplier_table.
        jrmt = data.get("joint_risk_multiplier_table", {})
        if "table_hash" in jrmt:
            raise RuntimeError(
                "MANIFEST_TABLEHASH_PRESENT: joint_risk_multiplier_table must not "
                "contain a table_hash key per Manifest Authority Policy."
            )

        # MVI-03: Extract the three FAS v6.1.0 constants.
        try:
            thresholds = data["thresholds"]
            shock_cap  = float(thresholds["shock_exposure_cap"])
            max_dd     = float(thresholds["max_drawdown_threshold"])
            vol_trig   = float(thresholds["vol_compression_trigger"])
        except (KeyError, ValueError) as exc:
            raise RuntimeError(
                f"INTEGRITY_FAILURE: Missing or invalid threshold key in manifest: {exc}"
            ) from exc

        # MVI-04: Verify the three extracted constants equal FAS v6.1.0 values.
        if not self._floats_equal(shock_cap, self._EXPECTED_SHOCK_EXPOSURE_CAP):
            raise RuntimeError(
                f"MANIFEST_CONSTANT_MISMATCH: shock_exposure_cap={shock_cap} "
                f"expected {self._EXPECTED_SHOCK_EXPOSURE_CAP}."
            )
        if not self._floats_equal(max_dd, self._EXPECTED_MAX_DRAWDOWN_THRESHOLD):
            raise RuntimeError(
                f"MANIFEST_CONSTANT_MISMATCH: max_drawdown_threshold={max_dd} "
                f"expected {self._EXPECTED_MAX_DRAWDOWN_THRESHOLD}."
            )
        if not self._floats_equal(vol_trig, self._EXPECTED_VOL_COMPRESSION_TRIGGER):
            raise RuntimeError(
                f"MANIFEST_CONSTANT_MISMATCH: vol_compression_trigger={vol_trig} "
                f"expected {self._EXPECTED_VOL_COMPRESSION_TRIGGER}."
            )

        # MVI-06: Return computed hash for propagation into ExecutionRecords.
        return computed_hash, thresholds

    def xǁManifestValidatorǁvalidate__mutmut_6(self) -> Tuple[str, Dict[str, Any]]:
        """
        Execute full manifest validation.

        Returns:
          (computed_hash, thresholds_dict)
          computed_hash -- SHA-256 hex digest of the manifest content.
          thresholds    -- dict from manifest["thresholds"] section.

        Raises RuntimeError with failure_type_id prefix on any hard failure.
        Failure types raised here:
          MANIFEST_HASH_MISMATCH    -- MVI-02
          MANIFEST_CONSTANT_MISMATCH -- MVI-04
          MANIFEST_TABLEHASH_PRESENT -- MVI-05
          INTEGRITY_FAILURE          -- missing file or parse error
        """
        # MVI-01: Load manifest file.
        if not self.manifest_path.exists():
            raise RuntimeError(
                "INTEGRITY_FAILURE: THRESHOLD_MANIFEST.json not found at "
                f"{self.manifest_path}. Harness cannot start without manifest."
            )

        try:
            with open(None, "r", encoding="utf-8") as f:
                raw = f.read()
            data = json.loads(raw)
        except Exception as exc:
            raise RuntimeError(
                f"INTEGRITY_FAILURE: Failed to load or parse THRESHOLD_MANIFEST.json: {exc}"
            ) from exc

        # MVI-01: Compute hash excluding manifest_hash field.
        data_for_hash = {k: v for k, v in data.items() if k != "manifest_hash"}
        computed_hash = hashlib.sha256(
            json.dumps(data_for_hash, sort_keys=True, separators=(",", ":")).encode("utf-8")
        ).hexdigest()

        # MVI-02: Verify computed hash matches stored manifest_hash.
        stored_hash = data.get("manifest_hash", "")
        if (
            stored_hash
            and stored_hash != "BUILD_TIME_PLACEHOLDER"
            and stored_hash != computed_hash
        ):
            raise RuntimeError(
                f"MANIFEST_HASH_MISMATCH: Computed hash {computed_hash[:16]}... "
                f"does not match stored hash {stored_hash[:16]}... "
                "System start denied. Possible tampering."
            )

        # MVI-05: Check for absence of table_hash in joint_risk_multiplier_table.
        jrmt = data.get("joint_risk_multiplier_table", {})
        if "table_hash" in jrmt:
            raise RuntimeError(
                "MANIFEST_TABLEHASH_PRESENT: joint_risk_multiplier_table must not "
                "contain a table_hash key per Manifest Authority Policy."
            )

        # MVI-03: Extract the three FAS v6.1.0 constants.
        try:
            thresholds = data["thresholds"]
            shock_cap  = float(thresholds["shock_exposure_cap"])
            max_dd     = float(thresholds["max_drawdown_threshold"])
            vol_trig   = float(thresholds["vol_compression_trigger"])
        except (KeyError, ValueError) as exc:
            raise RuntimeError(
                f"INTEGRITY_FAILURE: Missing or invalid threshold key in manifest: {exc}"
            ) from exc

        # MVI-04: Verify the three extracted constants equal FAS v6.1.0 values.
        if not self._floats_equal(shock_cap, self._EXPECTED_SHOCK_EXPOSURE_CAP):
            raise RuntimeError(
                f"MANIFEST_CONSTANT_MISMATCH: shock_exposure_cap={shock_cap} "
                f"expected {self._EXPECTED_SHOCK_EXPOSURE_CAP}."
            )
        if not self._floats_equal(max_dd, self._EXPECTED_MAX_DRAWDOWN_THRESHOLD):
            raise RuntimeError(
                f"MANIFEST_CONSTANT_MISMATCH: max_drawdown_threshold={max_dd} "
                f"expected {self._EXPECTED_MAX_DRAWDOWN_THRESHOLD}."
            )
        if not self._floats_equal(vol_trig, self._EXPECTED_VOL_COMPRESSION_TRIGGER):
            raise RuntimeError(
                f"MANIFEST_CONSTANT_MISMATCH: vol_compression_trigger={vol_trig} "
                f"expected {self._EXPECTED_VOL_COMPRESSION_TRIGGER}."
            )

        # MVI-06: Return computed hash for propagation into ExecutionRecords.
        return computed_hash, thresholds

    def xǁManifestValidatorǁvalidate__mutmut_7(self) -> Tuple[str, Dict[str, Any]]:
        """
        Execute full manifest validation.

        Returns:
          (computed_hash, thresholds_dict)
          computed_hash -- SHA-256 hex digest of the manifest content.
          thresholds    -- dict from manifest["thresholds"] section.

        Raises RuntimeError with failure_type_id prefix on any hard failure.
        Failure types raised here:
          MANIFEST_HASH_MISMATCH    -- MVI-02
          MANIFEST_CONSTANT_MISMATCH -- MVI-04
          MANIFEST_TABLEHASH_PRESENT -- MVI-05
          INTEGRITY_FAILURE          -- missing file or parse error
        """
        # MVI-01: Load manifest file.
        if not self.manifest_path.exists():
            raise RuntimeError(
                "INTEGRITY_FAILURE: THRESHOLD_MANIFEST.json not found at "
                f"{self.manifest_path}. Harness cannot start without manifest."
            )

        try:
            with open(self.manifest_path, None, encoding="utf-8") as f:
                raw = f.read()
            data = json.loads(raw)
        except Exception as exc:
            raise RuntimeError(
                f"INTEGRITY_FAILURE: Failed to load or parse THRESHOLD_MANIFEST.json: {exc}"
            ) from exc

        # MVI-01: Compute hash excluding manifest_hash field.
        data_for_hash = {k: v for k, v in data.items() if k != "manifest_hash"}
        computed_hash = hashlib.sha256(
            json.dumps(data_for_hash, sort_keys=True, separators=(",", ":")).encode("utf-8")
        ).hexdigest()

        # MVI-02: Verify computed hash matches stored manifest_hash.
        stored_hash = data.get("manifest_hash", "")
        if (
            stored_hash
            and stored_hash != "BUILD_TIME_PLACEHOLDER"
            and stored_hash != computed_hash
        ):
            raise RuntimeError(
                f"MANIFEST_HASH_MISMATCH: Computed hash {computed_hash[:16]}... "
                f"does not match stored hash {stored_hash[:16]}... "
                "System start denied. Possible tampering."
            )

        # MVI-05: Check for absence of table_hash in joint_risk_multiplier_table.
        jrmt = data.get("joint_risk_multiplier_table", {})
        if "table_hash" in jrmt:
            raise RuntimeError(
                "MANIFEST_TABLEHASH_PRESENT: joint_risk_multiplier_table must not "
                "contain a table_hash key per Manifest Authority Policy."
            )

        # MVI-03: Extract the three FAS v6.1.0 constants.
        try:
            thresholds = data["thresholds"]
            shock_cap  = float(thresholds["shock_exposure_cap"])
            max_dd     = float(thresholds["max_drawdown_threshold"])
            vol_trig   = float(thresholds["vol_compression_trigger"])
        except (KeyError, ValueError) as exc:
            raise RuntimeError(
                f"INTEGRITY_FAILURE: Missing or invalid threshold key in manifest: {exc}"
            ) from exc

        # MVI-04: Verify the three extracted constants equal FAS v6.1.0 values.
        if not self._floats_equal(shock_cap, self._EXPECTED_SHOCK_EXPOSURE_CAP):
            raise RuntimeError(
                f"MANIFEST_CONSTANT_MISMATCH: shock_exposure_cap={shock_cap} "
                f"expected {self._EXPECTED_SHOCK_EXPOSURE_CAP}."
            )
        if not self._floats_equal(max_dd, self._EXPECTED_MAX_DRAWDOWN_THRESHOLD):
            raise RuntimeError(
                f"MANIFEST_CONSTANT_MISMATCH: max_drawdown_threshold={max_dd} "
                f"expected {self._EXPECTED_MAX_DRAWDOWN_THRESHOLD}."
            )
        if not self._floats_equal(vol_trig, self._EXPECTED_VOL_COMPRESSION_TRIGGER):
            raise RuntimeError(
                f"MANIFEST_CONSTANT_MISMATCH: vol_compression_trigger={vol_trig} "
                f"expected {self._EXPECTED_VOL_COMPRESSION_TRIGGER}."
            )

        # MVI-06: Return computed hash for propagation into ExecutionRecords.
        return computed_hash, thresholds

    def xǁManifestValidatorǁvalidate__mutmut_8(self) -> Tuple[str, Dict[str, Any]]:
        """
        Execute full manifest validation.

        Returns:
          (computed_hash, thresholds_dict)
          computed_hash -- SHA-256 hex digest of the manifest content.
          thresholds    -- dict from manifest["thresholds"] section.

        Raises RuntimeError with failure_type_id prefix on any hard failure.
        Failure types raised here:
          MANIFEST_HASH_MISMATCH    -- MVI-02
          MANIFEST_CONSTANT_MISMATCH -- MVI-04
          MANIFEST_TABLEHASH_PRESENT -- MVI-05
          INTEGRITY_FAILURE          -- missing file or parse error
        """
        # MVI-01: Load manifest file.
        if not self.manifest_path.exists():
            raise RuntimeError(
                "INTEGRITY_FAILURE: THRESHOLD_MANIFEST.json not found at "
                f"{self.manifest_path}. Harness cannot start without manifest."
            )

        try:
            with open(self.manifest_path, "r", encoding=None) as f:
                raw = f.read()
            data = json.loads(raw)
        except Exception as exc:
            raise RuntimeError(
                f"INTEGRITY_FAILURE: Failed to load or parse THRESHOLD_MANIFEST.json: {exc}"
            ) from exc

        # MVI-01: Compute hash excluding manifest_hash field.
        data_for_hash = {k: v for k, v in data.items() if k != "manifest_hash"}
        computed_hash = hashlib.sha256(
            json.dumps(data_for_hash, sort_keys=True, separators=(",", ":")).encode("utf-8")
        ).hexdigest()

        # MVI-02: Verify computed hash matches stored manifest_hash.
        stored_hash = data.get("manifest_hash", "")
        if (
            stored_hash
            and stored_hash != "BUILD_TIME_PLACEHOLDER"
            and stored_hash != computed_hash
        ):
            raise RuntimeError(
                f"MANIFEST_HASH_MISMATCH: Computed hash {computed_hash[:16]}... "
                f"does not match stored hash {stored_hash[:16]}... "
                "System start denied. Possible tampering."
            )

        # MVI-05: Check for absence of table_hash in joint_risk_multiplier_table.
        jrmt = data.get("joint_risk_multiplier_table", {})
        if "table_hash" in jrmt:
            raise RuntimeError(
                "MANIFEST_TABLEHASH_PRESENT: joint_risk_multiplier_table must not "
                "contain a table_hash key per Manifest Authority Policy."
            )

        # MVI-03: Extract the three FAS v6.1.0 constants.
        try:
            thresholds = data["thresholds"]
            shock_cap  = float(thresholds["shock_exposure_cap"])
            max_dd     = float(thresholds["max_drawdown_threshold"])
            vol_trig   = float(thresholds["vol_compression_trigger"])
        except (KeyError, ValueError) as exc:
            raise RuntimeError(
                f"INTEGRITY_FAILURE: Missing or invalid threshold key in manifest: {exc}"
            ) from exc

        # MVI-04: Verify the three extracted constants equal FAS v6.1.0 values.
        if not self._floats_equal(shock_cap, self._EXPECTED_SHOCK_EXPOSURE_CAP):
            raise RuntimeError(
                f"MANIFEST_CONSTANT_MISMATCH: shock_exposure_cap={shock_cap} "
                f"expected {self._EXPECTED_SHOCK_EXPOSURE_CAP}."
            )
        if not self._floats_equal(max_dd, self._EXPECTED_MAX_DRAWDOWN_THRESHOLD):
            raise RuntimeError(
                f"MANIFEST_CONSTANT_MISMATCH: max_drawdown_threshold={max_dd} "
                f"expected {self._EXPECTED_MAX_DRAWDOWN_THRESHOLD}."
            )
        if not self._floats_equal(vol_trig, self._EXPECTED_VOL_COMPRESSION_TRIGGER):
            raise RuntimeError(
                f"MANIFEST_CONSTANT_MISMATCH: vol_compression_trigger={vol_trig} "
                f"expected {self._EXPECTED_VOL_COMPRESSION_TRIGGER}."
            )

        # MVI-06: Return computed hash for propagation into ExecutionRecords.
        return computed_hash, thresholds

    def xǁManifestValidatorǁvalidate__mutmut_9(self) -> Tuple[str, Dict[str, Any]]:
        """
        Execute full manifest validation.

        Returns:
          (computed_hash, thresholds_dict)
          computed_hash -- SHA-256 hex digest of the manifest content.
          thresholds    -- dict from manifest["thresholds"] section.

        Raises RuntimeError with failure_type_id prefix on any hard failure.
        Failure types raised here:
          MANIFEST_HASH_MISMATCH    -- MVI-02
          MANIFEST_CONSTANT_MISMATCH -- MVI-04
          MANIFEST_TABLEHASH_PRESENT -- MVI-05
          INTEGRITY_FAILURE          -- missing file or parse error
        """
        # MVI-01: Load manifest file.
        if not self.manifest_path.exists():
            raise RuntimeError(
                "INTEGRITY_FAILURE: THRESHOLD_MANIFEST.json not found at "
                f"{self.manifest_path}. Harness cannot start without manifest."
            )

        try:
            with open("r", encoding="utf-8") as f:
                raw = f.read()
            data = json.loads(raw)
        except Exception as exc:
            raise RuntimeError(
                f"INTEGRITY_FAILURE: Failed to load or parse THRESHOLD_MANIFEST.json: {exc}"
            ) from exc

        # MVI-01: Compute hash excluding manifest_hash field.
        data_for_hash = {k: v for k, v in data.items() if k != "manifest_hash"}
        computed_hash = hashlib.sha256(
            json.dumps(data_for_hash, sort_keys=True, separators=(",", ":")).encode("utf-8")
        ).hexdigest()

        # MVI-02: Verify computed hash matches stored manifest_hash.
        stored_hash = data.get("manifest_hash", "")
        if (
            stored_hash
            and stored_hash != "BUILD_TIME_PLACEHOLDER"
            and stored_hash != computed_hash
        ):
            raise RuntimeError(
                f"MANIFEST_HASH_MISMATCH: Computed hash {computed_hash[:16]}... "
                f"does not match stored hash {stored_hash[:16]}... "
                "System start denied. Possible tampering."
            )

        # MVI-05: Check for absence of table_hash in joint_risk_multiplier_table.
        jrmt = data.get("joint_risk_multiplier_table", {})
        if "table_hash" in jrmt:
            raise RuntimeError(
                "MANIFEST_TABLEHASH_PRESENT: joint_risk_multiplier_table must not "
                "contain a table_hash key per Manifest Authority Policy."
            )

        # MVI-03: Extract the three FAS v6.1.0 constants.
        try:
            thresholds = data["thresholds"]
            shock_cap  = float(thresholds["shock_exposure_cap"])
            max_dd     = float(thresholds["max_drawdown_threshold"])
            vol_trig   = float(thresholds["vol_compression_trigger"])
        except (KeyError, ValueError) as exc:
            raise RuntimeError(
                f"INTEGRITY_FAILURE: Missing or invalid threshold key in manifest: {exc}"
            ) from exc

        # MVI-04: Verify the three extracted constants equal FAS v6.1.0 values.
        if not self._floats_equal(shock_cap, self._EXPECTED_SHOCK_EXPOSURE_CAP):
            raise RuntimeError(
                f"MANIFEST_CONSTANT_MISMATCH: shock_exposure_cap={shock_cap} "
                f"expected {self._EXPECTED_SHOCK_EXPOSURE_CAP}."
            )
        if not self._floats_equal(max_dd, self._EXPECTED_MAX_DRAWDOWN_THRESHOLD):
            raise RuntimeError(
                f"MANIFEST_CONSTANT_MISMATCH: max_drawdown_threshold={max_dd} "
                f"expected {self._EXPECTED_MAX_DRAWDOWN_THRESHOLD}."
            )
        if not self._floats_equal(vol_trig, self._EXPECTED_VOL_COMPRESSION_TRIGGER):
            raise RuntimeError(
                f"MANIFEST_CONSTANT_MISMATCH: vol_compression_trigger={vol_trig} "
                f"expected {self._EXPECTED_VOL_COMPRESSION_TRIGGER}."
            )

        # MVI-06: Return computed hash for propagation into ExecutionRecords.
        return computed_hash, thresholds

    def xǁManifestValidatorǁvalidate__mutmut_10(self) -> Tuple[str, Dict[str, Any]]:
        """
        Execute full manifest validation.

        Returns:
          (computed_hash, thresholds_dict)
          computed_hash -- SHA-256 hex digest of the manifest content.
          thresholds    -- dict from manifest["thresholds"] section.

        Raises RuntimeError with failure_type_id prefix on any hard failure.
        Failure types raised here:
          MANIFEST_HASH_MISMATCH    -- MVI-02
          MANIFEST_CONSTANT_MISMATCH -- MVI-04
          MANIFEST_TABLEHASH_PRESENT -- MVI-05
          INTEGRITY_FAILURE          -- missing file or parse error
        """
        # MVI-01: Load manifest file.
        if not self.manifest_path.exists():
            raise RuntimeError(
                "INTEGRITY_FAILURE: THRESHOLD_MANIFEST.json not found at "
                f"{self.manifest_path}. Harness cannot start without manifest."
            )

        try:
            with open(self.manifest_path, encoding="utf-8") as f:
                raw = f.read()
            data = json.loads(raw)
        except Exception as exc:
            raise RuntimeError(
                f"INTEGRITY_FAILURE: Failed to load or parse THRESHOLD_MANIFEST.json: {exc}"
            ) from exc

        # MVI-01: Compute hash excluding manifest_hash field.
        data_for_hash = {k: v for k, v in data.items() if k != "manifest_hash"}
        computed_hash = hashlib.sha256(
            json.dumps(data_for_hash, sort_keys=True, separators=(",", ":")).encode("utf-8")
        ).hexdigest()

        # MVI-02: Verify computed hash matches stored manifest_hash.
        stored_hash = data.get("manifest_hash", "")
        if (
            stored_hash
            and stored_hash != "BUILD_TIME_PLACEHOLDER"
            and stored_hash != computed_hash
        ):
            raise RuntimeError(
                f"MANIFEST_HASH_MISMATCH: Computed hash {computed_hash[:16]}... "
                f"does not match stored hash {stored_hash[:16]}... "
                "System start denied. Possible tampering."
            )

        # MVI-05: Check for absence of table_hash in joint_risk_multiplier_table.
        jrmt = data.get("joint_risk_multiplier_table", {})
        if "table_hash" in jrmt:
            raise RuntimeError(
                "MANIFEST_TABLEHASH_PRESENT: joint_risk_multiplier_table must not "
                "contain a table_hash key per Manifest Authority Policy."
            )

        # MVI-03: Extract the three FAS v6.1.0 constants.
        try:
            thresholds = data["thresholds"]
            shock_cap  = float(thresholds["shock_exposure_cap"])
            max_dd     = float(thresholds["max_drawdown_threshold"])
            vol_trig   = float(thresholds["vol_compression_trigger"])
        except (KeyError, ValueError) as exc:
            raise RuntimeError(
                f"INTEGRITY_FAILURE: Missing or invalid threshold key in manifest: {exc}"
            ) from exc

        # MVI-04: Verify the three extracted constants equal FAS v6.1.0 values.
        if not self._floats_equal(shock_cap, self._EXPECTED_SHOCK_EXPOSURE_CAP):
            raise RuntimeError(
                f"MANIFEST_CONSTANT_MISMATCH: shock_exposure_cap={shock_cap} "
                f"expected {self._EXPECTED_SHOCK_EXPOSURE_CAP}."
            )
        if not self._floats_equal(max_dd, self._EXPECTED_MAX_DRAWDOWN_THRESHOLD):
            raise RuntimeError(
                f"MANIFEST_CONSTANT_MISMATCH: max_drawdown_threshold={max_dd} "
                f"expected {self._EXPECTED_MAX_DRAWDOWN_THRESHOLD}."
            )
        if not self._floats_equal(vol_trig, self._EXPECTED_VOL_COMPRESSION_TRIGGER):
            raise RuntimeError(
                f"MANIFEST_CONSTANT_MISMATCH: vol_compression_trigger={vol_trig} "
                f"expected {self._EXPECTED_VOL_COMPRESSION_TRIGGER}."
            )

        # MVI-06: Return computed hash for propagation into ExecutionRecords.
        return computed_hash, thresholds

    def xǁManifestValidatorǁvalidate__mutmut_11(self) -> Tuple[str, Dict[str, Any]]:
        """
        Execute full manifest validation.

        Returns:
          (computed_hash, thresholds_dict)
          computed_hash -- SHA-256 hex digest of the manifest content.
          thresholds    -- dict from manifest["thresholds"] section.

        Raises RuntimeError with failure_type_id prefix on any hard failure.
        Failure types raised here:
          MANIFEST_HASH_MISMATCH    -- MVI-02
          MANIFEST_CONSTANT_MISMATCH -- MVI-04
          MANIFEST_TABLEHASH_PRESENT -- MVI-05
          INTEGRITY_FAILURE          -- missing file or parse error
        """
        # MVI-01: Load manifest file.
        if not self.manifest_path.exists():
            raise RuntimeError(
                "INTEGRITY_FAILURE: THRESHOLD_MANIFEST.json not found at "
                f"{self.manifest_path}. Harness cannot start without manifest."
            )

        try:
            with open(self.manifest_path, "r", ) as f:
                raw = f.read()
            data = json.loads(raw)
        except Exception as exc:
            raise RuntimeError(
                f"INTEGRITY_FAILURE: Failed to load or parse THRESHOLD_MANIFEST.json: {exc}"
            ) from exc

        # MVI-01: Compute hash excluding manifest_hash field.
        data_for_hash = {k: v for k, v in data.items() if k != "manifest_hash"}
        computed_hash = hashlib.sha256(
            json.dumps(data_for_hash, sort_keys=True, separators=(",", ":")).encode("utf-8")
        ).hexdigest()

        # MVI-02: Verify computed hash matches stored manifest_hash.
        stored_hash = data.get("manifest_hash", "")
        if (
            stored_hash
            and stored_hash != "BUILD_TIME_PLACEHOLDER"
            and stored_hash != computed_hash
        ):
            raise RuntimeError(
                f"MANIFEST_HASH_MISMATCH: Computed hash {computed_hash[:16]}... "
                f"does not match stored hash {stored_hash[:16]}... "
                "System start denied. Possible tampering."
            )

        # MVI-05: Check for absence of table_hash in joint_risk_multiplier_table.
        jrmt = data.get("joint_risk_multiplier_table", {})
        if "table_hash" in jrmt:
            raise RuntimeError(
                "MANIFEST_TABLEHASH_PRESENT: joint_risk_multiplier_table must not "
                "contain a table_hash key per Manifest Authority Policy."
            )

        # MVI-03: Extract the three FAS v6.1.0 constants.
        try:
            thresholds = data["thresholds"]
            shock_cap  = float(thresholds["shock_exposure_cap"])
            max_dd     = float(thresholds["max_drawdown_threshold"])
            vol_trig   = float(thresholds["vol_compression_trigger"])
        except (KeyError, ValueError) as exc:
            raise RuntimeError(
                f"INTEGRITY_FAILURE: Missing or invalid threshold key in manifest: {exc}"
            ) from exc

        # MVI-04: Verify the three extracted constants equal FAS v6.1.0 values.
        if not self._floats_equal(shock_cap, self._EXPECTED_SHOCK_EXPOSURE_CAP):
            raise RuntimeError(
                f"MANIFEST_CONSTANT_MISMATCH: shock_exposure_cap={shock_cap} "
                f"expected {self._EXPECTED_SHOCK_EXPOSURE_CAP}."
            )
        if not self._floats_equal(max_dd, self._EXPECTED_MAX_DRAWDOWN_THRESHOLD):
            raise RuntimeError(
                f"MANIFEST_CONSTANT_MISMATCH: max_drawdown_threshold={max_dd} "
                f"expected {self._EXPECTED_MAX_DRAWDOWN_THRESHOLD}."
            )
        if not self._floats_equal(vol_trig, self._EXPECTED_VOL_COMPRESSION_TRIGGER):
            raise RuntimeError(
                f"MANIFEST_CONSTANT_MISMATCH: vol_compression_trigger={vol_trig} "
                f"expected {self._EXPECTED_VOL_COMPRESSION_TRIGGER}."
            )

        # MVI-06: Return computed hash for propagation into ExecutionRecords.
        return computed_hash, thresholds

    def xǁManifestValidatorǁvalidate__mutmut_12(self) -> Tuple[str, Dict[str, Any]]:
        """
        Execute full manifest validation.

        Returns:
          (computed_hash, thresholds_dict)
          computed_hash -- SHA-256 hex digest of the manifest content.
          thresholds    -- dict from manifest["thresholds"] section.

        Raises RuntimeError with failure_type_id prefix on any hard failure.
        Failure types raised here:
          MANIFEST_HASH_MISMATCH    -- MVI-02
          MANIFEST_CONSTANT_MISMATCH -- MVI-04
          MANIFEST_TABLEHASH_PRESENT -- MVI-05
          INTEGRITY_FAILURE          -- missing file or parse error
        """
        # MVI-01: Load manifest file.
        if not self.manifest_path.exists():
            raise RuntimeError(
                "INTEGRITY_FAILURE: THRESHOLD_MANIFEST.json not found at "
                f"{self.manifest_path}. Harness cannot start without manifest."
            )

        try:
            with open(self.manifest_path, "XXrXX", encoding="utf-8") as f:
                raw = f.read()
            data = json.loads(raw)
        except Exception as exc:
            raise RuntimeError(
                f"INTEGRITY_FAILURE: Failed to load or parse THRESHOLD_MANIFEST.json: {exc}"
            ) from exc

        # MVI-01: Compute hash excluding manifest_hash field.
        data_for_hash = {k: v for k, v in data.items() if k != "manifest_hash"}
        computed_hash = hashlib.sha256(
            json.dumps(data_for_hash, sort_keys=True, separators=(",", ":")).encode("utf-8")
        ).hexdigest()

        # MVI-02: Verify computed hash matches stored manifest_hash.
        stored_hash = data.get("manifest_hash", "")
        if (
            stored_hash
            and stored_hash != "BUILD_TIME_PLACEHOLDER"
            and stored_hash != computed_hash
        ):
            raise RuntimeError(
                f"MANIFEST_HASH_MISMATCH: Computed hash {computed_hash[:16]}... "
                f"does not match stored hash {stored_hash[:16]}... "
                "System start denied. Possible tampering."
            )

        # MVI-05: Check for absence of table_hash in joint_risk_multiplier_table.
        jrmt = data.get("joint_risk_multiplier_table", {})
        if "table_hash" in jrmt:
            raise RuntimeError(
                "MANIFEST_TABLEHASH_PRESENT: joint_risk_multiplier_table must not "
                "contain a table_hash key per Manifest Authority Policy."
            )

        # MVI-03: Extract the three FAS v6.1.0 constants.
        try:
            thresholds = data["thresholds"]
            shock_cap  = float(thresholds["shock_exposure_cap"])
            max_dd     = float(thresholds["max_drawdown_threshold"])
            vol_trig   = float(thresholds["vol_compression_trigger"])
        except (KeyError, ValueError) as exc:
            raise RuntimeError(
                f"INTEGRITY_FAILURE: Missing or invalid threshold key in manifest: {exc}"
            ) from exc

        # MVI-04: Verify the three extracted constants equal FAS v6.1.0 values.
        if not self._floats_equal(shock_cap, self._EXPECTED_SHOCK_EXPOSURE_CAP):
            raise RuntimeError(
                f"MANIFEST_CONSTANT_MISMATCH: shock_exposure_cap={shock_cap} "
                f"expected {self._EXPECTED_SHOCK_EXPOSURE_CAP}."
            )
        if not self._floats_equal(max_dd, self._EXPECTED_MAX_DRAWDOWN_THRESHOLD):
            raise RuntimeError(
                f"MANIFEST_CONSTANT_MISMATCH: max_drawdown_threshold={max_dd} "
                f"expected {self._EXPECTED_MAX_DRAWDOWN_THRESHOLD}."
            )
        if not self._floats_equal(vol_trig, self._EXPECTED_VOL_COMPRESSION_TRIGGER):
            raise RuntimeError(
                f"MANIFEST_CONSTANT_MISMATCH: vol_compression_trigger={vol_trig} "
                f"expected {self._EXPECTED_VOL_COMPRESSION_TRIGGER}."
            )

        # MVI-06: Return computed hash for propagation into ExecutionRecords.
        return computed_hash, thresholds

    def xǁManifestValidatorǁvalidate__mutmut_13(self) -> Tuple[str, Dict[str, Any]]:
        """
        Execute full manifest validation.

        Returns:
          (computed_hash, thresholds_dict)
          computed_hash -- SHA-256 hex digest of the manifest content.
          thresholds    -- dict from manifest["thresholds"] section.

        Raises RuntimeError with failure_type_id prefix on any hard failure.
        Failure types raised here:
          MANIFEST_HASH_MISMATCH    -- MVI-02
          MANIFEST_CONSTANT_MISMATCH -- MVI-04
          MANIFEST_TABLEHASH_PRESENT -- MVI-05
          INTEGRITY_FAILURE          -- missing file or parse error
        """
        # MVI-01: Load manifest file.
        if not self.manifest_path.exists():
            raise RuntimeError(
                "INTEGRITY_FAILURE: THRESHOLD_MANIFEST.json not found at "
                f"{self.manifest_path}. Harness cannot start without manifest."
            )

        try:
            with open(self.manifest_path, "R", encoding="utf-8") as f:
                raw = f.read()
            data = json.loads(raw)
        except Exception as exc:
            raise RuntimeError(
                f"INTEGRITY_FAILURE: Failed to load or parse THRESHOLD_MANIFEST.json: {exc}"
            ) from exc

        # MVI-01: Compute hash excluding manifest_hash field.
        data_for_hash = {k: v for k, v in data.items() if k != "manifest_hash"}
        computed_hash = hashlib.sha256(
            json.dumps(data_for_hash, sort_keys=True, separators=(",", ":")).encode("utf-8")
        ).hexdigest()

        # MVI-02: Verify computed hash matches stored manifest_hash.
        stored_hash = data.get("manifest_hash", "")
        if (
            stored_hash
            and stored_hash != "BUILD_TIME_PLACEHOLDER"
            and stored_hash != computed_hash
        ):
            raise RuntimeError(
                f"MANIFEST_HASH_MISMATCH: Computed hash {computed_hash[:16]}... "
                f"does not match stored hash {stored_hash[:16]}... "
                "System start denied. Possible tampering."
            )

        # MVI-05: Check for absence of table_hash in joint_risk_multiplier_table.
        jrmt = data.get("joint_risk_multiplier_table", {})
        if "table_hash" in jrmt:
            raise RuntimeError(
                "MANIFEST_TABLEHASH_PRESENT: joint_risk_multiplier_table must not "
                "contain a table_hash key per Manifest Authority Policy."
            )

        # MVI-03: Extract the three FAS v6.1.0 constants.
        try:
            thresholds = data["thresholds"]
            shock_cap  = float(thresholds["shock_exposure_cap"])
            max_dd     = float(thresholds["max_drawdown_threshold"])
            vol_trig   = float(thresholds["vol_compression_trigger"])
        except (KeyError, ValueError) as exc:
            raise RuntimeError(
                f"INTEGRITY_FAILURE: Missing or invalid threshold key in manifest: {exc}"
            ) from exc

        # MVI-04: Verify the three extracted constants equal FAS v6.1.0 values.
        if not self._floats_equal(shock_cap, self._EXPECTED_SHOCK_EXPOSURE_CAP):
            raise RuntimeError(
                f"MANIFEST_CONSTANT_MISMATCH: shock_exposure_cap={shock_cap} "
                f"expected {self._EXPECTED_SHOCK_EXPOSURE_CAP}."
            )
        if not self._floats_equal(max_dd, self._EXPECTED_MAX_DRAWDOWN_THRESHOLD):
            raise RuntimeError(
                f"MANIFEST_CONSTANT_MISMATCH: max_drawdown_threshold={max_dd} "
                f"expected {self._EXPECTED_MAX_DRAWDOWN_THRESHOLD}."
            )
        if not self._floats_equal(vol_trig, self._EXPECTED_VOL_COMPRESSION_TRIGGER):
            raise RuntimeError(
                f"MANIFEST_CONSTANT_MISMATCH: vol_compression_trigger={vol_trig} "
                f"expected {self._EXPECTED_VOL_COMPRESSION_TRIGGER}."
            )

        # MVI-06: Return computed hash for propagation into ExecutionRecords.
        return computed_hash, thresholds

    def xǁManifestValidatorǁvalidate__mutmut_14(self) -> Tuple[str, Dict[str, Any]]:
        """
        Execute full manifest validation.

        Returns:
          (computed_hash, thresholds_dict)
          computed_hash -- SHA-256 hex digest of the manifest content.
          thresholds    -- dict from manifest["thresholds"] section.

        Raises RuntimeError with failure_type_id prefix on any hard failure.
        Failure types raised here:
          MANIFEST_HASH_MISMATCH    -- MVI-02
          MANIFEST_CONSTANT_MISMATCH -- MVI-04
          MANIFEST_TABLEHASH_PRESENT -- MVI-05
          INTEGRITY_FAILURE          -- missing file or parse error
        """
        # MVI-01: Load manifest file.
        if not self.manifest_path.exists():
            raise RuntimeError(
                "INTEGRITY_FAILURE: THRESHOLD_MANIFEST.json not found at "
                f"{self.manifest_path}. Harness cannot start without manifest."
            )

        try:
            with open(self.manifest_path, "r", encoding="XXutf-8XX") as f:
                raw = f.read()
            data = json.loads(raw)
        except Exception as exc:
            raise RuntimeError(
                f"INTEGRITY_FAILURE: Failed to load or parse THRESHOLD_MANIFEST.json: {exc}"
            ) from exc

        # MVI-01: Compute hash excluding manifest_hash field.
        data_for_hash = {k: v for k, v in data.items() if k != "manifest_hash"}
        computed_hash = hashlib.sha256(
            json.dumps(data_for_hash, sort_keys=True, separators=(",", ":")).encode("utf-8")
        ).hexdigest()

        # MVI-02: Verify computed hash matches stored manifest_hash.
        stored_hash = data.get("manifest_hash", "")
        if (
            stored_hash
            and stored_hash != "BUILD_TIME_PLACEHOLDER"
            and stored_hash != computed_hash
        ):
            raise RuntimeError(
                f"MANIFEST_HASH_MISMATCH: Computed hash {computed_hash[:16]}... "
                f"does not match stored hash {stored_hash[:16]}... "
                "System start denied. Possible tampering."
            )

        # MVI-05: Check for absence of table_hash in joint_risk_multiplier_table.
        jrmt = data.get("joint_risk_multiplier_table", {})
        if "table_hash" in jrmt:
            raise RuntimeError(
                "MANIFEST_TABLEHASH_PRESENT: joint_risk_multiplier_table must not "
                "contain a table_hash key per Manifest Authority Policy."
            )

        # MVI-03: Extract the three FAS v6.1.0 constants.
        try:
            thresholds = data["thresholds"]
            shock_cap  = float(thresholds["shock_exposure_cap"])
            max_dd     = float(thresholds["max_drawdown_threshold"])
            vol_trig   = float(thresholds["vol_compression_trigger"])
        except (KeyError, ValueError) as exc:
            raise RuntimeError(
                f"INTEGRITY_FAILURE: Missing or invalid threshold key in manifest: {exc}"
            ) from exc

        # MVI-04: Verify the three extracted constants equal FAS v6.1.0 values.
        if not self._floats_equal(shock_cap, self._EXPECTED_SHOCK_EXPOSURE_CAP):
            raise RuntimeError(
                f"MANIFEST_CONSTANT_MISMATCH: shock_exposure_cap={shock_cap} "
                f"expected {self._EXPECTED_SHOCK_EXPOSURE_CAP}."
            )
        if not self._floats_equal(max_dd, self._EXPECTED_MAX_DRAWDOWN_THRESHOLD):
            raise RuntimeError(
                f"MANIFEST_CONSTANT_MISMATCH: max_drawdown_threshold={max_dd} "
                f"expected {self._EXPECTED_MAX_DRAWDOWN_THRESHOLD}."
            )
        if not self._floats_equal(vol_trig, self._EXPECTED_VOL_COMPRESSION_TRIGGER):
            raise RuntimeError(
                f"MANIFEST_CONSTANT_MISMATCH: vol_compression_trigger={vol_trig} "
                f"expected {self._EXPECTED_VOL_COMPRESSION_TRIGGER}."
            )

        # MVI-06: Return computed hash for propagation into ExecutionRecords.
        return computed_hash, thresholds

    def xǁManifestValidatorǁvalidate__mutmut_15(self) -> Tuple[str, Dict[str, Any]]:
        """
        Execute full manifest validation.

        Returns:
          (computed_hash, thresholds_dict)
          computed_hash -- SHA-256 hex digest of the manifest content.
          thresholds    -- dict from manifest["thresholds"] section.

        Raises RuntimeError with failure_type_id prefix on any hard failure.
        Failure types raised here:
          MANIFEST_HASH_MISMATCH    -- MVI-02
          MANIFEST_CONSTANT_MISMATCH -- MVI-04
          MANIFEST_TABLEHASH_PRESENT -- MVI-05
          INTEGRITY_FAILURE          -- missing file or parse error
        """
        # MVI-01: Load manifest file.
        if not self.manifest_path.exists():
            raise RuntimeError(
                "INTEGRITY_FAILURE: THRESHOLD_MANIFEST.json not found at "
                f"{self.manifest_path}. Harness cannot start without manifest."
            )

        try:
            with open(self.manifest_path, "r", encoding="UTF-8") as f:
                raw = f.read()
            data = json.loads(raw)
        except Exception as exc:
            raise RuntimeError(
                f"INTEGRITY_FAILURE: Failed to load or parse THRESHOLD_MANIFEST.json: {exc}"
            ) from exc

        # MVI-01: Compute hash excluding manifest_hash field.
        data_for_hash = {k: v for k, v in data.items() if k != "manifest_hash"}
        computed_hash = hashlib.sha256(
            json.dumps(data_for_hash, sort_keys=True, separators=(",", ":")).encode("utf-8")
        ).hexdigest()

        # MVI-02: Verify computed hash matches stored manifest_hash.
        stored_hash = data.get("manifest_hash", "")
        if (
            stored_hash
            and stored_hash != "BUILD_TIME_PLACEHOLDER"
            and stored_hash != computed_hash
        ):
            raise RuntimeError(
                f"MANIFEST_HASH_MISMATCH: Computed hash {computed_hash[:16]}... "
                f"does not match stored hash {stored_hash[:16]}... "
                "System start denied. Possible tampering."
            )

        # MVI-05: Check for absence of table_hash in joint_risk_multiplier_table.
        jrmt = data.get("joint_risk_multiplier_table", {})
        if "table_hash" in jrmt:
            raise RuntimeError(
                "MANIFEST_TABLEHASH_PRESENT: joint_risk_multiplier_table must not "
                "contain a table_hash key per Manifest Authority Policy."
            )

        # MVI-03: Extract the three FAS v6.1.0 constants.
        try:
            thresholds = data["thresholds"]
            shock_cap  = float(thresholds["shock_exposure_cap"])
            max_dd     = float(thresholds["max_drawdown_threshold"])
            vol_trig   = float(thresholds["vol_compression_trigger"])
        except (KeyError, ValueError) as exc:
            raise RuntimeError(
                f"INTEGRITY_FAILURE: Missing or invalid threshold key in manifest: {exc}"
            ) from exc

        # MVI-04: Verify the three extracted constants equal FAS v6.1.0 values.
        if not self._floats_equal(shock_cap, self._EXPECTED_SHOCK_EXPOSURE_CAP):
            raise RuntimeError(
                f"MANIFEST_CONSTANT_MISMATCH: shock_exposure_cap={shock_cap} "
                f"expected {self._EXPECTED_SHOCK_EXPOSURE_CAP}."
            )
        if not self._floats_equal(max_dd, self._EXPECTED_MAX_DRAWDOWN_THRESHOLD):
            raise RuntimeError(
                f"MANIFEST_CONSTANT_MISMATCH: max_drawdown_threshold={max_dd} "
                f"expected {self._EXPECTED_MAX_DRAWDOWN_THRESHOLD}."
            )
        if not self._floats_equal(vol_trig, self._EXPECTED_VOL_COMPRESSION_TRIGGER):
            raise RuntimeError(
                f"MANIFEST_CONSTANT_MISMATCH: vol_compression_trigger={vol_trig} "
                f"expected {self._EXPECTED_VOL_COMPRESSION_TRIGGER}."
            )

        # MVI-06: Return computed hash for propagation into ExecutionRecords.
        return computed_hash, thresholds

    def xǁManifestValidatorǁvalidate__mutmut_16(self) -> Tuple[str, Dict[str, Any]]:
        """
        Execute full manifest validation.

        Returns:
          (computed_hash, thresholds_dict)
          computed_hash -- SHA-256 hex digest of the manifest content.
          thresholds    -- dict from manifest["thresholds"] section.

        Raises RuntimeError with failure_type_id prefix on any hard failure.
        Failure types raised here:
          MANIFEST_HASH_MISMATCH    -- MVI-02
          MANIFEST_CONSTANT_MISMATCH -- MVI-04
          MANIFEST_TABLEHASH_PRESENT -- MVI-05
          INTEGRITY_FAILURE          -- missing file or parse error
        """
        # MVI-01: Load manifest file.
        if not self.manifest_path.exists():
            raise RuntimeError(
                "INTEGRITY_FAILURE: THRESHOLD_MANIFEST.json not found at "
                f"{self.manifest_path}. Harness cannot start without manifest."
            )

        try:
            with open(self.manifest_path, "r", encoding="utf-8") as f:
                raw = None
            data = json.loads(raw)
        except Exception as exc:
            raise RuntimeError(
                f"INTEGRITY_FAILURE: Failed to load or parse THRESHOLD_MANIFEST.json: {exc}"
            ) from exc

        # MVI-01: Compute hash excluding manifest_hash field.
        data_for_hash = {k: v for k, v in data.items() if k != "manifest_hash"}
        computed_hash = hashlib.sha256(
            json.dumps(data_for_hash, sort_keys=True, separators=(",", ":")).encode("utf-8")
        ).hexdigest()

        # MVI-02: Verify computed hash matches stored manifest_hash.
        stored_hash = data.get("manifest_hash", "")
        if (
            stored_hash
            and stored_hash != "BUILD_TIME_PLACEHOLDER"
            and stored_hash != computed_hash
        ):
            raise RuntimeError(
                f"MANIFEST_HASH_MISMATCH: Computed hash {computed_hash[:16]}... "
                f"does not match stored hash {stored_hash[:16]}... "
                "System start denied. Possible tampering."
            )

        # MVI-05: Check for absence of table_hash in joint_risk_multiplier_table.
        jrmt = data.get("joint_risk_multiplier_table", {})
        if "table_hash" in jrmt:
            raise RuntimeError(
                "MANIFEST_TABLEHASH_PRESENT: joint_risk_multiplier_table must not "
                "contain a table_hash key per Manifest Authority Policy."
            )

        # MVI-03: Extract the three FAS v6.1.0 constants.
        try:
            thresholds = data["thresholds"]
            shock_cap  = float(thresholds["shock_exposure_cap"])
            max_dd     = float(thresholds["max_drawdown_threshold"])
            vol_trig   = float(thresholds["vol_compression_trigger"])
        except (KeyError, ValueError) as exc:
            raise RuntimeError(
                f"INTEGRITY_FAILURE: Missing or invalid threshold key in manifest: {exc}"
            ) from exc

        # MVI-04: Verify the three extracted constants equal FAS v6.1.0 values.
        if not self._floats_equal(shock_cap, self._EXPECTED_SHOCK_EXPOSURE_CAP):
            raise RuntimeError(
                f"MANIFEST_CONSTANT_MISMATCH: shock_exposure_cap={shock_cap} "
                f"expected {self._EXPECTED_SHOCK_EXPOSURE_CAP}."
            )
        if not self._floats_equal(max_dd, self._EXPECTED_MAX_DRAWDOWN_THRESHOLD):
            raise RuntimeError(
                f"MANIFEST_CONSTANT_MISMATCH: max_drawdown_threshold={max_dd} "
                f"expected {self._EXPECTED_MAX_DRAWDOWN_THRESHOLD}."
            )
        if not self._floats_equal(vol_trig, self._EXPECTED_VOL_COMPRESSION_TRIGGER):
            raise RuntimeError(
                f"MANIFEST_CONSTANT_MISMATCH: vol_compression_trigger={vol_trig} "
                f"expected {self._EXPECTED_VOL_COMPRESSION_TRIGGER}."
            )

        # MVI-06: Return computed hash for propagation into ExecutionRecords.
        return computed_hash, thresholds

    def xǁManifestValidatorǁvalidate__mutmut_17(self) -> Tuple[str, Dict[str, Any]]:
        """
        Execute full manifest validation.

        Returns:
          (computed_hash, thresholds_dict)
          computed_hash -- SHA-256 hex digest of the manifest content.
          thresholds    -- dict from manifest["thresholds"] section.

        Raises RuntimeError with failure_type_id prefix on any hard failure.
        Failure types raised here:
          MANIFEST_HASH_MISMATCH    -- MVI-02
          MANIFEST_CONSTANT_MISMATCH -- MVI-04
          MANIFEST_TABLEHASH_PRESENT -- MVI-05
          INTEGRITY_FAILURE          -- missing file or parse error
        """
        # MVI-01: Load manifest file.
        if not self.manifest_path.exists():
            raise RuntimeError(
                "INTEGRITY_FAILURE: THRESHOLD_MANIFEST.json not found at "
                f"{self.manifest_path}. Harness cannot start without manifest."
            )

        try:
            with open(self.manifest_path, "r", encoding="utf-8") as f:
                raw = f.read()
            data = None
        except Exception as exc:
            raise RuntimeError(
                f"INTEGRITY_FAILURE: Failed to load or parse THRESHOLD_MANIFEST.json: {exc}"
            ) from exc

        # MVI-01: Compute hash excluding manifest_hash field.
        data_for_hash = {k: v for k, v in data.items() if k != "manifest_hash"}
        computed_hash = hashlib.sha256(
            json.dumps(data_for_hash, sort_keys=True, separators=(",", ":")).encode("utf-8")
        ).hexdigest()

        # MVI-02: Verify computed hash matches stored manifest_hash.
        stored_hash = data.get("manifest_hash", "")
        if (
            stored_hash
            and stored_hash != "BUILD_TIME_PLACEHOLDER"
            and stored_hash != computed_hash
        ):
            raise RuntimeError(
                f"MANIFEST_HASH_MISMATCH: Computed hash {computed_hash[:16]}... "
                f"does not match stored hash {stored_hash[:16]}... "
                "System start denied. Possible tampering."
            )

        # MVI-05: Check for absence of table_hash in joint_risk_multiplier_table.
        jrmt = data.get("joint_risk_multiplier_table", {})
        if "table_hash" in jrmt:
            raise RuntimeError(
                "MANIFEST_TABLEHASH_PRESENT: joint_risk_multiplier_table must not "
                "contain a table_hash key per Manifest Authority Policy."
            )

        # MVI-03: Extract the three FAS v6.1.0 constants.
        try:
            thresholds = data["thresholds"]
            shock_cap  = float(thresholds["shock_exposure_cap"])
            max_dd     = float(thresholds["max_drawdown_threshold"])
            vol_trig   = float(thresholds["vol_compression_trigger"])
        except (KeyError, ValueError) as exc:
            raise RuntimeError(
                f"INTEGRITY_FAILURE: Missing or invalid threshold key in manifest: {exc}"
            ) from exc

        # MVI-04: Verify the three extracted constants equal FAS v6.1.0 values.
        if not self._floats_equal(shock_cap, self._EXPECTED_SHOCK_EXPOSURE_CAP):
            raise RuntimeError(
                f"MANIFEST_CONSTANT_MISMATCH: shock_exposure_cap={shock_cap} "
                f"expected {self._EXPECTED_SHOCK_EXPOSURE_CAP}."
            )
        if not self._floats_equal(max_dd, self._EXPECTED_MAX_DRAWDOWN_THRESHOLD):
            raise RuntimeError(
                f"MANIFEST_CONSTANT_MISMATCH: max_drawdown_threshold={max_dd} "
                f"expected {self._EXPECTED_MAX_DRAWDOWN_THRESHOLD}."
            )
        if not self._floats_equal(vol_trig, self._EXPECTED_VOL_COMPRESSION_TRIGGER):
            raise RuntimeError(
                f"MANIFEST_CONSTANT_MISMATCH: vol_compression_trigger={vol_trig} "
                f"expected {self._EXPECTED_VOL_COMPRESSION_TRIGGER}."
            )

        # MVI-06: Return computed hash for propagation into ExecutionRecords.
        return computed_hash, thresholds

    def xǁManifestValidatorǁvalidate__mutmut_18(self) -> Tuple[str, Dict[str, Any]]:
        """
        Execute full manifest validation.

        Returns:
          (computed_hash, thresholds_dict)
          computed_hash -- SHA-256 hex digest of the manifest content.
          thresholds    -- dict from manifest["thresholds"] section.

        Raises RuntimeError with failure_type_id prefix on any hard failure.
        Failure types raised here:
          MANIFEST_HASH_MISMATCH    -- MVI-02
          MANIFEST_CONSTANT_MISMATCH -- MVI-04
          MANIFEST_TABLEHASH_PRESENT -- MVI-05
          INTEGRITY_FAILURE          -- missing file or parse error
        """
        # MVI-01: Load manifest file.
        if not self.manifest_path.exists():
            raise RuntimeError(
                "INTEGRITY_FAILURE: THRESHOLD_MANIFEST.json not found at "
                f"{self.manifest_path}. Harness cannot start without manifest."
            )

        try:
            with open(self.manifest_path, "r", encoding="utf-8") as f:
                raw = f.read()
            data = json.loads(None)
        except Exception as exc:
            raise RuntimeError(
                f"INTEGRITY_FAILURE: Failed to load or parse THRESHOLD_MANIFEST.json: {exc}"
            ) from exc

        # MVI-01: Compute hash excluding manifest_hash field.
        data_for_hash = {k: v for k, v in data.items() if k != "manifest_hash"}
        computed_hash = hashlib.sha256(
            json.dumps(data_for_hash, sort_keys=True, separators=(",", ":")).encode("utf-8")
        ).hexdigest()

        # MVI-02: Verify computed hash matches stored manifest_hash.
        stored_hash = data.get("manifest_hash", "")
        if (
            stored_hash
            and stored_hash != "BUILD_TIME_PLACEHOLDER"
            and stored_hash != computed_hash
        ):
            raise RuntimeError(
                f"MANIFEST_HASH_MISMATCH: Computed hash {computed_hash[:16]}... "
                f"does not match stored hash {stored_hash[:16]}... "
                "System start denied. Possible tampering."
            )

        # MVI-05: Check for absence of table_hash in joint_risk_multiplier_table.
        jrmt = data.get("joint_risk_multiplier_table", {})
        if "table_hash" in jrmt:
            raise RuntimeError(
                "MANIFEST_TABLEHASH_PRESENT: joint_risk_multiplier_table must not "
                "contain a table_hash key per Manifest Authority Policy."
            )

        # MVI-03: Extract the three FAS v6.1.0 constants.
        try:
            thresholds = data["thresholds"]
            shock_cap  = float(thresholds["shock_exposure_cap"])
            max_dd     = float(thresholds["max_drawdown_threshold"])
            vol_trig   = float(thresholds["vol_compression_trigger"])
        except (KeyError, ValueError) as exc:
            raise RuntimeError(
                f"INTEGRITY_FAILURE: Missing or invalid threshold key in manifest: {exc}"
            ) from exc

        # MVI-04: Verify the three extracted constants equal FAS v6.1.0 values.
        if not self._floats_equal(shock_cap, self._EXPECTED_SHOCK_EXPOSURE_CAP):
            raise RuntimeError(
                f"MANIFEST_CONSTANT_MISMATCH: shock_exposure_cap={shock_cap} "
                f"expected {self._EXPECTED_SHOCK_EXPOSURE_CAP}."
            )
        if not self._floats_equal(max_dd, self._EXPECTED_MAX_DRAWDOWN_THRESHOLD):
            raise RuntimeError(
                f"MANIFEST_CONSTANT_MISMATCH: max_drawdown_threshold={max_dd} "
                f"expected {self._EXPECTED_MAX_DRAWDOWN_THRESHOLD}."
            )
        if not self._floats_equal(vol_trig, self._EXPECTED_VOL_COMPRESSION_TRIGGER):
            raise RuntimeError(
                f"MANIFEST_CONSTANT_MISMATCH: vol_compression_trigger={vol_trig} "
                f"expected {self._EXPECTED_VOL_COMPRESSION_TRIGGER}."
            )

        # MVI-06: Return computed hash for propagation into ExecutionRecords.
        return computed_hash, thresholds

    def xǁManifestValidatorǁvalidate__mutmut_19(self) -> Tuple[str, Dict[str, Any]]:
        """
        Execute full manifest validation.

        Returns:
          (computed_hash, thresholds_dict)
          computed_hash -- SHA-256 hex digest of the manifest content.
          thresholds    -- dict from manifest["thresholds"] section.

        Raises RuntimeError with failure_type_id prefix on any hard failure.
        Failure types raised here:
          MANIFEST_HASH_MISMATCH    -- MVI-02
          MANIFEST_CONSTANT_MISMATCH -- MVI-04
          MANIFEST_TABLEHASH_PRESENT -- MVI-05
          INTEGRITY_FAILURE          -- missing file or parse error
        """
        # MVI-01: Load manifest file.
        if not self.manifest_path.exists():
            raise RuntimeError(
                "INTEGRITY_FAILURE: THRESHOLD_MANIFEST.json not found at "
                f"{self.manifest_path}. Harness cannot start without manifest."
            )

        try:
            with open(self.manifest_path, "r", encoding="utf-8") as f:
                raw = f.read()
            data = json.loads(raw)
        except Exception as exc:
            raise RuntimeError(
                None
            ) from exc

        # MVI-01: Compute hash excluding manifest_hash field.
        data_for_hash = {k: v for k, v in data.items() if k != "manifest_hash"}
        computed_hash = hashlib.sha256(
            json.dumps(data_for_hash, sort_keys=True, separators=(",", ":")).encode("utf-8")
        ).hexdigest()

        # MVI-02: Verify computed hash matches stored manifest_hash.
        stored_hash = data.get("manifest_hash", "")
        if (
            stored_hash
            and stored_hash != "BUILD_TIME_PLACEHOLDER"
            and stored_hash != computed_hash
        ):
            raise RuntimeError(
                f"MANIFEST_HASH_MISMATCH: Computed hash {computed_hash[:16]}... "
                f"does not match stored hash {stored_hash[:16]}... "
                "System start denied. Possible tampering."
            )

        # MVI-05: Check for absence of table_hash in joint_risk_multiplier_table.
        jrmt = data.get("joint_risk_multiplier_table", {})
        if "table_hash" in jrmt:
            raise RuntimeError(
                "MANIFEST_TABLEHASH_PRESENT: joint_risk_multiplier_table must not "
                "contain a table_hash key per Manifest Authority Policy."
            )

        # MVI-03: Extract the three FAS v6.1.0 constants.
        try:
            thresholds = data["thresholds"]
            shock_cap  = float(thresholds["shock_exposure_cap"])
            max_dd     = float(thresholds["max_drawdown_threshold"])
            vol_trig   = float(thresholds["vol_compression_trigger"])
        except (KeyError, ValueError) as exc:
            raise RuntimeError(
                f"INTEGRITY_FAILURE: Missing or invalid threshold key in manifest: {exc}"
            ) from exc

        # MVI-04: Verify the three extracted constants equal FAS v6.1.0 values.
        if not self._floats_equal(shock_cap, self._EXPECTED_SHOCK_EXPOSURE_CAP):
            raise RuntimeError(
                f"MANIFEST_CONSTANT_MISMATCH: shock_exposure_cap={shock_cap} "
                f"expected {self._EXPECTED_SHOCK_EXPOSURE_CAP}."
            )
        if not self._floats_equal(max_dd, self._EXPECTED_MAX_DRAWDOWN_THRESHOLD):
            raise RuntimeError(
                f"MANIFEST_CONSTANT_MISMATCH: max_drawdown_threshold={max_dd} "
                f"expected {self._EXPECTED_MAX_DRAWDOWN_THRESHOLD}."
            )
        if not self._floats_equal(vol_trig, self._EXPECTED_VOL_COMPRESSION_TRIGGER):
            raise RuntimeError(
                f"MANIFEST_CONSTANT_MISMATCH: vol_compression_trigger={vol_trig} "
                f"expected {self._EXPECTED_VOL_COMPRESSION_TRIGGER}."
            )

        # MVI-06: Return computed hash for propagation into ExecutionRecords.
        return computed_hash, thresholds

    def xǁManifestValidatorǁvalidate__mutmut_20(self) -> Tuple[str, Dict[str, Any]]:
        """
        Execute full manifest validation.

        Returns:
          (computed_hash, thresholds_dict)
          computed_hash -- SHA-256 hex digest of the manifest content.
          thresholds    -- dict from manifest["thresholds"] section.

        Raises RuntimeError with failure_type_id prefix on any hard failure.
        Failure types raised here:
          MANIFEST_HASH_MISMATCH    -- MVI-02
          MANIFEST_CONSTANT_MISMATCH -- MVI-04
          MANIFEST_TABLEHASH_PRESENT -- MVI-05
          INTEGRITY_FAILURE          -- missing file or parse error
        """
        # MVI-01: Load manifest file.
        if not self.manifest_path.exists():
            raise RuntimeError(
                "INTEGRITY_FAILURE: THRESHOLD_MANIFEST.json not found at "
                f"{self.manifest_path}. Harness cannot start without manifest."
            )

        try:
            with open(self.manifest_path, "r", encoding="utf-8") as f:
                raw = f.read()
            data = json.loads(raw)
        except Exception as exc:
            raise RuntimeError(
                f"INTEGRITY_FAILURE: Failed to load or parse THRESHOLD_MANIFEST.json: {exc}"
            ) from exc

        # MVI-01: Compute hash excluding manifest_hash field.
        data_for_hash = None
        computed_hash = hashlib.sha256(
            json.dumps(data_for_hash, sort_keys=True, separators=(",", ":")).encode("utf-8")
        ).hexdigest()

        # MVI-02: Verify computed hash matches stored manifest_hash.
        stored_hash = data.get("manifest_hash", "")
        if (
            stored_hash
            and stored_hash != "BUILD_TIME_PLACEHOLDER"
            and stored_hash != computed_hash
        ):
            raise RuntimeError(
                f"MANIFEST_HASH_MISMATCH: Computed hash {computed_hash[:16]}... "
                f"does not match stored hash {stored_hash[:16]}... "
                "System start denied. Possible tampering."
            )

        # MVI-05: Check for absence of table_hash in joint_risk_multiplier_table.
        jrmt = data.get("joint_risk_multiplier_table", {})
        if "table_hash" in jrmt:
            raise RuntimeError(
                "MANIFEST_TABLEHASH_PRESENT: joint_risk_multiplier_table must not "
                "contain a table_hash key per Manifest Authority Policy."
            )

        # MVI-03: Extract the three FAS v6.1.0 constants.
        try:
            thresholds = data["thresholds"]
            shock_cap  = float(thresholds["shock_exposure_cap"])
            max_dd     = float(thresholds["max_drawdown_threshold"])
            vol_trig   = float(thresholds["vol_compression_trigger"])
        except (KeyError, ValueError) as exc:
            raise RuntimeError(
                f"INTEGRITY_FAILURE: Missing or invalid threshold key in manifest: {exc}"
            ) from exc

        # MVI-04: Verify the three extracted constants equal FAS v6.1.0 values.
        if not self._floats_equal(shock_cap, self._EXPECTED_SHOCK_EXPOSURE_CAP):
            raise RuntimeError(
                f"MANIFEST_CONSTANT_MISMATCH: shock_exposure_cap={shock_cap} "
                f"expected {self._EXPECTED_SHOCK_EXPOSURE_CAP}."
            )
        if not self._floats_equal(max_dd, self._EXPECTED_MAX_DRAWDOWN_THRESHOLD):
            raise RuntimeError(
                f"MANIFEST_CONSTANT_MISMATCH: max_drawdown_threshold={max_dd} "
                f"expected {self._EXPECTED_MAX_DRAWDOWN_THRESHOLD}."
            )
        if not self._floats_equal(vol_trig, self._EXPECTED_VOL_COMPRESSION_TRIGGER):
            raise RuntimeError(
                f"MANIFEST_CONSTANT_MISMATCH: vol_compression_trigger={vol_trig} "
                f"expected {self._EXPECTED_VOL_COMPRESSION_TRIGGER}."
            )

        # MVI-06: Return computed hash for propagation into ExecutionRecords.
        return computed_hash, thresholds

    def xǁManifestValidatorǁvalidate__mutmut_21(self) -> Tuple[str, Dict[str, Any]]:
        """
        Execute full manifest validation.

        Returns:
          (computed_hash, thresholds_dict)
          computed_hash -- SHA-256 hex digest of the manifest content.
          thresholds    -- dict from manifest["thresholds"] section.

        Raises RuntimeError with failure_type_id prefix on any hard failure.
        Failure types raised here:
          MANIFEST_HASH_MISMATCH    -- MVI-02
          MANIFEST_CONSTANT_MISMATCH -- MVI-04
          MANIFEST_TABLEHASH_PRESENT -- MVI-05
          INTEGRITY_FAILURE          -- missing file or parse error
        """
        # MVI-01: Load manifest file.
        if not self.manifest_path.exists():
            raise RuntimeError(
                "INTEGRITY_FAILURE: THRESHOLD_MANIFEST.json not found at "
                f"{self.manifest_path}. Harness cannot start without manifest."
            )

        try:
            with open(self.manifest_path, "r", encoding="utf-8") as f:
                raw = f.read()
            data = json.loads(raw)
        except Exception as exc:
            raise RuntimeError(
                f"INTEGRITY_FAILURE: Failed to load or parse THRESHOLD_MANIFEST.json: {exc}"
            ) from exc

        # MVI-01: Compute hash excluding manifest_hash field.
        data_for_hash = {k: v for k, v in data.items() if k == "manifest_hash"}
        computed_hash = hashlib.sha256(
            json.dumps(data_for_hash, sort_keys=True, separators=(",", ":")).encode("utf-8")
        ).hexdigest()

        # MVI-02: Verify computed hash matches stored manifest_hash.
        stored_hash = data.get("manifest_hash", "")
        if (
            stored_hash
            and stored_hash != "BUILD_TIME_PLACEHOLDER"
            and stored_hash != computed_hash
        ):
            raise RuntimeError(
                f"MANIFEST_HASH_MISMATCH: Computed hash {computed_hash[:16]}... "
                f"does not match stored hash {stored_hash[:16]}... "
                "System start denied. Possible tampering."
            )

        # MVI-05: Check for absence of table_hash in joint_risk_multiplier_table.
        jrmt = data.get("joint_risk_multiplier_table", {})
        if "table_hash" in jrmt:
            raise RuntimeError(
                "MANIFEST_TABLEHASH_PRESENT: joint_risk_multiplier_table must not "
                "contain a table_hash key per Manifest Authority Policy."
            )

        # MVI-03: Extract the three FAS v6.1.0 constants.
        try:
            thresholds = data["thresholds"]
            shock_cap  = float(thresholds["shock_exposure_cap"])
            max_dd     = float(thresholds["max_drawdown_threshold"])
            vol_trig   = float(thresholds["vol_compression_trigger"])
        except (KeyError, ValueError) as exc:
            raise RuntimeError(
                f"INTEGRITY_FAILURE: Missing or invalid threshold key in manifest: {exc}"
            ) from exc

        # MVI-04: Verify the three extracted constants equal FAS v6.1.0 values.
        if not self._floats_equal(shock_cap, self._EXPECTED_SHOCK_EXPOSURE_CAP):
            raise RuntimeError(
                f"MANIFEST_CONSTANT_MISMATCH: shock_exposure_cap={shock_cap} "
                f"expected {self._EXPECTED_SHOCK_EXPOSURE_CAP}."
            )
        if not self._floats_equal(max_dd, self._EXPECTED_MAX_DRAWDOWN_THRESHOLD):
            raise RuntimeError(
                f"MANIFEST_CONSTANT_MISMATCH: max_drawdown_threshold={max_dd} "
                f"expected {self._EXPECTED_MAX_DRAWDOWN_THRESHOLD}."
            )
        if not self._floats_equal(vol_trig, self._EXPECTED_VOL_COMPRESSION_TRIGGER):
            raise RuntimeError(
                f"MANIFEST_CONSTANT_MISMATCH: vol_compression_trigger={vol_trig} "
                f"expected {self._EXPECTED_VOL_COMPRESSION_TRIGGER}."
            )

        # MVI-06: Return computed hash for propagation into ExecutionRecords.
        return computed_hash, thresholds

    def xǁManifestValidatorǁvalidate__mutmut_22(self) -> Tuple[str, Dict[str, Any]]:
        """
        Execute full manifest validation.

        Returns:
          (computed_hash, thresholds_dict)
          computed_hash -- SHA-256 hex digest of the manifest content.
          thresholds    -- dict from manifest["thresholds"] section.

        Raises RuntimeError with failure_type_id prefix on any hard failure.
        Failure types raised here:
          MANIFEST_HASH_MISMATCH    -- MVI-02
          MANIFEST_CONSTANT_MISMATCH -- MVI-04
          MANIFEST_TABLEHASH_PRESENT -- MVI-05
          INTEGRITY_FAILURE          -- missing file or parse error
        """
        # MVI-01: Load manifest file.
        if not self.manifest_path.exists():
            raise RuntimeError(
                "INTEGRITY_FAILURE: THRESHOLD_MANIFEST.json not found at "
                f"{self.manifest_path}. Harness cannot start without manifest."
            )

        try:
            with open(self.manifest_path, "r", encoding="utf-8") as f:
                raw = f.read()
            data = json.loads(raw)
        except Exception as exc:
            raise RuntimeError(
                f"INTEGRITY_FAILURE: Failed to load or parse THRESHOLD_MANIFEST.json: {exc}"
            ) from exc

        # MVI-01: Compute hash excluding manifest_hash field.
        data_for_hash = {k: v for k, v in data.items() if k != "XXmanifest_hashXX"}
        computed_hash = hashlib.sha256(
            json.dumps(data_for_hash, sort_keys=True, separators=(",", ":")).encode("utf-8")
        ).hexdigest()

        # MVI-02: Verify computed hash matches stored manifest_hash.
        stored_hash = data.get("manifest_hash", "")
        if (
            stored_hash
            and stored_hash != "BUILD_TIME_PLACEHOLDER"
            and stored_hash != computed_hash
        ):
            raise RuntimeError(
                f"MANIFEST_HASH_MISMATCH: Computed hash {computed_hash[:16]}... "
                f"does not match stored hash {stored_hash[:16]}... "
                "System start denied. Possible tampering."
            )

        # MVI-05: Check for absence of table_hash in joint_risk_multiplier_table.
        jrmt = data.get("joint_risk_multiplier_table", {})
        if "table_hash" in jrmt:
            raise RuntimeError(
                "MANIFEST_TABLEHASH_PRESENT: joint_risk_multiplier_table must not "
                "contain a table_hash key per Manifest Authority Policy."
            )

        # MVI-03: Extract the three FAS v6.1.0 constants.
        try:
            thresholds = data["thresholds"]
            shock_cap  = float(thresholds["shock_exposure_cap"])
            max_dd     = float(thresholds["max_drawdown_threshold"])
            vol_trig   = float(thresholds["vol_compression_trigger"])
        except (KeyError, ValueError) as exc:
            raise RuntimeError(
                f"INTEGRITY_FAILURE: Missing or invalid threshold key in manifest: {exc}"
            ) from exc

        # MVI-04: Verify the three extracted constants equal FAS v6.1.0 values.
        if not self._floats_equal(shock_cap, self._EXPECTED_SHOCK_EXPOSURE_CAP):
            raise RuntimeError(
                f"MANIFEST_CONSTANT_MISMATCH: shock_exposure_cap={shock_cap} "
                f"expected {self._EXPECTED_SHOCK_EXPOSURE_CAP}."
            )
        if not self._floats_equal(max_dd, self._EXPECTED_MAX_DRAWDOWN_THRESHOLD):
            raise RuntimeError(
                f"MANIFEST_CONSTANT_MISMATCH: max_drawdown_threshold={max_dd} "
                f"expected {self._EXPECTED_MAX_DRAWDOWN_THRESHOLD}."
            )
        if not self._floats_equal(vol_trig, self._EXPECTED_VOL_COMPRESSION_TRIGGER):
            raise RuntimeError(
                f"MANIFEST_CONSTANT_MISMATCH: vol_compression_trigger={vol_trig} "
                f"expected {self._EXPECTED_VOL_COMPRESSION_TRIGGER}."
            )

        # MVI-06: Return computed hash for propagation into ExecutionRecords.
        return computed_hash, thresholds

    def xǁManifestValidatorǁvalidate__mutmut_23(self) -> Tuple[str, Dict[str, Any]]:
        """
        Execute full manifest validation.

        Returns:
          (computed_hash, thresholds_dict)
          computed_hash -- SHA-256 hex digest of the manifest content.
          thresholds    -- dict from manifest["thresholds"] section.

        Raises RuntimeError with failure_type_id prefix on any hard failure.
        Failure types raised here:
          MANIFEST_HASH_MISMATCH    -- MVI-02
          MANIFEST_CONSTANT_MISMATCH -- MVI-04
          MANIFEST_TABLEHASH_PRESENT -- MVI-05
          INTEGRITY_FAILURE          -- missing file or parse error
        """
        # MVI-01: Load manifest file.
        if not self.manifest_path.exists():
            raise RuntimeError(
                "INTEGRITY_FAILURE: THRESHOLD_MANIFEST.json not found at "
                f"{self.manifest_path}. Harness cannot start without manifest."
            )

        try:
            with open(self.manifest_path, "r", encoding="utf-8") as f:
                raw = f.read()
            data = json.loads(raw)
        except Exception as exc:
            raise RuntimeError(
                f"INTEGRITY_FAILURE: Failed to load or parse THRESHOLD_MANIFEST.json: {exc}"
            ) from exc

        # MVI-01: Compute hash excluding manifest_hash field.
        data_for_hash = {k: v for k, v in data.items() if k != "MANIFEST_HASH"}
        computed_hash = hashlib.sha256(
            json.dumps(data_for_hash, sort_keys=True, separators=(",", ":")).encode("utf-8")
        ).hexdigest()

        # MVI-02: Verify computed hash matches stored manifest_hash.
        stored_hash = data.get("manifest_hash", "")
        if (
            stored_hash
            and stored_hash != "BUILD_TIME_PLACEHOLDER"
            and stored_hash != computed_hash
        ):
            raise RuntimeError(
                f"MANIFEST_HASH_MISMATCH: Computed hash {computed_hash[:16]}... "
                f"does not match stored hash {stored_hash[:16]}... "
                "System start denied. Possible tampering."
            )

        # MVI-05: Check for absence of table_hash in joint_risk_multiplier_table.
        jrmt = data.get("joint_risk_multiplier_table", {})
        if "table_hash" in jrmt:
            raise RuntimeError(
                "MANIFEST_TABLEHASH_PRESENT: joint_risk_multiplier_table must not "
                "contain a table_hash key per Manifest Authority Policy."
            )

        # MVI-03: Extract the three FAS v6.1.0 constants.
        try:
            thresholds = data["thresholds"]
            shock_cap  = float(thresholds["shock_exposure_cap"])
            max_dd     = float(thresholds["max_drawdown_threshold"])
            vol_trig   = float(thresholds["vol_compression_trigger"])
        except (KeyError, ValueError) as exc:
            raise RuntimeError(
                f"INTEGRITY_FAILURE: Missing or invalid threshold key in manifest: {exc}"
            ) from exc

        # MVI-04: Verify the three extracted constants equal FAS v6.1.0 values.
        if not self._floats_equal(shock_cap, self._EXPECTED_SHOCK_EXPOSURE_CAP):
            raise RuntimeError(
                f"MANIFEST_CONSTANT_MISMATCH: shock_exposure_cap={shock_cap} "
                f"expected {self._EXPECTED_SHOCK_EXPOSURE_CAP}."
            )
        if not self._floats_equal(max_dd, self._EXPECTED_MAX_DRAWDOWN_THRESHOLD):
            raise RuntimeError(
                f"MANIFEST_CONSTANT_MISMATCH: max_drawdown_threshold={max_dd} "
                f"expected {self._EXPECTED_MAX_DRAWDOWN_THRESHOLD}."
            )
        if not self._floats_equal(vol_trig, self._EXPECTED_VOL_COMPRESSION_TRIGGER):
            raise RuntimeError(
                f"MANIFEST_CONSTANT_MISMATCH: vol_compression_trigger={vol_trig} "
                f"expected {self._EXPECTED_VOL_COMPRESSION_TRIGGER}."
            )

        # MVI-06: Return computed hash for propagation into ExecutionRecords.
        return computed_hash, thresholds

    def xǁManifestValidatorǁvalidate__mutmut_24(self) -> Tuple[str, Dict[str, Any]]:
        """
        Execute full manifest validation.

        Returns:
          (computed_hash, thresholds_dict)
          computed_hash -- SHA-256 hex digest of the manifest content.
          thresholds    -- dict from manifest["thresholds"] section.

        Raises RuntimeError with failure_type_id prefix on any hard failure.
        Failure types raised here:
          MANIFEST_HASH_MISMATCH    -- MVI-02
          MANIFEST_CONSTANT_MISMATCH -- MVI-04
          MANIFEST_TABLEHASH_PRESENT -- MVI-05
          INTEGRITY_FAILURE          -- missing file or parse error
        """
        # MVI-01: Load manifest file.
        if not self.manifest_path.exists():
            raise RuntimeError(
                "INTEGRITY_FAILURE: THRESHOLD_MANIFEST.json not found at "
                f"{self.manifest_path}. Harness cannot start without manifest."
            )

        try:
            with open(self.manifest_path, "r", encoding="utf-8") as f:
                raw = f.read()
            data = json.loads(raw)
        except Exception as exc:
            raise RuntimeError(
                f"INTEGRITY_FAILURE: Failed to load or parse THRESHOLD_MANIFEST.json: {exc}"
            ) from exc

        # MVI-01: Compute hash excluding manifest_hash field.
        data_for_hash = {k: v for k, v in data.items() if k != "manifest_hash"}
        computed_hash = None

        # MVI-02: Verify computed hash matches stored manifest_hash.
        stored_hash = data.get("manifest_hash", "")
        if (
            stored_hash
            and stored_hash != "BUILD_TIME_PLACEHOLDER"
            and stored_hash != computed_hash
        ):
            raise RuntimeError(
                f"MANIFEST_HASH_MISMATCH: Computed hash {computed_hash[:16]}... "
                f"does not match stored hash {stored_hash[:16]}... "
                "System start denied. Possible tampering."
            )

        # MVI-05: Check for absence of table_hash in joint_risk_multiplier_table.
        jrmt = data.get("joint_risk_multiplier_table", {})
        if "table_hash" in jrmt:
            raise RuntimeError(
                "MANIFEST_TABLEHASH_PRESENT: joint_risk_multiplier_table must not "
                "contain a table_hash key per Manifest Authority Policy."
            )

        # MVI-03: Extract the three FAS v6.1.0 constants.
        try:
            thresholds = data["thresholds"]
            shock_cap  = float(thresholds["shock_exposure_cap"])
            max_dd     = float(thresholds["max_drawdown_threshold"])
            vol_trig   = float(thresholds["vol_compression_trigger"])
        except (KeyError, ValueError) as exc:
            raise RuntimeError(
                f"INTEGRITY_FAILURE: Missing or invalid threshold key in manifest: {exc}"
            ) from exc

        # MVI-04: Verify the three extracted constants equal FAS v6.1.0 values.
        if not self._floats_equal(shock_cap, self._EXPECTED_SHOCK_EXPOSURE_CAP):
            raise RuntimeError(
                f"MANIFEST_CONSTANT_MISMATCH: shock_exposure_cap={shock_cap} "
                f"expected {self._EXPECTED_SHOCK_EXPOSURE_CAP}."
            )
        if not self._floats_equal(max_dd, self._EXPECTED_MAX_DRAWDOWN_THRESHOLD):
            raise RuntimeError(
                f"MANIFEST_CONSTANT_MISMATCH: max_drawdown_threshold={max_dd} "
                f"expected {self._EXPECTED_MAX_DRAWDOWN_THRESHOLD}."
            )
        if not self._floats_equal(vol_trig, self._EXPECTED_VOL_COMPRESSION_TRIGGER):
            raise RuntimeError(
                f"MANIFEST_CONSTANT_MISMATCH: vol_compression_trigger={vol_trig} "
                f"expected {self._EXPECTED_VOL_COMPRESSION_TRIGGER}."
            )

        # MVI-06: Return computed hash for propagation into ExecutionRecords.
        return computed_hash, thresholds

    def xǁManifestValidatorǁvalidate__mutmut_25(self) -> Tuple[str, Dict[str, Any]]:
        """
        Execute full manifest validation.

        Returns:
          (computed_hash, thresholds_dict)
          computed_hash -- SHA-256 hex digest of the manifest content.
          thresholds    -- dict from manifest["thresholds"] section.

        Raises RuntimeError with failure_type_id prefix on any hard failure.
        Failure types raised here:
          MANIFEST_HASH_MISMATCH    -- MVI-02
          MANIFEST_CONSTANT_MISMATCH -- MVI-04
          MANIFEST_TABLEHASH_PRESENT -- MVI-05
          INTEGRITY_FAILURE          -- missing file or parse error
        """
        # MVI-01: Load manifest file.
        if not self.manifest_path.exists():
            raise RuntimeError(
                "INTEGRITY_FAILURE: THRESHOLD_MANIFEST.json not found at "
                f"{self.manifest_path}. Harness cannot start without manifest."
            )

        try:
            with open(self.manifest_path, "r", encoding="utf-8") as f:
                raw = f.read()
            data = json.loads(raw)
        except Exception as exc:
            raise RuntimeError(
                f"INTEGRITY_FAILURE: Failed to load or parse THRESHOLD_MANIFEST.json: {exc}"
            ) from exc

        # MVI-01: Compute hash excluding manifest_hash field.
        data_for_hash = {k: v for k, v in data.items() if k != "manifest_hash"}
        computed_hash = hashlib.sha256(
            None
        ).hexdigest()

        # MVI-02: Verify computed hash matches stored manifest_hash.
        stored_hash = data.get("manifest_hash", "")
        if (
            stored_hash
            and stored_hash != "BUILD_TIME_PLACEHOLDER"
            and stored_hash != computed_hash
        ):
            raise RuntimeError(
                f"MANIFEST_HASH_MISMATCH: Computed hash {computed_hash[:16]}... "
                f"does not match stored hash {stored_hash[:16]}... "
                "System start denied. Possible tampering."
            )

        # MVI-05: Check for absence of table_hash in joint_risk_multiplier_table.
        jrmt = data.get("joint_risk_multiplier_table", {})
        if "table_hash" in jrmt:
            raise RuntimeError(
                "MANIFEST_TABLEHASH_PRESENT: joint_risk_multiplier_table must not "
                "contain a table_hash key per Manifest Authority Policy."
            )

        # MVI-03: Extract the three FAS v6.1.0 constants.
        try:
            thresholds = data["thresholds"]
            shock_cap  = float(thresholds["shock_exposure_cap"])
            max_dd     = float(thresholds["max_drawdown_threshold"])
            vol_trig   = float(thresholds["vol_compression_trigger"])
        except (KeyError, ValueError) as exc:
            raise RuntimeError(
                f"INTEGRITY_FAILURE: Missing or invalid threshold key in manifest: {exc}"
            ) from exc

        # MVI-04: Verify the three extracted constants equal FAS v6.1.0 values.
        if not self._floats_equal(shock_cap, self._EXPECTED_SHOCK_EXPOSURE_CAP):
            raise RuntimeError(
                f"MANIFEST_CONSTANT_MISMATCH: shock_exposure_cap={shock_cap} "
                f"expected {self._EXPECTED_SHOCK_EXPOSURE_CAP}."
            )
        if not self._floats_equal(max_dd, self._EXPECTED_MAX_DRAWDOWN_THRESHOLD):
            raise RuntimeError(
                f"MANIFEST_CONSTANT_MISMATCH: max_drawdown_threshold={max_dd} "
                f"expected {self._EXPECTED_MAX_DRAWDOWN_THRESHOLD}."
            )
        if not self._floats_equal(vol_trig, self._EXPECTED_VOL_COMPRESSION_TRIGGER):
            raise RuntimeError(
                f"MANIFEST_CONSTANT_MISMATCH: vol_compression_trigger={vol_trig} "
                f"expected {self._EXPECTED_VOL_COMPRESSION_TRIGGER}."
            )

        # MVI-06: Return computed hash for propagation into ExecutionRecords.
        return computed_hash, thresholds

    def xǁManifestValidatorǁvalidate__mutmut_26(self) -> Tuple[str, Dict[str, Any]]:
        """
        Execute full manifest validation.

        Returns:
          (computed_hash, thresholds_dict)
          computed_hash -- SHA-256 hex digest of the manifest content.
          thresholds    -- dict from manifest["thresholds"] section.

        Raises RuntimeError with failure_type_id prefix on any hard failure.
        Failure types raised here:
          MANIFEST_HASH_MISMATCH    -- MVI-02
          MANIFEST_CONSTANT_MISMATCH -- MVI-04
          MANIFEST_TABLEHASH_PRESENT -- MVI-05
          INTEGRITY_FAILURE          -- missing file or parse error
        """
        # MVI-01: Load manifest file.
        if not self.manifest_path.exists():
            raise RuntimeError(
                "INTEGRITY_FAILURE: THRESHOLD_MANIFEST.json not found at "
                f"{self.manifest_path}. Harness cannot start without manifest."
            )

        try:
            with open(self.manifest_path, "r", encoding="utf-8") as f:
                raw = f.read()
            data = json.loads(raw)
        except Exception as exc:
            raise RuntimeError(
                f"INTEGRITY_FAILURE: Failed to load or parse THRESHOLD_MANIFEST.json: {exc}"
            ) from exc

        # MVI-01: Compute hash excluding manifest_hash field.
        data_for_hash = {k: v for k, v in data.items() if k != "manifest_hash"}
        computed_hash = hashlib.sha256(
            json.dumps(data_for_hash, sort_keys=True, separators=(",", ":")).encode(None)
        ).hexdigest()

        # MVI-02: Verify computed hash matches stored manifest_hash.
        stored_hash = data.get("manifest_hash", "")
        if (
            stored_hash
            and stored_hash != "BUILD_TIME_PLACEHOLDER"
            and stored_hash != computed_hash
        ):
            raise RuntimeError(
                f"MANIFEST_HASH_MISMATCH: Computed hash {computed_hash[:16]}... "
                f"does not match stored hash {stored_hash[:16]}... "
                "System start denied. Possible tampering."
            )

        # MVI-05: Check for absence of table_hash in joint_risk_multiplier_table.
        jrmt = data.get("joint_risk_multiplier_table", {})
        if "table_hash" in jrmt:
            raise RuntimeError(
                "MANIFEST_TABLEHASH_PRESENT: joint_risk_multiplier_table must not "
                "contain a table_hash key per Manifest Authority Policy."
            )

        # MVI-03: Extract the three FAS v6.1.0 constants.
        try:
            thresholds = data["thresholds"]
            shock_cap  = float(thresholds["shock_exposure_cap"])
            max_dd     = float(thresholds["max_drawdown_threshold"])
            vol_trig   = float(thresholds["vol_compression_trigger"])
        except (KeyError, ValueError) as exc:
            raise RuntimeError(
                f"INTEGRITY_FAILURE: Missing or invalid threshold key in manifest: {exc}"
            ) from exc

        # MVI-04: Verify the three extracted constants equal FAS v6.1.0 values.
        if not self._floats_equal(shock_cap, self._EXPECTED_SHOCK_EXPOSURE_CAP):
            raise RuntimeError(
                f"MANIFEST_CONSTANT_MISMATCH: shock_exposure_cap={shock_cap} "
                f"expected {self._EXPECTED_SHOCK_EXPOSURE_CAP}."
            )
        if not self._floats_equal(max_dd, self._EXPECTED_MAX_DRAWDOWN_THRESHOLD):
            raise RuntimeError(
                f"MANIFEST_CONSTANT_MISMATCH: max_drawdown_threshold={max_dd} "
                f"expected {self._EXPECTED_MAX_DRAWDOWN_THRESHOLD}."
            )
        if not self._floats_equal(vol_trig, self._EXPECTED_VOL_COMPRESSION_TRIGGER):
            raise RuntimeError(
                f"MANIFEST_CONSTANT_MISMATCH: vol_compression_trigger={vol_trig} "
                f"expected {self._EXPECTED_VOL_COMPRESSION_TRIGGER}."
            )

        # MVI-06: Return computed hash for propagation into ExecutionRecords.
        return computed_hash, thresholds

    def xǁManifestValidatorǁvalidate__mutmut_27(self) -> Tuple[str, Dict[str, Any]]:
        """
        Execute full manifest validation.

        Returns:
          (computed_hash, thresholds_dict)
          computed_hash -- SHA-256 hex digest of the manifest content.
          thresholds    -- dict from manifest["thresholds"] section.

        Raises RuntimeError with failure_type_id prefix on any hard failure.
        Failure types raised here:
          MANIFEST_HASH_MISMATCH    -- MVI-02
          MANIFEST_CONSTANT_MISMATCH -- MVI-04
          MANIFEST_TABLEHASH_PRESENT -- MVI-05
          INTEGRITY_FAILURE          -- missing file or parse error
        """
        # MVI-01: Load manifest file.
        if not self.manifest_path.exists():
            raise RuntimeError(
                "INTEGRITY_FAILURE: THRESHOLD_MANIFEST.json not found at "
                f"{self.manifest_path}. Harness cannot start without manifest."
            )

        try:
            with open(self.manifest_path, "r", encoding="utf-8") as f:
                raw = f.read()
            data = json.loads(raw)
        except Exception as exc:
            raise RuntimeError(
                f"INTEGRITY_FAILURE: Failed to load or parse THRESHOLD_MANIFEST.json: {exc}"
            ) from exc

        # MVI-01: Compute hash excluding manifest_hash field.
        data_for_hash = {k: v for k, v in data.items() if k != "manifest_hash"}
        computed_hash = hashlib.sha256(
            json.dumps(None, sort_keys=True, separators=(",", ":")).encode("utf-8")
        ).hexdigest()

        # MVI-02: Verify computed hash matches stored manifest_hash.
        stored_hash = data.get("manifest_hash", "")
        if (
            stored_hash
            and stored_hash != "BUILD_TIME_PLACEHOLDER"
            and stored_hash != computed_hash
        ):
            raise RuntimeError(
                f"MANIFEST_HASH_MISMATCH: Computed hash {computed_hash[:16]}... "
                f"does not match stored hash {stored_hash[:16]}... "
                "System start denied. Possible tampering."
            )

        # MVI-05: Check for absence of table_hash in joint_risk_multiplier_table.
        jrmt = data.get("joint_risk_multiplier_table", {})
        if "table_hash" in jrmt:
            raise RuntimeError(
                "MANIFEST_TABLEHASH_PRESENT: joint_risk_multiplier_table must not "
                "contain a table_hash key per Manifest Authority Policy."
            )

        # MVI-03: Extract the three FAS v6.1.0 constants.
        try:
            thresholds = data["thresholds"]
            shock_cap  = float(thresholds["shock_exposure_cap"])
            max_dd     = float(thresholds["max_drawdown_threshold"])
            vol_trig   = float(thresholds["vol_compression_trigger"])
        except (KeyError, ValueError) as exc:
            raise RuntimeError(
                f"INTEGRITY_FAILURE: Missing or invalid threshold key in manifest: {exc}"
            ) from exc

        # MVI-04: Verify the three extracted constants equal FAS v6.1.0 values.
        if not self._floats_equal(shock_cap, self._EXPECTED_SHOCK_EXPOSURE_CAP):
            raise RuntimeError(
                f"MANIFEST_CONSTANT_MISMATCH: shock_exposure_cap={shock_cap} "
                f"expected {self._EXPECTED_SHOCK_EXPOSURE_CAP}."
            )
        if not self._floats_equal(max_dd, self._EXPECTED_MAX_DRAWDOWN_THRESHOLD):
            raise RuntimeError(
                f"MANIFEST_CONSTANT_MISMATCH: max_drawdown_threshold={max_dd} "
                f"expected {self._EXPECTED_MAX_DRAWDOWN_THRESHOLD}."
            )
        if not self._floats_equal(vol_trig, self._EXPECTED_VOL_COMPRESSION_TRIGGER):
            raise RuntimeError(
                f"MANIFEST_CONSTANT_MISMATCH: vol_compression_trigger={vol_trig} "
                f"expected {self._EXPECTED_VOL_COMPRESSION_TRIGGER}."
            )

        # MVI-06: Return computed hash for propagation into ExecutionRecords.
        return computed_hash, thresholds

    def xǁManifestValidatorǁvalidate__mutmut_28(self) -> Tuple[str, Dict[str, Any]]:
        """
        Execute full manifest validation.

        Returns:
          (computed_hash, thresholds_dict)
          computed_hash -- SHA-256 hex digest of the manifest content.
          thresholds    -- dict from manifest["thresholds"] section.

        Raises RuntimeError with failure_type_id prefix on any hard failure.
        Failure types raised here:
          MANIFEST_HASH_MISMATCH    -- MVI-02
          MANIFEST_CONSTANT_MISMATCH -- MVI-04
          MANIFEST_TABLEHASH_PRESENT -- MVI-05
          INTEGRITY_FAILURE          -- missing file or parse error
        """
        # MVI-01: Load manifest file.
        if not self.manifest_path.exists():
            raise RuntimeError(
                "INTEGRITY_FAILURE: THRESHOLD_MANIFEST.json not found at "
                f"{self.manifest_path}. Harness cannot start without manifest."
            )

        try:
            with open(self.manifest_path, "r", encoding="utf-8") as f:
                raw = f.read()
            data = json.loads(raw)
        except Exception as exc:
            raise RuntimeError(
                f"INTEGRITY_FAILURE: Failed to load or parse THRESHOLD_MANIFEST.json: {exc}"
            ) from exc

        # MVI-01: Compute hash excluding manifest_hash field.
        data_for_hash = {k: v for k, v in data.items() if k != "manifest_hash"}
        computed_hash = hashlib.sha256(
            json.dumps(data_for_hash, sort_keys=None, separators=(",", ":")).encode("utf-8")
        ).hexdigest()

        # MVI-02: Verify computed hash matches stored manifest_hash.
        stored_hash = data.get("manifest_hash", "")
        if (
            stored_hash
            and stored_hash != "BUILD_TIME_PLACEHOLDER"
            and stored_hash != computed_hash
        ):
            raise RuntimeError(
                f"MANIFEST_HASH_MISMATCH: Computed hash {computed_hash[:16]}... "
                f"does not match stored hash {stored_hash[:16]}... "
                "System start denied. Possible tampering."
            )

        # MVI-05: Check for absence of table_hash in joint_risk_multiplier_table.
        jrmt = data.get("joint_risk_multiplier_table", {})
        if "table_hash" in jrmt:
            raise RuntimeError(
                "MANIFEST_TABLEHASH_PRESENT: joint_risk_multiplier_table must not "
                "contain a table_hash key per Manifest Authority Policy."
            )

        # MVI-03: Extract the three FAS v6.1.0 constants.
        try:
            thresholds = data["thresholds"]
            shock_cap  = float(thresholds["shock_exposure_cap"])
            max_dd     = float(thresholds["max_drawdown_threshold"])
            vol_trig   = float(thresholds["vol_compression_trigger"])
        except (KeyError, ValueError) as exc:
            raise RuntimeError(
                f"INTEGRITY_FAILURE: Missing or invalid threshold key in manifest: {exc}"
            ) from exc

        # MVI-04: Verify the three extracted constants equal FAS v6.1.0 values.
        if not self._floats_equal(shock_cap, self._EXPECTED_SHOCK_EXPOSURE_CAP):
            raise RuntimeError(
                f"MANIFEST_CONSTANT_MISMATCH: shock_exposure_cap={shock_cap} "
                f"expected {self._EXPECTED_SHOCK_EXPOSURE_CAP}."
            )
        if not self._floats_equal(max_dd, self._EXPECTED_MAX_DRAWDOWN_THRESHOLD):
            raise RuntimeError(
                f"MANIFEST_CONSTANT_MISMATCH: max_drawdown_threshold={max_dd} "
                f"expected {self._EXPECTED_MAX_DRAWDOWN_THRESHOLD}."
            )
        if not self._floats_equal(vol_trig, self._EXPECTED_VOL_COMPRESSION_TRIGGER):
            raise RuntimeError(
                f"MANIFEST_CONSTANT_MISMATCH: vol_compression_trigger={vol_trig} "
                f"expected {self._EXPECTED_VOL_COMPRESSION_TRIGGER}."
            )

        # MVI-06: Return computed hash for propagation into ExecutionRecords.
        return computed_hash, thresholds

    def xǁManifestValidatorǁvalidate__mutmut_29(self) -> Tuple[str, Dict[str, Any]]:
        """
        Execute full manifest validation.

        Returns:
          (computed_hash, thresholds_dict)
          computed_hash -- SHA-256 hex digest of the manifest content.
          thresholds    -- dict from manifest["thresholds"] section.

        Raises RuntimeError with failure_type_id prefix on any hard failure.
        Failure types raised here:
          MANIFEST_HASH_MISMATCH    -- MVI-02
          MANIFEST_CONSTANT_MISMATCH -- MVI-04
          MANIFEST_TABLEHASH_PRESENT -- MVI-05
          INTEGRITY_FAILURE          -- missing file or parse error
        """
        # MVI-01: Load manifest file.
        if not self.manifest_path.exists():
            raise RuntimeError(
                "INTEGRITY_FAILURE: THRESHOLD_MANIFEST.json not found at "
                f"{self.manifest_path}. Harness cannot start without manifest."
            )

        try:
            with open(self.manifest_path, "r", encoding="utf-8") as f:
                raw = f.read()
            data = json.loads(raw)
        except Exception as exc:
            raise RuntimeError(
                f"INTEGRITY_FAILURE: Failed to load or parse THRESHOLD_MANIFEST.json: {exc}"
            ) from exc

        # MVI-01: Compute hash excluding manifest_hash field.
        data_for_hash = {k: v for k, v in data.items() if k != "manifest_hash"}
        computed_hash = hashlib.sha256(
            json.dumps(data_for_hash, sort_keys=True, separators=None).encode("utf-8")
        ).hexdigest()

        # MVI-02: Verify computed hash matches stored manifest_hash.
        stored_hash = data.get("manifest_hash", "")
        if (
            stored_hash
            and stored_hash != "BUILD_TIME_PLACEHOLDER"
            and stored_hash != computed_hash
        ):
            raise RuntimeError(
                f"MANIFEST_HASH_MISMATCH: Computed hash {computed_hash[:16]}... "
                f"does not match stored hash {stored_hash[:16]}... "
                "System start denied. Possible tampering."
            )

        # MVI-05: Check for absence of table_hash in joint_risk_multiplier_table.
        jrmt = data.get("joint_risk_multiplier_table", {})
        if "table_hash" in jrmt:
            raise RuntimeError(
                "MANIFEST_TABLEHASH_PRESENT: joint_risk_multiplier_table must not "
                "contain a table_hash key per Manifest Authority Policy."
            )

        # MVI-03: Extract the three FAS v6.1.0 constants.
        try:
            thresholds = data["thresholds"]
            shock_cap  = float(thresholds["shock_exposure_cap"])
            max_dd     = float(thresholds["max_drawdown_threshold"])
            vol_trig   = float(thresholds["vol_compression_trigger"])
        except (KeyError, ValueError) as exc:
            raise RuntimeError(
                f"INTEGRITY_FAILURE: Missing or invalid threshold key in manifest: {exc}"
            ) from exc

        # MVI-04: Verify the three extracted constants equal FAS v6.1.0 values.
        if not self._floats_equal(shock_cap, self._EXPECTED_SHOCK_EXPOSURE_CAP):
            raise RuntimeError(
                f"MANIFEST_CONSTANT_MISMATCH: shock_exposure_cap={shock_cap} "
                f"expected {self._EXPECTED_SHOCK_EXPOSURE_CAP}."
            )
        if not self._floats_equal(max_dd, self._EXPECTED_MAX_DRAWDOWN_THRESHOLD):
            raise RuntimeError(
                f"MANIFEST_CONSTANT_MISMATCH: max_drawdown_threshold={max_dd} "
                f"expected {self._EXPECTED_MAX_DRAWDOWN_THRESHOLD}."
            )
        if not self._floats_equal(vol_trig, self._EXPECTED_VOL_COMPRESSION_TRIGGER):
            raise RuntimeError(
                f"MANIFEST_CONSTANT_MISMATCH: vol_compression_trigger={vol_trig} "
                f"expected {self._EXPECTED_VOL_COMPRESSION_TRIGGER}."
            )

        # MVI-06: Return computed hash for propagation into ExecutionRecords.
        return computed_hash, thresholds

    def xǁManifestValidatorǁvalidate__mutmut_30(self) -> Tuple[str, Dict[str, Any]]:
        """
        Execute full manifest validation.

        Returns:
          (computed_hash, thresholds_dict)
          computed_hash -- SHA-256 hex digest of the manifest content.
          thresholds    -- dict from manifest["thresholds"] section.

        Raises RuntimeError with failure_type_id prefix on any hard failure.
        Failure types raised here:
          MANIFEST_HASH_MISMATCH    -- MVI-02
          MANIFEST_CONSTANT_MISMATCH -- MVI-04
          MANIFEST_TABLEHASH_PRESENT -- MVI-05
          INTEGRITY_FAILURE          -- missing file or parse error
        """
        # MVI-01: Load manifest file.
        if not self.manifest_path.exists():
            raise RuntimeError(
                "INTEGRITY_FAILURE: THRESHOLD_MANIFEST.json not found at "
                f"{self.manifest_path}. Harness cannot start without manifest."
            )

        try:
            with open(self.manifest_path, "r", encoding="utf-8") as f:
                raw = f.read()
            data = json.loads(raw)
        except Exception as exc:
            raise RuntimeError(
                f"INTEGRITY_FAILURE: Failed to load or parse THRESHOLD_MANIFEST.json: {exc}"
            ) from exc

        # MVI-01: Compute hash excluding manifest_hash field.
        data_for_hash = {k: v for k, v in data.items() if k != "manifest_hash"}
        computed_hash = hashlib.sha256(
            json.dumps(sort_keys=True, separators=(",", ":")).encode("utf-8")
        ).hexdigest()

        # MVI-02: Verify computed hash matches stored manifest_hash.
        stored_hash = data.get("manifest_hash", "")
        if (
            stored_hash
            and stored_hash != "BUILD_TIME_PLACEHOLDER"
            and stored_hash != computed_hash
        ):
            raise RuntimeError(
                f"MANIFEST_HASH_MISMATCH: Computed hash {computed_hash[:16]}... "
                f"does not match stored hash {stored_hash[:16]}... "
                "System start denied. Possible tampering."
            )

        # MVI-05: Check for absence of table_hash in joint_risk_multiplier_table.
        jrmt = data.get("joint_risk_multiplier_table", {})
        if "table_hash" in jrmt:
            raise RuntimeError(
                "MANIFEST_TABLEHASH_PRESENT: joint_risk_multiplier_table must not "
                "contain a table_hash key per Manifest Authority Policy."
            )

        # MVI-03: Extract the three FAS v6.1.0 constants.
        try:
            thresholds = data["thresholds"]
            shock_cap  = float(thresholds["shock_exposure_cap"])
            max_dd     = float(thresholds["max_drawdown_threshold"])
            vol_trig   = float(thresholds["vol_compression_trigger"])
        except (KeyError, ValueError) as exc:
            raise RuntimeError(
                f"INTEGRITY_FAILURE: Missing or invalid threshold key in manifest: {exc}"
            ) from exc

        # MVI-04: Verify the three extracted constants equal FAS v6.1.0 values.
        if not self._floats_equal(shock_cap, self._EXPECTED_SHOCK_EXPOSURE_CAP):
            raise RuntimeError(
                f"MANIFEST_CONSTANT_MISMATCH: shock_exposure_cap={shock_cap} "
                f"expected {self._EXPECTED_SHOCK_EXPOSURE_CAP}."
            )
        if not self._floats_equal(max_dd, self._EXPECTED_MAX_DRAWDOWN_THRESHOLD):
            raise RuntimeError(
                f"MANIFEST_CONSTANT_MISMATCH: max_drawdown_threshold={max_dd} "
                f"expected {self._EXPECTED_MAX_DRAWDOWN_THRESHOLD}."
            )
        if not self._floats_equal(vol_trig, self._EXPECTED_VOL_COMPRESSION_TRIGGER):
            raise RuntimeError(
                f"MANIFEST_CONSTANT_MISMATCH: vol_compression_trigger={vol_trig} "
                f"expected {self._EXPECTED_VOL_COMPRESSION_TRIGGER}."
            )

        # MVI-06: Return computed hash for propagation into ExecutionRecords.
        return computed_hash, thresholds

    def xǁManifestValidatorǁvalidate__mutmut_31(self) -> Tuple[str, Dict[str, Any]]:
        """
        Execute full manifest validation.

        Returns:
          (computed_hash, thresholds_dict)
          computed_hash -- SHA-256 hex digest of the manifest content.
          thresholds    -- dict from manifest["thresholds"] section.

        Raises RuntimeError with failure_type_id prefix on any hard failure.
        Failure types raised here:
          MANIFEST_HASH_MISMATCH    -- MVI-02
          MANIFEST_CONSTANT_MISMATCH -- MVI-04
          MANIFEST_TABLEHASH_PRESENT -- MVI-05
          INTEGRITY_FAILURE          -- missing file or parse error
        """
        # MVI-01: Load manifest file.
        if not self.manifest_path.exists():
            raise RuntimeError(
                "INTEGRITY_FAILURE: THRESHOLD_MANIFEST.json not found at "
                f"{self.manifest_path}. Harness cannot start without manifest."
            )

        try:
            with open(self.manifest_path, "r", encoding="utf-8") as f:
                raw = f.read()
            data = json.loads(raw)
        except Exception as exc:
            raise RuntimeError(
                f"INTEGRITY_FAILURE: Failed to load or parse THRESHOLD_MANIFEST.json: {exc}"
            ) from exc

        # MVI-01: Compute hash excluding manifest_hash field.
        data_for_hash = {k: v for k, v in data.items() if k != "manifest_hash"}
        computed_hash = hashlib.sha256(
            json.dumps(data_for_hash, separators=(",", ":")).encode("utf-8")
        ).hexdigest()

        # MVI-02: Verify computed hash matches stored manifest_hash.
        stored_hash = data.get("manifest_hash", "")
        if (
            stored_hash
            and stored_hash != "BUILD_TIME_PLACEHOLDER"
            and stored_hash != computed_hash
        ):
            raise RuntimeError(
                f"MANIFEST_HASH_MISMATCH: Computed hash {computed_hash[:16]}... "
                f"does not match stored hash {stored_hash[:16]}... "
                "System start denied. Possible tampering."
            )

        # MVI-05: Check for absence of table_hash in joint_risk_multiplier_table.
        jrmt = data.get("joint_risk_multiplier_table", {})
        if "table_hash" in jrmt:
            raise RuntimeError(
                "MANIFEST_TABLEHASH_PRESENT: joint_risk_multiplier_table must not "
                "contain a table_hash key per Manifest Authority Policy."
            )

        # MVI-03: Extract the three FAS v6.1.0 constants.
        try:
            thresholds = data["thresholds"]
            shock_cap  = float(thresholds["shock_exposure_cap"])
            max_dd     = float(thresholds["max_drawdown_threshold"])
            vol_trig   = float(thresholds["vol_compression_trigger"])
        except (KeyError, ValueError) as exc:
            raise RuntimeError(
                f"INTEGRITY_FAILURE: Missing or invalid threshold key in manifest: {exc}"
            ) from exc

        # MVI-04: Verify the three extracted constants equal FAS v6.1.0 values.
        if not self._floats_equal(shock_cap, self._EXPECTED_SHOCK_EXPOSURE_CAP):
            raise RuntimeError(
                f"MANIFEST_CONSTANT_MISMATCH: shock_exposure_cap={shock_cap} "
                f"expected {self._EXPECTED_SHOCK_EXPOSURE_CAP}."
            )
        if not self._floats_equal(max_dd, self._EXPECTED_MAX_DRAWDOWN_THRESHOLD):
            raise RuntimeError(
                f"MANIFEST_CONSTANT_MISMATCH: max_drawdown_threshold={max_dd} "
                f"expected {self._EXPECTED_MAX_DRAWDOWN_THRESHOLD}."
            )
        if not self._floats_equal(vol_trig, self._EXPECTED_VOL_COMPRESSION_TRIGGER):
            raise RuntimeError(
                f"MANIFEST_CONSTANT_MISMATCH: vol_compression_trigger={vol_trig} "
                f"expected {self._EXPECTED_VOL_COMPRESSION_TRIGGER}."
            )

        # MVI-06: Return computed hash for propagation into ExecutionRecords.
        return computed_hash, thresholds

    def xǁManifestValidatorǁvalidate__mutmut_32(self) -> Tuple[str, Dict[str, Any]]:
        """
        Execute full manifest validation.

        Returns:
          (computed_hash, thresholds_dict)
          computed_hash -- SHA-256 hex digest of the manifest content.
          thresholds    -- dict from manifest["thresholds"] section.

        Raises RuntimeError with failure_type_id prefix on any hard failure.
        Failure types raised here:
          MANIFEST_HASH_MISMATCH    -- MVI-02
          MANIFEST_CONSTANT_MISMATCH -- MVI-04
          MANIFEST_TABLEHASH_PRESENT -- MVI-05
          INTEGRITY_FAILURE          -- missing file or parse error
        """
        # MVI-01: Load manifest file.
        if not self.manifest_path.exists():
            raise RuntimeError(
                "INTEGRITY_FAILURE: THRESHOLD_MANIFEST.json not found at "
                f"{self.manifest_path}. Harness cannot start without manifest."
            )

        try:
            with open(self.manifest_path, "r", encoding="utf-8") as f:
                raw = f.read()
            data = json.loads(raw)
        except Exception as exc:
            raise RuntimeError(
                f"INTEGRITY_FAILURE: Failed to load or parse THRESHOLD_MANIFEST.json: {exc}"
            ) from exc

        # MVI-01: Compute hash excluding manifest_hash field.
        data_for_hash = {k: v for k, v in data.items() if k != "manifest_hash"}
        computed_hash = hashlib.sha256(
            json.dumps(data_for_hash, sort_keys=True, ).encode("utf-8")
        ).hexdigest()

        # MVI-02: Verify computed hash matches stored manifest_hash.
        stored_hash = data.get("manifest_hash", "")
        if (
            stored_hash
            and stored_hash != "BUILD_TIME_PLACEHOLDER"
            and stored_hash != computed_hash
        ):
            raise RuntimeError(
                f"MANIFEST_HASH_MISMATCH: Computed hash {computed_hash[:16]}... "
                f"does not match stored hash {stored_hash[:16]}... "
                "System start denied. Possible tampering."
            )

        # MVI-05: Check for absence of table_hash in joint_risk_multiplier_table.
        jrmt = data.get("joint_risk_multiplier_table", {})
        if "table_hash" in jrmt:
            raise RuntimeError(
                "MANIFEST_TABLEHASH_PRESENT: joint_risk_multiplier_table must not "
                "contain a table_hash key per Manifest Authority Policy."
            )

        # MVI-03: Extract the three FAS v6.1.0 constants.
        try:
            thresholds = data["thresholds"]
            shock_cap  = float(thresholds["shock_exposure_cap"])
            max_dd     = float(thresholds["max_drawdown_threshold"])
            vol_trig   = float(thresholds["vol_compression_trigger"])
        except (KeyError, ValueError) as exc:
            raise RuntimeError(
                f"INTEGRITY_FAILURE: Missing or invalid threshold key in manifest: {exc}"
            ) from exc

        # MVI-04: Verify the three extracted constants equal FAS v6.1.0 values.
        if not self._floats_equal(shock_cap, self._EXPECTED_SHOCK_EXPOSURE_CAP):
            raise RuntimeError(
                f"MANIFEST_CONSTANT_MISMATCH: shock_exposure_cap={shock_cap} "
                f"expected {self._EXPECTED_SHOCK_EXPOSURE_CAP}."
            )
        if not self._floats_equal(max_dd, self._EXPECTED_MAX_DRAWDOWN_THRESHOLD):
            raise RuntimeError(
                f"MANIFEST_CONSTANT_MISMATCH: max_drawdown_threshold={max_dd} "
                f"expected {self._EXPECTED_MAX_DRAWDOWN_THRESHOLD}."
            )
        if not self._floats_equal(vol_trig, self._EXPECTED_VOL_COMPRESSION_TRIGGER):
            raise RuntimeError(
                f"MANIFEST_CONSTANT_MISMATCH: vol_compression_trigger={vol_trig} "
                f"expected {self._EXPECTED_VOL_COMPRESSION_TRIGGER}."
            )

        # MVI-06: Return computed hash for propagation into ExecutionRecords.
        return computed_hash, thresholds

    def xǁManifestValidatorǁvalidate__mutmut_33(self) -> Tuple[str, Dict[str, Any]]:
        """
        Execute full manifest validation.

        Returns:
          (computed_hash, thresholds_dict)
          computed_hash -- SHA-256 hex digest of the manifest content.
          thresholds    -- dict from manifest["thresholds"] section.

        Raises RuntimeError with failure_type_id prefix on any hard failure.
        Failure types raised here:
          MANIFEST_HASH_MISMATCH    -- MVI-02
          MANIFEST_CONSTANT_MISMATCH -- MVI-04
          MANIFEST_TABLEHASH_PRESENT -- MVI-05
          INTEGRITY_FAILURE          -- missing file or parse error
        """
        # MVI-01: Load manifest file.
        if not self.manifest_path.exists():
            raise RuntimeError(
                "INTEGRITY_FAILURE: THRESHOLD_MANIFEST.json not found at "
                f"{self.manifest_path}. Harness cannot start without manifest."
            )

        try:
            with open(self.manifest_path, "r", encoding="utf-8") as f:
                raw = f.read()
            data = json.loads(raw)
        except Exception as exc:
            raise RuntimeError(
                f"INTEGRITY_FAILURE: Failed to load or parse THRESHOLD_MANIFEST.json: {exc}"
            ) from exc

        # MVI-01: Compute hash excluding manifest_hash field.
        data_for_hash = {k: v for k, v in data.items() if k != "manifest_hash"}
        computed_hash = hashlib.sha256(
            json.dumps(data_for_hash, sort_keys=False, separators=(",", ":")).encode("utf-8")
        ).hexdigest()

        # MVI-02: Verify computed hash matches stored manifest_hash.
        stored_hash = data.get("manifest_hash", "")
        if (
            stored_hash
            and stored_hash != "BUILD_TIME_PLACEHOLDER"
            and stored_hash != computed_hash
        ):
            raise RuntimeError(
                f"MANIFEST_HASH_MISMATCH: Computed hash {computed_hash[:16]}... "
                f"does not match stored hash {stored_hash[:16]}... "
                "System start denied. Possible tampering."
            )

        # MVI-05: Check for absence of table_hash in joint_risk_multiplier_table.
        jrmt = data.get("joint_risk_multiplier_table", {})
        if "table_hash" in jrmt:
            raise RuntimeError(
                "MANIFEST_TABLEHASH_PRESENT: joint_risk_multiplier_table must not "
                "contain a table_hash key per Manifest Authority Policy."
            )

        # MVI-03: Extract the three FAS v6.1.0 constants.
        try:
            thresholds = data["thresholds"]
            shock_cap  = float(thresholds["shock_exposure_cap"])
            max_dd     = float(thresholds["max_drawdown_threshold"])
            vol_trig   = float(thresholds["vol_compression_trigger"])
        except (KeyError, ValueError) as exc:
            raise RuntimeError(
                f"INTEGRITY_FAILURE: Missing or invalid threshold key in manifest: {exc}"
            ) from exc

        # MVI-04: Verify the three extracted constants equal FAS v6.1.0 values.
        if not self._floats_equal(shock_cap, self._EXPECTED_SHOCK_EXPOSURE_CAP):
            raise RuntimeError(
                f"MANIFEST_CONSTANT_MISMATCH: shock_exposure_cap={shock_cap} "
                f"expected {self._EXPECTED_SHOCK_EXPOSURE_CAP}."
            )
        if not self._floats_equal(max_dd, self._EXPECTED_MAX_DRAWDOWN_THRESHOLD):
            raise RuntimeError(
                f"MANIFEST_CONSTANT_MISMATCH: max_drawdown_threshold={max_dd} "
                f"expected {self._EXPECTED_MAX_DRAWDOWN_THRESHOLD}."
            )
        if not self._floats_equal(vol_trig, self._EXPECTED_VOL_COMPRESSION_TRIGGER):
            raise RuntimeError(
                f"MANIFEST_CONSTANT_MISMATCH: vol_compression_trigger={vol_trig} "
                f"expected {self._EXPECTED_VOL_COMPRESSION_TRIGGER}."
            )

        # MVI-06: Return computed hash for propagation into ExecutionRecords.
        return computed_hash, thresholds

    def xǁManifestValidatorǁvalidate__mutmut_34(self) -> Tuple[str, Dict[str, Any]]:
        """
        Execute full manifest validation.

        Returns:
          (computed_hash, thresholds_dict)
          computed_hash -- SHA-256 hex digest of the manifest content.
          thresholds    -- dict from manifest["thresholds"] section.

        Raises RuntimeError with failure_type_id prefix on any hard failure.
        Failure types raised here:
          MANIFEST_HASH_MISMATCH    -- MVI-02
          MANIFEST_CONSTANT_MISMATCH -- MVI-04
          MANIFEST_TABLEHASH_PRESENT -- MVI-05
          INTEGRITY_FAILURE          -- missing file or parse error
        """
        # MVI-01: Load manifest file.
        if not self.manifest_path.exists():
            raise RuntimeError(
                "INTEGRITY_FAILURE: THRESHOLD_MANIFEST.json not found at "
                f"{self.manifest_path}. Harness cannot start without manifest."
            )

        try:
            with open(self.manifest_path, "r", encoding="utf-8") as f:
                raw = f.read()
            data = json.loads(raw)
        except Exception as exc:
            raise RuntimeError(
                f"INTEGRITY_FAILURE: Failed to load or parse THRESHOLD_MANIFEST.json: {exc}"
            ) from exc

        # MVI-01: Compute hash excluding manifest_hash field.
        data_for_hash = {k: v for k, v in data.items() if k != "manifest_hash"}
        computed_hash = hashlib.sha256(
            json.dumps(data_for_hash, sort_keys=True, separators=("XX,XX", ":")).encode("utf-8")
        ).hexdigest()

        # MVI-02: Verify computed hash matches stored manifest_hash.
        stored_hash = data.get("manifest_hash", "")
        if (
            stored_hash
            and stored_hash != "BUILD_TIME_PLACEHOLDER"
            and stored_hash != computed_hash
        ):
            raise RuntimeError(
                f"MANIFEST_HASH_MISMATCH: Computed hash {computed_hash[:16]}... "
                f"does not match stored hash {stored_hash[:16]}... "
                "System start denied. Possible tampering."
            )

        # MVI-05: Check for absence of table_hash in joint_risk_multiplier_table.
        jrmt = data.get("joint_risk_multiplier_table", {})
        if "table_hash" in jrmt:
            raise RuntimeError(
                "MANIFEST_TABLEHASH_PRESENT: joint_risk_multiplier_table must not "
                "contain a table_hash key per Manifest Authority Policy."
            )

        # MVI-03: Extract the three FAS v6.1.0 constants.
        try:
            thresholds = data["thresholds"]
            shock_cap  = float(thresholds["shock_exposure_cap"])
            max_dd     = float(thresholds["max_drawdown_threshold"])
            vol_trig   = float(thresholds["vol_compression_trigger"])
        except (KeyError, ValueError) as exc:
            raise RuntimeError(
                f"INTEGRITY_FAILURE: Missing or invalid threshold key in manifest: {exc}"
            ) from exc

        # MVI-04: Verify the three extracted constants equal FAS v6.1.0 values.
        if not self._floats_equal(shock_cap, self._EXPECTED_SHOCK_EXPOSURE_CAP):
            raise RuntimeError(
                f"MANIFEST_CONSTANT_MISMATCH: shock_exposure_cap={shock_cap} "
                f"expected {self._EXPECTED_SHOCK_EXPOSURE_CAP}."
            )
        if not self._floats_equal(max_dd, self._EXPECTED_MAX_DRAWDOWN_THRESHOLD):
            raise RuntimeError(
                f"MANIFEST_CONSTANT_MISMATCH: max_drawdown_threshold={max_dd} "
                f"expected {self._EXPECTED_MAX_DRAWDOWN_THRESHOLD}."
            )
        if not self._floats_equal(vol_trig, self._EXPECTED_VOL_COMPRESSION_TRIGGER):
            raise RuntimeError(
                f"MANIFEST_CONSTANT_MISMATCH: vol_compression_trigger={vol_trig} "
                f"expected {self._EXPECTED_VOL_COMPRESSION_TRIGGER}."
            )

        # MVI-06: Return computed hash for propagation into ExecutionRecords.
        return computed_hash, thresholds

    def xǁManifestValidatorǁvalidate__mutmut_35(self) -> Tuple[str, Dict[str, Any]]:
        """
        Execute full manifest validation.

        Returns:
          (computed_hash, thresholds_dict)
          computed_hash -- SHA-256 hex digest of the manifest content.
          thresholds    -- dict from manifest["thresholds"] section.

        Raises RuntimeError with failure_type_id prefix on any hard failure.
        Failure types raised here:
          MANIFEST_HASH_MISMATCH    -- MVI-02
          MANIFEST_CONSTANT_MISMATCH -- MVI-04
          MANIFEST_TABLEHASH_PRESENT -- MVI-05
          INTEGRITY_FAILURE          -- missing file or parse error
        """
        # MVI-01: Load manifest file.
        if not self.manifest_path.exists():
            raise RuntimeError(
                "INTEGRITY_FAILURE: THRESHOLD_MANIFEST.json not found at "
                f"{self.manifest_path}. Harness cannot start without manifest."
            )

        try:
            with open(self.manifest_path, "r", encoding="utf-8") as f:
                raw = f.read()
            data = json.loads(raw)
        except Exception as exc:
            raise RuntimeError(
                f"INTEGRITY_FAILURE: Failed to load or parse THRESHOLD_MANIFEST.json: {exc}"
            ) from exc

        # MVI-01: Compute hash excluding manifest_hash field.
        data_for_hash = {k: v for k, v in data.items() if k != "manifest_hash"}
        computed_hash = hashlib.sha256(
            json.dumps(data_for_hash, sort_keys=True, separators=(",", "XX:XX")).encode("utf-8")
        ).hexdigest()

        # MVI-02: Verify computed hash matches stored manifest_hash.
        stored_hash = data.get("manifest_hash", "")
        if (
            stored_hash
            and stored_hash != "BUILD_TIME_PLACEHOLDER"
            and stored_hash != computed_hash
        ):
            raise RuntimeError(
                f"MANIFEST_HASH_MISMATCH: Computed hash {computed_hash[:16]}... "
                f"does not match stored hash {stored_hash[:16]}... "
                "System start denied. Possible tampering."
            )

        # MVI-05: Check for absence of table_hash in joint_risk_multiplier_table.
        jrmt = data.get("joint_risk_multiplier_table", {})
        if "table_hash" in jrmt:
            raise RuntimeError(
                "MANIFEST_TABLEHASH_PRESENT: joint_risk_multiplier_table must not "
                "contain a table_hash key per Manifest Authority Policy."
            )

        # MVI-03: Extract the three FAS v6.1.0 constants.
        try:
            thresholds = data["thresholds"]
            shock_cap  = float(thresholds["shock_exposure_cap"])
            max_dd     = float(thresholds["max_drawdown_threshold"])
            vol_trig   = float(thresholds["vol_compression_trigger"])
        except (KeyError, ValueError) as exc:
            raise RuntimeError(
                f"INTEGRITY_FAILURE: Missing or invalid threshold key in manifest: {exc}"
            ) from exc

        # MVI-04: Verify the three extracted constants equal FAS v6.1.0 values.
        if not self._floats_equal(shock_cap, self._EXPECTED_SHOCK_EXPOSURE_CAP):
            raise RuntimeError(
                f"MANIFEST_CONSTANT_MISMATCH: shock_exposure_cap={shock_cap} "
                f"expected {self._EXPECTED_SHOCK_EXPOSURE_CAP}."
            )
        if not self._floats_equal(max_dd, self._EXPECTED_MAX_DRAWDOWN_THRESHOLD):
            raise RuntimeError(
                f"MANIFEST_CONSTANT_MISMATCH: max_drawdown_threshold={max_dd} "
                f"expected {self._EXPECTED_MAX_DRAWDOWN_THRESHOLD}."
            )
        if not self._floats_equal(vol_trig, self._EXPECTED_VOL_COMPRESSION_TRIGGER):
            raise RuntimeError(
                f"MANIFEST_CONSTANT_MISMATCH: vol_compression_trigger={vol_trig} "
                f"expected {self._EXPECTED_VOL_COMPRESSION_TRIGGER}."
            )

        # MVI-06: Return computed hash for propagation into ExecutionRecords.
        return computed_hash, thresholds

    def xǁManifestValidatorǁvalidate__mutmut_36(self) -> Tuple[str, Dict[str, Any]]:
        """
        Execute full manifest validation.

        Returns:
          (computed_hash, thresholds_dict)
          computed_hash -- SHA-256 hex digest of the manifest content.
          thresholds    -- dict from manifest["thresholds"] section.

        Raises RuntimeError with failure_type_id prefix on any hard failure.
        Failure types raised here:
          MANIFEST_HASH_MISMATCH    -- MVI-02
          MANIFEST_CONSTANT_MISMATCH -- MVI-04
          MANIFEST_TABLEHASH_PRESENT -- MVI-05
          INTEGRITY_FAILURE          -- missing file or parse error
        """
        # MVI-01: Load manifest file.
        if not self.manifest_path.exists():
            raise RuntimeError(
                "INTEGRITY_FAILURE: THRESHOLD_MANIFEST.json not found at "
                f"{self.manifest_path}. Harness cannot start without manifest."
            )

        try:
            with open(self.manifest_path, "r", encoding="utf-8") as f:
                raw = f.read()
            data = json.loads(raw)
        except Exception as exc:
            raise RuntimeError(
                f"INTEGRITY_FAILURE: Failed to load or parse THRESHOLD_MANIFEST.json: {exc}"
            ) from exc

        # MVI-01: Compute hash excluding manifest_hash field.
        data_for_hash = {k: v for k, v in data.items() if k != "manifest_hash"}
        computed_hash = hashlib.sha256(
            json.dumps(data_for_hash, sort_keys=True, separators=(",", ":")).encode("XXutf-8XX")
        ).hexdigest()

        # MVI-02: Verify computed hash matches stored manifest_hash.
        stored_hash = data.get("manifest_hash", "")
        if (
            stored_hash
            and stored_hash != "BUILD_TIME_PLACEHOLDER"
            and stored_hash != computed_hash
        ):
            raise RuntimeError(
                f"MANIFEST_HASH_MISMATCH: Computed hash {computed_hash[:16]}... "
                f"does not match stored hash {stored_hash[:16]}... "
                "System start denied. Possible tampering."
            )

        # MVI-05: Check for absence of table_hash in joint_risk_multiplier_table.
        jrmt = data.get("joint_risk_multiplier_table", {})
        if "table_hash" in jrmt:
            raise RuntimeError(
                "MANIFEST_TABLEHASH_PRESENT: joint_risk_multiplier_table must not "
                "contain a table_hash key per Manifest Authority Policy."
            )

        # MVI-03: Extract the three FAS v6.1.0 constants.
        try:
            thresholds = data["thresholds"]
            shock_cap  = float(thresholds["shock_exposure_cap"])
            max_dd     = float(thresholds["max_drawdown_threshold"])
            vol_trig   = float(thresholds["vol_compression_trigger"])
        except (KeyError, ValueError) as exc:
            raise RuntimeError(
                f"INTEGRITY_FAILURE: Missing or invalid threshold key in manifest: {exc}"
            ) from exc

        # MVI-04: Verify the three extracted constants equal FAS v6.1.0 values.
        if not self._floats_equal(shock_cap, self._EXPECTED_SHOCK_EXPOSURE_CAP):
            raise RuntimeError(
                f"MANIFEST_CONSTANT_MISMATCH: shock_exposure_cap={shock_cap} "
                f"expected {self._EXPECTED_SHOCK_EXPOSURE_CAP}."
            )
        if not self._floats_equal(max_dd, self._EXPECTED_MAX_DRAWDOWN_THRESHOLD):
            raise RuntimeError(
                f"MANIFEST_CONSTANT_MISMATCH: max_drawdown_threshold={max_dd} "
                f"expected {self._EXPECTED_MAX_DRAWDOWN_THRESHOLD}."
            )
        if not self._floats_equal(vol_trig, self._EXPECTED_VOL_COMPRESSION_TRIGGER):
            raise RuntimeError(
                f"MANIFEST_CONSTANT_MISMATCH: vol_compression_trigger={vol_trig} "
                f"expected {self._EXPECTED_VOL_COMPRESSION_TRIGGER}."
            )

        # MVI-06: Return computed hash for propagation into ExecutionRecords.
        return computed_hash, thresholds

    def xǁManifestValidatorǁvalidate__mutmut_37(self) -> Tuple[str, Dict[str, Any]]:
        """
        Execute full manifest validation.

        Returns:
          (computed_hash, thresholds_dict)
          computed_hash -- SHA-256 hex digest of the manifest content.
          thresholds    -- dict from manifest["thresholds"] section.

        Raises RuntimeError with failure_type_id prefix on any hard failure.
        Failure types raised here:
          MANIFEST_HASH_MISMATCH    -- MVI-02
          MANIFEST_CONSTANT_MISMATCH -- MVI-04
          MANIFEST_TABLEHASH_PRESENT -- MVI-05
          INTEGRITY_FAILURE          -- missing file or parse error
        """
        # MVI-01: Load manifest file.
        if not self.manifest_path.exists():
            raise RuntimeError(
                "INTEGRITY_FAILURE: THRESHOLD_MANIFEST.json not found at "
                f"{self.manifest_path}. Harness cannot start without manifest."
            )

        try:
            with open(self.manifest_path, "r", encoding="utf-8") as f:
                raw = f.read()
            data = json.loads(raw)
        except Exception as exc:
            raise RuntimeError(
                f"INTEGRITY_FAILURE: Failed to load or parse THRESHOLD_MANIFEST.json: {exc}"
            ) from exc

        # MVI-01: Compute hash excluding manifest_hash field.
        data_for_hash = {k: v for k, v in data.items() if k != "manifest_hash"}
        computed_hash = hashlib.sha256(
            json.dumps(data_for_hash, sort_keys=True, separators=(",", ":")).encode("UTF-8")
        ).hexdigest()

        # MVI-02: Verify computed hash matches stored manifest_hash.
        stored_hash = data.get("manifest_hash", "")
        if (
            stored_hash
            and stored_hash != "BUILD_TIME_PLACEHOLDER"
            and stored_hash != computed_hash
        ):
            raise RuntimeError(
                f"MANIFEST_HASH_MISMATCH: Computed hash {computed_hash[:16]}... "
                f"does not match stored hash {stored_hash[:16]}... "
                "System start denied. Possible tampering."
            )

        # MVI-05: Check for absence of table_hash in joint_risk_multiplier_table.
        jrmt = data.get("joint_risk_multiplier_table", {})
        if "table_hash" in jrmt:
            raise RuntimeError(
                "MANIFEST_TABLEHASH_PRESENT: joint_risk_multiplier_table must not "
                "contain a table_hash key per Manifest Authority Policy."
            )

        # MVI-03: Extract the three FAS v6.1.0 constants.
        try:
            thresholds = data["thresholds"]
            shock_cap  = float(thresholds["shock_exposure_cap"])
            max_dd     = float(thresholds["max_drawdown_threshold"])
            vol_trig   = float(thresholds["vol_compression_trigger"])
        except (KeyError, ValueError) as exc:
            raise RuntimeError(
                f"INTEGRITY_FAILURE: Missing or invalid threshold key in manifest: {exc}"
            ) from exc

        # MVI-04: Verify the three extracted constants equal FAS v6.1.0 values.
        if not self._floats_equal(shock_cap, self._EXPECTED_SHOCK_EXPOSURE_CAP):
            raise RuntimeError(
                f"MANIFEST_CONSTANT_MISMATCH: shock_exposure_cap={shock_cap} "
                f"expected {self._EXPECTED_SHOCK_EXPOSURE_CAP}."
            )
        if not self._floats_equal(max_dd, self._EXPECTED_MAX_DRAWDOWN_THRESHOLD):
            raise RuntimeError(
                f"MANIFEST_CONSTANT_MISMATCH: max_drawdown_threshold={max_dd} "
                f"expected {self._EXPECTED_MAX_DRAWDOWN_THRESHOLD}."
            )
        if not self._floats_equal(vol_trig, self._EXPECTED_VOL_COMPRESSION_TRIGGER):
            raise RuntimeError(
                f"MANIFEST_CONSTANT_MISMATCH: vol_compression_trigger={vol_trig} "
                f"expected {self._EXPECTED_VOL_COMPRESSION_TRIGGER}."
            )

        # MVI-06: Return computed hash for propagation into ExecutionRecords.
        return computed_hash, thresholds

    def xǁManifestValidatorǁvalidate__mutmut_38(self) -> Tuple[str, Dict[str, Any]]:
        """
        Execute full manifest validation.

        Returns:
          (computed_hash, thresholds_dict)
          computed_hash -- SHA-256 hex digest of the manifest content.
          thresholds    -- dict from manifest["thresholds"] section.

        Raises RuntimeError with failure_type_id prefix on any hard failure.
        Failure types raised here:
          MANIFEST_HASH_MISMATCH    -- MVI-02
          MANIFEST_CONSTANT_MISMATCH -- MVI-04
          MANIFEST_TABLEHASH_PRESENT -- MVI-05
          INTEGRITY_FAILURE          -- missing file or parse error
        """
        # MVI-01: Load manifest file.
        if not self.manifest_path.exists():
            raise RuntimeError(
                "INTEGRITY_FAILURE: THRESHOLD_MANIFEST.json not found at "
                f"{self.manifest_path}. Harness cannot start without manifest."
            )

        try:
            with open(self.manifest_path, "r", encoding="utf-8") as f:
                raw = f.read()
            data = json.loads(raw)
        except Exception as exc:
            raise RuntimeError(
                f"INTEGRITY_FAILURE: Failed to load or parse THRESHOLD_MANIFEST.json: {exc}"
            ) from exc

        # MVI-01: Compute hash excluding manifest_hash field.
        data_for_hash = {k: v for k, v in data.items() if k != "manifest_hash"}
        computed_hash = hashlib.sha256(
            json.dumps(data_for_hash, sort_keys=True, separators=(",", ":")).encode("utf-8")
        ).hexdigest()

        # MVI-02: Verify computed hash matches stored manifest_hash.
        stored_hash = None
        if (
            stored_hash
            and stored_hash != "BUILD_TIME_PLACEHOLDER"
            and stored_hash != computed_hash
        ):
            raise RuntimeError(
                f"MANIFEST_HASH_MISMATCH: Computed hash {computed_hash[:16]}... "
                f"does not match stored hash {stored_hash[:16]}... "
                "System start denied. Possible tampering."
            )

        # MVI-05: Check for absence of table_hash in joint_risk_multiplier_table.
        jrmt = data.get("joint_risk_multiplier_table", {})
        if "table_hash" in jrmt:
            raise RuntimeError(
                "MANIFEST_TABLEHASH_PRESENT: joint_risk_multiplier_table must not "
                "contain a table_hash key per Manifest Authority Policy."
            )

        # MVI-03: Extract the three FAS v6.1.0 constants.
        try:
            thresholds = data["thresholds"]
            shock_cap  = float(thresholds["shock_exposure_cap"])
            max_dd     = float(thresholds["max_drawdown_threshold"])
            vol_trig   = float(thresholds["vol_compression_trigger"])
        except (KeyError, ValueError) as exc:
            raise RuntimeError(
                f"INTEGRITY_FAILURE: Missing or invalid threshold key in manifest: {exc}"
            ) from exc

        # MVI-04: Verify the three extracted constants equal FAS v6.1.0 values.
        if not self._floats_equal(shock_cap, self._EXPECTED_SHOCK_EXPOSURE_CAP):
            raise RuntimeError(
                f"MANIFEST_CONSTANT_MISMATCH: shock_exposure_cap={shock_cap} "
                f"expected {self._EXPECTED_SHOCK_EXPOSURE_CAP}."
            )
        if not self._floats_equal(max_dd, self._EXPECTED_MAX_DRAWDOWN_THRESHOLD):
            raise RuntimeError(
                f"MANIFEST_CONSTANT_MISMATCH: max_drawdown_threshold={max_dd} "
                f"expected {self._EXPECTED_MAX_DRAWDOWN_THRESHOLD}."
            )
        if not self._floats_equal(vol_trig, self._EXPECTED_VOL_COMPRESSION_TRIGGER):
            raise RuntimeError(
                f"MANIFEST_CONSTANT_MISMATCH: vol_compression_trigger={vol_trig} "
                f"expected {self._EXPECTED_VOL_COMPRESSION_TRIGGER}."
            )

        # MVI-06: Return computed hash for propagation into ExecutionRecords.
        return computed_hash, thresholds

    def xǁManifestValidatorǁvalidate__mutmut_39(self) -> Tuple[str, Dict[str, Any]]:
        """
        Execute full manifest validation.

        Returns:
          (computed_hash, thresholds_dict)
          computed_hash -- SHA-256 hex digest of the manifest content.
          thresholds    -- dict from manifest["thresholds"] section.

        Raises RuntimeError with failure_type_id prefix on any hard failure.
        Failure types raised here:
          MANIFEST_HASH_MISMATCH    -- MVI-02
          MANIFEST_CONSTANT_MISMATCH -- MVI-04
          MANIFEST_TABLEHASH_PRESENT -- MVI-05
          INTEGRITY_FAILURE          -- missing file or parse error
        """
        # MVI-01: Load manifest file.
        if not self.manifest_path.exists():
            raise RuntimeError(
                "INTEGRITY_FAILURE: THRESHOLD_MANIFEST.json not found at "
                f"{self.manifest_path}. Harness cannot start without manifest."
            )

        try:
            with open(self.manifest_path, "r", encoding="utf-8") as f:
                raw = f.read()
            data = json.loads(raw)
        except Exception as exc:
            raise RuntimeError(
                f"INTEGRITY_FAILURE: Failed to load or parse THRESHOLD_MANIFEST.json: {exc}"
            ) from exc

        # MVI-01: Compute hash excluding manifest_hash field.
        data_for_hash = {k: v for k, v in data.items() if k != "manifest_hash"}
        computed_hash = hashlib.sha256(
            json.dumps(data_for_hash, sort_keys=True, separators=(",", ":")).encode("utf-8")
        ).hexdigest()

        # MVI-02: Verify computed hash matches stored manifest_hash.
        stored_hash = data.get(None, "")
        if (
            stored_hash
            and stored_hash != "BUILD_TIME_PLACEHOLDER"
            and stored_hash != computed_hash
        ):
            raise RuntimeError(
                f"MANIFEST_HASH_MISMATCH: Computed hash {computed_hash[:16]}... "
                f"does not match stored hash {stored_hash[:16]}... "
                "System start denied. Possible tampering."
            )

        # MVI-05: Check for absence of table_hash in joint_risk_multiplier_table.
        jrmt = data.get("joint_risk_multiplier_table", {})
        if "table_hash" in jrmt:
            raise RuntimeError(
                "MANIFEST_TABLEHASH_PRESENT: joint_risk_multiplier_table must not "
                "contain a table_hash key per Manifest Authority Policy."
            )

        # MVI-03: Extract the three FAS v6.1.0 constants.
        try:
            thresholds = data["thresholds"]
            shock_cap  = float(thresholds["shock_exposure_cap"])
            max_dd     = float(thresholds["max_drawdown_threshold"])
            vol_trig   = float(thresholds["vol_compression_trigger"])
        except (KeyError, ValueError) as exc:
            raise RuntimeError(
                f"INTEGRITY_FAILURE: Missing or invalid threshold key in manifest: {exc}"
            ) from exc

        # MVI-04: Verify the three extracted constants equal FAS v6.1.0 values.
        if not self._floats_equal(shock_cap, self._EXPECTED_SHOCK_EXPOSURE_CAP):
            raise RuntimeError(
                f"MANIFEST_CONSTANT_MISMATCH: shock_exposure_cap={shock_cap} "
                f"expected {self._EXPECTED_SHOCK_EXPOSURE_CAP}."
            )
        if not self._floats_equal(max_dd, self._EXPECTED_MAX_DRAWDOWN_THRESHOLD):
            raise RuntimeError(
                f"MANIFEST_CONSTANT_MISMATCH: max_drawdown_threshold={max_dd} "
                f"expected {self._EXPECTED_MAX_DRAWDOWN_THRESHOLD}."
            )
        if not self._floats_equal(vol_trig, self._EXPECTED_VOL_COMPRESSION_TRIGGER):
            raise RuntimeError(
                f"MANIFEST_CONSTANT_MISMATCH: vol_compression_trigger={vol_trig} "
                f"expected {self._EXPECTED_VOL_COMPRESSION_TRIGGER}."
            )

        # MVI-06: Return computed hash for propagation into ExecutionRecords.
        return computed_hash, thresholds

    def xǁManifestValidatorǁvalidate__mutmut_40(self) -> Tuple[str, Dict[str, Any]]:
        """
        Execute full manifest validation.

        Returns:
          (computed_hash, thresholds_dict)
          computed_hash -- SHA-256 hex digest of the manifest content.
          thresholds    -- dict from manifest["thresholds"] section.

        Raises RuntimeError with failure_type_id prefix on any hard failure.
        Failure types raised here:
          MANIFEST_HASH_MISMATCH    -- MVI-02
          MANIFEST_CONSTANT_MISMATCH -- MVI-04
          MANIFEST_TABLEHASH_PRESENT -- MVI-05
          INTEGRITY_FAILURE          -- missing file or parse error
        """
        # MVI-01: Load manifest file.
        if not self.manifest_path.exists():
            raise RuntimeError(
                "INTEGRITY_FAILURE: THRESHOLD_MANIFEST.json not found at "
                f"{self.manifest_path}. Harness cannot start without manifest."
            )

        try:
            with open(self.manifest_path, "r", encoding="utf-8") as f:
                raw = f.read()
            data = json.loads(raw)
        except Exception as exc:
            raise RuntimeError(
                f"INTEGRITY_FAILURE: Failed to load or parse THRESHOLD_MANIFEST.json: {exc}"
            ) from exc

        # MVI-01: Compute hash excluding manifest_hash field.
        data_for_hash = {k: v for k, v in data.items() if k != "manifest_hash"}
        computed_hash = hashlib.sha256(
            json.dumps(data_for_hash, sort_keys=True, separators=(",", ":")).encode("utf-8")
        ).hexdigest()

        # MVI-02: Verify computed hash matches stored manifest_hash.
        stored_hash = data.get("manifest_hash", None)
        if (
            stored_hash
            and stored_hash != "BUILD_TIME_PLACEHOLDER"
            and stored_hash != computed_hash
        ):
            raise RuntimeError(
                f"MANIFEST_HASH_MISMATCH: Computed hash {computed_hash[:16]}... "
                f"does not match stored hash {stored_hash[:16]}... "
                "System start denied. Possible tampering."
            )

        # MVI-05: Check for absence of table_hash in joint_risk_multiplier_table.
        jrmt = data.get("joint_risk_multiplier_table", {})
        if "table_hash" in jrmt:
            raise RuntimeError(
                "MANIFEST_TABLEHASH_PRESENT: joint_risk_multiplier_table must not "
                "contain a table_hash key per Manifest Authority Policy."
            )

        # MVI-03: Extract the three FAS v6.1.0 constants.
        try:
            thresholds = data["thresholds"]
            shock_cap  = float(thresholds["shock_exposure_cap"])
            max_dd     = float(thresholds["max_drawdown_threshold"])
            vol_trig   = float(thresholds["vol_compression_trigger"])
        except (KeyError, ValueError) as exc:
            raise RuntimeError(
                f"INTEGRITY_FAILURE: Missing or invalid threshold key in manifest: {exc}"
            ) from exc

        # MVI-04: Verify the three extracted constants equal FAS v6.1.0 values.
        if not self._floats_equal(shock_cap, self._EXPECTED_SHOCK_EXPOSURE_CAP):
            raise RuntimeError(
                f"MANIFEST_CONSTANT_MISMATCH: shock_exposure_cap={shock_cap} "
                f"expected {self._EXPECTED_SHOCK_EXPOSURE_CAP}."
            )
        if not self._floats_equal(max_dd, self._EXPECTED_MAX_DRAWDOWN_THRESHOLD):
            raise RuntimeError(
                f"MANIFEST_CONSTANT_MISMATCH: max_drawdown_threshold={max_dd} "
                f"expected {self._EXPECTED_MAX_DRAWDOWN_THRESHOLD}."
            )
        if not self._floats_equal(vol_trig, self._EXPECTED_VOL_COMPRESSION_TRIGGER):
            raise RuntimeError(
                f"MANIFEST_CONSTANT_MISMATCH: vol_compression_trigger={vol_trig} "
                f"expected {self._EXPECTED_VOL_COMPRESSION_TRIGGER}."
            )

        # MVI-06: Return computed hash for propagation into ExecutionRecords.
        return computed_hash, thresholds

    def xǁManifestValidatorǁvalidate__mutmut_41(self) -> Tuple[str, Dict[str, Any]]:
        """
        Execute full manifest validation.

        Returns:
          (computed_hash, thresholds_dict)
          computed_hash -- SHA-256 hex digest of the manifest content.
          thresholds    -- dict from manifest["thresholds"] section.

        Raises RuntimeError with failure_type_id prefix on any hard failure.
        Failure types raised here:
          MANIFEST_HASH_MISMATCH    -- MVI-02
          MANIFEST_CONSTANT_MISMATCH -- MVI-04
          MANIFEST_TABLEHASH_PRESENT -- MVI-05
          INTEGRITY_FAILURE          -- missing file or parse error
        """
        # MVI-01: Load manifest file.
        if not self.manifest_path.exists():
            raise RuntimeError(
                "INTEGRITY_FAILURE: THRESHOLD_MANIFEST.json not found at "
                f"{self.manifest_path}. Harness cannot start without manifest."
            )

        try:
            with open(self.manifest_path, "r", encoding="utf-8") as f:
                raw = f.read()
            data = json.loads(raw)
        except Exception as exc:
            raise RuntimeError(
                f"INTEGRITY_FAILURE: Failed to load or parse THRESHOLD_MANIFEST.json: {exc}"
            ) from exc

        # MVI-01: Compute hash excluding manifest_hash field.
        data_for_hash = {k: v for k, v in data.items() if k != "manifest_hash"}
        computed_hash = hashlib.sha256(
            json.dumps(data_for_hash, sort_keys=True, separators=(",", ":")).encode("utf-8")
        ).hexdigest()

        # MVI-02: Verify computed hash matches stored manifest_hash.
        stored_hash = data.get("")
        if (
            stored_hash
            and stored_hash != "BUILD_TIME_PLACEHOLDER"
            and stored_hash != computed_hash
        ):
            raise RuntimeError(
                f"MANIFEST_HASH_MISMATCH: Computed hash {computed_hash[:16]}... "
                f"does not match stored hash {stored_hash[:16]}... "
                "System start denied. Possible tampering."
            )

        # MVI-05: Check for absence of table_hash in joint_risk_multiplier_table.
        jrmt = data.get("joint_risk_multiplier_table", {})
        if "table_hash" in jrmt:
            raise RuntimeError(
                "MANIFEST_TABLEHASH_PRESENT: joint_risk_multiplier_table must not "
                "contain a table_hash key per Manifest Authority Policy."
            )

        # MVI-03: Extract the three FAS v6.1.0 constants.
        try:
            thresholds = data["thresholds"]
            shock_cap  = float(thresholds["shock_exposure_cap"])
            max_dd     = float(thresholds["max_drawdown_threshold"])
            vol_trig   = float(thresholds["vol_compression_trigger"])
        except (KeyError, ValueError) as exc:
            raise RuntimeError(
                f"INTEGRITY_FAILURE: Missing or invalid threshold key in manifest: {exc}"
            ) from exc

        # MVI-04: Verify the three extracted constants equal FAS v6.1.0 values.
        if not self._floats_equal(shock_cap, self._EXPECTED_SHOCK_EXPOSURE_CAP):
            raise RuntimeError(
                f"MANIFEST_CONSTANT_MISMATCH: shock_exposure_cap={shock_cap} "
                f"expected {self._EXPECTED_SHOCK_EXPOSURE_CAP}."
            )
        if not self._floats_equal(max_dd, self._EXPECTED_MAX_DRAWDOWN_THRESHOLD):
            raise RuntimeError(
                f"MANIFEST_CONSTANT_MISMATCH: max_drawdown_threshold={max_dd} "
                f"expected {self._EXPECTED_MAX_DRAWDOWN_THRESHOLD}."
            )
        if not self._floats_equal(vol_trig, self._EXPECTED_VOL_COMPRESSION_TRIGGER):
            raise RuntimeError(
                f"MANIFEST_CONSTANT_MISMATCH: vol_compression_trigger={vol_trig} "
                f"expected {self._EXPECTED_VOL_COMPRESSION_TRIGGER}."
            )

        # MVI-06: Return computed hash for propagation into ExecutionRecords.
        return computed_hash, thresholds

    def xǁManifestValidatorǁvalidate__mutmut_42(self) -> Tuple[str, Dict[str, Any]]:
        """
        Execute full manifest validation.

        Returns:
          (computed_hash, thresholds_dict)
          computed_hash -- SHA-256 hex digest of the manifest content.
          thresholds    -- dict from manifest["thresholds"] section.

        Raises RuntimeError with failure_type_id prefix on any hard failure.
        Failure types raised here:
          MANIFEST_HASH_MISMATCH    -- MVI-02
          MANIFEST_CONSTANT_MISMATCH -- MVI-04
          MANIFEST_TABLEHASH_PRESENT -- MVI-05
          INTEGRITY_FAILURE          -- missing file or parse error
        """
        # MVI-01: Load manifest file.
        if not self.manifest_path.exists():
            raise RuntimeError(
                "INTEGRITY_FAILURE: THRESHOLD_MANIFEST.json not found at "
                f"{self.manifest_path}. Harness cannot start without manifest."
            )

        try:
            with open(self.manifest_path, "r", encoding="utf-8") as f:
                raw = f.read()
            data = json.loads(raw)
        except Exception as exc:
            raise RuntimeError(
                f"INTEGRITY_FAILURE: Failed to load or parse THRESHOLD_MANIFEST.json: {exc}"
            ) from exc

        # MVI-01: Compute hash excluding manifest_hash field.
        data_for_hash = {k: v for k, v in data.items() if k != "manifest_hash"}
        computed_hash = hashlib.sha256(
            json.dumps(data_for_hash, sort_keys=True, separators=(",", ":")).encode("utf-8")
        ).hexdigest()

        # MVI-02: Verify computed hash matches stored manifest_hash.
        stored_hash = data.get("manifest_hash", )
        if (
            stored_hash
            and stored_hash != "BUILD_TIME_PLACEHOLDER"
            and stored_hash != computed_hash
        ):
            raise RuntimeError(
                f"MANIFEST_HASH_MISMATCH: Computed hash {computed_hash[:16]}... "
                f"does not match stored hash {stored_hash[:16]}... "
                "System start denied. Possible tampering."
            )

        # MVI-05: Check for absence of table_hash in joint_risk_multiplier_table.
        jrmt = data.get("joint_risk_multiplier_table", {})
        if "table_hash" in jrmt:
            raise RuntimeError(
                "MANIFEST_TABLEHASH_PRESENT: joint_risk_multiplier_table must not "
                "contain a table_hash key per Manifest Authority Policy."
            )

        # MVI-03: Extract the three FAS v6.1.0 constants.
        try:
            thresholds = data["thresholds"]
            shock_cap  = float(thresholds["shock_exposure_cap"])
            max_dd     = float(thresholds["max_drawdown_threshold"])
            vol_trig   = float(thresholds["vol_compression_trigger"])
        except (KeyError, ValueError) as exc:
            raise RuntimeError(
                f"INTEGRITY_FAILURE: Missing or invalid threshold key in manifest: {exc}"
            ) from exc

        # MVI-04: Verify the three extracted constants equal FAS v6.1.0 values.
        if not self._floats_equal(shock_cap, self._EXPECTED_SHOCK_EXPOSURE_CAP):
            raise RuntimeError(
                f"MANIFEST_CONSTANT_MISMATCH: shock_exposure_cap={shock_cap} "
                f"expected {self._EXPECTED_SHOCK_EXPOSURE_CAP}."
            )
        if not self._floats_equal(max_dd, self._EXPECTED_MAX_DRAWDOWN_THRESHOLD):
            raise RuntimeError(
                f"MANIFEST_CONSTANT_MISMATCH: max_drawdown_threshold={max_dd} "
                f"expected {self._EXPECTED_MAX_DRAWDOWN_THRESHOLD}."
            )
        if not self._floats_equal(vol_trig, self._EXPECTED_VOL_COMPRESSION_TRIGGER):
            raise RuntimeError(
                f"MANIFEST_CONSTANT_MISMATCH: vol_compression_trigger={vol_trig} "
                f"expected {self._EXPECTED_VOL_COMPRESSION_TRIGGER}."
            )

        # MVI-06: Return computed hash for propagation into ExecutionRecords.
        return computed_hash, thresholds

    def xǁManifestValidatorǁvalidate__mutmut_43(self) -> Tuple[str, Dict[str, Any]]:
        """
        Execute full manifest validation.

        Returns:
          (computed_hash, thresholds_dict)
          computed_hash -- SHA-256 hex digest of the manifest content.
          thresholds    -- dict from manifest["thresholds"] section.

        Raises RuntimeError with failure_type_id prefix on any hard failure.
        Failure types raised here:
          MANIFEST_HASH_MISMATCH    -- MVI-02
          MANIFEST_CONSTANT_MISMATCH -- MVI-04
          MANIFEST_TABLEHASH_PRESENT -- MVI-05
          INTEGRITY_FAILURE          -- missing file or parse error
        """
        # MVI-01: Load manifest file.
        if not self.manifest_path.exists():
            raise RuntimeError(
                "INTEGRITY_FAILURE: THRESHOLD_MANIFEST.json not found at "
                f"{self.manifest_path}. Harness cannot start without manifest."
            )

        try:
            with open(self.manifest_path, "r", encoding="utf-8") as f:
                raw = f.read()
            data = json.loads(raw)
        except Exception as exc:
            raise RuntimeError(
                f"INTEGRITY_FAILURE: Failed to load or parse THRESHOLD_MANIFEST.json: {exc}"
            ) from exc

        # MVI-01: Compute hash excluding manifest_hash field.
        data_for_hash = {k: v for k, v in data.items() if k != "manifest_hash"}
        computed_hash = hashlib.sha256(
            json.dumps(data_for_hash, sort_keys=True, separators=(",", ":")).encode("utf-8")
        ).hexdigest()

        # MVI-02: Verify computed hash matches stored manifest_hash.
        stored_hash = data.get("XXmanifest_hashXX", "")
        if (
            stored_hash
            and stored_hash != "BUILD_TIME_PLACEHOLDER"
            and stored_hash != computed_hash
        ):
            raise RuntimeError(
                f"MANIFEST_HASH_MISMATCH: Computed hash {computed_hash[:16]}... "
                f"does not match stored hash {stored_hash[:16]}... "
                "System start denied. Possible tampering."
            )

        # MVI-05: Check for absence of table_hash in joint_risk_multiplier_table.
        jrmt = data.get("joint_risk_multiplier_table", {})
        if "table_hash" in jrmt:
            raise RuntimeError(
                "MANIFEST_TABLEHASH_PRESENT: joint_risk_multiplier_table must not "
                "contain a table_hash key per Manifest Authority Policy."
            )

        # MVI-03: Extract the three FAS v6.1.0 constants.
        try:
            thresholds = data["thresholds"]
            shock_cap  = float(thresholds["shock_exposure_cap"])
            max_dd     = float(thresholds["max_drawdown_threshold"])
            vol_trig   = float(thresholds["vol_compression_trigger"])
        except (KeyError, ValueError) as exc:
            raise RuntimeError(
                f"INTEGRITY_FAILURE: Missing or invalid threshold key in manifest: {exc}"
            ) from exc

        # MVI-04: Verify the three extracted constants equal FAS v6.1.0 values.
        if not self._floats_equal(shock_cap, self._EXPECTED_SHOCK_EXPOSURE_CAP):
            raise RuntimeError(
                f"MANIFEST_CONSTANT_MISMATCH: shock_exposure_cap={shock_cap} "
                f"expected {self._EXPECTED_SHOCK_EXPOSURE_CAP}."
            )
        if not self._floats_equal(max_dd, self._EXPECTED_MAX_DRAWDOWN_THRESHOLD):
            raise RuntimeError(
                f"MANIFEST_CONSTANT_MISMATCH: max_drawdown_threshold={max_dd} "
                f"expected {self._EXPECTED_MAX_DRAWDOWN_THRESHOLD}."
            )
        if not self._floats_equal(vol_trig, self._EXPECTED_VOL_COMPRESSION_TRIGGER):
            raise RuntimeError(
                f"MANIFEST_CONSTANT_MISMATCH: vol_compression_trigger={vol_trig} "
                f"expected {self._EXPECTED_VOL_COMPRESSION_TRIGGER}."
            )

        # MVI-06: Return computed hash for propagation into ExecutionRecords.
        return computed_hash, thresholds

    def xǁManifestValidatorǁvalidate__mutmut_44(self) -> Tuple[str, Dict[str, Any]]:
        """
        Execute full manifest validation.

        Returns:
          (computed_hash, thresholds_dict)
          computed_hash -- SHA-256 hex digest of the manifest content.
          thresholds    -- dict from manifest["thresholds"] section.

        Raises RuntimeError with failure_type_id prefix on any hard failure.
        Failure types raised here:
          MANIFEST_HASH_MISMATCH    -- MVI-02
          MANIFEST_CONSTANT_MISMATCH -- MVI-04
          MANIFEST_TABLEHASH_PRESENT -- MVI-05
          INTEGRITY_FAILURE          -- missing file or parse error
        """
        # MVI-01: Load manifest file.
        if not self.manifest_path.exists():
            raise RuntimeError(
                "INTEGRITY_FAILURE: THRESHOLD_MANIFEST.json not found at "
                f"{self.manifest_path}. Harness cannot start without manifest."
            )

        try:
            with open(self.manifest_path, "r", encoding="utf-8") as f:
                raw = f.read()
            data = json.loads(raw)
        except Exception as exc:
            raise RuntimeError(
                f"INTEGRITY_FAILURE: Failed to load or parse THRESHOLD_MANIFEST.json: {exc}"
            ) from exc

        # MVI-01: Compute hash excluding manifest_hash field.
        data_for_hash = {k: v for k, v in data.items() if k != "manifest_hash"}
        computed_hash = hashlib.sha256(
            json.dumps(data_for_hash, sort_keys=True, separators=(",", ":")).encode("utf-8")
        ).hexdigest()

        # MVI-02: Verify computed hash matches stored manifest_hash.
        stored_hash = data.get("MANIFEST_HASH", "")
        if (
            stored_hash
            and stored_hash != "BUILD_TIME_PLACEHOLDER"
            and stored_hash != computed_hash
        ):
            raise RuntimeError(
                f"MANIFEST_HASH_MISMATCH: Computed hash {computed_hash[:16]}... "
                f"does not match stored hash {stored_hash[:16]}... "
                "System start denied. Possible tampering."
            )

        # MVI-05: Check for absence of table_hash in joint_risk_multiplier_table.
        jrmt = data.get("joint_risk_multiplier_table", {})
        if "table_hash" in jrmt:
            raise RuntimeError(
                "MANIFEST_TABLEHASH_PRESENT: joint_risk_multiplier_table must not "
                "contain a table_hash key per Manifest Authority Policy."
            )

        # MVI-03: Extract the three FAS v6.1.0 constants.
        try:
            thresholds = data["thresholds"]
            shock_cap  = float(thresholds["shock_exposure_cap"])
            max_dd     = float(thresholds["max_drawdown_threshold"])
            vol_trig   = float(thresholds["vol_compression_trigger"])
        except (KeyError, ValueError) as exc:
            raise RuntimeError(
                f"INTEGRITY_FAILURE: Missing or invalid threshold key in manifest: {exc}"
            ) from exc

        # MVI-04: Verify the three extracted constants equal FAS v6.1.0 values.
        if not self._floats_equal(shock_cap, self._EXPECTED_SHOCK_EXPOSURE_CAP):
            raise RuntimeError(
                f"MANIFEST_CONSTANT_MISMATCH: shock_exposure_cap={shock_cap} "
                f"expected {self._EXPECTED_SHOCK_EXPOSURE_CAP}."
            )
        if not self._floats_equal(max_dd, self._EXPECTED_MAX_DRAWDOWN_THRESHOLD):
            raise RuntimeError(
                f"MANIFEST_CONSTANT_MISMATCH: max_drawdown_threshold={max_dd} "
                f"expected {self._EXPECTED_MAX_DRAWDOWN_THRESHOLD}."
            )
        if not self._floats_equal(vol_trig, self._EXPECTED_VOL_COMPRESSION_TRIGGER):
            raise RuntimeError(
                f"MANIFEST_CONSTANT_MISMATCH: vol_compression_trigger={vol_trig} "
                f"expected {self._EXPECTED_VOL_COMPRESSION_TRIGGER}."
            )

        # MVI-06: Return computed hash for propagation into ExecutionRecords.
        return computed_hash, thresholds

    def xǁManifestValidatorǁvalidate__mutmut_45(self) -> Tuple[str, Dict[str, Any]]:
        """
        Execute full manifest validation.

        Returns:
          (computed_hash, thresholds_dict)
          computed_hash -- SHA-256 hex digest of the manifest content.
          thresholds    -- dict from manifest["thresholds"] section.

        Raises RuntimeError with failure_type_id prefix on any hard failure.
        Failure types raised here:
          MANIFEST_HASH_MISMATCH    -- MVI-02
          MANIFEST_CONSTANT_MISMATCH -- MVI-04
          MANIFEST_TABLEHASH_PRESENT -- MVI-05
          INTEGRITY_FAILURE          -- missing file or parse error
        """
        # MVI-01: Load manifest file.
        if not self.manifest_path.exists():
            raise RuntimeError(
                "INTEGRITY_FAILURE: THRESHOLD_MANIFEST.json not found at "
                f"{self.manifest_path}. Harness cannot start without manifest."
            )

        try:
            with open(self.manifest_path, "r", encoding="utf-8") as f:
                raw = f.read()
            data = json.loads(raw)
        except Exception as exc:
            raise RuntimeError(
                f"INTEGRITY_FAILURE: Failed to load or parse THRESHOLD_MANIFEST.json: {exc}"
            ) from exc

        # MVI-01: Compute hash excluding manifest_hash field.
        data_for_hash = {k: v for k, v in data.items() if k != "manifest_hash"}
        computed_hash = hashlib.sha256(
            json.dumps(data_for_hash, sort_keys=True, separators=(",", ":")).encode("utf-8")
        ).hexdigest()

        # MVI-02: Verify computed hash matches stored manifest_hash.
        stored_hash = data.get("manifest_hash", "XXXX")
        if (
            stored_hash
            and stored_hash != "BUILD_TIME_PLACEHOLDER"
            and stored_hash != computed_hash
        ):
            raise RuntimeError(
                f"MANIFEST_HASH_MISMATCH: Computed hash {computed_hash[:16]}... "
                f"does not match stored hash {stored_hash[:16]}... "
                "System start denied. Possible tampering."
            )

        # MVI-05: Check for absence of table_hash in joint_risk_multiplier_table.
        jrmt = data.get("joint_risk_multiplier_table", {})
        if "table_hash" in jrmt:
            raise RuntimeError(
                "MANIFEST_TABLEHASH_PRESENT: joint_risk_multiplier_table must not "
                "contain a table_hash key per Manifest Authority Policy."
            )

        # MVI-03: Extract the three FAS v6.1.0 constants.
        try:
            thresholds = data["thresholds"]
            shock_cap  = float(thresholds["shock_exposure_cap"])
            max_dd     = float(thresholds["max_drawdown_threshold"])
            vol_trig   = float(thresholds["vol_compression_trigger"])
        except (KeyError, ValueError) as exc:
            raise RuntimeError(
                f"INTEGRITY_FAILURE: Missing or invalid threshold key in manifest: {exc}"
            ) from exc

        # MVI-04: Verify the three extracted constants equal FAS v6.1.0 values.
        if not self._floats_equal(shock_cap, self._EXPECTED_SHOCK_EXPOSURE_CAP):
            raise RuntimeError(
                f"MANIFEST_CONSTANT_MISMATCH: shock_exposure_cap={shock_cap} "
                f"expected {self._EXPECTED_SHOCK_EXPOSURE_CAP}."
            )
        if not self._floats_equal(max_dd, self._EXPECTED_MAX_DRAWDOWN_THRESHOLD):
            raise RuntimeError(
                f"MANIFEST_CONSTANT_MISMATCH: max_drawdown_threshold={max_dd} "
                f"expected {self._EXPECTED_MAX_DRAWDOWN_THRESHOLD}."
            )
        if not self._floats_equal(vol_trig, self._EXPECTED_VOL_COMPRESSION_TRIGGER):
            raise RuntimeError(
                f"MANIFEST_CONSTANT_MISMATCH: vol_compression_trigger={vol_trig} "
                f"expected {self._EXPECTED_VOL_COMPRESSION_TRIGGER}."
            )

        # MVI-06: Return computed hash for propagation into ExecutionRecords.
        return computed_hash, thresholds

    def xǁManifestValidatorǁvalidate__mutmut_46(self) -> Tuple[str, Dict[str, Any]]:
        """
        Execute full manifest validation.

        Returns:
          (computed_hash, thresholds_dict)
          computed_hash -- SHA-256 hex digest of the manifest content.
          thresholds    -- dict from manifest["thresholds"] section.

        Raises RuntimeError with failure_type_id prefix on any hard failure.
        Failure types raised here:
          MANIFEST_HASH_MISMATCH    -- MVI-02
          MANIFEST_CONSTANT_MISMATCH -- MVI-04
          MANIFEST_TABLEHASH_PRESENT -- MVI-05
          INTEGRITY_FAILURE          -- missing file or parse error
        """
        # MVI-01: Load manifest file.
        if not self.manifest_path.exists():
            raise RuntimeError(
                "INTEGRITY_FAILURE: THRESHOLD_MANIFEST.json not found at "
                f"{self.manifest_path}. Harness cannot start without manifest."
            )

        try:
            with open(self.manifest_path, "r", encoding="utf-8") as f:
                raw = f.read()
            data = json.loads(raw)
        except Exception as exc:
            raise RuntimeError(
                f"INTEGRITY_FAILURE: Failed to load or parse THRESHOLD_MANIFEST.json: {exc}"
            ) from exc

        # MVI-01: Compute hash excluding manifest_hash field.
        data_for_hash = {k: v for k, v in data.items() if k != "manifest_hash"}
        computed_hash = hashlib.sha256(
            json.dumps(data_for_hash, sort_keys=True, separators=(",", ":")).encode("utf-8")
        ).hexdigest()

        # MVI-02: Verify computed hash matches stored manifest_hash.
        stored_hash = data.get("manifest_hash", "")
        if (
            stored_hash
            and stored_hash != "BUILD_TIME_PLACEHOLDER" or stored_hash != computed_hash
        ):
            raise RuntimeError(
                f"MANIFEST_HASH_MISMATCH: Computed hash {computed_hash[:16]}... "
                f"does not match stored hash {stored_hash[:16]}... "
                "System start denied. Possible tampering."
            )

        # MVI-05: Check for absence of table_hash in joint_risk_multiplier_table.
        jrmt = data.get("joint_risk_multiplier_table", {})
        if "table_hash" in jrmt:
            raise RuntimeError(
                "MANIFEST_TABLEHASH_PRESENT: joint_risk_multiplier_table must not "
                "contain a table_hash key per Manifest Authority Policy."
            )

        # MVI-03: Extract the three FAS v6.1.0 constants.
        try:
            thresholds = data["thresholds"]
            shock_cap  = float(thresholds["shock_exposure_cap"])
            max_dd     = float(thresholds["max_drawdown_threshold"])
            vol_trig   = float(thresholds["vol_compression_trigger"])
        except (KeyError, ValueError) as exc:
            raise RuntimeError(
                f"INTEGRITY_FAILURE: Missing or invalid threshold key in manifest: {exc}"
            ) from exc

        # MVI-04: Verify the three extracted constants equal FAS v6.1.0 values.
        if not self._floats_equal(shock_cap, self._EXPECTED_SHOCK_EXPOSURE_CAP):
            raise RuntimeError(
                f"MANIFEST_CONSTANT_MISMATCH: shock_exposure_cap={shock_cap} "
                f"expected {self._EXPECTED_SHOCK_EXPOSURE_CAP}."
            )
        if not self._floats_equal(max_dd, self._EXPECTED_MAX_DRAWDOWN_THRESHOLD):
            raise RuntimeError(
                f"MANIFEST_CONSTANT_MISMATCH: max_drawdown_threshold={max_dd} "
                f"expected {self._EXPECTED_MAX_DRAWDOWN_THRESHOLD}."
            )
        if not self._floats_equal(vol_trig, self._EXPECTED_VOL_COMPRESSION_TRIGGER):
            raise RuntimeError(
                f"MANIFEST_CONSTANT_MISMATCH: vol_compression_trigger={vol_trig} "
                f"expected {self._EXPECTED_VOL_COMPRESSION_TRIGGER}."
            )

        # MVI-06: Return computed hash for propagation into ExecutionRecords.
        return computed_hash, thresholds

    def xǁManifestValidatorǁvalidate__mutmut_47(self) -> Tuple[str, Dict[str, Any]]:
        """
        Execute full manifest validation.

        Returns:
          (computed_hash, thresholds_dict)
          computed_hash -- SHA-256 hex digest of the manifest content.
          thresholds    -- dict from manifest["thresholds"] section.

        Raises RuntimeError with failure_type_id prefix on any hard failure.
        Failure types raised here:
          MANIFEST_HASH_MISMATCH    -- MVI-02
          MANIFEST_CONSTANT_MISMATCH -- MVI-04
          MANIFEST_TABLEHASH_PRESENT -- MVI-05
          INTEGRITY_FAILURE          -- missing file or parse error
        """
        # MVI-01: Load manifest file.
        if not self.manifest_path.exists():
            raise RuntimeError(
                "INTEGRITY_FAILURE: THRESHOLD_MANIFEST.json not found at "
                f"{self.manifest_path}. Harness cannot start without manifest."
            )

        try:
            with open(self.manifest_path, "r", encoding="utf-8") as f:
                raw = f.read()
            data = json.loads(raw)
        except Exception as exc:
            raise RuntimeError(
                f"INTEGRITY_FAILURE: Failed to load or parse THRESHOLD_MANIFEST.json: {exc}"
            ) from exc

        # MVI-01: Compute hash excluding manifest_hash field.
        data_for_hash = {k: v for k, v in data.items() if k != "manifest_hash"}
        computed_hash = hashlib.sha256(
            json.dumps(data_for_hash, sort_keys=True, separators=(",", ":")).encode("utf-8")
        ).hexdigest()

        # MVI-02: Verify computed hash matches stored manifest_hash.
        stored_hash = data.get("manifest_hash", "")
        if (
            stored_hash or stored_hash != "BUILD_TIME_PLACEHOLDER"
            and stored_hash != computed_hash
        ):
            raise RuntimeError(
                f"MANIFEST_HASH_MISMATCH: Computed hash {computed_hash[:16]}... "
                f"does not match stored hash {stored_hash[:16]}... "
                "System start denied. Possible tampering."
            )

        # MVI-05: Check for absence of table_hash in joint_risk_multiplier_table.
        jrmt = data.get("joint_risk_multiplier_table", {})
        if "table_hash" in jrmt:
            raise RuntimeError(
                "MANIFEST_TABLEHASH_PRESENT: joint_risk_multiplier_table must not "
                "contain a table_hash key per Manifest Authority Policy."
            )

        # MVI-03: Extract the three FAS v6.1.0 constants.
        try:
            thresholds = data["thresholds"]
            shock_cap  = float(thresholds["shock_exposure_cap"])
            max_dd     = float(thresholds["max_drawdown_threshold"])
            vol_trig   = float(thresholds["vol_compression_trigger"])
        except (KeyError, ValueError) as exc:
            raise RuntimeError(
                f"INTEGRITY_FAILURE: Missing or invalid threshold key in manifest: {exc}"
            ) from exc

        # MVI-04: Verify the three extracted constants equal FAS v6.1.0 values.
        if not self._floats_equal(shock_cap, self._EXPECTED_SHOCK_EXPOSURE_CAP):
            raise RuntimeError(
                f"MANIFEST_CONSTANT_MISMATCH: shock_exposure_cap={shock_cap} "
                f"expected {self._EXPECTED_SHOCK_EXPOSURE_CAP}."
            )
        if not self._floats_equal(max_dd, self._EXPECTED_MAX_DRAWDOWN_THRESHOLD):
            raise RuntimeError(
                f"MANIFEST_CONSTANT_MISMATCH: max_drawdown_threshold={max_dd} "
                f"expected {self._EXPECTED_MAX_DRAWDOWN_THRESHOLD}."
            )
        if not self._floats_equal(vol_trig, self._EXPECTED_VOL_COMPRESSION_TRIGGER):
            raise RuntimeError(
                f"MANIFEST_CONSTANT_MISMATCH: vol_compression_trigger={vol_trig} "
                f"expected {self._EXPECTED_VOL_COMPRESSION_TRIGGER}."
            )

        # MVI-06: Return computed hash for propagation into ExecutionRecords.
        return computed_hash, thresholds

    def xǁManifestValidatorǁvalidate__mutmut_48(self) -> Tuple[str, Dict[str, Any]]:
        """
        Execute full manifest validation.

        Returns:
          (computed_hash, thresholds_dict)
          computed_hash -- SHA-256 hex digest of the manifest content.
          thresholds    -- dict from manifest["thresholds"] section.

        Raises RuntimeError with failure_type_id prefix on any hard failure.
        Failure types raised here:
          MANIFEST_HASH_MISMATCH    -- MVI-02
          MANIFEST_CONSTANT_MISMATCH -- MVI-04
          MANIFEST_TABLEHASH_PRESENT -- MVI-05
          INTEGRITY_FAILURE          -- missing file or parse error
        """
        # MVI-01: Load manifest file.
        if not self.manifest_path.exists():
            raise RuntimeError(
                "INTEGRITY_FAILURE: THRESHOLD_MANIFEST.json not found at "
                f"{self.manifest_path}. Harness cannot start without manifest."
            )

        try:
            with open(self.manifest_path, "r", encoding="utf-8") as f:
                raw = f.read()
            data = json.loads(raw)
        except Exception as exc:
            raise RuntimeError(
                f"INTEGRITY_FAILURE: Failed to load or parse THRESHOLD_MANIFEST.json: {exc}"
            ) from exc

        # MVI-01: Compute hash excluding manifest_hash field.
        data_for_hash = {k: v for k, v in data.items() if k != "manifest_hash"}
        computed_hash = hashlib.sha256(
            json.dumps(data_for_hash, sort_keys=True, separators=(",", ":")).encode("utf-8")
        ).hexdigest()

        # MVI-02: Verify computed hash matches stored manifest_hash.
        stored_hash = data.get("manifest_hash", "")
        if (
            stored_hash
            and stored_hash == "BUILD_TIME_PLACEHOLDER"
            and stored_hash != computed_hash
        ):
            raise RuntimeError(
                f"MANIFEST_HASH_MISMATCH: Computed hash {computed_hash[:16]}... "
                f"does not match stored hash {stored_hash[:16]}... "
                "System start denied. Possible tampering."
            )

        # MVI-05: Check for absence of table_hash in joint_risk_multiplier_table.
        jrmt = data.get("joint_risk_multiplier_table", {})
        if "table_hash" in jrmt:
            raise RuntimeError(
                "MANIFEST_TABLEHASH_PRESENT: joint_risk_multiplier_table must not "
                "contain a table_hash key per Manifest Authority Policy."
            )

        # MVI-03: Extract the three FAS v6.1.0 constants.
        try:
            thresholds = data["thresholds"]
            shock_cap  = float(thresholds["shock_exposure_cap"])
            max_dd     = float(thresholds["max_drawdown_threshold"])
            vol_trig   = float(thresholds["vol_compression_trigger"])
        except (KeyError, ValueError) as exc:
            raise RuntimeError(
                f"INTEGRITY_FAILURE: Missing or invalid threshold key in manifest: {exc}"
            ) from exc

        # MVI-04: Verify the three extracted constants equal FAS v6.1.0 values.
        if not self._floats_equal(shock_cap, self._EXPECTED_SHOCK_EXPOSURE_CAP):
            raise RuntimeError(
                f"MANIFEST_CONSTANT_MISMATCH: shock_exposure_cap={shock_cap} "
                f"expected {self._EXPECTED_SHOCK_EXPOSURE_CAP}."
            )
        if not self._floats_equal(max_dd, self._EXPECTED_MAX_DRAWDOWN_THRESHOLD):
            raise RuntimeError(
                f"MANIFEST_CONSTANT_MISMATCH: max_drawdown_threshold={max_dd} "
                f"expected {self._EXPECTED_MAX_DRAWDOWN_THRESHOLD}."
            )
        if not self._floats_equal(vol_trig, self._EXPECTED_VOL_COMPRESSION_TRIGGER):
            raise RuntimeError(
                f"MANIFEST_CONSTANT_MISMATCH: vol_compression_trigger={vol_trig} "
                f"expected {self._EXPECTED_VOL_COMPRESSION_TRIGGER}."
            )

        # MVI-06: Return computed hash for propagation into ExecutionRecords.
        return computed_hash, thresholds

    def xǁManifestValidatorǁvalidate__mutmut_49(self) -> Tuple[str, Dict[str, Any]]:
        """
        Execute full manifest validation.

        Returns:
          (computed_hash, thresholds_dict)
          computed_hash -- SHA-256 hex digest of the manifest content.
          thresholds    -- dict from manifest["thresholds"] section.

        Raises RuntimeError with failure_type_id prefix on any hard failure.
        Failure types raised here:
          MANIFEST_HASH_MISMATCH    -- MVI-02
          MANIFEST_CONSTANT_MISMATCH -- MVI-04
          MANIFEST_TABLEHASH_PRESENT -- MVI-05
          INTEGRITY_FAILURE          -- missing file or parse error
        """
        # MVI-01: Load manifest file.
        if not self.manifest_path.exists():
            raise RuntimeError(
                "INTEGRITY_FAILURE: THRESHOLD_MANIFEST.json not found at "
                f"{self.manifest_path}. Harness cannot start without manifest."
            )

        try:
            with open(self.manifest_path, "r", encoding="utf-8") as f:
                raw = f.read()
            data = json.loads(raw)
        except Exception as exc:
            raise RuntimeError(
                f"INTEGRITY_FAILURE: Failed to load or parse THRESHOLD_MANIFEST.json: {exc}"
            ) from exc

        # MVI-01: Compute hash excluding manifest_hash field.
        data_for_hash = {k: v for k, v in data.items() if k != "manifest_hash"}
        computed_hash = hashlib.sha256(
            json.dumps(data_for_hash, sort_keys=True, separators=(",", ":")).encode("utf-8")
        ).hexdigest()

        # MVI-02: Verify computed hash matches stored manifest_hash.
        stored_hash = data.get("manifest_hash", "")
        if (
            stored_hash
            and stored_hash != "XXBUILD_TIME_PLACEHOLDERXX"
            and stored_hash != computed_hash
        ):
            raise RuntimeError(
                f"MANIFEST_HASH_MISMATCH: Computed hash {computed_hash[:16]}... "
                f"does not match stored hash {stored_hash[:16]}... "
                "System start denied. Possible tampering."
            )

        # MVI-05: Check for absence of table_hash in joint_risk_multiplier_table.
        jrmt = data.get("joint_risk_multiplier_table", {})
        if "table_hash" in jrmt:
            raise RuntimeError(
                "MANIFEST_TABLEHASH_PRESENT: joint_risk_multiplier_table must not "
                "contain a table_hash key per Manifest Authority Policy."
            )

        # MVI-03: Extract the three FAS v6.1.0 constants.
        try:
            thresholds = data["thresholds"]
            shock_cap  = float(thresholds["shock_exposure_cap"])
            max_dd     = float(thresholds["max_drawdown_threshold"])
            vol_trig   = float(thresholds["vol_compression_trigger"])
        except (KeyError, ValueError) as exc:
            raise RuntimeError(
                f"INTEGRITY_FAILURE: Missing or invalid threshold key in manifest: {exc}"
            ) from exc

        # MVI-04: Verify the three extracted constants equal FAS v6.1.0 values.
        if not self._floats_equal(shock_cap, self._EXPECTED_SHOCK_EXPOSURE_CAP):
            raise RuntimeError(
                f"MANIFEST_CONSTANT_MISMATCH: shock_exposure_cap={shock_cap} "
                f"expected {self._EXPECTED_SHOCK_EXPOSURE_CAP}."
            )
        if not self._floats_equal(max_dd, self._EXPECTED_MAX_DRAWDOWN_THRESHOLD):
            raise RuntimeError(
                f"MANIFEST_CONSTANT_MISMATCH: max_drawdown_threshold={max_dd} "
                f"expected {self._EXPECTED_MAX_DRAWDOWN_THRESHOLD}."
            )
        if not self._floats_equal(vol_trig, self._EXPECTED_VOL_COMPRESSION_TRIGGER):
            raise RuntimeError(
                f"MANIFEST_CONSTANT_MISMATCH: vol_compression_trigger={vol_trig} "
                f"expected {self._EXPECTED_VOL_COMPRESSION_TRIGGER}."
            )

        # MVI-06: Return computed hash for propagation into ExecutionRecords.
        return computed_hash, thresholds

    def xǁManifestValidatorǁvalidate__mutmut_50(self) -> Tuple[str, Dict[str, Any]]:
        """
        Execute full manifest validation.

        Returns:
          (computed_hash, thresholds_dict)
          computed_hash -- SHA-256 hex digest of the manifest content.
          thresholds    -- dict from manifest["thresholds"] section.

        Raises RuntimeError with failure_type_id prefix on any hard failure.
        Failure types raised here:
          MANIFEST_HASH_MISMATCH    -- MVI-02
          MANIFEST_CONSTANT_MISMATCH -- MVI-04
          MANIFEST_TABLEHASH_PRESENT -- MVI-05
          INTEGRITY_FAILURE          -- missing file or parse error
        """
        # MVI-01: Load manifest file.
        if not self.manifest_path.exists():
            raise RuntimeError(
                "INTEGRITY_FAILURE: THRESHOLD_MANIFEST.json not found at "
                f"{self.manifest_path}. Harness cannot start without manifest."
            )

        try:
            with open(self.manifest_path, "r", encoding="utf-8") as f:
                raw = f.read()
            data = json.loads(raw)
        except Exception as exc:
            raise RuntimeError(
                f"INTEGRITY_FAILURE: Failed to load or parse THRESHOLD_MANIFEST.json: {exc}"
            ) from exc

        # MVI-01: Compute hash excluding manifest_hash field.
        data_for_hash = {k: v for k, v in data.items() if k != "manifest_hash"}
        computed_hash = hashlib.sha256(
            json.dumps(data_for_hash, sort_keys=True, separators=(",", ":")).encode("utf-8")
        ).hexdigest()

        # MVI-02: Verify computed hash matches stored manifest_hash.
        stored_hash = data.get("manifest_hash", "")
        if (
            stored_hash
            and stored_hash != "build_time_placeholder"
            and stored_hash != computed_hash
        ):
            raise RuntimeError(
                f"MANIFEST_HASH_MISMATCH: Computed hash {computed_hash[:16]}... "
                f"does not match stored hash {stored_hash[:16]}... "
                "System start denied. Possible tampering."
            )

        # MVI-05: Check for absence of table_hash in joint_risk_multiplier_table.
        jrmt = data.get("joint_risk_multiplier_table", {})
        if "table_hash" in jrmt:
            raise RuntimeError(
                "MANIFEST_TABLEHASH_PRESENT: joint_risk_multiplier_table must not "
                "contain a table_hash key per Manifest Authority Policy."
            )

        # MVI-03: Extract the three FAS v6.1.0 constants.
        try:
            thresholds = data["thresholds"]
            shock_cap  = float(thresholds["shock_exposure_cap"])
            max_dd     = float(thresholds["max_drawdown_threshold"])
            vol_trig   = float(thresholds["vol_compression_trigger"])
        except (KeyError, ValueError) as exc:
            raise RuntimeError(
                f"INTEGRITY_FAILURE: Missing or invalid threshold key in manifest: {exc}"
            ) from exc

        # MVI-04: Verify the three extracted constants equal FAS v6.1.0 values.
        if not self._floats_equal(shock_cap, self._EXPECTED_SHOCK_EXPOSURE_CAP):
            raise RuntimeError(
                f"MANIFEST_CONSTANT_MISMATCH: shock_exposure_cap={shock_cap} "
                f"expected {self._EXPECTED_SHOCK_EXPOSURE_CAP}."
            )
        if not self._floats_equal(max_dd, self._EXPECTED_MAX_DRAWDOWN_THRESHOLD):
            raise RuntimeError(
                f"MANIFEST_CONSTANT_MISMATCH: max_drawdown_threshold={max_dd} "
                f"expected {self._EXPECTED_MAX_DRAWDOWN_THRESHOLD}."
            )
        if not self._floats_equal(vol_trig, self._EXPECTED_VOL_COMPRESSION_TRIGGER):
            raise RuntimeError(
                f"MANIFEST_CONSTANT_MISMATCH: vol_compression_trigger={vol_trig} "
                f"expected {self._EXPECTED_VOL_COMPRESSION_TRIGGER}."
            )

        # MVI-06: Return computed hash for propagation into ExecutionRecords.
        return computed_hash, thresholds

    def xǁManifestValidatorǁvalidate__mutmut_51(self) -> Tuple[str, Dict[str, Any]]:
        """
        Execute full manifest validation.

        Returns:
          (computed_hash, thresholds_dict)
          computed_hash -- SHA-256 hex digest of the manifest content.
          thresholds    -- dict from manifest["thresholds"] section.

        Raises RuntimeError with failure_type_id prefix on any hard failure.
        Failure types raised here:
          MANIFEST_HASH_MISMATCH    -- MVI-02
          MANIFEST_CONSTANT_MISMATCH -- MVI-04
          MANIFEST_TABLEHASH_PRESENT -- MVI-05
          INTEGRITY_FAILURE          -- missing file or parse error
        """
        # MVI-01: Load manifest file.
        if not self.manifest_path.exists():
            raise RuntimeError(
                "INTEGRITY_FAILURE: THRESHOLD_MANIFEST.json not found at "
                f"{self.manifest_path}. Harness cannot start without manifest."
            )

        try:
            with open(self.manifest_path, "r", encoding="utf-8") as f:
                raw = f.read()
            data = json.loads(raw)
        except Exception as exc:
            raise RuntimeError(
                f"INTEGRITY_FAILURE: Failed to load or parse THRESHOLD_MANIFEST.json: {exc}"
            ) from exc

        # MVI-01: Compute hash excluding manifest_hash field.
        data_for_hash = {k: v for k, v in data.items() if k != "manifest_hash"}
        computed_hash = hashlib.sha256(
            json.dumps(data_for_hash, sort_keys=True, separators=(",", ":")).encode("utf-8")
        ).hexdigest()

        # MVI-02: Verify computed hash matches stored manifest_hash.
        stored_hash = data.get("manifest_hash", "")
        if (
            stored_hash
            and stored_hash != "BUILD_TIME_PLACEHOLDER"
            and stored_hash == computed_hash
        ):
            raise RuntimeError(
                f"MANIFEST_HASH_MISMATCH: Computed hash {computed_hash[:16]}... "
                f"does not match stored hash {stored_hash[:16]}... "
                "System start denied. Possible tampering."
            )

        # MVI-05: Check for absence of table_hash in joint_risk_multiplier_table.
        jrmt = data.get("joint_risk_multiplier_table", {})
        if "table_hash" in jrmt:
            raise RuntimeError(
                "MANIFEST_TABLEHASH_PRESENT: joint_risk_multiplier_table must not "
                "contain a table_hash key per Manifest Authority Policy."
            )

        # MVI-03: Extract the three FAS v6.1.0 constants.
        try:
            thresholds = data["thresholds"]
            shock_cap  = float(thresholds["shock_exposure_cap"])
            max_dd     = float(thresholds["max_drawdown_threshold"])
            vol_trig   = float(thresholds["vol_compression_trigger"])
        except (KeyError, ValueError) as exc:
            raise RuntimeError(
                f"INTEGRITY_FAILURE: Missing or invalid threshold key in manifest: {exc}"
            ) from exc

        # MVI-04: Verify the three extracted constants equal FAS v6.1.0 values.
        if not self._floats_equal(shock_cap, self._EXPECTED_SHOCK_EXPOSURE_CAP):
            raise RuntimeError(
                f"MANIFEST_CONSTANT_MISMATCH: shock_exposure_cap={shock_cap} "
                f"expected {self._EXPECTED_SHOCK_EXPOSURE_CAP}."
            )
        if not self._floats_equal(max_dd, self._EXPECTED_MAX_DRAWDOWN_THRESHOLD):
            raise RuntimeError(
                f"MANIFEST_CONSTANT_MISMATCH: max_drawdown_threshold={max_dd} "
                f"expected {self._EXPECTED_MAX_DRAWDOWN_THRESHOLD}."
            )
        if not self._floats_equal(vol_trig, self._EXPECTED_VOL_COMPRESSION_TRIGGER):
            raise RuntimeError(
                f"MANIFEST_CONSTANT_MISMATCH: vol_compression_trigger={vol_trig} "
                f"expected {self._EXPECTED_VOL_COMPRESSION_TRIGGER}."
            )

        # MVI-06: Return computed hash for propagation into ExecutionRecords.
        return computed_hash, thresholds

    def xǁManifestValidatorǁvalidate__mutmut_52(self) -> Tuple[str, Dict[str, Any]]:
        """
        Execute full manifest validation.

        Returns:
          (computed_hash, thresholds_dict)
          computed_hash -- SHA-256 hex digest of the manifest content.
          thresholds    -- dict from manifest["thresholds"] section.

        Raises RuntimeError with failure_type_id prefix on any hard failure.
        Failure types raised here:
          MANIFEST_HASH_MISMATCH    -- MVI-02
          MANIFEST_CONSTANT_MISMATCH -- MVI-04
          MANIFEST_TABLEHASH_PRESENT -- MVI-05
          INTEGRITY_FAILURE          -- missing file or parse error
        """
        # MVI-01: Load manifest file.
        if not self.manifest_path.exists():
            raise RuntimeError(
                "INTEGRITY_FAILURE: THRESHOLD_MANIFEST.json not found at "
                f"{self.manifest_path}. Harness cannot start without manifest."
            )

        try:
            with open(self.manifest_path, "r", encoding="utf-8") as f:
                raw = f.read()
            data = json.loads(raw)
        except Exception as exc:
            raise RuntimeError(
                f"INTEGRITY_FAILURE: Failed to load or parse THRESHOLD_MANIFEST.json: {exc}"
            ) from exc

        # MVI-01: Compute hash excluding manifest_hash field.
        data_for_hash = {k: v for k, v in data.items() if k != "manifest_hash"}
        computed_hash = hashlib.sha256(
            json.dumps(data_for_hash, sort_keys=True, separators=(",", ":")).encode("utf-8")
        ).hexdigest()

        # MVI-02: Verify computed hash matches stored manifest_hash.
        stored_hash = data.get("manifest_hash", "")
        if (
            stored_hash
            and stored_hash != "BUILD_TIME_PLACEHOLDER"
            and stored_hash != computed_hash
        ):
            raise RuntimeError(
                None
            )

        # MVI-05: Check for absence of table_hash in joint_risk_multiplier_table.
        jrmt = data.get("joint_risk_multiplier_table", {})
        if "table_hash" in jrmt:
            raise RuntimeError(
                "MANIFEST_TABLEHASH_PRESENT: joint_risk_multiplier_table must not "
                "contain a table_hash key per Manifest Authority Policy."
            )

        # MVI-03: Extract the three FAS v6.1.0 constants.
        try:
            thresholds = data["thresholds"]
            shock_cap  = float(thresholds["shock_exposure_cap"])
            max_dd     = float(thresholds["max_drawdown_threshold"])
            vol_trig   = float(thresholds["vol_compression_trigger"])
        except (KeyError, ValueError) as exc:
            raise RuntimeError(
                f"INTEGRITY_FAILURE: Missing or invalid threshold key in manifest: {exc}"
            ) from exc

        # MVI-04: Verify the three extracted constants equal FAS v6.1.0 values.
        if not self._floats_equal(shock_cap, self._EXPECTED_SHOCK_EXPOSURE_CAP):
            raise RuntimeError(
                f"MANIFEST_CONSTANT_MISMATCH: shock_exposure_cap={shock_cap} "
                f"expected {self._EXPECTED_SHOCK_EXPOSURE_CAP}."
            )
        if not self._floats_equal(max_dd, self._EXPECTED_MAX_DRAWDOWN_THRESHOLD):
            raise RuntimeError(
                f"MANIFEST_CONSTANT_MISMATCH: max_drawdown_threshold={max_dd} "
                f"expected {self._EXPECTED_MAX_DRAWDOWN_THRESHOLD}."
            )
        if not self._floats_equal(vol_trig, self._EXPECTED_VOL_COMPRESSION_TRIGGER):
            raise RuntimeError(
                f"MANIFEST_CONSTANT_MISMATCH: vol_compression_trigger={vol_trig} "
                f"expected {self._EXPECTED_VOL_COMPRESSION_TRIGGER}."
            )

        # MVI-06: Return computed hash for propagation into ExecutionRecords.
        return computed_hash, thresholds

    def xǁManifestValidatorǁvalidate__mutmut_53(self) -> Tuple[str, Dict[str, Any]]:
        """
        Execute full manifest validation.

        Returns:
          (computed_hash, thresholds_dict)
          computed_hash -- SHA-256 hex digest of the manifest content.
          thresholds    -- dict from manifest["thresholds"] section.

        Raises RuntimeError with failure_type_id prefix on any hard failure.
        Failure types raised here:
          MANIFEST_HASH_MISMATCH    -- MVI-02
          MANIFEST_CONSTANT_MISMATCH -- MVI-04
          MANIFEST_TABLEHASH_PRESENT -- MVI-05
          INTEGRITY_FAILURE          -- missing file or parse error
        """
        # MVI-01: Load manifest file.
        if not self.manifest_path.exists():
            raise RuntimeError(
                "INTEGRITY_FAILURE: THRESHOLD_MANIFEST.json not found at "
                f"{self.manifest_path}. Harness cannot start without manifest."
            )

        try:
            with open(self.manifest_path, "r", encoding="utf-8") as f:
                raw = f.read()
            data = json.loads(raw)
        except Exception as exc:
            raise RuntimeError(
                f"INTEGRITY_FAILURE: Failed to load or parse THRESHOLD_MANIFEST.json: {exc}"
            ) from exc

        # MVI-01: Compute hash excluding manifest_hash field.
        data_for_hash = {k: v for k, v in data.items() if k != "manifest_hash"}
        computed_hash = hashlib.sha256(
            json.dumps(data_for_hash, sort_keys=True, separators=(",", ":")).encode("utf-8")
        ).hexdigest()

        # MVI-02: Verify computed hash matches stored manifest_hash.
        stored_hash = data.get("manifest_hash", "")
        if (
            stored_hash
            and stored_hash != "BUILD_TIME_PLACEHOLDER"
            and stored_hash != computed_hash
        ):
            raise RuntimeError(
                f"MANIFEST_HASH_MISMATCH: Computed hash {computed_hash[:17]}... "
                f"does not match stored hash {stored_hash[:16]}... "
                "System start denied. Possible tampering."
            )

        # MVI-05: Check for absence of table_hash in joint_risk_multiplier_table.
        jrmt = data.get("joint_risk_multiplier_table", {})
        if "table_hash" in jrmt:
            raise RuntimeError(
                "MANIFEST_TABLEHASH_PRESENT: joint_risk_multiplier_table must not "
                "contain a table_hash key per Manifest Authority Policy."
            )

        # MVI-03: Extract the three FAS v6.1.0 constants.
        try:
            thresholds = data["thresholds"]
            shock_cap  = float(thresholds["shock_exposure_cap"])
            max_dd     = float(thresholds["max_drawdown_threshold"])
            vol_trig   = float(thresholds["vol_compression_trigger"])
        except (KeyError, ValueError) as exc:
            raise RuntimeError(
                f"INTEGRITY_FAILURE: Missing or invalid threshold key in manifest: {exc}"
            ) from exc

        # MVI-04: Verify the three extracted constants equal FAS v6.1.0 values.
        if not self._floats_equal(shock_cap, self._EXPECTED_SHOCK_EXPOSURE_CAP):
            raise RuntimeError(
                f"MANIFEST_CONSTANT_MISMATCH: shock_exposure_cap={shock_cap} "
                f"expected {self._EXPECTED_SHOCK_EXPOSURE_CAP}."
            )
        if not self._floats_equal(max_dd, self._EXPECTED_MAX_DRAWDOWN_THRESHOLD):
            raise RuntimeError(
                f"MANIFEST_CONSTANT_MISMATCH: max_drawdown_threshold={max_dd} "
                f"expected {self._EXPECTED_MAX_DRAWDOWN_THRESHOLD}."
            )
        if not self._floats_equal(vol_trig, self._EXPECTED_VOL_COMPRESSION_TRIGGER):
            raise RuntimeError(
                f"MANIFEST_CONSTANT_MISMATCH: vol_compression_trigger={vol_trig} "
                f"expected {self._EXPECTED_VOL_COMPRESSION_TRIGGER}."
            )

        # MVI-06: Return computed hash for propagation into ExecutionRecords.
        return computed_hash, thresholds

    def xǁManifestValidatorǁvalidate__mutmut_54(self) -> Tuple[str, Dict[str, Any]]:
        """
        Execute full manifest validation.

        Returns:
          (computed_hash, thresholds_dict)
          computed_hash -- SHA-256 hex digest of the manifest content.
          thresholds    -- dict from manifest["thresholds"] section.

        Raises RuntimeError with failure_type_id prefix on any hard failure.
        Failure types raised here:
          MANIFEST_HASH_MISMATCH    -- MVI-02
          MANIFEST_CONSTANT_MISMATCH -- MVI-04
          MANIFEST_TABLEHASH_PRESENT -- MVI-05
          INTEGRITY_FAILURE          -- missing file or parse error
        """
        # MVI-01: Load manifest file.
        if not self.manifest_path.exists():
            raise RuntimeError(
                "INTEGRITY_FAILURE: THRESHOLD_MANIFEST.json not found at "
                f"{self.manifest_path}. Harness cannot start without manifest."
            )

        try:
            with open(self.manifest_path, "r", encoding="utf-8") as f:
                raw = f.read()
            data = json.loads(raw)
        except Exception as exc:
            raise RuntimeError(
                f"INTEGRITY_FAILURE: Failed to load or parse THRESHOLD_MANIFEST.json: {exc}"
            ) from exc

        # MVI-01: Compute hash excluding manifest_hash field.
        data_for_hash = {k: v for k, v in data.items() if k != "manifest_hash"}
        computed_hash = hashlib.sha256(
            json.dumps(data_for_hash, sort_keys=True, separators=(",", ":")).encode("utf-8")
        ).hexdigest()

        # MVI-02: Verify computed hash matches stored manifest_hash.
        stored_hash = data.get("manifest_hash", "")
        if (
            stored_hash
            and stored_hash != "BUILD_TIME_PLACEHOLDER"
            and stored_hash != computed_hash
        ):
            raise RuntimeError(
                f"MANIFEST_HASH_MISMATCH: Computed hash {computed_hash[:16]}... "
                f"does not match stored hash {stored_hash[:17]}... "
                "System start denied. Possible tampering."
            )

        # MVI-05: Check for absence of table_hash in joint_risk_multiplier_table.
        jrmt = data.get("joint_risk_multiplier_table", {})
        if "table_hash" in jrmt:
            raise RuntimeError(
                "MANIFEST_TABLEHASH_PRESENT: joint_risk_multiplier_table must not "
                "contain a table_hash key per Manifest Authority Policy."
            )

        # MVI-03: Extract the three FAS v6.1.0 constants.
        try:
            thresholds = data["thresholds"]
            shock_cap  = float(thresholds["shock_exposure_cap"])
            max_dd     = float(thresholds["max_drawdown_threshold"])
            vol_trig   = float(thresholds["vol_compression_trigger"])
        except (KeyError, ValueError) as exc:
            raise RuntimeError(
                f"INTEGRITY_FAILURE: Missing or invalid threshold key in manifest: {exc}"
            ) from exc

        # MVI-04: Verify the three extracted constants equal FAS v6.1.0 values.
        if not self._floats_equal(shock_cap, self._EXPECTED_SHOCK_EXPOSURE_CAP):
            raise RuntimeError(
                f"MANIFEST_CONSTANT_MISMATCH: shock_exposure_cap={shock_cap} "
                f"expected {self._EXPECTED_SHOCK_EXPOSURE_CAP}."
            )
        if not self._floats_equal(max_dd, self._EXPECTED_MAX_DRAWDOWN_THRESHOLD):
            raise RuntimeError(
                f"MANIFEST_CONSTANT_MISMATCH: max_drawdown_threshold={max_dd} "
                f"expected {self._EXPECTED_MAX_DRAWDOWN_THRESHOLD}."
            )
        if not self._floats_equal(vol_trig, self._EXPECTED_VOL_COMPRESSION_TRIGGER):
            raise RuntimeError(
                f"MANIFEST_CONSTANT_MISMATCH: vol_compression_trigger={vol_trig} "
                f"expected {self._EXPECTED_VOL_COMPRESSION_TRIGGER}."
            )

        # MVI-06: Return computed hash for propagation into ExecutionRecords.
        return computed_hash, thresholds

    def xǁManifestValidatorǁvalidate__mutmut_55(self) -> Tuple[str, Dict[str, Any]]:
        """
        Execute full manifest validation.

        Returns:
          (computed_hash, thresholds_dict)
          computed_hash -- SHA-256 hex digest of the manifest content.
          thresholds    -- dict from manifest["thresholds"] section.

        Raises RuntimeError with failure_type_id prefix on any hard failure.
        Failure types raised here:
          MANIFEST_HASH_MISMATCH    -- MVI-02
          MANIFEST_CONSTANT_MISMATCH -- MVI-04
          MANIFEST_TABLEHASH_PRESENT -- MVI-05
          INTEGRITY_FAILURE          -- missing file or parse error
        """
        # MVI-01: Load manifest file.
        if not self.manifest_path.exists():
            raise RuntimeError(
                "INTEGRITY_FAILURE: THRESHOLD_MANIFEST.json not found at "
                f"{self.manifest_path}. Harness cannot start without manifest."
            )

        try:
            with open(self.manifest_path, "r", encoding="utf-8") as f:
                raw = f.read()
            data = json.loads(raw)
        except Exception as exc:
            raise RuntimeError(
                f"INTEGRITY_FAILURE: Failed to load or parse THRESHOLD_MANIFEST.json: {exc}"
            ) from exc

        # MVI-01: Compute hash excluding manifest_hash field.
        data_for_hash = {k: v for k, v in data.items() if k != "manifest_hash"}
        computed_hash = hashlib.sha256(
            json.dumps(data_for_hash, sort_keys=True, separators=(",", ":")).encode("utf-8")
        ).hexdigest()

        # MVI-02: Verify computed hash matches stored manifest_hash.
        stored_hash = data.get("manifest_hash", "")
        if (
            stored_hash
            and stored_hash != "BUILD_TIME_PLACEHOLDER"
            and stored_hash != computed_hash
        ):
            raise RuntimeError(
                f"MANIFEST_HASH_MISMATCH: Computed hash {computed_hash[:16]}... "
                f"does not match stored hash {stored_hash[:16]}... "
                "XXSystem start denied. Possible tampering.XX"
            )

        # MVI-05: Check for absence of table_hash in joint_risk_multiplier_table.
        jrmt = data.get("joint_risk_multiplier_table", {})
        if "table_hash" in jrmt:
            raise RuntimeError(
                "MANIFEST_TABLEHASH_PRESENT: joint_risk_multiplier_table must not "
                "contain a table_hash key per Manifest Authority Policy."
            )

        # MVI-03: Extract the three FAS v6.1.0 constants.
        try:
            thresholds = data["thresholds"]
            shock_cap  = float(thresholds["shock_exposure_cap"])
            max_dd     = float(thresholds["max_drawdown_threshold"])
            vol_trig   = float(thresholds["vol_compression_trigger"])
        except (KeyError, ValueError) as exc:
            raise RuntimeError(
                f"INTEGRITY_FAILURE: Missing or invalid threshold key in manifest: {exc}"
            ) from exc

        # MVI-04: Verify the three extracted constants equal FAS v6.1.0 values.
        if not self._floats_equal(shock_cap, self._EXPECTED_SHOCK_EXPOSURE_CAP):
            raise RuntimeError(
                f"MANIFEST_CONSTANT_MISMATCH: shock_exposure_cap={shock_cap} "
                f"expected {self._EXPECTED_SHOCK_EXPOSURE_CAP}."
            )
        if not self._floats_equal(max_dd, self._EXPECTED_MAX_DRAWDOWN_THRESHOLD):
            raise RuntimeError(
                f"MANIFEST_CONSTANT_MISMATCH: max_drawdown_threshold={max_dd} "
                f"expected {self._EXPECTED_MAX_DRAWDOWN_THRESHOLD}."
            )
        if not self._floats_equal(vol_trig, self._EXPECTED_VOL_COMPRESSION_TRIGGER):
            raise RuntimeError(
                f"MANIFEST_CONSTANT_MISMATCH: vol_compression_trigger={vol_trig} "
                f"expected {self._EXPECTED_VOL_COMPRESSION_TRIGGER}."
            )

        # MVI-06: Return computed hash for propagation into ExecutionRecords.
        return computed_hash, thresholds

    def xǁManifestValidatorǁvalidate__mutmut_56(self) -> Tuple[str, Dict[str, Any]]:
        """
        Execute full manifest validation.

        Returns:
          (computed_hash, thresholds_dict)
          computed_hash -- SHA-256 hex digest of the manifest content.
          thresholds    -- dict from manifest["thresholds"] section.

        Raises RuntimeError with failure_type_id prefix on any hard failure.
        Failure types raised here:
          MANIFEST_HASH_MISMATCH    -- MVI-02
          MANIFEST_CONSTANT_MISMATCH -- MVI-04
          MANIFEST_TABLEHASH_PRESENT -- MVI-05
          INTEGRITY_FAILURE          -- missing file or parse error
        """
        # MVI-01: Load manifest file.
        if not self.manifest_path.exists():
            raise RuntimeError(
                "INTEGRITY_FAILURE: THRESHOLD_MANIFEST.json not found at "
                f"{self.manifest_path}. Harness cannot start without manifest."
            )

        try:
            with open(self.manifest_path, "r", encoding="utf-8") as f:
                raw = f.read()
            data = json.loads(raw)
        except Exception as exc:
            raise RuntimeError(
                f"INTEGRITY_FAILURE: Failed to load or parse THRESHOLD_MANIFEST.json: {exc}"
            ) from exc

        # MVI-01: Compute hash excluding manifest_hash field.
        data_for_hash = {k: v for k, v in data.items() if k != "manifest_hash"}
        computed_hash = hashlib.sha256(
            json.dumps(data_for_hash, sort_keys=True, separators=(",", ":")).encode("utf-8")
        ).hexdigest()

        # MVI-02: Verify computed hash matches stored manifest_hash.
        stored_hash = data.get("manifest_hash", "")
        if (
            stored_hash
            and stored_hash != "BUILD_TIME_PLACEHOLDER"
            and stored_hash != computed_hash
        ):
            raise RuntimeError(
                f"MANIFEST_HASH_MISMATCH: Computed hash {computed_hash[:16]}... "
                f"does not match stored hash {stored_hash[:16]}... "
                "system start denied. possible tampering."
            )

        # MVI-05: Check for absence of table_hash in joint_risk_multiplier_table.
        jrmt = data.get("joint_risk_multiplier_table", {})
        if "table_hash" in jrmt:
            raise RuntimeError(
                "MANIFEST_TABLEHASH_PRESENT: joint_risk_multiplier_table must not "
                "contain a table_hash key per Manifest Authority Policy."
            )

        # MVI-03: Extract the three FAS v6.1.0 constants.
        try:
            thresholds = data["thresholds"]
            shock_cap  = float(thresholds["shock_exposure_cap"])
            max_dd     = float(thresholds["max_drawdown_threshold"])
            vol_trig   = float(thresholds["vol_compression_trigger"])
        except (KeyError, ValueError) as exc:
            raise RuntimeError(
                f"INTEGRITY_FAILURE: Missing or invalid threshold key in manifest: {exc}"
            ) from exc

        # MVI-04: Verify the three extracted constants equal FAS v6.1.0 values.
        if not self._floats_equal(shock_cap, self._EXPECTED_SHOCK_EXPOSURE_CAP):
            raise RuntimeError(
                f"MANIFEST_CONSTANT_MISMATCH: shock_exposure_cap={shock_cap} "
                f"expected {self._EXPECTED_SHOCK_EXPOSURE_CAP}."
            )
        if not self._floats_equal(max_dd, self._EXPECTED_MAX_DRAWDOWN_THRESHOLD):
            raise RuntimeError(
                f"MANIFEST_CONSTANT_MISMATCH: max_drawdown_threshold={max_dd} "
                f"expected {self._EXPECTED_MAX_DRAWDOWN_THRESHOLD}."
            )
        if not self._floats_equal(vol_trig, self._EXPECTED_VOL_COMPRESSION_TRIGGER):
            raise RuntimeError(
                f"MANIFEST_CONSTANT_MISMATCH: vol_compression_trigger={vol_trig} "
                f"expected {self._EXPECTED_VOL_COMPRESSION_TRIGGER}."
            )

        # MVI-06: Return computed hash for propagation into ExecutionRecords.
        return computed_hash, thresholds

    def xǁManifestValidatorǁvalidate__mutmut_57(self) -> Tuple[str, Dict[str, Any]]:
        """
        Execute full manifest validation.

        Returns:
          (computed_hash, thresholds_dict)
          computed_hash -- SHA-256 hex digest of the manifest content.
          thresholds    -- dict from manifest["thresholds"] section.

        Raises RuntimeError with failure_type_id prefix on any hard failure.
        Failure types raised here:
          MANIFEST_HASH_MISMATCH    -- MVI-02
          MANIFEST_CONSTANT_MISMATCH -- MVI-04
          MANIFEST_TABLEHASH_PRESENT -- MVI-05
          INTEGRITY_FAILURE          -- missing file or parse error
        """
        # MVI-01: Load manifest file.
        if not self.manifest_path.exists():
            raise RuntimeError(
                "INTEGRITY_FAILURE: THRESHOLD_MANIFEST.json not found at "
                f"{self.manifest_path}. Harness cannot start without manifest."
            )

        try:
            with open(self.manifest_path, "r", encoding="utf-8") as f:
                raw = f.read()
            data = json.loads(raw)
        except Exception as exc:
            raise RuntimeError(
                f"INTEGRITY_FAILURE: Failed to load or parse THRESHOLD_MANIFEST.json: {exc}"
            ) from exc

        # MVI-01: Compute hash excluding manifest_hash field.
        data_for_hash = {k: v for k, v in data.items() if k != "manifest_hash"}
        computed_hash = hashlib.sha256(
            json.dumps(data_for_hash, sort_keys=True, separators=(",", ":")).encode("utf-8")
        ).hexdigest()

        # MVI-02: Verify computed hash matches stored manifest_hash.
        stored_hash = data.get("manifest_hash", "")
        if (
            stored_hash
            and stored_hash != "BUILD_TIME_PLACEHOLDER"
            and stored_hash != computed_hash
        ):
            raise RuntimeError(
                f"MANIFEST_HASH_MISMATCH: Computed hash {computed_hash[:16]}... "
                f"does not match stored hash {stored_hash[:16]}... "
                "SYSTEM START DENIED. POSSIBLE TAMPERING."
            )

        # MVI-05: Check for absence of table_hash in joint_risk_multiplier_table.
        jrmt = data.get("joint_risk_multiplier_table", {})
        if "table_hash" in jrmt:
            raise RuntimeError(
                "MANIFEST_TABLEHASH_PRESENT: joint_risk_multiplier_table must not "
                "contain a table_hash key per Manifest Authority Policy."
            )

        # MVI-03: Extract the three FAS v6.1.0 constants.
        try:
            thresholds = data["thresholds"]
            shock_cap  = float(thresholds["shock_exposure_cap"])
            max_dd     = float(thresholds["max_drawdown_threshold"])
            vol_trig   = float(thresholds["vol_compression_trigger"])
        except (KeyError, ValueError) as exc:
            raise RuntimeError(
                f"INTEGRITY_FAILURE: Missing or invalid threshold key in manifest: {exc}"
            ) from exc

        # MVI-04: Verify the three extracted constants equal FAS v6.1.0 values.
        if not self._floats_equal(shock_cap, self._EXPECTED_SHOCK_EXPOSURE_CAP):
            raise RuntimeError(
                f"MANIFEST_CONSTANT_MISMATCH: shock_exposure_cap={shock_cap} "
                f"expected {self._EXPECTED_SHOCK_EXPOSURE_CAP}."
            )
        if not self._floats_equal(max_dd, self._EXPECTED_MAX_DRAWDOWN_THRESHOLD):
            raise RuntimeError(
                f"MANIFEST_CONSTANT_MISMATCH: max_drawdown_threshold={max_dd} "
                f"expected {self._EXPECTED_MAX_DRAWDOWN_THRESHOLD}."
            )
        if not self._floats_equal(vol_trig, self._EXPECTED_VOL_COMPRESSION_TRIGGER):
            raise RuntimeError(
                f"MANIFEST_CONSTANT_MISMATCH: vol_compression_trigger={vol_trig} "
                f"expected {self._EXPECTED_VOL_COMPRESSION_TRIGGER}."
            )

        # MVI-06: Return computed hash for propagation into ExecutionRecords.
        return computed_hash, thresholds

    def xǁManifestValidatorǁvalidate__mutmut_58(self) -> Tuple[str, Dict[str, Any]]:
        """
        Execute full manifest validation.

        Returns:
          (computed_hash, thresholds_dict)
          computed_hash -- SHA-256 hex digest of the manifest content.
          thresholds    -- dict from manifest["thresholds"] section.

        Raises RuntimeError with failure_type_id prefix on any hard failure.
        Failure types raised here:
          MANIFEST_HASH_MISMATCH    -- MVI-02
          MANIFEST_CONSTANT_MISMATCH -- MVI-04
          MANIFEST_TABLEHASH_PRESENT -- MVI-05
          INTEGRITY_FAILURE          -- missing file or parse error
        """
        # MVI-01: Load manifest file.
        if not self.manifest_path.exists():
            raise RuntimeError(
                "INTEGRITY_FAILURE: THRESHOLD_MANIFEST.json not found at "
                f"{self.manifest_path}. Harness cannot start without manifest."
            )

        try:
            with open(self.manifest_path, "r", encoding="utf-8") as f:
                raw = f.read()
            data = json.loads(raw)
        except Exception as exc:
            raise RuntimeError(
                f"INTEGRITY_FAILURE: Failed to load or parse THRESHOLD_MANIFEST.json: {exc}"
            ) from exc

        # MVI-01: Compute hash excluding manifest_hash field.
        data_for_hash = {k: v for k, v in data.items() if k != "manifest_hash"}
        computed_hash = hashlib.sha256(
            json.dumps(data_for_hash, sort_keys=True, separators=(",", ":")).encode("utf-8")
        ).hexdigest()

        # MVI-02: Verify computed hash matches stored manifest_hash.
        stored_hash = data.get("manifest_hash", "")
        if (
            stored_hash
            and stored_hash != "BUILD_TIME_PLACEHOLDER"
            and stored_hash != computed_hash
        ):
            raise RuntimeError(
                f"MANIFEST_HASH_MISMATCH: Computed hash {computed_hash[:16]}... "
                f"does not match stored hash {stored_hash[:16]}... "
                "System start denied. Possible tampering."
            )

        # MVI-05: Check for absence of table_hash in joint_risk_multiplier_table.
        jrmt = None
        if "table_hash" in jrmt:
            raise RuntimeError(
                "MANIFEST_TABLEHASH_PRESENT: joint_risk_multiplier_table must not "
                "contain a table_hash key per Manifest Authority Policy."
            )

        # MVI-03: Extract the three FAS v6.1.0 constants.
        try:
            thresholds = data["thresholds"]
            shock_cap  = float(thresholds["shock_exposure_cap"])
            max_dd     = float(thresholds["max_drawdown_threshold"])
            vol_trig   = float(thresholds["vol_compression_trigger"])
        except (KeyError, ValueError) as exc:
            raise RuntimeError(
                f"INTEGRITY_FAILURE: Missing or invalid threshold key in manifest: {exc}"
            ) from exc

        # MVI-04: Verify the three extracted constants equal FAS v6.1.0 values.
        if not self._floats_equal(shock_cap, self._EXPECTED_SHOCK_EXPOSURE_CAP):
            raise RuntimeError(
                f"MANIFEST_CONSTANT_MISMATCH: shock_exposure_cap={shock_cap} "
                f"expected {self._EXPECTED_SHOCK_EXPOSURE_CAP}."
            )
        if not self._floats_equal(max_dd, self._EXPECTED_MAX_DRAWDOWN_THRESHOLD):
            raise RuntimeError(
                f"MANIFEST_CONSTANT_MISMATCH: max_drawdown_threshold={max_dd} "
                f"expected {self._EXPECTED_MAX_DRAWDOWN_THRESHOLD}."
            )
        if not self._floats_equal(vol_trig, self._EXPECTED_VOL_COMPRESSION_TRIGGER):
            raise RuntimeError(
                f"MANIFEST_CONSTANT_MISMATCH: vol_compression_trigger={vol_trig} "
                f"expected {self._EXPECTED_VOL_COMPRESSION_TRIGGER}."
            )

        # MVI-06: Return computed hash for propagation into ExecutionRecords.
        return computed_hash, thresholds

    def xǁManifestValidatorǁvalidate__mutmut_59(self) -> Tuple[str, Dict[str, Any]]:
        """
        Execute full manifest validation.

        Returns:
          (computed_hash, thresholds_dict)
          computed_hash -- SHA-256 hex digest of the manifest content.
          thresholds    -- dict from manifest["thresholds"] section.

        Raises RuntimeError with failure_type_id prefix on any hard failure.
        Failure types raised here:
          MANIFEST_HASH_MISMATCH    -- MVI-02
          MANIFEST_CONSTANT_MISMATCH -- MVI-04
          MANIFEST_TABLEHASH_PRESENT -- MVI-05
          INTEGRITY_FAILURE          -- missing file or parse error
        """
        # MVI-01: Load manifest file.
        if not self.manifest_path.exists():
            raise RuntimeError(
                "INTEGRITY_FAILURE: THRESHOLD_MANIFEST.json not found at "
                f"{self.manifest_path}. Harness cannot start without manifest."
            )

        try:
            with open(self.manifest_path, "r", encoding="utf-8") as f:
                raw = f.read()
            data = json.loads(raw)
        except Exception as exc:
            raise RuntimeError(
                f"INTEGRITY_FAILURE: Failed to load or parse THRESHOLD_MANIFEST.json: {exc}"
            ) from exc

        # MVI-01: Compute hash excluding manifest_hash field.
        data_for_hash = {k: v for k, v in data.items() if k != "manifest_hash"}
        computed_hash = hashlib.sha256(
            json.dumps(data_for_hash, sort_keys=True, separators=(",", ":")).encode("utf-8")
        ).hexdigest()

        # MVI-02: Verify computed hash matches stored manifest_hash.
        stored_hash = data.get("manifest_hash", "")
        if (
            stored_hash
            and stored_hash != "BUILD_TIME_PLACEHOLDER"
            and stored_hash != computed_hash
        ):
            raise RuntimeError(
                f"MANIFEST_HASH_MISMATCH: Computed hash {computed_hash[:16]}... "
                f"does not match stored hash {stored_hash[:16]}... "
                "System start denied. Possible tampering."
            )

        # MVI-05: Check for absence of table_hash in joint_risk_multiplier_table.
        jrmt = data.get(None, {})
        if "table_hash" in jrmt:
            raise RuntimeError(
                "MANIFEST_TABLEHASH_PRESENT: joint_risk_multiplier_table must not "
                "contain a table_hash key per Manifest Authority Policy."
            )

        # MVI-03: Extract the three FAS v6.1.0 constants.
        try:
            thresholds = data["thresholds"]
            shock_cap  = float(thresholds["shock_exposure_cap"])
            max_dd     = float(thresholds["max_drawdown_threshold"])
            vol_trig   = float(thresholds["vol_compression_trigger"])
        except (KeyError, ValueError) as exc:
            raise RuntimeError(
                f"INTEGRITY_FAILURE: Missing or invalid threshold key in manifest: {exc}"
            ) from exc

        # MVI-04: Verify the three extracted constants equal FAS v6.1.0 values.
        if not self._floats_equal(shock_cap, self._EXPECTED_SHOCK_EXPOSURE_CAP):
            raise RuntimeError(
                f"MANIFEST_CONSTANT_MISMATCH: shock_exposure_cap={shock_cap} "
                f"expected {self._EXPECTED_SHOCK_EXPOSURE_CAP}."
            )
        if not self._floats_equal(max_dd, self._EXPECTED_MAX_DRAWDOWN_THRESHOLD):
            raise RuntimeError(
                f"MANIFEST_CONSTANT_MISMATCH: max_drawdown_threshold={max_dd} "
                f"expected {self._EXPECTED_MAX_DRAWDOWN_THRESHOLD}."
            )
        if not self._floats_equal(vol_trig, self._EXPECTED_VOL_COMPRESSION_TRIGGER):
            raise RuntimeError(
                f"MANIFEST_CONSTANT_MISMATCH: vol_compression_trigger={vol_trig} "
                f"expected {self._EXPECTED_VOL_COMPRESSION_TRIGGER}."
            )

        # MVI-06: Return computed hash for propagation into ExecutionRecords.
        return computed_hash, thresholds

    def xǁManifestValidatorǁvalidate__mutmut_60(self) -> Tuple[str, Dict[str, Any]]:
        """
        Execute full manifest validation.

        Returns:
          (computed_hash, thresholds_dict)
          computed_hash -- SHA-256 hex digest of the manifest content.
          thresholds    -- dict from manifest["thresholds"] section.

        Raises RuntimeError with failure_type_id prefix on any hard failure.
        Failure types raised here:
          MANIFEST_HASH_MISMATCH    -- MVI-02
          MANIFEST_CONSTANT_MISMATCH -- MVI-04
          MANIFEST_TABLEHASH_PRESENT -- MVI-05
          INTEGRITY_FAILURE          -- missing file or parse error
        """
        # MVI-01: Load manifest file.
        if not self.manifest_path.exists():
            raise RuntimeError(
                "INTEGRITY_FAILURE: THRESHOLD_MANIFEST.json not found at "
                f"{self.manifest_path}. Harness cannot start without manifest."
            )

        try:
            with open(self.manifest_path, "r", encoding="utf-8") as f:
                raw = f.read()
            data = json.loads(raw)
        except Exception as exc:
            raise RuntimeError(
                f"INTEGRITY_FAILURE: Failed to load or parse THRESHOLD_MANIFEST.json: {exc}"
            ) from exc

        # MVI-01: Compute hash excluding manifest_hash field.
        data_for_hash = {k: v for k, v in data.items() if k != "manifest_hash"}
        computed_hash = hashlib.sha256(
            json.dumps(data_for_hash, sort_keys=True, separators=(",", ":")).encode("utf-8")
        ).hexdigest()

        # MVI-02: Verify computed hash matches stored manifest_hash.
        stored_hash = data.get("manifest_hash", "")
        if (
            stored_hash
            and stored_hash != "BUILD_TIME_PLACEHOLDER"
            and stored_hash != computed_hash
        ):
            raise RuntimeError(
                f"MANIFEST_HASH_MISMATCH: Computed hash {computed_hash[:16]}... "
                f"does not match stored hash {stored_hash[:16]}... "
                "System start denied. Possible tampering."
            )

        # MVI-05: Check for absence of table_hash in joint_risk_multiplier_table.
        jrmt = data.get("joint_risk_multiplier_table", None)
        if "table_hash" in jrmt:
            raise RuntimeError(
                "MANIFEST_TABLEHASH_PRESENT: joint_risk_multiplier_table must not "
                "contain a table_hash key per Manifest Authority Policy."
            )

        # MVI-03: Extract the three FAS v6.1.0 constants.
        try:
            thresholds = data["thresholds"]
            shock_cap  = float(thresholds["shock_exposure_cap"])
            max_dd     = float(thresholds["max_drawdown_threshold"])
            vol_trig   = float(thresholds["vol_compression_trigger"])
        except (KeyError, ValueError) as exc:
            raise RuntimeError(
                f"INTEGRITY_FAILURE: Missing or invalid threshold key in manifest: {exc}"
            ) from exc

        # MVI-04: Verify the three extracted constants equal FAS v6.1.0 values.
        if not self._floats_equal(shock_cap, self._EXPECTED_SHOCK_EXPOSURE_CAP):
            raise RuntimeError(
                f"MANIFEST_CONSTANT_MISMATCH: shock_exposure_cap={shock_cap} "
                f"expected {self._EXPECTED_SHOCK_EXPOSURE_CAP}."
            )
        if not self._floats_equal(max_dd, self._EXPECTED_MAX_DRAWDOWN_THRESHOLD):
            raise RuntimeError(
                f"MANIFEST_CONSTANT_MISMATCH: max_drawdown_threshold={max_dd} "
                f"expected {self._EXPECTED_MAX_DRAWDOWN_THRESHOLD}."
            )
        if not self._floats_equal(vol_trig, self._EXPECTED_VOL_COMPRESSION_TRIGGER):
            raise RuntimeError(
                f"MANIFEST_CONSTANT_MISMATCH: vol_compression_trigger={vol_trig} "
                f"expected {self._EXPECTED_VOL_COMPRESSION_TRIGGER}."
            )

        # MVI-06: Return computed hash for propagation into ExecutionRecords.
        return computed_hash, thresholds

    def xǁManifestValidatorǁvalidate__mutmut_61(self) -> Tuple[str, Dict[str, Any]]:
        """
        Execute full manifest validation.

        Returns:
          (computed_hash, thresholds_dict)
          computed_hash -- SHA-256 hex digest of the manifest content.
          thresholds    -- dict from manifest["thresholds"] section.

        Raises RuntimeError with failure_type_id prefix on any hard failure.
        Failure types raised here:
          MANIFEST_HASH_MISMATCH    -- MVI-02
          MANIFEST_CONSTANT_MISMATCH -- MVI-04
          MANIFEST_TABLEHASH_PRESENT -- MVI-05
          INTEGRITY_FAILURE          -- missing file or parse error
        """
        # MVI-01: Load manifest file.
        if not self.manifest_path.exists():
            raise RuntimeError(
                "INTEGRITY_FAILURE: THRESHOLD_MANIFEST.json not found at "
                f"{self.manifest_path}. Harness cannot start without manifest."
            )

        try:
            with open(self.manifest_path, "r", encoding="utf-8") as f:
                raw = f.read()
            data = json.loads(raw)
        except Exception as exc:
            raise RuntimeError(
                f"INTEGRITY_FAILURE: Failed to load or parse THRESHOLD_MANIFEST.json: {exc}"
            ) from exc

        # MVI-01: Compute hash excluding manifest_hash field.
        data_for_hash = {k: v for k, v in data.items() if k != "manifest_hash"}
        computed_hash = hashlib.sha256(
            json.dumps(data_for_hash, sort_keys=True, separators=(",", ":")).encode("utf-8")
        ).hexdigest()

        # MVI-02: Verify computed hash matches stored manifest_hash.
        stored_hash = data.get("manifest_hash", "")
        if (
            stored_hash
            and stored_hash != "BUILD_TIME_PLACEHOLDER"
            and stored_hash != computed_hash
        ):
            raise RuntimeError(
                f"MANIFEST_HASH_MISMATCH: Computed hash {computed_hash[:16]}... "
                f"does not match stored hash {stored_hash[:16]}... "
                "System start denied. Possible tampering."
            )

        # MVI-05: Check for absence of table_hash in joint_risk_multiplier_table.
        jrmt = data.get({})
        if "table_hash" in jrmt:
            raise RuntimeError(
                "MANIFEST_TABLEHASH_PRESENT: joint_risk_multiplier_table must not "
                "contain a table_hash key per Manifest Authority Policy."
            )

        # MVI-03: Extract the three FAS v6.1.0 constants.
        try:
            thresholds = data["thresholds"]
            shock_cap  = float(thresholds["shock_exposure_cap"])
            max_dd     = float(thresholds["max_drawdown_threshold"])
            vol_trig   = float(thresholds["vol_compression_trigger"])
        except (KeyError, ValueError) as exc:
            raise RuntimeError(
                f"INTEGRITY_FAILURE: Missing or invalid threshold key in manifest: {exc}"
            ) from exc

        # MVI-04: Verify the three extracted constants equal FAS v6.1.0 values.
        if not self._floats_equal(shock_cap, self._EXPECTED_SHOCK_EXPOSURE_CAP):
            raise RuntimeError(
                f"MANIFEST_CONSTANT_MISMATCH: shock_exposure_cap={shock_cap} "
                f"expected {self._EXPECTED_SHOCK_EXPOSURE_CAP}."
            )
        if not self._floats_equal(max_dd, self._EXPECTED_MAX_DRAWDOWN_THRESHOLD):
            raise RuntimeError(
                f"MANIFEST_CONSTANT_MISMATCH: max_drawdown_threshold={max_dd} "
                f"expected {self._EXPECTED_MAX_DRAWDOWN_THRESHOLD}."
            )
        if not self._floats_equal(vol_trig, self._EXPECTED_VOL_COMPRESSION_TRIGGER):
            raise RuntimeError(
                f"MANIFEST_CONSTANT_MISMATCH: vol_compression_trigger={vol_trig} "
                f"expected {self._EXPECTED_VOL_COMPRESSION_TRIGGER}."
            )

        # MVI-06: Return computed hash for propagation into ExecutionRecords.
        return computed_hash, thresholds

    def xǁManifestValidatorǁvalidate__mutmut_62(self) -> Tuple[str, Dict[str, Any]]:
        """
        Execute full manifest validation.

        Returns:
          (computed_hash, thresholds_dict)
          computed_hash -- SHA-256 hex digest of the manifest content.
          thresholds    -- dict from manifest["thresholds"] section.

        Raises RuntimeError with failure_type_id prefix on any hard failure.
        Failure types raised here:
          MANIFEST_HASH_MISMATCH    -- MVI-02
          MANIFEST_CONSTANT_MISMATCH -- MVI-04
          MANIFEST_TABLEHASH_PRESENT -- MVI-05
          INTEGRITY_FAILURE          -- missing file or parse error
        """
        # MVI-01: Load manifest file.
        if not self.manifest_path.exists():
            raise RuntimeError(
                "INTEGRITY_FAILURE: THRESHOLD_MANIFEST.json not found at "
                f"{self.manifest_path}. Harness cannot start without manifest."
            )

        try:
            with open(self.manifest_path, "r", encoding="utf-8") as f:
                raw = f.read()
            data = json.loads(raw)
        except Exception as exc:
            raise RuntimeError(
                f"INTEGRITY_FAILURE: Failed to load or parse THRESHOLD_MANIFEST.json: {exc}"
            ) from exc

        # MVI-01: Compute hash excluding manifest_hash field.
        data_for_hash = {k: v for k, v in data.items() if k != "manifest_hash"}
        computed_hash = hashlib.sha256(
            json.dumps(data_for_hash, sort_keys=True, separators=(",", ":")).encode("utf-8")
        ).hexdigest()

        # MVI-02: Verify computed hash matches stored manifest_hash.
        stored_hash = data.get("manifest_hash", "")
        if (
            stored_hash
            and stored_hash != "BUILD_TIME_PLACEHOLDER"
            and stored_hash != computed_hash
        ):
            raise RuntimeError(
                f"MANIFEST_HASH_MISMATCH: Computed hash {computed_hash[:16]}... "
                f"does not match stored hash {stored_hash[:16]}... "
                "System start denied. Possible tampering."
            )

        # MVI-05: Check for absence of table_hash in joint_risk_multiplier_table.
        jrmt = data.get("joint_risk_multiplier_table", )
        if "table_hash" in jrmt:
            raise RuntimeError(
                "MANIFEST_TABLEHASH_PRESENT: joint_risk_multiplier_table must not "
                "contain a table_hash key per Manifest Authority Policy."
            )

        # MVI-03: Extract the three FAS v6.1.0 constants.
        try:
            thresholds = data["thresholds"]
            shock_cap  = float(thresholds["shock_exposure_cap"])
            max_dd     = float(thresholds["max_drawdown_threshold"])
            vol_trig   = float(thresholds["vol_compression_trigger"])
        except (KeyError, ValueError) as exc:
            raise RuntimeError(
                f"INTEGRITY_FAILURE: Missing or invalid threshold key in manifest: {exc}"
            ) from exc

        # MVI-04: Verify the three extracted constants equal FAS v6.1.0 values.
        if not self._floats_equal(shock_cap, self._EXPECTED_SHOCK_EXPOSURE_CAP):
            raise RuntimeError(
                f"MANIFEST_CONSTANT_MISMATCH: shock_exposure_cap={shock_cap} "
                f"expected {self._EXPECTED_SHOCK_EXPOSURE_CAP}."
            )
        if not self._floats_equal(max_dd, self._EXPECTED_MAX_DRAWDOWN_THRESHOLD):
            raise RuntimeError(
                f"MANIFEST_CONSTANT_MISMATCH: max_drawdown_threshold={max_dd} "
                f"expected {self._EXPECTED_MAX_DRAWDOWN_THRESHOLD}."
            )
        if not self._floats_equal(vol_trig, self._EXPECTED_VOL_COMPRESSION_TRIGGER):
            raise RuntimeError(
                f"MANIFEST_CONSTANT_MISMATCH: vol_compression_trigger={vol_trig} "
                f"expected {self._EXPECTED_VOL_COMPRESSION_TRIGGER}."
            )

        # MVI-06: Return computed hash for propagation into ExecutionRecords.
        return computed_hash, thresholds

    def xǁManifestValidatorǁvalidate__mutmut_63(self) -> Tuple[str, Dict[str, Any]]:
        """
        Execute full manifest validation.

        Returns:
          (computed_hash, thresholds_dict)
          computed_hash -- SHA-256 hex digest of the manifest content.
          thresholds    -- dict from manifest["thresholds"] section.

        Raises RuntimeError with failure_type_id prefix on any hard failure.
        Failure types raised here:
          MANIFEST_HASH_MISMATCH    -- MVI-02
          MANIFEST_CONSTANT_MISMATCH -- MVI-04
          MANIFEST_TABLEHASH_PRESENT -- MVI-05
          INTEGRITY_FAILURE          -- missing file or parse error
        """
        # MVI-01: Load manifest file.
        if not self.manifest_path.exists():
            raise RuntimeError(
                "INTEGRITY_FAILURE: THRESHOLD_MANIFEST.json not found at "
                f"{self.manifest_path}. Harness cannot start without manifest."
            )

        try:
            with open(self.manifest_path, "r", encoding="utf-8") as f:
                raw = f.read()
            data = json.loads(raw)
        except Exception as exc:
            raise RuntimeError(
                f"INTEGRITY_FAILURE: Failed to load or parse THRESHOLD_MANIFEST.json: {exc}"
            ) from exc

        # MVI-01: Compute hash excluding manifest_hash field.
        data_for_hash = {k: v for k, v in data.items() if k != "manifest_hash"}
        computed_hash = hashlib.sha256(
            json.dumps(data_for_hash, sort_keys=True, separators=(",", ":")).encode("utf-8")
        ).hexdigest()

        # MVI-02: Verify computed hash matches stored manifest_hash.
        stored_hash = data.get("manifest_hash", "")
        if (
            stored_hash
            and stored_hash != "BUILD_TIME_PLACEHOLDER"
            and stored_hash != computed_hash
        ):
            raise RuntimeError(
                f"MANIFEST_HASH_MISMATCH: Computed hash {computed_hash[:16]}... "
                f"does not match stored hash {stored_hash[:16]}... "
                "System start denied. Possible tampering."
            )

        # MVI-05: Check for absence of table_hash in joint_risk_multiplier_table.
        jrmt = data.get("XXjoint_risk_multiplier_tableXX", {})
        if "table_hash" in jrmt:
            raise RuntimeError(
                "MANIFEST_TABLEHASH_PRESENT: joint_risk_multiplier_table must not "
                "contain a table_hash key per Manifest Authority Policy."
            )

        # MVI-03: Extract the three FAS v6.1.0 constants.
        try:
            thresholds = data["thresholds"]
            shock_cap  = float(thresholds["shock_exposure_cap"])
            max_dd     = float(thresholds["max_drawdown_threshold"])
            vol_trig   = float(thresholds["vol_compression_trigger"])
        except (KeyError, ValueError) as exc:
            raise RuntimeError(
                f"INTEGRITY_FAILURE: Missing or invalid threshold key in manifest: {exc}"
            ) from exc

        # MVI-04: Verify the three extracted constants equal FAS v6.1.0 values.
        if not self._floats_equal(shock_cap, self._EXPECTED_SHOCK_EXPOSURE_CAP):
            raise RuntimeError(
                f"MANIFEST_CONSTANT_MISMATCH: shock_exposure_cap={shock_cap} "
                f"expected {self._EXPECTED_SHOCK_EXPOSURE_CAP}."
            )
        if not self._floats_equal(max_dd, self._EXPECTED_MAX_DRAWDOWN_THRESHOLD):
            raise RuntimeError(
                f"MANIFEST_CONSTANT_MISMATCH: max_drawdown_threshold={max_dd} "
                f"expected {self._EXPECTED_MAX_DRAWDOWN_THRESHOLD}."
            )
        if not self._floats_equal(vol_trig, self._EXPECTED_VOL_COMPRESSION_TRIGGER):
            raise RuntimeError(
                f"MANIFEST_CONSTANT_MISMATCH: vol_compression_trigger={vol_trig} "
                f"expected {self._EXPECTED_VOL_COMPRESSION_TRIGGER}."
            )

        # MVI-06: Return computed hash for propagation into ExecutionRecords.
        return computed_hash, thresholds

    def xǁManifestValidatorǁvalidate__mutmut_64(self) -> Tuple[str, Dict[str, Any]]:
        """
        Execute full manifest validation.

        Returns:
          (computed_hash, thresholds_dict)
          computed_hash -- SHA-256 hex digest of the manifest content.
          thresholds    -- dict from manifest["thresholds"] section.

        Raises RuntimeError with failure_type_id prefix on any hard failure.
        Failure types raised here:
          MANIFEST_HASH_MISMATCH    -- MVI-02
          MANIFEST_CONSTANT_MISMATCH -- MVI-04
          MANIFEST_TABLEHASH_PRESENT -- MVI-05
          INTEGRITY_FAILURE          -- missing file or parse error
        """
        # MVI-01: Load manifest file.
        if not self.manifest_path.exists():
            raise RuntimeError(
                "INTEGRITY_FAILURE: THRESHOLD_MANIFEST.json not found at "
                f"{self.manifest_path}. Harness cannot start without manifest."
            )

        try:
            with open(self.manifest_path, "r", encoding="utf-8") as f:
                raw = f.read()
            data = json.loads(raw)
        except Exception as exc:
            raise RuntimeError(
                f"INTEGRITY_FAILURE: Failed to load or parse THRESHOLD_MANIFEST.json: {exc}"
            ) from exc

        # MVI-01: Compute hash excluding manifest_hash field.
        data_for_hash = {k: v for k, v in data.items() if k != "manifest_hash"}
        computed_hash = hashlib.sha256(
            json.dumps(data_for_hash, sort_keys=True, separators=(",", ":")).encode("utf-8")
        ).hexdigest()

        # MVI-02: Verify computed hash matches stored manifest_hash.
        stored_hash = data.get("manifest_hash", "")
        if (
            stored_hash
            and stored_hash != "BUILD_TIME_PLACEHOLDER"
            and stored_hash != computed_hash
        ):
            raise RuntimeError(
                f"MANIFEST_HASH_MISMATCH: Computed hash {computed_hash[:16]}... "
                f"does not match stored hash {stored_hash[:16]}... "
                "System start denied. Possible tampering."
            )

        # MVI-05: Check for absence of table_hash in joint_risk_multiplier_table.
        jrmt = data.get("JOINT_RISK_MULTIPLIER_TABLE", {})
        if "table_hash" in jrmt:
            raise RuntimeError(
                "MANIFEST_TABLEHASH_PRESENT: joint_risk_multiplier_table must not "
                "contain a table_hash key per Manifest Authority Policy."
            )

        # MVI-03: Extract the three FAS v6.1.0 constants.
        try:
            thresholds = data["thresholds"]
            shock_cap  = float(thresholds["shock_exposure_cap"])
            max_dd     = float(thresholds["max_drawdown_threshold"])
            vol_trig   = float(thresholds["vol_compression_trigger"])
        except (KeyError, ValueError) as exc:
            raise RuntimeError(
                f"INTEGRITY_FAILURE: Missing or invalid threshold key in manifest: {exc}"
            ) from exc

        # MVI-04: Verify the three extracted constants equal FAS v6.1.0 values.
        if not self._floats_equal(shock_cap, self._EXPECTED_SHOCK_EXPOSURE_CAP):
            raise RuntimeError(
                f"MANIFEST_CONSTANT_MISMATCH: shock_exposure_cap={shock_cap} "
                f"expected {self._EXPECTED_SHOCK_EXPOSURE_CAP}."
            )
        if not self._floats_equal(max_dd, self._EXPECTED_MAX_DRAWDOWN_THRESHOLD):
            raise RuntimeError(
                f"MANIFEST_CONSTANT_MISMATCH: max_drawdown_threshold={max_dd} "
                f"expected {self._EXPECTED_MAX_DRAWDOWN_THRESHOLD}."
            )
        if not self._floats_equal(vol_trig, self._EXPECTED_VOL_COMPRESSION_TRIGGER):
            raise RuntimeError(
                f"MANIFEST_CONSTANT_MISMATCH: vol_compression_trigger={vol_trig} "
                f"expected {self._EXPECTED_VOL_COMPRESSION_TRIGGER}."
            )

        # MVI-06: Return computed hash for propagation into ExecutionRecords.
        return computed_hash, thresholds

    def xǁManifestValidatorǁvalidate__mutmut_65(self) -> Tuple[str, Dict[str, Any]]:
        """
        Execute full manifest validation.

        Returns:
          (computed_hash, thresholds_dict)
          computed_hash -- SHA-256 hex digest of the manifest content.
          thresholds    -- dict from manifest["thresholds"] section.

        Raises RuntimeError with failure_type_id prefix on any hard failure.
        Failure types raised here:
          MANIFEST_HASH_MISMATCH    -- MVI-02
          MANIFEST_CONSTANT_MISMATCH -- MVI-04
          MANIFEST_TABLEHASH_PRESENT -- MVI-05
          INTEGRITY_FAILURE          -- missing file or parse error
        """
        # MVI-01: Load manifest file.
        if not self.manifest_path.exists():
            raise RuntimeError(
                "INTEGRITY_FAILURE: THRESHOLD_MANIFEST.json not found at "
                f"{self.manifest_path}. Harness cannot start without manifest."
            )

        try:
            with open(self.manifest_path, "r", encoding="utf-8") as f:
                raw = f.read()
            data = json.loads(raw)
        except Exception as exc:
            raise RuntimeError(
                f"INTEGRITY_FAILURE: Failed to load or parse THRESHOLD_MANIFEST.json: {exc}"
            ) from exc

        # MVI-01: Compute hash excluding manifest_hash field.
        data_for_hash = {k: v for k, v in data.items() if k != "manifest_hash"}
        computed_hash = hashlib.sha256(
            json.dumps(data_for_hash, sort_keys=True, separators=(",", ":")).encode("utf-8")
        ).hexdigest()

        # MVI-02: Verify computed hash matches stored manifest_hash.
        stored_hash = data.get("manifest_hash", "")
        if (
            stored_hash
            and stored_hash != "BUILD_TIME_PLACEHOLDER"
            and stored_hash != computed_hash
        ):
            raise RuntimeError(
                f"MANIFEST_HASH_MISMATCH: Computed hash {computed_hash[:16]}... "
                f"does not match stored hash {stored_hash[:16]}... "
                "System start denied. Possible tampering."
            )

        # MVI-05: Check for absence of table_hash in joint_risk_multiplier_table.
        jrmt = data.get("joint_risk_multiplier_table", {})
        if "XXtable_hashXX" in jrmt:
            raise RuntimeError(
                "MANIFEST_TABLEHASH_PRESENT: joint_risk_multiplier_table must not "
                "contain a table_hash key per Manifest Authority Policy."
            )

        # MVI-03: Extract the three FAS v6.1.0 constants.
        try:
            thresholds = data["thresholds"]
            shock_cap  = float(thresholds["shock_exposure_cap"])
            max_dd     = float(thresholds["max_drawdown_threshold"])
            vol_trig   = float(thresholds["vol_compression_trigger"])
        except (KeyError, ValueError) as exc:
            raise RuntimeError(
                f"INTEGRITY_FAILURE: Missing or invalid threshold key in manifest: {exc}"
            ) from exc

        # MVI-04: Verify the three extracted constants equal FAS v6.1.0 values.
        if not self._floats_equal(shock_cap, self._EXPECTED_SHOCK_EXPOSURE_CAP):
            raise RuntimeError(
                f"MANIFEST_CONSTANT_MISMATCH: shock_exposure_cap={shock_cap} "
                f"expected {self._EXPECTED_SHOCK_EXPOSURE_CAP}."
            )
        if not self._floats_equal(max_dd, self._EXPECTED_MAX_DRAWDOWN_THRESHOLD):
            raise RuntimeError(
                f"MANIFEST_CONSTANT_MISMATCH: max_drawdown_threshold={max_dd} "
                f"expected {self._EXPECTED_MAX_DRAWDOWN_THRESHOLD}."
            )
        if not self._floats_equal(vol_trig, self._EXPECTED_VOL_COMPRESSION_TRIGGER):
            raise RuntimeError(
                f"MANIFEST_CONSTANT_MISMATCH: vol_compression_trigger={vol_trig} "
                f"expected {self._EXPECTED_VOL_COMPRESSION_TRIGGER}."
            )

        # MVI-06: Return computed hash for propagation into ExecutionRecords.
        return computed_hash, thresholds

    def xǁManifestValidatorǁvalidate__mutmut_66(self) -> Tuple[str, Dict[str, Any]]:
        """
        Execute full manifest validation.

        Returns:
          (computed_hash, thresholds_dict)
          computed_hash -- SHA-256 hex digest of the manifest content.
          thresholds    -- dict from manifest["thresholds"] section.

        Raises RuntimeError with failure_type_id prefix on any hard failure.
        Failure types raised here:
          MANIFEST_HASH_MISMATCH    -- MVI-02
          MANIFEST_CONSTANT_MISMATCH -- MVI-04
          MANIFEST_TABLEHASH_PRESENT -- MVI-05
          INTEGRITY_FAILURE          -- missing file or parse error
        """
        # MVI-01: Load manifest file.
        if not self.manifest_path.exists():
            raise RuntimeError(
                "INTEGRITY_FAILURE: THRESHOLD_MANIFEST.json not found at "
                f"{self.manifest_path}. Harness cannot start without manifest."
            )

        try:
            with open(self.manifest_path, "r", encoding="utf-8") as f:
                raw = f.read()
            data = json.loads(raw)
        except Exception as exc:
            raise RuntimeError(
                f"INTEGRITY_FAILURE: Failed to load or parse THRESHOLD_MANIFEST.json: {exc}"
            ) from exc

        # MVI-01: Compute hash excluding manifest_hash field.
        data_for_hash = {k: v for k, v in data.items() if k != "manifest_hash"}
        computed_hash = hashlib.sha256(
            json.dumps(data_for_hash, sort_keys=True, separators=(",", ":")).encode("utf-8")
        ).hexdigest()

        # MVI-02: Verify computed hash matches stored manifest_hash.
        stored_hash = data.get("manifest_hash", "")
        if (
            stored_hash
            and stored_hash != "BUILD_TIME_PLACEHOLDER"
            and stored_hash != computed_hash
        ):
            raise RuntimeError(
                f"MANIFEST_HASH_MISMATCH: Computed hash {computed_hash[:16]}... "
                f"does not match stored hash {stored_hash[:16]}... "
                "System start denied. Possible tampering."
            )

        # MVI-05: Check for absence of table_hash in joint_risk_multiplier_table.
        jrmt = data.get("joint_risk_multiplier_table", {})
        if "TABLE_HASH" in jrmt:
            raise RuntimeError(
                "MANIFEST_TABLEHASH_PRESENT: joint_risk_multiplier_table must not "
                "contain a table_hash key per Manifest Authority Policy."
            )

        # MVI-03: Extract the three FAS v6.1.0 constants.
        try:
            thresholds = data["thresholds"]
            shock_cap  = float(thresholds["shock_exposure_cap"])
            max_dd     = float(thresholds["max_drawdown_threshold"])
            vol_trig   = float(thresholds["vol_compression_trigger"])
        except (KeyError, ValueError) as exc:
            raise RuntimeError(
                f"INTEGRITY_FAILURE: Missing or invalid threshold key in manifest: {exc}"
            ) from exc

        # MVI-04: Verify the three extracted constants equal FAS v6.1.0 values.
        if not self._floats_equal(shock_cap, self._EXPECTED_SHOCK_EXPOSURE_CAP):
            raise RuntimeError(
                f"MANIFEST_CONSTANT_MISMATCH: shock_exposure_cap={shock_cap} "
                f"expected {self._EXPECTED_SHOCK_EXPOSURE_CAP}."
            )
        if not self._floats_equal(max_dd, self._EXPECTED_MAX_DRAWDOWN_THRESHOLD):
            raise RuntimeError(
                f"MANIFEST_CONSTANT_MISMATCH: max_drawdown_threshold={max_dd} "
                f"expected {self._EXPECTED_MAX_DRAWDOWN_THRESHOLD}."
            )
        if not self._floats_equal(vol_trig, self._EXPECTED_VOL_COMPRESSION_TRIGGER):
            raise RuntimeError(
                f"MANIFEST_CONSTANT_MISMATCH: vol_compression_trigger={vol_trig} "
                f"expected {self._EXPECTED_VOL_COMPRESSION_TRIGGER}."
            )

        # MVI-06: Return computed hash for propagation into ExecutionRecords.
        return computed_hash, thresholds

    def xǁManifestValidatorǁvalidate__mutmut_67(self) -> Tuple[str, Dict[str, Any]]:
        """
        Execute full manifest validation.

        Returns:
          (computed_hash, thresholds_dict)
          computed_hash -- SHA-256 hex digest of the manifest content.
          thresholds    -- dict from manifest["thresholds"] section.

        Raises RuntimeError with failure_type_id prefix on any hard failure.
        Failure types raised here:
          MANIFEST_HASH_MISMATCH    -- MVI-02
          MANIFEST_CONSTANT_MISMATCH -- MVI-04
          MANIFEST_TABLEHASH_PRESENT -- MVI-05
          INTEGRITY_FAILURE          -- missing file or parse error
        """
        # MVI-01: Load manifest file.
        if not self.manifest_path.exists():
            raise RuntimeError(
                "INTEGRITY_FAILURE: THRESHOLD_MANIFEST.json not found at "
                f"{self.manifest_path}. Harness cannot start without manifest."
            )

        try:
            with open(self.manifest_path, "r", encoding="utf-8") as f:
                raw = f.read()
            data = json.loads(raw)
        except Exception as exc:
            raise RuntimeError(
                f"INTEGRITY_FAILURE: Failed to load or parse THRESHOLD_MANIFEST.json: {exc}"
            ) from exc

        # MVI-01: Compute hash excluding manifest_hash field.
        data_for_hash = {k: v for k, v in data.items() if k != "manifest_hash"}
        computed_hash = hashlib.sha256(
            json.dumps(data_for_hash, sort_keys=True, separators=(",", ":")).encode("utf-8")
        ).hexdigest()

        # MVI-02: Verify computed hash matches stored manifest_hash.
        stored_hash = data.get("manifest_hash", "")
        if (
            stored_hash
            and stored_hash != "BUILD_TIME_PLACEHOLDER"
            and stored_hash != computed_hash
        ):
            raise RuntimeError(
                f"MANIFEST_HASH_MISMATCH: Computed hash {computed_hash[:16]}... "
                f"does not match stored hash {stored_hash[:16]}... "
                "System start denied. Possible tampering."
            )

        # MVI-05: Check for absence of table_hash in joint_risk_multiplier_table.
        jrmt = data.get("joint_risk_multiplier_table", {})
        if "table_hash" not in jrmt:
            raise RuntimeError(
                "MANIFEST_TABLEHASH_PRESENT: joint_risk_multiplier_table must not "
                "contain a table_hash key per Manifest Authority Policy."
            )

        # MVI-03: Extract the three FAS v6.1.0 constants.
        try:
            thresholds = data["thresholds"]
            shock_cap  = float(thresholds["shock_exposure_cap"])
            max_dd     = float(thresholds["max_drawdown_threshold"])
            vol_trig   = float(thresholds["vol_compression_trigger"])
        except (KeyError, ValueError) as exc:
            raise RuntimeError(
                f"INTEGRITY_FAILURE: Missing or invalid threshold key in manifest: {exc}"
            ) from exc

        # MVI-04: Verify the three extracted constants equal FAS v6.1.0 values.
        if not self._floats_equal(shock_cap, self._EXPECTED_SHOCK_EXPOSURE_CAP):
            raise RuntimeError(
                f"MANIFEST_CONSTANT_MISMATCH: shock_exposure_cap={shock_cap} "
                f"expected {self._EXPECTED_SHOCK_EXPOSURE_CAP}."
            )
        if not self._floats_equal(max_dd, self._EXPECTED_MAX_DRAWDOWN_THRESHOLD):
            raise RuntimeError(
                f"MANIFEST_CONSTANT_MISMATCH: max_drawdown_threshold={max_dd} "
                f"expected {self._EXPECTED_MAX_DRAWDOWN_THRESHOLD}."
            )
        if not self._floats_equal(vol_trig, self._EXPECTED_VOL_COMPRESSION_TRIGGER):
            raise RuntimeError(
                f"MANIFEST_CONSTANT_MISMATCH: vol_compression_trigger={vol_trig} "
                f"expected {self._EXPECTED_VOL_COMPRESSION_TRIGGER}."
            )

        # MVI-06: Return computed hash for propagation into ExecutionRecords.
        return computed_hash, thresholds

    def xǁManifestValidatorǁvalidate__mutmut_68(self) -> Tuple[str, Dict[str, Any]]:
        """
        Execute full manifest validation.

        Returns:
          (computed_hash, thresholds_dict)
          computed_hash -- SHA-256 hex digest of the manifest content.
          thresholds    -- dict from manifest["thresholds"] section.

        Raises RuntimeError with failure_type_id prefix on any hard failure.
        Failure types raised here:
          MANIFEST_HASH_MISMATCH    -- MVI-02
          MANIFEST_CONSTANT_MISMATCH -- MVI-04
          MANIFEST_TABLEHASH_PRESENT -- MVI-05
          INTEGRITY_FAILURE          -- missing file or parse error
        """
        # MVI-01: Load manifest file.
        if not self.manifest_path.exists():
            raise RuntimeError(
                "INTEGRITY_FAILURE: THRESHOLD_MANIFEST.json not found at "
                f"{self.manifest_path}. Harness cannot start without manifest."
            )

        try:
            with open(self.manifest_path, "r", encoding="utf-8") as f:
                raw = f.read()
            data = json.loads(raw)
        except Exception as exc:
            raise RuntimeError(
                f"INTEGRITY_FAILURE: Failed to load or parse THRESHOLD_MANIFEST.json: {exc}"
            ) from exc

        # MVI-01: Compute hash excluding manifest_hash field.
        data_for_hash = {k: v for k, v in data.items() if k != "manifest_hash"}
        computed_hash = hashlib.sha256(
            json.dumps(data_for_hash, sort_keys=True, separators=(",", ":")).encode("utf-8")
        ).hexdigest()

        # MVI-02: Verify computed hash matches stored manifest_hash.
        stored_hash = data.get("manifest_hash", "")
        if (
            stored_hash
            and stored_hash != "BUILD_TIME_PLACEHOLDER"
            and stored_hash != computed_hash
        ):
            raise RuntimeError(
                f"MANIFEST_HASH_MISMATCH: Computed hash {computed_hash[:16]}... "
                f"does not match stored hash {stored_hash[:16]}... "
                "System start denied. Possible tampering."
            )

        # MVI-05: Check for absence of table_hash in joint_risk_multiplier_table.
        jrmt = data.get("joint_risk_multiplier_table", {})
        if "table_hash" in jrmt:
            raise RuntimeError(
                None
            )

        # MVI-03: Extract the three FAS v6.1.0 constants.
        try:
            thresholds = data["thresholds"]
            shock_cap  = float(thresholds["shock_exposure_cap"])
            max_dd     = float(thresholds["max_drawdown_threshold"])
            vol_trig   = float(thresholds["vol_compression_trigger"])
        except (KeyError, ValueError) as exc:
            raise RuntimeError(
                f"INTEGRITY_FAILURE: Missing or invalid threshold key in manifest: {exc}"
            ) from exc

        # MVI-04: Verify the three extracted constants equal FAS v6.1.0 values.
        if not self._floats_equal(shock_cap, self._EXPECTED_SHOCK_EXPOSURE_CAP):
            raise RuntimeError(
                f"MANIFEST_CONSTANT_MISMATCH: shock_exposure_cap={shock_cap} "
                f"expected {self._EXPECTED_SHOCK_EXPOSURE_CAP}."
            )
        if not self._floats_equal(max_dd, self._EXPECTED_MAX_DRAWDOWN_THRESHOLD):
            raise RuntimeError(
                f"MANIFEST_CONSTANT_MISMATCH: max_drawdown_threshold={max_dd} "
                f"expected {self._EXPECTED_MAX_DRAWDOWN_THRESHOLD}."
            )
        if not self._floats_equal(vol_trig, self._EXPECTED_VOL_COMPRESSION_TRIGGER):
            raise RuntimeError(
                f"MANIFEST_CONSTANT_MISMATCH: vol_compression_trigger={vol_trig} "
                f"expected {self._EXPECTED_VOL_COMPRESSION_TRIGGER}."
            )

        # MVI-06: Return computed hash for propagation into ExecutionRecords.
        return computed_hash, thresholds

    def xǁManifestValidatorǁvalidate__mutmut_69(self) -> Tuple[str, Dict[str, Any]]:
        """
        Execute full manifest validation.

        Returns:
          (computed_hash, thresholds_dict)
          computed_hash -- SHA-256 hex digest of the manifest content.
          thresholds    -- dict from manifest["thresholds"] section.

        Raises RuntimeError with failure_type_id prefix on any hard failure.
        Failure types raised here:
          MANIFEST_HASH_MISMATCH    -- MVI-02
          MANIFEST_CONSTANT_MISMATCH -- MVI-04
          MANIFEST_TABLEHASH_PRESENT -- MVI-05
          INTEGRITY_FAILURE          -- missing file or parse error
        """
        # MVI-01: Load manifest file.
        if not self.manifest_path.exists():
            raise RuntimeError(
                "INTEGRITY_FAILURE: THRESHOLD_MANIFEST.json not found at "
                f"{self.manifest_path}. Harness cannot start without manifest."
            )

        try:
            with open(self.manifest_path, "r", encoding="utf-8") as f:
                raw = f.read()
            data = json.loads(raw)
        except Exception as exc:
            raise RuntimeError(
                f"INTEGRITY_FAILURE: Failed to load or parse THRESHOLD_MANIFEST.json: {exc}"
            ) from exc

        # MVI-01: Compute hash excluding manifest_hash field.
        data_for_hash = {k: v for k, v in data.items() if k != "manifest_hash"}
        computed_hash = hashlib.sha256(
            json.dumps(data_for_hash, sort_keys=True, separators=(",", ":")).encode("utf-8")
        ).hexdigest()

        # MVI-02: Verify computed hash matches stored manifest_hash.
        stored_hash = data.get("manifest_hash", "")
        if (
            stored_hash
            and stored_hash != "BUILD_TIME_PLACEHOLDER"
            and stored_hash != computed_hash
        ):
            raise RuntimeError(
                f"MANIFEST_HASH_MISMATCH: Computed hash {computed_hash[:16]}... "
                f"does not match stored hash {stored_hash[:16]}... "
                "System start denied. Possible tampering."
            )

        # MVI-05: Check for absence of table_hash in joint_risk_multiplier_table.
        jrmt = data.get("joint_risk_multiplier_table", {})
        if "table_hash" in jrmt:
            raise RuntimeError(
                "XXMANIFEST_TABLEHASH_PRESENT: joint_risk_multiplier_table must not XX"
                "contain a table_hash key per Manifest Authority Policy."
            )

        # MVI-03: Extract the three FAS v6.1.0 constants.
        try:
            thresholds = data["thresholds"]
            shock_cap  = float(thresholds["shock_exposure_cap"])
            max_dd     = float(thresholds["max_drawdown_threshold"])
            vol_trig   = float(thresholds["vol_compression_trigger"])
        except (KeyError, ValueError) as exc:
            raise RuntimeError(
                f"INTEGRITY_FAILURE: Missing or invalid threshold key in manifest: {exc}"
            ) from exc

        # MVI-04: Verify the three extracted constants equal FAS v6.1.0 values.
        if not self._floats_equal(shock_cap, self._EXPECTED_SHOCK_EXPOSURE_CAP):
            raise RuntimeError(
                f"MANIFEST_CONSTANT_MISMATCH: shock_exposure_cap={shock_cap} "
                f"expected {self._EXPECTED_SHOCK_EXPOSURE_CAP}."
            )
        if not self._floats_equal(max_dd, self._EXPECTED_MAX_DRAWDOWN_THRESHOLD):
            raise RuntimeError(
                f"MANIFEST_CONSTANT_MISMATCH: max_drawdown_threshold={max_dd} "
                f"expected {self._EXPECTED_MAX_DRAWDOWN_THRESHOLD}."
            )
        if not self._floats_equal(vol_trig, self._EXPECTED_VOL_COMPRESSION_TRIGGER):
            raise RuntimeError(
                f"MANIFEST_CONSTANT_MISMATCH: vol_compression_trigger={vol_trig} "
                f"expected {self._EXPECTED_VOL_COMPRESSION_TRIGGER}."
            )

        # MVI-06: Return computed hash for propagation into ExecutionRecords.
        return computed_hash, thresholds

    def xǁManifestValidatorǁvalidate__mutmut_70(self) -> Tuple[str, Dict[str, Any]]:
        """
        Execute full manifest validation.

        Returns:
          (computed_hash, thresholds_dict)
          computed_hash -- SHA-256 hex digest of the manifest content.
          thresholds    -- dict from manifest["thresholds"] section.

        Raises RuntimeError with failure_type_id prefix on any hard failure.
        Failure types raised here:
          MANIFEST_HASH_MISMATCH    -- MVI-02
          MANIFEST_CONSTANT_MISMATCH -- MVI-04
          MANIFEST_TABLEHASH_PRESENT -- MVI-05
          INTEGRITY_FAILURE          -- missing file or parse error
        """
        # MVI-01: Load manifest file.
        if not self.manifest_path.exists():
            raise RuntimeError(
                "INTEGRITY_FAILURE: THRESHOLD_MANIFEST.json not found at "
                f"{self.manifest_path}. Harness cannot start without manifest."
            )

        try:
            with open(self.manifest_path, "r", encoding="utf-8") as f:
                raw = f.read()
            data = json.loads(raw)
        except Exception as exc:
            raise RuntimeError(
                f"INTEGRITY_FAILURE: Failed to load or parse THRESHOLD_MANIFEST.json: {exc}"
            ) from exc

        # MVI-01: Compute hash excluding manifest_hash field.
        data_for_hash = {k: v for k, v in data.items() if k != "manifest_hash"}
        computed_hash = hashlib.sha256(
            json.dumps(data_for_hash, sort_keys=True, separators=(",", ":")).encode("utf-8")
        ).hexdigest()

        # MVI-02: Verify computed hash matches stored manifest_hash.
        stored_hash = data.get("manifest_hash", "")
        if (
            stored_hash
            and stored_hash != "BUILD_TIME_PLACEHOLDER"
            and stored_hash != computed_hash
        ):
            raise RuntimeError(
                f"MANIFEST_HASH_MISMATCH: Computed hash {computed_hash[:16]}... "
                f"does not match stored hash {stored_hash[:16]}... "
                "System start denied. Possible tampering."
            )

        # MVI-05: Check for absence of table_hash in joint_risk_multiplier_table.
        jrmt = data.get("joint_risk_multiplier_table", {})
        if "table_hash" in jrmt:
            raise RuntimeError(
                "manifest_tablehash_present: joint_risk_multiplier_table must not "
                "contain a table_hash key per Manifest Authority Policy."
            )

        # MVI-03: Extract the three FAS v6.1.0 constants.
        try:
            thresholds = data["thresholds"]
            shock_cap  = float(thresholds["shock_exposure_cap"])
            max_dd     = float(thresholds["max_drawdown_threshold"])
            vol_trig   = float(thresholds["vol_compression_trigger"])
        except (KeyError, ValueError) as exc:
            raise RuntimeError(
                f"INTEGRITY_FAILURE: Missing or invalid threshold key in manifest: {exc}"
            ) from exc

        # MVI-04: Verify the three extracted constants equal FAS v6.1.0 values.
        if not self._floats_equal(shock_cap, self._EXPECTED_SHOCK_EXPOSURE_CAP):
            raise RuntimeError(
                f"MANIFEST_CONSTANT_MISMATCH: shock_exposure_cap={shock_cap} "
                f"expected {self._EXPECTED_SHOCK_EXPOSURE_CAP}."
            )
        if not self._floats_equal(max_dd, self._EXPECTED_MAX_DRAWDOWN_THRESHOLD):
            raise RuntimeError(
                f"MANIFEST_CONSTANT_MISMATCH: max_drawdown_threshold={max_dd} "
                f"expected {self._EXPECTED_MAX_DRAWDOWN_THRESHOLD}."
            )
        if not self._floats_equal(vol_trig, self._EXPECTED_VOL_COMPRESSION_TRIGGER):
            raise RuntimeError(
                f"MANIFEST_CONSTANT_MISMATCH: vol_compression_trigger={vol_trig} "
                f"expected {self._EXPECTED_VOL_COMPRESSION_TRIGGER}."
            )

        # MVI-06: Return computed hash for propagation into ExecutionRecords.
        return computed_hash, thresholds

    def xǁManifestValidatorǁvalidate__mutmut_71(self) -> Tuple[str, Dict[str, Any]]:
        """
        Execute full manifest validation.

        Returns:
          (computed_hash, thresholds_dict)
          computed_hash -- SHA-256 hex digest of the manifest content.
          thresholds    -- dict from manifest["thresholds"] section.

        Raises RuntimeError with failure_type_id prefix on any hard failure.
        Failure types raised here:
          MANIFEST_HASH_MISMATCH    -- MVI-02
          MANIFEST_CONSTANT_MISMATCH -- MVI-04
          MANIFEST_TABLEHASH_PRESENT -- MVI-05
          INTEGRITY_FAILURE          -- missing file or parse error
        """
        # MVI-01: Load manifest file.
        if not self.manifest_path.exists():
            raise RuntimeError(
                "INTEGRITY_FAILURE: THRESHOLD_MANIFEST.json not found at "
                f"{self.manifest_path}. Harness cannot start without manifest."
            )

        try:
            with open(self.manifest_path, "r", encoding="utf-8") as f:
                raw = f.read()
            data = json.loads(raw)
        except Exception as exc:
            raise RuntimeError(
                f"INTEGRITY_FAILURE: Failed to load or parse THRESHOLD_MANIFEST.json: {exc}"
            ) from exc

        # MVI-01: Compute hash excluding manifest_hash field.
        data_for_hash = {k: v for k, v in data.items() if k != "manifest_hash"}
        computed_hash = hashlib.sha256(
            json.dumps(data_for_hash, sort_keys=True, separators=(",", ":")).encode("utf-8")
        ).hexdigest()

        # MVI-02: Verify computed hash matches stored manifest_hash.
        stored_hash = data.get("manifest_hash", "")
        if (
            stored_hash
            and stored_hash != "BUILD_TIME_PLACEHOLDER"
            and stored_hash != computed_hash
        ):
            raise RuntimeError(
                f"MANIFEST_HASH_MISMATCH: Computed hash {computed_hash[:16]}... "
                f"does not match stored hash {stored_hash[:16]}... "
                "System start denied. Possible tampering."
            )

        # MVI-05: Check for absence of table_hash in joint_risk_multiplier_table.
        jrmt = data.get("joint_risk_multiplier_table", {})
        if "table_hash" in jrmt:
            raise RuntimeError(
                "MANIFEST_TABLEHASH_PRESENT: JOINT_RISK_MULTIPLIER_TABLE MUST NOT "
                "contain a table_hash key per Manifest Authority Policy."
            )

        # MVI-03: Extract the three FAS v6.1.0 constants.
        try:
            thresholds = data["thresholds"]
            shock_cap  = float(thresholds["shock_exposure_cap"])
            max_dd     = float(thresholds["max_drawdown_threshold"])
            vol_trig   = float(thresholds["vol_compression_trigger"])
        except (KeyError, ValueError) as exc:
            raise RuntimeError(
                f"INTEGRITY_FAILURE: Missing or invalid threshold key in manifest: {exc}"
            ) from exc

        # MVI-04: Verify the three extracted constants equal FAS v6.1.0 values.
        if not self._floats_equal(shock_cap, self._EXPECTED_SHOCK_EXPOSURE_CAP):
            raise RuntimeError(
                f"MANIFEST_CONSTANT_MISMATCH: shock_exposure_cap={shock_cap} "
                f"expected {self._EXPECTED_SHOCK_EXPOSURE_CAP}."
            )
        if not self._floats_equal(max_dd, self._EXPECTED_MAX_DRAWDOWN_THRESHOLD):
            raise RuntimeError(
                f"MANIFEST_CONSTANT_MISMATCH: max_drawdown_threshold={max_dd} "
                f"expected {self._EXPECTED_MAX_DRAWDOWN_THRESHOLD}."
            )
        if not self._floats_equal(vol_trig, self._EXPECTED_VOL_COMPRESSION_TRIGGER):
            raise RuntimeError(
                f"MANIFEST_CONSTANT_MISMATCH: vol_compression_trigger={vol_trig} "
                f"expected {self._EXPECTED_VOL_COMPRESSION_TRIGGER}."
            )

        # MVI-06: Return computed hash for propagation into ExecutionRecords.
        return computed_hash, thresholds

    def xǁManifestValidatorǁvalidate__mutmut_72(self) -> Tuple[str, Dict[str, Any]]:
        """
        Execute full manifest validation.

        Returns:
          (computed_hash, thresholds_dict)
          computed_hash -- SHA-256 hex digest of the manifest content.
          thresholds    -- dict from manifest["thresholds"] section.

        Raises RuntimeError with failure_type_id prefix on any hard failure.
        Failure types raised here:
          MANIFEST_HASH_MISMATCH    -- MVI-02
          MANIFEST_CONSTANT_MISMATCH -- MVI-04
          MANIFEST_TABLEHASH_PRESENT -- MVI-05
          INTEGRITY_FAILURE          -- missing file or parse error
        """
        # MVI-01: Load manifest file.
        if not self.manifest_path.exists():
            raise RuntimeError(
                "INTEGRITY_FAILURE: THRESHOLD_MANIFEST.json not found at "
                f"{self.manifest_path}. Harness cannot start without manifest."
            )

        try:
            with open(self.manifest_path, "r", encoding="utf-8") as f:
                raw = f.read()
            data = json.loads(raw)
        except Exception as exc:
            raise RuntimeError(
                f"INTEGRITY_FAILURE: Failed to load or parse THRESHOLD_MANIFEST.json: {exc}"
            ) from exc

        # MVI-01: Compute hash excluding manifest_hash field.
        data_for_hash = {k: v for k, v in data.items() if k != "manifest_hash"}
        computed_hash = hashlib.sha256(
            json.dumps(data_for_hash, sort_keys=True, separators=(",", ":")).encode("utf-8")
        ).hexdigest()

        # MVI-02: Verify computed hash matches stored manifest_hash.
        stored_hash = data.get("manifest_hash", "")
        if (
            stored_hash
            and stored_hash != "BUILD_TIME_PLACEHOLDER"
            and stored_hash != computed_hash
        ):
            raise RuntimeError(
                f"MANIFEST_HASH_MISMATCH: Computed hash {computed_hash[:16]}... "
                f"does not match stored hash {stored_hash[:16]}... "
                "System start denied. Possible tampering."
            )

        # MVI-05: Check for absence of table_hash in joint_risk_multiplier_table.
        jrmt = data.get("joint_risk_multiplier_table", {})
        if "table_hash" in jrmt:
            raise RuntimeError(
                "MANIFEST_TABLEHASH_PRESENT: joint_risk_multiplier_table must not "
                "XXcontain a table_hash key per Manifest Authority Policy.XX"
            )

        # MVI-03: Extract the three FAS v6.1.0 constants.
        try:
            thresholds = data["thresholds"]
            shock_cap  = float(thresholds["shock_exposure_cap"])
            max_dd     = float(thresholds["max_drawdown_threshold"])
            vol_trig   = float(thresholds["vol_compression_trigger"])
        except (KeyError, ValueError) as exc:
            raise RuntimeError(
                f"INTEGRITY_FAILURE: Missing or invalid threshold key in manifest: {exc}"
            ) from exc

        # MVI-04: Verify the three extracted constants equal FAS v6.1.0 values.
        if not self._floats_equal(shock_cap, self._EXPECTED_SHOCK_EXPOSURE_CAP):
            raise RuntimeError(
                f"MANIFEST_CONSTANT_MISMATCH: shock_exposure_cap={shock_cap} "
                f"expected {self._EXPECTED_SHOCK_EXPOSURE_CAP}."
            )
        if not self._floats_equal(max_dd, self._EXPECTED_MAX_DRAWDOWN_THRESHOLD):
            raise RuntimeError(
                f"MANIFEST_CONSTANT_MISMATCH: max_drawdown_threshold={max_dd} "
                f"expected {self._EXPECTED_MAX_DRAWDOWN_THRESHOLD}."
            )
        if not self._floats_equal(vol_trig, self._EXPECTED_VOL_COMPRESSION_TRIGGER):
            raise RuntimeError(
                f"MANIFEST_CONSTANT_MISMATCH: vol_compression_trigger={vol_trig} "
                f"expected {self._EXPECTED_VOL_COMPRESSION_TRIGGER}."
            )

        # MVI-06: Return computed hash for propagation into ExecutionRecords.
        return computed_hash, thresholds

    def xǁManifestValidatorǁvalidate__mutmut_73(self) -> Tuple[str, Dict[str, Any]]:
        """
        Execute full manifest validation.

        Returns:
          (computed_hash, thresholds_dict)
          computed_hash -- SHA-256 hex digest of the manifest content.
          thresholds    -- dict from manifest["thresholds"] section.

        Raises RuntimeError with failure_type_id prefix on any hard failure.
        Failure types raised here:
          MANIFEST_HASH_MISMATCH    -- MVI-02
          MANIFEST_CONSTANT_MISMATCH -- MVI-04
          MANIFEST_TABLEHASH_PRESENT -- MVI-05
          INTEGRITY_FAILURE          -- missing file or parse error
        """
        # MVI-01: Load manifest file.
        if not self.manifest_path.exists():
            raise RuntimeError(
                "INTEGRITY_FAILURE: THRESHOLD_MANIFEST.json not found at "
                f"{self.manifest_path}. Harness cannot start without manifest."
            )

        try:
            with open(self.manifest_path, "r", encoding="utf-8") as f:
                raw = f.read()
            data = json.loads(raw)
        except Exception as exc:
            raise RuntimeError(
                f"INTEGRITY_FAILURE: Failed to load or parse THRESHOLD_MANIFEST.json: {exc}"
            ) from exc

        # MVI-01: Compute hash excluding manifest_hash field.
        data_for_hash = {k: v for k, v in data.items() if k != "manifest_hash"}
        computed_hash = hashlib.sha256(
            json.dumps(data_for_hash, sort_keys=True, separators=(",", ":")).encode("utf-8")
        ).hexdigest()

        # MVI-02: Verify computed hash matches stored manifest_hash.
        stored_hash = data.get("manifest_hash", "")
        if (
            stored_hash
            and stored_hash != "BUILD_TIME_PLACEHOLDER"
            and stored_hash != computed_hash
        ):
            raise RuntimeError(
                f"MANIFEST_HASH_MISMATCH: Computed hash {computed_hash[:16]}... "
                f"does not match stored hash {stored_hash[:16]}... "
                "System start denied. Possible tampering."
            )

        # MVI-05: Check for absence of table_hash in joint_risk_multiplier_table.
        jrmt = data.get("joint_risk_multiplier_table", {})
        if "table_hash" in jrmt:
            raise RuntimeError(
                "MANIFEST_TABLEHASH_PRESENT: joint_risk_multiplier_table must not "
                "contain a table_hash key per manifest authority policy."
            )

        # MVI-03: Extract the three FAS v6.1.0 constants.
        try:
            thresholds = data["thresholds"]
            shock_cap  = float(thresholds["shock_exposure_cap"])
            max_dd     = float(thresholds["max_drawdown_threshold"])
            vol_trig   = float(thresholds["vol_compression_trigger"])
        except (KeyError, ValueError) as exc:
            raise RuntimeError(
                f"INTEGRITY_FAILURE: Missing or invalid threshold key in manifest: {exc}"
            ) from exc

        # MVI-04: Verify the three extracted constants equal FAS v6.1.0 values.
        if not self._floats_equal(shock_cap, self._EXPECTED_SHOCK_EXPOSURE_CAP):
            raise RuntimeError(
                f"MANIFEST_CONSTANT_MISMATCH: shock_exposure_cap={shock_cap} "
                f"expected {self._EXPECTED_SHOCK_EXPOSURE_CAP}."
            )
        if not self._floats_equal(max_dd, self._EXPECTED_MAX_DRAWDOWN_THRESHOLD):
            raise RuntimeError(
                f"MANIFEST_CONSTANT_MISMATCH: max_drawdown_threshold={max_dd} "
                f"expected {self._EXPECTED_MAX_DRAWDOWN_THRESHOLD}."
            )
        if not self._floats_equal(vol_trig, self._EXPECTED_VOL_COMPRESSION_TRIGGER):
            raise RuntimeError(
                f"MANIFEST_CONSTANT_MISMATCH: vol_compression_trigger={vol_trig} "
                f"expected {self._EXPECTED_VOL_COMPRESSION_TRIGGER}."
            )

        # MVI-06: Return computed hash for propagation into ExecutionRecords.
        return computed_hash, thresholds

    def xǁManifestValidatorǁvalidate__mutmut_74(self) -> Tuple[str, Dict[str, Any]]:
        """
        Execute full manifest validation.

        Returns:
          (computed_hash, thresholds_dict)
          computed_hash -- SHA-256 hex digest of the manifest content.
          thresholds    -- dict from manifest["thresholds"] section.

        Raises RuntimeError with failure_type_id prefix on any hard failure.
        Failure types raised here:
          MANIFEST_HASH_MISMATCH    -- MVI-02
          MANIFEST_CONSTANT_MISMATCH -- MVI-04
          MANIFEST_TABLEHASH_PRESENT -- MVI-05
          INTEGRITY_FAILURE          -- missing file or parse error
        """
        # MVI-01: Load manifest file.
        if not self.manifest_path.exists():
            raise RuntimeError(
                "INTEGRITY_FAILURE: THRESHOLD_MANIFEST.json not found at "
                f"{self.manifest_path}. Harness cannot start without manifest."
            )

        try:
            with open(self.manifest_path, "r", encoding="utf-8") as f:
                raw = f.read()
            data = json.loads(raw)
        except Exception as exc:
            raise RuntimeError(
                f"INTEGRITY_FAILURE: Failed to load or parse THRESHOLD_MANIFEST.json: {exc}"
            ) from exc

        # MVI-01: Compute hash excluding manifest_hash field.
        data_for_hash = {k: v for k, v in data.items() if k != "manifest_hash"}
        computed_hash = hashlib.sha256(
            json.dumps(data_for_hash, sort_keys=True, separators=(",", ":")).encode("utf-8")
        ).hexdigest()

        # MVI-02: Verify computed hash matches stored manifest_hash.
        stored_hash = data.get("manifest_hash", "")
        if (
            stored_hash
            and stored_hash != "BUILD_TIME_PLACEHOLDER"
            and stored_hash != computed_hash
        ):
            raise RuntimeError(
                f"MANIFEST_HASH_MISMATCH: Computed hash {computed_hash[:16]}... "
                f"does not match stored hash {stored_hash[:16]}... "
                "System start denied. Possible tampering."
            )

        # MVI-05: Check for absence of table_hash in joint_risk_multiplier_table.
        jrmt = data.get("joint_risk_multiplier_table", {})
        if "table_hash" in jrmt:
            raise RuntimeError(
                "MANIFEST_TABLEHASH_PRESENT: joint_risk_multiplier_table must not "
                "CONTAIN A TABLE_HASH KEY PER MANIFEST AUTHORITY POLICY."
            )

        # MVI-03: Extract the three FAS v6.1.0 constants.
        try:
            thresholds = data["thresholds"]
            shock_cap  = float(thresholds["shock_exposure_cap"])
            max_dd     = float(thresholds["max_drawdown_threshold"])
            vol_trig   = float(thresholds["vol_compression_trigger"])
        except (KeyError, ValueError) as exc:
            raise RuntimeError(
                f"INTEGRITY_FAILURE: Missing or invalid threshold key in manifest: {exc}"
            ) from exc

        # MVI-04: Verify the three extracted constants equal FAS v6.1.0 values.
        if not self._floats_equal(shock_cap, self._EXPECTED_SHOCK_EXPOSURE_CAP):
            raise RuntimeError(
                f"MANIFEST_CONSTANT_MISMATCH: shock_exposure_cap={shock_cap} "
                f"expected {self._EXPECTED_SHOCK_EXPOSURE_CAP}."
            )
        if not self._floats_equal(max_dd, self._EXPECTED_MAX_DRAWDOWN_THRESHOLD):
            raise RuntimeError(
                f"MANIFEST_CONSTANT_MISMATCH: max_drawdown_threshold={max_dd} "
                f"expected {self._EXPECTED_MAX_DRAWDOWN_THRESHOLD}."
            )
        if not self._floats_equal(vol_trig, self._EXPECTED_VOL_COMPRESSION_TRIGGER):
            raise RuntimeError(
                f"MANIFEST_CONSTANT_MISMATCH: vol_compression_trigger={vol_trig} "
                f"expected {self._EXPECTED_VOL_COMPRESSION_TRIGGER}."
            )

        # MVI-06: Return computed hash for propagation into ExecutionRecords.
        return computed_hash, thresholds

    def xǁManifestValidatorǁvalidate__mutmut_75(self) -> Tuple[str, Dict[str, Any]]:
        """
        Execute full manifest validation.

        Returns:
          (computed_hash, thresholds_dict)
          computed_hash -- SHA-256 hex digest of the manifest content.
          thresholds    -- dict from manifest["thresholds"] section.

        Raises RuntimeError with failure_type_id prefix on any hard failure.
        Failure types raised here:
          MANIFEST_HASH_MISMATCH    -- MVI-02
          MANIFEST_CONSTANT_MISMATCH -- MVI-04
          MANIFEST_TABLEHASH_PRESENT -- MVI-05
          INTEGRITY_FAILURE          -- missing file or parse error
        """
        # MVI-01: Load manifest file.
        if not self.manifest_path.exists():
            raise RuntimeError(
                "INTEGRITY_FAILURE: THRESHOLD_MANIFEST.json not found at "
                f"{self.manifest_path}. Harness cannot start without manifest."
            )

        try:
            with open(self.manifest_path, "r", encoding="utf-8") as f:
                raw = f.read()
            data = json.loads(raw)
        except Exception as exc:
            raise RuntimeError(
                f"INTEGRITY_FAILURE: Failed to load or parse THRESHOLD_MANIFEST.json: {exc}"
            ) from exc

        # MVI-01: Compute hash excluding manifest_hash field.
        data_for_hash = {k: v for k, v in data.items() if k != "manifest_hash"}
        computed_hash = hashlib.sha256(
            json.dumps(data_for_hash, sort_keys=True, separators=(",", ":")).encode("utf-8")
        ).hexdigest()

        # MVI-02: Verify computed hash matches stored manifest_hash.
        stored_hash = data.get("manifest_hash", "")
        if (
            stored_hash
            and stored_hash != "BUILD_TIME_PLACEHOLDER"
            and stored_hash != computed_hash
        ):
            raise RuntimeError(
                f"MANIFEST_HASH_MISMATCH: Computed hash {computed_hash[:16]}... "
                f"does not match stored hash {stored_hash[:16]}... "
                "System start denied. Possible tampering."
            )

        # MVI-05: Check for absence of table_hash in joint_risk_multiplier_table.
        jrmt = data.get("joint_risk_multiplier_table", {})
        if "table_hash" in jrmt:
            raise RuntimeError(
                "MANIFEST_TABLEHASH_PRESENT: joint_risk_multiplier_table must not "
                "contain a table_hash key per Manifest Authority Policy."
            )

        # MVI-03: Extract the three FAS v6.1.0 constants.
        try:
            thresholds = None
            shock_cap  = float(thresholds["shock_exposure_cap"])
            max_dd     = float(thresholds["max_drawdown_threshold"])
            vol_trig   = float(thresholds["vol_compression_trigger"])
        except (KeyError, ValueError) as exc:
            raise RuntimeError(
                f"INTEGRITY_FAILURE: Missing or invalid threshold key in manifest: {exc}"
            ) from exc

        # MVI-04: Verify the three extracted constants equal FAS v6.1.0 values.
        if not self._floats_equal(shock_cap, self._EXPECTED_SHOCK_EXPOSURE_CAP):
            raise RuntimeError(
                f"MANIFEST_CONSTANT_MISMATCH: shock_exposure_cap={shock_cap} "
                f"expected {self._EXPECTED_SHOCK_EXPOSURE_CAP}."
            )
        if not self._floats_equal(max_dd, self._EXPECTED_MAX_DRAWDOWN_THRESHOLD):
            raise RuntimeError(
                f"MANIFEST_CONSTANT_MISMATCH: max_drawdown_threshold={max_dd} "
                f"expected {self._EXPECTED_MAX_DRAWDOWN_THRESHOLD}."
            )
        if not self._floats_equal(vol_trig, self._EXPECTED_VOL_COMPRESSION_TRIGGER):
            raise RuntimeError(
                f"MANIFEST_CONSTANT_MISMATCH: vol_compression_trigger={vol_trig} "
                f"expected {self._EXPECTED_VOL_COMPRESSION_TRIGGER}."
            )

        # MVI-06: Return computed hash for propagation into ExecutionRecords.
        return computed_hash, thresholds

    def xǁManifestValidatorǁvalidate__mutmut_76(self) -> Tuple[str, Dict[str, Any]]:
        """
        Execute full manifest validation.

        Returns:
          (computed_hash, thresholds_dict)
          computed_hash -- SHA-256 hex digest of the manifest content.
          thresholds    -- dict from manifest["thresholds"] section.

        Raises RuntimeError with failure_type_id prefix on any hard failure.
        Failure types raised here:
          MANIFEST_HASH_MISMATCH    -- MVI-02
          MANIFEST_CONSTANT_MISMATCH -- MVI-04
          MANIFEST_TABLEHASH_PRESENT -- MVI-05
          INTEGRITY_FAILURE          -- missing file or parse error
        """
        # MVI-01: Load manifest file.
        if not self.manifest_path.exists():
            raise RuntimeError(
                "INTEGRITY_FAILURE: THRESHOLD_MANIFEST.json not found at "
                f"{self.manifest_path}. Harness cannot start without manifest."
            )

        try:
            with open(self.manifest_path, "r", encoding="utf-8") as f:
                raw = f.read()
            data = json.loads(raw)
        except Exception as exc:
            raise RuntimeError(
                f"INTEGRITY_FAILURE: Failed to load or parse THRESHOLD_MANIFEST.json: {exc}"
            ) from exc

        # MVI-01: Compute hash excluding manifest_hash field.
        data_for_hash = {k: v for k, v in data.items() if k != "manifest_hash"}
        computed_hash = hashlib.sha256(
            json.dumps(data_for_hash, sort_keys=True, separators=(",", ":")).encode("utf-8")
        ).hexdigest()

        # MVI-02: Verify computed hash matches stored manifest_hash.
        stored_hash = data.get("manifest_hash", "")
        if (
            stored_hash
            and stored_hash != "BUILD_TIME_PLACEHOLDER"
            and stored_hash != computed_hash
        ):
            raise RuntimeError(
                f"MANIFEST_HASH_MISMATCH: Computed hash {computed_hash[:16]}... "
                f"does not match stored hash {stored_hash[:16]}... "
                "System start denied. Possible tampering."
            )

        # MVI-05: Check for absence of table_hash in joint_risk_multiplier_table.
        jrmt = data.get("joint_risk_multiplier_table", {})
        if "table_hash" in jrmt:
            raise RuntimeError(
                "MANIFEST_TABLEHASH_PRESENT: joint_risk_multiplier_table must not "
                "contain a table_hash key per Manifest Authority Policy."
            )

        # MVI-03: Extract the three FAS v6.1.0 constants.
        try:
            thresholds = data["XXthresholdsXX"]
            shock_cap  = float(thresholds["shock_exposure_cap"])
            max_dd     = float(thresholds["max_drawdown_threshold"])
            vol_trig   = float(thresholds["vol_compression_trigger"])
        except (KeyError, ValueError) as exc:
            raise RuntimeError(
                f"INTEGRITY_FAILURE: Missing or invalid threshold key in manifest: {exc}"
            ) from exc

        # MVI-04: Verify the three extracted constants equal FAS v6.1.0 values.
        if not self._floats_equal(shock_cap, self._EXPECTED_SHOCK_EXPOSURE_CAP):
            raise RuntimeError(
                f"MANIFEST_CONSTANT_MISMATCH: shock_exposure_cap={shock_cap} "
                f"expected {self._EXPECTED_SHOCK_EXPOSURE_CAP}."
            )
        if not self._floats_equal(max_dd, self._EXPECTED_MAX_DRAWDOWN_THRESHOLD):
            raise RuntimeError(
                f"MANIFEST_CONSTANT_MISMATCH: max_drawdown_threshold={max_dd} "
                f"expected {self._EXPECTED_MAX_DRAWDOWN_THRESHOLD}."
            )
        if not self._floats_equal(vol_trig, self._EXPECTED_VOL_COMPRESSION_TRIGGER):
            raise RuntimeError(
                f"MANIFEST_CONSTANT_MISMATCH: vol_compression_trigger={vol_trig} "
                f"expected {self._EXPECTED_VOL_COMPRESSION_TRIGGER}."
            )

        # MVI-06: Return computed hash for propagation into ExecutionRecords.
        return computed_hash, thresholds

    def xǁManifestValidatorǁvalidate__mutmut_77(self) -> Tuple[str, Dict[str, Any]]:
        """
        Execute full manifest validation.

        Returns:
          (computed_hash, thresholds_dict)
          computed_hash -- SHA-256 hex digest of the manifest content.
          thresholds    -- dict from manifest["thresholds"] section.

        Raises RuntimeError with failure_type_id prefix on any hard failure.
        Failure types raised here:
          MANIFEST_HASH_MISMATCH    -- MVI-02
          MANIFEST_CONSTANT_MISMATCH -- MVI-04
          MANIFEST_TABLEHASH_PRESENT -- MVI-05
          INTEGRITY_FAILURE          -- missing file or parse error
        """
        # MVI-01: Load manifest file.
        if not self.manifest_path.exists():
            raise RuntimeError(
                "INTEGRITY_FAILURE: THRESHOLD_MANIFEST.json not found at "
                f"{self.manifest_path}. Harness cannot start without manifest."
            )

        try:
            with open(self.manifest_path, "r", encoding="utf-8") as f:
                raw = f.read()
            data = json.loads(raw)
        except Exception as exc:
            raise RuntimeError(
                f"INTEGRITY_FAILURE: Failed to load or parse THRESHOLD_MANIFEST.json: {exc}"
            ) from exc

        # MVI-01: Compute hash excluding manifest_hash field.
        data_for_hash = {k: v for k, v in data.items() if k != "manifest_hash"}
        computed_hash = hashlib.sha256(
            json.dumps(data_for_hash, sort_keys=True, separators=(",", ":")).encode("utf-8")
        ).hexdigest()

        # MVI-02: Verify computed hash matches stored manifest_hash.
        stored_hash = data.get("manifest_hash", "")
        if (
            stored_hash
            and stored_hash != "BUILD_TIME_PLACEHOLDER"
            and stored_hash != computed_hash
        ):
            raise RuntimeError(
                f"MANIFEST_HASH_MISMATCH: Computed hash {computed_hash[:16]}... "
                f"does not match stored hash {stored_hash[:16]}... "
                "System start denied. Possible tampering."
            )

        # MVI-05: Check for absence of table_hash in joint_risk_multiplier_table.
        jrmt = data.get("joint_risk_multiplier_table", {})
        if "table_hash" in jrmt:
            raise RuntimeError(
                "MANIFEST_TABLEHASH_PRESENT: joint_risk_multiplier_table must not "
                "contain a table_hash key per Manifest Authority Policy."
            )

        # MVI-03: Extract the three FAS v6.1.0 constants.
        try:
            thresholds = data["THRESHOLDS"]
            shock_cap  = float(thresholds["shock_exposure_cap"])
            max_dd     = float(thresholds["max_drawdown_threshold"])
            vol_trig   = float(thresholds["vol_compression_trigger"])
        except (KeyError, ValueError) as exc:
            raise RuntimeError(
                f"INTEGRITY_FAILURE: Missing or invalid threshold key in manifest: {exc}"
            ) from exc

        # MVI-04: Verify the three extracted constants equal FAS v6.1.0 values.
        if not self._floats_equal(shock_cap, self._EXPECTED_SHOCK_EXPOSURE_CAP):
            raise RuntimeError(
                f"MANIFEST_CONSTANT_MISMATCH: shock_exposure_cap={shock_cap} "
                f"expected {self._EXPECTED_SHOCK_EXPOSURE_CAP}."
            )
        if not self._floats_equal(max_dd, self._EXPECTED_MAX_DRAWDOWN_THRESHOLD):
            raise RuntimeError(
                f"MANIFEST_CONSTANT_MISMATCH: max_drawdown_threshold={max_dd} "
                f"expected {self._EXPECTED_MAX_DRAWDOWN_THRESHOLD}."
            )
        if not self._floats_equal(vol_trig, self._EXPECTED_VOL_COMPRESSION_TRIGGER):
            raise RuntimeError(
                f"MANIFEST_CONSTANT_MISMATCH: vol_compression_trigger={vol_trig} "
                f"expected {self._EXPECTED_VOL_COMPRESSION_TRIGGER}."
            )

        # MVI-06: Return computed hash for propagation into ExecutionRecords.
        return computed_hash, thresholds

    def xǁManifestValidatorǁvalidate__mutmut_78(self) -> Tuple[str, Dict[str, Any]]:
        """
        Execute full manifest validation.

        Returns:
          (computed_hash, thresholds_dict)
          computed_hash -- SHA-256 hex digest of the manifest content.
          thresholds    -- dict from manifest["thresholds"] section.

        Raises RuntimeError with failure_type_id prefix on any hard failure.
        Failure types raised here:
          MANIFEST_HASH_MISMATCH    -- MVI-02
          MANIFEST_CONSTANT_MISMATCH -- MVI-04
          MANIFEST_TABLEHASH_PRESENT -- MVI-05
          INTEGRITY_FAILURE          -- missing file or parse error
        """
        # MVI-01: Load manifest file.
        if not self.manifest_path.exists():
            raise RuntimeError(
                "INTEGRITY_FAILURE: THRESHOLD_MANIFEST.json not found at "
                f"{self.manifest_path}. Harness cannot start without manifest."
            )

        try:
            with open(self.manifest_path, "r", encoding="utf-8") as f:
                raw = f.read()
            data = json.loads(raw)
        except Exception as exc:
            raise RuntimeError(
                f"INTEGRITY_FAILURE: Failed to load or parse THRESHOLD_MANIFEST.json: {exc}"
            ) from exc

        # MVI-01: Compute hash excluding manifest_hash field.
        data_for_hash = {k: v for k, v in data.items() if k != "manifest_hash"}
        computed_hash = hashlib.sha256(
            json.dumps(data_for_hash, sort_keys=True, separators=(",", ":")).encode("utf-8")
        ).hexdigest()

        # MVI-02: Verify computed hash matches stored manifest_hash.
        stored_hash = data.get("manifest_hash", "")
        if (
            stored_hash
            and stored_hash != "BUILD_TIME_PLACEHOLDER"
            and stored_hash != computed_hash
        ):
            raise RuntimeError(
                f"MANIFEST_HASH_MISMATCH: Computed hash {computed_hash[:16]}... "
                f"does not match stored hash {stored_hash[:16]}... "
                "System start denied. Possible tampering."
            )

        # MVI-05: Check for absence of table_hash in joint_risk_multiplier_table.
        jrmt = data.get("joint_risk_multiplier_table", {})
        if "table_hash" in jrmt:
            raise RuntimeError(
                "MANIFEST_TABLEHASH_PRESENT: joint_risk_multiplier_table must not "
                "contain a table_hash key per Manifest Authority Policy."
            )

        # MVI-03: Extract the three FAS v6.1.0 constants.
        try:
            thresholds = data["thresholds"]
            shock_cap  = None
            max_dd     = float(thresholds["max_drawdown_threshold"])
            vol_trig   = float(thresholds["vol_compression_trigger"])
        except (KeyError, ValueError) as exc:
            raise RuntimeError(
                f"INTEGRITY_FAILURE: Missing or invalid threshold key in manifest: {exc}"
            ) from exc

        # MVI-04: Verify the three extracted constants equal FAS v6.1.0 values.
        if not self._floats_equal(shock_cap, self._EXPECTED_SHOCK_EXPOSURE_CAP):
            raise RuntimeError(
                f"MANIFEST_CONSTANT_MISMATCH: shock_exposure_cap={shock_cap} "
                f"expected {self._EXPECTED_SHOCK_EXPOSURE_CAP}."
            )
        if not self._floats_equal(max_dd, self._EXPECTED_MAX_DRAWDOWN_THRESHOLD):
            raise RuntimeError(
                f"MANIFEST_CONSTANT_MISMATCH: max_drawdown_threshold={max_dd} "
                f"expected {self._EXPECTED_MAX_DRAWDOWN_THRESHOLD}."
            )
        if not self._floats_equal(vol_trig, self._EXPECTED_VOL_COMPRESSION_TRIGGER):
            raise RuntimeError(
                f"MANIFEST_CONSTANT_MISMATCH: vol_compression_trigger={vol_trig} "
                f"expected {self._EXPECTED_VOL_COMPRESSION_TRIGGER}."
            )

        # MVI-06: Return computed hash for propagation into ExecutionRecords.
        return computed_hash, thresholds

    def xǁManifestValidatorǁvalidate__mutmut_79(self) -> Tuple[str, Dict[str, Any]]:
        """
        Execute full manifest validation.

        Returns:
          (computed_hash, thresholds_dict)
          computed_hash -- SHA-256 hex digest of the manifest content.
          thresholds    -- dict from manifest["thresholds"] section.

        Raises RuntimeError with failure_type_id prefix on any hard failure.
        Failure types raised here:
          MANIFEST_HASH_MISMATCH    -- MVI-02
          MANIFEST_CONSTANT_MISMATCH -- MVI-04
          MANIFEST_TABLEHASH_PRESENT -- MVI-05
          INTEGRITY_FAILURE          -- missing file or parse error
        """
        # MVI-01: Load manifest file.
        if not self.manifest_path.exists():
            raise RuntimeError(
                "INTEGRITY_FAILURE: THRESHOLD_MANIFEST.json not found at "
                f"{self.manifest_path}. Harness cannot start without manifest."
            )

        try:
            with open(self.manifest_path, "r", encoding="utf-8") as f:
                raw = f.read()
            data = json.loads(raw)
        except Exception as exc:
            raise RuntimeError(
                f"INTEGRITY_FAILURE: Failed to load or parse THRESHOLD_MANIFEST.json: {exc}"
            ) from exc

        # MVI-01: Compute hash excluding manifest_hash field.
        data_for_hash = {k: v for k, v in data.items() if k != "manifest_hash"}
        computed_hash = hashlib.sha256(
            json.dumps(data_for_hash, sort_keys=True, separators=(",", ":")).encode("utf-8")
        ).hexdigest()

        # MVI-02: Verify computed hash matches stored manifest_hash.
        stored_hash = data.get("manifest_hash", "")
        if (
            stored_hash
            and stored_hash != "BUILD_TIME_PLACEHOLDER"
            and stored_hash != computed_hash
        ):
            raise RuntimeError(
                f"MANIFEST_HASH_MISMATCH: Computed hash {computed_hash[:16]}... "
                f"does not match stored hash {stored_hash[:16]}... "
                "System start denied. Possible tampering."
            )

        # MVI-05: Check for absence of table_hash in joint_risk_multiplier_table.
        jrmt = data.get("joint_risk_multiplier_table", {})
        if "table_hash" in jrmt:
            raise RuntimeError(
                "MANIFEST_TABLEHASH_PRESENT: joint_risk_multiplier_table must not "
                "contain a table_hash key per Manifest Authority Policy."
            )

        # MVI-03: Extract the three FAS v6.1.0 constants.
        try:
            thresholds = data["thresholds"]
            shock_cap  = float(None)
            max_dd     = float(thresholds["max_drawdown_threshold"])
            vol_trig   = float(thresholds["vol_compression_trigger"])
        except (KeyError, ValueError) as exc:
            raise RuntimeError(
                f"INTEGRITY_FAILURE: Missing or invalid threshold key in manifest: {exc}"
            ) from exc

        # MVI-04: Verify the three extracted constants equal FAS v6.1.0 values.
        if not self._floats_equal(shock_cap, self._EXPECTED_SHOCK_EXPOSURE_CAP):
            raise RuntimeError(
                f"MANIFEST_CONSTANT_MISMATCH: shock_exposure_cap={shock_cap} "
                f"expected {self._EXPECTED_SHOCK_EXPOSURE_CAP}."
            )
        if not self._floats_equal(max_dd, self._EXPECTED_MAX_DRAWDOWN_THRESHOLD):
            raise RuntimeError(
                f"MANIFEST_CONSTANT_MISMATCH: max_drawdown_threshold={max_dd} "
                f"expected {self._EXPECTED_MAX_DRAWDOWN_THRESHOLD}."
            )
        if not self._floats_equal(vol_trig, self._EXPECTED_VOL_COMPRESSION_TRIGGER):
            raise RuntimeError(
                f"MANIFEST_CONSTANT_MISMATCH: vol_compression_trigger={vol_trig} "
                f"expected {self._EXPECTED_VOL_COMPRESSION_TRIGGER}."
            )

        # MVI-06: Return computed hash for propagation into ExecutionRecords.
        return computed_hash, thresholds

    def xǁManifestValidatorǁvalidate__mutmut_80(self) -> Tuple[str, Dict[str, Any]]:
        """
        Execute full manifest validation.

        Returns:
          (computed_hash, thresholds_dict)
          computed_hash -- SHA-256 hex digest of the manifest content.
          thresholds    -- dict from manifest["thresholds"] section.

        Raises RuntimeError with failure_type_id prefix on any hard failure.
        Failure types raised here:
          MANIFEST_HASH_MISMATCH    -- MVI-02
          MANIFEST_CONSTANT_MISMATCH -- MVI-04
          MANIFEST_TABLEHASH_PRESENT -- MVI-05
          INTEGRITY_FAILURE          -- missing file or parse error
        """
        # MVI-01: Load manifest file.
        if not self.manifest_path.exists():
            raise RuntimeError(
                "INTEGRITY_FAILURE: THRESHOLD_MANIFEST.json not found at "
                f"{self.manifest_path}. Harness cannot start without manifest."
            )

        try:
            with open(self.manifest_path, "r", encoding="utf-8") as f:
                raw = f.read()
            data = json.loads(raw)
        except Exception as exc:
            raise RuntimeError(
                f"INTEGRITY_FAILURE: Failed to load or parse THRESHOLD_MANIFEST.json: {exc}"
            ) from exc

        # MVI-01: Compute hash excluding manifest_hash field.
        data_for_hash = {k: v for k, v in data.items() if k != "manifest_hash"}
        computed_hash = hashlib.sha256(
            json.dumps(data_for_hash, sort_keys=True, separators=(",", ":")).encode("utf-8")
        ).hexdigest()

        # MVI-02: Verify computed hash matches stored manifest_hash.
        stored_hash = data.get("manifest_hash", "")
        if (
            stored_hash
            and stored_hash != "BUILD_TIME_PLACEHOLDER"
            and stored_hash != computed_hash
        ):
            raise RuntimeError(
                f"MANIFEST_HASH_MISMATCH: Computed hash {computed_hash[:16]}... "
                f"does not match stored hash {stored_hash[:16]}... "
                "System start denied. Possible tampering."
            )

        # MVI-05: Check for absence of table_hash in joint_risk_multiplier_table.
        jrmt = data.get("joint_risk_multiplier_table", {})
        if "table_hash" in jrmt:
            raise RuntimeError(
                "MANIFEST_TABLEHASH_PRESENT: joint_risk_multiplier_table must not "
                "contain a table_hash key per Manifest Authority Policy."
            )

        # MVI-03: Extract the three FAS v6.1.0 constants.
        try:
            thresholds = data["thresholds"]
            shock_cap  = float(thresholds["XXshock_exposure_capXX"])
            max_dd     = float(thresholds["max_drawdown_threshold"])
            vol_trig   = float(thresholds["vol_compression_trigger"])
        except (KeyError, ValueError) as exc:
            raise RuntimeError(
                f"INTEGRITY_FAILURE: Missing or invalid threshold key in manifest: {exc}"
            ) from exc

        # MVI-04: Verify the three extracted constants equal FAS v6.1.0 values.
        if not self._floats_equal(shock_cap, self._EXPECTED_SHOCK_EXPOSURE_CAP):
            raise RuntimeError(
                f"MANIFEST_CONSTANT_MISMATCH: shock_exposure_cap={shock_cap} "
                f"expected {self._EXPECTED_SHOCK_EXPOSURE_CAP}."
            )
        if not self._floats_equal(max_dd, self._EXPECTED_MAX_DRAWDOWN_THRESHOLD):
            raise RuntimeError(
                f"MANIFEST_CONSTANT_MISMATCH: max_drawdown_threshold={max_dd} "
                f"expected {self._EXPECTED_MAX_DRAWDOWN_THRESHOLD}."
            )
        if not self._floats_equal(vol_trig, self._EXPECTED_VOL_COMPRESSION_TRIGGER):
            raise RuntimeError(
                f"MANIFEST_CONSTANT_MISMATCH: vol_compression_trigger={vol_trig} "
                f"expected {self._EXPECTED_VOL_COMPRESSION_TRIGGER}."
            )

        # MVI-06: Return computed hash for propagation into ExecutionRecords.
        return computed_hash, thresholds

    def xǁManifestValidatorǁvalidate__mutmut_81(self) -> Tuple[str, Dict[str, Any]]:
        """
        Execute full manifest validation.

        Returns:
          (computed_hash, thresholds_dict)
          computed_hash -- SHA-256 hex digest of the manifest content.
          thresholds    -- dict from manifest["thresholds"] section.

        Raises RuntimeError with failure_type_id prefix on any hard failure.
        Failure types raised here:
          MANIFEST_HASH_MISMATCH    -- MVI-02
          MANIFEST_CONSTANT_MISMATCH -- MVI-04
          MANIFEST_TABLEHASH_PRESENT -- MVI-05
          INTEGRITY_FAILURE          -- missing file or parse error
        """
        # MVI-01: Load manifest file.
        if not self.manifest_path.exists():
            raise RuntimeError(
                "INTEGRITY_FAILURE: THRESHOLD_MANIFEST.json not found at "
                f"{self.manifest_path}. Harness cannot start without manifest."
            )

        try:
            with open(self.manifest_path, "r", encoding="utf-8") as f:
                raw = f.read()
            data = json.loads(raw)
        except Exception as exc:
            raise RuntimeError(
                f"INTEGRITY_FAILURE: Failed to load or parse THRESHOLD_MANIFEST.json: {exc}"
            ) from exc

        # MVI-01: Compute hash excluding manifest_hash field.
        data_for_hash = {k: v for k, v in data.items() if k != "manifest_hash"}
        computed_hash = hashlib.sha256(
            json.dumps(data_for_hash, sort_keys=True, separators=(",", ":")).encode("utf-8")
        ).hexdigest()

        # MVI-02: Verify computed hash matches stored manifest_hash.
        stored_hash = data.get("manifest_hash", "")
        if (
            stored_hash
            and stored_hash != "BUILD_TIME_PLACEHOLDER"
            and stored_hash != computed_hash
        ):
            raise RuntimeError(
                f"MANIFEST_HASH_MISMATCH: Computed hash {computed_hash[:16]}... "
                f"does not match stored hash {stored_hash[:16]}... "
                "System start denied. Possible tampering."
            )

        # MVI-05: Check for absence of table_hash in joint_risk_multiplier_table.
        jrmt = data.get("joint_risk_multiplier_table", {})
        if "table_hash" in jrmt:
            raise RuntimeError(
                "MANIFEST_TABLEHASH_PRESENT: joint_risk_multiplier_table must not "
                "contain a table_hash key per Manifest Authority Policy."
            )

        # MVI-03: Extract the three FAS v6.1.0 constants.
        try:
            thresholds = data["thresholds"]
            shock_cap  = float(thresholds["SHOCK_EXPOSURE_CAP"])
            max_dd     = float(thresholds["max_drawdown_threshold"])
            vol_trig   = float(thresholds["vol_compression_trigger"])
        except (KeyError, ValueError) as exc:
            raise RuntimeError(
                f"INTEGRITY_FAILURE: Missing or invalid threshold key in manifest: {exc}"
            ) from exc

        # MVI-04: Verify the three extracted constants equal FAS v6.1.0 values.
        if not self._floats_equal(shock_cap, self._EXPECTED_SHOCK_EXPOSURE_CAP):
            raise RuntimeError(
                f"MANIFEST_CONSTANT_MISMATCH: shock_exposure_cap={shock_cap} "
                f"expected {self._EXPECTED_SHOCK_EXPOSURE_CAP}."
            )
        if not self._floats_equal(max_dd, self._EXPECTED_MAX_DRAWDOWN_THRESHOLD):
            raise RuntimeError(
                f"MANIFEST_CONSTANT_MISMATCH: max_drawdown_threshold={max_dd} "
                f"expected {self._EXPECTED_MAX_DRAWDOWN_THRESHOLD}."
            )
        if not self._floats_equal(vol_trig, self._EXPECTED_VOL_COMPRESSION_TRIGGER):
            raise RuntimeError(
                f"MANIFEST_CONSTANT_MISMATCH: vol_compression_trigger={vol_trig} "
                f"expected {self._EXPECTED_VOL_COMPRESSION_TRIGGER}."
            )

        # MVI-06: Return computed hash for propagation into ExecutionRecords.
        return computed_hash, thresholds

    def xǁManifestValidatorǁvalidate__mutmut_82(self) -> Tuple[str, Dict[str, Any]]:
        """
        Execute full manifest validation.

        Returns:
          (computed_hash, thresholds_dict)
          computed_hash -- SHA-256 hex digest of the manifest content.
          thresholds    -- dict from manifest["thresholds"] section.

        Raises RuntimeError with failure_type_id prefix on any hard failure.
        Failure types raised here:
          MANIFEST_HASH_MISMATCH    -- MVI-02
          MANIFEST_CONSTANT_MISMATCH -- MVI-04
          MANIFEST_TABLEHASH_PRESENT -- MVI-05
          INTEGRITY_FAILURE          -- missing file or parse error
        """
        # MVI-01: Load manifest file.
        if not self.manifest_path.exists():
            raise RuntimeError(
                "INTEGRITY_FAILURE: THRESHOLD_MANIFEST.json not found at "
                f"{self.manifest_path}. Harness cannot start without manifest."
            )

        try:
            with open(self.manifest_path, "r", encoding="utf-8") as f:
                raw = f.read()
            data = json.loads(raw)
        except Exception as exc:
            raise RuntimeError(
                f"INTEGRITY_FAILURE: Failed to load or parse THRESHOLD_MANIFEST.json: {exc}"
            ) from exc

        # MVI-01: Compute hash excluding manifest_hash field.
        data_for_hash = {k: v for k, v in data.items() if k != "manifest_hash"}
        computed_hash = hashlib.sha256(
            json.dumps(data_for_hash, sort_keys=True, separators=(",", ":")).encode("utf-8")
        ).hexdigest()

        # MVI-02: Verify computed hash matches stored manifest_hash.
        stored_hash = data.get("manifest_hash", "")
        if (
            stored_hash
            and stored_hash != "BUILD_TIME_PLACEHOLDER"
            and stored_hash != computed_hash
        ):
            raise RuntimeError(
                f"MANIFEST_HASH_MISMATCH: Computed hash {computed_hash[:16]}... "
                f"does not match stored hash {stored_hash[:16]}... "
                "System start denied. Possible tampering."
            )

        # MVI-05: Check for absence of table_hash in joint_risk_multiplier_table.
        jrmt = data.get("joint_risk_multiplier_table", {})
        if "table_hash" in jrmt:
            raise RuntimeError(
                "MANIFEST_TABLEHASH_PRESENT: joint_risk_multiplier_table must not "
                "contain a table_hash key per Manifest Authority Policy."
            )

        # MVI-03: Extract the three FAS v6.1.0 constants.
        try:
            thresholds = data["thresholds"]
            shock_cap  = float(thresholds["shock_exposure_cap"])
            max_dd     = None
            vol_trig   = float(thresholds["vol_compression_trigger"])
        except (KeyError, ValueError) as exc:
            raise RuntimeError(
                f"INTEGRITY_FAILURE: Missing or invalid threshold key in manifest: {exc}"
            ) from exc

        # MVI-04: Verify the three extracted constants equal FAS v6.1.0 values.
        if not self._floats_equal(shock_cap, self._EXPECTED_SHOCK_EXPOSURE_CAP):
            raise RuntimeError(
                f"MANIFEST_CONSTANT_MISMATCH: shock_exposure_cap={shock_cap} "
                f"expected {self._EXPECTED_SHOCK_EXPOSURE_CAP}."
            )
        if not self._floats_equal(max_dd, self._EXPECTED_MAX_DRAWDOWN_THRESHOLD):
            raise RuntimeError(
                f"MANIFEST_CONSTANT_MISMATCH: max_drawdown_threshold={max_dd} "
                f"expected {self._EXPECTED_MAX_DRAWDOWN_THRESHOLD}."
            )
        if not self._floats_equal(vol_trig, self._EXPECTED_VOL_COMPRESSION_TRIGGER):
            raise RuntimeError(
                f"MANIFEST_CONSTANT_MISMATCH: vol_compression_trigger={vol_trig} "
                f"expected {self._EXPECTED_VOL_COMPRESSION_TRIGGER}."
            )

        # MVI-06: Return computed hash for propagation into ExecutionRecords.
        return computed_hash, thresholds

    def xǁManifestValidatorǁvalidate__mutmut_83(self) -> Tuple[str, Dict[str, Any]]:
        """
        Execute full manifest validation.

        Returns:
          (computed_hash, thresholds_dict)
          computed_hash -- SHA-256 hex digest of the manifest content.
          thresholds    -- dict from manifest["thresholds"] section.

        Raises RuntimeError with failure_type_id prefix on any hard failure.
        Failure types raised here:
          MANIFEST_HASH_MISMATCH    -- MVI-02
          MANIFEST_CONSTANT_MISMATCH -- MVI-04
          MANIFEST_TABLEHASH_PRESENT -- MVI-05
          INTEGRITY_FAILURE          -- missing file or parse error
        """
        # MVI-01: Load manifest file.
        if not self.manifest_path.exists():
            raise RuntimeError(
                "INTEGRITY_FAILURE: THRESHOLD_MANIFEST.json not found at "
                f"{self.manifest_path}. Harness cannot start without manifest."
            )

        try:
            with open(self.manifest_path, "r", encoding="utf-8") as f:
                raw = f.read()
            data = json.loads(raw)
        except Exception as exc:
            raise RuntimeError(
                f"INTEGRITY_FAILURE: Failed to load or parse THRESHOLD_MANIFEST.json: {exc}"
            ) from exc

        # MVI-01: Compute hash excluding manifest_hash field.
        data_for_hash = {k: v for k, v in data.items() if k != "manifest_hash"}
        computed_hash = hashlib.sha256(
            json.dumps(data_for_hash, sort_keys=True, separators=(",", ":")).encode("utf-8")
        ).hexdigest()

        # MVI-02: Verify computed hash matches stored manifest_hash.
        stored_hash = data.get("manifest_hash", "")
        if (
            stored_hash
            and stored_hash != "BUILD_TIME_PLACEHOLDER"
            and stored_hash != computed_hash
        ):
            raise RuntimeError(
                f"MANIFEST_HASH_MISMATCH: Computed hash {computed_hash[:16]}... "
                f"does not match stored hash {stored_hash[:16]}... "
                "System start denied. Possible tampering."
            )

        # MVI-05: Check for absence of table_hash in joint_risk_multiplier_table.
        jrmt = data.get("joint_risk_multiplier_table", {})
        if "table_hash" in jrmt:
            raise RuntimeError(
                "MANIFEST_TABLEHASH_PRESENT: joint_risk_multiplier_table must not "
                "contain a table_hash key per Manifest Authority Policy."
            )

        # MVI-03: Extract the three FAS v6.1.0 constants.
        try:
            thresholds = data["thresholds"]
            shock_cap  = float(thresholds["shock_exposure_cap"])
            max_dd     = float(None)
            vol_trig   = float(thresholds["vol_compression_trigger"])
        except (KeyError, ValueError) as exc:
            raise RuntimeError(
                f"INTEGRITY_FAILURE: Missing or invalid threshold key in manifest: {exc}"
            ) from exc

        # MVI-04: Verify the three extracted constants equal FAS v6.1.0 values.
        if not self._floats_equal(shock_cap, self._EXPECTED_SHOCK_EXPOSURE_CAP):
            raise RuntimeError(
                f"MANIFEST_CONSTANT_MISMATCH: shock_exposure_cap={shock_cap} "
                f"expected {self._EXPECTED_SHOCK_EXPOSURE_CAP}."
            )
        if not self._floats_equal(max_dd, self._EXPECTED_MAX_DRAWDOWN_THRESHOLD):
            raise RuntimeError(
                f"MANIFEST_CONSTANT_MISMATCH: max_drawdown_threshold={max_dd} "
                f"expected {self._EXPECTED_MAX_DRAWDOWN_THRESHOLD}."
            )
        if not self._floats_equal(vol_trig, self._EXPECTED_VOL_COMPRESSION_TRIGGER):
            raise RuntimeError(
                f"MANIFEST_CONSTANT_MISMATCH: vol_compression_trigger={vol_trig} "
                f"expected {self._EXPECTED_VOL_COMPRESSION_TRIGGER}."
            )

        # MVI-06: Return computed hash for propagation into ExecutionRecords.
        return computed_hash, thresholds

    def xǁManifestValidatorǁvalidate__mutmut_84(self) -> Tuple[str, Dict[str, Any]]:
        """
        Execute full manifest validation.

        Returns:
          (computed_hash, thresholds_dict)
          computed_hash -- SHA-256 hex digest of the manifest content.
          thresholds    -- dict from manifest["thresholds"] section.

        Raises RuntimeError with failure_type_id prefix on any hard failure.
        Failure types raised here:
          MANIFEST_HASH_MISMATCH    -- MVI-02
          MANIFEST_CONSTANT_MISMATCH -- MVI-04
          MANIFEST_TABLEHASH_PRESENT -- MVI-05
          INTEGRITY_FAILURE          -- missing file or parse error
        """
        # MVI-01: Load manifest file.
        if not self.manifest_path.exists():
            raise RuntimeError(
                "INTEGRITY_FAILURE: THRESHOLD_MANIFEST.json not found at "
                f"{self.manifest_path}. Harness cannot start without manifest."
            )

        try:
            with open(self.manifest_path, "r", encoding="utf-8") as f:
                raw = f.read()
            data = json.loads(raw)
        except Exception as exc:
            raise RuntimeError(
                f"INTEGRITY_FAILURE: Failed to load or parse THRESHOLD_MANIFEST.json: {exc}"
            ) from exc

        # MVI-01: Compute hash excluding manifest_hash field.
        data_for_hash = {k: v for k, v in data.items() if k != "manifest_hash"}
        computed_hash = hashlib.sha256(
            json.dumps(data_for_hash, sort_keys=True, separators=(",", ":")).encode("utf-8")
        ).hexdigest()

        # MVI-02: Verify computed hash matches stored manifest_hash.
        stored_hash = data.get("manifest_hash", "")
        if (
            stored_hash
            and stored_hash != "BUILD_TIME_PLACEHOLDER"
            and stored_hash != computed_hash
        ):
            raise RuntimeError(
                f"MANIFEST_HASH_MISMATCH: Computed hash {computed_hash[:16]}... "
                f"does not match stored hash {stored_hash[:16]}... "
                "System start denied. Possible tampering."
            )

        # MVI-05: Check for absence of table_hash in joint_risk_multiplier_table.
        jrmt = data.get("joint_risk_multiplier_table", {})
        if "table_hash" in jrmt:
            raise RuntimeError(
                "MANIFEST_TABLEHASH_PRESENT: joint_risk_multiplier_table must not "
                "contain a table_hash key per Manifest Authority Policy."
            )

        # MVI-03: Extract the three FAS v6.1.0 constants.
        try:
            thresholds = data["thresholds"]
            shock_cap  = float(thresholds["shock_exposure_cap"])
            max_dd     = float(thresholds["XXmax_drawdown_thresholdXX"])
            vol_trig   = float(thresholds["vol_compression_trigger"])
        except (KeyError, ValueError) as exc:
            raise RuntimeError(
                f"INTEGRITY_FAILURE: Missing or invalid threshold key in manifest: {exc}"
            ) from exc

        # MVI-04: Verify the three extracted constants equal FAS v6.1.0 values.
        if not self._floats_equal(shock_cap, self._EXPECTED_SHOCK_EXPOSURE_CAP):
            raise RuntimeError(
                f"MANIFEST_CONSTANT_MISMATCH: shock_exposure_cap={shock_cap} "
                f"expected {self._EXPECTED_SHOCK_EXPOSURE_CAP}."
            )
        if not self._floats_equal(max_dd, self._EXPECTED_MAX_DRAWDOWN_THRESHOLD):
            raise RuntimeError(
                f"MANIFEST_CONSTANT_MISMATCH: max_drawdown_threshold={max_dd} "
                f"expected {self._EXPECTED_MAX_DRAWDOWN_THRESHOLD}."
            )
        if not self._floats_equal(vol_trig, self._EXPECTED_VOL_COMPRESSION_TRIGGER):
            raise RuntimeError(
                f"MANIFEST_CONSTANT_MISMATCH: vol_compression_trigger={vol_trig} "
                f"expected {self._EXPECTED_VOL_COMPRESSION_TRIGGER}."
            )

        # MVI-06: Return computed hash for propagation into ExecutionRecords.
        return computed_hash, thresholds

    def xǁManifestValidatorǁvalidate__mutmut_85(self) -> Tuple[str, Dict[str, Any]]:
        """
        Execute full manifest validation.

        Returns:
          (computed_hash, thresholds_dict)
          computed_hash -- SHA-256 hex digest of the manifest content.
          thresholds    -- dict from manifest["thresholds"] section.

        Raises RuntimeError with failure_type_id prefix on any hard failure.
        Failure types raised here:
          MANIFEST_HASH_MISMATCH    -- MVI-02
          MANIFEST_CONSTANT_MISMATCH -- MVI-04
          MANIFEST_TABLEHASH_PRESENT -- MVI-05
          INTEGRITY_FAILURE          -- missing file or parse error
        """
        # MVI-01: Load manifest file.
        if not self.manifest_path.exists():
            raise RuntimeError(
                "INTEGRITY_FAILURE: THRESHOLD_MANIFEST.json not found at "
                f"{self.manifest_path}. Harness cannot start without manifest."
            )

        try:
            with open(self.manifest_path, "r", encoding="utf-8") as f:
                raw = f.read()
            data = json.loads(raw)
        except Exception as exc:
            raise RuntimeError(
                f"INTEGRITY_FAILURE: Failed to load or parse THRESHOLD_MANIFEST.json: {exc}"
            ) from exc

        # MVI-01: Compute hash excluding manifest_hash field.
        data_for_hash = {k: v for k, v in data.items() if k != "manifest_hash"}
        computed_hash = hashlib.sha256(
            json.dumps(data_for_hash, sort_keys=True, separators=(",", ":")).encode("utf-8")
        ).hexdigest()

        # MVI-02: Verify computed hash matches stored manifest_hash.
        stored_hash = data.get("manifest_hash", "")
        if (
            stored_hash
            and stored_hash != "BUILD_TIME_PLACEHOLDER"
            and stored_hash != computed_hash
        ):
            raise RuntimeError(
                f"MANIFEST_HASH_MISMATCH: Computed hash {computed_hash[:16]}... "
                f"does not match stored hash {stored_hash[:16]}... "
                "System start denied. Possible tampering."
            )

        # MVI-05: Check for absence of table_hash in joint_risk_multiplier_table.
        jrmt = data.get("joint_risk_multiplier_table", {})
        if "table_hash" in jrmt:
            raise RuntimeError(
                "MANIFEST_TABLEHASH_PRESENT: joint_risk_multiplier_table must not "
                "contain a table_hash key per Manifest Authority Policy."
            )

        # MVI-03: Extract the three FAS v6.1.0 constants.
        try:
            thresholds = data["thresholds"]
            shock_cap  = float(thresholds["shock_exposure_cap"])
            max_dd     = float(thresholds["MAX_DRAWDOWN_THRESHOLD"])
            vol_trig   = float(thresholds["vol_compression_trigger"])
        except (KeyError, ValueError) as exc:
            raise RuntimeError(
                f"INTEGRITY_FAILURE: Missing or invalid threshold key in manifest: {exc}"
            ) from exc

        # MVI-04: Verify the three extracted constants equal FAS v6.1.0 values.
        if not self._floats_equal(shock_cap, self._EXPECTED_SHOCK_EXPOSURE_CAP):
            raise RuntimeError(
                f"MANIFEST_CONSTANT_MISMATCH: shock_exposure_cap={shock_cap} "
                f"expected {self._EXPECTED_SHOCK_EXPOSURE_CAP}."
            )
        if not self._floats_equal(max_dd, self._EXPECTED_MAX_DRAWDOWN_THRESHOLD):
            raise RuntimeError(
                f"MANIFEST_CONSTANT_MISMATCH: max_drawdown_threshold={max_dd} "
                f"expected {self._EXPECTED_MAX_DRAWDOWN_THRESHOLD}."
            )
        if not self._floats_equal(vol_trig, self._EXPECTED_VOL_COMPRESSION_TRIGGER):
            raise RuntimeError(
                f"MANIFEST_CONSTANT_MISMATCH: vol_compression_trigger={vol_trig} "
                f"expected {self._EXPECTED_VOL_COMPRESSION_TRIGGER}."
            )

        # MVI-06: Return computed hash for propagation into ExecutionRecords.
        return computed_hash, thresholds

    def xǁManifestValidatorǁvalidate__mutmut_86(self) -> Tuple[str, Dict[str, Any]]:
        """
        Execute full manifest validation.

        Returns:
          (computed_hash, thresholds_dict)
          computed_hash -- SHA-256 hex digest of the manifest content.
          thresholds    -- dict from manifest["thresholds"] section.

        Raises RuntimeError with failure_type_id prefix on any hard failure.
        Failure types raised here:
          MANIFEST_HASH_MISMATCH    -- MVI-02
          MANIFEST_CONSTANT_MISMATCH -- MVI-04
          MANIFEST_TABLEHASH_PRESENT -- MVI-05
          INTEGRITY_FAILURE          -- missing file or parse error
        """
        # MVI-01: Load manifest file.
        if not self.manifest_path.exists():
            raise RuntimeError(
                "INTEGRITY_FAILURE: THRESHOLD_MANIFEST.json not found at "
                f"{self.manifest_path}. Harness cannot start without manifest."
            )

        try:
            with open(self.manifest_path, "r", encoding="utf-8") as f:
                raw = f.read()
            data = json.loads(raw)
        except Exception as exc:
            raise RuntimeError(
                f"INTEGRITY_FAILURE: Failed to load or parse THRESHOLD_MANIFEST.json: {exc}"
            ) from exc

        # MVI-01: Compute hash excluding manifest_hash field.
        data_for_hash = {k: v for k, v in data.items() if k != "manifest_hash"}
        computed_hash = hashlib.sha256(
            json.dumps(data_for_hash, sort_keys=True, separators=(",", ":")).encode("utf-8")
        ).hexdigest()

        # MVI-02: Verify computed hash matches stored manifest_hash.
        stored_hash = data.get("manifest_hash", "")
        if (
            stored_hash
            and stored_hash != "BUILD_TIME_PLACEHOLDER"
            and stored_hash != computed_hash
        ):
            raise RuntimeError(
                f"MANIFEST_HASH_MISMATCH: Computed hash {computed_hash[:16]}... "
                f"does not match stored hash {stored_hash[:16]}... "
                "System start denied. Possible tampering."
            )

        # MVI-05: Check for absence of table_hash in joint_risk_multiplier_table.
        jrmt = data.get("joint_risk_multiplier_table", {})
        if "table_hash" in jrmt:
            raise RuntimeError(
                "MANIFEST_TABLEHASH_PRESENT: joint_risk_multiplier_table must not "
                "contain a table_hash key per Manifest Authority Policy."
            )

        # MVI-03: Extract the three FAS v6.1.0 constants.
        try:
            thresholds = data["thresholds"]
            shock_cap  = float(thresholds["shock_exposure_cap"])
            max_dd     = float(thresholds["max_drawdown_threshold"])
            vol_trig   = None
        except (KeyError, ValueError) as exc:
            raise RuntimeError(
                f"INTEGRITY_FAILURE: Missing or invalid threshold key in manifest: {exc}"
            ) from exc

        # MVI-04: Verify the three extracted constants equal FAS v6.1.0 values.
        if not self._floats_equal(shock_cap, self._EXPECTED_SHOCK_EXPOSURE_CAP):
            raise RuntimeError(
                f"MANIFEST_CONSTANT_MISMATCH: shock_exposure_cap={shock_cap} "
                f"expected {self._EXPECTED_SHOCK_EXPOSURE_CAP}."
            )
        if not self._floats_equal(max_dd, self._EXPECTED_MAX_DRAWDOWN_THRESHOLD):
            raise RuntimeError(
                f"MANIFEST_CONSTANT_MISMATCH: max_drawdown_threshold={max_dd} "
                f"expected {self._EXPECTED_MAX_DRAWDOWN_THRESHOLD}."
            )
        if not self._floats_equal(vol_trig, self._EXPECTED_VOL_COMPRESSION_TRIGGER):
            raise RuntimeError(
                f"MANIFEST_CONSTANT_MISMATCH: vol_compression_trigger={vol_trig} "
                f"expected {self._EXPECTED_VOL_COMPRESSION_TRIGGER}."
            )

        # MVI-06: Return computed hash for propagation into ExecutionRecords.
        return computed_hash, thresholds

    def xǁManifestValidatorǁvalidate__mutmut_87(self) -> Tuple[str, Dict[str, Any]]:
        """
        Execute full manifest validation.

        Returns:
          (computed_hash, thresholds_dict)
          computed_hash -- SHA-256 hex digest of the manifest content.
          thresholds    -- dict from manifest["thresholds"] section.

        Raises RuntimeError with failure_type_id prefix on any hard failure.
        Failure types raised here:
          MANIFEST_HASH_MISMATCH    -- MVI-02
          MANIFEST_CONSTANT_MISMATCH -- MVI-04
          MANIFEST_TABLEHASH_PRESENT -- MVI-05
          INTEGRITY_FAILURE          -- missing file or parse error
        """
        # MVI-01: Load manifest file.
        if not self.manifest_path.exists():
            raise RuntimeError(
                "INTEGRITY_FAILURE: THRESHOLD_MANIFEST.json not found at "
                f"{self.manifest_path}. Harness cannot start without manifest."
            )

        try:
            with open(self.manifest_path, "r", encoding="utf-8") as f:
                raw = f.read()
            data = json.loads(raw)
        except Exception as exc:
            raise RuntimeError(
                f"INTEGRITY_FAILURE: Failed to load or parse THRESHOLD_MANIFEST.json: {exc}"
            ) from exc

        # MVI-01: Compute hash excluding manifest_hash field.
        data_for_hash = {k: v for k, v in data.items() if k != "manifest_hash"}
        computed_hash = hashlib.sha256(
            json.dumps(data_for_hash, sort_keys=True, separators=(",", ":")).encode("utf-8")
        ).hexdigest()

        # MVI-02: Verify computed hash matches stored manifest_hash.
        stored_hash = data.get("manifest_hash", "")
        if (
            stored_hash
            and stored_hash != "BUILD_TIME_PLACEHOLDER"
            and stored_hash != computed_hash
        ):
            raise RuntimeError(
                f"MANIFEST_HASH_MISMATCH: Computed hash {computed_hash[:16]}... "
                f"does not match stored hash {stored_hash[:16]}... "
                "System start denied. Possible tampering."
            )

        # MVI-05: Check for absence of table_hash in joint_risk_multiplier_table.
        jrmt = data.get("joint_risk_multiplier_table", {})
        if "table_hash" in jrmt:
            raise RuntimeError(
                "MANIFEST_TABLEHASH_PRESENT: joint_risk_multiplier_table must not "
                "contain a table_hash key per Manifest Authority Policy."
            )

        # MVI-03: Extract the three FAS v6.1.0 constants.
        try:
            thresholds = data["thresholds"]
            shock_cap  = float(thresholds["shock_exposure_cap"])
            max_dd     = float(thresholds["max_drawdown_threshold"])
            vol_trig   = float(None)
        except (KeyError, ValueError) as exc:
            raise RuntimeError(
                f"INTEGRITY_FAILURE: Missing or invalid threshold key in manifest: {exc}"
            ) from exc

        # MVI-04: Verify the three extracted constants equal FAS v6.1.0 values.
        if not self._floats_equal(shock_cap, self._EXPECTED_SHOCK_EXPOSURE_CAP):
            raise RuntimeError(
                f"MANIFEST_CONSTANT_MISMATCH: shock_exposure_cap={shock_cap} "
                f"expected {self._EXPECTED_SHOCK_EXPOSURE_CAP}."
            )
        if not self._floats_equal(max_dd, self._EXPECTED_MAX_DRAWDOWN_THRESHOLD):
            raise RuntimeError(
                f"MANIFEST_CONSTANT_MISMATCH: max_drawdown_threshold={max_dd} "
                f"expected {self._EXPECTED_MAX_DRAWDOWN_THRESHOLD}."
            )
        if not self._floats_equal(vol_trig, self._EXPECTED_VOL_COMPRESSION_TRIGGER):
            raise RuntimeError(
                f"MANIFEST_CONSTANT_MISMATCH: vol_compression_trigger={vol_trig} "
                f"expected {self._EXPECTED_VOL_COMPRESSION_TRIGGER}."
            )

        # MVI-06: Return computed hash for propagation into ExecutionRecords.
        return computed_hash, thresholds

    def xǁManifestValidatorǁvalidate__mutmut_88(self) -> Tuple[str, Dict[str, Any]]:
        """
        Execute full manifest validation.

        Returns:
          (computed_hash, thresholds_dict)
          computed_hash -- SHA-256 hex digest of the manifest content.
          thresholds    -- dict from manifest["thresholds"] section.

        Raises RuntimeError with failure_type_id prefix on any hard failure.
        Failure types raised here:
          MANIFEST_HASH_MISMATCH    -- MVI-02
          MANIFEST_CONSTANT_MISMATCH -- MVI-04
          MANIFEST_TABLEHASH_PRESENT -- MVI-05
          INTEGRITY_FAILURE          -- missing file or parse error
        """
        # MVI-01: Load manifest file.
        if not self.manifest_path.exists():
            raise RuntimeError(
                "INTEGRITY_FAILURE: THRESHOLD_MANIFEST.json not found at "
                f"{self.manifest_path}. Harness cannot start without manifest."
            )

        try:
            with open(self.manifest_path, "r", encoding="utf-8") as f:
                raw = f.read()
            data = json.loads(raw)
        except Exception as exc:
            raise RuntimeError(
                f"INTEGRITY_FAILURE: Failed to load or parse THRESHOLD_MANIFEST.json: {exc}"
            ) from exc

        # MVI-01: Compute hash excluding manifest_hash field.
        data_for_hash = {k: v for k, v in data.items() if k != "manifest_hash"}
        computed_hash = hashlib.sha256(
            json.dumps(data_for_hash, sort_keys=True, separators=(",", ":")).encode("utf-8")
        ).hexdigest()

        # MVI-02: Verify computed hash matches stored manifest_hash.
        stored_hash = data.get("manifest_hash", "")
        if (
            stored_hash
            and stored_hash != "BUILD_TIME_PLACEHOLDER"
            and stored_hash != computed_hash
        ):
            raise RuntimeError(
                f"MANIFEST_HASH_MISMATCH: Computed hash {computed_hash[:16]}... "
                f"does not match stored hash {stored_hash[:16]}... "
                "System start denied. Possible tampering."
            )

        # MVI-05: Check for absence of table_hash in joint_risk_multiplier_table.
        jrmt = data.get("joint_risk_multiplier_table", {})
        if "table_hash" in jrmt:
            raise RuntimeError(
                "MANIFEST_TABLEHASH_PRESENT: joint_risk_multiplier_table must not "
                "contain a table_hash key per Manifest Authority Policy."
            )

        # MVI-03: Extract the three FAS v6.1.0 constants.
        try:
            thresholds = data["thresholds"]
            shock_cap  = float(thresholds["shock_exposure_cap"])
            max_dd     = float(thresholds["max_drawdown_threshold"])
            vol_trig   = float(thresholds["XXvol_compression_triggerXX"])
        except (KeyError, ValueError) as exc:
            raise RuntimeError(
                f"INTEGRITY_FAILURE: Missing or invalid threshold key in manifest: {exc}"
            ) from exc

        # MVI-04: Verify the three extracted constants equal FAS v6.1.0 values.
        if not self._floats_equal(shock_cap, self._EXPECTED_SHOCK_EXPOSURE_CAP):
            raise RuntimeError(
                f"MANIFEST_CONSTANT_MISMATCH: shock_exposure_cap={shock_cap} "
                f"expected {self._EXPECTED_SHOCK_EXPOSURE_CAP}."
            )
        if not self._floats_equal(max_dd, self._EXPECTED_MAX_DRAWDOWN_THRESHOLD):
            raise RuntimeError(
                f"MANIFEST_CONSTANT_MISMATCH: max_drawdown_threshold={max_dd} "
                f"expected {self._EXPECTED_MAX_DRAWDOWN_THRESHOLD}."
            )
        if not self._floats_equal(vol_trig, self._EXPECTED_VOL_COMPRESSION_TRIGGER):
            raise RuntimeError(
                f"MANIFEST_CONSTANT_MISMATCH: vol_compression_trigger={vol_trig} "
                f"expected {self._EXPECTED_VOL_COMPRESSION_TRIGGER}."
            )

        # MVI-06: Return computed hash for propagation into ExecutionRecords.
        return computed_hash, thresholds

    def xǁManifestValidatorǁvalidate__mutmut_89(self) -> Tuple[str, Dict[str, Any]]:
        """
        Execute full manifest validation.

        Returns:
          (computed_hash, thresholds_dict)
          computed_hash -- SHA-256 hex digest of the manifest content.
          thresholds    -- dict from manifest["thresholds"] section.

        Raises RuntimeError with failure_type_id prefix on any hard failure.
        Failure types raised here:
          MANIFEST_HASH_MISMATCH    -- MVI-02
          MANIFEST_CONSTANT_MISMATCH -- MVI-04
          MANIFEST_TABLEHASH_PRESENT -- MVI-05
          INTEGRITY_FAILURE          -- missing file or parse error
        """
        # MVI-01: Load manifest file.
        if not self.manifest_path.exists():
            raise RuntimeError(
                "INTEGRITY_FAILURE: THRESHOLD_MANIFEST.json not found at "
                f"{self.manifest_path}. Harness cannot start without manifest."
            )

        try:
            with open(self.manifest_path, "r", encoding="utf-8") as f:
                raw = f.read()
            data = json.loads(raw)
        except Exception as exc:
            raise RuntimeError(
                f"INTEGRITY_FAILURE: Failed to load or parse THRESHOLD_MANIFEST.json: {exc}"
            ) from exc

        # MVI-01: Compute hash excluding manifest_hash field.
        data_for_hash = {k: v for k, v in data.items() if k != "manifest_hash"}
        computed_hash = hashlib.sha256(
            json.dumps(data_for_hash, sort_keys=True, separators=(",", ":")).encode("utf-8")
        ).hexdigest()

        # MVI-02: Verify computed hash matches stored manifest_hash.
        stored_hash = data.get("manifest_hash", "")
        if (
            stored_hash
            and stored_hash != "BUILD_TIME_PLACEHOLDER"
            and stored_hash != computed_hash
        ):
            raise RuntimeError(
                f"MANIFEST_HASH_MISMATCH: Computed hash {computed_hash[:16]}... "
                f"does not match stored hash {stored_hash[:16]}... "
                "System start denied. Possible tampering."
            )

        # MVI-05: Check for absence of table_hash in joint_risk_multiplier_table.
        jrmt = data.get("joint_risk_multiplier_table", {})
        if "table_hash" in jrmt:
            raise RuntimeError(
                "MANIFEST_TABLEHASH_PRESENT: joint_risk_multiplier_table must not "
                "contain a table_hash key per Manifest Authority Policy."
            )

        # MVI-03: Extract the three FAS v6.1.0 constants.
        try:
            thresholds = data["thresholds"]
            shock_cap  = float(thresholds["shock_exposure_cap"])
            max_dd     = float(thresholds["max_drawdown_threshold"])
            vol_trig   = float(thresholds["VOL_COMPRESSION_TRIGGER"])
        except (KeyError, ValueError) as exc:
            raise RuntimeError(
                f"INTEGRITY_FAILURE: Missing or invalid threshold key in manifest: {exc}"
            ) from exc

        # MVI-04: Verify the three extracted constants equal FAS v6.1.0 values.
        if not self._floats_equal(shock_cap, self._EXPECTED_SHOCK_EXPOSURE_CAP):
            raise RuntimeError(
                f"MANIFEST_CONSTANT_MISMATCH: shock_exposure_cap={shock_cap} "
                f"expected {self._EXPECTED_SHOCK_EXPOSURE_CAP}."
            )
        if not self._floats_equal(max_dd, self._EXPECTED_MAX_DRAWDOWN_THRESHOLD):
            raise RuntimeError(
                f"MANIFEST_CONSTANT_MISMATCH: max_drawdown_threshold={max_dd} "
                f"expected {self._EXPECTED_MAX_DRAWDOWN_THRESHOLD}."
            )
        if not self._floats_equal(vol_trig, self._EXPECTED_VOL_COMPRESSION_TRIGGER):
            raise RuntimeError(
                f"MANIFEST_CONSTANT_MISMATCH: vol_compression_trigger={vol_trig} "
                f"expected {self._EXPECTED_VOL_COMPRESSION_TRIGGER}."
            )

        # MVI-06: Return computed hash for propagation into ExecutionRecords.
        return computed_hash, thresholds

    def xǁManifestValidatorǁvalidate__mutmut_90(self) -> Tuple[str, Dict[str, Any]]:
        """
        Execute full manifest validation.

        Returns:
          (computed_hash, thresholds_dict)
          computed_hash -- SHA-256 hex digest of the manifest content.
          thresholds    -- dict from manifest["thresholds"] section.

        Raises RuntimeError with failure_type_id prefix on any hard failure.
        Failure types raised here:
          MANIFEST_HASH_MISMATCH    -- MVI-02
          MANIFEST_CONSTANT_MISMATCH -- MVI-04
          MANIFEST_TABLEHASH_PRESENT -- MVI-05
          INTEGRITY_FAILURE          -- missing file or parse error
        """
        # MVI-01: Load manifest file.
        if not self.manifest_path.exists():
            raise RuntimeError(
                "INTEGRITY_FAILURE: THRESHOLD_MANIFEST.json not found at "
                f"{self.manifest_path}. Harness cannot start without manifest."
            )

        try:
            with open(self.manifest_path, "r", encoding="utf-8") as f:
                raw = f.read()
            data = json.loads(raw)
        except Exception as exc:
            raise RuntimeError(
                f"INTEGRITY_FAILURE: Failed to load or parse THRESHOLD_MANIFEST.json: {exc}"
            ) from exc

        # MVI-01: Compute hash excluding manifest_hash field.
        data_for_hash = {k: v for k, v in data.items() if k != "manifest_hash"}
        computed_hash = hashlib.sha256(
            json.dumps(data_for_hash, sort_keys=True, separators=(",", ":")).encode("utf-8")
        ).hexdigest()

        # MVI-02: Verify computed hash matches stored manifest_hash.
        stored_hash = data.get("manifest_hash", "")
        if (
            stored_hash
            and stored_hash != "BUILD_TIME_PLACEHOLDER"
            and stored_hash != computed_hash
        ):
            raise RuntimeError(
                f"MANIFEST_HASH_MISMATCH: Computed hash {computed_hash[:16]}... "
                f"does not match stored hash {stored_hash[:16]}... "
                "System start denied. Possible tampering."
            )

        # MVI-05: Check for absence of table_hash in joint_risk_multiplier_table.
        jrmt = data.get("joint_risk_multiplier_table", {})
        if "table_hash" in jrmt:
            raise RuntimeError(
                "MANIFEST_TABLEHASH_PRESENT: joint_risk_multiplier_table must not "
                "contain a table_hash key per Manifest Authority Policy."
            )

        # MVI-03: Extract the three FAS v6.1.0 constants.
        try:
            thresholds = data["thresholds"]
            shock_cap  = float(thresholds["shock_exposure_cap"])
            max_dd     = float(thresholds["max_drawdown_threshold"])
            vol_trig   = float(thresholds["vol_compression_trigger"])
        except (KeyError, ValueError) as exc:
            raise RuntimeError(
                None
            ) from exc

        # MVI-04: Verify the three extracted constants equal FAS v6.1.0 values.
        if not self._floats_equal(shock_cap, self._EXPECTED_SHOCK_EXPOSURE_CAP):
            raise RuntimeError(
                f"MANIFEST_CONSTANT_MISMATCH: shock_exposure_cap={shock_cap} "
                f"expected {self._EXPECTED_SHOCK_EXPOSURE_CAP}."
            )
        if not self._floats_equal(max_dd, self._EXPECTED_MAX_DRAWDOWN_THRESHOLD):
            raise RuntimeError(
                f"MANIFEST_CONSTANT_MISMATCH: max_drawdown_threshold={max_dd} "
                f"expected {self._EXPECTED_MAX_DRAWDOWN_THRESHOLD}."
            )
        if not self._floats_equal(vol_trig, self._EXPECTED_VOL_COMPRESSION_TRIGGER):
            raise RuntimeError(
                f"MANIFEST_CONSTANT_MISMATCH: vol_compression_trigger={vol_trig} "
                f"expected {self._EXPECTED_VOL_COMPRESSION_TRIGGER}."
            )

        # MVI-06: Return computed hash for propagation into ExecutionRecords.
        return computed_hash, thresholds

    def xǁManifestValidatorǁvalidate__mutmut_91(self) -> Tuple[str, Dict[str, Any]]:
        """
        Execute full manifest validation.

        Returns:
          (computed_hash, thresholds_dict)
          computed_hash -- SHA-256 hex digest of the manifest content.
          thresholds    -- dict from manifest["thresholds"] section.

        Raises RuntimeError with failure_type_id prefix on any hard failure.
        Failure types raised here:
          MANIFEST_HASH_MISMATCH    -- MVI-02
          MANIFEST_CONSTANT_MISMATCH -- MVI-04
          MANIFEST_TABLEHASH_PRESENT -- MVI-05
          INTEGRITY_FAILURE          -- missing file or parse error
        """
        # MVI-01: Load manifest file.
        if not self.manifest_path.exists():
            raise RuntimeError(
                "INTEGRITY_FAILURE: THRESHOLD_MANIFEST.json not found at "
                f"{self.manifest_path}. Harness cannot start without manifest."
            )

        try:
            with open(self.manifest_path, "r", encoding="utf-8") as f:
                raw = f.read()
            data = json.loads(raw)
        except Exception as exc:
            raise RuntimeError(
                f"INTEGRITY_FAILURE: Failed to load or parse THRESHOLD_MANIFEST.json: {exc}"
            ) from exc

        # MVI-01: Compute hash excluding manifest_hash field.
        data_for_hash = {k: v for k, v in data.items() if k != "manifest_hash"}
        computed_hash = hashlib.sha256(
            json.dumps(data_for_hash, sort_keys=True, separators=(",", ":")).encode("utf-8")
        ).hexdigest()

        # MVI-02: Verify computed hash matches stored manifest_hash.
        stored_hash = data.get("manifest_hash", "")
        if (
            stored_hash
            and stored_hash != "BUILD_TIME_PLACEHOLDER"
            and stored_hash != computed_hash
        ):
            raise RuntimeError(
                f"MANIFEST_HASH_MISMATCH: Computed hash {computed_hash[:16]}... "
                f"does not match stored hash {stored_hash[:16]}... "
                "System start denied. Possible tampering."
            )

        # MVI-05: Check for absence of table_hash in joint_risk_multiplier_table.
        jrmt = data.get("joint_risk_multiplier_table", {})
        if "table_hash" in jrmt:
            raise RuntimeError(
                "MANIFEST_TABLEHASH_PRESENT: joint_risk_multiplier_table must not "
                "contain a table_hash key per Manifest Authority Policy."
            )

        # MVI-03: Extract the three FAS v6.1.0 constants.
        try:
            thresholds = data["thresholds"]
            shock_cap  = float(thresholds["shock_exposure_cap"])
            max_dd     = float(thresholds["max_drawdown_threshold"])
            vol_trig   = float(thresholds["vol_compression_trigger"])
        except (KeyError, ValueError) as exc:
            raise RuntimeError(
                f"INTEGRITY_FAILURE: Missing or invalid threshold key in manifest: {exc}"
            ) from exc

        # MVI-04: Verify the three extracted constants equal FAS v6.1.0 values.
        if self._floats_equal(shock_cap, self._EXPECTED_SHOCK_EXPOSURE_CAP):
            raise RuntimeError(
                f"MANIFEST_CONSTANT_MISMATCH: shock_exposure_cap={shock_cap} "
                f"expected {self._EXPECTED_SHOCK_EXPOSURE_CAP}."
            )
        if not self._floats_equal(max_dd, self._EXPECTED_MAX_DRAWDOWN_THRESHOLD):
            raise RuntimeError(
                f"MANIFEST_CONSTANT_MISMATCH: max_drawdown_threshold={max_dd} "
                f"expected {self._EXPECTED_MAX_DRAWDOWN_THRESHOLD}."
            )
        if not self._floats_equal(vol_trig, self._EXPECTED_VOL_COMPRESSION_TRIGGER):
            raise RuntimeError(
                f"MANIFEST_CONSTANT_MISMATCH: vol_compression_trigger={vol_trig} "
                f"expected {self._EXPECTED_VOL_COMPRESSION_TRIGGER}."
            )

        # MVI-06: Return computed hash for propagation into ExecutionRecords.
        return computed_hash, thresholds

    def xǁManifestValidatorǁvalidate__mutmut_92(self) -> Tuple[str, Dict[str, Any]]:
        """
        Execute full manifest validation.

        Returns:
          (computed_hash, thresholds_dict)
          computed_hash -- SHA-256 hex digest of the manifest content.
          thresholds    -- dict from manifest["thresholds"] section.

        Raises RuntimeError with failure_type_id prefix on any hard failure.
        Failure types raised here:
          MANIFEST_HASH_MISMATCH    -- MVI-02
          MANIFEST_CONSTANT_MISMATCH -- MVI-04
          MANIFEST_TABLEHASH_PRESENT -- MVI-05
          INTEGRITY_FAILURE          -- missing file or parse error
        """
        # MVI-01: Load manifest file.
        if not self.manifest_path.exists():
            raise RuntimeError(
                "INTEGRITY_FAILURE: THRESHOLD_MANIFEST.json not found at "
                f"{self.manifest_path}. Harness cannot start without manifest."
            )

        try:
            with open(self.manifest_path, "r", encoding="utf-8") as f:
                raw = f.read()
            data = json.loads(raw)
        except Exception as exc:
            raise RuntimeError(
                f"INTEGRITY_FAILURE: Failed to load or parse THRESHOLD_MANIFEST.json: {exc}"
            ) from exc

        # MVI-01: Compute hash excluding manifest_hash field.
        data_for_hash = {k: v for k, v in data.items() if k != "manifest_hash"}
        computed_hash = hashlib.sha256(
            json.dumps(data_for_hash, sort_keys=True, separators=(",", ":")).encode("utf-8")
        ).hexdigest()

        # MVI-02: Verify computed hash matches stored manifest_hash.
        stored_hash = data.get("manifest_hash", "")
        if (
            stored_hash
            and stored_hash != "BUILD_TIME_PLACEHOLDER"
            and stored_hash != computed_hash
        ):
            raise RuntimeError(
                f"MANIFEST_HASH_MISMATCH: Computed hash {computed_hash[:16]}... "
                f"does not match stored hash {stored_hash[:16]}... "
                "System start denied. Possible tampering."
            )

        # MVI-05: Check for absence of table_hash in joint_risk_multiplier_table.
        jrmt = data.get("joint_risk_multiplier_table", {})
        if "table_hash" in jrmt:
            raise RuntimeError(
                "MANIFEST_TABLEHASH_PRESENT: joint_risk_multiplier_table must not "
                "contain a table_hash key per Manifest Authority Policy."
            )

        # MVI-03: Extract the three FAS v6.1.0 constants.
        try:
            thresholds = data["thresholds"]
            shock_cap  = float(thresholds["shock_exposure_cap"])
            max_dd     = float(thresholds["max_drawdown_threshold"])
            vol_trig   = float(thresholds["vol_compression_trigger"])
        except (KeyError, ValueError) as exc:
            raise RuntimeError(
                f"INTEGRITY_FAILURE: Missing or invalid threshold key in manifest: {exc}"
            ) from exc

        # MVI-04: Verify the three extracted constants equal FAS v6.1.0 values.
        if not self._floats_equal(None, self._EXPECTED_SHOCK_EXPOSURE_CAP):
            raise RuntimeError(
                f"MANIFEST_CONSTANT_MISMATCH: shock_exposure_cap={shock_cap} "
                f"expected {self._EXPECTED_SHOCK_EXPOSURE_CAP}."
            )
        if not self._floats_equal(max_dd, self._EXPECTED_MAX_DRAWDOWN_THRESHOLD):
            raise RuntimeError(
                f"MANIFEST_CONSTANT_MISMATCH: max_drawdown_threshold={max_dd} "
                f"expected {self._EXPECTED_MAX_DRAWDOWN_THRESHOLD}."
            )
        if not self._floats_equal(vol_trig, self._EXPECTED_VOL_COMPRESSION_TRIGGER):
            raise RuntimeError(
                f"MANIFEST_CONSTANT_MISMATCH: vol_compression_trigger={vol_trig} "
                f"expected {self._EXPECTED_VOL_COMPRESSION_TRIGGER}."
            )

        # MVI-06: Return computed hash for propagation into ExecutionRecords.
        return computed_hash, thresholds

    def xǁManifestValidatorǁvalidate__mutmut_93(self) -> Tuple[str, Dict[str, Any]]:
        """
        Execute full manifest validation.

        Returns:
          (computed_hash, thresholds_dict)
          computed_hash -- SHA-256 hex digest of the manifest content.
          thresholds    -- dict from manifest["thresholds"] section.

        Raises RuntimeError with failure_type_id prefix on any hard failure.
        Failure types raised here:
          MANIFEST_HASH_MISMATCH    -- MVI-02
          MANIFEST_CONSTANT_MISMATCH -- MVI-04
          MANIFEST_TABLEHASH_PRESENT -- MVI-05
          INTEGRITY_FAILURE          -- missing file or parse error
        """
        # MVI-01: Load manifest file.
        if not self.manifest_path.exists():
            raise RuntimeError(
                "INTEGRITY_FAILURE: THRESHOLD_MANIFEST.json not found at "
                f"{self.manifest_path}. Harness cannot start without manifest."
            )

        try:
            with open(self.manifest_path, "r", encoding="utf-8") as f:
                raw = f.read()
            data = json.loads(raw)
        except Exception as exc:
            raise RuntimeError(
                f"INTEGRITY_FAILURE: Failed to load or parse THRESHOLD_MANIFEST.json: {exc}"
            ) from exc

        # MVI-01: Compute hash excluding manifest_hash field.
        data_for_hash = {k: v for k, v in data.items() if k != "manifest_hash"}
        computed_hash = hashlib.sha256(
            json.dumps(data_for_hash, sort_keys=True, separators=(",", ":")).encode("utf-8")
        ).hexdigest()

        # MVI-02: Verify computed hash matches stored manifest_hash.
        stored_hash = data.get("manifest_hash", "")
        if (
            stored_hash
            and stored_hash != "BUILD_TIME_PLACEHOLDER"
            and stored_hash != computed_hash
        ):
            raise RuntimeError(
                f"MANIFEST_HASH_MISMATCH: Computed hash {computed_hash[:16]}... "
                f"does not match stored hash {stored_hash[:16]}... "
                "System start denied. Possible tampering."
            )

        # MVI-05: Check for absence of table_hash in joint_risk_multiplier_table.
        jrmt = data.get("joint_risk_multiplier_table", {})
        if "table_hash" in jrmt:
            raise RuntimeError(
                "MANIFEST_TABLEHASH_PRESENT: joint_risk_multiplier_table must not "
                "contain a table_hash key per Manifest Authority Policy."
            )

        # MVI-03: Extract the three FAS v6.1.0 constants.
        try:
            thresholds = data["thresholds"]
            shock_cap  = float(thresholds["shock_exposure_cap"])
            max_dd     = float(thresholds["max_drawdown_threshold"])
            vol_trig   = float(thresholds["vol_compression_trigger"])
        except (KeyError, ValueError) as exc:
            raise RuntimeError(
                f"INTEGRITY_FAILURE: Missing or invalid threshold key in manifest: {exc}"
            ) from exc

        # MVI-04: Verify the three extracted constants equal FAS v6.1.0 values.
        if not self._floats_equal(shock_cap, None):
            raise RuntimeError(
                f"MANIFEST_CONSTANT_MISMATCH: shock_exposure_cap={shock_cap} "
                f"expected {self._EXPECTED_SHOCK_EXPOSURE_CAP}."
            )
        if not self._floats_equal(max_dd, self._EXPECTED_MAX_DRAWDOWN_THRESHOLD):
            raise RuntimeError(
                f"MANIFEST_CONSTANT_MISMATCH: max_drawdown_threshold={max_dd} "
                f"expected {self._EXPECTED_MAX_DRAWDOWN_THRESHOLD}."
            )
        if not self._floats_equal(vol_trig, self._EXPECTED_VOL_COMPRESSION_TRIGGER):
            raise RuntimeError(
                f"MANIFEST_CONSTANT_MISMATCH: vol_compression_trigger={vol_trig} "
                f"expected {self._EXPECTED_VOL_COMPRESSION_TRIGGER}."
            )

        # MVI-06: Return computed hash for propagation into ExecutionRecords.
        return computed_hash, thresholds

    def xǁManifestValidatorǁvalidate__mutmut_94(self) -> Tuple[str, Dict[str, Any]]:
        """
        Execute full manifest validation.

        Returns:
          (computed_hash, thresholds_dict)
          computed_hash -- SHA-256 hex digest of the manifest content.
          thresholds    -- dict from manifest["thresholds"] section.

        Raises RuntimeError with failure_type_id prefix on any hard failure.
        Failure types raised here:
          MANIFEST_HASH_MISMATCH    -- MVI-02
          MANIFEST_CONSTANT_MISMATCH -- MVI-04
          MANIFEST_TABLEHASH_PRESENT -- MVI-05
          INTEGRITY_FAILURE          -- missing file or parse error
        """
        # MVI-01: Load manifest file.
        if not self.manifest_path.exists():
            raise RuntimeError(
                "INTEGRITY_FAILURE: THRESHOLD_MANIFEST.json not found at "
                f"{self.manifest_path}. Harness cannot start without manifest."
            )

        try:
            with open(self.manifest_path, "r", encoding="utf-8") as f:
                raw = f.read()
            data = json.loads(raw)
        except Exception as exc:
            raise RuntimeError(
                f"INTEGRITY_FAILURE: Failed to load or parse THRESHOLD_MANIFEST.json: {exc}"
            ) from exc

        # MVI-01: Compute hash excluding manifest_hash field.
        data_for_hash = {k: v for k, v in data.items() if k != "manifest_hash"}
        computed_hash = hashlib.sha256(
            json.dumps(data_for_hash, sort_keys=True, separators=(",", ":")).encode("utf-8")
        ).hexdigest()

        # MVI-02: Verify computed hash matches stored manifest_hash.
        stored_hash = data.get("manifest_hash", "")
        if (
            stored_hash
            and stored_hash != "BUILD_TIME_PLACEHOLDER"
            and stored_hash != computed_hash
        ):
            raise RuntimeError(
                f"MANIFEST_HASH_MISMATCH: Computed hash {computed_hash[:16]}... "
                f"does not match stored hash {stored_hash[:16]}... "
                "System start denied. Possible tampering."
            )

        # MVI-05: Check for absence of table_hash in joint_risk_multiplier_table.
        jrmt = data.get("joint_risk_multiplier_table", {})
        if "table_hash" in jrmt:
            raise RuntimeError(
                "MANIFEST_TABLEHASH_PRESENT: joint_risk_multiplier_table must not "
                "contain a table_hash key per Manifest Authority Policy."
            )

        # MVI-03: Extract the three FAS v6.1.0 constants.
        try:
            thresholds = data["thresholds"]
            shock_cap  = float(thresholds["shock_exposure_cap"])
            max_dd     = float(thresholds["max_drawdown_threshold"])
            vol_trig   = float(thresholds["vol_compression_trigger"])
        except (KeyError, ValueError) as exc:
            raise RuntimeError(
                f"INTEGRITY_FAILURE: Missing or invalid threshold key in manifest: {exc}"
            ) from exc

        # MVI-04: Verify the three extracted constants equal FAS v6.1.0 values.
        if not self._floats_equal(self._EXPECTED_SHOCK_EXPOSURE_CAP):
            raise RuntimeError(
                f"MANIFEST_CONSTANT_MISMATCH: shock_exposure_cap={shock_cap} "
                f"expected {self._EXPECTED_SHOCK_EXPOSURE_CAP}."
            )
        if not self._floats_equal(max_dd, self._EXPECTED_MAX_DRAWDOWN_THRESHOLD):
            raise RuntimeError(
                f"MANIFEST_CONSTANT_MISMATCH: max_drawdown_threshold={max_dd} "
                f"expected {self._EXPECTED_MAX_DRAWDOWN_THRESHOLD}."
            )
        if not self._floats_equal(vol_trig, self._EXPECTED_VOL_COMPRESSION_TRIGGER):
            raise RuntimeError(
                f"MANIFEST_CONSTANT_MISMATCH: vol_compression_trigger={vol_trig} "
                f"expected {self._EXPECTED_VOL_COMPRESSION_TRIGGER}."
            )

        # MVI-06: Return computed hash for propagation into ExecutionRecords.
        return computed_hash, thresholds

    def xǁManifestValidatorǁvalidate__mutmut_95(self) -> Tuple[str, Dict[str, Any]]:
        """
        Execute full manifest validation.

        Returns:
          (computed_hash, thresholds_dict)
          computed_hash -- SHA-256 hex digest of the manifest content.
          thresholds    -- dict from manifest["thresholds"] section.

        Raises RuntimeError with failure_type_id prefix on any hard failure.
        Failure types raised here:
          MANIFEST_HASH_MISMATCH    -- MVI-02
          MANIFEST_CONSTANT_MISMATCH -- MVI-04
          MANIFEST_TABLEHASH_PRESENT -- MVI-05
          INTEGRITY_FAILURE          -- missing file or parse error
        """
        # MVI-01: Load manifest file.
        if not self.manifest_path.exists():
            raise RuntimeError(
                "INTEGRITY_FAILURE: THRESHOLD_MANIFEST.json not found at "
                f"{self.manifest_path}. Harness cannot start without manifest."
            )

        try:
            with open(self.manifest_path, "r", encoding="utf-8") as f:
                raw = f.read()
            data = json.loads(raw)
        except Exception as exc:
            raise RuntimeError(
                f"INTEGRITY_FAILURE: Failed to load or parse THRESHOLD_MANIFEST.json: {exc}"
            ) from exc

        # MVI-01: Compute hash excluding manifest_hash field.
        data_for_hash = {k: v for k, v in data.items() if k != "manifest_hash"}
        computed_hash = hashlib.sha256(
            json.dumps(data_for_hash, sort_keys=True, separators=(",", ":")).encode("utf-8")
        ).hexdigest()

        # MVI-02: Verify computed hash matches stored manifest_hash.
        stored_hash = data.get("manifest_hash", "")
        if (
            stored_hash
            and stored_hash != "BUILD_TIME_PLACEHOLDER"
            and stored_hash != computed_hash
        ):
            raise RuntimeError(
                f"MANIFEST_HASH_MISMATCH: Computed hash {computed_hash[:16]}... "
                f"does not match stored hash {stored_hash[:16]}... "
                "System start denied. Possible tampering."
            )

        # MVI-05: Check for absence of table_hash in joint_risk_multiplier_table.
        jrmt = data.get("joint_risk_multiplier_table", {})
        if "table_hash" in jrmt:
            raise RuntimeError(
                "MANIFEST_TABLEHASH_PRESENT: joint_risk_multiplier_table must not "
                "contain a table_hash key per Manifest Authority Policy."
            )

        # MVI-03: Extract the three FAS v6.1.0 constants.
        try:
            thresholds = data["thresholds"]
            shock_cap  = float(thresholds["shock_exposure_cap"])
            max_dd     = float(thresholds["max_drawdown_threshold"])
            vol_trig   = float(thresholds["vol_compression_trigger"])
        except (KeyError, ValueError) as exc:
            raise RuntimeError(
                f"INTEGRITY_FAILURE: Missing or invalid threshold key in manifest: {exc}"
            ) from exc

        # MVI-04: Verify the three extracted constants equal FAS v6.1.0 values.
        if not self._floats_equal(shock_cap, ):
            raise RuntimeError(
                f"MANIFEST_CONSTANT_MISMATCH: shock_exposure_cap={shock_cap} "
                f"expected {self._EXPECTED_SHOCK_EXPOSURE_CAP}."
            )
        if not self._floats_equal(max_dd, self._EXPECTED_MAX_DRAWDOWN_THRESHOLD):
            raise RuntimeError(
                f"MANIFEST_CONSTANT_MISMATCH: max_drawdown_threshold={max_dd} "
                f"expected {self._EXPECTED_MAX_DRAWDOWN_THRESHOLD}."
            )
        if not self._floats_equal(vol_trig, self._EXPECTED_VOL_COMPRESSION_TRIGGER):
            raise RuntimeError(
                f"MANIFEST_CONSTANT_MISMATCH: vol_compression_trigger={vol_trig} "
                f"expected {self._EXPECTED_VOL_COMPRESSION_TRIGGER}."
            )

        # MVI-06: Return computed hash for propagation into ExecutionRecords.
        return computed_hash, thresholds

    def xǁManifestValidatorǁvalidate__mutmut_96(self) -> Tuple[str, Dict[str, Any]]:
        """
        Execute full manifest validation.

        Returns:
          (computed_hash, thresholds_dict)
          computed_hash -- SHA-256 hex digest of the manifest content.
          thresholds    -- dict from manifest["thresholds"] section.

        Raises RuntimeError with failure_type_id prefix on any hard failure.
        Failure types raised here:
          MANIFEST_HASH_MISMATCH    -- MVI-02
          MANIFEST_CONSTANT_MISMATCH -- MVI-04
          MANIFEST_TABLEHASH_PRESENT -- MVI-05
          INTEGRITY_FAILURE          -- missing file or parse error
        """
        # MVI-01: Load manifest file.
        if not self.manifest_path.exists():
            raise RuntimeError(
                "INTEGRITY_FAILURE: THRESHOLD_MANIFEST.json not found at "
                f"{self.manifest_path}. Harness cannot start without manifest."
            )

        try:
            with open(self.manifest_path, "r", encoding="utf-8") as f:
                raw = f.read()
            data = json.loads(raw)
        except Exception as exc:
            raise RuntimeError(
                f"INTEGRITY_FAILURE: Failed to load or parse THRESHOLD_MANIFEST.json: {exc}"
            ) from exc

        # MVI-01: Compute hash excluding manifest_hash field.
        data_for_hash = {k: v for k, v in data.items() if k != "manifest_hash"}
        computed_hash = hashlib.sha256(
            json.dumps(data_for_hash, sort_keys=True, separators=(",", ":")).encode("utf-8")
        ).hexdigest()

        # MVI-02: Verify computed hash matches stored manifest_hash.
        stored_hash = data.get("manifest_hash", "")
        if (
            stored_hash
            and stored_hash != "BUILD_TIME_PLACEHOLDER"
            and stored_hash != computed_hash
        ):
            raise RuntimeError(
                f"MANIFEST_HASH_MISMATCH: Computed hash {computed_hash[:16]}... "
                f"does not match stored hash {stored_hash[:16]}... "
                "System start denied. Possible tampering."
            )

        # MVI-05: Check for absence of table_hash in joint_risk_multiplier_table.
        jrmt = data.get("joint_risk_multiplier_table", {})
        if "table_hash" in jrmt:
            raise RuntimeError(
                "MANIFEST_TABLEHASH_PRESENT: joint_risk_multiplier_table must not "
                "contain a table_hash key per Manifest Authority Policy."
            )

        # MVI-03: Extract the three FAS v6.1.0 constants.
        try:
            thresholds = data["thresholds"]
            shock_cap  = float(thresholds["shock_exposure_cap"])
            max_dd     = float(thresholds["max_drawdown_threshold"])
            vol_trig   = float(thresholds["vol_compression_trigger"])
        except (KeyError, ValueError) as exc:
            raise RuntimeError(
                f"INTEGRITY_FAILURE: Missing or invalid threshold key in manifest: {exc}"
            ) from exc

        # MVI-04: Verify the three extracted constants equal FAS v6.1.0 values.
        if not self._floats_equal(shock_cap, self._EXPECTED_SHOCK_EXPOSURE_CAP):
            raise RuntimeError(
                None
            )
        if not self._floats_equal(max_dd, self._EXPECTED_MAX_DRAWDOWN_THRESHOLD):
            raise RuntimeError(
                f"MANIFEST_CONSTANT_MISMATCH: max_drawdown_threshold={max_dd} "
                f"expected {self._EXPECTED_MAX_DRAWDOWN_THRESHOLD}."
            )
        if not self._floats_equal(vol_trig, self._EXPECTED_VOL_COMPRESSION_TRIGGER):
            raise RuntimeError(
                f"MANIFEST_CONSTANT_MISMATCH: vol_compression_trigger={vol_trig} "
                f"expected {self._EXPECTED_VOL_COMPRESSION_TRIGGER}."
            )

        # MVI-06: Return computed hash for propagation into ExecutionRecords.
        return computed_hash, thresholds

    def xǁManifestValidatorǁvalidate__mutmut_97(self) -> Tuple[str, Dict[str, Any]]:
        """
        Execute full manifest validation.

        Returns:
          (computed_hash, thresholds_dict)
          computed_hash -- SHA-256 hex digest of the manifest content.
          thresholds    -- dict from manifest["thresholds"] section.

        Raises RuntimeError with failure_type_id prefix on any hard failure.
        Failure types raised here:
          MANIFEST_HASH_MISMATCH    -- MVI-02
          MANIFEST_CONSTANT_MISMATCH -- MVI-04
          MANIFEST_TABLEHASH_PRESENT -- MVI-05
          INTEGRITY_FAILURE          -- missing file or parse error
        """
        # MVI-01: Load manifest file.
        if not self.manifest_path.exists():
            raise RuntimeError(
                "INTEGRITY_FAILURE: THRESHOLD_MANIFEST.json not found at "
                f"{self.manifest_path}. Harness cannot start without manifest."
            )

        try:
            with open(self.manifest_path, "r", encoding="utf-8") as f:
                raw = f.read()
            data = json.loads(raw)
        except Exception as exc:
            raise RuntimeError(
                f"INTEGRITY_FAILURE: Failed to load or parse THRESHOLD_MANIFEST.json: {exc}"
            ) from exc

        # MVI-01: Compute hash excluding manifest_hash field.
        data_for_hash = {k: v for k, v in data.items() if k != "manifest_hash"}
        computed_hash = hashlib.sha256(
            json.dumps(data_for_hash, sort_keys=True, separators=(",", ":")).encode("utf-8")
        ).hexdigest()

        # MVI-02: Verify computed hash matches stored manifest_hash.
        stored_hash = data.get("manifest_hash", "")
        if (
            stored_hash
            and stored_hash != "BUILD_TIME_PLACEHOLDER"
            and stored_hash != computed_hash
        ):
            raise RuntimeError(
                f"MANIFEST_HASH_MISMATCH: Computed hash {computed_hash[:16]}... "
                f"does not match stored hash {stored_hash[:16]}... "
                "System start denied. Possible tampering."
            )

        # MVI-05: Check for absence of table_hash in joint_risk_multiplier_table.
        jrmt = data.get("joint_risk_multiplier_table", {})
        if "table_hash" in jrmt:
            raise RuntimeError(
                "MANIFEST_TABLEHASH_PRESENT: joint_risk_multiplier_table must not "
                "contain a table_hash key per Manifest Authority Policy."
            )

        # MVI-03: Extract the three FAS v6.1.0 constants.
        try:
            thresholds = data["thresholds"]
            shock_cap  = float(thresholds["shock_exposure_cap"])
            max_dd     = float(thresholds["max_drawdown_threshold"])
            vol_trig   = float(thresholds["vol_compression_trigger"])
        except (KeyError, ValueError) as exc:
            raise RuntimeError(
                f"INTEGRITY_FAILURE: Missing or invalid threshold key in manifest: {exc}"
            ) from exc

        # MVI-04: Verify the three extracted constants equal FAS v6.1.0 values.
        if not self._floats_equal(shock_cap, self._EXPECTED_SHOCK_EXPOSURE_CAP):
            raise RuntimeError(
                f"MANIFEST_CONSTANT_MISMATCH: shock_exposure_cap={shock_cap} "
                f"expected {self._EXPECTED_SHOCK_EXPOSURE_CAP}."
            )
        if self._floats_equal(max_dd, self._EXPECTED_MAX_DRAWDOWN_THRESHOLD):
            raise RuntimeError(
                f"MANIFEST_CONSTANT_MISMATCH: max_drawdown_threshold={max_dd} "
                f"expected {self._EXPECTED_MAX_DRAWDOWN_THRESHOLD}."
            )
        if not self._floats_equal(vol_trig, self._EXPECTED_VOL_COMPRESSION_TRIGGER):
            raise RuntimeError(
                f"MANIFEST_CONSTANT_MISMATCH: vol_compression_trigger={vol_trig} "
                f"expected {self._EXPECTED_VOL_COMPRESSION_TRIGGER}."
            )

        # MVI-06: Return computed hash for propagation into ExecutionRecords.
        return computed_hash, thresholds

    def xǁManifestValidatorǁvalidate__mutmut_98(self) -> Tuple[str, Dict[str, Any]]:
        """
        Execute full manifest validation.

        Returns:
          (computed_hash, thresholds_dict)
          computed_hash -- SHA-256 hex digest of the manifest content.
          thresholds    -- dict from manifest["thresholds"] section.

        Raises RuntimeError with failure_type_id prefix on any hard failure.
        Failure types raised here:
          MANIFEST_HASH_MISMATCH    -- MVI-02
          MANIFEST_CONSTANT_MISMATCH -- MVI-04
          MANIFEST_TABLEHASH_PRESENT -- MVI-05
          INTEGRITY_FAILURE          -- missing file or parse error
        """
        # MVI-01: Load manifest file.
        if not self.manifest_path.exists():
            raise RuntimeError(
                "INTEGRITY_FAILURE: THRESHOLD_MANIFEST.json not found at "
                f"{self.manifest_path}. Harness cannot start without manifest."
            )

        try:
            with open(self.manifest_path, "r", encoding="utf-8") as f:
                raw = f.read()
            data = json.loads(raw)
        except Exception as exc:
            raise RuntimeError(
                f"INTEGRITY_FAILURE: Failed to load or parse THRESHOLD_MANIFEST.json: {exc}"
            ) from exc

        # MVI-01: Compute hash excluding manifest_hash field.
        data_for_hash = {k: v for k, v in data.items() if k != "manifest_hash"}
        computed_hash = hashlib.sha256(
            json.dumps(data_for_hash, sort_keys=True, separators=(",", ":")).encode("utf-8")
        ).hexdigest()

        # MVI-02: Verify computed hash matches stored manifest_hash.
        stored_hash = data.get("manifest_hash", "")
        if (
            stored_hash
            and stored_hash != "BUILD_TIME_PLACEHOLDER"
            and stored_hash != computed_hash
        ):
            raise RuntimeError(
                f"MANIFEST_HASH_MISMATCH: Computed hash {computed_hash[:16]}... "
                f"does not match stored hash {stored_hash[:16]}... "
                "System start denied. Possible tampering."
            )

        # MVI-05: Check for absence of table_hash in joint_risk_multiplier_table.
        jrmt = data.get("joint_risk_multiplier_table", {})
        if "table_hash" in jrmt:
            raise RuntimeError(
                "MANIFEST_TABLEHASH_PRESENT: joint_risk_multiplier_table must not "
                "contain a table_hash key per Manifest Authority Policy."
            )

        # MVI-03: Extract the three FAS v6.1.0 constants.
        try:
            thresholds = data["thresholds"]
            shock_cap  = float(thresholds["shock_exposure_cap"])
            max_dd     = float(thresholds["max_drawdown_threshold"])
            vol_trig   = float(thresholds["vol_compression_trigger"])
        except (KeyError, ValueError) as exc:
            raise RuntimeError(
                f"INTEGRITY_FAILURE: Missing or invalid threshold key in manifest: {exc}"
            ) from exc

        # MVI-04: Verify the three extracted constants equal FAS v6.1.0 values.
        if not self._floats_equal(shock_cap, self._EXPECTED_SHOCK_EXPOSURE_CAP):
            raise RuntimeError(
                f"MANIFEST_CONSTANT_MISMATCH: shock_exposure_cap={shock_cap} "
                f"expected {self._EXPECTED_SHOCK_EXPOSURE_CAP}."
            )
        if not self._floats_equal(None, self._EXPECTED_MAX_DRAWDOWN_THRESHOLD):
            raise RuntimeError(
                f"MANIFEST_CONSTANT_MISMATCH: max_drawdown_threshold={max_dd} "
                f"expected {self._EXPECTED_MAX_DRAWDOWN_THRESHOLD}."
            )
        if not self._floats_equal(vol_trig, self._EXPECTED_VOL_COMPRESSION_TRIGGER):
            raise RuntimeError(
                f"MANIFEST_CONSTANT_MISMATCH: vol_compression_trigger={vol_trig} "
                f"expected {self._EXPECTED_VOL_COMPRESSION_TRIGGER}."
            )

        # MVI-06: Return computed hash for propagation into ExecutionRecords.
        return computed_hash, thresholds

    def xǁManifestValidatorǁvalidate__mutmut_99(self) -> Tuple[str, Dict[str, Any]]:
        """
        Execute full manifest validation.

        Returns:
          (computed_hash, thresholds_dict)
          computed_hash -- SHA-256 hex digest of the manifest content.
          thresholds    -- dict from manifest["thresholds"] section.

        Raises RuntimeError with failure_type_id prefix on any hard failure.
        Failure types raised here:
          MANIFEST_HASH_MISMATCH    -- MVI-02
          MANIFEST_CONSTANT_MISMATCH -- MVI-04
          MANIFEST_TABLEHASH_PRESENT -- MVI-05
          INTEGRITY_FAILURE          -- missing file or parse error
        """
        # MVI-01: Load manifest file.
        if not self.manifest_path.exists():
            raise RuntimeError(
                "INTEGRITY_FAILURE: THRESHOLD_MANIFEST.json not found at "
                f"{self.manifest_path}. Harness cannot start without manifest."
            )

        try:
            with open(self.manifest_path, "r", encoding="utf-8") as f:
                raw = f.read()
            data = json.loads(raw)
        except Exception as exc:
            raise RuntimeError(
                f"INTEGRITY_FAILURE: Failed to load or parse THRESHOLD_MANIFEST.json: {exc}"
            ) from exc

        # MVI-01: Compute hash excluding manifest_hash field.
        data_for_hash = {k: v for k, v in data.items() if k != "manifest_hash"}
        computed_hash = hashlib.sha256(
            json.dumps(data_for_hash, sort_keys=True, separators=(",", ":")).encode("utf-8")
        ).hexdigest()

        # MVI-02: Verify computed hash matches stored manifest_hash.
        stored_hash = data.get("manifest_hash", "")
        if (
            stored_hash
            and stored_hash != "BUILD_TIME_PLACEHOLDER"
            and stored_hash != computed_hash
        ):
            raise RuntimeError(
                f"MANIFEST_HASH_MISMATCH: Computed hash {computed_hash[:16]}... "
                f"does not match stored hash {stored_hash[:16]}... "
                "System start denied. Possible tampering."
            )

        # MVI-05: Check for absence of table_hash in joint_risk_multiplier_table.
        jrmt = data.get("joint_risk_multiplier_table", {})
        if "table_hash" in jrmt:
            raise RuntimeError(
                "MANIFEST_TABLEHASH_PRESENT: joint_risk_multiplier_table must not "
                "contain a table_hash key per Manifest Authority Policy."
            )

        # MVI-03: Extract the three FAS v6.1.0 constants.
        try:
            thresholds = data["thresholds"]
            shock_cap  = float(thresholds["shock_exposure_cap"])
            max_dd     = float(thresholds["max_drawdown_threshold"])
            vol_trig   = float(thresholds["vol_compression_trigger"])
        except (KeyError, ValueError) as exc:
            raise RuntimeError(
                f"INTEGRITY_FAILURE: Missing or invalid threshold key in manifest: {exc}"
            ) from exc

        # MVI-04: Verify the three extracted constants equal FAS v6.1.0 values.
        if not self._floats_equal(shock_cap, self._EXPECTED_SHOCK_EXPOSURE_CAP):
            raise RuntimeError(
                f"MANIFEST_CONSTANT_MISMATCH: shock_exposure_cap={shock_cap} "
                f"expected {self._EXPECTED_SHOCK_EXPOSURE_CAP}."
            )
        if not self._floats_equal(max_dd, None):
            raise RuntimeError(
                f"MANIFEST_CONSTANT_MISMATCH: max_drawdown_threshold={max_dd} "
                f"expected {self._EXPECTED_MAX_DRAWDOWN_THRESHOLD}."
            )
        if not self._floats_equal(vol_trig, self._EXPECTED_VOL_COMPRESSION_TRIGGER):
            raise RuntimeError(
                f"MANIFEST_CONSTANT_MISMATCH: vol_compression_trigger={vol_trig} "
                f"expected {self._EXPECTED_VOL_COMPRESSION_TRIGGER}."
            )

        # MVI-06: Return computed hash for propagation into ExecutionRecords.
        return computed_hash, thresholds

    def xǁManifestValidatorǁvalidate__mutmut_100(self) -> Tuple[str, Dict[str, Any]]:
        """
        Execute full manifest validation.

        Returns:
          (computed_hash, thresholds_dict)
          computed_hash -- SHA-256 hex digest of the manifest content.
          thresholds    -- dict from manifest["thresholds"] section.

        Raises RuntimeError with failure_type_id prefix on any hard failure.
        Failure types raised here:
          MANIFEST_HASH_MISMATCH    -- MVI-02
          MANIFEST_CONSTANT_MISMATCH -- MVI-04
          MANIFEST_TABLEHASH_PRESENT -- MVI-05
          INTEGRITY_FAILURE          -- missing file or parse error
        """
        # MVI-01: Load manifest file.
        if not self.manifest_path.exists():
            raise RuntimeError(
                "INTEGRITY_FAILURE: THRESHOLD_MANIFEST.json not found at "
                f"{self.manifest_path}. Harness cannot start without manifest."
            )

        try:
            with open(self.manifest_path, "r", encoding="utf-8") as f:
                raw = f.read()
            data = json.loads(raw)
        except Exception as exc:
            raise RuntimeError(
                f"INTEGRITY_FAILURE: Failed to load or parse THRESHOLD_MANIFEST.json: {exc}"
            ) from exc

        # MVI-01: Compute hash excluding manifest_hash field.
        data_for_hash = {k: v for k, v in data.items() if k != "manifest_hash"}
        computed_hash = hashlib.sha256(
            json.dumps(data_for_hash, sort_keys=True, separators=(",", ":")).encode("utf-8")
        ).hexdigest()

        # MVI-02: Verify computed hash matches stored manifest_hash.
        stored_hash = data.get("manifest_hash", "")
        if (
            stored_hash
            and stored_hash != "BUILD_TIME_PLACEHOLDER"
            and stored_hash != computed_hash
        ):
            raise RuntimeError(
                f"MANIFEST_HASH_MISMATCH: Computed hash {computed_hash[:16]}... "
                f"does not match stored hash {stored_hash[:16]}... "
                "System start denied. Possible tampering."
            )

        # MVI-05: Check for absence of table_hash in joint_risk_multiplier_table.
        jrmt = data.get("joint_risk_multiplier_table", {})
        if "table_hash" in jrmt:
            raise RuntimeError(
                "MANIFEST_TABLEHASH_PRESENT: joint_risk_multiplier_table must not "
                "contain a table_hash key per Manifest Authority Policy."
            )

        # MVI-03: Extract the three FAS v6.1.0 constants.
        try:
            thresholds = data["thresholds"]
            shock_cap  = float(thresholds["shock_exposure_cap"])
            max_dd     = float(thresholds["max_drawdown_threshold"])
            vol_trig   = float(thresholds["vol_compression_trigger"])
        except (KeyError, ValueError) as exc:
            raise RuntimeError(
                f"INTEGRITY_FAILURE: Missing or invalid threshold key in manifest: {exc}"
            ) from exc

        # MVI-04: Verify the three extracted constants equal FAS v6.1.0 values.
        if not self._floats_equal(shock_cap, self._EXPECTED_SHOCK_EXPOSURE_CAP):
            raise RuntimeError(
                f"MANIFEST_CONSTANT_MISMATCH: shock_exposure_cap={shock_cap} "
                f"expected {self._EXPECTED_SHOCK_EXPOSURE_CAP}."
            )
        if not self._floats_equal(self._EXPECTED_MAX_DRAWDOWN_THRESHOLD):
            raise RuntimeError(
                f"MANIFEST_CONSTANT_MISMATCH: max_drawdown_threshold={max_dd} "
                f"expected {self._EXPECTED_MAX_DRAWDOWN_THRESHOLD}."
            )
        if not self._floats_equal(vol_trig, self._EXPECTED_VOL_COMPRESSION_TRIGGER):
            raise RuntimeError(
                f"MANIFEST_CONSTANT_MISMATCH: vol_compression_trigger={vol_trig} "
                f"expected {self._EXPECTED_VOL_COMPRESSION_TRIGGER}."
            )

        # MVI-06: Return computed hash for propagation into ExecutionRecords.
        return computed_hash, thresholds

    def xǁManifestValidatorǁvalidate__mutmut_101(self) -> Tuple[str, Dict[str, Any]]:
        """
        Execute full manifest validation.

        Returns:
          (computed_hash, thresholds_dict)
          computed_hash -- SHA-256 hex digest of the manifest content.
          thresholds    -- dict from manifest["thresholds"] section.

        Raises RuntimeError with failure_type_id prefix on any hard failure.
        Failure types raised here:
          MANIFEST_HASH_MISMATCH    -- MVI-02
          MANIFEST_CONSTANT_MISMATCH -- MVI-04
          MANIFEST_TABLEHASH_PRESENT -- MVI-05
          INTEGRITY_FAILURE          -- missing file or parse error
        """
        # MVI-01: Load manifest file.
        if not self.manifest_path.exists():
            raise RuntimeError(
                "INTEGRITY_FAILURE: THRESHOLD_MANIFEST.json not found at "
                f"{self.manifest_path}. Harness cannot start without manifest."
            )

        try:
            with open(self.manifest_path, "r", encoding="utf-8") as f:
                raw = f.read()
            data = json.loads(raw)
        except Exception as exc:
            raise RuntimeError(
                f"INTEGRITY_FAILURE: Failed to load or parse THRESHOLD_MANIFEST.json: {exc}"
            ) from exc

        # MVI-01: Compute hash excluding manifest_hash field.
        data_for_hash = {k: v for k, v in data.items() if k != "manifest_hash"}
        computed_hash = hashlib.sha256(
            json.dumps(data_for_hash, sort_keys=True, separators=(",", ":")).encode("utf-8")
        ).hexdigest()

        # MVI-02: Verify computed hash matches stored manifest_hash.
        stored_hash = data.get("manifest_hash", "")
        if (
            stored_hash
            and stored_hash != "BUILD_TIME_PLACEHOLDER"
            and stored_hash != computed_hash
        ):
            raise RuntimeError(
                f"MANIFEST_HASH_MISMATCH: Computed hash {computed_hash[:16]}... "
                f"does not match stored hash {stored_hash[:16]}... "
                "System start denied. Possible tampering."
            )

        # MVI-05: Check for absence of table_hash in joint_risk_multiplier_table.
        jrmt = data.get("joint_risk_multiplier_table", {})
        if "table_hash" in jrmt:
            raise RuntimeError(
                "MANIFEST_TABLEHASH_PRESENT: joint_risk_multiplier_table must not "
                "contain a table_hash key per Manifest Authority Policy."
            )

        # MVI-03: Extract the three FAS v6.1.0 constants.
        try:
            thresholds = data["thresholds"]
            shock_cap  = float(thresholds["shock_exposure_cap"])
            max_dd     = float(thresholds["max_drawdown_threshold"])
            vol_trig   = float(thresholds["vol_compression_trigger"])
        except (KeyError, ValueError) as exc:
            raise RuntimeError(
                f"INTEGRITY_FAILURE: Missing or invalid threshold key in manifest: {exc}"
            ) from exc

        # MVI-04: Verify the three extracted constants equal FAS v6.1.0 values.
        if not self._floats_equal(shock_cap, self._EXPECTED_SHOCK_EXPOSURE_CAP):
            raise RuntimeError(
                f"MANIFEST_CONSTANT_MISMATCH: shock_exposure_cap={shock_cap} "
                f"expected {self._EXPECTED_SHOCK_EXPOSURE_CAP}."
            )
        if not self._floats_equal(max_dd, ):
            raise RuntimeError(
                f"MANIFEST_CONSTANT_MISMATCH: max_drawdown_threshold={max_dd} "
                f"expected {self._EXPECTED_MAX_DRAWDOWN_THRESHOLD}."
            )
        if not self._floats_equal(vol_trig, self._EXPECTED_VOL_COMPRESSION_TRIGGER):
            raise RuntimeError(
                f"MANIFEST_CONSTANT_MISMATCH: vol_compression_trigger={vol_trig} "
                f"expected {self._EXPECTED_VOL_COMPRESSION_TRIGGER}."
            )

        # MVI-06: Return computed hash for propagation into ExecutionRecords.
        return computed_hash, thresholds

    def xǁManifestValidatorǁvalidate__mutmut_102(self) -> Tuple[str, Dict[str, Any]]:
        """
        Execute full manifest validation.

        Returns:
          (computed_hash, thresholds_dict)
          computed_hash -- SHA-256 hex digest of the manifest content.
          thresholds    -- dict from manifest["thresholds"] section.

        Raises RuntimeError with failure_type_id prefix on any hard failure.
        Failure types raised here:
          MANIFEST_HASH_MISMATCH    -- MVI-02
          MANIFEST_CONSTANT_MISMATCH -- MVI-04
          MANIFEST_TABLEHASH_PRESENT -- MVI-05
          INTEGRITY_FAILURE          -- missing file or parse error
        """
        # MVI-01: Load manifest file.
        if not self.manifest_path.exists():
            raise RuntimeError(
                "INTEGRITY_FAILURE: THRESHOLD_MANIFEST.json not found at "
                f"{self.manifest_path}. Harness cannot start without manifest."
            )

        try:
            with open(self.manifest_path, "r", encoding="utf-8") as f:
                raw = f.read()
            data = json.loads(raw)
        except Exception as exc:
            raise RuntimeError(
                f"INTEGRITY_FAILURE: Failed to load or parse THRESHOLD_MANIFEST.json: {exc}"
            ) from exc

        # MVI-01: Compute hash excluding manifest_hash field.
        data_for_hash = {k: v for k, v in data.items() if k != "manifest_hash"}
        computed_hash = hashlib.sha256(
            json.dumps(data_for_hash, sort_keys=True, separators=(",", ":")).encode("utf-8")
        ).hexdigest()

        # MVI-02: Verify computed hash matches stored manifest_hash.
        stored_hash = data.get("manifest_hash", "")
        if (
            stored_hash
            and stored_hash != "BUILD_TIME_PLACEHOLDER"
            and stored_hash != computed_hash
        ):
            raise RuntimeError(
                f"MANIFEST_HASH_MISMATCH: Computed hash {computed_hash[:16]}... "
                f"does not match stored hash {stored_hash[:16]}... "
                "System start denied. Possible tampering."
            )

        # MVI-05: Check for absence of table_hash in joint_risk_multiplier_table.
        jrmt = data.get("joint_risk_multiplier_table", {})
        if "table_hash" in jrmt:
            raise RuntimeError(
                "MANIFEST_TABLEHASH_PRESENT: joint_risk_multiplier_table must not "
                "contain a table_hash key per Manifest Authority Policy."
            )

        # MVI-03: Extract the three FAS v6.1.0 constants.
        try:
            thresholds = data["thresholds"]
            shock_cap  = float(thresholds["shock_exposure_cap"])
            max_dd     = float(thresholds["max_drawdown_threshold"])
            vol_trig   = float(thresholds["vol_compression_trigger"])
        except (KeyError, ValueError) as exc:
            raise RuntimeError(
                f"INTEGRITY_FAILURE: Missing or invalid threshold key in manifest: {exc}"
            ) from exc

        # MVI-04: Verify the three extracted constants equal FAS v6.1.0 values.
        if not self._floats_equal(shock_cap, self._EXPECTED_SHOCK_EXPOSURE_CAP):
            raise RuntimeError(
                f"MANIFEST_CONSTANT_MISMATCH: shock_exposure_cap={shock_cap} "
                f"expected {self._EXPECTED_SHOCK_EXPOSURE_CAP}."
            )
        if not self._floats_equal(max_dd, self._EXPECTED_MAX_DRAWDOWN_THRESHOLD):
            raise RuntimeError(
                None
            )
        if not self._floats_equal(vol_trig, self._EXPECTED_VOL_COMPRESSION_TRIGGER):
            raise RuntimeError(
                f"MANIFEST_CONSTANT_MISMATCH: vol_compression_trigger={vol_trig} "
                f"expected {self._EXPECTED_VOL_COMPRESSION_TRIGGER}."
            )

        # MVI-06: Return computed hash for propagation into ExecutionRecords.
        return computed_hash, thresholds

    def xǁManifestValidatorǁvalidate__mutmut_103(self) -> Tuple[str, Dict[str, Any]]:
        """
        Execute full manifest validation.

        Returns:
          (computed_hash, thresholds_dict)
          computed_hash -- SHA-256 hex digest of the manifest content.
          thresholds    -- dict from manifest["thresholds"] section.

        Raises RuntimeError with failure_type_id prefix on any hard failure.
        Failure types raised here:
          MANIFEST_HASH_MISMATCH    -- MVI-02
          MANIFEST_CONSTANT_MISMATCH -- MVI-04
          MANIFEST_TABLEHASH_PRESENT -- MVI-05
          INTEGRITY_FAILURE          -- missing file or parse error
        """
        # MVI-01: Load manifest file.
        if not self.manifest_path.exists():
            raise RuntimeError(
                "INTEGRITY_FAILURE: THRESHOLD_MANIFEST.json not found at "
                f"{self.manifest_path}. Harness cannot start without manifest."
            )

        try:
            with open(self.manifest_path, "r", encoding="utf-8") as f:
                raw = f.read()
            data = json.loads(raw)
        except Exception as exc:
            raise RuntimeError(
                f"INTEGRITY_FAILURE: Failed to load or parse THRESHOLD_MANIFEST.json: {exc}"
            ) from exc

        # MVI-01: Compute hash excluding manifest_hash field.
        data_for_hash = {k: v for k, v in data.items() if k != "manifest_hash"}
        computed_hash = hashlib.sha256(
            json.dumps(data_for_hash, sort_keys=True, separators=(",", ":")).encode("utf-8")
        ).hexdigest()

        # MVI-02: Verify computed hash matches stored manifest_hash.
        stored_hash = data.get("manifest_hash", "")
        if (
            stored_hash
            and stored_hash != "BUILD_TIME_PLACEHOLDER"
            and stored_hash != computed_hash
        ):
            raise RuntimeError(
                f"MANIFEST_HASH_MISMATCH: Computed hash {computed_hash[:16]}... "
                f"does not match stored hash {stored_hash[:16]}... "
                "System start denied. Possible tampering."
            )

        # MVI-05: Check for absence of table_hash in joint_risk_multiplier_table.
        jrmt = data.get("joint_risk_multiplier_table", {})
        if "table_hash" in jrmt:
            raise RuntimeError(
                "MANIFEST_TABLEHASH_PRESENT: joint_risk_multiplier_table must not "
                "contain a table_hash key per Manifest Authority Policy."
            )

        # MVI-03: Extract the three FAS v6.1.0 constants.
        try:
            thresholds = data["thresholds"]
            shock_cap  = float(thresholds["shock_exposure_cap"])
            max_dd     = float(thresholds["max_drawdown_threshold"])
            vol_trig   = float(thresholds["vol_compression_trigger"])
        except (KeyError, ValueError) as exc:
            raise RuntimeError(
                f"INTEGRITY_FAILURE: Missing or invalid threshold key in manifest: {exc}"
            ) from exc

        # MVI-04: Verify the three extracted constants equal FAS v6.1.0 values.
        if not self._floats_equal(shock_cap, self._EXPECTED_SHOCK_EXPOSURE_CAP):
            raise RuntimeError(
                f"MANIFEST_CONSTANT_MISMATCH: shock_exposure_cap={shock_cap} "
                f"expected {self._EXPECTED_SHOCK_EXPOSURE_CAP}."
            )
        if not self._floats_equal(max_dd, self._EXPECTED_MAX_DRAWDOWN_THRESHOLD):
            raise RuntimeError(
                f"MANIFEST_CONSTANT_MISMATCH: max_drawdown_threshold={max_dd} "
                f"expected {self._EXPECTED_MAX_DRAWDOWN_THRESHOLD}."
            )
        if self._floats_equal(vol_trig, self._EXPECTED_VOL_COMPRESSION_TRIGGER):
            raise RuntimeError(
                f"MANIFEST_CONSTANT_MISMATCH: vol_compression_trigger={vol_trig} "
                f"expected {self._EXPECTED_VOL_COMPRESSION_TRIGGER}."
            )

        # MVI-06: Return computed hash for propagation into ExecutionRecords.
        return computed_hash, thresholds

    def xǁManifestValidatorǁvalidate__mutmut_104(self) -> Tuple[str, Dict[str, Any]]:
        """
        Execute full manifest validation.

        Returns:
          (computed_hash, thresholds_dict)
          computed_hash -- SHA-256 hex digest of the manifest content.
          thresholds    -- dict from manifest["thresholds"] section.

        Raises RuntimeError with failure_type_id prefix on any hard failure.
        Failure types raised here:
          MANIFEST_HASH_MISMATCH    -- MVI-02
          MANIFEST_CONSTANT_MISMATCH -- MVI-04
          MANIFEST_TABLEHASH_PRESENT -- MVI-05
          INTEGRITY_FAILURE          -- missing file or parse error
        """
        # MVI-01: Load manifest file.
        if not self.manifest_path.exists():
            raise RuntimeError(
                "INTEGRITY_FAILURE: THRESHOLD_MANIFEST.json not found at "
                f"{self.manifest_path}. Harness cannot start without manifest."
            )

        try:
            with open(self.manifest_path, "r", encoding="utf-8") as f:
                raw = f.read()
            data = json.loads(raw)
        except Exception as exc:
            raise RuntimeError(
                f"INTEGRITY_FAILURE: Failed to load or parse THRESHOLD_MANIFEST.json: {exc}"
            ) from exc

        # MVI-01: Compute hash excluding manifest_hash field.
        data_for_hash = {k: v for k, v in data.items() if k != "manifest_hash"}
        computed_hash = hashlib.sha256(
            json.dumps(data_for_hash, sort_keys=True, separators=(",", ":")).encode("utf-8")
        ).hexdigest()

        # MVI-02: Verify computed hash matches stored manifest_hash.
        stored_hash = data.get("manifest_hash", "")
        if (
            stored_hash
            and stored_hash != "BUILD_TIME_PLACEHOLDER"
            and stored_hash != computed_hash
        ):
            raise RuntimeError(
                f"MANIFEST_HASH_MISMATCH: Computed hash {computed_hash[:16]}... "
                f"does not match stored hash {stored_hash[:16]}... "
                "System start denied. Possible tampering."
            )

        # MVI-05: Check for absence of table_hash in joint_risk_multiplier_table.
        jrmt = data.get("joint_risk_multiplier_table", {})
        if "table_hash" in jrmt:
            raise RuntimeError(
                "MANIFEST_TABLEHASH_PRESENT: joint_risk_multiplier_table must not "
                "contain a table_hash key per Manifest Authority Policy."
            )

        # MVI-03: Extract the three FAS v6.1.0 constants.
        try:
            thresholds = data["thresholds"]
            shock_cap  = float(thresholds["shock_exposure_cap"])
            max_dd     = float(thresholds["max_drawdown_threshold"])
            vol_trig   = float(thresholds["vol_compression_trigger"])
        except (KeyError, ValueError) as exc:
            raise RuntimeError(
                f"INTEGRITY_FAILURE: Missing or invalid threshold key in manifest: {exc}"
            ) from exc

        # MVI-04: Verify the three extracted constants equal FAS v6.1.0 values.
        if not self._floats_equal(shock_cap, self._EXPECTED_SHOCK_EXPOSURE_CAP):
            raise RuntimeError(
                f"MANIFEST_CONSTANT_MISMATCH: shock_exposure_cap={shock_cap} "
                f"expected {self._EXPECTED_SHOCK_EXPOSURE_CAP}."
            )
        if not self._floats_equal(max_dd, self._EXPECTED_MAX_DRAWDOWN_THRESHOLD):
            raise RuntimeError(
                f"MANIFEST_CONSTANT_MISMATCH: max_drawdown_threshold={max_dd} "
                f"expected {self._EXPECTED_MAX_DRAWDOWN_THRESHOLD}."
            )
        if not self._floats_equal(None, self._EXPECTED_VOL_COMPRESSION_TRIGGER):
            raise RuntimeError(
                f"MANIFEST_CONSTANT_MISMATCH: vol_compression_trigger={vol_trig} "
                f"expected {self._EXPECTED_VOL_COMPRESSION_TRIGGER}."
            )

        # MVI-06: Return computed hash for propagation into ExecutionRecords.
        return computed_hash, thresholds

    def xǁManifestValidatorǁvalidate__mutmut_105(self) -> Tuple[str, Dict[str, Any]]:
        """
        Execute full manifest validation.

        Returns:
          (computed_hash, thresholds_dict)
          computed_hash -- SHA-256 hex digest of the manifest content.
          thresholds    -- dict from manifest["thresholds"] section.

        Raises RuntimeError with failure_type_id prefix on any hard failure.
        Failure types raised here:
          MANIFEST_HASH_MISMATCH    -- MVI-02
          MANIFEST_CONSTANT_MISMATCH -- MVI-04
          MANIFEST_TABLEHASH_PRESENT -- MVI-05
          INTEGRITY_FAILURE          -- missing file or parse error
        """
        # MVI-01: Load manifest file.
        if not self.manifest_path.exists():
            raise RuntimeError(
                "INTEGRITY_FAILURE: THRESHOLD_MANIFEST.json not found at "
                f"{self.manifest_path}. Harness cannot start without manifest."
            )

        try:
            with open(self.manifest_path, "r", encoding="utf-8") as f:
                raw = f.read()
            data = json.loads(raw)
        except Exception as exc:
            raise RuntimeError(
                f"INTEGRITY_FAILURE: Failed to load or parse THRESHOLD_MANIFEST.json: {exc}"
            ) from exc

        # MVI-01: Compute hash excluding manifest_hash field.
        data_for_hash = {k: v for k, v in data.items() if k != "manifest_hash"}
        computed_hash = hashlib.sha256(
            json.dumps(data_for_hash, sort_keys=True, separators=(",", ":")).encode("utf-8")
        ).hexdigest()

        # MVI-02: Verify computed hash matches stored manifest_hash.
        stored_hash = data.get("manifest_hash", "")
        if (
            stored_hash
            and stored_hash != "BUILD_TIME_PLACEHOLDER"
            and stored_hash != computed_hash
        ):
            raise RuntimeError(
                f"MANIFEST_HASH_MISMATCH: Computed hash {computed_hash[:16]}... "
                f"does not match stored hash {stored_hash[:16]}... "
                "System start denied. Possible tampering."
            )

        # MVI-05: Check for absence of table_hash in joint_risk_multiplier_table.
        jrmt = data.get("joint_risk_multiplier_table", {})
        if "table_hash" in jrmt:
            raise RuntimeError(
                "MANIFEST_TABLEHASH_PRESENT: joint_risk_multiplier_table must not "
                "contain a table_hash key per Manifest Authority Policy."
            )

        # MVI-03: Extract the three FAS v6.1.0 constants.
        try:
            thresholds = data["thresholds"]
            shock_cap  = float(thresholds["shock_exposure_cap"])
            max_dd     = float(thresholds["max_drawdown_threshold"])
            vol_trig   = float(thresholds["vol_compression_trigger"])
        except (KeyError, ValueError) as exc:
            raise RuntimeError(
                f"INTEGRITY_FAILURE: Missing or invalid threshold key in manifest: {exc}"
            ) from exc

        # MVI-04: Verify the three extracted constants equal FAS v6.1.0 values.
        if not self._floats_equal(shock_cap, self._EXPECTED_SHOCK_EXPOSURE_CAP):
            raise RuntimeError(
                f"MANIFEST_CONSTANT_MISMATCH: shock_exposure_cap={shock_cap} "
                f"expected {self._EXPECTED_SHOCK_EXPOSURE_CAP}."
            )
        if not self._floats_equal(max_dd, self._EXPECTED_MAX_DRAWDOWN_THRESHOLD):
            raise RuntimeError(
                f"MANIFEST_CONSTANT_MISMATCH: max_drawdown_threshold={max_dd} "
                f"expected {self._EXPECTED_MAX_DRAWDOWN_THRESHOLD}."
            )
        if not self._floats_equal(vol_trig, None):
            raise RuntimeError(
                f"MANIFEST_CONSTANT_MISMATCH: vol_compression_trigger={vol_trig} "
                f"expected {self._EXPECTED_VOL_COMPRESSION_TRIGGER}."
            )

        # MVI-06: Return computed hash for propagation into ExecutionRecords.
        return computed_hash, thresholds

    def xǁManifestValidatorǁvalidate__mutmut_106(self) -> Tuple[str, Dict[str, Any]]:
        """
        Execute full manifest validation.

        Returns:
          (computed_hash, thresholds_dict)
          computed_hash -- SHA-256 hex digest of the manifest content.
          thresholds    -- dict from manifest["thresholds"] section.

        Raises RuntimeError with failure_type_id prefix on any hard failure.
        Failure types raised here:
          MANIFEST_HASH_MISMATCH    -- MVI-02
          MANIFEST_CONSTANT_MISMATCH -- MVI-04
          MANIFEST_TABLEHASH_PRESENT -- MVI-05
          INTEGRITY_FAILURE          -- missing file or parse error
        """
        # MVI-01: Load manifest file.
        if not self.manifest_path.exists():
            raise RuntimeError(
                "INTEGRITY_FAILURE: THRESHOLD_MANIFEST.json not found at "
                f"{self.manifest_path}. Harness cannot start without manifest."
            )

        try:
            with open(self.manifest_path, "r", encoding="utf-8") as f:
                raw = f.read()
            data = json.loads(raw)
        except Exception as exc:
            raise RuntimeError(
                f"INTEGRITY_FAILURE: Failed to load or parse THRESHOLD_MANIFEST.json: {exc}"
            ) from exc

        # MVI-01: Compute hash excluding manifest_hash field.
        data_for_hash = {k: v for k, v in data.items() if k != "manifest_hash"}
        computed_hash = hashlib.sha256(
            json.dumps(data_for_hash, sort_keys=True, separators=(",", ":")).encode("utf-8")
        ).hexdigest()

        # MVI-02: Verify computed hash matches stored manifest_hash.
        stored_hash = data.get("manifest_hash", "")
        if (
            stored_hash
            and stored_hash != "BUILD_TIME_PLACEHOLDER"
            and stored_hash != computed_hash
        ):
            raise RuntimeError(
                f"MANIFEST_HASH_MISMATCH: Computed hash {computed_hash[:16]}... "
                f"does not match stored hash {stored_hash[:16]}... "
                "System start denied. Possible tampering."
            )

        # MVI-05: Check for absence of table_hash in joint_risk_multiplier_table.
        jrmt = data.get("joint_risk_multiplier_table", {})
        if "table_hash" in jrmt:
            raise RuntimeError(
                "MANIFEST_TABLEHASH_PRESENT: joint_risk_multiplier_table must not "
                "contain a table_hash key per Manifest Authority Policy."
            )

        # MVI-03: Extract the three FAS v6.1.0 constants.
        try:
            thresholds = data["thresholds"]
            shock_cap  = float(thresholds["shock_exposure_cap"])
            max_dd     = float(thresholds["max_drawdown_threshold"])
            vol_trig   = float(thresholds["vol_compression_trigger"])
        except (KeyError, ValueError) as exc:
            raise RuntimeError(
                f"INTEGRITY_FAILURE: Missing or invalid threshold key in manifest: {exc}"
            ) from exc

        # MVI-04: Verify the three extracted constants equal FAS v6.1.0 values.
        if not self._floats_equal(shock_cap, self._EXPECTED_SHOCK_EXPOSURE_CAP):
            raise RuntimeError(
                f"MANIFEST_CONSTANT_MISMATCH: shock_exposure_cap={shock_cap} "
                f"expected {self._EXPECTED_SHOCK_EXPOSURE_CAP}."
            )
        if not self._floats_equal(max_dd, self._EXPECTED_MAX_DRAWDOWN_THRESHOLD):
            raise RuntimeError(
                f"MANIFEST_CONSTANT_MISMATCH: max_drawdown_threshold={max_dd} "
                f"expected {self._EXPECTED_MAX_DRAWDOWN_THRESHOLD}."
            )
        if not self._floats_equal(self._EXPECTED_VOL_COMPRESSION_TRIGGER):
            raise RuntimeError(
                f"MANIFEST_CONSTANT_MISMATCH: vol_compression_trigger={vol_trig} "
                f"expected {self._EXPECTED_VOL_COMPRESSION_TRIGGER}."
            )

        # MVI-06: Return computed hash for propagation into ExecutionRecords.
        return computed_hash, thresholds

    def xǁManifestValidatorǁvalidate__mutmut_107(self) -> Tuple[str, Dict[str, Any]]:
        """
        Execute full manifest validation.

        Returns:
          (computed_hash, thresholds_dict)
          computed_hash -- SHA-256 hex digest of the manifest content.
          thresholds    -- dict from manifest["thresholds"] section.

        Raises RuntimeError with failure_type_id prefix on any hard failure.
        Failure types raised here:
          MANIFEST_HASH_MISMATCH    -- MVI-02
          MANIFEST_CONSTANT_MISMATCH -- MVI-04
          MANIFEST_TABLEHASH_PRESENT -- MVI-05
          INTEGRITY_FAILURE          -- missing file or parse error
        """
        # MVI-01: Load manifest file.
        if not self.manifest_path.exists():
            raise RuntimeError(
                "INTEGRITY_FAILURE: THRESHOLD_MANIFEST.json not found at "
                f"{self.manifest_path}. Harness cannot start without manifest."
            )

        try:
            with open(self.manifest_path, "r", encoding="utf-8") as f:
                raw = f.read()
            data = json.loads(raw)
        except Exception as exc:
            raise RuntimeError(
                f"INTEGRITY_FAILURE: Failed to load or parse THRESHOLD_MANIFEST.json: {exc}"
            ) from exc

        # MVI-01: Compute hash excluding manifest_hash field.
        data_for_hash = {k: v for k, v in data.items() if k != "manifest_hash"}
        computed_hash = hashlib.sha256(
            json.dumps(data_for_hash, sort_keys=True, separators=(",", ":")).encode("utf-8")
        ).hexdigest()

        # MVI-02: Verify computed hash matches stored manifest_hash.
        stored_hash = data.get("manifest_hash", "")
        if (
            stored_hash
            and stored_hash != "BUILD_TIME_PLACEHOLDER"
            and stored_hash != computed_hash
        ):
            raise RuntimeError(
                f"MANIFEST_HASH_MISMATCH: Computed hash {computed_hash[:16]}... "
                f"does not match stored hash {stored_hash[:16]}... "
                "System start denied. Possible tampering."
            )

        # MVI-05: Check for absence of table_hash in joint_risk_multiplier_table.
        jrmt = data.get("joint_risk_multiplier_table", {})
        if "table_hash" in jrmt:
            raise RuntimeError(
                "MANIFEST_TABLEHASH_PRESENT: joint_risk_multiplier_table must not "
                "contain a table_hash key per Manifest Authority Policy."
            )

        # MVI-03: Extract the three FAS v6.1.0 constants.
        try:
            thresholds = data["thresholds"]
            shock_cap  = float(thresholds["shock_exposure_cap"])
            max_dd     = float(thresholds["max_drawdown_threshold"])
            vol_trig   = float(thresholds["vol_compression_trigger"])
        except (KeyError, ValueError) as exc:
            raise RuntimeError(
                f"INTEGRITY_FAILURE: Missing or invalid threshold key in manifest: {exc}"
            ) from exc

        # MVI-04: Verify the three extracted constants equal FAS v6.1.0 values.
        if not self._floats_equal(shock_cap, self._EXPECTED_SHOCK_EXPOSURE_CAP):
            raise RuntimeError(
                f"MANIFEST_CONSTANT_MISMATCH: shock_exposure_cap={shock_cap} "
                f"expected {self._EXPECTED_SHOCK_EXPOSURE_CAP}."
            )
        if not self._floats_equal(max_dd, self._EXPECTED_MAX_DRAWDOWN_THRESHOLD):
            raise RuntimeError(
                f"MANIFEST_CONSTANT_MISMATCH: max_drawdown_threshold={max_dd} "
                f"expected {self._EXPECTED_MAX_DRAWDOWN_THRESHOLD}."
            )
        if not self._floats_equal(vol_trig, ):
            raise RuntimeError(
                f"MANIFEST_CONSTANT_MISMATCH: vol_compression_trigger={vol_trig} "
                f"expected {self._EXPECTED_VOL_COMPRESSION_TRIGGER}."
            )

        # MVI-06: Return computed hash for propagation into ExecutionRecords.
        return computed_hash, thresholds

    def xǁManifestValidatorǁvalidate__mutmut_108(self) -> Tuple[str, Dict[str, Any]]:
        """
        Execute full manifest validation.

        Returns:
          (computed_hash, thresholds_dict)
          computed_hash -- SHA-256 hex digest of the manifest content.
          thresholds    -- dict from manifest["thresholds"] section.

        Raises RuntimeError with failure_type_id prefix on any hard failure.
        Failure types raised here:
          MANIFEST_HASH_MISMATCH    -- MVI-02
          MANIFEST_CONSTANT_MISMATCH -- MVI-04
          MANIFEST_TABLEHASH_PRESENT -- MVI-05
          INTEGRITY_FAILURE          -- missing file or parse error
        """
        # MVI-01: Load manifest file.
        if not self.manifest_path.exists():
            raise RuntimeError(
                "INTEGRITY_FAILURE: THRESHOLD_MANIFEST.json not found at "
                f"{self.manifest_path}. Harness cannot start without manifest."
            )

        try:
            with open(self.manifest_path, "r", encoding="utf-8") as f:
                raw = f.read()
            data = json.loads(raw)
        except Exception as exc:
            raise RuntimeError(
                f"INTEGRITY_FAILURE: Failed to load or parse THRESHOLD_MANIFEST.json: {exc}"
            ) from exc

        # MVI-01: Compute hash excluding manifest_hash field.
        data_for_hash = {k: v for k, v in data.items() if k != "manifest_hash"}
        computed_hash = hashlib.sha256(
            json.dumps(data_for_hash, sort_keys=True, separators=(",", ":")).encode("utf-8")
        ).hexdigest()

        # MVI-02: Verify computed hash matches stored manifest_hash.
        stored_hash = data.get("manifest_hash", "")
        if (
            stored_hash
            and stored_hash != "BUILD_TIME_PLACEHOLDER"
            and stored_hash != computed_hash
        ):
            raise RuntimeError(
                f"MANIFEST_HASH_MISMATCH: Computed hash {computed_hash[:16]}... "
                f"does not match stored hash {stored_hash[:16]}... "
                "System start denied. Possible tampering."
            )

        # MVI-05: Check for absence of table_hash in joint_risk_multiplier_table.
        jrmt = data.get("joint_risk_multiplier_table", {})
        if "table_hash" in jrmt:
            raise RuntimeError(
                "MANIFEST_TABLEHASH_PRESENT: joint_risk_multiplier_table must not "
                "contain a table_hash key per Manifest Authority Policy."
            )

        # MVI-03: Extract the three FAS v6.1.0 constants.
        try:
            thresholds = data["thresholds"]
            shock_cap  = float(thresholds["shock_exposure_cap"])
            max_dd     = float(thresholds["max_drawdown_threshold"])
            vol_trig   = float(thresholds["vol_compression_trigger"])
        except (KeyError, ValueError) as exc:
            raise RuntimeError(
                f"INTEGRITY_FAILURE: Missing or invalid threshold key in manifest: {exc}"
            ) from exc

        # MVI-04: Verify the three extracted constants equal FAS v6.1.0 values.
        if not self._floats_equal(shock_cap, self._EXPECTED_SHOCK_EXPOSURE_CAP):
            raise RuntimeError(
                f"MANIFEST_CONSTANT_MISMATCH: shock_exposure_cap={shock_cap} "
                f"expected {self._EXPECTED_SHOCK_EXPOSURE_CAP}."
            )
        if not self._floats_equal(max_dd, self._EXPECTED_MAX_DRAWDOWN_THRESHOLD):
            raise RuntimeError(
                f"MANIFEST_CONSTANT_MISMATCH: max_drawdown_threshold={max_dd} "
                f"expected {self._EXPECTED_MAX_DRAWDOWN_THRESHOLD}."
            )
        if not self._floats_equal(vol_trig, self._EXPECTED_VOL_COMPRESSION_TRIGGER):
            raise RuntimeError(
                None
            )

        # MVI-06: Return computed hash for propagation into ExecutionRecords.
        return computed_hash, thresholds
    
    xǁManifestValidatorǁvalidate__mutmut_mutants : ClassVar[MutantDict] = { # type: ignore
    'xǁManifestValidatorǁvalidate__mutmut_1': xǁManifestValidatorǁvalidate__mutmut_1, 
        'xǁManifestValidatorǁvalidate__mutmut_2': xǁManifestValidatorǁvalidate__mutmut_2, 
        'xǁManifestValidatorǁvalidate__mutmut_3': xǁManifestValidatorǁvalidate__mutmut_3, 
        'xǁManifestValidatorǁvalidate__mutmut_4': xǁManifestValidatorǁvalidate__mutmut_4, 
        'xǁManifestValidatorǁvalidate__mutmut_5': xǁManifestValidatorǁvalidate__mutmut_5, 
        'xǁManifestValidatorǁvalidate__mutmut_6': xǁManifestValidatorǁvalidate__mutmut_6, 
        'xǁManifestValidatorǁvalidate__mutmut_7': xǁManifestValidatorǁvalidate__mutmut_7, 
        'xǁManifestValidatorǁvalidate__mutmut_8': xǁManifestValidatorǁvalidate__mutmut_8, 
        'xǁManifestValidatorǁvalidate__mutmut_9': xǁManifestValidatorǁvalidate__mutmut_9, 
        'xǁManifestValidatorǁvalidate__mutmut_10': xǁManifestValidatorǁvalidate__mutmut_10, 
        'xǁManifestValidatorǁvalidate__mutmut_11': xǁManifestValidatorǁvalidate__mutmut_11, 
        'xǁManifestValidatorǁvalidate__mutmut_12': xǁManifestValidatorǁvalidate__mutmut_12, 
        'xǁManifestValidatorǁvalidate__mutmut_13': xǁManifestValidatorǁvalidate__mutmut_13, 
        'xǁManifestValidatorǁvalidate__mutmut_14': xǁManifestValidatorǁvalidate__mutmut_14, 
        'xǁManifestValidatorǁvalidate__mutmut_15': xǁManifestValidatorǁvalidate__mutmut_15, 
        'xǁManifestValidatorǁvalidate__mutmut_16': xǁManifestValidatorǁvalidate__mutmut_16, 
        'xǁManifestValidatorǁvalidate__mutmut_17': xǁManifestValidatorǁvalidate__mutmut_17, 
        'xǁManifestValidatorǁvalidate__mutmut_18': xǁManifestValidatorǁvalidate__mutmut_18, 
        'xǁManifestValidatorǁvalidate__mutmut_19': xǁManifestValidatorǁvalidate__mutmut_19, 
        'xǁManifestValidatorǁvalidate__mutmut_20': xǁManifestValidatorǁvalidate__mutmut_20, 
        'xǁManifestValidatorǁvalidate__mutmut_21': xǁManifestValidatorǁvalidate__mutmut_21, 
        'xǁManifestValidatorǁvalidate__mutmut_22': xǁManifestValidatorǁvalidate__mutmut_22, 
        'xǁManifestValidatorǁvalidate__mutmut_23': xǁManifestValidatorǁvalidate__mutmut_23, 
        'xǁManifestValidatorǁvalidate__mutmut_24': xǁManifestValidatorǁvalidate__mutmut_24, 
        'xǁManifestValidatorǁvalidate__mutmut_25': xǁManifestValidatorǁvalidate__mutmut_25, 
        'xǁManifestValidatorǁvalidate__mutmut_26': xǁManifestValidatorǁvalidate__mutmut_26, 
        'xǁManifestValidatorǁvalidate__mutmut_27': xǁManifestValidatorǁvalidate__mutmut_27, 
        'xǁManifestValidatorǁvalidate__mutmut_28': xǁManifestValidatorǁvalidate__mutmut_28, 
        'xǁManifestValidatorǁvalidate__mutmut_29': xǁManifestValidatorǁvalidate__mutmut_29, 
        'xǁManifestValidatorǁvalidate__mutmut_30': xǁManifestValidatorǁvalidate__mutmut_30, 
        'xǁManifestValidatorǁvalidate__mutmut_31': xǁManifestValidatorǁvalidate__mutmut_31, 
        'xǁManifestValidatorǁvalidate__mutmut_32': xǁManifestValidatorǁvalidate__mutmut_32, 
        'xǁManifestValidatorǁvalidate__mutmut_33': xǁManifestValidatorǁvalidate__mutmut_33, 
        'xǁManifestValidatorǁvalidate__mutmut_34': xǁManifestValidatorǁvalidate__mutmut_34, 
        'xǁManifestValidatorǁvalidate__mutmut_35': xǁManifestValidatorǁvalidate__mutmut_35, 
        'xǁManifestValidatorǁvalidate__mutmut_36': xǁManifestValidatorǁvalidate__mutmut_36, 
        'xǁManifestValidatorǁvalidate__mutmut_37': xǁManifestValidatorǁvalidate__mutmut_37, 
        'xǁManifestValidatorǁvalidate__mutmut_38': xǁManifestValidatorǁvalidate__mutmut_38, 
        'xǁManifestValidatorǁvalidate__mutmut_39': xǁManifestValidatorǁvalidate__mutmut_39, 
        'xǁManifestValidatorǁvalidate__mutmut_40': xǁManifestValidatorǁvalidate__mutmut_40, 
        'xǁManifestValidatorǁvalidate__mutmut_41': xǁManifestValidatorǁvalidate__mutmut_41, 
        'xǁManifestValidatorǁvalidate__mutmut_42': xǁManifestValidatorǁvalidate__mutmut_42, 
        'xǁManifestValidatorǁvalidate__mutmut_43': xǁManifestValidatorǁvalidate__mutmut_43, 
        'xǁManifestValidatorǁvalidate__mutmut_44': xǁManifestValidatorǁvalidate__mutmut_44, 
        'xǁManifestValidatorǁvalidate__mutmut_45': xǁManifestValidatorǁvalidate__mutmut_45, 
        'xǁManifestValidatorǁvalidate__mutmut_46': xǁManifestValidatorǁvalidate__mutmut_46, 
        'xǁManifestValidatorǁvalidate__mutmut_47': xǁManifestValidatorǁvalidate__mutmut_47, 
        'xǁManifestValidatorǁvalidate__mutmut_48': xǁManifestValidatorǁvalidate__mutmut_48, 
        'xǁManifestValidatorǁvalidate__mutmut_49': xǁManifestValidatorǁvalidate__mutmut_49, 
        'xǁManifestValidatorǁvalidate__mutmut_50': xǁManifestValidatorǁvalidate__mutmut_50, 
        'xǁManifestValidatorǁvalidate__mutmut_51': xǁManifestValidatorǁvalidate__mutmut_51, 
        'xǁManifestValidatorǁvalidate__mutmut_52': xǁManifestValidatorǁvalidate__mutmut_52, 
        'xǁManifestValidatorǁvalidate__mutmut_53': xǁManifestValidatorǁvalidate__mutmut_53, 
        'xǁManifestValidatorǁvalidate__mutmut_54': xǁManifestValidatorǁvalidate__mutmut_54, 
        'xǁManifestValidatorǁvalidate__mutmut_55': xǁManifestValidatorǁvalidate__mutmut_55, 
        'xǁManifestValidatorǁvalidate__mutmut_56': xǁManifestValidatorǁvalidate__mutmut_56, 
        'xǁManifestValidatorǁvalidate__mutmut_57': xǁManifestValidatorǁvalidate__mutmut_57, 
        'xǁManifestValidatorǁvalidate__mutmut_58': xǁManifestValidatorǁvalidate__mutmut_58, 
        'xǁManifestValidatorǁvalidate__mutmut_59': xǁManifestValidatorǁvalidate__mutmut_59, 
        'xǁManifestValidatorǁvalidate__mutmut_60': xǁManifestValidatorǁvalidate__mutmut_60, 
        'xǁManifestValidatorǁvalidate__mutmut_61': xǁManifestValidatorǁvalidate__mutmut_61, 
        'xǁManifestValidatorǁvalidate__mutmut_62': xǁManifestValidatorǁvalidate__mutmut_62, 
        'xǁManifestValidatorǁvalidate__mutmut_63': xǁManifestValidatorǁvalidate__mutmut_63, 
        'xǁManifestValidatorǁvalidate__mutmut_64': xǁManifestValidatorǁvalidate__mutmut_64, 
        'xǁManifestValidatorǁvalidate__mutmut_65': xǁManifestValidatorǁvalidate__mutmut_65, 
        'xǁManifestValidatorǁvalidate__mutmut_66': xǁManifestValidatorǁvalidate__mutmut_66, 
        'xǁManifestValidatorǁvalidate__mutmut_67': xǁManifestValidatorǁvalidate__mutmut_67, 
        'xǁManifestValidatorǁvalidate__mutmut_68': xǁManifestValidatorǁvalidate__mutmut_68, 
        'xǁManifestValidatorǁvalidate__mutmut_69': xǁManifestValidatorǁvalidate__mutmut_69, 
        'xǁManifestValidatorǁvalidate__mutmut_70': xǁManifestValidatorǁvalidate__mutmut_70, 
        'xǁManifestValidatorǁvalidate__mutmut_71': xǁManifestValidatorǁvalidate__mutmut_71, 
        'xǁManifestValidatorǁvalidate__mutmut_72': xǁManifestValidatorǁvalidate__mutmut_72, 
        'xǁManifestValidatorǁvalidate__mutmut_73': xǁManifestValidatorǁvalidate__mutmut_73, 
        'xǁManifestValidatorǁvalidate__mutmut_74': xǁManifestValidatorǁvalidate__mutmut_74, 
        'xǁManifestValidatorǁvalidate__mutmut_75': xǁManifestValidatorǁvalidate__mutmut_75, 
        'xǁManifestValidatorǁvalidate__mutmut_76': xǁManifestValidatorǁvalidate__mutmut_76, 
        'xǁManifestValidatorǁvalidate__mutmut_77': xǁManifestValidatorǁvalidate__mutmut_77, 
        'xǁManifestValidatorǁvalidate__mutmut_78': xǁManifestValidatorǁvalidate__mutmut_78, 
        'xǁManifestValidatorǁvalidate__mutmut_79': xǁManifestValidatorǁvalidate__mutmut_79, 
        'xǁManifestValidatorǁvalidate__mutmut_80': xǁManifestValidatorǁvalidate__mutmut_80, 
        'xǁManifestValidatorǁvalidate__mutmut_81': xǁManifestValidatorǁvalidate__mutmut_81, 
        'xǁManifestValidatorǁvalidate__mutmut_82': xǁManifestValidatorǁvalidate__mutmut_82, 
        'xǁManifestValidatorǁvalidate__mutmut_83': xǁManifestValidatorǁvalidate__mutmut_83, 
        'xǁManifestValidatorǁvalidate__mutmut_84': xǁManifestValidatorǁvalidate__mutmut_84, 
        'xǁManifestValidatorǁvalidate__mutmut_85': xǁManifestValidatorǁvalidate__mutmut_85, 
        'xǁManifestValidatorǁvalidate__mutmut_86': xǁManifestValidatorǁvalidate__mutmut_86, 
        'xǁManifestValidatorǁvalidate__mutmut_87': xǁManifestValidatorǁvalidate__mutmut_87, 
        'xǁManifestValidatorǁvalidate__mutmut_88': xǁManifestValidatorǁvalidate__mutmut_88, 
        'xǁManifestValidatorǁvalidate__mutmut_89': xǁManifestValidatorǁvalidate__mutmut_89, 
        'xǁManifestValidatorǁvalidate__mutmut_90': xǁManifestValidatorǁvalidate__mutmut_90, 
        'xǁManifestValidatorǁvalidate__mutmut_91': xǁManifestValidatorǁvalidate__mutmut_91, 
        'xǁManifestValidatorǁvalidate__mutmut_92': xǁManifestValidatorǁvalidate__mutmut_92, 
        'xǁManifestValidatorǁvalidate__mutmut_93': xǁManifestValidatorǁvalidate__mutmut_93, 
        'xǁManifestValidatorǁvalidate__mutmut_94': xǁManifestValidatorǁvalidate__mutmut_94, 
        'xǁManifestValidatorǁvalidate__mutmut_95': xǁManifestValidatorǁvalidate__mutmut_95, 
        'xǁManifestValidatorǁvalidate__mutmut_96': xǁManifestValidatorǁvalidate__mutmut_96, 
        'xǁManifestValidatorǁvalidate__mutmut_97': xǁManifestValidatorǁvalidate__mutmut_97, 
        'xǁManifestValidatorǁvalidate__mutmut_98': xǁManifestValidatorǁvalidate__mutmut_98, 
        'xǁManifestValidatorǁvalidate__mutmut_99': xǁManifestValidatorǁvalidate__mutmut_99, 
        'xǁManifestValidatorǁvalidate__mutmut_100': xǁManifestValidatorǁvalidate__mutmut_100, 
        'xǁManifestValidatorǁvalidate__mutmut_101': xǁManifestValidatorǁvalidate__mutmut_101, 
        'xǁManifestValidatorǁvalidate__mutmut_102': xǁManifestValidatorǁvalidate__mutmut_102, 
        'xǁManifestValidatorǁvalidate__mutmut_103': xǁManifestValidatorǁvalidate__mutmut_103, 
        'xǁManifestValidatorǁvalidate__mutmut_104': xǁManifestValidatorǁvalidate__mutmut_104, 
        'xǁManifestValidatorǁvalidate__mutmut_105': xǁManifestValidatorǁvalidate__mutmut_105, 
        'xǁManifestValidatorǁvalidate__mutmut_106': xǁManifestValidatorǁvalidate__mutmut_106, 
        'xǁManifestValidatorǁvalidate__mutmut_107': xǁManifestValidatorǁvalidate__mutmut_107, 
        'xǁManifestValidatorǁvalidate__mutmut_108': xǁManifestValidatorǁvalidate__mutmut_108
    }
    xǁManifestValidatorǁvalidate__mutmut_orig.__name__ = 'xǁManifestValidatorǁvalidate'
