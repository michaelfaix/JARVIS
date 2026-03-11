# jarvis/portfolio/__init__.py
# External portfolio allocation module.
# External to jarvis/core/ and jarvis/risk/ per architecture rules.

from jarvis.portfolio.portfolio_allocator import allocate_positions
from jarvis.portfolio.multi_asset_allocator import (
    AllocationResult,
    MultiAssetCapitalAllocator,
)

__all__ = [
    "allocate_positions",
    "AllocationResult",
    "MultiAssetCapitalAllocator",
]
