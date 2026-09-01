from fastapi import APIRouter, HTTPException

from app.database.connection import engine
from app.schemas.table import PredefinedTableCreate
from app.services.table_service import (
    create_predefined_table,
    list_predefined_tables,
)

router = APIRouter(
    prefix="/tables",
    tags=["Predefined Tables"],
)

@router.post("/")
def create_table(
    request: PredefinedTableCreate,
):

    try:

        created = create_predefined_table(
            engine,
            request.table_name,
            request.fields,
        )
        if not created:
            raise HTTPException(
                status_code=409,
                detail=(
                    f"Table already exists: "
                    f"{request.table_name}"
                ),
            )
        return {
            "status": "success",
            "message": "Predefined table created",
            "table_name": request.table_name,
        }
    except HTTPException:
        raise
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

@router.get("/")
def list_tables():
    return {
        "tables": list_predefined_tables(
            engine
        )
    }