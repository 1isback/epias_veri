from datetime import date, datetime
from typing import Any

from sqlalchemy import and_, func, or_, select, tuple_
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.injection_quantity import InjectionQuantity, InjectionQuantityPowerPlant


class InjectionQuantityRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def upsert_powerplants(self, values: list[dict[str, Any]]) -> int:
        if not values:
            return 0
        statement = insert(InjectionQuantityPowerPlant).values(values)
        statement = statement.on_conflict_do_update(
            index_elements=[InjectionQuantityPowerPlant.epias_powerplant_id],
            set_={
                "name": statement.excluded.name,
                "short_name": statement.excluded.short_name,
                "eic": statement.excluded.eic,
                "raw_payload": statement.excluded.raw_payload,
                "last_synced_at": statement.excluded.last_synced_at,
                "updated_at": func.now(),
            },
        )
        result = await self.session.execute(statement)
        return result.rowcount or 0

    async def list_powerplants(self, search: str | None, limit: int, offset: int) -> list[InjectionQuantityPowerPlant]:
        statement = select(InjectionQuantityPowerPlant).order_by(InjectionQuantityPowerPlant.name).limit(limit).offset(offset)
        if search:
            statement = statement.where(
                or_(InjectionQuantityPowerPlant.name.ilike(f"%{search}%"), InjectionQuantityPowerPlant.short_name.ilike(f"%{search}%"))
            )
        return list((await self.session.execute(statement)).scalars())

    async def get_powerplant_by_epias_id(self, epias_powerplant_id: int) -> InjectionQuantityPowerPlant | None:
        statement = select(InjectionQuantityPowerPlant).where(InjectionQuantityPowerPlant.epias_powerplant_id == epias_powerplant_id)
        return (await self.session.execute(statement)).scalar_one_or_none()

    async def bulk_upsert_injection_quantities(self, values: list[dict[str, Any]]) -> tuple[int, int]:
        if not values:
            return 0, 0
        keys = [(value["epias_powerplant_id"], value["interval_start"]) for value in values]
        existing_statement = select(InjectionQuantity.epias_powerplant_id, InjectionQuantity.interval_start).where(
            tuple_(InjectionQuantity.epias_powerplant_id, InjectionQuantity.interval_start).in_(keys)
        )
        existing = set((await self.session.execute(existing_statement)).all())
        statement = insert(InjectionQuantity).values(values)
        statement = statement.on_conflict_do_update(
            constraint="uq_injection_quantity_plant_interval",
            set_={
                "date": statement.excluded.date,
                "period": statement.excluded.period,
                "injection_quantity": statement.excluded.injection_quantity,
                "unit": statement.excluded.unit,
                "source": statement.excluded.source,
                "raw_payload": statement.excluded.raw_payload,
                "updated_at": func.now(),
            },
        )
        await self.session.execute(statement)
        updated = sum(key in existing for key in keys)
        return len(values) - updated, updated

    async def list_injection_quantities(self, powerplant_id: int, start_date: date, end_date: date, limit: int, offset: int) -> list[InjectionQuantity]:
        statement = self._range_statement(powerplant_id, start_date, end_date).limit(limit).offset(offset)
        return list((await self.session.execute(statement)).scalars())

    async def get_injection_quantity_date_range(self, powerplant_id: int, start_date: date, end_date: date) -> list[InjectionQuantity]:
        return list((await self.session.execute(self._range_statement(powerplant_id, start_date, end_date))).scalars())

    def _range_statement(self, powerplant_id: int, start_date: date, end_date: date):
        return select(InjectionQuantity).where(
            and_(
                InjectionQuantity.epias_powerplant_id == powerplant_id,
                InjectionQuantity.date >= start_date,
                InjectionQuantity.date <= end_date,
            )
        ).order_by(InjectionQuantity.interval_start)
