from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database.connection import get_db
from app.schemas.mapping import MappingCreate
from app.services.mapping_service import (
    create_mapping,
    list_mappings,
)


router = APIRouter(
    prefix="/mappings",
    tags=["Mappings"],
)


@router.post("/")
def create_mapping_api(
    request: MappingCreate,
    db: Session = Depends(get_db),
):

    try:

        mapping = create_mapping(
            db,
            request,
        )

        return {
            "status": "success",
            "mapping_id": mapping.id,
            "mapping_name": mapping.mapping_name,
        }

    except ValueError as exc:

        raise HTTPException(
            status_code=400,
            detail=str(exc),
        )


@router.get("/")
def list_mapping_api(
    db: Session = Depends(get_db),
):

    mappings = list_mappings(db)

    return [
        {
            "id": mapping.id,
            "mapping_name": mapping.mapping_name,
            "source_name": mapping.source_name,
            "destination_table": mapping.destination_table,
            "file_type": mapping.file_type,
            "file_pattern": mapping.file_pattern,
            "is_active": mapping.is_active,
        }
        for mapping in mappings
    ]