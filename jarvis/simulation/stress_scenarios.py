# =============================================================================
# jarvis/simulation/stress_scenarios.py — Named Stress Scenario Presets (S28)
#
# Predefined historical and synthetic crisis return series for use with
# StrategyLab.stress_test().  Each preset is a frozen dataclass containing
# a deterministic daily-return tuple that models the crisis characteristics.
#
# Historical scenarios are STYLISED approximations capturing peak drawdown,
# duration, and volatility profile — NOT tick-level replays (no market data
# dependency, no File I/O, no external state).
#
# DETERMINISM:
#   DET-01  No stochastic operations.
#   DET-02  All inputs passed explicitly; presets are module-level constants.
#   DET-03  No side effects.
#   DET-06  All return arrays are fixed literals — NOT parametrisable.
#   DET-07  Same inputs = identical output.
#
# PROHIBITED: logging, random, file IO, network IO, datetime.now()
#
# DEPENDENCIES:
#   stdlib:   dataclasses, typing
#   internal: NONE
#   external: NONE (pure Python)
# =============================================================================

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, Tuple


# =============================================================================
# SECTION 1 -- DATACLASS
# =============================================================================

@dataclass(frozen=True)
class StressScenarioPreset:
    """
    Immutable preset for a named stress scenario.

    Fields:
        name:                  Unique scenario identifier (matches JARVIS_STRESS_SCENARIOS).
        description:           Human-readable scenario description.
        returns:               Tuple of daily returns (deterministic fixed literals).
        duration_days:         Number of trading days in the scenario.
        peak_drawdown:         Expected peak-to-trough drawdown (positive float, e.g. 0.40 = 40%).
        volatility_multiplier: Approximate volatility vs normal conditions (e.g. 4.0 = 4x).
        category:              "historical" or "synthetic".
    """
    name: str
    description: str
    returns: Tuple[float, ...]
    duration_days: int
    peak_drawdown: float
    volatility_multiplier: float
    category: str


# =============================================================================
# SECTION 2 -- HISTORICAL PRESETS (DET-06: fixed literals)
# =============================================================================

# ---------------------------------------------------------------------------
# 2008 Financial Crisis (Sep 15 – Nov 20, 2008)
# S&P 500 peak-to-trough ~40%.  Extreme daily swings -4% to -9%, punctuated
# by violent bear-market rallies.  Vol ~4x normal.  44 trading days.
# ---------------------------------------------------------------------------
_RETURNS_2008: Tuple[float, ...] = (
    -0.0474,  0.0141, -0.0440,  0.0168, -0.0354,  # week 1: Lehman week
    -0.0308, -0.0471,  0.0201, -0.0128, -0.0391,  # week 2: AIG rescue
     0.0316,  0.0413, -0.0259,  0.0402, -0.0137,  # week 3: TARP debate
    -0.0524, -0.0356,  0.0258, -0.0901,  0.0332,  # week 4: TARP rejected
    -0.0389,  0.0585, -0.0321, -0.0146, -0.0587,  # week 5: global contagion
    -0.0340,  0.0324, -0.0718,  0.0204, -0.0196,  # week 6: VIX 80
     0.0393, -0.0477, -0.0229,  0.0455, -0.0528,  # week 7: forced liquidation
     0.0358, -0.0303, -0.0163,  0.0644, -0.0234,  # week 8: dead-cat bounce
    -0.0680,  0.0362, -0.0512,  0.0284,            # week 9: bottom forming
)

FINANCIAL_CRISIS_2008: StressScenarioPreset = StressScenarioPreset(
    name="2008_FINANCIAL_CRISIS",
    description="2008 Financial Crisis (Lehman, TARP, global contagion). Sep-Nov 2008.",
    returns=_RETURNS_2008,
    duration_days=44,
    peak_drawdown=0.40,
    volatility_multiplier=4.0,
    category="historical",
)


# ---------------------------------------------------------------------------
# 2020 COVID-19 Crash (Feb 20 – Mar 23, 2020)
# S&P 500 dropped ~34% in 23 trading days.  Fastest bear market in history.
# Circuit breakers triggered multiple times.  Vol ~5x normal.
# ---------------------------------------------------------------------------
_RETURNS_COVID: Tuple[float, ...] = (
    -0.0328, -0.0295, -0.0410,  0.0456, -0.0227,  # week 1: initial shock
    -0.0332, -0.0498,  0.0431, -0.0368, -0.0107,  # week 2: circuit breakers
    -0.0954,  0.0493, -0.0943, -0.0530,  0.0583,  # week 3: panic selling
    -0.1198,  0.0562, -0.0494,  0.0072, -0.0419,  # week 4: bottom
    -0.0281,  0.0940, -0.0335,                     # week 5: partial recovery
)

COVID_CRASH_2020: StressScenarioPreset = StressScenarioPreset(
    name="2020_COVID_CRASH",
    description="COVID-19 market crash. Feb-Mar 2020. Fastest bear market in history.",
    returns=_RETURNS_COVID,
    duration_days=23,
    peak_drawdown=0.34,
    volatility_multiplier=5.0,
    category="historical",
)


# ---------------------------------------------------------------------------
# 2010 Flash Crash (May 6, 2010 + surrounding days)
# Intraday drop of ~9.2%, recovered to -3.2% by close.  Surrounding days
# showed elevated vol.  10 trading days modelled.  Vol ~3x.
# ---------------------------------------------------------------------------
_RETURNS_FLASH: Tuple[float, ...] = (
    -0.0082, -0.0142, -0.0147,  0.0020, -0.0110,  # pre-crash tension
    -0.0347,                                         # flash crash day (close-to-close)
     0.0136, -0.0043,  0.0074, -0.0036,             # recovery / aftershock
)

FLASH_CRASH_2010: StressScenarioPreset = StressScenarioPreset(
    name="2010_FLASH_CRASH",
    description="Flash Crash of May 6, 2010. Intraday -9.2%, close -3.5%. 10 trading days.",
    returns=_RETURNS_FLASH,
    duration_days=10,
    peak_drawdown=0.08,
    volatility_multiplier=3.0,
    category="historical",
)


# ---------------------------------------------------------------------------
# Dot-Com Bust (Mar 2000 – Oct 2002, worst 40-day phase)
# NASDAQ lost ~78% over 2.5 years.  S&P 500 lost ~49%.  Modelled as the
# worst 40-day stretch: grinding decline with weak rallies.  Vol ~2.5x.
# ---------------------------------------------------------------------------
_RETURNS_DOTCOM: Tuple[float, ...] = (
    -0.0180, -0.0095, -0.0200,  0.0072, -0.0155,  # week 1: tech sell-off
    -0.0230,  0.0045, -0.0175, -0.0110,  0.0090,  # week 2: Enron era
    -0.0310,  0.0065, -0.0245, -0.0120, -0.0085,  # week 3: accounting scandals
     0.0130, -0.0270, -0.0150,  0.0035, -0.0190,  # week 4: WorldCom
    -0.0140,  0.0055, -0.0205, -0.0170,  0.0080,  # week 5: broad sell-off
    -0.0260, -0.0100,  0.0110, -0.0185, -0.0095,  # week 6: capitulation starts
    -0.0220,  0.0040, -0.0165, -0.0210,  0.0060,  # week 7: near bottom
    -0.0250,  0.0075, -0.0135, -0.0180,  0.0105,  # week 8: bear market rally
)

DOTCOM_BUST_2000: StressScenarioPreset = StressScenarioPreset(
    name="DOTCOM_BUST_2000",
    description="Dot-Com bust worst phase (2000-2002). Grinding tech decline. 40 trading days.",
    returns=_RETURNS_DOTCOM,
    duration_days=40,
    peak_drawdown=0.35,
    volatility_multiplier=2.5,
    category="historical",
)


# ---------------------------------------------------------------------------
# Black Monday (Oct 19, 1987 + surrounding days)
# Single-day drop of -22.6%.  Preceded by a week of -10%.  Sharp partial
# recovery next day.  10 trading days.  Vol ~6x.
# ---------------------------------------------------------------------------
_RETURNS_BLACK_MONDAY: Tuple[float, ...] = (
    -0.0217, -0.0256, -0.0142,  0.0012, -0.0502,  # week before: pressure
    -0.2261,                                         # Black Monday (Oct 19)
     0.0533, -0.0849,  0.0417,  0.0258,             # recovery + aftershock
)

BLACK_MONDAY_1987: StressScenarioPreset = StressScenarioPreset(
    name="BLACK_MONDAY_1987",
    description="Black Monday, Oct 19, 1987. Single-day -22.6%. 10 trading days.",
    returns=_RETURNS_BLACK_MONDAY,
    duration_days=10,
    peak_drawdown=0.33,
    volatility_multiplier=6.0,
    category="historical",
)


# =============================================================================
# SECTION 3 -- SYNTHETIC PRESETS (DET-06: fixed literals)
# =============================================================================

# ---------------------------------------------------------------------------
# Synthetic Vol Shock 3x: 20 days at 3x normal volatility.
# Alternating large swings around zero (net drift ~ 0).
# ---------------------------------------------------------------------------
_RETURNS_VOL_SHOCK: Tuple[float, ...] = (
    -0.0350,  0.0380, -0.0420,  0.0290, -0.0510,
     0.0460, -0.0370,  0.0330, -0.0480,  0.0410,
    -0.0390,  0.0350, -0.0450,  0.0300, -0.0520,
     0.0470, -0.0340,  0.0310, -0.0400,  0.0360,
)

SYNTHETIC_VOL_SHOCK_3X: StressScenarioPreset = StressScenarioPreset(
    name="SYNTHETIC_VOL_SHOCK_3X",
    description="Synthetic 3x volatility shock. 20 days of extreme swings around zero.",
    returns=_RETURNS_VOL_SHOCK,
    duration_days=20,
    peak_drawdown=0.10,
    volatility_multiplier=3.0,
    category="synthetic",
)


# ---------------------------------------------------------------------------
# Synthetic Liquidity Crisis: 20 days with spread-induced negative drift.
# Models widening bid-ask spreads causing systematic slippage losses.
# ---------------------------------------------------------------------------
_RETURNS_LIQUIDITY: Tuple[float, ...] = (
    -0.0120, -0.0085, -0.0150, -0.0095, -0.0210,
    -0.0180, -0.0070, -0.0250, -0.0130, -0.0160,
    -0.0200, -0.0105, -0.0175, -0.0220, -0.0090,
    -0.0140, -0.0195, -0.0115, -0.0165, -0.0230,
)

SYNTHETIC_LIQUIDITY_CRISIS: StressScenarioPreset = StressScenarioPreset(
    name="SYNTHETIC_LIQUIDITY_CRISIS",
    description="Synthetic liquidity crisis. 20 days of spread-induced losses.",
    returns=_RETURNS_LIQUIDITY,
    duration_days=20,
    peak_drawdown=0.25,
    volatility_multiplier=2.0,
    category="synthetic",
)


# ---------------------------------------------------------------------------
# Synthetic Correlation Shock: 20 days where all assets move in lockstep
# downward (correlation → 0.95+).  Models diversification failure.
# ---------------------------------------------------------------------------
_RETURNS_CORR_SHOCK: Tuple[float, ...] = (
    -0.0220, -0.0185, -0.0260,  0.0040, -0.0310,
    -0.0195,  0.0025, -0.0275, -0.0150, -0.0240,
    -0.0200, -0.0170, -0.0290,  0.0035, -0.0265,
    -0.0210,  0.0015, -0.0235, -0.0180, -0.0255,
)

SYNTHETIC_CORRELATION_SHOCK: StressScenarioPreset = StressScenarioPreset(
    name="SYNTHETIC_CORRELATION_SHOCK",
    description="Synthetic correlation shock. All assets decline in lockstep. 20 days.",
    returns=_RETURNS_CORR_SHOCK,
    duration_days=20,
    peak_drawdown=0.30,
    volatility_multiplier=2.5,
    category="synthetic",
)


# =============================================================================
# SECTION 4 -- REGISTRY
# =============================================================================

SCENARIO_REGISTRY: Dict[str, StressScenarioPreset] = {
    FINANCIAL_CRISIS_2008.name: FINANCIAL_CRISIS_2008,
    COVID_CRASH_2020.name: COVID_CRASH_2020,
    FLASH_CRASH_2010.name: FLASH_CRASH_2010,
    DOTCOM_BUST_2000.name: DOTCOM_BUST_2000,
    BLACK_MONDAY_1987.name: BLACK_MONDAY_1987,
    SYNTHETIC_VOL_SHOCK_3X.name: SYNTHETIC_VOL_SHOCK_3X,
    SYNTHETIC_LIQUIDITY_CRISIS.name: SYNTHETIC_LIQUIDITY_CRISIS,
    SYNTHETIC_CORRELATION_SHOCK.name: SYNTHETIC_CORRELATION_SHOCK,
}


# =============================================================================
# SECTION 5 -- PUBLIC API
# =============================================================================

def get_scenario(name: str) -> StressScenarioPreset:
    """
    Retrieve a named stress scenario preset.

    Args:
        name: Scenario name (e.g. "2008_FINANCIAL_CRISIS").

    Returns:
        StressScenarioPreset for the requested scenario.

    Raises:
        TypeError:  If name is not a string.
        ValueError: If name is not found in the registry.
    """
    if not isinstance(name, str):
        raise TypeError(f"name must be a string, got {type(name).__name__}")
    if name not in SCENARIO_REGISTRY:
        available = ", ".join(sorted(SCENARIO_REGISTRY.keys()))
        raise ValueError(
            f"Unknown scenario '{name}'. Available: {available}"
        )
    return SCENARIO_REGISTRY[name]


def get_all_scenarios() -> Tuple[StressScenarioPreset, ...]:
    """Return all registered scenario presets as an immutable tuple."""
    return tuple(SCENARIO_REGISTRY.values())


def get_historical_scenarios() -> Tuple[StressScenarioPreset, ...]:
    """Return only historical scenario presets."""
    return tuple(s for s in SCENARIO_REGISTRY.values() if s.category == "historical")


def get_synthetic_scenarios() -> Tuple[StressScenarioPreset, ...]:
    """Return only synthetic scenario presets."""
    return tuple(s for s in SCENARIO_REGISTRY.values() if s.category == "synthetic")


def get_scenario_names() -> Tuple[str, ...]:
    """Return all registered scenario names."""
    return tuple(SCENARIO_REGISTRY.keys())
