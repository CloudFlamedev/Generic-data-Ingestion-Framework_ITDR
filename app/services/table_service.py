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


FRAMEWORK_TABLES = {
    "mapping_definitions",
    "mapping_fields",
    "ingestion_failure_log",
}


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

    data_type = data_type.lower().strip()

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

    table_name = table_name.strip()

    if not table_name:
        raise ValueError(
            "Table name cannot be empty"
        )

    if table_name in FRAMEWORK_TABLES:
        raise ValueError(
            f"'{table_name}' is a framework table "
            "and cannot be created as a destination table."
        )

    inspector = inspect(engine)

    # Predefined tables are created only once.
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

    existing_column_names = {
        "id",
        "event_id",
        "raw_data",
    }

    for field in fields:

        field_name = field.name.strip()

        if not field_name:
            raise ValueError(
                "Destination field name cannot be empty"
            )

        if field_name in existing_column_names:
            continue

        columns.append(
            Column(
                field_name,
                normalize_type(field.data_type),
                nullable=field.nullable,
            )
        )

        existing_column_names.add(field_name)

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

    return [
        table
        for table in inspector.get_table_names()
        if table not in FRAMEWORK_TABLES
    ]