# ITDR Generic Data Ingestion Framework

A mapping-driven backend framework for ingesting ITDR/security data from
**JSON, CSV, and XML** files into **PostgreSQL**.

> **Give the framework a file + tell it which mapping to use + choose
> how to load it. The framework parses, maps, validates, normalizes, and
> stores the data.**

------------------------------------------------------------------------

## 1. What Problem Are We Solving?

ITDR/security systems can send data in different formats:

-   JSON
-   CSV
-   XML

Instead of creating a separate ingestion program for every source, this
framework provides one common pipeline.

``` text
Different Files
      |
      v
FastAPI API
      |
      v
Parser
(JSON / CSV / XML)
      |
      v
Mapping
      |
      v
Normalization
      |
      v
Validation
      |
      +---------- invalid ----------> ingestion_failure_log
      |
    valid
      |
      v
Database Operation
(append / upsert / truncate_insert)
      |
      v
PostgreSQL Destination Table
```

------------------------------------------------------------------------

## 2. High-Level Architecture

``` text
                    +----------------------+
                    |      Source File     |
                    | JSON / CSV / XML     |
                    +----------+-----------+
                               |
                               v
                    +----------------------+
                    |      FastAPI API      |
                    |   POST /ingest/file  |
                    +----------+-----------+
                               |
                               v
                    +----------------------+
                    |       Parser         |
                    | JSON / CSV / XML     |
                    +----------+-----------+
                               |
                               v
                    +----------------------+
                    |   Mapping Definition |
                    | Which fields go      |
                    | where?               |
                    +----------+-----------+
                               |
                               v
                    +----------------------+
                    |    Normalization     |
                    | Convert data types   |
                    | Apply defaults       |
                    | Check mandatory      |
                    +----------+-----------+
                               |
                     +---------+---------+
                     |                   |
                  Valid               Invalid
                     |                   |
                     v                   v
          +-------------------+   +---------------------+
          | Database Operation|   | ingestion_failure_ |
          | append            |   | log                 |
          | upsert            |   +---------------------+
          | truncate_insert   |
          +---------+---------+
                    |
                    v
          +-----------------------+
          | PostgreSQL Destination|
          | Table                 |
          +-----------------------+
```

------------------------------------------------------------------------

## 3. Technologies Used

  Technology                       Purpose
  -------------------------------- ---------------------------
  Python                           Main programming language
  FastAPI                          REST API
  Pydantic                         Request validation
  SQLAlchemy                       Database interaction
  psycopg2                         PostgreSQL driver
  PostgreSQL                       Database
  Python `csv`                     CSV parsing
  Python `json`                    JSON parsing
  Python `xml.etree.ElementTree`   XML parsing
  pytest                           Automated testing
  httpx                            HTTP testing support
  python-multipart                 File upload support

------------------------------------------------------------------------

## 4. Project Structure

``` text
ITDR_GENERIC_DATA_INGESTION_FRAMEWORK/
│
├── app/
│   ├── api/
│   │   ├── ingestion.py
│   │   ├── mappings.py
│   │   └── tables.py
│   │
│   ├── core/
│   │   └── config.py
│   │
│   ├── database/
│   │   ├── base.py
│   │   └── connection.py
│   │
│   ├── models/
│   │   ├── ingestion.py
│   │   └── mapping.py
│   │
│   ├── normalizers/
│   │   └── generic.py
│   │
│   ├── operations/
│   │   └── database_operations.py
│   │
│   ├── parsers/
│   │   └── generic.py
│   │
│   ├── schemas/
│   │   ├── ingestion.py
│   │   ├── mapping.py
│   │   └── table.py
│   │
│   ├── services/
│   │   ├── ingestion_service.py
│   │   ├── mapping_service.py
│   │   └── table_service.py
│   │
│   └── main.py
│
├── test_data/
│   ├── active_directory.json
│   ├── active_directory_2.json
│   ├── active_directory.csv
│   └── active_directory.xml
│
├── .env
├── .env.example
├── requirements.txt
└── README.md
```

------------------------------------------------------------------------

# 5. Framework in Layman's Terms

Think of this framework as a **postal sorting center for data**.

A package arrives. The center needs to know:

1.  What format is it?
2.  Where should each piece of information go?
3.  Is the information valid?
4.  Should it be added, updated, or replace existing data?
5.  If something is wrong, what happened?

Our framework does the same thing for ITDR data.

``` text
Incoming File
     |
     v
"What format?"
     |
     +--> JSON parser
     +--> CSV parser
     +--> XML parser
     |
     v
"What mapping should I use?"
     |
     v
"Are the values valid?"
     |
     v
"Where should they go?"
     |
     v
"Append / Upsert / Replace?"
     |
     v
PostgreSQL
```

------------------------------------------------------------------------

# 6. Step-by-Step Flow

## Step 1: Create a Destination Table

We can create a destination table using:

``` http
POST /tables/
```

Example:

``` json
{
  "table_name": "active_directory",
  "fields": [
    {
      "name": "event_type",
      "data_type": "string",
      "nullable": false
    },
    {
      "name": "entity",
      "data_type": "string",
      "nullable": false
    },
    {
      "name": "action",
      "data_type": "string",
      "nullable": true
    }
  ]
}
```

The framework automatically adds:

``` text
id
event_id
raw_data
```

So the resulting table contains:

``` text
+----+----------+------------+--------+---------+----------+
| id | event_id | event_type | entity | action  | raw_data |
+----+----------+------------+--------+---------+----------+
```

### Why?

The destination table stores the clean, normalized security data.

-   `id` = database primary key
-   `event_id` = source/business identifier
-   `raw_data` = original source record

------------------------------------------------------------------------

# 7. Database Tables

There are two categories:

### Framework tables

These control the ingestion framework.

``` text
mapping_definitions
mapping_fields
ingestion_failure_log
```

### Destination tables

These contain actual ITDR/security data.

During our testing we created:

``` text
active_directory
active_directory_csv
active_directory_xml
```

------------------------------------------------------------------------

# 8. `mapping_definitions`

This is the **mapping master table**.

It answers:

> "For this source, which file type and destination table should I use?"

Current columns:

``` text
id
mapping_name
source_name
destination_table
file_type
file_pattern
description
is_active
created_at
```

Example:

``` text
mapping_name      = active_directory_events
source_name       = Active Directory
destination_table = active_directory
file_type         = json
file_pattern      = *.json
```

### Why?

We avoid hardcoding source-specific logic in Python.

Instead of:

``` python
if source == "Active Directory":
    ...
```

the configuration is stored in the database.

------------------------------------------------------------------------

# 9. `mapping_fields`

This is the **field-level mapping table**.

It answers:

> "Which source field goes into which destination field?"

Current columns:

``` text
id
mapping_id
source_field
destination_field
data_type
max_length
mandatory
validation_rule
default_value
```

Example:

``` text
source_field      = event_type
destination_field = event_type
data_type         = string
mandatory         = true
```

Relationship:

``` text
mapping_definitions
        |
        | 1
        |
        | many
        v
mapping_fields
```

One mapping can have many field mappings.

------------------------------------------------------------------------

# 10. `ingestion_failure_log`

This table stores records that fail during normalization/validation.

Current columns:

``` text
id
mapping_name
file_name
error_message
failed_record
created_at
```

Example:

``` text
mapping_name  = active_directory_events
file_name     = active_directory.json
error_message = Mandatory field missing: entity
failed_record = {"event_id":"AD-004", ...}
```

### Why?

Suppose a file contains 1,000 records and 5 are bad:

``` text
1000 records
     |
     +----> 995 valid records --> destination table
     |
     +----> 5 invalid records --> ingestion_failure_log
```

Bad records are not silently lost.

------------------------------------------------------------------------

# 11. Destination Tables

Destination tables contain actual source data.

For example:

``` text
active_directory
----------------
id
event_id
event_type
entity
action
raw_data
```

Our CSV and XML tests used:

``` text
active_directory_csv
active_directory_xml
```

The framework automatically includes `id`, `event_id`, and `raw_data`.

------------------------------------------------------------------------

# 12. Why `id` and `event_id` Are Different

`id` is generated by the database.

``` text
1
2
3
```

`event_id` comes from the source.

``` text
AD-001
AD-002
AD-003
```

Think of it as:

``` text
Database identity       Source identity
       |                       |
       v                       v
      id                    event_id
       1                     AD-001
       2                     AD-002
       3                     AD-003
```

The current upsert strategy uses `event_id`.

------------------------------------------------------------------------

# 13. Creating a Mapping

API:

``` http
POST /mappings/
```

Example:

``` json
{
  "mapping_name": "active_directory_events",
  "source_name": "Active Directory",
  "destination_table": "active_directory",
  "file_type": "json",
  "file_pattern": "*.json",
  "description": "Active Directory event ingestion mapping",
  "fields": [
    {
      "source_field": "event_id",
      "destination_field": "event_id",
      "data_type": "string",
      "mandatory": true
    },
    {
      "source_field": "event_type",
      "destination_field": "event_type",
      "data_type": "string",
      "mandatory": true
    },
    {
      "source_field": "entity",
      "destination_field": "entity",
      "data_type": "string",
      "mandatory": true
    },
    {
      "source_field": "action",
      "destination_field": "action",
      "data_type": "string"
    }
  ]
}
```

This configuration tells the framework how to understand incoming data.

------------------------------------------------------------------------

# 14. JSON Parsing

The parser accepts either a single object:

``` json
{
  "event_id": "AD-001",
  "event_type": "LOGIN",
  "entity": "user01",
  "action": "SUCCESS"
}
```

or an array:

``` json
[
  {
    "event_id": "AD-001",
    "event_type": "LOGIN",
    "entity": "user01",
    "action": "SUCCESS"
  },
  {
    "event_id": "AD-002",
    "event_type": "LOGIN",
    "entity": "user02",
    "action": "FAILED"
  }
]
```

The parser produces:

``` text
list[dict]
```

------------------------------------------------------------------------

# 15. CSV Parsing

Example:

``` csv
event_id,event_type,entity,action
CSV-001,LOGIN,user10,SUCCESS
CSV-002,LOGIN,user20,FAILED
CSV-003,LOGOUT,user10,SUCCESS
```

The CSV headers become source field names.

The result is equivalent to:

``` python
[
    {
        "event_id": "CSV-001",
        "event_type": "LOGIN",
        "entity": "user10",
        "action": "SUCCESS"
    },
    ...
]
```

------------------------------------------------------------------------

# 16. XML Parsing

The current parser expects a simple structure:

``` xml
<events>
    <event>
        <event_id>XML-001</event_id>
        <event_type>LOGIN</event_type>
        <entity>user100</entity>
        <action>SUCCESS</action>
    </event>
    <event>
        <event_id>XML-002</event_id>
        <event_type>LOGIN</event_type>
        <entity>user200</entity>
        <action>FAILED</action>
    </event>
</events>
```

Each `<event>` becomes one Python dictionary.

------------------------------------------------------------------------

# 17. Normalization

After parsing, the framework normalizes every record.

``` text
Source value
     |
     v
Does value exist?
     |
     +--> No + default exists --> use default
     |
     +--> No + mandatory ------> failure
     |
     +--> Yes
            |
            v
       Convert data type
            |
            v
        Normalized value
```

Current conversions include:

``` text
string / str
integer / int
float / double
boolean / bool
datetime / timestamp
```

------------------------------------------------------------------------

# 18. Mandatory Fields

Example:

``` json
{
  "source_field": "entity",
  "destination_field": "entity",
  "mandatory": true
}
```

If `entity` is missing, normalization raises an error and the record is
written to the failure log.

------------------------------------------------------------------------

# 19. Default Values

A mapping field can define a `default_value`.

Conceptually:

``` text
Incoming value
     |
     +--> exists? ------> use it
     |
     +--> missing?
             |
             +--> default exists --> use default
             |
             +--> mandatory ------> failure
```

------------------------------------------------------------------------

# 20. `event_id` Requirement

The ingestion service additionally requires every normalized record to
contain:

``` text
event_id
```

If it does not:

``` text
event_id is required
```

The record is treated as failed.

This is important because the current upsert implementation uses
`event_id` as its conflict key.

------------------------------------------------------------------------

# 21. Raw Data Preservation

After normalization the framework adds:

``` text
raw_data
```

The original source record is stored as JSON text.

Example:

``` json
{
  "event_id": "AD-001",
  "event_type": "LOGIN",
  "entity": "user01",
  "action": "SUCCESS"
}
```

### Why?

It provides a copy of the original source record for:

-   debugging
-   auditing
-   troubleshooting
-   traceability
-   investigation

------------------------------------------------------------------------

# 22. Database Operations

The framework supports:

``` text
append
upsert
truncate_insert
```

## Append

> Add new records and keep existing records.

``` text
Existing: AD-001, AD-002
New:      AD-003, AD-004

Result:   AD-001, AD-002, AD-003, AD-004
```

------------------------------------------------------------------------

## Upsert

> If the event exists, update it. Otherwise insert it.

Existing:

``` text
event_id | action
---------+--------
AD-001   | SUCCESS
AD-002   | FAILED
```

Incoming:

``` text
AD-002 | SUCCESS
AD-003 | SUCCESS
```

Result:

``` text
event_id | action
---------+--------
AD-001   | SUCCESS
AD-002   | SUCCESS   <-- updated
AD-003   | SUCCESS   <-- inserted
```

The current implementation uses `event_id` as the conflict key.

------------------------------------------------------------------------

## Truncate Insert

> Delete existing destination data and load the new file.

Before:

``` text
AD-001
AD-002
AD-003
```

New file:

``` text
AD-100
AD-101
```

After:

``` text
AD-100
AD-101
```

This is useful for full snapshot files.

------------------------------------------------------------------------

# 23. API Endpoints

## Health Check

``` http
GET /
```

## Create Destination Table

``` http
POST /tables/
```

## List Destination Tables

``` http
GET /tables/
```

## Create Mapping

``` http
POST /mappings/
```

## List Mappings

``` http
GET /mappings/
```

## Ingest File

``` http
POST /ingest/file
```

Form fields:

``` text
mapping_name
operation
file
```

Example:

``` text
mapping_name = active_directory_events
operation    = append
file         = active_directory.json
```

------------------------------------------------------------------------

# 24. Complete Example

Suppose Active Directory sends:

``` json
[
  {
    "event_id": "AD-001",
    "event_type": "LOGIN",
    "entity": "user01",
    "action": "SUCCESS"
  },
  {
    "event_id": "AD-002",
    "event_type": "LOGIN",
    "entity": "user02",
    "action": "FAILED"
  }
]
```

The framework performs:

``` text
1. Receive file
       |
2. Find mapping
       |
3. Parse JSON
       |
4. Get mapping fields
       |
5. Normalize values
       |
6. Validate mandatory fields
       |
7. Require event_id
       |
8. Preserve raw_data
       |
9. Execute operation
       |
10. Write to PostgreSQL
       |
11. Return ingestion result
```

Example response:

``` json
{
  "mapping_name": "active_directory_events",
  "operation": "append",
  "file_name": "active_directory.json",
  "records_received": 2,
  "records_loaded": 2,
  "records_failed": 0,
  "status": "success"
}
```

------------------------------------------------------------------------

# 25. What We Tested

## JSON

Result:

``` text
records_received = 3
records_loaded   = 3
records_failed   = 0
status           = success
```

## Upsert

We tested an updated JSON record using:

``` text
operation = upsert
```

The existing event was updated instead of creating a duplicate.

## Truncate Insert

We tested:

``` text
operation = truncate_insert
```

Result:

``` text
records_received = 3
records_loaded   = 3
records_failed   = 0
status           = success
```

## CSV

Test file:

``` text
test_data/active_directory.csv
```

Result:

``` text
CSV = 3 records
```

## XML

Test file:

``` text
test_data/active_directory.xml
```

Result:

``` text
XML = 3 records
```

Final PostgreSQL verification:

``` text
 source | count
--------+-------
 CSV    |     3
 XML    |     3
```

The JSON destination was also verified with three expected records, and
the failure log contained zero rows for the successful test runs.

------------------------------------------------------------------------

# 26. Why This Architecture Is Useful

### One ingestion engine

No separate application is required for every source.

### Multiple file formats

``` text
JSON
CSV
XML
```

### Configuration-driven mapping

Source-to-destination rules are stored in PostgreSQL.

### Data normalization

Incoming values can be converted to expected types.

### Mandatory-field validation

Bad records can be rejected without losing the entire file.

### Failure tracking

Failed records and error messages are stored for investigation.

### Multiple loading strategies

``` text
append
upsert
truncate_insert
```

### Raw data preservation

Original source data is retained in `raw_data`.

### Easy extension

New formats, rules, and operations can be added later.

------------------------------------------------------------------------

# 27. Important Design Idea

The most important architectural idea is:

> **Move source-specific behavior into configuration instead of
> hardcoding it into the ingestion engine.**

Instead of:

``` python
if source == "Active Directory":
    ...
elif source == "AWS":
    ...
elif source == "Azure":
    ...
```

we configure mappings:

``` text
              Mapping Configuration
                       |
       +---------------+---------------+
       |               |               |
       v               v               v
   Active Dir        AWS             Azure
       |               |               |
       v               v               v
    Mapping         Mapping         Mapping
       |               |               |
       +---------------+---------------+
                       |
                       v
              Same ingestion engine
```

That is what makes the framework **generic**.

------------------------------------------------------------------------

# 28. Current Limitations / Future Improvements

The current project is an MVP.

### Validation rules

`validation_rule` exists in the database model, but the current
normalizer does not yet execute arbitrary validation rules.

### Better error handling

Future versions can add:

-   structured error codes
-   safer error responses
-   better application logging
-   correlation IDs

### Transaction handling

The current implementation commits failure-log records before executing
the destination database operation. Future versions can make transaction
behavior more deliberate.

### Large-file processing

The current implementation loads parsed records into memory. Future
versions can add:

``` text
batch processing
streaming
chunked inserts
PostgreSQL COPY
```

### Security

Production hardening should include:

``` text
authentication
authorization
file-size limits
allowed file-type validation
rate limiting
secure credentials
audit logging
```

### More flexible XML

The current XML parser supports a simple root/record structure.
Real-world products may need configurable XML paths and nested-field
handling.

------------------------------------------------------------------------

# 29. The Framework in One Diagram

``` text
                     ITDR DATA SOURCES
                            |
             +--------------+--------------+
             |              |              |
           JSON            CSV            XML
             |              |              |
             +--------------+--------------+
                            |
                            v
                 +----------------------+
                 |      FastAPI API      |
                 |    /ingest/file       |
                 +----------+-----------+
                            |
                            v
                 +----------------------+
                 |       Parser          |
                 | JSON / CSV / XML      |
                 +----------+-----------+
                            |
                            v
                 +----------------------+
                 | Mapping Definitions   |
                 | + Mapping Fields      |
                 +----------+-----------+
                            |
                            v
                 +----------------------+
                 |     Normalization     |
                 | type conversion       |
                 | defaults              |
                 | mandatory fields      |
                 +----------+-----------+
                            |
                       +----+----+
                       |         |
                    VALID      INVALID
                       |         |
                       |         v
                       |   +------------------+
                       |   | Failure Log      |
                       |   | ingestion_failure|
                       |   +------------------+
                       |
                       v
              +-------------------------+
              | Database Operation      |
              |                         |
              | append                  |
              | upsert                  |
              | truncate_insert         |
              +------------+------------+
                           |
                           v
                 +----------------------+
                 |      PostgreSQL      |
                 | Destination Tables   |
                 +----------------------+
```

------------------------------------------------------------------------

# 30. Simple Mental Model

Remember these six words:

``` text
READ
  ↓
PARSE
  ↓
MAP
  ↓
VALIDATE
  ↓
LOAD
  ↓
LOG
```

### READ

Receive the file.

### PARSE

Understand JSON / CSV / XML.

### MAP

Understand where each source field belongs.

### VALIDATE

Check mandatory fields and convert values.

### LOAD

Write valid data to PostgreSQL.

### LOG

Remember what failed.

------------------------------------------------------------------------

# 31. Final Summary

The ITDR Generic Data Ingestion Framework is a **configurable data
pipeline**:

``` text
                    INPUT
                      |
             JSON / CSV / XML
                      |
                      v
                   PARSE
                      |
                      v
                   MAPPING
                      |
                      v
                 NORMALIZE
                      |
                      v
                  VALIDATE
                      |
             +--------+--------+
             |                 |
           VALID            INVALID
             |                 |
             v                 v
          LOAD DB         FAILURE LOG
             |
             v
      PostgreSQL tables
```

The three core framework tables are:

``` text
mapping_definitions
        |
        +--> What mapping is this?

mapping_fields
        |
        +--> How do individual fields map?

ingestion_failure_log
        |
        +--> What went wrong with bad records?
```

Destination tables contain the actual ITDR/security data.

The biggest architectural benefit is:

> **A new source can often be onboarded by creating a destination table
> and mapping configuration rather than writing a completely new
> ingestion application.**

------------------------------------------------------------------------

# 32. Current Project Status

``` text
Framework skeleton                 ✅
PostgreSQL connection              ✅
Dynamic destination tables         ✅
Mapping definitions                ✅
Field mappings                     ✅
JSON parser                        ✅
CSV parser                         ✅
XML parser                         ✅
Normalization                      ✅
Mandatory-field handling           ✅
Raw-data preservation              ✅
Append operation                   ✅
Upsert operation                   ✅
Truncate-insert operation          ✅
Failure logging                    ✅
FastAPI endpoints                  ✅
Swagger testing                    ✅
JSON end-to-end test               ✅
CSV end-to-end test                ✅
XML end-to-end test                ✅
```

