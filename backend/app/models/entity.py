import uuid
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import String, Float, ForeignKey
from sqlalchemy.dialects.postgresql import UUID

from app.models.base import BaseModel

class Company(BaseModel):
    __tablename__ = "companies"
    
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    eic_code: Mapped[str] = mapped_column(String(50), nullable=True, unique=True)
    
    power_plants = relationship("PowerPlant", back_populates="company")

class Region(BaseModel):
    __tablename__ = "regions"
    
    name: Mapped[str] = mapped_column(String(100), nullable=False, unique=True)
    
    power_plants = relationship("PowerPlant", back_populates="region")

class FuelType(BaseModel):
    __tablename__ = "fuel_types"
    
    name: Mapped[str] = mapped_column(String(100), nullable=False, unique=True)

class PowerPlant(BaseModel):
    __tablename__ = "power_plants"
    
    company_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("companies.id"), nullable=False)
    region_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("regions.id"), nullable=False)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    installed_capacity_mw: Mapped[float] = mapped_column(Float, nullable=True)
    
    company = relationship("Company", back_populates="power_plants")
    region = relationship("Region", back_populates="power_plants")
