import json

from fastapi import (
    APIRouter,
    Depends,
    File,
    HTTPException,
    UploadFile,
    status,
)
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.db.models import GeoFeature, UploadedFile
from app.schemas.files import (
    FileInfoResponse,
    FileUploadResponse,
    MeasurementsResponse,
)
from app.services.crs_service import get_measurement_gdf
from app.services.file_service import save_uploaded_file
from app.services.geospatial_service import (
    calculate_measurements,
    extract_features,
    get_crs_string,
    read_geospatial_file,
)


# ============================================================
# Router
# ============================================================

router = APIRouter(
    prefix="/api/files",
    tags=["Geospatial Files"],
)


# ============================================================
# POST /api/files/
# Upload and process geospatial file
# ============================================================

@router.post(
    "/",
    response_model=FileUploadResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Upload and Process Geospatial File",
    description=(
        "Upload either a KML file or a ZIP archive "
        "containing a valid Shapefile."
    ),
)
def upload_geospatial_file(
    file: UploadFile = File(
        ...,
        description="KML file or ZIP archive containing a Shapefile",
    ),
    db: Session = Depends(get_db),
):
    """
    Upload and process a KML file or zipped Shapefile.
    """

    # 1. Validate and save uploaded file
    saved_path, extension = save_uploaded_file(file)

    # 2. Determine file type
    if extension == ".kml":
        file_type = "KML"
    else:
        file_type = "SHAPEFILE"

    # 3. Create initial database record
    uploaded_file = UploadedFile(
        filename=file.filename,
        file_type=file_type,
        status="PROCESSING",
        feature_count=0,
        crs=None,
    )

    db.add(uploaded_file)
    db.commit()
    db.refresh(uploaded_file)

    try:
        # 4. Read geospatial data
        gdf = read_geospatial_file(
            saved_path,
            file_type,
        )

        # 5. Get original CRS
        crs = get_crs_string(gdf)

        # 6. Extract original features
        features = extract_features(gdf)

        # 7. Transform to suitable projected CRS
        #    before calculating measurements
        measurement_gdf, measurement_crs = (
            get_measurement_gdf(gdf)
        )

        # 8. Calculate measurements
        measurements = calculate_measurements(
            measurement_gdf
        )

        # 9. Save features and measurements
        for feature, measurement in zip(
            features,
            measurements,
        ):
            geo_feature = GeoFeature(
                uploaded_file_id=uploaded_file.id,
                feature_index=feature["feature_index"],
                geometry_type=feature["geometry_type"],
                geometry=feature["geometry"] or "",
                properties=json.dumps(
                    feature["properties"],
                    ensure_ascii=False,
                ),
                measurement_type=measurement[
                    "measurement_type"
                ],
                measurement_value=measurement[
                    "measurement_value"
                ],
                measurement_unit=measurement[
                    "measurement_unit"
                ],
            )

            db.add(geo_feature)

        # 10. Mark processing as completed
        uploaded_file.crs = crs
        uploaded_file.feature_count = len(features)
        uploaded_file.status = "COMPLETED"
        uploaded_file.error_message = None

        db.commit()
        db.refresh(uploaded_file)

        return uploaded_file

    except HTTPException as exc:
        db.rollback()

        uploaded_file.status = "FAILED"
        uploaded_file.error_message = str(exc.detail)

        db.add(uploaded_file)
        db.commit()

        raise

    except Exception as exc:
        db.rollback()

        uploaded_file.status = "FAILED"
        uploaded_file.error_message = str(exc)

        db.add(uploaded_file)
        db.commit()

        raise HTTPException(
            status_code=500,
            detail=(
                "Unexpected error while processing "
                "the geospatial file."
            ),
        ) from exc


# ============================================================
# GET /api/files/{file_id}/
# Return uploaded file information
# ============================================================

@router.get(
    "/{file_id}/",
    response_model=FileInfoResponse,
    summary="Get Uploaded File Information",
)
def get_file_information(
    file_id: str,
    db: Session = Depends(get_db),
):
    """
    Return metadata and processing status for an uploaded file.
    """

    uploaded_file = (
        db.query(UploadedFile)
        .filter(UploadedFile.id == file_id)
        .first()
    )

    if uploaded_file is None:
        raise HTTPException(
            status_code=404,
            detail="Uploaded file not found.",
        )

    return uploaded_file


# ============================================================
# GET /api/files/{file_id}/measurements/
# Return feature measurements
# ============================================================

@router.get(
    "/{file_id}/measurements/",
    response_model=MeasurementsResponse,
    summary="Get Feature Measurements",
)
def get_file_measurements(
    file_id: str,
    db: Session = Depends(get_db),
):
    """
    Return extracted features and their measurements.
    """

    # Find uploaded file
    uploaded_file = (
        db.query(UploadedFile)
        .filter(UploadedFile.id == file_id)
        .first()
    )

    if uploaded_file is None:
        raise HTTPException(
            status_code=404,
            detail="Uploaded file not found.",
        )

    # Get features belonging to this file
    features = (
        db.query(GeoFeature)
        .filter(
            GeoFeature.uploaded_file_id == file_id
        )
        .order_by(GeoFeature.feature_index)
        .all()
    )

    measurement_results = []

    # Convert database records into API response
    for feature in features:
        try:
            properties = (
                json.loads(feature.properties)
                if feature.properties
                else {}
            )

        except json.JSONDecodeError:
            properties = {}

        measurement_results.append(
            {
                "feature_index": feature.feature_index,
                "geometry_type": feature.geometry_type,
                "geometry": feature.geometry,
                "properties": properties,
                "measurement_type": feature.measurement_type,
                "measurement_value": feature.measurement_value,
                "measurement_unit": feature.measurement_unit,
            }
        )

    return {
        "file_id": uploaded_file.id,
        "filename": uploaded_file.filename,
        "crs": uploaded_file.crs,
        "feature_count": uploaded_file.feature_count,
        "measurements": measurement_results,
    }