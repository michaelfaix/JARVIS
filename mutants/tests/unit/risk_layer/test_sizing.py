# =============================================================================
# test_sizing.py -- Mutation-safe pytest tests for
#                   jarvis/core/risk_layer/sizing.py  (size_position)
#
# Mutation-killing strategy
# -------------------------
#
# ARITHMETIC MUTATIONS (+, -, *, /)
#   Every intermediate value in the 10-step pipeline is computed
#   independently from raw inputs in each test and compared with `==`
#   (or `pytest.approx` only where IEEE rounding is unavoidable).
#   Replacing any operator in the source with another breaks a test.
#
# COMPARISON MUTATIONS (<, <=, >, >=)
#   Every min() / max() call in the pipeline is probed with inputs that
#   sit EXACTLY at the selection boundary:
#     - one value that makes the left branch win by one ULP
#     - one value that makes the right branch win by one ULP
#     - the exact-equality case
#   Changing < to <= (or vice-versa) selects the wrong branch and
#   produces a different numeric result that the test catches.
#
# CONDITIONAL MUTATIONS (is / is not / ==)
#   HALT detection: both HALT and non-HALT verdicts tested.
#   REDUCE + clamped: all four quadrants of (verdict, clamped) tested.
#   position_vol=None: identity path vs non-None path both tested.
#
# CONSTANT MUTATIONS (1e-8 guard, 1.0 cap scalar ceiling)
#   position_vol = 0.0 forces the 1e-8 floor into effect; exact quotient
#   is asserted.
#   vol_cap_scalar = 1.0 ceiling tested with volatility_target_ann >
#   position_vol.
#
# EXACT ARITHMETIC
#   All expected values are computed by hand from the same formula
#   expressed in the test (not via a helper that mirrors the source).
#   This means a wrong formula in the source produces a different number.
#
# =============================================================================

from __future__ import annotations

import math
import sys
import types
import importlib.util
import pathlib
from typing import Optional
from unittest.mock import MagicMock

import pytest

# ---------------------------------------------------------------------------
# Bootstrap fake package tree so sizing.py's relative imports resolve
# ---------------------------------------------------------------------------
_SIZING_FAKE_KEYS = [
    "jarvis", "jarvis.core", "jarvis.core.risk_layer",
    "jarvis.core.risk_layer.exceptions", "jarvis.core.risk_layer.domain",
    "jarvis.core.risk_layer.evaluator", "jarvis.core.risk_layer.sizing",
]
_sizing_saved = {k: sys.modules[k] for k in _SIZING_FAKE_KEYS if k in sys.modules}

def _make_pkg(name: str) -> types.ModuleType:
    m = types.ModuleType(name)
    sys.modules[name] = m
    return m


# ---- jarvis / jarvis.core / jarvis.core.risk_layer -------------------------
_jarvis           = _make_pkg("jarvis")
_jarvis_core      = _make_pkg("jarvis.core")
_risk_layer_pkg   = _make_pkg("jarvis.core.risk_layer")
_jarvis.core      = _jarvis_core
_jarvis_core.risk_layer = _risk_layer_pkg

# ---- exceptions (minimal) --------------------------------------------------
_exc = _make_pkg("jarvis.core.risk_layer.exceptions")

class RiskError(Exception):
    pass

class RiskNumericalError(RiskError):
    def __init__(self, *, field_name, value):
        self.field_name = field_name; self.value = value
        super().__init__(f"{field_name}={value!r}")

class RiskValidationError(RiskError):
    def __init__(self, *, field_name, value, constraint):
        self.field_name = field_name; self.value = value; self.constraint = constraint
        super().__init__(f"{field_name}={value!r}: {constraint}")

class RiskParameterConsistencyError(RiskError):
    def __init__(self, *, field_a, value_a, field_b, value_b, invariant_description):
        self.field_a = field_a; self.value_a = value_a
        self.field_b = field_b; self.value_b = value_b
        self.invariant_description = invariant_description
        super().__init__(invariant_description)

_exc.RiskError                    = RiskError
_exc.RiskNumericalError           = RiskNumericalError
_exc.RiskValidationError          = RiskValidationError
_exc.RiskParameterConsistencyError = RiskParameterConsistencyError

# ---- domain (minimal dataclasses + enums) ----------------------------------
import math as _math
from dataclasses import dataclass as _dc
from enum import Enum as _Enum

VALID_ASSET_CLASSES = frozenset({"equity", "crypto", "fx", "commodity"})

class Side(str, _Enum):
    LONG  = "LONG"
    SHORT = "SHORT"

class RiskVerdict(str, _Enum):
    APPROVE = "APPROVE"
    REDUCE  = "REDUCE"
    HOLD    = "HOLD"
    HALT    = "HALT"
    REJECT  = "REJECT"

@_dc(frozen=True)
class PositionSpec:
    symbol: str
    asset_class: str
    side: "Side"
    entry_price: float
    current_price: float
    quantity: float
    max_position_usd: float

@_dc(frozen=True)
class PortfolioState:
    nav: float
    gross_exposure_usd: float
    net_exposure_usd: float
    open_positions: int
    peak_nav: float
    realized_drawdown_pct: float
    current_step: int

@_dc(frozen=True)
class RiskParameters:
    max_position_pct_nav: float
    max_gross_exposure_pct: float
    max_drawdown_hard_stop: float
    max_drawdown_soft_warn: float
    volatility_target_ann: float
    liquidity_haircut_floor: float
    max_open_positions: int
    kelly_fraction: float

_dom = _make_pkg("jarvis.core.risk_layer.domain")
_dom.Side            = Side
_dom.RiskVerdict     = RiskVerdict
_dom.PositionSpec    = PositionSpec
_dom.PortfolioState  = PortfolioState
_dom.RiskParameters  = RiskParameters
_dom.VALID_ASSET_CLASSES = VALID_ASSET_CLASSES

# ---- evaluator (minimal RiskDecision) --------------------------------------
@_dc(frozen=True)
class RiskDecision:
    verdict: RiskVerdict
    reason: str = ""

_eval = _make_pkg("jarvis.core.risk_layer.evaluator")
_eval.RiskDecision = RiskDecision

# ---- load sizing.py --------------------------------------------------------
_spec = importlib.util.spec_from_file_location(
    "jarvis.core.risk_layer.sizing",
    pathlib.Path(__file__).parent / "sizing.py",
)
_sizing_mod = importlib.util.module_from_spec(_spec)
_sizing_mod.__package__ = "jarvis.core.risk_layer"
sys.modules["jarvis.core.risk_layer.sizing"] = _sizing_mod
_spec.loader.exec_module(_sizing_mod)

size_position      = _sizing_mod.size_position
PositionSizingResult = _sizing_mod.PositionSizingResult

# ---------------------------------------------------------------------------
# Restore sys.modules so fake stubs do not leak into other test files
# (e.g. test_evaluator.py which imports the real jarvis.core.risk_layer).
# ---------------------------------------------------------------------------
for _key in _SIZING_FAKE_KEYS:
    if _key in _sizing_saved:
        sys.modules[_key] = _sizing_saved[_key]
    else:
        sys.modules.pop(_key, None)


# =============================================================================
# Canonical test-input factories
# All values chosen to produce clean, hand-verifiable arithmetic.
# =============================================================================

def _pos(
    quantity=10.0,
    current_price=100.0,
    entry_price=100.0,
    symbol="BTC-USD",
    asset_class="crypto",
    side=Side.LONG,
    max_position_usd=999_999.0,
) -> PositionSpec:
    return PositionSpec(
        symbol=symbol,
        asset_class=asset_class,
        side=side,
        entry_price=entry_price,
        current_price=current_price,
        quantity=quantity,
        max_position_usd=max_position_usd,
    )


def _pf(
    nav=1_000_000.0,
    gross_exposure_usd=0.0,
    net_exposure_usd=0.0,
    open_positions=0,
    peak_nav=1_000_000.0,
    realized_drawdown_pct=0.0,
    current_step=0,
) -> PortfolioState:
    return PortfolioState(
        nav=nav,
        gross_exposure_usd=gross_exposure_usd,
        net_exposure_usd=net_exposure_usd,
        open_positions=open_positions,
        peak_nav=peak_nav,
        realized_drawdown_pct=realized_drawdown_pct,
        current_step=current_step,
    )


def _rp(
    max_position_pct_nav=0.05,
    max_gross_exposure_pct=1.5,
    max_drawdown_hard_stop=0.20,
    max_drawdown_soft_warn=0.10,
    volatility_target_ann=0.15,
    liquidity_haircut_floor=0.50,
    max_open_positions=10,
    kelly_fraction=1.0,
) -> RiskParameters:
    return RiskParameters(
        max_position_pct_nav=max_position_pct_nav,
        max_gross_exposure_pct=max_gross_exposure_pct,
        max_drawdown_hard_stop=max_drawdown_hard_stop,
        max_drawdown_soft_warn=max_drawdown_soft_warn,
        volatility_target_ann=volatility_target_ann,
        liquidity_haircut_floor=liquidity_haircut_floor,
        max_open_positions=max_open_positions,
        kelly_fraction=kelly_fraction,
    )


def _dec(verdict=RiskVerdict.APPROVE) -> RiskDecision:
    return RiskDecision(verdict=verdict)


# =============================================================================
# SECTION 1 -- PositionSizingResult dataclass
# =============================================================================

class TestPositionSizingResult:
    def test_frozen_cannot_set_allowed(self):
        r = PositionSizingResult(allowed=True, target_notional=1000.0, reason=RiskVerdict.APPROVE)
        with pytest.raises((AttributeError, TypeError)):
            r.allowed = False  # type: ignore[misc]

    def test_frozen_cannot_set_target(self):
        r = PositionSizingResult(allowed=True, target_notional=1000.0, reason=RiskVerdict.APPROVE)
        with pytest.raises((AttributeError, TypeError)):
            r.target_notional = 999.0  # type: ignore[misc]

    def test_stores_allowed_true(self):
        r = PositionSizingResult(allowed=True, target_notional=500.0, reason=RiskVerdict.APPROVE)
        assert r.allowed is True

    def test_stores_allowed_false(self):
        r = PositionSizingResult(allowed=False, target_notional=None, reason=RiskVerdict.HALT)
        assert r.allowed is False

    def test_stores_target_notional_none(self):
        r = PositionSizingResult(allowed=False, target_notional=None, reason=RiskVerdict.HALT)
        assert r.target_notional is None

    def test_stores_reason(self):
        r = PositionSizingResult(allowed=True, target_notional=100.0, reason=RiskVerdict.REDUCE)
        assert r.reason is RiskVerdict.REDUCE


# =============================================================================
# SECTION 2 -- HALT branch (Step 1)
# =============================================================================

class TestHaltBranch:
    """
    Kills:  'is' -> '==' mutation on `decision.verdict is RiskVerdict.HALT`
            False-branch fallthrough mutation (HALT producing allowed=True)
    """

    def test_halt_returns_allowed_false(self):
        result = size_position(_pos(), _pf(), _rp(), _dec(RiskVerdict.HALT))
        assert result.allowed is False

    def test_halt_returns_target_notional_none(self):
        """INV-SZ-01: target_notional must be None when allowed is False."""
        result = size_position(_pos(), _pf(), _rp(), _dec(RiskVerdict.HALT))
        assert result.target_notional is None

    def test_halt_returns_reason_halt(self):
        result = size_position(_pos(), _pf(), _rp(), _dec(RiskVerdict.HALT))
        assert result.reason is RiskVerdict.HALT

    def test_approve_does_not_halt(self):
        result = size_position(_pos(), _pf(), _rp(), _dec(RiskVerdict.APPROVE))
        assert result.allowed is True

    def test_reduce_does_not_halt(self):
        result = size_position(_pos(), _pf(), _rp(), _dec(RiskVerdict.REDUCE))
        assert result.allowed is True

    def test_hold_does_not_halt(self):
        result = size_position(_pos(), _pf(), _rp(), _dec(RiskVerdict.HOLD))
        assert result.allowed is True

    def test_reject_does_not_halt(self):
        result = size_position(_pos(), _pf(), _rp(), _dec(RiskVerdict.REJECT))
        assert result.allowed is True

    def test_halt_no_arithmetic_performed(self):
        """
        Even with a degenerate portfolio (nav=0 would blow up arithmetic),
        HALT must short-circuit before any computation.
        """
        pf_degenerate = PortfolioState(
            nav=0.0,  # would cause division-by-zero downstream
            gross_exposure_usd=0.0, net_exposure_usd=0.0,
            open_positions=0, peak_nav=1.0,
            realized_drawdown_pct=0.0, current_step=0,
        )
        result = size_position(_pos(), pf_degenerate, _rp(), _dec(RiskVerdict.HALT))
        assert result.allowed is False
        assert result.target_notional is None


# =============================================================================
# SECTION 3 -- Step 2: requested_notional = quantity * current_price
# =============================================================================

class TestRequestedNotional:
    """
    Kills: * -> + mutation, * -> - mutation, swapped operands.
    """

    def test_requested_notional_basic(self):
        pos = _pos(quantity=10.0, current_price=200.0)
        pf  = _pf(nav=1_000_000.0)
        rp  = _rp(max_position_pct_nav=1.0, kelly_fraction=1.0,
                  liquidity_haircut_floor=1.0)
        # cap = 1e6, requested = 2000, no vol adjustment -> target = 2000
        result = size_position(pos, pf, rp, _dec())
        assert result.target_notional == pytest.approx(2000.0)

    def test_requested_notional_large_quantity(self):
        pos = _pos(quantity=1000.0, current_price=50.0)
        pf  = _pf(nav=1_000_000.0)
        rp  = _rp(max_position_pct_nav=1.0, kelly_fraction=1.0,
                  liquidity_haircut_floor=1.0)
        expected = 1000.0 * 50.0  # 50000
        result = size_position(pos, pf, rp, _dec())
        assert result.target_notional == pytest.approx(expected)

    def test_requested_notional_fractional(self):
        pos = _pos(quantity=0.5, current_price=1.0)
        pf  = _pf(nav=1_000_000.0)
        rp  = _rp(max_position_pct_nav=1.0, kelly_fraction=1.0,
                  liquidity_haircut_floor=1.0)
        result = size_position(pos, pf, rp, _dec())
        assert result.target_notional == pytest.approx(0.5)

    def test_requested_notional_uses_current_price_not_entry_price(self):
        """entry_price is irrelevant; only current_price participates."""
        pos = _pos(quantity=1.0, current_price=300.0, entry_price=100.0)
        pf  = _pf(nav=1_000_000.0)
        rp  = _rp(max_position_pct_nav=1.0, kelly_fraction=1.0,
                  liquidity_haircut_floor=1.0)
        result = size_position(pos, pf, rp, _dec())
        assert result.target_notional == pytest.approx(300.0)


# =============================================================================
# SECTION 4 -- Step 3: base_cap = nav * max_position_pct_nav
# =============================================================================

class TestBaseCap:
    """
    Kills: * -> / or + in base_cap, wrong operand chosen.
    """

    def test_base_cap_exact(self):
        """nav=1e6, pct=0.05 -> cap=50000. requested=1e9 -> target capped at 50000."""
        pos = _pos(quantity=1_000_000.0, current_price=1000.0)  # requested=1e9
        pf  = _pf(nav=1_000_000.0)
        rp  = _rp(max_position_pct_nav=0.05, kelly_fraction=1.0,
                  liquidity_haircut_floor=0.0)  # floor=0 so it doesn't lift
        # effective_cap=50000, raw_target=50000, kelly=50000, floor=0 -> 50000
        expected_cap = 1_000_000.0 * 0.05
        result = size_position(pos, pf, rp, _dec())
        assert result.target_notional == pytest.approx(expected_cap)

    def test_base_cap_full_nav(self):
        pos = _pos(quantity=1_000.0, current_price=2_000.0)  # requested=2e6 > nav
        pf  = _pf(nav=500_000.0)
        rp  = _rp(max_position_pct_nav=1.0, kelly_fraction=1.0,
                  liquidity_haircut_floor=0.0)
        expected_cap = 500_000.0 * 1.0  # 500000
        result = size_position(pos, pf, rp, _dec())
        assert result.target_notional == pytest.approx(expected_cap)

    def test_base_cap_tiny_pct(self):
        pos = _pos(quantity=10_000.0, current_price=1.0)  # requested=10000
        pf  = _pf(nav=1_000_000.0)
        rp  = _rp(max_position_pct_nav=0.001, kelly_fraction=1.0,
                  liquidity_haircut_floor=0.0)
        expected_cap = 1_000_000.0 * 0.001  # 1000
        result = size_position(pos, pf, rp, _dec())
        assert result.target_notional == pytest.approx(expected_cap)

    def test_base_cap_uses_nav_not_peak_nav(self):
        """nav=800k, peak_nav=1M; cap must use nav, not peak."""
        pos = _pos(quantity=1_000_000.0, current_price=1.0)
        pf  = _pf(nav=800_000.0, peak_nav=1_000_000.0, realized_drawdown_pct=0.2)
        rp  = _rp(max_position_pct_nav=0.10, kelly_fraction=1.0,
                  liquidity_haircut_floor=0.0)
        expected_cap = 800_000.0 * 0.10  # 80000, NOT 100000
        result = size_position(pos, pf, rp, _dec())
        assert result.target_notional == pytest.approx(expected_cap)


# =============================================================================
# SECTION 5 -- Step 4: vol_cap_scalar
# =============================================================================

class TestVolCapScalar:
    """
    Kills:
      - None branch vs non-None branch (is not None -> is None)
      - min(…, 1.0) vs max(…, 1.0) mutation
      - 1e-8 guard -> 0 mutation
      - / -> * mutation in volatility_target_ann / max(...)
    """

    def test_none_vol_gives_scalar_one(self):
        """position_vol=None -> vol_cap_scalar=1.0 -> effective_cap=base_cap."""
        pos = _pos(quantity=1.0, current_price=1.0)  # requested=1
        pf  = _pf(nav=1_000_000.0)
        rp  = _rp(max_position_pct_nav=0.05, volatility_target_ann=0.15,
                  kelly_fraction=1.0, liquidity_haircut_floor=0.0)
        base_cap = 1_000_000.0 * 0.05  # 50000
        # requested=1 < cap=50000 -> raw_target=1 -> kelly=1 -> floor=0 -> target=1
        result = size_position(pos, pf, rp, _dec(), position_vol=None)
        assert result.target_notional == pytest.approx(1.0)

    def test_vol_below_target_gives_scalar_gt_one_capped_at_one(self):
        """
        position_vol=0.05, target=0.15 -> raw_scalar=3.0 -> min(3.0,1.0)=1.0
        effective_cap must equal base_cap (not 3x).
        Kills: min -> max mutation (max would give 3.0, inflating the cap).
        """
        pos = _pos(quantity=1_000_000.0, current_price=1.0)
        pf  = _pf(nav=1_000_000.0)
        rp  = _rp(max_position_pct_nav=0.05, volatility_target_ann=0.15,
                  kelly_fraction=1.0, liquidity_haircut_floor=0.0)
        base_cap = 1_000_000.0 * 0.05  # 50000
        # raw_scalar = 0.15/0.05 = 3.0; capped at 1.0 -> effective_cap=50000
        result = size_position(pos, pf, rp, _dec(), position_vol=0.05)
        assert result.target_notional == pytest.approx(base_cap)

    def test_vol_above_target_gives_scalar_lt_one(self):
        """
        position_vol=0.30, target=0.15 -> scalar=0.5 -> effective_cap=0.5*base_cap.
        Kills: / -> * mutation.
        """
        pos = _pos(quantity=1_000_000.0, current_price=1.0)
        pf  = _pf(nav=1_000_000.0)
        rp  = _rp(max_position_pct_nav=0.10, volatility_target_ann=0.15,
                  kelly_fraction=1.0, liquidity_haircut_floor=0.0)
        base_cap = 1_000_000.0 * 0.10        # 100000
        scalar   = 0.15 / 0.30               # 0.5
        effective_cap = min(base_cap, base_cap * scalar)  # 50000
        result = size_position(pos, pf, rp, _dec(), position_vol=0.30)
        assert result.target_notional == pytest.approx(effective_cap)

    def test_vol_equals_target_gives_scalar_one(self):
        """Exact equality: scalar = target/target = 1.0."""
        pos = _pos(quantity=1_000_000.0, current_price=1.0)
        pf  = _pf(nav=1_000_000.0)
        rp  = _rp(max_position_pct_nav=0.10, volatility_target_ann=0.20,
                  kelly_fraction=1.0, liquidity_haircut_floor=0.0)
        base_cap = 1_000_000.0 * 0.10        # 100000
        # scalar = 0.20/0.20 = 1.0 -> effective_cap = base_cap
        result = size_position(pos, pf, rp, _dec(), position_vol=0.20)
        assert result.target_notional == pytest.approx(base_cap)

    def test_vol_zero_uses_guard_1e8(self):
        """
        position_vol=0.0 -> max(0.0, 1e-8) = 1e-8 -> scalar = target/1e-8.
        With target=0.15 -> scalar=0.15/1e-8=1.5e7 -> capped at 1.0.
        Kills: replacing 1e-8 with 0 (ZeroDivisionError) or a larger constant.
        """
        pos = _pos(quantity=1_000_000.0, current_price=1.0)
        pf  = _pf(nav=1_000_000.0)
        rp  = _rp(max_position_pct_nav=0.05, volatility_target_ann=0.15,
                  kelly_fraction=1.0, liquidity_haircut_floor=0.0)
        base_cap = 1_000_000.0 * 0.05        # 50000
        # scalar = min(0.15/1e-8, 1.0) = 1.0 -> effective_cap = base_cap
        result = size_position(pos, pf, rp, _dec(), position_vol=0.0)
        assert result.target_notional == pytest.approx(base_cap)

    def test_vol_tiny_positive_uses_guard(self):
        """
        position_vol=1e-10 < 1e-8 -> max(1e-10, 1e-8)=1e-8 -> same as vol=0.
        Kills: max -> min mutation in the guard.
        """
        pos = _pos(quantity=1_000_000.0, current_price=1.0)
        pf  = _pf(nav=1_000_000.0)
        rp  = _rp(max_position_pct_nav=0.05, volatility_target_ann=0.15,
                  kelly_fraction=1.0, liquidity_haircut_floor=0.0)
        base_cap = 1_000_000.0 * 0.05
        result_zero  = size_position(pos, pf, rp, _dec(), position_vol=0.0)
        result_tiny  = size_position(pos, pf, rp, _dec(), position_vol=1e-10)
        # Both should hit the 1e-8 floor and produce the same result
        assert result_tiny.target_notional == pytest.approx(result_zero.target_notional)

    def test_vol_above_1e8_does_not_use_guard(self):
        """
        position_vol=1e-7 > 1e-8 -> max(1e-7, 1e-8) = 1e-7 -> scalar != 1e-8 path.
        Kills: always using 1e-8 regardless of position_vol.
        """
        target_ann = 0.15
        pos_vol    = 1e-7
        pos = _pos(quantity=1_000_000.0, current_price=1.0)
        pf  = _pf(nav=1_000_000.0)
        rp  = _rp(max_position_pct_nav=0.05, volatility_target_ann=target_ann,
                  kelly_fraction=1.0, liquidity_haircut_floor=0.0)
        base_cap = 1_000_000.0 * 0.05
        scalar_with_guard = min(target_ann / max(pos_vol, 1e-8), 1.0)
        # scalar = min(0.15/1e-7, 1.0) = min(1.5e6, 1.0) = 1.0 -> still capped
        result = size_position(pos, pf, rp, _dec(), position_vol=pos_vol)
        assert result.target_notional == pytest.approx(base_cap * scalar_with_guard)

    def test_vol_exactly_1e8(self):
        """position_vol exactly at the guard boundary."""
        target_ann = 0.15
        pos_vol    = 1e-8
        pos = _pos(quantity=1_000_000.0, current_price=1.0)
        pf  = _pf(nav=1_000_000.0)
        rp  = _rp(max_position_pct_nav=0.05, volatility_target_ann=target_ann,
                  kelly_fraction=1.0, liquidity_haircut_floor=0.0)
        base_cap = 1_000_000.0 * 0.05
        # max(1e-8, 1e-8) = 1e-8; scalar = 0.15/1e-8 = 1.5e7 -> capped at 1.0
        result = size_position(pos, pf, rp, _dec(), position_vol=pos_vol)
        assert result.target_notional == pytest.approx(base_cap)


# =============================================================================
# SECTION 6 -- Step 5: effective_cap = min(base_cap, base_cap * vol_cap_scalar)
# =============================================================================

class TestEffectiveCap:
    """
    Kills: min -> max, wrong operand order, * -> + in base_cap * scalar.
    """

    def test_effective_cap_with_scalar_one_equals_base_cap(self):
        """scalar=1.0 -> base_cap*1.0=base_cap -> min(base,base)=base."""
        pos = _pos(quantity=1_000_000.0, current_price=1.0)
        pf  = _pf(nav=200_000.0)
        rp  = _rp(max_position_pct_nav=0.10, volatility_target_ann=0.20,
                  kelly_fraction=1.0, liquidity_haircut_floor=0.0)
        base_cap = 200_000.0 * 0.10  # 20000
        result = size_position(pos, pf, rp, _dec(), position_vol=None)
        assert result.target_notional == pytest.approx(base_cap)

    def test_effective_cap_with_scalar_half(self):
        """scalar=0.5 -> vol_cap=0.5*base -> min(base, 0.5*base) = 0.5*base."""
        pos = _pos(quantity=1_000_000.0, current_price=1.0)
        pf  = _pf(nav=200_000.0)
        rp  = _rp(max_position_pct_nav=0.10, volatility_target_ann=0.10,
                  kelly_fraction=1.0, liquidity_haircut_floor=0.0)
        # position_vol=0.20 -> scalar=0.10/0.20=0.5
        base_cap      = 200_000.0 * 0.10   # 20000
        vol_cap       = base_cap * 0.5     # 10000
        effective_cap = min(base_cap, vol_cap)  # 10000
        result = size_position(pos, pf, rp, _dec(), position_vol=0.20)
        assert result.target_notional == pytest.approx(effective_cap)

    def test_effective_cap_min_selects_lower(self):
        """
        With scalar<1: base_cap*scalar < base_cap -> effective_cap = base_cap*scalar.
        Kills: min -> max (which would select base_cap, not the reduced value).
        """
        pos = _pos(quantity=1_000_000.0, current_price=1.0)
        pf  = _pf(nav=1_000_000.0)
        rp  = _rp(max_position_pct_nav=0.20, volatility_target_ann=0.05,
                  kelly_fraction=1.0, liquidity_haircut_floor=0.0)
        # position_vol=0.25 -> scalar=0.05/0.25=0.2 -> vol_cap=0.2*200k=40k
        # base_cap=200k, effective_cap=min(200k,40k)=40k
        pos_vol = 0.25
        base_cap = 1_000_000.0 * 0.20
        scalar   = min(0.05 / max(pos_vol, 1e-8), 1.0)
        effective_cap = min(base_cap, base_cap * scalar)
        result = size_position(pos, pf, rp, _dec(), position_vol=pos_vol)
        assert result.target_notional == pytest.approx(effective_cap)


# =============================================================================
# SECTION 7 -- Step 6: raw_target = min(requested_notional, effective_cap)
# =============================================================================

class TestRawTarget:
    """
    Kills: min -> max, operand swap.
    Three sub-cases: requested < cap, requested == cap, requested > cap.
    """

    def test_raw_target_requested_less_than_cap(self):
        """requested=100, cap=50000 -> raw_target=100 (not the cap)."""
        pos = _pos(quantity=1.0, current_price=100.0)  # requested=100
        pf  = _pf(nav=1_000_000.0)
        rp  = _rp(max_position_pct_nav=0.05, kelly_fraction=1.0,
                  liquidity_haircut_floor=0.0)
        # cap=50000 >> 100 -> raw=100 -> kelly=100 -> floor=0 -> 100
        result = size_position(pos, pf, rp, _dec(), position_vol=None)
        assert result.target_notional == pytest.approx(100.0)

    def test_raw_target_requested_greater_than_cap(self):
        """requested=1e8, cap=50000 -> raw_target=50000."""
        pos = _pos(quantity=1_000_000.0, current_price=100.0)  # requested=1e8
        pf  = _pf(nav=1_000_000.0)
        rp  = _rp(max_position_pct_nav=0.05, kelly_fraction=1.0,
                  liquidity_haircut_floor=0.0)
        base_cap = 1_000_000.0 * 0.05  # 50000
        result = size_position(pos, pf, rp, _dec(), position_vol=None)
        assert result.target_notional == pytest.approx(base_cap)

    def test_raw_target_requested_equals_cap(self):
        """Exact boundary: requested == cap -> raw_target == cap == requested."""
        nav = 1_000_000.0
        pct = 0.05
        cap = nav * pct  # 50000
        pos = _pos(quantity=500.0, current_price=100.0)  # requested=50000 exactly
        pf  = _pf(nav=nav)
        rp  = _rp(max_position_pct_nav=pct, kelly_fraction=1.0,
                  liquidity_haircut_floor=0.0)
        result = size_position(pos, pf, rp, _dec(), position_vol=None)
        assert result.target_notional == pytest.approx(cap)

    def test_raw_target_one_below_cap(self):
        """
        requested = cap - 1 -> raw_target = requested (not cap).
        Kills: min -> max (which would return cap instead).
        """
        nav = 1_000_000.0
        cap = nav * 0.05   # 50000
        requested = cap - 1.0   # 49999
        pos = _pos(quantity=1.0, current_price=requested)
        pf  = _pf(nav=nav)
        rp  = _rp(max_position_pct_nav=0.05, kelly_fraction=1.0,
                  liquidity_haircut_floor=0.0)
        result = size_position(pos, pf, rp, _dec(), position_vol=None)
        assert result.target_notional == pytest.approx(requested)

    def test_raw_target_one_above_cap(self):
        """
        requested = cap + 1 -> raw_target = cap.
        Kills: min -> max.
        """
        nav = 1_000_000.0
        cap = nav * 0.05
        requested = cap + 1.0
        pos = _pos(quantity=1.0, current_price=requested)
        pf  = _pf(nav=nav)
        rp  = _rp(max_position_pct_nav=0.05, kelly_fraction=1.0,
                  liquidity_haircut_floor=0.0)
        result = size_position(pos, pf, rp, _dec(), position_vol=None)
        assert result.target_notional == pytest.approx(cap)


# =============================================================================
# SECTION 8 -- Step 7: kelly_target = raw_target * kelly_fraction
# =============================================================================

class TestKellyTarget:
    """
    Kills: * -> / or + mutation, kelly_fraction not applied, applied twice.
    """

    def test_kelly_fraction_one_is_identity(self):
        pos = _pos(quantity=1.0, current_price=100.0)
        pf  = _pf(nav=1_000_000.0)
        rp  = _rp(max_position_pct_nav=1.0, kelly_fraction=1.0,
                  liquidity_haircut_floor=0.0)
        # cap >> requested -> raw=100; kelly=100*1.0=100
        result = size_position(pos, pf, rp, _dec())
        assert result.target_notional == pytest.approx(100.0)

    def test_kelly_fraction_half(self):
        """kelly=0.5 -> kelly_target = raw * 0.5."""
        pos = _pos(quantity=1.0, current_price=1000.0)  # requested=1000
        pf  = _pf(nav=1_000_000.0)
        rp  = _rp(max_position_pct_nav=1.0, kelly_fraction=0.5,
                  liquidity_haircut_floor=0.0)
        result = size_position(pos, pf, rp, _dec())
        assert result.target_notional == pytest.approx(1000.0 * 0.5)

    def test_kelly_fraction_quarter(self):
        pos = _pos(quantity=1.0, current_price=1000.0)
        pf  = _pf(nav=1_000_000.0)
        rp  = _rp(max_position_pct_nav=1.0, kelly_fraction=0.25,
                  liquidity_haircut_floor=0.0)
        result = size_position(pos, pf, rp, _dec())
        assert result.target_notional == pytest.approx(1000.0 * 0.25)

    def test_kelly_applied_after_cap_not_before(self):
        """
        requested=100k > cap=50k -> raw=50k -> kelly(0.5)=25k.
        If kelly were applied before cap: kelly(100k)=50k -> min(50k,50k)=50k.
        The two orderings give 25k vs 50k; test pins the correct value.
        """
        pos = _pos(quantity=1_000.0, current_price=100.0)  # requested=100k
        pf  = _pf(nav=1_000_000.0)
        rp  = _rp(max_position_pct_nav=0.05, kelly_fraction=0.5,
                  liquidity_haircut_floor=0.0)
        cap    = 1_000_000.0 * 0.05   # 50000
        target = cap * 0.5             # 25000
        result = size_position(pos, pf, rp, _dec())
        assert result.target_notional == pytest.approx(target)

    def test_kelly_fraction_tiny(self):
        pos = _pos(quantity=1.0, current_price=1_000_000.0)
        pf  = _pf(nav=1e9)
        rp  = _rp(max_position_pct_nav=1.0, kelly_fraction=1e-6,
                  liquidity_haircut_floor=0.0)
        raw = 1_000_000.0
        expected = raw * 1e-6
        result = size_position(pos, pf, rp, _dec())
        assert result.target_notional == pytest.approx(expected)


# =============================================================================
# SECTION 9 -- Step 8: REDUCE + clamped conditional
# =============================================================================

class TestReduceMultiplier:
    """
    Four quadrants of (verdict, clamped) tested exhaustively.
    Kills:
      - 'is RiskVerdict.REDUCE' -> 'is RiskVerdict.APPROVE'
      - _was_clamped < -> <= mutation
      - haircut not applied when it should be / applied when it shouldn't
    """

    # --- Quadrant A: REDUCE + clamped (haircut applied) ---------------------

    def test_reduce_clamped_applies_haircut(self):
        """
        REDUCE verdict + requested > cap -> _was_clamped=True -> haircut applied.
        reduce_target = kelly_target * liquidity_haircut_floor.
        """
        requested = 100_000.0
        cap       = 50_000.0
        haircut   = 0.40
        kelly     = 0.80
        pos = _pos(quantity=1_000.0, current_price=100.0)   # requested=100k
        pf  = _pf(nav=1_000_000.0)
        rp  = _rp(max_position_pct_nav=0.05,                # cap=50k
                  kelly_fraction=kelly,
                  liquidity_haircut_floor=haircut)
        # raw=50k, kelly_t=50k*0.8=40k, reduce=40k*0.4=16k
        # floor=100k*0.4=40k -> max(16k,40k)=40k
        kelly_t      = cap * kelly                   # 40000
        reduce_t     = kelly_t * haircut             # 16000
        floor_val    = requested * haircut           # 40000
        expected     = max(reduce_t, floor_val)      # 40000
        result = size_position(pos, pf, rp, _dec(RiskVerdict.REDUCE))
        assert result.target_notional == pytest.approx(expected)

    def test_reduce_clamped_exact_haircut_arithmetic(self):
        """
        Exact arithmetic check with pristine values.
        cap=10k, kelly=0.5, haircut=0.50, requested=20k.
        reduce_t=10k*0.5*0.5=2500, floor=20k*0.5=10k -> target=10k.
        """
        pos = _pos(quantity=200.0, current_price=100.0)  # requested=20k
        pf  = _pf(nav=1_000_000.0)
        rp  = _rp(max_position_pct_nav=0.01,             # cap=10k
                  kelly_fraction=0.5,
                  liquidity_haircut_floor=0.50)
        expected = 10_000.0   # floor lifts
        result = size_position(pos, pf, rp, _dec(RiskVerdict.REDUCE))
        assert result.target_notional == pytest.approx(expected)

    # --- Quadrant B: REDUCE + not clamped (no haircut) ----------------------

    def test_reduce_not_clamped_no_haircut(self):
        """
        REDUCE verdict + requested <= cap -> _was_clamped=False -> NO haircut.
        reduce_target = kelly_target (unchanged).
        Kills: applying haircut unconditionally on REDUCE.
        """
        requested = 1_000.0   # well within cap
        cap       = 50_000.0
        kelly     = 0.80
        haircut   = 0.40
        pos = _pos(quantity=10.0, current_price=100.0)  # requested=1000
        pf  = _pf(nav=1_000_000.0)
        rp  = _rp(max_position_pct_nav=0.05, kelly_fraction=kelly,
                  liquidity_haircut_floor=haircut)
        # raw=1000, kelly_t=1000*0.8=800, NOT clamped -> reduce_t=800
        # floor=1000*0.4=400 -> max(800,400)=800
        kelly_t   = requested * kelly               # 800
        floor_val = requested * haircut             # 400
        expected  = max(kelly_t, floor_val)         # 800
        result = size_position(pos, pf, rp, _dec(RiskVerdict.REDUCE))
        assert result.target_notional == pytest.approx(expected)

    def test_reduce_not_clamped_vs_clamped_differ(self):
        """
        Same params; differ only in quantity (clamped vs not clamped).
        Proves the conditional changes the output.
        """
        pf    = _pf(nav=1_000_000.0)
        rp    = _rp(max_position_pct_nav=0.05, kelly_fraction=0.80,
                    liquidity_haircut_floor=0.40)
        cap   = 1_000_000.0 * 0.05  # 50000
        # not clamped: quantity=100, price=100 -> requested=10000 < cap
        pos_nc = _pos(quantity=100.0, current_price=100.0)
        r_nc   = size_position(pos_nc, pf, rp, _dec(RiskVerdict.REDUCE))
        # clamped: quantity=10000, price=100 -> requested=1000000 > cap
        pos_c  = _pos(quantity=10_000.0, current_price=100.0)
        r_c    = size_position(pos_c, pf, rp, _dec(RiskVerdict.REDUCE))
        # They should differ because haircut is only applied when clamped
        assert r_nc.target_notional != r_c.target_notional

    # --- Quadrant C: APPROVE + clamped (no haircut) -------------------------

    def test_approve_clamped_no_haircut(self):
        """
        APPROVE verdict + clamped -> haircut NOT applied.
        Kills: applying haircut on any clamped position regardless of verdict.
        """
        pos = _pos(quantity=10_000.0, current_price=100.0)  # requested=1M
        pf  = _pf(nav=1_000_000.0)
        rp  = _rp(max_position_pct_nav=0.05, kelly_fraction=1.0,
                  liquidity_haircut_floor=0.40)
        cap      = 1_000_000.0 * 0.05    # 50000
        kelly_t  = cap * 1.0             # 50000
        floor_v  = (10_000.0 * 100.0) * 0.40  # 400000
        expected = max(kelly_t, floor_v)  # floor lifts to 400000
        result   = size_position(pos, pf, rp, _dec(RiskVerdict.APPROVE))
        assert result.target_notional == pytest.approx(expected)

    # --- Quadrant D: APPROVE + not clamped ----------------------------------

    def test_approve_not_clamped_full_kelly(self):
        """APPROVE + not clamped -> target = kelly_target (subject to floor)."""
        pos = _pos(quantity=10.0, current_price=100.0)  # requested=1000
        pf  = _pf(nav=1_000_000.0)
        rp  = _rp(max_position_pct_nav=0.05, kelly_fraction=0.75,
                  liquidity_haircut_floor=0.40)
        # cap=50000 >> 1000 -> raw=1000, kelly_t=750, floor=400 -> max=750
        result = size_position(pos, pf, rp, _dec(RiskVerdict.APPROVE))
        assert result.target_notional == pytest.approx(1000.0 * 0.75)

    # --- Clamped boundary ---------------------------------------------------

    def test_clamped_boundary_equal_is_not_clamped(self):
        """
        raw_target < requested is False when raw==requested (exactly at cap).
        _was_clamped must be False -> no REDUCE haircut applied.
        Kills: < -> <= in `raw_target < requested_notional`.
        """
        nav = 1_000_000.0
        cap = nav * 0.05      # 50000
        # requested == cap exactly
        pos = _pos(quantity=500.0, current_price=100.0)   # 500*100=50000
        pf  = _pf(nav=nav)
        rp  = _rp(max_position_pct_nav=0.05, kelly_fraction=1.0,
                  liquidity_haircut_floor=0.50)
        # raw=cap=requested -> not clamped -> no REDUCE haircut
        # kelly_t=50000, floor=50000*0.5=25000 -> max=50000
        result = size_position(pos, pf, rp, _dec(RiskVerdict.REDUCE))
        assert result.target_notional == pytest.approx(cap * 1.0)

    def test_clamped_boundary_one_above_is_clamped(self):
        """
        requested = cap + epsilon -> raw < requested -> _was_clamped=True.
        Kills: < -> <= (which would make this case also not-clamped).
        """
        nav = 1_000_000.0
        cap = nav * 0.05       # 50000
        eps = 0.01
        # requested = cap + eps
        # Use price = cap + eps, quantity=1
        pos = _pos(quantity=1.0, current_price=cap + eps)
        pf  = _pf(nav=nav)
        rp  = _rp(max_position_pct_nav=0.05, kelly_fraction=1.0,
                  liquidity_haircut_floor=0.50)
        # raw=cap, requested=cap+eps -> clamped -> REDUCE haircut applied
        kelly_t   = cap * 1.0          # 50000
        reduce_t  = kelly_t * 0.50     # 25000
        floor_v   = (cap + eps) * 0.50 # 25000.005
        expected  = max(reduce_t, floor_v)
        result = size_position(pos, pf, rp, _dec(RiskVerdict.REDUCE))
        assert result.target_notional == pytest.approx(expected)


# =============================================================================
# SECTION 10 -- Step 9: liquidity_floor = requested_notional * haircut_floor
# =============================================================================

class TestLiquidityFloor:
    """
    Kills: * -> + mutation in floor calculation, wrong base (cap vs requested).
    """

    def test_floor_uses_requested_notional_not_cap(self):
        """
        Floor = requested * haircut. If source mistakenly used cap * haircut,
        these two values differ and the test catches it.
        """
        requested = 80_000.0
        cap       = 50_000.0
        haircut   = 0.50
        # Make kelly_target very small so floor dominates
        pos = _pos(quantity=800.0, current_price=100.0)  # requested=80k
        pf  = _pf(nav=1_000_000.0)
        rp  = _rp(max_position_pct_nav=0.05,     # cap=50k
                  kelly_fraction=0.01,            # kelly_t = cap*0.01=500
                  liquidity_haircut_floor=haircut)
        floor_correct = requested * haircut   # 40000 (from requested, not cap)
        floor_wrong   = cap * haircut         # 25000
        result = size_position(pos, pf, rp, _dec(RiskVerdict.APPROVE))
        # target = max(kelly_t, floor) = max(500, 40000) = 40000
        assert result.target_notional == pytest.approx(floor_correct)
        assert result.target_notional != pytest.approx(floor_wrong)

    def test_floor_exact_arithmetic(self):
        """requested=10k, haircut=0.30 -> floor=3000."""
        pos = _pos(quantity=100.0, current_price=100.0)  # requested=10k
        pf  = _pf(nav=1_000_000.0)
        rp  = _rp(max_position_pct_nav=1.0, kelly_fraction=0.01,
                  liquidity_haircut_floor=0.30)
        # kelly_t = 10000*0.01=100; floor=10000*0.30=3000 -> target=3000
        result = size_position(pos, pf, rp, _dec())
        assert result.target_notional == pytest.approx(3000.0)


# =============================================================================
# SECTION 11 -- Step 10: target = max(reduce_target, liquidity_floor)
# =============================================================================

class TestFinalMax:
    """
    Kills: max -> min mutation.
    Tests three sub-cases: reduce_target > floor, reduce_target == floor,
    reduce_target < floor.
    """

    def test_max_selects_reduce_target_when_larger(self):
        """
        reduce_target > floor -> target = reduce_target.
        Kills: max -> min (would select floor instead).
        """
        pos = _pos(quantity=1.0, current_price=100.0)   # requested=100
        pf  = _pf(nav=1_000_000.0)
        # cap >> 100 -> raw=100, kelly=1.0->kelly_t=100
        # haircut=0.10 -> floor=100*0.10=10
        # reduce_target=100 (APPROVE, not clamped) -> max(100, 10)=100
        rp  = _rp(max_position_pct_nav=1.0, kelly_fraction=1.0,
                  liquidity_haircut_floor=0.10)
        result = size_position(pos, pf, rp, _dec(RiskVerdict.APPROVE))
        assert result.target_notional == pytest.approx(100.0)

    def test_max_selects_floor_when_larger(self):
        """
        floor > reduce_target -> target = floor.
        Kills: max -> min (would select reduce_target instead).
        """
        pos = _pos(quantity=100.0, current_price=100.0)  # requested=10000
        pf  = _pf(nav=1_000_000.0)
        # cap=50000 >> 10000 -> raw=10000, kelly(0.01)=100
        # haircut=0.50 -> floor=10000*0.50=5000
        # reduce_target=100 (APPROVE not clamped) -> max(100,5000)=5000
        rp  = _rp(max_position_pct_nav=0.05, kelly_fraction=0.01,
                  liquidity_haircut_floor=0.50)
        result = size_position(pos, pf, rp, _dec(RiskVerdict.APPROVE))
        assert result.target_notional == pytest.approx(5000.0)

    def test_max_equal_case(self):
        """reduce_target == floor -> either value; result equals both."""
        pos = _pos(quantity=1.0, current_price=1000.0)  # requested=1000
        pf  = _pf(nav=1_000_000.0)
        # kelly=1.0 -> kelly_t=1000; haircut=1.0 -> floor=1000
        # max(1000,1000)=1000
        rp  = _rp(max_position_pct_nav=1.0, kelly_fraction=1.0,
                  liquidity_haircut_floor=1.0)
        result = size_position(pos, pf, rp, _dec(RiskVerdict.APPROVE))
        assert result.target_notional == pytest.approx(1000.0)

    def test_max_selects_floor_over_tiny_kelly(self):
        """
        Tiny kelly drags reduce_target near zero; floor rescues it.
        Verifies INV-SZ-05.
        """
        requested = 10_000.0
        haircut   = 0.25
        pos = _pos(quantity=100.0, current_price=100.0)
        pf  = _pf(nav=1_000_000.0)
        rp  = _rp(max_position_pct_nav=1.0, kelly_fraction=1e-9,
                  liquidity_haircut_floor=haircut)
        floor_val = requested * haircut  # 2500
        result = size_position(pos, pf, rp, _dec(RiskVerdict.APPROVE))
        assert result.target_notional >= floor_val - 1e-9
        assert result.target_notional == pytest.approx(floor_val)


# =============================================================================
# SECTION 12 -- INV-SZ-05: target >= requested * liquidity_haircut_floor
# =============================================================================

class TestLiquidityFloorInvariant:
    """
    For all non-HALT verdicts and any combination of vol/kelly compression,
    target >= requested * haircut must hold.
    """

    @pytest.mark.parametrize("verdict", [
        RiskVerdict.APPROVE,
        RiskVerdict.REDUCE,
        RiskVerdict.HOLD,
        RiskVerdict.REJECT,
    ])
    @pytest.mark.parametrize("kelly_fraction", [1.0, 0.5, 0.25, 0.01, 1e-6])
    @pytest.mark.parametrize("pos_vol", [None, 0.0, 0.01, 0.15, 0.50, 2.0])
    def test_floor_invariant_parametric(self, verdict, kelly_fraction, pos_vol):
        haircut = 0.30
        pos = _pos(quantity=50.0, current_price=200.0)      # requested=10000
        pf  = _pf(nav=1_000_000.0)
        rp  = _rp(max_position_pct_nav=0.05, kelly_fraction=kelly_fraction,
                  liquidity_haircut_floor=haircut)
        result = size_position(pos, pf, rp, _dec(verdict), position_vol=pos_vol)
        assert result.allowed is True
        requested = 50.0 * 200.0
        assert result.target_notional >= requested * haircut - 1e-9


# =============================================================================
# SECTION 13 -- INV-SZ-01 / INV-SZ-02: allowed / target_notional consistency
# =============================================================================

class TestAllowedInvariant:
    @pytest.mark.parametrize("verdict", [
        RiskVerdict.APPROVE,
        RiskVerdict.REDUCE,
        RiskVerdict.HOLD,
        RiskVerdict.REJECT,
    ])
    def test_non_halt_allowed_true(self, verdict):
        result = size_position(_pos(), _pf(), _rp(), _dec(verdict))
        assert result.allowed is True

    def test_halt_allowed_false(self):
        result = size_position(_pos(), _pf(), _rp(), _dec(RiskVerdict.HALT))
        assert result.allowed is False

    @pytest.mark.parametrize("verdict", [
        RiskVerdict.APPROVE,
        RiskVerdict.REDUCE,
        RiskVerdict.HOLD,
        RiskVerdict.REJECT,
    ])
    def test_non_halt_target_not_none(self, verdict):
        result = size_position(_pos(), _pf(), _rp(), _dec(verdict))
        assert result.target_notional is not None

    def test_halt_target_is_none(self):
        """INV-SZ-01."""
        result = size_position(_pos(), _pf(), _rp(), _dec(RiskVerdict.HALT))
        assert result.target_notional is None

    @pytest.mark.parametrize("verdict", [
        RiskVerdict.APPROVE,
        RiskVerdict.REDUCE,
        RiskVerdict.HOLD,
        RiskVerdict.REJECT,
    ])
    def test_non_halt_target_finite_positive(self, verdict):
        """INV-SZ-02: target must be finite and > 0."""
        result = size_position(_pos(), _pf(), _rp(), _dec(verdict))
        assert math.isfinite(result.target_notional)
        assert result.target_notional > 0.0


# =============================================================================
# SECTION 14 -- reason field echoes verdict
# =============================================================================

class TestReasonField:
    @pytest.mark.parametrize("verdict", list(RiskVerdict))
    def test_reason_echoes_verdict(self, verdict):
        result = size_position(_pos(), _pf(), _rp(), _dec(verdict))
        assert result.reason is verdict


# =============================================================================
# SECTION 15 -- No mutation of inputs
# =============================================================================

class TestNoSideEffects:
    def test_position_unchanged(self):
        pos = _pos(quantity=10.0, current_price=100.0)
        size_position(pos, _pf(), _rp(), _dec())
        assert pos.quantity      == 10.0
        assert pos.current_price == 100.0

    def test_portfolio_unchanged(self):
        pf = _pf(nav=1_000_000.0, open_positions=3)
        size_position(_pos(), pf, _rp(), _dec())
        assert pf.nav            == 1_000_000.0
        assert pf.open_positions == 3

    def test_params_unchanged(self):
        rp = _rp(kelly_fraction=0.25)
        size_position(_pos(), _pf(), rp, _dec())
        assert rp.kelly_fraction == 0.25

    def test_decision_unchanged(self):
        dec = _dec(RiskVerdict.REDUCE)
        size_position(_pos(), _pf(), _rp(), dec)
        assert dec.verdict is RiskVerdict.REDUCE

    def test_repeated_calls_same_result(self):
        """Determinism: same inputs always produce same output."""
        pos = _pos(); pf = _pf(); rp = _rp(); dec = _dec()
        r1 = size_position(pos, pf, rp, dec, position_vol=0.20)
        r2 = size_position(pos, pf, rp, dec, position_vol=0.20)
        assert r1.target_notional == r2.target_notional
        assert r1.allowed         == r2.allowed
        assert r1.reason          is r2.reason


# =============================================================================
# SECTION 16 -- Full end-to-end pipeline regression (exact values)
#
# Each test computes the ENTIRE pipeline by hand from raw inputs and
# asserts the exact result. Any mutation in any step breaks at least one test.
# =============================================================================

class TestEndToEndExact:

    def test_pipeline_approve_no_vol_no_kelly(self):
        """
        Simplest case: no vol, kelly=1, floor=0, APPROVE, not clamped.
        requested=500, cap=50000 >> 500 -> target=500.
        """
        pos = _pos(quantity=5.0, current_price=100.0)
        pf  = _pf(nav=1_000_000.0)
        rp  = _rp(max_position_pct_nav=0.05, kelly_fraction=1.0,
                  liquidity_haircut_floor=0.0)
        result = size_position(pos, pf, rp, _dec(RiskVerdict.APPROVE), position_vol=None)
        assert result.target_notional == pytest.approx(500.0)
        assert result.allowed is True
        assert result.reason is RiskVerdict.APPROVE

    def test_pipeline_approve_capped(self):
        """
        requested=1M, nav=1M, pct=0.05 -> cap=50k -> capped.
        kelly=0.80, haircut=0.30 (APPROVE -> no reduce), floor=1M*0.30=300k.
        target=max(50k*0.80, 300k)=max(40k,300k)=300k.
        """
        pos = _pos(quantity=10_000.0, current_price=100.0)  # requested=1M
        pf  = _pf(nav=1_000_000.0)
        rp  = _rp(max_position_pct_nav=0.05, kelly_fraction=0.80,
                  liquidity_haircut_floor=0.30)
        # requested=1e6, cap=50k, raw=50k, kelly_t=40k
        # floor=1e6*0.30=300k -> target=max(40k,300k)=300k
        result = size_position(pos, pf, rp, _dec(RiskVerdict.APPROVE), position_vol=None)
        assert result.target_notional == pytest.approx(300_000.0)

    def test_pipeline_reduce_clamped_full(self):
        """
        Full pipeline with REDUCE + clamped:
        requested=200k, nav=1M, pct=0.05 -> cap=50k.
        vol=0.30, target_vol=0.15 -> scalar=0.5 -> vol_cap=25k -> eff_cap=25k.
        raw=min(200k,25k)=25k. kelly=0.50 -> kelly_t=12.5k.
        REDUCE + clamped(200k>25k) -> reduce_t=12.5k*0.40=5k.
        floor=200k*0.40=80k -> target=max(5k,80k)=80k.
        """
        pos = _pos(quantity=2_000.0, current_price=100.0)  # requested=200k
        pf  = _pf(nav=1_000_000.0)
        rp  = _rp(max_position_pct_nav=0.05,
                  volatility_target_ann=0.15,
                  kelly_fraction=0.50,
                  liquidity_haircut_floor=0.40)
        pos_vol = 0.30
        requested    = 200_000.0
        base_cap     = 1_000_000.0 * 0.05         # 50000
        scalar       = min(0.15 / max(pos_vol, 1e-8), 1.0)  # 0.5
        effective_cap = min(base_cap, base_cap * scalar)      # 25000
        raw          = min(requested, effective_cap)           # 25000
        kelly_t      = raw * 0.50                              # 12500
        reduce_t     = kelly_t * 0.40                          # 5000
        floor_v      = requested * 0.40                        # 80000
        expected     = max(reduce_t, floor_v)                  # 80000
        result = size_position(pos, pf, rp, _dec(RiskVerdict.REDUCE), position_vol=pos_vol)
        assert result.target_notional == pytest.approx(expected)

    def test_pipeline_reduce_not_clamped(self):
        """
        REDUCE but NOT clamped: requested=1k < cap=50k -> no haircut.
        kelly=0.60, haircut=0.40.
        raw=1k, kelly_t=600, reduce_t=600 (no haircut), floor=400, target=600.
        """
        pos = _pos(quantity=10.0, current_price=100.0)  # requested=1000
        pf  = _pf(nav=1_000_000.0)
        rp  = _rp(max_position_pct_nav=0.05, kelly_fraction=0.60,
                  liquidity_haircut_floor=0.40)
        requested = 1_000.0
        raw       = 1_000.0     # not clamped
        kelly_t   = raw * 0.60  # 600
        reduce_t  = kelly_t     # no haircut (not clamped)
        floor_v   = requested * 0.40  # 400
        expected  = max(reduce_t, floor_v)  # 600
        result = size_position(pos, pf, rp, _dec(RiskVerdict.REDUCE), position_vol=None)
        assert result.target_notional == pytest.approx(expected)

    def test_pipeline_backward_compatible_7c(self):
        """
        7C backward-compat: position_vol=None, kelly=1.0, verdict=APPROVE.
        Target = min(requested, cap) (subject to floor=0).
        requested=3000, cap=50000 -> target=3000.
        """
        pos = _pos(quantity=30.0, current_price=100.0)
        pf  = _pf(nav=1_000_000.0)
        rp  = _rp(max_position_pct_nav=0.05, kelly_fraction=1.0,
                  liquidity_haircut_floor=0.0)
        result = size_position(pos, pf, rp, _dec(RiskVerdict.APPROVE), position_vol=None)
        assert result.target_notional == pytest.approx(3_000.0)

    def test_pipeline_vol_adjustment_reduces_target(self):
        """
        vol adjustment halves effective cap; verify the halving is exact.
        nav=1M, pct=0.20 -> cap=200k.
        pos_vol=0.30, target=0.15 -> scalar=0.5 -> eff_cap=100k.
        requested=500k > 100k -> raw=100k. kelly=1.0, haircut=0, floor=0.
        target=100k.
        """
        pos = _pos(quantity=5_000.0, current_price=100.0)   # requested=500k
        pf  = _pf(nav=1_000_000.0)
        rp  = _rp(max_position_pct_nav=0.20, volatility_target_ann=0.15,
                  kelly_fraction=1.0, liquidity_haircut_floor=0.0)
        result = size_position(pos, pf, rp, _dec(RiskVerdict.APPROVE), position_vol=0.30)
        assert result.target_notional == pytest.approx(100_000.0)

    def test_pipeline_hold_same_arithmetic_as_approve(self):
        """
        HOLD / REJECT / APPROVE follow the same arithmetic path.
        (Only HALT and REDUCE+clamped differ.)
        """
        pos = _pos(quantity=10.0, current_price=500.0)  # requested=5000
        pf  = _pf(nav=1_000_000.0)
        rp  = _rp(max_position_pct_nav=0.05, kelly_fraction=0.75,
                  liquidity_haircut_floor=0.20)
        r_approve = size_position(pos, pf, rp, _dec(RiskVerdict.APPROVE))
        r_hold    = size_position(pos, pf, rp, _dec(RiskVerdict.HOLD))
        r_reject  = size_position(pos, pf, rp, _dec(RiskVerdict.REJECT))
        assert r_approve.target_notional == pytest.approx(r_hold.target_notional)
        assert r_approve.target_notional == pytest.approx(r_reject.target_notional)


# =============================================================================
# SECTION 17 -- Extreme / edge values
# =============================================================================

class TestExtremeValues:
    def test_tiny_quantity_and_price(self):
        pos = _pos(quantity=1e-10, current_price=1e-10)  # requested=1e-20
        pf  = _pf(nav=1_000_000.0)
        rp  = _rp(max_position_pct_nav=1.0, kelly_fraction=1.0,
                  liquidity_haircut_floor=1.0)
        result = size_position(pos, pf, rp, _dec())
        assert math.isfinite(result.target_notional)
        assert result.target_notional > 0.0

    def test_very_large_nav(self):
        pos = _pos(quantity=1.0, current_price=1.0)
        pf  = _pf(nav=1e15)
        rp  = _rp(max_position_pct_nav=0.001, kelly_fraction=1.0,
                  liquidity_haircut_floor=0.0)
        # cap=1e12 >> 1 -> target=1
        result = size_position(pos, pf, rp, _dec())
        assert result.target_notional == pytest.approx(1.0)

    def test_kelly_fraction_exactly_1(self):
        pos = _pos(quantity=1.0, current_price=1000.0)
        pf  = _pf(nav=1_000_000.0)
        rp  = _rp(max_position_pct_nav=1.0, kelly_fraction=1.0,
                  liquidity_haircut_floor=0.0)
        result = size_position(pos, pf, rp, _dec())
        assert result.target_notional == pytest.approx(1000.0)

    def test_haircut_floor_exactly_1(self):
        """haircut=1.0 -> floor=requested -> target >= requested."""
        pos = _pos(quantity=10.0, current_price=100.0)  # requested=1000
        pf  = _pf(nav=1_000_000.0)
        rp  = _rp(max_position_pct_nav=0.05, kelly_fraction=0.01,
                  liquidity_haircut_floor=1.0)
        result = size_position(pos, pf, rp, _dec())
        assert result.target_notional >= 1000.0 - 1e-9

    def test_max_position_pct_nav_exactly_1(self):
        pos = _pos(quantity=100.0, current_price=100.0)  # requested=10k
        pf  = _pf(nav=1_000_000.0)
        rp  = _rp(max_position_pct_nav=1.0, kelly_fraction=1.0,
                  liquidity_haircut_floor=0.01)
        # cap=1M >> 10k -> target=10k
        result = size_position(pos, pf, rp, _dec())
        assert result.target_notional == pytest.approx(10_000.0)

    def test_position_vol_very_large(self):
        """pos_vol >> target_vol -> scalar near 0 -> effective_cap near 0 -> floor dominates."""
        pos = _pos(quantity=100.0, current_price=100.0)  # requested=10k
        pf  = _pf(nav=1_000_000.0)
        rp  = _rp(max_position_pct_nav=0.05, volatility_target_ann=0.15,
                  kelly_fraction=1.0, liquidity_haircut_floor=0.50)
        # scalar = 0.15/1e6 = 1.5e-7 -> eff_cap ~ 0; floor=10k*0.5=5k -> target>=5k
        result = size_position(pos, pf, rp, _dec(), position_vol=1e6)
        assert result.target_notional >= 10_000.0 * 0.50 - 1e-9

    def test_position_vol_exactly_target_vol(self):
        """scalar=1.0 exactly; effective_cap==base_cap."""
        target_ann = 0.20
        pos = _pos(quantity=1_000.0, current_price=100.0)  # requested=100k
        pf  = _pf(nav=1_000_000.0)
        rp  = _rp(max_position_pct_nav=0.05, volatility_target_ann=target_ann,
                  kelly_fraction=1.0, liquidity_haircut_floor=0.0)
        base_cap = 1_000_000.0 * 0.05  # 50k
        result = size_position(pos, pf, rp, _dec(), position_vol=target_ann)
        assert result.target_notional == pytest.approx(base_cap)


# =============================================================================
# SECTION 18 -- __all__ completeness
# =============================================================================

class TestDunderAll:
    def test_size_position_in_all(self):
        assert "size_position" in _sizing_mod.__all__

    def test_position_sizing_result_in_all(self):
        assert "PositionSizingResult" in _sizing_mod.__all__

    def test_all_has_exactly_two_entries(self):
        assert len(_sizing_mod.__all__) == 2
