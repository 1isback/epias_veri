from datetime import date, datetime
from decimal import Decimal
from typing import Any

from sqlalchemy import BigInteger, Date, DateTime, Index, Integer, Numeric, String, UniqueConstraint
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import BaseModel


class InjectionQuantityPowerPlant(BaseModel):
    __tablename__ = "injection_quantity_powerplants"

    epias_powerplant_id: Mapped[int] = mapped_column(BigInteger, unique=True, nullable=False, index=True)
    name: Mapped[str | None] = mapped_column(String(255))
    short_name: Mapped[str | None] = mapped_column(String(255))
    eic: Mapped[str | None] = mapped_column(String(64))
    raw_payload: Mapped[dict[str, Any] | None] = mapped_column(JSONB)
    last_synced_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))


class InjectionQuantity(BaseModel):
    __tablename__ = "injection_quantities"
    __table_args__ = (
        UniqueConstraint("epias_powerplant_id", "interval_start", name="uq_injection_quantity_plant_interval"),
        Index("ix_injection_quantities_plant_interval", "epias_powerplant_id", "interval_start"),
    )

    epias_powerplant_id: Mapped[int] = mapped_column(BigInteger, nullable=False)
    date: Mapped[date] = mapped_column(Date, nullable=False)
    period: Mapped[int] = mapped_column(Integer, nullable=False)
    interval_start: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    injection_quantity: Mapped[Decimal | None] = mapped_column(Numeric(20, 6))
    unit: Mapped[str] = mapped_column(String(16), nullable=False, default="MWh")
    source: Mapped[str] = mapped_column(String(32), nullable=False, default="EPIAS")
    raw_payload: Mapped[dict[str, Any] | None] = mapped_column(JSONB)
