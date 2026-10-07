from datetime import datetime
from typing import Optional

from pydantic import BaseModel


class FileUploadResponse(BaseModel):
    id: str
    filename: str
    file_type: str
    status: str
    feature_count: int
    crs: Optional[str] = None
    created_at: datetime

    model_config = {
        "from_attributes": True
    }


class FileInfoResponse(FileUploadResponse):
    error_message: Optional[str] = None
from typing import Any


class FeatureMeasurementResponse(BaseModel):
    feature_index: int
    geometry_type: str
    geometry: str
    properties: dict[str, Any]
    measurement_type: Optional[str] = None
    measurement_value: Optional[float] = None
    measurement_unit: Optional[str] = None


class MeasurementsResponse(BaseModel):
    file_id: str
    filename: str
    crs: Optional[str] = None
    feature_count: int
    measurements: list[FeatureMeasurementResponse]    