"""Calendar-aware helpers for EPİAŞ date-limited services."""

from dataclasses import dataclass
from datetime import date, timedelta
from calendar import monthrange


@dataclass(frozen=True)
class DateRange:
    start_date: date
    end_date: date


def _add_months(value: date, months: int) -> date:
    month_index = value.month - 1 + months
    year = value.year + month_index // 12
    month = month_index % 12 + 1
    return value.replace(year=year, month=month, day=min(value.day, monthrange(year, month)[1]))


def split_date_range_by_months(
    start_date: date, end_date: date, max_months: int = 3
) -> list[DateRange]:
    """Split an inclusive range into contiguous calendar-month chunks."""
    if max_months < 1:
        raise ValueError("max_months must be at least 1")
    if start_date > end_date:
        raise ValueError("start_date cannot be after end_date")

    ranges: list[DateRange] = []
    current_start = start_date
    while current_start <= end_date:
        next_start = _add_months(current_start, max_months)
        current_end = min(next_start - timedelta(days=1), end_date)
        ranges.append(DateRange(current_start, current_end))
        current_start = current_end + timedelta(days=1)
    return ranges
