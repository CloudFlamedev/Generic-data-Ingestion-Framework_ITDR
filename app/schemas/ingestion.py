from typing import Literal

from pydantic import BaseModel


OperationType = Literal[
    "append",
    "upsert",
    "truncate_insert",
]


class IngestionResponse(BaseModel):
    mapping_name: str
    operation: OperationType
    file_name: str
    records_received: int
    records_loaded: int
    records_failed: int
    status: str