import uuid
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import String, ForeignKey, Boolean, Integer, Text
from sqlalchemy.dialects.postgresql import UUID
from datetime import datetime
from sqlalchemy import DateTime

from app.models.base import BaseModel

class Dataset(BaseModel):
    __tablename__ = "datasets"
    
    code: Mapped[str] = mapped_column(String(50), nullable=False, unique=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=True)
    
    versions = relationship("DatasetVersion", back_populates="dataset")
    metadata_fields = relationship("DatasetMetadata", back_populates="dataset")
    data_dictionary = relationship("DataDictionary", back_populates="dataset")


class DatasetVersion(BaseModel):
    __tablename__ = "dataset_versions"
    
    dataset_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("datasets.id"), nullable=False)
    version_number: Mapped[int] = mapped_column(Integer, nullable=False)
    effective_from: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    
    dataset = relationship("Dataset", back_populates="versions")


class DatasetMetadata(BaseModel):
    __tablename__ = "dataset_metadata"
    
    dataset_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("datasets.id"), nullable=False)
    key: Mapped[str] = mapped_column(String(255), nullable=False)
    value: Mapped[str] = mapped_column(Text, nullable=False)
    
    dataset = relationship("Dataset", back_populates="metadata_fields")


class DataDictionary(BaseModel):
    __tablename__ = "data_dictionary"
    
    dataset_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("datasets.id"), nullable=False)
    field_name: Mapped[str] = mapped_column(String(100), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=True)
    data_type: Mapped[str] = mapped_column(String(50), nullable=False)
    unit: Mapped[str] = mapped_column(String(50), nullable=True)
    is_filterable: Mapped[bool] = mapped_column(Boolean, default=False)
    is_metric: Mapped[bool] = mapped_column(Boolean, default=False)
    
    dataset = relationship("Dataset", back_populates="data_dictionary")
