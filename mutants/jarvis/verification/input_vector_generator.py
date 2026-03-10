# jarvis/verification/input_vector_generator.py
# InputVectorGenerator -- produces the fixed input matrix for the harness.
# Authority: DVH Implementation Blueprint v1.0.0 Sections 5 and 7.
#
# NIC-01: No arithmetic operates on production data paths.
# NIC-05: No control flow of the production Risk Engine is altered.
# EEP-07: No random number generation. Matrix is fully deterministic.

from typing import List
from jarvis.verification.data_models.input_vector import InputVector
from jarvis.verification.vectors.vector_definitions import INPUT_MATRIX, VECTOR_COUNT
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


class InputVectorGenerator:
    """
    Returns the fixed, ordered input matrix from vector_definitions.py.

    The matrix is version-controlled. No vector is generated at runtime.
    No sampling is performed. The matrix is identical on every harness run
    for a given harness version (Section 7).
    """

    def generate(self) -> List[InputVector]:
        args = []# type: ignore
        kwargs = {}# type: ignore
        return _mutmut_trampoline(object.__getattribute__(self, 'xǁInputVectorGeneratorǁgenerate__mutmut_orig'), object.__getattribute__(self, 'xǁInputVectorGeneratorǁgenerate__mutmut_mutants'), args, kwargs, self)

    def xǁInputVectorGeneratorǁgenerate__mutmut_orig(self) -> List[InputVector]:
        """
        Return the complete ordered list of InputVector instances.

        Execution order follows Section 7.2:
          G-VOL, G-DD, G-MU, G-RP, G-JM, G-CR, G-BC, G-EX
        Within each group: ascending numeric suffix order.
        """
        return list(INPUT_MATRIX)

    def xǁInputVectorGeneratorǁgenerate__mutmut_1(self) -> List[InputVector]:
        """
        Return the complete ordered list of InputVector instances.

        Execution order follows Section 7.2:
          G-VOL, G-DD, G-MU, G-RP, G-JM, G-CR, G-BC, G-EX
        Within each group: ascending numeric suffix order.
        """
        return list(None)
    
    xǁInputVectorGeneratorǁgenerate__mutmut_mutants : ClassVar[MutantDict] = { # type: ignore
    'xǁInputVectorGeneratorǁgenerate__mutmut_1': xǁInputVectorGeneratorǁgenerate__mutmut_1
    }
    xǁInputVectorGeneratorǁgenerate__mutmut_orig.__name__ = 'xǁInputVectorGeneratorǁgenerate'

    def vector_count(self) -> int:
        """Return total number of vectors in the matrix."""
        return VECTOR_COUNT
