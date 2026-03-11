# =============================================================================
# jarvis/core/trading_calendar.py -- Trading Calendar (Pure, Deterministic)
#
# Fixed holiday lists for NYSE, CME, EUREX as tuples (DET-06).
# is_trading_day(date_ordinal, exchange) is a pure function.
#
# =============================================================================
# FAS COMPLIANCE DECLARATION
# =============================================================================
#
# Dependency matrix:
#   trading_calendar.py -> datetime (stdlib only)
#
# DETERMINISM GUARANTEES: DET-01 through DET-07 enforced.
#   DET-01  No stochastic operations.
#   DET-02  All inputs passed explicitly.
#   DET-03  No side effects.
#   DET-05  Same inputs -> same outputs.
#   DET-06  Fixed literals (holiday definitions) not parametrizable.
#
# PROHIBITED ACTIONS CONFIRMED ABSENT:
#   PROHIBITED-01: No numpy. Pure stdlib.
#   PROHIBITED-02: No file I/O.
#   PROHIBITED-03: No logging/print.
#   PROHIBITED-05: No global mutable state.
#
# ASCII COMPLIANCE: All literals are 7-bit ASCII.
# =============================================================================

from __future__ import annotations

import datetime
from typing import Sequence, Tuple


# =============================================================================
# SECTION 1 -- EXCHANGE IDENTIFIERS (string constants)
# =============================================================================

EXCHANGE_NYSE: str = "NYSE"
EXCHANGE_CME: str = "CME"
EXCHANGE_EUREX: str = "EUREX"

_VALID_EXCHANGES: Tuple[str, ...] = (EXCHANGE_NYSE, EXCHANGE_CME, EXCHANGE_EUREX)


# =============================================================================
# SECTION 2 -- FIXED ANNUAL HOLIDAYS (DET-06: fixed literals)
# =============================================================================

# (month, day) tuples for holidays that fall on the same date every year.
# Floating holidays (MLK, Presidents, Memorial, Labor, Thanksgiving, Easter)
# are computed deterministically per year in Section 4.

_NYSE_FIXED_HOLIDAYS: Tuple[Tuple[int, int], ...] = (
    (1, 1),    # New Year's Day
    (6, 19),   # Juneteenth National Independence Day
    (7, 4),    # Independence Day
    (12, 25),  # Christmas Day
)

_CME_FIXED_HOLIDAYS: Tuple[Tuple[int, int], ...] = (
    (1, 1),    # New Year's Day
    (6, 19),   # Juneteenth National Independence Day
    (7, 4),    # Independence Day
    (12, 25),  # Christmas Day
)

_EUREX_FIXED_HOLIDAYS: Tuple[Tuple[int, int], ...] = (
    (1, 1),    # New Year's Day
    (5, 1),    # Labour Day
    (12, 24),  # Christmas Eve
    (12, 25),  # Christmas Day
    (12, 26),  # St Stephen's Day / Boxing Day
    (12, 31),  # New Year's Eve
)


# =============================================================================
# SECTION 3 -- PURE DATE ARITHMETIC HELPERS
# =============================================================================

def _weekday_from_ordinal(ordinal: int) -> int:
    """Weekday from ordinal. Monday=0 .. Sunday=6. Pure arithmetic."""
    # datetime.date(1, 1, 1).toordinal() == 1, weekday() == 0 (Monday)
    return (ordinal + 6) % 7


def _date_to_ordinal(year: int, month: int, day: int) -> int:
    """Convert (year, month, day) to ordinal via datetime.date (stdlib)."""
    return datetime.date(year, month, day).toordinal()


def _ordinal_to_ymd(ordinal: int) -> Tuple[int, int, int]:
    """Convert ordinal to (year, month, day)."""
    d = datetime.date.fromordinal(ordinal)
    return (d.year, d.month, d.day)


def _nth_weekday_of_month(year: int, month: int, weekday: int, n: int) -> int:
    """Ordinal of the nth occurrence of weekday in month (1-indexed).

    Args:
        year: Calendar year.
        month: Month (1-12).
        weekday: 0=Monday .. 6=Sunday.
        n: 1=first, 2=second, 3=third, 4=fourth.

    Returns:
        Ordinal of the nth weekday in the given month.
    """
    first_day_ord = _date_to_ordinal(year, month, 1)
    first_weekday = _weekday_from_ordinal(first_day_ord)
    offset = (weekday - first_weekday) % 7
    return first_day_ord + offset + 7 * (n - 1)


def _last_weekday_of_month(year: int, month: int, weekday: int) -> int:
    """Ordinal of the last occurrence of weekday in month."""
    if month == 12:
        next_month_ord = _date_to_ordinal(year + 1, 1, 1)
    else:
        next_month_ord = _date_to_ordinal(year, month + 1, 1)
    last_day_ord = next_month_ord - 1
    last_weekday = _weekday_from_ordinal(last_day_ord)
    offset = (last_weekday - weekday) % 7
    return last_day_ord - offset


def _easter_ordinal(year: int) -> int:
    """Easter Sunday ordinal via Meeus/Jones/Butcher algorithm.

    Deterministic integer-only computation. Valid for Gregorian calendar.
    """
    a = year % 19
    b = year // 100
    c = year % 100
    d = b // 4
    e = b % 4
    f = (b + 8) // 25
    g = (b - f + 1) // 3
    h = (19 * a + b - d - g + 15) % 30
    i = c // 4
    k = c % 4
    el = (32 + 2 * e + 2 * i - h - k) % 7
    m = (a + 11 * h + 22 * el) // 451
    month = (h + el - 7 * m + 114) // 31
    day = ((h + el - 7 * m + 114) % 31) + 1
    return _date_to_ordinal(year, month, day)


def _observed_holiday(ordinal: int) -> int:
    """US observed-holiday rule: Saturday->Friday, Sunday->Monday."""
    wd = _weekday_from_ordinal(ordinal)
    if wd == 5:  # Saturday -> observed on Friday
        return ordinal - 1
    if wd == 6:  # Sunday -> observed on Monday
        return ordinal + 1
    return ordinal


# =============================================================================
# SECTION 4 -- PER-YEAR HOLIDAY GENERATION (deterministic, per exchange)
# =============================================================================

def _nyse_holidays_for_year(year: int) -> Tuple[int, ...]:
    """All NYSE holiday ordinals for a given year (with observed rules)."""
    holidays = []

    # Fixed holidays with US observed adjustment
    for month, day in _NYSE_FIXED_HOLIDAYS:
        holidays.append(_observed_holiday(_date_to_ordinal(year, month, day)))

    # Martin Luther King Jr. Day: 3rd Monday of January
    holidays.append(_nth_weekday_of_month(year, 1, 0, 3))
    # Presidents' Day: 3rd Monday of February
    holidays.append(_nth_weekday_of_month(year, 2, 0, 3))
    # Good Friday: Easter Sunday - 2
    holidays.append(_easter_ordinal(year) - 2)
    # Memorial Day: Last Monday of May
    holidays.append(_last_weekday_of_month(year, 5, 0))
    # Labor Day: 1st Monday of September
    holidays.append(_nth_weekday_of_month(year, 9, 0, 1))
    # Thanksgiving: 4th Thursday of November
    holidays.append(_nth_weekday_of_month(year, 11, 3, 4))

    return tuple(sorted(set(holidays)))


def _cme_holidays_for_year(year: int) -> Tuple[int, ...]:
    """All CME holiday ordinals for a given year (with observed rules)."""
    holidays = []

    for month, day in _CME_FIXED_HOLIDAYS:
        holidays.append(_observed_holiday(_date_to_ordinal(year, month, day)))

    holidays.append(_nth_weekday_of_month(year, 1, 0, 3))   # MLK Day
    holidays.append(_nth_weekday_of_month(year, 2, 0, 3))   # Presidents' Day
    holidays.append(_easter_ordinal(year) - 2)               # Good Friday
    holidays.append(_last_weekday_of_month(year, 5, 0))      # Memorial Day
    holidays.append(_nth_weekday_of_month(year, 9, 0, 1))    # Labor Day
    holidays.append(_nth_weekday_of_month(year, 11, 3, 4))   # Thanksgiving

    return tuple(sorted(set(holidays)))


def _eurex_holidays_for_year(year: int) -> Tuple[int, ...]:
    """All EUREX holiday ordinals for a given year."""
    holidays = []

    # Fixed holidays (no US observed rule for EUREX)
    for month, day in _EUREX_FIXED_HOLIDAYS:
        holidays.append(_date_to_ordinal(year, month, day))

    # Good Friday: Easter Sunday - 2
    easter = _easter_ordinal(year)
    holidays.append(easter - 2)
    # Easter Monday: Easter Sunday + 1
    holidays.append(easter + 1)

    return tuple(sorted(set(holidays)))


def _get_holidays_for_year(year: int, exchange: str) -> Tuple[int, ...]:
    """Dispatch to exchange-specific holiday generator."""
    if exchange == EXCHANGE_NYSE:
        return _nyse_holidays_for_year(year)
    if exchange == EXCHANGE_CME:
        return _cme_holidays_for_year(year)
    if exchange == EXCHANGE_EUREX:
        return _eurex_holidays_for_year(year)
    raise ValueError(
        f"Unknown exchange: {exchange!r}. Valid exchanges: {_VALID_EXCHANGES}"
    )


# =============================================================================
# SECTION 5 -- PUBLIC API (pure functions)
# =============================================================================

def is_trading_day(
    date_ordinal: int,
    exchange: str = EXCHANGE_NYSE,
) -> bool:
    """Determine whether a date ordinal is a trading day.

    A trading day is a weekday (Mon-Fri) that is not a holiday for the
    specified exchange.

    Args:
        date_ordinal: Date as integer ordinal (datetime.date.toordinal()).
        exchange: Exchange identifier. One of "NYSE", "CME", "EUREX".

    Returns:
        True if the date is a trading day, False otherwise.

    Raises:
        ValueError: If exchange is not a recognized identifier.
    """
    if exchange not in _VALID_EXCHANGES:
        raise ValueError(
            f"Unknown exchange: {exchange!r}. "
            f"Valid exchanges: {_VALID_EXCHANGES}"
        )

    # Weekend check (pure arithmetic, no datetime needed)
    if _weekday_from_ordinal(date_ordinal) >= 5:
        return False

    # Holiday check: must check current year AND adjacent years because
    # observed-holiday shifts can cross year boundaries (e.g., Jan 1 on
    # Saturday is observed on Dec 31 of the previous year).
    year, _, _ = _ordinal_to_ymd(date_ordinal)
    holidays = _get_holidays_for_year(year, exchange)
    if date_ordinal in holidays:
        return False
    # Check if next year's holidays spill into this year (Dec 31 observed)
    holidays_next = _get_holidays_for_year(year + 1, exchange)
    if date_ordinal in holidays_next:
        return False
    # Check if previous year's holidays spill into this year (Jan 1 on Sun -> Jan 2)
    holidays_prev = _get_holidays_for_year(year - 1, exchange)
    if date_ordinal in holidays_prev:
        return False
    return True


def filter_trading_days(
    date_ordinals: Sequence[int],
    exchange: str = EXCHANGE_NYSE,
) -> Tuple[int, ...]:
    """Return only trading-day ordinals from the input sequence.

    Args:
        date_ordinals: Sequence of date ordinals.
        exchange: Exchange identifier.

    Returns:
        Tuple of ordinals that are trading days.
    """
    return tuple(d for d in date_ordinals if is_trading_day(d, exchange))


def get_trading_day_mask(
    date_ordinals: Sequence[int],
    exchange: str = EXCHANGE_NYSE,
) -> Tuple[bool, ...]:
    """Return a boolean mask indicating trading days.

    Args:
        date_ordinals: Sequence of date ordinals.
        exchange: Exchange identifier.

    Returns:
        Tuple of bools, True for trading days.
    """
    return tuple(is_trading_day(d, exchange) for d in date_ordinals)


def count_trading_days(
    start_ordinal: int,
    end_ordinal: int,
    exchange: str = EXCHANGE_NYSE,
) -> int:
    """Count trading days in [start_ordinal, end_ordinal) (exclusive end).

    Args:
        start_ordinal: Start date ordinal (inclusive).
        end_ordinal: End date ordinal (exclusive).
        exchange: Exchange identifier.

    Returns:
        Number of trading days in the range.
    """
    return sum(
        1 for d in range(start_ordinal, end_ordinal)
        if is_trading_day(d, exchange)
    )


__all__ = [
    "EXCHANGE_NYSE",
    "EXCHANGE_CME",
    "EXCHANGE_EUREX",
    "is_trading_day",
    "filter_trading_days",
    "get_trading_day_mask",
    "count_trading_days",
]
