from pydantic import BaseModel, Field


class MappingFieldCreate(BaseModel):
    source_field: str
    destination_field: str
    data_type: str = "string"
    max_length: int | None = None
    mandatory: bool = False
    validation_rule: str | None = None
    default_value: str | None = None


class MappingCreate(BaseModel):
    mapping_name: str
    source_name: str
    destination_table: str
    file_type: str
    file_pattern: str
    description: str | None = None
    fields: list[MappingFieldCreate] = Field(min_length=1)