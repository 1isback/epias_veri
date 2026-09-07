import pytest
from datetime import datetime
from app.integrations.epias.engine import GenericRequestEngine, PAGE_SIZE

def test_split_date_range():
    engine = GenericRequestEngine()
    
    start_date = datetime(2023, 1, 1)
    end_date = datetime(2023, 12, 31)
    max_days = 90
    
    intervals = engine._split_date_range(start_date, end_date, max_days)
    
    # 2023 is 365 days. 365 / 90 = 4.05 -> so we expect 5 intervals.
    assert len(intervals) == 5
    
    # First interval (90 days inclusive: Jan 1 + 89 days)
    assert intervals[0][0] == datetime(2023, 1, 1)
    assert intervals[0][1] == datetime(2023, 3, 31)
    
    # Second interval starts the next day
    assert intervals[1][0] == datetime(2023, 4, 1)
    
    # Last interval must exactly end at our requested end_date
    assert intervals[-1][1] == datetime(2023, 12, 31)

def test_extract_items():
    engine = GenericRequestEngine()
    
    # Case 1: Standard EPİAŞ items array
    resp1 = {"items": [{"id": 1}, {"id": 2}]}
    assert len(engine._extract_items_from_response(resp1)) == 2
    
    # Case 2: Nested data.items array
    resp2 = {"data": {"items": [{"id": 3}]}}
    assert len(engine._extract_items_from_response(resp2)) == 1
    
    # Case 3: Flat or unknown dictionary structure
    resp3 = {"some_other_key": "value"}
    res3 = engine._extract_items_from_response(resp3)
    assert len(res3) == 1
    assert res3[0]["some_other_key"] == "value"


@pytest.mark.asyncio
async def test_fetch_all_pages_walks_pagination(monkeypatch):
    engine = GenericRequestEngine()
    # Two full pages + one short page -> pagination should stop after the short page.
    pages = [
        {"items": [{"i": n} for n in range(PAGE_SIZE)], "page": {"total": 2 * PAGE_SIZE + 3}},
        {"items": [{"i": n} for n in range(PAGE_SIZE)], "page": {"total": 2 * PAGE_SIZE + 3}},
        {"items": [{"i": n} for n in range(3)], "page": {"total": 2 * PAGE_SIZE + 3}},
    ]
    calls = []

    async def fake_request(method, url, params, headers):
        calls.append(params["page"]["number"])
        return pages[params["page"]["number"] - 1]

    monkeypatch.setattr(engine, "_execute_single_request", fake_request)
    records, truncated = await engine._fetch_all_pages("POST", "http://x", {}, {}, 0)

    assert calls == [1, 2, 3]
    assert len(records) == 2 * PAGE_SIZE + 3
    assert truncated is False
