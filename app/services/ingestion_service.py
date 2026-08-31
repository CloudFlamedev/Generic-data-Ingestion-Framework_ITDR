import json

from sqlalchemy import select

from app.database.connection import engine
from app.models.ingestion import IngestionFailureLog
from app.models.mapping import (
    MappingDefinition,
    MappingField,
)
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

    operation = operation.lower()

    if operation not in ALLOWED_OPERATIONS:
        raise ValueError(
            "Invalid operation. "
            "Use append, upsert or truncate_insert."
        )

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

    fields = db.scalars(
        select(MappingField).where(
            MappingField.mapping_id == mapping.id
        )
    ).all()

    records = parse_file(
        file_content,
        mapping.file_type,
    )

    normalized_records = []
    failed_records = 0

    for record in records:

        try:

            normalized = normalize_record(
                record,
                fields,
            )

            if not normalized.get("event_id"):
                raise ValueError(
                    "event_id is required"
                )

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

    return {
        "mapping_name": mapping_name,
        "operation": operation,
        "file_name": file_name,
        "records_received": len(records),
        "records_loaded": loaded,
        "records_failed": failed_records,
        "status": (
            "success"
            if failed_records == 0
            else "partial_success"
        ),
    }