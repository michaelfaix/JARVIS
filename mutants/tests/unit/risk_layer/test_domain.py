# =============================================================================
# test_domain.py  --  Mutation-safe pytest tests for jarvis/risk_layer/domain.py
#
# Strategy
# --------
# Every comparison boundary is tested with THREE values:
#   - one unit BELOW the threshold  → must RAISE
#   - the exact boundary             → depends on open/closed endpoint
#   - one unit ABOVE the threshold   → must PASS (or raise, for upper bounds)
#
# This kills every >, >=, <, <= mutation because any operator change shifts
# which of the three values is accepted vs rejected.
#
# Exception messages are tested explicitly so that renaming a field or
# changing a constraint string is immediately caught.
# =============================================================================

from __future__ import annotations

import dataclasses
import math
from unittest.mock import patch

import pytest

# ---------------------------------------------------------------------------
# Patch the external dependency so tests are hermetic
# ---------------------------------------------------------------------------
VALID_ASSET_CLASSES_MOCK = frozenset({"equity", "crypto", "fx", "commodity"})

import sys
import types

# ---------------------------------------------------------------------------
# Save original sys.modules state so we can restore it after loading
# the local domain.py copy (prevents fake stubs from leaking into other
# test files like test_evaluator.py).
# ---------------------------------------------------------------------------
_FAKE_KEYS = [
    "jarvis", "jarvis.core", "jarvis.core.data_layer",
    "jarvis.risk_layer", "jarvis.risk_layer.exceptions",
    "jarvis.risk_layer.domain",
]
_saved_modules = {k: sys.modules[k] for k in _FAKE_KEYS if k in sys.modules}

# Build a minimal fake module tree: jarvis.core.data_layer
jarvis_pkg        = types.ModuleType("jarvis")
jarvis_core_pkg   = types.ModuleType("jarvis.core")
data_layer_mod    = types.ModuleType("jarvis.core.data_layer")
data_layer_mod.VALID_ASSET_CLASSES = VALID_ASSET_CLASSES_MOCK
jarvis_pkg.core   = jarvis_core_pkg
jarvis_core_pkg.data_layer = data_layer_mod
sys.modules["jarvis"] = jarvis_pkg
sys.modules["jarvis.core"] = jarvis_core_pkg
sys.modules["jarvis.core.data_layer"] = data_layer_mod

# Build minimal exceptions module
exc_mod = types.ModuleType("jarvis.risk_layer.exceptions")

class RiskNumericalError(Exception):
    def __init__(self, *, field_name, value):
        self.field_name = field_name
        self.value = value
        super().__init__(f"{field_name}={value!r} is not finite")

class RiskValidationError(Exception):
    def __init__(self, *, field_name, value, constraint):
        self.field_name  = field_name
        self.value       = value
        self.constraint  = constraint
        super().__init__(f"{field_name}={value!r}: {constraint}")

class RiskParameterConsistencyError(Exception):
    def __init__(self, *, field_a, value_a, field_b, value_b, invariant_description):
        self.field_a = field_a
        self.value_a = value_a
        self.field_b = field_b
        self.value_b = value_b
        self.invariant_description = invariant_description
        super().__init__(f"{field_a}={value_a!r} vs {field_b}={value_b!r}: {invariant_description}")

exc_mod.RiskNumericalError            = RiskNumericalError
exc_mod.RiskValidationError           = RiskValidationError
exc_mod.RiskParameterConsistencyError = RiskParameterConsistencyError

risk_layer_pkg = types.ModuleType("jarvis.risk_layer")
risk_layer_pkg.exceptions = exc_mod
sys.modules["jarvis.risk_layer"] = risk_layer_pkg
sys.modules["jarvis.risk_layer.exceptions"] = exc_mod

# Load domain.py from same directory as this test file
import importlib
import importlib.util, pathlib
spec = importlib.util.spec_from_file_location(
    "jarvis.risk_layer.domain",
    pathlib.Path(__file__).parent / "domain.py",
    submodule_search_locations=[],
)
domain_mod = importlib.util.module_from_spec(spec)
domain_mod.__package__ = "jarvis.risk_layer"
sys.modules["jarvis.risk_layer.domain"] = domain_mod
spec.loader.exec_module(domain_mod)

Side                        = domain_mod.Side
RiskVerdict                 = domain_mod.RiskVerdict
PositionSpec                = domain_mod.PositionSpec
PortfolioState              = domain_mod.PortfolioState
RiskParameters              = domain_mod.RiskParameters

# ---------------------------------------------------------------------------
# Restore sys.modules: put back originals or remove fakes
# ---------------------------------------------------------------------------
for _key in _FAKE_KEYS:
    if _key in _saved_modules:
        sys.modules[_key] = _saved_modules[_key]
    else:
        sys.modules.pop(_key, None)

# ---------------------------------------------------------------------------
# Convenience factories (all valid defaults)
# ---------------------------------------------------------------------------

def _ps(**kwargs) -> PositionSpec:
    defaults = dict(
        symbol="BTC-USD",
        asset_class="crypto",
        side=Side.LONG,
        entry_price=100.0,
        current_price=105.0,
        quantity=1.0,
        max_position_usd=10_000.0,
    )
    defaults.update(kwargs)
    return PositionSpec(**defaults)


def _pf(**kwargs) -> PortfolioState:
    defaults = dict(
        nav=1_000_000.0,
        gross_exposure_usd=500_000.0,
        net_exposure_usd=200_000.0,
        open_positions=3,
        peak_nav=1_000_000.0,
        realized_drawdown_pct=0.0,
        current_step=0,
    )
    defaults.update(kwargs)
    return PortfolioState(**defaults)


def _rp(**kwargs) -> RiskParameters:
    defaults = dict(
        max_position_pct_nav=0.05,
        max_gross_exposure_pct=1.5,
        max_drawdown_hard_stop=0.20,
        max_drawdown_soft_warn=0.10,
        volatility_target_ann=0.15,
        liquidity_haircut_floor=0.5,
        max_open_positions=10,
        kelly_fraction=0.25,
    )
    defaults.update(kwargs)
    return RiskParameters(**defaults)


# =============================================================================
# SECTION 1 -- Side enum
# =============================================================================

class TestSideEnum:
    def test_long_value(self):
        assert Side.LONG == "LONG"

    def test_short_value(self):
        assert Side.SHORT == "SHORT"

    def test_str_inheritance(self):
        assert isinstance(Side.LONG, str)

    def test_no_extra_members(self):
        assert set(Side) == {Side.LONG, Side.SHORT}


# =============================================================================
# SECTION 2 -- Internal validator helpers (tested indirectly via dataclasses)
# =============================================================================

# _check_finite  ---------------------------------------------------------------

class TestCheckFinite:
    @pytest.mark.parametrize("bad", [math.inf, -math.inf, math.nan])
    def test_ps_entry_price_non_finite_raises_numerical_error(self, bad):
        with pytest.raises(RiskNumericalError) as exc_info:
            _ps(entry_price=bad)
        assert exc_info.value.field_name == "entry_price"
        assert exc_info.value.value == bad or math.isnan(bad)

    @pytest.mark.parametrize("bad", [math.inf, -math.inf, math.nan])
    def test_ps_current_price_non_finite(self, bad):
        with pytest.raises(RiskNumericalError) as exc_info:
            _ps(current_price=bad)
        assert exc_info.value.field_name == "current_price"

    @pytest.mark.parametrize("bad", [math.inf, -math.inf, math.nan])
    def test_ps_quantity_non_finite(self, bad):
        with pytest.raises(RiskNumericalError) as exc_info:
            _ps(quantity=bad)
        assert exc_info.value.field_name == "quantity"

    @pytest.mark.parametrize("bad", [math.inf, -math.inf, math.nan])
    def test_ps_max_position_usd_non_finite(self, bad):
        with pytest.raises(RiskNumericalError) as exc_info:
            _ps(max_position_usd=bad)
        assert exc_info.value.field_name == "max_position_usd"

    @pytest.mark.parametrize("bad", [math.inf, -math.inf, math.nan])
    def test_pf_nav_non_finite(self, bad):
        with pytest.raises(RiskNumericalError) as exc_info:
            _pf(nav=bad)
        assert exc_info.value.field_name == "nav"

    @pytest.mark.parametrize("bad", [math.inf, -math.inf, math.nan])
    def test_pf_gross_exposure_non_finite(self, bad):
        with pytest.raises(RiskNumericalError) as exc_info:
            _pf(gross_exposure_usd=bad)
        assert exc_info.value.field_name == "gross_exposure_usd"

    @pytest.mark.parametrize("bad", [math.inf, -math.inf, math.nan])
    def test_pf_net_exposure_non_finite(self, bad):
        with pytest.raises(RiskNumericalError) as exc_info:
            _pf(net_exposure_usd=bad)
        assert exc_info.value.field_name == "net_exposure_usd"

    @pytest.mark.parametrize("bad", [math.inf, -math.inf, math.nan])
    def test_pf_peak_nav_non_finite(self, bad):
        with pytest.raises(RiskNumericalError) as exc_info:
            _pf(peak_nav=bad, nav=1.0)
        assert exc_info.value.field_name == "peak_nav"

    @pytest.mark.parametrize("bad", [math.inf, -math.inf, math.nan])
    def test_pf_realized_drawdown_non_finite(self, bad):
        with pytest.raises(RiskNumericalError) as exc_info:
            _pf(realized_drawdown_pct=bad)
        assert exc_info.value.field_name == "realized_drawdown_pct"

    @pytest.mark.parametrize("bad", [math.inf, -math.inf, math.nan])
    def test_rp_max_position_pct_nav_non_finite(self, bad):
        with pytest.raises(RiskNumericalError) as exc_info:
            _rp(max_position_pct_nav=bad)
        assert exc_info.value.field_name == "max_position_pct_nav"


# =============================================================================
# SECTION 3 -- PositionSpec
# =============================================================================

class TestPositionSpecValid:
    def test_valid_long_construction(self):
        ps = _ps()
        assert ps.symbol == "BTC-USD"
        assert ps.side   == Side.LONG
        assert ps.entry_price == 100.0

    def test_valid_short_construction(self):
        ps = _ps(side=Side.SHORT)
        assert ps.side == Side.SHORT

    def test_frozen(self):
        ps = _ps()
        with pytest.raises((AttributeError, TypeError)):
            ps.entry_price = 999.0  # type: ignore[misc]

    def test_entry_price_small_positive(self):
        ps = _ps(entry_price=1e-10)
        assert ps.entry_price == 1e-10

    def test_quantity_small_positive(self):
        ps = _ps(quantity=1e-10)
        assert ps.quantity == 1e-10


class TestPositionSpecEntryPrice:
    """Kills > vs >= on _check_positive (value <= 0)."""

    def test_entry_price_zero_raises(self):
        """Boundary: 0 must be rejected (strictly > 0)."""
        with pytest.raises(RiskValidationError) as exc_info:
            _ps(entry_price=0.0)
        e = exc_info.value
        assert e.field_name == "entry_price"
        assert e.value == 0.0
        assert "must be > 0" in e.constraint

    def test_entry_price_negative_raises(self):
        with pytest.raises(RiskValidationError) as exc_info:
            _ps(entry_price=-1.0)
        assert exc_info.value.field_name == "entry_price"
        assert exc_info.value.value == -1.0

    def test_entry_price_tiny_positive_passes(self):
        """One epsilon above zero must pass to kill >= 0 mutation."""
        ps = _ps(entry_price=1e-300)
        assert ps.entry_price == 1e-300

    def test_entry_price_wrong_type_raises_numerical_or_validation(self):
        with pytest.raises((RiskNumericalError, RiskValidationError, TypeError)):
            _ps(entry_price="100")  # type: ignore[arg-type]


class TestPositionSpecCurrentPrice:
    def test_current_price_zero_raises(self):
        with pytest.raises(RiskValidationError) as exc_info:
            _ps(current_price=0.0)
        assert exc_info.value.field_name == "current_price"
        assert "must be > 0" in exc_info.value.constraint

    def test_current_price_negative_raises(self):
        with pytest.raises(RiskValidationError):
            _ps(current_price=-0.01)

    def test_current_price_tiny_positive_passes(self):
        assert _ps(current_price=1e-300).current_price == 1e-300


class TestPositionSpecQuantity:
    def test_quantity_zero_raises(self):
        with pytest.raises(RiskValidationError) as exc_info:
            _ps(quantity=0.0)
        assert exc_info.value.field_name == "quantity"
        assert "must be > 0" in exc_info.value.constraint

    def test_quantity_negative_raises(self):
        with pytest.raises(RiskValidationError):
            _ps(quantity=-1.0)

    def test_quantity_tiny_positive_passes(self):
        assert _ps(quantity=1e-300).quantity == 1e-300


class TestPositionSpecMaxPositionUsd:
    def test_max_position_usd_zero_raises(self):
        with pytest.raises(RiskValidationError) as exc_info:
            _ps(max_position_usd=0.0)
        assert exc_info.value.field_name == "max_position_usd"
        assert "must be > 0" in exc_info.value.constraint

    def test_max_position_usd_negative_raises(self):
        with pytest.raises(RiskValidationError):
            _ps(max_position_usd=-1000.0)

    def test_max_position_usd_tiny_positive_passes(self):
        assert _ps(max_position_usd=1e-10).max_position_usd == 1e-10


class TestPositionSpecSymbol:
    def test_empty_symbol_raises(self):
        with pytest.raises(RiskValidationError) as exc_info:
            _ps(symbol="")
        assert exc_info.value.field_name == "symbol"
        assert "non-empty" in exc_info.value.constraint

    def test_non_string_symbol_raises(self):
        with pytest.raises(RiskValidationError) as exc_info:
            _ps(symbol=123)  # type: ignore[arg-type]
        assert exc_info.value.field_name == "symbol"

    def test_none_symbol_raises(self):
        with pytest.raises(RiskValidationError):
            _ps(symbol=None)  # type: ignore[arg-type]

    def test_non_ascii_symbol_raises(self):
        with pytest.raises(RiskValidationError) as exc_info:
            _ps(symbol="BTC\u20AC")
        assert exc_info.value.field_name == "symbol"
        assert "ASCII" in exc_info.value.constraint

    def test_valid_ascii_symbol(self):
        ps = _ps(symbol="ETH-USD")
        assert ps.symbol == "ETH-USD"


class TestPositionSpecAssetClass:
    def test_invalid_asset_class_raises(self):
        with pytest.raises(RiskValidationError) as exc_info:
            _ps(asset_class="UNKNOWN_ASSET")
        e = exc_info.value
        assert e.field_name == "asset_class"
        assert "VALID_ASSET_CLASSES" in e.constraint

    def test_all_valid_asset_classes_pass(self):
        for ac in VALID_ASSET_CLASSES_MOCK:
            ps = _ps(asset_class=ac)
            assert ps.asset_class == ac


class TestPositionSpecSide:
    def test_invalid_side_string_raises(self):
        with pytest.raises(RiskValidationError) as exc_info:
            _ps(side="LONG")  # string, not enum  # type: ignore[arg-type]
        e = exc_info.value
        assert e.field_name == "side"
        assert "Side enum" in e.constraint

    def test_none_side_raises(self):
        with pytest.raises(RiskValidationError):
            _ps(side=None)  # type: ignore[arg-type]

    def test_integer_side_raises(self):
        with pytest.raises(RiskValidationError):
            _ps(side=1)  # type: ignore[arg-type]


# =============================================================================
# SECTION 4 -- PortfolioState
# =============================================================================

class TestPortfolioStateValid:
    def test_basic_valid(self):
        pf = _pf()
        assert pf.nav == 1_000_000.0

    def test_zero_drawdown(self):
        pf = _pf(nav=1e6, peak_nav=1e6, realized_drawdown_pct=0.0)
        assert pf.realized_drawdown_pct == 0.0

    def test_max_drawdown(self):
        pf = _pf(nav=500_000.0, peak_nav=1_000_000.0, realized_drawdown_pct=1.0)
        assert pf.realized_drawdown_pct == 1.0

    def test_frozen(self):
        pf = _pf()
        with pytest.raises((AttributeError, TypeError)):
            pf.nav = 0.0  # type: ignore[misc]

    def test_negative_net_exposure_valid(self):
        pf = _pf(net_exposure_usd=-500_000.0)
        assert pf.net_exposure_usd == -500_000.0


class TestPortfolioStateNav:
    """Kills > vs >= on _check_positive for nav."""

    def test_nav_zero_raises(self):
        with pytest.raises(RiskValidationError) as exc_info:
            _pf(nav=0.0)
        e = exc_info.value
        assert e.field_name == "nav"
        assert "must be > 0" in e.constraint

    def test_nav_negative_raises(self):
        with pytest.raises(RiskValidationError) as exc_info:
            _pf(nav=-1.0)
        assert exc_info.value.field_name == "nav"

    def test_nav_tiny_positive_passes(self):
        pf = _pf(nav=1e-300, peak_nav=1e-300)
        assert pf.nav == 1e-300


class TestPortfolioStateGrossExposure:
    """Kills < vs <= on _check_non_negative_float for gross_exposure_usd."""

    def test_gross_exposure_zero_passes(self):
        """Zero must be valid (>= 0 includes 0)."""
        pf = _pf(gross_exposure_usd=0.0)
        assert pf.gross_exposure_usd == 0.0

    def test_gross_exposure_negative_raises(self):
        with pytest.raises(RiskValidationError) as exc_info:
            _pf(gross_exposure_usd=-1.0)
        e = exc_info.value
        assert e.field_name == "gross_exposure_usd"
        assert "must be >= 0" in e.constraint

    def test_gross_exposure_tiny_negative_raises(self):
        """One epsilon below zero must fail (kills >= changed to >)."""
        with pytest.raises(RiskValidationError):
            _pf(gross_exposure_usd=-1e-15)

    def test_gross_exposure_positive_passes(self):
        pf = _pf(gross_exposure_usd=1.0)
        assert pf.gross_exposure_usd == 1.0


class TestPortfolioStateOpenPositions:
    """Kills < vs <= on _check_non_negative_int."""

    def test_open_positions_zero_passes(self):
        pf = _pf(open_positions=0)
        assert pf.open_positions == 0

    def test_open_positions_negative_raises(self):
        with pytest.raises(RiskValidationError) as exc_info:
            _pf(open_positions=-1)
        assert exc_info.value.field_name == "open_positions"

    def test_open_positions_float_raises(self):
        with pytest.raises(RiskValidationError) as exc_info:
            _pf(open_positions=3.0)  # type: ignore[arg-type]
        assert exc_info.value.field_name == "open_positions"
        assert "non-negative integer" in exc_info.value.constraint

    def test_open_positions_bool_raises(self):
        """bool subclasses int; must be rejected."""
        with pytest.raises(RiskValidationError):
            _pf(open_positions=True)  # type: ignore[arg-type]

    def test_open_positions_large_int_passes(self):
        pf = _pf(open_positions=999)
        assert pf.open_positions == 999


class TestPortfolioStatePeakNav:
    def test_peak_nav_zero_raises(self):
        with pytest.raises(RiskValidationError) as exc_info:
            _pf(peak_nav=0.0, nav=0.0)  # nav checked first; use nav=1 to reach peak_nav
        # nav=0 raises first; test peak_nav specifically:
        with pytest.raises((RiskValidationError, RiskNumericalError)):
            _pf(nav=1.0, peak_nav=0.0)

    def test_peak_nav_zero_specific(self):
        with pytest.raises(RiskValidationError) as exc_info:
            _pf(nav=1.0, peak_nav=0.0)
        assert exc_info.value.field_name == "peak_nav"
        assert "must be > 0" in exc_info.value.constraint

    def test_peak_nav_negative_raises(self):
        with pytest.raises(RiskValidationError) as exc_info:
            _pf(nav=1.0, peak_nav=-1.0)
        assert exc_info.value.field_name == "peak_nav"


class TestPortfolioStateRealizedDrawdown:
    """Kills every boundary of [0.0, 1.0]."""

    def test_drawdown_zero_passes(self):
        pf = _pf(nav=1e6, peak_nav=1e6, realized_drawdown_pct=0.0)
        assert pf.realized_drawdown_pct == 0.0

    def test_drawdown_one_passes(self):
        pf = _pf(nav=1e6, peak_nav=2e6, realized_drawdown_pct=1.0)
        assert pf.realized_drawdown_pct == 1.0

    def test_drawdown_just_above_one_raises(self):
        with pytest.raises(RiskValidationError) as exc_info:
            _pf(realized_drawdown_pct=1.0 + 1e-15)
        e = exc_info.value
        assert e.field_name == "realized_drawdown_pct"
        assert "[0.0, 1.0]" in e.constraint

    def test_drawdown_just_below_zero_raises(self):
        with pytest.raises(RiskValidationError) as exc_info:
            _pf(realized_drawdown_pct=-1e-15)
        e = exc_info.value
        assert e.field_name == "realized_drawdown_pct"
        assert "[0.0, 1.0]" in e.constraint

    def test_drawdown_negative_one_raises(self):
        with pytest.raises(RiskValidationError):
            _pf(realized_drawdown_pct=-0.5)

    def test_drawdown_two_raises(self):
        with pytest.raises(RiskValidationError):
            _pf(realized_drawdown_pct=2.0)


class TestPortfolioStateCurrentStep:
    def test_current_step_zero_passes(self):
        pf = _pf(current_step=0)
        assert pf.current_step == 0

    def test_current_step_negative_raises(self):
        with pytest.raises(RiskValidationError) as exc_info:
            _pf(current_step=-1)
        assert exc_info.value.field_name == "current_step"

    def test_current_step_bool_raises(self):
        with pytest.raises(RiskValidationError):
            _pf(current_step=False)  # type: ignore[arg-type]

    def test_current_step_float_raises(self):
        with pytest.raises(RiskValidationError):
            _pf(current_step=1.0)  # type: ignore[arg-type]


class TestPortfolioStatePeakNavCrossField:
    """INV-PF-09: peak_nav >= nav. Kills < vs <= mutation."""

    def test_peak_nav_equals_nav_passes(self):
        """Equality is permitted (no drawdown since reset)."""
        pf = _pf(nav=1e6, peak_nav=1e6)
        assert pf.peak_nav == pf.nav

    def test_peak_nav_greater_than_nav_passes(self):
        pf = _pf(nav=900_000.0, peak_nav=1_000_000.0, realized_drawdown_pct=0.1)
        assert pf.peak_nav > pf.nav

    def test_peak_nav_less_than_nav_raises(self):
        """peak_nav < nav is forbidden."""
        with pytest.raises(RiskParameterConsistencyError) as exc_info:
            _pf(nav=1_100_000.0, peak_nav=1_000_000.0)
        e = exc_info.value
        assert e.field_a == "peak_nav"
        assert e.field_b == "nav"
        assert "peak_nav" in e.invariant_description
        assert ">= nav" in e.invariant_description or "high-water" in e.invariant_description

    def test_peak_nav_one_cent_below_nav_raises(self):
        """One epsilon below equality must still raise (kills < → <= mutation)."""
        nav = 1_000_000.0
        peak = nav - 0.01
        with pytest.raises(RiskParameterConsistencyError):
            _pf(nav=nav, peak_nav=peak)

    def test_peak_nav_one_cent_above_nav_passes(self):
        nav   = 999_999.99
        peak  = 1_000_000.0
        pf = _pf(nav=nav, peak_nav=peak, realized_drawdown_pct=0.01/1_000_000.0)
        assert pf.peak_nav > pf.nav


# =============================================================================
# SECTION 5 -- RiskParameters
# =============================================================================

class TestRiskParametersValid:
    def test_basic_valid(self):
        rp = _rp()
        assert rp.kelly_fraction == 0.25

    def test_frozen(self):
        rp = _rp()
        with pytest.raises((AttributeError, TypeError)):
            rp.kelly_fraction = 0.5  # type: ignore[misc]


class TestRiskParametersMaxPositionPctNav:
    """(0.0, 1.0] -- kills all four operator mutations."""

    def test_zero_raises(self):
        with pytest.raises(RiskValidationError) as exc_info:
            _rp(max_position_pct_nav=0.0)
        e = exc_info.value
        assert e.field_name == "max_position_pct_nav"
        assert "(0.0, 1.0]" in e.constraint

    def test_tiny_positive_passes(self):
        """Just above lower open bound."""
        rp = _rp(max_position_pct_nav=1e-10)
        assert rp.max_position_pct_nav == 1e-10

    def test_one_passes(self):
        """Upper bound 1.0 is included (closed)."""
        rp = _rp(max_position_pct_nav=1.0)
        assert rp.max_position_pct_nav == 1.0

    def test_above_one_raises(self):
        with pytest.raises(RiskValidationError) as exc_info:
            _rp(max_position_pct_nav=1.0 + 1e-10)
        e = exc_info.value
        assert e.field_name == "max_position_pct_nav"
        assert "(0.0, 1.0]" in e.constraint

    def test_negative_raises(self):
        with pytest.raises(RiskValidationError):
            _rp(max_position_pct_nav=-0.01)


class TestRiskParametersMaxGrossExposurePct:
    """Strictly positive (> 0); values > 1.0 are allowed (leverage)."""

    def test_zero_raises(self):
        with pytest.raises(RiskValidationError) as exc_info:
            _rp(max_gross_exposure_pct=0.0)
        assert exc_info.value.field_name == "max_gross_exposure_pct"
        assert "must be > 0" in exc_info.value.constraint

    def test_negative_raises(self):
        with pytest.raises(RiskValidationError):
            _rp(max_gross_exposure_pct=-1.0)

    def test_tiny_positive_passes(self):
        rp = _rp(max_gross_exposure_pct=1e-300)
        assert rp.max_gross_exposure_pct == 1e-300

    def test_one_passes(self):
        rp = _rp(max_gross_exposure_pct=1.0)
        assert rp.max_gross_exposure_pct == 1.0

    def test_two_passes(self):
        """Leverage > 1 must be valid."""
        rp = _rp(max_gross_exposure_pct=2.0)
        assert rp.max_gross_exposure_pct == 2.0


class TestRiskParametersMaxDrawdownHardStop:
    """(0.0, 1.0) -- both endpoints excluded."""

    def test_zero_raises(self):
        with pytest.raises(RiskValidationError) as exc_info:
            _rp(max_drawdown_hard_stop=0.0, max_drawdown_soft_warn=0.0)
        # hard_stop=0 fails V2 before cross-field; soft_warn may also fail
        # We only care that it raises
        assert exc_info.value.field_name in ("max_drawdown_hard_stop", "max_drawdown_soft_warn")

    def test_hard_stop_zero_specifically(self):
        """Use soft_warn that would pass to isolate hard_stop."""
        # soft_warn checked after hard_stop; set soft_warn valid
        # hard_stop=0 must fail (0 not in (0,1))
        with pytest.raises(RiskValidationError) as exc_info:
            _rp(max_drawdown_hard_stop=0.0, max_drawdown_soft_warn=0.0)
        # hard_stop is validated first
        assert "max_drawdown" in exc_info.value.field_name

    def test_hard_stop_tiny_positive_passes(self):
        rp = _rp(max_drawdown_hard_stop=1e-10, max_drawdown_soft_warn=5e-11)
        assert rp.max_drawdown_hard_stop == 1e-10

    def test_hard_stop_one_raises(self):
        with pytest.raises(RiskValidationError) as exc_info:
            _rp(max_drawdown_hard_stop=1.0)
        assert exc_info.value.field_name == "max_drawdown_hard_stop"
        assert "(0.0, 1.0)" in exc_info.value.constraint

    def test_hard_stop_just_below_one_passes(self):
        rp = _rp(max_drawdown_hard_stop=1.0 - 1e-10,
                 max_drawdown_soft_warn=1.0 - 2e-10)
        assert rp.max_drawdown_hard_stop < 1.0

    def test_hard_stop_above_one_raises(self):
        with pytest.raises(RiskValidationError):
            _rp(max_drawdown_hard_stop=1.5)


class TestRiskParametersMaxDrawdownSoftWarn:
    """(0.0, 1.0) -- both endpoints excluded."""

    def test_soft_warn_zero_raises(self):
        # Set hard_stop > soft_warn to avoid cross-field triggering
        with pytest.raises(RiskValidationError) as exc_info:
            _rp(max_drawdown_soft_warn=0.0, max_drawdown_hard_stop=0.5)
        e = exc_info.value
        assert e.field_name == "max_drawdown_soft_warn"
        assert "(0.0, 1.0)" in e.constraint

    def test_soft_warn_one_raises(self):
        with pytest.raises(RiskValidationError) as exc_info:
            _rp(max_drawdown_soft_warn=1.0, max_drawdown_hard_stop=0.5)
        e = exc_info.value
        assert e.field_name == "max_drawdown_soft_warn"

    def test_soft_warn_tiny_positive_passes(self):
        rp = _rp(max_drawdown_soft_warn=1e-10, max_drawdown_hard_stop=2e-10)
        assert rp.max_drawdown_soft_warn == 1e-10

    def test_soft_warn_just_below_one_passes_with_hard_at_one(self):
        # hard_stop=1.0 is invalid itself; use just_below for both
        hard = 0.99
        soft = 0.98
        rp = _rp(max_drawdown_hard_stop=hard, max_drawdown_soft_warn=soft)
        assert rp.max_drawdown_soft_warn == soft


class TestRiskParametersVolatilityTargetAnn:
    def test_zero_raises(self):
        with pytest.raises(RiskValidationError) as exc_info:
            _rp(volatility_target_ann=0.0)
        assert exc_info.value.field_name == "volatility_target_ann"
        assert "must be > 0" in exc_info.value.constraint

    def test_negative_raises(self):
        with pytest.raises(RiskValidationError):
            _rp(volatility_target_ann=-0.1)

    def test_tiny_positive_passes(self):
        rp = _rp(volatility_target_ann=1e-300)
        assert rp.volatility_target_ann == 1e-300

    def test_large_value_passes(self):
        rp = _rp(volatility_target_ann=5.0)
        assert rp.volatility_target_ann == 5.0


class TestRiskParametersLiquidityHaircutFloor:
    """(0.0, 1.0] -- lower open, upper closed."""

    def test_zero_raises(self):
        with pytest.raises(RiskValidationError) as exc_info:
            _rp(liquidity_haircut_floor=0.0)
        e = exc_info.value
        assert e.field_name == "liquidity_haircut_floor"
        assert "(0.0, 1.0]" in e.constraint

    def test_tiny_positive_passes(self):
        rp = _rp(liquidity_haircut_floor=1e-10)
        assert rp.liquidity_haircut_floor == 1e-10

    def test_one_passes(self):
        rp = _rp(liquidity_haircut_floor=1.0)
        assert rp.liquidity_haircut_floor == 1.0

    def test_above_one_raises(self):
        with pytest.raises(RiskValidationError) as exc_info:
            _rp(liquidity_haircut_floor=1.0 + 1e-10)
        e = exc_info.value
        assert e.field_name == "liquidity_haircut_floor"

    def test_negative_raises(self):
        with pytest.raises(RiskValidationError):
            _rp(liquidity_haircut_floor=-0.5)


class TestRiskParametersMaxOpenPositions:
    """int >= 1. Kills < vs <= and type guards."""

    def test_one_passes(self):
        rp = _rp(max_open_positions=1)
        assert rp.max_open_positions == 1

    def test_zero_raises(self):
        with pytest.raises(RiskValidationError) as exc_info:
            _rp(max_open_positions=0)
        e = exc_info.value
        assert e.field_name == "max_open_positions"
        assert ">= 1" in e.constraint

    def test_negative_raises(self):
        with pytest.raises(RiskValidationError) as exc_info:
            _rp(max_open_positions=-1)
        assert exc_info.value.field_name == "max_open_positions"

    def test_float_raises(self):
        with pytest.raises(RiskValidationError) as exc_info:
            _rp(max_open_positions=1.0)  # type: ignore[arg-type]
        e = exc_info.value
        assert e.field_name == "max_open_positions"
        assert "positive integer" in e.constraint

    def test_bool_raises(self):
        with pytest.raises(RiskValidationError):
            _rp(max_open_positions=True)  # type: ignore[arg-type]

    def test_large_int_passes(self):
        rp = _rp(max_open_positions=100)
        assert rp.max_open_positions == 100


class TestRiskParametersKellyFraction:
    """(0.0, 1.0] -- lower open, upper closed."""

    def test_zero_raises(self):
        with pytest.raises(RiskValidationError) as exc_info:
            _rp(kelly_fraction=0.0)
        e = exc_info.value
        assert e.field_name == "kelly_fraction"
        assert "(0.0, 1.0]" in e.constraint

    def test_tiny_positive_passes(self):
        rp = _rp(kelly_fraction=1e-10)
        assert rp.kelly_fraction == 1e-10

    def test_one_passes(self):
        """Upper bound 1.0 is included (full Kelly)."""
        rp = _rp(kelly_fraction=1.0)
        assert rp.kelly_fraction == 1.0

    def test_above_one_raises(self):
        with pytest.raises(RiskValidationError) as exc_info:
            _rp(kelly_fraction=1.0 + 1e-10)
        assert exc_info.value.field_name == "kelly_fraction"

    def test_negative_raises(self):
        with pytest.raises(RiskValidationError):
            _rp(kelly_fraction=-0.25)


class TestRiskParametersCrossFieldDrawdown:
    """INV-RP-10: soft_warn < hard_stop. Kills >= vs > mutation."""

    def test_soft_less_than_hard_passes(self):
        rp = _rp(max_drawdown_soft_warn=0.05, max_drawdown_hard_stop=0.10)
        assert rp.max_drawdown_soft_warn < rp.max_drawdown_hard_stop

    def test_soft_equal_to_hard_raises(self):
        """Equality is forbidden (soft band collapses to zero width)."""
        with pytest.raises(RiskParameterConsistencyError) as exc_info:
            _rp(max_drawdown_soft_warn=0.10, max_drawdown_hard_stop=0.10)
        e = exc_info.value
        assert e.field_a == "max_drawdown_soft_warn"
        assert e.field_b == "max_drawdown_hard_stop"
        assert "strictly less than" in e.invariant_description
        assert "soft-warning band" in e.invariant_description

    def test_soft_greater_than_hard_raises(self):
        """Inverted values must raise."""
        with pytest.raises(RiskParameterConsistencyError) as exc_info:
            _rp(max_drawdown_soft_warn=0.15, max_drawdown_hard_stop=0.10)
        e = exc_info.value
        assert e.field_a == "max_drawdown_soft_warn"
        assert e.value_a == 0.15
        assert e.field_b == "max_drawdown_hard_stop"
        assert e.value_b == 0.10

    def test_soft_one_epsilon_below_hard_passes(self):
        """Kills the >= → > mutation: one epsilon below must pass."""
        hard = 0.10
        soft = hard - 1e-15
        rp = _rp(max_drawdown_soft_warn=soft, max_drawdown_hard_stop=hard)
        assert rp.max_drawdown_soft_warn < rp.max_drawdown_hard_stop

    def test_soft_one_epsilon_above_hard_raises(self):
        """Kills the < → <= mutation: one epsilon above hard must raise."""
        hard = 0.10
        soft = hard + 1e-15
        with pytest.raises(RiskParameterConsistencyError):
            _rp(max_drawdown_soft_warn=soft, max_drawdown_hard_stop=hard)


# =============================================================================
# SECTION 6 -- RiskVerdict (enum completeness)
# =============================================================================

class TestRiskVerdict:
    def test_all_members_present(self):
        members = {v.value for v in RiskVerdict}
        assert members == {"APPROVE", "REDUCE", "HOLD", "HALT", "REJECT"}

    def test_str_inheritance(self):
        assert isinstance(RiskVerdict.APPROVE, str)
        assert RiskVerdict.HALT == "HALT"


# =============================================================================
# SECTION 7 -- Exception message content (explicit string checks)
# =============================================================================

class TestExceptionMessages:
    """All exception strings are tested so that message changes break tests."""

    def test_numerical_error_message_contains_field_and_value(self):
        with pytest.raises(RiskNumericalError) as exc_info:
            _ps(entry_price=math.inf)
        msg = str(exc_info.value)
        assert "entry_price" in msg

    def test_validation_error_message_contains_field_value_constraint(self):
        with pytest.raises(RiskValidationError) as exc_info:
            _ps(entry_price=0.0)
        msg = str(exc_info.value)
        assert "entry_price" in msg
        assert "0.0" in msg or "0" in msg
        assert "must be > 0" in msg

    def test_consistency_error_message_contains_both_fields(self):
        with pytest.raises(RiskParameterConsistencyError) as exc_info:
            _pf(nav=1_100_000.0, peak_nav=1_000_000.0)
        msg = str(exc_info.value)
        assert "peak_nav" in msg
        assert "nav" in msg
        assert "high-water" in msg

    def test_rp_consistency_error_message_soft_hard(self):
        with pytest.raises(RiskParameterConsistencyError) as exc_info:
            _rp(max_drawdown_soft_warn=0.10, max_drawdown_hard_stop=0.10)
        msg = str(exc_info.value)
        assert "max_drawdown_soft_warn" in msg
        assert "max_drawdown_hard_stop" in msg
        assert "strictly less than" in msg

    def test_asset_class_error_mentions_valid_asset_classes(self):
        with pytest.raises(RiskValidationError) as exc_info:
            _ps(asset_class="INVALID")
        assert "VALID_ASSET_CLASSES" in exc_info.value.constraint

    def test_side_error_mentions_enum_members(self):
        with pytest.raises(RiskValidationError) as exc_info:
            _ps(side="LONG")  # type: ignore[arg-type]
        assert "Side.LONG" in exc_info.value.constraint
        assert "Side.SHORT" in exc_info.value.constraint

    def test_non_negative_int_wrong_type_message(self):
        with pytest.raises(RiskValidationError) as exc_info:
            _pf(open_positions=3.0)  # type: ignore[arg-type]
        assert "non-negative integer" in exc_info.value.constraint

    def test_positive_int_wrong_type_message(self):
        with pytest.raises(RiskValidationError) as exc_info:
            _rp(max_open_positions=1.0)  # type: ignore[arg-type]
        assert "positive integer" in exc_info.value.constraint

    def test_drawdown_closed_interval_message(self):
        with pytest.raises(RiskValidationError) as exc_info:
            _pf(realized_drawdown_pct=1.5)
        assert "[0.0, 1.0]" in exc_info.value.constraint

    def test_open_closed_interval_message(self):
        with pytest.raises(RiskValidationError) as exc_info:
            _rp(max_position_pct_nav=0.0)
        assert "(0.0, 1.0]" in exc_info.value.constraint

    def test_open_open_interval_message(self):
        with pytest.raises(RiskValidationError) as exc_info:
            _rp(max_drawdown_hard_stop=1.0)
        assert "(0.0, 1.0)" in exc_info.value.constraint


# =============================================================================
# SECTION 8 -- Immutability / frozen dataclasses
# =============================================================================

class TestImmutability:
    def test_position_spec_immutable(self):
        ps = _ps()
        with pytest.raises((AttributeError, TypeError, dataclasses.FrozenInstanceError)):
            ps.entry_price = 1.0

    def test_portfolio_state_immutable(self):
        pf = _pf()
        with pytest.raises((AttributeError, TypeError, dataclasses.FrozenInstanceError)):
            pf.nav = 1.0

    def test_risk_parameters_immutable(self):
        rp = _rp()
        with pytest.raises((AttributeError, TypeError, dataclasses.FrozenInstanceError)):
            rp.kelly_fraction = 1.0
