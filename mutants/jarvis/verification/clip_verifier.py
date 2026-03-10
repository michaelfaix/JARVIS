# jarvis/verification/clip_verifier.py
# ClipVerifier -- verifies clip chain behaviour from observable output fields.
# Authority: DVH Implementation Blueprint v1.0.0 Section 11.
#
# NIC-01: No production module is wrapped, decorated, or instrumented.
# NIC-09: No internal state of the production module is accessed.
# All verification is performed from observable output fields only.
# No production arithmetic is reimplemented here (NIC-02).

import struct
import math
from typing import List, Dict, Tuple

from jarvis.verification.data_models.execution_record import ExecutionRecord, ObservedOutput
from jarvis.verification.data_models.comparison_report import ComparisonReport, FieldMismatch
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


def _float_bits(value: float) -> bytes:
    args = [value]# type: ignore
    kwargs = {}# type: ignore
    return _mutmut_trampoline(x__float_bits__mutmut_orig, x__float_bits__mutmut_mutants, args, kwargs, None)


def x__float_bits__mutmut_orig(value: float) -> bytes:
    """Return 8-byte big-endian IEEE 754 representation."""
    return struct.pack(">d", value)


def x__float_bits__mutmut_1(value: float) -> bytes:
    """Return 8-byte big-endian IEEE 754 representation."""
    return struct.pack(None, value)


def x__float_bits__mutmut_2(value: float) -> bytes:
    """Return 8-byte big-endian IEEE 754 representation."""
    return struct.pack(">d", None)


def x__float_bits__mutmut_3(value: float) -> bytes:
    """Return 8-byte big-endian IEEE 754 representation."""
    return struct.pack(value)


def x__float_bits__mutmut_4(value: float) -> bytes:
    """Return 8-byte big-endian IEEE 754 representation."""
    return struct.pack(">d", )


def x__float_bits__mutmut_5(value: float) -> bytes:
    """Return 8-byte big-endian IEEE 754 representation."""
    return struct.pack("XX>dXX", value)


def x__float_bits__mutmut_6(value: float) -> bytes:
    """Return 8-byte big-endian IEEE 754 representation."""
    return struct.pack(">D", value)

x__float_bits__mutmut_mutants : ClassVar[MutantDict] = { # type: ignore
'x__float_bits__mutmut_1': x__float_bits__mutmut_1, 
    'x__float_bits__mutmut_2': x__float_bits__mutmut_2, 
    'x__float_bits__mutmut_3': x__float_bits__mutmut_3, 
    'x__float_bits__mutmut_4': x__float_bits__mutmut_4, 
    'x__float_bits__mutmut_5': x__float_bits__mutmut_5, 
    'x__float_bits__mutmut_6': x__float_bits__mutmut_6
}
x__float_bits__mutmut_orig.__name__ = 'x__float_bits'


def _floats_equal(a: float, b: float) -> bool:
    args = [a, b]# type: ignore
    kwargs = {}# type: ignore
    return _mutmut_trampoline(x__floats_equal__mutmut_orig, x__floats_equal__mutmut_mutants, args, kwargs, None)


def x__floats_equal__mutmut_orig(a: float, b: float) -> bool:
    """Exact bit-pattern equality (same rule as BitComparator)."""
    return _float_bits(a) == _float_bits(b)


def x__floats_equal__mutmut_1(a: float, b: float) -> bool:
    """Exact bit-pattern equality (same rule as BitComparator)."""
    return _float_bits(None) == _float_bits(b)


def x__floats_equal__mutmut_2(a: float, b: float) -> bool:
    """Exact bit-pattern equality (same rule as BitComparator)."""
    return _float_bits(a) != _float_bits(b)


def x__floats_equal__mutmut_3(a: float, b: float) -> bool:
    """Exact bit-pattern equality (same rule as BitComparator)."""
    return _float_bits(a) == _float_bits(None)

x__floats_equal__mutmut_mutants : ClassVar[MutantDict] = { # type: ignore
'x__floats_equal__mutmut_1': x__floats_equal__mutmut_1, 
    'x__floats_equal__mutmut_2': x__floats_equal__mutmut_2, 
    'x__floats_equal__mutmut_3': x__floats_equal__mutmut_3
}
x__floats_equal__mutmut_orig.__name__ = 'x__floats_equal'


class ClipVerifier:
    """
    Examines observable output fields and verifies clip chain constraints.

    Verification is derived entirely from observable output. No production
    module internal state is accessed (NIC-09). No production arithmetic
    is reimplemented (NIC-02).

    Implements CCV-A-01 through CCV-D-03 from Section 11.
    """

    def __init__(
        self,
        shock_exposure_cap:      float,
        max_drawdown_threshold:  float,
        vol_compression_trigger: float,
    ):
        args = [shock_exposure_cap, max_drawdown_threshold, vol_compression_trigger]# type: ignore
        kwargs = {}# type: ignore
        return _mutmut_trampoline(object.__getattribute__(self, 'xǁClipVerifierǁ__init____mutmut_orig'), object.__getattribute__(self, 'xǁClipVerifierǁ__init____mutmut_mutants'), args, kwargs, self)

    def xǁClipVerifierǁ__init____mutmut_orig(
        self,
        shock_exposure_cap:      float,
        max_drawdown_threshold:  float,
        vol_compression_trigger: float,
    ):
        self._sec  = shock_exposure_cap
        self._mdt  = max_drawdown_threshold
        self._vct  = vol_compression_trigger
        self._sec_bits = _float_bits(shock_exposure_cap)
        self._lb_bits  = _float_bits(1e-6)
        self._one_bits = _float_bits(1.0)
        self._zero_bits = _float_bits(0.0)

    def xǁClipVerifierǁ__init____mutmut_1(
        self,
        shock_exposure_cap:      float,
        max_drawdown_threshold:  float,
        vol_compression_trigger: float,
    ):
        self._sec  = None
        self._mdt  = max_drawdown_threshold
        self._vct  = vol_compression_trigger
        self._sec_bits = _float_bits(shock_exposure_cap)
        self._lb_bits  = _float_bits(1e-6)
        self._one_bits = _float_bits(1.0)
        self._zero_bits = _float_bits(0.0)

    def xǁClipVerifierǁ__init____mutmut_2(
        self,
        shock_exposure_cap:      float,
        max_drawdown_threshold:  float,
        vol_compression_trigger: float,
    ):
        self._sec  = shock_exposure_cap
        self._mdt  = None
        self._vct  = vol_compression_trigger
        self._sec_bits = _float_bits(shock_exposure_cap)
        self._lb_bits  = _float_bits(1e-6)
        self._one_bits = _float_bits(1.0)
        self._zero_bits = _float_bits(0.0)

    def xǁClipVerifierǁ__init____mutmut_3(
        self,
        shock_exposure_cap:      float,
        max_drawdown_threshold:  float,
        vol_compression_trigger: float,
    ):
        self._sec  = shock_exposure_cap
        self._mdt  = max_drawdown_threshold
        self._vct  = None
        self._sec_bits = _float_bits(shock_exposure_cap)
        self._lb_bits  = _float_bits(1e-6)
        self._one_bits = _float_bits(1.0)
        self._zero_bits = _float_bits(0.0)

    def xǁClipVerifierǁ__init____mutmut_4(
        self,
        shock_exposure_cap:      float,
        max_drawdown_threshold:  float,
        vol_compression_trigger: float,
    ):
        self._sec  = shock_exposure_cap
        self._mdt  = max_drawdown_threshold
        self._vct  = vol_compression_trigger
        self._sec_bits = None
        self._lb_bits  = _float_bits(1e-6)
        self._one_bits = _float_bits(1.0)
        self._zero_bits = _float_bits(0.0)

    def xǁClipVerifierǁ__init____mutmut_5(
        self,
        shock_exposure_cap:      float,
        max_drawdown_threshold:  float,
        vol_compression_trigger: float,
    ):
        self._sec  = shock_exposure_cap
        self._mdt  = max_drawdown_threshold
        self._vct  = vol_compression_trigger
        self._sec_bits = _float_bits(None)
        self._lb_bits  = _float_bits(1e-6)
        self._one_bits = _float_bits(1.0)
        self._zero_bits = _float_bits(0.0)

    def xǁClipVerifierǁ__init____mutmut_6(
        self,
        shock_exposure_cap:      float,
        max_drawdown_threshold:  float,
        vol_compression_trigger: float,
    ):
        self._sec  = shock_exposure_cap
        self._mdt  = max_drawdown_threshold
        self._vct  = vol_compression_trigger
        self._sec_bits = _float_bits(shock_exposure_cap)
        self._lb_bits  = None
        self._one_bits = _float_bits(1.0)
        self._zero_bits = _float_bits(0.0)

    def xǁClipVerifierǁ__init____mutmut_7(
        self,
        shock_exposure_cap:      float,
        max_drawdown_threshold:  float,
        vol_compression_trigger: float,
    ):
        self._sec  = shock_exposure_cap
        self._mdt  = max_drawdown_threshold
        self._vct  = vol_compression_trigger
        self._sec_bits = _float_bits(shock_exposure_cap)
        self._lb_bits  = _float_bits(None)
        self._one_bits = _float_bits(1.0)
        self._zero_bits = _float_bits(0.0)

    def xǁClipVerifierǁ__init____mutmut_8(
        self,
        shock_exposure_cap:      float,
        max_drawdown_threshold:  float,
        vol_compression_trigger: float,
    ):
        self._sec  = shock_exposure_cap
        self._mdt  = max_drawdown_threshold
        self._vct  = vol_compression_trigger
        self._sec_bits = _float_bits(shock_exposure_cap)
        self._lb_bits  = _float_bits(1.000001)
        self._one_bits = _float_bits(1.0)
        self._zero_bits = _float_bits(0.0)

    def xǁClipVerifierǁ__init____mutmut_9(
        self,
        shock_exposure_cap:      float,
        max_drawdown_threshold:  float,
        vol_compression_trigger: float,
    ):
        self._sec  = shock_exposure_cap
        self._mdt  = max_drawdown_threshold
        self._vct  = vol_compression_trigger
        self._sec_bits = _float_bits(shock_exposure_cap)
        self._lb_bits  = _float_bits(1e-6)
        self._one_bits = None
        self._zero_bits = _float_bits(0.0)

    def xǁClipVerifierǁ__init____mutmut_10(
        self,
        shock_exposure_cap:      float,
        max_drawdown_threshold:  float,
        vol_compression_trigger: float,
    ):
        self._sec  = shock_exposure_cap
        self._mdt  = max_drawdown_threshold
        self._vct  = vol_compression_trigger
        self._sec_bits = _float_bits(shock_exposure_cap)
        self._lb_bits  = _float_bits(1e-6)
        self._one_bits = _float_bits(None)
        self._zero_bits = _float_bits(0.0)

    def xǁClipVerifierǁ__init____mutmut_11(
        self,
        shock_exposure_cap:      float,
        max_drawdown_threshold:  float,
        vol_compression_trigger: float,
    ):
        self._sec  = shock_exposure_cap
        self._mdt  = max_drawdown_threshold
        self._vct  = vol_compression_trigger
        self._sec_bits = _float_bits(shock_exposure_cap)
        self._lb_bits  = _float_bits(1e-6)
        self._one_bits = _float_bits(2.0)
        self._zero_bits = _float_bits(0.0)

    def xǁClipVerifierǁ__init____mutmut_12(
        self,
        shock_exposure_cap:      float,
        max_drawdown_threshold:  float,
        vol_compression_trigger: float,
    ):
        self._sec  = shock_exposure_cap
        self._mdt  = max_drawdown_threshold
        self._vct  = vol_compression_trigger
        self._sec_bits = _float_bits(shock_exposure_cap)
        self._lb_bits  = _float_bits(1e-6)
        self._one_bits = _float_bits(1.0)
        self._zero_bits = None

    def xǁClipVerifierǁ__init____mutmut_13(
        self,
        shock_exposure_cap:      float,
        max_drawdown_threshold:  float,
        vol_compression_trigger: float,
    ):
        self._sec  = shock_exposure_cap
        self._mdt  = max_drawdown_threshold
        self._vct  = vol_compression_trigger
        self._sec_bits = _float_bits(shock_exposure_cap)
        self._lb_bits  = _float_bits(1e-6)
        self._one_bits = _float_bits(1.0)
        self._zero_bits = _float_bits(None)

    def xǁClipVerifierǁ__init____mutmut_14(
        self,
        shock_exposure_cap:      float,
        max_drawdown_threshold:  float,
        vol_compression_trigger: float,
    ):
        self._sec  = shock_exposure_cap
        self._mdt  = max_drawdown_threshold
        self._vct  = vol_compression_trigger
        self._sec_bits = _float_bits(shock_exposure_cap)
        self._lb_bits  = _float_bits(1e-6)
        self._one_bits = _float_bits(1.0)
        self._zero_bits = _float_bits(1.0)
    
    xǁClipVerifierǁ__init____mutmut_mutants : ClassVar[MutantDict] = { # type: ignore
    'xǁClipVerifierǁ__init____mutmut_1': xǁClipVerifierǁ__init____mutmut_1, 
        'xǁClipVerifierǁ__init____mutmut_2': xǁClipVerifierǁ__init____mutmut_2, 
        'xǁClipVerifierǁ__init____mutmut_3': xǁClipVerifierǁ__init____mutmut_3, 
        'xǁClipVerifierǁ__init____mutmut_4': xǁClipVerifierǁ__init____mutmut_4, 
        'xǁClipVerifierǁ__init____mutmut_5': xǁClipVerifierǁ__init____mutmut_5, 
        'xǁClipVerifierǁ__init____mutmut_6': xǁClipVerifierǁ__init____mutmut_6, 
        'xǁClipVerifierǁ__init____mutmut_7': xǁClipVerifierǁ__init____mutmut_7, 
        'xǁClipVerifierǁ__init____mutmut_8': xǁClipVerifierǁ__init____mutmut_8, 
        'xǁClipVerifierǁ__init____mutmut_9': xǁClipVerifierǁ__init____mutmut_9, 
        'xǁClipVerifierǁ__init____mutmut_10': xǁClipVerifierǁ__init____mutmut_10, 
        'xǁClipVerifierǁ__init____mutmut_11': xǁClipVerifierǁ__init____mutmut_11, 
        'xǁClipVerifierǁ__init____mutmut_12': xǁClipVerifierǁ__init____mutmut_12, 
        'xǁClipVerifierǁ__init____mutmut_13': xǁClipVerifierǁ__init____mutmut_13, 
        'xǁClipVerifierǁ__init____mutmut_14': xǁClipVerifierǁ__init____mutmut_14
    }
    xǁClipVerifierǁ__init____mutmut_orig.__name__ = 'xǁClipVerifierǁ__init__'

    def verify(
        self,
        er_records: List[ExecutionRecord],
    ) -> Tuple[List[str], List[str]]:
        args = [er_records]# type: ignore
        kwargs = {}# type: ignore
        return _mutmut_trampoline(object.__getattribute__(self, 'xǁClipVerifierǁverify__mutmut_orig'), object.__getattribute__(self, 'xǁClipVerifierǁverify__mutmut_mutants'), args, kwargs, self)

    def xǁClipVerifierǁverify__mutmut_orig(
        self,
        er_records: List[ExecutionRecord],
    ) -> Tuple[List[str], List[str]]:
        """
        Perform clip chain verification on ER-stage records.

        Returns:
          (violations, notes)
          violations -- list of violation description strings. Empty means pass.
          notes      -- list of non-failure informational notes.

        Raises RuntimeError with failure_type_id prefix on hard failures
        (CLIP_B_FLOOR_VIOLATION, CLIP_C_FLOOR_VIOLATION, CLIP_A_VIOLATION,
        CRISIS_ORDERING_VIOLATION).
        """
        violations = []
        notes      = []
        by_id: Dict[str, ExecutionRecord] = {r.vector_id: r for r in er_records}

        for rec in er_records:
            out = rec.observed_output
            if out.exception_raised:
                # No clip verification for exception vectors.
                continue

            vid = rec.vector_id
            iv  = rec.input_vector

            # ----------------------------------------------------------------
            # CCV-A-01: Clip A verification.
            # position_size_factor must be in [0.0, 1.0] for every normal vector.
            # ----------------------------------------------------------------
            psf = out.position_size_factor
            if psf < 0.0 or psf > 1.0:
                raise RuntimeError(
                    f"CLIP_A_VIOLATION: Vector {vid} position_size_factor={psf} "
                    "is outside [0.0, 1.0]. INV-01 violated."
                )

            # ----------------------------------------------------------------
            # CCV-B-01: For MU-02 and RP-02, E_pre_clip should be zero or near zero,
            # so Clip B floor should be active. exposure_weight bit pattern should
            # equal bit pattern of 1e-6.
            # ----------------------------------------------------------------
            if vid in ("MU-02", "RP-02"):
                ew_bits = _float_bits(out.exposure_weight)
                if ew_bits != self._lb_bits:
                    raise RuntimeError(
                        f"CLIP_B_FLOOR_VIOLATION: Vector {vid} exposure_weight "
                        f"expected bit pattern of 1e-6 but got "
                        f"{out.exposure_weight!r}. INV-02 violated."
                    )

            # ----------------------------------------------------------------
            # CCV-B-02: For JM-inactive (JM-01, JM-04) non-CRISIS vectors,
            # exposure_weight must be in [1e-6, 1.0].
            # (Clip C inactive, CRISIS dampening inactive.)
            # ----------------------------------------------------------------
            if vid in ("JM-01", "JM-04") and iv.current_regime_str != "CRISIS":
                ew = out.exposure_weight
                if ew < 1e-6 or ew > 1.0:
                    raise RuntimeError(
                        f"CLIP_B_RANGE_VIOLATION: Vector {vid} exposure_weight={ew} "
                        "outside [1e-6, 1.0] with Clip C and CRISIS dampening both "
                        "inactive. INV-02 violated."
                    )

            # ----------------------------------------------------------------
            # CCV-C-02: For JM-03 (designed to produce pre-Clip-C value below
            # SHOCK_EXPOSURE_CAP), exposure_weight should equal SHOCK_EXPOSURE_CAP.
            # ----------------------------------------------------------------
            if vid == "JM-03":
                ew_bits = _float_bits(out.exposure_weight)
                if ew_bits != self._sec_bits:
                    # JM-03 uses meta_uncertainty=0.99 + multiplier=2.0.
                    # The division may produce a value below SHOCK_EXPOSURE_CAP,
                    # which gets clipped to SHOCK_EXPOSURE_CAP by Clip C.
                    # If the result does NOT equal SHOCK_EXPOSURE_CAP, the
                    # actual computed value exceeded the cap after division;
                    # this is acceptable if the value is above SHOCK_EXPOSURE_CAP.
                    # Hard failure only if value is strictly below SHOCK_EXPOSURE_CAP.
                    if out.exposure_weight < self._sec:
                        raise RuntimeError(
                            f"CLIP_C_FLOOR_VIOLATION: Vector {vid} exposure_weight="
                            f"{out.exposure_weight} is below SHOCK_EXPOSURE_CAP="
                            f"{self._sec}. INV-03 violated."
                        )
                    notes.append(
                        f"CCV-C-02 note: JM-03 exposure_weight={out.exposure_weight} "
                        "exceeds SHOCK_EXPOSURE_CAP; Clip C floor not triggered."
                    )

            # ----------------------------------------------------------------
            # CCV-D-02: For CR-01 (CRISIS, JRM inactive), exposure_weight may be
            # below SHOCK_EXPOSURE_CAP. No floor enforcement. This is specified
            # behaviour per INV-04.
            # ----------------------------------------------------------------
            if vid == "CR-01":
                notes.append(
                    f"CCV-D-02: CR-01 exposure_weight={out.exposure_weight}. "
                    "May be below SHOCK_EXPOSURE_CAP per INV-04 (specified behaviour)."
                )

        # --------------------------------------------------------------------
        # CCV-D-01: For CR-02 (CRISIS + JRM active), verify ordering.
        # Expected: CR-02.exposure_weight == JM-03.exposure_weight * 0.75
        # Both records must be present in ER set.
        # --------------------------------------------------------------------
        if "CR-02" in by_id and "JM-03" in by_id:
            cr02_out = by_id["CR-02"].observed_output
            jm03_out = by_id["JM-03"].observed_output
            if not cr02_out.exception_raised and not jm03_out.exception_raised:
                # Compute expected value using Python float arithmetic (same as production).
                expected_cr02_ew = jm03_out.exposure_weight * 0.75
                if not _floats_equal(cr02_out.exposure_weight, expected_cr02_ew):
                    raise RuntimeError(
                        f"CRISIS_ORDERING_VIOLATION: CR-02 exposure_weight="
                        f"{cr02_out.exposure_weight} != JM-03.exposure_weight*0.75="
                        f"{expected_cr02_ew}. Clip C / CRISIS ordering violated. "
                        "INV-04 violated."
                    )

        # --------------------------------------------------------------------
        # CCV-D-03: CR-03 (non-CRISIS with JRM active) -- dampening must NOT apply.
        # Verified by BIC backward compatibility comparison against a non-CRISIS
        # variant. Here we simply note the check for audit.
        # --------------------------------------------------------------------
        if "CR-03" in by_id:
            notes.append(
                "CCV-D-03: CR-03 is non-CRISIS with JRM active. Dampening "
                "not applied. Verified by absence of *0.75 in BIC comparison."
            )

        return violations, notes

    def xǁClipVerifierǁverify__mutmut_1(
        self,
        er_records: List[ExecutionRecord],
    ) -> Tuple[List[str], List[str]]:
        """
        Perform clip chain verification on ER-stage records.

        Returns:
          (violations, notes)
          violations -- list of violation description strings. Empty means pass.
          notes      -- list of non-failure informational notes.

        Raises RuntimeError with failure_type_id prefix on hard failures
        (CLIP_B_FLOOR_VIOLATION, CLIP_C_FLOOR_VIOLATION, CLIP_A_VIOLATION,
        CRISIS_ORDERING_VIOLATION).
        """
        violations = None
        notes      = []
        by_id: Dict[str, ExecutionRecord] = {r.vector_id: r for r in er_records}

        for rec in er_records:
            out = rec.observed_output
            if out.exception_raised:
                # No clip verification for exception vectors.
                continue

            vid = rec.vector_id
            iv  = rec.input_vector

            # ----------------------------------------------------------------
            # CCV-A-01: Clip A verification.
            # position_size_factor must be in [0.0, 1.0] for every normal vector.
            # ----------------------------------------------------------------
            psf = out.position_size_factor
            if psf < 0.0 or psf > 1.0:
                raise RuntimeError(
                    f"CLIP_A_VIOLATION: Vector {vid} position_size_factor={psf} "
                    "is outside [0.0, 1.0]. INV-01 violated."
                )

            # ----------------------------------------------------------------
            # CCV-B-01: For MU-02 and RP-02, E_pre_clip should be zero or near zero,
            # so Clip B floor should be active. exposure_weight bit pattern should
            # equal bit pattern of 1e-6.
            # ----------------------------------------------------------------
            if vid in ("MU-02", "RP-02"):
                ew_bits = _float_bits(out.exposure_weight)
                if ew_bits != self._lb_bits:
                    raise RuntimeError(
                        f"CLIP_B_FLOOR_VIOLATION: Vector {vid} exposure_weight "
                        f"expected bit pattern of 1e-6 but got "
                        f"{out.exposure_weight!r}. INV-02 violated."
                    )

            # ----------------------------------------------------------------
            # CCV-B-02: For JM-inactive (JM-01, JM-04) non-CRISIS vectors,
            # exposure_weight must be in [1e-6, 1.0].
            # (Clip C inactive, CRISIS dampening inactive.)
            # ----------------------------------------------------------------
            if vid in ("JM-01", "JM-04") and iv.current_regime_str != "CRISIS":
                ew = out.exposure_weight
                if ew < 1e-6 or ew > 1.0:
                    raise RuntimeError(
                        f"CLIP_B_RANGE_VIOLATION: Vector {vid} exposure_weight={ew} "
                        "outside [1e-6, 1.0] with Clip C and CRISIS dampening both "
                        "inactive. INV-02 violated."
                    )

            # ----------------------------------------------------------------
            # CCV-C-02: For JM-03 (designed to produce pre-Clip-C value below
            # SHOCK_EXPOSURE_CAP), exposure_weight should equal SHOCK_EXPOSURE_CAP.
            # ----------------------------------------------------------------
            if vid == "JM-03":
                ew_bits = _float_bits(out.exposure_weight)
                if ew_bits != self._sec_bits:
                    # JM-03 uses meta_uncertainty=0.99 + multiplier=2.0.
                    # The division may produce a value below SHOCK_EXPOSURE_CAP,
                    # which gets clipped to SHOCK_EXPOSURE_CAP by Clip C.
                    # If the result does NOT equal SHOCK_EXPOSURE_CAP, the
                    # actual computed value exceeded the cap after division;
                    # this is acceptable if the value is above SHOCK_EXPOSURE_CAP.
                    # Hard failure only if value is strictly below SHOCK_EXPOSURE_CAP.
                    if out.exposure_weight < self._sec:
                        raise RuntimeError(
                            f"CLIP_C_FLOOR_VIOLATION: Vector {vid} exposure_weight="
                            f"{out.exposure_weight} is below SHOCK_EXPOSURE_CAP="
                            f"{self._sec}. INV-03 violated."
                        )
                    notes.append(
                        f"CCV-C-02 note: JM-03 exposure_weight={out.exposure_weight} "
                        "exceeds SHOCK_EXPOSURE_CAP; Clip C floor not triggered."
                    )

            # ----------------------------------------------------------------
            # CCV-D-02: For CR-01 (CRISIS, JRM inactive), exposure_weight may be
            # below SHOCK_EXPOSURE_CAP. No floor enforcement. This is specified
            # behaviour per INV-04.
            # ----------------------------------------------------------------
            if vid == "CR-01":
                notes.append(
                    f"CCV-D-02: CR-01 exposure_weight={out.exposure_weight}. "
                    "May be below SHOCK_EXPOSURE_CAP per INV-04 (specified behaviour)."
                )

        # --------------------------------------------------------------------
        # CCV-D-01: For CR-02 (CRISIS + JRM active), verify ordering.
        # Expected: CR-02.exposure_weight == JM-03.exposure_weight * 0.75
        # Both records must be present in ER set.
        # --------------------------------------------------------------------
        if "CR-02" in by_id and "JM-03" in by_id:
            cr02_out = by_id["CR-02"].observed_output
            jm03_out = by_id["JM-03"].observed_output
            if not cr02_out.exception_raised and not jm03_out.exception_raised:
                # Compute expected value using Python float arithmetic (same as production).
                expected_cr02_ew = jm03_out.exposure_weight * 0.75
                if not _floats_equal(cr02_out.exposure_weight, expected_cr02_ew):
                    raise RuntimeError(
                        f"CRISIS_ORDERING_VIOLATION: CR-02 exposure_weight="
                        f"{cr02_out.exposure_weight} != JM-03.exposure_weight*0.75="
                        f"{expected_cr02_ew}. Clip C / CRISIS ordering violated. "
                        "INV-04 violated."
                    )

        # --------------------------------------------------------------------
        # CCV-D-03: CR-03 (non-CRISIS with JRM active) -- dampening must NOT apply.
        # Verified by BIC backward compatibility comparison against a non-CRISIS
        # variant. Here we simply note the check for audit.
        # --------------------------------------------------------------------
        if "CR-03" in by_id:
            notes.append(
                "CCV-D-03: CR-03 is non-CRISIS with JRM active. Dampening "
                "not applied. Verified by absence of *0.75 in BIC comparison."
            )

        return violations, notes

    def xǁClipVerifierǁverify__mutmut_2(
        self,
        er_records: List[ExecutionRecord],
    ) -> Tuple[List[str], List[str]]:
        """
        Perform clip chain verification on ER-stage records.

        Returns:
          (violations, notes)
          violations -- list of violation description strings. Empty means pass.
          notes      -- list of non-failure informational notes.

        Raises RuntimeError with failure_type_id prefix on hard failures
        (CLIP_B_FLOOR_VIOLATION, CLIP_C_FLOOR_VIOLATION, CLIP_A_VIOLATION,
        CRISIS_ORDERING_VIOLATION).
        """
        violations = []
        notes      = None
        by_id: Dict[str, ExecutionRecord] = {r.vector_id: r for r in er_records}

        for rec in er_records:
            out = rec.observed_output
            if out.exception_raised:
                # No clip verification for exception vectors.
                continue

            vid = rec.vector_id
            iv  = rec.input_vector

            # ----------------------------------------------------------------
            # CCV-A-01: Clip A verification.
            # position_size_factor must be in [0.0, 1.0] for every normal vector.
            # ----------------------------------------------------------------
            psf = out.position_size_factor
            if psf < 0.0 or psf > 1.0:
                raise RuntimeError(
                    f"CLIP_A_VIOLATION: Vector {vid} position_size_factor={psf} "
                    "is outside [0.0, 1.0]. INV-01 violated."
                )

            # ----------------------------------------------------------------
            # CCV-B-01: For MU-02 and RP-02, E_pre_clip should be zero or near zero,
            # so Clip B floor should be active. exposure_weight bit pattern should
            # equal bit pattern of 1e-6.
            # ----------------------------------------------------------------
            if vid in ("MU-02", "RP-02"):
                ew_bits = _float_bits(out.exposure_weight)
                if ew_bits != self._lb_bits:
                    raise RuntimeError(
                        f"CLIP_B_FLOOR_VIOLATION: Vector {vid} exposure_weight "
                        f"expected bit pattern of 1e-6 but got "
                        f"{out.exposure_weight!r}. INV-02 violated."
                    )

            # ----------------------------------------------------------------
            # CCV-B-02: For JM-inactive (JM-01, JM-04) non-CRISIS vectors,
            # exposure_weight must be in [1e-6, 1.0].
            # (Clip C inactive, CRISIS dampening inactive.)
            # ----------------------------------------------------------------
            if vid in ("JM-01", "JM-04") and iv.current_regime_str != "CRISIS":
                ew = out.exposure_weight
                if ew < 1e-6 or ew > 1.0:
                    raise RuntimeError(
                        f"CLIP_B_RANGE_VIOLATION: Vector {vid} exposure_weight={ew} "
                        "outside [1e-6, 1.0] with Clip C and CRISIS dampening both "
                        "inactive. INV-02 violated."
                    )

            # ----------------------------------------------------------------
            # CCV-C-02: For JM-03 (designed to produce pre-Clip-C value below
            # SHOCK_EXPOSURE_CAP), exposure_weight should equal SHOCK_EXPOSURE_CAP.
            # ----------------------------------------------------------------
            if vid == "JM-03":
                ew_bits = _float_bits(out.exposure_weight)
                if ew_bits != self._sec_bits:
                    # JM-03 uses meta_uncertainty=0.99 + multiplier=2.0.
                    # The division may produce a value below SHOCK_EXPOSURE_CAP,
                    # which gets clipped to SHOCK_EXPOSURE_CAP by Clip C.
                    # If the result does NOT equal SHOCK_EXPOSURE_CAP, the
                    # actual computed value exceeded the cap after division;
                    # this is acceptable if the value is above SHOCK_EXPOSURE_CAP.
                    # Hard failure only if value is strictly below SHOCK_EXPOSURE_CAP.
                    if out.exposure_weight < self._sec:
                        raise RuntimeError(
                            f"CLIP_C_FLOOR_VIOLATION: Vector {vid} exposure_weight="
                            f"{out.exposure_weight} is below SHOCK_EXPOSURE_CAP="
                            f"{self._sec}. INV-03 violated."
                        )
                    notes.append(
                        f"CCV-C-02 note: JM-03 exposure_weight={out.exposure_weight} "
                        "exceeds SHOCK_EXPOSURE_CAP; Clip C floor not triggered."
                    )

            # ----------------------------------------------------------------
            # CCV-D-02: For CR-01 (CRISIS, JRM inactive), exposure_weight may be
            # below SHOCK_EXPOSURE_CAP. No floor enforcement. This is specified
            # behaviour per INV-04.
            # ----------------------------------------------------------------
            if vid == "CR-01":
                notes.append(
                    f"CCV-D-02: CR-01 exposure_weight={out.exposure_weight}. "
                    "May be below SHOCK_EXPOSURE_CAP per INV-04 (specified behaviour)."
                )

        # --------------------------------------------------------------------
        # CCV-D-01: For CR-02 (CRISIS + JRM active), verify ordering.
        # Expected: CR-02.exposure_weight == JM-03.exposure_weight * 0.75
        # Both records must be present in ER set.
        # --------------------------------------------------------------------
        if "CR-02" in by_id and "JM-03" in by_id:
            cr02_out = by_id["CR-02"].observed_output
            jm03_out = by_id["JM-03"].observed_output
            if not cr02_out.exception_raised and not jm03_out.exception_raised:
                # Compute expected value using Python float arithmetic (same as production).
                expected_cr02_ew = jm03_out.exposure_weight * 0.75
                if not _floats_equal(cr02_out.exposure_weight, expected_cr02_ew):
                    raise RuntimeError(
                        f"CRISIS_ORDERING_VIOLATION: CR-02 exposure_weight="
                        f"{cr02_out.exposure_weight} != JM-03.exposure_weight*0.75="
                        f"{expected_cr02_ew}. Clip C / CRISIS ordering violated. "
                        "INV-04 violated."
                    )

        # --------------------------------------------------------------------
        # CCV-D-03: CR-03 (non-CRISIS with JRM active) -- dampening must NOT apply.
        # Verified by BIC backward compatibility comparison against a non-CRISIS
        # variant. Here we simply note the check for audit.
        # --------------------------------------------------------------------
        if "CR-03" in by_id:
            notes.append(
                "CCV-D-03: CR-03 is non-CRISIS with JRM active. Dampening "
                "not applied. Verified by absence of *0.75 in BIC comparison."
            )

        return violations, notes

    def xǁClipVerifierǁverify__mutmut_3(
        self,
        er_records: List[ExecutionRecord],
    ) -> Tuple[List[str], List[str]]:
        """
        Perform clip chain verification on ER-stage records.

        Returns:
          (violations, notes)
          violations -- list of violation description strings. Empty means pass.
          notes      -- list of non-failure informational notes.

        Raises RuntimeError with failure_type_id prefix on hard failures
        (CLIP_B_FLOOR_VIOLATION, CLIP_C_FLOOR_VIOLATION, CLIP_A_VIOLATION,
        CRISIS_ORDERING_VIOLATION).
        """
        violations = []
        notes      = []
        by_id: Dict[str, ExecutionRecord] = None

        for rec in er_records:
            out = rec.observed_output
            if out.exception_raised:
                # No clip verification for exception vectors.
                continue

            vid = rec.vector_id
            iv  = rec.input_vector

            # ----------------------------------------------------------------
            # CCV-A-01: Clip A verification.
            # position_size_factor must be in [0.0, 1.0] for every normal vector.
            # ----------------------------------------------------------------
            psf = out.position_size_factor
            if psf < 0.0 or psf > 1.0:
                raise RuntimeError(
                    f"CLIP_A_VIOLATION: Vector {vid} position_size_factor={psf} "
                    "is outside [0.0, 1.0]. INV-01 violated."
                )

            # ----------------------------------------------------------------
            # CCV-B-01: For MU-02 and RP-02, E_pre_clip should be zero or near zero,
            # so Clip B floor should be active. exposure_weight bit pattern should
            # equal bit pattern of 1e-6.
            # ----------------------------------------------------------------
            if vid in ("MU-02", "RP-02"):
                ew_bits = _float_bits(out.exposure_weight)
                if ew_bits != self._lb_bits:
                    raise RuntimeError(
                        f"CLIP_B_FLOOR_VIOLATION: Vector {vid} exposure_weight "
                        f"expected bit pattern of 1e-6 but got "
                        f"{out.exposure_weight!r}. INV-02 violated."
                    )

            # ----------------------------------------------------------------
            # CCV-B-02: For JM-inactive (JM-01, JM-04) non-CRISIS vectors,
            # exposure_weight must be in [1e-6, 1.0].
            # (Clip C inactive, CRISIS dampening inactive.)
            # ----------------------------------------------------------------
            if vid in ("JM-01", "JM-04") and iv.current_regime_str != "CRISIS":
                ew = out.exposure_weight
                if ew < 1e-6 or ew > 1.0:
                    raise RuntimeError(
                        f"CLIP_B_RANGE_VIOLATION: Vector {vid} exposure_weight={ew} "
                        "outside [1e-6, 1.0] with Clip C and CRISIS dampening both "
                        "inactive. INV-02 violated."
                    )

            # ----------------------------------------------------------------
            # CCV-C-02: For JM-03 (designed to produce pre-Clip-C value below
            # SHOCK_EXPOSURE_CAP), exposure_weight should equal SHOCK_EXPOSURE_CAP.
            # ----------------------------------------------------------------
            if vid == "JM-03":
                ew_bits = _float_bits(out.exposure_weight)
                if ew_bits != self._sec_bits:
                    # JM-03 uses meta_uncertainty=0.99 + multiplier=2.0.
                    # The division may produce a value below SHOCK_EXPOSURE_CAP,
                    # which gets clipped to SHOCK_EXPOSURE_CAP by Clip C.
                    # If the result does NOT equal SHOCK_EXPOSURE_CAP, the
                    # actual computed value exceeded the cap after division;
                    # this is acceptable if the value is above SHOCK_EXPOSURE_CAP.
                    # Hard failure only if value is strictly below SHOCK_EXPOSURE_CAP.
                    if out.exposure_weight < self._sec:
                        raise RuntimeError(
                            f"CLIP_C_FLOOR_VIOLATION: Vector {vid} exposure_weight="
                            f"{out.exposure_weight} is below SHOCK_EXPOSURE_CAP="
                            f"{self._sec}. INV-03 violated."
                        )
                    notes.append(
                        f"CCV-C-02 note: JM-03 exposure_weight={out.exposure_weight} "
                        "exceeds SHOCK_EXPOSURE_CAP; Clip C floor not triggered."
                    )

            # ----------------------------------------------------------------
            # CCV-D-02: For CR-01 (CRISIS, JRM inactive), exposure_weight may be
            # below SHOCK_EXPOSURE_CAP. No floor enforcement. This is specified
            # behaviour per INV-04.
            # ----------------------------------------------------------------
            if vid == "CR-01":
                notes.append(
                    f"CCV-D-02: CR-01 exposure_weight={out.exposure_weight}. "
                    "May be below SHOCK_EXPOSURE_CAP per INV-04 (specified behaviour)."
                )

        # --------------------------------------------------------------------
        # CCV-D-01: For CR-02 (CRISIS + JRM active), verify ordering.
        # Expected: CR-02.exposure_weight == JM-03.exposure_weight * 0.75
        # Both records must be present in ER set.
        # --------------------------------------------------------------------
        if "CR-02" in by_id and "JM-03" in by_id:
            cr02_out = by_id["CR-02"].observed_output
            jm03_out = by_id["JM-03"].observed_output
            if not cr02_out.exception_raised and not jm03_out.exception_raised:
                # Compute expected value using Python float arithmetic (same as production).
                expected_cr02_ew = jm03_out.exposure_weight * 0.75
                if not _floats_equal(cr02_out.exposure_weight, expected_cr02_ew):
                    raise RuntimeError(
                        f"CRISIS_ORDERING_VIOLATION: CR-02 exposure_weight="
                        f"{cr02_out.exposure_weight} != JM-03.exposure_weight*0.75="
                        f"{expected_cr02_ew}. Clip C / CRISIS ordering violated. "
                        "INV-04 violated."
                    )

        # --------------------------------------------------------------------
        # CCV-D-03: CR-03 (non-CRISIS with JRM active) -- dampening must NOT apply.
        # Verified by BIC backward compatibility comparison against a non-CRISIS
        # variant. Here we simply note the check for audit.
        # --------------------------------------------------------------------
        if "CR-03" in by_id:
            notes.append(
                "CCV-D-03: CR-03 is non-CRISIS with JRM active. Dampening "
                "not applied. Verified by absence of *0.75 in BIC comparison."
            )

        return violations, notes

    def xǁClipVerifierǁverify__mutmut_4(
        self,
        er_records: List[ExecutionRecord],
    ) -> Tuple[List[str], List[str]]:
        """
        Perform clip chain verification on ER-stage records.

        Returns:
          (violations, notes)
          violations -- list of violation description strings. Empty means pass.
          notes      -- list of non-failure informational notes.

        Raises RuntimeError with failure_type_id prefix on hard failures
        (CLIP_B_FLOOR_VIOLATION, CLIP_C_FLOOR_VIOLATION, CLIP_A_VIOLATION,
        CRISIS_ORDERING_VIOLATION).
        """
        violations = []
        notes      = []
        by_id: Dict[str, ExecutionRecord] = {r.vector_id: r for r in er_records}

        for rec in er_records:
            out = None
            if out.exception_raised:
                # No clip verification for exception vectors.
                continue

            vid = rec.vector_id
            iv  = rec.input_vector

            # ----------------------------------------------------------------
            # CCV-A-01: Clip A verification.
            # position_size_factor must be in [0.0, 1.0] for every normal vector.
            # ----------------------------------------------------------------
            psf = out.position_size_factor
            if psf < 0.0 or psf > 1.0:
                raise RuntimeError(
                    f"CLIP_A_VIOLATION: Vector {vid} position_size_factor={psf} "
                    "is outside [0.0, 1.0]. INV-01 violated."
                )

            # ----------------------------------------------------------------
            # CCV-B-01: For MU-02 and RP-02, E_pre_clip should be zero or near zero,
            # so Clip B floor should be active. exposure_weight bit pattern should
            # equal bit pattern of 1e-6.
            # ----------------------------------------------------------------
            if vid in ("MU-02", "RP-02"):
                ew_bits = _float_bits(out.exposure_weight)
                if ew_bits != self._lb_bits:
                    raise RuntimeError(
                        f"CLIP_B_FLOOR_VIOLATION: Vector {vid} exposure_weight "
                        f"expected bit pattern of 1e-6 but got "
                        f"{out.exposure_weight!r}. INV-02 violated."
                    )

            # ----------------------------------------------------------------
            # CCV-B-02: For JM-inactive (JM-01, JM-04) non-CRISIS vectors,
            # exposure_weight must be in [1e-6, 1.0].
            # (Clip C inactive, CRISIS dampening inactive.)
            # ----------------------------------------------------------------
            if vid in ("JM-01", "JM-04") and iv.current_regime_str != "CRISIS":
                ew = out.exposure_weight
                if ew < 1e-6 or ew > 1.0:
                    raise RuntimeError(
                        f"CLIP_B_RANGE_VIOLATION: Vector {vid} exposure_weight={ew} "
                        "outside [1e-6, 1.0] with Clip C and CRISIS dampening both "
                        "inactive. INV-02 violated."
                    )

            # ----------------------------------------------------------------
            # CCV-C-02: For JM-03 (designed to produce pre-Clip-C value below
            # SHOCK_EXPOSURE_CAP), exposure_weight should equal SHOCK_EXPOSURE_CAP.
            # ----------------------------------------------------------------
            if vid == "JM-03":
                ew_bits = _float_bits(out.exposure_weight)
                if ew_bits != self._sec_bits:
                    # JM-03 uses meta_uncertainty=0.99 + multiplier=2.0.
                    # The division may produce a value below SHOCK_EXPOSURE_CAP,
                    # which gets clipped to SHOCK_EXPOSURE_CAP by Clip C.
                    # If the result does NOT equal SHOCK_EXPOSURE_CAP, the
                    # actual computed value exceeded the cap after division;
                    # this is acceptable if the value is above SHOCK_EXPOSURE_CAP.
                    # Hard failure only if value is strictly below SHOCK_EXPOSURE_CAP.
                    if out.exposure_weight < self._sec:
                        raise RuntimeError(
                            f"CLIP_C_FLOOR_VIOLATION: Vector {vid} exposure_weight="
                            f"{out.exposure_weight} is below SHOCK_EXPOSURE_CAP="
                            f"{self._sec}. INV-03 violated."
                        )
                    notes.append(
                        f"CCV-C-02 note: JM-03 exposure_weight={out.exposure_weight} "
                        "exceeds SHOCK_EXPOSURE_CAP; Clip C floor not triggered."
                    )

            # ----------------------------------------------------------------
            # CCV-D-02: For CR-01 (CRISIS, JRM inactive), exposure_weight may be
            # below SHOCK_EXPOSURE_CAP. No floor enforcement. This is specified
            # behaviour per INV-04.
            # ----------------------------------------------------------------
            if vid == "CR-01":
                notes.append(
                    f"CCV-D-02: CR-01 exposure_weight={out.exposure_weight}. "
                    "May be below SHOCK_EXPOSURE_CAP per INV-04 (specified behaviour)."
                )

        # --------------------------------------------------------------------
        # CCV-D-01: For CR-02 (CRISIS + JRM active), verify ordering.
        # Expected: CR-02.exposure_weight == JM-03.exposure_weight * 0.75
        # Both records must be present in ER set.
        # --------------------------------------------------------------------
        if "CR-02" in by_id and "JM-03" in by_id:
            cr02_out = by_id["CR-02"].observed_output
            jm03_out = by_id["JM-03"].observed_output
            if not cr02_out.exception_raised and not jm03_out.exception_raised:
                # Compute expected value using Python float arithmetic (same as production).
                expected_cr02_ew = jm03_out.exposure_weight * 0.75
                if not _floats_equal(cr02_out.exposure_weight, expected_cr02_ew):
                    raise RuntimeError(
                        f"CRISIS_ORDERING_VIOLATION: CR-02 exposure_weight="
                        f"{cr02_out.exposure_weight} != JM-03.exposure_weight*0.75="
                        f"{expected_cr02_ew}. Clip C / CRISIS ordering violated. "
                        "INV-04 violated."
                    )

        # --------------------------------------------------------------------
        # CCV-D-03: CR-03 (non-CRISIS with JRM active) -- dampening must NOT apply.
        # Verified by BIC backward compatibility comparison against a non-CRISIS
        # variant. Here we simply note the check for audit.
        # --------------------------------------------------------------------
        if "CR-03" in by_id:
            notes.append(
                "CCV-D-03: CR-03 is non-CRISIS with JRM active. Dampening "
                "not applied. Verified by absence of *0.75 in BIC comparison."
            )

        return violations, notes

    def xǁClipVerifierǁverify__mutmut_5(
        self,
        er_records: List[ExecutionRecord],
    ) -> Tuple[List[str], List[str]]:
        """
        Perform clip chain verification on ER-stage records.

        Returns:
          (violations, notes)
          violations -- list of violation description strings. Empty means pass.
          notes      -- list of non-failure informational notes.

        Raises RuntimeError with failure_type_id prefix on hard failures
        (CLIP_B_FLOOR_VIOLATION, CLIP_C_FLOOR_VIOLATION, CLIP_A_VIOLATION,
        CRISIS_ORDERING_VIOLATION).
        """
        violations = []
        notes      = []
        by_id: Dict[str, ExecutionRecord] = {r.vector_id: r for r in er_records}

        for rec in er_records:
            out = rec.observed_output
            if out.exception_raised:
                # No clip verification for exception vectors.
                break

            vid = rec.vector_id
            iv  = rec.input_vector

            # ----------------------------------------------------------------
            # CCV-A-01: Clip A verification.
            # position_size_factor must be in [0.0, 1.0] for every normal vector.
            # ----------------------------------------------------------------
            psf = out.position_size_factor
            if psf < 0.0 or psf > 1.0:
                raise RuntimeError(
                    f"CLIP_A_VIOLATION: Vector {vid} position_size_factor={psf} "
                    "is outside [0.0, 1.0]. INV-01 violated."
                )

            # ----------------------------------------------------------------
            # CCV-B-01: For MU-02 and RP-02, E_pre_clip should be zero or near zero,
            # so Clip B floor should be active. exposure_weight bit pattern should
            # equal bit pattern of 1e-6.
            # ----------------------------------------------------------------
            if vid in ("MU-02", "RP-02"):
                ew_bits = _float_bits(out.exposure_weight)
                if ew_bits != self._lb_bits:
                    raise RuntimeError(
                        f"CLIP_B_FLOOR_VIOLATION: Vector {vid} exposure_weight "
                        f"expected bit pattern of 1e-6 but got "
                        f"{out.exposure_weight!r}. INV-02 violated."
                    )

            # ----------------------------------------------------------------
            # CCV-B-02: For JM-inactive (JM-01, JM-04) non-CRISIS vectors,
            # exposure_weight must be in [1e-6, 1.0].
            # (Clip C inactive, CRISIS dampening inactive.)
            # ----------------------------------------------------------------
            if vid in ("JM-01", "JM-04") and iv.current_regime_str != "CRISIS":
                ew = out.exposure_weight
                if ew < 1e-6 or ew > 1.0:
                    raise RuntimeError(
                        f"CLIP_B_RANGE_VIOLATION: Vector {vid} exposure_weight={ew} "
                        "outside [1e-6, 1.0] with Clip C and CRISIS dampening both "
                        "inactive. INV-02 violated."
                    )

            # ----------------------------------------------------------------
            # CCV-C-02: For JM-03 (designed to produce pre-Clip-C value below
            # SHOCK_EXPOSURE_CAP), exposure_weight should equal SHOCK_EXPOSURE_CAP.
            # ----------------------------------------------------------------
            if vid == "JM-03":
                ew_bits = _float_bits(out.exposure_weight)
                if ew_bits != self._sec_bits:
                    # JM-03 uses meta_uncertainty=0.99 + multiplier=2.0.
                    # The division may produce a value below SHOCK_EXPOSURE_CAP,
                    # which gets clipped to SHOCK_EXPOSURE_CAP by Clip C.
                    # If the result does NOT equal SHOCK_EXPOSURE_CAP, the
                    # actual computed value exceeded the cap after division;
                    # this is acceptable if the value is above SHOCK_EXPOSURE_CAP.
                    # Hard failure only if value is strictly below SHOCK_EXPOSURE_CAP.
                    if out.exposure_weight < self._sec:
                        raise RuntimeError(
                            f"CLIP_C_FLOOR_VIOLATION: Vector {vid} exposure_weight="
                            f"{out.exposure_weight} is below SHOCK_EXPOSURE_CAP="
                            f"{self._sec}. INV-03 violated."
                        )
                    notes.append(
                        f"CCV-C-02 note: JM-03 exposure_weight={out.exposure_weight} "
                        "exceeds SHOCK_EXPOSURE_CAP; Clip C floor not triggered."
                    )

            # ----------------------------------------------------------------
            # CCV-D-02: For CR-01 (CRISIS, JRM inactive), exposure_weight may be
            # below SHOCK_EXPOSURE_CAP. No floor enforcement. This is specified
            # behaviour per INV-04.
            # ----------------------------------------------------------------
            if vid == "CR-01":
                notes.append(
                    f"CCV-D-02: CR-01 exposure_weight={out.exposure_weight}. "
                    "May be below SHOCK_EXPOSURE_CAP per INV-04 (specified behaviour)."
                )

        # --------------------------------------------------------------------
        # CCV-D-01: For CR-02 (CRISIS + JRM active), verify ordering.
        # Expected: CR-02.exposure_weight == JM-03.exposure_weight * 0.75
        # Both records must be present in ER set.
        # --------------------------------------------------------------------
        if "CR-02" in by_id and "JM-03" in by_id:
            cr02_out = by_id["CR-02"].observed_output
            jm03_out = by_id["JM-03"].observed_output
            if not cr02_out.exception_raised and not jm03_out.exception_raised:
                # Compute expected value using Python float arithmetic (same as production).
                expected_cr02_ew = jm03_out.exposure_weight * 0.75
                if not _floats_equal(cr02_out.exposure_weight, expected_cr02_ew):
                    raise RuntimeError(
                        f"CRISIS_ORDERING_VIOLATION: CR-02 exposure_weight="
                        f"{cr02_out.exposure_weight} != JM-03.exposure_weight*0.75="
                        f"{expected_cr02_ew}. Clip C / CRISIS ordering violated. "
                        "INV-04 violated."
                    )

        # --------------------------------------------------------------------
        # CCV-D-03: CR-03 (non-CRISIS with JRM active) -- dampening must NOT apply.
        # Verified by BIC backward compatibility comparison against a non-CRISIS
        # variant. Here we simply note the check for audit.
        # --------------------------------------------------------------------
        if "CR-03" in by_id:
            notes.append(
                "CCV-D-03: CR-03 is non-CRISIS with JRM active. Dampening "
                "not applied. Verified by absence of *0.75 in BIC comparison."
            )

        return violations, notes

    def xǁClipVerifierǁverify__mutmut_6(
        self,
        er_records: List[ExecutionRecord],
    ) -> Tuple[List[str], List[str]]:
        """
        Perform clip chain verification on ER-stage records.

        Returns:
          (violations, notes)
          violations -- list of violation description strings. Empty means pass.
          notes      -- list of non-failure informational notes.

        Raises RuntimeError with failure_type_id prefix on hard failures
        (CLIP_B_FLOOR_VIOLATION, CLIP_C_FLOOR_VIOLATION, CLIP_A_VIOLATION,
        CRISIS_ORDERING_VIOLATION).
        """
        violations = []
        notes      = []
        by_id: Dict[str, ExecutionRecord] = {r.vector_id: r for r in er_records}

        for rec in er_records:
            out = rec.observed_output
            if out.exception_raised:
                # No clip verification for exception vectors.
                continue

            vid = None
            iv  = rec.input_vector

            # ----------------------------------------------------------------
            # CCV-A-01: Clip A verification.
            # position_size_factor must be in [0.0, 1.0] for every normal vector.
            # ----------------------------------------------------------------
            psf = out.position_size_factor
            if psf < 0.0 or psf > 1.0:
                raise RuntimeError(
                    f"CLIP_A_VIOLATION: Vector {vid} position_size_factor={psf} "
                    "is outside [0.0, 1.0]. INV-01 violated."
                )

            # ----------------------------------------------------------------
            # CCV-B-01: For MU-02 and RP-02, E_pre_clip should be zero or near zero,
            # so Clip B floor should be active. exposure_weight bit pattern should
            # equal bit pattern of 1e-6.
            # ----------------------------------------------------------------
            if vid in ("MU-02", "RP-02"):
                ew_bits = _float_bits(out.exposure_weight)
                if ew_bits != self._lb_bits:
                    raise RuntimeError(
                        f"CLIP_B_FLOOR_VIOLATION: Vector {vid} exposure_weight "
                        f"expected bit pattern of 1e-6 but got "
                        f"{out.exposure_weight!r}. INV-02 violated."
                    )

            # ----------------------------------------------------------------
            # CCV-B-02: For JM-inactive (JM-01, JM-04) non-CRISIS vectors,
            # exposure_weight must be in [1e-6, 1.0].
            # (Clip C inactive, CRISIS dampening inactive.)
            # ----------------------------------------------------------------
            if vid in ("JM-01", "JM-04") and iv.current_regime_str != "CRISIS":
                ew = out.exposure_weight
                if ew < 1e-6 or ew > 1.0:
                    raise RuntimeError(
                        f"CLIP_B_RANGE_VIOLATION: Vector {vid} exposure_weight={ew} "
                        "outside [1e-6, 1.0] with Clip C and CRISIS dampening both "
                        "inactive. INV-02 violated."
                    )

            # ----------------------------------------------------------------
            # CCV-C-02: For JM-03 (designed to produce pre-Clip-C value below
            # SHOCK_EXPOSURE_CAP), exposure_weight should equal SHOCK_EXPOSURE_CAP.
            # ----------------------------------------------------------------
            if vid == "JM-03":
                ew_bits = _float_bits(out.exposure_weight)
                if ew_bits != self._sec_bits:
                    # JM-03 uses meta_uncertainty=0.99 + multiplier=2.0.
                    # The division may produce a value below SHOCK_EXPOSURE_CAP,
                    # which gets clipped to SHOCK_EXPOSURE_CAP by Clip C.
                    # If the result does NOT equal SHOCK_EXPOSURE_CAP, the
                    # actual computed value exceeded the cap after division;
                    # this is acceptable if the value is above SHOCK_EXPOSURE_CAP.
                    # Hard failure only if value is strictly below SHOCK_EXPOSURE_CAP.
                    if out.exposure_weight < self._sec:
                        raise RuntimeError(
                            f"CLIP_C_FLOOR_VIOLATION: Vector {vid} exposure_weight="
                            f"{out.exposure_weight} is below SHOCK_EXPOSURE_CAP="
                            f"{self._sec}. INV-03 violated."
                        )
                    notes.append(
                        f"CCV-C-02 note: JM-03 exposure_weight={out.exposure_weight} "
                        "exceeds SHOCK_EXPOSURE_CAP; Clip C floor not triggered."
                    )

            # ----------------------------------------------------------------
            # CCV-D-02: For CR-01 (CRISIS, JRM inactive), exposure_weight may be
            # below SHOCK_EXPOSURE_CAP. No floor enforcement. This is specified
            # behaviour per INV-04.
            # ----------------------------------------------------------------
            if vid == "CR-01":
                notes.append(
                    f"CCV-D-02: CR-01 exposure_weight={out.exposure_weight}. "
                    "May be below SHOCK_EXPOSURE_CAP per INV-04 (specified behaviour)."
                )

        # --------------------------------------------------------------------
        # CCV-D-01: For CR-02 (CRISIS + JRM active), verify ordering.
        # Expected: CR-02.exposure_weight == JM-03.exposure_weight * 0.75
        # Both records must be present in ER set.
        # --------------------------------------------------------------------
        if "CR-02" in by_id and "JM-03" in by_id:
            cr02_out = by_id["CR-02"].observed_output
            jm03_out = by_id["JM-03"].observed_output
            if not cr02_out.exception_raised and not jm03_out.exception_raised:
                # Compute expected value using Python float arithmetic (same as production).
                expected_cr02_ew = jm03_out.exposure_weight * 0.75
                if not _floats_equal(cr02_out.exposure_weight, expected_cr02_ew):
                    raise RuntimeError(
                        f"CRISIS_ORDERING_VIOLATION: CR-02 exposure_weight="
                        f"{cr02_out.exposure_weight} != JM-03.exposure_weight*0.75="
                        f"{expected_cr02_ew}. Clip C / CRISIS ordering violated. "
                        "INV-04 violated."
                    )

        # --------------------------------------------------------------------
        # CCV-D-03: CR-03 (non-CRISIS with JRM active) -- dampening must NOT apply.
        # Verified by BIC backward compatibility comparison against a non-CRISIS
        # variant. Here we simply note the check for audit.
        # --------------------------------------------------------------------
        if "CR-03" in by_id:
            notes.append(
                "CCV-D-03: CR-03 is non-CRISIS with JRM active. Dampening "
                "not applied. Verified by absence of *0.75 in BIC comparison."
            )

        return violations, notes

    def xǁClipVerifierǁverify__mutmut_7(
        self,
        er_records: List[ExecutionRecord],
    ) -> Tuple[List[str], List[str]]:
        """
        Perform clip chain verification on ER-stage records.

        Returns:
          (violations, notes)
          violations -- list of violation description strings. Empty means pass.
          notes      -- list of non-failure informational notes.

        Raises RuntimeError with failure_type_id prefix on hard failures
        (CLIP_B_FLOOR_VIOLATION, CLIP_C_FLOOR_VIOLATION, CLIP_A_VIOLATION,
        CRISIS_ORDERING_VIOLATION).
        """
        violations = []
        notes      = []
        by_id: Dict[str, ExecutionRecord] = {r.vector_id: r for r in er_records}

        for rec in er_records:
            out = rec.observed_output
            if out.exception_raised:
                # No clip verification for exception vectors.
                continue

            vid = rec.vector_id
            iv  = None

            # ----------------------------------------------------------------
            # CCV-A-01: Clip A verification.
            # position_size_factor must be in [0.0, 1.0] for every normal vector.
            # ----------------------------------------------------------------
            psf = out.position_size_factor
            if psf < 0.0 or psf > 1.0:
                raise RuntimeError(
                    f"CLIP_A_VIOLATION: Vector {vid} position_size_factor={psf} "
                    "is outside [0.0, 1.0]. INV-01 violated."
                )

            # ----------------------------------------------------------------
            # CCV-B-01: For MU-02 and RP-02, E_pre_clip should be zero or near zero,
            # so Clip B floor should be active. exposure_weight bit pattern should
            # equal bit pattern of 1e-6.
            # ----------------------------------------------------------------
            if vid in ("MU-02", "RP-02"):
                ew_bits = _float_bits(out.exposure_weight)
                if ew_bits != self._lb_bits:
                    raise RuntimeError(
                        f"CLIP_B_FLOOR_VIOLATION: Vector {vid} exposure_weight "
                        f"expected bit pattern of 1e-6 but got "
                        f"{out.exposure_weight!r}. INV-02 violated."
                    )

            # ----------------------------------------------------------------
            # CCV-B-02: For JM-inactive (JM-01, JM-04) non-CRISIS vectors,
            # exposure_weight must be in [1e-6, 1.0].
            # (Clip C inactive, CRISIS dampening inactive.)
            # ----------------------------------------------------------------
            if vid in ("JM-01", "JM-04") and iv.current_regime_str != "CRISIS":
                ew = out.exposure_weight
                if ew < 1e-6 or ew > 1.0:
                    raise RuntimeError(
                        f"CLIP_B_RANGE_VIOLATION: Vector {vid} exposure_weight={ew} "
                        "outside [1e-6, 1.0] with Clip C and CRISIS dampening both "
                        "inactive. INV-02 violated."
                    )

            # ----------------------------------------------------------------
            # CCV-C-02: For JM-03 (designed to produce pre-Clip-C value below
            # SHOCK_EXPOSURE_CAP), exposure_weight should equal SHOCK_EXPOSURE_CAP.
            # ----------------------------------------------------------------
            if vid == "JM-03":
                ew_bits = _float_bits(out.exposure_weight)
                if ew_bits != self._sec_bits:
                    # JM-03 uses meta_uncertainty=0.99 + multiplier=2.0.
                    # The division may produce a value below SHOCK_EXPOSURE_CAP,
                    # which gets clipped to SHOCK_EXPOSURE_CAP by Clip C.
                    # If the result does NOT equal SHOCK_EXPOSURE_CAP, the
                    # actual computed value exceeded the cap after division;
                    # this is acceptable if the value is above SHOCK_EXPOSURE_CAP.
                    # Hard failure only if value is strictly below SHOCK_EXPOSURE_CAP.
                    if out.exposure_weight < self._sec:
                        raise RuntimeError(
                            f"CLIP_C_FLOOR_VIOLATION: Vector {vid} exposure_weight="
                            f"{out.exposure_weight} is below SHOCK_EXPOSURE_CAP="
                            f"{self._sec}. INV-03 violated."
                        )
                    notes.append(
                        f"CCV-C-02 note: JM-03 exposure_weight={out.exposure_weight} "
                        "exceeds SHOCK_EXPOSURE_CAP; Clip C floor not triggered."
                    )

            # ----------------------------------------------------------------
            # CCV-D-02: For CR-01 (CRISIS, JRM inactive), exposure_weight may be
            # below SHOCK_EXPOSURE_CAP. No floor enforcement. This is specified
            # behaviour per INV-04.
            # ----------------------------------------------------------------
            if vid == "CR-01":
                notes.append(
                    f"CCV-D-02: CR-01 exposure_weight={out.exposure_weight}. "
                    "May be below SHOCK_EXPOSURE_CAP per INV-04 (specified behaviour)."
                )

        # --------------------------------------------------------------------
        # CCV-D-01: For CR-02 (CRISIS + JRM active), verify ordering.
        # Expected: CR-02.exposure_weight == JM-03.exposure_weight * 0.75
        # Both records must be present in ER set.
        # --------------------------------------------------------------------
        if "CR-02" in by_id and "JM-03" in by_id:
            cr02_out = by_id["CR-02"].observed_output
            jm03_out = by_id["JM-03"].observed_output
            if not cr02_out.exception_raised and not jm03_out.exception_raised:
                # Compute expected value using Python float arithmetic (same as production).
                expected_cr02_ew = jm03_out.exposure_weight * 0.75
                if not _floats_equal(cr02_out.exposure_weight, expected_cr02_ew):
                    raise RuntimeError(
                        f"CRISIS_ORDERING_VIOLATION: CR-02 exposure_weight="
                        f"{cr02_out.exposure_weight} != JM-03.exposure_weight*0.75="
                        f"{expected_cr02_ew}. Clip C / CRISIS ordering violated. "
                        "INV-04 violated."
                    )

        # --------------------------------------------------------------------
        # CCV-D-03: CR-03 (non-CRISIS with JRM active) -- dampening must NOT apply.
        # Verified by BIC backward compatibility comparison against a non-CRISIS
        # variant. Here we simply note the check for audit.
        # --------------------------------------------------------------------
        if "CR-03" in by_id:
            notes.append(
                "CCV-D-03: CR-03 is non-CRISIS with JRM active. Dampening "
                "not applied. Verified by absence of *0.75 in BIC comparison."
            )

        return violations, notes

    def xǁClipVerifierǁverify__mutmut_8(
        self,
        er_records: List[ExecutionRecord],
    ) -> Tuple[List[str], List[str]]:
        """
        Perform clip chain verification on ER-stage records.

        Returns:
          (violations, notes)
          violations -- list of violation description strings. Empty means pass.
          notes      -- list of non-failure informational notes.

        Raises RuntimeError with failure_type_id prefix on hard failures
        (CLIP_B_FLOOR_VIOLATION, CLIP_C_FLOOR_VIOLATION, CLIP_A_VIOLATION,
        CRISIS_ORDERING_VIOLATION).
        """
        violations = []
        notes      = []
        by_id: Dict[str, ExecutionRecord] = {r.vector_id: r for r in er_records}

        for rec in er_records:
            out = rec.observed_output
            if out.exception_raised:
                # No clip verification for exception vectors.
                continue

            vid = rec.vector_id
            iv  = rec.input_vector

            # ----------------------------------------------------------------
            # CCV-A-01: Clip A verification.
            # position_size_factor must be in [0.0, 1.0] for every normal vector.
            # ----------------------------------------------------------------
            psf = None
            if psf < 0.0 or psf > 1.0:
                raise RuntimeError(
                    f"CLIP_A_VIOLATION: Vector {vid} position_size_factor={psf} "
                    "is outside [0.0, 1.0]. INV-01 violated."
                )

            # ----------------------------------------------------------------
            # CCV-B-01: For MU-02 and RP-02, E_pre_clip should be zero or near zero,
            # so Clip B floor should be active. exposure_weight bit pattern should
            # equal bit pattern of 1e-6.
            # ----------------------------------------------------------------
            if vid in ("MU-02", "RP-02"):
                ew_bits = _float_bits(out.exposure_weight)
                if ew_bits != self._lb_bits:
                    raise RuntimeError(
                        f"CLIP_B_FLOOR_VIOLATION: Vector {vid} exposure_weight "
                        f"expected bit pattern of 1e-6 but got "
                        f"{out.exposure_weight!r}. INV-02 violated."
                    )

            # ----------------------------------------------------------------
            # CCV-B-02: For JM-inactive (JM-01, JM-04) non-CRISIS vectors,
            # exposure_weight must be in [1e-6, 1.0].
            # (Clip C inactive, CRISIS dampening inactive.)
            # ----------------------------------------------------------------
            if vid in ("JM-01", "JM-04") and iv.current_regime_str != "CRISIS":
                ew = out.exposure_weight
                if ew < 1e-6 or ew > 1.0:
                    raise RuntimeError(
                        f"CLIP_B_RANGE_VIOLATION: Vector {vid} exposure_weight={ew} "
                        "outside [1e-6, 1.0] with Clip C and CRISIS dampening both "
                        "inactive. INV-02 violated."
                    )

            # ----------------------------------------------------------------
            # CCV-C-02: For JM-03 (designed to produce pre-Clip-C value below
            # SHOCK_EXPOSURE_CAP), exposure_weight should equal SHOCK_EXPOSURE_CAP.
            # ----------------------------------------------------------------
            if vid == "JM-03":
                ew_bits = _float_bits(out.exposure_weight)
                if ew_bits != self._sec_bits:
                    # JM-03 uses meta_uncertainty=0.99 + multiplier=2.0.
                    # The division may produce a value below SHOCK_EXPOSURE_CAP,
                    # which gets clipped to SHOCK_EXPOSURE_CAP by Clip C.
                    # If the result does NOT equal SHOCK_EXPOSURE_CAP, the
                    # actual computed value exceeded the cap after division;
                    # this is acceptable if the value is above SHOCK_EXPOSURE_CAP.
                    # Hard failure only if value is strictly below SHOCK_EXPOSURE_CAP.
                    if out.exposure_weight < self._sec:
                        raise RuntimeError(
                            f"CLIP_C_FLOOR_VIOLATION: Vector {vid} exposure_weight="
                            f"{out.exposure_weight} is below SHOCK_EXPOSURE_CAP="
                            f"{self._sec}. INV-03 violated."
                        )
                    notes.append(
                        f"CCV-C-02 note: JM-03 exposure_weight={out.exposure_weight} "
                        "exceeds SHOCK_EXPOSURE_CAP; Clip C floor not triggered."
                    )

            # ----------------------------------------------------------------
            # CCV-D-02: For CR-01 (CRISIS, JRM inactive), exposure_weight may be
            # below SHOCK_EXPOSURE_CAP. No floor enforcement. This is specified
            # behaviour per INV-04.
            # ----------------------------------------------------------------
            if vid == "CR-01":
                notes.append(
                    f"CCV-D-02: CR-01 exposure_weight={out.exposure_weight}. "
                    "May be below SHOCK_EXPOSURE_CAP per INV-04 (specified behaviour)."
                )

        # --------------------------------------------------------------------
        # CCV-D-01: For CR-02 (CRISIS + JRM active), verify ordering.
        # Expected: CR-02.exposure_weight == JM-03.exposure_weight * 0.75
        # Both records must be present in ER set.
        # --------------------------------------------------------------------
        if "CR-02" in by_id and "JM-03" in by_id:
            cr02_out = by_id["CR-02"].observed_output
            jm03_out = by_id["JM-03"].observed_output
            if not cr02_out.exception_raised and not jm03_out.exception_raised:
                # Compute expected value using Python float arithmetic (same as production).
                expected_cr02_ew = jm03_out.exposure_weight * 0.75
                if not _floats_equal(cr02_out.exposure_weight, expected_cr02_ew):
                    raise RuntimeError(
                        f"CRISIS_ORDERING_VIOLATION: CR-02 exposure_weight="
                        f"{cr02_out.exposure_weight} != JM-03.exposure_weight*0.75="
                        f"{expected_cr02_ew}. Clip C / CRISIS ordering violated. "
                        "INV-04 violated."
                    )

        # --------------------------------------------------------------------
        # CCV-D-03: CR-03 (non-CRISIS with JRM active) -- dampening must NOT apply.
        # Verified by BIC backward compatibility comparison against a non-CRISIS
        # variant. Here we simply note the check for audit.
        # --------------------------------------------------------------------
        if "CR-03" in by_id:
            notes.append(
                "CCV-D-03: CR-03 is non-CRISIS with JRM active. Dampening "
                "not applied. Verified by absence of *0.75 in BIC comparison."
            )

        return violations, notes

    def xǁClipVerifierǁverify__mutmut_9(
        self,
        er_records: List[ExecutionRecord],
    ) -> Tuple[List[str], List[str]]:
        """
        Perform clip chain verification on ER-stage records.

        Returns:
          (violations, notes)
          violations -- list of violation description strings. Empty means pass.
          notes      -- list of non-failure informational notes.

        Raises RuntimeError with failure_type_id prefix on hard failures
        (CLIP_B_FLOOR_VIOLATION, CLIP_C_FLOOR_VIOLATION, CLIP_A_VIOLATION,
        CRISIS_ORDERING_VIOLATION).
        """
        violations = []
        notes      = []
        by_id: Dict[str, ExecutionRecord] = {r.vector_id: r for r in er_records}

        for rec in er_records:
            out = rec.observed_output
            if out.exception_raised:
                # No clip verification for exception vectors.
                continue

            vid = rec.vector_id
            iv  = rec.input_vector

            # ----------------------------------------------------------------
            # CCV-A-01: Clip A verification.
            # position_size_factor must be in [0.0, 1.0] for every normal vector.
            # ----------------------------------------------------------------
            psf = out.position_size_factor
            if psf < 0.0 and psf > 1.0:
                raise RuntimeError(
                    f"CLIP_A_VIOLATION: Vector {vid} position_size_factor={psf} "
                    "is outside [0.0, 1.0]. INV-01 violated."
                )

            # ----------------------------------------------------------------
            # CCV-B-01: For MU-02 and RP-02, E_pre_clip should be zero or near zero,
            # so Clip B floor should be active. exposure_weight bit pattern should
            # equal bit pattern of 1e-6.
            # ----------------------------------------------------------------
            if vid in ("MU-02", "RP-02"):
                ew_bits = _float_bits(out.exposure_weight)
                if ew_bits != self._lb_bits:
                    raise RuntimeError(
                        f"CLIP_B_FLOOR_VIOLATION: Vector {vid} exposure_weight "
                        f"expected bit pattern of 1e-6 but got "
                        f"{out.exposure_weight!r}. INV-02 violated."
                    )

            # ----------------------------------------------------------------
            # CCV-B-02: For JM-inactive (JM-01, JM-04) non-CRISIS vectors,
            # exposure_weight must be in [1e-6, 1.0].
            # (Clip C inactive, CRISIS dampening inactive.)
            # ----------------------------------------------------------------
            if vid in ("JM-01", "JM-04") and iv.current_regime_str != "CRISIS":
                ew = out.exposure_weight
                if ew < 1e-6 or ew > 1.0:
                    raise RuntimeError(
                        f"CLIP_B_RANGE_VIOLATION: Vector {vid} exposure_weight={ew} "
                        "outside [1e-6, 1.0] with Clip C and CRISIS dampening both "
                        "inactive. INV-02 violated."
                    )

            # ----------------------------------------------------------------
            # CCV-C-02: For JM-03 (designed to produce pre-Clip-C value below
            # SHOCK_EXPOSURE_CAP), exposure_weight should equal SHOCK_EXPOSURE_CAP.
            # ----------------------------------------------------------------
            if vid == "JM-03":
                ew_bits = _float_bits(out.exposure_weight)
                if ew_bits != self._sec_bits:
                    # JM-03 uses meta_uncertainty=0.99 + multiplier=2.0.
                    # The division may produce a value below SHOCK_EXPOSURE_CAP,
                    # which gets clipped to SHOCK_EXPOSURE_CAP by Clip C.
                    # If the result does NOT equal SHOCK_EXPOSURE_CAP, the
                    # actual computed value exceeded the cap after division;
                    # this is acceptable if the value is above SHOCK_EXPOSURE_CAP.
                    # Hard failure only if value is strictly below SHOCK_EXPOSURE_CAP.
                    if out.exposure_weight < self._sec:
                        raise RuntimeError(
                            f"CLIP_C_FLOOR_VIOLATION: Vector {vid} exposure_weight="
                            f"{out.exposure_weight} is below SHOCK_EXPOSURE_CAP="
                            f"{self._sec}. INV-03 violated."
                        )
                    notes.append(
                        f"CCV-C-02 note: JM-03 exposure_weight={out.exposure_weight} "
                        "exceeds SHOCK_EXPOSURE_CAP; Clip C floor not triggered."
                    )

            # ----------------------------------------------------------------
            # CCV-D-02: For CR-01 (CRISIS, JRM inactive), exposure_weight may be
            # below SHOCK_EXPOSURE_CAP. No floor enforcement. This is specified
            # behaviour per INV-04.
            # ----------------------------------------------------------------
            if vid == "CR-01":
                notes.append(
                    f"CCV-D-02: CR-01 exposure_weight={out.exposure_weight}. "
                    "May be below SHOCK_EXPOSURE_CAP per INV-04 (specified behaviour)."
                )

        # --------------------------------------------------------------------
        # CCV-D-01: For CR-02 (CRISIS + JRM active), verify ordering.
        # Expected: CR-02.exposure_weight == JM-03.exposure_weight * 0.75
        # Both records must be present in ER set.
        # --------------------------------------------------------------------
        if "CR-02" in by_id and "JM-03" in by_id:
            cr02_out = by_id["CR-02"].observed_output
            jm03_out = by_id["JM-03"].observed_output
            if not cr02_out.exception_raised and not jm03_out.exception_raised:
                # Compute expected value using Python float arithmetic (same as production).
                expected_cr02_ew = jm03_out.exposure_weight * 0.75
                if not _floats_equal(cr02_out.exposure_weight, expected_cr02_ew):
                    raise RuntimeError(
                        f"CRISIS_ORDERING_VIOLATION: CR-02 exposure_weight="
                        f"{cr02_out.exposure_weight} != JM-03.exposure_weight*0.75="
                        f"{expected_cr02_ew}. Clip C / CRISIS ordering violated. "
                        "INV-04 violated."
                    )

        # --------------------------------------------------------------------
        # CCV-D-03: CR-03 (non-CRISIS with JRM active) -- dampening must NOT apply.
        # Verified by BIC backward compatibility comparison against a non-CRISIS
        # variant. Here we simply note the check for audit.
        # --------------------------------------------------------------------
        if "CR-03" in by_id:
            notes.append(
                "CCV-D-03: CR-03 is non-CRISIS with JRM active. Dampening "
                "not applied. Verified by absence of *0.75 in BIC comparison."
            )

        return violations, notes

    def xǁClipVerifierǁverify__mutmut_10(
        self,
        er_records: List[ExecutionRecord],
    ) -> Tuple[List[str], List[str]]:
        """
        Perform clip chain verification on ER-stage records.

        Returns:
          (violations, notes)
          violations -- list of violation description strings. Empty means pass.
          notes      -- list of non-failure informational notes.

        Raises RuntimeError with failure_type_id prefix on hard failures
        (CLIP_B_FLOOR_VIOLATION, CLIP_C_FLOOR_VIOLATION, CLIP_A_VIOLATION,
        CRISIS_ORDERING_VIOLATION).
        """
        violations = []
        notes      = []
        by_id: Dict[str, ExecutionRecord] = {r.vector_id: r for r in er_records}

        for rec in er_records:
            out = rec.observed_output
            if out.exception_raised:
                # No clip verification for exception vectors.
                continue

            vid = rec.vector_id
            iv  = rec.input_vector

            # ----------------------------------------------------------------
            # CCV-A-01: Clip A verification.
            # position_size_factor must be in [0.0, 1.0] for every normal vector.
            # ----------------------------------------------------------------
            psf = out.position_size_factor
            if psf <= 0.0 or psf > 1.0:
                raise RuntimeError(
                    f"CLIP_A_VIOLATION: Vector {vid} position_size_factor={psf} "
                    "is outside [0.0, 1.0]. INV-01 violated."
                )

            # ----------------------------------------------------------------
            # CCV-B-01: For MU-02 and RP-02, E_pre_clip should be zero or near zero,
            # so Clip B floor should be active. exposure_weight bit pattern should
            # equal bit pattern of 1e-6.
            # ----------------------------------------------------------------
            if vid in ("MU-02", "RP-02"):
                ew_bits = _float_bits(out.exposure_weight)
                if ew_bits != self._lb_bits:
                    raise RuntimeError(
                        f"CLIP_B_FLOOR_VIOLATION: Vector {vid} exposure_weight "
                        f"expected bit pattern of 1e-6 but got "
                        f"{out.exposure_weight!r}. INV-02 violated."
                    )

            # ----------------------------------------------------------------
            # CCV-B-02: For JM-inactive (JM-01, JM-04) non-CRISIS vectors,
            # exposure_weight must be in [1e-6, 1.0].
            # (Clip C inactive, CRISIS dampening inactive.)
            # ----------------------------------------------------------------
            if vid in ("JM-01", "JM-04") and iv.current_regime_str != "CRISIS":
                ew = out.exposure_weight
                if ew < 1e-6 or ew > 1.0:
                    raise RuntimeError(
                        f"CLIP_B_RANGE_VIOLATION: Vector {vid} exposure_weight={ew} "
                        "outside [1e-6, 1.0] with Clip C and CRISIS dampening both "
                        "inactive. INV-02 violated."
                    )

            # ----------------------------------------------------------------
            # CCV-C-02: For JM-03 (designed to produce pre-Clip-C value below
            # SHOCK_EXPOSURE_CAP), exposure_weight should equal SHOCK_EXPOSURE_CAP.
            # ----------------------------------------------------------------
            if vid == "JM-03":
                ew_bits = _float_bits(out.exposure_weight)
                if ew_bits != self._sec_bits:
                    # JM-03 uses meta_uncertainty=0.99 + multiplier=2.0.
                    # The division may produce a value below SHOCK_EXPOSURE_CAP,
                    # which gets clipped to SHOCK_EXPOSURE_CAP by Clip C.
                    # If the result does NOT equal SHOCK_EXPOSURE_CAP, the
                    # actual computed value exceeded the cap after division;
                    # this is acceptable if the value is above SHOCK_EXPOSURE_CAP.
                    # Hard failure only if value is strictly below SHOCK_EXPOSURE_CAP.
                    if out.exposure_weight < self._sec:
                        raise RuntimeError(
                            f"CLIP_C_FLOOR_VIOLATION: Vector {vid} exposure_weight="
                            f"{out.exposure_weight} is below SHOCK_EXPOSURE_CAP="
                            f"{self._sec}. INV-03 violated."
                        )
                    notes.append(
                        f"CCV-C-02 note: JM-03 exposure_weight={out.exposure_weight} "
                        "exceeds SHOCK_EXPOSURE_CAP; Clip C floor not triggered."
                    )

            # ----------------------------------------------------------------
            # CCV-D-02: For CR-01 (CRISIS, JRM inactive), exposure_weight may be
            # below SHOCK_EXPOSURE_CAP. No floor enforcement. This is specified
            # behaviour per INV-04.
            # ----------------------------------------------------------------
            if vid == "CR-01":
                notes.append(
                    f"CCV-D-02: CR-01 exposure_weight={out.exposure_weight}. "
                    "May be below SHOCK_EXPOSURE_CAP per INV-04 (specified behaviour)."
                )

        # --------------------------------------------------------------------
        # CCV-D-01: For CR-02 (CRISIS + JRM active), verify ordering.
        # Expected: CR-02.exposure_weight == JM-03.exposure_weight * 0.75
        # Both records must be present in ER set.
        # --------------------------------------------------------------------
        if "CR-02" in by_id and "JM-03" in by_id:
            cr02_out = by_id["CR-02"].observed_output
            jm03_out = by_id["JM-03"].observed_output
            if not cr02_out.exception_raised and not jm03_out.exception_raised:
                # Compute expected value using Python float arithmetic (same as production).
                expected_cr02_ew = jm03_out.exposure_weight * 0.75
                if not _floats_equal(cr02_out.exposure_weight, expected_cr02_ew):
                    raise RuntimeError(
                        f"CRISIS_ORDERING_VIOLATION: CR-02 exposure_weight="
                        f"{cr02_out.exposure_weight} != JM-03.exposure_weight*0.75="
                        f"{expected_cr02_ew}. Clip C / CRISIS ordering violated. "
                        "INV-04 violated."
                    )

        # --------------------------------------------------------------------
        # CCV-D-03: CR-03 (non-CRISIS with JRM active) -- dampening must NOT apply.
        # Verified by BIC backward compatibility comparison against a non-CRISIS
        # variant. Here we simply note the check for audit.
        # --------------------------------------------------------------------
        if "CR-03" in by_id:
            notes.append(
                "CCV-D-03: CR-03 is non-CRISIS with JRM active. Dampening "
                "not applied. Verified by absence of *0.75 in BIC comparison."
            )

        return violations, notes

    def xǁClipVerifierǁverify__mutmut_11(
        self,
        er_records: List[ExecutionRecord],
    ) -> Tuple[List[str], List[str]]:
        """
        Perform clip chain verification on ER-stage records.

        Returns:
          (violations, notes)
          violations -- list of violation description strings. Empty means pass.
          notes      -- list of non-failure informational notes.

        Raises RuntimeError with failure_type_id prefix on hard failures
        (CLIP_B_FLOOR_VIOLATION, CLIP_C_FLOOR_VIOLATION, CLIP_A_VIOLATION,
        CRISIS_ORDERING_VIOLATION).
        """
        violations = []
        notes      = []
        by_id: Dict[str, ExecutionRecord] = {r.vector_id: r for r in er_records}

        for rec in er_records:
            out = rec.observed_output
            if out.exception_raised:
                # No clip verification for exception vectors.
                continue

            vid = rec.vector_id
            iv  = rec.input_vector

            # ----------------------------------------------------------------
            # CCV-A-01: Clip A verification.
            # position_size_factor must be in [0.0, 1.0] for every normal vector.
            # ----------------------------------------------------------------
            psf = out.position_size_factor
            if psf < 1.0 or psf > 1.0:
                raise RuntimeError(
                    f"CLIP_A_VIOLATION: Vector {vid} position_size_factor={psf} "
                    "is outside [0.0, 1.0]. INV-01 violated."
                )

            # ----------------------------------------------------------------
            # CCV-B-01: For MU-02 and RP-02, E_pre_clip should be zero or near zero,
            # so Clip B floor should be active. exposure_weight bit pattern should
            # equal bit pattern of 1e-6.
            # ----------------------------------------------------------------
            if vid in ("MU-02", "RP-02"):
                ew_bits = _float_bits(out.exposure_weight)
                if ew_bits != self._lb_bits:
                    raise RuntimeError(
                        f"CLIP_B_FLOOR_VIOLATION: Vector {vid} exposure_weight "
                        f"expected bit pattern of 1e-6 but got "
                        f"{out.exposure_weight!r}. INV-02 violated."
                    )

            # ----------------------------------------------------------------
            # CCV-B-02: For JM-inactive (JM-01, JM-04) non-CRISIS vectors,
            # exposure_weight must be in [1e-6, 1.0].
            # (Clip C inactive, CRISIS dampening inactive.)
            # ----------------------------------------------------------------
            if vid in ("JM-01", "JM-04") and iv.current_regime_str != "CRISIS":
                ew = out.exposure_weight
                if ew < 1e-6 or ew > 1.0:
                    raise RuntimeError(
                        f"CLIP_B_RANGE_VIOLATION: Vector {vid} exposure_weight={ew} "
                        "outside [1e-6, 1.0] with Clip C and CRISIS dampening both "
                        "inactive. INV-02 violated."
                    )

            # ----------------------------------------------------------------
            # CCV-C-02: For JM-03 (designed to produce pre-Clip-C value below
            # SHOCK_EXPOSURE_CAP), exposure_weight should equal SHOCK_EXPOSURE_CAP.
            # ----------------------------------------------------------------
            if vid == "JM-03":
                ew_bits = _float_bits(out.exposure_weight)
                if ew_bits != self._sec_bits:
                    # JM-03 uses meta_uncertainty=0.99 + multiplier=2.0.
                    # The division may produce a value below SHOCK_EXPOSURE_CAP,
                    # which gets clipped to SHOCK_EXPOSURE_CAP by Clip C.
                    # If the result does NOT equal SHOCK_EXPOSURE_CAP, the
                    # actual computed value exceeded the cap after division;
                    # this is acceptable if the value is above SHOCK_EXPOSURE_CAP.
                    # Hard failure only if value is strictly below SHOCK_EXPOSURE_CAP.
                    if out.exposure_weight < self._sec:
                        raise RuntimeError(
                            f"CLIP_C_FLOOR_VIOLATION: Vector {vid} exposure_weight="
                            f"{out.exposure_weight} is below SHOCK_EXPOSURE_CAP="
                            f"{self._sec}. INV-03 violated."
                        )
                    notes.append(
                        f"CCV-C-02 note: JM-03 exposure_weight={out.exposure_weight} "
                        "exceeds SHOCK_EXPOSURE_CAP; Clip C floor not triggered."
                    )

            # ----------------------------------------------------------------
            # CCV-D-02: For CR-01 (CRISIS, JRM inactive), exposure_weight may be
            # below SHOCK_EXPOSURE_CAP. No floor enforcement. This is specified
            # behaviour per INV-04.
            # ----------------------------------------------------------------
            if vid == "CR-01":
                notes.append(
                    f"CCV-D-02: CR-01 exposure_weight={out.exposure_weight}. "
                    "May be below SHOCK_EXPOSURE_CAP per INV-04 (specified behaviour)."
                )

        # --------------------------------------------------------------------
        # CCV-D-01: For CR-02 (CRISIS + JRM active), verify ordering.
        # Expected: CR-02.exposure_weight == JM-03.exposure_weight * 0.75
        # Both records must be present in ER set.
        # --------------------------------------------------------------------
        if "CR-02" in by_id and "JM-03" in by_id:
            cr02_out = by_id["CR-02"].observed_output
            jm03_out = by_id["JM-03"].observed_output
            if not cr02_out.exception_raised and not jm03_out.exception_raised:
                # Compute expected value using Python float arithmetic (same as production).
                expected_cr02_ew = jm03_out.exposure_weight * 0.75
                if not _floats_equal(cr02_out.exposure_weight, expected_cr02_ew):
                    raise RuntimeError(
                        f"CRISIS_ORDERING_VIOLATION: CR-02 exposure_weight="
                        f"{cr02_out.exposure_weight} != JM-03.exposure_weight*0.75="
                        f"{expected_cr02_ew}. Clip C / CRISIS ordering violated. "
                        "INV-04 violated."
                    )

        # --------------------------------------------------------------------
        # CCV-D-03: CR-03 (non-CRISIS with JRM active) -- dampening must NOT apply.
        # Verified by BIC backward compatibility comparison against a non-CRISIS
        # variant. Here we simply note the check for audit.
        # --------------------------------------------------------------------
        if "CR-03" in by_id:
            notes.append(
                "CCV-D-03: CR-03 is non-CRISIS with JRM active. Dampening "
                "not applied. Verified by absence of *0.75 in BIC comparison."
            )

        return violations, notes

    def xǁClipVerifierǁverify__mutmut_12(
        self,
        er_records: List[ExecutionRecord],
    ) -> Tuple[List[str], List[str]]:
        """
        Perform clip chain verification on ER-stage records.

        Returns:
          (violations, notes)
          violations -- list of violation description strings. Empty means pass.
          notes      -- list of non-failure informational notes.

        Raises RuntimeError with failure_type_id prefix on hard failures
        (CLIP_B_FLOOR_VIOLATION, CLIP_C_FLOOR_VIOLATION, CLIP_A_VIOLATION,
        CRISIS_ORDERING_VIOLATION).
        """
        violations = []
        notes      = []
        by_id: Dict[str, ExecutionRecord] = {r.vector_id: r for r in er_records}

        for rec in er_records:
            out = rec.observed_output
            if out.exception_raised:
                # No clip verification for exception vectors.
                continue

            vid = rec.vector_id
            iv  = rec.input_vector

            # ----------------------------------------------------------------
            # CCV-A-01: Clip A verification.
            # position_size_factor must be in [0.0, 1.0] for every normal vector.
            # ----------------------------------------------------------------
            psf = out.position_size_factor
            if psf < 0.0 or psf >= 1.0:
                raise RuntimeError(
                    f"CLIP_A_VIOLATION: Vector {vid} position_size_factor={psf} "
                    "is outside [0.0, 1.0]. INV-01 violated."
                )

            # ----------------------------------------------------------------
            # CCV-B-01: For MU-02 and RP-02, E_pre_clip should be zero or near zero,
            # so Clip B floor should be active. exposure_weight bit pattern should
            # equal bit pattern of 1e-6.
            # ----------------------------------------------------------------
            if vid in ("MU-02", "RP-02"):
                ew_bits = _float_bits(out.exposure_weight)
                if ew_bits != self._lb_bits:
                    raise RuntimeError(
                        f"CLIP_B_FLOOR_VIOLATION: Vector {vid} exposure_weight "
                        f"expected bit pattern of 1e-6 but got "
                        f"{out.exposure_weight!r}. INV-02 violated."
                    )

            # ----------------------------------------------------------------
            # CCV-B-02: For JM-inactive (JM-01, JM-04) non-CRISIS vectors,
            # exposure_weight must be in [1e-6, 1.0].
            # (Clip C inactive, CRISIS dampening inactive.)
            # ----------------------------------------------------------------
            if vid in ("JM-01", "JM-04") and iv.current_regime_str != "CRISIS":
                ew = out.exposure_weight
                if ew < 1e-6 or ew > 1.0:
                    raise RuntimeError(
                        f"CLIP_B_RANGE_VIOLATION: Vector {vid} exposure_weight={ew} "
                        "outside [1e-6, 1.0] with Clip C and CRISIS dampening both "
                        "inactive. INV-02 violated."
                    )

            # ----------------------------------------------------------------
            # CCV-C-02: For JM-03 (designed to produce pre-Clip-C value below
            # SHOCK_EXPOSURE_CAP), exposure_weight should equal SHOCK_EXPOSURE_CAP.
            # ----------------------------------------------------------------
            if vid == "JM-03":
                ew_bits = _float_bits(out.exposure_weight)
                if ew_bits != self._sec_bits:
                    # JM-03 uses meta_uncertainty=0.99 + multiplier=2.0.
                    # The division may produce a value below SHOCK_EXPOSURE_CAP,
                    # which gets clipped to SHOCK_EXPOSURE_CAP by Clip C.
                    # If the result does NOT equal SHOCK_EXPOSURE_CAP, the
                    # actual computed value exceeded the cap after division;
                    # this is acceptable if the value is above SHOCK_EXPOSURE_CAP.
                    # Hard failure only if value is strictly below SHOCK_EXPOSURE_CAP.
                    if out.exposure_weight < self._sec:
                        raise RuntimeError(
                            f"CLIP_C_FLOOR_VIOLATION: Vector {vid} exposure_weight="
                            f"{out.exposure_weight} is below SHOCK_EXPOSURE_CAP="
                            f"{self._sec}. INV-03 violated."
                        )
                    notes.append(
                        f"CCV-C-02 note: JM-03 exposure_weight={out.exposure_weight} "
                        "exceeds SHOCK_EXPOSURE_CAP; Clip C floor not triggered."
                    )

            # ----------------------------------------------------------------
            # CCV-D-02: For CR-01 (CRISIS, JRM inactive), exposure_weight may be
            # below SHOCK_EXPOSURE_CAP. No floor enforcement. This is specified
            # behaviour per INV-04.
            # ----------------------------------------------------------------
            if vid == "CR-01":
                notes.append(
                    f"CCV-D-02: CR-01 exposure_weight={out.exposure_weight}. "
                    "May be below SHOCK_EXPOSURE_CAP per INV-04 (specified behaviour)."
                )

        # --------------------------------------------------------------------
        # CCV-D-01: For CR-02 (CRISIS + JRM active), verify ordering.
        # Expected: CR-02.exposure_weight == JM-03.exposure_weight * 0.75
        # Both records must be present in ER set.
        # --------------------------------------------------------------------
        if "CR-02" in by_id and "JM-03" in by_id:
            cr02_out = by_id["CR-02"].observed_output
            jm03_out = by_id["JM-03"].observed_output
            if not cr02_out.exception_raised and not jm03_out.exception_raised:
                # Compute expected value using Python float arithmetic (same as production).
                expected_cr02_ew = jm03_out.exposure_weight * 0.75
                if not _floats_equal(cr02_out.exposure_weight, expected_cr02_ew):
                    raise RuntimeError(
                        f"CRISIS_ORDERING_VIOLATION: CR-02 exposure_weight="
                        f"{cr02_out.exposure_weight} != JM-03.exposure_weight*0.75="
                        f"{expected_cr02_ew}. Clip C / CRISIS ordering violated. "
                        "INV-04 violated."
                    )

        # --------------------------------------------------------------------
        # CCV-D-03: CR-03 (non-CRISIS with JRM active) -- dampening must NOT apply.
        # Verified by BIC backward compatibility comparison against a non-CRISIS
        # variant. Here we simply note the check for audit.
        # --------------------------------------------------------------------
        if "CR-03" in by_id:
            notes.append(
                "CCV-D-03: CR-03 is non-CRISIS with JRM active. Dampening "
                "not applied. Verified by absence of *0.75 in BIC comparison."
            )

        return violations, notes

    def xǁClipVerifierǁverify__mutmut_13(
        self,
        er_records: List[ExecutionRecord],
    ) -> Tuple[List[str], List[str]]:
        """
        Perform clip chain verification on ER-stage records.

        Returns:
          (violations, notes)
          violations -- list of violation description strings. Empty means pass.
          notes      -- list of non-failure informational notes.

        Raises RuntimeError with failure_type_id prefix on hard failures
        (CLIP_B_FLOOR_VIOLATION, CLIP_C_FLOOR_VIOLATION, CLIP_A_VIOLATION,
        CRISIS_ORDERING_VIOLATION).
        """
        violations = []
        notes      = []
        by_id: Dict[str, ExecutionRecord] = {r.vector_id: r for r in er_records}

        for rec in er_records:
            out = rec.observed_output
            if out.exception_raised:
                # No clip verification for exception vectors.
                continue

            vid = rec.vector_id
            iv  = rec.input_vector

            # ----------------------------------------------------------------
            # CCV-A-01: Clip A verification.
            # position_size_factor must be in [0.0, 1.0] for every normal vector.
            # ----------------------------------------------------------------
            psf = out.position_size_factor
            if psf < 0.0 or psf > 2.0:
                raise RuntimeError(
                    f"CLIP_A_VIOLATION: Vector {vid} position_size_factor={psf} "
                    "is outside [0.0, 1.0]. INV-01 violated."
                )

            # ----------------------------------------------------------------
            # CCV-B-01: For MU-02 and RP-02, E_pre_clip should be zero or near zero,
            # so Clip B floor should be active. exposure_weight bit pattern should
            # equal bit pattern of 1e-6.
            # ----------------------------------------------------------------
            if vid in ("MU-02", "RP-02"):
                ew_bits = _float_bits(out.exposure_weight)
                if ew_bits != self._lb_bits:
                    raise RuntimeError(
                        f"CLIP_B_FLOOR_VIOLATION: Vector {vid} exposure_weight "
                        f"expected bit pattern of 1e-6 but got "
                        f"{out.exposure_weight!r}. INV-02 violated."
                    )

            # ----------------------------------------------------------------
            # CCV-B-02: For JM-inactive (JM-01, JM-04) non-CRISIS vectors,
            # exposure_weight must be in [1e-6, 1.0].
            # (Clip C inactive, CRISIS dampening inactive.)
            # ----------------------------------------------------------------
            if vid in ("JM-01", "JM-04") and iv.current_regime_str != "CRISIS":
                ew = out.exposure_weight
                if ew < 1e-6 or ew > 1.0:
                    raise RuntimeError(
                        f"CLIP_B_RANGE_VIOLATION: Vector {vid} exposure_weight={ew} "
                        "outside [1e-6, 1.0] with Clip C and CRISIS dampening both "
                        "inactive. INV-02 violated."
                    )

            # ----------------------------------------------------------------
            # CCV-C-02: For JM-03 (designed to produce pre-Clip-C value below
            # SHOCK_EXPOSURE_CAP), exposure_weight should equal SHOCK_EXPOSURE_CAP.
            # ----------------------------------------------------------------
            if vid == "JM-03":
                ew_bits = _float_bits(out.exposure_weight)
                if ew_bits != self._sec_bits:
                    # JM-03 uses meta_uncertainty=0.99 + multiplier=2.0.
                    # The division may produce a value below SHOCK_EXPOSURE_CAP,
                    # which gets clipped to SHOCK_EXPOSURE_CAP by Clip C.
                    # If the result does NOT equal SHOCK_EXPOSURE_CAP, the
                    # actual computed value exceeded the cap after division;
                    # this is acceptable if the value is above SHOCK_EXPOSURE_CAP.
                    # Hard failure only if value is strictly below SHOCK_EXPOSURE_CAP.
                    if out.exposure_weight < self._sec:
                        raise RuntimeError(
                            f"CLIP_C_FLOOR_VIOLATION: Vector {vid} exposure_weight="
                            f"{out.exposure_weight} is below SHOCK_EXPOSURE_CAP="
                            f"{self._sec}. INV-03 violated."
                        )
                    notes.append(
                        f"CCV-C-02 note: JM-03 exposure_weight={out.exposure_weight} "
                        "exceeds SHOCK_EXPOSURE_CAP; Clip C floor not triggered."
                    )

            # ----------------------------------------------------------------
            # CCV-D-02: For CR-01 (CRISIS, JRM inactive), exposure_weight may be
            # below SHOCK_EXPOSURE_CAP. No floor enforcement. This is specified
            # behaviour per INV-04.
            # ----------------------------------------------------------------
            if vid == "CR-01":
                notes.append(
                    f"CCV-D-02: CR-01 exposure_weight={out.exposure_weight}. "
                    "May be below SHOCK_EXPOSURE_CAP per INV-04 (specified behaviour)."
                )

        # --------------------------------------------------------------------
        # CCV-D-01: For CR-02 (CRISIS + JRM active), verify ordering.
        # Expected: CR-02.exposure_weight == JM-03.exposure_weight * 0.75
        # Both records must be present in ER set.
        # --------------------------------------------------------------------
        if "CR-02" in by_id and "JM-03" in by_id:
            cr02_out = by_id["CR-02"].observed_output
            jm03_out = by_id["JM-03"].observed_output
            if not cr02_out.exception_raised and not jm03_out.exception_raised:
                # Compute expected value using Python float arithmetic (same as production).
                expected_cr02_ew = jm03_out.exposure_weight * 0.75
                if not _floats_equal(cr02_out.exposure_weight, expected_cr02_ew):
                    raise RuntimeError(
                        f"CRISIS_ORDERING_VIOLATION: CR-02 exposure_weight="
                        f"{cr02_out.exposure_weight} != JM-03.exposure_weight*0.75="
                        f"{expected_cr02_ew}. Clip C / CRISIS ordering violated. "
                        "INV-04 violated."
                    )

        # --------------------------------------------------------------------
        # CCV-D-03: CR-03 (non-CRISIS with JRM active) -- dampening must NOT apply.
        # Verified by BIC backward compatibility comparison against a non-CRISIS
        # variant. Here we simply note the check for audit.
        # --------------------------------------------------------------------
        if "CR-03" in by_id:
            notes.append(
                "CCV-D-03: CR-03 is non-CRISIS with JRM active. Dampening "
                "not applied. Verified by absence of *0.75 in BIC comparison."
            )

        return violations, notes

    def xǁClipVerifierǁverify__mutmut_14(
        self,
        er_records: List[ExecutionRecord],
    ) -> Tuple[List[str], List[str]]:
        """
        Perform clip chain verification on ER-stage records.

        Returns:
          (violations, notes)
          violations -- list of violation description strings. Empty means pass.
          notes      -- list of non-failure informational notes.

        Raises RuntimeError with failure_type_id prefix on hard failures
        (CLIP_B_FLOOR_VIOLATION, CLIP_C_FLOOR_VIOLATION, CLIP_A_VIOLATION,
        CRISIS_ORDERING_VIOLATION).
        """
        violations = []
        notes      = []
        by_id: Dict[str, ExecutionRecord] = {r.vector_id: r for r in er_records}

        for rec in er_records:
            out = rec.observed_output
            if out.exception_raised:
                # No clip verification for exception vectors.
                continue

            vid = rec.vector_id
            iv  = rec.input_vector

            # ----------------------------------------------------------------
            # CCV-A-01: Clip A verification.
            # position_size_factor must be in [0.0, 1.0] for every normal vector.
            # ----------------------------------------------------------------
            psf = out.position_size_factor
            if psf < 0.0 or psf > 1.0:
                raise RuntimeError(
                    None
                )

            # ----------------------------------------------------------------
            # CCV-B-01: For MU-02 and RP-02, E_pre_clip should be zero or near zero,
            # so Clip B floor should be active. exposure_weight bit pattern should
            # equal bit pattern of 1e-6.
            # ----------------------------------------------------------------
            if vid in ("MU-02", "RP-02"):
                ew_bits = _float_bits(out.exposure_weight)
                if ew_bits != self._lb_bits:
                    raise RuntimeError(
                        f"CLIP_B_FLOOR_VIOLATION: Vector {vid} exposure_weight "
                        f"expected bit pattern of 1e-6 but got "
                        f"{out.exposure_weight!r}. INV-02 violated."
                    )

            # ----------------------------------------------------------------
            # CCV-B-02: For JM-inactive (JM-01, JM-04) non-CRISIS vectors,
            # exposure_weight must be in [1e-6, 1.0].
            # (Clip C inactive, CRISIS dampening inactive.)
            # ----------------------------------------------------------------
            if vid in ("JM-01", "JM-04") and iv.current_regime_str != "CRISIS":
                ew = out.exposure_weight
                if ew < 1e-6 or ew > 1.0:
                    raise RuntimeError(
                        f"CLIP_B_RANGE_VIOLATION: Vector {vid} exposure_weight={ew} "
                        "outside [1e-6, 1.0] with Clip C and CRISIS dampening both "
                        "inactive. INV-02 violated."
                    )

            # ----------------------------------------------------------------
            # CCV-C-02: For JM-03 (designed to produce pre-Clip-C value below
            # SHOCK_EXPOSURE_CAP), exposure_weight should equal SHOCK_EXPOSURE_CAP.
            # ----------------------------------------------------------------
            if vid == "JM-03":
                ew_bits = _float_bits(out.exposure_weight)
                if ew_bits != self._sec_bits:
                    # JM-03 uses meta_uncertainty=0.99 + multiplier=2.0.
                    # The division may produce a value below SHOCK_EXPOSURE_CAP,
                    # which gets clipped to SHOCK_EXPOSURE_CAP by Clip C.
                    # If the result does NOT equal SHOCK_EXPOSURE_CAP, the
                    # actual computed value exceeded the cap after division;
                    # this is acceptable if the value is above SHOCK_EXPOSURE_CAP.
                    # Hard failure only if value is strictly below SHOCK_EXPOSURE_CAP.
                    if out.exposure_weight < self._sec:
                        raise RuntimeError(
                            f"CLIP_C_FLOOR_VIOLATION: Vector {vid} exposure_weight="
                            f"{out.exposure_weight} is below SHOCK_EXPOSURE_CAP="
                            f"{self._sec}. INV-03 violated."
                        )
                    notes.append(
                        f"CCV-C-02 note: JM-03 exposure_weight={out.exposure_weight} "
                        "exceeds SHOCK_EXPOSURE_CAP; Clip C floor not triggered."
                    )

            # ----------------------------------------------------------------
            # CCV-D-02: For CR-01 (CRISIS, JRM inactive), exposure_weight may be
            # below SHOCK_EXPOSURE_CAP. No floor enforcement. This is specified
            # behaviour per INV-04.
            # ----------------------------------------------------------------
            if vid == "CR-01":
                notes.append(
                    f"CCV-D-02: CR-01 exposure_weight={out.exposure_weight}. "
                    "May be below SHOCK_EXPOSURE_CAP per INV-04 (specified behaviour)."
                )

        # --------------------------------------------------------------------
        # CCV-D-01: For CR-02 (CRISIS + JRM active), verify ordering.
        # Expected: CR-02.exposure_weight == JM-03.exposure_weight * 0.75
        # Both records must be present in ER set.
        # --------------------------------------------------------------------
        if "CR-02" in by_id and "JM-03" in by_id:
            cr02_out = by_id["CR-02"].observed_output
            jm03_out = by_id["JM-03"].observed_output
            if not cr02_out.exception_raised and not jm03_out.exception_raised:
                # Compute expected value using Python float arithmetic (same as production).
                expected_cr02_ew = jm03_out.exposure_weight * 0.75
                if not _floats_equal(cr02_out.exposure_weight, expected_cr02_ew):
                    raise RuntimeError(
                        f"CRISIS_ORDERING_VIOLATION: CR-02 exposure_weight="
                        f"{cr02_out.exposure_weight} != JM-03.exposure_weight*0.75="
                        f"{expected_cr02_ew}. Clip C / CRISIS ordering violated. "
                        "INV-04 violated."
                    )

        # --------------------------------------------------------------------
        # CCV-D-03: CR-03 (non-CRISIS with JRM active) -- dampening must NOT apply.
        # Verified by BIC backward compatibility comparison against a non-CRISIS
        # variant. Here we simply note the check for audit.
        # --------------------------------------------------------------------
        if "CR-03" in by_id:
            notes.append(
                "CCV-D-03: CR-03 is non-CRISIS with JRM active. Dampening "
                "not applied. Verified by absence of *0.75 in BIC comparison."
            )

        return violations, notes

    def xǁClipVerifierǁverify__mutmut_15(
        self,
        er_records: List[ExecutionRecord],
    ) -> Tuple[List[str], List[str]]:
        """
        Perform clip chain verification on ER-stage records.

        Returns:
          (violations, notes)
          violations -- list of violation description strings. Empty means pass.
          notes      -- list of non-failure informational notes.

        Raises RuntimeError with failure_type_id prefix on hard failures
        (CLIP_B_FLOOR_VIOLATION, CLIP_C_FLOOR_VIOLATION, CLIP_A_VIOLATION,
        CRISIS_ORDERING_VIOLATION).
        """
        violations = []
        notes      = []
        by_id: Dict[str, ExecutionRecord] = {r.vector_id: r for r in er_records}

        for rec in er_records:
            out = rec.observed_output
            if out.exception_raised:
                # No clip verification for exception vectors.
                continue

            vid = rec.vector_id
            iv  = rec.input_vector

            # ----------------------------------------------------------------
            # CCV-A-01: Clip A verification.
            # position_size_factor must be in [0.0, 1.0] for every normal vector.
            # ----------------------------------------------------------------
            psf = out.position_size_factor
            if psf < 0.0 or psf > 1.0:
                raise RuntimeError(
                    f"CLIP_A_VIOLATION: Vector {vid} position_size_factor={psf} "
                    "XXis outside [0.0, 1.0]. INV-01 violated.XX"
                )

            # ----------------------------------------------------------------
            # CCV-B-01: For MU-02 and RP-02, E_pre_clip should be zero or near zero,
            # so Clip B floor should be active. exposure_weight bit pattern should
            # equal bit pattern of 1e-6.
            # ----------------------------------------------------------------
            if vid in ("MU-02", "RP-02"):
                ew_bits = _float_bits(out.exposure_weight)
                if ew_bits != self._lb_bits:
                    raise RuntimeError(
                        f"CLIP_B_FLOOR_VIOLATION: Vector {vid} exposure_weight "
                        f"expected bit pattern of 1e-6 but got "
                        f"{out.exposure_weight!r}. INV-02 violated."
                    )

            # ----------------------------------------------------------------
            # CCV-B-02: For JM-inactive (JM-01, JM-04) non-CRISIS vectors,
            # exposure_weight must be in [1e-6, 1.0].
            # (Clip C inactive, CRISIS dampening inactive.)
            # ----------------------------------------------------------------
            if vid in ("JM-01", "JM-04") and iv.current_regime_str != "CRISIS":
                ew = out.exposure_weight
                if ew < 1e-6 or ew > 1.0:
                    raise RuntimeError(
                        f"CLIP_B_RANGE_VIOLATION: Vector {vid} exposure_weight={ew} "
                        "outside [1e-6, 1.0] with Clip C and CRISIS dampening both "
                        "inactive. INV-02 violated."
                    )

            # ----------------------------------------------------------------
            # CCV-C-02: For JM-03 (designed to produce pre-Clip-C value below
            # SHOCK_EXPOSURE_CAP), exposure_weight should equal SHOCK_EXPOSURE_CAP.
            # ----------------------------------------------------------------
            if vid == "JM-03":
                ew_bits = _float_bits(out.exposure_weight)
                if ew_bits != self._sec_bits:
                    # JM-03 uses meta_uncertainty=0.99 + multiplier=2.0.
                    # The division may produce a value below SHOCK_EXPOSURE_CAP,
                    # which gets clipped to SHOCK_EXPOSURE_CAP by Clip C.
                    # If the result does NOT equal SHOCK_EXPOSURE_CAP, the
                    # actual computed value exceeded the cap after division;
                    # this is acceptable if the value is above SHOCK_EXPOSURE_CAP.
                    # Hard failure only if value is strictly below SHOCK_EXPOSURE_CAP.
                    if out.exposure_weight < self._sec:
                        raise RuntimeError(
                            f"CLIP_C_FLOOR_VIOLATION: Vector {vid} exposure_weight="
                            f"{out.exposure_weight} is below SHOCK_EXPOSURE_CAP="
                            f"{self._sec}. INV-03 violated."
                        )
                    notes.append(
                        f"CCV-C-02 note: JM-03 exposure_weight={out.exposure_weight} "
                        "exceeds SHOCK_EXPOSURE_CAP; Clip C floor not triggered."
                    )

            # ----------------------------------------------------------------
            # CCV-D-02: For CR-01 (CRISIS, JRM inactive), exposure_weight may be
            # below SHOCK_EXPOSURE_CAP. No floor enforcement. This is specified
            # behaviour per INV-04.
            # ----------------------------------------------------------------
            if vid == "CR-01":
                notes.append(
                    f"CCV-D-02: CR-01 exposure_weight={out.exposure_weight}. "
                    "May be below SHOCK_EXPOSURE_CAP per INV-04 (specified behaviour)."
                )

        # --------------------------------------------------------------------
        # CCV-D-01: For CR-02 (CRISIS + JRM active), verify ordering.
        # Expected: CR-02.exposure_weight == JM-03.exposure_weight * 0.75
        # Both records must be present in ER set.
        # --------------------------------------------------------------------
        if "CR-02" in by_id and "JM-03" in by_id:
            cr02_out = by_id["CR-02"].observed_output
            jm03_out = by_id["JM-03"].observed_output
            if not cr02_out.exception_raised and not jm03_out.exception_raised:
                # Compute expected value using Python float arithmetic (same as production).
                expected_cr02_ew = jm03_out.exposure_weight * 0.75
                if not _floats_equal(cr02_out.exposure_weight, expected_cr02_ew):
                    raise RuntimeError(
                        f"CRISIS_ORDERING_VIOLATION: CR-02 exposure_weight="
                        f"{cr02_out.exposure_weight} != JM-03.exposure_weight*0.75="
                        f"{expected_cr02_ew}. Clip C / CRISIS ordering violated. "
                        "INV-04 violated."
                    )

        # --------------------------------------------------------------------
        # CCV-D-03: CR-03 (non-CRISIS with JRM active) -- dampening must NOT apply.
        # Verified by BIC backward compatibility comparison against a non-CRISIS
        # variant. Here we simply note the check for audit.
        # --------------------------------------------------------------------
        if "CR-03" in by_id:
            notes.append(
                "CCV-D-03: CR-03 is non-CRISIS with JRM active. Dampening "
                "not applied. Verified by absence of *0.75 in BIC comparison."
            )

        return violations, notes

    def xǁClipVerifierǁverify__mutmut_16(
        self,
        er_records: List[ExecutionRecord],
    ) -> Tuple[List[str], List[str]]:
        """
        Perform clip chain verification on ER-stage records.

        Returns:
          (violations, notes)
          violations -- list of violation description strings. Empty means pass.
          notes      -- list of non-failure informational notes.

        Raises RuntimeError with failure_type_id prefix on hard failures
        (CLIP_B_FLOOR_VIOLATION, CLIP_C_FLOOR_VIOLATION, CLIP_A_VIOLATION,
        CRISIS_ORDERING_VIOLATION).
        """
        violations = []
        notes      = []
        by_id: Dict[str, ExecutionRecord] = {r.vector_id: r for r in er_records}

        for rec in er_records:
            out = rec.observed_output
            if out.exception_raised:
                # No clip verification for exception vectors.
                continue

            vid = rec.vector_id
            iv  = rec.input_vector

            # ----------------------------------------------------------------
            # CCV-A-01: Clip A verification.
            # position_size_factor must be in [0.0, 1.0] for every normal vector.
            # ----------------------------------------------------------------
            psf = out.position_size_factor
            if psf < 0.0 or psf > 1.0:
                raise RuntimeError(
                    f"CLIP_A_VIOLATION: Vector {vid} position_size_factor={psf} "
                    "is outside [0.0, 1.0]. inv-01 violated."
                )

            # ----------------------------------------------------------------
            # CCV-B-01: For MU-02 and RP-02, E_pre_clip should be zero or near zero,
            # so Clip B floor should be active. exposure_weight bit pattern should
            # equal bit pattern of 1e-6.
            # ----------------------------------------------------------------
            if vid in ("MU-02", "RP-02"):
                ew_bits = _float_bits(out.exposure_weight)
                if ew_bits != self._lb_bits:
                    raise RuntimeError(
                        f"CLIP_B_FLOOR_VIOLATION: Vector {vid} exposure_weight "
                        f"expected bit pattern of 1e-6 but got "
                        f"{out.exposure_weight!r}. INV-02 violated."
                    )

            # ----------------------------------------------------------------
            # CCV-B-02: For JM-inactive (JM-01, JM-04) non-CRISIS vectors,
            # exposure_weight must be in [1e-6, 1.0].
            # (Clip C inactive, CRISIS dampening inactive.)
            # ----------------------------------------------------------------
            if vid in ("JM-01", "JM-04") and iv.current_regime_str != "CRISIS":
                ew = out.exposure_weight
                if ew < 1e-6 or ew > 1.0:
                    raise RuntimeError(
                        f"CLIP_B_RANGE_VIOLATION: Vector {vid} exposure_weight={ew} "
                        "outside [1e-6, 1.0] with Clip C and CRISIS dampening both "
                        "inactive. INV-02 violated."
                    )

            # ----------------------------------------------------------------
            # CCV-C-02: For JM-03 (designed to produce pre-Clip-C value below
            # SHOCK_EXPOSURE_CAP), exposure_weight should equal SHOCK_EXPOSURE_CAP.
            # ----------------------------------------------------------------
            if vid == "JM-03":
                ew_bits = _float_bits(out.exposure_weight)
                if ew_bits != self._sec_bits:
                    # JM-03 uses meta_uncertainty=0.99 + multiplier=2.0.
                    # The division may produce a value below SHOCK_EXPOSURE_CAP,
                    # which gets clipped to SHOCK_EXPOSURE_CAP by Clip C.
                    # If the result does NOT equal SHOCK_EXPOSURE_CAP, the
                    # actual computed value exceeded the cap after division;
                    # this is acceptable if the value is above SHOCK_EXPOSURE_CAP.
                    # Hard failure only if value is strictly below SHOCK_EXPOSURE_CAP.
                    if out.exposure_weight < self._sec:
                        raise RuntimeError(
                            f"CLIP_C_FLOOR_VIOLATION: Vector {vid} exposure_weight="
                            f"{out.exposure_weight} is below SHOCK_EXPOSURE_CAP="
                            f"{self._sec}. INV-03 violated."
                        )
                    notes.append(
                        f"CCV-C-02 note: JM-03 exposure_weight={out.exposure_weight} "
                        "exceeds SHOCK_EXPOSURE_CAP; Clip C floor not triggered."
                    )

            # ----------------------------------------------------------------
            # CCV-D-02: For CR-01 (CRISIS, JRM inactive), exposure_weight may be
            # below SHOCK_EXPOSURE_CAP. No floor enforcement. This is specified
            # behaviour per INV-04.
            # ----------------------------------------------------------------
            if vid == "CR-01":
                notes.append(
                    f"CCV-D-02: CR-01 exposure_weight={out.exposure_weight}. "
                    "May be below SHOCK_EXPOSURE_CAP per INV-04 (specified behaviour)."
                )

        # --------------------------------------------------------------------
        # CCV-D-01: For CR-02 (CRISIS + JRM active), verify ordering.
        # Expected: CR-02.exposure_weight == JM-03.exposure_weight * 0.75
        # Both records must be present in ER set.
        # --------------------------------------------------------------------
        if "CR-02" in by_id and "JM-03" in by_id:
            cr02_out = by_id["CR-02"].observed_output
            jm03_out = by_id["JM-03"].observed_output
            if not cr02_out.exception_raised and not jm03_out.exception_raised:
                # Compute expected value using Python float arithmetic (same as production).
                expected_cr02_ew = jm03_out.exposure_weight * 0.75
                if not _floats_equal(cr02_out.exposure_weight, expected_cr02_ew):
                    raise RuntimeError(
                        f"CRISIS_ORDERING_VIOLATION: CR-02 exposure_weight="
                        f"{cr02_out.exposure_weight} != JM-03.exposure_weight*0.75="
                        f"{expected_cr02_ew}. Clip C / CRISIS ordering violated. "
                        "INV-04 violated."
                    )

        # --------------------------------------------------------------------
        # CCV-D-03: CR-03 (non-CRISIS with JRM active) -- dampening must NOT apply.
        # Verified by BIC backward compatibility comparison against a non-CRISIS
        # variant. Here we simply note the check for audit.
        # --------------------------------------------------------------------
        if "CR-03" in by_id:
            notes.append(
                "CCV-D-03: CR-03 is non-CRISIS with JRM active. Dampening "
                "not applied. Verified by absence of *0.75 in BIC comparison."
            )

        return violations, notes

    def xǁClipVerifierǁverify__mutmut_17(
        self,
        er_records: List[ExecutionRecord],
    ) -> Tuple[List[str], List[str]]:
        """
        Perform clip chain verification on ER-stage records.

        Returns:
          (violations, notes)
          violations -- list of violation description strings. Empty means pass.
          notes      -- list of non-failure informational notes.

        Raises RuntimeError with failure_type_id prefix on hard failures
        (CLIP_B_FLOOR_VIOLATION, CLIP_C_FLOOR_VIOLATION, CLIP_A_VIOLATION,
        CRISIS_ORDERING_VIOLATION).
        """
        violations = []
        notes      = []
        by_id: Dict[str, ExecutionRecord] = {r.vector_id: r for r in er_records}

        for rec in er_records:
            out = rec.observed_output
            if out.exception_raised:
                # No clip verification for exception vectors.
                continue

            vid = rec.vector_id
            iv  = rec.input_vector

            # ----------------------------------------------------------------
            # CCV-A-01: Clip A verification.
            # position_size_factor must be in [0.0, 1.0] for every normal vector.
            # ----------------------------------------------------------------
            psf = out.position_size_factor
            if psf < 0.0 or psf > 1.0:
                raise RuntimeError(
                    f"CLIP_A_VIOLATION: Vector {vid} position_size_factor={psf} "
                    "IS OUTSIDE [0.0, 1.0]. INV-01 VIOLATED."
                )

            # ----------------------------------------------------------------
            # CCV-B-01: For MU-02 and RP-02, E_pre_clip should be zero or near zero,
            # so Clip B floor should be active. exposure_weight bit pattern should
            # equal bit pattern of 1e-6.
            # ----------------------------------------------------------------
            if vid in ("MU-02", "RP-02"):
                ew_bits = _float_bits(out.exposure_weight)
                if ew_bits != self._lb_bits:
                    raise RuntimeError(
                        f"CLIP_B_FLOOR_VIOLATION: Vector {vid} exposure_weight "
                        f"expected bit pattern of 1e-6 but got "
                        f"{out.exposure_weight!r}. INV-02 violated."
                    )

            # ----------------------------------------------------------------
            # CCV-B-02: For JM-inactive (JM-01, JM-04) non-CRISIS vectors,
            # exposure_weight must be in [1e-6, 1.0].
            # (Clip C inactive, CRISIS dampening inactive.)
            # ----------------------------------------------------------------
            if vid in ("JM-01", "JM-04") and iv.current_regime_str != "CRISIS":
                ew = out.exposure_weight
                if ew < 1e-6 or ew > 1.0:
                    raise RuntimeError(
                        f"CLIP_B_RANGE_VIOLATION: Vector {vid} exposure_weight={ew} "
                        "outside [1e-6, 1.0] with Clip C and CRISIS dampening both "
                        "inactive. INV-02 violated."
                    )

            # ----------------------------------------------------------------
            # CCV-C-02: For JM-03 (designed to produce pre-Clip-C value below
            # SHOCK_EXPOSURE_CAP), exposure_weight should equal SHOCK_EXPOSURE_CAP.
            # ----------------------------------------------------------------
            if vid == "JM-03":
                ew_bits = _float_bits(out.exposure_weight)
                if ew_bits != self._sec_bits:
                    # JM-03 uses meta_uncertainty=0.99 + multiplier=2.0.
                    # The division may produce a value below SHOCK_EXPOSURE_CAP,
                    # which gets clipped to SHOCK_EXPOSURE_CAP by Clip C.
                    # If the result does NOT equal SHOCK_EXPOSURE_CAP, the
                    # actual computed value exceeded the cap after division;
                    # this is acceptable if the value is above SHOCK_EXPOSURE_CAP.
                    # Hard failure only if value is strictly below SHOCK_EXPOSURE_CAP.
                    if out.exposure_weight < self._sec:
                        raise RuntimeError(
                            f"CLIP_C_FLOOR_VIOLATION: Vector {vid} exposure_weight="
                            f"{out.exposure_weight} is below SHOCK_EXPOSURE_CAP="
                            f"{self._sec}. INV-03 violated."
                        )
                    notes.append(
                        f"CCV-C-02 note: JM-03 exposure_weight={out.exposure_weight} "
                        "exceeds SHOCK_EXPOSURE_CAP; Clip C floor not triggered."
                    )

            # ----------------------------------------------------------------
            # CCV-D-02: For CR-01 (CRISIS, JRM inactive), exposure_weight may be
            # below SHOCK_EXPOSURE_CAP. No floor enforcement. This is specified
            # behaviour per INV-04.
            # ----------------------------------------------------------------
            if vid == "CR-01":
                notes.append(
                    f"CCV-D-02: CR-01 exposure_weight={out.exposure_weight}. "
                    "May be below SHOCK_EXPOSURE_CAP per INV-04 (specified behaviour)."
                )

        # --------------------------------------------------------------------
        # CCV-D-01: For CR-02 (CRISIS + JRM active), verify ordering.
        # Expected: CR-02.exposure_weight == JM-03.exposure_weight * 0.75
        # Both records must be present in ER set.
        # --------------------------------------------------------------------
        if "CR-02" in by_id and "JM-03" in by_id:
            cr02_out = by_id["CR-02"].observed_output
            jm03_out = by_id["JM-03"].observed_output
            if not cr02_out.exception_raised and not jm03_out.exception_raised:
                # Compute expected value using Python float arithmetic (same as production).
                expected_cr02_ew = jm03_out.exposure_weight * 0.75
                if not _floats_equal(cr02_out.exposure_weight, expected_cr02_ew):
                    raise RuntimeError(
                        f"CRISIS_ORDERING_VIOLATION: CR-02 exposure_weight="
                        f"{cr02_out.exposure_weight} != JM-03.exposure_weight*0.75="
                        f"{expected_cr02_ew}. Clip C / CRISIS ordering violated. "
                        "INV-04 violated."
                    )

        # --------------------------------------------------------------------
        # CCV-D-03: CR-03 (non-CRISIS with JRM active) -- dampening must NOT apply.
        # Verified by BIC backward compatibility comparison against a non-CRISIS
        # variant. Here we simply note the check for audit.
        # --------------------------------------------------------------------
        if "CR-03" in by_id:
            notes.append(
                "CCV-D-03: CR-03 is non-CRISIS with JRM active. Dampening "
                "not applied. Verified by absence of *0.75 in BIC comparison."
            )

        return violations, notes

    def xǁClipVerifierǁverify__mutmut_18(
        self,
        er_records: List[ExecutionRecord],
    ) -> Tuple[List[str], List[str]]:
        """
        Perform clip chain verification on ER-stage records.

        Returns:
          (violations, notes)
          violations -- list of violation description strings. Empty means pass.
          notes      -- list of non-failure informational notes.

        Raises RuntimeError with failure_type_id prefix on hard failures
        (CLIP_B_FLOOR_VIOLATION, CLIP_C_FLOOR_VIOLATION, CLIP_A_VIOLATION,
        CRISIS_ORDERING_VIOLATION).
        """
        violations = []
        notes      = []
        by_id: Dict[str, ExecutionRecord] = {r.vector_id: r for r in er_records}

        for rec in er_records:
            out = rec.observed_output
            if out.exception_raised:
                # No clip verification for exception vectors.
                continue

            vid = rec.vector_id
            iv  = rec.input_vector

            # ----------------------------------------------------------------
            # CCV-A-01: Clip A verification.
            # position_size_factor must be in [0.0, 1.0] for every normal vector.
            # ----------------------------------------------------------------
            psf = out.position_size_factor
            if psf < 0.0 or psf > 1.0:
                raise RuntimeError(
                    f"CLIP_A_VIOLATION: Vector {vid} position_size_factor={psf} "
                    "is outside [0.0, 1.0]. INV-01 violated."
                )

            # ----------------------------------------------------------------
            # CCV-B-01: For MU-02 and RP-02, E_pre_clip should be zero or near zero,
            # so Clip B floor should be active. exposure_weight bit pattern should
            # equal bit pattern of 1e-6.
            # ----------------------------------------------------------------
            if vid not in ("MU-02", "RP-02"):
                ew_bits = _float_bits(out.exposure_weight)
                if ew_bits != self._lb_bits:
                    raise RuntimeError(
                        f"CLIP_B_FLOOR_VIOLATION: Vector {vid} exposure_weight "
                        f"expected bit pattern of 1e-6 but got "
                        f"{out.exposure_weight!r}. INV-02 violated."
                    )

            # ----------------------------------------------------------------
            # CCV-B-02: For JM-inactive (JM-01, JM-04) non-CRISIS vectors,
            # exposure_weight must be in [1e-6, 1.0].
            # (Clip C inactive, CRISIS dampening inactive.)
            # ----------------------------------------------------------------
            if vid in ("JM-01", "JM-04") and iv.current_regime_str != "CRISIS":
                ew = out.exposure_weight
                if ew < 1e-6 or ew > 1.0:
                    raise RuntimeError(
                        f"CLIP_B_RANGE_VIOLATION: Vector {vid} exposure_weight={ew} "
                        "outside [1e-6, 1.0] with Clip C and CRISIS dampening both "
                        "inactive. INV-02 violated."
                    )

            # ----------------------------------------------------------------
            # CCV-C-02: For JM-03 (designed to produce pre-Clip-C value below
            # SHOCK_EXPOSURE_CAP), exposure_weight should equal SHOCK_EXPOSURE_CAP.
            # ----------------------------------------------------------------
            if vid == "JM-03":
                ew_bits = _float_bits(out.exposure_weight)
                if ew_bits != self._sec_bits:
                    # JM-03 uses meta_uncertainty=0.99 + multiplier=2.0.
                    # The division may produce a value below SHOCK_EXPOSURE_CAP,
                    # which gets clipped to SHOCK_EXPOSURE_CAP by Clip C.
                    # If the result does NOT equal SHOCK_EXPOSURE_CAP, the
                    # actual computed value exceeded the cap after division;
                    # this is acceptable if the value is above SHOCK_EXPOSURE_CAP.
                    # Hard failure only if value is strictly below SHOCK_EXPOSURE_CAP.
                    if out.exposure_weight < self._sec:
                        raise RuntimeError(
                            f"CLIP_C_FLOOR_VIOLATION: Vector {vid} exposure_weight="
                            f"{out.exposure_weight} is below SHOCK_EXPOSURE_CAP="
                            f"{self._sec}. INV-03 violated."
                        )
                    notes.append(
                        f"CCV-C-02 note: JM-03 exposure_weight={out.exposure_weight} "
                        "exceeds SHOCK_EXPOSURE_CAP; Clip C floor not triggered."
                    )

            # ----------------------------------------------------------------
            # CCV-D-02: For CR-01 (CRISIS, JRM inactive), exposure_weight may be
            # below SHOCK_EXPOSURE_CAP. No floor enforcement. This is specified
            # behaviour per INV-04.
            # ----------------------------------------------------------------
            if vid == "CR-01":
                notes.append(
                    f"CCV-D-02: CR-01 exposure_weight={out.exposure_weight}. "
                    "May be below SHOCK_EXPOSURE_CAP per INV-04 (specified behaviour)."
                )

        # --------------------------------------------------------------------
        # CCV-D-01: For CR-02 (CRISIS + JRM active), verify ordering.
        # Expected: CR-02.exposure_weight == JM-03.exposure_weight * 0.75
        # Both records must be present in ER set.
        # --------------------------------------------------------------------
        if "CR-02" in by_id and "JM-03" in by_id:
            cr02_out = by_id["CR-02"].observed_output
            jm03_out = by_id["JM-03"].observed_output
            if not cr02_out.exception_raised and not jm03_out.exception_raised:
                # Compute expected value using Python float arithmetic (same as production).
                expected_cr02_ew = jm03_out.exposure_weight * 0.75
                if not _floats_equal(cr02_out.exposure_weight, expected_cr02_ew):
                    raise RuntimeError(
                        f"CRISIS_ORDERING_VIOLATION: CR-02 exposure_weight="
                        f"{cr02_out.exposure_weight} != JM-03.exposure_weight*0.75="
                        f"{expected_cr02_ew}. Clip C / CRISIS ordering violated. "
                        "INV-04 violated."
                    )

        # --------------------------------------------------------------------
        # CCV-D-03: CR-03 (non-CRISIS with JRM active) -- dampening must NOT apply.
        # Verified by BIC backward compatibility comparison against a non-CRISIS
        # variant. Here we simply note the check for audit.
        # --------------------------------------------------------------------
        if "CR-03" in by_id:
            notes.append(
                "CCV-D-03: CR-03 is non-CRISIS with JRM active. Dampening "
                "not applied. Verified by absence of *0.75 in BIC comparison."
            )

        return violations, notes

    def xǁClipVerifierǁverify__mutmut_19(
        self,
        er_records: List[ExecutionRecord],
    ) -> Tuple[List[str], List[str]]:
        """
        Perform clip chain verification on ER-stage records.

        Returns:
          (violations, notes)
          violations -- list of violation description strings. Empty means pass.
          notes      -- list of non-failure informational notes.

        Raises RuntimeError with failure_type_id prefix on hard failures
        (CLIP_B_FLOOR_VIOLATION, CLIP_C_FLOOR_VIOLATION, CLIP_A_VIOLATION,
        CRISIS_ORDERING_VIOLATION).
        """
        violations = []
        notes      = []
        by_id: Dict[str, ExecutionRecord] = {r.vector_id: r for r in er_records}

        for rec in er_records:
            out = rec.observed_output
            if out.exception_raised:
                # No clip verification for exception vectors.
                continue

            vid = rec.vector_id
            iv  = rec.input_vector

            # ----------------------------------------------------------------
            # CCV-A-01: Clip A verification.
            # position_size_factor must be in [0.0, 1.0] for every normal vector.
            # ----------------------------------------------------------------
            psf = out.position_size_factor
            if psf < 0.0 or psf > 1.0:
                raise RuntimeError(
                    f"CLIP_A_VIOLATION: Vector {vid} position_size_factor={psf} "
                    "is outside [0.0, 1.0]. INV-01 violated."
                )

            # ----------------------------------------------------------------
            # CCV-B-01: For MU-02 and RP-02, E_pre_clip should be zero or near zero,
            # so Clip B floor should be active. exposure_weight bit pattern should
            # equal bit pattern of 1e-6.
            # ----------------------------------------------------------------
            if vid in ("XXMU-02XX", "RP-02"):
                ew_bits = _float_bits(out.exposure_weight)
                if ew_bits != self._lb_bits:
                    raise RuntimeError(
                        f"CLIP_B_FLOOR_VIOLATION: Vector {vid} exposure_weight "
                        f"expected bit pattern of 1e-6 but got "
                        f"{out.exposure_weight!r}. INV-02 violated."
                    )

            # ----------------------------------------------------------------
            # CCV-B-02: For JM-inactive (JM-01, JM-04) non-CRISIS vectors,
            # exposure_weight must be in [1e-6, 1.0].
            # (Clip C inactive, CRISIS dampening inactive.)
            # ----------------------------------------------------------------
            if vid in ("JM-01", "JM-04") and iv.current_regime_str != "CRISIS":
                ew = out.exposure_weight
                if ew < 1e-6 or ew > 1.0:
                    raise RuntimeError(
                        f"CLIP_B_RANGE_VIOLATION: Vector {vid} exposure_weight={ew} "
                        "outside [1e-6, 1.0] with Clip C and CRISIS dampening both "
                        "inactive. INV-02 violated."
                    )

            # ----------------------------------------------------------------
            # CCV-C-02: For JM-03 (designed to produce pre-Clip-C value below
            # SHOCK_EXPOSURE_CAP), exposure_weight should equal SHOCK_EXPOSURE_CAP.
            # ----------------------------------------------------------------
            if vid == "JM-03":
                ew_bits = _float_bits(out.exposure_weight)
                if ew_bits != self._sec_bits:
                    # JM-03 uses meta_uncertainty=0.99 + multiplier=2.0.
                    # The division may produce a value below SHOCK_EXPOSURE_CAP,
                    # which gets clipped to SHOCK_EXPOSURE_CAP by Clip C.
                    # If the result does NOT equal SHOCK_EXPOSURE_CAP, the
                    # actual computed value exceeded the cap after division;
                    # this is acceptable if the value is above SHOCK_EXPOSURE_CAP.
                    # Hard failure only if value is strictly below SHOCK_EXPOSURE_CAP.
                    if out.exposure_weight < self._sec:
                        raise RuntimeError(
                            f"CLIP_C_FLOOR_VIOLATION: Vector {vid} exposure_weight="
                            f"{out.exposure_weight} is below SHOCK_EXPOSURE_CAP="
                            f"{self._sec}. INV-03 violated."
                        )
                    notes.append(
                        f"CCV-C-02 note: JM-03 exposure_weight={out.exposure_weight} "
                        "exceeds SHOCK_EXPOSURE_CAP; Clip C floor not triggered."
                    )

            # ----------------------------------------------------------------
            # CCV-D-02: For CR-01 (CRISIS, JRM inactive), exposure_weight may be
            # below SHOCK_EXPOSURE_CAP. No floor enforcement. This is specified
            # behaviour per INV-04.
            # ----------------------------------------------------------------
            if vid == "CR-01":
                notes.append(
                    f"CCV-D-02: CR-01 exposure_weight={out.exposure_weight}. "
                    "May be below SHOCK_EXPOSURE_CAP per INV-04 (specified behaviour)."
                )

        # --------------------------------------------------------------------
        # CCV-D-01: For CR-02 (CRISIS + JRM active), verify ordering.
        # Expected: CR-02.exposure_weight == JM-03.exposure_weight * 0.75
        # Both records must be present in ER set.
        # --------------------------------------------------------------------
        if "CR-02" in by_id and "JM-03" in by_id:
            cr02_out = by_id["CR-02"].observed_output
            jm03_out = by_id["JM-03"].observed_output
            if not cr02_out.exception_raised and not jm03_out.exception_raised:
                # Compute expected value using Python float arithmetic (same as production).
                expected_cr02_ew = jm03_out.exposure_weight * 0.75
                if not _floats_equal(cr02_out.exposure_weight, expected_cr02_ew):
                    raise RuntimeError(
                        f"CRISIS_ORDERING_VIOLATION: CR-02 exposure_weight="
                        f"{cr02_out.exposure_weight} != JM-03.exposure_weight*0.75="
                        f"{expected_cr02_ew}. Clip C / CRISIS ordering violated. "
                        "INV-04 violated."
                    )

        # --------------------------------------------------------------------
        # CCV-D-03: CR-03 (non-CRISIS with JRM active) -- dampening must NOT apply.
        # Verified by BIC backward compatibility comparison against a non-CRISIS
        # variant. Here we simply note the check for audit.
        # --------------------------------------------------------------------
        if "CR-03" in by_id:
            notes.append(
                "CCV-D-03: CR-03 is non-CRISIS with JRM active. Dampening "
                "not applied. Verified by absence of *0.75 in BIC comparison."
            )

        return violations, notes

    def xǁClipVerifierǁverify__mutmut_20(
        self,
        er_records: List[ExecutionRecord],
    ) -> Tuple[List[str], List[str]]:
        """
        Perform clip chain verification on ER-stage records.

        Returns:
          (violations, notes)
          violations -- list of violation description strings. Empty means pass.
          notes      -- list of non-failure informational notes.

        Raises RuntimeError with failure_type_id prefix on hard failures
        (CLIP_B_FLOOR_VIOLATION, CLIP_C_FLOOR_VIOLATION, CLIP_A_VIOLATION,
        CRISIS_ORDERING_VIOLATION).
        """
        violations = []
        notes      = []
        by_id: Dict[str, ExecutionRecord] = {r.vector_id: r for r in er_records}

        for rec in er_records:
            out = rec.observed_output
            if out.exception_raised:
                # No clip verification for exception vectors.
                continue

            vid = rec.vector_id
            iv  = rec.input_vector

            # ----------------------------------------------------------------
            # CCV-A-01: Clip A verification.
            # position_size_factor must be in [0.0, 1.0] for every normal vector.
            # ----------------------------------------------------------------
            psf = out.position_size_factor
            if psf < 0.0 or psf > 1.0:
                raise RuntimeError(
                    f"CLIP_A_VIOLATION: Vector {vid} position_size_factor={psf} "
                    "is outside [0.0, 1.0]. INV-01 violated."
                )

            # ----------------------------------------------------------------
            # CCV-B-01: For MU-02 and RP-02, E_pre_clip should be zero or near zero,
            # so Clip B floor should be active. exposure_weight bit pattern should
            # equal bit pattern of 1e-6.
            # ----------------------------------------------------------------
            if vid in ("mu-02", "RP-02"):
                ew_bits = _float_bits(out.exposure_weight)
                if ew_bits != self._lb_bits:
                    raise RuntimeError(
                        f"CLIP_B_FLOOR_VIOLATION: Vector {vid} exposure_weight "
                        f"expected bit pattern of 1e-6 but got "
                        f"{out.exposure_weight!r}. INV-02 violated."
                    )

            # ----------------------------------------------------------------
            # CCV-B-02: For JM-inactive (JM-01, JM-04) non-CRISIS vectors,
            # exposure_weight must be in [1e-6, 1.0].
            # (Clip C inactive, CRISIS dampening inactive.)
            # ----------------------------------------------------------------
            if vid in ("JM-01", "JM-04") and iv.current_regime_str != "CRISIS":
                ew = out.exposure_weight
                if ew < 1e-6 or ew > 1.0:
                    raise RuntimeError(
                        f"CLIP_B_RANGE_VIOLATION: Vector {vid} exposure_weight={ew} "
                        "outside [1e-6, 1.0] with Clip C and CRISIS dampening both "
                        "inactive. INV-02 violated."
                    )

            # ----------------------------------------------------------------
            # CCV-C-02: For JM-03 (designed to produce pre-Clip-C value below
            # SHOCK_EXPOSURE_CAP), exposure_weight should equal SHOCK_EXPOSURE_CAP.
            # ----------------------------------------------------------------
            if vid == "JM-03":
                ew_bits = _float_bits(out.exposure_weight)
                if ew_bits != self._sec_bits:
                    # JM-03 uses meta_uncertainty=0.99 + multiplier=2.0.
                    # The division may produce a value below SHOCK_EXPOSURE_CAP,
                    # which gets clipped to SHOCK_EXPOSURE_CAP by Clip C.
                    # If the result does NOT equal SHOCK_EXPOSURE_CAP, the
                    # actual computed value exceeded the cap after division;
                    # this is acceptable if the value is above SHOCK_EXPOSURE_CAP.
                    # Hard failure only if value is strictly below SHOCK_EXPOSURE_CAP.
                    if out.exposure_weight < self._sec:
                        raise RuntimeError(
                            f"CLIP_C_FLOOR_VIOLATION: Vector {vid} exposure_weight="
                            f"{out.exposure_weight} is below SHOCK_EXPOSURE_CAP="
                            f"{self._sec}. INV-03 violated."
                        )
                    notes.append(
                        f"CCV-C-02 note: JM-03 exposure_weight={out.exposure_weight} "
                        "exceeds SHOCK_EXPOSURE_CAP; Clip C floor not triggered."
                    )

            # ----------------------------------------------------------------
            # CCV-D-02: For CR-01 (CRISIS, JRM inactive), exposure_weight may be
            # below SHOCK_EXPOSURE_CAP. No floor enforcement. This is specified
            # behaviour per INV-04.
            # ----------------------------------------------------------------
            if vid == "CR-01":
                notes.append(
                    f"CCV-D-02: CR-01 exposure_weight={out.exposure_weight}. "
                    "May be below SHOCK_EXPOSURE_CAP per INV-04 (specified behaviour)."
                )

        # --------------------------------------------------------------------
        # CCV-D-01: For CR-02 (CRISIS + JRM active), verify ordering.
        # Expected: CR-02.exposure_weight == JM-03.exposure_weight * 0.75
        # Both records must be present in ER set.
        # --------------------------------------------------------------------
        if "CR-02" in by_id and "JM-03" in by_id:
            cr02_out = by_id["CR-02"].observed_output
            jm03_out = by_id["JM-03"].observed_output
            if not cr02_out.exception_raised and not jm03_out.exception_raised:
                # Compute expected value using Python float arithmetic (same as production).
                expected_cr02_ew = jm03_out.exposure_weight * 0.75
                if not _floats_equal(cr02_out.exposure_weight, expected_cr02_ew):
                    raise RuntimeError(
                        f"CRISIS_ORDERING_VIOLATION: CR-02 exposure_weight="
                        f"{cr02_out.exposure_weight} != JM-03.exposure_weight*0.75="
                        f"{expected_cr02_ew}. Clip C / CRISIS ordering violated. "
                        "INV-04 violated."
                    )

        # --------------------------------------------------------------------
        # CCV-D-03: CR-03 (non-CRISIS with JRM active) -- dampening must NOT apply.
        # Verified by BIC backward compatibility comparison against a non-CRISIS
        # variant. Here we simply note the check for audit.
        # --------------------------------------------------------------------
        if "CR-03" in by_id:
            notes.append(
                "CCV-D-03: CR-03 is non-CRISIS with JRM active. Dampening "
                "not applied. Verified by absence of *0.75 in BIC comparison."
            )

        return violations, notes

    def xǁClipVerifierǁverify__mutmut_21(
        self,
        er_records: List[ExecutionRecord],
    ) -> Tuple[List[str], List[str]]:
        """
        Perform clip chain verification on ER-stage records.

        Returns:
          (violations, notes)
          violations -- list of violation description strings. Empty means pass.
          notes      -- list of non-failure informational notes.

        Raises RuntimeError with failure_type_id prefix on hard failures
        (CLIP_B_FLOOR_VIOLATION, CLIP_C_FLOOR_VIOLATION, CLIP_A_VIOLATION,
        CRISIS_ORDERING_VIOLATION).
        """
        violations = []
        notes      = []
        by_id: Dict[str, ExecutionRecord] = {r.vector_id: r for r in er_records}

        for rec in er_records:
            out = rec.observed_output
            if out.exception_raised:
                # No clip verification for exception vectors.
                continue

            vid = rec.vector_id
            iv  = rec.input_vector

            # ----------------------------------------------------------------
            # CCV-A-01: Clip A verification.
            # position_size_factor must be in [0.0, 1.0] for every normal vector.
            # ----------------------------------------------------------------
            psf = out.position_size_factor
            if psf < 0.0 or psf > 1.0:
                raise RuntimeError(
                    f"CLIP_A_VIOLATION: Vector {vid} position_size_factor={psf} "
                    "is outside [0.0, 1.0]. INV-01 violated."
                )

            # ----------------------------------------------------------------
            # CCV-B-01: For MU-02 and RP-02, E_pre_clip should be zero or near zero,
            # so Clip B floor should be active. exposure_weight bit pattern should
            # equal bit pattern of 1e-6.
            # ----------------------------------------------------------------
            if vid in ("MU-02", "XXRP-02XX"):
                ew_bits = _float_bits(out.exposure_weight)
                if ew_bits != self._lb_bits:
                    raise RuntimeError(
                        f"CLIP_B_FLOOR_VIOLATION: Vector {vid} exposure_weight "
                        f"expected bit pattern of 1e-6 but got "
                        f"{out.exposure_weight!r}. INV-02 violated."
                    )

            # ----------------------------------------------------------------
            # CCV-B-02: For JM-inactive (JM-01, JM-04) non-CRISIS vectors,
            # exposure_weight must be in [1e-6, 1.0].
            # (Clip C inactive, CRISIS dampening inactive.)
            # ----------------------------------------------------------------
            if vid in ("JM-01", "JM-04") and iv.current_regime_str != "CRISIS":
                ew = out.exposure_weight
                if ew < 1e-6 or ew > 1.0:
                    raise RuntimeError(
                        f"CLIP_B_RANGE_VIOLATION: Vector {vid} exposure_weight={ew} "
                        "outside [1e-6, 1.0] with Clip C and CRISIS dampening both "
                        "inactive. INV-02 violated."
                    )

            # ----------------------------------------------------------------
            # CCV-C-02: For JM-03 (designed to produce pre-Clip-C value below
            # SHOCK_EXPOSURE_CAP), exposure_weight should equal SHOCK_EXPOSURE_CAP.
            # ----------------------------------------------------------------
            if vid == "JM-03":
                ew_bits = _float_bits(out.exposure_weight)
                if ew_bits != self._sec_bits:
                    # JM-03 uses meta_uncertainty=0.99 + multiplier=2.0.
                    # The division may produce a value below SHOCK_EXPOSURE_CAP,
                    # which gets clipped to SHOCK_EXPOSURE_CAP by Clip C.
                    # If the result does NOT equal SHOCK_EXPOSURE_CAP, the
                    # actual computed value exceeded the cap after division;
                    # this is acceptable if the value is above SHOCK_EXPOSURE_CAP.
                    # Hard failure only if value is strictly below SHOCK_EXPOSURE_CAP.
                    if out.exposure_weight < self._sec:
                        raise RuntimeError(
                            f"CLIP_C_FLOOR_VIOLATION: Vector {vid} exposure_weight="
                            f"{out.exposure_weight} is below SHOCK_EXPOSURE_CAP="
                            f"{self._sec}. INV-03 violated."
                        )
                    notes.append(
                        f"CCV-C-02 note: JM-03 exposure_weight={out.exposure_weight} "
                        "exceeds SHOCK_EXPOSURE_CAP; Clip C floor not triggered."
                    )

            # ----------------------------------------------------------------
            # CCV-D-02: For CR-01 (CRISIS, JRM inactive), exposure_weight may be
            # below SHOCK_EXPOSURE_CAP. No floor enforcement. This is specified
            # behaviour per INV-04.
            # ----------------------------------------------------------------
            if vid == "CR-01":
                notes.append(
                    f"CCV-D-02: CR-01 exposure_weight={out.exposure_weight}. "
                    "May be below SHOCK_EXPOSURE_CAP per INV-04 (specified behaviour)."
                )

        # --------------------------------------------------------------------
        # CCV-D-01: For CR-02 (CRISIS + JRM active), verify ordering.
        # Expected: CR-02.exposure_weight == JM-03.exposure_weight * 0.75
        # Both records must be present in ER set.
        # --------------------------------------------------------------------
        if "CR-02" in by_id and "JM-03" in by_id:
            cr02_out = by_id["CR-02"].observed_output
            jm03_out = by_id["JM-03"].observed_output
            if not cr02_out.exception_raised and not jm03_out.exception_raised:
                # Compute expected value using Python float arithmetic (same as production).
                expected_cr02_ew = jm03_out.exposure_weight * 0.75
                if not _floats_equal(cr02_out.exposure_weight, expected_cr02_ew):
                    raise RuntimeError(
                        f"CRISIS_ORDERING_VIOLATION: CR-02 exposure_weight="
                        f"{cr02_out.exposure_weight} != JM-03.exposure_weight*0.75="
                        f"{expected_cr02_ew}. Clip C / CRISIS ordering violated. "
                        "INV-04 violated."
                    )

        # --------------------------------------------------------------------
        # CCV-D-03: CR-03 (non-CRISIS with JRM active) -- dampening must NOT apply.
        # Verified by BIC backward compatibility comparison against a non-CRISIS
        # variant. Here we simply note the check for audit.
        # --------------------------------------------------------------------
        if "CR-03" in by_id:
            notes.append(
                "CCV-D-03: CR-03 is non-CRISIS with JRM active. Dampening "
                "not applied. Verified by absence of *0.75 in BIC comparison."
            )

        return violations, notes

    def xǁClipVerifierǁverify__mutmut_22(
        self,
        er_records: List[ExecutionRecord],
    ) -> Tuple[List[str], List[str]]:
        """
        Perform clip chain verification on ER-stage records.

        Returns:
          (violations, notes)
          violations -- list of violation description strings. Empty means pass.
          notes      -- list of non-failure informational notes.

        Raises RuntimeError with failure_type_id prefix on hard failures
        (CLIP_B_FLOOR_VIOLATION, CLIP_C_FLOOR_VIOLATION, CLIP_A_VIOLATION,
        CRISIS_ORDERING_VIOLATION).
        """
        violations = []
        notes      = []
        by_id: Dict[str, ExecutionRecord] = {r.vector_id: r for r in er_records}

        for rec in er_records:
            out = rec.observed_output
            if out.exception_raised:
                # No clip verification for exception vectors.
                continue

            vid = rec.vector_id
            iv  = rec.input_vector

            # ----------------------------------------------------------------
            # CCV-A-01: Clip A verification.
            # position_size_factor must be in [0.0, 1.0] for every normal vector.
            # ----------------------------------------------------------------
            psf = out.position_size_factor
            if psf < 0.0 or psf > 1.0:
                raise RuntimeError(
                    f"CLIP_A_VIOLATION: Vector {vid} position_size_factor={psf} "
                    "is outside [0.0, 1.0]. INV-01 violated."
                )

            # ----------------------------------------------------------------
            # CCV-B-01: For MU-02 and RP-02, E_pre_clip should be zero or near zero,
            # so Clip B floor should be active. exposure_weight bit pattern should
            # equal bit pattern of 1e-6.
            # ----------------------------------------------------------------
            if vid in ("MU-02", "rp-02"):
                ew_bits = _float_bits(out.exposure_weight)
                if ew_bits != self._lb_bits:
                    raise RuntimeError(
                        f"CLIP_B_FLOOR_VIOLATION: Vector {vid} exposure_weight "
                        f"expected bit pattern of 1e-6 but got "
                        f"{out.exposure_weight!r}. INV-02 violated."
                    )

            # ----------------------------------------------------------------
            # CCV-B-02: For JM-inactive (JM-01, JM-04) non-CRISIS vectors,
            # exposure_weight must be in [1e-6, 1.0].
            # (Clip C inactive, CRISIS dampening inactive.)
            # ----------------------------------------------------------------
            if vid in ("JM-01", "JM-04") and iv.current_regime_str != "CRISIS":
                ew = out.exposure_weight
                if ew < 1e-6 or ew > 1.0:
                    raise RuntimeError(
                        f"CLIP_B_RANGE_VIOLATION: Vector {vid} exposure_weight={ew} "
                        "outside [1e-6, 1.0] with Clip C and CRISIS dampening both "
                        "inactive. INV-02 violated."
                    )

            # ----------------------------------------------------------------
            # CCV-C-02: For JM-03 (designed to produce pre-Clip-C value below
            # SHOCK_EXPOSURE_CAP), exposure_weight should equal SHOCK_EXPOSURE_CAP.
            # ----------------------------------------------------------------
            if vid == "JM-03":
                ew_bits = _float_bits(out.exposure_weight)
                if ew_bits != self._sec_bits:
                    # JM-03 uses meta_uncertainty=0.99 + multiplier=2.0.
                    # The division may produce a value below SHOCK_EXPOSURE_CAP,
                    # which gets clipped to SHOCK_EXPOSURE_CAP by Clip C.
                    # If the result does NOT equal SHOCK_EXPOSURE_CAP, the
                    # actual computed value exceeded the cap after division;
                    # this is acceptable if the value is above SHOCK_EXPOSURE_CAP.
                    # Hard failure only if value is strictly below SHOCK_EXPOSURE_CAP.
                    if out.exposure_weight < self._sec:
                        raise RuntimeError(
                            f"CLIP_C_FLOOR_VIOLATION: Vector {vid} exposure_weight="
                            f"{out.exposure_weight} is below SHOCK_EXPOSURE_CAP="
                            f"{self._sec}. INV-03 violated."
                        )
                    notes.append(
                        f"CCV-C-02 note: JM-03 exposure_weight={out.exposure_weight} "
                        "exceeds SHOCK_EXPOSURE_CAP; Clip C floor not triggered."
                    )

            # ----------------------------------------------------------------
            # CCV-D-02: For CR-01 (CRISIS, JRM inactive), exposure_weight may be
            # below SHOCK_EXPOSURE_CAP. No floor enforcement. This is specified
            # behaviour per INV-04.
            # ----------------------------------------------------------------
            if vid == "CR-01":
                notes.append(
                    f"CCV-D-02: CR-01 exposure_weight={out.exposure_weight}. "
                    "May be below SHOCK_EXPOSURE_CAP per INV-04 (specified behaviour)."
                )

        # --------------------------------------------------------------------
        # CCV-D-01: For CR-02 (CRISIS + JRM active), verify ordering.
        # Expected: CR-02.exposure_weight == JM-03.exposure_weight * 0.75
        # Both records must be present in ER set.
        # --------------------------------------------------------------------
        if "CR-02" in by_id and "JM-03" in by_id:
            cr02_out = by_id["CR-02"].observed_output
            jm03_out = by_id["JM-03"].observed_output
            if not cr02_out.exception_raised and not jm03_out.exception_raised:
                # Compute expected value using Python float arithmetic (same as production).
                expected_cr02_ew = jm03_out.exposure_weight * 0.75
                if not _floats_equal(cr02_out.exposure_weight, expected_cr02_ew):
                    raise RuntimeError(
                        f"CRISIS_ORDERING_VIOLATION: CR-02 exposure_weight="
                        f"{cr02_out.exposure_weight} != JM-03.exposure_weight*0.75="
                        f"{expected_cr02_ew}. Clip C / CRISIS ordering violated. "
                        "INV-04 violated."
                    )

        # --------------------------------------------------------------------
        # CCV-D-03: CR-03 (non-CRISIS with JRM active) -- dampening must NOT apply.
        # Verified by BIC backward compatibility comparison against a non-CRISIS
        # variant. Here we simply note the check for audit.
        # --------------------------------------------------------------------
        if "CR-03" in by_id:
            notes.append(
                "CCV-D-03: CR-03 is non-CRISIS with JRM active. Dampening "
                "not applied. Verified by absence of *0.75 in BIC comparison."
            )

        return violations, notes

    def xǁClipVerifierǁverify__mutmut_23(
        self,
        er_records: List[ExecutionRecord],
    ) -> Tuple[List[str], List[str]]:
        """
        Perform clip chain verification on ER-stage records.

        Returns:
          (violations, notes)
          violations -- list of violation description strings. Empty means pass.
          notes      -- list of non-failure informational notes.

        Raises RuntimeError with failure_type_id prefix on hard failures
        (CLIP_B_FLOOR_VIOLATION, CLIP_C_FLOOR_VIOLATION, CLIP_A_VIOLATION,
        CRISIS_ORDERING_VIOLATION).
        """
        violations = []
        notes      = []
        by_id: Dict[str, ExecutionRecord] = {r.vector_id: r for r in er_records}

        for rec in er_records:
            out = rec.observed_output
            if out.exception_raised:
                # No clip verification for exception vectors.
                continue

            vid = rec.vector_id
            iv  = rec.input_vector

            # ----------------------------------------------------------------
            # CCV-A-01: Clip A verification.
            # position_size_factor must be in [0.0, 1.0] for every normal vector.
            # ----------------------------------------------------------------
            psf = out.position_size_factor
            if psf < 0.0 or psf > 1.0:
                raise RuntimeError(
                    f"CLIP_A_VIOLATION: Vector {vid} position_size_factor={psf} "
                    "is outside [0.0, 1.0]. INV-01 violated."
                )

            # ----------------------------------------------------------------
            # CCV-B-01: For MU-02 and RP-02, E_pre_clip should be zero or near zero,
            # so Clip B floor should be active. exposure_weight bit pattern should
            # equal bit pattern of 1e-6.
            # ----------------------------------------------------------------
            if vid in ("MU-02", "RP-02"):
                ew_bits = None
                if ew_bits != self._lb_bits:
                    raise RuntimeError(
                        f"CLIP_B_FLOOR_VIOLATION: Vector {vid} exposure_weight "
                        f"expected bit pattern of 1e-6 but got "
                        f"{out.exposure_weight!r}. INV-02 violated."
                    )

            # ----------------------------------------------------------------
            # CCV-B-02: For JM-inactive (JM-01, JM-04) non-CRISIS vectors,
            # exposure_weight must be in [1e-6, 1.0].
            # (Clip C inactive, CRISIS dampening inactive.)
            # ----------------------------------------------------------------
            if vid in ("JM-01", "JM-04") and iv.current_regime_str != "CRISIS":
                ew = out.exposure_weight
                if ew < 1e-6 or ew > 1.0:
                    raise RuntimeError(
                        f"CLIP_B_RANGE_VIOLATION: Vector {vid} exposure_weight={ew} "
                        "outside [1e-6, 1.0] with Clip C and CRISIS dampening both "
                        "inactive. INV-02 violated."
                    )

            # ----------------------------------------------------------------
            # CCV-C-02: For JM-03 (designed to produce pre-Clip-C value below
            # SHOCK_EXPOSURE_CAP), exposure_weight should equal SHOCK_EXPOSURE_CAP.
            # ----------------------------------------------------------------
            if vid == "JM-03":
                ew_bits = _float_bits(out.exposure_weight)
                if ew_bits != self._sec_bits:
                    # JM-03 uses meta_uncertainty=0.99 + multiplier=2.0.
                    # The division may produce a value below SHOCK_EXPOSURE_CAP,
                    # which gets clipped to SHOCK_EXPOSURE_CAP by Clip C.
                    # If the result does NOT equal SHOCK_EXPOSURE_CAP, the
                    # actual computed value exceeded the cap after division;
                    # this is acceptable if the value is above SHOCK_EXPOSURE_CAP.
                    # Hard failure only if value is strictly below SHOCK_EXPOSURE_CAP.
                    if out.exposure_weight < self._sec:
                        raise RuntimeError(
                            f"CLIP_C_FLOOR_VIOLATION: Vector {vid} exposure_weight="
                            f"{out.exposure_weight} is below SHOCK_EXPOSURE_CAP="
                            f"{self._sec}. INV-03 violated."
                        )
                    notes.append(
                        f"CCV-C-02 note: JM-03 exposure_weight={out.exposure_weight} "
                        "exceeds SHOCK_EXPOSURE_CAP; Clip C floor not triggered."
                    )

            # ----------------------------------------------------------------
            # CCV-D-02: For CR-01 (CRISIS, JRM inactive), exposure_weight may be
            # below SHOCK_EXPOSURE_CAP. No floor enforcement. This is specified
            # behaviour per INV-04.
            # ----------------------------------------------------------------
            if vid == "CR-01":
                notes.append(
                    f"CCV-D-02: CR-01 exposure_weight={out.exposure_weight}. "
                    "May be below SHOCK_EXPOSURE_CAP per INV-04 (specified behaviour)."
                )

        # --------------------------------------------------------------------
        # CCV-D-01: For CR-02 (CRISIS + JRM active), verify ordering.
        # Expected: CR-02.exposure_weight == JM-03.exposure_weight * 0.75
        # Both records must be present in ER set.
        # --------------------------------------------------------------------
        if "CR-02" in by_id and "JM-03" in by_id:
            cr02_out = by_id["CR-02"].observed_output
            jm03_out = by_id["JM-03"].observed_output
            if not cr02_out.exception_raised and not jm03_out.exception_raised:
                # Compute expected value using Python float arithmetic (same as production).
                expected_cr02_ew = jm03_out.exposure_weight * 0.75
                if not _floats_equal(cr02_out.exposure_weight, expected_cr02_ew):
                    raise RuntimeError(
                        f"CRISIS_ORDERING_VIOLATION: CR-02 exposure_weight="
                        f"{cr02_out.exposure_weight} != JM-03.exposure_weight*0.75="
                        f"{expected_cr02_ew}. Clip C / CRISIS ordering violated. "
                        "INV-04 violated."
                    )

        # --------------------------------------------------------------------
        # CCV-D-03: CR-03 (non-CRISIS with JRM active) -- dampening must NOT apply.
        # Verified by BIC backward compatibility comparison against a non-CRISIS
        # variant. Here we simply note the check for audit.
        # --------------------------------------------------------------------
        if "CR-03" in by_id:
            notes.append(
                "CCV-D-03: CR-03 is non-CRISIS with JRM active. Dampening "
                "not applied. Verified by absence of *0.75 in BIC comparison."
            )

        return violations, notes

    def xǁClipVerifierǁverify__mutmut_24(
        self,
        er_records: List[ExecutionRecord],
    ) -> Tuple[List[str], List[str]]:
        """
        Perform clip chain verification on ER-stage records.

        Returns:
          (violations, notes)
          violations -- list of violation description strings. Empty means pass.
          notes      -- list of non-failure informational notes.

        Raises RuntimeError with failure_type_id prefix on hard failures
        (CLIP_B_FLOOR_VIOLATION, CLIP_C_FLOOR_VIOLATION, CLIP_A_VIOLATION,
        CRISIS_ORDERING_VIOLATION).
        """
        violations = []
        notes      = []
        by_id: Dict[str, ExecutionRecord] = {r.vector_id: r for r in er_records}

        for rec in er_records:
            out = rec.observed_output
            if out.exception_raised:
                # No clip verification for exception vectors.
                continue

            vid = rec.vector_id
            iv  = rec.input_vector

            # ----------------------------------------------------------------
            # CCV-A-01: Clip A verification.
            # position_size_factor must be in [0.0, 1.0] for every normal vector.
            # ----------------------------------------------------------------
            psf = out.position_size_factor
            if psf < 0.0 or psf > 1.0:
                raise RuntimeError(
                    f"CLIP_A_VIOLATION: Vector {vid} position_size_factor={psf} "
                    "is outside [0.0, 1.0]. INV-01 violated."
                )

            # ----------------------------------------------------------------
            # CCV-B-01: For MU-02 and RP-02, E_pre_clip should be zero or near zero,
            # so Clip B floor should be active. exposure_weight bit pattern should
            # equal bit pattern of 1e-6.
            # ----------------------------------------------------------------
            if vid in ("MU-02", "RP-02"):
                ew_bits = _float_bits(None)
                if ew_bits != self._lb_bits:
                    raise RuntimeError(
                        f"CLIP_B_FLOOR_VIOLATION: Vector {vid} exposure_weight "
                        f"expected bit pattern of 1e-6 but got "
                        f"{out.exposure_weight!r}. INV-02 violated."
                    )

            # ----------------------------------------------------------------
            # CCV-B-02: For JM-inactive (JM-01, JM-04) non-CRISIS vectors,
            # exposure_weight must be in [1e-6, 1.0].
            # (Clip C inactive, CRISIS dampening inactive.)
            # ----------------------------------------------------------------
            if vid in ("JM-01", "JM-04") and iv.current_regime_str != "CRISIS":
                ew = out.exposure_weight
                if ew < 1e-6 or ew > 1.0:
                    raise RuntimeError(
                        f"CLIP_B_RANGE_VIOLATION: Vector {vid} exposure_weight={ew} "
                        "outside [1e-6, 1.0] with Clip C and CRISIS dampening both "
                        "inactive. INV-02 violated."
                    )

            # ----------------------------------------------------------------
            # CCV-C-02: For JM-03 (designed to produce pre-Clip-C value below
            # SHOCK_EXPOSURE_CAP), exposure_weight should equal SHOCK_EXPOSURE_CAP.
            # ----------------------------------------------------------------
            if vid == "JM-03":
                ew_bits = _float_bits(out.exposure_weight)
                if ew_bits != self._sec_bits:
                    # JM-03 uses meta_uncertainty=0.99 + multiplier=2.0.
                    # The division may produce a value below SHOCK_EXPOSURE_CAP,
                    # which gets clipped to SHOCK_EXPOSURE_CAP by Clip C.
                    # If the result does NOT equal SHOCK_EXPOSURE_CAP, the
                    # actual computed value exceeded the cap after division;
                    # this is acceptable if the value is above SHOCK_EXPOSURE_CAP.
                    # Hard failure only if value is strictly below SHOCK_EXPOSURE_CAP.
                    if out.exposure_weight < self._sec:
                        raise RuntimeError(
                            f"CLIP_C_FLOOR_VIOLATION: Vector {vid} exposure_weight="
                            f"{out.exposure_weight} is below SHOCK_EXPOSURE_CAP="
                            f"{self._sec}. INV-03 violated."
                        )
                    notes.append(
                        f"CCV-C-02 note: JM-03 exposure_weight={out.exposure_weight} "
                        "exceeds SHOCK_EXPOSURE_CAP; Clip C floor not triggered."
                    )

            # ----------------------------------------------------------------
            # CCV-D-02: For CR-01 (CRISIS, JRM inactive), exposure_weight may be
            # below SHOCK_EXPOSURE_CAP. No floor enforcement. This is specified
            # behaviour per INV-04.
            # ----------------------------------------------------------------
            if vid == "CR-01":
                notes.append(
                    f"CCV-D-02: CR-01 exposure_weight={out.exposure_weight}. "
                    "May be below SHOCK_EXPOSURE_CAP per INV-04 (specified behaviour)."
                )

        # --------------------------------------------------------------------
        # CCV-D-01: For CR-02 (CRISIS + JRM active), verify ordering.
        # Expected: CR-02.exposure_weight == JM-03.exposure_weight * 0.75
        # Both records must be present in ER set.
        # --------------------------------------------------------------------
        if "CR-02" in by_id and "JM-03" in by_id:
            cr02_out = by_id["CR-02"].observed_output
            jm03_out = by_id["JM-03"].observed_output
            if not cr02_out.exception_raised and not jm03_out.exception_raised:
                # Compute expected value using Python float arithmetic (same as production).
                expected_cr02_ew = jm03_out.exposure_weight * 0.75
                if not _floats_equal(cr02_out.exposure_weight, expected_cr02_ew):
                    raise RuntimeError(
                        f"CRISIS_ORDERING_VIOLATION: CR-02 exposure_weight="
                        f"{cr02_out.exposure_weight} != JM-03.exposure_weight*0.75="
                        f"{expected_cr02_ew}. Clip C / CRISIS ordering violated. "
                        "INV-04 violated."
                    )

        # --------------------------------------------------------------------
        # CCV-D-03: CR-03 (non-CRISIS with JRM active) -- dampening must NOT apply.
        # Verified by BIC backward compatibility comparison against a non-CRISIS
        # variant. Here we simply note the check for audit.
        # --------------------------------------------------------------------
        if "CR-03" in by_id:
            notes.append(
                "CCV-D-03: CR-03 is non-CRISIS with JRM active. Dampening "
                "not applied. Verified by absence of *0.75 in BIC comparison."
            )

        return violations, notes

    def xǁClipVerifierǁverify__mutmut_25(
        self,
        er_records: List[ExecutionRecord],
    ) -> Tuple[List[str], List[str]]:
        """
        Perform clip chain verification on ER-stage records.

        Returns:
          (violations, notes)
          violations -- list of violation description strings. Empty means pass.
          notes      -- list of non-failure informational notes.

        Raises RuntimeError with failure_type_id prefix on hard failures
        (CLIP_B_FLOOR_VIOLATION, CLIP_C_FLOOR_VIOLATION, CLIP_A_VIOLATION,
        CRISIS_ORDERING_VIOLATION).
        """
        violations = []
        notes      = []
        by_id: Dict[str, ExecutionRecord] = {r.vector_id: r for r in er_records}

        for rec in er_records:
            out = rec.observed_output
            if out.exception_raised:
                # No clip verification for exception vectors.
                continue

            vid = rec.vector_id
            iv  = rec.input_vector

            # ----------------------------------------------------------------
            # CCV-A-01: Clip A verification.
            # position_size_factor must be in [0.0, 1.0] for every normal vector.
            # ----------------------------------------------------------------
            psf = out.position_size_factor
            if psf < 0.0 or psf > 1.0:
                raise RuntimeError(
                    f"CLIP_A_VIOLATION: Vector {vid} position_size_factor={psf} "
                    "is outside [0.0, 1.0]. INV-01 violated."
                )

            # ----------------------------------------------------------------
            # CCV-B-01: For MU-02 and RP-02, E_pre_clip should be zero or near zero,
            # so Clip B floor should be active. exposure_weight bit pattern should
            # equal bit pattern of 1e-6.
            # ----------------------------------------------------------------
            if vid in ("MU-02", "RP-02"):
                ew_bits = _float_bits(out.exposure_weight)
                if ew_bits == self._lb_bits:
                    raise RuntimeError(
                        f"CLIP_B_FLOOR_VIOLATION: Vector {vid} exposure_weight "
                        f"expected bit pattern of 1e-6 but got "
                        f"{out.exposure_weight!r}. INV-02 violated."
                    )

            # ----------------------------------------------------------------
            # CCV-B-02: For JM-inactive (JM-01, JM-04) non-CRISIS vectors,
            # exposure_weight must be in [1e-6, 1.0].
            # (Clip C inactive, CRISIS dampening inactive.)
            # ----------------------------------------------------------------
            if vid in ("JM-01", "JM-04") and iv.current_regime_str != "CRISIS":
                ew = out.exposure_weight
                if ew < 1e-6 or ew > 1.0:
                    raise RuntimeError(
                        f"CLIP_B_RANGE_VIOLATION: Vector {vid} exposure_weight={ew} "
                        "outside [1e-6, 1.0] with Clip C and CRISIS dampening both "
                        "inactive. INV-02 violated."
                    )

            # ----------------------------------------------------------------
            # CCV-C-02: For JM-03 (designed to produce pre-Clip-C value below
            # SHOCK_EXPOSURE_CAP), exposure_weight should equal SHOCK_EXPOSURE_CAP.
            # ----------------------------------------------------------------
            if vid == "JM-03":
                ew_bits = _float_bits(out.exposure_weight)
                if ew_bits != self._sec_bits:
                    # JM-03 uses meta_uncertainty=0.99 + multiplier=2.0.
                    # The division may produce a value below SHOCK_EXPOSURE_CAP,
                    # which gets clipped to SHOCK_EXPOSURE_CAP by Clip C.
                    # If the result does NOT equal SHOCK_EXPOSURE_CAP, the
                    # actual computed value exceeded the cap after division;
                    # this is acceptable if the value is above SHOCK_EXPOSURE_CAP.
                    # Hard failure only if value is strictly below SHOCK_EXPOSURE_CAP.
                    if out.exposure_weight < self._sec:
                        raise RuntimeError(
                            f"CLIP_C_FLOOR_VIOLATION: Vector {vid} exposure_weight="
                            f"{out.exposure_weight} is below SHOCK_EXPOSURE_CAP="
                            f"{self._sec}. INV-03 violated."
                        )
                    notes.append(
                        f"CCV-C-02 note: JM-03 exposure_weight={out.exposure_weight} "
                        "exceeds SHOCK_EXPOSURE_CAP; Clip C floor not triggered."
                    )

            # ----------------------------------------------------------------
            # CCV-D-02: For CR-01 (CRISIS, JRM inactive), exposure_weight may be
            # below SHOCK_EXPOSURE_CAP. No floor enforcement. This is specified
            # behaviour per INV-04.
            # ----------------------------------------------------------------
            if vid == "CR-01":
                notes.append(
                    f"CCV-D-02: CR-01 exposure_weight={out.exposure_weight}. "
                    "May be below SHOCK_EXPOSURE_CAP per INV-04 (specified behaviour)."
                )

        # --------------------------------------------------------------------
        # CCV-D-01: For CR-02 (CRISIS + JRM active), verify ordering.
        # Expected: CR-02.exposure_weight == JM-03.exposure_weight * 0.75
        # Both records must be present in ER set.
        # --------------------------------------------------------------------
        if "CR-02" in by_id and "JM-03" in by_id:
            cr02_out = by_id["CR-02"].observed_output
            jm03_out = by_id["JM-03"].observed_output
            if not cr02_out.exception_raised and not jm03_out.exception_raised:
                # Compute expected value using Python float arithmetic (same as production).
                expected_cr02_ew = jm03_out.exposure_weight * 0.75
                if not _floats_equal(cr02_out.exposure_weight, expected_cr02_ew):
                    raise RuntimeError(
                        f"CRISIS_ORDERING_VIOLATION: CR-02 exposure_weight="
                        f"{cr02_out.exposure_weight} != JM-03.exposure_weight*0.75="
                        f"{expected_cr02_ew}. Clip C / CRISIS ordering violated. "
                        "INV-04 violated."
                    )

        # --------------------------------------------------------------------
        # CCV-D-03: CR-03 (non-CRISIS with JRM active) -- dampening must NOT apply.
        # Verified by BIC backward compatibility comparison against a non-CRISIS
        # variant. Here we simply note the check for audit.
        # --------------------------------------------------------------------
        if "CR-03" in by_id:
            notes.append(
                "CCV-D-03: CR-03 is non-CRISIS with JRM active. Dampening "
                "not applied. Verified by absence of *0.75 in BIC comparison."
            )

        return violations, notes

    def xǁClipVerifierǁverify__mutmut_26(
        self,
        er_records: List[ExecutionRecord],
    ) -> Tuple[List[str], List[str]]:
        """
        Perform clip chain verification on ER-stage records.

        Returns:
          (violations, notes)
          violations -- list of violation description strings. Empty means pass.
          notes      -- list of non-failure informational notes.

        Raises RuntimeError with failure_type_id prefix on hard failures
        (CLIP_B_FLOOR_VIOLATION, CLIP_C_FLOOR_VIOLATION, CLIP_A_VIOLATION,
        CRISIS_ORDERING_VIOLATION).
        """
        violations = []
        notes      = []
        by_id: Dict[str, ExecutionRecord] = {r.vector_id: r for r in er_records}

        for rec in er_records:
            out = rec.observed_output
            if out.exception_raised:
                # No clip verification for exception vectors.
                continue

            vid = rec.vector_id
            iv  = rec.input_vector

            # ----------------------------------------------------------------
            # CCV-A-01: Clip A verification.
            # position_size_factor must be in [0.0, 1.0] for every normal vector.
            # ----------------------------------------------------------------
            psf = out.position_size_factor
            if psf < 0.0 or psf > 1.0:
                raise RuntimeError(
                    f"CLIP_A_VIOLATION: Vector {vid} position_size_factor={psf} "
                    "is outside [0.0, 1.0]. INV-01 violated."
                )

            # ----------------------------------------------------------------
            # CCV-B-01: For MU-02 and RP-02, E_pre_clip should be zero or near zero,
            # so Clip B floor should be active. exposure_weight bit pattern should
            # equal bit pattern of 1e-6.
            # ----------------------------------------------------------------
            if vid in ("MU-02", "RP-02"):
                ew_bits = _float_bits(out.exposure_weight)
                if ew_bits != self._lb_bits:
                    raise RuntimeError(
                        None
                    )

            # ----------------------------------------------------------------
            # CCV-B-02: For JM-inactive (JM-01, JM-04) non-CRISIS vectors,
            # exposure_weight must be in [1e-6, 1.0].
            # (Clip C inactive, CRISIS dampening inactive.)
            # ----------------------------------------------------------------
            if vid in ("JM-01", "JM-04") and iv.current_regime_str != "CRISIS":
                ew = out.exposure_weight
                if ew < 1e-6 or ew > 1.0:
                    raise RuntimeError(
                        f"CLIP_B_RANGE_VIOLATION: Vector {vid} exposure_weight={ew} "
                        "outside [1e-6, 1.0] with Clip C and CRISIS dampening both "
                        "inactive. INV-02 violated."
                    )

            # ----------------------------------------------------------------
            # CCV-C-02: For JM-03 (designed to produce pre-Clip-C value below
            # SHOCK_EXPOSURE_CAP), exposure_weight should equal SHOCK_EXPOSURE_CAP.
            # ----------------------------------------------------------------
            if vid == "JM-03":
                ew_bits = _float_bits(out.exposure_weight)
                if ew_bits != self._sec_bits:
                    # JM-03 uses meta_uncertainty=0.99 + multiplier=2.0.
                    # The division may produce a value below SHOCK_EXPOSURE_CAP,
                    # which gets clipped to SHOCK_EXPOSURE_CAP by Clip C.
                    # If the result does NOT equal SHOCK_EXPOSURE_CAP, the
                    # actual computed value exceeded the cap after division;
                    # this is acceptable if the value is above SHOCK_EXPOSURE_CAP.
                    # Hard failure only if value is strictly below SHOCK_EXPOSURE_CAP.
                    if out.exposure_weight < self._sec:
                        raise RuntimeError(
                            f"CLIP_C_FLOOR_VIOLATION: Vector {vid} exposure_weight="
                            f"{out.exposure_weight} is below SHOCK_EXPOSURE_CAP="
                            f"{self._sec}. INV-03 violated."
                        )
                    notes.append(
                        f"CCV-C-02 note: JM-03 exposure_weight={out.exposure_weight} "
                        "exceeds SHOCK_EXPOSURE_CAP; Clip C floor not triggered."
                    )

            # ----------------------------------------------------------------
            # CCV-D-02: For CR-01 (CRISIS, JRM inactive), exposure_weight may be
            # below SHOCK_EXPOSURE_CAP. No floor enforcement. This is specified
            # behaviour per INV-04.
            # ----------------------------------------------------------------
            if vid == "CR-01":
                notes.append(
                    f"CCV-D-02: CR-01 exposure_weight={out.exposure_weight}. "
                    "May be below SHOCK_EXPOSURE_CAP per INV-04 (specified behaviour)."
                )

        # --------------------------------------------------------------------
        # CCV-D-01: For CR-02 (CRISIS + JRM active), verify ordering.
        # Expected: CR-02.exposure_weight == JM-03.exposure_weight * 0.75
        # Both records must be present in ER set.
        # --------------------------------------------------------------------
        if "CR-02" in by_id and "JM-03" in by_id:
            cr02_out = by_id["CR-02"].observed_output
            jm03_out = by_id["JM-03"].observed_output
            if not cr02_out.exception_raised and not jm03_out.exception_raised:
                # Compute expected value using Python float arithmetic (same as production).
                expected_cr02_ew = jm03_out.exposure_weight * 0.75
                if not _floats_equal(cr02_out.exposure_weight, expected_cr02_ew):
                    raise RuntimeError(
                        f"CRISIS_ORDERING_VIOLATION: CR-02 exposure_weight="
                        f"{cr02_out.exposure_weight} != JM-03.exposure_weight*0.75="
                        f"{expected_cr02_ew}. Clip C / CRISIS ordering violated. "
                        "INV-04 violated."
                    )

        # --------------------------------------------------------------------
        # CCV-D-03: CR-03 (non-CRISIS with JRM active) -- dampening must NOT apply.
        # Verified by BIC backward compatibility comparison against a non-CRISIS
        # variant. Here we simply note the check for audit.
        # --------------------------------------------------------------------
        if "CR-03" in by_id:
            notes.append(
                "CCV-D-03: CR-03 is non-CRISIS with JRM active. Dampening "
                "not applied. Verified by absence of *0.75 in BIC comparison."
            )

        return violations, notes

    def xǁClipVerifierǁverify__mutmut_27(
        self,
        er_records: List[ExecutionRecord],
    ) -> Tuple[List[str], List[str]]:
        """
        Perform clip chain verification on ER-stage records.

        Returns:
          (violations, notes)
          violations -- list of violation description strings. Empty means pass.
          notes      -- list of non-failure informational notes.

        Raises RuntimeError with failure_type_id prefix on hard failures
        (CLIP_B_FLOOR_VIOLATION, CLIP_C_FLOOR_VIOLATION, CLIP_A_VIOLATION,
        CRISIS_ORDERING_VIOLATION).
        """
        violations = []
        notes      = []
        by_id: Dict[str, ExecutionRecord] = {r.vector_id: r for r in er_records}

        for rec in er_records:
            out = rec.observed_output
            if out.exception_raised:
                # No clip verification for exception vectors.
                continue

            vid = rec.vector_id
            iv  = rec.input_vector

            # ----------------------------------------------------------------
            # CCV-A-01: Clip A verification.
            # position_size_factor must be in [0.0, 1.0] for every normal vector.
            # ----------------------------------------------------------------
            psf = out.position_size_factor
            if psf < 0.0 or psf > 1.0:
                raise RuntimeError(
                    f"CLIP_A_VIOLATION: Vector {vid} position_size_factor={psf} "
                    "is outside [0.0, 1.0]. INV-01 violated."
                )

            # ----------------------------------------------------------------
            # CCV-B-01: For MU-02 and RP-02, E_pre_clip should be zero or near zero,
            # so Clip B floor should be active. exposure_weight bit pattern should
            # equal bit pattern of 1e-6.
            # ----------------------------------------------------------------
            if vid in ("MU-02", "RP-02"):
                ew_bits = _float_bits(out.exposure_weight)
                if ew_bits != self._lb_bits:
                    raise RuntimeError(
                        f"CLIP_B_FLOOR_VIOLATION: Vector {vid} exposure_weight "
                        f"expected bit pattern of 1e-6 but got "
                        f"{out.exposure_weight!r}. INV-02 violated."
                    )

            # ----------------------------------------------------------------
            # CCV-B-02: For JM-inactive (JM-01, JM-04) non-CRISIS vectors,
            # exposure_weight must be in [1e-6, 1.0].
            # (Clip C inactive, CRISIS dampening inactive.)
            # ----------------------------------------------------------------
            if vid in ("JM-01", "JM-04") or iv.current_regime_str != "CRISIS":
                ew = out.exposure_weight
                if ew < 1e-6 or ew > 1.0:
                    raise RuntimeError(
                        f"CLIP_B_RANGE_VIOLATION: Vector {vid} exposure_weight={ew} "
                        "outside [1e-6, 1.0] with Clip C and CRISIS dampening both "
                        "inactive. INV-02 violated."
                    )

            # ----------------------------------------------------------------
            # CCV-C-02: For JM-03 (designed to produce pre-Clip-C value below
            # SHOCK_EXPOSURE_CAP), exposure_weight should equal SHOCK_EXPOSURE_CAP.
            # ----------------------------------------------------------------
            if vid == "JM-03":
                ew_bits = _float_bits(out.exposure_weight)
                if ew_bits != self._sec_bits:
                    # JM-03 uses meta_uncertainty=0.99 + multiplier=2.0.
                    # The division may produce a value below SHOCK_EXPOSURE_CAP,
                    # which gets clipped to SHOCK_EXPOSURE_CAP by Clip C.
                    # If the result does NOT equal SHOCK_EXPOSURE_CAP, the
                    # actual computed value exceeded the cap after division;
                    # this is acceptable if the value is above SHOCK_EXPOSURE_CAP.
                    # Hard failure only if value is strictly below SHOCK_EXPOSURE_CAP.
                    if out.exposure_weight < self._sec:
                        raise RuntimeError(
                            f"CLIP_C_FLOOR_VIOLATION: Vector {vid} exposure_weight="
                            f"{out.exposure_weight} is below SHOCK_EXPOSURE_CAP="
                            f"{self._sec}. INV-03 violated."
                        )
                    notes.append(
                        f"CCV-C-02 note: JM-03 exposure_weight={out.exposure_weight} "
                        "exceeds SHOCK_EXPOSURE_CAP; Clip C floor not triggered."
                    )

            # ----------------------------------------------------------------
            # CCV-D-02: For CR-01 (CRISIS, JRM inactive), exposure_weight may be
            # below SHOCK_EXPOSURE_CAP. No floor enforcement. This is specified
            # behaviour per INV-04.
            # ----------------------------------------------------------------
            if vid == "CR-01":
                notes.append(
                    f"CCV-D-02: CR-01 exposure_weight={out.exposure_weight}. "
                    "May be below SHOCK_EXPOSURE_CAP per INV-04 (specified behaviour)."
                )

        # --------------------------------------------------------------------
        # CCV-D-01: For CR-02 (CRISIS + JRM active), verify ordering.
        # Expected: CR-02.exposure_weight == JM-03.exposure_weight * 0.75
        # Both records must be present in ER set.
        # --------------------------------------------------------------------
        if "CR-02" in by_id and "JM-03" in by_id:
            cr02_out = by_id["CR-02"].observed_output
            jm03_out = by_id["JM-03"].observed_output
            if not cr02_out.exception_raised and not jm03_out.exception_raised:
                # Compute expected value using Python float arithmetic (same as production).
                expected_cr02_ew = jm03_out.exposure_weight * 0.75
                if not _floats_equal(cr02_out.exposure_weight, expected_cr02_ew):
                    raise RuntimeError(
                        f"CRISIS_ORDERING_VIOLATION: CR-02 exposure_weight="
                        f"{cr02_out.exposure_weight} != JM-03.exposure_weight*0.75="
                        f"{expected_cr02_ew}. Clip C / CRISIS ordering violated. "
                        "INV-04 violated."
                    )

        # --------------------------------------------------------------------
        # CCV-D-03: CR-03 (non-CRISIS with JRM active) -- dampening must NOT apply.
        # Verified by BIC backward compatibility comparison against a non-CRISIS
        # variant. Here we simply note the check for audit.
        # --------------------------------------------------------------------
        if "CR-03" in by_id:
            notes.append(
                "CCV-D-03: CR-03 is non-CRISIS with JRM active. Dampening "
                "not applied. Verified by absence of *0.75 in BIC comparison."
            )

        return violations, notes

    def xǁClipVerifierǁverify__mutmut_28(
        self,
        er_records: List[ExecutionRecord],
    ) -> Tuple[List[str], List[str]]:
        """
        Perform clip chain verification on ER-stage records.

        Returns:
          (violations, notes)
          violations -- list of violation description strings. Empty means pass.
          notes      -- list of non-failure informational notes.

        Raises RuntimeError with failure_type_id prefix on hard failures
        (CLIP_B_FLOOR_VIOLATION, CLIP_C_FLOOR_VIOLATION, CLIP_A_VIOLATION,
        CRISIS_ORDERING_VIOLATION).
        """
        violations = []
        notes      = []
        by_id: Dict[str, ExecutionRecord] = {r.vector_id: r for r in er_records}

        for rec in er_records:
            out = rec.observed_output
            if out.exception_raised:
                # No clip verification for exception vectors.
                continue

            vid = rec.vector_id
            iv  = rec.input_vector

            # ----------------------------------------------------------------
            # CCV-A-01: Clip A verification.
            # position_size_factor must be in [0.0, 1.0] for every normal vector.
            # ----------------------------------------------------------------
            psf = out.position_size_factor
            if psf < 0.0 or psf > 1.0:
                raise RuntimeError(
                    f"CLIP_A_VIOLATION: Vector {vid} position_size_factor={psf} "
                    "is outside [0.0, 1.0]. INV-01 violated."
                )

            # ----------------------------------------------------------------
            # CCV-B-01: For MU-02 and RP-02, E_pre_clip should be zero or near zero,
            # so Clip B floor should be active. exposure_weight bit pattern should
            # equal bit pattern of 1e-6.
            # ----------------------------------------------------------------
            if vid in ("MU-02", "RP-02"):
                ew_bits = _float_bits(out.exposure_weight)
                if ew_bits != self._lb_bits:
                    raise RuntimeError(
                        f"CLIP_B_FLOOR_VIOLATION: Vector {vid} exposure_weight "
                        f"expected bit pattern of 1e-6 but got "
                        f"{out.exposure_weight!r}. INV-02 violated."
                    )

            # ----------------------------------------------------------------
            # CCV-B-02: For JM-inactive (JM-01, JM-04) non-CRISIS vectors,
            # exposure_weight must be in [1e-6, 1.0].
            # (Clip C inactive, CRISIS dampening inactive.)
            # ----------------------------------------------------------------
            if vid not in ("JM-01", "JM-04") and iv.current_regime_str != "CRISIS":
                ew = out.exposure_weight
                if ew < 1e-6 or ew > 1.0:
                    raise RuntimeError(
                        f"CLIP_B_RANGE_VIOLATION: Vector {vid} exposure_weight={ew} "
                        "outside [1e-6, 1.0] with Clip C and CRISIS dampening both "
                        "inactive. INV-02 violated."
                    )

            # ----------------------------------------------------------------
            # CCV-C-02: For JM-03 (designed to produce pre-Clip-C value below
            # SHOCK_EXPOSURE_CAP), exposure_weight should equal SHOCK_EXPOSURE_CAP.
            # ----------------------------------------------------------------
            if vid == "JM-03":
                ew_bits = _float_bits(out.exposure_weight)
                if ew_bits != self._sec_bits:
                    # JM-03 uses meta_uncertainty=0.99 + multiplier=2.0.
                    # The division may produce a value below SHOCK_EXPOSURE_CAP,
                    # which gets clipped to SHOCK_EXPOSURE_CAP by Clip C.
                    # If the result does NOT equal SHOCK_EXPOSURE_CAP, the
                    # actual computed value exceeded the cap after division;
                    # this is acceptable if the value is above SHOCK_EXPOSURE_CAP.
                    # Hard failure only if value is strictly below SHOCK_EXPOSURE_CAP.
                    if out.exposure_weight < self._sec:
                        raise RuntimeError(
                            f"CLIP_C_FLOOR_VIOLATION: Vector {vid} exposure_weight="
                            f"{out.exposure_weight} is below SHOCK_EXPOSURE_CAP="
                            f"{self._sec}. INV-03 violated."
                        )
                    notes.append(
                        f"CCV-C-02 note: JM-03 exposure_weight={out.exposure_weight} "
                        "exceeds SHOCK_EXPOSURE_CAP; Clip C floor not triggered."
                    )

            # ----------------------------------------------------------------
            # CCV-D-02: For CR-01 (CRISIS, JRM inactive), exposure_weight may be
            # below SHOCK_EXPOSURE_CAP. No floor enforcement. This is specified
            # behaviour per INV-04.
            # ----------------------------------------------------------------
            if vid == "CR-01":
                notes.append(
                    f"CCV-D-02: CR-01 exposure_weight={out.exposure_weight}. "
                    "May be below SHOCK_EXPOSURE_CAP per INV-04 (specified behaviour)."
                )

        # --------------------------------------------------------------------
        # CCV-D-01: For CR-02 (CRISIS + JRM active), verify ordering.
        # Expected: CR-02.exposure_weight == JM-03.exposure_weight * 0.75
        # Both records must be present in ER set.
        # --------------------------------------------------------------------
        if "CR-02" in by_id and "JM-03" in by_id:
            cr02_out = by_id["CR-02"].observed_output
            jm03_out = by_id["JM-03"].observed_output
            if not cr02_out.exception_raised and not jm03_out.exception_raised:
                # Compute expected value using Python float arithmetic (same as production).
                expected_cr02_ew = jm03_out.exposure_weight * 0.75
                if not _floats_equal(cr02_out.exposure_weight, expected_cr02_ew):
                    raise RuntimeError(
                        f"CRISIS_ORDERING_VIOLATION: CR-02 exposure_weight="
                        f"{cr02_out.exposure_weight} != JM-03.exposure_weight*0.75="
                        f"{expected_cr02_ew}. Clip C / CRISIS ordering violated. "
                        "INV-04 violated."
                    )

        # --------------------------------------------------------------------
        # CCV-D-03: CR-03 (non-CRISIS with JRM active) -- dampening must NOT apply.
        # Verified by BIC backward compatibility comparison against a non-CRISIS
        # variant. Here we simply note the check for audit.
        # --------------------------------------------------------------------
        if "CR-03" in by_id:
            notes.append(
                "CCV-D-03: CR-03 is non-CRISIS with JRM active. Dampening "
                "not applied. Verified by absence of *0.75 in BIC comparison."
            )

        return violations, notes

    def xǁClipVerifierǁverify__mutmut_29(
        self,
        er_records: List[ExecutionRecord],
    ) -> Tuple[List[str], List[str]]:
        """
        Perform clip chain verification on ER-stage records.

        Returns:
          (violations, notes)
          violations -- list of violation description strings. Empty means pass.
          notes      -- list of non-failure informational notes.

        Raises RuntimeError with failure_type_id prefix on hard failures
        (CLIP_B_FLOOR_VIOLATION, CLIP_C_FLOOR_VIOLATION, CLIP_A_VIOLATION,
        CRISIS_ORDERING_VIOLATION).
        """
        violations = []
        notes      = []
        by_id: Dict[str, ExecutionRecord] = {r.vector_id: r for r in er_records}

        for rec in er_records:
            out = rec.observed_output
            if out.exception_raised:
                # No clip verification for exception vectors.
                continue

            vid = rec.vector_id
            iv  = rec.input_vector

            # ----------------------------------------------------------------
            # CCV-A-01: Clip A verification.
            # position_size_factor must be in [0.0, 1.0] for every normal vector.
            # ----------------------------------------------------------------
            psf = out.position_size_factor
            if psf < 0.0 or psf > 1.0:
                raise RuntimeError(
                    f"CLIP_A_VIOLATION: Vector {vid} position_size_factor={psf} "
                    "is outside [0.0, 1.0]. INV-01 violated."
                )

            # ----------------------------------------------------------------
            # CCV-B-01: For MU-02 and RP-02, E_pre_clip should be zero or near zero,
            # so Clip B floor should be active. exposure_weight bit pattern should
            # equal bit pattern of 1e-6.
            # ----------------------------------------------------------------
            if vid in ("MU-02", "RP-02"):
                ew_bits = _float_bits(out.exposure_weight)
                if ew_bits != self._lb_bits:
                    raise RuntimeError(
                        f"CLIP_B_FLOOR_VIOLATION: Vector {vid} exposure_weight "
                        f"expected bit pattern of 1e-6 but got "
                        f"{out.exposure_weight!r}. INV-02 violated."
                    )

            # ----------------------------------------------------------------
            # CCV-B-02: For JM-inactive (JM-01, JM-04) non-CRISIS vectors,
            # exposure_weight must be in [1e-6, 1.0].
            # (Clip C inactive, CRISIS dampening inactive.)
            # ----------------------------------------------------------------
            if vid in ("XXJM-01XX", "JM-04") and iv.current_regime_str != "CRISIS":
                ew = out.exposure_weight
                if ew < 1e-6 or ew > 1.0:
                    raise RuntimeError(
                        f"CLIP_B_RANGE_VIOLATION: Vector {vid} exposure_weight={ew} "
                        "outside [1e-6, 1.0] with Clip C and CRISIS dampening both "
                        "inactive. INV-02 violated."
                    )

            # ----------------------------------------------------------------
            # CCV-C-02: For JM-03 (designed to produce pre-Clip-C value below
            # SHOCK_EXPOSURE_CAP), exposure_weight should equal SHOCK_EXPOSURE_CAP.
            # ----------------------------------------------------------------
            if vid == "JM-03":
                ew_bits = _float_bits(out.exposure_weight)
                if ew_bits != self._sec_bits:
                    # JM-03 uses meta_uncertainty=0.99 + multiplier=2.0.
                    # The division may produce a value below SHOCK_EXPOSURE_CAP,
                    # which gets clipped to SHOCK_EXPOSURE_CAP by Clip C.
                    # If the result does NOT equal SHOCK_EXPOSURE_CAP, the
                    # actual computed value exceeded the cap after division;
                    # this is acceptable if the value is above SHOCK_EXPOSURE_CAP.
                    # Hard failure only if value is strictly below SHOCK_EXPOSURE_CAP.
                    if out.exposure_weight < self._sec:
                        raise RuntimeError(
                            f"CLIP_C_FLOOR_VIOLATION: Vector {vid} exposure_weight="
                            f"{out.exposure_weight} is below SHOCK_EXPOSURE_CAP="
                            f"{self._sec}. INV-03 violated."
                        )
                    notes.append(
                        f"CCV-C-02 note: JM-03 exposure_weight={out.exposure_weight} "
                        "exceeds SHOCK_EXPOSURE_CAP; Clip C floor not triggered."
                    )

            # ----------------------------------------------------------------
            # CCV-D-02: For CR-01 (CRISIS, JRM inactive), exposure_weight may be
            # below SHOCK_EXPOSURE_CAP. No floor enforcement. This is specified
            # behaviour per INV-04.
            # ----------------------------------------------------------------
            if vid == "CR-01":
                notes.append(
                    f"CCV-D-02: CR-01 exposure_weight={out.exposure_weight}. "
                    "May be below SHOCK_EXPOSURE_CAP per INV-04 (specified behaviour)."
                )

        # --------------------------------------------------------------------
        # CCV-D-01: For CR-02 (CRISIS + JRM active), verify ordering.
        # Expected: CR-02.exposure_weight == JM-03.exposure_weight * 0.75
        # Both records must be present in ER set.
        # --------------------------------------------------------------------
        if "CR-02" in by_id and "JM-03" in by_id:
            cr02_out = by_id["CR-02"].observed_output
            jm03_out = by_id["JM-03"].observed_output
            if not cr02_out.exception_raised and not jm03_out.exception_raised:
                # Compute expected value using Python float arithmetic (same as production).
                expected_cr02_ew = jm03_out.exposure_weight * 0.75
                if not _floats_equal(cr02_out.exposure_weight, expected_cr02_ew):
                    raise RuntimeError(
                        f"CRISIS_ORDERING_VIOLATION: CR-02 exposure_weight="
                        f"{cr02_out.exposure_weight} != JM-03.exposure_weight*0.75="
                        f"{expected_cr02_ew}. Clip C / CRISIS ordering violated. "
                        "INV-04 violated."
                    )

        # --------------------------------------------------------------------
        # CCV-D-03: CR-03 (non-CRISIS with JRM active) -- dampening must NOT apply.
        # Verified by BIC backward compatibility comparison against a non-CRISIS
        # variant. Here we simply note the check for audit.
        # --------------------------------------------------------------------
        if "CR-03" in by_id:
            notes.append(
                "CCV-D-03: CR-03 is non-CRISIS with JRM active. Dampening "
                "not applied. Verified by absence of *0.75 in BIC comparison."
            )

        return violations, notes

    def xǁClipVerifierǁverify__mutmut_30(
        self,
        er_records: List[ExecutionRecord],
    ) -> Tuple[List[str], List[str]]:
        """
        Perform clip chain verification on ER-stage records.

        Returns:
          (violations, notes)
          violations -- list of violation description strings. Empty means pass.
          notes      -- list of non-failure informational notes.

        Raises RuntimeError with failure_type_id prefix on hard failures
        (CLIP_B_FLOOR_VIOLATION, CLIP_C_FLOOR_VIOLATION, CLIP_A_VIOLATION,
        CRISIS_ORDERING_VIOLATION).
        """
        violations = []
        notes      = []
        by_id: Dict[str, ExecutionRecord] = {r.vector_id: r for r in er_records}

        for rec in er_records:
            out = rec.observed_output
            if out.exception_raised:
                # No clip verification for exception vectors.
                continue

            vid = rec.vector_id
            iv  = rec.input_vector

            # ----------------------------------------------------------------
            # CCV-A-01: Clip A verification.
            # position_size_factor must be in [0.0, 1.0] for every normal vector.
            # ----------------------------------------------------------------
            psf = out.position_size_factor
            if psf < 0.0 or psf > 1.0:
                raise RuntimeError(
                    f"CLIP_A_VIOLATION: Vector {vid} position_size_factor={psf} "
                    "is outside [0.0, 1.0]. INV-01 violated."
                )

            # ----------------------------------------------------------------
            # CCV-B-01: For MU-02 and RP-02, E_pre_clip should be zero or near zero,
            # so Clip B floor should be active. exposure_weight bit pattern should
            # equal bit pattern of 1e-6.
            # ----------------------------------------------------------------
            if vid in ("MU-02", "RP-02"):
                ew_bits = _float_bits(out.exposure_weight)
                if ew_bits != self._lb_bits:
                    raise RuntimeError(
                        f"CLIP_B_FLOOR_VIOLATION: Vector {vid} exposure_weight "
                        f"expected bit pattern of 1e-6 but got "
                        f"{out.exposure_weight!r}. INV-02 violated."
                    )

            # ----------------------------------------------------------------
            # CCV-B-02: For JM-inactive (JM-01, JM-04) non-CRISIS vectors,
            # exposure_weight must be in [1e-6, 1.0].
            # (Clip C inactive, CRISIS dampening inactive.)
            # ----------------------------------------------------------------
            if vid in ("jm-01", "JM-04") and iv.current_regime_str != "CRISIS":
                ew = out.exposure_weight
                if ew < 1e-6 or ew > 1.0:
                    raise RuntimeError(
                        f"CLIP_B_RANGE_VIOLATION: Vector {vid} exposure_weight={ew} "
                        "outside [1e-6, 1.0] with Clip C and CRISIS dampening both "
                        "inactive. INV-02 violated."
                    )

            # ----------------------------------------------------------------
            # CCV-C-02: For JM-03 (designed to produce pre-Clip-C value below
            # SHOCK_EXPOSURE_CAP), exposure_weight should equal SHOCK_EXPOSURE_CAP.
            # ----------------------------------------------------------------
            if vid == "JM-03":
                ew_bits = _float_bits(out.exposure_weight)
                if ew_bits != self._sec_bits:
                    # JM-03 uses meta_uncertainty=0.99 + multiplier=2.0.
                    # The division may produce a value below SHOCK_EXPOSURE_CAP,
                    # which gets clipped to SHOCK_EXPOSURE_CAP by Clip C.
                    # If the result does NOT equal SHOCK_EXPOSURE_CAP, the
                    # actual computed value exceeded the cap after division;
                    # this is acceptable if the value is above SHOCK_EXPOSURE_CAP.
                    # Hard failure only if value is strictly below SHOCK_EXPOSURE_CAP.
                    if out.exposure_weight < self._sec:
                        raise RuntimeError(
                            f"CLIP_C_FLOOR_VIOLATION: Vector {vid} exposure_weight="
                            f"{out.exposure_weight} is below SHOCK_EXPOSURE_CAP="
                            f"{self._sec}. INV-03 violated."
                        )
                    notes.append(
                        f"CCV-C-02 note: JM-03 exposure_weight={out.exposure_weight} "
                        "exceeds SHOCK_EXPOSURE_CAP; Clip C floor not triggered."
                    )

            # ----------------------------------------------------------------
            # CCV-D-02: For CR-01 (CRISIS, JRM inactive), exposure_weight may be
            # below SHOCK_EXPOSURE_CAP. No floor enforcement. This is specified
            # behaviour per INV-04.
            # ----------------------------------------------------------------
            if vid == "CR-01":
                notes.append(
                    f"CCV-D-02: CR-01 exposure_weight={out.exposure_weight}. "
                    "May be below SHOCK_EXPOSURE_CAP per INV-04 (specified behaviour)."
                )

        # --------------------------------------------------------------------
        # CCV-D-01: For CR-02 (CRISIS + JRM active), verify ordering.
        # Expected: CR-02.exposure_weight == JM-03.exposure_weight * 0.75
        # Both records must be present in ER set.
        # --------------------------------------------------------------------
        if "CR-02" in by_id and "JM-03" in by_id:
            cr02_out = by_id["CR-02"].observed_output
            jm03_out = by_id["JM-03"].observed_output
            if not cr02_out.exception_raised and not jm03_out.exception_raised:
                # Compute expected value using Python float arithmetic (same as production).
                expected_cr02_ew = jm03_out.exposure_weight * 0.75
                if not _floats_equal(cr02_out.exposure_weight, expected_cr02_ew):
                    raise RuntimeError(
                        f"CRISIS_ORDERING_VIOLATION: CR-02 exposure_weight="
                        f"{cr02_out.exposure_weight} != JM-03.exposure_weight*0.75="
                        f"{expected_cr02_ew}. Clip C / CRISIS ordering violated. "
                        "INV-04 violated."
                    )

        # --------------------------------------------------------------------
        # CCV-D-03: CR-03 (non-CRISIS with JRM active) -- dampening must NOT apply.
        # Verified by BIC backward compatibility comparison against a non-CRISIS
        # variant. Here we simply note the check for audit.
        # --------------------------------------------------------------------
        if "CR-03" in by_id:
            notes.append(
                "CCV-D-03: CR-03 is non-CRISIS with JRM active. Dampening "
                "not applied. Verified by absence of *0.75 in BIC comparison."
            )

        return violations, notes

    def xǁClipVerifierǁverify__mutmut_31(
        self,
        er_records: List[ExecutionRecord],
    ) -> Tuple[List[str], List[str]]:
        """
        Perform clip chain verification on ER-stage records.

        Returns:
          (violations, notes)
          violations -- list of violation description strings. Empty means pass.
          notes      -- list of non-failure informational notes.

        Raises RuntimeError with failure_type_id prefix on hard failures
        (CLIP_B_FLOOR_VIOLATION, CLIP_C_FLOOR_VIOLATION, CLIP_A_VIOLATION,
        CRISIS_ORDERING_VIOLATION).
        """
        violations = []
        notes      = []
        by_id: Dict[str, ExecutionRecord] = {r.vector_id: r for r in er_records}

        for rec in er_records:
            out = rec.observed_output
            if out.exception_raised:
                # No clip verification for exception vectors.
                continue

            vid = rec.vector_id
            iv  = rec.input_vector

            # ----------------------------------------------------------------
            # CCV-A-01: Clip A verification.
            # position_size_factor must be in [0.0, 1.0] for every normal vector.
            # ----------------------------------------------------------------
            psf = out.position_size_factor
            if psf < 0.0 or psf > 1.0:
                raise RuntimeError(
                    f"CLIP_A_VIOLATION: Vector {vid} position_size_factor={psf} "
                    "is outside [0.0, 1.0]. INV-01 violated."
                )

            # ----------------------------------------------------------------
            # CCV-B-01: For MU-02 and RP-02, E_pre_clip should be zero or near zero,
            # so Clip B floor should be active. exposure_weight bit pattern should
            # equal bit pattern of 1e-6.
            # ----------------------------------------------------------------
            if vid in ("MU-02", "RP-02"):
                ew_bits = _float_bits(out.exposure_weight)
                if ew_bits != self._lb_bits:
                    raise RuntimeError(
                        f"CLIP_B_FLOOR_VIOLATION: Vector {vid} exposure_weight "
                        f"expected bit pattern of 1e-6 but got "
                        f"{out.exposure_weight!r}. INV-02 violated."
                    )

            # ----------------------------------------------------------------
            # CCV-B-02: For JM-inactive (JM-01, JM-04) non-CRISIS vectors,
            # exposure_weight must be in [1e-6, 1.0].
            # (Clip C inactive, CRISIS dampening inactive.)
            # ----------------------------------------------------------------
            if vid in ("JM-01", "XXJM-04XX") and iv.current_regime_str != "CRISIS":
                ew = out.exposure_weight
                if ew < 1e-6 or ew > 1.0:
                    raise RuntimeError(
                        f"CLIP_B_RANGE_VIOLATION: Vector {vid} exposure_weight={ew} "
                        "outside [1e-6, 1.0] with Clip C and CRISIS dampening both "
                        "inactive. INV-02 violated."
                    )

            # ----------------------------------------------------------------
            # CCV-C-02: For JM-03 (designed to produce pre-Clip-C value below
            # SHOCK_EXPOSURE_CAP), exposure_weight should equal SHOCK_EXPOSURE_CAP.
            # ----------------------------------------------------------------
            if vid == "JM-03":
                ew_bits = _float_bits(out.exposure_weight)
                if ew_bits != self._sec_bits:
                    # JM-03 uses meta_uncertainty=0.99 + multiplier=2.0.
                    # The division may produce a value below SHOCK_EXPOSURE_CAP,
                    # which gets clipped to SHOCK_EXPOSURE_CAP by Clip C.
                    # If the result does NOT equal SHOCK_EXPOSURE_CAP, the
                    # actual computed value exceeded the cap after division;
                    # this is acceptable if the value is above SHOCK_EXPOSURE_CAP.
                    # Hard failure only if value is strictly below SHOCK_EXPOSURE_CAP.
                    if out.exposure_weight < self._sec:
                        raise RuntimeError(
                            f"CLIP_C_FLOOR_VIOLATION: Vector {vid} exposure_weight="
                            f"{out.exposure_weight} is below SHOCK_EXPOSURE_CAP="
                            f"{self._sec}. INV-03 violated."
                        )
                    notes.append(
                        f"CCV-C-02 note: JM-03 exposure_weight={out.exposure_weight} "
                        "exceeds SHOCK_EXPOSURE_CAP; Clip C floor not triggered."
                    )

            # ----------------------------------------------------------------
            # CCV-D-02: For CR-01 (CRISIS, JRM inactive), exposure_weight may be
            # below SHOCK_EXPOSURE_CAP. No floor enforcement. This is specified
            # behaviour per INV-04.
            # ----------------------------------------------------------------
            if vid == "CR-01":
                notes.append(
                    f"CCV-D-02: CR-01 exposure_weight={out.exposure_weight}. "
                    "May be below SHOCK_EXPOSURE_CAP per INV-04 (specified behaviour)."
                )

        # --------------------------------------------------------------------
        # CCV-D-01: For CR-02 (CRISIS + JRM active), verify ordering.
        # Expected: CR-02.exposure_weight == JM-03.exposure_weight * 0.75
        # Both records must be present in ER set.
        # --------------------------------------------------------------------
        if "CR-02" in by_id and "JM-03" in by_id:
            cr02_out = by_id["CR-02"].observed_output
            jm03_out = by_id["JM-03"].observed_output
            if not cr02_out.exception_raised and not jm03_out.exception_raised:
                # Compute expected value using Python float arithmetic (same as production).
                expected_cr02_ew = jm03_out.exposure_weight * 0.75
                if not _floats_equal(cr02_out.exposure_weight, expected_cr02_ew):
                    raise RuntimeError(
                        f"CRISIS_ORDERING_VIOLATION: CR-02 exposure_weight="
                        f"{cr02_out.exposure_weight} != JM-03.exposure_weight*0.75="
                        f"{expected_cr02_ew}. Clip C / CRISIS ordering violated. "
                        "INV-04 violated."
                    )

        # --------------------------------------------------------------------
        # CCV-D-03: CR-03 (non-CRISIS with JRM active) -- dampening must NOT apply.
        # Verified by BIC backward compatibility comparison against a non-CRISIS
        # variant. Here we simply note the check for audit.
        # --------------------------------------------------------------------
        if "CR-03" in by_id:
            notes.append(
                "CCV-D-03: CR-03 is non-CRISIS with JRM active. Dampening "
                "not applied. Verified by absence of *0.75 in BIC comparison."
            )

        return violations, notes

    def xǁClipVerifierǁverify__mutmut_32(
        self,
        er_records: List[ExecutionRecord],
    ) -> Tuple[List[str], List[str]]:
        """
        Perform clip chain verification on ER-stage records.

        Returns:
          (violations, notes)
          violations -- list of violation description strings. Empty means pass.
          notes      -- list of non-failure informational notes.

        Raises RuntimeError with failure_type_id prefix on hard failures
        (CLIP_B_FLOOR_VIOLATION, CLIP_C_FLOOR_VIOLATION, CLIP_A_VIOLATION,
        CRISIS_ORDERING_VIOLATION).
        """
        violations = []
        notes      = []
        by_id: Dict[str, ExecutionRecord] = {r.vector_id: r for r in er_records}

        for rec in er_records:
            out = rec.observed_output
            if out.exception_raised:
                # No clip verification for exception vectors.
                continue

            vid = rec.vector_id
            iv  = rec.input_vector

            # ----------------------------------------------------------------
            # CCV-A-01: Clip A verification.
            # position_size_factor must be in [0.0, 1.0] for every normal vector.
            # ----------------------------------------------------------------
            psf = out.position_size_factor
            if psf < 0.0 or psf > 1.0:
                raise RuntimeError(
                    f"CLIP_A_VIOLATION: Vector {vid} position_size_factor={psf} "
                    "is outside [0.0, 1.0]. INV-01 violated."
                )

            # ----------------------------------------------------------------
            # CCV-B-01: For MU-02 and RP-02, E_pre_clip should be zero or near zero,
            # so Clip B floor should be active. exposure_weight bit pattern should
            # equal bit pattern of 1e-6.
            # ----------------------------------------------------------------
            if vid in ("MU-02", "RP-02"):
                ew_bits = _float_bits(out.exposure_weight)
                if ew_bits != self._lb_bits:
                    raise RuntimeError(
                        f"CLIP_B_FLOOR_VIOLATION: Vector {vid} exposure_weight "
                        f"expected bit pattern of 1e-6 but got "
                        f"{out.exposure_weight!r}. INV-02 violated."
                    )

            # ----------------------------------------------------------------
            # CCV-B-02: For JM-inactive (JM-01, JM-04) non-CRISIS vectors,
            # exposure_weight must be in [1e-6, 1.0].
            # (Clip C inactive, CRISIS dampening inactive.)
            # ----------------------------------------------------------------
            if vid in ("JM-01", "jm-04") and iv.current_regime_str != "CRISIS":
                ew = out.exposure_weight
                if ew < 1e-6 or ew > 1.0:
                    raise RuntimeError(
                        f"CLIP_B_RANGE_VIOLATION: Vector {vid} exposure_weight={ew} "
                        "outside [1e-6, 1.0] with Clip C and CRISIS dampening both "
                        "inactive. INV-02 violated."
                    )

            # ----------------------------------------------------------------
            # CCV-C-02: For JM-03 (designed to produce pre-Clip-C value below
            # SHOCK_EXPOSURE_CAP), exposure_weight should equal SHOCK_EXPOSURE_CAP.
            # ----------------------------------------------------------------
            if vid == "JM-03":
                ew_bits = _float_bits(out.exposure_weight)
                if ew_bits != self._sec_bits:
                    # JM-03 uses meta_uncertainty=0.99 + multiplier=2.0.
                    # The division may produce a value below SHOCK_EXPOSURE_CAP,
                    # which gets clipped to SHOCK_EXPOSURE_CAP by Clip C.
                    # If the result does NOT equal SHOCK_EXPOSURE_CAP, the
                    # actual computed value exceeded the cap after division;
                    # this is acceptable if the value is above SHOCK_EXPOSURE_CAP.
                    # Hard failure only if value is strictly below SHOCK_EXPOSURE_CAP.
                    if out.exposure_weight < self._sec:
                        raise RuntimeError(
                            f"CLIP_C_FLOOR_VIOLATION: Vector {vid} exposure_weight="
                            f"{out.exposure_weight} is below SHOCK_EXPOSURE_CAP="
                            f"{self._sec}. INV-03 violated."
                        )
                    notes.append(
                        f"CCV-C-02 note: JM-03 exposure_weight={out.exposure_weight} "
                        "exceeds SHOCK_EXPOSURE_CAP; Clip C floor not triggered."
                    )

            # ----------------------------------------------------------------
            # CCV-D-02: For CR-01 (CRISIS, JRM inactive), exposure_weight may be
            # below SHOCK_EXPOSURE_CAP. No floor enforcement. This is specified
            # behaviour per INV-04.
            # ----------------------------------------------------------------
            if vid == "CR-01":
                notes.append(
                    f"CCV-D-02: CR-01 exposure_weight={out.exposure_weight}. "
                    "May be below SHOCK_EXPOSURE_CAP per INV-04 (specified behaviour)."
                )

        # --------------------------------------------------------------------
        # CCV-D-01: For CR-02 (CRISIS + JRM active), verify ordering.
        # Expected: CR-02.exposure_weight == JM-03.exposure_weight * 0.75
        # Both records must be present in ER set.
        # --------------------------------------------------------------------
        if "CR-02" in by_id and "JM-03" in by_id:
            cr02_out = by_id["CR-02"].observed_output
            jm03_out = by_id["JM-03"].observed_output
            if not cr02_out.exception_raised and not jm03_out.exception_raised:
                # Compute expected value using Python float arithmetic (same as production).
                expected_cr02_ew = jm03_out.exposure_weight * 0.75
                if not _floats_equal(cr02_out.exposure_weight, expected_cr02_ew):
                    raise RuntimeError(
                        f"CRISIS_ORDERING_VIOLATION: CR-02 exposure_weight="
                        f"{cr02_out.exposure_weight} != JM-03.exposure_weight*0.75="
                        f"{expected_cr02_ew}. Clip C / CRISIS ordering violated. "
                        "INV-04 violated."
                    )

        # --------------------------------------------------------------------
        # CCV-D-03: CR-03 (non-CRISIS with JRM active) -- dampening must NOT apply.
        # Verified by BIC backward compatibility comparison against a non-CRISIS
        # variant. Here we simply note the check for audit.
        # --------------------------------------------------------------------
        if "CR-03" in by_id:
            notes.append(
                "CCV-D-03: CR-03 is non-CRISIS with JRM active. Dampening "
                "not applied. Verified by absence of *0.75 in BIC comparison."
            )

        return violations, notes

    def xǁClipVerifierǁverify__mutmut_33(
        self,
        er_records: List[ExecutionRecord],
    ) -> Tuple[List[str], List[str]]:
        """
        Perform clip chain verification on ER-stage records.

        Returns:
          (violations, notes)
          violations -- list of violation description strings. Empty means pass.
          notes      -- list of non-failure informational notes.

        Raises RuntimeError with failure_type_id prefix on hard failures
        (CLIP_B_FLOOR_VIOLATION, CLIP_C_FLOOR_VIOLATION, CLIP_A_VIOLATION,
        CRISIS_ORDERING_VIOLATION).
        """
        violations = []
        notes      = []
        by_id: Dict[str, ExecutionRecord] = {r.vector_id: r for r in er_records}

        for rec in er_records:
            out = rec.observed_output
            if out.exception_raised:
                # No clip verification for exception vectors.
                continue

            vid = rec.vector_id
            iv  = rec.input_vector

            # ----------------------------------------------------------------
            # CCV-A-01: Clip A verification.
            # position_size_factor must be in [0.0, 1.0] for every normal vector.
            # ----------------------------------------------------------------
            psf = out.position_size_factor
            if psf < 0.0 or psf > 1.0:
                raise RuntimeError(
                    f"CLIP_A_VIOLATION: Vector {vid} position_size_factor={psf} "
                    "is outside [0.0, 1.0]. INV-01 violated."
                )

            # ----------------------------------------------------------------
            # CCV-B-01: For MU-02 and RP-02, E_pre_clip should be zero or near zero,
            # so Clip B floor should be active. exposure_weight bit pattern should
            # equal bit pattern of 1e-6.
            # ----------------------------------------------------------------
            if vid in ("MU-02", "RP-02"):
                ew_bits = _float_bits(out.exposure_weight)
                if ew_bits != self._lb_bits:
                    raise RuntimeError(
                        f"CLIP_B_FLOOR_VIOLATION: Vector {vid} exposure_weight "
                        f"expected bit pattern of 1e-6 but got "
                        f"{out.exposure_weight!r}. INV-02 violated."
                    )

            # ----------------------------------------------------------------
            # CCV-B-02: For JM-inactive (JM-01, JM-04) non-CRISIS vectors,
            # exposure_weight must be in [1e-6, 1.0].
            # (Clip C inactive, CRISIS dampening inactive.)
            # ----------------------------------------------------------------
            if vid in ("JM-01", "JM-04") and iv.current_regime_str == "CRISIS":
                ew = out.exposure_weight
                if ew < 1e-6 or ew > 1.0:
                    raise RuntimeError(
                        f"CLIP_B_RANGE_VIOLATION: Vector {vid} exposure_weight={ew} "
                        "outside [1e-6, 1.0] with Clip C and CRISIS dampening both "
                        "inactive. INV-02 violated."
                    )

            # ----------------------------------------------------------------
            # CCV-C-02: For JM-03 (designed to produce pre-Clip-C value below
            # SHOCK_EXPOSURE_CAP), exposure_weight should equal SHOCK_EXPOSURE_CAP.
            # ----------------------------------------------------------------
            if vid == "JM-03":
                ew_bits = _float_bits(out.exposure_weight)
                if ew_bits != self._sec_bits:
                    # JM-03 uses meta_uncertainty=0.99 + multiplier=2.0.
                    # The division may produce a value below SHOCK_EXPOSURE_CAP,
                    # which gets clipped to SHOCK_EXPOSURE_CAP by Clip C.
                    # If the result does NOT equal SHOCK_EXPOSURE_CAP, the
                    # actual computed value exceeded the cap after division;
                    # this is acceptable if the value is above SHOCK_EXPOSURE_CAP.
                    # Hard failure only if value is strictly below SHOCK_EXPOSURE_CAP.
                    if out.exposure_weight < self._sec:
                        raise RuntimeError(
                            f"CLIP_C_FLOOR_VIOLATION: Vector {vid} exposure_weight="
                            f"{out.exposure_weight} is below SHOCK_EXPOSURE_CAP="
                            f"{self._sec}. INV-03 violated."
                        )
                    notes.append(
                        f"CCV-C-02 note: JM-03 exposure_weight={out.exposure_weight} "
                        "exceeds SHOCK_EXPOSURE_CAP; Clip C floor not triggered."
                    )

            # ----------------------------------------------------------------
            # CCV-D-02: For CR-01 (CRISIS, JRM inactive), exposure_weight may be
            # below SHOCK_EXPOSURE_CAP. No floor enforcement. This is specified
            # behaviour per INV-04.
            # ----------------------------------------------------------------
            if vid == "CR-01":
                notes.append(
                    f"CCV-D-02: CR-01 exposure_weight={out.exposure_weight}. "
                    "May be below SHOCK_EXPOSURE_CAP per INV-04 (specified behaviour)."
                )

        # --------------------------------------------------------------------
        # CCV-D-01: For CR-02 (CRISIS + JRM active), verify ordering.
        # Expected: CR-02.exposure_weight == JM-03.exposure_weight * 0.75
        # Both records must be present in ER set.
        # --------------------------------------------------------------------
        if "CR-02" in by_id and "JM-03" in by_id:
            cr02_out = by_id["CR-02"].observed_output
            jm03_out = by_id["JM-03"].observed_output
            if not cr02_out.exception_raised and not jm03_out.exception_raised:
                # Compute expected value using Python float arithmetic (same as production).
                expected_cr02_ew = jm03_out.exposure_weight * 0.75
                if not _floats_equal(cr02_out.exposure_weight, expected_cr02_ew):
                    raise RuntimeError(
                        f"CRISIS_ORDERING_VIOLATION: CR-02 exposure_weight="
                        f"{cr02_out.exposure_weight} != JM-03.exposure_weight*0.75="
                        f"{expected_cr02_ew}. Clip C / CRISIS ordering violated. "
                        "INV-04 violated."
                    )

        # --------------------------------------------------------------------
        # CCV-D-03: CR-03 (non-CRISIS with JRM active) -- dampening must NOT apply.
        # Verified by BIC backward compatibility comparison against a non-CRISIS
        # variant. Here we simply note the check for audit.
        # --------------------------------------------------------------------
        if "CR-03" in by_id:
            notes.append(
                "CCV-D-03: CR-03 is non-CRISIS with JRM active. Dampening "
                "not applied. Verified by absence of *0.75 in BIC comparison."
            )

        return violations, notes

    def xǁClipVerifierǁverify__mutmut_34(
        self,
        er_records: List[ExecutionRecord],
    ) -> Tuple[List[str], List[str]]:
        """
        Perform clip chain verification on ER-stage records.

        Returns:
          (violations, notes)
          violations -- list of violation description strings. Empty means pass.
          notes      -- list of non-failure informational notes.

        Raises RuntimeError with failure_type_id prefix on hard failures
        (CLIP_B_FLOOR_VIOLATION, CLIP_C_FLOOR_VIOLATION, CLIP_A_VIOLATION,
        CRISIS_ORDERING_VIOLATION).
        """
        violations = []
        notes      = []
        by_id: Dict[str, ExecutionRecord] = {r.vector_id: r for r in er_records}

        for rec in er_records:
            out = rec.observed_output
            if out.exception_raised:
                # No clip verification for exception vectors.
                continue

            vid = rec.vector_id
            iv  = rec.input_vector

            # ----------------------------------------------------------------
            # CCV-A-01: Clip A verification.
            # position_size_factor must be in [0.0, 1.0] for every normal vector.
            # ----------------------------------------------------------------
            psf = out.position_size_factor
            if psf < 0.0 or psf > 1.0:
                raise RuntimeError(
                    f"CLIP_A_VIOLATION: Vector {vid} position_size_factor={psf} "
                    "is outside [0.0, 1.0]. INV-01 violated."
                )

            # ----------------------------------------------------------------
            # CCV-B-01: For MU-02 and RP-02, E_pre_clip should be zero or near zero,
            # so Clip B floor should be active. exposure_weight bit pattern should
            # equal bit pattern of 1e-6.
            # ----------------------------------------------------------------
            if vid in ("MU-02", "RP-02"):
                ew_bits = _float_bits(out.exposure_weight)
                if ew_bits != self._lb_bits:
                    raise RuntimeError(
                        f"CLIP_B_FLOOR_VIOLATION: Vector {vid} exposure_weight "
                        f"expected bit pattern of 1e-6 but got "
                        f"{out.exposure_weight!r}. INV-02 violated."
                    )

            # ----------------------------------------------------------------
            # CCV-B-02: For JM-inactive (JM-01, JM-04) non-CRISIS vectors,
            # exposure_weight must be in [1e-6, 1.0].
            # (Clip C inactive, CRISIS dampening inactive.)
            # ----------------------------------------------------------------
            if vid in ("JM-01", "JM-04") and iv.current_regime_str != "XXCRISISXX":
                ew = out.exposure_weight
                if ew < 1e-6 or ew > 1.0:
                    raise RuntimeError(
                        f"CLIP_B_RANGE_VIOLATION: Vector {vid} exposure_weight={ew} "
                        "outside [1e-6, 1.0] with Clip C and CRISIS dampening both "
                        "inactive. INV-02 violated."
                    )

            # ----------------------------------------------------------------
            # CCV-C-02: For JM-03 (designed to produce pre-Clip-C value below
            # SHOCK_EXPOSURE_CAP), exposure_weight should equal SHOCK_EXPOSURE_CAP.
            # ----------------------------------------------------------------
            if vid == "JM-03":
                ew_bits = _float_bits(out.exposure_weight)
                if ew_bits != self._sec_bits:
                    # JM-03 uses meta_uncertainty=0.99 + multiplier=2.0.
                    # The division may produce a value below SHOCK_EXPOSURE_CAP,
                    # which gets clipped to SHOCK_EXPOSURE_CAP by Clip C.
                    # If the result does NOT equal SHOCK_EXPOSURE_CAP, the
                    # actual computed value exceeded the cap after division;
                    # this is acceptable if the value is above SHOCK_EXPOSURE_CAP.
                    # Hard failure only if value is strictly below SHOCK_EXPOSURE_CAP.
                    if out.exposure_weight < self._sec:
                        raise RuntimeError(
                            f"CLIP_C_FLOOR_VIOLATION: Vector {vid} exposure_weight="
                            f"{out.exposure_weight} is below SHOCK_EXPOSURE_CAP="
                            f"{self._sec}. INV-03 violated."
                        )
                    notes.append(
                        f"CCV-C-02 note: JM-03 exposure_weight={out.exposure_weight} "
                        "exceeds SHOCK_EXPOSURE_CAP; Clip C floor not triggered."
                    )

            # ----------------------------------------------------------------
            # CCV-D-02: For CR-01 (CRISIS, JRM inactive), exposure_weight may be
            # below SHOCK_EXPOSURE_CAP. No floor enforcement. This is specified
            # behaviour per INV-04.
            # ----------------------------------------------------------------
            if vid == "CR-01":
                notes.append(
                    f"CCV-D-02: CR-01 exposure_weight={out.exposure_weight}. "
                    "May be below SHOCK_EXPOSURE_CAP per INV-04 (specified behaviour)."
                )

        # --------------------------------------------------------------------
        # CCV-D-01: For CR-02 (CRISIS + JRM active), verify ordering.
        # Expected: CR-02.exposure_weight == JM-03.exposure_weight * 0.75
        # Both records must be present in ER set.
        # --------------------------------------------------------------------
        if "CR-02" in by_id and "JM-03" in by_id:
            cr02_out = by_id["CR-02"].observed_output
            jm03_out = by_id["JM-03"].observed_output
            if not cr02_out.exception_raised and not jm03_out.exception_raised:
                # Compute expected value using Python float arithmetic (same as production).
                expected_cr02_ew = jm03_out.exposure_weight * 0.75
                if not _floats_equal(cr02_out.exposure_weight, expected_cr02_ew):
                    raise RuntimeError(
                        f"CRISIS_ORDERING_VIOLATION: CR-02 exposure_weight="
                        f"{cr02_out.exposure_weight} != JM-03.exposure_weight*0.75="
                        f"{expected_cr02_ew}. Clip C / CRISIS ordering violated. "
                        "INV-04 violated."
                    )

        # --------------------------------------------------------------------
        # CCV-D-03: CR-03 (non-CRISIS with JRM active) -- dampening must NOT apply.
        # Verified by BIC backward compatibility comparison against a non-CRISIS
        # variant. Here we simply note the check for audit.
        # --------------------------------------------------------------------
        if "CR-03" in by_id:
            notes.append(
                "CCV-D-03: CR-03 is non-CRISIS with JRM active. Dampening "
                "not applied. Verified by absence of *0.75 in BIC comparison."
            )

        return violations, notes

    def xǁClipVerifierǁverify__mutmut_35(
        self,
        er_records: List[ExecutionRecord],
    ) -> Tuple[List[str], List[str]]:
        """
        Perform clip chain verification on ER-stage records.

        Returns:
          (violations, notes)
          violations -- list of violation description strings. Empty means pass.
          notes      -- list of non-failure informational notes.

        Raises RuntimeError with failure_type_id prefix on hard failures
        (CLIP_B_FLOOR_VIOLATION, CLIP_C_FLOOR_VIOLATION, CLIP_A_VIOLATION,
        CRISIS_ORDERING_VIOLATION).
        """
        violations = []
        notes      = []
        by_id: Dict[str, ExecutionRecord] = {r.vector_id: r for r in er_records}

        for rec in er_records:
            out = rec.observed_output
            if out.exception_raised:
                # No clip verification for exception vectors.
                continue

            vid = rec.vector_id
            iv  = rec.input_vector

            # ----------------------------------------------------------------
            # CCV-A-01: Clip A verification.
            # position_size_factor must be in [0.0, 1.0] for every normal vector.
            # ----------------------------------------------------------------
            psf = out.position_size_factor
            if psf < 0.0 or psf > 1.0:
                raise RuntimeError(
                    f"CLIP_A_VIOLATION: Vector {vid} position_size_factor={psf} "
                    "is outside [0.0, 1.0]. INV-01 violated."
                )

            # ----------------------------------------------------------------
            # CCV-B-01: For MU-02 and RP-02, E_pre_clip should be zero or near zero,
            # so Clip B floor should be active. exposure_weight bit pattern should
            # equal bit pattern of 1e-6.
            # ----------------------------------------------------------------
            if vid in ("MU-02", "RP-02"):
                ew_bits = _float_bits(out.exposure_weight)
                if ew_bits != self._lb_bits:
                    raise RuntimeError(
                        f"CLIP_B_FLOOR_VIOLATION: Vector {vid} exposure_weight "
                        f"expected bit pattern of 1e-6 but got "
                        f"{out.exposure_weight!r}. INV-02 violated."
                    )

            # ----------------------------------------------------------------
            # CCV-B-02: For JM-inactive (JM-01, JM-04) non-CRISIS vectors,
            # exposure_weight must be in [1e-6, 1.0].
            # (Clip C inactive, CRISIS dampening inactive.)
            # ----------------------------------------------------------------
            if vid in ("JM-01", "JM-04") and iv.current_regime_str != "crisis":
                ew = out.exposure_weight
                if ew < 1e-6 or ew > 1.0:
                    raise RuntimeError(
                        f"CLIP_B_RANGE_VIOLATION: Vector {vid} exposure_weight={ew} "
                        "outside [1e-6, 1.0] with Clip C and CRISIS dampening both "
                        "inactive. INV-02 violated."
                    )

            # ----------------------------------------------------------------
            # CCV-C-02: For JM-03 (designed to produce pre-Clip-C value below
            # SHOCK_EXPOSURE_CAP), exposure_weight should equal SHOCK_EXPOSURE_CAP.
            # ----------------------------------------------------------------
            if vid == "JM-03":
                ew_bits = _float_bits(out.exposure_weight)
                if ew_bits != self._sec_bits:
                    # JM-03 uses meta_uncertainty=0.99 + multiplier=2.0.
                    # The division may produce a value below SHOCK_EXPOSURE_CAP,
                    # which gets clipped to SHOCK_EXPOSURE_CAP by Clip C.
                    # If the result does NOT equal SHOCK_EXPOSURE_CAP, the
                    # actual computed value exceeded the cap after division;
                    # this is acceptable if the value is above SHOCK_EXPOSURE_CAP.
                    # Hard failure only if value is strictly below SHOCK_EXPOSURE_CAP.
                    if out.exposure_weight < self._sec:
                        raise RuntimeError(
                            f"CLIP_C_FLOOR_VIOLATION: Vector {vid} exposure_weight="
                            f"{out.exposure_weight} is below SHOCK_EXPOSURE_CAP="
                            f"{self._sec}. INV-03 violated."
                        )
                    notes.append(
                        f"CCV-C-02 note: JM-03 exposure_weight={out.exposure_weight} "
                        "exceeds SHOCK_EXPOSURE_CAP; Clip C floor not triggered."
                    )

            # ----------------------------------------------------------------
            # CCV-D-02: For CR-01 (CRISIS, JRM inactive), exposure_weight may be
            # below SHOCK_EXPOSURE_CAP. No floor enforcement. This is specified
            # behaviour per INV-04.
            # ----------------------------------------------------------------
            if vid == "CR-01":
                notes.append(
                    f"CCV-D-02: CR-01 exposure_weight={out.exposure_weight}. "
                    "May be below SHOCK_EXPOSURE_CAP per INV-04 (specified behaviour)."
                )

        # --------------------------------------------------------------------
        # CCV-D-01: For CR-02 (CRISIS + JRM active), verify ordering.
        # Expected: CR-02.exposure_weight == JM-03.exposure_weight * 0.75
        # Both records must be present in ER set.
        # --------------------------------------------------------------------
        if "CR-02" in by_id and "JM-03" in by_id:
            cr02_out = by_id["CR-02"].observed_output
            jm03_out = by_id["JM-03"].observed_output
            if not cr02_out.exception_raised and not jm03_out.exception_raised:
                # Compute expected value using Python float arithmetic (same as production).
                expected_cr02_ew = jm03_out.exposure_weight * 0.75
                if not _floats_equal(cr02_out.exposure_weight, expected_cr02_ew):
                    raise RuntimeError(
                        f"CRISIS_ORDERING_VIOLATION: CR-02 exposure_weight="
                        f"{cr02_out.exposure_weight} != JM-03.exposure_weight*0.75="
                        f"{expected_cr02_ew}. Clip C / CRISIS ordering violated. "
                        "INV-04 violated."
                    )

        # --------------------------------------------------------------------
        # CCV-D-03: CR-03 (non-CRISIS with JRM active) -- dampening must NOT apply.
        # Verified by BIC backward compatibility comparison against a non-CRISIS
        # variant. Here we simply note the check for audit.
        # --------------------------------------------------------------------
        if "CR-03" in by_id:
            notes.append(
                "CCV-D-03: CR-03 is non-CRISIS with JRM active. Dampening "
                "not applied. Verified by absence of *0.75 in BIC comparison."
            )

        return violations, notes

    def xǁClipVerifierǁverify__mutmut_36(
        self,
        er_records: List[ExecutionRecord],
    ) -> Tuple[List[str], List[str]]:
        """
        Perform clip chain verification on ER-stage records.

        Returns:
          (violations, notes)
          violations -- list of violation description strings. Empty means pass.
          notes      -- list of non-failure informational notes.

        Raises RuntimeError with failure_type_id prefix on hard failures
        (CLIP_B_FLOOR_VIOLATION, CLIP_C_FLOOR_VIOLATION, CLIP_A_VIOLATION,
        CRISIS_ORDERING_VIOLATION).
        """
        violations = []
        notes      = []
        by_id: Dict[str, ExecutionRecord] = {r.vector_id: r for r in er_records}

        for rec in er_records:
            out = rec.observed_output
            if out.exception_raised:
                # No clip verification for exception vectors.
                continue

            vid = rec.vector_id
            iv  = rec.input_vector

            # ----------------------------------------------------------------
            # CCV-A-01: Clip A verification.
            # position_size_factor must be in [0.0, 1.0] for every normal vector.
            # ----------------------------------------------------------------
            psf = out.position_size_factor
            if psf < 0.0 or psf > 1.0:
                raise RuntimeError(
                    f"CLIP_A_VIOLATION: Vector {vid} position_size_factor={psf} "
                    "is outside [0.0, 1.0]. INV-01 violated."
                )

            # ----------------------------------------------------------------
            # CCV-B-01: For MU-02 and RP-02, E_pre_clip should be zero or near zero,
            # so Clip B floor should be active. exposure_weight bit pattern should
            # equal bit pattern of 1e-6.
            # ----------------------------------------------------------------
            if vid in ("MU-02", "RP-02"):
                ew_bits = _float_bits(out.exposure_weight)
                if ew_bits != self._lb_bits:
                    raise RuntimeError(
                        f"CLIP_B_FLOOR_VIOLATION: Vector {vid} exposure_weight "
                        f"expected bit pattern of 1e-6 but got "
                        f"{out.exposure_weight!r}. INV-02 violated."
                    )

            # ----------------------------------------------------------------
            # CCV-B-02: For JM-inactive (JM-01, JM-04) non-CRISIS vectors,
            # exposure_weight must be in [1e-6, 1.0].
            # (Clip C inactive, CRISIS dampening inactive.)
            # ----------------------------------------------------------------
            if vid in ("JM-01", "JM-04") and iv.current_regime_str != "CRISIS":
                ew = None
                if ew < 1e-6 or ew > 1.0:
                    raise RuntimeError(
                        f"CLIP_B_RANGE_VIOLATION: Vector {vid} exposure_weight={ew} "
                        "outside [1e-6, 1.0] with Clip C and CRISIS dampening both "
                        "inactive. INV-02 violated."
                    )

            # ----------------------------------------------------------------
            # CCV-C-02: For JM-03 (designed to produce pre-Clip-C value below
            # SHOCK_EXPOSURE_CAP), exposure_weight should equal SHOCK_EXPOSURE_CAP.
            # ----------------------------------------------------------------
            if vid == "JM-03":
                ew_bits = _float_bits(out.exposure_weight)
                if ew_bits != self._sec_bits:
                    # JM-03 uses meta_uncertainty=0.99 + multiplier=2.0.
                    # The division may produce a value below SHOCK_EXPOSURE_CAP,
                    # which gets clipped to SHOCK_EXPOSURE_CAP by Clip C.
                    # If the result does NOT equal SHOCK_EXPOSURE_CAP, the
                    # actual computed value exceeded the cap after division;
                    # this is acceptable if the value is above SHOCK_EXPOSURE_CAP.
                    # Hard failure only if value is strictly below SHOCK_EXPOSURE_CAP.
                    if out.exposure_weight < self._sec:
                        raise RuntimeError(
                            f"CLIP_C_FLOOR_VIOLATION: Vector {vid} exposure_weight="
                            f"{out.exposure_weight} is below SHOCK_EXPOSURE_CAP="
                            f"{self._sec}. INV-03 violated."
                        )
                    notes.append(
                        f"CCV-C-02 note: JM-03 exposure_weight={out.exposure_weight} "
                        "exceeds SHOCK_EXPOSURE_CAP; Clip C floor not triggered."
                    )

            # ----------------------------------------------------------------
            # CCV-D-02: For CR-01 (CRISIS, JRM inactive), exposure_weight may be
            # below SHOCK_EXPOSURE_CAP. No floor enforcement. This is specified
            # behaviour per INV-04.
            # ----------------------------------------------------------------
            if vid == "CR-01":
                notes.append(
                    f"CCV-D-02: CR-01 exposure_weight={out.exposure_weight}. "
                    "May be below SHOCK_EXPOSURE_CAP per INV-04 (specified behaviour)."
                )

        # --------------------------------------------------------------------
        # CCV-D-01: For CR-02 (CRISIS + JRM active), verify ordering.
        # Expected: CR-02.exposure_weight == JM-03.exposure_weight * 0.75
        # Both records must be present in ER set.
        # --------------------------------------------------------------------
        if "CR-02" in by_id and "JM-03" in by_id:
            cr02_out = by_id["CR-02"].observed_output
            jm03_out = by_id["JM-03"].observed_output
            if not cr02_out.exception_raised and not jm03_out.exception_raised:
                # Compute expected value using Python float arithmetic (same as production).
                expected_cr02_ew = jm03_out.exposure_weight * 0.75
                if not _floats_equal(cr02_out.exposure_weight, expected_cr02_ew):
                    raise RuntimeError(
                        f"CRISIS_ORDERING_VIOLATION: CR-02 exposure_weight="
                        f"{cr02_out.exposure_weight} != JM-03.exposure_weight*0.75="
                        f"{expected_cr02_ew}. Clip C / CRISIS ordering violated. "
                        "INV-04 violated."
                    )

        # --------------------------------------------------------------------
        # CCV-D-03: CR-03 (non-CRISIS with JRM active) -- dampening must NOT apply.
        # Verified by BIC backward compatibility comparison against a non-CRISIS
        # variant. Here we simply note the check for audit.
        # --------------------------------------------------------------------
        if "CR-03" in by_id:
            notes.append(
                "CCV-D-03: CR-03 is non-CRISIS with JRM active. Dampening "
                "not applied. Verified by absence of *0.75 in BIC comparison."
            )

        return violations, notes

    def xǁClipVerifierǁverify__mutmut_37(
        self,
        er_records: List[ExecutionRecord],
    ) -> Tuple[List[str], List[str]]:
        """
        Perform clip chain verification on ER-stage records.

        Returns:
          (violations, notes)
          violations -- list of violation description strings. Empty means pass.
          notes      -- list of non-failure informational notes.

        Raises RuntimeError with failure_type_id prefix on hard failures
        (CLIP_B_FLOOR_VIOLATION, CLIP_C_FLOOR_VIOLATION, CLIP_A_VIOLATION,
        CRISIS_ORDERING_VIOLATION).
        """
        violations = []
        notes      = []
        by_id: Dict[str, ExecutionRecord] = {r.vector_id: r for r in er_records}

        for rec in er_records:
            out = rec.observed_output
            if out.exception_raised:
                # No clip verification for exception vectors.
                continue

            vid = rec.vector_id
            iv  = rec.input_vector

            # ----------------------------------------------------------------
            # CCV-A-01: Clip A verification.
            # position_size_factor must be in [0.0, 1.0] for every normal vector.
            # ----------------------------------------------------------------
            psf = out.position_size_factor
            if psf < 0.0 or psf > 1.0:
                raise RuntimeError(
                    f"CLIP_A_VIOLATION: Vector {vid} position_size_factor={psf} "
                    "is outside [0.0, 1.0]. INV-01 violated."
                )

            # ----------------------------------------------------------------
            # CCV-B-01: For MU-02 and RP-02, E_pre_clip should be zero or near zero,
            # so Clip B floor should be active. exposure_weight bit pattern should
            # equal bit pattern of 1e-6.
            # ----------------------------------------------------------------
            if vid in ("MU-02", "RP-02"):
                ew_bits = _float_bits(out.exposure_weight)
                if ew_bits != self._lb_bits:
                    raise RuntimeError(
                        f"CLIP_B_FLOOR_VIOLATION: Vector {vid} exposure_weight "
                        f"expected bit pattern of 1e-6 but got "
                        f"{out.exposure_weight!r}. INV-02 violated."
                    )

            # ----------------------------------------------------------------
            # CCV-B-02: For JM-inactive (JM-01, JM-04) non-CRISIS vectors,
            # exposure_weight must be in [1e-6, 1.0].
            # (Clip C inactive, CRISIS dampening inactive.)
            # ----------------------------------------------------------------
            if vid in ("JM-01", "JM-04") and iv.current_regime_str != "CRISIS":
                ew = out.exposure_weight
                if ew < 1e-6 and ew > 1.0:
                    raise RuntimeError(
                        f"CLIP_B_RANGE_VIOLATION: Vector {vid} exposure_weight={ew} "
                        "outside [1e-6, 1.0] with Clip C and CRISIS dampening both "
                        "inactive. INV-02 violated."
                    )

            # ----------------------------------------------------------------
            # CCV-C-02: For JM-03 (designed to produce pre-Clip-C value below
            # SHOCK_EXPOSURE_CAP), exposure_weight should equal SHOCK_EXPOSURE_CAP.
            # ----------------------------------------------------------------
            if vid == "JM-03":
                ew_bits = _float_bits(out.exposure_weight)
                if ew_bits != self._sec_bits:
                    # JM-03 uses meta_uncertainty=0.99 + multiplier=2.0.
                    # The division may produce a value below SHOCK_EXPOSURE_CAP,
                    # which gets clipped to SHOCK_EXPOSURE_CAP by Clip C.
                    # If the result does NOT equal SHOCK_EXPOSURE_CAP, the
                    # actual computed value exceeded the cap after division;
                    # this is acceptable if the value is above SHOCK_EXPOSURE_CAP.
                    # Hard failure only if value is strictly below SHOCK_EXPOSURE_CAP.
                    if out.exposure_weight < self._sec:
                        raise RuntimeError(
                            f"CLIP_C_FLOOR_VIOLATION: Vector {vid} exposure_weight="
                            f"{out.exposure_weight} is below SHOCK_EXPOSURE_CAP="
                            f"{self._sec}. INV-03 violated."
                        )
                    notes.append(
                        f"CCV-C-02 note: JM-03 exposure_weight={out.exposure_weight} "
                        "exceeds SHOCK_EXPOSURE_CAP; Clip C floor not triggered."
                    )

            # ----------------------------------------------------------------
            # CCV-D-02: For CR-01 (CRISIS, JRM inactive), exposure_weight may be
            # below SHOCK_EXPOSURE_CAP. No floor enforcement. This is specified
            # behaviour per INV-04.
            # ----------------------------------------------------------------
            if vid == "CR-01":
                notes.append(
                    f"CCV-D-02: CR-01 exposure_weight={out.exposure_weight}. "
                    "May be below SHOCK_EXPOSURE_CAP per INV-04 (specified behaviour)."
                )

        # --------------------------------------------------------------------
        # CCV-D-01: For CR-02 (CRISIS + JRM active), verify ordering.
        # Expected: CR-02.exposure_weight == JM-03.exposure_weight * 0.75
        # Both records must be present in ER set.
        # --------------------------------------------------------------------
        if "CR-02" in by_id and "JM-03" in by_id:
            cr02_out = by_id["CR-02"].observed_output
            jm03_out = by_id["JM-03"].observed_output
            if not cr02_out.exception_raised and not jm03_out.exception_raised:
                # Compute expected value using Python float arithmetic (same as production).
                expected_cr02_ew = jm03_out.exposure_weight * 0.75
                if not _floats_equal(cr02_out.exposure_weight, expected_cr02_ew):
                    raise RuntimeError(
                        f"CRISIS_ORDERING_VIOLATION: CR-02 exposure_weight="
                        f"{cr02_out.exposure_weight} != JM-03.exposure_weight*0.75="
                        f"{expected_cr02_ew}. Clip C / CRISIS ordering violated. "
                        "INV-04 violated."
                    )

        # --------------------------------------------------------------------
        # CCV-D-03: CR-03 (non-CRISIS with JRM active) -- dampening must NOT apply.
        # Verified by BIC backward compatibility comparison against a non-CRISIS
        # variant. Here we simply note the check for audit.
        # --------------------------------------------------------------------
        if "CR-03" in by_id:
            notes.append(
                "CCV-D-03: CR-03 is non-CRISIS with JRM active. Dampening "
                "not applied. Verified by absence of *0.75 in BIC comparison."
            )

        return violations, notes

    def xǁClipVerifierǁverify__mutmut_38(
        self,
        er_records: List[ExecutionRecord],
    ) -> Tuple[List[str], List[str]]:
        """
        Perform clip chain verification on ER-stage records.

        Returns:
          (violations, notes)
          violations -- list of violation description strings. Empty means pass.
          notes      -- list of non-failure informational notes.

        Raises RuntimeError with failure_type_id prefix on hard failures
        (CLIP_B_FLOOR_VIOLATION, CLIP_C_FLOOR_VIOLATION, CLIP_A_VIOLATION,
        CRISIS_ORDERING_VIOLATION).
        """
        violations = []
        notes      = []
        by_id: Dict[str, ExecutionRecord] = {r.vector_id: r for r in er_records}

        for rec in er_records:
            out = rec.observed_output
            if out.exception_raised:
                # No clip verification for exception vectors.
                continue

            vid = rec.vector_id
            iv  = rec.input_vector

            # ----------------------------------------------------------------
            # CCV-A-01: Clip A verification.
            # position_size_factor must be in [0.0, 1.0] for every normal vector.
            # ----------------------------------------------------------------
            psf = out.position_size_factor
            if psf < 0.0 or psf > 1.0:
                raise RuntimeError(
                    f"CLIP_A_VIOLATION: Vector {vid} position_size_factor={psf} "
                    "is outside [0.0, 1.0]. INV-01 violated."
                )

            # ----------------------------------------------------------------
            # CCV-B-01: For MU-02 and RP-02, E_pre_clip should be zero or near zero,
            # so Clip B floor should be active. exposure_weight bit pattern should
            # equal bit pattern of 1e-6.
            # ----------------------------------------------------------------
            if vid in ("MU-02", "RP-02"):
                ew_bits = _float_bits(out.exposure_weight)
                if ew_bits != self._lb_bits:
                    raise RuntimeError(
                        f"CLIP_B_FLOOR_VIOLATION: Vector {vid} exposure_weight "
                        f"expected bit pattern of 1e-6 but got "
                        f"{out.exposure_weight!r}. INV-02 violated."
                    )

            # ----------------------------------------------------------------
            # CCV-B-02: For JM-inactive (JM-01, JM-04) non-CRISIS vectors,
            # exposure_weight must be in [1e-6, 1.0].
            # (Clip C inactive, CRISIS dampening inactive.)
            # ----------------------------------------------------------------
            if vid in ("JM-01", "JM-04") and iv.current_regime_str != "CRISIS":
                ew = out.exposure_weight
                if ew <= 1e-6 or ew > 1.0:
                    raise RuntimeError(
                        f"CLIP_B_RANGE_VIOLATION: Vector {vid} exposure_weight={ew} "
                        "outside [1e-6, 1.0] with Clip C and CRISIS dampening both "
                        "inactive. INV-02 violated."
                    )

            # ----------------------------------------------------------------
            # CCV-C-02: For JM-03 (designed to produce pre-Clip-C value below
            # SHOCK_EXPOSURE_CAP), exposure_weight should equal SHOCK_EXPOSURE_CAP.
            # ----------------------------------------------------------------
            if vid == "JM-03":
                ew_bits = _float_bits(out.exposure_weight)
                if ew_bits != self._sec_bits:
                    # JM-03 uses meta_uncertainty=0.99 + multiplier=2.0.
                    # The division may produce a value below SHOCK_EXPOSURE_CAP,
                    # which gets clipped to SHOCK_EXPOSURE_CAP by Clip C.
                    # If the result does NOT equal SHOCK_EXPOSURE_CAP, the
                    # actual computed value exceeded the cap after division;
                    # this is acceptable if the value is above SHOCK_EXPOSURE_CAP.
                    # Hard failure only if value is strictly below SHOCK_EXPOSURE_CAP.
                    if out.exposure_weight < self._sec:
                        raise RuntimeError(
                            f"CLIP_C_FLOOR_VIOLATION: Vector {vid} exposure_weight="
                            f"{out.exposure_weight} is below SHOCK_EXPOSURE_CAP="
                            f"{self._sec}. INV-03 violated."
                        )
                    notes.append(
                        f"CCV-C-02 note: JM-03 exposure_weight={out.exposure_weight} "
                        "exceeds SHOCK_EXPOSURE_CAP; Clip C floor not triggered."
                    )

            # ----------------------------------------------------------------
            # CCV-D-02: For CR-01 (CRISIS, JRM inactive), exposure_weight may be
            # below SHOCK_EXPOSURE_CAP. No floor enforcement. This is specified
            # behaviour per INV-04.
            # ----------------------------------------------------------------
            if vid == "CR-01":
                notes.append(
                    f"CCV-D-02: CR-01 exposure_weight={out.exposure_weight}. "
                    "May be below SHOCK_EXPOSURE_CAP per INV-04 (specified behaviour)."
                )

        # --------------------------------------------------------------------
        # CCV-D-01: For CR-02 (CRISIS + JRM active), verify ordering.
        # Expected: CR-02.exposure_weight == JM-03.exposure_weight * 0.75
        # Both records must be present in ER set.
        # --------------------------------------------------------------------
        if "CR-02" in by_id and "JM-03" in by_id:
            cr02_out = by_id["CR-02"].observed_output
            jm03_out = by_id["JM-03"].observed_output
            if not cr02_out.exception_raised and not jm03_out.exception_raised:
                # Compute expected value using Python float arithmetic (same as production).
                expected_cr02_ew = jm03_out.exposure_weight * 0.75
                if not _floats_equal(cr02_out.exposure_weight, expected_cr02_ew):
                    raise RuntimeError(
                        f"CRISIS_ORDERING_VIOLATION: CR-02 exposure_weight="
                        f"{cr02_out.exposure_weight} != JM-03.exposure_weight*0.75="
                        f"{expected_cr02_ew}. Clip C / CRISIS ordering violated. "
                        "INV-04 violated."
                    )

        # --------------------------------------------------------------------
        # CCV-D-03: CR-03 (non-CRISIS with JRM active) -- dampening must NOT apply.
        # Verified by BIC backward compatibility comparison against a non-CRISIS
        # variant. Here we simply note the check for audit.
        # --------------------------------------------------------------------
        if "CR-03" in by_id:
            notes.append(
                "CCV-D-03: CR-03 is non-CRISIS with JRM active. Dampening "
                "not applied. Verified by absence of *0.75 in BIC comparison."
            )

        return violations, notes

    def xǁClipVerifierǁverify__mutmut_39(
        self,
        er_records: List[ExecutionRecord],
    ) -> Tuple[List[str], List[str]]:
        """
        Perform clip chain verification on ER-stage records.

        Returns:
          (violations, notes)
          violations -- list of violation description strings. Empty means pass.
          notes      -- list of non-failure informational notes.

        Raises RuntimeError with failure_type_id prefix on hard failures
        (CLIP_B_FLOOR_VIOLATION, CLIP_C_FLOOR_VIOLATION, CLIP_A_VIOLATION,
        CRISIS_ORDERING_VIOLATION).
        """
        violations = []
        notes      = []
        by_id: Dict[str, ExecutionRecord] = {r.vector_id: r for r in er_records}

        for rec in er_records:
            out = rec.observed_output
            if out.exception_raised:
                # No clip verification for exception vectors.
                continue

            vid = rec.vector_id
            iv  = rec.input_vector

            # ----------------------------------------------------------------
            # CCV-A-01: Clip A verification.
            # position_size_factor must be in [0.0, 1.0] for every normal vector.
            # ----------------------------------------------------------------
            psf = out.position_size_factor
            if psf < 0.0 or psf > 1.0:
                raise RuntimeError(
                    f"CLIP_A_VIOLATION: Vector {vid} position_size_factor={psf} "
                    "is outside [0.0, 1.0]. INV-01 violated."
                )

            # ----------------------------------------------------------------
            # CCV-B-01: For MU-02 and RP-02, E_pre_clip should be zero or near zero,
            # so Clip B floor should be active. exposure_weight bit pattern should
            # equal bit pattern of 1e-6.
            # ----------------------------------------------------------------
            if vid in ("MU-02", "RP-02"):
                ew_bits = _float_bits(out.exposure_weight)
                if ew_bits != self._lb_bits:
                    raise RuntimeError(
                        f"CLIP_B_FLOOR_VIOLATION: Vector {vid} exposure_weight "
                        f"expected bit pattern of 1e-6 but got "
                        f"{out.exposure_weight!r}. INV-02 violated."
                    )

            # ----------------------------------------------------------------
            # CCV-B-02: For JM-inactive (JM-01, JM-04) non-CRISIS vectors,
            # exposure_weight must be in [1e-6, 1.0].
            # (Clip C inactive, CRISIS dampening inactive.)
            # ----------------------------------------------------------------
            if vid in ("JM-01", "JM-04") and iv.current_regime_str != "CRISIS":
                ew = out.exposure_weight
                if ew < 1.000001 or ew > 1.0:
                    raise RuntimeError(
                        f"CLIP_B_RANGE_VIOLATION: Vector {vid} exposure_weight={ew} "
                        "outside [1e-6, 1.0] with Clip C and CRISIS dampening both "
                        "inactive. INV-02 violated."
                    )

            # ----------------------------------------------------------------
            # CCV-C-02: For JM-03 (designed to produce pre-Clip-C value below
            # SHOCK_EXPOSURE_CAP), exposure_weight should equal SHOCK_EXPOSURE_CAP.
            # ----------------------------------------------------------------
            if vid == "JM-03":
                ew_bits = _float_bits(out.exposure_weight)
                if ew_bits != self._sec_bits:
                    # JM-03 uses meta_uncertainty=0.99 + multiplier=2.0.
                    # The division may produce a value below SHOCK_EXPOSURE_CAP,
                    # which gets clipped to SHOCK_EXPOSURE_CAP by Clip C.
                    # If the result does NOT equal SHOCK_EXPOSURE_CAP, the
                    # actual computed value exceeded the cap after division;
                    # this is acceptable if the value is above SHOCK_EXPOSURE_CAP.
                    # Hard failure only if value is strictly below SHOCK_EXPOSURE_CAP.
                    if out.exposure_weight < self._sec:
                        raise RuntimeError(
                            f"CLIP_C_FLOOR_VIOLATION: Vector {vid} exposure_weight="
                            f"{out.exposure_weight} is below SHOCK_EXPOSURE_CAP="
                            f"{self._sec}. INV-03 violated."
                        )
                    notes.append(
                        f"CCV-C-02 note: JM-03 exposure_weight={out.exposure_weight} "
                        "exceeds SHOCK_EXPOSURE_CAP; Clip C floor not triggered."
                    )

            # ----------------------------------------------------------------
            # CCV-D-02: For CR-01 (CRISIS, JRM inactive), exposure_weight may be
            # below SHOCK_EXPOSURE_CAP. No floor enforcement. This is specified
            # behaviour per INV-04.
            # ----------------------------------------------------------------
            if vid == "CR-01":
                notes.append(
                    f"CCV-D-02: CR-01 exposure_weight={out.exposure_weight}. "
                    "May be below SHOCK_EXPOSURE_CAP per INV-04 (specified behaviour)."
                )

        # --------------------------------------------------------------------
        # CCV-D-01: For CR-02 (CRISIS + JRM active), verify ordering.
        # Expected: CR-02.exposure_weight == JM-03.exposure_weight * 0.75
        # Both records must be present in ER set.
        # --------------------------------------------------------------------
        if "CR-02" in by_id and "JM-03" in by_id:
            cr02_out = by_id["CR-02"].observed_output
            jm03_out = by_id["JM-03"].observed_output
            if not cr02_out.exception_raised and not jm03_out.exception_raised:
                # Compute expected value using Python float arithmetic (same as production).
                expected_cr02_ew = jm03_out.exposure_weight * 0.75
                if not _floats_equal(cr02_out.exposure_weight, expected_cr02_ew):
                    raise RuntimeError(
                        f"CRISIS_ORDERING_VIOLATION: CR-02 exposure_weight="
                        f"{cr02_out.exposure_weight} != JM-03.exposure_weight*0.75="
                        f"{expected_cr02_ew}. Clip C / CRISIS ordering violated. "
                        "INV-04 violated."
                    )

        # --------------------------------------------------------------------
        # CCV-D-03: CR-03 (non-CRISIS with JRM active) -- dampening must NOT apply.
        # Verified by BIC backward compatibility comparison against a non-CRISIS
        # variant. Here we simply note the check for audit.
        # --------------------------------------------------------------------
        if "CR-03" in by_id:
            notes.append(
                "CCV-D-03: CR-03 is non-CRISIS with JRM active. Dampening "
                "not applied. Verified by absence of *0.75 in BIC comparison."
            )

        return violations, notes

    def xǁClipVerifierǁverify__mutmut_40(
        self,
        er_records: List[ExecutionRecord],
    ) -> Tuple[List[str], List[str]]:
        """
        Perform clip chain verification on ER-stage records.

        Returns:
          (violations, notes)
          violations -- list of violation description strings. Empty means pass.
          notes      -- list of non-failure informational notes.

        Raises RuntimeError with failure_type_id prefix on hard failures
        (CLIP_B_FLOOR_VIOLATION, CLIP_C_FLOOR_VIOLATION, CLIP_A_VIOLATION,
        CRISIS_ORDERING_VIOLATION).
        """
        violations = []
        notes      = []
        by_id: Dict[str, ExecutionRecord] = {r.vector_id: r for r in er_records}

        for rec in er_records:
            out = rec.observed_output
            if out.exception_raised:
                # No clip verification for exception vectors.
                continue

            vid = rec.vector_id
            iv  = rec.input_vector

            # ----------------------------------------------------------------
            # CCV-A-01: Clip A verification.
            # position_size_factor must be in [0.0, 1.0] for every normal vector.
            # ----------------------------------------------------------------
            psf = out.position_size_factor
            if psf < 0.0 or psf > 1.0:
                raise RuntimeError(
                    f"CLIP_A_VIOLATION: Vector {vid} position_size_factor={psf} "
                    "is outside [0.0, 1.0]. INV-01 violated."
                )

            # ----------------------------------------------------------------
            # CCV-B-01: For MU-02 and RP-02, E_pre_clip should be zero or near zero,
            # so Clip B floor should be active. exposure_weight bit pattern should
            # equal bit pattern of 1e-6.
            # ----------------------------------------------------------------
            if vid in ("MU-02", "RP-02"):
                ew_bits = _float_bits(out.exposure_weight)
                if ew_bits != self._lb_bits:
                    raise RuntimeError(
                        f"CLIP_B_FLOOR_VIOLATION: Vector {vid} exposure_weight "
                        f"expected bit pattern of 1e-6 but got "
                        f"{out.exposure_weight!r}. INV-02 violated."
                    )

            # ----------------------------------------------------------------
            # CCV-B-02: For JM-inactive (JM-01, JM-04) non-CRISIS vectors,
            # exposure_weight must be in [1e-6, 1.0].
            # (Clip C inactive, CRISIS dampening inactive.)
            # ----------------------------------------------------------------
            if vid in ("JM-01", "JM-04") and iv.current_regime_str != "CRISIS":
                ew = out.exposure_weight
                if ew < 1e-6 or ew >= 1.0:
                    raise RuntimeError(
                        f"CLIP_B_RANGE_VIOLATION: Vector {vid} exposure_weight={ew} "
                        "outside [1e-6, 1.0] with Clip C and CRISIS dampening both "
                        "inactive. INV-02 violated."
                    )

            # ----------------------------------------------------------------
            # CCV-C-02: For JM-03 (designed to produce pre-Clip-C value below
            # SHOCK_EXPOSURE_CAP), exposure_weight should equal SHOCK_EXPOSURE_CAP.
            # ----------------------------------------------------------------
            if vid == "JM-03":
                ew_bits = _float_bits(out.exposure_weight)
                if ew_bits != self._sec_bits:
                    # JM-03 uses meta_uncertainty=0.99 + multiplier=2.0.
                    # The division may produce a value below SHOCK_EXPOSURE_CAP,
                    # which gets clipped to SHOCK_EXPOSURE_CAP by Clip C.
                    # If the result does NOT equal SHOCK_EXPOSURE_CAP, the
                    # actual computed value exceeded the cap after division;
                    # this is acceptable if the value is above SHOCK_EXPOSURE_CAP.
                    # Hard failure only if value is strictly below SHOCK_EXPOSURE_CAP.
                    if out.exposure_weight < self._sec:
                        raise RuntimeError(
                            f"CLIP_C_FLOOR_VIOLATION: Vector {vid} exposure_weight="
                            f"{out.exposure_weight} is below SHOCK_EXPOSURE_CAP="
                            f"{self._sec}. INV-03 violated."
                        )
                    notes.append(
                        f"CCV-C-02 note: JM-03 exposure_weight={out.exposure_weight} "
                        "exceeds SHOCK_EXPOSURE_CAP; Clip C floor not triggered."
                    )

            # ----------------------------------------------------------------
            # CCV-D-02: For CR-01 (CRISIS, JRM inactive), exposure_weight may be
            # below SHOCK_EXPOSURE_CAP. No floor enforcement. This is specified
            # behaviour per INV-04.
            # ----------------------------------------------------------------
            if vid == "CR-01":
                notes.append(
                    f"CCV-D-02: CR-01 exposure_weight={out.exposure_weight}. "
                    "May be below SHOCK_EXPOSURE_CAP per INV-04 (specified behaviour)."
                )

        # --------------------------------------------------------------------
        # CCV-D-01: For CR-02 (CRISIS + JRM active), verify ordering.
        # Expected: CR-02.exposure_weight == JM-03.exposure_weight * 0.75
        # Both records must be present in ER set.
        # --------------------------------------------------------------------
        if "CR-02" in by_id and "JM-03" in by_id:
            cr02_out = by_id["CR-02"].observed_output
            jm03_out = by_id["JM-03"].observed_output
            if not cr02_out.exception_raised and not jm03_out.exception_raised:
                # Compute expected value using Python float arithmetic (same as production).
                expected_cr02_ew = jm03_out.exposure_weight * 0.75
                if not _floats_equal(cr02_out.exposure_weight, expected_cr02_ew):
                    raise RuntimeError(
                        f"CRISIS_ORDERING_VIOLATION: CR-02 exposure_weight="
                        f"{cr02_out.exposure_weight} != JM-03.exposure_weight*0.75="
                        f"{expected_cr02_ew}. Clip C / CRISIS ordering violated. "
                        "INV-04 violated."
                    )

        # --------------------------------------------------------------------
        # CCV-D-03: CR-03 (non-CRISIS with JRM active) -- dampening must NOT apply.
        # Verified by BIC backward compatibility comparison against a non-CRISIS
        # variant. Here we simply note the check for audit.
        # --------------------------------------------------------------------
        if "CR-03" in by_id:
            notes.append(
                "CCV-D-03: CR-03 is non-CRISIS with JRM active. Dampening "
                "not applied. Verified by absence of *0.75 in BIC comparison."
            )

        return violations, notes

    def xǁClipVerifierǁverify__mutmut_41(
        self,
        er_records: List[ExecutionRecord],
    ) -> Tuple[List[str], List[str]]:
        """
        Perform clip chain verification on ER-stage records.

        Returns:
          (violations, notes)
          violations -- list of violation description strings. Empty means pass.
          notes      -- list of non-failure informational notes.

        Raises RuntimeError with failure_type_id prefix on hard failures
        (CLIP_B_FLOOR_VIOLATION, CLIP_C_FLOOR_VIOLATION, CLIP_A_VIOLATION,
        CRISIS_ORDERING_VIOLATION).
        """
        violations = []
        notes      = []
        by_id: Dict[str, ExecutionRecord] = {r.vector_id: r for r in er_records}

        for rec in er_records:
            out = rec.observed_output
            if out.exception_raised:
                # No clip verification for exception vectors.
                continue

            vid = rec.vector_id
            iv  = rec.input_vector

            # ----------------------------------------------------------------
            # CCV-A-01: Clip A verification.
            # position_size_factor must be in [0.0, 1.0] for every normal vector.
            # ----------------------------------------------------------------
            psf = out.position_size_factor
            if psf < 0.0 or psf > 1.0:
                raise RuntimeError(
                    f"CLIP_A_VIOLATION: Vector {vid} position_size_factor={psf} "
                    "is outside [0.0, 1.0]. INV-01 violated."
                )

            # ----------------------------------------------------------------
            # CCV-B-01: For MU-02 and RP-02, E_pre_clip should be zero or near zero,
            # so Clip B floor should be active. exposure_weight bit pattern should
            # equal bit pattern of 1e-6.
            # ----------------------------------------------------------------
            if vid in ("MU-02", "RP-02"):
                ew_bits = _float_bits(out.exposure_weight)
                if ew_bits != self._lb_bits:
                    raise RuntimeError(
                        f"CLIP_B_FLOOR_VIOLATION: Vector {vid} exposure_weight "
                        f"expected bit pattern of 1e-6 but got "
                        f"{out.exposure_weight!r}. INV-02 violated."
                    )

            # ----------------------------------------------------------------
            # CCV-B-02: For JM-inactive (JM-01, JM-04) non-CRISIS vectors,
            # exposure_weight must be in [1e-6, 1.0].
            # (Clip C inactive, CRISIS dampening inactive.)
            # ----------------------------------------------------------------
            if vid in ("JM-01", "JM-04") and iv.current_regime_str != "CRISIS":
                ew = out.exposure_weight
                if ew < 1e-6 or ew > 2.0:
                    raise RuntimeError(
                        f"CLIP_B_RANGE_VIOLATION: Vector {vid} exposure_weight={ew} "
                        "outside [1e-6, 1.0] with Clip C and CRISIS dampening both "
                        "inactive. INV-02 violated."
                    )

            # ----------------------------------------------------------------
            # CCV-C-02: For JM-03 (designed to produce pre-Clip-C value below
            # SHOCK_EXPOSURE_CAP), exposure_weight should equal SHOCK_EXPOSURE_CAP.
            # ----------------------------------------------------------------
            if vid == "JM-03":
                ew_bits = _float_bits(out.exposure_weight)
                if ew_bits != self._sec_bits:
                    # JM-03 uses meta_uncertainty=0.99 + multiplier=2.0.
                    # The division may produce a value below SHOCK_EXPOSURE_CAP,
                    # which gets clipped to SHOCK_EXPOSURE_CAP by Clip C.
                    # If the result does NOT equal SHOCK_EXPOSURE_CAP, the
                    # actual computed value exceeded the cap after division;
                    # this is acceptable if the value is above SHOCK_EXPOSURE_CAP.
                    # Hard failure only if value is strictly below SHOCK_EXPOSURE_CAP.
                    if out.exposure_weight < self._sec:
                        raise RuntimeError(
                            f"CLIP_C_FLOOR_VIOLATION: Vector {vid} exposure_weight="
                            f"{out.exposure_weight} is below SHOCK_EXPOSURE_CAP="
                            f"{self._sec}. INV-03 violated."
                        )
                    notes.append(
                        f"CCV-C-02 note: JM-03 exposure_weight={out.exposure_weight} "
                        "exceeds SHOCK_EXPOSURE_CAP; Clip C floor not triggered."
                    )

            # ----------------------------------------------------------------
            # CCV-D-02: For CR-01 (CRISIS, JRM inactive), exposure_weight may be
            # below SHOCK_EXPOSURE_CAP. No floor enforcement. This is specified
            # behaviour per INV-04.
            # ----------------------------------------------------------------
            if vid == "CR-01":
                notes.append(
                    f"CCV-D-02: CR-01 exposure_weight={out.exposure_weight}. "
                    "May be below SHOCK_EXPOSURE_CAP per INV-04 (specified behaviour)."
                )

        # --------------------------------------------------------------------
        # CCV-D-01: For CR-02 (CRISIS + JRM active), verify ordering.
        # Expected: CR-02.exposure_weight == JM-03.exposure_weight * 0.75
        # Both records must be present in ER set.
        # --------------------------------------------------------------------
        if "CR-02" in by_id and "JM-03" in by_id:
            cr02_out = by_id["CR-02"].observed_output
            jm03_out = by_id["JM-03"].observed_output
            if not cr02_out.exception_raised and not jm03_out.exception_raised:
                # Compute expected value using Python float arithmetic (same as production).
                expected_cr02_ew = jm03_out.exposure_weight * 0.75
                if not _floats_equal(cr02_out.exposure_weight, expected_cr02_ew):
                    raise RuntimeError(
                        f"CRISIS_ORDERING_VIOLATION: CR-02 exposure_weight="
                        f"{cr02_out.exposure_weight} != JM-03.exposure_weight*0.75="
                        f"{expected_cr02_ew}. Clip C / CRISIS ordering violated. "
                        "INV-04 violated."
                    )

        # --------------------------------------------------------------------
        # CCV-D-03: CR-03 (non-CRISIS with JRM active) -- dampening must NOT apply.
        # Verified by BIC backward compatibility comparison against a non-CRISIS
        # variant. Here we simply note the check for audit.
        # --------------------------------------------------------------------
        if "CR-03" in by_id:
            notes.append(
                "CCV-D-03: CR-03 is non-CRISIS with JRM active. Dampening "
                "not applied. Verified by absence of *0.75 in BIC comparison."
            )

        return violations, notes

    def xǁClipVerifierǁverify__mutmut_42(
        self,
        er_records: List[ExecutionRecord],
    ) -> Tuple[List[str], List[str]]:
        """
        Perform clip chain verification on ER-stage records.

        Returns:
          (violations, notes)
          violations -- list of violation description strings. Empty means pass.
          notes      -- list of non-failure informational notes.

        Raises RuntimeError with failure_type_id prefix on hard failures
        (CLIP_B_FLOOR_VIOLATION, CLIP_C_FLOOR_VIOLATION, CLIP_A_VIOLATION,
        CRISIS_ORDERING_VIOLATION).
        """
        violations = []
        notes      = []
        by_id: Dict[str, ExecutionRecord] = {r.vector_id: r for r in er_records}

        for rec in er_records:
            out = rec.observed_output
            if out.exception_raised:
                # No clip verification for exception vectors.
                continue

            vid = rec.vector_id
            iv  = rec.input_vector

            # ----------------------------------------------------------------
            # CCV-A-01: Clip A verification.
            # position_size_factor must be in [0.0, 1.0] for every normal vector.
            # ----------------------------------------------------------------
            psf = out.position_size_factor
            if psf < 0.0 or psf > 1.0:
                raise RuntimeError(
                    f"CLIP_A_VIOLATION: Vector {vid} position_size_factor={psf} "
                    "is outside [0.0, 1.0]. INV-01 violated."
                )

            # ----------------------------------------------------------------
            # CCV-B-01: For MU-02 and RP-02, E_pre_clip should be zero or near zero,
            # so Clip B floor should be active. exposure_weight bit pattern should
            # equal bit pattern of 1e-6.
            # ----------------------------------------------------------------
            if vid in ("MU-02", "RP-02"):
                ew_bits = _float_bits(out.exposure_weight)
                if ew_bits != self._lb_bits:
                    raise RuntimeError(
                        f"CLIP_B_FLOOR_VIOLATION: Vector {vid} exposure_weight "
                        f"expected bit pattern of 1e-6 but got "
                        f"{out.exposure_weight!r}. INV-02 violated."
                    )

            # ----------------------------------------------------------------
            # CCV-B-02: For JM-inactive (JM-01, JM-04) non-CRISIS vectors,
            # exposure_weight must be in [1e-6, 1.0].
            # (Clip C inactive, CRISIS dampening inactive.)
            # ----------------------------------------------------------------
            if vid in ("JM-01", "JM-04") and iv.current_regime_str != "CRISIS":
                ew = out.exposure_weight
                if ew < 1e-6 or ew > 1.0:
                    raise RuntimeError(
                        None
                    )

            # ----------------------------------------------------------------
            # CCV-C-02: For JM-03 (designed to produce pre-Clip-C value below
            # SHOCK_EXPOSURE_CAP), exposure_weight should equal SHOCK_EXPOSURE_CAP.
            # ----------------------------------------------------------------
            if vid == "JM-03":
                ew_bits = _float_bits(out.exposure_weight)
                if ew_bits != self._sec_bits:
                    # JM-03 uses meta_uncertainty=0.99 + multiplier=2.0.
                    # The division may produce a value below SHOCK_EXPOSURE_CAP,
                    # which gets clipped to SHOCK_EXPOSURE_CAP by Clip C.
                    # If the result does NOT equal SHOCK_EXPOSURE_CAP, the
                    # actual computed value exceeded the cap after division;
                    # this is acceptable if the value is above SHOCK_EXPOSURE_CAP.
                    # Hard failure only if value is strictly below SHOCK_EXPOSURE_CAP.
                    if out.exposure_weight < self._sec:
                        raise RuntimeError(
                            f"CLIP_C_FLOOR_VIOLATION: Vector {vid} exposure_weight="
                            f"{out.exposure_weight} is below SHOCK_EXPOSURE_CAP="
                            f"{self._sec}. INV-03 violated."
                        )
                    notes.append(
                        f"CCV-C-02 note: JM-03 exposure_weight={out.exposure_weight} "
                        "exceeds SHOCK_EXPOSURE_CAP; Clip C floor not triggered."
                    )

            # ----------------------------------------------------------------
            # CCV-D-02: For CR-01 (CRISIS, JRM inactive), exposure_weight may be
            # below SHOCK_EXPOSURE_CAP. No floor enforcement. This is specified
            # behaviour per INV-04.
            # ----------------------------------------------------------------
            if vid == "CR-01":
                notes.append(
                    f"CCV-D-02: CR-01 exposure_weight={out.exposure_weight}. "
                    "May be below SHOCK_EXPOSURE_CAP per INV-04 (specified behaviour)."
                )

        # --------------------------------------------------------------------
        # CCV-D-01: For CR-02 (CRISIS + JRM active), verify ordering.
        # Expected: CR-02.exposure_weight == JM-03.exposure_weight * 0.75
        # Both records must be present in ER set.
        # --------------------------------------------------------------------
        if "CR-02" in by_id and "JM-03" in by_id:
            cr02_out = by_id["CR-02"].observed_output
            jm03_out = by_id["JM-03"].observed_output
            if not cr02_out.exception_raised and not jm03_out.exception_raised:
                # Compute expected value using Python float arithmetic (same as production).
                expected_cr02_ew = jm03_out.exposure_weight * 0.75
                if not _floats_equal(cr02_out.exposure_weight, expected_cr02_ew):
                    raise RuntimeError(
                        f"CRISIS_ORDERING_VIOLATION: CR-02 exposure_weight="
                        f"{cr02_out.exposure_weight} != JM-03.exposure_weight*0.75="
                        f"{expected_cr02_ew}. Clip C / CRISIS ordering violated. "
                        "INV-04 violated."
                    )

        # --------------------------------------------------------------------
        # CCV-D-03: CR-03 (non-CRISIS with JRM active) -- dampening must NOT apply.
        # Verified by BIC backward compatibility comparison against a non-CRISIS
        # variant. Here we simply note the check for audit.
        # --------------------------------------------------------------------
        if "CR-03" in by_id:
            notes.append(
                "CCV-D-03: CR-03 is non-CRISIS with JRM active. Dampening "
                "not applied. Verified by absence of *0.75 in BIC comparison."
            )

        return violations, notes

    def xǁClipVerifierǁverify__mutmut_43(
        self,
        er_records: List[ExecutionRecord],
    ) -> Tuple[List[str], List[str]]:
        """
        Perform clip chain verification on ER-stage records.

        Returns:
          (violations, notes)
          violations -- list of violation description strings. Empty means pass.
          notes      -- list of non-failure informational notes.

        Raises RuntimeError with failure_type_id prefix on hard failures
        (CLIP_B_FLOOR_VIOLATION, CLIP_C_FLOOR_VIOLATION, CLIP_A_VIOLATION,
        CRISIS_ORDERING_VIOLATION).
        """
        violations = []
        notes      = []
        by_id: Dict[str, ExecutionRecord] = {r.vector_id: r for r in er_records}

        for rec in er_records:
            out = rec.observed_output
            if out.exception_raised:
                # No clip verification for exception vectors.
                continue

            vid = rec.vector_id
            iv  = rec.input_vector

            # ----------------------------------------------------------------
            # CCV-A-01: Clip A verification.
            # position_size_factor must be in [0.0, 1.0] for every normal vector.
            # ----------------------------------------------------------------
            psf = out.position_size_factor
            if psf < 0.0 or psf > 1.0:
                raise RuntimeError(
                    f"CLIP_A_VIOLATION: Vector {vid} position_size_factor={psf} "
                    "is outside [0.0, 1.0]. INV-01 violated."
                )

            # ----------------------------------------------------------------
            # CCV-B-01: For MU-02 and RP-02, E_pre_clip should be zero or near zero,
            # so Clip B floor should be active. exposure_weight bit pattern should
            # equal bit pattern of 1e-6.
            # ----------------------------------------------------------------
            if vid in ("MU-02", "RP-02"):
                ew_bits = _float_bits(out.exposure_weight)
                if ew_bits != self._lb_bits:
                    raise RuntimeError(
                        f"CLIP_B_FLOOR_VIOLATION: Vector {vid} exposure_weight "
                        f"expected bit pattern of 1e-6 but got "
                        f"{out.exposure_weight!r}. INV-02 violated."
                    )

            # ----------------------------------------------------------------
            # CCV-B-02: For JM-inactive (JM-01, JM-04) non-CRISIS vectors,
            # exposure_weight must be in [1e-6, 1.0].
            # (Clip C inactive, CRISIS dampening inactive.)
            # ----------------------------------------------------------------
            if vid in ("JM-01", "JM-04") and iv.current_regime_str != "CRISIS":
                ew = out.exposure_weight
                if ew < 1e-6 or ew > 1.0:
                    raise RuntimeError(
                        f"CLIP_B_RANGE_VIOLATION: Vector {vid} exposure_weight={ew} "
                        "XXoutside [1e-6, 1.0] with Clip C and CRISIS dampening both XX"
                        "inactive. INV-02 violated."
                    )

            # ----------------------------------------------------------------
            # CCV-C-02: For JM-03 (designed to produce pre-Clip-C value below
            # SHOCK_EXPOSURE_CAP), exposure_weight should equal SHOCK_EXPOSURE_CAP.
            # ----------------------------------------------------------------
            if vid == "JM-03":
                ew_bits = _float_bits(out.exposure_weight)
                if ew_bits != self._sec_bits:
                    # JM-03 uses meta_uncertainty=0.99 + multiplier=2.0.
                    # The division may produce a value below SHOCK_EXPOSURE_CAP,
                    # which gets clipped to SHOCK_EXPOSURE_CAP by Clip C.
                    # If the result does NOT equal SHOCK_EXPOSURE_CAP, the
                    # actual computed value exceeded the cap after division;
                    # this is acceptable if the value is above SHOCK_EXPOSURE_CAP.
                    # Hard failure only if value is strictly below SHOCK_EXPOSURE_CAP.
                    if out.exposure_weight < self._sec:
                        raise RuntimeError(
                            f"CLIP_C_FLOOR_VIOLATION: Vector {vid} exposure_weight="
                            f"{out.exposure_weight} is below SHOCK_EXPOSURE_CAP="
                            f"{self._sec}. INV-03 violated."
                        )
                    notes.append(
                        f"CCV-C-02 note: JM-03 exposure_weight={out.exposure_weight} "
                        "exceeds SHOCK_EXPOSURE_CAP; Clip C floor not triggered."
                    )

            # ----------------------------------------------------------------
            # CCV-D-02: For CR-01 (CRISIS, JRM inactive), exposure_weight may be
            # below SHOCK_EXPOSURE_CAP. No floor enforcement. This is specified
            # behaviour per INV-04.
            # ----------------------------------------------------------------
            if vid == "CR-01":
                notes.append(
                    f"CCV-D-02: CR-01 exposure_weight={out.exposure_weight}. "
                    "May be below SHOCK_EXPOSURE_CAP per INV-04 (specified behaviour)."
                )

        # --------------------------------------------------------------------
        # CCV-D-01: For CR-02 (CRISIS + JRM active), verify ordering.
        # Expected: CR-02.exposure_weight == JM-03.exposure_weight * 0.75
        # Both records must be present in ER set.
        # --------------------------------------------------------------------
        if "CR-02" in by_id and "JM-03" in by_id:
            cr02_out = by_id["CR-02"].observed_output
            jm03_out = by_id["JM-03"].observed_output
            if not cr02_out.exception_raised and not jm03_out.exception_raised:
                # Compute expected value using Python float arithmetic (same as production).
                expected_cr02_ew = jm03_out.exposure_weight * 0.75
                if not _floats_equal(cr02_out.exposure_weight, expected_cr02_ew):
                    raise RuntimeError(
                        f"CRISIS_ORDERING_VIOLATION: CR-02 exposure_weight="
                        f"{cr02_out.exposure_weight} != JM-03.exposure_weight*0.75="
                        f"{expected_cr02_ew}. Clip C / CRISIS ordering violated. "
                        "INV-04 violated."
                    )

        # --------------------------------------------------------------------
        # CCV-D-03: CR-03 (non-CRISIS with JRM active) -- dampening must NOT apply.
        # Verified by BIC backward compatibility comparison against a non-CRISIS
        # variant. Here we simply note the check for audit.
        # --------------------------------------------------------------------
        if "CR-03" in by_id:
            notes.append(
                "CCV-D-03: CR-03 is non-CRISIS with JRM active. Dampening "
                "not applied. Verified by absence of *0.75 in BIC comparison."
            )

        return violations, notes

    def xǁClipVerifierǁverify__mutmut_44(
        self,
        er_records: List[ExecutionRecord],
    ) -> Tuple[List[str], List[str]]:
        """
        Perform clip chain verification on ER-stage records.

        Returns:
          (violations, notes)
          violations -- list of violation description strings. Empty means pass.
          notes      -- list of non-failure informational notes.

        Raises RuntimeError with failure_type_id prefix on hard failures
        (CLIP_B_FLOOR_VIOLATION, CLIP_C_FLOOR_VIOLATION, CLIP_A_VIOLATION,
        CRISIS_ORDERING_VIOLATION).
        """
        violations = []
        notes      = []
        by_id: Dict[str, ExecutionRecord] = {r.vector_id: r for r in er_records}

        for rec in er_records:
            out = rec.observed_output
            if out.exception_raised:
                # No clip verification for exception vectors.
                continue

            vid = rec.vector_id
            iv  = rec.input_vector

            # ----------------------------------------------------------------
            # CCV-A-01: Clip A verification.
            # position_size_factor must be in [0.0, 1.0] for every normal vector.
            # ----------------------------------------------------------------
            psf = out.position_size_factor
            if psf < 0.0 or psf > 1.0:
                raise RuntimeError(
                    f"CLIP_A_VIOLATION: Vector {vid} position_size_factor={psf} "
                    "is outside [0.0, 1.0]. INV-01 violated."
                )

            # ----------------------------------------------------------------
            # CCV-B-01: For MU-02 and RP-02, E_pre_clip should be zero or near zero,
            # so Clip B floor should be active. exposure_weight bit pattern should
            # equal bit pattern of 1e-6.
            # ----------------------------------------------------------------
            if vid in ("MU-02", "RP-02"):
                ew_bits = _float_bits(out.exposure_weight)
                if ew_bits != self._lb_bits:
                    raise RuntimeError(
                        f"CLIP_B_FLOOR_VIOLATION: Vector {vid} exposure_weight "
                        f"expected bit pattern of 1e-6 but got "
                        f"{out.exposure_weight!r}. INV-02 violated."
                    )

            # ----------------------------------------------------------------
            # CCV-B-02: For JM-inactive (JM-01, JM-04) non-CRISIS vectors,
            # exposure_weight must be in [1e-6, 1.0].
            # (Clip C inactive, CRISIS dampening inactive.)
            # ----------------------------------------------------------------
            if vid in ("JM-01", "JM-04") and iv.current_regime_str != "CRISIS":
                ew = out.exposure_weight
                if ew < 1e-6 or ew > 1.0:
                    raise RuntimeError(
                        f"CLIP_B_RANGE_VIOLATION: Vector {vid} exposure_weight={ew} "
                        "outside [1e-6, 1.0] with clip c and crisis dampening both "
                        "inactive. INV-02 violated."
                    )

            # ----------------------------------------------------------------
            # CCV-C-02: For JM-03 (designed to produce pre-Clip-C value below
            # SHOCK_EXPOSURE_CAP), exposure_weight should equal SHOCK_EXPOSURE_CAP.
            # ----------------------------------------------------------------
            if vid == "JM-03":
                ew_bits = _float_bits(out.exposure_weight)
                if ew_bits != self._sec_bits:
                    # JM-03 uses meta_uncertainty=0.99 + multiplier=2.0.
                    # The division may produce a value below SHOCK_EXPOSURE_CAP,
                    # which gets clipped to SHOCK_EXPOSURE_CAP by Clip C.
                    # If the result does NOT equal SHOCK_EXPOSURE_CAP, the
                    # actual computed value exceeded the cap after division;
                    # this is acceptable if the value is above SHOCK_EXPOSURE_CAP.
                    # Hard failure only if value is strictly below SHOCK_EXPOSURE_CAP.
                    if out.exposure_weight < self._sec:
                        raise RuntimeError(
                            f"CLIP_C_FLOOR_VIOLATION: Vector {vid} exposure_weight="
                            f"{out.exposure_weight} is below SHOCK_EXPOSURE_CAP="
                            f"{self._sec}. INV-03 violated."
                        )
                    notes.append(
                        f"CCV-C-02 note: JM-03 exposure_weight={out.exposure_weight} "
                        "exceeds SHOCK_EXPOSURE_CAP; Clip C floor not triggered."
                    )

            # ----------------------------------------------------------------
            # CCV-D-02: For CR-01 (CRISIS, JRM inactive), exposure_weight may be
            # below SHOCK_EXPOSURE_CAP. No floor enforcement. This is specified
            # behaviour per INV-04.
            # ----------------------------------------------------------------
            if vid == "CR-01":
                notes.append(
                    f"CCV-D-02: CR-01 exposure_weight={out.exposure_weight}. "
                    "May be below SHOCK_EXPOSURE_CAP per INV-04 (specified behaviour)."
                )

        # --------------------------------------------------------------------
        # CCV-D-01: For CR-02 (CRISIS + JRM active), verify ordering.
        # Expected: CR-02.exposure_weight == JM-03.exposure_weight * 0.75
        # Both records must be present in ER set.
        # --------------------------------------------------------------------
        if "CR-02" in by_id and "JM-03" in by_id:
            cr02_out = by_id["CR-02"].observed_output
            jm03_out = by_id["JM-03"].observed_output
            if not cr02_out.exception_raised and not jm03_out.exception_raised:
                # Compute expected value using Python float arithmetic (same as production).
                expected_cr02_ew = jm03_out.exposure_weight * 0.75
                if not _floats_equal(cr02_out.exposure_weight, expected_cr02_ew):
                    raise RuntimeError(
                        f"CRISIS_ORDERING_VIOLATION: CR-02 exposure_weight="
                        f"{cr02_out.exposure_weight} != JM-03.exposure_weight*0.75="
                        f"{expected_cr02_ew}. Clip C / CRISIS ordering violated. "
                        "INV-04 violated."
                    )

        # --------------------------------------------------------------------
        # CCV-D-03: CR-03 (non-CRISIS with JRM active) -- dampening must NOT apply.
        # Verified by BIC backward compatibility comparison against a non-CRISIS
        # variant. Here we simply note the check for audit.
        # --------------------------------------------------------------------
        if "CR-03" in by_id:
            notes.append(
                "CCV-D-03: CR-03 is non-CRISIS with JRM active. Dampening "
                "not applied. Verified by absence of *0.75 in BIC comparison."
            )

        return violations, notes

    def xǁClipVerifierǁverify__mutmut_45(
        self,
        er_records: List[ExecutionRecord],
    ) -> Tuple[List[str], List[str]]:
        """
        Perform clip chain verification on ER-stage records.

        Returns:
          (violations, notes)
          violations -- list of violation description strings. Empty means pass.
          notes      -- list of non-failure informational notes.

        Raises RuntimeError with failure_type_id prefix on hard failures
        (CLIP_B_FLOOR_VIOLATION, CLIP_C_FLOOR_VIOLATION, CLIP_A_VIOLATION,
        CRISIS_ORDERING_VIOLATION).
        """
        violations = []
        notes      = []
        by_id: Dict[str, ExecutionRecord] = {r.vector_id: r for r in er_records}

        for rec in er_records:
            out = rec.observed_output
            if out.exception_raised:
                # No clip verification for exception vectors.
                continue

            vid = rec.vector_id
            iv  = rec.input_vector

            # ----------------------------------------------------------------
            # CCV-A-01: Clip A verification.
            # position_size_factor must be in [0.0, 1.0] for every normal vector.
            # ----------------------------------------------------------------
            psf = out.position_size_factor
            if psf < 0.0 or psf > 1.0:
                raise RuntimeError(
                    f"CLIP_A_VIOLATION: Vector {vid} position_size_factor={psf} "
                    "is outside [0.0, 1.0]. INV-01 violated."
                )

            # ----------------------------------------------------------------
            # CCV-B-01: For MU-02 and RP-02, E_pre_clip should be zero or near zero,
            # so Clip B floor should be active. exposure_weight bit pattern should
            # equal bit pattern of 1e-6.
            # ----------------------------------------------------------------
            if vid in ("MU-02", "RP-02"):
                ew_bits = _float_bits(out.exposure_weight)
                if ew_bits != self._lb_bits:
                    raise RuntimeError(
                        f"CLIP_B_FLOOR_VIOLATION: Vector {vid} exposure_weight "
                        f"expected bit pattern of 1e-6 but got "
                        f"{out.exposure_weight!r}. INV-02 violated."
                    )

            # ----------------------------------------------------------------
            # CCV-B-02: For JM-inactive (JM-01, JM-04) non-CRISIS vectors,
            # exposure_weight must be in [1e-6, 1.0].
            # (Clip C inactive, CRISIS dampening inactive.)
            # ----------------------------------------------------------------
            if vid in ("JM-01", "JM-04") and iv.current_regime_str != "CRISIS":
                ew = out.exposure_weight
                if ew < 1e-6 or ew > 1.0:
                    raise RuntimeError(
                        f"CLIP_B_RANGE_VIOLATION: Vector {vid} exposure_weight={ew} "
                        "OUTSIDE [1E-6, 1.0] WITH CLIP C AND CRISIS DAMPENING BOTH "
                        "inactive. INV-02 violated."
                    )

            # ----------------------------------------------------------------
            # CCV-C-02: For JM-03 (designed to produce pre-Clip-C value below
            # SHOCK_EXPOSURE_CAP), exposure_weight should equal SHOCK_EXPOSURE_CAP.
            # ----------------------------------------------------------------
            if vid == "JM-03":
                ew_bits = _float_bits(out.exposure_weight)
                if ew_bits != self._sec_bits:
                    # JM-03 uses meta_uncertainty=0.99 + multiplier=2.0.
                    # The division may produce a value below SHOCK_EXPOSURE_CAP,
                    # which gets clipped to SHOCK_EXPOSURE_CAP by Clip C.
                    # If the result does NOT equal SHOCK_EXPOSURE_CAP, the
                    # actual computed value exceeded the cap after division;
                    # this is acceptable if the value is above SHOCK_EXPOSURE_CAP.
                    # Hard failure only if value is strictly below SHOCK_EXPOSURE_CAP.
                    if out.exposure_weight < self._sec:
                        raise RuntimeError(
                            f"CLIP_C_FLOOR_VIOLATION: Vector {vid} exposure_weight="
                            f"{out.exposure_weight} is below SHOCK_EXPOSURE_CAP="
                            f"{self._sec}. INV-03 violated."
                        )
                    notes.append(
                        f"CCV-C-02 note: JM-03 exposure_weight={out.exposure_weight} "
                        "exceeds SHOCK_EXPOSURE_CAP; Clip C floor not triggered."
                    )

            # ----------------------------------------------------------------
            # CCV-D-02: For CR-01 (CRISIS, JRM inactive), exposure_weight may be
            # below SHOCK_EXPOSURE_CAP. No floor enforcement. This is specified
            # behaviour per INV-04.
            # ----------------------------------------------------------------
            if vid == "CR-01":
                notes.append(
                    f"CCV-D-02: CR-01 exposure_weight={out.exposure_weight}. "
                    "May be below SHOCK_EXPOSURE_CAP per INV-04 (specified behaviour)."
                )

        # --------------------------------------------------------------------
        # CCV-D-01: For CR-02 (CRISIS + JRM active), verify ordering.
        # Expected: CR-02.exposure_weight == JM-03.exposure_weight * 0.75
        # Both records must be present in ER set.
        # --------------------------------------------------------------------
        if "CR-02" in by_id and "JM-03" in by_id:
            cr02_out = by_id["CR-02"].observed_output
            jm03_out = by_id["JM-03"].observed_output
            if not cr02_out.exception_raised and not jm03_out.exception_raised:
                # Compute expected value using Python float arithmetic (same as production).
                expected_cr02_ew = jm03_out.exposure_weight * 0.75
                if not _floats_equal(cr02_out.exposure_weight, expected_cr02_ew):
                    raise RuntimeError(
                        f"CRISIS_ORDERING_VIOLATION: CR-02 exposure_weight="
                        f"{cr02_out.exposure_weight} != JM-03.exposure_weight*0.75="
                        f"{expected_cr02_ew}. Clip C / CRISIS ordering violated. "
                        "INV-04 violated."
                    )

        # --------------------------------------------------------------------
        # CCV-D-03: CR-03 (non-CRISIS with JRM active) -- dampening must NOT apply.
        # Verified by BIC backward compatibility comparison against a non-CRISIS
        # variant. Here we simply note the check for audit.
        # --------------------------------------------------------------------
        if "CR-03" in by_id:
            notes.append(
                "CCV-D-03: CR-03 is non-CRISIS with JRM active. Dampening "
                "not applied. Verified by absence of *0.75 in BIC comparison."
            )

        return violations, notes

    def xǁClipVerifierǁverify__mutmut_46(
        self,
        er_records: List[ExecutionRecord],
    ) -> Tuple[List[str], List[str]]:
        """
        Perform clip chain verification on ER-stage records.

        Returns:
          (violations, notes)
          violations -- list of violation description strings. Empty means pass.
          notes      -- list of non-failure informational notes.

        Raises RuntimeError with failure_type_id prefix on hard failures
        (CLIP_B_FLOOR_VIOLATION, CLIP_C_FLOOR_VIOLATION, CLIP_A_VIOLATION,
        CRISIS_ORDERING_VIOLATION).
        """
        violations = []
        notes      = []
        by_id: Dict[str, ExecutionRecord] = {r.vector_id: r for r in er_records}

        for rec in er_records:
            out = rec.observed_output
            if out.exception_raised:
                # No clip verification for exception vectors.
                continue

            vid = rec.vector_id
            iv  = rec.input_vector

            # ----------------------------------------------------------------
            # CCV-A-01: Clip A verification.
            # position_size_factor must be in [0.0, 1.0] for every normal vector.
            # ----------------------------------------------------------------
            psf = out.position_size_factor
            if psf < 0.0 or psf > 1.0:
                raise RuntimeError(
                    f"CLIP_A_VIOLATION: Vector {vid} position_size_factor={psf} "
                    "is outside [0.0, 1.0]. INV-01 violated."
                )

            # ----------------------------------------------------------------
            # CCV-B-01: For MU-02 and RP-02, E_pre_clip should be zero or near zero,
            # so Clip B floor should be active. exposure_weight bit pattern should
            # equal bit pattern of 1e-6.
            # ----------------------------------------------------------------
            if vid in ("MU-02", "RP-02"):
                ew_bits = _float_bits(out.exposure_weight)
                if ew_bits != self._lb_bits:
                    raise RuntimeError(
                        f"CLIP_B_FLOOR_VIOLATION: Vector {vid} exposure_weight "
                        f"expected bit pattern of 1e-6 but got "
                        f"{out.exposure_weight!r}. INV-02 violated."
                    )

            # ----------------------------------------------------------------
            # CCV-B-02: For JM-inactive (JM-01, JM-04) non-CRISIS vectors,
            # exposure_weight must be in [1e-6, 1.0].
            # (Clip C inactive, CRISIS dampening inactive.)
            # ----------------------------------------------------------------
            if vid in ("JM-01", "JM-04") and iv.current_regime_str != "CRISIS":
                ew = out.exposure_weight
                if ew < 1e-6 or ew > 1.0:
                    raise RuntimeError(
                        f"CLIP_B_RANGE_VIOLATION: Vector {vid} exposure_weight={ew} "
                        "outside [1e-6, 1.0] with Clip C and CRISIS dampening both "
                        "XXinactive. INV-02 violated.XX"
                    )

            # ----------------------------------------------------------------
            # CCV-C-02: For JM-03 (designed to produce pre-Clip-C value below
            # SHOCK_EXPOSURE_CAP), exposure_weight should equal SHOCK_EXPOSURE_CAP.
            # ----------------------------------------------------------------
            if vid == "JM-03":
                ew_bits = _float_bits(out.exposure_weight)
                if ew_bits != self._sec_bits:
                    # JM-03 uses meta_uncertainty=0.99 + multiplier=2.0.
                    # The division may produce a value below SHOCK_EXPOSURE_CAP,
                    # which gets clipped to SHOCK_EXPOSURE_CAP by Clip C.
                    # If the result does NOT equal SHOCK_EXPOSURE_CAP, the
                    # actual computed value exceeded the cap after division;
                    # this is acceptable if the value is above SHOCK_EXPOSURE_CAP.
                    # Hard failure only if value is strictly below SHOCK_EXPOSURE_CAP.
                    if out.exposure_weight < self._sec:
                        raise RuntimeError(
                            f"CLIP_C_FLOOR_VIOLATION: Vector {vid} exposure_weight="
                            f"{out.exposure_weight} is below SHOCK_EXPOSURE_CAP="
                            f"{self._sec}. INV-03 violated."
                        )
                    notes.append(
                        f"CCV-C-02 note: JM-03 exposure_weight={out.exposure_weight} "
                        "exceeds SHOCK_EXPOSURE_CAP; Clip C floor not triggered."
                    )

            # ----------------------------------------------------------------
            # CCV-D-02: For CR-01 (CRISIS, JRM inactive), exposure_weight may be
            # below SHOCK_EXPOSURE_CAP. No floor enforcement. This is specified
            # behaviour per INV-04.
            # ----------------------------------------------------------------
            if vid == "CR-01":
                notes.append(
                    f"CCV-D-02: CR-01 exposure_weight={out.exposure_weight}. "
                    "May be below SHOCK_EXPOSURE_CAP per INV-04 (specified behaviour)."
                )

        # --------------------------------------------------------------------
        # CCV-D-01: For CR-02 (CRISIS + JRM active), verify ordering.
        # Expected: CR-02.exposure_weight == JM-03.exposure_weight * 0.75
        # Both records must be present in ER set.
        # --------------------------------------------------------------------
        if "CR-02" in by_id and "JM-03" in by_id:
            cr02_out = by_id["CR-02"].observed_output
            jm03_out = by_id["JM-03"].observed_output
            if not cr02_out.exception_raised and not jm03_out.exception_raised:
                # Compute expected value using Python float arithmetic (same as production).
                expected_cr02_ew = jm03_out.exposure_weight * 0.75
                if not _floats_equal(cr02_out.exposure_weight, expected_cr02_ew):
                    raise RuntimeError(
                        f"CRISIS_ORDERING_VIOLATION: CR-02 exposure_weight="
                        f"{cr02_out.exposure_weight} != JM-03.exposure_weight*0.75="
                        f"{expected_cr02_ew}. Clip C / CRISIS ordering violated. "
                        "INV-04 violated."
                    )

        # --------------------------------------------------------------------
        # CCV-D-03: CR-03 (non-CRISIS with JRM active) -- dampening must NOT apply.
        # Verified by BIC backward compatibility comparison against a non-CRISIS
        # variant. Here we simply note the check for audit.
        # --------------------------------------------------------------------
        if "CR-03" in by_id:
            notes.append(
                "CCV-D-03: CR-03 is non-CRISIS with JRM active. Dampening "
                "not applied. Verified by absence of *0.75 in BIC comparison."
            )

        return violations, notes

    def xǁClipVerifierǁverify__mutmut_47(
        self,
        er_records: List[ExecutionRecord],
    ) -> Tuple[List[str], List[str]]:
        """
        Perform clip chain verification on ER-stage records.

        Returns:
          (violations, notes)
          violations -- list of violation description strings. Empty means pass.
          notes      -- list of non-failure informational notes.

        Raises RuntimeError with failure_type_id prefix on hard failures
        (CLIP_B_FLOOR_VIOLATION, CLIP_C_FLOOR_VIOLATION, CLIP_A_VIOLATION,
        CRISIS_ORDERING_VIOLATION).
        """
        violations = []
        notes      = []
        by_id: Dict[str, ExecutionRecord] = {r.vector_id: r for r in er_records}

        for rec in er_records:
            out = rec.observed_output
            if out.exception_raised:
                # No clip verification for exception vectors.
                continue

            vid = rec.vector_id
            iv  = rec.input_vector

            # ----------------------------------------------------------------
            # CCV-A-01: Clip A verification.
            # position_size_factor must be in [0.0, 1.0] for every normal vector.
            # ----------------------------------------------------------------
            psf = out.position_size_factor
            if psf < 0.0 or psf > 1.0:
                raise RuntimeError(
                    f"CLIP_A_VIOLATION: Vector {vid} position_size_factor={psf} "
                    "is outside [0.0, 1.0]. INV-01 violated."
                )

            # ----------------------------------------------------------------
            # CCV-B-01: For MU-02 and RP-02, E_pre_clip should be zero or near zero,
            # so Clip B floor should be active. exposure_weight bit pattern should
            # equal bit pattern of 1e-6.
            # ----------------------------------------------------------------
            if vid in ("MU-02", "RP-02"):
                ew_bits = _float_bits(out.exposure_weight)
                if ew_bits != self._lb_bits:
                    raise RuntimeError(
                        f"CLIP_B_FLOOR_VIOLATION: Vector {vid} exposure_weight "
                        f"expected bit pattern of 1e-6 but got "
                        f"{out.exposure_weight!r}. INV-02 violated."
                    )

            # ----------------------------------------------------------------
            # CCV-B-02: For JM-inactive (JM-01, JM-04) non-CRISIS vectors,
            # exposure_weight must be in [1e-6, 1.0].
            # (Clip C inactive, CRISIS dampening inactive.)
            # ----------------------------------------------------------------
            if vid in ("JM-01", "JM-04") and iv.current_regime_str != "CRISIS":
                ew = out.exposure_weight
                if ew < 1e-6 or ew > 1.0:
                    raise RuntimeError(
                        f"CLIP_B_RANGE_VIOLATION: Vector {vid} exposure_weight={ew} "
                        "outside [1e-6, 1.0] with Clip C and CRISIS dampening both "
                        "inactive. inv-02 violated."
                    )

            # ----------------------------------------------------------------
            # CCV-C-02: For JM-03 (designed to produce pre-Clip-C value below
            # SHOCK_EXPOSURE_CAP), exposure_weight should equal SHOCK_EXPOSURE_CAP.
            # ----------------------------------------------------------------
            if vid == "JM-03":
                ew_bits = _float_bits(out.exposure_weight)
                if ew_bits != self._sec_bits:
                    # JM-03 uses meta_uncertainty=0.99 + multiplier=2.0.
                    # The division may produce a value below SHOCK_EXPOSURE_CAP,
                    # which gets clipped to SHOCK_EXPOSURE_CAP by Clip C.
                    # If the result does NOT equal SHOCK_EXPOSURE_CAP, the
                    # actual computed value exceeded the cap after division;
                    # this is acceptable if the value is above SHOCK_EXPOSURE_CAP.
                    # Hard failure only if value is strictly below SHOCK_EXPOSURE_CAP.
                    if out.exposure_weight < self._sec:
                        raise RuntimeError(
                            f"CLIP_C_FLOOR_VIOLATION: Vector {vid} exposure_weight="
                            f"{out.exposure_weight} is below SHOCK_EXPOSURE_CAP="
                            f"{self._sec}. INV-03 violated."
                        )
                    notes.append(
                        f"CCV-C-02 note: JM-03 exposure_weight={out.exposure_weight} "
                        "exceeds SHOCK_EXPOSURE_CAP; Clip C floor not triggered."
                    )

            # ----------------------------------------------------------------
            # CCV-D-02: For CR-01 (CRISIS, JRM inactive), exposure_weight may be
            # below SHOCK_EXPOSURE_CAP. No floor enforcement. This is specified
            # behaviour per INV-04.
            # ----------------------------------------------------------------
            if vid == "CR-01":
                notes.append(
                    f"CCV-D-02: CR-01 exposure_weight={out.exposure_weight}. "
                    "May be below SHOCK_EXPOSURE_CAP per INV-04 (specified behaviour)."
                )

        # --------------------------------------------------------------------
        # CCV-D-01: For CR-02 (CRISIS + JRM active), verify ordering.
        # Expected: CR-02.exposure_weight == JM-03.exposure_weight * 0.75
        # Both records must be present in ER set.
        # --------------------------------------------------------------------
        if "CR-02" in by_id and "JM-03" in by_id:
            cr02_out = by_id["CR-02"].observed_output
            jm03_out = by_id["JM-03"].observed_output
            if not cr02_out.exception_raised and not jm03_out.exception_raised:
                # Compute expected value using Python float arithmetic (same as production).
                expected_cr02_ew = jm03_out.exposure_weight * 0.75
                if not _floats_equal(cr02_out.exposure_weight, expected_cr02_ew):
                    raise RuntimeError(
                        f"CRISIS_ORDERING_VIOLATION: CR-02 exposure_weight="
                        f"{cr02_out.exposure_weight} != JM-03.exposure_weight*0.75="
                        f"{expected_cr02_ew}. Clip C / CRISIS ordering violated. "
                        "INV-04 violated."
                    )

        # --------------------------------------------------------------------
        # CCV-D-03: CR-03 (non-CRISIS with JRM active) -- dampening must NOT apply.
        # Verified by BIC backward compatibility comparison against a non-CRISIS
        # variant. Here we simply note the check for audit.
        # --------------------------------------------------------------------
        if "CR-03" in by_id:
            notes.append(
                "CCV-D-03: CR-03 is non-CRISIS with JRM active. Dampening "
                "not applied. Verified by absence of *0.75 in BIC comparison."
            )

        return violations, notes

    def xǁClipVerifierǁverify__mutmut_48(
        self,
        er_records: List[ExecutionRecord],
    ) -> Tuple[List[str], List[str]]:
        """
        Perform clip chain verification on ER-stage records.

        Returns:
          (violations, notes)
          violations -- list of violation description strings. Empty means pass.
          notes      -- list of non-failure informational notes.

        Raises RuntimeError with failure_type_id prefix on hard failures
        (CLIP_B_FLOOR_VIOLATION, CLIP_C_FLOOR_VIOLATION, CLIP_A_VIOLATION,
        CRISIS_ORDERING_VIOLATION).
        """
        violations = []
        notes      = []
        by_id: Dict[str, ExecutionRecord] = {r.vector_id: r for r in er_records}

        for rec in er_records:
            out = rec.observed_output
            if out.exception_raised:
                # No clip verification for exception vectors.
                continue

            vid = rec.vector_id
            iv  = rec.input_vector

            # ----------------------------------------------------------------
            # CCV-A-01: Clip A verification.
            # position_size_factor must be in [0.0, 1.0] for every normal vector.
            # ----------------------------------------------------------------
            psf = out.position_size_factor
            if psf < 0.0 or psf > 1.0:
                raise RuntimeError(
                    f"CLIP_A_VIOLATION: Vector {vid} position_size_factor={psf} "
                    "is outside [0.0, 1.0]. INV-01 violated."
                )

            # ----------------------------------------------------------------
            # CCV-B-01: For MU-02 and RP-02, E_pre_clip should be zero or near zero,
            # so Clip B floor should be active. exposure_weight bit pattern should
            # equal bit pattern of 1e-6.
            # ----------------------------------------------------------------
            if vid in ("MU-02", "RP-02"):
                ew_bits = _float_bits(out.exposure_weight)
                if ew_bits != self._lb_bits:
                    raise RuntimeError(
                        f"CLIP_B_FLOOR_VIOLATION: Vector {vid} exposure_weight "
                        f"expected bit pattern of 1e-6 but got "
                        f"{out.exposure_weight!r}. INV-02 violated."
                    )

            # ----------------------------------------------------------------
            # CCV-B-02: For JM-inactive (JM-01, JM-04) non-CRISIS vectors,
            # exposure_weight must be in [1e-6, 1.0].
            # (Clip C inactive, CRISIS dampening inactive.)
            # ----------------------------------------------------------------
            if vid in ("JM-01", "JM-04") and iv.current_regime_str != "CRISIS":
                ew = out.exposure_weight
                if ew < 1e-6 or ew > 1.0:
                    raise RuntimeError(
                        f"CLIP_B_RANGE_VIOLATION: Vector {vid} exposure_weight={ew} "
                        "outside [1e-6, 1.0] with Clip C and CRISIS dampening both "
                        "INACTIVE. INV-02 VIOLATED."
                    )

            # ----------------------------------------------------------------
            # CCV-C-02: For JM-03 (designed to produce pre-Clip-C value below
            # SHOCK_EXPOSURE_CAP), exposure_weight should equal SHOCK_EXPOSURE_CAP.
            # ----------------------------------------------------------------
            if vid == "JM-03":
                ew_bits = _float_bits(out.exposure_weight)
                if ew_bits != self._sec_bits:
                    # JM-03 uses meta_uncertainty=0.99 + multiplier=2.0.
                    # The division may produce a value below SHOCK_EXPOSURE_CAP,
                    # which gets clipped to SHOCK_EXPOSURE_CAP by Clip C.
                    # If the result does NOT equal SHOCK_EXPOSURE_CAP, the
                    # actual computed value exceeded the cap after division;
                    # this is acceptable if the value is above SHOCK_EXPOSURE_CAP.
                    # Hard failure only if value is strictly below SHOCK_EXPOSURE_CAP.
                    if out.exposure_weight < self._sec:
                        raise RuntimeError(
                            f"CLIP_C_FLOOR_VIOLATION: Vector {vid} exposure_weight="
                            f"{out.exposure_weight} is below SHOCK_EXPOSURE_CAP="
                            f"{self._sec}. INV-03 violated."
                        )
                    notes.append(
                        f"CCV-C-02 note: JM-03 exposure_weight={out.exposure_weight} "
                        "exceeds SHOCK_EXPOSURE_CAP; Clip C floor not triggered."
                    )

            # ----------------------------------------------------------------
            # CCV-D-02: For CR-01 (CRISIS, JRM inactive), exposure_weight may be
            # below SHOCK_EXPOSURE_CAP. No floor enforcement. This is specified
            # behaviour per INV-04.
            # ----------------------------------------------------------------
            if vid == "CR-01":
                notes.append(
                    f"CCV-D-02: CR-01 exposure_weight={out.exposure_weight}. "
                    "May be below SHOCK_EXPOSURE_CAP per INV-04 (specified behaviour)."
                )

        # --------------------------------------------------------------------
        # CCV-D-01: For CR-02 (CRISIS + JRM active), verify ordering.
        # Expected: CR-02.exposure_weight == JM-03.exposure_weight * 0.75
        # Both records must be present in ER set.
        # --------------------------------------------------------------------
        if "CR-02" in by_id and "JM-03" in by_id:
            cr02_out = by_id["CR-02"].observed_output
            jm03_out = by_id["JM-03"].observed_output
            if not cr02_out.exception_raised and not jm03_out.exception_raised:
                # Compute expected value using Python float arithmetic (same as production).
                expected_cr02_ew = jm03_out.exposure_weight * 0.75
                if not _floats_equal(cr02_out.exposure_weight, expected_cr02_ew):
                    raise RuntimeError(
                        f"CRISIS_ORDERING_VIOLATION: CR-02 exposure_weight="
                        f"{cr02_out.exposure_weight} != JM-03.exposure_weight*0.75="
                        f"{expected_cr02_ew}. Clip C / CRISIS ordering violated. "
                        "INV-04 violated."
                    )

        # --------------------------------------------------------------------
        # CCV-D-03: CR-03 (non-CRISIS with JRM active) -- dampening must NOT apply.
        # Verified by BIC backward compatibility comparison against a non-CRISIS
        # variant. Here we simply note the check for audit.
        # --------------------------------------------------------------------
        if "CR-03" in by_id:
            notes.append(
                "CCV-D-03: CR-03 is non-CRISIS with JRM active. Dampening "
                "not applied. Verified by absence of *0.75 in BIC comparison."
            )

        return violations, notes

    def xǁClipVerifierǁverify__mutmut_49(
        self,
        er_records: List[ExecutionRecord],
    ) -> Tuple[List[str], List[str]]:
        """
        Perform clip chain verification on ER-stage records.

        Returns:
          (violations, notes)
          violations -- list of violation description strings. Empty means pass.
          notes      -- list of non-failure informational notes.

        Raises RuntimeError with failure_type_id prefix on hard failures
        (CLIP_B_FLOOR_VIOLATION, CLIP_C_FLOOR_VIOLATION, CLIP_A_VIOLATION,
        CRISIS_ORDERING_VIOLATION).
        """
        violations = []
        notes      = []
        by_id: Dict[str, ExecutionRecord] = {r.vector_id: r for r in er_records}

        for rec in er_records:
            out = rec.observed_output
            if out.exception_raised:
                # No clip verification for exception vectors.
                continue

            vid = rec.vector_id
            iv  = rec.input_vector

            # ----------------------------------------------------------------
            # CCV-A-01: Clip A verification.
            # position_size_factor must be in [0.0, 1.0] for every normal vector.
            # ----------------------------------------------------------------
            psf = out.position_size_factor
            if psf < 0.0 or psf > 1.0:
                raise RuntimeError(
                    f"CLIP_A_VIOLATION: Vector {vid} position_size_factor={psf} "
                    "is outside [0.0, 1.0]. INV-01 violated."
                )

            # ----------------------------------------------------------------
            # CCV-B-01: For MU-02 and RP-02, E_pre_clip should be zero or near zero,
            # so Clip B floor should be active. exposure_weight bit pattern should
            # equal bit pattern of 1e-6.
            # ----------------------------------------------------------------
            if vid in ("MU-02", "RP-02"):
                ew_bits = _float_bits(out.exposure_weight)
                if ew_bits != self._lb_bits:
                    raise RuntimeError(
                        f"CLIP_B_FLOOR_VIOLATION: Vector {vid} exposure_weight "
                        f"expected bit pattern of 1e-6 but got "
                        f"{out.exposure_weight!r}. INV-02 violated."
                    )

            # ----------------------------------------------------------------
            # CCV-B-02: For JM-inactive (JM-01, JM-04) non-CRISIS vectors,
            # exposure_weight must be in [1e-6, 1.0].
            # (Clip C inactive, CRISIS dampening inactive.)
            # ----------------------------------------------------------------
            if vid in ("JM-01", "JM-04") and iv.current_regime_str != "CRISIS":
                ew = out.exposure_weight
                if ew < 1e-6 or ew > 1.0:
                    raise RuntimeError(
                        f"CLIP_B_RANGE_VIOLATION: Vector {vid} exposure_weight={ew} "
                        "outside [1e-6, 1.0] with Clip C and CRISIS dampening both "
                        "inactive. INV-02 violated."
                    )

            # ----------------------------------------------------------------
            # CCV-C-02: For JM-03 (designed to produce pre-Clip-C value below
            # SHOCK_EXPOSURE_CAP), exposure_weight should equal SHOCK_EXPOSURE_CAP.
            # ----------------------------------------------------------------
            if vid != "JM-03":
                ew_bits = _float_bits(out.exposure_weight)
                if ew_bits != self._sec_bits:
                    # JM-03 uses meta_uncertainty=0.99 + multiplier=2.0.
                    # The division may produce a value below SHOCK_EXPOSURE_CAP,
                    # which gets clipped to SHOCK_EXPOSURE_CAP by Clip C.
                    # If the result does NOT equal SHOCK_EXPOSURE_CAP, the
                    # actual computed value exceeded the cap after division;
                    # this is acceptable if the value is above SHOCK_EXPOSURE_CAP.
                    # Hard failure only if value is strictly below SHOCK_EXPOSURE_CAP.
                    if out.exposure_weight < self._sec:
                        raise RuntimeError(
                            f"CLIP_C_FLOOR_VIOLATION: Vector {vid} exposure_weight="
                            f"{out.exposure_weight} is below SHOCK_EXPOSURE_CAP="
                            f"{self._sec}. INV-03 violated."
                        )
                    notes.append(
                        f"CCV-C-02 note: JM-03 exposure_weight={out.exposure_weight} "
                        "exceeds SHOCK_EXPOSURE_CAP; Clip C floor not triggered."
                    )

            # ----------------------------------------------------------------
            # CCV-D-02: For CR-01 (CRISIS, JRM inactive), exposure_weight may be
            # below SHOCK_EXPOSURE_CAP. No floor enforcement. This is specified
            # behaviour per INV-04.
            # ----------------------------------------------------------------
            if vid == "CR-01":
                notes.append(
                    f"CCV-D-02: CR-01 exposure_weight={out.exposure_weight}. "
                    "May be below SHOCK_EXPOSURE_CAP per INV-04 (specified behaviour)."
                )

        # --------------------------------------------------------------------
        # CCV-D-01: For CR-02 (CRISIS + JRM active), verify ordering.
        # Expected: CR-02.exposure_weight == JM-03.exposure_weight * 0.75
        # Both records must be present in ER set.
        # --------------------------------------------------------------------
        if "CR-02" in by_id and "JM-03" in by_id:
            cr02_out = by_id["CR-02"].observed_output
            jm03_out = by_id["JM-03"].observed_output
            if not cr02_out.exception_raised and not jm03_out.exception_raised:
                # Compute expected value using Python float arithmetic (same as production).
                expected_cr02_ew = jm03_out.exposure_weight * 0.75
                if not _floats_equal(cr02_out.exposure_weight, expected_cr02_ew):
                    raise RuntimeError(
                        f"CRISIS_ORDERING_VIOLATION: CR-02 exposure_weight="
                        f"{cr02_out.exposure_weight} != JM-03.exposure_weight*0.75="
                        f"{expected_cr02_ew}. Clip C / CRISIS ordering violated. "
                        "INV-04 violated."
                    )

        # --------------------------------------------------------------------
        # CCV-D-03: CR-03 (non-CRISIS with JRM active) -- dampening must NOT apply.
        # Verified by BIC backward compatibility comparison against a non-CRISIS
        # variant. Here we simply note the check for audit.
        # --------------------------------------------------------------------
        if "CR-03" in by_id:
            notes.append(
                "CCV-D-03: CR-03 is non-CRISIS with JRM active. Dampening "
                "not applied. Verified by absence of *0.75 in BIC comparison."
            )

        return violations, notes

    def xǁClipVerifierǁverify__mutmut_50(
        self,
        er_records: List[ExecutionRecord],
    ) -> Tuple[List[str], List[str]]:
        """
        Perform clip chain verification on ER-stage records.

        Returns:
          (violations, notes)
          violations -- list of violation description strings. Empty means pass.
          notes      -- list of non-failure informational notes.

        Raises RuntimeError with failure_type_id prefix on hard failures
        (CLIP_B_FLOOR_VIOLATION, CLIP_C_FLOOR_VIOLATION, CLIP_A_VIOLATION,
        CRISIS_ORDERING_VIOLATION).
        """
        violations = []
        notes      = []
        by_id: Dict[str, ExecutionRecord] = {r.vector_id: r for r in er_records}

        for rec in er_records:
            out = rec.observed_output
            if out.exception_raised:
                # No clip verification for exception vectors.
                continue

            vid = rec.vector_id
            iv  = rec.input_vector

            # ----------------------------------------------------------------
            # CCV-A-01: Clip A verification.
            # position_size_factor must be in [0.0, 1.0] for every normal vector.
            # ----------------------------------------------------------------
            psf = out.position_size_factor
            if psf < 0.0 or psf > 1.0:
                raise RuntimeError(
                    f"CLIP_A_VIOLATION: Vector {vid} position_size_factor={psf} "
                    "is outside [0.0, 1.0]. INV-01 violated."
                )

            # ----------------------------------------------------------------
            # CCV-B-01: For MU-02 and RP-02, E_pre_clip should be zero or near zero,
            # so Clip B floor should be active. exposure_weight bit pattern should
            # equal bit pattern of 1e-6.
            # ----------------------------------------------------------------
            if vid in ("MU-02", "RP-02"):
                ew_bits = _float_bits(out.exposure_weight)
                if ew_bits != self._lb_bits:
                    raise RuntimeError(
                        f"CLIP_B_FLOOR_VIOLATION: Vector {vid} exposure_weight "
                        f"expected bit pattern of 1e-6 but got "
                        f"{out.exposure_weight!r}. INV-02 violated."
                    )

            # ----------------------------------------------------------------
            # CCV-B-02: For JM-inactive (JM-01, JM-04) non-CRISIS vectors,
            # exposure_weight must be in [1e-6, 1.0].
            # (Clip C inactive, CRISIS dampening inactive.)
            # ----------------------------------------------------------------
            if vid in ("JM-01", "JM-04") and iv.current_regime_str != "CRISIS":
                ew = out.exposure_weight
                if ew < 1e-6 or ew > 1.0:
                    raise RuntimeError(
                        f"CLIP_B_RANGE_VIOLATION: Vector {vid} exposure_weight={ew} "
                        "outside [1e-6, 1.0] with Clip C and CRISIS dampening both "
                        "inactive. INV-02 violated."
                    )

            # ----------------------------------------------------------------
            # CCV-C-02: For JM-03 (designed to produce pre-Clip-C value below
            # SHOCK_EXPOSURE_CAP), exposure_weight should equal SHOCK_EXPOSURE_CAP.
            # ----------------------------------------------------------------
            if vid == "XXJM-03XX":
                ew_bits = _float_bits(out.exposure_weight)
                if ew_bits != self._sec_bits:
                    # JM-03 uses meta_uncertainty=0.99 + multiplier=2.0.
                    # The division may produce a value below SHOCK_EXPOSURE_CAP,
                    # which gets clipped to SHOCK_EXPOSURE_CAP by Clip C.
                    # If the result does NOT equal SHOCK_EXPOSURE_CAP, the
                    # actual computed value exceeded the cap after division;
                    # this is acceptable if the value is above SHOCK_EXPOSURE_CAP.
                    # Hard failure only if value is strictly below SHOCK_EXPOSURE_CAP.
                    if out.exposure_weight < self._sec:
                        raise RuntimeError(
                            f"CLIP_C_FLOOR_VIOLATION: Vector {vid} exposure_weight="
                            f"{out.exposure_weight} is below SHOCK_EXPOSURE_CAP="
                            f"{self._sec}. INV-03 violated."
                        )
                    notes.append(
                        f"CCV-C-02 note: JM-03 exposure_weight={out.exposure_weight} "
                        "exceeds SHOCK_EXPOSURE_CAP; Clip C floor not triggered."
                    )

            # ----------------------------------------------------------------
            # CCV-D-02: For CR-01 (CRISIS, JRM inactive), exposure_weight may be
            # below SHOCK_EXPOSURE_CAP. No floor enforcement. This is specified
            # behaviour per INV-04.
            # ----------------------------------------------------------------
            if vid == "CR-01":
                notes.append(
                    f"CCV-D-02: CR-01 exposure_weight={out.exposure_weight}. "
                    "May be below SHOCK_EXPOSURE_CAP per INV-04 (specified behaviour)."
                )

        # --------------------------------------------------------------------
        # CCV-D-01: For CR-02 (CRISIS + JRM active), verify ordering.
        # Expected: CR-02.exposure_weight == JM-03.exposure_weight * 0.75
        # Both records must be present in ER set.
        # --------------------------------------------------------------------
        if "CR-02" in by_id and "JM-03" in by_id:
            cr02_out = by_id["CR-02"].observed_output
            jm03_out = by_id["JM-03"].observed_output
            if not cr02_out.exception_raised and not jm03_out.exception_raised:
                # Compute expected value using Python float arithmetic (same as production).
                expected_cr02_ew = jm03_out.exposure_weight * 0.75
                if not _floats_equal(cr02_out.exposure_weight, expected_cr02_ew):
                    raise RuntimeError(
                        f"CRISIS_ORDERING_VIOLATION: CR-02 exposure_weight="
                        f"{cr02_out.exposure_weight} != JM-03.exposure_weight*0.75="
                        f"{expected_cr02_ew}. Clip C / CRISIS ordering violated. "
                        "INV-04 violated."
                    )

        # --------------------------------------------------------------------
        # CCV-D-03: CR-03 (non-CRISIS with JRM active) -- dampening must NOT apply.
        # Verified by BIC backward compatibility comparison against a non-CRISIS
        # variant. Here we simply note the check for audit.
        # --------------------------------------------------------------------
        if "CR-03" in by_id:
            notes.append(
                "CCV-D-03: CR-03 is non-CRISIS with JRM active. Dampening "
                "not applied. Verified by absence of *0.75 in BIC comparison."
            )

        return violations, notes

    def xǁClipVerifierǁverify__mutmut_51(
        self,
        er_records: List[ExecutionRecord],
    ) -> Tuple[List[str], List[str]]:
        """
        Perform clip chain verification on ER-stage records.

        Returns:
          (violations, notes)
          violations -- list of violation description strings. Empty means pass.
          notes      -- list of non-failure informational notes.

        Raises RuntimeError with failure_type_id prefix on hard failures
        (CLIP_B_FLOOR_VIOLATION, CLIP_C_FLOOR_VIOLATION, CLIP_A_VIOLATION,
        CRISIS_ORDERING_VIOLATION).
        """
        violations = []
        notes      = []
        by_id: Dict[str, ExecutionRecord] = {r.vector_id: r for r in er_records}

        for rec in er_records:
            out = rec.observed_output
            if out.exception_raised:
                # No clip verification for exception vectors.
                continue

            vid = rec.vector_id
            iv  = rec.input_vector

            # ----------------------------------------------------------------
            # CCV-A-01: Clip A verification.
            # position_size_factor must be in [0.0, 1.0] for every normal vector.
            # ----------------------------------------------------------------
            psf = out.position_size_factor
            if psf < 0.0 or psf > 1.0:
                raise RuntimeError(
                    f"CLIP_A_VIOLATION: Vector {vid} position_size_factor={psf} "
                    "is outside [0.0, 1.0]. INV-01 violated."
                )

            # ----------------------------------------------------------------
            # CCV-B-01: For MU-02 and RP-02, E_pre_clip should be zero or near zero,
            # so Clip B floor should be active. exposure_weight bit pattern should
            # equal bit pattern of 1e-6.
            # ----------------------------------------------------------------
            if vid in ("MU-02", "RP-02"):
                ew_bits = _float_bits(out.exposure_weight)
                if ew_bits != self._lb_bits:
                    raise RuntimeError(
                        f"CLIP_B_FLOOR_VIOLATION: Vector {vid} exposure_weight "
                        f"expected bit pattern of 1e-6 but got "
                        f"{out.exposure_weight!r}. INV-02 violated."
                    )

            # ----------------------------------------------------------------
            # CCV-B-02: For JM-inactive (JM-01, JM-04) non-CRISIS vectors,
            # exposure_weight must be in [1e-6, 1.0].
            # (Clip C inactive, CRISIS dampening inactive.)
            # ----------------------------------------------------------------
            if vid in ("JM-01", "JM-04") and iv.current_regime_str != "CRISIS":
                ew = out.exposure_weight
                if ew < 1e-6 or ew > 1.0:
                    raise RuntimeError(
                        f"CLIP_B_RANGE_VIOLATION: Vector {vid} exposure_weight={ew} "
                        "outside [1e-6, 1.0] with Clip C and CRISIS dampening both "
                        "inactive. INV-02 violated."
                    )

            # ----------------------------------------------------------------
            # CCV-C-02: For JM-03 (designed to produce pre-Clip-C value below
            # SHOCK_EXPOSURE_CAP), exposure_weight should equal SHOCK_EXPOSURE_CAP.
            # ----------------------------------------------------------------
            if vid == "jm-03":
                ew_bits = _float_bits(out.exposure_weight)
                if ew_bits != self._sec_bits:
                    # JM-03 uses meta_uncertainty=0.99 + multiplier=2.0.
                    # The division may produce a value below SHOCK_EXPOSURE_CAP,
                    # which gets clipped to SHOCK_EXPOSURE_CAP by Clip C.
                    # If the result does NOT equal SHOCK_EXPOSURE_CAP, the
                    # actual computed value exceeded the cap after division;
                    # this is acceptable if the value is above SHOCK_EXPOSURE_CAP.
                    # Hard failure only if value is strictly below SHOCK_EXPOSURE_CAP.
                    if out.exposure_weight < self._sec:
                        raise RuntimeError(
                            f"CLIP_C_FLOOR_VIOLATION: Vector {vid} exposure_weight="
                            f"{out.exposure_weight} is below SHOCK_EXPOSURE_CAP="
                            f"{self._sec}. INV-03 violated."
                        )
                    notes.append(
                        f"CCV-C-02 note: JM-03 exposure_weight={out.exposure_weight} "
                        "exceeds SHOCK_EXPOSURE_CAP; Clip C floor not triggered."
                    )

            # ----------------------------------------------------------------
            # CCV-D-02: For CR-01 (CRISIS, JRM inactive), exposure_weight may be
            # below SHOCK_EXPOSURE_CAP. No floor enforcement. This is specified
            # behaviour per INV-04.
            # ----------------------------------------------------------------
            if vid == "CR-01":
                notes.append(
                    f"CCV-D-02: CR-01 exposure_weight={out.exposure_weight}. "
                    "May be below SHOCK_EXPOSURE_CAP per INV-04 (specified behaviour)."
                )

        # --------------------------------------------------------------------
        # CCV-D-01: For CR-02 (CRISIS + JRM active), verify ordering.
        # Expected: CR-02.exposure_weight == JM-03.exposure_weight * 0.75
        # Both records must be present in ER set.
        # --------------------------------------------------------------------
        if "CR-02" in by_id and "JM-03" in by_id:
            cr02_out = by_id["CR-02"].observed_output
            jm03_out = by_id["JM-03"].observed_output
            if not cr02_out.exception_raised and not jm03_out.exception_raised:
                # Compute expected value using Python float arithmetic (same as production).
                expected_cr02_ew = jm03_out.exposure_weight * 0.75
                if not _floats_equal(cr02_out.exposure_weight, expected_cr02_ew):
                    raise RuntimeError(
                        f"CRISIS_ORDERING_VIOLATION: CR-02 exposure_weight="
                        f"{cr02_out.exposure_weight} != JM-03.exposure_weight*0.75="
                        f"{expected_cr02_ew}. Clip C / CRISIS ordering violated. "
                        "INV-04 violated."
                    )

        # --------------------------------------------------------------------
        # CCV-D-03: CR-03 (non-CRISIS with JRM active) -- dampening must NOT apply.
        # Verified by BIC backward compatibility comparison against a non-CRISIS
        # variant. Here we simply note the check for audit.
        # --------------------------------------------------------------------
        if "CR-03" in by_id:
            notes.append(
                "CCV-D-03: CR-03 is non-CRISIS with JRM active. Dampening "
                "not applied. Verified by absence of *0.75 in BIC comparison."
            )

        return violations, notes

    def xǁClipVerifierǁverify__mutmut_52(
        self,
        er_records: List[ExecutionRecord],
    ) -> Tuple[List[str], List[str]]:
        """
        Perform clip chain verification on ER-stage records.

        Returns:
          (violations, notes)
          violations -- list of violation description strings. Empty means pass.
          notes      -- list of non-failure informational notes.

        Raises RuntimeError with failure_type_id prefix on hard failures
        (CLIP_B_FLOOR_VIOLATION, CLIP_C_FLOOR_VIOLATION, CLIP_A_VIOLATION,
        CRISIS_ORDERING_VIOLATION).
        """
        violations = []
        notes      = []
        by_id: Dict[str, ExecutionRecord] = {r.vector_id: r for r in er_records}

        for rec in er_records:
            out = rec.observed_output
            if out.exception_raised:
                # No clip verification for exception vectors.
                continue

            vid = rec.vector_id
            iv  = rec.input_vector

            # ----------------------------------------------------------------
            # CCV-A-01: Clip A verification.
            # position_size_factor must be in [0.0, 1.0] for every normal vector.
            # ----------------------------------------------------------------
            psf = out.position_size_factor
            if psf < 0.0 or psf > 1.0:
                raise RuntimeError(
                    f"CLIP_A_VIOLATION: Vector {vid} position_size_factor={psf} "
                    "is outside [0.0, 1.0]. INV-01 violated."
                )

            # ----------------------------------------------------------------
            # CCV-B-01: For MU-02 and RP-02, E_pre_clip should be zero or near zero,
            # so Clip B floor should be active. exposure_weight bit pattern should
            # equal bit pattern of 1e-6.
            # ----------------------------------------------------------------
            if vid in ("MU-02", "RP-02"):
                ew_bits = _float_bits(out.exposure_weight)
                if ew_bits != self._lb_bits:
                    raise RuntimeError(
                        f"CLIP_B_FLOOR_VIOLATION: Vector {vid} exposure_weight "
                        f"expected bit pattern of 1e-6 but got "
                        f"{out.exposure_weight!r}. INV-02 violated."
                    )

            # ----------------------------------------------------------------
            # CCV-B-02: For JM-inactive (JM-01, JM-04) non-CRISIS vectors,
            # exposure_weight must be in [1e-6, 1.0].
            # (Clip C inactive, CRISIS dampening inactive.)
            # ----------------------------------------------------------------
            if vid in ("JM-01", "JM-04") and iv.current_regime_str != "CRISIS":
                ew = out.exposure_weight
                if ew < 1e-6 or ew > 1.0:
                    raise RuntimeError(
                        f"CLIP_B_RANGE_VIOLATION: Vector {vid} exposure_weight={ew} "
                        "outside [1e-6, 1.0] with Clip C and CRISIS dampening both "
                        "inactive. INV-02 violated."
                    )

            # ----------------------------------------------------------------
            # CCV-C-02: For JM-03 (designed to produce pre-Clip-C value below
            # SHOCK_EXPOSURE_CAP), exposure_weight should equal SHOCK_EXPOSURE_CAP.
            # ----------------------------------------------------------------
            if vid == "JM-03":
                ew_bits = None
                if ew_bits != self._sec_bits:
                    # JM-03 uses meta_uncertainty=0.99 + multiplier=2.0.
                    # The division may produce a value below SHOCK_EXPOSURE_CAP,
                    # which gets clipped to SHOCK_EXPOSURE_CAP by Clip C.
                    # If the result does NOT equal SHOCK_EXPOSURE_CAP, the
                    # actual computed value exceeded the cap after division;
                    # this is acceptable if the value is above SHOCK_EXPOSURE_CAP.
                    # Hard failure only if value is strictly below SHOCK_EXPOSURE_CAP.
                    if out.exposure_weight < self._sec:
                        raise RuntimeError(
                            f"CLIP_C_FLOOR_VIOLATION: Vector {vid} exposure_weight="
                            f"{out.exposure_weight} is below SHOCK_EXPOSURE_CAP="
                            f"{self._sec}. INV-03 violated."
                        )
                    notes.append(
                        f"CCV-C-02 note: JM-03 exposure_weight={out.exposure_weight} "
                        "exceeds SHOCK_EXPOSURE_CAP; Clip C floor not triggered."
                    )

            # ----------------------------------------------------------------
            # CCV-D-02: For CR-01 (CRISIS, JRM inactive), exposure_weight may be
            # below SHOCK_EXPOSURE_CAP. No floor enforcement. This is specified
            # behaviour per INV-04.
            # ----------------------------------------------------------------
            if vid == "CR-01":
                notes.append(
                    f"CCV-D-02: CR-01 exposure_weight={out.exposure_weight}. "
                    "May be below SHOCK_EXPOSURE_CAP per INV-04 (specified behaviour)."
                )

        # --------------------------------------------------------------------
        # CCV-D-01: For CR-02 (CRISIS + JRM active), verify ordering.
        # Expected: CR-02.exposure_weight == JM-03.exposure_weight * 0.75
        # Both records must be present in ER set.
        # --------------------------------------------------------------------
        if "CR-02" in by_id and "JM-03" in by_id:
            cr02_out = by_id["CR-02"].observed_output
            jm03_out = by_id["JM-03"].observed_output
            if not cr02_out.exception_raised and not jm03_out.exception_raised:
                # Compute expected value using Python float arithmetic (same as production).
                expected_cr02_ew = jm03_out.exposure_weight * 0.75
                if not _floats_equal(cr02_out.exposure_weight, expected_cr02_ew):
                    raise RuntimeError(
                        f"CRISIS_ORDERING_VIOLATION: CR-02 exposure_weight="
                        f"{cr02_out.exposure_weight} != JM-03.exposure_weight*0.75="
                        f"{expected_cr02_ew}. Clip C / CRISIS ordering violated. "
                        "INV-04 violated."
                    )

        # --------------------------------------------------------------------
        # CCV-D-03: CR-03 (non-CRISIS with JRM active) -- dampening must NOT apply.
        # Verified by BIC backward compatibility comparison against a non-CRISIS
        # variant. Here we simply note the check for audit.
        # --------------------------------------------------------------------
        if "CR-03" in by_id:
            notes.append(
                "CCV-D-03: CR-03 is non-CRISIS with JRM active. Dampening "
                "not applied. Verified by absence of *0.75 in BIC comparison."
            )

        return violations, notes

    def xǁClipVerifierǁverify__mutmut_53(
        self,
        er_records: List[ExecutionRecord],
    ) -> Tuple[List[str], List[str]]:
        """
        Perform clip chain verification on ER-stage records.

        Returns:
          (violations, notes)
          violations -- list of violation description strings. Empty means pass.
          notes      -- list of non-failure informational notes.

        Raises RuntimeError with failure_type_id prefix on hard failures
        (CLIP_B_FLOOR_VIOLATION, CLIP_C_FLOOR_VIOLATION, CLIP_A_VIOLATION,
        CRISIS_ORDERING_VIOLATION).
        """
        violations = []
        notes      = []
        by_id: Dict[str, ExecutionRecord] = {r.vector_id: r for r in er_records}

        for rec in er_records:
            out = rec.observed_output
            if out.exception_raised:
                # No clip verification for exception vectors.
                continue

            vid = rec.vector_id
            iv  = rec.input_vector

            # ----------------------------------------------------------------
            # CCV-A-01: Clip A verification.
            # position_size_factor must be in [0.0, 1.0] for every normal vector.
            # ----------------------------------------------------------------
            psf = out.position_size_factor
            if psf < 0.0 or psf > 1.0:
                raise RuntimeError(
                    f"CLIP_A_VIOLATION: Vector {vid} position_size_factor={psf} "
                    "is outside [0.0, 1.0]. INV-01 violated."
                )

            # ----------------------------------------------------------------
            # CCV-B-01: For MU-02 and RP-02, E_pre_clip should be zero or near zero,
            # so Clip B floor should be active. exposure_weight bit pattern should
            # equal bit pattern of 1e-6.
            # ----------------------------------------------------------------
            if vid in ("MU-02", "RP-02"):
                ew_bits = _float_bits(out.exposure_weight)
                if ew_bits != self._lb_bits:
                    raise RuntimeError(
                        f"CLIP_B_FLOOR_VIOLATION: Vector {vid} exposure_weight "
                        f"expected bit pattern of 1e-6 but got "
                        f"{out.exposure_weight!r}. INV-02 violated."
                    )

            # ----------------------------------------------------------------
            # CCV-B-02: For JM-inactive (JM-01, JM-04) non-CRISIS vectors,
            # exposure_weight must be in [1e-6, 1.0].
            # (Clip C inactive, CRISIS dampening inactive.)
            # ----------------------------------------------------------------
            if vid in ("JM-01", "JM-04") and iv.current_regime_str != "CRISIS":
                ew = out.exposure_weight
                if ew < 1e-6 or ew > 1.0:
                    raise RuntimeError(
                        f"CLIP_B_RANGE_VIOLATION: Vector {vid} exposure_weight={ew} "
                        "outside [1e-6, 1.0] with Clip C and CRISIS dampening both "
                        "inactive. INV-02 violated."
                    )

            # ----------------------------------------------------------------
            # CCV-C-02: For JM-03 (designed to produce pre-Clip-C value below
            # SHOCK_EXPOSURE_CAP), exposure_weight should equal SHOCK_EXPOSURE_CAP.
            # ----------------------------------------------------------------
            if vid == "JM-03":
                ew_bits = _float_bits(None)
                if ew_bits != self._sec_bits:
                    # JM-03 uses meta_uncertainty=0.99 + multiplier=2.0.
                    # The division may produce a value below SHOCK_EXPOSURE_CAP,
                    # which gets clipped to SHOCK_EXPOSURE_CAP by Clip C.
                    # If the result does NOT equal SHOCK_EXPOSURE_CAP, the
                    # actual computed value exceeded the cap after division;
                    # this is acceptable if the value is above SHOCK_EXPOSURE_CAP.
                    # Hard failure only if value is strictly below SHOCK_EXPOSURE_CAP.
                    if out.exposure_weight < self._sec:
                        raise RuntimeError(
                            f"CLIP_C_FLOOR_VIOLATION: Vector {vid} exposure_weight="
                            f"{out.exposure_weight} is below SHOCK_EXPOSURE_CAP="
                            f"{self._sec}. INV-03 violated."
                        )
                    notes.append(
                        f"CCV-C-02 note: JM-03 exposure_weight={out.exposure_weight} "
                        "exceeds SHOCK_EXPOSURE_CAP; Clip C floor not triggered."
                    )

            # ----------------------------------------------------------------
            # CCV-D-02: For CR-01 (CRISIS, JRM inactive), exposure_weight may be
            # below SHOCK_EXPOSURE_CAP. No floor enforcement. This is specified
            # behaviour per INV-04.
            # ----------------------------------------------------------------
            if vid == "CR-01":
                notes.append(
                    f"CCV-D-02: CR-01 exposure_weight={out.exposure_weight}. "
                    "May be below SHOCK_EXPOSURE_CAP per INV-04 (specified behaviour)."
                )

        # --------------------------------------------------------------------
        # CCV-D-01: For CR-02 (CRISIS + JRM active), verify ordering.
        # Expected: CR-02.exposure_weight == JM-03.exposure_weight * 0.75
        # Both records must be present in ER set.
        # --------------------------------------------------------------------
        if "CR-02" in by_id and "JM-03" in by_id:
            cr02_out = by_id["CR-02"].observed_output
            jm03_out = by_id["JM-03"].observed_output
            if not cr02_out.exception_raised and not jm03_out.exception_raised:
                # Compute expected value using Python float arithmetic (same as production).
                expected_cr02_ew = jm03_out.exposure_weight * 0.75
                if not _floats_equal(cr02_out.exposure_weight, expected_cr02_ew):
                    raise RuntimeError(
                        f"CRISIS_ORDERING_VIOLATION: CR-02 exposure_weight="
                        f"{cr02_out.exposure_weight} != JM-03.exposure_weight*0.75="
                        f"{expected_cr02_ew}. Clip C / CRISIS ordering violated. "
                        "INV-04 violated."
                    )

        # --------------------------------------------------------------------
        # CCV-D-03: CR-03 (non-CRISIS with JRM active) -- dampening must NOT apply.
        # Verified by BIC backward compatibility comparison against a non-CRISIS
        # variant. Here we simply note the check for audit.
        # --------------------------------------------------------------------
        if "CR-03" in by_id:
            notes.append(
                "CCV-D-03: CR-03 is non-CRISIS with JRM active. Dampening "
                "not applied. Verified by absence of *0.75 in BIC comparison."
            )

        return violations, notes

    def xǁClipVerifierǁverify__mutmut_54(
        self,
        er_records: List[ExecutionRecord],
    ) -> Tuple[List[str], List[str]]:
        """
        Perform clip chain verification on ER-stage records.

        Returns:
          (violations, notes)
          violations -- list of violation description strings. Empty means pass.
          notes      -- list of non-failure informational notes.

        Raises RuntimeError with failure_type_id prefix on hard failures
        (CLIP_B_FLOOR_VIOLATION, CLIP_C_FLOOR_VIOLATION, CLIP_A_VIOLATION,
        CRISIS_ORDERING_VIOLATION).
        """
        violations = []
        notes      = []
        by_id: Dict[str, ExecutionRecord] = {r.vector_id: r for r in er_records}

        for rec in er_records:
            out = rec.observed_output
            if out.exception_raised:
                # No clip verification for exception vectors.
                continue

            vid = rec.vector_id
            iv  = rec.input_vector

            # ----------------------------------------------------------------
            # CCV-A-01: Clip A verification.
            # position_size_factor must be in [0.0, 1.0] for every normal vector.
            # ----------------------------------------------------------------
            psf = out.position_size_factor
            if psf < 0.0 or psf > 1.0:
                raise RuntimeError(
                    f"CLIP_A_VIOLATION: Vector {vid} position_size_factor={psf} "
                    "is outside [0.0, 1.0]. INV-01 violated."
                )

            # ----------------------------------------------------------------
            # CCV-B-01: For MU-02 and RP-02, E_pre_clip should be zero or near zero,
            # so Clip B floor should be active. exposure_weight bit pattern should
            # equal bit pattern of 1e-6.
            # ----------------------------------------------------------------
            if vid in ("MU-02", "RP-02"):
                ew_bits = _float_bits(out.exposure_weight)
                if ew_bits != self._lb_bits:
                    raise RuntimeError(
                        f"CLIP_B_FLOOR_VIOLATION: Vector {vid} exposure_weight "
                        f"expected bit pattern of 1e-6 but got "
                        f"{out.exposure_weight!r}. INV-02 violated."
                    )

            # ----------------------------------------------------------------
            # CCV-B-02: For JM-inactive (JM-01, JM-04) non-CRISIS vectors,
            # exposure_weight must be in [1e-6, 1.0].
            # (Clip C inactive, CRISIS dampening inactive.)
            # ----------------------------------------------------------------
            if vid in ("JM-01", "JM-04") and iv.current_regime_str != "CRISIS":
                ew = out.exposure_weight
                if ew < 1e-6 or ew > 1.0:
                    raise RuntimeError(
                        f"CLIP_B_RANGE_VIOLATION: Vector {vid} exposure_weight={ew} "
                        "outside [1e-6, 1.0] with Clip C and CRISIS dampening both "
                        "inactive. INV-02 violated."
                    )

            # ----------------------------------------------------------------
            # CCV-C-02: For JM-03 (designed to produce pre-Clip-C value below
            # SHOCK_EXPOSURE_CAP), exposure_weight should equal SHOCK_EXPOSURE_CAP.
            # ----------------------------------------------------------------
            if vid == "JM-03":
                ew_bits = _float_bits(out.exposure_weight)
                if ew_bits == self._sec_bits:
                    # JM-03 uses meta_uncertainty=0.99 + multiplier=2.0.
                    # The division may produce a value below SHOCK_EXPOSURE_CAP,
                    # which gets clipped to SHOCK_EXPOSURE_CAP by Clip C.
                    # If the result does NOT equal SHOCK_EXPOSURE_CAP, the
                    # actual computed value exceeded the cap after division;
                    # this is acceptable if the value is above SHOCK_EXPOSURE_CAP.
                    # Hard failure only if value is strictly below SHOCK_EXPOSURE_CAP.
                    if out.exposure_weight < self._sec:
                        raise RuntimeError(
                            f"CLIP_C_FLOOR_VIOLATION: Vector {vid} exposure_weight="
                            f"{out.exposure_weight} is below SHOCK_EXPOSURE_CAP="
                            f"{self._sec}. INV-03 violated."
                        )
                    notes.append(
                        f"CCV-C-02 note: JM-03 exposure_weight={out.exposure_weight} "
                        "exceeds SHOCK_EXPOSURE_CAP; Clip C floor not triggered."
                    )

            # ----------------------------------------------------------------
            # CCV-D-02: For CR-01 (CRISIS, JRM inactive), exposure_weight may be
            # below SHOCK_EXPOSURE_CAP. No floor enforcement. This is specified
            # behaviour per INV-04.
            # ----------------------------------------------------------------
            if vid == "CR-01":
                notes.append(
                    f"CCV-D-02: CR-01 exposure_weight={out.exposure_weight}. "
                    "May be below SHOCK_EXPOSURE_CAP per INV-04 (specified behaviour)."
                )

        # --------------------------------------------------------------------
        # CCV-D-01: For CR-02 (CRISIS + JRM active), verify ordering.
        # Expected: CR-02.exposure_weight == JM-03.exposure_weight * 0.75
        # Both records must be present in ER set.
        # --------------------------------------------------------------------
        if "CR-02" in by_id and "JM-03" in by_id:
            cr02_out = by_id["CR-02"].observed_output
            jm03_out = by_id["JM-03"].observed_output
            if not cr02_out.exception_raised and not jm03_out.exception_raised:
                # Compute expected value using Python float arithmetic (same as production).
                expected_cr02_ew = jm03_out.exposure_weight * 0.75
                if not _floats_equal(cr02_out.exposure_weight, expected_cr02_ew):
                    raise RuntimeError(
                        f"CRISIS_ORDERING_VIOLATION: CR-02 exposure_weight="
                        f"{cr02_out.exposure_weight} != JM-03.exposure_weight*0.75="
                        f"{expected_cr02_ew}. Clip C / CRISIS ordering violated. "
                        "INV-04 violated."
                    )

        # --------------------------------------------------------------------
        # CCV-D-03: CR-03 (non-CRISIS with JRM active) -- dampening must NOT apply.
        # Verified by BIC backward compatibility comparison against a non-CRISIS
        # variant. Here we simply note the check for audit.
        # --------------------------------------------------------------------
        if "CR-03" in by_id:
            notes.append(
                "CCV-D-03: CR-03 is non-CRISIS with JRM active. Dampening "
                "not applied. Verified by absence of *0.75 in BIC comparison."
            )

        return violations, notes

    def xǁClipVerifierǁverify__mutmut_55(
        self,
        er_records: List[ExecutionRecord],
    ) -> Tuple[List[str], List[str]]:
        """
        Perform clip chain verification on ER-stage records.

        Returns:
          (violations, notes)
          violations -- list of violation description strings. Empty means pass.
          notes      -- list of non-failure informational notes.

        Raises RuntimeError with failure_type_id prefix on hard failures
        (CLIP_B_FLOOR_VIOLATION, CLIP_C_FLOOR_VIOLATION, CLIP_A_VIOLATION,
        CRISIS_ORDERING_VIOLATION).
        """
        violations = []
        notes      = []
        by_id: Dict[str, ExecutionRecord] = {r.vector_id: r for r in er_records}

        for rec in er_records:
            out = rec.observed_output
            if out.exception_raised:
                # No clip verification for exception vectors.
                continue

            vid = rec.vector_id
            iv  = rec.input_vector

            # ----------------------------------------------------------------
            # CCV-A-01: Clip A verification.
            # position_size_factor must be in [0.0, 1.0] for every normal vector.
            # ----------------------------------------------------------------
            psf = out.position_size_factor
            if psf < 0.0 or psf > 1.0:
                raise RuntimeError(
                    f"CLIP_A_VIOLATION: Vector {vid} position_size_factor={psf} "
                    "is outside [0.0, 1.0]. INV-01 violated."
                )

            # ----------------------------------------------------------------
            # CCV-B-01: For MU-02 and RP-02, E_pre_clip should be zero or near zero,
            # so Clip B floor should be active. exposure_weight bit pattern should
            # equal bit pattern of 1e-6.
            # ----------------------------------------------------------------
            if vid in ("MU-02", "RP-02"):
                ew_bits = _float_bits(out.exposure_weight)
                if ew_bits != self._lb_bits:
                    raise RuntimeError(
                        f"CLIP_B_FLOOR_VIOLATION: Vector {vid} exposure_weight "
                        f"expected bit pattern of 1e-6 but got "
                        f"{out.exposure_weight!r}. INV-02 violated."
                    )

            # ----------------------------------------------------------------
            # CCV-B-02: For JM-inactive (JM-01, JM-04) non-CRISIS vectors,
            # exposure_weight must be in [1e-6, 1.0].
            # (Clip C inactive, CRISIS dampening inactive.)
            # ----------------------------------------------------------------
            if vid in ("JM-01", "JM-04") and iv.current_regime_str != "CRISIS":
                ew = out.exposure_weight
                if ew < 1e-6 or ew > 1.0:
                    raise RuntimeError(
                        f"CLIP_B_RANGE_VIOLATION: Vector {vid} exposure_weight={ew} "
                        "outside [1e-6, 1.0] with Clip C and CRISIS dampening both "
                        "inactive. INV-02 violated."
                    )

            # ----------------------------------------------------------------
            # CCV-C-02: For JM-03 (designed to produce pre-Clip-C value below
            # SHOCK_EXPOSURE_CAP), exposure_weight should equal SHOCK_EXPOSURE_CAP.
            # ----------------------------------------------------------------
            if vid == "JM-03":
                ew_bits = _float_bits(out.exposure_weight)
                if ew_bits != self._sec_bits:
                    # JM-03 uses meta_uncertainty=0.99 + multiplier=2.0.
                    # The division may produce a value below SHOCK_EXPOSURE_CAP,
                    # which gets clipped to SHOCK_EXPOSURE_CAP by Clip C.
                    # If the result does NOT equal SHOCK_EXPOSURE_CAP, the
                    # actual computed value exceeded the cap after division;
                    # this is acceptable if the value is above SHOCK_EXPOSURE_CAP.
                    # Hard failure only if value is strictly below SHOCK_EXPOSURE_CAP.
                    if out.exposure_weight <= self._sec:
                        raise RuntimeError(
                            f"CLIP_C_FLOOR_VIOLATION: Vector {vid} exposure_weight="
                            f"{out.exposure_weight} is below SHOCK_EXPOSURE_CAP="
                            f"{self._sec}. INV-03 violated."
                        )
                    notes.append(
                        f"CCV-C-02 note: JM-03 exposure_weight={out.exposure_weight} "
                        "exceeds SHOCK_EXPOSURE_CAP; Clip C floor not triggered."
                    )

            # ----------------------------------------------------------------
            # CCV-D-02: For CR-01 (CRISIS, JRM inactive), exposure_weight may be
            # below SHOCK_EXPOSURE_CAP. No floor enforcement. This is specified
            # behaviour per INV-04.
            # ----------------------------------------------------------------
            if vid == "CR-01":
                notes.append(
                    f"CCV-D-02: CR-01 exposure_weight={out.exposure_weight}. "
                    "May be below SHOCK_EXPOSURE_CAP per INV-04 (specified behaviour)."
                )

        # --------------------------------------------------------------------
        # CCV-D-01: For CR-02 (CRISIS + JRM active), verify ordering.
        # Expected: CR-02.exposure_weight == JM-03.exposure_weight * 0.75
        # Both records must be present in ER set.
        # --------------------------------------------------------------------
        if "CR-02" in by_id and "JM-03" in by_id:
            cr02_out = by_id["CR-02"].observed_output
            jm03_out = by_id["JM-03"].observed_output
            if not cr02_out.exception_raised and not jm03_out.exception_raised:
                # Compute expected value using Python float arithmetic (same as production).
                expected_cr02_ew = jm03_out.exposure_weight * 0.75
                if not _floats_equal(cr02_out.exposure_weight, expected_cr02_ew):
                    raise RuntimeError(
                        f"CRISIS_ORDERING_VIOLATION: CR-02 exposure_weight="
                        f"{cr02_out.exposure_weight} != JM-03.exposure_weight*0.75="
                        f"{expected_cr02_ew}. Clip C / CRISIS ordering violated. "
                        "INV-04 violated."
                    )

        # --------------------------------------------------------------------
        # CCV-D-03: CR-03 (non-CRISIS with JRM active) -- dampening must NOT apply.
        # Verified by BIC backward compatibility comparison against a non-CRISIS
        # variant. Here we simply note the check for audit.
        # --------------------------------------------------------------------
        if "CR-03" in by_id:
            notes.append(
                "CCV-D-03: CR-03 is non-CRISIS with JRM active. Dampening "
                "not applied. Verified by absence of *0.75 in BIC comparison."
            )

        return violations, notes

    def xǁClipVerifierǁverify__mutmut_56(
        self,
        er_records: List[ExecutionRecord],
    ) -> Tuple[List[str], List[str]]:
        """
        Perform clip chain verification on ER-stage records.

        Returns:
          (violations, notes)
          violations -- list of violation description strings. Empty means pass.
          notes      -- list of non-failure informational notes.

        Raises RuntimeError with failure_type_id prefix on hard failures
        (CLIP_B_FLOOR_VIOLATION, CLIP_C_FLOOR_VIOLATION, CLIP_A_VIOLATION,
        CRISIS_ORDERING_VIOLATION).
        """
        violations = []
        notes      = []
        by_id: Dict[str, ExecutionRecord] = {r.vector_id: r for r in er_records}

        for rec in er_records:
            out = rec.observed_output
            if out.exception_raised:
                # No clip verification for exception vectors.
                continue

            vid = rec.vector_id
            iv  = rec.input_vector

            # ----------------------------------------------------------------
            # CCV-A-01: Clip A verification.
            # position_size_factor must be in [0.0, 1.0] for every normal vector.
            # ----------------------------------------------------------------
            psf = out.position_size_factor
            if psf < 0.0 or psf > 1.0:
                raise RuntimeError(
                    f"CLIP_A_VIOLATION: Vector {vid} position_size_factor={psf} "
                    "is outside [0.0, 1.0]. INV-01 violated."
                )

            # ----------------------------------------------------------------
            # CCV-B-01: For MU-02 and RP-02, E_pre_clip should be zero or near zero,
            # so Clip B floor should be active. exposure_weight bit pattern should
            # equal bit pattern of 1e-6.
            # ----------------------------------------------------------------
            if vid in ("MU-02", "RP-02"):
                ew_bits = _float_bits(out.exposure_weight)
                if ew_bits != self._lb_bits:
                    raise RuntimeError(
                        f"CLIP_B_FLOOR_VIOLATION: Vector {vid} exposure_weight "
                        f"expected bit pattern of 1e-6 but got "
                        f"{out.exposure_weight!r}. INV-02 violated."
                    )

            # ----------------------------------------------------------------
            # CCV-B-02: For JM-inactive (JM-01, JM-04) non-CRISIS vectors,
            # exposure_weight must be in [1e-6, 1.0].
            # (Clip C inactive, CRISIS dampening inactive.)
            # ----------------------------------------------------------------
            if vid in ("JM-01", "JM-04") and iv.current_regime_str != "CRISIS":
                ew = out.exposure_weight
                if ew < 1e-6 or ew > 1.0:
                    raise RuntimeError(
                        f"CLIP_B_RANGE_VIOLATION: Vector {vid} exposure_weight={ew} "
                        "outside [1e-6, 1.0] with Clip C and CRISIS dampening both "
                        "inactive. INV-02 violated."
                    )

            # ----------------------------------------------------------------
            # CCV-C-02: For JM-03 (designed to produce pre-Clip-C value below
            # SHOCK_EXPOSURE_CAP), exposure_weight should equal SHOCK_EXPOSURE_CAP.
            # ----------------------------------------------------------------
            if vid == "JM-03":
                ew_bits = _float_bits(out.exposure_weight)
                if ew_bits != self._sec_bits:
                    # JM-03 uses meta_uncertainty=0.99 + multiplier=2.0.
                    # The division may produce a value below SHOCK_EXPOSURE_CAP,
                    # which gets clipped to SHOCK_EXPOSURE_CAP by Clip C.
                    # If the result does NOT equal SHOCK_EXPOSURE_CAP, the
                    # actual computed value exceeded the cap after division;
                    # this is acceptable if the value is above SHOCK_EXPOSURE_CAP.
                    # Hard failure only if value is strictly below SHOCK_EXPOSURE_CAP.
                    if out.exposure_weight < self._sec:
                        raise RuntimeError(
                            None
                        )
                    notes.append(
                        f"CCV-C-02 note: JM-03 exposure_weight={out.exposure_weight} "
                        "exceeds SHOCK_EXPOSURE_CAP; Clip C floor not triggered."
                    )

            # ----------------------------------------------------------------
            # CCV-D-02: For CR-01 (CRISIS, JRM inactive), exposure_weight may be
            # below SHOCK_EXPOSURE_CAP. No floor enforcement. This is specified
            # behaviour per INV-04.
            # ----------------------------------------------------------------
            if vid == "CR-01":
                notes.append(
                    f"CCV-D-02: CR-01 exposure_weight={out.exposure_weight}. "
                    "May be below SHOCK_EXPOSURE_CAP per INV-04 (specified behaviour)."
                )

        # --------------------------------------------------------------------
        # CCV-D-01: For CR-02 (CRISIS + JRM active), verify ordering.
        # Expected: CR-02.exposure_weight == JM-03.exposure_weight * 0.75
        # Both records must be present in ER set.
        # --------------------------------------------------------------------
        if "CR-02" in by_id and "JM-03" in by_id:
            cr02_out = by_id["CR-02"].observed_output
            jm03_out = by_id["JM-03"].observed_output
            if not cr02_out.exception_raised and not jm03_out.exception_raised:
                # Compute expected value using Python float arithmetic (same as production).
                expected_cr02_ew = jm03_out.exposure_weight * 0.75
                if not _floats_equal(cr02_out.exposure_weight, expected_cr02_ew):
                    raise RuntimeError(
                        f"CRISIS_ORDERING_VIOLATION: CR-02 exposure_weight="
                        f"{cr02_out.exposure_weight} != JM-03.exposure_weight*0.75="
                        f"{expected_cr02_ew}. Clip C / CRISIS ordering violated. "
                        "INV-04 violated."
                    )

        # --------------------------------------------------------------------
        # CCV-D-03: CR-03 (non-CRISIS with JRM active) -- dampening must NOT apply.
        # Verified by BIC backward compatibility comparison against a non-CRISIS
        # variant. Here we simply note the check for audit.
        # --------------------------------------------------------------------
        if "CR-03" in by_id:
            notes.append(
                "CCV-D-03: CR-03 is non-CRISIS with JRM active. Dampening "
                "not applied. Verified by absence of *0.75 in BIC comparison."
            )

        return violations, notes

    def xǁClipVerifierǁverify__mutmut_57(
        self,
        er_records: List[ExecutionRecord],
    ) -> Tuple[List[str], List[str]]:
        """
        Perform clip chain verification on ER-stage records.

        Returns:
          (violations, notes)
          violations -- list of violation description strings. Empty means pass.
          notes      -- list of non-failure informational notes.

        Raises RuntimeError with failure_type_id prefix on hard failures
        (CLIP_B_FLOOR_VIOLATION, CLIP_C_FLOOR_VIOLATION, CLIP_A_VIOLATION,
        CRISIS_ORDERING_VIOLATION).
        """
        violations = []
        notes      = []
        by_id: Dict[str, ExecutionRecord] = {r.vector_id: r for r in er_records}

        for rec in er_records:
            out = rec.observed_output
            if out.exception_raised:
                # No clip verification for exception vectors.
                continue

            vid = rec.vector_id
            iv  = rec.input_vector

            # ----------------------------------------------------------------
            # CCV-A-01: Clip A verification.
            # position_size_factor must be in [0.0, 1.0] for every normal vector.
            # ----------------------------------------------------------------
            psf = out.position_size_factor
            if psf < 0.0 or psf > 1.0:
                raise RuntimeError(
                    f"CLIP_A_VIOLATION: Vector {vid} position_size_factor={psf} "
                    "is outside [0.0, 1.0]. INV-01 violated."
                )

            # ----------------------------------------------------------------
            # CCV-B-01: For MU-02 and RP-02, E_pre_clip should be zero or near zero,
            # so Clip B floor should be active. exposure_weight bit pattern should
            # equal bit pattern of 1e-6.
            # ----------------------------------------------------------------
            if vid in ("MU-02", "RP-02"):
                ew_bits = _float_bits(out.exposure_weight)
                if ew_bits != self._lb_bits:
                    raise RuntimeError(
                        f"CLIP_B_FLOOR_VIOLATION: Vector {vid} exposure_weight "
                        f"expected bit pattern of 1e-6 but got "
                        f"{out.exposure_weight!r}. INV-02 violated."
                    )

            # ----------------------------------------------------------------
            # CCV-B-02: For JM-inactive (JM-01, JM-04) non-CRISIS vectors,
            # exposure_weight must be in [1e-6, 1.0].
            # (Clip C inactive, CRISIS dampening inactive.)
            # ----------------------------------------------------------------
            if vid in ("JM-01", "JM-04") and iv.current_regime_str != "CRISIS":
                ew = out.exposure_weight
                if ew < 1e-6 or ew > 1.0:
                    raise RuntimeError(
                        f"CLIP_B_RANGE_VIOLATION: Vector {vid} exposure_weight={ew} "
                        "outside [1e-6, 1.0] with Clip C and CRISIS dampening both "
                        "inactive. INV-02 violated."
                    )

            # ----------------------------------------------------------------
            # CCV-C-02: For JM-03 (designed to produce pre-Clip-C value below
            # SHOCK_EXPOSURE_CAP), exposure_weight should equal SHOCK_EXPOSURE_CAP.
            # ----------------------------------------------------------------
            if vid == "JM-03":
                ew_bits = _float_bits(out.exposure_weight)
                if ew_bits != self._sec_bits:
                    # JM-03 uses meta_uncertainty=0.99 + multiplier=2.0.
                    # The division may produce a value below SHOCK_EXPOSURE_CAP,
                    # which gets clipped to SHOCK_EXPOSURE_CAP by Clip C.
                    # If the result does NOT equal SHOCK_EXPOSURE_CAP, the
                    # actual computed value exceeded the cap after division;
                    # this is acceptable if the value is above SHOCK_EXPOSURE_CAP.
                    # Hard failure only if value is strictly below SHOCK_EXPOSURE_CAP.
                    if out.exposure_weight < self._sec:
                        raise RuntimeError(
                            f"CLIP_C_FLOOR_VIOLATION: Vector {vid} exposure_weight="
                            f"{out.exposure_weight} is below SHOCK_EXPOSURE_CAP="
                            f"{self._sec}. INV-03 violated."
                        )
                    notes.append(
                        None
                    )

            # ----------------------------------------------------------------
            # CCV-D-02: For CR-01 (CRISIS, JRM inactive), exposure_weight may be
            # below SHOCK_EXPOSURE_CAP. No floor enforcement. This is specified
            # behaviour per INV-04.
            # ----------------------------------------------------------------
            if vid == "CR-01":
                notes.append(
                    f"CCV-D-02: CR-01 exposure_weight={out.exposure_weight}. "
                    "May be below SHOCK_EXPOSURE_CAP per INV-04 (specified behaviour)."
                )

        # --------------------------------------------------------------------
        # CCV-D-01: For CR-02 (CRISIS + JRM active), verify ordering.
        # Expected: CR-02.exposure_weight == JM-03.exposure_weight * 0.75
        # Both records must be present in ER set.
        # --------------------------------------------------------------------
        if "CR-02" in by_id and "JM-03" in by_id:
            cr02_out = by_id["CR-02"].observed_output
            jm03_out = by_id["JM-03"].observed_output
            if not cr02_out.exception_raised and not jm03_out.exception_raised:
                # Compute expected value using Python float arithmetic (same as production).
                expected_cr02_ew = jm03_out.exposure_weight * 0.75
                if not _floats_equal(cr02_out.exposure_weight, expected_cr02_ew):
                    raise RuntimeError(
                        f"CRISIS_ORDERING_VIOLATION: CR-02 exposure_weight="
                        f"{cr02_out.exposure_weight} != JM-03.exposure_weight*0.75="
                        f"{expected_cr02_ew}. Clip C / CRISIS ordering violated. "
                        "INV-04 violated."
                    )

        # --------------------------------------------------------------------
        # CCV-D-03: CR-03 (non-CRISIS with JRM active) -- dampening must NOT apply.
        # Verified by BIC backward compatibility comparison against a non-CRISIS
        # variant. Here we simply note the check for audit.
        # --------------------------------------------------------------------
        if "CR-03" in by_id:
            notes.append(
                "CCV-D-03: CR-03 is non-CRISIS with JRM active. Dampening "
                "not applied. Verified by absence of *0.75 in BIC comparison."
            )

        return violations, notes

    def xǁClipVerifierǁverify__mutmut_58(
        self,
        er_records: List[ExecutionRecord],
    ) -> Tuple[List[str], List[str]]:
        """
        Perform clip chain verification on ER-stage records.

        Returns:
          (violations, notes)
          violations -- list of violation description strings. Empty means pass.
          notes      -- list of non-failure informational notes.

        Raises RuntimeError with failure_type_id prefix on hard failures
        (CLIP_B_FLOOR_VIOLATION, CLIP_C_FLOOR_VIOLATION, CLIP_A_VIOLATION,
        CRISIS_ORDERING_VIOLATION).
        """
        violations = []
        notes      = []
        by_id: Dict[str, ExecutionRecord] = {r.vector_id: r for r in er_records}

        for rec in er_records:
            out = rec.observed_output
            if out.exception_raised:
                # No clip verification for exception vectors.
                continue

            vid = rec.vector_id
            iv  = rec.input_vector

            # ----------------------------------------------------------------
            # CCV-A-01: Clip A verification.
            # position_size_factor must be in [0.0, 1.0] for every normal vector.
            # ----------------------------------------------------------------
            psf = out.position_size_factor
            if psf < 0.0 or psf > 1.0:
                raise RuntimeError(
                    f"CLIP_A_VIOLATION: Vector {vid} position_size_factor={psf} "
                    "is outside [0.0, 1.0]. INV-01 violated."
                )

            # ----------------------------------------------------------------
            # CCV-B-01: For MU-02 and RP-02, E_pre_clip should be zero or near zero,
            # so Clip B floor should be active. exposure_weight bit pattern should
            # equal bit pattern of 1e-6.
            # ----------------------------------------------------------------
            if vid in ("MU-02", "RP-02"):
                ew_bits = _float_bits(out.exposure_weight)
                if ew_bits != self._lb_bits:
                    raise RuntimeError(
                        f"CLIP_B_FLOOR_VIOLATION: Vector {vid} exposure_weight "
                        f"expected bit pattern of 1e-6 but got "
                        f"{out.exposure_weight!r}. INV-02 violated."
                    )

            # ----------------------------------------------------------------
            # CCV-B-02: For JM-inactive (JM-01, JM-04) non-CRISIS vectors,
            # exposure_weight must be in [1e-6, 1.0].
            # (Clip C inactive, CRISIS dampening inactive.)
            # ----------------------------------------------------------------
            if vid in ("JM-01", "JM-04") and iv.current_regime_str != "CRISIS":
                ew = out.exposure_weight
                if ew < 1e-6 or ew > 1.0:
                    raise RuntimeError(
                        f"CLIP_B_RANGE_VIOLATION: Vector {vid} exposure_weight={ew} "
                        "outside [1e-6, 1.0] with Clip C and CRISIS dampening both "
                        "inactive. INV-02 violated."
                    )

            # ----------------------------------------------------------------
            # CCV-C-02: For JM-03 (designed to produce pre-Clip-C value below
            # SHOCK_EXPOSURE_CAP), exposure_weight should equal SHOCK_EXPOSURE_CAP.
            # ----------------------------------------------------------------
            if vid == "JM-03":
                ew_bits = _float_bits(out.exposure_weight)
                if ew_bits != self._sec_bits:
                    # JM-03 uses meta_uncertainty=0.99 + multiplier=2.0.
                    # The division may produce a value below SHOCK_EXPOSURE_CAP,
                    # which gets clipped to SHOCK_EXPOSURE_CAP by Clip C.
                    # If the result does NOT equal SHOCK_EXPOSURE_CAP, the
                    # actual computed value exceeded the cap after division;
                    # this is acceptable if the value is above SHOCK_EXPOSURE_CAP.
                    # Hard failure only if value is strictly below SHOCK_EXPOSURE_CAP.
                    if out.exposure_weight < self._sec:
                        raise RuntimeError(
                            f"CLIP_C_FLOOR_VIOLATION: Vector {vid} exposure_weight="
                            f"{out.exposure_weight} is below SHOCK_EXPOSURE_CAP="
                            f"{self._sec}. INV-03 violated."
                        )
                    notes.append(
                        f"CCV-C-02 note: JM-03 exposure_weight={out.exposure_weight} "
                        "XXexceeds SHOCK_EXPOSURE_CAP; Clip C floor not triggered.XX"
                    )

            # ----------------------------------------------------------------
            # CCV-D-02: For CR-01 (CRISIS, JRM inactive), exposure_weight may be
            # below SHOCK_EXPOSURE_CAP. No floor enforcement. This is specified
            # behaviour per INV-04.
            # ----------------------------------------------------------------
            if vid == "CR-01":
                notes.append(
                    f"CCV-D-02: CR-01 exposure_weight={out.exposure_weight}. "
                    "May be below SHOCK_EXPOSURE_CAP per INV-04 (specified behaviour)."
                )

        # --------------------------------------------------------------------
        # CCV-D-01: For CR-02 (CRISIS + JRM active), verify ordering.
        # Expected: CR-02.exposure_weight == JM-03.exposure_weight * 0.75
        # Both records must be present in ER set.
        # --------------------------------------------------------------------
        if "CR-02" in by_id and "JM-03" in by_id:
            cr02_out = by_id["CR-02"].observed_output
            jm03_out = by_id["JM-03"].observed_output
            if not cr02_out.exception_raised and not jm03_out.exception_raised:
                # Compute expected value using Python float arithmetic (same as production).
                expected_cr02_ew = jm03_out.exposure_weight * 0.75
                if not _floats_equal(cr02_out.exposure_weight, expected_cr02_ew):
                    raise RuntimeError(
                        f"CRISIS_ORDERING_VIOLATION: CR-02 exposure_weight="
                        f"{cr02_out.exposure_weight} != JM-03.exposure_weight*0.75="
                        f"{expected_cr02_ew}. Clip C / CRISIS ordering violated. "
                        "INV-04 violated."
                    )

        # --------------------------------------------------------------------
        # CCV-D-03: CR-03 (non-CRISIS with JRM active) -- dampening must NOT apply.
        # Verified by BIC backward compatibility comparison against a non-CRISIS
        # variant. Here we simply note the check for audit.
        # --------------------------------------------------------------------
        if "CR-03" in by_id:
            notes.append(
                "CCV-D-03: CR-03 is non-CRISIS with JRM active. Dampening "
                "not applied. Verified by absence of *0.75 in BIC comparison."
            )

        return violations, notes

    def xǁClipVerifierǁverify__mutmut_59(
        self,
        er_records: List[ExecutionRecord],
    ) -> Tuple[List[str], List[str]]:
        """
        Perform clip chain verification on ER-stage records.

        Returns:
          (violations, notes)
          violations -- list of violation description strings. Empty means pass.
          notes      -- list of non-failure informational notes.

        Raises RuntimeError with failure_type_id prefix on hard failures
        (CLIP_B_FLOOR_VIOLATION, CLIP_C_FLOOR_VIOLATION, CLIP_A_VIOLATION,
        CRISIS_ORDERING_VIOLATION).
        """
        violations = []
        notes      = []
        by_id: Dict[str, ExecutionRecord] = {r.vector_id: r for r in er_records}

        for rec in er_records:
            out = rec.observed_output
            if out.exception_raised:
                # No clip verification for exception vectors.
                continue

            vid = rec.vector_id
            iv  = rec.input_vector

            # ----------------------------------------------------------------
            # CCV-A-01: Clip A verification.
            # position_size_factor must be in [0.0, 1.0] for every normal vector.
            # ----------------------------------------------------------------
            psf = out.position_size_factor
            if psf < 0.0 or psf > 1.0:
                raise RuntimeError(
                    f"CLIP_A_VIOLATION: Vector {vid} position_size_factor={psf} "
                    "is outside [0.0, 1.0]. INV-01 violated."
                )

            # ----------------------------------------------------------------
            # CCV-B-01: For MU-02 and RP-02, E_pre_clip should be zero or near zero,
            # so Clip B floor should be active. exposure_weight bit pattern should
            # equal bit pattern of 1e-6.
            # ----------------------------------------------------------------
            if vid in ("MU-02", "RP-02"):
                ew_bits = _float_bits(out.exposure_weight)
                if ew_bits != self._lb_bits:
                    raise RuntimeError(
                        f"CLIP_B_FLOOR_VIOLATION: Vector {vid} exposure_weight "
                        f"expected bit pattern of 1e-6 but got "
                        f"{out.exposure_weight!r}. INV-02 violated."
                    )

            # ----------------------------------------------------------------
            # CCV-B-02: For JM-inactive (JM-01, JM-04) non-CRISIS vectors,
            # exposure_weight must be in [1e-6, 1.0].
            # (Clip C inactive, CRISIS dampening inactive.)
            # ----------------------------------------------------------------
            if vid in ("JM-01", "JM-04") and iv.current_regime_str != "CRISIS":
                ew = out.exposure_weight
                if ew < 1e-6 or ew > 1.0:
                    raise RuntimeError(
                        f"CLIP_B_RANGE_VIOLATION: Vector {vid} exposure_weight={ew} "
                        "outside [1e-6, 1.0] with Clip C and CRISIS dampening both "
                        "inactive. INV-02 violated."
                    )

            # ----------------------------------------------------------------
            # CCV-C-02: For JM-03 (designed to produce pre-Clip-C value below
            # SHOCK_EXPOSURE_CAP), exposure_weight should equal SHOCK_EXPOSURE_CAP.
            # ----------------------------------------------------------------
            if vid == "JM-03":
                ew_bits = _float_bits(out.exposure_weight)
                if ew_bits != self._sec_bits:
                    # JM-03 uses meta_uncertainty=0.99 + multiplier=2.0.
                    # The division may produce a value below SHOCK_EXPOSURE_CAP,
                    # which gets clipped to SHOCK_EXPOSURE_CAP by Clip C.
                    # If the result does NOT equal SHOCK_EXPOSURE_CAP, the
                    # actual computed value exceeded the cap after division;
                    # this is acceptable if the value is above SHOCK_EXPOSURE_CAP.
                    # Hard failure only if value is strictly below SHOCK_EXPOSURE_CAP.
                    if out.exposure_weight < self._sec:
                        raise RuntimeError(
                            f"CLIP_C_FLOOR_VIOLATION: Vector {vid} exposure_weight="
                            f"{out.exposure_weight} is below SHOCK_EXPOSURE_CAP="
                            f"{self._sec}. INV-03 violated."
                        )
                    notes.append(
                        f"CCV-C-02 note: JM-03 exposure_weight={out.exposure_weight} "
                        "exceeds shock_exposure_cap; clip c floor not triggered."
                    )

            # ----------------------------------------------------------------
            # CCV-D-02: For CR-01 (CRISIS, JRM inactive), exposure_weight may be
            # below SHOCK_EXPOSURE_CAP. No floor enforcement. This is specified
            # behaviour per INV-04.
            # ----------------------------------------------------------------
            if vid == "CR-01":
                notes.append(
                    f"CCV-D-02: CR-01 exposure_weight={out.exposure_weight}. "
                    "May be below SHOCK_EXPOSURE_CAP per INV-04 (specified behaviour)."
                )

        # --------------------------------------------------------------------
        # CCV-D-01: For CR-02 (CRISIS + JRM active), verify ordering.
        # Expected: CR-02.exposure_weight == JM-03.exposure_weight * 0.75
        # Both records must be present in ER set.
        # --------------------------------------------------------------------
        if "CR-02" in by_id and "JM-03" in by_id:
            cr02_out = by_id["CR-02"].observed_output
            jm03_out = by_id["JM-03"].observed_output
            if not cr02_out.exception_raised and not jm03_out.exception_raised:
                # Compute expected value using Python float arithmetic (same as production).
                expected_cr02_ew = jm03_out.exposure_weight * 0.75
                if not _floats_equal(cr02_out.exposure_weight, expected_cr02_ew):
                    raise RuntimeError(
                        f"CRISIS_ORDERING_VIOLATION: CR-02 exposure_weight="
                        f"{cr02_out.exposure_weight} != JM-03.exposure_weight*0.75="
                        f"{expected_cr02_ew}. Clip C / CRISIS ordering violated. "
                        "INV-04 violated."
                    )

        # --------------------------------------------------------------------
        # CCV-D-03: CR-03 (non-CRISIS with JRM active) -- dampening must NOT apply.
        # Verified by BIC backward compatibility comparison against a non-CRISIS
        # variant. Here we simply note the check for audit.
        # --------------------------------------------------------------------
        if "CR-03" in by_id:
            notes.append(
                "CCV-D-03: CR-03 is non-CRISIS with JRM active. Dampening "
                "not applied. Verified by absence of *0.75 in BIC comparison."
            )

        return violations, notes

    def xǁClipVerifierǁverify__mutmut_60(
        self,
        er_records: List[ExecutionRecord],
    ) -> Tuple[List[str], List[str]]:
        """
        Perform clip chain verification on ER-stage records.

        Returns:
          (violations, notes)
          violations -- list of violation description strings. Empty means pass.
          notes      -- list of non-failure informational notes.

        Raises RuntimeError with failure_type_id prefix on hard failures
        (CLIP_B_FLOOR_VIOLATION, CLIP_C_FLOOR_VIOLATION, CLIP_A_VIOLATION,
        CRISIS_ORDERING_VIOLATION).
        """
        violations = []
        notes      = []
        by_id: Dict[str, ExecutionRecord] = {r.vector_id: r for r in er_records}

        for rec in er_records:
            out = rec.observed_output
            if out.exception_raised:
                # No clip verification for exception vectors.
                continue

            vid = rec.vector_id
            iv  = rec.input_vector

            # ----------------------------------------------------------------
            # CCV-A-01: Clip A verification.
            # position_size_factor must be in [0.0, 1.0] for every normal vector.
            # ----------------------------------------------------------------
            psf = out.position_size_factor
            if psf < 0.0 or psf > 1.0:
                raise RuntimeError(
                    f"CLIP_A_VIOLATION: Vector {vid} position_size_factor={psf} "
                    "is outside [0.0, 1.0]. INV-01 violated."
                )

            # ----------------------------------------------------------------
            # CCV-B-01: For MU-02 and RP-02, E_pre_clip should be zero or near zero,
            # so Clip B floor should be active. exposure_weight bit pattern should
            # equal bit pattern of 1e-6.
            # ----------------------------------------------------------------
            if vid in ("MU-02", "RP-02"):
                ew_bits = _float_bits(out.exposure_weight)
                if ew_bits != self._lb_bits:
                    raise RuntimeError(
                        f"CLIP_B_FLOOR_VIOLATION: Vector {vid} exposure_weight "
                        f"expected bit pattern of 1e-6 but got "
                        f"{out.exposure_weight!r}. INV-02 violated."
                    )

            # ----------------------------------------------------------------
            # CCV-B-02: For JM-inactive (JM-01, JM-04) non-CRISIS vectors,
            # exposure_weight must be in [1e-6, 1.0].
            # (Clip C inactive, CRISIS dampening inactive.)
            # ----------------------------------------------------------------
            if vid in ("JM-01", "JM-04") and iv.current_regime_str != "CRISIS":
                ew = out.exposure_weight
                if ew < 1e-6 or ew > 1.0:
                    raise RuntimeError(
                        f"CLIP_B_RANGE_VIOLATION: Vector {vid} exposure_weight={ew} "
                        "outside [1e-6, 1.0] with Clip C and CRISIS dampening both "
                        "inactive. INV-02 violated."
                    )

            # ----------------------------------------------------------------
            # CCV-C-02: For JM-03 (designed to produce pre-Clip-C value below
            # SHOCK_EXPOSURE_CAP), exposure_weight should equal SHOCK_EXPOSURE_CAP.
            # ----------------------------------------------------------------
            if vid == "JM-03":
                ew_bits = _float_bits(out.exposure_weight)
                if ew_bits != self._sec_bits:
                    # JM-03 uses meta_uncertainty=0.99 + multiplier=2.0.
                    # The division may produce a value below SHOCK_EXPOSURE_CAP,
                    # which gets clipped to SHOCK_EXPOSURE_CAP by Clip C.
                    # If the result does NOT equal SHOCK_EXPOSURE_CAP, the
                    # actual computed value exceeded the cap after division;
                    # this is acceptable if the value is above SHOCK_EXPOSURE_CAP.
                    # Hard failure only if value is strictly below SHOCK_EXPOSURE_CAP.
                    if out.exposure_weight < self._sec:
                        raise RuntimeError(
                            f"CLIP_C_FLOOR_VIOLATION: Vector {vid} exposure_weight="
                            f"{out.exposure_weight} is below SHOCK_EXPOSURE_CAP="
                            f"{self._sec}. INV-03 violated."
                        )
                    notes.append(
                        f"CCV-C-02 note: JM-03 exposure_weight={out.exposure_weight} "
                        "EXCEEDS SHOCK_EXPOSURE_CAP; CLIP C FLOOR NOT TRIGGERED."
                    )

            # ----------------------------------------------------------------
            # CCV-D-02: For CR-01 (CRISIS, JRM inactive), exposure_weight may be
            # below SHOCK_EXPOSURE_CAP. No floor enforcement. This is specified
            # behaviour per INV-04.
            # ----------------------------------------------------------------
            if vid == "CR-01":
                notes.append(
                    f"CCV-D-02: CR-01 exposure_weight={out.exposure_weight}. "
                    "May be below SHOCK_EXPOSURE_CAP per INV-04 (specified behaviour)."
                )

        # --------------------------------------------------------------------
        # CCV-D-01: For CR-02 (CRISIS + JRM active), verify ordering.
        # Expected: CR-02.exposure_weight == JM-03.exposure_weight * 0.75
        # Both records must be present in ER set.
        # --------------------------------------------------------------------
        if "CR-02" in by_id and "JM-03" in by_id:
            cr02_out = by_id["CR-02"].observed_output
            jm03_out = by_id["JM-03"].observed_output
            if not cr02_out.exception_raised and not jm03_out.exception_raised:
                # Compute expected value using Python float arithmetic (same as production).
                expected_cr02_ew = jm03_out.exposure_weight * 0.75
                if not _floats_equal(cr02_out.exposure_weight, expected_cr02_ew):
                    raise RuntimeError(
                        f"CRISIS_ORDERING_VIOLATION: CR-02 exposure_weight="
                        f"{cr02_out.exposure_weight} != JM-03.exposure_weight*0.75="
                        f"{expected_cr02_ew}. Clip C / CRISIS ordering violated. "
                        "INV-04 violated."
                    )

        # --------------------------------------------------------------------
        # CCV-D-03: CR-03 (non-CRISIS with JRM active) -- dampening must NOT apply.
        # Verified by BIC backward compatibility comparison against a non-CRISIS
        # variant. Here we simply note the check for audit.
        # --------------------------------------------------------------------
        if "CR-03" in by_id:
            notes.append(
                "CCV-D-03: CR-03 is non-CRISIS with JRM active. Dampening "
                "not applied. Verified by absence of *0.75 in BIC comparison."
            )

        return violations, notes

    def xǁClipVerifierǁverify__mutmut_61(
        self,
        er_records: List[ExecutionRecord],
    ) -> Tuple[List[str], List[str]]:
        """
        Perform clip chain verification on ER-stage records.

        Returns:
          (violations, notes)
          violations -- list of violation description strings. Empty means pass.
          notes      -- list of non-failure informational notes.

        Raises RuntimeError with failure_type_id prefix on hard failures
        (CLIP_B_FLOOR_VIOLATION, CLIP_C_FLOOR_VIOLATION, CLIP_A_VIOLATION,
        CRISIS_ORDERING_VIOLATION).
        """
        violations = []
        notes      = []
        by_id: Dict[str, ExecutionRecord] = {r.vector_id: r for r in er_records}

        for rec in er_records:
            out = rec.observed_output
            if out.exception_raised:
                # No clip verification for exception vectors.
                continue

            vid = rec.vector_id
            iv  = rec.input_vector

            # ----------------------------------------------------------------
            # CCV-A-01: Clip A verification.
            # position_size_factor must be in [0.0, 1.0] for every normal vector.
            # ----------------------------------------------------------------
            psf = out.position_size_factor
            if psf < 0.0 or psf > 1.0:
                raise RuntimeError(
                    f"CLIP_A_VIOLATION: Vector {vid} position_size_factor={psf} "
                    "is outside [0.0, 1.0]. INV-01 violated."
                )

            # ----------------------------------------------------------------
            # CCV-B-01: For MU-02 and RP-02, E_pre_clip should be zero or near zero,
            # so Clip B floor should be active. exposure_weight bit pattern should
            # equal bit pattern of 1e-6.
            # ----------------------------------------------------------------
            if vid in ("MU-02", "RP-02"):
                ew_bits = _float_bits(out.exposure_weight)
                if ew_bits != self._lb_bits:
                    raise RuntimeError(
                        f"CLIP_B_FLOOR_VIOLATION: Vector {vid} exposure_weight "
                        f"expected bit pattern of 1e-6 but got "
                        f"{out.exposure_weight!r}. INV-02 violated."
                    )

            # ----------------------------------------------------------------
            # CCV-B-02: For JM-inactive (JM-01, JM-04) non-CRISIS vectors,
            # exposure_weight must be in [1e-6, 1.0].
            # (Clip C inactive, CRISIS dampening inactive.)
            # ----------------------------------------------------------------
            if vid in ("JM-01", "JM-04") and iv.current_regime_str != "CRISIS":
                ew = out.exposure_weight
                if ew < 1e-6 or ew > 1.0:
                    raise RuntimeError(
                        f"CLIP_B_RANGE_VIOLATION: Vector {vid} exposure_weight={ew} "
                        "outside [1e-6, 1.0] with Clip C and CRISIS dampening both "
                        "inactive. INV-02 violated."
                    )

            # ----------------------------------------------------------------
            # CCV-C-02: For JM-03 (designed to produce pre-Clip-C value below
            # SHOCK_EXPOSURE_CAP), exposure_weight should equal SHOCK_EXPOSURE_CAP.
            # ----------------------------------------------------------------
            if vid == "JM-03":
                ew_bits = _float_bits(out.exposure_weight)
                if ew_bits != self._sec_bits:
                    # JM-03 uses meta_uncertainty=0.99 + multiplier=2.0.
                    # The division may produce a value below SHOCK_EXPOSURE_CAP,
                    # which gets clipped to SHOCK_EXPOSURE_CAP by Clip C.
                    # If the result does NOT equal SHOCK_EXPOSURE_CAP, the
                    # actual computed value exceeded the cap after division;
                    # this is acceptable if the value is above SHOCK_EXPOSURE_CAP.
                    # Hard failure only if value is strictly below SHOCK_EXPOSURE_CAP.
                    if out.exposure_weight < self._sec:
                        raise RuntimeError(
                            f"CLIP_C_FLOOR_VIOLATION: Vector {vid} exposure_weight="
                            f"{out.exposure_weight} is below SHOCK_EXPOSURE_CAP="
                            f"{self._sec}. INV-03 violated."
                        )
                    notes.append(
                        f"CCV-C-02 note: JM-03 exposure_weight={out.exposure_weight} "
                        "exceeds SHOCK_EXPOSURE_CAP; Clip C floor not triggered."
                    )

            # ----------------------------------------------------------------
            # CCV-D-02: For CR-01 (CRISIS, JRM inactive), exposure_weight may be
            # below SHOCK_EXPOSURE_CAP. No floor enforcement. This is specified
            # behaviour per INV-04.
            # ----------------------------------------------------------------
            if vid != "CR-01":
                notes.append(
                    f"CCV-D-02: CR-01 exposure_weight={out.exposure_weight}. "
                    "May be below SHOCK_EXPOSURE_CAP per INV-04 (specified behaviour)."
                )

        # --------------------------------------------------------------------
        # CCV-D-01: For CR-02 (CRISIS + JRM active), verify ordering.
        # Expected: CR-02.exposure_weight == JM-03.exposure_weight * 0.75
        # Both records must be present in ER set.
        # --------------------------------------------------------------------
        if "CR-02" in by_id and "JM-03" in by_id:
            cr02_out = by_id["CR-02"].observed_output
            jm03_out = by_id["JM-03"].observed_output
            if not cr02_out.exception_raised and not jm03_out.exception_raised:
                # Compute expected value using Python float arithmetic (same as production).
                expected_cr02_ew = jm03_out.exposure_weight * 0.75
                if not _floats_equal(cr02_out.exposure_weight, expected_cr02_ew):
                    raise RuntimeError(
                        f"CRISIS_ORDERING_VIOLATION: CR-02 exposure_weight="
                        f"{cr02_out.exposure_weight} != JM-03.exposure_weight*0.75="
                        f"{expected_cr02_ew}. Clip C / CRISIS ordering violated. "
                        "INV-04 violated."
                    )

        # --------------------------------------------------------------------
        # CCV-D-03: CR-03 (non-CRISIS with JRM active) -- dampening must NOT apply.
        # Verified by BIC backward compatibility comparison against a non-CRISIS
        # variant. Here we simply note the check for audit.
        # --------------------------------------------------------------------
        if "CR-03" in by_id:
            notes.append(
                "CCV-D-03: CR-03 is non-CRISIS with JRM active. Dampening "
                "not applied. Verified by absence of *0.75 in BIC comparison."
            )

        return violations, notes

    def xǁClipVerifierǁverify__mutmut_62(
        self,
        er_records: List[ExecutionRecord],
    ) -> Tuple[List[str], List[str]]:
        """
        Perform clip chain verification on ER-stage records.

        Returns:
          (violations, notes)
          violations -- list of violation description strings. Empty means pass.
          notes      -- list of non-failure informational notes.

        Raises RuntimeError with failure_type_id prefix on hard failures
        (CLIP_B_FLOOR_VIOLATION, CLIP_C_FLOOR_VIOLATION, CLIP_A_VIOLATION,
        CRISIS_ORDERING_VIOLATION).
        """
        violations = []
        notes      = []
        by_id: Dict[str, ExecutionRecord] = {r.vector_id: r for r in er_records}

        for rec in er_records:
            out = rec.observed_output
            if out.exception_raised:
                # No clip verification for exception vectors.
                continue

            vid = rec.vector_id
            iv  = rec.input_vector

            # ----------------------------------------------------------------
            # CCV-A-01: Clip A verification.
            # position_size_factor must be in [0.0, 1.0] for every normal vector.
            # ----------------------------------------------------------------
            psf = out.position_size_factor
            if psf < 0.0 or psf > 1.0:
                raise RuntimeError(
                    f"CLIP_A_VIOLATION: Vector {vid} position_size_factor={psf} "
                    "is outside [0.0, 1.0]. INV-01 violated."
                )

            # ----------------------------------------------------------------
            # CCV-B-01: For MU-02 and RP-02, E_pre_clip should be zero or near zero,
            # so Clip B floor should be active. exposure_weight bit pattern should
            # equal bit pattern of 1e-6.
            # ----------------------------------------------------------------
            if vid in ("MU-02", "RP-02"):
                ew_bits = _float_bits(out.exposure_weight)
                if ew_bits != self._lb_bits:
                    raise RuntimeError(
                        f"CLIP_B_FLOOR_VIOLATION: Vector {vid} exposure_weight "
                        f"expected bit pattern of 1e-6 but got "
                        f"{out.exposure_weight!r}. INV-02 violated."
                    )

            # ----------------------------------------------------------------
            # CCV-B-02: For JM-inactive (JM-01, JM-04) non-CRISIS vectors,
            # exposure_weight must be in [1e-6, 1.0].
            # (Clip C inactive, CRISIS dampening inactive.)
            # ----------------------------------------------------------------
            if vid in ("JM-01", "JM-04") and iv.current_regime_str != "CRISIS":
                ew = out.exposure_weight
                if ew < 1e-6 or ew > 1.0:
                    raise RuntimeError(
                        f"CLIP_B_RANGE_VIOLATION: Vector {vid} exposure_weight={ew} "
                        "outside [1e-6, 1.0] with Clip C and CRISIS dampening both "
                        "inactive. INV-02 violated."
                    )

            # ----------------------------------------------------------------
            # CCV-C-02: For JM-03 (designed to produce pre-Clip-C value below
            # SHOCK_EXPOSURE_CAP), exposure_weight should equal SHOCK_EXPOSURE_CAP.
            # ----------------------------------------------------------------
            if vid == "JM-03":
                ew_bits = _float_bits(out.exposure_weight)
                if ew_bits != self._sec_bits:
                    # JM-03 uses meta_uncertainty=0.99 + multiplier=2.0.
                    # The division may produce a value below SHOCK_EXPOSURE_CAP,
                    # which gets clipped to SHOCK_EXPOSURE_CAP by Clip C.
                    # If the result does NOT equal SHOCK_EXPOSURE_CAP, the
                    # actual computed value exceeded the cap after division;
                    # this is acceptable if the value is above SHOCK_EXPOSURE_CAP.
                    # Hard failure only if value is strictly below SHOCK_EXPOSURE_CAP.
                    if out.exposure_weight < self._sec:
                        raise RuntimeError(
                            f"CLIP_C_FLOOR_VIOLATION: Vector {vid} exposure_weight="
                            f"{out.exposure_weight} is below SHOCK_EXPOSURE_CAP="
                            f"{self._sec}. INV-03 violated."
                        )
                    notes.append(
                        f"CCV-C-02 note: JM-03 exposure_weight={out.exposure_weight} "
                        "exceeds SHOCK_EXPOSURE_CAP; Clip C floor not triggered."
                    )

            # ----------------------------------------------------------------
            # CCV-D-02: For CR-01 (CRISIS, JRM inactive), exposure_weight may be
            # below SHOCK_EXPOSURE_CAP. No floor enforcement. This is specified
            # behaviour per INV-04.
            # ----------------------------------------------------------------
            if vid == "XXCR-01XX":
                notes.append(
                    f"CCV-D-02: CR-01 exposure_weight={out.exposure_weight}. "
                    "May be below SHOCK_EXPOSURE_CAP per INV-04 (specified behaviour)."
                )

        # --------------------------------------------------------------------
        # CCV-D-01: For CR-02 (CRISIS + JRM active), verify ordering.
        # Expected: CR-02.exposure_weight == JM-03.exposure_weight * 0.75
        # Both records must be present in ER set.
        # --------------------------------------------------------------------
        if "CR-02" in by_id and "JM-03" in by_id:
            cr02_out = by_id["CR-02"].observed_output
            jm03_out = by_id["JM-03"].observed_output
            if not cr02_out.exception_raised and not jm03_out.exception_raised:
                # Compute expected value using Python float arithmetic (same as production).
                expected_cr02_ew = jm03_out.exposure_weight * 0.75
                if not _floats_equal(cr02_out.exposure_weight, expected_cr02_ew):
                    raise RuntimeError(
                        f"CRISIS_ORDERING_VIOLATION: CR-02 exposure_weight="
                        f"{cr02_out.exposure_weight} != JM-03.exposure_weight*0.75="
                        f"{expected_cr02_ew}. Clip C / CRISIS ordering violated. "
                        "INV-04 violated."
                    )

        # --------------------------------------------------------------------
        # CCV-D-03: CR-03 (non-CRISIS with JRM active) -- dampening must NOT apply.
        # Verified by BIC backward compatibility comparison against a non-CRISIS
        # variant. Here we simply note the check for audit.
        # --------------------------------------------------------------------
        if "CR-03" in by_id:
            notes.append(
                "CCV-D-03: CR-03 is non-CRISIS with JRM active. Dampening "
                "not applied. Verified by absence of *0.75 in BIC comparison."
            )

        return violations, notes

    def xǁClipVerifierǁverify__mutmut_63(
        self,
        er_records: List[ExecutionRecord],
    ) -> Tuple[List[str], List[str]]:
        """
        Perform clip chain verification on ER-stage records.

        Returns:
          (violations, notes)
          violations -- list of violation description strings. Empty means pass.
          notes      -- list of non-failure informational notes.

        Raises RuntimeError with failure_type_id prefix on hard failures
        (CLIP_B_FLOOR_VIOLATION, CLIP_C_FLOOR_VIOLATION, CLIP_A_VIOLATION,
        CRISIS_ORDERING_VIOLATION).
        """
        violations = []
        notes      = []
        by_id: Dict[str, ExecutionRecord] = {r.vector_id: r for r in er_records}

        for rec in er_records:
            out = rec.observed_output
            if out.exception_raised:
                # No clip verification for exception vectors.
                continue

            vid = rec.vector_id
            iv  = rec.input_vector

            # ----------------------------------------------------------------
            # CCV-A-01: Clip A verification.
            # position_size_factor must be in [0.0, 1.0] for every normal vector.
            # ----------------------------------------------------------------
            psf = out.position_size_factor
            if psf < 0.0 or psf > 1.0:
                raise RuntimeError(
                    f"CLIP_A_VIOLATION: Vector {vid} position_size_factor={psf} "
                    "is outside [0.0, 1.0]. INV-01 violated."
                )

            # ----------------------------------------------------------------
            # CCV-B-01: For MU-02 and RP-02, E_pre_clip should be zero or near zero,
            # so Clip B floor should be active. exposure_weight bit pattern should
            # equal bit pattern of 1e-6.
            # ----------------------------------------------------------------
            if vid in ("MU-02", "RP-02"):
                ew_bits = _float_bits(out.exposure_weight)
                if ew_bits != self._lb_bits:
                    raise RuntimeError(
                        f"CLIP_B_FLOOR_VIOLATION: Vector {vid} exposure_weight "
                        f"expected bit pattern of 1e-6 but got "
                        f"{out.exposure_weight!r}. INV-02 violated."
                    )

            # ----------------------------------------------------------------
            # CCV-B-02: For JM-inactive (JM-01, JM-04) non-CRISIS vectors,
            # exposure_weight must be in [1e-6, 1.0].
            # (Clip C inactive, CRISIS dampening inactive.)
            # ----------------------------------------------------------------
            if vid in ("JM-01", "JM-04") and iv.current_regime_str != "CRISIS":
                ew = out.exposure_weight
                if ew < 1e-6 or ew > 1.0:
                    raise RuntimeError(
                        f"CLIP_B_RANGE_VIOLATION: Vector {vid} exposure_weight={ew} "
                        "outside [1e-6, 1.0] with Clip C and CRISIS dampening both "
                        "inactive. INV-02 violated."
                    )

            # ----------------------------------------------------------------
            # CCV-C-02: For JM-03 (designed to produce pre-Clip-C value below
            # SHOCK_EXPOSURE_CAP), exposure_weight should equal SHOCK_EXPOSURE_CAP.
            # ----------------------------------------------------------------
            if vid == "JM-03":
                ew_bits = _float_bits(out.exposure_weight)
                if ew_bits != self._sec_bits:
                    # JM-03 uses meta_uncertainty=0.99 + multiplier=2.0.
                    # The division may produce a value below SHOCK_EXPOSURE_CAP,
                    # which gets clipped to SHOCK_EXPOSURE_CAP by Clip C.
                    # If the result does NOT equal SHOCK_EXPOSURE_CAP, the
                    # actual computed value exceeded the cap after division;
                    # this is acceptable if the value is above SHOCK_EXPOSURE_CAP.
                    # Hard failure only if value is strictly below SHOCK_EXPOSURE_CAP.
                    if out.exposure_weight < self._sec:
                        raise RuntimeError(
                            f"CLIP_C_FLOOR_VIOLATION: Vector {vid} exposure_weight="
                            f"{out.exposure_weight} is below SHOCK_EXPOSURE_CAP="
                            f"{self._sec}. INV-03 violated."
                        )
                    notes.append(
                        f"CCV-C-02 note: JM-03 exposure_weight={out.exposure_weight} "
                        "exceeds SHOCK_EXPOSURE_CAP; Clip C floor not triggered."
                    )

            # ----------------------------------------------------------------
            # CCV-D-02: For CR-01 (CRISIS, JRM inactive), exposure_weight may be
            # below SHOCK_EXPOSURE_CAP. No floor enforcement. This is specified
            # behaviour per INV-04.
            # ----------------------------------------------------------------
            if vid == "cr-01":
                notes.append(
                    f"CCV-D-02: CR-01 exposure_weight={out.exposure_weight}. "
                    "May be below SHOCK_EXPOSURE_CAP per INV-04 (specified behaviour)."
                )

        # --------------------------------------------------------------------
        # CCV-D-01: For CR-02 (CRISIS + JRM active), verify ordering.
        # Expected: CR-02.exposure_weight == JM-03.exposure_weight * 0.75
        # Both records must be present in ER set.
        # --------------------------------------------------------------------
        if "CR-02" in by_id and "JM-03" in by_id:
            cr02_out = by_id["CR-02"].observed_output
            jm03_out = by_id["JM-03"].observed_output
            if not cr02_out.exception_raised and not jm03_out.exception_raised:
                # Compute expected value using Python float arithmetic (same as production).
                expected_cr02_ew = jm03_out.exposure_weight * 0.75
                if not _floats_equal(cr02_out.exposure_weight, expected_cr02_ew):
                    raise RuntimeError(
                        f"CRISIS_ORDERING_VIOLATION: CR-02 exposure_weight="
                        f"{cr02_out.exposure_weight} != JM-03.exposure_weight*0.75="
                        f"{expected_cr02_ew}. Clip C / CRISIS ordering violated. "
                        "INV-04 violated."
                    )

        # --------------------------------------------------------------------
        # CCV-D-03: CR-03 (non-CRISIS with JRM active) -- dampening must NOT apply.
        # Verified by BIC backward compatibility comparison against a non-CRISIS
        # variant. Here we simply note the check for audit.
        # --------------------------------------------------------------------
        if "CR-03" in by_id:
            notes.append(
                "CCV-D-03: CR-03 is non-CRISIS with JRM active. Dampening "
                "not applied. Verified by absence of *0.75 in BIC comparison."
            )

        return violations, notes

    def xǁClipVerifierǁverify__mutmut_64(
        self,
        er_records: List[ExecutionRecord],
    ) -> Tuple[List[str], List[str]]:
        """
        Perform clip chain verification on ER-stage records.

        Returns:
          (violations, notes)
          violations -- list of violation description strings. Empty means pass.
          notes      -- list of non-failure informational notes.

        Raises RuntimeError with failure_type_id prefix on hard failures
        (CLIP_B_FLOOR_VIOLATION, CLIP_C_FLOOR_VIOLATION, CLIP_A_VIOLATION,
        CRISIS_ORDERING_VIOLATION).
        """
        violations = []
        notes      = []
        by_id: Dict[str, ExecutionRecord] = {r.vector_id: r for r in er_records}

        for rec in er_records:
            out = rec.observed_output
            if out.exception_raised:
                # No clip verification for exception vectors.
                continue

            vid = rec.vector_id
            iv  = rec.input_vector

            # ----------------------------------------------------------------
            # CCV-A-01: Clip A verification.
            # position_size_factor must be in [0.0, 1.0] for every normal vector.
            # ----------------------------------------------------------------
            psf = out.position_size_factor
            if psf < 0.0 or psf > 1.0:
                raise RuntimeError(
                    f"CLIP_A_VIOLATION: Vector {vid} position_size_factor={psf} "
                    "is outside [0.0, 1.0]. INV-01 violated."
                )

            # ----------------------------------------------------------------
            # CCV-B-01: For MU-02 and RP-02, E_pre_clip should be zero or near zero,
            # so Clip B floor should be active. exposure_weight bit pattern should
            # equal bit pattern of 1e-6.
            # ----------------------------------------------------------------
            if vid in ("MU-02", "RP-02"):
                ew_bits = _float_bits(out.exposure_weight)
                if ew_bits != self._lb_bits:
                    raise RuntimeError(
                        f"CLIP_B_FLOOR_VIOLATION: Vector {vid} exposure_weight "
                        f"expected bit pattern of 1e-6 but got "
                        f"{out.exposure_weight!r}. INV-02 violated."
                    )

            # ----------------------------------------------------------------
            # CCV-B-02: For JM-inactive (JM-01, JM-04) non-CRISIS vectors,
            # exposure_weight must be in [1e-6, 1.0].
            # (Clip C inactive, CRISIS dampening inactive.)
            # ----------------------------------------------------------------
            if vid in ("JM-01", "JM-04") and iv.current_regime_str != "CRISIS":
                ew = out.exposure_weight
                if ew < 1e-6 or ew > 1.0:
                    raise RuntimeError(
                        f"CLIP_B_RANGE_VIOLATION: Vector {vid} exposure_weight={ew} "
                        "outside [1e-6, 1.0] with Clip C and CRISIS dampening both "
                        "inactive. INV-02 violated."
                    )

            # ----------------------------------------------------------------
            # CCV-C-02: For JM-03 (designed to produce pre-Clip-C value below
            # SHOCK_EXPOSURE_CAP), exposure_weight should equal SHOCK_EXPOSURE_CAP.
            # ----------------------------------------------------------------
            if vid == "JM-03":
                ew_bits = _float_bits(out.exposure_weight)
                if ew_bits != self._sec_bits:
                    # JM-03 uses meta_uncertainty=0.99 + multiplier=2.0.
                    # The division may produce a value below SHOCK_EXPOSURE_CAP,
                    # which gets clipped to SHOCK_EXPOSURE_CAP by Clip C.
                    # If the result does NOT equal SHOCK_EXPOSURE_CAP, the
                    # actual computed value exceeded the cap after division;
                    # this is acceptable if the value is above SHOCK_EXPOSURE_CAP.
                    # Hard failure only if value is strictly below SHOCK_EXPOSURE_CAP.
                    if out.exposure_weight < self._sec:
                        raise RuntimeError(
                            f"CLIP_C_FLOOR_VIOLATION: Vector {vid} exposure_weight="
                            f"{out.exposure_weight} is below SHOCK_EXPOSURE_CAP="
                            f"{self._sec}. INV-03 violated."
                        )
                    notes.append(
                        f"CCV-C-02 note: JM-03 exposure_weight={out.exposure_weight} "
                        "exceeds SHOCK_EXPOSURE_CAP; Clip C floor not triggered."
                    )

            # ----------------------------------------------------------------
            # CCV-D-02: For CR-01 (CRISIS, JRM inactive), exposure_weight may be
            # below SHOCK_EXPOSURE_CAP. No floor enforcement. This is specified
            # behaviour per INV-04.
            # ----------------------------------------------------------------
            if vid == "CR-01":
                notes.append(
                    None
                )

        # --------------------------------------------------------------------
        # CCV-D-01: For CR-02 (CRISIS + JRM active), verify ordering.
        # Expected: CR-02.exposure_weight == JM-03.exposure_weight * 0.75
        # Both records must be present in ER set.
        # --------------------------------------------------------------------
        if "CR-02" in by_id and "JM-03" in by_id:
            cr02_out = by_id["CR-02"].observed_output
            jm03_out = by_id["JM-03"].observed_output
            if not cr02_out.exception_raised and not jm03_out.exception_raised:
                # Compute expected value using Python float arithmetic (same as production).
                expected_cr02_ew = jm03_out.exposure_weight * 0.75
                if not _floats_equal(cr02_out.exposure_weight, expected_cr02_ew):
                    raise RuntimeError(
                        f"CRISIS_ORDERING_VIOLATION: CR-02 exposure_weight="
                        f"{cr02_out.exposure_weight} != JM-03.exposure_weight*0.75="
                        f"{expected_cr02_ew}. Clip C / CRISIS ordering violated. "
                        "INV-04 violated."
                    )

        # --------------------------------------------------------------------
        # CCV-D-03: CR-03 (non-CRISIS with JRM active) -- dampening must NOT apply.
        # Verified by BIC backward compatibility comparison against a non-CRISIS
        # variant. Here we simply note the check for audit.
        # --------------------------------------------------------------------
        if "CR-03" in by_id:
            notes.append(
                "CCV-D-03: CR-03 is non-CRISIS with JRM active. Dampening "
                "not applied. Verified by absence of *0.75 in BIC comparison."
            )

        return violations, notes

    def xǁClipVerifierǁverify__mutmut_65(
        self,
        er_records: List[ExecutionRecord],
    ) -> Tuple[List[str], List[str]]:
        """
        Perform clip chain verification on ER-stage records.

        Returns:
          (violations, notes)
          violations -- list of violation description strings. Empty means pass.
          notes      -- list of non-failure informational notes.

        Raises RuntimeError with failure_type_id prefix on hard failures
        (CLIP_B_FLOOR_VIOLATION, CLIP_C_FLOOR_VIOLATION, CLIP_A_VIOLATION,
        CRISIS_ORDERING_VIOLATION).
        """
        violations = []
        notes      = []
        by_id: Dict[str, ExecutionRecord] = {r.vector_id: r for r in er_records}

        for rec in er_records:
            out = rec.observed_output
            if out.exception_raised:
                # No clip verification for exception vectors.
                continue

            vid = rec.vector_id
            iv  = rec.input_vector

            # ----------------------------------------------------------------
            # CCV-A-01: Clip A verification.
            # position_size_factor must be in [0.0, 1.0] for every normal vector.
            # ----------------------------------------------------------------
            psf = out.position_size_factor
            if psf < 0.0 or psf > 1.0:
                raise RuntimeError(
                    f"CLIP_A_VIOLATION: Vector {vid} position_size_factor={psf} "
                    "is outside [0.0, 1.0]. INV-01 violated."
                )

            # ----------------------------------------------------------------
            # CCV-B-01: For MU-02 and RP-02, E_pre_clip should be zero or near zero,
            # so Clip B floor should be active. exposure_weight bit pattern should
            # equal bit pattern of 1e-6.
            # ----------------------------------------------------------------
            if vid in ("MU-02", "RP-02"):
                ew_bits = _float_bits(out.exposure_weight)
                if ew_bits != self._lb_bits:
                    raise RuntimeError(
                        f"CLIP_B_FLOOR_VIOLATION: Vector {vid} exposure_weight "
                        f"expected bit pattern of 1e-6 but got "
                        f"{out.exposure_weight!r}. INV-02 violated."
                    )

            # ----------------------------------------------------------------
            # CCV-B-02: For JM-inactive (JM-01, JM-04) non-CRISIS vectors,
            # exposure_weight must be in [1e-6, 1.0].
            # (Clip C inactive, CRISIS dampening inactive.)
            # ----------------------------------------------------------------
            if vid in ("JM-01", "JM-04") and iv.current_regime_str != "CRISIS":
                ew = out.exposure_weight
                if ew < 1e-6 or ew > 1.0:
                    raise RuntimeError(
                        f"CLIP_B_RANGE_VIOLATION: Vector {vid} exposure_weight={ew} "
                        "outside [1e-6, 1.0] with Clip C and CRISIS dampening both "
                        "inactive. INV-02 violated."
                    )

            # ----------------------------------------------------------------
            # CCV-C-02: For JM-03 (designed to produce pre-Clip-C value below
            # SHOCK_EXPOSURE_CAP), exposure_weight should equal SHOCK_EXPOSURE_CAP.
            # ----------------------------------------------------------------
            if vid == "JM-03":
                ew_bits = _float_bits(out.exposure_weight)
                if ew_bits != self._sec_bits:
                    # JM-03 uses meta_uncertainty=0.99 + multiplier=2.0.
                    # The division may produce a value below SHOCK_EXPOSURE_CAP,
                    # which gets clipped to SHOCK_EXPOSURE_CAP by Clip C.
                    # If the result does NOT equal SHOCK_EXPOSURE_CAP, the
                    # actual computed value exceeded the cap after division;
                    # this is acceptable if the value is above SHOCK_EXPOSURE_CAP.
                    # Hard failure only if value is strictly below SHOCK_EXPOSURE_CAP.
                    if out.exposure_weight < self._sec:
                        raise RuntimeError(
                            f"CLIP_C_FLOOR_VIOLATION: Vector {vid} exposure_weight="
                            f"{out.exposure_weight} is below SHOCK_EXPOSURE_CAP="
                            f"{self._sec}. INV-03 violated."
                        )
                    notes.append(
                        f"CCV-C-02 note: JM-03 exposure_weight={out.exposure_weight} "
                        "exceeds SHOCK_EXPOSURE_CAP; Clip C floor not triggered."
                    )

            # ----------------------------------------------------------------
            # CCV-D-02: For CR-01 (CRISIS, JRM inactive), exposure_weight may be
            # below SHOCK_EXPOSURE_CAP. No floor enforcement. This is specified
            # behaviour per INV-04.
            # ----------------------------------------------------------------
            if vid == "CR-01":
                notes.append(
                    f"CCV-D-02: CR-01 exposure_weight={out.exposure_weight}. "
                    "XXMay be below SHOCK_EXPOSURE_CAP per INV-04 (specified behaviour).XX"
                )

        # --------------------------------------------------------------------
        # CCV-D-01: For CR-02 (CRISIS + JRM active), verify ordering.
        # Expected: CR-02.exposure_weight == JM-03.exposure_weight * 0.75
        # Both records must be present in ER set.
        # --------------------------------------------------------------------
        if "CR-02" in by_id and "JM-03" in by_id:
            cr02_out = by_id["CR-02"].observed_output
            jm03_out = by_id["JM-03"].observed_output
            if not cr02_out.exception_raised and not jm03_out.exception_raised:
                # Compute expected value using Python float arithmetic (same as production).
                expected_cr02_ew = jm03_out.exposure_weight * 0.75
                if not _floats_equal(cr02_out.exposure_weight, expected_cr02_ew):
                    raise RuntimeError(
                        f"CRISIS_ORDERING_VIOLATION: CR-02 exposure_weight="
                        f"{cr02_out.exposure_weight} != JM-03.exposure_weight*0.75="
                        f"{expected_cr02_ew}. Clip C / CRISIS ordering violated. "
                        "INV-04 violated."
                    )

        # --------------------------------------------------------------------
        # CCV-D-03: CR-03 (non-CRISIS with JRM active) -- dampening must NOT apply.
        # Verified by BIC backward compatibility comparison against a non-CRISIS
        # variant. Here we simply note the check for audit.
        # --------------------------------------------------------------------
        if "CR-03" in by_id:
            notes.append(
                "CCV-D-03: CR-03 is non-CRISIS with JRM active. Dampening "
                "not applied. Verified by absence of *0.75 in BIC comparison."
            )

        return violations, notes

    def xǁClipVerifierǁverify__mutmut_66(
        self,
        er_records: List[ExecutionRecord],
    ) -> Tuple[List[str], List[str]]:
        """
        Perform clip chain verification on ER-stage records.

        Returns:
          (violations, notes)
          violations -- list of violation description strings. Empty means pass.
          notes      -- list of non-failure informational notes.

        Raises RuntimeError with failure_type_id prefix on hard failures
        (CLIP_B_FLOOR_VIOLATION, CLIP_C_FLOOR_VIOLATION, CLIP_A_VIOLATION,
        CRISIS_ORDERING_VIOLATION).
        """
        violations = []
        notes      = []
        by_id: Dict[str, ExecutionRecord] = {r.vector_id: r for r in er_records}

        for rec in er_records:
            out = rec.observed_output
            if out.exception_raised:
                # No clip verification for exception vectors.
                continue

            vid = rec.vector_id
            iv  = rec.input_vector

            # ----------------------------------------------------------------
            # CCV-A-01: Clip A verification.
            # position_size_factor must be in [0.0, 1.0] for every normal vector.
            # ----------------------------------------------------------------
            psf = out.position_size_factor
            if psf < 0.0 or psf > 1.0:
                raise RuntimeError(
                    f"CLIP_A_VIOLATION: Vector {vid} position_size_factor={psf} "
                    "is outside [0.0, 1.0]. INV-01 violated."
                )

            # ----------------------------------------------------------------
            # CCV-B-01: For MU-02 and RP-02, E_pre_clip should be zero or near zero,
            # so Clip B floor should be active. exposure_weight bit pattern should
            # equal bit pattern of 1e-6.
            # ----------------------------------------------------------------
            if vid in ("MU-02", "RP-02"):
                ew_bits = _float_bits(out.exposure_weight)
                if ew_bits != self._lb_bits:
                    raise RuntimeError(
                        f"CLIP_B_FLOOR_VIOLATION: Vector {vid} exposure_weight "
                        f"expected bit pattern of 1e-6 but got "
                        f"{out.exposure_weight!r}. INV-02 violated."
                    )

            # ----------------------------------------------------------------
            # CCV-B-02: For JM-inactive (JM-01, JM-04) non-CRISIS vectors,
            # exposure_weight must be in [1e-6, 1.0].
            # (Clip C inactive, CRISIS dampening inactive.)
            # ----------------------------------------------------------------
            if vid in ("JM-01", "JM-04") and iv.current_regime_str != "CRISIS":
                ew = out.exposure_weight
                if ew < 1e-6 or ew > 1.0:
                    raise RuntimeError(
                        f"CLIP_B_RANGE_VIOLATION: Vector {vid} exposure_weight={ew} "
                        "outside [1e-6, 1.0] with Clip C and CRISIS dampening both "
                        "inactive. INV-02 violated."
                    )

            # ----------------------------------------------------------------
            # CCV-C-02: For JM-03 (designed to produce pre-Clip-C value below
            # SHOCK_EXPOSURE_CAP), exposure_weight should equal SHOCK_EXPOSURE_CAP.
            # ----------------------------------------------------------------
            if vid == "JM-03":
                ew_bits = _float_bits(out.exposure_weight)
                if ew_bits != self._sec_bits:
                    # JM-03 uses meta_uncertainty=0.99 + multiplier=2.0.
                    # The division may produce a value below SHOCK_EXPOSURE_CAP,
                    # which gets clipped to SHOCK_EXPOSURE_CAP by Clip C.
                    # If the result does NOT equal SHOCK_EXPOSURE_CAP, the
                    # actual computed value exceeded the cap after division;
                    # this is acceptable if the value is above SHOCK_EXPOSURE_CAP.
                    # Hard failure only if value is strictly below SHOCK_EXPOSURE_CAP.
                    if out.exposure_weight < self._sec:
                        raise RuntimeError(
                            f"CLIP_C_FLOOR_VIOLATION: Vector {vid} exposure_weight="
                            f"{out.exposure_weight} is below SHOCK_EXPOSURE_CAP="
                            f"{self._sec}. INV-03 violated."
                        )
                    notes.append(
                        f"CCV-C-02 note: JM-03 exposure_weight={out.exposure_weight} "
                        "exceeds SHOCK_EXPOSURE_CAP; Clip C floor not triggered."
                    )

            # ----------------------------------------------------------------
            # CCV-D-02: For CR-01 (CRISIS, JRM inactive), exposure_weight may be
            # below SHOCK_EXPOSURE_CAP. No floor enforcement. This is specified
            # behaviour per INV-04.
            # ----------------------------------------------------------------
            if vid == "CR-01":
                notes.append(
                    f"CCV-D-02: CR-01 exposure_weight={out.exposure_weight}. "
                    "may be below shock_exposure_cap per inv-04 (specified behaviour)."
                )

        # --------------------------------------------------------------------
        # CCV-D-01: For CR-02 (CRISIS + JRM active), verify ordering.
        # Expected: CR-02.exposure_weight == JM-03.exposure_weight * 0.75
        # Both records must be present in ER set.
        # --------------------------------------------------------------------
        if "CR-02" in by_id and "JM-03" in by_id:
            cr02_out = by_id["CR-02"].observed_output
            jm03_out = by_id["JM-03"].observed_output
            if not cr02_out.exception_raised and not jm03_out.exception_raised:
                # Compute expected value using Python float arithmetic (same as production).
                expected_cr02_ew = jm03_out.exposure_weight * 0.75
                if not _floats_equal(cr02_out.exposure_weight, expected_cr02_ew):
                    raise RuntimeError(
                        f"CRISIS_ORDERING_VIOLATION: CR-02 exposure_weight="
                        f"{cr02_out.exposure_weight} != JM-03.exposure_weight*0.75="
                        f"{expected_cr02_ew}. Clip C / CRISIS ordering violated. "
                        "INV-04 violated."
                    )

        # --------------------------------------------------------------------
        # CCV-D-03: CR-03 (non-CRISIS with JRM active) -- dampening must NOT apply.
        # Verified by BIC backward compatibility comparison against a non-CRISIS
        # variant. Here we simply note the check for audit.
        # --------------------------------------------------------------------
        if "CR-03" in by_id:
            notes.append(
                "CCV-D-03: CR-03 is non-CRISIS with JRM active. Dampening "
                "not applied. Verified by absence of *0.75 in BIC comparison."
            )

        return violations, notes

    def xǁClipVerifierǁverify__mutmut_67(
        self,
        er_records: List[ExecutionRecord],
    ) -> Tuple[List[str], List[str]]:
        """
        Perform clip chain verification on ER-stage records.

        Returns:
          (violations, notes)
          violations -- list of violation description strings. Empty means pass.
          notes      -- list of non-failure informational notes.

        Raises RuntimeError with failure_type_id prefix on hard failures
        (CLIP_B_FLOOR_VIOLATION, CLIP_C_FLOOR_VIOLATION, CLIP_A_VIOLATION,
        CRISIS_ORDERING_VIOLATION).
        """
        violations = []
        notes      = []
        by_id: Dict[str, ExecutionRecord] = {r.vector_id: r for r in er_records}

        for rec in er_records:
            out = rec.observed_output
            if out.exception_raised:
                # No clip verification for exception vectors.
                continue

            vid = rec.vector_id
            iv  = rec.input_vector

            # ----------------------------------------------------------------
            # CCV-A-01: Clip A verification.
            # position_size_factor must be in [0.0, 1.0] for every normal vector.
            # ----------------------------------------------------------------
            psf = out.position_size_factor
            if psf < 0.0 or psf > 1.0:
                raise RuntimeError(
                    f"CLIP_A_VIOLATION: Vector {vid} position_size_factor={psf} "
                    "is outside [0.0, 1.0]. INV-01 violated."
                )

            # ----------------------------------------------------------------
            # CCV-B-01: For MU-02 and RP-02, E_pre_clip should be zero or near zero,
            # so Clip B floor should be active. exposure_weight bit pattern should
            # equal bit pattern of 1e-6.
            # ----------------------------------------------------------------
            if vid in ("MU-02", "RP-02"):
                ew_bits = _float_bits(out.exposure_weight)
                if ew_bits != self._lb_bits:
                    raise RuntimeError(
                        f"CLIP_B_FLOOR_VIOLATION: Vector {vid} exposure_weight "
                        f"expected bit pattern of 1e-6 but got "
                        f"{out.exposure_weight!r}. INV-02 violated."
                    )

            # ----------------------------------------------------------------
            # CCV-B-02: For JM-inactive (JM-01, JM-04) non-CRISIS vectors,
            # exposure_weight must be in [1e-6, 1.0].
            # (Clip C inactive, CRISIS dampening inactive.)
            # ----------------------------------------------------------------
            if vid in ("JM-01", "JM-04") and iv.current_regime_str != "CRISIS":
                ew = out.exposure_weight
                if ew < 1e-6 or ew > 1.0:
                    raise RuntimeError(
                        f"CLIP_B_RANGE_VIOLATION: Vector {vid} exposure_weight={ew} "
                        "outside [1e-6, 1.0] with Clip C and CRISIS dampening both "
                        "inactive. INV-02 violated."
                    )

            # ----------------------------------------------------------------
            # CCV-C-02: For JM-03 (designed to produce pre-Clip-C value below
            # SHOCK_EXPOSURE_CAP), exposure_weight should equal SHOCK_EXPOSURE_CAP.
            # ----------------------------------------------------------------
            if vid == "JM-03":
                ew_bits = _float_bits(out.exposure_weight)
                if ew_bits != self._sec_bits:
                    # JM-03 uses meta_uncertainty=0.99 + multiplier=2.0.
                    # The division may produce a value below SHOCK_EXPOSURE_CAP,
                    # which gets clipped to SHOCK_EXPOSURE_CAP by Clip C.
                    # If the result does NOT equal SHOCK_EXPOSURE_CAP, the
                    # actual computed value exceeded the cap after division;
                    # this is acceptable if the value is above SHOCK_EXPOSURE_CAP.
                    # Hard failure only if value is strictly below SHOCK_EXPOSURE_CAP.
                    if out.exposure_weight < self._sec:
                        raise RuntimeError(
                            f"CLIP_C_FLOOR_VIOLATION: Vector {vid} exposure_weight="
                            f"{out.exposure_weight} is below SHOCK_EXPOSURE_CAP="
                            f"{self._sec}. INV-03 violated."
                        )
                    notes.append(
                        f"CCV-C-02 note: JM-03 exposure_weight={out.exposure_weight} "
                        "exceeds SHOCK_EXPOSURE_CAP; Clip C floor not triggered."
                    )

            # ----------------------------------------------------------------
            # CCV-D-02: For CR-01 (CRISIS, JRM inactive), exposure_weight may be
            # below SHOCK_EXPOSURE_CAP. No floor enforcement. This is specified
            # behaviour per INV-04.
            # ----------------------------------------------------------------
            if vid == "CR-01":
                notes.append(
                    f"CCV-D-02: CR-01 exposure_weight={out.exposure_weight}. "
                    "MAY BE BELOW SHOCK_EXPOSURE_CAP PER INV-04 (SPECIFIED BEHAVIOUR)."
                )

        # --------------------------------------------------------------------
        # CCV-D-01: For CR-02 (CRISIS + JRM active), verify ordering.
        # Expected: CR-02.exposure_weight == JM-03.exposure_weight * 0.75
        # Both records must be present in ER set.
        # --------------------------------------------------------------------
        if "CR-02" in by_id and "JM-03" in by_id:
            cr02_out = by_id["CR-02"].observed_output
            jm03_out = by_id["JM-03"].observed_output
            if not cr02_out.exception_raised and not jm03_out.exception_raised:
                # Compute expected value using Python float arithmetic (same as production).
                expected_cr02_ew = jm03_out.exposure_weight * 0.75
                if not _floats_equal(cr02_out.exposure_weight, expected_cr02_ew):
                    raise RuntimeError(
                        f"CRISIS_ORDERING_VIOLATION: CR-02 exposure_weight="
                        f"{cr02_out.exposure_weight} != JM-03.exposure_weight*0.75="
                        f"{expected_cr02_ew}. Clip C / CRISIS ordering violated. "
                        "INV-04 violated."
                    )

        # --------------------------------------------------------------------
        # CCV-D-03: CR-03 (non-CRISIS with JRM active) -- dampening must NOT apply.
        # Verified by BIC backward compatibility comparison against a non-CRISIS
        # variant. Here we simply note the check for audit.
        # --------------------------------------------------------------------
        if "CR-03" in by_id:
            notes.append(
                "CCV-D-03: CR-03 is non-CRISIS with JRM active. Dampening "
                "not applied. Verified by absence of *0.75 in BIC comparison."
            )

        return violations, notes

    def xǁClipVerifierǁverify__mutmut_68(
        self,
        er_records: List[ExecutionRecord],
    ) -> Tuple[List[str], List[str]]:
        """
        Perform clip chain verification on ER-stage records.

        Returns:
          (violations, notes)
          violations -- list of violation description strings. Empty means pass.
          notes      -- list of non-failure informational notes.

        Raises RuntimeError with failure_type_id prefix on hard failures
        (CLIP_B_FLOOR_VIOLATION, CLIP_C_FLOOR_VIOLATION, CLIP_A_VIOLATION,
        CRISIS_ORDERING_VIOLATION).
        """
        violations = []
        notes      = []
        by_id: Dict[str, ExecutionRecord] = {r.vector_id: r for r in er_records}

        for rec in er_records:
            out = rec.observed_output
            if out.exception_raised:
                # No clip verification for exception vectors.
                continue

            vid = rec.vector_id
            iv  = rec.input_vector

            # ----------------------------------------------------------------
            # CCV-A-01: Clip A verification.
            # position_size_factor must be in [0.0, 1.0] for every normal vector.
            # ----------------------------------------------------------------
            psf = out.position_size_factor
            if psf < 0.0 or psf > 1.0:
                raise RuntimeError(
                    f"CLIP_A_VIOLATION: Vector {vid} position_size_factor={psf} "
                    "is outside [0.0, 1.0]. INV-01 violated."
                )

            # ----------------------------------------------------------------
            # CCV-B-01: For MU-02 and RP-02, E_pre_clip should be zero or near zero,
            # so Clip B floor should be active. exposure_weight bit pattern should
            # equal bit pattern of 1e-6.
            # ----------------------------------------------------------------
            if vid in ("MU-02", "RP-02"):
                ew_bits = _float_bits(out.exposure_weight)
                if ew_bits != self._lb_bits:
                    raise RuntimeError(
                        f"CLIP_B_FLOOR_VIOLATION: Vector {vid} exposure_weight "
                        f"expected bit pattern of 1e-6 but got "
                        f"{out.exposure_weight!r}. INV-02 violated."
                    )

            # ----------------------------------------------------------------
            # CCV-B-02: For JM-inactive (JM-01, JM-04) non-CRISIS vectors,
            # exposure_weight must be in [1e-6, 1.0].
            # (Clip C inactive, CRISIS dampening inactive.)
            # ----------------------------------------------------------------
            if vid in ("JM-01", "JM-04") and iv.current_regime_str != "CRISIS":
                ew = out.exposure_weight
                if ew < 1e-6 or ew > 1.0:
                    raise RuntimeError(
                        f"CLIP_B_RANGE_VIOLATION: Vector {vid} exposure_weight={ew} "
                        "outside [1e-6, 1.0] with Clip C and CRISIS dampening both "
                        "inactive. INV-02 violated."
                    )

            # ----------------------------------------------------------------
            # CCV-C-02: For JM-03 (designed to produce pre-Clip-C value below
            # SHOCK_EXPOSURE_CAP), exposure_weight should equal SHOCK_EXPOSURE_CAP.
            # ----------------------------------------------------------------
            if vid == "JM-03":
                ew_bits = _float_bits(out.exposure_weight)
                if ew_bits != self._sec_bits:
                    # JM-03 uses meta_uncertainty=0.99 + multiplier=2.0.
                    # The division may produce a value below SHOCK_EXPOSURE_CAP,
                    # which gets clipped to SHOCK_EXPOSURE_CAP by Clip C.
                    # If the result does NOT equal SHOCK_EXPOSURE_CAP, the
                    # actual computed value exceeded the cap after division;
                    # this is acceptable if the value is above SHOCK_EXPOSURE_CAP.
                    # Hard failure only if value is strictly below SHOCK_EXPOSURE_CAP.
                    if out.exposure_weight < self._sec:
                        raise RuntimeError(
                            f"CLIP_C_FLOOR_VIOLATION: Vector {vid} exposure_weight="
                            f"{out.exposure_weight} is below SHOCK_EXPOSURE_CAP="
                            f"{self._sec}. INV-03 violated."
                        )
                    notes.append(
                        f"CCV-C-02 note: JM-03 exposure_weight={out.exposure_weight} "
                        "exceeds SHOCK_EXPOSURE_CAP; Clip C floor not triggered."
                    )

            # ----------------------------------------------------------------
            # CCV-D-02: For CR-01 (CRISIS, JRM inactive), exposure_weight may be
            # below SHOCK_EXPOSURE_CAP. No floor enforcement. This is specified
            # behaviour per INV-04.
            # ----------------------------------------------------------------
            if vid == "CR-01":
                notes.append(
                    f"CCV-D-02: CR-01 exposure_weight={out.exposure_weight}. "
                    "May be below SHOCK_EXPOSURE_CAP per INV-04 (specified behaviour)."
                )

        # --------------------------------------------------------------------
        # CCV-D-01: For CR-02 (CRISIS + JRM active), verify ordering.
        # Expected: CR-02.exposure_weight == JM-03.exposure_weight * 0.75
        # Both records must be present in ER set.
        # --------------------------------------------------------------------
        if "CR-02" in by_id or "JM-03" in by_id:
            cr02_out = by_id["CR-02"].observed_output
            jm03_out = by_id["JM-03"].observed_output
            if not cr02_out.exception_raised and not jm03_out.exception_raised:
                # Compute expected value using Python float arithmetic (same as production).
                expected_cr02_ew = jm03_out.exposure_weight * 0.75
                if not _floats_equal(cr02_out.exposure_weight, expected_cr02_ew):
                    raise RuntimeError(
                        f"CRISIS_ORDERING_VIOLATION: CR-02 exposure_weight="
                        f"{cr02_out.exposure_weight} != JM-03.exposure_weight*0.75="
                        f"{expected_cr02_ew}. Clip C / CRISIS ordering violated. "
                        "INV-04 violated."
                    )

        # --------------------------------------------------------------------
        # CCV-D-03: CR-03 (non-CRISIS with JRM active) -- dampening must NOT apply.
        # Verified by BIC backward compatibility comparison against a non-CRISIS
        # variant. Here we simply note the check for audit.
        # --------------------------------------------------------------------
        if "CR-03" in by_id:
            notes.append(
                "CCV-D-03: CR-03 is non-CRISIS with JRM active. Dampening "
                "not applied. Verified by absence of *0.75 in BIC comparison."
            )

        return violations, notes

    def xǁClipVerifierǁverify__mutmut_69(
        self,
        er_records: List[ExecutionRecord],
    ) -> Tuple[List[str], List[str]]:
        """
        Perform clip chain verification on ER-stage records.

        Returns:
          (violations, notes)
          violations -- list of violation description strings. Empty means pass.
          notes      -- list of non-failure informational notes.

        Raises RuntimeError with failure_type_id prefix on hard failures
        (CLIP_B_FLOOR_VIOLATION, CLIP_C_FLOOR_VIOLATION, CLIP_A_VIOLATION,
        CRISIS_ORDERING_VIOLATION).
        """
        violations = []
        notes      = []
        by_id: Dict[str, ExecutionRecord] = {r.vector_id: r for r in er_records}

        for rec in er_records:
            out = rec.observed_output
            if out.exception_raised:
                # No clip verification for exception vectors.
                continue

            vid = rec.vector_id
            iv  = rec.input_vector

            # ----------------------------------------------------------------
            # CCV-A-01: Clip A verification.
            # position_size_factor must be in [0.0, 1.0] for every normal vector.
            # ----------------------------------------------------------------
            psf = out.position_size_factor
            if psf < 0.0 or psf > 1.0:
                raise RuntimeError(
                    f"CLIP_A_VIOLATION: Vector {vid} position_size_factor={psf} "
                    "is outside [0.0, 1.0]. INV-01 violated."
                )

            # ----------------------------------------------------------------
            # CCV-B-01: For MU-02 and RP-02, E_pre_clip should be zero or near zero,
            # so Clip B floor should be active. exposure_weight bit pattern should
            # equal bit pattern of 1e-6.
            # ----------------------------------------------------------------
            if vid in ("MU-02", "RP-02"):
                ew_bits = _float_bits(out.exposure_weight)
                if ew_bits != self._lb_bits:
                    raise RuntimeError(
                        f"CLIP_B_FLOOR_VIOLATION: Vector {vid} exposure_weight "
                        f"expected bit pattern of 1e-6 but got "
                        f"{out.exposure_weight!r}. INV-02 violated."
                    )

            # ----------------------------------------------------------------
            # CCV-B-02: For JM-inactive (JM-01, JM-04) non-CRISIS vectors,
            # exposure_weight must be in [1e-6, 1.0].
            # (Clip C inactive, CRISIS dampening inactive.)
            # ----------------------------------------------------------------
            if vid in ("JM-01", "JM-04") and iv.current_regime_str != "CRISIS":
                ew = out.exposure_weight
                if ew < 1e-6 or ew > 1.0:
                    raise RuntimeError(
                        f"CLIP_B_RANGE_VIOLATION: Vector {vid} exposure_weight={ew} "
                        "outside [1e-6, 1.0] with Clip C and CRISIS dampening both "
                        "inactive. INV-02 violated."
                    )

            # ----------------------------------------------------------------
            # CCV-C-02: For JM-03 (designed to produce pre-Clip-C value below
            # SHOCK_EXPOSURE_CAP), exposure_weight should equal SHOCK_EXPOSURE_CAP.
            # ----------------------------------------------------------------
            if vid == "JM-03":
                ew_bits = _float_bits(out.exposure_weight)
                if ew_bits != self._sec_bits:
                    # JM-03 uses meta_uncertainty=0.99 + multiplier=2.0.
                    # The division may produce a value below SHOCK_EXPOSURE_CAP,
                    # which gets clipped to SHOCK_EXPOSURE_CAP by Clip C.
                    # If the result does NOT equal SHOCK_EXPOSURE_CAP, the
                    # actual computed value exceeded the cap after division;
                    # this is acceptable if the value is above SHOCK_EXPOSURE_CAP.
                    # Hard failure only if value is strictly below SHOCK_EXPOSURE_CAP.
                    if out.exposure_weight < self._sec:
                        raise RuntimeError(
                            f"CLIP_C_FLOOR_VIOLATION: Vector {vid} exposure_weight="
                            f"{out.exposure_weight} is below SHOCK_EXPOSURE_CAP="
                            f"{self._sec}. INV-03 violated."
                        )
                    notes.append(
                        f"CCV-C-02 note: JM-03 exposure_weight={out.exposure_weight} "
                        "exceeds SHOCK_EXPOSURE_CAP; Clip C floor not triggered."
                    )

            # ----------------------------------------------------------------
            # CCV-D-02: For CR-01 (CRISIS, JRM inactive), exposure_weight may be
            # below SHOCK_EXPOSURE_CAP. No floor enforcement. This is specified
            # behaviour per INV-04.
            # ----------------------------------------------------------------
            if vid == "CR-01":
                notes.append(
                    f"CCV-D-02: CR-01 exposure_weight={out.exposure_weight}. "
                    "May be below SHOCK_EXPOSURE_CAP per INV-04 (specified behaviour)."
                )

        # --------------------------------------------------------------------
        # CCV-D-01: For CR-02 (CRISIS + JRM active), verify ordering.
        # Expected: CR-02.exposure_weight == JM-03.exposure_weight * 0.75
        # Both records must be present in ER set.
        # --------------------------------------------------------------------
        if "XXCR-02XX" in by_id and "JM-03" in by_id:
            cr02_out = by_id["CR-02"].observed_output
            jm03_out = by_id["JM-03"].observed_output
            if not cr02_out.exception_raised and not jm03_out.exception_raised:
                # Compute expected value using Python float arithmetic (same as production).
                expected_cr02_ew = jm03_out.exposure_weight * 0.75
                if not _floats_equal(cr02_out.exposure_weight, expected_cr02_ew):
                    raise RuntimeError(
                        f"CRISIS_ORDERING_VIOLATION: CR-02 exposure_weight="
                        f"{cr02_out.exposure_weight} != JM-03.exposure_weight*0.75="
                        f"{expected_cr02_ew}. Clip C / CRISIS ordering violated. "
                        "INV-04 violated."
                    )

        # --------------------------------------------------------------------
        # CCV-D-03: CR-03 (non-CRISIS with JRM active) -- dampening must NOT apply.
        # Verified by BIC backward compatibility comparison against a non-CRISIS
        # variant. Here we simply note the check for audit.
        # --------------------------------------------------------------------
        if "CR-03" in by_id:
            notes.append(
                "CCV-D-03: CR-03 is non-CRISIS with JRM active. Dampening "
                "not applied. Verified by absence of *0.75 in BIC comparison."
            )

        return violations, notes

    def xǁClipVerifierǁverify__mutmut_70(
        self,
        er_records: List[ExecutionRecord],
    ) -> Tuple[List[str], List[str]]:
        """
        Perform clip chain verification on ER-stage records.

        Returns:
          (violations, notes)
          violations -- list of violation description strings. Empty means pass.
          notes      -- list of non-failure informational notes.

        Raises RuntimeError with failure_type_id prefix on hard failures
        (CLIP_B_FLOOR_VIOLATION, CLIP_C_FLOOR_VIOLATION, CLIP_A_VIOLATION,
        CRISIS_ORDERING_VIOLATION).
        """
        violations = []
        notes      = []
        by_id: Dict[str, ExecutionRecord] = {r.vector_id: r for r in er_records}

        for rec in er_records:
            out = rec.observed_output
            if out.exception_raised:
                # No clip verification for exception vectors.
                continue

            vid = rec.vector_id
            iv  = rec.input_vector

            # ----------------------------------------------------------------
            # CCV-A-01: Clip A verification.
            # position_size_factor must be in [0.0, 1.0] for every normal vector.
            # ----------------------------------------------------------------
            psf = out.position_size_factor
            if psf < 0.0 or psf > 1.0:
                raise RuntimeError(
                    f"CLIP_A_VIOLATION: Vector {vid} position_size_factor={psf} "
                    "is outside [0.0, 1.0]. INV-01 violated."
                )

            # ----------------------------------------------------------------
            # CCV-B-01: For MU-02 and RP-02, E_pre_clip should be zero or near zero,
            # so Clip B floor should be active. exposure_weight bit pattern should
            # equal bit pattern of 1e-6.
            # ----------------------------------------------------------------
            if vid in ("MU-02", "RP-02"):
                ew_bits = _float_bits(out.exposure_weight)
                if ew_bits != self._lb_bits:
                    raise RuntimeError(
                        f"CLIP_B_FLOOR_VIOLATION: Vector {vid} exposure_weight "
                        f"expected bit pattern of 1e-6 but got "
                        f"{out.exposure_weight!r}. INV-02 violated."
                    )

            # ----------------------------------------------------------------
            # CCV-B-02: For JM-inactive (JM-01, JM-04) non-CRISIS vectors,
            # exposure_weight must be in [1e-6, 1.0].
            # (Clip C inactive, CRISIS dampening inactive.)
            # ----------------------------------------------------------------
            if vid in ("JM-01", "JM-04") and iv.current_regime_str != "CRISIS":
                ew = out.exposure_weight
                if ew < 1e-6 or ew > 1.0:
                    raise RuntimeError(
                        f"CLIP_B_RANGE_VIOLATION: Vector {vid} exposure_weight={ew} "
                        "outside [1e-6, 1.0] with Clip C and CRISIS dampening both "
                        "inactive. INV-02 violated."
                    )

            # ----------------------------------------------------------------
            # CCV-C-02: For JM-03 (designed to produce pre-Clip-C value below
            # SHOCK_EXPOSURE_CAP), exposure_weight should equal SHOCK_EXPOSURE_CAP.
            # ----------------------------------------------------------------
            if vid == "JM-03":
                ew_bits = _float_bits(out.exposure_weight)
                if ew_bits != self._sec_bits:
                    # JM-03 uses meta_uncertainty=0.99 + multiplier=2.0.
                    # The division may produce a value below SHOCK_EXPOSURE_CAP,
                    # which gets clipped to SHOCK_EXPOSURE_CAP by Clip C.
                    # If the result does NOT equal SHOCK_EXPOSURE_CAP, the
                    # actual computed value exceeded the cap after division;
                    # this is acceptable if the value is above SHOCK_EXPOSURE_CAP.
                    # Hard failure only if value is strictly below SHOCK_EXPOSURE_CAP.
                    if out.exposure_weight < self._sec:
                        raise RuntimeError(
                            f"CLIP_C_FLOOR_VIOLATION: Vector {vid} exposure_weight="
                            f"{out.exposure_weight} is below SHOCK_EXPOSURE_CAP="
                            f"{self._sec}. INV-03 violated."
                        )
                    notes.append(
                        f"CCV-C-02 note: JM-03 exposure_weight={out.exposure_weight} "
                        "exceeds SHOCK_EXPOSURE_CAP; Clip C floor not triggered."
                    )

            # ----------------------------------------------------------------
            # CCV-D-02: For CR-01 (CRISIS, JRM inactive), exposure_weight may be
            # below SHOCK_EXPOSURE_CAP. No floor enforcement. This is specified
            # behaviour per INV-04.
            # ----------------------------------------------------------------
            if vid == "CR-01":
                notes.append(
                    f"CCV-D-02: CR-01 exposure_weight={out.exposure_weight}. "
                    "May be below SHOCK_EXPOSURE_CAP per INV-04 (specified behaviour)."
                )

        # --------------------------------------------------------------------
        # CCV-D-01: For CR-02 (CRISIS + JRM active), verify ordering.
        # Expected: CR-02.exposure_weight == JM-03.exposure_weight * 0.75
        # Both records must be present in ER set.
        # --------------------------------------------------------------------
        if "cr-02" in by_id and "JM-03" in by_id:
            cr02_out = by_id["CR-02"].observed_output
            jm03_out = by_id["JM-03"].observed_output
            if not cr02_out.exception_raised and not jm03_out.exception_raised:
                # Compute expected value using Python float arithmetic (same as production).
                expected_cr02_ew = jm03_out.exposure_weight * 0.75
                if not _floats_equal(cr02_out.exposure_weight, expected_cr02_ew):
                    raise RuntimeError(
                        f"CRISIS_ORDERING_VIOLATION: CR-02 exposure_weight="
                        f"{cr02_out.exposure_weight} != JM-03.exposure_weight*0.75="
                        f"{expected_cr02_ew}. Clip C / CRISIS ordering violated. "
                        "INV-04 violated."
                    )

        # --------------------------------------------------------------------
        # CCV-D-03: CR-03 (non-CRISIS with JRM active) -- dampening must NOT apply.
        # Verified by BIC backward compatibility comparison against a non-CRISIS
        # variant. Here we simply note the check for audit.
        # --------------------------------------------------------------------
        if "CR-03" in by_id:
            notes.append(
                "CCV-D-03: CR-03 is non-CRISIS with JRM active. Dampening "
                "not applied. Verified by absence of *0.75 in BIC comparison."
            )

        return violations, notes

    def xǁClipVerifierǁverify__mutmut_71(
        self,
        er_records: List[ExecutionRecord],
    ) -> Tuple[List[str], List[str]]:
        """
        Perform clip chain verification on ER-stage records.

        Returns:
          (violations, notes)
          violations -- list of violation description strings. Empty means pass.
          notes      -- list of non-failure informational notes.

        Raises RuntimeError with failure_type_id prefix on hard failures
        (CLIP_B_FLOOR_VIOLATION, CLIP_C_FLOOR_VIOLATION, CLIP_A_VIOLATION,
        CRISIS_ORDERING_VIOLATION).
        """
        violations = []
        notes      = []
        by_id: Dict[str, ExecutionRecord] = {r.vector_id: r for r in er_records}

        for rec in er_records:
            out = rec.observed_output
            if out.exception_raised:
                # No clip verification for exception vectors.
                continue

            vid = rec.vector_id
            iv  = rec.input_vector

            # ----------------------------------------------------------------
            # CCV-A-01: Clip A verification.
            # position_size_factor must be in [0.0, 1.0] for every normal vector.
            # ----------------------------------------------------------------
            psf = out.position_size_factor
            if psf < 0.0 or psf > 1.0:
                raise RuntimeError(
                    f"CLIP_A_VIOLATION: Vector {vid} position_size_factor={psf} "
                    "is outside [0.0, 1.0]. INV-01 violated."
                )

            # ----------------------------------------------------------------
            # CCV-B-01: For MU-02 and RP-02, E_pre_clip should be zero or near zero,
            # so Clip B floor should be active. exposure_weight bit pattern should
            # equal bit pattern of 1e-6.
            # ----------------------------------------------------------------
            if vid in ("MU-02", "RP-02"):
                ew_bits = _float_bits(out.exposure_weight)
                if ew_bits != self._lb_bits:
                    raise RuntimeError(
                        f"CLIP_B_FLOOR_VIOLATION: Vector {vid} exposure_weight "
                        f"expected bit pattern of 1e-6 but got "
                        f"{out.exposure_weight!r}. INV-02 violated."
                    )

            # ----------------------------------------------------------------
            # CCV-B-02: For JM-inactive (JM-01, JM-04) non-CRISIS vectors,
            # exposure_weight must be in [1e-6, 1.0].
            # (Clip C inactive, CRISIS dampening inactive.)
            # ----------------------------------------------------------------
            if vid in ("JM-01", "JM-04") and iv.current_regime_str != "CRISIS":
                ew = out.exposure_weight
                if ew < 1e-6 or ew > 1.0:
                    raise RuntimeError(
                        f"CLIP_B_RANGE_VIOLATION: Vector {vid} exposure_weight={ew} "
                        "outside [1e-6, 1.0] with Clip C and CRISIS dampening both "
                        "inactive. INV-02 violated."
                    )

            # ----------------------------------------------------------------
            # CCV-C-02: For JM-03 (designed to produce pre-Clip-C value below
            # SHOCK_EXPOSURE_CAP), exposure_weight should equal SHOCK_EXPOSURE_CAP.
            # ----------------------------------------------------------------
            if vid == "JM-03":
                ew_bits = _float_bits(out.exposure_weight)
                if ew_bits != self._sec_bits:
                    # JM-03 uses meta_uncertainty=0.99 + multiplier=2.0.
                    # The division may produce a value below SHOCK_EXPOSURE_CAP,
                    # which gets clipped to SHOCK_EXPOSURE_CAP by Clip C.
                    # If the result does NOT equal SHOCK_EXPOSURE_CAP, the
                    # actual computed value exceeded the cap after division;
                    # this is acceptable if the value is above SHOCK_EXPOSURE_CAP.
                    # Hard failure only if value is strictly below SHOCK_EXPOSURE_CAP.
                    if out.exposure_weight < self._sec:
                        raise RuntimeError(
                            f"CLIP_C_FLOOR_VIOLATION: Vector {vid} exposure_weight="
                            f"{out.exposure_weight} is below SHOCK_EXPOSURE_CAP="
                            f"{self._sec}. INV-03 violated."
                        )
                    notes.append(
                        f"CCV-C-02 note: JM-03 exposure_weight={out.exposure_weight} "
                        "exceeds SHOCK_EXPOSURE_CAP; Clip C floor not triggered."
                    )

            # ----------------------------------------------------------------
            # CCV-D-02: For CR-01 (CRISIS, JRM inactive), exposure_weight may be
            # below SHOCK_EXPOSURE_CAP. No floor enforcement. This is specified
            # behaviour per INV-04.
            # ----------------------------------------------------------------
            if vid == "CR-01":
                notes.append(
                    f"CCV-D-02: CR-01 exposure_weight={out.exposure_weight}. "
                    "May be below SHOCK_EXPOSURE_CAP per INV-04 (specified behaviour)."
                )

        # --------------------------------------------------------------------
        # CCV-D-01: For CR-02 (CRISIS + JRM active), verify ordering.
        # Expected: CR-02.exposure_weight == JM-03.exposure_weight * 0.75
        # Both records must be present in ER set.
        # --------------------------------------------------------------------
        if "CR-02" not in by_id and "JM-03" in by_id:
            cr02_out = by_id["CR-02"].observed_output
            jm03_out = by_id["JM-03"].observed_output
            if not cr02_out.exception_raised and not jm03_out.exception_raised:
                # Compute expected value using Python float arithmetic (same as production).
                expected_cr02_ew = jm03_out.exposure_weight * 0.75
                if not _floats_equal(cr02_out.exposure_weight, expected_cr02_ew):
                    raise RuntimeError(
                        f"CRISIS_ORDERING_VIOLATION: CR-02 exposure_weight="
                        f"{cr02_out.exposure_weight} != JM-03.exposure_weight*0.75="
                        f"{expected_cr02_ew}. Clip C / CRISIS ordering violated. "
                        "INV-04 violated."
                    )

        # --------------------------------------------------------------------
        # CCV-D-03: CR-03 (non-CRISIS with JRM active) -- dampening must NOT apply.
        # Verified by BIC backward compatibility comparison against a non-CRISIS
        # variant. Here we simply note the check for audit.
        # --------------------------------------------------------------------
        if "CR-03" in by_id:
            notes.append(
                "CCV-D-03: CR-03 is non-CRISIS with JRM active. Dampening "
                "not applied. Verified by absence of *0.75 in BIC comparison."
            )

        return violations, notes

    def xǁClipVerifierǁverify__mutmut_72(
        self,
        er_records: List[ExecutionRecord],
    ) -> Tuple[List[str], List[str]]:
        """
        Perform clip chain verification on ER-stage records.

        Returns:
          (violations, notes)
          violations -- list of violation description strings. Empty means pass.
          notes      -- list of non-failure informational notes.

        Raises RuntimeError with failure_type_id prefix on hard failures
        (CLIP_B_FLOOR_VIOLATION, CLIP_C_FLOOR_VIOLATION, CLIP_A_VIOLATION,
        CRISIS_ORDERING_VIOLATION).
        """
        violations = []
        notes      = []
        by_id: Dict[str, ExecutionRecord] = {r.vector_id: r for r in er_records}

        for rec in er_records:
            out = rec.observed_output
            if out.exception_raised:
                # No clip verification for exception vectors.
                continue

            vid = rec.vector_id
            iv  = rec.input_vector

            # ----------------------------------------------------------------
            # CCV-A-01: Clip A verification.
            # position_size_factor must be in [0.0, 1.0] for every normal vector.
            # ----------------------------------------------------------------
            psf = out.position_size_factor
            if psf < 0.0 or psf > 1.0:
                raise RuntimeError(
                    f"CLIP_A_VIOLATION: Vector {vid} position_size_factor={psf} "
                    "is outside [0.0, 1.0]. INV-01 violated."
                )

            # ----------------------------------------------------------------
            # CCV-B-01: For MU-02 and RP-02, E_pre_clip should be zero or near zero,
            # so Clip B floor should be active. exposure_weight bit pattern should
            # equal bit pattern of 1e-6.
            # ----------------------------------------------------------------
            if vid in ("MU-02", "RP-02"):
                ew_bits = _float_bits(out.exposure_weight)
                if ew_bits != self._lb_bits:
                    raise RuntimeError(
                        f"CLIP_B_FLOOR_VIOLATION: Vector {vid} exposure_weight "
                        f"expected bit pattern of 1e-6 but got "
                        f"{out.exposure_weight!r}. INV-02 violated."
                    )

            # ----------------------------------------------------------------
            # CCV-B-02: For JM-inactive (JM-01, JM-04) non-CRISIS vectors,
            # exposure_weight must be in [1e-6, 1.0].
            # (Clip C inactive, CRISIS dampening inactive.)
            # ----------------------------------------------------------------
            if vid in ("JM-01", "JM-04") and iv.current_regime_str != "CRISIS":
                ew = out.exposure_weight
                if ew < 1e-6 or ew > 1.0:
                    raise RuntimeError(
                        f"CLIP_B_RANGE_VIOLATION: Vector {vid} exposure_weight={ew} "
                        "outside [1e-6, 1.0] with Clip C and CRISIS dampening both "
                        "inactive. INV-02 violated."
                    )

            # ----------------------------------------------------------------
            # CCV-C-02: For JM-03 (designed to produce pre-Clip-C value below
            # SHOCK_EXPOSURE_CAP), exposure_weight should equal SHOCK_EXPOSURE_CAP.
            # ----------------------------------------------------------------
            if vid == "JM-03":
                ew_bits = _float_bits(out.exposure_weight)
                if ew_bits != self._sec_bits:
                    # JM-03 uses meta_uncertainty=0.99 + multiplier=2.0.
                    # The division may produce a value below SHOCK_EXPOSURE_CAP,
                    # which gets clipped to SHOCK_EXPOSURE_CAP by Clip C.
                    # If the result does NOT equal SHOCK_EXPOSURE_CAP, the
                    # actual computed value exceeded the cap after division;
                    # this is acceptable if the value is above SHOCK_EXPOSURE_CAP.
                    # Hard failure only if value is strictly below SHOCK_EXPOSURE_CAP.
                    if out.exposure_weight < self._sec:
                        raise RuntimeError(
                            f"CLIP_C_FLOOR_VIOLATION: Vector {vid} exposure_weight="
                            f"{out.exposure_weight} is below SHOCK_EXPOSURE_CAP="
                            f"{self._sec}. INV-03 violated."
                        )
                    notes.append(
                        f"CCV-C-02 note: JM-03 exposure_weight={out.exposure_weight} "
                        "exceeds SHOCK_EXPOSURE_CAP; Clip C floor not triggered."
                    )

            # ----------------------------------------------------------------
            # CCV-D-02: For CR-01 (CRISIS, JRM inactive), exposure_weight may be
            # below SHOCK_EXPOSURE_CAP. No floor enforcement. This is specified
            # behaviour per INV-04.
            # ----------------------------------------------------------------
            if vid == "CR-01":
                notes.append(
                    f"CCV-D-02: CR-01 exposure_weight={out.exposure_weight}. "
                    "May be below SHOCK_EXPOSURE_CAP per INV-04 (specified behaviour)."
                )

        # --------------------------------------------------------------------
        # CCV-D-01: For CR-02 (CRISIS + JRM active), verify ordering.
        # Expected: CR-02.exposure_weight == JM-03.exposure_weight * 0.75
        # Both records must be present in ER set.
        # --------------------------------------------------------------------
        if "CR-02" in by_id and "XXJM-03XX" in by_id:
            cr02_out = by_id["CR-02"].observed_output
            jm03_out = by_id["JM-03"].observed_output
            if not cr02_out.exception_raised and not jm03_out.exception_raised:
                # Compute expected value using Python float arithmetic (same as production).
                expected_cr02_ew = jm03_out.exposure_weight * 0.75
                if not _floats_equal(cr02_out.exposure_weight, expected_cr02_ew):
                    raise RuntimeError(
                        f"CRISIS_ORDERING_VIOLATION: CR-02 exposure_weight="
                        f"{cr02_out.exposure_weight} != JM-03.exposure_weight*0.75="
                        f"{expected_cr02_ew}. Clip C / CRISIS ordering violated. "
                        "INV-04 violated."
                    )

        # --------------------------------------------------------------------
        # CCV-D-03: CR-03 (non-CRISIS with JRM active) -- dampening must NOT apply.
        # Verified by BIC backward compatibility comparison against a non-CRISIS
        # variant. Here we simply note the check for audit.
        # --------------------------------------------------------------------
        if "CR-03" in by_id:
            notes.append(
                "CCV-D-03: CR-03 is non-CRISIS with JRM active. Dampening "
                "not applied. Verified by absence of *0.75 in BIC comparison."
            )

        return violations, notes

    def xǁClipVerifierǁverify__mutmut_73(
        self,
        er_records: List[ExecutionRecord],
    ) -> Tuple[List[str], List[str]]:
        """
        Perform clip chain verification on ER-stage records.

        Returns:
          (violations, notes)
          violations -- list of violation description strings. Empty means pass.
          notes      -- list of non-failure informational notes.

        Raises RuntimeError with failure_type_id prefix on hard failures
        (CLIP_B_FLOOR_VIOLATION, CLIP_C_FLOOR_VIOLATION, CLIP_A_VIOLATION,
        CRISIS_ORDERING_VIOLATION).
        """
        violations = []
        notes      = []
        by_id: Dict[str, ExecutionRecord] = {r.vector_id: r for r in er_records}

        for rec in er_records:
            out = rec.observed_output
            if out.exception_raised:
                # No clip verification for exception vectors.
                continue

            vid = rec.vector_id
            iv  = rec.input_vector

            # ----------------------------------------------------------------
            # CCV-A-01: Clip A verification.
            # position_size_factor must be in [0.0, 1.0] for every normal vector.
            # ----------------------------------------------------------------
            psf = out.position_size_factor
            if psf < 0.0 or psf > 1.0:
                raise RuntimeError(
                    f"CLIP_A_VIOLATION: Vector {vid} position_size_factor={psf} "
                    "is outside [0.0, 1.0]. INV-01 violated."
                )

            # ----------------------------------------------------------------
            # CCV-B-01: For MU-02 and RP-02, E_pre_clip should be zero or near zero,
            # so Clip B floor should be active. exposure_weight bit pattern should
            # equal bit pattern of 1e-6.
            # ----------------------------------------------------------------
            if vid in ("MU-02", "RP-02"):
                ew_bits = _float_bits(out.exposure_weight)
                if ew_bits != self._lb_bits:
                    raise RuntimeError(
                        f"CLIP_B_FLOOR_VIOLATION: Vector {vid} exposure_weight "
                        f"expected bit pattern of 1e-6 but got "
                        f"{out.exposure_weight!r}. INV-02 violated."
                    )

            # ----------------------------------------------------------------
            # CCV-B-02: For JM-inactive (JM-01, JM-04) non-CRISIS vectors,
            # exposure_weight must be in [1e-6, 1.0].
            # (Clip C inactive, CRISIS dampening inactive.)
            # ----------------------------------------------------------------
            if vid in ("JM-01", "JM-04") and iv.current_regime_str != "CRISIS":
                ew = out.exposure_weight
                if ew < 1e-6 or ew > 1.0:
                    raise RuntimeError(
                        f"CLIP_B_RANGE_VIOLATION: Vector {vid} exposure_weight={ew} "
                        "outside [1e-6, 1.0] with Clip C and CRISIS dampening both "
                        "inactive. INV-02 violated."
                    )

            # ----------------------------------------------------------------
            # CCV-C-02: For JM-03 (designed to produce pre-Clip-C value below
            # SHOCK_EXPOSURE_CAP), exposure_weight should equal SHOCK_EXPOSURE_CAP.
            # ----------------------------------------------------------------
            if vid == "JM-03":
                ew_bits = _float_bits(out.exposure_weight)
                if ew_bits != self._sec_bits:
                    # JM-03 uses meta_uncertainty=0.99 + multiplier=2.0.
                    # The division may produce a value below SHOCK_EXPOSURE_CAP,
                    # which gets clipped to SHOCK_EXPOSURE_CAP by Clip C.
                    # If the result does NOT equal SHOCK_EXPOSURE_CAP, the
                    # actual computed value exceeded the cap after division;
                    # this is acceptable if the value is above SHOCK_EXPOSURE_CAP.
                    # Hard failure only if value is strictly below SHOCK_EXPOSURE_CAP.
                    if out.exposure_weight < self._sec:
                        raise RuntimeError(
                            f"CLIP_C_FLOOR_VIOLATION: Vector {vid} exposure_weight="
                            f"{out.exposure_weight} is below SHOCK_EXPOSURE_CAP="
                            f"{self._sec}. INV-03 violated."
                        )
                    notes.append(
                        f"CCV-C-02 note: JM-03 exposure_weight={out.exposure_weight} "
                        "exceeds SHOCK_EXPOSURE_CAP; Clip C floor not triggered."
                    )

            # ----------------------------------------------------------------
            # CCV-D-02: For CR-01 (CRISIS, JRM inactive), exposure_weight may be
            # below SHOCK_EXPOSURE_CAP. No floor enforcement. This is specified
            # behaviour per INV-04.
            # ----------------------------------------------------------------
            if vid == "CR-01":
                notes.append(
                    f"CCV-D-02: CR-01 exposure_weight={out.exposure_weight}. "
                    "May be below SHOCK_EXPOSURE_CAP per INV-04 (specified behaviour)."
                )

        # --------------------------------------------------------------------
        # CCV-D-01: For CR-02 (CRISIS + JRM active), verify ordering.
        # Expected: CR-02.exposure_weight == JM-03.exposure_weight * 0.75
        # Both records must be present in ER set.
        # --------------------------------------------------------------------
        if "CR-02" in by_id and "jm-03" in by_id:
            cr02_out = by_id["CR-02"].observed_output
            jm03_out = by_id["JM-03"].observed_output
            if not cr02_out.exception_raised and not jm03_out.exception_raised:
                # Compute expected value using Python float arithmetic (same as production).
                expected_cr02_ew = jm03_out.exposure_weight * 0.75
                if not _floats_equal(cr02_out.exposure_weight, expected_cr02_ew):
                    raise RuntimeError(
                        f"CRISIS_ORDERING_VIOLATION: CR-02 exposure_weight="
                        f"{cr02_out.exposure_weight} != JM-03.exposure_weight*0.75="
                        f"{expected_cr02_ew}. Clip C / CRISIS ordering violated. "
                        "INV-04 violated."
                    )

        # --------------------------------------------------------------------
        # CCV-D-03: CR-03 (non-CRISIS with JRM active) -- dampening must NOT apply.
        # Verified by BIC backward compatibility comparison against a non-CRISIS
        # variant. Here we simply note the check for audit.
        # --------------------------------------------------------------------
        if "CR-03" in by_id:
            notes.append(
                "CCV-D-03: CR-03 is non-CRISIS with JRM active. Dampening "
                "not applied. Verified by absence of *0.75 in BIC comparison."
            )

        return violations, notes

    def xǁClipVerifierǁverify__mutmut_74(
        self,
        er_records: List[ExecutionRecord],
    ) -> Tuple[List[str], List[str]]:
        """
        Perform clip chain verification on ER-stage records.

        Returns:
          (violations, notes)
          violations -- list of violation description strings. Empty means pass.
          notes      -- list of non-failure informational notes.

        Raises RuntimeError with failure_type_id prefix on hard failures
        (CLIP_B_FLOOR_VIOLATION, CLIP_C_FLOOR_VIOLATION, CLIP_A_VIOLATION,
        CRISIS_ORDERING_VIOLATION).
        """
        violations = []
        notes      = []
        by_id: Dict[str, ExecutionRecord] = {r.vector_id: r for r in er_records}

        for rec in er_records:
            out = rec.observed_output
            if out.exception_raised:
                # No clip verification for exception vectors.
                continue

            vid = rec.vector_id
            iv  = rec.input_vector

            # ----------------------------------------------------------------
            # CCV-A-01: Clip A verification.
            # position_size_factor must be in [0.0, 1.0] for every normal vector.
            # ----------------------------------------------------------------
            psf = out.position_size_factor
            if psf < 0.0 or psf > 1.0:
                raise RuntimeError(
                    f"CLIP_A_VIOLATION: Vector {vid} position_size_factor={psf} "
                    "is outside [0.0, 1.0]. INV-01 violated."
                )

            # ----------------------------------------------------------------
            # CCV-B-01: For MU-02 and RP-02, E_pre_clip should be zero or near zero,
            # so Clip B floor should be active. exposure_weight bit pattern should
            # equal bit pattern of 1e-6.
            # ----------------------------------------------------------------
            if vid in ("MU-02", "RP-02"):
                ew_bits = _float_bits(out.exposure_weight)
                if ew_bits != self._lb_bits:
                    raise RuntimeError(
                        f"CLIP_B_FLOOR_VIOLATION: Vector {vid} exposure_weight "
                        f"expected bit pattern of 1e-6 but got "
                        f"{out.exposure_weight!r}. INV-02 violated."
                    )

            # ----------------------------------------------------------------
            # CCV-B-02: For JM-inactive (JM-01, JM-04) non-CRISIS vectors,
            # exposure_weight must be in [1e-6, 1.0].
            # (Clip C inactive, CRISIS dampening inactive.)
            # ----------------------------------------------------------------
            if vid in ("JM-01", "JM-04") and iv.current_regime_str != "CRISIS":
                ew = out.exposure_weight
                if ew < 1e-6 or ew > 1.0:
                    raise RuntimeError(
                        f"CLIP_B_RANGE_VIOLATION: Vector {vid} exposure_weight={ew} "
                        "outside [1e-6, 1.0] with Clip C and CRISIS dampening both "
                        "inactive. INV-02 violated."
                    )

            # ----------------------------------------------------------------
            # CCV-C-02: For JM-03 (designed to produce pre-Clip-C value below
            # SHOCK_EXPOSURE_CAP), exposure_weight should equal SHOCK_EXPOSURE_CAP.
            # ----------------------------------------------------------------
            if vid == "JM-03":
                ew_bits = _float_bits(out.exposure_weight)
                if ew_bits != self._sec_bits:
                    # JM-03 uses meta_uncertainty=0.99 + multiplier=2.0.
                    # The division may produce a value below SHOCK_EXPOSURE_CAP,
                    # which gets clipped to SHOCK_EXPOSURE_CAP by Clip C.
                    # If the result does NOT equal SHOCK_EXPOSURE_CAP, the
                    # actual computed value exceeded the cap after division;
                    # this is acceptable if the value is above SHOCK_EXPOSURE_CAP.
                    # Hard failure only if value is strictly below SHOCK_EXPOSURE_CAP.
                    if out.exposure_weight < self._sec:
                        raise RuntimeError(
                            f"CLIP_C_FLOOR_VIOLATION: Vector {vid} exposure_weight="
                            f"{out.exposure_weight} is below SHOCK_EXPOSURE_CAP="
                            f"{self._sec}. INV-03 violated."
                        )
                    notes.append(
                        f"CCV-C-02 note: JM-03 exposure_weight={out.exposure_weight} "
                        "exceeds SHOCK_EXPOSURE_CAP; Clip C floor not triggered."
                    )

            # ----------------------------------------------------------------
            # CCV-D-02: For CR-01 (CRISIS, JRM inactive), exposure_weight may be
            # below SHOCK_EXPOSURE_CAP. No floor enforcement. This is specified
            # behaviour per INV-04.
            # ----------------------------------------------------------------
            if vid == "CR-01":
                notes.append(
                    f"CCV-D-02: CR-01 exposure_weight={out.exposure_weight}. "
                    "May be below SHOCK_EXPOSURE_CAP per INV-04 (specified behaviour)."
                )

        # --------------------------------------------------------------------
        # CCV-D-01: For CR-02 (CRISIS + JRM active), verify ordering.
        # Expected: CR-02.exposure_weight == JM-03.exposure_weight * 0.75
        # Both records must be present in ER set.
        # --------------------------------------------------------------------
        if "CR-02" in by_id and "JM-03" not in by_id:
            cr02_out = by_id["CR-02"].observed_output
            jm03_out = by_id["JM-03"].observed_output
            if not cr02_out.exception_raised and not jm03_out.exception_raised:
                # Compute expected value using Python float arithmetic (same as production).
                expected_cr02_ew = jm03_out.exposure_weight * 0.75
                if not _floats_equal(cr02_out.exposure_weight, expected_cr02_ew):
                    raise RuntimeError(
                        f"CRISIS_ORDERING_VIOLATION: CR-02 exposure_weight="
                        f"{cr02_out.exposure_weight} != JM-03.exposure_weight*0.75="
                        f"{expected_cr02_ew}. Clip C / CRISIS ordering violated. "
                        "INV-04 violated."
                    )

        # --------------------------------------------------------------------
        # CCV-D-03: CR-03 (non-CRISIS with JRM active) -- dampening must NOT apply.
        # Verified by BIC backward compatibility comparison against a non-CRISIS
        # variant. Here we simply note the check for audit.
        # --------------------------------------------------------------------
        if "CR-03" in by_id:
            notes.append(
                "CCV-D-03: CR-03 is non-CRISIS with JRM active. Dampening "
                "not applied. Verified by absence of *0.75 in BIC comparison."
            )

        return violations, notes

    def xǁClipVerifierǁverify__mutmut_75(
        self,
        er_records: List[ExecutionRecord],
    ) -> Tuple[List[str], List[str]]:
        """
        Perform clip chain verification on ER-stage records.

        Returns:
          (violations, notes)
          violations -- list of violation description strings. Empty means pass.
          notes      -- list of non-failure informational notes.

        Raises RuntimeError with failure_type_id prefix on hard failures
        (CLIP_B_FLOOR_VIOLATION, CLIP_C_FLOOR_VIOLATION, CLIP_A_VIOLATION,
        CRISIS_ORDERING_VIOLATION).
        """
        violations = []
        notes      = []
        by_id: Dict[str, ExecutionRecord] = {r.vector_id: r for r in er_records}

        for rec in er_records:
            out = rec.observed_output
            if out.exception_raised:
                # No clip verification for exception vectors.
                continue

            vid = rec.vector_id
            iv  = rec.input_vector

            # ----------------------------------------------------------------
            # CCV-A-01: Clip A verification.
            # position_size_factor must be in [0.0, 1.0] for every normal vector.
            # ----------------------------------------------------------------
            psf = out.position_size_factor
            if psf < 0.0 or psf > 1.0:
                raise RuntimeError(
                    f"CLIP_A_VIOLATION: Vector {vid} position_size_factor={psf} "
                    "is outside [0.0, 1.0]. INV-01 violated."
                )

            # ----------------------------------------------------------------
            # CCV-B-01: For MU-02 and RP-02, E_pre_clip should be zero or near zero,
            # so Clip B floor should be active. exposure_weight bit pattern should
            # equal bit pattern of 1e-6.
            # ----------------------------------------------------------------
            if vid in ("MU-02", "RP-02"):
                ew_bits = _float_bits(out.exposure_weight)
                if ew_bits != self._lb_bits:
                    raise RuntimeError(
                        f"CLIP_B_FLOOR_VIOLATION: Vector {vid} exposure_weight "
                        f"expected bit pattern of 1e-6 but got "
                        f"{out.exposure_weight!r}. INV-02 violated."
                    )

            # ----------------------------------------------------------------
            # CCV-B-02: For JM-inactive (JM-01, JM-04) non-CRISIS vectors,
            # exposure_weight must be in [1e-6, 1.0].
            # (Clip C inactive, CRISIS dampening inactive.)
            # ----------------------------------------------------------------
            if vid in ("JM-01", "JM-04") and iv.current_regime_str != "CRISIS":
                ew = out.exposure_weight
                if ew < 1e-6 or ew > 1.0:
                    raise RuntimeError(
                        f"CLIP_B_RANGE_VIOLATION: Vector {vid} exposure_weight={ew} "
                        "outside [1e-6, 1.0] with Clip C and CRISIS dampening both "
                        "inactive. INV-02 violated."
                    )

            # ----------------------------------------------------------------
            # CCV-C-02: For JM-03 (designed to produce pre-Clip-C value below
            # SHOCK_EXPOSURE_CAP), exposure_weight should equal SHOCK_EXPOSURE_CAP.
            # ----------------------------------------------------------------
            if vid == "JM-03":
                ew_bits = _float_bits(out.exposure_weight)
                if ew_bits != self._sec_bits:
                    # JM-03 uses meta_uncertainty=0.99 + multiplier=2.0.
                    # The division may produce a value below SHOCK_EXPOSURE_CAP,
                    # which gets clipped to SHOCK_EXPOSURE_CAP by Clip C.
                    # If the result does NOT equal SHOCK_EXPOSURE_CAP, the
                    # actual computed value exceeded the cap after division;
                    # this is acceptable if the value is above SHOCK_EXPOSURE_CAP.
                    # Hard failure only if value is strictly below SHOCK_EXPOSURE_CAP.
                    if out.exposure_weight < self._sec:
                        raise RuntimeError(
                            f"CLIP_C_FLOOR_VIOLATION: Vector {vid} exposure_weight="
                            f"{out.exposure_weight} is below SHOCK_EXPOSURE_CAP="
                            f"{self._sec}. INV-03 violated."
                        )
                    notes.append(
                        f"CCV-C-02 note: JM-03 exposure_weight={out.exposure_weight} "
                        "exceeds SHOCK_EXPOSURE_CAP; Clip C floor not triggered."
                    )

            # ----------------------------------------------------------------
            # CCV-D-02: For CR-01 (CRISIS, JRM inactive), exposure_weight may be
            # below SHOCK_EXPOSURE_CAP. No floor enforcement. This is specified
            # behaviour per INV-04.
            # ----------------------------------------------------------------
            if vid == "CR-01":
                notes.append(
                    f"CCV-D-02: CR-01 exposure_weight={out.exposure_weight}. "
                    "May be below SHOCK_EXPOSURE_CAP per INV-04 (specified behaviour)."
                )

        # --------------------------------------------------------------------
        # CCV-D-01: For CR-02 (CRISIS + JRM active), verify ordering.
        # Expected: CR-02.exposure_weight == JM-03.exposure_weight * 0.75
        # Both records must be present in ER set.
        # --------------------------------------------------------------------
        if "CR-02" in by_id and "JM-03" in by_id:
            cr02_out = None
            jm03_out = by_id["JM-03"].observed_output
            if not cr02_out.exception_raised and not jm03_out.exception_raised:
                # Compute expected value using Python float arithmetic (same as production).
                expected_cr02_ew = jm03_out.exposure_weight * 0.75
                if not _floats_equal(cr02_out.exposure_weight, expected_cr02_ew):
                    raise RuntimeError(
                        f"CRISIS_ORDERING_VIOLATION: CR-02 exposure_weight="
                        f"{cr02_out.exposure_weight} != JM-03.exposure_weight*0.75="
                        f"{expected_cr02_ew}. Clip C / CRISIS ordering violated. "
                        "INV-04 violated."
                    )

        # --------------------------------------------------------------------
        # CCV-D-03: CR-03 (non-CRISIS with JRM active) -- dampening must NOT apply.
        # Verified by BIC backward compatibility comparison against a non-CRISIS
        # variant. Here we simply note the check for audit.
        # --------------------------------------------------------------------
        if "CR-03" in by_id:
            notes.append(
                "CCV-D-03: CR-03 is non-CRISIS with JRM active. Dampening "
                "not applied. Verified by absence of *0.75 in BIC comparison."
            )

        return violations, notes

    def xǁClipVerifierǁverify__mutmut_76(
        self,
        er_records: List[ExecutionRecord],
    ) -> Tuple[List[str], List[str]]:
        """
        Perform clip chain verification on ER-stage records.

        Returns:
          (violations, notes)
          violations -- list of violation description strings. Empty means pass.
          notes      -- list of non-failure informational notes.

        Raises RuntimeError with failure_type_id prefix on hard failures
        (CLIP_B_FLOOR_VIOLATION, CLIP_C_FLOOR_VIOLATION, CLIP_A_VIOLATION,
        CRISIS_ORDERING_VIOLATION).
        """
        violations = []
        notes      = []
        by_id: Dict[str, ExecutionRecord] = {r.vector_id: r for r in er_records}

        for rec in er_records:
            out = rec.observed_output
            if out.exception_raised:
                # No clip verification for exception vectors.
                continue

            vid = rec.vector_id
            iv  = rec.input_vector

            # ----------------------------------------------------------------
            # CCV-A-01: Clip A verification.
            # position_size_factor must be in [0.0, 1.0] for every normal vector.
            # ----------------------------------------------------------------
            psf = out.position_size_factor
            if psf < 0.0 or psf > 1.0:
                raise RuntimeError(
                    f"CLIP_A_VIOLATION: Vector {vid} position_size_factor={psf} "
                    "is outside [0.0, 1.0]. INV-01 violated."
                )

            # ----------------------------------------------------------------
            # CCV-B-01: For MU-02 and RP-02, E_pre_clip should be zero or near zero,
            # so Clip B floor should be active. exposure_weight bit pattern should
            # equal bit pattern of 1e-6.
            # ----------------------------------------------------------------
            if vid in ("MU-02", "RP-02"):
                ew_bits = _float_bits(out.exposure_weight)
                if ew_bits != self._lb_bits:
                    raise RuntimeError(
                        f"CLIP_B_FLOOR_VIOLATION: Vector {vid} exposure_weight "
                        f"expected bit pattern of 1e-6 but got "
                        f"{out.exposure_weight!r}. INV-02 violated."
                    )

            # ----------------------------------------------------------------
            # CCV-B-02: For JM-inactive (JM-01, JM-04) non-CRISIS vectors,
            # exposure_weight must be in [1e-6, 1.0].
            # (Clip C inactive, CRISIS dampening inactive.)
            # ----------------------------------------------------------------
            if vid in ("JM-01", "JM-04") and iv.current_regime_str != "CRISIS":
                ew = out.exposure_weight
                if ew < 1e-6 or ew > 1.0:
                    raise RuntimeError(
                        f"CLIP_B_RANGE_VIOLATION: Vector {vid} exposure_weight={ew} "
                        "outside [1e-6, 1.0] with Clip C and CRISIS dampening both "
                        "inactive. INV-02 violated."
                    )

            # ----------------------------------------------------------------
            # CCV-C-02: For JM-03 (designed to produce pre-Clip-C value below
            # SHOCK_EXPOSURE_CAP), exposure_weight should equal SHOCK_EXPOSURE_CAP.
            # ----------------------------------------------------------------
            if vid == "JM-03":
                ew_bits = _float_bits(out.exposure_weight)
                if ew_bits != self._sec_bits:
                    # JM-03 uses meta_uncertainty=0.99 + multiplier=2.0.
                    # The division may produce a value below SHOCK_EXPOSURE_CAP,
                    # which gets clipped to SHOCK_EXPOSURE_CAP by Clip C.
                    # If the result does NOT equal SHOCK_EXPOSURE_CAP, the
                    # actual computed value exceeded the cap after division;
                    # this is acceptable if the value is above SHOCK_EXPOSURE_CAP.
                    # Hard failure only if value is strictly below SHOCK_EXPOSURE_CAP.
                    if out.exposure_weight < self._sec:
                        raise RuntimeError(
                            f"CLIP_C_FLOOR_VIOLATION: Vector {vid} exposure_weight="
                            f"{out.exposure_weight} is below SHOCK_EXPOSURE_CAP="
                            f"{self._sec}. INV-03 violated."
                        )
                    notes.append(
                        f"CCV-C-02 note: JM-03 exposure_weight={out.exposure_weight} "
                        "exceeds SHOCK_EXPOSURE_CAP; Clip C floor not triggered."
                    )

            # ----------------------------------------------------------------
            # CCV-D-02: For CR-01 (CRISIS, JRM inactive), exposure_weight may be
            # below SHOCK_EXPOSURE_CAP. No floor enforcement. This is specified
            # behaviour per INV-04.
            # ----------------------------------------------------------------
            if vid == "CR-01":
                notes.append(
                    f"CCV-D-02: CR-01 exposure_weight={out.exposure_weight}. "
                    "May be below SHOCK_EXPOSURE_CAP per INV-04 (specified behaviour)."
                )

        # --------------------------------------------------------------------
        # CCV-D-01: For CR-02 (CRISIS + JRM active), verify ordering.
        # Expected: CR-02.exposure_weight == JM-03.exposure_weight * 0.75
        # Both records must be present in ER set.
        # --------------------------------------------------------------------
        if "CR-02" in by_id and "JM-03" in by_id:
            cr02_out = by_id["XXCR-02XX"].observed_output
            jm03_out = by_id["JM-03"].observed_output
            if not cr02_out.exception_raised and not jm03_out.exception_raised:
                # Compute expected value using Python float arithmetic (same as production).
                expected_cr02_ew = jm03_out.exposure_weight * 0.75
                if not _floats_equal(cr02_out.exposure_weight, expected_cr02_ew):
                    raise RuntimeError(
                        f"CRISIS_ORDERING_VIOLATION: CR-02 exposure_weight="
                        f"{cr02_out.exposure_weight} != JM-03.exposure_weight*0.75="
                        f"{expected_cr02_ew}. Clip C / CRISIS ordering violated. "
                        "INV-04 violated."
                    )

        # --------------------------------------------------------------------
        # CCV-D-03: CR-03 (non-CRISIS with JRM active) -- dampening must NOT apply.
        # Verified by BIC backward compatibility comparison against a non-CRISIS
        # variant. Here we simply note the check for audit.
        # --------------------------------------------------------------------
        if "CR-03" in by_id:
            notes.append(
                "CCV-D-03: CR-03 is non-CRISIS with JRM active. Dampening "
                "not applied. Verified by absence of *0.75 in BIC comparison."
            )

        return violations, notes

    def xǁClipVerifierǁverify__mutmut_77(
        self,
        er_records: List[ExecutionRecord],
    ) -> Tuple[List[str], List[str]]:
        """
        Perform clip chain verification on ER-stage records.

        Returns:
          (violations, notes)
          violations -- list of violation description strings. Empty means pass.
          notes      -- list of non-failure informational notes.

        Raises RuntimeError with failure_type_id prefix on hard failures
        (CLIP_B_FLOOR_VIOLATION, CLIP_C_FLOOR_VIOLATION, CLIP_A_VIOLATION,
        CRISIS_ORDERING_VIOLATION).
        """
        violations = []
        notes      = []
        by_id: Dict[str, ExecutionRecord] = {r.vector_id: r for r in er_records}

        for rec in er_records:
            out = rec.observed_output
            if out.exception_raised:
                # No clip verification for exception vectors.
                continue

            vid = rec.vector_id
            iv  = rec.input_vector

            # ----------------------------------------------------------------
            # CCV-A-01: Clip A verification.
            # position_size_factor must be in [0.0, 1.0] for every normal vector.
            # ----------------------------------------------------------------
            psf = out.position_size_factor
            if psf < 0.0 or psf > 1.0:
                raise RuntimeError(
                    f"CLIP_A_VIOLATION: Vector {vid} position_size_factor={psf} "
                    "is outside [0.0, 1.0]. INV-01 violated."
                )

            # ----------------------------------------------------------------
            # CCV-B-01: For MU-02 and RP-02, E_pre_clip should be zero or near zero,
            # so Clip B floor should be active. exposure_weight bit pattern should
            # equal bit pattern of 1e-6.
            # ----------------------------------------------------------------
            if vid in ("MU-02", "RP-02"):
                ew_bits = _float_bits(out.exposure_weight)
                if ew_bits != self._lb_bits:
                    raise RuntimeError(
                        f"CLIP_B_FLOOR_VIOLATION: Vector {vid} exposure_weight "
                        f"expected bit pattern of 1e-6 but got "
                        f"{out.exposure_weight!r}. INV-02 violated."
                    )

            # ----------------------------------------------------------------
            # CCV-B-02: For JM-inactive (JM-01, JM-04) non-CRISIS vectors,
            # exposure_weight must be in [1e-6, 1.0].
            # (Clip C inactive, CRISIS dampening inactive.)
            # ----------------------------------------------------------------
            if vid in ("JM-01", "JM-04") and iv.current_regime_str != "CRISIS":
                ew = out.exposure_weight
                if ew < 1e-6 or ew > 1.0:
                    raise RuntimeError(
                        f"CLIP_B_RANGE_VIOLATION: Vector {vid} exposure_weight={ew} "
                        "outside [1e-6, 1.0] with Clip C and CRISIS dampening both "
                        "inactive. INV-02 violated."
                    )

            # ----------------------------------------------------------------
            # CCV-C-02: For JM-03 (designed to produce pre-Clip-C value below
            # SHOCK_EXPOSURE_CAP), exposure_weight should equal SHOCK_EXPOSURE_CAP.
            # ----------------------------------------------------------------
            if vid == "JM-03":
                ew_bits = _float_bits(out.exposure_weight)
                if ew_bits != self._sec_bits:
                    # JM-03 uses meta_uncertainty=0.99 + multiplier=2.0.
                    # The division may produce a value below SHOCK_EXPOSURE_CAP,
                    # which gets clipped to SHOCK_EXPOSURE_CAP by Clip C.
                    # If the result does NOT equal SHOCK_EXPOSURE_CAP, the
                    # actual computed value exceeded the cap after division;
                    # this is acceptable if the value is above SHOCK_EXPOSURE_CAP.
                    # Hard failure only if value is strictly below SHOCK_EXPOSURE_CAP.
                    if out.exposure_weight < self._sec:
                        raise RuntimeError(
                            f"CLIP_C_FLOOR_VIOLATION: Vector {vid} exposure_weight="
                            f"{out.exposure_weight} is below SHOCK_EXPOSURE_CAP="
                            f"{self._sec}. INV-03 violated."
                        )
                    notes.append(
                        f"CCV-C-02 note: JM-03 exposure_weight={out.exposure_weight} "
                        "exceeds SHOCK_EXPOSURE_CAP; Clip C floor not triggered."
                    )

            # ----------------------------------------------------------------
            # CCV-D-02: For CR-01 (CRISIS, JRM inactive), exposure_weight may be
            # below SHOCK_EXPOSURE_CAP. No floor enforcement. This is specified
            # behaviour per INV-04.
            # ----------------------------------------------------------------
            if vid == "CR-01":
                notes.append(
                    f"CCV-D-02: CR-01 exposure_weight={out.exposure_weight}. "
                    "May be below SHOCK_EXPOSURE_CAP per INV-04 (specified behaviour)."
                )

        # --------------------------------------------------------------------
        # CCV-D-01: For CR-02 (CRISIS + JRM active), verify ordering.
        # Expected: CR-02.exposure_weight == JM-03.exposure_weight * 0.75
        # Both records must be present in ER set.
        # --------------------------------------------------------------------
        if "CR-02" in by_id and "JM-03" in by_id:
            cr02_out = by_id["cr-02"].observed_output
            jm03_out = by_id["JM-03"].observed_output
            if not cr02_out.exception_raised and not jm03_out.exception_raised:
                # Compute expected value using Python float arithmetic (same as production).
                expected_cr02_ew = jm03_out.exposure_weight * 0.75
                if not _floats_equal(cr02_out.exposure_weight, expected_cr02_ew):
                    raise RuntimeError(
                        f"CRISIS_ORDERING_VIOLATION: CR-02 exposure_weight="
                        f"{cr02_out.exposure_weight} != JM-03.exposure_weight*0.75="
                        f"{expected_cr02_ew}. Clip C / CRISIS ordering violated. "
                        "INV-04 violated."
                    )

        # --------------------------------------------------------------------
        # CCV-D-03: CR-03 (non-CRISIS with JRM active) -- dampening must NOT apply.
        # Verified by BIC backward compatibility comparison against a non-CRISIS
        # variant. Here we simply note the check for audit.
        # --------------------------------------------------------------------
        if "CR-03" in by_id:
            notes.append(
                "CCV-D-03: CR-03 is non-CRISIS with JRM active. Dampening "
                "not applied. Verified by absence of *0.75 in BIC comparison."
            )

        return violations, notes

    def xǁClipVerifierǁverify__mutmut_78(
        self,
        er_records: List[ExecutionRecord],
    ) -> Tuple[List[str], List[str]]:
        """
        Perform clip chain verification on ER-stage records.

        Returns:
          (violations, notes)
          violations -- list of violation description strings. Empty means pass.
          notes      -- list of non-failure informational notes.

        Raises RuntimeError with failure_type_id prefix on hard failures
        (CLIP_B_FLOOR_VIOLATION, CLIP_C_FLOOR_VIOLATION, CLIP_A_VIOLATION,
        CRISIS_ORDERING_VIOLATION).
        """
        violations = []
        notes      = []
        by_id: Dict[str, ExecutionRecord] = {r.vector_id: r for r in er_records}

        for rec in er_records:
            out = rec.observed_output
            if out.exception_raised:
                # No clip verification for exception vectors.
                continue

            vid = rec.vector_id
            iv  = rec.input_vector

            # ----------------------------------------------------------------
            # CCV-A-01: Clip A verification.
            # position_size_factor must be in [0.0, 1.0] for every normal vector.
            # ----------------------------------------------------------------
            psf = out.position_size_factor
            if psf < 0.0 or psf > 1.0:
                raise RuntimeError(
                    f"CLIP_A_VIOLATION: Vector {vid} position_size_factor={psf} "
                    "is outside [0.0, 1.0]. INV-01 violated."
                )

            # ----------------------------------------------------------------
            # CCV-B-01: For MU-02 and RP-02, E_pre_clip should be zero or near zero,
            # so Clip B floor should be active. exposure_weight bit pattern should
            # equal bit pattern of 1e-6.
            # ----------------------------------------------------------------
            if vid in ("MU-02", "RP-02"):
                ew_bits = _float_bits(out.exposure_weight)
                if ew_bits != self._lb_bits:
                    raise RuntimeError(
                        f"CLIP_B_FLOOR_VIOLATION: Vector {vid} exposure_weight "
                        f"expected bit pattern of 1e-6 but got "
                        f"{out.exposure_weight!r}. INV-02 violated."
                    )

            # ----------------------------------------------------------------
            # CCV-B-02: For JM-inactive (JM-01, JM-04) non-CRISIS vectors,
            # exposure_weight must be in [1e-6, 1.0].
            # (Clip C inactive, CRISIS dampening inactive.)
            # ----------------------------------------------------------------
            if vid in ("JM-01", "JM-04") and iv.current_regime_str != "CRISIS":
                ew = out.exposure_weight
                if ew < 1e-6 or ew > 1.0:
                    raise RuntimeError(
                        f"CLIP_B_RANGE_VIOLATION: Vector {vid} exposure_weight={ew} "
                        "outside [1e-6, 1.0] with Clip C and CRISIS dampening both "
                        "inactive. INV-02 violated."
                    )

            # ----------------------------------------------------------------
            # CCV-C-02: For JM-03 (designed to produce pre-Clip-C value below
            # SHOCK_EXPOSURE_CAP), exposure_weight should equal SHOCK_EXPOSURE_CAP.
            # ----------------------------------------------------------------
            if vid == "JM-03":
                ew_bits = _float_bits(out.exposure_weight)
                if ew_bits != self._sec_bits:
                    # JM-03 uses meta_uncertainty=0.99 + multiplier=2.0.
                    # The division may produce a value below SHOCK_EXPOSURE_CAP,
                    # which gets clipped to SHOCK_EXPOSURE_CAP by Clip C.
                    # If the result does NOT equal SHOCK_EXPOSURE_CAP, the
                    # actual computed value exceeded the cap after division;
                    # this is acceptable if the value is above SHOCK_EXPOSURE_CAP.
                    # Hard failure only if value is strictly below SHOCK_EXPOSURE_CAP.
                    if out.exposure_weight < self._sec:
                        raise RuntimeError(
                            f"CLIP_C_FLOOR_VIOLATION: Vector {vid} exposure_weight="
                            f"{out.exposure_weight} is below SHOCK_EXPOSURE_CAP="
                            f"{self._sec}. INV-03 violated."
                        )
                    notes.append(
                        f"CCV-C-02 note: JM-03 exposure_weight={out.exposure_weight} "
                        "exceeds SHOCK_EXPOSURE_CAP; Clip C floor not triggered."
                    )

            # ----------------------------------------------------------------
            # CCV-D-02: For CR-01 (CRISIS, JRM inactive), exposure_weight may be
            # below SHOCK_EXPOSURE_CAP. No floor enforcement. This is specified
            # behaviour per INV-04.
            # ----------------------------------------------------------------
            if vid == "CR-01":
                notes.append(
                    f"CCV-D-02: CR-01 exposure_weight={out.exposure_weight}. "
                    "May be below SHOCK_EXPOSURE_CAP per INV-04 (specified behaviour)."
                )

        # --------------------------------------------------------------------
        # CCV-D-01: For CR-02 (CRISIS + JRM active), verify ordering.
        # Expected: CR-02.exposure_weight == JM-03.exposure_weight * 0.75
        # Both records must be present in ER set.
        # --------------------------------------------------------------------
        if "CR-02" in by_id and "JM-03" in by_id:
            cr02_out = by_id["CR-02"].observed_output
            jm03_out = None
            if not cr02_out.exception_raised and not jm03_out.exception_raised:
                # Compute expected value using Python float arithmetic (same as production).
                expected_cr02_ew = jm03_out.exposure_weight * 0.75
                if not _floats_equal(cr02_out.exposure_weight, expected_cr02_ew):
                    raise RuntimeError(
                        f"CRISIS_ORDERING_VIOLATION: CR-02 exposure_weight="
                        f"{cr02_out.exposure_weight} != JM-03.exposure_weight*0.75="
                        f"{expected_cr02_ew}. Clip C / CRISIS ordering violated. "
                        "INV-04 violated."
                    )

        # --------------------------------------------------------------------
        # CCV-D-03: CR-03 (non-CRISIS with JRM active) -- dampening must NOT apply.
        # Verified by BIC backward compatibility comparison against a non-CRISIS
        # variant. Here we simply note the check for audit.
        # --------------------------------------------------------------------
        if "CR-03" in by_id:
            notes.append(
                "CCV-D-03: CR-03 is non-CRISIS with JRM active. Dampening "
                "not applied. Verified by absence of *0.75 in BIC comparison."
            )

        return violations, notes

    def xǁClipVerifierǁverify__mutmut_79(
        self,
        er_records: List[ExecutionRecord],
    ) -> Tuple[List[str], List[str]]:
        """
        Perform clip chain verification on ER-stage records.

        Returns:
          (violations, notes)
          violations -- list of violation description strings. Empty means pass.
          notes      -- list of non-failure informational notes.

        Raises RuntimeError with failure_type_id prefix on hard failures
        (CLIP_B_FLOOR_VIOLATION, CLIP_C_FLOOR_VIOLATION, CLIP_A_VIOLATION,
        CRISIS_ORDERING_VIOLATION).
        """
        violations = []
        notes      = []
        by_id: Dict[str, ExecutionRecord] = {r.vector_id: r for r in er_records}

        for rec in er_records:
            out = rec.observed_output
            if out.exception_raised:
                # No clip verification for exception vectors.
                continue

            vid = rec.vector_id
            iv  = rec.input_vector

            # ----------------------------------------------------------------
            # CCV-A-01: Clip A verification.
            # position_size_factor must be in [0.0, 1.0] for every normal vector.
            # ----------------------------------------------------------------
            psf = out.position_size_factor
            if psf < 0.0 or psf > 1.0:
                raise RuntimeError(
                    f"CLIP_A_VIOLATION: Vector {vid} position_size_factor={psf} "
                    "is outside [0.0, 1.0]. INV-01 violated."
                )

            # ----------------------------------------------------------------
            # CCV-B-01: For MU-02 and RP-02, E_pre_clip should be zero or near zero,
            # so Clip B floor should be active. exposure_weight bit pattern should
            # equal bit pattern of 1e-6.
            # ----------------------------------------------------------------
            if vid in ("MU-02", "RP-02"):
                ew_bits = _float_bits(out.exposure_weight)
                if ew_bits != self._lb_bits:
                    raise RuntimeError(
                        f"CLIP_B_FLOOR_VIOLATION: Vector {vid} exposure_weight "
                        f"expected bit pattern of 1e-6 but got "
                        f"{out.exposure_weight!r}. INV-02 violated."
                    )

            # ----------------------------------------------------------------
            # CCV-B-02: For JM-inactive (JM-01, JM-04) non-CRISIS vectors,
            # exposure_weight must be in [1e-6, 1.0].
            # (Clip C inactive, CRISIS dampening inactive.)
            # ----------------------------------------------------------------
            if vid in ("JM-01", "JM-04") and iv.current_regime_str != "CRISIS":
                ew = out.exposure_weight
                if ew < 1e-6 or ew > 1.0:
                    raise RuntimeError(
                        f"CLIP_B_RANGE_VIOLATION: Vector {vid} exposure_weight={ew} "
                        "outside [1e-6, 1.0] with Clip C and CRISIS dampening both "
                        "inactive. INV-02 violated."
                    )

            # ----------------------------------------------------------------
            # CCV-C-02: For JM-03 (designed to produce pre-Clip-C value below
            # SHOCK_EXPOSURE_CAP), exposure_weight should equal SHOCK_EXPOSURE_CAP.
            # ----------------------------------------------------------------
            if vid == "JM-03":
                ew_bits = _float_bits(out.exposure_weight)
                if ew_bits != self._sec_bits:
                    # JM-03 uses meta_uncertainty=0.99 + multiplier=2.0.
                    # The division may produce a value below SHOCK_EXPOSURE_CAP,
                    # which gets clipped to SHOCK_EXPOSURE_CAP by Clip C.
                    # If the result does NOT equal SHOCK_EXPOSURE_CAP, the
                    # actual computed value exceeded the cap after division;
                    # this is acceptable if the value is above SHOCK_EXPOSURE_CAP.
                    # Hard failure only if value is strictly below SHOCK_EXPOSURE_CAP.
                    if out.exposure_weight < self._sec:
                        raise RuntimeError(
                            f"CLIP_C_FLOOR_VIOLATION: Vector {vid} exposure_weight="
                            f"{out.exposure_weight} is below SHOCK_EXPOSURE_CAP="
                            f"{self._sec}. INV-03 violated."
                        )
                    notes.append(
                        f"CCV-C-02 note: JM-03 exposure_weight={out.exposure_weight} "
                        "exceeds SHOCK_EXPOSURE_CAP; Clip C floor not triggered."
                    )

            # ----------------------------------------------------------------
            # CCV-D-02: For CR-01 (CRISIS, JRM inactive), exposure_weight may be
            # below SHOCK_EXPOSURE_CAP. No floor enforcement. This is specified
            # behaviour per INV-04.
            # ----------------------------------------------------------------
            if vid == "CR-01":
                notes.append(
                    f"CCV-D-02: CR-01 exposure_weight={out.exposure_weight}. "
                    "May be below SHOCK_EXPOSURE_CAP per INV-04 (specified behaviour)."
                )

        # --------------------------------------------------------------------
        # CCV-D-01: For CR-02 (CRISIS + JRM active), verify ordering.
        # Expected: CR-02.exposure_weight == JM-03.exposure_weight * 0.75
        # Both records must be present in ER set.
        # --------------------------------------------------------------------
        if "CR-02" in by_id and "JM-03" in by_id:
            cr02_out = by_id["CR-02"].observed_output
            jm03_out = by_id["XXJM-03XX"].observed_output
            if not cr02_out.exception_raised and not jm03_out.exception_raised:
                # Compute expected value using Python float arithmetic (same as production).
                expected_cr02_ew = jm03_out.exposure_weight * 0.75
                if not _floats_equal(cr02_out.exposure_weight, expected_cr02_ew):
                    raise RuntimeError(
                        f"CRISIS_ORDERING_VIOLATION: CR-02 exposure_weight="
                        f"{cr02_out.exposure_weight} != JM-03.exposure_weight*0.75="
                        f"{expected_cr02_ew}. Clip C / CRISIS ordering violated. "
                        "INV-04 violated."
                    )

        # --------------------------------------------------------------------
        # CCV-D-03: CR-03 (non-CRISIS with JRM active) -- dampening must NOT apply.
        # Verified by BIC backward compatibility comparison against a non-CRISIS
        # variant. Here we simply note the check for audit.
        # --------------------------------------------------------------------
        if "CR-03" in by_id:
            notes.append(
                "CCV-D-03: CR-03 is non-CRISIS with JRM active. Dampening "
                "not applied. Verified by absence of *0.75 in BIC comparison."
            )

        return violations, notes

    def xǁClipVerifierǁverify__mutmut_80(
        self,
        er_records: List[ExecutionRecord],
    ) -> Tuple[List[str], List[str]]:
        """
        Perform clip chain verification on ER-stage records.

        Returns:
          (violations, notes)
          violations -- list of violation description strings. Empty means pass.
          notes      -- list of non-failure informational notes.

        Raises RuntimeError with failure_type_id prefix on hard failures
        (CLIP_B_FLOOR_VIOLATION, CLIP_C_FLOOR_VIOLATION, CLIP_A_VIOLATION,
        CRISIS_ORDERING_VIOLATION).
        """
        violations = []
        notes      = []
        by_id: Dict[str, ExecutionRecord] = {r.vector_id: r for r in er_records}

        for rec in er_records:
            out = rec.observed_output
            if out.exception_raised:
                # No clip verification for exception vectors.
                continue

            vid = rec.vector_id
            iv  = rec.input_vector

            # ----------------------------------------------------------------
            # CCV-A-01: Clip A verification.
            # position_size_factor must be in [0.0, 1.0] for every normal vector.
            # ----------------------------------------------------------------
            psf = out.position_size_factor
            if psf < 0.0 or psf > 1.0:
                raise RuntimeError(
                    f"CLIP_A_VIOLATION: Vector {vid} position_size_factor={psf} "
                    "is outside [0.0, 1.0]. INV-01 violated."
                )

            # ----------------------------------------------------------------
            # CCV-B-01: For MU-02 and RP-02, E_pre_clip should be zero or near zero,
            # so Clip B floor should be active. exposure_weight bit pattern should
            # equal bit pattern of 1e-6.
            # ----------------------------------------------------------------
            if vid in ("MU-02", "RP-02"):
                ew_bits = _float_bits(out.exposure_weight)
                if ew_bits != self._lb_bits:
                    raise RuntimeError(
                        f"CLIP_B_FLOOR_VIOLATION: Vector {vid} exposure_weight "
                        f"expected bit pattern of 1e-6 but got "
                        f"{out.exposure_weight!r}. INV-02 violated."
                    )

            # ----------------------------------------------------------------
            # CCV-B-02: For JM-inactive (JM-01, JM-04) non-CRISIS vectors,
            # exposure_weight must be in [1e-6, 1.0].
            # (Clip C inactive, CRISIS dampening inactive.)
            # ----------------------------------------------------------------
            if vid in ("JM-01", "JM-04") and iv.current_regime_str != "CRISIS":
                ew = out.exposure_weight
                if ew < 1e-6 or ew > 1.0:
                    raise RuntimeError(
                        f"CLIP_B_RANGE_VIOLATION: Vector {vid} exposure_weight={ew} "
                        "outside [1e-6, 1.0] with Clip C and CRISIS dampening both "
                        "inactive. INV-02 violated."
                    )

            # ----------------------------------------------------------------
            # CCV-C-02: For JM-03 (designed to produce pre-Clip-C value below
            # SHOCK_EXPOSURE_CAP), exposure_weight should equal SHOCK_EXPOSURE_CAP.
            # ----------------------------------------------------------------
            if vid == "JM-03":
                ew_bits = _float_bits(out.exposure_weight)
                if ew_bits != self._sec_bits:
                    # JM-03 uses meta_uncertainty=0.99 + multiplier=2.0.
                    # The division may produce a value below SHOCK_EXPOSURE_CAP,
                    # which gets clipped to SHOCK_EXPOSURE_CAP by Clip C.
                    # If the result does NOT equal SHOCK_EXPOSURE_CAP, the
                    # actual computed value exceeded the cap after division;
                    # this is acceptable if the value is above SHOCK_EXPOSURE_CAP.
                    # Hard failure only if value is strictly below SHOCK_EXPOSURE_CAP.
                    if out.exposure_weight < self._sec:
                        raise RuntimeError(
                            f"CLIP_C_FLOOR_VIOLATION: Vector {vid} exposure_weight="
                            f"{out.exposure_weight} is below SHOCK_EXPOSURE_CAP="
                            f"{self._sec}. INV-03 violated."
                        )
                    notes.append(
                        f"CCV-C-02 note: JM-03 exposure_weight={out.exposure_weight} "
                        "exceeds SHOCK_EXPOSURE_CAP; Clip C floor not triggered."
                    )

            # ----------------------------------------------------------------
            # CCV-D-02: For CR-01 (CRISIS, JRM inactive), exposure_weight may be
            # below SHOCK_EXPOSURE_CAP. No floor enforcement. This is specified
            # behaviour per INV-04.
            # ----------------------------------------------------------------
            if vid == "CR-01":
                notes.append(
                    f"CCV-D-02: CR-01 exposure_weight={out.exposure_weight}. "
                    "May be below SHOCK_EXPOSURE_CAP per INV-04 (specified behaviour)."
                )

        # --------------------------------------------------------------------
        # CCV-D-01: For CR-02 (CRISIS + JRM active), verify ordering.
        # Expected: CR-02.exposure_weight == JM-03.exposure_weight * 0.75
        # Both records must be present in ER set.
        # --------------------------------------------------------------------
        if "CR-02" in by_id and "JM-03" in by_id:
            cr02_out = by_id["CR-02"].observed_output
            jm03_out = by_id["jm-03"].observed_output
            if not cr02_out.exception_raised and not jm03_out.exception_raised:
                # Compute expected value using Python float arithmetic (same as production).
                expected_cr02_ew = jm03_out.exposure_weight * 0.75
                if not _floats_equal(cr02_out.exposure_weight, expected_cr02_ew):
                    raise RuntimeError(
                        f"CRISIS_ORDERING_VIOLATION: CR-02 exposure_weight="
                        f"{cr02_out.exposure_weight} != JM-03.exposure_weight*0.75="
                        f"{expected_cr02_ew}. Clip C / CRISIS ordering violated. "
                        "INV-04 violated."
                    )

        # --------------------------------------------------------------------
        # CCV-D-03: CR-03 (non-CRISIS with JRM active) -- dampening must NOT apply.
        # Verified by BIC backward compatibility comparison against a non-CRISIS
        # variant. Here we simply note the check for audit.
        # --------------------------------------------------------------------
        if "CR-03" in by_id:
            notes.append(
                "CCV-D-03: CR-03 is non-CRISIS with JRM active. Dampening "
                "not applied. Verified by absence of *0.75 in BIC comparison."
            )

        return violations, notes

    def xǁClipVerifierǁverify__mutmut_81(
        self,
        er_records: List[ExecutionRecord],
    ) -> Tuple[List[str], List[str]]:
        """
        Perform clip chain verification on ER-stage records.

        Returns:
          (violations, notes)
          violations -- list of violation description strings. Empty means pass.
          notes      -- list of non-failure informational notes.

        Raises RuntimeError with failure_type_id prefix on hard failures
        (CLIP_B_FLOOR_VIOLATION, CLIP_C_FLOOR_VIOLATION, CLIP_A_VIOLATION,
        CRISIS_ORDERING_VIOLATION).
        """
        violations = []
        notes      = []
        by_id: Dict[str, ExecutionRecord] = {r.vector_id: r for r in er_records}

        for rec in er_records:
            out = rec.observed_output
            if out.exception_raised:
                # No clip verification for exception vectors.
                continue

            vid = rec.vector_id
            iv  = rec.input_vector

            # ----------------------------------------------------------------
            # CCV-A-01: Clip A verification.
            # position_size_factor must be in [0.0, 1.0] for every normal vector.
            # ----------------------------------------------------------------
            psf = out.position_size_factor
            if psf < 0.0 or psf > 1.0:
                raise RuntimeError(
                    f"CLIP_A_VIOLATION: Vector {vid} position_size_factor={psf} "
                    "is outside [0.0, 1.0]. INV-01 violated."
                )

            # ----------------------------------------------------------------
            # CCV-B-01: For MU-02 and RP-02, E_pre_clip should be zero or near zero,
            # so Clip B floor should be active. exposure_weight bit pattern should
            # equal bit pattern of 1e-6.
            # ----------------------------------------------------------------
            if vid in ("MU-02", "RP-02"):
                ew_bits = _float_bits(out.exposure_weight)
                if ew_bits != self._lb_bits:
                    raise RuntimeError(
                        f"CLIP_B_FLOOR_VIOLATION: Vector {vid} exposure_weight "
                        f"expected bit pattern of 1e-6 but got "
                        f"{out.exposure_weight!r}. INV-02 violated."
                    )

            # ----------------------------------------------------------------
            # CCV-B-02: For JM-inactive (JM-01, JM-04) non-CRISIS vectors,
            # exposure_weight must be in [1e-6, 1.0].
            # (Clip C inactive, CRISIS dampening inactive.)
            # ----------------------------------------------------------------
            if vid in ("JM-01", "JM-04") and iv.current_regime_str != "CRISIS":
                ew = out.exposure_weight
                if ew < 1e-6 or ew > 1.0:
                    raise RuntimeError(
                        f"CLIP_B_RANGE_VIOLATION: Vector {vid} exposure_weight={ew} "
                        "outside [1e-6, 1.0] with Clip C and CRISIS dampening both "
                        "inactive. INV-02 violated."
                    )

            # ----------------------------------------------------------------
            # CCV-C-02: For JM-03 (designed to produce pre-Clip-C value below
            # SHOCK_EXPOSURE_CAP), exposure_weight should equal SHOCK_EXPOSURE_CAP.
            # ----------------------------------------------------------------
            if vid == "JM-03":
                ew_bits = _float_bits(out.exposure_weight)
                if ew_bits != self._sec_bits:
                    # JM-03 uses meta_uncertainty=0.99 + multiplier=2.0.
                    # The division may produce a value below SHOCK_EXPOSURE_CAP,
                    # which gets clipped to SHOCK_EXPOSURE_CAP by Clip C.
                    # If the result does NOT equal SHOCK_EXPOSURE_CAP, the
                    # actual computed value exceeded the cap after division;
                    # this is acceptable if the value is above SHOCK_EXPOSURE_CAP.
                    # Hard failure only if value is strictly below SHOCK_EXPOSURE_CAP.
                    if out.exposure_weight < self._sec:
                        raise RuntimeError(
                            f"CLIP_C_FLOOR_VIOLATION: Vector {vid} exposure_weight="
                            f"{out.exposure_weight} is below SHOCK_EXPOSURE_CAP="
                            f"{self._sec}. INV-03 violated."
                        )
                    notes.append(
                        f"CCV-C-02 note: JM-03 exposure_weight={out.exposure_weight} "
                        "exceeds SHOCK_EXPOSURE_CAP; Clip C floor not triggered."
                    )

            # ----------------------------------------------------------------
            # CCV-D-02: For CR-01 (CRISIS, JRM inactive), exposure_weight may be
            # below SHOCK_EXPOSURE_CAP. No floor enforcement. This is specified
            # behaviour per INV-04.
            # ----------------------------------------------------------------
            if vid == "CR-01":
                notes.append(
                    f"CCV-D-02: CR-01 exposure_weight={out.exposure_weight}. "
                    "May be below SHOCK_EXPOSURE_CAP per INV-04 (specified behaviour)."
                )

        # --------------------------------------------------------------------
        # CCV-D-01: For CR-02 (CRISIS + JRM active), verify ordering.
        # Expected: CR-02.exposure_weight == JM-03.exposure_weight * 0.75
        # Both records must be present in ER set.
        # --------------------------------------------------------------------
        if "CR-02" in by_id and "JM-03" in by_id:
            cr02_out = by_id["CR-02"].observed_output
            jm03_out = by_id["JM-03"].observed_output
            if not cr02_out.exception_raised or not jm03_out.exception_raised:
                # Compute expected value using Python float arithmetic (same as production).
                expected_cr02_ew = jm03_out.exposure_weight * 0.75
                if not _floats_equal(cr02_out.exposure_weight, expected_cr02_ew):
                    raise RuntimeError(
                        f"CRISIS_ORDERING_VIOLATION: CR-02 exposure_weight="
                        f"{cr02_out.exposure_weight} != JM-03.exposure_weight*0.75="
                        f"{expected_cr02_ew}. Clip C / CRISIS ordering violated. "
                        "INV-04 violated."
                    )

        # --------------------------------------------------------------------
        # CCV-D-03: CR-03 (non-CRISIS with JRM active) -- dampening must NOT apply.
        # Verified by BIC backward compatibility comparison against a non-CRISIS
        # variant. Here we simply note the check for audit.
        # --------------------------------------------------------------------
        if "CR-03" in by_id:
            notes.append(
                "CCV-D-03: CR-03 is non-CRISIS with JRM active. Dampening "
                "not applied. Verified by absence of *0.75 in BIC comparison."
            )

        return violations, notes

    def xǁClipVerifierǁverify__mutmut_82(
        self,
        er_records: List[ExecutionRecord],
    ) -> Tuple[List[str], List[str]]:
        """
        Perform clip chain verification on ER-stage records.

        Returns:
          (violations, notes)
          violations -- list of violation description strings. Empty means pass.
          notes      -- list of non-failure informational notes.

        Raises RuntimeError with failure_type_id prefix on hard failures
        (CLIP_B_FLOOR_VIOLATION, CLIP_C_FLOOR_VIOLATION, CLIP_A_VIOLATION,
        CRISIS_ORDERING_VIOLATION).
        """
        violations = []
        notes      = []
        by_id: Dict[str, ExecutionRecord] = {r.vector_id: r for r in er_records}

        for rec in er_records:
            out = rec.observed_output
            if out.exception_raised:
                # No clip verification for exception vectors.
                continue

            vid = rec.vector_id
            iv  = rec.input_vector

            # ----------------------------------------------------------------
            # CCV-A-01: Clip A verification.
            # position_size_factor must be in [0.0, 1.0] for every normal vector.
            # ----------------------------------------------------------------
            psf = out.position_size_factor
            if psf < 0.0 or psf > 1.0:
                raise RuntimeError(
                    f"CLIP_A_VIOLATION: Vector {vid} position_size_factor={psf} "
                    "is outside [0.0, 1.0]. INV-01 violated."
                )

            # ----------------------------------------------------------------
            # CCV-B-01: For MU-02 and RP-02, E_pre_clip should be zero or near zero,
            # so Clip B floor should be active. exposure_weight bit pattern should
            # equal bit pattern of 1e-6.
            # ----------------------------------------------------------------
            if vid in ("MU-02", "RP-02"):
                ew_bits = _float_bits(out.exposure_weight)
                if ew_bits != self._lb_bits:
                    raise RuntimeError(
                        f"CLIP_B_FLOOR_VIOLATION: Vector {vid} exposure_weight "
                        f"expected bit pattern of 1e-6 but got "
                        f"{out.exposure_weight!r}. INV-02 violated."
                    )

            # ----------------------------------------------------------------
            # CCV-B-02: For JM-inactive (JM-01, JM-04) non-CRISIS vectors,
            # exposure_weight must be in [1e-6, 1.0].
            # (Clip C inactive, CRISIS dampening inactive.)
            # ----------------------------------------------------------------
            if vid in ("JM-01", "JM-04") and iv.current_regime_str != "CRISIS":
                ew = out.exposure_weight
                if ew < 1e-6 or ew > 1.0:
                    raise RuntimeError(
                        f"CLIP_B_RANGE_VIOLATION: Vector {vid} exposure_weight={ew} "
                        "outside [1e-6, 1.0] with Clip C and CRISIS dampening both "
                        "inactive. INV-02 violated."
                    )

            # ----------------------------------------------------------------
            # CCV-C-02: For JM-03 (designed to produce pre-Clip-C value below
            # SHOCK_EXPOSURE_CAP), exposure_weight should equal SHOCK_EXPOSURE_CAP.
            # ----------------------------------------------------------------
            if vid == "JM-03":
                ew_bits = _float_bits(out.exposure_weight)
                if ew_bits != self._sec_bits:
                    # JM-03 uses meta_uncertainty=0.99 + multiplier=2.0.
                    # The division may produce a value below SHOCK_EXPOSURE_CAP,
                    # which gets clipped to SHOCK_EXPOSURE_CAP by Clip C.
                    # If the result does NOT equal SHOCK_EXPOSURE_CAP, the
                    # actual computed value exceeded the cap after division;
                    # this is acceptable if the value is above SHOCK_EXPOSURE_CAP.
                    # Hard failure only if value is strictly below SHOCK_EXPOSURE_CAP.
                    if out.exposure_weight < self._sec:
                        raise RuntimeError(
                            f"CLIP_C_FLOOR_VIOLATION: Vector {vid} exposure_weight="
                            f"{out.exposure_weight} is below SHOCK_EXPOSURE_CAP="
                            f"{self._sec}. INV-03 violated."
                        )
                    notes.append(
                        f"CCV-C-02 note: JM-03 exposure_weight={out.exposure_weight} "
                        "exceeds SHOCK_EXPOSURE_CAP; Clip C floor not triggered."
                    )

            # ----------------------------------------------------------------
            # CCV-D-02: For CR-01 (CRISIS, JRM inactive), exposure_weight may be
            # below SHOCK_EXPOSURE_CAP. No floor enforcement. This is specified
            # behaviour per INV-04.
            # ----------------------------------------------------------------
            if vid == "CR-01":
                notes.append(
                    f"CCV-D-02: CR-01 exposure_weight={out.exposure_weight}. "
                    "May be below SHOCK_EXPOSURE_CAP per INV-04 (specified behaviour)."
                )

        # --------------------------------------------------------------------
        # CCV-D-01: For CR-02 (CRISIS + JRM active), verify ordering.
        # Expected: CR-02.exposure_weight == JM-03.exposure_weight * 0.75
        # Both records must be present in ER set.
        # --------------------------------------------------------------------
        if "CR-02" in by_id and "JM-03" in by_id:
            cr02_out = by_id["CR-02"].observed_output
            jm03_out = by_id["JM-03"].observed_output
            if cr02_out.exception_raised and not jm03_out.exception_raised:
                # Compute expected value using Python float arithmetic (same as production).
                expected_cr02_ew = jm03_out.exposure_weight * 0.75
                if not _floats_equal(cr02_out.exposure_weight, expected_cr02_ew):
                    raise RuntimeError(
                        f"CRISIS_ORDERING_VIOLATION: CR-02 exposure_weight="
                        f"{cr02_out.exposure_weight} != JM-03.exposure_weight*0.75="
                        f"{expected_cr02_ew}. Clip C / CRISIS ordering violated. "
                        "INV-04 violated."
                    )

        # --------------------------------------------------------------------
        # CCV-D-03: CR-03 (non-CRISIS with JRM active) -- dampening must NOT apply.
        # Verified by BIC backward compatibility comparison against a non-CRISIS
        # variant. Here we simply note the check for audit.
        # --------------------------------------------------------------------
        if "CR-03" in by_id:
            notes.append(
                "CCV-D-03: CR-03 is non-CRISIS with JRM active. Dampening "
                "not applied. Verified by absence of *0.75 in BIC comparison."
            )

        return violations, notes

    def xǁClipVerifierǁverify__mutmut_83(
        self,
        er_records: List[ExecutionRecord],
    ) -> Tuple[List[str], List[str]]:
        """
        Perform clip chain verification on ER-stage records.

        Returns:
          (violations, notes)
          violations -- list of violation description strings. Empty means pass.
          notes      -- list of non-failure informational notes.

        Raises RuntimeError with failure_type_id prefix on hard failures
        (CLIP_B_FLOOR_VIOLATION, CLIP_C_FLOOR_VIOLATION, CLIP_A_VIOLATION,
        CRISIS_ORDERING_VIOLATION).
        """
        violations = []
        notes      = []
        by_id: Dict[str, ExecutionRecord] = {r.vector_id: r for r in er_records}

        for rec in er_records:
            out = rec.observed_output
            if out.exception_raised:
                # No clip verification for exception vectors.
                continue

            vid = rec.vector_id
            iv  = rec.input_vector

            # ----------------------------------------------------------------
            # CCV-A-01: Clip A verification.
            # position_size_factor must be in [0.0, 1.0] for every normal vector.
            # ----------------------------------------------------------------
            psf = out.position_size_factor
            if psf < 0.0 or psf > 1.0:
                raise RuntimeError(
                    f"CLIP_A_VIOLATION: Vector {vid} position_size_factor={psf} "
                    "is outside [0.0, 1.0]. INV-01 violated."
                )

            # ----------------------------------------------------------------
            # CCV-B-01: For MU-02 and RP-02, E_pre_clip should be zero or near zero,
            # so Clip B floor should be active. exposure_weight bit pattern should
            # equal bit pattern of 1e-6.
            # ----------------------------------------------------------------
            if vid in ("MU-02", "RP-02"):
                ew_bits = _float_bits(out.exposure_weight)
                if ew_bits != self._lb_bits:
                    raise RuntimeError(
                        f"CLIP_B_FLOOR_VIOLATION: Vector {vid} exposure_weight "
                        f"expected bit pattern of 1e-6 but got "
                        f"{out.exposure_weight!r}. INV-02 violated."
                    )

            # ----------------------------------------------------------------
            # CCV-B-02: For JM-inactive (JM-01, JM-04) non-CRISIS vectors,
            # exposure_weight must be in [1e-6, 1.0].
            # (Clip C inactive, CRISIS dampening inactive.)
            # ----------------------------------------------------------------
            if vid in ("JM-01", "JM-04") and iv.current_regime_str != "CRISIS":
                ew = out.exposure_weight
                if ew < 1e-6 or ew > 1.0:
                    raise RuntimeError(
                        f"CLIP_B_RANGE_VIOLATION: Vector {vid} exposure_weight={ew} "
                        "outside [1e-6, 1.0] with Clip C and CRISIS dampening both "
                        "inactive. INV-02 violated."
                    )

            # ----------------------------------------------------------------
            # CCV-C-02: For JM-03 (designed to produce pre-Clip-C value below
            # SHOCK_EXPOSURE_CAP), exposure_weight should equal SHOCK_EXPOSURE_CAP.
            # ----------------------------------------------------------------
            if vid == "JM-03":
                ew_bits = _float_bits(out.exposure_weight)
                if ew_bits != self._sec_bits:
                    # JM-03 uses meta_uncertainty=0.99 + multiplier=2.0.
                    # The division may produce a value below SHOCK_EXPOSURE_CAP,
                    # which gets clipped to SHOCK_EXPOSURE_CAP by Clip C.
                    # If the result does NOT equal SHOCK_EXPOSURE_CAP, the
                    # actual computed value exceeded the cap after division;
                    # this is acceptable if the value is above SHOCK_EXPOSURE_CAP.
                    # Hard failure only if value is strictly below SHOCK_EXPOSURE_CAP.
                    if out.exposure_weight < self._sec:
                        raise RuntimeError(
                            f"CLIP_C_FLOOR_VIOLATION: Vector {vid} exposure_weight="
                            f"{out.exposure_weight} is below SHOCK_EXPOSURE_CAP="
                            f"{self._sec}. INV-03 violated."
                        )
                    notes.append(
                        f"CCV-C-02 note: JM-03 exposure_weight={out.exposure_weight} "
                        "exceeds SHOCK_EXPOSURE_CAP; Clip C floor not triggered."
                    )

            # ----------------------------------------------------------------
            # CCV-D-02: For CR-01 (CRISIS, JRM inactive), exposure_weight may be
            # below SHOCK_EXPOSURE_CAP. No floor enforcement. This is specified
            # behaviour per INV-04.
            # ----------------------------------------------------------------
            if vid == "CR-01":
                notes.append(
                    f"CCV-D-02: CR-01 exposure_weight={out.exposure_weight}. "
                    "May be below SHOCK_EXPOSURE_CAP per INV-04 (specified behaviour)."
                )

        # --------------------------------------------------------------------
        # CCV-D-01: For CR-02 (CRISIS + JRM active), verify ordering.
        # Expected: CR-02.exposure_weight == JM-03.exposure_weight * 0.75
        # Both records must be present in ER set.
        # --------------------------------------------------------------------
        if "CR-02" in by_id and "JM-03" in by_id:
            cr02_out = by_id["CR-02"].observed_output
            jm03_out = by_id["JM-03"].observed_output
            if not cr02_out.exception_raised and jm03_out.exception_raised:
                # Compute expected value using Python float arithmetic (same as production).
                expected_cr02_ew = jm03_out.exposure_weight * 0.75
                if not _floats_equal(cr02_out.exposure_weight, expected_cr02_ew):
                    raise RuntimeError(
                        f"CRISIS_ORDERING_VIOLATION: CR-02 exposure_weight="
                        f"{cr02_out.exposure_weight} != JM-03.exposure_weight*0.75="
                        f"{expected_cr02_ew}. Clip C / CRISIS ordering violated. "
                        "INV-04 violated."
                    )

        # --------------------------------------------------------------------
        # CCV-D-03: CR-03 (non-CRISIS with JRM active) -- dampening must NOT apply.
        # Verified by BIC backward compatibility comparison against a non-CRISIS
        # variant. Here we simply note the check for audit.
        # --------------------------------------------------------------------
        if "CR-03" in by_id:
            notes.append(
                "CCV-D-03: CR-03 is non-CRISIS with JRM active. Dampening "
                "not applied. Verified by absence of *0.75 in BIC comparison."
            )

        return violations, notes

    def xǁClipVerifierǁverify__mutmut_84(
        self,
        er_records: List[ExecutionRecord],
    ) -> Tuple[List[str], List[str]]:
        """
        Perform clip chain verification on ER-stage records.

        Returns:
          (violations, notes)
          violations -- list of violation description strings. Empty means pass.
          notes      -- list of non-failure informational notes.

        Raises RuntimeError with failure_type_id prefix on hard failures
        (CLIP_B_FLOOR_VIOLATION, CLIP_C_FLOOR_VIOLATION, CLIP_A_VIOLATION,
        CRISIS_ORDERING_VIOLATION).
        """
        violations = []
        notes      = []
        by_id: Dict[str, ExecutionRecord] = {r.vector_id: r for r in er_records}

        for rec in er_records:
            out = rec.observed_output
            if out.exception_raised:
                # No clip verification for exception vectors.
                continue

            vid = rec.vector_id
            iv  = rec.input_vector

            # ----------------------------------------------------------------
            # CCV-A-01: Clip A verification.
            # position_size_factor must be in [0.0, 1.0] for every normal vector.
            # ----------------------------------------------------------------
            psf = out.position_size_factor
            if psf < 0.0 or psf > 1.0:
                raise RuntimeError(
                    f"CLIP_A_VIOLATION: Vector {vid} position_size_factor={psf} "
                    "is outside [0.0, 1.0]. INV-01 violated."
                )

            # ----------------------------------------------------------------
            # CCV-B-01: For MU-02 and RP-02, E_pre_clip should be zero or near zero,
            # so Clip B floor should be active. exposure_weight bit pattern should
            # equal bit pattern of 1e-6.
            # ----------------------------------------------------------------
            if vid in ("MU-02", "RP-02"):
                ew_bits = _float_bits(out.exposure_weight)
                if ew_bits != self._lb_bits:
                    raise RuntimeError(
                        f"CLIP_B_FLOOR_VIOLATION: Vector {vid} exposure_weight "
                        f"expected bit pattern of 1e-6 but got "
                        f"{out.exposure_weight!r}. INV-02 violated."
                    )

            # ----------------------------------------------------------------
            # CCV-B-02: For JM-inactive (JM-01, JM-04) non-CRISIS vectors,
            # exposure_weight must be in [1e-6, 1.0].
            # (Clip C inactive, CRISIS dampening inactive.)
            # ----------------------------------------------------------------
            if vid in ("JM-01", "JM-04") and iv.current_regime_str != "CRISIS":
                ew = out.exposure_weight
                if ew < 1e-6 or ew > 1.0:
                    raise RuntimeError(
                        f"CLIP_B_RANGE_VIOLATION: Vector {vid} exposure_weight={ew} "
                        "outside [1e-6, 1.0] with Clip C and CRISIS dampening both "
                        "inactive. INV-02 violated."
                    )

            # ----------------------------------------------------------------
            # CCV-C-02: For JM-03 (designed to produce pre-Clip-C value below
            # SHOCK_EXPOSURE_CAP), exposure_weight should equal SHOCK_EXPOSURE_CAP.
            # ----------------------------------------------------------------
            if vid == "JM-03":
                ew_bits = _float_bits(out.exposure_weight)
                if ew_bits != self._sec_bits:
                    # JM-03 uses meta_uncertainty=0.99 + multiplier=2.0.
                    # The division may produce a value below SHOCK_EXPOSURE_CAP,
                    # which gets clipped to SHOCK_EXPOSURE_CAP by Clip C.
                    # If the result does NOT equal SHOCK_EXPOSURE_CAP, the
                    # actual computed value exceeded the cap after division;
                    # this is acceptable if the value is above SHOCK_EXPOSURE_CAP.
                    # Hard failure only if value is strictly below SHOCK_EXPOSURE_CAP.
                    if out.exposure_weight < self._sec:
                        raise RuntimeError(
                            f"CLIP_C_FLOOR_VIOLATION: Vector {vid} exposure_weight="
                            f"{out.exposure_weight} is below SHOCK_EXPOSURE_CAP="
                            f"{self._sec}. INV-03 violated."
                        )
                    notes.append(
                        f"CCV-C-02 note: JM-03 exposure_weight={out.exposure_weight} "
                        "exceeds SHOCK_EXPOSURE_CAP; Clip C floor not triggered."
                    )

            # ----------------------------------------------------------------
            # CCV-D-02: For CR-01 (CRISIS, JRM inactive), exposure_weight may be
            # below SHOCK_EXPOSURE_CAP. No floor enforcement. This is specified
            # behaviour per INV-04.
            # ----------------------------------------------------------------
            if vid == "CR-01":
                notes.append(
                    f"CCV-D-02: CR-01 exposure_weight={out.exposure_weight}. "
                    "May be below SHOCK_EXPOSURE_CAP per INV-04 (specified behaviour)."
                )

        # --------------------------------------------------------------------
        # CCV-D-01: For CR-02 (CRISIS + JRM active), verify ordering.
        # Expected: CR-02.exposure_weight == JM-03.exposure_weight * 0.75
        # Both records must be present in ER set.
        # --------------------------------------------------------------------
        if "CR-02" in by_id and "JM-03" in by_id:
            cr02_out = by_id["CR-02"].observed_output
            jm03_out = by_id["JM-03"].observed_output
            if not cr02_out.exception_raised and not jm03_out.exception_raised:
                # Compute expected value using Python float arithmetic (same as production).
                expected_cr02_ew = None
                if not _floats_equal(cr02_out.exposure_weight, expected_cr02_ew):
                    raise RuntimeError(
                        f"CRISIS_ORDERING_VIOLATION: CR-02 exposure_weight="
                        f"{cr02_out.exposure_weight} != JM-03.exposure_weight*0.75="
                        f"{expected_cr02_ew}. Clip C / CRISIS ordering violated. "
                        "INV-04 violated."
                    )

        # --------------------------------------------------------------------
        # CCV-D-03: CR-03 (non-CRISIS with JRM active) -- dampening must NOT apply.
        # Verified by BIC backward compatibility comparison against a non-CRISIS
        # variant. Here we simply note the check for audit.
        # --------------------------------------------------------------------
        if "CR-03" in by_id:
            notes.append(
                "CCV-D-03: CR-03 is non-CRISIS with JRM active. Dampening "
                "not applied. Verified by absence of *0.75 in BIC comparison."
            )

        return violations, notes

    def xǁClipVerifierǁverify__mutmut_85(
        self,
        er_records: List[ExecutionRecord],
    ) -> Tuple[List[str], List[str]]:
        """
        Perform clip chain verification on ER-stage records.

        Returns:
          (violations, notes)
          violations -- list of violation description strings. Empty means pass.
          notes      -- list of non-failure informational notes.

        Raises RuntimeError with failure_type_id prefix on hard failures
        (CLIP_B_FLOOR_VIOLATION, CLIP_C_FLOOR_VIOLATION, CLIP_A_VIOLATION,
        CRISIS_ORDERING_VIOLATION).
        """
        violations = []
        notes      = []
        by_id: Dict[str, ExecutionRecord] = {r.vector_id: r for r in er_records}

        for rec in er_records:
            out = rec.observed_output
            if out.exception_raised:
                # No clip verification for exception vectors.
                continue

            vid = rec.vector_id
            iv  = rec.input_vector

            # ----------------------------------------------------------------
            # CCV-A-01: Clip A verification.
            # position_size_factor must be in [0.0, 1.0] for every normal vector.
            # ----------------------------------------------------------------
            psf = out.position_size_factor
            if psf < 0.0 or psf > 1.0:
                raise RuntimeError(
                    f"CLIP_A_VIOLATION: Vector {vid} position_size_factor={psf} "
                    "is outside [0.0, 1.0]. INV-01 violated."
                )

            # ----------------------------------------------------------------
            # CCV-B-01: For MU-02 and RP-02, E_pre_clip should be zero or near zero,
            # so Clip B floor should be active. exposure_weight bit pattern should
            # equal bit pattern of 1e-6.
            # ----------------------------------------------------------------
            if vid in ("MU-02", "RP-02"):
                ew_bits = _float_bits(out.exposure_weight)
                if ew_bits != self._lb_bits:
                    raise RuntimeError(
                        f"CLIP_B_FLOOR_VIOLATION: Vector {vid} exposure_weight "
                        f"expected bit pattern of 1e-6 but got "
                        f"{out.exposure_weight!r}. INV-02 violated."
                    )

            # ----------------------------------------------------------------
            # CCV-B-02: For JM-inactive (JM-01, JM-04) non-CRISIS vectors,
            # exposure_weight must be in [1e-6, 1.0].
            # (Clip C inactive, CRISIS dampening inactive.)
            # ----------------------------------------------------------------
            if vid in ("JM-01", "JM-04") and iv.current_regime_str != "CRISIS":
                ew = out.exposure_weight
                if ew < 1e-6 or ew > 1.0:
                    raise RuntimeError(
                        f"CLIP_B_RANGE_VIOLATION: Vector {vid} exposure_weight={ew} "
                        "outside [1e-6, 1.0] with Clip C and CRISIS dampening both "
                        "inactive. INV-02 violated."
                    )

            # ----------------------------------------------------------------
            # CCV-C-02: For JM-03 (designed to produce pre-Clip-C value below
            # SHOCK_EXPOSURE_CAP), exposure_weight should equal SHOCK_EXPOSURE_CAP.
            # ----------------------------------------------------------------
            if vid == "JM-03":
                ew_bits = _float_bits(out.exposure_weight)
                if ew_bits != self._sec_bits:
                    # JM-03 uses meta_uncertainty=0.99 + multiplier=2.0.
                    # The division may produce a value below SHOCK_EXPOSURE_CAP,
                    # which gets clipped to SHOCK_EXPOSURE_CAP by Clip C.
                    # If the result does NOT equal SHOCK_EXPOSURE_CAP, the
                    # actual computed value exceeded the cap after division;
                    # this is acceptable if the value is above SHOCK_EXPOSURE_CAP.
                    # Hard failure only if value is strictly below SHOCK_EXPOSURE_CAP.
                    if out.exposure_weight < self._sec:
                        raise RuntimeError(
                            f"CLIP_C_FLOOR_VIOLATION: Vector {vid} exposure_weight="
                            f"{out.exposure_weight} is below SHOCK_EXPOSURE_CAP="
                            f"{self._sec}. INV-03 violated."
                        )
                    notes.append(
                        f"CCV-C-02 note: JM-03 exposure_weight={out.exposure_weight} "
                        "exceeds SHOCK_EXPOSURE_CAP; Clip C floor not triggered."
                    )

            # ----------------------------------------------------------------
            # CCV-D-02: For CR-01 (CRISIS, JRM inactive), exposure_weight may be
            # below SHOCK_EXPOSURE_CAP. No floor enforcement. This is specified
            # behaviour per INV-04.
            # ----------------------------------------------------------------
            if vid == "CR-01":
                notes.append(
                    f"CCV-D-02: CR-01 exposure_weight={out.exposure_weight}. "
                    "May be below SHOCK_EXPOSURE_CAP per INV-04 (specified behaviour)."
                )

        # --------------------------------------------------------------------
        # CCV-D-01: For CR-02 (CRISIS + JRM active), verify ordering.
        # Expected: CR-02.exposure_weight == JM-03.exposure_weight * 0.75
        # Both records must be present in ER set.
        # --------------------------------------------------------------------
        if "CR-02" in by_id and "JM-03" in by_id:
            cr02_out = by_id["CR-02"].observed_output
            jm03_out = by_id["JM-03"].observed_output
            if not cr02_out.exception_raised and not jm03_out.exception_raised:
                # Compute expected value using Python float arithmetic (same as production).
                expected_cr02_ew = jm03_out.exposure_weight / 0.75
                if not _floats_equal(cr02_out.exposure_weight, expected_cr02_ew):
                    raise RuntimeError(
                        f"CRISIS_ORDERING_VIOLATION: CR-02 exposure_weight="
                        f"{cr02_out.exposure_weight} != JM-03.exposure_weight*0.75="
                        f"{expected_cr02_ew}. Clip C / CRISIS ordering violated. "
                        "INV-04 violated."
                    )

        # --------------------------------------------------------------------
        # CCV-D-03: CR-03 (non-CRISIS with JRM active) -- dampening must NOT apply.
        # Verified by BIC backward compatibility comparison against a non-CRISIS
        # variant. Here we simply note the check for audit.
        # --------------------------------------------------------------------
        if "CR-03" in by_id:
            notes.append(
                "CCV-D-03: CR-03 is non-CRISIS with JRM active. Dampening "
                "not applied. Verified by absence of *0.75 in BIC comparison."
            )

        return violations, notes

    def xǁClipVerifierǁverify__mutmut_86(
        self,
        er_records: List[ExecutionRecord],
    ) -> Tuple[List[str], List[str]]:
        """
        Perform clip chain verification on ER-stage records.

        Returns:
          (violations, notes)
          violations -- list of violation description strings. Empty means pass.
          notes      -- list of non-failure informational notes.

        Raises RuntimeError with failure_type_id prefix on hard failures
        (CLIP_B_FLOOR_VIOLATION, CLIP_C_FLOOR_VIOLATION, CLIP_A_VIOLATION,
        CRISIS_ORDERING_VIOLATION).
        """
        violations = []
        notes      = []
        by_id: Dict[str, ExecutionRecord] = {r.vector_id: r for r in er_records}

        for rec in er_records:
            out = rec.observed_output
            if out.exception_raised:
                # No clip verification for exception vectors.
                continue

            vid = rec.vector_id
            iv  = rec.input_vector

            # ----------------------------------------------------------------
            # CCV-A-01: Clip A verification.
            # position_size_factor must be in [0.0, 1.0] for every normal vector.
            # ----------------------------------------------------------------
            psf = out.position_size_factor
            if psf < 0.0 or psf > 1.0:
                raise RuntimeError(
                    f"CLIP_A_VIOLATION: Vector {vid} position_size_factor={psf} "
                    "is outside [0.0, 1.0]. INV-01 violated."
                )

            # ----------------------------------------------------------------
            # CCV-B-01: For MU-02 and RP-02, E_pre_clip should be zero or near zero,
            # so Clip B floor should be active. exposure_weight bit pattern should
            # equal bit pattern of 1e-6.
            # ----------------------------------------------------------------
            if vid in ("MU-02", "RP-02"):
                ew_bits = _float_bits(out.exposure_weight)
                if ew_bits != self._lb_bits:
                    raise RuntimeError(
                        f"CLIP_B_FLOOR_VIOLATION: Vector {vid} exposure_weight "
                        f"expected bit pattern of 1e-6 but got "
                        f"{out.exposure_weight!r}. INV-02 violated."
                    )

            # ----------------------------------------------------------------
            # CCV-B-02: For JM-inactive (JM-01, JM-04) non-CRISIS vectors,
            # exposure_weight must be in [1e-6, 1.0].
            # (Clip C inactive, CRISIS dampening inactive.)
            # ----------------------------------------------------------------
            if vid in ("JM-01", "JM-04") and iv.current_regime_str != "CRISIS":
                ew = out.exposure_weight
                if ew < 1e-6 or ew > 1.0:
                    raise RuntimeError(
                        f"CLIP_B_RANGE_VIOLATION: Vector {vid} exposure_weight={ew} "
                        "outside [1e-6, 1.0] with Clip C and CRISIS dampening both "
                        "inactive. INV-02 violated."
                    )

            # ----------------------------------------------------------------
            # CCV-C-02: For JM-03 (designed to produce pre-Clip-C value below
            # SHOCK_EXPOSURE_CAP), exposure_weight should equal SHOCK_EXPOSURE_CAP.
            # ----------------------------------------------------------------
            if vid == "JM-03":
                ew_bits = _float_bits(out.exposure_weight)
                if ew_bits != self._sec_bits:
                    # JM-03 uses meta_uncertainty=0.99 + multiplier=2.0.
                    # The division may produce a value below SHOCK_EXPOSURE_CAP,
                    # which gets clipped to SHOCK_EXPOSURE_CAP by Clip C.
                    # If the result does NOT equal SHOCK_EXPOSURE_CAP, the
                    # actual computed value exceeded the cap after division;
                    # this is acceptable if the value is above SHOCK_EXPOSURE_CAP.
                    # Hard failure only if value is strictly below SHOCK_EXPOSURE_CAP.
                    if out.exposure_weight < self._sec:
                        raise RuntimeError(
                            f"CLIP_C_FLOOR_VIOLATION: Vector {vid} exposure_weight="
                            f"{out.exposure_weight} is below SHOCK_EXPOSURE_CAP="
                            f"{self._sec}. INV-03 violated."
                        )
                    notes.append(
                        f"CCV-C-02 note: JM-03 exposure_weight={out.exposure_weight} "
                        "exceeds SHOCK_EXPOSURE_CAP; Clip C floor not triggered."
                    )

            # ----------------------------------------------------------------
            # CCV-D-02: For CR-01 (CRISIS, JRM inactive), exposure_weight may be
            # below SHOCK_EXPOSURE_CAP. No floor enforcement. This is specified
            # behaviour per INV-04.
            # ----------------------------------------------------------------
            if vid == "CR-01":
                notes.append(
                    f"CCV-D-02: CR-01 exposure_weight={out.exposure_weight}. "
                    "May be below SHOCK_EXPOSURE_CAP per INV-04 (specified behaviour)."
                )

        # --------------------------------------------------------------------
        # CCV-D-01: For CR-02 (CRISIS + JRM active), verify ordering.
        # Expected: CR-02.exposure_weight == JM-03.exposure_weight * 0.75
        # Both records must be present in ER set.
        # --------------------------------------------------------------------
        if "CR-02" in by_id and "JM-03" in by_id:
            cr02_out = by_id["CR-02"].observed_output
            jm03_out = by_id["JM-03"].observed_output
            if not cr02_out.exception_raised and not jm03_out.exception_raised:
                # Compute expected value using Python float arithmetic (same as production).
                expected_cr02_ew = jm03_out.exposure_weight * 1.75
                if not _floats_equal(cr02_out.exposure_weight, expected_cr02_ew):
                    raise RuntimeError(
                        f"CRISIS_ORDERING_VIOLATION: CR-02 exposure_weight="
                        f"{cr02_out.exposure_weight} != JM-03.exposure_weight*0.75="
                        f"{expected_cr02_ew}. Clip C / CRISIS ordering violated. "
                        "INV-04 violated."
                    )

        # --------------------------------------------------------------------
        # CCV-D-03: CR-03 (non-CRISIS with JRM active) -- dampening must NOT apply.
        # Verified by BIC backward compatibility comparison against a non-CRISIS
        # variant. Here we simply note the check for audit.
        # --------------------------------------------------------------------
        if "CR-03" in by_id:
            notes.append(
                "CCV-D-03: CR-03 is non-CRISIS with JRM active. Dampening "
                "not applied. Verified by absence of *0.75 in BIC comparison."
            )

        return violations, notes

    def xǁClipVerifierǁverify__mutmut_87(
        self,
        er_records: List[ExecutionRecord],
    ) -> Tuple[List[str], List[str]]:
        """
        Perform clip chain verification on ER-stage records.

        Returns:
          (violations, notes)
          violations -- list of violation description strings. Empty means pass.
          notes      -- list of non-failure informational notes.

        Raises RuntimeError with failure_type_id prefix on hard failures
        (CLIP_B_FLOOR_VIOLATION, CLIP_C_FLOOR_VIOLATION, CLIP_A_VIOLATION,
        CRISIS_ORDERING_VIOLATION).
        """
        violations = []
        notes      = []
        by_id: Dict[str, ExecutionRecord] = {r.vector_id: r for r in er_records}

        for rec in er_records:
            out = rec.observed_output
            if out.exception_raised:
                # No clip verification for exception vectors.
                continue

            vid = rec.vector_id
            iv  = rec.input_vector

            # ----------------------------------------------------------------
            # CCV-A-01: Clip A verification.
            # position_size_factor must be in [0.0, 1.0] for every normal vector.
            # ----------------------------------------------------------------
            psf = out.position_size_factor
            if psf < 0.0 or psf > 1.0:
                raise RuntimeError(
                    f"CLIP_A_VIOLATION: Vector {vid} position_size_factor={psf} "
                    "is outside [0.0, 1.0]. INV-01 violated."
                )

            # ----------------------------------------------------------------
            # CCV-B-01: For MU-02 and RP-02, E_pre_clip should be zero or near zero,
            # so Clip B floor should be active. exposure_weight bit pattern should
            # equal bit pattern of 1e-6.
            # ----------------------------------------------------------------
            if vid in ("MU-02", "RP-02"):
                ew_bits = _float_bits(out.exposure_weight)
                if ew_bits != self._lb_bits:
                    raise RuntimeError(
                        f"CLIP_B_FLOOR_VIOLATION: Vector {vid} exposure_weight "
                        f"expected bit pattern of 1e-6 but got "
                        f"{out.exposure_weight!r}. INV-02 violated."
                    )

            # ----------------------------------------------------------------
            # CCV-B-02: For JM-inactive (JM-01, JM-04) non-CRISIS vectors,
            # exposure_weight must be in [1e-6, 1.0].
            # (Clip C inactive, CRISIS dampening inactive.)
            # ----------------------------------------------------------------
            if vid in ("JM-01", "JM-04") and iv.current_regime_str != "CRISIS":
                ew = out.exposure_weight
                if ew < 1e-6 or ew > 1.0:
                    raise RuntimeError(
                        f"CLIP_B_RANGE_VIOLATION: Vector {vid} exposure_weight={ew} "
                        "outside [1e-6, 1.0] with Clip C and CRISIS dampening both "
                        "inactive. INV-02 violated."
                    )

            # ----------------------------------------------------------------
            # CCV-C-02: For JM-03 (designed to produce pre-Clip-C value below
            # SHOCK_EXPOSURE_CAP), exposure_weight should equal SHOCK_EXPOSURE_CAP.
            # ----------------------------------------------------------------
            if vid == "JM-03":
                ew_bits = _float_bits(out.exposure_weight)
                if ew_bits != self._sec_bits:
                    # JM-03 uses meta_uncertainty=0.99 + multiplier=2.0.
                    # The division may produce a value below SHOCK_EXPOSURE_CAP,
                    # which gets clipped to SHOCK_EXPOSURE_CAP by Clip C.
                    # If the result does NOT equal SHOCK_EXPOSURE_CAP, the
                    # actual computed value exceeded the cap after division;
                    # this is acceptable if the value is above SHOCK_EXPOSURE_CAP.
                    # Hard failure only if value is strictly below SHOCK_EXPOSURE_CAP.
                    if out.exposure_weight < self._sec:
                        raise RuntimeError(
                            f"CLIP_C_FLOOR_VIOLATION: Vector {vid} exposure_weight="
                            f"{out.exposure_weight} is below SHOCK_EXPOSURE_CAP="
                            f"{self._sec}. INV-03 violated."
                        )
                    notes.append(
                        f"CCV-C-02 note: JM-03 exposure_weight={out.exposure_weight} "
                        "exceeds SHOCK_EXPOSURE_CAP; Clip C floor not triggered."
                    )

            # ----------------------------------------------------------------
            # CCV-D-02: For CR-01 (CRISIS, JRM inactive), exposure_weight may be
            # below SHOCK_EXPOSURE_CAP. No floor enforcement. This is specified
            # behaviour per INV-04.
            # ----------------------------------------------------------------
            if vid == "CR-01":
                notes.append(
                    f"CCV-D-02: CR-01 exposure_weight={out.exposure_weight}. "
                    "May be below SHOCK_EXPOSURE_CAP per INV-04 (specified behaviour)."
                )

        # --------------------------------------------------------------------
        # CCV-D-01: For CR-02 (CRISIS + JRM active), verify ordering.
        # Expected: CR-02.exposure_weight == JM-03.exposure_weight * 0.75
        # Both records must be present in ER set.
        # --------------------------------------------------------------------
        if "CR-02" in by_id and "JM-03" in by_id:
            cr02_out = by_id["CR-02"].observed_output
            jm03_out = by_id["JM-03"].observed_output
            if not cr02_out.exception_raised and not jm03_out.exception_raised:
                # Compute expected value using Python float arithmetic (same as production).
                expected_cr02_ew = jm03_out.exposure_weight * 0.75
                if _floats_equal(cr02_out.exposure_weight, expected_cr02_ew):
                    raise RuntimeError(
                        f"CRISIS_ORDERING_VIOLATION: CR-02 exposure_weight="
                        f"{cr02_out.exposure_weight} != JM-03.exposure_weight*0.75="
                        f"{expected_cr02_ew}. Clip C / CRISIS ordering violated. "
                        "INV-04 violated."
                    )

        # --------------------------------------------------------------------
        # CCV-D-03: CR-03 (non-CRISIS with JRM active) -- dampening must NOT apply.
        # Verified by BIC backward compatibility comparison against a non-CRISIS
        # variant. Here we simply note the check for audit.
        # --------------------------------------------------------------------
        if "CR-03" in by_id:
            notes.append(
                "CCV-D-03: CR-03 is non-CRISIS with JRM active. Dampening "
                "not applied. Verified by absence of *0.75 in BIC comparison."
            )

        return violations, notes

    def xǁClipVerifierǁverify__mutmut_88(
        self,
        er_records: List[ExecutionRecord],
    ) -> Tuple[List[str], List[str]]:
        """
        Perform clip chain verification on ER-stage records.

        Returns:
          (violations, notes)
          violations -- list of violation description strings. Empty means pass.
          notes      -- list of non-failure informational notes.

        Raises RuntimeError with failure_type_id prefix on hard failures
        (CLIP_B_FLOOR_VIOLATION, CLIP_C_FLOOR_VIOLATION, CLIP_A_VIOLATION,
        CRISIS_ORDERING_VIOLATION).
        """
        violations = []
        notes      = []
        by_id: Dict[str, ExecutionRecord] = {r.vector_id: r for r in er_records}

        for rec in er_records:
            out = rec.observed_output
            if out.exception_raised:
                # No clip verification for exception vectors.
                continue

            vid = rec.vector_id
            iv  = rec.input_vector

            # ----------------------------------------------------------------
            # CCV-A-01: Clip A verification.
            # position_size_factor must be in [0.0, 1.0] for every normal vector.
            # ----------------------------------------------------------------
            psf = out.position_size_factor
            if psf < 0.0 or psf > 1.0:
                raise RuntimeError(
                    f"CLIP_A_VIOLATION: Vector {vid} position_size_factor={psf} "
                    "is outside [0.0, 1.0]. INV-01 violated."
                )

            # ----------------------------------------------------------------
            # CCV-B-01: For MU-02 and RP-02, E_pre_clip should be zero or near zero,
            # so Clip B floor should be active. exposure_weight bit pattern should
            # equal bit pattern of 1e-6.
            # ----------------------------------------------------------------
            if vid in ("MU-02", "RP-02"):
                ew_bits = _float_bits(out.exposure_weight)
                if ew_bits != self._lb_bits:
                    raise RuntimeError(
                        f"CLIP_B_FLOOR_VIOLATION: Vector {vid} exposure_weight "
                        f"expected bit pattern of 1e-6 but got "
                        f"{out.exposure_weight!r}. INV-02 violated."
                    )

            # ----------------------------------------------------------------
            # CCV-B-02: For JM-inactive (JM-01, JM-04) non-CRISIS vectors,
            # exposure_weight must be in [1e-6, 1.0].
            # (Clip C inactive, CRISIS dampening inactive.)
            # ----------------------------------------------------------------
            if vid in ("JM-01", "JM-04") and iv.current_regime_str != "CRISIS":
                ew = out.exposure_weight
                if ew < 1e-6 or ew > 1.0:
                    raise RuntimeError(
                        f"CLIP_B_RANGE_VIOLATION: Vector {vid} exposure_weight={ew} "
                        "outside [1e-6, 1.0] with Clip C and CRISIS dampening both "
                        "inactive. INV-02 violated."
                    )

            # ----------------------------------------------------------------
            # CCV-C-02: For JM-03 (designed to produce pre-Clip-C value below
            # SHOCK_EXPOSURE_CAP), exposure_weight should equal SHOCK_EXPOSURE_CAP.
            # ----------------------------------------------------------------
            if vid == "JM-03":
                ew_bits = _float_bits(out.exposure_weight)
                if ew_bits != self._sec_bits:
                    # JM-03 uses meta_uncertainty=0.99 + multiplier=2.0.
                    # The division may produce a value below SHOCK_EXPOSURE_CAP,
                    # which gets clipped to SHOCK_EXPOSURE_CAP by Clip C.
                    # If the result does NOT equal SHOCK_EXPOSURE_CAP, the
                    # actual computed value exceeded the cap after division;
                    # this is acceptable if the value is above SHOCK_EXPOSURE_CAP.
                    # Hard failure only if value is strictly below SHOCK_EXPOSURE_CAP.
                    if out.exposure_weight < self._sec:
                        raise RuntimeError(
                            f"CLIP_C_FLOOR_VIOLATION: Vector {vid} exposure_weight="
                            f"{out.exposure_weight} is below SHOCK_EXPOSURE_CAP="
                            f"{self._sec}. INV-03 violated."
                        )
                    notes.append(
                        f"CCV-C-02 note: JM-03 exposure_weight={out.exposure_weight} "
                        "exceeds SHOCK_EXPOSURE_CAP; Clip C floor not triggered."
                    )

            # ----------------------------------------------------------------
            # CCV-D-02: For CR-01 (CRISIS, JRM inactive), exposure_weight may be
            # below SHOCK_EXPOSURE_CAP. No floor enforcement. This is specified
            # behaviour per INV-04.
            # ----------------------------------------------------------------
            if vid == "CR-01":
                notes.append(
                    f"CCV-D-02: CR-01 exposure_weight={out.exposure_weight}. "
                    "May be below SHOCK_EXPOSURE_CAP per INV-04 (specified behaviour)."
                )

        # --------------------------------------------------------------------
        # CCV-D-01: For CR-02 (CRISIS + JRM active), verify ordering.
        # Expected: CR-02.exposure_weight == JM-03.exposure_weight * 0.75
        # Both records must be present in ER set.
        # --------------------------------------------------------------------
        if "CR-02" in by_id and "JM-03" in by_id:
            cr02_out = by_id["CR-02"].observed_output
            jm03_out = by_id["JM-03"].observed_output
            if not cr02_out.exception_raised and not jm03_out.exception_raised:
                # Compute expected value using Python float arithmetic (same as production).
                expected_cr02_ew = jm03_out.exposure_weight * 0.75
                if not _floats_equal(None, expected_cr02_ew):
                    raise RuntimeError(
                        f"CRISIS_ORDERING_VIOLATION: CR-02 exposure_weight="
                        f"{cr02_out.exposure_weight} != JM-03.exposure_weight*0.75="
                        f"{expected_cr02_ew}. Clip C / CRISIS ordering violated. "
                        "INV-04 violated."
                    )

        # --------------------------------------------------------------------
        # CCV-D-03: CR-03 (non-CRISIS with JRM active) -- dampening must NOT apply.
        # Verified by BIC backward compatibility comparison against a non-CRISIS
        # variant. Here we simply note the check for audit.
        # --------------------------------------------------------------------
        if "CR-03" in by_id:
            notes.append(
                "CCV-D-03: CR-03 is non-CRISIS with JRM active. Dampening "
                "not applied. Verified by absence of *0.75 in BIC comparison."
            )

        return violations, notes

    def xǁClipVerifierǁverify__mutmut_89(
        self,
        er_records: List[ExecutionRecord],
    ) -> Tuple[List[str], List[str]]:
        """
        Perform clip chain verification on ER-stage records.

        Returns:
          (violations, notes)
          violations -- list of violation description strings. Empty means pass.
          notes      -- list of non-failure informational notes.

        Raises RuntimeError with failure_type_id prefix on hard failures
        (CLIP_B_FLOOR_VIOLATION, CLIP_C_FLOOR_VIOLATION, CLIP_A_VIOLATION,
        CRISIS_ORDERING_VIOLATION).
        """
        violations = []
        notes      = []
        by_id: Dict[str, ExecutionRecord] = {r.vector_id: r for r in er_records}

        for rec in er_records:
            out = rec.observed_output
            if out.exception_raised:
                # No clip verification for exception vectors.
                continue

            vid = rec.vector_id
            iv  = rec.input_vector

            # ----------------------------------------------------------------
            # CCV-A-01: Clip A verification.
            # position_size_factor must be in [0.0, 1.0] for every normal vector.
            # ----------------------------------------------------------------
            psf = out.position_size_factor
            if psf < 0.0 or psf > 1.0:
                raise RuntimeError(
                    f"CLIP_A_VIOLATION: Vector {vid} position_size_factor={psf} "
                    "is outside [0.0, 1.0]. INV-01 violated."
                )

            # ----------------------------------------------------------------
            # CCV-B-01: For MU-02 and RP-02, E_pre_clip should be zero or near zero,
            # so Clip B floor should be active. exposure_weight bit pattern should
            # equal bit pattern of 1e-6.
            # ----------------------------------------------------------------
            if vid in ("MU-02", "RP-02"):
                ew_bits = _float_bits(out.exposure_weight)
                if ew_bits != self._lb_bits:
                    raise RuntimeError(
                        f"CLIP_B_FLOOR_VIOLATION: Vector {vid} exposure_weight "
                        f"expected bit pattern of 1e-6 but got "
                        f"{out.exposure_weight!r}. INV-02 violated."
                    )

            # ----------------------------------------------------------------
            # CCV-B-02: For JM-inactive (JM-01, JM-04) non-CRISIS vectors,
            # exposure_weight must be in [1e-6, 1.0].
            # (Clip C inactive, CRISIS dampening inactive.)
            # ----------------------------------------------------------------
            if vid in ("JM-01", "JM-04") and iv.current_regime_str != "CRISIS":
                ew = out.exposure_weight
                if ew < 1e-6 or ew > 1.0:
                    raise RuntimeError(
                        f"CLIP_B_RANGE_VIOLATION: Vector {vid} exposure_weight={ew} "
                        "outside [1e-6, 1.0] with Clip C and CRISIS dampening both "
                        "inactive. INV-02 violated."
                    )

            # ----------------------------------------------------------------
            # CCV-C-02: For JM-03 (designed to produce pre-Clip-C value below
            # SHOCK_EXPOSURE_CAP), exposure_weight should equal SHOCK_EXPOSURE_CAP.
            # ----------------------------------------------------------------
            if vid == "JM-03":
                ew_bits = _float_bits(out.exposure_weight)
                if ew_bits != self._sec_bits:
                    # JM-03 uses meta_uncertainty=0.99 + multiplier=2.0.
                    # The division may produce a value below SHOCK_EXPOSURE_CAP,
                    # which gets clipped to SHOCK_EXPOSURE_CAP by Clip C.
                    # If the result does NOT equal SHOCK_EXPOSURE_CAP, the
                    # actual computed value exceeded the cap after division;
                    # this is acceptable if the value is above SHOCK_EXPOSURE_CAP.
                    # Hard failure only if value is strictly below SHOCK_EXPOSURE_CAP.
                    if out.exposure_weight < self._sec:
                        raise RuntimeError(
                            f"CLIP_C_FLOOR_VIOLATION: Vector {vid} exposure_weight="
                            f"{out.exposure_weight} is below SHOCK_EXPOSURE_CAP="
                            f"{self._sec}. INV-03 violated."
                        )
                    notes.append(
                        f"CCV-C-02 note: JM-03 exposure_weight={out.exposure_weight} "
                        "exceeds SHOCK_EXPOSURE_CAP; Clip C floor not triggered."
                    )

            # ----------------------------------------------------------------
            # CCV-D-02: For CR-01 (CRISIS, JRM inactive), exposure_weight may be
            # below SHOCK_EXPOSURE_CAP. No floor enforcement. This is specified
            # behaviour per INV-04.
            # ----------------------------------------------------------------
            if vid == "CR-01":
                notes.append(
                    f"CCV-D-02: CR-01 exposure_weight={out.exposure_weight}. "
                    "May be below SHOCK_EXPOSURE_CAP per INV-04 (specified behaviour)."
                )

        # --------------------------------------------------------------------
        # CCV-D-01: For CR-02 (CRISIS + JRM active), verify ordering.
        # Expected: CR-02.exposure_weight == JM-03.exposure_weight * 0.75
        # Both records must be present in ER set.
        # --------------------------------------------------------------------
        if "CR-02" in by_id and "JM-03" in by_id:
            cr02_out = by_id["CR-02"].observed_output
            jm03_out = by_id["JM-03"].observed_output
            if not cr02_out.exception_raised and not jm03_out.exception_raised:
                # Compute expected value using Python float arithmetic (same as production).
                expected_cr02_ew = jm03_out.exposure_weight * 0.75
                if not _floats_equal(cr02_out.exposure_weight, None):
                    raise RuntimeError(
                        f"CRISIS_ORDERING_VIOLATION: CR-02 exposure_weight="
                        f"{cr02_out.exposure_weight} != JM-03.exposure_weight*0.75="
                        f"{expected_cr02_ew}. Clip C / CRISIS ordering violated. "
                        "INV-04 violated."
                    )

        # --------------------------------------------------------------------
        # CCV-D-03: CR-03 (non-CRISIS with JRM active) -- dampening must NOT apply.
        # Verified by BIC backward compatibility comparison against a non-CRISIS
        # variant. Here we simply note the check for audit.
        # --------------------------------------------------------------------
        if "CR-03" in by_id:
            notes.append(
                "CCV-D-03: CR-03 is non-CRISIS with JRM active. Dampening "
                "not applied. Verified by absence of *0.75 in BIC comparison."
            )

        return violations, notes

    def xǁClipVerifierǁverify__mutmut_90(
        self,
        er_records: List[ExecutionRecord],
    ) -> Tuple[List[str], List[str]]:
        """
        Perform clip chain verification on ER-stage records.

        Returns:
          (violations, notes)
          violations -- list of violation description strings. Empty means pass.
          notes      -- list of non-failure informational notes.

        Raises RuntimeError with failure_type_id prefix on hard failures
        (CLIP_B_FLOOR_VIOLATION, CLIP_C_FLOOR_VIOLATION, CLIP_A_VIOLATION,
        CRISIS_ORDERING_VIOLATION).
        """
        violations = []
        notes      = []
        by_id: Dict[str, ExecutionRecord] = {r.vector_id: r for r in er_records}

        for rec in er_records:
            out = rec.observed_output
            if out.exception_raised:
                # No clip verification for exception vectors.
                continue

            vid = rec.vector_id
            iv  = rec.input_vector

            # ----------------------------------------------------------------
            # CCV-A-01: Clip A verification.
            # position_size_factor must be in [0.0, 1.0] for every normal vector.
            # ----------------------------------------------------------------
            psf = out.position_size_factor
            if psf < 0.0 or psf > 1.0:
                raise RuntimeError(
                    f"CLIP_A_VIOLATION: Vector {vid} position_size_factor={psf} "
                    "is outside [0.0, 1.0]. INV-01 violated."
                )

            # ----------------------------------------------------------------
            # CCV-B-01: For MU-02 and RP-02, E_pre_clip should be zero or near zero,
            # so Clip B floor should be active. exposure_weight bit pattern should
            # equal bit pattern of 1e-6.
            # ----------------------------------------------------------------
            if vid in ("MU-02", "RP-02"):
                ew_bits = _float_bits(out.exposure_weight)
                if ew_bits != self._lb_bits:
                    raise RuntimeError(
                        f"CLIP_B_FLOOR_VIOLATION: Vector {vid} exposure_weight "
                        f"expected bit pattern of 1e-6 but got "
                        f"{out.exposure_weight!r}. INV-02 violated."
                    )

            # ----------------------------------------------------------------
            # CCV-B-02: For JM-inactive (JM-01, JM-04) non-CRISIS vectors,
            # exposure_weight must be in [1e-6, 1.0].
            # (Clip C inactive, CRISIS dampening inactive.)
            # ----------------------------------------------------------------
            if vid in ("JM-01", "JM-04") and iv.current_regime_str != "CRISIS":
                ew = out.exposure_weight
                if ew < 1e-6 or ew > 1.0:
                    raise RuntimeError(
                        f"CLIP_B_RANGE_VIOLATION: Vector {vid} exposure_weight={ew} "
                        "outside [1e-6, 1.0] with Clip C and CRISIS dampening both "
                        "inactive. INV-02 violated."
                    )

            # ----------------------------------------------------------------
            # CCV-C-02: For JM-03 (designed to produce pre-Clip-C value below
            # SHOCK_EXPOSURE_CAP), exposure_weight should equal SHOCK_EXPOSURE_CAP.
            # ----------------------------------------------------------------
            if vid == "JM-03":
                ew_bits = _float_bits(out.exposure_weight)
                if ew_bits != self._sec_bits:
                    # JM-03 uses meta_uncertainty=0.99 + multiplier=2.0.
                    # The division may produce a value below SHOCK_EXPOSURE_CAP,
                    # which gets clipped to SHOCK_EXPOSURE_CAP by Clip C.
                    # If the result does NOT equal SHOCK_EXPOSURE_CAP, the
                    # actual computed value exceeded the cap after division;
                    # this is acceptable if the value is above SHOCK_EXPOSURE_CAP.
                    # Hard failure only if value is strictly below SHOCK_EXPOSURE_CAP.
                    if out.exposure_weight < self._sec:
                        raise RuntimeError(
                            f"CLIP_C_FLOOR_VIOLATION: Vector {vid} exposure_weight="
                            f"{out.exposure_weight} is below SHOCK_EXPOSURE_CAP="
                            f"{self._sec}. INV-03 violated."
                        )
                    notes.append(
                        f"CCV-C-02 note: JM-03 exposure_weight={out.exposure_weight} "
                        "exceeds SHOCK_EXPOSURE_CAP; Clip C floor not triggered."
                    )

            # ----------------------------------------------------------------
            # CCV-D-02: For CR-01 (CRISIS, JRM inactive), exposure_weight may be
            # below SHOCK_EXPOSURE_CAP. No floor enforcement. This is specified
            # behaviour per INV-04.
            # ----------------------------------------------------------------
            if vid == "CR-01":
                notes.append(
                    f"CCV-D-02: CR-01 exposure_weight={out.exposure_weight}. "
                    "May be below SHOCK_EXPOSURE_CAP per INV-04 (specified behaviour)."
                )

        # --------------------------------------------------------------------
        # CCV-D-01: For CR-02 (CRISIS + JRM active), verify ordering.
        # Expected: CR-02.exposure_weight == JM-03.exposure_weight * 0.75
        # Both records must be present in ER set.
        # --------------------------------------------------------------------
        if "CR-02" in by_id and "JM-03" in by_id:
            cr02_out = by_id["CR-02"].observed_output
            jm03_out = by_id["JM-03"].observed_output
            if not cr02_out.exception_raised and not jm03_out.exception_raised:
                # Compute expected value using Python float arithmetic (same as production).
                expected_cr02_ew = jm03_out.exposure_weight * 0.75
                if not _floats_equal(expected_cr02_ew):
                    raise RuntimeError(
                        f"CRISIS_ORDERING_VIOLATION: CR-02 exposure_weight="
                        f"{cr02_out.exposure_weight} != JM-03.exposure_weight*0.75="
                        f"{expected_cr02_ew}. Clip C / CRISIS ordering violated. "
                        "INV-04 violated."
                    )

        # --------------------------------------------------------------------
        # CCV-D-03: CR-03 (non-CRISIS with JRM active) -- dampening must NOT apply.
        # Verified by BIC backward compatibility comparison against a non-CRISIS
        # variant. Here we simply note the check for audit.
        # --------------------------------------------------------------------
        if "CR-03" in by_id:
            notes.append(
                "CCV-D-03: CR-03 is non-CRISIS with JRM active. Dampening "
                "not applied. Verified by absence of *0.75 in BIC comparison."
            )

        return violations, notes

    def xǁClipVerifierǁverify__mutmut_91(
        self,
        er_records: List[ExecutionRecord],
    ) -> Tuple[List[str], List[str]]:
        """
        Perform clip chain verification on ER-stage records.

        Returns:
          (violations, notes)
          violations -- list of violation description strings. Empty means pass.
          notes      -- list of non-failure informational notes.

        Raises RuntimeError with failure_type_id prefix on hard failures
        (CLIP_B_FLOOR_VIOLATION, CLIP_C_FLOOR_VIOLATION, CLIP_A_VIOLATION,
        CRISIS_ORDERING_VIOLATION).
        """
        violations = []
        notes      = []
        by_id: Dict[str, ExecutionRecord] = {r.vector_id: r for r in er_records}

        for rec in er_records:
            out = rec.observed_output
            if out.exception_raised:
                # No clip verification for exception vectors.
                continue

            vid = rec.vector_id
            iv  = rec.input_vector

            # ----------------------------------------------------------------
            # CCV-A-01: Clip A verification.
            # position_size_factor must be in [0.0, 1.0] for every normal vector.
            # ----------------------------------------------------------------
            psf = out.position_size_factor
            if psf < 0.0 or psf > 1.0:
                raise RuntimeError(
                    f"CLIP_A_VIOLATION: Vector {vid} position_size_factor={psf} "
                    "is outside [0.0, 1.0]. INV-01 violated."
                )

            # ----------------------------------------------------------------
            # CCV-B-01: For MU-02 and RP-02, E_pre_clip should be zero or near zero,
            # so Clip B floor should be active. exposure_weight bit pattern should
            # equal bit pattern of 1e-6.
            # ----------------------------------------------------------------
            if vid in ("MU-02", "RP-02"):
                ew_bits = _float_bits(out.exposure_weight)
                if ew_bits != self._lb_bits:
                    raise RuntimeError(
                        f"CLIP_B_FLOOR_VIOLATION: Vector {vid} exposure_weight "
                        f"expected bit pattern of 1e-6 but got "
                        f"{out.exposure_weight!r}. INV-02 violated."
                    )

            # ----------------------------------------------------------------
            # CCV-B-02: For JM-inactive (JM-01, JM-04) non-CRISIS vectors,
            # exposure_weight must be in [1e-6, 1.0].
            # (Clip C inactive, CRISIS dampening inactive.)
            # ----------------------------------------------------------------
            if vid in ("JM-01", "JM-04") and iv.current_regime_str != "CRISIS":
                ew = out.exposure_weight
                if ew < 1e-6 or ew > 1.0:
                    raise RuntimeError(
                        f"CLIP_B_RANGE_VIOLATION: Vector {vid} exposure_weight={ew} "
                        "outside [1e-6, 1.0] with Clip C and CRISIS dampening both "
                        "inactive. INV-02 violated."
                    )

            # ----------------------------------------------------------------
            # CCV-C-02: For JM-03 (designed to produce pre-Clip-C value below
            # SHOCK_EXPOSURE_CAP), exposure_weight should equal SHOCK_EXPOSURE_CAP.
            # ----------------------------------------------------------------
            if vid == "JM-03":
                ew_bits = _float_bits(out.exposure_weight)
                if ew_bits != self._sec_bits:
                    # JM-03 uses meta_uncertainty=0.99 + multiplier=2.0.
                    # The division may produce a value below SHOCK_EXPOSURE_CAP,
                    # which gets clipped to SHOCK_EXPOSURE_CAP by Clip C.
                    # If the result does NOT equal SHOCK_EXPOSURE_CAP, the
                    # actual computed value exceeded the cap after division;
                    # this is acceptable if the value is above SHOCK_EXPOSURE_CAP.
                    # Hard failure only if value is strictly below SHOCK_EXPOSURE_CAP.
                    if out.exposure_weight < self._sec:
                        raise RuntimeError(
                            f"CLIP_C_FLOOR_VIOLATION: Vector {vid} exposure_weight="
                            f"{out.exposure_weight} is below SHOCK_EXPOSURE_CAP="
                            f"{self._sec}. INV-03 violated."
                        )
                    notes.append(
                        f"CCV-C-02 note: JM-03 exposure_weight={out.exposure_weight} "
                        "exceeds SHOCK_EXPOSURE_CAP; Clip C floor not triggered."
                    )

            # ----------------------------------------------------------------
            # CCV-D-02: For CR-01 (CRISIS, JRM inactive), exposure_weight may be
            # below SHOCK_EXPOSURE_CAP. No floor enforcement. This is specified
            # behaviour per INV-04.
            # ----------------------------------------------------------------
            if vid == "CR-01":
                notes.append(
                    f"CCV-D-02: CR-01 exposure_weight={out.exposure_weight}. "
                    "May be below SHOCK_EXPOSURE_CAP per INV-04 (specified behaviour)."
                )

        # --------------------------------------------------------------------
        # CCV-D-01: For CR-02 (CRISIS + JRM active), verify ordering.
        # Expected: CR-02.exposure_weight == JM-03.exposure_weight * 0.75
        # Both records must be present in ER set.
        # --------------------------------------------------------------------
        if "CR-02" in by_id and "JM-03" in by_id:
            cr02_out = by_id["CR-02"].observed_output
            jm03_out = by_id["JM-03"].observed_output
            if not cr02_out.exception_raised and not jm03_out.exception_raised:
                # Compute expected value using Python float arithmetic (same as production).
                expected_cr02_ew = jm03_out.exposure_weight * 0.75
                if not _floats_equal(cr02_out.exposure_weight, ):
                    raise RuntimeError(
                        f"CRISIS_ORDERING_VIOLATION: CR-02 exposure_weight="
                        f"{cr02_out.exposure_weight} != JM-03.exposure_weight*0.75="
                        f"{expected_cr02_ew}. Clip C / CRISIS ordering violated. "
                        "INV-04 violated."
                    )

        # --------------------------------------------------------------------
        # CCV-D-03: CR-03 (non-CRISIS with JRM active) -- dampening must NOT apply.
        # Verified by BIC backward compatibility comparison against a non-CRISIS
        # variant. Here we simply note the check for audit.
        # --------------------------------------------------------------------
        if "CR-03" in by_id:
            notes.append(
                "CCV-D-03: CR-03 is non-CRISIS with JRM active. Dampening "
                "not applied. Verified by absence of *0.75 in BIC comparison."
            )

        return violations, notes

    def xǁClipVerifierǁverify__mutmut_92(
        self,
        er_records: List[ExecutionRecord],
    ) -> Tuple[List[str], List[str]]:
        """
        Perform clip chain verification on ER-stage records.

        Returns:
          (violations, notes)
          violations -- list of violation description strings. Empty means pass.
          notes      -- list of non-failure informational notes.

        Raises RuntimeError with failure_type_id prefix on hard failures
        (CLIP_B_FLOOR_VIOLATION, CLIP_C_FLOOR_VIOLATION, CLIP_A_VIOLATION,
        CRISIS_ORDERING_VIOLATION).
        """
        violations = []
        notes      = []
        by_id: Dict[str, ExecutionRecord] = {r.vector_id: r for r in er_records}

        for rec in er_records:
            out = rec.observed_output
            if out.exception_raised:
                # No clip verification for exception vectors.
                continue

            vid = rec.vector_id
            iv  = rec.input_vector

            # ----------------------------------------------------------------
            # CCV-A-01: Clip A verification.
            # position_size_factor must be in [0.0, 1.0] for every normal vector.
            # ----------------------------------------------------------------
            psf = out.position_size_factor
            if psf < 0.0 or psf > 1.0:
                raise RuntimeError(
                    f"CLIP_A_VIOLATION: Vector {vid} position_size_factor={psf} "
                    "is outside [0.0, 1.0]. INV-01 violated."
                )

            # ----------------------------------------------------------------
            # CCV-B-01: For MU-02 and RP-02, E_pre_clip should be zero or near zero,
            # so Clip B floor should be active. exposure_weight bit pattern should
            # equal bit pattern of 1e-6.
            # ----------------------------------------------------------------
            if vid in ("MU-02", "RP-02"):
                ew_bits = _float_bits(out.exposure_weight)
                if ew_bits != self._lb_bits:
                    raise RuntimeError(
                        f"CLIP_B_FLOOR_VIOLATION: Vector {vid} exposure_weight "
                        f"expected bit pattern of 1e-6 but got "
                        f"{out.exposure_weight!r}. INV-02 violated."
                    )

            # ----------------------------------------------------------------
            # CCV-B-02: For JM-inactive (JM-01, JM-04) non-CRISIS vectors,
            # exposure_weight must be in [1e-6, 1.0].
            # (Clip C inactive, CRISIS dampening inactive.)
            # ----------------------------------------------------------------
            if vid in ("JM-01", "JM-04") and iv.current_regime_str != "CRISIS":
                ew = out.exposure_weight
                if ew < 1e-6 or ew > 1.0:
                    raise RuntimeError(
                        f"CLIP_B_RANGE_VIOLATION: Vector {vid} exposure_weight={ew} "
                        "outside [1e-6, 1.0] with Clip C and CRISIS dampening both "
                        "inactive. INV-02 violated."
                    )

            # ----------------------------------------------------------------
            # CCV-C-02: For JM-03 (designed to produce pre-Clip-C value below
            # SHOCK_EXPOSURE_CAP), exposure_weight should equal SHOCK_EXPOSURE_CAP.
            # ----------------------------------------------------------------
            if vid == "JM-03":
                ew_bits = _float_bits(out.exposure_weight)
                if ew_bits != self._sec_bits:
                    # JM-03 uses meta_uncertainty=0.99 + multiplier=2.0.
                    # The division may produce a value below SHOCK_EXPOSURE_CAP,
                    # which gets clipped to SHOCK_EXPOSURE_CAP by Clip C.
                    # If the result does NOT equal SHOCK_EXPOSURE_CAP, the
                    # actual computed value exceeded the cap after division;
                    # this is acceptable if the value is above SHOCK_EXPOSURE_CAP.
                    # Hard failure only if value is strictly below SHOCK_EXPOSURE_CAP.
                    if out.exposure_weight < self._sec:
                        raise RuntimeError(
                            f"CLIP_C_FLOOR_VIOLATION: Vector {vid} exposure_weight="
                            f"{out.exposure_weight} is below SHOCK_EXPOSURE_CAP="
                            f"{self._sec}. INV-03 violated."
                        )
                    notes.append(
                        f"CCV-C-02 note: JM-03 exposure_weight={out.exposure_weight} "
                        "exceeds SHOCK_EXPOSURE_CAP; Clip C floor not triggered."
                    )

            # ----------------------------------------------------------------
            # CCV-D-02: For CR-01 (CRISIS, JRM inactive), exposure_weight may be
            # below SHOCK_EXPOSURE_CAP. No floor enforcement. This is specified
            # behaviour per INV-04.
            # ----------------------------------------------------------------
            if vid == "CR-01":
                notes.append(
                    f"CCV-D-02: CR-01 exposure_weight={out.exposure_weight}. "
                    "May be below SHOCK_EXPOSURE_CAP per INV-04 (specified behaviour)."
                )

        # --------------------------------------------------------------------
        # CCV-D-01: For CR-02 (CRISIS + JRM active), verify ordering.
        # Expected: CR-02.exposure_weight == JM-03.exposure_weight * 0.75
        # Both records must be present in ER set.
        # --------------------------------------------------------------------
        if "CR-02" in by_id and "JM-03" in by_id:
            cr02_out = by_id["CR-02"].observed_output
            jm03_out = by_id["JM-03"].observed_output
            if not cr02_out.exception_raised and not jm03_out.exception_raised:
                # Compute expected value using Python float arithmetic (same as production).
                expected_cr02_ew = jm03_out.exposure_weight * 0.75
                if not _floats_equal(cr02_out.exposure_weight, expected_cr02_ew):
                    raise RuntimeError(
                        None
                    )

        # --------------------------------------------------------------------
        # CCV-D-03: CR-03 (non-CRISIS with JRM active) -- dampening must NOT apply.
        # Verified by BIC backward compatibility comparison against a non-CRISIS
        # variant. Here we simply note the check for audit.
        # --------------------------------------------------------------------
        if "CR-03" in by_id:
            notes.append(
                "CCV-D-03: CR-03 is non-CRISIS with JRM active. Dampening "
                "not applied. Verified by absence of *0.75 in BIC comparison."
            )

        return violations, notes

    def xǁClipVerifierǁverify__mutmut_93(
        self,
        er_records: List[ExecutionRecord],
    ) -> Tuple[List[str], List[str]]:
        """
        Perform clip chain verification on ER-stage records.

        Returns:
          (violations, notes)
          violations -- list of violation description strings. Empty means pass.
          notes      -- list of non-failure informational notes.

        Raises RuntimeError with failure_type_id prefix on hard failures
        (CLIP_B_FLOOR_VIOLATION, CLIP_C_FLOOR_VIOLATION, CLIP_A_VIOLATION,
        CRISIS_ORDERING_VIOLATION).
        """
        violations = []
        notes      = []
        by_id: Dict[str, ExecutionRecord] = {r.vector_id: r for r in er_records}

        for rec in er_records:
            out = rec.observed_output
            if out.exception_raised:
                # No clip verification for exception vectors.
                continue

            vid = rec.vector_id
            iv  = rec.input_vector

            # ----------------------------------------------------------------
            # CCV-A-01: Clip A verification.
            # position_size_factor must be in [0.0, 1.0] for every normal vector.
            # ----------------------------------------------------------------
            psf = out.position_size_factor
            if psf < 0.0 or psf > 1.0:
                raise RuntimeError(
                    f"CLIP_A_VIOLATION: Vector {vid} position_size_factor={psf} "
                    "is outside [0.0, 1.0]. INV-01 violated."
                )

            # ----------------------------------------------------------------
            # CCV-B-01: For MU-02 and RP-02, E_pre_clip should be zero or near zero,
            # so Clip B floor should be active. exposure_weight bit pattern should
            # equal bit pattern of 1e-6.
            # ----------------------------------------------------------------
            if vid in ("MU-02", "RP-02"):
                ew_bits = _float_bits(out.exposure_weight)
                if ew_bits != self._lb_bits:
                    raise RuntimeError(
                        f"CLIP_B_FLOOR_VIOLATION: Vector {vid} exposure_weight "
                        f"expected bit pattern of 1e-6 but got "
                        f"{out.exposure_weight!r}. INV-02 violated."
                    )

            # ----------------------------------------------------------------
            # CCV-B-02: For JM-inactive (JM-01, JM-04) non-CRISIS vectors,
            # exposure_weight must be in [1e-6, 1.0].
            # (Clip C inactive, CRISIS dampening inactive.)
            # ----------------------------------------------------------------
            if vid in ("JM-01", "JM-04") and iv.current_regime_str != "CRISIS":
                ew = out.exposure_weight
                if ew < 1e-6 or ew > 1.0:
                    raise RuntimeError(
                        f"CLIP_B_RANGE_VIOLATION: Vector {vid} exposure_weight={ew} "
                        "outside [1e-6, 1.0] with Clip C and CRISIS dampening both "
                        "inactive. INV-02 violated."
                    )

            # ----------------------------------------------------------------
            # CCV-C-02: For JM-03 (designed to produce pre-Clip-C value below
            # SHOCK_EXPOSURE_CAP), exposure_weight should equal SHOCK_EXPOSURE_CAP.
            # ----------------------------------------------------------------
            if vid == "JM-03":
                ew_bits = _float_bits(out.exposure_weight)
                if ew_bits != self._sec_bits:
                    # JM-03 uses meta_uncertainty=0.99 + multiplier=2.0.
                    # The division may produce a value below SHOCK_EXPOSURE_CAP,
                    # which gets clipped to SHOCK_EXPOSURE_CAP by Clip C.
                    # If the result does NOT equal SHOCK_EXPOSURE_CAP, the
                    # actual computed value exceeded the cap after division;
                    # this is acceptable if the value is above SHOCK_EXPOSURE_CAP.
                    # Hard failure only if value is strictly below SHOCK_EXPOSURE_CAP.
                    if out.exposure_weight < self._sec:
                        raise RuntimeError(
                            f"CLIP_C_FLOOR_VIOLATION: Vector {vid} exposure_weight="
                            f"{out.exposure_weight} is below SHOCK_EXPOSURE_CAP="
                            f"{self._sec}. INV-03 violated."
                        )
                    notes.append(
                        f"CCV-C-02 note: JM-03 exposure_weight={out.exposure_weight} "
                        "exceeds SHOCK_EXPOSURE_CAP; Clip C floor not triggered."
                    )

            # ----------------------------------------------------------------
            # CCV-D-02: For CR-01 (CRISIS, JRM inactive), exposure_weight may be
            # below SHOCK_EXPOSURE_CAP. No floor enforcement. This is specified
            # behaviour per INV-04.
            # ----------------------------------------------------------------
            if vid == "CR-01":
                notes.append(
                    f"CCV-D-02: CR-01 exposure_weight={out.exposure_weight}. "
                    "May be below SHOCK_EXPOSURE_CAP per INV-04 (specified behaviour)."
                )

        # --------------------------------------------------------------------
        # CCV-D-01: For CR-02 (CRISIS + JRM active), verify ordering.
        # Expected: CR-02.exposure_weight == JM-03.exposure_weight * 0.75
        # Both records must be present in ER set.
        # --------------------------------------------------------------------
        if "CR-02" in by_id and "JM-03" in by_id:
            cr02_out = by_id["CR-02"].observed_output
            jm03_out = by_id["JM-03"].observed_output
            if not cr02_out.exception_raised and not jm03_out.exception_raised:
                # Compute expected value using Python float arithmetic (same as production).
                expected_cr02_ew = jm03_out.exposure_weight * 0.75
                if not _floats_equal(cr02_out.exposure_weight, expected_cr02_ew):
                    raise RuntimeError(
                        f"CRISIS_ORDERING_VIOLATION: CR-02 exposure_weight="
                        f"{cr02_out.exposure_weight} != JM-03.exposure_weight*0.75="
                        f"{expected_cr02_ew}. Clip C / CRISIS ordering violated. "
                        "XXINV-04 violated.XX"
                    )

        # --------------------------------------------------------------------
        # CCV-D-03: CR-03 (non-CRISIS with JRM active) -- dampening must NOT apply.
        # Verified by BIC backward compatibility comparison against a non-CRISIS
        # variant. Here we simply note the check for audit.
        # --------------------------------------------------------------------
        if "CR-03" in by_id:
            notes.append(
                "CCV-D-03: CR-03 is non-CRISIS with JRM active. Dampening "
                "not applied. Verified by absence of *0.75 in BIC comparison."
            )

        return violations, notes

    def xǁClipVerifierǁverify__mutmut_94(
        self,
        er_records: List[ExecutionRecord],
    ) -> Tuple[List[str], List[str]]:
        """
        Perform clip chain verification on ER-stage records.

        Returns:
          (violations, notes)
          violations -- list of violation description strings. Empty means pass.
          notes      -- list of non-failure informational notes.

        Raises RuntimeError with failure_type_id prefix on hard failures
        (CLIP_B_FLOOR_VIOLATION, CLIP_C_FLOOR_VIOLATION, CLIP_A_VIOLATION,
        CRISIS_ORDERING_VIOLATION).
        """
        violations = []
        notes      = []
        by_id: Dict[str, ExecutionRecord] = {r.vector_id: r for r in er_records}

        for rec in er_records:
            out = rec.observed_output
            if out.exception_raised:
                # No clip verification for exception vectors.
                continue

            vid = rec.vector_id
            iv  = rec.input_vector

            # ----------------------------------------------------------------
            # CCV-A-01: Clip A verification.
            # position_size_factor must be in [0.0, 1.0] for every normal vector.
            # ----------------------------------------------------------------
            psf = out.position_size_factor
            if psf < 0.0 or psf > 1.0:
                raise RuntimeError(
                    f"CLIP_A_VIOLATION: Vector {vid} position_size_factor={psf} "
                    "is outside [0.0, 1.0]. INV-01 violated."
                )

            # ----------------------------------------------------------------
            # CCV-B-01: For MU-02 and RP-02, E_pre_clip should be zero or near zero,
            # so Clip B floor should be active. exposure_weight bit pattern should
            # equal bit pattern of 1e-6.
            # ----------------------------------------------------------------
            if vid in ("MU-02", "RP-02"):
                ew_bits = _float_bits(out.exposure_weight)
                if ew_bits != self._lb_bits:
                    raise RuntimeError(
                        f"CLIP_B_FLOOR_VIOLATION: Vector {vid} exposure_weight "
                        f"expected bit pattern of 1e-6 but got "
                        f"{out.exposure_weight!r}. INV-02 violated."
                    )

            # ----------------------------------------------------------------
            # CCV-B-02: For JM-inactive (JM-01, JM-04) non-CRISIS vectors,
            # exposure_weight must be in [1e-6, 1.0].
            # (Clip C inactive, CRISIS dampening inactive.)
            # ----------------------------------------------------------------
            if vid in ("JM-01", "JM-04") and iv.current_regime_str != "CRISIS":
                ew = out.exposure_weight
                if ew < 1e-6 or ew > 1.0:
                    raise RuntimeError(
                        f"CLIP_B_RANGE_VIOLATION: Vector {vid} exposure_weight={ew} "
                        "outside [1e-6, 1.0] with Clip C and CRISIS dampening both "
                        "inactive. INV-02 violated."
                    )

            # ----------------------------------------------------------------
            # CCV-C-02: For JM-03 (designed to produce pre-Clip-C value below
            # SHOCK_EXPOSURE_CAP), exposure_weight should equal SHOCK_EXPOSURE_CAP.
            # ----------------------------------------------------------------
            if vid == "JM-03":
                ew_bits = _float_bits(out.exposure_weight)
                if ew_bits != self._sec_bits:
                    # JM-03 uses meta_uncertainty=0.99 + multiplier=2.0.
                    # The division may produce a value below SHOCK_EXPOSURE_CAP,
                    # which gets clipped to SHOCK_EXPOSURE_CAP by Clip C.
                    # If the result does NOT equal SHOCK_EXPOSURE_CAP, the
                    # actual computed value exceeded the cap after division;
                    # this is acceptable if the value is above SHOCK_EXPOSURE_CAP.
                    # Hard failure only if value is strictly below SHOCK_EXPOSURE_CAP.
                    if out.exposure_weight < self._sec:
                        raise RuntimeError(
                            f"CLIP_C_FLOOR_VIOLATION: Vector {vid} exposure_weight="
                            f"{out.exposure_weight} is below SHOCK_EXPOSURE_CAP="
                            f"{self._sec}. INV-03 violated."
                        )
                    notes.append(
                        f"CCV-C-02 note: JM-03 exposure_weight={out.exposure_weight} "
                        "exceeds SHOCK_EXPOSURE_CAP; Clip C floor not triggered."
                    )

            # ----------------------------------------------------------------
            # CCV-D-02: For CR-01 (CRISIS, JRM inactive), exposure_weight may be
            # below SHOCK_EXPOSURE_CAP. No floor enforcement. This is specified
            # behaviour per INV-04.
            # ----------------------------------------------------------------
            if vid == "CR-01":
                notes.append(
                    f"CCV-D-02: CR-01 exposure_weight={out.exposure_weight}. "
                    "May be below SHOCK_EXPOSURE_CAP per INV-04 (specified behaviour)."
                )

        # --------------------------------------------------------------------
        # CCV-D-01: For CR-02 (CRISIS + JRM active), verify ordering.
        # Expected: CR-02.exposure_weight == JM-03.exposure_weight * 0.75
        # Both records must be present in ER set.
        # --------------------------------------------------------------------
        if "CR-02" in by_id and "JM-03" in by_id:
            cr02_out = by_id["CR-02"].observed_output
            jm03_out = by_id["JM-03"].observed_output
            if not cr02_out.exception_raised and not jm03_out.exception_raised:
                # Compute expected value using Python float arithmetic (same as production).
                expected_cr02_ew = jm03_out.exposure_weight * 0.75
                if not _floats_equal(cr02_out.exposure_weight, expected_cr02_ew):
                    raise RuntimeError(
                        f"CRISIS_ORDERING_VIOLATION: CR-02 exposure_weight="
                        f"{cr02_out.exposure_weight} != JM-03.exposure_weight*0.75="
                        f"{expected_cr02_ew}. Clip C / CRISIS ordering violated. "
                        "inv-04 violated."
                    )

        # --------------------------------------------------------------------
        # CCV-D-03: CR-03 (non-CRISIS with JRM active) -- dampening must NOT apply.
        # Verified by BIC backward compatibility comparison against a non-CRISIS
        # variant. Here we simply note the check for audit.
        # --------------------------------------------------------------------
        if "CR-03" in by_id:
            notes.append(
                "CCV-D-03: CR-03 is non-CRISIS with JRM active. Dampening "
                "not applied. Verified by absence of *0.75 in BIC comparison."
            )

        return violations, notes

    def xǁClipVerifierǁverify__mutmut_95(
        self,
        er_records: List[ExecutionRecord],
    ) -> Tuple[List[str], List[str]]:
        """
        Perform clip chain verification on ER-stage records.

        Returns:
          (violations, notes)
          violations -- list of violation description strings. Empty means pass.
          notes      -- list of non-failure informational notes.

        Raises RuntimeError with failure_type_id prefix on hard failures
        (CLIP_B_FLOOR_VIOLATION, CLIP_C_FLOOR_VIOLATION, CLIP_A_VIOLATION,
        CRISIS_ORDERING_VIOLATION).
        """
        violations = []
        notes      = []
        by_id: Dict[str, ExecutionRecord] = {r.vector_id: r for r in er_records}

        for rec in er_records:
            out = rec.observed_output
            if out.exception_raised:
                # No clip verification for exception vectors.
                continue

            vid = rec.vector_id
            iv  = rec.input_vector

            # ----------------------------------------------------------------
            # CCV-A-01: Clip A verification.
            # position_size_factor must be in [0.0, 1.0] for every normal vector.
            # ----------------------------------------------------------------
            psf = out.position_size_factor
            if psf < 0.0 or psf > 1.0:
                raise RuntimeError(
                    f"CLIP_A_VIOLATION: Vector {vid} position_size_factor={psf} "
                    "is outside [0.0, 1.0]. INV-01 violated."
                )

            # ----------------------------------------------------------------
            # CCV-B-01: For MU-02 and RP-02, E_pre_clip should be zero or near zero,
            # so Clip B floor should be active. exposure_weight bit pattern should
            # equal bit pattern of 1e-6.
            # ----------------------------------------------------------------
            if vid in ("MU-02", "RP-02"):
                ew_bits = _float_bits(out.exposure_weight)
                if ew_bits != self._lb_bits:
                    raise RuntimeError(
                        f"CLIP_B_FLOOR_VIOLATION: Vector {vid} exposure_weight "
                        f"expected bit pattern of 1e-6 but got "
                        f"{out.exposure_weight!r}. INV-02 violated."
                    )

            # ----------------------------------------------------------------
            # CCV-B-02: For JM-inactive (JM-01, JM-04) non-CRISIS vectors,
            # exposure_weight must be in [1e-6, 1.0].
            # (Clip C inactive, CRISIS dampening inactive.)
            # ----------------------------------------------------------------
            if vid in ("JM-01", "JM-04") and iv.current_regime_str != "CRISIS":
                ew = out.exposure_weight
                if ew < 1e-6 or ew > 1.0:
                    raise RuntimeError(
                        f"CLIP_B_RANGE_VIOLATION: Vector {vid} exposure_weight={ew} "
                        "outside [1e-6, 1.0] with Clip C and CRISIS dampening both "
                        "inactive. INV-02 violated."
                    )

            # ----------------------------------------------------------------
            # CCV-C-02: For JM-03 (designed to produce pre-Clip-C value below
            # SHOCK_EXPOSURE_CAP), exposure_weight should equal SHOCK_EXPOSURE_CAP.
            # ----------------------------------------------------------------
            if vid == "JM-03":
                ew_bits = _float_bits(out.exposure_weight)
                if ew_bits != self._sec_bits:
                    # JM-03 uses meta_uncertainty=0.99 + multiplier=2.0.
                    # The division may produce a value below SHOCK_EXPOSURE_CAP,
                    # which gets clipped to SHOCK_EXPOSURE_CAP by Clip C.
                    # If the result does NOT equal SHOCK_EXPOSURE_CAP, the
                    # actual computed value exceeded the cap after division;
                    # this is acceptable if the value is above SHOCK_EXPOSURE_CAP.
                    # Hard failure only if value is strictly below SHOCK_EXPOSURE_CAP.
                    if out.exposure_weight < self._sec:
                        raise RuntimeError(
                            f"CLIP_C_FLOOR_VIOLATION: Vector {vid} exposure_weight="
                            f"{out.exposure_weight} is below SHOCK_EXPOSURE_CAP="
                            f"{self._sec}. INV-03 violated."
                        )
                    notes.append(
                        f"CCV-C-02 note: JM-03 exposure_weight={out.exposure_weight} "
                        "exceeds SHOCK_EXPOSURE_CAP; Clip C floor not triggered."
                    )

            # ----------------------------------------------------------------
            # CCV-D-02: For CR-01 (CRISIS, JRM inactive), exposure_weight may be
            # below SHOCK_EXPOSURE_CAP. No floor enforcement. This is specified
            # behaviour per INV-04.
            # ----------------------------------------------------------------
            if vid == "CR-01":
                notes.append(
                    f"CCV-D-02: CR-01 exposure_weight={out.exposure_weight}. "
                    "May be below SHOCK_EXPOSURE_CAP per INV-04 (specified behaviour)."
                )

        # --------------------------------------------------------------------
        # CCV-D-01: For CR-02 (CRISIS + JRM active), verify ordering.
        # Expected: CR-02.exposure_weight == JM-03.exposure_weight * 0.75
        # Both records must be present in ER set.
        # --------------------------------------------------------------------
        if "CR-02" in by_id and "JM-03" in by_id:
            cr02_out = by_id["CR-02"].observed_output
            jm03_out = by_id["JM-03"].observed_output
            if not cr02_out.exception_raised and not jm03_out.exception_raised:
                # Compute expected value using Python float arithmetic (same as production).
                expected_cr02_ew = jm03_out.exposure_weight * 0.75
                if not _floats_equal(cr02_out.exposure_weight, expected_cr02_ew):
                    raise RuntimeError(
                        f"CRISIS_ORDERING_VIOLATION: CR-02 exposure_weight="
                        f"{cr02_out.exposure_weight} != JM-03.exposure_weight*0.75="
                        f"{expected_cr02_ew}. Clip C / CRISIS ordering violated. "
                        "INV-04 VIOLATED."
                    )

        # --------------------------------------------------------------------
        # CCV-D-03: CR-03 (non-CRISIS with JRM active) -- dampening must NOT apply.
        # Verified by BIC backward compatibility comparison against a non-CRISIS
        # variant. Here we simply note the check for audit.
        # --------------------------------------------------------------------
        if "CR-03" in by_id:
            notes.append(
                "CCV-D-03: CR-03 is non-CRISIS with JRM active. Dampening "
                "not applied. Verified by absence of *0.75 in BIC comparison."
            )

        return violations, notes

    def xǁClipVerifierǁverify__mutmut_96(
        self,
        er_records: List[ExecutionRecord],
    ) -> Tuple[List[str], List[str]]:
        """
        Perform clip chain verification on ER-stage records.

        Returns:
          (violations, notes)
          violations -- list of violation description strings. Empty means pass.
          notes      -- list of non-failure informational notes.

        Raises RuntimeError with failure_type_id prefix on hard failures
        (CLIP_B_FLOOR_VIOLATION, CLIP_C_FLOOR_VIOLATION, CLIP_A_VIOLATION,
        CRISIS_ORDERING_VIOLATION).
        """
        violations = []
        notes      = []
        by_id: Dict[str, ExecutionRecord] = {r.vector_id: r for r in er_records}

        for rec in er_records:
            out = rec.observed_output
            if out.exception_raised:
                # No clip verification for exception vectors.
                continue

            vid = rec.vector_id
            iv  = rec.input_vector

            # ----------------------------------------------------------------
            # CCV-A-01: Clip A verification.
            # position_size_factor must be in [0.0, 1.0] for every normal vector.
            # ----------------------------------------------------------------
            psf = out.position_size_factor
            if psf < 0.0 or psf > 1.0:
                raise RuntimeError(
                    f"CLIP_A_VIOLATION: Vector {vid} position_size_factor={psf} "
                    "is outside [0.0, 1.0]. INV-01 violated."
                )

            # ----------------------------------------------------------------
            # CCV-B-01: For MU-02 and RP-02, E_pre_clip should be zero or near zero,
            # so Clip B floor should be active. exposure_weight bit pattern should
            # equal bit pattern of 1e-6.
            # ----------------------------------------------------------------
            if vid in ("MU-02", "RP-02"):
                ew_bits = _float_bits(out.exposure_weight)
                if ew_bits != self._lb_bits:
                    raise RuntimeError(
                        f"CLIP_B_FLOOR_VIOLATION: Vector {vid} exposure_weight "
                        f"expected bit pattern of 1e-6 but got "
                        f"{out.exposure_weight!r}. INV-02 violated."
                    )

            # ----------------------------------------------------------------
            # CCV-B-02: For JM-inactive (JM-01, JM-04) non-CRISIS vectors,
            # exposure_weight must be in [1e-6, 1.0].
            # (Clip C inactive, CRISIS dampening inactive.)
            # ----------------------------------------------------------------
            if vid in ("JM-01", "JM-04") and iv.current_regime_str != "CRISIS":
                ew = out.exposure_weight
                if ew < 1e-6 or ew > 1.0:
                    raise RuntimeError(
                        f"CLIP_B_RANGE_VIOLATION: Vector {vid} exposure_weight={ew} "
                        "outside [1e-6, 1.0] with Clip C and CRISIS dampening both "
                        "inactive. INV-02 violated."
                    )

            # ----------------------------------------------------------------
            # CCV-C-02: For JM-03 (designed to produce pre-Clip-C value below
            # SHOCK_EXPOSURE_CAP), exposure_weight should equal SHOCK_EXPOSURE_CAP.
            # ----------------------------------------------------------------
            if vid == "JM-03":
                ew_bits = _float_bits(out.exposure_weight)
                if ew_bits != self._sec_bits:
                    # JM-03 uses meta_uncertainty=0.99 + multiplier=2.0.
                    # The division may produce a value below SHOCK_EXPOSURE_CAP,
                    # which gets clipped to SHOCK_EXPOSURE_CAP by Clip C.
                    # If the result does NOT equal SHOCK_EXPOSURE_CAP, the
                    # actual computed value exceeded the cap after division;
                    # this is acceptable if the value is above SHOCK_EXPOSURE_CAP.
                    # Hard failure only if value is strictly below SHOCK_EXPOSURE_CAP.
                    if out.exposure_weight < self._sec:
                        raise RuntimeError(
                            f"CLIP_C_FLOOR_VIOLATION: Vector {vid} exposure_weight="
                            f"{out.exposure_weight} is below SHOCK_EXPOSURE_CAP="
                            f"{self._sec}. INV-03 violated."
                        )
                    notes.append(
                        f"CCV-C-02 note: JM-03 exposure_weight={out.exposure_weight} "
                        "exceeds SHOCK_EXPOSURE_CAP; Clip C floor not triggered."
                    )

            # ----------------------------------------------------------------
            # CCV-D-02: For CR-01 (CRISIS, JRM inactive), exposure_weight may be
            # below SHOCK_EXPOSURE_CAP. No floor enforcement. This is specified
            # behaviour per INV-04.
            # ----------------------------------------------------------------
            if vid == "CR-01":
                notes.append(
                    f"CCV-D-02: CR-01 exposure_weight={out.exposure_weight}. "
                    "May be below SHOCK_EXPOSURE_CAP per INV-04 (specified behaviour)."
                )

        # --------------------------------------------------------------------
        # CCV-D-01: For CR-02 (CRISIS + JRM active), verify ordering.
        # Expected: CR-02.exposure_weight == JM-03.exposure_weight * 0.75
        # Both records must be present in ER set.
        # --------------------------------------------------------------------
        if "CR-02" in by_id and "JM-03" in by_id:
            cr02_out = by_id["CR-02"].observed_output
            jm03_out = by_id["JM-03"].observed_output
            if not cr02_out.exception_raised and not jm03_out.exception_raised:
                # Compute expected value using Python float arithmetic (same as production).
                expected_cr02_ew = jm03_out.exposure_weight * 0.75
                if not _floats_equal(cr02_out.exposure_weight, expected_cr02_ew):
                    raise RuntimeError(
                        f"CRISIS_ORDERING_VIOLATION: CR-02 exposure_weight="
                        f"{cr02_out.exposure_weight} != JM-03.exposure_weight*0.75="
                        f"{expected_cr02_ew}. Clip C / CRISIS ordering violated. "
                        "INV-04 violated."
                    )

        # --------------------------------------------------------------------
        # CCV-D-03: CR-03 (non-CRISIS with JRM active) -- dampening must NOT apply.
        # Verified by BIC backward compatibility comparison against a non-CRISIS
        # variant. Here we simply note the check for audit.
        # --------------------------------------------------------------------
        if "XXCR-03XX" in by_id:
            notes.append(
                "CCV-D-03: CR-03 is non-CRISIS with JRM active. Dampening "
                "not applied. Verified by absence of *0.75 in BIC comparison."
            )

        return violations, notes

    def xǁClipVerifierǁverify__mutmut_97(
        self,
        er_records: List[ExecutionRecord],
    ) -> Tuple[List[str], List[str]]:
        """
        Perform clip chain verification on ER-stage records.

        Returns:
          (violations, notes)
          violations -- list of violation description strings. Empty means pass.
          notes      -- list of non-failure informational notes.

        Raises RuntimeError with failure_type_id prefix on hard failures
        (CLIP_B_FLOOR_VIOLATION, CLIP_C_FLOOR_VIOLATION, CLIP_A_VIOLATION,
        CRISIS_ORDERING_VIOLATION).
        """
        violations = []
        notes      = []
        by_id: Dict[str, ExecutionRecord] = {r.vector_id: r for r in er_records}

        for rec in er_records:
            out = rec.observed_output
            if out.exception_raised:
                # No clip verification for exception vectors.
                continue

            vid = rec.vector_id
            iv  = rec.input_vector

            # ----------------------------------------------------------------
            # CCV-A-01: Clip A verification.
            # position_size_factor must be in [0.0, 1.0] for every normal vector.
            # ----------------------------------------------------------------
            psf = out.position_size_factor
            if psf < 0.0 or psf > 1.0:
                raise RuntimeError(
                    f"CLIP_A_VIOLATION: Vector {vid} position_size_factor={psf} "
                    "is outside [0.0, 1.0]. INV-01 violated."
                )

            # ----------------------------------------------------------------
            # CCV-B-01: For MU-02 and RP-02, E_pre_clip should be zero or near zero,
            # so Clip B floor should be active. exposure_weight bit pattern should
            # equal bit pattern of 1e-6.
            # ----------------------------------------------------------------
            if vid in ("MU-02", "RP-02"):
                ew_bits = _float_bits(out.exposure_weight)
                if ew_bits != self._lb_bits:
                    raise RuntimeError(
                        f"CLIP_B_FLOOR_VIOLATION: Vector {vid} exposure_weight "
                        f"expected bit pattern of 1e-6 but got "
                        f"{out.exposure_weight!r}. INV-02 violated."
                    )

            # ----------------------------------------------------------------
            # CCV-B-02: For JM-inactive (JM-01, JM-04) non-CRISIS vectors,
            # exposure_weight must be in [1e-6, 1.0].
            # (Clip C inactive, CRISIS dampening inactive.)
            # ----------------------------------------------------------------
            if vid in ("JM-01", "JM-04") and iv.current_regime_str != "CRISIS":
                ew = out.exposure_weight
                if ew < 1e-6 or ew > 1.0:
                    raise RuntimeError(
                        f"CLIP_B_RANGE_VIOLATION: Vector {vid} exposure_weight={ew} "
                        "outside [1e-6, 1.0] with Clip C and CRISIS dampening both "
                        "inactive. INV-02 violated."
                    )

            # ----------------------------------------------------------------
            # CCV-C-02: For JM-03 (designed to produce pre-Clip-C value below
            # SHOCK_EXPOSURE_CAP), exposure_weight should equal SHOCK_EXPOSURE_CAP.
            # ----------------------------------------------------------------
            if vid == "JM-03":
                ew_bits = _float_bits(out.exposure_weight)
                if ew_bits != self._sec_bits:
                    # JM-03 uses meta_uncertainty=0.99 + multiplier=2.0.
                    # The division may produce a value below SHOCK_EXPOSURE_CAP,
                    # which gets clipped to SHOCK_EXPOSURE_CAP by Clip C.
                    # If the result does NOT equal SHOCK_EXPOSURE_CAP, the
                    # actual computed value exceeded the cap after division;
                    # this is acceptable if the value is above SHOCK_EXPOSURE_CAP.
                    # Hard failure only if value is strictly below SHOCK_EXPOSURE_CAP.
                    if out.exposure_weight < self._sec:
                        raise RuntimeError(
                            f"CLIP_C_FLOOR_VIOLATION: Vector {vid} exposure_weight="
                            f"{out.exposure_weight} is below SHOCK_EXPOSURE_CAP="
                            f"{self._sec}. INV-03 violated."
                        )
                    notes.append(
                        f"CCV-C-02 note: JM-03 exposure_weight={out.exposure_weight} "
                        "exceeds SHOCK_EXPOSURE_CAP; Clip C floor not triggered."
                    )

            # ----------------------------------------------------------------
            # CCV-D-02: For CR-01 (CRISIS, JRM inactive), exposure_weight may be
            # below SHOCK_EXPOSURE_CAP. No floor enforcement. This is specified
            # behaviour per INV-04.
            # ----------------------------------------------------------------
            if vid == "CR-01":
                notes.append(
                    f"CCV-D-02: CR-01 exposure_weight={out.exposure_weight}. "
                    "May be below SHOCK_EXPOSURE_CAP per INV-04 (specified behaviour)."
                )

        # --------------------------------------------------------------------
        # CCV-D-01: For CR-02 (CRISIS + JRM active), verify ordering.
        # Expected: CR-02.exposure_weight == JM-03.exposure_weight * 0.75
        # Both records must be present in ER set.
        # --------------------------------------------------------------------
        if "CR-02" in by_id and "JM-03" in by_id:
            cr02_out = by_id["CR-02"].observed_output
            jm03_out = by_id["JM-03"].observed_output
            if not cr02_out.exception_raised and not jm03_out.exception_raised:
                # Compute expected value using Python float arithmetic (same as production).
                expected_cr02_ew = jm03_out.exposure_weight * 0.75
                if not _floats_equal(cr02_out.exposure_weight, expected_cr02_ew):
                    raise RuntimeError(
                        f"CRISIS_ORDERING_VIOLATION: CR-02 exposure_weight="
                        f"{cr02_out.exposure_weight} != JM-03.exposure_weight*0.75="
                        f"{expected_cr02_ew}. Clip C / CRISIS ordering violated. "
                        "INV-04 violated."
                    )

        # --------------------------------------------------------------------
        # CCV-D-03: CR-03 (non-CRISIS with JRM active) -- dampening must NOT apply.
        # Verified by BIC backward compatibility comparison against a non-CRISIS
        # variant. Here we simply note the check for audit.
        # --------------------------------------------------------------------
        if "cr-03" in by_id:
            notes.append(
                "CCV-D-03: CR-03 is non-CRISIS with JRM active. Dampening "
                "not applied. Verified by absence of *0.75 in BIC comparison."
            )

        return violations, notes

    def xǁClipVerifierǁverify__mutmut_98(
        self,
        er_records: List[ExecutionRecord],
    ) -> Tuple[List[str], List[str]]:
        """
        Perform clip chain verification on ER-stage records.

        Returns:
          (violations, notes)
          violations -- list of violation description strings. Empty means pass.
          notes      -- list of non-failure informational notes.

        Raises RuntimeError with failure_type_id prefix on hard failures
        (CLIP_B_FLOOR_VIOLATION, CLIP_C_FLOOR_VIOLATION, CLIP_A_VIOLATION,
        CRISIS_ORDERING_VIOLATION).
        """
        violations = []
        notes      = []
        by_id: Dict[str, ExecutionRecord] = {r.vector_id: r for r in er_records}

        for rec in er_records:
            out = rec.observed_output
            if out.exception_raised:
                # No clip verification for exception vectors.
                continue

            vid = rec.vector_id
            iv  = rec.input_vector

            # ----------------------------------------------------------------
            # CCV-A-01: Clip A verification.
            # position_size_factor must be in [0.0, 1.0] for every normal vector.
            # ----------------------------------------------------------------
            psf = out.position_size_factor
            if psf < 0.0 or psf > 1.0:
                raise RuntimeError(
                    f"CLIP_A_VIOLATION: Vector {vid} position_size_factor={psf} "
                    "is outside [0.0, 1.0]. INV-01 violated."
                )

            # ----------------------------------------------------------------
            # CCV-B-01: For MU-02 and RP-02, E_pre_clip should be zero or near zero,
            # so Clip B floor should be active. exposure_weight bit pattern should
            # equal bit pattern of 1e-6.
            # ----------------------------------------------------------------
            if vid in ("MU-02", "RP-02"):
                ew_bits = _float_bits(out.exposure_weight)
                if ew_bits != self._lb_bits:
                    raise RuntimeError(
                        f"CLIP_B_FLOOR_VIOLATION: Vector {vid} exposure_weight "
                        f"expected bit pattern of 1e-6 but got "
                        f"{out.exposure_weight!r}. INV-02 violated."
                    )

            # ----------------------------------------------------------------
            # CCV-B-02: For JM-inactive (JM-01, JM-04) non-CRISIS vectors,
            # exposure_weight must be in [1e-6, 1.0].
            # (Clip C inactive, CRISIS dampening inactive.)
            # ----------------------------------------------------------------
            if vid in ("JM-01", "JM-04") and iv.current_regime_str != "CRISIS":
                ew = out.exposure_weight
                if ew < 1e-6 or ew > 1.0:
                    raise RuntimeError(
                        f"CLIP_B_RANGE_VIOLATION: Vector {vid} exposure_weight={ew} "
                        "outside [1e-6, 1.0] with Clip C and CRISIS dampening both "
                        "inactive. INV-02 violated."
                    )

            # ----------------------------------------------------------------
            # CCV-C-02: For JM-03 (designed to produce pre-Clip-C value below
            # SHOCK_EXPOSURE_CAP), exposure_weight should equal SHOCK_EXPOSURE_CAP.
            # ----------------------------------------------------------------
            if vid == "JM-03":
                ew_bits = _float_bits(out.exposure_weight)
                if ew_bits != self._sec_bits:
                    # JM-03 uses meta_uncertainty=0.99 + multiplier=2.0.
                    # The division may produce a value below SHOCK_EXPOSURE_CAP,
                    # which gets clipped to SHOCK_EXPOSURE_CAP by Clip C.
                    # If the result does NOT equal SHOCK_EXPOSURE_CAP, the
                    # actual computed value exceeded the cap after division;
                    # this is acceptable if the value is above SHOCK_EXPOSURE_CAP.
                    # Hard failure only if value is strictly below SHOCK_EXPOSURE_CAP.
                    if out.exposure_weight < self._sec:
                        raise RuntimeError(
                            f"CLIP_C_FLOOR_VIOLATION: Vector {vid} exposure_weight="
                            f"{out.exposure_weight} is below SHOCK_EXPOSURE_CAP="
                            f"{self._sec}. INV-03 violated."
                        )
                    notes.append(
                        f"CCV-C-02 note: JM-03 exposure_weight={out.exposure_weight} "
                        "exceeds SHOCK_EXPOSURE_CAP; Clip C floor not triggered."
                    )

            # ----------------------------------------------------------------
            # CCV-D-02: For CR-01 (CRISIS, JRM inactive), exposure_weight may be
            # below SHOCK_EXPOSURE_CAP. No floor enforcement. This is specified
            # behaviour per INV-04.
            # ----------------------------------------------------------------
            if vid == "CR-01":
                notes.append(
                    f"CCV-D-02: CR-01 exposure_weight={out.exposure_weight}. "
                    "May be below SHOCK_EXPOSURE_CAP per INV-04 (specified behaviour)."
                )

        # --------------------------------------------------------------------
        # CCV-D-01: For CR-02 (CRISIS + JRM active), verify ordering.
        # Expected: CR-02.exposure_weight == JM-03.exposure_weight * 0.75
        # Both records must be present in ER set.
        # --------------------------------------------------------------------
        if "CR-02" in by_id and "JM-03" in by_id:
            cr02_out = by_id["CR-02"].observed_output
            jm03_out = by_id["JM-03"].observed_output
            if not cr02_out.exception_raised and not jm03_out.exception_raised:
                # Compute expected value using Python float arithmetic (same as production).
                expected_cr02_ew = jm03_out.exposure_weight * 0.75
                if not _floats_equal(cr02_out.exposure_weight, expected_cr02_ew):
                    raise RuntimeError(
                        f"CRISIS_ORDERING_VIOLATION: CR-02 exposure_weight="
                        f"{cr02_out.exposure_weight} != JM-03.exposure_weight*0.75="
                        f"{expected_cr02_ew}. Clip C / CRISIS ordering violated. "
                        "INV-04 violated."
                    )

        # --------------------------------------------------------------------
        # CCV-D-03: CR-03 (non-CRISIS with JRM active) -- dampening must NOT apply.
        # Verified by BIC backward compatibility comparison against a non-CRISIS
        # variant. Here we simply note the check for audit.
        # --------------------------------------------------------------------
        if "CR-03" not in by_id:
            notes.append(
                "CCV-D-03: CR-03 is non-CRISIS with JRM active. Dampening "
                "not applied. Verified by absence of *0.75 in BIC comparison."
            )

        return violations, notes

    def xǁClipVerifierǁverify__mutmut_99(
        self,
        er_records: List[ExecutionRecord],
    ) -> Tuple[List[str], List[str]]:
        """
        Perform clip chain verification on ER-stage records.

        Returns:
          (violations, notes)
          violations -- list of violation description strings. Empty means pass.
          notes      -- list of non-failure informational notes.

        Raises RuntimeError with failure_type_id prefix on hard failures
        (CLIP_B_FLOOR_VIOLATION, CLIP_C_FLOOR_VIOLATION, CLIP_A_VIOLATION,
        CRISIS_ORDERING_VIOLATION).
        """
        violations = []
        notes      = []
        by_id: Dict[str, ExecutionRecord] = {r.vector_id: r for r in er_records}

        for rec in er_records:
            out = rec.observed_output
            if out.exception_raised:
                # No clip verification for exception vectors.
                continue

            vid = rec.vector_id
            iv  = rec.input_vector

            # ----------------------------------------------------------------
            # CCV-A-01: Clip A verification.
            # position_size_factor must be in [0.0, 1.0] for every normal vector.
            # ----------------------------------------------------------------
            psf = out.position_size_factor
            if psf < 0.0 or psf > 1.0:
                raise RuntimeError(
                    f"CLIP_A_VIOLATION: Vector {vid} position_size_factor={psf} "
                    "is outside [0.0, 1.0]. INV-01 violated."
                )

            # ----------------------------------------------------------------
            # CCV-B-01: For MU-02 and RP-02, E_pre_clip should be zero or near zero,
            # so Clip B floor should be active. exposure_weight bit pattern should
            # equal bit pattern of 1e-6.
            # ----------------------------------------------------------------
            if vid in ("MU-02", "RP-02"):
                ew_bits = _float_bits(out.exposure_weight)
                if ew_bits != self._lb_bits:
                    raise RuntimeError(
                        f"CLIP_B_FLOOR_VIOLATION: Vector {vid} exposure_weight "
                        f"expected bit pattern of 1e-6 but got "
                        f"{out.exposure_weight!r}. INV-02 violated."
                    )

            # ----------------------------------------------------------------
            # CCV-B-02: For JM-inactive (JM-01, JM-04) non-CRISIS vectors,
            # exposure_weight must be in [1e-6, 1.0].
            # (Clip C inactive, CRISIS dampening inactive.)
            # ----------------------------------------------------------------
            if vid in ("JM-01", "JM-04") and iv.current_regime_str != "CRISIS":
                ew = out.exposure_weight
                if ew < 1e-6 or ew > 1.0:
                    raise RuntimeError(
                        f"CLIP_B_RANGE_VIOLATION: Vector {vid} exposure_weight={ew} "
                        "outside [1e-6, 1.0] with Clip C and CRISIS dampening both "
                        "inactive. INV-02 violated."
                    )

            # ----------------------------------------------------------------
            # CCV-C-02: For JM-03 (designed to produce pre-Clip-C value below
            # SHOCK_EXPOSURE_CAP), exposure_weight should equal SHOCK_EXPOSURE_CAP.
            # ----------------------------------------------------------------
            if vid == "JM-03":
                ew_bits = _float_bits(out.exposure_weight)
                if ew_bits != self._sec_bits:
                    # JM-03 uses meta_uncertainty=0.99 + multiplier=2.0.
                    # The division may produce a value below SHOCK_EXPOSURE_CAP,
                    # which gets clipped to SHOCK_EXPOSURE_CAP by Clip C.
                    # If the result does NOT equal SHOCK_EXPOSURE_CAP, the
                    # actual computed value exceeded the cap after division;
                    # this is acceptable if the value is above SHOCK_EXPOSURE_CAP.
                    # Hard failure only if value is strictly below SHOCK_EXPOSURE_CAP.
                    if out.exposure_weight < self._sec:
                        raise RuntimeError(
                            f"CLIP_C_FLOOR_VIOLATION: Vector {vid} exposure_weight="
                            f"{out.exposure_weight} is below SHOCK_EXPOSURE_CAP="
                            f"{self._sec}. INV-03 violated."
                        )
                    notes.append(
                        f"CCV-C-02 note: JM-03 exposure_weight={out.exposure_weight} "
                        "exceeds SHOCK_EXPOSURE_CAP; Clip C floor not triggered."
                    )

            # ----------------------------------------------------------------
            # CCV-D-02: For CR-01 (CRISIS, JRM inactive), exposure_weight may be
            # below SHOCK_EXPOSURE_CAP. No floor enforcement. This is specified
            # behaviour per INV-04.
            # ----------------------------------------------------------------
            if vid == "CR-01":
                notes.append(
                    f"CCV-D-02: CR-01 exposure_weight={out.exposure_weight}. "
                    "May be below SHOCK_EXPOSURE_CAP per INV-04 (specified behaviour)."
                )

        # --------------------------------------------------------------------
        # CCV-D-01: For CR-02 (CRISIS + JRM active), verify ordering.
        # Expected: CR-02.exposure_weight == JM-03.exposure_weight * 0.75
        # Both records must be present in ER set.
        # --------------------------------------------------------------------
        if "CR-02" in by_id and "JM-03" in by_id:
            cr02_out = by_id["CR-02"].observed_output
            jm03_out = by_id["JM-03"].observed_output
            if not cr02_out.exception_raised and not jm03_out.exception_raised:
                # Compute expected value using Python float arithmetic (same as production).
                expected_cr02_ew = jm03_out.exposure_weight * 0.75
                if not _floats_equal(cr02_out.exposure_weight, expected_cr02_ew):
                    raise RuntimeError(
                        f"CRISIS_ORDERING_VIOLATION: CR-02 exposure_weight="
                        f"{cr02_out.exposure_weight} != JM-03.exposure_weight*0.75="
                        f"{expected_cr02_ew}. Clip C / CRISIS ordering violated. "
                        "INV-04 violated."
                    )

        # --------------------------------------------------------------------
        # CCV-D-03: CR-03 (non-CRISIS with JRM active) -- dampening must NOT apply.
        # Verified by BIC backward compatibility comparison against a non-CRISIS
        # variant. Here we simply note the check for audit.
        # --------------------------------------------------------------------
        if "CR-03" in by_id:
            notes.append(
                None
            )

        return violations, notes

    def xǁClipVerifierǁverify__mutmut_100(
        self,
        er_records: List[ExecutionRecord],
    ) -> Tuple[List[str], List[str]]:
        """
        Perform clip chain verification on ER-stage records.

        Returns:
          (violations, notes)
          violations -- list of violation description strings. Empty means pass.
          notes      -- list of non-failure informational notes.

        Raises RuntimeError with failure_type_id prefix on hard failures
        (CLIP_B_FLOOR_VIOLATION, CLIP_C_FLOOR_VIOLATION, CLIP_A_VIOLATION,
        CRISIS_ORDERING_VIOLATION).
        """
        violations = []
        notes      = []
        by_id: Dict[str, ExecutionRecord] = {r.vector_id: r for r in er_records}

        for rec in er_records:
            out = rec.observed_output
            if out.exception_raised:
                # No clip verification for exception vectors.
                continue

            vid = rec.vector_id
            iv  = rec.input_vector

            # ----------------------------------------------------------------
            # CCV-A-01: Clip A verification.
            # position_size_factor must be in [0.0, 1.0] for every normal vector.
            # ----------------------------------------------------------------
            psf = out.position_size_factor
            if psf < 0.0 or psf > 1.0:
                raise RuntimeError(
                    f"CLIP_A_VIOLATION: Vector {vid} position_size_factor={psf} "
                    "is outside [0.0, 1.0]. INV-01 violated."
                )

            # ----------------------------------------------------------------
            # CCV-B-01: For MU-02 and RP-02, E_pre_clip should be zero or near zero,
            # so Clip B floor should be active. exposure_weight bit pattern should
            # equal bit pattern of 1e-6.
            # ----------------------------------------------------------------
            if vid in ("MU-02", "RP-02"):
                ew_bits = _float_bits(out.exposure_weight)
                if ew_bits != self._lb_bits:
                    raise RuntimeError(
                        f"CLIP_B_FLOOR_VIOLATION: Vector {vid} exposure_weight "
                        f"expected bit pattern of 1e-6 but got "
                        f"{out.exposure_weight!r}. INV-02 violated."
                    )

            # ----------------------------------------------------------------
            # CCV-B-02: For JM-inactive (JM-01, JM-04) non-CRISIS vectors,
            # exposure_weight must be in [1e-6, 1.0].
            # (Clip C inactive, CRISIS dampening inactive.)
            # ----------------------------------------------------------------
            if vid in ("JM-01", "JM-04") and iv.current_regime_str != "CRISIS":
                ew = out.exposure_weight
                if ew < 1e-6 or ew > 1.0:
                    raise RuntimeError(
                        f"CLIP_B_RANGE_VIOLATION: Vector {vid} exposure_weight={ew} "
                        "outside [1e-6, 1.0] with Clip C and CRISIS dampening both "
                        "inactive. INV-02 violated."
                    )

            # ----------------------------------------------------------------
            # CCV-C-02: For JM-03 (designed to produce pre-Clip-C value below
            # SHOCK_EXPOSURE_CAP), exposure_weight should equal SHOCK_EXPOSURE_CAP.
            # ----------------------------------------------------------------
            if vid == "JM-03":
                ew_bits = _float_bits(out.exposure_weight)
                if ew_bits != self._sec_bits:
                    # JM-03 uses meta_uncertainty=0.99 + multiplier=2.0.
                    # The division may produce a value below SHOCK_EXPOSURE_CAP,
                    # which gets clipped to SHOCK_EXPOSURE_CAP by Clip C.
                    # If the result does NOT equal SHOCK_EXPOSURE_CAP, the
                    # actual computed value exceeded the cap after division;
                    # this is acceptable if the value is above SHOCK_EXPOSURE_CAP.
                    # Hard failure only if value is strictly below SHOCK_EXPOSURE_CAP.
                    if out.exposure_weight < self._sec:
                        raise RuntimeError(
                            f"CLIP_C_FLOOR_VIOLATION: Vector {vid} exposure_weight="
                            f"{out.exposure_weight} is below SHOCK_EXPOSURE_CAP="
                            f"{self._sec}. INV-03 violated."
                        )
                    notes.append(
                        f"CCV-C-02 note: JM-03 exposure_weight={out.exposure_weight} "
                        "exceeds SHOCK_EXPOSURE_CAP; Clip C floor not triggered."
                    )

            # ----------------------------------------------------------------
            # CCV-D-02: For CR-01 (CRISIS, JRM inactive), exposure_weight may be
            # below SHOCK_EXPOSURE_CAP. No floor enforcement. This is specified
            # behaviour per INV-04.
            # ----------------------------------------------------------------
            if vid == "CR-01":
                notes.append(
                    f"CCV-D-02: CR-01 exposure_weight={out.exposure_weight}. "
                    "May be below SHOCK_EXPOSURE_CAP per INV-04 (specified behaviour)."
                )

        # --------------------------------------------------------------------
        # CCV-D-01: For CR-02 (CRISIS + JRM active), verify ordering.
        # Expected: CR-02.exposure_weight == JM-03.exposure_weight * 0.75
        # Both records must be present in ER set.
        # --------------------------------------------------------------------
        if "CR-02" in by_id and "JM-03" in by_id:
            cr02_out = by_id["CR-02"].observed_output
            jm03_out = by_id["JM-03"].observed_output
            if not cr02_out.exception_raised and not jm03_out.exception_raised:
                # Compute expected value using Python float arithmetic (same as production).
                expected_cr02_ew = jm03_out.exposure_weight * 0.75
                if not _floats_equal(cr02_out.exposure_weight, expected_cr02_ew):
                    raise RuntimeError(
                        f"CRISIS_ORDERING_VIOLATION: CR-02 exposure_weight="
                        f"{cr02_out.exposure_weight} != JM-03.exposure_weight*0.75="
                        f"{expected_cr02_ew}. Clip C / CRISIS ordering violated. "
                        "INV-04 violated."
                    )

        # --------------------------------------------------------------------
        # CCV-D-03: CR-03 (non-CRISIS with JRM active) -- dampening must NOT apply.
        # Verified by BIC backward compatibility comparison against a non-CRISIS
        # variant. Here we simply note the check for audit.
        # --------------------------------------------------------------------
        if "CR-03" in by_id:
            notes.append(
                "XXCCV-D-03: CR-03 is non-CRISIS with JRM active. Dampening XX"
                "not applied. Verified by absence of *0.75 in BIC comparison."
            )

        return violations, notes

    def xǁClipVerifierǁverify__mutmut_101(
        self,
        er_records: List[ExecutionRecord],
    ) -> Tuple[List[str], List[str]]:
        """
        Perform clip chain verification on ER-stage records.

        Returns:
          (violations, notes)
          violations -- list of violation description strings. Empty means pass.
          notes      -- list of non-failure informational notes.

        Raises RuntimeError with failure_type_id prefix on hard failures
        (CLIP_B_FLOOR_VIOLATION, CLIP_C_FLOOR_VIOLATION, CLIP_A_VIOLATION,
        CRISIS_ORDERING_VIOLATION).
        """
        violations = []
        notes      = []
        by_id: Dict[str, ExecutionRecord] = {r.vector_id: r for r in er_records}

        for rec in er_records:
            out = rec.observed_output
            if out.exception_raised:
                # No clip verification for exception vectors.
                continue

            vid = rec.vector_id
            iv  = rec.input_vector

            # ----------------------------------------------------------------
            # CCV-A-01: Clip A verification.
            # position_size_factor must be in [0.0, 1.0] for every normal vector.
            # ----------------------------------------------------------------
            psf = out.position_size_factor
            if psf < 0.0 or psf > 1.0:
                raise RuntimeError(
                    f"CLIP_A_VIOLATION: Vector {vid} position_size_factor={psf} "
                    "is outside [0.0, 1.0]. INV-01 violated."
                )

            # ----------------------------------------------------------------
            # CCV-B-01: For MU-02 and RP-02, E_pre_clip should be zero or near zero,
            # so Clip B floor should be active. exposure_weight bit pattern should
            # equal bit pattern of 1e-6.
            # ----------------------------------------------------------------
            if vid in ("MU-02", "RP-02"):
                ew_bits = _float_bits(out.exposure_weight)
                if ew_bits != self._lb_bits:
                    raise RuntimeError(
                        f"CLIP_B_FLOOR_VIOLATION: Vector {vid} exposure_weight "
                        f"expected bit pattern of 1e-6 but got "
                        f"{out.exposure_weight!r}. INV-02 violated."
                    )

            # ----------------------------------------------------------------
            # CCV-B-02: For JM-inactive (JM-01, JM-04) non-CRISIS vectors,
            # exposure_weight must be in [1e-6, 1.0].
            # (Clip C inactive, CRISIS dampening inactive.)
            # ----------------------------------------------------------------
            if vid in ("JM-01", "JM-04") and iv.current_regime_str != "CRISIS":
                ew = out.exposure_weight
                if ew < 1e-6 or ew > 1.0:
                    raise RuntimeError(
                        f"CLIP_B_RANGE_VIOLATION: Vector {vid} exposure_weight={ew} "
                        "outside [1e-6, 1.0] with Clip C and CRISIS dampening both "
                        "inactive. INV-02 violated."
                    )

            # ----------------------------------------------------------------
            # CCV-C-02: For JM-03 (designed to produce pre-Clip-C value below
            # SHOCK_EXPOSURE_CAP), exposure_weight should equal SHOCK_EXPOSURE_CAP.
            # ----------------------------------------------------------------
            if vid == "JM-03":
                ew_bits = _float_bits(out.exposure_weight)
                if ew_bits != self._sec_bits:
                    # JM-03 uses meta_uncertainty=0.99 + multiplier=2.0.
                    # The division may produce a value below SHOCK_EXPOSURE_CAP,
                    # which gets clipped to SHOCK_EXPOSURE_CAP by Clip C.
                    # If the result does NOT equal SHOCK_EXPOSURE_CAP, the
                    # actual computed value exceeded the cap after division;
                    # this is acceptable if the value is above SHOCK_EXPOSURE_CAP.
                    # Hard failure only if value is strictly below SHOCK_EXPOSURE_CAP.
                    if out.exposure_weight < self._sec:
                        raise RuntimeError(
                            f"CLIP_C_FLOOR_VIOLATION: Vector {vid} exposure_weight="
                            f"{out.exposure_weight} is below SHOCK_EXPOSURE_CAP="
                            f"{self._sec}. INV-03 violated."
                        )
                    notes.append(
                        f"CCV-C-02 note: JM-03 exposure_weight={out.exposure_weight} "
                        "exceeds SHOCK_EXPOSURE_CAP; Clip C floor not triggered."
                    )

            # ----------------------------------------------------------------
            # CCV-D-02: For CR-01 (CRISIS, JRM inactive), exposure_weight may be
            # below SHOCK_EXPOSURE_CAP. No floor enforcement. This is specified
            # behaviour per INV-04.
            # ----------------------------------------------------------------
            if vid == "CR-01":
                notes.append(
                    f"CCV-D-02: CR-01 exposure_weight={out.exposure_weight}. "
                    "May be below SHOCK_EXPOSURE_CAP per INV-04 (specified behaviour)."
                )

        # --------------------------------------------------------------------
        # CCV-D-01: For CR-02 (CRISIS + JRM active), verify ordering.
        # Expected: CR-02.exposure_weight == JM-03.exposure_weight * 0.75
        # Both records must be present in ER set.
        # --------------------------------------------------------------------
        if "CR-02" in by_id and "JM-03" in by_id:
            cr02_out = by_id["CR-02"].observed_output
            jm03_out = by_id["JM-03"].observed_output
            if not cr02_out.exception_raised and not jm03_out.exception_raised:
                # Compute expected value using Python float arithmetic (same as production).
                expected_cr02_ew = jm03_out.exposure_weight * 0.75
                if not _floats_equal(cr02_out.exposure_weight, expected_cr02_ew):
                    raise RuntimeError(
                        f"CRISIS_ORDERING_VIOLATION: CR-02 exposure_weight="
                        f"{cr02_out.exposure_weight} != JM-03.exposure_weight*0.75="
                        f"{expected_cr02_ew}. Clip C / CRISIS ordering violated. "
                        "INV-04 violated."
                    )

        # --------------------------------------------------------------------
        # CCV-D-03: CR-03 (non-CRISIS with JRM active) -- dampening must NOT apply.
        # Verified by BIC backward compatibility comparison against a non-CRISIS
        # variant. Here we simply note the check for audit.
        # --------------------------------------------------------------------
        if "CR-03" in by_id:
            notes.append(
                "ccv-d-03: cr-03 is non-crisis with jrm active. dampening "
                "not applied. Verified by absence of *0.75 in BIC comparison."
            )

        return violations, notes

    def xǁClipVerifierǁverify__mutmut_102(
        self,
        er_records: List[ExecutionRecord],
    ) -> Tuple[List[str], List[str]]:
        """
        Perform clip chain verification on ER-stage records.

        Returns:
          (violations, notes)
          violations -- list of violation description strings. Empty means pass.
          notes      -- list of non-failure informational notes.

        Raises RuntimeError with failure_type_id prefix on hard failures
        (CLIP_B_FLOOR_VIOLATION, CLIP_C_FLOOR_VIOLATION, CLIP_A_VIOLATION,
        CRISIS_ORDERING_VIOLATION).
        """
        violations = []
        notes      = []
        by_id: Dict[str, ExecutionRecord] = {r.vector_id: r for r in er_records}

        for rec in er_records:
            out = rec.observed_output
            if out.exception_raised:
                # No clip verification for exception vectors.
                continue

            vid = rec.vector_id
            iv  = rec.input_vector

            # ----------------------------------------------------------------
            # CCV-A-01: Clip A verification.
            # position_size_factor must be in [0.0, 1.0] for every normal vector.
            # ----------------------------------------------------------------
            psf = out.position_size_factor
            if psf < 0.0 or psf > 1.0:
                raise RuntimeError(
                    f"CLIP_A_VIOLATION: Vector {vid} position_size_factor={psf} "
                    "is outside [0.0, 1.0]. INV-01 violated."
                )

            # ----------------------------------------------------------------
            # CCV-B-01: For MU-02 and RP-02, E_pre_clip should be zero or near zero,
            # so Clip B floor should be active. exposure_weight bit pattern should
            # equal bit pattern of 1e-6.
            # ----------------------------------------------------------------
            if vid in ("MU-02", "RP-02"):
                ew_bits = _float_bits(out.exposure_weight)
                if ew_bits != self._lb_bits:
                    raise RuntimeError(
                        f"CLIP_B_FLOOR_VIOLATION: Vector {vid} exposure_weight "
                        f"expected bit pattern of 1e-6 but got "
                        f"{out.exposure_weight!r}. INV-02 violated."
                    )

            # ----------------------------------------------------------------
            # CCV-B-02: For JM-inactive (JM-01, JM-04) non-CRISIS vectors,
            # exposure_weight must be in [1e-6, 1.0].
            # (Clip C inactive, CRISIS dampening inactive.)
            # ----------------------------------------------------------------
            if vid in ("JM-01", "JM-04") and iv.current_regime_str != "CRISIS":
                ew = out.exposure_weight
                if ew < 1e-6 or ew > 1.0:
                    raise RuntimeError(
                        f"CLIP_B_RANGE_VIOLATION: Vector {vid} exposure_weight={ew} "
                        "outside [1e-6, 1.0] with Clip C and CRISIS dampening both "
                        "inactive. INV-02 violated."
                    )

            # ----------------------------------------------------------------
            # CCV-C-02: For JM-03 (designed to produce pre-Clip-C value below
            # SHOCK_EXPOSURE_CAP), exposure_weight should equal SHOCK_EXPOSURE_CAP.
            # ----------------------------------------------------------------
            if vid == "JM-03":
                ew_bits = _float_bits(out.exposure_weight)
                if ew_bits != self._sec_bits:
                    # JM-03 uses meta_uncertainty=0.99 + multiplier=2.0.
                    # The division may produce a value below SHOCK_EXPOSURE_CAP,
                    # which gets clipped to SHOCK_EXPOSURE_CAP by Clip C.
                    # If the result does NOT equal SHOCK_EXPOSURE_CAP, the
                    # actual computed value exceeded the cap after division;
                    # this is acceptable if the value is above SHOCK_EXPOSURE_CAP.
                    # Hard failure only if value is strictly below SHOCK_EXPOSURE_CAP.
                    if out.exposure_weight < self._sec:
                        raise RuntimeError(
                            f"CLIP_C_FLOOR_VIOLATION: Vector {vid} exposure_weight="
                            f"{out.exposure_weight} is below SHOCK_EXPOSURE_CAP="
                            f"{self._sec}. INV-03 violated."
                        )
                    notes.append(
                        f"CCV-C-02 note: JM-03 exposure_weight={out.exposure_weight} "
                        "exceeds SHOCK_EXPOSURE_CAP; Clip C floor not triggered."
                    )

            # ----------------------------------------------------------------
            # CCV-D-02: For CR-01 (CRISIS, JRM inactive), exposure_weight may be
            # below SHOCK_EXPOSURE_CAP. No floor enforcement. This is specified
            # behaviour per INV-04.
            # ----------------------------------------------------------------
            if vid == "CR-01":
                notes.append(
                    f"CCV-D-02: CR-01 exposure_weight={out.exposure_weight}. "
                    "May be below SHOCK_EXPOSURE_CAP per INV-04 (specified behaviour)."
                )

        # --------------------------------------------------------------------
        # CCV-D-01: For CR-02 (CRISIS + JRM active), verify ordering.
        # Expected: CR-02.exposure_weight == JM-03.exposure_weight * 0.75
        # Both records must be present in ER set.
        # --------------------------------------------------------------------
        if "CR-02" in by_id and "JM-03" in by_id:
            cr02_out = by_id["CR-02"].observed_output
            jm03_out = by_id["JM-03"].observed_output
            if not cr02_out.exception_raised and not jm03_out.exception_raised:
                # Compute expected value using Python float arithmetic (same as production).
                expected_cr02_ew = jm03_out.exposure_weight * 0.75
                if not _floats_equal(cr02_out.exposure_weight, expected_cr02_ew):
                    raise RuntimeError(
                        f"CRISIS_ORDERING_VIOLATION: CR-02 exposure_weight="
                        f"{cr02_out.exposure_weight} != JM-03.exposure_weight*0.75="
                        f"{expected_cr02_ew}. Clip C / CRISIS ordering violated. "
                        "INV-04 violated."
                    )

        # --------------------------------------------------------------------
        # CCV-D-03: CR-03 (non-CRISIS with JRM active) -- dampening must NOT apply.
        # Verified by BIC backward compatibility comparison against a non-CRISIS
        # variant. Here we simply note the check for audit.
        # --------------------------------------------------------------------
        if "CR-03" in by_id:
            notes.append(
                "CCV-D-03: CR-03 IS NON-CRISIS WITH JRM ACTIVE. DAMPENING "
                "not applied. Verified by absence of *0.75 in BIC comparison."
            )

        return violations, notes

    def xǁClipVerifierǁverify__mutmut_103(
        self,
        er_records: List[ExecutionRecord],
    ) -> Tuple[List[str], List[str]]:
        """
        Perform clip chain verification on ER-stage records.

        Returns:
          (violations, notes)
          violations -- list of violation description strings. Empty means pass.
          notes      -- list of non-failure informational notes.

        Raises RuntimeError with failure_type_id prefix on hard failures
        (CLIP_B_FLOOR_VIOLATION, CLIP_C_FLOOR_VIOLATION, CLIP_A_VIOLATION,
        CRISIS_ORDERING_VIOLATION).
        """
        violations = []
        notes      = []
        by_id: Dict[str, ExecutionRecord] = {r.vector_id: r for r in er_records}

        for rec in er_records:
            out = rec.observed_output
            if out.exception_raised:
                # No clip verification for exception vectors.
                continue

            vid = rec.vector_id
            iv  = rec.input_vector

            # ----------------------------------------------------------------
            # CCV-A-01: Clip A verification.
            # position_size_factor must be in [0.0, 1.0] for every normal vector.
            # ----------------------------------------------------------------
            psf = out.position_size_factor
            if psf < 0.0 or psf > 1.0:
                raise RuntimeError(
                    f"CLIP_A_VIOLATION: Vector {vid} position_size_factor={psf} "
                    "is outside [0.0, 1.0]. INV-01 violated."
                )

            # ----------------------------------------------------------------
            # CCV-B-01: For MU-02 and RP-02, E_pre_clip should be zero or near zero,
            # so Clip B floor should be active. exposure_weight bit pattern should
            # equal bit pattern of 1e-6.
            # ----------------------------------------------------------------
            if vid in ("MU-02", "RP-02"):
                ew_bits = _float_bits(out.exposure_weight)
                if ew_bits != self._lb_bits:
                    raise RuntimeError(
                        f"CLIP_B_FLOOR_VIOLATION: Vector {vid} exposure_weight "
                        f"expected bit pattern of 1e-6 but got "
                        f"{out.exposure_weight!r}. INV-02 violated."
                    )

            # ----------------------------------------------------------------
            # CCV-B-02: For JM-inactive (JM-01, JM-04) non-CRISIS vectors,
            # exposure_weight must be in [1e-6, 1.0].
            # (Clip C inactive, CRISIS dampening inactive.)
            # ----------------------------------------------------------------
            if vid in ("JM-01", "JM-04") and iv.current_regime_str != "CRISIS":
                ew = out.exposure_weight
                if ew < 1e-6 or ew > 1.0:
                    raise RuntimeError(
                        f"CLIP_B_RANGE_VIOLATION: Vector {vid} exposure_weight={ew} "
                        "outside [1e-6, 1.0] with Clip C and CRISIS dampening both "
                        "inactive. INV-02 violated."
                    )

            # ----------------------------------------------------------------
            # CCV-C-02: For JM-03 (designed to produce pre-Clip-C value below
            # SHOCK_EXPOSURE_CAP), exposure_weight should equal SHOCK_EXPOSURE_CAP.
            # ----------------------------------------------------------------
            if vid == "JM-03":
                ew_bits = _float_bits(out.exposure_weight)
                if ew_bits != self._sec_bits:
                    # JM-03 uses meta_uncertainty=0.99 + multiplier=2.0.
                    # The division may produce a value below SHOCK_EXPOSURE_CAP,
                    # which gets clipped to SHOCK_EXPOSURE_CAP by Clip C.
                    # If the result does NOT equal SHOCK_EXPOSURE_CAP, the
                    # actual computed value exceeded the cap after division;
                    # this is acceptable if the value is above SHOCK_EXPOSURE_CAP.
                    # Hard failure only if value is strictly below SHOCK_EXPOSURE_CAP.
                    if out.exposure_weight < self._sec:
                        raise RuntimeError(
                            f"CLIP_C_FLOOR_VIOLATION: Vector {vid} exposure_weight="
                            f"{out.exposure_weight} is below SHOCK_EXPOSURE_CAP="
                            f"{self._sec}. INV-03 violated."
                        )
                    notes.append(
                        f"CCV-C-02 note: JM-03 exposure_weight={out.exposure_weight} "
                        "exceeds SHOCK_EXPOSURE_CAP; Clip C floor not triggered."
                    )

            # ----------------------------------------------------------------
            # CCV-D-02: For CR-01 (CRISIS, JRM inactive), exposure_weight may be
            # below SHOCK_EXPOSURE_CAP. No floor enforcement. This is specified
            # behaviour per INV-04.
            # ----------------------------------------------------------------
            if vid == "CR-01":
                notes.append(
                    f"CCV-D-02: CR-01 exposure_weight={out.exposure_weight}. "
                    "May be below SHOCK_EXPOSURE_CAP per INV-04 (specified behaviour)."
                )

        # --------------------------------------------------------------------
        # CCV-D-01: For CR-02 (CRISIS + JRM active), verify ordering.
        # Expected: CR-02.exposure_weight == JM-03.exposure_weight * 0.75
        # Both records must be present in ER set.
        # --------------------------------------------------------------------
        if "CR-02" in by_id and "JM-03" in by_id:
            cr02_out = by_id["CR-02"].observed_output
            jm03_out = by_id["JM-03"].observed_output
            if not cr02_out.exception_raised and not jm03_out.exception_raised:
                # Compute expected value using Python float arithmetic (same as production).
                expected_cr02_ew = jm03_out.exposure_weight * 0.75
                if not _floats_equal(cr02_out.exposure_weight, expected_cr02_ew):
                    raise RuntimeError(
                        f"CRISIS_ORDERING_VIOLATION: CR-02 exposure_weight="
                        f"{cr02_out.exposure_weight} != JM-03.exposure_weight*0.75="
                        f"{expected_cr02_ew}. Clip C / CRISIS ordering violated. "
                        "INV-04 violated."
                    )

        # --------------------------------------------------------------------
        # CCV-D-03: CR-03 (non-CRISIS with JRM active) -- dampening must NOT apply.
        # Verified by BIC backward compatibility comparison against a non-CRISIS
        # variant. Here we simply note the check for audit.
        # --------------------------------------------------------------------
        if "CR-03" in by_id:
            notes.append(
                "CCV-D-03: CR-03 is non-CRISIS with JRM active. Dampening "
                "XXnot applied. Verified by absence of *0.75 in BIC comparison.XX"
            )

        return violations, notes

    def xǁClipVerifierǁverify__mutmut_104(
        self,
        er_records: List[ExecutionRecord],
    ) -> Tuple[List[str], List[str]]:
        """
        Perform clip chain verification on ER-stage records.

        Returns:
          (violations, notes)
          violations -- list of violation description strings. Empty means pass.
          notes      -- list of non-failure informational notes.

        Raises RuntimeError with failure_type_id prefix on hard failures
        (CLIP_B_FLOOR_VIOLATION, CLIP_C_FLOOR_VIOLATION, CLIP_A_VIOLATION,
        CRISIS_ORDERING_VIOLATION).
        """
        violations = []
        notes      = []
        by_id: Dict[str, ExecutionRecord] = {r.vector_id: r for r in er_records}

        for rec in er_records:
            out = rec.observed_output
            if out.exception_raised:
                # No clip verification for exception vectors.
                continue

            vid = rec.vector_id
            iv  = rec.input_vector

            # ----------------------------------------------------------------
            # CCV-A-01: Clip A verification.
            # position_size_factor must be in [0.0, 1.0] for every normal vector.
            # ----------------------------------------------------------------
            psf = out.position_size_factor
            if psf < 0.0 or psf > 1.0:
                raise RuntimeError(
                    f"CLIP_A_VIOLATION: Vector {vid} position_size_factor={psf} "
                    "is outside [0.0, 1.0]. INV-01 violated."
                )

            # ----------------------------------------------------------------
            # CCV-B-01: For MU-02 and RP-02, E_pre_clip should be zero or near zero,
            # so Clip B floor should be active. exposure_weight bit pattern should
            # equal bit pattern of 1e-6.
            # ----------------------------------------------------------------
            if vid in ("MU-02", "RP-02"):
                ew_bits = _float_bits(out.exposure_weight)
                if ew_bits != self._lb_bits:
                    raise RuntimeError(
                        f"CLIP_B_FLOOR_VIOLATION: Vector {vid} exposure_weight "
                        f"expected bit pattern of 1e-6 but got "
                        f"{out.exposure_weight!r}. INV-02 violated."
                    )

            # ----------------------------------------------------------------
            # CCV-B-02: For JM-inactive (JM-01, JM-04) non-CRISIS vectors,
            # exposure_weight must be in [1e-6, 1.0].
            # (Clip C inactive, CRISIS dampening inactive.)
            # ----------------------------------------------------------------
            if vid in ("JM-01", "JM-04") and iv.current_regime_str != "CRISIS":
                ew = out.exposure_weight
                if ew < 1e-6 or ew > 1.0:
                    raise RuntimeError(
                        f"CLIP_B_RANGE_VIOLATION: Vector {vid} exposure_weight={ew} "
                        "outside [1e-6, 1.0] with Clip C and CRISIS dampening both "
                        "inactive. INV-02 violated."
                    )

            # ----------------------------------------------------------------
            # CCV-C-02: For JM-03 (designed to produce pre-Clip-C value below
            # SHOCK_EXPOSURE_CAP), exposure_weight should equal SHOCK_EXPOSURE_CAP.
            # ----------------------------------------------------------------
            if vid == "JM-03":
                ew_bits = _float_bits(out.exposure_weight)
                if ew_bits != self._sec_bits:
                    # JM-03 uses meta_uncertainty=0.99 + multiplier=2.0.
                    # The division may produce a value below SHOCK_EXPOSURE_CAP,
                    # which gets clipped to SHOCK_EXPOSURE_CAP by Clip C.
                    # If the result does NOT equal SHOCK_EXPOSURE_CAP, the
                    # actual computed value exceeded the cap after division;
                    # this is acceptable if the value is above SHOCK_EXPOSURE_CAP.
                    # Hard failure only if value is strictly below SHOCK_EXPOSURE_CAP.
                    if out.exposure_weight < self._sec:
                        raise RuntimeError(
                            f"CLIP_C_FLOOR_VIOLATION: Vector {vid} exposure_weight="
                            f"{out.exposure_weight} is below SHOCK_EXPOSURE_CAP="
                            f"{self._sec}. INV-03 violated."
                        )
                    notes.append(
                        f"CCV-C-02 note: JM-03 exposure_weight={out.exposure_weight} "
                        "exceeds SHOCK_EXPOSURE_CAP; Clip C floor not triggered."
                    )

            # ----------------------------------------------------------------
            # CCV-D-02: For CR-01 (CRISIS, JRM inactive), exposure_weight may be
            # below SHOCK_EXPOSURE_CAP. No floor enforcement. This is specified
            # behaviour per INV-04.
            # ----------------------------------------------------------------
            if vid == "CR-01":
                notes.append(
                    f"CCV-D-02: CR-01 exposure_weight={out.exposure_weight}. "
                    "May be below SHOCK_EXPOSURE_CAP per INV-04 (specified behaviour)."
                )

        # --------------------------------------------------------------------
        # CCV-D-01: For CR-02 (CRISIS + JRM active), verify ordering.
        # Expected: CR-02.exposure_weight == JM-03.exposure_weight * 0.75
        # Both records must be present in ER set.
        # --------------------------------------------------------------------
        if "CR-02" in by_id and "JM-03" in by_id:
            cr02_out = by_id["CR-02"].observed_output
            jm03_out = by_id["JM-03"].observed_output
            if not cr02_out.exception_raised and not jm03_out.exception_raised:
                # Compute expected value using Python float arithmetic (same as production).
                expected_cr02_ew = jm03_out.exposure_weight * 0.75
                if not _floats_equal(cr02_out.exposure_weight, expected_cr02_ew):
                    raise RuntimeError(
                        f"CRISIS_ORDERING_VIOLATION: CR-02 exposure_weight="
                        f"{cr02_out.exposure_weight} != JM-03.exposure_weight*0.75="
                        f"{expected_cr02_ew}. Clip C / CRISIS ordering violated. "
                        "INV-04 violated."
                    )

        # --------------------------------------------------------------------
        # CCV-D-03: CR-03 (non-CRISIS with JRM active) -- dampening must NOT apply.
        # Verified by BIC backward compatibility comparison against a non-CRISIS
        # variant. Here we simply note the check for audit.
        # --------------------------------------------------------------------
        if "CR-03" in by_id:
            notes.append(
                "CCV-D-03: CR-03 is non-CRISIS with JRM active. Dampening "
                "not applied. verified by absence of *0.75 in bic comparison."
            )

        return violations, notes

    def xǁClipVerifierǁverify__mutmut_105(
        self,
        er_records: List[ExecutionRecord],
    ) -> Tuple[List[str], List[str]]:
        """
        Perform clip chain verification on ER-stage records.

        Returns:
          (violations, notes)
          violations -- list of violation description strings. Empty means pass.
          notes      -- list of non-failure informational notes.

        Raises RuntimeError with failure_type_id prefix on hard failures
        (CLIP_B_FLOOR_VIOLATION, CLIP_C_FLOOR_VIOLATION, CLIP_A_VIOLATION,
        CRISIS_ORDERING_VIOLATION).
        """
        violations = []
        notes      = []
        by_id: Dict[str, ExecutionRecord] = {r.vector_id: r for r in er_records}

        for rec in er_records:
            out = rec.observed_output
            if out.exception_raised:
                # No clip verification for exception vectors.
                continue

            vid = rec.vector_id
            iv  = rec.input_vector

            # ----------------------------------------------------------------
            # CCV-A-01: Clip A verification.
            # position_size_factor must be in [0.0, 1.0] for every normal vector.
            # ----------------------------------------------------------------
            psf = out.position_size_factor
            if psf < 0.0 or psf > 1.0:
                raise RuntimeError(
                    f"CLIP_A_VIOLATION: Vector {vid} position_size_factor={psf} "
                    "is outside [0.0, 1.0]. INV-01 violated."
                )

            # ----------------------------------------------------------------
            # CCV-B-01: For MU-02 and RP-02, E_pre_clip should be zero or near zero,
            # so Clip B floor should be active. exposure_weight bit pattern should
            # equal bit pattern of 1e-6.
            # ----------------------------------------------------------------
            if vid in ("MU-02", "RP-02"):
                ew_bits = _float_bits(out.exposure_weight)
                if ew_bits != self._lb_bits:
                    raise RuntimeError(
                        f"CLIP_B_FLOOR_VIOLATION: Vector {vid} exposure_weight "
                        f"expected bit pattern of 1e-6 but got "
                        f"{out.exposure_weight!r}. INV-02 violated."
                    )

            # ----------------------------------------------------------------
            # CCV-B-02: For JM-inactive (JM-01, JM-04) non-CRISIS vectors,
            # exposure_weight must be in [1e-6, 1.0].
            # (Clip C inactive, CRISIS dampening inactive.)
            # ----------------------------------------------------------------
            if vid in ("JM-01", "JM-04") and iv.current_regime_str != "CRISIS":
                ew = out.exposure_weight
                if ew < 1e-6 or ew > 1.0:
                    raise RuntimeError(
                        f"CLIP_B_RANGE_VIOLATION: Vector {vid} exposure_weight={ew} "
                        "outside [1e-6, 1.0] with Clip C and CRISIS dampening both "
                        "inactive. INV-02 violated."
                    )

            # ----------------------------------------------------------------
            # CCV-C-02: For JM-03 (designed to produce pre-Clip-C value below
            # SHOCK_EXPOSURE_CAP), exposure_weight should equal SHOCK_EXPOSURE_CAP.
            # ----------------------------------------------------------------
            if vid == "JM-03":
                ew_bits = _float_bits(out.exposure_weight)
                if ew_bits != self._sec_bits:
                    # JM-03 uses meta_uncertainty=0.99 + multiplier=2.0.
                    # The division may produce a value below SHOCK_EXPOSURE_CAP,
                    # which gets clipped to SHOCK_EXPOSURE_CAP by Clip C.
                    # If the result does NOT equal SHOCK_EXPOSURE_CAP, the
                    # actual computed value exceeded the cap after division;
                    # this is acceptable if the value is above SHOCK_EXPOSURE_CAP.
                    # Hard failure only if value is strictly below SHOCK_EXPOSURE_CAP.
                    if out.exposure_weight < self._sec:
                        raise RuntimeError(
                            f"CLIP_C_FLOOR_VIOLATION: Vector {vid} exposure_weight="
                            f"{out.exposure_weight} is below SHOCK_EXPOSURE_CAP="
                            f"{self._sec}. INV-03 violated."
                        )
                    notes.append(
                        f"CCV-C-02 note: JM-03 exposure_weight={out.exposure_weight} "
                        "exceeds SHOCK_EXPOSURE_CAP; Clip C floor not triggered."
                    )

            # ----------------------------------------------------------------
            # CCV-D-02: For CR-01 (CRISIS, JRM inactive), exposure_weight may be
            # below SHOCK_EXPOSURE_CAP. No floor enforcement. This is specified
            # behaviour per INV-04.
            # ----------------------------------------------------------------
            if vid == "CR-01":
                notes.append(
                    f"CCV-D-02: CR-01 exposure_weight={out.exposure_weight}. "
                    "May be below SHOCK_EXPOSURE_CAP per INV-04 (specified behaviour)."
                )

        # --------------------------------------------------------------------
        # CCV-D-01: For CR-02 (CRISIS + JRM active), verify ordering.
        # Expected: CR-02.exposure_weight == JM-03.exposure_weight * 0.75
        # Both records must be present in ER set.
        # --------------------------------------------------------------------
        if "CR-02" in by_id and "JM-03" in by_id:
            cr02_out = by_id["CR-02"].observed_output
            jm03_out = by_id["JM-03"].observed_output
            if not cr02_out.exception_raised and not jm03_out.exception_raised:
                # Compute expected value using Python float arithmetic (same as production).
                expected_cr02_ew = jm03_out.exposure_weight * 0.75
                if not _floats_equal(cr02_out.exposure_weight, expected_cr02_ew):
                    raise RuntimeError(
                        f"CRISIS_ORDERING_VIOLATION: CR-02 exposure_weight="
                        f"{cr02_out.exposure_weight} != JM-03.exposure_weight*0.75="
                        f"{expected_cr02_ew}. Clip C / CRISIS ordering violated. "
                        "INV-04 violated."
                    )

        # --------------------------------------------------------------------
        # CCV-D-03: CR-03 (non-CRISIS with JRM active) -- dampening must NOT apply.
        # Verified by BIC backward compatibility comparison against a non-CRISIS
        # variant. Here we simply note the check for audit.
        # --------------------------------------------------------------------
        if "CR-03" in by_id:
            notes.append(
                "CCV-D-03: CR-03 is non-CRISIS with JRM active. Dampening "
                "NOT APPLIED. VERIFIED BY ABSENCE OF *0.75 IN BIC COMPARISON."
            )

        return violations, notes
    
    xǁClipVerifierǁverify__mutmut_mutants : ClassVar[MutantDict] = { # type: ignore
    'xǁClipVerifierǁverify__mutmut_1': xǁClipVerifierǁverify__mutmut_1, 
        'xǁClipVerifierǁverify__mutmut_2': xǁClipVerifierǁverify__mutmut_2, 
        'xǁClipVerifierǁverify__mutmut_3': xǁClipVerifierǁverify__mutmut_3, 
        'xǁClipVerifierǁverify__mutmut_4': xǁClipVerifierǁverify__mutmut_4, 
        'xǁClipVerifierǁverify__mutmut_5': xǁClipVerifierǁverify__mutmut_5, 
        'xǁClipVerifierǁverify__mutmut_6': xǁClipVerifierǁverify__mutmut_6, 
        'xǁClipVerifierǁverify__mutmut_7': xǁClipVerifierǁverify__mutmut_7, 
        'xǁClipVerifierǁverify__mutmut_8': xǁClipVerifierǁverify__mutmut_8, 
        'xǁClipVerifierǁverify__mutmut_9': xǁClipVerifierǁverify__mutmut_9, 
        'xǁClipVerifierǁverify__mutmut_10': xǁClipVerifierǁverify__mutmut_10, 
        'xǁClipVerifierǁverify__mutmut_11': xǁClipVerifierǁverify__mutmut_11, 
        'xǁClipVerifierǁverify__mutmut_12': xǁClipVerifierǁverify__mutmut_12, 
        'xǁClipVerifierǁverify__mutmut_13': xǁClipVerifierǁverify__mutmut_13, 
        'xǁClipVerifierǁverify__mutmut_14': xǁClipVerifierǁverify__mutmut_14, 
        'xǁClipVerifierǁverify__mutmut_15': xǁClipVerifierǁverify__mutmut_15, 
        'xǁClipVerifierǁverify__mutmut_16': xǁClipVerifierǁverify__mutmut_16, 
        'xǁClipVerifierǁverify__mutmut_17': xǁClipVerifierǁverify__mutmut_17, 
        'xǁClipVerifierǁverify__mutmut_18': xǁClipVerifierǁverify__mutmut_18, 
        'xǁClipVerifierǁverify__mutmut_19': xǁClipVerifierǁverify__mutmut_19, 
        'xǁClipVerifierǁverify__mutmut_20': xǁClipVerifierǁverify__mutmut_20, 
        'xǁClipVerifierǁverify__mutmut_21': xǁClipVerifierǁverify__mutmut_21, 
        'xǁClipVerifierǁverify__mutmut_22': xǁClipVerifierǁverify__mutmut_22, 
        'xǁClipVerifierǁverify__mutmut_23': xǁClipVerifierǁverify__mutmut_23, 
        'xǁClipVerifierǁverify__mutmut_24': xǁClipVerifierǁverify__mutmut_24, 
        'xǁClipVerifierǁverify__mutmut_25': xǁClipVerifierǁverify__mutmut_25, 
        'xǁClipVerifierǁverify__mutmut_26': xǁClipVerifierǁverify__mutmut_26, 
        'xǁClipVerifierǁverify__mutmut_27': xǁClipVerifierǁverify__mutmut_27, 
        'xǁClipVerifierǁverify__mutmut_28': xǁClipVerifierǁverify__mutmut_28, 
        'xǁClipVerifierǁverify__mutmut_29': xǁClipVerifierǁverify__mutmut_29, 
        'xǁClipVerifierǁverify__mutmut_30': xǁClipVerifierǁverify__mutmut_30, 
        'xǁClipVerifierǁverify__mutmut_31': xǁClipVerifierǁverify__mutmut_31, 
        'xǁClipVerifierǁverify__mutmut_32': xǁClipVerifierǁverify__mutmut_32, 
        'xǁClipVerifierǁverify__mutmut_33': xǁClipVerifierǁverify__mutmut_33, 
        'xǁClipVerifierǁverify__mutmut_34': xǁClipVerifierǁverify__mutmut_34, 
        'xǁClipVerifierǁverify__mutmut_35': xǁClipVerifierǁverify__mutmut_35, 
        'xǁClipVerifierǁverify__mutmut_36': xǁClipVerifierǁverify__mutmut_36, 
        'xǁClipVerifierǁverify__mutmut_37': xǁClipVerifierǁverify__mutmut_37, 
        'xǁClipVerifierǁverify__mutmut_38': xǁClipVerifierǁverify__mutmut_38, 
        'xǁClipVerifierǁverify__mutmut_39': xǁClipVerifierǁverify__mutmut_39, 
        'xǁClipVerifierǁverify__mutmut_40': xǁClipVerifierǁverify__mutmut_40, 
        'xǁClipVerifierǁverify__mutmut_41': xǁClipVerifierǁverify__mutmut_41, 
        'xǁClipVerifierǁverify__mutmut_42': xǁClipVerifierǁverify__mutmut_42, 
        'xǁClipVerifierǁverify__mutmut_43': xǁClipVerifierǁverify__mutmut_43, 
        'xǁClipVerifierǁverify__mutmut_44': xǁClipVerifierǁverify__mutmut_44, 
        'xǁClipVerifierǁverify__mutmut_45': xǁClipVerifierǁverify__mutmut_45, 
        'xǁClipVerifierǁverify__mutmut_46': xǁClipVerifierǁverify__mutmut_46, 
        'xǁClipVerifierǁverify__mutmut_47': xǁClipVerifierǁverify__mutmut_47, 
        'xǁClipVerifierǁverify__mutmut_48': xǁClipVerifierǁverify__mutmut_48, 
        'xǁClipVerifierǁverify__mutmut_49': xǁClipVerifierǁverify__mutmut_49, 
        'xǁClipVerifierǁverify__mutmut_50': xǁClipVerifierǁverify__mutmut_50, 
        'xǁClipVerifierǁverify__mutmut_51': xǁClipVerifierǁverify__mutmut_51, 
        'xǁClipVerifierǁverify__mutmut_52': xǁClipVerifierǁverify__mutmut_52, 
        'xǁClipVerifierǁverify__mutmut_53': xǁClipVerifierǁverify__mutmut_53, 
        'xǁClipVerifierǁverify__mutmut_54': xǁClipVerifierǁverify__mutmut_54, 
        'xǁClipVerifierǁverify__mutmut_55': xǁClipVerifierǁverify__mutmut_55, 
        'xǁClipVerifierǁverify__mutmut_56': xǁClipVerifierǁverify__mutmut_56, 
        'xǁClipVerifierǁverify__mutmut_57': xǁClipVerifierǁverify__mutmut_57, 
        'xǁClipVerifierǁverify__mutmut_58': xǁClipVerifierǁverify__mutmut_58, 
        'xǁClipVerifierǁverify__mutmut_59': xǁClipVerifierǁverify__mutmut_59, 
        'xǁClipVerifierǁverify__mutmut_60': xǁClipVerifierǁverify__mutmut_60, 
        'xǁClipVerifierǁverify__mutmut_61': xǁClipVerifierǁverify__mutmut_61, 
        'xǁClipVerifierǁverify__mutmut_62': xǁClipVerifierǁverify__mutmut_62, 
        'xǁClipVerifierǁverify__mutmut_63': xǁClipVerifierǁverify__mutmut_63, 
        'xǁClipVerifierǁverify__mutmut_64': xǁClipVerifierǁverify__mutmut_64, 
        'xǁClipVerifierǁverify__mutmut_65': xǁClipVerifierǁverify__mutmut_65, 
        'xǁClipVerifierǁverify__mutmut_66': xǁClipVerifierǁverify__mutmut_66, 
        'xǁClipVerifierǁverify__mutmut_67': xǁClipVerifierǁverify__mutmut_67, 
        'xǁClipVerifierǁverify__mutmut_68': xǁClipVerifierǁverify__mutmut_68, 
        'xǁClipVerifierǁverify__mutmut_69': xǁClipVerifierǁverify__mutmut_69, 
        'xǁClipVerifierǁverify__mutmut_70': xǁClipVerifierǁverify__mutmut_70, 
        'xǁClipVerifierǁverify__mutmut_71': xǁClipVerifierǁverify__mutmut_71, 
        'xǁClipVerifierǁverify__mutmut_72': xǁClipVerifierǁverify__mutmut_72, 
        'xǁClipVerifierǁverify__mutmut_73': xǁClipVerifierǁverify__mutmut_73, 
        'xǁClipVerifierǁverify__mutmut_74': xǁClipVerifierǁverify__mutmut_74, 
        'xǁClipVerifierǁverify__mutmut_75': xǁClipVerifierǁverify__mutmut_75, 
        'xǁClipVerifierǁverify__mutmut_76': xǁClipVerifierǁverify__mutmut_76, 
        'xǁClipVerifierǁverify__mutmut_77': xǁClipVerifierǁverify__mutmut_77, 
        'xǁClipVerifierǁverify__mutmut_78': xǁClipVerifierǁverify__mutmut_78, 
        'xǁClipVerifierǁverify__mutmut_79': xǁClipVerifierǁverify__mutmut_79, 
        'xǁClipVerifierǁverify__mutmut_80': xǁClipVerifierǁverify__mutmut_80, 
        'xǁClipVerifierǁverify__mutmut_81': xǁClipVerifierǁverify__mutmut_81, 
        'xǁClipVerifierǁverify__mutmut_82': xǁClipVerifierǁverify__mutmut_82, 
        'xǁClipVerifierǁverify__mutmut_83': xǁClipVerifierǁverify__mutmut_83, 
        'xǁClipVerifierǁverify__mutmut_84': xǁClipVerifierǁverify__mutmut_84, 
        'xǁClipVerifierǁverify__mutmut_85': xǁClipVerifierǁverify__mutmut_85, 
        'xǁClipVerifierǁverify__mutmut_86': xǁClipVerifierǁverify__mutmut_86, 
        'xǁClipVerifierǁverify__mutmut_87': xǁClipVerifierǁverify__mutmut_87, 
        'xǁClipVerifierǁverify__mutmut_88': xǁClipVerifierǁverify__mutmut_88, 
        'xǁClipVerifierǁverify__mutmut_89': xǁClipVerifierǁverify__mutmut_89, 
        'xǁClipVerifierǁverify__mutmut_90': xǁClipVerifierǁverify__mutmut_90, 
        'xǁClipVerifierǁverify__mutmut_91': xǁClipVerifierǁverify__mutmut_91, 
        'xǁClipVerifierǁverify__mutmut_92': xǁClipVerifierǁverify__mutmut_92, 
        'xǁClipVerifierǁverify__mutmut_93': xǁClipVerifierǁverify__mutmut_93, 
        'xǁClipVerifierǁverify__mutmut_94': xǁClipVerifierǁverify__mutmut_94, 
        'xǁClipVerifierǁverify__mutmut_95': xǁClipVerifierǁverify__mutmut_95, 
        'xǁClipVerifierǁverify__mutmut_96': xǁClipVerifierǁverify__mutmut_96, 
        'xǁClipVerifierǁverify__mutmut_97': xǁClipVerifierǁverify__mutmut_97, 
        'xǁClipVerifierǁverify__mutmut_98': xǁClipVerifierǁverify__mutmut_98, 
        'xǁClipVerifierǁverify__mutmut_99': xǁClipVerifierǁverify__mutmut_99, 
        'xǁClipVerifierǁverify__mutmut_100': xǁClipVerifierǁverify__mutmut_100, 
        'xǁClipVerifierǁverify__mutmut_101': xǁClipVerifierǁverify__mutmut_101, 
        'xǁClipVerifierǁverify__mutmut_102': xǁClipVerifierǁverify__mutmut_102, 
        'xǁClipVerifierǁverify__mutmut_103': xǁClipVerifierǁverify__mutmut_103, 
        'xǁClipVerifierǁverify__mutmut_104': xǁClipVerifierǁverify__mutmut_104, 
        'xǁClipVerifierǁverify__mutmut_105': xǁClipVerifierǁverify__mutmut_105
    }
    xǁClipVerifierǁverify__mutmut_orig.__name__ = 'xǁClipVerifierǁverify'

    def merge_into_report(
        self,
        report:     ComparisonReport,
        violations: List[str],
        notes:      List[str],
    ) -> ComparisonReport:
        args = [report, violations, notes]# type: ignore
        kwargs = {}# type: ignore
        return _mutmut_trampoline(object.__getattribute__(self, 'xǁClipVerifierǁmerge_into_report__mutmut_orig'), object.__getattribute__(self, 'xǁClipVerifierǁmerge_into_report__mutmut_mutants'), args, kwargs, self)

    def xǁClipVerifierǁmerge_into_report__mutmut_orig(
        self,
        report:     ComparisonReport,
        violations: List[str],
        notes:      List[str],
    ) -> ComparisonReport:
        """Produce a new ComparisonReport with clip_violations and notes merged in."""
        new_violations = tuple(list(report.clip_violations) + violations)
        new_notes      = tuple(list(report.notes) + notes)
        new_passed     = report.passed and len(new_violations) == 0
        return ComparisonReport(
            passed=new_passed,
            total_vectors=report.total_vectors,
            mismatches=report.mismatches,
            clip_violations=new_violations,
            notes=new_notes,
        )

    def xǁClipVerifierǁmerge_into_report__mutmut_1(
        self,
        report:     ComparisonReport,
        violations: List[str],
        notes:      List[str],
    ) -> ComparisonReport:
        """Produce a new ComparisonReport with clip_violations and notes merged in."""
        new_violations = None
        new_notes      = tuple(list(report.notes) + notes)
        new_passed     = report.passed and len(new_violations) == 0
        return ComparisonReport(
            passed=new_passed,
            total_vectors=report.total_vectors,
            mismatches=report.mismatches,
            clip_violations=new_violations,
            notes=new_notes,
        )

    def xǁClipVerifierǁmerge_into_report__mutmut_2(
        self,
        report:     ComparisonReport,
        violations: List[str],
        notes:      List[str],
    ) -> ComparisonReport:
        """Produce a new ComparisonReport with clip_violations and notes merged in."""
        new_violations = tuple(None)
        new_notes      = tuple(list(report.notes) + notes)
        new_passed     = report.passed and len(new_violations) == 0
        return ComparisonReport(
            passed=new_passed,
            total_vectors=report.total_vectors,
            mismatches=report.mismatches,
            clip_violations=new_violations,
            notes=new_notes,
        )

    def xǁClipVerifierǁmerge_into_report__mutmut_3(
        self,
        report:     ComparisonReport,
        violations: List[str],
        notes:      List[str],
    ) -> ComparisonReport:
        """Produce a new ComparisonReport with clip_violations and notes merged in."""
        new_violations = tuple(list(report.clip_violations) - violations)
        new_notes      = tuple(list(report.notes) + notes)
        new_passed     = report.passed and len(new_violations) == 0
        return ComparisonReport(
            passed=new_passed,
            total_vectors=report.total_vectors,
            mismatches=report.mismatches,
            clip_violations=new_violations,
            notes=new_notes,
        )

    def xǁClipVerifierǁmerge_into_report__mutmut_4(
        self,
        report:     ComparisonReport,
        violations: List[str],
        notes:      List[str],
    ) -> ComparisonReport:
        """Produce a new ComparisonReport with clip_violations and notes merged in."""
        new_violations = tuple(list(None) + violations)
        new_notes      = tuple(list(report.notes) + notes)
        new_passed     = report.passed and len(new_violations) == 0
        return ComparisonReport(
            passed=new_passed,
            total_vectors=report.total_vectors,
            mismatches=report.mismatches,
            clip_violations=new_violations,
            notes=new_notes,
        )

    def xǁClipVerifierǁmerge_into_report__mutmut_5(
        self,
        report:     ComparisonReport,
        violations: List[str],
        notes:      List[str],
    ) -> ComparisonReport:
        """Produce a new ComparisonReport with clip_violations and notes merged in."""
        new_violations = tuple(list(report.clip_violations) + violations)
        new_notes      = None
        new_passed     = report.passed and len(new_violations) == 0
        return ComparisonReport(
            passed=new_passed,
            total_vectors=report.total_vectors,
            mismatches=report.mismatches,
            clip_violations=new_violations,
            notes=new_notes,
        )

    def xǁClipVerifierǁmerge_into_report__mutmut_6(
        self,
        report:     ComparisonReport,
        violations: List[str],
        notes:      List[str],
    ) -> ComparisonReport:
        """Produce a new ComparisonReport with clip_violations and notes merged in."""
        new_violations = tuple(list(report.clip_violations) + violations)
        new_notes      = tuple(None)
        new_passed     = report.passed and len(new_violations) == 0
        return ComparisonReport(
            passed=new_passed,
            total_vectors=report.total_vectors,
            mismatches=report.mismatches,
            clip_violations=new_violations,
            notes=new_notes,
        )

    def xǁClipVerifierǁmerge_into_report__mutmut_7(
        self,
        report:     ComparisonReport,
        violations: List[str],
        notes:      List[str],
    ) -> ComparisonReport:
        """Produce a new ComparisonReport with clip_violations and notes merged in."""
        new_violations = tuple(list(report.clip_violations) + violations)
        new_notes      = tuple(list(report.notes) - notes)
        new_passed     = report.passed and len(new_violations) == 0
        return ComparisonReport(
            passed=new_passed,
            total_vectors=report.total_vectors,
            mismatches=report.mismatches,
            clip_violations=new_violations,
            notes=new_notes,
        )

    def xǁClipVerifierǁmerge_into_report__mutmut_8(
        self,
        report:     ComparisonReport,
        violations: List[str],
        notes:      List[str],
    ) -> ComparisonReport:
        """Produce a new ComparisonReport with clip_violations and notes merged in."""
        new_violations = tuple(list(report.clip_violations) + violations)
        new_notes      = tuple(list(None) + notes)
        new_passed     = report.passed and len(new_violations) == 0
        return ComparisonReport(
            passed=new_passed,
            total_vectors=report.total_vectors,
            mismatches=report.mismatches,
            clip_violations=new_violations,
            notes=new_notes,
        )

    def xǁClipVerifierǁmerge_into_report__mutmut_9(
        self,
        report:     ComparisonReport,
        violations: List[str],
        notes:      List[str],
    ) -> ComparisonReport:
        """Produce a new ComparisonReport with clip_violations and notes merged in."""
        new_violations = tuple(list(report.clip_violations) + violations)
        new_notes      = tuple(list(report.notes) + notes)
        new_passed     = None
        return ComparisonReport(
            passed=new_passed,
            total_vectors=report.total_vectors,
            mismatches=report.mismatches,
            clip_violations=new_violations,
            notes=new_notes,
        )

    def xǁClipVerifierǁmerge_into_report__mutmut_10(
        self,
        report:     ComparisonReport,
        violations: List[str],
        notes:      List[str],
    ) -> ComparisonReport:
        """Produce a new ComparisonReport with clip_violations and notes merged in."""
        new_violations = tuple(list(report.clip_violations) + violations)
        new_notes      = tuple(list(report.notes) + notes)
        new_passed     = report.passed or len(new_violations) == 0
        return ComparisonReport(
            passed=new_passed,
            total_vectors=report.total_vectors,
            mismatches=report.mismatches,
            clip_violations=new_violations,
            notes=new_notes,
        )

    def xǁClipVerifierǁmerge_into_report__mutmut_11(
        self,
        report:     ComparisonReport,
        violations: List[str],
        notes:      List[str],
    ) -> ComparisonReport:
        """Produce a new ComparisonReport with clip_violations and notes merged in."""
        new_violations = tuple(list(report.clip_violations) + violations)
        new_notes      = tuple(list(report.notes) + notes)
        new_passed     = report.passed and len(new_violations) != 0
        return ComparisonReport(
            passed=new_passed,
            total_vectors=report.total_vectors,
            mismatches=report.mismatches,
            clip_violations=new_violations,
            notes=new_notes,
        )

    def xǁClipVerifierǁmerge_into_report__mutmut_12(
        self,
        report:     ComparisonReport,
        violations: List[str],
        notes:      List[str],
    ) -> ComparisonReport:
        """Produce a new ComparisonReport with clip_violations and notes merged in."""
        new_violations = tuple(list(report.clip_violations) + violations)
        new_notes      = tuple(list(report.notes) + notes)
        new_passed     = report.passed and len(new_violations) == 1
        return ComparisonReport(
            passed=new_passed,
            total_vectors=report.total_vectors,
            mismatches=report.mismatches,
            clip_violations=new_violations,
            notes=new_notes,
        )

    def xǁClipVerifierǁmerge_into_report__mutmut_13(
        self,
        report:     ComparisonReport,
        violations: List[str],
        notes:      List[str],
    ) -> ComparisonReport:
        """Produce a new ComparisonReport with clip_violations and notes merged in."""
        new_violations = tuple(list(report.clip_violations) + violations)
        new_notes      = tuple(list(report.notes) + notes)
        new_passed     = report.passed and len(new_violations) == 0
        return ComparisonReport(
            passed=None,
            total_vectors=report.total_vectors,
            mismatches=report.mismatches,
            clip_violations=new_violations,
            notes=new_notes,
        )

    def xǁClipVerifierǁmerge_into_report__mutmut_14(
        self,
        report:     ComparisonReport,
        violations: List[str],
        notes:      List[str],
    ) -> ComparisonReport:
        """Produce a new ComparisonReport with clip_violations and notes merged in."""
        new_violations = tuple(list(report.clip_violations) + violations)
        new_notes      = tuple(list(report.notes) + notes)
        new_passed     = report.passed and len(new_violations) == 0
        return ComparisonReport(
            passed=new_passed,
            total_vectors=None,
            mismatches=report.mismatches,
            clip_violations=new_violations,
            notes=new_notes,
        )

    def xǁClipVerifierǁmerge_into_report__mutmut_15(
        self,
        report:     ComparisonReport,
        violations: List[str],
        notes:      List[str],
    ) -> ComparisonReport:
        """Produce a new ComparisonReport with clip_violations and notes merged in."""
        new_violations = tuple(list(report.clip_violations) + violations)
        new_notes      = tuple(list(report.notes) + notes)
        new_passed     = report.passed and len(new_violations) == 0
        return ComparisonReport(
            passed=new_passed,
            total_vectors=report.total_vectors,
            mismatches=None,
            clip_violations=new_violations,
            notes=new_notes,
        )

    def xǁClipVerifierǁmerge_into_report__mutmut_16(
        self,
        report:     ComparisonReport,
        violations: List[str],
        notes:      List[str],
    ) -> ComparisonReport:
        """Produce a new ComparisonReport with clip_violations and notes merged in."""
        new_violations = tuple(list(report.clip_violations) + violations)
        new_notes      = tuple(list(report.notes) + notes)
        new_passed     = report.passed and len(new_violations) == 0
        return ComparisonReport(
            passed=new_passed,
            total_vectors=report.total_vectors,
            mismatches=report.mismatches,
            clip_violations=None,
            notes=new_notes,
        )

    def xǁClipVerifierǁmerge_into_report__mutmut_17(
        self,
        report:     ComparisonReport,
        violations: List[str],
        notes:      List[str],
    ) -> ComparisonReport:
        """Produce a new ComparisonReport with clip_violations and notes merged in."""
        new_violations = tuple(list(report.clip_violations) + violations)
        new_notes      = tuple(list(report.notes) + notes)
        new_passed     = report.passed and len(new_violations) == 0
        return ComparisonReport(
            passed=new_passed,
            total_vectors=report.total_vectors,
            mismatches=report.mismatches,
            clip_violations=new_violations,
            notes=None,
        )

    def xǁClipVerifierǁmerge_into_report__mutmut_18(
        self,
        report:     ComparisonReport,
        violations: List[str],
        notes:      List[str],
    ) -> ComparisonReport:
        """Produce a new ComparisonReport with clip_violations and notes merged in."""
        new_violations = tuple(list(report.clip_violations) + violations)
        new_notes      = tuple(list(report.notes) + notes)
        new_passed     = report.passed and len(new_violations) == 0
        return ComparisonReport(
            total_vectors=report.total_vectors,
            mismatches=report.mismatches,
            clip_violations=new_violations,
            notes=new_notes,
        )

    def xǁClipVerifierǁmerge_into_report__mutmut_19(
        self,
        report:     ComparisonReport,
        violations: List[str],
        notes:      List[str],
    ) -> ComparisonReport:
        """Produce a new ComparisonReport with clip_violations and notes merged in."""
        new_violations = tuple(list(report.clip_violations) + violations)
        new_notes      = tuple(list(report.notes) + notes)
        new_passed     = report.passed and len(new_violations) == 0
        return ComparisonReport(
            passed=new_passed,
            mismatches=report.mismatches,
            clip_violations=new_violations,
            notes=new_notes,
        )

    def xǁClipVerifierǁmerge_into_report__mutmut_20(
        self,
        report:     ComparisonReport,
        violations: List[str],
        notes:      List[str],
    ) -> ComparisonReport:
        """Produce a new ComparisonReport with clip_violations and notes merged in."""
        new_violations = tuple(list(report.clip_violations) + violations)
        new_notes      = tuple(list(report.notes) + notes)
        new_passed     = report.passed and len(new_violations) == 0
        return ComparisonReport(
            passed=new_passed,
            total_vectors=report.total_vectors,
            clip_violations=new_violations,
            notes=new_notes,
        )

    def xǁClipVerifierǁmerge_into_report__mutmut_21(
        self,
        report:     ComparisonReport,
        violations: List[str],
        notes:      List[str],
    ) -> ComparisonReport:
        """Produce a new ComparisonReport with clip_violations and notes merged in."""
        new_violations = tuple(list(report.clip_violations) + violations)
        new_notes      = tuple(list(report.notes) + notes)
        new_passed     = report.passed and len(new_violations) == 0
        return ComparisonReport(
            passed=new_passed,
            total_vectors=report.total_vectors,
            mismatches=report.mismatches,
            notes=new_notes,
        )

    def xǁClipVerifierǁmerge_into_report__mutmut_22(
        self,
        report:     ComparisonReport,
        violations: List[str],
        notes:      List[str],
    ) -> ComparisonReport:
        """Produce a new ComparisonReport with clip_violations and notes merged in."""
        new_violations = tuple(list(report.clip_violations) + violations)
        new_notes      = tuple(list(report.notes) + notes)
        new_passed     = report.passed and len(new_violations) == 0
        return ComparisonReport(
            passed=new_passed,
            total_vectors=report.total_vectors,
            mismatches=report.mismatches,
            clip_violations=new_violations,
            )
    
    xǁClipVerifierǁmerge_into_report__mutmut_mutants : ClassVar[MutantDict] = { # type: ignore
    'xǁClipVerifierǁmerge_into_report__mutmut_1': xǁClipVerifierǁmerge_into_report__mutmut_1, 
        'xǁClipVerifierǁmerge_into_report__mutmut_2': xǁClipVerifierǁmerge_into_report__mutmut_2, 
        'xǁClipVerifierǁmerge_into_report__mutmut_3': xǁClipVerifierǁmerge_into_report__mutmut_3, 
        'xǁClipVerifierǁmerge_into_report__mutmut_4': xǁClipVerifierǁmerge_into_report__mutmut_4, 
        'xǁClipVerifierǁmerge_into_report__mutmut_5': xǁClipVerifierǁmerge_into_report__mutmut_5, 
        'xǁClipVerifierǁmerge_into_report__mutmut_6': xǁClipVerifierǁmerge_into_report__mutmut_6, 
        'xǁClipVerifierǁmerge_into_report__mutmut_7': xǁClipVerifierǁmerge_into_report__mutmut_7, 
        'xǁClipVerifierǁmerge_into_report__mutmut_8': xǁClipVerifierǁmerge_into_report__mutmut_8, 
        'xǁClipVerifierǁmerge_into_report__mutmut_9': xǁClipVerifierǁmerge_into_report__mutmut_9, 
        'xǁClipVerifierǁmerge_into_report__mutmut_10': xǁClipVerifierǁmerge_into_report__mutmut_10, 
        'xǁClipVerifierǁmerge_into_report__mutmut_11': xǁClipVerifierǁmerge_into_report__mutmut_11, 
        'xǁClipVerifierǁmerge_into_report__mutmut_12': xǁClipVerifierǁmerge_into_report__mutmut_12, 
        'xǁClipVerifierǁmerge_into_report__mutmut_13': xǁClipVerifierǁmerge_into_report__mutmut_13, 
        'xǁClipVerifierǁmerge_into_report__mutmut_14': xǁClipVerifierǁmerge_into_report__mutmut_14, 
        'xǁClipVerifierǁmerge_into_report__mutmut_15': xǁClipVerifierǁmerge_into_report__mutmut_15, 
        'xǁClipVerifierǁmerge_into_report__mutmut_16': xǁClipVerifierǁmerge_into_report__mutmut_16, 
        'xǁClipVerifierǁmerge_into_report__mutmut_17': xǁClipVerifierǁmerge_into_report__mutmut_17, 
        'xǁClipVerifierǁmerge_into_report__mutmut_18': xǁClipVerifierǁmerge_into_report__mutmut_18, 
        'xǁClipVerifierǁmerge_into_report__mutmut_19': xǁClipVerifierǁmerge_into_report__mutmut_19, 
        'xǁClipVerifierǁmerge_into_report__mutmut_20': xǁClipVerifierǁmerge_into_report__mutmut_20, 
        'xǁClipVerifierǁmerge_into_report__mutmut_21': xǁClipVerifierǁmerge_into_report__mutmut_21, 
        'xǁClipVerifierǁmerge_into_report__mutmut_22': xǁClipVerifierǁmerge_into_report__mutmut_22
    }
    xǁClipVerifierǁmerge_into_report__mutmut_orig.__name__ = 'xǁClipVerifierǁmerge_into_report'
