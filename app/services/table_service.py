from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    Float,
    Integer,
    MetaData,
    String,
    Table,
    Text,
    inspect,
)


TYPE_MAP = {
    "string": String(255),
    "varchar": String(255),
    "text": Text(),
    "integer": Integer(),
    "int": Integer(),
    "float": Float(),
    "boolean": Boolean(),
    "bool": Boolean(),
    "datetime": DateTime(),
    "timestamp": DateTime(),
}


def normalize_type(data_type: str):

    data_type = data_type.lower()

    if data_type.startswith("varchar"):
        return String(255)

    if data_type in TYPE_MAP:
        return TYPE_MAP[data_type]

    raise ValueError(
        f"Unsupported database data type: {data_type}"
    )


def create_predefined_table(
    engine,
    table_name: str,
    fields,
):

    inspector = inspect(engine)

    if table_name in inspector.get_table_names():
        return False

    metadata = MetaData()

    columns = [
        Column(
            "id",
            Integer,
            primary_key=True,
            autoincrement=True,
        ),
        Column(
            "event_id",
            String(255),
            unique=True,
            nullable=False,
        ),
    ]

    for field in fields:

        if field.name in {
            "id",
            "event_id",
        }:
            continue

        columns.append(
            Column(
                field.name,
                normalize_type(field.data_type),
                nullable=field.nullable,
            )
        )

    columns.append(
        Column(
            "raw_data",
            Text,
            nullable=True,
        )
    )

    table = Table(
        table_name,
        metadata,
        *columns,
    )

    metadata.create_all(
        engine,
        tables=[table],
    )

    return True


def list_predefined_tables(engine):

    inspector = inspect(engine)

    excluded = {
        "mapping_definitions",
        "mapping_fields",
        "ingestion_failure_log",
    }

    return [
        table
        for table in inspector.get_table_names()
        if table not in excluded
    ]