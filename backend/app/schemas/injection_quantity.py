from datetime import date, datetime
from decimal import Decimal
from typing import Annotated

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator


PowerplantId = Annotated[int, Field(gt=0)]


class InjectionQuantityQuery(BaseModel):
    powerplant_id: PowerplantId
    start_date: date
    end_date: date
    force_refresh: bool = False

    @model_validator(mode="after")
    def validate_date_range(self) -> "InjectionQuantityQuery":
        if self.start_date > self.end_date:
            raise ValueError("start_date cannot be after end_date")
        return self


class InjectionQuantityPowerPlantSchema(BaseModel):
    epias_powerplant_id: int = Field(validation_alias="id", serialization_alias="epias_powerplant_id")
    name: str | None = None
    short_name: str | None = Field(default=None, validation_alias="shortName")
    eic: str | None = None

    model_config = ConfigDict(populate_by_name=True)


class EpiasInjectionQuantityRequestDto(BaseModel):
    start_date: datetime = Field(serialization_alias="startDate")
    end_date: datetime = Field(serialization_alias="endDate")
    powerplant_id: PowerplantId = Field(serialization_alias="powerplantId")

    model_config = ConfigDict(populate_by_name=True)


class InjectionQuantityRecordSchema(BaseModel):
    date: datetime
    hour: int = Field(ge=0, le=24)
    total: Decimal | None = None
    asphaltite: Decimal | None = None
    biomass: Decimal | None = None
    dam: Decimal | None = None
    fueloil: Decimal | None = None
    geothermal: Decimal | None = None
    imported_coal: Decimal | None = Field(default=None, validation_alias="importedCoal")
    international_export: Decimal | None = Field(default=None, validation_alias="internationalExport")
    international_import: Decimal | None = Field(default=None, validation_alias="internationalImport")
    lignite: Decimal | None = None
    lng: Decimal | None = None
    naphtha: Decimal | None = None
    natural_gas: Decimal | None = Field(default=None, validation_alias="naturalGas")
    other: Decimal | None = None
    river: Decimal | None = None
    stone_coal: Decimal | None = Field(default=None, validation_alias="stoneCoal")
    sun: Decimal | None = None
    wind: Decimal | None = None

    model_config = ConfigDict(populate_by_name=True, extra="ignore")


class EpiasInjectionQuantityResponseDto(BaseModel):
    items: list[InjectionQuantityRecordSchema] = Field(default_factory=list)
    model_config = ConfigDict(extra="ignore")


class InjectionQuantityResponseSchema(BaseModel):
    items: list[InjectionQuantityRecordSchema]
    total: int


class InjectionQuantitySyncResponse(BaseModel):
    powerplant_id: int
    requested_start_date: date
    requested_end_date: date
    chunk_count: int
    fetched_record_count: int
    inserted_record_count: int
    updated_record_count: int
    duplicate_record_count: int
    status: str
