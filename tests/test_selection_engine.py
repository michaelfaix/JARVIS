# =============================================================================
# Unit Tests for jarvis/selection/engine.py
# =============================================================================

import copy
import pytest

from jarvis.selection.engine import (
    rank_candidates,
    filter_by_threshold,
    select_top_n,
    run_selection,
    _safe_cagr,
    _safe_sharpe,
    _safe_max_drawdown,
    _compute_score_tuple,
)


# ---------------------------------------------------------------------------
# HELPERS
# ---------------------------------------------------------------------------

def _make_opt_entry(window, step, meta, cagr=0.0, sharpe=0.0, mdd=0.0):
    """Build a single optimization output entry."""
    return {
        "window": window,
        "step": step,
        "meta_uncertainty": meta,
        "result": {
            "segments": [],
            "segment_metrics": [],
            "aggregate": {
                "cagr": cagr,
                "sharpe_ratio": sharpe,
                "max_drawdown": mdd,
            },
        },
    }


def _make_opt_output(*entries):
    """Build optimization output list from tuples of
    (window, step, meta, cagr, sharpe, mdd)."""
    return [_make_opt_entry(*e) for e in entries]


# ===================================================================
# TestRankCandidates
# ===================================================================

class TestRankCandidates:
    def test_descending_default(self):
        scores = {"A": 1.0, "B": 3.0, "C": 2.0}
        result = rank_candidates(["A", "B", "C"], lambda s: scores[s])
        assert result == ["B", "C", "A"]

    def test_ascending(self):
        scores = {"A": 1.0, "B": 3.0, "C": 2.0}
        result = rank_candidates(["A", "B", "C"], lambda s: scores[s], descending=False)
        assert result == ["A", "C", "B"]

    def test_tie_breaking_lexicographic(self):
        result = rank_candidates(["Z", "A", "M"], lambda s: 1.0)
        assert result == ["A", "M", "Z"]

    def test_tie_breaking_ascending_order(self):
        result = rank_candidates(["Z", "A", "M"], lambda s: 1.0, descending=False)
        assert result == ["A", "M", "Z"]

    def test_empty_candidates(self):
        result = rank_candidates([], lambda s: 0.0)
        assert result == []

    def test_single_candidate(self):
        result = rank_candidates(["X"], lambda s: 5.0)
        assert result == ["X"]

    def test_input_order_does_not_matter(self):
        scores = {"A": 1.0, "B": 2.0, "C": 3.0}
        r1 = rank_candidates(["A", "B", "C"], lambda s: scores[s])
        r2 = rank_candidates(["C", "A", "B"], lambda s: scores[s])
        assert r1 == r2

    def test_negative_scores(self):
        scores = {"A": -1.0, "B": -3.0, "C": -2.0}
        result = rank_candidates(["A", "B", "C"], lambda s: scores[s])
        assert result == ["A", "C", "B"]

    def test_determinism(self):
        scores = {"A": 1.0, "B": 2.0, "C": 3.0}
        fn = lambda s: scores[s]
        r1 = rank_candidates(["A", "B", "C"], fn)
        r2 = rank_candidates(["A", "B", "C"], fn)
        assert r1 == r2

    def test_input_not_mutated(self):
        candidates = ["A", "B", "C"]
        original = list(candidates)
        rank_candidates(candidates, lambda s: 1.0)
        assert candidates == original


# ===================================================================
# TestFilterByThreshold
# ===================================================================

class TestFilterByThreshold:
    def test_basic_filter(self):
        scores = {"A": 1.0, "B": 3.0, "C": 2.0}
        result = filter_by_threshold(["A", "B", "C"], scores, 2.0)
        assert result == ["B", "C"]

    def test_inclusive_threshold(self):
        scores = {"A": 2.0}
        result = filter_by_threshold(["A"], scores, 2.0)
        assert result == ["A"]

    def test_all_below_threshold(self):
        scores = {"A": 1.0, "B": 0.5}
        result = filter_by_threshold(["A", "B"], scores, 5.0)
        assert result == []

    def test_missing_symbol_defaults_zero(self):
        scores = {"A": 1.0}
        result = filter_by_threshold(["A", "B"], scores, 0.0)
        assert "A" in result
        assert "B" in result

    def test_missing_symbol_below_threshold(self):
        scores = {"A": 1.0}
        result = filter_by_threshold(["A", "B"], scores, 0.5)
        assert result == ["A"]

    def test_sorted_descending_by_score(self):
        scores = {"A": 3.0, "B": 5.0, "C": 4.0}
        result = filter_by_threshold(["A", "B", "C"], scores, 0.0)
        assert result == ["B", "C", "A"]

    def test_tie_breaking_lexicographic(self):
        scores = {"Z": 1.0, "A": 1.0, "M": 1.0}
        result = filter_by_threshold(["Z", "A", "M"], scores, 1.0)
        assert result == ["A", "M", "Z"]

    def test_empty_candidates(self):
        result = filter_by_threshold([], {"A": 1.0}, 0.0)
        assert result == []

    def test_negative_threshold(self):
        scores = {"A": -1.0, "B": -5.0}
        result = filter_by_threshold(["A", "B"], scores, -3.0)
        assert result == ["A"]

    def test_determinism(self):
        scores = {"A": 1.0, "B": 2.0, "C": 3.0}
        r1 = filter_by_threshold(["A", "B", "C"], scores, 1.0)
        r2 = filter_by_threshold(["A", "B", "C"], scores, 1.0)
        assert r1 == r2


# ===================================================================
# TestSelectTopN
# ===================================================================

class TestSelectTopN:
    def test_basic_top_n(self):
        scores = {"A": 1.0, "B": 3.0, "C": 2.0}
        result = select_top_n(["A", "B", "C"], scores, 2)
        assert result == ["B", "C"]

    def test_n_zero(self):
        scores = {"A": 1.0}
        result = select_top_n(["A"], scores, 0)
        assert result == []

    def test_n_exceeds_length(self):
        scores = {"A": 1.0, "B": 2.0}
        result = select_top_n(["A", "B"], scores, 10)
        assert result == ["B", "A"]

    def test_n_negative_raises(self):
        with pytest.raises(ValueError, match="n must be >= 0"):
            select_top_n(["A"], {"A": 1.0}, -1)

    def test_n_equals_length(self):
        scores = {"A": 1.0, "B": 2.0}
        result = select_top_n(["A", "B"], scores, 2)
        assert result == ["B", "A"]

    def test_tie_breaking(self):
        scores = {"Z": 1.0, "A": 1.0}
        result = select_top_n(["Z", "A"], scores, 1)
        assert result == ["A"]

    def test_empty_candidates(self):
        result = select_top_n([], {}, 5)
        assert result == []

    def test_determinism(self):
        scores = {"A": 1.0, "B": 2.0, "C": 3.0}
        r1 = select_top_n(["A", "B", "C"], scores, 2)
        r2 = select_top_n(["A", "B", "C"], scores, 2)
        assert r1 == r2


# ===================================================================
# TestSafeExtractors
# ===================================================================

class TestSafeExtractors:
    def test_safe_cagr_present(self):
        assert _safe_cagr({"cagr": 0.15}) == 0.15

    def test_safe_cagr_missing(self):
        assert _safe_cagr({}) == 0.0

    def test_safe_sharpe_present(self):
        assert _safe_sharpe({"sharpe_ratio": 1.5}) == 1.5

    def test_safe_sharpe_missing(self):
        assert _safe_sharpe({}) == 0.0

    def test_safe_max_drawdown_present(self):
        assert _safe_max_drawdown({"max_drawdown": 0.2}) == 0.2

    def test_safe_max_drawdown_missing(self):
        assert _safe_max_drawdown({}) == 1.0


# ===================================================================
# TestComputeScoreTuple
# ===================================================================

class TestComputeScoreTuple:
    def test_basic_score_tuple(self):
        agg = {"sharpe_ratio": 1.5, "cagr": 0.1, "max_drawdown": 0.2}
        result = _compute_score_tuple(agg)
        assert result == (1.5, 0.1, -0.2)

    def test_empty_aggregate(self):
        result = _compute_score_tuple({})
        assert result == (0.0, 0.0, -1.0)

    def test_ordering_sharpe_first(self):
        a = _compute_score_tuple({"sharpe_ratio": 2.0, "cagr": 0.05, "max_drawdown": 0.3})
        b = _compute_score_tuple({"sharpe_ratio": 1.0, "cagr": 0.10, "max_drawdown": 0.1})
        assert a > b

    def test_ordering_cagr_second(self):
        a = _compute_score_tuple({"sharpe_ratio": 1.0, "cagr": 0.10, "max_drawdown": 0.3})
        b = _compute_score_tuple({"sharpe_ratio": 1.0, "cagr": 0.05, "max_drawdown": 0.1})
        assert a > b

    def test_ordering_drawdown_third(self):
        a = _compute_score_tuple({"sharpe_ratio": 1.0, "cagr": 0.10, "max_drawdown": 0.1})
        b = _compute_score_tuple({"sharpe_ratio": 1.0, "cagr": 0.10, "max_drawdown": 0.3})
        assert a > b


# ===================================================================
# TestRunSelectionValidation
# ===================================================================

class TestRunSelectionValidation:
    def test_top_n_zero_raises(self):
        with pytest.raises(ValueError, match="top_n must be >= 1"):
            run_selection([_make_opt_entry(20, 1, 0.2)], top_n=0)

    def test_top_n_negative_raises(self):
        with pytest.raises(ValueError, match="top_n must be >= 1"):
            run_selection([_make_opt_entry(20, 1, 0.2)], top_n=-1)

    def test_empty_optimization_output_raises(self):
        with pytest.raises(ValueError, match="optimization_output must not be empty"):
            run_selection([])

    def test_valid_single_entry(self):
        result = run_selection([_make_opt_entry(20, 1, 0.2)])
        assert "ranking" in result
        assert len(result["ranking"]) == 1


# ===================================================================
# TestRunSelectionOutputStructure
# ===================================================================

class TestRunSelectionOutputStructure:
    def setup_method(self):
        self.opt = _make_opt_output(
            (20, 1, 0.1, 0.10, 1.5, 0.15),
            (30, 2, 0.2, 0.08, 1.2, 0.10),
            (40, 3, 0.3, 0.12, 1.8, 0.20),
        )
        self.result = run_selection(self.opt)

    def test_top_level_keys(self):
        assert set(self.result.keys()) == {"best_params", "best_score", "ranking"}

    def test_best_params_has_required_keys(self):
        bp = self.result["best_params"]
        assert "window" in bp
        assert "step" in bp
        assert "meta_uncertainty" in bp

    def test_best_score_is_dict(self):
        assert isinstance(self.result["best_score"], dict)

    def test_ranking_is_list(self):
        assert isinstance(self.result["ranking"], list)

    def test_ranking_entries_have_required_keys(self):
        for entry in self.result["ranking"]:
            assert "window" in entry
            assert "step" in entry
            assert "meta_uncertainty" in entry
            assert "aggregate" in entry
            assert "score_tuple" in entry

    def test_ranking_aggregate_has_enriched_keys(self):
        for entry in self.result["ranking"]:
            agg = entry["aggregate"]
            assert "mean_cagr" in agg
            assert "mean_sharpe" in agg
            assert "worst_max_drawdown" in agg

    def test_score_tuple_is_tuple_of_three(self):
        for entry in self.result["ranking"]:
            st = entry["score_tuple"]
            assert isinstance(st, tuple)
            assert len(st) == 3

    def test_best_params_matches_ranking_first(self):
        bp = self.result["best_params"]
        first = self.result["ranking"][0]
        assert bp["window"] == first["window"]
        assert bp["step"] == first["step"]
        assert bp["meta_uncertainty"] == first["meta_uncertainty"]


# ===================================================================
# TestRunSelectionRanking
# ===================================================================

class TestRunSelectionRanking:
    def test_ranked_by_sharpe_descending(self):
        opt = _make_opt_output(
            (20, 1, 0.1, 0.05, 1.0, 0.1),
            (30, 1, 0.1, 0.05, 3.0, 0.1),
            (40, 1, 0.1, 0.05, 2.0, 0.1),
        )
        result = run_selection(opt)
        windows = [e["window"] for e in result["ranking"]]
        assert windows == [30, 40, 20]

    def test_sharpe_tie_broken_by_cagr(self):
        opt = _make_opt_output(
            (20, 1, 0.1, 0.05, 1.0, 0.1),
            (30, 1, 0.1, 0.10, 1.0, 0.1),
        )
        result = run_selection(opt)
        windows = [e["window"] for e in result["ranking"]]
        assert windows == [30, 20]

    def test_sharpe_cagr_tie_broken_by_drawdown(self):
        opt = _make_opt_output(
            (20, 1, 0.1, 0.10, 1.0, 0.3),
            (30, 1, 0.1, 0.10, 1.0, 0.1),
        )
        result = run_selection(opt)
        windows = [e["window"] for e in result["ranking"]]
        assert windows == [30, 20]

    def test_full_tie_broken_by_window_step_meta(self):
        opt = _make_opt_output(
            (30, 1, 0.1, 0.10, 1.0, 0.1),
            (20, 1, 0.1, 0.10, 1.0, 0.1),
        )
        result = run_selection(opt)
        windows = [e["window"] for e in result["ranking"]]
        assert windows == [20, 30]

    def test_full_tie_broken_by_step(self):
        opt = _make_opt_output(
            (20, 3, 0.1, 0.10, 1.0, 0.1),
            (20, 1, 0.1, 0.10, 1.0, 0.1),
        )
        result = run_selection(opt)
        steps = [e["step"] for e in result["ranking"]]
        assert steps == [1, 3]

    def test_full_tie_broken_by_meta(self):
        opt = _make_opt_output(
            (20, 1, 0.5, 0.10, 1.0, 0.1),
            (20, 1, 0.1, 0.10, 1.0, 0.1),
        )
        result = run_selection(opt)
        metas = [e["meta_uncertainty"] for e in result["ranking"]]
        assert metas == [0.1, 0.5]

    def test_best_is_highest_sharpe(self):
        opt = _make_opt_output(
            (20, 1, 0.1, 0.05, 1.0, 0.1),
            (30, 1, 0.1, 0.05, 5.0, 0.1),
        )
        result = run_selection(opt)
        assert result["best_params"]["window"] == 30


# ===================================================================
# TestRunSelectionTopN
# ===================================================================

class TestRunSelectionTopN:
    def test_top_n_limits_ranking(self):
        opt = _make_opt_output(
            (20, 1, 0.1, 0.05, 1.0, 0.1),
            (30, 1, 0.1, 0.05, 2.0, 0.1),
            (40, 1, 0.1, 0.05, 3.0, 0.1),
        )
        result = run_selection(opt, top_n=2)
        assert len(result["ranking"]) == 2

    def test_top_n_exceeds_entries(self):
        opt = _make_opt_output(
            (20, 1, 0.1, 0.05, 1.0, 0.1),
        )
        result = run_selection(opt, top_n=100)
        assert len(result["ranking"]) == 1

    def test_top_n_one(self):
        opt = _make_opt_output(
            (20, 1, 0.1, 0.05, 1.0, 0.1),
            (30, 1, 0.1, 0.05, 2.0, 0.1),
        )
        result = run_selection(opt, top_n=1)
        assert len(result["ranking"]) == 1
        assert result["ranking"][0]["window"] == 30


# ===================================================================
# TestRunSelectionMinSharpe
# ===================================================================

class TestRunSelectionMinSharpe:
    def test_filters_below_min_sharpe(self):
        opt = _make_opt_output(
            (20, 1, 0.1, 0.05, 0.5, 0.1),
            (30, 1, 0.1, 0.05, 1.5, 0.1),
            (40, 1, 0.1, 0.05, 2.5, 0.1),
        )
        result = run_selection(opt, min_sharpe=1.0)
        assert len(result["ranking"]) == 2
        windows = [e["window"] for e in result["ranking"]]
        assert 20 not in windows

    def test_all_filtered_returns_empty_ranking(self):
        opt = _make_opt_output(
            (20, 1, 0.1, 0.05, 0.5, 0.1),
        )
        result = run_selection(opt, min_sharpe=10.0)
        assert result["ranking"] == []
        assert result["best_params"] == {}
        assert result["best_score"] == {}

    def test_inclusive_threshold(self):
        opt = _make_opt_output(
            (20, 1, 0.1, 0.05, 1.0, 0.1),
        )
        result = run_selection(opt, min_sharpe=1.0)
        assert len(result["ranking"]) == 1

    def test_default_no_filter(self):
        opt = _make_opt_output(
            (20, 1, 0.1, 0.05, -100.0, 0.1),
        )
        result = run_selection(opt)
        assert len(result["ranking"]) == 1


# ===================================================================
# TestRunSelectionEnrichment
# ===================================================================

class TestRunSelectionEnrichment:
    def test_mean_cagr_equals_cagr(self):
        opt = _make_opt_output((20, 1, 0.1, 0.15, 1.0, 0.1))
        result = run_selection(opt)
        agg = result["ranking"][0]["aggregate"]
        assert agg["mean_cagr"] == pytest.approx(0.15)

    def test_mean_sharpe_equals_sharpe(self):
        opt = _make_opt_output((20, 1, 0.1, 0.15, 2.5, 0.1))
        result = run_selection(opt)
        agg = result["ranking"][0]["aggregate"]
        assert agg["mean_sharpe"] == pytest.approx(2.5)

    def test_worst_max_drawdown_equals_mdd(self):
        opt = _make_opt_output((20, 1, 0.1, 0.15, 1.0, 0.25))
        result = run_selection(opt)
        agg = result["ranking"][0]["aggregate"]
        assert agg["worst_max_drawdown"] == pytest.approx(0.25)

    def test_original_keys_preserved(self):
        opt = _make_opt_output((20, 1, 0.1, 0.15, 1.0, 0.25))
        result = run_selection(opt)
        agg = result["ranking"][0]["aggregate"]
        assert "cagr" in agg
        assert "sharpe_ratio" in agg
        assert "max_drawdown" in agg


# ===================================================================
# TestRunSelectionDeterminism
# ===================================================================

class TestRunSelectionDeterminism:
    def test_identical_calls_identical_output(self):
        opt = _make_opt_output(
            (20, 1, 0.1, 0.05, 1.0, 0.1),
            (30, 2, 0.2, 0.08, 1.5, 0.2),
            (40, 3, 0.3, 0.12, 2.0, 0.15),
        )
        r1 = run_selection(opt, top_n=2, min_sharpe=0.5)
        r2 = run_selection(opt, top_n=2, min_sharpe=0.5)
        assert r1["ranking"] == r2["ranking"]
        assert r1["best_params"] == r2["best_params"]

    def test_input_not_mutated(self):
        opt = _make_opt_output(
            (20, 1, 0.1, 0.05, 1.0, 0.1),
            (30, 2, 0.2, 0.08, 1.5, 0.2),
        )
        original = copy.deepcopy(opt)
        run_selection(opt)
        assert opt == original


# ===================================================================
# TestRunSelectionRobustnessCompat
# ===================================================================

class TestRunSelectionRobustnessCompat:
    def test_ranking_has_aggregate_with_mean_cagr(self):
        opt = _make_opt_output(
            (20, 1, 0.1, 0.10, 1.0, 0.1),
            (30, 1, 0.1, 0.08, 0.9, 0.1),
        )
        result = run_selection(opt)
        for entry in result["ranking"]:
            assert "mean_cagr" in entry["aggregate"]
            assert isinstance(entry["aggregate"]["mean_cagr"], float)

    def test_ranking_has_aggregate_with_mean_sharpe(self):
        opt = _make_opt_output(
            (20, 1, 0.1, 0.10, 1.0, 0.1),
        )
        result = run_selection(opt)
        assert "mean_sharpe" in result["ranking"][0]["aggregate"]

    def test_ranking_has_aggregate_with_worst_max_drawdown(self):
        opt = _make_opt_output(
            (20, 1, 0.1, 0.10, 1.0, 0.1),
        )
        result = run_selection(opt)
        assert "worst_max_drawdown" in result["ranking"][0]["aggregate"]

    def test_best_params_has_all_keys(self):
        opt = _make_opt_output((20, 1, 0.1, 0.10, 1.0, 0.1))
        result = run_selection(opt)
        bp = result["best_params"]
        assert set(bp.keys()) == {"window", "step", "meta_uncertainty"}

    def test_end_to_end_with_evaluate_robustness(self):
        from jarvis.robustness.engine import evaluate_robustness
        opt = _make_opt_output(
            (20, 1, 0.1, 0.10, 1.5, 0.15),
            (30, 2, 0.2, 0.08, 1.2, 0.10),
            (40, 3, 0.3, 0.12, 1.8, 0.20),
        )
        sel = run_selection(opt)
        rob = evaluate_robustness(sel)
        assert "robustness_score" in rob
        assert "best_params" in rob
        assert "stability_metrics" in rob
        assert isinstance(rob["robustness_score"], float)


# ===================================================================
# TestModuleAll
# ===================================================================

class TestModuleAll:
    def test_contains_rank_candidates(self):
        from jarvis.selection import engine
        assert "rank_candidates" in engine.__all__

    def test_contains_filter_by_threshold(self):
        from jarvis.selection import engine
        assert "filter_by_threshold" in engine.__all__

    def test_contains_select_top_n(self):
        from jarvis.selection import engine
        assert "select_top_n" in engine.__all__

    def test_contains_run_selection(self):
        from jarvis.selection import engine
        assert "run_selection" in engine.__all__

    def test_all_length(self):
        from jarvis.selection import engine
        assert len(engine.__all__) == 4
