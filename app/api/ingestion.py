from fastapi import (
    APIRouter,
    Depends,
    File,
    Form,
    HTTPException,
    UploadFile,
)
from sqlalchemy.orm import Session

from app.database.connection import get_db
from app.services.ingestion_service import ingest_file


router = APIRouter(
    prefix="/ingest",
    tags=["Data Ingestion"],
)


@router.post("/file")
async def ingest_file_api(
    mapping_name: str = Form(...),
    operation: str = Form(...),
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
):

    try:

        content = await file.read()

        result = ingest_file(
            db=db,
            file_name=file.filename,
            file_content=content,
            mapping_name=mapping_name,
            operation=operation,
        )

        return result

    except ValueError as exc:

        raise HTTPException(
            status_code=400,
            detail=str(exc),
        )

    except Exception as exc:

        raise HTTPException(
            status_code=500,
            detail=str(exc),
        )