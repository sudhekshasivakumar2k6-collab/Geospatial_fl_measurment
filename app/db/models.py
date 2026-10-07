import uuid

from sqlalchemy import (
    Column,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
)
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.db.database import Base


class UploadedFile(Base):
    __tablename__ = "uploaded_files"

    id = Column(
        String,
        primary_key=True,
        default=lambda: str(uuid.uuid4()),
    )

    filename = Column(
        String,
        nullable=False,
    )

    file_type = Column(
        String,
        nullable=False,
    )

    crs = Column(
        String,
        nullable=True,
    )

    feature_count = Column(
        Integer,
        default=0,
        nullable=False,
    )

    status = Column(
        String,
        default="PENDING",
        nullable=False,
    )

    error_message = Column(
        Text,
        nullable=True,
    )

    created_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    features = relationship(
        "GeoFeature",
        back_populates="uploaded_file",
        cascade="all, delete-orphan",
    )


class GeoFeature(Base):
    __tablename__ = "geo_features"

    id = Column(
        Integer,
        primary_key=True,
        index=True,
    )

    uploaded_file_id = Column(
        String,
        ForeignKey("uploaded_files.id"),
        nullable=False,
        index=True,
    )

    feature_index = Column(
        Integer,
        nullable=False,
    )

    geometry_type = Column(
        String,
        nullable=False,
    )

    geometry = Column(
        Text,
        nullable=False,
    )

    properties = Column(
        Text,
        nullable=True,
    )

    measurement_type = Column(
        String,
        nullable=True,
    )

    measurement_value = Column(
        Float,
        nullable=True,
    )

    measurement_unit = Column(
        String,
        nullable=True,
    )

    uploaded_file = relationship(
        "UploadedFile",
        back_populates="features",
    )