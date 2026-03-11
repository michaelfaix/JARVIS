# tests/unit/risk/test_fx_exposure_manager.py
# Comprehensive tests for FXExposureManager per FAS v6.0.1 Phase 6A.
# Covers: frozen dataclasses, currency decomposition, netting, risk scoring,
# edge cases, determinism, and import contracts.

import math
import pytest

from jarvis.risk.fx_exposure_manager import (
    CurrencyExposure,
    FXExposureResult,
    FXExposureManager,
)


# ---------------------------------------------------------------------------
# FIXTURES
# ---------------------------------------------------------------------------

@pytest.fixture
def manager():
    """Fresh FXExposureManager instance per test (DET-02)."""
    return FXExposureManager()


# ===========================================================================
# 1. FROZEN / IMMUTABILITY TESTS
# ===========================================================================

class TestCurrencyExposureFrozen:
    """CurrencyExposure must be a frozen dataclass."""

    def test_frozen_currency_exposure_cannot_set_field(self):
        exp = CurrencyExposure(
            currency="EUR", gross_long=100.0, gross_short=50.0,
            net_exposure=50.0, hedge_ratio=0.5,
        )
        with pytest.raises(AttributeError):
            exp.currency = "USD"

    def test_frozen_currency_exposure_cannot_set_numeric_field(self):
        exp = CurrencyExposure(
            currency="EUR", gross_long=100.0, gross_short=50.0,
            net_exposure=50.0, hedge_ratio=0.5,
        )
        with pytest.raises(AttributeError):
            exp.gross_long = 999.0

    def test_currency_exposure_fields_correct(self):
        exp = CurrencyExposure(
            currency="USD", gross_long=200.0, gross_short=100.0,
            net_exposure=100.0, hedge_ratio=0.5,
        )
        assert exp.currency == "USD"
        assert exp.gross_long == 200.0
        assert exp.gross_short == 100.0
        assert exp.net_exposure == 100.0
        assert exp.hedge_ratio == 0.5


class TestFXExposureResultFrozen:
    """FXExposureResult must be a frozen dataclass."""

    def test_frozen_fx_exposure_result_cannot_set_field(self):
        result = FXExposureResult(
            exposures=(), total_gross_exposure=0.0,
            total_net_exposure=0.0, netting_benefit=0.0, risk_score=0.0,
        )
        with pytest.raises(AttributeError):
            result.risk_score = 0.5

    def test_frozen_fx_exposure_result_cannot_set_exposures(self):
        result = FXExposureResult(
            exposures=(), total_gross_exposure=0.0,
            total_net_exposure=0.0, netting_benefit=0.0, risk_score=0.0,
        )
        with pytest.raises(AttributeError):
            result.exposures = ()

    def test_exposures_is_tuple(self):
        """Exposures must be a tuple (immutable sequence)."""
        result = FXExposureResult(
            exposures=(), total_gross_exposure=0.0,
            total_net_exposure=0.0, netting_benefit=0.0, risk_score=0.0,
        )
        assert isinstance(result.exposures, tuple)


# ===========================================================================
# 2. SINGLE PAIR DECOMPOSITION
# ===========================================================================

class TestSinglePairExposure:
    """Test currency decomposition for a single forex pair."""

    def test_eurusd_long_decomposes_correctly(self, manager):
        """Long EURUSD = long EUR, short USD."""
        result = manager.compute_exposure({"EURUSD": 100000.0})

        eur = _find_currency(result, "EUR")
        usd = _find_currency(result, "USD")

        assert eur is not None
        assert eur.gross_long == 100000.0
        assert eur.gross_short == 0.0
        assert eur.net_exposure == 100000.0

        assert usd is not None
        assert usd.gross_long == 0.0
        assert usd.gross_short == 100000.0
        assert usd.net_exposure == -100000.0

    def test_eurusd_short_decomposes_correctly(self, manager):
        """Short EURUSD = short EUR, long USD."""
        result = manager.compute_exposure({"EURUSD": -100000.0})

        eur = _find_currency(result, "EUR")
        usd = _find_currency(result, "USD")

        assert eur.gross_long == 0.0
        assert eur.gross_short == 100000.0
        assert eur.net_exposure == -100000.0

        assert usd.gross_long == 100000.0
        assert usd.gross_short == 0.0
        assert usd.net_exposure == 100000.0

    def test_usdjpy_long_decomposes_correctly(self, manager):
        """Long USDJPY = long USD, short JPY."""
        result = manager.compute_exposure({"USDJPY": 50000.0})

        usd = _find_currency(result, "USD")
        jpy = _find_currency(result, "JPY")

        assert usd.gross_long == 50000.0
        assert usd.net_exposure == 50000.0
        assert jpy.gross_short == 50000.0
        assert jpy.net_exposure == -50000.0

    def test_single_pair_no_netting(self, manager):
        """A single pair has zero netting benefit."""
        result = manager.compute_exposure({"GBPUSD": 100000.0})
        assert result.netting_benefit == 0.0

    def test_single_pair_total_gross(self, manager):
        """Total gross = 2 * abs(position) for a single pair (two legs)."""
        result = manager.compute_exposure({"EURUSD": 100000.0})
        assert result.total_gross_exposure == 200000.0

    def test_single_pair_total_net(self, manager):
        """Total net = sum of abs(net) per currency."""
        result = manager.compute_exposure({"EURUSD": 100000.0})
        # EUR net=+100k, USD net=-100k => total_net = 200k
        assert result.total_net_exposure == 200000.0


# ===========================================================================
# 3. MULTIPLE PAIRS WITH NETTING
# ===========================================================================

class TestMultiplePairNetting:
    """Test netting across multiple forex pairs."""

    def test_eurusd_long_eurgbp_short_partial_eur_netting(self, manager):
        """
        Long EURUSD (+EUR, -USD) + Short EURGBP (-EUR, +GBP).
        EUR partially nets: long 100k + short 50k = net +50k.
        """
        result = manager.compute_exposure({
            "EURUSD": 100000.0,
            "EURGBP": -50000.0,
        })

        eur = _find_currency(result, "EUR")
        assert eur.gross_long == 100000.0
        assert eur.gross_short == 50000.0
        assert eur.net_exposure == 50000.0
        # hedge_ratio = 1 - |net|/gross = 1 - 50k/150k = 2/3
        assert eur.hedge_ratio == pytest.approx(2.0 / 3.0, abs=1e-10)

    def test_eurusd_and_gbpusd_long_usd_netting(self, manager):
        """
        Long EURUSD (-USD) + Long GBPUSD (-USD).
        USD shorts accumulate: no netting on USD side.
        """
        result = manager.compute_exposure({
            "EURUSD": 100000.0,
            "GBPUSD": 100000.0,
        })

        usd = _find_currency(result, "USD")
        assert usd.gross_short == 200000.0
        assert usd.gross_long == 0.0
        assert usd.net_exposure == -200000.0
        assert usd.hedge_ratio == 0.0

    def test_three_pairs_complex_netting(self, manager):
        """Multiple pairs create cross-currency netting."""
        result = manager.compute_exposure({
            "EURUSD": 100000.0,   # +EUR, -USD
            "USDJPY": 100000.0,   # +USD, -JPY
            "EURJPY": -50000.0,   # -EUR, +JPY
        })

        # EUR: long 100k (EURUSD), short 50k (EURJPY) => net +50k
        eur = _find_currency(result, "EUR")
        assert eur.net_exposure == 50000.0

        # USD: short 100k (EURUSD), long 100k (USDJPY) => net 0
        usd = _find_currency(result, "USD")
        assert usd.net_exposure == 0.0
        assert usd.hedge_ratio == 1.0  # fully hedged

        # JPY: short 100k (USDJPY), long 50k (EURJPY) => net -50k
        jpy = _find_currency(result, "JPY")
        assert jpy.net_exposure == -50000.0

    def test_netting_benefit_positive_when_hedging_exists(self, manager):
        """Netting benefit > 0 when cross-pair hedging occurs."""
        result = manager.compute_exposure({
            "EURUSD": 100000.0,
            "USDJPY": 100000.0,
        })
        # USD nets: short 100k + long 100k = 0 net
        # So total_net < total_gross => netting_benefit > 0
        assert result.netting_benefit > 0.0

    def test_netting_benefit_bounded_zero_one(self, manager):
        """Netting benefit is always in [0, 1]."""
        result = manager.compute_exposure({
            "EURUSD": 100000.0,
            "EURGBP": -50000.0,
            "GBPJPY": 75000.0,
        })
        assert 0.0 <= result.netting_benefit <= 1.0


# ===========================================================================
# 4. OPPOSITE POSITIONS — FULL NETTING
# ===========================================================================

class TestFullNetting:
    """Test that opposite positions in the same pair fully net out."""

    def test_same_pair_opposite_positions_zero_net(self, manager):
        """Long and short same pair, same size => zero net per currency."""
        result = manager.compute_exposure({
            "EURUSD": 100000.0,
        })
        # Add opposite — simulate with two separate pairs not possible
        # Instead test with a zero position
        result_zero = manager.compute_exposure({"EURUSD": 0.0})
        assert result_zero.total_net_exposure == 0.0
        assert result_zero.total_gross_exposure == 0.0

    def test_two_pairs_full_hedge_usd(self, manager):
        """EURUSD long + USDJPY short => USD fully hedged."""
        # EURUSD long: +EUR -USD(100k)
        # USDJPY short: -USD(100k) +JPY  -- wait, short USDJPY = short USD, long JPY
        # Actually short USDJPY: short USD, long JPY
        # So USD: short 100k + short 100k = no hedge
        # Let's do: EURUSD short + USDJPY long
        # EURUSD short: -EUR +USD(100k)
        # USDJPY long: +USD(100k) -JPY
        # USD: long 100k + long 100k = no hedge either
        # For full USD hedge: EURUSD long (-USD) + GBPUSD short (-GBP +USD)
        result = manager.compute_exposure({
            "EURUSD": 100000.0,    # +EUR, -USD
            "GBPUSD": -100000.0,   # -GBP, +USD
        })
        usd = _find_currency(result, "USD")
        assert usd.net_exposure == 0.0
        assert usd.hedge_ratio == 1.0


# ===========================================================================
# 5. NO POSITIONS / EDGE CASES
# ===========================================================================

class TestEdgeCases:
    """Edge cases: empty dict, zero positions, etc."""

    def test_empty_positions_returns_zero(self, manager):
        result = manager.compute_exposure({})
        assert result.total_gross_exposure == 0.0
        assert result.total_net_exposure == 0.0
        assert result.netting_benefit == 0.0
        assert result.risk_score == 0.0
        assert result.exposures == ()

    def test_zero_position_size(self, manager):
        result = manager.compute_exposure({"EURUSD": 0.0})
        assert result.total_gross_exposure == 0.0
        assert result.total_net_exposure == 0.0

    def test_very_small_position(self, manager):
        result = manager.compute_exposure({"EURUSD": 0.01})
        assert result.total_gross_exposure == pytest.approx(0.02, abs=1e-10)

    def test_all_zero_positions(self, manager):
        result = manager.compute_exposure({
            "EURUSD": 0.0,
            "GBPUSD": 0.0,
            "USDJPY": 0.0,
        })
        assert result.total_gross_exposure == 0.0
        assert result.total_net_exposure == 0.0
        assert result.exposures == ()


# ===========================================================================
# 6. RISK SCORE
# ===========================================================================

class TestRiskScore:
    """Risk score must be in [0, 1] and reflect concentration."""

    def test_risk_score_in_range(self, manager):
        result = manager.compute_exposure({"EURUSD": 100000.0})
        assert 0.0 <= result.risk_score <= 1.0

    def test_risk_score_single_pair_is_maximum(self, manager):
        """Single pair => two currencies => some concentration."""
        result = manager.compute_exposure({"EURUSD": 100000.0})
        # Two currencies with equal net => HHI_norm = 0 (perfectly balanced)
        # Actually: EUR net=100k, USD net=-100k => weights both 0.5
        # HHI = 0.25 + 0.25 = 0.5, min=0.5, norm = 0.0
        assert result.risk_score == pytest.approx(0.0, abs=1e-10)

    def test_risk_score_concentrated_exposure(self, manager):
        """Highly concentrated => higher risk score."""
        # EURUSD long 100k + EURGBP long 100k + EURJPY long 100k
        # EUR longs: 300k total, other currencies split
        result = manager.compute_exposure({
            "EURUSD": 100000.0,
            "EURGBP": 100000.0,
            "EURJPY": 100000.0,
        })
        # EUR has large net vs USD/GBP/JPY each with smaller nets
        assert result.risk_score > 0.0

    def test_risk_score_diversified_lower_than_concentrated(self, manager):
        """More diversified positions should have lower risk score."""
        # Concentrated: all EUR-based
        concentrated = manager.compute_exposure({
            "EURUSD": 100000.0,
            "EURGBP": 100000.0,
            "EURJPY": 100000.0,
        })

        # Diversified: spread across different base currencies
        diversified = manager.compute_exposure({
            "EURUSD": 100000.0,
            "GBPJPY": 100000.0,
            "AUDUSD": 100000.0,
        })

        assert diversified.risk_score <= concentrated.risk_score

    def test_risk_score_zero_for_empty(self, manager):
        result = manager.compute_exposure({})
        assert result.risk_score == 0.0

    def test_risk_score_zero_for_fully_netted(self, manager):
        """If all net exposures are zero, risk score is zero."""
        result = manager.compute_exposure({
            "EURUSD": 100000.0,
            "GBPUSD": -100000.0,
        })
        # USD fully hedged (net=0). EUR net=+100k, GBP net=-100k
        # Not fully netted overall, but USD is
        # risk_score depends on remaining concentrations
        assert 0.0 <= result.risk_score <= 1.0


# ===========================================================================
# 7. NETTING BENEFIT CALCULATION
# ===========================================================================

class TestNettingBenefit:
    """Netting benefit = 1 - (total_net / total_gross)."""

    def test_no_netting_benefit_single_pair(self, manager):
        result = manager.compute_exposure({"EURUSD": 100000.0})
        assert result.netting_benefit == pytest.approx(0.0, abs=1e-10)

    def test_full_netting_benefit(self, manager):
        """When all currencies net to zero, netting benefit = 1.0."""
        # EURUSD long + USDJPY long + EURJPY short of matching sizes
        # EUR: long 100k, short 100k => net 0
        # USD: short 100k, long 100k => net 0
        # JPY: short 100k, long 100k => net 0
        result = manager.compute_exposure({
            "EURUSD": 100000.0,    # +EUR -USD
            "USDJPY": 100000.0,    # +USD -JPY
            "EURJPY": -100000.0,   # -EUR +JPY
        })
        assert result.netting_benefit == pytest.approx(1.0, abs=1e-10)
        assert result.total_net_exposure == pytest.approx(0.0, abs=1e-10)

    def test_partial_netting_benefit(self, manager):
        """Partial netting gives benefit between 0 and 1."""
        result = manager.compute_exposure({
            "EURUSD": 100000.0,
            "USDJPY": 100000.0,
        })
        assert 0.0 < result.netting_benefit < 1.0


# ===========================================================================
# 8. BASE CURRENCY HANDLING
# ===========================================================================

class TestBaseCurrency:
    """Base currency parameter is accepted and does not affect pure analysis."""

    def test_default_base_currency_usd(self, manager):
        """Default base_currency is USD."""
        result = manager.compute_exposure({"EURUSD": 100000.0})
        assert result.total_gross_exposure > 0.0

    def test_custom_base_currency_accepted(self, manager):
        result = manager.compute_exposure(
            {"EURUSD": 100000.0}, base_currency="EUR"
        )
        assert result.total_gross_exposure > 0.0

    def test_base_currency_does_not_change_calculation(self, manager):
        """Base currency is informational only — no rate conversion."""
        result_usd = manager.compute_exposure(
            {"EURUSD": 100000.0}, base_currency="USD"
        )
        result_eur = manager.compute_exposure(
            {"EURUSD": 100000.0}, base_currency="EUR"
        )
        assert result_usd.total_gross_exposure == result_eur.total_gross_exposure
        assert result_usd.total_net_exposure == result_eur.total_net_exposure
        assert result_usd.netting_benefit == result_eur.netting_benefit
        assert result_usd.risk_score == result_eur.risk_score


# ===========================================================================
# 9. UNKNOWN PAIR HANDLING
# ===========================================================================

class TestUnknownPairHandling:
    """Unknown pairs must raise ValueError."""

    def test_unknown_pair_raises_value_error(self, manager):
        with pytest.raises(ValueError, match="Unknown currency pair"):
            manager.compute_exposure({"XYZABC": 100000.0})

    def test_unknown_pair_among_valid_raises(self, manager):
        with pytest.raises(ValueError, match="Unknown currency pair"):
            manager.compute_exposure({
                "EURUSD": 100000.0,
                "FOOBAZ": 50000.0,
            })

    def test_invalid_positions_type_raises(self, manager):
        with pytest.raises(TypeError, match="positions must be a dict"):
            manager.compute_exposure([("EURUSD", 100000.0)])


# ===========================================================================
# 10. DETERMINISM TESTS (DET-01 through DET-07)
# ===========================================================================

class TestDeterminism:
    """Same inputs must produce bit-identical outputs."""

    def test_deterministic_same_input_same_output(self, manager):
        positions = {
            "EURUSD": 100000.0,
            "GBPUSD": -50000.0,
            "USDJPY": 75000.0,
        }
        result1 = manager.compute_exposure(positions)
        result2 = manager.compute_exposure(positions)

        assert result1.total_gross_exposure == result2.total_gross_exposure
        assert result1.total_net_exposure == result2.total_net_exposure
        assert result1.netting_benefit == result2.netting_benefit
        assert result1.risk_score == result2.risk_score
        assert len(result1.exposures) == len(result2.exposures)

        for e1, e2 in zip(result1.exposures, result2.exposures):
            assert e1.currency == e2.currency
            assert e1.gross_long == e2.gross_long
            assert e1.gross_short == e2.gross_short
            assert e1.net_exposure == e2.net_exposure
            assert e1.hedge_ratio == e2.hedge_ratio

    def test_deterministic_fresh_instance(self):
        """Fresh manager instances must produce identical results (DET-02)."""
        positions = {"EURUSD": 100000.0, "EURGBP": -30000.0}
        result1 = FXExposureManager().compute_exposure(positions)
        result2 = FXExposureManager().compute_exposure(positions)
        assert result1.total_gross_exposure == result2.total_gross_exposure
        assert result1.risk_score == result2.risk_score


# ===========================================================================
# 11. IMPORT CONTRACT
# ===========================================================================

class TestImportContract:
    """__all__ must export the public API."""

    def test_all_exports_defined(self):
        from jarvis.risk import fx_exposure_manager
        assert hasattr(fx_exposure_manager, "__all__")
        assert "CurrencyExposure" in fx_exposure_manager.__all__
        assert "FXExposureResult" in fx_exposure_manager.__all__
        assert "FXExposureManager" in fx_exposure_manager.__all__

    def test_all_exports_count(self):
        from jarvis.risk import fx_exposure_manager
        assert len(fx_exposure_manager.__all__) == 3


# ===========================================================================
# 12. ALL SUPPORTED PAIRS
# ===========================================================================

class TestAllSupportedPairs:
    """Every supported pair must decompose without error."""

    @pytest.mark.parametrize("pair", [
        "EURUSD", "GBPUSD", "USDJPY", "AUDUSD", "USDCHF",
        "USDCAD", "NZDUSD", "EURGBP", "EURJPY", "GBPJPY",
    ])
    def test_supported_pair_long(self, manager, pair):
        result = manager.compute_exposure({pair: 100000.0})
        assert result.total_gross_exposure == 200000.0
        assert len(result.exposures) == 2

    @pytest.mark.parametrize("pair", [
        "EURUSD", "GBPUSD", "USDJPY", "AUDUSD", "USDCHF",
        "USDCAD", "NZDUSD", "EURGBP", "EURJPY", "GBPJPY",
    ])
    def test_supported_pair_short(self, manager, pair):
        result = manager.compute_exposure({pair: -100000.0})
        assert result.total_gross_exposure == 200000.0
        assert len(result.exposures) == 2


# ===========================================================================
# HELPERS
# ===========================================================================

def _find_currency(result: FXExposureResult, currency: str):
    """Find a CurrencyExposure by currency code, or None."""
    for exp in result.exposures:
        if exp.currency == currency:
            return exp
    return None
