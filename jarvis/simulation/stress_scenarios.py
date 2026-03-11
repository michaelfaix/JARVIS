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
# Regime-aware stress testing:
#   RegimeAwareScenario pairs a StressScenarioPreset with a per-day
#   GlobalRegimeState sequence.  run_regime_aware_stress_test() rolls
#   through the scenario using the per-day regime instead of a static one.
#
# DETERMINISM:
#   DET-01  No stochastic operations.
#   DET-02  All inputs passed explicitly; presets are module-level constants.
#   DET-03  No side effects.
#   DET-06  All return arrays and regime sequences are fixed literals.
#   DET-07  Same inputs = identical output.
#
# PROHIBITED: logging, random, file IO, network IO, datetime.now()
#
# DEPENDENCIES:
#   stdlib:   dataclasses, typing
#   internal: jarvis.core.regime (GlobalRegimeState) — Enum only, no logic
#             jarvis.orchestrator (run_full_pipeline) — delegated backtest logic
#   external: NONE (pure Python)
# =============================================================================

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List, Optional, Sequence, Tuple

from jarvis.core.regime import GlobalRegimeState


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


# =============================================================================
# SECTION 6 -- REGIME-AWARE STRESS SCENARIOS
# =============================================================================

@dataclass(frozen=True)
class RegimeAwareScenario:
    """
    Pairs a StressScenarioPreset with a per-day regime sequence.

    The regime_sequence tuple has the same length as preset.returns.
    Each entry is the GlobalRegimeState active on that trading day.

    Fields:
        preset:          The underlying StressScenarioPreset.
        regime_sequence: Per-day GlobalRegimeState, len == len(preset.returns).
    """
    preset: StressScenarioPreset
    regime_sequence: Tuple[GlobalRegimeState, ...]


@dataclass(frozen=True)
class RegimeAwareStressResult:
    """
    Result of run_regime_aware_stress_test().

    Fields:
        scenario_name:   Name of the stress scenario.
        equity_curve:    Equity values per timestep after the lookback window.
        regime_sequence: The regime sequence used (same as input).
        peak_drawdown:   Peak-to-trough drawdown from the equity curve.
        final_equity:    Last equity value.
        n_regime_changes: Number of regime transitions in the sequence.
    """
    scenario_name: str
    equity_curve: Tuple[float, ...]
    regime_sequence: Tuple[GlobalRegimeState, ...]
    peak_drawdown: float
    final_equity: float
    n_regime_changes: int


# =============================================================================
# SECTION 7 -- REGIME SEQUENCES (DET-06: fixed literals)
# =============================================================================
#
# Each sequence models the regime evolution during the crisis.
# Length must exactly match the corresponding preset's duration_days.

_RS = GlobalRegimeState

# 2008 Financial Crisis: 44 days
# RISK_ON (5d) -> RISK_OFF (10d) -> CRISIS (19d) -> RISK_OFF (10d)
_REGIME_2008: Tuple[GlobalRegimeState, ...] = (
    _RS.RISK_ON,  _RS.RISK_ON,  _RS.RISK_ON,  _RS.RISK_ON,  _RS.RISK_ON,     # w1
    _RS.RISK_OFF, _RS.RISK_OFF, _RS.RISK_OFF, _RS.RISK_OFF, _RS.RISK_OFF,     # w2
    _RS.RISK_OFF, _RS.RISK_OFF, _RS.RISK_OFF, _RS.RISK_OFF, _RS.RISK_OFF,     # w3
    _RS.CRISIS,   _RS.CRISIS,   _RS.CRISIS,   _RS.CRISIS,   _RS.CRISIS,       # w4
    _RS.CRISIS,   _RS.CRISIS,   _RS.CRISIS,   _RS.CRISIS,   _RS.CRISIS,       # w5
    _RS.CRISIS,   _RS.CRISIS,   _RS.CRISIS,   _RS.CRISIS,   _RS.CRISIS,       # w6
    _RS.CRISIS,   _RS.CRISIS,   _RS.CRISIS,   _RS.CRISIS,   _RS.RISK_OFF,     # w7
    _RS.RISK_OFF, _RS.RISK_OFF, _RS.RISK_OFF, _RS.RISK_OFF, _RS.RISK_OFF,     # w8
    _RS.RISK_OFF, _RS.RISK_OFF, _RS.RISK_OFF, _RS.RISK_OFF,                   # w9
)

# 2020 COVID Crash: 23 days
# RISK_ON (3d) -> RISK_OFF (5d) -> CRISIS (10d) -> RISK_OFF (5d)
_REGIME_COVID: Tuple[GlobalRegimeState, ...] = (
    _RS.RISK_ON,  _RS.RISK_ON,  _RS.RISK_ON,                                   # initial
    _RS.RISK_OFF, _RS.RISK_OFF, _RS.RISK_OFF, _RS.RISK_OFF, _RS.RISK_OFF,     # circuit brk
    _RS.CRISIS,   _RS.CRISIS,   _RS.CRISIS,   _RS.CRISIS,   _RS.CRISIS,       # panic
    _RS.CRISIS,   _RS.CRISIS,   _RS.CRISIS,   _RS.CRISIS,   _RS.CRISIS,       # bottom
    _RS.RISK_OFF, _RS.RISK_OFF, _RS.RISK_OFF, _RS.RISK_OFF, _RS.RISK_OFF,     # recovery
)

# 2010 Flash Crash: 10 days
# RISK_ON (4d) -> CRISIS (1d) -> RISK_OFF (3d) -> RISK_ON (2d)
_REGIME_FLASH: Tuple[GlobalRegimeState, ...] = (
    _RS.RISK_ON,  _RS.RISK_ON,  _RS.RISK_ON,  _RS.RISK_ON,                    # pre-crash
    _RS.RISK_OFF,                                                               # tension
    _RS.CRISIS,                                                                 # flash crash
    _RS.RISK_OFF, _RS.RISK_OFF, _RS.RISK_OFF,                                 # aftershock
    _RS.RISK_ON,                                                                # recovery
)

# Dot-Com Bust: 40 days
# RISK_OFF (10d) -> CRISIS (15d) -> RISK_OFF (10d) -> TRANSITION (5d)
_REGIME_DOTCOM: Tuple[GlobalRegimeState, ...] = (
    _RS.RISK_OFF, _RS.RISK_OFF, _RS.RISK_OFF, _RS.RISK_OFF, _RS.RISK_OFF,    # w1
    _RS.RISK_OFF, _RS.RISK_OFF, _RS.RISK_OFF, _RS.RISK_OFF, _RS.RISK_OFF,    # w2
    _RS.CRISIS,   _RS.CRISIS,   _RS.CRISIS,   _RS.CRISIS,   _RS.CRISIS,      # w3
    _RS.CRISIS,   _RS.CRISIS,   _RS.CRISIS,   _RS.CRISIS,   _RS.CRISIS,      # w4
    _RS.CRISIS,   _RS.CRISIS,   _RS.CRISIS,   _RS.CRISIS,   _RS.CRISIS,      # w5
    _RS.RISK_OFF, _RS.RISK_OFF, _RS.RISK_OFF, _RS.RISK_OFF, _RS.RISK_OFF,    # w6
    _RS.RISK_OFF, _RS.RISK_OFF, _RS.RISK_OFF, _RS.RISK_OFF, _RS.RISK_OFF,    # w7
    _RS.TRANSITION, _RS.TRANSITION, _RS.TRANSITION, _RS.TRANSITION, _RS.TRANSITION,  # w8
)

# Black Monday: 10 days
# RISK_ON (4d) -> RISK_OFF (1d) -> CRISIS (1d) -> RISK_OFF (2d) -> RISK_ON (2d)
_REGIME_BLACK_MONDAY: Tuple[GlobalRegimeState, ...] = (
    _RS.RISK_ON,  _RS.RISK_ON,  _RS.RISK_ON,  _RS.RISK_ON,                    # pre-crash
    _RS.RISK_OFF,                                                               # selling
    _RS.CRISIS,                                                                 # Black Monday
    _RS.RISK_OFF, _RS.RISK_OFF,                                                # aftershock
    _RS.RISK_ON,  _RS.RISK_ON,                                                 # recovery
)

# Synthetic Vol Shock: 20 days — RISK_OFF throughout
_REGIME_VOL_SHOCK: Tuple[GlobalRegimeState, ...] = tuple(
    _RS.RISK_OFF for _ in range(20)
)

# Synthetic Liquidity Crisis: 20 days — CRISIS throughout
_REGIME_LIQUIDITY: Tuple[GlobalRegimeState, ...] = tuple(
    _RS.CRISIS for _ in range(20)
)

# Synthetic Correlation Shock: 20 days — CRISIS throughout
_REGIME_CORR_SHOCK: Tuple[GlobalRegimeState, ...] = tuple(
    _RS.CRISIS for _ in range(20)
)


# =============================================================================
# SECTION 8 -- REGIME-AWARE SCENARIO PRESETS
# =============================================================================

REGIME_AWARE_2008 = RegimeAwareScenario(
    preset=FINANCIAL_CRISIS_2008,
    regime_sequence=_REGIME_2008,
)

REGIME_AWARE_COVID = RegimeAwareScenario(
    preset=COVID_CRASH_2020,
    regime_sequence=_REGIME_COVID,
)

REGIME_AWARE_FLASH = RegimeAwareScenario(
    preset=FLASH_CRASH_2010,
    regime_sequence=_REGIME_FLASH,
)

REGIME_AWARE_DOTCOM = RegimeAwareScenario(
    preset=DOTCOM_BUST_2000,
    regime_sequence=_REGIME_DOTCOM,
)

REGIME_AWARE_BLACK_MONDAY = RegimeAwareScenario(
    preset=BLACK_MONDAY_1987,
    regime_sequence=_REGIME_BLACK_MONDAY,
)

REGIME_AWARE_VOL_SHOCK = RegimeAwareScenario(
    preset=SYNTHETIC_VOL_SHOCK_3X,
    regime_sequence=_REGIME_VOL_SHOCK,
)

REGIME_AWARE_LIQUIDITY = RegimeAwareScenario(
    preset=SYNTHETIC_LIQUIDITY_CRISIS,
    regime_sequence=_REGIME_LIQUIDITY,
)

REGIME_AWARE_CORR_SHOCK = RegimeAwareScenario(
    preset=SYNTHETIC_CORRELATION_SHOCK,
    regime_sequence=_REGIME_CORR_SHOCK,
)

REGIME_AWARE_REGISTRY: Dict[str, RegimeAwareScenario] = {
    FINANCIAL_CRISIS_2008.name: REGIME_AWARE_2008,
    COVID_CRASH_2020.name: REGIME_AWARE_COVID,
    FLASH_CRASH_2010.name: REGIME_AWARE_FLASH,
    DOTCOM_BUST_2000.name: REGIME_AWARE_DOTCOM,
    BLACK_MONDAY_1987.name: REGIME_AWARE_BLACK_MONDAY,
    SYNTHETIC_VOL_SHOCK_3X.name: REGIME_AWARE_VOL_SHOCK,
    SYNTHETIC_LIQUIDITY_CRISIS.name: REGIME_AWARE_LIQUIDITY,
    SYNTHETIC_CORRELATION_SHOCK.name: REGIME_AWARE_CORR_SHOCK,
}


def get_regime_aware_scenario(name: str) -> RegimeAwareScenario:
    """
    Retrieve a regime-aware stress scenario by name.

    Args:
        name: Scenario name (e.g. "2008_FINANCIAL_CRISIS").

    Returns:
        RegimeAwareScenario for the requested scenario.

    Raises:
        TypeError:  If name is not a string.
        ValueError: If name is not found in the regime-aware registry.
    """
    if not isinstance(name, str):
        raise TypeError(f"name must be a string, got {type(name).__name__}")
    if name not in REGIME_AWARE_REGISTRY:
        available = ", ".join(sorted(REGIME_AWARE_REGISTRY.keys()))
        raise ValueError(
            f"Unknown regime-aware scenario '{name}'. Available: {available}"
        )
    return REGIME_AWARE_REGISTRY[name]


# =============================================================================
# SECTION 9 -- REGIME-AWARE STRESS TEST ENGINE
# =============================================================================

_SYNTHETIC_SYMBOL: str = "ASSET"
_MIN_WINDOW: int = 20
_EQUITY_FLOOR: float = 1e-10


def _count_regime_changes(seq: Sequence[GlobalRegimeState]) -> int:
    """Count the number of regime transitions in a sequence."""
    count = 0
    for i in range(1, len(seq)):
        if seq[i] != seq[i - 1]:
            count += 1
    return count


def _compute_peak_drawdown(equity_curve: Sequence[float]) -> float:
    """Compute peak-to-trough drawdown from an equity curve."""
    if len(equity_curve) < 2:
        return 0.0
    peak = equity_curve[0]
    max_dd = 0.0
    for v in equity_curve:
        if v > peak:
            peak = v
        if peak > 0.0:
            dd = (peak - v) / peak
            if dd > max_dd:
                max_dd = dd
    return max_dd


def run_regime_aware_stress_test(
    scenario: RegimeAwareScenario,
    *,
    window: int = 20,
    initial_capital: float = 100_000.0,
    meta_uncertainty: float = 0.3,
    asset_price_start: float = 100.0,
) -> RegimeAwareStressResult:
    """
    Run a single-asset backtest using per-day regime from the scenario.

    Delegates all risk/allocation logic to run_full_pipeline() — no
    risk formulas reimplemented here (PROHIBITED-06).

    For each timestep t >= window:
      1. Slices scenario returns[t-window : t] as lookback.
      2. Uses regime_sequence[t] as the current regime.
      3. Calls run_full_pipeline() to obtain position size.
      4. Updates equity: equity * (1 + return[t] * position_size).

    Args:
        scenario: RegimeAwareScenario with preset and regime_sequence.
        window: Lookback window size (>= 20, RiskEngine minimum).
        initial_capital: Starting equity (> 0).
        meta_uncertainty: Meta-uncertainty in [0.0, 1.0].
        asset_price_start: Starting asset price for synthetic price series.

    Returns:
        RegimeAwareStressResult with equity curve and metrics.

    Raises:
        TypeError:  If scenario is not a RegimeAwareScenario.
        ValueError: If window < 20, initial_capital <= 0,
                    or regime_sequence length != returns length.
    """
    from jarvis.orchestrator import run_full_pipeline

    if not isinstance(scenario, RegimeAwareScenario):
        raise TypeError(
            f"scenario must be a RegimeAwareScenario, "
            f"got {type(scenario).__name__}"
        )
    if window < _MIN_WINDOW:
        raise ValueError(f"window must be >= {_MIN_WINDOW}, got {window}")
    if initial_capital <= 0.0:
        raise ValueError(
            f"initial_capital must be > 0, got {initial_capital}"
        )
    if meta_uncertainty < 0.0 or meta_uncertainty > 1.0:
        raise ValueError(
            f"meta_uncertainty must be in [0.0, 1.0], got {meta_uncertainty}"
        )
    if asset_price_start <= 0.0:
        raise ValueError(
            f"asset_price_start must be > 0, got {asset_price_start}"
        )

    returns = scenario.preset.returns
    regimes = scenario.regime_sequence

    if len(regimes) != len(returns):
        raise ValueError(
            f"regime_sequence length ({len(regimes)}) must equal "
            f"returns length ({len(returns)})"
        )

    # Build deterministic price series from returns
    prices: List[float] = [asset_price_start]
    for r in returns[:-1]:
        prices.append(prices[-1] * (1.0 + r))

    n = len(returns)
    equity = initial_capital
    equity_values: List[float] = []

    for t in range(window, n):
        window_returns = list(returns[t - window: t])
        current_regime = regimes[t]
        current_price = prices[t] if t < len(prices) else prices[-1]

        positions = run_full_pipeline(
            returns_history=window_returns,
            current_regime=current_regime,
            meta_uncertainty=meta_uncertainty,
            total_capital=equity,
            asset_prices={_SYNTHETIC_SYMBOL: current_price},
        )

        position_size = positions[_SYNTHETIC_SYMBOL]
        updated_equity = equity * (1.0 + returns[t] * position_size)
        equity = max(_EQUITY_FLOOR, updated_equity)
        equity_values.append(equity)

    eq_tuple = tuple(equity_values)
    peak_dd = _compute_peak_drawdown(equity_values)
    final_eq = equity_values[-1] if equity_values else initial_capital

    return RegimeAwareStressResult(
        scenario_name=scenario.preset.name,
        equity_curve=eq_tuple,
        regime_sequence=regimes,
        peak_drawdown=round(peak_dd, 10),
        final_equity=final_eq,
        n_regime_changes=_count_regime_changes(regimes),
    )
