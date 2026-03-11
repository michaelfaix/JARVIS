# tests/unit/risk_layer/test_domain_cov.py
# Coverage target: jarvis/core/risk_layer/domain.py -> 95%+
# Missing lines: 163, 169, 179, 189, 199, 209, 219, 226-227, 247, 257, 263,
#                273, 279, 437, 562
#
# These are all validation helper raise branches. The existing test_domain.py
# imports from a local copy with mock exceptions so coverage doesn't count
# against the real module. This file imports from the REAL module.

import math

import pytest

from jarvis.core.risk_layer.domain import (
    PositionSpec,
    PortfolioState,
    RiskParameters,
    Side,
    RiskVerdict,
)
from jarvis.core.risk_layer.exceptions import (
    RiskNumericalError,
    RiskParameterConsistencyError,
    RiskValidationError,
)
from jarvis.core.data_layer import VALID_ASSET_CLASSES


# ---------------------------------------------------------------------------
# Convenience factories (all valid defaults)
# ---------------------------------------------------------------------------

def _ps(**kwargs):
    ac = next(iter(VALID_ASSET_CLASSES))
    defaults = dict(
        symbol="BTC-USD",
        asset_class=ac,
        side=Side.LONG,
        entry_price=100.0,
        current_price=105.0,
        quantity=1.0,
        max_position_usd=10_000.0,
    )
    defaults.update(kwargs)
    return PositionSpec(**defaults)


def _pf(**kwargs):
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


def _rp(**kwargs):
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
# _check_finite (line 163)
# =============================================================================

class TestCheckFinite:
    def test_inf_entry_price_raises(self):
        with pytest.raises(RiskNumericalError):
            _ps(entry_price=math.inf)

    def test_nan_entry_price_raises(self):
        with pytest.raises(RiskNumericalError):
            _ps(entry_price=math.nan)

    def test_neg_inf_entry_price_raises(self):
        with pytest.raises(RiskNumericalError):
            _ps(entry_price=-math.inf)


# =============================================================================
# _check_positive (line 169)
# =============================================================================

class TestCheckPositive:
    def test_zero_entry_price_raises(self):
        with pytest.raises(RiskValidationError) as exc_info:
            _ps(entry_price=0.0)
        assert exc_info.value.field_name == "entry_price"

    def test_negative_entry_price_raises(self):
        with pytest.raises(RiskValidationError):
            _ps(entry_price=-1.0)


# =============================================================================
# _check_non_negative_float (line 179)
# =============================================================================

class TestCheckNonNegativeFloat:
    def test_negative_gross_exposure_raises(self):
        with pytest.raises(RiskValidationError) as exc_info:
            _pf(gross_exposure_usd=-1.0)
        assert exc_info.value.field_name == "gross_exposure_usd"
        assert "must be >= 0" in exc_info.value.constraint


# =============================================================================
# _check_unit_interval_open_closed (line 189)
# =============================================================================

class TestCheckUnitIntervalOpenClosed:
    def test_zero_max_position_pct_raises(self):
        with pytest.raises(RiskValidationError) as exc_info:
            _rp(max_position_pct_nav=0.0)
        assert "(0.0, 1.0]" in exc_info.value.constraint

    def test_above_one_max_position_pct_raises(self):
        with pytest.raises(RiskValidationError):
            _rp(max_position_pct_nav=1.01)


# =============================================================================
# _check_unit_interval_closed (line 199)
# =============================================================================

class TestCheckUnitIntervalClosed:
    def test_drawdown_above_one_raises(self):
        with pytest.raises(RiskValidationError) as exc_info:
            _pf(realized_drawdown_pct=1.5)
        assert "[0.0, 1.0]" in exc_info.value.constraint

    def test_drawdown_negative_raises(self):
        with pytest.raises(RiskValidationError):
            _pf(realized_drawdown_pct=-0.1)


# =============================================================================
# _check_unit_interval_open_open (line 209)
# =============================================================================

class TestCheckUnitIntervalOpenOpen:
    def test_hard_stop_zero_raises(self):
        with pytest.raises(RiskValidationError) as exc_info:
            _rp(max_drawdown_hard_stop=0.0, max_drawdown_soft_warn=0.0)
        assert "(0.0, 1.0)" in exc_info.value.constraint

    def test_hard_stop_one_raises(self):
        with pytest.raises(RiskValidationError) as exc_info:
            _rp(max_drawdown_hard_stop=1.0)
        assert "(0.0, 1.0)" in exc_info.value.constraint


# =============================================================================
# _check_non_empty_ascii_string (line 219, 226-227)
# =============================================================================

class TestCheckNonEmptyAsciiString:
    def test_empty_symbol_raises(self):
        with pytest.raises(RiskValidationError) as exc_info:
            _ps(symbol="")
        assert "non-empty" in exc_info.value.constraint

    def test_none_symbol_raises(self):
        with pytest.raises(RiskValidationError):
            _ps(symbol=None)

    def test_non_ascii_symbol_raises(self):
        # lines 226-227: UnicodeEncodeError branch
        with pytest.raises(RiskValidationError) as exc_info:
            _ps(symbol="BTC\u20AC")
        assert "ASCII" in exc_info.value.constraint

    def test_integer_symbol_raises(self):
        with pytest.raises(RiskValidationError):
            _ps(symbol=123)


# =============================================================================
# _check_side (line 247)
# =============================================================================

class TestCheckSide:
    def test_string_side_raises(self):
        with pytest.raises(RiskValidationError) as exc_info:
            _ps(side="LONG")
        assert "Side enum" in exc_info.value.constraint

    def test_none_side_raises(self):
        with pytest.raises(RiskValidationError):
            _ps(side=None)


# =============================================================================
# _check_non_negative_int (lines 257, 263)
# =============================================================================

class TestCheckNonNegativeInt:
    def test_float_open_positions_raises(self):
        # line 257: type check
        with pytest.raises(RiskValidationError) as exc_info:
            _pf(open_positions=3.0)
        assert "non-negative integer" in exc_info.value.constraint

    def test_bool_open_positions_raises(self):
        # line 257: bool subclass rejection
        with pytest.raises(RiskValidationError):
            _pf(open_positions=True)

    def test_negative_open_positions_raises(self):
        # line 263: value < 0
        with pytest.raises(RiskValidationError) as exc_info:
            _pf(open_positions=-1)
        assert "must be >= 0" in exc_info.value.constraint


# =============================================================================
# _check_positive_int (lines 273, 279)
# =============================================================================

class TestCheckPositiveInt:
    def test_float_max_open_positions_raises(self):
        # line 273: type check
        with pytest.raises(RiskValidationError) as exc_info:
            _rp(max_open_positions=1.0)
        assert "positive integer" in exc_info.value.constraint

    def test_bool_max_open_positions_raises(self):
        # line 273: bool subclass rejection
        with pytest.raises(RiskValidationError):
            _rp(max_open_positions=True)

    def test_zero_max_open_positions_raises(self):
        # line 279: value < 1
        with pytest.raises(RiskValidationError) as exc_info:
            _rp(max_open_positions=0)
        assert "must be >= 1" in exc_info.value.constraint


# =============================================================================
# PortfolioState cross-field: peak_nav < nav (line 437)
# =============================================================================

class TestPortfolioStateCrossField:
    def test_peak_nav_less_than_nav_raises(self):
        with pytest.raises(RiskParameterConsistencyError) as exc_info:
            _pf(nav=1_100_000.0, peak_nav=1_000_000.0)
        e = exc_info.value
        assert e.field_a == "peak_nav"
        assert e.field_b == "nav"
        assert "high-water" in e.invariant_description


# =============================================================================
# RiskParameters cross-field: soft_warn >= hard_stop (line 562)
# =============================================================================

class TestRiskParametersCrossField:
    def test_soft_warn_equal_hard_stop_raises(self):
        with pytest.raises(RiskParameterConsistencyError) as exc_info:
            _rp(max_drawdown_soft_warn=0.10, max_drawdown_hard_stop=0.10)
        e = exc_info.value
        assert e.field_a == "max_drawdown_soft_warn"
        assert "strictly less than" in e.invariant_description

    def test_soft_warn_greater_than_hard_stop_raises(self):
        with pytest.raises(RiskParameterConsistencyError):
            _rp(max_drawdown_soft_warn=0.20, max_drawdown_hard_stop=0.10)


# =============================================================================
# Valid constructions (ensure happy path covers real module)
# =============================================================================

class TestValidConstructions:
    def test_position_spec_valid(self):
        ps = _ps()
        assert ps.symbol == "BTC-USD"
        assert ps.side == Side.LONG

    def test_portfolio_state_valid(self):
        pf = _pf()
        assert pf.nav == 1_000_000.0

    def test_risk_parameters_valid(self):
        rp = _rp()
        assert rp.kelly_fraction == 0.25

    def test_enums(self):
        assert Side.LONG == "LONG"
        assert Side.SHORT == "SHORT"
        assert RiskVerdict.APPROVE == "APPROVE"
        assert RiskVerdict.HALT == "HALT"
