# =============================================================================
# Unit Tests for jarvis/robustness/engine.py
# =============================================================================

import copy
import pytest

from jarvis.robustness.engine import evaluate_robustness


# ---------------------------------------------------------------------------
# HELPERS
# ---------------------------------------------------------------------------

def _make_ranking_entry(window, step, meta, mean_cagr, mean_sharpe, worst_mdd):
    """Build a single ranking entry as produced by run_selection()."""
    return {
        "window": window,
        "step": step,
        "meta_uncertainty": meta,
        "aggregate": {
            "mean_cagr": mean_cagr,
            "mean_sharpe": mean_sharpe,
            "worst_max_drawdown": worst_mdd,
        },
        "score_tuple": (mean_sharpe, mean_cagr, -worst_mdd),
    }


def _make_selection_output(entries):
    """Build selection_output dict from list of ranking entry tuples."""
    ranking = [_make_ranking_entry(*e) for e in entries]
    if ranking:
        best = ranking[0]
        best_params = {
            "window": best["window"],
            "step": best["step"],
            "meta_uncertainty": best["meta_uncertainty"],
        }
        best_score = best["aggregate"]
    else:
        best_params = {}
        best_score = {}
    return {
        "best_params": best_params,
        "best_score": best_score,
        "ranking": ranking,
    }


# ===================================================================
# TestEvaluateRobustnessValidation
# ===================================================================

class TestEvaluateRobustnessValidation:
    def test_empty_ranking_raises(self):
        sel = {"best_params": {}, "best_score": {}, "ranking": []}
        with pytest.raises(ValueError, match="ranking must not be empty"):
            evaluate_robustness(sel)

    def test_missing_ranking_key_raises(self):
        with pytest.raises(KeyError):
            evaluate_robustness({"best_params": {}, "best_score": {}})

    def test_missing_aggregate_key_raises(self):
        sel = {
            "best_params": {},
            "best_score": {},
            "ranking": [{"window": 20, "step": 1, "meta_uncertainty": 0.2}],
        }
        with pytest.raises(KeyError):
            evaluate_robustness(sel)

    def test_valid_single_entry(self):
        sel = _make_selection_output([
            (20, 1, 0.2, 0.10, 1.5, 0.15),
        ])
        result = evaluate_robustness(sel)
        assert "robustness_score" in result


# ===================================================================
# TestEvaluateRobustnessOutputStructure
# ===================================================================

class TestEvaluateRobustnessOutputStructure:
    def setup_method(self):
        self.sel = _make_selection_output([
            (20, 1, 0.1, 0.12, 1.8, 0.15),
            (30, 2, 0.2, 0.08, 1.2, 0.10),
            (40, 3, 0.3, 0.05, 0.9, 0.20),
        ])
        self.result = evaluate_robustness(self.sel)

    def test_top_level_keys(self):
        assert set(self.result.keys()) == {
            "best_params", "robustness_score", "stability_metrics",
        }

    def test_best_params_keys(self):
        bp = self.result["best_params"]
        assert set(bp.keys()) == {"window", "step", "meta_uncertainty"}

    def test_best_params_matches_first_ranking(self):
        bp = self.result["best_params"]
        assert bp["window"] == 20
        assert bp["step"] == 1
        assert bp["meta_uncertainty"] == 0.1

    def test_robustness_score_is_float(self):
        assert isinstance(self.result["robustness_score"], float)

    def test_stability_metrics_keys(self):
        sm = self.result["stability_metrics"]
        assert set(sm.keys()) == {
            "top_gap", "cagr_variance", "sharpe_variance", "drawdown_variance",
        }

    def test_stability_metrics_are_floats(self):
        sm = self.result["stability_metrics"]
        for key in sm:
            assert isinstance(sm[key], float)


# ===================================================================
# TestTopGap
# ===================================================================

class TestTopGap:
    def test_single_entry_top_gap_zero(self):
        sel = _make_selection_output([
            (20, 1, 0.1, 0.10, 1.5, 0.15),
        ])
        result = evaluate_robustness(sel)
        assert result["stability_metrics"]["top_gap"] == 0.0

    def test_two_entries_top_gap(self):
        sel = _make_selection_output([
            (20, 1, 0.1, 0.10, 1.5, 0.15),
            (30, 1, 0.1, 0.06, 1.2, 0.10),
        ])
        result = evaluate_robustness(sel)
        assert result["stability_metrics"]["top_gap"] == pytest.approx(0.04)

    def test_negative_top_gap(self):
        # Second entry has higher CAGR than first (unusual but possible)
        sel = _make_selection_output([
            (20, 1, 0.1, 0.05, 1.5, 0.15),
            (30, 1, 0.1, 0.10, 1.2, 0.10),
        ])
        result = evaluate_robustness(sel)
        assert result["stability_metrics"]["top_gap"] == pytest.approx(-0.05)

    def test_equal_cagr_top_gap_zero(self):
        sel = _make_selection_output([
            (20, 1, 0.1, 0.10, 1.5, 0.15),
            (30, 1, 0.1, 0.10, 1.2, 0.10),
        ])
        result = evaluate_robustness(sel)
        assert result["stability_metrics"]["top_gap"] == pytest.approx(0.0)

    def test_three_entries_uses_first_two_only(self):
        sel = _make_selection_output([
            (20, 1, 0.1, 0.20, 1.5, 0.15),
            (30, 1, 0.1, 0.10, 1.2, 0.10),
            (40, 1, 0.1, 0.01, 0.5, 0.30),
        ])
        result = evaluate_robustness(sel)
        # top_gap = 0.20 - 0.10 = 0.10, third entry irrelevant
        assert result["stability_metrics"]["top_gap"] == pytest.approx(0.10)


# ===================================================================
# TestVarianceComputation
# ===================================================================

class TestVarianceComputation:
    def test_single_entry_all_variance_zero(self):
        sel = _make_selection_output([
            (20, 1, 0.1, 0.10, 1.5, 0.15),
        ])
        result = evaluate_robustness(sel)
        sm = result["stability_metrics"]
        assert sm["cagr_variance"] == 0.0
        assert sm["sharpe_variance"] == 0.0
        assert sm["drawdown_variance"] == 0.0

    def test_identical_entries_variance_zero(self):
        sel = _make_selection_output([
            (20, 1, 0.1, 0.10, 1.5, 0.15),
            (30, 1, 0.1, 0.10, 1.5, 0.15),
            (40, 1, 0.1, 0.10, 1.5, 0.15),
        ])
        result = evaluate_robustness(sel)
        sm = result["stability_metrics"]
        assert sm["cagr_variance"] == pytest.approx(0.0)
        assert sm["sharpe_variance"] == pytest.approx(0.0)
        assert sm["drawdown_variance"] == pytest.approx(0.0)

    def test_cagr_variance_hand_computed(self):
        # values: [0.10, 0.06]
        # mean = 0.08, var = ((0.02)^2 + (0.02)^2) / 2 = 0.0004
        sel = _make_selection_output([
            (20, 1, 0.1, 0.10, 1.0, 0.1),
            (30, 1, 0.1, 0.06, 1.0, 0.1),
        ])
        result = evaluate_robustness(sel)
        assert result["stability_metrics"]["cagr_variance"] == pytest.approx(0.0004)

    def test_sharpe_variance_hand_computed(self):
        # values: [2.0, 1.0]
        # mean = 1.5, var = (0.5^2 + 0.5^2) / 2 = 0.25
        sel = _make_selection_output([
            (20, 1, 0.1, 0.10, 2.0, 0.1),
            (30, 1, 0.1, 0.10, 1.0, 0.1),
        ])
        result = evaluate_robustness(sel)
        assert result["stability_metrics"]["sharpe_variance"] == pytest.approx(0.25)

    def test_drawdown_variance_hand_computed(self):
        # values: [0.10, 0.30]
        # mean = 0.20, var = (0.10^2 + 0.10^2) / 2 = 0.01
        sel = _make_selection_output([
            (20, 1, 0.1, 0.10, 1.0, 0.10),
            (30, 1, 0.1, 0.10, 1.0, 0.30),
        ])
        result = evaluate_robustness(sel)
        assert result["stability_metrics"]["drawdown_variance"] == pytest.approx(0.01)

    def test_three_entries_population_variance(self):
        # cagr values: [0.12, 0.09, 0.06]
        # mean = 0.09, var = ((0.03)^2 + 0^2 + (0.03)^2) / 3 = 0.0006
        sel = _make_selection_output([
            (20, 1, 0.1, 0.12, 1.0, 0.1),
            (30, 1, 0.1, 0.09, 1.0, 0.1),
            (40, 1, 0.1, 0.06, 1.0, 0.1),
        ])
        result = evaluate_robustness(sel)
        assert result["stability_metrics"]["cagr_variance"] == pytest.approx(0.0006)


# ===================================================================
# TestRobustnessScore
# ===================================================================

class TestRobustnessScore:
    def test_single_entry_score_zero(self):
        # top_gap = 0.0 -> score = 0.0
        sel = _make_selection_output([
            (20, 1, 0.1, 0.10, 1.5, 0.15),
        ])
        result = evaluate_robustness(sel)
        assert result["robustness_score"] == 0.0

    def test_zero_variance_score_equals_top_gap(self):
        # Both entries same sharpe and cagr variance = 0 for those
        # Actually need different cagr for top_gap > 0 but same sharpe
        sel = _make_selection_output([
            (20, 1, 0.1, 0.10, 1.0, 0.1),
            (30, 1, 0.1, 0.05, 1.0, 0.1),
        ])
        result = evaluate_robustness(sel)
        top_gap = 0.05
        # cagr variance: mean=0.075, var = (0.025^2 + 0.025^2)/2 = 0.000625
        # sharpe variance: 0.0 (both 1.0)
        cagr_var = 0.000625
        expected = top_gap * (1.0 / (1.0 + cagr_var)) * (1.0 / (1.0 + 0.0))
        assert result["robustness_score"] == pytest.approx(expected)

    def test_hand_computed_full(self):
        # ranking: cagr=[0.10, 0.06], sharpe=[2.0, 1.0], mdd=[0.15, 0.10]
        # top_gap = 0.10 - 0.06 = 0.04
        # cagr_var = ((0.02)^2 + (0.02)^2) / 2 = 0.0004
        # sharpe_var = ((0.5)^2 + (0.5)^2) / 2 = 0.25
        # score = 0.04 * (1/(1+0.0004)) * (1/(1+0.25))
        #       = 0.04 * 0.9996... * 0.8 = 0.031987...
        sel = _make_selection_output([
            (20, 1, 0.1, 0.10, 2.0, 0.15),
            (30, 1, 0.1, 0.06, 1.0, 0.10),
        ])
        result = evaluate_robustness(sel)
        expected = 0.04 * (1.0 / 1.0004) * (1.0 / 1.25)
        assert result["robustness_score"] == pytest.approx(expected, rel=1e-9)

    def test_negative_top_gap_gives_negative_score(self):
        sel = _make_selection_output([
            (20, 1, 0.1, 0.05, 1.0, 0.1),
            (30, 1, 0.1, 0.10, 1.0, 0.1),
        ])
        result = evaluate_robustness(sel)
        assert result["robustness_score"] < 0.0

    def test_high_variance_dampens_score(self):
        # Low variance
        sel_low = _make_selection_output([
            (20, 1, 0.1, 0.10, 1.01, 0.1),
            (30, 1, 0.1, 0.05, 1.00, 0.1),
        ])
        # High variance
        sel_high = _make_selection_output([
            (20, 1, 0.1, 0.10, 5.0, 0.1),
            (30, 1, 0.1, 0.05, 0.1, 0.1),
        ])
        r_low = evaluate_robustness(sel_low)
        r_high = evaluate_robustness(sel_high)
        # Same top_gap (0.05) but high sharpe variance dampens score
        assert abs(r_low["robustness_score"]) > abs(r_high["robustness_score"])


# ===================================================================
# TestEvaluateRobustnessDeterminism
# ===================================================================

class TestEvaluateRobustnessDeterminism:
    def test_identical_calls(self):
        sel = _make_selection_output([
            (20, 1, 0.1, 0.10, 1.5, 0.15),
            (30, 2, 0.2, 0.08, 1.2, 0.10),
        ])
        r1 = evaluate_robustness(sel)
        r2 = evaluate_robustness(sel)
        assert r1 == r2

    def test_input_not_mutated(self):
        sel = _make_selection_output([
            (20, 1, 0.1, 0.10, 1.5, 0.15),
            (30, 2, 0.2, 0.08, 1.2, 0.10),
        ])
        original = copy.deepcopy(sel)
        evaluate_robustness(sel)
        assert sel == original


# ===================================================================
# TestEvaluateRobustnessIntegration
# ===================================================================

class TestEvaluateRobustnessIntegration:
    def test_end_to_end_with_run_selection(self):
        """Consume real run_selection() output."""
        from jarvis.selection.engine import run_selection

        def _make_opt_entry(w, s, m, cagr, sharpe, mdd):
            return {
                "window": w, "step": s, "meta_uncertainty": m,
                "result": {
                    "segments": [], "segment_metrics": [],
                    "aggregate": {
                        "cagr": cagr, "sharpe_ratio": sharpe, "max_drawdown": mdd,
                    },
                },
            }

        opt = [
            _make_opt_entry(20, 1, 0.1, 0.10, 1.5, 0.15),
            _make_opt_entry(30, 2, 0.2, 0.08, 1.2, 0.10),
            _make_opt_entry(40, 3, 0.3, 0.12, 1.8, 0.20),
        ]
        sel = run_selection(opt)
        rob = evaluate_robustness(sel)

        assert isinstance(rob["robustness_score"], float)
        assert "best_params" in rob
        assert "stability_metrics" in rob
        sm = rob["stability_metrics"]
        assert sm["cagr_variance"] >= 0.0
        assert sm["sharpe_variance"] >= 0.0
        assert sm["drawdown_variance"] >= 0.0


# ===================================================================
# TestModuleExports
# ===================================================================

class TestModuleExports:
    def test_init_exports_evaluate_robustness(self):
        from jarvis.robustness import evaluate_robustness as er
        assert er is evaluate_robustness

    def test_importable_from_engine(self):
        from jarvis.robustness.engine import evaluate_robustness as er
        assert callable(er)
