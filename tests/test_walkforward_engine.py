# =============================================================================
# Unit Tests for jarvis/walkforward/engine.py
# =============================================================================

import copy
import pytest

from jarvis.walkforward.engine import (
    WalkForwardWindow,
    generate_windows,
    run_walkforward,
)


# ===================================================================
# TestWalkForwardWindow
# ===================================================================

class TestWalkForwardWindow:
    def test_creation(self):
        w = WalkForwardWindow(fold=0, train_start=0, train_end=10, test_start=10, test_end=15)
        assert w.fold == 0
        assert w.train_start == 0
        assert w.train_end == 10
        assert w.test_start == 10
        assert w.test_end == 15

    def test_frozen(self):
        w = WalkForwardWindow(fold=0, train_start=0, train_end=10, test_start=10, test_end=15)
        with pytest.raises(AttributeError):
            w.fold = 1

    def test_equality(self):
        a = WalkForwardWindow(fold=0, train_start=0, train_end=10, test_start=10, test_end=15)
        b = WalkForwardWindow(fold=0, train_start=0, train_end=10, test_start=10, test_end=15)
        assert a == b

    def test_inequality(self):
        a = WalkForwardWindow(fold=0, train_start=0, train_end=10, test_start=10, test_end=15)
        b = WalkForwardWindow(fold=1, train_start=0, train_end=10, test_start=10, test_end=15)
        assert a != b


# ===================================================================
# TestGenerateWindowsValidation
# ===================================================================

class TestGenerateWindowsValidation:
    def test_n_zero_raises(self):
        with pytest.raises(ValueError, match="n must be >= 1"):
            generate_windows(0, 5, 5, 1)

    def test_n_negative_raises(self):
        with pytest.raises(ValueError, match="n must be >= 1"):
            generate_windows(-1, 5, 5, 1)

    def test_train_size_zero_raises(self):
        with pytest.raises(ValueError, match="train_size must be >= 1"):
            generate_windows(100, 0, 5, 1)

    def test_train_size_negative_raises(self):
        with pytest.raises(ValueError, match="train_size must be >= 1"):
            generate_windows(100, -1, 5, 1)

    def test_test_size_zero_raises(self):
        with pytest.raises(ValueError, match="test_size must be >= 1"):
            generate_windows(100, 5, 0, 1)

    def test_test_size_negative_raises(self):
        with pytest.raises(ValueError, match="test_size must be >= 1"):
            generate_windows(100, 5, -1, 1)

    def test_step_zero_raises(self):
        with pytest.raises(ValueError, match="step must be >= 1"):
            generate_windows(100, 5, 5, 0)

    def test_step_negative_raises(self):
        with pytest.raises(ValueError, match="step must be >= 1"):
            generate_windows(100, 5, 5, -1)


# ===================================================================
# TestGenerateWindowsBehavior
# ===================================================================

class TestGenerateWindowsBehavior:
    def test_single_window(self):
        # n=10, train=5, test=5, step=1 -> first window fits exactly
        windows = generate_windows(10, 5, 5, 1)
        assert len(windows) >= 1
        w = windows[0]
        assert w.fold == 0
        assert w.train_start == 0
        assert w.train_end == 5
        assert w.test_start == 5
        assert w.test_end == 10

    def test_exact_fit_single(self):
        # Exactly one window: n=10, train=5, test=5, step=10
        windows = generate_windows(10, 5, 5, 10)
        assert len(windows) == 1

    def test_no_window_when_too_short(self):
        # n=5 but train+test = 6 -> no window fits
        windows = generate_windows(5, 3, 3, 1)
        assert windows == []

    def test_multiple_windows_step_one(self):
        # n=12, train=5, test=5, step=1
        # fold 0: train[0:5], test[5:10]
        # fold 1: train[1:6], test[6:11]
        # fold 2: train[2:7], test[7:12]
        # fold 3: train[3:8], test[8:13] -> exceeds n=12
        windows = generate_windows(12, 5, 5, 1)
        assert len(windows) == 3

    def test_multiple_windows_step_two(self):
        # n=20, train=5, test=5, step=2
        # fold 0: train[0:5], test[5:10]
        # fold 1: train[2:7], test[7:12]
        # fold 2: train[4:9], test[9:14]
        # fold 3: train[6:11], test[11:16]
        # fold 4: train[8:13], test[13:18]
        # fold 5: train[10:15], test[15:20]
        # fold 6: train[12:17], test[17:22] -> exceeds
        windows = generate_windows(20, 5, 5, 2)
        assert len(windows) == 6

    def test_fold_indices_sequential(self):
        windows = generate_windows(30, 10, 5, 3)
        for i, w in enumerate(windows):
            assert w.fold == i

    def test_train_test_contiguous(self):
        windows = generate_windows(50, 10, 5, 5)
        for w in windows:
            assert w.test_start == w.train_end

    def test_train_size_correct(self):
        windows = generate_windows(50, 10, 5, 5)
        for w in windows:
            assert w.train_end - w.train_start == 10

    def test_test_size_correct(self):
        windows = generate_windows(50, 10, 5, 5)
        for w in windows:
            assert w.test_end - w.test_start == 5

    def test_step_advances_train_start(self):
        windows = generate_windows(50, 10, 5, 3)
        for i in range(1, len(windows)):
            assert windows[i].train_start == windows[i - 1].train_start + 3

    def test_test_end_never_exceeds_n(self):
        n = 25
        windows = generate_windows(n, 8, 4, 2)
        for w in windows:
            assert w.test_end <= n

    def test_large_step_single_window(self):
        windows = generate_windows(100, 10, 5, 100)
        assert len(windows) == 1

    def test_train_plus_test_equals_n(self):
        windows = generate_windows(10, 5, 5, 1)
        # First window covers exactly [0:10]
        assert windows[0].train_start == 0
        assert windows[0].test_end == 10

    def test_n_equals_one_fails_for_normal_sizes(self):
        # n=1 with train=1, test=1 needs 2 points
        windows = generate_windows(1, 1, 1, 1)
        assert windows == []

    def test_n_equals_two_minimal(self):
        windows = generate_windows(2, 1, 1, 1)
        assert len(windows) == 1
        w = windows[0]
        assert w.train_start == 0
        assert w.train_end == 1
        assert w.test_start == 1
        assert w.test_end == 2


# ===================================================================
# TestGenerateWindowsDeterminism
# ===================================================================

class TestGenerateWindowsDeterminism:
    def test_identical_calls(self):
        r1 = generate_windows(50, 10, 5, 3)
        r2 = generate_windows(50, 10, 5, 3)
        assert r1 == r2

    def test_returns_fresh_list(self):
        r1 = generate_windows(20, 5, 5, 2)
        r2 = generate_windows(20, 5, 5, 2)
        assert r1 is not r2


# ===================================================================
# TestRunWalkforwardValidation
# ===================================================================

class TestRunWalkforwardValidation:
    def test_propagates_validation_errors(self):
        with pytest.raises(ValueError, match="train_size must be >= 1"):
            run_walkforward([1, 2, 3], 0, 1, 1, lambda tr, te: {})

    def test_empty_data_raises(self):
        with pytest.raises(ValueError, match="n must be >= 1"):
            run_walkforward([], 1, 1, 1, lambda tr, te: {})


# ===================================================================
# TestRunWalkforwardBehavior
# ===================================================================

class TestRunWalkforwardBehavior:
    def test_basic_run(self):
        data = list(range(20))
        results = run_walkforward(
            data, train_size=5, test_size=5, step=5,
            evaluate_fn=lambda tr, te: {"train_sum": sum(tr), "test_sum": sum(te)},
        )
        assert len(results) >= 1

    def test_fold_index_in_results(self):
        data = list(range(20))
        results = run_walkforward(
            data, train_size=5, test_size=5, step=5,
            evaluate_fn=lambda tr, te: {},
        )
        for i, r in enumerate(results):
            assert r["fold"] == i

    def test_window_in_results(self):
        data = list(range(20))
        results = run_walkforward(
            data, train_size=5, test_size=5, step=5,
            evaluate_fn=lambda tr, te: {},
        )
        for r in results:
            assert isinstance(r["window"], WalkForwardWindow)

    def test_evaluate_fn_results_merged(self):
        data = list(range(20))
        results = run_walkforward(
            data, train_size=5, test_size=5, step=5,
            evaluate_fn=lambda tr, te: {"metric_a": 42, "metric_b": "ok"},
        )
        for r in results:
            assert r["metric_a"] == 42
            assert r["metric_b"] == "ok"

    def test_correct_slicing(self):
        data = list(range(20))
        captured = []

        def capture_fn(train, test):
            captured.append((list(train), list(test)))
            return {}

        run_walkforward(data, train_size=5, test_size=3, step=3, evaluate_fn=capture_fn)
        # fold 0: train=[0,1,2,3,4], test=[5,6,7]
        assert captured[0] == ([0, 1, 2, 3, 4], [5, 6, 7])
        # fold 1: train=[3,4,5,6,7], test=[8,9,10]
        assert captured[1] == ([3, 4, 5, 6, 7], [8, 9, 10])

    def test_no_folds_returns_empty(self):
        data = [1, 2]
        results = run_walkforward(
            data, train_size=5, test_size=5, step=1,
            evaluate_fn=lambda tr, te: {},
        )
        assert results == []

    def test_number_of_folds_matches_generate_windows(self):
        data = list(range(50))
        windows = generate_windows(len(data), 10, 5, 3)
        results = run_walkforward(
            data, train_size=10, test_size=5, step=3,
            evaluate_fn=lambda tr, te: {},
        )
        assert len(results) == len(windows)

    def test_train_slice_length(self):
        data = list(range(30))
        results = run_walkforward(
            data, train_size=8, test_size=4, step=4,
            evaluate_fn=lambda tr, te: {"train_len": len(tr), "test_len": len(te)},
        )
        for r in results:
            assert r["train_len"] == 8
            assert r["test_len"] == 4

    def test_window_matches_fold(self):
        data = list(range(30))
        results = run_walkforward(
            data, train_size=8, test_size=4, step=4,
            evaluate_fn=lambda tr, te: {},
        )
        for r in results:
            assert r["window"].fold == r["fold"]


# ===================================================================
# TestRunWalkforwardDeterminism
# ===================================================================

class TestRunWalkforwardDeterminism:
    def test_identical_calls(self):
        data = list(range(30))
        fn = lambda tr, te: {"s": sum(tr) + sum(te)}
        r1 = run_walkforward(data, 10, 5, 3, fn)
        r2 = run_walkforward(data, 10, 5, 3, fn)
        assert len(r1) == len(r2)
        for a, b in zip(r1, r2):
            assert a["fold"] == b["fold"]
            assert a["window"] == b["window"]
            assert a["s"] == b["s"]

    def test_input_not_mutated(self):
        data = list(range(30))
        original = list(data)
        run_walkforward(data, 10, 5, 3, lambda tr, te: {})
        assert data == original


# ===================================================================
# TestRunWalkforwardEdgeCases
# ===================================================================

class TestRunWalkforwardEdgeCases:
    def test_step_equals_test_size(self):
        # Non-overlapping test windows
        data = list(range(20))
        results = run_walkforward(
            data, train_size=5, test_size=5, step=5,
            evaluate_fn=lambda tr, te: {"test": list(te)},
        )
        # Verify test windows don't overlap
        all_test_indices = []
        for r in results:
            w = r["window"]
            all_test_indices.extend(range(w.test_start, w.test_end))
        assert len(all_test_indices) == len(set(all_test_indices))

    def test_step_one_maximum_overlap(self):
        data = list(range(12))
        results = run_walkforward(
            data, train_size=5, test_size=5, step=1,
            evaluate_fn=lambda tr, te: {},
        )
        # Same as generate_windows(12, 5, 5, 1) = 3 folds
        assert len(results) == 3

    def test_string_data(self):
        data = list("abcdefghijklmnop")
        results = run_walkforward(
            data, train_size=4, test_size=3, step=3,
            evaluate_fn=lambda tr, te: {"train": "".join(tr), "test": "".join(te)},
        )
        assert results[0]["train"] == "abcd"
        assert results[0]["test"] == "efg"

    def test_tuple_data(self):
        data = tuple(range(20))
        results = run_walkforward(
            data, train_size=5, test_size=5, step=5,
            evaluate_fn=lambda tr, te: {"n": len(tr)},
        )
        assert len(results) >= 1
        assert results[0]["n"] == 5


# ===================================================================
# TestModuleAll
# ===================================================================

class TestModuleAll:
    def test_contains_walkforwardwindow(self):
        from jarvis.walkforward import engine
        assert "WalkForwardWindow" in engine.__all__

    def test_contains_generate_windows(self):
        from jarvis.walkforward import engine
        assert "generate_windows" in engine.__all__

    def test_contains_run_walkforward(self):
        from jarvis.walkforward import engine
        assert "run_walkforward" in engine.__all__

    def test_all_length(self):
        from jarvis.walkforward import engine
        assert len(engine.__all__) == 3

    def test_init_exports_walkforwardwindow(self):
        from jarvis.walkforward import WalkForwardWindow as W
        assert W is WalkForwardWindow

    def test_init_exports_generate_windows(self):
        from jarvis.walkforward import generate_windows as gw
        assert gw is generate_windows


# ===================================================================
# TestRunWalkforwardOverfittingDetection
# ===================================================================

class TestRunWalkforwardOverfittingDetection:
    """Tests for optional overfitting detection in run_walkforward."""

    def test_default_no_overfitting_key(self):
        """Without detect_overfitting=True, no report is added."""
        data = list(range(20))
        results = run_walkforward(
            data, train_size=5, test_size=5, step=5,
            evaluate_fn=lambda tr, te: {"is_sharpe": 2.0, "oos_sharpe": 1.0},
        )
        for r in results:
            assert "overfitting_report" not in r

    def test_detect_overfitting_adds_report(self):
        """With detect_overfitting=True and sharpe keys, report is added."""
        data = list(range(20))
        results = run_walkforward(
            data, train_size=5, test_size=5, step=5,
            evaluate_fn=lambda tr, te: {"is_sharpe": 2.0, "oos_sharpe": 1.0},
            detect_overfitting=True,
        )
        for r in results:
            assert "overfitting_report" in r
            report = r["overfitting_report"]
            assert report is not None
            assert isinstance(report.overfitting_flag, bool)

    def test_detect_overfitting_no_sharpe_keys_gives_none(self):
        """If evaluate_fn doesn't return sharpe keys, report is None."""
        data = list(range(20))
        results = run_walkforward(
            data, train_size=5, test_size=5, step=5,
            evaluate_fn=lambda tr, te: {"metric": 42},
            detect_overfitting=True,
        )
        for r in results:
            assert r["overfitting_report"] is None

    def test_detect_overfitting_high_spike(self):
        """IS/OOS ratio > 3.0 should flag overfitting."""
        data = list(range(20))
        results = run_walkforward(
            data, train_size=5, test_size=5, step=5,
            evaluate_fn=lambda tr, te: {"is_sharpe": 10.0, "oos_sharpe": 1.0},
            detect_overfitting=True,
        )
        for r in results:
            report = r["overfitting_report"]
            assert report is not None
            assert report.performance_spike is True
            assert report.overfitting_flag is True

    def test_detect_overfitting_no_spike(self):
        """IS/OOS ratio <= 3.0 should not flag performance spike."""
        data = list(range(20))
        results = run_walkforward(
            data, train_size=5, test_size=5, step=5,
            evaluate_fn=lambda tr, te: {"is_sharpe": 1.5, "oos_sharpe": 1.0},
            detect_overfitting=True,
        )
        for r in results:
            report = r["overfitting_report"]
            assert report is not None
            assert report.performance_spike is False
            assert report.overfitting_flag is False

    def test_detect_overfitting_uses_sensitivity_score(self):
        """If evaluate_fn provides sensitivity_score, it is used."""
        data = list(range(20))
        results = run_walkforward(
            data, train_size=5, test_size=5, step=5,
            evaluate_fn=lambda tr, te: {
                "is_sharpe": 1.0, "oos_sharpe": 1.0,
                "sensitivity_score": 0.8,
            },
            detect_overfitting=True,
        )
        for r in results:
            report = r["overfitting_report"]
            assert report is not None
            assert report.sensitivity_score == 0.8
            assert report.param_sensitivity is True
            assert report.overfitting_flag is True

    def test_detect_overfitting_strategy_id(self):
        """Strategy ID should contain fold index."""
        data = list(range(20))
        results = run_walkforward(
            data, train_size=5, test_size=5, step=5,
            evaluate_fn=lambda tr, te: {"is_sharpe": 1.0, "oos_sharpe": 1.0},
            detect_overfitting=True,
        )
        for r in results:
            report = r["overfitting_report"]
            assert report is not None
            assert report.strategy_id == f"walkforward_fold_{r['fold']}"

    def test_detect_overfitting_deterministic(self):
        """Same inputs produce same overfitting reports."""
        data = list(range(30))
        fn = lambda tr, te: {"is_sharpe": 2.5, "oos_sharpe": 0.5}
        r1 = run_walkforward(data, 10, 5, 5, fn, detect_overfitting=True)
        r2 = run_walkforward(data, 10, 5, 5, fn, detect_overfitting=True)
        for a, b in zip(r1, r2):
            assert a["overfitting_report"] == b["overfitting_report"]

    def test_detect_overfitting_empty_folds(self):
        """No folds -> empty list, no crash."""
        data = [1, 2]
        results = run_walkforward(
            data, train_size=5, test_size=5, step=1,
            evaluate_fn=lambda tr, te: {"is_sharpe": 1.0, "oos_sharpe": 1.0},
            detect_overfitting=True,
        )
        assert results == []

    def test_backward_compatible_without_flag(self):
        """Existing calls without detect_overfitting still work."""
        data = list(range(20))
        results = run_walkforward(
            data, train_size=5, test_size=5, step=5,
            evaluate_fn=lambda tr, te: {"sum": sum(tr)},
        )
        assert len(results) >= 1
        assert "overfitting_report" not in results[0]
