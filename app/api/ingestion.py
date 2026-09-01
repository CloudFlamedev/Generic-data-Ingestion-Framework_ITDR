import json
from sqlalchemy import inspect, select
from app.database.connection import engine
from app.models.ingestion import IngestionFailureLog
from app.models.mapping import (
    MappingDefinition,
    MappingField,
)
from fastapi import APIRouter, Depends, File, Form, UploadFile
from sqlalchemy.orm import Session
from app.database.connection import get_db
from app.normalizers.generic import normalize_record
from app.operations.database_operations import (
    append_records,
    truncate_insert_records,
    upsert_records,
)
from app.parsers.generic import parse_file
ALLOWED_OPERATIONS = {
    "append",
    "upsert",
    "truncate_insert",
}
def ingest_file(
    db,
    file_name: str,
    file_content: bytes,
    mapping_name: str,
    operation: str,
):

    operation = operation.lower().strip()

    if operation not in ALLOWED_OPERATIONS:
        raise ValueError(
            "Invalid operation. "
            "Use append, upsert or truncate_insert."
        )

    # ---------------------------------------------------------
    # 1. Find active mapping
    # ---------------------------------------------------------

    mapping = db.scalar(
        select(MappingDefinition).where(
            MappingDefinition.mapping_name
            == mapping_name,
            MappingDefinition.is_active.is_(True),
        )
    )

    if not mapping:
        raise ValueError(
            f"Mapping not found: {mapping_name}"
        )

    # ---------------------------------------------------------
    # 2. Verify destination table exists
    #
    # Destination tables are created separately through
    # POST /tables/.
    # ---------------------------------------------------------

    inspector = inspect(engine)

    if mapping.destination_table not in inspector.get_table_names():
        raise ValueError(
            f"Destination table does not exist: "
            f"{mapping.destination_table}"
        )

    # ---------------------------------------------------------
    # 3. Load field mappings
    # ---------------------------------------------------------

    fields = db.scalars(
        select(MappingField).where(
            MappingField.mapping_id == mapping.id
        )
    ).all()

    if not fields:
        raise ValueError(
            f"No field mappings found for mapping: "
            f"{mapping_name}"
        )

    # ---------------------------------------------------------
    # 4. Parse input file
    # ---------------------------------------------------------

    records = parse_file(
        file_content,
        mapping.file_type,
    )

    normalized_records = []
    failed_records = 0
    # ---------------------------------------------------------
    # 5. Normalize and validate each record
    # ---------------------------------------------------------
    for record in records:

        try:

            normalized = normalize_record(
                record,
                fields,
            )

            # Current upsert strategy requires event_id.
            if not normalized.get("event_id"):
                raise ValueError(
                    "event_id is required"
                )

            # Preserve original source record.
            normalized["raw_data"] = json.dumps(
                record
            )

            normalized_records.append(
                normalized
            )

        except Exception as exc:

            failed_records += 1

            failure = IngestionFailureLog(
                mapping_name=mapping_name,
                file_name=file_name,
                error_message=str(exc),
                failed_record=json.dumps(record),
            )

            db.add(failure)

    db.commit()

    # ---------------------------------------------------------
    # 6. Execute database operation
    # ---------------------------------------------------------
    if operation == "append":

        loaded = append_records(
            engine,
            mapping.destination_table,
            normalized_records,
        )
    elif operation == "upsert":

        loaded = upsert_records(
            engine,
            mapping.destination_table,
            normalized_records,
        )
    elif operation == "truncate_insert":

        loaded = truncate_insert_records(
            engine,
            mapping.destination_table,
            normalized_records,
        )

    else:
        raise ValueError(
            f"Unsupported operation: {operation}"
        )
    # ---------------------------------------------------------
    # 7. Return ingestion result
    # ---------------------------------------------------------
    return {
        "mapping_name": mapping_name,
        "operation": operation,
        "file_name": file_name,
        "destination_table": mapping.destination_table,
        "records_received": len(records),
        "records_loaded": loaded,
        "records_failed": failed_records,
        "status": (
            "success"
            if failed_records == 0
            else "partial_success"
        ),
    }
router = APIRouter(
    prefix="/ingest",
    tags=["Data Ingestion"],
)


@router.post("/file")
def ingest_file_api(
    mapping_name: str = Form(...),
    operation: str = Form(...),
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
):
    file_content = file.file.read()

    return ingest_file(
        db=db,
        file_name=file.filename,
        file_content=file_content,
        mapping_name=mapping_name,
        operation=operation,
    )