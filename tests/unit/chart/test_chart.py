# =============================================================================
# tests/unit/chart/test_chart.py — S32 Chart Interface
#
# Comprehensive tests for:
#   - ChartOverlay (contract dataclass)
#   - ChartDataBuilder (data transformation)
#   - P0 enforcement (no order-type fields)
#   - Uncertainty band classification
#   - Determinism (DET-05)
# =============================================================================

import dataclasses
import pytest
from dataclasses import dataclass
from enum import Enum
from typing import List

from jarvis.chart.chart_contract import ChartOverlay
from jarvis.chart.chart_data_builder import ChartDataBuilder


# ---------------------------------------------------------------------------
# MOCK INPUT TYPES (duck-typed stand-ins for real system outputs)
# ---------------------------------------------------------------------------

@dataclass
class MockConfidenceZone:
    entry_lower: float = 47890.0
    entry_upper: float = 48320.0
    entry_confidence: float = 0.712
    exit_soft: float = 47200.0
    exit_hard: float = 46500.0
    exit_confidence: float = 0.288
    expected_move_pct: float = 2.14
    vol_adjusted_stop: float = 46812.0
    meta_uncertainty: float = 0.234


class MockStrategyMode(Enum):
    MOMENTUM = "MOMENTUM"
    DEFENSIVE = "DEFENSIVE"
    RISK_REDUCTION = "RISK_REDUCTION"
    MEAN_REVERSION = "MEAN_REVERSION"
    MINIMAL_EXPOSURE = "MINIMAL_EXPOSURE"


@dataclass(frozen=True)
class MockStrategyModeConfig:
    label: str = "MOMENTUM"
    confidence_box_scale: float = 1.0
    max_exposure_pct: float = 0.80
    position_size_cap: float = 0.9
    recalibration_priority: str = "LOW"


@dataclass
class MockStrategySelection:
    mode: MockStrategyMode = MockStrategyMode.MOMENTUM
    config: MockStrategyModeConfig = None
    activation_reason: str = "Trend detected"
    override_locked: bool = True

    def __post_init__(self):
        if self.config is None:
            self.config = MockStrategyModeConfig()


@dataclass
class MockRiskOutput:
    expected_drawdown: float = 0.05
    expected_drawdown_p95: float = 0.10
    volatility_forecast: float = 0.18
    risk_compression_active: bool = False
    position_size_factor: float = 0.8
    exposure_weight: float = 0.65
    risk_regime: str = "NORMAL"


# ---------------------------------------------------------------------------
# CHART OVERLAY DATACLASS
# ---------------------------------------------------------------------------

class TestChartOverlayFields:
    """Verify ChartOverlay has all required fields per FAS."""

    def test_all_fields_present(self):
        overlay = ChartOverlay(
            entry_box_lower=47890.0,
            entry_box_upper=48320.0,
            entry_confidence_pct=71.2,
            exit_corridor_soft=47200.0,
            exit_corridor_hard=46500.0,
            exit_confidence_pct=28.8,
            expected_move_pct=2.14,
            vol_stop_price=46812.0,
            vol_stop_distance_pct=2.48,
            regime_label="TRENDING",
            strategy_mode_label="MOMENTUM",
            meta_uncertainty_pct=23.4,
            uncertainty_band="LOW",
            timeframe_label="5m",
            risk_compression_active=False,
        )
        assert overlay.entry_box_lower == 47890.0
        assert overlay.entry_box_upper == 48320.0
        assert overlay.entry_confidence_pct == 71.2
        assert overlay.exit_corridor_soft == 47200.0
        assert overlay.exit_corridor_hard == 46500.0
        assert overlay.exit_confidence_pct == 28.8
        assert overlay.expected_move_pct == 2.14
        assert overlay.vol_stop_price == 46812.0
        assert overlay.vol_stop_distance_pct == 2.48
        assert overlay.regime_label == "TRENDING"
        assert overlay.strategy_mode_label == "MOMENTUM"
        assert overlay.meta_uncertainty_pct == 23.4
        assert overlay.uncertainty_band == "LOW"
        assert overlay.timeframe_label == "5m"
        assert overlay.risk_compression_active is False

    def test_field_count(self):
        """ChartOverlay must have exactly 15 fields."""
        fields = dataclasses.fields(ChartOverlay)
        assert len(fields) == 15


# ---------------------------------------------------------------------------
# P0 ENFORCEMENT — NO ORDER-TYPE FIELDS
# ---------------------------------------------------------------------------

class TestP0Enforcement:
    """Verify: ChartOverlay contains NO order-type fields."""

    FORBIDDEN_FIELD_NAMES = [
        "buy", "sell", "execute", "order", "close_position",
        "broker", "margin", "account_balance", "trade",
        "long", "short", "take_profit", "stop_loss_order",
        "routing", "api_key", "one_click",
    ]

    def test_no_forbidden_fields(self):
        field_names = [f.name for f in dataclasses.fields(ChartOverlay)]
        for forbidden in self.FORBIDDEN_FIELD_NAMES:
            for name in field_names:
                assert forbidden not in name.lower(), (
                    f"P0 VIOLATION: Field '{name}' contains forbidden term "
                    f"'{forbidden}'"
                )

    def test_no_signal_direction_fields(self):
        """No field should indicate trade direction."""
        field_names = [f.name for f in dataclasses.fields(ChartOverlay)]
        direction_terms = ["signal", "direction", "side", "action"]
        for term in direction_terms:
            for name in field_names:
                assert term not in name.lower(), (
                    f"P0 VIOLATION: Field '{name}' suggests direction"
                )


# ---------------------------------------------------------------------------
# CHART DATA BUILDER — CONSTANTS
# ---------------------------------------------------------------------------

class TestChartDataBuilderConstants:
    """Verify fixed literals (DET-06)."""

    def test_uncertainty_bands(self):
        bands = ChartDataBuilder.UNCERTAINTY_BANDS
        assert len(bands) == 4
        assert bands[0] == (0.20, "LOW")
        assert bands[1] == (0.50, "MODERATE")
        assert bands[2] == (0.75, "HIGH")
        assert bands[3] == (1.00, "EXTREME")

    def test_bands_sorted_ascending(self):
        bands = ChartDataBuilder.UNCERTAINTY_BANDS
        thresholds = [b[0] for b in bands]
        assert thresholds == sorted(thresholds)


# ---------------------------------------------------------------------------
# CHART DATA BUILDER — BUILD
# ---------------------------------------------------------------------------

class TestChartDataBuilderBuild:
    """Test the build() data transformation."""

    def _build_default(self, **cz_overrides):
        builder = ChartDataBuilder()
        cz = MockConfidenceZone(**cz_overrides)
        risk = MockRiskOutput()
        strat = MockStrategySelection()
        return builder.build(cz, risk, strat, current_price=48000.0,
                              timeframe_label="5m")

    def test_build_returns_chart_overlay(self):
        overlay = self._build_default()
        assert isinstance(overlay, ChartOverlay)

    def test_entry_box_mapped(self):
        overlay = self._build_default()
        assert overlay.entry_box_lower == 47890.0
        assert overlay.entry_box_upper == 48320.0

    def test_entry_confidence_pct(self):
        overlay = self._build_default()
        assert overlay.entry_confidence_pct == 71.2  # 0.712 * 100

    def test_exit_corridor_mapped(self):
        overlay = self._build_default()
        assert overlay.exit_corridor_soft == 47200.0
        assert overlay.exit_corridor_hard == 46500.0

    def test_exit_confidence_pct(self):
        overlay = self._build_default()
        assert overlay.exit_confidence_pct == 28.8  # 0.288 * 100

    def test_expected_move_pct(self):
        overlay = self._build_default()
        assert overlay.expected_move_pct == 2.14

    def test_vol_stop_price(self):
        overlay = self._build_default()
        assert overlay.vol_stop_price == 46812.0

    def test_vol_stop_distance_pct(self):
        """abs(48000 - 46812) / 48000 * 100 = 2.475 → 2.48"""
        overlay = self._build_default()
        expected = round(abs(48000.0 - 46812.0) / 48000.0 * 100.0, 2)
        assert overlay.vol_stop_distance_pct == expected

    def test_regime_label_from_config(self):
        overlay = self._build_default()
        assert overlay.regime_label == "MOMENTUM"

    def test_strategy_mode_label_from_mode_value(self):
        overlay = self._build_default()
        assert overlay.strategy_mode_label == "MOMENTUM"

    def test_meta_uncertainty_pct(self):
        overlay = self._build_default()
        assert overlay.meta_uncertainty_pct == 23.4  # 0.234 * 100

    def test_timeframe_label(self):
        overlay = self._build_default()
        assert overlay.timeframe_label == "5m"

    def test_risk_compression_from_risk_output(self):
        builder = ChartDataBuilder()
        cz = MockConfidenceZone()
        risk = MockRiskOutput(risk_compression_active=True)
        strat = MockStrategySelection()
        overlay = builder.build(cz, risk, strat, 48000.0, "1h")
        assert overlay.risk_compression_active is True

    def test_risk_compression_false(self):
        overlay = self._build_default()
        assert overlay.risk_compression_active is False


# ---------------------------------------------------------------------------
# UNCERTAINTY BAND CLASSIFICATION
# ---------------------------------------------------------------------------

class TestUncertaintyBands:
    """Test uncertainty band thresholds."""

    def _build_with_uncertainty(self, meta_uncertainty: float):
        builder = ChartDataBuilder()
        cz = MockConfidenceZone(meta_uncertainty=meta_uncertainty)
        risk = MockRiskOutput()
        strat = MockStrategySelection()
        return builder.build(cz, risk, strat, 48000.0, "5m")

    def test_band_low(self):
        overlay = self._build_with_uncertainty(0.10)
        assert overlay.uncertainty_band == "LOW"

    def test_band_low_boundary(self):
        overlay = self._build_with_uncertainty(0.20)
        assert overlay.uncertainty_band == "LOW"

    def test_band_moderate(self):
        overlay = self._build_with_uncertainty(0.35)
        assert overlay.uncertainty_band == "MODERATE"

    def test_band_moderate_boundary(self):
        overlay = self._build_with_uncertainty(0.50)
        assert overlay.uncertainty_band == "MODERATE"

    def test_band_high(self):
        overlay = self._build_with_uncertainty(0.60)
        assert overlay.uncertainty_band == "HIGH"

    def test_band_high_boundary(self):
        overlay = self._build_with_uncertainty(0.75)
        assert overlay.uncertainty_band == "HIGH"

    def test_band_extreme(self):
        overlay = self._build_with_uncertainty(0.90)
        assert overlay.uncertainty_band == "EXTREME"

    def test_band_extreme_boundary(self):
        overlay = self._build_with_uncertainty(1.00)
        assert overlay.uncertainty_band == "EXTREME"

    def test_band_zero_is_low(self):
        overlay = self._build_with_uncertainty(0.0)
        assert overlay.uncertainty_band == "LOW"

    def test_meta_uncertainty_pct_computed(self):
        overlay = self._build_with_uncertainty(0.60)
        assert overlay.meta_uncertainty_pct == 60.0

    def test_meta_uncertainty_pct_rounding(self):
        overlay = self._build_with_uncertainty(0.333)
        assert overlay.meta_uncertainty_pct == 33.3


# ---------------------------------------------------------------------------
# VOLATILITY STOP DISTANCE COMPUTATION
# ---------------------------------------------------------------------------

class TestVolStopDistance:
    """Test vol stop distance percentage computation."""

    def test_stop_below_price(self):
        builder = ChartDataBuilder()
        cz = MockConfidenceZone(vol_adjusted_stop=46000.0)
        risk = MockRiskOutput()
        strat = MockStrategySelection()
        overlay = builder.build(cz, risk, strat, 48000.0, "5m")
        expected = round(abs(48000.0 - 46000.0) / 48000.0 * 100.0, 2)
        assert overlay.vol_stop_distance_pct == expected

    def test_stop_above_price(self):
        """For short positions: stop above current price."""
        builder = ChartDataBuilder()
        cz = MockConfidenceZone(vol_adjusted_stop=50000.0)
        risk = MockRiskOutput()
        strat = MockStrategySelection()
        overlay = builder.build(cz, risk, strat, 48000.0, "5m")
        expected = round(abs(48000.0 - 50000.0) / 48000.0 * 100.0, 2)
        assert overlay.vol_stop_distance_pct == expected

    def test_stop_equals_price(self):
        builder = ChartDataBuilder()
        cz = MockConfidenceZone(vol_adjusted_stop=48000.0)
        risk = MockRiskOutput()
        strat = MockStrategySelection()
        overlay = builder.build(cz, risk, strat, 48000.0, "5m")
        assert overlay.vol_stop_distance_pct == 0.0

    def test_stop_distance_zero_price_safe(self):
        """Division by zero protection via max(price, 1e-10)."""
        builder = ChartDataBuilder()
        cz = MockConfidenceZone(vol_adjusted_stop=100.0)
        risk = MockRiskOutput()
        strat = MockStrategySelection()
        overlay = builder.build(cz, risk, strat, 0.0, "5m")
        # Should not raise, uses max(0.0, 1e-10) = 1e-10
        assert overlay.vol_stop_distance_pct > 0


# ---------------------------------------------------------------------------
# STRATEGY MODE VARIATIONS
# ---------------------------------------------------------------------------

class TestStrategyModeVariations:
    """Test with different strategy modes."""

    def test_defensive_mode(self):
        builder = ChartDataBuilder()
        cz = MockConfidenceZone()
        risk = MockRiskOutput()
        strat = MockStrategySelection(
            mode=MockStrategyMode.DEFENSIVE,
            config=MockStrategyModeConfig(label="DEFENSIVE"),
        )
        overlay = builder.build(cz, risk, strat, 48000.0, "1h")
        assert overlay.regime_label == "DEFENSIVE"
        assert overlay.strategy_mode_label == "DEFENSIVE"

    def test_risk_reduction_mode(self):
        builder = ChartDataBuilder()
        cz = MockConfidenceZone()
        risk = MockRiskOutput()
        strat = MockStrategySelection(
            mode=MockStrategyMode.RISK_REDUCTION,
            config=MockStrategyModeConfig(label="RISK_REDUCTION"),
        )
        overlay = builder.build(cz, risk, strat, 48000.0, "15m")
        assert overlay.regime_label == "RISK_REDUCTION"
        assert overlay.strategy_mode_label == "RISK_REDUCTION"

    def test_minimal_exposure_mode(self):
        builder = ChartDataBuilder()
        cz = MockConfidenceZone()
        risk = MockRiskOutput()
        strat = MockStrategySelection(
            mode=MockStrategyMode.MINIMAL_EXPOSURE,
            config=MockStrategyModeConfig(label="MINIMAL_EXPOSURE"),
        )
        overlay = builder.build(cz, risk, strat, 48000.0, "1D")
        assert overlay.strategy_mode_label == "MINIMAL_EXPOSURE"


# ---------------------------------------------------------------------------
# TIMEFRAME VARIATIONS
# ---------------------------------------------------------------------------

class TestTimeframeVariations:
    """Test with different timeframe labels."""

    @pytest.mark.parametrize("tf", ["1m", "5m", "15m", "1h", "4h", "1D", "1W"])
    def test_timeframe_passthrough(self, tf):
        builder = ChartDataBuilder()
        cz = MockConfidenceZone()
        risk = MockRiskOutput()
        strat = MockStrategySelection()
        overlay = builder.build(cz, risk, strat, 48000.0, tf)
        assert overlay.timeframe_label == tf


# ---------------------------------------------------------------------------
# R3/R4/R5 VISIBILITY REQUIREMENTS
# ---------------------------------------------------------------------------

class TestVisibilityRequirements:
    """Verify R3, R4, R5: required fields always present."""

    def test_r3_meta_uncertainty_always_present(self):
        """R3: meta_uncertainty_pct IMMER sichtbar."""
        builder = ChartDataBuilder()
        cz = MockConfidenceZone(meta_uncertainty=0.0)
        risk = MockRiskOutput()
        strat = MockStrategySelection()
        overlay = builder.build(cz, risk, strat, 48000.0, "5m")
        assert hasattr(overlay, "meta_uncertainty_pct")
        assert overlay.meta_uncertainty_pct == 0.0

    def test_r4_risk_compression_always_present(self):
        """R4: risk_compression_active IMMER im Header sichtbar."""
        builder = ChartDataBuilder()
        cz = MockConfidenceZone()
        risk = MockRiskOutput(risk_compression_active=False)
        strat = MockStrategySelection()
        overlay = builder.build(cz, risk, strat, 48000.0, "5m")
        assert hasattr(overlay, "risk_compression_active")
        assert overlay.risk_compression_active is False

    def test_r5_timeframe_always_present(self):
        """R5: timeframe_label IMMER sichtbar."""
        builder = ChartDataBuilder()
        cz = MockConfidenceZone()
        risk = MockRiskOutput()
        strat = MockStrategySelection()
        overlay = builder.build(cz, risk, strat, 48000.0, "15m")
        assert hasattr(overlay, "timeframe_label")
        assert overlay.timeframe_label == "15m"


# ---------------------------------------------------------------------------
# DETERMINISM (DET-05)
# ---------------------------------------------------------------------------

class TestDeterminism:
    """Same inputs → same outputs."""

    def test_same_inputs_same_output(self):
        builder = ChartDataBuilder()
        cz = MockConfidenceZone()
        risk = MockRiskOutput()
        strat = MockStrategySelection()

        o1 = builder.build(cz, risk, strat, 48000.0, "5m")
        o2 = builder.build(cz, risk, strat, 48000.0, "5m")

        assert o1.entry_box_lower == o2.entry_box_lower
        assert o1.entry_box_upper == o2.entry_box_upper
        assert o1.entry_confidence_pct == o2.entry_confidence_pct
        assert o1.exit_corridor_soft == o2.exit_corridor_soft
        assert o1.exit_corridor_hard == o2.exit_corridor_hard
        assert o1.exit_confidence_pct == o2.exit_confidence_pct
        assert o1.expected_move_pct == o2.expected_move_pct
        assert o1.vol_stop_price == o2.vol_stop_price
        assert o1.vol_stop_distance_pct == o2.vol_stop_distance_pct
        assert o1.regime_label == o2.regime_label
        assert o1.strategy_mode_label == o2.strategy_mode_label
        assert o1.meta_uncertainty_pct == o2.meta_uncertainty_pct
        assert o1.uncertainty_band == o2.uncertainty_band
        assert o1.timeframe_label == o2.timeframe_label
        assert o1.risk_compression_active == o2.risk_compression_active

    def test_different_inputs_different_output(self):
        builder = ChartDataBuilder()
        risk = MockRiskOutput()
        strat = MockStrategySelection()

        cz1 = MockConfidenceZone(entry_lower=47000.0)
        cz2 = MockConfidenceZone(entry_lower=48000.0)

        o1 = builder.build(cz1, risk, strat, 48000.0, "5m")
        o2 = builder.build(cz2, risk, strat, 48000.0, "5m")

        assert o1.entry_box_lower != o2.entry_box_lower


# ---------------------------------------------------------------------------
# EDGE CASES
# ---------------------------------------------------------------------------

class TestEdgeCases:
    """Edge cases and boundary conditions."""

    def test_very_small_price(self):
        builder = ChartDataBuilder()
        cz = MockConfidenceZone(vol_adjusted_stop=0.001)
        risk = MockRiskOutput()
        strat = MockStrategySelection()
        overlay = builder.build(cz, risk, strat, 0.01, "5m")
        assert overlay.vol_stop_distance_pct >= 0

    def test_very_large_price(self):
        builder = ChartDataBuilder()
        cz = MockConfidenceZone(
            entry_lower=99000.0, entry_upper=101000.0,
            vol_adjusted_stop=95000.0,
        )
        risk = MockRiskOutput()
        strat = MockStrategySelection()
        overlay = builder.build(cz, risk, strat, 100000.0, "5m")
        assert overlay.entry_box_lower == 99000.0
        assert overlay.vol_stop_distance_pct == 5.0

    def test_full_uncertainty(self):
        builder = ChartDataBuilder()
        cz = MockConfidenceZone(meta_uncertainty=1.0)
        risk = MockRiskOutput()
        strat = MockStrategySelection()
        overlay = builder.build(cz, risk, strat, 48000.0, "5m")
        assert overlay.meta_uncertainty_pct == 100.0
        assert overlay.uncertainty_band == "EXTREME"

    def test_zero_uncertainty(self):
        builder = ChartDataBuilder()
        cz = MockConfidenceZone(meta_uncertainty=0.0)
        risk = MockRiskOutput()
        strat = MockStrategySelection()
        overlay = builder.build(cz, risk, strat, 48000.0, "5m")
        assert overlay.meta_uncertainty_pct == 0.0
        assert overlay.uncertainty_band == "LOW"

    def test_confidence_rounding(self):
        """Confidence values are rounded to 1 decimal."""
        builder = ChartDataBuilder()
        cz = MockConfidenceZone(
            entry_confidence=0.71234,
            exit_confidence=0.28876,
        )
        risk = MockRiskOutput()
        strat = MockStrategySelection()
        overlay = builder.build(cz, risk, strat, 48000.0, "5m")
        assert overlay.entry_confidence_pct == 71.2
        assert overlay.exit_confidence_pct == 28.9

    def test_expected_move_rounding(self):
        """Expected move rounded to 2 decimals."""
        builder = ChartDataBuilder()
        cz = MockConfidenceZone(expected_move_pct=2.14567)
        risk = MockRiskOutput()
        strat = MockStrategySelection()
        overlay = builder.build(cz, risk, strat, 48000.0, "5m")
        assert overlay.expected_move_pct == 2.15


# ---------------------------------------------------------------------------
# R1: SINGLE SOURCE
# ---------------------------------------------------------------------------

class TestR1SingleSource:
    """R1: ChartDataBuilder is the ONLY source for chart data."""

    def test_builder_produces_complete_overlay(self):
        """Builder must populate ALL fields."""
        builder = ChartDataBuilder()
        cz = MockConfidenceZone()
        risk = MockRiskOutput()
        strat = MockStrategySelection()
        overlay = builder.build(cz, risk, strat, 48000.0, "5m")

        for f in dataclasses.fields(ChartOverlay):
            value = getattr(overlay, f.name)
            assert value is not None, f"Field '{f.name}' is None"


# ---------------------------------------------------------------------------
# PACKAGE IMPORT
# ---------------------------------------------------------------------------

class TestPackageImport:
    def test_import_from_package(self):
        from jarvis.chart import ChartOverlay, ChartDataBuilder
        assert ChartOverlay is not None
        assert ChartDataBuilder is not None
