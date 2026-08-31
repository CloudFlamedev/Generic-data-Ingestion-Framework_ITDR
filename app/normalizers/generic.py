from datetime import datetime


def convert_value(
    value,
    data_type: str,
    max_length: int | None = None,
):
    if value is None:
        return None

    data_type = data_type.lower()

    if data_type in {"string", "str"}:
        value = str(value)

        if max_length:
            value = value[:max_length]

        return value

    if data_type in {"integer", "int"}:
        return int(value)

    if data_type in {"float", "double"}:
        return float(value)

    if data_type in {"boolean", "bool"}:
        if isinstance(value, bool):
            return value

        return str(value).lower() in {
            "true",
            "1",
            "yes",
        }

    if data_type in {
        "datetime",
        "timestamp",
    }:
        if isinstance(value, datetime):
            return value

        return datetime.fromisoformat(
            str(value).replace("Z", "+00:00")
        )

    return value


def normalize_record(
    record: dict,
    mapping_fields,
) -> dict:

    normalized = {}

    for field in mapping_fields:

        value = record.get(field.source_field)

        if value is None or value == "":
            if field.default_value is not None:
                value = field.default_value

            elif field.mandatory:
                raise ValueError(
                    f"Mandatory field missing: "
                    f"{field.source_field}"
                )

        value = convert_value(
            value,
            field.data_type,
            field.max_length,
        )

        normalized[field.destination_field] = value

    return normalized