from pydantic import BaseModel, Field


class TableFieldDefinition(BaseModel):
    name: str
    data_type: str = "VARCHAR(255)"
    nullable: bool = True


class PredefinedTableCreate(BaseModel):
    table_name: str
    fields: list[TableFieldDefinition] = Field(min_length=1)


class PredefinedTableResponse(BaseModel):
    table_name: str
    created: bool