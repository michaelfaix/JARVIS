# =============================================================================
# jarvis/core/data_structures.py -- Multi-Asset Data Structures (Phase 1)
#
# Market Microstructure, Session Structure, Trading Hours, Spread Model,
# Liquidity Profile, and Volatility Scaling for multi-asset support.
#
# Complements jarvis/core/data_layer.py (OHLCV, MarketData, EnhancedMarketData).
# These structures define PER-ASSET-CLASS characteristics.
#
# =============================================================================
# FAS COMPLIANCE DECLARATION
# =============================================================================
#
# Dependency matrix (binding):
#   data_structures.py -> (stdlib only, no internal imports)
#
# DETERMINISM GUARANTEES:
#   DET-01  No stochastic operations.
#   DET-02  All inputs passed explicitly.
#   DET-03  No side effects.
#   DET-04  All branches deterministic functions of explicit inputs.
#   DET-05  Same inputs -> same outputs.
#   DET-06  Fixed literals not parameterizable.
#
# PROHIBITED ACTIONS CONFIRMED ABSENT:
#   PROHIBITED-01  No random/Monte Carlo/sampling.
#   PROHIBITED-02  No file I/O.
#   PROHIBITED-03  No logging/print.
#   PROHIBITED-04  No environment variable access.
#   PROHIBITED-05  No global mutable state.
#   PROHIBITED-07  No runtime constant mutation.
#
# ASCII COMPLIANCE: All literals are 7-bit ASCII.
# =============================================================================

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, FrozenSet, List, Tuple


# =============================================================================
# SECTION 1 -- ASSET CLASS ENUM (canonical identifiers)
# =============================================================================

VALID_ASSET_CLASSES: FrozenSet[str] = frozenset({
    "crypto",
    "forex",
    "indices",
    "commodities",
    "rates",
})


# =============================================================================
# SECTION 2 -- VOLATILITY SCALING (DET-06: fixed literals)
# =============================================================================

# FAS Section 3 / Fehler 5: normalize_volatility()
# Scaling factors for cross-asset volatility normalization.
# Crypto is baseline (1.0). FX is 3x less volatile, etc.
VOLATILITY_SCALING: Dict[str, float] = {
    "crypto":      1.0,
    "forex":       0.3,
    "indices":     0.6,
    "commodities": 0.8,
    "rates":       0.25,
}


# =============================================================================
# SECTION 3 -- TRADING HOURS
# =============================================================================

@dataclass(frozen=True)
class TradingHours:
    """Trading hours specification for an asset class.

    Attributes:
        mode: One of '24/7', '24/5', 'session'.
              - '24/7': Always open (crypto).
              - '24/5': Open Mon-Fri, closed weekends (forex).
              - 'session': Defined session windows (indices, commodities).
        has_gaps: Whether overnight/weekend gaps are expected.
    """

    mode: str       # "24/7" | "24/5" | "session"
    has_gaps: bool   # True for session-based markets

    def __post_init__(self) -> None:
        valid_modes = ("24/7", "24/5", "session")
        if self.mode not in valid_modes:
            raise ValueError(
                f"Invalid trading hours mode: '{self.mode}'. "
                f"Must be one of {valid_modes}."
            )


# =============================================================================
# SECTION 4 -- SESSION DEFINITION
# =============================================================================

@dataclass(frozen=True)
class SessionDefinition:
    """A single trading session window.

    Times are in UTC, represented as 'HH:MM' strings.
    Liquidity classification: 'high', 'normal', 'low'.

    Attributes:
        name: Session identifier (e.g., 'asia', 'europe', 'us').
        start_utc: Session start time in UTC ('HH:MM').
        end_utc: Session end time in UTC ('HH:MM').
        liquidity: Expected liquidity level.
    """

    name: str
    start_utc: str    # "HH:MM" format, UTC
    end_utc: str      # "HH:MM" format, UTC
    liquidity: str    # "high" | "normal" | "low"

    def __post_init__(self) -> None:
        valid_liquidity = ("high", "normal", "low")
        if self.liquidity not in valid_liquidity:
            raise ValueError(
                f"Invalid liquidity level: '{self.liquidity}'. "
                f"Must be one of {valid_liquidity}."
            )
        # Validate time format
        for label, val in [("start_utc", self.start_utc), ("end_utc", self.end_utc)]:
            parts = val.split(":")
            if len(parts) != 2:
                raise ValueError(f"Invalid time format for {label}: '{val}'. Use 'HH:MM'.")
            try:
                hh, mm = int(parts[0]), int(parts[1])
            except ValueError:
                raise ValueError(f"Invalid time format for {label}: '{val}'. Use 'HH:MM'.")
            if not (0 <= hh <= 23 and 0 <= mm <= 59):
                raise ValueError(f"Invalid time value for {label}: '{val}'.")


# =============================================================================
# SECTION 5 -- SESSION STRUCTURE
# =============================================================================

@dataclass(frozen=True)
class SessionStructure:
    """Complete session structure for an asset class.

    Attributes:
        sessions: Tuple of SessionDefinition objects (ordered by start time).
    """

    sessions: Tuple[SessionDefinition, ...]

    def __post_init__(self) -> None:
        if not isinstance(self.sessions, tuple):
            raise TypeError("sessions must be a tuple of SessionDefinition.")
        for s in self.sessions:
            if not isinstance(s, SessionDefinition):
                raise TypeError(
                    f"Each session must be a SessionDefinition, got {type(s).__name__}."
                )

    def get_session_names(self) -> List[str]:
        """Return ordered list of session names."""
        return [s.name for s in self.sessions]


# =============================================================================
# SECTION 6 -- SPREAD MODEL
# =============================================================================

@dataclass(frozen=True)
class SpreadModel:
    """Spread characteristics for an asset class.

    Attributes:
        typical_spread_bps: Typical bid-ask spread in basis points.
        session_multipliers: Multiplier per session (e.g., Asia=1.5 for wider spreads).
                             Empty dict if not session-dependent.
    """

    typical_spread_bps: float
    session_multipliers: Tuple[Tuple[str, float], ...]  # ((session_name, multiplier), ...)

    def __post_init__(self) -> None:
        if self.typical_spread_bps < 0:
            raise ValueError(
                f"typical_spread_bps must be >= 0, got {self.typical_spread_bps}."
            )

    def get_spread_bps(self, session_name: str = "") -> float:
        """Get spread for a specific session, falling back to typical."""
        for name, mult in self.session_multipliers:
            if name == session_name:
                return self.typical_spread_bps * mult
        return self.typical_spread_bps


# =============================================================================
# SECTION 7 -- LIQUIDITY PROFILE
# =============================================================================

@dataclass(frozen=True)
class LiquidityProfile:
    """Liquidity characteristics for an asset class.

    Attributes:
        base_liquidity: Baseline liquidity level ('high', 'normal', 'low').
        session_dependent: Whether liquidity varies by session.
        quality_minimum: Minimum quality score for liquidity acceptance.
    """

    base_liquidity: str    # "high" | "normal" | "low"
    session_dependent: bool
    quality_minimum: float  # [0.0, 1.0]

    def __post_init__(self) -> None:
        valid = ("high", "normal", "low")
        if self.base_liquidity not in valid:
            raise ValueError(
                f"Invalid base_liquidity: '{self.base_liquidity}'. Must be one of {valid}."
            )
        if not (0.0 <= self.quality_minimum <= 1.0):
            raise ValueError(
                f"quality_minimum must be in [0.0, 1.0], got {self.quality_minimum}."
            )


# =============================================================================
# SECTION 8 -- MARKET MICROSTRUCTURE (per asset class)
# =============================================================================

@dataclass(frozen=True)
class MarketMicrostructure:
    """Complete market microstructure definition for one asset class.

    This is the central configuration object for multi-asset support.
    Each asset class (crypto, forex, indices, commodities, rates) has
    one MarketMicrostructure instance describing its characteristics.

    FAS Section 6: Configuration per asset class.

    Attributes:
        asset_class: Canonical asset class identifier.
        trading_hours: Trading hours specification.
        gap_detection: Whether gap detection is enabled.
        typical_spread_bps: Typical spread in basis points.
        volatility_scaling: Volatility normalization factor.
        ood_threshold: OOD detection base threshold.
        margin_requirement: Required margin fraction.
        session_structure: Optional session definitions.
        spread_model: Spread model with session adjustments.
        liquidity_profile: Liquidity characteristics.
        specific_features: Tuple of asset-specific feature names.
    """

    asset_class: str
    trading_hours: TradingHours
    gap_detection: bool
    typical_spread_bps: float
    volatility_scaling: float
    ood_threshold: float
    margin_requirement: float
    session_structure: SessionStructure  # empty sessions tuple for 24/7 markets
    spread_model: SpreadModel
    liquidity_profile: LiquidityProfile
    specific_features: Tuple[str, ...]

    def __post_init__(self) -> None:
        if self.asset_class not in VALID_ASSET_CLASSES:
            raise ValueError(
                f"Invalid asset_class: '{self.asset_class}'. "
                f"Must be one of {sorted(VALID_ASSET_CLASSES)}."
            )
        if self.volatility_scaling <= 0:
            raise ValueError(
                f"volatility_scaling must be > 0, got {self.volatility_scaling}."
            )
        if not (0.0 <= self.ood_threshold <= 1.0):
            raise ValueError(
                f"ood_threshold must be in [0.0, 1.0], got {self.ood_threshold}."
            )
        if self.margin_requirement <= 0:
            raise ValueError(
                f"margin_requirement must be > 0, got {self.margin_requirement}."
            )
        if self.typical_spread_bps < 0:
            raise ValueError(
                f"typical_spread_bps must be >= 0, got {self.typical_spread_bps}."
            )


# =============================================================================
# SECTION 9 -- VOLATILITY NORMALIZATION (DET-06)
# =============================================================================

def normalize_volatility(vol: float, asset_class: str) -> float:
    """Normalize volatility to comparable cross-asset scale.

    FAS Section 3 / Fehler 5: Different assets have different baselines.
    Crypto 5% daily vol = normal. FX 5% daily vol = crisis.

    Args:
        vol: Raw volatility value.
        asset_class: Canonical asset class identifier.

    Returns:
        Normalized volatility.

    Raises:
        ValueError: If asset_class is not recognized.
    """
    if asset_class not in VOLATILITY_SCALING:
        raise ValueError(
            f"Unknown asset_class for volatility scaling: '{asset_class}'. "
            f"Must be one of {sorted(VOLATILITY_SCALING.keys())}."
        )
    scaling = VOLATILITY_SCALING[asset_class]
    if scaling == 0:
        raise ValueError("Volatility scaling factor must not be zero.")
    return vol / scaling


# =============================================================================
# SECTION 10 -- CANONICAL MICROSTRUCTURE CONFIGS (DET-06: fixed literals)
# =============================================================================

# FAS Section 6: Asset Configuration (config/assets.yaml translated to code)
# These are the canonical microstructure definitions per asset class.

CRYPTO_MICROSTRUCTURE = MarketMicrostructure(
    asset_class="crypto",
    trading_hours=TradingHours(mode="24/7", has_gaps=False),
    gap_detection=False,
    typical_spread_bps=10.0,
    volatility_scaling=1.0,
    ood_threshold=0.7,
    margin_requirement=0.05,
    session_structure=SessionStructure(sessions=()),
    spread_model=SpreadModel(typical_spread_bps=10.0, session_multipliers=()),
    liquidity_profile=LiquidityProfile(
        base_liquidity="normal",
        session_dependent=False,
        quality_minimum=0.6,
    ),
    specific_features=(
        "funding_rate",
        "open_interest",
        "liquidations",
        "orderbook_imbalance",
    ),
)

FOREX_SESSIONS = SessionStructure(
    sessions=(
        SessionDefinition(name="asia", start_utc="00:00", end_utc="09:00", liquidity="low"),
        SessionDefinition(name="europe", start_utc="08:00", end_utc="17:00", liquidity="high"),
        SessionDefinition(name="us", start_utc="13:00", end_utc="22:00", liquidity="high"),
    )
)

FOREX_MICROSTRUCTURE = MarketMicrostructure(
    asset_class="forex",
    trading_hours=TradingHours(mode="24/5", has_gaps=False),
    gap_detection=False,
    typical_spread_bps=1.0,
    volatility_scaling=0.3,
    ood_threshold=0.5,
    margin_requirement=0.01,
    session_structure=FOREX_SESSIONS,
    spread_model=SpreadModel(
        typical_spread_bps=1.0,
        session_multipliers=(
            ("asia", 1.5),
            ("europe", 1.0),
            ("us", 1.0),
        ),
    ),
    liquidity_profile=LiquidityProfile(
        base_liquidity="high",
        session_dependent=True,
        quality_minimum=0.6,
    ),
    specific_features=(
        "rate_differential",
        "dxy_correlation",
        "carry_signal",
        "cb_meeting_proximity",
    ),
)

INDICES_SESSIONS = SessionStructure(
    sessions=(
        SessionDefinition(name="pre_market", start_utc="04:00", end_utc="09:30", liquidity="low"),
        SessionDefinition(name="regular", start_utc="09:30", end_utc="16:00", liquidity="high"),
        SessionDefinition(name="post_market", start_utc="16:00", end_utc="20:00", liquidity="low"),
    )
)

INDICES_MICROSTRUCTURE = MarketMicrostructure(
    asset_class="indices",
    trading_hours=TradingHours(mode="session", has_gaps=True),
    gap_detection=True,
    typical_spread_bps=5.0,
    volatility_scaling=0.6,
    ood_threshold=0.6,
    margin_requirement=0.05,
    session_structure=INDICES_SESSIONS,
    spread_model=SpreadModel(
        typical_spread_bps=5.0,
        session_multipliers=(
            ("pre_market", 2.0),
            ("regular", 1.0),
            ("post_market", 1.8),
        ),
    ),
    liquidity_profile=LiquidityProfile(
        base_liquidity="high",
        session_dependent=True,
        quality_minimum=0.6,
    ),
    specific_features=(
        "vix_level",
        "vix_term_structure",
        "put_call_ratio",
        "credit_spread",
        "sector_rotation",
    ),
)

COMMODITIES_MICROSTRUCTURE = MarketMicrostructure(
    asset_class="commodities",
    trading_hours=TradingHours(mode="session", has_gaps=True),
    gap_detection=True,
    typical_spread_bps=8.0,
    volatility_scaling=0.8,
    ood_threshold=0.6,
    margin_requirement=0.05,
    session_structure=SessionStructure(
        sessions=(
            SessionDefinition(name="regular", start_utc="08:00", end_utc="17:00", liquidity="high"),
        )
    ),
    spread_model=SpreadModel(
        typical_spread_bps=8.0,
        session_multipliers=(
            ("regular", 1.0),
        ),
    ),
    liquidity_profile=LiquidityProfile(
        base_liquidity="normal",
        session_dependent=True,
        quality_minimum=0.6,
    ),
    specific_features=(
        "contango_backwardation",
        "inventory_levels",
        "seasonal_pattern",
    ),
)

RATES_MICROSTRUCTURE = MarketMicrostructure(
    asset_class="rates",
    trading_hours=TradingHours(mode="session", has_gaps=True),
    gap_detection=True,
    typical_spread_bps=0.5,
    volatility_scaling=0.25,
    ood_threshold=0.5,
    margin_requirement=0.02,
    session_structure=SessionStructure(
        sessions=(
            SessionDefinition(name="regular", start_utc="07:00", end_utc="17:00", liquidity="high"),
        )
    ),
    spread_model=SpreadModel(
        typical_spread_bps=0.5,
        session_multipliers=(
            ("regular", 1.0),
        ),
    ),
    liquidity_profile=LiquidityProfile(
        base_liquidity="high",
        session_dependent=False,
        quality_minimum=0.6,
    ),
    specific_features=(
        "yield_curve_slope",
        "term_premium",
        "central_bank_rate",
    ),
)


# =============================================================================
# SECTION 11 -- MICROSTRUCTURE REGISTRY
# =============================================================================

# Canonical lookup: asset_class -> MarketMicrostructure
MICROSTRUCTURE_REGISTRY: Dict[str, MarketMicrostructure] = {
    "crypto":      CRYPTO_MICROSTRUCTURE,
    "forex":       FOREX_MICROSTRUCTURE,
    "indices":     INDICES_MICROSTRUCTURE,
    "commodities": COMMODITIES_MICROSTRUCTURE,
    "rates":       RATES_MICROSTRUCTURE,
}


def get_microstructure(asset_class: str) -> MarketMicrostructure:
    """Retrieve canonical MarketMicrostructure for an asset class.

    Args:
        asset_class: Canonical asset class identifier.

    Returns:
        MarketMicrostructure for the given asset class.

    Raises:
        ValueError: If asset_class is not recognized.
    """
    if asset_class not in MICROSTRUCTURE_REGISTRY:
        raise ValueError(
            f"Unknown asset_class: '{asset_class}'. "
            f"Must be one of {sorted(MICROSTRUCTURE_REGISTRY.keys())}."
        )
    return MICROSTRUCTURE_REGISTRY[asset_class]
