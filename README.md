# Geospatial File Measurement API

A backend API built with FastAPI for uploading, processing, and measuring geospatial data from KML files and zipped Shapefiles.

## Features

- Upload KML files
- Upload zipped Shapefiles
- Extract geospatial features
- Detect geometry types
- Extract feature properties
- Handle coordinate reference systems (CRS)
- Calculate polygon area
- Calculate line length
- Handle point geometries
- Retrieve uploaded file information
- Retrieve feature measurements
- Graceful error handling

## Technology Stack

- Python
- FastAPI
- SQLAlchemy
- GeoPandas
- Shapely
- PyProj
- Fiona
- SQLite
- Pytest

## Supported File Formats

- `.kml`
- `.zip` containing a Shapefile

## API Endpoints

### Upload File

`POST /api/files/`

### Get File Information

`GET /api/files/{id}/`

### Get Measurements

`GET /api/files/{id}/measurements/`

## Development Status

Currently under development.

## Learning

This project explores geospatial file processing, coordinate reference systems, geometry operations, backend API design, and production-oriented Python development.

## Future Scope

Future improvements may include asynchronous processing, PostGIS integration, cloud storage, authentication, and support for additional geospatial formats.