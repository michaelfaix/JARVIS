# =============================================================================
# tests/unit/core/test_trading_calendar.py
# =============================================================================
#
# Comprehensive tests for jarvis/core/trading_calendar.py:
#   - is_trading_day() pure function
#   - Fixed holiday lists (NYSE, CME, EUREX)
#   - Weekend detection (pure arithmetic)
#   - Floating holidays (MLK, Presidents, Memorial, Labor, Thanksgiving, Easter)
#   - US observed-holiday rule (Sat->Fri, Sun->Mon)
#   - filter_trading_days, get_trading_day_mask, count_trading_days
#   - Integration: generate_trading_windows in walkforward
#   - Determinism (DET-01..DET-07)
#   - Import contract
#
# =============================================================================

import datetime

import pytest

from jarvis.core.trading_calendar import (
    EXCHANGE_CME,
    EXCHANGE_EUREX,
    EXCHANGE_NYSE,
    count_trading_days,
    filter_trading_days,
    get_trading_day_mask,
    is_trading_day,
)


# =============================================================================
# HELPERS
# =============================================================================

def _ord(year: int, month: int, day: int) -> int:
    """Shorthand for date ordinal."""
    return datetime.date(year, month, day).toordinal()


# =============================================================================
# SECTION 1 -- WEEKEND DETECTION
# =============================================================================

class TestWeekendDetection:
    """Weekends are never trading days on any exchange."""

    def test_saturday_nyse(self):
        assert is_trading_day(_ord(2024, 3, 2), EXCHANGE_NYSE) is False

    def test_sunday_nyse(self):
        assert is_trading_day(_ord(2024, 3, 3), EXCHANGE_NYSE) is False

    def test_saturday_cme(self):
        assert is_trading_day(_ord(2024, 3, 2), EXCHANGE_CME) is False

    def test_sunday_eurex(self):
        assert is_trading_day(_ord(2024, 3, 3), EXCHANGE_EUREX) is False

    def test_monday_is_trading_day(self):
        # Mon March 4, 2024 -- regular weekday, no holiday
        assert is_trading_day(_ord(2024, 3, 4), EXCHANGE_NYSE) is True

    def test_friday_is_trading_day(self):
        # Fri March 8, 2024 -- regular weekday
        assert is_trading_day(_ord(2024, 3, 8), EXCHANGE_NYSE) is True

    def test_full_week_pattern(self):
        """Mon-Fri trading, Sat-Sun not (non-holiday week)."""
        # Week of March 4-10, 2024 (no holidays)
        mon = _ord(2024, 3, 4)
        results = [is_trading_day(mon + i) for i in range(7)]
        assert results == [True, True, True, True, True, False, False]


# =============================================================================
# SECTION 2 -- NYSE FIXED HOLIDAYS
# =============================================================================

class TestNYSEFixedHolidays:
    """NYSE fixed holidays: New Year, Juneteenth, Independence Day, Christmas."""

    def test_new_years_day_2024(self):
        assert is_trading_day(_ord(2024, 1, 1), EXCHANGE_NYSE) is False

    def test_juneteenth_2024(self):
        # June 19, 2024 is a Wednesday
        assert is_trading_day(_ord(2024, 6, 19), EXCHANGE_NYSE) is False

    def test_independence_day_2024(self):
        # July 4, 2024 is a Thursday
        assert is_trading_day(_ord(2024, 7, 4), EXCHANGE_NYSE) is False

    def test_christmas_2024(self):
        # Dec 25, 2024 is a Wednesday
        assert is_trading_day(_ord(2024, 12, 25), EXCHANGE_NYSE) is False

    def test_day_after_christmas_nyse(self):
        # Dec 26, 2024 is a Thursday -- NYSE open
        assert is_trading_day(_ord(2024, 12, 26), EXCHANGE_NYSE) is True


# =============================================================================
# SECTION 3 -- NYSE OBSERVED HOLIDAY RULE
# =============================================================================

class TestNYSEObservedRule:
    """When a fixed holiday falls on Sat, observed Fri; on Sun, observed Mon."""

    def test_july_4_on_saturday_observed_friday(self):
        # July 4, 2026 is Saturday -> observed Friday July 3
        assert is_trading_day(_ord(2026, 7, 3), EXCHANGE_NYSE) is False
        # Saturday itself is already not a trading day (weekend)
        assert is_trading_day(_ord(2026, 7, 4), EXCHANGE_NYSE) is False

    def test_july_4_on_sunday_observed_monday(self):
        # July 4, 2027 is Sunday -> observed Monday July 5
        assert is_trading_day(_ord(2027, 7, 5), EXCHANGE_NYSE) is False

    def test_new_years_on_saturday_observed_friday(self):
        # Jan 1, 2028 is Saturday -> observed Friday Dec 31, 2027
        assert is_trading_day(_ord(2027, 12, 31), EXCHANGE_NYSE) is False

    def test_christmas_on_sunday_observed_monday(self):
        # Dec 25, 2033 is Sunday -> observed Monday Dec 26
        assert is_trading_day(_ord(2033, 12, 26), EXCHANGE_NYSE) is False


# =============================================================================
# SECTION 4 -- NYSE FLOATING HOLIDAYS
# =============================================================================

class TestNYSEFloatingHolidays:
    """MLK, Presidents, Good Friday, Memorial, Labor, Thanksgiving."""

    def test_mlk_day_2024(self):
        # 3rd Monday of January 2024 = Jan 15
        assert is_trading_day(_ord(2024, 1, 15), EXCHANGE_NYSE) is False

    def test_presidents_day_2024(self):
        # 3rd Monday of February 2024 = Feb 19
        assert is_trading_day(_ord(2024, 2, 19), EXCHANGE_NYSE) is False

    def test_good_friday_2024(self):
        # Easter 2024: March 31 -> Good Friday: March 29
        assert is_trading_day(_ord(2024, 3, 29), EXCHANGE_NYSE) is False

    def test_memorial_day_2024(self):
        # Last Monday of May 2024 = May 27
        assert is_trading_day(_ord(2024, 5, 27), EXCHANGE_NYSE) is False

    def test_labor_day_2024(self):
        # 1st Monday of September 2024 = Sep 2
        assert is_trading_day(_ord(2024, 9, 2), EXCHANGE_NYSE) is False

    def test_thanksgiving_2024(self):
        # 4th Thursday of November 2024 = Nov 28
        assert is_trading_day(_ord(2024, 11, 28), EXCHANGE_NYSE) is False

    def test_day_before_thanksgiving_is_trading(self):
        # Nov 27, 2024 (Wednesday) is a trading day
        assert is_trading_day(_ord(2024, 11, 27), EXCHANGE_NYSE) is True

    def test_good_friday_2025(self):
        # Easter 2025: April 20 -> Good Friday: April 18
        assert is_trading_day(_ord(2025, 4, 18), EXCHANGE_NYSE) is False

    def test_mlk_day_2025(self):
        # 3rd Monday of January 2025 = Jan 20
        assert is_trading_day(_ord(2025, 1, 20), EXCHANGE_NYSE) is False


# =============================================================================
# SECTION 5 -- CME HOLIDAYS
# =============================================================================

class TestCMEHolidays:
    """CME has same holiday structure as NYSE."""

    def test_christmas_2024(self):
        assert is_trading_day(_ord(2024, 12, 25), EXCHANGE_CME) is False

    def test_good_friday_2024(self):
        assert is_trading_day(_ord(2024, 3, 29), EXCHANGE_CME) is False

    def test_thanksgiving_2024(self):
        assert is_trading_day(_ord(2024, 11, 28), EXCHANGE_CME) is False

    def test_regular_day_cme(self):
        assert is_trading_day(_ord(2024, 3, 4), EXCHANGE_CME) is True

    def test_juneteenth_cme(self):
        assert is_trading_day(_ord(2024, 6, 19), EXCHANGE_CME) is False


# =============================================================================
# SECTION 6 -- EUREX HOLIDAYS
# =============================================================================

class TestEUREXHolidays:
    """EUREX has European holidays (Labour Day, Boxing Day, Easter Monday)."""

    def test_new_years_2024(self):
        assert is_trading_day(_ord(2024, 1, 1), EXCHANGE_EUREX) is False

    def test_labour_day_2024(self):
        # May 1, 2024 is a Wednesday
        assert is_trading_day(_ord(2024, 5, 1), EXCHANGE_EUREX) is False

    def test_christmas_eve_2024(self):
        # Dec 24, 2024 is a Tuesday
        assert is_trading_day(_ord(2024, 12, 24), EXCHANGE_EUREX) is False

    def test_christmas_2024(self):
        assert is_trading_day(_ord(2024, 12, 25), EXCHANGE_EUREX) is False

    def test_boxing_day_2024(self):
        # Dec 26, 2024 -- closed on EUREX
        assert is_trading_day(_ord(2024, 12, 26), EXCHANGE_EUREX) is False

    def test_new_years_eve_2024(self):
        # Dec 31, 2024 is a Tuesday -- closed on EUREX
        assert is_trading_day(_ord(2024, 12, 31), EXCHANGE_EUREX) is False

    def test_good_friday_eurex_2024(self):
        assert is_trading_day(_ord(2024, 3, 29), EXCHANGE_EUREX) is False

    def test_easter_monday_eurex_2024(self):
        # Easter Monday 2024: April 1
        assert is_trading_day(_ord(2024, 4, 1), EXCHANGE_EUREX) is False

    def test_regular_day_eurex(self):
        assert is_trading_day(_ord(2024, 3, 4), EXCHANGE_EUREX) is True

    def test_eurex_no_us_observed_rule(self):
        """EUREX does not shift holidays for Sat/Sun."""
        # May 1, 2027 is Saturday. EUREX holiday is on the actual date,
        # so Friday April 30 should be a trading day.
        assert is_trading_day(_ord(2027, 4, 30), EXCHANGE_EUREX) is True

    def test_eurex_no_mlk_day(self):
        """EUREX does not observe MLK Day."""
        # MLK Day 2024 = Jan 15 (Monday) -- EUREX should be open
        assert is_trading_day(_ord(2024, 1, 15), EXCHANGE_EUREX) is True

    def test_eurex_no_thanksgiving(self):
        """EUREX does not observe Thanksgiving."""
        assert is_trading_day(_ord(2024, 11, 28), EXCHANGE_EUREX) is True


# =============================================================================
# SECTION 7 -- EXCHANGE DIFFERENCES
# =============================================================================

class TestExchangeDifferences:
    """Same dates may differ across exchanges."""

    def test_boxing_day_nyse_vs_eurex(self):
        # Dec 26, 2024: NYSE open, EUREX closed
        assert is_trading_day(_ord(2024, 12, 26), EXCHANGE_NYSE) is True
        assert is_trading_day(_ord(2024, 12, 26), EXCHANGE_EUREX) is False

    def test_labour_day_may_1(self):
        # May 1, 2024: EUREX closed (Labour Day), NYSE/CME open
        assert is_trading_day(_ord(2024, 5, 1), EXCHANGE_NYSE) is True
        assert is_trading_day(_ord(2024, 5, 1), EXCHANGE_CME) is True
        assert is_trading_day(_ord(2024, 5, 1), EXCHANGE_EUREX) is False

    def test_christmas_eve(self):
        # Dec 24, 2024: NYSE/CME open, EUREX closed
        assert is_trading_day(_ord(2024, 12, 24), EXCHANGE_NYSE) is True
        assert is_trading_day(_ord(2024, 12, 24), EXCHANGE_EUREX) is False


# =============================================================================
# SECTION 8 -- INVALID EXCHANGE
# =============================================================================

class TestInvalidExchange:
    """Unknown exchange should raise ValueError."""

    def test_invalid_exchange_raises(self):
        with pytest.raises(ValueError, match="Unknown exchange"):
            is_trading_day(_ord(2024, 1, 2), "INVALID")

    def test_empty_exchange_raises(self):
        with pytest.raises(ValueError, match="Unknown exchange"):
            is_trading_day(_ord(2024, 1, 2), "")

    def test_lowercase_raises(self):
        with pytest.raises(ValueError, match="Unknown exchange"):
            is_trading_day(_ord(2024, 1, 2), "nyse")


# =============================================================================
# SECTION 9 -- DEFAULT EXCHANGE
# =============================================================================

class TestDefaultExchange:
    """is_trading_day defaults to NYSE."""

    def test_default_is_nyse(self):
        # Christmas 2024 -- closed on NYSE
        result_default = is_trading_day(_ord(2024, 12, 25))
        result_nyse = is_trading_day(_ord(2024, 12, 25), EXCHANGE_NYSE)
        assert result_default == result_nyse

    def test_default_regular_day(self):
        assert is_trading_day(_ord(2024, 3, 4)) is True


# =============================================================================
# SECTION 10 -- filter_trading_days
# =============================================================================

class TestFilterTradingDays:
    """filter_trading_days returns only trading day ordinals."""

    def test_filters_weekends(self):
        # Mon-Sun week of March 4-10, 2024
        mon = _ord(2024, 3, 4)
        ordinals = list(range(mon, mon + 7))
        result = filter_trading_days(ordinals)
        assert len(result) == 5
        assert all(is_trading_day(d) for d in result)

    def test_filters_holidays(self):
        # Week containing Christmas 2024 (Wed Dec 25)
        mon = _ord(2024, 12, 23)
        ordinals = list(range(mon, mon + 5))  # Mon-Fri
        result = filter_trading_days(ordinals)
        assert len(result) == 4  # Wed is Christmas
        assert _ord(2024, 12, 25) not in result

    def test_empty_input(self):
        assert filter_trading_days([]) == ()

    def test_all_weekends(self):
        sat = _ord(2024, 3, 2)
        sun = sat + 1
        assert filter_trading_days([sat, sun]) == ()


# =============================================================================
# SECTION 11 -- get_trading_day_mask
# =============================================================================

class TestGetTradingDayMask:
    """get_trading_day_mask returns tuple of bools."""

    def test_week_mask(self):
        mon = _ord(2024, 3, 4)
        ordinals = list(range(mon, mon + 7))
        mask = get_trading_day_mask(ordinals)
        assert mask == (True, True, True, True, True, False, False)

    def test_empty(self):
        assert get_trading_day_mask([]) == ()

    def test_holiday_in_mask(self):
        # Christmas week Mon-Fri
        ordinals = [_ord(2024, 12, 23 + i) for i in range(5)]
        mask = get_trading_day_mask(ordinals)
        # Wed Dec 25 is False
        assert mask[2] is False
        assert sum(mask) == 4


# =============================================================================
# SECTION 12 -- count_trading_days
# =============================================================================

class TestCountTradingDays:
    """count_trading_days counts trading days in [start, end)."""

    def test_full_week(self):
        # Mon-Fri = 5 trading days, exclusive end is next Monday
        mon = _ord(2024, 3, 4)
        next_mon = _ord(2024, 3, 11)
        assert count_trading_days(mon, next_mon) == 5

    def test_includes_weekend(self):
        # Mon through Sun (exclusive): range covers Mon-Sat = 5 weekdays
        mon = _ord(2024, 3, 4)
        sun = _ord(2024, 3, 10)
        # range(mon, sun) = Mon,Tue,Wed,Thu,Fri,Sat -> 5 trading days (Sat excluded)
        assert count_trading_days(mon, sun) == 5

    def test_two_weeks(self):
        mon1 = _ord(2024, 3, 4)
        mon3 = _ord(2024, 3, 18)
        assert count_trading_days(mon1, mon3) == 10

    def test_empty_range(self):
        d = _ord(2024, 3, 4)
        assert count_trading_days(d, d) == 0

    def test_holiday_reduces_count(self):
        # Week of Christmas 2024: Mon Dec 23 - Fri Dec 27 = 4 trading days
        mon = _ord(2024, 12, 23)
        sat = _ord(2024, 12, 28)
        assert count_trading_days(mon, sat) == 4


# =============================================================================
# SECTION 13 -- DETERMINISM
# =============================================================================

class TestDeterminism:
    """Same inputs always produce same outputs (DET-05)."""

    def test_is_trading_day_deterministic(self):
        d = _ord(2024, 7, 4)
        results = [is_trading_day(d, EXCHANGE_NYSE) for _ in range(100)]
        assert all(r is False for r in results)

    def test_filter_deterministic(self):
        ordinals = list(range(_ord(2024, 1, 1), _ord(2024, 2, 1)))
        r1 = filter_trading_days(ordinals)
        r2 = filter_trading_days(ordinals)
        assert r1 == r2

    def test_count_deterministic(self):
        s, e = _ord(2024, 1, 1), _ord(2024, 12, 31)
        c1 = count_trading_days(s, e)
        c2 = count_trading_days(s, e)
        assert c1 == c2

    def test_cross_year_consistency(self):
        """Holiday computation works across year boundaries."""
        # Dec 31, 2024 is a Tuesday -- trading day on NYSE
        assert is_trading_day(_ord(2024, 12, 31), EXCHANGE_NYSE) is True
        # Jan 1, 2025 is a Wednesday -- New Year's, not trading
        assert is_trading_day(_ord(2025, 1, 1), EXCHANGE_NYSE) is False


# =============================================================================
# SECTION 14 -- EASTER ALGORITHM CORRECTNESS
# =============================================================================

class TestEasterAlgorithm:
    """Verify Easter computation against known dates."""

    def test_easter_2024(self):
        # Easter 2024: March 31
        from jarvis.core.trading_calendar import _easter_ordinal
        assert _easter_ordinal(2024) == _ord(2024, 3, 31)

    def test_easter_2025(self):
        # Easter 2025: April 20
        from jarvis.core.trading_calendar import _easter_ordinal
        assert _easter_ordinal(2025) == _ord(2025, 4, 20)

    def test_easter_2026(self):
        # Easter 2026: April 5
        from jarvis.core.trading_calendar import _easter_ordinal
        assert _easter_ordinal(2026) == _ord(2026, 4, 5)

    def test_easter_2023(self):
        # Easter 2023: April 9
        from jarvis.core.trading_calendar import _easter_ordinal
        assert _easter_ordinal(2023) == _ord(2023, 4, 9)

    def test_easter_2030(self):
        # Easter 2030: April 21
        from jarvis.core.trading_calendar import _easter_ordinal
        assert _easter_ordinal(2030) == _ord(2030, 4, 21)


# =============================================================================
# SECTION 15 -- WEEKDAY ARITHMETIC
# =============================================================================

class TestWeekdayArithmetic:
    """Verify _weekday_from_ordinal correctness."""

    def test_known_monday(self):
        from jarvis.core.trading_calendar import _weekday_from_ordinal
        # March 4, 2024 is Monday
        assert _weekday_from_ordinal(_ord(2024, 3, 4)) == 0

    def test_known_friday(self):
        from jarvis.core.trading_calendar import _weekday_from_ordinal
        assert _weekday_from_ordinal(_ord(2024, 3, 8)) == 4

    def test_known_saturday(self):
        from jarvis.core.trading_calendar import _weekday_from_ordinal
        assert _weekday_from_ordinal(_ord(2024, 3, 9)) == 5

    def test_known_sunday(self):
        from jarvis.core.trading_calendar import _weekday_from_ordinal
        assert _weekday_from_ordinal(_ord(2024, 3, 10)) == 6

    def test_matches_datetime(self):
        """Weekday computation matches datetime.date.weekday()."""
        for offset in range(365):
            d = datetime.date(2024, 1, 1) + datetime.timedelta(days=offset)
            from jarvis.core.trading_calendar import _weekday_from_ordinal
            assert _weekday_from_ordinal(d.toordinal()) == d.weekday()


# =============================================================================
# SECTION 16 -- GENERATE TRADING WINDOWS INTEGRATION
# =============================================================================

class TestGenerateTradingWindows:
    """Integration: generate_trading_windows in walkforward engine."""

    def test_basic_windows(self):
        from jarvis.walkforward.engine import generate_trading_windows
        # 60 calendar days starting Jan 1, 2024
        start = _ord(2024, 1, 1)
        ordinals = list(range(start, start + 60))
        windows = generate_trading_windows(
            ordinals, train_days=10, test_days=5, step_days=5,
        )
        assert len(windows) > 0
        for w in windows:
            assert w.train_end > w.train_start
            assert w.test_end > w.test_start
            assert w.test_start >= w.train_end

    def test_windows_skip_weekends(self):
        from jarvis.walkforward.engine import generate_trading_windows
        # 30 calendar days
        start = _ord(2024, 3, 1)
        ordinals = list(range(start, start + 30))
        windows = generate_trading_windows(
            ordinals, train_days=5, test_days=3, step_days=3,
        )
        # Verify window boundaries reference trading days
        for w in windows:
            train_ord = ordinals[w.train_start]
            assert is_trading_day(train_ord, EXCHANGE_NYSE)
            test_ord = ordinals[w.test_start]
            assert is_trading_day(test_ord, EXCHANGE_NYSE)

    def test_empty_when_not_enough_trading_days(self):
        from jarvis.walkforward.engine import generate_trading_windows
        # Only 2 calendar days (weekend)
        sat = _ord(2024, 3, 2)
        ordinals = [sat, sat + 1]
        windows = generate_trading_windows(
            ordinals, train_days=1, test_days=1, step_days=1,
        )
        assert windows == []

    def test_eurex_exchange(self):
        from jarvis.walkforward.engine import generate_trading_windows
        start = _ord(2024, 1, 1)
        ordinals = list(range(start, start + 60))
        windows_nyse = generate_trading_windows(
            ordinals, train_days=10, test_days=5, step_days=5, exchange=EXCHANGE_NYSE,
        )
        windows_eurex = generate_trading_windows(
            ordinals, train_days=10, test_days=5, step_days=5, exchange=EXCHANGE_EUREX,
        )
        # Different holiday schedules may produce different window counts or bounds
        # Both should produce valid windows
        assert len(windows_nyse) > 0
        assert len(windows_eurex) > 0

    def test_deterministic_windows(self):
        from jarvis.walkforward.engine import generate_trading_windows
        start = _ord(2024, 1, 1)
        ordinals = list(range(start, start + 90))
        w1 = generate_trading_windows(ordinals, 20, 10, 10)
        w2 = generate_trading_windows(ordinals, 20, 10, 10)
        assert len(w1) == len(w2)
        for a, b in zip(w1, w2):
            assert a == b

    def test_validation_train_days(self):
        from jarvis.walkforward.engine import generate_trading_windows
        with pytest.raises(ValueError, match="train_days"):
            generate_trading_windows([1, 2, 3], train_days=0, test_days=1, step_days=1)

    def test_validation_test_days(self):
        from jarvis.walkforward.engine import generate_trading_windows
        with pytest.raises(ValueError, match="test_days"):
            generate_trading_windows([1, 2, 3], train_days=1, test_days=0, step_days=1)

    def test_validation_step_days(self):
        from jarvis.walkforward.engine import generate_trading_windows
        with pytest.raises(ValueError, match="step_days"):
            generate_trading_windows([1, 2, 3], train_days=1, test_days=1, step_days=0)

    def test_fold_indices_sequential(self):
        from jarvis.walkforward.engine import generate_trading_windows
        start = _ord(2024, 1, 1)
        ordinals = list(range(start, start + 90))
        windows = generate_trading_windows(ordinals, 10, 5, 5)
        for i, w in enumerate(windows):
            assert w.fold == i

    def test_window_indices_within_bounds(self):
        from jarvis.walkforward.engine import generate_trading_windows
        start = _ord(2024, 1, 1)
        ordinals = list(range(start, start + 60))
        windows = generate_trading_windows(ordinals, 10, 5, 5)
        for w in windows:
            assert w.train_start >= 0
            assert w.test_end <= len(ordinals)


# =============================================================================
# SECTION 17 -- IMPORT CONTRACT
# =============================================================================

class TestImportContract:
    """Verify all public symbols are importable."""

    def test_core_imports(self):
        from jarvis.core.trading_calendar import (
            EXCHANGE_NYSE,
            EXCHANGE_CME,
            EXCHANGE_EUREX,
            is_trading_day,
            filter_trading_days,
            get_trading_day_mask,
            count_trading_days,
        )
        assert EXCHANGE_NYSE == "NYSE"
        assert EXCHANGE_CME == "CME"
        assert EXCHANGE_EUREX == "EUREX"
        assert callable(is_trading_day)
        assert callable(filter_trading_days)
        assert callable(get_trading_day_mask)
        assert callable(count_trading_days)

    def test_walkforward_import(self):
        from jarvis.walkforward import generate_trading_windows
        assert callable(generate_trading_windows)

    def test_walkforward_engine_import(self):
        from jarvis.walkforward.engine import generate_trading_windows
        assert callable(generate_trading_windows)


# =============================================================================
# SECTION 18 -- ANNUAL TRADING DAY COUNTS
# =============================================================================

class TestAnnualTradingDays:
    """Sanity check: ~250-253 trading days per year on NYSE."""

    def test_2024_nyse_count(self):
        start = _ord(2024, 1, 1)
        end = _ord(2025, 1, 1)
        count = count_trading_days(start, end, EXCHANGE_NYSE)
        assert 248 <= count <= 253

    def test_2025_nyse_count(self):
        start = _ord(2025, 1, 1)
        end = _ord(2026, 1, 1)
        count = count_trading_days(start, end, EXCHANGE_NYSE)
        assert 248 <= count <= 253

    def test_eurex_fewer_than_nyse_possible(self):
        """EUREX may have different count due to different holidays."""
        start = _ord(2024, 1, 1)
        end = _ord(2025, 1, 1)
        nyse_count = count_trading_days(start, end, EXCHANGE_NYSE)
        eurex_count = count_trading_days(start, end, EXCHANGE_EUREX)
        # Both should be in reasonable range
        assert 245 <= eurex_count <= 255
        assert 245 <= nyse_count <= 255


# =============================================================================
# SECTION 19 -- MULTIPLE YEARS
# =============================================================================

class TestMultipleYears:
    """Verify calendar works across multiple years."""

    def test_thanksgiving_different_years(self):
        # Thanksgiving 2023: Nov 23 (4th Thursday)
        assert is_trading_day(_ord(2023, 11, 23), EXCHANGE_NYSE) is False
        # Thanksgiving 2025: Nov 27
        assert is_trading_day(_ord(2025, 11, 27), EXCHANGE_NYSE) is False

    def test_good_friday_different_years(self):
        # Good Friday 2023: April 7 (Easter April 9)
        assert is_trading_day(_ord(2023, 4, 7), EXCHANGE_NYSE) is False
        # Good Friday 2025: April 18 (Easter April 20)
        assert is_trading_day(_ord(2025, 4, 18), EXCHANGE_NYSE) is False

    def test_count_across_years(self):
        start = _ord(2023, 7, 1)
        end = _ord(2024, 7, 1)
        count = count_trading_days(start, end)
        assert 248 <= count <= 255
