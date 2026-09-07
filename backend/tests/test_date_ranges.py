from datetime import date

import pytest

from app.utils.date_ranges import DateRange, split_date_range_by_months


@pytest.mark.parametrize(
    ("start", "end", "expected"),
    [
        (date(2025, 1, 1), date(2025, 1, 1), [DateRange(date(2025, 1, 1), date(2025, 1, 1))]),
        (date(2025, 1, 1), date(2025, 1, 31), [DateRange(date(2025, 1, 1), date(2025, 1, 31))]),
        (date(2025, 1, 1), date(2025, 3, 31), [DateRange(date(2025, 1, 1), date(2025, 3, 31))]),
        (date(2025, 1, 1), date(2025, 4, 1), [DateRange(date(2025, 1, 1), date(2025, 3, 31)), DateRange(date(2025, 4, 1), date(2025, 4, 1))]),
        (date(2024, 11, 30), date(2025, 2, 28), [DateRange(date(2024, 11, 30), date(2025, 2, 27)), DateRange(date(2025, 2, 28), date(2025, 2, 28))]),
        (date(2024, 2, 1), date(2024, 2, 29), [DateRange(date(2024, 2, 1), date(2024, 2, 29))]),
    ],
)
def test_split_date_range_by_months(start: date, end: date, expected: list[DateRange]) -> None:
    assert split_date_range_by_months(start, end) == expected


def test_split_one_year_is_contiguous() -> None:
    ranges = split_date_range_by_months(date(2025, 1, 1), date(2025, 12, 31))
    assert len(ranges) == 4
    assert ranges[-1].end_date == date(2025, 12, 31)
    assert all(left.end_date.fromordinal(left.end_date.toordinal() + 1) == right.start_date for left, right in zip(ranges, ranges[1:]))


def test_split_date_range_rejects_reverse_range() -> None:
    with pytest.raises(ValueError, match="cannot be after"):
        split_date_range_by_months(date(2025, 1, 2), date(2025, 1, 1))
