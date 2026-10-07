from pathlib import Path
import shutil
import uuid
import zipfile

from fastapi import HTTPException, UploadFile

from app.core.config import settings


ALLOWED_EXTENSIONS = {".kml", ".zip"}

REQUIRED_SHAPEFILE_EXTENSIONS = {
    ".shp",
    ".shx",
    ".dbf",
}


def validate_file_extension(filename: str) -> str:
    """
    Validate the uploaded file extension.
    """

    extension = Path(filename).suffix.lower()

    if extension not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=400,
            detail=(
                "Unsupported file type. "
                "Only .kml and .zip files are allowed."
            ),
        )

    return extension


def validate_shapefile_zip(file_path: Path) -> None:
    """
    Validate that a ZIP archive contains the required
    Shapefile components.
    """

    if not zipfile.is_zipfile(file_path):
        raise HTTPException(
            status_code=400,
            detail="The uploaded ZIP file is not a valid ZIP archive.",
        )

    try:
        with zipfile.ZipFile(file_path, "r") as archive:
            filenames = archive.namelist()

            extensions = {
                Path(name).suffix.lower()
                for name in filenames
                if not name.endswith("/")
            }

            missing = REQUIRED_SHAPEFILE_EXTENSIONS - extensions

            if missing:
                missing_text = ", ".join(sorted(missing))

                raise HTTPException(
                    status_code=400,
                    detail=(
                        "Invalid Shapefile archive. "
                        f"Missing required component(s): {missing_text}"
                    ),
                )

    except zipfile.BadZipFile:
        raise HTTPException(
            status_code=400,
            detail="The uploaded ZIP file is corrupted.",
        )


def save_uploaded_file(upload_file: UploadFile) -> tuple[Path, str]:
    """
    Validate and save an uploaded geospatial file.
    """

    if not upload_file.filename:
        raise HTTPException(
            status_code=400,
            detail="Uploaded file must have a filename.",
        )

    extension = validate_file_extension(upload_file.filename)

    upload_directory = settings.upload_path
    upload_directory.mkdir(
        parents=True,
        exist_ok=True,
    )

    unique_filename = f"{uuid.uuid4()}{extension}"

    destination = upload_directory / unique_filename

    try:
        with destination.open("wb") as buffer:
            shutil.copyfileobj(
                upload_file.file,
                buffer,
            )

        if extension == ".zip":
            validate_shapefile_zip(destination)

    except HTTPException:
        destination.unlink(missing_ok=True)
        raise

    except Exception:
        destination.unlink(missing_ok=True)

        raise HTTPException(
            status_code=500,
            detail="Unable to save uploaded file.",
        )

    return destination, extension