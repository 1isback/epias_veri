import uuid
from datetime import datetime

from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy import DateTime, Float, ForeignKey, UniqueConstraint

from app.models.base import BaseModel

class PTFData(BaseModel):
    __tablename__ = "ptf_data"
    __table_args__ = (
        UniqueConstraint('timestamp', name='uq_ptf_timestamp'),
    )
    
    timestamp: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, unique=True)
    price_tl: Mapped[float] = mapped_column(Float, nullable=False)
    price_usd: Mapped[float] = mapped_column(Float, nullable=False)
    price_eur: Mapped[float] = mapped_column(Float, nullable=False)
    
    dataset_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("datasets.id"), nullable=False)
    dataset_version_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("dataset_versions.id"), nullable=False)
    sync_job_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("sync_jobs.id"), nullable=False)
    
    sync_job = relationship("SyncJob", back_populates="ptf_data")
