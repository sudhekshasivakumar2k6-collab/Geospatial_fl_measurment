from pathlib import Path

import geopandas as gpd
from fastapi import HTTPException

def calculate_measurements(
    measurement_gdf: gpd.GeoDataFrame,
) -> list[dict]:
    """
    Calculate measurements for supported geometry types.

    Polygon / MultiPolygon:
        Area in square metres.

    LineString / MultiLineString:
        Length in metres.

    Point / MultiPoint:
        No measurement.
    """

    results = []

    for position, (_, row) in enumerate(
        measurement_gdf.iterrows()
    ):
        geometry = row.geometry

        measurement_type = None
        measurement_value = None
        measurement_unit = None

        if geometry is not None and not geometry.is_empty:

            geometry_type = geometry.geom_type

            if geometry_type in {
                "Polygon",
                "MultiPolygon",
            }:
                measurement_type = "area"
                measurement_value = round(
                    float(geometry.area),
                    2,
                )
                measurement_unit = "m²"

            elif geometry_type in {
                "LineString",
                "MultiLineString",
            }:
                measurement_type = "length"
                measurement_value = round(
                    float(geometry.length),
                    2,
                )
                measurement_unit = "m"

        results.append(
            {
                "feature_index": position,
                "measurement_type": measurement_type,
                "measurement_value": measurement_value,
                "measurement_unit": measurement_unit,
            }
        )

    return results
def read_geospatial_file(
    file_path: Path,
    file_type: str,
) -> gpd.GeoDataFrame:
    """
    Read a supported geospatial file and return a GeoDataFrame.
    """

    try:
        if file_type == "KML":
            gdf = gpd.read_file(
                file_path,
                driver="KML",
            )

        elif file_type == "SHAPEFILE":
            gdf = gpd.read_file(file_path)

        else:
            raise HTTPException(
                status_code=400,
                detail="Unsupported geospatial file type.",
            )

    except HTTPException:
        raise

    except Exception as exc:
        raise HTTPException(
            status_code=422,
            detail=f"Unable to read geospatial file: {exc}",
        ) from exc

    if gdf.empty:
        raise HTTPException(
            status_code=422,
            detail="The uploaded geospatial file contains no features.",
        )

    return gdf


def get_crs_string(
    gdf: gpd.GeoDataFrame,
) -> str | None:
    """
    Convert the dataset CRS into a readable string,
    preferably in EPSG format.
    """

    if gdf.crs is None:
        return None

    authority = gdf.crs.to_authority()

    if authority:
        return f"{authority[0]}:{authority[1]}"

    return gdf.crs.to_string()


def extract_features(
    gdf: gpd.GeoDataFrame,
) -> list[dict]:
    """
    Extract geometry and properties from each feature.
    """

    features = []

    for position, (_, row) in enumerate(gdf.iterrows()):
        geometry = row.geometry

        if geometry is None:
            geometry_type = "Unknown"
            geometry_wkt = None
        else:
            geometry_type = geometry.geom_type
            geometry_wkt = geometry.wkt

        properties = {}

        for column in gdf.columns:
            if column == gdf.geometry.name:
                continue

            value = row[column]

            if value is None:
                properties[column] = None
            else:
                properties[column] = str(value)

        features.append(
            {
                "feature_index": position,
                "geometry_type": geometry_type,
                "geometry": geometry_wkt,
                "properties": properties,
            }
        )

    return features