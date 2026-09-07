import uuid
from datetime import datetime
from typing import Any

from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy import DateTime, String, Float, Integer, ForeignKey

from app.models.base import BaseModel

class SyncJob(BaseModel):
    __tablename__ = "sync_jobs"
    
    endpoint_id: Mapped[str] = mapped_column(String(50), nullable=False)
    dataset_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("datasets.id"), nullable=True)
    dataset_version_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("dataset_versions.id"), nullable=True)
    requested_start: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    requested_end: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    record_count: Mapped[int] = mapped_column(Integer, default=0)
    status: Mapped[str] = mapped_column(String(20), default="PENDING")  # PENDING, SUCCESS, FAILED
    duration_ms: Mapped[float] = mapped_column(Float, nullable=True)
    
    # Relationships
    raw_imports = relationship("RawImport", back_populates="sync_job", cascade="all, delete-orphan")
    ptf_data = relationship("PTFData", back_populates="sync_job", cascade="all, delete-orphan")


class RawImport(BaseModel):
    __tablename__ = "raw_imports"
    
    sync_job_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("sync_jobs.id"), nullable=False)
    payload: Mapped[Any] = mapped_column(JSONB, nullable=False)
    fetched_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    validation_status: Mapped[str] = mapped_column(String(20), default="UNVALIDATED") # UNVALIDATED, VALID, INVALID
    
    # Relationships
    sync_job = relationship("SyncJob", back_populates="raw_imports")
