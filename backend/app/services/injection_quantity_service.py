import logging
from datetime import date, datetime, time, timedelta
from typing import Any
from zoneinfo import ZoneInfo

from sqlalchemy.ext.asyncio import AsyncSession

from app.integrations.epias.engine import GenericRequestEngine
from app.repositories.injection_quantity_repo import InjectionQuantityRepository
from app.schemas.injection_quantity import (
    EpiasInjectionQuantityRequestDto,
    EpiasInjectionQuantityResponseDto,
    InjectionQuantityPowerPlantSchema,
    InjectionQuantityQuery,
    InjectionQuantityRecordSchema,
    InjectionQuantitySyncResponse,
)
from app.utils.date_ranges import split_date_range_by_months

logger = logging.getLogger(__name__)
ISTANBUL = ZoneInfo("Europe/Istanbul")
INJECTION_QUANTITY = "/generation/data/injection-quantity"
INJECTION_QUANTITY_POWERPLANT_LIST = "/generation/data/injection-quantity-powerplant-list"


class InjectionQuantityService:
    def __init__(self, session: AsyncSession, request_engine: GenericRequestEngine | None = None):
        self.session = session
        self.repo = InjectionQuantityRepository(session)
        self.request_engine = request_engine or GenericRequestEngine()

    async def get_injection_quantity_powerplants(self) -> list[InjectionQuantityPowerPlantSchema]:
        payload = await self.request_engine.execute_raw(INJECTION_QUANTITY_POWERPLANT_LIST, "GET")
        items = payload.get("items", []) if isinstance(payload, dict) else payload
        if not isinstance(items, list):
            raise ValueError("Unexpected EPİAŞ powerplant response schema")
        return [InjectionQuantityPowerPlantSchema.model_validate(item) for item in items]

    async def get_injection_quantity(self, query: InjectionQuantityQuery) -> list[InjectionQuantityRecordSchema]:
        body = EpiasInjectionQuantityRequestDto(
            start_date=datetime.combine(query.start_date, time.min, ISTANBUL),
            end_date=datetime.combine(query.end_date, time.max, ISTANBUL),
            powerplant_id=query.powerplant_id,
        )
        payload = await self.request_engine.execute_raw(
            INJECTION_QUANTITY, "POST", body.model_dump(by_alias=True, mode="json")
        )
        if not isinstance(payload, dict):
            raise ValueError("Unexpected EPİAŞ injection quantity response schema")
        return EpiasInjectionQuantityResponseDto.model_validate(payload).items

    async def get_injection_quantity_chunked(self, query: InjectionQuantityQuery) -> tuple[list[InjectionQuantityRecordSchema], int, int]:
        chunks = split_date_range_by_months(query.start_date, query.end_date)
        deduplicated: dict[tuple[datetime, int], InjectionQuantityRecordSchema] = {}
        fetched_count = 0
        for chunk in chunks:
            chunk_query = query.model_copy(update={"start_date": chunk.start_date, "end_date": chunk.end_date})
            try:
                records = await self.get_injection_quantity(chunk_query)
            except Exception:
                logger.exception("UEVM chunk failed for powerplant_id=%s, range=%s..%s", query.powerplant_id, chunk.start_date, chunk.end_date)
                raise
            fetched_count += len(records)
            for record in records:
                deduplicated[(record.date, record.hour)] = record
        records = sorted(deduplicated.values(), key=lambda record: (record.date, record.hour))
        return records, len(chunks), fetched_count - len(records)

    async def sync_powerplants(self) -> int:
        powerplants = await self.get_injection_quantity_powerplants()
        now = datetime.now(ISTANBUL)
        values: list[dict[str, Any]] = [
            {
                "epias_powerplant_id": plant.epias_powerplant_id,
                "name": plant.name,
                "short_name": plant.short_name,
                "eic": plant.eic,
                "raw_payload": plant.model_dump(by_alias=True),
                "last_synced_at": now,
            }
            for plant in powerplants
        ]
        count = await self.repo.upsert_powerplants(values)
        await self.session.commit()
        return count

    async def sync_injection_quantities(self, query: InjectionQuantityQuery) -> InjectionQuantitySyncResponse:
        if await self.repo.get_powerplant_by_epias_id(query.powerplant_id) is None:
            raise LookupError("UEVM powerplant was not found; synchronize powerplants first")
        records, chunk_count, duplicate_count = await self.get_injection_quantity_chunked(query)
        values = [self._record_to_value(query.powerplant_id, record) for record in records]
        # A single DB transaction is committed only after every EPİAŞ chunk succeeds.
        inserted, updated = await self.repo.bulk_upsert_injection_quantities(values)
        await self.session.commit()
        return InjectionQuantitySyncResponse(
            powerplant_id=query.powerplant_id,
            requested_start_date=query.start_date,
            requested_end_date=query.end_date,
            chunk_count=chunk_count,
            fetched_record_count=len(records) + duplicate_count,
            inserted_record_count=inserted,
            updated_record_count=updated,
            duplicate_record_count=duplicate_count,
            status="completed",
        )

    @staticmethod
    def _record_to_value(powerplant_id: int, record: InjectionQuantityRecordSchema) -> dict[str, Any]:
        source_date = record.date.astimezone(ISTANBUL).date() if record.date.tzinfo else record.date.date()
        interval_start = datetime.combine(source_date, time.min, ISTANBUL) + timedelta(hours=record.hour)
        return {
            "epias_powerplant_id": powerplant_id,
            "date": source_date,
            "period": record.hour,
            "interval_start": interval_start,
            "injection_quantity": record.total,
            "unit": "MWh",
            "source": "EPIAS",
            "raw_payload": record.model_dump(by_alias=True, mode="json"),
        }
