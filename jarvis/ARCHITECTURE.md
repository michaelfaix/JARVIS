JARVIS ARCHITECTURE SPECIFICATION
FAS v6.1.0
===========================================================================

SECTION 1 -- LAYER STRUCTURE
===========================================================================

The JARVIS system is organized into two categories of layers: Stable Core
Layers and External Orchestration Layers.

STABLE CORE LAYERS
These layers contain canonical logic that must not be reimplemented,
extended, or modified without a signed release and version bump:

  jarvis/core/
    Single authoritative source for all regime enum definitions and the
    canonical regime transmission object. No other module may define
    regime types.

  jarvis/risk/
    Single authoritative source for the RiskEngine and all risk
    assessment arithmetic. Contains THRESHOLD_MANIFEST.json which
    hash-protects all numeric constants.

  jarvis/utils/
    Single authoritative source for all hash-protected numeric constants.
    Constants are declared once and imported everywhere. No constant may
    be redeclared or shadowed in any other module.

  jarvis/portfolio/
    Single authoritative source for portfolio allocation logic.
    allocate_positions() is the canonical allocation function.
    No other module may reimplement allocation arithmetic.

  jarvis/execution/
    Single authoritative source for the boundary adapter between risk
    exposure output and portfolio allocation.
    route_exposure_to_positions() is the canonical routing function.
    No other module may reimplement routing logic.

EXTERNAL ORCHESTRATION LAYERS
These layers may call into stable core layers but must never reimplement
any logic owned by those layers:

  jarvis/orchestrator/
    Connects RiskEngine.assess() -> exposure_weight ->
    route_exposure_to_positions() -> final positions.
    Pure delegation. No arithmetic. No regime logic.

  jarvis/backtest/
    Rolls a sliding window over time series data and delegates each
    timestep to run_full_pipeline(). Manages equity curve accumulation
    only. No risk logic. No allocation logic.

  jarvis/walkforward/
    Reserved for walk-forward validation over backtest segments.
    Must delegate entirely to jarvis/backtest/ and jarvis/orchestrator/.
    No risk logic. No allocation logic.


SECTION 2 -- IMPORT RULES
===========================================================================

The following directed import rules are enforced. An arrow A -> B means
module A is permitted to import from module B.

  jarvis/orchestrator/   -> jarvis/core/
  jarvis/orchestrator/   -> jarvis/risk/
  jarvis/orchestrator/   -> jarvis/execution/

  jarvis/backtest/       -> jarvis/core/
  jarvis/backtest/       -> jarvis/orchestrator/

  jarvis/walkforward/    -> jarvis/core/
  jarvis/walkforward/    -> jarvis/backtest/
  jarvis/walkforward/    -> jarvis/orchestrator/

  jarvis/execution/      -> jarvis/core/
  jarvis/execution/      -> jarvis/portfolio/

  jarvis/portfolio/      -> (standard library only)

  jarvis/risk/           -> jarvis/core/
  jarvis/risk/           -> jarvis/utils/

  jarvis/utils/          -> jarvis/core/

  jarvis/core/           -> (standard library only)

PROHIBITED IMPORT DIRECTIONS

  Stable core layers must never import from external orchestration layers.
  jarvis/core/       must never import from orchestrator/, backtest/, walkforward/
  jarvis/risk/       must never import from orchestrator/, backtest/, walkforward/
  jarvis/utils/      must never import from orchestrator/, backtest/, walkforward/
  jarvis/portfolio/  must never import from orchestrator/, backtest/, walkforward/
  jarvis/execution/  must never import from orchestrator/, backtest/, walkforward/

  Circular imports are prohibited in all cases without exception.

  No module outside jarvis/core/ may define, shadow, or alias any enum
  or type that is defined in jarvis/core/regime.py.

  No module outside jarvis/utils/ may declare a numeric constant that
  duplicates or shadows a constant registered in THRESHOLD_MANIFEST.json.


SECTION 3 -- DETERMINISM GUARANTEES
===========================================================================

All modules in the JARVIS system must satisfy the following determinism
guarantees without exception:

  DET-01  No stochastic operations anywhere in the system.
          No calls to random(), numpy.random, secrets, os.urandom, or
          any other source of non-deterministic values.

  DET-02  No external state reads inside any computational function.
          All inputs must be passed explicitly as function parameters.
          No function may read from module-level mutable variables,
          class-level mutable variables, or any shared mutable container
          during execution.

  DET-03  No side effects. Computational functions must not write to any
          external state, mutate any input argument, modify any module-level
          variable, or produce any observable effect beyond their return value.

  DET-04  All arithmetic operations are deterministic floating-point.
          No symbolic math, no lazy evaluation, no deferred computation.

  DET-05  All conditional branches are deterministic functions of their
          explicit inputs. No branch may depend on time, process ID,
          thread state, or any other implicit environmental value.

  DET-06  Fixed literals used as algorithm parameters must not be
          parameterised, overridden, or made configurable at runtime.
          They are part of the algorithm specification.

  DET-07  Backward compatibility is deterministic. For any call site that
          passes the same inputs as a prior version, the output must be
          bit-identical to that prior version unless a version bump with
          migration documentation has been issued.


SECTION 4 -- PROHIBITED ACTIONS
===========================================================================

The following actions are unconditionally prohibited in all modules at
all layers. There are no exceptions.

  PROHIBITED-01  Stochastic operations.
    No random number generation. No sampling. No probabilistic branching.
    No Monte Carlo. No stochastic simulation of any kind.

  PROHIBITED-02  File input and output in computational layers.
    No open(). No pathlib.Path.read*(). No pathlib.Path.write*().
    No csv, json, pickle, shelve, sqlite3, or any other I/O library call
    inside any function that performs computation or returns a result.
    File I/O is permitted only in dedicated loader modules that are
    explicitly excluded from the computational layer definition and that
    produce only immutable inputs to computational functions.

  PROHIBITED-03  Logging in computational layers.
    No calls to logging.getLogger(). No print() statements. No sys.stderr
    writes. No structured logging frameworks inside computational functions.

  PROHIBITED-04  Environment variable access.
    No os.environ. No os.getenv(). No dotenv. No configuration loaded from
    environment at runtime inside any computational function.

  PROHIBITED-05  Global mutable state.
    No module-level mutable containers that are written to during execution.
    No singleton objects that accumulate state across calls. No class-level
    mutable attributes shared across instances.

  PROHIBITED-06  Reimplementation of canonical logic.
    No module outside the canonical owner may reimplement, duplicate, or
    inline the logic of any canonical function. All callers must import
    and delegate to the canonical function.

  PROHIBITED-07  Modification of hash-protected constants.
    No numeric constant registered in THRESHOLD_MANIFEST.json may be
    changed at runtime, overridden by subclassing, or shadowed by a local
    variable of the same name within the scope of any function that uses
    the constant in arithmetic.

  PROHIBITED-08  New regime taxonomy definitions.
    No module outside jarvis/core/regime.py may define a new enum class
    that represents a regime state, correlation state, asset class, or
    any other taxonomy that duplicates or extends the canonical enums.

  PROHIBITED-09  String-based regime branching.
    No module may branch on the string value of a regime by comparing
    against a hardcoded string literal. All regime comparisons must use
    canonical enum instances imported from jarvis/core/regime.py.

  PROHIBITED-10  Architectural drift.
    No new dependency edge may be introduced between modules without
    explicit review against the import rules in Section 2. No new layer
    may be created without documenting it in this file and confirming
    compliance with all rules in Sections 2 through 7.


SECTION 5 -- DELEGATION RULE
===========================================================================

Any module that needs the result of a computation owned by another module
must import and call the canonical function that produces that result.

A module must never reproduce, inline, or approximate the logic of a
function it does not own, even if the reproduction would be functionally
equivalent.

Delegation is the only permitted form of code reuse across module
boundaries.

This rule applies at all layers. It applies to single-line computations
as well as multi-step algorithms. Simplicity of the reimplementation does
not exempt it from this rule.

If a canonical function does not exist for a required computation, the
correct action is to create a new canonical function in the appropriate
stable core layer and import it from there. Creating a local approximation
in an orchestration layer is prohibited.


SECTION 6 -- NO REIMPLEMENTATION RULE
===========================================================================

The no-reimplementation rule is a specific application of the delegation
rule. It states:

  The logic of any function defined in a stable core layer must exist in
  exactly one place in the codebase: the canonical definition in that
  stable core layer.

  Consequence for orchestration layers: orchestration layers may not
  contain any arithmetic, conditional branching, or data transformation
  that duplicates logic already present in a stable core layer, even if
  the orchestration layer applies that logic to different data shapes or
  at a different granularity.

  Consequence for testing: test files that need to replicate a computation
  to assert a result must import the canonical function and call it.
  Tests must not contain hardcoded expected values derived by manually
  executing canonical arithmetic outside the system.

  Consequence for documentation: documentation examples must call
  canonical functions. Documentation must not contain inline pseudocode
  that reimplements canonical logic.


SECTION 7 -- EXTERNAL LAYER DEFINITION
===========================================================================

An external layer is any module or package that satisfies all of the
following conditions:

  1. It resides outside jarvis/core/, jarvis/risk/, jarvis/utils/,
     jarvis/portfolio/, and jarvis/execution/.

  2. It does not define any canonical enum, canonical constant, or
     canonical computational function.

  3. It delegates all risk assessment, regime classification, allocation
     arithmetic, and exposure routing to stable core layers via import.

  4. It satisfies all determinism guarantees in Section 3.

  5. It complies with all prohibitions in Section 4.

Current external layers: jarvis/orchestrator/, jarvis/backtest/,
jarvis/walkforward/ (reserved).

A module is not automatically external simply because it resides outside
the stable core directories. A module that reimplements canonical logic
violates the no-reimplementation rule regardless of its directory location.


SECTION 8 -- STABILITY CONTRACT FOR STABLE CORE LAYERS
===========================================================================

The stable core layers -- jarvis/core/, jarvis/risk/, jarvis/utils/,
jarvis/portfolio/, jarvis/execution/ -- are governed by the following
stability contract:

  CONTRACT-01  No file inside a stable core layer may be modified without
    a signed release that increments the version number and updates
    THRESHOLD_MANIFEST.json if any hash-protected value is affected.

  CONTRACT-02  No numeric constant inside a stable core layer may be
    changed between versions without a migration document that records
    the old value, the new value, the rationale, and the impact on all
    downstream call sites.

  CONTRACT-03  No function signature inside a stable core layer may be
    changed in a backward-incompatible way without a major version bump.

  CONTRACT-04  No enum value inside jarvis/core/regime.py may be removed
    or renamed without auditing all call sites across the entire codebase
    and issuing a migration guide.

  CONTRACT-05  No new enum value may be added to jarvis/core/regime.py
    without confirming that all lookup tables and branching logic that
    reference that enum are updated to handle the new value explicitly.
    Silent fallthrough to a default case is not permitted.

  CONTRACT-06  The canonical exposure equation defined in risk_engine.py
    must remain identical across versions unless a full FAS revision is
    issued. Arithmetic modifications require a new FAS version number and
    a complete re-hash of all affected entries in THRESHOLD_MANIFEST.json.

  CONTRACT-07  The clip chain order defined in risk_engine.py -- Clip A,
    Clip B, Clip C, CRISIS dampening -- must remain identical across
    versions. Reordering constitutes a semantic change and requires a
    full FAS revision.


SECTION 9 -- ORCHESTRATOR ROLE
===========================================================================

jarvis/orchestrator/ is the canonical integration point between the risk
assessment layer and the portfolio allocation layer.

Its sole responsibility is to connect the output of RiskEngine.assess()
to the input of route_exposure_to_positions() in the correct order with
the correct field extraction.

The orchestrator must:

  1. Instantiate RiskEngine fresh per call. No instance may be reused
     across pipeline invocations. This satisfies DET-02.

  2. Call RiskEngine.assess() with all required parameters passed
     explicitly. No parameter may be sourced from module-level state.

  3. Extract exposure_weight from the returned RiskOutput. No other
     field of RiskOutput may be used by the orchestrator for computation.
     Other fields may be passed through to callers as part of a richer
     output type if a future version requires it, but such extension
     requires a version bump and must not change existing behavior.

  4. Pass exposure_weight as exposure_fraction to
     route_exposure_to_positions(). The field name mapping is fixed.
     No scaling, transformation, or clamping of exposure_weight is
     permitted between extraction and delegation.

  5. Return the positions dict unchanged from route_exposure_to_positions().
     No post-processing of positions is permitted in the orchestrator.

The orchestrator must not:

  - Contain any risk arithmetic.
  - Contain any allocation arithmetic.
  - Contain any regime branching logic.
  - Validate inputs that are already validated by downstream modules.
  - Cache any result across calls.
  - Read from or write to any external state.


SECTION 10 -- BACKTEST ROLE
===========================================================================

jarvis/backtest/ is the canonical layer for rolling-window historical
simulation over a time series of returns and prices.

Its sole responsibility is to manage the iteration over timesteps, the
slicing of the lookback window, the delegation of each timestep to
run_full_pipeline(), and the accumulation of the equity curve.

The backtest layer must:

  1. Validate that window >= 20 before beginning iteration. This mirrors
     the minimum length requirement of RiskEngine.compute_expected_drawdown().

  2. Validate that initial_capital > 0 before beginning iteration.

  3. Validate that asset_price_series and returns_series have equal length
     before beginning iteration.

  4. At each timestep t >= window, slice the lookback window as
     returns_series[t - window : t]. The slice must be exactly window
     elements. No padding, no interpolation.

  5. Delegate each timestep entirely to run_full_pipeline() by passing
     the window slice as returns_history, the current price as the sole
     entry in asset_prices, and all other parameters unchanged.

  6. Extract position_size as the scalar value from the single-entry
     positions dict returned by run_full_pipeline().

  7. Update equity as: equity * (1.0 + returns_series[t] * position_size).
     This is the only arithmetic the backtest layer may perform.
     No other formula may be used for equity updating.

  8. Append the updated equity value to the equity curve after each step.

  9. Return the equity curve as a list of floats after all timesteps are
     processed.

The backtest layer must not:

  - Contain any risk arithmetic beyond the equity update formula above.
  - Contain any allocation arithmetic.
  - Contain any regime detection or regime branching logic.
  - Reimplement any portion of run_full_pipeline().
  - Cache pipeline results across timesteps.
  - Read from or write to any file or external state.
  - Produce any output other than the equity curve list.

SECTION 11 -- MASTER DATA FLOW PIPELINE (S37 AUTORITATIV)
===========================================================================

Source: FAS v6.0.1 -- 37_SYSTEM_ADDENDUM.md
This is the single authoritative data flow definition. All modules
reference this pipeline. No implicit data paths are permitted. Every
data transfer must appear in this definition.

LAYER HIERARCHY (Enforcement Priority P0-P9)

  P0  Integrity / Hash Chain          (S01)  -- blocks ALL if violated
  P1  Global State Controller         (S35)  -- singleton, no bypass
  P2  OOD Ensemble Gate               (S10)  -- blocks P3-P9 if OOD=True
  P3  Regime Engine                   (S05)  -- required before P4-P9
  P4  Volatility Layer                (S16-S17) -- required before P5-P9
  P5  Risk Engine                     (S17)  -- required before P6-P9
  P6  Strategy Layer                  (S26)  -- required before P7-P9
  P7  Portfolio Context               (S29-S30) -- required before P8-P9
  P8  Confidence Engine               (S08, S11) -- required before P9
  P9  Visual Output                   (S13)  -- terminal, ZERO write perms

STAGE 0 -- LIVE DATA INTEGRITY GATE
  Applies before Stage 1 in MODE_LIVE_ANALYTICAL and MODE_HYBRID only.
  In MODE_HISTORICAL: gate is bypassed (data pre-validated in store).
  File: jarvis/core/live_data_integrity_gate.py

  All incoming ticks/candles must pass ALL 5 checks before admission:

    CHECK 1 -- MISSING DATA
      No required OHLCV field may be None, NaN, or Inf.
      volume must be > 0.
      Failure: FM-03 (DATA_GAP) triggered for affected asset.

    CHECK 2 -- TIMESTAMP CONTINUITY
      sequence_id must be monotonically increasing per symbol/timeframe.
      Gap threshold varies by asset class:
        Crypto:      2 * timeframe_seconds (24/7)
        Forex:       5 * timeframe_seconds (during session)
        Indices:     1 * timeframe_seconds (during session hours)
        Commodities: 3 * timeframe_seconds (during session)
      Failure: FM-03 triggered; is_stale = True on object.

    CHECK 3 -- SPREAD ANOMALY DETECTION
      spread_bps must be < max_entry_spread_bps * 2.0.
      Failure: FM-06 (SPREAD_ANOMALY) triggered. Object passed but flagged.
      No new entries permitted for asset.

    CHECK 4 -- OUTLIER FILTER (Robust Z-Score)
      close price must satisfy: |z_score| < 5.0
      where z_score = (close - rolling_median) / rolling_MAD
      rolling window: 20 candles.
      Failure: quality_score reduced by 0.30; object passed as SUSPECT.
      If quality_score < 0.5 after reduction: FM-03 triggered.

    CHECK 5 -- ASSET CLASS VALIDATION
      asset_class must resolve in VOLATILITY_SCALING.
      session_tag must be valid for declared asset_class.
      Failure: FM-03 triggered; object rejected.

  ON INTEGRITY FAILURE:
    - Trigger appropriate Failure Mode (FM-03 or FM-06)
    - meta_uncertainty increases per IMPACT_TABLE
    - Confidence decreases per Failure Mode rules
    - System does NOT halt unless FM rules mandate it
    - All failures logged to structured audit log

  INPUT:   Raw tick/candle from LiveDataProvider
  OUTPUT:  StandardizedMarketDataObject (validated) or FM trigger
  READ:    VolatilityState rolling buffer, StrategyObject spread thresholds
  WRITE:   meta_uncertainty (via ctrl) if integrity fails
  GATE:    All 5 checks must pass; else FM-03 or FM-06
  DEPS:    S03 (market_data_provider.py), failure_handler.py

STAGE 1 -- MARKET DATA
  INPUT:   Raw OHLCV, order book snapshots, tick data per asset_id
  OUTPUT:  EnhancedMarketData (validated, gap-flagged, session-tagged,
           spread_bps, liquidity_regime)
  READ:    External feeds, config/assets.yaml
  WRITE:   EnhancedMarketData object -- data_layer.py ONLY
  GATE:    quality_score >= 0.5; else STOP, log FM-03
  DEPS:    S03, S19 (microstructure advisory)

STAGE 2 -- NVU NORMALIZATION
  INPUT:   EnhancedMarketData.volatility, asset_class
  OUTPUT:  nvu_score (float >= 0, normalized relative to asset baseline)
  READ:    VOLATILITY_SCALING constants -- IMMUTABLE
  WRITE:   FeatureVector.nvu_score -- feature_registry.py ONLY
  GATE:    asset_class must resolve in VOLATILITY_SCALING; else STOP
  RULE:    VOLATILITY_SCALING values are FROZEN. No runtime override.
  DEPS:    S04, 38_MULTI_ASSET_UPGRADE.md

STAGE 3 -- REGIME ENGINE
  INPUT:   FeatureVector (including nvu_score), RegimeState (read-only)
  OUTPUT:  RegimeResult {regime, confidence, probs}
  READ:    FeatureVector, GlobalSystemState.regime (snapshot)
  WRITE:   RegimeState -- via GlobalSystemStateController.update() ONLY
  GATE:    drift_severity < 0.8 (Drift Gate); OOD Gate (P2)
  RULE:    Cannot write StrategyState or PortfolioState directly
  FAILURE: confidence < 0.40 triggers FM-01 (UNDEFINED_REGIME)
  DEPS:    S05, S10

STAGE 4 -- VOLATILITY LAYER
  INPUT:   RegimeResult, nvu_score, microstructure_vol_idx
  OUTPUT:  VolatilityResult {realized_vol, forecast_vol, vol_regime,
           vol_percentile, vol_spike_flag}
  READ:    RegimeState (snapshot), NVU output from FeatureVector
  WRITE:   VolatilityState -- via GlobalSystemStateController.update() ONLY
  GATE:    vol_regime must align with RegimeResult.regime or emit WARNING
  FAILURE: nvu_normalized > 3.0 or vol_percentile > 0.95 triggers FM-02
  DEPS:    S16, S17

STAGE 5 -- STRATEGY LAYER
  INPUT:   RegimeResult, VolatilityResult, GlobalSystemState snapshot
  OUTPUT:  StrategyObject (canonical schema -- see S26)
  READ:    RegimeState, VolatilityState, GlobalSystemState (all read-only)
  WRITE:   StrategyState -- via GlobalSystemStateController.update() ONLY
  GATE:    Regime must not be UNKNOWN; vol_spike_flag must be False for
           new entries
  RULE:    Adaptive Weighting ONLY operates through StrategyObject.Weight_Model
  FAILURE: UNKNOWN regime triggers FM-01; vol spike applies FM-02 size scalar
  DEPS:    S26, S05

STAGE 6 -- RISK ENGINE
  INPUT:   StrategyObject, VolatilityResult, PortfolioState snapshot
  OUTPUT:  RiskDecision {position_size, var_estimate, risk_mode,
           compression_flag}
  READ:    StrategyState, VolatilityState, PortfolioState (all read-only)
  WRITE:   risk_mode, risk_compression fields only -- via ctrl
  GATE:    VaR >= -0.20; drawdown < 0.15; slippage < 0.01
  RULE:    Cannot reduce confidence floors. Cannot bypass VaR gate.
  FAILURE: Extreme correlation triggers FM-04; vol spike applies FM-02
  DEPS:    S17, S40

STAGE 7 -- PORTFOLIO CONTEXT
  INPUT:   RiskDecision, current_positions (read-only PortfolioState)
  OUTPUT:  PortfolioDecision {allocation, cross_asset_exposure,
           correlation_matrix, diversification_ratio}
  READ:    PortfolioState snapshot, RiskDecision
  WRITE:   PortfolioState -- via GlobalSystemStateController.update() ONLY
  GATE:    All correlation matrix values must be finite; else FM-04
  FAILURE: mean pairwise correlation > 0.85 triggers FM-04;
           illiquid session triggers FM-05
  DEPS:    S29, S30

STAGE 8 -- CONFIDENCE ENGINE
  INPUT:   All prior layer outputs, GlobalSystemState snapshot
  OUTPUT:  ConfidenceBundle {mu, sigma2, Q, S, U, R}
  READ:    ALL states (read-only snapshots only)
  WRITE:   GlobalSystemState.meta_uncertainty ONLY
  GATE:    None -- Confidence Engine always runs, even in degraded mode
  RULE:    Can ONLY reduce confidence. Never fabricates certainty.
           Failure mode impacts applied via IMPACT_TABLE.
  DEPS:    S08, S11

STAGE 9 -- VISUAL OUTPUT
  INPUT:   ConfidenceBundle, StrategyObject, PortfolioDecision
  OUTPUT:  DisplayPayload (human-readable decision support -- manual ONLY)
  READ:    ALL states (read-only snapshots)
  WRITE:   NONE -- zero write permissions under any condition
  GATE:    None -- always renders; failure modes shown as banners
  RULE:    Purely analytical. No order execution. No broker API.
  DEPS:    S13


SECTION 12 -- MODULE STATE WRITE PERMISSION MATRIX
===========================================================================

Source: FAS v6.0.1 -- 37_SYSTEM_ADDENDUM.md
All state mutations route through GlobalSystemStateController.update().
No module may directly assign fields on SystemState, RegimeState,
VolatilityState, StrategyState, or PortfolioState. Direct field
assignment is a P1-level violation detectable by static analysis.

  Module                  | Writes To                    | Forbidden From Writing
  ------------------------|------------------------------|-------------------------------
  data_layer.py           | EnhancedMarketData           | Any state
  feature_registry.py     | FeatureVector.nvu_score       | Any state
  regime_engine.py        | RegimeState (via ctrl)        | StrategyState, PortfolioState,
                          |                              | VolatilityState
  volatility_layer.py     | VolatilityState (via ctrl)    | RegimeState, StrategyState,
                          |                              | PortfolioState
  strategy_selector.py    | StrategyState (via ctrl)      | RegimeState, VolatilityState,
                          |                              | PortfolioState
  adaptive_weighting.py   | StrategyState.weight (via     | All other states
                          | ctrl)                        |
  risk_engine.py          | risk_mode, risk_compression   | StrategyState, PortfolioState
                          | (via ctrl)                   |
  portfolio_context.py    | PortfolioState (via ctrl)     | RegimeState, VolatilityState,
                          |                              | StrategyState
  confidence_engine.py    | meta_uncertainty (via ctrl)   | All other state fields
  failure_handler.py      | meta_uncertainty (via         | All other state fields
                          | IMPACT_TABLE deltas)         |
  hybrid_coordinator.py   | hybrid_sync_point (once       | All other state fields
                          | only), operating_mode        |
  replay_engine.py        | all fields (during replay     | N/A (replay mode only)
                          | from checkpoint only)        |
  visual_output.py        | NONE                         | All states

  ALL OTHER MODULES:        FORBIDDEN from calling ctrl.update()


SECTION 13 -- EVENT BUS FORMALIZATION
===========================================================================

Source: FAS v6.0.1 -- 37_SYSTEM_ADDENDUM.md
File: jarvis/core/event_bus.py
Classification: Analytical and research only. No execution triggers.
                No order events.
Governance: All events are immutable. All state mutation routes through
            ctrl.update(). The event system is the sole mechanism for
            communicating state changes between layers.

EVENT TYPES (EventType enum)

  MARKET_DATA          Emitted when a StandardizedMarketDataObject is
                       admitted through the Integrity Gate or loaded from
                       historical store.

  REGIME_CHANGE        Emitted when RegimeState.regime changes value.

  FAILURE_MODE         Emitted when a Failure Mode (FM-01..FM-06) is
                       activated or resolved.

  EXPOSURE             Emitted when PortfolioState.gross_exposure or
                       net_exposure changes beyond EXPOSURE_DELTA_THRESHOLD.

  STRATEGY_WEIGHT      Emitted when StrategyState.weight_scalar changes.

  CONFIDENCE_UPDATE    Emitted when ConfidenceBundle values change (only on
                       permitted refresh triggers).

EVENT OBJECTS (all frozen dataclasses)

  BaseEvent
    event_id:     str         -- UUID, unique per event
    event_type:   EventType
    timestamp:    datetime
    sequence_id:  int         -- global monotonic sequence for replay
    asset_id:     Optional[str]  -- None means system-wide event

  MarketDataEvent(BaseEvent)
    symbol, timeframe, close, quality_score, gap_detected, is_stale,
    data_source ("historical" | "live" | "hybrid_backfill" | "hybrid_live")

  RegimeChangeEvent(BaseEvent)
    from_regime, to_regime, confidence, transition_flag

  FailureModeEvent(BaseEvent)
    failure_mode_code ("FM-01".."FM-06"), activated (bool),
    trigger_condition, confidence_impact (dict from IMPACT_TABLE)

  ExposureEvent(BaseEvent)
    prior_gross_exposure, current_gross_exposure,
    prior_net_exposure, current_net_exposure, trigger_source

  StrategyWeightChangeEvent(BaseEvent)
    strategy_id, prior_weight, new_weight, regime_trigger

  ConfidenceUpdateEvent(BaseEvent)
    prior_mu, new_mu, prior_Q, new_Q, prior_U, new_U, trigger

EVENT QUEUE -- DeterministicEventQueue

  File: jarvis/core/event_queue.py
  Invariants (non-negotiable):
    1. FIFO ordering -- events processed in emission order
    2. No parallel mutation -- single-threaded event processing
    3. All state mutation routes through ctrl.update() -- never inside queue
    4. No execution events permitted -- queue is analytical only
    5. Queue is not a broker interface -- no order objects may enter
    6. Events are immutable (frozen dataclasses) -- never modified in transit

  API:
    emit(event) -> int      Add event; returns sequence_id. Raises
                            OverflowError if max_size exceeded.
    drain() -> Iterator     Yields all pending events in FIFO order,
                            removing them. Single processing thread only.
    peek() -> List          Read-only view; does not consume events.
    depth -> int            Current queue depth.
    processed_count -> int  Total events processed lifetime.

EVENT PROPAGATION RULES

  Source Layer emits Event -> EventQueue (FIFO) -> EventDispatcher reads ->
  Handler calls ctrl.update() -> State updated -> Next event processed

  Emitting Layers:
    Live/Historical Provider  -> MarketDataEvent
    Integrity Gate            -> FailureModeEvent (FM-03, FM-06)
    Regime Engine (P3)        -> RegimeChangeEvent
    Failure Handler           -> FailureModeEvent (all FM types)
    Portfolio Context (P7)    -> ExposureEvent
    Strategy Layer (P6)       -> StrategyWeightChangeEvent
    Confidence Engine (P8)    -> ConfidenceUpdateEvent

  Propagation Constraints:
    1. Events do NOT trigger other events inside the same dispatch cycle
       (no cascading emission -- prevents infinite loops).
    2. State reads inside event handlers use snapshot from BEFORE the cycle.
    3. All ctrl.update() calls happen AFTER the full event is processed.
    4. Visual Output (P9) reads state AFTER all events in cycle are processed.
    5. Sandbox/Research layers may read the event log but may not emit events
       during live operation (only in replay mode).

  Hybrid Mode uses the same DeterministicEventQueue. Mode affects only
  the event source, not the event system's behavior.

FORBIDDEN EVENT PATTERNS

  The following event types must NEVER enter the queue:
    - OrderEvent (no order objects permitted)
    - BrokerConnectEvent (no broker connectivity)
    - ExecutionEvent (no execution triggers)
    - CapitalMutationEvent (no real capital changes)
    - AccountStateEvent (no broker account state)

  Any event type not listed in EventType enum is rejected at emission time.


SECTION 14 -- CONFIDENCE REFRESH LOGIC
===========================================================================

Source: FAS v6.0.1 -- 37_SYSTEM_ADDENDUM.md
File: jarvis/confidence/confidence_refresh.py

The Confidence Score (ConfidenceBundle {mu, sigma2, Q, S, U, R}) is a
Research Strength Indicator -- NOT a trade trigger. It quantifies how
reliable the current market assessment is.

MODE-AWARE REFRESH TRIGGERS

  In MODE_HISTORICAL:
    Confidence always recomputes (batch recompute on every step).

  In MODE_LIVE_ANALYTICAL and MODE_HYBRID (live window):
    Confidence may ONLY update when one of these triggers is present:

    1. regime_change:             RegimeState.regime value changed
    2. volatility_state_change:   VolatilityState.vol_regime or
                                  vol_spike_flag changed
    3. strategy_weight_change:    StrategyState.weight_scalar changed
    4. portfolio_exposure_change: PortfolioState.gross_exposure delta
                                  exceeds threshold
    5. failure_mode_trigger:      Any FM-01..FM-06 activated or deactivated

  NOT PERMITTED -- Confidence must NOT recalculate when:
    - A tick arrives but no state has changed
    - Regime and volatility state are identical to prior snapshot
    - No failure mode status changed
    - Only sequence_id incremented (pure data flow, no analytical change)

REFRESH GATE FUNCTION

  def should_refresh_confidence(prev_state, curr_state, operating_mode):
      """
      Returns True if confidence engine should recompute.
      HISTORICAL mode: always True (batch recompute).
      LIVE / HYBRID: only on genuine state changes.
      """
      if operating_mode == "historical":
          return True

      return any([
          prev_state.regime          != curr_state.regime,
          prev_state.risk_mode       != curr_state.risk_mode,
          prev_state.strategy_mode   != curr_state.strategy_mode,
          prev_state.ood_status      != curr_state.ood_status,
          prev_state.meta_uncertainty != curr_state.meta_uncertainty,
      ])

CONFIDENCE UPDATE PATH (complete, unambiguous)

  1. STATE CHANGE OCCURS (any of five permitted triggers)
  2. should_refresh_confidence(prev, curr, mode) returns True
  3. confidence_engine.compute(curr_snapshot) produces new ConfidenceBundle
  4. IMPACT_TABLE applied if any FM active (confidence can only decrease)
  5. ctrl.update(meta_uncertainty=new_bundle.U) -- ONLY field written to state
  6. ConfidenceUpdateEvent emitted with delta values
  7. EventQueue -> EventDispatcher routes to Visual Output (P9)
  8. Visual Output renders updated confidence display

  WHAT DOES NOT HAPPEN:
    - confidence_engine does NOT write mu, Q, S, R to GlobalSystemState
      (only meta_uncertainty is written; other bundle fields are display-only)
    - Confidence does NOT trigger execution of any kind
    - Confidence does NOT override Risk Engine outputs
    - Confidence does NOT auto-adjust StrategyObject weights directly
      (strategy weight changes are a separate StrategyWeightChangeEvent)

CORRECT USAGE PATTERN

  prev_snapshot = ctrl.get_state()
  provider.ingest_tick(...)               # Data update
  curr_snapshot = ctrl.get_state()

  if should_refresh_confidence(prev_snapshot, curr_snapshot, mode):
      new_bundle = confidence_engine.compute(curr_snapshot)
      ctrl.update(meta_uncertainty=new_bundle.U)
      # Bundle goes ONLY to Visual Output (P9)

SPIKE-UP PREVENTION

  Confidence score increases are only permitted when:
    - A Failure Mode has been resolved (FM deactivated)
    - Regime transitions from SHOCK/UNKNOWN to a stable regime
    - Recovery criteria met (per FM-01..FM-06 recovery rules)
  Even then, recovery is incremental -- not instantaneous.

CONFIDENCE SCORE GOVERNANCE

  PERMITTED -- Confidence Score may:
    - Be displayed in UI as quality indicator
    - Inform Strategy weighting models (via Weight_Model, read-only)
    - Serve as input to Research Layer
    - Be used in Scenario Sandbox simulations
    - Be included in Benchmark analyses

  FORBIDDEN -- Confidence Score must NOT:
    - Trigger execution
    - Automatically open positions
    - Directly overwrite Portfolio State
    - Call Broker API
    - Trigger any external system action

  ENFORCEMENT:
    Confidence output goes ONLY to:
      1. Visual Output Layer (P9) -- for display
      2. Strategy Layer (P6) -- via Weight_Model (read-only)
      3. Research Extensions -- Scenario Sandbox, Benchmark Engine
    Any other data path from Confidence Engine is an architecture violation.


SECTION 15 -- EVENT SYSTEM CONSTRAINTS
===========================================================================

Source: FAS v6.0.1 -- 37_SYSTEM_ADDENDUM.md

  CONSTRAINT 1 -- NO RECURSIVE EVENT LOOPS
    Events must NOT emit new events during the same dispatch cycle.
    DeterministicEventQueue.emit() may not be called from within an
    event handler. New events generated as a consequence of a state
    change are queued for the NEXT dispatch cycle only.
    Violation: EventDispatcher tracks call stack depth. If emit() is
    called while drain() is active: RuntimeError raised.

  CONSTRAINT 2 -- NO CASCADING RE-SCORING WITHOUT STATE CHANGE
    Confidence Engine must not recompute unless
    should_refresh_confidence() returns True. Re-scoring without a
    permitted trigger is a correctness violation.

  CONSTRAINT 3 -- NO CONFIDENCE REFRESH WITHOUT TRIGGER
    ConfidenceUpdateEvent must not be emitted unless:
      a. One of the five defined refresh triggers is present, AND
      b. should_refresh_confidence(prev, curr, mode) returns True.
    Tick-level recalculation is explicitly forbidden.

  CONSTRAINT 4 -- NO FULL PORTFOLIO RECOMPUTE ON SINGLE TICK
    PortfolioState recompute (correlation matrix, VaR, exposure) must
    only trigger on EXPOSURE_DELTA_THRESHOLD or CORRELATION_REGIME_SHIFT
    events. Single tick ingestion does not trigger full portfolio recompute.

  CONSTRAINT 5 -- NO SANDBOX MUTATION OF LIVE STATE
    ScenarioSandboxEngine operates on immutable state snapshots.
    ctrl.update() may not be called from within ScenarioSandboxEngine
    or any research/benchmark extension module.

  CONSTRAINT 6 -- NO CROSS-MODE STATE LEAKAGE
    In MODE_HYBRID:
      - Backtest-window state must not overwrite live-window state
        after sync_point.
      - Live-window state must not contaminate backtest-window results.
      - sync_point is session-immutable after setting.
      - State from historical phase is READ-ONLY after sync_point.

  CONSTRAINT 7 -- SINGLE MUTATION PATH
    All state mutations route through ctrl.update(). No module may
    directly assign fields on SystemState, RegimeState, VolatilityState,
    StrategyState, or PortfolioState.

  CONSTRAINT 8 -- NO UNBOUNDED BACKFILL LOOPS
    Historical backfill in MODE_HYBRID must terminate at sync_point.
    Maximum backfill duration: 10 minutes. If exceeded: checkpoint
    exported; backfill paused; operator notified.


===========================================================================
END OF ARCHITECTURE SPECIFICATION
FAS v6.1.0 -- Sections 1-10 original; Sections 11-15 from S37 Addendum
===========================================================================
