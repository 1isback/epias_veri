from datetime import date

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user
from app.models.user import User
from app.core.database import get_db_session
from app.repositories.injection_quantity_repo import InjectionQuantityRepository
from app.schemas.injection_quantity import (
    InjectionQuantityPowerPlantSchema,
    InjectionQuantityQuery,
    InjectionQuantityRecordSchema,
    InjectionQuantityResponseSchema,
    InjectionQuantitySyncResponse,
)
from app.services.injection_quantity_service import InjectionQuantityService

router = APIRouter()


@router.post("/powerplants/sync", status_code=status.HTTP_200_OK)
async def sync_powerplants(db: AsyncSession = Depends(get_db_session), current_user: User = Depends(get_current_user)) -> dict[str, int]:
    return {"synced_count": await InjectionQuantityService(db).sync_powerplants()}


@router.get("/powerplants", response_model=list[InjectionQuantityPowerPlantSchema])
async def list_powerplants(search: str | None = None, limit: int = Query(100, ge=1, le=1000), offset: int = Query(0, ge=0), db: AsyncSession = Depends(get_db_session), current_user: User = Depends(get_current_user)) -> list[InjectionQuantityPowerPlantSchema]:
    rows = await InjectionQuantityRepository(db).list_powerplants(search, limit, offset)
    return [InjectionQuantityPowerPlantSchema(epias_powerplant_id=row.epias_powerplant_id, name=row.name, short_name=row.short_name, eic=row.eic) for row in rows]


@router.post("/sync", response_model=InjectionQuantitySyncResponse)
async def sync_injection_quantities(query: InjectionQuantityQuery, db: AsyncSession = Depends(get_db_session), current_user: User = Depends(get_current_user)) -> InjectionQuantitySyncResponse:
    try:
        return await InjectionQuantityService(db).sync_injection_quantities(query)
    except LookupError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc


@router.get("", response_model=InjectionQuantityResponseSchema)
async def list_injection_quantities(powerplant_id: int, start_date: date, end_date: date, limit: int = Query(1000, ge=1, le=10000), offset: int = Query(0, ge=0), db: AsyncSession = Depends(get_db_session), current_user: User = Depends(get_current_user)) -> InjectionQuantityResponseSchema:
    if start_date > end_date:
        raise HTTPException(status_code=422, detail="start_date cannot be after end_date")
    rows = await InjectionQuantityRepository(db).list_injection_quantities(powerplant_id, start_date, end_date, limit, offset)
    items = [InjectionQuantityRecordSchema(date=row.interval_start, hour=row.period, total=row.injection_quantity) for row in rows]
    return InjectionQuantityResponseSchema(items=items, total=len(items))
