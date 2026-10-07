from fastapi import FastAPI

from app.api.files import router as files_router
from app.core.config import settings
from app.db import models
from app.db.database import Base, engine


# Create database tables
Base.metadata.create_all(bind=engine)


app = FastAPI(
    title=settings.APP_NAME,
    description=(
        "Backend API for uploading, processing, "
        "and measuring KML and Shapefile geospatial data."
    ),
    version=settings.APP_VERSION,
)


# Register geospatial file routes
app.include_router(files_router)


@app.get("/", tags=["Health"])
def root():
    return {
        "application": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "status": "running",
    }


@app.get("/health", tags=["Health"])
def health_check():
    return {
        "status": "healthy"
    }