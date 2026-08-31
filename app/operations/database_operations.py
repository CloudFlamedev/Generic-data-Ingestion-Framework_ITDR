from sqlalchemy import MetaData, Table, delete, insert
from sqlalchemy.dialects.postgresql import insert as pg_insert


def get_table(engine, table_name: str):
    metadata = MetaData()

    return Table(
        table_name,
        metadata,
        autoload_with=engine,
    )


def append_records(
    engine,
    table_name: str,
    records: list[dict],
):
    if not records:
        return 0

    table = get_table(
        engine,
        table_name,
    )

    with engine.begin() as connection:
        connection.execute(
            insert(table),
            records,
        )

    return len(records)


def upsert_records(
    engine,
    table_name: str,
    records: list[dict],
):
    if not records:
        return 0

    table = get_table(
        engine,
        table_name,
    )

    if "event_id" not in table.c:
        raise ValueError(
            f"Table '{table_name}' does not contain event_id. "
            "event_id is required for the current upsert strategy."
        )

    statement = pg_insert(table).values(records)

    update_columns = {
        column.name: getattr(statement.excluded, column.name)
        for column in table.columns
        if column.name not in {"id", "event_id"}
    }

    statement = statement.on_conflict_do_update(
        index_elements=["event_id"],
        set_=update_columns,
    )

    with engine.begin() as connection:
        connection.execute(statement)

    return len(records)


def truncate_insert_records(
    engine,
    table_name: str,
    records: list[dict],
):
    table = get_table(
        engine,
        table_name,
    )

    with engine.begin() as connection:

        connection.execute(
            delete(table)
        )

        if records:
            connection.execute(
                insert(table),
                records,
            )

    return len(records)