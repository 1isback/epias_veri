from datetime import date

import pytest

from app.schemas.injection_quantity import InjectionQuantityQuery
from app.services.injection_quantity_service import InjectionQuantityService


class FakeEngine:
    def __init__(self) -> None:
        self.calls: list[tuple[str, str, dict]] = []

    async def execute_raw(self, path: str, method: str, params: dict | None = None):
        self.calls.append((path, method, params or {}))
        if method == "GET":
            return {"items": [{"id": 123, "name": "Test Plant", "shortName": "TP", "eic": "EIC"}]}
        return {"items": [{"date": params["startDate"], "hour": 1, "total": 2.5}, {"date": params["startDate"], "hour": 1, "total": 2.5}]}


@pytest.mark.asyncio
async def test_powerplant_request_uses_get_and_parses_response() -> None:
    engine = FakeEngine()
    service = InjectionQuantityService(session=None, request_engine=engine)  # type: ignore[arg-type]
    plants = await service.get_injection_quantity_powerplants()
    assert plants[0].epias_powerplant_id == 123
    assert engine.calls[0][1] == "GET"


@pytest.mark.asyncio
async def test_chunked_request_uses_documented_body_and_deduplicates() -> None:
    engine = FakeEngine()
    service = InjectionQuantityService(session=None, request_engine=engine)  # type: ignore[arg-type]
    records, chunks, duplicates = await service.get_injection_quantity_chunked(InjectionQuantityQuery(powerplant_id=123, start_date=date(2025, 1, 1), end_date=date(2025, 4, 1)))
    assert chunks == 2
    assert duplicates == 2
    assert len(records) == 2
    body = engine.calls[0][2]
    assert body["powerplantId"] == 123
    assert body["startDate"].endswith("+03:00")
