import geopandas as gpd
from fastapi import HTTPException
from pyproj import CRS


def is_geographic_crs(gdf: gpd.GeoDataFrame) -> bool:
    """
    Check whether the GeoDataFrame uses a geographic CRS,
    such as EPSG:4326.
    """

    if gdf.crs is None:
        raise HTTPException(
            status_code=422,
            detail="The geospatial file does not contain a valid CRS.",
        )

    crs = CRS.from_user_input(gdf.crs)

    return crs.is_geographic


def get_measurement_gdf(
    gdf: gpd.GeoDataFrame,
) -> tuple[gpd.GeoDataFrame, str]:
    """
    Return a GeoDataFrame in a projected CRS suitable
    for area and length calculations.

    Geographic datasets are projected to an estimated
    local UTM CRS.
    """

    if gdf.crs is None:
        raise HTTPException(
            status_code=422,
            detail=(
                "Cannot calculate measurements because "
                "the dataset CRS is missing."
            ),
        )

    try:
        crs = CRS.from_user_input(gdf.crs)

        if crs.is_geographic:
            projected_crs = gdf.estimate_utm_crs()

            if projected_crs is None:
                raise HTTPException(
                    status_code=422,
                    detail=(
                        "Unable to determine an appropriate "
                        "projected CRS for this dataset."
                    ),
                )

            projected_gdf = gdf.to_crs(projected_crs)

            return (
                projected_gdf,
                projected_crs.to_string(),
            )

        # Already projected
        return (
            gdf.copy(),
            crs.to_string(),
        )

    except HTTPException:
        raise

    except Exception as exc:
        raise HTTPException(
            status_code=422,
            detail=f"CRS transformation failed: {exc}",
        ) from exc