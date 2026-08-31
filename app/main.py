from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.api.ingestion import router as ingestion_router
from app.api.mappings import router as mappings_router
from app.api.tables import router as tables_router
from app.database.base import Base
from app.database.connection import engine

from app.models.ingestion import IngestionFailureLog
from app.models.mapping import (
    MappingDefinition,
    MappingField,
)


@asynccontextmanager
async def lifespan(app: FastAPI):

    # Create ONLY framework metadata tables.
    #
    # Destination/predefined tables are NOT automatically
    # created here.
    #
    # They must be explicitly created through:
    # POST /tables/

    Base.metadata.create_all(
        bind=engine,
        tables=[
            MappingDefinition.__table__,
            MappingField.__table__,
            IngestionFailureLog.__table__,
        ],
    )

    yield


app = FastAPI(
    title="ITDR Generic Data Ingestion Framework",
    description=(
        "Generic mapping-driven ITDR data ingestion "
        "framework supporting JSON, CSV and XML."
    ),
    version="1.0.0",
    lifespan=lifespan,
)


app.include_router(
    tables_router
)

app.include_router(
    mappings_router
)

app.include_router(
    ingestion_router
)


@app.get("/")
def health_check():

    return {
        "application": (
            "ITDR Generic Data Ingestion Framework"
        ),
        "status": "running",
    }