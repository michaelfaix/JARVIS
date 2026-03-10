# =============================================================================
# jarvis/chart/chart_data_builder.py — Chart Data Builder (S32)
#
# Baut ChartOverlay aus System-Outputs zusammen.
# Einziger Weg, Daten ins Chart-Interface zu bekommen.
#
# R1: ChartDataBuilder ist die EINZIGE Quelle fuer Chart-Daten
# R2: Keine Direktzugriffe auf Berechnungsmodule vom UI
# R6: Alle angezeigten Werte muessen aus versioniertem Output stammen
#
# DET-05: Same inputs → same outputs
# DET-06: UNCERTAINTY_BANDS are fixed literals
# =============================================================================

from __future__ import annotations

from jarvis.chart.chart_contract import ChartOverlay


class ChartDataBuilder:
    """Build ChartOverlay from system outputs.

    Only way to get data into the chart interface.
    No computation logic here: only data transformation.
    """

    UNCERTAINTY_BANDS = [
        (0.20, "LOW"),
        (0.50, "MODERATE"),
        (0.75, "HIGH"),
        (1.00, "EXTREME"),
    ]

    def build(
        self,
        confidence_zone,  # ConfidenceZone
        risk_output,  # RiskOutput
        strategy_selection,  # StrategySelection
        current_price: float,
        timeframe_label: str,
    ) -> ChartOverlay:
        """Transform system outputs into chart interface data.

        No computation logic: only data transformation.

        Args:
            confidence_zone: ConfidenceZone with entry/exit data.
            risk_output: RiskOutput with risk compression info.
            strategy_selection: StrategySelection with mode/config.
            current_price: Current asset price.
            timeframe_label: Timeframe string (e.g. "5m", "1h").

        Returns:
            ChartOverlay with all chart data.
        """
        # Entry Box
        entry_box_lower = confidence_zone.entry_lower
        entry_box_upper = confidence_zone.entry_upper
        entry_conf_pct = round(confidence_zone.entry_confidence * 100.0, 1)

        # Exit Corridor
        exit_soft = confidence_zone.exit_soft
        exit_hard = confidence_zone.exit_hard
        exit_conf_pct = round(confidence_zone.exit_confidence * 100.0, 1)

        # Expected Move
        exp_move_pct = round(confidence_zone.expected_move_pct, 2)

        # Volatility Stop
        vol_stop = confidence_zone.vol_adjusted_stop
        stop_dist_pct = round(
            abs(current_price - vol_stop) / max(current_price, 1e-10) * 100.0,
            2,
        )

        # Meta-Uncertainty
        unc_pct = round(confidence_zone.meta_uncertainty * 100.0, 1)
        unc_band = "EXTREME"
        for threshold, label in self.UNCERTAINTY_BANDS:
            if confidence_zone.meta_uncertainty <= threshold:
                unc_band = label
                break

        return ChartOverlay(
            entry_box_lower=entry_box_lower,
            entry_box_upper=entry_box_upper,
            entry_confidence_pct=entry_conf_pct,
            exit_corridor_soft=exit_soft,
            exit_corridor_hard=exit_hard,
            exit_confidence_pct=exit_conf_pct,
            expected_move_pct=exp_move_pct,
            vol_stop_price=vol_stop,
            vol_stop_distance_pct=stop_dist_pct,
            regime_label=strategy_selection.config.label,
            strategy_mode_label=strategy_selection.mode.value,
            meta_uncertainty_pct=unc_pct,
            uncertainty_band=unc_band,
            timeframe_label=timeframe_label,
            risk_compression_active=risk_output.risk_compression_active,
        )
