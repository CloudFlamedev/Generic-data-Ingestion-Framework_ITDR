import csv
import io
import json
import xml.etree.ElementTree as ET


def parse_json(content: bytes) -> list[dict]:
    data = json.loads(content.decode("utf-8"))

    if isinstance(data, dict):
        return [data]

    if isinstance(data, list):
        return data

    raise ValueError("JSON must contain an object or array of objects")


def parse_csv(content: bytes) -> list[dict]:
    text = content.decode("utf-8-sig")

    reader = csv.DictReader(io.StringIO(text))

    return [
        dict(row)
        for row in reader
    ]


def parse_xml(content: bytes) -> list[dict]:
    root = ET.fromstring(content)

    records = []

    for event in root:
        record = {}

        for child in event:
            record[child.tag] = child.text

        if record:
            records.append(record)

    return records


def parse_file(content: bytes, file_type: str) -> list[dict]:

    file_type = file_type.lower()

    if file_type == "json":
        return parse_json(content)

    if file_type == "csv":
        return parse_csv(content)

    if file_type == "xml":
        return parse_xml(content)

    raise ValueError(
        f"Unsupported file type: {file_type}"
    )