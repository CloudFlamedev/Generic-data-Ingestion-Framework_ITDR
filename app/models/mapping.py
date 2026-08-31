from datetime import datetime

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import Base


class MappingDefinition(Base):
    __tablename__ = "mapping_definitions"

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        autoincrement=True,
    )

    mapping_name: Mapped[str] = mapped_column(
        String(100),
        unique=True,
        nullable=False,
    )

    source_name: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
    )

    destination_table: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
    )

    file_type: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
    )

    file_pattern: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )

    description: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    is_active: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
        nullable=False,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
        nullable=False,
    )

    fields: Mapped[list["MappingField"]] = relationship(
        back_populates="mapping",
        cascade="all, delete-orphan",
    )


class MappingField(Base):
    __tablename__ = "mapping_fields"

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        autoincrement=True,
    )

    mapping_id: Mapped[int] = mapped_column(
        ForeignKey("mapping_definitions.id", ondelete="CASCADE"),
        nullable=False,
    )

    source_field: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
    )

    destination_field: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
    )

    data_type: Mapped[str] = mapped_column(
        String(50),
        default="string",
        nullable=False,
    )

    max_length: Mapped[int | None] = mapped_column(
        Integer,
        nullable=True,
    )

    mandatory: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False,
    )

    validation_rule: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    default_value: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    mapping: Mapped["MappingDefinition"] = relationship(
        back_populates="fields",
    )