from sqlalchemy import inspect, select

from app.models.mapping import (
    MappingDefinition,
    MappingField,
)


def create_mapping(db, mapping_data):

    # Check mapping name
    existing = db.scalar(
        select(MappingDefinition).where(
            MappingDefinition.mapping_name
            == mapping_data.mapping_name
        )
    )

    if existing:
        raise ValueError(
            f"Mapping already exists: "
            f"{mapping_data.mapping_name}"
        )

    # Destination table must already exist.
    # Tables are created separately through /tables/.
    inspector = inspect(db.bind)

    if mapping_data.destination_table not in inspector.get_table_names():
        raise ValueError(
            f"Destination table does not exist: "
            f"{mapping_data.destination_table}. "
            "Create the predefined table first using POST /tables/."
        )

    mapping = MappingDefinition(
        mapping_name=mapping_data.mapping_name,
        source_name=mapping_data.source_name,
        destination_table=mapping_data.destination_table,
        file_type=mapping_data.file_type.lower(),
        file_pattern=mapping_data.file_pattern,
        description=mapping_data.description,
    )

    db.add(mapping)

    db.flush()

    for field in mapping_data.fields:

        mapping_field = MappingField(
            mapping_id=mapping.id,
            source_field=field.source_field,
            destination_field=field.destination_field,
            data_type=field.data_type,
            max_length=field.max_length,
            mandatory=field.mandatory,
            validation_rule=field.validation_rule,
            default_value=field.default_value,
        )

        db.add(mapping_field)

    db.commit()

    return mapping


def list_mappings(db):

    return db.scalars(
        select(MappingDefinition)
    ).all()